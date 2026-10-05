@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found. Please run setup.bat first.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
echo Starting ORBIT-GUARD dashboard... (a browser tab will open; press Ctrl+C here to stop)
python -m streamlit run app/dashboard.py
pause
