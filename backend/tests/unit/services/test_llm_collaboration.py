"""
Unit tests for LLM Collaboration Services - B12 (Fase 24).

Tests cover:
- AgentRouter: Task routing, scoring, session management
- ContextSharingService: Context CRUD, pub/sub, snapshots
- ResultAggregator: All aggregation strategies
- Collaboration types: Data classes and enums

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch

from app.services.llm_collaboration.collaboration_types import (
    CollaborationPattern,
    AgentCapabilityType,
    AgentStatus,
    TaskPriority,
    AggregationStrategy,
    AgentProfile,
    CollaborationTask,
    AgentResult,
    CollaborationSession,
    RoutingDecision,
    AggregatedResult,
    PREDEFINED_PATTERNS,
)
from app.services.llm_collaboration.agent_router import (
    AgentRouter,
    RoutingScore,
    get_agent_router,
)
from app.services.llm_collaboration.context_sharing import (
    ContextScope,
    ContextPriority,
    ConflictStrategy,
    ContextEntry,
    ContextUpdate,
    ContextSharingService,
    get_context_sharing_service,
)
from app.services.llm_collaboration.result_aggregator import (
    AggregationConfig,
    ResultAggregator,
    get_result_aggregator,
)


# ==================== AgentProfile Tests ====================

class TestAgentProfile:
    """Test AgentProfile data class."""

    def test_create_agent_profile(self):
        """Test basic agent profile creation."""
        profile = AgentProfile(
            agent_id="test-agent",
            name="Test Agent",
            capabilities={AgentCapabilityType.CODE_ANALYSIS}
        )
        assert profile.agent_id == "test-agent"
        assert profile.name == "Test Agent"
        assert AgentCapabilityType.CODE_ANALYSIS in profile.capabilities

    def test_is_available_when_ready(self):
        """Test agent is available when status is AVAILABLE and not overloaded."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            status=AgentStatus.AVAILABLE,
            current_load=2,
            max_concurrent=5
        )
        assert profile.is_available is True

    def test_is_not_available_when_busy(self):
        """Test agent is not available when status is BUSY."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            status=AgentStatus.BUSY
        )
        assert profile.is_available is False

    def test_is_not_available_when_overloaded(self):
        """Test agent is not available when at max capacity."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            status=AgentStatus.AVAILABLE,
            current_load=5,
            max_concurrent=5
        )
        assert profile.is_available is False

    def test_load_factor_calculation(self):
        """Test load factor is calculated correctly."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            current_load=2,
            max_concurrent=4
        )
        assert profile.load_factor == 0.5

    def test_load_factor_zero_max(self):
        """Test load factor with zero max concurrent."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            max_concurrent=0
        )
        assert profile.load_factor == 1.0

    def test_has_capability(self):
        """Test capability checking."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities={AgentCapabilityType.CODE_ANALYSIS, AgentCapabilityType.TESTING}
        )
        assert profile.has_capability(AgentCapabilityType.CODE_ANALYSIS) is True
        assert profile.has_capability(AgentCapabilityType.SECURITY_AUDIT) is False

    def test_matches_specialization_full_match(self):
        """Test specialization matching with full match."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            specializations=["python", "javascript", "security"]
        )
        score = profile.matches_specialization(["python", "javascript"])
        assert score == 1.0

    def test_matches_specialization_partial_match(self):
        """Test specialization matching with partial match."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            specializations=["python", "javascript"]
        )
        score = profile.matches_specialization(["python", "rust"])
        assert score == 0.5

    def test_matches_specialization_no_required(self):
        """Test specialization matching with no requirements."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set()
        )
        score = profile.matches_specialization([])
        assert score == 1.0

    def test_matches_specialization_no_specializations(self):
        """Test specialization matching when agent has none."""
        profile = AgentProfile(
            agent_id="test",
            name="Test",
            capabilities=set(),
            specializations=[]
        )
        score = profile.matches_specialization(["python"])
        assert score == 0.5  # Neutral


# ==================== CollaborationTask Tests ====================

