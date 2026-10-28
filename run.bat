@echo off
rem Change to the script directory (handles spaces)
cd /d "%~dp0"

rem Run the Koro Telegram bot
python "koro_bot.py"

rem Keep the window open to view any output
pause