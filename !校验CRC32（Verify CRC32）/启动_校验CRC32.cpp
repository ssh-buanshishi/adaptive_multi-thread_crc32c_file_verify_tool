#pragma comment(linker, "/subsystem:windows /entry:mainCRTStartup")
//编译不弹黑窗的选项

#include <string.h>
#include <direct.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <winuser.h>
#include <tchar.h>


int main(void)
{
    //进入到当前路径下的“bin”文件夹 
	_chdir("bin");//一定要先进入到文件夹（设定程序的工作文件夹）再启动exe，不然窗口左上角的图标显示不出来，还有可能会有其他意想不到的问题
    
	SHELLEXECUTEINFO sei;
    ZeroMemory(&sei, sizeof(SHELLEXECUTEINFO));//使用前最好清空
    sei.cbSize = sizeof(SHELLEXECUTEINFO);//管理员权限执行，最基本的使用与 ShellExecute 类似
    sei.lpVerb = _T("runas");
    sei.lpFile = _T("校验CRC32.exe");
    sei.nShow = SW_SHOWNORMAL;
    sei.fMask = SEE_MASK_FLAG_NO_UI;//出现错误，不在函数执行中显示错误消息框，比如不会弹出找不到文件之类的窗口，直接返回失败。防止在后面重复弹出错误消息。 
    
	if (!ShellExecuteEx(&sei))
    {
        DWORD dwStatus = GetLastError();
        
		if (dwStatus == ERROR_CANCELLED)
        {
            //printf("提升权限被用户拒绝\n");
            MessageBox(
				NULL,
				(LPCTSTR)"提升权限被用户拒绝",//文本
				(LPCTSTR)"starter",//标题
				MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND //“确定”按钮、“错误”图标、置顶、前台
			);
        }
        else if (dwStatus == ERROR_FILE_NOT_FOUND)
        {
            //printf("所要执行的文件没有找到\n");
            MessageBox(
				NULL,
				(LPCTSTR)"所要执行的文件没有找到",//文本
				(LPCTSTR)"starter",//标题
				MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND //“确定”按钮、“错误”图标、置顶、前台
			);
        }
        
    }

    return 0;
}


