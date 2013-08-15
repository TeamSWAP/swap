import os, sys

extra = ['external', 'etc/pylint_stubs']
extra = [os.getcwd() + "/" + e for e in extra]
initHook = "import sys; sys.path = sys.path + " + repr(extra)

pylintCmd = "pylint %%s -E --rcfile=%s --init-hook=\"%s\""%(os.getcwd() + "/pylint.rc", initHook)

def ret_or_die(x):
    if x:
        exit(x)

ret_or_die(os.system(pylintCmd%"build.py clean.py run.py package.py lint_all.py"))
ret_or_die(os.chdir("external"))
ret_or_die(os.system(pylintCmd%"fuzion"))
ret_or_die(os.chdir("../src"))
ret_or_die(os.system(pylintCmd%(" ".join([x for x in os.listdir(".") if x.endswith('.py')]))))
ret_or_die(os.chdir(".."))

exit(0)
