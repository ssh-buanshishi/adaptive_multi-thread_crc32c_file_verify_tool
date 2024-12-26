import os , sys , time , ctypes , platform , threading , concurrent.futures
import win32gui, win32print, win32con
import tkinter , tkinter.filedialog
from copy import copy

import crc32c , wmi
from my_custom_pySMART import Device


# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝【环境检测】＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# 是否为win10及以上
win10_up = "10." in platform.version()
# 设置控制台黑窗尺寸
os.system("mode con cols=130 lines=35")
# 告诉操作系统使用程序自身的dpi适配
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        ctypes.windll.User32.SetProcessDPIAware()
    except:
        pass
# 获取屏幕的缩放比例
hDC = win32gui.GetDC(0)
dpi1 = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
dpi2 = win32print.GetDeviceCaps(hDC, win32con.HORZRES)
scale_factor = int(round(dpi1/dpi2 , 2) * 100)



#  程序所在文件夹
program_dir = os.path.dirname(sys.argv[0])
# 添加程序所在文件夹的路径到临时环境变量，方便运行smartctl
# 如果不是以分隔符结尾，要补上分隔符“;”，
if not (os.environ['PATH']).endswith(";"):
    os.environ['PATH'] += ";"
os.environ['PATH'] += f"{program_dir}\\SmartMonTools\\;"
    




# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝【配置】＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝

# 显示内容的刷新间隔
if win10_up:
    refresh_time = 0.1
else:
    refresh_time = 0.5

# 同时显示进度条的数量
bars_at_a_time = 6
# 文件大小（字节）的显示长度
file_size_display_length = 12
# 线程数：同时最多有几个文件在读取和计算CRC32
#  固态
thread_num_for_ssd = 4
#  机械
thread_num_for_hdd = 1
#  其他未知（可能为U盘）
thread_num_for_other = 2
#  获取失败时的线程数
thread_num_for_error = 1

#  记录和校验的输出文件
rec_output_file = ".\\checksum.crc32c"
verify_output_file = ".\\_校验结果_.txt"
#  可能出现的记录文件
possible_rec_files = (
    ".\\checksum.crc32c",
    ".\\checksum.crc32c.txt",
    ".\\_文件CRC32校验值_.txt",
    ".\\_crc32c_checksum_.txt",
    ".\\_文件CRC32(C)校验值_.txt",
    ".\\_文件CRC32C校验值_.txt",
)
#  可能出现的校验结果文件
possible_vrf_files = (
    ".\\_校验结果_.txt",
    ".\\校验结果.txt",
)



# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝【函数】＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝

def handle_error(text_info:str) -> None:
    text_info = text_info.replace("\n"," ｜ ")
    os.system(f"cls&&title {text_info}")
    # 闪烁屏幕
    for _ in range(2):
        time.sleep(0.1)
        os.system("color 0F")
        time.sleep(0.1)
        os.system("color EC")
    print(f"\n\n\n\n\n     {text_info}\n\n\n\n\n按任意键结束。")
    os.system("@pause>nul")
    sys.exit(2)

def delay_end() -> None:
    global in_progress
    time.sleep(0.6)
    in_progress = False
    return


if win10_up:
    def progress_cleaner() -> None:
        global progress_dict
        delete_keys = []
        
        while in_progress:
            delete_keys.clear()

            copied_progress_dict = copy(progress_dict)

            for task in copied_progress_dict:
                if (finish_timestamp := copied_progress_dict[task][2]) and (time.time() - finish_timestamp > refresh_time):
                    delete_keys.append(copy(task))
            
            for key in delete_keys:
                del progress_dict[key]
            
            time.sleep(refresh_time)
        
        return
else:
    def progress_cleaner() -> None:
        global progress_dict
        delete_keys = []
        
        while in_progress:
            delete_keys.clear()

            copied_progress_dict = copy(progress_dict)

            for task in copied_progress_dict:
                if (finish_timestamp := copied_progress_dict[task][2]) and (time.time() - finish_timestamp > refresh_time):
                    delete_keys.append(copy(task))
            
            for key in delete_keys:
                del progress_dict[key]
            
            time.sleep(refresh_time/2)
        
        return



