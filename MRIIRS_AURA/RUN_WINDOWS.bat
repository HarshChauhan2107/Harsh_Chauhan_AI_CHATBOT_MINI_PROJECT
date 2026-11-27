@echo off
setlocal
cd /d "%~dp0"
title MRIIRS AURA - Artificial University Response Assistant
echo.
echo  ================================================
echo   MRIIRS AURA - Artificial University Response Assistant
echo   Ask. Explore. Discover.
echo  ================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (set PY=python)
if not exist .venv\Scripts\python.exe (
  echo [1/3] Creating Python virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 goto error
)
echo [2/3] Installing / checking required packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo [3/3] Starting MRIIRS AURA...
echo.
echo Open this address in your browser: http://127.0.0.1:5000
echo Keep this window open while using the chatbot.
echo Press Ctrl+C to stop the server.
echo.
.venv\Scripts\python.exe app.py
goto end
:error
echo.
echo Setup failed. Check that Python 3.10+ is installed and internet is available for installing Flask.
echo You can also read README.md for manual setup.
pause
:end
endlocal
