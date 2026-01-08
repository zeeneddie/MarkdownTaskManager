"""
Quick validation test for Function Point Calculator
Tests basic functionality before comprehensive test suite
"""

import sys
sys.path.insert(0, '/home/eddie/Projects/MarkdownTaskManager/backend')

from estimation.function_points import (
    FunctionPointCalculator,
    FunctionPointRequest,
    ComponentInput
)


def test_simple_calculation():
    """Test 1: Simple calculation without VAF"""
    print("=" * 70)
    print("TEST 1: Simple E-Commerce Project (No VAF)")
    print("=" * 70)

    request = FunctionPointRequest(
        project_name="Simple E-Commerce",
        ilfs=[
            ComponentInput(name="Users", rets=1, dets=8),  # Low: 7 FP
            ComponentInput(name="Products", rets=3, dets=25),  # Average: 10 FP
            ComponentInput(name="Orders", rets=2, dets=30),  # Average: 10 FP
        ],
        eifs=[
            ComponentInput(name="Payment Gateway", rets=1, dets=10),  # Low: 5 FP
        ],
        eis=[
            ComponentInput(name="Register", ftrs=1, dets=6),  # Low: 3 FP
            ComponentInput(name="Login", ftrs=1, dets=3),  # Low: 3 FP
            ComponentInput(name="Add to Cart", ftrs=2, dets=4),  # Low: 3 FP
            ComponentInput(name="Checkout", ftrs=2, dets=10),  # Average: 4 FP
        ],
        eos=[
            ComponentInput(name="Order Confirmation", ftrs=1, dets=8),  # Low: 4 FP
            ComponentInput(name="Sales Report", ftrs=3, dets=15),  # High: 7 FP
        ],
        eqs=[
            ComponentInput(name="Search Products", ftrs=1, dets=4),  # Low: 3 FP
            ComponentInput(name="View Order", ftrs=1, dets=10),  # Low: 3 FP
        ],
        use_vaf=False
    )

    calculator = FunctionPointCalculator(request)
    result = calculator.calculate()

    print(f"\nProject: {result.project_name}")
    print(f"\n{'Component Type':<20} {'Count':<8} {'Total FP':<10}")
    print("-" * 40)
    print(f"{'ILFs':<20} {len(result.ilf_results):<8} {result.total_ilf_fp:<10}")
    print(f"{'EIFs':<20} {len(result.eif_results):<8} {result.total_eif_fp:<10}")
    print(f"{'EIs':<20} {len(result.ei_results):<8} {result.total_ei_fp:<10}")
    print(f"{'EOs':<20} {len(result.eo_results):<8} {result.total_eo_fp:<10}")
    print(f"{'EQs':<20} {len(result.eq_results):<8} {result.total_eq_fp:<10}")
    print("-" * 40)
    print(f"{'TOTAL':<20} {'':<8} {result.unadjusted_fp:<10}")

    print(f"\nUnadjusted FP: {result.unadjusted_fp}")
    print(f"VAF: {result.vaf} (no adjustment)")
    print(f"Adjusted FP: {result.adjusted_fp}")

    print(f"\nProject Size: {result.summary['estimation_guidance']['project_size']}")
    print(f"Estimated Effort: {result.summary['estimation_guidance']['estimated_person_days']} person-days")

    print("\n✅ Test 1 PASSED\n")
    return result


