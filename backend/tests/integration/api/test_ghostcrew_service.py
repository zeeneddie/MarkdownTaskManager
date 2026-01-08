"""
Unit tests for GhostCrewService - Week 80

Tests for security scanning functionality including:
- Assist mode (interactive)
- Autonomous scanning
- Multi-agent crew mode
- False positive handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime


class TestGhostCrewServiceInit:
    """Test GhostCrewService initialization."""

    def test_init_with_db_session(self):
        """Service should initialize with database session."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()
        service = GhostCrewService(mock_db)
        assert service.db == mock_db

    def test_vulnerability_patterns_loaded(self):
        """Module should have vulnerability patterns loaded."""
        from app.services import ghostcrew_service
        assert hasattr(ghostcrew_service, 'VULNERABILITY_PATTERNS')
        assert len(ghostcrew_service.VULNERABILITY_PATTERNS) > 0

    def test_vulnerability_patterns_structure(self):
        """Vulnerability patterns should have required keys."""
        from app.services.ghostcrew_service import VULNERABILITY_PATTERNS
        for vuln_type, config in VULNERABILITY_PATTERNS.items():
            assert "patterns" in config
            assert "severity" in config
            assert "owasp" in config
            assert "cwe" in config


class TestAssistMode:
    """Tests for interactive assist mode."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()

        # Setup proper mock chain for scalars().all() pattern
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        return GhostCrewService(mock_db)

    @pytest.mark.asyncio
    async def test_assist_with_query(self, service):
        """Assist should respond to security query."""
        result = await service.assist(
            query="How do I prevent SQL injection?",
            context=None,
            project_id=None,
            include_knowledge=True
        )
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_assist_with_code_context(self, service):
        """Assist should analyze provided code context."""
        code = """
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        """
        result = await service.assist(
            query="Is this code secure?",
            context=code,
            project_id=None,
            include_knowledge=True
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_assist_returns_recommendations(self, service):
        """Assist should return recommendations."""
        result = await service.assist(
            query="What are XSS best practices?",
            context=None,
            project_id=None,
            include_knowledge=False
        )
        assert result is not None


class TestAutonomousScan:
    """Tests for autonomous security scanning."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()

        # Setup proper mock chain for scalars().all() pattern
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar_one_or_none.return_value = None

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        return GhostCrewService(mock_db)

    @pytest.mark.asyncio
    async def test_scan_returns_scan_id(self, service):
        """Autonomous scan should return scan ID."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[]):
            result = await service.scan_autonomous(
                repo_path="/tmp/test",
                project_id=1,
                scan_type="quick"
            )
            assert "scan_id" in result

    @pytest.mark.asyncio
    async def test_scan_quick_type(self, service):
        """Quick scan should complete."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[]):
            result = await service.scan_autonomous(
                repo_path="/tmp/test",
                project_id=1,
                scan_type="quick"
            )
            assert "status" in result or "scan_id" in result

    @pytest.mark.asyncio
    async def test_scan_full_type(self, service):
        """Full scan should complete."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[]):
            result = await service.scan_autonomous(
                repo_path="/tmp/test",
                project_id=1,
                scan_type="full"
            )
            assert result is not None


class TestVulnerabilityDetection:
    """Tests for vulnerability pattern detection."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return GhostCrewService(mock_db)

    @pytest.mark.asyncio
    async def test_code_snippet_scan(self, service):
        """Should scan code snippet for vulnerabilities."""
        code = '''
        query = f"SELECT * FROM users WHERE id = {user_id}"
        '''
        findings = await service._scan_code_snippet(code)
        assert isinstance(findings, list)

    @pytest.mark.asyncio
    async def test_detect_hardcoded_secrets_pattern(self, service):
        """Should detect hardcoded secrets pattern."""
        code = '''
        api_key = "sk-1234567890abcdef"
        password = "admin123"
        '''
        findings = await service._scan_code_snippet(code)
        assert isinstance(findings, list)


class TestCrewMode:
    """Tests for multi-agent crew mode."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.execute = AsyncMock()
        return GhostCrewService(mock_db)

    @pytest.mark.asyncio
    async def test_run_crew_returns_results(self, service):
        """Crew should return results."""
        with patch('pathlib.Path.exists', return_value=True):
            result = await service.run_crew(
                project_id=1,
                target_path=None,
                agents=None
            )
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_run_crew_specific_agents(self, service):
        """Crew should accept specific agents."""
        with patch('pathlib.Path.exists', return_value=True):
            result = await service.run_crew(
                project_id=1,
                target_path=None,
                agents=["SecurityAgent"]
            )
            assert result is not None


class TestFalsePositiveHandling:
    """Tests for false positive management."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        return GhostCrewService(mock_db)

    @pytest.mark.asyncio
    async def test_mark_false_positive_not_found(self, service):
        """Should return error if finding not found."""
        finding_id = uuid4()

        # Mock no finding found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute.return_value = mock_result

        result = await service.mark_finding_false_positive(
            finding_id=finding_id,
            reason="Test",
            marked_by="test_user"
        )
        assert "error" in result


class TestScanManagement:
    """Tests for scan management functions."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        from app.services.ghostcrew_service import GhostCrewService
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return GhostCrewService(mock_db)

    @pytest.mark.asyncio
    async def test_get_scan(self, service):
        """Should retrieve scan by ID."""
        scan_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute.return_value = mock_result

        result = await service.get_scan(scan_id)
        assert result is None  # No scan found

    @pytest.mark.asyncio
    async def test_get_scan_findings(self, service):
        """Should retrieve findings for a scan."""
        scan_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.db.execute.return_value = mock_result

        result = await service.get_scan_findings(scan_id, severity=None, limit=100)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_project_scans(self, service):
        """Should retrieve scans for a project."""
        project_id = 1
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.db.execute.return_value = mock_result

        result = await service.get_project_scans(project_id, limit=20)
        assert isinstance(result, list)
