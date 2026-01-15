"""
Unit tests for RiskHeatMapService (A4 - Fase 24).

Tests cover:
- Risk scoring algorithms
- File and module risk calculation
- Heat map generation
- D3.js export format
- Summary reporting

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from app.services.risk_heat_map_service import (
    RiskLevel,
    RiskCategory,
    RiskScore,
    FileRisk,
    ModuleRisk,
    HeatMapCell,
    RiskHeatMap,
    RiskHeatMapService,
    SEVERITY_WEIGHTS,
    create_risk_heat_map_service,
)
from app.services.security_scanner.models.findings import (
    SecurityFinding,
    SecurityReport,
    ScanResult,
    ScannerType,
    Severity,
    Location,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh RiskHeatMapService instance."""
    return RiskHeatMapService()


@pytest.fixture
def sample_finding():
    """Create a sample security finding."""
    return SecurityFinding(
        id="test-001",
        rule_id="SQL-001",
        title="SQL Injection",
        description="Potential SQL injection vulnerability",
        severity=Severity.HIGH,
        scanner=ScannerType.OPENGREP,
        location=Location(
            file_path="/project/app/database.py",
            start_line=42,
        ),
        category="sql_injection",
        cwe_ids=["CWE-89"],
    )


@pytest.fixture
def sample_findings():
    """Create a list of sample findings."""
    return [
        SecurityFinding(
            id="f1",
            rule_id="SQL-001",
            title="SQL Injection",
            description="SQL injection",
            severity=Severity.CRITICAL,
            scanner=ScannerType.OPENGREP,
            location=Location(file_path="/project/app/db.py", start_line=10),
            category="sql_injection",
        ),
        SecurityFinding(
            id="f2",
            rule_id="XSS-001",
            title="XSS",
            description="Cross-site scripting",
            severity=Severity.HIGH,
            scanner=ScannerType.OPENGREP,
            location=Location(file_path="/project/app/db.py", start_line=20),
            category="xss",
        ),
        SecurityFinding(
            id="f3",
            rule_id="SEC-001",
            title="Hardcoded Secret",
            description="Hardcoded secret",
            severity=Severity.MEDIUM,
            scanner=ScannerType.SECRET_SCANNER,
            location=Location(file_path="/project/app/config.py", start_line=5),
            category="hardcoded_secret",
        ),
    ]


@pytest.fixture
def sample_security_report(sample_findings):
    """Create a sample security report."""
    scan_result = ScanResult(
        scanner=ScannerType.OPENGREP,
        scanner_version="1.0.0",
        scan_duration_ms=1000,
        findings=sample_findings,
        files_scanned=10,
    )

    return SecurityReport(
        project_path="/project",
        scan_results=[scan_result],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        languages_detected={"python"},
        scanners_used={ScannerType.OPENGREP},
    )


# ==================== RiskScore Tests ====================

class TestRiskScore:
    """Test RiskScore functionality."""

    def test_from_score_critical(self):
        """Test score >= 80 is critical."""
        score = RiskScore.from_score(85)
        assert score.level == RiskLevel.CRITICAL
        assert score.raw_score == 85

    def test_from_score_high(self):
        """Test score 60-79 is high."""
        score = RiskScore.from_score(65)
        assert score.level == RiskLevel.HIGH

    def test_from_score_medium(self):
        """Test score 40-59 is medium."""
        score = RiskScore.from_score(50)
        assert score.level == RiskLevel.MEDIUM

    def test_from_score_low(self):
        """Test score 20-39 is low."""
        score = RiskScore.from_score(30)
        assert score.level == RiskLevel.LOW

    def test_from_score_minimal(self):
        """Test score < 20 is minimal."""
        score = RiskScore.from_score(10)
        assert score.level == RiskLevel.MINIMAL

    def test_normalized_property(self):
        """Test normalized property."""
        score = RiskScore(raw_score=50, level=RiskLevel.MEDIUM)
        assert score.normalized == 0.5

    def test_normalized_capped_at_1(self):
        """Test normalized is capped at 1."""
        score = RiskScore(raw_score=150, level=RiskLevel.CRITICAL)
        assert score.normalized == 1.0


# ==================== FileRisk Tests ====================

class TestFileRisk:
    """Test FileRisk functionality."""

    def test_to_dict(self):
        """Test FileRisk serialization."""
        file_risk = FileRisk(
            file_path="/project/app/db.py",
            risk_score=RiskScore.from_score(75),
            finding_count=5,
            critical_count=1,
            high_count=2,
            medium_count=2,
            low_count=0,
            categories={"sql_injection", "xss"},
            cwe_ids={"CWE-89", "CWE-79"},
            scanners={"opengrep"},
            relative_path="app/db.py",
            directory="/project/app",
            filename="db.py",
        )

        data = file_risk.to_dict()

        assert data["file_path"] == "/project/app/db.py"
        assert data["risk_score"] == 75
        assert data["risk_level"] == "high"
        assert data["finding_count"] == 5
        assert data["severity_breakdown"]["critical"] == 1
        assert "sql_injection" in data["categories"]
        assert "CWE-89" in data["cwe_ids"]


