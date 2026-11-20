#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9,<3.15"
# dependencies = ["androguard>=4"]
# ///
import re
import sys
import zipfile
import shutil
import argparse
import logging
import traceback

try:
    from multiprocessing import Pool, cpu_count
except ImportError:
    # Mock required support when multiprocessing is unavailable
    def cpu_count():
        return 1

from pathlib import Path
import unrpyc

# Optional: androguard resolves resources through resources.arsc, which is
# required for APKs built by newer RAPT (shortened/obfuscated res/ paths,
# e.g. res/-i.png instead of res/mipmap-xxxhdpi-v4/icon_foreground.png).
try:
    from androguard.core.apk import APK
    try:
        # androguard logs very verbosely through loguru; silence it.
        from loguru import logger as _loguru_logger
        _loguru_logger.remove()
    except Exception:
        pass
    HAS_ANDROGUARD = True
except ImportError:
    HAS_ANDROGUARD = False

# Where RAPT has stored the game directory inside the APK, newest first.
GAME_DIR_CANDIDATES = ('assets/x-game/', 'assets/game/')

# Icon resource names -> output file names expected by the Ren'Py SDK.
ICON_RESOURCES = {
    'icon_background': 'android-icon_background.png',
    'icon_foreground': 'android-icon_foreground.png',
}

# Top-level assets such as android-presplash.jpg / android-downloading.jpg.
ANDROID_ASSET_RE = re.compile(r'^assets/(?:x-)?(android-[^/]+\.(?:jpg|jpeg|png))$', re.I)

# Legacy layout: res/mipmap-<density>[-vN]/<name>.png
LEGACY_ICON_RE = re.compile(r'^res/mipmap-([a-z]+dpi)(?:-v\d+)?/([^/]+)\.png$')
DENSITY_RANK = {'ldpi': 120, 'mdpi': 160, 'tvdpi': 213, 'hdpi': 240,
                'xhdpi': 320, 'xxhdpi': 480, 'xxxhdpi': 640}

RAPT_PREFIX = 'x-'

class Context:
    def __init__(self):
        self.log_contents = []
        self.error = None
        self.state = "error"
        self.value = None

    def log(self, message):
        self.log_contents.append(message)

    def set_error(self, error):
        self.error = error

    def set_result(self, value):
        self.value = value

    def set_state(self, state):
        self.state = state


def worker_common(arg_tup):
    """
    Standalone worker function for decompiling RPYC files.

    Args:
        arg_tup (tuple): Tuple containing (args, filename)

    Returns:
        Context: Decompilation result context
    """
    args, filename = arg_tup
    context = Context()

    try:
        # Use the original unrpyc decompilation method with default arguments
        unrpyc.decompile_rpyc(
            filename, context,
            overwrite=getattr(args, 'clobber', False),
            try_harder=getattr(args, 'try_harder', False),
            dump=getattr(args, 'dump', False),
            no_pyexpr=getattr(args, 'no_pyexpr', False),
            comparable=getattr(args, 'comparable', False),
            init_offset=getattr(args, 'init_offset', True),
            sl_custom_names=getattr(args, 'sl_custom_names', None),
            translator=getattr(args, 'translator', None)
        )

    except Exception as e:
        context.set_error(e)
        context.log(f'Error while decompiling {filename}:')
        context.log(traceback.format_exc())

    return context


def run_workers(worker, common_args, private_args, parallelism):
    """
    Runs worker in parallel using multiprocessing.

    Args:
        worker (callable): Worker function to execute
        common_args (argparse.Namespace): Common arguments
        private_args (list): List of files to process
        parallelism (int): Number of processes to use

    Returns:
        list: Results from workers
    """
    worker_args = ((common_args, x) for x in private_args)

    results = []
    if parallelism > 1:
        with Pool(parallelism) as pool:
            for result in pool.imap(worker, worker_args, 1):
                results.append(result)
                for line in result.log_contents:
                    print(line)
                print("")
    else:
        for result in map(worker, worker_args):
            results.append(result)
            for line in result.log_contents:
                print(line)
            print("")

    return results


