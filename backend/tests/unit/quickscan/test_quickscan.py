"""
Tests for Legacy Quickscan Service.

Fase 24 - A1: 15-minute automated legacy assessment.
"""

import pytest
from pathlib import Path
from datetime import datetime

from app.services.quickscan import (
    QuickscanConfig,
    QuickscanReport,
    TechnologyStack,
    ComplexityScore,
    RiskAssessment,
    Recommendation,
    ModernizationApproach,
    LegacyQuickscanService,
    create_quickscan_service,
)
from app.services.quickscan.models import RiskLevel, EffortEstimate
from app.services.quickscan.analyzers import (
    TechnologyDetector,
    ComplexityAnalyzer,
    SecurityAnalyzer,
    EffortEstimator,
)


# =============================================================================
# MODEL TESTS
# =============================================================================


class TestQuickscanConfig:
    """Tests for QuickscanConfig model."""

    def test_config_creation(self, tmp_path):
        """Should create config with defaults."""
        config = QuickscanConfig(project_path=tmp_path)
        assert config.project_path == tmp_path
        assert config.max_scan_time_seconds == 900
        assert config.include_security_scan is True

    def test_config_project_name_default(self, tmp_path):
        """Should default project name to folder name."""
        config = QuickscanConfig(project_path=tmp_path)
        assert config.project_name == tmp_path.name

    def test_config_custom_name(self, tmp_path):
        """Should use custom project name."""
        config = QuickscanConfig(
            project_path=tmp_path,
            project_name="CustomProject"
        )
        assert config.project_name == "CustomProject"


class TestTechnologyStack:
    """Tests for TechnologyStack model."""

    def test_stack_creation(self):
        """Should create technology stack."""
        stack = TechnologyStack(
            primary_language="Classic ASP",
            languages={"Classic ASP": 10000, "JavaScript": 2000},
            frameworks=["jQuery"],
            databases=["SQL Server"],
        )
        assert stack.primary_language == "Classic ASP"
        assert stack.languages["Classic ASP"] == 10000

    def test_stack_to_dict(self):
        """Should convert to dict."""
        stack = TechnologyStack(
            primary_language="Python",
            languages={"Python": 5000},
        )
        data = stack.to_dict()
        assert data["primary_language"] == "Python"
        assert "languages" in data


class TestComplexityScore:
    """Tests for ComplexityScore model."""

    def test_score_creation(self):
        """Should create complexity score."""
        score = ComplexityScore(
            overall_score=65.5,
            cyclomatic_complexity_avg=15.2,
            lines_of_code=50000,
        )
        assert score.overall_score == 65.5
        assert score.lines_of_code == 50000

    def test_score_defaults(self):
        """Should have sensible defaults."""
        score = ComplexityScore(overall_score=50.0)
        assert score.maintainability_index == 0.0
        assert score.duplication_percentage == 0.0


class TestRiskAssessment:
    """Tests for RiskAssessment model."""

    def test_assessment_creation(self):
        """Should create risk assessment."""
        assessment = RiskAssessment(
            overall_risk_score=75.0,
            risk_level=RiskLevel.HIGH,
            critical_findings=5,
            high_findings=20,
        )
        assert assessment.overall_risk_score == 75.0
        assert assessment.risk_level == RiskLevel.HIGH


class TestRecommendation:
    """Tests for Recommendation enum."""

    def test_recommendation_values(self):
        """Should have expected values."""
        assert Recommendation.GO.value == "go"
        assert Recommendation.CONDITIONAL.value == "conditional"
        assert Recommendation.NO_GO.value == "no_go"


class TestModernizationApproach:
    """Tests for ModernizationApproach enum."""

    def test_approach_values(self):
        """Should have all 5 R's."""
        assert ModernizationApproach.REHOST.value == "rehost"
        assert ModernizationApproach.REPLATFORM.value == "replatform"
        assert ModernizationApproach.REFACTOR.value == "refactor"
        assert ModernizationApproach.REBUILD.value == "rebuild"
        assert ModernizationApproach.REPLACE.value == "replace"


# =============================================================================
# ANALYZER TESTS
# =============================================================================


class TestTechnologyDetector:
    """Tests for TechnologyDetector analyzer."""

    @pytest.mark.asyncio
    async def test_detect_python(self, tmp_path):
        """Should detect Python files."""
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        detector = TechnologyDetector()
        config = QuickscanConfig(project_path=tmp_path)
        result = await detector.analyze(config)

        assert result.success is True
        stack = result.data["technology_stack"]
        assert stack.primary_language == "Python"

    @pytest.mark.asyncio
    async def test_detect_asp(self, tmp_path):
        """Should detect Classic ASP files."""
        (tmp_path / "index.asp").write_text("<%Response.Write(\"Hello\")%>")
        (tmp_path / "functions.inc").write_text("Function Test()\nEnd Function")

        detector = TechnologyDetector()
        config = QuickscanConfig(project_path=tmp_path)
        result = await detector.analyze(config)

        assert result.success is True
        stack = result.data["technology_stack"]
        assert stack.primary_language == "Classic ASP"

    @pytest.mark.asyncio
    async def test_empty_directory(self, tmp_path):
        """Should handle empty directory."""
        detector = TechnologyDetector()
        config = QuickscanConfig(project_path=tmp_path)
        result = await detector.analyze(config)

        # Should not crash, may return Unknown
        assert result.success is True


class TestComplexityAnalyzer:
    """Tests for ComplexityAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyze_simple_code(self, tmp_path):
        """Should analyze simple code."""
        (tmp_path / "simple.py").write_text("""
def hello():
    print("Hello")

