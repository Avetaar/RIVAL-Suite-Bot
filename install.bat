@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ==============================================
echo  RIVAL Suite Bot  -  v0.1  -  Avetaar AI
echo ==============================================
where python >nul 2>nul
if errorlevel 1 (
    echo [1/4] python not found - trying python3...
    where python3 >nul 2>nul
    if errorlevel 1 (
        echo Install Python from python.org first, then run this file again.
        pause
        exit /b 1
    )
    set "PY=python3"
) else (
    set "PY=python"
)
for /f "delims=" %%v in ('%PY% --version 2^>^&1') do echo      %%v
echo [2/4] Installing dependencies...
%PY% -m pip install --quiet httpx Pillow
echo      done
if not exist "RIVAL\bot_credentials.json" (
    echo [3/4] Setup - 3 quick questions
    set /p T_TOKEN="1. Bot token (from BotFather) > "
    set /p T_USER="2. Your Telegram username WITHOUT @ (developer contact) > "
    set /p T_ID="3. Your numeric Telegram ID (the owner) > "
    > "RIVAL\bot_credentials.json" (echo {
    echo     "token": "%T_TOKEN%",
    echo     "owner_id": %T_ID%,
    echo     "owner_username": "%T_USER%"
    echo })
    echo      saved to RIVAL\bot_credentials.json
) else (
    echo [3/4] Credentials already exist - keeping them
)
echo [4/4] Starting the bot...  (Ctrl+C stops it, rerun to start again)
%PY% Avetaar.py
pause
endlocal
