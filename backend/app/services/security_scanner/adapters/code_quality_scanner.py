"""
Code Quality Scanner - Common Programming Mistakes Detection.

Detects language-specific programming mistakes and code smells that lead to
bugs, unexpected behavior, or maintenance issues.

Based on common programming mistakes analysis including:
- TryParse without proper default handling
- Floating-point comparison issues
- Unhandled exogenous exceptions
- Redundant boolean literals
- Exception re-throwing with stack trace loss
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone
from enum import Enum

from ..models.findings import (
    SecurityFinding, ScanResult, Severity, ScannerType, Location, SuggestedFix,
)
from .base import BaseScanner

logger = logging.getLogger(__name__)


# =============================================================================
# FINDING CATEGORIES
# =============================================================================

class QualityCategory(str, Enum):
    """Categories of code quality issues."""
    TYPE_CONVERSION = "type_conversion"
    NUMERIC_PRECISION = "numeric_precision"
    EXCEPTION_HANDLING = "exception_handling"
    CODE_SMELL = "code_smell"
    DEFENSIVE_CODING = "defensive_coding"


# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================

@dataclass
class LanguageDefinition:
    """Definition of a programming language for scanning."""
    name: str
    extensions: Set[str]


SUPPORTED_LANGUAGES: Dict[str, LanguageDefinition] = {
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs", ".cshtml", ".razor"},
    ),
    "vbnet": LanguageDefinition(
        name="VB.NET",
        extensions={".vb", ".aspx", ".ascx", ".asmx", ".ashx"},
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java", ".jsp"},
    ),
    "javascript": LanguageDefinition(
        name="JavaScript/TypeScript",
        extensions={".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
    ),
    "python": LanguageDefinition(
        name="Python",
        extensions={".py", ".pyw"},
    ),
}


# =============================================================================
# CODE QUALITY RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class CodeQualityRule:
    """A code quality rule with language-specific patterns."""
    id: str
    title: str
    description: str
    severity: Severity
    category: QualityCategory

    # Language-specific regex patterns
    patterns: Dict[str, LanguagePattern]

    # Fix suggestions
    fix_suggestion: str
    correct_example: str = ""
    incorrect_example: str = ""

    # Documentation reference
    references: List[str] = field(default_factory=list)


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

CODE_QUALITY_RULES: List[CodeQualityRule] = [
    # =========================================================================
    # CQ-001: TryParse Without Proper Default Handling
    # =========================================================================
    CodeQualityRule(
        id="CQ-TRYPARSE-001",
        title="TryParse result not used for default value assignment",
        description=(
            "TryParse is called but the boolean return value is not used to assign "
            "a default value when parsing fails. The out parameter will contain the "
            "type's default value (0 for int), not your intended default. "
            "This leads to unexpected behavior when input cannot be parsed."
        ),
        severity=Severity.MEDIUM,
        category=QualityCategory.TYPE_CONVERSION,
        patterns={
            # Matches: int.TryParse(x, out y); return y; (without checking result)
            "csharp": LanguagePattern(
                r'(?:int|double|float|decimal|long|short|byte)\.TryParse\s*\([^;]+\)\s*;'
                r'\s*(?!if\s*\(|return\s+\w+\s*\?)',
                flags=re.IGNORECASE | re.MULTILINE
            ),
            # Matches: Integer.TryParse(x, y) without If check
            "vbnet": LanguagePattern(
                r'(?:Integer|Double|Single|Decimal|Long|Short|Byte)\.TryParse\s*\([^)]+\)'
                r'(?!\s*Then)',
                flags=re.IGNORECASE
            ),
        },
        fix_suggestion=(
            "Use the TryParse return value to conditionally assign your default:\n"
            "if (!int.TryParse(input, out var result)) { result = defaultValue; }"
        ),
        incorrect_example="""
// INCORRECT - default value 100 is never used
int value = 100;
int.TryParse(input, out value);
return value;  // Returns 0 if parsing fails, not 100!
""",
        correct_example="""
