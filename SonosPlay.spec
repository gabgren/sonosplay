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
    [],
    exclude_binaries=True,
    name='SonosPlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/gabgren/Documents/GitHub/sonosplay/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SonosPlay',
)
app = BUNDLE(
    coll,
    name='SonosPlay.app',
    icon='/Users/gabgren/Documents/GitHub/sonosplay/icon.icns',
    bundle_identifier=None,
)
