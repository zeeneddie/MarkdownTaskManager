"""
Security Impact Mapper.

Maps security vulnerabilities to functionality impact with regulatory risk assessment.
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


class SecurityImpactMapper:
    """
    Maps security issues to functionality impact.

    Analyzes:
    - Data flow to identify exposed features
    - Regulatory risks (GDPR, WGBO, NEN7510)
    - User impact based on affected functionality
    - Business impact estimation
    """

    # CWE to regulatory risk mappings
    CWE_REGULATORY_RISKS = {
        "CWE-89": [RegulatoryRisk.GDPR, RegulatoryRisk.NEN7510],  # SQL Injection
        "CWE-79": [RegulatoryRisk.GDPR],  # XSS
        "CWE-798": [RegulatoryRisk.NEN7510, RegulatoryRisk.ISO27001],  # Hardcoded creds
        "CWE-311": [RegulatoryRisk.GDPR, RegulatoryRisk.WGBO, RegulatoryRisk.NEN7510],  # Missing encryption
        "CWE-200": [RegulatoryRisk.GDPR, RegulatoryRisk.WGBO],  # Sensitive data exposure
        "CWE-287": [RegulatoryRisk.NEN7510, RegulatoryRisk.ISO27001],  # Auth bypass
        "CWE-306": [RegulatoryRisk.NEN7510],  # Missing auth
        "CWE-352": [RegulatoryRisk.NEN7510],  # CSRF
    }

    # Sensitive data patterns and their regulatory implications
    SENSITIVE_DATA_PATTERNS = {
        "bsn": (RegulatoryRisk.GDPR, RegulatoryRisk.WGBO),
        "patient": (RegulatoryRisk.WGBO, RegulatoryRisk.GDPR),
        "diagnose": (RegulatoryRisk.WGBO,),
        "behandeling": (RegulatoryRisk.WGBO,),
        "wachtwoord": (RegulatoryRisk.NEN7510,),
        "password": (RegulatoryRisk.NEN7510,),
        "creditcard": (RegulatoryRisk.PCI_DSS,),
        "iban": (RegulatoryRisk.GDPR,),
        "email": (RegulatoryRisk.GDPR,),
        "telefoon": (RegulatoryRisk.GDPR,),
        "adres": (RegulatoryRisk.GDPR,),
    }

    # Base user impact multipliers
    SEVERITY_USER_MULTIPLIER = {
        ImpactSeverity.CRITICAL: 1.0,
        ImpactSeverity.HIGH: 0.7,
        ImpactSeverity.MEDIUM: 0.4,
        ImpactSeverity.LOW: 0.1,
        ImpactSeverity.INFO: 0.0,
    }

    def __init__(self, code_mapper: CodeToFunctionalityMapper):
        """
        Initialize security impact mapper.

        Args:
            code_mapper: Mapper for code to functionality resolution
        """
        self.code_mapper = code_mapper

    def map_issue(
        self,
        issue: QualityIssue,
        base_user_count: int = 1000,
    ) -> QualityImpactMapping:
        """
        Map a security issue to its functionality impact.

        Args:
            issue: The security/privacy issue to map
            base_user_count: Base daily user count for the project

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

        # Determine regulatory risks
        regulatory_risks = self._assess_regulatory_risks(issue)

        # Calculate user impact
        users_affected = self._calculate_user_impact(
            issue, base_user_count
        )

        # Build impact description
        business_impact = self._build_impact_description(issue, regulatory_risks)
        financial_risk = self._estimate_financial_risk(issue, regulatory_risks)

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
            financial_risk_estimate=financial_risk,
            confidence_score=func_mapping.confidence,
        )

        return QualityImpactMapping(
            issue=issue,
            impact=impact,
        )

    def _assess_regulatory_risks(self, issue: QualityIssue) -> List[RegulatoryRisk]:
        """Assess regulatory risks based on CWE and data exposure."""
        risks = set()

        # Check CWE-based risks
        if issue.cwe_id and issue.cwe_id in self.CWE_REGULATORY_RISKS:
            risks.update(self.CWE_REGULATORY_RISKS[issue.cwe_id])

        # Check data exposure patterns
        for data_item in issue.data_exposed:
            data_lower = data_item.lower()
            for pattern, pattern_risks in self.SENSITIVE_DATA_PATTERNS.items():
                if pattern in data_lower:
                    risks.update(pattern_risks)

        # Check description for sensitive data mentions
        desc_lower = issue.description.lower()
        for pattern, pattern_risks in self.SENSITIVE_DATA_PATTERNS.items():
            if pattern in desc_lower:
                risks.update(pattern_risks)

        return list(risks)

    def _calculate_user_impact(
        self,
        issue: QualityIssue,
        base_user_count: int,
    ) -> int:
        """Calculate estimated users affected daily."""
        multiplier = self.SEVERITY_USER_MULTIPLIER.get(issue.severity, 0.1)

        # Adjust for data exposure
        if issue.data_exposed:
            data_multiplier = min(1.0, len(issue.data_exposed) * 0.2)
            multiplier = max(multiplier, data_multiplier)

        return int(base_user_count * multiplier)

    def _build_impact_description(
        self,
        issue: QualityIssue,
        regulatory_risks: List[RegulatoryRisk],
    ) -> str:
        """Build business impact description."""
        parts = []

        if issue.severity == ImpactSeverity.CRITICAL:
            parts.append("KRITIEKE beveiligingskwetsbaarheid")
        elif issue.severity == ImpactSeverity.HIGH:
            parts.append("Ernstige beveiligingskwetsbaarheid")
        else:
            parts.append("Beveiligingsprobleem gedetecteerd")

        if issue.data_exposed:
            data_list = ", ".join(issue.data_exposed[:3])
            parts.append(f"Blootgestelde data: {data_list}")

        if regulatory_risks:
            risk_list = ", ".join(r.value for r in regulatory_risks)
            parts.append(f"Compliance risico's: {risk_list}")

        return ". ".join(parts)

    def _estimate_financial_risk(
        self,
        issue: QualityIssue,
        regulatory_risks: List[RegulatoryRisk],
    ) -> str:
        """Estimate financial risk based on severity and regulations."""
        if RegulatoryRisk.GDPR in regulatory_risks:
            if issue.severity == ImpactSeverity.CRITICAL:
                return "Mogelijke boete tot 4% jaaromzet (GDPR)"
            elif issue.severity == ImpactSeverity.HIGH:
                return "Mogelijke boete tot 2% jaaromzet (GDPR)"

        if RegulatoryRisk.NEN7510 in regulatory_risks:
            return "Risico op certificeringsverlies en contractbreuk"

        if RegulatoryRisk.WGBO in regulatory_risks:
            return "Risico op medisch tuchtrechtelijke gevolgen"

        if issue.severity == ImpactSeverity.CRITICAL:
            return "Hoog financieel risico - directe actie vereist"
        elif issue.severity == ImpactSeverity.HIGH:
            return "Significant financieel risico"

        return "Beperkt financieel risico"

    def batch_map(
        self,
        issues: List[QualityIssue],
        base_user_count: int = 1000,
    ) -> List[QualityImpactMapping]:
        """
        Map multiple security issues in batch.

        Args:
            issues: List of security issues
            base_user_count: Base daily user count

        Returns:
            List of QualityImpactMapping
        """
        return [
            self.map_issue(issue, base_user_count)
            for issue in issues
            if issue.issue_type in (IssueType.SECURITY, IssueType.PRIVACY)
        ]
