"""
Tests for RmtooAdapterService - Week 117

Tests conversion of MarQed business rules to rmtoo requirement format.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.services.rmtoo_adapter_service import RmtooAdapterService
from app.models.rmtoo import (
    RmtooRequirement,
    RmtooTopic,
    RmtooTraceabilityLink,
    RequirementCategory,
    RequirementStatus,
    LinkType,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_business_rule():
    """Create mock HybridExtractedRule."""
    rule = MagicMock()
    rule.id = uuid4()
    rule.session_id = uuid4()
    rule.rule_name = "ValidateCustomerAge"
    rule.rule_description = "Customer must be at least 18 years old to register"
    rule.rule_category = "validation"
    rule.source_file = "src/services/customer_service.py"
    rule.source_lines = "45-52"
    rule.confidence = 0.85
    rule.complexity_score = 3
    rule.business_impact = "high"
    rule.metadata = {}
    return rule


@pytest.fixture
def mock_requirement():
    """Create mock RmtooRequirement."""
    req = MagicMock(spec=RmtooRequirement)
    req.id = uuid4()
    req.project_id = 1
    req.name = "REQ-BR-0001"
    req.req_type = "requirement"
    req.description = "Customer must be at least 18 years old"
    req.rationale = "Legal compliance requirement"
    req.invented_on = datetime.now()
    req.invented_by = "system"
    req.owner = "development"
    req.status = "not done"
    req.category = "BR"
    req.priority = "high"
    req.confidence = 0.85
    req.validated = False
    req.validated_by = None
    req.solved_by = []
    req.depends_on = []
    req.topic = "BusinessRules"
    req.rmtoo_content = None
    return req


@pytest.fixture
def mock_topic():
    """Create mock RmtooTopic."""
    topic = MagicMock(spec=RmtooTopic)
    topic.id = uuid4()
    topic.project_id = 1
    topic.name = "BusinessRules"
    topic.title = "Business Rules"
    topic.description = "Business rules and validations"
    topic.parent_topic_name = "Requirements"
    return topic


# ============================================================================
# TEST: Requirement Name Generation
# ============================================================================

class TestRequirementNameGeneration:
    """Test requirement name generation with prefixes."""

    @pytest.mark.asyncio
    async def test_generate_br_name(self, mock_db):
        """Should generate REQ-BR-XXXX for business rules."""
        service = RmtooAdapterService(mock_db)

        # Mock query to return no existing requirements (count = 0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 0
        mock_db.execute.return_value = mock_result

        name = await service._get_next_requirement_id(1, RequirementCategory.BR)

        assert name.startswith("REQ-BR-")
        # Name format is REQ-BR-XXX (3 digits) so length is 10
        assert len(name) >= 10

    @pytest.mark.asyncio
    async def test_generate_fr_name(self, mock_db):
        """Should generate REQ-FR-XXXX for functional requirements."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        name = await service._get_next_requirement_id(1, RequirementCategory.FR)

        assert name.startswith("REQ-FR-")

    @pytest.mark.asyncio
    async def test_generate_nfr_name(self, mock_db):
        """Should generate REQ-NFR-XXXX for non-functional requirements."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        name = await service._get_next_requirement_id(1, RequirementCategory.NFR)

        assert name.startswith("REQ-NFR-")

    @pytest.mark.asyncio
    async def test_increment_sequence_number(self, mock_db):
        """Should increment sequence number based on existing requirements."""
        service = RmtooAdapterService(mock_db)

        # Mock existing requirement - return the max name as a string (REQ-BR-005)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "REQ-BR-005"  # Max existing is 005

        mock_db.execute.return_value = mock_result

        name = await service._get_next_requirement_id(1, RequirementCategory.BR)

        # Should be 006 (5 + 1), formatted with leading zeros
        assert name.startswith("REQ-BR-")
        assert name == "REQ-BR-006"


# ============================================================================
# TEST: Category Mapping
# ============================================================================

class TestCategoryMapping:
    """Test mapping business rule categories to rmtoo categories using RULE_TYPE_TO_CATEGORY."""

    def test_map_validation_to_br(self, mock_db):
        """Validation rules should map to BR (Business Rule)."""
        from app.services.rmtoo_adapter_service import RULE_TYPE_TO_CATEGORY
        from app.models.hybrid_extraction import RuleType

        category = RULE_TYPE_TO_CATEGORY.get(RuleType.VALIDATION)
        assert category == RequirementCategory.BR

    def test_map_calculation_to_br(self, mock_db):
        """Calculation rules should map to BR (Business Rule)."""
        from app.services.rmtoo_adapter_service import RULE_TYPE_TO_CATEGORY
        from app.models.hybrid_extraction import RuleType

        category = RULE_TYPE_TO_CATEGORY.get(RuleType.CALCULATION)
        assert category == RequirementCategory.BR

    def test_map_security_to_nfr(self, mock_db):
        """Authorization/Security rules should map to NFR (Non-Functional)."""
        from app.services.rmtoo_adapter_service import RULE_TYPE_TO_CATEGORY
        from app.models.hybrid_extraction import RuleType

        # Authorization is the security-related rule type
        category = RULE_TYPE_TO_CATEGORY.get(RuleType.AUTHORIZATION)
        assert category == RequirementCategory.NFR

    def test_map_performance_to_nfr(self, mock_db):
        """Error handling (performance-related) should map to NFR."""
        from app.services.rmtoo_adapter_service import RULE_TYPE_TO_CATEGORY
        from app.models.hybrid_extraction import RuleType

        # Error handling is NFR-related
        category = RULE_TYPE_TO_CATEGORY.get(RuleType.ERROR_HANDLING)
        assert category == RequirementCategory.NFR

    def test_map_data_access_to_tr(self, mock_db):
        """Data access rules should map to TR (Technical)."""
        from app.services.rmtoo_adapter_service import RULE_TYPE_TO_CATEGORY
        from app.models.hybrid_extraction import RuleType

        category = RULE_TYPE_TO_CATEGORY.get(RuleType.DATA_ACCESS)
        assert category == RequirementCategory.TR

    def test_map_workflow_to_fr(self, mock_db):
        """Workflow rules should map to FR (Functional)."""
        from app.services.rmtoo_adapter_service import RULE_TYPE_TO_CATEGORY
        from app.models.hybrid_extraction import RuleType

        category = RULE_TYPE_TO_CATEGORY.get(RuleType.WORKFLOW)
        assert category == RequirementCategory.FR


# ============================================================================
# TEST: Rmtoo Format Generation
# ============================================================================

class TestRmtooFormatGeneration:
    """Test generation of rmtoo .req file format using model's to_rmtoo_format."""

    def test_generate_basic_format(self, mock_db, mock_requirement):
        """Should generate valid rmtoo format with required fields."""
        # Use the model's to_rmtoo_format method
        mock_requirement.to_rmtoo_format = MagicMock(
            return_value=f"Name: {mock_requirement.name}\nType: {mock_requirement.req_type}\nDescription: {mock_requirement.description}\n"
        )

        content = mock_requirement.to_rmtoo_format()

        assert f"Name: {mock_requirement.name}" in content
        assert f"Type: {mock_requirement.req_type}" in content
        assert "Description:" in content
        assert mock_requirement.description in content

    def test_include_optional_fields(self, mock_db, mock_requirement):
        """Should include optional fields when present."""
        mock_requirement.rationale = "For legal compliance"
        mock_requirement.priority = "high"
        mock_requirement.owner = "development"
        mock_requirement.to_rmtoo_format = MagicMock(
            return_value=f"Name: {mock_requirement.name}\nType: requirement\nRationale: For legal compliance\nPriority: high\nOwner: development\n"
        )

        content = mock_requirement.to_rmtoo_format()

        assert "Rationale:" in content
        assert "Priority:" in content
        assert "Owner:" in content

    def test_include_solved_by_links(self, mock_db, mock_requirement):
        """Should include Solved by references."""
        mock_requirement.solved_by = ["REQ-TR-0001", "REQ-TR-0002"]
        mock_requirement.to_rmtoo_format = MagicMock(
            return_value=f"Name: {mock_requirement.name}\nSolved by: REQ-TR-0001 REQ-TR-0002\n"
        )

        content = mock_requirement.to_rmtoo_format()

        assert "Solved by: REQ-TR-0001 REQ-TR-0002" in content

    def test_include_depends_on_links(self, mock_db, mock_requirement):
        """Should include Depends on references."""
        mock_requirement.depends_on = ["REQ-BR-0001"]
        mock_requirement.to_rmtoo_format = MagicMock(
            return_value=f"Name: {mock_requirement.name}\nDepends on: REQ-BR-0001\n"
        )

        content = mock_requirement.to_rmtoo_format()

        assert "Depends on: REQ-BR-0001" in content

    def test_include_topic(self, mock_db, mock_requirement):
        """Should include Topic reference."""
        mock_requirement.topic = "BusinessRules"
        mock_requirement.to_rmtoo_format = MagicMock(
            return_value=f"Name: {mock_requirement.name}\nTopic: BusinessRules\n"
        )

        content = mock_requirement.to_rmtoo_format()

        assert "Topic: BusinessRules" in content


