"""
Unit tests for CVEScanner (K2 - Fase 24).

Tests cover:
- Dependency parsing (package.json, requirements.txt, etc.)
- CVE lookup and matching
- CVSS scoring
- Coverage reporting

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.services.security_scanner.adapters.cve_scanner import (
    CVEScanner,
    CVEDatabaseService,
    CVERecord,
    CVSSScore,
    CVSSVersion,
    CVESource,
    DependencyInfo,
    VulnerabilityMatch,
    CVECoverageReport,
    create_cve_scanner,
    ECOSYSTEM_MAP,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# ==================== Fixtures ====================

@pytest.fixture
def scanner():
    """Create a fresh CVEScanner instance."""
    return CVEScanner()


@pytest.fixture
def cve_service():
    """Create a CVE database service."""
    return CVEDatabaseService()


@pytest.fixture
def sample_cve():
    """Create a sample CVE record."""
    return CVERecord(
        cve_id="CVE-2021-44228",
        title="CVE-2021-44228: Log4Shell",
        description="Apache Log4j2 JNDI features RCE vulnerability",
        published_date=datetime(2021, 12, 10),
        last_modified=datetime(2021, 12, 15),
        cvss_scores=[
            CVSSScore(
                version=CVSSVersion.V3_1,
                base_score=10.0,
                vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                severity="CRITICAL",
            )
        ],
        cwe_ids=["CWE-502", "CWE-400"],
        source=CVESource.NVD,
    )


@pytest.fixture
def temp_project():
    """Create a temporary project with dependency files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "4.17.20",
                "express": "4.17.1",
            },
            "devDependencies": {
                "jest": "26.6.0",
            },
        }
        (project_dir / "package.json").write_text(json.dumps(package_json))

        # Create requirements.txt
        requirements = """
requests==2.25.1
django==3.1.0
flask>=1.1.0
"""
        (project_dir / "requirements.txt").write_text(requirements)

        yield project_dir


# ==================== CVERecord Tests ====================

class TestCVERecord:
    """Test CVE record functionality."""

    def test_highest_cvss_single_score(self, sample_cve):
        """Test getting highest CVSS with single score."""
        cvss = sample_cve.highest_cvss
        assert cvss is not None
        assert cvss.base_score == 10.0

    def test_highest_cvss_multiple_scores(self):
        """Test getting highest CVSS with multiple scores."""
        cve = CVERecord(
            cve_id="CVE-TEST",
            title="Test",
            description="Test",
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
            cvss_scores=[
                CVSSScore(version=CVSSVersion.V2, base_score=6.0, vector_string="", severity="MEDIUM"),
                CVSSScore(version=CVSSVersion.V3_1, base_score=8.5, vector_string="", severity="HIGH"),
            ],
        )
        cvss = cve.highest_cvss
        assert cvss.base_score == 8.5

    def test_severity_critical(self, sample_cve):
        """Test severity mapping for critical."""
        assert sample_cve.severity == Severity.CRITICAL

    def test_severity_high(self):
        """Test severity mapping for high."""
        cve = CVERecord(
            cve_id="CVE-TEST",
            title="Test",
            description="Test",
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
            cvss_scores=[
                CVSSScore(version=CVSSVersion.V3_1, base_score=7.5, vector_string="", severity="HIGH"),
            ],
        )
        assert cve.severity == Severity.HIGH

    def test_severity_medium(self):
        """Test severity mapping for medium."""
        cve = CVERecord(
            cve_id="CVE-TEST",
            title="Test",
            description="Test",
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
            cvss_scores=[
                CVSSScore(version=CVSSVersion.V3_1, base_score=5.0, vector_string="", severity="MEDIUM"),
            ],
        )
        assert cve.severity == Severity.MEDIUM

    def test_severity_no_cvss(self):
        """Test severity with no CVSS scores."""
        cve = CVERecord(
            cve_id="CVE-TEST",
            title="Test",
            description="Test",
            published_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )
        assert cve.severity == Severity.MEDIUM  # Default


# ==================== Dependency Parsing Tests ====================

class TestDependencyParsing:
    """Test dependency file parsing."""

    def test_parse_package_json(self, scanner, temp_project):
        """Test parsing package.json."""
        package_json = temp_project / "package.json"
        content = package_json.read_text()
        deps = scanner._parse_package_json(content, str(package_json))

        assert len(deps) == 3
        lodash = next(d for d in deps if d.name == "lodash")
        assert lodash.version == "4.17.20"
        assert lodash.ecosystem == "npm"
        assert not lodash.is_dev_dependency

        jest = next(d for d in deps if d.name == "jest")
        assert jest.is_dev_dependency

    def test_parse_requirements_txt(self, scanner, temp_project):
        """Test parsing requirements.txt."""
        req_file = temp_project / "requirements.txt"
        content = req_file.read_text()
        deps = scanner._parse_requirements_txt(content, str(req_file))

        assert len(deps) >= 2
        requests = next(d for d in deps if d.name == "requests")
        assert requests.version == "2.25.1"
        assert requests.ecosystem == "pypi"

    def test_parse_empty_file(self, scanner):
        """Test parsing empty file."""
        deps = scanner._parse_package_json("{}", "/test/package.json")
        assert deps == []

    def test_parse_invalid_json(self, scanner):
        """Test parsing invalid JSON."""
        deps = scanner._parse_package_json("not json", "/test/package.json")
        assert deps == []