# 只有win10及以上支持“\033c”清屏，win7需要调用“cls”
if win10_up:

    def progress_printer() -> None:

        while in_progress:
            copied_dict = copy(progress_dict)

            progress_left = len(copied_dict)
            progress_completed = file_total-progress_left
            if file_total:
                main_percent = int( progress_completed/file_total*100 )
            else:
                main_percent = 100
            
            content_list = [
                "＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝\n",
                "\n",
                "    处理中，如需暂停或终止，请直接点击右上角的红色关闭按钮。\n",
                "    处理过程中是不会写出文件或者有其他影响的，尽管放心点击右上角关闭按钮。\n",
                "    不要尝试键盘上的【Pause】和【Ctrl + C】键，方法无效，估计是因为多线程的缘故。\n",
                "\n",
                "                 ☆★            总进度 :  " ,
                (f"{progress_completed}／{file_total}").rjust( 2*len(str(file_total)) + 2 , " " ) ,
                "  ("     , str(main_percent).rjust(3," ") , " % )             ★☆                 " , "\n",
                
                "［ ",  "▋"*main_percent,  " "*(100-main_percent),  " ］", "\n",

                "＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝","\n",
                "\n",
                "\n",
            ]

            i = 0
            for task in copied_dict:
                i += 1
                if (i > bars_at_a_time):
                    break

                filesize , readed_size , _  = copied_dict[task]
                
                displayed_filesize , displayed_readed_size = \
                    str(filesize)[0:file_size_display_length] , str(readed_size)[0:file_size_display_length]
                if filesize:
                    percent_num = int(readed_size/filesize*100)
                else:
                    percent_num = 100
                    #displayed_readed_size = displayed_filesize = "0"
                
                
                content_list.extend([
                    task,"\n",
                    "  >> >> >>  ",  (f"{displayed_readed_size}／{displayed_filesize}").rjust( (2*file_size_display_length + 2) , " " ),    "  ( " , str(percent_num).rjust(3," ") , " % )", "\n" ,
                    "［ ",  "▋"*percent_num,  " "*(100-percent_num),  " ］", "\n",
                ])

        
            if progress_left > bars_at_a_time:
                content_list.append(f"\n\n             ······  ······ 此处省略 {progress_left - bars_at_a_time} 个文件进度条 ······  ······             ")
            
            # 清屏控制码："\033c"
            sys.stdout.write("\033c" + "".join(content_list))
            sys.stdout.flush()
            
            # 0.06s是上面这些运算过程大致需要的时间
            time.sleep(refresh_time-0.06)
        
        return

else:

    def progress_printer() -> None:

        while in_progress:
            copied_dict = copy(progress_dict)

            progress_left = len(copied_dict)
            progress_completed = file_total-progress_left
            if file_total:
                main_percent = int( progress_completed/file_total*100 )
            else:
                main_percent = 100
            
            content_list = [
                "＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝\n",
                "\n",
                "    处理中，如需暂停或终止，请直接点击右上角的红色关闭按钮。\n",
                "    处理过程中是不会写出文件或者有其他影响的，尽管放心点击右上角关闭按钮。\n",
                "    不要尝试键盘上的【Pause】和【Ctrl + C】键，方法无效，估计是因为多线程的缘故。\n",
                "\n",
                "                 ☆★            总进度 :  " ,
                (f"{progress_completed}／{file_total}").rjust( 2*len(str(file_total)) + 2 , " " ) ,
                "  ("     , str(main_percent).rjust(3," ") , " % )             ★☆                 " , "\n",
                
                "［ ",  "="*main_percent,  " "*(100-main_percent),  " ］", "\n",

                "＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝","\n",
                "\n",
                "\n",
            ]

            i = 0
            for task in copied_dict:
                i += 1
                if (i > bars_at_a_time):
                    break

                filesize , readed_size , _  = copied_dict[task]
                
                displayed_filesize , displayed_readed_size = \
                    str(filesize)[0:file_size_display_length] , str(readed_size)[0:file_size_display_length]
                if filesize:
                    percent_num = int(readed_size/filesize*100)
                else:
                    percent_num = 100
                    #displayed_readed_size = displayed_filesize = "0"
                
                
                content_list.extend([
                    task,"\n",
                    "  >> >> >>  ",  (f"{displayed_readed_size}／{displayed_filesize}").rjust( (2*file_size_display_length + 2) , " " ),    "  ( " , str(percent_num).rjust(3," ") , " % )", "\n" ,
                    "［ ",  "="*percent_num,  " "*(100-percent_num),  " ］", "\n",
                ])

        
            if progress_left > bars_at_a_time:
                content_list.append(f"\n\n             ······  ······ 此处省略 {progress_left - bars_at_a_time} 个文件进度条 ······  ······             ")
            
            # 传统清屏
            os.system("cls")
            sys.stdout.write("".join(content_list))
            sys.stdout.flush()
            
            
            time.sleep(refresh_time)
        
        return

