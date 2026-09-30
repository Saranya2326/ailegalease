@echo off
title LegalEase Fullstack Server
cd /d "%~dp0"
echo ============================================================
echo           Starting LegalEase Application Server
echo ============================================================
if exist "backend\venv\Scripts\python.exe" (
    echo [OK] Using backend virtual environment python...
    start "" "%~dp0frontend.html"
    "backend\venv\Scripts\python.exe" "backend\run.py"
) else if exist "venv\Scripts\python.exe" (
    echo [OK] Using root virtual environment python...
    start "" "%~dp0frontend.html"
    "venv\Scripts\python.exe" "backend\run.py"
) else (
    echo [*] Using system python...
    start "" "%~dp0frontend.html"
    python "backend\run.py"
)
pause
