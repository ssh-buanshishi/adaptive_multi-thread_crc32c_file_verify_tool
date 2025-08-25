# 标准库
import os, sys, time, ctypes, msvcrt, io, platform, threading, concurrent.futures
import tkinter , tkinter.filedialog
from copy import copy
from contextlib import suppress
# 第三方库
import win32gui, win32print, win32con, win32file, psutil
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

# 线程锁
#file_passed_lock = threading.Lock()
#file_corrupted_lock = threading.Lock()
file_error_lock = threading.Lock()
#possible_moved_file_dict_lock = threading.Lock()

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

# 只有win10及以上支持清屏控制码"\033c"，win7、win8都只能用传统的cls清屏
if win10_up:
    refresh_time = 0.1 #"\033c"快速清屏不会闪烁，因此刷新时间能达到0.1秒
    actual_sleep_time = refresh_time - 0.02 # 0.02秒是sleep函数前面这些过程大概需要花费的时间，需要算进去
    
    def progress_manager() -> None:
        global progress_dict

        while in_progress:

            # 本意是：拷贝一次进度字典到线程独立的内存空间，线程就可以单独处理，
            # 不需要再访问全局变量，减少“干扰”
            # 就是不知道python的copy靠不靠谱，毕竟python是根据“值”来管理内存的
            copied_progress_dict = copy(progress_dict)
            
            
            # 计算、收集总进度
            progress_left = len(copied_progress_dict)
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

            # 由于任务的提交顺序和字典用for遍历的顺序相同，
            # 且跟据观察，完成读取任务的文件总是排在最前面，
            # 所以不用完全遍历整个字典，恰当的时候break能提高性能
            
            print_switch = True #打印开关
            continuous_blank_counting = 0 # 结束时间为None的任务连续计数

            # enumerate返回的是生成器对象，是惰性的，因此下面的for循环不会加载整个字典
            for i,task in enumerate(copied_progress_dict,start=1):

                filesize , readed_size , finish_timestamp  = copied_progress_dict[task]
                
                # 一、清理已完成的
                if finish_timestamp:
                    continuous_blank_counting = 0 # 计数清零
                    if (time.time() - finish_timestamp > refresh_time):
                        del progress_dict[task]
                else:
                    continuous_blank_counting += 1
                
                # 连续10个文件进度没有结束时间，就可以退出循环了，
                # 下面基本不会有完成的进度了
                if continuous_blank_counting > 10:
                    break
            
                # 二、计算、收集各个文件的进度
                if print_switch:

                    if (i > bars_at_a_time):
                        print_switch = False
                        continue
                    
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

            time.sleep(actual_sleep_time)
        
        return

else:
    refresh_time = 0.5 #传统的cls清屏会闪烁，所以刷新时间得放宽些（0.5秒）
    actual_sleep_time = refresh_time - 0.02 # 0.02秒是sleep函数前面这些过程大概需要花费的时间，需要算进去
    
    def progress_manager() -> None:
        global progress_dict

        while in_progress:

            # 本意是：拷贝一次进度字典到线程独立的内存空间，线程就可以单独处理，
            # 不需要再访问全局变量，减少“干扰”
            # 就是不知道python的copy靠不靠谱，毕竟python是根据“值”来管理内存的
            copied_progress_dict = copy(progress_dict)
            
            
            # 计算、收集总进度
            progress_left = len(copied_progress_dict)
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

            # 由于任务的提交顺序和字典用for遍历的顺序相同，
            # 且跟据观察，完成读取任务的文件总是排在最前面，
            # 所以不用完全遍历整个字典，恰当的时候break能提高性能
            
            print_switch = True #打印开关
            continuous_blank_counting = 0 # 结束时间为None的任务连续计数

            # enumerate返回的是生成器对象，是惰性的，因此下面的for循环不会加载整个字典
            for i,task in enumerate(copied_progress_dict,start=1):

                filesize , readed_size , finish_timestamp  = copied_progress_dict[task]
                
                # 一、清理已完成的
                if finish_timestamp:
                    continuous_blank_counting = 0 # 计数清零
                    if (time.time() - finish_timestamp > refresh_time):
                        del progress_dict[task]
                else:
                    continuous_blank_counting += 1
                
                # 连续10个文件进度没有结束时间，就可以退出循环了，
                # 下面基本不会有完成的进度了
                if continuous_blank_counting > 10:
                    break
            
                # 二、计算、收集各个文件的进度
                if print_switch:

                    if (i > bars_at_a_time):
                        print_switch = False
                        continue
                    
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

            time.sleep(actual_sleep_time)
        
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
        with file_error_lock:
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


