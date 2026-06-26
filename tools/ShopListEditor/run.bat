@echo off
cd /d "%~dp0"
echo IKappaID Phone Shop List Editor
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Install Python 3.10+ and add it to PATH.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
python -m pip install -q -r requirements.txt
python main.py
if errorlevel 1 pause
