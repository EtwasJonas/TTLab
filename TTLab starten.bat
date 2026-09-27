@echo off
chcp 65001 >nul
title TTLab starten
echo Starting TTLab...

REM Repo-Pfad ermitteln: Liegt diese .bat IM Projektordner, wird der Ordner
REM der .bat genutzt. Liegt sie woanders (z.B. Desktop-Verknuepfung), wird
REM der feste Installationspfad darunter verwendet.
set "TTLAB_ROOT=%~dp0"
if not exist "%TTLAB_ROOT%backend\venv\Scripts\python.exe" set "TTLAB_ROOT=C:\Users\Jonas\Documents\OpenCode\ttlab\"
if not exist "%TTLAB_ROOT%backend\venv\Scripts\python.exe" (
    echo FEHLER: TTLab-Installation nicht gefunden.
    echo Erwartet: C:\Users\Jonas\Documents\OpenCode\ttlab\backend\venv
    echo Diese .bat muss entweder im TTLab-Projektordner liegen oder der
    echo Pfad oben muss angepasst werden.
    pause
    exit /b 1
)

echo Raume alte TTLab-Prozesse auf (verhindert Port-Konflikte)...
REM Alte TTLab-Shell-Fenster schliessen (falls von einem frueheren Start)
taskkill /FI "WINDOWTITLE eq TTLab Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq TTLab Frontend*" /T /F >nul 2>&1
REM Alles beenden, was noch auf den Ports lauscht
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,3000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

REM Backend in separatem Fenster starten
pushd "%TTLAB_ROOT%backend"
start "TTLab Backend" cmd /k ".\venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
popd

REM Warten bis Backend bereit ist
timeout /t 3 /nobreak >nul

REM Frontend in separatem Fenster starten
pushd "%TTLAB_ROOT%frontend"
start "TTLab Frontend" cmd /k "npm run dev"
popd

REM Browser oeffnen
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo TTLab is running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Ordner:   %TTLAB_ROOT%
echo.
echo Beenden: Button "Beenden" oben rechts im TTLab-Interface
echo (schliesst Backend, Frontend und die beiden Server-Fenster).
echo.
echo Dieses Fenster kann geschlossen werden.
echo Die beiden Server-Fenster (Backend/Frontend) offen lassen.
echo.
pause >nul
