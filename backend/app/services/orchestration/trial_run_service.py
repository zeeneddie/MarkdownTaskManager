"""
Trial Run Validation Service

Week 108 - AO-M-5: Dry run validation before actual execution.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Simulate actions before actual execution
- Validate expected outcomes
- Detect potential issues before they occur
- Compare predicted vs actual results
- Enable rollback planning

Example usage:
    service = TrialRunService()

    # Create a trial run for planned changes
    trial = service.create_trial(
        name="Add user authentication",
        actions=[
            {"type": "create_file", "path": "src/auth/login.py", "content": "..."},
            {"type": "modify_file", "path": "src/main.py", "changes": "..."},
            {"type": "run_tests", "pattern": "test_auth_*"},
        ]
    )

    # Execute dry run
    result = await service.execute_dry_run(trial.id)

    # Check for issues
    if result.has_issues:
        print(f"Issues detected: {result.issues}")
    else:
        # Proceed with actual execution
        actual_result = await service.execute_actual(trial.id)

    # Compare results
    comparison = service.compare_results(trial.id)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Awaitable, Tuple
from pathlib import Path
import json
import copy
import hashlib
import uuid


class ActionType(Enum):
    """Type of action to perform."""
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    RENAME_FILE = "rename_file"
    MOVE_FILE = "move_file"
    RUN_COMMAND = "run_command"
    RUN_TESTS = "run_tests"
    API_CALL = "api_call"
    DATABASE_QUERY = "database_query"
    CUSTOM = "custom"


class ValidationLevel(Enum):
    """Level of validation to perform."""
    SYNTAX = "syntax"        # Check syntax validity
    SEMANTIC = "semantic"    # Check semantic correctness
    INTEGRATION = "integration"  # Check integration impact
    FULL = "full"           # All validations


class IssueType(Enum):
    """Type of issue detected."""
    SYNTAX_ERROR = "syntax_error"
    FILE_CONFLICT = "file_conflict"
    DEPENDENCY_MISSING = "dependency_missing"
    TEST_FAILURE = "test_failure"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_LIMIT = "resource_limit"
    COMPATIBILITY = "compatibility"
    ROLLBACK_IMPOSSIBLE = "rollback_impossible"
    WARNING = "warning"


class IssueSeverity(Enum):
    """Severity of an issue."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TrialIssue:
    """An issue detected during trial run."""
    id: str
    issue_type: IssueType
    severity: IssueSeverity
    action_index: int
    description: str
    details: Dict[str, Any]
    suggested_fix: Optional[str] = None
    can_proceed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.issue_type.value,
            "severity": self.severity.value,
            "action_index": self.action_index,
            "description": self.description,
            "details": self.details,
            "suggested_fix": self.suggested_fix,
            "can_proceed": self.can_proceed
        }


@dataclass
class ActionSnapshot:
    """Snapshot of system state before/after an action."""
    action_index: int
    timestamp: datetime
    files_state: Dict[str, str]  # path -> content hash
    variables: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_index": self.action_index,
            "timestamp": self.timestamp.isoformat(),
            "files_state": self.files_state,
            "variables": self.variables,
            "metadata": self.metadata
        }


@dataclass
class ActionResult:
    """Result of executing an action."""
    action_index: int
    action_type: ActionType
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0
    side_effects: List[str] = field(default_factory=list)
    before_snapshot: Optional[ActionSnapshot] = None
    after_snapshot: Optional[ActionSnapshot] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_index": self.action_index,
            "action_type": self.action_type.value,
            "success": self.success,
            "output": str(self.output) if self.output else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "side_effects": self.side_effects,
            "before_snapshot": self.before_snapshot.to_dict() if self.before_snapshot else None,
            "after_snapshot": self.after_snapshot.to_dict() if self.after_snapshot else None
        }


