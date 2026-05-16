# ◉ Radiola

**Radiola** je lahek predvajalnik internetnega radia za Linux, Windows in macOS, napisan v Pythonu s tkinter GUI.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Funkcionalnosti

| | |
|---|---|
| 📻 | Predvajanje internet radio postaj (Shoutcast, Icecast, HLS) |
| 🖼 | Ikone postaj (PNG/JPG/WEBP, 225×225 px, shranjene v base64) |
| 🔊 | Drsnik glasnosti + scroll kolesa na drsniku |
| 🎙 | Samodejni dvig glasnosti pri govoru (zazna po naslovu / ICY metadata) |
| ⏱ | Timer za izklop z opcijskim postopnim utišanjem |
| ✏️ | Vgrajen urejevalnik postaj (multi-select, drag & drop, Ctrl+A, Delete) |
| 📂 | Uvoz / izvoz postaj (.txt) z izbiro načina (dodaj / zamenjaj) |
| 🌐 | Samodejni prenos ikon iz interneta (favicon scraping) |
| 🗂 | Mapa `ICONS/` za lokalne ikone s predogledom |
| 🌙 | Samodejno zaznavanje svetle / temne teme OS |
| 🇸🇮 🇬🇧 | Slovenski in angleški vmesnik |

---

## 📦 Zahteve

### Python
Python **3.8** ali novejši.

### Odvisnosti
```bash
pip install pillow requests
```

### Predvajalnik (obvezno)
Radiola za predvajanje avdia potrebuje zunanji predvajalnik:

