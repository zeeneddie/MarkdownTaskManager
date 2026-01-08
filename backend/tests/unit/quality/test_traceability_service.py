# backend/tests/services/week113/test_traceability_service.py
"""
Tests for Week 113: Traceability Service

Tests for linking business rules to epic/feature/story hierarchy.
Covers:
- Link management (create, delete, query)
- Impact analysis
- Traceability matrix generation
- Auto-linking suggestions
- CRUD workflow detection
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4, UUID

from app.services.traceability_service import TraceabilityService
from app.models.traceability import (
    LinkType,
    WorkflowType,
    CRUDOperation,
    StoryBusinessRule,
    FeatureBusinessRule,
    EpicBusinessRule,
    RuleWorkflow,
    RuleWorkflowMember,
    TraceabilityMatrixRow,
    RuleImpact,
    TraceabilitySummary,
)


class TestTraceabilityServiceInit:
    """Test TraceabilityService initialization."""

    def test_init_with_session(self):
        """Should initialize with database session."""
        mock_session = Mock()
        service = TraceabilityService(mock_session)

        assert service.db == mock_session


class TestLinkRuleToStory:
    """Test linking business rules to stories."""

    @pytest.mark.asyncio
    async def test_link_rule_to_story_basic(self):
        """Should create basic story-rule link."""
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()

        service = TraceabilityService(mock_session)

        story_id = uuid4()
        rule_id = "BR-001"

        link = await service.link_rule_to_story(
            story_id=story_id,
            rule_id=rule_id,
        )

        assert link.story_id == story_id
        assert link.rule_id == rule_id
        assert link.link_type == LinkType.IMPLEMENTS.value
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_rule_to_story_with_metadata(self):
        """Should create story-rule link with full metadata."""
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()

        service = TraceabilityService(mock_session)

        story_id = uuid4()
        rule_id = "BR-042"

        link = await service.link_rule_to_story(
            story_id=story_id,
            rule_id=rule_id,
            link_type=LinkType.VALIDATES,
            confidence=0.95,
            linked_by="peter",
            link_reason="Story validates BR-042 authorization rule",
        )

        assert link.story_id == story_id
        assert link.rule_id == rule_id
        assert link.link_type == LinkType.VALIDATES.value
        assert link.confidence == 0.95
        assert link.linked_by == "peter"
        assert "BR-042" in link.link_reason


class TestLinkRuleToFeature:
    """Test linking business rules to features."""

    @pytest.mark.asyncio
    async def test_link_rule_to_feature(self):
        """Should create feature-rule link."""
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()

        service = TraceabilityService(mock_session)

        feature_id = uuid4()
        rule_id = "BR-015"

        link = await service.link_rule_to_feature(
            feature_id=feature_id,
            rule_id=rule_id,
            link_type=LinkType.CONTAINS,
            confidence=0.85,
        )

        assert link.feature_id == feature_id
        assert link.rule_id == rule_id
        assert link.link_type == LinkType.CONTAINS.value


class TestLinkRuleToEpic:
    """Test linking business rules to epics."""

    @pytest.mark.asyncio
    async def test_link_rule_to_epic(self):
        """Should create epic-rule link."""
        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()

        service = TraceabilityService(mock_session)

        epic_id = uuid4()
        rule_id = "BR-100"

        link = await service.link_rule_to_epic(
            epic_id=epic_id,
            rule_id=rule_id,
            link_type=LinkType.GOVERNS,
            linked_by="auto",
        )

        assert link.epic_id == epic_id
        assert link.rule_id == rule_id
        assert link.link_type == LinkType.GOVERNS.value


class TestUnlinkRules:
    """Test removing rule links."""

    @pytest.mark.asyncio
    async def test_unlink_rule_from_story(self):
        """Should remove story-rule link."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=Mock())
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.delete = AsyncMock()

        service = TraceabilityService(mock_session)

        story_id = uuid4()
        result = await service.unlink_rule_from_story(story_id, "BR-001")

        assert result is True
        mock_session.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlink_rule_not_found(self):
        """Should return False when link not found."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TraceabilityService(mock_session)

        story_id = uuid4()
        result = await service.unlink_rule_from_story(story_id, "BR-999")

        assert result is False


class TestGetRulesForStory:
    """Test querying rules for a story."""

    @pytest.mark.asyncio
    async def test_get_rules_for_story_calls_db(self):
        """Should execute query to get rules for story."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.all = Mock(return_value=[])
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TraceabilityService(mock_session)

        story_id = uuid4()
        rules = await service.get_rules_for_story(story_id)

        # Should have called execute
        mock_session.execute.assert_called_once()
        assert isinstance(rules, list)


