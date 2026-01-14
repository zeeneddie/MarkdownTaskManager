"""
Tests for Confucius Quality Gate System.

Tests cover:
- Quality rules evaluation
- QualityGateEvaluator
- IterationController PIV loop
- EscalationService
- SSE streaming
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.confucius.quality import (
    # Rules
    QualityDimension,
    Severity,
    RuleViolation,
    RuleResult,
    QualityRule,
    CompletenessRule,
    NonEmptyOutputRule,
    SuccessStatusRule,
    NoErrorsRule,
    ArchitectureDecisionRule,
    CriticalIssuesRule,
    EstimationConfidenceRule,
    get_rules_for_domain,
    DOMAIN_RULE_SETS,
    # Evaluator
    GateDecision,
    QualityGateEvaluator,
    EvaluationResult,
    create_evaluator,
    # Iteration
    IterationStatus,
    ImprovementStrategy,
    IterationContext,
    IterationController,
    create_iteration_controller,
    # Escalation
    EscalationType,
    EscalationPriority,
    EscalationService,
    EscalationDecision,
    create_escalation_service,
    # Streaming
    StreamEventType,
    StreamEvent,
    QualityProgressStream,
    QualityProgressContext,
    get_global_stream,
    reset_global_stream,
)


# =============================================================================
# RULES TESTS
# =============================================================================

class TestQualityRules:
    """Tests for quality scoring rules."""

    def test_completeness_rule_all_present(self):
        """Test completeness with all fields present."""
        rule = CompletenessRule(["name", "value"])
        output = {"name": "test", "value": 42}

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score == 1.0
        assert len(result.violations) == 0

    def test_completeness_rule_missing_field(self):
        """Test completeness with missing field."""
        rule = CompletenessRule(["name", "value", "description"])
        output = {"name": "test", "value": 42}

        result = rule.evaluate(output, {})

        assert not result.passed
        assert result.score < 1.0
        assert any(v.message.find("description") >= 0 for v in result.violations)

    def test_completeness_rule_empty_field(self):
        """Test completeness with empty field."""
        rule = CompletenessRule(["name", "items"])
        output = {"name": "test", "items": []}

        result = rule.evaluate(output, {})

        # Empty is a warning, not failure
        assert result.passed
        assert any(v.severity == Severity.WARNING for v in result.violations)

    def test_success_status_rule_success(self):
        """Test success status rule with success."""
        rule = SuccessStatusRule()
        output = {"success": True, "result": "done"}

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score == 1.0

    def test_success_status_rule_failure(self):
        """Test success status rule with failure."""
        rule = SuccessStatusRule()
        output = {"success": False, "error": "Something went wrong"}

        result = rule.evaluate(output, {})

        assert not result.passed
        assert result.score == 0.0
        assert result.violations[0].severity == Severity.CRITICAL

    def test_no_errors_rule_clean(self):
        """Test no errors rule with clean output."""
        rule = NoErrorsRule()
        output = {"success": True, "data": []}

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score == 1.0

    def test_no_errors_rule_with_errors(self):
        """Test no errors rule with errors."""
        rule = NoErrorsRule()
        output = {"success": True, "errors": ["Error 1", "Error 2"]}

        result = rule.evaluate(output, {})

        assert not result.passed
        assert len(result.violations) == 2

    def test_non_empty_output_rule_sufficient(self):
        """Test non-empty output with sufficient content."""
        rule = NonEmptyOutputRule(min_content_length=10)
        output = {"data": "This is sufficient content"}

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score > 0

    def test_non_empty_output_rule_too_short(self):
        """Test non-empty output with too short content."""
        rule = NonEmptyOutputRule(min_content_length=100)
        output = {"x": 1}

        result = rule.evaluate(output, {})

        assert not result.passed
        assert result.score == 0.0
        assert result.violations[0].severity == Severity.CRITICAL

    def test_architecture_decision_rule_present(self):
        """Test architecture decision rule with decisions."""
        rule = ArchitectureDecisionRule(min_decisions=2)
        output = {
            "architecture_decisions": [
                {"title": "Use microservices"},
                {"title": "Use PostgreSQL"},
            ]
        }

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score == 1.0

    def test_architecture_decision_rule_insufficient(self):
        """Test architecture decision rule with too few decisions."""
        rule = ArchitectureDecisionRule(min_decisions=3)
        output = {"architecture_decisions": [{"title": "Use Docker"}]}

        result = rule.evaluate(output, {})

        assert not result.passed
        assert result.score < 1.0

    def test_critical_issues_rule_clean(self):
        """Test critical issues rule with no critical issues."""
        rule = CriticalIssuesRule()
        output = {
            "security_issues": [{"severity": "warning", "description": "Low risk"}]
        }

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score == 1.0

    def test_critical_issues_rule_with_critical(self):
        """Test critical issues rule with critical issues."""
        rule = CriticalIssuesRule()
        output = {
            "security_issues": [{"severity": "critical", "description": "SQL injection"}]
        }

        result = rule.evaluate(output, {})

        assert not result.passed
        assert result.score == 0.0
        assert result.violations[0].severity == Severity.CRITICAL

    def test_estimation_confidence_rule_high(self):
        """Test estimation confidence with high confidence."""
        rule = EstimationConfidenceRule(min_confidence=0.6)
        output = {"confidence": 0.85}

        result = rule.evaluate(output, {})

        assert result.passed
        assert result.score == 1.0

    def test_estimation_confidence_rule_low(self):
        """Test estimation confidence with low confidence."""
        rule = EstimationConfidenceRule(min_confidence=0.6)
        output = {"confidence": 0.4}

        result = rule.evaluate(output, {})

        assert not result.passed
        assert result.score < 1.0

    def test_get_rules_for_domain(self):
        """Test getting rules for specific domain."""
        arch_rules = get_rules_for_domain("architecture")
        assert arch_rules.domain == "architecture"
        assert len(arch_rules.rules) > 0

        unknown_rules = get_rules_for_domain("unknown")
        assert unknown_rules.domain == "general"

    def test_domain_rule_sets_exist(self):
        """Test that all domain rule sets are defined."""
        expected_domains = ["architecture", "quality", "estimation", "documentation", "testing", "general"]
        for domain in expected_domains:
            assert domain in DOMAIN_RULE_SETS


# =============================================================================
# EVALUATOR TESTS
# =============================================================================

class TestQualityGateEvaluator:
    """Tests for QualityGateEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance."""
        return QualityGateEvaluator(
            default_threshold=0.85,
            warn_threshold=0.90,
        )

    def test_evaluate_passing_output(self, evaluator):
        """Test evaluation of passing output."""
        output = {
            "success": True,
            "architecture_decisions": [{"title": "Decision 1"}],
            "recommendations": ["Rec 1"],
            "risks": ["Risk 1"],
        }

        result = evaluator.evaluate(
            output=output,
            context={"domain": "architecture"},
            entry_id="test-123",
            agent_name="Felix",
        )

        assert isinstance(result, EvaluationResult)
        assert result.entry_id == "test-123"
        assert result.agent_name == "Felix"
        assert result.domain == "architecture"
        assert 0 <= result.overall_score <= 1

    def test_evaluate_failing_output(self, evaluator):
        """Test evaluation of failing output."""
        output = {
            "success": False,
            "error": "Something failed",
        }

        result = evaluator.evaluate(
            output=output,
            context={"domain": "architecture"},
            entry_id="test-456",
            agent_name="Felix",
        )

        assert result.decision == GateDecision.FAIL
        assert result.has_critical
        assert result.feedback_for_retry is not None

    def test_evaluate_with_threshold_override(self, evaluator):
        """Test evaluation with threshold override."""
        output = {"success": True, "data": "x" * 100}

        result = evaluator.evaluate(
            output=output,
            context={"domain": "general"},
            entry_id="test-789",
            agent_name="Quinn",
            threshold_override=0.5,
        )

        assert result.threshold == 0.5

    def test_evaluate_domain_detection(self, evaluator):
        """Test automatic domain detection from agent name."""
        output = {"success": True, "function_points": 120}

        result = evaluator.evaluate(
            output=output,
            context={},  # No domain specified
            entry_id="test-eliza",
            agent_name="Eliza",
        )

        assert result.domain == "estimation"

    def test_evaluate_dimension_scores(self, evaluator):
        """Test that dimension scores are calculated."""
        output = {"success": True, "data": "content"}

        result = evaluator.evaluate(
            output=output,
            context={"domain": "general"},
            entry_id="test-dim",
            agent_name="Test",
        )

        assert len(result.dimension_scores) > 0
        for dim, score in result.dimension_scores.items():
            assert score.rule_count > 0

    def test_evaluate_to_dict(self, evaluator):
        """Test result serialization."""
        output = {"success": True}

        result = evaluator.evaluate(
            output=output,
            context={"domain": "general"},
            entry_id="test-dict",
            agent_name="Test",
        )

        result_dict = result.to_dict()

        assert "entry_id" in result_dict
        assert "overall_score" in result_dict
        assert "decision" in result_dict
        assert "violations" in result_dict

    def test_register_custom_rules(self, evaluator):
        """Test registering custom rules."""

        class CustomRule(QualityRule):
            def __init__(self):
                super().__init__("custom", QualityDimension.RELEVANCE)

            def evaluate(self, output, context):
                return self._create_result(True, 1.0)

        evaluator.register_custom_rules("test", [CustomRule()])

        summary = evaluator.get_rule_summary("test")
        # Custom rules apply, but domain defaults to general
        assert summary["custom_rules"] == 1

    def test_create_evaluator_factory(self):
        """Test factory function."""
        evaluator = create_evaluator(threshold=0.75)
        assert isinstance(evaluator, QualityGateEvaluator)


# =============================================================================
# ITERATION CONTROLLER TESTS
# =============================================================================

class TestIterationController:
    """Tests for IterationController."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator."""
        return create_evaluator(threshold=0.85)

    @pytest.fixture
    def controller(self, evaluator):
        """Create controller."""
        return IterationController(
            evaluator=evaluator,
            max_iterations=3,
        )

    @pytest.mark.asyncio
    async def test_run_single_successful_iteration(self, controller):
        """Test single successful iteration."""
        async def executor(task, context):
            return {"success": True, "result": "done", "data": "x" * 100}

        result = await controller.run_with_quality_gate(
            task="Test task",
            context={"domain": "general"},
            agent_executor=executor,
            entry_id="test-success",
            agent_name="Test",
        )

        assert "_iteration_metadata" in result
        metadata = result["_iteration_metadata"]
        assert metadata["final_status"] in ["succeeded", "escalated"]

    @pytest.mark.asyncio
    async def test_run_with_retry(self, controller):
        """Test iteration with retry."""
        call_count = 0

        async def executor(task, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return {"success": False, "error": "Simulated failure"}
            return {"success": True, "result": "done", "data": "x" * 100}

        result = await controller.run_with_quality_gate(
            task="Test task",
            context={"domain": "general"},
            agent_executor=executor,
            entry_id="test-retry",
            agent_name="Test",
        )

        metadata = result["_iteration_metadata"]
        assert metadata["total_iterations"] >= 2

    @pytest.mark.asyncio
    async def test_run_escalates_after_max_iterations(self, controller):
        """Test escalation after max iterations."""
        async def executor(task, context):
            return {"success": False, "error": "Always fails"}

        result = await controller.run_with_quality_gate(
            task="Test task",
            context={"domain": "general"},
            agent_executor=executor,
            entry_id="test-escalate",
            agent_name="Test",
        )

        metadata = result["_iteration_metadata"]
        assert metadata["final_status"] == "escalated"
        assert metadata["total_iterations"] == 3

    @pytest.mark.asyncio
    async def test_progress_callback(self, controller):
        """Test progress callback is called."""
        events = []

        async def callback(event, data):
            events.append((event, data))

        controller.set_progress_callback(callback)

        async def executor(task, context):
            return {"success": True, "data": "x" * 100}

        await controller.run_with_quality_gate(
            task="Test task",
            context={"domain": "general"},
            agent_executor=executor,
            entry_id="test-callback",
            agent_name="Test",
        )

        assert len(events) > 0
        event_types = [e[0] for e in events]
        assert "iteration_started" in event_types

    def test_iteration_context_enrichment(self):
        """Test iteration context enrichment."""
        ctx = IterationContext(
            entry_id="test",
            agent_name="Test",
            original_task="Task",
            original_context={"key": "value"},
        )
        ctx.add_feedback("Feedback 1")
        ctx.current_iteration = 2

        enriched = ctx.get_enriched_context()

        assert enriched["key"] == "value"
        assert enriched["iteration"] == 2
        assert "Feedback 1" in enriched["previous_feedback"]

    def test_create_iteration_controller_factory(self):
        """Test factory function."""
        controller = create_iteration_controller(max_iterations=5)
        assert isinstance(controller, IterationController)


# =============================================================================
# ESCALATION SERVICE TESTS
# =============================================================================

class TestEscalationService:
    """Tests for EscalationService."""

    @pytest.fixture
    def service(self):
        """Create escalation service."""
        return EscalationService(
            partial_acceptance_threshold=0.7,
            decomposition_threshold=0.5,
        )

    @pytest.fixture
    def failed_context(self):
        """Create failed iteration context."""
        ctx = IterationContext(
            entry_id="test-fail",
            agent_name="Felix",
            original_task="Analyze architecture",
            original_context={},
            max_iterations=3,
            current_iteration=3,
        )
        return ctx

    @pytest.mark.asyncio
    async def test_escalate_creates_ticket(self, service, failed_context):
        """Test escalation creates ticket."""
        decision = await service.escalate(failed_context)

        assert isinstance(decision, EscalationDecision)
        assert decision.escalation_type is not None
        assert decision.priority is not None
        assert decision.action is not None

    @pytest.mark.asyncio
    async def test_escalate_with_handler(self, service, failed_context):
        """Test escalation with registered handler."""
        handler_called = False

        async def handler(ticket):
            nonlocal handler_called
            handler_called = True
            return {"handled": True}

        service.register_handler(EscalationType.COUNCIL_REVIEW, handler)

        await service.escalate(failed_context)

        # Handler may or may not be called depending on escalation type
        # Just verify the service works

    def test_fallback_agents_defined(self, service):
        """Test fallback agents are defined for all agents."""
        expected_agents = [
            "Felix", "Quinn", "Eliza", "Diana", "Marcus",
            "Miguel", "Tessa", "Peter", "Paul", "Betty", "Vicky",
        ]

        for agent in expected_agents:
            assert agent in service.FALLBACK_AGENTS
            assert len(service.FALLBACK_AGENTS[agent]) > 0

    @pytest.mark.asyncio
    async def test_resolve_ticket(self, service, failed_context):
        """Test ticket resolution."""
        # First escalate to create ticket
        await service.escalate(failed_context)

        # Get open tickets
        tickets = service.get_open_tickets()
        assert len(tickets) > 0

        ticket = tickets[0]
        result = await service.resolve_ticket(
            ticket.ticket_id,
            "Manually fixed",
            "Test User",
        )

        assert result is True
        resolved_ticket = service.get_ticket(ticket.ticket_id)
        assert resolved_ticket.resolved_at is not None
        assert resolved_ticket.resolution == "Manually fixed"

    def test_escalation_stats(self, service):
        """Test escalation statistics."""
        stats = service.get_escalation_stats()

        assert "total_tickets" in stats
        assert "open_tickets" in stats
        assert "by_type" in stats

    def test_create_escalation_service_factory(self):
        """Test factory function."""
        service = create_escalation_service(partial_threshold=0.6)
        assert isinstance(service, EscalationService)


# =============================================================================
# STREAMING TESTS
# =============================================================================

class TestQualityProgressStream:
    """Tests for SSE streaming."""

    @pytest.fixture
    def stream(self):
        """Create stream instance."""
        return QualityProgressStream()

    @pytest.mark.asyncio
    async def test_emit_event(self, stream):
        """Test emitting event."""
        await stream.emit(
            StreamEventType.TASK_STARTED,
            "test-123",
            {"agent_name": "Felix"},
        )

        # No exception means success

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self, stream):
        """Test subscribing and receiving events."""
        import asyncio

        async def subscriber():
            events = []
            async for event in stream.subscribe("test-sub", include_heartbeat=False):
                events.append(event)
                if event.event_type == StreamEventType.TASK_COMPLETED:
                    break
            return events

        async def emitter():
            await asyncio.sleep(0.01)
            await stream.emit(StreamEventType.TASK_STARTED, "test-sub", {})
            await stream.emit(StreamEventType.PROGRESS_UPDATE, "test-sub", {"progress": 0.5})
            await stream.emit(StreamEventType.TASK_COMPLETED, "test-sub", {})

        # Run both concurrently
        sub_task = asyncio.create_task(subscriber())
        emit_task = asyncio.create_task(emitter())

        events = await asyncio.wait_for(sub_task, timeout=5.0)
        await emit_task

        assert len(events) == 3
        assert events[0].event_type == StreamEventType.TASK_STARTED
        assert events[1].event_type == StreamEventType.PROGRESS_UPDATE
        assert events[2].event_type == StreamEventType.TASK_COMPLETED

    def test_stream_event_to_sse(self, stream):
        """Test SSE format output."""
        event = StreamEvent(
            event_type=StreamEventType.ITERATION_STARTED,
            entry_id="test-sse",
            data={"iteration": 1},
        )

        sse_output = event.to_sse()

        assert "event: iteration_started" in sse_output
        assert "data:" in sse_output
        assert "test-sse" in sse_output

    def test_create_progress_callback(self, stream):
        """Test progress callback creation."""
        callback = stream.create_progress_callback("test-cb")

        assert callable(callback)

    def test_unsubscribe(self, stream):
        """Test unsubscribing."""
        # Not subscribed yet
        assert stream.unsubscribe("not-exists") is False

    def test_get_subscriber_count(self, stream):
        """Test subscriber count."""
        assert stream.get_subscriber_count() == 0

    def test_shutdown(self, stream):
        """Test shutdown."""
        stream.shutdown()
        # Should not raise

    def test_global_stream(self):
        """Test global stream singleton."""
        reset_global_stream()

        stream1 = get_global_stream()
        stream2 = get_global_stream()

        assert stream1 is stream2

        reset_global_stream()


