import py_compile, glob, sys
files = glob.glob('**/*.py', recursive=True)
error = False
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        print('compile error', f, e)
        error = True
sys.exit(1 if error else 0)
