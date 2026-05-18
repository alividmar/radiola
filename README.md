# ◉ Radiola

**Radiola** is a lightweight internet radio player for Linux, Windows and macOS, written in Python with a tkinter GUI.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.4.0-orange)

---

## ✨ Features

| | |
|---|---|
| 📻 | Stream internet radio stations (Shoutcast, Icecast, HLS) |
| 🖼 | Station icons (PNG/JPG/WEBP, 225×225 px, stored as base64) |
| 🔊 | Volume slider + mouse wheel on slider |
| 🎙 | Auto volume boost on speech detection (via ICY metadata title matching) |
| ⏱ | Sleep timer with optional gradual fade-out |
| ✏️ | Built-in station editor (multi-select, drag & drop, Ctrl+A, Delete) |
| 📂 | Import / export stations (.txt) — add or replace mode |
| 🌍 | Station search — **Radio Browser** (free, no key) + **RapidAPI** (90k+ stations) |
| 🌐 | Auto icon download (favicon scraping) |
| 🗂 | `ICONS/` folder with built-in image browser and preview |
| 🌙 | Automatic light / dark theme detection |
| 🇸🇮 🇬🇧 | Slovenian and English UI |

---

## 📸 Layout

```
┌─────────────────────────────────────────────────────────┐
│ ◉ Radiola                         player: mpv · Linux   │
├───────────────────────┬──────┬──────┬───────────────────┤
│ STATION  ◀ menu ▶    │  🔊  │  🎙  │                   │
│ NOW PLAYING  ○ kw    │  72% │ +30% │   station icon    │
│ Song title here...   │  ↕   │ [✓]  │   (auto square)   │
├───────────────────────┴──────┴──────┴───────────────────┤
│ ▶ Play  ■ Stop   Timer: 30 min ▶ ×  ☑ Fade before stop  │
├─────────────────────────────────────────────────────────┤
│  📻 Val202  🎸 ROCK1  📡 ROBIN  ...  (2 rows × 8)       │
│  ● LIVE — Val 202                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Requirements

### Python packages
```bash
pip install pillow requests
```

> `requests` is optional — Radio Browser search works without it (uses built-in `urllib`).

### Media player (required)

| OS | Player | Install |
|---|---|---|
| **Linux** | `mpv` | `sudo apt install mpv` |
| **macOS** | `mpv` | `brew install mpv` |
| **Windows** | `mpv.exe` | [mpv.io](https://mpv.io/installation/) — place next to Radiola.exe |

---

## 🚀 Quick Start

```bash
git clone https://github.com/alividmar/radiola.git
cd radiola
pip install -r requirements.txt
python3 radiola.py
```

---

## 📁 Project Structure

```
radiola/
├── radiola.py              # Main application
├── radiola.spec            # PyInstaller build config
├── build.py                # Local build script (→ EXE/AppImage)
├── requirements.txt
├── ICONS/                  # Local station icons folder
├── docs/
│   ├── radiola_navodila.html   # User manual (SL + EN)
│   ├── packaging_guide.html    # Build EXE/AppImage guide
│   └── github_vodic.html       # GitHub guide
├── scraper_ikone.py        # Tool: bulk icon download
└── scraper_slo_radio.py    # Tool: scrape SLO radio stations
```

---

## 🌍 Station Search

The built-in search dialog has two tabs:

### 🆓 Radio Browser — no registration, no limits
- ~35,000 verified active stations
- Filter by country, genre
- Sort by votes / popularity / name / bitrate
- "Active only" toggle (streams checked daily)

### 🔑 RapidAPI — 90,000+ stations
1. Free signup at [rapidapi.com](https://rapidapi.com) → **50K Radio Stations** → Subscribe (500 req/month free)
2. **Settings → RapidAPI key…** → paste your key

---

## 🎙 Speech Detection & Auto Volume Boost

Radiola matches ICY metadata titles against keywords and automatically raises the volume for spoken content.

```
Settings → Keyword…
Enter: talk;news;vote;speech;interview
```

- Matching is **substring-based** — `vote` also matches *voting*, *voter*
- Set boost amount with the 🎙 slider (+0–60%)
- Per-station keyword overrides the global setting

---

## ⌨️ Shortcuts

| Action | Shortcut |
|---|---|
| Volume up/down | Scroll wheel **on the volume slider** |
| Select all (editor) | `Ctrl+A` |
| Delete selected (editor) | `Delete` / `Backspace` |
| Multi-select (editor) | `Ctrl+click` / `Shift+click` |
| Reorder station (editor) | Drag & drop |

---

## 📦 Building EXE / AppImage

```bash
pip install pyinstaller
python3 build.py
```

| Platform | Output |
|---|---|
| 🪟 Windows | `dist/Radiola/Radiola.exe` |
| 🐧 Linux | `dist/Radiola/Radiola` + `*.AppImage` |
| 🍎 macOS | `dist/Radiola.app` |

### GitHub Actions — automated builds for all platforms

```bash
git tag v1.4.0
git push origin --tags
# → EXE + AppImage appear in GitHub Releases in ~10 minutes
```

---

## ⚙️ settings.json

| Key | Description | Default |
|---|---|---|
| `glasnost` | Volume 0.0–1.0 | `0.6` |
| `dvig` | Speech boost 0.0–0.6 | `0.3` |
| `kw_glasnost` | Absolute target volume on speech (0 = relative) | `0.0` |
| `kljucna_beseda` | Keywords separated by `;` | `"talk"` |
| `jezik` | UI language: `si` / `en` | `"en"` |
| `icon_rows` | Icon grid rows: 1 or 2 | `2` |
| `avto_predvajaj` | Auto-play on startup | `false` |
| `rapidapi_key` | RapidAPI key (optional) | `""` |

---

## 🤝 Contributing

Pull requests are welcome! For major changes please open an issue first.

```bash
git checkout -b feature/my-feature
git commit -m 'Add my feature'
git push origin feature/my-feature
# → open Pull Request on GitHub
```

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 🙏 Credits

- [mpv](https://mpv.io/) — media player engine
- [Radio Browser](https://www.radio-browser.info/) — free open radio database
- [Pillow](https://python-pillow.org/) — image processing
- [RapidAPI / 50K Radio Stations](https://rapidapi.com/herihermwn/api/50k-radio-stations) — extended database
- Python tkinter — GUI framework
