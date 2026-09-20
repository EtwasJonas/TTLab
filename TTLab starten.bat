@echo off
chcp 65001 >nul
title TTLab starten
echo Starting TTLab...

REM Backend in separatem Fenster starten (erbt das Arbeitsverzeichnis)
pushd "%~dp0backend"
start "TTLab Backend" cmd /k ".\venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
popd

REM Warten bis Backend bereit ist
timeout /t 3 /nobreak >nul

REM Frontend in separatem Fenster starten (erbt das Arbeitsverzeichnis)
pushd "%~dp0frontend"
start "TTLab Frontend" cmd /k "npm run dev"
popd

REM Browser oeffnen
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo TTLab is running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo Dieses Fenster kann geschlossen werden.
echo Die beiden Server-Fenster (Backend/Frontend) offen lassen.
echo.
pause >nul
