"""
Story Point Estimator - Fibonacci-based estimation with confidence intervals

Features:
- Fibonacci mapping (1, 2, 3, 5, 8, 13, 21)
- Three-point estimation (PERT formula)
- Confidence intervals (±10%, ±25%)
- Complexity scoring from multiple factors

Author: Claude Code (Week 14 Day 4-5)
Date: 2025-11-19
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, model_validator
import math


# Pydantic Models
class ComplexityFactors(BaseModel):
    """Input factors for complexity scoring"""
    technical_complexity: int = Field(..., ge=1, le=10, description="Technical complexity (1-10)")
    business_value: int = Field(..., ge=1, le=10, description="Business value (1-10)")
    risk_level: int = Field(..., ge=1, le=10, description="Risk level (1-10)")
    uncertainty: int = Field(default=5, ge=1, le=10, description="Uncertainty level (1-10)")
    dependencies: int = Field(default=1, ge=0, le=10, description="Number of dependencies (0-10)")


class ThreePointEstimate(BaseModel):
    """Three-point estimation inputs"""
    optimistic_hours: float = Field(..., gt=0, description="Optimistic estimate (hours)")
    most_likely_hours: float = Field(..., gt=0, description="Most likely estimate (hours)")
    pessimistic_hours: float = Field(..., gt=0, description="Pessimistic estimate (hours)")

    @model_validator(mode='after')
    def validate_estimates_order(self):
        """Ensure pessimistic >= most_likely >= optimistic"""
        if self.most_likely_hours < self.optimistic_hours:
            raise ValueError("Most likely estimate must be >= optimistic estimate")
        if self.pessimistic_hours < self.most_likely_hours:
            raise ValueError("Pessimistic estimate must be >= most likely estimate")
        return self


class StoryPointRequest(BaseModel):
    """Request model for story point estimation"""
    story_name: str = Field(..., min_length=1, max_length=200, description="Story name")
    complexity_factors: ComplexityFactors
    three_point: Optional[ThreePointEstimate] = None
    description: Optional[str] = Field(None, max_length=1000, description="Story description")


class ConfidenceInterval(BaseModel):
    """Confidence interval range"""
    min: float = Field(..., description="Minimum value in interval")
    max: float = Field(..., description="Maximum value in interval")
    percentage: str = Field(..., description="Confidence level (e.g., '±10%')")


class StoryPointResponse(BaseModel):
    """Response model for story point estimation"""
    story_name: str
    fibonacci_points: int = Field(..., description="Story points (Fibonacci: 1, 2, 3, 5, 8, 13, 21)")
    complexity_score: float = Field(..., description="Raw complexity score (0-100)")
    confidence_narrow: ConfidenceInterval = Field(..., description="±10% confidence interval")
    confidence_wide: ConfidenceInterval = Field(..., description="±25% confidence interval")
    hours_estimate: Optional[Dict] = Field(None, description="Hours estimate (if three-point provided)")
    reasoning: str = Field(..., description="Explanation of the estimate")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


# Fibonacci Mapper
class FibonacciMapper:
    """Maps complexity scores to Fibonacci story points"""

    FIBONACCI = [1, 2, 3, 5, 8, 13, 21]

    # Complexity thresholds (0-100 scale)
    THRESHOLDS = {
        1: (0, 10),      # Trivial (< 1 hour)
        2: (10, 20),     # Simple (1-2 hours)
        3: (20, 35),     # Small (2-4 hours)
        5: (35, 55),     # Medium (1 day)
        8: (55, 70),     # Large (2-3 days)
        13: (70, 85),    # Very large (1 week) - consider splitting
        21: (85, 100)    # Epic-sized - MUST be split
    }

    @classmethod
    def map_to_fibonacci(cls, complexity_score: float) -> int:
        """
        Map continuous complexity score (0-100) to nearest Fibonacci number

        Args:
            complexity_score: Continuous score from 0-100

        Returns:
            Fibonacci story point (1, 2, 3, 5, 8, 13, 21)
        """
        # Clamp to 0-100
        score = max(0, min(100, complexity_score))

        # Find matching Fibonacci number based on thresholds
        for fib_value, (min_threshold, max_threshold) in cls.THRESHOLDS.items():
            if min_threshold <= score < max_threshold:
                return fib_value

        # Handle edge case (score = 100)
        return 21

    @classmethod
    def get_description(cls, fibonacci_points: int) -> str:
        """Get human-readable description of story point value"""
        descriptions = {
            1: "Trivial task (< 1 hour)",
            2: "Simple task (1-2 hours)",
            3: "Small story (2-4 hours)",
            5: "Medium story (1 day)",
            8: "Large story (2-3 days)",
            13: "Very large story (1 week) - consider splitting",
            21: "Epic-sized - MUST be split into smaller stories"
        }
        return descriptions.get(fibonacci_points, "Unknown")


# Complexity Calculator
class ComplexityCalculator:
    """Calculates complexity score from multiple factors"""

    # Weights for each factor (total = 100%)
    WEIGHTS = {
        'technical_complexity': 0.35,   # 35% - Most important
        'business_value': 0.20,         # 20% - High value = more scrutiny = more complex
        'risk_level': 0.25,             # 25% - Risk adds complexity
        'uncertainty': 0.15,            # 15% - Uncertainty requires more exploration
        'dependencies': 0.05            # 5% - Dependencies add coordination complexity
    }

    @classmethod
    def calculate_complexity_score(cls, factors: ComplexityFactors) -> Tuple[float, List[str]]:
        """
        Calculate weighted complexity score (0-100)

        Args:
            factors: ComplexityFactors input

        Returns:
            Tuple of (complexity_score, risk_factors_list)
        """
        # Normalize all factors to 0-10 scale (already validated by Pydantic)
        scores = {
            'technical_complexity': factors.technical_complexity,
            'business_value': factors.business_value,
            'risk_level': factors.risk_level,
            'uncertainty': factors.uncertainty,
            'dependencies': factors.dependencies
        }

        # Calculate weighted score (0-100)
        weighted_score = 0
        for factor, value in scores.items():
            # Convert 0-10 to 0-100, then apply weight
            weighted_score += (value * 10) * cls.WEIGHTS[factor]

        # Identify risk factors (anything >= 7 is high)
        risk_factors = []
        if factors.technical_complexity >= 7:
            risk_factors.append("High technical complexity - may require specialized expertise")
        if factors.business_value >= 8:
            risk_factors.append("High business value - requires extra scrutiny and testing")
        if factors.risk_level >= 7:
            risk_factors.append("High risk level - consider proof of concept first")
        if factors.uncertainty >= 7:
            risk_factors.append("High uncertainty - may need spikes or research")
        if factors.dependencies >= 5:
            risk_factors.append("Many dependencies - coordination overhead")

        return round(weighted_score, 2), risk_factors


# Three-Point Estimator
class ThreePointEstimator:
    """Three-point estimation using PERT formula"""

    @staticmethod
    def calculate_pert_estimate(three_point: ThreePointEstimate) -> Dict:
        """
        Calculate PERT estimate: (O + 4M + P) / 6

        PERT = Program Evaluation and Review Technique
        Gives more weight to the most likely estimate

        Args:
            three_point: ThreePointEstimate input

        Returns:
            Dict with PERT estimate, range, and standard deviation
        """
        o = three_point.optimistic_hours
        m = three_point.most_likely_hours
        p = three_point.pessimistic_hours

        # PERT formula
        pert_estimate = (o + 4 * m + p) / 6

        # Standard deviation (used for confidence intervals)
        # σ = (P - O) / 6
        std_dev = (p - o) / 6

        # 68% confidence interval (±1 σ)
        ci_68_min = pert_estimate - std_dev
        ci_68_max = pert_estimate + std_dev

        # 95% confidence interval (±2 σ)
        ci_95_min = max(0, pert_estimate - 2 * std_dev)
        ci_95_max = pert_estimate + 2 * std_dev

        return {
            'pert_estimate': round(pert_estimate, 2),
            'optimistic': o,
            'most_likely': m,
            'pessimistic': p,
            'range': f"{o}-{p} hours",
            'standard_deviation': round(std_dev, 2),
            'confidence_68': {
                'min': round(ci_68_min, 2),
                'max': round(ci_68_max, 2)
            },
            'confidence_95': {
                'min': round(ci_95_min, 2),
                'max': round(ci_95_max, 2)
            }
        }


# Confidence Interval Calculator
class ConfidenceIntervalCalculator:
    """Calculate confidence intervals for story points"""

    @staticmethod
    def calculate_intervals(story_points: int) -> Tuple[ConfidenceInterval, ConfidenceInterval]:
        """
        Calculate ±10% and ±25% confidence intervals

        Args:
            story_points: Fibonacci story point value

        Returns:
            Tuple of (narrow_interval, wide_interval)
        """
        # Narrow interval (±10%)
        narrow_min = story_points * 0.90
        narrow_max = story_points * 1.10

        narrow = ConfidenceInterval(
            min=round(narrow_min, 1),
            max=round(narrow_max, 1),
            percentage="±10%"
        )

        # Wide interval (±25%)
        wide_min = story_points * 0.75
        wide_max = story_points * 1.25

        wide = ConfidenceInterval(
            min=round(wide_min, 1),
            max=round(wide_max, 1),
            percentage="±25%"
        )

        return narrow, wide


# Main Story Point Estimator
class StoryPointEstimator:
    """Main estimator orchestrating all calculations"""

    @classmethod
    def estimate(cls, request: StoryPointRequest) -> StoryPointResponse:
        """
        Perform complete story point estimation

        Args:
            request: StoryPointRequest with all inputs

        Returns:
            StoryPointResponse with estimation results
        """
        # 1. Calculate complexity score
        complexity_score, risk_factors = ComplexityCalculator.calculate_complexity_score(
            request.complexity_factors
        )

        # 2. Map to Fibonacci
        fibonacci_points = FibonacciMapper.map_to_fibonacci(complexity_score)

        # 3. Calculate confidence intervals
        confidence_narrow, confidence_wide = ConfidenceIntervalCalculator.calculate_intervals(
            fibonacci_points
        )

        # 4. Calculate hours estimate (if three-point provided)
        hours_estimate = None
        if request.three_point:
            hours_estimate = ThreePointEstimator.calculate_pert_estimate(request.three_point)

        # 5. Generate reasoning
        reasoning = cls._generate_reasoning(
            request.complexity_factors,
            complexity_score,
            fibonacci_points
        )

        # 6. Generate recommendations
        recommendations = cls._generate_recommendations(
            fibonacci_points,
            request.complexity_factors,
            risk_factors
        )

        return StoryPointResponse(
            story_name=request.story_name,
            fibonacci_points=fibonacci_points,
            complexity_score=complexity_score,
            confidence_narrow=confidence_narrow,
            confidence_wide=confidence_wide,
            hours_estimate=hours_estimate,
            reasoning=reasoning,
            risk_factors=risk_factors,
            recommendations=recommendations
        )

    @staticmethod
    def _generate_reasoning(
        factors: ComplexityFactors,
        complexity_score: float,
        fibonacci_points: int
    ) -> str:
        """Generate human-readable reasoning for the estimate"""
        parts = []

        # Technical complexity
        if factors.technical_complexity >= 7:
            parts.append("high technical complexity")
        elif factors.technical_complexity >= 4:
            parts.append("moderate technical complexity")
        else:
            parts.append("low technical complexity")

        # Business value
        if factors.business_value >= 8:
            parts.append("very high business value")
        elif factors.business_value >= 5:
            parts.append("significant business value")

        # Risk
        if factors.risk_level >= 7:
            parts.append("high risk")
        elif factors.risk_level >= 4:
            parts.append("moderate risk")

        # Uncertainty
        if factors.uncertainty >= 7:
            parts.append("high uncertainty")

        # Dependencies
        if factors.dependencies >= 5:
            parts.append(f"{factors.dependencies} dependencies")

        reasoning = f"Estimated at {fibonacci_points} story points ({FibonacciMapper.get_description(fibonacci_points)}) "
        reasoning += f"based on {', '.join(parts)}. "
        reasoning += f"Complexity score: {complexity_score}/100."

        return reasoning

    @staticmethod
    def _generate_recommendations(
        fibonacci_points: int,
        factors: ComplexityFactors,
        risk_factors: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Large story warning
        if fibonacci_points >= 13:
            recommendations.append(
                "⚠️ Story is very large - strongly consider splitting into smaller stories (target: 3-5 points each)"
            )

        # High uncertainty
        if factors.uncertainty >= 7:
            recommendations.append(
                "📊 Create a spike story to reduce uncertainty before implementation"
            )

        # High risk
        if factors.risk_level >= 7:
            recommendations.append(
                "🔬 Consider proof of concept or prototype to validate approach"
            )

        # High technical complexity
        if factors.technical_complexity >= 8:
            recommendations.append(
                "👥 Pair programming recommended - complex technical implementation"
            )

        # Many dependencies
        if factors.dependencies >= 5:
            recommendations.append(
                "🔗 Review and document all dependencies - create coordination plan"
            )

        # High business value + high risk
        if factors.business_value >= 8 and factors.risk_level >= 6:
            recommendations.append(
                "🎯 High value + risk - extra testing, code review, and stakeholder demos required"
            )

        return recommendations


# Utility function for quick estimation
def quick_estimate(
    technical_complexity: int,
    business_value: int,
    risk_level: int
) -> int:
    """
    Quick story point estimation with minimal inputs

    Args:
        technical_complexity: 1-10
        business_value: 1-10
        risk_level: 1-10

    Returns:
        Fibonacci story points
    """
    factors = ComplexityFactors(
        technical_complexity=technical_complexity,
        business_value=business_value,
        risk_level=risk_level
    )

    request = StoryPointRequest(
        story_name="Quick Estimate",
        complexity_factors=factors
    )

    response = StoryPointEstimator.estimate(request)
    return response.fibonacci_points
