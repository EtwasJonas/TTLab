<div align="center">

<img src="docs/logo.svg" alt="TTLab Logo" style="max-width: 400px; height: auto;" />

# TTLab – KI-gestützte Tischtennis-Videoanalyse

*Table Tennis Intelligence*

</div>

[![Version](https://img.shields.io/badge/Version-0.5.0-blue)](https://github.com/yourusername/ttlab/releases)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-green)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-19-black)](https://nextjs.org)

**Automatische Ballwechsel-Erkennung für Tischtennis-Videos – 100% lokal, ohne Cloud-Zwang.**

---

## Überblick

TTLab ist eine Open-Source-Alternative zu vergleichbaren kommerziellen Plattformen. Die Software analysiert Trainingsvideos automatisch, erkennt Ballwechsel durch KI-gestützte Bewegungs- und Audioanalyse, und extrahiert diese als einzelne Clips – alles lokal auf deinem Rechner ohne Abo-Kosten oder Datenweitergabe an Dritte.

### Kernfunktionen

- **Automatische Rally-Erkennung** – Kombination aus Motion Detection, Audio-Peaks und Ball-Tracking
- **Zwei Analyse-Modi** – ⚡ Volle Leistung (alle CPU-Kerne, identische Ergebnisse) oder 🌙 Hintergrund (PC bleibt nutzbar)
- **Automatische Highlights** – Lange oder intensive Ballwechsel werden automatisch markiert; manuelle Favoriten bleiben erhalten; bestehende Matches mit einem Klick neu bewerten
- **100% Lokal & Privat** – Keine Cloud, keine API-Calls, Videos bleiben privat
- **Match-Verwaltung** – Metadaten, Statistiken, Filter nach Sieg/Niederlage/Unentschieden
- **Schnelle parallele Analyse** – Multi-Core-Pipeline mit Live-Fortschritt (Sekunden-Updates)
- **Tastatur-Shortcuts** – Play/Pause, Frame-Schritte, Rally-Navigation, Validierung (siehe In-App-Hilfe)
- **Manuelle Kalibrierung** – Interaktive Tischmarkierung für präzisere Erkennung
- **Clip-Export** – Alle Highlights oder Rallys als einzelnes Video oder ZIP

---

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)
*Dashboard mit Match-Übersicht, Statistiken und Upload-Bereich.*

![Tischkalibrierung](docs/screenshots/table-calibration.png)
*Interaktive Tischmarkierung – 4 Ecken klicken um den Spielbereich zu definieren.*

![Rally Timeline](docs/screenshots/rally-timeline.png)
*Rally-Timeline mit Notizen, Filtern und Validierungsstatus für jeden Ballwechsel.*

---

## Schnelleinstieg

### Ein-Klick-Start (Windows)

Nach der Installation einfach doppelt auf **"TTLab starten.bat"** auf dem Desktop klicken.

### Voraussetzungen

| Software | Version | Link |
|----------|---------|------|
| Python | 3.13+ | [Download](https://python.org) |
| Node.js | 20+ | [Download](https://nodejs.org) |
| FFmpeg | 7.x | [Anleitung](https://www.gyan.dev/ffmpeg/builds/) |

### Installation

```bash
# 1. Repository klonen
git clone https://github.com/DEIN_USERNAME/ttlab.git
cd ttlab

# 2. Backend installieren
cd backend
uv venv
.\venv\Scripts\activate
uv pip install -r requirements.txt

# 3. Frontend installieren
cd ../frontend
npm install
```

**Hinweis:** FFmpeg wird für die Clip-Erstellung benötigt.

---

## Bedienung

### Workflow

1. **Video hochladen** – MP4, AVI, MOV, MKV oder WebM über das Frontend
2. **Tisch markieren** – 4 Ecken im Video anklicken (einmal pro Match)
3. **Analyse starten** – ⚡ Volle Leistung oder 🌙 Hintergrund-Modus wählen
4. **Rallies prüfen** – Timeline durchgehen, falsche Erkennungen ablehnen, Highlights markieren (H)
5. **Highlights exportieren** – Alle Highlights als Video oder ZIP

### Filter

- **Alle Rallys** – Vollständige Liste
- **Highlights** – Automatische und manuell markierte Top-Ballwechsel
- **Ballwechsel** – Nur akzeptierte Rallys
- **Kein Ballwechsel** – Abgelehnte Erkennungen

### Tastatur-Shortcuts

Leertaste (Play/Pause), ←/→ (100ms-Schritte), ↑/↓ (vorherige/nächste Rally), H (Highlight), R/N/L (Validierung), 1-4 (Filter), Strg+←/→ (Video-Position). Die vollständige Liste ist über das Tastatur-Symbol in der Kopfzeile verfügbar.

### Sprachumschaltung

Oben rechts zwischen Deutsch und Englisch wechseln.

---

## Roadmap

| Version | Status | Features |
|---------|--------|----------|
| V0.1 | Veröffentlicht | Video Upload, Rally Detection (Motion + Audio), Clip-Export |
| V0.2 | Veröffentlicht | Match-Metadaten, Statistik-Dashboard, Ergebnis-Filter |
| V0.3 | Veröffentlicht | Tischkalibrierung, Rally-Validierung, 100ms-Navigation |
| V0.4 | Veröffentlicht | Dual-Mode Video-Export (Fast/Compatible) |
| V0.5 | Veröffentlicht | Parallele Analyse (2 Modi), Bounce-Filter, Auto-Highlights, Shortcuts, UX |
| V0.6 | Geplant | Trainiertes YOLOv8n-Ball-Tracking, Labeling-Tool |
| V0.7 | Geplant | Player Detection, Pose Estimation, Schlagtyp-Erkennung |
| V0.8 | Geplant | Taktik-Analyse, Heatmaps, Schwachstellen-Erkennung |
| V1.0 | Geplant | KI-Coach (LLM), Spielerprofile, Trainingspläne |

---

## Architektur

```
┌─────────────────────┐
│   Next.js Frontend  │  Port 3000
│   (React 19, TS)    │
└──────────┬──────────┘
           │ REST API
┌──────────▼──────────┐
│   FastAPI Backend   │  Port 8000
│   (Python 3.13)     │
└──────────┬──────────┘
           │ SQLAlchemy
┌──────────▼──────────┐
│   SQLite / PostgreSQL │
└──────────┬──────────┘
           │ Filesystem
┌──────────▼──────────┐
│   data/videos/      │
│   data/clips/       │
└─────────────────────┘
```

### Tech Stack

**Backend:** Python 3.13, FastAPI, OpenCV, librosa, SQLAlchemy, FFmpeg  
**Frontend:** Next.js 19, React 19, TypeScript, Tailwind CSS  
**CV/ML:** OpenCV MOG2, Audio Peak Detection, YOLOv8 (geplant)

---

## Mitmachen

- Fehler über [Issues](https://github.com/DEIN_USERNAME/ttlab/issues) melden
- Feature-Wünsche in [Discussions](https://github.com/DEIN_USERNAME/ttlab/discussions)
- Pull Requests willkommen

---

## FAQ

**F: Warum wird mein Video nicht analysiert?**  
A: FFmpeg muss installiert und im PATH sein. Backend-Console prüfen.

**F: Kann ich TTLab auf einem Server betreiben?**  
A: Ja! Siehe Deployment-Dokumentation.

**F: Wie genau ist die Rally-Erkennung?**  
A: Der Bounce-Filter aus V0.5 entfernt die meisten Fehl-Rallys (Ball aufheben/auf den Tisch springen). Trainiertes Ball-Tracking (V0.6) zielt auf >90% Precision.

**F: Das exportierte Video lässt sich im Windows Media Player nicht abspielen (Fehler 0x80004005)?**  
A: In V0.5 behoben. Clips aus 10-bit Handy-Videos (HEVC Main 10) werden jetzt als Standard 8-bit H.264 (yuv420p) encodiert. Für Clips älterer Versionen einmalig `python reencode_clips.py` im Backend-Ordner ausführen.

**F: Sind mehrere Benutzer möglich?**  
A: Aktuell nein. Für V1.0 geplant.

---

## Lizenz

Dieses Projekt ist proprietär. Alle Rechte vorbehalten. Kommerzielle Nutzung nur mit Genehmigung. Siehe [LICENSE](LICENSE) für Details.

---

## Danksagung

Entwickelt mit [opencode](https://opencode.ai). Dank an die Tischtennis-Community und Open-Source-Projekte wie OpenCV, FastAPI und Next.js.

---

<div align="center">

**Für Tischtennisspieler entwickelt**

</div>
