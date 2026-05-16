#!/usr/bin/env python3
"""
build.py — Avtomatski build skript za Radiola
=============================================
Zaženi: python3 build.py

Podpira:
  Windows → Radiola.exe (in dist/Radiola/)
  Linux   → Radiola binarni + AppImage (opcijsko)
  macOS   → Radiola.app

Zahteve:
  pip install pyinstaller pillow requests
  Linux AppImage: snap install appimagetool (opcijsko)
"""

import sys, os, shutil, subprocess, platform, zipfile, urllib.request

OS      = platform.system()
VERSION = "1.4.0"
APPNAME = "Radiola"
DIST    = os.path.join("dist", APPNAME)
BUILD   = "build"

# ── Barve za terminal ──────────────────────────────────────────────────────────
GREEN  = "\033[92m" if OS != "Windows" else ""
YELLOW = "\033[93m" if OS != "Windows" else ""
RED    = "\033[91m" if OS != "Windows" else ""
RESET  = "\033[0m"  if OS != "Windows" else ""

def ok(msg):   print(f"{GREEN}  ✓ {msg}{RESET}")
def warn(msg): print(f"{YELLOW}  ⚠ {msg}{RESET}")
def err(msg):  print(f"{RED}  ✗ {msg}{RESET}"); sys.exit(1)
def step(msg): print(f"\n{YELLOW}▶ {msg}{RESET}")

# ── 1. Preveri odvisnosti ─────────────────────────────────────────────────────
step("Preverjam odvisnosti...")

def check_pkg(name, import_name=None):
    try:
        __import__(import_name or name)
        ok(name)
        return True
    except ImportError:
        warn(f"{name} ni nameščen → pip install {name}")
        return False

pyinstaller_ok = check_pkg("PyInstaller")
pillow_ok      = check_pkg("Pillow", "PIL")
requests_ok    = check_pkg("requests")

if not pyinstaller_ok:
    err("PyInstaller je obvezen: pip install pyinstaller")
if not pillow_ok:
    err("Pillow je obvezen: pip install pillow")
if not requests_ok:
    warn("requests ni nameščen — RapidAPI in favicon ne bosta delovala")

# ── 2. Preveri da radiola.py obstaja ─────────────────────────────────────────
step("Preverjam izvorno kodo...")
if not os.path.isfile("radiola.py"):
    err("radiola.py ni v trenutni mapi! Zaženi build.py iz mape Radiole.")
ok("radiola.py najden")

# ── 3. Počisti stari build ────────────────────────────────────────────────────
step("Čistim stare build datoteke...")
for d in [DIST, BUILD, "__pycache__"]:
    if os.path.isdir(d):
        shutil.rmtree(d)
        ok(f"Odstranil {d}/")

# ── 4. Generiraj radiola.ico za Windows (iz PNG če obstaja) ──────────────────
if OS == "Windows" and not os.path.isfile("radiola.ico"):
    step("Generiram Windows ikono...")
    try:
        from PIL import Image
        # Ustvari preprosto ikono (krožek z R)
        sizes = [16, 32, 48, 64, 128, 256]
        imgs = []
        for s in sizes:
            img = Image.new("RGBA", (s,s), (204,34,0,255))
            imgs.append(img)
        imgs[0].save("radiola.ico", format="ICO", sizes=[(s,s) for s in sizes],
                     append_images=imgs[1:])
        ok("radiola.ico ustvarjen")
    except Exception as e:
        warn(f"Ikona ni bila ustvarjena: {e}")

# ── 5. Zaženi PyInstaller ─────────────────────────────────────────────────────
step("Gradim aplikacijo s PyInstaller...")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "radiola.spec",
    "--clean",
    "--noconfirm",
]
print(f"  Ukaz: {' '.join(cmd)}\n")

result = subprocess.run(cmd)
if result.returncode != 0:
    err("PyInstaller je naletel na napako!")
ok("PyInstaller uspešno zaključen")

# ── 6. Pospravi dist/ mapo ────────────────────────────────────────────────────
step("Pripravljam distribucijsko mapo...")

# Ustvari ICONS mapo
icons_dst = os.path.join(DIST, "ICONS")
os.makedirs(icons_dst, exist_ok=True)
with open(os.path.join(icons_dst, ".gitkeep"), "w") as f:
    f.write("# Sem daj ikone postaj (.png/.jpg)\n")
ok("ICONS/ mapa ustvarjena")

# Dodaj README za distribucijo
readme_content = f"""# {APPNAME} v{VERSION}

## Zagon
"""
if OS == "Windows":
    readme_content += "Dvoklikni **Radiola.exe**\n\n"
elif OS == "Darwin":
    readme_content += "Odpri **Radiola.app**\n\n"
else:
    readme_content += "V terminalu: **./Radiola**\n\n"

