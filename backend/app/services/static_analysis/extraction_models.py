# backend/app/services/static_analysis/extraction_models.py
"""
Extraction Models for Multi-Language Business Rule Extraction.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime


class ExtractionTier(Enum):
    """Customer extraction tiers determining LLM access levels."""
    FREE = "free"              # AST + Regex only, no LLM
    BASIC = "basic"            # + Ollama local LLMs
    STANDARD = "standard"      # + Groq, Gemini
    PROFESSIONAL = "professional"  # + OpenAI GPT-5.2
    PREMIUM = "premium"        # + Claude Opus, human review


class RuleType(Enum):
    """Types of business rules detected."""
    VALIDATION = "validation"       # Input validation rules
    AUTHORIZATION = "authorization" # Access control rules
    SCHEDULING = "scheduling"       # Date/time scheduling rules
    WORKFLOW = "workflow"           # State transitions
    BRANCHING = "branching"         # Select Case / switch logic
    THRESHOLD = "threshold"         # Numeric boundary checks
    DATA_ACCESS = "data_access"     # Database operations
    STATE_MANAGEMENT = "state_management"  # Session/state handling
    ERROR_HANDLING = "error_handling"  # Exception/error handling
    NAVIGATION = "navigation"       # Redirects, navigation
    CALCULATION = "calculation"     # Business calculations
    CONSTRAINT = "constraint"       # Business constraints
    DERIVATION = "derivation"       # Derived values


class ExtractionMethod(Enum):
    """Method used to extract the rule."""
    AST = "ast"           # Abstract Syntax Tree parsing
    REGEX = "regex"       # Regular expression pattern
    LLM = "llm"           # LLM-assisted extraction
    HYBRID = "hybrid"     # Combination of methods


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
    VBNET = "vbnet"
    CLASSIC_ASP = "asp"
    ASPX = "aspx"  # ASP.NET WebForms markup (.aspx, .ascx)
    VBSCRIPT = "vbscript"
    TSQL = "tsql"
    PLSQL = "plsql"
    JAVA = "java"
    GO = "go"
    PHP = "php"
    VB6 = "vb6"  # Visual Basic 6 legacy


# Extension to Language mapping
EXTENSION_LANGUAGE_MAP: Dict[str, Language] = {
    '.py': Language.PYTHON,
    '.js': Language.JAVASCRIPT,
    '.jsx': Language.JAVASCRIPT,
    '.ts': Language.TYPESCRIPT,
    '.tsx': Language.TYPESCRIPT,
    '.cs': Language.CSHARP,
    '.vb': Language.VBNET,
    '.aspx.vb': Language.VBNET,
    '.ascx.vb': Language.VBNET,
    '.aspx.cs': Language.CSHARP,
    '.asp': Language.CLASSIC_ASP,
    '.asa': Language.CLASSIC_ASP,
    '.vbs': Language.VBSCRIPT,
    '.sql': Language.TSQL,
    '.prc': Language.TSQL,
    '.pkg': Language.PLSQL,
    '.pkb': Language.PLSQL,
    '.pks': Language.PLSQL,
    '.java': Language.JAVA,
    '.go': Language.GO,
    '.php': Language.PHP,
    # VB6 legacy
    '.frm': Language.VB6,
    '.bas': Language.VB6,
    '.cls': Language.VB6,
    '.vbp': Language.VB6,
    '.ctl': Language.VB6,
}


@dataclass
class BusinessRule:
    """
    A detected business rule with full metadata.

    Enhanced from original to support:
    - Workflow context linking
    - Traceability to epics/features/stories
    - Multi-language extraction
    - Tier-aware confidence scoring
    """
    id: str                          # "BR-001"
    rule_type: RuleType              # validation, authorization, etc.
    condition: str                   # IF part / trigger condition
    action: str                      # THEN part / resulting action
    source_file: str                 # File path
    source_lines: Tuple[int, int]    # (start_line, end_line)
    confidence: float                # 0.0-1.0 confidence score
    natural_language: str            # Human-readable description

    # Additional metadata
    variables_involved: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)  # Domain entities
    language: Optional[Language] = None
    extraction_method: ExtractionMethod = ExtractionMethod.REGEX
    extraction_tier: ExtractionTier = ExtractionTier.FREE

    # Workflow context (for correlation)
    workflow_context: Optional[str] = None    # "appointment_create"
    workflow_step: Optional[int] = None       # Step number in workflow

    # Traceability (linked after extraction)
    epic_id: Optional[str] = None             # "EP-001"
    feature_id: Optional[str] = None          # "FT-001"
    story_id: Optional[str] = None            # "US-001"

    # Code context
    code_snippet: Optional[str] = None        # Original code
    parent_function: Optional[str] = None     # Containing function/method
    parent_class: Optional[str] = None        # Containing class
    region: Optional[str] = None              # VB.NET #Region context

    # Validation metadata
    validated_by_llm: bool = False
    llm_validation_result: Optional[str] = None

    # Timestamps
    extracted_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "rule_type": self.rule_type.value,
            "condition": self.condition,
            "action": self.action,
            "source_file": self.source_file,
            "source_lines": list(self.source_lines),
            "confidence": self.confidence,
            "natural_language": self.natural_language,
            "variables_involved": self.variables_involved,
            "related_entities": self.related_entities,
            "language": self.language.value if self.language else None,
            "extraction_method": self.extraction_method.value,
            "extraction_tier": self.extraction_tier.value,
            "workflow_context": self.workflow_context,
            "workflow_step": self.workflow_step,
            "epic_id": self.epic_id,
            "feature_id": self.feature_id,
            "story_id": self.story_id,
            "code_snippet": self.code_snippet,
            "parent_function": self.parent_function,
            "parent_class": self.parent_class,
            "region": self.region,
            "validated_by_llm": self.validated_by_llm,
            "extracted_at": self.extracted_at.isoformat(),
        }


@dataclass
class CodeSymbol:
    """A code symbol (class, method, property, etc.)."""
    name: str
    symbol_type: str  # class, method, property, function, enum, sub
    line_start: int
    line_end: int
    docstring: str = ""
    parent: str = ""
    language: Optional[Language] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol_type": self.symbol_type,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
            "parent": self.parent,
            "language": self.language.value if self.language else None,
        }


@dataclass
class NFRIndicator:
    """Non-Functional Requirement indicator."""
    id: str
    category: str  # performance, security, usability, reliability, maintainability
    description: str
    metric: str
    source_text: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "metric": self.metric,
            "source_text": self.source_text,
            "source_file": self.source_file,
            "source_line": self.source_line,
        }


@dataclass
class ExtractionResult:
    """Result of business rule extraction from a single file or directory."""
    source_path: str
    language: Language
    extraction_tier: ExtractionTier
    extraction_method: ExtractionMethod

    # Extracted data
    business_rules: List[BusinessRule]
    code_symbols: List[CodeSymbol]
    nfr_indicators: List[NFRIndicator]

    # Statistics
    lines_of_code: int = 0
    files_processed: int = 1
    extraction_time_ms: int = 0

    # Aggregations
    rules_by_type: Dict[str, int] = field(default_factory=dict)
    rules_by_confidence: Dict[str, int] = field(default_factory=dict)  # high/medium/low

    # Errors/warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate aggregations after initialization."""
        if not self.rules_by_type:
            self._calculate_aggregations()

    def _calculate_aggregations(self):
        """Calculate rule type and confidence distributions."""
        # Rules by type
        for rule in self.business_rules:
            type_name = rule.rule_type.value
            self.rules_by_type[type_name] = self.rules_by_type.get(type_name, 0) + 1

        # Rules by confidence level
        high = sum(1 for r in self.business_rules if r.confidence >= 0.8)
        medium = sum(1 for r in self.business_rules if 0.5 <= r.confidence < 0.8)
        low = sum(1 for r in self.business_rules if r.confidence < 0.5)
        self.rules_by_confidence = {"high": high, "medium": medium, "low": low}

    @property
    def total_rules(self) -> int:
        return len(self.business_rules)

    @property
    def high_confidence_rules(self) -> int:
        return self.rules_by_confidence.get("high", 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self.source_path,
            "language": self.language.value,
            "extraction_tier": self.extraction_tier.value,
            "extraction_method": self.extraction_method.value,
            "business_rules": [r.to_dict() for r in self.business_rules],
            "code_symbols": [s.to_dict() for s in self.code_symbols],
            "nfr_indicators": [n.to_dict() for n in self.nfr_indicators],
            "lines_of_code": self.lines_of_code,
            "files_processed": self.files_processed,
            "extraction_time_ms": self.extraction_time_ms,
            "total_rules": self.total_rules,
            "high_confidence_rules": self.high_confidence_rules,
            "rules_by_type": self.rules_by_type,
            "rules_by_confidence": self.rules_by_confidence,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class MultiFileExtractionResult:
    """Result of extraction across multiple files."""
    project_id: Optional[int]
    base_path: str
    extraction_tier: ExtractionTier

    # Per-file results
    file_results: Dict[str, ExtractionResult]

    # Aggregated rules
    all_rules: List[BusinessRule] = field(default_factory=list)
    all_symbols: List[CodeSymbol] = field(default_factory=list)
    all_nfrs: List[NFRIndicator] = field(default_factory=list)

    # Statistics
    total_files: int = 0
    total_lines: int = 0
    total_extraction_time_ms: int = 0

    # Language breakdown
    files_by_language: Dict[str, int] = field(default_factory=dict)
    rules_by_language: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Aggregate all results."""
        self._aggregate_results()

    def _aggregate_results(self):
        """Aggregate results from all files."""
        for file_path, result in self.file_results.items():
            self.all_rules.extend(result.business_rules)
            self.all_symbols.extend(result.code_symbols)
            self.all_nfrs.extend(result.nfr_indicators)
            self.total_lines += result.lines_of_code
            self.total_extraction_time_ms += result.extraction_time_ms

            lang = result.language.value
            self.files_by_language[lang] = self.files_by_language.get(lang, 0) + 1
            self.rules_by_language[lang] = self.rules_by_language.get(lang, 0) + len(result.business_rules)

        self.total_files = len(self.file_results)

    @property
    def total_rules(self) -> int:
        return len(self.all_rules)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "base_path": self.base_path,
            "extraction_tier": self.extraction_tier.value,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "total_rules": self.total_rules,
            "total_extraction_time_ms": self.total_extraction_time_ms,
            "files_by_language": self.files_by_language,
            "rules_by_language": self.rules_by_language,
            "rules": [r.to_dict() for r in self.all_rules],
            "symbols": [s.to_dict() for s in self.all_symbols],
            "nfrs": [n.to_dict() for n in self.all_nfrs],
        }


# Tier-based LLM provider mapping
TIER_LLM_PROVIDERS: Dict[ExtractionTier, List[str]] = {
    ExtractionTier.FREE: [],
    ExtractionTier.BASIC: ["ollama"],
    ExtractionTier.STANDARD: ["ollama", "groq", "gemini"],
    ExtractionTier.PROFESSIONAL: ["ollama", "groq", "gemini", "openai"],
    ExtractionTier.PREMIUM: ["ollama", "groq", "gemini", "openai", "anthropic"],
}


# Target confidence by tier
TIER_TARGET_CONFIDENCE: Dict[ExtractionTier, Tuple[float, float]] = {
    ExtractionTier.FREE: (0.70, 0.75),
    ExtractionTier.BASIC: (0.75, 0.80),
    ExtractionTier.STANDARD: (0.80, 0.85),
    ExtractionTier.PROFESSIONAL: (0.85, 0.90),
    ExtractionTier.PREMIUM: (0.90, 0.95),
}


# =============================================================================
# Phase 3: Rule Correlation Models
# =============================================================================

class CRUDOperation(Enum):
    """CRUD operation types for workflow detection."""
    CREATE = "create"    # INSERT, Add, New
    READ = "read"        # SELECT, Get, View, List
    UPDATE = "update"    # UPDATE, Edit, Modify
    DELETE = "delete"    # DELETE, Remove
    COPY = "copy"        # READ + CREATE (clone operation)
    SEARCH = "search"    # Complex queries, filtering
    EXPORT = "export"    # Data export operations
    IMPORT = "import"    # Data import operations


class WorkflowType(Enum):
    """Types of detected business workflows."""
    CRUD = "crud"                    # Standard CRUD operations
    STATE_MACHINE = "state_machine"  # State transitions
    APPROVAL = "approval"            # Approval/review workflows
    SCHEDULING = "scheduling"        # Scheduling/calendar workflows
    NOTIFICATION = "notification"    # Notification workflows
    INTEGRATION = "integration"      # External system integration
    REPORTING = "reporting"          # Report generation


@dataclass
class Entity:
    """
    A domain entity detected from business rules.

    Entities are extracted from:
    - Table names (taAfspraak -> Afspraak)
    - Class names (AppointmentService -> Appointment)
    - Variable patterns (intAgendaID -> Agenda)
    """
    id: str                          # "ENT-001"
    name: str                        # "Afspraak" (normalized)
    original_names: List[str] = field(default_factory=list)  # ["taAfspraak", "Appointment"]
    entity_type: str = "domain"      # domain, lookup, audit, config

    # Linked rules
    rule_ids: List[str] = field(default_factory=list)

    # CRUD coverage
    has_create: bool = False
    has_read: bool = False
    has_update: bool = False
    has_delete: bool = False

    # Statistics
    rule_count: int = 0
    files_referenced: List[str] = field(default_factory=list)

    @property
    def crud_coverage(self) -> str:
        """Get CRUD coverage as string (e.g., 'CRUD', 'CR', 'R')."""
        coverage = ""
        if self.has_create: coverage += "C"
        if self.has_read: coverage += "R"
        if self.has_update: coverage += "U"
        if self.has_delete: coverage += "D"
        return coverage or "-"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "original_names": self.original_names,
            "entity_type": self.entity_type,
            "rule_ids": self.rule_ids,
            "crud_coverage": self.crud_coverage,
            "has_create": self.has_create,
            "has_read": self.has_read,
            "has_update": self.has_update,
            "has_delete": self.has_delete,
            "rule_count": self.rule_count,
            "files_referenced": self.files_referenced,
        }


@dataclass
class Workflow:
    """
    A detected business workflow grouping related rules.

    Workflows represent a coherent set of operations on an entity,
    such as "Appointment Management" with Create, View, Edit, Delete.
    """
    id: str                          # "WF-001"
    name: str                        # "Appointment Management"
    workflow_type: WorkflowType = WorkflowType.CRUD

    # Primary entity
    primary_entity: Optional[str] = None  # Entity name

    # Operations in this workflow
    operations: List[CRUDOperation] = field(default_factory=list)

    # Rules grouped by operation
    rules_by_operation: Dict[str, List[str]] = field(default_factory=dict)

    # All rule IDs in this workflow
    rule_ids: List[str] = field(default_factory=list)

    # Authorization pattern
    auth_pattern: Optional[str] = None  # "intCan{Operation}" pattern
    auth_rules: List[str] = field(default_factory=list)

    # Validation rules
    validation_rules: List[str] = field(default_factory=list)

    # Files involved
    source_files: List[str] = field(default_factory=list)

    # Statistics
    total_rules: int = 0
    confidence: float = 0.0  # Workflow detection confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "workflow_type": self.workflow_type.value,
            "primary_entity": self.primary_entity,
            "operations": [op.value for op in self.operations],
            "rules_by_operation": self.rules_by_operation,
            "rule_ids": self.rule_ids,
            "auth_pattern": self.auth_pattern,
            "auth_rules": self.auth_rules,
            "validation_rules": self.validation_rules,
            "source_files": self.source_files,
            "total_rules": self.total_rules,
            "confidence": self.confidence,
        }


@dataclass
class RuleRelationship:
    """
    A relationship between two business rules.

    Types:
    - depends_on: Rule A requires Rule B to pass first
    - guards: Rule A is an authorization check for Rule B
    - validates: Rule A validates input for Rule B
    - triggers: Rule A triggers Rule B
    - shares_entity: Rules operate on the same entity
    """
    source_rule_id: str
    target_rule_id: str
    relationship_type: str  # depends_on, guards, validates, triggers, shares_entity
    confidence: float = 0.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_rule_id": self.source_rule_id,
            "target_rule_id": self.target_rule_id,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class CorrelationResult:
    """
    Result of rule correlation analysis.

    Contains detected workflows, entities, and rule relationships.
    """
    project_id: Optional[int] = None

    # Detected structures
    entities: List[Entity] = field(default_factory=list)
    workflows: List[Workflow] = field(default_factory=list)
    relationships: List[RuleRelationship] = field(default_factory=list)

    # Source rules analyzed
    total_rules_analyzed: int = 0
    rules_correlated: int = 0  # Rules assigned to workflows
    rules_orphaned: int = 0    # Rules not fitting any workflow

    # Statistics
    entities_detected: int = 0
    workflows_detected: int = 0
    relationships_detected: int = 0

    # Processing info
    correlation_time_ms: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate statistics."""
        self.entities_detected = len(self.entities)
        self.workflows_detected = len(self.workflows)
        self.relationships_detected = len(self.relationships)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "entities": [e.to_dict() for e in self.entities],
            "workflows": [w.to_dict() for w in self.workflows],
            "relationships": [r.to_dict() for r in self.relationships],
            "total_rules_analyzed": self.total_rules_analyzed,
            "rules_correlated": self.rules_correlated,
            "rules_orphaned": self.rules_orphaned,
            "entities_detected": self.entities_detected,
            "workflows_detected": self.workflows_detected,
            "relationships_detected": self.relationships_detected,
            "correlation_time_ms": self.correlation_time_ms,
            "errors": self.errors,
            "warnings": self.warnings,
        }
