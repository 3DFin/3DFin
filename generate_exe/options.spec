# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main_with_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('stripe.png', '.'), ('original_cloud.png', '.'), ('normalized_cloud.png', '.'), ('info_icon.png', '.'), ('section_details.png', '.'), ('sectors.png', '.'), ('documentation.pdf', '.'), ('3dfin_logo.png', '.'), ('icon_window.ico', '.'), ('warning_img_1.png', '.'), ('carlos_pic_1.jpg', '.'), ('celestino_pic_1.jpg', '.'), ('diego_pic_1.jpg', '.'), ('cris_pic_1.jpg', '.'), ('stefan_pic_1.jpg', '.'), ('tadas_pic_1.jpg', '.'), ('covadonga_pic_1.jpg', '.'), ('uniovi_logo_1.png', '.'), ('nerc_logo_1.png', '.'), ('spain_logo_1.png', '.'), ('csic_logo_1.png', '.'), ('swansea_logo_1.png', '.'), ('License.txt', '.')],
    hiddenimports=['jakteristics.utils', 'xlsxwriter', 'laszip', 'lazrs', 'sklearn.metrics._pairwise_distances_reduction._datasets_pair', 'sklearn.metrics._pairwise_distances_reduction._base', 'sklearn.metrics._pairwise_distances_reduction._middle_term_computer'],
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
    name='main_with_gui',
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
    icon=['icon_window.ico'],
)