| OS | Predvajalnik | Namestitev |
|---|---|---|
| **Linux** | `mpv` | `sudo apt install mpv` |
| **macOS** | `mpv` | `brew install mpv` |
| **Windows** | `mpv.exe` ali `ffplay.exe` | [mpv.io](https://mpv.io/installation/) — daj v PATH ali v mapo programa |

---

## 🚀 Namestitev in zagon

```bash
# 1. Kloniraj repozitorij
git clone https://github.com/TvojeIme/radiola.git
cd radiola

# 2. Namesti odvisnosti
pip install -r requirements.txt

# 3. Zaženi
python3 radiola.py
```

Na **Windowsu**:
```cmd
python radiola.py
```

---

## 📁 Struktura projekta

```
radiola/
├── radiola.py              # Glavni program
├── stations.json           # Seznam postaj (samodejno ustvarjen)
├── settings.json           # Nastavitve (samodejno ustvarjen)
├── requirements.txt        # Python odvisnosti
├── ICONS/                  # Mapa za lokalne ikone postaj
│   └── (tvoje .png/.jpg slike)
├── docs/
│   └── radiola_navodila.html   # Navodila za uporabo (SL + EN)
├── scraper_ikone.py        # Pripomoček: prenos ikon iz spleta
└── scraper_slo_radio.py    # Pripomoček: scraping SLO radio postaj
```

---

## 🖥 Postavitev okna

```
┌─────────────────────────────────────────────────────────┐
│ ◉ Radiola                         predvajalnik · sistem │
├───────────────────────┬──────┬──────┬───────────────────┤
│ POSTAJA  ◀ menu ▶    │  🔊  │  🎙  │                   │
│ ─────────────────── │  %   │  +%  │  ikona predvajane  │
│ ZDAJ PREDVAJA  ○ kw  │  │   │ [✓] │  postaje           │
│ Naslov pesmi ...     │  ↕   │  ↕   │  (kvadrat)         │
├───────────────────────┴──────┴──────┴───────────────────┤
│ ▶ Predvajaj  ■ Ustavi  Timer: 30 min ▶ ×  ☑ Utišaj     │
├─────────────────────────────────────────────────────────┤
│  📻 Val202  🎸 ROCK1  📡 ROBIN  ...  (2 vrsti × 8)      │
│  ● V ŽIVO — Val 202                                     │
└─────────────────────────────────────────────────────────┘
```

---

## ⌨️ Bližnjice

| Akcija | Bližnjica |
|---|---|
| Glasnost gor/dol | Scroll kolesa **na drsniku glasnosti** |
| Izberi vse postaje (urejevalnik) | `Ctrl+A` |
| Izbriši izbrane (urejevalnik) | `Delete` ali `Backspace` |
| Multi-select (urejevalnik) | `Ctrl+klik` / `Shift+klik` |
| Premikanje postaje (urejevalnik) | Drag & drop z miško |

---

## 📻 Dodajanje postaj

### Ročno
1. Klikni **✏ Uredi postaje → ➕ NOVA**
2. Vpiši ime, stream URL in opcijsko ikono
3. Klikni **✏ UREDI** za shranjevanje

### Uvoz iz datoteke
Format `.txt` (brez ikon):
```
# Komentar
Val 202 = http://mp3.rtvslo.si:8000/val202
ROCK 1 = http://mp3.rtvslo.si:8000/rock
Best FM = https://live.radio.si/BestFM  # kw: glasovanje
```

Format z ikonami:
```
Val 202 = http://mp3.rtvslo.si:8000/val202 = data:image/png;base64,iVBOR...
```

### Scraper (samodejni prenos)
```bash
pip install requests beautifulsoup4
python3 scraper_ikone.py --samo-brez-ikone   # doda ikone postajam ki jih nimajo
python3 scraper_ikone.py --postaja "Val 202" # test za eno postajo
python3 scraper_slo_radio.py                  # scrape vseh SLO postaj
```

---

## 🎙 Dvig glasnosti pri govoru

Radiola zazna govorno vsebino po naslovu ICY metadata in samodejno dvigne glasnost.

**Nastavitev:**
1. Nastavitve → Ključna beseda…
2. Vpiši besede ločene s `;` npr.: `govorna;glasovanje;pogovor;mix`
3. Nastavi % dviga z drsnikom 🎙 v glavnem oknu
4. Opcijsko: nastavi absolutno glasnost pri govoru (npr. 80%)

Iskanje je **podbesedilo** — `glasov` zazna tudi *glasovanje*, *glasoval*, *glasovanju*.

---

## 🗂 Mapa ICONS

Ustvari mapo `ICONS/` v isti mapi kot `radiola.py` in vanjo daj slike postaj (PNG, JPG, WEBP). Ko klikneš 📁 v urejevalniku, se brskalnik samodejno odpre v tej mapi.

---

## ⚙️ settings.json

```json
{
  "glasnost": 0.6,
  "dvig": 0.3,
  "kw_glasnost": 0.0,
  "zadnja_postaja": "Val 202",
  "avto_predvajaj": false,
  "kljucna_beseda": "govorna;glasovanje",
  "jezik": "si",
  "icon_rows": 2,
  "timer_min": 30,
  "brskalnik": ""
}
```

| Ključ | Opis |
|---|---|
| `glasnost` | Glasnost 0.0–1.0 |
| `dvig` | Relativni dvig pri govoru (0.0–0.6) |
| `kw_glasnost` | Absolutna glasnost pri govoru (0 = izklopljeno) |
| `kljucna_beseda` | Ključne besede ločene s `;` |
| `icon_rows` | Število vrstic ikon (1 ali 2) |
| `avto_predvajaj` | Samodejno predvajaj ob zagonu |

---

## 🤝 Prispevanje

Pull requesti so dobrodošli! Za večje spremembe najprej odpri issue.

1. Fork repozitorija
2. Ustvari feature branch: `git checkout -b feature/nova-funkcija`
3. Commit: `git commit -m 'Dodaj novo funkcijo'`
4. Push: `git push origin feature/nova-funkcija`
5. Odpri Pull Request

---

## 📄 Licenca

MIT License — glej [LICENSE](LICENSE)

---

## 🙏 Zahvale

- [mpv](https://mpv.io/) — medijski predvajalnik
- [Pillow](https://python-pillow.org/) — obdelava slik
- Python tkinter — GUI ogrodje

---

## 🌍 Iskanje postaj prek RapidAPI

Radiola podpira samodejno iskanje in dodajanje postaj iz baze **90.000+ radijskih postaj iz 200+ držav** prek [50K Radio Stations API](https://rapidapi.com/herihermwn/api/50k-radio-stations).

### Namestitev
1. Registriraj se brezplačno na [rapidapi.com](https://rapidapi.com)
2. Poišči **"50K Radio Stations"** in klikni **Subscribe** (Free plan: 500 zahtev/mesec)
3. Kopiraj API ključ
4. V Radioli: **Nastavitve → RapidAPI ključ…** → vstavi ključ

### Uporaba
1. **Uredi postaje → 🌍 Poišči postaje**
2. Izberi državo in/ali žanr
3. Opcijsko: vpiši iskalni niz (ime postaje)
4. Klikni **🔍 Poišči**
5. Izberi postaje (Ctrl+klik za več) → **✓ Dodaj izbrane**

Ikone se prenesejo samodejno ob dodajanju.

### Cenik
| Plan | Zahteve/mesec | Cena |
|---|---|---|
| Free | 500 | $0 |
| Basic | 10.000 | ~$10/mes |
| Pro | 100.000 | ~$50/mes |

Za osebno uporabo je **brezplačni plan povsem dovolj** (50 postaj/iskanje = 10 iskanj/mesec).

---

## 🆓 Radio Browser (brez registracije)

Poleg RapidAPI Radiola podpira tudi **[Radio Browser](https://www.radio-browser.info/)** — odprtokodno bazo ~35.000 aktivnih postaj, ki ne zahteva registracije ali API ključa.

| | Radio Browser | RapidAPI |
|---|---|---|
| Registracija | ❌ ni | ✅ brezplačna |
| API ključ | ❌ ni | ✅ brezplačen |
| Postaje | ~35.000 | 90.000+ |
| Omejitev zahtev | ❌ ni | 500/mesec free |
| Preverjanje streamov | ✅ dnevno | ❌ |
| Razvrsti po glasovih | ✅ | ❌ |

Oba vira sta dostopna v enem dialogu z zavihkoma **🆓 Radio Browser** in **🔑 RapidAPI**.

---

## 📦 Pakiranje v EXE / AppImage

### Hitri start

```bash
# Namesti PyInstaller
pip install pyinstaller

# Zaženi build skript
python3 build.py
```

| Platforma | Rezultat | Distribucija |
|---|---|---|
| 🪟 Windows | `dist/Radiola/Radiola.exe` | Zapakiraj v ZIP |
| 🐧 Linux | `dist/Radiola/Radiola` + `*.AppImage` | tar.gz ali AppImage |
| 🍎 macOS | `dist/Radiola.app` | tar.gz ali DMG |

### GitHub Actions (samodejni build)

Pri vsakem `git tag v*` GitHub samodejno zgradi za vse platforme:

```bash
git tag v1.4.0
git push origin --tags
# → GitHub Release se ustvari samodejno
```

Podroben vodič: [docs/packaging_guide.html](docs/packaging_guide.html)
