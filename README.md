# adaptive_multi-thread_crc32c_file_verify_tool
这是一款由我用python编写，通过在分享前获取文件CRC32C校验值并记录在文件中，和在接受文件之后根据记录文件比对文件CRC32C的方式，方便文件分享者和接收者确认数据完整性、正确性的工具。

开发此程序的过程和故事：https://www.52pojie.cn/thread-1925899-1-1.html

This is a tool written by me in python, which facilitates the file sharer and receiver to confirm the data integrity and correctness by obtaining the file CRC32C checksum value before sharing and recording it in the file, and comparing the file CRC32C according to the recorded file after accepting the file.

The process and story of developing this program: https://www.52pojie.cn/thread-1925899-1-1.html

【Translated with DeepL.com (free version)】


====================================================================


软件（和源码）链接：

①百度云：（拥有完整资料，包括软件自身、说明文本、操作演示视频和背景音乐欣赏，以及视频中出现的音乐文件分享）https://pan.baidu.com/s/1iBlKi5hV_kdkkzCgVjblYQ?pwd=0000

②蓝奏云：（因文件大小100M限制，只有软件自身、源码和一个说明用的txt文本文件，以及导航用的、存有百度云链接的文本文件）https://wwm.lanzouq.com/b0ny5lvuf

③没有百度云VIP账号，想要看操作演示的（或者只是想随便听听音乐打发时间的），请访问下面这个链接，到B站收看：https://www.bilibili.com/video/BV18rupeWEt7

Software (and source code) links:

① Baidu cloud disk: (with complete information, including the software itself, description of the text, operation demo video and background music to enjoy, as well as the video appeared in the music file sharing) https://pan.baidu.com/s/1iBlKi5hV_kdkkzCgVjblYQ?pwd=0000

② Lanzou cloud: (due to the file size of 100M limit, only the software itself, source code and a description of the txt text file, as well as navigation with the text file stored in the Baidu cloud link) https://wwm.lanzouq.com/b0ny5lvuf

③ no Baidu cloud VIP account, want to see the operation of the demonstration (or just want to casually listen to the music to pass the time), please visit the following link to the BiliBili video site to watch: https://www.bilibili.com/video/BV18rupeWEt7

【Translated with DeepL.com (free version)】


====================================================================


工具基于python的wmi模块获取文件路径所在磁盘的数字编号，然后基于磁盘SMART工具“smartctl.exe"根据前面获取到的磁盘数字编号，获取对应磁盘的旋转速度、接口类型、是否为SSD的SMART属性，以此判断磁盘硬件类型（固态／机械），并合理分配同时读取的文件数（线程数）。

The tool is based on python's wmi module to get the number of the disk where the file path is located, and then based on the disk SMART tool "smartctl.exe" according to the number of the disk obtained earlier, to get the corresponding disk rotational speed, interface type, whether it is an SSD SMART attributes, in order to determine the type of disk hardware (solid state / mechanical), and reasonably allocate the number of files to be read simultaneously (number of threads).

【Translated with DeepL.com (free version)】


====================================================================


①在机械硬盘（HDD）上以单线程读取文件（逐个读取文件），降低机械盘寻道压力的同时。读取、计算校验的速度也能赶上机械盘自身的连续读取大文件的速度，和知名解压软件7-zip校验CRC的速度不相上下；

②在nvme和SSD上以4线程读取文件（同时读取4个文件）。在获取一个文件夹下的多个文件（递归）CRC值的场景下，相较于7-zip和已有的大部分校验软件，速度上应该会有显著提升，可以加快校验速度，节省时间。
在我自己电脑的nvme固态盘上测试，读取速度相较原来翻了一倍。4个线程也是我多次测试所得最优线程数。

③在不能读取识别明确硬件类型的磁盘上（U盘、虚拟磁盘……），以2线程读取文件（同时读取2个文件）；

④识别磁盘硬件类型出错的情况下，以单线程运行。

① Read files in a single thread on a mechanical hard disk (HDD) (read files one by one) to reduce the mechanical disk seek pressure at the same time. The speed of reading and calculating checksums can also catch up with the mechanical disk's own speed of continuous reading of large files, and the speed of CRC checksums of the well-known decompression software 7-zip is comparable;

② Reading files with 4 threads on nvme and SSD (reading 4 files at the same time). In the scenario of getting the CRC values of multiple files (recursively) in a folder, compared to 7-zip and most of the existing verification software, there should be a significant increase in speed, which can speed up the verification and save time.
In my own computer nvme solid state disk test, read speed compared to the original doubled. 4 threads is also the optimal number of threads I have tested many times.

③Read files with 2 threads (2 files at the same time) on a disk that cannot read the disk with a clear hardware type (USB flash drive, virtual disk ......);

④ If there is an error in identifying the hardware type of the disk, run it in a single thread.

【Translated with DeepL.com (free version)】
