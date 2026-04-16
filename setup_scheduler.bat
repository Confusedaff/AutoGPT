@echo off
:: setup_scheduler.bat
:: Registers a daily Windows Task Scheduler job at 6 AM (commits spread 6 AM - 11 PM)
:: Run this ONCE as Administrator

set PROJECT_DIR=C:\Me\Projects\Recursive_Self_Improvement
set PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe
set TASK_NAME=LedgerAutoImprover

echo.
echo  Creating Windows Task: %TASK_NAME%
echo  Project:  %PROJECT_DIR%
echo  Python:   %PYTHON_EXE%
echo.

:: Verify the venv Python actually exists before continuing
if not exist "%PYTHON_EXE%" (
    echo  [ERROR] Could not find: %PYTHON_EXE%
    echo  Make sure your virtual environment is at %PROJECT_DIR%\.venv
    echo  and was created with: python -m venv .venv
    pause
    exit /b 1
)

:: Delete existing task if present
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

:: PYTHONUTF8=1 forces UTF-8 output so Unicode chars don't crash on Windows cp1252
:: cmd /c lets us set the env var and cd into the project dir before running
schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /TR "cmd /c set PYTHONUTF8=1 && cd /d \"%PROJECT_DIR%\" && \"%PYTHON_EXE%\" runner.py >> \"%PROJECT_DIR%\cron.log\" 2>&1" ^
    /SC DAILY ^
    /ST 06:00 ^
    /RL HIGHEST ^
    /F

echo.
echo  Task scheduled! It will run every day at 6:00 AM.
echo  Commits will be spread randomly between 6 AM and 11 PM.
echo.
echo  Logs will be written to: %PROJECT_DIR%\cron.log
echo.
echo  Verifying task...
schtasks /Query /TN "%TASK_NAME%"
echo.
echo  To test immediately (no delay):
echo    cd /d %PROJECT_DIR%
echo    set PYTHONUTF8=1
echo    "%PYTHON_EXE%" runner.py --no-delay
echo.
pause
