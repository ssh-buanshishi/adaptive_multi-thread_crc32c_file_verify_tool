@echo off
rem --include-plugin-directory=xxx,yyy,zzz,xxx\111,yyy\222 ^ �Լ�Ҫ���ȥ�Ŀ�

call python -m nuitka --mingw64 --standalone --show-progress --remove-output ^
--include-data-files="./*"="./" ^
--windows-icon-from-ico="./icon-console.ico" ^
--output-dir=".." ^
"У��CRC32.py"

cd..
ren "У��CRC32.dist" "bin"
cd "bin"
del /f /q "�������.bat"
del /f /q "У��CRC32.py"
del /f /q "������--requirements.txt"
pause
