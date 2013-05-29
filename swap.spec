# -*- mode: python -*-
sa = Analysis(['src/swap.py'])
ua = Analysis(['src/updater.py'])
spyz = PYZ(sa.pure)
upyz = PYZ(ua.pure)
sexe = EXE(spyz,
          sa.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\swap', 'swap.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False )
uexe = EXE(upyz,
          ua.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\updater', 'updater.exe'),
          debug=False,
          strip=True,
          upx=True,
          console=False )
coll = COLLECT(sexe, uexe,
               sa.binaries,
               sa.zipfiles,
               sa.datas,
               ua.binaries,
               ua.zipfiles,
               ua.datas,
               strip=False,
               upx=True,
               name='')
