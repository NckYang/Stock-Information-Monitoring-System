@echo off
chcp 65001 >nul
setlocal

echo =======================================
echo   Stock Monitoring Dashboard
echo =======================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [Error] Python was not found.
    echo Please install Python 3.9 or newer and enable "Add Python to PATH".
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist app.py (
    echo [Error] app.py was not found.
    echo Please run this file from the project folder.
    pause
    exit /b 1
)

if not exist requirements.txt (
    echo [Error] requirements.txt was not found.
    echo Please make sure the full project folder was copied.
    pause
    exit /b 1
)

if not exist venv (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [Error] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo [Error] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [3/4] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [Error] Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

if "%GEMINI_API_KEY%"=="" (
    echo.
    echo [Notice] GEMINI_API_KEY is not set.
    echo Gemini AI sentiment analysis will use keyword fallback unless you set the API key.
    echo See README.md for setup instructions.
    echo.
)

echo [4/4] Starting Streamlit...
streamlit run app.py

pause
