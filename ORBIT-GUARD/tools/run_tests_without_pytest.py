"""Fallback test runner that needs no pytest:  python tools/run_tests_without_pytest.py"""
import sys, importlib, traceback
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
m = importlib.import_module("tests.test_orbit_guard")
bad = 0
for n in sorted(dir(m)):
    if n.startswith("test_"):
        try:
            getattr(m, n)(); print("PASS", n)
        except Exception:
            bad += 1; print("FAIL", n); traceback.print_exc()
print("failures:", bad)
