@echo off
title YSK e-Fatura Donusturucu
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Lutfen Python kurun.
    pause
    exit /b 1
)
pip install -r requirements.txt >nul 2>&1
start "" pythonw main.py
exit
