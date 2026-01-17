"""
Control Flow Logic Detector - Loop/If/Switch/Exception Error Detection.

Fase 36: Detects control flow and logic errors across multiple languages:
- CWE-193: Off-by-One Error
- CWE-835: Loop with Unreachable Exit Condition (Infinite Loop)
- CWE-481: Assigning instead of Comparing
- CWE-483: Incorrect Block Delimitation
- CWE-484: Omitted Break Statement in Switch
- CWE-478: Missing Default Case in Switch
- CWE-1069: Empty Exception Handler
- CWE-459: Incomplete Cleanup

Supports: Python, JavaScript/TypeScript, Java, C#, C/C++, Go, PHP, Ruby
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone

from ..models.findings import (
    SecurityFinding, ScanResult, Severity, ScannerType, Location, SuggestedFix,
)
from .base import BaseScanner

logger = logging.getLogger(__name__)


# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================

@dataclass
class LanguageDefinition:
    """Definition of a programming language for scanning."""
    name: str
    extensions: Set[str]


SUPPORTED_LANGUAGES: Dict[str, LanguageDefinition] = {
    "python": LanguageDefinition(
        name="Python",
        extensions={".py", ".pyw"},
    ),
    "javascript": LanguageDefinition(
        name="JavaScript/TypeScript",
        extensions={".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java", ".jsp"},
    ),
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs", ".cshtml", ".razor"},
    ),
    "cpp": LanguageDefinition(
        name="C/C++",
        extensions={".c", ".cpp", ".h", ".hpp", ".cc", ".cxx"},
    ),
    "go": LanguageDefinition(
        name="Go",
        extensions={".go"},
    ),
    "php": LanguageDefinition(
        name="PHP",
        extensions={".php", ".phtml"},
    ),
    "ruby": LanguageDefinition(
        name="Ruby",
        extensions={".rb", ".erb"},
    ),
}


# =============================================================================
# CONTROL FLOW RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class ControlFlowRule:
    """A control flow logic rule with language-specific patterns."""
    id: str
    title: str
    description: str
    severity: Severity
    cwe_ids: List[str]
    category: str

    # Language-specific regex patterns
    patterns: Dict[str, LanguagePattern]

    # Fix suggestions
    fix_suggestion: str

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

CONTROL_FLOW_RULES: List[ControlFlowRule] = [
    # =========================================================================
    # CF001: Off-by-One Error (CWE-193)
    # =========================================================================
    ControlFlowRule(
        id="CF001",
        title="Off-by-one error: loop uses <= with length/size",
        description=(
            "A loop condition uses <= with length/size/count which typically causes "
            "an off-by-one error. Array indices are 0-based, so valid indices are "
            "0 to length-1. Using <= causes an extra iteration accessing index [length] "
            "which is out of bounds."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-193"],
        category="loop_error",
        patterns={
            "python": LanguagePattern(
                r'(?:for|while)\s+.*<=\s*(?:len\s*\(|\.size|\.count)',
            ),
            "javascript": LanguagePattern(
                r'for\s*\([^;]*;\s*\w+\s*<=\s*\w+\.(?:length|size|count)',
            ),
            "java": LanguagePattern(
                r'for\s*\([^;]*;\s*\w+\s*<=\s*\w+\.(?:length|size\(\)|count\(\))',
            ),
            "csharp": LanguagePattern(
                r'for\s*\([^;]*;\s*\w+\s*<=\s*\w+\.(?:Length|Count)',
            ),
            "cpp": LanguagePattern(
                r'for\s*\([^;]*;\s*\w+\s*<=\s*(?:\w+\.size\(\)|sizeof|strlen)',
            ),
            "go": LanguagePattern(
                r'for\s+.*<=\s*len\s*\(',
            ),
            "php": LanguagePattern(
                r'for\s*\([^;]*;\s*\$\w+\s*<=\s*(?:count|sizeof|strlen)\s*\(',
            ),
        },
        fix_suggestion="Change <= to < in the loop condition. For 0-based indices, use: for (i = 0; i < length; i++)",
    ),

    # =========================================================================
    # CF002: Infinite Loop Risk (CWE-835)
    # =========================================================================
    ControlFlowRule(
        id="CF002",
        title="Potential infinite loop: while(true) without visible break",
        description=(
            "A while(true) or for(;;) loop is detected without an obvious break, return, "
            "or throw statement nearby. While intentional infinite loops exist, "
            "this pattern often indicates a bug where the exit condition was forgotten."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-835"],
        category="loop_error",
        patterns={
            "javascript": LanguagePattern(
                r'while\s*\(\s*true\s*\)\s*\{[^}]{0,100}\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'while\s*\(\s*true\s*\)\s*\{[^}]{0,100}\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'while\s*\(\s*true\s*\)\s*\{[^}]{0,100}\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "cpp": LanguagePattern(
                r'(?:while\s*\(\s*(?:true|1)\s*\)|for\s*\(\s*;\s*;\s*\))\s*\{[^}]{0,100}\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "go": LanguagePattern(
                r'for\s*\{[^}]{0,100}\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "php": LanguagePattern(
                r'while\s*\(\s*true\s*\)\s*\{[^}]{0,100}\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
        },
        fix_suggestion="Ensure infinite loops have a clear exit condition with break, return, or throw.",
        false_positive_patterns=[
            r'break', r'return', r'throw', r'exit', r'continue',
        ],
    ),

    # =========================================================================
    # CF003: Empty Loop Body (semicolon after for/while)
    # =========================================================================
    ControlFlowRule(
        id="CF003",
        title="Empty loop body: semicolon immediately after loop statement",
        description=(
            "A semicolon immediately follows a for or while statement, creating an "
            "empty loop body. The code block after it is NOT part of the loop. "
            "This is almost always a bug caused by an accidental semicolon."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-483"],
        category="loop_error",
        patterns={
            "javascript": LanguagePattern(
                r'(?:for|while)\s*\([^)]+\)\s*;',
            ),
            "java": LanguagePattern(
                r'(?:for|while)\s*\([^)]+\)\s*;',
            ),
            "csharp": LanguagePattern(
                r'(?:for|while)\s*\([^)]+\)\s*;',
            ),
            "cpp": LanguagePattern(
                r'(?:for|while)\s*\([^)]+\)\s*;',
            ),
            "php": LanguagePattern(
                r'(?:for|while)\s*\([^)]+\)\s*;',
            ),
        },
        fix_suggestion="Remove the semicolon after the for/while statement. The loop body should be enclosed in braces {}.",
    ),

    # =========================================================================
    # CF004: Float Loop Counter
    # =========================================================================
    ControlFlowRule(
        id="CF004",
        title="Float or double used as loop counter",
        description=(
            "A floating-point variable (float/double) is used as a loop counter. "
            "Due to floating-point precision issues, the loop may not execute the "
            "expected number of iterations. Accumulated rounding errors can cause "
            "the termination condition to be missed."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-835"],
        category="loop_error",
        patterns={
            "java": LanguagePattern(
                r'for\s*\(\s*(?:float|double)\s+\w+\s*=',
            ),
            "csharp": LanguagePattern(
                r'for\s*\(\s*(?:float|double|decimal)\s+\w+\s*=',
            ),
            "cpp": LanguagePattern(
                r'for\s*\(\s*(?:float|double)\s+\w+\s*=',
            ),
        },
        fix_suggestion="Use integer loop counters. Calculate the floating-point value inside the loop: for (int i = 0; i < n; i++) { double x = i * step; }",
    ),

    # =========================================================================
    # CF010: Assignment in Condition (CWE-481)
    # =========================================================================
    ControlFlowRule(
        id="CF010",
        title="Assignment instead of comparison in condition (= vs ==)",
        description=(
            "A single equals sign (=) is used in a condition where a comparison (== or ===) "
            "was likely intended. This performs an assignment and then evaluates the "
            "assigned value as a boolean, which is rarely the intended behavior."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-481"],
        category="condition_error",
        patterns={
            "javascript": LanguagePattern(
                r'if\s*\(\s*\w+\s*=[^=]',
            ),
            "java": LanguagePattern(
                r'if\s*\(\s*\w+\s*=[^=]',
            ),
            "csharp": LanguagePattern(
                r'if\s*\(\s*\w+\s*=[^=]',
            ),
            "cpp": LanguagePattern(
                r'if\s*\(\s*\w+\s*=[^=]',
            ),
            "php": LanguagePattern(
                r'if\s*\(\s*\$\w+\s*=[^=]',
            ),
        },
        fix_suggestion="Use == or === for comparison. If assignment is intentional, wrap in extra parentheses: if ((x = getValue()))",
        false_positive_patterns=[
            r'\(\s*\w+\s*=\s*\w+\s*\)',  # Intentional assignment with extra parens
        ],
    ),

    # =========================================================================
    # CF011: Dangling Else Ambiguity (CWE-483)
    # =========================================================================
    ControlFlowRule(
        id="CF011",
        title="Dangling else: else without braces may bind to wrong if",
        description=(
            "An if statement without braces has an else clause. When nested ifs exist, "
            "the else binds to the nearest if which may not be the intended one. "
            "This is known as the 'dangling else' problem and causes logic bugs."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-483"],
        category="condition_error",
        patterns={
            "javascript": LanguagePattern(
                r'if\s*\([^)]+\)\s*\n\s*(?!.*\{)\S.*\n\s*else',
                flags=re.MULTILINE
            ),
            "java": LanguagePattern(
                r'if\s*\([^)]+\)\s*\n\s*(?!.*\{)\S.*\n\s*else',
                flags=re.MULTILINE
            ),
            "csharp": LanguagePattern(
                r'if\s*\([^)]+\)\s*\n\s*(?!.*\{)\S.*\n\s*else',
                flags=re.MULTILINE
            ),
            "cpp": LanguagePattern(
                r'if\s*\([^)]+\)\s*\n\s*(?!.*\{)\S.*\n\s*else',
                flags=re.MULTILINE
            ),
        },
        fix_suggestion="Always use braces {} with if statements, especially when else clauses are involved.",
    ),

    # =========================================================================
    # CF020: Missing Break in Switch (CWE-484)
    # =========================================================================
    ControlFlowRule(
        id="CF020",
        title="Missing break in switch case (fall-through)",
        description=(
            "A switch case appears to be missing a break, return, or throw statement, "
            "causing unintentional fall-through to the next case. While sometimes "
            "intentional, missing breaks are a common source of bugs."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-484"],
        category="switch_error",
        patterns={
            "javascript": LanguagePattern(
                r'case\s+[^:]+:\s*\n(?:[^}]*?)(?=case\s+|default\s*:)',
                flags=re.MULTILINE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'case\s+[^:]+:\s*\n(?:[^}]*?)(?=case\s+|default\s*:)',
                flags=re.MULTILINE | re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'case\s+[^:]+:\s*\n(?:[^}]*?)(?=case\s+|default\s*:)',
                flags=re.MULTILINE | re.DOTALL
            ),
            "cpp": LanguagePattern(
                r'case\s+[^:]+:\s*\n(?:[^}]*?)(?=case\s+|default\s*:)',
                flags=re.MULTILINE | re.DOTALL
            ),
            "php": LanguagePattern(
                r'case\s+[^:]+:\s*\n(?:[^}]*?)(?=case\s+|default\s*:)',
                flags=re.MULTILINE | re.DOTALL
            ),
        },
        fix_suggestion="Add break, return, or throw at the end of each case. If fall-through is intentional, add a // fallthrough comment.",
        false_positive_patterns=[
            r'break\s*;', r'return', r'throw', r'exit', r'// fall',
            r'/\* fall', r'goto',
        ],
    ),

    # =========================================================================
    # CF021: Missing Default Case (CWE-478)
    # =========================================================================
    ControlFlowRule(
        id="CF021",
        title="Missing default case in switch statement",
        description=(
            "A switch statement does not have a default case. Without a default case, "
            "unexpected input values are silently ignored, which can lead to bugs "
            "and security vulnerabilities when new enum values are added."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-478"],
        category="switch_error",
        patterns={
            "javascript": LanguagePattern(
                r'switch\s*\([^)]+\)\s*\{(?:(?!default\s*:)[^}])*\}',
                flags=re.DOTALL
            ),
            "java": LanguagePattern(
                r'switch\s*\([^)]+\)\s*\{(?:(?!default\s*:)[^}])*\}',
                flags=re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'switch\s*\([^)]+\)\s*\{(?:(?!default\s*:)[^}])*\}',
                flags=re.DOTALL
            ),
            "cpp": LanguagePattern(
                r'switch\s*\([^)]+\)\s*\{(?:(?!default\s*:)[^}])*\}',
                flags=re.DOTALL
            ),
            "php": LanguagePattern(
                r'switch\s*\([^)]+\)\s*\{(?:(?!default\s*:)[^}])*\}',
                flags=re.DOTALL
            ),
            "go": LanguagePattern(
                r'switch\s+[^{]*\{(?:(?!default\s*:)[^}])*\}',
                flags=re.DOTALL
            ),
        },
        fix_suggestion="Add a default case to handle unexpected values. At minimum, log or throw an error for unexpected inputs.",
    ),

    # =========================================================================
    # CF022: Enum Case Not Exhaustive
    # =========================================================================
    ControlFlowRule(
        id="CF022",
        title="Switch on enum may not cover all values",
        description=(
            "A switch statement operates on an enum type but may not handle all "
            "possible values. When new enum values are added, this switch will "
            "silently ignore them, potentially causing bugs."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-478"],
        category="switch_error",
        patterns={
            "java": LanguagePattern(
                r'switch\s*\(\s*\w+(?:\.\w+)*\s*\)\s*\{[^}]*\}',
                flags=re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'switch\s*\(\s*\w+(?:\.\w+)*\s*\)\s*\{[^}]*\}',
                flags=re.DOTALL
            ),
        },
        fix_suggestion="Use exhaustive switch patterns or add a default case that throws for unexpected enum values.",
        false_positive_patterns=[
            r'default\s*:', r'_\s*=>', r'_\s*:',
        ],
    ),

    # =========================================================================
    # CF030: Empty Catch Block (CWE-1069)
    # =========================================================================
    ControlFlowRule(
        id="CF030",
        title="Empty exception catch block",
        description=(
            "An exception is caught but the catch block is empty or contains only "
            "a comment. This silently swallows exceptions, hiding bugs and making "
            "debugging extremely difficult. Exceptions should be logged at minimum."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1069"],
        category="exception_error",
        patterns={
            "python": LanguagePattern(
                r'except\s*(?:\w+)?(?:\s+as\s+\w+)?\s*:\s*\n\s*pass\s*(?:\n|$)',
            ),
            "javascript": LanguagePattern(
                r'catch\s*\([^)]*\)\s*\{\s*(?://[^\n]*)?\s*\}',
            ),
            "java": LanguagePattern(
                r'catch\s*\([^)]+\)\s*\{\s*(?://[^\n]*)?\s*\}',
            ),
            "csharp": LanguagePattern(
                r'catch\s*(?:\([^)]*\))?\s*\{\s*(?://[^\n]*)?\s*\}',
            ),
            "cpp": LanguagePattern(
                r'catch\s*\([^)]*\)\s*\{\s*(?://[^\n]*)?\s*\}',
            ),
            "php": LanguagePattern(
                r'catch\s*\([^)]+\)\s*\{\s*(?://[^\n]*)?\s*\}',
            ),
            "ruby": LanguagePattern(
                r'rescue\s*(?:\w+)?\s*(?:=>\s*\w+)?\s*\n\s*(?:#[^\n]*)?\s*end',
            ),
        },
        fix_suggestion="At minimum, log the exception. Consider re-throwing or handling specifically. Never silently swallow exceptions.",
    ),

    # =========================================================================
    # CF031: Missing Finally Cleanup (CWE-459)
    # =========================================================================
    ControlFlowRule(
        id="CF031",
        title="Resource acquisition without finally/using/with cleanup",
        description=(
            "A resource (file, connection, stream) is acquired but there is no "
            "finally block or using/with statement to ensure proper cleanup. "
            "If an exception occurs, the resource may leak."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-459"],
        category="exception_error",
        patterns={
            "java": LanguagePattern(
                r'(?:new\s+(?:FileInputStream|FileOutputStream|BufferedReader|Connection))\s*\([^)]+\)(?!.*(?:finally|try\s*\())',
                flags=re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'(?:new\s+(?:StreamReader|StreamWriter|SqlConnection|FileStream))\s*\([^)]+\)(?!.*(?:finally|using))',
                flags=re.DOTALL
            ),
        },
        fix_suggestion="Use try-with-resources (Java), using statement (C#), or with statement (Python) for automatic resource cleanup.",
    ),

    # =========================================================================
    # CF032: Catch Generic Exception
    # =========================================================================
    ControlFlowRule(
        id="CF032",
        title="Catching generic Exception class",
        description=(
            "A catch block catches the generic Exception/Throwable class instead of "
            "specific exception types. This can inadvertently catch and hide errors "
            "that should propagate, including system errors and programming bugs."
        ),
        severity=Severity.LOW,
        cwe_ids=["CWE-755"],
        category="exception_error",
        patterns={
            "python": LanguagePattern(
                r'except\s*(?:Exception|BaseException)\s*(?:as\s+\w+)?\s*:',
            ),
            "javascript": LanguagePattern(
                r'catch\s*\(\s*\w+\s*\)',  # JS catches all by default
            ),
            "java": LanguagePattern(
                r'catch\s*\(\s*(?:Exception|Throwable)\s+\w+\s*\)',
            ),
            "csharp": LanguagePattern(
                r'catch\s*(?:\(\s*Exception\s+\w+\s*\)|\s*\{)',
            ),
            "cpp": LanguagePattern(
                r'catch\s*\(\s*\.\.\.\s*\)',
            ),
            "php": LanguagePattern(
                r'catch\s*\(\s*(?:Exception|Throwable)\s+\$\w+\s*\)',
            ),
        },
        fix_suggestion="Catch specific exception types. If catching all is necessary, ensure critical exceptions are re-thrown.",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class ControlFlowLogicDetector(BaseScanner):
    """
    Detects control flow and logic errors in code.

    Scans for loop errors, condition mistakes, switch issues,
    and exception handling problems.
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in CONTROL_FLOW_RULES:
            self._compiled_patterns[rule.id] = {}
            for lang, lang_pattern in rule.patterns.items():
                try:
                    self._compiled_patterns[rule.id][lang] = re.compile(
                        lang_pattern.pattern,
                        lang_pattern.flags
                    )
                except re.error as e:
                    logger.warning(f"Invalid regex for {rule.id}/{lang}: {e}")

            # Compile false positive patterns
            self._compiled_fp_patterns[rule.id] = []
            for fp_pattern in rule.false_positive_patterns:
                try:
                    self._compiled_fp_patterns[rule.id].append(
                        re.compile(fp_pattern, re.IGNORECASE)
                    )
                except re.error:
                    pass

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.CONTROL_FLOW_LOGIC

    @property
    def supported_languages(self) -> Set[str]:
        return set(SUPPORTED_LANGUAGES.keys())

    @property
    def supported_extensions(self) -> Set[str]:
        extensions = set()
        for lang_def in SUPPORTED_LANGUAGES.values():
            extensions.update(lang_def.extensions)
        return extensions

    def is_available(self) -> bool:
        return True

    def get_scanner_version(self) -> Optional[str]:
        return self.SCANNER_VERSION

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        for lang_name, lang_def in SUPPORTED_LANGUAGES.items():
            if ext in lang_def.extensions:
                return lang_name
        return None

    def _is_false_positive(
        self,
        rule_id: str,
        matched_text: str,
    ) -> bool:
        """Check if match is a false positive."""
        fp_patterns = self._compiled_fp_patterns.get(rule_id, [])

        for fp_pattern in fp_patterns:
            if fp_pattern.search(matched_text):
                return True
        return False

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute control flow logic scan."""
        started_at = datetime.now(timezone.utc)
        findings = []
        files_scanned = 0
        errors = []

        # Get files to scan
        if target_path.is_file():
            files = [target_path]
        else:
            files = []
            for ext in self.supported_extensions:
                files.extend(target_path.rglob(f"*{ext}"))

        for file_path in files:
            files_scanned += 1
            language = self._detect_language(file_path)

            if not language:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.split("\n")

                for rule in CONTROL_FLOW_RULES:
                    # Get language-specific pattern
                    compiled_pattern = self._compiled_patterns.get(rule.id, {}).get(language)
                    if not compiled_pattern:
                        continue

                    for match in compiled_pattern.finditer(content):
                        # Check for false positives
                        if self._is_false_positive(rule.id, match.group()):
                            continue

                        # Calculate line number
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        # Get snippet
                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet = "\n".join(lines[snippet_start:snippet_end])

                        finding = SecurityFinding(
                            id=f"cf-{rule.id}-{file_path}:{line_start}",
                            rule_id=rule.id,
                            title=rule.title,
                            description=rule.description,
                            severity=rule.severity,
                            scanner=self.scanner_type,
                            location=Location(
                                file_path=str(file_path),
                                start_line=line_start,
                                end_line=line_end,
                                snippet=snippet,
                            ),
                            cwe_ids=rule.cwe_ids,
                            category=rule.category,
                            tags={f"lang:{language}", "control-flow"},
                        )

                        finding.suggested_fixes.append(
                            SuggestedFix(description=rule.fix_suggestion)
                        )

                        findings.append(finding)

            except Exception as e:
                errors.append(f"Error scanning {file_path}: {e}")
                logger.error(f"Error scanning {file_path}: {e}")

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        return ScanResult(
            scanner=self.scanner_type,
            scanner_version=self.SCANNER_VERSION,
            scan_duration_ms=duration_ms,
            findings=findings,
            files_scanned=files_scanned,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
        )

    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of all rules."""
        return {
            "total_rules": len(CONTROL_FLOW_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in CONTROL_FLOW_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_control_flow_logic_detector() -> ControlFlowLogicDetector:
    """Factory function to create control flow logic detector."""
    return ControlFlowLogicDetector()
