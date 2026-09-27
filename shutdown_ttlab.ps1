# TTLab sauber beenden: Shell-Fenster, Backend (8000), Frontend (3000).
# Wird vom Backend-Endpoint /api/shutdown aufgerufen (detached) und vom
# Nutzer NICHT direkt gebraucht.
param(
    [int]$BackendPid = 0
)

$log = "$env:TEMP\ttlab_shutdown.log"
"=== $(Get-Date -Format o) pid=$BackendPid ===" | Add-Content $log

Start-Sleep -Milliseconds 1500  # Antwort an den Browser durchlassen

# 1) Alte TTLab-Shell-Fenster schliessen, die den start-Titel tragen
#    (klassische conhost-Fenster; Windows Terminal siehe Stufe 2)
Get-Process cmd -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -match 'TTLab (Backend|Frontend)' } |
    ForEach-Object {
        "kill fenster cmd pid $($_.Id)" | Add-Content $log
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

# 2) Alles was auf den TTLab-Ports lauscht beenden (Backend + Frontend-Devserver)
#    und danach auch deren Eltern-cmd-Fenster schliessen, damit keine leeren
#    Shells uebrig bleiben (Windows Terminal zeigt den Titel beim cmd-Prozess
#    nicht an - deshalb der Weg ueber die Prozess-Elternkette).
foreach ($port in 8000, 3000) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        $pid_ = $conn.OwningProcess

        # Elternkette VOR dem Kill sammeln (danach ist die CIM-Instanz weg):
        # ALLE cmd.exe-Vorfahren schliessen (npm.cmd ist selbst ein cmd.exe;
        # erst das aeusserste ist das Shell-Fenster). WindowsTerminal.exe
        # selbst NIEMALS toeten - es koennte weitere, nicht zu TTLab
        # gehoerige Tabs des Nutzers offen halten. Die Tabs sterben mit
        # ihren cmd-Prozessen von selbst.
        $cmdAncestors = @()
        $current = $pid_
        for ($i = 0; $i -lt 8; $i++) {
            $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$current" -ErrorAction SilentlyContinue
            if (-not $proc) { break }
            $parent = $proc.ParentProcessId
            if (-not $parent) { break }
            $parentProc = Get-CimInstance Win32_Process -Filter "ProcessId=$parent" -ErrorAction SilentlyContinue
            if (-not $parentProc) { break }
            if ($parentProc.Name -eq 'WindowsTerminal.exe') { break }
            if ($parentProc.Name -eq 'cmd.exe') {
                $cmdAncestors += $parent
            }
            $current = $parent
        }

        "kill port $port pid $pid_" | Add-Content $log
        Stop-Process -Id $pid_ -Force -ErrorAction SilentlyContinue

        foreach ($anc in $cmdAncestors) {
            "kill eltern-cmd pid $anc" | Add-Content $log
            Stop-Process -Id $anc -Force -ErrorAction SilentlyContinue
        }
    }
}

# 3) Backend-PID explizit (falls der Port-Kill schon griff, ist das ein No-Op)
if ($BackendPid -gt 0) {
    Stop-Process -Id $BackendPid -Force -ErrorAction SilentlyContinue
}
