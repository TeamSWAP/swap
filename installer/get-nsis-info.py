import sys
sys.path.append("..\\src\\")
import constants

version = constants.VERSION
vs = version.split(".")
v1 = int(vs[0])
v2 = int(vs[1])
v3 = 0
v4 = 0
if len(vs) >= 3:
    v3 = int(vs[2])
if len(vs) >= 4:
    v4 = int(vs[3])
vi_version = "%02d.%02d.%02d.%02d"%(v1, v2, v3, v4)

f = open('nsis-info.nsh', 'w')
f.write('# Created by get-nsis-info.py\n')
f.write('# DO NOT EDIT.\n\n')
f.write('!define VERSION "%s"\n'%version)
f.write('!define VI_VERSION "%s"\n'%vi_version)