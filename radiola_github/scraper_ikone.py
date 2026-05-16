#!/usr/bin/env python3
"""
scraper_ikone.py  –  Pobere SAMO ikone SLO radijskih postaj
============================================================
Bere obstoječ stations.json, doda/popravi ikone iz spleta.

Strategija (v tem vrstnem redu):
  1. Google Favicon API  (hiter, 64px)
  2. ICY header icy-url  → favicon domene postaje
  3. Scraping HTML strani postaje (og:image, apple-touch-icon, ikona v <img>)

Rezultat:
  stations_z_ikonami.json   – posodobljen stations.json z ikonami

Namestitev (enkrat):
  pip install requests beautifulsoup4 pillow  --break-system-packages

Poganjanje:
  python3 scraper_ikone.py
  python3 scraper_ikone.py --vhod moj_stations.json --izhod rezultat.json
  python3 scraper_ikone.py --samo-brez-ikone   # preskoči postaje ki že imajo ikono
  python3 scraper_ikone.py --postaja "Val 202" # samo ena postaja (za test)
"""

import sys, os, json, base64, io, re, time, argparse
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image

# ── Konfiguracija ─────────────────────────────────────────────────────────────

STORE_SZ  = 225      # velikost shranjene ikone (px, kvadrat)
TIMEOUT   = 8        # sekunde za HTTP zahteve
ZAMIK     = 0.4      # sekunde med zahtevami (ne preobremenimo strežnikov)
MIN_PX    = 16       # minimalna velikost ikone (manjše zavržemo)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
})

# ── Helpers ───────────────────────────────────────────────────────────────────

def pravilna_rgba(img):
    """Pretvori PIL sliko v čisto RGBA."""
    if img.mode == "P":
        img = img.convert("RGBA") if "transparency" in img.info else img.convert("RGB").convert("RGBA")
    elif img.mode not in ("RGBA",):
        img = img.convert("RGBA")
    return img

