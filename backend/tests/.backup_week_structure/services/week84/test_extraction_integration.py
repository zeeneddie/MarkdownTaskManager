"""
Tests for Extraction Integration Service - Week 84

Tests:
- ExtractionIntegrationService
- OnboardingWorkflowIntegration
- Kanban import functionality
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.services.extraction_integration_service import (
    ExtractionIntegrationService,
    OnboardingWorkflowIntegration,
    KanbanImportResult,
    OnboardingExtractionResult,
    get_extraction_integration_service,
    get_onboarding_integration,
)


class TestKanbanImportResult:
    """Tests for KanbanImportResult dataclass."""

    def test_create_empty_result(self):
        """Should create result with defaults."""
        result = KanbanImportResult(
            success=False,
            items_created=0,
            epics_created=0,
            features_created=0,
            stories_created=0,
            tasks_created=0,
        )

        assert result.success is False
        assert result.items_created == 0
        assert result.errors == []
        assert result.kanban_item_ids == []

    def test_create_successful_result(self):
        """Should create successful result with counts."""
        result = KanbanImportResult(
            success=True,
            items_created=10,
            epics_created=2,
            features_created=3,
            stories_created=4,
            tasks_created=1,
            kanban_item_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        )

        assert result.success is True
        assert result.items_created == 10
        assert result.epics_created == 2
        assert result.features_created == 3
        assert result.stories_created == 4
        assert result.tasks_created == 1
        assert len(result.kanban_item_ids) == 10


class TestOnboardingExtractionResult:
    """Tests for OnboardingExtractionResult dataclass."""

    def test_create_empty_result(self):
        """Should create result with defaults."""
        result = OnboardingExtractionResult(
            success=False,
            extraction_session_id="",
            stories_extracted=0,
            kanban_import_result=None,
            tier_used="FREE",
            confidence=0.0,
            duration_ms=0,
        )

        assert result.success is False
        assert result.stories_extracted == 0
        assert result.kanban_import_result is None
        assert result.errors == []

    def test_create_successful_result(self):
        """Should create successful result."""
        kanban_result = KanbanImportResult(
            success=True,
            items_created=5,
            epics_created=1,
            features_created=2,
            stories_created=2,
            tasks_created=0,
        )

        result = OnboardingExtractionResult(
            success=True,
            extraction_session_id=str(uuid4()),
            stories_extracted=5,
            kanban_import_result=kanban_result,
            tier_used="STANDARD",
            confidence=0.82,
            duration_ms=1500,
        )

        assert result.success is True
        assert result.stories_extracted == 5
        assert result.kanban_import_result.items_created == 5
        assert result.confidence == 0.82


class TestExtractionIntegrationService:
    """Tests for ExtractionIntegrationService."""

    def test_init_service(self):
        """Should initialize service."""
        mock_db = Mock()
        service = ExtractionIntegrationService(mock_db)

        assert service.db == mock_db
        assert service.extraction_service is not None

    @pytest.mark.asyncio
    async def test_extract_and_import_invalid_tier(self):
        """Should handle invalid tier gracefully."""
        mock_db = Mock()
        service = ExtractionIntegrationService(mock_db)

        # Mock extraction service
        service.extraction_service.extract_hierarchical = AsyncMock(return_value=Mock(
            extraction_id=str(uuid4()),
            total_stories=5,
            overall_confidence=0.75,
            is_successful=True,
            tier=Mock(value="FREE"),
            repository_path="/test",
            primary_stack="python",
            total_epics=1,
            total_features=2,
            total_tasks=0,
            total_tokens=1000,
            total_cost_usd=0.0,
            total_duration_ms=500,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            errors=[],
            function_level=None,
            class_level=None,
            module_level=None,
            system_level=None,
        ))

        result = await service.extract_and_import(
            project_id=1,
            repository_path="/test/path",
            tier="INVALID_TIER",  # Invalid tier
            auto_import_to_kanban=False,
        )

        # Should default to FREE tier
        assert result.tier_used == "FREE"

    def test_map_confidence_to_priority_high(self):
        """Should map high confidence to high priority."""
        mock_db = Mock()
        service = ExtractionIntegrationService(mock_db)

        assert service._map_confidence_to_priority(0.9) == "high"
        assert service._map_confidence_to_priority(0.95) == "high"
        assert service._map_confidence_to_priority(1.0) == "high"

    def test_map_confidence_to_priority_medium(self):
        """Should map medium confidence to medium priority."""
        mock_db = Mock()
        service = ExtractionIntegrationService(mock_db)

        assert service._map_confidence_to_priority(0.7) == "medium"
        assert service._map_confidence_to_priority(0.8) == "medium"
        assert service._map_confidence_to_priority(0.89) == "medium"

    def test_map_confidence_to_priority_low(self):
        """Should map low confidence to low priority."""
        mock_db = Mock()
        service = ExtractionIntegrationService(mock_db)

        assert service._map_confidence_to_priority(0.5) == "low"
        assert service._map_confidence_to_priority(0.69) == "low"
        assert service._map_confidence_to_priority(0.0) == "low"


class TestOnboardingWorkflowIntegration:
    """Tests for OnboardingWorkflowIntegration."""

    def test_init_integration(self):
        """Should initialize integration."""
        mock_db = Mock()
        integration = OnboardingWorkflowIntegration(mock_db)

        assert integration.db == mock_db
        assert integration.integration_service is not None

    @pytest.mark.asyncio
    async def test_on_project_registered_no_extraction(self):
        """Should return None when auto_extract is False."""
        mock_db = Mock()
        integration = OnboardingWorkflowIntegration(mock_db)

        result = await integration.on_project_registered(
            project_id=1,
            repository_path="/test",
            auto_extract=False,
        )

        assert result is None


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_extraction_integration_service(self):
        """Should create service via factory."""
        mock_db = Mock()
        service = get_extraction_integration_service(mock_db)

        assert isinstance(service, ExtractionIntegrationService)

    def test_get_onboarding_integration(self):
        """Should create integration via factory."""
        mock_db = Mock()
        integration = get_onboarding_integration(mock_db)

        assert isinstance(integration, OnboardingWorkflowIntegration)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
