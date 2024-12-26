@echo off
rem -------------------- encoding:GB 2312(ANSI) ---------------------
rem It is recommended to use "Visual Studio Code" to edit this file.
rem 写一点中文，防止记事本抽风
setlocal enabledelayedexpansion

cd /d "%~dp0"
cd /d "bin"

rem 直接在当前cmd窗口运行，不启动新窗口
"记录CRC32C.exe" %*
exit 0