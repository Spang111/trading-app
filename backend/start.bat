@echo off
echo Starting QuantFlow Backend Server...
echo.

cd /d "%~dp0"

REM Check if virtual environment exists (or recreate if broken)
if exist ".venv\\Scripts\\python.exe" (
    ".venv\\Scripts\\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo Existing .venv looks broken, recreating...
        rmdir /s /q .venv
        echo.
    )
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Initialize database and start server
echo Starting server...
echo API Documentation: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
