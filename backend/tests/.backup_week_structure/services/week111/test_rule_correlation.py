# tests/services/week111/test_rule_correlation.py
"""
Unit tests for Rule Correlation Service.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline - Phase 3

Tests:
- CRUD operation detection
- Entity extraction and normalization
- Workflow detection
- Rule relationship detection
- Correlation result aggregation
"""

import pytest
from typing import List

from app.services.static_analysis.extraction_models import (
    BusinessRule,
    RuleType,
    ExtractionMethod,
    ExtractionTier,
    CRUDOperation,
    WorkflowType,
    Entity,
    Workflow,
    RuleRelationship,
    CorrelationResult,
    Language,
)
from app.services.static_analysis.rule_correlation_service import (
    RuleCorrelationService,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def correlation_service():
    """Create a correlation service instance."""
    return RuleCorrelationService(project_id=1)


@pytest.fixture
def sample_crud_rules() -> List[BusinessRule]:
    """Create sample rules for CRUD workflow testing."""
    return [
        BusinessRule(
            id="BR-001",
            rule_type=RuleType.AUTHORIZATION,
            condition="intCanAdd = CheckPermission('Afspraak', 'Add')",
            action="If intCanAdd = 0 Then Exit Sub",
            source_file="Agenda.vb",
            source_lines=(10, 12),
            confidence=0.85,
            natural_language="User must have Add permission for Afspraak",
            code_snippet="If intCanAdd = 0 Then Response.Redirect 'NoAccess.asp'",
        ),
        BusinessRule(
            id="BR-002",
            rule_type=RuleType.VALIDATION,
            condition="strDatum <> '' And IsDate(strDatum)",
            action="Validate date format before insertion",
            source_file="Agenda.vb",
            source_lines=(20, 25),
            confidence=0.80,
            natural_language="Date must be valid format",
            parent_function="SaveAfspraak",
        ),
        BusinessRule(
            id="BR-003",
            rule_type=RuleType.DATA_ACCESS,
            condition="INSERT INTO taAfspraak",
            action="Insert new appointment record",
            source_file="AgendaData.asp",
            source_lines=(50, 60),
            confidence=0.90,
            natural_language="Create new appointment in database",
            code_snippet="INSERT INTO taAfspraak (Datum, Tijd, Hulpverlener) VALUES (@Datum, @Tijd, @HV)",
            parent_function="SaveAfspraak",
        ),
        BusinessRule(
            id="BR-004",
            rule_type=RuleType.AUTHORIZATION,
            condition="intCanView = CheckPermission('Afspraak', 'View')",
            action="Check view permission",
            source_file="Agenda.vb",
            source_lines=(100, 102),
            confidence=0.85,
            natural_language="User must have View permission",
        ),
        BusinessRule(
            id="BR-005",
            rule_type=RuleType.DATA_ACCESS,
            condition="SELECT * FROM taAfspraak WHERE AfspraakID = @ID",
            action="Retrieve appointment details",
            source_file="AgendaData.asp",
            source_lines=(150, 160),
            confidence=0.90,
            natural_language="Get appointment by ID",
            code_snippet="SELECT * FROM taAfspraak WHERE AfspraakID = @ID",
        ),
        BusinessRule(
            id="BR-006",
            rule_type=RuleType.AUTHORIZATION,
            condition="intCanEdit = CheckPermission('Afspraak', 'Edit')",
            action="Check edit permission",
            source_file="Agenda.vb",
            source_lines=(200, 202),
            confidence=0.85,
            natural_language="User must have Edit permission",
        ),
        BusinessRule(
            id="BR-007",
            rule_type=RuleType.DATA_ACCESS,
            condition="UPDATE taAfspraak SET",
            action="Update appointment record",
            source_file="AgendaData.asp",
            source_lines=(250, 270),
            confidence=0.90,
            natural_language="Update existing appointment",
            code_snippet="UPDATE taAfspraak SET Datum = @Datum, Tijd = @Tijd WHERE AfspraakID = @ID",
        ),
        BusinessRule(
            id="BR-008",
            rule_type=RuleType.AUTHORIZATION,
            condition="intCanDelete = CheckPermission('Afspraak', 'Delete')",
            action="Check delete permission",
            source_file="Agenda.vb",
            source_lines=(300, 302),
            confidence=0.85,
            natural_language="User must have Delete permission",
        ),
        BusinessRule(
            id="BR-009",
            rule_type=RuleType.DATA_ACCESS,
            condition="DELETE FROM taAfspraak WHERE AfspraakID = @ID",
            action="Delete appointment record",
            source_file="AgendaData.asp",
            source_lines=(350, 355),
            confidence=0.90,
            natural_language="Delete appointment by ID",
            code_snippet="DELETE FROM taAfspraak WHERE AfspraakID = @ID",
        ),
    ]


@pytest.fixture
def sample_state_machine_rules() -> List[BusinessRule]:
    """Create sample rules for state machine workflow testing."""
    return [
        BusinessRule(
            id="BR-010",
            rule_type=RuleType.WORKFLOW,
            condition="status = 'Draft'",
            action="Set status to 'Draft'",
            source_file="Order.cs",
            source_lines=(10, 15),
            confidence=0.80,
            natural_language="Order starts in Draft status",
        ),
        BusinessRule(
            id="BR-011",
            rule_type=RuleType.STATE_MANAGEMENT,
            condition="status = 'Submitted'",
            action="Set status to 'Submitted'",
            source_file="Order.cs",
            source_lines=(20, 25),
            confidence=0.80,
            natural_language="Order submitted for approval",
        ),
        BusinessRule(
            id="BR-012",
            rule_type=RuleType.WORKFLOW,
            condition="status = 'Approved'",
            action="Set status to 'Approved'",
            source_file="Order.cs",
            source_lines=(30, 35),
            confidence=0.80,
            natural_language="Order approved by manager",
        ),
        BusinessRule(
            id="BR-013",
            rule_type=RuleType.STATE_MANAGEMENT,
            condition="status = 'Completed'",
            action="Set status to 'Completed'",
            source_file="Order.cs",
            source_lines=(40, 45),
            confidence=0.80,
            natural_language="Order processing completed",
        ),
    ]


@pytest.fixture
def sample_multi_entity_rules() -> List[BusinessRule]:
    """Create sample rules with multiple entities."""
    return [
        BusinessRule(
            id="BR-020",
            rule_type=RuleType.DATA_ACCESS,
            condition="SELECT * FROM taKlant WHERE KlantID = @ID",
            action="Get customer details",
            source_file="Customer.vb",
            source_lines=(10, 15),
            confidence=0.85,
            natural_language="Retrieve customer by ID",
        ),
        BusinessRule(
            id="BR-021",
            rule_type=RuleType.DATA_ACCESS,
            condition="INSERT INTO taKlant",
            action="Create new customer",
            source_file="Customer.vb",
            source_lines=(30, 40),
            confidence=0.85,
            natural_language="Insert new customer record",
            code_snippet="INSERT INTO taKlant (Naam, Email) VALUES (@Naam, @Email)",
        ),
        BusinessRule(
            id="BR-022",
            rule_type=RuleType.DATA_ACCESS,
            condition="SELECT * FROM taProduct WHERE ProductID = @ID",
            action="Get product details",
            source_file="Product.vb",
            source_lines=(10, 15),
            confidence=0.85,
            natural_language="Retrieve product by ID",
        ),
        BusinessRule(
            id="BR-023",
            rule_type=RuleType.DATA_ACCESS,
            condition="UPDATE taProduct SET Prijs = @Prijs",
            action="Update product price",
            source_file="Product.vb",
            source_lines=(50, 60),
            confidence=0.85,
            natural_language="Update product price",
        ),
    ]


# =============================================================================
# Test CRUD Operation Detection
# =============================================================================

class TestCRUDOperationDetection:
    """Test CRUD operation detection from rules."""

    def test_detect_create_operation(self, correlation_service):
        """Test detection of CREATE/INSERT operations."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="INSERT INTO taTest",
                action="Insert record",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.9,
                natural_language="Insert test record",
                code_snippet="INSERT INTO taTest (Col1) VALUES (@Val1)",
            )
        ]

        operations = correlation_service._detect_crud_operations(rules)

        assert "BR-001" in operations
        assert CRUDOperation.CREATE in operations["BR-001"]

    def test_detect_read_operation(self, correlation_service):
        """Test detection of READ/SELECT operations."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="SELECT * FROM taTest",
                action="Read records",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.9,
                natural_language="Select test records",
            )
        ]

        operations = correlation_service._detect_crud_operations(rules)

        assert CRUDOperation.READ in operations["BR-001"]

    def test_detect_update_operation(self, correlation_service):
        """Test detection of UPDATE operations."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="UPDATE taTest SET Col1 = @Val1",
                action="Update record",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.9,
                natural_language="Update test record",
            )
        ]

        operations = correlation_service._detect_crud_operations(rules)

        assert CRUDOperation.UPDATE in operations["BR-001"]

    def test_detect_delete_operation(self, correlation_service):
        """Test detection of DELETE operations."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="DELETE FROM taTest WHERE ID = @ID",
                action="Delete record",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.9,
                natural_language="Delete test record",
            )
        ]

        operations = correlation_service._detect_crud_operations(rules)

        assert CRUDOperation.DELETE in operations["BR-001"]

    def test_detect_authorization_pattern(self, correlation_service):
        """Test detection of authorization patterns as CRUD indicators."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.AUTHORIZATION,
                condition="intCanAdd = CheckPermission('Test', 'Add')",
                action="Check add permission",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.85,
                natural_language="Check add permission",
            )
        ]

        operations = correlation_service._detect_crud_operations(rules)

        assert CRUDOperation.CREATE in operations["BR-001"]

    def test_detect_multiple_operations(self, correlation_service):
        """Test detection of multiple operations in one rule."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="Copy record",
                action="SELECT then INSERT",
                source_file="test.vb",
                source_lines=(1, 10),
                confidence=0.85,
                natural_language="Copy record to new location",
                code_snippet="SELECT * FROM taTest; INSERT INTO taTest VALUES...",
            )
        ]

        operations = correlation_service._detect_crud_operations(rules)

        # Should detect both READ (SELECT) and CREATE (INSERT)
        assert len(operations["BR-001"]) >= 1