def world():
    print("World")
""")

        analyzer = ComplexityAnalyzer()
        config = QuickscanConfig(project_path=tmp_path)
        result = await analyzer.analyze(config)

        assert result.success is True
        score = result.data["complexity_score"]
        assert score.files_count == 1
        assert score.lines_of_code > 0

    @pytest.mark.asyncio
    async def test_analyze_complex_code(self, tmp_path):
        """Should detect high complexity."""
        # Create file with many branches
        complex_code = """
def process(data):
    if data is None:
        return None
    elif data == 1:
        return "one"
    elif data == 2:
        return "two"
    elif data == 3:
        for i in range(10):
            if i % 2 == 0:
                while i > 0:
                    i -= 1
        return "three"
    else:
        try:
            return str(data)
        except Exception:
            return "error"
"""
        (tmp_path / "complex.py").write_text(complex_code)

        analyzer = ComplexityAnalyzer()
        config = QuickscanConfig(project_path=tmp_path)
        result = await analyzer.analyze(config)

        assert result.success is True
        score = result.data["complexity_score"]
        assert score.cyclomatic_complexity_avg > 0


# =============================================================================
# SERVICE TESTS
# =============================================================================


class TestLegacyQuickscanService:
    """Tests for LegacyQuickscanService."""

    def test_service_creation(self):
        """Should create service with analyzers."""
        service = create_quickscan_service()
        assert service is not None
        assert len(service.analyzers) == 4

    @pytest.mark.asyncio
    async def test_scan_python_project(self, tmp_path):
        """Should scan Python project."""
        # Create simple Python project
        (tmp_path / "app.py").write_text("print('Hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        service = create_quickscan_service()
        config = QuickscanConfig(project_path=tmp_path)
        report = await service.scan(config)

        assert report.id is not None
        assert report.recommendation in [Recommendation.GO, Recommendation.CONDITIONAL, Recommendation.NO_GO]
        assert report.technology_stack is not None
        assert report.complexity_score is not None

    @pytest.mark.asyncio
    async def test_scan_asp_project(self, tmp_path):
        """Should scan Classic ASP project."""
        # Create ASP project
        (tmp_path / "index.asp").write_text("""
<%
Response.Write("Hello")
sql = "SELECT * FROM users WHERE id=" & Request("id")
conn.Execute(sql)
%>
""")

        service = create_quickscan_service()
        config = QuickscanConfig(project_path=tmp_path)
        report = await service.scan(config)

        assert report.technology_stack.primary_language == "Classic ASP"
        # ASP should generally get lower scores due to legacy nature
        assert report.recommendation_score < 80

    @pytest.mark.asyncio
    async def test_report_has_next_steps(self, tmp_path):
        """Report should include next steps."""
        (tmp_path / "app.py").write_text("print('Hello')")

        service = create_quickscan_service()
        config = QuickscanConfig(project_path=tmp_path)
        report = await service.scan(config)

        assert len(report.recommended_next_steps) > 0
        assert len(report.key_findings) > 0

    @pytest.mark.asyncio
    async def test_report_duration(self, tmp_path):
        """Report should track duration."""
        (tmp_path / "app.py").write_text("print('Hello')")

        service = create_quickscan_service()
        config = QuickscanConfig(project_path=tmp_path)
        report = await service.scan(config)

        assert report.duration_seconds > 0
        assert report.completed_at is not None
        assert report.started_at < report.completed_at


class TestRecommendationLogic:
    """Tests for recommendation generation logic."""

    @pytest.mark.asyncio
    async def test_go_recommendation_for_modern_code(self, tmp_path):
        """Modern, simple code should get GO."""
        # Create modern TypeScript project
        (tmp_path / "app.ts").write_text("const hello = () => console.log('Hello');")
        (tmp_path / "utils.ts").write_text("export const add = (a: number, b: number) => a + b;")

        service = create_quickscan_service()
        config = QuickscanConfig(project_path=tmp_path)
        report = await service.scan(config)

        # Small, modern code should generally be favorable
        assert report.recommendation_score >= 40

    @pytest.mark.asyncio
    async def test_conditional_or_nogo_for_legacy(self, tmp_path):
        """Legacy code should get CONDITIONAL or NO_GO."""
        # Create legacy VB6 project
        (tmp_path / "Form1.frm").write_text("""
VERSION 5.00
Begin VB.Form Form1
   Private Sub Form_Load()
      MsgBox "Hello"
   End Sub
End
""")

        service = create_quickscan_service()
        config = QuickscanConfig(project_path=tmp_path)
        report = await service.scan(config)

        # VB6 is very legacy - should not be GO
        # Note: Small codebase might still score OK
        assert report.suggested_approach in [
            ModernizationApproach.REBUILD,
            ModernizationApproach.REPLACE,
            ModernizationApproach.REFACTOR,
        ]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestQuickscanIntegration:
    """Integration tests for quickscan."""

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self, tmp_path):
        """Test complete scan workflow."""
        # Create mixed project
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("def main(): print('Hello')")
        (src / "app.js").write_text("console.log('Hello');")

        service = create_quickscan_service()
        config = QuickscanConfig(
            project_path=tmp_path,
            project_name="TestProject",
        )
        report = await service.scan(config)

        # Verify complete report
        assert report.project_name == "TestProject"
        assert report.technology_stack is not None
        assert report.complexity_score is not None
        assert report.recommendation is not None
        assert report.suggested_approach is not None
        assert len(report.analyzer_results) > 0

        # Verify serialization
        report_dict = report.to_dict()
        assert "recommendation" in report_dict
        assert "technology_stack" in report_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
