"""
Task Generation Service

Breaks down approved HLD specifications into hierarchical work items:
Specification → Epic → Feature → Story → Task

Felix agent (Feature Architect) performs the breakdown with intelligent
estimation and dependency mapping.

Includes Vector DB Integration for context-aware task generation.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.green_paper import Specification, SpecificationStatus
from app.models.task_hierarchy import (
    Epic, Feature, Story, Task,
    EpicStatus, FeatureStatus, StoryStatus, TaskStatus,
    Priority
)
from app.services.agent_service import AgentService
from app.services.task_generation.validation_service import HierarchyValidationService

# Week 143: Vector DB Integration
logger = logging.getLogger(__name__)

try:
    from app.services.chroma_service import ChromaService
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaService not available - Vector DB context disabled for task generation")


class TaskGenerationService:
    """Service for generating task hierarchies from specifications."""

    def __init__(
        self,
        db: AsyncSession,
        agent_service: AgentService,
        project_id: int = 1000  # Week 143: Default to HCI-CRS for Vector DB
    ):
        self.db = db
        self.agent_service = agent_service
        self.validation_service = HierarchyValidationService(db)
        self.project_id = project_id

        # Week 143: Vector DB service (lazy initialization)
        self._chroma_service: Optional["ChromaService"] = None

    def _get_chroma_service(self) -> Optional["ChromaService"]:
        """Get or create ChromaDB service instance (lazy init)."""
        if not CHROMA_AVAILABLE:
            return None
        if self._chroma_service is None:
            try:
                self._chroma_service = ChromaService()
                logger.info("ChromaDB service initialized for TaskGenerationService")
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}. Vector context disabled.")
                return None
        return self._chroma_service

    def _fetch_generation_context(
        self,
        context_type: str,  # "epic", "feature", "story", "task"
        topics: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch relevant context from Vector DB for task generation.

        Args:
            context_type: Type of work item being generated
            topics: Optional list of topics to search for

        Returns:
            Dict with implementation patterns, technical details, and examples
        """
        chroma = self._get_chroma_service()
        if not chroma:
            return None

        try:
            context = {
                "implementation_patterns": [],
                "technical_details": [],
                "similar_work_items": [],
                "estimation_guidance": []
            }

            # Build queries based on context type
            queries = []
            if context_type == "epic":
                queries = ["epic breakdown patterns", "user value stories", "business requirements"]
            elif context_type == "feature":
                queries = ["feature implementation", "API design patterns", "database design"]
            elif context_type == "story":
                queries = ["user story examples", "acceptance criteria", "story points estimation"]
            elif context_type == "task":
                queries = ["task breakdown", "implementation details", "technical tasks"]

            # Add topic-specific queries
            if topics:
                for topic in topics[:3]:
                    queries.append(f"{topic} implementation")

            # Fetch from Vector DB
            for query in queries[:5]:
                results = chroma.query_project_knowledge(
                    project_id=self.project_id,
                    query=query,
                    n_results=3
                )

                if results and "documents" in results:
                    for doc in results.get("documents", [[]])[0]:
                        if doc and len(doc) > 50:
                            doc_lower = doc.lower()
                            if any(x in doc_lower for x in ["pattern", "implementation", "approach"]):
                                if doc not in context["implementation_patterns"]:
                                    context["implementation_patterns"].append(doc[:400])
                            elif any(x in doc_lower for x in ["api", "database", "service", "technical"]):
                                if doc not in context["technical_details"]:
                                    context["technical_details"].append(doc[:400])
                            elif any(x in doc_lower for x in ["estimate", "point", "hour"]):
                                if doc not in context["estimation_guidance"]:
                                    context["estimation_guidance"].append(doc[:400])

            # Limit results
            for key in context:
                context[key] = context[key][:3]

            total_items = sum(len(v) for v in context.values())
            if total_items > 0:
                logger.info(f"Fetched {total_items} context items for {context_type} generation")
                return context

            return None

        except Exception as e:
            logger.warning(f"Error fetching generation context: {e}")
            return None

    def get_vector_context_for_type(self, context_type: str) -> Optional[Dict[str, Any]]:
        """Public method to get Vector DB context for a specific generation type."""
        return self._fetch_generation_context(context_type)

    # ========== Epic Generation ==========

    async def generate_epics_from_specification(
        self,
        specification_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate epics from an approved specification.

        Args:
            specification_id: The specification UUID
            options: Generation options (e.g., max_epics, focus_areas)

        Returns:
            Dict with generated epics and statistics

        Raises:
            ValueError: If specification not found or not approved
        """
        # Validate specification exists and is approved
        result = await self.db.execute(
            select(Specification).where(Specification.id == specification_id)
        )
        specification = result.scalar_one_or_none()

        if not specification:
            raise ValueError(f"Specification {specification_id} not found")

        if specification.status != SpecificationStatus.APPROVED:
            raise ValueError(
                f"Specification must be approved before generating epics. "
                f"Current status: {specification.status}"
            )

        # Check if epics already exist
        result = await self.db.execute(
            select(func.count(Epic.id)).where(Epic.specification_id == specification_id)
        )
        existing_count = result.scalar()

        if existing_count > 0:
            raise ValueError(
                f"Epics already exist for specification {specification_id}. "
                f"Use regenerate_epics() to recreate them."
            )

        # Validate epic creation with max_epics option
        max_epics = options.get("max_epics", 7) if options else 7
        is_valid, error_msg = await self.validation_service.validate_epic_creation(
            specification_id=str(specification_id),
            num_epics_to_create=max_epics
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Call Felix agent to generate epics
        felix_response = await self._call_felix_for_epics(
            specification=specification,
            options=options or {}
        )

        # Create epic records
        epics = []
        for idx, epic_data in enumerate(felix_response["epics"], start=1):
            # Validate epic data
            validation_errors = await self.validation_service.validate_epic_data(epic_data)
            if validation_errors:
                raise ValueError(f"Epic {idx} validation failed: {', '.join(validation_errors)}")

            epic = Epic(
                specification_id=specification_id,
                project_id=specification.project_id,
                title=epic_data["title"],
                description=epic_data["description"],
                status=EpicStatus.DRAFT,
                priority=epic_data.get("priority", Priority.MEDIUM),
                business_value=epic_data.get("business_value"),
                user_personas=epic_data.get("user_personas", []),
                acceptance_criteria=epic_data.get("acceptance_criteria", []),
                estimated_story_points=epic_data.get("estimated_story_points"),
                estimated_weeks=epic_data.get("estimated_weeks"),
                sequence_number=idx,
                generated_by="Felix",
                generation_prompt=felix_response.get("prompt_used"),
                generation_metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "specification_title": specification.content_json.get("title"),
                    "generation_version": "1.0"
                }
            )

            self.db.add(epic)
            epics.append(epic)

        await self.db.commit()

        # Refresh to get IDs
        for epic in epics:
            await self.db.refresh(epic)

        return {
            "specification_id": str(specification_id),
            "epics_generated": len(epics),
            "epics": [
                {
                    "id": str(epic.id),
                    "title": epic.title,
                    "description": epic.description,
                    "priority": epic.priority,
                    "estimated_story_points": epic.estimated_story_points,
                    "estimated_weeks": epic.estimated_weeks,
                    "sequence_number": epic.sequence_number
                }
                for epic in epics
            ],
            "next_step": "generate_features"
        }

    async def _call_felix_for_epics(
        self,
        specification: Specification,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call Felix agent to break down specification into epics."""

        # Prepare specification data for Felix
        spec_data = {
            "id": str(specification.id),
            "project_id": specification.project_id,
            "content_json": specification.content_json,
            "content_markdown": specification.content_markdown
        }

        # Call Felix via agent service
        result = await self.agent_service.generate_epics_from_specification(
            specification=spec_data,
            project_id=specification.project_id,
            options=options
        )

        return result

    # ========== Feature Generation ==========

    async def generate_features_from_epic(
        self,
        epic_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate features from an epic.

        Args:
            epic_id: The epic UUID
            options: Generation options

        Returns:
            Dict with generated features and statistics
        """
        # Validate epic exists
        result = await self.db.execute(
            select(Epic).where(Epic.id == epic_id)
        )
        epic = result.scalar_one_or_none()

        if not epic:
            raise ValueError(f"Epic {epic_id} not found")

        # Check if features already exist
        result = await self.db.execute(
            select(func.count(Feature.id)).where(Feature.epic_id == epic_id)
        )
        existing_count = result.scalar()

        if existing_count > 0:
            raise ValueError(
                f"Features already exist for epic {epic_id}. "
                f"Use regenerate_features() to recreate them."
            )

        # Validate feature creation with max_features option
        max_features = options.get("max_features", 10) if options else 10
        is_valid, error_msg = await self.validation_service.validate_feature_creation(
            epic_id=str(epic_id),
            num_features_to_create=max_features
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Call Felix agent to generate features
        felix_response = await self._call_felix_for_features(
            epic=epic,
            options=options or {}
        )

        # Create feature records
        features = []
        for idx, feature_data in enumerate(felix_response["features"], start=1):
            # Validate feature data
            validation_errors = await self.validation_service.validate_feature_data(feature_data)
            if validation_errors:
                raise ValueError(f"Feature {idx} validation failed: {', '.join(validation_errors)}")

            feature = Feature(
                epic_id=epic_id,
                project_id=epic.project_id,
                title=feature_data["title"],
                description=feature_data["description"],
                status=FeatureStatus.DRAFT,
                priority=feature_data.get("priority", Priority.MEDIUM),
                technical_approach=feature_data.get("technical_approach"),
                api_endpoints=feature_data.get("api_endpoints", []),
                database_changes=feature_data.get("database_changes", []),
                dependencies=feature_data.get("dependencies", []),
                estimated_story_points=feature_data.get("estimated_story_points"),
                estimated_days=feature_data.get("estimated_days"),
                complexity=feature_data.get("complexity", "moderate"),
                sequence_number=idx,
                generated_by="Felix",
                generation_metadata={
                    "epic_title": epic.title,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )

            self.db.add(feature)
            features.append(feature)

        await self.db.commit()

        for feature in features:
            await self.db.refresh(feature)

        return {
            "epic_id": str(epic_id),
            "features_generated": len(features),
            "features": [
                {
                    "id": str(feature.id),
                    "title": feature.title,
                    "description": feature.description,
                    "complexity": feature.complexity,
                    "estimated_story_points": feature.estimated_story_points
                }
                for feature in features
            ],
            "next_step": "generate_stories"
        }

    async def _call_felix_for_features(
        self,
        epic: Epic,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call Felix agent to break down epic into features."""

        # Prepare epic data for Felix
        epic_data = {
            "id": str(epic.id),
            "title": epic.title,
            "description": epic.description,
            "business_value": epic.business_value,
            "user_personas": epic.user_personas,
            "acceptance_criteria": epic.acceptance_criteria
        }

        # Get specification context if available
        specification_context = None
        if epic.specification_id:
            result = await self.db.execute(
                select(Specification).where(Specification.id == epic.specification_id)
            )
            spec = result.scalar_one_or_none()
            if spec:
                specification_context = {
                    "title": spec.content_json.get("title"),
                    "architecture": spec.content_json.get("architecture")
                }

        # Call Felix via agent service
        result = await self.agent_service.generate_features_from_epic(
            epic=epic_data,
            specification_context=specification_context,
            options=options
        )

        return result

    # ========== Story Generation ==========

    async def generate_stories_from_feature(
        self,
        feature_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate user stories from a feature.

        Args:
            feature_id: The feature UUID
            options: Generation options

        Returns:
            Dict with generated stories
        """
        # Validate feature exists
        result = await self.db.execute(
            select(Feature).where(Feature.id == feature_id)
        )
        feature = result.scalar_one_or_none()

        if not feature:
            raise ValueError(f"Feature {feature_id} not found")

        # Check if stories already exist
        result = await self.db.execute(
            select(func.count(Story.id)).where(Story.feature_id == feature_id)
        )
        existing_count = result.scalar()

        if existing_count > 0:
            raise ValueError(
                f"Stories already exist for feature {feature_id}. "
                f"Use regenerate_stories() to recreate them."
            )

        # Validate story creation with max_stories option
        max_stories = options.get("max_stories", 7) if options else 7
        is_valid, error_msg = await self.validation_service.validate_story_creation(
            feature_id=str(feature_id),
            num_stories_to_create=max_stories
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Call Felix agent to generate stories
        felix_response = await self._call_felix_for_stories(
            feature=feature,
            options=options or {}
        )

        # Create story records
        stories = []
        for idx, story_data in enumerate(felix_response["stories"], start=1):
            # Validate story data
            validation_errors = await self.validation_service.validate_story_data(story_data)
            if validation_errors:
                raise ValueError(f"Story {idx} validation failed: {', '.join(validation_errors)}")

            story = Story(
                feature_id=feature_id,
                project_id=feature.project_id,
                title=story_data["title"],
                description=story_data["description"],
                user_type=story_data.get("user_type"),
                user_goal=story_data.get("user_goal"),
                user_benefit=story_data.get("user_benefit"),
                status=StoryStatus.DRAFT,
                priority=story_data.get("priority", Priority.MEDIUM),
                acceptance_criteria=story_data.get("acceptance_criteria", []),
                story_points=story_data.get("story_points"),
                estimated_hours=story_data.get("estimated_hours"),
                sequence_number=idx,
                generated_by="Felix",
                generation_metadata={
                    "feature_title": feature.title,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )

            self.db.add(story)
            stories.append(story)

        await self.db.commit()

        for story in stories:
            await self.db.refresh(story)

        return {
            "feature_id": str(feature_id),
            "stories_generated": len(stories),
            "stories": [
                {
                    "id": str(story.id),
                    "title": story.title,
                    "user_type": story.user_type,
                    "story_points": story.story_points
                }
                for story in stories
            ],
            "next_step": "generate_tasks"
        }

    async def _call_felix_for_stories(
        self,
        feature: Feature,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call Felix agent to break down feature into user stories."""

        # Prepare feature data for Felix
        feature_data = {
            "id": str(feature.id),
            "title": feature.title,
            "description": feature.description,
            "technical_approach": feature.technical_approach,
            "complexity": feature.complexity
        }

        # Get epic context if available
        epic_context = None
        if feature.epic_id:
            result = await self.db.execute(
                select(Epic).where(Epic.id == feature.epic_id)
            )
            epic = result.scalar_one_or_none()
            if epic:
                epic_context = {
                    "title": epic.title,
                    "business_value": epic.business_value,
                    "user_personas": epic.user_personas
                }

        # Call Felix via agent service
        result = await self.agent_service.generate_stories_from_feature(
            feature=feature_data,
            epic_context=epic_context,
            options=options
        )

        return result

    # ========== Task Generation ==========

    async def generate_tasks_from_story(
        self,
        story_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate technical tasks from a user story.

        Args:
            story_id: The story UUID
            options: Generation options

        Returns:
            Dict with generated tasks
        """
        # Validate story exists
        result = await self.db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()

        if not story:
            raise ValueError(f"Story {story_id} not found")

        # Check if tasks already exist
        result = await self.db.execute(
            select(func.count(Task.id)).where(Task.story_id == story_id)
        )
        existing_count = result.scalar()

        if existing_count > 0:
            raise ValueError(
                f"Tasks already exist for story {story_id}. "
                f"Use regenerate_tasks() to recreate them."
            )

        # Validate task creation with max_tasks option
        max_tasks = options.get("max_tasks", 5) if options else 5
        is_valid, error_msg = await self.validation_service.validate_task_creation(
            story_id=str(story_id),
            num_tasks_to_create=max_tasks
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Call Felix agent to generate tasks
        felix_response = await self._call_felix_for_tasks(
            story=story,
            options=options or {}
        )

        # Create task records
        tasks = []
        for idx, task_data in enumerate(felix_response["tasks"], start=1):
            # Validate task data
            validation_errors = await self.validation_service.validate_task_data(task_data)
            if validation_errors:
                raise ValueError(f"Task {idx} validation failed: {', '.join(validation_errors)}")

            task = Task(
                story_id=story_id,
                project_id=story.project_id,
                title=task_data["title"],
                description=task_data.get("description"),
                status=TaskStatus.TODO,
                priority=task_data.get("priority", Priority.MEDIUM),
                task_type=task_data.get("task_type"),
                technical_notes=task_data.get("technical_notes"),
                code_files=task_data.get("code_files", []),
                estimated_hours=task_data.get("estimated_hours"),
                sequence_number=idx,
                generated_by="Felix",
                generation_metadata={
                    "story_title": story.title,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )

            self.db.add(task)
            tasks.append(task)

        await self.db.commit()

        for task in tasks:
            await self.db.refresh(task)

        return {
            "story_id": str(story_id),
            "tasks_generated": len(tasks),
            "tasks": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "task_type": task.task_type,
                    "estimated_hours": task.estimated_hours
                }
                for task in tasks
            ],
            "next_step": "complete"
        }

    async def _call_felix_for_tasks(
        self,
        story: Story,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call Felix agent to break down story into technical tasks."""

        # Prepare story data for Felix
        story_data = {
            "id": str(story.id),
            "title": story.title,
            "description": story.description,
            "user_type": story.user_type,
            "user_goal": story.user_goal,
            "user_benefit": story.user_benefit,
            "acceptance_criteria": story.acceptance_criteria,
            "story_points": story.story_points
        }

        # Get feature context if available
        feature_context = None
        if story.feature_id:
            result = await self.db.execute(
                select(Feature).where(Feature.id == story.feature_id)
            )
            feature = result.scalar_one_or_none()
            if feature:
                feature_context = {
                    "title": feature.title,
                    "technical_approach": feature.technical_approach,
                    "api_endpoints": feature.api_endpoints,
                    "database_changes": feature.database_changes
                }

        # Call Felix via agent service
        result = await self.agent_service.generate_tasks_from_story(
            story=story_data,
            feature_context=feature_context,
            options=options
        )

        return result

    # ========== Complete Hierarchy Generation ==========

    async def generate_complete_hierarchy(
        self,
        specification_id: UUID,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete task hierarchy from specification.

        This is a convenience method that generates:
        1. Epics from specification
        2. Features from each epic
        3. Stories from each feature
        4. Tasks from each story

        Args:
            specification_id: The specification UUID
            options: Generation options

        Returns:
            Dict with complete hierarchy statistics
        """
        # Generate epics
        epic_result = await self.generate_epics_from_specification(
            specification_id,
            options
        )

        # Generate features for each epic
        total_features = 0
        total_stories = 0
        total_tasks = 0

        for epic_data in epic_result["epics"]:
            epic_id = UUID(epic_data["id"])

            # Generate features
            feature_result = await self.generate_features_from_epic(epic_id, options)
            total_features += feature_result["features_generated"]

            # Generate stories for each feature
            for feature_data in feature_result["features"]:
                feature_id = UUID(feature_data["id"])

                story_result = await self.generate_stories_from_feature(feature_id, options)
                total_stories += story_result["stories_generated"]

                # Generate tasks for each story
                for story_data in story_result["stories"]:
                    story_id = UUID(story_data["id"])

                    task_result = await self.generate_tasks_from_story(story_id, options)
                    total_tasks += task_result["tasks_generated"]

        return {
            "specification_id": str(specification_id),
            "hierarchy_complete": True,
            "statistics": {
                "epics": epic_result["epics_generated"],
                "features": total_features,
                "stories": total_stories,
                "tasks": total_tasks,
                "total_work_items": (
                    epic_result["epics_generated"] +
                    total_features +
                    total_stories +
                    total_tasks
                )
            },
            "next_step": "review_and_estimate"
        }
