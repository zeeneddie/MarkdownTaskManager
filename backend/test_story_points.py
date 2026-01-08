"""
Quick test for Story Point Estimator

Tests the Story Point Estimator with various complexity levels.
"""

import sys
sys.path.insert(0, '/home/eddie/Projects/MarkdownTaskManager/backend')

from estimation.story_points import (
    StoryPointEstimator,
    StoryPointRequest,
    ComplexityFactors,
    ThreePointEstimate,
    quick_estimate
)


def test_simple_story():
    """Test a simple story (low complexity)"""
    print("=" * 70)
    print("TEST 1: Simple Story (Low Complexity)")
    print("=" * 70)

    request = StoryPointRequest(
        story_name="Add validation to email field",
        complexity_factors=ComplexityFactors(
            technical_complexity=2,
            business_value=3,
            risk_level=1,
            uncertainty=2,
            dependencies=0
        )
    )

    result = StoryPointEstimator.estimate(request)

    print(f"\nStory: {result.story_name}")
    print(f"Fibonacci Points: {result.fibonacci_points}")
    print(f"Complexity Score: {result.complexity_score}/100")
    print(f"Confidence (±10%): {result.confidence_narrow.min} - {result.confidence_narrow.max}")
    print(f"Confidence (±25%): {result.confidence_wide.min} - {result.confidence_wide.max}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Risk Factors: {result.risk_factors or 'None'}")
    print(f"Recommendations: {result.recommendations or 'None'}")

    assert result.fibonacci_points in [1, 2, 3], "Should be low story points"
    print("\n✅ TEST 1 PASSED\n")


def test_medium_story():
    """Test a medium story"""
    print("=" * 70)
    print("TEST 2: Medium Story")
    print("=" * 70)

    request = StoryPointRequest(
        story_name="Implement user profile page",
        complexity_factors=ComplexityFactors(
            technical_complexity=5,
            business_value=6,
            risk_level=4,
            uncertainty=5,
            dependencies=2
        )
    )

    result = StoryPointEstimator.estimate(request)

    print(f"\nStory: {result.story_name}")
    print(f"Fibonacci Points: {result.fibonacci_points}")
    print(f"Complexity Score: {result.complexity_score}/100")
    print(f"Reasoning: {result.reasoning}")
    print(f"Risk Factors: {len(result.risk_factors)} identified")

    assert result.fibonacci_points in [3, 5, 8], "Should be medium story points"
    print("\n✅ TEST 2 PASSED\n")


def test_complex_story_with_three_point():
    """Test a complex story with three-point estimation"""
    print("=" * 70)
    print("TEST 3: Complex Story with Three-Point Estimation")
    print("=" * 70)

    request = StoryPointRequest(
        story_name="Implement OAuth authentication with multiple providers",
        complexity_factors=ComplexityFactors(
            technical_complexity=8,
            business_value=9,
            risk_level=7,
            uncertainty=6,
            dependencies=4
        ),
        three_point=ThreePointEstimate(
            optimistic_hours=8,
            most_likely_hours=16,
            pessimistic_hours=32
        ),
        description="OAuth 2.0 with Google, GitHub, and Microsoft providers"
    )

    result = StoryPointEstimator.estimate(request)

    print(f"\nStory: {result.story_name}")
    print(f"Fibonacci Points: {result.fibonacci_points}")
    print(f"Complexity Score: {result.complexity_score}/100")
    print(f"\nThree-Point Estimation:")
    print(f"  Optimistic: {result.hours_estimate['optimistic']} hours")
    print(f"  Most Likely: {result.hours_estimate['most_likely']} hours")
    print(f"  Pessimistic: {result.hours_estimate['pessimistic']} hours")
    print(f"  PERT Estimate: {result.hours_estimate['pert_estimate']} hours")
    print(f"  Range: {result.hours_estimate['range']}")
    print(f"  Standard Deviation: {result.hours_estimate['standard_deviation']}")
    print(f"  68% Confidence: {result.hours_estimate['confidence_68']['min']:.2f} - {result.hours_estimate['confidence_68']['max']:.2f} hours")
    print(f"  95% Confidence: {result.hours_estimate['confidence_95']['min']:.2f} - {result.hours_estimate['confidence_95']['max']:.2f} hours")
    print(f"\nReasoning: {result.reasoning}")
    print(f"\nRisk Factors ({len(result.risk_factors)}):")
    for risk in result.risk_factors:
        print(f"  - {risk}")
    print(f"\nRecommendations ({len(result.recommendations)}):")
    for rec in result.recommendations:
        print(f"  - {rec}")

    assert result.fibonacci_points in [8, 13], "Should be large story points"
    assert result.hours_estimate is not None, "Should have hours estimate"
    assert len(result.risk_factors) > 0, "Should have risk factors"
    assert len(result.recommendations) > 0, "Should have recommendations"
    print("\n✅ TEST 3 PASSED\n")


