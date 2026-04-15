@echo off
:: setup_scheduler.bat
:: Registers a daily Windows Task Scheduler job at 6 PM
:: Run this ONCE as Administrator

set PROJECT_DIR=%~dp0
set PYTHON_EXE=python
set TASK_NAME=LedgerAutoImprover

echo.
echo  Creating Windows Task: %TASK_NAME%
echo  Project: %PROJECT_DIR%
echo.

:: Delete existing task if present
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

:: Create new daily task at 18:00
schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "cmd /c cd /d \"%PROJECT_DIR%\" && %PYTHON_EXE% runner.py" ^
  /SC DAILY ^
  /ST 18:00 ^
  /RL HIGHEST ^
  /F

echo.
echo  ✦ Task scheduled! It will run every day at 6:00 PM.
echo  ✦ The script will sleep a random amount (up to 5h) before committing.
echo  ✦ So commits land between 6 PM and 11 PM.
echo.
echo  To test immediately (no delay):
echo    python runner.py --no-delay
echo.
pause