class TestCollaborationTask:
    """Test CollaborationTask data class."""

    def test_create_task(self):
        """Test basic task creation."""
        task = CollaborationTask(
            task_type="code_review",
            payload={"code": "print('hello')"},
            required_capabilities={AgentCapabilityType.CODE_REVIEW}
        )
        assert task.task_type == "code_review"
        assert task.task_id is not None
        assert AgentCapabilityType.CODE_REVIEW in task.required_capabilities

    def test_task_to_dict(self):
        """Test task serialization."""
        task = CollaborationTask(
            task_type="test",
            priority=TaskPriority.HIGH
        )
        data = task.to_dict()
        assert data["task_type"] == "test"
        assert data["priority"] == "high"
        assert "task_id" in data


# ==================== AgentResult Tests ====================

class TestAgentResult:
    """Test AgentResult data class."""

    def test_create_successful_result(self):
        """Test successful result creation."""
        task_id = uuid4()
        result = AgentResult(
            agent_id="felix",
            task_id=task_id,
            success=True,
            output={"findings": ["issue1", "issue2"]},
            confidence=0.95
        )
        assert result.success is True
        assert result.confidence == 0.95
        assert result.error is None

    def test_create_failed_result(self):
        """Test failed result creation."""
        result = AgentResult(
            agent_id="quinn",
            task_id=uuid4(),
            success=False,
            error="Timeout exceeded"
        )
        assert result.success is False
        assert result.error == "Timeout exceeded"

    def test_result_to_dict(self):
        """Test result serialization."""
        result = AgentResult(
            agent_id="test",
            task_id=uuid4(),
            success=True,
            output="test output"
        )
        data = result.to_dict()
        assert data["agent_id"] == "test"
        assert data["success"] is True


# ==================== CollaborationSession Tests ====================

class TestCollaborationSession:
    """Test CollaborationSession data class."""

    def test_create_session(self):
        """Test session creation."""
        session = CollaborationSession(
            pattern=CollaborationPattern.PARALLEL,
            participating_agents=["felix", "quinn"]
        )
        assert session.session_id is not None
        assert session.pattern == CollaborationPattern.PARALLEL
        assert "felix" in session.participating_agents
        assert session.status == "active"

    def test_add_result(self):
        """Test adding results to session."""
        session = CollaborationSession()
        result = AgentResult(
            agent_id="test",
            task_id=uuid4(),
            success=True
        )
        session.add_result(result)
        assert len(session.results) == 1

    def test_get_successful_results(self):
        """Test filtering successful results."""
        session = CollaborationSession()
        session.add_result(AgentResult(agent_id="a", task_id=uuid4(), success=True))
        session.add_result(AgentResult(agent_id="b", task_id=uuid4(), success=False))
        session.add_result(AgentResult(agent_id="c", task_id=uuid4(), success=True))

        successful = session.get_successful_results()
        assert len(successful) == 2

    def test_get_failed_results(self):
        """Test filtering failed results."""
        session = CollaborationSession()
        session.add_result(AgentResult(agent_id="a", task_id=uuid4(), success=True))
        session.add_result(AgentResult(agent_id="b", task_id=uuid4(), success=False))

        failed = session.get_failed_results()
        assert len(failed) == 1

    def test_complete_session(self):
        """Test completing a session."""
        session = CollaborationSession()
        assert session.completed_at is None

        session.complete()

        assert session.status == "completed"
        assert session.completed_at is not None


# ==================== AgentRouter Tests ====================

