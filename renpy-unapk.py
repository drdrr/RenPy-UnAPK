"""还原并反编译APK格式的RenPy游戏"""
import zipfile
import os
import shutil
import argparse
from unrpyc import *


def remove_x (dir2 : str, some_text : str) -> None:
    "递归重命名"
    names = os.listdir(dir2)

    for name in names:
        sub_path = os.path.join(dir2, name)

        if os.path.isdir(sub_path):
            remove_x(sub_path, some_text)

        name = name.replace(some_text, '')
        new_path = os.path.join(dir2, name)

        os.rename(sub_path, new_path)


    # unrpycfile = open(os.path.join(dir3, 'un.rpyc'), 'wb')
    # unrpycfile.write(unrpyccode)
    # unrpycfile.close()

def extract(apkfile : str) -> None:
    "解压apk"
    print(f"{i}正在还原……")
    with zipfile.ZipFile(apkfile) as zf:
        game_folder = os.path.join(os.getcwd(), apkfile[:-4])
        temp_folder = os.path.join(os.getcwd(), "TMP_FOR_UNAPK")
        try:
            os.makedirs(game_folder)
        except FileExistsError:
            pass
        try:
            os.makedirs(temp_folder)
        except FileExistsError:
            pass

        zf.extractall(temp_folder)

        shutil.move(os.path.join(temp_folder, 'assets', 'x-game'), game_folder)
        shutil.move(os.path.join(temp_folder, 'res', 'mipmap-xxxhdpi-v4', 'icon_background.png'), os.path.join(game_folder, 'android-icon_background.png'))
        shutil.move(os.path.join(temp_folder, 'res', 'mipmap-xxxhdpi-v4', 'icon_foreground.png'), os.path.join(game_folder, 'android-icon_foreground.png'))
        shutil.move(os.path.join(temp_folder, 'assets', 'android-presplash.jpg'), game_folder)

        tempfiles = os.listdir(temp_folder)
        for j in tempfiles:
            j_path = os.path.join(temp_folder, j)
            try:
                os.remove(j_path)
            except:
                shutil.rmtree(j_path)
        shutil.rmtree(temp_folder)

        remove_x(game_folder, 'x-')
        print(f"{i}还原完毕！")

