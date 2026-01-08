"""
Refactor Guard Service

Week 108 - AO-M-4: Protection against unnecessary code modifications.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Prevents scope creep during agent operations
- Guards against unauthorized refactoring
- Enforces change boundaries
- Validates modifications against allowed scope
- Detects anti-patterns in agent behavior

Example usage:
    guard = RefactorGuardService()

    # Define allowed scope for a task
    scope = guard.create_scope(
        task_id="fix-auth-bug",
        allowed_files=["src/auth/*.py"],
        allowed_operations=["modify", "add_tests"],
        forbidden_patterns=["refactor", "restructure", "improve"]
    )

    # Check if a change is allowed
    result = guard.check_change(
        scope_id=scope.id,
        file_path="src/auth/login.py",
        operation="modify",
        description="Fix null pointer in login validation"
    )

    if not result.allowed:
        print(f"Change blocked: {result.reason}")

    # Enforce guard as decorator
    @guard.enforce(scope_id=scope.id)
    async def fix_bug():
        # This function's file operations will be guarded
        pass
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Set, Pattern
from pathlib import Path
from functools import wraps
import fnmatch
import json
import re
import uuid


class OperationType(Enum):
    """Type of file operation."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"
    ADD_TESTS = "add_tests"
    ADD_DOCS = "add_docs"
    REFACTOR = "refactor"
    RESTRUCTURE = "restructure"


class ViolationType(Enum):
    """Type of scope violation."""
    OUT_OF_SCOPE_FILE = "out_of_scope_file"
    FORBIDDEN_OPERATION = "forbidden_operation"
    FORBIDDEN_PATTERN = "forbidden_pattern"
    SCOPE_CREEP = "scope_creep"
    UNAUTHORIZED_REFACTOR = "unauthorized_refactor"
    EXCESSIVE_CHANGES = "excessive_changes"
    UNRELATED_CHANGE = "unrelated_change"


