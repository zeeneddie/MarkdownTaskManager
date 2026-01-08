"""
CCPM Orchestrator - Week 79

Orchestrates PRD decomposition, task prioritization, and intelligent recommendations.
Integrates with LLM agents for automated work breakdown.
"""

import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, desc, func

from app.models.ccpm import (
    PRDDecomposition,
    TaskRecommendation,
    DecompositionStatus,
    RecommendationStatus
)
from app.providers.registry import ProviderRegistry


class DecompositionResult:
    """Result of PRD decomposition."""
    def __init__(
        self,
        id: UUID,
        title: str,
        epics: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        stories: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        total_story_points: int,
        total_function_points: float,
        processing_time_ms: int
    ):
        self.id = id
        self.title = title
        self.epics = epics
        self.features = features
        self.stories = stories
        self.tasks = tasks
        self.total_story_points = total_story_points
        self.total_function_points = total_function_points
        self.processing_time_ms = processing_time_ms


class TaskRecommendationResult:
    """Task recommendation with scoring."""
    def __init__(
        self,
        id: UUID,
        task_id: Optional[UUID],
        task_title: str,
        task_type: str,
        priority_score: float,
        reasoning: str,
        recommended_agent: str,
        estimated_hours: float,
        impact_score: float,
        urgency_score: float,
        complexity_score: float,
        dependencies_met: bool,
        blocked_by: List[UUID]
    ):
        self.id = id
        self.task_id = task_id
        self.task_title = task_title
        self.task_type = task_type
        self.priority_score = priority_score
        self.reasoning = reasoning
        self.recommended_agent = recommended_agent
        self.estimated_hours = estimated_hours
        self.impact_score = impact_score
        self.urgency_score = urgency_score
        self.complexity_score = complexity_score
        self.dependencies_met = dependencies_met
        self.blocked_by = blocked_by


