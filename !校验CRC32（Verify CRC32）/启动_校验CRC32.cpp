#pragma comment(linker, "/subsystem:windows /entry:mainCRTStartup")
//���벻���ڴ���ѡ��

#include <string.h>
#include <direct.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <winuser.h>
#include <tchar.h>


int main(void)
{
    //���뵽��ǰ·���µġ�bin���ļ��� 
	_chdir("bin");//һ��Ҫ�Ƚ��뵽�ļ��У��趨����Ĺ����ļ��У�������exe����Ȼ�������Ͻǵ�ͼ����ʾ�����������п��ܻ����������벻��������
    
	SHELLEXECUTEINFO sei;
    ZeroMemory(&sei, sizeof(SHELLEXECUTEINFO));//ʹ��ǰ������
    sei.cbSize = sizeof(SHELLEXECUTEINFO);//����ԱȨ��ִ�У��������ʹ���� ShellExecute ����
    sei.lpVerb = _T("runas");
    sei.lpFile = _T("У��CRC32.exe");
    sei.nShow = SW_SHOWNORMAL;
    sei.fMask = SEE_MASK_FLAG_NO_UI;//���ִ��󣬲��ں���ִ������ʾ������Ϣ�򣬱��粻�ᵯ���Ҳ����ļ�֮��Ĵ��ڣ�ֱ�ӷ���ʧ�ܡ���ֹ�ں����ظ�����������Ϣ�� 
    
	if (!ShellExecuteEx(&sei))
    {
        DWORD dwStatus = GetLastError();
        
		if (dwStatus == ERROR_CANCELLED)
        {
            //printf("����Ȩ�ޱ��û��ܾ�\n");
            MessageBox(
				NULL,
				(LPCTSTR)"����Ȩ�ޱ��û��ܾ�",//�ı�
				(LPCTSTR)"starter",//����
				MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND //��ȷ������ť��������ͼ�ꡢ�ö���ǰ̨
			);
        }
        else if (dwStatus == ERROR_FILE_NOT_FOUND)
        {
            //printf("��Ҫִ�е��ļ�û���ҵ�\n");
            MessageBox(
				NULL,
				(LPCTSTR)"��Ҫִ�е��ļ�û���ҵ�",//�ı�
				(LPCTSTR)"starter",//����
				MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND //��ȷ������ť��������ͼ�ꡢ�ö���ǰ̨
			);
        }
        
    }

    return 0;
}