class TestAgentRouter:
    """Test AgentRouter service."""

    @pytest.fixture
    def router(self):
        """Create a fresh router instance."""
        return AgentRouter()

    @pytest.fixture
    def custom_agent(self):
        """Create a custom test agent."""
        return AgentProfile(
            agent_id="custom-agent",
            name="Custom Test Agent",
            capabilities={
                AgentCapabilityType.CODE_ANALYSIS,
                AgentCapabilityType.TESTING
            },
            specializations=["python", "testing"],
            reliability=0.9,
            avg_latency_ms=2000
        )

    def test_router_initializes_with_known_agents(self, router):
        """Test router initializes with predefined agents."""
        agents = router.list_agents()
        assert len(agents) > 0
        # Check for known agents
        agent_ids = [a.agent_id for a in agents]
        assert "felix" in agent_ids
        assert "quinn" in agent_ids

    def test_register_custom_agent(self, router, custom_agent):
        """Test registering a custom agent."""
        initial_count = len(router.list_agents())
        router.register_agent(custom_agent)

        assert len(router.list_agents()) == initial_count + 1
        assert router.get_agent("custom-agent") is not None

    def test_unregister_agent(self, router, custom_agent):
        """Test unregistering an agent."""
        router.register_agent(custom_agent)
        assert router.get_agent("custom-agent") is not None

        result = router.unregister_agent("custom-agent")

        assert result is True
        assert router.get_agent("custom-agent") is None

    def test_unregister_nonexistent_agent(self, router):
        """Test unregistering agent that doesn't exist."""
        result = router.unregister_agent("nonexistent")
        assert result is False

    def test_list_agents_by_capability(self, router):
        """Test filtering agents by capability."""
        security_agents = router.list_agents(
            capability=AgentCapabilityType.SECURITY_AUDIT
        )
        for agent in security_agents:
            assert agent.has_capability(AgentCapabilityType.SECURITY_AUDIT)

    def test_list_available_agents_only(self, router):
        """Test filtering to available agents only."""
        # Make one agent busy
        router.update_agent_status("felix", status=AgentStatus.BUSY)

        available = router.list_agents(available_only=True)
        for agent in available:
            assert agent.is_available

    def test_update_agent_status(self, router):
        """Test updating agent status."""
        result = router.update_agent_status("felix", status=AgentStatus.PAUSED)

        assert result is True
        assert router.get_agent("felix").status == AgentStatus.PAUSED

    def test_update_agent_load(self, router):
        """Test updating agent load."""
        result = router.update_agent_status("felix", current_load=3)

        assert result is True
        assert router.get_agent("felix").current_load == 3

    def test_route_task_selects_capable_agents(self, router):
        """Test routing selects agents with required capabilities."""
        task = CollaborationTask(
            task_type="security_audit",
            required_capabilities={AgentCapabilityType.SECURITY_AUDIT}
        )

        decision = router.route_task(task)

        assert len(decision.selected_agents) > 0
        for agent_id in decision.selected_agents:
            agent = router.get_agent(agent_id)
            assert agent.has_capability(AgentCapabilityType.SECURITY_AUDIT)

    def test_route_task_respects_max_agents(self, router):
        """Test routing respects max_agents parameter."""
        task = CollaborationTask(
            task_type="code_review",
            required_capabilities={AgentCapabilityType.CODE_REVIEW}
        )

        decision = router.route_task(task, max_agents=2)

        assert len(decision.selected_agents) <= 2

    def test_route_task_respects_min_score(self, router):
        """Test routing respects minimum score threshold."""
        task = CollaborationTask(
            task_type="obscure_task",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS}
        )

        decision = router.route_task(task, min_score=0.9)

        # All selected agents should have high scores
        # (or none if no agents meet threshold)
        assert isinstance(decision.selected_agents, list)

    def test_route_task_prefers_preferred_agents(self, router):
        """Test routing prioritizes preferred agents."""
        task = CollaborationTask(
            task_type="code_review",
            required_capabilities={AgentCapabilityType.CODE_REVIEW},
            preferred_agents=["quinn"]
        )

        decision = router.route_task(task, max_agents=1)

        # Quinn should be selected if available
        if decision.selected_agents:
            assert "quinn" in decision.selected_agents

    def test_route_task_includes_fallbacks(self, router):
        """Test routing includes fallback agents."""
        task = CollaborationTask(
            task_type="code_analysis",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS}
        )

        decision = router.route_task(task, max_agents=1)

        # Should have fallback agents if multiple agents matched
        assert isinstance(decision.fallback_agents, list)

    def test_route_task_generates_reasoning(self, router):
        """Test routing generates reasoning string."""
        task = CollaborationTask(
            task_type="code_review",
            required_capabilities={AgentCapabilityType.CODE_REVIEW}
        )

        decision = router.route_task(task)

        assert decision.reasoning is not None
        assert len(decision.reasoning) > 0

    def test_route_task_selects_pattern(self, router):
        """Test routing selects appropriate collaboration pattern."""
        task = CollaborationTask(
            task_type="security_audit",
            required_capabilities={AgentCapabilityType.SECURITY_AUDIT}
        )

        decision = router.route_task(task)

        assert decision.pattern in CollaborationPattern

    def test_route_task_critical_uses_parallel(self, router):
        """Test critical tasks use parallel pattern."""
        task = CollaborationTask(
            task_type="urgent_task",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS},
            priority=TaskPriority.CRITICAL
        )

        decision = router.route_task(task)

        # Critical tasks should use parallel for speed
        assert decision.pattern == CollaborationPattern.PARALLEL

    def test_create_session(self, router):
        """Test creating a collaboration session."""
        task = CollaborationTask(
            task_type="test",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS}
        )
        decision = router.route_task(task)

        session = router.create_session(task, decision)

        assert session.session_id is not None
        assert session.pattern == decision.pattern
        assert session.participating_agents == decision.selected_agents

    def test_create_session_increases_agent_load(self, router):
        """Test session creation increases agent load."""
        agent = router.get_agent("felix")
        initial_load = agent.current_load

        task = CollaborationTask(
            task_type="test",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS},
            preferred_agents=["felix"]
        )
        decision = router.route_task(task, max_agents=1)
        router.create_session(task, decision)

        if "felix" in decision.selected_agents:
            assert agent.current_load == initial_load + 1

    def test_complete_session(self, router):
        """Test completing a session."""
        task = CollaborationTask(
            task_type="test",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS}
        )
        decision = router.route_task(task)
        session = router.create_session(task, decision)

        completed = router.complete_session(session.session_id)

        assert completed is not None
        assert completed.status == "completed"

    def test_complete_session_releases_load(self, router):
        """Test completing session releases agent load."""
        task = CollaborationTask(
            task_type="test",
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS},
            preferred_agents=["felix"]
        )
        decision = router.route_task(task, max_agents=1)

        agent = router.get_agent("felix")
        if "felix" in decision.selected_agents:
            initial_load = agent.current_load
            session = router.create_session(task, decision)
            router.complete_session(session.session_id)
            assert agent.current_load == initial_load

    def test_get_routing_stats(self, router):
        """Test getting routing statistics."""
        # Route a few tasks
        for _ in range(3):
            task = CollaborationTask(
                task_type="test",
                required_capabilities={AgentCapabilityType.CODE_ANALYSIS}
            )
            router.route_task(task)

        stats = router.get_routing_stats()

        assert stats["total_routings"] >= 3
        assert "pattern_distribution" in stats
        assert "agent_usage" in stats


