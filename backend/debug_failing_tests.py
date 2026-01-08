"""
Debug failing tests to see actual vs expected values
"""

import sys
sys.path.insert(0, '/home/eddie/Projects/MarkdownTaskManager/backend')

from estimation.function_points import (
    FunctionPointCalculator,
    FunctionPointRequest,
    ComponentInput
)

def test_all_component_types():
    """Test with all 5 component types"""
    request = FunctionPointRequest(
        project_name="Complete System",
        ilfs=[ComponentInput(name="ILF1", rets=1, dets=10)],
        eifs=[ComponentInput(name="EIF1", rets=1, dets=10)],
        eis=[ComponentInput(name="EI1", ftrs=1, dets=5)],
        eos=[ComponentInput(name="EO1", ftrs=1, dets=8)],
        eqs=[ComponentInput(name="EQ1", ftrs=1, dets=6)],
        use_vaf=False
    )

    calculator = FunctionPointCalculator(request)
    result = calculator.calculate()

    print(f"test_all_component_types:")
    print(f"  Expected UFP: 20 (7+5+3+4+3)")
    print(f"  Actual UFP: {result.unadjusted_fp}")
    print(f"  Breakdown:")
    print(f"    ILF: {result.total_ilf_fp} (expected 7)")
    print(f"    EIF: {result.total_eif_fp} (expected 5)")
    print(f"    EI: {result.total_ei_fp} (expected 3)")
    print(f"    EO: {result.total_eo_fp} (expected 4)")
    print(f"    EQ: {result.total_eq_fp} (expected 3)")
    print()

def test_simple_crud_app():
    """Simple CRUD app (~80 FP)"""
    request = FunctionPointRequest(
        project_name="Blog Platform",
        ilfs=[
            ComponentInput(name="Users", rets=1, dets=12),  # Low: 7
            ComponentInput(name="Posts", rets=2, dets=18),  # Low: 7
            ComponentInput(name="Comments", rets=1, dets=8),  # Low: 7
        ],
        eifs=[
            ComponentInput(name="Auth Service", rets=1, dets=6),  # Low: 5
        ],
        eis=[
            ComponentInput(name="Register", ftrs=1, dets=10),  # Low: 3
            ComponentInput(name="Login", ftrs=1, dets=3),  # Low: 3
            ComponentInput(name="Create Post", ftrs=1, dets=8),  # Low: 3
            ComponentInput(name="Add Comment", ftrs=2, dets=5),  # Low: 3
        ],
        eos=[
            ComponentInput(name="User Profile", ftrs=1, dets=12),  # Low: 4
            ComponentInput(name="Post Feed", ftrs=2, dets=10),  # Average: 5
        ],
        eqs=[
            ComponentInput(name="Search Posts", ftrs=1, dets=6),  # Low: 3
            ComponentInput(name="View Post", ftrs=2, dets=10),  # Low: 3
            ComponentInput(name="List Comments", ftrs=1, dets=8),  # Low: 3
        ],
        use_vaf=False
    )

    calculator = FunctionPointCalculator(request)
    result = calculator.calculate()

    expected_ufp = 21 + 5 + 12 + 9 + 9  # ILF + EIF + EI + EO + EQ
    print(f"test_simple_crud_app:")
    print(f"  Expected UFP: {expected_ufp}")
    print(f"  Actual UFP: {result.unadjusted_fp}")
    print(f"  Breakdown:")
    print(f"    ILF: {result.total_ilf_fp} (expected 21)")
    print(f"    EIF: {result.total_eif_fp} (expected 5)")
    print(f"    EI: {result.total_ei_fp} (expected 12)")
    print(f"    EO: {result.total_eo_fp} (expected 9)")
    print(f"    EQ: {result.total_eq_fp} (expected 9)")
    print(f"  Range check: 50 < {result.unadjusted_fp} < 100: {50 < result.unadjusted_fp < 100}")
    print()

def test_ecommerce_platform():
    """E-commerce platform (~200 FP)"""
    request = FunctionPointRequest(
        project_name="E-Commerce",
        ilfs=[
            ComponentInput(name="Users", rets=3, dets=25),  # Average: 10
            ComponentInput(name="Products", rets=4, dets=35),  # Average: 10
            ComponentInput(name="Orders", rets=5, dets=40),  # Average: 10
            ComponentInput(name="Inventory", rets=3, dets=20),  # Low: 7
            ComponentInput(name="Cart", rets=2, dets=15),  # Low: 7
        ],
        eifs=[
            ComponentInput(name="Payment Gateway", rets=2, dets=25),  # Average: 7
            ComponentInput(name="Shipping API", rets=1, dets=15),  # Low: 5
        ],
        eis=[
            ComponentInput(name="Checkout", ftrs=3, dets=20),  # High: 6
            ComponentInput(name="Add to Cart", ftrs=2, dets=8),  # Low: 3
            ComponentInput(name="Update Inventory", ftrs=2, dets=12),  # Average: 4
        ],
        eos=[
            ComponentInput(name="Order Confirmation", ftrs=2, dets=15),  # Average: 5
            ComponentInput(name="Sales Report", ftrs=4, dets=25),  # High: 7
            ComponentInput(name="Invoice", ftrs=3, dets=22),  # High: 7
        ],
        eqs=[
            ComponentInput(name="Search Products", ftrs=2, dets=12),  # Average: 4
            ComponentInput(name="View Order", ftrs=2, dets=15),  # Average: 4
        ],
        use_vaf=False
    )

    calculator = FunctionPointCalculator(request)
    result = calculator.calculate()

    print(f"test_ecommerce_platform:")
    print(f"  Actual UFP: {result.unadjusted_fp}")
    print(f"  Breakdown:")
    print(f"    ILF: {result.total_ilf_fp}")
    print(f"    EIF: {result.total_eif_fp}")
    print(f"    EI: {result.total_ei_fp}")
    print(f"    EO: {result.total_eo_fp}")
    print(f"    EQ: {result.total_eq_fp}")
    print(f"  Range check: 150 < {result.unadjusted_fp} < 250: {150 < result.unadjusted_fp < 250}")
    print(f"  Project size: {result.summary['estimation_guidance']['project_size']}")
    print()

if __name__ == "__main__":
    test_all_component_types()
    test_simple_crud_app()
    test_ecommerce_platform()
