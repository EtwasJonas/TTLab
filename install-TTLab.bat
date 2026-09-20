@echo off
chcp 65001 >nul
title TTLab Installation
setlocal EnableExtensions

echo ==================================================
echo            TTLab - Automatische Installation
echo ==================================================
echo.
echo  Dieses Skript installiert alle benoetigten Programme
echo  und richtet TTLab komplett automatisch ein:
echo.
echo    1. Python 3.13      (falls fehlt)
echo    2. Node.js 20+      (falls fehlt)
echo    3. FFmpeg           (falls fehlt)
echo    4. Backend-Abhaengigkeiten
echo    5. Frontend-Abhaengigkeiten
echo    6. Desktop-Verknuepfung "TTLab starten"
echo.
echo  Dauer: ca. 5-15 Minuten (je nach Internetverbindung)
echo  Es werden KEINE Programme entfernt oder geaendert,
echo  die bereits installiert sind.
echo.
pause

set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"
set "WINGET_FLAGS=-e --accept-source-agreements --accept-package-agreements --silent"

echo.
echo ==================================================
echo  [1/6] Pruefe Python...
echo ==================================================
where python >nul 2>nul
if errorlevel 1 (
    echo   Python nicht gefunden - wird installiert...
    winget install --id Python.Python.3.13 %WINGET_FLAGS%
    if errorlevel 1 goto :winget_error
    call :refresh_path
) else (
    for /f "tokens=*" %%v in ('python --version 2^>nul') do echo   %%v gefunden
)

echo.
echo ==================================================
echo  [2/6] Pruefe Node.js...
echo ==================================================
where npm >nul 2>nul
if errorlevel 1 (
    echo   Node.js nicht gefunden - wird installiert...
    winget install --id OpenJS.NodeJS.LTS %WINGET_FLAGS%
    if errorlevel 1 goto :winget_error
    call :refresh_path
) else (
    for /f "tokens=*" %%v in ('node --version 2^>nul') do echo   Node.js %%v gefunden
)

echo.
echo ==================================================
echo  [3/6] Pruefe FFmpeg...
echo ==================================================
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo   FFmpeg nicht gefunden - wird installiert...
    winget install --id Gyan.FFmpeg %WINGET_FLAGS%
    if errorlevel 1 goto :winget_error
    call :refresh_path
) else (
    for /f "tokens=*" %%v in ('ffmpeg -version 2^>nul') do (
        echo   %%v
        goto :ffmpeg_ok
    )
    :ffmpeg_ok
)

echo.
echo ==================================================
echo  [4/6] Installiere Backend (Python-Umgebung)...
echo ==================================================
if not exist "backend\venv" (
    python -m venv backend\venv
    if errorlevel 1 goto :python_error
)
backend\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
if errorlevel 1 goto :pip_error
echo   Installiere Pakete (OpenCV, FastAPI, ...) - das dauert einen Moment...
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt --quiet
if errorlevel 1 goto :pip_error
echo   Backend fertig.

echo.
echo ==================================================
echo  [5/6] Installiere Frontend (Node-Module)...
echo ==================================================
where npm >nul 2>nul
if errorlevel 1 goto :node_missing
pushd frontend
call npm install --no-fund --no-audit
set "NPM_RESULT=%errorlevel%"
popd
if not "%NPM_RESULT%"=="0" goto :npm_error
echo   Frontend fertig.

echo.
echo ==================================================
echo  [6/6] Erstelle Desktop-Verknuepfung...
echo ==================================================
if not exist "TTLab starten.bat" (
    echo   WARNUNG: "TTLab starten.bat" nicht im Projektordner gefunden.
    echo   Verknuepfung wird trotzdem erstellt, startet aber evtl. nicht.
)
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $lnk = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\TTLab starten.lnk'); $lnk.TargetPath = '%INSTALL_DIR%TTLab starten.bat'; $lnk.WorkingDirectory = '%INSTALL_DIR%'; $lnk.Description = 'TTLab starten'; $lnk.Save()"
if errorlevel 1 (
    echo   Verknuepfung konnte nicht erstellt werden - nicht kritisch.
) else (
    echo   Verknuepfung "TTLab starten" auf dem Desktop erstellt.
)

echo.
echo ==================================================
echo            Installation abgeschlossen!
echo ==================================================
echo.
echo  TTLab jetzt starten:
echo    - Doppelklick auf "TTLab starten" auf dem Desktop
echo    - oder Doppelklick auf "TTLab starten.bat" im Projektordner
echo.
echo  Im Browser oeffnet sich automatisch das Dashboard:
echo    http://localhost:3000
echo.
pause
goto :eof

:refresh_path
REM Aktualisiert PATH aus der Registry (nach winget-Installationen)
for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('PATH','Machine')+';'+[Environment]::GetEnvironmentVariable('PATH','User')"`) do set "PATH=%%p"
goto :eof

:winget_error
echo.
echo  FEHLER: Installation ueber winget fehlgeschlagen.
echo.
echo  Moegliche Loesungen:
echo    1. Skript als Administrator ausfuehren (Rechtsklick)
echo    2. Pruefen ob winget vorhanden ist (in Windows-Suche "winget" eingeben)
echo    3. Programme manuell installieren:
echo       - Python 3.13:  https://www.python.org/downloads/
echo       - Node.js LTS:  https://nodejs.org/
echo       - FFmpeg:       https://www.gyan.dev/ffmpeg/builds/
echo       Danach dieses Skript erneut starten.
echo.
pause
exit /b 1

:python_error
echo.
echo  FEHLER: Python-Umgebung konnte nicht erstellt werden.
echo  Wurde Python gerade installiert? Dann dieses Fenster schliessen
echo  und das Skript erneut starten (PATH muss aktualisiert werden).
echo.
pause
exit /b 1

:pip_error
echo.
echo  FEHLER: Python-Pakete konnten nicht installiert werden.
echo  Internetverbindung pruefen und Skript erneut starten.
echo.
pause
exit /b 1

:node_missing
echo.
echo  FEHLER: npm nicht gefunden. Node.js wurde evtl. gerade installiert -
echo  dieses Fenster schliessen und das Skript erneut starten.
echo.
pause
exit /b 1

:npm_error
echo.
echo  FEHLER: Frontend-Abhaengigkeiten konnten nicht installiert werden.
echo  Internetverbindung pruefen und Skript erneut starten.
echo.
pause
exit /b 1