@dataclass
class TrialAction:
    """An action to perform in a trial."""
    index: int
    action_type: ActionType
    description: str
    params: Dict[str, Any]
    expected_output: Optional[Any] = None
    dependencies: List[int] = field(default_factory=list)  # Indices of dependent actions
    rollback_action: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 60
    retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "type": self.action_type.value,
            "description": self.description,
            "params": self.params,
            "expected_output": self.expected_output,
            "dependencies": self.dependencies,
            "rollback_action": self.rollback_action,
            "timeout_seconds": self.timeout_seconds,
            "retries": self.retries
        }


@dataclass
class TrialRunResult:
    """Result of a trial run."""
    trial_id: str
    is_dry_run: bool
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    action_results: List[ActionResult]
    issues: List[TrialIssue]
    initial_snapshot: Optional[ActionSnapshot]
    final_snapshot: Optional[ActionSnapshot]
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def blocking_issues(self) -> List[TrialIssue]:
        return [i for i in self.issues if not i.can_proceed]

    @property
    def can_proceed(self) -> bool:
        return len(self.blocking_issues) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "is_dry_run": self.is_dry_run,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "action_results": [r.to_dict() for r in self.action_results],
            "issues": [i.to_dict() for i in self.issues],
            "initial_snapshot": self.initial_snapshot.to_dict() if self.initial_snapshot else None,
            "final_snapshot": self.final_snapshot.to_dict() if self.final_snapshot else None,
            "variables": self.variables,
            "metadata": self.metadata,
            "has_issues": self.has_issues,
            "can_proceed": self.can_proceed
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        status = "" if self.success else ""
        mode = "Dry Run" if self.is_dry_run else "Actual Run"

        lines = [
            f"# Trial Run Report {status}",
            "",
            f"**Mode**: {mode}",
            f"**Started**: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Completed**: {self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else 'In Progress'}",
            f"**Success**: {'Yes' if self.success else 'No'}",
            "",
            "## Actions",
            ""
        ]

        for result in self.action_results:
            status_icon = "" if result.success else ""
            lines.append(f"### {status_icon} Action {result.action_index + 1}: {result.action_type.value}")
            if result.error:
                lines.append(f"**Error**: {result.error}")
            if result.duration_ms > 0:
                lines.append(f"**Duration**: {result.duration_ms:.2f}ms")
            lines.append("")

        if self.issues:
            lines.extend(["## Issues", ""])
            for issue in self.issues:
                icon = {
                    IssueSeverity.LOW: "",
                    IssueSeverity.MEDIUM: "",
                    IssueSeverity.HIGH: "",
                    IssueSeverity.CRITICAL: ""
                }.get(issue.severity, "")
                lines.append(f"### {icon} {issue.issue_type.value}")
                lines.append(f"**Severity**: {issue.severity.value}")
                lines.append(f"**Description**: {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"**Suggested Fix**: {issue.suggested_fix}")
                lines.append(f"**Can Proceed**: {'Yes' if issue.can_proceed else 'No'}")
                lines.append("")

        return "\n".join(lines)


@dataclass
class TrialRun:
    """A trial run definition."""
    id: str
    name: str
    description: str
    created_at: datetime
    validation_level: ValidationLevel
    actions: List[TrialAction]
    context: Dict[str, Any]
    dry_run_result: Optional[TrialRunResult] = None
    actual_result: Optional[TrialRunResult] = None
    is_executed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "validation_level": self.validation_level.value,
            "actions": [a.to_dict() for a in self.actions],
            "context": self.context,
            "dry_run_result": self.dry_run_result.to_dict() if self.dry_run_result else None,
            "actual_result": self.actual_result.to_dict() if self.actual_result else None,
            "is_executed": self.is_executed,
            "metadata": self.metadata
        }


@dataclass
class ResultComparison:
    """Comparison between dry run and actual results."""
    trial_id: str
    match_percentage: float
    action_comparisons: List[Dict[str, Any]]
    divergences: List[Dict[str, Any]]
    unexpected_side_effects: List[str]
    missing_side_effects: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "match_percentage": self.match_percentage,
            "action_comparisons": self.action_comparisons,
            "divergences": self.divergences,
            "unexpected_side_effects": self.unexpected_side_effects,
            "missing_side_effects": self.missing_side_effects
        }