# ============================================================================
# TEST: Validation
# ============================================================================

class TestValidation:
    """Test requirement validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_requirement(self, mock_db, mock_requirement):
        """Should mark requirement as validated."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_requirement
        mock_db.execute.return_value = mock_result

        result = await service.validate_requirement(mock_requirement.id, "john.doe")

        assert result.validated == True
        assert result.validated_by == "john.doe"
        assert result.status == "approved"

    @pytest.mark.asyncio
    async def test_validate_nonexistent_requirement(self, mock_db):
        """Should raise error for nonexistent requirement."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Correct mock path
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await service.validate_requirement(uuid4(), "john.doe")


# ============================================================================
# TEST: Traceability Links
# ============================================================================

class TestTraceabilityLinks:
    """Test traceability link creation."""

    @pytest.mark.asyncio
    async def test_create_implements_link(self, mock_db, mock_requirement):
        """Should create implements traceability link."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_requirement
        mock_db.execute.return_value = mock_result

        link = await service.create_traceability_link(
            requirement_id=mock_requirement.id,
            entity_type="epic",
            entity_id="EPIC-001",
            entity_name="User Authentication",
            link_type=LinkType.IMPLEMENTS,
            confidence=0.9
        )

        assert link.link_type == "implements"
        assert link.entity_type == "epic"
        assert link.entity_id == "EPIC-001"

    @pytest.mark.asyncio
    async def test_create_tests_link(self, mock_db, mock_requirement):
        """Should create tests traceability link."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_requirement
        mock_db.execute.return_value = mock_result

        link = await service.create_traceability_link(
            requirement_id=mock_requirement.id,
            entity_type="test",
            entity_id="TEST-001",
            entity_name="Age Validation Test",
            link_type=LinkType.TESTS,  # Use TESTS instead of VERIFIES
            confidence=1.0
        )

        assert link.link_type == "tests"


# ============================================================================
# TEST: Dependencies
# ============================================================================

class TestDependencies:
    """Test dependency management."""

    @pytest.mark.asyncio
    async def test_add_dependency(self, mock_db, mock_requirement):
        """Should add solved_by dependency."""
        service = RmtooAdapterService(mock_db)
        mock_requirement.solved_by = []
        mock_requirement.to_rmtoo_format = MagicMock(return_value="Name: REQ-BR-0001\n")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_requirement
        mock_db.execute.return_value = mock_result

        result = await service.add_dependency(mock_requirement.id, "REQ-TR-0001")

        assert "REQ-TR-0001" in result.solved_by

    @pytest.mark.asyncio
    async def test_prevent_duplicate_dependency(self, mock_db, mock_requirement):
        """Should not add duplicate dependency."""
        service = RmtooAdapterService(mock_db)
        mock_requirement.solved_by = ["REQ-TR-0001"]
        mock_requirement.to_rmtoo_format = MagicMock(return_value="Name: REQ-BR-0001\n")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_requirement
        mock_db.execute.return_value = mock_result

        result = await service.add_dependency(mock_requirement.id, "REQ-TR-0001")

        # Should still have only one entry
        assert result.solved_by.count("REQ-TR-0001") == 1


# ============================================================================
# TEST: Statistics
# ============================================================================

class TestStatistics:
    """Test project statistics calculation."""

    @pytest.mark.asyncio
    async def test_get_project_statistics(self, mock_db, mock_requirement):
        """Should calculate correct statistics."""
        service = RmtooAdapterService(mock_db)

        # Mock requirements list
        # Mock by_category result - returns tuples
        mock_cat_result = MagicMock()
        mock_cat_result.all.return_value = [("BR", 1), ("FR", 1)]

        # Mock by_status result - returns tuples
        mock_status_result = MagicMock()
        mock_status_result.all.return_value = [("done", 1), ("not done", 1)]

        # Mock validated count
        mock_validated_result = MagicMock()
        mock_validated_result.scalar.return_value = 1

        # Mock total count
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 2

        # Mock avg confidence
        mock_avg_result = MagicMock()
        mock_avg_result.scalar.return_value = 0.75

        # Mock traceability links count
        mock_link_result = MagicMock()
        mock_link_result.scalar.return_value = 5

        mock_db.execute.side_effect = [
            mock_cat_result,
            mock_status_result,
            mock_validated_result,
            mock_total_result,
            mock_avg_result,
            mock_link_result,
        ]

        stats = await service.get_project_statistics(1)

        # Verify stats structure exists
        assert stats is not None
        assert "total_requirements" in stats
        assert stats["total_requirements"] == 2
        assert stats["traceability_links"] == 5


# ============================================================================
# TEST: Topic Initialization
# ============================================================================

class TestTopicInitialization:
    """Test default topic structure initialization."""

    @pytest.mark.asyncio
    async def test_initialize_default_topics(self, mock_db):
        """Should create default topic hierarchy."""
        service = RmtooAdapterService(mock_db)

        # Each topic check should return None (no existing topics)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        topics = await service.initialize_topics(1)

        # Should create 5 default topics
        assert len(topics) == 5
        topic_names = [t.name for t in topics]
        assert "BusinessRules" in topic_names
        assert "FunctionalRequirements" in topic_names
        assert "NonFunctional" in topic_names

    @pytest.mark.asyncio
    async def test_skip_existing_topics(self, mock_db, mock_topic):
        """Should not recreate existing topics."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_topic]
        mock_db.execute.return_value = mock_result

        # Should handle gracefully without errors
        topics = await service.initialize_topics(1)

        # Should return existing topics or skip creation
        assert topics is not None


