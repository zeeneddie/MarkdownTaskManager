"""
B9: UI Wrapper Field Mapper Service

Visual field mapper for legacy system wrapping with:
- Drag-and-drop field coupling interface data model
- JSON configuration export/import
- Field transformations (lowercase, uppercase, date_nl, currency_eur, etc.)
- Composite field support (combining multiple legacy fields)
- Validation rules
- Live preview generation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID, uuid4
import json
import re


class TransformationType(str, Enum):
    """Available field transformation types."""
    NONE = "none"
    LOWERCASE = "lowercase"
    UPPERCASE = "uppercase"
    TRIM = "trim"
    DATE_NL = "date_nl"  # DD-MM-YYYY format
    DATE_ISO = "date_iso"  # YYYY-MM-DD format
    DATE_US = "date_us"  # MM/DD/YYYY format
    CURRENCY_EUR = "currency_eur"  # €1.234,56
    CURRENCY_USD = "currency_usd"  # $1,234.56
    NUMBER_NL = "number_nl"  # 1.234,56
    NUMBER_US = "number_us"  # 1,234.56
    PHONE_NL = "phone_nl"  # +31 6 12345678
    POSTAL_CODE_NL = "postal_code_nl"  # 1234 AB
    BSN = "bsn"  # Dutch social security number
    IBAN = "iban"  # International Bank Account Number
    CUSTOM = "custom"  # Custom regex transformation


class ValidationType(str, Enum):
    """Available validation rule types."""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    EMAIL = "email"
    URL = "url"
    NUMBER = "number"
    INTEGER = "integer"
    DATE = "date"
    RANGE = "range"
    ENUM = "enum"
    CUSTOM = "custom"


class FieldType(str, Enum):
    """Field data types."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ValidationRule:
    """A validation rule for a field."""
    type: ValidationType
    value: Optional[Any] = None  # e.g., min_length value, pattern regex
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "value": self.value,
            "message": self.message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationRule":
        return cls(
            type=ValidationType(data["type"]),
            value=data.get("value"),
            message=data.get("message", "")
        )


@dataclass
class FieldTransformation:
    """A transformation applied to a field value."""
    type: TransformationType
    custom_pattern: Optional[str] = None  # For CUSTOM type
    custom_replacement: Optional[str] = None  # For CUSTOM type
    format_string: Optional[str] = None  # For date/number formatting

    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type.value}
        if self.custom_pattern:
            result["custom_pattern"] = self.custom_pattern
        if self.custom_replacement:
            result["custom_replacement"] = self.custom_replacement
        if self.format_string:
            result["format_string"] = self.format_string
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldTransformation":
        return cls(
            type=TransformationType(data["type"]),
            custom_pattern=data.get("custom_pattern"),
            custom_replacement=data.get("custom_replacement"),
            format_string=data.get("format_string")
        )


@dataclass
class LegacyFieldDefinition:
    """Definition of a field in the legacy system."""
    id: str
    name: str
    selector: str  # CSS selector or XPath for UI scraping
    field_type: FieldType = FieldType.STRING
    description: str = ""
    sample_values: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "selector": self.selector,
            "field_type": self.field_type.value,
            "description": self.description,
            "sample_values": self.sample_values
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LegacyFieldDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            selector=data["selector"],
            field_type=FieldType(data.get("field_type", "string")),
            description=data.get("description", ""),
            sample_values=data.get("sample_values", [])
        )


@dataclass
class NewFieldDefinition:
    """Definition of a field in the new system."""
    id: str
    name: str
    path: str  # JSON path or object path (e.g., "user.address.street")
    field_type: FieldType = FieldType.STRING
    description: str = ""
    default_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "field_type": self.field_type.value,
            "description": self.description,
            "default_value": self.default_value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewFieldDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            field_type=FieldType(data.get("field_type", "string")),
            description=data.get("description", ""),
            default_value=data.get("default_value")
        )


