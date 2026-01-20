"""
Unit tests for UIWrapperFieldMapperService (B9 - Fase 24)

Tests field mapping configuration, transformations (Dutch locale support),
validations, and export functionality.
"""

import pytest
import json
from datetime import datetime
from uuid import UUID, uuid4

from app.services.ui_wrapper_field_mapper_service import (
    UIWrapperFieldMapperService,
    TransformationType,
    ValidationType,
    FieldType,
    ValidationRule,
    FieldTransformation,
    LegacyFieldDefinition,
    NewFieldDefinition,
    FieldMapping,
    MappingConfiguration,
    ValidationResult,
    TransformationResult,
    MappingPreview,
)


# ============================================================================
# Dataclass Tests
# ============================================================================

class TestValidationRule:
    """Tests for ValidationRule dataclass."""

    def test_validation_rule_creation(self):
        """Test creating a validation rule."""
        rule = ValidationRule(
            type=ValidationType.REQUIRED,
            message="This field is mandatory"
        )
        assert rule.type == ValidationType.REQUIRED
        assert rule.message == "This field is mandatory"

    def test_validation_rule_with_value(self):
        """Test validation rule with value."""
        rule = ValidationRule(
            type=ValidationType.MIN_LENGTH,
            value=5,
            message="Minimum 5 characters"
        )
        data = rule.to_dict()
        assert data["type"] == "min_length"
        assert data["value"] == 5

    def test_validation_rule_from_dict(self):
        """Test deserializing validation rule."""
        data = {"type": "max_length", "value": 100, "message": "Too long"}
        rule = ValidationRule.from_dict(data)
        assert rule.type == ValidationType.MAX_LENGTH
        assert rule.value == 100


class TestFieldTransformation:
    """Tests for FieldTransformation dataclass."""

    def test_transformation_creation(self):
        """Test creating a transformation."""
        transform = FieldTransformation(type=TransformationType.UPPERCASE)
        assert transform.type == TransformationType.UPPERCASE

    def test_transformation_with_custom(self):
        """Test custom transformation."""
        transform = FieldTransformation(
            type=TransformationType.CUSTOM,
            custom_pattern=r"\s+",
            custom_replacement="-"
        )
        data = transform.to_dict()
        assert data["custom_pattern"] == r"\s+"

    def test_transformation_from_dict(self):
        """Test deserializing transformation."""
        data = {
            "type": "date_nl",
            "format_string": "%d-%m-%Y"
        }
        transform = FieldTransformation.from_dict(data)
        assert transform.type == TransformationType.DATE_NL


class TestLegacyFieldDefinition:
    """Tests for LegacyFieldDefinition dataclass."""

    def test_legacy_field_definition(self):
        """Test legacy field definition."""
        field_def = LegacyFieldDefinition(
            id="user_name",
            name="Gebruikersnaam",
            selector="#txtUserName",
            field_type=FieldType.STRING,
            description="Legacy username field",
            sample_values=["jan_jansen", "piet_pietersen"]
        )
        data = field_def.to_dict()
        assert data["id"] == "user_name"
        assert data["selector"] == "#txtUserName"
        assert len(data["sample_values"]) == 2

    def test_legacy_field_from_dict(self):
        """Test deserializing legacy field."""
        data = {
            "id": "amount",
            "name": "Bedrag",
            "selector": ".amount-field",
            "field_type": "number"
        }
        field_def = LegacyFieldDefinition.from_dict(data)
        assert field_def.field_type == FieldType.NUMBER


class TestNewFieldDefinition:
    """Tests for NewFieldDefinition dataclass."""

    def test_new_field_definition(self):
        """Test new field definition."""
        field_def = NewFieldDefinition(
            id="username",
            name="Username",
            path="user.profile.username",
            field_type=FieldType.STRING,
            default_value=""
        )
        data = field_def.to_dict()
        assert data["path"] == "user.profile.username"

    def test_new_field_from_dict(self):
        """Test deserializing new field."""
        data = {
            "id": "price",
            "name": "Price",
            "path": "product.price",
            "field_type": "number",
            "default_value": 0.0
        }
        field_def = NewFieldDefinition.from_dict(data)
        assert field_def.default_value == 0.0


