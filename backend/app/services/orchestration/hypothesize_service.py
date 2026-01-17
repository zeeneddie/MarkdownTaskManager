"""
Hypothesize Pattern Service - Week 107 (AO-QW-4)

Agent verbalization of expectations BEFORE execution.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Before making changes, agent MUST state expected outcomes
- Verification criteria defined upfront
- Recovery action specified if hypothesis fails
- Prevents unvalidated leaps and contaminated context

Key Features:
- Hypothesis creation with expected outcomes
- Verification criteria specification
- Failure recovery planning
- Hypothesis validation tracking
- Learning from hypothesis outcomes
"""

import json
import hashlib
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable


class HypothesisStatus(str, Enum):
    """Status of a hypothesis."""
    PENDING = "pending"          # Not yet tested
    TESTING = "testing"          # Currently being tested
    VALIDATED = "validated"      # Hypothesis confirmed
    INVALIDATED = "invalidated"  # Hypothesis disproven
    PARTIAL = "partial"          # Partially confirmed
    ABORTED = "aborted"          # Testing aborted


class VerificationMethod(str, Enum):
    """Methods for verifying a hypothesis."""
    TEST_EXECUTION = "test_execution"    # Run tests
    CODE_REVIEW = "code_review"          # Review code
    OUTPUT_CHECK = "output_check"        # Check output
    BEHAVIOR_CHECK = "behavior_check"    # Check behavior
    METRIC_CHECK = "metric_check"        # Check metrics
    MANUAL_CHECK = "manual_check"        # Manual verification
    AUTOMATED = "automated"              # Automated verification


class RecoveryAction(str, Enum):
    """Actions to take if hypothesis fails."""
    ROLLBACK = "rollback"              # Revert changes
    RETRY = "retry"                    # Try again
    ALTERNATIVE = "alternative"        # Try alternative approach
    ESCALATE = "escalate"             # Escalate to human
    INVESTIGATE = "investigate"        # Investigate cause
    ABORT = "abort"                   # Abort operation


@dataclass
class ExpectedOutcome:
    """
    An expected outcome of an action.

    Describes what we expect to happen when we
    execute an action, enabling verification.
    """
    id: str
    description: str
    verification_method: VerificationMethod
    success_criteria: str
    priority: int = 0  # Higher = more important
    optional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "verification_method": self.verification_method.value,
            "success_criteria": self.success_criteria,
            "priority": self.priority,
            "optional": self.optional,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    """
    Result of verifying an expected outcome.

    Records whether the outcome was achieved
    and any relevant details.
    """
    outcome_id: str
    passed: bool
    actual_result: str
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "outcome_id": self.outcome_id,
            "passed": self.passed,
            "actual_result": self.actual_result,
            "verified_at": self.verified_at.isoformat(),
            "error_message": self.error_message,
            "evidence": self.evidence,
        }


