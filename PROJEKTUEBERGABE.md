# TTLab - Projektübergabe & Entwicklungsstand

**Version:** V0.5 (Performance- & Highlight-Optimierung)  
**Datum:** 5. September 2026  
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

### V0.3 (Tischkalibrierung & Validierung - abgeschlossen)

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

### V0.4 (Video-Export - abgeschlossen)

**Neue Funktionen:**

- ✅ Dual-Mode Video-Export (Fast Mode ~2s / Compatible Mode ~60s)
- ✅ Windows Media Player Kompatibilität garantiert
- ✅ Automatischer Fallback bei Inkompatibilität
- ✅ H.264 Main Profile + AAC Encoding
- ✅ yuv420p Pixel-Format für maximale Kompatibilität

**API-Endpunkte erweitert:**

- `GET /api/matches/{id}/export-highlights-video?fast=true` - Schneller Modus
- `GET /api/matches/{id}/export-all-rallies-video?fast=true` - Schneller Modus

---

### V0.5 (Performance- & Highlight-Optimierung - abgeschlossen)

**Performance (Analyse stark beschleunigt, Erkennungsqualität unverändert):**

- ✅ Zwei Analyse-Modi per Button: **⚡ Volle Leistung** (alle Kerne minus 1; bit-identisch zur ursprünglichen Erkennung – per Test verifiziert) und **🌙 Hintergrund** (~halbe Kerne, `frame_step=2`, Downscale auf 960px Breite)
- ✅ Segment-parallele Motion-Dekodierung: jeder Worker erhält eigene `VideoCapture`, `CAP_PROP_POS_FRAMES`-Seek, Chunk-Grenzen auf dem Frame-Step-Raster (Ergebnisse im Performance-Modus bit-identisch)
- ✅ Ball-Validierung parallel über alle Kandidaten-Gruppen (Queue + Threads, persistente `VideoCapture` pro Worker, Live-Fortschritt „Ballwechsel X/Y geprüft")
- ✅ 1-Seek-Optimierung beim Ball-Lesen (`ball_seek_mode="single"`): statt 3 Seeks nur noch 1 – identische Treffer, ~2,8× schneller (Fallback `"triple"` verfügbar)
- ✅ Audio-Extraktion überlappt mit der Motion-Phase
- ✅ Parallele Clip-Extraktion (ThreadPoolExecutor + mehrere FFmpeg-Prozesse)
- ✅ Worker-Zahl dynamisch über `os.cpu_count()` – nichts hardcoded, funktioniert auf jedem PC
- ✅ Fortschrittsanzeige beginnt bei 2 % statt 10 %, Phasen-Timing-Logs in der Backend-Konsole

**Rally-Erkennung (Qualität):**

- ✅ Bounce-Decay-Filter (`_strip_bounce_tail`): Erkennt Phasen, in denen nach dem Ballwechsel der Ball auf den Tisch geworfen oder aufgehoben wird → Clips enden rechtzeitig, Fehl-Rallys werden verworfen (Parameter: `bounce_height_decay=0.95`, `bounce_interval_decay=0.85`, `bounce_entry_ratio=0.9`)

**Highlight-Erkennung (neu kalibriert):**

- ✅ `classify_highlight()`: Rally ist Highlight wenn **Dauer ≥ 10s ODER Impact-Sounds ≥ 24 ODER Score ≥ 0.9 × Match-Maximum** (kalibriert auf ~10–17 % der Rallys pro Match; 24 Sounds ≈ 12 echte Ballkontakte)
- ✅ Automatische Highlights im Frontend sichtbar: Badge ⭐, Highlight-Filter, gelber Hintergrund, H-Shortcut, Toggle-Button; manuelle Markierungen (`user_marked_highlight`) haben Vorrang und bleiben erhalten
- ✅ `POST /api/matches/{id}/reevaluate-highlights` + Button **„🔄 Neu bewerten"**: wendet aktuelle Regeln auf bestehende Matches an, ohne neue Video-Analyse
- ✅ **Export-Fix:** Video-Export und Clip-Download filtern jetzt auf `is_highlight OR user_marked_highlight` – exakt wie die Frontend-Anzeige (`isMarked`). Zuvor fehlten automatisch erkannte Highlights (Filter nur `user_marked_highlight`) bzw. nach „Neu bewerten" manuell markierte (Filter nur `is_highlight`). „Neu bewerten" entfernt manuelle Markierungen nie mehr aus dem Highlight-Status

**Windows-Media-Player-Kompatibilität (0x80004005-Fix):**

- ✅ Ursache gefunden: iPhone-Videos sind **HEVC Main 10 (10-bit)**; die Clip-Extraktion (libx264 ohne `pix_fmt`) erzeugte daraus **H.264 High 10 (Hi10P)** – ein Profil, das der Windows Media Player nicht decodieren kann („Es wurden nicht unterstützte Codierungseinstellungen verwendet", 0x80004005). Der Fast-Export (`-c copy`) kopiert dieses Profil 1:1; nur der Compatible-Modus (`yuv420p`) funktionierte
- ✅ Clip-Extraktion schreibt jetzt `pix_fmt=yuv420p` + `movflags +faststart` – alle neuen Clips sind 8-bit H.264 High und damit WMP-kompatibel
- ✅ Einmal-Migration `backend/reencode_clips.py`: re-encodiert bestehende 10-bit-Clips in-place (Video CRF 18, Audio-Copy) und löscht veraltete Export-Dateien – bereits über alle 406 betroffenen Clips gelaufen, keine Neu-Analyse nötig

**UX:**

- ✅ Tastatur-Shortcuts (Space Play/Pause, ←/→ 100ms, ↑/↓ Rally, H Highlight, R/N/L Validierung, 1-4 Filter, Strg+←/→ Video-Position) mit ShortcutsModal (Button in der Kopfzeile)
- ✅ Video-Player: Geschwindigkeit 0.25–1.5x, Loop-Funktion, Vor-/Zurück-Navigation zwischen Rallys, Auto-Scroll zum Video
- ✅ Analyse-Ansicht aktualisiert sekündlich (vorher 3s-Polling); „Erkannte Rallys / Highlights"-Kacheln während der Analyse entfernt
- ✅ Notizen werden live mit Debounce (600ms) gespeichert, Rally-Nummerierung pro Match, übersetzte Tooltips auf allen Buttons

**Stabilität & Code-Qualität:**

- ✅ Background-Analyse-Fix: Fortschritts-Updates funktionieren wieder (ursprünglich `asyncio.run()` im Thread kaputt → jetzt `asyncio.to_thread` + `run_coroutine_threadsafe`)
- ✅ Streaming-Upload (1MB-Chunks), `lifespan` statt `on_event`, `async_sessionmaker`, `eval()` durch sicheres `_parse_frame_rate()` ersetzt
- ✅ Frontend: geteilte Typen (`lib/types.ts`) und API-Helper (`lib/api.ts`), React-Refs statt `querySelector`, `useMemo` für Rally-Nummern, 32 unbenutzte Translation-Keys entfernt
- ✅ Export-/Download-Endpunkte refaktoriert (gemeinsame Helper), Bulk-Delete, `request.base_url` statt hardcoded localhost
- ✅ SQLite-DB unter `data/db/ttlab.db` (Clips in `data/clips/`, Originale in `data/videos/`)

---

### V0.6 (In Entwicklung - Ball-Tracking-Modell YOLOv8n)

**Status: Phase 1 abgeschlossen, Phase 2 (ML-Integration) umgesetzt & verifiziert – Tests eingecheckt (Stand 27.09.2026)**

**Status Labeling (User): 618 Frames gelabelt** (517 mit Ball, 101 Negativ-Frames, Datensatz `v1-ml-training`, bereits exportiert) – Ziel ~600 erreicht. Training auf dem Desktop-PC steht aus.

**Phase 2 – ML-Integration + Rotations-Fix (20.09.2026, umgesetzt & verifiziert):**

- **Neu `app/ball_detector.py`:** `HeuristicBallDetector` (Logik 1:1 aus `RallyDetector._is_ball_candidate` übernommen; `RallyDetector._is_ball_candidate` ist jetzt dünner Delegat – alte Variante bleibt als Fallback dauerhaft erhalten) + `MLBallDetector` (onnxruntime, NUR CPU, thread-safe geteilte Session, Ultralytics-Letterbox-Preprocessing exakt nachgebildet, YOLOv8-Output-Interpretation `(B, 5, N)` mit Fallback `(B, N, 5)`, Confidence-Schwelle 0.30, Detection zählt wenn Zentrum im Tisch-Polygon). Factory `create_ball_detector()`: Modell in `data/models/*.onnx` (neuestes) → ML, sonst Heuristik; erzwingbar per `TTLAB_BALL_DETECTION=auto|ml|heuristic`; kaputtes Modell → Warnung + Heuristik (Analyse bricht nie ab).
- **Rotations-Fix in der Analyse-Pipeline:** `extract_motion_features` und `_ball_scanner` lesen Frames jetzt in **Anzeige-Orientierung** (`video_processor.get_display_rotation/rotate_frame`, gemeinsam mit Labeling-Tool). Zuvor: Tisch-Maske lag bei 180°-iPhone-Videos um 180° versetzt (Tischmarkierung im Browser = rotiertes Koordinatensystem, Pipeline las rohe Frames). Beweis: 12/12 gelabelte Ball-Boxen passten nur auf rotierte Frames (4/12 auf rohe). Für 90°/270°-Videos werden die Mask-Masse getauscht; `rotate_frame()` ist bei 0° ein No-Op ohne Kopie.
- **DB:** `rallies.model_version` (`heuristic_v0.5` bzw. ONNX-Dateiname) + Migration; `RallyResponse`-Schema erweitert; `main.py` schreibt die Version beim Speichern.
- **`onnxruntime==1.20.1`** in requirements.txt (kein torch im Backend!).
- **Verifikation (Skripte in `%TEMP%\opencode\phase2-verify\`):** Bit-Identität am unrotierten MP4 **bestanden** (Motion 9015 Werte exakt gleich, Ball-Hits identisch `[2,3,3,3,1,3,0,1]`) – der Refactor verändert V0.5-Ergebnisse unrotierter Videos garantiert nicht. Fallback-Tests bestanden (auto/heuristic/kaputtes Modell). Rotations-Fix gemessen: Ball-Hits bei Match 2 von Summe 21 → 12 – siehe offene Frage unten.

**⚠️ OFFENE FRAGE (nächste Sitzung klären): Tisch-Maske = Tischplatte oder Spielzone?**
Die korrekt platzierte Maske (Tischplatten-Polygon) erfasst den Ball nur bei Abpunkten – der Ball FLIEGT während Ballwechseln überwiegend im Luftraum ÜBER der Platte (ausserhalb des Polygons). Die vormals versehentlich gespiegelte Maske deckte zufällig diesen Luftraum ab (deshalb vorher MEHR Hits). Betroffen: Heuristik UND ML-Detector (ML prüft ebenfalls `Detection im Polygon`). **Empfohlene Entscheidung:** Masken-Semantik auf „Spielzone" erweitern (Polygon nach oben um ~1 Tischhöhe erweitern, konfigurierbar) und gegen die User-Ground-Truth validieren (Match 2 hat 118 manuell validierte Rallys in der DB: accepted/rejected). Dafür `rallies_from_audio_peaks`-Filter `ball_hits < 2 → Rally verwerfen` im Blick behalten. Bit-Identität gilt weiterhin NUR für unrotierte Videos mit unveränderter Masken-Semantik.

**Implementiert (27.09.2026, Schritt 2 der Masken-Entscheidung):** `rally_detection.play_zone_polygon()` erweitert das Ball-Validierungs-Polygon als konvexe Hülle mit einer um Faktor × Tischhöhe nach oben verschobenen Kopie (folgt der Tisch-Perspektive, keine seitliche Verbreiterung). Konfiguration per `TTLAB_PLAY_ZONE` (0.0–3.0, Default **0.0** = bit-identisches V0.5-Verhalten; am echten Video verifiziert: Ball-Hits Match 5 exakt gleich). NUR die Ball-Maske ist erweiterbar – die Motion-Maske bleibt auf der Platte (Motion-False-Positives kommen von laufenden Personen). Unit-Tests: `backend/tests/test_play_zone.py` (Identität bei 0, Luftraum bei >0, Perspektive, Klemmung). Beispiel `TTLAB_PLAY_ZONE=1.0`: Ball-Hits Match 5 Summe 16 → 33.

**Rally-Gate gegen Wurf-/Hüpf-Clips (04.10.2026, implementiert & verifiziert):** Problem des Users: (a) nach dem Ballwechsel laufende Rallys beim Rüberwerfen des Balls, (b) Aufschlag-Vorbereitungs-Hüpfen zählt als Rally. User-Vorgaben: **Rally-Enden NIEMALS abschneiden, Rally-Anfänge NIEMALS verändern** – Lösung flaggt daher ganze Gruppen, fasst Grenzen nie an. Vorgehen: Feature-Analyse an frischer User-Ground-Truth (**Match 7 = `Training_Theodor.mov`, komplett validiert am 04.10.2026: 72 acc/28 rej**; Match 4 = alter August-Stand, nicht als GT genutzt) in 3 Stufen: (1) Audio-Peak-Features trennen zu schwach (bestes Gate 31/72 bei 17/255 Kollateral), (2) **ML-Ballpositionen** pro Peak (neu: `is_ball_candidate_pos` in ball_detector.py, `provides_positions`-Capability; `_validate_ball_hits(collect_positions=True)` sammelt normalisierte Ballzentren, Standard-Pfad bit-identisch), (3) Gruppen-Level-Sweep (Rohdaten: 337 Gruppen, 169 acc/49 rej mit GT). **Finale Regel (`rally_gate_flag`): A) ≥3 Positionen + lokale Ball-Spannweite (x_range < 0.12) + Ball bei ≥40 % der Peaks, ODER B) 0 Ballpositionen in kurzer Gruppe (<10 Peaks).** Gruppenebene: fängt 24/49 Müll-Gruppen, 9/169 Kollateral; **auf Rally-Ebene (nach bestehendem `ball_hits≥2`-Filter): 6/49 geflaggt bei 3/169 Kollateral (1,8 %)** – e2e verifiziert via Replay (Match 2: 1/21 geflaggt, 2/97 kollateral; Match 7: 5/28, 1/72). Modus per `TTLAB_RALLY_GATE` = `review` (Default: geflaggte Rallys landen als ⚠ review statt auto-accept – nichts geht verloren, User entscheidet) / `reject` / `off`. Grenzen: Rübergeworfene Bälle mit breitem Ballflug über den Tisch entgehen Regel A (sieht positionell wie eine Rally aus); Heuristik-Detektor hat keine Positionen → Gate dort inaktiv (Bit-Identität per `verify_playzone_identity.py` PASS, 68/68 pytest). Hebel für die nächste Iteration: Ball-Geschwindigkeit/Richtung zwischen Frames, Cadence-Analyse, mehr gelabelte Frames.

**✅ ENTSCHIEDEN (27.09.2026, Schritt 3 – Ground-Truth-Messung): Tischplatte (Faktor 0.0) bleibt Default.**
Messung (Skript + Ergebnisse: `backend/tests/phase2_verification/playzone_measurement.py` / `playzone_results.json`; 1× Motion+Audio, dann pro Faktor Ball-Validierung + Rally-Zusammenbau; Match-Regel: Zeit-Überlappung ≥ 20 % des kürzeren Fensters gegen die User-Ground-Truth):

| Faktor | Match 2 (97 acc/21 rej): Precision / Recall / F1 | Match 5 (16 acc/4 rej): F1 | Match 2: erkannte abgelehnte Rallys |
|--------|--------------------------------------------------|---------------------------|--------------------------------------|
| **0.0 Platte** | **0.752 / 0.907 / 0.822** | **0.788** | 17 von 21 vermieden |
| 0.5 | 0.664 / 1.0 / 0.798 | 0.727 | 0 (alle 21 fälschlich erkannt) |
| 1.0 | 0.660 / 1.0 / 0.795 | 0.711 | 0 |
| 1.5 | 0.655 / 1.0 / 0.792 | 0.711 | 0 |

**Interpretation:** Die Spielzone findet zwar alle echten Ballwechsel (Recall 1.0), aber die Precision bricht ein – der Ball-Validierungs-Filter verliert seine diskriminierende Kraft: Genau die Fehl-Rallys (Ball aufheben/werfen, „hier ist dein Ball") werden mit Luftraum-Maske ebenfalls validiert, weil ihr Ball durch die Luft fliegt, ohne auf der Platte abzuprallen. Die Platten-Maske ist der bessere Rally-Diskriminator. Der frühere „Treffer-Verlust" (21 → 12 Ball-Hits bei Match 2) war keine Verschlechterung, sondern Präzisionsgewinn. `TTLAB_PLAY_ZONE` bleibt implementiert (0.0–3.0) für den ML-Realtest: **Hypothese für die nächste Sitzung** – mit trainiertem Modell könnte die Zone sinnvoll sein, weil der ML-Detektor den Ball zuverlässig vom weißen T-Shirt/Reflexionen unterscheidet und die Zone dann Recall bringt, ohne die Präzision zu verlieren. Das ist beim Realtest mit `TTLAB_PLAY_ZONE=0.5/1.0` gegen dieselbe Ground-Truth zu messen.

**✅ ML-REALTEST ABSCHLOSSEN (04.10.2026): Modell trainiert, integriert, gemessen.** Der User hat YOLOv8n auf 618 Frames trainiert (GTX 1050, `torch==2.5.1+cu118` – neuere Builds unterstützen sm_61/Pascal nicht mehr; Setup-Fixes in `backend/ml/README.md` commit `7dc919b`): **mAP50 0.804, Precision 0.917, Recall 0.753** (100 Epochen, 0.72 h). ONNX liegt in `data/models/ball_yolov8n.onnx` → `TTLAB_BALL_DETECTION=auto` nutzt ML ab jetzt automatisch (Heuristik bleibt Fallback ohne Modell). Evaluation mit `backend/ml/evaluate.py` (commit `44fa60a`) gegen dieselbe Ground-Truth, Rohdaten in `tests/phase2_verification/ml_realtest_results.json`:

| Variante | Match 2: P / R / F1 | Match 5: F1 | Match 2: FP auf abgelehnten Rallys |
|---|---|---|---|
| Heuristik, Platte | 0.752 / 0.907 / 0.822 | 0.788 | 17 |
| Heuristik, Zone 0.5 | 0.664 / 1.0 / 0.798 | 0.727 | 21 |
| **ML, Platte** | **0.839** / 0.804 / 0.821 | 0.759 | **4** |
| ML, Zone 0.5 | 0.744 / 0.928 / 0.826 | 0.743 | 12 |
| ML, Zone 1.0 | 0.746 / 0.938 / **0.831** | 0.778 | 12 |

**Fazit:** (1) **ML + Platte: Precision-Sprung** (+0.09, FP auf abgelehnten Rallys 17 → 4) bei gleichem F1 – klar besseres Production-Default als die Heuristik. (2) **Die dokumentierte Hypothese ist bestätigt:** ML + Spielzone hält die Precision (0.744–0.746 vs. Heuristik-Einbruch auf 0.66) und erzielt das beste F1 überhaupt (Zone 1.0: 0.831) – der ML-Detektor erkennt den Ball im Luftraum zuverlässig. (3) Abstand ML-Platte ↔ ML-Zone ist aber klein (0.821 vs. 0.831) und der kleine Kontroll-Match 5 favorisiert weiterhin die Platte (0.788). **Entscheidung: Default bleibt `TTLAB_PLAY_ZONE=0.0` + ML (auto)** – beste Precision, bit-identische Semantik. Die Zone bleibt als Experiment per Env-Variable verfügbar. ML-Ball-Validierung ist ~2× langsamer als die Heuristik (ONNX auf CPU, ~6 min statt ~3 min pro Ball-Pass bei Match 2) – vertretbar. **Hinweis:** Match 2 NICHT per UI neu analysieren (würde die 118 validierten Rallys zurücksetzen) – die Evaluation läuft über `evaluate.py` ohne DB-Änderung. **Nächste Verbesserungshebel:** Recall des Modells (0.753 auf Val) – mehr/ diverse Frames labeln (v.a. schnelle Bälle, schlechtes Licht), 2. Modell-Generation; danach Shot-Klassifikation (V0.7).

**Phase 2 – noch offen:**
- Masken-Semantik-Entscheidung (siehe oben) + Validierung gegen User-Ground-Truth
- Echte ML-Verifikation: sobald `data/models/ball_yolov8n.onnx` vom Training existiert, komplette Analyse mit ML durchlaufen lassen und mit Heuristik + Ground-Truth vergleichen
- Evaluationsskript `backend/ml/evaluate.py` (Precision/Recall Heuristik vs. ML, ursprünglich Phase 3)

**Geplante Inhalte (zuvor V0.4.1):**

- [x] Integriertes Labeling-Tool (Frontend-Route `/labeling`, server-seitige Frame-Extraktion – der Browser kann HEVC Main 10 nicht dekodieren)
- [x] Trainings-Export (YOLO-Layout mit deterministischem 80/20 train/val-Split + portabler `data.yaml` mit relativem Pfad) inkl. **ZIP-Download** (`GET /api/labeling/datasets/{ds}/download`) – nach dem Export wird der Download automatisch gestartet, Button für erneuten Download vorhanden
- [x] Trainings-Skripte für den GTX-1050-Desktop (`backend/ml/train_yolo.py`, `export_onnx.py`, Anleitung `backend/ml/README.md`)
- [ ] Datensatz sammeln: 500–1000 Frames manuell annotieren (User-Aufgabe, ~1–1,5h)
- [ ] Modell trainieren (User-Aufgabe auf dem Linux-Mint-Desktop, ~2–4h)
- [ ] Integration in die Rally-Erkennung: `MLBallDetector` via ONNX Runtime (kein torch im Backend!), alte Heuristik bleibt als Fallback vollständig erhalten
- [ ] Evaluation: Precision/Recall gegen bestehende accepted/rejected-Rallys als Ground-Truth

**Phase 1 – Labeling-Tool (fertig):**

- **Backend `app/labeling.py`:** persistente `VideoCapture` pro Video (thread-sicher), Frame-Navigation **frame-index-basiert** (POS_MSEC-Seek hat Rundungsprobleme), JPEG-Anzeige-Frames auf 1280px verkleinert + LRU-Cache, Trainingsbilder in **voller Auflösung** gespeichert. **Rotations-Fix:** iPhone-Videos speichern die Orientierung als Display-Matrix (`side_data rotation: -180`); Browser wenden sie an, OpenCV ignoriert sie – alle Frames werden jetzt per `get_display_rotation()` (ffprobe, gecached) in die Anzeige-Orientierung gedreht (verifiziert gegen FFmpeg-Autorotate-Referenz). Preview UND Trainingsbild drehen konsistent, normalisierte BBox-Koordinaten passen dadurch immer. **Wichtig für Phase 2:** Auch die ML-Inferenz muss Frames über dieselbe rotationierte Extraktion lesen. Bounding-Boxes als normalisierte YOLO-Koordinaten `[cx, cy, w, h]` – unabhängig von der Anzeige-Auflösung. **Multi-Box:** Ein Frame kann mehrere Bälle enthalten (z.B. Bälle auf dem Boden) – eine Box pro Ball, eine Zeile pro Ball in der Label-Datei (Standard-YOLO-Multi-Objekt-Format); Alt-Annotationen (Einzel-`bbox` aus der ersten Phase) werden beim Lesen automatisch migriert. Frames ohne Ball werden als **Negativ-Samples** (leere Label-Datei) gespeichert – ultralytics nutzt sie als Hintergrund-Bilder, das ist die wichtigste Waffe gegen False Positives. `annotations.json` ist die Quelle der UI, Label-Dateien werden deterministisch daraus erzeugt. Atomares Schreiben (`.tmp` + `os.replace`), BOM-tolerantes Lesen.
- **Datensatz-Struktur:** `data/datasets/<name>/raw/{images,labels}/` + `annotations.json`; Export erstellt `yolo/{images,labels}/{train,val}/` + `data.yaml` (Hardlinks statt Kopien – kein doppelter Speicherplatz, deterministischer Split per Seed).
- **API-Endpunkte (alle verifiziert):** `GET /api/matches/{id}/video-info`, `GET /api/matches/{id}/frame?frame=N` (JPEG mit `Cache-Control: immutable`), `GET/POST /api/labeling/datasets`, `GET/POST /api/labeling/datasets/{ds}/annotations`, `DELETE /api/labeling/datasets/{ds}/annotations/{match_id}/{frame}`, `POST /api/labeling/datasets/{ds}/export`. Validierung: Datensatz-Namen `[a-z0-9_-]` (Path-Traversal-Schutz), BBox-Felder 0..1 + innerhalb des Bildes, Frame-Index im Video.
- **Frontend:** Route `/labeling` (Datensatz wählen/erstellen → Video wählen → Workbench `FrameLabeler.tsx`), BBox per Maus-Ziehen, **mehrere Boxen pro Frame** (jede Box einzeln per ×-Button entfernbar, „Alle löschen"-Button), Auto-Speichern mit kurzer Verzögerung nach der **letzten** gezeichneten Box (unterbrechbar durch weitere Boxen – Hinweis „Speichert automatisch…" wird angezeigt), „Kein Ball"-Markierung (N), vorhandene Annotationen werden beim Navigieren angezeigt (überschreibbar/löschbar), Frame-Vorladen des nächsten Bildes, Shortcuts (←/→ Frame, Shift+←/→ 1s, N kein Ball, ⏎ speichern), DE/EN-übersetzt, Nav-Link „Labeling" in der Kopfzeile.

**Kritischer CSS-Fix (20.09.2026):** `postcss.config.mjs` nutzte `@tailwindcss/postcss` – das **Tailwind-v4-Plugin** – während `globals.css` v3-Direktiven (`@tailwind base/components/utilities`) und `tailwind.config.ts` die v3-Config enthält. Das v4-Plugin emittiert bei v3-Direktiven **kein Theme**: Alle Theme-abhängigen Utilities (Spacing `p-*`, Farben `bg-*`/`text-*`/`border-*`, `rounded-*`, `inset-0`, Schriftgrößen) fehlten im kompilierten CSS – nur 107 statt 332 Regeln. Folge: Der Zeichen-Overlay im Labeling-Tool hatte Größe 0×0 (kein `inset-0`), das Zeichnen war unmöglich. **Fix:** postcss.config zurück auf das v3-Plugin (`tailwindcss: {}`, dem die Config + Direktiven entsprechen), `@tailwindcss/postcss` deinstalliert. Verifiziert per isoliertem PostCSS-Test beider Varianten, CSS-Audit im echten Browser (v3: 332 Regeln, alle Utilities) und vollständigem E2E-Browser-Test des Zeichen-Workflows (Headless Edge via puppeteer-core): Overlay-Größe, Zieh-Vorschau, Box-Erstellung, Auto-Save, Backend-Persistenz, „gelabelt"-Badge – alles grün. Zusätzlich `data-testid`-Anker im Workbench für wiederverwendbare UI-Tests.
- **Trainings-Vorbereitung:** `train_yolo.py` (YOLOv8n, auf 2 GB VRAM ausgelegt: batch=8, imgsz=640, AMP; OOM-Fallbacks dokumentiert), `export_onnx.py` (ONNX opset 12, dynamic batch) → Ziel: `data/models/ball_yolov8n.onnx`. Vollständige Schritt-für-Schritt-Anleitung in `backend/ml/README.md` (Linux Mint, CUDA-Check, Fehlerbehebung). **Datensatz-Transfer:** Export lädt automatisch eine ZIP herunter (`GET /api/labeling/datasets/{ds}/download`), `data.yaml` mit relativem Pfad (portabel auf jedem Rechner).
- **Scroll-Stabilität (UX):** Frame-Container im Labeling-Tool reserviert das Video-Seitenverhältnis per `aspectRatio` (kein Layout-Kollaps beim Laden), das Frame-`<img>` wird nicht mehr per `key` neu gemountet, sondern nur die `src` getauscht (altes Bild bleibt sichtbar, bis das neue dekodiert ist) – die Scroll-Position bleibt beim ±Sekunden-Springen exakt erhalten. Clip-Player in MatchDetail ebenfalls mit reserviertem `aspect-video`. Per E2E-Browser-Test verifiziert (Scroll-Position nach 4 Sprüngen identisch).
- **Frame-Lade-Watchdog (Bugfix):** Schnelles ±Springen konnte das `<img>` in einen kaputten Browser-Zustand versetzen (`complete=true`, `naturalWidth=0`, kein weiteres Load-Event → Frame bleibt schwarz, bis man erneut springt). Ein Watchdog prüft 500/1200/2500 ms nach jedem Frame-Wechsel diesen Zustand und stößt den Ladevorgang per Neu-Zuweisung der `src` an (aus dem Cache, sofort sichtbar); abgebrochene Loads feuern Error-Events, die bis zu 3× still wiederholt werden, bevor eine Fehlermeldung erscheint. E2E-verifiziert: 3 Rapid-Szenarien (6× +1s, 10× Frame▶, gemischt vor/zurück) laden danach zuverlässig.
- **„Letzter gelabelter Frame"-Button:** Springt zum zuletzt gelabelten Frame des aktuellen Videos (nach `labeled_at` sortiert) – zum Weitermachen nach einer Pause; gespeicherte Box + „gelabelt"-Status werden dort angezeigt. E2E-verifiziert.

**Meilensteine (Rest):**

1. Datensatz zusammenstellen (verschiedene Beleuchtungen, Winkel, weiße/orange Bälle)
2. Modell trainieren (YOLOv8n auf GTX 1050)
3. Integration in Rally-Erkennung (Ball-Tracking als zusätzlicher Input, Fallback auf Heuristik)
4. Evaluation (Precision/Recall auf Test-Videos)

**Erwartete Verbesserungen:**

- False Positive Rate: ~40% → ~10%
- Confidence-Score genauer durch Ball-Präsenz
- Serve-Erkennung (Ballwurf → erster Kontakt)

---

### V0.7 (Geplant - Shot-Klassifikation)

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

### V0.8 (Geplant - Taktik-Analyse)

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

### Abgeschlossene Tasks (V0.1 - V0.5)

#### Backend

- [x] FastAPI-App mit allen API-Endpunkten
- [x] SQLAlchemy-Modelle (Match, Rally)
- [x] Async-Datenbankverbindungen
- [x] Migration-Logik für Legacy-Daten
- [x] RallyDetector-Klasse (Motion + Audio + Ball)
- [x] VideoProcessor (FFmpeg Wrapper)
- [x] Background-Job für Videoanalyse
- [x] Status-Tracking (pending → processing → completed/failed)
- [x] Error-Handling mit sinnvollen Fehlermeldungen
- [x] Dual-Mode Video-Export (Fast/Compatible)
- [x] **Zwei Analyse-Modi (performance/background) mit paralleler Pipeline**
- [x] **Bounce-Decay-Filter gegen zu lange Clips & Fehl-Rallys**
- [x] **Highlight-Klassifizierung + Reevaluate-Endpoint**
- [x] **Streaming-Upload (1MB-Chunks), Bulk-Delete, Export-/Download-Refactoring**

#### Frontend

- [x] Dashboard mit Match-Übersicht
- [x] MatchDetail-Komponente mit Video-Player
- [x] Tischkalibrierung UI (Canvas mit 4 Klick-Punkten)
- [x] Rally-Timeline mit Scroll-Container
- [x] Highlight-Filter Toggle
- [x] Auto-Play Queue
- [x] 100ms-Schritt Navigation (Pfeiltasten)
- [x] Result-Filter (Siege/Niederlagen/Unentschieden/Alle)
- [x] Statistik-Cards (Gesamtübersicht)
- [x] Delete-Button für Matches
- [x] Export-Funktion (Highlights concat)
- [x] **Tastatur-Shortcuts + ShortcutsModal**
- [x] **Video-Player: Geschwindigkeit, Loop, Rally-Navigation**
- [x] **Automatische Highlights (Badge/Filter/Shortcut) + „Neu bewerten"-Button**
- [x] **1s-Live-Polling während der Analyse, Notizen-Debounce, übersetzte Tooltips**
- [x] **Geteilte Typen & API-Helper (lib/types.ts, lib/api.ts), DE/EN-Übersetzungen vollständig**

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
- **Neu (V0.5):** Bounce-Decay-Filter verwirft Rallys, die nur aus Ball-aufheben/auf-Tisch-werfen bestehen, und schneidet solche Enden ab

**Restprobleme:**

- False Positive Rate deutlich gesunken (Bounce-Filter), aber immer noch vorhanden
- Einfache Helligkeitsfilterung (180-255 RGB) zu ungenau
- Kleine/schnelle Bälle werden übersehen

**Nächster Schritt (V0.6):** Trainiertes Ball-Tracking-Modell entwickeln

---

#### GitHub-Repository Setup

**Status:** Repository existiert (https://github.com/EtwasJonas/TTLab) – **V0.5 ist committet und gepusht** (Commit `4b75c00` "V0.5: Parallel analysis, bounce filter, highlight calibration, WMP fix").

**Neu seit V0.5-Commit (uncommittet):**

- Neu: `install-TTLab.bat` (One-Click-Installer für Endanwender, siehe Roadmap)
- Neu: `TTLab starten.bat` (im Repo, war bisher nur auf dem Desktop vorhanden)
- Neu (V0.6 Phase 1): `backend/app/labeling.py`, Labeling-API in `main.py` + `schemas.py`, `frontend/app/labeling/page.tsx`, `frontend/components/FrameLabeler.tsx`, `frontend/lib/types.ts` erweitert, `backend/ml/` (train_yolo.py, export_onnx.py, README.md)
- Aktualisiert: `README.md`, `README.de.md` (vereinfachte Installation), `PROJEKTUEBERGABE.md` (Roadmap V0.9: One-File-.exe, V0.6-Status)

**Commit-Vorschlag:**

```bash
git add -A
git commit -m "V0.6 Phase 1: Labeling-Tool (Frame-Extraktion, YOLO-Datensatz, Export), Trainings-Skripte, One-Click-Installer"
git push
```

---

### Technische Schulden

#### Fehlende Automated Tests

**Status:** Kein permanentes Test-Framework. In V0.5 wurden Korrektheit ad-hoc mit temporären Skripten verifiziert (Bit-Identität Motion-Pipeline, Seek-Äquivalenz `single` vs `triple`, 6 Bounce-Szenarien, Highlight-Grenzfälle) – diese Skripte sind nicht eingecheckt.

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

- Upload startet Background-Analyse (Streaming, 1MB-Chunks)
- Frontend pollt Status des ausgewählten Matches jede Sekunde, Dashboard-Statistiken alle 3s
- Bei Timeout: User sieht "Analyse läuft...", aber Backend arbeitet weiter
- Nach Abschluss: Status wechselt zu "completed", UI aktualisiert automatisch

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

### Kurzfristig (nächste Sitzung: V0.6)

| Feature | Status | Priorität | Aufwand |
|---------|--------|-----------|---------|
| ~~V0.5-Änderungen committen & pushen~~ | ✅ Erledigt (Commit `4b75c00`) | - | - |
| ~~One-Click-Installer `install-TTLab.bat`~~ | ✅ Erledigt (winget-basiert) | - | - |
| ~~README vereinfachen (Installation für Laien)~~ | ✅ Erledigt (DE + EN) | - | - |
| ~~Labeling Tool~~ | ✅ Erledigt (Phase 1 V0.6, siehe Versionshistorie) | - | - |
| ~~Trainings-Skripte (train_yolo.py, export_onnx.py)~~ | ✅ Erledigt | - | - |
| Datensatz sammeln (500-1000 Frames) | ✅ Erledigt: 618 Frames (517 Ball / 101 Negativ), exportiert | - | - |
| YOLOv8n Training | 🟡 User-Aufgabe (GTX-1050-Desktop), ZIP-Download bereit | Hoch | 4h |
| ~~Ball-Tracking Integration (Phase 2)~~ | ✅ Code fertig & verifiziert (offen: Masken-Semantik, ML-Realtest) | - | - |
| Evaluation Heuristik vs. ML (Phase 3) | ⚪ Pending (braucht trainiertes Modell) | Hoch | 4h |
| E2E-Tests ins Repo (Paket 2) | ✅ Erledigt (27.09.2026): `frontend/e2e/`, `npm run e2e`, 6/6 grün | - | - |
| pytest-Backend-Tests (Paket 3) | ✅ Erledigt (27.09.2026): `backend/tests/`, 48/48 grün, `requirements-dev.txt` | - | - |

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
| One-File-Desktop-App (.exe) – **V0.9** | ⚪ Pending | Hoch | 16h |
| Multi-Camera Support | ⚪ Pending | Niedrig | 24h |
| 3D-Trajektorie Rekonstruktion | ⚪ Pending | Niedrig | 32h |
| Cloud-Sync (optional) | ⚪ Pending | Niedrig | 16h |
| Plugin-System für Erweiterungen | ⚪ Pending | Niedrig | 20h |
| Mobile App (React Native) | ⚪ Pending | Niedrig | 40h |

#### V0.9: One-File-Desktop-App (.exe)

**Ziel:** Ein einzelner Installer bzw. eine einzelne `TTLab.exe`, die ohne Python, Node.js oder FFmpeg-Vorinstallation läuft – TTLab per Doppelklick nutzbar wie eine normale Desktop-App.

**Geplanter Ansatz (Web-UI bleibt erhalten!):**

1. Frontend als statischen Build exportieren (`next build` mit `output: 'export'`) und vom FastAPI-Backend via `StaticFiles` ausliefern – nur noch ein Server-Prozess
2. Backend mit **PyInstaller** packen (inkl. OpenCV, onnxruntime, ML-Modell)
3. FFmpeg einbetten (Lizenz GPL/LGPL beachten, ~100 MB) oder beim ersten Start automatisch herunterladen
4. EXe startet Server auf localhost und öffnet automatisch den Browser
5. Optional: Installer mit Inno Setup, Auto-Update-Mechanismus

**Bewertung:** Sehr sinnvoll für die Zielgruppe (Trainer/Spieler ohne IT-Hintergrund). Aufwand ~16h. Bewusst ans Projektende geplant (V0.9), weil sich die Dependencies bis dahin ändern (onnxruntime, ML-Modelle) und der Installer sonst jede Version neu gebaut und getestet werden müsste. Zwischenlösung bis dahin: `install-TTLab.bat` (umgesetzt).

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
│   │   ├── ball_detector.py     # V0.6: Ball-Erkennung (Heuristik + ML/ONNX + Fallback)
│   │   ├── labeling.py          # V0.6: Labeling-Backend (Frames, Datensätze, Export)
│   │   ├── video_processor.py   # FFmpeg Wrapper + Rotations-Helfer (get_display_rotation)
│   │   └── schemas.py           # Pydantic Schemas für Request/Response
│   │
│   ├── venv/                    # Python Virtual Environment (nicht versioniert)
│   ├── reencode_clips.py        # Einmal-Migration: 10-bit-Clips → 8-bit yuv420p (WMP-Fix)
│   ├── ml/                      # V0.6: Trainings-Skripte (laufen auf dem Trainings-PC, nicht auf dem Server)
│   │   ├── train_yolo.py        #   YOLOv8n-Training (GTX 1050, 2 GB VRAM)
│   │   ├── export_onnx.py       #   best.pt → data/models/ball_yolov8n.onnx
│   │   └── README.md            #   Schritt-für-Schritt-Anleitung (Linux Mint)
│   ├── requirements.txt         # Python Dependencies
│   └── .env                     # Lokale Konfiguration (nicht versioniert)
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root Layout mit Providers + Navigation
│   │   ├── page.tsx             # Dashboard (Match-Liste, Stats, Polling)
│   │   ├── labeling/page.tsx    # V0.6: Labeling-Tool (Datensatz/Video-Auswahl, Export)
│   │   └── globals.css          # Globale Styles (Tailwind)
│   │
│   ├── components/
│   │   ├── MatchList.tsx        # Match-Übersicht mit Filter
│   │   ├── MatchDetail.tsx      # Detail-View mit Player, Shortcuts, Highlights
│   │   ├── VideoUpload.tsx      # Upload (Drag & Drop)
│   │   ├── FrameLabeler.tsx     # V0.6: Labeling-Workbench (Frame-Navigation, BBox-Zeichnung)
│   │   ├── LanguageSwitcher.tsx # DE/EN-Umschalter + Shortcuts-Button
│   │   └── ShortcutsModal.tsx   # Tastatur-Shortcuts-Übersicht
│   │
│   ├── lib/
│   │   ├── api.ts               # API_BASE/apiUrl-Helper
│   │   ├── types.ts             # Geteilte Typen (Match, Rally, AnalysisMode)
│   │   ├── translations.ts      # DE/EN-Übersetzungen
│   │   └── LanguageContext.tsx  # Language-Provider/Hook
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
│   ├── datasets/                # V0.6: Labeling-Datensätze (raw/ + yolo-Export)
│   ├── models/                  # V0.6: trainierte ONNX-Modelle (ball_yolov8n.onnx)
│   └── db/
│       └── ttlab.db             # SQLite Datenbank
│
├── .git/                        # Git Repository
├── .gitignore                   # Ausschlussregeln (data/, venv/, node_modules/)
├── .gitattributes               # Line Endings (LF für Code, CRLF für .bat)
├── README.md                    # Projektübersicht & Quickstart
├── README.de.md                 # Deutsche Projektübersicht & Quickstart
├── install-TTLab.bat            # One-Click-Installer für Endanwender (winget-basiert)
├── TTLab starten.bat            # Start-Skript (Backend + Frontend + Browser)
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

#### Übersicht (Stand V0.5, aus `backend/app/main.py`)

| Methode | Pfad | Zweck |
|---------|------|-------|
| POST | `/api/upload` | Video hochladen (Streaming, 1MB-Chunks), Match erstellen |
| GET | `/api/matches` | Alle Matches |
| GET | `/api/matches/{id}` | Einzelnes Match |
| PATCH | `/api/matches/{id}` | Metadaten aktualisieren (Titel, Spieler, Ergebnis, Notizen, …) |
| DELETE | `/api/matches/{id}` | Match löschen (inkl. Clips & Rallys) |
| POST | `/api/matches/{id}/analyze?mode=performance\|background` | Analyse starten (**V0.5:** Modus-Wahl) |
| POST | `/api/matches/{id}/reevaluate-highlights` | **Neu (V0.5):** Highlights mit aktuellen Regeln neu bewerten |
| GET | `/api/matches/{id}/rallies` | Alle Rallys eines Matches |
| GET | `/api/matches/{id}/status` | Verarbeitungsstatus (Progress, Message) |
| GET | `/api/matches/{id}/export-highlights-video?fast=true` | Highlight-Video exportieren |
| GET | `/api/matches/{id}/export-all-rallies-video?fast=true` | Alle-Rallys-Video exportieren |
| GET | `/api/matches/{id}/download-all-rallies` | Alle Clips als ZIP |
| GET | `/api/matches/{id}/download-highlights` | Highlight-Clips als ZIP |
| PATCH | `/api/rallies/{id}` | Rally aktualisieren (Validierung, Notiz, manuelles Highlight) |
| GET | `/api/clips/{clip_filename}` | Clip streamen (Range-Support) |
| GET | `/api/videos/{video_filename}` | Originalvideo streamen (Range-Support) |
| GET | `/api/matches/{id}/video-info` | **Neu (V0.6):** Video-Metadaten (fps, Frame-Anzahl) für Labeling-UI |
| GET | `/api/matches/{id}/frame?frame=N` | **Neu (V0.6):** Einzelnen Frame als JPEG (server-seitig extrahiert, HEVC-fähig) |
| GET | `/api/labeling/datasets` | **Neu (V0.6):** Alle Datensätze mit Statistiken |
| POST | `/api/labeling/datasets` | **Neu (V0.6):** Datensatz erstellen |
| GET | `/api/labeling/datasets/{ds}/annotations` | **Neu (V0.6):** Alle Annotationen eines Datensatzes |
| POST | `/api/labeling/datasets/{ds}/annotations` | **Neu (V0.6):** Frame-Annotation speichern (überschreibt vorhandene) |
| DELETE | `/api/labeling/datasets/{ds}/annotations/{match_id}/{frame}` | **Neu (V0.6):** Annotation löschen |
| POST | `/api/labeling/datasets/{ds}/export` | **Neu (V0.6):** YOLO-Trainingslayout erstellen (train/val-Split + data.yaml mit relativem, portablen Pfad) |
| GET | `/api/labeling/datasets/{ds}/download` | **Neu (V0.6):** Exportierten Datensatz als ZIP herunterladen (für Transfer auf den Trainings-PC) |
| POST | `/api/shutdown` | **Neu (27.09.2026):** TTLab komplett beenden (Backend, Frontend-Devserver, Shell-Fenster). `409`, solange eine Videoanalyse läuft |
| GET | `/api/health` | Health Check |

**Hinweis:** Match- und Rally-IDs sind Integer (nicht UUID). Match-Status: `pending`, `processing`, `completed`, `failed`.

#### POST /api/matches/{id}/analyze (V0.5 geändert)

**Query Parameters:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `mode` | string | `background` | `performance`: alle Kerne minus 1, volle Auflösung, bit-identisches Ergebnis. `background`: halbe Kerne, `frame_step=2`, 960px – PC bleibt nutzbar |

**Response:**

```json
{ "message": "Analyse gestartet", "mode": "performance" }
```

**Status Codes:** `202 Accepted`, `400` (ungültiger Modus / kein Video / läuft bereits), `404`

#### POST /api/matches/{id}/reevaluate-highlights (Neu in V0.5)

**Beschreibung:** Wendet die aktuelle Highlight-Heuristik (`classify_highlight`: Dauer ≥ 10s ODER ≥ 24 Impacts ODER Score ≥ 0.9 × Match-Maximum) auf alle Rallys eines abgeschlossenen Matches an – ohne neue Video-Analyse. Manuelle Markierungen (`user_marked_highlight`) bleiben unberührt und halten die Rally dauerhaft als Highlight (auch wenn die Heuristik sie nicht auswählen würde).

**Response:**

```json
{ "message": "Highlights neu bewertet", "highlights": 12, "total_rallies": 100 }
```

**Status Codes:** `200 OK`, `400` (Match nicht abgeschlossen), `404`

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

> **Endanwender:** Doppelklick auf `install-TTLab.bat` im Projektordner – installiert Python, Node.js und FFmpeg automatisch (falls fehlt) und richtet alles ein. Das folgende Kapitel beschreibt die manuelle Installation für Entwickler.

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

**Zweck:** Kernlogik der Ballwechsel-Erkennung (Motion + Audio + Ball), seit V0.5 vollständig parallelisiert

**Architektur (V0.5):**

```python
class RallyDetector:
    def __init__(self, motion_threshold=15.0, audio_threshold=0.3)
        # Bounce-Filter: bounce_height_decay=0.95, bounce_interval_decay=0.85,
        #                bounce_entry_ratio=0.9
        # Highlight-Regeln: highlight_min_duration=10.0 (s),
        #                   highlight_min_impacts=24, highlight_score_ratio=0.9
        # ball_seek_mode = "single" (1 Seek statt 3, ~2.8x schneller; "triple" = Fallback)

    # --- Pipeline (aufgerufen aus main.process_match_background_sync) ---
    def extract_motion_features(video_path, max_workers, frame_step=1,
                                max_width=None, progress_callback=None)
        # Segment-parallele Bewegungsanalyse: Jeder Worker bekommt eigene
        # VideoCapture + POS_FRAMES-Seek; Chunk-Grenzen liegen auf dem
        # Frame-Step-Raster. frame_step=1 + max_workers=1 + max_width=None
        # = bit-identisch zur ursprünglichen single-threaded Erkennung.
    def extract_audio_features(video_path)      # librosa, läuft parallel zur Motion-Phase
    def detect_rallies(video_path, mode, progress_callback)
        # Orchestriert: Motion + Audio (parallel) → Kombination → Audio-Peak-Gruppen
        # → Bounce-Filter → Ball-Validierung (parallel) → Rally-Segmente

    # --- Highlight & Bounce ---
    def classify_highlight(duration, impact_count, score, max_score)
        # Highlight wenn Dauer>=10s ODER Impacts>=24 ODER Score>=0.9*max
    def _strip_bounce_tail(...)                 # verwirft/kürzt "Ball aufheben/werfen"-Phasen

    # --- Ball-Validierung (parallel über Gruppen) ---
    def _validate_ball_hits(...)                # Queue + Threads, Live-Fortschritt
    def _ball_scanner(...)                      # persistente VideoCapture pro Worker
    def _read_peak_frames_single(...)           # 1-Seek-Variante (Standard)
    def _read_peak_frames_triple(...)           # 3-Seek-Variante (Fallback)
    def _is_ball_candidate(...)                 # Helligkeit + Größe im Tischbereich

    # --- Score-Fusion ---
    def _resample_motion(...)                   # Motion auf Audio-Zeitpunkte resampeln
    def _combine_scores(...)                    # gewichtete Kombination Motion+Audio
    def _find_rally_segments(...)               # Schwellwert-Segmente → Rallys
```

**Wichtige Konstanten/Stellen:**

- Modus-Parameter in `main.py`: `performance` → `frame_step=1`, volle Auflösung, Worker `max(1, cpu-1)`; `background` → `frame_step=2`, `motion_max_width=960`, Worker `max(1, cpu//2 - 1)`
- Phasen-Progress: startet bei 2 %, Motion 2–40 %, Ball-Validierung 50–62 % mit Live-Zähler, Clips danach
- Clip-Extraktion: `video_processor.create_rally_clips(max_workers, progress_callback)` mit ThreadPoolExecutor (FFmpeg, `threads=2` je Prozess)

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

### Sofort (nächste Sitzung: V0.6 fortsetzen – Pakete 2 & 3)

**Aktueller Stand:** Phase 2 Code fertig & verifiziert (siehe Versionshistorie V0.6), uncommittet (Stand 20.09.2026): `backend/app/ball_detector.py` (neu), `rally_detection.py`, `video_processor.py`, `labeling.py`, `models.py`, `database.py`, `schemas.py`, `main.py`, `requirements.txt` (+ onnxruntime), `PROJEKTUEBERGABE.md`. Frontend-Änderungen aus derselben Sitzung (ShortcutsModal-Portal-Fix, FrameLabeler-Watchdog/Last-Labeled-Button, Sprungweiten-Feld) ebenfalls uncommittet. **Commit-Vorschlag:** zwei Commits: 1) Frontend-Fixes „V0.6 UX: Shortcut-Modal-Portal, Frame-Lade-Watchdog, letzter gelabelter Frame, Sprungweite einstellbar", 2) Backend „V0.6 Phase 2: Ball-Detector (ML+Heuristik-Fallback), Rotations-Fix, model_version".

**WICHTIG für die nächste Sitzung:**
1. ~~**Offene Masken-Frage klären**~~ ✅ **Erledigt (27.09.2026):** Tischplatte bleibt Default (Faktor 0.0) – Ground-Truth-Messung siehe Versionshistorie V0.6. Beim ML-Realtest zusätzlich `TTLAB_PLAY_ZONE=0.5/1.0` gegen dieselbe Ground-Truth messen (Hypothese: ML-Detektor + Zone = Recall-Gewinn ohne Präzisionsverlust).
2. ~~**Paket 2 – E2E-Tests ins Repo**~~ ✅ **Erledigt (27.09.2026):** 6 Suiten unter `frontend/e2e/` (test-draw/jump/scroll/modal/rapid/lastlabeled.mjs, 1:1 aus der vorherigen Sitzung überführt, 2 kaputte Assertionen korrigiert), Runner `npm run e2e` (Exit-Code pro Suite via `process.exitCode`), `puppeteer-core` als devDependency, README mit Voraussetzungen. **Alle 6 Suiten laufen grün** (verifiziert am 27.09.2026). Suiten legen eigene `uitest_*`/`jumptest_*`/…-Datensätze an, `v1-ml-training` wird nie angefasst.
3. ~~**Paket 3 – pytest**~~ ✅ **Erledigt (27.09.2026):** `backend/tests/` mit `test_labeling.py` (BBox-Validierung, Altformat-Migration, BOM, kaputtes JSON, Export-Determinismus + data.yaml-Portabilität + Multi-Box/Negativ-Labels, Stats), `test_highlights.py` (classify_highlight-Grenzfälle: exakt 10s/24 Impacts/0.9×max, max_score=0, Cap bei 1.0), `test_bounce_filter.py` (7 Bounce-Szenarien + Nicht-Mutation), `test_video_processor.py` (_parse_frame_rate inkl. eval-Injektion & 0-Divisor, rotate_frame 0°=No-Op gleiche Objekt-Identität, 90/180/270, Roundtrip). **48/48 Tests grün** (`python -m pytest tests`). `requirements-dev.txt` (pytest) angelegt. Phase-2-Verifikationsskripte eingecheckt unter `backend/tests/phase2_verification/` (README erklärt Bit-Identitäts-Workflow; `.npy`-Baseline bewusst nicht im Repo). Hinweis: das Backend-venv wurde verschoben – pip nur per `python -m pip` nutzen, `pip.exe` zeigt noch auf den alten Pfad.
4. ~~**Nach dem Training des Users:** `data/models/ball_yolov8n.onnx` liegt bereit → komplette Analyse eines Matches mit ML laufen lassen, mit Heuristik + User-Ground-Truth vergleichen; Evaluationsskript `evaluate.py` bauen~~ ✅ **Erledigt (04.10.2026):** Modell trainiert (mAP50 0.804), `evaluate.py` gebaut, ML-Realtest gegen Ground-Truth gefahren – Ergebnisse + Entscheidung siehe „ML-REALTEST ABSCHLOSSEN" in der Versionshistorie. Nächste Hebel: Modell-Recall verbessern (mehr Frames), danach V0.7.

**Beenden-Funktion & Start-Skript-Fix (27.09.2026, umgesetzt & E2E-verifiziert):**
- **`TTLab starten.bat`:** Räumt vor dem Start alte TTLab-Prozesse auf (schließt Fenster mit Titel „TTLab Backend/Frontend" per `taskkill /T /F`, killt alles auf Port 8000/3000 per PowerShell) – der `WinError 10013` (Port durch vergessenen alten Prozess belegt) kann so nicht mehr auftreten. **Ortsunabhängig:** Liegt die .bat nicht im Projektordner (z.B. Desktop-Kopie), fällt sie auf den festen Pfad `C:\Users\Jonas\Documents\OpenCode\ttlab\` zurück (mit Fehlermeldung, falls auch der nicht existiert) – Desktop-Kopie und Repo-Version sind identisch.
- **Windows-Terminal-Fix im Shutdown:** `start`-Fenster öffnen bei Win11-Default in Windows Terminal, wo `cmd.exe` keinen Fenstertitel trägt – das Skript sammelt deshalb die **Eltern-cmd-Kette jedes Server-Prozesses VOR dem Kill** (CIM-Instanzen verschwinden mit dem Prozess!) und schließt alle cmd-Vorfahren (inkl. npm.cmd-Zwischenschicht), tötet aber niemals `WindowsTerminal.exe` selbst (fremde Tabs des Nutzers).
- **Beenden-Button** oben rechts (`ShutdownButton.tsx`, rot, „⏻ Beenden", DE/EN, Bestätigungs-Schritt): ruft `POST /api/shutdown`. Der Endpoint **verweigert mit 409, solange ein Match `status="processing"` hat** (Notizen & Labeling speichern ohnehin automatisch – Debounce/Auto-Save). Sonst startet er `shutdown_ttlab.ps1` (Repo-Root, detached via `CREATE_NO_WINDOW` + DEVNULL-Handles – `DETACHED_PROCESS`+`close_fds` lässt PowerShell lautlos sterben!) und beendet: Backend-PID, alles auf Port 8000/3000, die TTLab-Shell-Fenster. Frontend versucht `window.close()` und zeigt sonst ein Vollbild-Overlay „TTLab wurde beendet – Tab kann geschlossen werden".
- **Verifikation:** Echter Shutdown-Run (Ports 8000+3000 tot, beide Dummy-Shell-Fenster geschlossen, Log `%TEMP%\ttlab_shutdown.log`), 409-Schutz mit künstlich laufender Analyse (Backend überlebt), Button im Frontend-Markup. Stolperfalle entdeckt: Der Backend-Start setzt `processing`-Matches auf `pending` zurück (Stale-Reset im lifespan) – der 409-Test muss den Status NACH dem Start setzen.

### Danach (V0.7/V0.8)

1. **Shot-Klassifikation (V0.7)**
   - Datensatz für Vorhand/Rückhand/Topspin/Slice sammeln
   - CNN-LSTM Hybrid-Modell trainieren
   - In Rally-Erkennung integrieren

2. **Taktik-Analyse (V0.8)**
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

**Letztes Update:** 5. September 2026 (V0.5)  
**Autor:** TTLab Development Team  
**Lizenz:** Proprietär (alle Rechte vorbehalten)
