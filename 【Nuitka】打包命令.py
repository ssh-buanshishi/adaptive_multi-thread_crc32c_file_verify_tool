import os,sys,subprocess,shutil
software_version = "v1.21"

# 检查python版本是否在3.8以上
try:
    if sys.version_info.major < 3:
        raise Exception("Python 版本过低，至少要3.8")
    if (sys.version_info.major == 3) and (sys.version_info.minor) < 8:
        raise Exception("Python 版本过低，至少要3.8")
except Exception as e:
    print(str(e))
    print("\n")
    print("★★ 按任意键退出 ★★")
    os.system("@pause>nul")
    sys.exit(2)


# 检查是否安装Nuitka
if os.system("nuitka --help >nul 2>nul"):
    print("\n")
    print("未安装Nuitka")
    print("\n")
    print("★★ 按任意键退出 ★★")
    os.system("@pause>nul")
    sys.exit(2)




exe_output_dir = f"CRC32(C)多线程文件校验工具_{software_version}"
module_packages_layout_dir = "bin"

py_file_list = [
    "校验CRC32C.py",# 排在第一个的，进行完整打包确认
    "记录CRC32C.py",
]

# 如果新增了库，请在这边加上
module_include_list = [
    "os","sys","time","ctypes","wmi","platform",
    "win32gui","win32print","win32con",
    "my_custom_pySMART","threading","concurrent.futures",
    "crc32c","copy",
    "tkinter","tkinter.filedialog",
]

include_cmd = " ".join([f"--follow-import-to={i}" for i in module_include_list])


os.system("cls&&title 尝试用【Nuitka】打包中")
print("尝试用【Nuitka】打包")

cmd_head = f"python -m nuitka --mingw64 --standalone --windows-uac-admin --windows-icon-from-ico=icon-console.ico --show-progress --remove-output --enable-plugin=tk-inter"
try:
    for i , py in enumerate(py_file_list):
        # 排在第一个的，进行完整打包确认
        if i==0:
            cmd_line = f"{cmd_head}  {include_cmd}  --clean-cache=all  \"{py}\""
        else:
            cmd_line = f"{cmd_head}  {include_cmd}  \"{py}\""
        subprocess.run(args=cmd_line,shell=True,check=True)
except:
    print("【Nuitka】打包出错")
    print("\n")
    print("★★ 按任意键退出 ★★")
    os.system("@pause>nul")
    sys.exit(0)

try:
    print("====================================================")
    print("\n")
    print("【清理重复打包的库】")

    first_py_name = os.path.splitext(py_file_list[0])[0]
    for after_py_name in [os.path.splitext(i)[0] for i in py_file_list[1:]]:
        shutil.move(src=f"{after_py_name}.dist\\{after_py_name}.exe",dst=f"{first_py_name}.dist\\")
        shutil.rmtree(f"{after_py_name}.dist")

    os.rename(f"{first_py_name}.dist" , module_packages_layout_dir)
    os.mkdir(exe_output_dir)
    shutil.move(module_packages_layout_dir , f"{exe_output_dir}\\")

    print("\n")
    print("====================================================")
    print("\n")
    print("【复制依赖的exe和dll到可执行文件的文件夹】")

    shutil.copytree("SmartMonTools",f"{exe_output_dir}\\{module_packages_layout_dir}\\SmartMonTools\\")

    print("\n")
    print("====================================================")
    print("\n")
    print("【复制bat启动器】")

    shutil.copyfile("batch_starter\\记录CRC32C启动器.bat",f"{exe_output_dir}\\记录CRC32C启动器.bat")
    shutil.copyfile("batch_starter\\校验CRC32C启动器.bat",f"{exe_output_dir}\\校验CRC32C启动器.bat")

except Exception as e:
    os.system("title ×× 出错了 ××")
    print(f"出错了，详情：{e}")
    print("\n")
    print("★★ 按任意键退出 ★★")

else:
    os.system("title 【打包成功】")
    print(
    f"""
    打包完成，可执行文件位于当前目录下的【 {exe_output_dir} 】文件夹内

    ★★ 按任意键退出 ★★

    """
    )
finally:
    os.system("@pause>nul")
    sys.exit(0)