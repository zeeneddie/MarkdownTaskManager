"""
Performance Impact Mapper.

Maps performance issues (slow queries, N+1, missing indexes) to functionality impact.
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


class PerformanceImpactMapper:
    """
    Maps performance issues to functionality impact.

    Analyzes:
    - Query patterns to identify affected CRUD operations
    - Table usage to map to features
    - Latency impact estimation
    - User experience degradation
    """

    # Performance thresholds (ms)
    LATENCY_THRESHOLDS = {
        "excellent": 100,
        "good": 300,
        "acceptable": 1000,
        "poor": 3000,
        "critical": 10000,
    }

    # Severity based on latency impact
    LATENCY_SEVERITY = {
        "critical": ImpactSeverity.CRITICAL,
        "poor": ImpactSeverity.HIGH,
        "acceptable": ImpactSeverity.MEDIUM,
        "good": ImpactSeverity.LOW,
        "excellent": ImpactSeverity.INFO,
    }

    # Table to business domain mappings (common patterns)
    TABLE_DOMAIN_PATTERNS = {
        "patient": "Patientbeheer",
        "declaratie": "Declaratieverwerking",
        "factuur": "Facturatie",
        "afspraak": "Agendabeheer",
        "agenda": "Agendabeheer",
        "behandeling": "Behandelingen",
        "dossier": "Dossierbeheer",
        "user": "Gebruikersbeheer",
        "zorgverlener": "Zorgverlenerbeheer",
        "verzekeraar": "Verzekeringsbeheer",
        "tarief": "Tariefbeheer",
    }

    def __init__(self, code_mapper: CodeToFunctionalityMapper):
        """
        Initialize performance impact mapper.

        Args:
            code_mapper: Mapper for code to functionality resolution
        """
        self.code_mapper = code_mapper

    def map_issue(
        self,
        issue: QualityIssue,
        base_user_count: int = 1000,
        queries_per_user: int = 50,
    ) -> QualityImpactMapping:
        """
        Map a performance issue to its functionality impact.

        Args:
            issue: The performance issue to map
            base_user_count: Base daily user count
            queries_per_user: Average queries per user session

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

        # Try to identify domain from table names in description
        domain = self._identify_domain_from_issue(issue)
        if domain and not func_mapping.epic_name:
            func_mapping.epic_name = domain
            func_mapping.confidence = max(func_mapping.confidence, 0.6)

        # Calculate user impact
        users_affected = self._calculate_user_impact(issue, base_user_count)

        # Build impact description
        business_impact = self._build_impact_description(issue)
        latency_impact = self._estimate_latency_impact(issue, queries_per_user)

        impact = FunctionalityImpact(
            epic_id=func_mapping.epic_id,
            epic_name=func_mapping.epic_name,
            feature_id=func_mapping.feature_id,
            feature_name=func_mapping.feature_name or "Database Operations",
            story_id=func_mapping.story_id,
            story_name=func_mapping.story_name,
            users_affected_daily=users_affected,
            business_process=func_mapping.epic_name or "Unknown",
            regulatory_risks=[],  # Performance issues rarely have regulatory impact
            business_impact_description=business_impact,
            financial_risk_estimate=latency_impact,
            confidence_score=func_mapping.confidence,
        )

        return QualityImpactMapping(
            issue=issue,
            impact=impact,
        )

    def _identify_domain_from_issue(self, issue: QualityIssue) -> Optional[str]:
        """Identify business domain from issue description and location."""
        text = f"{issue.description} {issue.location.get('file', '')}".lower()

        for pattern, domain in self.TABLE_DOMAIN_PATTERNS.items():
            if pattern in text:
                return domain

        return None

    def _calculate_user_impact(
        self,
        issue: QualityIssue,
        base_user_count: int,
    ) -> int:
        """Calculate estimated users affected by performance issue."""
        # Performance issues typically affect all users of a feature
        severity_multipliers = {
            ImpactSeverity.CRITICAL: 1.0,
            ImpactSeverity.HIGH: 0.8,
            ImpactSeverity.MEDIUM: 0.5,
            ImpactSeverity.LOW: 0.3,
            ImpactSeverity.INFO: 0.1,
        }
        multiplier = severity_multipliers.get(issue.severity, 0.3)
        return int(base_user_count * multiplier)

    def _build_impact_description(self, issue: QualityIssue) -> str:
        """Build business impact description for performance issue."""
        parts = []

        # Classify the performance issue type
        desc_lower = issue.description.lower()

        if "n+1" in desc_lower:
            parts.append("N+1 query probleem gedetecteerd")
            parts.append("Exponentieel traag bij grote datasets")
        elif "index" in desc_lower:
            parts.append("Ontbrekende database index")
            parts.append("Trage zoekacties en rapportages")
        elif "full scan" in desc_lower or "table scan" in desc_lower:
            parts.append("Full table scan gedetecteerd")
            parts.append("Database onder zware belasting")
        elif "query" in desc_lower:
            parts.append("Trage database query")
        else:
            parts.append("Performance probleem")

        if issue.severity == ImpactSeverity.CRITICAL:
            parts.append("Directe gebruikersimpact verwacht")

        return ". ".join(parts)

    def _estimate_latency_impact(
        self,
        issue: QualityIssue,
        queries_per_user: int,
    ) -> str:
        """Estimate latency impact on user experience."""
        severity_latency = {
            ImpactSeverity.CRITICAL: "10+ seconden per actie",
            ImpactSeverity.HIGH: "3-10 seconden per actie",
            ImpactSeverity.MEDIUM: "1-3 seconden per actie",
            ImpactSeverity.LOW: "Merkbare vertraging (<1s)",
            ImpactSeverity.INFO: "Minimale vertraging",
        }

        base_impact = severity_latency.get(issue.severity, "Onbekende impact")

        if issue.severity in (ImpactSeverity.CRITICAL, ImpactSeverity.HIGH):
            return f"{base_impact}. Risico op time-outs en gefrustreerde gebruikers"
        return base_impact

    def map_query_issue(
        self,
        table_name: str,
        query_type: str,  # SELECT, INSERT, UPDATE, DELETE
        estimated_latency_ms: int,
        location: Dict[str, Any],
    ) -> QualityImpactMapping:
        """
        Create performance issue from query analysis.

        Args:
            table_name: Name of the affected table
            query_type: Type of SQL operation
            estimated_latency_ms: Estimated query latency
            location: Code location of the query

        Returns:
            QualityImpactMapping for the performance issue
        """
        # Determine severity from latency
        severity = ImpactSeverity.INFO
        for threshold_name, threshold_ms in sorted(
            self.LATENCY_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            if estimated_latency_ms >= threshold_ms:
                severity = self.LATENCY_SEVERITY[threshold_name]
                break

        issue = QualityIssue(
            issue_id=f"PERF-{table_name}-{query_type}",
            issue_type=IssueType.PERFORMANCE,
            severity=severity,
            location=location,
            description=f"Slow {query_type} on {table_name}: {estimated_latency_ms}ms",
            recommendation=f"Add index or optimize query on {table_name}",
            source_scanner="PerformanceAnalyzer",
        )

        return self.map_issue(issue)

    def batch_map(
        self,
        issues: List[QualityIssue],
        base_user_count: int = 1000,
    ) -> List[QualityImpactMapping]:
        """
        Map multiple performance issues in batch.

        Args:
            issues: List of performance issues
            base_user_count: Base daily user count

        Returns:
            List of QualityImpactMapping
        """
        return [
            self.map_issue(issue, base_user_count)
            for issue in issues
            if issue.issue_type == IssueType.PERFORMANCE
        ]