// CORRECT - properly handle parse failure
if (!int.TryParse(input, out int value))
{
    value = 100;  // Use default when parsing fails
}
return value;
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/api/system.int32.tryparse",
        ],
    ),

    # =========================================================================
    # CQ-002: Floating-Point Equality Comparison
    # =========================================================================
    CodeQualityRule(
        id="CQ-FLOAT-001",
        title="Direct floating-point equality comparison",
        description=(
            "Floating-point numbers (float, double) are compared using == or != operators. "
            "Due to the inherent imprecision of floating-point arithmetic, values that appear "
            "equal may differ by tiny amounts (e.g., 0.1 + 0.2 != 0.3). "
            "This leads to unexpected comparison results and hard-to-find bugs."
        ),
        severity=Severity.MEDIUM,
        category=QualityCategory.NUMERIC_PRECISION,
        patterns={
            # Matches: float/double variable == or != comparison
            "csharp": LanguagePattern(
                r'(?:float|double)\s+\w+[^;]*(?:==|!=)\s*(?:\d+\.|\w+)',
                flags=re.IGNORECASE
            ),
            # Also match comparison patterns
            "csharp_alt": LanguagePattern(
                r'\w+\s*(?:==|!=)\s*\w+[^;]*//.*(?:float|double)',
                flags=re.IGNORECASE
            ),
            "java": LanguagePattern(
                r'(?:float|double)\s+\w+[^;]*(?:==|!=)',
                flags=re.IGNORECASE
            ),
            "javascript": LanguagePattern(
                r'(?:===|!==|==|!=)\s*(?:\d+\.\d+|\w+\s*[\+\-\*\/]\s*\d+\.\d+)',
                flags=re.IGNORECASE
            ),
            "python": LanguagePattern(
                r'(?:float\s*\(|(?:\d+\.\d+))\s*(?:==|!=)',
                flags=re.IGNORECASE
            ),
        },
        fix_suggestion=(
            "Use epsilon-based comparison for floating-point equality:\n"
            "Math.Abs(a - b) < epsilon where epsilon is your acceptable tolerance."
        ),
        incorrect_example="""
// INCORRECT - may fail unexpectedly
double a = 0.1 + 0.2;
double b = 0.3;
if (a == b)  // This is FALSE due to floating-point imprecision!
{
    Console.WriteLine("Equal");
}
""",
        correct_example="""
// CORRECT - use epsilon comparison
const double epsilon = 1e-10;
double a = 0.1 + 0.2;
double b = 0.3;
if (Math.Abs(a - b) < epsilon)
{
    Console.WriteLine("Equal within tolerance");
}
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/floating-point-numeric-types",
            "https://floating-point-gui.de/errors/comparison/",
        ],
    ),

    # =========================================================================
    # CQ-003: File Operations Without Existence Check
    # =========================================================================
    CodeQualityRule(
        id="CQ-EXOGENOUS-001",
        title="File operation without existence check (exogenous exception risk)",
        description=(
            "File operations (Open, Read, Delete) are performed without first checking "
            "if the file exists. While exceptions can be caught, it's more efficient and "
            "cleaner to check preconditions before operations. This is an 'exogenous exception' "
            "that can and should be prevented through defensive coding."
        ),
        severity=Severity.LOW,
        category=QualityCategory.DEFENSIVE_CODING,
        patterns={
            # File.Open/Read/Delete without preceding File.Exists
            "csharp": LanguagePattern(
                r'File\.(?:Open|ReadAll|Delete|Move|Copy)\s*\([^)]+\)'
                r'(?!.*File\.Exists)',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "vbnet": LanguagePattern(
                r'(?:File|FileSystem)\.(?:Open|ReadAll|Delete|Move|Copy)\s*\([^)]+\)'
                r'(?!.*File\.Exists)',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'new\s+File(?:Input|Output)Stream\s*\([^)]+\)',
                flags=re.IGNORECASE
            ),
            "python": LanguagePattern(
                r'open\s*\([^)]+\)(?!.*os\.path\.exists|.*Path\([^)]+\)\.exists)',
                flags=re.IGNORECASE
            ),
        },
        fix_suggestion=(
            "Check if the file exists before performing operations:\n"
            "if (File.Exists(path)) { /* operation */ } else { /* handle missing file */ }"
        ),
        incorrect_example="""
// INCORRECT - exception as flow control
try
{
    var content = File.ReadAllText(filePath);
}
catch (FileNotFoundException)
{
    // Handle missing file
}
""",
        correct_example="""
// CORRECT - check existence first
if (File.Exists(filePath))
{
    var content = File.ReadAllText(filePath);
}
else
{
    // Handle missing file without exception
}
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/standard/io/handling-io-errors",
        ],
    ),

    # =========================================================================
    # CQ-004: Redundant Boolean Literal Comparison
    # =========================================================================
    CodeQualityRule(
        id="CQ-BOOL-001",
        title="Redundant boolean literal comparison",
        description=(
            "A boolean variable is compared to a boolean literal (true/false) instead of "
            "being used directly. This is redundant and reduces code readability. "
            "Boolean variables already represent a condition and don't need comparison."
        ),
        severity=Severity.INFO,
        category=QualityCategory.CODE_SMELL,
        patterns={
            # Matches: if (x == true), if (x == false), if (true == x)
            "csharp": LanguagePattern(
                r'(?:if|while|&&|\|\|)\s*\(\s*(?:\w+\s*==\s*(?:true|false)|(?:true|false)\s*==\s*\w+)\s*\)',
                flags=re.IGNORECASE
            ),
            "vbnet": LanguagePattern(
                r'(?:If|While|AndAlso|OrElse)\s+(?:\w+\s*=\s*(?:True|False)|(?:True|False)\s*=\s*\w+)',
                flags=re.IGNORECASE
            ),
            "java": LanguagePattern(
                r'(?:if|while|&&|\|\|)\s*\(\s*(?:\w+\s*==\s*(?:true|false)|(?:true|false)\s*==\s*\w+)\s*\)',
                flags=re.IGNORECASE
            ),
            "javascript": LanguagePattern(
                r'(?:if|while|&&|\|\|)\s*\(\s*(?:\w+\s*===?\s*(?:true|false)|(?:true|false)\s*===?\s*\w+)\s*\)',
                flags=re.IGNORECASE
            ),
            "python": LanguagePattern(
                r'(?:if|while|and|or)\s+(?:\w+\s*==\s*(?:True|False)|(?:True|False)\s*==\s*\w+)',
                flags=re.IGNORECASE
            ),
        },
        fix_suggestion=(
            "Use the boolean variable directly:\n"
            "Instead of 'if (isValid == true)' use 'if (isValid)'\n"
            "Instead of 'if (isValid == false)' use 'if (!isValid)'"
        ),
        incorrect_example="""
// INCORRECT - redundant comparison
bool isActive = true;
if (isActive == true)  // Unnecessary comparison
{
    DoSomething();
}
""",
        correct_example="""
// CORRECT - use boolean directly
bool isActive = true;
if (isActive)  // Clean and readable
{
    DoSomething();
}
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/bool",
        ],
    ),

    # =========================================================================
    # CQ-005: Exception Re-throw with Stack Trace Loss
    # =========================================================================
    CodeQualityRule(
        id="CQ-EXCEPTION-001",
        title="Exception re-thrown with 'throw ex' loses original stack trace",
        description=(
            "An exception is caught and re-thrown using 'throw ex;' instead of 'throw;'. "
            "This resets the stack trace to the current location, losing the original "
            "exception origin. This makes debugging significantly harder as you cannot "
            "see where the exception actually occurred."
        ),
        severity=Severity.HIGH,
        category=QualityCategory.EXCEPTION_HANDLING,
        patterns={
            # Matches: catch (Exception ex) { ... throw ex; }
            "csharp": LanguagePattern(
                r'catch\s*\([^)]*\b(\w+)\s*\)[^}]*throw\s+\1\s*;',
                flags=re.IGNORECASE | re.DOTALL
            ),
            # Alternative pattern for simpler detection
            "csharp_simple": LanguagePattern(
                r'throw\s+(?:ex|e|exception|err)\s*;',
                flags=re.IGNORECASE
            ),
            "vbnet": LanguagePattern(
                r'Catch\s+(\w+)\s+As\s+Exception[^}]*Throw\s+\1',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'catch\s*\([^)]*\b(\w+)\s*\)[^}]*throw\s+\1\s*;',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "python": LanguagePattern(
                r'except\s+\w+\s+as\s+(\w+)\s*:[^}]*raise\s+\1(?:\s|$)',
                flags=re.IGNORECASE | re.DOTALL
            ),
        },
        fix_suggestion=(
            "Use 'throw;' without the exception variable to preserve the stack trace:\n"
            "catch (Exception ex) { Log(ex); throw; }  // Preserves original stack trace"
        ),
        incorrect_example="""
// INCORRECT - loses original stack trace
try
{
    SomeOperation();
}
catch (Exception ex)
{
    Logger.Log(ex);
    throw ex;  // Stack trace now points HERE, not to SomeOperation()!
}
""",
        correct_example="""
// CORRECT - preserves original stack trace
try
{
    SomeOperation();
}
catch (Exception ex)
{
    Logger.Log(ex);
    throw;  // Re-throws with original stack trace intact
}
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/csharp/fundamentals/exceptions/creating-and-throwing-exceptions",
            "https://docs.microsoft.com/en-us/dotnet/standard/exceptions/best-practices-for-exceptions",
        ],
    ),

    # =========================================================================
    # CQ-006: Empty Catch Block
    # =========================================================================
    CodeQualityRule(
        id="CQ-EXCEPTION-002",
        title="Empty catch block swallows exceptions silently",
        description=(
            "An exception is caught but the catch block is empty or only contains a comment. "
            "This silently swallows errors, making bugs invisible and extremely hard to diagnose. "
            "At minimum, exceptions should be logged."
        ),
        severity=Severity.HIGH,
        category=QualityCategory.EXCEPTION_HANDLING,
        patterns={
            # Empty catch blocks
            "csharp": LanguagePattern(
                r'catch\s*(?:\([^)]*\))?\s*\{\s*(?://[^\n]*\n\s*)?\}',
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "vbnet": LanguagePattern(
                r'Catch\s*(?:\w+\s+As\s+\w+)?\s*\n\s*(?:\'[^\n]*\n\s*)?End\s+Try',
                flags=re.IGNORECASE
            ),
            "java": LanguagePattern(
                r'catch\s*\([^)]*\)\s*\{\s*(?://[^\n]*\n\s*)?\}',
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "javascript": LanguagePattern(
                r'catch\s*\([^)]*\)\s*\{\s*(?://[^\n]*\n\s*)?\}',
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "python": LanguagePattern(
                r'except\s*(?:\w+)?(?:\s+as\s+\w+)?\s*:\s*\n\s*pass\s*(?:\n|$)',
                flags=re.IGNORECASE | re.MULTILINE
            ),
        },
        fix_suggestion=(
            "At minimum, log the exception:\n"
            "catch (Exception ex) { Logger.Error(ex); throw; }\n"
            "Or explicitly document why it's intentionally ignored."
        ),
        incorrect_example="""
// INCORRECT - silent failure
try
{
    SomeOperation();
}
catch (Exception)
{
    // Swallowed - bugs will be invisible!
}
""",
        correct_example="""
// CORRECT - at least log the exception
try
{
    SomeOperation();
}
catch (Exception ex)
{
    Logger.Warning($"Operation failed: {ex.Message}");
    // Decide: rethrow, return default, or handle specifically
}
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/standard/exceptions/best-practices-for-exceptions",
        ],
    ),

    # =========================================================================
    # CQ-007: String Concatenation in Loop
    # =========================================================================
    CodeQualityRule(
        id="CQ-PERF-001",
        title="String concatenation in loop (performance issue)",
        description=(
            "Strings are concatenated using += inside a loop. Since strings are immutable, "
            "each concatenation creates a new string object, resulting in O(n²) complexity. "
            "For large iterations, this causes significant performance degradation. "
            "Use StringBuilder instead."
        ),
        severity=Severity.MEDIUM,
        category=QualityCategory.CODE_SMELL,
        patterns={
            "csharp": LanguagePattern(
                r'(?:for|foreach|while)\s*[^{]*\{[^}]*\w+\s*\+=\s*["\'][^}]*\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "vbnet": LanguagePattern(
                r'(?:For|For\s+Each|While|Do)[^}]*\w+\s*&=\s*["\']',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'(?:for|while)\s*[^{]*\{[^}]*\w+\s*\+=\s*["\'][^}]*\}',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "python": LanguagePattern(
                r'(?:for|while)\s+[^:]+:[^}]*\w+\s*\+=\s*["\']',
                flags=re.IGNORECASE | re.DOTALL
            ),
        },
        fix_suggestion=(
            "Use StringBuilder for string concatenation in loops:\n"
            "var sb = new StringBuilder();\n"
            "foreach (var item in items) { sb.Append(item); }\n"
            "var result = sb.ToString();"
        ),
        incorrect_example="""
// INCORRECT - O(n²) complexity
string result = "";
foreach (var item in items)
{
    result += item.ToString();  // Creates new string each iteration!
}
""",
        correct_example="""
// CORRECT - O(n) complexity
var sb = new StringBuilder();
foreach (var item in items)
{
    sb.Append(item.ToString());
}
var result = sb.ToString();
""",
        references=[
            "https://docs.microsoft.com/en-us/dotnet/api/system.text.stringbuilder",
        ],
    ),

    # =========================================================================
    # CQ-008: Async Void Method
    # =========================================================================
    CodeQualityRule(
        id="CQ-ASYNC-001",
        title="Async void method (except event handlers)",
        description=(
            "An async method returns void instead of Task. Async void methods cannot be awaited, "
            "their exceptions cannot be caught with try/catch, and they can cause unexpected "
            "application crashes. Only use async void for event handlers."
        ),
        severity=Severity.HIGH,
        category=QualityCategory.EXCEPTION_HANDLING,
        patterns={
            # async void method (excluding common event handler patterns)
            "csharp": LanguagePattern(
                r'async\s+void\s+(?!On\w+|Handle\w+|\w+_\w+)\w+\s*\(',
                flags=re.IGNORECASE
            ),
        },
        fix_suggestion=(
            "Return Task instead of void for async methods:\n"
            "async Task DoSomethingAsync() instead of async void DoSomethingAsync()"
        ),
        incorrect_example="""
// INCORRECT - exceptions will crash the app
async void ProcessDataAsync()
{
    await SomeOperationAsync();  // If this throws, app may crash!
}
""",
        correct_example="""
// CORRECT - exceptions can be properly handled
async Task ProcessDataAsync()
{
    await SomeOperationAsync();
}
""",
        references=[
            "https://docs.microsoft.com/en-us/archive/msdn-magazine/2013/march/async-await-best-practices-in-asynchronous-programming",
        ],
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class CodeQualityScanner(BaseScanner):
    """
    Scanner for common programming mistakes and code smells.

    Detects issues that lead to bugs, unexpected behavior,
    or maintainability problems.
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in CODE_QUALITY_RULES:
            self._compiled_patterns[rule.id] = {}
            for lang, lang_pattern in rule.patterns.items():
                # Handle language variants (e.g., csharp_alt)
                base_lang = lang.split('_')[0]
                try:
                    self._compiled_patterns[rule.id][lang] = re.compile(
                        lang_pattern.pattern,
                        lang_pattern.flags
                    )
                except re.error as e:
                    logger.warning(f"Invalid regex for {rule.id}/{lang}: {e}")

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.CODE_QUALITY

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

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute code quality scan."""
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

                for rule in CODE_QUALITY_RULES:
                    # Check for patterns in this language
                    for pattern_key, compiled_pattern in self._compiled_patterns.get(rule.id, {}).items():
                        # Match base language
                        if not pattern_key.startswith(language):
                            continue

                        for match in compiled_pattern.finditer(content):
                            # Calculate line number
                            line_start = content[:match.start()].count("\n") + 1
                            line_end = content[:match.end()].count("\n") + 1

                            # Get snippet
                            snippet_start = max(0, line_start - 2)
                            snippet_end = min(len(lines), line_end + 3)
                            snippet = "\n".join(lines[snippet_start:snippet_end])

                            finding = SecurityFinding(
                                id=f"cq-{rule.id}-{file_path}:{line_start}",
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
                                cwe_ids=[],  # These are code quality, not security CWEs
                                category=rule.category.value,
                                tags={f"lang:{language}", "code-quality"},
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
            "total_rules": len(CODE_QUALITY_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "category": rule.category.value,
                    "languages": [k.split('_')[0] for k in rule.patterns.keys()],
                }
                for rule in CODE_QUALITY_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_code_quality_scanner() -> CodeQualityScanner:
    """Factory function to create code quality scanner."""
    return CodeQualityScanner()
