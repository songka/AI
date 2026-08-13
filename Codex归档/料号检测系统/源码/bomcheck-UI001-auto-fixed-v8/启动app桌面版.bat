@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在启动料号检测系统桌面版...

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)

set EXIT_CODE=%ERRORLEVEL%
if not "%EXIT_CODE%"=="0" (
    echo.
    echo 程序异常退出，错误码：%EXIT_CODE%
    echo 请把上面的错误信息发给维护人员查看。
)

echo.
pause
