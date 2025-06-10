@echo off
title 啟動 Bot 中...
cd /d "%~dp0"

REM 啟用虛擬環境（如果有）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM 執行 bot 主程式
python dont't_want_work.py

pause
