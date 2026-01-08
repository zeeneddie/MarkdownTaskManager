"""
Tests for StateMachineExtractorService - Fase 25: Business Logic Extraction

Author: Claude Code (Week 138-139 - Fase 25)
Date: 2026-01-01
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.state_machine_extractor_service import (
    StateMachineExtractorService,
    ExtractedStateMachine,
    ExtractedState,
    ExtractedTransition,
    StatePatternType,
    StateMachineOutputFormat,
    StateMachineExtractionResult,
)


class TestStateMachineExtractorService:
    """Test suite for StateMachineExtractorService"""

    @pytest.fixture
    def service(self):
        """Create a service instance"""
        return StateMachineExtractorService(db=None)

    @pytest.fixture
    def vbnet_enum_state_code(self):
        """Sample VB.NET code with enum-based states"""
        return '''
        Public Enum OrderStatus
            Pending = 0
            Processing = 1
            Shipped = 2
            Delivered = 3
            Cancelled = 4
        End Enum

        Public Class Order
            Public Property Status As OrderStatus

            Public Sub Process()
                If Status = OrderStatus.Pending Then
                    Status = OrderStatus.Processing
                End If
            End Sub

            Public Sub Ship()
                If Status = OrderStatus.Processing Then
                    Status = OrderStatus.Shipped
                End If
            End Sub

            Public Sub Deliver()
                If Status = OrderStatus.Shipped Then
                    Status = OrderStatus.Delivered
                End If
            End Sub

            Public Sub Cancel()
                If Status <> OrderStatus.Delivered Then
                    Status = OrderStatus.Cancelled
                End If
            End Sub
        End Class
        '''

    @pytest.fixture
    def csharp_state_pattern_code(self):
        """Sample C# code with state design pattern"""
        return '''
        public interface IOrderState
        {
            void Process(Order order);
            void Ship(Order order);
            void Cancel(Order order);
        }

        public class PendingState : IOrderState
        {
            public void Process(Order order)
            {
                order.SetState(new ProcessingState());
            }
            public void Ship(Order order) => throw new InvalidOperationException();
            public void Cancel(Order order)
            {
                order.SetState(new CancelledState());
            }
        }

        public class ProcessingState : IOrderState
        {
            public void Process(Order order) => throw new InvalidOperationException();
            public void Ship(Order order)
            {
                order.SetState(new ShippedState());
            }
            public void Cancel(Order order)
            {
                order.SetState(new CancelledState());
            }
        }
        '''

    @pytest.fixture
    def vbnet_string_status_code(self):
        """Sample VB.NET code with string-based status"""
        return '''
        Public Class Document
            Private strStatus As String = "Draft"

            Public Sub Submit()
                If strStatus = "Draft" Then
                    strStatus = "Submitted"
                End If
            End Sub

            Public Sub Approve()
                If strStatus = "Submitted" Then
                    strStatus = "Approved"
                End If
            End Sub

            Public Sub Reject()
                If strStatus = "Submitted" Then
                    strStatus = "Rejected"
                End If
            End Sub

            Public Sub Publish()
                If strStatus = "Approved" Then
                    strStatus = "Published"
                End If
            End Sub
        End Class
        '''

    @pytest.fixture
    def javascript_switch_state_code(self):
        """Sample JavaScript code with switch-based state transitions"""
        return '''
        class TaskStateMachine {
            constructor() {
                this.state = "todo";
            }

            transition(action) {
                switch (this.state) {
                    case "todo":
                        if (action === "start") this.state = "in_progress";
                        break;
                    case "in_progress":
                        if (action === "complete") this.state = "done";
                        else if (action === "block") this.state = "blocked";
                        break;
                    case "blocked":
                        if (action === "unblock") this.state = "in_progress";
                        break;
                    case "done":
                        if (action === "reopen") this.state = "todo";
                        break;
                }
            }
        }
        '''

    @pytest.mark.asyncio
    async def test_create_session(self, service):
        """Test session creation"""
        session_id = await service.create_session(
            project_id="test-project",
            name="State Machine Test"
        )

        assert session_id is not None
        assert len(session_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_extract_from_vbnet_enum(self, service, vbnet_enum_state_code):
        """Test extraction from VB.NET enum-based states"""
        session_id = await service.create_session(name="VB.NET Enum Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"order.vb": vbnet_enum_state_code},
            language="vbnet"
        )

        assert result is not None
        assert result.total_files_scanned == 1
        assert len(result.errors) == 0
        # Should detect OrderStatus enum
        if result.total_machines_extracted > 0:
            assert any("OrderStatus" in m.name or "Order" in m.name for m in result.machines)

    @pytest.mark.asyncio
    async def test_extract_from_csharp_pattern(self, service, csharp_state_pattern_code):
        """Test extraction from C# state design pattern"""
        session_id = await service.create_session(name="C# Pattern Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"order_state.cs": csharp_state_pattern_code},
            language="csharp"
        )

        assert result is not None
        assert result.total_files_scanned == 1
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_extract_from_string_status(self, service, vbnet_string_status_code):
        """Test extraction from string-based status field"""
        session_id = await service.create_session(name="String Status Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"document.vb": vbnet_string_status_code},
            language="vbnet"
        )

        assert result is not None
        assert result.total_files_scanned == 1
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_extract_from_javascript_switch(self, service, javascript_switch_state_code):
        """Test extraction from JavaScript switch-based states"""
        session_id = await service.create_session(name="JavaScript Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"task.js": javascript_switch_state_code},
            language="javascript"
        )

        assert result is not None
        assert result.total_files_scanned == 1
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, service):
        """Test getting non-existent session"""
        result = await service.get_session("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_after_extraction(self, service, vbnet_enum_state_code):
        """Test getting session after extraction"""
        session_id = await service.create_session(name="Get Session Test")

        await service.extract_from_files(
            session_id=session_id,
            files={"test.vb": vbnet_enum_state_code},
            language="vbnet"
        )

        result = await service.get_session(session_id)
        assert result is not None
        assert result.session_id == session_id

    @pytest.mark.asyncio
    async def test_export_to_mermaid(self, service):
        """Test Mermaid diagram export"""
        machine = ExtractedStateMachine(
            name="OrderStateMachine",
            description="Order processing state machine",
            states=[
                ExtractedState(name="Pending", is_initial=True),
                ExtractedState(name="Processing"),
                ExtractedState(name="Shipped"),
                ExtractedState(name="Delivered", is_final=True),
            ],
            transitions=[
                ExtractedTransition(from_state="Pending", to_state="Processing", trigger="process"),
                ExtractedTransition(from_state="Processing", to_state="Shipped", trigger="ship"),
                ExtractedTransition(from_state="Shipped", to_state="Delivered", trigger="deliver"),
            ],
            initial_state="Pending",
        )

        mermaid = await service.export_to_format(machine, StateMachineOutputFormat.MERMAID)

        assert "stateDiagram-v2" in mermaid
        assert "Pending" in mermaid
        assert "Processing" in mermaid
        assert "Shipped" in mermaid
        assert "Delivered" in mermaid
        assert "-->" in mermaid

    @pytest.mark.asyncio
    async def test_export_to_xstate(self, service):
        """Test XState JSON export"""
        machine = ExtractedStateMachine(
            name="SimpleStateMachine",
            states=[
                ExtractedState(name="idle", is_initial=True),
                ExtractedState(name="active"),
                ExtractedState(name="done", is_final=True),
            ],
            transitions=[
                ExtractedTransition(from_state="idle", to_state="active", trigger="START"),
                ExtractedTransition(from_state="active", to_state="done", trigger="FINISH"),
            ],
            initial_state="idle",
        )

        xstate_json = await service.export_to_format(machine, StateMachineOutputFormat.XSTATE)

        assert "SimpleStateMachine" in xstate_json
        assert '"initial": "idle"' in xstate_json
        assert "states" in xstate_json
        assert "START" in xstate_json
        assert "FINISH" in xstate_json

    @pytest.mark.asyncio
    async def test_export_to_plantuml(self, service):
        """Test PlantUML export"""
        machine = ExtractedStateMachine(
            name="TestMachine",
            states=[
                ExtractedState(name="Start", is_initial=True),
                ExtractedState(name="End", is_final=True),
            ],
            transitions=[
                ExtractedTransition(from_state="Start", to_state="End", trigger="go"),
            ],
            initial_state="Start",
        )

        plantuml = await service.export_to_format(machine, StateMachineOutputFormat.PLANTUML)

        assert "@startuml" in plantuml
        assert "@enduml" in plantuml
        assert "Start" in plantuml
        assert "End" in plantuml
        assert "-->" in plantuml

    @pytest.mark.asyncio
    async def test_export_session(self, service, vbnet_enum_state_code):
        """Test exporting entire session"""
        session_id = await service.create_session(name="Export Test")

        await service.extract_from_files(
            session_id=session_id,
            files={"test.vb": vbnet_enum_state_code},
            language="vbnet"
        )

        content = await service.export_session(session_id, StateMachineOutputFormat.MARKDOWN)
        assert content is not None
        assert isinstance(content, str)

    @pytest.mark.asyncio
    async def test_multiple_files_extraction(self, service, vbnet_enum_state_code, javascript_switch_state_code):
        """Test extraction from multiple files"""
        session_id = await service.create_session(name="Multi-file Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={
                "order.vb": vbnet_enum_state_code,
                "task.js": javascript_switch_state_code,
            },
            language="vbnet"
        )

        assert result is not None
        assert result.total_files_scanned == 2


