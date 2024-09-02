# -*- mode: python ; coding: utf-8 -*-


mp_a = Analysis(
    ['main_prog.py'],
    pathex=[],
    binaries=[],
    datas=[('asset', 'asset')],
    hiddenimports=['openpyxl.cell._writer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
mp_pyz = PYZ(mp_a.pure)

mp_exe = EXE(
    mp_pyz,
    mp_a.scripts,
    [],
    exclude_binaries=True,
    name='CIP_IRT',
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
	icon='asset/irt.ico',
)

is_a = Analysis(
    ['import_settings.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['openpyxl.cell._writer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
is_pyz = PYZ(is_a.pure)

is_exe = EXE(
    is_pyz,
    is_pyz.scripts,
    [],
    exclude_binaries=True,
    name='IRT_SettingsImporter',
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
	icon='asset/irt_si.ico',
)

coll = COLLECT(
    mp_exe,
    mp_a.binaries,
    mp_a.zipfiles,
    mp_a.datas,
    is_exe,
    is_a.binaries,
    is_a.zipfiles,
    is_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CIP Inventory Resource Tracker',
)