class TrialRunService:
    """
    Service for trial run validation.

    Provides:
    - Trial run creation and management
    - Dry run execution with validation
    - Actual execution with comparison
    - Issue detection and reporting
    - Rollback planning
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/trial_runs")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.trials: Dict[str, TrialRun] = {}
        self.action_handlers: Dict[ActionType, Callable] = {}
        self.validators: Dict[ActionType, Callable] = {}
        self._register_default_handlers()
        self._load_trials()

    def _load_trials(self) -> None:
        """Load trials from storage."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                trial = self._trial_from_dict(data)
                self.trials[trial.id] = trial
            except Exception:
                pass

    def _trial_from_dict(self, data: Dict[str, Any]) -> TrialRun:
        """Reconstruct trial from dictionary."""
        actions = [
            TrialAction(
                index=a["index"],
                action_type=ActionType(a["type"]),
                description=a.get("description", ""),
                params=a.get("params", {}),
                expected_output=a.get("expected_output"),
                dependencies=a.get("dependencies", []),
                rollback_action=a.get("rollback_action"),
                timeout_seconds=a.get("timeout_seconds", 60),
                retries=a.get("retries", 0)
            )
            for a in data.get("actions", [])
        ]

        return TrialRun(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            validation_level=ValidationLevel(data.get("validation_level", "syntax")),
            actions=actions,
            context=data.get("context", {}),
            is_executed=data.get("is_executed", False),
            metadata=data.get("metadata", {})
        )

    def _save_trial(self, trial: TrialRun) -> None:
        """Persist trial to storage."""
        file_path = self.storage_path / f"{trial.id}.json"
        file_path.write_text(json.dumps(trial.to_dict(), indent=2, default=str))

    def _register_default_handlers(self) -> None:
        """Register default action handlers for dry run."""
        self.validators[ActionType.CREATE_FILE] = self._validate_create_file
        self.validators[ActionType.MODIFY_FILE] = self._validate_modify_file
        self.validators[ActionType.DELETE_FILE] = self._validate_delete_file
        self.validators[ActionType.RUN_COMMAND] = self._validate_run_command
        self.validators[ActionType.RUN_TESTS] = self._validate_run_tests

    async def _validate_create_file(self, action: TrialAction, context: Dict[str, Any]) -> Tuple[bool, List[TrialIssue]]:
        """Validate file creation."""
        issues = []
        path = action.params.get("path", "")

        # Check if file already exists
        if Path(path).exists():
            issues.append(TrialIssue(
                id=str(uuid.uuid4()),
                issue_type=IssueType.FILE_CONFLICT,
                severity=IssueSeverity.HIGH,
                action_index=action.index,
                description=f"File already exists: {path}",
                details={"path": path},
                suggested_fix="Delete existing file or use modify action",
                can_proceed=False
            ))

        # Check if parent directory exists
        parent = Path(path).parent
        if not parent.exists():
            issues.append(TrialIssue(
                id=str(uuid.uuid4()),
                issue_type=IssueType.DEPENDENCY_MISSING,
                severity=IssueSeverity.MEDIUM,
                action_index=action.index,
                description=f"Parent directory does not exist: {parent}",
                details={"parent": str(parent)},
                suggested_fix="Create parent directory first",
                can_proceed=True
            ))

        # Validate content if provided
        content = action.params.get("content", "")
        if path.endswith(".py"):
            try:
                compile(content, path, "exec")
            except SyntaxError as e:
                issues.append(TrialIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.SYNTAX_ERROR,
                    severity=IssueSeverity.HIGH,
                    action_index=action.index,
                    description=f"Python syntax error: {e.msg}",
                    details={"line": e.lineno, "offset": e.offset},
                    suggested_fix="Fix syntax error before creating file",
                    can_proceed=False
                ))

        return len([i for i in issues if not i.can_proceed]) == 0, issues

    async def _validate_modify_file(self, action: TrialAction, context: Dict[str, Any]) -> Tuple[bool, List[TrialIssue]]:
        """Validate file modification."""
        issues = []
        path = action.params.get("path", "")

        # Check if file exists
        if not Path(path).exists():
            issues.append(TrialIssue(
                id=str(uuid.uuid4()),
                issue_type=IssueType.DEPENDENCY_MISSING,
                severity=IssueSeverity.CRITICAL,
                action_index=action.index,
                description=f"File does not exist: {path}",
                details={"path": path},
                suggested_fix="Use create action or check file path",
                can_proceed=False
            ))

        return len([i for i in issues if not i.can_proceed]) == 0, issues

    async def _validate_delete_file(self, action: TrialAction, context: Dict[str, Any]) -> Tuple[bool, List[TrialIssue]]:
        """Validate file deletion."""
        issues = []
        path = action.params.get("path", "")

        # Check if file exists
        if not Path(path).exists():
            issues.append(TrialIssue(
                id=str(uuid.uuid4()),
                issue_type=IssueType.WARNING,
                severity=IssueSeverity.LOW,
                action_index=action.index,
                description=f"File does not exist: {path}",
                details={"path": path},
                can_proceed=True
            ))

        # Check for rollback capability
        if not action.rollback_action:
            issues.append(TrialIssue(
                id=str(uuid.uuid4()),
                issue_type=IssueType.ROLLBACK_IMPOSSIBLE,
                severity=IssueSeverity.MEDIUM,
                action_index=action.index,
                description="No rollback action defined for file deletion",
                details={"path": path},
                suggested_fix="Define rollback action with file content backup",
                can_proceed=True
            ))

        return True, issues

    async def _validate_run_command(self, action: TrialAction, context: Dict[str, Any]) -> Tuple[bool, List[TrialIssue]]:
        """Validate command execution."""
        issues = []
        command = action.params.get("command", "")

        # Check for dangerous commands
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"sudo\s+rm",
            r">\s*/dev/",
            r":\(\)\{\s*:\|:\s*&\s*\}",  # Fork bomb
            r"mkfs\.",
            r"dd\s+if=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command):
                issues.append(TrialIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.PERMISSION_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    action_index=action.index,
                    description=f"Potentially dangerous command detected",
                    details={"command": command, "pattern": pattern},
                    can_proceed=False
                ))

        return len([i for i in issues if not i.can_proceed]) == 0, issues

    async def _validate_run_tests(self, action: TrialAction, context: Dict[str, Any]) -> Tuple[bool, List[TrialIssue]]:
        """Validate test execution."""
        issues = []
        pattern = action.params.get("pattern", "")

        # Check if test files exist
        test_path = action.params.get("path", ".")
        if not Path(test_path).exists():
            issues.append(TrialIssue(
                id=str(uuid.uuid4()),
                issue_type=IssueType.DEPENDENCY_MISSING,
                severity=IssueSeverity.MEDIUM,
                action_index=action.index,
                description=f"Test path does not exist: {test_path}",
                details={"path": test_path, "pattern": pattern},
                can_proceed=True
            ))

        return True, issues

    def register_validator(self, action_type: ActionType, validator: Callable) -> None:
        """Register a custom validator for an action type."""
        self.validators[action_type] = validator

    def register_handler(self, action_type: ActionType, handler: Callable) -> None:
        """Register a custom handler for actual execution."""
        self.action_handlers[action_type] = handler

    def create_trial(
        self,
        name: str,
        actions: List[Dict[str, Any]],
        description: str = "",
        validation_level: str = "syntax",
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TrialRun:
        """
        Create a new trial run.

        Args:
            name: Trial name
            actions: List of action definitions
            description: Trial description
            validation_level: Level of validation
            context: Initial context
            metadata: Additional metadata

        Returns:
            Created TrialRun
        """
        parsed_actions = []
        for i, a in enumerate(actions):
            action_type = ActionType(a.get("type", "custom"))

            # Generate rollback action if not provided
            rollback = a.get("rollback")
            if not rollback and action_type == ActionType.CREATE_FILE:
                rollback = {
                    "type": "delete_file",
                    "params": {"path": a.get("params", {}).get("path")}
                }

            parsed_actions.append(TrialAction(
                index=i,
                action_type=action_type,
                description=a.get("description", ""),
                params=a.get("params", {}),
                expected_output=a.get("expected_output"),
                dependencies=a.get("dependencies", []),
                rollback_action=rollback,
                timeout_seconds=a.get("timeout_seconds", 60),
                retries=a.get("retries", 0)
            ))

        trial = TrialRun(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=datetime.now(),
            validation_level=ValidationLevel(validation_level),
            actions=parsed_actions,
            context=context or {},
            metadata=metadata or {}
        )

        self.trials[trial.id] = trial
        self._save_trial(trial)
        return trial

    def get_trial(self, trial_id: str) -> Optional[TrialRun]:
        """Get trial by ID."""
        return self.trials.get(trial_id)

    def list_trials(self, include_executed: bool = True) -> List[TrialRun]:
        """List all trials."""
        trials = list(self.trials.values())
        if not include_executed:
            trials = [t for t in trials if not t.is_executed]
        return sorted(trials, key=lambda t: t.created_at, reverse=True)

    def delete_trial(self, trial_id: str) -> bool:
        """Delete a trial."""
        if trial_id in self.trials:
            del self.trials[trial_id]
            file_path = self.storage_path / f"{trial_id}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        return False

    async def execute_dry_run(self, trial_id: str) -> TrialRunResult:
        """
        Execute a trial as a dry run (validation only).

        Args:
            trial_id: Trial ID

        Returns:
            TrialRunResult with validation results
        """
        trial = self.get_trial(trial_id)
        if not trial:
            return TrialRunResult(
                trial_id=trial_id,
                is_dry_run=True,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                success=False,
                action_results=[],
                issues=[TrialIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.DEPENDENCY_MISSING,
                    severity=IssueSeverity.CRITICAL,
                    action_index=-1,
                    description=f"Trial '{trial_id}' not found",
                    details={},
                    can_proceed=False
                )],
                initial_snapshot=None,
                final_snapshot=None
            )

        started_at = datetime.now()
        action_results = []
        all_issues = []
        context = copy.deepcopy(trial.context)

        # Take initial snapshot
        initial_snapshot = self._take_snapshot(-1, context)

        # Validate each action
        for action in trial.actions:
            action_start = datetime.now()

            # Check dependencies
            for dep_index in action.dependencies:
                if dep_index < len(action_results):
                    if not action_results[dep_index].success:
                        all_issues.append(TrialIssue(
                            id=str(uuid.uuid4()),
                            issue_type=IssueType.DEPENDENCY_MISSING,
                            severity=IssueSeverity.HIGH,
                            action_index=action.index,
                            description=f"Dependent action {dep_index} failed",
                            details={"dependency": dep_index},
                            can_proceed=False
                        ))

            # Run validator
            success = True
            issues = []
            if action.action_type in self.validators:
                validator = self.validators[action.action_type]
                success, issues = await validator(action, context)
                all_issues.extend(issues)

            action_end = datetime.now()
            duration_ms = (action_end - action_start).total_seconds() * 1000

            # Simulate expected output
            simulated_output = action.expected_output if success else None

            action_results.append(ActionResult(
                action_index=action.index,
                action_type=action.action_type,
                success=success,
                output=simulated_output,
                error=issues[0].description if issues and not success else None,
                duration_ms=duration_ms,
                side_effects=self._predict_side_effects(action)
            ))

        # Take final snapshot
        final_snapshot = self._take_snapshot(len(trial.actions) - 1, context)

        # Determine overall success
        blocking_issues = [i for i in all_issues if not i.can_proceed]
        overall_success = len(blocking_issues) == 0

        result = TrialRunResult(
            trial_id=trial_id,
            is_dry_run=True,
            started_at=started_at,
            completed_at=datetime.now(),
            success=overall_success,
            action_results=action_results,
            issues=all_issues,
            initial_snapshot=initial_snapshot,
            final_snapshot=final_snapshot,
            variables=context
        )

        trial.dry_run_result = result
        self._save_trial(trial)

        return result

    async def execute_actual(self, trial_id: str, skip_dry_run: bool = False) -> TrialRunResult:
        """
        Execute a trial for real.

        Args:
            trial_id: Trial ID
            skip_dry_run: Skip dry run validation

        Returns:
            TrialRunResult with actual results
        """
        trial = self.get_trial(trial_id)
        if not trial:
            return TrialRunResult(
                trial_id=trial_id,
                is_dry_run=False,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                success=False,
                action_results=[],
                issues=[],
                initial_snapshot=None,
                final_snapshot=None
            )

        # Check if dry run was performed
        if not skip_dry_run and not trial.dry_run_result:
            dry_result = await self.execute_dry_run(trial_id)
            if not dry_result.can_proceed:
                return TrialRunResult(
                    trial_id=trial_id,
                    is_dry_run=False,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    success=False,
                    action_results=[],
                    issues=dry_result.issues,
                    initial_snapshot=None,
                    final_snapshot=None,
                    metadata={"blocked_by_dry_run": True}
                )

        started_at = datetime.now()
        action_results = []
        context = copy.deepcopy(trial.context)

        # Take initial snapshot
        initial_snapshot = self._take_snapshot(-1, context)

        # Execute each action
        for action in trial.actions:
            before_snapshot = self._take_snapshot(action.index, context)
            action_start = datetime.now()

            success = True
            output = None
            error = None
            side_effects = []

            if action.action_type in self.action_handlers:
                try:
                    handler = self.action_handlers[action.action_type]
                    output = await handler(action, context)
                except Exception as e:
                    success = False
                    error = str(e)
            else:
                # Simulate success for unhandled actions
                output = action.expected_output

            action_end = datetime.now()
            duration_ms = (action_end - action_start).total_seconds() * 1000

            after_snapshot = self._take_snapshot(action.index, context)

            # Detect side effects
            side_effects = self._detect_side_effects(before_snapshot, after_snapshot)

            action_results.append(ActionResult(
                action_index=action.index,
                action_type=action.action_type,
                success=success,
                output=output,
                error=error,
                duration_ms=duration_ms,
                side_effects=side_effects,
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot
            ))

            if not success:
                break

        # Take final snapshot
        final_snapshot = self._take_snapshot(len(trial.actions) - 1, context)

        # Determine overall success
        overall_success = all(r.success for r in action_results)

        result = TrialRunResult(
            trial_id=trial_id,
            is_dry_run=False,
            started_at=started_at,
            completed_at=datetime.now(),
            success=overall_success,
            action_results=action_results,
            issues=[],
            initial_snapshot=initial_snapshot,
            final_snapshot=final_snapshot,
            variables=context
        )

        trial.actual_result = result
        trial.is_executed = True
        self._save_trial(trial)

        return result

    def compare_results(self, trial_id: str) -> Optional[ResultComparison]:
        """
        Compare dry run and actual results.

        Args:
            trial_id: Trial ID

        Returns:
            ResultComparison or None if not both results exist
        """
        trial = self.get_trial(trial_id)
        if not trial or not trial.dry_run_result or not trial.actual_result:
            return None

        dry = trial.dry_run_result
        actual = trial.actual_result

        action_comparisons = []
        divergences = []
        total_actions = len(dry.action_results)
        matching_actions = 0

        for i, (dry_action, actual_action) in enumerate(zip(dry.action_results, actual.action_results)):
            matches = dry_action.success == actual_action.success

            comparison = {
                "action_index": i,
                "dry_success": dry_action.success,
                "actual_success": actual_action.success,
                "matches": matches,
                "dry_output": str(dry_action.output)[:100] if dry_action.output else None,
                "actual_output": str(actual_action.output)[:100] if actual_action.output else None
            }

            action_comparisons.append(comparison)

            if matches:
                matching_actions += 1
            else:
                divergences.append({
                    "action_index": i,
                    "type": "outcome_mismatch",
                    "expected": "success" if dry_action.success else "failure",
                    "actual": "success" if actual_action.success else "failure"
                })

        # Compare side effects
        dry_side_effects = set()
        actual_side_effects = set()

        for r in dry.action_results:
            dry_side_effects.update(r.side_effects)
        for r in actual.action_results:
            actual_side_effects.update(r.side_effects)

        unexpected = list(actual_side_effects - dry_side_effects)
        missing = list(dry_side_effects - actual_side_effects)

        match_percentage = (matching_actions / total_actions * 100) if total_actions > 0 else 100

        return ResultComparison(
            trial_id=trial_id,
            match_percentage=match_percentage,
            action_comparisons=action_comparisons,
            divergences=divergences,
            unexpected_side_effects=unexpected,
            missing_side_effects=missing
        )

    def _take_snapshot(self, action_index: int, context: Dict[str, Any]) -> ActionSnapshot:
        """Take a snapshot of current state."""
        return ActionSnapshot(
            action_index=action_index,
            timestamp=datetime.now(),
            files_state={},  # Would capture actual file hashes in real implementation
            variables=copy.deepcopy(context)
        )

    def _predict_side_effects(self, action: TrialAction) -> List[str]:
        """Predict side effects of an action."""
        effects = []

        if action.action_type == ActionType.CREATE_FILE:
            path = action.params.get("path", "")
            effects.append(f"file_created:{path}")

        elif action.action_type == ActionType.MODIFY_FILE:
            path = action.params.get("path", "")
            effects.append(f"file_modified:{path}")

        elif action.action_type == ActionType.DELETE_FILE:
            path = action.params.get("path", "")
            effects.append(f"file_deleted:{path}")

        elif action.action_type == ActionType.RUN_COMMAND:
            effects.append("command_executed")

        elif action.action_type == ActionType.RUN_TESTS:
            effects.append("tests_executed")

        return effects

    def _detect_side_effects(
        self,
        before: ActionSnapshot,
        after: ActionSnapshot
    ) -> List[str]:
        """Detect actual side effects between snapshots."""
        effects = []

        # Compare file states
        for path, hash_val in after.files_state.items():
            if path not in before.files_state:
                effects.append(f"file_created:{path}")
            elif before.files_state[path] != hash_val:
                effects.append(f"file_modified:{path}")

        for path in before.files_state:
            if path not in after.files_state:
                effects.append(f"file_deleted:{path}")

        # Compare variables
        for key, value in after.variables.items():
            if key not in before.variables:
                effects.append(f"variable_created:{key}")
            elif before.variables[key] != value:
                effects.append(f"variable_changed:{key}")

        return effects

    def get_rollback_plan(self, trial_id: str) -> List[Dict[str, Any]]:
        """
        Generate a rollback plan for a trial.

        Args:
            trial_id: Trial ID

        Returns:
            List of rollback actions in reverse order
        """
        trial = self.get_trial(trial_id)
        if not trial:
            return []

        rollback_actions = []
        for action in reversed(trial.actions):
            if action.rollback_action:
                rollback_actions.append({
                    "original_action": action.index,
                    "rollback": action.rollback_action
                })
            else:
                rollback_actions.append({
                    "original_action": action.index,
                    "rollback": None,
                    "warning": "No rollback action defined"
                })

        return rollback_actions
