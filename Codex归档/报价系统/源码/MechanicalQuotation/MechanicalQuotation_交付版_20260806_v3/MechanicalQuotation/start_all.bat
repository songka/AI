@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "MechanicalQuotation API" /min "%~dp0MechanicalQuotationConsole.exe" -m quotation.launcher --api
timeout /t 2 /nobreak >nul
"%~dp0MechanicalQuotation.exe" -m quotation.launcher --ui
