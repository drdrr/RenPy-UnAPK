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
            try_harder=getattr(args, 'try_harder', False)
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

    def remove_prefix_from_names(self, dir_path: Path, prefix: str) -> None:
        """
        Recursively remove specified prefix from all file and directory names.

        Args:
            dir_path (Path): Directory to process
            prefix (str): Prefix to remove from names
        """
        for item in dir_path.rglob('*'):
            new_name = item.name.replace(prefix, '')
            new_path = item.parent / new_name

            try:
                item.rename(new_path)
            except OSError as e:
                self.logger.error(f"Could not rename {item}: {e}")

    def extract_apk(self, apk_path: Path) -> Path:
        """
        Extract game files from an APK.

        Args:
            apk_path (Path): Path to the APK file

        Returns:
            Path: Extracted game directory
        """
        self.logger.info(f"Extracting {apk_path}")

        # Create extraction directories
        game_folder = apk_path.with_suffix('')
        temp_folder = Path.cwd() / "TMP_APK_EXTRACT"
        game_folder.mkdir(exist_ok=True)
        temp_folder.mkdir(exist_ok=True)

        # Extract APK contents
        with zipfile.ZipFile(apk_path) as zf:
            zf.extractall(temp_folder)

        # Move required files
        try:
            shutil.move(
                temp_folder / 'assets' / 'x-game',
                game_folder
            )

            # Move icons and splash screen
            icon_sources = [
                ('res/mipmap-xxxhdpi-v4/icon_background.png', 'android-icon_background.png'),
                ('res/mipmap-xxxhdpi-v4/icon_foreground.png', 'android-icon_foreground.png'),
                ('assets/android-presplash.jpg', 'android-presplash.jpg')
            ]

            for src, dest in icon_sources:
                src_path = temp_folder / src
                if src_path.exists():
                    shutil.move(src_path, game_folder / dest)

        except Exception as e:
            self.logger.error(f"Error moving files: {e}")
            raise

        # Clean up temporary folder
        shutil.rmtree(temp_folder)

        # Remove 'x-' prefix from files and directories
        self.remove_prefix_from_names(game_folder, 'x-')

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

    parser.add_argument('-t', '--translation-file'
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
