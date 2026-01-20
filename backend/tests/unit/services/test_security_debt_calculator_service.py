"""
Unit tests for SecurityDebtCalculatorService (K4 - Fase 24)

Tests security debt calculation, exposure factors, asset valuation,
and remediation prioritization.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from app.services.security_debt_calculator_service import (
    SecurityDebtCalculatorService,
    VulnerabilitySeverity,
    NetworkExposure,
    AuthenticationLevel,
    DataSensitivity,
    BusinessCriticality,
    DataClassification,
    ExposureFactor,
    AssetValue,
    SecurityVulnerability,
    SecurityDebtItem,
    SecurityDebtReport,
)


# ============================================================================
# ExposureFactor Tests
# ============================================================================

class TestExposureFactor:
    """Tests for ExposureFactor dataclass."""

    def test_exposure_factor_calculation(self):
        """Test exposure factor score calculation."""
        ef = ExposureFactor(
            network_exposure=NetworkExposure.INTERNET_FACING,
            authentication_level=AuthenticationLevel.NONE,
            data_sensitivity=DataSensitivity.TOP_SECRET
        )
        # Score = 1.0 * 0.4 + 1.0 * 0.3 + 1.0 * 0.3 = 1.0
        assert ef.score == 1.0
        assert ef.network_score == 1.0
        assert ef.auth_score == 1.0
        assert ef.sensitivity_score == 1.0

    def test_exposure_factor_low_risk(self):
        """Test low risk exposure factor."""
        ef = ExposureFactor(
            network_exposure=NetworkExposure.ISOLATED,
            authentication_level=AuthenticationLevel.ZERO_TRUST,
            data_sensitivity=DataSensitivity.PUBLIC
        )
        # Score = 0.1 * 0.4 + 0.05 * 0.3 + 0.1 * 0.3 = 0.04 + 0.015 + 0.03 = 0.085
        assert ef.score == pytest.approx(0.085, rel=0.01)

    def test_exposure_factor_medium_risk(self):
        """Test medium risk exposure factor."""
        ef = ExposureFactor(
            network_exposure=NetworkExposure.INTERNAL_NETWORK,
            authentication_level=AuthenticationLevel.STANDARD,
            data_sensitivity=DataSensitivity.CONFIDENTIAL
        )
        # Score = 0.4 * 0.4 + 0.5 * 0.3 + 0.6 * 0.3 = 0.16 + 0.15 + 0.18 = 0.49
        assert ef.score == pytest.approx(0.49, rel=0.01)

    def test_exposure_factor_to_dict(self):
        """Test exposure factor serialization."""
        ef = ExposureFactor(
            network_exposure=NetworkExposure.DMZ,
            authentication_level=AuthenticationLevel.BASIC,
            data_sensitivity=DataSensitivity.RESTRICTED
        )
        data = ef.to_dict()
        assert data["network_exposure"] == "dmz"
        assert data["authentication_level"] == "basic"
        assert data["data_sensitivity"] == "restricted"
        assert "score" in data
        assert "components" in data


# ============================================================================
# AssetValue Tests
# ============================================================================

class TestAssetValue:
    """Tests for AssetValue dataclass."""

    def test_asset_value_basic(self):
        """Test basic asset value calculation."""
        av = AssetValue(
            asset_name="Test Asset",
            base_value_eur=100_000,
            business_criticality=BusinessCriticality.IMPORTANT,
            data_classification=DataClassification.CONFIDENTIAL
        )
        # Base * criticality(1.5) * classification(1.5) = 100000 * 1.5 * 1.5 = 225000
        assert av.criticality_multiplier == 1.5
        assert av.classification_multiplier == 1.5
        assert av.total_value_eur == pytest.approx(225_000, rel=0.01)

    def test_asset_value_mission_critical(self):
        """Test mission critical asset value."""
        av = AssetValue(
            asset_name="Core Database",
            base_value_eur=500_000,
            business_criticality=BusinessCriticality.MISSION_CRITICAL,
            data_classification=DataClassification.PII
        )
        # Base * 5.0 * 2.0 = 5_000_000
        assert av.criticality_multiplier == 5.0
        assert av.classification_multiplier == 2.0
        assert av.total_value_eur == pytest.approx(5_000_000, rel=0.01)

    def test_asset_value_with_revenue_impact(self):
        """Test asset value with revenue impact."""
        av = AssetValue(
            asset_name="E-commerce Platform",
            base_value_eur=200_000,
            business_criticality=BusinessCriticality.CRITICAL,
            data_classification=DataClassification.FINANCIAL,
            daily_revenue_impact_eur=50_000,
            estimated_downtime_days=3.0
        )
        # Base * 2.5 * 2.0 + revenue_impact = 1_000_000 + 150_000 = 1_150_000
        revenue_impact = 50_000 * 3.0
        base_adjusted = 200_000 * 2.5 * 2.0
        assert av.total_value_eur == pytest.approx(base_adjusted + revenue_impact, rel=0.01)

    def test_asset_value_with_gdpr_compliance(self):
        """Test asset value with GDPR compliance penalty risk."""
        av = AssetValue(
            asset_name="Customer Database",
            base_value_eur=100_000,
            business_criticality=BusinessCriticality.IMPORTANT,
            data_classification=DataClassification.PII,
            gdpr_applicable=True
        )
        # Should include €500,000 GDPR penalty risk
        assert av.compliance_penalty_risk_eur == 500_000
        assert av.total_value_eur > 100_000 + 500_000

    def test_asset_value_with_multiple_compliance(self):
        """Test asset value with multiple compliance requirements."""
        av = AssetValue(
            asset_name="Healthcare Payment System",
            base_value_eur=300_000,
            business_criticality=BusinessCriticality.MISSION_CRITICAL,
            data_classification=DataClassification.PHI,
            gdpr_applicable=True,
            pci_applicable=True,
            hipaa_applicable=True
        )
        # GDPR: 500k + PCI: 250k + HIPAA: 500k = 1.25M
        assert av.compliance_penalty_risk_eur == 1_250_000

    def test_asset_value_to_dict(self):
        """Test asset value serialization."""
        av = AssetValue(
            asset_name="Test Asset",
            base_value_eur=100_000,
            business_criticality=BusinessCriticality.SUPPORTING,
            data_classification=DataClassification.INTERNAL
        )
        data = av.to_dict()
        assert data["asset_name"] == "Test Asset"
        assert data["base_value_eur"] == 100_000
        assert data["business_criticality"] == "supporting"
        assert data["calculated"]["total_value_eur"] > 0


# ============================================================================
# SecurityVulnerability Tests
# ============================================================================

class TestSecurityVulnerability:
    """Tests for SecurityVulnerability dataclass."""

    def test_severity_multiplier_critical(self):
        """Test severity multiplier for critical vulnerability."""
        vuln = SecurityVulnerability(
            id="VULN-001",
            name="SQL Injection",
            description="Critical SQL injection vulnerability",
            severity=VulnerabilitySeverity.CRITICAL,
            cvss_score=9.8
        )
        assert vuln.get_severity_multiplier() == pytest.approx(0.98, rel=0.01)

    def test_severity_multiplier_low(self):
        """Test severity multiplier for low vulnerability."""
        vuln = SecurityVulnerability(
            id="VULN-002",
            name="Information Disclosure",
            description="Minor information disclosure",
            severity=VulnerabilitySeverity.LOW,
            cvss_score=2.5
        )
        assert vuln.get_severity_multiplier() == pytest.approx(0.25, rel=0.01)

    def test_vulnerability_to_dict(self):
        """Test vulnerability serialization."""
        vuln = SecurityVulnerability(
            id="VULN-003",
            name="XSS",
            description="Cross-site scripting",
            severity=VulnerabilitySeverity.HIGH,
            cvss_score=7.5,
            cwe_id="CWE-79",
            cve_id="CVE-2024-1234",
            affected_component="web_frontend",
            remediation_effort_hours=8.0,
            remediation_cost_eur=1_000
        )
        data = vuln.to_dict()
        assert data["id"] == "VULN-003"
        assert data["severity"] == "high"
        assert data["cvss_score"] == 7.5
        assert data["cwe_id"] == "CWE-79"
        assert data["cve_id"] == "CVE-2024-1234"


# ============================================================================
# SecurityDebtItem Tests
# ============================================================================

class TestSecurityDebtItem:
    """Tests for SecurityDebtItem dataclass."""

    def test_debt_item_calculation(self):
        """Test security debt item calculation."""
        vuln = SecurityVulnerability(
            id="VULN-001",
            name="Test Vuln",
            description="Test",
            severity=VulnerabilitySeverity.HIGH,
            cvss_score=8.0
        )
        ef = ExposureFactor(
            network_exposure=NetworkExposure.INTERNET_FACING,
            authentication_level=AuthenticationLevel.NONE,
            data_sensitivity=DataSensitivity.RESTRICTED
        )
        av = AssetValue(
            asset_name="Test Asset",
            base_value_eur=100_000,
            business_criticality=BusinessCriticality.CRITICAL,
            data_classification=DataClassification.PII
        )

        item = SecurityDebtItem(
            vulnerability=vuln,
            exposure_factor=ef,
            asset_value=av
        )

        # Debt = severity_multiplier * exposure_factor * asset_value
        expected_debt = (8.0 / 10.0) * ef.score * av.total_value_eur
        assert item.debt_value_eur == pytest.approx(expected_debt, rel=0.01)

    def test_debt_item_annual_loss_expectancy(self):
        """Test annual loss expectancy calculation."""
        vuln = SecurityVulnerability(
            id="VULN-001",
            name="Test",
            description="Test",
            severity=VulnerabilitySeverity.CRITICAL,
            cvss_score=10.0
        )
        ef = ExposureFactor(
            network_exposure=NetworkExposure.INTERNET_FACING,
            authentication_level=AuthenticationLevel.NONE,
            data_sensitivity=DataSensitivity.TOP_SECRET
        )
        av = AssetValue(
            asset_name="Test",
            base_value_eur=1_000_000,
            business_criticality=BusinessCriticality.MISSION_CRITICAL,
            data_classification=DataClassification.FINANCIAL
        )

        item = SecurityDebtItem(
            vulnerability=vuln,
            exposure_factor=ef,
            asset_value=av
        )

        # ALE = debt_value * (0.1 + exposure_factor * 0.2)
        expected_aro = 0.1 + (ef.score * 0.2)
        expected_ale = item.debt_value_eur * expected_aro
        assert item.annual_loss_expectancy_eur == pytest.approx(expected_ale, rel=0.01)


# ============================================================================
# SecurityDebtReport Tests
# ============================================================================

class TestSecurityDebtReport:
    """Tests for SecurityDebtReport dataclass."""

    def test_report_aggregation(self):
        """Test report aggregation of debt items."""
        vuln1 = SecurityVulnerability(
            id="V1", name="Critical", description="",
            severity=VulnerabilitySeverity.CRITICAL, cvss_score=9.5
        )
        vuln2 = SecurityVulnerability(
            id="V2", name="High", description="",
            severity=VulnerabilitySeverity.HIGH, cvss_score=7.5
        )
        vuln3 = SecurityVulnerability(
            id="V3", name="Medium", description="",
            severity=VulnerabilitySeverity.MEDIUM, cvss_score=5.0,
            remediation_cost_eur=2_000
        )

        ef = ExposureFactor(
            network_exposure=NetworkExposure.INTERNAL_NETWORK,
            authentication_level=AuthenticationLevel.STANDARD,
            data_sensitivity=DataSensitivity.CONFIDENTIAL
        )
        av = AssetValue(
            asset_name="Test", base_value_eur=100_000,
            business_criticality=BusinessCriticality.IMPORTANT,
            data_classification=DataClassification.CONFIDENTIAL
        )

        items = [
            SecurityDebtItem(vulnerability=vuln1, exposure_factor=ef, asset_value=av),
            SecurityDebtItem(vulnerability=vuln2, exposure_factor=ef, asset_value=av),
            SecurityDebtItem(vulnerability=vuln3, exposure_factor=ef, asset_value=av),
        ]

        report = SecurityDebtReport(
            id=uuid4(),
            system_name="Test System",
            assessment_date=datetime.now(),
            debt_items=items
        )

        # Total debt should be sum of all items
        expected_total = sum(item.debt_value_eur for item in items)
        assert report.total_debt_eur == pytest.approx(expected_total, rel=0.01)

        # Check severity breakdown
        assert report.critical_debt_eur == pytest.approx(items[0].debt_value_eur, rel=0.01)
        assert report.high_debt_eur == pytest.approx(items[1].debt_value_eur, rel=0.01)
        assert report.medium_debt_eur == pytest.approx(items[2].debt_value_eur, rel=0.01)

    def test_report_to_dict(self):
        """Test report serialization."""
        report = SecurityDebtReport(
            id=uuid4(),
            system_name="Production System",
            assessment_date=datetime.now(),
            debt_items=[]
        )
        data = report.to_dict()
        assert data["system_name"] == "Production System"
        assert "summary" in data
        assert "breakdown_by_severity" in data


# ============================================================================
# SecurityDebtCalculatorService Tests
# ============================================================================

class TestSecurityDebtCalculatorService:
    """Tests for SecurityDebtCalculatorService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return SecurityDebtCalculatorService()

    def test_register_asset(self, service):
        """Test asset registration."""
        asset = service.register_asset(
            asset_name="API Server",
            base_value_eur=250_000,
            business_criticality=BusinessCriticality.CRITICAL,
            data_classification=DataClassification.CONFIDENTIAL
        )

        assert asset.asset_name == "API Server"
        assert service.get_asset("API Server") == asset

    def test_register_asset_with_compliance(self, service):
        """Test asset registration with compliance flags."""
        asset = service.register_asset(
            asset_name="Payment System",
            base_value_eur=500_000,
            business_criticality=BusinessCriticality.MISSION_CRITICAL,
            data_classification=DataClassification.PCI,
            pci_applicable=True,
            gdpr_applicable=True
        )

        assert asset.pci_applicable
        assert asset.gdpr_applicable
        assert asset.compliance_penalty_risk_eur >= 750_000  # GDPR + PCI

    def test_list_assets(self, service):
        """Test listing registered assets."""
        service.register_asset(
            "Asset1", 100_000,
            BusinessCriticality.SUPPORTING,
            DataClassification.INTERNAL
        )
        service.register_asset(
            "Asset2", 200_000,
            BusinessCriticality.IMPORTANT,
            DataClassification.CONFIDENTIAL
        )

        assets = service.list_assets()
        assert len(assets) == 2

    def test_set_exposure_factor(self, service):
        """Test setting exposure factor."""
        ef = service.set_exposure_factor(
            component_name="web_api",
            network_exposure=NetworkExposure.INTERNET_FACING,
            authentication_level=AuthenticationLevel.STRONG,
            data_sensitivity=DataSensitivity.RESTRICTED
        )

        assert service.get_exposure_factor("web_api") == ef

    def test_calculate_debt_item(self, service):
        """Test debt item calculation."""
        service.register_asset(
            "Database", 1_000_000,
            BusinessCriticality.CRITICAL,
            DataClassification.PII
        )
        service.set_exposure_factor(
            "database_component",
            NetworkExposure.INTERNAL_NETWORK,
            AuthenticationLevel.STRONG,
            DataSensitivity.RESTRICTED
        )

        vuln = SecurityVulnerability(
            id="SQL-001",
            name="SQL Injection",
            description="SQL injection in user input",
            severity=VulnerabilitySeverity.CRITICAL,
            cvss_score=9.8,
            cwe_id="CWE-89"
        )

        item = service.calculate_debt_item(
            vulnerability=vuln,
            asset_name="Database",
            component_name="database_component"
        )

        assert item.debt_value_eur > 0
        assert item.vulnerability == vuln

    def test_calculate_debt_item_missing_asset(self, service):
        """Test debt calculation with missing asset."""
        vuln = SecurityVulnerability(
            id="V1", name="Test", description="",
            severity=VulnerabilitySeverity.LOW, cvss_score=2.0
        )

        with pytest.raises(ValueError, match="Asset not found"):
            service.calculate_debt_item(vuln, "NonExistentAsset")

    def test_calculate_debt_item_default_exposure(self, service):
        """Test debt calculation with default exposure factor."""
        service.register_asset(
            "Server", 100_000,
            BusinessCriticality.IMPORTANT,
            DataClassification.CONFIDENTIAL
        )

        vuln = SecurityVulnerability(
            id="V1", name="Test", description="",
            severity=VulnerabilitySeverity.MEDIUM, cvss_score=5.0
        )

        # Should use default exposure factor
        item = service.calculate_debt_item(vuln, "Server")
        assert item.debt_value_eur > 0

    def test_calculate_report(self, service):
        """Test complete report calculation."""
        service.register_asset(
            "WebApp", 500_000,
            BusinessCriticality.CRITICAL,
            DataClassification.PII,
            gdpr_applicable=True
        )
        service.set_exposure_factor(
            "frontend",
            NetworkExposure.INTERNET_FACING,
            AuthenticationLevel.STANDARD,
            DataSensitivity.RESTRICTED
        )

        vulns = [
            SecurityVulnerability(
                id="XSS-001", name="XSS", description="XSS in search",
                severity=VulnerabilitySeverity.HIGH, cvss_score=7.5,
                affected_component="frontend",
                remediation_cost_eur=5_000
            ),
            SecurityVulnerability(
                id="CSRF-001", name="CSRF", description="Missing CSRF token",
                severity=VulnerabilitySeverity.MEDIUM, cvss_score=5.5,
                affected_component="frontend",
                remediation_cost_eur=2_000
            ),
        ]

        asset_mapping = {
            "XSS-001": "WebApp",
            "CSRF-001": "WebApp"
        }

        report = service.calculate_report(
            system_name="Production Web App",
            vulnerabilities=vulns,
            asset_mapping=asset_mapping
        )

        assert report.system_name == "Production Web App"
        assert len(report.debt_items) == 2
        assert report.total_debt_eur > 0
        assert report.total_remediation_cost_eur == 7_000

    def test_get_report(self, service):
        """Test retrieving a report by ID."""
        service.register_asset("Test", 100_000, BusinessCriticality.SUPPORTING, DataClassification.INTERNAL)
        report = service.calculate_report("Test", [], {})

        retrieved = service.get_report(report.id)
        assert retrieved == report

        # Test with string ID
        retrieved_str = service.get_report(str(report.id))
        assert retrieved_str == report

    def test_quick_calculate(self, service):
        """Test quick debt calculation."""
        result = service.quick_calculate(
            cvss_score=8.5,
            network_exposure=NetworkExposure.INTERNET_FACING,
            auth_level=AuthenticationLevel.BASIC,
            data_sensitivity=DataSensitivity.RESTRICTED,
            asset_value_eur=100_000,
            business_criticality=BusinessCriticality.CRITICAL
        )

        assert "debt_value_eur" in result
        assert "annual_loss_expectancy_eur" in result
        assert "exposure_factor" in result
        assert result["debt_value_eur"] > 0

    def test_prioritize_remediation(self, service):
        """Test remediation prioritization."""
        service.register_asset(
            "System", 1_000_000,
            BusinessCriticality.CRITICAL,
            DataClassification.PII
        )

        vulns = [
            SecurityVulnerability(
                id="V1", name="High Impact Low Cost",
                description="", severity=VulnerabilitySeverity.CRITICAL,
                cvss_score=9.5, remediation_cost_eur=1_000,
                remediation_effort_hours=2
            ),
            SecurityVulnerability(
                id="V2", name="Low Impact High Cost",
                description="", severity=VulnerabilitySeverity.LOW,
                cvss_score=2.0, remediation_cost_eur=50_000,
                remediation_effort_hours=100
            ),
            SecurityVulnerability(
                id="V3", name="Free Fix",
                description="", severity=VulnerabilitySeverity.MEDIUM,
                cvss_score=5.0, remediation_cost_eur=0,
                remediation_effort_hours=1
            ),
        ]

        report = service.calculate_report(
            "Test", vulns,
            {"V1": "System", "V2": "System", "V3": "System"}
        )

        prioritized = service.prioritize_remediation(report.id)

        # Free fix should be first (infinite ROI)
        assert prioritized[0]["vulnerability_id"] == "V3"
        assert prioritized[0]["roi_percentage"] == "∞"

        # High impact low cost should be second
        assert prioritized[1]["vulnerability_id"] == "V1"

    def test_export_report_json(self, service):
        """Test report export to JSON."""
        service.register_asset("Test", 100_000, BusinessCriticality.SUPPORTING, DataClassification.INTERNAL)
        report = service.calculate_report("Test System", [], {})

        json_export = service.export_report(report.id, format="json")
        assert "Test System" in json_export
        assert "total_debt_eur" in json_export

    def test_export_report_markdown(self, service):
        """Test report export to Markdown."""
        service.register_asset("WebApp", 500_000, BusinessCriticality.CRITICAL, DataClassification.PII)
        vuln = SecurityVulnerability(
            id="V1", name="SQL Injection", description="Test",
            severity=VulnerabilitySeverity.CRITICAL, cvss_score=9.5,
            remediation_cost_eur=5_000
        )
        report = service.calculate_report("Production System", [vuln], {"V1": "WebApp"})

        md_export = service.export_report(report.id, format="markdown")
        assert "# Security Debt Assessment: Production System" in md_export
        assert "Executive Summary" in md_export
        assert "Debt by Severity" in md_export

    def test_export_report_invalid_format(self, service):
        """Test report export with invalid format."""
        service.register_asset("Test", 100_000, BusinessCriticality.SUPPORTING, DataClassification.INTERNAL)
        report = service.calculate_report("Test", [], {})

        with pytest.raises(ValueError, match="Unsupported format"):
            service.export_report(report.id, format="xml")

    def test_export_report_not_found(self, service):
        """Test report export with non-existent report."""
        with pytest.raises(ValueError, match="Report not found"):
            service.export_report(uuid4())