# ==================== ModuleRisk Tests ====================

class TestModuleRisk:
    """Test ModuleRisk functionality."""

    def test_to_dict(self):
        """Test ModuleRisk serialization."""
        module_risk = ModuleRisk(
            module_path="/project/app",
            module_name="app",
            risk_score=RiskScore.from_score(60),
            file_count=5,
            total_findings=10,
            high_risk_files=["db.py", "auth.py"],
            avg_file_risk=45.0,
            max_file_risk=75.0,
        )

        data = module_risk.to_dict()

        assert data["module_name"] == "app"
        assert data["risk_score"] == 60
        assert data["file_count"] == 5
        assert "db.py" in data["high_risk_files"]


# ==================== HeatMapCell Tests ====================

class TestHeatMapCell:
    """Test HeatMapCell functionality."""

    def test_to_dict(self):
        """Test HeatMapCell serialization."""
        cell = HeatMapCell(
            x=0,
            y=1,
            label="db.py",
            risk_score=75.0,
            risk_level=RiskLevel.HIGH,
            file_count=1,
            finding_count=5,
            tooltip="app/db.py: 5 findings",
        )

        data = cell.to_dict()

        assert data["x"] == 0
        assert data["y"] == 1
        assert data["value"] == 75.0
        assert data["level"] == "high"
        assert "5 findings" in data["tooltip"]


# ==================== RiskHeatMap Tests ====================

class TestRiskHeatMap:
    """Test RiskHeatMap functionality."""

    def test_to_dict(self):
        """Test RiskHeatMap serialization."""
        heat_map = RiskHeatMap(
            project_path="/project",
            generated_at=datetime(2026, 1, 15, 12, 0, 0),
            overall_risk=RiskScore.from_score(50),
            total_files=10,
            total_findings=25,
            files_by_risk={"critical": 1, "high": 3},
            findings_by_severity={"critical": 2, "high": 10},
        )

        data = heat_map.to_dict()

        assert data["project_path"] == "/project"
        assert data["summary"]["overall_risk_score"] == 50
        assert data["summary"]["total_files"] == 10
        assert data["distribution"]["by_risk_level"]["critical"] == 1

    def test_to_d3_format(self):
        """Test D3.js format export."""
        heat_map = RiskHeatMap(
            project_path="/project/myapp",
            generated_at=datetime.utcnow(),
            overall_risk=RiskScore.from_score(45),
            total_files=5,
            total_findings=10,
        )

        d3_data = heat_map.to_d3_format()

        assert d3_data["name"] == "myapp"
        assert "metadata" in d3_data
        assert d3_data["metadata"]["overall_risk"] == 45


# ==================== RiskHeatMapService Tests ====================

