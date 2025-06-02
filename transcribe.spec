# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('uploads', 'uploads'),
        ('chunks', 'chunks'),
    ],
    hiddenimports=[
        'channels',
        'daphne',
        'django',
        'SpeechRecognition',
        'pydub',
        'ffmpeg',
        'ffmpeg-python',
        'aifc',
        'wave',
        'audioop',
        'array',
        'struct',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='transcribe',
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
) 

pyinstaller --onefile --clean --noconfirm --add-data "templates:templates" --add-data "static:static" --add-data "uploads:uploads" --add-data "chunks:chunks" --hidden-import channels --hidden-import daphne --hidden-import django --hidden-import SpeechRecognition --hidden-import pydub --hidden-import ffmpeg --hidden-import ffmpeg-python --hidden-import aifc --hidden-import wave --hidden-import audioop --hidden-import array --hidden-import struct gui.py