def unrpyc(apkfile : str) -> None:
    "Code from unrpyc.main"
    parser = argparse.ArgumentParser(description="Decompile .rpyc/.rpymc files")

    parser.add_argument('-c', '--clobber', dest='clobber', action='store_false',
                        help="overwrites existing output files")

    parser.add_argument('-d', '--dump', dest='dump', action='store_true',
                        help="instead of decompiling, pretty print the ast to a file")

    parser.add_argument('-t', '--translation-file', dest='translation_file', action='store', default=None,
                        help="use the specified file to translate during decompilation")

    parser.add_argument('-T', '--write-translation-file', dest='write_translation_file', action='store', default=None,
                        help="store translations in the specified file instead of decompiling")

    parser.add_argument('-l', '--language', dest='language', action='store', default='english',
                        help="if writing a translation file, the language of the translations to write")

    parser.add_argument('--sl1-as-python', dest='decompile_python', action='store_true',
                        help="Only dumping and for decompiling screen language 1 screens. "
                        "Convert SL1 Python AST to Python code instead of dumping it or converting it to screenlang.")

    parser.add_argument('--comparable', dest='comparable', action='store_true',
                        help="Only for dumping, remove several false differences when comparing dumps. "
                        "This suppresses attributes that are different even when the code is identical, such as file modification times. ")

    parser.add_argument('--no-pyexpr', dest='no_pyexpr', action='store_true',
                        help="Only for dumping, disable special handling of PyExpr objects, instead printing them as strings. "
                        "This is useful when comparing dumps from different versions of Ren'Py. "
                        "It should only be used if necessary, since it will cause loss of information such as line numbers.")

    parser.add_argument('--tag-outside-block', dest='tag_outside_block', action='store_true',
                        help="Always put SL2 'tag's on the same line as 'screen' rather than inside the block. "
                        "This will break compiling with Ren'Py 7.3 and above, but is needed to get correct line numbers "
                        "from some files compiled with older Ren'Py versions.")

    parser.add_argument('--init-offset', dest='init_offset', action='store_true',
                        help="Attempt to guess when init offset statements were used and insert them. "
                        "This is always safe to enable if the game's Ren'Py version supports init offset statements, "
                        "and the generated code is exactly equivalent, only less cluttered.")

    parser.add_argument('--try-harder', dest="try_harder", action="store_true",
                        help="Tries some workarounds against common obfuscation methods. This is a lot slower.")

    args = parser.parse_args()

    if args.write_translation_file and not args.clobber and path.exists(args.write_translation_file):
        pass

    if args.translation_file:
        with open(args.translation_file, 'rb') as in_file:
            args.translations = in_file.read()

    # Expand wildcards
    def glob_or_complain(s):
        retval = glob.glob(s)
        if not retval:
            print("File not found: " + s)
        return retval
    filesAndDirs = list(map(glob_or_complain, [apkfile[:-4]]))
    # Concatenate lists
    filesAndDirs = list(itertools.chain(*filesAndDirs))

    # Recursively add .rpyc files from any directories passed
    files = []
    for k in filesAndDirs:
        if path.isdir(k):
            for dirpath, _, filenames in walk(k):
                files.extend(path.join(dirpath, j) for j in filenames if len(j) >= 5 and j.endswith(('.rpyc', '.rpymc')))
        else:
            files.append(k)
    
    # Check if we actually have files. Don't worry about
    # no parameters passed, since ArgumentParser catches that
    if len(files) == 0:
        print("No script files to decompile.")
        return

    files = [(args, x, path.getsize(x)) for x in files]

    # Decompile in the order Ren'Py loads in
    files.sort(key=itemgetter(1))
    results = list(map(worker, files))

    if args.write_translation_file:
        print("Writing translations to %s..." % args.write_translation_file)
        translated_dialogue = {}
        translated_strings = {}
        good = 0
        bad = 0
        for result in results:
            if not result:
                bad += 1
                continue
            good += 1
            translated_dialogue.update(magic.loads(result[0], cls_factory_75))
            translated_strings.update(result[1])
        with open(args.write_translation_file, 'wb') as out_file:
            magic.safe_dump((args.language, translated_dialogue, translated_strings), out_file)

    else:
        # Check per file if everything went well and report back
        good = results.count(True)
        bad = results.count(False)

    print("RPYC反编译完成！")

print("RenPy-UnApk：将APK格式的RenPy游戏恢复为工程文件")
print("By Koshiro, Version 1.3")
print("\n使用前请将apk文件放在本目录下\n")

allfiles = os.listdir()
apkfile = ''
for i in allfiles:
    if i.lower().endswith(".apk"):
        apkfile = i
        try:
            extract(apkfile)
            unrpyc(apkfile)
            print(f"{apkfile}还原完成！")
        except Exception as e:
            print(f"{apkfile} 还原失败。错误信息：\n{e}")

if not apkfile:
    print("没有找到apk文件。你确定文件在此目录下吗？")
# apkfile = i
    
# with zipfile.ZipFile(apkfile) as zf:
#     zf.extractall(apkfile.split(".")[0])

# gamefolder = os.path.join(os.getcwd(), apkfile.strip(".apk"))
# os.makedirs(gamefolder)

# shutil.move(os.path.join(os.getcwd(), 'assets', 'x-game'), gamefolder)
# shutil.move(os.path.join(os.getcwd(), 'res', 'mipmap-xxxhdpi-v4', 'icon_background.png'), os.path.join(gamefolder, 'android-icon_background.png'))
# shutil.move(os.path.join(os.getcwd(), 'res', 'mipmap-xxxhdpi-v4', 'icon_foreground.png'), os.path.join(gamefolder, 'android-icon_foreground.png'))
# shutil.move(os.path.join(os.getcwd(), 'assets', 'android-presplash.jpg'), gamefolder)

# tempfiles = os.listdir()
# for i in tempfiles:
#     if i == apkfile.strip(".apk") or i.endswith('.py') or i.endswith('.apk') or i.endswith('.exe'):
#         pass
#     elif not i in allfiles:
#         try:
#             os.remove(i)
#         except:
#             shutil.rmtree(i)

# remove_x(gamefolder, 'x-')
#writeunrpyc(os.path.join(gamefolder, 'game'))

input('\n按回车键退出')