class TestFieldMapping:
    """Tests for FieldMapping dataclass."""

    def test_field_mapping_simple(self):
        """Test simple field mapping."""
        mapping = FieldMapping(
            id=uuid4(),
            legacy_fields=["old_field"],
            new_field="new_field",
            enabled=True
        )
        data = mapping.to_dict()
        assert len(data["legacy_fields"]) == 1
        assert data["enabled"]

    def test_field_mapping_composite(self):
        """Test composite field mapping."""
        mapping = FieldMapping(
            id=uuid4(),
            legacy_fields=["first_name", "last_name"],
            new_field="full_name",
            composite_template="{first_name} {last_name}",
            bidirectional=False
        )
        data = mapping.to_dict()
        assert data["composite_template"] == "{first_name} {last_name}"

    def test_field_mapping_from_dict(self):
        """Test deserializing field mapping."""
        data = {
            "id": str(uuid4()),
            "legacy_fields": ["f1", "f2"],
            "new_field": "combined",
            "transformations": [{"type": "trim"}],
            "validations": [{"type": "required"}],
            "bidirectional": True
        }
        mapping = FieldMapping.from_dict(data)
        assert mapping.bidirectional
        assert len(mapping.transformations) == 1


# ============================================================================
# UIWrapperFieldMapperService Tests
# ============================================================================