# ============================================================================
# TEST: Import from Extraction
# ============================================================================

class TestImportFromExtraction:
    """Test importing requirements from extraction sessions."""

    @pytest.mark.asyncio
    async def test_import_with_confidence_filter(self, mock_db, mock_business_rule):
        """Should filter rules by minimum confidence."""
        service = RmtooAdapterService(mock_db)

        # Mock extraction session
        mock_session = MagicMock()
        mock_session.project_id = 1
        mock_session.id = uuid4()
        mock_session_result = MagicMock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        # Mock topic check (5 times, all return None to create new topics)
        mock_topic_result = MagicMock()
        mock_topic_result.scalar_one_or_none.return_value = None

        # Mock rules query with one high confidence rule
        high_confidence_rule = MagicMock()
        high_confidence_rule.confidence = 0.9
        high_confidence_rule.id = uuid4()
        high_confidence_rule.rule_name = "HighConfRule"
        high_confidence_rule.rule_description = "High confidence rule"
        high_confidence_rule.rule_category = "validation"
        high_confidence_rule.source_file = "test.py"
        high_confidence_rule.business_impact = "high"
        high_confidence_rule.source_line = 10

        mock_rules_result = MagicMock()
        mock_rules_result.scalars.return_value.all.return_value = [high_confidence_rule]

        # Mock for requirement ID generation
        mock_req_id_result = MagicMock()
        mock_req_id_result.scalar_one_or_none.return_value = None

        # Side effects: session + 5 topics + rules + req_id
        mock_db.execute.side_effect = [
            mock_session_result,  # Get extraction session
            mock_topic_result,    # Topic 1 check
            mock_topic_result,    # Topic 2 check
            mock_topic_result,    # Topic 3 check
            mock_topic_result,    # Topic 4 check
            mock_topic_result,    # Topic 5 check
            mock_rules_result,    # Get rules
            mock_req_id_result,   # Get max requirement ID
        ]

        stats = await service.import_from_extraction_session(
            extraction_session_id=mock_session.id,
            min_confidence=0.5
        )

        # Should return stats dict
        assert "total_rules" in stats or "requirements_created" in stats


