# -*- mode: python -*-

block_cipher = None


a = Analysis(['loginsightexport/__main__.py'],
             pathex=['/Users/acastonguay/workspace/loginsight-export.git'],
             binaries=[],
             datas=[],
             hiddenimports=['queue', 'utllib3', 'loginsightexport', 'requests'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='loginsightexport',
          debug=False,
          strip=False,
          upx=True,
          console=True )
