@echo off
setlocal
cd /d "%~dp0"
echo ==============================================
echo   ORBIT-GUARD setup  (SOFTWARE SIMULATION)
echo ==============================================

set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python was not found. Install Python 3.13 from https://www.python.org/downloads/
        echo         and tick "Add python.exe to PATH" during installation.
        pause
        exit /b 1
    )
    set "PY=py -3"
)

echo Checking Python...
%PY% --version
if errorlevel 1 (
    echo [ERROR] Python could not be started.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

call ".venv\Scripts\activate.bat"
echo Installing requirements (internet needed once)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation failed. See docs\TROUBLESHOOTING.md
    pause
    exit /b 1
)

if not exist "data\logs" mkdir "data\logs"
if not exist "data\sample" mkdir "data\sample"

echo.
echo Setup finished successfully.
echo Next step:  run.bat      (or:  streamlit run app/dashboard.py)
echo Optional :  python -m pytest
pause