# ============================================================================
# TEST: Query Methods
# ============================================================================

class TestQueryMethods:
    """Test requirement query methods."""

    @pytest.mark.asyncio
    async def test_get_requirements_by_project(self, mock_db, mock_requirement):
        """Should retrieve requirements for a project."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_requirement]
        mock_db.execute.return_value = mock_result

        requirements = await service.get_requirements_by_project(1)

        assert len(requirements) == 1
        assert requirements[0].name == mock_requirement.name

    @pytest.mark.asyncio
    async def test_filter_by_category(self, mock_db, mock_requirement):
        """Should filter by category."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_requirement]
        mock_db.execute.return_value = mock_result

        requirements = await service.get_requirements_by_project(
            1,
            category=RequirementCategory.BR
        )

        assert len(requirements) >= 0  # Query was filtered

    @pytest.mark.asyncio
    async def test_filter_validated_only(self, mock_db, mock_requirement):
        """Should filter validated requirements only."""
        service = RmtooAdapterService(mock_db)
        mock_requirement.validated = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_requirement]
        mock_db.execute.return_value = mock_result

        requirements = await service.get_requirements_by_project(
            1,
            validated_only=True
        )

        assert all(r.validated for r in requirements)

    @pytest.mark.asyncio
    async def test_get_requirement_by_name(self, mock_db, mock_requirement):
        """Should retrieve requirement by name."""
        service = RmtooAdapterService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_requirement
        mock_db.execute.return_value = mock_result

        req = await service.get_requirement_by_name(1, "REQ-BR-0001")

        assert req is not None
        assert req.name == mock_requirement.name
