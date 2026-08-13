@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist runtime\api.pid (echo API PID file not found.& exit /b 0)
set /p API_PID=<runtime\api.pid
taskkill /PID %API_PID% /T /F
