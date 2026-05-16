#!/usr/bin/env python3
"""
scraper_slo_radio.py  –  Pobere SLO radijske postaje z ikon in stream URL-jev
Strani: siradio.si  +  radijskepostaje.si  (več podstrani)

Rezultat:
  stations_scraped.json   – postaje v formatu Radiola (ime, url, ikona base64, kw)
  stations_scraped.txt    – izvoz v formatu Radiola txt (ime = url = base64)

Namestitev odvisnosti (enkrat):
  pip install requests beautifulsoup4 pillow  --break-system-packages
"""

import requests, base64, io, json, time, re, sys
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import Image

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Radiola/1.3"})
TIMEOUT = 10
STORE_SZ = 225   # px – enako kot Radiola

# ─────────────────────────── helpers ─────────────────────────────────────────

def pravilna_rgba(img):
    if img.mode == "P":
        img = img.convert("RGBA") if "transparency" in img.info else img.convert("RGB").convert("RGBA")
    elif img.mode not in ("RGBA",):
        img = img.convert("RGBA")
    return img

def ikona_url_v_b64(url, referer=""):
    """Prenese sliko z URL-ja in jo pretvori v base64 PNG 225×225."""
    try:
        h = {"Referer": referer} if referer else {}
        r = SESSION.get(url, timeout=TIMEOUT, headers=h)
        r.raise_for_status()
        img = pravilna_rgba(Image.open(io.BytesIO(r.content)))
        w, h_ = img.size
        mn = min(w, h_)
        img = img.crop(((w-mn)//2, (h_-mn)//2, (w+mn)//2, (h_+mn)//2))
        img = img.resize((STORE_SZ, STORE_SZ), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print(f"    ⚠  ikona napaka {url}: {e}")
        return ""

def je_stream_url(url):
    """Preveri ali je URL verjetno audio stream."""
    if not url:
        return False
    low = url.lower()
    # Skupni stream formati / poti
    if any(x in low for x in [".mp3", ".ogg", ".aac", ".m3u", ".pls", ".m3u8",
                                "/stream", "/live", "/radio", "/audio", "/listen",
                                "icecast", "shoutcast", "8000", "8080", "8443",
                                "stream.", "listen.", "radio."]):
        return True
    return False

def get_soup(url):
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser"), r.url
    except Exception as e:
        print(f"  ✗  Ne morem naložiti {url}: {e}")
        return None, url

def najdi_stream_v_html(soup, base_url):
    """Išče stream URL-je v HTML (audio tag, source, data atributi, JS)."""
    candidates = []

    # <audio src=...> ali <source src=...>
    for tag in soup.find_all(["audio", "source"]):
        src = tag.get("src","")
        if src: candidates.append(urljoin(base_url, src))

    # data-* atributi ki vsebujejo URL
    for tag in soup.find_all(True):
        for attr, val in tag.attrs.items():
            if isinstance(val, str) and "http" in val and je_stream_url(val):
                candidates.append(val)

    # JS vsebina – išče stringe podobne stream URL-jem
    for script in soup.find_all("script"):
        text = script.string or ""
        # Išče http://...  ali //... ki vsebuje stream ključne besede
        for m in re.findall(r'["\']((https?:)?//[^"\'<>\s]{8,})["\']', text):
            u = m[0]
            if not u.startswith("http"):
                u = "https:" + u
            if je_stream_url(u):
                candidates.append(u)

    # Odstrani duplikate, ohrani vrstni red
    seen = set()
    result = []
    for u in candidates:
        if u not in seen:
            seen.add(u); result.append(u)
    return result

# ─────────────────────────── siradio.si ──────────────────────────────────────

def scrape_siradio():
    """
    siradio.si prikazuje postaje z embed playerji.
    Poskušamo pobrati: ime, ikono, stream URL.
    """
    BASE = "https://siradio.si"
    print(f"\n{'='*60}")
    print(f"  Scraping: {BASE}")
    print('='*60)

    postaje = []
    soup, real_url = get_soup(BASE)
    if not soup:
        return postaje

    # Poišči vse elemente ki vsebujejo postaje
    # Tipična struktura: kartica z imenom + logo sliko + stream linkom
    cards = (
        soup.find_all(class_=re.compile(r"radio|station|card|item|postaj", re.I)) or
        soup.find_all("article") or
        soup.find_all("li", class_=True)
    )

    # Fallback: vse slike z linki poleg njih
    if not cards:
        print("  Ni našel kartic, iščem slike+linke...")
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src","")
            if not src or "logo" not in src.lower() and "icon" not in src.lower():
                continue
            # Ime: alt ali bližnji tekst
            ime = img_tag.get("alt","").strip()
            if not ime:
                parent = img_tag.find_parent(["a","div","li","article"])
                ime = parent.get_text(strip=True)[:40] if parent else ""
            if not ime:
                continue
            # Stream: poišči v bližnjem HTML
            parent = img_tag.find_parent(["div","li","article","section"])
            streams = najdi_stream_v_html(BeautifulSoup(str(parent),"html.parser"), BASE) if parent else []
            stream = streams[0] if streams else ""
            # Ikona
            ico_url = urljoin(BASE, src)
            print(f"  + {ime[:30]:<30}  stream={'✓' if stream else '✗'}  ikona={'✓' if src else '✗'}")
            b64 = ikona_url_v_b64(ico_url, BASE) if src else ""
            postaje.append({"ime": ime, "url": stream, "ikona": b64, "kw": ""})
            time.sleep(0.3)
    else:
        for card in cards:
            ime = ""
            # Poišči ime
            for tag in card.find_all(["h1","h2","h3","h4","h5","span","p","div"]):
                t = tag.get_text(strip=True)
                if 3 < len(t) < 60 and not t.startswith("http"):
                    ime = t; break
            if not ime:
                ime = card.get_text(strip=True)[:40]
            if not ime:
                continue

            # Ikona
            img_tag = card.find("img")
            ico_url = urljoin(BASE, img_tag["src"]) if img_tag and img_tag.get("src") else ""

            # Stream
            streams = najdi_stream_v_html(card, BASE)
            # Tudi v href linkih
            for a in card.find_all("a", href=True):
                href = urljoin(BASE, a["href"])
                if je_stream_url(href):
                    streams.insert(0, href)
            stream = streams[0] if streams else ""

            print(f"  + {ime[:30]:<30}  stream={'✓' if stream else '✗'}  ikona={'✓' if ico_url else '✗'}")
            b64 = ikona_url_v_b64(ico_url, BASE) if ico_url else ""
            postaje.append({"ime": ime, "url": stream, "ikona": b64, "kw": ""})
            time.sleep(0.3)

    print(f"  → {len(postaje)} postaj s siradio.si")
    return postaje

# ─────────────────────────── radijskepostaje.si ──────────────────────────────

def scrape_radijskepostaje():
    """
    radijskepostaje.si ima več strani (ugotovi koliko in jih obdela vse).
    """
    BASE = "https://radijskepostaje.si"
    print(f"\n{'='*60}")
    print(f"  Scraping: {BASE}  (vse strani)")
    print('='*60)

    postaje = []

    # Ugotovi število strani – preizkusi /stran/1 .. /stran/10 ali ?page=
    stran_urls = []

    # Preizkusi različne paginacijske formate
    paginacija_formati = [
        BASE + "/stran/{n}",
        BASE + "/page/{n}",
        BASE + "/?page={n}",
        BASE + "/?p={n}",
    ]

    # Najprej naloži glavno stran in poišči paginator
    soup0, _ = get_soup(BASE)
    if soup0:
        # Poišči max stran
        max_stran = 1
        for a in soup0.find_all("a", href=True):
            href = a["href"]
            for fmt in [r"/stran/(\d+)", r"/page/(\d+)", r"page=(\d+)", r"p=(\d+)"]:
                m = re.search(fmt, href)
                if m:
                    n = int(m.group(1))
                    if n > max_stran:
                        max_stran = n

        print(f"  Našel {max_stran} strani")

        if max_stran == 1:
            # Poskusi različne formate
            for fmt in paginacija_formati:
                test_url = fmt.format(n=2)
                try:
                    r = SESSION.head(test_url, timeout=5)
                    if r.status_code == 200:
                        # Štej strani
                        for n in range(2, 20):
                            url = fmt.format(n=n)
                            r2 = SESSION.head(url, timeout=5)
                            if r2.status_code != 200:
                                max_stran = n - 1; break
                            max_stran = n
                        print(f"  Format: {fmt}  →  {max_stran} strani")
                        stran_urls = [fmt.format(n=n) for n in range(1, max_stran+1)]
                        break
                except: pass

        if not stran_urls:
            stran_urls = [BASE] + [BASE + f"/stran/{n}" for n in range(2, max_stran+1)]
    else:
        stran_urls = [BASE]

    # Scrape vsake strani
    for page_url in stran_urls:
        print(f"\n  Stran: {page_url}")
        soup, real_url = get_soup(page_url)
        if not soup:
            continue

        # Poišči kartice postaj
        cards = (
            soup.find_all(class_=re.compile(r"radio|station|card|postaj|entry", re.I)) or
            soup.find_all("article") or
            []
        )

        if not cards:
            # Fallback: vse slike
            cards_temp = []
            for img in soup.find_all("img"):
                p = img.find_parent(["div","li","article","section"])
                if p and p not in cards_temp:
                    cards_temp.append(p)
            cards = cards_temp

        for card in cards:
            # Ime
            ime = ""
            for tag in card.find_all(["h1","h2","h3","h4","h5","strong","span"]):
                t = tag.get_text(strip=True)
                if 2 < len(t) < 60 and not t.startswith("http"):
                    ime = t; break
            if not ime:
                ime = card.get_text(strip=True)[:40].split("\n")[0].strip()
            if not ime or len(ime) < 2:
                continue

            # Ikona
            img_tag = card.find("img")
            ico_url = ""
            if img_tag:
                src = img_tag.get("src","") or img_tag.get("data-src","")
                if src:
                    ico_url = urljoin(page_url, src)

            # Stream – v kartici ali v href
            streams = najdi_stream_v_html(card, page_url)
            for a in card.find_all("a", href=True):
                href = urljoin(page_url, a["href"])
                if je_stream_url(href):
                    streams.insert(0, href)
            stream = streams[0] if streams else ""

            # Če ni streama v kartici, odpri detail stran
            if not stream:
                detail_a = card.find("a", href=True)
                if detail_a:
                    detail_url = urljoin(page_url, detail_a["href"])
                    if detail_url != page_url and BASE in detail_url:
                        try:
                            ds, _ = get_soup(detail_url)
                            if ds:
                                streams2 = najdi_stream_v_html(ds, detail_url)
                                if streams2:
                                    stream = streams2[0]
                                    print(f"    detail stream: {stream[:60]}")
                        except: pass
                        time.sleep(0.2)

            print(f"  + {ime[:30]:<30}  stream={'✓' if stream else '✗'}  ikona={'✓' if ico_url else '✗'}")
            b64 = ikona_url_v_b64(ico_url, page_url) if ico_url else ""
            postaje.append({"ime": ime, "url": stream, "ikona": b64, "kw": ""})
            time.sleep(0.3)

    print(f"\n  → {len(postaje)} postaj z radijskepostaje.si")
    return postaje

# ─────────────────────────── deduplikacija ───────────────────────────────────

def dedupliciraj(postaje):
    """Odstrani duplikate po URL-ju (ohrani prvi), in duplikate po imenu."""
    videni_url = set()
    videna_imena = set()
    rezultat = []
    for p in postaje:
        url_key = p["url"].strip().lower()
        ime_key = p["ime"].strip().lower()
        # Preskoci prazna ali duplikat
        if ime_key in videna_imena:
            continue
        if url_key and url_key in videni_url:
            continue
        videna_imena.add(ime_key)
        if url_key:
            videni_url.add(url_key)
        rezultat.append(p)
    return rezultat

# ─────────────────────────── shrani ──────────────────────────────────────────

def shrani(postaje, json_file="stations_scraped.json", txt_file="stations_scraped.txt"):
    # JSON (Radiola format)
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(postaje, f, ensure_ascii=False, indent=2)
    print(f"\n  ✓  Shranjeno {len(postaje)} postaj → {json_file}")

    # TXT (Radiola uvoz format: Ime = URL = base64)
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("# Radiola stations export – scraper_slo_radio.py\n")
        f.write("# Format: Ime = URL = base64_ikona\n\n")
        for p in postaje:
            line = f"{p['ime']} = {p['url']}"
            if p.get("ikona"):
                line += f" = {p['ikona']}"
            f.write(line + "\n")
    print(f"  ✓  Shranjeno → {txt_file}")

# ─────────────────────────── main ────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Radiola – SLO Radio Scraper")
    print("  Scraping: siradio.si + radijskepostaje.si")
    print("=" * 60)

    vse = []

    try:
        vse += scrape_siradio()
    except Exception as e:
        print(f"\n  ✗  siradio.si napaka: {e}")

    try:
        vse += scrape_radijskepostaje()
    except Exception as e:
        print(f"\n  ✗  radijskepostaje.si napaka: {e}")

    if not vse:
        print("\n  ⚠  Ni bilo mogoče pobrati nobene postaje.")
        print("     Možno: spremenjena struktura strani, ali blokiran dostop.")
        sys.exit(1)

    print(f"\n  Skupaj pred deduplikacijo: {len(vse)}")
    vse = dedupliciraj(vse)
    print(f"  Po deduplikaciji: {len(vse)}")

    shrani(vse)

    # Statistika
    z_ikono  = sum(1 for p in vse if p.get("ikona"))
    z_url    = sum(1 for p in vse if p.get("url"))
    brez_url = [p["ime"] for p in vse if not p.get("url")]

    print(f"\n  Statistika:")
    print(f"    Z ikono:    {z_ikono}/{len(vse)}")
    print(f"    Z URL:      {z_url}/{len(vse)}")
    if brez_url:
        print(f"    Brez URL ({len(brez_url)}):")
        for ime in brez_url[:10]:
            print(f"      – {ime}")
        if len(brez_url) > 10:
            print(f"      ... in še {len(brez_url)-10}")

    print("\n  Uvozi stations_scraped.txt v Radiola:")
    print("  Uredi postaje → 📂 Uvozi .txt")
    print("\nKonec.\n")

if __name__ == "__main__":
    main()