def sort_progress_by_filesize(src_dict: dict) -> dict:
    if thread_num > 1:
        # 大文件在前，之后速度越来越快。多线程下空闲时间似乎会少一点。
        tmp_list = sorted(src_dict.items(), key=lambda x: x[1][0] ,reverse=True)
        return dict(tmp_list)
    else:
        # 单线程不做处理
        return src_dict



def calc(task_file: str) -> tuple:
    global progress_dict
    global file_error
    
    
    try:
        result = 0
        crc32c_handle = crc32c.CRC32CHash(gil_release_mode=1)

        with open(task_file , mode="rb") as file_handle:

            # 只要文件没读完，就不断迭代结果自身。
            #   一次read的字节大小理论上可以随便选，因为大部分文件的大小不是一次读取的大小的整数倍，总会多出或少掉几个字节，
            #   而且看网上资料说，这个函数还可以传入字符串，字符串的长度就更随意了，所以可以放心一次读取的长度应该不会影响到最终结果。
            #  
            #   取“1048576（1 MiB）”是出于性能考虑，我使用ATTO测试过，我的nvme盘在传输大小（块大小）为1 MiB到2 MiB时，
            #   未勾选“直接传输”的读取速率差不多达到最大，估计其他固态和机械盘应该也差不多
            #   “直接传输”据我估计是带上系统自身调度和缓冲特性的操作，和勾上后用到的底层操作，也就是硬件层面类似磁盘碎片整理软件里看到的“directwrite”操作正好相对。
            #   python读取文件的函数到不了底层，所以得去掉这个勾。
            #   恰好这个数字和1024关系很直接，感觉非常不错，所以就定为了“1048576（1 MiB）”
            #  
            #   突然想到固态盘里，闪存单元的块大小是不是也是这么大？不过感觉应该要比1 MiB小吧。
            #
            # 【2024年12月24日补充】：crc32c模块添加了在计算时释放GIL锁的特性，缓冲区buf越大越有利
            #     目前的PCIE4.0固态和将来的固态速度会越来越快，
            #     此crc32c库单线程条件下的校验速率约为 15-20 Gib/s （使用随机值生成的 1 GiB 内存缓冲作的测试）
            #     所以为了“战未来”，GIL锁释放的特性很有必要加入
            
            while buf := file_handle.read(2097152): # 2 × 1024 × 1024 = 2097152（2 MiB）
                crc32c_handle.update(buf)
                # 更新已读取计数
                progress_dict[task_file][1] += len(buf)
        
        result = crc32c_handle.checksum
    
    except:
        value_reliable = False
        file_error.append(copy(task_file))
    
    else:
        value_reliable = True
    
    finally:
        #打上完成时间戳
        progress_dict[task_file][2] = time.time()
        return (task_file , str(result).zfill(10) , value_reliable)


def allocate_thread_num_by_disk_hardware_type() -> tuple:
    # 获取硬盘分区和磁盘号的关联
    section_to_physical_disk_dict = dict()
    for physical_disk in wmi.WMI().Win32_DiskDrive():
        for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                #print("|".join([physical_disk.Caption, partition.Caption, logical_disk.Caption]))
                section_to_physical_disk_dict[logical_disk.DeviceID] = physical_disk.Index
    
    # 获取程序所在目录的盘符，寻找对应的磁盘号
    section = os.path.splitdrive(os.getcwd())[0]
    #print(f"所在盘符为：【{section}】")

    # 获取所在的磁盘号
    disk_index = section_to_physical_disk_dict.get(section)
    #print(f"磁盘号为：【{disk_index}】")
    #print("\n")

    if disk_index != None:
        handle = Device(f'/dev/pd{disk_index}')
        spin , slot , is_SSD = handle.rotation_rate , handle.interface , handle.is_ssd
        #print(f"旋转速度：{spin}")
        #print(f"接口：【{slot}】")
        #print(f"是否为SSD：{is_SSD}")
        #print("\n")
        if spin:
            #print("硬件类型：机械硬盘")
            disk_type = "HDD"
            allocated_thread_num = thread_num_for_hdd
        elif (slot == "nvme") or is_SSD :
            #print("硬件类型：固态硬盘")
            disk_type = "SSD"
            allocated_thread_num = thread_num_for_ssd
        else:
            #print("硬件类型：未知，无旋转速度，可能为U盘")
            disk_type = "other"
            allocated_thread_num = thread_num_for_other
    else:
        #print("获取磁盘号失败")
        disk_type = "error"
        allocated_thread_num = thread_num_for_error
    
    return (allocated_thread_num , disk_type)


