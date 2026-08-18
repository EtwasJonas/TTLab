# 🏓 TTLab – AI-Powered Table Tennis Video Analysis

[![Version](https://img.shields.io/badge/Version-0.3.0-blue.svg)](https://github.com/yourusername/ttlab/releases)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-19-black.svg?logo=next.js)](https://nextjs.org)
[![Built with](https://img.shields.io/badge/Built%20with-opencode-purple.svg)](https://opencode.ai)

**Automatic rally detection for table tennis videos – 100% local, no cloud required.**

---

## 🎯 What is TTLab?

TTLab is an **open-source alternative** to commercial table tennis analysis platforms. The software automatically analyzes your training videos, detects rallies (ball exchanges) through AI-powered motion and audio analysis, and extracts them as individual clips – all **running locally on your machine**, without subscription fees or sending data to third parties.

### ✨ Key Features

- 🎾 **Automatic Rally Detection** – Combines motion detection, audio peaks, and ball tracking
- 🔒 **100% Local & Private** – No cloud, no API calls, your videos stay on your device
- 📊 **Match Management** – Metadata, statistics, filter by win/loss
- ⚡ **Fast Async Analysis** – Background processing with progress tracking
- 🛠️ **Manual Calibration** – Interactive table marking for improved accuracy
- 🎬 **Clip Export** – Export all accepted highlights as a single video

---

## 📸 Screenshots

> *Add your screenshots here:*
> - Dashboard with match overview
> - Match detail with table calibration
> - Rally timeline with filters

---

## 🚀 Quick Start

### One-Click Launch (Windows) ⭐

**After installation**, simply double-click **"TTLab starten.bat"** on your desktop to start both backend and frontend servers automatically. No terminal commands needed!

### Prerequisites

| Software | Version | Link |
|----------|---------|------|
| Python | 3.13+ | [Download](https://python.org) |
| Node.js | 20+ | [Download](https://nodejs.org) |
| FFmpeg | 7.x | [Guide](https://www.gyan.dev/ffmpeg/builds/) |

### Installation (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/ttlab.git
cd ttlab

# 2. Install backend
cd backend
uv venv
.\venv\Scripts\activate  # Windows
uv pip install -r requirements.txt

# 3. Install frontend
cd ../frontend
npm install

# 4. Create desktop shortcut (Windows)
# Copy "TTLab starten.bat" to your desktop
```

**Don't forget FFmpeg!** Without FFmpeg, clip extraction won't work.

---

## 📖 How to Use

### First Workflow

1. **Upload Video** – MP4, AVI, MOV, MKV or WebM via the frontend
2. **Mark Table** – Click 4 corners of the table in the video (once per match)
3. **Start Analysis** – Click "Start Analysis Now"
4. **Review Rallies** – Go through timeline, reject false detections
5. **Export Highlights** – Export all accepted rallies as a video

### Filter Functions

- **All Rallies** – Complete list
- **⭐ Highlights** – Manually marked top rallies
- **✅ Ball Changes** – Only accepted rallies
- **❌ No Rally** – Rejected detections

### Language Switch

Click the **🇩🇪 DE / 🇬🇧 EN** button in the top-right corner to switch between German and English interface.

---

## 🗺️ Roadmap

| Version | Status | Features |
|---------|--------|----------|
| **V0.1** | ✅ | Video Upload, Rally Detection (Motion + Audio), Clip Export |
| **V0.2** | ✅ | Match Metadata, Stats Dashboard, Result Filters |
| **V0.3** | ✅ | Table Calibration, Rally Validation, 100ms Navigation |
| **V0.4** | 🔄 | Trained YOLOv8n Ball Tracking, Labeling Tool |
| **V0.5** | ⏳ | Player Detection, Pose Estimation, Shot Type Recognition |
| **V0.6** | ⏳ | Tactical Analysis, Heatmaps, Weakness Detection |
| **V1.0** | ⏳ | AI Coach (LLM), Player Profiles, Training Plans |

---

## 🏗️ Architecture

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
**CV/ML:** OpenCV MOG2, Audio Peak Detection, YOLOv8 (planned)

---

## 🤝 Contributing

### How to Help

- 🐛 **Report Bugs** – [Open an Issue](https://github.com/YOUR_USERNAME/ttlab/issues)
- 💡 **Request Feature** – Discussion in [Discussions Tab](https://github.com/YOUR_USERNAME/ttlab/discussions)
- 🔧 **Contribute Code** – Pull Requests welcome!

### Development

```bash
# Test backend
cd backend
pytest

# Test frontend
cd frontend
npm run test
```

---

## ❓ FAQ

**Q: Why isn't my video being analyzed?**  
A: Make sure FFmpeg is installed and in your PATH. Check the backend console logs.

**Q: Can I run TTLab on a server?**  
A: Yes! See [Deployment Guide](docs/DEPLOYMENT.md).

**Q: How accurate is rally detection?**  
A: V0.3 achieves ~60-70% precision. V0.4 with trained model targets >90%.

**Q: Are multiple users supported?**  
A: Not yet. Multi-user support is planned for V1.0.

---

## 📄 License

This project is **proprietary**. All rights reserved.

Commercial use requires explicit permission from the maintainers.

See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

**Built with [opencode](https://opencode.ai)** – AI-powered code generation for modern web applications.

Special thanks to:
- The table tennis community for inspiration and feedback
- Open-source projects like OpenCV, FastAPI, and Next.js

---

## 📬 Contact

| Platform | Link |
|----------|------|
| GitHub | [@EtwasJonas](https://github.com/EtwasJonas) |
| Website | _Coming soon_ |
| Discord | _Coming soon_ |

---

<div align="center">

**Made with ❤️ for Table Tennis Players**  
[⬆ Back to Top](#ttlab-ai-powered-table-tennis-video-analysis)

</div>
