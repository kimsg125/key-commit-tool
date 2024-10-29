# key_committing_tool_gui.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['key_committing_tool_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('key_committing_tool.ui', '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data,
    cipher=block_cipher,
)
exe = EXE(pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='key_committing_tool_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='key_committing_tool_gui',
)
