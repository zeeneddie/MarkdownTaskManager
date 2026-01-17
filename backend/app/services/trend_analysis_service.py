"""
Trend Analysis Service

Week 53 Day 5: Performance Trend Analysis
Predictive analytics for agent performance forecasting and anomaly detection.

Author: Claude Code (Week 53 Day 5)
Date: 2025-11-25
"""

import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evolution_dashboard_service import (
    EvolutionDashboardService,
    AgentPerformanceMetrics,
    TimeRange
)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class TrendType(str, Enum):
    """Types of trends."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class AnomalyType(str, Enum):
    """Types of anomalies."""
    SUDDEN_DROP = "sudden_drop"  # Abrupt performance decrease
    SUDDEN_SPIKE = "sudden_spike"  # Unusual performance increase
    OSCILLATION = "oscillation"  # Unstable, swinging performance
    PLATEAU = "plateau"  # Performance stuck at same level


class AnomalySeverity(str, Enum):
    """Severity levels for anomalies."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TrendForecast:
    """Predicted future performance."""
    agent_id: str
    forecast_days: int
    predicted_success_rate: float
    confidence_interval: Tuple[float, float]  # (low, high)
    confidence_level: float  # 0-1
    trend_direction: TrendType
    expected_change: float  # % change from current
    forecast_date: datetime


@dataclass
class PerformanceAnomaly:
    """Detected performance anomaly."""
    agent_id: str
    anomaly_type: AnomalyType
    detected_at: datetime
    severity: str  # LOW/MEDIUM/HIGH/CRITICAL
    current_value: float
    expected_value: float
    deviation: float
    description: str
    recommended_action: str


@dataclass
class TrendAnalysis:
    """Complete trend analysis."""
    agent_id: str
    time_range: TimeRange
    current_performance: float
    trend_type: TrendType
    trend_strength: float  # 0-1 (how strong is trend)
    volatility: float  # 0-1 (how unstable)
    forecasts: List[TrendForecast]
    anomalies: List[PerformanceAnomaly]
    recommendations: List[str]
    analysis_date: datetime


@dataclass
class ComparativeAnalysis:
    """Compare multiple agents."""
    best_performer: str
    worst_performer: str
    average_performance: float
    performance_spread: float
    converging: bool  # Are agents becoming more similar?
    diverging: bool  # Are agents becoming more different?
    outliers: List[str]


# ============================================================================
# TREND ANALYSIS SERVICE
# ============================================================================

