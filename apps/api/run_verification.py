#!/usr/bin/env python
"""Verify Inngest module compilation and import."""

import sys
import os

# Change to project directory
os.chdir('d:\\Project\\Archimedes\\apps\\api')
sys.path.insert(0, os.getcwd())

print("=" * 60)
print("STEP 1: Attempting py_compile check")
print("=" * 60)

try:
    import py_compile
    py_compile.compile('app/inngest.py', doraise=True)
    print("✓ SUCCESS: app/inngest.py compiles without syntax errors")
except py_compile.PyCompileError as e:
    print(f"✗ FAILED: Compilation error:\n{e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("STEP 2: Attempting module import")
print("=" * 60)

try:
    import app.inngest
    print("✓ SUCCESS: app.inngest imported successfully")
    print(f"  - Module file: {app.inngest.__file__}")
    print(f"  - Has client: {hasattr(app.inngest, 'client')}")
    print(f"  - Has FUNCTIONS: {hasattr(app.inngest, 'FUNCTIONS')}")
    print(f"  - Has register_inngest: {hasattr(app.inngest, 'register_inngest')}")
    if hasattr(app.inngest, 'FUNCTIONS'):
        print(f"  - Number of functions: {len(app.inngest.FUNCTIONS)}")
        for fn in app.inngest.FUNCTIONS:
            print(f"    • {fn.id}")
except ImportError as e:
    print(f"✗ IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL CHECKS PASSED")
print("=" * 60)
