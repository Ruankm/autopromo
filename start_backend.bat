@echo off
REM AutoPromo - Start Backend Server
REM Run this to start the FastAPI backend

echo ======================================
echo AutoPromo Backend - Starting Server
echo ======================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [1/3] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found at backend\venv
    echo Using global Python installation...
)

echo.
echo [2/3] Checking environment...
py -3.12 --version
echo.

echo [3/3] Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.

py -3.12 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