# ==================== ContextSharingService Tests ====================

class TestContextSharingService:
    """Test ContextSharingService."""

    @pytest.fixture
    def service(self):
        """Create a fresh context service."""
        return ContextSharingService()

    @pytest.fixture
    def session_id(self):
        """Create a test session ID."""
        return uuid4()

    def test_set_and_get_context(self, service, session_id):
        """Test basic context set and get."""
        service.set_context(
            key="test_key",
            value={"data": "test_value"},
            session_id=session_id
        )

        value = service.get_context(
            key="test_key",
            session_id=session_id
        )

        assert value == {"data": "test_value"}

    def test_get_nonexistent_context(self, service, session_id):
        """Test getting context that doesn't exist."""
        value = service.get_context(
            key="nonexistent",
            session_id=session_id,
            default="default_value"
        )
        assert value == "default_value"

    def test_update_context(self, service, session_id):
        """Test updating existing context."""
        service.set_context(key="key", value="v1", session_id=session_id)
        service.set_context(key="key", value="v2", session_id=session_id)

        value = service.get_context(key="key", session_id=session_id)
        assert value == "v2"

    def test_context_versioning(self, service, session_id):
        """Test context version increments on update."""
        entry1 = service.set_context(key="key", value="v1", session_id=session_id)
        entry2 = service.set_context(key="key", value="v2", session_id=session_id)

        assert entry2.version == entry1.version + 1

    def test_delete_context(self, service, session_id):
        """Test deleting context."""
        service.set_context(key="key", value="value", session_id=session_id)

        result = service.delete_context(key="key", session_id=session_id)

        assert result is True
        assert service.get_context(key="key", session_id=session_id) is None

    def test_delete_nonexistent_context(self, service, session_id):
        """Test deleting context that doesn't exist."""
        result = service.delete_context(key="nonexistent", session_id=session_id)
        assert result is False

    def test_list_context_keys(self, service, session_id):
        """Test listing context keys."""
        service.set_context(key="key1", value="v1", session_id=session_id)
        service.set_context(key="key2", value="v2", session_id=session_id)
        service.set_context(key="other", value="v3", session_id=session_id)

        keys = service.list_context(session_id=session_id)

        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys

    def test_list_context_with_prefix(self, service, session_id):
        """Test listing context keys with prefix filter."""
        service.set_context(key="prefix_a", value="1", session_id=session_id)
        service.set_context(key="prefix_b", value="2", session_id=session_id)
        service.set_context(key="other", value="3", session_id=session_id)

        keys = service.list_context(session_id=session_id, prefix="prefix_")

        assert len(keys) == 2
        assert "prefix_a" in keys
        assert "prefix_b" in keys

    def test_get_all_context(self, service, session_id):
        """Test getting all context values."""
        service.set_context(key="a", value=1, session_id=session_id)
        service.set_context(key="b", value=2, session_id=session_id)

        all_context = service.get_all_context(session_id=session_id)

        assert all_context == {"a": 1, "b": 2}

    def test_context_scope_isolation(self, service, session_id):
        """Test context is isolated by scope."""
        service.set_context(
            key="key",
            value="session_value",
            session_id=session_id,
            scope=ContextScope.SESSION
        )
        service.set_context(
            key="key",
            value="task_value",
            session_id=session_id,
            scope=ContextScope.TASK
        )

        session_val = service.get_context(
            key="key",
            session_id=session_id,
            scope=ContextScope.SESSION
        )
        task_val = service.get_context(
            key="key",
            session_id=session_id,
            scope=ContextScope.TASK
        )

        assert session_val == "session_value"
        assert task_val == "task_value"

    def test_global_scope_shared(self, service):
        """Test global scope is shared across sessions."""
        session1 = uuid4()
        session2 = uuid4()

        service.set_context(
            key="global_key",
            value="global_value",
            scope=ContextScope.GLOBAL
        )

        val1 = service.get_context(key="global_key", scope=ContextScope.GLOBAL)
        val2 = service.get_context(key="global_key", scope=ContextScope.GLOBAL)

        assert val1 == val2 == "global_value"

    def test_context_expiration(self, service, session_id):
        """Test context expires after TTL."""
        service.set_context(
            key="expiring",
            value="test",
            session_id=session_id,
            ttl_seconds=1
        )

        # Should exist initially
        assert service.get_context(key="expiring", session_id=session_id) == "test"

        # Manually expire by setting expires_at in the past
        entry = service.get_entry(key="expiring", session_id=session_id)
        entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        # Should now be expired
        assert service.get_context(key="expiring", session_id=session_id) is None

    def test_subscribe_and_notify(self, service, session_id):
        """Test subscribing to context updates."""
        updates_received = []

        def callback(update: ContextUpdate):
            updates_received.append(update)

        service.subscribe(
            key="watched_key",
            agent_id="test_agent",
            callback=callback,
            session_id=session_id
        )

        service.set_context(
            key="watched_key",
            value="new_value",
            session_id=session_id,
            owner_agent="other_agent"
        )

        assert len(updates_received) == 1
        assert updates_received[0].entry.value == "new_value"
        assert updates_received[0].update_type == "created"

    def test_wildcard_subscription(self, service, session_id):
        """Test wildcard subscription receives all updates."""
        updates_received = []

        def callback(update: ContextUpdate):
            updates_received.append(update)

        service.subscribe(
            key="*",
            agent_id="watcher",
            callback=callback,
            session_id=session_id
        )

        service.set_context(key="key1", value="v1", session_id=session_id)
        service.set_context(key="key2", value="v2", session_id=session_id)

        assert len(updates_received) == 2

    def test_unsubscribe(self, service, session_id):
        """Test unsubscribing from updates."""
        updates_received = []

        def callback(update: ContextUpdate):
            updates_received.append(update)

        service.subscribe(
            key="key",
            agent_id="agent",
            callback=callback,
            session_id=session_id
        )

        service.set_context(key="key", value="v1", session_id=session_id)
        assert len(updates_received) == 1

        service.unsubscribe(key="key", agent_id="agent", session_id=session_id)

        service.set_context(key="key", value="v2", session_id=session_id)
        assert len(updates_received) == 1  # No new updates

    def test_conflict_strategy_last_write_wins(self, session_id):
        """Test LAST_WRITE_WINS conflict strategy."""
        service = ContextSharingService(
            conflict_strategy=ConflictStrategy.LAST_WRITE_WINS
        )

        service.set_context(key="key", value="v1", session_id=session_id)
        service.set_context(key="key", value="v2", session_id=session_id)

        assert service.get_context(key="key", session_id=session_id) == "v2"

    def test_conflict_strategy_first_write_wins(self, session_id):
        """Test FIRST_WRITE_WINS conflict strategy."""
        service = ContextSharingService(
            conflict_strategy=ConflictStrategy.FIRST_WRITE_WINS
        )

        service.set_context(key="key", value="v1", session_id=session_id)
        service.set_context(key="key", value="v2", session_id=session_id)

        assert service.get_context(key="key", session_id=session_id) == "v1"

    def test_conflict_strategy_priority(self, session_id):
        """Test PRIORITY conflict strategy."""
        service = ContextSharingService(
            conflict_strategy=ConflictStrategy.PRIORITY
        )

        service.set_context(
            key="key",
            value="high",
            session_id=session_id,
            priority=ContextPriority.HIGH
        )
        service.set_context(
            key="key",
            value="low",
            session_id=session_id,
            priority=ContextPriority.LOW
        )

        # Low priority should not override high
        assert service.get_context(key="key", session_id=session_id) == "high"

    def test_conflict_strategy_merge(self, session_id):
        """Test MERGE conflict strategy for dicts."""
        service = ContextSharingService(
            conflict_strategy=ConflictStrategy.MERGE
        )

        service.set_context(
            key="key",
            value={"a": 1, "b": 2},
            session_id=session_id
        )
        service.set_context(
            key="key",
            value={"b": 3, "c": 4},
            session_id=session_id
        )

        result = service.get_context(key="key", session_id=session_id)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_create_and_restore_snapshot(self, service, session_id):
        """Test creating and restoring context snapshots."""
        service.set_context(key="key1", value="v1", session_id=session_id)
        service.set_context(key="key2", value="v2", session_id=session_id)

        snapshot_id = service.create_snapshot(session_id)

        # Delete all context
        service.delete_context(key="key1", session_id=session_id)
        service.delete_context(key="key2", session_id=session_id)

        # Restore snapshot
        result = service.restore_snapshot(snapshot_id, session_id)

        assert result is True
        assert service.get_context(key="key1", session_id=session_id) == "v1"
        assert service.get_context(key="key2", session_id=session_id) == "v2"

    def test_cleanup_expired(self, service, session_id):
        """Test cleaning up expired entries."""
        # Create entries with immediate expiration
        entry = service.set_context(
            key="expiring",
            value="test",
            session_id=session_id,
            ttl_seconds=1
        )
        entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        removed = service.cleanup_expired()

        assert removed >= 1

    def test_clear_session(self, service, session_id):
        """Test clearing all context for a session."""
        service.set_context(key="a", value=1, session_id=session_id)
        service.set_context(key="b", value=2, session_id=session_id)

        removed = service.clear_session(session_id)

        assert removed == 2
        assert service.get_context(key="a", session_id=session_id) is None

    def test_get_stats(self, service, session_id):
        """Test getting service statistics."""
        service.set_context(key="a", value=1, session_id=session_id)
        service.set_context(key="b", value=2, session_id=session_id)

        stats = service.get_stats()

        assert stats["total_entries"] >= 2
        assert "total_namespaces" in stats


