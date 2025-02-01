# RenPy-UnAPK
将APK格式的RenPy游戏恢复为工程文件（提取+反编译）

### 使用方法

将`RenPy-UnAPK.exe`文件和apk文件放在同一目录下，运行，输出的文件存放在游戏同名文件夹内。

或者下载本仓库，在终端运行`python renpy-unapk.py`。

### Features

- 提取图标、splash等
- 支持多个apk文件同时还原
- 支持rpyc反编译（应该兼容renpy 8）

### Credits

unrpyc: https://github.com/madeddy/unrpyc


-------------

## Changelog (2025/01/31)

### Refactor RenPy APK Decompilation Tool

- Restructured unrpyc APK extraction and decompilation script
- Improved multiprocessing support for file processing
- Enhanced error handling and logging
- Maintained original unrpyc decompilation logic

### Key changes:
- Converted script to class-based architecture
- Extracted worker function to top-level for multiprocessing compatibility
- Implemented robust logging mechanism
- Improved file and directory handling
- Enhanced error reporting and summary generation

Fixes potential issues with file processing and provides a more maintainable codebase for RenPy APK decompilation.

Version bumped to 2.0
