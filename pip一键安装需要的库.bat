@echo off
rem -------------------- encoding:GBK (ANSI) ---------------------
rem 建议运行前查看“requirements.txt”确认。
rem 如果需要特定版本的python（高低版本或者32、64位的各种特定python），请自行修改下方的pip命令

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo 建议运行前查看“requirements.txt”确认是否需要根据自己需要修改或精简，
echo 如果需要特定版本的python（高低版本或者32、64位的各种特定python），
echo 请退出此bat批处理后，自行编辑修改下方的pip命令
echo.
echo ★★ 如确定继续，请按任意键；           ★★ 
echo ★★ 如需要终止退出，请按右上角退出按钮。★★ 

@pause>nul

pip install -r "requirements.txt" -U -i "https://mirrors.aliyun.com/pypi/simple/"

pause
exit 0