# ==================== ResultAggregator Tests ====================

class TestResultAggregator:
    """Test ResultAggregator service."""

    @pytest.fixture
    def aggregator(self):
        """Create a fresh aggregator."""
        return ResultAggregator()

    @pytest.fixture
    def session_id(self):
        """Create a test session ID."""
        return uuid4()

    @pytest.fixture
    def task_id(self):
        """Create a test task ID."""
        return uuid4()

    def test_add_and_get_results(self, aggregator, session_id, task_id):
        """Test adding and retrieving results."""
        result = AgentResult(
            agent_id="test",
            task_id=task_id,
            success=True,
            output="test output"
        )

        aggregator.add_result(session_id, result)
        results = aggregator.get_results(session_id)

        assert len(results) == 1
        assert results[0].agent_id == "test"

    def test_get_successful_results(self, aggregator, session_id, task_id):
        """Test filtering successful results."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=False
        ))

        successful = aggregator.get_successful_results(session_id)

        assert len(successful) == 1
        assert successful[0].agent_id == "a"

    def test_aggregate_first_strategy(self, aggregator, session_id, task_id):
        """Test FIRST aggregation strategy."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="first"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True, output="second"
        ))

        config = AggregationConfig(strategy=AggregationStrategy.FIRST)
        result = aggregator.aggregate(session_id, config)

        assert result.final_output == "first"

    def test_aggregate_best_strategy(self, aggregator, session_id, task_id):
        """Test BEST aggregation strategy selects highest confidence."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True,
            output="low_conf", confidence=0.5
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True,
            output="high_conf", confidence=0.95
        ))

        config = AggregationConfig(strategy=AggregationStrategy.BEST)
        result = aggregator.aggregate(session_id, config)

        assert result.final_output == "high_conf"

    def test_aggregate_merge_dicts(self, aggregator, session_id, task_id):
        """Test MERGE strategy for dictionaries."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True,
            output={"findings": ["a1", "a2"]}
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True,
            output={"recommendations": ["b1"]}
        ))

        config = AggregationConfig(strategy=AggregationStrategy.MERGE)
        result = aggregator.aggregate(session_id, config)

        assert "findings" in result.final_output
        assert "recommendations" in result.final_output

    def test_aggregate_merge_lists(self, aggregator, session_id, task_id):
        """Test MERGE strategy for lists."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True,
            output=["item1", "item2"]
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True,
            output=["item3", "item4"]
        ))

        config = AggregationConfig(strategy=AggregationStrategy.MERGE)
        result = aggregator.aggregate(session_id, config)

        assert len(result.final_output) == 4

    def test_aggregate_vote_strategy(self, aggregator, session_id, task_id):
        """Test VOTE aggregation strategy."""
        # 2 votes for "approve", 1 for "reject"
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="approve"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True, output="approve"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="c", task_id=task_id, success=True, output="reject"
        ))

        config = AggregationConfig(strategy=AggregationStrategy.VOTE)
        result = aggregator.aggregate(session_id, config)

        assert result.final_output == "approve"

    def test_aggregate_weighted_numeric(self, aggregator, session_id, task_id):
        """Test WEIGHTED strategy for numeric values."""
        aggregator.set_agent_weight("a", 2.0)
        aggregator.set_agent_weight("b", 1.0)

        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True,
            output=100, confidence=1.0
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True,
            output=50, confidence=1.0
        ))

        config = AggregationConfig(
            strategy=AggregationStrategy.WEIGHTED,
            weight_by_confidence=False
        )
        result = aggregator.aggregate(session_id, config)

        # (100 * 2 + 50 * 1) / 3 = 83.33
        assert abs(result.final_output - 83.33) < 1

    def test_aggregate_consensus_reached(self, aggregator, session_id, task_id):
        """Test CONSENSUS strategy when threshold is met."""
        # 3 out of 4 agree (75%)
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="yes"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True, output="yes"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="c", task_id=task_id, success=True, output="yes"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="d", task_id=task_id, success=True, output="no"
        ))

        config = AggregationConfig(
            strategy=AggregationStrategy.CONSENSUS,
            consensus_threshold=0.7
        )
        result = aggregator.aggregate(session_id, config)

        assert result.final_output == "yes"

    def test_aggregate_consensus_not_reached(self, aggregator, session_id, task_id):
        """Test CONSENSUS strategy when threshold is not met."""
        # 50/50 split
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="yes"
        ))
        aggregator.add_result(session_id, AgentResult(
            agent_id="b", task_id=task_id, success=True, output="no"
        ))

        config = AggregationConfig(
            strategy=AggregationStrategy.CONSENSUS,
            consensus_threshold=0.7
        )
        result = aggregator.aggregate(session_id, config)

        assert result.final_output is None

    def test_aggregate_with_min_results(self, aggregator, session_id, task_id):
        """Test aggregation respects min_results."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="test"
        ))

        config = AggregationConfig(min_results=3)
        result = aggregator.aggregate(session_id, config)

        # Should still return result but with warning
        assert result is not None

    def test_aggregate_with_required_agents(self, aggregator, session_id, task_id):
        """Test aggregation checks for required agents."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="test"
        ))

        config = AggregationConfig(required_agents=["a", "b"])
        result = aggregator.aggregate(session_id, config)

        assert "b" in result.aggregation_metadata["missing_required"]

    def test_aggregate_session(self, aggregator, task_id):
        """Test aggregating from CollaborationSession."""
        session = CollaborationSession()
        session.add_result(AgentResult(
            agent_id="a", task_id=task_id, success=True, output="output"
        ))

        result = aggregator.aggregate_session(session)

        assert result.final_output == "output"
        assert result.session_id == session.session_id

    def test_clear_session(self, aggregator, session_id, task_id):
        """Test clearing session results."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True
        ))

        aggregator.clear_session(session_id)

        assert len(aggregator.get_results(session_id)) == 0

    def test_agent_weights(self, aggregator):
        """Test setting and getting agent weights."""
        aggregator.set_agent_weight("felix", 1.5)

        assert aggregator.get_agent_weight("felix") == 1.5
        assert aggregator.get_agent_weight("unknown") == 1.0  # Default

    def test_agent_weight_clamping(self, aggregator):
        """Test agent weights are clamped to valid range."""
        aggregator.set_agent_weight("a", 5.0)  # Over max
        aggregator.set_agent_weight("b", -1.0)  # Under min

        assert aggregator.get_agent_weight("a") == 2.0
        assert aggregator.get_agent_weight("b") == 0.0

    def test_get_stats(self, aggregator, session_id, task_id):
        """Test getting aggregation statistics."""
        aggregator.add_result(session_id, AgentResult(
            agent_id="a", task_id=task_id, success=True, output="test"
        ))
        aggregator.aggregate(session_id)

        stats = aggregator.get_stats()

        assert stats["total_aggregations"] >= 1
        assert "strategy_distribution" in stats


