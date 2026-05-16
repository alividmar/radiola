# Changelog

All notable changes are documented here.  
Format: [Semantic Versioning](https://semver.org/)

---

## [1.2.0] – 2025

### Added
- Vertikalna drsnika glasnosti (🔊) in dviga (🎙) z barvno kljukico
- Scroll kolesa na drsniku glasnosti = sprememba glasnosti ±2%
- Multi-select v urejevalniku (Ctrl+klik, Shift+klik, Ctrl+A, Delete)
- Drag & drop premikanje postaj v urejevalniku
- Dialog za uvoz: Dodaj / Zamenjaj obstoječe
- Dialog za izvoz: Samo postaje (berljivo) / Z ikonami (base64)
- Iskanje podvojenih postaj z možnostjo samodejnega brisanja
- Mapa `ICONS/` za lokalne ikone s predogledom v brskalniku
- Absolutna glasnost pri govoru (kw_glasnost v nastavitvah)
- Navodila v slovenščini in angleščini (HTML)

### Changed
- Ikone postaj so zdaj na dnu okna, Play/Stop/Timer nad njimi
- Postavitev: info zgoraj, ikona predvajane postaje desno
- Drsnika glasnosti in dviga sta vertikalna, eden zraven drugega
- Play/Stop gumba sta manjša
- "Utišaj pred izklopom" je desno od × gumba timerja

### Fixed
- Popravek pokvarjenih base64 zapisov ikon (artefakt uvoza)
- Pravilna konverzija palette (P mode) PNG slik
- Ikone v nizki ločljivosti (36px) zamenjane s 225px pri novem uvozu

---

## [1.1.0] – 2025

### Added
- Lasten brskalnik ikon s predogledom (namesto sistemskega file dialoga)
- Predogled ikone v urejevalniku postaj
- Samodejni prenos ikon (favicon scraping)
- Zaobljeni koti na gumbih postaj
- Skaliranje okna (resizable)
- Delno ujemanje ključnih besed (substring, ločene s ;)
- Nastavitev zadnje mape v brskalniku ikon

### Changed
- Ikone postaj shranjene v 225×225 px (prej 36px)
- Gumbi postaj: ikona čez cel gumb, ime pod njim

---

## [1.0.0] – 2025

### Initial release
- Predvajanje internet radio postaj
- Urejevalnik postaj z uvozom/izvozom
- Samodejni dvig glasnosti pri govoru
- Timer za izklop
- Svetla/temna tema
- Slovenski in angleški vmesnik

---

## [1.3.0] – 2025

### Added
- **🌍 RapidAPI integracija** — iskanje 90.000+ postaj iz 200+ držav
  - Filter po državi (40+ držav v dropdownu)
  - Filter po žanru (28 žanrov)
  - Iskanje po imenu
  - Multi-select z Ctrl+klik
  - Predogled ikone in stream URL-ja ob izbiri
  - Samodejni prenos ikon ob dodajanju
- **RapidAPI ključ dialog** (Nastavitve → RapidAPI ključ…)
  - Prikaži/skrij ključ
  - Direktna povezava do RapidAPI strani

### Changed
- Scroll kolesa miške za glasnost deluje samo ko je miška nad drsnikom

---

## [1.4.0] – 2025

### Added
- **🆓 Radio Browser integracija** — ~35.000 postaj, brez registracije, brez API ključa
  - Iskanje po državi, žanru in imenu
  - Razvrsti po glasovih, priljubljenosti, imenu ali bitratu
  - Filter "Samo aktivne" (preverja delovanje streamov)
  - Prikaz glasov skupnosti (♥)
- **Zavihka v iskalnem dialogu** — Radio Browser | RapidAPI v enem oknu
- Ikone se prenašajo v ozadju (UI ne zamrzne)
- Detajlni predogled postaje ob dvojnem kliku (vir, bitrate, glasovi, URL)
