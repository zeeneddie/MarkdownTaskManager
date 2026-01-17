"""
Path Security Detector - Uncontrolled Search Path, Unquoted Path, ReDoS Detection.

Fase 39: Detects path and regex security vulnerabilities across multiple languages:
- CWE-427: Uncontrolled Search Path Element (DLL/library hijacking)
- CWE-428: Unquoted Search Path or Element
- CWE-1333: Inefficient Regular Expression Complexity (ReDoS)

Multi-language support: Python, JavaScript, Java, C#, C/C++, PHP, Ruby, Go, Bash
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
        name="JavaScript",
        extensions={".js", ".jsx", ".mjs", ".cjs"},
    ),
    "typescript": LanguageDefinition(
        name="TypeScript",
        extensions={".ts", ".tsx"},
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java"},
    ),
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs"},
    ),
    "cpp": LanguageDefinition(
        name="C++",
        extensions={".cpp", ".hpp", ".cc", ".cxx", ".c++", ".h++", ".hh"},
    ),
    "c": LanguageDefinition(
        name="C",
        extensions={".c", ".h"},
    ),
    "php": LanguageDefinition(
        name="PHP",
        extensions={".php"},
    ),
    "ruby": LanguageDefinition(
        name="Ruby",
        extensions={".rb"},
    ),
    "go": LanguageDefinition(
        name="Go",
        extensions={".go"},
    ),
    "bash": LanguageDefinition(
        name="Bash",
        extensions={".sh", ".bash"},
    ),
    "powershell": LanguageDefinition(
        name="PowerShell",
        extensions={".ps1", ".psm1", ".psd1"},
    ),
    "perl": LanguageDefinition(
        name="Perl",
        extensions={".pl", ".pm"},
    ),
}


# =============================================================================
# PATH SECURITY RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class PathSecurityRule:
    """A path security rule with language-specific patterns."""
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
# RULE DEFINITIONS (10 rules as per Fase 39 plan)
# =============================================================================

PATH_SECURITY_RULES: List[PathSecurityRule] = [
    # =========================================================================
    # CWE-427: UNCONTROLLED SEARCH PATH (3 rules)
    # =========================================================================

    # PS001: Relative path library loading
    PathSecurityRule(
        id="PS001",
        title="Relative path in library loading",
        description=(
            "Loading libraries from relative paths allows DLL/SO hijacking. "
            "An attacker can place a malicious library in the working directory or earlier in the search path "
            "to execute arbitrary code with the application's privileges."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-427", "CWE-426"],
        category="uncontrolled_path",
        patterns={
            "cpp": LanguagePattern(
                r'\b(?:LoadLibrary|LoadLibraryEx|dlopen)\s*\(\s*["\'][^/\\"\'][^"\']*["\']',
                flags=re.MULTILINE,
            ),
            "c": LanguagePattern(
                r'\b(?:LoadLibrary|LoadLibraryEx|dlopen)\s*\(\s*["\'][^/\\"\'][^"\']*["\']',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'\b(?:Assembly\.(?:Load|LoadFrom)|DllImport\s*\(\s*)["\'][^/\\"\'][^"\']*["\']',
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r'\b(?:ctypes\.(?:CDLL|WinDLL|cdll\.LoadLibrary)|importlib\.import_module)\s*\(\s*["\'][^/\\"\'][^"\']*["\']',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'\bSystem\.(?:loadLibrary|load)\s*\(\s*["\'][^/\\"\'][^"\']*["\']',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use absolute paths for library loading. Validate PATH/LD_LIBRARY_PATH before loading.",
    ),

    # PS002: PATH environment modification
    PathSecurityRule(
        id="PS002",
        title="Unsafe PATH environment modification",
        description=(
            "Adding untrusted paths to PATH environment variable can lead to binary hijacking. "
            "Attackers can place malicious executables earlier in the path to intercept system commands."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-427"],
        category="uncontrolled_path",
        patterns={
            "python": LanguagePattern(
                r'os\.environ\s*\[\s*["\']PATH["\']\s*\]\s*=',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'process\.env\.PATH\s*=',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'System\.setProperty\s*\(\s*["\']java\.library\.path',
                flags=re.MULTILINE,
            ),
            "cpp": LanguagePattern(
                r'\b(?:putenv|setenv|_putenv)\s*\(\s*["\']PATH',
                flags=re.MULTILINE,
            ),
            "c": LanguagePattern(
                r'\b(?:putenv|setenv|_putenv)\s*\(\s*["\']PATH',
                flags=re.MULTILINE,
            ),
            "bash": LanguagePattern(
                r'\bexport\s+PATH\s*=',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Prepend only trusted, absolute paths. Never add user-controlled paths. Validate PATH modifications.",
    ),

    # PS003: Current directory in search path
    PathSecurityRule(
        id="PS003",
        title="Current directory in module search path",
        description=(
            "Including '.' or empty path in search path enables module hijacking. "
            "Attackers can place malicious modules in the current working directory to execute code."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-427"],
        category="uncontrolled_path",
        patterns={
            "python": LanguagePattern(
                r'sys\.path\.(?:insert|append)\s*\([^)]*(?:["\']\.?["\']|os\.getcwd)',
                flags=re.MULTILINE,
            ),
            "perl": LanguagePattern(
                r'(?:push|unshift)\s*\@INC\s*,.*["\']\.?["\']',
                flags=re.MULTILINE,
            ),
            "ruby": LanguagePattern(
                r'\$LOAD_PATH\.(?:unshift|push|<<).*["\']\.?["\']',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Avoid adding '.' or current directory to search paths. Use absolute paths only.",
    ),

    # =========================================================================
    # CWE-428: UNQUOTED SEARCH PATH (3 rules)
    # =========================================================================

    # PS010: Unquoted path with spaces (Windows)
    PathSecurityRule(
        id="PS010",
        title="Unquoted path with spaces",
        description=(
            "Unquoted paths with spaces allow path interception attacks on Windows. "
            "For 'C:\\Program Files\\App\\run.exe', Windows may execute 'C:\\Program.exe' instead."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-428"],
        category="unquoted_path",
        patterns={
            "cpp": LanguagePattern(
                r'\b(?:CreateProcess|ShellExecute|WinExec|system)\s*\([^"]*Program\s+Files',
                flags=re.MULTILINE,
            ),
            "c": LanguagePattern(
                r'\b(?:CreateProcess|ShellExecute|WinExec|system)\s*\([^"]*Program\s+Files',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'Process\.Start\s*\(\s*[^"]*Program\s+Files',
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r'subprocess\.\w+\s*\(\s*["\'][^"\']*Program\s+Files[^"\']*["\']',
                flags=re.MULTILINE,
            ),
            "powershell": LanguagePattern(
                r'Start-Process\s+[^"\'-][^\r\n]*Program\s+Files',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion='Always quote paths containing spaces: "C:\\Program Files\\..." or use short paths (C:\\PROGRA~1).',
    ),

    # PS011: Registry unquoted service path
    PathSecurityRule(
        id="PS011",
        title="Unquoted service path in registry",
        description=(
            "Windows services with unquoted ImagePath containing spaces are vulnerable to hijacking. "
            "Attackers can place executables at path breakpoints to gain SYSTEM privileges."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-428"],
        category="unquoted_path",
        patterns={
            "csharp": LanguagePattern(
                r'Registry.*ImagePath.*=.*[^"]*Program\s+Files',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "cpp": LanguagePattern(
                r'RegSetValue.*ImagePath.*[^"]*Program',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "c": LanguagePattern(
                r'RegSetValue.*ImagePath.*[^"]*Program',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "powershell": LanguagePattern(
                r'Set-ItemProperty.*ImagePath.*[^"\']*Program\s+Files',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion='Always quote service executable paths in registry: ImagePath = "\\"C:\\Program Files\\...".',
    ),

    # PS012: Command execution with unquoted variables
    PathSecurityRule(
        id="PS012",
        title="Unquoted variable in command execution",
        description=(
            "Unquoted shell variables can cause path splitting and unexpected argument handling. "
            "Variables containing spaces will be split into multiple arguments."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-428"],
        category="unquoted_path",
        patterns={
            "bash": LanguagePattern(
                r'(?:exec|eval|`)\s*\$\w+[^"\']',
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r'os\.system\s*\([^)]*\$\w+[^"\']',
                flags=re.MULTILINE,
            ),
            "perl": LanguagePattern(
                r'\bsystem\s*\(\s*\$\w+[^"\']',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion='Always quote shell variables: "$PATH" instead of $PATH. Use arrays for complex commands.',
    ),

    # =========================================================================
    # CWE-1333: ReDoS - INEFFICIENT REGEX (4 rules)
    # =========================================================================

    # PS020: Nested quantifiers
    PathSecurityRule(
        id="PS020",
        title="Regex with nested quantifiers (ReDoS)",
        description=(
            "Nested quantifiers like (a+)+ cause exponential backtracking (ReDoS). "
            "Malicious input can cause the regex engine to take exponential time, causing denial of service."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1333", "CWE-400"],
        category="redos",
        patterns={
            "python": LanguagePattern(
                r're\.(?:compile|search|match|findall|sub)\s*\([^)]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:new\s+RegExp\s*\(|/)[^/\n]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'(?:new\s+RegExp\s*\(|/)[^/\n]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'Pattern\.compile\s*\([^)]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'new\s+Regex\s*\([^)]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "php": LanguagePattern(
                r'preg_(?:match|replace|match_all)\s*\([^)]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "ruby": LanguagePattern(
                r'(?:Regexp\.new\s*\(|/)[^/\n]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
            "go": LanguagePattern(
                r'regexp\.(?:Compile|MustCompile)\s*\([^)]*\([^)]*[+*][^)]*\)[+*]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Avoid nested quantifiers. Use atomic groups (?>...) or possessive quantifiers a++. Set regex timeout.",
    ),

    # PS021: Overlapping alternations
    PathSecurityRule(
        id="PS021",
        title="Regex with overlapping alternations",
        description=(
            "Overlapping alternations like (a|a)+ cause exponential backtracking time. "
            "The regex engine tries all possible combinations, leading to denial of service."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1333"],
        category="redos",
        patterns={
            "python": LanguagePattern(
                r're\.(?:compile|search|match)\s*\([^)]*\(\w+\|\w+\)[+*]',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:RegExp|/)[^/\n]*\(\w+\|\w+\)[+*]',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'Pattern\.compile\s*\([^)]*\(\w+\|\w+\)[+*]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Simplify alternations to non-overlapping patterns. Use character classes [abc] instead of (a|b|c).",
    ),

    # PS022: Greedy quantifier before similar pattern
    PathSecurityRule(
        id="PS022",
        title="Greedy quantifier followed by similar pattern",
        description=(
            "Pattern like .*x.* causes O(n^2) or worse on non-matching input. "
            "The greedy .* consumes everything, then backtracks character by character trying to match x."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1333"],
        category="redos",
        patterns={
            "python": LanguagePattern(
                r're\.\w+\s*\([^)]*\.\*[^)]*\.\*',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:RegExp|/)[^/\n]*\.\*[^/\n]*\.\*',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'Pattern\.compile\s*\([^)]*\.\*[^)]*\.\*',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Use non-greedy quantifiers .*? or more specific character classes [^x]* instead of .*.",
    ),

    # PS023: User input in regex
    PathSecurityRule(
        id="PS023",
        title="User input used directly in regex",
        description=(
            "Unescaped user input in regex can cause ReDoS or regex injection attacks. "
            "Attackers can provide input containing regex metacharacters or ReDoS patterns."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1333", "CWE-185"],
        category="redos",
        patterns={
            "python": LanguagePattern(
                r're\.\w+\s*\(\s*(?:request|input|user|f["\']|params|args)',
                flags=re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'new\s+RegExp\s*\(\s*(?:req\.|params\.|input|user|query)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'new\s+RegExp\s*\(\s*(?:req\.|params\.|input|user|query)',
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r'Pattern\.compile\s*\(\s*(?:request|input|user|getParameter)',
                flags=re.MULTILINE,
            ),
            "csharp": LanguagePattern(
                r'new\s+Regex\s*\(\s*(?:Request|input|user)',
                flags=re.MULTILINE,
            ),
            "php": LanguagePattern(
                r'preg_\w+\s*\(\s*["\']?(?:\$_GET|\$_POST|\$_REQUEST|\$input)',
                flags=re.MULTILINE,
            ),
            "ruby": LanguagePattern(
                r'Regexp\.new\s*\(\s*(?:params|request|input)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion="Escape user input with re.escape() / Regex.Escape() / Pattern.quote(). Or use literal string matching.",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class PathSecurityDetector(BaseScanner):
    """
    Detects path and regex security vulnerabilities across multiple languages.

    Scans for uncontrolled search path (DLL hijacking), unquoted path vulnerabilities,
    and ReDoS (Regular Expression Denial of Service) patterns.

    Covers CWE-427 (Uncontrolled Search Path), CWE-428 (Unquoted Search Path),
    CWE-1333 (Inefficient Regular Expression).
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in PATH_SECURITY_RULES:
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
        return ScannerType.PATH_SECURITY

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
        """Execute path security scan."""
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

                for rule in PATH_SECURITY_RULES:
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
                            id=f"pathsec-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "path_security"},
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
            "total_rules": len(PATH_SECURITY_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in PATH_SECURITY_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": {
                "CWE-427": "Uncontrolled Search Path Element",
                "CWE-428": "Unquoted Search Path or Element",
                "CWE-1333": "Inefficient Regular Expression Complexity",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_path_security_detector() -> PathSecurityDetector:
    """Factory function to create path security detector."""
    return PathSecurityDetector()
