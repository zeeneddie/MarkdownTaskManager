"""
Rule Completeness Checker - Week 101

Validates that extracted business rules cover all expected business areas.
Identifies gaps in rule coverage and provides recommendations.

Usage:
    checker = RuleCompletenessChecker()

    # Check completeness for a domain
    result = checker.check_completeness(rules, domain="healthcare")

    # Get gap analysis
    gaps = checker.find_coverage_gaps(rules, domain="ecommerce")

    # Get recommendations for missing areas
    recommendations = checker.get_recommendations(gaps)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


class BusinessArea(Enum):
    """Standard business areas that should have rules."""
    # Core areas (all domains)
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_VALIDATION = "data_validation"
    ERROR_HANDLING = "error_handling"
    AUDIT_LOGGING = "audit_logging"

    # Data management
    DATA_RETENTION = "data_retention"
    DATA_PRIVACY = "data_privacy"
    DATA_INTEGRITY = "data_integrity"

    # Process areas
    WORKFLOW = "workflow"
    STATE_TRANSITIONS = "state_transitions"
    BUSINESS_PROCESS = "business_process"

    # Financial
    PRICING = "pricing"
    BILLING = "billing"
    PAYMENT = "payment"
    REFUND = "refund"

    # User management
    USER_REGISTRATION = "user_registration"
    USER_PROFILE = "user_profile"
    USER_PREFERENCES = "user_preferences"

    # Communication
    NOTIFICATIONS = "notifications"
    EMAIL = "email"
    ALERTS = "alerts"

    # Compliance
    GDPR = "gdpr"
    SECURITY = "security"
    CONSENT = "consent"


@dataclass
class CoverageMetric:
    """Coverage metric for a business area."""
    area: BusinessArea
    expected: bool  # Is this area expected for the domain?
    covered: bool   # Are there rules covering this area?
    rule_count: int
    confidence: float  # 0-1 confidence in coverage
    sample_rules: List[str] = field(default_factory=list)


@dataclass
class CoverageGap:
    """Represents a gap in rule coverage."""
    area: BusinessArea
    severity: str  # critical, high, medium, low
    description: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CompletenessReport:
    """Complete report of rule coverage analysis."""
    domain: str
    total_rules: int
    coverage_percentage: float
    metrics: List[CoverageMetric]
    gaps: List[CoverageGap]
    strengths: List[str]
    recommendations: List[str]


@dataclass
class ExtractedRule:
    """Simplified rule structure for checking."""
    id: str
    text: str
    rule_type: str
    source_file: str = ""
    tags: List[str] = field(default_factory=list)


class RuleCompletenessChecker:
    """
    Service for checking completeness of extracted business rules.

    Validates that rules cover all expected business areas for a domain
    and identifies gaps that need attention.
    """

    def __init__(self):
        self._domain_requirements = self._load_domain_requirements()
        self._area_keywords = self._load_area_keywords()
        self._severity_levels = self._load_severity_levels()

    # =========================================================================
    # Domain Requirements
    # =========================================================================

    def _load_domain_requirements(self) -> Dict[str, Set[BusinessArea]]:
        """Load expected business areas for each domain."""
        return {
            "healthcare": {
                BusinessArea.AUTHENTICATION,
                BusinessArea.AUTHORIZATION,
                BusinessArea.DATA_VALIDATION,
                BusinessArea.DATA_PRIVACY,
                BusinessArea.DATA_RETENTION,
                BusinessArea.AUDIT_LOGGING,
                BusinessArea.CONSENT,
                BusinessArea.GDPR,
                BusinessArea.SECURITY,
                BusinessArea.WORKFLOW,
                BusinessArea.STATE_TRANSITIONS,
                BusinessArea.NOTIFICATIONS,
                BusinessArea.USER_REGISTRATION,
                BusinessArea.ERROR_HANDLING,
            },
            "finance": {
                BusinessArea.AUTHENTICATION,
                BusinessArea.AUTHORIZATION,
                BusinessArea.DATA_VALIDATION,
                BusinessArea.DATA_INTEGRITY,
                BusinessArea.AUDIT_LOGGING,
                BusinessArea.SECURITY,
                BusinessArea.PRICING,
                BusinessArea.BILLING,
                BusinessArea.PAYMENT,
                BusinessArea.REFUND,
                BusinessArea.WORKFLOW,
                BusinessArea.STATE_TRANSITIONS,
                BusinessArea.NOTIFICATIONS,
                BusinessArea.USER_REGISTRATION,
                BusinessArea.ERROR_HANDLING,
                BusinessArea.GDPR,
            },
            "ecommerce": {
                BusinessArea.AUTHENTICATION,
                BusinessArea.AUTHORIZATION,
                BusinessArea.DATA_VALIDATION,
                BusinessArea.PRICING,
                BusinessArea.BILLING,
                BusinessArea.PAYMENT,
                BusinessArea.REFUND,
                BusinessArea.WORKFLOW,
                BusinessArea.STATE_TRANSITIONS,
                BusinessArea.NOTIFICATIONS,
                BusinessArea.EMAIL,
                BusinessArea.USER_REGISTRATION,
                BusinessArea.USER_PROFILE,
                BusinessArea.USER_PREFERENCES,
                BusinessArea.GDPR,
                BusinessArea.CONSENT,
                BusinessArea.ERROR_HANDLING,
            },
            "generic": {
                BusinessArea.AUTHENTICATION,
                BusinessArea.AUTHORIZATION,
                BusinessArea.DATA_VALIDATION,
                BusinessArea.ERROR_HANDLING,
                BusinessArea.AUDIT_LOGGING,
                BusinessArea.USER_REGISTRATION,
            },
        }

    def _load_area_keywords(self) -> Dict[BusinessArea, List[str]]:
        """Load keywords that indicate coverage of a business area."""
        return {
            BusinessArea.AUTHENTICATION: [
                "login", "password", "authenticate", "credential", "token",
                "session", "signin", "signout", "logout", "mfa", "2fa",
            ],
            BusinessArea.AUTHORIZATION: [
                "permission", "role", "access", "authorize", "admin",
                "privilege", "rbac", "acl", "can ", "allowed", "forbidden",
            ],
            BusinessArea.DATA_VALIDATION: [
                "valid", "required", "format", "pattern", "constraint",
                "must be", "cannot be", "should be", "check", "verify",
            ],
            BusinessArea.ERROR_HANDLING: [
                "error", "exception", "fail", "invalid", "reject",
                "handle", "catch", "throw", "warning", "message",
            ],
            BusinessArea.AUDIT_LOGGING: [
                "audit", "log", "track", "record", "history", "trail",
                "monitor", "event", "action", "activity",
            ],
            BusinessArea.DATA_RETENTION: [
                "retention", "expire", "delete", "archive", "purge",
                "keep", "store", "ttl", "lifecycle", "cleanup",
            ],
            BusinessArea.DATA_PRIVACY: [
                "privacy", "personal", "pii", "sensitive", "confidential",
                "anonymize", "pseudonymize", "encrypt", "mask",
            ],
            BusinessArea.DATA_INTEGRITY: [
                "integrity", "consistent", "corrupt", "checksum", "hash",
                "validate", "verify", "sync", "reconcile",
            ],
            BusinessArea.WORKFLOW: [
                "workflow", "process", "step", "stage", "pipeline",
                "flow", "sequence", "order", "procedure",
            ],
            BusinessArea.STATE_TRANSITIONS: [
                "state", "status", "transition", "change", "move",
                "pending", "approved", "rejected", "complete",
            ],
            BusinessArea.BUSINESS_PROCESS: [
                "business", "process", "operation", "procedure", "rule",
                "policy", "guideline", "standard",
            ],
            BusinessArea.PRICING: [
                "price", "cost", "rate", "fee", "discount", "tax",
                "amount", "calculate", "charge",
            ],
            BusinessArea.BILLING: [
                "bill", "invoice", "statement", "charge", "account",
                "balance", "due", "outstanding",
            ],
            BusinessArea.PAYMENT: [
                "payment", "pay", "credit", "debit", "card", "transfer",
                "transaction", "settle", "process",
            ],
            BusinessArea.REFUND: [
                "refund", "return", "cancel", "reverse", "chargeback",
                "credit", "reimburs", "compensat",
            ],
            BusinessArea.USER_REGISTRATION: [
                "register", "signup", "create account", "enroll",
                "onboard", "new user", "join",
            ],
            BusinessArea.USER_PROFILE: [
                "profile", "account", "settings", "preferences", "info",
                "details", "personal", "update",
            ],
            BusinessArea.USER_PREFERENCES: [
                "preference", "setting", "option", "configure", "customize",
                "default", "choice",
            ],
            BusinessArea.NOTIFICATIONS: [
                "notification", "notify", "alert", "message", "remind",
                "inform", "push", "bell",
            ],
            BusinessArea.EMAIL: [
                "email", "mail", "send", "deliver", "template",
                "subject", "body", "recipient",
            ],
            BusinessArea.ALERTS: [
                "alert", "alarm", "warning", "critical", "urgent",
                "immediate", "escalate",
            ],
            BusinessArea.GDPR: [
                "gdpr", "data subject", "consent", "right to", "erasure",
                "portability", "processing", "controller", "processor",
            ],
            BusinessArea.SECURITY: [
                "security", "secure", "encrypt", "protect", "safe",
                "threat", "vulnerability", "attack", "breach",
            ],
            BusinessArea.CONSENT: [
                "consent", "agree", "accept", "opt-in", "opt-out",
                "permission", "allow", "grant",
            ],
        }

    def _load_severity_levels(self) -> Dict[BusinessArea, str]:
        """Load severity level for missing each business area."""
        critical = {
            BusinessArea.AUTHENTICATION,
            BusinessArea.AUTHORIZATION,
            BusinessArea.DATA_PRIVACY,
            BusinessArea.SECURITY,
            BusinessArea.PAYMENT,
        }

        high = {
            BusinessArea.DATA_VALIDATION,
            BusinessArea.ERROR_HANDLING,
            BusinessArea.AUDIT_LOGGING,
            BusinessArea.GDPR,
            BusinessArea.CONSENT,
            BusinessArea.DATA_INTEGRITY,
        }

        medium = {
            BusinessArea.WORKFLOW,
            BusinessArea.STATE_TRANSITIONS,
            BusinessArea.USER_REGISTRATION,
            BusinessArea.BILLING,
            BusinessArea.REFUND,
            BusinessArea.DATA_RETENTION,
        }

        # Everything else is low severity
        severity = {}
        for area in BusinessArea:
            if area in critical:
                severity[area] = "critical"
            elif area in high:
                severity[area] = "high"
            elif area in medium:
                severity[area] = "medium"
            else:
                severity[area] = "low"

        return severity

    # =========================================================================
    # Main API
    # =========================================================================

    def check_completeness(
        self,
        rules: List[ExtractedRule],
        domain: str = "generic",
    ) -> CompletenessReport:
        """
        Check completeness of extracted rules for a domain.

        Args:
            rules: List of extracted business rules
            domain: Business domain (healthcare, finance, ecommerce, generic)

        Returns:
            CompletenessReport with coverage analysis
        """
        # Get expected areas for domain
        expected_areas = self._domain_requirements.get(
            domain.lower(),
            self._domain_requirements["generic"],
        )

        # Analyze coverage
        metrics = []
        covered_areas: Set[BusinessArea] = set()

        for area in BusinessArea:
            is_expected = area in expected_areas
            matching_rules = self._find_rules_for_area(rules, area)
            is_covered = len(matching_rules) > 0
            confidence = self._calculate_confidence(matching_rules, area)

            if is_covered:
                covered_areas.add(area)

            metrics.append(CoverageMetric(
                area=area,
                expected=is_expected,
                covered=is_covered,
                rule_count=len(matching_rules),
                confidence=confidence,
                sample_rules=[r.text[:100] for r in matching_rules[:3]],
            ))

        # Find gaps
        gaps = self.find_coverage_gaps(rules, domain)

        # Calculate coverage percentage (only for expected areas)
        expected_covered = covered_areas & expected_areas
        coverage_pct = (
            len(expected_covered) / len(expected_areas) * 100
            if expected_areas else 0
        )

        # Identify strengths
        strengths = self._identify_strengths(metrics)

        # Generate recommendations
        recommendations = self.get_recommendations(gaps)

        return CompletenessReport(
            domain=domain,
            total_rules=len(rules),
            coverage_percentage=round(coverage_pct, 1),
            metrics=metrics,
            gaps=gaps,
            strengths=strengths,
            recommendations=recommendations,
        )

    def find_coverage_gaps(
        self,
        rules: List[ExtractedRule],
        domain: str = "generic",
    ) -> List[CoverageGap]:
        """
        Find gaps in rule coverage.

        Args:
            rules: List of extracted rules
            domain: Business domain

        Returns:
            List of CoverageGap objects
        """
        expected_areas = self._domain_requirements.get(
            domain.lower(),
            self._domain_requirements["generic"],
        )

        gaps = []
        for area in expected_areas:
            matching_rules = self._find_rules_for_area(rules, area)

            if len(matching_rules) == 0:
                # Complete gap
                gaps.append(CoverageGap(
                    area=area,
                    severity=self._severity_levels[area],
                    description=f"No rules found covering {area.value}",
                    recommendations=self._get_area_recommendations(area),
                ))
            elif len(matching_rules) < 2:
                # Weak coverage
                if self._severity_levels[area] in ["critical", "high"]:
                    gaps.append(CoverageGap(
                        area=area,
                        severity="medium",  # Downgrade severity for weak coverage
                        description=f"Weak coverage for {area.value} (only {len(matching_rules)} rule)",
                        recommendations=[
                            f"Consider adding more specific rules for {area.value}",
                        ],
                    ))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda g: severity_order.get(g.severity, 4))

        return gaps

    def get_recommendations(self, gaps: List[CoverageGap]) -> List[str]:
        """
        Get prioritized recommendations based on gaps.

        Args:
            gaps: List of coverage gaps

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Group by severity
        critical_gaps = [g for g in gaps if g.severity == "critical"]
        high_gaps = [g for g in gaps if g.severity == "high"]
        medium_gaps = [g for g in gaps if g.severity == "medium"]

        if critical_gaps:
            areas = ", ".join(g.area.value for g in critical_gaps)
            recommendations.append(
                f"CRITICAL: Immediately add rules for {areas}"
            )

        if high_gaps:
            areas = ", ".join(g.area.value for g in high_gaps)
            recommendations.append(
                f"HIGH: Add rules for {areas} before production"
            )

        if medium_gaps:
            areas = ", ".join(g.area.value for g in medium_gaps[:5])
            recommendations.append(
                f"MEDIUM: Consider adding rules for {areas}"
            )

        # Add specific recommendations from gaps
        for gap in gaps[:5]:  # Top 5 most severe
            recommendations.extend(gap.recommendations)

        return recommendations

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _find_rules_for_area(
        self,
        rules: List[ExtractedRule],
        area: BusinessArea,
    ) -> List[ExtractedRule]:
        """Find rules that cover a specific business area."""
        keywords = self._area_keywords.get(area, [])
        matching = []

        for rule in rules:
            text_lower = rule.text.lower()
            tags_lower = [t.lower() for t in rule.tags]

            # Check keywords in text
            keyword_match = any(kw in text_lower for kw in keywords)

            # Check area name in tags
            tag_match = area.value in tags_lower

            # Check rule type matches area
            type_match = self._rule_type_matches_area(rule.rule_type, area)

            if keyword_match or tag_match or type_match:
                matching.append(rule)

        return matching

    def _rule_type_matches_area(self, rule_type: str, area: BusinessArea) -> bool:
        """Check if rule type indicates coverage of an area."""
        type_to_areas = {
            "validation": [BusinessArea.DATA_VALIDATION],
            "authorization": [BusinessArea.AUTHORIZATION, BusinessArea.AUTHENTICATION],
            "calculation": [BusinessArea.PRICING, BusinessArea.BILLING],
            "workflow": [BusinessArea.WORKFLOW, BusinessArea.STATE_TRANSITIONS],
            "constraint": [BusinessArea.DATA_INTEGRITY, BusinessArea.DATA_VALIDATION],
        }

        areas_for_type = type_to_areas.get(rule_type.lower(), [])
        return area in areas_for_type

    def _calculate_confidence(
        self,
        rules: List[ExtractedRule],
        area: BusinessArea,
    ) -> float:
        """Calculate confidence that an area is properly covered."""
        if not rules:
            return 0.0

        # Base confidence on number of rules
        base_confidence = min(len(rules) / 5, 1.0)  # Max at 5 rules

        # Adjust based on keyword density
        keywords = self._area_keywords.get(area, [])
        total_matches = 0
        for rule in rules:
            text_lower = rule.text.lower()
            matches = sum(1 for kw in keywords if kw in text_lower)
            total_matches += matches

        keyword_factor = min(total_matches / (len(rules) * 2), 1.0)

        return round(base_confidence * 0.6 + keyword_factor * 0.4, 2)

    def _identify_strengths(
        self,
        metrics: List[CoverageMetric],
    ) -> List[str]:
        """Identify areas with strong coverage."""
        strengths = []

        for metric in metrics:
            if metric.expected and metric.covered and metric.confidence >= 0.7:
                strengths.append(
                    f"Strong coverage for {metric.area.value} "
                    f"({metric.rule_count} rules, {metric.confidence:.0%} confidence)"
                )

        return strengths[:5]  # Top 5 strengths

    def _get_area_recommendations(self, area: BusinessArea) -> List[str]:
        """Get specific recommendations for a missing area."""
        recommendations = {
            BusinessArea.AUTHENTICATION: [
                "Add rules for password requirements (length, complexity)",
                "Add rules for session timeout and management",
                "Add rules for failed login attempt handling",
            ],
            BusinessArea.AUTHORIZATION: [
                "Define role-based access control rules",
                "Add rules for resource-level permissions",
                "Add rules for permission inheritance",
            ],
            BusinessArea.DATA_VALIDATION: [
                "Add input validation rules for all user inputs",
                "Define format rules for email, phone, dates",
                "Add business-specific validation rules",
            ],
            BusinessArea.DATA_PRIVACY: [
                "Add rules for handling personal data (PII)",
                "Define data anonymization requirements",
                "Add rules for data access logging",
            ],
            BusinessArea.SECURITY: [
                "Add rules for encryption requirements",
                "Define secure communication rules (HTTPS)",
                "Add rules for security headers",
            ],
            BusinessArea.PAYMENT: [
                "Add rules for payment validation",
                "Define rules for transaction limits",
                "Add rules for payment failure handling",
            ],
            BusinessArea.GDPR: [
                "Add rules for data subject rights",
                "Define consent management rules",
                "Add rules for data portability",
            ],
            BusinessArea.ERROR_HANDLING: [
                "Add rules for error message formatting",
                "Define error recovery procedures",
                "Add rules for error logging",
            ],
        }

        return recommendations.get(area, [
            f"Review existing code for {area.value} related logic",
            f"Document business requirements for {area.value}",
        ])

    # =========================================================================
    # Analysis Helpers
    # =========================================================================

    def get_coverage_summary(
        self,
        report: CompletenessReport,
    ) -> Dict:
        """Get a summary of coverage report."""
        gap_by_severity = defaultdict(int)
        for gap in report.gaps:
            gap_by_severity[gap.severity] += 1

        covered_areas = [
            m.area.value for m in report.metrics
            if m.expected and m.covered
        ]
        missing_areas = [
            m.area.value for m in report.metrics
            if m.expected and not m.covered
        ]

        return {
            "domain": report.domain,
            "total_rules": report.total_rules,
            "coverage_percentage": report.coverage_percentage,
            "gaps_by_severity": dict(gap_by_severity),
            "total_gaps": len(report.gaps),
            "covered_areas": covered_areas,
            "missing_areas": missing_areas,
            "top_recommendations": report.recommendations[:3],
        }


# Convenience functions
def check_rule_completeness(
    rules: List[ExtractedRule],
    domain: str = "generic",
) -> CompletenessReport:
    """Quick function to check rule completeness."""
    return RuleCompletenessChecker().check_completeness(rules, domain)


def get_coverage_gaps(
    rules: List[ExtractedRule],
    domain: str = "generic",
) -> List[CoverageGap]:
    """Quick function to find coverage gaps."""
    return RuleCompletenessChecker().find_coverage_gaps(rules, domain)
