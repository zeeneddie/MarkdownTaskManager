# FP Component Validator
# IFPUG CPM 4.3.1 compliant validation rules
#
# Validates components against strict IFPUG/NESMA rules:
# - ILF: Internal Logical Files (user data maintained within boundary)
# - EIF: External Interface Files (data from external systems)
# - EI: External Inputs (data entry/updates)
# - EO: External Outputs (reports/derived data)
# - EQ: External Inquiries (read-only queries)
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity of validation issues."""
    ERROR = "error"      # Component should not be counted
    WARNING = "warning"  # Component may be miscounted
    INFO = "info"        # Informational note


@dataclass
class ValidationResult:
    """Result of validating an FP component."""
    is_valid: bool
    component_name: str
    component_type: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def add_issue(
        self,
        severity: ValidationSeverity,
        message: str,
        rule: str = "",
    ):
        """Add a validation issue."""
        self.issues.append({
            "severity": severity.value,
            "message": message,
            "rule": rule,
        })
        if severity == ValidationSeverity.ERROR:
            self.is_valid = False
            self.confidence = 0.0
        elif severity == ValidationSeverity.WARNING:
            self.confidence = min(self.confidence, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "component_name": self.component_name,
            "component_type": self.component_type,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "confidence": round(self.confidence, 2),
        }


class FPComponentValidator:
    """
    Validate FP components against IFPUG CPM 4.3.1 rules.

    Key validation rules:
    - ILF must be user-identifiable data maintained within boundary
    - EIF must be external data referenced read-only
    - Source code files are NEVER data files (ILF/EIF)
    - Code patterns/helpers are NEVER transactions (EI/EO/EQ)

    Usage:
        validator = FPComponentValidator()

        # Validate ILF
        result = validator.validate_ilf(
            name="Customer Table",
            description="Customer master data",
            dets=15,
            rets=3
        )

        # This should FAIL:
        result = validator.validate_eif(
            name="ASP Source Files",
            description="Source code being analyzed"
        )
        # result.is_valid == False
        # result.issues[0]["message"] contains explanation
    """

    # Patterns that indicate source code (NOT data files)
    SOURCE_CODE_PATTERNS = [
        r"\.asp$", r"\.vb$", r"\.cs$", r"\.py$", r"\.js$", r"\.ts$",
        r"\.java$", r"\.cpp$", r"\.c$", r"\.h$", r"\.php$", r"\.rb$",
        r"source\s*file", r"source\s*code", r"code\s*file",
        r"script", r"module", r"class\s*file", r"library",
    ]

    # Patterns that indicate code constructs (NOT transactions)
    CODE_CONSTRUCT_PATTERNS = [
        r"helper", r"function", r"method", r"procedure", r"routine",
        r"subroutine", r"class", r"module", r"template", r"pattern",
        r"utility", r"library", r"framework", r"cleanup", r"init",
    ]

    # Valid data file patterns
    DATA_FILE_PATTERNS = [
        r"table", r"database", r"record", r"entity", r"master\s*data",
        r"transaction\s*log", r"configuration", r"settings", r"parameter",
        r"customer", r"order", r"invoice", r"product", r"employee",
    ]

    # Valid transaction patterns
    TRANSACTION_PATTERNS = [
        r"create", r"add", r"insert", r"new", r"register",
        r"update", r"modify", r"edit", r"change",
        r"delete", r"remove", r"cancel",
        r"report", r"list", r"display", r"export", r"print",
        r"search", r"query", r"lookup", r"find", r"retrieve",
    ]

    def validate_ilf(
        self,
        name: str,
        description: str = "",
        dets: int = 0,
        rets: int = 0,
        source_info: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate Internal Logical File (ILF) component.

        IFPUG CPM 4.3.1 ILF Rules:
        1. Must be a user-identifiable group of logically related data
        2. Must reside entirely within the application boundary
        3. Must be maintained (created/updated/deleted) through EIs
        4. Must NOT be source code, configuration, or temporary data

        Args:
            name: Component name
            description: Component description
            dets: Data Element Types count
            rets: Record Element Types count
            source_info: Optional source location info

        Returns:
            ValidationResult with is_valid and any issues
        """
        result = ValidationResult(
            is_valid=True,
            component_name=name,
            component_type="ILF",
        )

        combined_text = f"{name} {description}".lower()

        # Rule 1: Check for source code patterns (INVALID)
        for pattern in self.SOURCE_CODE_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"'{name}' appears to be source code, not a data file. "
                    "Source code being analyzed is INPUT to your process, not an ILF. "
                    "ILF must be user-maintained DATA within your application.",
                    "CPM 4.3.1 Section 5.2.1"
                )
                result.suggestions.append(
                    "Remove this component. Source code analysis has no FP - "
                    "use Time & Materials estimation instead."
                )
                return result

        # Rule 2: Check for code construct patterns (INVALID)
        for pattern in self.CODE_CONSTRUCT_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"'{name}' appears to be a code construct (helper/function/class), not data. "
                    "ILF must be a logical group of DATA, not code patterns or utilities.",
                    "CPM 4.3.1 Section 5.2.1"
                )
                result.suggestions.append(
                    "If this is a new function being added, count it as an EI (External Input) "
                    "in an Enhancement FP calculation, not as an ILF."
                )
                return result

        # Rule 3: Check for valid data patterns (ENCOURAGED)
        has_data_pattern = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in self.DATA_FILE_PATTERNS
        )
        if not has_data_pattern:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"'{name}' doesn't clearly indicate user data. "
                "Verify this is a user-identifiable logical data group.",
                "CPM 4.3.1 Section 5.2.1"
            )
            result.suggestions.append(
                "ILF examples: Customer Table, Order Records, Product Catalog, "
                "Employee Master, Configuration Settings (if user-maintained)"
            )

        # Rule 4: Validate DET/RET counts
        if dets < 1:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"ILF '{name}' has {dets} DETs. Must have at least 1 DET.",
                "CPM 4.3.1 Section 5.2.3"
            )

        if rets < 1:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"ILF '{name}' has {rets} RETs. Must have at least 1 RET.",
                "CPM 4.3.1 Section 5.2.4"
            )

        # Rule 5: Check for reasonable complexity
        if dets > 100:
            result.add_issue(
                ValidationSeverity.INFO,
                f"ILF '{name}' has {dets} DETs which is unusually high. "
                "Consider if this should be split into multiple ILFs.",
                "CPM 4.3.1 Best Practice"
            )

        return result

    def validate_eif(
        self,
        name: str,
        description: str = "",
        dets: int = 0,
        rets: int = 0,
        source_info: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate External Interface File (EIF) component.

        IFPUG CPM 4.3.1 EIF Rules:
        1. Must be a user-identifiable group of logically related data
        2. Must reside OUTSIDE the application boundary
        3. Must be referenced for read-only purposes
        4. Must be maintained by ANOTHER application
        5. Must NOT be source code being analyzed

        Args:
            name: Component name
            description: Component description
            dets: Data Element Types count
            rets: Record Element Types count
            source_info: Optional source location info

        Returns:
            ValidationResult with is_valid and any issues
        """
        result = ValidationResult(
            is_valid=True,
            component_name=name,
            component_type="EIF",
        )

        combined_text = f"{name} {description}".lower()

        # Rule 1: Check for source code patterns (CRITICAL - most common error)
        for pattern in self.SOURCE_CODE_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"'{name}' appears to be source code. "
                    "Source code you are ANALYZING is NOT an EIF! "
                    "EIF must be external DATA maintained by another system that you READ. "
                    "Your analysis tool reads source code as INPUT, not as referenced data.",
                    "CPM 4.3.1 Section 5.3.1"
                )
                result.suggestions.append(
                    "Code analysis/audit work has NO Function Points. "
                    "Use Time & Materials estimation for analysis work."
                )
                return result

        # Rule 2: Check for code construct patterns (INVALID)
        for pattern in self.CODE_CONSTRUCT_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"'{name}' appears to be a code construct, not external data. "
                    "EIF must be DATA from an external system, not code patterns.",
                    "CPM 4.3.1 Section 5.3.1"
                )
                return result

        # Rule 3: Verify external ownership
        internal_indicators = ["our", "my", "this app", "internal", "local"]
        for indicator in internal_indicators:
            if indicator in combined_text:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"'{name}' may be internal data based on description. "
                    "EIF must be maintained by an EXTERNAL system.",
                    "CPM 4.3.1 Section 5.3.1"
                )
                result.suggestions.append(
                    "If this data is maintained by YOUR application, count it as ILF, not EIF."
                )

        # Rule 4: Validate DET/RET counts
        if dets < 1:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"EIF '{name}' has {dets} DETs. Must have at least 1 DET.",
                "CPM 4.3.1 Section 5.3.3"
            )

        return result

    def validate_ei(
        self,
        name: str,
        description: str = "",
        dets: int = 0,
        ftrs: int = 0,
        source_info: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate External Input (EI) component.

        IFPUG CPM 4.3.1 EI Rules:
        1. Must process data or control information from outside boundary
        2. Primary intent: maintain ILF and/or alter system behavior
        3. Must be uniquely identifiable by user
        4. Must be self-contained and leave ILF in consistent state

        Args:
            name: Component name
            description: Component description
            dets: Data Element Types count
            ftrs: File Types Referenced count
            source_info: Optional source location info

        Returns:
            ValidationResult with is_valid and any issues
        """
        result = ValidationResult(
            is_valid=True,
            component_name=name,
            component_type="EI",
        )

        combined_text = f"{name} {description}".lower()

        # Check for valid transaction patterns
        has_input_pattern = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in ["create", "add", "insert", "new", "register",
                     "update", "modify", "edit", "change", "save",
                     "delete", "remove", "cancel", "process", "submit"]
        )

        if not has_input_pattern:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"'{name}' doesn't clearly indicate a data entry/update transaction. "
                "Verify this is a user-initiated data modification.",
                "CPM 4.3.1 Section 6.1.1"
            )

        # Check for read-only patterns (should be EQ, not EI)
        readonly_patterns = ["view", "display", "show", "get", "retrieve", "list", "query"]
        for pattern in readonly_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"'{name}' may be read-only. If no ILF is modified, "
                    "consider counting as EQ (External Inquiry) instead of EI.",
                    "CPM 4.3.1 Section 6.1.1"
                )
                break

        # Validate FTR count
        if ftrs < 1:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"EI '{name}' references 0 FTRs. EI should reference at least 1 ILF/EIF.",
                "CPM 4.3.1 Section 6.1.3"
            )

        return result

    def validate_eo(
        self,
        name: str,
        description: str = "",
        dets: int = 0,
        ftrs: int = 0,
        source_info: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate External Output (EO) component.

        IFPUG CPM 4.3.1 EO Rules:
        1. Must send data/control information outside boundary
        2. Must include derived data OR update ILF OR alter system behavior
        3. Must be uniquely identifiable by user
        4. Processing logic must be unique from other EOs

        Args:
            name: Component name
            description: Component description
            dets: Data Element Types count
            ftrs: File Types Referenced count
            source_info: Optional source location info

        Returns:
            ValidationResult with is_valid and any issues
        """
        result = ValidationResult(
            is_valid=True,
            component_name=name,
            component_type="EO",
        )

        combined_text = f"{name} {description}".lower()

        # Check for output patterns
        output_patterns = ["report", "export", "print", "generate", "calculate",
                         "summary", "total", "analysis", "derive"]
        has_output_pattern = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in output_patterns
        )

        if not has_output_pattern:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"'{name}' doesn't clearly indicate an output/report. "
                "Verify this produces derived data or external output.",
                "CPM 4.3.1 Section 6.2.1"
            )

        # Check for simple retrieval (should be EQ)
        simple_retrieval = ["list", "view", "display", "show"]
        is_simple = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in simple_retrieval
        )
        has_derivation = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in ["calculate", "compute", "derive", "total", "sum", "average"]
        )

        if is_simple and not has_derivation:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"'{name}' may be simple retrieval without derived data. "
                "EO requires derived data or ILF update. Consider EQ instead.",
                "CPM 4.3.1 Section 6.2.1"
            )

        return result

    def validate_eq(
        self,
        name: str,
        description: str = "",
        dets: int = 0,
        ftrs: int = 0,
        source_info: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate External Inquiry (EQ) component.

        IFPUG CPM 4.3.1 EQ Rules:
        1. Must send data/control information outside boundary
        2. Must NOT contain derived data
        3. Must NOT update ILF
        4. Must retrieve data from ILF/EIF
        5. Must be uniquely identifiable by user

        Args:
            name: Component name
            description: Component description
            dets: Data Element Types count
            ftrs: File Types Referenced count
            source_info: Optional source location info

        Returns:
            ValidationResult with is_valid and any issues
        """
        result = ValidationResult(
            is_valid=True,
            component_name=name,
            component_type="EQ",
        )

        combined_text = f"{name} {description}".lower()

        # Check for inquiry patterns
        inquiry_patterns = ["search", "find", "lookup", "query", "retrieve",
                          "get", "fetch", "display", "view", "list"]
        has_inquiry_pattern = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in inquiry_patterns
        )

        if not has_inquiry_pattern:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"'{name}' doesn't clearly indicate a query/lookup. "
                "Verify this is a read-only data retrieval.",
                "CPM 4.3.1 Section 6.3.1"
            )

        # Check for derivation (should be EO)
        derivation_patterns = ["calculate", "compute", "total", "sum", "average", "derive"]
        has_derivation = any(
            re.search(p, combined_text, re.IGNORECASE)
            for p in derivation_patterns
        )

        if has_derivation:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"'{name}' appears to include derived data. "
                "EQ must NOT contain derived data. Consider counting as EO instead.",
                "CPM 4.3.1 Section 6.3.1"
            )

        return result

    def validate_batch(
        self,
        components: List[Dict[str, Any]],
    ) -> Tuple[List[ValidationResult], Dict[str, Any]]:
        """
        Validate a batch of components.

        Args:
            components: List of component dicts with keys:
                - type: ILF, EIF, EI, EO, EQ
                - name: Component name
                - description: Component description
                - dets: Data Element Types
                - rets/ftrs: Record Element Types / File Types Referenced

        Returns:
            Tuple of (validation results, summary statistics)
        """
        results = []
        validators = {
            "ILF": self.validate_ilf,
            "EIF": self.validate_eif,
            "EI": self.validate_ei,
            "EO": self.validate_eo,
            "EQ": self.validate_eq,
        }

        for comp in components:
            comp_type = comp.get("type", "").upper()
            if comp_type not in validators:
                result = ValidationResult(
                    is_valid=False,
                    component_name=comp.get("name", "Unknown"),
                    component_type=comp_type,
                )
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Unknown component type: {comp_type}",
                    "CPM 4.3.1"
                )
                results.append(result)
                continue

            validator = validators[comp_type]
            result = validator(
                name=comp.get("name", ""),
                description=comp.get("description", ""),
                dets=comp.get("dets", 0),
                rets=comp.get("rets", 0) if comp_type in ["ILF", "EIF"] else 0,
                ftrs=comp.get("ftrs", 0) if comp_type in ["EI", "EO", "EQ"] else 0,
            )
            results.append(result)

        # Generate summary
        summary = {
            "total_components": len(components),
            "valid_count": sum(1 for r in results if r.is_valid),
            "invalid_count": sum(1 for r in results if not r.is_valid),
            "warning_count": sum(
                1 for r in results
                if any(i["severity"] == "warning" for i in r.issues)
            ),
            "average_confidence": (
                sum(r.confidence for r in results) / len(results)
                if results else 0
            ),
        }

        return results, summary
