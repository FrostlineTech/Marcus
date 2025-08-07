@echo off
title Marcus the Worm Discord Bot
color 0A

echo.
echo  ===================================
echo       MARCUS THE WORM BOT
echo  ===================================
echo.
echo  Starting up Marcus...
echo  Press Ctrl+C to stop the bot
echo.

:: Check if virtual environment exists and activate if it does
if exist "venv\Scripts\activate.bat" (
    echo  [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo  [INFO] Virtual environment activated
) else (
    echo  [INFO] No virtual environment found, using system Python
)

:: Run the bot with console output
echo  [INFO] Starting Marcus Discord Bot at %time% on %date%
echo.

python Main.py

:: If the bot exits with an error, pause so user can see
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo  [ERROR] Bot exited with error code %errorlevel%
    echo  Check the error message above for details
    echo.
    pause
) else (
    echo.
    echo  [INFO] Bot shutdown normally
    timeout /t 5
)