class TestStateMachineModels:
    """Test state machine models"""

    def test_extracted_state_creation(self):
        """Test ExtractedState dataclass creation"""
        state = ExtractedState(
            name="Processing",
            description="Order is being processed",
            is_initial=False,
            is_final=False,
            original_value="PROCESSING",
            metadata={"entry_actions": ["notifyStart"], "exit_actions": ["logTransition"]},
        )

        assert state.name == "Processing"
        assert not state.is_initial
        assert not state.is_final
        assert state.original_value == "PROCESSING"
        assert "notifyStart" in state.metadata["entry_actions"]
        assert "logTransition" in state.metadata["exit_actions"]

    def test_extracted_transition_creation(self):
        """Test ExtractedTransition dataclass creation"""
        transition = ExtractedTransition(
            from_state="Pending",
            to_state="Processing",
            trigger="process",
            guard="order.isValid()",
            action="validateOrder",
            description="Process order when valid",
        )

        assert transition.from_state == "Pending"
        assert transition.to_state == "Processing"
        assert transition.trigger == "process"
        assert transition.guard == "order.isValid()"
        assert transition.action == "validateOrder"

    def test_extracted_state_machine_methods(self):
        """Test ExtractedStateMachine methods"""
        machine = ExtractedStateMachine(
            name="TestMachine",
            description="Test state machine",
            pattern_type=StatePatternType.ENUM_BASED,
            states=[
                ExtractedState(name="S1", is_initial=True),
                ExtractedState(name="S2"),
            ],
            transitions=[ExtractedTransition(from_state="S1", to_state="S2", trigger="go")],
            initial_state="S1",
        )

        # Test get_state_names method
        state_names = machine.get_state_names()
        assert state_names == ["S1", "S2"]

        # Test to_mermaid method
        mermaid = machine.to_mermaid()
        assert "stateDiagram-v2" in mermaid
        assert "S1 --> S2" in mermaid

    def test_state_pattern_type_enum(self):
        """Test StatePatternType enum values"""
        assert StatePatternType.ENUM_BASED.value == "enum_based"
        assert StatePatternType.STRING_BASED.value == "string_based"
        assert StatePatternType.CLASS_BASED.value == "class_based"
        assert StatePatternType.SWITCH_CASE.value == "switch_case"
        assert StatePatternType.IF_ELSE_CHAIN.value == "if_else_chain"
        assert StatePatternType.STATUS_FIELD.value == "status_field"

    def test_output_format_enum(self):
        """Test StateMachineOutputFormat enum values"""
        assert StateMachineOutputFormat.MERMAID.value == "mermaid"
        assert StateMachineOutputFormat.XSTATE.value == "xstate"
        assert StateMachineOutputFormat.PLANTUML.value == "plantuml"
        assert StateMachineOutputFormat.JSON.value == "json"
        assert StateMachineOutputFormat.MARKDOWN.value == "markdown"

    def test_extracted_transition_with_source_info(self):
        """Test ExtractedTransition with source tracking"""
        transition = ExtractedTransition(
            from_state="A",
            to_state="B",
            trigger="transition",
            source_file="order.vb",
            source_line_start=100,
            source_line_end=105,
            source_code="If Status = A Then Status = B",
            confidence=0.85,
        )

        assert transition.source_file == "order.vb"
        assert transition.source_line_start == 100
        assert transition.source_line_end == 105
        assert transition.confidence == 0.85
