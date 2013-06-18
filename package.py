import os, zipfile, sys, shutil
sys.path.append('src')
import constants
sys.path = sys.path[:-1]

if os.path.exists("dist"):
	shutil.rmtree('dist')
os.mkdir("dist")

# Remove files we don't want included
if os.path.exists("out/debug-swap.log"):
	os.unlink("out/debug-swap.log")
if os.path.exists("out/debug-updater.log"):
	os.unlink("out/debug-updater.log")
if os.path.exists("out/settings.json"):
	os.unlink("out/settings.json")

# Build installer
NSIS_PATH = "C:\\Program Files (x86)\\NSIS\\makensis"
os.system("\"%s\" installer/swap.nsi"%(NSIS_PATH))
shutil.move('installer/out/swap-v%s-setup.exe'%(constants.VERSION), 'dist')

# Build zip
z = zipfile.ZipFile('dist/swap-v%s.zip'%(constants.VERSION), 'w', zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk('out'):
	rs = root.split('\\')
	if len(rs) > 1:
		rs = rs[1:]
		root = "\\".join(rs)
	else:
		root = ""
	for file in files:
		path = os.path.join(root, file)
		z.write('out/' + path, path)
z.close()