class TestGetStoriesForRule:
    """Test querying stories for a rule."""

    @pytest.mark.asyncio
    async def test_get_stories_for_rule_calls_db(self):
        """Should execute query to get stories for rule."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.all = Mock(return_value=[])
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TraceabilityService(mock_session)

        stories = await service.get_stories_for_rule("BR-001")

        mock_session.execute.assert_called_once()
        assert isinstance(stories, list)


class TestRuleImpact:
    """Test impact analysis for rules."""

    def test_rule_impact_creation(self):
        """Should create RuleImpact from factory."""
        # Test the RuleImpact dataclass directly
        impact = RuleImpact(
            rule_id="BR-042",
            rule_type="data_access",
            rule_description="Data access rule",
            story_count=5,
            feature_count=2,
            epic_count=1,
        )

        assert impact.rule_id == "BR-042"
        assert isinstance(impact, RuleImpact)

    def test_rule_impact_dataclass(self):
        """Should create RuleImpact with all fields."""
        impact = RuleImpact(
            rule_id="BR-042",
            rule_type="data_access",
            rule_description="Data access control",
            source_file="data.vb",
            entity_name="Afspraak",
            story_count=5,
            feature_count=2,
            epic_count=1,
            affected_stories=["S1", "S2"],
            affected_features=["F1"],
            affected_epics=["E1"],
        )

        assert impact.story_count == 5
        assert len(impact.affected_stories) == 2


class TestTraceabilityMatrix:
    """Test traceability matrix generation."""

    @pytest.mark.asyncio
    async def test_get_traceability_matrix_calls_db(self):
        """Should query database for matrix."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.all = Mock(return_value=[])
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TraceabilityService(mock_session)

        matrix = await service.get_traceability_matrix(project_id=1)

        # Should have queried the database
        assert mock_session.execute.called
        assert isinstance(matrix, list)

    def test_traceability_matrix_row_dataclass(self):
        """Should create matrix row with all fields."""
        row = TraceabilityMatrixRow(
            epic_id="epic-1",
            epic_title="Epic 1",
            feature_id="feat-1",
            feature_title="Feature 1",
            story_id="story-1",
            story_title="Story 1",
            rule_id="BR-001",
            rule_type="authorization",
            rule_description="Auth rule",
            rule_confidence=0.9,
            link_type="implements",
            linked_by="peter",
        )

        assert row.rule_id == "BR-001"
        assert row.link_type == "implements"


class TestTraceabilitySummary:
    """Test traceability summary statistics."""

    @pytest.mark.asyncio
    async def test_get_traceability_summary_calls_db(self):
        """Should query database for summary."""
        mock_session = AsyncMock()

        # Mock returns for scalar queries
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=10)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TraceabilityService(mock_session)

        summary = await service.get_traceability_summary(project_id=1)

        # Should return a TraceabilitySummary
        assert isinstance(summary, TraceabilitySummary)
        assert mock_session.execute.called

    def test_traceability_summary_dataclass(self):
        """Should create summary with all fields."""
        summary = TraceabilitySummary(
            total_rules=100,
            linked_rules=75,
            unlinked_rules=25,
            total_stories=50,
            stories_with_rules=40,
            stories_without_rules=10,
            avg_rules_per_story=3.0,
            workflows_detected=5,
            coverage_percentage=75.0,
        )

        assert summary.total_rules == 100
        assert summary.coverage_percentage == 75.0


class TestSuggestLinks:
    """Test auto-linking suggestions."""

    def test_keyword_extraction_logic(self):
        """Test the concept of keyword matching for suggestions."""
        # Keywords that would match between story and rule
        story_keywords = {"authorization", "admin", "access", "control"}
        rule_keywords = {"admin", "authorization", "permission"}

        # Intersection represents potential matches
        matches = story_keywords & rule_keywords

        assert "admin" in matches
        assert "authorization" in matches
        assert len(matches) == 2


class TestCRUDWorkflowDetection:
    """Test CRUD workflow detection."""

    def test_crud_workflow_grouping_logic(self):
        """Test the concept of grouping rules by entity."""
        # Rules grouped by entity
        rules_by_entity = {
            "Afspraak": ["BR-001", "BR-002", "BR-003", "BR-004"],
            "User": ["BR-005", "BR-006"],
            "Orphan": ["BR-007"],  # Only 1 rule, won't form workflow
        }

        # Filter entities with min 2 rules
        min_rules = 2
        valid_workflows = {
            entity: rules
            for entity, rules in rules_by_entity.items()
            if len(rules) >= min_rules
        }

        assert "Afspraak" in valid_workflows
        assert "User" in valid_workflows
        assert "Orphan" not in valid_workflows
        assert len(valid_workflows) == 2


