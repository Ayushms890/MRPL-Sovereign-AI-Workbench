import py_compile
import sys

try:
    py_compile.compile('app/inngest.py', doraise=True)
    print('SUCCESS: app/inngest.py compiled successfully')
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f'COMPILE ERROR: {e}')
    sys.exit(1)
