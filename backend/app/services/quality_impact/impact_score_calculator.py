"""
Impact Score Calculator.

Calculates composite impact scores for quality issues based on multiple factors.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .types import (
    QualityIssue,
    FunctionalityImpact,
    QualityImpactMapping,
    ImpactSummary,
    IssueType,
    ImpactSeverity,
    RegulatoryRisk,
)


@dataclass
class ImpactWeights:
    """Configurable weights for impact score calculation."""
    severity_weight: float = 0.30
    user_impact_weight: float = 0.25
    regulatory_weight: float = 0.25
    functionality_weight: float = 0.20

    def validate(self) -> bool:
        """Validate weights sum to 1.0."""
        total = (
            self.severity_weight +
            self.user_impact_weight +
            self.regulatory_weight +
            self.functionality_weight
        )
        return abs(total - 1.0) < 0.001


class ImpactScoreCalculator:
    """
    Calculates and ranks impact scores for quality issues.

    Factors:
    - Severity (Critical=100, High=75, Medium=50, Low=25, Info=10)
    - User impact (normalized by project size)
    - Regulatory risk (GDPR/NEN7510 = high weight)
    - Functionality level (Epic > Feature > Story)
    """

    SEVERITY_SCORES = {
        ImpactSeverity.CRITICAL: 100,
        ImpactSeverity.HIGH: 75,
        ImpactSeverity.MEDIUM: 50,
        ImpactSeverity.LOW: 25,
        ImpactSeverity.INFO: 10,
    }

    REGULATORY_SCORES = {
        RegulatoryRisk.GDPR: 30,
        RegulatoryRisk.WGBO: 35,
        RegulatoryRisk.NEN7510: 30,
        RegulatoryRisk.HIPAA: 35,
        RegulatoryRisk.PCI_DSS: 25,
        RegulatoryRisk.SOX: 20,
        RegulatoryRisk.ISO27001: 15,
    }

    FUNCTIONALITY_SCORES = {
        "epic": 30,
        "feature": 20,
        "story": 10,
        "unknown": 5,
    }

    def __init__(
        self,
        weights: Optional[ImpactWeights] = None,
        max_daily_users: int = 10000,
    ):
        """
        Initialize impact score calculator.

        Args:
            weights: Custom impact weights
            max_daily_users: Maximum daily users for normalization
        """
        self.weights = weights or ImpactWeights()
        self.max_daily_users = max_daily_users

        if not self.weights.validate():
            raise ValueError("Impact weights must sum to 1.0")

    def calculate_score(self, mapping: QualityImpactMapping) -> float:
        """
        Calculate composite impact score for a mapping.

        Args:
            mapping: The quality impact mapping to score

        Returns:
            Impact score (0-100)
        """
        # 1. Severity score component
        severity_score = self.SEVERITY_SCORES.get(
            mapping.issue.severity, 25
        )

        # 2. User impact score component (normalized)
        user_score = min(100, (
            mapping.impact.users_affected_daily / self.max_daily_users
        ) * 100)

        # 3. Regulatory risk score component
        regulatory_score = 0
        for risk in mapping.impact.regulatory_risks:
            regulatory_score += self.REGULATORY_SCORES.get(risk, 10)
        regulatory_score = min(100, regulatory_score)

        # 4. Functionality level score component
        functionality_score = 0
        if mapping.impact.epic_id:
            functionality_score = self.FUNCTIONALITY_SCORES["epic"]
        elif mapping.impact.feature_id:
            functionality_score = self.FUNCTIONALITY_SCORES["feature"]
        elif mapping.impact.story_id:
            functionality_score = self.FUNCTIONALITY_SCORES["story"]
        else:
            functionality_score = self.FUNCTIONALITY_SCORES["unknown"]

        # Normalize functionality score to 0-100
        functionality_score = (functionality_score / 30) * 100

        # Calculate weighted score
        total_score = (
            severity_score * self.weights.severity_weight +
            user_score * self.weights.user_impact_weight +
            regulatory_score * self.weights.regulatory_weight +
            functionality_score * self.weights.functionality_weight
        )

        return round(total_score, 2)

    def rank_mappings(
        self,
        mappings: List[QualityImpactMapping],
    ) -> List[QualityImpactMapping]:
        """
        Calculate scores and rank mappings by impact.

        Args:
            mappings: List of quality impact mappings

        Returns:
            Mappings sorted by impact score (highest first), with scores and ranks set
        """
        # Calculate scores
        for mapping in mappings:
            mapping.impact_score = self.calculate_score(mapping)

        # Sort by score (descending)
        sorted_mappings = sorted(
            mappings,
            key=lambda m: m.impact_score,
            reverse=True,
        )

        # Assign ranks
        for i, mapping in enumerate(sorted_mappings, 1):
            mapping.priority_rank = i

        return sorted_mappings

    def calculate_health_score(
        self,
        mappings: List[QualityImpactMapping],
    ) -> float:
        """
        Calculate overall health score based on issues.

        Health = 100 - (weighted issue impact)

        Args:
            mappings: List of quality impact mappings

        Returns:
            Health score (0-100, higher is better)
        """
        if not mappings:
            return 100.0

        # Count by severity
        severity_counts = {
            ImpactSeverity.CRITICAL: 0,
            ImpactSeverity.HIGH: 0,
            ImpactSeverity.MEDIUM: 0,
            ImpactSeverity.LOW: 0,
            ImpactSeverity.INFO: 0,
        }

        for mapping in mappings:
            severity_counts[mapping.issue.severity] = (
                severity_counts.get(mapping.issue.severity, 0) + 1
            )

        # Calculate penalty
        penalty = (
            severity_counts[ImpactSeverity.CRITICAL] * 20 +
            severity_counts[ImpactSeverity.HIGH] * 10 +
            severity_counts[ImpactSeverity.MEDIUM] * 5 +
            severity_counts[ImpactSeverity.LOW] * 2 +
            severity_counts[ImpactSeverity.INFO] * 0.5
        )

        return max(0.0, 100.0 - penalty)

    def create_summary(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        mappings: List[QualityImpactMapping],
    ) -> ImpactSummary:
        """
        Create impact summary for a functionality entity.

        Args:
            entity_type: "epic", "feature", or "story"
            entity_id: Entity identifier
            entity_name: Entity name
            mappings: Mappings associated with this entity

        Returns:
            ImpactSummary with aggregated data
        """
        # Count by severity
        critical_count = sum(
            1 for m in mappings
            if m.issue.severity == ImpactSeverity.CRITICAL
        )
        high_count = sum(
            1 for m in mappings
            if m.issue.severity == ImpactSeverity.HIGH
        )
        medium_count = sum(
            1 for m in mappings
            if m.issue.severity == ImpactSeverity.MEDIUM
        )
        low_count = sum(
            1 for m in mappings
            if m.issue.severity == ImpactSeverity.LOW
        )

        # Aggregate regulatory risks
        all_risks = set()
        for mapping in mappings:
            all_risks.update(mapping.impact.regulatory_risks)

        # Get max user impact
        max_users = max(
            (m.impact.users_affected_daily for m in mappings),
            default=0,
        )

        # Get top issues by impact score
        ranked = self.rank_mappings(list(mappings))
        top_issues = ranked[:5]

        # Calculate health score
        health = self.calculate_health_score(list(mappings))

        # Estimate daily risk
        if critical_count > 0:
            daily_risk = f"{critical_count} kritieke issues - directe actie vereist"
        elif high_count > 0:
            daily_risk = f"{high_count} hoge prioriteit issues"
        elif medium_count > 0:
            daily_risk = f"{medium_count} medium prioriteit issues"
        else:
            daily_risk = "Laag risico"

        return ImpactSummary(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            health_score=health,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            total_issues=len(mappings),
            top_issues=top_issues,
            regulatory_risks=list(all_risks),
            estimated_users_affected=max_users,
            estimated_daily_risk=daily_risk,
        )

    def get_score_breakdown(
        self,
        mapping: QualityImpactMapping,
    ) -> Dict[str, Any]:
        """
        Get detailed breakdown of how score was calculated.

        Args:
            mapping: The mapping to analyze

        Returns:
            Dictionary with score components
        """
        severity_score = self.SEVERITY_SCORES.get(
            mapping.issue.severity, 25
        )
        user_score = min(100, (
            mapping.impact.users_affected_daily / self.max_daily_users
        ) * 100)

        regulatory_score = 0
        regulatory_breakdown = {}
        for risk in mapping.impact.regulatory_risks:
            risk_score = self.REGULATORY_SCORES.get(risk, 10)
            regulatory_breakdown[risk.value] = risk_score
            regulatory_score += risk_score
        regulatory_score = min(100, regulatory_score)

        functionality_level = "unknown"
        if mapping.impact.epic_id:
            functionality_level = "epic"
        elif mapping.impact.feature_id:
            functionality_level = "feature"
        elif mapping.impact.story_id:
            functionality_level = "story"

        functionality_score = (
            self.FUNCTIONALITY_SCORES[functionality_level] / 30
        ) * 100

        return {
            "total_score": mapping.impact_score,
            "components": {
                "severity": {
                    "value": mapping.issue.severity.value,
                    "raw_score": severity_score,
                    "weight": self.weights.severity_weight,
                    "weighted_score": severity_score * self.weights.severity_weight,
                },
                "user_impact": {
                    "users_affected": mapping.impact.users_affected_daily,
                    "max_users": self.max_daily_users,
                    "raw_score": round(user_score, 2),
                    "weight": self.weights.user_impact_weight,
                    "weighted_score": round(user_score * self.weights.user_impact_weight, 2),
                },
                "regulatory": {
                    "risks": regulatory_breakdown,
                    "raw_score": regulatory_score,
                    "weight": self.weights.regulatory_weight,
                    "weighted_score": round(regulatory_score * self.weights.regulatory_weight, 2),
                },
                "functionality": {
                    "level": functionality_level,
                    "raw_score": round(functionality_score, 2),
                    "weight": self.weights.functionality_weight,
                    "weighted_score": round(functionality_score * self.weights.functionality_weight, 2),
                },
            },
        }
