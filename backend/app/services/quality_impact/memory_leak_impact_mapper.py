"""
Memory Leak Impact Mapper.

Maps memory/resource leaks to functionality impact with crash probability assessment.
"""

from typing import Dict, List, Optional, Any
from .types import (
    QualityIssue,
    FunctionalityImpact,
    QualityImpactMapping,
    IssueType,
    ImpactSeverity,
    RegulatoryRisk,
)
from .code_to_functionality_mapper import CodeToFunctionalityMapper


class MemoryLeakImpactMapper:
    """
    Maps memory and resource leak issues to functionality impact.

    Analyzes:
    - Function call graphs to identify entry points
    - Resource types (ADO, COM, File handles) for severity
    - Crash probability based on leak patterns
    - User flows affected
    """

    # Leak patterns and their severity
    LEAK_PATTERNS = {
        "NEVER_CLOSED": ImpactSeverity.CRITICAL,
        "LOOP_LEAK": ImpactSeverity.CRITICAL,
        "FUNCTION_LEAK": ImpactSeverity.HIGH,
        "EARLY_EXIT_LEAK": ImpactSeverity.HIGH,
        "REOPEN_LEAK": ImpactSeverity.HIGH,
        "SET_WITHOUT_CLOSE": ImpactSeverity.MEDIUM,
    }

    # Resource types and their impact
    RESOURCE_SEVERITY = {
        "ado_connection": ImpactSeverity.CRITICAL,
        "ado_recordset": ImpactSeverity.CRITICAL,
        "com_object": ImpactSeverity.HIGH,
        "file_handle": ImpactSeverity.MEDIUM,
        "session": ImpactSeverity.LOW,
    }

    # Crash probability multipliers based on pattern
    CRASH_PROBABILITY = {
        "NEVER_CLOSED": 0.9,
        "LOOP_LEAK": 0.95,
        "FUNCTION_LEAK": 0.7,
        "EARLY_EXIT_LEAK": 0.6,
        "REOPEN_LEAK": 0.5,
        "SET_WITHOUT_CLOSE": 0.3,
    }

    def __init__(self, code_mapper: CodeToFunctionalityMapper):
        """
        Initialize memory leak impact mapper.

        Args:
            code_mapper: Mapper for code to functionality resolution
        """
        self.code_mapper = code_mapper

    def map_issue(
        self,
        issue: QualityIssue,
        base_user_count: int = 1000,
        daily_executions: int = 10000,
    ) -> QualityImpactMapping:
        """
        Map a memory/resource leak issue to its functionality impact.

        Args:
            issue: The leak issue to map
            base_user_count: Base daily user count
            daily_executions: Estimated daily executions of affected code

        Returns:
            QualityImpactMapping with full impact analysis
        """
        # Get functionality mapping from code location
        file_path = issue.location.get("file", "")
        func_name = issue.location.get("function", "")

        func_mapping = self.code_mapper.map_code_location(
            file_path=file_path,
            function_name=func_name,
        )

        # Extract leak pattern from description
        leak_pattern = self._extract_leak_pattern(issue)

        # Calculate crash probability
        crash_prob = self._calculate_crash_probability(issue, leak_pattern)

        # Calculate user impact based on crash probability
        users_affected = self._calculate_user_impact(
            issue, base_user_count, crash_prob
        )

        # Build impact description
        business_impact = self._build_impact_description(
            issue, leak_pattern, crash_prob
        )
        stability_risk = self._estimate_stability_risk(
            issue, daily_executions, crash_prob
        )

        # Check for regulatory implications (healthcare stability is compliance-related)
        regulatory_risks = self._assess_stability_compliance(issue)

        impact = FunctionalityImpact(
            epic_id=func_mapping.epic_id,
            epic_name=func_mapping.epic_name,
            feature_id=func_mapping.feature_id,
            feature_name=func_mapping.feature_name,
            story_id=func_mapping.story_id,
            story_name=func_mapping.story_name,
            users_affected_daily=users_affected,
            business_process=func_mapping.epic_name or "Unknown",
            regulatory_risks=regulatory_risks,
            business_impact_description=business_impact,
            financial_risk_estimate=stability_risk,
            confidence_score=func_mapping.confidence,
        )

        return QualityImpactMapping(
            issue=issue,
            impact=impact,
        )

    def _extract_leak_pattern(self, issue: QualityIssue) -> str:
        """Extract leak pattern from issue description."""
        desc_upper = issue.description.upper()

        for pattern in self.LEAK_PATTERNS.keys():
            if pattern in desc_upper:
                return pattern

        # Check for pattern indicators
        if "loop" in desc_upper.lower():
            return "LOOP_LEAK"
        elif "never" in desc_upper.lower() and "close" in desc_upper.lower():
            return "NEVER_CLOSED"
        elif "exit" in desc_upper.lower() or "response.end" in desc_upper.lower():
            return "EARLY_EXIT_LEAK"

        return "FUNCTION_LEAK"  # Default

    def _calculate_crash_probability(
        self,
        issue: QualityIssue,
        leak_pattern: str,
    ) -> float:
        """Calculate probability of crash/instability."""
        base_prob = self.CRASH_PROBABILITY.get(leak_pattern, 0.5)

        # Adjust for severity
        severity_multiplier = {
            ImpactSeverity.CRITICAL: 1.0,
            ImpactSeverity.HIGH: 0.8,
            ImpactSeverity.MEDIUM: 0.6,
            ImpactSeverity.LOW: 0.4,
            ImpactSeverity.INFO: 0.2,
        }
        multiplier = severity_multiplier.get(issue.severity, 0.5)

        return min(1.0, base_prob * multiplier)

    def _calculate_user_impact(
        self,
        issue: QualityIssue,
        base_user_count: int,
        crash_probability: float,
    ) -> int:
        """Calculate estimated users affected by potential crashes."""
        # Users affected = users who might experience crash/hang
        return int(base_user_count * crash_probability)

    def _build_impact_description(
        self,
        issue: QualityIssue,
        leak_pattern: str,
        crash_probability: float,
    ) -> str:
        """Build business impact description for leak issue."""
        parts = []

        # Describe leak type
        leak_descriptions = {
            "NEVER_CLOSED": "Resource wordt nooit vrijgegeven",
            "LOOP_LEAK": "Resource lek in loop - snel uitputting",
            "FUNCTION_LEAK": "Resource niet vrijgegeven bij function exit",
            "EARLY_EXIT_LEAK": "Resource orphaned bij early exit",
            "REOPEN_LEAK": "Resource heropend zonder sluiting",
            "SET_WITHOUT_CLOSE": "Object vrijgegeven zonder close",
        }
        parts.append(leak_descriptions.get(leak_pattern, "Resource lek"))

        # Crash probability
        if crash_probability > 0.7:
            parts.append(f"Hoge crash kans ({int(crash_probability * 100)}%)")
        elif crash_probability > 0.4:
            parts.append(f"Matige crash kans ({int(crash_probability * 100)}%)")
        else:
            parts.append(f"Lage crash kans ({int(crash_probability * 100)}%)")

        # Resource exhaustion warning
        if leak_pattern in ("NEVER_CLOSED", "LOOP_LEAK"):
            parts.append("Server herstart mogelijk vereist")

        return ". ".join(parts)

    def _estimate_stability_risk(
        self,
        issue: QualityIssue,
        daily_executions: int,
        crash_probability: float,
    ) -> str:
        """Estimate stability risk and potential downtime."""
        expected_crashes = int(daily_executions * crash_probability * 0.01)

        if expected_crashes > 100:
            return f"~{expected_crashes} potentiele crashes/dag - kritieke stabiliteitsrisico"
        elif expected_crashes > 10:
            return f"~{expected_crashes} potentiele crashes/dag - hoog stabiliteitsrisico"
        elif expected_crashes > 0:
            return f"~{expected_crashes} potentiele crashes/dag - matig stabiliteitsrisico"
        else:
            return "Laag stabiliteitsrisico"

    def _assess_stability_compliance(
        self,
        issue: QualityIssue,
    ) -> List[RegulatoryRisk]:
        """Assess compliance implications of stability issues."""
        risks = []

        # Healthcare systems require high availability
        if issue.severity in (ImpactSeverity.CRITICAL, ImpactSeverity.HIGH):
            # System stability is part of NEN7510 continuity requirements
            risks.append(RegulatoryRisk.NEN7510)

        return risks

    def map_stability_finding(
        self,
        resource_type: str,
        leak_pattern: str,
        location: Dict[str, Any],
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> QualityImpactMapping:
        """
        Create leak issue from stability analysis finding.

        Args:
            resource_type: Type of leaked resource
            leak_pattern: Pattern of the leak
            location: Code location of the leak
            additional_info: Extra context about the leak

        Returns:
            QualityImpactMapping for the leak issue
        """
        # Determine severity
        resource_severity = self.RESOURCE_SEVERITY.get(
            resource_type, ImpactSeverity.MEDIUM
        )
        pattern_severity = self.LEAK_PATTERNS.get(leak_pattern, ImpactSeverity.MEDIUM)

        # Use the worse severity
        severities = [resource_severity, pattern_severity]
        severity_order = [
            ImpactSeverity.CRITICAL,
            ImpactSeverity.HIGH,
            ImpactSeverity.MEDIUM,
            ImpactSeverity.LOW,
            ImpactSeverity.INFO,
        ]
        severity = min(severities, key=lambda s: severity_order.index(s))

        issue = QualityIssue(
            issue_id=f"LEAK-{resource_type}-{location.get('line', 0)}",
            issue_type=IssueType.MEMORY_LEAK if "memory" in resource_type else IssueType.RESOURCE_LEAK,
            severity=severity,
            location=location,
            description=f"{leak_pattern}: {resource_type} leak in {location.get('function', 'unknown')}",
            recommendation=f"Ensure {resource_type} is properly closed before function exit",
            source_scanner="StabilityAnalyzer",
        )

        return self.map_issue(issue)

    def batch_map(
        self,
        issues: List[QualityIssue],
        base_user_count: int = 1000,
    ) -> List[QualityImpactMapping]:
        """
        Map multiple leak issues in batch.

        Args:
            issues: List of leak issues
            base_user_count: Base daily user count

        Returns:
            List of QualityImpactMapping
        """
        return [
            self.map_issue(issue, base_user_count)
            for issue in issues
            if issue.issue_type in (IssueType.MEMORY_LEAK, IssueType.RESOURCE_LEAK)
        ]
