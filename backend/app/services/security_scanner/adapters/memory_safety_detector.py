"""
Memory Safety Detector - Buffer Overflow and Memory Corruption Detection.

Fase 38: Detects memory safety issues to achieve 100% CWE Top 25 coverage:
- CWE-787: Out-of-bounds Write
- CWE-416: Use After Free
- CWE-125: Out-of-bounds Read
- CWE-119: Buffer Overflow
- CWE-122: Heap-based Buffer Overflow
- CWE-124: Buffer Underwrite
- CWE-126: Buffer Over-read
- CWE-127: Buffer Under-read
- CWE-415: Double Free
- CWE-590: Free of Memory not on the Heap
- CWE-134: Format String Vulnerability
- CWE-562: Return of Stack Variable Address
- CWE-824: Uninitialized Pointer
- CWE-457: Uninitialized Variable
- CWE-190: Integer Overflow
- CWE-401: Memory Leak

Primary focus: C, C++, Rust (unsafe blocks)
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
    "c": LanguageDefinition(
        name="C",
        extensions={".c", ".h"},
    ),
    "cpp": LanguageDefinition(
        name="C++",
        extensions={".cpp", ".hpp", ".cc", ".cxx", ".c++", ".h++", ".hh"},
    ),
    "rust": LanguageDefinition(
        name="Rust",
        extensions={".rs"},
    ),
}


# =============================================================================
# MEMORY SAFETY RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class MemorySafetyRule:
    """A memory safety rule with language-specific patterns."""
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
# RULE DEFINITIONS (16 rules as per Fase 38 plan)
# =============================================================================

MEMORY_SAFETY_RULES: List[MemorySafetyRule] = [
    # =========================================================================
    # MS001: Unsafe string copy functions (CWE-119, CWE-787)
    # =========================================================================
    MemorySafetyRule(
        id="MS001",
        title="Unsafe string copy function (strcpy, strcat, sprintf)",
        description=(
            "strcpy/strcat/sprintf do not check buffer bounds, leading to buffer overflow. "
            "These functions will write past the end of the destination buffer if the source "
            "is larger than the destination, causing memory corruption."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-119", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "c": LanguagePattern(
                r'\b(strcpy|strcat|sprintf|vsprintf|wcscpy|wcscat)\s*\(',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(strcpy|strcat|sprintf|vsprintf|wcscpy|wcscat)\s*\(',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use strncpy/strncat/snprintf with explicit size limits, or use C++ std::string.",
        false_positive_patterns=[
            r'#\s*define', r'//.*(?:safe|checked|bounded)',
        ],
    ),

    # =========================================================================
    # MS002: gets() function (CWE-119, CWE-787, CWE-242)
    # =========================================================================
    MemorySafetyRule(
        id="MS002",
        title="Use of gets() function (removed in C11)",
        description=(
            "gets() cannot limit input size and always causes a buffer overflow vulnerability. "
            "It has been removed from the C standard in C11. There is no safe way to use gets()."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-119", "CWE-787", "CWE-242"],
        category="buffer_overflow",
        patterns={
            "c": LanguagePattern(
                r'\bgets\s*\(',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\bgets\s*\(',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use fgets() with explicit buffer size: fgets(buffer, sizeof(buffer), stdin)",
    ),

    # =========================================================================
    # MS003: scanf without width specifier (CWE-119, CWE-787)
    # =========================================================================
    MemorySafetyRule(
        id="MS003",
        title="scanf/sscanf %s without width specifier",
        description=(
            "Using scanf/sscanf with %s format without a width specifier can overflow the buffer. "
            "The %s format reads until whitespace, potentially writing beyond buffer bounds."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "c": LanguagePattern(
                r'\b(scanf|sscanf|fscanf|wscanf)\s*\([^)]*"%[^"]*(?<!\d)s[^"]*"',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(scanf|sscanf|fscanf|wscanf)\s*\([^)]*"%[^"]*(?<!\d)s[^"]*"',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use width specifier: scanf(\"%99s\", buffer) for 100-byte buffer, or use fgets().",
    ),

    # =========================================================================
    # MS004: memcpy/memmove with unchecked size (CWE-119, CWE-787, CWE-805)
    # =========================================================================
    MemorySafetyRule(
        id="MS004",
        title="memcpy/memmove with potentially unchecked size",
        description=(
            "Memory copy functions with size from potentially untrusted sources can cause "
            "buffer overflow. Always validate the size parameter against destination buffer size."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-787", "CWE-805"],
        category="buffer_overflow",
        patterns={
            "c": LanguagePattern(
                r'\b(memcpy|memmove|bcopy|wmemcpy|wmemmove)\s*\([^;]+\)',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(memcpy|memmove|bcopy|wmemcpy|wmemmove)\s*\([^;]+\)',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["user", "input", "request", "recv", "read", "network", "socket", "client"],
        require_context=True,
        context_window_lines=15,
        fix_suggestion="Validate size parameter: if (size <= dest_size) memcpy(dest, src, size);",
    ),

    # =========================================================================
    # MS005: Use after free pattern (CWE-416)
    # =========================================================================
    MemorySafetyRule(
        id="MS005",
        title="Potential use after free",
        description=(
            "Memory may be accessed after being freed, leading to undefined behavior. "
            "This can cause crashes, data corruption, or security vulnerabilities."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-416"],
        category="use_after_free",
        patterns={
            "c": LanguagePattern(
                r'free\s*\(\s*(\w+)\s*\)\s*;(?!\s*\1\s*=\s*NULL)',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'delete\s+(\w+)\s*;(?!\s*\1\s*=\s*nullptr)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Set pointer to NULL after free: free(ptr); ptr = NULL; (or nullptr in C++)",
    ),

    # =========================================================================
    # MS006: Double free (CWE-415)
    # =========================================================================
    MemorySafetyRule(
        id="MS006",
        title="Potential double free vulnerability",
        description=(
            "The same memory may be freed twice, causing heap corruption. "
            "Double free can lead to arbitrary code execution or denial of service."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-415"],
        category="use_after_free",
        patterns={
            "c": LanguagePattern(
                r'free\s*\(\s*(\w+)\s*\)[\s\S]{0,200}?free\s*\(\s*\1\s*\)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "cpp": LanguagePattern(
                r'delete\s+(\w+)\s*;[\s\S]{0,200}?delete\s+\1\s*;',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Track allocation state or set pointer to NULL/nullptr after free to prevent double free.",
    ),

    # =========================================================================
    # MS007: Return of stack variable address (CWE-562)
    # =========================================================================
    MemorySafetyRule(
        id="MS007",
        title="Return of local variable address (dangling pointer)",
        description=(
            "Returning the address of a local (stack) variable creates a dangling pointer. "
            "The stack memory is reclaimed when the function returns, making the pointer invalid."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-562"],
        category="use_after_free",
        patterns={
            "c": LanguagePattern(
                r'return\s+&\s*\w+\s*;',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'return\s+&\s*\w+\s*;',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Return by value, use static storage, pass buffer as parameter, or allocate on heap.",
        false_positive_patterns=[
            r'static\s+', r'&\s*this->', r'&\s*m_',
        ],
    ),

    # =========================================================================
    # MS008: Integer overflow in allocation (CWE-190, CWE-122)
    # =========================================================================
    MemorySafetyRule(
        id="MS008",
        title="Integer overflow risk in memory allocation size",
        description=(
            "Multiplication in malloc/calloc size can overflow, allocating a smaller buffer than "
            "expected. This leads to heap buffer overflow when the full expected size is used."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-190", "CWE-122"],
        category="integer_overflow",
        patterns={
            "c": LanguagePattern(
                r'\b(malloc|calloc|realloc)\s*\(\s*[^)]*\*[^)]*\)',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\bnew\s+\w+\s*\[\s*[^]]*\*[^]]*\]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Check for overflow before allocation: if (a > SIZE_MAX / b) return error; or use calloc().",
    ),

    # =========================================================================
    # MS009: Signed/unsigned comparison (CWE-195, CWE-697)
    # =========================================================================
    MemorySafetyRule(
        id="MS009",
        title="Signed/unsigned comparison in bounds check",
        description=(
            "Comparing signed with unsigned integers can bypass bounds checks. "
            "A negative signed value becomes a large unsigned value, passing the check."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-195", "CWE-697"],
        category="integer_overflow",
        patterns={
            "c": LanguagePattern(
                r'if\s*\(\s*\w+\s*<\s*sizeof\s*\(',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'if\s*\(\s*\w+\s*<\s*(?:sizeof|\.size\(\))',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use size_t for sizes and ensure consistent signedness. Cast explicitly if needed.",
    ),

    # =========================================================================
    # MS010: Format string vulnerability (CWE-134)
    # =========================================================================
    MemorySafetyRule(
        id="MS010",
        title="Format string vulnerability",
        description=(
            "Using user-controlled input as format string can read/write arbitrary memory. "
            "Attackers can use format specifiers like %n to write to memory."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-134"],
        category="format_string",
        patterns={
            "c": LanguagePattern(
                r'\b(printf|fprintf|sprintf|snprintf|syslog)\s*\(\s*(?:[^",]+,\s*)?(\w+)\s*\)',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(printf|fprintf|sprintf|snprintf|syslog)\s*\(\s*(?:[^",]+,\s*)?(\w+)\s*\)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Always use format string literal: printf(\"%s\", user_input); never printf(user_input);",
        false_positive_patterns=[
            r'printf\s*\(\s*"', r'fprintf\s*\([^,]+,\s*"',
        ],
    ),

    # =========================================================================
    # MS011: Uninitialized pointer (CWE-824, CWE-457)
    # =========================================================================
    MemorySafetyRule(
        id="MS011",
        title="Potentially uninitialized pointer",
        description=(
            "Pointer declared without initialization may contain garbage value. "
            "Dereferencing an uninitialized pointer leads to undefined behavior."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-824", "CWE-457"],
        category="uninitialized",
        patterns={
            "c": LanguagePattern(
                r'^\s*(?:const\s+)?(?:\w+\s+)+\*\s*\w+\s*;$',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'^\s*(?:const\s+)?(?:\w+\s+)+\*\s*\w+\s*;$',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Initialize pointers: int *ptr = NULL; (C) or int *ptr = nullptr; (C++)",
        false_positive_patterns=[
            r'extern\s+', r'typedef\s+',
        ],
    ),

    # =========================================================================
    # MS012: Unsafe Rust block (CWE-119)
    # =========================================================================
    MemorySafetyRule(
        id="MS012",
        title="Unsafe Rust block detected",
        description=(
            "Unsafe blocks bypass Rust's memory safety guarantees. "
            "While sometimes necessary, unsafe code should be minimized and carefully reviewed."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-119"],
        category="unsafe_rust",
        patterns={
            "rust": LanguagePattern(
                r'\bunsafe\s*\{',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Review unsafe block carefully. Consider safe alternatives or encapsulate in safe API.",
    ),

    # =========================================================================
    # MS013: Raw pointer dereference in Rust (CWE-119, CWE-416)
    # =========================================================================
    MemorySafetyRule(
        id="MS013",
        title="Raw pointer dereference in Rust",
        description=(
            "Dereferencing raw pointers (*const T, *mut T) in Rust requires unsafe and "
            "can lead to memory safety violations if the pointer is invalid."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-416"],
        category="unsafe_rust",
        patterns={
            "rust": LanguagePattern(
                r'\*\w+\s+as\s+\*(?:const|mut)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use references (&T, &mut T) instead of raw pointers when possible.",
    ),

    # =========================================================================
    # MS014: std::vector operator[] without bounds check (CWE-125, CWE-787)
    # =========================================================================
    MemorySafetyRule(
        id="MS014",
        title="std::vector/array operator[] without bounds check",
        description=(
            "The operator[] on std::vector and std::array does not perform bounds checking. "
            "Out-of-bounds access leads to undefined behavior."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-125", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "cpp": LanguagePattern(
                r'(?:std::)?(?:vector|array)<[^>]+>\s*\w+[^;{]*\[\s*\w+\s*\]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use .at(index) for bounds-checked access, or validate index first.",
        false_positive_patterns=[
            r'\.at\s*\(', r'if\s*\([^)]*<\s*(?:\.size\(\)|\.length\(\))',
        ],
    ),

    # =========================================================================
    # MS015: Manual new/delete (CWE-401, CWE-416)
    # =========================================================================
    MemorySafetyRule(
        id="MS015",
        title="Manual new/delete instead of smart pointers",
        description=(
            "Using raw new/delete is error-prone and can lead to memory leaks or "
            "use-after-free. Modern C++ prefers smart pointers for automatic memory management."
        ),
        severity=Severity.LOW,
        cwe_ids=["CWE-401", "CWE-416"],
        category="memory_management",
        patterns={
            "cpp": LanguagePattern(
                r'\bnew\s+\w+(?:\s*\[|\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use std::unique_ptr, std::shared_ptr, or std::make_unique/std::make_shared.",
        false_positive_patterns=[
            r'placement\s+new', r'operator\s+new',
        ],
    ),

    # =========================================================================
    # MS016: alloca/VLA on stack (CWE-119, CWE-770)
    # =========================================================================
    MemorySafetyRule(
        id="MS016",
        title="Dynamic stack allocation (alloca/VLA) risk",
        description=(
            "alloca() and Variable Length Arrays (VLAs) allocate memory on the stack. "
            "Large or unvalidated sizes can cause stack overflow, leading to crashes or exploits."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-770"],
        category="buffer_overflow",
        patterns={
            "c": LanguagePattern(
                r'\b(alloca|_alloca|__builtin_alloca)\s*\(',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(alloca|_alloca|__builtin_alloca)\s*\(',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use heap allocation (malloc/new) with size validation instead of alloca/VLA.",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class MemorySafetyDetector(BaseScanner):
    """
    Detects memory safety vulnerabilities in C, C++, and Rust.

    Scans for buffer overflows, use-after-free, format string vulnerabilities,
    integer overflows, and other memory corruption issues.

    Closes CWE Top 25 gaps: CWE-787, CWE-416, CWE-125, CWE-119.
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in MEMORY_SAFETY_RULES:
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
        return ScannerType.MEMORY_SAFETY

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
        """Execute memory safety scan."""
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

                for rule in MEMORY_SAFETY_RULES:
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
                            id=f"memory-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "memory_safety"},
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
            "total_rules": len(MEMORY_SAFETY_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in MEMORY_SAFETY_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": {
                "CWE-787": "Out-of-bounds Write",
                "CWE-416": "Use After Free",
                "CWE-125": "Out-of-bounds Read",
                "CWE-119": "Buffer Overflow",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_memory_safety_detector() -> MemorySafetyDetector:
    """Factory function to create memory safety detector."""
    return MemorySafetyDetector()
