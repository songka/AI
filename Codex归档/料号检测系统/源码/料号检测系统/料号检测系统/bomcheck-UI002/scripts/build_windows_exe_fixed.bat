@echo off
setlocal enabledelayedexpansion

rem Switch to the repository root (one level above this script)
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.." || exit /b 1

if defined BOMCHECK_PYTHON (
    set "PYTHON_EXE=%BOMCHECK_PYTHON%"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -c "import sys; print(sys.version)" >nul 2>nul
if errorlevel 1 (
    echo Python is not available. Install Python 3.10+ or set BOMCHECK_PYTHON to python.exe.
    goto :error
)

rem Recreate venv if it is missing or incomplete.
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    if exist ".venv" rmdir /s /q ".venv"
    "%PYTHON_EXE%" -m venv ".venv"
    if errorlevel 1 goto :error
)

set "VENV_PY=.venv\Scripts\python.exe"

"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :error

"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

"%VENV_PY%" -m pip install pyinstaller
if errorlevel 1 goto :error

"%VENV_PY%" -m PyInstaller --noconfirm --clean bomcheck.spec
if errorlevel 1 goto :error

echo.
echo Build finished. The executable is located at dist\bomcheck\bomcheck.exe
popd
goto :eof

:error
echo Build failed. Please check the errors above.
popd
exit /b 1
