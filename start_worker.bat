@echo off
REM AutoPromo - Start WhatsApp Worker
REM Run this to start the Playwright worker

echo ======================================
echo AutoPromo Worker - Starting
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
python --version
echo.

echo [3/3] Starting WhatsApp Worker...
echo Worker will monitor connections and process messages
echo Press Ctrl+C to stop gracefully
echo.

python -m workers.whatsapp_worker

pause