# ==================== Scanner Tests ====================

class TestCVEScanner:
    """Test CVE scanner functionality."""

    def test_scanner_type(self, scanner):
        """Test scanner type is correct."""
        assert scanner.scanner_type == ScannerType.CVE_SCANNER

    def test_scanner_version(self, scanner):
        """Test scanner has version."""
        assert scanner.VERSION == "1.0.0"

    def test_is_available(self, scanner):
        """Test scanner is always available."""
        assert scanner.is_available() is True

    def test_supported_languages(self, scanner):
        """Test supported languages."""
        languages = scanner.supported_languages
        assert "generic" in languages

    @pytest.mark.asyncio
    async def test_scan_empty_directory(self, scanner):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await scanner.scan(Path(tmpdir))
            assert result.scanner == ScannerType.CVE_SCANNER
            assert result.files_scanned == 0
            assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_scan_with_dependencies(self, scanner, temp_project):
        """Test scanning project with dependencies."""
        # Mock the CVE lookup to avoid network calls
        with patch.object(scanner.cve_service, 'lookup_package_vulnerabilities', new_callable=AsyncMock) as mock_lookup:
            mock_lookup.return_value = []  # No vulnerabilities

            result = await scanner.scan(temp_project)

            assert result.scanner == ScannerType.CVE_SCANNER
            assert result.files_scanned > 0


# ==================== Coverage Report Tests ====================

class TestCVECoverageReport:
    """Test CVE coverage reporting."""

    def test_coverage_report_structure(self, scanner):
        """Test coverage report has correct structure."""
        report = scanner.get_coverage_report()

        assert isinstance(report, CVECoverageReport)
        assert report.scan_timestamp is not None
        assert report.cve_sources_used is not None

    def test_coverage_report_to_dict(self, scanner):
        """Test coverage report can be serialized."""
        report = scanner.get_coverage_report()
        data = report.to_dict()

        assert "summary" in data
        assert "severity_breakdown" in data
        assert "sources_used" in data


# ==================== Factory Function Tests ====================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_cve_scanner(self):
        """Test factory function creates scanner."""
        scanner = create_cve_scanner()

        assert isinstance(scanner, CVEScanner)
        assert scanner.scanner_type == ScannerType.CVE_SCANNER

    def test_create_cve_scanner_with_api_key(self):
        """Test factory function with API key."""
        scanner = create_cve_scanner(nvd_api_key="test-key")

        assert scanner.cve_service.nvd_api_key == "test-key"


# ==================== Ecosystem Map Tests ====================

class TestEcosystemMap:
    """Test ecosystem mapping."""

    def test_npm_files(self):
        """Test npm ecosystem files."""
        assert "package.json" in ECOSYSTEM_MAP["npm"]
        assert "package-lock.json" in ECOSYSTEM_MAP["npm"]
        assert "yarn.lock" in ECOSYSTEM_MAP["npm"]

    def test_pypi_files(self):
        """Test pypi ecosystem files."""
        assert "requirements.txt" in ECOSYSTEM_MAP["pypi"]
        assert "poetry.lock" in ECOSYSTEM_MAP["pypi"]

    def test_go_files(self):
        """Test go ecosystem files."""
        assert "go.mod" in ECOSYSTEM_MAP["go"]
        assert "go.sum" in ECOSYSTEM_MAP["go"]

    def test_all_ecosystems_have_files(self):
        """Test all ecosystems have associated files."""
        for ecosystem, files in ECOSYSTEM_MAP.items():
            assert len(files) > 0, f"Ecosystem {ecosystem} has no files"


# ==================== CVSS Score Tests ====================

class TestCVSSScore:
    """Test CVSS score functionality."""

    def test_cvss_v3_1(self):
        """Test CVSS v3.1 score."""
        score = CVSSScore(
            version=CVSSVersion.V3_1,
            base_score=9.8,
            vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            severity="CRITICAL",
            attack_vector="NETWORK",
            attack_complexity="LOW",
        )
        assert score.version == CVSSVersion.V3_1
        assert score.base_score == 9.8
        assert score.attack_vector == "NETWORK"

    def test_cvss_v2(self):
        """Test CVSS v2 score."""
        score = CVSSScore(
            version=CVSSVersion.V2,
            base_score=7.5,
            vector_string="AV:N/AC:L/Au:N/C:P/I:P/A:P",
            severity="HIGH",
        )
        assert score.version == CVSSVersion.V2
        assert score.base_score == 7.5


# ==================== Finding Creation Tests ====================

class TestFindingCreation:
    """Test security finding creation."""

    def test_create_finding_from_match(self, scanner, sample_cve):
        """Test creating finding from vulnerability match."""
        dep = DependencyInfo(
            name="log4j-core",
            version="2.14.0",
            ecosystem="maven",
            file_path="/test/pom.xml",
            line_number=15,
        )

        match = VulnerabilityMatch(
            dependency=dep,
            cve=sample_cve,
            affected_versions="<= 2.14.0",
            fixed_version="2.17.0",
        )

        finding = scanner._create_finding(match)

        assert "CVE-2021-44228" in finding.rule_id
        assert finding.severity == Severity.CRITICAL
        assert "log4j-core" in finding.title
        assert finding.location.file_path == "/test/pom.xml"
        assert finding.location.start_line == 15
        assert len(finding.suggested_fixes) > 0
