import os, shutil

#
# BUILD SWAP
#

args = {
    'opts': '--log-level=INFO -n swap -y --distpath=out --workpath=build --upx-dir external/upx',
    'spec': 'swap.spec'
}

print "Compiling with args:"
print args
print "-" * 10
os.system("external\\pyinstaller\\pyinstaller.py %(opts)s %(spec)s"%args)
