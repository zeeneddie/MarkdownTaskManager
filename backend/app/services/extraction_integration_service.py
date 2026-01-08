"""
Extraction Integration Service - Week 84

Integrates hierarchical story extraction into:
1. Project Registration Workflow (onboarding)
2. Kanban/Task Management System (automatic story creation)

This service connects the extraction pipeline with the existing
project management infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.models.hierarchical_extraction import (
    HierarchicalExtractionSession,
    ExtractedStoryItem,
    ExtractionSessionStatus,
    StoryItemType,
    ExtractionLevel,
)
from app.models.item import Item
from app.models.task_hierarchy import Epic, Feature, Story, Task
from app.models.deep_extraction import ExtractionTier
from app.services.hierarchical_story_extraction_service import (
    HierarchicalStoryExtractionService,
    HierarchicalExtractionResult,
    ExtractedStory,
    get_hierarchical_extraction_service,
)
from app.services.kanban_event_service import KanbanEventService, KanbanLane


logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class KanbanImportResult:
    """Result of importing extracted stories to kanban."""
    success: bool
    items_created: int
    epics_created: int
    features_created: int
    stories_created: int
    tasks_created: int
    errors: List[str] = field(default_factory=list)
    kanban_item_ids: List[int] = field(default_factory=list)


@dataclass
class OnboardingExtractionResult:
    """Result of extraction during onboarding."""
    success: bool
    extraction_session_id: str
    stories_extracted: int
    kanban_import_result: Optional[KanbanImportResult]
    tier_used: str
    confidence: float
    duration_ms: int
    errors: List[str] = field(default_factory=list)


# =============================================================================
# EXTRACTION INTEGRATION SERVICE
# =============================================================================

class ExtractionIntegrationService:
    """
    Integrates hierarchical extraction with project management.

    Usage:
        service = ExtractionIntegrationService(db)

        # During project onboarding
        result = await service.extract_and_import(
            project_id=1,
            repository_path="/path/to/repo",
            tier="STANDARD",
            auto_import_to_kanban=True,
        )

        # Manual import to kanban
        await service.import_session_to_kanban(session_id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.extraction_service = get_hierarchical_extraction_service(db)

    async def extract_and_import(
        self,
        project_id: int,
        repository_path: str,
        tier: str = "FREE",
        auto_import_to_kanban: bool = True,
        target_lane: str = "BACKLOG",
        levels: Optional[List[str]] = None,
    ) -> OnboardingExtractionResult:
        """
        Run extraction and optionally import to kanban.

        This is the main entry point for project onboarding.

        Args:
            project_id: Database project ID
            repository_path: Path to repository
            tier: Extraction tier (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)
            auto_import_to_kanban: Whether to import stories to kanban
            target_lane: Initial kanban lane for imported items
            levels: Which levels to extract (default: all)

        Returns:
            OnboardingExtractionResult with extraction and import status
        """
        import time
        start_time = time.time()

        result = OnboardingExtractionResult(
            success=False,
            extraction_session_id="",
            stories_extracted=0,
            kanban_import_result=None,
            tier_used=tier,
            confidence=0.0,
            duration_ms=0,
        )

        try:
            # Parse tier
            try:
                extraction_tier = ExtractionTier(tier.upper())
            except ValueError:
                extraction_tier = ExtractionTier.FREE

            # Parse levels
            level_enums = None
            if levels:
                from app.services.hierarchical_story_extraction_service import ExtractionLevel as SvcLevel
                level_enums = []
                for level in levels:
                    try:
                        level_enums.append(SvcLevel(level))
                    except ValueError:
                        pass

            # Run extraction
            print(f"[DEBUG] Starting hierarchical extraction: project={project_id}, path={repository_path}, tier={extraction_tier}")
            extraction_result = await self.extraction_service.extract_hierarchical(
                project_id=project_id,
                repository_path=repository_path,
                tier=extraction_tier,
                levels=level_enums,
            )
            logger.info(f"Extraction complete: stories={extraction_result.total_stories}, errors={extraction_result.errors}")

            result.extraction_session_id = extraction_result.extraction_id
            result.stories_extracted = extraction_result.total_stories
            result.confidence = extraction_result.overall_confidence
            result.tier_used = extraction_tier.value

            if not extraction_result.is_successful:
                logger.warning(f"Extraction failed: {extraction_result.errors}")
                result.errors.extend(extraction_result.errors)
                return result

            # Store extraction session in database
            await self._store_extraction_session(project_id, extraction_result)

            # Import to kanban if requested
            if auto_import_to_kanban:
                import_result = await self._import_to_kanban(
                    project_id=project_id,
                    extraction_result=extraction_result,
                    target_lane=target_lane,
                )
                result.kanban_import_result = import_result

                if not import_result.success:
                    result.errors.extend(import_result.errors)

            result.success = True

        except Exception as e:
            logger.exception("Extraction integration failed")
            result.errors.append(str(e))

        result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def import_session_to_kanban(
        self,
        session_id: str,
        target_lane: str = "BACKLOG",
        min_confidence: float = 0.5,
    ) -> KanbanImportResult:
        """
        Import an existing extraction session to kanban.

        Args:
            session_id: Extraction session UUID
            target_lane: Initial kanban lane
            min_confidence: Minimum confidence threshold for import

        Returns:
            KanbanImportResult with created items
        """
        result = KanbanImportResult(
            success=False,
            items_created=0,
            epics_created=0,
            features_created=0,
            stories_created=0,
            tasks_created=0,
        )

        try:
            session_uuid = UUID(session_id)

            # Get session
            session_result = await self.db.execute(
                select(HierarchicalExtractionSession)
                .where(HierarchicalExtractionSession.id == session_uuid)
            )
            session = session_result.scalar_one_or_none()

            if not session:
                result.errors.append("Session not found")
                return result

            # Get extracted items
            items_result = await self.db.execute(
                select(ExtractedStoryItem)
                .where(
                    ExtractedStoryItem.session_id == session_uuid,
                    ExtractedStoryItem.confidence >= min_confidence,
                )
            )
            items = items_result.scalars().all()

            # Import items
            for item in items:
                kanban_item = await self._create_kanban_item(
                    project_id=session.project_id,
                    extracted_item=item,
                    target_lane=target_lane,
                )

                if kanban_item:
                    result.items_created += 1
                    result.kanban_item_ids.append(kanban_item.id)

                    if item.item_type == StoryItemType.EPIC:
                        result.epics_created += 1
                    elif item.item_type == StoryItemType.FEATURE:
                        result.features_created += 1
                    elif item.item_type == StoryItemType.STORY:
                        result.stories_created += 1
                    elif item.item_type == StoryItemType.TASK:
                        result.tasks_created += 1

            await self.db.commit()
            result.success = True

        except Exception as e:
            logger.exception("Kanban import failed")
            result.errors.append(str(e))

        return result

    async def _store_extraction_session(
        self,
        project_id: int,
        result: HierarchicalExtractionResult,
    ):
        """Store extraction session to database."""
        session = HierarchicalExtractionSession(
            id=UUID(result.extraction_id),
            project_id=project_id,
            repository_path=result.repository_path,
            tier=result.tier.value,
            primary_stack=result.primary_stack,
            status=ExtractionSessionStatus.COMPLETED,
            total_epics=result.total_epics,
            total_features=result.total_features,
            total_stories=result.total_stories,
            total_tasks=result.total_tasks,
            overall_confidence=result.overall_confidence,
            total_tokens=result.total_tokens,
            total_cost_usd=result.total_cost_usd,
            duration_ms=result.total_duration_ms,
            started_at=result.started_at,
            completed_at=result.completed_at,
            errors=result.errors,
        )

        self.db.add(session)

        # Store individual items
        await self._store_extracted_items(session.id, result)

        await self.db.commit()

    async def _store_extracted_items(
        self,
        session_id: UUID,
        result: HierarchicalExtractionResult,
    ):
        """Store extracted items to database."""
        for level_result in [
            result.function_level,
            result.class_level,
            result.module_level,
            result.system_level,
        ]:
            if not level_result:
                continue

            for story in level_result.stories + level_result.features + level_result.epics:
                item = ExtractedStoryItem(
                    id=UUID(story.id),
                    session_id=session_id,
                    item_type=StoryItemType(story.item_type.value),
                    extraction_level=ExtractionLevel(story.level.value),
                    title=story.title,
                    description=story.description,
                    acceptance_criteria=story.acceptance_criteria,
                    source_file=story.source_file,
                    source_symbol=story.source_symbol,
                    confidence=story.confidence,
                    complexity=story.complexity,
                    tags=story.tags,
                    story_points=story.story_points,
                    function_points=story.function_points,
                    extracted_by=story.extracted_by,
                )
                self.db.add(item)

    async def _import_to_kanban(
        self,
        project_id: int,
        extraction_result: HierarchicalExtractionResult,
        target_lane: str,
    ) -> KanbanImportResult:
        """Import extraction result to kanban."""
        result = KanbanImportResult(
            success=False,
            items_created=0,
            epics_created=0,
            features_created=0,
            stories_created=0,
            tasks_created=0,
        )

        try:
            # Collect all stories from all levels
            all_items: List[ExtractedStory] = []

            for level_result in [
                extraction_result.function_level,
                extraction_result.class_level,
                extraction_result.module_level,
                extraction_result.system_level,
            ]:
                if level_result:
                    all_items.extend(level_result.epics)
                    all_items.extend(level_result.features)
                    all_items.extend(level_result.stories)
                    all_items.extend(level_result.tasks)

            # Create kanban items
            for item in all_items:
                kanban_item = await self._create_kanban_item_from_story(
                    project_id=project_id,
                    story=item,
                    target_lane=target_lane,
                )

                if kanban_item:
                    result.items_created += 1
                    result.kanban_item_ids.append(kanban_item.id)

                    if item.item_type.value == "epic":
                        result.epics_created += 1
                    elif item.item_type.value == "feature":
                        result.features_created += 1
                    elif item.item_type.value == "story":
                        result.stories_created += 1
                    elif item.item_type.value == "task":
                        result.tasks_created += 1

            await self.db.commit()
            result.success = True

        except Exception as e:
            logger.exception("Import to kanban failed")
            result.errors.append(str(e))

        return result

    async def _create_kanban_item(
        self,
        project_id: int,
        extracted_item: ExtractedStoryItem,
        target_lane: str,
    ) -> Optional[Item]:
        """Create a kanban Item from an extracted item."""
        try:
            # Map confidence to priority
            priority = self._map_confidence_to_priority(extracted_item.confidence)

            # Create Item (base kanban item)
            item = Item(
                id=str(uuid4()),
                title=extracted_item.title,
                description=extracted_item.description or "",
                type=extracted_item.item_type.value,
                status=target_lane.lower(),
                priority=priority,
                lane=target_lane,
                tags=",".join(extracted_item.tags or []),
                sp=extracted_item.story_points,
                source_extraction_id=str(extracted_item.session_id),
            )

            self.db.add(item)
            await self.db.flush()

            return item

        except Exception as e:
            logger.warning(f"Failed to create kanban item: {e}")
            return None

    async def _create_kanban_item_from_story(
        self,
        project_id: int,
        story: ExtractedStory,
        target_lane: str,
    ) -> Optional[Item]:
        """Create a kanban Item from an ExtractedStory."""
        try:
            priority = self._map_confidence_to_priority(story.confidence)

            item = Item(
                id=str(uuid4()),
                title=story.title,
                description=story.description or "",
                type=story.item_type.value,
                status=target_lane.lower(),
                priority=priority,
                lane=target_lane,
                tags=",".join(story.tags or []),
                sp=story.story_points,
            )

            self.db.add(item)
            await self.db.flush()

            return item

        except Exception as e:
            logger.warning(f"Failed to create kanban item from story: {e}")
            return None

    def _map_confidence_to_priority(self, confidence: float) -> str:
        """Map extraction confidence to priority."""
        if confidence >= 0.9:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        return "low"


# =============================================================================
# ONBOARDING WORKFLOW INTEGRATION
# =============================================================================

class OnboardingWorkflowIntegration:
    """
    Integrates extraction into the project onboarding workflow.

    This class hooks into the project registration flow to
    automatically extract stories when a new project is registered.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.integration_service = ExtractionIntegrationService(db)

    async def on_project_registered(
        self,
        project_id: int,
        repository_path: str,
        tier: str = "FREE",
        auto_extract: bool = True,
        auto_import: bool = True,
    ) -> Optional[OnboardingExtractionResult]:
        """
        Called when a project is registered.

        This is the hook for the project registration workflow.

        Args:
            project_id: Newly registered project ID
            repository_path: Path to the repository
            tier: Extraction tier
            auto_extract: Whether to run extraction
            auto_import: Whether to import to kanban

        Returns:
            Extraction result if auto_extract is True
        """
        if not auto_extract:
            return None

        logger.info(f"Starting extraction for project {project_id}")

        result = await self.integration_service.extract_and_import(
            project_id=project_id,
            repository_path=repository_path,
            tier=tier,
            auto_import_to_kanban=auto_import,
            target_lane="BACKLOG",
        )

        if result.success:
            logger.info(
                f"Extraction complete for project {project_id}: "
                f"{result.stories_extracted} stories extracted"
            )
        else:
            logger.warning(
                f"Extraction failed for project {project_id}: "
                f"{result.errors}"
            )

        return result


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_extraction_integration_service(db: AsyncSession) -> ExtractionIntegrationService:
    """Factory function for ExtractionIntegrationService."""
    return ExtractionIntegrationService(db)


def get_onboarding_integration(db: AsyncSession) -> OnboardingWorkflowIntegration:
    """Factory function for OnboardingWorkflowIntegration."""
    return OnboardingWorkflowIntegration(db)
