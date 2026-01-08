"""
Task Generation Service
Week 23-24: Self-Questioning Agents

Enables agents to generate their own training tasks based on
skill gaps, failures, and unexplored areas.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

from app.models.task_generation import (
    TrainingTask, TrainingTaskResult, SkillGap,
    ExplorationTarget, ImprovementMetric, TrainingSession,
    GenerationStrategy, GeneratedTaskType, TaskDifficulty,
    TaskStatus, TaskSource, SkillGapSeverity, ImprovementTrend
)
from app.models.attribution import Attribution
from app.schemas.task_generation import (
    TrainingTaskCreate, GenerateTasksRequest, GenerationStrategyInput,
    SkillGapCreate, TrainingTaskResultCreate, TrainingTaskQuery,
    TaskGenerationSummary
)


# =============================================================================
# Default Agent Strategies
# =============================================================================

DEFAULT_AGENT_STRATEGIES = {
    'felix_001': {
        'focus_areas': ['architecture', 'specifications', 'system_design'],
        'difficulty_preference': 'HARD',
        'max_tasks_per_session': 5,
        'cooldown_period_ms': 3600000,
        'type_weights': {
            'FAILURE_RETRY': 0.3, 'EDGE_CASE_TEST': 0.25, 'SKILL_EXPANSION': 0.2,
            'VALIDATION_TEST': 0.1, 'PATTERN_PRACTICE': 0.1, 'EXPLORATION': 0.05
        }
    },
    'marcus_001': {
        'focus_areas': ['refactoring', 'technical_debt', 'code_maintenance'],
        'difficulty_preference': 'MEDIUM',
        'max_tasks_per_session': 6,
        'cooldown_period_ms': 3600000,
        'type_weights': {
            'FAILURE_RETRY': 0.25, 'EDGE_CASE_TEST': 0.15, 'SKILL_EXPANSION': 0.15,
            'VALIDATION_TEST': 0.15, 'PATTERN_PRACTICE': 0.2, 'EXPLORATION': 0.1
        }
    },
    'quinn_001': {
        'focus_areas': ['security', 'quality', 'code_review'],
        'difficulty_preference': 'HARD',
        'max_tasks_per_session': 8,
        'cooldown_period_ms': 1800000,
        'type_weights': {
            'FAILURE_RETRY': 0.2, 'EDGE_CASE_TEST': 0.3, 'SKILL_EXPANSION': 0.1,
            'VALIDATION_TEST': 0.25, 'PATTERN_PRACTICE': 0.1, 'EXPLORATION': 0.05
        }
    },
    'betty_001': {
        'focus_areas': ['debugging', 'error_handling', 'root_cause_analysis'],
        'difficulty_preference': 'HARD',
        'max_tasks_per_session': 4,
        'cooldown_period_ms': 3600000,
        'type_weights': {
            'FAILURE_RETRY': 0.35, 'EDGE_CASE_TEST': 0.25, 'SKILL_EXPANSION': 0.1,
            'VALIDATION_TEST': 0.1, 'PATTERN_PRACTICE': 0.15, 'EXPLORATION': 0.05
        }
    },
    'eliza_001': {
        'focus_areas': ['estimation', 'complexity_analysis', 'prediction'],
        'difficulty_preference': 'MEDIUM',
        'max_tasks_per_session': 5,
        'cooldown_period_ms': 7200000,
        'type_weights': {
            'FAILURE_RETRY': 0.3, 'EDGE_CASE_TEST': 0.2, 'SKILL_EXPANSION': 0.15,
            'VALIDATION_TEST': 0.1, 'PATTERN_PRACTICE': 0.2, 'EXPLORATION': 0.05
        }
    },
    'tessa_001': {
        'focus_areas': ['testing', 'test_strategy', 'coverage'],
        'difficulty_preference': 'MEDIUM',
        'max_tasks_per_session': 7,
        'cooldown_period_ms': 1800000,
        'type_weights': {
            'FAILURE_RETRY': 0.2, 'EDGE_CASE_TEST': 0.35, 'SKILL_EXPANSION': 0.1,
            'VALIDATION_TEST': 0.2, 'PATTERN_PRACTICE': 0.1, 'EXPLORATION': 0.05
        }
    },
    'miguel_001': {
        'focus_areas': ['migration', 'platform_upgrades', 'compatibility'],
        'difficulty_preference': 'HARD',
        'max_tasks_per_session': 3,
        'cooldown_period_ms': 7200000,
        'type_weights': {
            'FAILURE_RETRY': 0.3, 'EDGE_CASE_TEST': 0.2, 'SKILL_EXPANSION': 0.2,
            'VALIDATION_TEST': 0.15, 'PATTERN_PRACTICE': 0.1, 'EXPLORATION': 0.05
        }
    },
    'diana_001': {
        'focus_areas': ['documentation', 'api_docs', 'user_guides'],
        'difficulty_preference': 'EASY',
        'max_tasks_per_session': 6,
        'cooldown_period_ms': 3600000,
        'type_weights': {
            'FAILURE_RETRY': 0.2, 'EDGE_CASE_TEST': 0.15, 'SKILL_EXPANSION': 0.2,
            'VALIDATION_TEST': 0.1, 'PATTERN_PRACTICE': 0.25, 'EXPLORATION': 0.1
        }
    },
    'peter_001': {
        'focus_areas': ['requirements', 'user_stories', 'business_analysis'],
        'difficulty_preference': 'MEDIUM',
        'max_tasks_per_session': 5,
        'cooldown_period_ms': 3600000,
        'type_weights': {
            'FAILURE_RETRY': 0.25, 'EDGE_CASE_TEST': 0.2, 'SKILL_EXPANSION': 0.2,
            'VALIDATION_TEST': 0.1, 'PATTERN_PRACTICE': 0.15, 'EXPLORATION': 0.1
        }
    },
    'paul_001': {
        'focus_areas': ['planning', 'coordination', 'risk_management'],
        'difficulty_preference': 'MEDIUM',
        'max_tasks_per_session': 4,
        'cooldown_period_ms': 7200000,
        'type_weights': {
            'FAILURE_RETRY': 0.25, 'EDGE_CASE_TEST': 0.15, 'SKILL_EXPANSION': 0.2,
            'VALIDATION_TEST': 0.1, 'PATTERN_PRACTICE': 0.2, 'EXPLORATION': 0.1
        }
    }
}

AGENT_NAMES = {
    'felix_001': 'Felix', 'marcus_001': 'Marcus', 'quinn_001': 'Quinn',
    'betty_001': 'Betty', 'eliza_001': 'Eliza', 'tessa_001': 'Tessa',
    'miguel_001': 'Miguel', 'diana_001': 'Diana', 'peter_001': 'Peter',
    'paul_001': 'Paul'
}


class TaskGenerationService:
    """Service for generating and managing agent training tasks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # Task Generation
    # -------------------------------------------------------------------------

    async def generate_tasks(self, request: GenerateTasksRequest) -> Dict[str, Any]:
        """Generate training tasks for an agent based on skill gaps."""
        agent_id = request.agent_id
        max_tasks = request.max_tasks or 5

        # Get strategy (custom or default)
        strategy = await self._get_or_create_strategy(agent_id, request.strategy)

        # Analyze recent attributions for skill gaps
        skill_gaps = await self._analyze_recent_attributions(agent_id)

        # Also get existing unaddressed gaps
        existing_gaps = await self._get_unaddressed_skill_gaps(agent_id)
        all_gaps = skill_gaps + [g for g in existing_gaps if g.id not in [sg.id for sg in skill_gaps]]

        # Target specific gaps if requested
        if request.target_skill_gaps:
            all_gaps = [g for g in all_gaps if g.id in request.target_skill_gaps]

        # Prioritize and select gaps
        prioritized_gaps = self._prioritize_skill_gaps(all_gaps)[:max_tasks]

        # Generate tasks from gaps
        tasks = []
        for gap in prioritized_gaps:
            task_type = self._select_task_type(gap, strategy)
            task = await self._create_task_from_gap(agent_id, gap, task_type, strategy)
            tasks.append(task)

        # Calculate estimated training time
        estimated_time = sum(t.estimated_duration_ms for t in tasks)

        return {
            'tasks': tasks,
            'skill_gaps_targeted': prioritized_gaps,
            'estimated_training_time_ms': estimated_time
        }

    async def _analyze_recent_attributions(self, agent_id: str) -> List[SkillGap]:
        """Analyze recent attributions to identify skill gaps."""
        # Get attributions from last 7 days
        since = datetime.now() - timedelta(days=7)
        result = await self.db.execute(
            select(Attribution).where(
                and_(
                    Attribution.agent_id == agent_id,
                    Attribution.created_at >= since,
                    or_(
                        Attribution.outcome_type == 'FAILURE',
                        Attribution.outcome_type == 'PARTIAL',
                        Attribution.confidence < 0.6
                    )
                )
            )
        )
        attributions = result.scalars().all()

        skill_gaps = []
        for attr in attributions:
            gaps = self._extract_gaps_from_attribution(attr)
            for gap in gaps:
                self.db.add(gap)
                skill_gaps.append(gap)

        await self.db.commit()
        return skill_gaps

    def _extract_gaps_from_attribution(self, attribution: Attribution) -> List[SkillGap]:
        """Extract skill gaps from an attribution."""
        gaps = []
        agent_name = AGENT_NAMES.get(attribution.agent_id, 'Unknown')

        # Extract from causal factors if available
        causal_factors = attribution.causal_factors or []
        for factor in causal_factors:
            if isinstance(factor, dict) and factor.get('impact', 0) < 0:
                gap = SkillGap(
                    id=uuid4(),
                    agent_id=attribution.agent_id,
                    agent_name=agent_name,
                    description=f"Skill gap: {factor.get('factor', 'Unknown')}",
                    area=self._categorize_factor(factor.get('factor', '')),
                    severity=self._calculate_severity(factor.get('impact', 0)),
                    evidence=[{
                        'type': 'ATTRIBUTION_FAILURE',
                        'source_id': str(attribution.id),
                        'description': factor.get('description', ''),
                        'timestamp': datetime.now().isoformat()
                    }],
                    addressed=False,
                    identified_at=datetime.now()
                )
                gaps.append(gap)

        # Low confidence gap
        if attribution.confidence < 0.6:
            gap = SkillGap(
                id=uuid4(),
                agent_id=attribution.agent_id,
                agent_name=agent_name,
                description=f"Low confidence ({attribution.confidence:.1%})",
                area='general',
                severity=SkillGapSeverity.MINOR,
                evidence=[{
                    'type': 'LOW_CONFIDENCE',
                    'source_id': str(attribution.id),
                    'description': f'Confidence: {attribution.confidence}',
                    'timestamp': datetime.now().isoformat()
                }],
                addressed=False,
                identified_at=datetime.now()
            )
            gaps.append(gap)

        return gaps

    def _categorize_factor(self, factor: str) -> str:
        """Categorize a causal factor into an area."""
        factor_lower = factor.lower()
        if 'architecture' in factor_lower or 'design' in factor_lower:
            return 'architecture'
        if 'test' in factor_lower or 'coverage' in factor_lower:
            return 'testing'
        if 'security' in factor_lower:
            return 'security'
        if 'performance' in factor_lower:
            return 'performance'
        if 'documentation' in factor_lower:
            return 'documentation'
        return 'general'

    def _calculate_severity(self, impact: float) -> SkillGapSeverity:
        """Calculate severity from impact score."""
        if impact <= -0.7:
            return SkillGapSeverity.CRITICAL
        if impact <= -0.4:
            return SkillGapSeverity.IMPORTANT
        return SkillGapSeverity.MINOR

    def _prioritize_skill_gaps(self, gaps: List[SkillGap]) -> List[SkillGap]:
        """Prioritize skill gaps by severity and evidence."""
        severity_order = {
            SkillGapSeverity.CRITICAL: 0,
            SkillGapSeverity.IMPORTANT: 1,
            SkillGapSeverity.MINOR: 2
        }
        return sorted(gaps, key=lambda g: (
            severity_order.get(g.severity, 2),
            -len(g.evidence or [])
        ))

    def _select_task_type(
        self,
        gap: SkillGap,
        strategy: GenerationStrategy
    ) -> GeneratedTaskType:
        """Select appropriate task type for a skill gap."""
        if gap.severity == SkillGapSeverity.CRITICAL:
            return GeneratedTaskType.FAILURE_RETRY

        # Check evidence type
        evidence = gap.evidence or []
        has_validation = any(e.get('type') == 'VALIDATION_FAILURE' for e in evidence)
        if has_validation:
            return GeneratedTaskType.VALIDATION_TEST

        # Use strategy weights
        weights = strategy.type_weights or {}
        import random
        total = sum(weights.values()) if weights else 1
        r = random.random() * total
        for task_type, weight in weights.items():
            r -= weight
            if r <= 0:
                return GeneratedTaskType(task_type)

        return GeneratedTaskType.PATTERN_PRACTICE

    async def _create_task_from_gap(
        self,
        agent_id: str,
        gap: SkillGap,
        task_type: GeneratedTaskType,
        strategy: GenerationStrategy
    ) -> TrainingTask:
        """Create a training task from a skill gap."""
        agent_name = AGENT_NAMES.get(agent_id, 'Unknown')
        difficulty = TaskDifficulty(strategy.difficulty_preference or 'MEDIUM')

        task = TrainingTask(
            id=uuid4(),
            agent_id=agent_id,
            agent_name=agent_name,
            task_type=task_type,
            difficulty=difficulty,
            source=TaskSource.ATTRIBUTION,
            status=TaskStatus.PENDING,
            scenario_description=f"Address skill gap: {gap.description}",
            scenario_context={'skill_gap': gap.description, 'area': gap.area},
            scenario_constraints=[],
            scenario_success_criteria=['Task completes successfully', 'Validation passes'],
            scenario_focus_areas=[gap.area],
            learning_objective=f"Improve skills in {gap.area}",
            expected_success_rate=0.7,
            target_skills=[gap.area],
            improvement_metrics=['confidence_score', 'validation_pass_rate'],
            skill_gap_id=gap.id,
            priority=self._calculate_priority(gap, task_type),
            estimated_duration_ms=self._estimate_duration(task_type, difficulty),
            execution_attempts=0,
            max_attempts=3,
            created_at=datetime.now()
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    def _calculate_priority(self, gap: SkillGap, task_type: GeneratedTaskType) -> int:
        """Calculate task priority."""
        priority = 50
        if gap.severity == SkillGapSeverity.CRITICAL:
            priority += 30
        elif gap.severity == SkillGapSeverity.IMPORTANT:
            priority += 15
        if task_type == GeneratedTaskType.FAILURE_RETRY:
            priority += 10
        return min(100, priority)

    def _estimate_duration(
        self,
        task_type: GeneratedTaskType,
        difficulty: TaskDifficulty
    ) -> int:
        """Estimate task duration in milliseconds."""
        base = {
            GeneratedTaskType.FAILURE_RETRY: 600000,
            GeneratedTaskType.EDGE_CASE_TEST: 300000,
            GeneratedTaskType.SKILL_EXPANSION: 900000,
            GeneratedTaskType.VALIDATION_TEST: 300000,
            GeneratedTaskType.PATTERN_PRACTICE: 450000,
            GeneratedTaskType.EXPLORATION: 600000
        }.get(task_type, 300000)

        multiplier = {
            TaskDifficulty.EASY: 0.7,
            TaskDifficulty.MEDIUM: 1.0,
            TaskDifficulty.HARD: 1.5
        }.get(difficulty, 1.0)

        return int(base * multiplier)

    # -------------------------------------------------------------------------
    # Task Management
    # -------------------------------------------------------------------------

    async def list_tasks(self, query: TrainingTaskQuery) -> Dict[str, Any]:
        """List training tasks with filtering and pagination."""
        stmt = select(TrainingTask)

        if query.agent_id:
            stmt = stmt.where(TrainingTask.agent_id == query.agent_id)
        if query.task_type:
            stmt = stmt.where(TrainingTask.task_type == query.task_type)
        if query.status:
            stmt = stmt.where(TrainingTask.status == query.status)
        if query.difficulty:
            stmt = stmt.where(TrainingTask.difficulty == query.difficulty)
        if query.min_priority:
            stmt = stmt.where(TrainingTask.priority >= query.min_priority)

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total = count_result.scalar() or 0

        # Paginate
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)
        stmt = stmt.order_by(TrainingTask.created_at.desc())

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            'items': items,
            'total': total,
            'page': query.page,
            'page_size': query.page_size,
            'total_pages': (total + query.page_size - 1) // query.page_size
        }

    async def get_task(self, task_id: UUID) -> Optional[TrainingTask]:
        """Get a specific task by ID."""
        result = await self.db.execute(
            select(TrainingTask).where(TrainingTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def record_result(self, data: TrainingTaskResultCreate) -> TrainingTaskResult:
        """Record a training task result."""
        result = TrainingTaskResult(
            id=uuid4(),
            task_id=data.task_id,
            agent_id=data.agent_id,
            success=data.success,
            learning_achieved=data.actual_outcome.learning_achieved,
            skills_improved=data.actual_outcome.skills_improved,
            unexpected_learnings=data.actual_outcome.unexpected_learnings,
            duration_ms=data.metrics.duration,
            attempts=data.metrics.attempts,
            validation_passed=data.metrics.validation_passed,
            confidence_score=data.metrics.confidence_score,
            lessons=[l.model_dump() for l in data.lessons],
            follow_up_tasks=data.follow_up_tasks,
            attribution_id=data.attribution_id,
            completed_at=datetime.now()
        )

        self.db.add(result)

        # Update task status
        task = await self.get_task(data.task_id)
        if task:
            task.status = TaskStatus.COMPLETED if data.success else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.execution_attempts += 1

            # Mark skill gap as addressed if successful
            if data.success and task.skill_gap_id:
                await self._mark_gap_addressed(task.skill_gap_id)

        await self.db.commit()
        await self.db.refresh(result)
        return result

    # -------------------------------------------------------------------------
    # Skill Gaps
    # -------------------------------------------------------------------------

    async def _get_unaddressed_skill_gaps(self, agent_id: str) -> List[SkillGap]:
        """Get unaddressed skill gaps for an agent."""
        result = await self.db.execute(
            select(SkillGap).where(
                and_(
                    SkillGap.agent_id == agent_id,
                    SkillGap.addressed == False
                )
            )
        )
        return list(result.scalars().all())

    async def _mark_gap_addressed(self, gap_id: UUID) -> None:
        """Mark a skill gap as addressed."""
        result = await self.db.execute(
            select(SkillGap).where(SkillGap.id == gap_id)
        )
        gap = result.scalar_one_or_none()
        if gap:
            gap.addressed = True
            gap.addressed_at = datetime.now()

    async def get_skill_gaps(
        self,
        agent_id: str,
        min_severity: Optional[SkillGapSeverity] = None,
        include_addressed: bool = False
    ) -> Dict[str, Any]:
        """Get skill gaps for an agent."""
        stmt = select(SkillGap).where(SkillGap.agent_id == agent_id)

        if not include_addressed:
            stmt = stmt.where(SkillGap.addressed == False)

        result = await self.db.execute(stmt)
        gaps = list(result.scalars().all())

        if min_severity:
            severity_order = {
                SkillGapSeverity.CRITICAL: 0,
                SkillGapSeverity.IMPORTANT: 1,
                SkillGapSeverity.MINOR: 2
            }
            min_order = severity_order.get(min_severity, 2)
            gaps = [g for g in gaps if severity_order.get(g.severity, 2) <= min_order]

        critical = len([g for g in gaps if g.severity == SkillGapSeverity.CRITICAL])
        addressed = len([g for g in gaps if g.addressed])

        return {
            'skill_gaps': gaps,
            'total_gaps': len(gaps),
            'critical_gaps': critical,
            'addressed_gaps': addressed
        }

    # -------------------------------------------------------------------------
    # Strategy Management
    # -------------------------------------------------------------------------

    async def _get_or_create_strategy(
        self,
        agent_id: str,
        custom: Optional[GenerationStrategyInput] = None
    ) -> GenerationStrategy:
        """Get or create generation strategy for an agent."""
        result = await self.db.execute(
            select(GenerationStrategy).where(GenerationStrategy.agent_id == agent_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            defaults = DEFAULT_AGENT_STRATEGIES.get(agent_id, {})
            strategy = GenerationStrategy(
                id=uuid4(),
                agent_id=agent_id,
                focus_areas=defaults.get('focus_areas', ['general']),
                difficulty_preference=TaskDifficulty(defaults.get('difficulty_preference', 'MEDIUM')),
                max_tasks_per_session=defaults.get('max_tasks_per_session', 5),
                cooldown_period_ms=defaults.get('cooldown_period_ms', 3600000),
                type_weights=defaults.get('type_weights', {}),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.db.add(strategy)
            await self.db.commit()
            await self.db.refresh(strategy)

        # Apply custom overrides
        if custom:
            if custom.focus_areas:
                strategy.focus_areas = custom.focus_areas
            if custom.difficulty_preference:
                strategy.difficulty_preference = custom.difficulty_preference
            if custom.max_tasks_per_session:
                strategy.max_tasks_per_session = custom.max_tasks_per_session
            if custom.type_weights:
                strategy.type_weights = {k.value: v for k, v in custom.type_weights.items()}
            strategy.updated_at = datetime.now()

        return strategy

    async def update_strategy(
        self,
        agent_id: str,
        data: GenerationStrategyInput
    ) -> GenerationStrategy:
        """Update generation strategy for an agent."""
        strategy = await self._get_or_create_strategy(agent_id, data)
        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------

    async def get_summary(self) -> TaskGenerationSummary:
        """Get task generation summary."""
        # Count tasks by status
        result = await self.db.execute(
            select(
                TrainingTask.status,
                func.count(TrainingTask.id)
            ).group_by(TrainingTask.status)
        )
        status_counts = dict(result.all())

        total = sum(status_counts.values())
        pending = status_counts.get(TaskStatus.PENDING, 0)
        completed = status_counts.get(TaskStatus.COMPLETED, 0)
        failed = status_counts.get(TaskStatus.FAILED, 0)

        # Count skill gaps
        gap_result = await self.db.execute(
            select(
                func.count(SkillGap.id),
                func.sum(func.cast(SkillGap.addressed == False, Integer))
            )
        )
        gap_row = gap_result.first()
        total_gaps = gap_row[0] if gap_row else 0
        unaddressed = gap_row[1] if gap_row and gap_row[1] else 0

        # Count active agents
        agent_result = await self.db.execute(
            select(func.count(func.distinct(TrainingTask.agent_id)))
        )
        agents_active = agent_result.scalar() or 0

        success_rate = completed / total if total > 0 else 0.0

        return TaskGenerationSummary(
            total_tasks=total,
            pending_tasks=pending,
            completed_tasks=completed,
            failed_tasks=failed,
            success_rate=success_rate,
            total_skill_gaps=total_gaps,
            unaddressed_skill_gaps=unaddressed,
            agents_active=agents_active
        )


# Import Integer for SQL cast
from sqlalchemy import Integer
