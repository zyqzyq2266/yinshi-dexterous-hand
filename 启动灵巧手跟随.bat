@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Python environment not found: .venv\Scripts\python.exe
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m hand_tracking.app --config config.yaml
echo.
echo The tracking program has stopped.
pause
