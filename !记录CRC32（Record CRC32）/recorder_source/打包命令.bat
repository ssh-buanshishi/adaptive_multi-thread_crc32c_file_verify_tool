@echo off
rem --include-plugin-directory=xxx,yyy,zzz,xxx\111,yyy\222 ^ �Լ�Ҫ���ȥ�Ŀ�

call python -m nuitka --mingw64 --standalone --show-progress --remove-output ^
--include-data-files="./*"="./" ^
--windows-icon-from-ico="./icon-console.ico" ^
--output-dir=".." ^
"��¼CRC32.py"

cd..
ren "��¼CRC32.dist" "bin"
cd "bin"
del /f /q "�������.bat">nul
del /f /q "��¼CRC32.py">nul
del /f /q "������--requirements.txt"
pause
