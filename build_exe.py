import PyInstaller.__main__
import sys
import os
from webdriver_manager.chrome import ChromeDriverManager

# Download ChromeDriver
chromedriver_path = ChromeDriverManager().install()

# Create spec file content
spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('{chromedriver_path}', '.')
    ],
    datas=[
        ('data.json', '.'),
        ('.env', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='X-Engagement-Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

# Write spec file
with open('X-Engagement-Tracker.spec', 'w') as f:
    f.write(spec_content)

# Run PyInstaller
PyInstaller.__main__.run([
    'X-Engagement-Tracker.spec',
    '--clean'
]) 