readme_content += """## Predvajalnik (obvezno)
Radiola potrebuje mpv za predvajanje avdia.

"""
if OS == "Windows":
    readme_content += "Prenesi mpv.exe z https://mpv.io/installation/ in ga daj v to mapo.\n"
elif OS == "Darwin":
    readme_content += "brew install mpv\n"
else:
    readme_content += "sudo apt install mpv\n"

readme_content += f"""
## Ikone postaj
Daj .png/.jpg ikone v mapo ICONS/ — Radiola jih samodejno ponudi pri izbiri ikone.

## Datoteke
- stations.json  — seznam postaj (ustvari se samodejno)
- settings.json  — nastavitve (ustvari se samodejno)
- ICONS/         — mapa za ikone postaj

## Verzija
{APPNAME} v{VERSION} | https://github.com/TvojeIme/radiola
"""

with open(os.path.join(DIST, "PREBERI_ME.txt" if OS!="Windows" else "README.txt"), "w", encoding="utf-8") as f:
    f.write(readme_content)
ok("README ustvarjen")

# ── 7. Pakiranje v ZIP / tar.gz ───────────────────────────────────────────────
step("Pakiranje distribucije...")

if OS == "Windows":
    zip_name = f"Radiola-{VERSION}-Windows.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DIST):
            for file in files:
                fp = os.path.join(root, file)
                arcname = os.path.relpath(fp, os.path.dirname(DIST))
                zf.write(fp, arcname)
    ok(f"Ustvarjen: {zip_name}")
    pkg_file = zip_name

else:
    import tarfile
    tar_name = f"Radiola-{VERSION}-{'Linux' if OS=='Linux' else 'macOS'}.tar.gz"
    with tarfile.open(tar_name, "w:gz") as tf:
        tf.add(DIST, arcname=APPNAME)
    ok(f"Ustvarjen: {tar_name}")
    pkg_file = tar_name

# ── 8. AppImage za Linux (opcijsko) ───────────────────────────────────────────
if OS == "Linux":
    step("Preverjam za AppImage gradnjo...")
    if shutil.which("appimagetool") or shutil.which("appimagetool-x86_64.AppImage"):
        _build_appimage()
    else:
        warn("appimagetool ni nameščen — AppImage preskočen")
        warn("Za AppImage: snap install appimagetool --classic")

def _build_appimage():
    """Zgradi Linux AppImage."""
    appdir = f"{APPNAME}.AppDir"
    if os.path.isdir(appdir):
        shutil.rmtree(appdir)
    os.makedirs(f"{appdir}/usr/bin", exist_ok=True)
    os.makedirs(f"{appdir}/usr/share/applications", exist_ok=True)
    os.makedirs(f"{appdir}/usr/share/icons", exist_ok=True)

    # Kopiraj dist/ v AppDir
    shutil.copytree(DIST, f"{appdir}/usr/bin/Radiola_data")

    # AppRun skripta
    with open(f"{appdir}/AppRun", "w") as f:
        f.write('#!/bin/bash\n')
        f.write('APPDIR="$(dirname "$(readlink -f "$0")")"\n')
        f.write('"$APPDIR/usr/bin/Radiola_data/Radiola" "$@"\n')
    os.chmod(f"{appdir}/AppRun", 0o755)

    # .desktop datoteka
    with open(f"{appdir}/usr/share/applications/radiola.desktop", "w") as f:
        f.write("[Desktop Entry]\n")
        f.write(f"Name={APPNAME}\n")
        f.write("Type=Application\n")
        f.write("Exec=Radiola\n")
        f.write("Icon=radiola\n")
        f.write("Categories=Audio;Music;\n")
        f.write("Comment=Internet Radio Player\n")
    shutil.copy(f"{appdir}/usr/share/applications/radiola.desktop", f"{appdir}/radiola.desktop")

    # Zaženi appimagetool
    tool = shutil.which("appimagetool") or shutil.which("appimagetool-x86_64.AppImage")
    appimage_name = f"Radiola-{VERSION}-x86_64.AppImage"
    subprocess.run([tool, appdir, appimage_name], check=True)
    shutil.rmtree(appdir)
    ok(f"AppImage: {appimage_name}")

# ── 9. Zaključek ──────────────────────────────────────────────────────────────
print(f"""
{GREEN}══════════════════════════════════════════════════
  ✓ BUILD USPEŠEN — Radiola v{VERSION}
══════════════════════════════════════════════════{RESET}

  Distribucijska mapa:  dist/Radiola/
  Paket za distribucijo: {pkg_file}

  Naslednji koraki:
  1. Testiraj dist/Radiola/{'Radiola.exe' if OS=='Windows' else 'Radiola'}
  2. Namesti mpv na ciljnem računalniku
  3. Daj ZIP/tar.gz v GitHub Releases
""")
