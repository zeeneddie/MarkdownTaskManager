"""
Concurrency Error Detector - Race Condition and Thread Safety Detection.

Fase 38: Detects concurrency issues to achieve 100% CWE Top 25 coverage:
- CWE-362: Concurrent Execution Using Shared Resource with Improper Synchronization ('Race Condition')
- CWE-366: Race Condition within a Thread
- CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition
- CWE-820: Missing Synchronization
- CWE-821: Incorrect Synchronization
- CWE-764: Multiple Locks of a Critical Resource
- CWE-765: Multiple Unlocks of a Critical Resource
- CWE-833: Deadlock

Primary focus: C, C++, Java, Python, Go
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
    "java": LanguageDefinition(
        name="Java",
        extensions={".java"},
    ),
    "python": LanguageDefinition(
        name="Python",
        extensions={".py"},
    ),
    "go": LanguageDefinition(
        name="Go",
        extensions={".go"},
    ),
}


# =============================================================================
# CONCURRENCY RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class ConcurrencyRule:
    """A concurrency rule with language-specific patterns."""
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
# RULE DEFINITIONS (8 rules as per Fase 38 plan)
# =============================================================================

CONCURRENCY_RULES: List[ConcurrencyRule] = [
    # =========================================================================
    # CC001: Thread creation with shared data (CWE-362, CWE-366)
    # =========================================================================
    ConcurrencyRule(
        id="CC001",
        title="Thread creation with potential shared data access",
        description=(
            "A new thread is created which may access shared data without proper synchronization. "
            "Concurrent access to shared state without locks can cause race conditions."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-362", "CWE-366"],
        category="race_condition",
        patterns={
            "c": LanguagePattern(
                r'pthread_create\s*\(',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'(?:std::thread|boost::thread)\s*\w*\s*\(',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'(?:new\s+Thread\s*\(|\.start\s*\(\s*\)|ExecutorService)',
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r'(?:threading\.Thread\s*\(|concurrent\.futures)',
                flags=re.MULTILINE,
            ),
            "go": LanguagePattern(
                r'\bgo\s+\w+\s*\(',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["global", "shared", "static", "mutable", "class"],
        require_context=True,
        context_window_lines=20,
        fix_suggestion="Protect shared data with mutex/lock, use atomic operations, or use thread-safe data structures.",
    ),

    # =========================================================================
    # CC002: TOCTOU (Time-of-check Time-of-use) race (CWE-362, CWE-367)
    # =========================================================================
    ConcurrencyRule(
        id="CC002",
        title="Time-of-check to time-of-use (TOCTOU) race condition",
        description=(
            "A file or resource is checked then used without atomicity. "
            "An attacker can modify the resource between check and use."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-362", "CWE-367"],
        category="race_condition",
        patterns={
            "c": LanguagePattern(
                r'(?:access|stat|lstat|fstat)\s*\([^)]+\)',
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r'(?:os\.path\.exists|os\.path\.isfile|os\.path\.isdir|os\.access)\s*\(',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'\.(?:exists|canRead|canWrite|isFile|isDirectory)\s*\(\s*\)',
                flags=re.MULTILINE,
            ),
            "go": LanguagePattern(
                r'os\.Stat\s*\(',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["open", "fopen", "read", "write", "unlink", "remove", "delete", "create"],
        require_context=True,
        context_window_lines=15,
        fix_suggestion="Use atomic operations, file locking (flock/fcntl), or handle errors from operations instead of pre-checking.",
    ),

    # =========================================================================
    # CC003: Signal handler race (CWE-362, CWE-479)
    # =========================================================================
    ConcurrencyRule(
        id="CC003",
        title="Non-reentrant function in signal handler",
        description=(
            "Signal handlers should only call async-signal-safe functions. "
            "Calling non-reentrant functions (printf, malloc, etc.) can cause deadlock or corruption."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-362", "CWE-479"],
        category="race_condition",
        patterns={
            "c": LanguagePattern(
                r'signal\s*\(\s*SIG\w+\s*,',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'(?:signal|std::signal)\s*\(\s*SIG\w+\s*,',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["printf", "malloc", "free", "exit", "fprintf", "syslog", "new", "delete"],
        require_context=True,
        context_window_lines=30,
        fix_suggestion="Only use async-signal-safe functions in signal handlers. Set a flag and handle in main loop.",
    ),

    # =========================================================================
    # CC004: Nested locks - potential deadlock (CWE-833, CWE-764)
    # =========================================================================
    ConcurrencyRule(
        id="CC004",
        title="Nested lock acquisition (potential deadlock)",
        description=(
            "Acquiring multiple locks without consistent ordering can cause deadlock. "
            "Thread A holds lock1 waiting for lock2, while Thread B holds lock2 waiting for lock1."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-833", "CWE-764"],
        category="deadlock",
        patterns={
            "c": LanguagePattern(
                r'pthread_mutex_lock\s*\([^)]+\)[\s\S]{0,500}?pthread_mutex_lock\s*\(',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "cpp": LanguagePattern(
                r'\.lock\s*\(\s*\)[\s\S]{0,500}?\.lock\s*\(\s*\)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "java": LanguagePattern(
                r'synchronized\s*\([^)]+\)\s*\{[\s\S]{0,500}?synchronized\s*\(',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "python": LanguagePattern(
                r'\.acquire\s*\(\s*\)[\s\S]{0,500}?\.acquire\s*\(\s*\)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "go": LanguagePattern(
                r'\.Lock\s*\(\s*\)[\s\S]{0,500}?\.Lock\s*\(\s*\)',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Use consistent lock ordering, std::scoped_lock (C++), or lock hierarchy.",
    ),

    # =========================================================================
    # CC005: Lock not released on error path (CWE-764, CWE-765)
    # =========================================================================
    ConcurrencyRule(
        id="CC005",
        title="Lock potentially not released on error path",
        description=(
            "A lock is acquired but may not be released if an error occurs or exception is thrown. "
            "This causes resource starvation and potential deadlock."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-764", "CWE-765"],
        category="deadlock",
        patterns={
            "c": LanguagePattern(
                r'pthread_mutex_lock\s*\([^)]+\)[\s\S]{0,300}?(?:return|goto)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "cpp": LanguagePattern(
                r'\.lock\s*\(\s*\)[\s\S]{0,300}?(?:return|throw)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "java": LanguagePattern(
                r'\.lock\s*\(\s*\)[\s\S]{0,300}?(?:return|throw)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "python": LanguagePattern(
                r'\.acquire\s*\(\s*\)[\s\S]{0,300}?(?:return|raise)',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "go": LanguagePattern(
                r'\.Lock\s*\(\s*\)[\s\S]{0,300}?return',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Use RAII (std::lock_guard/unique_lock in C++), try-finally, defer (Go), or context manager (Python).",
        false_positive_patterns=[
            r'lock_guard', r'unique_lock', r'scoped_lock', r'defer.*Unlock', r'finally.*unlock', r'with\s+\w+:',
        ],
    ),

    # =========================================================================
    # CC006: Thread-unsafe function usage (CWE-820)
    # =========================================================================
    ConcurrencyRule(
        id="CC006",
        title="Thread-unsafe function in multi-threaded context",
        description=(
            "Using non-thread-safe functions (strtok, localtime, rand, etc.) in multi-threaded code "
            "can cause race conditions due to internal static buffers."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-820"],
        category="thread_safety",
        patterns={
            "c": LanguagePattern(
                r'\b(strtok|localtime|gmtime|asctime|ctime|rand|strerror|getenv|setenv|readdir)\s*\(',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(strtok|localtime|gmtime|asctime|ctime|rand|strerror|getenv|setenv|readdir)\s*\(',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["thread", "pthread", "concurrent", "parallel", "async"],
        require_context=True,
        context_window_lines=30,
        fix_suggestion="Use thread-safe variants: strtok_r, localtime_r, gmtime_r, rand_r, strerror_r, etc.",
    ),

    # =========================================================================
    # CC007: Volatile misuse for synchronization (CWE-820)
    # =========================================================================
    ConcurrencyRule(
        id="CC007",
        title="Volatile used incorrectly for thread synchronization",
        description=(
            "Using volatile for thread synchronization is incorrect. Volatile does not provide "
            "atomicity or memory ordering guarantees needed for proper synchronization."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-820"],
        category="thread_safety",
        patterns={
            "c": LanguagePattern(
                r'\bvolatile\s+(?:int|bool|long|char)\s+\w+\s*=',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\bvolatile\s+(?:int|bool|long|char|std::atomic)\s+\w+\s*=',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'\bvolatile\s+(?:int|boolean|long)\s+\w+\s*=',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["thread", "concurrent", "shared", "flag", "stop", "running"],
        require_context=True,
        context_window_lines=20,
        fix_suggestion="Use std::atomic (C++), AtomicInteger/AtomicBoolean (Java), or proper synchronization primitives.",
        false_positive_patterns=[
            r'std::atomic', r'Atomic(?:Integer|Boolean|Long|Reference)',
        ],
    ),

    # =========================================================================
    # CC008: Data race on shared flag (CWE-820, CWE-821)
    # =========================================================================
    ConcurrencyRule(
        id="CC008",
        title="Potential data race on shared flag variable",
        description=(
            "A flag variable (stop, done, running, etc.) appears to be shared between threads "
            "without proper synchronization or atomic operations."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-820", "CWE-821"],
        category="thread_safety",
        patterns={
            "c": LanguagePattern(
                r'(?<!volatile\s)(?:int|bool|_Bool)\s+\w*(?:flag|stop|done|running|active|ready|finished)\w*\s*=',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'(?<!volatile\s)(?<!atomic<)(?:int|bool)\s+\w*(?:flag|stop|done|running|active|ready|finished)\w*\s*=',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'(?<!volatile\s)(?:boolean|int)\s+\w*(?:flag|stop|done|running|active|ready|finished)\w*\s*=',
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r'\w*(?:flag|stop|done|running|active|ready|finished)\w*\s*=\s*(?:True|False)',
                flags=re.MULTILINE,
            ),
        },
        context_keywords=["thread", "threading", "concurrent", "pthread", "parallel"],
        require_context=True,
        context_window_lines=30,
        fix_suggestion="Use atomic types, volatile (Java only), or protect with mutex. In Python, consider threading.Event.",
        false_positive_patterns=[
            r'std::atomic', r'AtomicBoolean', r'AtomicInteger', r'threading\.Event', r'volatile',
        ],
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class ConcurrencyErrorDetector(BaseScanner):
    """
    Detects concurrency vulnerabilities and race conditions.

    Scans for race conditions, TOCTOU bugs, deadlocks, improper synchronization,
    and thread-unsafe function usage.

    Closes CWE Top 25 gap: CWE-362 (Race Condition).
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in CONCURRENCY_RULES:
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
        return ScannerType.CONCURRENCY_ERROR

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
        """Execute concurrency safety scan."""
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

                for rule in CONCURRENCY_RULES:
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
                            id=f"concurrency-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "concurrency"},
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
            "total_rules": len(CONCURRENCY_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in CONCURRENCY_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": {
                "CWE-362": "Race Condition",
                "CWE-367": "TOCTOU",
                "CWE-833": "Deadlock",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_concurrency_error_detector() -> ConcurrencyErrorDetector:
    """Factory function to create concurrency error detector."""
    return ConcurrencyErrorDetector()