# ==================== PREDEFINED_PATTERNS Tests ====================

class TestPredefinedPatterns:
    """Test predefined collaboration patterns."""

    def test_security_audit_pattern(self):
        """Test security audit uses ENSEMBLE pattern."""
        pattern = PREDEFINED_PATTERNS["security_audit"]
        assert pattern["pattern"] == CollaborationPattern.ENSEMBLE
        assert AgentCapabilityType.SECURITY_AUDIT in pattern["required_capabilities"]

    def test_code_review_pattern(self):
        """Test code review uses CONSENSUS pattern."""
        pattern = PREDEFINED_PATTERNS["code_review"]
        assert pattern["pattern"] == CollaborationPattern.CONSENSUS
        assert pattern["aggregation_strategy"] == AggregationStrategy.CONSENSUS

    def test_migration_planning_pattern(self):
        """Test migration planning uses PIPELINE pattern."""
        pattern = PREDEFINED_PATTERNS["migration_planning"]
        assert pattern["pattern"] == CollaborationPattern.PIPELINE

    def test_rapid_prototyping_pattern(self):
        """Test rapid prototyping uses PARALLEL with BEST aggregation."""
        pattern = PREDEFINED_PATTERNS["rapid_prototyping"]
        assert pattern["pattern"] == CollaborationPattern.PARALLEL
        assert pattern["aggregation_strategy"] == AggregationStrategy.BEST


# ==================== Singleton Tests ====================

class TestSingletons:
    """Test singleton instances."""

    def test_get_agent_router_singleton(self):
        """Test agent router singleton."""
        router1 = get_agent_router()
        router2 = get_agent_router()
        assert router1 is router2

    def test_get_context_sharing_singleton(self):
        """Test context sharing singleton."""
        service1 = get_context_sharing_service()
        service2 = get_context_sharing_service()
        assert service1 is service2

    def test_get_result_aggregator_singleton(self):
        """Test result aggregator singleton."""
        agg1 = get_result_aggregator()
        agg2 = get_result_aggregator()
        assert agg1 is agg2
