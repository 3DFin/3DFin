# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["../src/three_d_fin/__main__.py"],
    pathex=["../src/three_d_fin/"],
    binaries=[],
    datas=[
        ("../src/three_d_fin/assets/stripe.png", "."),
        ("../src/three_d_fin/assets/original_cloud.png", "."),
        ("../src/three_d_fin/assets/normalized_cloud.png", "."),
        ("../src/three_d_fin/assets/info_icon.png", "."),
        ("../src/three_d_fin/assets/section_details.png", "."),
        ("../src/three_d_fin/assets/sectors.png", "."),
        ("../src/three_d_fin/assets/documentation.pdf", "."),
        ("../src/three_d_fin/assets/3dfin_logo.png", "."),
        ("../src/three_d_fin/assets/icon_window.ico", "."),
        ("../src/three_d_fin/assets/warning_img_1.png", "."),
        ("../src/three_d_fin/assets/carlos_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/celestino_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/diego_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/cris_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/stefan_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/tadas_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/covadonga_pic_1.jpg", "."),
        ("../src/three_d_fin/assets/uniovi_logo_1.png", "."),
        ("../src/three_d_fin/assets/nerc_logo_1.png", "."),
        ("../src/three_d_fin/assets/spain_logo_1.png", "."),
        ("../src/three_d_fin/assets/csic_logo_1.png", "."),
        ("../src/three_d_fin/assets/swansea_logo_1.png", "."),
        ("../src/three_d_fin/assets/License.txt", "."),
    ],
    hiddenimports=[
        "jakteristics.utils",
        "xlsxwriter",
        "laszip",
        "lazrs",
        "sklearn.metrics._pairwise_distances_reduction._datasets_pair",
        "sklearn.metrics._pairwise_distances_reduction._base",
        "sklearn.metrics._pairwise_distances_reduction._middle_term_computer",
        "xlsxwriter"
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
    name="3DFin",
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
    icon=["icon_window.ico"],
)
