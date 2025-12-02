@echo off
REM LoL Coach AI - Web Server Launcher for Windows

echo.
echo ========================================
echo   LOL COACH AI - WEB SERVER
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
)

echo.
echo 🚀 Starting LoL Coach AI Web Server...
echo.
echo    Web UI:     http://localhost:5000
echo    Mobile UI:  http://<your-computer-ip>:5000
echo.
echo    To find your IP: Open Command Prompt and type 'ipconfig'
echo    Look for 'IPv4 Address' (usually 192.168.x.x)
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
