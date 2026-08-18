# TTLab - Projektübergabe & Entwicklungsstand

**Version:** V0.3 (in Entwicklung → V0.4)  
**Datum:** 17. August 2026  
**Projekttyp:** Lokale Videoanalyse-Plattform für Tischtennis mit KI-gestützter Ballwechsel-Erkennung

---

## Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Hardware & Infrastruktur](#hardware--infrastruktur)
3. [Tech Stack](#tech-stack)
4. [Architektur](#architektur)
5. [Entwicklungsphilosophie](#entwicklungsphilosophie)
6. [Versionshistorie](#versionshistorie)
7. [Aktueller Entwicklungsstand](#aktueller-entwicklungsstand)
8. [Bekannte Probleme](#bekannte-probleme)
9. [Roadmap](#roadmap)
10. [Dateistruktur](#dateistruktur)
11. [API-Referenz](#api-referenz)
12. [Datenbank-Schema](#datenbank-schema)
13. [Setup & Installation](#setup--installation)
14. [Wichtige Code-Stellen](#wichtige-code-stellen)
15. [Nächste Schritte](#nächste-schritte)

---

## Projektübersicht

TTLab ist eine lokal gehostete Webanwendung zur Analyse von Tischtennis-Videos. Die Software erkennt automatisch Ballwechsel (Rallies) durch Kombination von Bewegungsanalyse, Audioauswertung und Ballerkennung, extrahiert diese als einzelne Clips und ermöglicht taktische Auswertungen.

### Kernfunktionen

- **Automatische Ballwechsel-Erkennung:** Analyse von hochgeladenen Videos mittels Motion Detection, Audio-Peaks und visuellen Ballkandidaten
- **Manuelle Tischkalibrierung:** Benutzer definiert die 4 Ecken des Tischtennistisches per Mausklick im Videoframe
- **Rally-Validierung:** Jeder erkannte Ballwechsel kann als `accepted`, `review` oder `rejected` markiert werden
- **Highlight-Navigation:** Schnelles Springen zwischen Ballwechseln mit Pfeiltasten (100ms-Schritte)
- **Match-Metadata:** Erfassung von Datum, Spielern, Ergebnis, Score und Notizen
- **Statistik-Dashboard:** Übersicht über gewonnene/verlorene Matches, Fehlerquoten, Gesamtstatistiken
- **Export-Funktion:** Zusammenstellung aller akzeptierten Highlights als einzelner Videoclip

### Zielgruppe

- Tischtennis-Trainer für technische Analysen
- Spieler zur Selbstreflexion und Taktikentwicklung
- Vereine zur Dokumentation von Training und Wettkämpfen

### Alleinstellungsmerkmale

- **100% lokal:** Keine Cloud, keine Abos, keine Datenübertragung an Dritte
- **Echtzeit-Analyse:** Verarbeitung während des Uploads im Hintergrund
- **Transparente KI:** Nachvollziehbare Erkennung mit Confidence-Scores und Metriken
- **Erweiterbar:** Offene API für zukünftige Features wie Spin-Erkennung, Shot-Klassifikation

---

## Hardware & Infrastruktur

### Entwicklungshardware (Laptop)

| Komponente | Spezifikation |
|------------|---------------|
| CPU | AMD Ryzen AI 9 HX 370 (12 Kerne, bis 5.1 GHz) |
| iGPU | Radeon 890M (integrierte Grafikeinheit) |
| RAM | 32 GB DDR5 |
| OS | Windows 11 Home |
| KI-Beschleunigung | AMD Ryzen AI NPU (für zukünftige ONNX-Modelle) |

### Geplante Server-Hardware (Desktop)

| Komponente | Spezifikation |
|------------|---------------|
| CPU | Intel Core i7 4. Generation |
| GPU | NVIDIA GTX 1050 (2 GB VRAM) |
| Einsatz | Backend-Server für Videoanalyse im Heimnetzwerk |

### Netzwerkkonfiguration

```
Laptop (Entwicklung):  http://localhost:3000 (Frontend)
                       http://localhost:8000 (Backend)

Desktop (Produktion):  http://192.168.1.xxx:3000 (Frontend)
                       http://192.168.1.xxx:8000 (Backend)
```

### Speicherstruktur

```
ttlab/data/
├── videos/          # Hochgeladene Originalvideos (MP4, MOV, etc.)
├── clips/           # Extrahierte Rally-Clips (einzelne MP4-Dateien)
└── ttlab.db         # SQLite-Datenbank (Development)
```

**Hinweis:** Der `data/`-Ordner ist in `.gitignore` ausgeschlossen und wird nicht versioniert.

---

## Tech Stack

### Frontend

| Technologie | Version | Zweck |
|-------------|---------|-------|
| Next.js | 16.3.0 | React-Framework mit App Router |
| React | 19.0.0 | UI-Komponenten |
| TypeScript | 5.x | Typsicherheit |
| Tailwind CSS | 3.4.1 | Styling |
| FFmpeg.wasm | (geplant) | Client-seitige Videovorverarbeitung |

### Backend

| Technologie | Version | Zweck |
|-------------|---------|-------|
| FastAPI | 0.115.6 | REST-API mit automatischer OpenAPI-Dokumentation |
| Python | 3.13 | Backend-Logik |
| SQLAlchemy | 2.0.36 | ORM für Datenbankzugriffe |
| SQLite | 3.x | Development-Datenbank |
| PostgreSQL | 16+ (geplant) | Produktionsdatenbank |
| Alembic | (geplant) | Database Migrations |

### Video & Audio

| Technologie | Version | Zweck |
|-------------|---------|-------|
| OpenCV | 4.11.0 | Bildverarbeitung, Motion Detection |
| FFmpeg | 7.x | Video-Extraktion, Encoding |
| librosa | 0.11.0 | Audioanalyse (Peak Detection) |
| NumPy | 2.2.1 | Array-Operationen |

### KI & Machine Learning

| Technologie | Version | Zweck |
|-------------|---------|-------|
| KIT-Modelle | kit.qwen3.5-397b-A17b | Code-Generierung, Dokumentation (kostenlos) |
| Azure OpenAI | Backup ($5/Monat Budget) | Fallback bei komplexen Tasks |
| YOLOv8 | (V0.4 geplant) | Ball-Tracking Modell |
| RT-DETR | (Alternative zu YOLO) | Echtzeit-Objektdetektion |

### Entwicklungstools

| Tool | Zweck |
|------|-------|
| Git | Versionskontrolle |
| GitHub Desktop / CLI | Repository-Management |
| uv | Python Package Manager (schneller als pip) |
| npm/pnpm | Node.js Package Manager |
| Windows PowerShell | Shell-Umgebung |

---

## Architektur

### Systemarchitektur (Übersicht)

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Client)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Next.js Frontend (:3000)                 │   │
│  │  - Dashboard                                         │   │
│  │  - Match-Detail mit Video-Player                     │   │
│  │  - Tisch-Kalibrierung UI                             │   │
│  │  - Rally-Timeline                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (:8000)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  main.py     │  │  models.py   │  │  database.py │      │
│  │  (API Routes)│  │  (SQLAlchemy)│  │  (DB Conn)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ rally_       │  │ video_       │                         │
│  │ detection.py │  │ processor.py │                         │
│  │  - Motion    │  │  - FFmpeg    │                         │
│  │  - Audio     │  │  - Clipping  │                         │
│  │  - Ball      │  │              │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Background Analysis Job                  │   │
│  │  - Asynchrone Videoanalyse                           │   │
│  │  - Fortschrittsverfolgung                            │   │
│  │  - Rally-Erkennung & Validierung                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy Async
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     SQLite / PostgreSQL                      │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │  matches Table     │  │  rallies Table     │            │
│  │  - id              │  │  - id              │            │
│  │  - title           │  │  - match_id        │            │
│  │  - date            │  │  - start_time      │            │
│  │  - player_name     │  │  - end_time        │            │
│  │  - opponent_name   │  │  - confidence      │            │
│  │  - result          │  │  - impact_count    │            │
│  │  - score           │  │  - validation_status│           │
│  │  - notes           │  │  - table_corners   │            │
│  │  - status          │  │  - clip_path       │            │
│  │  - table_corners   │  │  - highlights      │            │
│  │  - created_at      │  │  - created_at      │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Filesystem
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      data/ Directory                         │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │  videos/           │  │  clips/            │            │
│  │  - original.mp4    │  │  - rally_1.mp4     │            │
│  │  - training.mov    │  │  - rally_2.mp4     │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Datenfluss (Video-Upload → Analyse)

```
1. User lädt Video über Frontend hoch
           │
           ▼
2. Backend speichert Datei in data/videos/{uuid}_{filename}
           │
           ▼
3. POST /api/matches/{id}/analyze startet Background-Job
           │
           ├─► 3a. Motion Detection (OpenCV MOG2)
           │       - Foreground-Mask berechnen
           │       - Konturen finden
           │       - Bewegung im kalibrierten Tischbereich?
           │
           ├─► 3b. Audio Peak Detection (librosa)
           │       - RMS-Energie berechnen
           │       - Schwellenwert-basierte Peak-Erkennung
           │       - Ball-Schläger-Impakt identifizieren
           │
           ├─► 3c. Ball Candidate Detection
           │       - Helle Blobs im Tischbereich (180-255 RGB)
           │       - Größe: 3-15 Pixel Durchmesser
           │       - Bewegung zwischen Frames tracken
           │
           ▼
4. Rally-Erkennung kombiniert alle Signale
           │
           ├─► Motion + Audio = möglicher Rally-Start
           │
           ├─► Ball-Kandidat bestätigt = höhere Confidence
           │
           ├─► Mehrere Impacts (impact_count ≥ 3) = validierter Rally
           │
           ▼
5. Rally wird in Datenbank gespeichert
           │
           ├─► start_time, end_time (ms)
           │
           ├─► confidence (0.0 - 1.0)
           │
           ├─► validation_status ("review" initial)
           │
           ▼
6. FFmpeg extrahiert Clip nach data/clips/rally_{id}.mp4
           │
           ▼
7. Frontend zeigt Rally in Timeline an (sobald verfügbar)
```

---

## Entwicklungsphilosophie

### Prioritäten (absteigend)

1. **Funktionalität vor Geschwindigkeit**
   - Lieber korrekte Erkennung als schnelle falsche Ergebnisse
   - Hintergrundanalyse darf mehrere Minuten dauern
   - User Experience leidet nicht unter Wartezeit (Fortschrittsanzeige)

2. **Robustheit vor Performance**
   - Edge Cases behandeln (korrupte Videos, fehlende Audio-Spur)
   - Graceful Degradation (wenn Ballerkennung fehlschlägt → nur Motion+Audio)
   - Datenbank-Migrationen rückwärtskompatibel

3. **Lokal vor Cloud**
   - Keine externen APIs für Kernfunktionen
   - Datenschutz durch lokale Speicherung
   - Offline-Fähigkeit (kein Internet required after setup)

4. **Einfachheit vor Komplexität**
   - Monolithische Architektur (keine Microservices)
   - SQLite für Development (kein Docker Compose Overhead)
   - Klare, lesbare Code-Struktur vor cleveren Optimierungen

### Code-Qualitätsprinzipien

- **Typsicherheit:** TypeScript strikt aktivieren, keine `any`-Types
- **Async/Await:** Alle I/O-Operationen asynchron (FastAPI, SQLAlchemy)
- **Fehlerbehandlung:** Try/Catch mit aussagekräftigen Error-Messages
- **Logging:** Console.log für Dev, strukturiertes Logging für Prod (geplant)
- **Dokumentation:** Inline-Kommentare nur bei komplexer Logik, sonst sprechende Variablennamen

---

## Versionshistorie

### V0.1 (Erstversion - abgeschlossen)

**Kernfunktionen implementiert:**

- ✅ Video-Upload (Drag & Drop + Dateiauswahl)
- ✅ Automatische Ballwechsel-Erkennung (Motion + Audio)
- ✅ Rally-Clip-Extraktion mit FFmpeg
- ✅ Web-Player mit integrierter Timeline
- ✅ Highlight-Erkennung (Confidence-basiert)
- ✅ Match-Management (Liste, Löschen, Details)

**Technische Meilensteine:**

- FastAPI Backend mit Async-Support
- Next.js Frontend mit App Router
- SQLite-Datenbank mit SQLAlchemy ORM
- OpenCV Motion Detection (MOG2 Algorithmus)
- librosa Audio Peak Detection (RMS-Energie)

**Bekannte Limitationen:**

- Keine manuelle Kalibrierung (ganzer Videorahmen wird analysiert)
- Falschpositive Erkennung bei Gehbewegungen
- Keine Metadaten (Datum, Spieler, Ergebnis)

---

### V0.2 (Metadaten & Statistik - abgeschlossen)

**Neue Funktionen:**

- ✅ Match-Metadaten (Datum, Spieler, Gegner, Ergebnis, Score, Notizen)
- ✅ Ergebnis-Filter (alle / Siege / Niederlagen)
- ✅ Dashboard-Statistiken (Gesamtübersicht)
- ✅ PATCH-API für Match-Updates
- ✅ Verbesserte Rally-Timeline (visuelle Confidence-Anzeige)

**Database Changes:**

- `matches`-Tabelle erweitert um:
  - `player_name`, `opponent_name`
  - `result` (win/loss/unknown)
  - `score` (z.B. "3:2", "11:9 8:11 11:7")
  - `notes` (Freitext für Taktik-Notizen)

**UI-Verbesserungen:**

- MatchCards zeigen Ergebnis-Badge (grün/rot)
- Filter-Dropdown oben rechts im Dashboard
- Statistik-Cards oben (Matches, Siege, Quote)
- Editierbare Metadaten im Detail-View

**API-Endpunkte hinzugefügt:**

- `PATCH /api/matches/{id}` - Update Metadaten
- `GET /api/matches?result=win` - Filtern nach Ergebnis

---

### V0.3 (Tischkalibrierung & Validierung - aktuell)

**Neue Funktionen:**

- ✅ Manuelle Tischkalibrierung (4 Ecken anklicken)
- ✅ Ballkandidaten-Erkennung im markierten Bereich
- ✅ Rally-Validierungsstatus (`accepted`/`review`/`rejected`)
- ✅ Confidence & Impact_Count Metriken
- ✅ 100ms-Schritt Navigation (Pfeiltasten ← →)
- ✅ Auto-Play Queue (nächster Rally startet automatisch)
- ✅ Highlight-Filter Toggle (nur akzeptierte Rallies)
- ✅ "Kein Ballwechsel" Reject-Button

**Algorithmus-Verbesserungen:**

- Motion Detection nur noch im kalibrierten Tischbereich
- Ball-Kandidaten: Helligkeit 180-255 RGB + Größe 3-15px
- Impact Counter zählt Audio-Peaks pro Rally
- Confidence-Score kombiniert Motion + Audio + Ball

**Database Changes:**

- `rallies`-Tabelle erweitert um:
  - `validation_status` (default: "review")
  - `impact_count` (Anzahl Ball-Schläger-Kontakte)
  - `table_corners` (JSON mit 4 Koordinaten)
  - `clip_path` (relativer Pfad zum extrahierten Clip)

- `matches`-Tabelle erweitert um:
  - `table_corners` (globale Kalibrierung fürs ganze Match)
  - `status` (pending/analyzing/ready/error)

**UI-Komponenten:**

- Canvas-Overlay für Tischkalibrierung
- RallyItem zeigt Validierungs-Icon (✅ ⚠️ ❌)
- Bulk-Actions ("Alle akzeptieren", "Export")
- Fortschrittsanzeige während Analyse

**Performance-Optimierungen:**

- Lazy Loading für Rally-Clips (erst bei Klick laden)
- Debounced API Calls bei Kalibrierung
- Background-Analyse ohne Blockierung des UI

---

### V0.4 (Geplant - Ball-Tracking Modell)

**Ziele:**

- Trainiertes YOLOv8n oder RT-DETR Modell für Ball-Erkennung
- Reduktion False Positives (Gehbewegungen, Serve-Vorbereitung)
- Ball-Trajektorie-Analyse (Flugkurve rekonstruieren)
- Spin-Erkennung (Magnus-Effekt sichtbar machen)

**Meilensteine:**

1. Labeling-Tool erstellen (500-1000 Frames manuell annotieren)
2. Datensatz zusammenstellen (verschiedene Beleuchtungen, Winkel)
3. Modell trainieren (YOLOv8n auf GTX 1050)
4. Integration in Rally-Erkennung (Ball-Tracking als zusätzlicher Input)
5. Evaluation (Precision/Recall auf Test-Videos)

**Erwartete Verbesserungen:**

- False Positive Rate: ~40% → ~10%
- Confidence-Score genauer durch Ball-Präsenz
- Serve-Erkennung (Ballwurf → erster Kontakt)

---

### V0.5 (Geplant - Shot-Klassifikation)

**Ziele:**

- Vorhand vs. Rückhand erkennen
- Topspin vs. Slice vs. Block unterscheiden
- Schlägerwinkel schätzen (OpenCV Pose Estimation)
- Ballflugbahn vorhersagen (wo würde Ball landen?)

**ML-Modell:**

- CNN für Frame-basierte Klassifikation
- LSTM für Sequenz-Analyse (mehrere Frames)
- Multi-Task Learning (Shot-Type + Landing-Position)

---

### V0.6 (Geplant - Taktik-Analyse)

**Ziele:**

- Mustererkennung (welche Bälle führt zu Punktgewinn?)
- Schwachstellen-Analyse (wo verliere ich meistens Punkte?)
- Gegner-Profilierung (stärkere/schwächere Seiten)
- Automatisches Highlight-Reel (beste Ballwechsel)

**Features:**

- Heatmap der Balllandepositionen
- Zeitlinien-Visualisierung (Score-Verlauf)
- Vergleich zwischen Matches (Fortschritt tracking)

---

## Aktueller Entwicklungsstand

### Abgeschlossene Tasks (V0.1 - V0.3)

#### Backend

- [x] FastAPI-App mit allen API-Endpunkten
- [x] SQLAlchemy-Modelle (Match, Rally)
- [x] Async-Datenbankverbindungen
- [x] Migration-Logik für Legacy-Daten
- [x] RallyDetector-Klasse (Motion + Audio + Ball)
- [x] VideoProcessor (FFmpeg Wrapper)
- [x] Background-Job für Videoanalyse
- [x] Status-Tracking (pending → analyzing → ready)
- [x] Error-Handling mit sinnvollen Fehlermeldungen

#### Frontend

- [x] Dashboard mit Match-Übersicht
- [x] MatchDetail-Komponente mit Video-Player
- [x] Tischkalibrierung UI (Canvas mit 4 Klick-Punkten)
- [x] Rally-Timeline mit Scroll-Container
- [x] Highlight-Filter Toggle
- [x] Auto-Play Queue
- [x] 100ms-Schritt Navigation (Pfeiltasten)
- [x] Result-Filter (Siege/Niederlagen/Alle)
- [x] Statistik-Cards (Gesamtübersicht)
- [x] Delete-Button für Matches
- [x] Export-Funktion (Highlights concat)

#### Infrastruktur

- [x] `.gitignore` (data/, venv/, node_modules/, .env)
- [x] `.gitattributes` (Line Endings: LF für Code, CRLF für .bat)
- [x] `README.md` mit Projektübersicht
- [x] `TTLab starten.bat` (Dual-Server Startup-Skript)
- [x] Backend-Installation mit uv (Python 3.13)
- [x] Frontend-Installation mit npm (Node.js 20+)

#### Dokumentation

- [x] Diese Projektübergabe erstellt
- [x] API-Dokumentation (/docs Swagger UI)
- [x] Inline-Kommentare bei komplexer Logik
- [x] Versionshistorie im README

---

### Aktive Baustellen

#### Rally-Erkennung (False Positives)

**Problem:** Aktuelle Erkennung produziert zu viele falsch-positive Rallies

**Ursachen:**

1. Gehbewegungen vor/nach dem Tisch werden als Rally erkannt
2. Serve-Vorbereitung ("hier ist dein Ball") wird detektiert
3. Schattenbewegungen bei schlechter Beleuchtung
4. Kamera-Wackeln wird als Motion interpretiert

**Aktuelle Gegenmaßnahmen:**

- Tischkalibrierung begrenzt Analysebereich
- Audio-Peaks bestätigen Ball-Schläger-Kontakt
- Mind. 3 Impacts erforderlich für validierten Rally

**Restprobleme:**

- Immer noch ~30-40% False Positive Rate
- Einfache Helligkeitsfilterung (180-255 RGB) zu ungenau
- Kleine/schnelle Bälle werden übersehen

**Nächster Schritt (V0.4):** Trainiertes Ball-Tracking-Modell entwickeln

---

#### GitHub-Repository Setup

**Status:** In Progress

**Aufgaben:**

- [ ] Initiales Git-Repository erstellen (`git init`)
- [ ] Erstes Commit mit allen Dateien (`git add .`, `git commit`)
- [ ] Remote-Repository auf GitHub anlegen
- [ ] Push durchführen (`git remote add origin`, `git push -u origin main`)

**Entscheidung ausstehend:** User wählt zwischen

- **GitHub Desktop:** GUI-basiert, einfacher für Einsteiger
- **Git CLI:** Befehlszeile, mehr Kontrolle, Skript-fähig

**Empfohlene Vorgehensweise:**

```bash
cd C:\Users\Jonas\Documents\OpenCode\ttlab
git init
git add .
git commit -m "Initial commit: TTLab V0.3"
# GitHub Desktop: Repository hinzufügen und pushen
# ODER CLI:
git remote add origin https://github.com/USERNAME/ttlab.git
git branch -M main
git push -u origin main
```

---

### Technische Schulden

#### Fehlende Automated Tests

**Status:** Nur manuelles Testing durchgeführt

**Risiken:**

- Regressionen bei Code-Änderungen unbemerkt
- Schwer zu refaktorisieren ohne Safety Net
- Neue Features können bestehende brechen

**Geplante Tests:**

```python
# tests/test_rally_detection.py
def test_motion_detection_with_static_camera():
    """Bewegungserkennung sollte bei statischem Hintergrund funktionieren"""
    pass

def test_audio_peak_detection_silence():
    """Stille Abschnitte sollten keine Peaks erzeugen"""
    pass

def test_ball_candidate_white_ball():
    """Weiße Bälle sollten korrekt erkannt werden"""
    pass

def test_table_calibration_polygon():
    """Kalibrierung sollte gültiges Polygon erzeugen"""
    pass
```

```typescript
// __tests__/MatchDetail.test.tsx
test('renders rally timeline with correct items', () => {
  // ...
});

test('keyboard navigation moves video by 100ms', () => {
  // ...
});
```

**Priorität:** Mittel (nach V0.4 Release)

---

#### Database Migrations

**Status:** Manuelle Migration-Logik in `database.py`

**Aktueller Ansatz:**

```python
# Manuelles Hinzufügen neuer Spalten beim Startup
async def migrate_database():
    async with engine.begin() as conn:
        # Prüfen ob Spalte existiert, wenn nicht → hinzufügen
        if not column_exists("matches", "table_corners"):
            await conn.execute(text("ALTER TABLE matches ADD COLUMN table_corners JSON"))
```

**Probleme:**

- Nicht versioniert (keine Historie der Schema-Änderungen)
- Fehleranfällig bei komplexen Migrationen
- Keine Rollback-Funktionalität

**Geplante Lösung:** Alembic einführen

```bash
alembic init alembic
alembic revision --autogenerate -m "Add table_corners to matches"
alembic upgrade head
```

**Priorität:** Niedrig (funktioniert aktuell, aber langfristig notwendig)

---

#### Long-Video Timeout

**Problem:** Videos >5 Minuten können Browser-Timeout (300s) treffen

**Aktuelles Verhalten:**

- Upload startet Background-Analyse
- Frontend pollt Status alle 2 Sekunden
- Bei Timeout: User sieht "Analyzing...", aber Backend arbeitet weiter
- Nach Abschluss: Status wechselt zu "ready", User muss Seite neu laden

**Workaround:**

- Background-Job läuft unabhängig vom Frontend
- Datenbank speichert Fortschritt (current_frame / total_frames)
- User kann Browser schließen und später zurückkommen

**Langfristige Lösung:**

- WebSocket für Echtzeit-Fortschrittsupdates
- Server-Sent Events (SSE) als Alternative
- Chunked Upload für große Videos

**Priorität:** Niedrig (betrifft selten lange Trainingsvideos)

---

## Bekannte Probleme

### 1. False Positive Rally-Erkennung

**Symptom:** Gehbewegungen, Serve-Vorbereitung werden als Ballwechsel erkannt

**Ursache:** Motion Detection allein unterscheidet nicht zwischen Ball und Person

**Workaround:** Manuelle Validierung im Frontend (Review-Queue)

**Lösung:** V0.4 mit trainiertem Ball-Tracking-Modell

**Severity:** Mittel (beeinträchtigt UX, aber funktional)

---

### 2. Ball-Erkennung bei schlechtem Licht

**Symptom:** Weiße Bälle werden nicht erkannt bei dunklem Hintergrund

**Ursache:** Einfacher Helligkeitsfilter (180-255 RGB) zu starr

**Workaround:** Gute Beleuchtung beim Aufnehmen sicherstellen

**Lösung:** Adaptiver Schwellenwert (Otsu's Method) oder ML-Modell

**Severity:** Mittel (betrifft ~20% der Videos)

---

### 3. Lange Ladezeiten bei vielen Rallies

**Symptom:** Timeline braucht mehrere Sekunden zum Rendern bei 100+ Rallies

**Ursache:** Alle Rally-Items werden sofort gerendert (kein Virtual Scrolling)

**Workaround:** Highlight-Filter aktivieren (zeigt nur akzeptierte Rallies)

**Lösung:** React Window für Virtual Scrolling implementieren

**Severity:** Niedrig (betrifft nur sehr lange Matches)

---

### 4. Kein Mobile Support

**Symptom:** Frontend ist nicht responsive auf Smartphones

**Ursache:** Fokus auf Desktop-Usage (Trainer am PC analysieren)

**Workaround:** Tablet im Querformat verwenden

**Lösung:** Media Queries für Mobile Breakpoints (< 768px)

**Severity:** Niedrig (Mobile nicht primärer Use-Case)

---

### 5. SQLite Locking bei parallelen Zugriffen

**Symptom:** "Database is locked" Fehler bei gleichzeitigen Requests

**Ursache:** SQLite erlaubt nur einen Writer gleichzeitig

**Workaround:** Sequential Processing (ein Video nach dem anderen)

**Lösung:** PostgreSQL für Production einsetzen

**Severity:** Niedrig (Development-only Problem)

---

## Roadmap

### Kurzfristig (Q3 2026)

| Feature | Status | Priorität | Aufwand |
|---------|--------|-----------|---------|
| GitHub Repo Setup | 🟡 In Progress | Hoch | 1h |
| V0.4 Planning | ⚪ Pending | Hoch | 2h |
| Labeling Tool | ⚪ Pending | Hoch | 8h |
| Datensatz sammeln (500-1000 Frames) | ⚪ Pending | Hoch | 4h |
| YOLOv8n Training | ⚪ Pending | Hoch | 6h |
| Ball-Tracking Integration | ⚪ Pending | Hoch | 12h |

### Mittelfristig (Q4 2026)

| Feature | Status | Priorität | Aufwand |
|---------|--------|-----------|---------|
| Shot-Klassifikation (Vorhand/Rückhand) | ⚪ Pending | Mittel | 16h |
| Taktik-Analyse (Heatmaps) | ⚪ Pending | Mittel | 20h |
| PostgreSQL Migration | ⚪ Pending | Mittel | 8h |
| Automated Tests (Unit + Integration) | ⚪ Pending | Mittel | 12h |
| WebSocket für Live-Fortschritt | ⚪ Pending | Niedrig | 6h |

### Langfristig (Q1 2027)

| Feature | Status | Priorität | Aufwand |
|---------|--------|-----------|---------|
| Multi-Camera Support | ⚪ Pending | Niedrig | 24h |
| 3D-Trajektorie Rekonstruktion | ⚪ Pending | Niedrig | 32h |
| Cloud-Sync (optional) | ⚪ Pending | Niedrig | 16h |
| Plugin-System für Erweiterungen | ⚪ Pending | Niedrig | 20h |
| Mobile App (React Native) | ⚪ Pending | Niedrig | 40h |

---

## Dateistruktur

```
ttlab/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI App, alle API-Routen
│   │   ├── models.py            # SQLAlchemy Modelle (Match, Rally)
│   │   ├── database.py          # DB-Connection, Sessions, Migration-Logik
│   │   ├── rally_detection.py   # RallyDetector Klasse (Motion, Audio, Ball)
│   │   ├── video_processor.py   # FFmpeg Wrapper für Clip-Extraktion
│   │   └── schemas.py           # Pydantic Schemas für Request/Response
│   │
│   ├── venv/                    # Python Virtual Environment (nicht versioniert)
│   ├── pyproject.toml           # Python Dependencies (uv)
│   └── uv.lock                  # Dependency Lockfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root Layout mit Providers
│   │   ├── page.tsx             # Dashboard (Match-Liste, Stats)
│   │   └── globals.css          # Globale Styles (Tailwind)
│   │
│   ├── components/
│   │   ├── MatchList.tsx        # Match-Übersicht mit Filter
│   │   ├── MatchDetail.tsx      # Detail-View mit Player & Kalibrierung
│   │   └── ui/                  # Wiederverwendbare UI-Komponenten
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       └── input.tsx
│   │
│   ├── public/                  # Statische Assets
│   ├── next.config.ts           # Next.js Konfiguration
│   ├── package.json             # Node.js Dependencies
│   ├── tailwind.config.ts       # Tailwind Konfiguration
│   └── tsconfig.json            # TypeScript Konfiguration
│
├── data/                        # NICHT versioniert (.gitignore)
│   ├── videos/                  # Originalvideos (hochgeladen von Usern)
│   ├── clips/                   # Extrahierte Rally-Clips
│   └── ttlab.db                 # SQLite Datenbank
│
├── .git/                        # Git Repository
├── .gitignore                   # Ausschlussregeln (data/, venv/, node_modules/)
├── .gitattributes               # Line Endings (LF für Code, CRLF für .bat)
├── README.md                    # Projektübersicht & Quickstart
├── TTLab starten.bat            # Windows Startup-Skript (Desktop)
└── PROJEKTUEBERGABE.md          # Dieses Dokument (ausführliche Dokumentation)
```

---

## API-Referenz

### Base URL

```
Development: http://localhost:8000
Production:  http://<server-ip>:8000
```

### Endpunkte

#### GET /api/matches

**Beschreibung:** Alle Matches abrufen (optional gefiltert)

**Query Parameters:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `result` | string | - | Filter nach Ergebnis: `win`, `loss`, `unknown` |
| `limit` | integer | 100 | Maximale Anzahl zurückgegebener Matches |
| `offset` | integer | 0 | Pagination Offset |

**Response:**

```json
{
  "matches": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Training vs. Roboter",
      "date": "2026-08-15",
      "player_name": "Jonas",
      "opponent_name": "Roboter",
      "result": "win",
      "score": "3:0",
      "notes": "Aufschlag gut trainiert",
      "status": "ready",
      "table_corners": [[100, 200], [500, 200], [500, 400], [100, 400]],
      "created_at": "2026-08-15T14:30:00Z",
      "rally_count": 47,
      "video_path": "/api/videos/550e8400-e29b-41d4-a716-446655440000.mp4"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

**Status Codes:**

- `200 OK`: Erfolgreich
- `400 Bad Request`: Ungültige Query Parameters

---

#### POST /api/matches

**Beschreibung:** Neues Match erstellen (mit Video-Upload)

**Request Body (multipart/form-data):**

| Field | Typ | Required | Beschreibung |
|-------|-----|----------|--------------|
| `title` | string | Ja | Titel des Matches |
| `date` | string | Nein | Datum (ISO 8601: YYYY-MM-DD) |
| `player_name` | string | Nein | Name des Spielers |
| `opponent_name` | string | Nein | Name des Gegners |
| `result` | string | Nein | Ergebnis: `win`, `loss`, `unknown` |
| `score` | string | Nein | Score (z.B. "3:2") |
| `notes` | string | Nein | Freitext-Notizen |
| `video` | file | Ja | Videodatei (MP4, MOV, AVI, etc.) |

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Training vs. Roboter",
  "status": "pending",
  "message": "Match erstellt. Analyse startet im Hintergrund."
}
```

**Status Codes:**

- `201 Created`: Match erfolgreich erstellt
- `400 Bad Request`: Fehlende Felder oder ungültiges Video-Format
- `500 Internal Server Error`: Server-Fehler beim Speichern

---

#### GET /api/matches/{id}

**Beschreibung:** Einzelnes Match mit Details abrufen

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Matches |

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Training vs. Roboter",
  "date": "2026-08-15",
  "player_name": "Jonas",
  "opponent_name": "Roboter",
  "result": "win",
  "score": "3:0",
  "notes": "Aufschlag gut trainiert",
  "status": "ready",
  "table_corners": [[100, 200], [500, 200], [500, 400], [100, 400]],
  "created_at": "2026-08-15T14:30:00Z",
  "rallies": [
    {
      "id": "rally-001",
      "match_id": "550e8400-e29b-41d4-a716-446655440000",
      "start_time": 12500,
      "end_time": 15800,
      "confidence": 0.87,
      "impact_count": 5,
      "validation_status": "accepted",
      "table_corners": [[100, 200], [500, 200], [500, 400], [100, 400]],
      "clip_path": "/api/clips/rally-001.mp4",
      "highlights": [13000, 14500],
      "created_at": "2026-08-15T14:32:00Z"
    }
  ],
  "video_path": "/api/videos/550e8400-e29b-41d4-a716-446655440000.mp4"
}
```

**Status Codes:**

- `200 OK`: Erfolgreich
- `404 Not Found`: Match mit ID nicht gefunden

---

#### PATCH /api/matches/{id}

**Beschreibung:** Match-Metadaten aktualisieren

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Matches |

**Request Body (JSON):**

```json
{
  "title": "Updated Title",
  "result": "loss",
  "score": "2:3",
  "notes": "Neue Notizen"
}
```

**Alle Felder optional.** Nur angegebene Felder werden aktualisiert.

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Title",
  "result": "loss",
  "score": "2:3",
  "notes": "Neue Notizen",
  "message": "Match aktualisiert"
}
```

**Status Codes:**

- `200 OK`: Erfolgreich aktualisiert
- `400 Bad Request`: Ungültige Daten (z.B. `result` nicht in `[win, loss, unknown]`)
- `404 Not Found`: Match mit ID nicht gefunden

---

#### POST /api/matches/{id}/analyze

**Beschreibung:** Videoanalyse manuell starten (Background-Job)

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Matches |

**Request Body:** Keiner erforderlich

**Response:**

```json
{
  "message": "Analyse gestartet",
  "status": "analyzing"
}
```

**Status Codes:**

- `202 Accepted`: Analyse erfolgreich gestartet
- `400 Bad Request`: Match hat kein Video oder bereits analysiert
- `404 Not Found`: Match mit ID nicht gefunden

**Hinweis:** Die Analyse läuft asynchron im Hintergrund. Status kann über `GET /api/matches/{id}` abgefragt werden.

---

#### GET /api/rallies/{id}

**Beschreibung:** Einzelnen Rally mit Details abrufen

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Rallies |

**Response:**

```json
{
  "id": "rally-001",
  "match_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": 12500,
  "end_time": 15800,
  "confidence": 0.87,
  "impact_count": 5,
  "validation_status": "accepted",
  "table_corners": [[100, 200], [500, 200], [500, 400], [100, 400]],
  "clip_path": "/api/clips/rally-001.mp4",
  "highlights": [13000, 14500],
  "created_at": "2026-08-15T14:32:00Z"
}
```

**Status Codes:**

- `200 OK`: Erfolgreich
- `404 Not Found`: Rally mit ID nicht gefunden

---

#### PATCH /api/rallies/{id}

**Beschreibung:** Rally-Validierungsstatus aktualisieren

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Rallies |

**Request Body (JSON):**

```json
{
  "validation_status": "accepted"
}
```

**Erlaubte Werte für `validation_status`:** `accepted`, `review`, `rejected`

**Response:**

```json
{
  "id": "rally-001",
  "validation_status": "accepted",
  "message": "Rally aktualisiert"
}
```

**Status Codes:**

- `200 OK`: Erfolgreich aktualisiert
- `400 Bad Request`: Ungültiger Status
- `404 Not Found`: Rally mit ID nicht gefunden

---

#### DELETE /api/rallies/{id}

**Beschreibung:** Rally löschen (inkl. Clip-Datei)

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Rallies |

**Response:**

```json
{
  "message": "Rally gelöscht"
}
```

**Status Codes:**

- `200 OK`: Erfolgreich gelöscht
- `404 Not Found`: Rally mit ID nicht gefunden

---

#### GET /api/matches/{id}/export-highlights

**Beschreibung:** Alle akzeptierten Rallies als einzelnes Video exportieren

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | UUID | ID des Matches |

**Query Parameters:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `min_confidence` | float | 0.7 | Minimale Confidence für Export |

**Response:** Download des exportierten Videos (`highlights_{match_id}.mp4`)

**Status Codes:**

- `200 OK`: Export erfolgreich (File-Download)
- `404 Not Found`: Match mit ID nicht gefunden
- `400 Bad Request:` Keine akzeptierten Rallies vorhanden

**Hinweis:** FFmpeg concat demuxer wird verwendet, um Clips ohne Re-Encoding zu verbinden (schnell).

---

#### GET /api/videos/{match_id}

**Beschreibung:** Originalvideo streamen (für HTML5 Video-Player)

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `match_id` | UUID | ID des Matches |

**Headers:**

- `Accept-Ranges: bytes` (Partial Content Support für Seek)
- `Content-Type: video/mp4`

**Response:** Video-Stream mit Range-Support

**Status Codes:**

- `200 OK`: Vollständiges Video
- `206 Partial Content:` Angeforderter Byte-Range
- `404 Not Found:` Video nicht gefunden

---

#### GET /api/clips/{rally_id}

**Beschreibung:** Extrahierten Rally-Clip streamen

**Path Parameters:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `rally_id` | UUID | ID des Rallies |

**Headers:**

- `Accept-Ranges: bytes`
- `Content-Type: video/mp4`

**Response:** Video-Stream

**Status Codes:**

- `200 OK`: Stream erfolgreich
- `404 Not Found:` Clip nicht gefunden

---

#### GET /health

**Beschreibung:** Health Check für Monitoring

**Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.3.0"
}
```

**Status Codes:**

- `200 OK`: Alles funktioniert
- `503 Service Unavailable`: Datenbank oder andere Abhängigkeit nicht verfügbar

---

#### GET /docs

**Beschreibung:** Interaktive API-Dokumentation (Swagger UI)

**Response:** HTML-Seite mit allen Endpunkten, Request/Response-Schemas und "Try it out"-Funktion

**URL:** `http://localhost:8000/docs`

---

## Datenbank-Schema

### matches Tabelle

| Spalte | Typ | Nullable | Default | Beschreibung |
|--------|-----|----------|---------|--------------|
| `id` | UUID | No | gen_random_uuid() | Primärschlüssel |
| `title` | VARCHAR(255) | No | - | Titel des Matches |
| `date` | DATE | Yes | CURRENT_DATE | Datum des Matches |
| `player_name` | VARCHAR(100) | Yes | NULL | Name des Spielers |
| `opponent_name` | VARCHAR(100) | Yes | NULL | Name des Gegners |
| `result` | VARCHAR(20) | Yes | 'unknown' | Ergebnis: win/loss/unknown |
| `score` | VARCHAR(50) | Yes | NULL | Score (z.B. "3:2", "11:9 8:11") |
| `notes` | TEXT | Yes | NULL | Freitext-Notizen |
| `status` | VARCHAR(20) | Yes | 'pending' | Status: pending/analyzing/ready/error |
| `table_corners` | JSON | Yes | NULL | 4 Ecken des Tisches: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] |
| `video_path` | VARCHAR(500) | Yes | NULL | Relativer Pfad zum Originalvideo |
| `created_at` | TIMESTAMP | Yes | CURRENT_TIMESTAMP | Erstellungszeitpunkt |
| `updated_at` | TIMESTAMP | Yes | CURRENT_TIMESTAMP | Letzte Aktualisierung |

**Indizes:**

- PRIMARY KEY auf `id`
- INDEX auf `status` (für Filterung nach analysierten Matches)
- INDEX auf `result` (für Statistik-Queries)

---

### rallies Tabelle

| Spalte | Typ | Nullable | Default | Beschreibung |
|--------|-----|----------|---------|--------------|
| `id` | UUID | No | gen_random_uuid() | Primärschlüssel |
| `match_id` | UUID | No | - | Fremdschlüssel zu matches.id |
| `start_time` | INTEGER | No | - | Startzeit in Millisekunden |
| `end_time` | INTEGER | No | - | Endzeit in Millisekunden |
| `confidence` | FLOAT | Yes | 0.0 | Erkennungs-Sicherheit (0.0-1.0) |
| `impact_count` | INTEGER | Yes | 0 | Anzahl Ball-Schläger-Kontakte |
| `validation_status` | VARCHAR(20) | Yes | 'review' | Status: accepted/review/rejected |
| `table_corners` | JSON | Yes | NULL | Tischkalibrierung für diesen Rally |
| `clip_path` | VARCHAR(500) | Yes | NULL | Relativer Pfad zum extrahierten Clip |
| `highlights` | JSON | Yes | NULL | Array von Highlight-Zeitpunkten [ms, ms, ...] |
| `created_at` | TIMESTAMP | Yes | CURRENT_TIMESTAMP | Erstellungszeitpunkt |

**Indizes:**

- PRIMARY KEY auf `id`
- FOREIGN KEY auf `match_id` (CASCADE DELETE)
- INDEX auf `validation_status` (für Filterung)
- INDEX auf `confidence` (für Sortierung nach Qualität)

**Constraints:**

- `CHECK (confidence >= 0.0 AND confidence <= 1.0)`
- `CHECK (start_time < end_time)`
- `CHECK (validation_status IN ('accepted', 'review', 'rejected'))`

---

### Entity-Relationship-Diagramm

```
┌─────────────────────────┐
│        matches          │
├─────────────────────────┤
│ PK  id                  │
│     title               │
│     date                │
│     player_name         │
│     opponent_name       │
│     result              │
│     score               │
│     notes               │
│     status              │
│     table_corners       │
│     video_path          │
│     created_at          │
│     updated_at          │
└─────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────┐
│         rallies         │
├─────────────────────────┤
│ PK  id                  │
│ FK  match_id ───────────┤
│     start_time          │
│     end_time            │
│     confidence          │
│     impact_count        │
│     validation_status   │
│     table_corners       │
│     clip_path           │
│     highlights          │
│     created_at          │
└─────────────────────────┘
```

---

### Migration-Historie

**V0.1 → V0.2:**

```sql
ALTER TABLE matches ADD COLUMN player_name VARCHAR(100);
ALTER TABLE matches ADD COLUMN opponent_name VARCHAR(100);
ALTER TABLE matches ADD COLUMN result VARCHAR(20) DEFAULT 'unknown';
ALTER TABLE matches ADD COLUMN score VARCHAR(50);
ALTER TABLE matches ADD COLUMN notes TEXT;
```

**V0.2 → V0.3:**

```sql
ALTER TABLE matches ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE matches ADD COLUMN table_corners JSON;

ALTER TABLE rallies ADD COLUMN validation_status VARCHAR(20) DEFAULT 'review';
ALTER TABLE rallies ADD COLUMN impact_count INTEGER DEFAULT 0;
ALTER TABLE rallies ADD COLUMN table_corners JSON;
ALTER TABLE rallies ADD COLUMN clip_path VARCHAR(500);
ALTER TABLE rallies ADD COLUMN highlights JSON;
ALTER TABLE rallies ADD COLUMN confidence FLOAT DEFAULT 0.0;
```

**Geplante Migrationen (V0.4):**

```sql
-- Für Ball-Tracking-Modell-Versionierung
ALTER TABLE rallies ADD COLUMN model_version VARCHAR(50);

-- Für erweiterte Statistiken
ALTER TABLE rallies ADD COLUMN shot_type VARCHAR(50); -- forehand/backhand
ALTER TABLE rallies ADD COLUMN landing_position JSON; -- {x, y} Koordinaten
```

---

## Setup & Installation

### Voraussetzungen

**Software:**

- Python 3.13 oder höher
- Node.js 20 oder höher
- Git (für Versionskontrolle)
- FFmpeg (für Video-Processing)

**Hardware (Minimum):**

- 8 GB RAM
- 4 CPU-Kerne
- 10 GB freier Speicherplatz
- GPU optional (beschleunigt ML-Inferenz)

---

### Backend Installation

**Schritt 1: Repository klonen**

```bash
cd C:\Users\Jonas\Documents\OpenCode
git clone https://github.com/USERNAME/ttlab.git
cd ttlab
```

**Schritt 2: Python Virtual Environment erstellen**

```bash
# Mit uv (empfohlen, schneller als venv)
uv venv

# Alternativ mit Standard venv
python -m venv venv
```

**Schritt 3: Virtual Environment aktivieren**

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**Schritt 4: Dependencies installieren**

```bash
# Mit uv (empfohlen)
uv pip install -r backend/pyproject.toml

# Mit pip
pip install -r backend/requirements.txt
```

**Schritt 5: Umgebungsvariablen setzen (optional)**

```bash
# .env Datei im backend/ Verzeichnis erstellen
DATABASE_URL=sqlite+aiosqlite:///./data/ttlab.db
UPLOAD_DIR=./data/videos
CLIPS_DIR=./data/clips
DEBUG=true
```

**Schritt 6: Backend starten**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Erfolgskontrolle:**

- Terminal zeigt: `Uvicorn running on http://0.0.0.0:8000`
- Browser öffnen: `http://localhost:8000/docs`
- Swagger UI sollte alle API-Endpunkte anzeigen

---

### Frontend Installation

**Schritt 1: Dependencies installieren**

```bash
cd frontend
npm install
# oder
pnpm install
```

**Schritt 2: Development Server starten**

```bash
npm run dev
# oder
pnpm dev
```

**Erfolgskontrolle:**

- Terminal zeigt: `Ready in 1234ms`
- Browser öffnen: `http://localhost:3000`
- Dashboard sollte leer (keine Matches) oder mit Beispielen geladen werden

---

### One-Click Startup (Windows)

**TTLab starten.bat** im Projektroot enthält:

```batch
@echo off
echo Starting TTLab...

REM Backend in separatem Fenster starten
start "TTLab Backend" cmd /k "cd backend && .\venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM Warten bis Backend bereit ist
timeout /t 3 /nobreak >nul

REM Frontend in separatem Fenster starten
start "TTLab Frontend" cmd /k "cd frontend && npm run dev"

REM Browser öffnen
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo TTLab is running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Press any key to exit this window...
pause >nul
```

**Doppelklick auf die .bat-Datei startet:**

1. Backend-Server (Port 8000)
2. Frontend-Server (Port 3000)
3. Browser mit Frontend-URL

---

### Production Deployment (Desktop-Server)

**Schritt 1: Backend für Production bauen**

```bash
cd backend

# Dependencies installieren (ohne dev-dependencies)
uv pip install --no-deps fastapi sqlalchemy aiosqlite opencv-python librosa

# Gunicorn als ASGI Server (besser als Uvicorn für Production)
uv pip install gunicorn
```

**Schritt 2: systemd Service erstellen (Linux)**

```ini
# /etc/systemd/system/ttlab-backend.service
[Unit]
Description=TTLab Backend Service
After=network.target

[Service]
Type=simple
User=jonas
WorkingDirectory=/home/jonas/ttlab/backend
ExecStart=/home/jonas/ttlab/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ttlab-backend
sudo systemctl start ttlab-backend
```

**Schritt 3: Frontend statisch bauen**

```bash
cd frontend
npm run build

# Output: frontend/.next/ (Next.js Build)
```

**Schritt 4: Nginx Reverse Proxy konfigurieren**

```nginx
# /etc/nginx/sites-available/ttlab
server {
    listen 80;
    server_name ttlab.local;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ttlab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Schritt 5: Firewall konfigurieren**

```bash
# Nur Ports 80 (HTTP) und 443 (HTTPS) freigeben
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Wichtige Code-Stellen

### Backend

#### RallyDetector-Klasse

**Datei:** `backend/app/rally_detection.py`

**Zweck:** Kernlogik der Ballwechsel-Erkennung (Motion + Audio + Ball)

**Wichtige Methoden:**

```python
class RallyDetector:
    def __init__(self, table_corners: Optional[List[Tuple[int, int]]] = None):
        """
        Initialisiert den RallyDetector mit optionaler Tischkalibrierung.
        
        Args:
            table_corners: 4 Ecken des Tisches [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        """
        self.table_corners = table_corners
        self.bg_subtractor = cv2.createMOG2(history=500, varThreshold=100)
    
    def detect(self, video_path: str) -> List[RallyCandidate]:
        """
        Hauptmethode zur Rally-Erkennung.
        
        Returns:
            Liste von RallyCandidate-Objekten mit start_time, end_time, confidence
        """
        # 1. Motion Detection
        motion_events = self._detect_motion(video_path)
        
        # 2. Audio Peak Detection
        audio_peaks = self._detect_audio_peaks(video_path)
        
        # 3. Ball Candidate Detection
        ball_candidates = self._detect_ball_candidates(video_path)
        
        # 4. Fusion aller Signale
        rallies = self._fuse_signals(motion_events, audio_peaks, ball_candidates)
        
        return rallies
    
    def _detect_motion(self, video_path: str) -> List[MotionEvent]:
        """
        Bewegungserkennung mit OpenCV MOG2.
        
        Algorithmus:
        1. Hintergrundmodell erstellen
        2. Vordergrundmasken berechnen
        3. Konturen finden
        4. Bewegung im Tischbereich prüfen
        """
        # ... Implementierung ...
    
    def _detect_audio_peaks(self, video_path: str) -> List[AudioPeak]:
        """
        Audio-Peak-Erkennung mit librosa.
        
        Algorithmus:
        1. Audio extrahieren
        2. RMS-Energie berechnen
        3. Schwellenwert-basierte Peak-Erkennung
        4. Benachbarte Peaks mergen
        """
        # ... Implementierung ...
    
    def _detect_ball_candidates(self, video_path: str) -> List[BallCandidate]:
        """
        Ballkandidaten-Erkennung im kalibrierten Tischbereich.
        
        Algorithmus:
        1. Frames einlesen
        2. ROI (Tischbereich) extrahieren
        3. Helligkeitsfilter (180-255 RGB für weiße Bälle)
        4. Konturen finden, Größe prüfen (3-15px Durchmesser)
        5. Position zwischen Frames tracken
        """
        # ... Implementierung ...
    
    def _fuse_signals(
        self,
        motion_events: List[MotionEvent],
        audio_peaks: List[AudioPeak],
        ball_candidates: List[BallCandidate]
    ) -> List[RallyCandidate]:
        """
        Fusion aller Signale zu Rally-Kandidaten.
        
        Logik:
        - Motion + Audio innerhalb von 200ms = möglicher Rally-Start
        - Ball-Kandidat bestätigt = Confidence +0.2
        - Multiple Audio-Peaks (≥3) = impact_count erhöht
        - Dauer < 500ms = verwerfen (zu kurz für echten Rally)
        """
        # ... Implementierung ...
```

**Zeilennummern:** 1-250 (gesamte Datei)

---

#### FastAPI Main App

**Datei:** `backend/app/main.py`

**Zweck:** API-Routen, Background-Jobs, Error-Handling

**Wichtige Routen:**

```python
app = FastAPI(title="TTLab API", version="0.3.0")

@app.post("/api/matches")
async def create_match(
    title: str = Form(...),
    date: Optional[str] = Form(None),
    player_name: Optional[str] = Form(None),
    opponent_name: Optional[str] = Form(None),
    result: Optional[str] = Form(None),
    score: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    video: UploadFile = File(...)
):
    """
    Neues Match mit Video-Upload erstellen.
    """
    # 1. UUID generieren
    # 2. Video speichern
    # 3. Match in DB anlegen
    # 4. Background-Job starten
    # 5. Response zurückgeben

@app.post("/api/matches/{match_id}/analyze")
async def analyze_match(match_id: UUID):
    """
    Videoanalyse im Hintergrund starten.
    
    Background-Job:
    1. Video laden
    2. RallyDetector.initialisieren()
    3. detect() ausführen
    4. Rallies in DB speichern
    5. FFmpeg für Clip-Extraktion
    6. Status auf "ready" setzen
    """
    background_tasks.add_task(run_analysis, match_id)
    return {"status": "analyzing"}

@app.get("/api/matches")
async def get_matches(
    result: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Alle Matches abrufen (optional gefiltert).
    """
    # Query mit optionalem result-Filter
    # Pagination mit limit/offset

@app.patch("/api/matches/{match_id}")
async def update_match(match_id: UUID, update_data: MatchUpdate):
    """
    Match-Metadaten aktualisieren.
    """
    # Nur angegebene Felder updaten
    # Return updated match
```

**Zeilennummern:** 1-400 (gesamte Datei)

---

#### SQLAlchemy Modelle

**Datei:** `backend/app/models.py`

**Zweck:** Datenbank-Schema als Python-Klassen

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    date = Column(Date, default=date.today)
    player_name = Column(String(100), nullable=True)
    opponent_name = Column(String(100), nullable=True)
    result = Column(String(20), default="unknown")
    score = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    table_corners = Column(JSON, nullable=True)
    video_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    rallies = relationship("Rally", back_populates="match", cascade="all, delete-orphan")

class Rally(Base):
    __tablename__ = "rallies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    start_time = Column(Integer, nullable=False)  # Millisekunden
    end_time = Column(Integer, nullable=False)
    confidence = Column(Float, default=0.0)
    impact_count = Column(Integer, default=0)
    validation_status = Column(String(20), default="review")
    table_corners = Column(JSON, nullable=True)
    clip_path = Column(String(500), nullable=True)
    highlights = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    match = relationship("Match", back_populates="rallies")
```

**Zeilennummern:** 1-100 (gesamte Datei)

---

### Frontend

#### Dashboard Page

**Datei:** `frontend/app/page.tsx`

**Zweck:** Haupt-Dashboard mit Match-Übersicht und Statistiken

```typescript
'use client'

import { useState, useEffect } from 'react'
import MatchList from '../components/MatchList'
import StatsCards from '../components/StatsCards'

export default function Dashboard() {
  const [matches, setMatches] = useState([])
  const [filter, setFilter] = useState<'all' | 'win' | 'loss'>('all')
  
  useEffect(() => {
    // Matches von API laden
    fetch(`/api/matches?result=${filter}`)
      .then(res => res.json())
      .then(data => setMatches(data.matches))
  }, [filter])
  
  return (
    <div className="container mx-auto p-4">
      <StatsCards matches={matches} />
      <MatchList 
        matches={matches} 
        filter={filter}
        onFilterChange={setFilter}
      />
    </div>
  )
}
```

**Zeilennummern:** 1-100 (gesamte Datei)

---

#### MatchDetail Komponente

**Datei:** `frontend/components/MatchDetail.tsx`

**Zweck:** Detail-View mit Video-Player, Tischkalibrierung und Rally-Timeline

**Wichtige Features:**

```typescript
interface MatchDetailProps {
  matchId: string
}

export default function MatchDetail({ matchId }: MatchDetailProps) {
  const [match, setMatch] = useState(null)
  const [tableCorners, setTableCorners] = useState<Array<[number, number]>>([])
  const [currentTime, setCurrentTime] = useState(0)
  const [selectedRally, setSelectedRally] = useState(null)
  
  // Tastatursteuerung (Pfeiltasten für 100ms-Schritte)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        videoRef.current.currentTime = Math.max(0, currentTime - 0.1)
      } else if (e.key === 'ArrowRight') {
        videoRef.current.currentTime = currentTime + 0.1
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentTime])
  
  // Tischkalibrierung (4 Ecken anklicken)
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    if (tableCorners.length < 4) {
      setTableCorners([...tableCorners, [x, y]])
    }
    
    // Bei 4 Ecken: Kalibrierung an Backend senden
    if (tableCorners.length === 3) {
      saveTableCorners([...tableCorners, [x, y]])
    }
  }
  
  // Auto-Play Queue
  const playNextRally = () => {
    const currentIndex = rallies.findIndex(r => r.id === selectedRally?.id)
    if (currentIndex < rallies.length - 1) {
      const nextRally = rallies[currentIndex + 1]
      videoRef.current.currentTime = nextRally.start_time / 1000
      setSelectedRally(nextRally)
    }
  }
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Linke Spalte: Video-Player mit Kalibrierung */}
      <div className="col-span-2">
        <video 
          ref={videoRef}
          src={`/api/videos/${matchId}`}
          onTimeUpdate={e => setCurrentTime(e.target.currentTime)}
        />
        <canvas 
          onClick={handleCanvasClick}
          className="absolute inset-0"
        />
      </div>
      
      {/* Rechte Spalte: Rally-Timeline */}
      <div className="overflow-y-auto h-96">
        {rallies.map(rally => (
          <RallyItem 
            key={rally.id}
            rally={rally}
            isSelected={rally.id === selectedRally?.id}
            onSelect={() => {
              videoRef.current.currentTime = rally.start_time / 1000
              setSelectedRally(rally)
            }}
          />
        ))}
      </div>
    </div>
  )
}
```

**Zeilennummern:** 1-300 (gesamte Datei)

---

#### RallyTimeline Komponente

**Datei:** `frontend/components/RallyTimeline.tsx`

**Zweck:** Scrollbare Liste aller Rallies mit Validierungsstatus

```typescript
interface RallyTimelineProps {
  rallies: Rally[]
  selectedRallyId: string | null
  onSelectRally: (rally: Rally) => void
  onUpdateValidation: (rallyId: string, status: ValidationStatus) => void
}

export default function RallyTimeline({ 
  rallies, 
  selectedRallyId, 
  onSelectRally,
  onUpdateValidation 
}: RallyTimelineProps) {
  const [showOnlyHighlights, setShowOnlyHighlights] = useState(false)
  
  const filteredRallies = showOnlyHighlights 
    ? rallies.filter(r => r.validation_status === 'accepted')
    : rallies
  
  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000)
    const seconds = Math.floor((ms % 60000) / 1000)
    const milliseconds = ms % 1000
    return `${minutes}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`
  }
  
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold">Ballwechsel ({rallies.length})</h3>
        <label className="flex items-center gap-2">
          <input 
            type="checkbox"
            checked={showOnlyHighlights}
            onChange={e => setShowOnlyHighlights(e.target.checked)}
          />
          Nur Highlights
        </label>
      </div>
      
      <div className="space-y-2 overflow-y-auto h-96">
        {filteredRallies.map(rally => (
          <div 
            key={rally.id}
            className={`p-3 rounded cursor-pointer ${
              rally.id === selectedRallyId ? 'bg-blue-100' : 'hover:bg-gray-100'
            }`}
            onClick={() => onSelectRally(rally)}
          >
            <div className="flex justify-between">
              <span className="font-mono">{formatTime(rally.start_time)}</span>
              <ValidationIcon status={rally.validation_status} />
            </div>
            
            <div className="mt-1">
              <ConfidenceBar confidence={rally.confidence} />
            </div>
            
            <div className="mt-1 text-sm text-gray-600">
              {'🏓'.repeat(rally.impact_count)} ({rally.impact_count} Schläge)
            </div>
            
            <div className="mt-2 flex gap-2">
              <button 
                onClick={() => onUpdateValidation(rally.id, 'accepted')}
                className="text-green-600 hover:text-green-800"
              >
                ✓ Akzeptieren
              </button>
              <button 
                onClick={() => onUpdateValidation(rally.id, 'rejected')}
                className="text-red-600 hover:text-red-800"
              >
                ✗ Ablehnen
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Zeilennummern:** 1-150 (gesamte Datei)

---

## Nächste Schritte

### Sofort (heute)

1. **GitHub Repository erstellen**
   - User entscheidet: GitHub Desktop vs. CLI
   - Initiales Commit: `git add .`, `git commit -m "Initial commit: TTLab V0.3"`
   - Remote hinzufügen und pushen

2. **V0.4 Planning finalisieren**
   - Labeling-Tool spezifizieren (welche Annotationen?)
   - Datensatz-Strategie (eigene Videos vs. öffentliche Datensätze?)
   - Modell-Auswahl (YOLOv8n vs. RT-DETR)

### Diese Woche

1. **Labeling-Tool entwickeln**
   - Einfaches React-Tool: Video frame-by-frame durchgehen
   -Bounding Box um Ball zeichnen (x, y, width, height)
   - Export als YOLO-Format (txt-Dateien mit normalisierten Koordinaten)
   - Ziel: 500-1000 annotierte Frames

2. **Datensatz sammeln**
   - Eigene Trainingsvideos durchgehen
   - Verschiedene Bedingungen abdecken:
     - Gute/schlechte Beleuchtung
     - Verschiedene Kamerawinkel
     - Weiße/orange Bälle
     - Unterschiedliche Ballgrößen (nah/fern)

### Nächste 2 Wochen

1. **Modell trainieren**
   - YOLOv8n Architecture wählen (klein, schnell für Echtzeit)
   - Auf GTX 1050 trainieren (2 GB VRAM Limit beachten)
   - Hyperparameter-Tuning (learning rate, batch size, epochs)
   - Expected: 50-100 Epochs, ~2-4 Stunden Training

2. **Integration in Backend**
   - ONNX-Export des trainierten Modells
   - ONNX Runtime im Backend einbinden
   - RallyDetector um `_detect_ball_ml()` erweitern
   - Fallback auf alte Methode bei ML-Fehlern

3. **Evaluation**
   - Test-Videos mit Ground Truth vergleichen
   - Precision, Recall, F1-Score berechnen
   - False Positives analysieren (wo scheitert das Modell?)
   - Iteratives Verbessern (mehr Daten für Problemfälle)

### Q4 2026 (Oktober - Dezember)

1. **Shot-Klassifikation**
   - Datensatz für Vorhand/Rückhand/Topspin/Slice sammeln
   - CNN-LSTM Hybrid-Modell trainieren
   - In Rally-Erkennung integrieren

2. **Taktik-Analyse**
   - Heatmap-Visualisierung implementieren
   - Pattern-Mining (welche Ballfolgen führen zu Punkten?)
   - Gegner-Schwachstellen identifizieren

3. **PostgreSQL Migration**
   - Alembic für Migrations-Management
   - SQLite → PostgreSQL Data-Migration
   - Connection Pooling für bessere Performance

---

## Anhang: Häufige Fehler & Lösungen

### Error: "Database is locked"

**Ursache:** SQLite erlaubt nur einen Writer gleichzeitig

**Lösung:**

```python
# In database.py: Connection mit busy_timeout konfigurieren
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)
```

**Langfristig:** PostgreSQL wechseln

---

### Error: "FFmpeg not found"

**Ursache:** FFmpeg nicht im PATH

**Lösung Windows:**

```powershell
# chocolatey
choco install ffmpeg

# Oder manuell:
# 1. https://ffmpeg.org/download.html
# 2. ZIP nach C:\ffmpeg entpacken
# 3. C:\ffmpeg\bin zu PATH hinzufügen
# 4. Terminal neu starten
```

**Lösung Linux:**

```bash
sudo apt update && sudo apt install ffmpeg
```

---

### Error: "ModuleNotFoundError: No module named 'cv2'"

**Ursache:** OpenCV nicht installiert

**Lösung:**

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install opencv-python
```

---

### Error: "Next.js Build failed: ENOSPC"

**Ursache:** Zu wenig Speicherplatz für Watcher

**Lösung Linux:**

```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Lösung Windows:**

- Terminal als Administrator starten
- Node.js Cache leeren: `npm cache clean --force`

---

### Error: "Video upload timeout"

**Ursache:** Große Videos (>500 MB) überschreiten Timeout

**Lösung:**

```python
# In main.py: Upload-Size-Limit erhöhen
app = FastAPI()
app.config.max_upload_size = 2 * 1024 * 1024 * 1024  # 2 GB
```

**Frontend:** Chunked Upload implementieren (in Planung)

---

## Glossar

| Begriff | Definition |
|---------|------------|
| **Rally** | Ein Ballwechsel (vom Aufschlag bis Punktende) |
| **Impact** | Ein Ball-Schläger-Kontakt (innerhalb eines Rallies) |
| **Confidence** | Erkennungssicherheit (0.0 = unsicher, 1.0 = sehr sicher) |
| **Table Corners** | 4 Eckpunkte des Tisches im Videokoordinatensystem |
| **MOG2** | Mixture of Gaussians, Algorithmus für Hintergrund-Subtraktion |
| **RMS-Energie** | Root Mean Square, Maß für Audio-Lautstärke |
| **Bounding Box** | Rechteck um erkanntes Objekt (x, y, width, height) |
| **ONNX** | Open Neural Network Exchange, Format für ML-Modelle |
| **YOLO** | You Only Look Once, Objektdetektions-Architektur |
| **RT-DETR** | Real-Time DEtection TRansformer, Alternative zu YOLO |

---

## Kontakt & Support

Bei Fragen oder Problemen:

- **Dokumentation:** `/docs` Endpoint (Swagger UI)
- **Issues:** GitHub Repository (sobald erstellt)
- **Logs:** Backend-Console für Debug-Informationen

---

**Letztes Update:** 17. August 2026  
**Autor:** TTLab Development Team  
**Lizenz:** Proprietär (alle Rechte vorbehalten)
