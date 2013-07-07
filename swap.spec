# -*- mode: python -*-
a = Analysis(['src/swap.py'],
             pathex=['C:\\Users\\Daniel\\Desktop\\swap'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='swap.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
