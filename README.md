# TTLab V0.3 - Tischtennis Videoanalyse mit KI

TTLab ist eine lokal gehostete Webanwendung zur automatischen Analyse von Tischtennis-Videos. Die Software erkennt Ballwechsel (Rallies) durch Kombination von Bewegungsanalyse, Audioauswertung und Ballerkennung.

**Version:** V0.3 (V0.4 mit trainiertem Ball-Tracking in Planung)  
**Datum:** August 2026

## Projektstruktur

```
ttlab/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py             # API Endpunkte
│   │   ├── models.py           # SQLAlchemy Modelle
│   │   ├── database.py         # DB Konfiguration & Migration
│   │   ├── schemas.py          # Pydantic Schemas
│   │   ├── rally_detection.py  # Rally Detection (Motion + Audio + Ball)
│   │   └── video_processor.py  # FFmpeg Clip-Erzeugung
│   ├── requirements.txt
│   └── .env
├── frontend/                   # Next.js 19 Frontend
│   ├── app/
│   │   ├── page.tsx            # Dashboard
│   │   ├── layout.tsx          # Root Layout
│   │   └── globals.css         # Tailwind Styles
│   ├── components/
│   │   ├── MatchList.tsx       # Match-Übersicht
│   │   ├── MatchDetail.tsx     # Detail mit Tischkalibrierung
│   │   └── VideoUpload.tsx     # Upload-Komponente
│   └── package.json
└── data/                       # NICHT versioniert (.gitignore)
    ├── videos/                 # Hochgeladene Videos
    ├── clips/                  # Extrahierte Rally-Clips
    └── ttlab.db                # SQLite Datenbank
```

## Installation

### Voraussetzungen

- Python 3.13+
- Node.js 20+
- FFmpeg (für Video-Processing)

### Backend

```bash
cd backend
uv venv
.\venv\Scripts\activate
uv pip install -r requirements.txt
```

**FFmpeg installieren (Windows):**
- Download: https://www.gyan.dev/ffmpeg/builds/
- ZIP entpacken und `bin`-Ordner zu PATH hinzufügen
- Oder: `choco install ffmpeg` (mit Chocolatey)

### Frontend

```bash
cd frontend
npm install
```

## Starten

**Bequem mit Batch-Skript:** Doppelklick auf `TTLab starten.bat` auf dem Desktop

**Oder manuell:**

### Terminal 1 - Backend:
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

## Zugriff

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Doku (Swagger): http://localhost:8000/docs

## Workflow

1. Video über Frontend hochladen (MP4, AVI, MOV, MKV, WebM)
2. Analyse startet automatisch im Hintergrund
3. Rally Detection kombiniert Motion + Audio + Ball-Kandidaten
4. Einzelne Ballwechsel werden als Clips gespeichert
5. Timeline-Ansicht zum Navigieren durch alle Rallies
6. Manuelle Validierung (akzeptieren/ablehnen) möglich

## Features nach Version

### V0.1 ✅
- Video Upload
- Automatische Rally Detection (Motion + Audio)
- Clip-Erzeugung pro Ballwechsel
- Webplayer mit Timeline
- Highlight-Erkennung
- Match-Verwaltung

### V0.2 ✅
- Match-Metadaten (Spieler, Gegner, Ergebnis, Datum)
- Notizen
- Filter nach Ergebnis (Siege/Niederlagen)
- Dashboard-Statistiken

### V0.3 ✅ (aktuell)
- Manuelle Tischmarkierung (4 Ecken)
- Ball-Kandidatenerkennung im Tischbereich
- Rally-Validierung (accepted/review/rejected)
- Confidence & Impact_Count Metriken
- 100ms-Schritt Navigation (Pfeiltasten)
- Auto-Play Queue
- Highlight-Filter

### V0.4 🔄 (in Planung)
- Trainiertes Ball-Tracking-Modell (YOLOv8n oder RT-DETR)
- Labeling-Tool für Ballpositionen
- Reduktion False Positives
- Ball-Flugbahn-Analyse
- Unterscheidung: Aufschlag-Vorbereitung vs. echter Ballwechsel

### V0.5 ⏳
- Player Detection
- Pose Estimation
- Schlagtyp-Erkennung (Vorhand/Rückhand/Topspin)

### V0.6 ⏳
- Taktik-Analyse
- Heatmaps der Balllandepositionen
- Schwachstellen-Erkennung

### V1.0 ⏳
- KI-Coach mit LLM-Integration
- Spielerprofile mit Historie
- Trainings-Empfehlungen

## Dokumentation

- **Ausführliche Projektdokumentation:** Siehe `PROJEKTUEBERGABE.md`
- **API-Dokumentation:** http://localhost:8000/docs (nach Backend-Start)

## Lizenz

Proprietär (alle Rechte vorbehalten)

## Workflow

1. Video über Frontend hochladen (MP4, AVI, MOV, MKV, WebM)
2. Analyse startet automatisch im Hintergrund
3. Rally Detection kombiniert Motion + Audio
4. Einzelne Ballwechsel werden als Clips gespeichert
5. Timeline-Ansicht zum Navigieren durch alle Rallys

## Versionshistorie

### V0.1 - Rally Detection
✅ Video Upload  
✅ Automatische Rally Detection (Motion + Audio)  
✅ Clip-Erzeugung pro Ballwechsel  
✅ Webplayer mit Timeline  
✅ Highlight-Erkennung  
✅ Match-Verwaltung  

### V0.2 - Match Library
✅ Match-Metadaten (Spieler, Gegner, Ergebnis, Datum)  
✅ Notizen  
✅ Filter nach Ergebnis (Siege/Niederlagen)  
✅ Dashboard-Statistiken  

### V0.3 - Verbesserte Rally-Erkennung
✅ Manuelle Tischmarkierung (4 Ecken)  
✅ Ball-Kandidatenerkennung im Tischbereich  
✅ Rally-Validierung (Sicher/Prüfen/Verworfen)  
✅ Konservative Erkennung (weniger falsche Clips)  

## Roadmap

### V0.4 - Trainiertes Ball-Tracking-Modell
🔄 Labeling-Tool für Ballpositionen  
🔄 YOLOv8/RT-DETR Training  
🔄 Ball-Flugbahn-Analyse  
🔄 Unterscheidung: Aufschlag-Vorbereitung vs. echter Ballwechsel  

### V0.5 - Computer Vision
⏳ Player Detection  
⏳ Pose Estimation  
⏳ Schlagtyp-Erkennung  

### V0.6 - KI-Coach
⏳ Spielanalyse mit LLM  
⏳ Schwächen erkennen  
⏳ Trainings-Empfehlungen  

### V1.0 - Vollständiger Analyse-Assistent
⏳ Spielerprofile  
⏳ Fortschritt über mehrere Spiele  
⏳ Taktische Analysen
