@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ==============================================
echo  RIVAL Suite Bot - Avetaar AI Suite (v0.1)
echo  One-command installer: Windows / Termux / Linux / macOS
echo ==============================================
where python >nul 2>nul
if errorlevel 1 (
    echo [1/4] python not found - trying python3...
    where python3 >nul 2>nul
    if errorlevel 1 (
        echo install python3 from python.org first, then run this file again
        pause
        exit /b 1
    )
    set "PY=python3"
) else (
    set "PY=python"
)
for /f "delims=" %%v in ('%PY% --version 2^>^&1') do echo [1/4] %%v
%PY% -m pip install --quiet --upgrade pip 2>nul
%PY% -m pip install --quiet httpx Pillow
echo [2/4] dependencies installed (httpx + Pillow)
if not exist "RIVAL\bot_credentials.json" (
    echo [3/4] setup credentials
    set /p T_TOKEN="bot token (from @BotFather) > "
    set /p T_USER="bot username WITHOUT @ (dev contact link) > "
    set /p T_ID="owner telegram user id (numeric) > "
    > "RIVAL\bot_credentials.json" (echo {
    echo     "token": "%T_TOKEN%",
    echo     "owner_id": %T_ID%,
    echo     "owner_username": "%T_USER%"
    echo })
    echo credentials written to RIVAL\bot_credentials.json
) else (
    echo [3/4] credentials already in RIVAL\bot_credentials.json - keeping them
)
echo [4/4] starting bot (Ctrl+C stops it; rerun to start again)
%PY% Avetaar.py
pause
endlocal
