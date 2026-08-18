# 🏓 TTLab – KI-gestützte Tischtennis-Videoanalyse

[![Version](https://img.shields.io/badge/Version-0.3.0-blue.svg)](https://github.com/yourusername/ttlab/releases)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-19-black.svg?logo=next.js)](https://nextjs.org)
[![Built with](https://img.shields.io/badge/Built%20with-opencode-purple.svg)](https://opencode.ai)

**Automatische Ballwechsel-Erkennung für Tischtennis-Videos – 100% lokal, ohne Cloud-Zwang.**

---

## 🎯 Was ist TTLab?

TTLab ist eine **Open-Source-Alternative** zu vergleichbaren kommerziellen Plattformen. Die Software analysiert deine Trainingsvideos automatisch, erkennt Ballwechsel (Rallies) durch KI-gestützte Bewegungs- und Audioanalyse, und extrahiert diese als einzelne Clips – alles **lokal auf deinem Rechner**, ohne Abo-Kosten oder Datenweitergabe an Dritte.

### ✨ Kernfunktionen

- 🎾 **Automatische Rally-Erkennung** – Kombination aus Motion Detection, Audio-Peaks und Ball-Tracking
- 🔒 **100% Lokal & Privat** – Keine Cloud, keine API-Calls, deine Videos bleiben privat
- 📊 **Match-Verwaltung** – Metadaten, Statistiken, Filter nach Sieg/Niederlage
- ⚡ **Schnelle Analyse** – Asynchrone Verarbeitung im Hintergrund mit Fortschrittsanzeige
- 🛠️ **Manuelle Kalibrierung** – Interaktive Tischmarkierung für präzisere Erkennung
- 🎬 **Clip-Export** – Alle akzeptierten Highlights als einzelnes Video exportieren

---

## 📸 Einblicke

![Dashboard](docs/screenshots/dashboard.png)
*Dashboard mit Match-Übersicht, Statistiken und Upload-Bereich.*

![Tischkalibrierung](docs/screenshots/table-calibration.png)
*Interaktive Tischmarkierung – 4 Ecken klicken um den Spielbereich zu definieren.*

![Rally Timeline](docs/screenshots/rally-timeline.png)
*Rally-Timeline mit Notizen, Filtern und Validierungsstatus für jeden Ballwechsel.*

---

## 🚀 Schnelleinstieg

### Ein-Klick-Start (Windows) ⭐

**Nach der Installation** einfach doppelt auf **"TTLab starten.bat"** auf dem Desktop klicken – Backend und Frontend werden automatisch gestartet. Keine Terminal-Befehle nötig!

### Voraussetzungen

| Software | Version | Link |
|----------|---------|------|
| Python | 3.13+ | [Download](https://python.org) |
| Node.js | 20+ | [Download](https://nodejs.org) |
| FFmpeg | 7.x | [Anleitung](https://www.gyan.dev/ffmpeg/builds/) |

### Installation in 5 Minuten

```bash
# 1. Repository klonen
git clone https://github.com/DEIN_USERNAME/ttlab.git
cd ttlab

# 2. Backend installieren
cd backend
uv venv
.\venv\Scripts\activate  # Windows
uv pip install -r requirements.txt

# 3. Frontend installieren
cd ../frontend
npm install

# 4. Desktop-Verknüpfung erstellen (Windows)
# Kopiere "TTLab starten.bat" auf deinen Desktop
```

**FFmpeg nicht vergessen!** Ohne FFmpeg können keine Clips extrahiert werden.

---

## 📖 Bedienung

### Erster Workflow

1. **Video hochladen** – MP4, AVI, MOV, MKV oder WebM über das Frontend
2. **Tisch markieren** – 4 Ecken im Video anklicken (einmal pro Match)
3. **Analyse starten** – Klick auf "Analyse jetzt starten"
4. **Rallies prüfen** – Timeline durchgehen, falsche Erkennungen ablehnen
5. **Highlights exportieren** – Alle akzeptierten Ballwechsel als Video

### Filter-Funktionen

- **Alle Rallys** – Vollständige Liste
- **⭐ Highlights** – Manuell markierte Top-Ballwechsel
- **✅ Ballwechsel** – Nur akzeptierte Rallys
- **❌ Kein Ballwechsel** – Abgelehnte Erkennungen

### Sprachumschaltung

Klicke auf den **🇩🇪 DE / 🇬🇧 EN** Button oben rechts, um zwischen deutscher und englischer Oberfläche zu wechseln.

---

## 🗺️ Roadmap

| Version | Status | Features |
|---------|--------|----------|
| **V0.1** | ✅ | Video Upload, Rally Detection (Motion + Audio), Clip-Export |
| **V0.2** | ✅ | Match-Metadaten, Statistik-Dashboard, Ergebnis-Filter |
| **V0.3** | ✅ | Tischkalibrierung, Rally-Validierung, 100ms-Navigation |
| **V0.4** | 🔄 | Trainiertes YOLOv8n-Ball-Tracking, Labeling-Tool |
| **V0.5** | ⏳ | Player Detection, Pose Estimation, Schlagtyp-Erkennung |
| **V0.6** | ⏳ | Taktik-Analyse, Heatmaps, Schwachstellen-Erkennung |
| **V1.0** | ⏳ | KI-Coach (LLM), Spielerprofile, Trainingspläne |

---

## 🏗️ Architektur

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

## 🤝 Mitmachen

### Beitrag leisten

- 🐛 **Fehler melden** – [Issue öffnen](https://github.com/DEIN_USERNAME/ttlab/issues)
- 💡 **Feature wünschen** – Diskussion im [Discussions-Tab](https://github.com/DEIN_USERNAME/ttlab/discussions)
- 🔧 **Code beitragen** – Pull Requests sind willkommen!

### Entwicklung

```bash
# Backend testen
cd backend
pytest

# Frontend testen
cd frontend
npm run test
```

---

## ❓ FAQ

**F: Warum wird mein Video nicht analysiert?**  
A: Stelle sicher, dass FFmpeg installiert und im PATH ist. Prüfe die Console-Logs des Backends.

**F: Kann ich TTLab auf einem Server betreiben?**  
A: Ja! Anleitung unter [Deployment](docs/DEPLOYMENT.md).

**F: Wie genau ist die Rally-Erkennung?**  
A: V0.3 erreicht ~60-70% Precision. V0.4 mit trainiertem Modell soll >90% erreichen.

**F: Sind mehrere Benutzer möglich?**  
A: Aktuell nein. Multi-User-Support ist für V1.0 geplant.

---

## 📄 Lizenz

Dieses Projekt ist **proprietär**. Alle Rechte vorbehalten.

Eine kommerzielle Nutzung ist nur mit ausdrücklicher Genehmigung gestattet.

Siehe [LICENSE](LICENSE) für Details.

---

## 🙏 Danksagung

**Entwickelt mit [opencode](https://opencode.ai)** – KI-gestützte Code-Generierung für moderne Webanwendungen.

Besonderer Dank an:
- Die Tischtennis-Community für Inspiration und Feedback
- Open-Source-Projekte wie OpenCV, FastAPI und Next.js

---

## 📬 Kontakt

| Platform | Link |
|----------|------|
| GitHub | [@DEIN_USERNAME](https://github.com/DEIN_USERNAME) |
| Website | _kommt bald_ |
| Discord | _kommt bald_ |

---

<div align="center">

**Made with ❤️ for Table Tennis Players**  
[⬆ Nach oben](#ttlab-ki-gestützte-tischtennis-videoanalyse)

</div>
