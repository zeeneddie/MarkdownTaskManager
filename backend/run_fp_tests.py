"""
Standalone test runner for Function Point tests
Runs tests without pytest to avoid conftest.py loading issues
"""

import sys
sys.path.insert(0, '/home/eddie/Projects/MarkdownTaskManager/backend')

# Import all test classes
from tests.estimation.test_function_points import (
    TestILFComplexity,
    TestEIFComplexity,
    TestEIComplexity,
    TestEOComplexity,
    TestEQComplexity,
    TestVAFCalculation,
    TestEndToEndCalculation,
    TestEdgeCases,
    TestErrorHandling,
    TestRealWorldExamples
)

def run_test_class(test_class, class_name):
    """Run all tests in a test class"""
    print(f"\n{'='*70}")
    print(f"{class_name}")
    print('='*70)

    test_instance = test_class()
    test_methods = [m for m in dir(test_instance) if m.startswith('test_')]

    passed = 0
    failed = 0

    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            print(f"✅ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {method_name}: AssertionError: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"❌ {method_name}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    return passed, failed

def main():
    """Run all test suites"""
    print("\n" + "="*70)
    print(" FUNCTION POINT CALCULATOR - COMPREHENSIVE TEST SUITE")
    print("="*70)

    test_classes = [
        (TestILFComplexity, "Test Category 1: ILF Complexity Matrix (9 tests)"),
        (TestEIFComplexity, "Test Category 2: EIF Complexity Matrix (9 tests)"),
        (TestEIComplexity, "Test Category 3: EI Complexity Matrix (9 tests)"),
        (TestEOComplexity, "Test Category 4: EO Complexity Matrix (9 tests)"),
        (TestEQComplexity, "Test Category 5: EQ Complexity Matrix (9 tests)"),
        (TestVAFCalculation, "Test Category 6: VAF Calculation (4 tests)"),
        (TestEndToEndCalculation, "Test Category 7: End-to-End Calculation (3 tests)"),
        (TestEdgeCases, "Test Category 8: Edge Cases (5 tests)"),
        (TestErrorHandling, "Test Category 9: Error Handling (5 tests)"),
        (TestRealWorldExamples, "Test Category 10: Real-World Examples (3 tests)")
    ]

    total_passed = 0
    total_failed = 0

    for test_class, class_name in test_classes:
        passed, failed = run_test_class(test_class, class_name)
        total_passed += passed
        total_failed += failed

    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed} ✅")
    print(f"Failed: {total_failed} ❌")

    if total_failed == 0:
        print("\n" + "="*70)
        print(" ALL TESTS PASSED! ✅")
        print("="*70)
        print("\nFunction Point Calculator is production-ready!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
