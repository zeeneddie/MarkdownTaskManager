"""
MP-M-2: Habit Hooks Service

Automated scripts triggered by pattern violations.
Enforces development habits through hooks that respond to events.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Register hooks for various trigger events
- Execute actions on violations (block, notify, log, script)
- Pre-configured default hooks for common violations
- Hook execution history and analytics

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Pattern
from uuid import UUID, uuid4
import logging
import re
import json

logger = logging.getLogger(__name__)


class HookTrigger(Enum):
    """Events that can trigger hooks."""
    ANTIPATTERN_DETECTED = "antipattern_detected"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    CONTEXT_LIMIT_APPROACHING = "context_limit_approaching"
    TDD_VIOLATION = "tdd_violation"
    SCOPE_CREEP = "scope_creep"
    COMMIT_WITHOUT_TESTS = "commit_without_tests"
    TEST_FAILURE = "test_failure"
    SECURITY_ISSUE = "security_issue"
    DEPENDENCY_OUTDATED = "dependency_outdated"
    CODE_COVERAGE_DROP = "code_coverage_drop"
    BREAKING_CHANGE = "breaking_change"
    LARGE_CHANGE = "large_change"
    CUSTOM = "custom"


class ActionType(Enum):
    """Types of actions hooks can perform."""
    LOG = "log"              # Log message only
    NOTIFICATION = "notification"  # Send notification to user
    BLOCK = "block"          # Block the operation
    SCRIPT = "script"        # Execute a script
    CALLBACK = "callback"    # Call a registered callback
    CHAIN = "chain"          # Chain to another hook


class SeverityLevel(Enum):
    """Severity of the hook action."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HookStatus(Enum):
    """Status of hook execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class HookAction:
    """Action to perform when hook triggers."""
    type: ActionType
    severity: SeverityLevel
    message: Optional[str] = None
    command: Optional[str] = None
    callback_name: Optional[str] = None
    chain_hook_id: Optional[UUID] = None
    timeout_seconds: int = 30
    retry_count: int = 0


@dataclass
class HookCondition:
    """Condition for hook execution."""
    field: str            # JSONPath or dot notation to field in event data
    operator: str         # eq, ne, gt, lt, gte, lte, contains, matches, exists
    value: Any            # Value to compare against
    case_sensitive: bool = True


@dataclass
class HabitHook:
    """A configured habit hook."""
    id: UUID
    name: str
    description: str
    trigger: HookTrigger
    action: HookAction
    conditions: List[HookCondition] = field(default_factory=list)
    enabled: bool = True
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 50  # 0-100, higher = earlier execution
    cooldown_seconds: int = 0  # Minimum time between executions


@dataclass
class HookExecution:
    """Record of a hook execution."""
    id: UUID
    hook_id: UUID
    hook_name: str
    trigger: HookTrigger
    trigger_data: Dict[str, Any]
    action_type: ActionType
    status: HookStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    blocked: bool = False


@dataclass
class HookEvent:
    """An event that may trigger hooks."""
    id: UUID
    trigger: HookTrigger
    data: Dict[str, Any]
    source: str
    timestamp: datetime
    session_id: Optional[UUID] = None


class HabitHooksService:
    """
    Service for managing and executing habit hooks.

    The "Habit Hooks" pattern uses automated triggers to enforce
    development habits and catch violations early.
    """

    # Allowed script commands for safety (whitelist)
    ALLOWED_SCRIPT_PREFIXES = [
        "echo ",
        "git status",
        "git diff",
        "npm test",
        "npm run lint",
        "pytest",
        "make test",
        "cargo test",
        "go test",
    ]

    def __init__(self):
        self._hooks: Dict[UUID, HabitHook] = {}
        self._executions: Dict[UUID, HookExecution] = {}
        self._trigger_hooks: Dict[HookTrigger, List[UUID]] = {t: [] for t in HookTrigger}
        self._callbacks: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._blocked_triggers: Dict[UUID, str] = {}  # session_id -> block reason

        # Initialize default hooks
        self._init_default_hooks()

    def _init_default_hooks(self) -> None:
        """Initialize default habit hooks."""
        default_hooks = [
            HabitHook(
                id=uuid4(),
                name="Block on Scope Creep",
                description="Block when scope creep antipattern is detected",
                trigger=HookTrigger.SCOPE_CREEP,
                action=HookAction(
                    type=ActionType.BLOCK,
                    severity=SeverityLevel.ERROR,
                    message="Scope creep detected! Stay focused on the original task."
                ),
                priority=90
            ),
            HabitHook(
                id=uuid4(),
                name="TDD Reminder",
                description="Remind to write tests first",
                trigger=HookTrigger.TDD_VIOLATION,
                action=HookAction(
                    type=ActionType.NOTIFICATION,
                    severity=SeverityLevel.WARNING,
                    message="Remember: Write the test first, then the implementation!"
                ),
                priority=80
            ),
            HabitHook(
                id=uuid4(),
                name="Context Limit Warning",
                description="Warn when approaching context limits",
                trigger=HookTrigger.CONTEXT_LIMIT_APPROACHING,
                action=HookAction(
                    type=ActionType.NOTIFICATION,
                    severity=SeverityLevel.WARNING,
                    message="Context limit approaching. Consider summarizing or creating a checkpoint."
                ),
                conditions=[
                    HookCondition(field="usage_percent", operator="gte", value=80)
                ],
                priority=70
            ),
            HabitHook(
                id=uuid4(),
                name="Security Issue Alert",
                description="Alert on security issues",
                trigger=HookTrigger.SECURITY_ISSUE,
                action=HookAction(
                    type=ActionType.BLOCK,
                    severity=SeverityLevel.CRITICAL,
                    message="Security issue detected! Review and fix before proceeding."
                ),
                priority=100
            ),
            HabitHook(
                id=uuid4(),
                name="Log Antipattern",
                description="Log detected antipatterns",
                trigger=HookTrigger.ANTIPATTERN_DETECTED,
                action=HookAction(
                    type=ActionType.LOG,
                    severity=SeverityLevel.INFO,
                    message="Antipattern detected: {pattern_type}"
                ),
                priority=30
            ),
            HabitHook(
                id=uuid4(),
                name="Test Failure Handler",
                description="Handle test failures",
                trigger=HookTrigger.TEST_FAILURE,
                action=HookAction(
                    type=ActionType.NOTIFICATION,
                    severity=SeverityLevel.ERROR,
                    message="Tests failed! Fix before continuing. Failing: {failed_count}"
                ),
                priority=85
            ),
            HabitHook(
                id=uuid4(),
                name="Large Change Warning",
                description="Warn on large changes",
                trigger=HookTrigger.LARGE_CHANGE,
                action=HookAction(
                    type=ActionType.NOTIFICATION,
                    severity=SeverityLevel.WARNING,
                    message="Large change detected ({lines_changed} lines). Consider breaking into smaller commits."
                ),
                conditions=[
                    HookCondition(field="lines_changed", operator="gt", value=500)
                ],
                priority=50
            ),
        ]

        for hook in default_hooks:
            self._hooks[hook.id] = hook
            self._trigger_hooks[hook.trigger].append(hook.id)

        logger.info(f"Initialized {len(default_hooks)} default habit hooks")

    def register_hook(
        self,
        name: str,
        trigger: HookTrigger,
        action: HookAction,
        description: str = "",
        conditions: Optional[List[HookCondition]] = None,
        priority: int = 50,
        cooldown_seconds: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HabitHook:
        """
        Register a new habit hook.

        Args:
            name: Hook name
            trigger: Event that triggers this hook
            action: Action to perform
            description: Description of what the hook does
            conditions: Optional conditions for execution
            priority: Execution priority (higher = earlier)
            cooldown_seconds: Minimum time between executions
            metadata: Additional metadata

        Returns:
            Created HabitHook
        """
        hook = HabitHook(
            id=uuid4(),
            name=name,
            description=description,
            trigger=trigger,
            action=action,
            conditions=conditions or [],
            priority=priority,
            cooldown_seconds=cooldown_seconds,
            metadata=metadata or {}
        )

        self._hooks[hook.id] = hook
        self._trigger_hooks[trigger].append(hook.id)

        logger.info(f"Registered hook '{name}' for trigger {trigger.value}")

        return hook

    def register_callback(self, name: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a callback that hooks can invoke."""
        self._callbacks[name] = callback
        logger.info(f"Registered callback '{name}'")

    def check_triggers(
        self,
        event_type: HookTrigger,
        event_data: Dict[str, Any],
        source: str = "unknown",
        session_id: Optional[UUID] = None
    ) -> List[HabitHook]:
        """
        Check which hooks would be triggered by an event.

        Args:
            event_type: Type of event
            event_data: Event data
            source: Source of the event
            session_id: Optional session ID

        Returns:
            List of hooks that would trigger
        """
        event = HookEvent(
            id=uuid4(),
            trigger=event_type,
            data=event_data,
            source=source,
            timestamp=datetime.utcnow(),
            session_id=session_id
        )

        matching_hooks = []
        hook_ids = self._trigger_hooks.get(event_type, [])

        for hook_id in hook_ids:
            hook = self._hooks.get(hook_id)
            if not hook or not hook.enabled:
                continue

            # Check cooldown
            if hook.cooldown_seconds > 0 and hook.last_executed:
                elapsed = (datetime.utcnow() - hook.last_executed).total_seconds()
                if elapsed < hook.cooldown_seconds:
                    continue

            # Check conditions
            if self._evaluate_conditions(hook.conditions, event_data):
                matching_hooks.append(hook)

        # Sort by priority (descending)
        matching_hooks.sort(key=lambda h: h.priority, reverse=True)

        return matching_hooks

    def execute_hooks(
        self,
        event_type: HookTrigger,
        event_data: Dict[str, Any],
        source: str = "unknown",
        session_id: Optional[UUID] = None,
        dry_run: bool = False
    ) -> List[HookExecution]:
        """
        Execute all matching hooks for an event.

        Args:
            event_type: Type of event
            event_data: Event data
            source: Source of the event
            session_id: Optional session ID
            dry_run: If True, don't actually execute, just simulate

        Returns:
            List of HookExecution records
        """
        matching_hooks = self.check_triggers(event_type, event_data, source, session_id)
        executions = []

        for hook in matching_hooks:
            execution = self._execute_hook(hook, event_data, dry_run)
            executions.append(execution)

            # If this hook blocks, stop processing further hooks
            if execution.blocked:
                if session_id:
                    self._blocked_triggers[session_id] = execution.result or "Blocked by hook"
                break

        return executions

    def execute_hook(
        self,
        hook_id: UUID,
        trigger_data: Dict[str, Any],
        dry_run: bool = False
    ) -> HookExecution:
        """
        Execute a specific hook manually.

        Args:
            hook_id: ID of hook to execute
            trigger_data: Data to pass to the hook
            dry_run: If True, don't actually execute

        Returns:
            HookExecution record
        """
        hook = self._hooks.get(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        return self._execute_hook(hook, trigger_data, dry_run)

    def _execute_hook(
        self,
        hook: HabitHook,
        trigger_data: Dict[str, Any],
        dry_run: bool = False
    ) -> HookExecution:
        """Execute a single hook."""
        execution = HookExecution(
            id=uuid4(),
            hook_id=hook.id,
            hook_name=hook.name,
            trigger=hook.trigger,
            trigger_data=trigger_data,
            action_type=hook.action.type,
            status=HookStatus.PENDING,
            started_at=datetime.utcnow()
        )

        if dry_run:
            execution.status = HookStatus.SKIPPED
            execution.result = "Dry run - not executed"
            execution.completed_at = datetime.utcnow()
            return execution

        execution.status = HookStatus.RUNNING

        try:
            result = self._perform_action(hook.action, trigger_data)
            execution.status = HookStatus.SUCCESS
            execution.result = result

            if hook.action.type == ActionType.BLOCK:
                execution.blocked = True

        except Exception as e:
            execution.status = HookStatus.FAILED
            execution.error = str(e)
            logger.error(f"Hook '{hook.name}' execution failed: {e}")

        execution.completed_at = datetime.utcnow()

        # Update hook statistics
        hook.execution_count += 1
        hook.last_executed = execution.completed_at

        self._executions[execution.id] = execution

        logger.info(f"Executed hook '{hook.name}': {execution.status.value}")

        return execution

    def _perform_action(self, action: HookAction, data: Dict[str, Any]) -> str:
        """Perform the hook action."""
        message = self._format_message(action.message or "", data)

        if action.type == ActionType.LOG:
            log_level = {
                SeverityLevel.INFO: logging.INFO,
                SeverityLevel.WARNING: logging.WARNING,
                SeverityLevel.ERROR: logging.ERROR,
                SeverityLevel.CRITICAL: logging.CRITICAL,
            }.get(action.severity, logging.INFO)
            logger.log(log_level, f"[HabitHook] {message}")
            return f"Logged: {message}"

        elif action.type == ActionType.NOTIFICATION:
            # In production, this would send to notification system
            logger.info(f"[Notification] {action.severity.value.upper()}: {message}")
            return f"Notified: {message}"

        elif action.type == ActionType.BLOCK:
            logger.warning(f"[Block] {message}")
            return f"Blocked: {message}"

        elif action.type == ActionType.SCRIPT:
            if action.command:
                # Safety check
                if not self._is_script_allowed(action.command):
                    raise ValueError(f"Script command not allowed: {action.command}")
                # In production, would execute in sandbox
                logger.info(f"[Script] Would execute: {action.command}")
                return f"Script queued: {action.command}"
            return "No command specified"

        elif action.type == ActionType.CALLBACK:
            if action.callback_name and action.callback_name in self._callbacks:
                callback = self._callbacks[action.callback_name]
                result = callback(data)
                return f"Callback result: {result}"
            return f"Callback not found: {action.callback_name}"

        elif action.type == ActionType.CHAIN:
            if action.chain_hook_id:
                chained_hook = self._hooks.get(action.chain_hook_id)
                if chained_hook:
                    return f"Chained to: {chained_hook.name}"
            return "Chain target not found"

        return "Unknown action type"

    def _format_message(self, template: str, data: Dict[str, Any]) -> str:
        """Format message template with data."""
        try:
            return template.format(**data)
        except KeyError:
            # If data doesn't have all keys, do partial formatting
            result = template
            for key, value in data.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result

    def _is_script_allowed(self, command: str) -> bool:
        """Check if a script command is in the allowlist."""
        return any(command.startswith(prefix) for prefix in self.ALLOWED_SCRIPT_PREFIXES)

    def _evaluate_conditions(
        self,
        conditions: List[HookCondition],
        data: Dict[str, Any]
    ) -> bool:
        """Evaluate all conditions against data."""
        if not conditions:
            return True

        for condition in conditions:
            if not self._evaluate_condition(condition, data):
                return False

        return True

    def _evaluate_condition(self, condition: HookCondition, data: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        # Get value from data using dot notation
        value = self._get_nested_value(data, condition.field)

        if condition.operator == "exists":
            return value is not None

        if value is None:
            return False

        target = condition.value

        # Handle string comparisons
        if isinstance(value, str) and not condition.case_sensitive:
            value = value.lower()
            if isinstance(target, str):
                target = target.lower()

        # Evaluate operator
        if condition.operator == "eq":
            return value == target
        elif condition.operator == "ne":
            return value != target
        elif condition.operator == "gt":
            return value > target
        elif condition.operator == "lt":
            return value < target
        elif condition.operator == "gte":
            return value >= target
        elif condition.operator == "lte":
            return value <= target
        elif condition.operator == "contains":
            return target in str(value)
        elif condition.operator == "matches":
            return bool(re.match(str(target), str(value)))

        return False

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a nested value using dot notation."""
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def enable_hook(self, hook_id: UUID) -> HabitHook:
        """Enable a hook."""
        hook = self._hooks.get(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        hook.enabled = True
        logger.info(f"Enabled hook '{hook.name}'")
        return hook

    def disable_hook(self, hook_id: UUID) -> HabitHook:
        """Disable a hook."""
        hook = self._hooks.get(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        hook.enabled = False
        logger.info(f"Disabled hook '{hook.name}'")
        return hook

    def get_hook(self, hook_id: UUID) -> Optional[HabitHook]:
        """Get a hook by ID."""
        return self._hooks.get(hook_id)

    def get_all_hooks(
        self,
        trigger: Optional[HookTrigger] = None,
        enabled_only: bool = False
    ) -> List[HabitHook]:
        """Get all hooks with optional filtering."""
        hooks = list(self._hooks.values())

        if trigger:
            hooks = [h for h in hooks if h.trigger == trigger]

        if enabled_only:
            hooks = [h for h in hooks if h.enabled]

        return sorted(hooks, key=lambda h: h.priority, reverse=True)

    def get_execution_history(
        self,
        hook_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[HookExecution]:
        """Get hook execution history."""
        executions = list(self._executions.values())

        if hook_id:
            executions = [e for e in executions if e.hook_id == hook_id]

        executions.sort(key=lambda e: e.started_at, reverse=True)

        return executions[:limit]

    def get_hook_stats(self, hook_id: UUID) -> Dict[str, Any]:
        """Get statistics for a specific hook."""
        hook = self._hooks.get(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        executions = [e for e in self._executions.values() if e.hook_id == hook_id]

        success_count = len([e for e in executions if e.status == HookStatus.SUCCESS])
        failed_count = len([e for e in executions if e.status == HookStatus.FAILED])
        blocked_count = len([e for e in executions if e.blocked])

        return {
            "hook_id": str(hook_id),
            "hook_name": hook.name,
            "total_executions": hook.execution_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "blocked_count": blocked_count,
            "success_rate": success_count / len(executions) if executions else 0,
            "last_executed": hook.last_executed.isoformat() if hook.last_executed else None,
            "enabled": hook.enabled
        }

    def is_blocked(self, session_id: UUID) -> Optional[str]:
        """Check if a session is blocked by a hook."""
        return self._blocked_triggers.get(session_id)

    def clear_block(self, session_id: UUID) -> bool:
        """Clear a session block."""
        if session_id in self._blocked_triggers:
            del self._blocked_triggers[session_id]
            return True
        return False

    def delete_hook(self, hook_id: UUID) -> bool:
        """Delete a hook."""
        hook = self._hooks.get(hook_id)
        if not hook:
            return False

        del self._hooks[hook_id]
        self._trigger_hooks[hook.trigger].remove(hook_id)

        logger.info(f"Deleted hook '{hook.name}'")
        return True
