"""
K4: Security Debt Calculator

Kwantificering van security risico's in financiële termen.

Formule:
    Security Debt = Σ (Vulnerability_Severity × Exposure_Factor × Asset_Value)

Components:
- Vulnerability Severity: CVSS-based scoring (0-10)
- Exposure Factor: Network exposure, auth level, data sensitivity (0-1)
- Asset Value: Business criticality, data classification, revenue impact (€)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
import json


class VulnerabilitySeverity(str, Enum):
    """CVSS-based severity levels."""
    CRITICAL = "critical"  # 9.0 - 10.0
    HIGH = "high"          # 7.0 - 8.9
    MEDIUM = "medium"      # 4.0 - 6.9
    LOW = "low"            # 0.1 - 3.9
    INFO = "info"          # 0.0


class NetworkExposure(str, Enum):
    """Network exposure levels."""
    INTERNET_FACING = "internet_facing"      # Directly accessible from internet
    DMZ = "dmz"                              # In DMZ, some protection
    INTERNAL_NETWORK = "internal_network"    # Internal network only
    ISOLATED = "isolated"                    # Air-gapped or fully isolated


class AuthenticationLevel(str, Enum):
    """Authentication protection levels."""
    NONE = "none"                            # No authentication required
    BASIC = "basic"                          # Basic auth or weak credentials
    STANDARD = "standard"                    # Standard auth (password, session)
    STRONG = "strong"                        # MFA or certificate-based
    ZERO_TRUST = "zero_trust"                # Zero trust architecture


class DataSensitivity(str, Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"                        # Public data
    INTERNAL = "internal"                    # Internal use only
    CONFIDENTIAL = "confidential"            # Confidential business data
    RESTRICTED = "restricted"                # Highly restricted (PII, financial)
    TOP_SECRET = "top_secret"                # Critical secrets (keys, credentials)


class BusinessCriticality(str, Enum):
    """Business criticality levels."""
    NON_ESSENTIAL = "non_essential"          # Nice to have
    SUPPORTING = "supporting"                # Supports business operations
    IMPORTANT = "important"                  # Important for business
    CRITICAL = "critical"                    # Business critical
    MISSION_CRITICAL = "mission_critical"    # Cannot operate without


class DataClassification(str, Enum):
    """Data classification for compliance."""
    UNCLASSIFIED = "unclassified"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"                              # Personal Identifiable Information
    PHI = "phi"                              # Protected Health Information
    PCI = "pci"                              # Payment Card Industry data
    FINANCIAL = "financial"                  # Financial/SOX data


# ============================================================================
# Exposure Factor Components
# ============================================================================

@dataclass
class ExposureFactor:
    """
    Exposure Factor (EF) calculation.

    EF = weighted combination of:
    - Network exposure (40%)
    - Authentication level (30%)
    - Data sensitivity (30%)

    Range: 0.0 - 1.0 (higher = more exposed)
    """
    network_exposure: NetworkExposure
    authentication_level: AuthenticationLevel
    data_sensitivity: DataSensitivity

    # Calculated score
    score: float = 0.0

    # Component scores
    network_score: float = 0.0
    auth_score: float = 0.0
    sensitivity_score: float = 0.0

    def __post_init__(self):
        self._calculate()

    def _calculate(self):
        """Calculate exposure factor score."""
        # Network exposure scoring (higher = more exposed)
        network_scores = {
            NetworkExposure.INTERNET_FACING: 1.0,
            NetworkExposure.DMZ: 0.7,
            NetworkExposure.INTERNAL_NETWORK: 0.4,
            NetworkExposure.ISOLATED: 0.1,
        }
        self.network_score = network_scores.get(self.network_exposure, 0.5)

        # Authentication level scoring (higher = less protected = more exposed)
        auth_scores = {
            AuthenticationLevel.NONE: 1.0,
            AuthenticationLevel.BASIC: 0.8,
            AuthenticationLevel.STANDARD: 0.5,
            AuthenticationLevel.STRONG: 0.2,
            AuthenticationLevel.ZERO_TRUST: 0.05,
        }
        self.auth_score = auth_scores.get(self.authentication_level, 0.5)

        # Data sensitivity scoring (higher = more sensitive = higher impact)
        sensitivity_scores = {
            DataSensitivity.PUBLIC: 0.1,
            DataSensitivity.INTERNAL: 0.3,
            DataSensitivity.CONFIDENTIAL: 0.6,
            DataSensitivity.RESTRICTED: 0.85,
            DataSensitivity.TOP_SECRET: 1.0,
        }
        self.sensitivity_score = sensitivity_scores.get(self.data_sensitivity, 0.5)

        # Weighted calculation
        self.score = (
            self.network_score * 0.4 +
            self.auth_score * 0.3 +
            self.sensitivity_score * 0.3
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "network_exposure": self.network_exposure.value,
            "authentication_level": self.authentication_level.value,
            "data_sensitivity": self.data_sensitivity.value,
            "score": round(self.score, 3),
            "components": {
                "network_score": round(self.network_score, 3),
                "auth_score": round(self.auth_score, 3),
                "sensitivity_score": round(self.sensitivity_score, 3)
            }
        }


# ============================================================================
# Asset Value Components
# ============================================================================

@dataclass
class AssetValue:
    """
    Asset Value (AV) calculation in monetary terms.

    AV = Base value adjusted by:
    - Business criticality multiplier
    - Data classification multiplier
    - Revenue impact factor
    - Compliance penalty risk

    Result in EUR (or configured currency)
    """
    asset_name: str
    base_value_eur: float  # Direct replacement/recovery cost

    business_criticality: BusinessCriticality
    data_classification: DataClassification

    # Revenue factors
    daily_revenue_impact_eur: float = 0.0  # Revenue lost per day of downtime
    estimated_downtime_days: float = 1.0   # Expected recovery time

    # Compliance factors
    gdpr_applicable: bool = False
    pci_applicable: bool = False
    sox_applicable: bool = False
    hipaa_applicable: bool = False

    # Calculated values
    total_value_eur: float = 0.0
    criticality_multiplier: float = 1.0
    classification_multiplier: float = 1.0
    compliance_penalty_risk_eur: float = 0.0

    def __post_init__(self):
        self._calculate()

    def _calculate(self):
        """Calculate total asset value."""
        # Business criticality multipliers
        criticality_multipliers = {
            BusinessCriticality.NON_ESSENTIAL: 0.5,
            BusinessCriticality.SUPPORTING: 1.0,
            BusinessCriticality.IMPORTANT: 1.5,
            BusinessCriticality.CRITICAL: 2.5,
            BusinessCriticality.MISSION_CRITICAL: 5.0,
        }
        self.criticality_multiplier = criticality_multipliers.get(
            self.business_criticality, 1.0
        )

        # Data classification multipliers
        classification_multipliers = {
            DataClassification.UNCLASSIFIED: 1.0,
            DataClassification.INTERNAL: 1.2,
            DataClassification.CONFIDENTIAL: 1.5,
            DataClassification.PII: 2.0,
            DataClassification.PHI: 2.5,
            DataClassification.PCI: 2.5,
            DataClassification.FINANCIAL: 2.0,
        }
        self.classification_multiplier = classification_multipliers.get(
            self.data_classification, 1.0
        )

        # Calculate compliance penalty risk
        self.compliance_penalty_risk_eur = self._calculate_compliance_risk()

        # Revenue impact
        revenue_impact = self.daily_revenue_impact_eur * self.estimated_downtime_days

        # Total value calculation
        self.total_value_eur = (
            (self.base_value_eur * self.criticality_multiplier * self.classification_multiplier) +
            revenue_impact +
            self.compliance_penalty_risk_eur
        )

    def _calculate_compliance_risk(self) -> float:
        """Calculate potential compliance penalty exposure."""
        penalty_risk = 0.0

        # GDPR: Up to €20M or 4% of annual revenue (using conservative estimate)
        if self.gdpr_applicable:
            penalty_risk += 500_000  # Conservative GDPR exposure

        # PCI-DSS: $5,000 - $100,000 per month until compliant
        if self.pci_applicable:
            penalty_risk += 250_000  # ~€230k

        # SOX: Up to $5M fine and 20 years imprisonment (using financial impact)
        if self.sox_applicable:
            penalty_risk += 1_000_000

        # HIPAA: $100 - $50,000 per violation, up to $1.5M per year
        if self.hipaa_applicable:
            penalty_risk += 500_000

        return penalty_risk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_name": self.asset_name,
            "base_value_eur": self.base_value_eur,
            "business_criticality": self.business_criticality.value,
            "data_classification": self.data_classification.value,
            "daily_revenue_impact_eur": self.daily_revenue_impact_eur,
            "estimated_downtime_days": self.estimated_downtime_days,
            "compliance": {
                "gdpr": self.gdpr_applicable,
                "pci": self.pci_applicable,
                "sox": self.sox_applicable,
                "hipaa": self.hipaa_applicable,
            },
            "calculated": {
                "criticality_multiplier": self.criticality_multiplier,
                "classification_multiplier": self.classification_multiplier,
                "compliance_penalty_risk_eur": self.compliance_penalty_risk_eur,
                "total_value_eur": round(self.total_value_eur, 2)
            }
        }


# ============================================================================
# Vulnerability & Security Debt
# ============================================================================

@dataclass
class SecurityVulnerability:
    """A security vulnerability with severity scoring."""
    id: str
    name: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: float  # 0.0 - 10.0
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    affected_component: str = ""
    remediation_effort_hours: float = 0.0
    remediation_cost_eur: float = 0.0

    def get_severity_multiplier(self) -> float:
        """Get severity as a multiplier (0-1 scale)."""
        return self.cvss_score / 10.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "cvss_score": self.cvss_score,
            "cwe_id": self.cwe_id,
            "cve_id": self.cve_id,
            "affected_component": self.affected_component,
            "remediation_effort_hours": self.remediation_effort_hours,
            "remediation_cost_eur": self.remediation_cost_eur,
            "severity_multiplier": self.get_severity_multiplier()
        }


@dataclass
class SecurityDebtItem:
    """A single security debt item with calculated monetary value."""
    vulnerability: SecurityVulnerability
    exposure_factor: ExposureFactor
    asset_value: AssetValue

    # Calculated debt
    debt_value_eur: float = 0.0
    annual_loss_expectancy_eur: float = 0.0

    def __post_init__(self):
        self._calculate()

    def _calculate(self):
        """Calculate security debt value."""
        # Security Debt = Severity × Exposure Factor × Asset Value
        self.debt_value_eur = (
            self.vulnerability.get_severity_multiplier() *
            self.exposure_factor.score *
            self.asset_value.total_value_eur
        )

        # Annual Loss Expectancy (simplified: assume 10% annual probability)
        # In reality this would be based on threat intelligence
        annual_rate_of_occurrence = 0.1 + (self.exposure_factor.score * 0.2)
        self.annual_loss_expectancy_eur = self.debt_value_eur * annual_rate_of_occurrence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vulnerability": self.vulnerability.to_dict(),
            "exposure_factor": self.exposure_factor.to_dict(),
            "asset_value": self.asset_value.to_dict(),
            "debt_value_eur": round(self.debt_value_eur, 2),
            "annual_loss_expectancy_eur": round(self.annual_loss_expectancy_eur, 2)
        }


@dataclass
class SecurityDebtReport:
    """Complete security debt assessment report."""
    id: UUID
    system_name: str
    assessment_date: datetime

    # Debt items
    debt_items: List[SecurityDebtItem]

    # Aggregated values
    total_debt_eur: float = 0.0
    total_ale_eur: float = 0.0  # Annual Loss Expectancy
    total_remediation_cost_eur: float = 0.0

    # Risk breakdown
    critical_debt_eur: float = 0.0
    high_debt_eur: float = 0.0
    medium_debt_eur: float = 0.0
    low_debt_eur: float = 0.0

    def __post_init__(self):
        self._aggregate()

    def _aggregate(self):
        """Aggregate debt values."""
        self.total_debt_eur = sum(item.debt_value_eur for item in self.debt_items)
        self.total_ale_eur = sum(item.annual_loss_expectancy_eur for item in self.debt_items)
        self.total_remediation_cost_eur = sum(
            item.vulnerability.remediation_cost_eur for item in self.debt_items
        )

        # Breakdown by severity
        for item in self.debt_items:
            if item.vulnerability.severity == VulnerabilitySeverity.CRITICAL:
                self.critical_debt_eur += item.debt_value_eur
            elif item.vulnerability.severity == VulnerabilitySeverity.HIGH:
                self.high_debt_eur += item.debt_value_eur
            elif item.vulnerability.severity == VulnerabilitySeverity.MEDIUM:
                self.medium_debt_eur += item.debt_value_eur
            else:
                self.low_debt_eur += item.debt_value_eur

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "system_name": self.system_name,
            "assessment_date": self.assessment_date.isoformat(),
            "summary": {
                "total_debt_eur": round(self.total_debt_eur, 2),
                "total_ale_eur": round(self.total_ale_eur, 2),
                "total_remediation_cost_eur": round(self.total_remediation_cost_eur, 2),
                "roi_on_remediation": round(
                    (self.total_ale_eur - self.total_remediation_cost_eur) /
                    max(self.total_remediation_cost_eur, 1) * 100, 1
                )
            },
            "breakdown_by_severity": {
                "critical": round(self.critical_debt_eur, 2),
                "high": round(self.high_debt_eur, 2),
                "medium": round(self.medium_debt_eur, 2),
                "low": round(self.low_debt_eur, 2)
            },
            "debt_items": [item.to_dict() for item in self.debt_items],
            "item_count": len(self.debt_items)
        }


# ============================================================================
# Service
# ============================================================================

class SecurityDebtCalculatorService:
    """
    Service voor het berekenen van security debt in financiële termen.

    Gebruik:
    1. Definieer assets met hun waarde en classificatie
    2. Definieer exposure factors per asset/component
    3. Voeg vulnerabilities toe
    4. Bereken totale security debt en ALE
    5. Genereer rapport voor business case
    """

    def __init__(self):
        self._reports: Dict[UUID, SecurityDebtReport] = {}
        self._assets: Dict[str, AssetValue] = {}
        self._exposure_factors: Dict[str, ExposureFactor] = {}

    # =========================================================================
    # Asset Management
    # =========================================================================

    def register_asset(
        self,
        asset_name: str,
        base_value_eur: float,
        business_criticality: BusinessCriticality,
        data_classification: DataClassification,
        daily_revenue_impact_eur: float = 0.0,
        estimated_downtime_days: float = 1.0,
        gdpr_applicable: bool = False,
        pci_applicable: bool = False,
        sox_applicable: bool = False,
        hipaa_applicable: bool = False
    ) -> AssetValue:
        """Register an asset with its value characteristics."""
        asset = AssetValue(
            asset_name=asset_name,
            base_value_eur=base_value_eur,
            business_criticality=business_criticality,
            data_classification=data_classification,
            daily_revenue_impact_eur=daily_revenue_impact_eur,
            estimated_downtime_days=estimated_downtime_days,
            gdpr_applicable=gdpr_applicable,
            pci_applicable=pci_applicable,
            sox_applicable=sox_applicable,
            hipaa_applicable=hipaa_applicable
        )
        self._assets[asset_name] = asset
        return asset

    def get_asset(self, asset_name: str) -> Optional[AssetValue]:
        """Get a registered asset."""
        return self._assets.get(asset_name)

    def list_assets(self) -> List[AssetValue]:
        """List all registered assets."""
        return list(self._assets.values())

    # =========================================================================
    # Exposure Factor Management
    # =========================================================================

    def set_exposure_factor(
        self,
        component_name: str,
        network_exposure: NetworkExposure,
        authentication_level: AuthenticationLevel,
        data_sensitivity: DataSensitivity
    ) -> ExposureFactor:
        """Set exposure factor for a component."""
        ef = ExposureFactor(
            network_exposure=network_exposure,
            authentication_level=authentication_level,
            data_sensitivity=data_sensitivity
        )
        self._exposure_factors[component_name] = ef
        return ef

    def get_exposure_factor(self, component_name: str) -> Optional[ExposureFactor]:
        """Get exposure factor for a component."""
        return self._exposure_factors.get(component_name)

    # =========================================================================
    # Debt Calculation
    # =========================================================================

    def calculate_debt_item(
        self,
        vulnerability: SecurityVulnerability,
        asset_name: str,
        component_name: Optional[str] = None
    ) -> SecurityDebtItem:
        """Calculate security debt for a single vulnerability."""
        asset = self._assets.get(asset_name)
        if not asset:
            raise ValueError(f"Asset not found: {asset_name}")

        # Use component-specific exposure factor or create default
        ef = self._exposure_factors.get(component_name or asset_name)
        if not ef:
            # Default exposure factor
            ef = ExposureFactor(
                network_exposure=NetworkExposure.INTERNAL_NETWORK,
                authentication_level=AuthenticationLevel.STANDARD,
                data_sensitivity=DataSensitivity.CONFIDENTIAL
            )

        return SecurityDebtItem(
            vulnerability=vulnerability,
            exposure_factor=ef,
            asset_value=asset
        )

    def calculate_report(
        self,
        system_name: str,
        vulnerabilities: List[SecurityVulnerability],
        asset_mapping: Dict[str, str]  # vulnerability_id -> asset_name
    ) -> SecurityDebtReport:
        """Calculate complete security debt report."""
        debt_items = []

        for vuln in vulnerabilities:
            asset_name = asset_mapping.get(vuln.id)
            if asset_name and asset_name in self._assets:
                item = self.calculate_debt_item(
                    vulnerability=vuln,
                    asset_name=asset_name,
                    component_name=vuln.affected_component or None
                )
                debt_items.append(item)

        report = SecurityDebtReport(
            id=uuid4(),
            system_name=system_name,
            assessment_date=datetime.now(),
            debt_items=debt_items
        )

        self._reports[report.id] = report
        return report

    def get_report(self, report_id: Union[UUID, str]) -> Optional[SecurityDebtReport]:
        """Get a report by ID."""
        if isinstance(report_id, str):
            report_id = UUID(report_id)
        return self._reports.get(report_id)

    # =========================================================================
    # Quick Calculation Helpers
    # =========================================================================

    def quick_calculate(
        self,
        cvss_score: float,
        network_exposure: NetworkExposure,
        auth_level: AuthenticationLevel,
        data_sensitivity: DataSensitivity,
        asset_value_eur: float,
        business_criticality: BusinessCriticality = BusinessCriticality.IMPORTANT
    ) -> Dict[str, float]:
        """
        Quick security debt calculation without full registration.

        Returns dict with debt_value_eur and annual_loss_expectancy_eur.
        """
        ef = ExposureFactor(
            network_exposure=network_exposure,
            authentication_level=auth_level,
            data_sensitivity=data_sensitivity
        )

        av = AssetValue(
            asset_name="quick_calc",
            base_value_eur=asset_value_eur,
            business_criticality=business_criticality,
            data_classification=DataClassification.CONFIDENTIAL
        )

        severity_multiplier = cvss_score / 10.0
        debt_value = severity_multiplier * ef.score * av.total_value_eur

        # Simplified ALE
        aro = 0.1 + (ef.score * 0.2)
        ale = debt_value * aro

        return {
            "debt_value_eur": round(debt_value, 2),
            "annual_loss_expectancy_eur": round(ale, 2),
            "exposure_factor": round(ef.score, 3),
            "asset_value_adjusted_eur": round(av.total_value_eur, 2)
        }

    # =========================================================================
    # Prioritization
    # =========================================================================

    def prioritize_remediation(
        self,
        report_id: Union[UUID, str]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize vulnerabilities for remediation based on ROI.

        ROI = (Debt Value - Remediation Cost) / Remediation Cost
        """
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")

        prioritized = []
        for item in report.debt_items:
            remediation_cost = item.vulnerability.remediation_cost_eur
            if remediation_cost > 0:
                roi = (item.debt_value_eur - remediation_cost) / remediation_cost
            else:
                roi = float('inf')  # Free remediation = infinite ROI

            prioritized.append({
                "vulnerability_id": item.vulnerability.id,
                "vulnerability_name": item.vulnerability.name,
                "severity": item.vulnerability.severity.value,
                "debt_value_eur": round(item.debt_value_eur, 2),
                "remediation_cost_eur": round(remediation_cost, 2),
                "roi_percentage": round(roi * 100, 1) if roi != float('inf') else "∞",
                "effort_hours": item.vulnerability.remediation_effort_hours,
                "affected_asset": item.asset_value.asset_name
            })

        # Sort by ROI descending (highest ROI first)
        return sorted(
            prioritized,
            key=lambda x: x["roi_percentage"] if x["roi_percentage"] != "∞" else float('inf'),
            reverse=True
        )

    # =========================================================================
    # Export
    # =========================================================================

    def export_report(
        self,
        report_id: Union[UUID, str],
        format: str = "json"
    ) -> str:
        """Export report to JSON or markdown."""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")

        if format == "json":
            return json.dumps(report.to_dict(), indent=2)
        elif format == "markdown":
            return self._export_markdown(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_markdown(self, report: SecurityDebtReport) -> str:
        """Export report as markdown."""
        lines = [
            f"# Security Debt Assessment: {report.system_name}",
            f"",
            f"**Assessment Date**: {report.assessment_date.strftime('%Y-%m-%d')}",
            f"**Report ID**: {report.id}",
            f"",
            "## Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| **Total Security Debt** | €{report.total_debt_eur:,.2f} |",
            f"| **Annual Loss Expectancy** | €{report.total_ale_eur:,.2f} |",
            f"| **Total Remediation Cost** | €{report.total_remediation_cost_eur:,.2f} |",
            f"| **Vulnerabilities Assessed** | {len(report.debt_items)} |",
            f"",
            "## Debt by Severity",
            f"",
            f"| Severity | Debt Value |",
            f"|----------|------------|",
            f"| Critical | €{report.critical_debt_eur:,.2f} |",
            f"| High | €{report.high_debt_eur:,.2f} |",
            f"| Medium | €{report.medium_debt_eur:,.2f} |",
            f"| Low | €{report.low_debt_eur:,.2f} |",
            f"",
            "## Top 10 Debt Items",
            f"",
            "| Vulnerability | Severity | Asset | Debt Value |",
            "|---------------|----------|-------|------------|"
        ]

        # Sort by debt value descending
        sorted_items = sorted(
            report.debt_items,
            key=lambda x: x.debt_value_eur,
            reverse=True
        )[:10]

        for item in sorted_items:
            lines.append(
                f"| {item.vulnerability.name} | {item.vulnerability.severity.value} | "
                f"{item.asset_value.asset_name} | €{item.debt_value_eur:,.2f} |"
            )

        lines.extend([
            f"",
            "## Recommendations",
            f"",
            "1. **Immediate Action**: Address {report.critical_debt_eur:,.0f} EUR in critical vulnerabilities",
            f"2. **Quick Wins**: Focus on high-ROI remediations first",
            f"3. **Budget Planning**: Allocate €{report.total_remediation_cost_eur:,.0f} for full remediation",
            f"",
            "---",
            f"*Report generated by Security Debt Calculator Service*"
        ])

        return "\n".join(lines)
