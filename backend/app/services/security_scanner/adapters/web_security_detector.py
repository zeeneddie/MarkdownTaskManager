"""
Web Security Detector - Prototype Pollution, CSV Injection, Invalid Quantity Detection.

Fase 39: Detects web security vulnerabilities across multiple languages:
- CWE-1321: Prototype Pollution (JavaScript/TypeScript)
- CWE-1236: CSV/Formula Injection (all languages)
- CWE-1284: Invalid Quantity in Input (all languages)

Multi-language support: JavaScript, TypeScript, Python, Java, C#, PHP, Ruby
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
    "javascript": LanguageDefinition(
        name="JavaScript",
        extensions={".js", ".jsx", ".mjs", ".cjs"},
    ),
    "typescript": LanguageDefinition(
        name="TypeScript",
        extensions={".ts", ".tsx"},
    ),
    "python": LanguageDefinition(
        name="Python",
        extensions={".py", ".pyw"},
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java"},
    ),
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs"},
    ),
    "php": LanguageDefinition(
        name="PHP",
        extensions={".php"},
    ),
    "ruby": LanguageDefinition(
        name="Ruby",
        extensions={".rb"},
    ),
}


# =============================================================================
# WEB SECURITY RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class WebSecurityRule:
    """A web security rule with language-specific patterns."""
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

    # Context keywords for reducing false positives
    context_keywords: List[str] = field(default_factory=list)
    require_context: bool = False
    context_window_lines: int = 10

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)


# =============================================================================
# RULE DEFINITIONS (12 rules as per Fase 39 plan)
# =============================================================================

WEB_SECURITY_RULES: List[WebSecurityRule] = [
    # =========================================================================
    # CWE-1321: PROTOTYPE POLLUTION (4 rules)
    # =========================================================================

    # WS001: Direct __proto__ assignment
    WebSecurityRule(
        id="WS001",
        title="Direct __proto__ assignment",
        description=(
            "Assigning to __proto__ allows prototype pollution attacks. "
            "Attackers can inject properties into Object.prototype, affecting all objects "
            "in the application, leading to security bypasses or remote code execution."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-1321"],
        category="prototype_pollution",
        patterns={
            "javascript": LanguagePattern(
                r'__proto__\s*[=\[]',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'__proto__\s*[=\[]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use Object.create(null) or Map instead of plain objects. Never allow __proto__ as a property key.",
    ),

    # WS002: constructor.prototype manipulation
    WebSecurityRule(
        id="WS002",
        title="Constructor prototype manipulation",
        description=(
            "Modifying constructor.prototype can pollute all object instances. "
            "This pattern is dangerous when the property name or value comes from user input."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1321"],
        category="prototype_pollution",
        patterns={
            "javascript": LanguagePattern(
                r'constructor\s*\.\s*prototype\s*[=\[]',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'constructor\s*\.\s*prototype\s*[=\[]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Avoid modifying prototypes with user input. Use Object.freeze() on prototypes to prevent modification.",
    ),

    # WS003: Object.assign with user input
    WebSecurityRule(
        id="WS003",
        title="Object.assign with untrusted source",
        description=(
            "Object.assign can copy __proto__ from user-controlled objects, enabling prototype pollution. "
            "When merging user input into objects, __proto__ properties are copied."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1321"],
        category="prototype_pollution",
        patterns={
            "javascript": LanguagePattern(
                r'Object\.assign\s*\([^,]+,\s*(?:req\.|params\.|body\.|query\.|input|args)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'Object\.assign\s*\([^,]+,\s*(?:req\.|params\.|body\.|query\.|input|args)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Validate input before Object.assign. Use structuredClone() or filter out __proto__, constructor, prototype keys.",
    ),

    # WS004: Dynamic property access with user input
    WebSecurityRule(
        id="WS004",
        title="Dynamic property access with user input",
        description=(
            "Using bracket notation (obj[userInput]) allows setting __proto__ if input is not validated. "
            "Attackers can pollute prototypes by providing '__proto__' as the property name."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1321"],
        category="prototype_pollution",
        patterns={
            "javascript": LanguagePattern(
                r'\w+\s*\[\s*(?:req\.|params\.|body\.|query\.|input|key|prop|name)\w*\s*\]',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'\w+\s*\[\s*(?:req\.|params\.|body\.|query\.|input|key|prop|name)\w*\s*\]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Validate property names against an allowlist. Reject '__proto__', 'constructor', 'prototype' as keys.",
        false_positive_patterns=[
            r'hasOwnProperty', r'Object\.hasOwn',
        ],
    ),

    # =========================================================================
    # CWE-1236: CSV INJECTION (4 rules)
    # =========================================================================

    # WS010: CSV formula injection risk
    WebSecurityRule(
        id="WS010",
        title="CSV formula injection risk",
        description=(
            "User data written to CSV that starts with =, +, -, @ can execute formulas in spreadsheets. "
            "When opened in Excel or Google Sheets, these formulas can run malicious commands or exfiltrate data."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1236"],
        category="csv_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:csv\.writer|writerow|to_csv).*(?:request|input|user|data|params)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "javascript": LanguagePattern(
                r'(?:createObjectCsvWriter|csv|xlsx|excel|writeFile).*(?:req\.|input|user|data|body)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "java": LanguagePattern(
                r'(?:CSVWriter|opencsv|writeNext|CSVPrinter).*(?:request|input|user|getParameter)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "csharp": LanguagePattern(
                r'(?:CsvWriter|WriteRecord|StreamWriter.*\.csv|CsvHelper).*(?:Request|input|user)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "php": LanguagePattern(
                r'(?:fputcsv|csv).*\$_(?:GET|POST|REQUEST)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "ruby": LanguagePattern(
                r'(?:CSV\.open|to_csv|CSV\.generate).*(?:params|request|input)',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Prefix values with single quote or tab character. Escape formula characters (=, +, -, @, |) at start of cell values.",
    ),

    # WS011: Missing CSV sanitization
    WebSecurityRule(
        id="WS011",
        title="CSV output without sanitization",
        description=(
            "Exporting data to CSV without escaping formula characters allows formula injection. "
            "Always sanitize cell values before CSV export to prevent spreadsheet formula attacks."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1236"],
        category="csv_injection",
        patterns={
            "python": LanguagePattern(
                r'writerow\s*\(\s*\[.*?\]',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'\.join\s*\(\s*["\'],',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'writeNext\s*\(\s*(?:new\s+String\s*\[\]|Arrays\.asList)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Implement CSV sanitization: prefix formula characters (=+-@|) with a single quote or tab.",
        context_keywords=["csv", "export", "download", "spreadsheet", "excel"],
        require_context=True,
        context_window_lines=15,
    ),

    # WS012: Spreadsheet export with user data
    WebSecurityRule(
        id="WS012",
        title="Spreadsheet export with user data",
        description=(
            "Excel/spreadsheet exports can execute formulas from user-provided data. "
            "Libraries like openpyxl, xlsxwriter, or xlsx can create files with executable formulas."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1236"],
        category="csv_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:openpyxl|xlsxwriter|pandas\.DataFrame.*to_excel|xlwt)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:xlsx|exceljs|SheetJS|XLSX).*(?:write|export|utils\.json_to_sheet)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "java": LanguagePattern(
                r'(?:XSSFWorkbook|HSSFWorkbook|poi\.ss|createSheet)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Sanitize cell values before Excel export. Set cell format to text explicitly. Prefix formula characters with quotes.",
        context_keywords=["user", "input", "request", "data", "export"],
        require_context=True,
        context_window_lines=15,
    ),

    # WS013: TSV/Tab-separated output
    WebSecurityRule(
        id="WS013",
        title="Tab-separated output with user data",
        description=(
            "Tab-separated values (TSV) files opened in spreadsheets are also vulnerable to formula injection. "
            "The same sanitization rules apply as for CSV files."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1236"],
        category="csv_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:delimiter\s*=\s*["\']\\t["\']|\.tsv)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:join\s*\(\s*["\']\\t["\']|\.tsv)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Apply the same sanitization as CSV: escape formula characters at start of values.",
        context_keywords=["user", "input", "export", "download"],
        require_context=True,
        context_window_lines=10,
    ),

    # =========================================================================
    # CWE-1284: INVALID QUANTITY IN INPUT (4 rules)
    # =========================================================================

    # WS020: Unchecked array index from user input
    WebSecurityRule(
        id="WS020",
        title="Unchecked array index from user input",
        description=(
            "Using user input as array index without bounds validation can cause out-of-bounds access. "
            "This may lead to crashes, information disclosure, or security vulnerabilities."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1284", "CWE-129"],
        category="invalid_quantity",
        patterns={
            "python": LanguagePattern(
                r'\w+\s*\[\s*(?:int\s*\()?\s*(?:request|input|user|params|args)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'\w+\s*\[\s*(?:parseInt\s*\()?\s*(?:req\.|params\.|query\.|body\.)',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'\w+\s*\[\s*(?:Integer\.parseInt\s*\()?\s*(?:request|input|getParameter)',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'\w+\s*\[\s*(?:int\.Parse\s*\()?\s*(?:Request|input)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Validate index is within bounds: 0 <= index < array.length before accessing.",
    ),

    # WS021: Loop count from untrusted source
    WebSecurityRule(
        id="WS021",
        title="Loop count from untrusted source",
        description=(
            "Loop iterations controlled by user input without limit can cause denial of service. "
            "Attackers can provide very large numbers causing excessive CPU usage or memory allocation."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1284", "CWE-606"],
        category="invalid_quantity",
        patterns={
            "python": LanguagePattern(
                r'(?:for|while).*range\s*\(.*(?:request|input|user|int\s*\(|params)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'for\s*\([^;]*;\s*\w+\s*[<>=]+\s*(?:req\.|params\.|parseInt|Number\()',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'for\s*\([^;]*;\s*\w+\s*[<>=]+\s*(?:request|Integer\.parseInt|getParameter)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Set a maximum iteration limit. Validate user-provided count: count = Math.min(userInput, MAX_ALLOWED).",
    ),

    # WS022: Memory allocation size from user input
    WebSecurityRule(
        id="WS022",
        title="Memory allocation size from user input",
        description=(
            "Allocating memory based on user-controlled size can cause denial of service or crashes. "
            "Very large values can exhaust memory, while negative values can cause undefined behavior."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1284", "CWE-789"],
        category="invalid_quantity",
        patterns={
            "python": LanguagePattern(
                r'(?:bytearray|bytes|list\s*\*|b["\']\s*\*)\s*\(\s*(?:int\s*\()?\s*(?:request|input|params)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:Buffer\.alloc|new\s+ArrayBuffer|new\s+Uint8Array)\s*\(\s*(?:parseInt)?\s*\(?(?:req\.|params|Number)',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'new\s+byte\s*\[\s*(?:Integer\.parseInt\s*\()?\s*(?:request|input|getParameter)',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'new\s+byte\s*\[\s*(?:int\.Parse\s*\()?\s*(?:Request|input)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Validate and cap allocation size. Reject negative values. Set maximum: size = Math.min(Math.max(0, userSize), MAX_SIZE).",
    ),

    # WS023: Quantity may be negative
    WebSecurityRule(
        id="WS023",
        title="Quantity may be negative",
        description=(
            "User-provided quantity used without checking for negative values can cause logic errors. "
            "Negative quantities in financial calculations, inventory, or pagination can have severe consequences."
        ),
        severity=Severity.LOW,
        cwe_ids=["CWE-1284"],
        category="invalid_quantity",
        patterns={
            "python": LanguagePattern(
                r'(?:quantity|count|amount|size|num|limit|offset|page)\s*=\s*(?:int\s*\()?\s*(?:request|input|params|args)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:quantity|count|amount|size|num|limit|offset|page)\s*=\s*(?:parseInt|Number)?\s*\(?(?:req\.|params|query)',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'(?:quantity|count|amount|size|num|limit|offset|page)\s*=\s*(?:Integer\.parseInt\s*\()?\s*(?:request|getParameter)',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'(?:quantity|count|amount|size|num|limit|offset|page)\s*=\s*(?:int\.Parse\s*\()?\s*(?:Request)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Validate quantity >= 0 and <= maximum allowed value. Use unsigned types where appropriate.",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class WebSecurityDetector(BaseScanner):
    """
    Detects web security vulnerabilities across multiple languages.

    Scans for prototype pollution (JS/TS), CSV/formula injection (all languages),
    and invalid quantity handling vulnerabilities.

    Covers CWE-1321 (Prototype Pollution), CWE-1236 (CSV Injection),
    CWE-1284 (Invalid Quantity in Input).
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in WEB_SECURITY_RULES:
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
        return ScannerType.WEB_SECURITY

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

    def _has_context_keyword(
        self,
        lines: List[str],
        match_line: int,
        keywords: List[str],
        window: int
    ) -> bool:
        """Check if any context keyword appears near the match."""
        if not keywords:
            return True

        start_line = max(0, match_line - window)
        end_line = min(len(lines), match_line + window)
        context_text = "\n".join(lines[start_line:end_line]).lower()

        return any(kw.lower() in context_text for kw in keywords)

    def _is_false_positive(
        self,
        rule_id: str,
        matched_text: str,
        context_lines: str
    ) -> bool:
        """Check if match is a false positive."""
        fp_patterns = self._compiled_fp_patterns.get(rule_id, [])
        full_text = matched_text + " " + context_lines

        for fp_pattern in fp_patterns:
            if fp_pattern.search(full_text):
                return True
        return False

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute web security scan."""
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

                for rule in WEB_SECURITY_RULES:
                    # Get language-specific pattern
                    compiled_pattern = self._compiled_patterns.get(rule.id, {}).get(language)
                    if not compiled_pattern:
                        continue

                    for match in compiled_pattern.finditer(content):
                        # Calculate line number
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        # Check context keywords if required
                        if rule.require_context:
                            if not self._has_context_keyword(
                                lines, line_start,
                                rule.context_keywords, rule.context_window_lines
                            ):
                                continue

                        # Get snippet
                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet = "\n".join(lines[snippet_start:snippet_end])

                        # Check for false positives
                        if self._is_false_positive(rule.id, match.group(), snippet):
                            continue

                        finding = SecurityFinding(
                            id=f"websec-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "web_security"},
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
            "total_rules": len(WEB_SECURITY_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in WEB_SECURITY_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": {
                "CWE-1321": "Prototype Pollution",
                "CWE-1236": "CSV/Formula Injection",
                "CWE-1284": "Invalid Quantity in Input",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_web_security_detector() -> WebSecurityDetector:
    """Factory function to create web security detector."""
    return WebSecurityDetector()