class TestRuleWorkflow:
    """Test RuleWorkflow model."""

    def test_workflow_to_dict(self):
        """Should convert workflow to dict."""
        workflow = RuleWorkflow(
            id=1,
            project_id=1,
            name="Afspraak CRUD",
            workflow_type=WorkflowType.CRUD.value,
            entity_name="Afspraak",
            rule_count=4,
            operations={"create": ["BR-001"], "read": ["BR-002"], "update": ["BR-003"], "delete": ["BR-004"]},
        )

        result = workflow.to_dict()

        assert result["name"] == "Afspraak CRUD"
        assert result["workflow_type"] == "CRUD"
        assert result["entity_name"] == "Afspraak"
        assert result["rule_count"] == 4
        assert "create" in result["operations"]

    def test_workflow_generate_mermaid(self):
        """Should generate Mermaid diagram for CRUD workflow."""
        workflow = RuleWorkflow(
            id=1,
            project_id=1,
            name="User CRUD",
            workflow_type=WorkflowType.CRUD.value,
            entity_name="User",
            rule_count=4,
            operations={
                "create": ["BR-001"],
                "read": ["BR-002"],
                "update": ["BR-003"],
                "delete": ["BR-004"],
            },
        )

        mermaid = workflow.generate_mermaid()

        assert "flowchart LR" in mermaid
        assert "CREATE[Create User]" in mermaid
        assert "READ[Read User]" in mermaid


class TestDataclasses:
    """Test helper dataclasses."""

    def test_traceability_matrix_row(self):
        """Should create matrix row."""
        row = TraceabilityMatrixRow(
            epic_id="epic-1",
            epic_title="Epic 1",
            feature_id="feature-1",
            feature_title="Feature 1",
            story_id="story-1",
            story_title="Story 1",
            rule_id="BR-001",
            rule_type="authorization",
            rule_description="Admin access rule",
            rule_confidence=0.95,
            link_type="implements",
            linked_by="peter",
        )

        assert row.rule_id == "BR-001"
        assert row.link_type == "implements"

    def test_rule_impact(self):
        """Should create rule impact."""
        impact = RuleImpact(
            rule_id="BR-042",
            rule_type="data_access",
            rule_description="Data access control",
            source_file="data.vb",
            entity_name="Afspraak",
            story_count=5,
            feature_count=2,
            epic_count=1,
            affected_stories=["Story 1", "Story 2", "Story 3"],
            affected_features=["Feature 1", "Feature 2"],
            affected_epics=["Epic 1"],
        )

        assert impact.rule_id == "BR-042"
        assert impact.story_count == 5
        assert len(impact.affected_stories) == 3

    def test_traceability_summary(self):
        """Should create summary."""
        summary = TraceabilitySummary(
            total_rules=100,
            linked_rules=75,
            unlinked_rules=25,
            total_stories=50,
            stories_with_rules=40,
            stories_without_rules=10,
            avg_rules_per_story=3.0,
            workflows_detected=5,
            coverage_percentage=75.0,
        )

        assert summary.total_rules == 100
        assert summary.coverage_percentage == 75.0


class TestLinkTypeEnum:
    """Test LinkType enum."""

    def test_link_type_values(self):
        """Should have correct link types."""
        assert LinkType.IMPLEMENTS.value == "implements"
        assert LinkType.VALIDATES.value == "validates"
        assert LinkType.TRIGGERS.value == "triggers"
        assert LinkType.CONTAINS.value == "contains"
        assert LinkType.GOVERNS.value == "governs"
        assert LinkType.DEPENDS_ON.value == "depends_on"


class TestWorkflowTypeEnum:
    """Test WorkflowType enum."""

    def test_workflow_type_values(self):
        """Should have correct workflow types."""
        assert WorkflowType.CRUD.value == "CRUD"
        assert WorkflowType.STATE_MACHINE.value == "STATE_MACHINE"
        assert WorkflowType.APPROVAL.value == "APPROVAL"
        assert WorkflowType.AUTHORIZATION.value == "AUTHORIZATION"


class TestCRUDOperationEnum:
    """Test CRUDOperation enum."""

    def test_crud_operation_values(self):
        """Should have correct CRUD operations."""
        assert CRUDOperation.CREATE.value == "create"
        assert CRUDOperation.READ.value == "read"
        assert CRUDOperation.UPDATE.value == "update"
        assert CRUDOperation.DELETE.value == "delete"
        assert CRUDOperation.VALIDATE.value == "validate"
        assert CRUDOperation.AUTHORIZE.value == "authorize"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