# 预分配磁盘空间的写入文件方式，能极大减少输出的文件碎片
def pre_allocate_write_output_file(output_path:str , data:str , encoding="utf-8-sig") -> None:
    
    # 覆盖，不然fsutil会报错，不能创建
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except:
            raise Exception(f"文件【{output_path}】已存在且删除失败，无法预分配空间")
    
    if isinstance(data , str):
        data = "\r\n".join(data.splitlines()) # 换成CRLF
        data = data.encode(encoding=encoding , errors="replace")
        
        if (ret := os.system(f"fsutil file createNew \"{output_path}\" {len(data)} >nul")):
            raise Exception(f"无法给【{output_path}】预分配空间")
        
        with open(output_path,mode="br+",buffering=0) as f:
            f.write(data)
    
    else:
        raise Exception("第二个参数data类型错误")
    
    
    # 无返回值
    return



# # # # # # # # # # # # # # # 初始化变量 # # # # # # # # # # # # # # #

progress_dict = dict()
result_list = []
#file_passed = 0
file_error  = []
#file_corrupted  = []
in_progress = True

# # # # # # # # # # # # # # # 初始化变量 # # # # # # # # # # # # # # # 



'''
        ........       .......                    .....                                                       
        =@@@@@@@.     ,@@@@@@@                    =@@@@                                                       
        =@@@@@@@^     /@@@@@@@                    =@@@@                                                       
        =@@@@@@@@.   =@@@@@@@@      .]]]]]]`              .]]]`  ,]]]].                                       
        =@@@@=@@@^   @@@@=@@@@    /@@@@@@@@@@@.   =@@@@   =@@@@/@@@@@@@@`                                     
        =@@@@.@@@@. =@@@^=@@@@   /@@@/` .,@@@@^   =@@@@   =@@@@@/. ,@@@@@.                                    
        =@@@@.=@@@\ @@@@.=@@@@          ,]/@@@@   =@@@@   =@@@@^    =@@@@.         ,]]]]]]]]]]]]]]]]]]]`      
        =@@@@. @@@@/@@@^ =@@@@    ,@@@@@@@@@@@@   =@@@@   =@@@@.    =@@@@.         \@@@@@@@@@@@@@@@@@@@@.     
        =@@@@. =@@@@@@@. =@@@@  .@@@@@/[`.=@@@/   =@@@@   =@@@@.    =@@@@.                           =@@^     
        =@@@@.  @@@@@@^  =@@@@  =@@@@`   ,@@@@\   =@@@@   =@@@@.    =@@@@.                           =@@^     
        =@@@@.  =@@@@@.  =@@@@   \@@@@@@@@@@@@@   =@@@@   =@@@@.    =@@@@.                        @@@@@@@@@@  
        ,@@@@.   @@@@/   =@@@@    ,\@@@@[` \@@@^  =@@@O   ,@@@@.    ,@@@@.                        ,@@@@@@@@`  
                                                                                                   =@@@@@@^   
                                                                                                    @@@@@@    
                                                                                                    .@@@@^    
                                                                                                     =@@/     
                                                                                                      \@.     
                                                                                                       `      
'''
# 检查管理员权限
if not bool(ctypes.WinDLL("shell32.dll").IsUserAnAdmin()):
    handle_error("未取得管理员权限。如本文件为.py脚本文件，请以管理员身份运行")

# 检查组件
os.system("title 检查组件中")
if os.system("smartctl --version >nul 2>nul"):
    handle_error("组件【smartctl.exe】缺失")

