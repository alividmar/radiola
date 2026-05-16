"""
Radiola – Internet Radio Player with Auto Volume
=================================================
Cross-platform: Linux & Windows
https://github.com/yourusername/radiola

Requirements:
    Linux:   pip install requests pillow  |  sudo apt install mpv
    Windows: pip install requests pillow pycaw comtypes
             + mpv.exe in same folder as radiola.py
"""

import platform, threading, subprocess, time, os, json, base64, io, shutil
import urllib.request, urllib.parse, urllib.error
import tkinter as tk

# requests je opcijski — fallback na urllib
try:
    import requests as _requests_lib
    REQUESTS_OK = True
except ImportError:
    _requests_lib = None
    REQUESTS_OK = False
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont

OS       = platform.system()
VERSION  = "1.2.0"
APP_NAME = "Radiola"

PYCAW_OK = False
if OS == "Windows":
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        PYCAW_OK = True
    except ImportError:
        pass

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
POSTAJE_FILE  = os.path.join(BASE_DIR, "stations.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
ICON_FILE     = os.path.join(BASE_DIR, "radiola_icon.png")

POSTAJE_PRIVZETE = [
    {"ime":"Val 202",         "url":"http://mp3.rtvslo.si:8000/val202","ikona":"","kw":""},
    {"ime":"Radio Slovenija", "url":"http://mp3.rtvslo.si:8000/prvi",  "ikona":"","kw":""},
    {"ime":"ARS",             "url":"http://mp3.rtvslo.si:8000/ars",   "ikona":"","kw":""},
    {"ime":"Radio Koper",     "url":"http://mp3.rtvslo.si:8000/capo",  "ikona":"","kw":""},
    {"ime":"Radio Maribor",   "url":"http://mp3.rtvslo.si:8000/rmb",   "ikona":"","kw":""},
    {"ime":"MMR",             "url":"http://mp3.rtvslo.si:8000/mmr",   "ikona":"","kw":""},
    {"ime":"Radio Koper 2",   "url":"http://mp3.rtvslo.si:8000/rakp",  "ikona":"","kw":""},
    {"ime":"Radio 1",         "url":"http://mp3.rtvslo.si:8000/val202","ikona":"","kw":""},
    {"ime":"Postaja 9",       "url":"","ikona":"","kw":""},
    {"ime":"Postaja 10",      "url":"","ikona":"","kw":""},
    {"ime":"Postaja 11",      "url":"","ikona":"","kw":""},
    {"ime":"Postaja 12",      "url":"","ikona":"","kw":""},
    {"ime":"Postaja 13",      "url":"","ikona":"","kw":""},
    {"ime":"Postaja 14",      "url":"","ikona":"","kw":""},
    {"ime":"Postaja 15",      "url":"","ikona":"","kw":""},
    {"ime":"Postaja 16",      "url":"","ikona":"","kw":""},
]

PREHOD_KORAKI = 15
PREHOD_ZAMIK  = 0.03
BTN_SZ        = 64   # icon button size px  (80% of original 80)
ICON_SZ       = 60   # icon fills full button  (80% of original 76)
ICON_RADIUS   = 8    # zaobljeni koti px
PER_ROW       = 8

# ── i18n ──────────────────────────────────────────────────────────────────────
S = {
"si": dict(
    play="▶  Predvajaj", stop="■  Ustavi",
    station="POSTAJA", now_playing="ZDAJ PREDVAJA",
    volume="Glasnost", boost="Dvig pri govoru",
    keyword="Ključna beseda",
    kw_hint="Več besed loči s podpičjem ;  Zazna DELNO ujemanje (podbesedilo)\nPrimer: govorna;glasovanje;mix — zazna karkoli kar vsebuje to besedo",
    options="⚙  MOŽNOSTI", autoplay="Predvajaj ob zagonu zadnjo postajo",
    timer_lbl="Timer:", timer_start="▶", timer_stop="✕",
    timer_fade="Utišaj pred izklopom (zadnjih 60s)",
    stopped="● Ustavljeno", live="● V ŽIVO  —  ",
    speech_on="🎙  Govor zaznan — glasnost dvignjena",
    m_settings="Nastavitve", m_about="O programu", m_lang="Jezik",
    m_1row="1 vrsta ikon (8)", m_2rows="2 vrsti ikon (16)",
    m_volume="Glasnost in dvig...", m_keyword="Ključna beseda...",
    m_si="🇸🇮  Slovenščina", m_en="🇬🇧  English",
    about_title="O Radiola",
    station_kw="Ključna beseda postaje  (prazno = globalna)",
    no_player="⚠  mpv ni nameščen!",
    player_lbl="▶  predvajalnik: ",
    edit="✏  Uredi postaje",
    export_btn="📤 Izvozi .txt",
    import_btn="📂 Uvozi .txt",
    fetch_ico="🌐 Ikona",
    fetch_all="🌐 Vse ikone",
    radio_search="🌍 Poišči postaje",
    radio_search_title="Poišči radio postaje (RapidAPI)",
    radio_country="Država:",
    radio_genre="Žanr:",
    radio_search_lbl="Iskanje:",
    radio_btn_search="🔍 Poišči",
    radio_btn_add="✓ Dodaj izbrane",
    radio_no_key="Najprej nastavi RapidAPI ključ v:\nNastavitve → RapidAPI ključ…",
    radio_no_results="Ni rezultatov.",
    radio_loading="Iščem...",
    radio_added="Dodanih {n} postaj.",
    rapidapi_menu="RapidAPI ključ…",
    rapidapi_title="RapidAPI ključ",
    rapidapi_hint="Brezplačen ključ: rapidapi.com → 50K Radio Stations → Subscribe\n500 zahtev/mesec brezplačno.",
    rapidapi_save="💾 Shrani ključ",
    rb_tab="🆓 Radio Browser",
    rapid_tab="🔑 RapidAPI",
    rb_info="Brezplačno · Brez registracije · ~35.000 postaj",
    rb_order="Razvrsti:",
    rb_only_active="Samo aktivne",
    rb_votes="glasovi",
    rb_clicks="priljubljenost",
    rb_name_ord="ime",
    rb_bitrate_ord="bitrate",
    fetching="Pridobivam ikone...",
    fetch_done="Ikone posodobljene",
    save="💾 Shrani",
    vol_title="Glasnost in dvig",
    kw_title="Ključna beseda",
    about_text=(
        f"{APP_NAME}  v{VERSION}\n\n"
        "Internetni radijski predvajalnik z avtomatskim\n"
        "dvigom glasnosti pri govoru.\n\n"
        "Licenca: MIT\n"
        "https://github.com/yourusername/radiola\n\n"
        "Predvajalnik: mpv / ffplay / vlc\n"
        "Glasnost: pactl (Linux) · pycaw (Windows)\n\n"
        "Ikone: Google Favicon API + ICY metadata\n"
        "(deluje za postaje z lastno domeno;\n"
        "za RTV SLO streame dodaj ikone ročno)"
    ),
),
"en": dict(
    play="▶  Play", stop="■  Stop",
    station="STATION", now_playing="NOW PLAYING",
    volume="Volume", boost="Speech boost",
    keyword="Trigger keyword",
    kw_hint="Separate with semicolons ;  Partial match (substring)\nExample: talk;vote;mix — detects any title containing these words",
    options="⚙  OPTIONS", autoplay="Autoplay last station on startup",
    timer_lbl="Timer:", timer_start="▶", timer_stop="✕",
    timer_fade="Fade out before stop (last 60s)",
    stopped="● Stopped", live="● LIVE  —  ",
    speech_on="🎙  Speech detected — volume boosted",
    m_settings="Settings", m_about="About", m_lang="Language",
    m_1row="1 row of icons (8)", m_2rows="2 rows of icons (16)",
    m_volume="Volume & boost...", m_keyword="Trigger keyword...",
    m_si="🇸🇮  Slovenščina", m_en="🇬🇧  English",
    about_title=f"About {APP_NAME}",
    station_kw="Station keyword  (empty = use global)",
    no_player="⚠  mpv not found!",
    player_lbl="▶  player: ",
    edit="✏  Edit stations",
    export_btn="📤 Export .txt",
    import_btn="📂 Import .txt",
    fetch_ico="🌐 Icon",
    fetch_all="🌐 All icons",
    radio_search="🌍 Find stations",
    radio_search_title="Find radio stations (RapidAPI)",
    radio_country="Country:",
    radio_genre="Genre:",
    radio_search_lbl="Search:",
    radio_btn_search="🔍 Search",
    radio_btn_add="✓ Add selected",
    radio_no_key="Set your RapidAPI key first:\nSettings → RapidAPI key…",
    radio_no_results="No results.",
    radio_loading="Searching...",
    radio_added="Added {n} stations.",
    rapidapi_menu="RapidAPI key…",
    rapidapi_title="RapidAPI key",
    rapidapi_hint="Free key: rapidapi.com → 50K Radio Stations → Subscribe\n500 requests/month free.",
    rapidapi_save="💾 Save key",
    rb_tab="🆓 Radio Browser",
    rapid_tab="🔑 RapidAPI",
    rb_info="Free · No registration · ~35,000 stations",
    rb_order="Order by:",
    rb_only_active="Active only",
    rb_votes="votes",
    rb_clicks="popularity",
    rb_name_ord="name",
    rb_bitrate_ord="bitrate",
    fetching="Fetching icons...",
    fetch_done="Icons updated",
    save="💾 Save",
    vol_title="Volume & Boost",
    kw_title="Trigger Keyword",
    about_text=(
        f"{APP_NAME}  v{VERSION}\n\n"
        "Internet radio player with automatic\n"
        "volume boost during speech.\n\n"
        "License: MIT\n"
        "https://github.com/yourusername/radiola\n\n"
        "Player: mpv / ffplay / vlc\n"
        "Volume: pactl (Linux) · pycaw (Windows)\n\n"
        "Icons: Google Favicon API + ICY metadata\n"
        "(works for stations with own domain;\n"
        "for RTV SLO streams add icons manually)"
    ),
),
}

# ── Load / Save ───────────────────────────────────────────────────────────────

def nalozi_postaje():
    if os.path.exists(POSTAJE_FILE):
        try:
            d = json.load(open(POSTAJE_FILE, encoding="utf-8"))
            if isinstance(d, list):
                for p in d: p.setdefault("kw",""); p.setdefault("ikona","")
                return d
        except Exception: pass
    return [dict(p) for p in POSTAJE_PRIVZETE]

def shrani_postaje(p):
    json.dump(p, open(POSTAJE_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def nalozi_settings():
    d = dict(glasnost=0.5, dvig=0.30, kw_glasnost=0.0, zadnja_postaja="",
             avto_predvajaj=False, kljucna_beseda="Govorna vsebina",
             jezik="si", icon_rows=2, rapidapi_key="")
    if os.path.exists(SETTINGS_FILE):
        try: d.update(json.load(open(SETTINGS_FILE, encoding="utf-8")))
        except Exception: pass
    return d

def shrani_settings(d):
    json.dump(d, open(SETTINGS_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# ── Theme ─────────────────────────────────────────────────────────────────────

def zazna_temo():
    try:
        if OS == "Linux":
            o = subprocess.check_output(
                ["gsettings","get","org.gnome.desktop.interface","color-scheme"],
                stderr=subprocess.DEVNULL).decode()
            if "dark" in o.lower(): return "dark"
            o2 = subprocess.check_output(
                ["gsettings","get","org.gnome.desktop.interface","gtk-theme"],
                stderr=subprocess.DEVNULL).decode().lower()
            if "dark" in o2: return "dark"
        elif OS == "Windows":
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            v,_ = winreg.QueryValueEx(k,"AppsUseLightTheme")
            return "light" if v else "dark"
    except Exception: pass
    return "light"

def barve(tema):
    if tema == "dark":
        return dict(BG="#1e1e1e",CARD="#2a2a2a",CARD2="#333333",
                    FG="#e8e8e8",MUTED="#888888",ACCENT="#4fc3f7",
                    LIVE="#66bb6a",TROUGH="#555555",BTN_FG="#ffffff",
                    SL_BG="#3a3a3a",SL_FG="#4fc3f7",
                    GREEN="#388e3c",RED="#c62828",ICON_BG="#333333")
    else:
        return dict(BG="#f0f0f0",CARD="#ffffff",CARD2="#e0e0e0",
                    FG="#1a1a1a",MUTED="#666666",ACCENT="#0277bd",
                    LIVE="#2e7d32",TROUGH="#c0c0c0",BTN_FG="#ffffff",
                    SL_BG="#d8d8d8",SL_FG="#0277bd",
                    GREEN="#2e7d32",RED="#c62828",ICON_BG="#e8e8e8")

def fonti():
    b = 11 if OS == "Windows" else 10
    return dict(
        F  = ("TkDefaultFont", b),
        FB = ("TkDefaultFont", b, "bold"),
        FS = ("TkDefaultFont", b),
        FT = ("TkDefaultFont", b+4, "bold"),
        FK = ("TkDefaultFont", b-1),
    )

# ── Icons ─────────────────────────────────────────────────────────────────────

def _pravilna_rgba(img):
    """Pretvori PIL sliko v čisto RGBA - pravilno obravnava palette (P) slike."""
    if img.mode == "P":
        if "transparency" in img.info:
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB").convert("RGBA")
    elif img.mode not in ("RGBA", "RGB"):
        img = img.convert("RGBA")
    elif img.mode == "RGB":
        img = img.convert("RGBA")
    return img

def _ocisti_b64(b64):
    """Popravi morebitne artefakte v b64 stringu (npr. 'timestamp = data:...')."""
    if not b64:
        return ""
    # Poišči pravi data: URI
    import re as _re
    m = _re.search(r'(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)', b64)
    if m:
        return m.group(1).replace("\n","").replace("\r","")
    # Čist base64 brez data: prefiks
    stripped = b64.strip()
    if _re.match(r'^[A-Za-z0-9+/=]+$', stripped):
        return stripped
    return ""

def ikona_iz_base64(b64, vel=(ICON_SZ,ICON_SZ)):
    """Naloži ikono iz base64 stringa ALI poti do datoteke."""
    try:
        b64 = _ocisti_b64(b64) if b64 else ""
        if not b64: return None
        # Pot do datoteke
        if not b64.startswith("data:") and os.path.isfile(b64):
            img=_pravilna_rgba(Image.open(b64))
            img=img.resize(vel,Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        # Base64
        data = b64
        if data.startswith("data:"): data=data.split(",",1)[1]
        img=_pravilna_rgba(Image.open(io.BytesIO(base64.b64decode(data))))
        img=img.resize(vel,Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception: return None

def ikona_inicialke(ime, vel=ICON_SZ, c=None):
    c = c or {}
    bg = c.get("ACCENT","#4fc3f7"); fg = c.get("BTN_FG","#ffffff")
    img  = Image.new("RGBA",(vel,vel),(0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([1,1,vel-1,vel-1], fill=bg)
    crka = (ime[0] if ime else "?").upper()
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",vel//2)
    except Exception:
        try: font = ImageFont.truetype("arial.ttf", vel//2)
        except Exception: font = ImageFont.load_default()
    bb = draw.textbbox((0,0),crka,font=font)
    tw,th = bb[2]-bb[0],bb[3]-bb[1]
    draw.text(((vel-tw)//2,(vel-th)//2-1),crka,fill=fg,font=font)
    return ImageTk.PhotoImage(img)

def ikona_prazna(vel=ICON_SZ, c=None):
    """Siva ikona za prazne placeholder gumbe."""
    c = c or {}
    bg = c.get("CARD2","#cccccc")
    img  = Image.new("RGBA",(vel,vel),(0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([1,1,vel-1,vel-1], fill=bg)
    return ImageTk.PhotoImage(img)

def ikona_v_b64(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# Velikost za shranjevanje ikon v stations.json (visoka ločljivost)
STORE_SZ = 225

def ikona_iz_poti(pot):
    """Naloži ikono iz datoteke in jo pretvori v base64 (shrani v visoki ločljivosti)."""
    try:
        img=_pravilna_rgba(Image.open(pot))
        # Ohrani razmerje, obreži na kvadrat, potem povečaj na STORE_SZ
        w,h=img.size
        mn=min(w,h)
        img=img.crop(((w-mn)//2,(h-mn)//2,(w+mn)//2,(h+mn)//2))
        img=img.resize((STORE_SZ,STORE_SZ),Image.LANCZOS)
        return ikona_v_b64(img)
    except Exception: return ""

# ── Favicon fetch ─────────────────────────────────────────────────────────────

def pridobi_favicon(stream_url, timeout=6):
    """
    Iskanje ikone v tem vrstnem redu:
    1. ICY header 'icy-url' → favicon domene postaje
    2. Google Favicon API z domeno iz stream URL

    OPOMBA: Za RTV SLO streame (mp3.rtvslo.si) Google vrne skupni RTV favicon
    ker vsi delijo isto domeno. Za te postaje dodaj ikone ročno v urejevalniku.
    """
    try:
        import requests as _req
        station_domain = None

        # Korak 1: Preberi ICY header
        try:
            r = _req.get(stream_url, headers={"Icy-MetaData":"1"},
                         stream=True, timeout=timeout)
            icy_url = r.headers.get("icy-url","").strip()
            r.close()
            if icy_url:
                parsed = urllib.parse.urlparse(icy_url)
                station_domain = parsed.netloc or parsed.path
        except Exception: pass

        # Korak 2: Fallback na domeno stream URL
        if not station_domain:
            parsed = urllib.parse.urlparse(stream_url)
            station_domain = parsed.hostname or ""

        if not station_domain:
            return None

        # Google Favicon API
        fav_url = f"https://www.google.com/s2/favicons?domain={station_domain}&sz=64"
        req = urllib.request.Request(fav_url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            # Zavrni privzeto Google ikono (siva, 16x16 → pomeni ni našel)
            if img.size == (16,16):
                return None
            w,h=img.size; mn=min(w,h)
        img=img.crop(((w-mn)//2,(h-mn)//2,(w+mn)//2,(h+mn)//2))
        return img.resize((STORE_SZ,STORE_SZ), Image.LANCZOS)
    except Exception:
        return None

# ── Audio player ──────────────────────────────────────────────────────────────

class PredvajalnikAvdia:
    LINUX   = ["mpv","ffplay","cvlc"]
    WINDOWS = ["mpv",r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"]

    def __init__(self):
        self._proc  = None
        self._lock  = threading.Lock()
        self._player = self._najdi()

    def _najdi(self):
        local = os.path.join(BASE_DIR, "mpv.exe" if OS=="Windows" else "mpv")
        if os.path.isfile(local): return local
        for p in (self.LINUX if OS!="Windows" else self.WINDOWS):
            if os.path.isfile(p) or shutil.which(p): return p
        return None

    @property
    def na_voljo(self): return self._player is not None
    @property
    def ime(self):
        if not self._player: return "ni najden"
        return os.path.basename(self._player).replace(".exe","")

    def _ukaz(self, url):
        p = self.ime.lower()
        if "mpv"    in p: return [self._player,"--no-video","--really-quiet","--cache=yes","--cache-secs=5",url]
        elif "ffplay" in p: return [self._player,"-nodisp","-loglevel","quiet","-i",url]
        else:               return [self._player,"--intf","dummy","--quiet",url]

    def predvajaj(self, url):
        self.ustavi()
        if not self._player: return False
        with self._lock:
            try:
                self._proc = subprocess.Popen(
                    self._ukaz(url),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True)
                return True
            except Exception as e:
                print(f"Player error: {e}"); self._proc=None; return False

    def ustavi(self):
        with self._lock:
            if not self._proc: return
            try:
                if OS == "Windows":
                    subprocess.run(["taskkill","/F","/T","/PID",str(self._proc.pid)],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                else:
                    import signal as _s, os as _o
                    try: _o.killpg(_o.getpgid(self._proc.pid),_s.SIGTERM)
                    except Exception: self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                try: self._proc.kill()
                except Exception: pass
            finally: self._proc = None

# ── Volume ────────────────────────────────────────────────────────────────────

class Glasnost:
    def get(self):
        try: return self._wg() if OS=="Windows" else self._lg()
        except Exception: return 0.5
    def set(self, n):
        n = max(0.0,min(1.0,n))
        try:
            if OS=="Windows": self._ws(n)
            else: self._ls(n)
        except Exception: pass
    def gladko(self, od, do, stop=None):
        for i in range(1,PREHOD_KORAKI+1):
            if stop and stop.is_set(): break
            self.set(od+(do-od)*(i/PREHOD_KORAKI)); time.sleep(PREHOD_ZAMIK)
    def _wg(self):
        if not PYCAW_OK: return 0.5
        d=AudioUtilities.GetSpeakers(); i=d.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
        return cast(i,POINTER(IAudioEndpointVolume)).GetMasterVolumeLevelScalar()
    def _ws(self,n):
        if not PYCAW_OK: return
        d=AudioUtilities.GetSpeakers(); i=d.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
        cast(i,POINTER(IAudioEndpointVolume)).SetMasterVolumeLevelScalar(n,None)
    def _lg(self):
        o=subprocess.check_output(["pactl","get-sink-volume","@DEFAULT_SINK@"],
                                   stderr=subprocess.DEVNULL).decode()
        for t in o.split():
            if t.endswith("%"): return int(t[:-1])/100
        return 0.5
    def _ls(self,n):
        subprocess.run(["pactl","set-sink-volume","@DEFAULT_SINK@",f"{int(n*100)}%"],
                       stderr=subprocess.DEVNULL)

# ── Metadata ──────────────────────────────────────────────────────────────────

class MetadataBralnik:
    def __init__(self,url,cb): self.url=url; self.cb=cb; self._stop=threading.Event()
    def start(self): self._stop.clear(); threading.Thread(target=self._loop,daemon=True).start()
    def stop(self): self._stop.set()
    def _loop(self):
        import requests
        try:
            if not REQUESTS_OK: raise ImportError("namesti requests")
            r=_requests_lib.get(self.url,headers={"Icy-MetaData":"1"},stream=True,timeout=15)
            iv=int(r.headers.get("icy-metaint",0))
            if not iv: return
            while not self._stop.is_set():
                r.raw.read(iv); mb=r.raw.read(1)
                if not mb: break
                dl=ord(mb)*16
                if dl>0:
                    raw=r.raw.read(dl).decode("utf-8",errors="ignore")
                    if "StreamTitle='" in raw:
                        self.cb(raw.split("StreamTitle='")[1].split("';")[0])
        except Exception: pass

# ── Volume / Boost settings dialog ───────────────────────────────────────────

class GlasnostDialog(tk.Toplevel):
    def __init__(self, master, nas, glasnost_obj, c, fnt, lang, on_save):
        super().__init__(master)
        self.title(S[lang]["vol_title"])
        self.configure(bg=c["BG"]); self.resizable(False,False)
        self.nas=nas; self.gl=glasnost_obj; self.c=c; self.fnt=fnt
        self.lang=lang; self.on_save=on_save
        self._build(); self.geometry("340x220"); self.grab_set()

    def _build(self):
        c=self.c; F=self.fnt["F"]; FS=self.fnt["FS"]; FB=self.fnt["FB"]
        pad=dict(padx=16,pady=6)

        # Volume slider
        r1=tk.Frame(self,bg=c["BG"]); r1.pack(fill="x",**pad)
        tk.Label(r1,text=S[self.lang]["volume"],font=F,bg=c["BG"],fg=c["FG"]).pack(side="left")
        self.lbl_gl=tk.Label(r1,text="",font=F,bg=c["BG"],fg=c["ACCENT"])
        self.lbl_gl.pack(side="right")
        self.sl_gl=tk.Scale(self,from_=0,to=100,orient="horizontal",
                            command=self._on_gl,
                            bg=c["SL_BG"],fg=c["SL_FG"],troughcolor=c["TROUGH"],
                            activebackground=c["ACCENT"],highlightbackground=c["BG"],
                            highlightthickness=1,bd=0,sliderrelief="raised",
                            width=16,sliderlength=24,showvalue=False)
        self.sl_gl.pack(fill="x",padx=16)
        try:
            gl=self.gl.get(); self.sl_gl.set(int(gl*100))
            self.lbl_gl.config(text=f"{int(gl*100)}%")
        except Exception:
            self.sl_gl.set(int(self.nas["glasnost"]*100))
            self.lbl_gl.config(text=f"{int(self.nas['glasnost']*100)}%")

        # Boost slider
        r2=tk.Frame(self,bg=c["BG"]); r2.pack(fill="x",**pad)
        tk.Label(r2,text=S[self.lang]["boost"],font=F,bg=c["BG"],fg=c["FG"]).pack(side="left")
        self.lbl_dvig=tk.Label(r2,text="",font=F,bg=c["BG"],fg=c["ACCENT"])
        self.lbl_dvig.pack(side="right")
        self.sl_dvig=tk.Scale(self,from_=0,to=60,orient="horizontal",
                              command=self._on_dvig,
                              bg=c["SL_BG"],fg=c["SL_FG"],troughcolor=c["TROUGH"],
                              activebackground=c["ACCENT"],highlightbackground=c["BG"],
                              highlightthickness=1,bd=0,sliderrelief="raised",
                              width=16,sliderlength=24,showvalue=False)
        self.sl_dvig.pack(fill="x",padx=16)
        self.sl_dvig.set(int(self.nas["dvig"]*100))
        self.lbl_dvig.config(text=f"+{int(self.nas['dvig']*100)}%")

        # ── Glasnost pri ključni besedi ───────────────────────────────────────
        tk.Frame(self,bg=c["BG"],height=1).pack(fill="x",padx=16,pady=(8,0))
        tk.Label(self,text="Glasnost pri govoru  (0 = samo dvig za %):",
                 font=FK,bg=c["BG"],fg=c["FG"]).pack(anchor="w",padx=16,pady=(10,2))
        kw_gl_row=tk.Frame(self,bg=c["BG"]); kw_gl_row.pack(fill="x",padx=16)
        self.var_kw_gl=tk.DoubleVar(value=self.nas.get("kw_glasnost",0.0)*100)
        self.var_kw_gl_lbl=tk.StringVar(
            value=("izklopljeno" if self.nas.get("kw_glasnost",0.0)==0
                   else f"{int(self.nas.get('kw_glasnost',0.0)*100)}%"))
        sl=tk.Scale(kw_gl_row,from_=0,to=100,orient="horizontal",
                    variable=self.var_kw_gl,showvalue=False,length=280,
                    bg=c["BG"],troughcolor=c["CARD2"],highlightthickness=0,
                    command=self._on_kw_gl)
        sl.pack(side="left")
        tk.Label(kw_gl_row,textvariable=self.var_kw_gl_lbl,font=FK,
                 bg=c["BG"],fg=c["FG"],width=12).pack(side="left",padx=(6,0))
        tk.Label(self,
            text="Nastavi absolutno glasnost (npr. 80%) ko zazna govor.\nPusti 0 za relativni dvig z drsnikom v glavnem oknu.",
            font=FK,bg=c["BG"],fg=c["MUTED"],wraplength=360,justify="left"
            ).pack(anchor="w",padx=16,pady=(4,0))

        tk.Button(self,text=S[self.lang]["save"],font=FB,
                  bg=c["ACCENT"],fg=c["BTN_FG"],relief="flat",
                  padx=20,pady=8,cursor="hand2",command=self._save).pack(pady=12)

    def _on_gl(self,val):
        self.gl.set(float(val)/100)
        self.nas["glasnost"]=float(val)/100
        self.lbl_gl.config(text=f"{int(float(val))}%")

    def _on_dvig(self,val):
        self.nas["dvig"]=float(val)/100
        self.lbl_dvig.config(text=f"+{int(float(val))}%")

    def _save(self):
        self.on_save(self.nas); self.destroy()

# ── Keyword dialog ────────────────────────────────────────────────────────────

class KljucnaBeseadaDialog(tk.Toplevel):
    def __init__(self, master, nas, c, fnt, lang, on_save):
        super().__init__(master)
        self.title(S[lang]["kw_title"])
        self.configure(bg=c["BG"]); self.resizable(False,False)
        self.nas=nas; self.c=c; self.fnt=fnt; self.lang=lang; self.on_save=on_save
        self._build(); self.geometry("400x340"); self.grab_set()

    def _build(self):
        c=self.c; F=self.fnt["F"]; FK=self.fnt["FK"]; FB=self.fnt["FB"]
        tk.Label(self,text=S[self.lang]["keyword"],font=FB,
                 bg=c["BG"],fg=c["FG"]).pack(anchor="w",padx=16,pady=(14,4))
        self.ent=tk.Entry(self,font=F,bg=c["CARD"],fg=c["FG"],
                          insertbackground=c["FG"],relief="flat",bd=4)
        self.ent.insert(0,self.nas.get("kljucna_beseda","Govorna vsebina"))
        self.ent.pack(fill="x",padx=16)
        # Hint - razloži delno ujemanje
        hint=S[self.lang]["kw_hint"]
        tk.Label(self,text=hint,font=FK,
                 bg=c["BG"],fg=c["MUTED"],wraplength=360,justify="left"
                 ).pack(anchor="w",padx=16,pady=(6,0))
        # Primer
        primer_frame=tk.Frame(self,bg=c["CARD"],padx=10,pady=6)
        primer_frame.pack(fill="x",padx=16,pady=(8,0))
        primer_naslov="RAZLIČNI IZVAJALCI - Mix za glasovanje za Popevko tedna"
        tk.Label(primer_frame,text="Primer naslova:",font=FK,bg=c["CARD"],fg=c["MUTED"]
                 ).pack(anchor="w")
        tk.Label(primer_frame,text=primer_naslov,font=FK,bg=c["CARD"],fg=c["FG"],
                 wraplength=340,justify="left").pack(anchor="w")
        tk.Label(primer_frame,text="↑ Zazna z besedo: glasovanje  ali  mix",
                 font=FK,bg=c["CARD"],fg=c["LIVE"]).pack(anchor="w",pady=(4,0))
        # ── Glasnost pri ključni besedi ───────────────────────────────────────
        tk.Frame(self,bg=c["BG"],height=1).pack(fill="x",padx=16,pady=(8,0))
        tk.Label(self,text="Glasnost pri govoru  (0 = samo dvig za %):",
                 font=FK,bg=c["BG"],fg=c["FG"]).pack(anchor="w",padx=16,pady=(10,2))
        kw_gl_row=tk.Frame(self,bg=c["BG"]); kw_gl_row.pack(fill="x",padx=16)
        self.var_kw_gl=tk.DoubleVar(value=self.nas.get("kw_glasnost",0.0)*100)
        self.var_kw_gl_lbl=tk.StringVar(
            value=("izklopljeno" if self.nas.get("kw_glasnost",0.0)==0
                   else f"{int(self.nas.get('kw_glasnost',0.0)*100)}%"))
        sl=tk.Scale(kw_gl_row,from_=0,to=100,orient="horizontal",
                    variable=self.var_kw_gl,showvalue=False,length=280,
                    bg=c["BG"],troughcolor=c["CARD2"],highlightthickness=0,
                    command=self._on_kw_gl)
        sl.pack(side="left")
        tk.Label(kw_gl_row,textvariable=self.var_kw_gl_lbl,font=FK,
                 bg=c["BG"],fg=c["FG"],width=12).pack(side="left",padx=(6,0))
        tk.Label(self,
            text="Nastavi absolutno glasnost (npr. 80%) ko zazna govor.\nPusti 0 za relativni dvig z drsnikom v glavnem oknu.",
            font=FK,bg=c["BG"],fg=c["MUTED"],wraplength=360,justify="left"
            ).pack(anchor="w",padx=16,pady=(4,0))

        tk.Button(self,text=S[self.lang]["save"],font=FB,
                  bg=c["ACCENT"],fg=c["BTN_FG"],relief="flat",
                  padx=20,pady=8,cursor="hand2",command=self._save).pack(pady=12)

    def _on_kw_gl(self, val):
        v=float(val)
        self.var_kw_gl_lbl.set("izklopljeno" if v==0 else f"{int(v)}%")

    def _save(self):
        self.nas["kljucna_beseda"]=self.ent.get().strip()
        self.nas["kw_glasnost"]=round(self.var_kw_gl.get()/100,2)
        self.on_save(self.nas); self.destroy()

# ── Brskalnik ikon s predogledom ─────────────────────────────────────────────

class IzbiraIkone(tk.Toplevel):
    """Lasten dialog za izbiro slike z vgrajenim predogledom."""
    THUMB = 80    # velikost sličic v mreži
    COLS  = 5     # stolpci v mreži

    _zadnja_mapa = None   # razredna spremenljivka – si zapomni med klici

    def __init__(self, master, entry_widget, c, fnt):
        super().__init__(master)
        self.title("Izberi ikono")
        self.configure(bg=c["BG"]); self.resizable(True, True)
        self.c=c; self.fnt=fnt; self.entry=entry_widget
        self._pot=tk.StringVar()
        self._slike=[]      # (pot, PhotoImage)
        self._izbrana=None
        self._build()
        self.geometry("660x520")
        self.grab_set()
        # Odpri v zadnji mapi → BASE_DIR (mapa radiola.py) → domača mapa
        if IzbiraIkone._zadnja_mapa and os.path.isdir(IzbiraIkone._zadnja_mapa):
            zacetna = IzbiraIkone._zadnja_mapa
        else:
            # Preveri ICONS podmapa v BASE_DIR
            icons_dir = os.path.join(BASE_DIR, "ICONS")
            if os.path.isdir(icons_dir):
                zacetna = icons_dir
            elif os.path.isdir(BASE_DIR):
                zacetna = BASE_DIR
            else:
                zacetna = os.path.expanduser("~")
        self._nalozi_mapo(zacetna)

    def _build(self):
        c=self.c; FK=self.fnt["FK"]; FB=self.fnt["FB"]

        # ── Vrstica z potjo ─────────────────────────────────────────────────
        top=tk.Frame(self,bg=c["BG"]); top.pack(fill="x",padx=8,pady=(8,4))
        tk.Label(top,text="Mapa:",font=FK,bg=c["BG"],fg=c["FG"]).pack(side="left")
        self._ent_pot=tk.Entry(top,textvariable=self._pot,font=FK,
                               bg=c["CARD"],fg=c["FG"],insertbackground=c["FG"],
                               relief="flat",bd=4)
        self._ent_pot.pack(side="left",fill="x",expand=True,padx=(4,4))
        self._ent_pot.bind("<Return>", lambda e: self._nalozi_mapo(self._pot.get()))
        tk.Button(top,text="🏠",font=FK,bg=c["CARD2"],fg=c["FG"],relief="flat",
                  padx=6,cursor="hand2",
                  command=lambda: self._nalozi_mapo(os.path.expanduser("~"))
                  ).pack(side="left",padx=(0,2))
        tk.Button(top,text="⬆ Gor",font=FK,bg=c["CARD2"],fg=c["FG"],relief="flat",
                  padx=6,cursor="hand2",command=self._gor).pack(side="left")

        # ── Glavno območje: mapa (levo) + predogled (desno) ─────────────────
        mid=tk.Frame(self,bg=c["BG"]); mid.pack(fill="both",expand=True,padx=8,pady=4)

        # Levo: drevo map + datoteke
        levo=tk.Frame(mid,bg=c["BG"]); levo.pack(side="left",fill="both",expand=True)

        # Mreža sličic
        cv_outer=tk.Frame(levo,bg=c["CARD"]); cv_outer.pack(fill="both",expand=True)
        self._canvas=tk.Canvas(cv_outer,bg=c["CARD"],highlightthickness=0)
        sb=tk.Scrollbar(cv_outer,orient="vertical",command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y")
        self._canvas.pack(side="left",fill="both",expand=True)
        self._frm_slike=tk.Frame(self._canvas,bg=c["CARD"])
        self._canvas_win=self._canvas.create_window((0,0),window=self._frm_slike,anchor="nw")
        self._frm_slike.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._canvas_win, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        # Desno: predogled + ime
        desno=tk.Frame(mid,bg=c["BG"],width=160); desno.pack(side="right",fill="y",padx=(8,0))
        desno.pack_propagate(False)
        tk.Label(desno,text="Predogled",font=FK,bg=c["BG"],fg=c["MUTED"]).pack(pady=(0,4))
        self._lbl_prev=tk.Label(desno,bg=c["CARD2"],width=140,height=140,relief="flat")
        self._lbl_prev.pack()
        self._lbl_ime=tk.Label(desno,text="",font=FK,bg=c["BG"],fg=c["FG"],
                                wraplength=150,justify="center")
        self._lbl_ime.pack(pady=(4,0))

        # ── Spodnji gumbi ────────────────────────────────────────────────────
        bot=tk.Frame(self,bg=c["BG"]); bot.pack(fill="x",padx=8,pady=(4,8))
        tk.Button(bot,text="📁 Izberi datoteko",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=8,pady=5,cursor="hand2",
                  command=self._sistemski_dialog).pack(side="left",padx=(0,4))
        tk.Button(bot,text="✓ Potrdi",font=FB,bg=c["GREEN"] if "GREEN" in c else c["ACCENT"],
                  fg=c["BTN_FG"],relief="flat",padx=12,pady=5,cursor="hand2",
                  command=self._potrdi).pack(side="right",padx=(4,0))
        tk.Button(bot,text="Prekliči",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=8,pady=5,cursor="hand2",
                  command=self.destroy).pack(side="right")

    def _nalozi_mapo(self, pot):
        pot=os.path.abspath(os.path.expanduser(pot))
        if not os.path.isdir(pot): return
        self._pot.set(pot)
        IzbiraIkone._zadnja_mapa = pot   # zapomni si
        # Počisti mrežo
        for w in self._frm_slike.winfo_children(): w.destroy()
        self._slike.clear()
        self._izbrana=None

        c=self.c; FK=self.fnt["FK"]
        row=col=0

        # Mape najprej
        try:
            vnosi = sorted(os.scandir(pot), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        for entry in vnosi:
            if entry.is_dir():
                # Mapa gumb
                frm=tk.Frame(self._frm_slike,bg=c["BG"],
                              width=self.THUMB,height=self.THUMB+20)
                frm.grid(row=row,column=col,padx=3,pady=3)
                frm.grid_propagate(False)
                tk.Button(frm,text="📁 "+entry.name[:9],font=FK,
                          bg=c["CARD2"],fg=c["FG"],relief="flat",
                          cursor="hand2",wraplength=self.THUMB-4,justify="center",
                          command=lambda p=entry.path: self._nalozi_mapo(p)
                          ).place(relx=0.5,rely=0.5,anchor="center",
                                   width=self.THUMB-2,height=self.THUMB+16)
                col+=1
                if col>=self.COLS: col=0; row+=1

        # Slike
        IMG_EXT = {".png",".jpg",".jpeg",".ico",".gif",".bmp",".webp"}
        for entry in vnosi:
            if not entry.is_file(): continue
            if os.path.splitext(entry.name)[1].lower() not in IMG_EXT: continue

            frm=tk.Frame(self._frm_slike,bg=c["BG"],
                          width=self.THUMB,height=self.THUMB+20)
            frm.grid(row=row,column=col,padx=3,pady=3)
            frm.grid_propagate(False)

            # Sličica
            ph=None
            try:
                img=_pravilna_rgba(Image.open(entry.path))
                img.thumbnail((self.THUMB-4,self.THUMB-4),Image.LANCZOS)
                ph=ImageTk.PhotoImage(img)
            except Exception:
                pass

            idx=len(self._slike)
            self._slike.append((entry.path, ph))

            btn=tk.Button(frm,image=ph if ph else None,
                          text="" if ph else entry.name[:8],
                          compound="top" if ph else "none",
                          font=FK,bg=c["CARD"],fg=c["FG"],
                          relief="flat",cursor="hand2",bd=0,
                          command=lambda i=idx: self._klik(i))
            if ph: btn.image=ph
            btn.place(relx=0.5,rely=0,anchor="n",width=self.THUMB-2,height=self.THUMB+2)
            # Ime pod sličico
            tk.Label(frm,text=entry.name[:11],font=(self.fnt["FK"][0],7),
                     bg=c["BG"],fg=c["MUTED"],anchor="center"
                     ).place(relx=0.5,rely=1,anchor="s",width=self.THUMB-2)

            col+=1
            if col>=self.COLS: col=0; row+=1

        if not self._slike and col==0 and row==0:
            tk.Label(self._frm_slike,text="Ni slik v tej mapi",
                     font=FK,bg=c["CARD"],fg=c["MUTED"]).grid(pady=20)

        self._canvas.yview_moveto(0)

    def _klik(self, idx):
        """Izbere sliko in pokaže predogled."""
        self._izbrana=idx
        pot, ph = self._slike[idx]
        # Večji predogled (140px)
        try:
            img=_pravilna_rgba(Image.open(pot))
            img.thumbnail((140,140),Image.LANCZOS)
            ph2=ImageTk.PhotoImage(img)
            self._lbl_prev.config(image=ph2); self._lbl_prev._ph=ph2
        except: pass
        self._lbl_ime.config(text=os.path.basename(pot))

    def _gor(self):
        trenutna=self._pot.get()
        starš=os.path.dirname(trenutna)
        if starš != trenutna:
            self._nalozi_mapo(starš)

    def _sistemski_dialog(self):
        """Fallback – standardni sistemski dialog."""
        pot=filedialog.askopenfilename(parent=self,title="Izberi ikono",
            filetypes=[("Slike","*.png *.jpg *.jpeg *.ico *.gif *.bmp *.webp"),("Vse","*.*")])
        if pot:
            self._nalozi_mapo(os.path.dirname(pot))
            # Poišči in izberi to sliko
            for i,(p,_) in enumerate(self._slike):
                if p==pot:
                    self._klik(i); break

    def _potrdi(self):
        if self._izbrana is None:
            messagebox.showwarning("",
                "Izberi sliko s klikom na sličico.",parent=self); return
        pot,_=self._slike[self._izbrana]
        try:
            img=_pravilna_rgba(Image.open(pot))
            w,h=img.size; mn=min(w,h)
            img=img.crop(((w-mn)//2,(h-mn)//2,(w+mn)//2,(h+mn)//2))
            img=img.resize((STORE_SZ,STORE_SZ),Image.LANCZOS)
            buf=io.BytesIO(); img.save(buf,format="PNG")
            b64="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
            self.entry.delete(0,"end"); self.entry.insert(0,b64)
            # Obvesti starš okno da posodobi predogled
            try: self.master._posodobi_prev_ikone(b64)
            except Exception: pass
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Napaka",str(ex),parent=self)

# ── Station editor ────────────────────────────────────────────────────────────



# ── RapidAPI key dialog ───────────────────────────────────────────────────────

class RapidAPIKeyDialog(tk.Toplevel):
    """Dialog za vnos in shranjevanje RapidAPI ključa."""
    def __init__(self, master, nas, c, fnt, lang, on_save):
        super().__init__(master)
        self.title(S[lang]["rapidapi_title"])
        self.configure(bg=c["BG"]); self.resizable(False,False)
        self.nas=nas; self.on_save=on_save
        FK=fnt["FK"]; FB=fnt["FB"]

        tk.Label(self,text="🔑 RapidAPI ključ",font=FB,
                 bg=c["BG"],fg=c["FG"]).pack(padx=20,pady=(16,6))

        self.ent=tk.Entry(self,font=FK,bg=c["CARD"],fg=c["FG"],
                          insertbackground=c["FG"],relief="flat",bd=4,width=48,
                          show="")
        self.ent.insert(0, nas.get("rapidapi_key",""))
        self.ent.pack(padx=20,fill="x")

        # Prikaži/skrij ključ
        self.var_show=tk.BooleanVar(value=False)
        tk.Checkbutton(self,text="Prikaži ključ",variable=self.var_show,
                       bg=c["BG"],fg=c["MUTED"],selectcolor=c["CARD2"],
                       activebackground=c["BG"],font=FK,relief="flat",
                       command=lambda: self.ent.config(
                           show="" if self.var_show.get() else "•")
                       ).pack(anchor="w",padx=20,pady=(2,0))
        self.ent.config(show="•")

        tk.Label(self,text=S[lang]["rapidapi_hint"],font=FK,
                 bg=c["BG"],fg=c["MUTED"],wraplength=380,justify="left"
                 ).pack(padx=20,pady=(10,0))

        # Link
        lnk=tk.Label(self,text="→ rapidapi.com/herihermwn/api/50k-radio-stations",
                     font=FK,bg=c["BG"],fg=c["ACCENT"],cursor="hand2")
        lnk.pack(padx=20,anchor="w")
        lnk.bind("<Button-1>",lambda e:self._odpri_url(
            "https://rapidapi.com/herihermwn/api/50k-radio-stations"))

        tk.Button(self,text=S[lang]["rapidapi_save"],font=FB,
                  bg=c["ACCENT"],fg=c["BTN_FG"],relief="flat",
                  padx=16,pady=7,cursor="hand2",command=self._save
                  ).pack(pady=14)
        self.geometry("420x280")
        self.grab_set()

    def _odpri_url(self,url):
        import webbrowser; webbrowser.open(url)

    def _save(self):
        self.nas["rapidapi_key"]=self.ent.get().strip()
        self.on_save(self.nas); self.destroy()


# ── Radio Iskanje — RapidAPI dialog ──────────────────────────────────────────

# Podatki za dropdown menije
DRZAVE = [
    ("Vse",""), ("Slovenija","SI"), ("Hrvaška","HR"), ("Srbija","RS"),
    ("Avstrija","AT"), ("Italija","IT"), ("Nemčija","DE"), ("Francija","FR"),
    ("Španija","ES"), ("Velika Britanija","GB"), ("ZDA","US"), ("Kanada","CA"),
    ("Avstralija","AU"), ("Japonska","JP"), ("Brazilija","BR"), ("Rusija","RU"),
    ("Nizozemska","NL"), ("Belgija","BE"), ("Švica","CH"), ("Češka","CZ"),
    ("Slovaška","SK"), ("Madžarska","HU"), ("Poljska","PL"), ("Romunija","RO"),
    ("Bolgarija","BG"), ("Grčija","GR"), ("Turčija","TR"), ("Mehika","MX"),
    ("Argentina","AR"), ("Kolumbija","CO"), ("Čile","CL"), ("Indija","IN"),
    ("Kitajska","CN"), ("Južna Koreja","KR"), ("Norveška","NO"),
    ("Švedska","SE"), ("Danska","DK"), ("Finska","FI"), ("Irska","IE"),
    ("Portugalska","PT"),
]

ZANRI = [
    ("Vsi",""), ("Pop","pop"), ("Rock","rock"), ("Jazz","jazz"),
    ("Classical","classical"), ("Electronic","electronic"), ("Hip-Hop","hip-hop"),
    ("R&B","rnb"), ("Country","country"), ("Folk","folk"), ("Reggae","reggae"),
    ("Metal","metal"), ("Blues","blues"), ("Soul","soul"), ("Funk","funk"),
    ("Latin","latin"), ("News","news"), ("Talk","talk"), ("Sports","sports"),
    ("Religious","religious"), ("Children","children"), ("Dance","dance"),
    ("Ambient","ambient"), ("Indie","indie"), ("Alternative","alternative"),
    ("80s","80s"), ("90s","90s"), ("Oldies","oldies"),
]

RAPIDAPI_URL  = "https://50k-radio-stations.p.rapidapi.com/radios"
RAPIDAPI_HOST = "50k-radio-stations.p.rapidapi.com"

# Radio Browser (brez registracije)
RB_SERVERS = ["de1.api.radio-browser.info",
               "nl1.api.radio-browser.info",
               "at1.api.radio-browser.info"]
RB_UA      = f"Radiola/{VERSION}"


class RadioIskanje(tk.Toplevel):
    """Dialog za iskanje radio postaj — zavihka: Radio Browser + RapidAPI."""

    def __init__(self, master, api_key, c, fnt, lang, callback):
        super().__init__(master)
        self.title(S[lang]["radio_search_title"])
        self.configure(bg=c["BG"]); self.resizable(True,True)
        self.minsize(660,520)
        self.api_key    = api_key
        self.c=c; self.fnt=fnt; self.lang=lang
        self.callback   = callback
        self._rezultati = []
        self._aktiven_zavihek = "rb"   # "rb" ali "rapid"
        self._build()
        self.geometry("760x600")
        self.grab_set()

    def t(self,k): return S[self.lang].get(k,k)

    def _build(self):
        c=self.c; FK=self.fnt["FK"]; FB=self.fnt["FB"]; F=self.fnt["F"]

        # ══════════════════════════════════════════════════════════════════════
        # ZAVIHKA — Radio Browser | RapidAPI
        # ══════════════════════════════════════════════════════════════════════
        tab_bar=tk.Frame(self,bg=c["BG"]); tab_bar.pack(fill="x",padx=0,pady=0)

        self._tab_rb=tk.Button(tab_bar,text=self.t("rb_tab"),font=self.fnt["FB"],
                                relief="flat",padx=16,pady=8,cursor="hand2",
                                command=lambda:self._preklopi_zavihek("rb"))
        self._tab_rb.pack(side="left")
        self._tab_rapid=tk.Button(tab_bar,text=self.t("rapid_tab"),font=self.fnt["FK"],
                                   relief="flat",padx=16,pady=8,cursor="hand2",
                                   command=lambda:self._preklopi_zavihek("rapid"))
        self._tab_rapid.pack(side="left")
        tk.Frame(tab_bar,bg=c["CARD2"],height=2).pack(side="bottom",fill="x")

        # Vsebinski container — pakiran TAKOJ po tab_bar, PRED listboxom
        self._tab_vsebina = tk.Frame(self,bg=c["BG"])
        self._tab_vsebina.pack(fill="x",padx=14,pady=(4,0))

        self._frm_rb    = tk.Frame(self._tab_vsebina,bg=c["BG"])
        self._frm_rapid = tk.Frame(self._tab_vsebina,bg=c["BG"])
        self._build_rb(self._frm_rb)
        self._build_rapid(self._frm_rapid)

        # ── Skupni seznam rezultatov ──────────────────────────────────────────
        tk.Frame(self,bg=c["CARD2"],height=1).pack(fill="x",padx=14,pady=(2,2))
        frm=tk.Frame(self,bg=c["BG"]); frm.pack(fill="both",expand=True,padx=14)
        sb=tk.Scrollbar(frm); sb.pack(side="right",fill="y")
        self.lb=tk.Listbox(frm,yscrollcommand=sb.set,
                           bg=c["CARD"],fg=c["FG"],
                           selectbackground=c["ACCENT"],selectforeground=c["BTN_FG"],
                           font=("Courier New" if OS=="Windows" else "TkFixedFont",
                                 self.fnt["F"][1]),
                           bd=0,relief="flat",activestyle="none",
                           selectmode="extended")
        self.lb.pack(fill="both",expand=True)
        sb.config(command=self.lb.yview)
        self.lb.bind("<<ListboxSelect>>",self._on_sel)
        self.lb.bind("<Double-Button-1>",lambda e:self._predoglej())
        self.lb.bind("<Control-a>",
                     lambda e:(self.lb.selection_set(0,"end"),
                               self.btn_dodaj.config(state="normal")) if hasattr(self,"btn_dodaj") else None)

        # Predogled
        prev_row=tk.Frame(self,bg=c["BG"]); prev_row.pack(fill="x",padx=14,pady=(4,0))
        self._prev_frm=tk.Frame(prev_row,bg=c["CARD2"],width=48,height=48)
        self._prev_frm.pack(side="left"); self._prev_frm.pack_propagate(False)
        self._prev_ph=None
        self._prev_lbl=tk.Label(self._prev_frm,bg=c["CARD2"],text="",font=FK)
        self._prev_lbl.place(relx=0.5,rely=0.5,anchor="center")
        self._info_lbl=tk.Label(prev_row,text="",font=FK,
                                bg=c["BG"],fg=c["MUTED"],
                                wraplength=580,justify="left",anchor="w")
        self._info_lbl.pack(side="left",padx=(8,0))

        # ── Spodnji gumbi ─────────────────────────────────────────────────────
        tk.Frame(self,bg=c["CARD2"],height=1).pack(fill="x",padx=14,pady=(6,3))
        bot=tk.Frame(self,bg=c["BG"]); bot.pack(fill="x",padx=14,pady=(0,8))
        self.lbl_status=tk.Label(bot,text="",font=FK,bg=c["BG"],fg=c["MUTED"])
        self.lbl_status.pack(side="left")
        tk.Button(bot,text="Prekliči",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=10,pady=5,cursor="hand2",
                  command=self.destroy).pack(side="right")
        self.btn_dodaj=tk.Button(bot,text=self.t("radio_btn_add"),font=FB,
                                  bg=c["LIVE"],fg="#fff",relief="flat",
                                  padx=12,pady=5,cursor="hand2",
                                  state="disabled",command=self._dodaj)
        self.btn_dodaj.pack(side="right",padx=(0,6))

        # Aktiviraj privzeti zavihek
        self._preklopi_zavihek("rb")

    def _preklopi_zavihek(self, z):
        """Preklopi med Radio Browser in RapidAPI zavihkom."""
        self._aktiven_zavihek = z
        c=self.c; FK=self.fnt["FK"]; FB=self.fnt["FB"]
        if z=="rb":
            self._frm_rb.pack(fill="x")
            self._frm_rapid.pack_forget()
            self._tab_rb.config(bg=c["CARD"],fg=c["ACCENT"],font=FB,relief="groove")
            self._tab_rapid.config(bg=c["BG"],fg=c["MUTED"],font=FK,relief="flat")
        else:
            self._frm_rapid.pack(fill="x")
            self._frm_rb.pack_forget()
            self._tab_rapid.config(bg=c["CARD"],fg=c["ACCENT"],font=FB,relief="groove")
            self._tab_rb.config(bg=c["BG"],fg=c["MUTED"],font=FK,relief="flat")
        # Počisti rezultate ob menjavi zavihka
        try:
            self.lb.delete(0,"end"); self._rezultati=[]
            self.lbl_status.config(text="",fg=c["MUTED"])
            self.btn_dodaj.config(state="disabled")
            self._info_lbl.config(text="")
        except Exception:
            pass  # ob prvem klicu btn_dodaj še ne obstaja

    # ── Radio Browser zavihek ─────────────────────────────────────────────────

    def _build_rb(self, parent):
        c=self.c; FK=self.fnt["FK"]; F=self.fnt["F"]

        # Info vrstica
        info_row=tk.Frame(parent,bg=c["BG"]); info_row.pack(fill="x",pady=(0,4))
        tk.Label(info_row,text=self.t("rb_info"),font=FK,
                 bg=c["BG"],fg=c["LIVE"]).pack(side="left")

        # Vrstica 1: Država + Žanr
        r1=tk.Frame(parent,bg=c["BG"]); r1.pack(fill="x",pady=(0,3))
        tk.Label(r1,text=self.t("radio_country"),font=FK,
                 bg=c["BG"],fg=c["FG"],width=8,anchor="w").pack(side="left")
        self.var_drzava=tk.StringVar()
        cb_dr=ttk.Combobox(r1,textvariable=self.var_drzava,
                            values=[d[0] for d in DRZAVE],
                            state="readonly",width=20,font=FK)
        cb_dr.set("Vse"); cb_dr.pack(side="left",padx=(4,0))
        tk.Label(r1,text=self.t("radio_genre"),font=FK,
                 bg=c["BG"],fg=c["FG"],width=6,anchor="w").pack(side="left",padx=(12,0))
        self.var_zanr=tk.StringVar()
        cb_zan=ttk.Combobox(r1,textvariable=self.var_zanr,
                             values=[z[0] for z in ZANRI],
                             state="readonly",width=16,font=FK)
        cb_zan.set("Vsi"); cb_zan.pack(side="left",padx=(4,0))

        # Vrstica 2: Iskanje + razvrsti + filter + gumb
        r2=tk.Frame(parent,bg=c["BG"]); r2.pack(fill="x",pady=(0,3))
        tk.Label(r2,text=self.t("radio_search_lbl"),font=FK,
                 bg=c["BG"],fg=c["FG"],width=8,anchor="w").pack(side="left")
        self.var_q_rb=tk.StringVar()
        ent=tk.Entry(r2,textvariable=self.var_q_rb,font=F,
                     bg=c["CARD"],fg=c["FG"],insertbackground=c["FG"],
                     relief="flat",bd=4)
        ent.pack(side="left",fill="x",expand=True,padx=(4,6))
        ent.bind("<Return>",lambda e:self._iskanje())

        # Razvrsti
        tk.Label(r2,text=self.t("rb_order"),font=FK,
                 bg=c["BG"],fg=c["MUTED"]).pack(side="left")
        self.var_rb_order=tk.StringVar(value=self.t("rb_votes"))
        ttk.Combobox(r2,textvariable=self.var_rb_order,
                     values=[self.t("rb_votes"),self.t("rb_clicks"),
                             self.t("rb_name_ord"),self.t("rb_bitrate_ord")],
                     state="readonly",width=12,font=FK).pack(side="left",padx=(4,6))

        # Samo aktivne
        self.var_rb_active=tk.BooleanVar(value=True)
        tk.Checkbutton(r2,text=self.t("rb_only_active"),variable=self.var_rb_active,
                       bg=c["BG"],fg=c["FG"],selectcolor=c["CARD2"],
                       activebackground=c["BG"],font=FK,relief="flat").pack(side="left",padx=(0,6))

        tk.Button(r2,text=self.t("radio_btn_search"),font=FK,
                  bg=c["ACCENT"],fg=c["BTN_FG"],relief="flat",
                  padx=10,pady=3,cursor="hand2",
                  command=self._iskanje).pack(side="left")

        # Limit
        r3=tk.Frame(parent,bg=c["BG"]); r3.pack(fill="x",pady=(0,2))
        tk.Label(r3,text="Limit:",font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left")
        self.var_limit=tk.StringVar(value="100")
        tk.Spinbox(r3,from_=10,to=500,textvariable=self.var_limit,
                   width=5,font=FK,bg=c["CARD"],fg=c["FG"],
                   relief="flat",bd=2).pack(side="left",padx=(4,0))
        tk.Label(r3,text="  |  Brez omejitev zahtev  ·  radio-browser.info",
                 font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left",padx=(8,0))

    # ── RapidAPI zavihek ──────────────────────────────────────────────────────

    def _build_rapid(self, parent):
        c=self.c; FK=self.fnt["FK"]; F=self.fnt["F"]

        tk.Label(parent,text="🔑 "+self.t("rapid_tab")+"  |  500 zahtev/mesec brezplačno",
                 font=FK,bg=c["BG"],fg=c["MUTED"]).pack(anchor="w",pady=(0,4))

        r1=tk.Frame(parent,bg=c["BG"]); r1.pack(fill="x",pady=(0,3))
        tk.Label(r1,text=self.t("radio_country"),font=FK,
                 bg=c["BG"],fg=c["FG"],width=8,anchor="w").pack(side="left")
        self.var_drzava_rap=tk.StringVar()
        cb_dr=ttk.Combobox(r1,textvariable=self.var_drzava_rap,
                            values=[d[0] for d in DRZAVE],
                            state="readonly",width=20,font=FK)
        cb_dr.set("Vse"); cb_dr.pack(side="left",padx=(4,0))
        tk.Label(r1,text=self.t("radio_genre"),font=FK,
                 bg=c["BG"],fg=c["FG"],width=6,anchor="w").pack(side="left",padx=(12,0))
        self.var_zanr_rap=tk.StringVar()
        cb_zan=ttk.Combobox(r1,textvariable=self.var_zanr_rap,
                             values=[z[0] for z in ZANRI],
                             state="readonly",width=16,font=FK)
        cb_zan.set("Vsi"); cb_zan.pack(side="left",padx=(4,0))

        r2=tk.Frame(parent,bg=c["BG"]); r2.pack(fill="x",pady=(0,3))
        tk.Label(r2,text=self.t("radio_search_lbl"),font=FK,
                 bg=c["BG"],fg=c["FG"],width=8,anchor="w").pack(side="left")
        self.var_q_rap=tk.StringVar()
        ent=tk.Entry(r2,textvariable=self.var_q_rap,font=F,
                     bg=c["CARD"],fg=c["FG"],insertbackground=c["FG"],
                     relief="flat",bd=4)
        ent.pack(side="left",fill="x",expand=True,padx=(4,6))
        ent.bind("<Return>",lambda e:self._iskanje())

        r3=tk.Frame(parent,bg=c["BG"]); r3.pack(fill="x",pady=(0,2))
        tk.Label(r3,text="Limit:",font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left")
        self.var_limit_rap=tk.StringVar(value="50")
        tk.Spinbox(r3,from_=10,to=200,textvariable=self.var_limit_rap,
                   width=5,font=FK,bg=c["CARD"],fg=c["FG"],
                   relief="flat",bd=2).pack(side="left",padx=(4,6))
        tk.Button(r2,text=self.t("radio_btn_search"),font=FK,
                  bg=c["ACCENT"],fg=c["BTN_FG"],relief="flat",
                  padx=10,pady=3,cursor="hand2",
                  command=self._iskanje).pack(side="left")

        # Ključ ni nastavljen opozorilo
        if not self.api_key:
            tk.Label(parent,
                text="⚠  RapidAPI ključ ni nastavljen  →  Nastavitve → RapidAPI ključ…",
                font=self.fnt["FK"],bg="#fff3cd",fg="#856404",
                relief="flat",padx=8,pady=4).pack(fill="x",pady=(4,0))

    # ── Skupne metode ─────────────────────────────────────────────────────────

    def _koda_drzave(self, var=None):
        if var is None:
            var = self.var_drzava if self._aktiven_zavihek=="rb" else self.var_drzava_rap
        ime=var.get()
        for n,k in DRZAVE:
            if n==ime: return k
        return ""

    def _koda_zanra(self, var=None):
        if var is None:
            var = self.var_zanr if self._aktiven_zavihek=="rb" else self.var_zanr_rap
        ime=var.get()
        for n,k in ZANRI:
            if n==ime: return k
        return ""

    def _rb_server(self):
        """Vrne naključni delujoči RB strežnik."""
        import random
        return random.choice(RB_SERVERS)

    def _iskanje(self):
        self.lbl_status.config(text=self.t("radio_loading"),fg=self.c["MUTED"])
        self.lb.delete(0,"end"); self._rezultati=[]
        self.btn_dodaj.config(state="disabled"); self._info_lbl.config(text="")
        if self._aktiven_zavihek=="rb":
            threading.Thread(target=self._rb_klic,daemon=True).start()
        else:
            if not self.api_key:
                self.lbl_status.config(
                    text="Nastavi RapidAPI ključ v Nastavitve!",fg="#cc2200")
                return
            threading.Thread(target=self._rapid_klic,daemon=True).start()

    def _rb_server_url(self):
        """Pridobi delujoči Radio Browser strežnik prek DNS discovery."""
        import socket as _socket
        # Najprej poskusi DNS discovery (priporočen način)
        for host in ["all.api.radio-browser.info"] + RB_SERVERS:
            try:
                _socket.getaddrinfo(host, 80)
                return host
            except Exception:
                continue
        return RB_SERVERS[0]  # fallback

    def _rb_http_get(self, url, params):
        """HTTP GET prek requests ali urllib (fallback)."""
        full_url = url + "?" + urllib.parse.urlencode(params)
        if REQUESTS_OK:
            r = _requests_lib.get(url, params=params,
                                  headers={"User-Agent": RB_UA}, timeout=15)
            r.raise_for_status()
            return r.json()
        else:
            req = urllib.request.Request(full_url,
                                         headers={"User-Agent": RB_UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))

    def _rb_klic(self):
        """Radio Browser API klic — brez ključa, brez requests odvisnosti."""
        try:
            dr  = self._koda_drzave(self.var_drzava)
            za  = self._koda_zanra(self.var_zanr)
            q   = self.var_q_rb.get().strip()
            lim = int(self.var_limit.get() or 100)

            order_map = {
                self.t("rb_votes"):      "votes",
                self.t("rb_clicks"):     "clickcount",
                self.t("rb_name_ord"):   "name",
                self.t("rb_bitrate_ord"):"bitrate",
            }
            order       = order_map.get(self.var_rb_order.get(), "votes")
            only_active = self.var_rb_active.get()

            srv = self._rb_server_url()
            url = f"https://{srv}/json/stations/search"

            params = {
                "limit":      lim,
                "order":      order,
                "reverse":    "true",
                "hidebroken": "true" if only_active else "false",
            }
            if q:  params["name"]        = q
            if dr: params["countrycode"] = dr
            if za: params["tag"]         = za

            raw = self._rb_http_get(url, params)

            if not isinstance(raw, list):
                raise ValueError(f"Nepričakovan format odgovora: {str(raw)[:80]}")

            postaje = [self._rb_norm(p) for p in raw]
            self.after(0, lambda p=postaje: self._prikaži(p, "rb"))

        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self.lbl_status.config(
                text=f"Radio Browser: {m}", fg="#cc2200"))

    def _rb_norm(self, p):
        """Normalizira RB odgovor na skupni interni format."""
        return {
            "name":         p.get("name","?"),
            "url":          p.get("url_resolved") or p.get("url",""),
            "favicon":      p.get("favicon",""),
            "country_code": p.get("countrycode",""),
            "genre_slug":   (p.get("tags","") or "").split(",")[0][:14],
            "bitrate":      p.get("bitrate",0) or 0,
            "votes":        p.get("votes",0),
            "_src":         "rb",
        }

    def _rapid_klic(self):
        """RapidAPI klic."""
        try:
            dr  = self._koda_drzave(self.var_drzava_rap)
            za  = self._koda_zanra(self.var_zanr_rap)
            q   = self.var_q_rap.get().strip()
            lim = int(self.var_limit_rap.get() or 50)
            params={"limit":lim}
            if dr: params["country_code"]=dr.lower()
            if za: params["genre_slug"]=za
            if q:
                url=RAPIDAPI_URL+"/search"; params["q"]=q
            else:
                url=RAPIDAPI_URL
            hdrs={"X-RapidAPI-Key":self.api_key,"X-RapidAPI-Host":RAPIDAPI_HOST}
            if not REQUESTS_OK:
                raise ImportError("Namesti requests: pip install requests")
            r=_requests_lib.get(url,params=params,headers=hdrs,timeout=10)
            r.raise_for_status()
            data=r.json()
            raw=data.get("data",data) if isinstance(data,dict) else data
            # Normalizacija
            postaje=[self._rapid_norm(p) for p in raw]
            self.after(0,lambda p=postaje:self._prikaži(p,"rapid"))
        except requests.exceptions.HTTPError as e:
            koda = e.response.status_code
            msg  = (f"RapidAPI {koda}: "
                    f"{'Napačen ključ — preveri v Nastavitve' if koda==401 else str(e)}")
            self.after(0, lambda m=msg: self.lbl_status.config(text=m, fg="#cc2200"))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self.lbl_status.config(
                text=f"Napaka: {m}", fg="#cc2200"))

    def _rapid_norm(self, p):
        streams=p.get("streams",[])
        url=(streams[0].get("url","") if streams
             else p.get("url","") or p.get("stream_url",""))
        return {
            "name":         p.get("name","?"),
            "url":          url,
            "favicon":      p.get("favicon","") or p.get("logo",""),
            "country_code": p.get("country_code",""),
            "genre_slug":   p.get("genre_slug",""),
            "bitrate":      p.get("bitrate",0) or 0,
            "votes":        0,
            "_src":         "rapid",
        }

    def _prikaži(self, postaje, vir="rb"):
        self._rezultati=postaje
        self.lb.delete(0,"end")
        if not postaje:
            self.lbl_status.config(text=self.t("radio_no_results"),fg=self.c["MUTED"])
            return
        for p in postaje:
            ime=p.get("name","?")[:32]
            drzava=p.get("country_code","").upper()[:4]
            zanr=(p.get("genre_slug","") or "")[:13]
            bitrate=p.get("bitrate",0) or 0
            br=f"{bitrate}k" if bitrate else ""
            votes=p.get("votes",0) or 0
            ikona="●" if p.get("favicon") else "○"
            if vir=="rb":
                vr=f"  {ikona} {ime:<32} {drzava:<5} {zanr:<14} {br:<6} ♥{votes}"
            else:
                vr=f"  {ikona} {ime:<32} {drzava:<5} {zanr:<14} {br}"
            self.lb.insert("end",vr)
        vir_lbl="Radio Browser" if vir=="rb" else "RapidAPI"
        self.lbl_status.config(
            text=f"Najdenih: {len(postaje)}  [{vir_lbl}]",fg=self.c["LIVE"])

    def _on_sel(self,_=None):
        sel=self.lb.curselection()
        if not sel:
            self.btn_dodaj.config(state="disabled"); return
        self.btn_dodaj.config(state="normal")
        p=self._rezultati[sel[-1]]
        bitrate=p.get("bitrate",0) or 0
        zanr=p.get("genre_slug","") or ""
        drzava=p.get("country_code","").upper()
        votes=p.get("votes",0) or 0
        br_str=f"{bitrate}k" if bitrate else ""
        vot_str=f"  ♥{votes}" if votes else ""
        url=p.get("url","")
        info=(f"{p.get('name','?')}  |  {drzava}  |  {zanr}  |  {br_str}{vot_str}\n{url}")
        self._info_lbl.config(text=info)
        ico_url=p.get("favicon","")
        if ico_url:
            threading.Thread(target=self._nalozi_prev,args=(ico_url,),daemon=True).start()
        else:
            # Počisti prejšnjo ikono
            self._prev_lbl.config(image="",text=""); self._prev_ph=None

    def _stream_url(self, p):
        """Vrne stream URL iz normaliziranega zapisa."""
        return p.get("url","")

    def _nalozi_prev(self, url):
        try:
            if not REQUESTS_OK: raise ImportError("namesti requests")
            r=_requests_lib.get(url,timeout=5)
            r.raise_for_status()
            img=_pravilna_rgba(Image.open(io.BytesIO(r.content)))
            img=img.resize((46,46),Image.LANCZOS)
            ph=ImageTk.PhotoImage(img)
            self.after(0,lambda:self._nastavi_prev(ph))
        except Exception:
            pass

    def _nastavi_prev(self, ph):
        self._prev_ph=ph
        self._prev_lbl.config(image=ph,text=""); self._prev_lbl.image=ph

    def _predoglej(self):
        """Dvojni klik — predoglej stream URL."""
        sel=self.lb.curselection()
        if not sel: return
        p=self._rezultati[sel[0]]
        url=p.get("url","")
        vir="Radio Browser" if p.get("_src")=="rb" else "RapidAPI"
        votes=p.get("votes",0) or 0
        bitrate=p.get("bitrate",0) or 0
        info=(f"Ime: {p.get('name','?')}\n"
              f"Vir: {vir}\n"
              f"Država: {p.get('country_code','').upper()}\n"
              f"Žanr: {p.get('genre_slug','')}\n"
              f"Bitrate: {bitrate}k\n"
              f"Glasovi: {votes}\n\n"
              f"Stream URL:\n{url}\n\n"
              f"Ikona:\n{p.get('favicon','—')}")
        messagebox.showinfo(p.get("name",""),info,parent=self)

    def _dodaj(self):
        """Dodaj izbrane postaje v Radiolo (prenese ikone v ozadju)."""
        sel=self.lb.curselection()
        if not sel: return
        self.btn_dodaj.config(state="disabled",text="Prenašam...")
        threading.Thread(target=self._dodaj_thread,args=(sel,),daemon=True).start()

    def _dodaj_thread(self, sel):
        nove=[]
        for i in sel:
            p=self._rezultati[i]
            url=p.get("url","")
            if not url: continue
            b64=""
            ico_url=p.get("favicon","")
            if ico_url:
                try:
                    if not REQUESTS_OK: raise ImportError('namesti requests')
                    r=_requests_lib.get(ico_url,timeout=5)
                    r.raise_for_status()
                    img=_pravilna_rgba(Image.open(io.BytesIO(r.content)))
                    w,h=img.size; mn=min(w,h)
                    img=img.crop(((w-mn)//2,(h-mn)//2,(w+mn)//2,(h+mn)//2))
                    img=img.resize((STORE_SZ,STORE_SZ),Image.LANCZOS)
                    buf=io.BytesIO(); img.save(buf,format="PNG")
                    b64="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
                except Exception:
                    pass
            nove.append({"ime":p.get("name","?"),"url":url,"ikona":b64,"kw":""})
        if not nove:
            t=self.t("radio_btn_add")
            self.after(0,lambda:messagebox.showwarning(
                "","Ni veljavnih stream URL-jev.",parent=self))
            self.after(0,lambda tt=t:self.btn_dodaj.config(state="normal",text=tt))
            return
        self.after(0,lambda:self.callback(nove))
        self.after(0,self.destroy)


class _UvozNacin(tk.Toplevel):
    """Mini dialog: Dodaj postaje ali Izbriši trenutne in dodaj."""
    def __init__(self, master, c, fnt):
        super().__init__(master)
        self.title("Uvoz postaj"); self.result=None
        self.configure(bg=c["BG"]); self.resizable(False,False)
        FK=fnt["FK"]; FB=fnt["FB"]
        tk.Label(self,text="Način uvoza:",font=FB,bg=c["BG"],fg=c["FG"]
                 ).pack(padx=20,pady=(16,8))
        tk.Button(self,text="➕  DODAJ postaje obstoječim",font=FK,
                  bg=c["LIVE"],fg="#fff",relief="flat",padx=14,pady=8,
                  cursor="hand2",
                  command=lambda:(setattr(self,"result","dodaj"),self.destroy())
                  ).pack(fill="x",padx=20,pady=(0,6))
        tk.Button(self,text="🗑  IZBRIŠI trenutne in uvozi samo te",font=FK,
                  bg=c.get("RED","#cc2200"),fg="#fff",relief="flat",padx=14,pady=8,
                  cursor="hand2",
                  command=lambda:(setattr(self,"result","zamenjaj"),self.destroy())
                  ).pack(fill="x",padx=20,pady=(0,6))
        tk.Button(self,text="Prekliči",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=14,pady=6,cursor="hand2",
                  command=self.destroy).pack(pady=(0,14))
        self.grab_set(); self.wait_window()

class _IzvozNacin(tk.Toplevel):
    """Mini dialog: Izvoz samo postaje ali z ikonami."""
    def __init__(self, master, c, fnt):
        super().__init__(master)
        self.title("Izvoz postaj"); self.result=None
        self.configure(bg=c["BG"]); self.resizable(False,False)
        FK=fnt["FK"]; FB=fnt["FB"]
        tk.Label(self,text="Kaj izvoziti?",font=FB,bg=c["BG"],fg=c["FG"]
                 ).pack(padx=20,pady=(16,4))
        tk.Label(self,text="Brez ikon = berljiva besedilna datoteka",
                 font=FK,bg=c["BG"],fg=c["MUTED"]).pack(padx=20,pady=(0,8))
        tk.Button(self,text="📋  Samo postaje  (ime + URL, brez ikon)",font=FK,
                  bg=c["ACCENT"],fg="#fff",relief="flat",padx=14,pady=8,
                  cursor="hand2",
                  command=lambda:(setattr(self,"result","brez_ikon"),self.destroy())
                  ).pack(fill="x",padx=20,pady=(0,6))
        tk.Button(self,text="🖼  Postaje Z IKONAMI  (večja datoteka)",font=FK,
                  bg=c["CARD2"],fg=c["FG"],relief="flat",padx=14,pady=8,
                  cursor="hand2",
                  command=lambda:(setattr(self,"result","z_ikonami"),self.destroy())
                  ).pack(fill="x",padx=20,pady=(0,6))
        tk.Button(self,text="Prekliči",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=14,pady=6,cursor="hand2",
                  command=self.destroy).pack(pady=(0,14))
        self.grab_set(); self.wait_window()

class UrejevalnikPostaj(tk.Toplevel):
    def __init__(self, master, postaje, c, fnt, lang, on_save):
        super().__init__(master)
        self.title("Uredi postaje / Edit stations")
        self.resizable(True,True); self.configure(bg=c["BG"])
        self.postaje=[dict(p) for p in postaje]
        self.c=c; self.fnt=fnt; self.lang=lang; self.on_save=on_save
        self._di=None; self._urejamo_idx=None
        self._filtriran=[]
        self._build()
        self.geometry("660x660")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._shrani)

    def _build(self):
        c=self.c; F=self.fnt["F"]; FB=self.fnt["FB"]; FK=self.fnt["FK"]

        # ── Iskanje ───────────────────────────────────────────────────────────
        frm_s=tk.Frame(self,bg=c["BG"]); frm_s.pack(fill="x",padx=14,pady=(10,4))
        tk.Label(frm_s,text="🔍",font=F,bg=c["BG"],fg=c["MUTED"]).pack(side="left")
        self.var_iskanje=tk.StringVar()
        ent_iskanje=tk.Entry(frm_s,textvariable=self.var_iskanje,font=F,
                             bg=c["CARD"],fg=c["FG"],insertbackground=c["FG"],
                             relief="flat",bd=4)
        ent_iskanje.pack(side="left",fill="x",expand=True,padx=(4,0))
        self._dodaj_km(ent_iskanje)
        self.var_iskanje.trace_add("write",lambda *_:self._filtriraj())
        tk.Button(frm_s,text="✕",font=FK,bg=c["CARD2"],fg=c["FG"],relief="flat",
                  padx=6,cursor="hand2",
                  command=lambda:(self.var_iskanje.set(""),self._filtriraj())
                  ).pack(side="left",padx=(4,0))
        tk.Button(frm_s,text="Podvojene",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=8,pady=3,cursor="hand2",
                  command=self._pokazi_podvojene).pack(side="left",padx=(8,0))

        # ── Seznam ────────────────────────────────────────────────────────────
        tk.Label(self,text="● ikona prisotna   ○ manjka ikona   (povleci za vrstni red)",
                 font=FK,bg=c["BG"],fg=c["MUTED"]).pack(anchor="w",padx=14,pady=(0,2))
        frm=tk.Frame(self,bg=c["BG"]); frm.pack(fill="both",expand=True,padx=14)
        sb=tk.Scrollbar(frm); sb.pack(side="right",fill="y")
        self.lb=tk.Listbox(frm,yscrollcommand=sb.set,bg=c["CARD"],fg=c["FG"],
                           selectbackground=c["ACCENT"],selectforeground=c["BTN_FG"],
                           font=("Courier New" if OS=="Windows" else "TkFixedFont",
                                 self.fnt["F"][1]),
                           bd=0,relief="flat",activestyle="none",height=9,
                           selectmode="extended")
        self.lb.pack(fill="both",expand=True); sb.config(command=self.lb.yview)
        # Drag & drop za premikanje
        self.lb.bind("<ButtonPress-1>",self._drag_start)
        self.lb.bind("<B1-Motion>",self._dm)
        self.lb.bind("<ButtonRelease-1>",self._drag_end)
        self.lb.bind("<<ListboxSelect>>",self._sel)
        # Multi-select + Delete tipka
        self.lb.bind("<Delete>",lambda e:self._del_multi())
        self.lb.bind("<BackSpace>",lambda e:self._del_multi())
        # Ctrl+A = izberi vse
        self.lb.bind("<Control-a>",lambda e:(self.lb.selection_set(0,"end"),None))
        self.lb.bind("<Control-A>",lambda e:(self.lb.selection_set(0,"end"),None))

        # ── Premikanje ────────────────────────────────────────────────────────
        fm=tk.Frame(self,bg=c["BG"]); fm.pack(fill="x",padx=14,pady=(2,0))
        for t,cmd in [("▲",self._gor),("▼",self._dol)]:
            tk.Button(fm,text=t,command=cmd,bg=c["CARD2"],fg=c["FG"],
                      relief="flat",padx=10,pady=3,cursor="hand2",font=F).pack(side="left",padx=(0,4))
        self.lbl_stevilo=tk.Label(fm,text="",font=FK,bg=c["BG"],fg=c["MUTED"])
        self.lbl_stevilo.pack(side="right")
        self._filtriraj()  # kličemo ŠELE ko lbl_stevilo obstaja

        # ── Način urejanja ────────────────────────────────────────────────────
        self.lbl_nacin=tk.Label(self,text="— Nova postaja —",font=FK,bg=c["BG"],fg=c["ACCENT"])
        self.lbl_nacin.pack(anchor="w",padx=14,pady=(6,0))

        # ── Vnosna polja ──────────────────────────────────────────────────────
        f2=tk.Frame(self,bg=c["BG"]); f2.pack(fill="x",padx=14,pady=4)
        self._ent={}

        # Pozicija (za premikanje na določeno mesto)
        tk.Label(f2,text="# Poz.:",font=FK,bg=c["BG"],fg=c["FG"]).grid(
            row=0,column=0,sticky="nw",pady=2)
        rpos=tk.Frame(f2,bg=c["BG"]); rpos.grid(row=0,column=1,sticky="ew",padx=(8,0))
        self.ent_poz=tk.Entry(rpos,font=F,bg=c["CARD"],fg=c["FG"],
                               insertbackground=c["FG"],relief="flat",bd=4,width=6)
        self.ent_poz.pack(side="left")
        self._dodaj_km(self.ent_poz)
        tk.Label(rpos,text="  (prazno = ohrani; število = premakni na to mesto)",
                 font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left")

        fields=[("Ime / Name","ime"),("URL","url"),
                (S[self.lang]["station_kw"],"kw"),
                ("Ikona  (base64 ali pot .png/.jpg)","ikona")]
        for i,(lbl,k) in enumerate(fields):
            tk.Label(f2,text=lbl+":",font=FK,bg=c["BG"],fg=c["FG"]).grid(
                row=i+1,column=0,sticky="nw",pady=2)
            rf=tk.Frame(f2,bg=c["BG"]); rf.grid(row=i+1,column=1,sticky="ew",padx=(8,0))
            e=tk.Entry(rf,font=F,bg=c["CARD"],fg=c["FG"],
                       insertbackground=c["FG"],relief="flat",bd=4)
            e.pack(side="left",fill="x",expand=True)
            self._ent[k]=e; self._dodaj_km(e)
            if k=="ikona":
                tk.Button(rf,text="📁",font=FK,bg=c["CARD2"],fg=c["FG"],
                          relief="flat",padx=6,cursor="hand2",
                          command=lambda ek=e:self._brskalnik_ikone(ek)).pack(side="left",padx=(4,0))
                # Gumb za čiščenje ikone
                tk.Button(rf,text="✕",font=FK,bg=c["CARD2"],fg=c["FG"],
                          relief="flat",padx=4,cursor="hand2",
                          command=lambda ek=e:(ek.delete(0,"end"),self._posodobi_prev_ikone(""))
                          ).pack(side="left",padx=(2,0))
                # Gumb za takojšen predogled
                tk.Button(rf,text="👁",font=FK,bg=c["CARD2"],fg=c["FG"],
                          relief="flat",padx=4,cursor="hand2",
                          command=lambda ek=e:self._posodobi_prev_ikone(ek.get())
                          ).pack(side="left",padx=(2,0))
                # Ob vsaki spremembi v polju posodobi predogled
                e.bind("<FocusOut>", lambda ev,ek=e: self._posodobi_prev_ikone(ek.get()))
        f2.columnconfigure(1,weight=1)

        # ── Predogled ikone ───────────────────────────────────────────────────
        f_prev=tk.Frame(self,bg=c["BG"]); f_prev.pack(fill="x",padx=14,pady=(0,4))
        tk.Label(f_prev,text="Predogled ikone:",font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left")
        self._prev_iko_frm=tk.Frame(f_prev,bg=c["CARD2"],width=64,height=64)
        self._prev_iko_frm.pack(side="left",padx=(8,0))
        self._prev_iko_frm.pack_propagate(False)
        self._prev_iko_lbl=tk.Label(self._prev_iko_frm,bg=c["CARD2"],text="—",
                                     font=FK,fg=c["MUTED"])
        self._prev_iko_lbl.place(relx=0.5,rely=0.5,anchor="center")
        self._prev_iko_ph=None

        # ── Gumbi ─────────────────────────────────────────────────────────────
        f3=tk.Frame(self,bg=c["BG"]); f3.pack(fill="x",padx=14,pady=(4,8))
        def btn(t,cmd,bg=None,fg=None):
            return tk.Button(f3,text=t,command=cmd,bg=bg or c["CARD2"],
                             fg=fg or c["FG"],relief="flat",padx=8,pady=5,
                             cursor="hand2",font=FK)
        self.btn_nova=btn("➕ NOVA",self._nova_postaja,c["ACCENT"],c["BTN_FG"])
        self.btn_nova.pack(side="left",padx=(0,3))
        self.btn_uredi=btn("✏ UREDI",self._posodobi_postajo,c["GREEN"],c["BTN_FG"])
        self.btn_uredi.pack(side="left",padx=(0,3))
        btn("🗑 Izbriši",self._del).pack(side="left",padx=(0,3))
        btn(S[self.lang]["fetch_ico"],self._fetch_one).pack(side="left",padx=(0,3))
        btn(S[self.lang]["fetch_all"],self._fetch_all).pack(side="left",padx=(0,3))
        btn(S[self.lang]["radio_search"],self._odpri_radio_iskanje,
            c["ACCENT"],c["BTN_FG"]).pack(side="left",padx=(0,3))
        btn("Zapri",self._shrani,c["ACCENT"],c["BTN_FG"]).pack(side="right")
        btn(S[self.lang]["export_btn"],self._izvozi).pack(side="right",padx=(0,4))
        btn(S[self.lang]["import_btn"],self._uvozi).pack(side="right",padx=(0,4))
        self._posodobi_gumbe()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lb_idx(self, lb_pos):
        if 0 <= lb_pos < len(self._filtriran): return self._filtriran[lb_pos]
        return None

    def _filtriraj(self, _=None):
        q=self.var_iskanje.get().lower().strip()
        self._filtriran=[]
        for i,p in enumerate(self.postaje):
            if not q or q in p.get("ime","").lower() or q in p.get("url","").lower():
                self._filtriran.append(i)
        self.lb.delete(0,"end")
        for lb_i, real_i in enumerate(self._filtriran):
            p=self.postaje[real_i]
            has_ico=bool(p.get("ikona",""))
            dot="●" if has_ico else "○"
            # Format: pozicija(4) + dot + ime(28) + url(42)
            self.lb.insert("end",
                f"{real_i+1:>4}. {dot} {p.get('ime','')[:26]:<26}  {p.get('url','')[:44]}")
            # Cela vrstica: zelena = ikona, rdeča = brez ikone
            self.lb.itemconfig(lb_i,
                fg=self.c["LIVE"] if has_ico else self.c["RED"])
        self.lbl_stevilo.config(text=f"{len(self._filtriran)}/{len(self.postaje)}")

    def _pokazi_podvojene(self):
        from collections import Counter
        urls=[p.get("url","") for p in self.postaje if p.get("url","")]
        podv={u for u,n in Counter(urls).items() if n>1}
        if not podv:
            messagebox.showinfo("","Ni podvojenih URL-jev. ✓",parent=self); return
        self.var_iskanje.set("")
        self.lb.delete(0,"end"); self._filtriran=[]
        for i,p in enumerate(self.postaje):
            if p.get("url","") in podv:
                self._filtriran.append(i)
                self.lb.insert("end",f"  {i+1:>3}.⚠ {p['ime'][:28]:<28}  {p['url'][:42]}")
                self.lb.itemconfig("end",fg="#ff6666")
        n=len(self._filtriran)
        self.lbl_stevilo.config(text=f"Podvojene: {n}")
        if n and messagebox.askyesno("Podvojene",
            f"Najdenih {n} podvojenih postaj.\nIzbriši vse razen prve pojavitve?",
            parent=self):
            # Ohrani samo prvo pojavitev vsakega URL-ja
            videni=set(); za_bris=[]
            for i,p in enumerate(self.postaje):
                u=p.get("url","")
                if u in podv:
                    if u in videni: za_bris.append(i)
                    else: videni.add(u)
            for i in sorted(za_bris,reverse=True):
                del self.postaje[i]
            self._filtriraj()
            messagebox.showinfo("",f"Izbrisano {len(za_bris)} podvojenih postaj.",parent=self)

    def _posodobi_gumbe(self):
        c=self.c
        if self._urejamo_idx is None:
            self.lbl_nacin.config(text="— Nova postaja —",fg=c["ACCENT"])
            self.btn_nova.config(bg=c["ACCENT"],fg=c["BTN_FG"],text="➕ NOVA")
            self.btn_uredi.config(state="disabled",bg=c["CARD2"],fg=c["MUTED"],text="✏ UREDI")
        else:
            ime=self.postaje[self._urejamo_idx].get("ime","")
            poz=self._urejamo_idx+1
            self.lbl_nacin.config(text=f"— Urejam #{poz}: {ime} —",fg=c["GREEN"])
            self.btn_nova.config(bg=c["CARD2"],fg=c["FG"],text="✕ Prekliči")
            self.btn_uredi.config(state="normal",bg=c["GREEN"],fg=c["BTN_FG"],text="✏ UREDI (shrani)")

    def _dodaj_km(self, widget):
        """Kontekstni meni kopiraj/prilepi."""
        c=self.c
        m=tk.Menu(widget,tearoff=0,bg=c["CARD"],fg=c["FG"],
                  activebackground=c["ACCENT"],activeforeground=c["BTN_FG"])
        m.add_command(label="✂ Izreži",  command=lambda:widget.event_generate("<<Cut>>"))
        m.add_command(label="📋 Kopiraj",command=lambda:widget.event_generate("<<Copy>>"))
        m.add_command(label="📌 Prilepi",command=lambda:widget.event_generate("<<Paste>>"))
        m.add_separator()
        m.add_command(label="Izberi vse",command=lambda:widget.select_range(0,"end"))
        m.add_command(label="Počisti",   command=lambda:widget.delete(0,"end"))
        def show(e): m.tk_popup(e.x_root,e.y_root)
        widget.bind("<Button-3>",show); widget.bind("<Button-2>",show)

    def _posodobi_prev_ikone(self, b64):
        """Prikaže predogled ikone v okvirčku urejevalnika."""
        for w in self._prev_iko_frm.winfo_children(): w.destroy()
        if not b64:
            tk.Label(self._prev_iko_frm,text="—",font=self.fnt["FK"],
                     bg=self.c["CARD2"],fg=self.c["MUTED"]
                     ).place(relx=0.5,rely=0.5,anchor="center")
            return
        try:
            b64c = _ocisti_b64(b64)
            if not b64c: raise ValueError("invalid")
            data = b64c.split(",",1)[1] if b64c.startswith("data:") else b64c
            import base64 as _b64
            img = _pravilna_rgba(Image.open(io.BytesIO(_b64.b64decode(data))))
            img = img.resize((60,60), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self._prev_iko_ph = ph
            lbl = tk.Label(self._prev_iko_frm,image=ph,bg=self.c["CARD2"],bd=0)
            lbl.image = ph
            lbl.place(relx=0.5,rely=0.5,anchor="center")
        except Exception:
            tk.Label(self._prev_iko_frm,text="✗",font=self.fnt["FK"],
                     bg=self.c["CARD2"],fg=self.c["RED"]
                     ).place(relx=0.5,rely=0.5,anchor="center")

    def _brskalnik_ikone(self, entry):
        """Odpre lasten brskalnik z predogledom slik."""
        IzbiraIkone(self, entry, self.c, self.fnt)
        # Po zaprtju dialoga posodobi predogled
        self.after(200, lambda: self._posodobi_prev_ikone(self._ent.get("ikona","").get() if hasattr(self._ent.get("ikona",""),"get") else ""))

    # ── Listbox operacije ─────────────────────────────────────────────────────

    def _sel(self,_=None):
        sel=self.lb.curselection()
        if not sel: return
        real_idx=self._lb_idx(sel[0])
        if real_idx is None: return
        p=self.postaje[real_idx]
        for k,e in self._ent.items(): e.delete(0,"end"); e.insert(0,p.get(k,""))
        self.ent_poz.delete(0,"end")
        self.ent_poz.insert(0,str(real_idx+1))
        self._urejamo_idx=real_idx
        self._posodobi_gumbe()
        # Posodobi predogled ikone
        self._posodobi_prev_ikone(p.get("ikona",""))

    def _drag_start(self,e):
        lb_pos=self.lb.nearest(e.y)
        self._di=self._lb_idx(lb_pos)
        self._dragging=False

    def _dm(self,e):
        if self._di is None: return
        lb_pos=self.lb.nearest(e.y); real_idx=self._lb_idx(lb_pos)
        if real_idx is None or real_idx==self._di: return
        self._dragging=True
        self.postaje.insert(real_idx, self.postaje.pop(self._di))
        self._di=real_idx
        self._urejamo_idx=real_idx
        self._filtriraj()
        self.lb.selection_clear(0,"end"); self.lb.selection_set(lb_pos)

    def _drag_end(self,e):
        if not getattr(self,"_dragging",False):
            pass  # navaden klik — _sel se pokliče ločeno
        self._dragging=False
        self._di=None

    def _gor(self):
        sel=self.lb.curselection()
        if not sel or sel[0]==0: return
        lb=sel[0]; ri=self._lb_idx(lb); ri2=self._lb_idx(lb-1)
        if ri is None or ri2 is None: return
        self.postaje[ri],self.postaje[ri2]=self.postaje[ri2],self.postaje[ri]
        self._filtriraj(); self.lb.selection_set(lb-1)

    def _dol(self):
        sel=self.lb.curselection()
        if not sel or sel[0]>=len(self._filtriran)-1: return
        lb=sel[0]; ri=self._lb_idx(lb); ri2=self._lb_idx(lb+1)
        if ri is None or ri2 is None: return
        self.postaje[ri],self.postaje[ri2]=self.postaje[ri2],self.postaje[ri]
        self._filtriraj(); self.lb.selection_set(lb+1)

    # ── Dodaj / Posodobi ──────────────────────────────────────────────────────

    def _nova_postaja(self):
        if self._urejamo_idx is not None:
            self._urejamo_idx=None
            for e in self._ent.values(): e.delete(0,"end")
            self.ent_poz.delete(0,"end")
            self.lb.selection_clear(0,"end")
        else:
            ime=self._ent["ime"].get().strip(); url=self._ent["url"].get().strip()
            if not ime or not url:
                messagebox.showwarning("","Vpiši ime in URL.",parent=self); return
            nova={k:self._ent[k].get().strip() for k in self._ent}
            # Preveri pozicijo
            poz_str=self.ent_poz.get().strip()
            if poz_str.isdigit():
                poz=max(1,min(int(poz_str),len(self.postaje)+1))-1
                self.postaje.insert(poz,nova)
            else:
                self.postaje.append(nova)
            for e in self._ent.values(): e.delete(0,"end")
            self.ent_poz.delete(0,"end")
            self._filtriraj(); self.lb.see("end")
        self._posodobi_gumbe()

    def _posodobi_postajo(self):
        """Posodobi izbrano postajo — upošteva tudi novo pozicijo."""
        if self._urejamo_idx is None: return
        ime=self._ent["ime"].get().strip(); url=self._ent["url"].get().strip()
        if not ime or not url:
            messagebox.showwarning("","Vpiši ime in URL.",parent=self); return

        # Posodobi polja
        for k in self._ent:
            self.postaje[self._urejamo_idx][k]=self._ent[k].get().strip()

        # Premakni na novo pozicijo če je vpisana
        poz_str=self.ent_poz.get().strip()
        if poz_str.isdigit():
            nova_poz=max(1,min(int(poz_str),len(self.postaje)))-1
            stara_poz=self._urejamo_idx
            if nova_poz != stara_poz:
                p=self.postaje.pop(stara_poz)
                self.postaje.insert(nova_poz,p)

        self._urejamo_idx=None
        for e in self._ent.values(): e.delete(0,"end")
        self.ent_poz.delete(0,"end")
        self._filtriraj(); self._posodobi_gumbe()

    def _del(self):
        self._del_multi()

    def _del_multi(self):
        sel=self.lb.curselection()
        if not sel: return
        idxs=[self._lb_idx(s) for s in sel]
        idxs=[i for i in idxs if i is not None]
        if not idxs: return
        if len(idxs)==1:
            ime=self.postaje[idxs[0]].get("ime","?")
            if not messagebox.askyesno("Izbriši",f"Izbriši postajo:\n{ime}?",parent=self): return
        else:
            if not messagebox.askyesno("Izbriši",
                f"Izbriši {len(idxs)} izbranih postaj?",parent=self): return
        for i in sorted(set(idxs),reverse=True):
            if self._urejamo_idx==i: self._urejamo_idx=None
            del self.postaje[i]
        self._filtriraj(); self._posodobi_gumbe()

    # ── Favicon ───────────────────────────────────────────────────────────────

    def _fetch_one(self):
        sel=self.lb.curselection()
        if not sel: messagebox.showinfo("","Izberi postajo.",parent=self); return
        p=self.postaje[self._lb_idx(sel[0])]
        def _do():
            img=pridobi_favicon(p["url"])
            if img: p["ikona"]=ikona_v_b64(img); self.after(0,self._filtriraj)
            msg=(f"Ikona za {p['ime']} posodobljena." if img
                 else "Ikone ni bilo mogoče pridobiti.\nDodaj ročno z gumbom 📁")
            self.after(0,lambda:messagebox.showinfo("",msg,parent=self))
        threading.Thread(target=_do,daemon=True).start()

    def _fetch_all(self):
        def _do():
            n=0
            for p in self.postaje:
                if not p.get("ikona","") and p.get("url",""):
                    img=pridobi_favicon(p["url"])
                    if img: p["ikona"]=ikona_v_b64(img); n+=1
            self.after(0,self._filtriraj)
            self.after(0,lambda:messagebox.showinfo("",
                f"{S[self.lang]['fetch_done']}: {n}",parent=self))
        threading.Thread(target=_do,daemon=True).start()
        messagebox.showinfo("",S[self.lang]["fetching"],parent=self)

    # ── Uvoz / Izvoz ──────────────────────────────────────────────────────────

    def _uvozi(self):
        pot=filedialog.askopenfilename(parent=self,
            filetypes=[("Text files","*.txt"),("All","*.*")])
        if not pot: return
        # Dialog: dodaj ali zamenjaj
        nacin=_UvozNacin(self,self.c,self.fnt).result
        if nacin is None: return  # Prekliči
        n=0; nove=[]
        with open(pot,encoding="utf-8") as f:
            for vr in f:
                vr=vr.strip()
                if not vr or vr.startswith("#"): continue
                d=[x.strip() for x in vr.split("=",2)]
                if len(d)>=2 and d[1]:
                    nove.append({
                        "ime":  d[0],
                        "url":  d[1],
                        "ikona":d[2] if len(d)>2 else "",
                        "kw":   ""}); n+=1
        if nacin=="zamenjaj":
            self.postaje=nove
        else:
            self.postaje.extend(nove)
        self._filtriraj()
        messagebox.showinfo("",f"Uvoženo {n} postaj.",parent=self)

    def _izvozi(self):
        # Vprašaj kaj izvoziti
        nacin=_IzvozNacin(self,self.c,self.fnt).result
        if nacin is None: return
        z_ikonami = (nacin=="z_ikonami")
        privzeto = "stations_export.txt" if not z_ikonami else "stations_z_ikonami.txt"
        pot=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",
            filetypes=[("Text files","*.txt"),("All","*.*")],
            initialfile=privzeto)
        if not pot: return
        with open(pot,"w",encoding="utf-8") as f:
            if z_ikonami:
                f.write("# Radiola – izvoz postaj Z IKONAMI\n")
                f.write("# Format:  Ime = URL = data:image/png;base64,...\n\n")
                for p in self.postaje:
                    line=f"{p['ime']} = {p.get('url','')} = {p.get('ikona','')}\n"
                    f.write(line)
            else:
                f.write("# Radiola – izvoz postaj (brez ikon)\n")
                f.write("# ──────────────────────────────────────────────────────────\n")
                f.write("# Format:  Ime postaje = Stream URL\n")
                f.write("# Uvoz:    Uredi postaje → Uvozi .txt\n")
                f.write("# ──────────────────────────────────────────────────────────\n\n")
                for p in self.postaje:
                    ime=p.get("ime","?"); url=p.get("url","")
                    kw=p.get("kw","")
                    komentar=f"  # kw: {kw}" if kw else ""
                    f.write(f"{ime} = {url}{komentar}\n")
        messagebox.showinfo("",f"Izvoženo {len(self.postaje)} postaj.\n{'(z ikonami)' if z_ikonami else '(brez ikon)'}",
                            parent=self)

    def _odpri_radio_iskanje(self):
        """Odpre dialog za iskanje postaj (Radio Browser + RapidAPI)."""
        try:
            nas = self.master.nas
        except AttributeError:
            nas = {}
        kljuc = nas.get("rapidapi_key","").strip()
        # Odpre se vedno — Radio Browser ne potrebuje ključa
        RadioIskanje(self, kljuc, self.c, self.fnt, self.lang,
                     callback=self._dodaj_iz_api)

    def _dodaj_iz_api(self, nove_postaje):
        """Callback: doda postaje iz API iskanja."""
        self.postaje.extend(nove_postaje)
        self._filtriraj()
        messagebox.showinfo(
            "",self.t("radio_added").format(n=len(nove_postaje)),
            parent=self)

    def t(self, k):
        return S[self.lang].get(k, k)

    def _shrani(self):
        shrani_postaje(self.postaje); self.on_save(self.postaje); self.destroy()


# ── Main App ──────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)  # resizable se nastavi v _build()
        self.nas     = nalozi_settings()
        self.lang    = self.nas.get("jezik","si")
        self.tema    = zazna_temo()
        self.c       = barve(self.tema)
        self.fnt     = fonti()
        self.postaje = nalozi_postaje()
        self.player  = PredvajalnikAvdia()
        self.gl_obj  = Glasnost()
        self.meta    = None
        self.predvaja= False
        self.govor_aktiven=False
        self.izvorna_gl=self.nas["glasnost"]
        self._stop_gl=threading.Event()
        self._timer_after=None
        self._timer_sek=0
        self._timer_running=False
        self._ikone={}
        self._predvajal_pred_spanjem=False
        self.configure(bg=self.c["BG"])
        self._set_app_icon()
        self._style()
        self._build_menu()
        self._build()
        if self.nas["avto_predvajaj"] and self.nas["zadnja_postaja"]:
            for p in self.postaje:
                if p["ime"]==self.nas["zadnja_postaja"]:
                    self.var_postaja.set(p["ime"]); self.after(900,self._play); break
        # Monitor za prebujanje iz spanja (daemon nit — se konča z programom)
        threading.Thread(target=self._spanje_monitor,daemon=True).start()

    def _dodaj_kontekstni_meni_spinbox(self, widget):
        """Doda desni-klik meni za Spinbox."""
        c=self.c
        menu=tk.Menu(widget,tearoff=0,bg=c["CARD"],fg=c["FG"],
                     activebackground=c["ACCENT"],activeforeground=c["BTN_FG"])
        menu.add_command(label="📋 Kopiraj", command=lambda:widget.event_generate("<<Copy>>"))
        menu.add_command(label="📌 Prilepi", command=lambda:widget.event_generate("<<Paste>>"))
        menu.add_command(label="Izberi vse", command=lambda:widget.selection("range",0,"end"))
        def show(e): menu.tk_popup(e.x_root,e.y_root)
        widget.bind("<Button-3>",show)
        widget.bind("<Button-2>",show)

    def t(self,k): return S[self.lang].get(k,k)

    def _set_app_icon(self):
        """Nastavi ikono za naslovnico in opravilno vrstico."""
        try:
            if os.path.exists(ICON_FILE):
                # Večja ikona za opravilno vrstico (128px)
                img_big=Image.open(ICON_FILE).resize((128,128),Image.LANCZOS)
                self._appicon_big=ImageTk.PhotoImage(img_big)
                # Manjša za naslovnico (32px)
                img_sm=Image.open(ICON_FILE).resize((32,32),Image.LANCZOS)
                self._appicon_sm=ImageTk.PhotoImage(img_sm)
                # Nastavi obe — Tkinter vzame prvo za taskbar
                self.iconphoto(True,self._appicon_big,self._appicon_sm)
                # Linux: nastavi WM_CLASS za pravilno skupiniranje
                if OS=="Linux":
                    self.tk.call("wm","iconphoto",self._w,self._appicon_big)
        except Exception: pass

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        c=self.c
        mb=tk.Menu(self,bg=c["CARD"],fg=c["FG"],
                   activebackground=c["ACCENT"],activeforeground=c["BTN_FG"],relief="flat",bd=0)
        self.config(menu=mb)
        ms=tk.Menu(mb,tearoff=0,bg=c["CARD"],fg=c["FG"],
                   activebackground=c["ACCENT"],activeforeground=c["BTN_FG"])
        mb.add_cascade(label=self.t("m_settings"),menu=ms)
        # Volume & boost
        ms.add_command(label=self.t("m_volume"),command=self._open_vol)
        # Keyword
        ms.add_command(label=self.t("m_keyword"),command=self._open_kw)
        ms.add_command(label=self.t("rapidapi_menu"),command=self._nas_rapidapi)
        ms.add_separator()
        # Icon rows
        self.var_rows=tk.IntVar(value=self.nas.get("icon_rows",2))
        ms.add_radiobutton(label=self.t("m_1row"),variable=self.var_rows,
                           value=1,command=self._on_rows)
        ms.add_radiobutton(label=self.t("m_2rows"),variable=self.var_rows,
                           value=2,command=self._on_rows)
        ms.add_separator()
        # Autoplay
        self.var_avto=tk.BooleanVar(value=self.nas["avto_predvajaj"])
        ms.add_checkbutton(label=self.t("autoplay"),variable=self.var_avto,
                           command=self._shrani_nas)
        ms.add_separator()
        # Language
        ml=tk.Menu(ms,tearoff=0,bg=c["CARD"],fg=c["FG"],
                   activebackground=c["ACCENT"],activeforeground=c["BTN_FG"])
        ms.add_cascade(label=self.t("m_lang"),menu=ml)
        self.var_lang=tk.StringVar(value=self.lang)
        ml.add_radiobutton(label=self.t("m_si"),variable=self.var_lang,
                           value="si",command=lambda:self._set_lang("si"))
        ml.add_radiobutton(label=self.t("m_en"),variable=self.var_lang,
                           value="en",command=lambda:self._set_lang("en"))
        # About
        ma=tk.Menu(mb,tearoff=0,bg=c["CARD"],fg=c["FG"],
                   activebackground=c["ACCENT"],activeforeground=c["BTN_FG"])
        mb.add_cascade(label=self.t("m_about"),menu=ma)
        ma.add_command(label=f"{APP_NAME} v{VERSION}...",command=self._about)

    def _set_lang(self,l):
        self.lang=l; self.nas["jezik"]=l; shrani_settings(self.nas)
        messagebox.showinfo(APP_NAME,
            "Jezik spremenjen. Znova zaženi Radiola.\n"
            "Language changed. Please restart Radiola.")

    def _on_rows(self):
        self.nas["icon_rows"]=self.var_rows.get()
        shrani_settings(self.nas); self._ikone.clear(); self._naredi_gumbe()

    def _open_vol(self):
        GlasnostDialog(self,self.nas,self.gl_obj,self.c,self.fnt,self.lang,self._shrani_nas)

    def _open_kw(self):
        KljucnaBeseadaDialog(self,self.nas,self.c,self.fnt,self.lang,self._shrani_nas)

    def _nas_rapidapi(self):
        RapidAPIKeyDialog(self,self.nas,self.c,self.fnt,self.lang,self._shrani_nas)

    def _about(self):
        w=tk.Toplevel(self); w.title(self.t("about_title"))
        w.configure(bg=self.c["BG"]); w.resizable(False,False)
        try:
            if os.path.exists(ICON_FILE):
                img=Image.open(ICON_FILE).resize((72,72),Image.LANCZOS)
                ph=ImageTk.PhotoImage(img); w._ph=ph
                tk.Label(w,image=ph,bg=self.c["BG"]).pack(pady=(16,4))
        except Exception: pass
        tk.Label(w,text=self.t("about_text"),font=self.fnt["F"],
                 bg=self.c["BG"],fg=self.c["FG"],justify="center").pack(padx=24,pady=8)
        tk.Button(w,text="OK",command=w.destroy,bg=self.c["ACCENT"],fg=self.c["BTN_FG"],
                  relief="flat",padx=20,pady=6,cursor="hand2",font=self.fnt["FB"]).pack(pady=(4,16))
        w.grab_set()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        c=self.c; F=self.fnt["F"]; FB=self.fnt["FB"]
        FS=self.fnt["FS"]; FT=self.fnt["FT"]; FK=self.fnt["FK"]

        # ── resizable okno ────────────────────────────────────────────
        self.resizable(True, True)
        self.minsize(600, 480)
        self.columnconfigure(0, weight=1)

        # ════════════════════════════════════════════════════════════
        # ZGORAJ: Header + Postaja + Zdaj predvaja + kontrole glasnosti
        # ════════════════════════════════════════════════════════════

        # Header
        g=tk.Frame(self,bg=c["BG"]); g.pack(fill="x",padx=14,pady=(7,2))
        tk.Label(g,text=f"◉ {APP_NAME}",font=FT,bg=c["BG"],fg=c["ACCENT"]).pack(side="left")
        inf=(f"Win · {'pycaw✓' if PYCAW_OK else 'pycaw✗'}" if OS=="Windows"
             else f"{OS} · pactl")
        tk.Label(g,text=inf,font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="right")
        pt=(self.t("player_lbl")+self.player.ime if self.player.na_voljo else self.t("no_player"))
        tk.Label(g,text=pt,font=FK,bg=c["BG"],
                 fg=c["MUTED"] if self.player.na_voljo else "#ff6666").pack(side="right",padx=(0,10))

        # ── Zgornja vrstica: [POSTAJA+ZDAJ levo] | [🔊 vert] [🎙 vert+dd] | [ikona]
        # Vse tri stolpce enake višine – ikona = enako kot kartici skupaj
        top=tk.Frame(self,bg=c["BG"]); top.pack(fill="x",padx=14,pady=(2,3))

        # ── LEVO: POSTAJA + ZDAJ PREDVAJA ────────────────────────────
        levo=tk.Frame(top,bg=c["BG"]); levo.pack(side="left",fill="both",expand=True)

        # POSTAJA kartica
        k_post=tk.Frame(levo,bg=c["CARD"],padx=12,pady=5)
        k_post.pack(fill="x",pady=(0,3))
        r1=tk.Frame(k_post,bg=c["CARD"]); r1.pack(fill="x")
        tk.Label(r1,text=self.t("station"),font=FK,bg=c["CARD"],fg=c["MUTED"]).pack(side="left")
        tk.Button(r1,text="✏ "+self.t("edit_stations"),font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=5,pady=1,cursor="hand2",
                  command=self._uredi_postaje).pack(side="right")
        r2=tk.Frame(k_post,bg=c["CARD"]); r2.pack(fill="x",pady=(3,0))
        tk.Button(r2,text="◀",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=5,pady=2,cursor="hand2",
                  command=self._prejsnja_postaja).pack(side="left",padx=(0,2))
        self.var_postaja=tk.StringVar(
            value=self.nas.get("zadnja_postaja","") or
                  (self.postaje[0]["ime"] if self.postaje else ""))
        self.cb=ttk.Combobox(r2,textvariable=self.var_postaja,
                              values=[p["ime"] for p in self.postaje],
                              state="normal",style="R.TCombobox",font=FB,height=30)
        self.cb.pack(side="left",fill="x",expand=True)
        self.cb.bind("<<ComboboxSelected>>",lambda _:self._postaja_change())
        self.cb.bind("<Return>",lambda _:self._postaja_change())
        tk.Button(r2,text="▶",font=FK,bg=c["CARD2"],fg=c["FG"],
                  relief="flat",padx=5,pady=2,cursor="hand2",
                  command=self._naslednja_postaja).pack(side="left",padx=(2,0))

        # ZDAJ PREDVAJA kartica
        k2=tk.Frame(levo,bg=c["CARD"],padx=12,pady=5)
        k2.pack(fill="x")
        np_row=tk.Frame(k2,bg=c["CARD"]); np_row.pack(fill="x")
        tk.Label(np_row,text=self.t("now_playing"),font=FK,
                 bg=c["CARD"],fg=c["MUTED"]).pack(side="left")
        self.frm_kw_ind=tk.Frame(np_row,bg=c["CARD2"],padx=6,pady=1)
        self.frm_kw_ind.pack(side="left",padx=(8,0))
        self.lbl_kw_ind=tk.Label(self.frm_kw_ind,text="",font=FK,bg=c["CARD2"],fg=c["MUTED"])
        self.lbl_kw_ind.pack()
        self._posodobi_kw_indikator(False)
        self.lbl_naslov=tk.Label(k2,text="—",font=FB,bg=c["CARD"],fg=c["FG"],
                                  wraplength=300,justify="left",anchor="w")
        self.lbl_naslov.pack(fill="x",pady=(3,0))
        self.lbl_govor=tk.Label(k2,text="",font=FK,bg=c["CARD"],fg=c["LIVE"],anchor="w")
        self.lbl_govor.pack(fill="x",pady=(1,1))

        # ── SREDINA: dva vertikalna drsnika ──────────────────────────
        # Glasnost (🔊) in Dvig (🎙) — vsak v svojem stolpcu, fill=y
        mid=tk.Frame(top,bg=c["BG"]); mid.pack(side="left",fill="y",padx=(6,4))

        # — Glasnost —
        col_gl=tk.Frame(mid,bg=c["BG"]); col_gl.pack(side="left",fill="y",padx=(0,4))
        tk.Label(col_gl,text="🔊",font=FK,bg=c["BG"],fg=c["MUTED"]).pack()
        self.var_gl_lbl=tk.StringVar(value=f"{int(self.nas.get('glasnost',0.5)*100)}%")
        tk.Label(col_gl,textvariable=self.var_gl_lbl,font=FK,
                 bg=c["BG"],fg=c["FG"],width=4).pack()
        self.sl_gl_main=tk.Scale(col_gl,from_=100,to=0,orient="vertical",
                                  showvalue=False,length=90,width=18,
                                  bg=c["BG"],fg=c["FG"],
                                  troughcolor=c["CARD2"],highlightthickness=0,
                                  command=self._on_gl_main)
        self.sl_gl_main.set(int(self.nas.get("glasnost",0.5)*100))
        self.sl_gl_main.pack(fill="y",expand=True)

        # — Separator —
        tk.Frame(mid,bg=c["CARD2"],width=1).pack(side="left",fill="y",padx=2)

        # — Dvig —
        col_dv=tk.Frame(mid,bg=c["BG"]); col_dv.pack(side="left",fill="y")
        tk.Label(col_dv,text="🎙",font=FK,bg=c["BG"],fg=c["MUTED"]).pack()
        self.var_dvig_lbl=tk.StringVar(value=f"+{int(self.nas.get('dvig',0.3)*100)}%")
        tk.Label(col_dv,textvariable=self.var_dvig_lbl,font=FK,
                 bg=c["BG"],fg=c["FG"],width=4).pack()
        # Drsnik — enaka višina kot glasnost (fill="y", expand=True)
        self.sl_dvig_main=tk.Scale(col_dv,from_=60,to=0,orient="vertical",
                                    showvalue=False,length=90,width=18,
                                    bg=c["BG"],fg=c["FG"],
                                    troughcolor=c["CARD2"],highlightthickness=0,
                                    command=self._on_dvig_main)
        self.sl_dvig_main.set(int(self.nas.get("dvig",0.3)*100))
        self.sl_dvig_main.pack(fill="y",expand=True)
        # Kljukica: rdeč kvadratek = izklopljeno, zelen = aktivno
        dvig_aktiven = self.nas.get("dvig",0.3) > 0
        BOX=20
        self.cv_dvig_chk=tk.Canvas(col_dv,width=BOX,height=BOX,
                                    bg=c["BG"],highlightthickness=0,cursor="hand2")
        self.cv_dvig_chk.pack(pady=(4,2))
        self._dvig_aktiven = dvig_aktiven
        self._narisi_dvig_chk()
        self.cv_dvig_chk.bind("<Button-1>", self._toggle_dvig_chk)

        # ── DESNO: ikona predvajane postaje — enako visoka kot levo ──
        # Uporabimo place() da ikona zapolni preostali prostor desno
        self.frm_aktivna_iko=tk.Frame(top,bg=c["CARD2"])
        self.frm_aktivna_iko.pack(side="left",fill="y",padx=(4,0))
        self._aktivna_iko_ph=None
        # Minimalna širina = višina (kvadrat) — posodobimo po pack z after
        self.after(10, self._popravi_aktivno_ikono_vel)

        self.after(100,self._posodobi_aktivno_ikono)

        # ════════════════════════════════════════════════════════════
        # SREDINA: Play / Stop / Timer  (nad ikonami)
        # ════════════════════════════════════════════════════════════
        sep=tk.Frame(self,bg=c["CARD2"],height=1); sep.pack(fill="x",padx=14,pady=(3,3))

        # Play / Stop + Timer v eni vrstici
        bot=tk.Frame(self,bg=c["BG"]); bot.pack(fill="x",padx=14,pady=(0,3))

        self.btn_play=tk.Button(bot,text=self.t("play"),font=F,
                                bg=c["GREEN"],fg=c["BTN_FG"],activebackground=c["CARD2"],
                                relief="flat",padx=10,pady=5,cursor="hand2",command=self._play)
        self.btn_play.pack(side="left",padx=(0,3))

        self.btn_stop=tk.Button(bot,text=self.t("stop"),font=F,
                                bg=c["CARD2"],fg=c["FG"],activebackground=c["CARD"],
                                relief="flat",padx=10,pady=5,cursor="hand2",command=self._stop)
        self.btn_stop.pack(side="left",padx=(0,12))

        # Timer – v isti vrstici
        tk.Label(bot,text=self.t("timer_lbl"),font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left")
        self.var_timer=tk.StringVar(value=str(self.nas.get("timer_min",30) or 30))
        sp=tk.Spinbox(bot,from_=1,to=240,textvariable=self.var_timer,
                      width=4,font=F,bg=c["CARD"],fg=c["FG"],
                      buttonbackground=c["CARD2"],relief="flat",bd=2,
                      insertbackground=c["FG"])
        sp.pack(side="left",padx=(4,2))
        self._dodaj_kontekstni_meni_spinbox(sp)
        tk.Label(bot,text="min",font=FK,bg=c["BG"],fg=c["MUTED"]).pack(side="left",padx=(0,5))
        tk.Button(bot,text=self.t("timer_start"),font=F,bg=c["GREEN"],fg=c["BTN_FG"],
                  relief="flat",padx=8,pady=5,cursor="hand2",
                  command=self._timer_start).pack(side="left",padx=(0,3))
        self.btn_timer_stop=tk.Button(bot,text=self.t("timer_stop"),font=F,
                                       bg=c["CARD2"],fg=c["FG"],
                                       relief="flat",padx=8,pady=5,cursor="hand2",
                                       command=self._timer_cancel)
        self.btn_timer_stop.pack(side="left",padx=(0,8))
        # Utišaj pred izklopom — takoj desno od × gumba
        self.var_fade=tk.BooleanVar(value=True)
        tk.Checkbutton(bot,text=self.t("timer_fade"),variable=self.var_fade,
                       bg=c["BG"],fg=c["MUTED"],selectcolor=c["CARD2"],
                       activebackground=c["BG"],font=FK,relief="flat").pack(side="left")
        # Timer odštevanje — desno v isti vrstici
        self.lbl_timer=tk.Label(bot,text="",font=FS,bg=c["BG"],fg=c["LIVE"])
        self.lbl_timer.pack(side="right")

        # ════════════════════════════════════════════════════════════
        # SPODAJ: Ikone postaj
        # ════════════════════════════════════════════════════════════
        sep2=tk.Frame(self,bg=c["CARD2"],height=1); sep2.pack(fill="x",padx=14,pady=(2,3))

        self.frm_outer=tk.Frame(self,bg=c["BG"])
        self.frm_outer.pack(fill="x",pady=(0,3))
        self.frm_gumbi=tk.Frame(self.frm_outer,bg=c["BG"])
        self.frm_gumbi.pack(anchor="center")
        self._naredi_gumbe()

        self.lbl_status=tk.Label(self,text=self.t("stopped"),font=FK,bg=c["BG"],fg=c["MUTED"])
        self.lbl_status.pack(pady=(0,4))

        self.geometry("700x660")
        # Posodobi wraplength naslova ob spremembi širine
        self.bind("<Configure>", self._on_resize)
        # Scroll kolesa = glasnost — samo ko je miška nad drsnikom
        self.sl_gl_main.bind("<Button-4>",   self._on_scroll_vol)
        self.sl_gl_main.bind("<Button-5>",   self._on_scroll_vol)
        self.sl_gl_main.bind("<MouseWheel>", self._on_scroll_vol)

    def _popravi_aktivno_ikono_vel(self):
        """Nastavi širino ikone aktivne postaje = višina (kvadrat)."""
        try:
            h = self.frm_aktivna_iko.winfo_height()
            if h > 10:
                self.frm_aktivna_iko.config(width=h)
                self._posodobi_aktivno_ikono()
            else:
                self.after(50, self._popravi_aktivno_ikono_vel)
        except Exception:
            pass

    def _spanje_monitor(self):
        """Zazna prebujanje sistema iz spanja in znova zažene predvajanje."""
        import time as _time
        INTERVAL = 10   # sekund med preverjanji
        PRAG     = 30   # če je zamuda > 30s → sistem je spal
        zadnji   = _time.monotonic()
        while True:
            _time.sleep(INTERVAL)
            zdaj = _time.monotonic()
            zamuda = zdaj - zadnji - INTERVAL
            if zamuda > PRAG:
                # Sistem se je prebudil iz spanja
                if self._predvajal_pred_spanjem and not self.predvaja:
                    self.after(0, self._play_po_prebujanju)
                self._predvajal_pred_spanjem = False
            zadnji = zdaj

    def _play_po_prebujanju(self):
        """Zažene predvajanje po prebujanju iz spanja."""
        try:
            # Počakaj sekundo da se omrežje vzpostavi
            self.after(3000, self._play)
        except Exception:
            pass

    def _on_scroll_vol(self, event):
        """Scroll kolesa miške NA DRSNIKU = glasnost ±2%."""
        try:
            korak = 2
            if event.num == 4 or (hasattr(event,"delta") and event.delta > 0):
                nova = min(100, self.sl_gl_main.get() + korak)
            else:
                nova = max(0,   self.sl_gl_main.get() - korak)
            self.sl_gl_main.set(nova)
            self._on_gl_main(nova)
        except Exception: pass

    def _on_resize(self, event):
        """Prilagodi wraplength naslova pesmi glede na širino okna."""
        if event.widget is not self: return
        try:
            w = event.width - 280
            if w > 100:
                self.lbl_naslov.config(wraplength=max(100, w))
        except Exception:
            pass

    def _k(self,naslov):
        c=self.c; f=tk.Frame(self,bg=c["CARD"],padx=14,pady=8)
        f.pack(fill="x",padx=14,pady=2)
        tk.Label(f,text=naslov,font=self.fnt["FK"],bg=c["CARD"],fg=c["MUTED"]).pack(anchor="w")
        return f

    def _style(self):
        c=self.c; s=ttk.Style(); s.theme_use("clam")
        s.configure("R.TCombobox",
                    fieldbackground=c["CARD"],background=c["CARD"],
                    foreground=c["FG"],selectbackground=c["CARD"],
                    selectforeground=c["ACCENT"],arrowcolor=c["ACCENT"],
                    borderwidth=0,padding=5)

    # ── Icon buttons ──────────────────────────────────────────────────────────

    def _zaobljeni_gumb_ikona(self, parent, ph, prazna, c):
        """Canvas z zaobljenim kvadratkom in ikono čez cel gumb."""
        r = ICON_RADIUS
        w = BTN_SZ; h = BTN_SZ
        bg_main = parent.cget("bg")
        cv = tk.Canvas(parent, width=w, height=h, bg=bg_main,
                       highlightthickness=0, bd=0)
        fill = c["ICON_BG"] if not prazna else c["CARD2"]
        # Zaobljeni pravokotnik
        cv.create_arc(0,0,2*r,2*r, start=90, extent=90, fill=fill, outline=fill)
        cv.create_arc(w-2*r,0,w,2*r, start=0, extent=90, fill=fill, outline=fill)
        cv.create_arc(0,h-2*r,2*r,h, start=180, extent=90, fill=fill, outline=fill)
        cv.create_arc(w-2*r,h-2*r,w,h, start=270, extent=90, fill=fill, outline=fill)
        cv.create_rectangle(r,0,w-r,h, fill=fill, outline=fill)
        cv.create_rectangle(0,r,w,h-r, fill=fill, outline=fill)
        if ph:
            cv.create_image(w//2, h//2, image=ph, anchor="center")
        return cv

    def _naredi_gumbe(self):
        for w in self.frm_gumbi.winfo_children(): w.destroy()
        c=self.c
        rows    = self.nas.get("icon_rows",2)
        max_btn = PER_ROW * rows   # 8 or 16
        LBL_H   = 16  # višina besedila pod gumbom

        for idx in range(max_btn):
            row = idx // PER_ROW
            col = idx % PER_ROW
            p   = self.postaje[idx] if idx < len(self.postaje) else None

            # Zunanji frame: gumb + ime pod njim
            outer=tk.Frame(self.frm_gumbi,bg=c["BG"])
            outer.grid(row=row,column=col,padx=3,pady=(3,1))

            if p is None or not p.get("url",""):
                # Prazen placeholder
                ph=ikona_prazna(ICON_SZ,c)
                cv=self._zaobljeni_gumb_ikona(outer,ph,True,c)
                cv.pack()
                cv._ph=ph
                tk.Label(outer,text="",font=self.fnt["FK"],
                         bg=c["BG"],fg=c["MUTED"],width=9,anchor="center").pack()
                continue

            ime=p["ime"]; b64=p.get("ikona","")
            if ime not in self._ikone:
                ph=None
                if b64: ph=ikona_iz_base64(b64,(ICON_SZ,ICON_SZ))
                if not ph: ph=ikona_inicialke(ime,ICON_SZ,c)
                self._ikone[ime]=ph
            ph=self._ikone[ime]

            def mk(n): return lambda:self._play_postaja(n)

            cv=self._zaobljeni_gumb_ikona(outer,ph,False,c)
            cv.pack()
            cv._ph=ph
            cv.config(cursor="hand2")
            ime_cmd=ime
            cv.bind("<Button-1>", lambda e,n=ime_cmd: self._play_postaja(n))
            cv.bind("<Enter>",  lambda e,cv=cv,c=c: cv.configure(bg=c["CARD2"]))
            cv.bind("<Leave>",  lambda e,cv=cv,bg=outer.cget("bg"): cv.configure(bg=bg))

            # Ime pod gumbom
            tk.Label(outer,text=ime[:10],font=self.fnt["FK"],
                     bg=c["BG"],fg=c["FG"],width=9,anchor="center").pack()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _posodobi_aktivno_ikono(self):
        """Prikaže ikono aktivne postaje – velikost = višina okvirja (kvadrat)."""
        c=self.c
        ime=self.var_postaja.get()
        b64=""
        for p in self.postaje:
            if p["ime"]==ime:
                b64=p.get("ikona",""); break

        for w in self.frm_aktivna_iko.winfo_children():
            w.destroy()

        # Dinamična velikost: uporabi dejanski winfo_height, min 80
        sz = max(80, self.frm_aktivna_iko.winfo_height())
        self.frm_aktivna_iko.config(width=sz)  # kvadrat

        ph=None
        if b64:
            try:
                b64c=_ocisti_b64(b64)
                if not b64c: raise ValueError("invalid")
                raw=b64c.split(",",1)[1] if b64c.startswith("data:") else b64c
                img=_pravilna_rgba(Image.open(io.BytesIO(base64.b64decode(raw))))
                img=img.resize((sz,sz),Image.LANCZOS)
                ph=ImageTk.PhotoImage(img)
                self._aktivna_iko_ph=ph
                lbl=tk.Label(self.frm_aktivna_iko,image=ph,bg=c["CARD2"],bd=0)
                lbl.image=ph
                lbl.place(relx=0.5,rely=0.5,anchor="center")
            except Exception:
                ph=None

        if not ph:
            fs=max(14,sz//5)
            krac=ime[:3].upper() if ime else "?"
            tk.Label(self.frm_aktivna_iko,text=krac,
                     font=("TkDefaultFont",fs,"bold"),
                     bg=c["CARD2"],fg=c["MUTED"]).place(relx=0.5,rely=0.5,anchor="center")

    def _prejsnja_postaja(self):
        imen=[p["ime"] for p in self.postaje]
        if not imen: return
        try: idx=imen.index(self.var_postaja.get())
        except ValueError: idx=0
        nova=imen[(idx-1) % len(imen)]
        self.var_postaja.set(nova)
        if self.predvaja: self._play()

    def _naslednja_postaja(self):
        imen=[p["ime"] for p in self.postaje]
        if not imen: return
        try: idx=imen.index(self.var_postaja.get())
        except ValueError: idx=-1
        nova=imen[(idx+1) % len(imen)]
        self.var_postaja.set(nova)
        if self.predvaja: self._play()

    def _posodobi_kw_indikator(self, aktiven):
        """Obarva kw indikator glede na to ali je govor aktiven."""
        c=self.c
        kw=self.nas.get("kljucna_beseda","Govorna vsebina")
        # Pokaži samo prvih 20 znakov ključne besede
        kw_prikaz=kw.split(";")[0][:22]+"…" if len(kw.split(";")[0])>22 else kw.split(";")[0]
        if aktiven:
            self.frm_kw_ind.config(bg=c["LIVE"])
            self.lbl_kw_ind.config(text=f"🎙 {kw_prikaz}",bg=c["LIVE"],fg="#ffffff")
        else:
            self.frm_kw_ind.config(bg=c["CARD2"])
            self.lbl_kw_ind.config(text=f"○ {kw_prikaz}",bg=c["CARD2"],fg=c["MUTED"])

    def _play_postaja(self,ime):
        self.var_postaja.set(ime); self._play()

    def _play(self):
        ime=self.var_postaja.get()
        url=next((p["url"] for p in self.postaje if p["ime"]==ime),"")
        if not url: return
        if self.meta: self.meta.stop()
        self.player.ustavi()
        if self.govor_aktiven: self.gl_obj.set(self.izvorna_gl); self.govor_aktiven=False
        if not self.player.na_voljo:
            messagebox.showerror(APP_NAME,
                "mpv ni nameščen!\nLinux: sudo apt install mpv\n"
                "Windows: mpv.exe v isto mapo kot radiola.py"); return
        threading.Thread(target=self.player.predvajaj,args=(url,),daemon=True).start()
        self.meta=MetadataBralnik(url,self._on_meta); self.meta.start()
        self.predvaja=True
        self._predvajal_pred_spanjem=True
        self.lbl_status.config(text=self.t("live")+ime,fg=self.c["LIVE"])
        self.btn_play.config(bg=self.c["CARD2"],fg=self.c["FG"])
        self.btn_stop.config(bg=self.c["RED"],fg=self.c["BTN_FG"])
        self.nas["zadnja_postaja"]=ime; self._shrani_nas()
        self.after(400,self._vrni_fokus)
        self.after(100,self._posodobi_aktivno_ikono)

    def _stop(self):
        if self.meta: self.meta.stop()
        self._stop_gl.set()
        if self.govor_aktiven: self.gl_obj.set(self.izvorna_gl); self.govor_aktiven=False
        self.player.ustavi(); self.predvaja=False
        self.lbl_status.config(text=self.t("stopped"),fg=self.c["MUTED"])
        self.lbl_naslov.config(text="—"); self.lbl_govor.config(text="")
        self.btn_play.config(bg=self.c["GREEN"],fg=self.c["BTN_FG"])
        self.btn_stop.config(bg=self.c["CARD2"],fg=self.c["FG"])

    def _postaja_change(self):
        if self.predvaja: self._play()

    def _vrni_fokus(self):
        try:
            self.lift(); self.focus_force()
            if OS=="Windows":
                self.wm_attributes("-topmost",True)
                self.after(500,lambda:self.wm_attributes("-topmost",False))
        except Exception: pass

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _timer_start(self):
        try: m=int(self.var_timer.get())
        except: return
        if m<=0: return
        self._timer_sek=m*60; self._timer_running=True
        self.lbl_timer.config(fg=self.c["LIVE"])
        self.btn_timer_stop.config(bg=self.c["RED"],fg=self.c["BTN_FG"])
        self._timer_tick()

    def _timer_cancel(self):
        self._timer_running=False
        if self._timer_after: self.after_cancel(self._timer_after); self._timer_after=None
        self.lbl_timer.config(text="")
        try: self.btn_timer_stop.config(bg=self.c["CARD2"],fg=self.c["FG"])
        except Exception: pass
        if self.predvaja:
            threading.Thread(target=self.gl_obj.set,
                             args=(self.nas["glasnost"],),daemon=True).start()

    def _timer_tick(self):
        if not self._timer_running: return
        if self._timer_sek<=0:
            self.lbl_timer.config(text=""); self._timer_running=False; self._stop(); return
        m,s=divmod(self._timer_sek,60)
        self.lbl_timer.config(text=f"⏱ {m:02d}:{s:02d}")
        if self.var_fade.get() and self._timer_sek<=60 and self.predvaja:
            threading.Thread(target=self.gl_obj.set,
                             args=(max(0.0,self.nas["glasnost"]*self._timer_sek/60),),
                             daemon=True).start()
        self._timer_sek-=1
        self._timer_after=self.after(1000,self._timer_tick)

    # ── Stations ──────────────────────────────────────────────────────────────

    def _uredi_postaje(self):
        UrejevalnikPostaj(self,self.postaje,self.c,self.fnt,self.lang,self._on_postaje_saved)

    def _on_postaje_saved(self,nove):
        self.postaje=nove
        self.cb["values"]=[p["ime"] for p in nove]
        if self.var_postaja.get() not in [p["ime"] for p in nove]:
            self.var_postaja.set(nove[0]["ime"] if nove else "")
        self._ikone.clear()
        self._naredi_gumbe()
        self.after(100,self._posodobi_aktivno_ikono)

    def _shrani_nas(self,d=None):
        if d: self.nas.update(d)
        try: self.nas["avto_predvajaj"]=self.var_avto.get()
        except Exception: pass
        shrani_settings(self.nas)

    # ── Keywords ──────────────────────────────────────────────────────────────

    def _get_keywords(self):
        ime=self.var_postaja.get()
        for p in self.postaje:
            if p["ime"]==ime:
                sk=p.get("kw","").strip()
                if sk: return [k.strip() for k in sk.split(";") if k.strip()]
        gk=self.nas.get("kljucna_beseda","Govorna vsebina")
        return [k.strip() for k in gk.split(";") if k.strip()]

    # ── Inline glasnost + dvig kontrolniki ──────────────────────────────────────

    def _narisi_dvig_chk(self):
        """Nariše kljukico: zelen kvadrat = aktiven, rdeč = izklopljen."""
        cv=self.cv_dvig_chk; cv.delete("all")
        BOX=20; r=4; c=self.c
        fill = c["LIVE"] if self._dvig_aktiven else c.get("RED","#cc2200")
        # Zaobljeni pravokotnik
        cv.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
        cv.create_arc(BOX-2*r,0,BOX,2*r,start=0,extent=90,fill=fill,outline=fill)
        cv.create_arc(0,BOX-2*r,2*r,BOX,start=180,extent=90,fill=fill,outline=fill)
        cv.create_arc(BOX-2*r,BOX-2*r,BOX,BOX,start=270,extent=90,fill=fill,outline=fill)
        cv.create_rectangle(r,0,BOX-r,BOX,fill=fill,outline=fill)
        cv.create_rectangle(0,r,BOX,BOX-r,fill=fill,outline=fill)
        if self._dvig_aktiven:
            # Kljukica
            cv.create_line(4,10, 9,15, 16,5, width=2,fill="#ffffff",capstyle="round",joinstyle="round")
        else:
            # × 
            cv.create_line(5,5,15,15,width=2,fill="#ffffff",capstyle="round")
            cv.create_line(15,5,5,15,width=2,fill="#ffffff",capstyle="round")

    def _toggle_dvig_chk(self, _=None):
        """Preklopi aktivnost dviga glasnosti."""
        self._dvig_aktiven = not self._dvig_aktiven
        if self._dvig_aktiven:
            # Obnovi vrednost iz drsnika
            v = self.sl_dvig_main.get() / 100
            if v <= 0:
                self.sl_dvig_main.set(30); v=0.30
            self.nas["dvig"] = v
        else:
            self.nas["dvig"] = 0.0
        self._narisi_dvig_chk()
        shrani_settings(self.nas)

    def _on_gl_main(self, val):
        """Drsnik glasnosti v glavnem oknu."""
        v = float(val)/100
        self.nas["glasnost"] = v
        try: self.gl_obj.set(v)
        except Exception: pass
        self.var_gl_lbl.set(f"{int(float(val))}%")
        shrani_settings(self.nas)

    def _on_dvig_main(self, val):
        """Drsnik za ojačanje pri govoru v glavnem oknu."""
        v = float(val)/100
        self.var_dvig_lbl.set(f"+{int(float(val))}%")
        if self._dvig_aktiven:
            self.nas["dvig"] = v
            shrani_settings(self.nas)

    def _vsebuje_kw(self,naslov):
        """Vrne True če naslov vsebuje katerokoli od ključnih besed (podbesedilo)."""
        if not naslov: return False
        nl=naslov.lower()
        return any(k.lower() in nl for k in self._get_keywords())

    # ── Metadata ──────────────────────────────────────────────────────────────

    def _on_meta(self,naslov):
        self.after(0,self._gui_update,naslov)
        threading.Thread(target=self._gl_logika,args=(naslov,),daemon=True).start()

    def _gui_update(self,naslov):
        self.lbl_naslov.config(text=naslov or "—")
        aktiven=self._vsebuje_kw(naslov)
        self.lbl_govor.config(text=self.t("speech_on") if aktiven else "")
        self._posodobi_kw_indikator(aktiven)

    def _gl_logika(self,naslov):
        self._stop_gl.clear()
        if self._vsebuje_kw(naslov):
            if not self.govor_aktiven:
                self.izvorna_gl=self.gl_obj.get()
                # kw_glasnost: absolutna glasnost pri govoru (0=ne uporabi)
                kw_gl=self.nas.get("kw_glasnost",0.0)
                cilj=(kw_gl if kw_gl>0 else
                      min(1.0,self.izvorna_gl+self.nas.get("dvig",0.3)))
                self.gl_obj.gladko(self.izvorna_gl,cilj,self._stop_gl)
                self.govor_aktiven=True
        else:
            if self.govor_aktiven:
                self.gl_obj.gladko(self.gl_obj.get(),self.izvorna_gl,self._stop_gl)
                self.govor_aktiven=False

    def on_close(self):
        self._timer_cancel(); self._shrani_nas(); self._stop(); self.destroy()


if __name__=="__main__":
    app=App()
    app.protocol("WM_DELETE_WINDOW",app.on_close)
    app.mainloop()
