import os,sys,subprocess,shutil

try:
    # 检查python版本是否在3.8以上
    if sys.version_info.major < 3:
        raise Exception("Python 版本过低，至少要3.8")
    if (sys.version_info.major == 3) and (sys.version_info.minor) < 8:
        raise Exception("Python 版本过低，至少要3.8")
    
    print("为了exe和依赖项的文件布局的需要，\n检查pyinstaller版本是否支持命令【--contents-directory=】中……\n\n")
    
    # 检查pyinstaller版本是否在6.1.0及以上
    # 获取命令行结果
    stdout, stderr = b"",b""
    process = subprocess.Popen(args="pyinstaller --version", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # 获取命令输出结果
    stdout, stderr = process.communicate()
    if process.returncode or stderr:
        raise Exception("运行【pyinstaller --version】命令时出错，检查是否安装了pyinstaller")
    if not stdout:
        raise Exception("pyinstaller运行【--version】命令时未输出结果")
    # 转换输出结果和判断版本
    version_num_list = stdout.decode("utf-8",errors="replace").strip().split(".")
    if (len(version_num_list) < 3):
        raise Exception("pyinstaller版本输出不正常，分割点小于3个")
    for i,num in enumerate(version_num_list):
        if not num.isdigit():
            raise Exception("pyinstaller版本输出不正常，分割点之间出现非数字")
        else:
            version_num_list[i] = int(num)
    if version_num_list[0] < 6:
        raise Exception("pyinstaller版本过低，至少要达到6.1.0")
    elif version_num_list[0] == 6 and version_num_list[1] < 1:
        raise Exception("pyinstaller版本过低，至少要达到6.1.0")
    
except Exception as e:
    print(str(e))
    print("\n")
    print("★★ 按任意键退出 ★★")
    os.system("@pause>nul")
    sys.exit(2)



exe_output_dir = "CRC32(C)多线程文件校验工具_v1.2"
module_packages_layout_dir = "bin"

py_file_list = [
    "记录CRC32C.py",# 排在第一个的，进行完整打包确认
    "校验CRC32C.py",
]

# 如果新增了库，请在这边加上
module_include_list = [
    "os","sys","time","ctypes","wmi","platform",
    "win32gui","win32print","win32con",
    "my_custom_pySMART","threading","concurrent.futures",
    "crc32c","copy",
    "tkinter","tkinter.filedialog",
]

# all_include_cmd = " ".join([(f"--collect-all {i}") for i in module_include_list])
include_cmd = \
    " ".join([(f"--collect-data {i}") for i in module_include_list]) + " " \
    + " ".join([(f"--collect-binaries {i}") for i in module_include_list])



os.system("cls&&title 尝试用【pyinstaller】打包中")
print("开始用【pyinstaller】打包")

cmd_head = f"pyinstaller --onedir --console --icon icon-console.ico --uac-admin --debug noarchive --contents-directory=\"{module_packages_layout_dir}\""
try:
    for i , py in enumerate(py_file_list):
        # 排在第一个的，进行完整打包确认
        if i==0:
            cmd_line = f"{cmd_head}  {include_cmd}  --clean  \"{py}\""
        else:
            cmd_line = f"{cmd_head}  --clean  \"{py}\""
        subprocess.run(args=cmd_line,shell=True,check=True)
except:
    print("pyinstaller打包出错")
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
        shutil.move(src=f"dist\\{after_py_name}\\{after_py_name}.exe",dst=f"dist\\{first_py_name}\\")
        shutil.rmtree(f"dist\\{after_py_name}")

    shutil.move(f"dist\\{first_py_name}",".\\")
    os.rename(first_py_name , exe_output_dir)
    shutil.rmtree("dist")

    print("\n")
    print("====================================================")
    print("\n")
    print("【清理无用文件】")

    shutil.rmtree("build")
    [os.remove(i) for i in os.listdir() if (os.path.isfile(i) and i.endswith(".spec"))]

    print("\n")
    print("====================================================")
    print("\n")
    print("【复制依赖的exe和dll到可执行文件的文件夹】")

    shutil.copytree(f"SmartMonTools",f"{exe_output_dir}\\SmartMonTools\\")

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



