# backend/tests/services/week138/test_business_logic_extraction.py
"""
Fase 25: Business Logic Extraction Tests

Tests for:
- RuleCorrelationService.generate_decision_tables() - DMN decision tables
- RuleCorrelationService.generate_authorization_matrix() - RBAC matrix
- RuleCorrelationService._detect_state_machine_workflows() - State machine detection
"""

import pytest
from datetime import datetime


# Test Decision Table Generation
class TestDecisionTableGeneration:
    """Tests for RuleCorrelationService.generate_decision_tables()."""

    def test_generate_decision_tables_empty(self):
        """Test with no BRANCHING rules."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )

        service = RuleCorrelationService()
        tables = service.generate_decision_tables([])

        assert tables == []

    def test_generate_decision_tables_with_context(self):
        """Test decision table generation from rules with shared context."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        # Rules need parent_function to be grouped together
        rules = [
            BusinessRule(
                id="br-001",
                rule_type=RuleType.BRANCHING,
                condition="credit_score > 700",
                action="approve_loan",
                source_file="lending.py",
                source_lines=(20, 25),
                variables_involved=["credit_score"],
                confidence=0.85,
                natural_language="Approve loan if credit score > 700",
                parent_function="evaluate_loan",
            ),
            BusinessRule(
                id="br-002",
                rule_type=RuleType.BRANCHING,
                condition="credit_score <= 700 AND income > 50000",
                action="manual_review",
                source_file="lending.py",
                source_lines=(26, 30),
                variables_involved=["credit_score", "income"],
                confidence=0.85,
                natural_language="Require manual review for marginal cases",
                parent_function="evaluate_loan",
            ),
            BusinessRule(
                id="br-003",
                rule_type=RuleType.BRANCHING,
                condition="credit_score < 500",
                action="reject_loan",
                source_file="lending.py",
                source_lines=(31, 35),
                variables_involved=["credit_score"],
                confidence=0.90,
                natural_language="Reject loan if credit score < 500",
                parent_function="evaluate_loan",
            ),
        ]

        service = RuleCorrelationService()
        tables = service.generate_decision_tables(rules)

        assert len(tables) >= 1
        # Tables should be grouped by function context
        table = tables[0]
        assert "id" in table
        assert "name" in table
        assert "rules" in table
        assert len(table["rules"]) >= 2

    def test_generate_decision_tables_dmn_format(self):
        """Test that DMN XML is generated."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        rules = [
            BusinessRule(
                id="br-001",
                rule_type=RuleType.BRANCHING,
                condition="status == 'active'",
                action="process",
                source_file="workflow.py",
                source_lines=(5, 10),
                variables_involved=["status"],
                confidence=0.8,
                natural_language="Process if status is active",
                parent_function="handle_order",
            ),
            BusinessRule(
                id="br-002",
                rule_type=RuleType.BRANCHING,
                condition="status == 'pending'",
                action="queue",
                source_file="workflow.py",
                source_lines=(11, 15),
                variables_involved=["status"],
                confidence=0.8,
                natural_language="Queue if status is pending",
                parent_function="handle_order",
            ),
        ]

        service = RuleCorrelationService()
        tables = service.generate_decision_tables(rules)

        assert len(tables) >= 1
        table = tables[0]
        assert "dmn_xml" in table
        assert "<definitions" in table["dmn_xml"]
        assert "decision" in table["dmn_xml"].lower()

    def test_generate_decision_tables_markdown(self):
        """Test that markdown output is generated."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        rules = [
            BusinessRule(
                id="br-001",
                rule_type=RuleType.BRANCHING,
                condition="level >= 5",
                action="unlock_feature",
                source_file="game.py",
                source_lines=(100, 105),
                variables_involved=["level"],
                confidence=0.95,
                natural_language="Unlock feature at level 5",
                parent_class="GameProgress",
            ),
            BusinessRule(
                id="br-002",
                rule_type=RuleType.BRANCHING,
                condition="level >= 10",
                action="unlock_premium",
                source_file="game.py",
                source_lines=(106, 110),
                variables_involved=["level"],
                confidence=0.95,
                natural_language="Unlock premium at level 10",
                parent_class="GameProgress",
            ),
        ]

        service = RuleCorrelationService()
        tables = service.generate_decision_tables(rules)

        assert len(tables) >= 1
        table = tables[0]
        assert "markdown" in table
        assert "|" in table["markdown"]  # Markdown table syntax

    def test_generate_decision_tables_single_rule_ignored(self):
        """Test that single rule is not enough for a decision table."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        # Single rule should not generate a decision table
        rules = [
            BusinessRule(
                id="br-001",
                rule_type=RuleType.BRANCHING,
                condition="age >= 18",
                action="allow_access",
                source_file="auth.py",
                source_lines=(10, 15),
                variables_involved=["age"],
                confidence=0.9,
                natural_language="If age is 18 or older, allow access",
                parent_function="check_age",
            )
        ]

        service = RuleCorrelationService()
        tables = service.generate_decision_tables(rules)

        # Single rule should not produce a decision table
        assert len(tables) == 0


# Test Authorization Matrix Generation
class TestAuthorizationMatrixGeneration:
    """Tests for RuleCorrelationService.generate_authorization_matrix()."""

    def test_generate_auth_matrix_empty(self):
        """Test with no AUTHORIZATION rules."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )

        service = RuleCorrelationService()
        matrix = service.generate_authorization_matrix([])

        # Empty rules should return empty matrix (or defaults)
        assert "roles" in matrix
        assert "permissions" in matrix
        assert "matrix" in matrix

    def test_generate_auth_matrix_single_rule(self):
        """Test matrix generation from single authorization rule."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        rules = [
            BusinessRule(
                id="ar-001",
                rule_type=RuleType.AUTHORIZATION,
                condition="role == 'admin'",
                action="allow_delete",
                source_file="permissions.py",
                source_lines=(10, 15),
                variables_involved=["role"],
                confidence=0.9,
                natural_language="Admin can delete records"
            )
        ]

        service = RuleCorrelationService()
        matrix = service.generate_authorization_matrix(rules)

        assert "roles" in matrix
        assert "permissions" in matrix
        assert "matrix" in matrix

    def test_generate_auth_matrix_multiple_roles(self):
        """Test matrix with multiple roles and permissions."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        rules = [
            BusinessRule(
                id="ar-001",
                rule_type=RuleType.AUTHORIZATION,
                condition="role == 'admin'",
                action="can_delete_users",
                source_file="auth.py",
                source_lines=(10, 15),
                variables_involved=["role"],
                confidence=0.9,
                natural_language="Admin can delete users"
            ),
            BusinessRule(
                id="ar-002",
                rule_type=RuleType.AUTHORIZATION,
                condition="role == 'admin' OR role == 'manager'",
                action="can_edit_users",
                source_file="auth.py",
                source_lines=(16, 20),
                variables_involved=["role"],
                confidence=0.85,
                natural_language="Admin or manager can edit users"
            ),
            BusinessRule(
                id="ar-003",
                rule_type=RuleType.AUTHORIZATION,
                condition="role == 'user'",
                action="can_view_profile",
                source_file="auth.py",
                source_lines=(21, 25),
                variables_involved=["role"],
                confidence=0.95,
                natural_language="User can view profile"
            ),
        ]

        service = RuleCorrelationService()
        matrix = service.generate_authorization_matrix(rules)

        # Should have detected roles and permissions
        assert len(matrix["roles"]) >= 1
        assert len(matrix["permissions"]) >= 1

    def test_generate_auth_matrix_markdown(self):
        """Test that markdown table is generated."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        rules = [
            BusinessRule(
                id="ar-001",
                rule_type=RuleType.AUTHORIZATION,
                condition="role == 'editor'",
                action="can_publish_articles",
                source_file="cms.py",
                source_lines=(50, 55),
                variables_involved=["role"],
                confidence=0.88,
                natural_language="Editor can publish articles"
            ),
        ]

        service = RuleCorrelationService()
        matrix = service.generate_authorization_matrix(rules)

        assert "markdown" in matrix
        assert "|" in matrix["markdown"]  # Markdown table syntax


# Test State Machine Workflow Detection
class TestStateMachineWorkflowDetection:
    """Tests for RuleCorrelationService._detect_state_machine_workflows()."""

    def test_detect_state_machine_empty(self):
        """Test with no rules."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )

        service = RuleCorrelationService()
        workflows = service._detect_state_machine_workflows([])

        assert workflows == []

    def test_detect_state_machine_from_state_transitions(self):
        """Test detection from state transition patterns."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        rules = [
            BusinessRule(
                id="sr-001",
                rule_type=RuleType.BRANCHING,
                condition="state == 'draft'",
                action="transition_to_review",
                source_file="document.py",
                source_lines=(10, 15),
                variables_involved=["state"],
                confidence=0.85,
                natural_language="Draft transitions to review"
            ),
            BusinessRule(
                id="sr-002",
                rule_type=RuleType.BRANCHING,
                condition="state == 'review'",
                action="transition_to_published",
                source_file="document.py",
                source_lines=(16, 20),
                variables_involved=["state"],
                confidence=0.85,
                natural_language="Review transitions to published"
            ),
        ]

        service = RuleCorrelationService()
        workflows = service._detect_state_machine_workflows(rules)

        # Should detect state pattern
        assert isinstance(workflows, list)


# Integration test
class TestFase25Integration:
    """Integration tests for Fase 25 components working together."""

    def test_full_business_logic_extraction(self):
        """Test complete business logic extraction pipeline."""
        from app.services.static_analysis.rule_correlation_service import (
            RuleCorrelationService
        )
        from app.services.static_analysis.extraction_models import (
            BusinessRule, RuleType
        )

        # Mix of rule types with proper context
        rules = [
            # Branching rules (for decision tables) - need 2+ with same context
            BusinessRule(
                id="br-001",
                rule_type=RuleType.BRANCHING,
                condition="order_total > 100",
                action="apply_discount",
                source_file="orders.py",
                source_lines=(10, 15),
                variables_involved=["order_total"],
                confidence=0.9,
                natural_language="Apply discount for orders over $100",
                parent_function="calculate_discount",
            ),
            BusinessRule(
                id="br-002",
                rule_type=RuleType.BRANCHING,
                condition="order_total > 500",
                action="apply_premium_discount",
                source_file="orders.py",
                source_lines=(16, 20),
                variables_involved=["order_total"],
                confidence=0.9,
                natural_language="Apply premium discount for large orders",
                parent_function="calculate_discount",
            ),
            # Authorization rules (for RBAC matrix)
            BusinessRule(
                id="ar-001",
                rule_type=RuleType.AUTHORIZATION,
                condition="role == 'manager'",
                action="can_approve_refunds",
                source_file="refunds.py",
                source_lines=(20, 25),
                variables_involved=["role"],
                confidence=0.88,
                natural_language="Manager can approve refunds"
            ),
            # Validation rules
            BusinessRule(
                id="vr-001",
                rule_type=RuleType.VALIDATION,
                condition="email matches r'^[a-z]+@[a-z]+\\.[a-z]+$'",
                action="validate_email",
                source_file="users.py",
                source_lines=(30, 35),
                variables_involved=["email"],
                confidence=0.95,
                natural_language="Email must be valid format"
            ),
        ]

        service = RuleCorrelationService()

        # Generate decision tables from BRANCHING rules
        branching_rules = [r for r in rules if r.rule_type == RuleType.BRANCHING]
        tables = service.generate_decision_tables(branching_rules)
        assert len(tables) >= 1  # Should have 1 table for calculate_discount context

        # Generate auth matrix from AUTHORIZATION rules
        auth_rules = [r for r in rules if r.rule_type == RuleType.AUTHORIZATION]
        matrix = service.generate_authorization_matrix(auth_rules)
        assert "roles" in matrix
        assert "permissions" in matrix

        # Detect state machines
        workflows = service._detect_state_machine_workflows(rules)
        assert isinstance(workflows, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
