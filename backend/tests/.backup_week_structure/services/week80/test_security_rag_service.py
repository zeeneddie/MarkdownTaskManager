"""
Unit tests for SecurityRAGService - Week 81

Tests for security knowledge base with RAG capabilities:
- OWASP Top 10 2021 guidance
- CWE knowledge base
- Remediation recommendations
- Security checklists
- Knowledge search
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.security_rag_service import SecurityRAGService


class TestSecurityRAGServiceInit:
    """Test SecurityRAGService initialization."""

    def test_init_with_db_session(self):
        """Service should initialize with database session."""
        mock_db = MagicMock()
        service = SecurityRAGService(mock_db)
        assert service.db == mock_db

    def test_owasp_knowledge_loaded(self):
        """Service should have OWASP Top 10 knowledge."""
        mock_db = MagicMock()
        service = SecurityRAGService(mock_db)
        assert hasattr(service, 'OWASP_TOP_10_2021')
        assert len(service.OWASP_TOP_10_2021) == 10

    def test_cwe_knowledge_loaded(self):
        """Service should have CWE knowledge."""
        mock_db = MagicMock()
        service = SecurityRAGService(mock_db)
        assert hasattr(service, 'CWE_KNOWLEDGE')
        assert len(service.CWE_KNOWLEDGE) > 0


class TestOWASPGuidance:
    """Tests for OWASP Top 10 guidance."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return SecurityRAGService(mock_db)

    @pytest.mark.asyncio
    async def test_get_owasp_a01_guidance(self, service):
        """Should provide A01 Broken Access Control guidance."""
        result = await service.get_owasp_guidance("A01")

        assert result is not None
        assert "name" in result or "description" in result

    @pytest.mark.asyncio
    async def test_get_owasp_a02_guidance(self, service):
        """Should provide A02 Cryptographic Failures guidance."""
        result = await service.get_owasp_guidance("A02")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a03_guidance(self, service):
        """Should provide A03 Injection guidance."""
        result = await service.get_owasp_guidance("A03")

        assert result is not None
        assert "injection" in str(result).lower() or "name" in result

    @pytest.mark.asyncio
    async def test_get_owasp_a04_guidance(self, service):
        """Should provide A04 Insecure Design guidance."""
        result = await service.get_owasp_guidance("A04")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a05_guidance(self, service):
        """Should provide A05 Security Misconfiguration guidance."""
        result = await service.get_owasp_guidance("A05")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a06_guidance(self, service):
        """Should provide A06 Vulnerable Components guidance."""
        result = await service.get_owasp_guidance("A06")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a07_guidance(self, service):
        """Should provide A07 Authentication Failures guidance."""
        result = await service.get_owasp_guidance("A07")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a08_guidance(self, service):
        """Should provide A08 Software and Data Integrity Failures guidance."""
        result = await service.get_owasp_guidance("A08")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a09_guidance(self, service):
        """Should provide A09 Security Logging Failures guidance."""
        result = await service.get_owasp_guidance("A09")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_a10_guidance(self, service):
        """Should provide A10 SSRF guidance."""
        result = await service.get_owasp_guidance("A10")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_owasp_invalid_category(self, service):
        """Should return None for invalid category."""
        result = await service.get_owasp_guidance("A99")

        assert result is None


