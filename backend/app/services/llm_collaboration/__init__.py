"""
LLM Agent Collaboration Framework - B12 (Fase 24)

Multi-agent collaboration infrastructure for coordinating LLM agents.

Components:
- collaboration_types: Type definitions for agent collaboration
- agent_router: Intelligent task routing to appropriate agents
- context_sharing: Real-time context sharing between agents
- result_aggregator: Combining multi-agent results

Integrates with existing services:
- orchestration/cross_context_memory_service: Persistent memory
- orchestration/taskchain_service: Sequential task execution
- orchestration/active_partner_service: Human-AI collaboration
- llm_council_service: Multi-model consensus
- ghostcrew_service: Security-focused multi-agent

Usage:
    from app.services.llm_collaboration import (
        # Types
        CollaborationPattern,
        AgentCapabilityType,
        CollaborationTask,
        AgentResult,
        AggregationStrategy,

        # Services
        get_agent_router,
        get_context_sharing_service,
        get_result_aggregator,
    )

    # Route a task to appropriate agents
    router = get_agent_router()
    decision = router.route_task(CollaborationTask(
        task_type="security_audit",
        required_capabilities={AgentCapabilityType.SECURITY_AUDIT}
    ))

    # Create collaboration session
    session = router.create_session(task, decision)

    # Share context between agents
    context_service = get_context_sharing_service()
    context_service.set_context(
        session_id=session.session_id,
        key="findings",
        value={"vulnerabilities": [...]},
        owner_agent="ghostcrew"
    )

    # Aggregate results
    aggregator = get_result_aggregator()
    aggregator.add_result(session.session_id, result1)
    aggregator.add_result(session.session_id, result2)
    final_result = aggregator.aggregate(session.session_id)

Version: 1.0.0
Week: 129 (Fase 24)
"""

# Types
from .collaboration_types import (
    # Enums
    CollaborationPattern,
    AgentCapabilityType,
    AgentStatus,
    TaskPriority,
    AggregationStrategy,

    # Dataclasses
    AgentProfile,
    CollaborationTask,
    AgentResult,
    CollaborationSession,
    RoutingDecision,
    AggregatedResult,

    # Predefined patterns
    PREDEFINED_PATTERNS,
)

# Agent Router
from .agent_router import (
    AgentRouter,
    RoutingScore,
    get_agent_router,
)

# Context Sharing
from .context_sharing import (
    ContextSharingService,
    ContextScope,
    ContextPriority,
    ConflictStrategy,
    ContextEntry,
    ContextUpdate,
    get_context_sharing_service,
)

# Result Aggregator
from .result_aggregator import (
    ResultAggregator,
    AggregationConfig,
    get_result_aggregator,
)

__all__ = [
    # Collaboration Types
    "CollaborationPattern",
    "AgentCapabilityType",
    "AgentStatus",
    "TaskPriority",
    "AggregationStrategy",
    "AgentProfile",
    "CollaborationTask",
    "AgentResult",
    "CollaborationSession",
    "RoutingDecision",
    "AggregatedResult",
    "PREDEFINED_PATTERNS",

    # Agent Router
    "AgentRouter",
    "RoutingScore",
    "get_agent_router",

    # Context Sharing
    "ContextSharingService",
    "ContextScope",
    "ContextPriority",
    "ConflictStrategy",
    "ContextEntry",
    "ContextUpdate",
    "get_context_sharing_service",

    # Result Aggregator
    "ResultAggregator",
    "AggregationConfig",
    "get_result_aggregator",
]

__version__ = "1.0.0"
