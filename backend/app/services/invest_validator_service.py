"""
INVEST Validator Service - Week 85

Validates user stories against INVEST criteria:
- Independent: Story can be developed independently
- Negotiable: Details can be negotiated
- Valuable: Delivers value to user/customer
- Estimable: Can be estimated by the team
- Small: Can be completed in one sprint
- Testable: Has clear acceptance criteria

Also validates SMART criteria for tasks:
- Specific: Clear and unambiguous
- Measurable: Has success criteria
- Achievable: Realistic given resources
- Relevant: Aligns with story/feature
- Time-bound: Has duration estimate
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from uuid import uuid4
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ValidationLevel(str, Enum):
    """Validation strictness level."""
    LENIENT = "lenient"      # Basic checks only
    STANDARD = "standard"    # Normal validation
    STRICT = "strict"        # All criteria must pass


class CriterionStatus(str, Enum):
    """Status of individual criterion."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ItemType(str, Enum):
    """Type of item being validated."""
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CriterionResult:
    """Result of validating a single criterion."""
    criterion: str
    status: CriterionStatus
    score: float  # 0.0 to 1.0
    feedback: str
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion": self.criterion,
            "status": self.status.value,
            "score": self.score,
            "feedback": self.feedback,
            "suggestions": self.suggestions,
        }


@dataclass
class INVESTValidationResult:
    """Complete INVEST validation result for a story."""
    id: str = field(default_factory=lambda: str(uuid4()))
    item_id: str = ""
    item_type: ItemType = ItemType.STORY
    title: str = ""

    # Individual criteria results
    independent: Optional[CriterionResult] = None
    negotiable: Optional[CriterionResult] = None
    valuable: Optional[CriterionResult] = None
    estimable: Optional[CriterionResult] = None
    small: Optional[CriterionResult] = None
    testable: Optional[CriterionResult] = None

    # Overall scores
    overall_score: float = 0.0
    is_valid: bool = False
    validation_level: ValidationLevel = ValidationLevel.STANDARD

    # Metadata
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "item_type": self.item_type.value,
            "title": self.title,
            "criteria": {
                "independent": self.independent.to_dict() if self.independent else None,
                "negotiable": self.negotiable.to_dict() if self.negotiable else None,
                "valuable": self.valuable.to_dict() if self.valuable else None,
                "estimable": self.estimable.to_dict() if self.estimable else None,
                "small": self.small.to_dict() if self.small else None,
                "testable": self.testable.to_dict() if self.testable else None,
            },
            "overall_score": self.overall_score,
            "is_valid": self.is_valid,
            "validation_level": self.validation_level.value,
            "validated_at": self.validated_at.isoformat(),
            "errors": self.errors,
        }

    def get_failing_criteria(self) -> List[str]:
        """Get list of failing criteria."""
        failing = []
        for name, result in [
            ("independent", self.independent),
            ("negotiable", self.negotiable),
            ("valuable", self.valuable),
            ("estimable", self.estimable),
            ("small", self.small),
            ("testable", self.testable),
        ]:
            if result and result.status == CriterionStatus.FAIL:
                failing.append(name)
        return failing


@dataclass
class SMARTValidationResult:
    """SMART validation result for tasks."""
    id: str = field(default_factory=lambda: str(uuid4()))
    task_id: str = ""
    title: str = ""

    specific: Optional[CriterionResult] = None
    measurable: Optional[CriterionResult] = None
    achievable: Optional[CriterionResult] = None
    relevant: Optional[CriterionResult] = None
    time_bound: Optional[CriterionResult] = None

    overall_score: float = 0.0
    is_valid: bool = False
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "criteria": {
                "specific": self.specific.to_dict() if self.specific else None,
                "measurable": self.measurable.to_dict() if self.measurable else None,
                "achievable": self.achievable.to_dict() if self.achievable else None,
                "relevant": self.relevant.to_dict() if self.relevant else None,
                "time_bound": self.time_bound.to_dict() if self.time_bound else None,
            },
            "overall_score": self.overall_score,
            "is_valid": self.is_valid,
            "validated_at": self.validated_at.isoformat(),
        }