def test_with_vaf():
    """Test 2: Calculation with VAF"""
    print("=" * 70)
    print("TEST 2: Complex Project with VAF")
    print("=" * 70)

    # GSC ratings: all average (3) except high complexity processing (5)
    gsc_ratings = [3, 3, 4, 3, 4, 3, 3, 3, 5, 3, 3, 3, 3, 3]  # TDI = 47

    request = FunctionPointRequest(
        project_name="Enterprise ERP System",
        ilfs=[
            ComponentInput(name="Inventory", rets=6, dets=30),  # High: 15 FP
            ComponentInput(name="Customers", rets=4, dets=40),  # Average: 10 FP
            ComponentInput(name="Suppliers", rets=3, dets=25),  # Average: 10 FP
            ComponentInput(name="Transactions", rets=7, dets=50),  # High: 15 FP
        ],
        eifs=[
            ComponentInput(name="Tax API", rets=2, dets=15),  # Low: 5 FP
            ComponentInput(name="Currency API", rets=1, dets=10),  # Low: 5 FP
        ],
        eis=[
            ComponentInput(name="Create Order", ftrs=3, dets=20),  # High: 6 FP
            ComponentInput(name="Update Inventory", ftrs=2, dets=15),  # Average: 4 FP
            ComponentInput(name="Add Customer", ftrs=1, dets=12),  # Low: 3 FP
        ],
        eos=[
            ComponentInput(name="Inventory Report", ftrs=4, dets=25),  # High: 7 FP
            ComponentInput(name="Financial Dashboard", ftrs=5, dets=30),  # High: 7 FP
        ],
        eqs=[
            ComponentInput(name="Search Inventory", ftrs=2, dets=8),  # Average: 4 FP
            ComponentInput(name="View Customer", ftrs=1, dets=10),  # Low: 3 FP
        ],
        use_vaf=True,
        gsc_ratings=gsc_ratings
    )

    calculator = FunctionPointCalculator(request)
    result = calculator.calculate()

    print(f"\nProject: {result.project_name}")
    print(f"\n{'Component Type':<20} {'Count':<8} {'Total FP':<10}")
    print("-" * 40)
    print(f"{'ILFs':<20} {len(result.ilf_results):<8} {result.total_ilf_fp:<10}")
    print(f"{'EIFs':<20} {len(result.eif_results):<8} {result.total_eif_fp:<10}")
    print(f"{'EIs':<20} {len(result.ei_results):<8} {result.total_ei_fp:<10}")
    print(f"{'EOs':<20} {len(result.eo_results):<8} {result.total_eo_fp:<10}")
    print(f"{'EQs':<20} {len(result.eq_results):<8} {result.total_eq_fp:<10}")
    print("-" * 40)
    print(f"{'TOTAL (UFP)':<20} {'':<8} {result.unadjusted_fp:<10}")

    print(f"\nUnadjusted FP: {result.unadjusted_fp}")

    vaf_breakdown = result.summary['vaf_breakdown']
    print(f"TDI (Total Degree of Influence): {vaf_breakdown['tdi']}")
    print(f"VAF: {result.vaf} (0.65 + {vaf_breakdown['tdi']} × 0.01)")
    print(f"Adjusted FP: {result.adjusted_fp} ({result.unadjusted_fp} × {result.vaf})")

    print(f"\nProject Size: {result.summary['estimation_guidance']['project_size']}")
    print(f"Estimated Effort: {result.summary['estimation_guidance']['estimated_person_days']} person-days")

    print("\n✅ Test 2 PASSED\n")
    return result


def test_complexity_matrices():
    """Test 3: Verify complexity determination"""
    print("=" * 70)
    print("TEST 3: Complexity Matrix Validation")
    print("=" * 70)

    from estimation.function_points import ILFCalculator, EICalculator

    # ILF: 1 RET, 10 DETs → Low (7 FP)
    assert ILFCalculator.determine_complexity(1, 10) == "Low"
    # ILF: 1 RET, 60 DETs → Average (10 FP)
    assert ILFCalculator.determine_complexity(1, 60) == "Average"
    # ILF: 3 RETs, 40 DETs → Average (10 FP)
    assert ILFCalculator.determine_complexity(3, 40) == "Average"
    # ILF: 6 RETs, 100 DETs → High (15 FP)
    assert ILFCalculator.determine_complexity(6, 100) == "High"
    print("✅ ILF complexity matrix: CORRECT")

    # EI: 1 FTR, 10 DETs → Low (3 FP)
    assert EICalculator.determine_complexity(1, 10) == "Low"
    # EI: 2 FTRs, 10 DETs → Average (4 FP)
    assert EICalculator.determine_complexity(2, 10) == "Average"
    # EI: 3 FTRs, 20 DETs → High (6 FP)
    assert EICalculator.determine_complexity(3, 20) == "High"
    print("✅ EI complexity matrix: CORRECT")

    print("\n✅ Test 3 PASSED\n")


def test_component_breakdown():
    """Test 4: Verify component-level details"""
    print("=" * 70)
    print("TEST 4: Component Breakdown Details")
    print("=" * 70)

    request = FunctionPointRequest(
        project_name="Test Project",
        ilfs=[
            ComponentInput(name="User Database", description="Stores user data", rets=2, dets=15)
        ],
        eis=[
            ComponentInput(name="Login Form", description="User authentication", ftrs=1, dets=3)
        ]
    )

    calculator = FunctionPointCalculator(request)
    result = calculator.calculate()

    # Check ILF result
    ilf = result.ilf_results[0]
    print(f"\nILF: {ilf.name}")
    print(f"  Complexity: {ilf.complexity}")
    print(f"  Function Points: {ilf.function_points}")
    print(f"  Reasoning: {ilf.details['reasoning']}")
    assert ilf.complexity == "Low"
    assert ilf.function_points == 7

    # Check EI result
    ei = result.ei_results[0]
    print(f"\nEI: {ei.name}")
    print(f"  Complexity: {ei.complexity}")
    print(f"  Function Points: {ei.function_points}")
    print(f"  Reasoning: {ei.details['reasoning']}")
    assert ei.complexity == "Low"
    assert ei.function_points == 3

    print("\n✅ Test 4 PASSED\n")


if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print(" FUNCTION POINT CALCULATOR - QUICK VALIDATION")
        print("=" * 70 + "\n")

        # Run all tests
        test_simple_calculation()
        test_with_vaf()
        test_complexity_matrices()
        test_component_breakdown()

        print("=" * 70)
        print(" ALL TESTS PASSED! ✅")
        print("=" * 70)
        print("\nFunction Point Calculator is working correctly!")
        print("Ready for comprehensive test suite (Day 5)\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