@dataclass
class Hypothesis:
    """
    A hypothesis about the outcome of an action.

    Before making changes, an agent creates a hypothesis
    stating what they expect to happen. This enables
    validation and prevents unvalidated leaps.
    """
    id: str
    action: str                          # What action is being taken
    context: str                         # Context/situation
    expected_outcomes: List[ExpectedOutcome] = field(default_factory=list)
    verification_plan: List[str] = field(default_factory=list)
    recovery_action: RecoveryAction = RecoveryAction.ROLLBACK
    recovery_details: str = ""
    status: HypothesisStatus = HypothesisStatus.PENDING
    results: List[VerificationResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: Optional[datetime] = None
    confidence: float = 0.0              # 0.0 to 1.0
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_outcome(
        self,
        description: str,
        success_criteria: str,
        verification_method: VerificationMethod = VerificationMethod.OUTPUT_CHECK,
        priority: int = 0,
        optional: bool = False,
    ) -> ExpectedOutcome:
        """Add an expected outcome."""
        outcome_id = hashlib.md5(
            f"{self.id}:{description}".encode()
        ).hexdigest()[:8]

        outcome = ExpectedOutcome(
            id=outcome_id,
            description=description,
            verification_method=verification_method,
            success_criteria=success_criteria,
            priority=priority,
            optional=optional,
        )

        self.expected_outcomes.append(outcome)
        return outcome

    def add_verification_step(self, step: str) -> None:
        """Add a verification step."""
        self.verification_plan.append(step)

    def add_assumption(self, assumption: str) -> None:
        """Add an assumption."""
        self.assumptions.append(assumption)

    def add_risk(self, risk: str) -> None:
        """Add a risk."""
        self.risks.append(risk)

    def record_result(
        self,
        outcome_id: str,
        passed: bool,
        actual_result: str,
        error_message: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Record a verification result."""
        result = VerificationResult(
            outcome_id=outcome_id,
            passed=passed,
            actual_result=actual_result,
            error_message=error_message,
            evidence=evidence,
        )
        self.results.append(result)
        return result

    def evaluate(self) -> HypothesisStatus:
        """
        Evaluate hypothesis based on results.

        Returns:
            Updated status based on verification results
        """
        if not self.results:
            return HypothesisStatus.PENDING

        # Count required outcomes
        required_outcomes = [
            o for o in self.expected_outcomes if not o.optional
        ]

        if not required_outcomes:
            # All optional, check if any passed
            if any(r.passed for r in self.results):
                self.status = HypothesisStatus.VALIDATED
            else:
                self.status = HypothesisStatus.INVALIDATED
            return self.status

        # Check required outcomes
        required_ids = {o.id for o in required_outcomes}
        result_map = {r.outcome_id: r for r in self.results}

        passed_required = 0
        failed_required = 0

        for outcome_id in required_ids:
            if outcome_id in result_map:
                if result_map[outcome_id].passed:
                    passed_required += 1
                else:
                    failed_required += 1

        total_required = len(required_ids)

        if passed_required == total_required:
            self.status = HypothesisStatus.VALIDATED
            self.confidence = 1.0
        elif failed_required > 0:
            if passed_required > 0:
                self.status = HypothesisStatus.PARTIAL
                self.confidence = passed_required / total_required
            else:
                self.status = HypothesisStatus.INVALIDATED
                self.confidence = 0.0
        else:
            self.status = HypothesisStatus.TESTING

        self.validated_at = datetime.now(timezone.utc)
        return self.status

    def format_markdown(self) -> str:
        """Format hypothesis as markdown."""
        lines = ["# Hypothesis\n"]

        lines.append(f"**Action:** {self.action}")
        lines.append(f"**Context:** {self.context}")
        lines.append(f"**Status:** {self.status.value}")
        lines.append("")

        lines.append("## Expected Outcomes")
        for i, outcome in enumerate(self.expected_outcomes, 1):
            optional = " (optional)" if outcome.optional else ""
            lines.append(f"{i}. {outcome.description}{optional}")
            lines.append(f"   - Criteria: {outcome.success_criteria}")
            lines.append(f"   - Verify via: {outcome.verification_method.value}")

        if self.verification_plan:
            lines.append("\n## Verification Plan")
            for i, step in enumerate(self.verification_plan, 1):
                lines.append(f"{i}. {step}")

        if self.assumptions:
            lines.append("\n## Assumptions")
            for assumption in self.assumptions:
                lines.append(f"- {assumption}")

        if self.risks:
            lines.append("\n## Risks")
            for risk in self.risks:
                lines.append(f"- {risk}")

        lines.append(f"\n## If Hypothesis Fails")
        lines.append(f"**Recovery Action:** {self.recovery_action.value}")
        if self.recovery_details:
            lines.append(f"**Details:** {self.recovery_details}")

        if self.results:
            lines.append("\n## Results")
            for result in self.results:
                status = "" if result.passed else ""
                lines.append(f"- {status} {result.outcome_id}: {result.actual_result}")
                if result.error_message:
                    lines.append(f"  - Error: {result.error_message}")

        return '\n'.join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "context": self.context,
            "expected_outcomes": [o.to_dict() for o in self.expected_outcomes],
            "verification_plan": self.verification_plan,
            "recovery_action": self.recovery_action.value,
            "recovery_details": self.recovery_details,
            "status": self.status.value,
            "results": [r.to_dict() for r in self.results],
            "created_at": self.created_at.isoformat(),
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "risks": self.risks,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        """Create from dictionary."""
        hypothesis = cls(
            id=data["id"],
            action=data["action"],
            context=data["context"],
            verification_plan=data.get("verification_plan", []),
            recovery_action=RecoveryAction(data.get("recovery_action", "rollback")),
            recovery_details=data.get("recovery_details", ""),
            status=HypothesisStatus(data.get("status", "pending")),
            confidence=data.get("confidence", 0.0),
            assumptions=data.get("assumptions", []),
            risks=data.get("risks", []),
            metadata=data.get("metadata", {}),
        )

        hypothesis.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("validated_at"):
            hypothesis.validated_at = datetime.fromisoformat(data["validated_at"])

        # Parse outcomes
        for o_data in data.get("expected_outcomes", []):
            hypothesis.expected_outcomes.append(ExpectedOutcome(
                id=o_data["id"],
                description=o_data["description"],
                verification_method=VerificationMethod(o_data["verification_method"]),
                success_criteria=o_data["success_criteria"],
                priority=o_data.get("priority", 0),
                optional=o_data.get("optional", False),
                metadata=o_data.get("metadata", {}),
            ))

        # Parse results
        for r_data in data.get("results", []):
            hypothesis.results.append(VerificationResult(
                outcome_id=r_data["outcome_id"],
                passed=r_data["passed"],
                actual_result=r_data["actual_result"],
                verified_at=datetime.fromisoformat(r_data["verified_at"]),
                error_message=r_data.get("error_message"),
                evidence=r_data.get("evidence"),
            ))

        return hypothesis


class HypothesizeService:
    """
    Hypothesize Pattern Service for mandatory expectation verbalization.

    Enforces the Hypothesize pattern by requiring agents to
    state expected outcomes before making changes.

    Usage:
        service = HypothesizeService()

        # Create hypothesis before action
        hypothesis = service.create_hypothesis(
            action="Add authentication middleware",
            context="Implementing JWT-based auth for API endpoints",
            outcomes=[
                ("All protected routes require valid JWT", "Return 401 for invalid tokens"),
                ("Tokens expire after 24 hours", "Expired tokens are rejected"),
            ],
            verification=[
                "Run authentication tests",
                "Manually test with expired token",
            ],
            recovery=RecoveryAction.ROLLBACK,
        )

        # Execute action...

        # Record results
        service.record_result(hypothesis, hypothesis.expected_outcomes[0].id, True, "Tests pass")
        service.record_result(hypothesis, hypothesis.expected_outcomes[1].id, True, "Expired token rejected")

        # Evaluate
        status = service.evaluate(hypothesis)
        if status == HypothesisStatus.VALIDATED:
            print("Hypothesis confirmed!")
    """

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        require_hypothesis: bool = True,
        min_outcomes: int = 1,
        require_verification: bool = True,
    ):
        """
        Initialize Hypothesize Service.

        Args:
            storage_dir: Directory for hypothesis storage
            require_hypothesis: Enforce hypothesis requirement
            min_outcomes: Minimum expected outcomes required
            require_verification: Require verification plan
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(".hypotheses")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.require_hypothesis = require_hypothesis
        self.min_outcomes = min_outcomes
        self.require_verification = require_verification

        # In-memory cache
        self._hypotheses: Dict[str, Hypothesis] = {}

        # Learning: track patterns of success/failure
        self._outcome_patterns: Dict[str, Dict[str, int]] = {}

    # === Hypothesis Creation ===

    def create_hypothesis(
        self,
        action: str,
        context: str,
        outcomes: Optional[List[tuple]] = None,
        verification: Optional[List[str]] = None,
        recovery: RecoveryAction = RecoveryAction.ROLLBACK,
        recovery_details: str = "",
        assumptions: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
    ) -> Hypothesis:
        """
        Create a new hypothesis.

        Args:
            action: The action being taken
            context: Context/situation
            outcomes: List of (description, success_criteria) tuples
            verification: List of verification steps
            recovery: Recovery action if hypothesis fails
            recovery_details: Details about recovery
            assumptions: List of assumptions
            risks: List of risks

        Returns:
            Created Hypothesis
        """
        hypothesis_id = hashlib.md5(
            f"{action}:{context}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]

        hypothesis = Hypothesis(
            id=hypothesis_id,
            action=action,
            context=context,
            verification_plan=verification or [],
            recovery_action=recovery,
            recovery_details=recovery_details,
            assumptions=assumptions or [],
            risks=risks or [],
        )

        # Add outcomes
        if outcomes:
            for desc, criteria in outcomes:
                hypothesis.add_outcome(desc, criteria)

        # Validate
        self._validate_hypothesis(hypothesis)

        # Store
        self._hypotheses[hypothesis_id] = hypothesis
        self._save_hypothesis(hypothesis)

        return hypothesis

    def _validate_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Validate hypothesis meets requirements."""
        if len(hypothesis.expected_outcomes) < self.min_outcomes:
            raise ValueError(
                f"Hypothesis requires at least {self.min_outcomes} expected outcomes"
            )

        if self.require_verification and not hypothesis.verification_plan:
            raise ValueError("Hypothesis requires a verification plan")

    # === Hypothesis Retrieval ===

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get a hypothesis by ID."""
        if hypothesis_id in self._hypotheses:
            return self._hypotheses[hypothesis_id]

        return self._load_hypothesis(hypothesis_id)

    def get_pending_hypotheses(self) -> List[Hypothesis]:
        """Get all pending (unvalidated) hypotheses."""
        self._load_all()
        return [
            h for h in self._hypotheses.values()
            if h.status == HypothesisStatus.PENDING
        ]

    def get_hypotheses_by_status(
        self,
        status: HypothesisStatus,
    ) -> List[Hypothesis]:
        """Get hypotheses by status."""
        self._load_all()
        return [
            h for h in self._hypotheses.values()
            if h.status == status
        ]

    # === Result Recording ===

    def record_result(
        self,
        hypothesis: Hypothesis,
        outcome_id: str,
        passed: bool,
        actual_result: str,
        error_message: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """
        Record a verification result.

        Args:
            hypothesis: The hypothesis being verified
            outcome_id: ID of the expected outcome
            passed: Whether the outcome was achieved
            actual_result: What actually happened
            error_message: Error message if failed
            evidence: Supporting evidence

        Returns:
            The recorded VerificationResult
        """
        result = hypothesis.record_result(
            outcome_id=outcome_id,
            passed=passed,
            actual_result=actual_result,
            error_message=error_message,
            evidence=evidence,
        )

        # Update pattern tracking for learning
        self._track_outcome_pattern(hypothesis, outcome_id, passed)

        # Save updated hypothesis
        self._save_hypothesis(hypothesis)

        return result

    def record_all_results(
        self,
        hypothesis: Hypothesis,
        results: List[Dict[str, Any]],
    ) -> List[VerificationResult]:
        """
        Record multiple results at once.

        Args:
            hypothesis: The hypothesis being verified
            results: List of result dicts with outcome_id, passed, actual_result

        Returns:
            List of recorded VerificationResults
        """
        recorded = []
        for r in results:
            result = self.record_result(
                hypothesis=hypothesis,
                outcome_id=r["outcome_id"],
                passed=r["passed"],
                actual_result=r["actual_result"],
                error_message=r.get("error_message"),
                evidence=r.get("evidence"),
            )
            recorded.append(result)

        return recorded

    # === Evaluation ===

    def evaluate(self, hypothesis: Hypothesis) -> HypothesisStatus:
        """
        Evaluate a hypothesis and determine its status.

        Returns:
            The evaluated status
        """
        status = hypothesis.evaluate()
        self._save_hypothesis(hypothesis)
        return status

    def get_recovery_recommendation(
        self,
        hypothesis: Hypothesis,
    ) -> Dict[str, Any]:
        """
        Get recovery recommendation for failed hypothesis.

        Returns:
            Dict with recommended action and details
        """
        if hypothesis.status == HypothesisStatus.VALIDATED:
            return {"action": "none", "reason": "Hypothesis validated"}

        # Analyze failure patterns
        failed_outcomes = [
            r for r in hypothesis.results if not r.passed
        ]

        recommendation = {
            "action": hypothesis.recovery_action.value,
            "details": hypothesis.recovery_details,
            "failed_outcomes": [r.outcome_id for r in failed_outcomes],
            "partial_success": hypothesis.status == HypothesisStatus.PARTIAL,
        }

        # Add specific guidance based on recovery action
        if hypothesis.recovery_action == RecoveryAction.ROLLBACK:
            recommendation["steps"] = [
                "Revert changes to last known good state",
                "Analyze what went wrong",
                "Create new hypothesis with adjusted expectations",
            ]
        elif hypothesis.recovery_action == RecoveryAction.RETRY:
            recommendation["steps"] = [
                "Review failed outcomes",
                "Adjust implementation if needed",
                "Re-run verification",
            ]
        elif hypothesis.recovery_action == RecoveryAction.ALTERNATIVE:
            recommendation["steps"] = [
                "Identify alternative approaches",
                "Create new hypothesis for alternative",
                "Proceed with alternative if hypothesis looks valid",
            ]
        elif hypothesis.recovery_action == RecoveryAction.ESCALATE:
            recommendation["steps"] = [
                "Document the issue and failed outcomes",
                "Prepare context for human review",
                "Wait for human guidance",
            ]

        return recommendation

    # === Learning & Patterns ===

    def _track_outcome_pattern(
        self,
        hypothesis: Hypothesis,
        outcome_id: str,
        passed: bool,
    ) -> None:
        """Track outcome patterns for learning."""
        # Create pattern key from action type
        action_key = hypothesis.action.split()[0].lower()

        if action_key not in self._outcome_patterns:
            self._outcome_patterns[action_key] = {"passed": 0, "failed": 0}

        if passed:
            self._outcome_patterns[action_key]["passed"] += 1
        else:
            self._outcome_patterns[action_key]["failed"] += 1

    def get_success_rate(self, action_type: str) -> float:
        """
        Get historical success rate for an action type.

        Returns:
            Success rate from 0.0 to 1.0
        """
        key = action_type.lower()
        if key not in self._outcome_patterns:
            return 0.5  # No data, assume 50%

        data = self._outcome_patterns[key]
        total = data["passed"] + data["failed"]
        if total == 0:
            return 0.5

        return data["passed"] / total

    def suggest_outcomes(
        self,
        action: str,
        context: str,
    ) -> List[Dict[str, str]]:
        """
        Suggest expected outcomes based on action type.

        Uses patterns from previous hypotheses to suggest
        common outcomes for similar actions.
        """
        suggestions = []

        action_lower = action.lower()

        # Common patterns for different action types
        if "test" in action_lower:
            suggestions.extend([
                {"description": "All tests pass", "criteria": "Test exit code 0"},
                {"description": "No new test failures", "criteria": "Same or fewer failing tests"},
                {"description": "Code coverage maintained", "criteria": "Coverage >= previous"},
            ])
        elif "add" in action_lower or "implement" in action_lower:
            suggestions.extend([
                {"description": "Feature works as expected", "criteria": "Manual verification passes"},
                {"description": "Existing functionality preserved", "criteria": "No regression in tests"},
                {"description": "Code follows standards", "criteria": "Linting passes"},
            ])
        elif "refactor" in action_lower:
            suggestions.extend([
                {"description": "Behavior unchanged", "criteria": "All existing tests pass"},
                {"description": "Code cleaner/simpler", "criteria": "Reduced complexity metrics"},
                {"description": "No new bugs introduced", "criteria": "No new test failures"},
            ])
        elif "fix" in action_lower or "bug" in action_lower:
            suggestions.extend([
                {"description": "Bug is fixed", "criteria": "Reproduction steps no longer reproduce"},
                {"description": "No side effects", "criteria": "Related functionality works"},
                {"description": "Test added for bug", "criteria": "New test covers the fix"},
            ])
        elif "delete" in action_lower or "remove" in action_lower:
            suggestions.extend([
                {"description": "Target removed", "criteria": "File/code no longer exists"},
                {"description": "No broken references", "criteria": "No import/reference errors"},
                {"description": "Tests updated", "criteria": "Tests don't reference removed code"},
            ])

        return suggestions

    # === Persistence ===

    def _save_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Save hypothesis to file."""
        file_path = self.storage_dir / f"{hypothesis.id}.json"
        with open(file_path, 'w') as f:
            json.dump(hypothesis.to_dict(), f, indent=2)

        # Also save markdown version
        md_path = self.storage_dir / f"{hypothesis.id}.md"
        with open(md_path, 'w') as f:
            f.write(hypothesis.format_markdown())

    def _load_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Load hypothesis from file."""
        file_path = self.storage_dir / f"{hypothesis_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            hypothesis = Hypothesis.from_dict(data)
            self._hypotheses[hypothesis_id] = hypothesis
            return hypothesis
        except Exception:
            return None

    def _load_all(self) -> None:
        """Load all hypotheses from storage."""
        for file_path in self.storage_dir.glob("*.json"):
            hypothesis_id = file_path.stem
            if hypothesis_id not in self._hypotheses:
                self._load_hypothesis(hypothesis_id)

    def delete_hypothesis(self, hypothesis_id: str) -> bool:
        """Delete a hypothesis."""
        self._hypotheses.pop(hypothesis_id, None)

        json_path = self.storage_dir / f"{hypothesis_id}.json"
        md_path = self.storage_dir / f"{hypothesis_id}.md"

        deleted = False
        if json_path.exists():
            json_path.unlink()
            deleted = True
        if md_path.exists():
            md_path.unlink()

        return deleted

    # === Enforcement ===

    def check_hypothesis_required(
        self,
        action: str,
        bypass_actions: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if a hypothesis is required for an action.

        Some trivial actions may not require a hypothesis.

        Args:
            action: The action being taken
            bypass_actions: Actions that don't require hypothesis

        Returns:
            True if hypothesis is required
        """
        if not self.require_hypothesis:
            return False

        # Default bypass list for trivial actions
        default_bypass = [
            "read", "list", "get", "show", "display", "print",
            "log", "comment", "format", "lint",
        ]

        bypass_list = bypass_actions or default_bypass

        action_lower = action.lower()
        for bypass in bypass_list:
            if bypass in action_lower:
                return False

        return True

    def enforce_hypothesis(
        self,
        action: str,
        hypothesis: Optional[Hypothesis] = None,
    ) -> None:
        """
        Enforce hypothesis requirement.

        Raises:
            ValueError if hypothesis required but not provided
        """
        if self.check_hypothesis_required(action):
            if hypothesis is None:
                raise ValueError(
                    f"Action '{action}' requires a hypothesis. "
                    "Please create a hypothesis before proceeding."
                )

            if hypothesis.status != HypothesisStatus.PENDING:
                raise ValueError(
                    f"Hypothesis already evaluated (status: {hypothesis.status}). "
                    "Create a new hypothesis for this action."
                )


# Decorator for enforcing hypothesis pattern
def requires_hypothesis(service: HypothesizeService):
    """
    Decorator to enforce hypothesis requirement.

    Usage:
        @requires_hypothesis(hypothesis_service)
        def make_change(hypothesis: Hypothesis, code: str):
            # Make changes...
            pass
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            hypothesis = kwargs.get('hypothesis')
            if hypothesis is None and args:
                # Try to find hypothesis in positional args
                for arg in args:
                    if isinstance(arg, Hypothesis):
                        hypothesis = arg
                        break

            # Get action from function name
            action = func.__name__.replace('_', ' ')

            service.enforce_hypothesis(action, hypothesis)
            return func(*args, **kwargs)

        return wrapper
    return decorator