@dataclass
class BatchValidationResult:
    """Result of validating multiple items."""
    total_items: int = 0
    valid_items: int = 0
    invalid_items: int = 0
    average_score: float = 0.0
    results: List[INVESTValidationResult] = field(default_factory=list)
    summary_by_criterion: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_items": self.total_items,
            "valid_items": self.valid_items,
            "invalid_items": self.invalid_items,
            "average_score": self.average_score,
            "pass_rate": self.valid_items / self.total_items if self.total_items > 0 else 0,
            "results": [r.to_dict() for r in self.results],
            "summary_by_criterion": self.summary_by_criterion,
        }


@dataclass
class CausalContext:
    """
    Week 125: CiRA causal context for enhanced INVEST validation.

    Provides causal dependency information to improve validation accuracy:
    - Independent check: Uses causal graph to identify blocking dependencies
    - Estimable check: Adds dependency overhead factor
    - Testable check: Uses CiRA-generated test case suggestions
    """
    # Story dependencies from CiRA graph
    blocks: List[str] = field(default_factory=list)  # Stories this story blocks
    blocked_by: List[str] = field(default_factory=list)  # Stories blocking this one
    causes: List[str] = field(default_factory=list)  # Stories this one enables
    caused_by: List[str] = field(default_factory=list)  # Stories that enable this
    depends_on: List[str] = field(default_factory=list)  # Dependencies
    depended_by: List[str] = field(default_factory=list)  # Dependents

    # Graph metrics
    is_root_node: bool = False  # No incoming dependencies
    is_leaf_node: bool = False  # No outgoing dependencies
    critical_path_position: Optional[int] = None  # Position in critical path
    total_dependency_depth: int = 0  # How deep in dependency chain

    # CiRA-generated test suggestions
    suggested_tests: List[Dict[str, str]] = field(default_factory=list)

    # Session reference
    cira_session_id: Optional[str] = None

    @property
    def total_dependencies(self) -> int:
        """Total number of dependencies (blocking + enabling)."""
        return len(self.blocked_by) + len(self.caused_by) + len(self.depends_on)

    @property
    def total_dependents(self) -> int:
        """Total number of dependent stories."""
        return len(self.blocks) + len(self.causes) + len(self.depended_by)

    @property
    def dependency_score_impact(self) -> float:
        """
        Calculate the impact on the Independent score.

        Returns value between 0 (no impact) and 0.5 (max penalty).
        """
        if self.is_root_node:
            return 0.0  # Root nodes are fully independent

        # Each blocker reduces score significantly
        blocker_penalty = len(self.blocked_by) * 0.15

        # Dependencies have moderate impact
        dependency_penalty = len(self.depends_on) * 0.10

        # Being in critical path is a concern
        critical_path_penalty = 0.1 if self.critical_path_position is not None else 0.0

        return min(0.5, blocker_penalty + dependency_penalty + critical_path_penalty)


# =============================================================================
# INVEST VALIDATOR SERVICE
# =============================================================================

