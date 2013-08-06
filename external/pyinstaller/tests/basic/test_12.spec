# -*- mode: python -*-
a = Analysis(['test_12.py'],
             pathex=['C:\\Users\\Daniel\\Desktop\\swap\\external\\pyinstaller\\tests\\basic'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='test_12.exe',
          debug=True,
          strip=None,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=False,
               name='test_12')
