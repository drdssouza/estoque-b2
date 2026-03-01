# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Controle B2 — modo onedir (pasta)
# O Inno Setup vai empacotar essa pasta num único instalador .exe

block_cipher = None

a = Analysis(
    ['desktop/app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('desktop/assets', 'desktop/assets'),
        ('version.py', '.'),
    ],
    hiddenimports=[
        'pandas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.timedeltas',
        'pyarrow',
        'pyarrow.vendored.version',
        'pyarrow._parquet',
        'openpyxl',
        'openpyxl.cell._writer',
        'reportlab',
        'reportlab.graphics.barcode.code39',
        'reportlab.graphics.barcode.code93',
        'pkg_resources.py2_compat',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'fastapi',
        'uvicorn',
        'pyjwt',
        'python_multipart',
        'pytest',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='estoque-b2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                  # sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='estoque-b2',
)
