@echo off
REM Change to the directory where the script is located
cd /d %~dp0

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

REM Run the Python script
python main.py

pause