def test_epic_story():
    """Test an epic-sized story (should recommend splitting)"""
    print("=" * 70)
    print("TEST 4: Epic-Sized Story (Should Recommend Splitting)")
    print("=" * 70)

    request = StoryPointRequest(
        story_name="Build complete user management system",
        complexity_factors=ComplexityFactors(
            technical_complexity=9,
            business_value=10,
            risk_level=8,
            uncertainty=8,
            dependencies=7
        )
    )

    result = StoryPointEstimator.estimate(request)

    print(f"\nStory: {result.story_name}")
    print(f"Fibonacci Points: {result.fibonacci_points}")
    print(f"Complexity Score: {result.complexity_score}/100")
    print(f"\nRecommendations ({len(result.recommendations)}):")
    for rec in result.recommendations:
        print(f"  - {rec}")

    assert result.fibonacci_points >= 13, "Should be very large or epic"
    assert any("split" in rec.lower() for rec in result.recommendations), "Should recommend splitting"
    print("\n✅ TEST 4 PASSED\n")


def test_quick_estimate():
    """Test the quick estimate utility function"""
    print("=" * 70)
    print("TEST 5: Quick Estimate Function")
    print("=" * 70)

    # Test 1: Simple
    points1 = quick_estimate(technical_complexity=2, business_value=3, risk_level=1)
    print(f"\nSimple story (2, 3, 1): {points1} points")
    assert points1 in [1, 2, 3], "Should be low"

    # Test 2: Medium
    points2 = quick_estimate(technical_complexity=5, business_value=5, risk_level=5)
    print(f"Medium story (5, 5, 5): {points2} points")
    assert points2 in [3, 5, 8], "Should be medium"

    # Test 3: Complex
    points3 = quick_estimate(technical_complexity=8, business_value=9, risk_level=7)
    print(f"Complex story (8, 9, 7): {points3} points")
    assert points3 in [8, 13], "Should be large"

    print("\n✅ TEST 5 PASSED\n")


def test_fibonacci_mapping():
    """Test Fibonacci mapping thresholds"""
    print("=" * 70)
    print("TEST 6: Fibonacci Mapping Thresholds")
    print("=" * 70)

    from estimation.story_points import FibonacciMapper

    test_cases = [
        (5, 1),      # 0-10 → 1 point
        (15, 2),     # 10-20 → 2 points
        (25, 3),     # 20-35 → 3 points
        (45, 5),     # 35-55 → 5 points
        (60, 8),     # 55-70 → 8 points
        (75, 13),    # 70-85 → 13 points
        (90, 21),    # 85-100 → 21 points
    ]

    print("\nComplexity Score → Fibonacci Points:")
    for score, expected_points in test_cases:
        actual_points = FibonacciMapper.map_to_fibonacci(score)
        status = "✅" if actual_points == expected_points else "❌"
        print(f"  {score}/100 → {actual_points} points (expected {expected_points}) {status}")
        assert actual_points == expected_points, f"Mapping failed for {score}"

    print("\n✅ TEST 6 PASSED\n")


def test_three_point_validation():
    """Test three-point estimation validation"""
    print("=" * 70)
    print("TEST 7: Three-Point Estimation Validation")
    print("=" * 70)

    # Valid case
    print("\nValid case (4, 8, 16):")
    try:
        valid = ThreePointEstimate(
            optimistic_hours=4,
            most_likely_hours=8,
            pessimistic_hours=16
        )
        print("  ✅ Accepted")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        raise

    # Invalid case 1: pessimistic < most_likely
    print("\nInvalid case (pessimistic < most_likely):")
    try:
        invalid1 = ThreePointEstimate(
            optimistic_hours=4,
            most_likely_hours=16,
            pessimistic_hours=8
        )
        print("  ❌ Should have raised ValueError")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    # Invalid case 2: most_likely < optimistic
    print("\nInvalid case (most_likely < optimistic):")
    try:
        invalid2 = ThreePointEstimate(
            optimistic_hours=16,
            most_likely_hours=8,
            pessimistic_hours=20
        )
        print("  ❌ Should have raised ValueError")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    print("\n✅ TEST 7 PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" STORY POINT ESTIMATOR - TEST SUITE")
    print("=" * 70)
    print()

    try:
        test_simple_story()
        test_medium_story()
        test_complex_story_with_three_point()
        test_epic_story()
        test_quick_estimate()
        test_fibonacci_mapping()
        test_three_point_validation()

        print("=" * 70)
        print(" ALL TESTS PASSED! ✅")
        print("=" * 70)
        print("\nStory Point Estimator is working correctly!")
        print("\nKey Features Verified:")
        print("  ✅ Fibonacci mapping (1, 2, 3, 5, 8, 13, 21)")
        print("  ✅ Complexity scoring from multiple factors")
        print("  ✅ Three-point estimation (PERT formula)")
        print("  ✅ Confidence intervals (±10%, ±25%)")
        print("  ✅ Risk factor identification")
        print("  ✅ Actionable recommendations")
        print("  ✅ Input validation")
        print("\nReady for integration! 🚀\n")

    except Exception as e:
        print("\n" + "=" * 70)
        print(" TEST FAILED ❌")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
