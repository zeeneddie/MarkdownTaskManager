# INVEST Validator - Week 102: Functional Requirements Quick Wins
# FR-QW-2: Validate stories against INVEST criteria with scoring

"""
INVEST Validator for User Story Quality

Validates user stories against the INVEST criteria:
- Independent: Can be developed independently
- Negotiable: Not a specific contract, details can be negotiated
- Valuable: Delivers value to stakeholder
- Estimable: Can be estimated with reasonable accuracy
- Small: Small enough to complete in one sprint
- Testable: Has clear acceptance criteria

Each criterion scored 0.0-1.0 with overall weighted score.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
import re


class INVESTCriterion(Enum):
    """The six INVEST criteria for user story quality."""
    INDEPENDENT = "independent"
    NEGOTIABLE = "negotiable"
    VALUABLE = "valuable"
    ESTIMABLE = "estimable"
    SMALL = "small"
    TESTABLE = "testable"


class IssueSeverity(Enum):
    """Severity levels for INVEST issues."""
    CRITICAL = "critical"     # Blocks story acceptance
    MAJOR = "major"           # Significant quality issue
    MINOR = "minor"           # Improvement opportunity
    SUGGESTION = "suggestion" # Nice-to-have enhancement


@dataclass
class INVESTIssue:
    """A specific issue found during INVEST validation."""
    criterion: INVESTCriterion
    severity: IssueSeverity
    message: str
    suggestion: str
    location: Optional[str] = None  # Which part of story


@dataclass
class CriterionScore:
    """Score for a single INVEST criterion."""
    criterion: INVESTCriterion
    score: float  # 0.0-1.0
    weight: float  # Weight in overall score
    issues: List[INVESTIssue] = field(default_factory=list)
    passed: bool = True
    details: str = ""


@dataclass
class UserStory:
    """A user story to validate."""
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    story_points: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @property
    def as_who_format(self) -> bool:
        """Check if description follows 'As a... I want... So that...' format."""
        pattern = r"(?i)as\s+a[n]?\s+.+,?\s+i\s+want\s+.+,?\s+so\s+that\s+.+"
        return bool(re.search(pattern, self.description))

    @property
    def has_acceptance_criteria(self) -> bool:
        return len(self.acceptance_criteria) > 0

    @property
    def word_count(self) -> int:
        return len(self.description.split())


@dataclass
class INVESTValidationResult:
    """Complete INVEST validation result."""
    story: UserStory
    overall_score: float  # 0.0-1.0
    overall_grade: str    # A, B, C, D, F
    criterion_scores: Dict[INVESTCriterion, CriterionScore]
    all_issues: List[INVESTIssue]
    passed: bool
    recommendations: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "story_title": self.story.title,
            "overall_score": round(self.overall_score, 2),
            "overall_grade": self.overall_grade,
            "passed": self.passed,
            "criterion_scores": {
                c.value: {
                    "score": round(cs.score, 2),
                    "passed": cs.passed,
                    "details": cs.details,
                    "issues": [
                        {
                            "severity": i.severity.value,
                            "message": i.message,
                            "suggestion": i.suggestion
                        }
                        for i in cs.issues
                    ]
                }
                for c, cs in self.criterion_scores.items()
            },
            "recommendations": self.recommendations,
            "issue_count": len(self.all_issues),
            "critical_issues": len([i for i in self.all_issues if i.severity == IssueSeverity.CRITICAL])
        }


class INVESTValidator:
    """
    Validates user stories against INVEST criteria.

    INVEST = Independent, Negotiable, Valuable, Estimable, Small, Testable

    Usage:
        validator = INVESTValidator()
        story = UserStory(
            title="User Registration",
            description="As a new user, I want to register an account, so that I can access the platform",
            acceptance_criteria=["Email validation works", "Password meets requirements"]
        )
        result = validator.validate(story)
        print(f"Score: {result.overall_score}, Grade: {result.overall_grade}")
    """

    # Default weights for each criterion (sum to 1.0)
    DEFAULT_WEIGHTS = {
        INVESTCriterion.INDEPENDENT: 0.15,
        INVESTCriterion.NEGOTIABLE: 0.10,
        INVESTCriterion.VALUABLE: 0.20,
        INVESTCriterion.ESTIMABLE: 0.15,
        INVESTCriterion.SMALL: 0.15,
        INVESTCriterion.TESTABLE: 0.25,
    }

    # Pass thresholds
    OVERALL_PASS_THRESHOLD = 0.60
    CRITERION_PASS_THRESHOLD = 0.50

    # Patterns for detection
    DEPENDENCY_PATTERNS = [
        r"(?i)depends?\s+on",
        r"(?i)after\s+.+\s+is\s+(done|complete|finished)",
        r"(?i)requires?\s+.+\s+to\s+be",
        r"(?i)blocked\s+by",
        r"(?i)waiting\s+for",
        r"(?i)once\s+.+\s+is\s+(done|complete|ready)",
    ]

    IMPLEMENTATION_DETAIL_PATTERNS = [
        r"(?i)\busing\s+(react|vue|angular|django|flask|spring)\b",
        r"(?i)\bapi\s+endpoint\b",
        r"(?i)\bdatabase\s+(table|schema|query)\b",
        r"(?i)\bjson\s+format\b",
        r"(?i)\brest\s+api\b",
        r"(?i)\bsql\s+query\b",
        r"(?i)\bhttp\s+(get|post|put|delete)\b",
    ]

    VALUE_INDICATORS = [
        r"(?i)so\s+that\s+.+",
        r"(?i)in\s+order\s+to\s+.+",
        r"(?i)to\s+(improve|enable|allow|ensure|provide|reduce|increase)",
        r"(?i)(benefit|value|outcome|result)",
        r"(?i)business\s+(need|requirement|goal)",
    ]

    VAGUE_TERMS = [
        "quickly", "easily", "efficiently", "properly", "appropriately",
        "various", "some", "many", "few", "several", "etc", "and so on",
        "as needed", "if necessary", "when appropriate", "as required",
        "good", "better", "best", "nice", "cool", "great"
    ]

    TESTABLE_AC_PATTERNS = [
        r"(?i)given\s+.+\s+when\s+.+\s+then\s+.+",
        r"(?i)verify\s+(that\s+)?",
        r"(?i)ensure\s+(that\s+)?",
        r"(?i)should\s+(be|have|display|show|return)",
        r"(?i)must\s+(be|have|display|show|return)",
        r"(?i)\d+\s*(seconds?|minutes?|ms|milliseconds?)",  # Timing requirements
        r"(?i)(exactly|at\s+least|at\s+most|between)\s+\d+",  # Numeric constraints
    ]

    def __init__(
        self,
        weights: Optional[Dict[INVESTCriterion, float]] = None,
        pass_threshold: float = 0.60,
        strict_mode: bool = False
    ):
        """
        Initialize the INVEST validator.

        Args:
            weights: Custom weights for each criterion (must sum to 1.0)
            pass_threshold: Overall score threshold for passing
            strict_mode: If True, any CRITICAL issue fails the story
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.pass_threshold = pass_threshold
        self.strict_mode = strict_mode

        # Validate weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            # Normalize weights
            self.weights = {k: v / weight_sum for k, v in self.weights.items()}

    def validate(self, story: UserStory) -> INVESTValidationResult:
        """
        Validate a user story against all INVEST criteria.

        Args:
            story: The user story to validate

        Returns:
            INVESTValidationResult with scores and recommendations
        """
        criterion_scores = {
            INVESTCriterion.INDEPENDENT: self._validate_independent(story),
            INVESTCriterion.NEGOTIABLE: self._validate_negotiable(story),
            INVESTCriterion.VALUABLE: self._validate_valuable(story),
            INVESTCriterion.ESTIMABLE: self._validate_estimable(story),
            INVESTCriterion.SMALL: self._validate_small(story),
            INVESTCriterion.TESTABLE: self._validate_testable(story),
        }

        # Calculate weighted overall score
        overall_score = sum(
            cs.score * self.weights[c]
            for c, cs in criterion_scores.items()
        )

        # Collect all issues
        all_issues = []
        for cs in criterion_scores.values():
            all_issues.extend(cs.issues)

        # Determine if passed
        passed = overall_score >= self.pass_threshold
        if self.strict_mode:
            has_critical = any(i.severity == IssueSeverity.CRITICAL for i in all_issues)
            passed = passed and not has_critical

        # Generate recommendations
        recommendations = self._generate_recommendations(criterion_scores, all_issues)

        return INVESTValidationResult(
            story=story,
            overall_score=overall_score,
            overall_grade=self._score_to_grade(overall_score),
            criterion_scores=criterion_scores,
            all_issues=all_issues,
            passed=passed,
            recommendations=recommendations
        )

    def _validate_independent(self, story: UserStory) -> CriterionScore:
        """
        Validate the Independent criterion.

        A story should be self-contained and not depend on other stories.
        """
        issues = []
        score = 1.0

        # Check explicit dependencies
        if story.dependencies:
            score -= 0.3 * min(len(story.dependencies), 3)
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.INDEPENDENT,
                severity=IssueSeverity.MAJOR if len(story.dependencies) > 1 else IssueSeverity.MINOR,
                message=f"Story has {len(story.dependencies)} explicit dependencies",
                suggestion="Consider splitting or reordering to reduce dependencies"
            ))

        # Check for dependency language in description
        for pattern in self.DEPENDENCY_PATTERNS:
            if re.search(pattern, story.description):
                score -= 0.2
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.INDEPENDENT,
                    severity=IssueSeverity.MINOR,
                    message="Description contains dependency language",
                    suggestion="Rephrase to focus on what this story delivers, not what it depends on"
                ))
                break

        # Check for references to other stories/features
        if re.search(r"(?i)(story|feature|ticket)\s*#?\d+", story.description):
            score -= 0.15
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.INDEPENDENT,
                severity=IssueSeverity.MINOR,
                message="Story references other tickets/stories",
                suggestion="Include necessary context in this story instead of referencing others"
            ))

        score = max(0.0, score)
        return CriterionScore(
            criterion=INVESTCriterion.INDEPENDENT,
            score=score,
            weight=self.weights[INVESTCriterion.INDEPENDENT],
            issues=issues,
            passed=score >= self.CRITERION_PASS_THRESHOLD,
            details="Story can be developed independently" if score >= 0.7 else "Story has dependencies that may block progress"
        )

    def _validate_negotiable(self, story: UserStory) -> CriterionScore:
        """
        Validate the Negotiable criterion.

        A story should not be overly prescriptive about implementation details.
        """
        issues = []
        score = 1.0

        # Check for implementation details
        impl_details_found = []
        for pattern in self.IMPLEMENTATION_DETAIL_PATTERNS:
            matches = re.findall(pattern, story.description)
            impl_details_found.extend(matches)

        if impl_details_found:
            score -= 0.15 * min(len(impl_details_found), 4)
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.NEGOTIABLE,
                severity=IssueSeverity.MINOR,
                message=f"Story contains implementation details: {', '.join(impl_details_found[:3])}",
                suggestion="Focus on WHAT is needed, not HOW to implement it"
            ))

        # Check if story is too prescriptive (very long with specific details)
        if story.word_count > 100:
            score -= 0.15
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.NEGOTIABLE,
                severity=IssueSeverity.MINOR,
                message=f"Story description is very detailed ({story.word_count} words)",
                suggestion="Consider moving implementation details to technical notes"
            ))

        # Check for overly specific UI details
        ui_specific = re.findall(
            r"(?i)(button|field|dropdown|checkbox|modal|popup|screen|page|form)\s+(should|must|will)\s+(be|have|show|display)",
            story.description
        )
        if len(ui_specific) > 2:
            score -= 0.2
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.NEGOTIABLE,
                severity=IssueSeverity.MINOR,
                message="Story contains specific UI implementation details",
                suggestion="Describe desired user experience instead of specific UI elements"
            ))

        score = max(0.0, score)
        return CriterionScore(
            criterion=INVESTCriterion.NEGOTIABLE,
            score=score,
            weight=self.weights[INVESTCriterion.NEGOTIABLE],
            issues=issues,
            passed=score >= self.CRITERION_PASS_THRESHOLD,
            details="Story leaves room for implementation discussion" if score >= 0.7 else "Story is overly prescriptive"
        )

    def _validate_valuable(self, story: UserStory) -> CriterionScore:
        """
        Validate the Valuable criterion.

        A story should deliver clear value to a stakeholder.
        """
        issues = []
        score = 0.5  # Start neutral

        # Check for "As a... I want... So that..." format
        if story.as_who_format:
            score += 0.3
        else:
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.VALUABLE,
                severity=IssueSeverity.MAJOR,
                message="Story doesn't follow 'As a [user], I want [goal], so that [benefit]' format",
                suggestion="Rewrite using the standard user story format to clarify value"
            ))

        # Check for value indicators
        value_found = False
        for pattern in self.VALUE_INDICATORS:
            if re.search(pattern, story.description):
                value_found = True
                score += 0.1
                break

        if not value_found:
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.VALUABLE,
                severity=IssueSeverity.MAJOR,
                message="No clear business value or benefit stated",
                suggestion="Add 'so that...' clause explaining the benefit"
            ))

        # Check for stakeholder identification
        stakeholder_pattern = r"(?i)as\s+a[n]?\s+(\w+(?:\s+\w+)?)"
        stakeholder_match = re.search(stakeholder_pattern, story.description)
        if stakeholder_match:
            stakeholder = stakeholder_match.group(1).lower()
            # Penalize generic stakeholders
            if stakeholder in ["user", "person", "someone", "anybody"]:
                score -= 0.1
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.VALUABLE,
                    severity=IssueSeverity.MINOR,
                    message=f"Generic stakeholder '{stakeholder}' used",
                    suggestion="Use specific role like 'customer', 'admin', 'sales rep'"
                ))
            else:
                score += 0.1

        # Check for technical-only stories
        technical_only_patterns = [
            r"(?i)refactor",
            r"(?i)update\s+dependencies",
            r"(?i)upgrade\s+.+\s+version",
            r"(?i)fix\s+technical\s+debt",
            r"(?i)improve\s+code\s+quality",
        ]
        for pattern in technical_only_patterns:
            if re.search(pattern, story.description):
                if not value_found:
                    score -= 0.2
                    issues.append(INVESTIssue(
                        criterion=INVESTCriterion.VALUABLE,
                        severity=IssueSeverity.MINOR,
                        message="Story appears to be purely technical without user benefit",
                        suggestion="Explain how this technical work benefits end users"
                    ))
                break

        score = max(0.0, min(1.0, score))
        return CriterionScore(
            criterion=INVESTCriterion.VALUABLE,
            score=score,
            weight=self.weights[INVESTCriterion.VALUABLE],
            issues=issues,
            passed=score >= self.CRITERION_PASS_THRESHOLD,
            details="Story delivers clear value" if score >= 0.7 else "Value proposition is unclear"
        )

    def _validate_estimable(self, story: UserStory) -> CriterionScore:
        """
        Validate the Estimable criterion.

        A story should be clear enough to estimate with reasonable accuracy.
        """
        issues = []
        score = 0.7  # Start optimistic

        # Check for vague terms
        vague_found = []
        desc_lower = story.description.lower()
        for term in self.VAGUE_TERMS:
            if term in desc_lower:
                vague_found.append(term)

        if vague_found:
            score -= 0.1 * min(len(vague_found), 4)
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.ESTIMABLE,
                severity=IssueSeverity.MINOR,
                message=f"Vague terms found: {', '.join(vague_found[:5])}",
                suggestion="Replace vague terms with specific, measurable criteria"
            ))

        # Check for open-ended requirements
        open_ended_patterns = [
            r"(?i)and\s+more",
            r"(?i)etc\.?",
            r"(?i)and\s+so\s+on",
            r"(?i)among\s+others",
            r"(?i)including\s+but\s+not\s+limited",
        ]
        for pattern in open_ended_patterns:
            if re.search(pattern, story.description):
                score -= 0.2
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.ESTIMABLE,
                    severity=IssueSeverity.MAJOR,
                    message="Story contains open-ended requirements",
                    suggestion="Define explicit scope boundaries"
                ))
                break

        # Check if acceptance criteria help with estimation
        if story.has_acceptance_criteria:
            # More ACs generally means better estimability
            ac_count = len(story.acceptance_criteria)
            if ac_count >= 3:
                score += 0.15
            elif ac_count >= 1:
                score += 0.05
        else:
            score -= 0.2
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.ESTIMABLE,
                severity=IssueSeverity.MAJOR,
                message="No acceptance criteria defined",
                suggestion="Add acceptance criteria to clarify scope and aid estimation"
            ))

        # Check for unknowns/research needed
        unknown_patterns = [
            r"(?i)need\s+to\s+(research|investigate|explore)",
            r"(?i)tbd|to\s+be\s+determined",
            r"(?i)unclear|unknown",
            r"(?i)spike|proof\s+of\s+concept",
        ]
        for pattern in unknown_patterns:
            if re.search(pattern, story.description):
                score -= 0.25
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.ESTIMABLE,
                    severity=IssueSeverity.MAJOR,
                    message="Story contains unknowns that need investigation",
                    suggestion="Create a spike/research story first, then estimate the implementation"
                ))
                break

        # Existing estimate is a good sign
        if story.story_points is not None:
            score += 0.1

        score = max(0.0, min(1.0, score))
        return CriterionScore(
            criterion=INVESTCriterion.ESTIMABLE,
            score=score,
            weight=self.weights[INVESTCriterion.ESTIMABLE],
            issues=issues,
            passed=score >= self.CRITERION_PASS_THRESHOLD,
            details="Story is well-defined for estimation" if score >= 0.7 else "Story needs clarification for accurate estimation"
        )

    def _validate_small(self, story: UserStory) -> CriterionScore:
        """
        Validate the Small criterion.

        A story should be completable within a sprint (typically 1-8 story points).
        """
        issues = []
        score = 0.8  # Start optimistic

        # Check story points if available
        if story.story_points is not None:
            if story.story_points <= 3:
                score = 1.0
            elif story.story_points <= 5:
                score = 0.9
            elif story.story_points <= 8:
                score = 0.7
            elif story.story_points <= 13:
                score = 0.5
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.SMALL,
                    severity=IssueSeverity.MINOR,
                    message=f"Story is large ({story.story_points} points)",
                    suggestion="Consider splitting into smaller stories"
                ))
            else:
                score = 0.2
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.SMALL,
                    severity=IssueSeverity.CRITICAL,
                    message=f"Story is too large ({story.story_points} points)",
                    suggestion="Must be split - no story should exceed 13 points"
                ))

        # Check description length as proxy for complexity
        if story.word_count > 200:
            score -= 0.2
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.SMALL,
                severity=IssueSeverity.MINOR,
                message=f"Long description ({story.word_count} words) may indicate large scope",
                suggestion="Review if story can be split into smaller pieces"
            ))

        # Check number of acceptance criteria
        if len(story.acceptance_criteria) > 10:
            score -= 0.2
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.SMALL,
                severity=IssueSeverity.MINOR,
                message=f"Many acceptance criteria ({len(story.acceptance_criteria)}) suggest large scope",
                suggestion="Consider splitting into multiple stories"
            ))

        # Check for compound requirements (and, also, additionally)
        compound_patterns = [
            r"(?i)\band\s+also\b",
            r"(?i)\badditionally\b",
            r"(?i)\bfurthermore\b",
            r"(?i)\bas\s+well\s+as\b",
        ]
        compound_count = sum(
            1 for p in compound_patterns
            if re.search(p, story.description)
        )
        if compound_count >= 2:
            score -= 0.15
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.SMALL,
                severity=IssueSeverity.MINOR,
                message="Story contains multiple compound requirements",
                suggestion="Split into separate stories for each distinct requirement"
            ))

        # Check for epic-level language
        epic_patterns = [
            r"(?i)entire\s+(system|application|platform)",
            r"(?i)all\s+(users|customers|data)",
            r"(?i)complete\s+(overhaul|redesign|rewrite)",
            r"(?i)across\s+all\s+",
        ]
        for pattern in epic_patterns:
            if re.search(pattern, story.description):
                score -= 0.3
                issues.append(INVESTIssue(
                    criterion=INVESTCriterion.SMALL,
                    severity=IssueSeverity.MAJOR,
                    message="Story scope appears epic-level",
                    suggestion="Break down into smaller, sprint-sized stories"
                ))
                break

        score = max(0.0, min(1.0, score))
        return CriterionScore(
            criterion=INVESTCriterion.SMALL,
            score=score,
            weight=self.weights[INVESTCriterion.SMALL],
            issues=issues,
            passed=score >= self.CRITERION_PASS_THRESHOLD,
            details="Story is appropriately sized" if score >= 0.7 else "Story may be too large for single sprint"
        )

    def _validate_testable(self, story: UserStory) -> CriterionScore:
        """
        Validate the Testable criterion.

        A story should have clear, verifiable acceptance criteria.
        """
        issues = []
        score = 0.3  # Start pessimistic - testability must be proven

        # No acceptance criteria is a critical issue
        if not story.has_acceptance_criteria:
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.TESTABLE,
                severity=IssueSeverity.CRITICAL,
                message="No acceptance criteria defined",
                suggestion="Add specific, testable acceptance criteria"
            ))
            return CriterionScore(
                criterion=INVESTCriterion.TESTABLE,
                score=0.1,
                weight=self.weights[INVESTCriterion.TESTABLE],
                issues=issues,
                passed=False,
                details="Cannot verify completion without acceptance criteria"
            )

        # Evaluate each acceptance criterion
        testable_count = 0
        vague_ac_count = 0

        for ac in story.acceptance_criteria:
            is_testable = False

            # Check for testable patterns
            for pattern in self.TESTABLE_AC_PATTERNS:
                if re.search(pattern, ac):
                    is_testable = True
                    break

            # Check for specific values/numbers
            if re.search(r"\d+", ac):
                is_testable = True

            # Check for vague language
            ac_lower = ac.lower()
            vague_in_ac = any(term in ac_lower for term in self.VAGUE_TERMS)

            if is_testable and not vague_in_ac:
                testable_count += 1
            elif vague_in_ac:
                vague_ac_count += 1

        # Score based on testable ratio
        total_ac = len(story.acceptance_criteria)
        testable_ratio = testable_count / total_ac
        score = 0.3 + (0.6 * testable_ratio)

        if testable_ratio < 0.5:
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.TESTABLE,
                severity=IssueSeverity.MAJOR,
                message=f"Only {testable_count}/{total_ac} acceptance criteria are clearly testable",
                suggestion="Rewrite ACs with specific, measurable outcomes"
            ))

        if vague_ac_count > 0:
            score -= 0.1 * min(vague_ac_count, 3)
            issues.append(INVESTIssue(
                criterion=INVESTCriterion.TESTABLE,
                severity=IssueSeverity.MINOR,
                message=f"{vague_ac_count} acceptance criteria contain vague terms",
                suggestion="Replace vague terms with specific, verifiable criteria"
            ))

        # Bonus for Given/When/Then format
        gwt_count = sum(
            1 for ac in story.acceptance_criteria
            if re.search(r"(?i)given\s+.+\s+when\s+.+\s+then\s+.+", ac)
        )
        if gwt_count > 0:
            score += 0.1

        score = max(0.0, min(1.0, score))
        return CriterionScore(
            criterion=INVESTCriterion.TESTABLE,
            score=score,
            weight=self.weights[INVESTCriterion.TESTABLE],
            issues=issues,
            passed=score >= self.CRITERION_PASS_THRESHOLD,
            details="Story has clear, testable criteria" if score >= 0.7 else "Acceptance criteria need improvement"
        )

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.90:
            return "A"
        elif score >= 0.80:
            return "B"
        elif score >= 0.70:
            return "C"
        elif score >= 0.60:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
        self,
        criterion_scores: Dict[INVESTCriterion, CriterionScore],
        all_issues: List[INVESTIssue]
    ) -> List[str]:
        """Generate prioritized recommendations based on validation results."""
        recommendations = []

        # Sort criteria by score (worst first)
        sorted_criteria = sorted(
            criterion_scores.items(),
            key=lambda x: x[1].score
        )

        # Add recommendations for failing criteria
        for criterion, cs in sorted_criteria:
            if not cs.passed:
                if criterion == INVESTCriterion.TESTABLE:
                    recommendations.append(
                        "Priority: Add clear, verifiable acceptance criteria with specific outcomes"
                    )
                elif criterion == INVESTCriterion.VALUABLE:
                    recommendations.append(
                        "Clarify the business value using 'As a [role], I want [goal], so that [benefit]'"
                    )
                elif criterion == INVESTCriterion.SMALL:
                    recommendations.append(
                        "Consider splitting this story into smaller, sprint-sized pieces"
                    )
                elif criterion == INVESTCriterion.ESTIMABLE:
                    recommendations.append(
                        "Remove vague terms and add specific scope boundaries"
                    )
                elif criterion == INVESTCriterion.INDEPENDENT:
                    recommendations.append(
                        "Reduce dependencies or include necessary context within the story"
                    )
                elif criterion == INVESTCriterion.NEGOTIABLE:
                    recommendations.append(
                        "Focus on user needs rather than implementation details"
                    )

        # Add general recommendations based on critical issues
        critical_issues = [i for i in all_issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.insert(0, f"Address {len(critical_issues)} critical issue(s) before sprint planning")

        return recommendations[:5]  # Return top 5 recommendations


# Convenience functions
def validate_story(
    title: str,
    description: str,
    acceptance_criteria: Optional[List[str]] = None,
    story_points: Optional[int] = None,
    dependencies: Optional[List[str]] = None
) -> INVESTValidationResult:
    """
    Convenience function to validate a user story.

    Args:
        title: Story title
        description: Story description
        acceptance_criteria: List of acceptance criteria
        story_points: Estimated story points
        dependencies: List of dependency descriptions

    Returns:
        INVESTValidationResult with scores and recommendations
    """
    story = UserStory(
        title=title,
        description=description,
        acceptance_criteria=acceptance_criteria or [],
        story_points=story_points,
        dependencies=dependencies or []
    )
    validator = INVESTValidator()
    return validator.validate(story)


def quick_score(description: str, acceptance_criteria: Optional[List[str]] = None) -> float:
    """
    Quick INVEST score for a story description.

    Args:
        description: Story description
        acceptance_criteria: Optional list of acceptance criteria

    Returns:
        Overall INVEST score (0.0-1.0)
    """
    result = validate_story(
        title="Quick Score",
        description=description,
        acceptance_criteria=acceptance_criteria
    )
    return result.overall_score


def is_invest_compliant(
    description: str,
    acceptance_criteria: Optional[List[str]] = None,
    threshold: float = 0.60
) -> bool:
    """
    Check if a story meets INVEST compliance threshold.

    Args:
        description: Story description
        acceptance_criteria: Optional list of acceptance criteria
        threshold: Minimum score to pass (default 0.60)

    Returns:
        True if story meets threshold
    """
    return quick_score(description, acceptance_criteria) >= threshold
