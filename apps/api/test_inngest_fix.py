#!/usr/bin/env python3
"""Test the Inngest module fix."""

import sys
import os
from pathlib import Path

# Setup paths
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path.cwd()))

results = []

def log(msg):
    """Log message to both console and results list."""
    results.append(msg)
    print(msg)

log("=" * 70)
log("INNGEST INTEGRATION FIX VERIFICATION")
log("=" * 70)

# Step 1: Check compilation
log("\n[STEP 1] Checking Python syntax with py_compile...")
try:
    import py_compile
    py_compile.compile('app/inngest.py', doraise=True)
    log("✓ PASS: app/inngest.py is syntactically valid")
except Exception as e:
    log(f"✗ FAIL: {e}")
    sys.exit(1)

# Step 2: Check imports
log("\n[STEP 2] Testing module import...")
try:
    import app.inngest
    log("✓ PASS: app.inngest imported successfully")
except ImportError as e:
    log(f"✗ FAIL: Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    log(f"✗ FAIL: Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Verify module components
log("\n[STEP 3] Verifying module components...")
required_attrs = ['client', 'FUNCTIONS', 'register_inngest', 'demo_workflow', 'demo_failure_workflow']
missing = []
for attr in required_attrs:
    if hasattr(app.inngest, attr):
        log(f"  ✓ {attr} exists")
    else:
        log(f"  ✗ {attr} MISSING")
        missing.append(attr)

if missing:
    log(f"\n✗ FAIL: Missing attributes: {missing}")
    sys.exit(1)

log(f"✓ PASS: All required attributes present")

# Step 4: Check FUNCTIONS list
log("\n[STEP 4] Checking workflow functions...")
functions = app.inngest.FUNCTIONS
if len(functions) == 2:
    log(f"✓ PASS: Found 2 functions")
    for fn in functions:
        log(f"  - {fn.id}")
else:
    log(f"✗ FAIL: Expected 2 functions, got {len(functions)}")
    sys.exit(1)

# Step 5: Verify fast_api import
log("\n[STEP 5] Verifying fast_api import...")
try:
    from inngest import fast_api
    log("✓ PASS: inngest.fast_api can be imported directly")
    if hasattr(fast_api, 'serve'):
        log("  ✓ fast_api.serve() function exists")
    else:
        log("  ✗ fast_api.serve() not found")
        sys.exit(1)
except ImportError as e:
    log(f"✗ FAIL: Cannot import fast_api: {e}")
    sys.exit(1)

log("\n" + "=" * 70)
log("ALL VERIFICATION CHECKS PASSED ✓")
log("=" * 70)

# Write results to file
with open("verification_results.txt", "w") as f:
    f.write("\n".join(results))
    f.write("\n")

print("\nResults also saved to: verification_results.txt")
