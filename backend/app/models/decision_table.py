"""
Decision Table Models - Fase 25: Business Logic Extraction

Models for representing decision tables extracted from nested IF-THEN-ELSE logic
in legacy code. Supports export to DMN XML, JSON, and Markdown formats.

Author: Claude Code (Week 138 - Fase 25)
Date: 2026-01-01
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class HitPolicy(str, Enum):
    """DMN hit policy for decision tables"""
    UNIQUE = "U"  # Only one rule can match
    FIRST = "F"   # First matching rule wins
    PRIORITY = "P"  # Priority order determines winner
    ANY = "A"     # Any rule can match (all must have same output)
    COLLECT = "C"  # Collect all matching outputs
    RULE_ORDER = "R"  # Rules evaluated in order


class ConditionOperator(str, Enum):
    """Operators for conditions"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUALS = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUALS = "<="
    IN = "in"
    NOT_IN = "not in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    MATCHES = "matches"  # Regex
    ANY = "-"  # DMN: any value matches


class DecisionTableOutputFormat(str, Enum):
    """Output formats for decision tables"""
    DMN_XML = "dmn_xml"
    DMN_JSON = "dmn_json"
    MARKDOWN = "markdown"
    CSV = "csv"
    EXCEL = "excel"


@dataclass
class InputColumn:
    """A condition/input column in a decision table"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""  # e.g., "customerType"
    label: str = ""  # e.g., "Customer Type"
    type_ref: str = "string"  # DMN type reference
    allowed_values: List[str] = field(default_factory=list)
    source_variable: Optional[str] = None  # Original variable in code
    source_file: Optional[str] = None
    source_line: Optional[int] = None


@dataclass
class OutputColumn:
    """An action/output column in a decision table"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""  # e.g., "discount"
    label: str = ""  # e.g., "Discount Percentage"
    type_ref: str = "string"
    default_value: Optional[str] = None
    source_variable: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None


@dataclass
class ConditionEntry:
    """A single condition entry in a rule row"""
    column_id: str = ""
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Any = None  # The comparison value
    value2: Optional[Any] = None  # For BETWEEN operator
    expression: str = ""  # Original expression if complex


@dataclass
class ActionEntry:
    """A single action/output entry in a rule row"""
    column_id: str = ""
    value: Any = None
    expression: str = ""  # Original expression if complex


@dataclass
class DecisionRule:
    """A single rule (row) in a decision table"""
    id: str = field(default_factory=lambda: str(uuid4()))
    rule_number: int = 0  # 1-based row number
    conditions: List[ConditionEntry] = field(default_factory=list)
    actions: List[ActionEntry] = field(default_factory=list)
    annotation: str = ""  # Description/comment for this rule
    source_code: Optional[str] = None  # Original code snippet
    source_file: Optional[str] = None
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    confidence: float = 1.0  # How confident we are in extraction


@dataclass
class DecisionTableStatistics:
    """Statistics for a decision table"""
    total_rules: int = 0
    total_inputs: int = 0
    total_outputs: int = 0
    unique_conditions: int = 0
    complexity_score: float = 0.0  # Based on rules × conditions
    coverage_estimate: float = 0.0  # Percentage of input space covered
    has_default_rule: bool = False
    has_gaps: bool = False  # True if some combinations not covered
    has_overlaps: bool = False  # True if rules can conflict


@dataclass
class DecisionTable:
    """A complete decision table extracted from code"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Structure
    inputs: List[InputColumn] = field(default_factory=list)
    outputs: List[OutputColumn] = field(default_factory=list)
    rules: List[DecisionRule] = field(default_factory=list)

    # DMN properties
    hit_policy: HitPolicy = HitPolicy.UNIQUE
    aggregation: Optional[str] = None  # For COLLECT policy

    # Source tracking
    source_file: Optional[str] = None
    source_function: Optional[str] = None
    source_class: Optional[str] = None
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    original_code: Optional[str] = None

    # Metadata
    domain: Optional[str] = None  # Business domain
    business_rule_ids: List[str] = field(default_factory=list)  # Linked rules
    statistics: Optional[DecisionTableStatistics] = None
    confidence: float = 1.0
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extracted_by: str = "DecisionTableExtractorService"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "inputs": [
                {
                    "id": inp.id,
                    "name": inp.name,
                    "label": inp.label,
                    "type_ref": inp.type_ref,
                    "allowed_values": inp.allowed_values,
                    "source_variable": inp.source_variable
                }
                for inp in self.inputs
            ],
            "outputs": [
                {
                    "id": out.id,
                    "name": out.name,
                    "label": out.label,
                    "type_ref": out.type_ref,
                    "default_value": out.default_value
                }
                for out in self.outputs
            ],
            "rules": [
                {
                    "id": rule.id,
                    "rule_number": rule.rule_number,
                    "conditions": [
                        {
                            "column_id": c.column_id,
                            "operator": c.operator.value,
                            "value": c.value,
                            "expression": c.expression
                        }
                        for c in rule.conditions
                    ],
                    "actions": [
                        {
                            "column_id": a.column_id,
                            "value": a.value,
                            "expression": a.expression
                        }
                        for a in rule.actions
                    ],
                    "annotation": rule.annotation,
                    "confidence": rule.confidence
                }
                for rule in self.rules
            ],
            "hit_policy": self.hit_policy.value,
            "source_file": self.source_file,
            "source_function": self.source_function,
            "domain": self.domain,
            "statistics": {
                "total_rules": self.statistics.total_rules,
                "total_inputs": self.statistics.total_inputs,
                "total_outputs": self.statistics.total_outputs,
                "complexity_score": self.statistics.complexity_score,
                "has_gaps": self.statistics.has_gaps,
                "has_overlaps": self.statistics.has_overlaps
            } if self.statistics else None,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat()
        }


@dataclass
class DecisionTableExtractionResult:
    """Result of decision table extraction from a codebase"""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None

    # Results
    tables: List[DecisionTable] = field(default_factory=list)

    # Statistics
    total_files_scanned: int = 0
    files_with_tables: int = 0
    total_tables_extracted: int = 0
    total_rules_extracted: int = 0
    average_confidence: float = 0.0

    # Warnings/issues
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "tables": [t.to_dict() for t in self.tables],
            "statistics": {
                "total_files_scanned": self.total_files_scanned,
                "files_with_tables": self.files_with_tables,
                "total_tables_extracted": self.total_tables_extracted,
                "total_rules_extracted": self.total_rules_extracted,
                "average_confidence": self.average_confidence
            },
            "warnings": self.warnings,
            "errors": self.errors,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds
        }
