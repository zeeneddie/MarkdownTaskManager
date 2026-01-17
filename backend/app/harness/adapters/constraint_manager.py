"""
MarQed Native Constraint Manager

YAML-driven agent constraint management with:
- Action-based constraints (what agents can/cannot do)
- Output validation (pattern matching, length limits)
- Audit logging for compliance
- Runtime constraint updates
"""

import re
import uuid
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone

import yaml

from app.harness.core.protocols import (
    ConstraintManagerProtocol,
    ConstraintResult,
    ConstraintSeverity,
    BaseAdapter,
)

logger = logging.getLogger(__name__)


# Default constraint configuration
DEFAULT_CONSTRAINTS = {
    "global": {
        "max_output_length": 50000,  # Characters
        "max_file_size": 10485760,   # 10MB
        "forbidden_patterns": [
            r"DROP\s+DATABASE",
            r"rm\s+-rf\s+/",
            r"FORMAT\s+C:",
            r"sudo\s+rm",
        ],
        "forbidden_file_extensions": [
            ".exe", ".dll", ".so", ".dylib", ".sys"
        ],
    },
    "agents": {
        "felix": {
            "allowed_actions": ["file_read", "file_write", "code_generate", "api_internal"],
            "denied_actions": ["file_delete", "code_execute", "database_write"],
            "max_tokens_per_request": 8000,
            "requires_approval": ["api_external"],
        },
        "marcus": {
            "allowed_actions": ["file_read", "file_write", "code_generate", "database_read"],
            "denied_actions": ["file_delete", "code_execute"],
            "max_tokens_per_request": 6000,
            "requires_approval": ["database_write"],
        },
        "quinn": {
            "allowed_actions": ["file_read", "code_generate", "security"],
            "denied_actions": ["file_write", "file_delete", "code_execute", "database_write"],
            "max_tokens_per_request": 4000,
            "requires_approval": [],
        },
        "betty": {
            "allowed_actions": ["file_read", "code_generate", "code_execute"],
            "denied_actions": ["file_delete", "database_write"],
            "max_tokens_per_request": 6000,
            "requires_approval": ["file_write"],
        },
        "eliza": {
            "allowed_actions": ["file_read", "database_read"],
            "denied_actions": ["file_write", "file_delete", "code_execute", "database_write"],
            "max_tokens_per_request": 4000,
            "requires_approval": [],
        },
        "diana": {
            "allowed_actions": ["file_read", "file_write"],
            "denied_actions": ["file_delete", "code_execute", "database_write"],
            "max_tokens_per_request": 6000,
            "requires_approval": [],
        },
        "tessa": {
            "allowed_actions": ["file_read", "file_write", "code_execute", "code_generate"],
            "denied_actions": ["file_delete", "database_write"],
            "max_tokens_per_request": 8000,
            "requires_approval": [],
        },
        "miguel": {
            "allowed_actions": ["file_read", "file_write", "database_read", "database_write", "code_generate"],
            "denied_actions": ["file_delete"],
            "max_tokens_per_request": 10000,
            "requires_approval": ["code_execute"],
        },
        "peter": {
            "allowed_actions": ["file_read", "api_internal"],
            "denied_actions": ["file_write", "file_delete", "code_execute", "database_write"],
            "max_tokens_per_request": 4000,
            "requires_approval": [],
        },
        "paul": {
            "allowed_actions": ["file_read", "database_read", "api_internal"],
            "denied_actions": ["file_write", "file_delete", "code_execute", "database_write"],
            "max_tokens_per_request": 4000,
            "requires_approval": [],
        },
    }
}


