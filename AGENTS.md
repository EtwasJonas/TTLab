# TTLab – Arbeitskonventionen für Coding-Agenten

## Git: Committe und pushe proaktiv

- **Sobald eine abgeschlossene, verifizierte Arbeitseinheit steht: committen UND auf
  GitHub pushen** (Remote `origin`, aktuell Branch `ml-ball-recognition`). Nicht auf
  Aufforderung warten – der Nutzer hat dies ausdrücklich so gewünscht (27.09.2026).
- Logische Commits (ein Thema pro Commit, deutsche Beschreibung im Stil der bisherigen
  Historie). Vor jedem Commit: `git status` + `git diff` prüfen, nichts Unbekanntes
  oder Secrethaftes commiten, Build-Artefakte draußen lassen.
- Nie `--force` pushen, nie Hooks umgehen.

## Projekt-Kernfakten (kurz)

- Lokale Tischtennis-Videoanalyse: FastAPI-Backend (:8000) + Next.js-Frontend (:3000),
  SQLite in `data/db/ttlab.db` (`data/` ist NIE im Repo).
- Wichtige Doku: `PROJEKTUEBERGABE.md` (Versionshistorie, offene Fragen, "Nächste
  Schritte" – nach jeder Session aktualisieren).
- Python-venv wurde verschoben: pip NUR als `python -m pip` nutzen
  (`backend\venv\Scripts\pip.exe` zeigt auf einen toten Alt-Pfad).
- Tests: `cd backend && python -m pytest tests -q` (Unit) und
  `cd frontend && npm run e2e` (braucht laufende Server + Edge, räumt eigene
  `*test_*`-Datensätze ein, NIE `v1-ml-training` anfassen).
- Vor Pipeline-Änderungen an der Rally-Erkennung: Bit-Identitäts-Workflow in
  `backend/tests/phase2_verification/README.md` beachten.
- Masken-Semantik ENTSCHIEDEN (27.09.2026): `TTLAB_PLAY_ZONE=0.0` (Tischplatte) ist
  Default – Ground-Truth-Messung hat Spielzone (Recall 1.0, aber Precision-Einbruch)
  verloren. Offen: ML-Realtest mit Faktor 0.5/1.0, sobald ONNX-Modell existiert.
- Backend-`start` des Shutdown-Endpoints (`/api/shutdown` → `shutdown_ttlab.ps1`):
  Popen mit `CREATE_NO_WINDOW` + DEVNULL-Handles, NICHT `DETACHED_PROCESS`+
  `close_fds` (stirbt lautlos).

## Stil

- Keine Kommentare außer bei echter Komplexität; bestehende Muster der Datei folgen.
- Backend-Fehlermeldungen/Konsolenausgaben auf Deutsch (bestehender Stil).
