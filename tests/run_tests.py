"""
Test Runner Script for H2S Dosimeter System.
Executes all unit and integration test suites.
Usage: python tests/run_tests.py
"""

import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def run_all_tests():
    print("=" * 65)
    print("    RUNNING AUTOMATED TEST SUITE FOR H2S DOSIMETER SYSTEM     ")
    print("=" * 65)
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(BASE_DIR, 'tests'), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 65)
    if result.wasSuccessful():
        print(" [PASSED] ALL UNIT & INTEGRATION TESTS EXECUTED SUCCESSFULLY! ")
    else:
        print(f" [FAILED] Tests failed: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 65 + "\n")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