def win_preallocate_newfile(
    # 日常使用参数
    file:str, size:int, exist_ok:bool=False,
    buffering:int=-1,
    text_mode:bool=False, encoding:str="utf-8-sig", 
    errors=None, newline="\r\n",
) -> io.BytesIO:

    # 分区名
    drive_name = os.path.splitdrive(os.path.abspath(file))[0] + "\\"
    # 文件系统
    fs_type = tmp if ( tmp := (fs_info_dict.get(drive_name))[0] ) else ""
    new_fs = True if (fs_type in {"NTFS","ReFS"}) else False
    # 簇大小
    cluster_size = tmp if ( tmp := (fs_info_dict.get(drive_name))[-1] ) else 1
    # 与簇大小对齐的文件分配空间
    al_size = (size + (cluster_size - remain_size)) if (remain_size := size%cluster_size) else size

    # 检查文件是否已经存在
    if os.path.isfile(file) and (not exist_ok):
        raise Exception("文件已存在，且未设置覆盖")
    
    
    # 上面为止文件都没有正式打开
    # 下面套个try是为了方便在失败时关掉句柄和删除残留
    try:
        # 打开一个python文件句柄
        if text_mode:
            py_fh = open(file, mode="wt+", encoding=encoding, buffering=buffering, errors=errors, newline=newline)
        else:
            py_fh = open(file, mode="wb+", buffering=buffering)
        
        # 转换为windows的句柄方便操作
        win_hf = msvcrt.get_osfhandle(py_fh.fileno())
        
        # 设置文件的磁盘分配空间
        win32file.SetFileInformationByHandle(win_hf , win32file.FileAllocationInfo , al_size)
        
        # 根据上面的配置结果，选择是否在一开始就移动EOF至文件的分配大小
        if new_fs:
            # 移动EOF至分配的文件大小
            # 虽然EOF的大小（文件大小）不需要对齐簇大小，
            # 不过这里设置成对齐簇大小的al_size，多一丢丢文件的实际大小，问题也不大
            win32file.SetFileInformationByHandle(win_hf , win32file.FileEndOfFileInfo , al_size)

    except Exception as x:
        e = copy(x) # 如果不找个新变量copy过来，下面的with suppress(Exception)会使存储异常的变量“人间蒸发”
        with suppress(Exception): py_fh.close()
        with suppress(Exception): os.remove(file)
        raise e
    
    return py_fh 



# 预分配磁盘空间的写入文件方式，能极大减少输出的文件碎片
def pre_allocate_write_output_file(output_path:str , data:str , encoding="utf-8-sig") -> None:

    if isinstance(data , str):
        data = "\r\n".join(data.splitlines()) # 换成CRLF
        data = data.encode(encoding=encoding , errors="replace")
        
        with win_preallocate_newfile(output_path, len(data), exist_ok=True) as f:
            f.write(data)
            f.truncate()
    
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
#file_not_in_record = set()
#file_disappear = set()
#possible_moved_file_dict = dict()#存放可能移动的文件，以crc32c值为键，文件路径的列表为值
in_progress = True

# 文件系统信息
fs_info_dict = dict()
for partition in psutil.disk_partitions(all=True):
    section = getattr(partition,"mountpoint","") # 盘符
    fs_type = getattr(partition,"fstype","") # 文件系统类型
    try:
        # 获取每扇区字节数，和每簇的扇区数
        sectors_per_cluster , bytes_per_sector , _ ,_ =win32file.GetDiskFreeSpace(section)
    except:
        cluster_size = 0
    else:
        # 相乘得到簇大小
        cluster_size = bytes_per_sector * sectors_per_cluster
    
    fs_info_dict[copy(section)]=(copy(fs_type) , copy(cluster_size))

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
# 获取当前实际的文件列表（集合）
current_file_set = set()
for root , foldersets , filesets in os.walk("."):
    for file in filesets:
        current_file_set.add(f"{root}\\{file}")

# 排除自身产生的记录文件
for rec_file in possible_rec_files:
    current_file_set.discard(rec_file)
for vrf_file in possible_vrf_files:
    current_file_set.discard(vrf_file)


# 初始化进度信息
for file in current_file_set:
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
# 启动进度显示和清理的线程
progress_manager_thread = threading.Thread(target=progress_manager)
progress_manager_thread.start()


os.system(f"title 磁盘为：{disk_hardware_type} ｜ 文件并发数：{thread_num} ｜ 处理器CRC32C(SSE4.2)指令支持：{crc32c.hardware_based}")
# 创建线程池，最大线程数设置为thread_num 
with concurrent.futures.ThreadPoolExecutor(max_workers = thread_num) as executor:  
    # 提交任务到线程池执行，并获取Future对象列表
    # 如果要用.keys()，需要用列表推导式，因为.keys()返回的应该是生成器对象，会卡住不动
    futures = [executor.submit(calc, i) for i in [i for i in progress_dict.keys()]]
      
    # 遍历Future对象列表，获取任务结果  
    for future in concurrent.futures.as_completed(futures):  
        result_list.append(future.result())
del futures
# 启动延迟结束显示线程
delay_thread = threading.Thread(target=delay_end)
delay_thread.start()
# 等待所有线程结束
delay_thread.join()
progress_manager_thread.join()
# 删掉省点内存
del progress_dict
    
result_list.sort(key=lambda x:x[0])
try:
    tmp = "\n".join(  [ ">>>>>".join(i[0:2]) for i in result_list if i[2] ]  )
    del result_list
    pre_allocate_write_output_file(output_path=rec_output_file , data=tmp , encoding="utf-8-sig")
except Exception as e:
    handle_error(f"CRC32C记录写入出错，详情：{e}。")


tmp = ""
if file_error:
    tmp += "".join(["读取失败的文件：" , "\n    " , "\n    ".join(file_error) , "\n\n"])
os.system("cls")
sys.stdout.write(
    "\n".join([
        "\n",
        "===================================","\n",
        "",
        tmp,
        "",
        "【 处理完成 】",
        "",
        f"CRC32值已写入目标文件夹下的【{rec_output_file}】文件中。",
        "",
        "★  按任意键结束  ★",
        "\n",
    ])
)
sys.stdout.flush()

os.system("@pause>nul")
sys.exit(0)