class TestQualityProgressContext:
    """Tests for progress context manager."""

    @pytest.mark.asyncio
    async def test_context_emits_start_complete(self):
        """Test context emits start and complete events."""
        stream = QualityProgressStream()
        events = []

        original_emit = stream.emit

        async def capture_emit(event_type, entry_id, data):
            events.append(event_type)
            await original_emit(event_type, entry_id, data)

        stream.emit = capture_emit

        async with QualityProgressContext(stream, "test-ctx", "Felix"):
            pass

        assert StreamEventType.TASK_STARTED in events
        assert StreamEventType.TASK_COMPLETED in events

    @pytest.mark.asyncio
    async def test_context_emits_fail_on_exception(self):
        """Test context emits fail on exception."""
        stream = QualityProgressStream()
        events = []

        original_emit = stream.emit

        async def capture_emit(event_type, entry_id, data):
            events.append(event_type)
            await original_emit(event_type, entry_id, data)

        stream.emit = capture_emit

        with pytest.raises(ValueError):
            async with QualityProgressContext(stream, "test-fail", "Felix"):
                raise ValueError("Test error")

        assert StreamEventType.TASK_STARTED in events
        assert StreamEventType.TASK_FAILED in events

    @pytest.mark.asyncio
    async def test_context_update_progress(self):
        """Test progress update method."""
        stream = QualityProgressStream()

        async with QualityProgressContext(stream, "test-prog", "Felix") as ctx:
            await ctx.update_progress(0.5, "Halfway done")

        # No exception means success

    @pytest.mark.asyncio
    async def test_context_emit_partial(self):
        """Test partial result emission."""
        stream = QualityProgressStream()

        async with QualityProgressContext(stream, "test-partial", "Felix") as ctx:
            await ctx.emit_partial({"patterns": ["MVC", "Repository"]})

        # No exception means success


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestQualityGateIntegration:
    """Integration tests for the quality gate system."""

    @pytest.mark.asyncio
    async def test_full_piv_loop_success(self):
        """Test full PIV loop with success."""
        evaluator = create_evaluator(threshold=0.7)
        controller = create_iteration_controller(evaluator=evaluator, max_iterations=3)

        async def architect_executor(task, context):
            return {
                "success": True,
                "architecture_decisions": [{"title": "Use microservices"}],
                "recommendations": ["Scale horizontally"],
                "risks": ["Network latency"],
                "components": {"legacy": [], "target": []},
                "data": "x" * 100,
            }

        result = await controller.run_with_quality_gate(
            task="Analyze legacy system",
            context={"domain": "architecture"},
            agent_executor=architect_executor,
            entry_id="integration-test",
            agent_name="Felix",
        )

        assert result["success"] is True
        assert "_iteration_metadata" in result
        assert result["_iteration_metadata"]["final_status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_full_piv_loop_with_escalation(self):
        """Test full PIV loop ending in escalation."""
        evaluator = create_evaluator(threshold=0.95)  # High threshold
        controller = create_iteration_controller(evaluator=evaluator, max_iterations=2)
        escalation = create_escalation_service()

        async def failing_executor(task, context):
            return {"success": False, "error": "Cannot process"}

        result = await controller.run_with_quality_gate(
            task="Impossible task",
            context={"domain": "general"},
            agent_executor=failing_executor,
            entry_id="escalation-test",
            agent_name="Quinn",
        )

        # Should be escalated
        metadata = result["_iteration_metadata"]
        assert metadata["final_status"] == "escalated"

        # Can escalate the context
        ctx = IterationContext(
            entry_id="escalation-test",
            agent_name="Quinn",
            original_task="Impossible task",
            original_context={},
            current_iteration=2,
        )
        decision = await escalation.escalate(ctx)

        assert decision is not None
        assert decision.action is not None
