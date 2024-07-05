# adaptive_multi-thread_crc32c_file_verify_tool
这是一款由我用python编写，通过在分享前获取文件CRC32C校验值并记录在文件中，和在接受文件之后根据记录文件比对文件CRC32C的方式，方便文件分享者和接收者确认数据完整性、正确性的工具。
This is a tool written by me in python, which facilitates the file sharer and receiver to confirm the data integrity and correctness by obtaining the file CRC32C checksum value before sharing and recording it in the file, and comparing the file CRC32C according to the recorded file after accepting the file.
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
