# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['sonosplay.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['soco', 'soco.services', 'soco.core', 'soco.discovery', 'soco.music_services', 'soco.data_structures', 'soco.events', 'soco.events_base', 'soco.groups', 'soco.utils', 'soco.xml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SonosPlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Client\\Documents\\GitHub\\sonosplay\\icon.ico'],
)