# 接受文件夹路径
os.system("title 接受文件夹路径中")
if (len(sys.argv) == 2) and os.path.isdir(sys.argv[1]):
    os.chdir(sys.argv[1])
elif (len(sys.argv) > 2):
    handle_error("命令行参数过多，仅接受1个文件夹路径作为参数")
else:
    # 创建一个Tkinter窗口
    root = tkinter.Tk()
    # 设置程序缩放
    if scale_factor != 100:
        root.tk.call('tk', 'scaling', scale_factor/75)
    # 隐藏根窗口，只显示对话框
    root.withdraw()
    # 打开文件夹选择对话框
    initial_dir = os.path.splitdrive(program_dir)[0]
    folder = tkinter.filedialog.askdirectory(
        initialdir=f"{initial_dir}\\" ,
        parent=root ,
        title="请选择需要记录CRC32(C)的文件夹"
    )
    # 关掉窗口实例
    root.destroy()

    if os.path.isdir(folder):
        os.chdir(folder)
    else:
        handle_error("未选择文件夹，或文件夹不存在。")

# 分配线程数，获取磁盘硬件类型
os.system("title 获取磁盘硬件类型中")
thread_num , disk_hardware_type = allocate_thread_num_by_disk_hardware_type()

os.system("title 获取当前目录下所有文件的路径中")
# 获取文件
file_set = []
for root , foldersets , filesets in os.walk("."):
    for file in filesets:
            file_set.append(f"{root}\\{file}")

# 排除自身产生的记录文件
for rec_file in possible_rec_files:
    try:
        file_set.remove(rec_file)
    except:
        pass
for vrf_file in possible_vrf_files:
    try:
        file_set.remove(vrf_file)
    except:
        pass


# 初始化进度信息
for file in file_set:
    try:
        size = os.path.getsize(file)
    except:
        size = 0
    
    
    progress_dict[copy(file)] = [
        #0 【int】 文件大小
        copy(size),

        #1 【int】 已读取大小
        0,

        #2 【None|float】完成时间戳
        None,
    ]

# 按文件大小倒序排列任务表
progress_dict = sort_progress_by_filesize(progress_dict)
file_total = len(progress_dict)
# 启动清理线程
progress_clean_thread = threading.Thread(target=progress_cleaner)
progress_clean_thread.start()
# 启动显示线程
display_thread = threading.Thread(target=progress_printer)
display_thread.start()


os.system(f"title 磁盘为：{disk_hardware_type} ｜ 文件并发数：{thread_num} ｜ 处理器CRC32C(SSE4.2)指令支持：{crc32c.hardware_based}")
# 创建线程池，最大线程数设置为thread_num 
with concurrent.futures.ThreadPoolExecutor(max_workers = thread_num) as executor:  
    # 提交任务到线程池执行，并获取Future对象列表  
    futures = [executor.submit(calc, i) for i in copy(progress_dict)]
      
    # 遍历Future对象列表，获取任务结果  
    for future in concurrent.futures.as_completed(futures):  
        result_list.append(future.result())

# 启动延迟结束显示线程
delay_thread = threading.Thread(target=delay_end)
delay_thread.start()
# 等待所有线程结束
delay_thread.join() , display_thread.join() , progress_clean_thread.join()

    
result_list.sort(key=lambda x:x[0])
try:
    tmp = "\n".join(  [ ">>>>>".join(i[0:2]) for i in result_list if i[2] ]  )
    pre_allocate_write_output_file(output_path=rec_output_file , data=tmp , encoding="utf-8-sig")
except Exception as e:
    handle_error(f"CRC32写入出错，详情：{e}。")


tmp = ""
if file_error:
    tmp += "".join(["读取失败的文件：" , "\n    " , "\n    ".join(file_error) , "\n"])
os.system("cls")
sys.stdout.write(
    "".join([
        "\n\n",
        "===================================","\n",
        "\n",
        tmp,
        "\n\n",
        "☆★    处理完成    ☆★",
        "\n\n",
        f"CRC32值已写入目标文件夹下的【{rec_output_file}】文件中。",
        "\n",
        "按任意键结束",
        "\n",
    ])
)
sys.stdout.flush()

os.system("@pause>nul")
sys.exit(0)