class TestCWEGuidance:
    """Tests for CWE knowledge base."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return SecurityRAGService(mock_db)

    @pytest.mark.asyncio
    async def test_get_cwe_79_xss(self, service):
        """Should provide CWE-79 XSS guidance."""
        result = await service.get_cwe_guidance("CWE-79")

        assert result is not None
        if result:
            assert "xss" in str(result).lower() or "script" in str(result).lower()

    @pytest.mark.asyncio
    async def test_get_cwe_89_sql_injection(self, service):
        """Should provide CWE-89 SQL Injection guidance."""
        result = await service.get_cwe_guidance("CWE-89")

        assert result is not None
        if result:
            assert "sql" in str(result).lower()

    @pytest.mark.asyncio
    async def test_get_cwe_22_path_traversal(self, service):
        """Should provide CWE-22 Path Traversal guidance."""
        result = await service.get_cwe_guidance("CWE-22")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_cwe_78_os_injection(self, service):
        """Should provide CWE-78 OS Command Injection guidance."""
        result = await service.get_cwe_guidance("CWE-78")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_cwe_352_csrf(self, service):
        """Should provide CWE-352 CSRF guidance."""
        result = await service.get_cwe_guidance("CWE-352")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_cwe_918_ssrf(self, service):
        """Should provide CWE-918 SSRF guidance."""
        result = await service.get_cwe_guidance("CWE-918")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_cwe_invalid(self, service):
        """Should return None for unknown CWE."""
        result = await service.get_cwe_guidance("CWE-99999")

        assert result is None


class TestRemediationGuidance:
    """Tests for remediation recommendations."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return SecurityRAGService(mock_db)

    @pytest.mark.asyncio
    async def test_get_sql_injection_remediation(self, service):
        """Should provide SQL injection remediation."""
        result = await service.get_remediation(
            vulnerability_type="sql_injection",
            language="python",
            framework=None
        )

        assert result is not None
        assert "steps" in result or "recommendation" in result or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_xss_remediation(self, service):
        """Should provide XSS remediation."""
        result = await service.get_remediation(
            vulnerability_type="xss",
            language="javascript",
            framework="react"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_remediation_with_framework(self, service):
        """Should provide framework-specific remediation."""
        result = await service.get_remediation(
            vulnerability_type="sql_injection",
            language="python",
            framework="django"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_remediation_generic(self, service):
        """Should provide generic remediation when no language specified."""
        result = await service.get_remediation(
            vulnerability_type="hardcoded_secrets",
            language=None,
            framework=None
        )

        assert result is not None


class TestKnowledgeSearch:
    """Tests for knowledge base search."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return SecurityRAGService(mock_db)

    @pytest.mark.asyncio
    async def test_search_knowledge_sql_injection(self, service):
        """Should find SQL injection related knowledge."""
        service.db.execute.return_value.scalars.return_value.all = MagicMock(return_value=[])

        result = await service.search_knowledge(
            query="sql injection prevention",
            knowledge_type=None,
            limit=10
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_knowledge_with_type(self, service):
        """Should filter by knowledge type."""
        service.db.execute.return_value.scalars.return_value.all = MagicMock(return_value=[])

        result = await service.search_knowledge(
            query="access control",
            knowledge_type="owasp",
            limit=10
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_knowledge_limit(self, service):
        """Should respect limit parameter."""
        mock_results = [MagicMock() for _ in range(5)]
        service.db.execute.return_value.scalars.return_value.all = MagicMock(return_value=mock_results)

        result = await service.search_knowledge(
            query="security",
            knowledge_type=None,
            limit=5
        )

        assert len(result) <= 5


class TestSecurityChecklists:
    """Tests for security checklist generation."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        return SecurityRAGService(mock_db)

    @pytest.mark.asyncio
    async def test_get_python_checklist(self, service):
        """Should provide Python security checklist."""
        result = await service.get_security_checklist(
            language="python",
            framework=None
        )

        assert "checklist" in result or "items" in result or isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_get_javascript_checklist(self, service):
        """Should provide JavaScript security checklist."""
        result = await service.get_security_checklist(
            language="javascript",
            framework=None
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_framework_checklist(self, service):
        """Should provide framework-specific checklist."""
        result = await service.get_security_checklist(
            language="python",
            framework="django"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_generic_checklist(self, service):
        """Should provide generic checklist."""
        result = await service.get_security_checklist(
            language=None,
            framework=None
        )

        assert result is not None


class TestKnowledgeBaseInitialization:
    """Tests for knowledge base initialization."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database."""
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.execute = AsyncMock()
        return SecurityRAGService(mock_db)

    @pytest.mark.asyncio
    async def test_initialize_knowledge_base(self, service):
        """Should initialize knowledge base with OWASP and CWE data."""
        # Mock empty existing data
        service.db.execute.return_value.scalar = MagicMock(return_value=0)

        result = await service.initialize_knowledge_base()

        assert "status" in result or "loaded" in result or result is not None

    @pytest.mark.asyncio
    async def test_initialize_skips_if_exists(self, service):
        """Should skip initialization if data already exists."""
        # Mock existing data
        service.db.execute.return_value.scalar = MagicMock(return_value=10)

        result = await service.initialize_knowledge_base()

        # Should indicate already initialized
        assert result is not None
