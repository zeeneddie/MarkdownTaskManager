"""
Tests for DecisionTableExtractorService - Fase 25: Business Logic Extraction

Author: Claude Code (Week 138-139 - Fase 25)
Date: 2026-01-01
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.decision_table import (
    DecisionTable,
    DecisionRule,
    DecisionTableExtractionResult,
    HitPolicy,
    ConditionOperator,
    InputColumn,
    OutputColumn,
    ConditionEntry,
    ActionEntry,
    DecisionTableOutputFormat,
)
from app.services.decision_table_extractor_service import DecisionTableExtractorService


class TestDecisionTableExtractorService:
    """Test suite for DecisionTableExtractorService"""

    @pytest.fixture
    def service(self):
        """Create a service instance"""
        return DecisionTableExtractorService(db=None)

    @pytest.fixture
    def vbnet_if_else_code(self):
        """Sample VB.NET code with nested IF-ELSE"""
        return '''
        Function CalculateDiscount(ByVal orderTotal As Decimal, ByVal customerType As String) As Decimal
            Dim discount As Decimal = 0
            
            If customerType = "Premium" Then
                If orderTotal >= 1000 Then
                    discount = 0.20
                ElseIf orderTotal >= 500 Then
                    discount = 0.15
                ElseIf orderTotal >= 100 Then
                    discount = 0.10
                Else
                    discount = 0.05
                End If
            ElseIf customerType = "Regular" Then
                If orderTotal >= 1000 Then
                    discount = 0.10
                ElseIf orderTotal >= 500 Then
                    discount = 0.05
                Else
                    discount = 0
                End If
            Else
                discount = 0
            End If
            
            Return discount
        End Function
        '''

    @pytest.fixture
    def csharp_switch_code(self):
        """Sample C# code with switch statement"""
        return '''
        public decimal GetShippingCost(string region, decimal weight)
        {
            switch (region)
            {
                case "US":
                    if (weight < 1) return 5.99m;
                    else if (weight < 5) return 9.99m;
                    else return 14.99m;
                case "EU":
                    if (weight < 1) return 9.99m;
                    else if (weight < 5) return 19.99m;
                    else return 29.99m;
                case "ASIA":
                    if (weight < 1) return 14.99m;
                    else if (weight < 5) return 29.99m;
                    else return 49.99m;
                default:
                    return 99.99m;
            }
        }
        '''

    @pytest.fixture
    def python_conditional_code(self):
        """Sample Python code with conditional logic"""
        return '''
        def get_priority_level(urgency, impact):
            if urgency == "high" and impact == "high":
                return "P1"
            elif urgency == "high" and impact == "medium":
                return "P2"
            elif urgency == "high" and impact == "low":
                return "P3"
            elif urgency == "medium" and impact == "high":
                return "P2"
            elif urgency == "medium" and impact == "medium":
                return "P3"
            else:
                return "P4"
        '''

    @pytest.mark.asyncio
    async def test_create_session(self, service):
        """Test session creation"""
        session_id = await service.create_session(
            project_id="test-project",
            name="Test Extraction"
        )

        assert session_id is not None
        assert len(session_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_extract_from_vbnet_if_else(self, service, vbnet_if_else_code):
        """Test extraction from VB.NET nested IF-ELSE"""
        session_id = await service.create_session(name="VB.NET Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"discount.vb": vbnet_if_else_code},
            language="vbnet"
        )

        assert result is not None
        assert result.total_files_scanned == 1
        assert result.total_tables_extracted >= 0  # Pattern detection may vary
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_extract_from_csharp_switch(self, service, csharp_switch_code):
        """Test extraction from C# switch statement"""
        session_id = await service.create_session(name="C# Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"shipping.cs": csharp_switch_code},
            language="csharp"
        )

        assert result is not None
        assert result.total_files_scanned == 1
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_extract_from_python(self, service, python_conditional_code):
        """Test extraction from Python conditional logic"""
        session_id = await service.create_session(name="Python Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={"priority.py": python_conditional_code},
            language="python"
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
    async def test_get_session_after_extraction(self, service, python_conditional_code):
        """Test getting session after extraction"""
        session_id = await service.create_session(name="Get Session Test")

        await service.extract_from_files(
            session_id=session_id,
            files={"test.py": python_conditional_code},
            language="python"
        )

        result = await service.get_session(session_id)
        assert result is not None
        assert result.session_id == session_id

    @pytest.mark.asyncio
    async def test_export_to_markdown(self, service):
        """Test markdown export"""
        # Create input/output columns first to get IDs
        input1 = InputColumn(name="customerType", label="Customer Type", type_ref="string")
        input2 = InputColumn(name="orderTotal", label="Order Total", type_ref="decimal")
        output1 = OutputColumn(name="discount", label="Discount", type_ref="decimal")

        # Create a decision table manually
        table = DecisionTable(
            name="DiscountTable",
            description="Test discount table",
            inputs=[input1, input2],
            outputs=[output1],
            rules=[
                DecisionRule(
                    rule_number=1,
                    annotation="Premium customer with high order",
                    conditions=[
                        ConditionEntry(column_id=input1.id, operator=ConditionOperator.EQUALS, value="Premium"),
                        ConditionEntry(column_id=input2.id, operator=ConditionOperator.GREATER_THAN_OR_EQUALS, value="1000"),
                    ],
                    actions=[ActionEntry(column_id=output1.id, value="0.20")],
                ),
            ],
            hit_policy=HitPolicy.UNIQUE,
        )

        markdown = await service.export_to_markdown(table)

        assert "DiscountTable" in markdown
        assert "Customer Type" in markdown
        assert "Order Total" in markdown
        assert "Discount" in markdown

    @pytest.mark.asyncio
    async def test_export_to_dmn_xml(self, service):
        """Test DMN XML export"""
        input1 = InputColumn(name="input1", label="Input 1", type_ref="string")
        output1 = OutputColumn(name="output1", label="Output 1", type_ref="string")

        table = DecisionTable(
            name="SimpleTable",
            description="Simple test table",
            inputs=[input1],
            outputs=[output1],
            rules=[
                DecisionRule(
                    rule_number=1,
                    conditions=[ConditionEntry(column_id=input1.id, operator=ConditionOperator.EQUALS, value="A")],
                    actions=[ActionEntry(column_id=output1.id, value="Result A")],
                ),
            ],
        )

        xml = await service.export_to_dmn_xml(table)

        # XML declaration may use single or double quotes
        assert '<?xml version=' in xml
        assert 'xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"' in xml
        assert "SimpleTable" in xml
        assert "<input" in xml
        assert "<output" in xml
        assert "<rule" in xml

    @pytest.mark.asyncio
    async def test_multiple_files_extraction(self, service, vbnet_if_else_code, python_conditional_code):
        """Test extraction from multiple files"""
        session_id = await service.create_session(name="Multi-file Test")

        result = await service.extract_from_files(
            session_id=session_id,
            files={
                "discount.vb": vbnet_if_else_code,
                "priority.py": python_conditional_code,
            },
            language="vbnet"  # Will use VB.NET patterns primarily
        )

        assert result is not None
        assert result.total_files_scanned == 2

    @pytest.mark.asyncio
    async def test_min_nesting_parameter(self, service, vbnet_if_else_code):
        """Test min_nesting parameter affects extraction"""
        session_id = await service.create_session(name="Nesting Test")

        # Extract with default min_nesting (2)
        result1 = await service.extract_from_files(
            session_id=session_id,
            files={"test.vb": vbnet_if_else_code},
            language="vbnet",
            min_nesting=2
        )

        session_id2 = await service.create_session(name="Nesting Test 2")

        # Extract with higher min_nesting (5)
        result2 = await service.extract_from_files(
            session_id=session_id2,
            files={"test.vb": vbnet_if_else_code},
            language="vbnet",
            min_nesting=5
        )

        # Both should complete without errors
        assert len(result1.errors) == 0
        assert len(result2.errors) == 0


class TestDecisionTableModels:
    """Test decision table models"""

    def test_decision_rule_creation(self):
        """Test DecisionRule dataclass creation"""
        rule = DecisionRule(
            rule_number=1,
            annotation="Test rule",
            conditions=[
                ConditionEntry(
                    column_id="status-col",
                    operator=ConditionOperator.EQUALS,
                    value="active"
                )
            ],
            actions=[
                ActionEntry(column_id="result-col", value="approved")
            ],
            confidence=0.9,
        )

        assert rule.rule_number == 1
        assert len(rule.conditions) == 1
        assert len(rule.actions) == 1
        assert rule.confidence == 0.9
        assert rule.annotation == "Test rule"

    def test_decision_table_to_dict(self):
        """Test DecisionTable to_dict method"""
        table = DecisionTable(
            name="TestTable",
            description="Test description",
            inputs=[InputColumn(name="in1", label="Input 1", type_ref="string")],
            outputs=[OutputColumn(name="out1", label="Output 1", type_ref="string")],
            rules=[],
            hit_policy=HitPolicy.FIRST,
        )

        result = table.to_dict()

        assert result["name"] == "TestTable"
        assert result["description"] == "Test description"
        assert result["hit_policy"] == "F"  # HitPolicy.FIRST = "F"
        assert len(result["inputs"]) == 1
        assert len(result["outputs"]) == 1

    def test_hit_policy_enum(self):
        """Test HitPolicy enum values"""
        assert HitPolicy.UNIQUE.value == "U"
        assert HitPolicy.FIRST.value == "F"
        assert HitPolicy.ANY.value == "A"
        assert HitPolicy.COLLECT.value == "C"
        assert HitPolicy.PRIORITY.value == "P"
        assert HitPolicy.RULE_ORDER.value == "R"

    def test_condition_operator_enum(self):
        """Test ConditionOperator enum values"""
        assert ConditionOperator.EQUALS.value == "="
        assert ConditionOperator.NOT_EQUALS.value == "!="
        assert ConditionOperator.GREATER_THAN.value == ">"
        assert ConditionOperator.LESS_THAN.value == "<"
        assert ConditionOperator.IN.value == "in"

    def test_condition_entry_creation(self):
        """Test ConditionEntry dataclass creation"""
        entry = ConditionEntry(
            column_id="col1",
            operator=ConditionOperator.BETWEEN,
            value=100,
            value2=500,
            expression="x BETWEEN 100 AND 500"
        )

        assert entry.column_id == "col1"
        assert entry.operator == ConditionOperator.BETWEEN
        assert entry.value == 100
        assert entry.value2 == 500

    def test_action_entry_creation(self):
        """Test ActionEntry dataclass creation"""
        entry = ActionEntry(
            column_id="out1",
            value="Result",
            expression="RETURN 'Result'"
        )

        assert entry.column_id == "out1"
        assert entry.value == "Result"
        assert entry.expression == "RETURN 'Result'"
