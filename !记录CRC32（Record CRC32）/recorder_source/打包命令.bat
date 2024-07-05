@echo off
rem --include-plugin-directory=xxx,yyy,zzz,xxx\111,yyy\222 ^ 自己要编进去的库

call python -m nuitka --mingw64 --standalone --show-progress --remove-output ^
--include-data-files="./*"="./" ^
--windows-icon-from-ico="./icon-console.ico" ^
--output-dir=".." ^
"记录CRC32.py"

cd..
ren "记录CRC32.dist" "bin"
cd "bin"
del /f /q "打包命令.bat">nul
del /f /q "记录CRC32.py">nul
del /f /q "库需求--requirements.txt"
pause