class MarQedConstraintManager(BaseAdapter, ConstraintManagerProtocol):
    """
    MarQed native implementation of ConstraintManagerProtocol.

    Features:
    - YAML configuration loading
    - Per-agent action constraints
    - Global forbidden patterns
    - Output validation with regex
    - Audit trail generation

    Usage:
        manager = MarQedConstraintManager(config_path="constraints.yaml")

        result = await manager.check_action(
            agent_id="felix",
            action_type="file_write",
            action_params={"path": "/tmp/test.txt", "content": "hello"}
        )

        if not result.allowed:
            print(f"Blocked: {result.reason}")
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize constraint manager.

        Args:
            config_path: Path to YAML config file
            config_dict: Direct config dict (overrides file)
        """
        super().__init__(**kwargs)

        self._constraints: Dict[str, Any] = {}
        self._runtime_constraints: Dict[str, List[Dict[str, Any]]] = {}  # Runtime additions
        self._audit_log: List[Dict[str, Any]] = []

        # Load configuration
        if config_dict:
            self._constraints = config_dict
        elif config_path:
            self._load_config(config_path)
        else:
            self._constraints = DEFAULT_CONSTRAINTS.copy()

        self._initialized = True
        logger.info(f"MarQedConstraintManager initialized with {len(self._constraints.get('agents', {}))} agent configs")

    def _load_config(self, config_path: str) -> None:
        """Load constraints from YAML file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self._constraints = DEFAULT_CONSTRAINTS.copy()
            return

        try:
            with open(path, 'r') as f:
                self._constraints = yaml.safe_load(f)
            logger.info(f"Loaded constraints from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            self._constraints = DEFAULT_CONSTRAINTS.copy()

    def _get_agent_constraints(self, agent_id: str) -> Dict[str, Any]:
        """Get constraints for specific agent, with fallback to defaults."""
        agents = self._constraints.get("agents", {})

        # Try exact match
        if agent_id in agents:
            return agents[agent_id]

        # Try lowercase
        agent_lower = agent_id.lower()
        if agent_lower in agents:
            return agents[agent_lower]

        # Return empty defaults
        return {
            "allowed_actions": [],
            "denied_actions": [],
            "max_tokens_per_request": 4000,
            "requires_approval": [],
        }

    async def check_action(
        self,
        agent_id: str,
        action_type: str,
        action_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintResult:
        """
        Check if an action is allowed for an agent.

        Checks in order:
        1. Is action explicitly denied?
        2. Is action in allowed list?
        3. Does action require approval?
        4. Global constraints (file size, patterns)
        """
        audit_id = str(uuid.uuid4())[:8]
        matched_rules: List[str] = []

        agent_constraints = self._get_agent_constraints(agent_id)
        global_constraints = self._constraints.get("global", {})

        # Check runtime constraints first
        for constraint in self._runtime_constraints.get(agent_id, []):
            if constraint.get("action_type") == action_type:
                if constraint.get("denied", False):
                    return ConstraintResult(
                        allowed=False,
                        severity=ConstraintSeverity.BLOCK,
                        reason=f"Runtime constraint: {constraint.get('reason', 'denied')}",
                        requires_approval=False,
                        audit_id=audit_id,
                        matched_rules=["runtime_deny"]
                    )

        # Check denied actions
        denied_actions = agent_constraints.get("denied_actions", [])
        if action_type in denied_actions:
            self._log_audit(audit_id, agent_id, action_type, "DENIED", "action_denied")
            return ConstraintResult(
                allowed=False,
                severity=ConstraintSeverity.BLOCK,
                reason=f"Action '{action_type}' is explicitly denied for agent '{agent_id}'",
                requires_approval=False,
                audit_id=audit_id,
                matched_rules=["denied_actions"]
            )

        # Check allowed actions
        allowed_actions = agent_constraints.get("allowed_actions", [])
        if allowed_actions and action_type not in allowed_actions:
            self._log_audit(audit_id, agent_id, action_type, "DENIED", "not_in_allowed")
            return ConstraintResult(
                allowed=False,
                severity=ConstraintSeverity.BLOCK,
                reason=f"Action '{action_type}' is not in allowed list for agent '{agent_id}'",
                requires_approval=False,
                audit_id=audit_id,
                matched_rules=["allowed_actions"]
            )
        matched_rules.append("allowed_actions")

        # Check requires approval
        requires_approval = agent_constraints.get("requires_approval", [])
        if action_type in requires_approval:
            self._log_audit(audit_id, agent_id, action_type, "APPROVAL_REQUIRED", "requires_approval")
            return ConstraintResult(
                allowed=True,
                severity=ConstraintSeverity.APPROVE,
                reason=f"Action '{action_type}' requires human approval",
                requires_approval=True,
                audit_id=audit_id,
                matched_rules=["requires_approval"]
            )

        # Check file-specific constraints
        if action_type == "file_write":
            file_path = action_params.get("path", "")
            content = action_params.get("content", "")

            # Check file extension
            forbidden_extensions = global_constraints.get("forbidden_file_extensions", [])
            for ext in forbidden_extensions:
                if file_path.lower().endswith(ext):
                    self._log_audit(audit_id, agent_id, action_type, "DENIED", "forbidden_extension")
                    return ConstraintResult(
                        allowed=False,
                        severity=ConstraintSeverity.BLOCK,
                        reason=f"File extension '{ext}' is forbidden",
                        requires_approval=False,
                        audit_id=audit_id,
                        matched_rules=["forbidden_file_extensions"]
                    )

            # Check file size
            max_size = global_constraints.get("max_file_size", 10485760)
            if len(content.encode('utf-8')) > max_size:
                self._log_audit(audit_id, agent_id, action_type, "DENIED", "file_too_large")
                return ConstraintResult(
                    allowed=False,
                    severity=ConstraintSeverity.BLOCK,
                    reason=f"File content exceeds maximum size ({max_size} bytes)",
                    requires_approval=False,
                    audit_id=audit_id,
                    matched_rules=["max_file_size"]
                )
            matched_rules.append("file_size_ok")

        # Check forbidden patterns in any content
        content_to_check = str(action_params.get("content", ""))
        forbidden_patterns = global_constraints.get("forbidden_patterns", [])
        for pattern in forbidden_patterns:
            try:
                if re.search(pattern, content_to_check, re.IGNORECASE):
                    self._log_audit(audit_id, agent_id, action_type, "DENIED", f"forbidden_pattern:{pattern}")
                    return ConstraintResult(
                        allowed=False,
                        severity=ConstraintSeverity.BLOCK,
                        reason=f"Content matches forbidden pattern: {pattern}",
                        requires_approval=False,
                        audit_id=audit_id,
                        matched_rules=[f"forbidden_pattern:{pattern}"]
                    )
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
        matched_rules.append("patterns_ok")

        # All checks passed
        self._log_audit(audit_id, agent_id, action_type, "ALLOWED", "all_checks_passed")
        return ConstraintResult(
            allowed=True,
            severity=ConstraintSeverity.AUDIT,
            reason="Action allowed",
            requires_approval=False,
            audit_id=audit_id,
            matched_rules=matched_rules
        )

    async def get_constraints(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all constraints configured for an agent."""
        agent_constraints = self._get_agent_constraints(agent_id)
        global_constraints = self._constraints.get("global", {})
        runtime = self._runtime_constraints.get(agent_id, [])

        return [
            {"type": "agent", "config": agent_constraints},
            {"type": "global", "config": global_constraints},
            {"type": "runtime", "constraints": runtime},
        ]

    async def add_constraint(
        self,
        agent_id: str,
        constraint: Dict[str, Any]
    ) -> bool:
        """Add a runtime constraint for an agent."""
        if agent_id not in self._runtime_constraints:
            self._runtime_constraints[agent_id] = []

        constraint["id"] = str(uuid.uuid4())[:8]
        constraint["added_at"] = datetime.now(timezone.utc).isoformat()
        self._runtime_constraints[agent_id].append(constraint)

        logger.info(f"Added runtime constraint for {agent_id}: {constraint['id']}")
        return True

    async def remove_constraint(
        self,
        agent_id: str,
        constraint_id: str
    ) -> bool:
        """Remove a runtime constraint by ID."""
        if agent_id not in self._runtime_constraints:
            return False

        original_len = len(self._runtime_constraints[agent_id])
        self._runtime_constraints[agent_id] = [
            c for c in self._runtime_constraints[agent_id]
            if c.get("id") != constraint_id
        ]

        removed = len(self._runtime_constraints[agent_id]) < original_len
        if removed:
            logger.info(f"Removed runtime constraint {constraint_id} for {agent_id}")
        return removed

    async def validate_output(
        self,
        agent_id: str,
        output: str,
        output_type: str
    ) -> ConstraintResult:
        """
        Validate agent output against output constraints.

        Checks:
        - Length limits
        - Forbidden patterns
        - Output-type specific rules
        """
        audit_id = str(uuid.uuid4())[:8]
        matched_rules: List[str] = []
        global_constraints = self._constraints.get("global", {})

        # Check output length
        max_length = global_constraints.get("max_output_length", 50000)
        if len(output) > max_length:
            self._log_audit(audit_id, agent_id, f"output_{output_type}", "DENIED", "output_too_long")
            return ConstraintResult(
                allowed=False,
                severity=ConstraintSeverity.BLOCK,
                reason=f"Output exceeds maximum length ({max_length} characters)",
                requires_approval=False,
                audit_id=audit_id,
                matched_rules=["max_output_length"]
            )
        matched_rules.append("length_ok")

        # Check forbidden patterns
        forbidden_patterns = global_constraints.get("forbidden_patterns", [])
        for pattern in forbidden_patterns:
            try:
                if re.search(pattern, output, re.IGNORECASE):
                    self._log_audit(audit_id, agent_id, f"output_{output_type}", "DENIED", f"forbidden_pattern:{pattern}")
                    return ConstraintResult(
                        allowed=False,
                        severity=ConstraintSeverity.BLOCK,
                        reason=f"Output contains forbidden pattern: {pattern}",
                        requires_approval=False,
                        audit_id=audit_id,
                        matched_rules=[f"forbidden_pattern:{pattern}"]
                    )
            except re.error:
                pass
        matched_rules.append("patterns_ok")

        # Output-type specific validation
        if output_type == "code":
            # Additional code-specific checks could go here
            matched_rules.append("code_format_ok")
        elif output_type == "sql":
            # Check for destructive SQL
            destructive_patterns = [r"DROP\s+", r"TRUNCATE\s+", r"DELETE\s+FROM.*WHERE\s*$"]
            for pattern in destructive_patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    self._log_audit(audit_id, agent_id, f"output_{output_type}", "WARN", f"destructive_sql:{pattern}")
                    return ConstraintResult(
                        allowed=True,
                        severity=ConstraintSeverity.WARN,
                        reason=f"SQL output contains potentially destructive pattern",
                        requires_approval=False,
                        audit_id=audit_id,
                        matched_rules=["destructive_sql_warning"]
                    )
            matched_rules.append("sql_safe")

        self._log_audit(audit_id, agent_id, f"output_{output_type}", "ALLOWED", "output_valid")
        return ConstraintResult(
            allowed=True,
            severity=ConstraintSeverity.AUDIT,
            reason="Output validation passed",
            requires_approval=False,
            audit_id=audit_id,
            matched_rules=matched_rules
        )

    def _log_audit(
        self,
        audit_id: str,
        agent_id: str,
        action: str,
        result: str,
        reason: str
    ) -> None:
        """Log audit entry for compliance."""
        entry = {
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "action": action,
            "result": result,
            "reason": reason,
        }
        self._audit_log.append(entry)

        # Keep only last 10000 entries in memory
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]

    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit log entries, optionally filtered by agent."""
        if agent_id:
            entries = [e for e in self._audit_log if e["agent_id"] == agent_id]
        else:
            entries = self._audit_log

        return entries[-limit:]

    def health_check(self) -> bool:
        """Check if constraint manager is operational."""
        return self._initialized and bool(self._constraints)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about constraint usage."""
        return {
            "agents_configured": len(self._constraints.get("agents", {})),
            "global_patterns": len(self._constraints.get("global", {}).get("forbidden_patterns", [])),
            "runtime_constraints": sum(len(c) for c in self._runtime_constraints.values()),
            "audit_log_size": len(self._audit_log),
            "initialized": self._initialized,
        }
