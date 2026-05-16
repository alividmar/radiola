# -*- mode: python ; coding: utf-8 -*-
# radiola.spec — PyInstaller konfiguracija za Radiola
# Poganjanje: pyinstaller radiola.spec

import sys, os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Zaznaj platformo ──────────────────────────────────────────────────────────
IS_WIN   = sys.platform == "win32"
IS_MAC   = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# ── Zberi podatke ─────────────────────────────────────────────────────────────
datas = []
datas += collect_data_files("PIL")          # Pillow
datas += collect_data_files("tkinter")      # tkinter

# Dodaj ICONS mapo če obstaja
if os.path.isdir("ICONS"):
    datas.append(("ICONS", "ICONS"))

# Privzeti stations.json (prazen seznam — vsak si ga ustvari sam)
if os.path.isfile("stations_default.json"):
    datas.append(("stations_default.json", "."))

# Ikona aplikacije
icon_file = None
if IS_WIN and os.path.isfile("radiola.ico"):
    icon_file = "radiola.ico"
elif IS_MAC and os.path.isfile("radiola.icns"):
    icon_file = "radiola.icns"
elif IS_LINUX and os.path.isfile("radiola.png"):
    icon_file = "radiola.png"

# ── Skrite odvisnosti ─────────────────────────────────────────────────────────
hiddenimports = [
    "PIL._tkinter_finder",
    "PIL.Image", "PIL.ImageTk", "PIL.ImageDraw", "PIL.ImageFont",
    "tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.filedialog",
    "urllib.request", "urllib.parse", "urllib.error",
    "json", "base64", "threading", "subprocess",
    "platform", "shutil", "socket", "random",
]

# requests je opcijski
try:
    import requests
    hiddenimports += ["requests", "requests.adapters", "requests.auth",
                      "requests.models", "urllib3"]
except ImportError:
    pass

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ["radiola.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "numpy", "scipy", "pandas",
        "IPython", "jupyter", "notebook",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "wx", "gi",
        "test", "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE / binarni izhod ───────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Radiola",
    debug=False,
    bootloader_ignore_signals=False,
    strip=IS_LINUX or IS_MAC,
    upx=True,
    upx_exclude=[],
    console=False,       # brez konzolnega okna (GUI aplikacija)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# ── Collect (mapa z vsemi datotekami) ─────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=IS_LINUX or IS_MAC,
    upx=True,
    upx_exclude=[],
    name="Radiola",
)

# ── macOS .app bundle (samo na Macu) ──────────────────────────────────────────
if IS_MAC:
    app = BUNDLE(
        coll,
        name="Radiola.app",
        icon=icon_file,
        bundle_identifier="si.radiola.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.14",
            "CFBundleShortVersionString": "1.4.0",
            "CFBundleVersion": "1.4.0",
        },
    )
