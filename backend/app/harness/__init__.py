"""
Agent Harness Framework - Pluggable AI Agent Control Layer

This module provides a plug-and-play framework for:
1. Agent Constraints - What agents cannot do
2. Structured Context - 3-layer context management
3. Tool Registry - Permission-based tool access
4. Context Versioning - Audit trail for reproducibility

Usage:
    from app.harness import registry, ModuleType

    # Get constraint manager
    constraints = registry.get(ModuleType.CONSTRAINTS)

    # Check if action is allowed
    result = await constraints.check_action(
        agent_id="felix",
        action_type="file_write",
        action_params={"path": "/tmp/test.txt"}
    )
"""

from app.harness.core.registry import registry, PluginRegistry, ModuleType
from app.harness.core.protocols import (
    ConstraintManagerProtocol,
    ContextManagerProtocol,
    ToolRegistryProtocol,
    ContextVersionTrackerProtocol,
    ConstraintResult,
    ConstraintSeverity,
    ContextLayer,
    ResolvedContext,
    ToolDefinition,
    ToolCategory,
    ToolCallRequest,
    ToolCallResult,
    ContextSnapshot,
    ContextDiff,
)

__all__ = [
    # Registry
    "registry",
    "PluginRegistry",
    "ModuleType",
    # Protocols
    "ConstraintManagerProtocol",
    "ContextManagerProtocol",
    "ToolRegistryProtocol",
    "ContextVersionTrackerProtocol",
    # Data classes
    "ConstraintResult",
    "ConstraintSeverity",
    "ContextLayer",
    "ResolvedContext",
    "ToolDefinition",
    "ToolCategory",
    "ToolCallRequest",
    "ToolCallResult",
    "ContextSnapshot",
    "ContextDiff",
]
