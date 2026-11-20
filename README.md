# RenPy-UnAPK

[English](#english) | [中文](#中文)

---

## English

Restore a Ren'Py Android game (`.apk`) to a project folder that the Ren'Py SDK can open: extracts the game files, icons and splash images, then decompiles the `.rpyc` scripts.

### Features

- Extracts game files, adaptive icons (`android-icon_foreground.png` / `android-icon_background.png`) and presplash/downloading images
- Supports APKs built by both older and newer Ren'Py / RAPT versions (including builds where `res/` file names are shortened)
- Processes multiple APKs in one run
- Decompiles `.rpyc` / `.rpymc` scripts with unrpyc (Ren'Py 8 compatible)

### Requirements

- Python **3.9 – 3.14**
- [androguard](https://github.com/androguard/androguard) ≥ 4: only needed for APKs built by newer Ren'Py versions (see below)
<!-- - unrpyc v2.0.3: included in this repository (`unrpyc.py` and `decompiler/` must stay in the same folder as `renpy-unapk.py`) -->

### How to run

#### Option A: uv (recommended)

The script declares its Python version and dependencies inline, so [uv](https://docs.astral.sh/uv/) sets up an isolated environment automatically, with nothing installed into your system Python.

```bash
# 1. Install uv (once), see https://docs.astral.sh/uv/getting-started/installation/
# 2. Download / clone this repository, then from the repository folder:
uv run renpy-unapk.py path/to/game.apk

# Or process every .apk in the current folder:
uv run renpy-unapk.py
```

uv picks (or downloads) a compatible Python below 3.15 and installs androguard for you on the first run.

On macOS / Linux you can also make the script directly executable:

```bash
chmod +x renpy-unapk.py
./renpy-unapk.py path/to/game.apk
```

#### Option B: plain Python

```bash
# Use Python 3.9–3.14
python renpy-unapk.py path/to/game.apk
```

This works as-is for APKs built by older Ren'Py versions. If you see warnings like these and no icons are extracted:

```
WARNING: Icons not at legacy paths and androguard is not installed; ...
WARNING: Icon icon_foreground not found
```

the APK was built by a newer Ren'Py version, so install androguard and run again:

```bash
python -m pip install "androguard>=4"
```

(A virtual environment is recommended: `python -m venv .venv`, then activate it before installing.)

### Output

Output goes into a folder with the same name as the APK, next to it:

```
game/                            # game files + decompiled .rpy scripts
android-icon_foreground.png
android-icon_background.png
android-presplash.jpg
```

### Standalone .exe

A standalone `.exe` is **not provided for now**: the packaged executable was flagged as a virus by Windows Defender (a false positive common with PyInstaller-style builds). Please run from source as described above.

### Credits

- unrpyc v2.0.3: https://github.com/CensoredUsername/unrpyc
- androguard: https://github.com/androguard/androguard

---

## 中文

将 APK 格式的 Ren'Py 安卓游戏恢复为可以用 Ren'Py SDK 打开的工程文件：提取游戏文件、图标和启动图，并反编译 `.rpyc` 脚本。

### 功能

- 提取游戏文件、自适应图标（`android-icon_foreground.png` / `android-icon_background.png`）以及 presplash / downloading 启动图
- 同时兼容旧版和新版 Ren'Py / RAPT 打包的 APK（包括 `res/` 文件名被缩短的新版构建）
- 支持一次还原多个 APK
- 使用 unrpyc 反编译 `.rpyc` / `.rpymc` 脚本（兼容 Ren'Py 8）

### 环境要求

- Python **3.9 – 3.14**（unrpyc 无法在 Python 3.15 上运行）
- [androguard](https://github.com/androguard/androguard) ≥ 4：仅在处理新版 Ren'Py 打包的 APK 时需要（见下文）
<!-- - unrpyc v2.0.3：已包含在本仓库中（`unrpyc.py` 和 `decompiler/` 需与 `renpy-unapk.py` 放在同一目录） -->

### 运行方法

#### 方法 A：使用 uv（推荐）

脚本内已声明所需的 Python 版本和依赖，[uv](https://docs.astral.sh/uv/) 会自动创建独立环境，不会改动系统 Python。

```bash
# 1. 安装 uv（只需一次），见 https://docs.astral.sh/uv/getting-started/installation/
# 2. 下载 / 克隆本仓库，在仓库目录下运行：
uv run renpy-unapk.py path/to/game.apk

# 或者还原当前目录下的所有 .apk：
uv run renpy-unapk.py
```

首次运行时，uv 会自动选择（或下载）低于 3.15 的兼容 Python 版本，并安装 androguard。

在 macOS / Linux 上也可以让脚本直接运行：

```bash
chmod +x renpy-unapk.py
./renpy-unapk.py path/to/game.apk
```

#### 方法 B：直接使用 Python

```bash
# 请使用 Python 3.9–3.14
python renpy-unapk.py path/to/game.apk
```

旧版 Ren'Py 打包的 APK 可以直接还原。如果出现以下警告且没有提取到图标：

```
WARNING: Icons not at legacy paths and androguard is not installed; ...
WARNING: Icon icon_foreground not found
```

说明该 APK 由新版 Ren'Py 打包，请安装 androguard 后重新运行：

```bash
python -m pip install "androguard>=4"
```

（建议使用虚拟环境：先运行 `python -m venv .venv` 并激活，再安装。）

### 输出

输出文件位于 APK 所在目录下、与 APK 同名的文件夹中：

```
game/                            # 游戏文件 + 反编译得到的 .rpy 脚本
android-icon_foreground.png
android-icon_background.png
android-presplash.jpg
```

### 独立 .exe 版本

**暂不提供**独立 `.exe`：打包后的可执行文件被 Windows Defender 误报为病毒（PyInstaller 类打包程序常见的误报）。请按上述方法从源码运行。

### 致谢

- unrpyc v2.0.3：https://github.com/CensoredUsername/unrpyc
- androguard：https://github.com/androguard/androguard

---

## Changelog / 更新日志

### v2.1 (2026/11/20)

**EN**
- Support APKs built by newer Ren'Py / RAPT, where `res/` file names are shortened: icons are now located through `resources.arsc` (requires androguard); older APKs still work without it
- Icons: pick the highest available density instead of only `mipmap-xxxhdpi-v4`
- Extract all `android-*.jpg/png` assets (presplash, downloading screen)
- Accept both `assets/x-game/` and `assets/game/` layouts
- Fix: the `x-` prefix was removed from anywhere in a name (e.g. `box-x-art.png` → `boart.png`); now only stripped from the start of each path component
- Fix: renaming could break when a parent folder was renamed before its children
- Extract only needed files directly from the APK (no temporary full unzip); reject unsafe paths in the archive
- Add inline script metadata for `uv run` (Python 3.9–3.14, androguard)
- Update unrpyc from v2.0.2 to v2.0.3

**中文**
- 支持新版 Ren'Py / RAPT 打包的 APK（`res/` 文件名被缩短）：通过 `resources.arsc` 定位图标（需要 androguard）；旧版 APK 无需 androguard 仍可正常还原
- 图标：自动选取最高分辨率，而不再只查找 `mipmap-xxxhdpi-v4`
- 提取所有 `android-*.jpg/png` 资源（presplash、downloading 画面）
- 同时兼容 `assets/x-game/` 与 `assets/game/` 目录结构
- 修复：之前会删除文件名中任意位置的 `x-`（如 `box-x-art.png` → `boart.png`），现仅去除每级路径开头的前缀
- 修复：父目录先于子项重命名时可能导致重命名失败
- 直接从 APK 中提取所需文件（不再完整解压到临时目录），并拒绝压缩包内的不安全路径
- 添加内联脚本元数据，支持 `uv run`（Python 3.9–3.14，androguard）
- unrpyc 由 v2.0.2 升级至 v2.0.3

### v2.0 (2025/01/31)

**EN**
- Converted script to class-based architecture
- Extracted worker function to top level for multiprocessing compatibility
- Improved logging, error handling and decompilation summary
- Maintained original unrpyc decompilation logic

**中文**
- 重构为基于类的结构
- 将 worker 函数移至顶层，以兼容多进程
- 改进日志、错误处理和反编译结果汇总
- 保留原有的 unrpyc 反编译逻辑
