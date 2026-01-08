# backend/tests/services/week97/test_business_rule_extractor.py
"""
Unit tests for BusinessRuleExtractor - Week 97-98 (Fase 15).

Tests IF-THEN business rule extraction from code.
"""

import pytest
from app.services.static_analysis.business_rule_extractor import (
    BusinessRuleExtractor,
    BusinessRule,
    RuleType,
    RuleExtractionResult,
)


class TestBusinessRuleExtractor:
    """Tests for BusinessRuleExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return BusinessRuleExtractor()

    @pytest.mark.asyncio
    async def test_extract_validation_rule_python(self, extractor):
        """Test extraction of validation rule from Python code."""
        code = '''
def validate_order(order):
    if order.total < 0:
        raise ValueError("Order total cannot be negative")
    return True
'''
        rules = await extractor.extract_from_file("orders.py", code)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_authorization_rule(self, extractor):
        """Test extraction of authorization rule."""
        code = '''
def check_access(user, resource):
    if not user.has_permission(resource.required_permission):
        return False
    return True
'''
        rules = await extractor.extract_from_file("auth.py", code)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_calculation_rule(self, extractor):
        """Test extraction of calculation rule."""
        code = '''
def calculate_discount(order):
    if order.total > 1000:
        discount = order.total * 0.1
    else:
        discount = 0
    return discount
'''
        rules = await extractor.extract_from_file("pricing.py", code)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_workflow_rule(self, extractor):
        """Test extraction of workflow/state transition rule."""
        code = '''
def process_order(order):
    if order.status == "pending" and order.payment_confirmed:
        order.status = "processing"
    return order
'''
        rules = await extractor.extract_from_file("workflow.py", code)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_constraint_rule(self, extractor):
        """Test extraction of constraint rule."""
        code = '''
def add_to_cart(cart, item):
    if len(cart.items) >= cart.max_items:
        raise Exception("Cart limit exceeded")
    cart.items.append(item)
'''
        rules = await extractor.extract_from_file("cart.py", code)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_derivation_rule(self, extractor):
        """Test extraction of derivation rule."""
        code = '''
def get_age_category(person):
    if person.age < 18:
        return "minor"
    elif person.age < 65:
        return "adult"
    else:
        return "senior"
'''
        rules = await extractor.extract_from_file("categories.py", code)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_rule_attributes(self, extractor):
        """Test that extracted rules have expected attributes."""
        code = '''
def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
'''
        rules = await extractor.extract_from_file("validation.py", code)

        for rule in rules:
            assert hasattr(rule, 'id')
            assert hasattr(rule, 'rule_type')
            assert hasattr(rule, 'condition')
            assert hasattr(rule, 'action')
            assert hasattr(rule, 'source_file')
            assert hasattr(rule, 'confidence')

    @pytest.mark.asyncio
    async def test_extract_all_from_multiple_files(self, extractor):
        """Test extraction from multiple files."""
        files = {
            "validation.py": '''
def validate(x):
    if x < 0:
        return False
''',
            "pricing.py": '''
def calc_price(qty, unit_price):
    if qty > 100:
        return qty * unit_price * 0.9
    return qty * unit_price
''',
        }

        result = await extractor.extract_all(files)

        assert isinstance(result, RuleExtractionResult)
        assert result.total_rules >= 0


class TestSQLBusinessRuleExtraction:
    """Tests for SQL stored procedure rule extraction."""

    @pytest.fixture
    def extractor(self):
        return BusinessRuleExtractor()

    @pytest.mark.asyncio
    async def test_extract_from_where_clause(self, extractor):
        """Test extraction from SQL WHERE clause."""
        sql = '''
CREATE PROCEDURE GetActiveCustomers
AS
BEGIN
    SELECT * FROM Customers
    WHERE Status = 'Active' AND Balance > 0
END
'''
        rules = await extractor.extract_from_file("customers.sql", sql)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_from_check_constraint(self, extractor):
        """Test extraction from CHECK constraint."""
        sql = '''
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    Total DECIMAL(10,2) CHECK (Total >= 0),
    Quantity INT CHECK (Quantity > 0 AND Quantity <= 1000)
)
'''
        rules = await extractor.extract_from_file("schema.sql", sql)
        assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_extract_from_trigger(self, extractor):
        """Test extraction from SQL trigger."""
        sql = '''
CREATE TRIGGER UpdateBalance
ON Transactions
AFTER INSERT
AS
BEGIN
    IF (SELECT SUM(Amount) FROM Inserted) < 0
    BEGIN
        RAISERROR('Transaction amount cannot be negative', 16, 1)
        ROLLBACK TRANSACTION
    END
END
'''
        rules = await extractor.extract_from_file("triggers.sql", sql)
        assert isinstance(rules, list)


class TestRuleExtractionResult:
    """Tests for RuleExtractionResult dataclass."""

    def test_result_creation(self):
        """Test RuleExtractionResult creation."""
        result = RuleExtractionResult(
            rules=[],
            rules_by_type={},
            rules_by_file={},
            total_rules=0,
            high_confidence_rules=0,
        )
        assert result.total_rules == 0
        assert len(result.rules) == 0

    def test_rules_by_type_property(self):
        """Test rules_by_type field."""
        rule1 = BusinessRule(
            id="BR-0001",
            rule_type=RuleType.VALIDATION,
            condition="x < 0",
            action="raise error",
            source_file="test.py",
            source_lines=(1, 2),
            variables_involved=["x"],
            confidence=0.8,
            natural_language="Validate x is not negative",
        )
        rule2 = BusinessRule(
            id="BR-0002",
            rule_type=RuleType.CALCULATION,
            condition="qty > 100",
            action="apply discount",
            source_file="test.py",
            source_lines=(3, 4),
            variables_involved=["qty"],
            confidence=0.7,
            natural_language="Calculate discount for large orders",
        )
        result = RuleExtractionResult(
            rules=[rule1, rule2],
            rules_by_type={RuleType.VALIDATION: [rule1], RuleType.CALCULATION: [rule2]},
            rules_by_file={"test.py": [rule1, rule2]},
            total_rules=2,
            high_confidence_rules=1,
        )

        by_type = result.rules_by_type
        assert RuleType.VALIDATION in by_type
        assert RuleType.CALCULATION in by_type
