@echo off
setlocal enabledelayedexpansion
title Marcus the Worm Discord Bot - Advanced Launcher
color 0B

:: Banner
echo.
echo  =================================================
echo       MARCUS THE WORM - ADVANCED LAUNCHER
echo  =================================================
echo.

:: Menu
:menu
echo  Choose an option:
echo.
echo  [1] Run Marcus normally
echo  [2] Run Marcus in debug mode
echo  [3] Setup environment (install dependencies)
echo  [4] Create/update virtual environment
echo  [5] Check GPU status for AI optimization
echo  [6] Backup database
echo  [Q] Quit
echo.

set /p choice="Enter option: "

if "%choice%"=="1" goto run_normal
if "%choice%"=="2" goto run_debug
if "%choice%"=="3" goto setup_env
if "%choice%"=="4" goto create_venv
if "%choice%"=="5" goto check_gpu
if "%choice%"=="6" goto backup_db
if /i "%choice%"=="Q" goto end
goto menu

:run_normal
cls
echo Running Marcus in normal mode...
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python Main.py
pause
goto menu

:run_debug
cls
echo Running Marcus in DEBUG mode...
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

set PYTHONPATH=%CD%
set LOG_LEVEL=DEBUG
python Main.py --debug
pause
goto menu

:setup_env
cls
echo Installing dependencies...
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

pip install -r requirements.txt
echo.
echo Dependencies installed.
pause
goto menu

:create_venv
cls
echo Setting up virtual environment...
echo.

if exist venv (
    echo Virtual environment already exists.
    set /p update="Update it? (Y/N): "
    if /i "!update!"=="Y" (
        echo Updating virtual environment...
        python -m venv venv --upgrade
    ) else (
        echo Virtual environment not updated.
        pause
        goto menu
    )
) else (
    echo Creating new virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Virtual environment ready!
pause
goto menu

:check_gpu
cls
echo Checking GPU status for AI optimization...
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU device count:', torch.cuda.device_count()); print('GPU name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A')"
echo.
pause
goto menu

:backup_db
cls
echo Backing up database...
echo.

:: Get date and time in format YYYY-MM-DD_HH-MM
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set backupdate=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

:: Create backups directory if it doesn't exist
if not exist "backups" mkdir backups

:: Get database settings from .env file
for /f "tokens=1,2 delims==" %%G in (.env) do (
    if "%%G"=="DB_NAME" set DB_NAME=%%H
    if "%%G"=="DB_USER" set DB_USER=%%H
    if "%%G"=="DB_PASSWORD" set DB_PASSWORD=%%H
    if "%%G"=="DB_HOST" set DB_HOST=%%H
    if "%%G"=="DB_PORT" set DB_PORT=%%H
)

echo Backing up %DB_NAME% database to backups\marcus_%backupdate%.sql
echo This requires the pg_dump utility from PostgreSQL to be in your PATH
echo.

set PGPASSWORD=%DB_PASSWORD%
pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -F c -b -v -f "backups\marcus_%backupdate%.backup" %DB_NAME%

if %errorlevel% neq 0 (
    echo Backup failed! Make sure PostgreSQL tools are installed and in your PATH.
) else (
    echo Backup completed successfully!
)

echo.
pause
goto menu

:end
echo.
echo Goodbye!
timeout /t 2 > nul
exit