def kvadrat_resize(img, vel=STORE_SZ):
    """Obreži na kvadrat in povečaj/pomanjšaj na vel×vel."""
    w, h = img.size
    mn = min(w, h)
    img = img.crop(((w-mn)//2, (h-mn)//2, (w+mn)//2, (h+mn)//2))
    return img.resize((vel, vel), Image.LANCZOS)

def pil_v_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def prenesi_sliko(url, referer="", min_px=MIN_PX):
    """Prenese sliko z URL-ja → PIL Image ali None."""
    try:
        h = {}
        if referer: h["Referer"] = referer
        r = SESSION.get(url, timeout=TIMEOUT, headers=h, stream=True)
        r.raise_for_status()
        ct = r.headers.get("Content-Type","")
        # Zavrni ne-slike (HTML, JSON...)
        if "html" in ct or "json" in ct or "text" in ct:
            return None
        data = r.content
        if len(data) < 100:   # prazno
            return None
        img = pravilna_rgba(Image.open(io.BytesIO(data)))
        # Zavrni premajhne (privzeta Google ikona je 16x16)
        if img.size[0] < min_px or img.size[1] < min_px:
            return None
        return img
    except Exception:
        return None

def domena(url):
    """Vrne domeno iz URL-ja."""
    try:
        p = urllib.parse.urlparse(url if "://" in url else "http://" + url)
        return p.netloc or p.path.split("/")[0]
    except Exception:
        return ""

def absolutni_url(url, base):
    """Pretvori relativni URL v absolutni."""
    try:
        return urllib.parse.urljoin(base, url)
    except Exception:
        return url

# ── Strategije pridobivanja ikon ──────────────────────────────────────────────

def strategija_google_favicon(stream_url, postaja_url=""):
    """Google Favicon API – hiter, deluje za večino domen."""
    for url in [postaja_url, stream_url]:
        d = domena(url)
        if not d or d.startswith("mp3.") or d.startswith("stream."):
            # Stream-only domene nimajo logojev
            continue
        fav_url = f"https://www.google.com/s2/favicons?domain={d}&sz=128"
        img = prenesi_sliko(fav_url, min_px=32)  # Google privzeto = 16px (ni logo)
        if img and img.size[0] >= 32:
            return img
    return None

def strategija_icy_header(stream_url):
    """Prebere ICY header iz streama → dobi domeno postaje → favicon."""
    try:
        r = SESSION.get(stream_url,
                        headers={"Icy-MetaData": "1"},
                        stream=True, timeout=5)
        icy_url = r.headers.get("icy-url", "").strip()
        r.close()
        if not icy_url:
            return None
        d = domena(icy_url)
        if not d:
            return None
        # Poskusi favicon na domeni postaje
        for pot in ["/apple-touch-icon.png", "/favicon.png", "/favicon.ico",
                    "/logo.png", "/images/logo.png"]:
            img = prenesi_sliko(f"https://{d}{pot}", min_px=32)
            if img:
                return img
        # Google Favicon za to domeno
        img = prenesi_sliko(
            f"https://www.google.com/s2/favicons?domain={d}&sz=128", min_px=32)
        return img
    except Exception:
        return None

def strategija_html_scraping(postaja_url, stream_url=""):
    """Scrape HTML strani postaje – poišče og:image, apple-touch-icon, logo."""
    url = postaja_url or stream_url
    if not url or not url.startswith("http"):
        return None
    # Postaj stream URL-ji niso HTML
    if any(x in url.lower() for x in [":8000", ":8080", ".mp3", ".ogg", ".aac", ".m3u"]):
        return None
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        kandidati = []

        # og:image
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            kandidati.append(absolutni_url(og["content"], url))

        # apple-touch-icon
        for rel in ["apple-touch-icon", "apple-touch-icon-precomposed"]:
            tag = soup.find("link", rel=re.compile(rel, re.I))
            if tag and tag.get("href"):
                kandidati.append(absolutni_url(tag["href"], url))

        # Navadni favicon
        fav = soup.find("link", rel=re.compile(r"icon", re.I))
        if fav and fav.get("href"):
            kandidati.append(absolutni_url(fav["href"], url))

        # Slike z "logo" v src/alt/class
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src","") or img_tag.get("data-src","")
            alt = img_tag.get("alt","").lower()
            cls = " ".join(img_tag.get("class",[])).lower()
            if src and ("logo" in src.lower() or "logo" in alt or "logo" in cls):
                kandidati.append(absolutni_url(src, url))

        # Preizkusi kandidate
        for c_url in kandidati:
            if not c_url:
                continue
            img = prenesi_sliko(c_url, url, min_px=32)
            if img:
                return img

    except Exception:
        pass
    return None

# ── Pridobi ikono za eno postajo ──────────────────────────────────────────────

def pridobi_ikono(postaja, vsi_url_ji=None):
    """
    Poskusi vse strategije in vrne PIL Image ali None.
    postaja = {"ime": ..., "url": ..., "ikona": ...}
    """
    ime       = postaja.get("ime", "?")
    stream    = postaja.get("url", "")
    # Postaja URL (ne stream) – morda je v prihodnje shranjen posebej
    web_url   = postaja.get("web_url", "")

    print(f"  → {ime[:35]:<35}", end=" ", flush=True)

    # 1. HTML scraping (najboljša kakovost)
    if web_url:
        img = strategija_html_scraping(web_url, stream)
        if img:
            print("✓ html")
            return img

    # 2. Google Favicon (hiter)
    img = strategija_google_favicon(stream, web_url)
    if img:
        print("✓ google")
        return img

    # 3. ICY header → domain favicon
    if stream and stream.startswith("http"):
        img = strategija_icy_header(stream)
        if img:
            print("✓ icy")
            return img

    print("✗ ni ikone")
    return None

# ── Popravi obstoječe ikone ───────────────────────────────────────────────────

def ocisti_b64(b64):
    """Popravi morebitne artefakte v b64 polju (npr. 'timestamp = data:...')."""
    if not b64:
        return ""
    m = re.search(r'(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)', b64)
    if m:
        return m.group(1)
    stripped = b64.strip()
    if re.match(r'^[A-Za-z0-9+/=]+$', stripped):
        return stripped
    return ""

def validna_ikona(b64):
    """Vrne True če je b64 veljavna slika."""
    if not b64:
        return False
    try:
        data = b64.split(",",1)[1] if b64.startswith("data:") else b64
        img = Image.open(io.BytesIO(base64.b64decode(data)))
        return img.size[0] >= MIN_PX
    except Exception:
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Scraper ikon za Radiola")
    ap.add_argument("--vhod",  default="stations.json",       help="Vhodni JSON")
    ap.add_argument("--izhod", default="stations_z_ikonami.json", help="Izhodni JSON")
    ap.add_argument("--samo-brez-ikone", action="store_true",
                    help="Preskoči postaje ki že imajo veljavno ikono")
    ap.add_argument("--postaja", default="",
                    help="Obdelaj samo eno postajo (po imenu, za test)")
    ap.add_argument("--popravi-samo", action="store_true",
                    help="Samo popravi pokvarjene b64 zapise, ne scrapa novih")
    args = ap.parse_args()

    if not os.path.isfile(args.vhod):
        print(f"✗ Datoteka ne obstaja: {args.vhod}")
        sys.exit(1)

    with open(args.vhod, encoding="utf-8") as f:
        postaje = json.load(f)

    print(f"Naloženih {len(postaje)} postaj iz {args.vhod}\n")

    # Popravi pokvarjene b64 zapise
    popravljenih = 0
    for p in postaje:
        b64 = p.get("ikona","")
        if not b64:
            continue
        ociscen = ocisti_b64(b64)
        if ociscen != b64:
            p["ikona"] = ociscen
            popravljenih += 1
    if popravljenih:
        print(f"Popravljenih pokvarjenih b64 zapisov: {popravljenih}\n")

    if args.popravi_samo:
        with open(args.izhod, "w", encoding="utf-8") as f:
            json.dump(postaje, f, ensure_ascii=False, indent=2)
        print(f"Shranjeno (samo popravek): {args.izhod}")
        return

    # Filter po imenu
    if args.postaja:
        za_obdelavo = [p for p in postaje if args.postaja.lower() in p.get("ime","").lower()]
        print(f"Filtrirano na: {[p['ime'] for p in za_obdelavo]}\n")
    else:
        za_obdelavo = postaje

    # Statistika pred
    z_veljavno   = sum(1 for p in postaje if validna_ikona(ocisti_b64(p.get("ikona",""))))
    brez_ikone   = sum(1 for p in postaje if not p.get("ikona",""))
    pokvarjenih  = len(postaje) - z_veljavno - brez_ikone
    print(f"Stanje pred scrapingom:")
    print(f"  Z veljavno ikono:  {z_veljavno}")
    print(f"  Pokvarjenih:       {pokvarjenih}")
    print(f"  Brez ikone:        {brez_ikone}")
    print(f"  Za obdelavo:       {len(za_obdelavo)}\n")

    print("Pridobivam ikone...\n")
    pridobljenih = 0
    napak = 0

    for p in za_obdelavo:
        b64_clean = ocisti_b64(p.get("ikona",""))

        # Preskoči če ima veljavno ikono in je izbran --samo-brez-ikone
        if args.samo_brez_ikone and validna_ikona(b64_clean):
            print(f"  ○ {p.get('ime','?')[:35]:<35} (preskoči – že ima ikono)")
            continue

        img = pridobi_ikono(p)
        time.sleep(ZAMIK)

        if img:
            try:
                img = kvadrat_resize(img, STORE_SZ)
                p["ikona"] = pil_v_b64(img)
                pridobljenih += 1
            except Exception as e:
                print(f"    ⚠ Napaka pri shranjevanju: {e}")
                napak += 1
        else:
            # Ohrani staro (popravljeno) ikono če obstaja
            if b64_clean and validna_ikona(b64_clean):
                p["ikona"] = b64_clean
            else:
                p["ikona"] = ""
            if not b64_clean:
                napak += 1

    # Shrani
    with open(args.izhod, "w", encoding="utf-8") as f:
        json.dump(postaje, f, ensure_ascii=False, indent=2)

    # Statistika po
    z_veljavno_po = sum(1 for p in postaje if validna_ikona(p.get("ikona","")))

    print(f"\n{'='*50}")
    print(f"Končano!")
    print(f"  Novih ikon:        {pridobljenih}")
    print(f"  Brez uspeha:       {napak}")
    print(f"  Skupaj z ikono:    {z_veljavno_po}/{len(postaje)}")
    print(f"  Shranjeno:         {args.izhod}")
    print(f"\nKopiraš {args.izhod} → stations.json in zaženeš Radiola.")

if __name__ == "__main__":
    main()