@dataclass
class FieldMapping:
    """A mapping between legacy and new system fields."""
    id: UUID
    legacy_fields: List[str]  # List of legacy field IDs (for composite fields)
    new_field: str  # New field ID
    transformations: List[FieldTransformation] = field(default_factory=list)
    validations: List[ValidationRule] = field(default_factory=list)
    composite_template: Optional[str] = None  # Template for combining fields: "{field1} {field2}"
    bidirectional: bool = False  # Whether mapping works both ways
    enabled: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "legacy_fields": self.legacy_fields,
            "new_field": self.new_field,
            "transformations": [t.to_dict() for t in self.transformations],
            "validations": [v.to_dict() for v in self.validations],
            "composite_template": self.composite_template,
            "bidirectional": self.bidirectional,
            "enabled": self.enabled,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldMapping":
        return cls(
            id=UUID(data["id"]),
            legacy_fields=data["legacy_fields"],
            new_field=data["new_field"],
            transformations=[FieldTransformation.from_dict(t) for t in data.get("transformations", [])],
            validations=[ValidationRule.from_dict(v) for v in data.get("validations", [])],
            composite_template=data.get("composite_template"),
            bidirectional=data.get("bidirectional", False),
            enabled=data.get("enabled", True),
            notes=data.get("notes", "")
        )