# ============================================================================
# Enum Tests
# ============================================================================

class TestEnums:
    """Tests for service enums."""

    def test_vulnerability_severity_values(self):
        """Test vulnerability severity enum values."""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.INFO.value == "info"

    def test_network_exposure_values(self):
        """Test network exposure enum values."""
        assert NetworkExposure.INTERNET_FACING.value == "internet_facing"
        assert NetworkExposure.DMZ.value == "dmz"
        assert NetworkExposure.INTERNAL_NETWORK.value == "internal_network"
        assert NetworkExposure.ISOLATED.value == "isolated"

    def test_authentication_level_values(self):
        """Test authentication level enum values."""
        assert AuthenticationLevel.NONE.value == "none"
        assert AuthenticationLevel.BASIC.value == "basic"
        assert AuthenticationLevel.STANDARD.value == "standard"
        assert AuthenticationLevel.STRONG.value == "strong"
        assert AuthenticationLevel.ZERO_TRUST.value == "zero_trust"

    def test_data_sensitivity_values(self):
        """Test data sensitivity enum values."""
        assert DataSensitivity.PUBLIC.value == "public"
        assert DataSensitivity.INTERNAL.value == "internal"
        assert DataSensitivity.CONFIDENTIAL.value == "confidential"
        assert DataSensitivity.RESTRICTED.value == "restricted"
        assert DataSensitivity.TOP_SECRET.value == "top_secret"

    def test_business_criticality_values(self):
        """Test business criticality enum values."""
        assert BusinessCriticality.NON_ESSENTIAL.value == "non_essential"
        assert BusinessCriticality.SUPPORTING.value == "supporting"
        assert BusinessCriticality.IMPORTANT.value == "important"
        assert BusinessCriticality.CRITICAL.value == "critical"
        assert BusinessCriticality.MISSION_CRITICAL.value == "mission_critical"

    def test_data_classification_values(self):
        """Test data classification enum values."""
        assert DataClassification.UNCLASSIFIED.value == "unclassified"
        assert DataClassification.PII.value == "pii"
        assert DataClassification.PHI.value == "phi"
        assert DataClassification.PCI.value == "pci"
        assert DataClassification.FINANCIAL.value == "financial"