class CCPMOrchestrator:
    """
    Orchestrates CCPM (Claude Code Project Management) operations.

    Features:
    - PRD decomposition into epics, features, stories, tasks
    - Intelligent task prioritization
    - Agent assignment recommendations
    - Dependency tracking and critical path analysis
    """

    # Agent capability mapping
    AGENT_CAPABILITIES = {
        "felix": ["architecture", "design", "api", "system"],
        "quinn": ["quality", "review", "security", "audit"],
        "betty": ["debug", "bug", "fix", "troubleshoot"],
        "eliza": ["estimate", "planning", "sizing"],
        "diana": ["documentation", "docs", "readme", "guide"],
        "marcus": ["refactor", "maintenance", "cleanup", "debt"],
        "tessa": ["test", "testing", "coverage", "e2e"],
        "miguel": ["migration", "upgrade", "convert", "port"],
        "peter": ["requirements", "story", "feature", "prd"],
        "paul": ["planning", "sprint", "resource", "schedule"]
    }

    # Complexity keywords
    COMPLEXITY_KEYWORDS = {
        "high": ["complex", "distributed", "real-time", "security", "performance", "migration"],
        "medium": ["integration", "api", "database", "authentication", "validation"],
        "low": ["simple", "basic", "update", "fix", "minor", "documentation"]
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_registry = ProviderRegistry()

    async def decompose_prd(
        self,
        title: str,
        prd_content: str,
        project_id: Optional[int] = None,
        agent: str = "peter",
        llm_model: Optional[str] = None
    ) -> DecompositionResult:
        """
        Decompose a PRD into hierarchical tasks.

        Args:
            title: PRD title
            prd_content: Full PRD text
            project_id: Optional project association
            agent: Agent to use for decomposition
            llm_model: Optional specific LLM model

        Returns:
            DecompositionResult with full hierarchy
        """
        start_time = time.time()

        # Check for duplicate PRD
        prd_hash = hashlib.sha256(prd_content.encode()).hexdigest()
        existing = await self._get_existing_decomposition(prd_hash, project_id)
        if existing and existing.status == DecompositionStatus.COMPLETED.value:
            return self._to_decomposition_result(existing)

        # Create decomposition record
        decomposition = PRDDecomposition(
            id=uuid.uuid4(),
            project_id=project_id,
            title=title,
            prd_content=prd_content,
            prd_hash=prd_hash,
            status=DecompositionStatus.PROCESSING.value,
            agent_used=agent,
            llm_model=llm_model
        )

        self.db.add(decomposition)
        await self.db.commit()

        try:
            # Get LLM provider
            provider = await self.provider_registry.get_provider(
                model_name=llm_model
            )

            # Decompose using LLM
            decomposition_prompt = self._build_decomposition_prompt(prd_content)
            result = await provider.generate(decomposition_prompt)

            # Parse the result
            hierarchy = self._parse_decomposition_result(result)

            # Update record
            decomposition.decomposition_result = hierarchy
            decomposition.epics_count = len(hierarchy.get("epics", []))
            decomposition.features_count = len(hierarchy.get("features", []))
            decomposition.stories_count = len(hierarchy.get("stories", []))
            decomposition.tasks_count = len(hierarchy.get("tasks", []))
            decomposition.total_story_points = hierarchy.get("total_story_points", 0)
            decomposition.total_function_points = hierarchy.get("total_function_points", 0.0)
            decomposition.status = DecompositionStatus.COMPLETED.value
            decomposition.processing_time_ms = int((time.time() - start_time) * 1000)
            decomposition.completed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(decomposition)

            return self._to_decomposition_result(decomposition)

        except Exception as e:
            decomposition.status = DecompositionStatus.FAILED.value
            decomposition.error_message = str(e)
            decomposition.processing_time_ms = int((time.time() - start_time) * 1000)
            await self.db.commit()

            raise RuntimeError(f"PRD decomposition failed: {e}")

    async def get_decomposition(
        self,
        decomposition_id: UUID
    ) -> Optional[PRDDecomposition]:
        """Get a decomposition by ID."""
        result = await self.db.execute(
            select(PRDDecomposition).where(PRDDecomposition.id == decomposition_id)
        )
        return result.scalar_one_or_none()

    async def list_decompositions(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[PRDDecomposition]:
        """List decompositions with filters."""
        query = select(PRDDecomposition)

        if project_id:
            query = query.where(PRDDecomposition.project_id == project_id)
        if status:
            query = query.where(PRDDecomposition.status == status)

        query = query.order_by(desc(PRDDecomposition.created_at)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_next_task(
        self,
        project_id: int,
        agent_id: Optional[str] = None,
        refresh: bool = False
    ) -> Optional[TaskRecommendationResult]:
        """
        Get the next recommended task for a project or agent.

        Args:
            project_id: Project to get task for
            agent_id: Optional specific agent
            refresh: Force recalculation of recommendations

        Returns:
            Top recommended task
        """
        if refresh:
            await self._refresh_recommendations(project_id)

        # Get top recommendation
        query = select(TaskRecommendation).where(
            and_(
                TaskRecommendation.project_id == project_id,
                TaskRecommendation.status == RecommendationStatus.PENDING.value,
                TaskRecommendation.dependencies_met == True
            )
        )

        if agent_id:
            query = query.where(TaskRecommendation.recommended_agent == agent_id)

        query = query.order_by(desc(TaskRecommendation.priority_score)).limit(1)

        result = await self.db.execute(query)
        recommendation = result.scalar_one_or_none()

        if recommendation:
            return self._to_recommendation_result(recommendation)

        return None

    async def get_task_recommendations(
        self,
        project_id: int,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[TaskRecommendationResult]:
        """
        Get ranked task recommendations.

        Args:
            project_id: Project ID
            agent_id: Optional agent filter
            limit: Max recommendations to return

        Returns:
            List of task recommendations sorted by priority
        """
        query = select(TaskRecommendation).where(
            and_(
                TaskRecommendation.project_id == project_id,
                TaskRecommendation.status == RecommendationStatus.PENDING.value
            )
        )

        if agent_id:
            query = query.where(TaskRecommendation.recommended_agent == agent_id)

        query = query.order_by(desc(TaskRecommendation.priority_score)).limit(limit)

        result = await self.db.execute(query)
        recommendations = result.scalars().all()

        return [self._to_recommendation_result(r) for r in recommendations]

    async def accept_recommendation(
        self,
        recommendation_id: UUID,
        accepted_by: str = "user"
    ) -> TaskRecommendation:
        """Mark a recommendation as accepted."""
        result = await self.db.execute(
            select(TaskRecommendation).where(TaskRecommendation.id == recommendation_id)
        )
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        recommendation.status = RecommendationStatus.ACCEPTED.value
        recommendation.accepted_at = datetime.utcnow()
        recommendation.accepted_by = accepted_by

        await self.db.commit()
        return recommendation

    async def reject_recommendation(
        self,
        recommendation_id: UUID
    ) -> TaskRecommendation:
        """Mark a recommendation as rejected."""
        result = await self.db.execute(
            select(TaskRecommendation).where(TaskRecommendation.id == recommendation_id)
        )
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        recommendation.status = RecommendationStatus.REJECTED.value
        await self.db.commit()

        return recommendation

    async def create_recommendations_from_decomposition(
        self,
        decomposition_id: UUID
    ) -> List[TaskRecommendation]:
        """
        Create task recommendations from a PRD decomposition.

        Args:
            decomposition_id: Source decomposition

        Returns:
            List of created recommendations
        """
        decomposition = await self.get_decomposition(decomposition_id)
        if not decomposition:
            raise ValueError(f"Decomposition {decomposition_id} not found")

        if decomposition.status != DecompositionStatus.COMPLETED.value:
            raise ValueError("Decomposition not completed")

        recommendations = []
        hierarchy = decomposition.decomposition_result

        # Create recommendations for all tasks
        for task in hierarchy.get("tasks", []):
            recommendation = await self._create_recommendation_from_task(
                task,
                decomposition.project_id,
                hierarchy
            )
            recommendations.append(recommendation)

        return recommendations

    async def get_statistics(
        self,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get CCPM statistics."""
        # Decomposition stats
        dec_query = select(PRDDecomposition)
        rec_query = select(TaskRecommendation)

        if project_id:
            dec_query = dec_query.where(PRDDecomposition.project_id == project_id)
            rec_query = rec_query.where(TaskRecommendation.project_id == project_id)

        dec_result = await self.db.execute(dec_query)
        decompositions = dec_result.scalars().all()

        rec_result = await self.db.execute(rec_query)
        recommendations = rec_result.scalars().all()

        dec_status = {}
        rec_status = {}
        agent_assignments = {}

        for d in decompositions:
            dec_status[d.status] = dec_status.get(d.status, 0) + 1

        for r in recommendations:
            rec_status[r.status] = rec_status.get(r.status, 0) + 1
            if r.recommended_agent:
                agent_assignments[r.recommended_agent] = (
                    agent_assignments.get(r.recommended_agent, 0) + 1
                )

        return {
            "decompositions": {
                "total": len(decompositions),
                "by_status": dec_status
            },
            "recommendations": {
                "total": len(recommendations),
                "by_status": rec_status,
                "by_agent": agent_assignments
            },
            "total_story_points": sum(
                d.total_story_points or 0 for d in decompositions
                if d.status == DecompositionStatus.COMPLETED.value
            ),
            "total_function_points": sum(
                d.total_function_points or 0 for d in decompositions
                if d.status == DecompositionStatus.COMPLETED.value
            )
        }

    # Private helper methods

    async def _get_existing_decomposition(
        self,
        prd_hash: str,
        project_id: Optional[int]
    ) -> Optional[PRDDecomposition]:
        """Check for existing decomposition of same PRD."""
        query = select(PRDDecomposition).where(
            PRDDecomposition.prd_hash == prd_hash
        )
        if project_id:
            query = query.where(PRDDecomposition.project_id == project_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _build_decomposition_prompt(self, prd_content: str) -> str:
        """Build the LLM prompt for PRD decomposition."""
        return f"""Analyze this Product Requirements Document (PRD) and decompose it into a hierarchical task structure.

PRD Content:
{prd_content}

Create a JSON response with the following structure:
{{
    "epics": [
        {{
            "id": "E1",
            "title": "Epic title",
            "description": "Epic description",
            "story_points": 40,
            "features": ["F1", "F2"]
        }}
    ],
    "features": [
        {{
            "id": "F1",
            "title": "Feature title",
            "description": "Feature description",
            "epic_id": "E1",
            "story_points": 13,
            "stories": ["S1", "S2"]
        }}
    ],
    "stories": [
        {{
            "id": "S1",
            "title": "As a user, I want...",
            "description": "Story description",
            "feature_id": "F1",
            "story_points": 5,
            "acceptance_criteria": ["AC1", "AC2"],
            "tasks": ["T1", "T2"]
        }}
    ],
    "tasks": [
        {{
            "id": "T1",
            "title": "Task title",
            "description": "Task description",
            "story_id": "S1",
            "estimated_hours": 4,
            "complexity": "medium",
            "keywords": ["api", "backend"],
            "dependencies": []
        }}
    ],
    "total_story_points": 100,
    "total_function_points": 45.5,
    "critical_path": ["T1", "T3", "T7"]
}}

Guidelines:
- Create realistic story point estimates (1, 2, 3, 5, 8, 13, 21)
- Identify dependencies between tasks
- Mark complexity as "low", "medium", or "high"
- Include relevant keywords for agent assignment
- Calculate function points based on complexity

Respond with ONLY the JSON, no additional text."""

    def _parse_decomposition_result(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into hierarchy structure."""
        import json

        # Clean the response
        response = llm_response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            # Return empty structure on parse failure
            return {
                "epics": [],
                "features": [],
                "stories": [],
                "tasks": [],
                "total_story_points": 0,
                "total_function_points": 0,
                "parse_error": str(e)
            }

    async def _create_recommendation_from_task(
        self,
        task: Dict[str, Any],
        project_id: Optional[int],
        hierarchy: Dict[str, Any]
    ) -> TaskRecommendation:
        """Create a recommendation from a task dict."""
        # Calculate scores
        complexity_score = self._calculate_complexity_score(task)
        impact_score = self._calculate_impact_score(task, hierarchy)
        urgency_score = self._calculate_urgency_score(task, hierarchy)

        # Priority formula: 0.4*impact + 0.3*urgency + 0.3*(1-complexity)
        priority_score = (
            0.4 * impact_score +
            0.3 * urgency_score +
            0.3 * (100 - complexity_score)
        )

        # Determine best agent
        recommended_agent = self._recommend_agent(task)

        # Check dependencies
        dependencies_met = True
        blocked_by = []
        for dep_id in task.get("dependencies", []):
            # In real implementation, check if dep task is completed
            blocked_by.append(dep_id)
            dependencies_met = len(blocked_by) == 0

        recommendation = TaskRecommendation(
            id=uuid.uuid4(),
            project_id=project_id,
            task_title=task.get("title", "Untitled Task"),
            task_type="task",
            priority_score=priority_score,
            reasoning=f"Impact: {impact_score:.0f}, Urgency: {urgency_score:.0f}, Complexity: {complexity_score:.0f}",
            factors={
                "impact": impact_score,
                "urgency": urgency_score,
                "complexity": complexity_score
            },
            dependencies_met=dependencies_met,
            blocked_by=blocked_by,
            recommended_agent=recommended_agent,
            estimated_effort_hours=task.get("estimated_hours", 4),
            impact_score=impact_score,
            urgency_score=urgency_score,
            complexity_score=complexity_score,
            status=RecommendationStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        self.db.add(recommendation)
        await self.db.commit()
        await self.db.refresh(recommendation)

        return recommendation

    def _calculate_complexity_score(self, task: Dict[str, Any]) -> float:
        """Calculate complexity score (0-100)."""
        complexity = task.get("complexity", "medium").lower()
        base_score = {"low": 25, "medium": 50, "high": 75}.get(complexity, 50)

        # Adjust based on keywords
        keywords = task.get("keywords", [])
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in self.COMPLEXITY_KEYWORDS["high"]:
                base_score += 10
            elif kw_lower in self.COMPLEXITY_KEYWORDS["low"]:
                base_score -= 10

        return min(100, max(0, base_score))

    def _calculate_impact_score(
        self,
        task: Dict[str, Any],
        hierarchy: Dict[str, Any]
    ) -> float:
        """Calculate business impact score (0-100)."""
        # Base score from task position in hierarchy
        story_id = task.get("story_id")
        if not story_id:
            return 50

        # Find parent story
        for story in hierarchy.get("stories", []):
            if story.get("id") == story_id:
                # Higher story points = higher impact
                story_points = story.get("story_points", 3)
                return min(100, story_points * 10)

        return 50

    def _calculate_urgency_score(
        self,
        task: Dict[str, Any],
        hierarchy: Dict[str, Any]
    ) -> float:
        """Calculate urgency score (0-100)."""
        # Check if on critical path
        critical_path = hierarchy.get("critical_path", [])
        if task.get("id") in critical_path:
            return 90

        # Check dependencies - tasks blocking others are urgent
        task_id = task.get("id")
        blocking_count = 0

        for other_task in hierarchy.get("tasks", []):
            if task_id in other_task.get("dependencies", []):
                blocking_count += 1

        return min(100, 50 + blocking_count * 15)

    def _recommend_agent(self, task: Dict[str, Any]) -> str:
        """Recommend best agent for a task."""
        keywords = [kw.lower() for kw in task.get("keywords", [])]
        title_words = task.get("title", "").lower().split()
        all_words = keywords + title_words

        # Score each agent
        agent_scores = {}
        for agent, capabilities in self.AGENT_CAPABILITIES.items():
            score = 0
            for word in all_words:
                for cap in capabilities:
                    if cap in word or word in cap:
                        score += 1
            agent_scores[agent] = score

        # Return highest scoring agent, default to felix
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        return best_agent[0] if best_agent[1] > 0 else "felix"

    async def _refresh_recommendations(self, project_id: int) -> None:
        """Recalculate all recommendations for a project."""
        # Get all pending recommendations
        result = await self.db.execute(
            select(TaskRecommendation).where(
                and_(
                    TaskRecommendation.project_id == project_id,
                    TaskRecommendation.status == RecommendationStatus.PENDING.value
                )
            )
        )
        recommendations = result.scalars().all()

        # Recalculate priority scores
        for rec in recommendations:
            rec.priority_score = (
                0.4 * (rec.impact_score or 50) +
                0.3 * (rec.urgency_score or 50) +
                0.3 * (100 - (rec.complexity_score or 50))
            )

        await self.db.commit()

    def _to_decomposition_result(
        self,
        decomposition: PRDDecomposition
    ) -> DecompositionResult:
        """Convert model to result object."""
        hierarchy = decomposition.decomposition_result or {}

        return DecompositionResult(
            id=decomposition.id,
            title=decomposition.title,
            epics=hierarchy.get("epics", []),
            features=hierarchy.get("features", []),
            stories=hierarchy.get("stories", []),
            tasks=hierarchy.get("tasks", []),
            total_story_points=decomposition.total_story_points or 0,
            total_function_points=decomposition.total_function_points or 0.0,
            processing_time_ms=decomposition.processing_time_ms or 0
        )

    def _to_recommendation_result(
        self,
        rec: TaskRecommendation
    ) -> TaskRecommendationResult:
        """Convert model to result object."""
        return TaskRecommendationResult(
            id=rec.id,
            task_id=rec.task_id,
            task_title=rec.task_title,
            task_type=rec.task_type or "task",
            priority_score=rec.priority_score,
            reasoning=rec.reasoning or "",
            recommended_agent=rec.recommended_agent or "felix",
            estimated_hours=rec.estimated_effort_hours or 4,
            impact_score=rec.impact_score or 50,
            urgency_score=rec.urgency_score or 50,
            complexity_score=rec.complexity_score or 50,
            dependencies_met=rec.dependencies_met,
            blocked_by=rec.blocked_by or []
        )
