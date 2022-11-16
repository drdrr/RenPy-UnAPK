# RenPy-UnAPK
将APK格式的RenPy游戏恢复为工程文件

### 使用方法

将`RenPy-UnAPK.exe`文件和apk文件放在同一目录下，运行，输出的文件存放在`/extract`文件夹内。

完成后会在`extract/game`文件夹中生成`un.rpyc`文件，用于将`.rpyc`格式还原为`.rpy`。请用RenPy启动一次工程，然后即可把`un.rpyc`文件删除

### Features

- 提取图标、splash等
- 支持多个apk文件同时还原
- 支持rpyc反编译（应该兼容renpy 8）

### Credits

unrpyc: https://github.com/madeddy/unrpyc