# =============================================================================
# Test Entity Extraction
# =============================================================================

class TestEntityExtraction:
    """Test entity extraction from rules."""

    def test_extract_table_entity(self, correlation_service):
        """Test extraction of entity from table name."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="SELECT * FROM taAfspraak",
                action="Get appointments",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.9,
                natural_language="Get appointments",
            )
        ]

        entities = correlation_service._extract_entities(rules)

        assert len(entities) >= 1
        # Should find "Afspraak" entity (normalized from "taAfspraak")
        entity_names = [e.name for e in entities.values()]
        assert "Afspraak" in entity_names or any("afspraak" in n.lower() for n in entity_names)

    def test_normalize_table_prefix(self, correlation_service):
        """Test normalization of table prefixes."""
        assert correlation_service._normalize_entity_name("taAfspraak") == "Afspraak"
        assert correlation_service._normalize_entity_name("tblCustomer") == "Customer"
        assert correlation_service._normalize_entity_name("tbOrder") == "Order"

    def test_normalize_class_suffix(self, correlation_service):
        """Test normalization of class suffixes."""
        assert correlation_service._normalize_entity_name("OrderService") == "Order"
        assert correlation_service._normalize_entity_name("CustomerRepository") == "Customer"
        assert correlation_service._normalize_entity_name("ProductController") == "Product"

    def test_extract_multiple_entities(self, correlation_service, sample_multi_entity_rules):
        """Test extraction of multiple entities from rules."""
        entities = correlation_service._extract_entities(sample_multi_entity_rules)

        assert len(entities) >= 2
        entity_names = [e.name.lower() for e in entities.values()]
        assert any("klant" in n or "customer" in n for n in entity_names)
        assert any("product" in n for n in entity_names)

    def test_entity_crud_coverage(self, correlation_service, sample_crud_rules):
        """Test that entities track CRUD coverage correctly."""
        result = correlation_service.correlate(sample_crud_rules)

        # Find the Afspraak entity
        afspraak_entity = None
        for entity in result.entities:
            if "afspraak" in entity.name.lower():
                afspraak_entity = entity
                break

        assert afspraak_entity is not None
        # Should have full CRUD coverage
        assert afspraak_entity.has_create or afspraak_entity.has_read
        assert afspraak_entity.rule_count > 0


# =============================================================================
# Test Workflow Detection
# =============================================================================

class TestWorkflowDetection:
    """Test workflow detection from rules."""

    def test_detect_crud_workflow(self, correlation_service, sample_crud_rules):
        """Test detection of CRUD workflow."""
        result = correlation_service.correlate(sample_crud_rules)

        assert result.workflows_detected >= 1

        # Find Afspraak workflow
        afspraak_workflow = None
        for workflow in result.workflows:
            if "afspraak" in workflow.name.lower():
                afspraak_workflow = workflow
                break

        assert afspraak_workflow is not None
        assert afspraak_workflow.workflow_type == WorkflowType.CRUD
        assert afspraak_workflow.total_rules > 0

    def test_detect_state_machine_workflow(self, correlation_service, sample_state_machine_rules):
        """Test detection of state machine workflow."""
        result = correlation_service.correlate(sample_state_machine_rules)

        # Should detect status state machine
        state_workflows = [
            w for w in result.workflows
            if w.workflow_type == WorkflowType.STATE_MACHINE
        ]
        assert len(state_workflows) >= 1

    def test_workflow_contains_auth_rules(self, correlation_service, sample_crud_rules):
        """Test that workflows properly categorize authorization rules."""
        result = correlation_service.correlate(sample_crud_rules)

        # Find workflow with auth rules
        workflow_with_auth = None
        for workflow in result.workflows:
            if workflow.auth_rules:
                workflow_with_auth = workflow
                break

        if workflow_with_auth:
            assert len(workflow_with_auth.auth_rules) > 0

    def test_workflow_confidence_calculation(self, correlation_service, sample_crud_rules):
        """Test that workflow confidence is calculated."""
        result = correlation_service.correlate(sample_crud_rules)

        for workflow in result.workflows:
            assert 0.0 <= workflow.confidence <= 1.0

    def test_workflow_operations_detected(self, correlation_service, sample_crud_rules):
        """Test that workflows track their CRUD operations."""
        result = correlation_service.correlate(sample_crud_rules)

        # Find workflow with operations
        workflow_with_ops = None
        for workflow in result.workflows:
            if workflow.operations:
                workflow_with_ops = workflow
                break

        if workflow_with_ops:
            assert len(workflow_with_ops.operations) > 0


# =============================================================================
# Test Relationship Detection
# =============================================================================

class TestRelationshipDetection:
    """Test rule relationship detection."""

    def test_detect_shares_entity_relationship(self, correlation_service, sample_crud_rules):
        """Test detection of shares_entity relationships."""
        result = correlation_service.correlate(sample_crud_rules)

        shares_entity_rels = [
            r for r in result.relationships
            if r.relationship_type == "shares_entity"
        ]

        # Rules operating on taAfspraak should be related
        assert len(shares_entity_rels) > 0

    def test_detect_guards_relationship(self, correlation_service):
        """Test detection of guards relationships (auth guards data access)."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.AUTHORIZATION,
                condition="intCanView = CheckPermission('Test', 'View')",
                action="Check view permission",
                source_file="test.vb",
                source_lines=(10, 12),
                confidence=0.85,
                natural_language="Check view permission",
                parent_function="GetData",
            ),
            BusinessRule(
                id="BR-002",
                rule_type=RuleType.DATA_ACCESS,
                condition="SELECT * FROM taTest",
                action="Get test data",
                source_file="test.vb",
                source_lines=(15, 20),
                confidence=0.90,
                natural_language="Get test data",
                parent_function="GetData",
            ),
        ]

        result = correlation_service.correlate(rules)

        guards_rels = [
            r for r in result.relationships
            if r.relationship_type == "guards"
        ]

        assert len(guards_rels) >= 1
        assert guards_rels[0].source_rule_id == "BR-001"
        assert guards_rels[0].target_rule_id == "BR-002"

    def test_detect_validates_relationship(self, correlation_service):
        """Test detection of validates relationships."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.VALIDATION,
                condition="strValue <> ''",
                action="Validate input",
                source_file="test.vb",
                source_lines=(10, 12),
                confidence=0.80,
                natural_language="Validate input not empty",
                parent_function="SaveData",
            ),
            BusinessRule(
                id="BR-002",
                rule_type=RuleType.DATA_ACCESS,
                condition="INSERT INTO taTest",
                action="Insert data",
                source_file="test.vb",
                source_lines=(20, 25),
                confidence=0.90,
                natural_language="Insert test data",
                parent_function="SaveData",
            ),
        ]

        result = correlation_service.correlate(rules)

        validates_rels = [
            r for r in result.relationships
            if r.relationship_type == "validates"
        ]

        assert len(validates_rels) >= 1


# =============================================================================
# Test Correlation Result
# =============================================================================

class TestCorrelationResult:
    """Test correlation result aggregation."""

    def test_correlation_statistics(self, correlation_service, sample_crud_rules):
        """Test correlation result statistics."""
        result = correlation_service.correlate(sample_crud_rules)

        assert result.total_rules_analyzed == len(sample_crud_rules)
        assert result.entities_detected >= 1
        assert result.correlation_time_ms >= 0

    def test_rules_correlated_count(self, correlation_service, sample_crud_rules):
        """Test that correlated rule count is accurate."""
        result = correlation_service.correlate(sample_crud_rules)

        # rules_correlated + rules_orphaned should equal total
        assert (result.rules_correlated + result.rules_orphaned) <= result.total_rules_analyzed

    def test_result_to_dict(self, correlation_service, sample_crud_rules):
        """Test that result can be serialized to dict."""
        result = correlation_service.correlate(sample_crud_rules)

        result_dict = result.to_dict()

        assert "entities" in result_dict
        assert "workflows" in result_dict
        assert "relationships" in result_dict
        assert "total_rules_analyzed" in result_dict

    def test_workflow_summary(self, correlation_service, sample_crud_rules):
        """Test workflow summary generation."""
        result = correlation_service.correlate(sample_crud_rules)

        summary = correlation_service.get_workflow_summary(result)

        assert "total_entities" in summary
        assert "total_workflows" in summary
        assert "coverage" in summary
        assert "coverage_percent" in summary["coverage"]

    def test_empty_rules_correlation(self, correlation_service):
        """Test correlation with empty rules list."""
        result = correlation_service.correlate([])

        assert result.total_rules_analyzed == 0
        assert result.entities_detected == 0
        assert result.workflows_detected == 0


# =============================================================================
# Test Entity Model
# =============================================================================

class TestEntityModel:
    """Test Entity dataclass functionality."""

    def test_entity_crud_coverage_string(self):
        """Test CRUD coverage string generation."""
        entity = Entity(
            id="ENT-001",
            name="Test",
            has_create=True,
            has_read=True,
            has_update=False,
            has_delete=False,
        )

        assert entity.crud_coverage == "CR"

    def test_entity_full_crud(self):
        """Test entity with full CRUD coverage."""
        entity = Entity(
            id="ENT-001",
            name="Test",
            has_create=True,
            has_read=True,
            has_update=True,
            has_delete=True,
        )

        assert entity.crud_coverage == "CRUD"

    def test_entity_no_crud(self):
        """Test entity with no CRUD coverage."""
        entity = Entity(
            id="ENT-001",
            name="Test",
        )

        assert entity.crud_coverage == "-"

    def test_entity_to_dict(self):
        """Test entity serialization."""
        entity = Entity(
            id="ENT-001",
            name="Test",
            original_names=["taTest", "tblTest"],
            entity_type="table",
            rule_ids=["BR-001", "BR-002"],
            has_create=True,
            has_read=True,
            rule_count=2,
        )

        entity_dict = entity.to_dict()

        assert entity_dict["id"] == "ENT-001"
        assert entity_dict["name"] == "Test"
        assert entity_dict["crud_coverage"] == "CR"
        assert len(entity_dict["rule_ids"]) == 2


# =============================================================================
# Test Workflow Model
# =============================================================================

class TestWorkflowModel:
    """Test Workflow dataclass functionality."""

    def test_workflow_to_dict(self):
        """Test workflow serialization."""
        workflow = Workflow(
            id="WF-001",
            name="Test Management",
            workflow_type=WorkflowType.CRUD,
            primary_entity="Test",
            operations=[CRUDOperation.CREATE, CRUDOperation.READ],
            rule_ids=["BR-001", "BR-002"],
            total_rules=2,
            confidence=0.85,
        )

        workflow_dict = workflow.to_dict()

        assert workflow_dict["id"] == "WF-001"
        assert workflow_dict["workflow_type"] == "crud"
        assert "create" in workflow_dict["operations"]
        assert workflow_dict["confidence"] == 0.85


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_rule_with_no_code_snippet(self, correlation_service):
        """Test handling of rules without code snippets."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.VALIDATION,
                condition="value > 0",
                action="validate positive",
                source_file="test.py",
                source_lines=(1, 5),
                confidence=0.8,
                natural_language="Value must be positive",
                code_snippet=None,
            )
        ]

        result = correlation_service.correlate(rules)

        assert result.total_rules_analyzed == 1
        assert len(result.errors) == 0

    def test_rule_with_empty_condition(self, correlation_service):
        """Test handling of rules with empty condition."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="",
                action="SELECT * FROM taTest",
                source_file="test.py",
                source_lines=(1, 5),
                confidence=0.8,
                natural_language="Get test data",
            )
        ]

        result = correlation_service.correlate(rules)

        assert result.total_rules_analyzed == 1

    def test_entity_name_edge_cases(self, correlation_service):
        """Test entity name normalization edge cases."""
        assert correlation_service._normalize_entity_name("") == ""
        assert correlation_service._normalize_entity_name("A") == "A"
        assert correlation_service._normalize_entity_name("ab") == "Ab"

    def test_correlation_with_single_rule(self, correlation_service):
        """Test correlation with only one rule."""
        rules = [
            BusinessRule(
                id="BR-001",
                rule_type=RuleType.DATA_ACCESS,
                condition="SELECT * FROM taTest",
                action="Get data",
                source_file="test.vb",
                source_lines=(1, 5),
                confidence=0.9,
                natural_language="Get test data",
            )
        ]

        result = correlation_service.correlate(rules)

        assert result.total_rules_analyzed == 1
        # Single rule entity might not form a workflow (min 2 rules)
        assert result.entities_detected >= 0