class INVESTValidatorService:
    """
    Validates user stories against INVEST criteria.

    Usage:
        validator = INVESTValidatorService()

        result = await validator.validate_story({
            "title": "User Login",
            "description": "As a user, I want to login...",
            "acceptance_criteria": ["Can login with email", "Session persists"],
            "story_points": 5,
        })

        if result.is_valid:
            print("Story is INVEST-compliant!")
        else:
            print(f"Failing criteria: {result.get_failing_criteria()}")
    """

    # Thresholds for validation levels
    THRESHOLDS = {
        ValidationLevel.LENIENT: 0.5,
        ValidationLevel.STANDARD: 0.7,
        ValidationLevel.STRICT: 0.85,
    }

    # Criterion weights
    WEIGHTS = {
        "independent": 0.15,
        "negotiable": 0.10,
        "valuable": 0.25,
        "estimable": 0.15,
        "small": 0.15,
        "testable": 0.20,
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def validate_story(
        self,
        story: Dict[str, Any],
        level: ValidationLevel = ValidationLevel.STANDARD,
        context: Optional[Dict[str, Any]] = None,
        causal_context: Optional[CausalContext] = None,  # Week 125: CiRA integration
    ) -> INVESTValidationResult:
        """
        Validate a single story against INVEST criteria.

        Args:
            story: Story dict with title, description, acceptance_criteria, etc.
            level: Validation strictness
            context: Additional context (related stories, sprint info, etc.)
            causal_context: Week 125 - CiRA causal dependency info

        Returns:
            INVESTValidationResult with all criteria scores
        """
        result = INVESTValidationResult(
            item_id=story.get("id", ""),
            item_type=ItemType.STORY,
            title=story.get("title", ""),
            validation_level=level,
        )

        try:
            # Validate each criterion (Week 125: pass causal_context where applicable)
            result.independent = self._validate_independent(story, context, causal_context)
            result.negotiable = self._validate_negotiable(story)
            result.valuable = self._validate_valuable(story)
            result.estimable = self._validate_estimable(story, causal_context)
            result.small = self._validate_small(story)
            result.testable = self._validate_testable(story, causal_context)

            # Calculate overall score
            result.overall_score = self._calculate_overall_score(result)

            # Determine validity based on level
            threshold = self.THRESHOLDS[level]
            result.is_valid = result.overall_score >= threshold

        except Exception as e:
            logger.exception("Story validation failed")
            result.errors.append(str(e))

        return result

    async def validate_batch(
        self,
        stories: List[Dict[str, Any]],
        level: ValidationLevel = ValidationLevel.STANDARD,
    ) -> BatchValidationResult:
        """
        Validate multiple stories and aggregate results.

        Args:
            stories: List of story dicts
            level: Validation strictness

        Returns:
            BatchValidationResult with aggregated statistics
        """
        batch_result = BatchValidationResult()
        batch_result.total_items = len(stories)

        criterion_counts = {
            criterion: {"pass": 0, "warn": 0, "fail": 0}
            for criterion in self.WEIGHTS.keys()
        }

        for story in stories:
            result = await self.validate_story(story, level)
            batch_result.results.append(result)

            if result.is_valid:
                batch_result.valid_items += 1
            else:
                batch_result.invalid_items += 1

            # Count criterion statuses
            for criterion_name in self.WEIGHTS.keys():
                criterion_result = getattr(result, criterion_name)
                if criterion_result:
                    status = criterion_result.status.value
                    criterion_counts[criterion_name][status] += 1

        # Calculate average score
        if batch_result.results:
            batch_result.average_score = sum(
                r.overall_score for r in batch_result.results
            ) / len(batch_result.results)

        batch_result.summary_by_criterion = criterion_counts

        return batch_result

    async def validate_task(
        self,
        task: Dict[str, Any],
        parent_story: Optional[Dict[str, Any]] = None,
    ) -> SMARTValidationResult:
        """
        Validate a task against SMART criteria.

        Args:
            task: Task dict with title, description, duration, etc.
            parent_story: Optional parent story for relevance check

        Returns:
            SMARTValidationResult
        """
        result = SMARTValidationResult(
            task_id=task.get("id", ""),
            title=task.get("title", ""),
        )

        try:
            result.specific = self._validate_specific(task)
            result.measurable = self._validate_measurable(task)
            result.achievable = self._validate_achievable(task)
            result.relevant = self._validate_relevant(task, parent_story)
            result.time_bound = self._validate_time_bound(task)

            # Calculate overall score
            scores = [
                r.score for r in [
                    result.specific, result.measurable, result.achievable,
                    result.relevant, result.time_bound
                ] if r
            ]
            result.overall_score = sum(scores) / len(scores) if scores else 0.0
            result.is_valid = result.overall_score >= 0.7

        except Exception as e:
            logger.exception("Task validation failed")

        return result

    # =========================================================================
    # INVEST CRITERION VALIDATORS
    # =========================================================================

    def _validate_independent(
        self,
        story: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        causal_context: Optional[CausalContext] = None,  # Week 125: CiRA integration
    ) -> CriterionResult:
        """
        Check if story can be developed independently.

        Checks:
        - No explicit dependencies mentioned
        - Self-contained description
        - No "after X is done" phrases
        - Week 125: Uses CiRA causal graph for accurate dependency detection
        """
        description = story.get("description", "").lower()
        title = story.get("title", "").lower()
        dependencies = story.get("dependencies", [])

        score = 1.0
        feedback = "Story appears independent"
        suggestions = []

        # Check for explicit dependencies
        if dependencies:
            score -= 0.3
            feedback = f"Has {len(dependencies)} explicit dependencies"
            suggestions.append("Consider splitting or reordering to reduce dependencies")

        # Check for dependency keywords
        dependency_patterns = [
            r"after .* is done",
            r"depends on",
            r"requires .* first",
            r"blocked by",
            r"waiting for",
            r"once .* is complete",
        ]

        for pattern in dependency_patterns:
            if re.search(pattern, description) or re.search(pattern, title):
                score -= 0.2
                suggestions.append(f"Remove dependency language: '{pattern}'")

        # Check context for related stories
        if context and context.get("related_stories"):
            related = context["related_stories"]
            if len(related) > 3:
                score -= 0.1
                suggestions.append("Consider if all related stories are necessary")

        # Week 125: Apply CiRA causal dependency analysis
        if causal_context:
            # Apply causal dependency penalty
            causal_penalty = causal_context.dependency_score_impact
            score -= causal_penalty

            if causal_context.blocked_by:
                blockers = ", ".join(causal_context.blocked_by[:3])
                suggestions.append(
                    f"CiRA detected blocking dependencies: {blockers}. "
                    "Complete these stories first."
                )

            if causal_context.is_root_node:
                score += 0.1  # Bonus for root nodes
                feedback = "Story is a root node with no incoming dependencies"

            if causal_context.critical_path_position is not None:
                suggestions.append(
                    f"Story is on critical path (position {causal_context.critical_path_position}). "
                    "Prioritize to avoid blocking downstream work."
                )

        score = max(0.0, min(1.0, score))
        status = self._score_to_status(score)

        if score >= 0.8:
            feedback = "Story is independent and self-contained"
        elif score >= 0.5:
            feedback = "Story has some dependencies but can proceed"
        else:
            feedback = "Story has significant dependencies"

        return CriterionResult(
            criterion="independent",
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
        )

    def _validate_negotiable(self, story: Dict[str, Any]) -> CriterionResult:
        """
        Check if story details are negotiable.

        Checks:
        - Description focuses on WHAT, not HOW
        - No implementation details
        - Room for discussion
        """
        description = story.get("description", "").lower()

        score = 1.0
        feedback = "Story is negotiable"
        suggestions = []

        # Check for implementation details
        implementation_keywords = [
            "use react", "implement with", "sql query", "api endpoint",
            "database table", "function called", "class named",
            "specific color", "exact position", "pixel",
            "must use", "required technology",
        ]

        for keyword in implementation_keywords:
            if keyword in description:
                score -= 0.15
                suggestions.append(f"Remove implementation detail: '{keyword}'")

        # Check if using user story format
        if not re.search(r"as a .*, i want", description):
            score -= 0.1
            suggestions.append("Consider using 'As a [user], I want [goal]' format")

        # Check for overly specific language
        if len(description) > 500:
            score -= 0.1
            suggestions.append("Description is very detailed - consider leaving room for negotiation")

        score = max(0.0, score)
        status = self._score_to_status(score)

        if score >= 0.8:
            feedback = "Story focuses on goals, not implementation"
        elif score >= 0.5:
            feedback = "Story has some implementation details"
        else:
            feedback = "Story is too prescriptive"

        return CriterionResult(
            criterion="negotiable",
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
        )

    def _validate_valuable(self, story: Dict[str, Any]) -> CriterionResult:
        """
        Check if story delivers value to user/customer.

        Checks:
        - Clear user benefit
        - Business value statement
        - Not purely technical
        """
        description = story.get("description", "").lower()
        title = story.get("title", "").lower()

        score = 0.5  # Start neutral
        feedback = "Value proposition unclear"
        suggestions = []

        # Check for value indicators
        value_keywords = [
            "so that", "in order to", "to be able to",
            "save time", "reduce", "improve", "enable",
            "user can", "customer will", "business value",
        ]

        for keyword in value_keywords:
            if keyword in description:
                score += 0.1

        # Check for user-centric language
        if re.search(r"as a (user|customer|admin|manager)", description):
            score += 0.2

        # Penalize purely technical stories
        technical_only = [
            "refactor", "migrate database", "update dependency",
            "fix technical debt", "improve performance",
        ]

        is_technical = any(kw in title or kw in description for kw in technical_only)
        if is_technical and "so that" not in description:
            score -= 0.2
            suggestions.append("Add business justification with 'so that [benefit]'")

        score = min(1.0, max(0.0, score))
        status = self._score_to_status(score)

        if score >= 0.8:
            feedback = "Clear value proposition for user/business"
        elif score >= 0.5:
            feedback = "Some value indicated but could be clearer"
        else:
            feedback = "No clear user/business value"
            suggestions.append("Add 'so that [user benefit]' to clarify value")

        return CriterionResult(
            criterion="valuable",
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
        )

    def _validate_estimable(
        self,
        story: Dict[str, Any],
        causal_context: Optional[CausalContext] = None,  # Week 125: CiRA integration
    ) -> CriterionResult:
        """
        Check if story can be estimated by the team.

        Checks:
        - Sufficient detail for estimation
        - Clear scope
        - Has story points or FP estimate
        - Week 125: Considers dependency overhead from CiRA analysis
        """
        description = story.get("description", "")
        story_points = story.get("story_points")
        function_points = story.get("function_points")
        acceptance_criteria = story.get("acceptance_criteria", [])

        score = 0.5
        feedback = "Story may be difficult to estimate"
        suggestions = []

        # Has estimate
        if story_points or function_points:
            score += 0.3

        # Has acceptance criteria
        if acceptance_criteria and len(acceptance_criteria) >= 2:
            score += 0.2
        elif not acceptance_criteria:
            suggestions.append("Add acceptance criteria to clarify scope")

        # Description length (not too short, not too long)
        desc_len = len(description)
        if 50 <= desc_len <= 300:
            score += 0.1
        elif desc_len < 50:
            score -= 0.1
            suggestions.append("Add more detail to enable estimation")
        elif desc_len > 500:
            score -= 0.1
            suggestions.append("Consider splitting - too much detail may hide complexity")

        # Check for vague language
        vague_patterns = [
            r"etc\.?", r"and more", r"various", r"several",
            r"some kind of", r"something like", r"maybe",
        ]

        for pattern in vague_patterns:
            if re.search(pattern, description.lower()):
                score -= 0.1
                suggestions.append(f"Remove vague language: '{pattern}'")

        # Week 125: CiRA dependency overhead analysis
        if causal_context:
            dep_count = causal_context.total_dependencies
            if dep_count > 0:
                # Dependencies add estimation uncertainty
                overhead_penalty = min(0.2, dep_count * 0.05)
                score -= overhead_penalty
                suggestions.append(
                    f"CiRA detected {dep_count} dependencies. "
                    "Add 15-20% buffer to estimate for coordination overhead."
                )

            if causal_context.total_dependency_depth > 2:
                score -= 0.1
                suggestions.append(
                    f"Story is {causal_context.total_dependency_depth} levels deep "
                    "in dependency chain. Consider additional risk buffer."
                )

            # Having dependents improves estimability (well-understood scope)
            if causal_context.total_dependents > 0 and score < 0.8:
                score += 0.05
                feedback = "Story scope is clear from its downstream dependents"

        score = min(1.0, max(0.0, score))
        status = self._score_to_status(score)

        if score >= 0.8:
            feedback = "Story is well-defined and estimable"
        elif score >= 0.5:
            feedback = "Story can be estimated with some assumptions"

        return CriterionResult(
            criterion="estimable",
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
        )

    def _validate_small(self, story: Dict[str, Any]) -> CriterionResult:
        """
        Check if story can be completed in one sprint.

        Checks:
        - Story points within range
        - Not too many acceptance criteria
        - Scope indicators
        """
        story_points = story.get("story_points", 0)
        acceptance_criteria = story.get("acceptance_criteria", [])
        description = story.get("description", "").lower()

        score = 1.0
        feedback = "Story size is appropriate"
        suggestions = []

        # Story points check (1-8 ideal, 13 max)
        if story_points:
            if story_points <= 5:
                score = 1.0
            elif story_points <= 8:
                score = 0.8
            elif story_points <= 13:
                score = 0.5
                suggestions.append("Consider splitting stories > 8 points")
            else:
                score = 0.2
                suggestions.append("Story is too large - split into smaller stories")

        # Acceptance criteria count
        ac_count = len(acceptance_criteria)
        if ac_count > 8:
            score -= 0.2
            suggestions.append(f"Too many acceptance criteria ({ac_count}) - consider splitting")

        # Check for "epic-like" language
        epic_patterns = [
            r"complete system", r"full implementation",
            r"all features", r"entire module",
        ]

        for pattern in epic_patterns:
            if re.search(pattern, description):
                score -= 0.2
                suggestions.append("Scope seems too large for a single story")

        score = max(0.0, score)
        status = self._score_to_status(score)

        if score >= 0.8:
            feedback = "Story is appropriately sized for a sprint"
        elif score >= 0.5:
            feedback = "Story may be large but manageable"
        else:
            feedback = "Story is too large - should be split"

        return CriterionResult(
            criterion="small",
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
        )

    def _validate_testable(
        self,
        story: Dict[str, Any],
        causal_context: Optional[CausalContext] = None,
    ) -> CriterionResult:
        """
        Check if story has clear acceptance criteria.

        Checks:
        - Has acceptance criteria
        - Criteria are specific and measurable
        - Clear success/failure conditions
        - Week 125: CiRA-generated test suggestions

        Args:
            story: Story dictionary
            causal_context: Optional CiRA causal context with test suggestions
        """
        acceptance_criteria = story.get("acceptance_criteria", [])
        description = story.get("description", "")

        score = 0.0
        feedback = "Story lacks acceptance criteria"
        suggestions = []

        # Has acceptance criteria
        if acceptance_criteria:
            score = 0.5 + (min(len(acceptance_criteria), 5) * 0.1)

            # Check quality of criteria
            good_criteria = 0
            for criterion in acceptance_criteria:
                criterion_lower = criterion.lower()

                # Check for measurable language
                measurable_patterns = [
                    r"should", r"must", r"can", r"is able to",
                    r"displays", r"shows", r"returns", r"validates",
                ]

                if any(re.search(p, criterion_lower) for p in measurable_patterns):
                    good_criteria += 1

            if good_criteria >= len(acceptance_criteria) * 0.8:
                score += 0.1
            else:
                suggestions.append("Make acceptance criteria more specific and measurable")

        else:
            suggestions.append("Add acceptance criteria (Given/When/Then format recommended)")

            # Check if description has implicit criteria
            if "should" in description.lower() or "must" in description.lower():
                score = 0.3
                suggestions.append("Extract 'should' statements as acceptance criteria")

        # Week 125: CiRA test suggestions enhancement
        if causal_context:
            cira_tests = causal_context.suggested_tests

            if cira_tests:
                # CiRA has provided test suggestions based on causal analysis
                score += 0.1  # Bonus for having causal test coverage

                # Add CiRA-generated test suggestions
                for test in cira_tests[:3]:  # Limit to top 3 suggestions
                    test_type = test.get("type", "unit")
                    test_desc = test.get("description", "")
                    if test_desc:
                        suggestions.append(
                            f"[CiRA] Add {test_type} test: {test_desc}"
                        )

                # Check if acceptance criteria cover causal dependencies
                if causal_context.total_dependencies > 0:
                    # Story has dependencies - should test the causal chain
                    dependency_coverage = self._check_causal_test_coverage(
                        acceptance_criteria, causal_context
                    )
                    if dependency_coverage < 0.5:
                        suggestions.append(
                            f"[CiRA] Story has {causal_context.total_dependencies} dependencies - "
                            "add integration tests for causal chain"
                        )
                    else:
                        score += 0.05  # Bonus for covering dependencies in tests

                # Check if leaf nodes have edge case tests
                if causal_context.is_leaf_node:
                    suggestions.append(
                        "[CiRA] Leaf node story - ensure edge case and boundary tests"
                    )

                # Check if root nodes have setup/prerequisite tests
                if causal_context.is_root_node:
                    suggestions.append(
                        "[CiRA] Root node story - include prerequisite and setup validation tests"
                    )

        score = min(1.0, max(0.0, score))
        status = self._score_to_status(score)

        if score >= 0.8:
            feedback = "Story has clear, testable acceptance criteria"
            if causal_context and causal_context.suggested_tests:
                feedback += " with CiRA causal test coverage"
        elif score >= 0.5:
            feedback = "Acceptance criteria present but could be more specific"

        return CriterionResult(
            criterion="testable",
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
        )

    def _check_causal_test_coverage(
        self,
        acceptance_criteria: List[str],
        causal_context: CausalContext,
    ) -> float:
        """
        Week 125: Check if acceptance criteria cover causal dependencies.

        Returns coverage ratio (0.0 to 1.0).
        """
        if not acceptance_criteria or not causal_context:
            return 0.0

        # Collect all dependency story IDs
        all_dependencies = set(
            causal_context.blocks +
            causal_context.blocked_by +
            causal_context.depends_on +
            causal_context.depended_by
        )

        if not all_dependencies:
            return 1.0  # No dependencies to cover

        # Check how many dependencies are mentioned in acceptance criteria
        criteria_text = " ".join(acceptance_criteria).lower()
        covered = 0

        # Look for references to dependencies in criteria
        dependency_patterns = [
            "after", "before", "when", "requires", "depends on",
            "following", "prerequisite", "setup", "given that",
            "integration", "chain", "workflow", "sequence"
        ]

        for pattern in dependency_patterns:
            if pattern in criteria_text:
                covered += 1

        # Normalize coverage ratio
        coverage = min(1.0, covered / max(len(all_dependencies), 1))
        return coverage

    # =========================================================================
    # SMART CRITERION VALIDATORS (for Tasks)
    # =========================================================================

    def _validate_specific(self, task: Dict[str, Any]) -> CriterionResult:
        """Check if task is specific and unambiguous."""
        title = task.get("title", "")
        description = task.get("description", "")

        score = 0.5
        suggestions = []

        # Check title specificity
        if len(title) >= 10 and len(title) <= 80:
            score += 0.2

        # Check for action verbs
        action_verbs = ["create", "implement", "add", "update", "fix", "remove", "configure"]
        if any(title.lower().startswith(verb) for verb in action_verbs):
            score += 0.2

        # Check for vague terms
        vague_terms = ["stuff", "things", "handle", "deal with", "work on"]
        if any(term in title.lower() or term in description.lower() for term in vague_terms):
            score -= 0.2
            suggestions.append("Use more specific action verbs")

        score = min(1.0, max(0.0, score))
        status = self._score_to_status(score)

        return CriterionResult(
            criterion="specific",
            status=status,
            score=score,
            feedback="Task is specific" if score >= 0.7 else "Task could be more specific",
            suggestions=suggestions,
        )

    def _validate_measurable(self, task: Dict[str, Any]) -> CriterionResult:
        """Check if task has measurable success criteria."""
        description = task.get("description", "")
        done_criteria = task.get("done_criteria", [])

        score = 0.5
        suggestions = []

        if done_criteria:
            score += 0.3
        else:
            suggestions.append("Add 'Definition of Done' criteria")

        # Check for measurable language
        if any(kw in description.lower() for kw in ["test", "verify", "confirm", "check"]):
            score += 0.2

        score = min(1.0, max(0.0, score))
        status = self._score_to_status(score)

        return CriterionResult(
            criterion="measurable",
            status=status,
            score=score,
            feedback="Task is measurable" if score >= 0.7 else "Add measurable criteria",
            suggestions=suggestions,
        )

    def _validate_achievable(self, task: Dict[str, Any]) -> CriterionResult:
        """Check if task is achievable given resources."""
        hours = task.get("estimated_hours", 0)
        complexity = task.get("complexity", "medium")

        score = 0.7
        suggestions = []

        # Check duration
        if hours:
            if hours <= 8:
                score = 1.0
            elif hours <= 16:
                score = 0.8
            else:
                score = 0.5
                suggestions.append("Task may be too large - consider splitting")

        status = self._score_to_status(score)

        return CriterionResult(
            criterion="achievable",
            status=status,
            score=score,
            feedback="Task is achievable" if score >= 0.7 else "Task may be too complex",
            suggestions=suggestions,
        )

    def _validate_relevant(
        self,
        task: Dict[str, Any],
        parent_story: Optional[Dict[str, Any]] = None,
    ) -> CriterionResult:
        """Check if task is relevant to parent story."""
        score = 0.7
        suggestions = []

        if parent_story:
            # Check if task title relates to story
            story_keywords = parent_story.get("title", "").lower().split()
            task_title = task.get("title", "").lower()

            matching = sum(1 for kw in story_keywords if kw in task_title and len(kw) > 3)
            if matching > 0:
                score = 1.0
            else:
                score = 0.6
                suggestions.append("Ensure task aligns with parent story")
        else:
            suggestions.append("Link task to parent story for relevance check")

        status = self._score_to_status(score)

        return CriterionResult(
            criterion="relevant",
            status=status,
            score=score,
            feedback="Task is relevant" if score >= 0.7 else "Check task relevance",
            suggestions=suggestions,
        )

    def _validate_time_bound(self, task: Dict[str, Any]) -> CriterionResult:
        """Check if task has time estimate."""
        hours = task.get("estimated_hours")
        due_date = task.get("due_date")

        score = 0.5
        suggestions = []

        if hours:
            score += 0.3
        else:
            suggestions.append("Add time estimate in hours")

        if due_date:
            score += 0.2

        score = min(1.0, score)
        status = self._score_to_status(score)

        return CriterionResult(
            criterion="time_bound",
            status=status,
            score=score,
            feedback="Task has time bounds" if score >= 0.7 else "Add time estimate",
            suggestions=suggestions,
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _calculate_overall_score(self, result: INVESTValidationResult) -> float:
        """Calculate weighted overall score."""
        total_weight = 0.0
        weighted_score = 0.0

        criteria_results = [
            ("independent", result.independent),
            ("negotiable", result.negotiable),
            ("valuable", result.valuable),
            ("estimable", result.estimable),
            ("small", result.small),
            ("testable", result.testable),
        ]

        for name, criterion in criteria_results:
            if criterion:
                weight = self.WEIGHTS.get(name, 0.15)
                weighted_score += criterion.score * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _score_to_status(self, score: float) -> CriterionStatus:
        """Convert score to status."""
        if score >= 0.7:
            return CriterionStatus.PASS
        elif score >= 0.4:
            return CriterionStatus.WARN
        return CriterionStatus.FAIL


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_invest_validator(db: Optional[AsyncSession] = None) -> INVESTValidatorService:
    """Factory function for INVESTValidatorService."""
    return INVESTValidatorService(db)
