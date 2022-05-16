import zipfile
import os
import shutil
from unrpyccode import *

def remove_x (dir2, some_text):

    names = os.listdir(dir2)

    for name in names:
        sub_path = os.path.join(dir2, name)

        if os.path.isdir(sub_path):
            remove_x(sub_path, some_text)

        name = name.replace(some_text, '')
        new_path = os.path.join(dir2, name)

        os.rename(sub_path, new_path)

def writeunrpyc(dir3):
    unrpycfile = open(os.path.join(dir3, 'un.rpyc'), 'wb')
    unrpycfile.write(unrpyccode)
    unrpycfile.close()



print("RenPy-UnApk：将APK格式的RenPy游戏恢复为工程文件")
print("By Koshiro, Version 1.0")
print("\n使用前请将apk文件放在本目录下")

allfiles = os.listdir()
apkfile = ''
for i in allfiles:
    if '.apk' in i:
        apkfile = i
with zipfile.ZipFile(apkfile) as zf:
    zf.extractall()

gamefolder = os.path.join(os.getcwd(), 'extract')
os.makedirs(gamefolder)

shutil.move(os.path.join(os.getcwd(), 'assets', 'x-game'), gamefolder)
shutil.move(os.path.join(os.getcwd(), 'res', 'mipmap-xxxhdpi-v4', 'icon_background.png'), os.path.join(gamefolder, 'android-icon_background.png'))
shutil.move(os.path.join(os.getcwd(), 'res', 'mipmap-xxxhdpi-v4', 'icon_foreground.png'), os.path.join(gamefolder, 'android-icon_foreground.png'))
shutil.move(os.path.join(os.getcwd(), 'assets', 'android-presplash.jpg'), gamefolder)

tempfiles = os.listdir()
for i in tempfiles:
    if i == 'extract' or i.endswith('.py') or i.endswith('.apk') or i.endswith('.exe'):
        pass
    else:
        try:
            os.remove(i)
        except:
            shutil.rmtree(i)

remove_x(gamefolder, 'x-')
writeunrpyc(os.path.join(gamefolder, 'game'))

print("\n生成完毕\n\n【重要事项】\n已在extract/game文件夹中生成un.rpyc文件，用于将.rpyc格式还原为.rpy。\n请用RenPy启动一次工程，然后即可把un.rpyc文件删除")
input('\n按回车键退出')
