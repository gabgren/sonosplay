#!/usr/bin/env python3
"""Build SonosPlay into a standalone desktop app using PyInstaller.

Usage:
    macOS:   python3 build.py   -> dist/SonosPlay.app
    Windows: python build.py    -> dist/SonosPlay.exe
"""

import os
import platform
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_pyinstaller():
    """Install PyInstaller if it isn't already available."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found — installing…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def ensure_icon():
    """Generate icon files if they don't exist yet."""
    icns = os.path.join(SCRIPT_DIR, "icon.icns")
    ico = os.path.join(SCRIPT_DIR, "icon.ico")
    if not os.path.exists(icns) or not os.path.exists(ico):
        print("Icon files not found — generating…")
        subprocess.check_call([sys.executable, os.path.join(SCRIPT_DIR, "generate_icon.py")])


def build():
    ensure_pyinstaller()
    ensure_icon()

    system = platform.system()
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SonosPlay",
        "--windowed",
        "--noconfirm",
        "--hidden-import", "soco",
        "--hidden-import", "soco.services",
        "--hidden-import", "soco.core",
        "--hidden-import", "soco.discovery",
        "--hidden-import", "soco.music_services",
        "--hidden-import", "soco.data_structures",
        "--hidden-import", "soco.events",
        "--hidden-import", "soco.events_base",
        "--hidden-import", "soco.groups",
        "--hidden-import", "soco.utils",
        "--hidden-import", "soco.xml",
    ]

    if system == "Windows":
        args.extend(["--onefile", "--icon", os.path.join(SCRIPT_DIR, "icon.ico")])
        print("Building single-file .exe for Windows…")
    elif system == "Darwin":
        args.extend(["--icon", os.path.join(SCRIPT_DIR, "icon.icns")])
        # On macOS, skip --onefile to get a proper .app bundle
        print("Building .app bundle for macOS…")
    else:
        args.append("--onefile")
        print(f"Building for {system} (onefile mode)…")

    args.append("sonosplay.py")

    print(f"Running: {' '.join(args)}\n")
    subprocess.check_call(args)

    if system == "Darwin":
        print("\n✓ Build complete: dist/SonosPlay.app")
    elif system == "Windows":
        print("\n✓ Build complete: dist/SonosPlay.exe")
    else:
        print("\n✓ Build complete: dist/SonosPlay")


if __name__ == "__main__":
    build()