class TestUIWrapperFieldMapperService:
    """Tests for UIWrapperFieldMapperService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return UIWrapperFieldMapperService()

    # =========================================================================
    # Configuration Management Tests
    # =========================================================================

    def test_create_configuration(self, service):
        """Test creating a mapping configuration."""
        config = service.create_configuration(
            name="Legacy CRM Mapping",
            description="Field mapping for legacy CRM system",
            legacy_system="SAP CRM v4.5"
        )

        assert config.name == "Legacy CRM Mapping"
        assert config.legacy_system == "SAP CRM v4.5"
        assert isinstance(config.id, UUID)

    def test_get_configuration(self, service):
        """Test retrieving a configuration."""
        config = service.create_configuration("Test", "Test config", "Legacy")

        retrieved = service.get_configuration(config.id)
        assert retrieved == config

        # Test with string ID
        retrieved_str = service.get_configuration(str(config.id))
        assert retrieved_str == config

    def test_list_configurations(self, service):
        """Test listing configurations."""
        service.create_configuration("Config1", "Desc1", "System1")
        service.create_configuration("Config2", "Desc2", "System2")

        configs = service.list_configurations()
        assert len(configs) == 2

    def test_delete_configuration(self, service):
        """Test deleting a configuration."""
        config = service.create_configuration("ToDelete", "Delete me", "Legacy")

        assert service.delete_configuration(config.id)
        assert service.get_configuration(config.id) is None

        # Delete non-existent
        assert not service.delete_configuration(uuid4())

    # =========================================================================
    # Field Definition Tests
    # =========================================================================

    def test_add_legacy_field(self, service):
        """Test adding a legacy field definition."""
        config = service.create_configuration("Test", "Test", "Legacy")

        field = service.add_legacy_field(
            config_id=config.id,
            field_id="customer_nr",
            name="Klantnummer",
            selector="#txtCustomerNr",
            field_type=FieldType.STRING,
            sample_values=["KL001", "KL002"]
        )

        assert field.id == "customer_nr"
        assert len(config.legacy_fields) == 1

    def test_add_new_field(self, service):
        """Test adding a new field definition."""
        config = service.create_configuration("Test", "Test", "Legacy")

        field = service.add_new_field(
            config_id=config.id,
            field_id="customerId",
            name="Customer ID",
            path="customer.id",
            field_type=FieldType.STRING
        )

        assert field.path == "customer.id"
        assert len(config.new_fields) == 1

    def test_add_field_invalid_config(self, service):
        """Test adding field to non-existent config."""
        result = service.add_legacy_field(
            config_id=uuid4(),
            field_id="test",
            name="Test",
            selector=".test"
        )
        assert result is None

    # =========================================================================
    # Mapping Management Tests
    # =========================================================================

    def test_create_mapping(self, service):
        """Test creating a field mapping."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "old_name", "Oude Naam", "#name")
        service.add_new_field(config.id, "new_name", "New Name", "user.name")

        mapping = service.create_mapping(
            config_id=config.id,
            legacy_field_ids=["old_name"],
            new_field_id="new_name",
            transformations=[FieldTransformation(type=TransformationType.TRIM)],
            validations=[ValidationRule(type=ValidationType.REQUIRED)]
        )

        assert mapping is not None
        assert len(mapping.transformations) == 1

    def test_create_composite_mapping(self, service):
        """Test creating a composite field mapping."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "first", "Voornaam", "#first")
        service.add_legacy_field(config.id, "last", "Achternaam", "#last")
        service.add_new_field(config.id, "full", "Full Name", "user.fullName")

        mapping = service.create_mapping(
            config_id=config.id,
            legacy_field_ids=["first", "last"],
            new_field_id="full",
            composite_template="{first} {last}"
        )

        assert mapping.composite_template == "{first} {last}"

    def test_create_mapping_invalid_legacy_field(self, service):
        """Test creating mapping with invalid legacy field."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_new_field(config.id, "new", "New", "path")

        with pytest.raises(ValueError, match="Legacy field .* not found"):
            service.create_mapping(config.id, ["nonexistent"], "new")

    def test_create_mapping_invalid_new_field(self, service):
        """Test creating mapping with invalid new field."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "old", "Old", "#old")

        with pytest.raises(ValueError, match="New field .* not found"):
            service.create_mapping(config.id, ["old"], "nonexistent")

    def test_update_mapping(self, service):
        """Test updating a mapping."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "f1", "F1", "#f1")
        service.add_new_field(config.id, "f2", "F2", "f2")
        mapping = service.create_mapping(config.id, ["f1"], "f2", notes="Original")

        updated = service.update_mapping(
            config.id, mapping.id,
            notes="Updated notes",
            enabled=False
        )

        assert updated.notes == "Updated notes"
        assert not updated.enabled

    def test_delete_mapping(self, service):
        """Test deleting a mapping."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "f1", "F1", "#f1")
        service.add_new_field(config.id, "f2", "F2", "f2")
        mapping = service.create_mapping(config.id, ["f1"], "f2")

        assert service.delete_mapping(config.id, mapping.id)
        assert len(config.mappings) == 0

    # =========================================================================
    # Transformation Tests
    # =========================================================================

    def test_transform_lowercase(self, service):
        """Test lowercase transformation."""
        result = service.transform_value(
            "HELLO WORLD",
            [FieldTransformation(type=TransformationType.LOWERCASE)]
        )
        assert result.transformed_value == "hello world"
        assert result.success

    def test_transform_uppercase(self, service):
        """Test uppercase transformation."""
        result = service.transform_value(
            "hello world",
            [FieldTransformation(type=TransformationType.UPPERCASE)]
        )
        assert result.transformed_value == "HELLO WORLD"

    def test_transform_trim(self, service):
        """Test trim transformation."""
        result = service.transform_value(
            "  spaced  ",
            [FieldTransformation(type=TransformationType.TRIM)]
        )
        assert result.transformed_value == "spaced"

    def test_transform_date_nl(self, service):
        """Test Dutch date format transformation."""
        result = service.transform_value(
            "2024-12-25",
            [FieldTransformation(type=TransformationType.DATE_NL)]
        )
        assert result.transformed_value == "25-12-2024"

    def test_transform_date_iso(self, service):
        """Test ISO date format transformation."""
        result = service.transform_value(
            "25-12-2024",
            [FieldTransformation(type=TransformationType.DATE_ISO)]
        )
        assert result.transformed_value == "2024-12-25"

    def test_transform_date_us(self, service):
        """Test US date format transformation."""
        result = service.transform_value(
            "2024-12-25",
            [FieldTransformation(type=TransformationType.DATE_US)]
        )
        assert result.transformed_value == "12/25/2024"

    def test_transform_datetime_object(self, service):
        """Test datetime object transformation."""
        dt = datetime(2024, 6, 15)
        result = service.transform_value(
            dt,
            [FieldTransformation(type=TransformationType.DATE_NL)]
        )
        assert result.transformed_value == "15-06-2024"

    def test_transform_currency_eur(self, service):
        """Test Euro currency transformation."""
        result = service.transform_value(
            1234.56,
            [FieldTransformation(type=TransformationType.CURRENCY_EUR)]
        )
        assert result.transformed_value == "€1.234,56"

    def test_transform_currency_usd(self, service):
        """Test USD currency transformation."""
        result = service.transform_value(
            1234.56,
            [FieldTransformation(type=TransformationType.CURRENCY_USD)]
        )
        assert result.transformed_value == "$1,234.56"

    def test_transform_number_nl(self, service):
        """Test Dutch number format transformation."""
        result = service.transform_value(
            1234.56,
            [FieldTransformation(type=TransformationType.NUMBER_NL)]
        )
        assert result.transformed_value == "1.234,56"

    def test_transform_number_us(self, service):
        """Test US number format transformation."""
        result = service.transform_value(
            1234.56,
            [FieldTransformation(type=TransformationType.NUMBER_US)]
        )
        assert result.transformed_value == "1,234.56"

    def test_transform_phone_nl(self, service):
        """Test Dutch phone number transformation."""
        # Mobile number
        result = service.transform_value(
            "0612345678",
            [FieldTransformation(type=TransformationType.PHONE_NL)]
        )
        assert result.transformed_value == "+31 6 1234 5678"

    def test_transform_postal_code_nl(self, service):
        """Test Dutch postal code transformation."""
        result = service.transform_value(
            "1234AB",
            [FieldTransformation(type=TransformationType.POSTAL_CODE_NL)]
        )
        assert result.transformed_value == "1234 AB"

    def test_transform_postal_code_nl_with_space(self, service):
        """Test Dutch postal code with existing space."""
        result = service.transform_value(
            "1234 ab",
            [FieldTransformation(type=TransformationType.POSTAL_CODE_NL)]
        )
        assert result.transformed_value == "1234 AB"

    def test_transform_bsn(self, service):
        """Test BSN transformation."""
        result = service.transform_value(
            "123456789",
            [FieldTransformation(type=TransformationType.BSN)]
        )
        assert result.transformed_value == "123456789"

    def test_transform_iban(self, service):
        """Test IBAN transformation."""
        result = service.transform_value(
            "NL91ABNA0417164300",
            [FieldTransformation(type=TransformationType.IBAN)]
        )
        assert result.transformed_value == "NL91 ABNA 0417 1643 00"

    def test_transform_custom(self, service):
        """Test custom regex transformation."""
        result = service.transform_value(
            "hello   world",
            [FieldTransformation(
                type=TransformationType.CUSTOM,
                custom_pattern=r"\s+",
                custom_replacement="-"
            )]
        )
        assert result.transformed_value == "hello-world"

    def test_transform_chain(self, service):
        """Test chained transformations."""
        result = service.transform_value(
            "  HELLO WORLD  ",
            [
                FieldTransformation(type=TransformationType.TRIM),
                FieldTransformation(type=TransformationType.LOWERCASE)
            ]
        )
        assert result.transformed_value == "hello world"
        assert len(result.transformations_applied) == 2

    def test_transform_none_value(self, service):
        """Test transformation with None value."""
        result = service.transform_value(
            None,
            [FieldTransformation(type=TransformationType.UPPERCASE)]
        )
        assert result.transformed_value is None

    def test_transform_empty_value(self, service):
        """Test transformation with empty value."""
        result = service.transform_value(
            "",
            [FieldTransformation(type=TransformationType.DATE_NL)]
        )
        assert result.transformed_value == ""

    # =========================================================================
    # Validation Tests
    # =========================================================================

    def test_validate_required_pass(self, service):
        """Test required validation passing."""
        result = service.validate_value(
            "some value",
            [ValidationRule(type=ValidationType.REQUIRED)],
            "test_field"
        )
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_required_fail(self, service):
        """Test required validation failing."""
        result = service.validate_value(
            "",
            [ValidationRule(type=ValidationType.REQUIRED)],
            "test_field"
        )
        assert not result.valid
        assert len(result.errors) == 1

    def test_validate_min_length(self, service):
        """Test min length validation."""
        result = service.validate_value(
            "ab",
            [ValidationRule(type=ValidationType.MIN_LENGTH, value=3)],
            "test"
        )
        assert not result.valid

    def test_validate_max_length(self, service):
        """Test max length validation."""
        result = service.validate_value(
            "toolongvalue",
            [ValidationRule(type=ValidationType.MAX_LENGTH, value=5)],
            "test"
        )
        assert not result.valid

    def test_validate_pattern(self, service):
        """Test pattern validation."""
        result = service.validate_value(
            "ABC123",
            [ValidationRule(type=ValidationType.PATTERN, value=r"^[A-Z]{3}\d{3}$")],
            "test"
        )
        assert result.valid

    def test_validate_pattern_fail(self, service):
        """Test pattern validation failing."""
        result = service.validate_value(
            "abc123",
            [ValidationRule(type=ValidationType.PATTERN, value=r"^[A-Z]{3}\d{3}$")],
            "test"
        )
        assert not result.valid

    def test_validate_email(self, service):
        """Test email validation."""
        result = service.validate_value(
            "test@example.com",
            [ValidationRule(type=ValidationType.EMAIL)],
            "email"
        )
        assert result.valid

    def test_validate_email_fail(self, service):
        """Test email validation failing."""
        result = service.validate_value(
            "not-an-email",
            [ValidationRule(type=ValidationType.EMAIL)],
            "email"
        )
        assert not result.valid

    def test_validate_url(self, service):
        """Test URL validation."""
        result = service.validate_value(
            "https://example.com/path",
            [ValidationRule(type=ValidationType.URL)],
            "url"
        )
        assert result.valid

    def test_validate_number(self, service):
        """Test number validation."""
        result = service.validate_value(
            "123.45",
            [ValidationRule(type=ValidationType.NUMBER)],
            "amount"
        )
        assert result.valid

    def test_validate_integer(self, service):
        """Test integer validation."""
        result = service.validate_value(
            "123",
            [ValidationRule(type=ValidationType.INTEGER)],
            "count"
        )
        assert result.valid

    def test_validate_integer_fail(self, service):
        """Test integer validation failing."""
        result = service.validate_value(
            "123.45",
            [ValidationRule(type=ValidationType.INTEGER)],
            "count"
        )
        assert not result.valid

    def test_validate_date(self, service):
        """Test date validation."""
        result = service.validate_value(
            "2024-12-25",
            [ValidationRule(type=ValidationType.DATE)],
            "date"
        )
        assert result.valid

    def test_validate_range(self, service):
        """Test range validation."""
        result = service.validate_value(
            "50",
            [ValidationRule(type=ValidationType.RANGE, value={"min": 0, "max": 100})],
            "percentage"
        )
        assert result.valid

    def test_validate_range_fail(self, service):
        """Test range validation failing."""
        result = service.validate_value(
            "150",
            [ValidationRule(type=ValidationType.RANGE, value={"min": 0, "max": 100})],
            "percentage"
        )
        assert not result.valid

    def test_validate_enum(self, service):
        """Test enum validation."""
        result = service.validate_value(
            "active",
            [ValidationRule(type=ValidationType.ENUM, value=["active", "inactive", "pending"])],
            "status"
        )
        assert result.valid

    def test_validate_enum_fail(self, service):
        """Test enum validation failing."""
        result = service.validate_value(
            "unknown",
            [ValidationRule(type=ValidationType.ENUM, value=["active", "inactive"])],
            "status"
        )
        assert not result.valid

    def test_validate_multiple_rules(self, service):
        """Test multiple validation rules."""
        result = service.validate_value(
            "ab",
            [
                ValidationRule(type=ValidationType.REQUIRED),
                ValidationRule(type=ValidationType.MIN_LENGTH, value=5),
                ValidationRule(type=ValidationType.MAX_LENGTH, value=10)
            ],
            "test"
        )
        assert not result.valid
        assert len(result.errors) == 1  # Only min_length fails

    # =========================================================================
    # Mapping Execution Tests
    # =========================================================================

    def test_map_to_new_simple(self, service):
        """Test simple field mapping execution."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "old_name", "Naam", "#name")
        service.add_new_field(config.id, "new_name", "Name", "user.name")
        service.create_mapping(
            config.id, ["old_name"], "new_name",
            transformations=[FieldTransformation(type=TransformationType.TRIM)]
        )

        result = service.map_to_new(
            config.id,
            {"old_name": "  John Doe  "}
        )

        assert result["user.name"] == "John Doe"

    def test_map_to_new_composite(self, service):
        """Test composite field mapping execution."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "first", "Voornaam", "#first")
        service.add_legacy_field(config.id, "last", "Achternaam", "#last")
        service.add_new_field(config.id, "full", "Full Name", "user.fullName")
        service.create_mapping(
            config.id, ["first", "last"], "full",
            composite_template="{first} {last}"
        )

        result = service.map_to_new(
            config.id,
            {"first": "Jan", "last": "Jansen"}
        )

        assert result["user.fullName"] == "Jan Jansen"

    def test_map_to_new_disabled_mapping(self, service):
        """Test that disabled mappings are skipped."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "f1", "F1", "#f1")
        service.add_new_field(config.id, "f2", "F2", "f2")
        mapping = service.create_mapping(config.id, ["f1"], "f2")
        mapping.enabled = False

        result = service.map_to_new(config.id, {"f1": "value"})
        assert "f2" not in result

    def test_map_to_new_invalid_config(self, service):
        """Test mapping with invalid config."""
        with pytest.raises(ValueError, match="Configuration not found"):
            service.map_to_new(uuid4(), {})

    def test_map_to_legacy_bidirectional(self, service):
        """Test bidirectional mapping to legacy."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "old_f", "Old", "#old")
        service.add_new_field(config.id, "new_f", "New", "new.path")
        service.create_mapping(
            config.id, ["old_f"], "new_f",
            bidirectional=True
        )

        result = service.map_to_legacy(
            config.id,
            {"new.path": "test value"}
        )

        assert result["#old"] == "test value"

    # =========================================================================
    # Preview Generation Tests
    # =========================================================================

    def test_generate_preview(self, service):
        """Test preview generation."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "amount", "Bedrag", "#amount")
        service.add_new_field(config.id, "price", "Price", "item.price")
        mapping = service.create_mapping(
            config.id, ["amount"], "price",
            transformations=[FieldTransformation(type=TransformationType.CURRENCY_EUR)],
            validations=[ValidationRule(type=ValidationType.REQUIRED)]
        )

        preview = service.generate_preview(
            config.id,
            mapping.id,
            {"amount": 1234.56}
        )

        assert preview is not None
        assert preview.new_value == "€1.234,56"
        assert preview.validation_result.valid

    def test_generate_preview_composite(self, service):
        """Test preview generation for composite mapping."""
        config = service.create_configuration("Test", "Test", "Legacy")
        service.add_legacy_field(config.id, "street", "Straat", "#street")
        service.add_legacy_field(config.id, "number", "Nummer", "#number")
        service.add_new_field(config.id, "address", "Address", "user.address")
        mapping = service.create_mapping(
            config.id, ["street", "number"], "address",
            composite_template="{street} {number}"
        )

        preview = service.generate_preview(
            config.id,
            mapping.id,
            {"street": "Hoofdstraat", "number": "123"}
        )

        assert preview.new_value == "Hoofdstraat 123"

    # =========================================================================
    # Export/Import Tests
    # =========================================================================

    def test_export_configuration(self, service):
        """Test configuration export to JSON."""
        config = service.create_configuration("Export Test", "Test export", "Legacy")
        service.add_legacy_field(config.id, "f1", "F1", "#f1")
        service.add_new_field(config.id, "f2", "F2", "f2")
        service.create_mapping(config.id, ["f1"], "f2")

        json_export = service.export_configuration(config.id)
        data = json.loads(json_export)

        assert data["name"] == "Export Test"
        assert len(data["legacy_fields"]) == 1
        assert len(data["mappings"]) == 1

    def test_import_configuration(self, service):
        """Test configuration import from JSON."""
        json_data = json.dumps({
            "id": str(uuid4()),
            "name": "Imported Config",
            "description": "Imported",
            "legacy_system": "Legacy",
            "legacy_fields": [
                {"id": "f1", "name": "F1", "selector": "#f1"}
            ],
            "new_fields": [
                {"id": "f2", "name": "F2", "path": "f2"}
            ],
            "mappings": []
        })

        config = service.import_configuration(json_data)
        assert config.name == "Imported Config"
        assert len(config.legacy_fields) == 1

    def test_export_mapping_as_typescript(self, service):
        """Test exporting mapping as TypeScript code."""
        config = service.create_configuration("TS Export", "Test", "Legacy")
        service.add_legacy_field(config.id, "userName", "User", "#user", FieldType.STRING)
        service.add_legacy_field(config.id, "userAge", "Age", "#age", FieldType.NUMBER)
        service.add_new_field(config.id, "name", "Name", "user.name", FieldType.STRING)
        service.add_new_field(config.id, "age", "Age", "user.age", FieldType.NUMBER)
        service.create_mapping(config.id, ["userName"], "name")
        service.create_mapping(config.id, ["userAge"], "age")

        ts_code = service.export_mapping_as_code(config.id, "typescript")

        assert "interface LegacyData" in ts_code
        assert "interface NewData" in ts_code
        assert "mapLegacyToNew" in ts_code
        assert "userName: string" in ts_code

    def test_export_mapping_as_python(self, service):
        """Test exporting mapping as Python code."""
        config = service.create_configuration("PY Export", "Test", "Legacy")
        service.add_legacy_field(config.id, "name", "Name", "#name", FieldType.STRING)
        service.add_new_field(config.id, "fullName", "Full Name", "user.fullName", FieldType.STRING)
        service.create_mapping(config.id, ["name"], "fullName")

        py_code = service.export_mapping_as_code(config.id, "python")

        assert "@dataclass" in py_code
        assert "class LegacyData:" in py_code
        assert "def map_legacy_to_new" in py_code

    def test_export_mapping_invalid_language(self, service):
        """Test export with invalid language."""
        config = service.create_configuration("Test", "Test", "Legacy")

        with pytest.raises(ValueError, match="Unsupported language"):
            service.export_mapping_as_code(config.id, "java")