class RenPyUnapk:
    def __init__(self, args=None):
        """Initialize the RenPy Unapk tool with configuration."""
        self.logger = self._setup_logging()
        self.args = self._prepare_args(args)

    def _setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)

    def _prepare_args(self, args):
        """
        Prepare arguments for decompilation, ensuring all necessary attributes exist.

        Args:
            args (argparse.Namespace or None): Input arguments

        Returns:
            argparse.Namespace: Prepared arguments with default values
        """
        # Start with a base Namespace with default values
        prepared_args = argparse.Namespace(
            clobber=False,
            try_harder=False,
            dump=False,
            no_pyexpr=False,
            comparable=False,
            init_offset=True,
            sl_custom_names=None,
            translator=None
        )

        # Update with provided args if any
        if args:
            for attr, value in vars(args).items():
                setattr(prepared_args, attr, value)

        return prepared_args

    @staticmethod
    def _strip_rapt_prefix(rel_path: str) -> Path:
        """
        RAPT prefixes every file/dir under the game folder with 'x-' so that
        aapt doesn't drop names starting with '_' or '.'. Strip it from the
        start of each path component only (not from the middle of names).
        """
        parts = [p[len(RAPT_PREFIX):] if p.startswith(RAPT_PREFIX) else p
                 for p in rel_path.split('/') if p]
        return Path(*parts)

    @staticmethod
    def _safe_extract(zf: zipfile.ZipFile, member: str, dest: Path, root: Path) -> None:
        """Extract a single member to dest, refusing paths outside root."""
        dest_resolved = dest.resolve()
        if root.resolve() not in dest_resolved.parents:
            raise ValueError(f"Unsafe path in APK: {member}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, open(dest, 'wb') as dst:
            shutil.copyfileobj(src, dst)

    def _find_game_prefix(self, names) -> str:
        for prefix in GAME_DIR_CANDIDATES:
            if any(n.startswith(prefix) for n in names):
                return prefix
        raise FileNotFoundError(
            "No game directory found in APK (looked for: "
            + ", ".join(GAME_DIR_CANDIDATES) + ")")

    def _resolve_icons_arsc(self, apk_path: Path) -> dict:
        """
        New RAPT: res/ paths are shortened, so look the icons up by resource
        name in resources.arsc and pick the highest-density PNG.
        Returns {resource_name: path_in_apk}.
        """
        found = {}
        if not HAS_ANDROGUARD:
            return found
        try:
            apk = APK(str(apk_path))
            arsc = apk.get_android_resources()
            pkg = apk.get_package()
            for name in ICON_RESOURCES:
                rid = None
                for res_type in ('mipmap', 'drawable'):
                    rid = arsc.get_res_id_by_key(pkg, res_type, name)
                    if rid is not None:
                        break
                if rid is None:
                    continue
                configs = [(cfg, p) for cfg, p in arsc.get_resolved_res_configs(rid)
                           if isinstance(p, str) and p.lower().endswith('.png')]
                if configs:
                    cfg, path = max(configs, key=lambda cp: cp[0].get_density())
                    found[name] = path
        except Exception as e:
            self.logger.warning(f"Could not read resources.arsc: {e}")
        return found

    @staticmethod
    def _resolve_icons_legacy(names) -> dict:
        """Old RAPT: res/mipmap-<density>[-vN]/<name>.png, highest density wins."""
        best = {}
        for n in names:
            m = LEGACY_ICON_RE.match(n)
            if not m or m.group(2) not in ICON_RESOURCES:
                continue
            rank = DENSITY_RANK.get(m.group(1), 0)
            if m.group(2) not in best or rank > best[m.group(2)][0]:
                best[m.group(2)] = (rank, n)
        return {k: v[1] for k, v in best.items()}

    def extract_apk(self, apk_path: Path) -> Path:
        """
        Extract game files, icons and presplash images from an APK.

        Args:
            apk_path (Path): Path to the APK file

        Returns:
            Path: Extracted project directory
        """
        self.logger.info(f"Extracting {apk_path}")

        game_folder = apk_path.with_suffix('')
        game_folder.mkdir(exist_ok=True)

        with zipfile.ZipFile(apk_path) as zf:
            names = zf.namelist()
            name_set = set(names)

            # 1. Game files -> <project>/game/
            prefix = self._find_game_prefix(names)
            count = 0
            for member in names:
                if not member.startswith(prefix) or member.endswith('/'):
                    continue
                rel = self._strip_rapt_prefix(member[len(prefix):])
                self._safe_extract(zf, member, game_folder / 'game' / rel, game_folder)
                count += 1
            self.logger.info(f"Extracted {count} game files from {prefix}")

            # 2. Icons: legacy paths first (cheap), then resources.arsc for
            #    anything missing (new RAPT with shortened resource paths).
            icons = self._resolve_icons_legacy(names)
            missing = [n for n in ICON_RESOURCES if n not in icons]
            if missing:
                if HAS_ANDROGUARD:
                    arsc_icons = self._resolve_icons_arsc(apk_path)
                    icons.update({k: v for k, v in arsc_icons.items() if k in missing})
                else:
                    self.logger.warning(
                        "Icons not at legacy paths and androguard is not installed; "
                        "run 'pip install androguard' to extract icons from newer APKs.")

            for res_name, out_name in ICON_RESOURCES.items():
                src = icons.get(res_name)
                if src and src in name_set:
                    self._safe_extract(zf, src, game_folder / out_name, game_folder)
                    self.logger.info(f"Icon {res_name}: {src} -> {out_name}")
                else:
                    self.logger.warning(f"Icon {res_name} not found")

            # 3. android-presplash / android-downloading images
            for member in names:
                m = ANDROID_ASSET_RE.match(member)
                if m:
                    self._safe_extract(zf, member, game_folder / m.group(1), game_folder)
                    self.logger.info(f"Asset: {member} -> {m.group(1)}")

        self.logger.info(f"Extracted to {game_folder}")
        return game_folder

    def decompile_rpyc(self, game_folder: Path):
        """
        Decompile RenPy scripts in the game folder.

        Args:
            game_folder (Path): Folder containing game files
        """
        self.logger.info(f"Decompiling RenPy scripts in {game_folder}")

        # Find all .rpyc and .rpymc files
        rpyc_files = list(game_folder.rglob('*.rpyc')) + list(game_folder.rglob('*.rpymc'))

        if not rpyc_files:
            self.logger.warning("No script files found to decompile.")
            return

        # Use multiprocessing to match the original implementation
        parallelism = min(max(1, cpu_count() - 1), len(rpyc_files))

        # Run workers similar to the original implementation
        results = run_workers(worker_common, self.args, rpyc_files, parallelism)

        # Log results
        success = sum(result.state == "ok" for result in results)
        skipped = sum(result.state == "skip" for result in results)
        failed = sum(result.state == "error" for result in results)
        broken = sum(result.state == "bad_header" for result in results)

        self.logger.info(f"Decompilation summary:")
        self.logger.info(f"Total files: {len(results)}")
        self.logger.info(f"Successfully decompiled: {success}")
        self.logger.info(f"Skipped: {skipped}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Bad headers: {broken}")

    def process_apk(self, apk_path: Path):
        """
        Main processing method for an APK file.

        Args:
            apk_path (Path): Path to the APK file
        """
        try:
            game_folder = self.extract_apk(apk_path)
            self.decompile_rpyc(game_folder)
            self.logger.info(f"Successfully processed {apk_path}")
        except Exception as e:
            self.logger.error(f"Failed to process {apk_path}: {e}")


def parse_arguments():
    """Parse command-line arguments for the tool."""
    parser = argparse.ArgumentParser(description="RenPy APK Extraction and Decompilation Tool")

    parser.add_argument('apk', nargs='?', help='Path to APK file to process')

    parser.add_argument('-l', '--language', default='english',
                        help='Language for translation file (default: english)')

    parser.add_argument('-t', '--translation-file',
                        help='File to use for translations during decompilation')

    parser.add_argument('--try-harder', action='store_true',
                        help='Attempt advanced deobfuscation techniques')

    parser.add_argument('-c', '--clobber', action='store_true',
                        help='Overwrite existing output files')

    return parser.parse_args()


def main():
    """Main entry point for the application."""
    print("RenPy-UnApk: Restore RenPy Android Games to Project Files")
    print("Version 2.0 - Refactored")

    args = parse_arguments()
    tool = RenPyUnapk(args)

    # If no APK specified, find in current directory
    if not args.apk:
        apk_files = list(Path.cwd().glob('*.apk'))

        if not apk_files:
            tool.logger.error("No APK files found in current directory.")
            sys.exit(1)

        for apk in apk_files:
            tool.process_apk(apk)
    else:
        apk_path = Path(args.apk)
        if not apk_path.is_file():
            tool.logger.error(f"File not found: {apk_path}")
            sys.exit(1)

        tool.process_apk(apk_path)

    input('\nPress Enter to exit...')


if __name__ == '__main__':
    main()
