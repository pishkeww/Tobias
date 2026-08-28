@echo off
cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
    echo python was not found on PATH. install python 3.10+ from python.org and try again.
    pause
    exit /b 1
)

if not exist venv (
    echo creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo installing dependencies...
pip install -r requirements.txt

echo starting local companion...
python main.py

pause
