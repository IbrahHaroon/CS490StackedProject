@echo off
REM Quick script to run analytics tests on Windows

echo.
echo 📊 Dashboard Analytics Test Suite
echo ==================================
echo.

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pytest not found. Installing dependencies...
    python -m pip install pytest pytest-asyncio sqlalchemy
)

echo Running analytics tests...
echo.

cd /d "%~dp0"

python -m pytest tests\test_analytics.py -v --tb=short

echo.
echo ✅ Test run complete!
pause