class TestRiskHeatMapService:
    """Test RiskHeatMapService functionality."""

    def test_initialization_default(self, service):
        """Test default initialization."""
        assert service.severity_weights == SEVERITY_WEIGHTS
        assert service.max_score == 100.0

    def test_initialization_custom_weights(self):
        """Test custom severity weights."""
        custom_weights = {Severity.CRITICAL: 20.0}
        service = RiskHeatMapService(severity_weights=custom_weights)
        assert service.severity_weights[Severity.CRITICAL] == 20.0

    def test_generate_heat_map(self, service, sample_security_report):
        """Test heat map generation."""
        heat_map = service.generate_heat_map(sample_security_report)

        assert heat_map.project_path == "/project"
        assert heat_map.total_files >= 1
        assert heat_map.total_findings == 3
        assert heat_map.overall_risk is not None

    def test_generate_heat_map_with_project_root(self, service, sample_security_report):
        """Test heat map with custom project root."""
        heat_map = service.generate_heat_map(
            sample_security_report,
            project_root=Path("/custom/root"),
        )

        assert heat_map.project_path == "/custom/root"

    def test_calculate_file_risks(self, service, sample_findings):
        """Test file risk calculation."""
        file_risks = service._calculate_file_risks(sample_findings, "/project")

        # Should have 2 unique files
        assert len(file_risks) == 2

        # Find db.py file risk
        db_risk = next(f for f in file_risks if "db.py" in f.file_path)
        assert db_risk.finding_count == 2
        assert db_risk.critical_count == 1
        assert db_risk.high_count == 1

    def test_calculate_module_risks(self, service, sample_findings):
        """Test module risk calculation."""
        file_risks = service._calculate_file_risks(sample_findings, "/project")
        module_risks = service._calculate_module_risks(file_risks)

        assert len(module_risks) >= 1

    def test_calculate_overall_risk_empty(self, service):
        """Test overall risk with no files."""
        risk = service._calculate_overall_risk([])
        assert risk.raw_score == 0
        assert risk.level == RiskLevel.MINIMAL

    def test_count_by_risk_level(self, service):
        """Test counting files by risk level."""
        file_risks = [
            FileRisk(
                file_path="/a.py",
                risk_score=RiskScore.from_score(85),
                finding_count=1,
                critical_count=1,
                high_count=0,
                medium_count=0,
                low_count=0,
            ),
            FileRisk(
                file_path="/b.py",
                risk_score=RiskScore.from_score(25),
                finding_count=1,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=1,
            ),
        ]

        counts = service._count_by_risk_level(file_risks)

        assert counts["critical"] == 1
        assert counts["low"] == 1

    def test_count_by_category(self, service, sample_findings):
        """Test counting findings by category."""
        counts = service._count_by_category(sample_findings)

        assert counts["sql_injection"] == 1
        assert counts["xss"] == 1
        assert counts["hardcoded_secret"] == 1

    def test_generate_summary_report(self, service, sample_security_report):
        """Test summary report generation."""
        heat_map = service.generate_heat_map(sample_security_report)
        summary = service.generate_summary_report(heat_map)

        assert "executive_summary" in summary
        assert "key_findings" in summary
        assert "recommendations" in summary

    def test_generate_recommendations(self, service):
        """Test recommendation generation."""
        heat_map = RiskHeatMap(
            project_path="/project",
            generated_at=datetime.utcnow(),
            overall_risk=RiskScore.from_score(75),
            total_files=10,
            total_findings=20,
            findings_by_severity={"critical": 5, "high": 10},
            findings_by_category={"sql_injection": 3, "hardcoded_secret": 2},
        )

        recommendations = service._generate_recommendations(heat_map)

        assert len(recommendations) > 0
        assert any("critical" in r.lower() for r in recommendations)

    def test_generate_grid(self, service, sample_security_report):
        """Test heat map grid generation."""
        heat_map = service.generate_heat_map(sample_security_report)
        grid = heat_map.heat_map_grid

        # Grid should be generated from modules
        assert isinstance(grid, list)

    def test_hotspots_sorted_by_risk(self, service, sample_security_report):
        """Test hotspots are sorted by risk score."""
        heat_map = service.generate_heat_map(sample_security_report)

        if len(heat_map.hotspots) >= 2:
            for i in range(len(heat_map.hotspots) - 1):
                assert (
                    heat_map.hotspots[i].risk_score.raw_score
                    >= heat_map.hotspots[i + 1].risk_score.raw_score
                )


# ==================== Factory Function Tests ====================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_risk_heat_map_service(self):
        """Test factory function creates service."""
        service = create_risk_heat_map_service()

        assert isinstance(service, RiskHeatMapService)
        assert service.max_score == 100.0


# ==================== Severity Weights Tests ====================

class TestSeverityWeights:
    """Test severity weight configuration."""

    def test_default_weights_exist(self):
        """Test all severity levels have weights."""
        for severity in Severity:
            assert severity in SEVERITY_WEIGHTS

    def test_critical_highest_weight(self):
        """Test critical has highest weight."""
        assert SEVERITY_WEIGHTS[Severity.CRITICAL] > SEVERITY_WEIGHTS[Severity.HIGH]
        assert SEVERITY_WEIGHTS[Severity.HIGH] > SEVERITY_WEIGHTS[Severity.MEDIUM]
        assert SEVERITY_WEIGHTS[Severity.MEDIUM] > SEVERITY_WEIGHTS[Severity.LOW]


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases."""

    def test_empty_report(self, service):
        """Test with empty security report."""
        empty_report = SecurityReport(
            project_path="/empty",
            scan_results=[],
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        heat_map = service.generate_heat_map(empty_report)

        assert heat_map.total_files == 0
        assert heat_map.total_findings == 0
        assert heat_map.overall_risk.level == RiskLevel.MINIMAL

    def test_single_finding(self, service):
        """Test with single finding."""
        finding = SecurityFinding(
            id="single",
            rule_id="TEST",
            title="Test",
            description="Test",
            severity=Severity.LOW,
            scanner=ScannerType.OPENGREP,
            location=Location(file_path="/test.py", start_line=1),
        )

        report = SecurityReport(
            project_path="/project",
            scan_results=[
                ScanResult(
                    scanner=ScannerType.OPENGREP,
                    scanner_version="1.0",
                    scan_duration_ms=100,
                    findings=[finding],
                    files_scanned=1,
                )
            ],
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        heat_map = service.generate_heat_map(report)

        assert heat_map.total_files == 1
        assert heat_map.total_findings == 1

