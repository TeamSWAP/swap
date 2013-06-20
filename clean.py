import os, shutil

# Clean build files
if os.path.isdir('build'):
	shutil.rmtree('build')
if os.path.isdir('dist'):
	shutil.rmtree('dist')
if os.path.isdir('out'):
	shutil.rmtree('out')

# Remove settings file from src (from running .py)
if os.path.exists('src/settings.dat'):
	os.remove('src/settings.dat')

# Clean src/
def CleanDirectory(dir, ext):
	print "Cleaning directory", dir, "of", ext
	for file in os.listdir(dir):
		fullFile = dir + '/' + file
		if os.path.isdir(fullFile):
			CleanDirectory(fullFile, ext)
		elif file.endswith('.' + ext):
			print "Removing file", fullFile
			os.remove(fullFile)

CleanDirectory('src', 'pyc')