@dataclass
class MappingConfiguration:
    """Complete field mapping configuration for a legacy system wrapper."""
    id: UUID
    name: str
    description: str
    legacy_system: str
    legacy_fields: List[LegacyFieldDefinition]
    new_fields: List[NewFieldDefinition]
    mappings: List[FieldMapping]
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "legacy_system": self.legacy_system,
            "legacy_fields": [f.to_dict() for f in self.legacy_fields],
            "new_fields": [f.to_dict() for f in self.new_fields],
            "mappings": [m.to_dict() for m in self.mappings],
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MappingConfiguration":
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            description=data["description"],
            legacy_system=data["legacy_system"],
            legacy_fields=[LegacyFieldDefinition.from_dict(f) for f in data["legacy_fields"]],
            new_fields=[NewFieldDefinition.from_dict(f) for f in data["new_fields"]],
            mappings=[FieldMapping.from_dict(m) for m in data["mappings"]],
            version=data.get("version", "1.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        )


@dataclass
class ValidationResult:
    """Result of field validation."""
    valid: bool
    field_id: str
    value: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TransformationResult:
    """Result of field transformation."""
    original_value: Any
    transformed_value: Any
    transformations_applied: List[str]
    success: bool
    error: Optional[str] = None


@dataclass
class MappingPreview:
    """Preview of a field mapping result."""
    legacy_values: Dict[str, Any]
    new_value: Any
    transformation_steps: List[TransformationResult]
    validation_result: ValidationResult
    mapping_id: UUID


class UIWrapperFieldMapperService:
    """
    Service for visual field mapping between legacy and new systems.

    Provides:
    - Field mapping configuration management
    - Value transformation with Dutch locale support
    - Validation with detailed error reporting
    - Bidirectional mapping support
    - Live preview generation
    - JSON configuration export/import
    """

    def __init__(self):
        self._configurations: Dict[UUID, MappingConfiguration] = {}
        self._transformers: Dict[TransformationType, Callable[[Any, FieldTransformation], Any]] = {
            TransformationType.NONE: lambda v, t: v,
            TransformationType.LOWERCASE: lambda v, t: str(v).lower() if v else v,
            TransformationType.UPPERCASE: lambda v, t: str(v).upper() if v else v,
            TransformationType.TRIM: lambda v, t: str(v).strip() if v else v,
            TransformationType.DATE_NL: self._transform_date_nl,
            TransformationType.DATE_ISO: self._transform_date_iso,
            TransformationType.DATE_US: self._transform_date_us,
            TransformationType.CURRENCY_EUR: self._transform_currency_eur,
            TransformationType.CURRENCY_USD: self._transform_currency_usd,
            TransformationType.NUMBER_NL: self._transform_number_nl,
            TransformationType.NUMBER_US: self._transform_number_us,
            TransformationType.PHONE_NL: self._transform_phone_nl,
            TransformationType.POSTAL_CODE_NL: self._transform_postal_code_nl,
            TransformationType.BSN: self._transform_bsn,
            TransformationType.IBAN: self._transform_iban,
            TransformationType.CUSTOM: self._transform_custom,
        }
        self._validators: Dict[ValidationType, Callable[[Any, ValidationRule], Optional[str]]] = {
            ValidationType.REQUIRED: self._validate_required,
            ValidationType.MIN_LENGTH: self._validate_min_length,
            ValidationType.MAX_LENGTH: self._validate_max_length,
            ValidationType.PATTERN: self._validate_pattern,
            ValidationType.EMAIL: self._validate_email,
            ValidationType.URL: self._validate_url,
            ValidationType.NUMBER: self._validate_number,
            ValidationType.INTEGER: self._validate_integer,
            ValidationType.DATE: self._validate_date,
            ValidationType.RANGE: self._validate_range,
            ValidationType.ENUM: self._validate_enum,
            ValidationType.CUSTOM: self._validate_custom,
        }

    # =========================================================================
    # Configuration Management
    # =========================================================================

    def create_configuration(
        self,
        name: str,
        description: str,
        legacy_system: str
    ) -> MappingConfiguration:
        """Create a new mapping configuration."""
        config = MappingConfiguration(
            id=uuid4(),
            name=name,
            description=description,
            legacy_system=legacy_system,
            legacy_fields=[],
            new_fields=[],
            mappings=[]
        )
        self._configurations[config.id] = config
        return config

    def get_configuration(self, config_id: Union[UUID, str]) -> Optional[MappingConfiguration]:
        """Get a configuration by ID."""
        if isinstance(config_id, str):
            config_id = UUID(config_id)
        return self._configurations.get(config_id)

    def list_configurations(self) -> List[MappingConfiguration]:
        """List all configurations."""
        return list(self._configurations.values())

    def delete_configuration(self, config_id: Union[UUID, str]) -> bool:
        """Delete a configuration."""
        if isinstance(config_id, str):
            config_id = UUID(config_id)
        if config_id in self._configurations:
            del self._configurations[config_id]
            return True
        return False

    # =========================================================================
    # Field Definition Management
    # =========================================================================

    def add_legacy_field(
        self,
        config_id: Union[UUID, str],
        field_id: str,
        name: str,
        selector: str,
        field_type: FieldType = FieldType.STRING,
        description: str = "",
        sample_values: Optional[List[str]] = None
    ) -> Optional[LegacyFieldDefinition]:
        """Add a legacy field definition to a configuration."""
        config = self.get_configuration(config_id)
        if not config:
            return None

        field_def = LegacyFieldDefinition(
            id=field_id,
            name=name,
            selector=selector,
            field_type=field_type,
            description=description,
            sample_values=sample_values or []
        )
        config.legacy_fields.append(field_def)
        config.updated_at = datetime.now()
        return field_def

    def add_new_field(
        self,
        config_id: Union[UUID, str],
        field_id: str,
        name: str,
        path: str,
        field_type: FieldType = FieldType.STRING,
        description: str = "",
        default_value: Optional[Any] = None
    ) -> Optional[NewFieldDefinition]:
        """Add a new field definition to a configuration."""
        config = self.get_configuration(config_id)
        if not config:
            return None

        field_def = NewFieldDefinition(
            id=field_id,
            name=name,
            path=path,
            field_type=field_type,
            description=description,
            default_value=default_value
        )
        config.new_fields.append(field_def)
        config.updated_at = datetime.now()
        return field_def

    # =========================================================================
    # Mapping Management
    # =========================================================================

    def create_mapping(
        self,
        config_id: Union[UUID, str],
        legacy_field_ids: List[str],
        new_field_id: str,
        transformations: Optional[List[FieldTransformation]] = None,
        validations: Optional[List[ValidationRule]] = None,
        composite_template: Optional[str] = None,
        bidirectional: bool = False,
        notes: str = ""
    ) -> Optional[FieldMapping]:
        """Create a field mapping."""
        config = self.get_configuration(config_id)
        if not config:
            return None

        # Validate field IDs exist
        legacy_ids = {f.id for f in config.legacy_fields}
        new_ids = {f.id for f in config.new_fields}

        for field_id in legacy_field_ids:
            if field_id not in legacy_ids:
                raise ValueError(f"Legacy field '{field_id}' not found in configuration")

        if new_field_id not in new_ids:
            raise ValueError(f"New field '{new_field_id}' not found in configuration")

        mapping = FieldMapping(
            id=uuid4(),
            legacy_fields=legacy_field_ids,
            new_field=new_field_id,
            transformations=transformations or [],
            validations=validations or [],
            composite_template=composite_template,
            bidirectional=bidirectional,
            notes=notes
        )
        config.mappings.append(mapping)
        config.updated_at = datetime.now()
        return mapping

    def update_mapping(
        self,
        config_id: Union[UUID, str],
        mapping_id: Union[UUID, str],
        **updates
    ) -> Optional[FieldMapping]:
        """Update an existing mapping."""
        config = self.get_configuration(config_id)
        if not config:
            return None

        if isinstance(mapping_id, str):
            mapping_id = UUID(mapping_id)

        for mapping in config.mappings:
            if mapping.id == mapping_id:
                for key, value in updates.items():
                    if hasattr(mapping, key):
                        setattr(mapping, key, value)
                config.updated_at = datetime.now()
                return mapping
        return None

    def delete_mapping(
        self,
        config_id: Union[UUID, str],
        mapping_id: Union[UUID, str]
    ) -> bool:
        """Delete a mapping."""
        config = self.get_configuration(config_id)
        if not config:
            return False

        if isinstance(mapping_id, str):
            mapping_id = UUID(mapping_id)

        for i, mapping in enumerate(config.mappings):
            if mapping.id == mapping_id:
                config.mappings.pop(i)
                config.updated_at = datetime.now()
                return True
        return False

    # =========================================================================
    # Transformation Functions
    # =========================================================================

    def _transform_date_nl(self, value: Any, transform: FieldTransformation) -> str:
        """Transform date to Dutch format (DD-MM-YYYY)."""
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%d-%m-%Y")
        # Try to parse various formats
        date_obj = self._parse_date(value)
        return date_obj.strftime("%d-%m-%Y") if date_obj else str(value)

    def _transform_date_iso(self, value: Any, transform: FieldTransformation) -> str:
        """Transform date to ISO format (YYYY-MM-DD)."""
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        date_obj = self._parse_date(value)
        return date_obj.strftime("%Y-%m-%d") if date_obj else str(value)

    def _transform_date_us(self, value: Any, transform: FieldTransformation) -> str:
        """Transform date to US format (MM/DD/YYYY)."""
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y")
        date_obj = self._parse_date(value)
        return date_obj.strftime("%m/%d/%Y") if date_obj else str(value)

    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parse date from various formats."""
        formats = [
            "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None

    def _transform_currency_eur(self, value: Any, transform: FieldTransformation) -> str:
        """Transform number to Euro currency format (€1.234,56)."""
        if value is None:
            return ""
        try:
            num = float(str(value).replace(",", ".").replace("€", "").replace(" ", ""))
            # Format with Dutch locale (. for thousands, , for decimal)
            formatted = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"€{formatted}"
        except ValueError:
            return str(value)

    def _transform_currency_usd(self, value: Any, transform: FieldTransformation) -> str:
        """Transform number to USD currency format ($1,234.56)."""
        if value is None:
            return ""
        try:
            num = float(str(value).replace(",", "").replace("$", "").replace(" ", ""))
            return f"${num:,.2f}"
        except ValueError:
            return str(value)

    def _transform_number_nl(self, value: Any, transform: FieldTransformation) -> str:
        """Transform number to Dutch format (1.234,56)."""
        if value is None:
            return ""
        try:
            num = float(str(value).replace(",", ".").replace(" ", ""))
            formatted = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted
        except ValueError:
            return str(value)

    def _transform_number_us(self, value: Any, transform: FieldTransformation) -> str:
        """Transform number to US format (1,234.56)."""
        if value is None:
            return ""
        try:
            num = float(str(value).replace(",", "").replace(" ", ""))
            return f"{num:,.2f}"
        except ValueError:
            return str(value)

    def _transform_phone_nl(self, value: Any, transform: FieldTransformation) -> str:
        """Transform phone number to Dutch format (+31 6 12345678)."""
        if not value:
            return ""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", str(value))

        # Handle various input formats
        if digits.startswith("31"):
            digits = digits[2:]
        elif digits.startswith("0"):
            digits = digits[1:]

        if len(digits) == 9:
            if digits.startswith("6"):
                return f"+31 6 {digits[1:5]} {digits[5:]}"
            else:
                return f"+31 {digits[0:2]} {digits[2:5]} {digits[5:]}"
        return str(value)

    def _transform_postal_code_nl(self, value: Any, transform: FieldTransformation) -> str:
        """Transform to Dutch postal code format (1234 AB)."""
        if not value:
            return ""
        cleaned = re.sub(r"\s+", "", str(value).upper())
        if len(cleaned) == 6:
            return f"{cleaned[:4]} {cleaned[4:]}"
        return str(value)

    def _transform_bsn(self, value: Any, transform: FieldTransformation) -> str:
        """Format Dutch BSN (Burgerservicenummer)."""
        if not value:
            return ""
        digits = re.sub(r"\D", "", str(value))
        if len(digits) == 9:
            return digits  # BSN is typically displayed without formatting
        return str(value)

    def _transform_iban(self, value: Any, transform: FieldTransformation) -> str:
        """Format IBAN in groups of 4."""
        if not value:
            return ""
        cleaned = re.sub(r"\s+", "", str(value).upper())
        # Format in groups of 4
        return " ".join([cleaned[i:i+4] for i in range(0, len(cleaned), 4)])

    def _transform_custom(self, value: Any, transform: FieldTransformation) -> str:
        """Apply custom regex transformation."""
        if not value or not transform.custom_pattern:
            return str(value) if value else ""
        try:
            return re.sub(
                transform.custom_pattern,
                transform.custom_replacement or "",
                str(value)
            )
        except re.error:
            return str(value)

    def transform_value(
        self,
        value: Any,
        transformations: List[FieldTransformation]
    ) -> TransformationResult:
        """Apply a list of transformations to a value."""
        current_value = value
        applied = []

        try:
            for transform in transformations:
                transformer = self._transformers.get(transform.type)
                if transformer:
                    current_value = transformer(current_value, transform)
                    applied.append(transform.type.value)

            return TransformationResult(
                original_value=value,
                transformed_value=current_value,
                transformations_applied=applied,
                success=True
            )
        except Exception as e:
            return TransformationResult(
                original_value=value,
                transformed_value=value,
                transformations_applied=applied,
                success=False,
                error=str(e)
            )

    # =========================================================================
    # Validation Functions
    # =========================================================================

    def _validate_required(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate that a value is present."""
        if value is None or value == "":
            return rule.message or "This field is required"
        return None

    def _validate_min_length(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate minimum length."""
        if value and len(str(value)) < rule.value:
            return rule.message or f"Minimum length is {rule.value}"
        return None

    def _validate_max_length(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate maximum length."""
        if value and len(str(value)) > rule.value:
            return rule.message or f"Maximum length is {rule.value}"
        return None

    def _validate_pattern(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate against a regex pattern."""
        if value and not re.match(rule.value, str(value)):
            return rule.message or "Value does not match required pattern"
        return None

    def _validate_email(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate email format."""
        if value:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                return rule.message or "Invalid email format"
        return None

    def _validate_url(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate URL format."""
        if value:
            url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if not re.match(url_pattern, str(value)):
                return rule.message or "Invalid URL format"
        return None

    def _validate_number(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate that value is a number."""
        if value:
            try:
                float(str(value).replace(",", "."))
            except ValueError:
                return rule.message or "Value must be a number"
        return None

    def _validate_integer(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate that value is an integer."""
        if value:
            try:
                int(str(value))
            except ValueError:
                return rule.message or "Value must be an integer"
        return None

    def _validate_date(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate date format."""
        if value and not self._parse_date(str(value)):
            return rule.message or "Invalid date format"
        return None

    def _validate_range(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate that value is within a range."""
        if value and rule.value:
            try:
                num = float(str(value).replace(",", "."))
                min_val = rule.value.get("min")
                max_val = rule.value.get("max")
                if min_val is not None and num < min_val:
                    return rule.message or f"Value must be at least {min_val}"
                if max_val is not None and num > max_val:
                    return rule.message or f"Value must be at most {max_val}"
            except (ValueError, AttributeError):
                pass
        return None

    def _validate_enum(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate that value is in an allowed list."""
        if value and rule.value and str(value) not in rule.value:
            return rule.message or f"Value must be one of: {', '.join(rule.value)}"
        return None

    def _validate_custom(self, value: Any, rule: ValidationRule) -> Optional[str]:
        """Apply custom validation (expects regex pattern in rule.value)."""
        if value and rule.value:
            if not re.match(rule.value, str(value)):
                return rule.message or "Custom validation failed"
        return None

    def validate_value(
        self,
        value: Any,
        validations: List[ValidationRule],
        field_id: str = ""
    ) -> ValidationResult:
        """Validate a value against a list of rules."""
        errors = []
        warnings = []

        for rule in validations:
            validator = self._validators.get(rule.type)
            if validator:
                error = validator(value, rule)
                if error:
                    errors.append(error)

        return ValidationResult(
            valid=len(errors) == 0,
            field_id=field_id,
            value=value,
            errors=errors,
            warnings=warnings
        )

    # =========================================================================
    # Mapping Execution
    # =========================================================================

    def map_to_new(
        self,
        config_id: Union[UUID, str],
        legacy_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map legacy field values to new system fields.

        Args:
            config_id: Configuration ID
            legacy_values: Dict of legacy field ID -> value

        Returns:
            Dict of new field path -> transformed value
        """
        config = self.get_configuration(config_id)
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")

        result = {}

        for mapping in config.mappings:
            if not mapping.enabled:
                continue

            # Get values from legacy fields
            if len(mapping.legacy_fields) == 1:
                # Simple mapping
                value = legacy_values.get(mapping.legacy_fields[0])
            else:
                # Composite mapping
                if mapping.composite_template:
                    # Use template to combine values
                    value = mapping.composite_template
                    for field_id in mapping.legacy_fields:
                        field_value = legacy_values.get(field_id, "")
                        value = value.replace(f"{{{field_id}}}", str(field_value))
                else:
                    # Concatenate with space
                    values = [str(legacy_values.get(fid, "")) for fid in mapping.legacy_fields]
                    value = " ".join(filter(None, values))

            # Apply transformations
            transform_result = self.transform_value(value, mapping.transformations)

            # Get new field path
            new_field = next((f for f in config.new_fields if f.id == mapping.new_field), None)
            if new_field:
                result[new_field.path] = transform_result.transformed_value

        return result

    def map_to_legacy(
        self,
        config_id: Union[UUID, str],
        new_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map new system field values back to legacy fields (for bidirectional mappings).

        Args:
            config_id: Configuration ID
            new_values: Dict of new field path -> value

        Returns:
            Dict of legacy field selector -> value
        """
        config = self.get_configuration(config_id)
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")

        result = {}

        for mapping in config.mappings:
            if not mapping.enabled or not mapping.bidirectional:
                continue

            # Get new field and its value
            new_field = next((f for f in config.new_fields if f.id == mapping.new_field), None)
            if not new_field or new_field.path not in new_values:
                continue

            value = new_values[new_field.path]

            # For simple mappings, map back to the legacy field
            if len(mapping.legacy_fields) == 1:
                legacy_field = next(
                    (f for f in config.legacy_fields if f.id == mapping.legacy_fields[0]),
                    None
                )
                if legacy_field:
                    result[legacy_field.selector] = value

        return result

    # =========================================================================
    # Preview Generation
    # =========================================================================

    def generate_preview(
        self,
        config_id: Union[UUID, str],
        mapping_id: Union[UUID, str],
        legacy_values: Dict[str, Any]
    ) -> Optional[MappingPreview]:
        """
        Generate a preview of how a mapping will transform values.

        Args:
            config_id: Configuration ID
            mapping_id: Mapping ID to preview
            legacy_values: Sample legacy field values

        Returns:
            MappingPreview showing transformation steps and result
        """
        config = self.get_configuration(config_id)
        if not config:
            return None

        if isinstance(mapping_id, str):
            mapping_id = UUID(mapping_id)

        mapping = next((m for m in config.mappings if m.id == mapping_id), None)
        if not mapping:
            return None

        # Get relevant legacy values
        relevant_values = {
            fid: legacy_values.get(fid) for fid in mapping.legacy_fields
        }

        # Compute initial value
        if len(mapping.legacy_fields) == 1:
            value = relevant_values.get(mapping.legacy_fields[0])
        elif mapping.composite_template:
            value = mapping.composite_template
            for field_id, field_value in relevant_values.items():
                value = value.replace(f"{{{field_id}}}", str(field_value or ""))
        else:
            value = " ".join(str(v) for v in relevant_values.values() if v)

        # Track transformation steps
        steps = []
        current_value = value

        for transform in mapping.transformations:
            result = self.transform_value(current_value, [transform])
            steps.append(result)
            current_value = result.transformed_value

        # Validate final value
        validation_result = self.validate_value(
            current_value,
            mapping.validations,
            mapping.new_field
        )

        return MappingPreview(
            legacy_values=relevant_values,
            new_value=current_value,
            transformation_steps=steps,
            validation_result=validation_result,
            mapping_id=mapping.id
        )

    # =========================================================================
    # Export/Import
    # =========================================================================

    def export_configuration(
        self,
        config_id: Union[UUID, str],
        pretty: bool = True
    ) -> str:
        """Export configuration to JSON string."""
        config = self.get_configuration(config_id)
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")

        if pretty:
            return json.dumps(config.to_dict(), indent=2, ensure_ascii=False)
        return json.dumps(config.to_dict(), ensure_ascii=False)

    def import_configuration(self, json_data: str) -> MappingConfiguration:
        """Import configuration from JSON string."""
        data = json.loads(json_data)
        config = MappingConfiguration.from_dict(data)
        self._configurations[config.id] = config
        return config

    def export_mapping_as_code(
        self,
        config_id: Union[UUID, str],
        language: str = "typescript"
    ) -> str:
        """
        Export mapping configuration as executable code.

        Args:
            config_id: Configuration ID
            language: Target language (typescript, python)

        Returns:
            Code string that implements the mapping
        """
        config = self.get_configuration(config_id)
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")

        if language == "typescript":
            return self._export_typescript(config)
        elif language == "python":
            return self._export_python(config)
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _export_typescript(self, config: MappingConfiguration) -> str:
        """Export configuration as TypeScript code."""
        lines = [
            f"// Field Mapper: {config.name}",
            f"// Generated: {datetime.now().isoformat()}",
            "",
            "interface LegacyData {",
        ]

        for field in config.legacy_fields:
            lines.append(f"  {field.id}: {self._ts_type(field.field_type)};")
        lines.append("}")
        lines.append("")
        lines.append("interface NewData {")

        for field in config.new_fields:
            lines.append(f"  {field.path.replace('.', '_')}: {self._ts_type(field.field_type)};")
        lines.append("}")
        lines.append("")
        lines.append("export function mapLegacyToNew(legacy: LegacyData): NewData {")
        lines.append("  return {")

        for mapping in config.mappings:
            if not mapping.enabled:
                continue
            new_field = next((f for f in config.new_fields if f.id == mapping.new_field), None)
            if not new_field:
                continue

            field_name = new_field.path.replace(".", "_")
            if len(mapping.legacy_fields) == 1:
                lines.append(f"    {field_name}: legacy.{mapping.legacy_fields[0]},")
            else:
                template = mapping.composite_template or " ".join(f"${{legacy.{fid}}}" for fid in mapping.legacy_fields)
                lines.append(f"    {field_name}: `{template}`,")

        lines.append("  };")
        lines.append("}")

        return "\n".join(lines)

    def _export_python(self, config: MappingConfiguration) -> str:
        """Export configuration as Python code."""
        lines = [
            f'"""Field Mapper: {config.name}"""',
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "from dataclasses import dataclass",
            "from typing import Optional",
            "",
            "@dataclass",
            "class LegacyData:",
        ]

        for field in config.legacy_fields:
            lines.append(f"    {field.id}: {self._py_type(field.field_type)}")
        lines.append("")
        lines.append("@dataclass")
        lines.append("class NewData:")

        for field in config.new_fields:
            lines.append(f"    {field.path.replace('.', '_')}: {self._py_type(field.field_type)}")
        lines.append("")
        lines.append("def map_legacy_to_new(legacy: LegacyData) -> NewData:")
        lines.append("    return NewData(")

        for mapping in config.mappings:
            if not mapping.enabled:
                continue
            new_field = next((f for f in config.new_fields if f.id == mapping.new_field), None)
            if not new_field:
                continue

            field_name = new_field.path.replace(".", "_")
            if len(mapping.legacy_fields) == 1:
                lines.append(f"        {field_name}=legacy.{mapping.legacy_fields[0]},")
            else:
                template = mapping.composite_template or " ".join(f"{{legacy.{fid}}}" for fid in mapping.legacy_fields)
                lines.append(f"        {field_name}=f'{template}',")

        lines.append("    )")

        return "\n".join(lines)

    def _ts_type(self, field_type: FieldType) -> str:
        """Convert FieldType to TypeScript type."""
        mapping = {
            FieldType.STRING: "string",
            FieldType.NUMBER: "number",
            FieldType.BOOLEAN: "boolean",
            FieldType.DATE: "Date",
            FieldType.DATETIME: "Date",
            FieldType.ARRAY: "any[]",
            FieldType.OBJECT: "Record<string, any>",
        }
        return mapping.get(field_type, "any")

    def _py_type(self, field_type: FieldType) -> str:
        """Convert FieldType to Python type."""
        mapping = {
            FieldType.STRING: "str",
            FieldType.NUMBER: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.DATE: "str",
            FieldType.DATETIME: "str",
            FieldType.ARRAY: "list",
            FieldType.OBJECT: "dict",
        }
        return mapping.get(field_type, "Any")