class TrendAnalysisService:
    """
    Performance trend analysis and forecasting service.

    Features:
    - Trend detection (improving/stable/declining/volatile)
    - Performance forecasting (predictive analytics)
    - Anomaly detection (sudden drops, spikes, oscillations)
    - Comparative analysis (compare multiple agents)
    - Recommendations generation
    """

    def __init__(self, db: AsyncSession):
        """Initialize trend analysis service."""
        self.db = db
        self.dashboard_service = EvolutionDashboardService(db)

    # ========================================================================
    # TREND DETECTION
    # ========================================================================

    async def analyze_agent_trend(
        self,
        agent_id: str,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> TrendAnalysis:
        """
        Analyze performance trend for specific agent.

        Args:
            agent_id: Agent to analyze
            time_range: Time period for analysis

        Returns:
            Complete trend analysis with forecasts and anomalies
        """
        # Get performance metrics
        metrics = await self.dashboard_service.get_agent_performance_trends(
            agent_id, time_range
        )

        # Get daily success rates
        daily_rates = metrics.daily_success_rates or []
        if len(daily_rates) < 7:
            return TrendAnalysis(
                agent_id=agent_id,
                time_range=time_range,
                current_performance=metrics.success_rate,
                trend_type=TrendType.INSUFFICIENT_DATA,
                trend_strength=0.0,
                volatility=0.0,
                forecasts=[],
                anomalies=[],
                recommendations=["Need at least 7 days of data for trend analysis"],
                analysis_date=datetime.now(timezone.utc)
            )

        # Extract success rates
        success_rates = [rate for _, rate in daily_rates]

        # Detect trend type and strength
        trend_type, trend_strength = self._detect_trend(success_rates)

        # Calculate volatility
        volatility = self._calculate_volatility(success_rates)

        # Generate forecasts
        forecasts = self._generate_forecasts(agent_id, success_rates, trend_type)

        # Detect anomalies
        anomalies = self._detect_anomalies(agent_id, success_rates)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics, trend_type, volatility, anomalies
        )

        return TrendAnalysis(
            agent_id=agent_id,
            time_range=time_range,
            current_performance=metrics.success_rate,
            trend_type=trend_type,
            trend_strength=trend_strength,
            volatility=volatility,
            forecasts=forecasts,
            anomalies=anomalies,
            recommendations=recommendations,
            analysis_date=datetime.now(timezone.utc)
        )

    def _detect_trend(
        self,
        values: List[float]
    ) -> Tuple[TrendType, float]:
        """
        Detect trend type and strength using linear regression.

        Args:
            values: Time series of performance values

        Returns:
            (trend_type, strength) where strength is 0-1
        """
        if len(values) < 7:
            return TrendType.INSUFFICIENT_DATA, 0.0

        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values

        # Calculate slope (trend direction)
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return TrendType.STABLE, 0.0

        slope = numerator / denominator

        # Calculate R² (trend strength)
        y_pred = [y_mean + slope * (x[i] - x_mean) for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        strength = max(0.0, min(1.0, r_squared))  # Clamp to 0-1

        # Calculate volatility for volatile check
        if len(values) >= 3:
            changes = [abs(values[i+1] - values[i]) for i in range(len(values)-1)]
            avg_change = sum(changes) / len(changes)
            volatility_ratio = avg_change / (y_mean if y_mean > 0 else 1)

            if volatility_ratio > 0.15:  # More than 15% average change
                return TrendType.VOLATILE, strength

        # Determine trend type based on slope
        if abs(slope) < 0.1:  # Nearly flat
            return TrendType.STABLE, strength
        elif slope > 0.1:
            return TrendType.IMPROVING, strength
        else:
            return TrendType.DECLINING, strength

    def _calculate_volatility(self, values: List[float]) -> float:
        """
        Calculate performance volatility (0-1).

        Args:
            values: Performance values

        Returns:
            Volatility score (0=stable, 1=very volatile)
        """
        if len(values) < 2:
            return 0.0

        # Calculate standard deviation as % of mean
        mean = statistics.mean(values)
        if mean == 0:
            return 0.0

        stdev = statistics.stdev(values)
        coefficient_of_variation = stdev / mean

        # Normalize to 0-1 (CV of 0.3 = very volatile)
        volatility = min(1.0, coefficient_of_variation / 0.3)

        return volatility

    # ========================================================================
    # FORECASTING
    # ========================================================================

    def _generate_forecasts(
        self,
        agent_id: str,
        historical_values: List[float],
        trend_type: TrendType
    ) -> List[TrendForecast]:
        """
        Generate performance forecasts.

        Args:
            agent_id: Agent being forecasted
            historical_values: Historical performance data
            trend_type: Detected trend type

        Returns:
            List of forecasts for 7, 14, 30 days
        """
        if len(historical_values) < 7:
            return []

        forecasts = []
        current_value = historical_values[-1]

        # Calculate trend slope
        n = len(historical_values)
        x = list(range(n))
        y = historical_values

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        # Generate forecasts for 7, 14, 30 days
        for days in [7, 14, 30]:
            predicted = current_value + (slope * days)

            # Clamp to realistic range (0-100%)
            predicted = max(0.0, min(100.0, predicted))

            # Calculate confidence interval (wider for longer forecasts)
            stdev = statistics.stdev(historical_values) if len(historical_values) > 1 else 5.0
            margin = stdev * (1 + (days / 30))  # Wider margin for longer forecasts

            low = max(0.0, predicted - margin)
            high = min(100.0, predicted + margin)

            # Confidence decreases with forecast distance
            confidence = max(0.5, 1.0 - (days / 60))

            # Expected change
            expected_change = ((predicted - current_value) / current_value * 100) if current_value > 0 else 0

            forecasts.append(TrendForecast(
                agent_id=agent_id,
                forecast_days=days,
                predicted_success_rate=predicted,
                confidence_interval=(low, high),
                confidence_level=confidence,
                trend_direction=trend_type,
                expected_change=expected_change,
                forecast_date=datetime.now(timezone.utc) + timedelta(days=days)
            ))

        return forecasts

    # ========================================================================
    # ANOMALY DETECTION
    # ========================================================================

    def _detect_anomalies(
        self,
        agent_id: str,
        values: List[float]
    ) -> List[PerformanceAnomaly]:
        """
        Detect performance anomalies.

        Args:
            agent_id: Agent to check
            values: Performance time series

        Returns:
            List of detected anomalies
        """
        if len(values) < 7:
            return []

        anomalies = []
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        # Check for sudden drops
        for i in range(1, len(values)):
            drop = values[i-1] - values[i]
            if drop > (2 * stdev) and drop > 10:  # 2σ and >10% drop
                severity = self._calculate_severity(drop, stdev)
                anomalies.append(PerformanceAnomaly(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.SUDDEN_DROP,
                    detected_at=datetime.now(timezone.utc) - timedelta(days=len(values)-i),
                    severity=severity,
                    current_value=values[i],
                    expected_value=values[i-1],
                    deviation=drop,
                    description=f"Performance dropped {drop:.1f}% suddenly",
                    recommended_action="Investigate recent changes, consider rollback"
                ))

        # Check for oscillation (swinging back and forth)
        if len(values) >= 5:
            changes = [values[i+1] - values[i] for i in range(len(values)-1)]
            sign_changes = sum(1 for i in range(len(changes)-1) if changes[i] * changes[i+1] < 0)
            oscillation_ratio = sign_changes / len(changes)

            if oscillation_ratio > 0.6:  # More than 60% sign changes
                anomalies.append(PerformanceAnomaly(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.OSCILLATION,
                    detected_at=datetime.now(timezone.utc),
                    severity="MEDIUM",
                    current_value=values[-1],
                    expected_value=mean,
                    deviation=stdev,
                    description=f"Performance oscillating with {oscillation_ratio*100:.0f}% volatility",
                    recommended_action="Stabilize configuration, reduce experimental changes"
                ))

        # Check for plateau (stuck at same level)
        if len(values) >= 10:
            recent = values[-10:]
            recent_stdev = statistics.stdev(recent)
            if recent_stdev < 2.0 and mean > 0:  # Very little variation
                anomalies.append(PerformanceAnomaly(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.PLATEAU,
                    detected_at=datetime.now(timezone.utc),
                    severity="LOW",
                    current_value=values[-1],
                    expected_value=mean,
                    deviation=0.0,
                    description="Performance plateaued, no improvement or decline",
                    recommended_action="Consider new experiments to break plateau"
                ))

        return anomalies

    def _calculate_severity(self, deviation: float, stdev: float) -> str:
        """Calculate anomaly severity."""
        z_score = abs(deviation / stdev) if stdev > 0 else 0

        if z_score > 3:
            return "CRITICAL"
        elif z_score > 2.5:
            return "HIGH"
        elif z_score > 2:
            return "MEDIUM"
        else:
            return "LOW"

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    def _generate_recommendations(
        self,
        metrics: AgentPerformanceMetrics,
        trend_type: TrendType,
        volatility: float,
        anomalies: List[PerformanceAnomaly]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Trend-based recommendations
        if trend_type == TrendType.DECLINING:
            recommendations.append(
                f"⚠️ Performance declining at {abs(metrics.improvement_rate):.1f}%/week - "
                "Schedule experiment to reverse trend"
            )

        elif trend_type == TrendType.IMPROVING:
            recommendations.append(
                f"✅ Performance improving at {metrics.improvement_rate:.1f}%/week - "
                "Consider documenting successful changes"
            )

        elif trend_type == TrendType.VOLATILE:
            recommendations.append(
                "📊 High volatility detected - "
                "Reduce experimentation frequency, stabilize configuration"
            )

        elif trend_type == TrendType.STABLE:
            if metrics.success_rate < 75:
                recommendations.append(
                    "➡️ Performance stable but below target - "
                    "Schedule improvement experiment"
                )

        # Volatility-based recommendations
        if volatility > 0.5:
            recommendations.append(
                f"⚡ High volatility ({volatility*100:.0f}%) - "
                "Consider longer experiment durations for accurate results"
            )

        # Anomaly-based recommendations
        for anomaly in anomalies:
            if anomaly.severity in ["CRITICAL", "HIGH"]:
                recommendations.append(
                    f"🚨 {anomaly.anomaly_type.value}: {anomaly.description}"
                )

        # Performance level recommendations
        if metrics.success_rate < 60:
            recommendations.append(
                "❌ Critical performance level - "
                "Immediate intervention required, consider rollback"
            )
        elif metrics.success_rate >= 90:
            recommendations.append(
                "🎯 Excellent performance - "
                "Use as baseline for other agents"
            )

        return recommendations if recommendations else ["No specific recommendations - performance is acceptable"]

    # ========================================================================
    # COMPARATIVE ANALYSIS
    # ========================================================================

    async def compare_agents(
        self,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> ComparativeAnalysis:
        """
        Compare performance of all agents.

        Args:
            time_range: Time period for comparison

        Returns:
            Comparative analysis of all agents
        """
        # Get all agents
        all_agents = await self.dashboard_service.get_all_agents_performance(time_range)

        if not all_agents:
            raise ValueError("No agent data available")

        # Find best and worst performers
        sorted_agents = sorted(all_agents, key=lambda a: a.success_rate, reverse=True)
        best = sorted_agents[0]
        worst = sorted_agents[-1]

        # Calculate average and spread
        success_rates = [a.success_rate for a in all_agents]
        avg_performance = statistics.mean(success_rates)
        performance_spread = max(success_rates) - min(success_rates)

        # Detect outliers (agents >2σ from mean)
        stdev = statistics.stdev(success_rates) if len(success_rates) > 1 else 0
        outliers = [
            a.agent_id for a in all_agents
            if abs(a.success_rate - avg_performance) > (2 * stdev)
        ]

        # Check convergence/divergence (needs historical data)
        # Simplified: just check current spread
        converging = performance_spread < 20  # Agents within 20% of each other
        diverging = performance_spread > 40  # Agents spread >40%

        return ComparativeAnalysis(
            best_performer=best.agent_id,
            worst_performer=worst.agent_id,
            average_performance=avg_performance,
            performance_spread=performance_spread,
            converging=converging,
            diverging=diverging,
            outliers=outliers
        )