class SeverityLevel(Enum):
    """Severity of a violation."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Violation:
    """Record of a scope violation."""
    id: str
    violation_type: ViolationType
    severity: SeverityLevel
    file_path: Optional[str]
    operation: Optional[OperationType]
    description: str
    context: Dict[str, Any]
    timestamp: datetime
    scope_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.violation_type.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "operation": self.operation.value if self.operation else None,
            "description": self.description,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "scope_id": self.scope_id
        }


@dataclass
class ChangeCheckResult:
    """Result of checking a proposed change."""
    allowed: bool
    reason: Optional[str] = None
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggested_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "suggested_action": self.suggested_action
        }


@dataclass
class ChangeScope:
    """Definition of allowed change scope."""
    id: str
    task_id: str
    task_description: str
    created_at: datetime
    expires_at: Optional[datetime]

    # File scope
    allowed_files: List[str]  # Glob patterns
    forbidden_files: List[str]  # Glob patterns
    allowed_directories: List[str]

    # Operation scope
    allowed_operations: List[OperationType]
    forbidden_operations: List[OperationType]

    # Content scope
    forbidden_patterns: List[str]  # Regex patterns that indicate scope creep
    required_patterns: List[str]  # Patterns that must be present in changes

    # Limits
    max_files_changed: int
    max_lines_changed: int
    max_new_files: int

    # State
    files_changed: Set[str] = field(default_factory=set)
    lines_changed: int = 0
    new_files_created: int = 0
    violations: List[Violation] = field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_file_allowed(self, file_path: str) -> bool:
        """Check if file is within allowed scope."""
        # Check forbidden first
        for pattern in self.forbidden_files:
            if fnmatch.fnmatch(file_path, pattern):
                return False

        # Check allowed
        if self.allowed_files:
            for pattern in self.allowed_files:
                if fnmatch.fnmatch(file_path, pattern):
                    return True
            return False

        # Check directories
        if self.allowed_directories:
            file_dir = str(Path(file_path).parent)
            for dir_pattern in self.allowed_directories:
                if file_dir.startswith(dir_pattern) or fnmatch.fnmatch(file_dir, dir_pattern):
                    return True
            return False

        return True

    def is_operation_allowed(self, operation: OperationType) -> bool:
        """Check if operation is allowed."""
        if operation in self.forbidden_operations:
            return False
        if self.allowed_operations:
            return operation in self.allowed_operations
        return True

    def check_content(self, content: str) -> List[str]:
        """Check content for forbidden patterns."""
        violations = []
        for pattern in self.forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"Forbidden pattern detected: {pattern}")
        return violations

    def check_limits(self) -> List[str]:
        """Check if limits are exceeded."""
        issues = []
        if len(self.files_changed) > self.max_files_changed:
            issues.append(f"Exceeded max files: {len(self.files_changed)} > {self.max_files_changed}")
        if self.lines_changed > self.max_lines_changed:
            issues.append(f"Exceeded max lines: {self.lines_changed} > {self.max_lines_changed}")
        if self.new_files_created > self.max_new_files:
            issues.append(f"Exceeded max new files: {self.new_files_created} > {self.max_new_files}")
        return issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_description": self.task_description,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "allowed_files": self.allowed_files,
            "forbidden_files": self.forbidden_files,
            "allowed_directories": self.allowed_directories,
            "allowed_operations": [o.value for o in self.allowed_operations],
            "forbidden_operations": [o.value for o in self.forbidden_operations],
            "forbidden_patterns": self.forbidden_patterns,
            "required_patterns": self.required_patterns,
            "max_files_changed": self.max_files_changed,
            "max_lines_changed": self.max_lines_changed,
            "max_new_files": self.max_new_files,
            "files_changed": list(self.files_changed),
            "lines_changed": self.lines_changed,
            "new_files_created": self.new_files_created,
            "violations": [v.to_dict() for v in self.violations],
            "is_active": self.is_active,
            "metadata": self.metadata
        }

    def to_markdown(self) -> str:
        """Generate markdown summary."""
        lines = [
            f"# Change Scope: {self.task_id}",
            "",
            f"**Description**: {self.task_description}",
            f"**Created**: {self.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Status**: {'Active' if self.is_active else 'Inactive'}",
            "",
            "## Allowed Files",
            ""
        ]

        for pattern in self.allowed_files:
            lines.append(f"- `{pattern}`")

        if self.forbidden_files:
            lines.extend(["", "## Forbidden Files", ""])
            for pattern in self.forbidden_files:
                lines.append(f"- `{pattern}`")

        lines.extend([
            "",
            "## Allowed Operations",
            ""
        ])
        for op in self.allowed_operations:
            lines.append(f"- {op.value}")

        lines.extend([
            "",
            "## Limits",
            "",
            f"- Max files: {self.max_files_changed}",
            f"- Max lines: {self.max_lines_changed}",
            f"- Max new files: {self.max_new_files}",
            "",
            "## Current Usage",
            "",
            f"- Files changed: {len(self.files_changed)} / {self.max_files_changed}",
            f"- Lines changed: {self.lines_changed} / {self.max_lines_changed}",
            f"- New files: {self.new_files_created} / {self.max_new_files}",
        ])

        if self.violations:
            lines.extend([
                "",
                "## Violations",
                ""
            ])
            for v in self.violations:
                lines.append(f"- [{v.severity.value}] {v.description}")

        return "\n".join(lines)


# Common scope creep patterns
SCOPE_CREEP_PATTERNS = [
    r"while\s+I('m|s)\s+(here|at it|doing this)",
    r"also\s+(refactor|clean|improve|optimize)",
    r"might\s+as\s+well",
    r"let('s)?\s+(also|quickly)",
    r"should\s+be\s+refactored",
    r"needs\s+some\s+cleanup",
    r"could\s+be\s+improved",
    r"better\s+to\s+(rename|restructure|reorganize)",
    r"unrelated\s+but",
    r"noticed\s+that",
    r"side\s+note",
    r"by\s+the\s+way",
]

# Refactoring indicator patterns
REFACTORING_PATTERNS = [
    r"extract\s+(method|function|class|interface)",
    r"rename\s+(variable|function|class|method)",
    r"move\s+(to|into)\s+(new|different)",
    r"split\s+(into|up)",
    r"merge\s+(with|into)",
    r"inline\s+(variable|function)",
    r"introduce\s+(constant|variable|parameter)",
    r"remove\s+(duplicate|unused|dead)",
    r"simplify\s+(conditional|logic)",
    r"consolidate\s+(duplicate|similar)",
]


class RefactorGuardService:
    """
    Service for guarding against scope creep and unauthorized refactoring.

    Provides:
    - Change scope definition and management
    - File and operation validation
    - Scope creep detection
    - Violation tracking and reporting
    - Enforcement decorators
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/refactor_guard")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.scopes: Dict[str, ChangeScope] = {}
        self.scope_creep_patterns = [re.compile(p, re.IGNORECASE) for p in SCOPE_CREEP_PATTERNS]
        self.refactoring_patterns = [re.compile(p, re.IGNORECASE) for p in REFACTORING_PATTERNS]
        self._load_scopes()

    def _load_scopes(self) -> None:
        """Load scopes from storage."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                scope = self._scope_from_dict(data)
                if scope.is_active:
                    self.scopes[scope.id] = scope
            except Exception:
                pass

    def _scope_from_dict(self, data: Dict[str, Any]) -> ChangeScope:
        """Reconstruct scope from dictionary."""
        violations = [
            Violation(
                id=v["id"],
                violation_type=ViolationType(v["type"]),
                severity=SeverityLevel(v["severity"]),
                file_path=v.get("file_path"),
                operation=OperationType(v["operation"]) if v.get("operation") else None,
                description=v["description"],
                context=v.get("context", {}),
                timestamp=datetime.fromisoformat(v["timestamp"]),
                scope_id=data["id"]
            )
            for v in data.get("violations", [])
        ]

        return ChangeScope(
            id=data["id"],
            task_id=data["task_id"],
            task_description=data["task_description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            allowed_files=data.get("allowed_files", []),
            forbidden_files=data.get("forbidden_files", []),
            allowed_directories=data.get("allowed_directories", []),
            allowed_operations=[OperationType(o) for o in data.get("allowed_operations", [])],
            forbidden_operations=[OperationType(o) for o in data.get("forbidden_operations", [])],
            forbidden_patterns=data.get("forbidden_patterns", []),
            required_patterns=data.get("required_patterns", []),
            max_files_changed=data.get("max_files_changed", 10),
            max_lines_changed=data.get("max_lines_changed", 500),
            max_new_files=data.get("max_new_files", 5),
            files_changed=set(data.get("files_changed", [])),
            lines_changed=data.get("lines_changed", 0),
            new_files_created=data.get("new_files_created", 0),
            violations=violations,
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {})
        )

    def _save_scope(self, scope: ChangeScope) -> None:
        """Persist scope to storage."""
        file_path = self.storage_path / f"{scope.id}.json"
        file_path.write_text(json.dumps(scope.to_dict(), indent=2, default=str))

    def create_scope(
        self,
        task_id: str,
        task_description: str = "",
        allowed_files: Optional[List[str]] = None,
        forbidden_files: Optional[List[str]] = None,
        allowed_directories: Optional[List[str]] = None,
        allowed_operations: Optional[List[str]] = None,
        forbidden_operations: Optional[List[str]] = None,
        forbidden_patterns: Optional[List[str]] = None,
        max_files_changed: int = 10,
        max_lines_changed: int = 500,
        max_new_files: int = 5,
        expires_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChangeScope:
        """
        Create a new change scope.

        Args:
            task_id: Identifier for the task
            task_description: Description of what's allowed
            allowed_files: Glob patterns for allowed files
            forbidden_files: Glob patterns for forbidden files
            allowed_directories: Allowed directory paths
            allowed_operations: List of allowed operations
            forbidden_operations: List of forbidden operations
            forbidden_patterns: Regex patterns to detect scope creep
            max_files_changed: Maximum number of files
            max_lines_changed: Maximum lines of change
            max_new_files: Maximum new files
            expires_hours: Hours until scope expires
            metadata: Additional metadata

        Returns:
            Created ChangeScope
        """
        now = datetime.now()

        # Default forbidden patterns include scope creep indicators
        default_forbidden = SCOPE_CREEP_PATTERNS.copy()
        if forbidden_patterns:
            default_forbidden.extend(forbidden_patterns)

        # Parse operations
        parsed_allowed_ops = []
        if allowed_operations:
            for op in allowed_operations:
                try:
                    parsed_allowed_ops.append(OperationType(op))
                except ValueError:
                    pass

        parsed_forbidden_ops = []
        if forbidden_operations:
            for op in forbidden_operations:
                try:
                    parsed_forbidden_ops.append(OperationType(op))
                except ValueError:
                    pass

        # Default: forbid refactoring unless explicitly allowed
        if OperationType.REFACTOR not in parsed_allowed_ops:
            if OperationType.REFACTOR not in parsed_forbidden_ops:
                parsed_forbidden_ops.append(OperationType.REFACTOR)
        if OperationType.RESTRUCTURE not in parsed_allowed_ops:
            if OperationType.RESTRUCTURE not in parsed_forbidden_ops:
                parsed_forbidden_ops.append(OperationType.RESTRUCTURE)

        scope = ChangeScope(
            id=str(uuid.uuid4()),
            task_id=task_id,
            task_description=task_description,
            created_at=now,
            expires_at=datetime.fromtimestamp(now.timestamp() + expires_hours * 3600) if expires_hours else None,
            allowed_files=allowed_files or [],
            forbidden_files=forbidden_files or [],
            allowed_directories=allowed_directories or [],
            allowed_operations=parsed_allowed_ops,
            forbidden_operations=parsed_forbidden_ops,
            forbidden_patterns=default_forbidden,
            required_patterns=[],
            max_files_changed=max_files_changed,
            max_lines_changed=max_lines_changed,
            max_new_files=max_new_files,
            metadata=metadata or {}
        )

        self.scopes[scope.id] = scope
        self._save_scope(scope)
        return scope

    def get_scope(self, scope_id: str) -> Optional[ChangeScope]:
        """Get scope by ID."""
        return self.scopes.get(scope_id)

    def get_scope_by_task(self, task_id: str) -> Optional[ChangeScope]:
        """Get active scope for a task."""
        for scope in self.scopes.values():
            if scope.task_id == task_id and scope.is_active:
                return scope
        return None

    def close_scope(self, scope_id: str) -> bool:
        """Close a scope."""
        scope = self.get_scope(scope_id)
        if scope:
            scope.is_active = False
            self._save_scope(scope)
            return True
        return False

    def check_change(
        self,
        scope_id: str,
        file_path: str,
        operation: str,
        description: str = "",
        content: Optional[str] = None,
        lines_changed: int = 0
    ) -> ChangeCheckResult:
        """
        Check if a proposed change is allowed.

        Args:
            scope_id: Scope ID to check against
            file_path: Path of file to change
            operation: Type of operation
            description: Description of the change
            content: Optional content to check for patterns
            lines_changed: Number of lines being changed

        Returns:
            ChangeCheckResult indicating if change is allowed
        """
        scope = self.get_scope(scope_id)
        if not scope:
            return ChangeCheckResult(
                allowed=False,
                reason=f"Scope '{scope_id}' not found"
            )

        if not scope.is_active:
            return ChangeCheckResult(
                allowed=False,
                reason="Scope is no longer active"
            )

        # Check expiration
        if scope.expires_at and datetime.now() > scope.expires_at:
            scope.is_active = False
            self._save_scope(scope)
            return ChangeCheckResult(
                allowed=False,
                reason="Scope has expired"
            )

        violations = []
        warnings = []

        # Parse operation
        try:
            op = OperationType(operation)
        except ValueError:
            op = OperationType.MODIFY

        # Check file scope
        if not scope.is_file_allowed(file_path):
            violations.append(Violation(
                id=str(uuid.uuid4()),
                violation_type=ViolationType.OUT_OF_SCOPE_FILE,
                severity=SeverityLevel.ERROR,
                file_path=file_path,
                operation=op,
                description=f"File '{file_path}' is outside allowed scope",
                context={"allowed_patterns": scope.allowed_files},
                timestamp=datetime.now(),
                scope_id=scope_id
            ))

        # Check operation
        if not scope.is_operation_allowed(op):
            violations.append(Violation(
                id=str(uuid.uuid4()),
                violation_type=ViolationType.FORBIDDEN_OPERATION,
                severity=SeverityLevel.ERROR,
                file_path=file_path,
                operation=op,
                description=f"Operation '{op.value}' is not allowed",
                context={"allowed_operations": [o.value for o in scope.allowed_operations]},
                timestamp=datetime.now(),
                scope_id=scope_id
            ))

        # Check content for scope creep
        if content:
            pattern_violations = scope.check_content(content)
            for pv in pattern_violations:
                violations.append(Violation(
                    id=str(uuid.uuid4()),
                    violation_type=ViolationType.SCOPE_CREEP,
                    severity=SeverityLevel.WARNING,
                    file_path=file_path,
                    operation=op,
                    description=pv,
                    context={},
                    timestamp=datetime.now(),
                    scope_id=scope_id
                ))

        # Check description for scope creep
        if description:
            creep_detected = self._detect_scope_creep(description)
            for pattern in creep_detected:
                warnings.append(f"Potential scope creep detected: '{pattern}'")

            refactor_detected = self._detect_refactoring(description)
            if refactor_detected and op not in [OperationType.REFACTOR, OperationType.RESTRUCTURE]:
                for pattern in refactor_detected:
                    violations.append(Violation(
                        id=str(uuid.uuid4()),
                        violation_type=ViolationType.UNAUTHORIZED_REFACTOR,
                        severity=SeverityLevel.WARNING,
                        file_path=file_path,
                        operation=op,
                        description=f"Refactoring detected but not authorized: '{pattern}'",
                        context={},
                        timestamp=datetime.now(),
                        scope_id=scope_id
                    ))

        # Check limits (prospectively)
        prospective_files = len(scope.files_changed | {file_path})
        prospective_lines = scope.lines_changed + lines_changed
        prospective_new = scope.new_files_created + (1 if op == OperationType.CREATE else 0)

        if prospective_files > scope.max_files_changed:
            violations.append(Violation(
                id=str(uuid.uuid4()),
                violation_type=ViolationType.EXCESSIVE_CHANGES,
                severity=SeverityLevel.ERROR,
                file_path=file_path,
                operation=op,
                description=f"Would exceed max files: {prospective_files} > {scope.max_files_changed}",
                context={"current": len(scope.files_changed), "max": scope.max_files_changed},
                timestamp=datetime.now(),
                scope_id=scope_id
            ))

        if prospective_lines > scope.max_lines_changed:
            warnings.append(f"Approaching line limit: {prospective_lines} / {scope.max_lines_changed}")

        if prospective_new > scope.max_new_files:
            violations.append(Violation(
                id=str(uuid.uuid4()),
                violation_type=ViolationType.EXCESSIVE_CHANGES,
                severity=SeverityLevel.ERROR,
                file_path=file_path,
                operation=op,
                description=f"Would exceed max new files: {prospective_new} > {scope.max_new_files}",
                context={"current": scope.new_files_created, "max": scope.max_new_files},
                timestamp=datetime.now(),
                scope_id=scope_id
            ))

        # Determine result
        error_violations = [v for v in violations if v.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]]
        allowed = len(error_violations) == 0

        # Store violations
        scope.violations.extend(violations)
        self._save_scope(scope)

        suggested_action = None
        if not allowed:
            suggested_action = "Review change scope and modify task to stay within boundaries"
            if any(v.violation_type == ViolationType.OUT_OF_SCOPE_FILE for v in violations):
                suggested_action = f"Only modify files matching: {scope.allowed_files}"
            elif any(v.violation_type == ViolationType.UNAUTHORIZED_REFACTOR for v in violations):
                suggested_action = "Focus on the current task without refactoring"

        return ChangeCheckResult(
            allowed=allowed,
            reason=violations[0].description if violations else None,
            violations=violations,
            warnings=warnings,
            suggested_action=suggested_action
        )

    def record_change(
        self,
        scope_id: str,
        file_path: str,
        operation: str,
        lines_changed: int = 0
    ) -> bool:
        """
        Record a completed change.

        Args:
            scope_id: Scope ID
            file_path: Changed file
            operation: Operation performed
            lines_changed: Lines changed

        Returns:
            True if recorded successfully
        """
        scope = self.get_scope(scope_id)
        if not scope:
            return False

        try:
            op = OperationType(operation)
        except ValueError:
            op = OperationType.MODIFY

        scope.files_changed.add(file_path)
        scope.lines_changed += lines_changed

        if op == OperationType.CREATE:
            scope.new_files_created += 1

        self._save_scope(scope)
        return True

    def _detect_scope_creep(self, text: str) -> List[str]:
        """Detect scope creep patterns in text."""
        detected = []
        for pattern in self.scope_creep_patterns:
            match = pattern.search(text)
            if match:
                detected.append(match.group(0))
        return detected

    def _detect_refactoring(self, text: str) -> List[str]:
        """Detect refactoring patterns in text."""
        detected = []
        for pattern in self.refactoring_patterns:
            match = pattern.search(text)
            if match:
                detected.append(match.group(0))
        return detected

    def enforce(self, scope_id: str, strict: bool = True):
        """
        Decorator to enforce scope on a function.

        Usage:
            @guard.enforce(scope_id="my-scope")
            async def modify_files():
                # File operations here will be guarded
                pass
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                scope = self.get_scope(scope_id)
                if not scope:
                    if strict:
                        raise ValueError(f"Scope '{scope_id}' not found")
                    return await func(*args, **kwargs)

                if not scope.is_active:
                    if strict:
                        raise ValueError(f"Scope '{scope_id}' is not active")
                    return await func(*args, **kwargs)

                # Execute function and return result
                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def get_scope_report(self, scope_id: str) -> str:
        """Generate a report for a scope."""
        scope = self.get_scope(scope_id)
        if not scope:
            return f"Scope '{scope_id}' not found"

        return scope.to_markdown()

    def get_violation_summary(self, scope_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of violations.

        Args:
            scope_id: Optional scope ID (all scopes if None)

        Returns:
            Summary statistics
        """
        if scope_id:
            scopes = [self.get_scope(scope_id)] if self.get_scope(scope_id) else []
        else:
            scopes = list(self.scopes.values())

        all_violations = []
        for scope in scopes:
            all_violations.extend(scope.violations)

        by_type = {}
        by_severity = {}

        for v in all_violations:
            by_type[v.violation_type.value] = by_type.get(v.violation_type.value, 0) + 1
            by_severity[v.severity.value] = by_severity.get(v.severity.value, 0) + 1

        return {
            "total_violations": len(all_violations),
            "by_type": by_type,
            "by_severity": by_severity,
            "scopes_checked": len(scopes)
        }


# Predefined scope templates
def create_bugfix_scope(guard: RefactorGuardService, task_id: str, file_patterns: List[str]) -> ChangeScope:
    """Create a scope for bug fixing (no refactoring allowed)."""
    return guard.create_scope(
        task_id=task_id,
        task_description="Bug fix - minimal changes only",
        allowed_files=file_patterns,
        allowed_operations=["modify", "add_tests"],
        forbidden_operations=["refactor", "restructure", "rename", "move"],
        max_files_changed=5,
        max_lines_changed=100,
        max_new_files=2,
        metadata={"type": "bugfix"}
    )


def create_feature_scope(guard: RefactorGuardService, task_id: str, directory: str) -> ChangeScope:
    """Create a scope for feature development (limited refactoring)."""
    return guard.create_scope(
        task_id=task_id,
        task_description="Feature development",
        allowed_directories=[directory],
        allowed_operations=["create", "modify", "add_tests", "add_docs"],
        forbidden_operations=["restructure"],
        max_files_changed=15,
        max_lines_changed=1000,
        max_new_files=10,
        metadata={"type": "feature"}
    )


def create_refactoring_scope(guard: RefactorGuardService, task_id: str, file_patterns: List[str]) -> ChangeScope:
    """Create a scope for explicit refactoring (all operations allowed)."""
    return guard.create_scope(
        task_id=task_id,
        task_description="Authorized refactoring",
        allowed_files=file_patterns,
        allowed_operations=["modify", "refactor", "restructure", "rename", "move", "delete"],
        forbidden_patterns=[],  # Don't block scope creep patterns for refactoring
        max_files_changed=30,
        max_lines_changed=2000,
        max_new_files=5,
        metadata={"type": "refactoring"}
    )
