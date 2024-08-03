# -*- coding: UTF-8 -*-

import os,sys,time,wmi
from pySMART import Device
import threading
import concurrent.futures
import crc32c
from copy import copy

# 显示内容的刷新间隔
refresh_time = 0.1
# 刷新间隔至少大于0.06s，否则下面progress_printer()减去0.06，得到sleep(0)，会卡死
if refresh_time <= 0.06:
    refresh_time = 0.07

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
rec_output_file = ".\\_文件CRC32校验值_.txt"
verify_output_file = ".\\校验结果.txt"



def delay_end() -> None:
    global in_progress
    time.sleep(0.5)
    in_progress = False
    return

def progress_cleaner() -> None:
    global progress_dict
    delete_keys = []
    
    while in_progress:
        delete_keys.clear()

        for task in progress_dict:
            finish_timestamp = progress_dict[task][2]
            if finish_timestamp and (time.time() - finish_timestamp > 1.5*refresh_time):
                delete_keys.append(copy(task))
        
        for key in delete_keys:
            progress_dict.pop(key)
        
        time.sleep(refresh_time/2-0.01)
    
    return



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
            "＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝","\n",
            
            "                 ☆★            总进度 :  " ,
            (f"{progress_completed}／{file_total}").rjust( 2*len(str(file_total)) + 2 , " " ) ,
            "  ("     , str(main_percent).rjust(3," ") , " % )             ★☆                 " , "\n",
            
            "［ ",  "▋"*main_percent,  " "*(100-main_percent),  " ］", "\n",

            "＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝　＝","\n",
            "\n",
            "\n",
        ]

        for i,task in enumerate(copied_dict):
            if (i >= bars_at_a_time):
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
                "   ▶▷▷   ",  (f"{displayed_readed_size}／{displayed_filesize}").rjust( (2*file_size_display_length + 2) , " " ),    "  ( " , str(percent_num).rjust(3," ") , " % )", "\n" ,
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

def sort_progress_by_filesize(src_dict: dict) -> dict:
    if disk_hardware_type == "SSD":
        # 大文件在前，之后速度越来越快
        tmp_list = sorted(src_dict.items(), key=lambda x: x[1][0] ,reverse=True)
        return dict(tmp_list)
    else:
        # 其他的情况不做处理
        return src_dict



def calc(task_file: str) -> tuple:
    global progress_dict
    global file_error,file_corrupted,file_passed
    
    crc32_to_be  = file_set_dict[task_file]
    
    try:
        result = 0

        file_handle = open(task_file, "rb")

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
        while buf := file_handle.read(1048576): # 1024 × 1024 = 1048576（1 MiB）
            result = crc32c.crc32c(buf,result)
            # 更新已读取计数
            progress_dict[task_file][1] += len(buf)
        file_handle.close()
    
    except:
        try:
            file_handle.close()
        except:
            pass
        output = "【打开时出错（可能是未找到）】"
        file_error.append(copy(task_file))

        crc32_result = "-FAILED-"
    
    else:
        crc32_result = str(result).zfill(10)
        
        if crc32_result == crc32_to_be:
            output = "【通过】"
            file_passed += 1
        else:
            output = "【已被修改】"
            file_corrupted.append(copy(task_file))
    
    finally:
        #打上完成时间戳
        progress_dict[task_file][2] = time.time()
        return (task_file , crc32_to_be , crc32_result , output)


def allocate_thread_num_by_disk_hardware_type() -> tuple:
    # 获取硬盘分区和磁盘号的关联
    c = wmi.WMI()
    section_to_physical_disk_dict = {}
    for physical_disk in c.Win32_DiskDrive():
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


# # # # # # # # # # # # # # # 初始化变量 # # # # # # # # # # # # # # #
 
# 分配线程数，获取磁盘硬件类型（在刚启动时的文件夹里才能调用smartctl）
os.system("title 获取磁盘硬件类型中")
thread_num , disk_hardware_type = allocate_thread_num_by_disk_hardware_type()

# 获取程序所在的相对路径
#os.chdir("..")
#exe_path = os.getcwd()
os.chdir("../..")
#cwd = os.getcwd()
#exe_path = "." + exe_path.replace(cwd , "")


progress_dict = {}
result_list = []
file_passed = 0
file_error  = []
file_corrupted  = []
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

os.system("mode con cols=120 lines=30")
os.system("title 读取记录文件中的信息中")
# 获取文件预定的CRC32信息
file_set_dict = {}
if os.path.exists(rec_output_file):
    src = open(file = rec_output_file ,mode="r",encoding="utf-8-sig")
    line_buf = (src.read()).splitlines()
    src.close()
else:
    print(f"\n\n找不到：{rec_output_file}，按任意键结束")
    os.system("@pause>nul")
    sys.exit(0)

for line in line_buf:
    tmp = line.split(">>>>>")
    file_set_dict[tmp[0]] = tmp[-1]



# 初始化进度信息
for file in file_set_dict:
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
    tmp = "".join(["\n",f"文件总数：{file_total}，通过校验的文件个数：{file_passed}，存在问题的个数：{file_total-file_passed}","\n\n"])
    if file_error:
        tmp += "".join(["打开出错或找不到的文件：" , "\n    " , "\n    ".join(file_error) , "\n\n"])
    if file_corrupted:
        tmp += "".join(["已被修改的文件：" , "\n    " , "\n    ".join(file_corrupted) , "\n\n"])
    
    tmp += "\n".join(
            ["\n","格式：【文件路径】 | 【原本的CRC32_C】 | 【目前的CRC32_C】 | 【结果】","\n"]
            + [" | ".join(i) for i in result_list]
    )
    
    f = open(file = verify_output_file ,mode="w",encoding="utf-8-sig")
    f.write(tmp)
    f.close()
except:
    print("校验结果写入出错，按任意键结束")
    os.system("@pause>nul")
    sys.exit(0)


os.system("title -----获取完成-----")
tmp = "".join([f"文件总数：{file_total}，通过校验的文件个数：{file_passed}，存在问题的个数：{file_total-file_passed}","\n\n"])
if file_error:
    tmp += "".join(["打开出错或找不到的文件：" , "\n    " , "\n    ".join(file_error) , "\n\n"])
if file_corrupted:
    tmp += "".join(["已被修改的文件：" , "\n    " , "\n    ".join(file_corrupted) , "\n"])
sys.stdout.write(
    "".join([
        "\033c",# 清屏控制码："\033c"
        "\n\n",
        "===================================","\n",
        "\n",
        tmp,
        "\n\n",
        f"校验结果已写入文件：{verify_output_file}",
        "\n",
        "按任意键结束",
        "\n",
    ])
)
sys.stdout.flush()

os.system("@pause>nul")
sys.exit(0)