# ============================================================================
# Enum Tests
# ============================================================================

class TestEnums:
    """Tests for service enums."""

    def test_transformation_type_values(self):
        """Test transformation type enum values."""
        assert TransformationType.NONE.value == "none"
        assert TransformationType.LOWERCASE.value == "lowercase"
        assert TransformationType.UPPERCASE.value == "uppercase"
        assert TransformationType.DATE_NL.value == "date_nl"
        assert TransformationType.CURRENCY_EUR.value == "currency_eur"
        assert TransformationType.PHONE_NL.value == "phone_nl"
        assert TransformationType.POSTAL_CODE_NL.value == "postal_code_nl"
        assert TransformationType.BSN.value == "bsn"
        assert TransformationType.IBAN.value == "iban"

    def test_validation_type_values(self):
        """Test validation type enum values."""
        assert ValidationType.REQUIRED.value == "required"
        assert ValidationType.MIN_LENGTH.value == "min_length"
        assert ValidationType.MAX_LENGTH.value == "max_length"
        assert ValidationType.PATTERN.value == "pattern"
        assert ValidationType.EMAIL.value == "email"
        assert ValidationType.URL.value == "url"
        assert ValidationType.RANGE.value == "range"
        assert ValidationType.ENUM.value == "enum"

    def test_field_type_values(self):
        """Test field type enum values."""
        assert FieldType.STRING.value == "string"
        assert FieldType.NUMBER.value == "number"
        assert FieldType.BOOLEAN.value == "boolean"
        assert FieldType.DATE.value == "date"
        assert FieldType.DATETIME.value == "datetime"
        assert FieldType.ARRAY.value == "array"
        assert FieldType.OBJECT.value == "object"
