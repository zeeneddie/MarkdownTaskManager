"""
Agent Evolution Service

Week 17: AgentEvolver Integration - Core Evolution Logic
Based on: github.com/zeeneddie/AgentEvolver

Implements three core mechanisms:
1. Self-Questioning: Automatic task generation for learning
2. Self-Navigating: Experience-guided decision making
3. Self-Attributing: Outcome analysis and credit assignment

Author: Claude Code (Week 17 Day 3)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
import uuid
import logging
import asyncio
import random

from app.services.experience_store_service import (
    ExperienceStoreService,
    get_experience_store,
    Experience,
    SuccessfulPattern,
    FailureAnalysis,
    EstimationAccuracy,
    QualityMetricsRecord,
    AgentRole,
    WorkType,
    Outcome,
    FailureType,
    Complexity,
    KeyDecision
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TaskContext:
    """Context for a task being executed"""
    work_type: WorkType
    description: str
    complexity: Complexity
    domain: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    previous_attempts: int = 0


@dataclass
class Guidance:
    """Guidance from past experience"""
    relevant_experiences: List[Experience]
    suggested_approach: str
    warnings_from_past: List[str]
    confidence_score: float  # 0-1
    pattern_matches: List[Tuple[SuccessfulPattern, float]]
    should_explore: bool  # True if agent should try something new


@dataclass
class StepAttribution:
    """Attribution for a single step"""
    step_name: str
    step_index: int
    contribution: float  # -1 to 1
    confidence: float  # 0-1
    reasoning: str
    could_improve: bool
    improvement_suggestion: Optional[str] = None


@dataclass
class Attribution:
    """Complete attribution for a task outcome"""
    task_id: str
    agent_id: str
    total_score: float
    attributions: List[StepAttribution]
    key_success_factors: List[str]
    key_failure_factors: List[str]
    recommendations: List[str]


@dataclass
class EvolutionConfig:
    """Configuration for agent evolution behavior"""
    learning_rate: float = 0.1
    experience_weight: float = 0.7
    exploration_rate: float = 0.2
    attribution_depth: int = 3
    min_experience_confidence: float = 0.6
    max_experiences_to_consider: int = 10
    self_questioning_enabled: bool = True
    self_navigating_enabled: bool = True
    self_attributing_enabled: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    agent_role: AgentRole
    period_start: datetime
    period_end: datetime

    # Success metrics
    total_tasks: int = 0
    successful_tasks: int = 0
    partial_tasks: int = 0
    failed_tasks: int = 0

    # Quality metrics
    average_quality_score: float = 0.0
    quality_trend: str = "stable"  # 'improving', 'stable', 'declining'
    validation_pass_rate: float = 0.0

    # Efficiency metrics
    average_duration: float = 0.0
    average_retries: float = 0.0
    peer_assistance_rate: float = 0.0

    # Learning metrics
    experiences_generated: int = 0
    patterns_discovered: int = 0
    experience_reuse_rate: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0.0


@dataclass
class LearningTask:
    """A task generated for learning purposes"""
    id: str
    agent_id: str
    work_type: WorkType
    description: str
    learning_goal: str
    expected_difficulty: Complexity
    knowledge_gap: str
    created_at: datetime


# ============================================================================
# AGENT EVOLUTION SERVICE
# ============================================================================

class AgentEvolutionService:
    """
    Service for managing agent evolution and learning.

    Implements:
    1. Self-Questioning: Generate learning tasks based on knowledge gaps
    2. Self-Navigating: Consult experience for guidance on new tasks
    3. Self-Attributing: Analyze outcomes and attribute credit/blame
    """

    # Default configs per agent role
    DEFAULT_CONFIGS: Dict[AgentRole, EvolutionConfig] = {
        AgentRole.FEATURE_ARCHITECT: EvolutionConfig(
            learning_rate=0.15, experience_weight=0.8, exploration_rate=0.15
        ),
        AgentRole.MAINTENANCE_SPECIALIST: EvolutionConfig(
            learning_rate=0.1, experience_weight=0.75, exploration_rate=0.2
        ),
        AgentRole.QUALITY_INSPECTOR: EvolutionConfig(
            learning_rate=0.08, experience_weight=0.85, exploration_rate=0.1
        ),
        AgentRole.BUG_HUNTER: EvolutionConfig(
            learning_rate=0.12, experience_weight=0.7, exploration_rate=0.25
        ),
        AgentRole.ESTIMATION_ENGINE: EvolutionConfig(
            learning_rate=0.2, experience_weight=0.9, exploration_rate=0.1
        ),
        AgentRole.TEST_ENGINEER: EvolutionConfig(
            learning_rate=0.1, experience_weight=0.75, exploration_rate=0.2
        ),
        AgentRole.MIGRATION_ARCHITECT: EvolutionConfig(
            learning_rate=0.08, experience_weight=0.85, exploration_rate=0.1
        ),
        AgentRole.DOCUMENTATION_WRITER: EvolutionConfig(
            learning_rate=0.12, experience_weight=0.7, exploration_rate=0.2
        ),
        AgentRole.PRODUCT_OWNER: EvolutionConfig(
            learning_rate=0.1, experience_weight=0.8, exploration_rate=0.15
        ),
        AgentRole.PROJECT_LEAD: EvolutionConfig(
            learning_rate=0.1, experience_weight=0.8, exploration_rate=0.15
        ),
    }

    def __init__(
        self,
        experience_store: Optional[ExperienceStoreService] = None
    ):
        self.experience_store = experience_store or get_experience_store()
        self._agent_configs: Dict[str, EvolutionConfig] = {}
        self._agent_metrics: Dict[str, PerformanceMetrics] = {}
        self._learning_tasks: Dict[str, List[LearningTask]] = {}

    # =========================================================================
    # SELF-NAVIGATING: Experience-Guided Decisions
    # =========================================================================

    async def consult_experience(
        self,
        agent_id: str,
        agent_role: AgentRole,
        context: TaskContext
    ) -> Guidance:
        """
        Consult past experiences for guidance on a new task.

        This is the core of Self-Navigating: the agent looks at how
        it handled similar situations in the past.
        """
        config = self._get_config(agent_id, agent_role)

        # Find similar experiences
        similar_experiences, _ = await self._find_relevant_experiences(
            context, agent_role, config
        )

        # Find applicable patterns
        pattern_matches = await self.experience_store.find_applicable_patterns(
            context.description,
            context.work_type,
            limit=5
        )

        # Find potential warnings from past failures
        warnings = await self._get_warnings_from_failures(context, agent_role)

        # Determine if we should explore or exploit
        should_explore = self._should_explore(
            similar_experiences, config, context.previous_attempts
        )

        # Generate suggested approach
        suggested_approach = self._generate_suggested_approach(
            similar_experiences, pattern_matches, should_explore, context
        )

        # Calculate confidence
        confidence = self._calculate_guidance_confidence(
            similar_experiences, pattern_matches, context
        )

        return Guidance(
            relevant_experiences=similar_experiences[:config.max_experiences_to_consider],
            suggested_approach=suggested_approach,
            warnings_from_past=warnings,
            confidence_score=confidence,
            pattern_matches=pattern_matches,
            should_explore=should_explore
        )

    async def _find_relevant_experiences(
        self,
        context: TaskContext,
        agent_role: AgentRole,
        config: EvolutionConfig
    ) -> Tuple[List[Experience], List[float]]:
        """Find experiences relevant to the current context"""
        results = await self.experience_store.find_similar_experiences(
            context.description,
            work_type=context.work_type,
            agent_role=agent_role,
            limit=config.max_experiences_to_consider * 2
        )

        # Filter by minimum confidence
        filtered = [
            (exp, score) for exp, score in results
            if score >= config.min_experience_confidence
        ]

        if not filtered:
            # Return all if none meet confidence threshold
            return [exp for exp, _ in results], [score for _, score in results]

        return [exp for exp, _ in filtered], [score for _, score in filtered]

    async def _get_warnings_from_failures(
        self,
        context: TaskContext,
        agent_role: AgentRole
    ) -> List[str]:
        """Get warnings based on past failures"""
        warnings = []

        # Search for similar failures
        failures = await self.experience_store.find_similar_failures(
            context.description,
            work_type=context.work_type,
            limit=5
        )

        for failure, similarity in failures:
            if similarity > 0.5:
                warnings.append(f"Past failure: {failure.root_cause}")
                for strategy in failure.prevention_strategies[:2]:
                    warnings.append(f"  - Prevention: {strategy}")

        return warnings[:10]  # Limit warnings

    def _should_explore(
        self,
        experiences: List[Experience],
        config: EvolutionConfig,
        previous_attempts: int
    ) -> bool:
        """Decide whether to explore new approaches or exploit known ones"""
        # Always explore if no relevant experience
        if not experiences:
            return True

        # Increase exploration after failed attempts
        effective_exploration_rate = config.exploration_rate + (previous_attempts * 0.1)

        # Check if successful experiences exist
        success_experiences = [e for e in experiences if e.outcome == Outcome.SUCCESS]
        if not success_experiences:
            return True  # Explore if no successful precedent

        # Random exploration based on rate
        return random.random() < min(effective_exploration_rate, 0.5)

    def _generate_suggested_approach(
        self,
        experiences: List[Experience],
        patterns: List[Tuple[SuccessfulPattern, float]],
        should_explore: bool,
        context: TaskContext
    ) -> str:
        """Generate a suggested approach based on experience"""
        suggestions = []

        if should_explore:
            suggestions.append("EXPLORATION MODE: Consider trying a new approach.")

        # Best pattern
        if patterns:
            best_pattern, score = patterns[0]
            suggestions.append(f"Recommended pattern: {best_pattern.name}")
            suggestions.append(f"Steps: {' -> '.join(best_pattern.steps[:5])}")
            suggestions.append(f"Success rate: {best_pattern.success_rate:.1%}")

        # Best experience
        successful_exp = [e for e in experiences if e.outcome == Outcome.SUCCESS]
        if successful_exp:
            best_exp = max(successful_exp, key=lambda e: e.quality_score)
            suggestions.append(f"Similar successful task: {best_exp.task_description[:100]}")
            suggestions.append(f"Approach used: {best_exp.approach[:200]}")
            if best_exp.lessons_learned:
                suggestions.append(f"Key lesson: {best_exp.lessons_learned[0]}")

        # Complexity note
        if context.complexity == Complexity.HIGH:
            suggestions.append("NOTE: High complexity - consider breaking down the task.")

        return "\n".join(suggestions) if suggestions else "No specific guidance available."

    def _calculate_guidance_confidence(
        self,
        experiences: List[Experience],
        patterns: List[Tuple[SuccessfulPattern, float]],
        context: TaskContext
    ) -> float:
        """Calculate confidence in the guidance provided"""
        confidence = 0.0

        # Experience contribution
        if experiences:
            successful = [e for e in experiences if e.outcome == Outcome.SUCCESS]
            exp_confidence = len(successful) / len(experiences) * 0.4
            confidence += exp_confidence

        # Pattern contribution
        if patterns:
            best_pattern, score = patterns[0]
            pattern_confidence = best_pattern.success_rate * score * 0.4
            confidence += pattern_confidence

        # Context familiarity (more data = more confidence)
        data_confidence = min(len(experiences) / 10, 1.0) * 0.2
        confidence += data_confidence

        return min(confidence, 1.0)

    # =========================================================================
    # SELF-ATTRIBUTING: Outcome Analysis
    # =========================================================================

    async def analyze_outcome(
        self,
        agent_id: str,
        agent_role: AgentRole,
        task_id: str,
        steps_taken: List[Dict[str, Any]],
        outcome: Outcome,
        quality_score: float,
        duration: int
    ) -> Attribution:
        """
        Analyze the outcome of a task and attribute credit/blame to steps.

        This is the core of Self-Attributing: understanding which
        actions led to success or failure.
        """
        config = self._get_config(agent_id, agent_role)

        # Attribute each step
        step_attributions = []
        for i, step in enumerate(steps_taken[:config.attribution_depth * 3]):
            attribution = self._attribute_step(
                step, i, outcome, quality_score, len(steps_taken)
            )
            step_attributions.append(attribution)

        # Identify key factors
        key_success_factors = [
            attr.step_name for attr in step_attributions
            if attr.contribution > 0.3
        ]
        key_failure_factors = [
            attr.step_name for attr in step_attributions
            if attr.contribution < -0.3
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            step_attributions, outcome, quality_score
        )

        # Calculate total score
        total_score = sum(attr.contribution for attr in step_attributions) / len(step_attributions) if step_attributions else 0

        attribution = Attribution(
            task_id=task_id,
            agent_id=agent_id,
            total_score=total_score,
            attributions=step_attributions,
            key_success_factors=key_success_factors,
            key_failure_factors=key_failure_factors,
            recommendations=recommendations
        )

        # Store the experience
        await self._store_experience_from_attribution(
            agent_id, agent_role, task_id, steps_taken,
            outcome, quality_score, duration, attribution
        )

        return attribution

    def _attribute_step(
        self,
        step: Dict[str, Any],
        index: int,
        outcome: Outcome,
        quality_score: float,
        total_steps: int
    ) -> StepAttribution:
        """Attribute contribution to a single step"""
        step_name = step.get('name', f'Step {index + 1}')
        step_success = step.get('success', True)
        step_duration = step.get('duration', 0)
        step_errors = step.get('errors', [])

        # Base contribution from step success
        if step_success:
            contribution = 0.2 + (quality_score / 100) * 0.3
        else:
            contribution = -0.3 - len(step_errors) * 0.1

        # Adjust based on outcome
        if outcome == Outcome.SUCCESS:
            contribution = abs(contribution)
        elif outcome == Outcome.FAILURE:
            contribution = -abs(contribution)
        else:  # Partial
            contribution *= 0.5

        # Position weight (early steps have more impact)
        position_weight = 1 - (index / total_steps) * 0.3
        contribution *= position_weight

        # Determine if improvement is possible
        could_improve = contribution < 0.5 or step_errors

        return StepAttribution(
            step_name=step_name,
            step_index=index,
            contribution=max(-1, min(1, contribution)),
            confidence=0.7 if step.get('metrics') else 0.5,
            reasoning=self._generate_attribution_reasoning(step, contribution),
            could_improve=could_improve,
            improvement_suggestion=self._suggest_improvement(step) if could_improve else None
        )

    def _generate_attribution_reasoning(
        self,
        step: Dict[str, Any],
        contribution: float
    ) -> str:
        """Generate reasoning for a step's attribution"""
        if contribution > 0.3:
            return f"Step completed successfully with good quality"
        elif contribution > 0:
            return f"Step completed but with room for improvement"
        elif contribution > -0.3:
            return f"Step had minor issues that affected outcome"
        else:
            return f"Step had significant problems: {', '.join(step.get('errors', ['unknown issues']))}"

    def _suggest_improvement(self, step: Dict[str, Any]) -> Optional[str]:
        """Suggest improvement for a step"""
        errors = step.get('errors', [])
        if errors:
            return f"Address issues: {errors[0]}"
        if step.get('duration', 0) > 60000:  # More than 60 seconds
            return "Consider optimizing for faster execution"
        return "Review approach for potential improvements"

    def _generate_recommendations(
        self,
        attributions: List[StepAttribution],
        outcome: Outcome,
        quality_score: float
    ) -> List[str]:
        """Generate recommendations based on attribution analysis"""
        recommendations = []

        # Identify weak steps
        weak_steps = [a for a in attributions if a.contribution < 0.2]
        if weak_steps:
            recommendations.append(
                f"Focus on improving: {', '.join(s.step_name for s in weak_steps[:3])}"
            )

        # Quality-based recommendations
        if quality_score < 70:
            recommendations.append("Consider adding more validation steps")
        if quality_score < 50:
            recommendations.append("Review the overall approach - significant changes may be needed")

        # Outcome-based recommendations
        if outcome == Outcome.FAILURE:
            recommendations.append("Analyze failure patterns and consult similar past failures")
        elif outcome == Outcome.PARTIAL:
            recommendations.append("Identify which aspects succeeded to build on them")

        return recommendations

    async def _store_experience_from_attribution(
        self,
        agent_id: str,
        agent_role: AgentRole,
        task_id: str,
        steps_taken: List[Dict[str, Any]],
        outcome: Outcome,
        quality_score: float,
        duration: int,
        attribution: Attribution
    ):
        """Store an experience based on attribution analysis"""
        # Create key decisions from steps
        key_decisions = []
        for step in steps_taken[:5]:  # Top 5 steps
            if step.get('decision'):
                key_decisions.append(KeyDecision(
                    decision=step.get('decision', step.get('name', 'Unknown')),
                    reasoning=step.get('reasoning', 'Not specified'),
                    alternatives=step.get('alternatives', []),
                    outcome='positive' if step.get('success', True) else 'negative',
                    impact_score=step.get('impact', 0.5)
                ))

        experience = Experience(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            agent_role=agent_role,
            work_type=WorkType.NEW_FEATURE,  # Default, should be passed
            task_description=steps_taken[0].get('name', 'Task') if steps_taken else 'Unknown task',
            approach=' -> '.join(s.get('name', '') for s in steps_taken[:5]),
            outcome=outcome,
            lessons_learned=attribution.recommendations,
            key_decisions=key_decisions,
            duration=duration,
            quality_score=quality_score,
            timestamp=datetime.utcnow(),
            metadata={
                'task_id': task_id,
                'attribution_score': attribution.total_score
            }
        )

        await self.experience_store.add_experience(experience)

    # =========================================================================
    # SELF-QUESTIONING: Learning Task Generation
    # =========================================================================

    async def generate_learning_tasks(
        self,
        agent_id: str,
        agent_role: AgentRole,
        max_tasks: int = 5
    ) -> List[LearningTask]:
        """
        Generate learning tasks based on knowledge gaps.

        This is the core of Self-Questioning: the agent identifies
        what it needs to learn and creates tasks to fill those gaps.
        """
        config = self._get_config(agent_id, agent_role)
        if not config.self_questioning_enabled:
            return []

        learning_tasks = []

        # 1. Identify knowledge gaps from failure patterns
        failure_gaps = await self._identify_failure_gaps(agent_id, agent_role)
        for gap in failure_gaps[:2]:
            task = LearningTask(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                work_type=gap['work_type'],
                description=f"Practice task: {gap['description']}",
                learning_goal=f"Improve handling of: {gap['failure_type']}",
                expected_difficulty=Complexity.MEDIUM,
                knowledge_gap=gap['gap'],
                created_at=datetime.utcnow()
            )
            learning_tasks.append(task)

        # 2. Identify under-explored work types
        underexplored = await self._identify_underexplored_areas(agent_id, agent_role)
        for area in underexplored[:2]:
            task = LearningTask(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                work_type=area['work_type'],
                description=f"Exploration task: {area['description']}",
                learning_goal=f"Gain experience in: {area['work_type'].value}",
                expected_difficulty=Complexity.LOW,
                knowledge_gap=area['gap'],
                created_at=datetime.utcnow()
            )
            learning_tasks.append(task)

        # 3. Generate edge case exploration tasks
        edge_cases = self._generate_edge_case_tasks(agent_role)
        for edge_case in edge_cases[:1]:
            task = LearningTask(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                work_type=edge_case['work_type'],
                description=f"Edge case exploration: {edge_case['description']}",
                learning_goal=edge_case['goal'],
                expected_difficulty=Complexity.HIGH,
                knowledge_gap="Edge case handling",
                created_at=datetime.utcnow()
            )
            learning_tasks.append(task)

        # Store for tracking
        self._learning_tasks[agent_id] = learning_tasks[:max_tasks]

        return learning_tasks[:max_tasks]

    async def _identify_failure_gaps(
        self,
        agent_id: str,
        agent_role: AgentRole
    ) -> List[Dict[str, Any]]:
        """Identify knowledge gaps from failure patterns"""
        # Get recent failures
        experiences = await self.experience_store.get_agent_experiences(
            agent_id,
            outcome=Outcome.FAILURE,
            limit=20
        )

        gaps = []
        failure_types: Dict[str, int] = {}

        for exp in experiences:
            # Count failure types by work type
            key = f"{exp.work_type.value}"
            failure_types[key] = failure_types.get(key, 0) + 1

        # Create gaps from most common failures
        for work_type_str, count in sorted(failure_types.items(), key=lambda x: -x[1]):
            if count >= 2:
                gaps.append({
                    'work_type': WorkType(work_type_str),
                    'description': f"Handle {work_type_str.replace('_', ' ').lower()} tasks better",
                    'failure_type': 'repeated failures',
                    'gap': f"Failed {count} times in {work_type_str}"
                })

        return gaps

    async def _identify_underexplored_areas(
        self,
        agent_id: str,
        agent_role: AgentRole
    ) -> List[Dict[str, Any]]:
        """Identify work types with limited experience"""
        # Get all experiences
        experiences = await self.experience_store.get_agent_experiences(agent_id, limit=100)

        # Count by work type
        work_type_counts: Dict[WorkType, int] = {}
        for wt in WorkType:
            work_type_counts[wt] = 0

        for exp in experiences:
            work_type_counts[exp.work_type] = work_type_counts.get(exp.work_type, 0) + 1

        # Find underexplored
        underexplored = []
        for wt, count in work_type_counts.items():
            if count < 5:  # Less than 5 experiences
                underexplored.append({
                    'work_type': wt,
                    'description': f"Explore {wt.value.replace('_', ' ').lower()} scenarios",
                    'gap': f"Only {count} experiences in this area"
                })

        return sorted(underexplored, key=lambda x: work_type_counts[x['work_type']])

    def _generate_edge_case_tasks(
        self,
        agent_role: AgentRole
    ) -> List[Dict[str, Any]]:
        """Generate edge case exploration tasks based on agent role"""
        edge_cases = {
            AgentRole.FEATURE_ARCHITECT: [
                {'work_type': WorkType.NEW_FEATURE, 'description': 'Design microservices with circular dependencies', 'goal': 'Handle complex dependency scenarios'},
                {'work_type': WorkType.NEW_FEATURE, 'description': 'Design system with conflicting requirements', 'goal': 'Balance trade-offs'},
            ],
            AgentRole.BUG_HUNTER: [
                {'work_type': WorkType.BUG, 'description': 'Debug race condition in async code', 'goal': 'Master concurrent debugging'},
                {'work_type': WorkType.BUG, 'description': 'Find memory leak in long-running process', 'goal': 'Improve memory analysis skills'},
            ],
            AgentRole.QUALITY_INSPECTOR: [
                {'work_type': WorkType.QUALITY_AUDIT, 'description': 'Audit code with intentional vulnerabilities', 'goal': 'Sharpen security detection'},
                {'work_type': WorkType.QUALITY_AUDIT, 'description': 'Review performance-critical code', 'goal': 'Improve performance analysis'},
            ],
        }

        return edge_cases.get(agent_role, [
            {'work_type': WorkType.ENHANCEMENT, 'description': 'Handle ambiguous requirements', 'goal': 'Improve requirement clarification'}
        ])

    # =========================================================================
    # PERFORMANCE METRICS
    # =========================================================================

    async def get_performance_metrics(
        self,
        agent_id: str,
        agent_role: AgentRole,
        days: int = 30
    ) -> PerformanceMetrics:
        """Get performance metrics for an agent"""
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # Get experiences for the period
        all_experiences = await self.experience_store.get_agent_experiences(agent_id, limit=500)
        experiences = [
            e for e in all_experiences
            if e.timestamp >= period_start
        ]

        # Get summary from experience store
        summary = await self.experience_store.get_agent_performance_summary(agent_id)
        quality_trend = await self.experience_store.get_quality_trend(agent_id, days=days)

        # Calculate metrics
        total = len(experiences)
        successful = sum(1 for e in experiences if e.outcome == Outcome.SUCCESS)
        partial = sum(1 for e in experiences if e.outcome == Outcome.PARTIAL)
        failed = sum(1 for e in experiences if e.outcome == Outcome.FAILURE)

        avg_quality = sum(e.quality_score for e in experiences) / total if total else 0
        avg_duration = sum(e.duration for e in experiences) / total if total else 0

        metrics = PerformanceMetrics(
            agent_id=agent_id,
            agent_role=agent_role,
            period_start=period_start,
            period_end=period_end,
            total_tasks=total,
            successful_tasks=successful,
            partial_tasks=partial,
            failed_tasks=failed,
            average_quality_score=avg_quality,
            quality_trend=quality_trend.get('trend', 'stable'),
            average_duration=avg_duration,
            experiences_generated=total
        )

        # Cache metrics
        self._agent_metrics[agent_id] = metrics

        return metrics

    # =========================================================================
    # CONFIG MANAGEMENT
    # =========================================================================

    def _get_config(
        self,
        agent_id: str,
        agent_role: AgentRole
    ) -> EvolutionConfig:
        """Get evolution config for an agent"""
        if agent_id in self._agent_configs:
            return self._agent_configs[agent_id]
        return self.DEFAULT_CONFIGS.get(agent_role, EvolutionConfig())

    def update_config(
        self,
        agent_id: str,
        config: EvolutionConfig
    ):
        """Update evolution config for an agent"""
        self._agent_configs[agent_id] = config
        logger.info(f"Updated evolution config for agent {agent_id}")

    async def adapt_config(
        self,
        agent_id: str,
        agent_role: AgentRole
    ) -> EvolutionConfig:
        """Adapt evolution config based on performance"""
        metrics = await self.get_performance_metrics(agent_id, agent_role)
        current_config = self._get_config(agent_id, agent_role)

        # Adapt based on performance
        new_config = EvolutionConfig(
            learning_rate=current_config.learning_rate,
            experience_weight=current_config.experience_weight,
            exploration_rate=current_config.exploration_rate,
            attribution_depth=current_config.attribution_depth,
            min_experience_confidence=current_config.min_experience_confidence,
            max_experiences_to_consider=current_config.max_experiences_to_consider,
            self_questioning_enabled=current_config.self_questioning_enabled,
            self_navigating_enabled=current_config.self_navigating_enabled,
            self_attributing_enabled=current_config.self_attributing_enabled
        )

        # If success rate is low, increase exploration
        if metrics.success_rate < 0.7:
            new_config.exploration_rate = min(0.4, current_config.exploration_rate + 0.05)
            new_config.learning_rate = min(0.3, current_config.learning_rate + 0.02)

        # If success rate is high, exploit more
        if metrics.success_rate > 0.9:
            new_config.exploration_rate = max(0.1, current_config.exploration_rate - 0.02)
            new_config.experience_weight = min(0.95, current_config.experience_weight + 0.02)

        # If quality is declining, increase attribution depth
        if metrics.quality_trend == 'declining':
            new_config.attribution_depth = min(5, current_config.attribution_depth + 1)

        self._agent_configs[agent_id] = new_config
        return new_config


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_evolution_service: Optional[AgentEvolutionService] = None


def get_evolution_service() -> AgentEvolutionService:
    """Get or create the evolution service singleton"""
    global _evolution_service
    if _evolution_service is None:
        _evolution_service = AgentEvolutionService()
    return _evolution_service
