"""
Boolean Logic Detector - Boolean/Comparison/Precedence Error Detection.

Fase 36: Detects boolean logic and comparison errors across multiple languages:
- CWE-480: Use of Incorrect Operator
- CWE-783: Operator Precedence Logic Error
- CWE-843: Access of Resource Using Incompatible Type
- CWE-1077: Floating Point Comparison with Incorrect Operator
- CWE-476: NULL Pointer Dereference
- CWE-768: Incorrect Short Circuit Evaluation
- CWE-570: Expression is Always False
- CWE-571: Expression is Always True

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
# BOOLEAN LOGIC RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class BooleanLogicRule:
    """A boolean logic rule with language-specific patterns."""
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

BOOLEAN_LOGIC_RULES: List[BooleanLogicRule] = [
    # =========================================================================
    # BL001: Bitwise AND in Boolean Context (CWE-480)
    # =========================================================================
    BooleanLogicRule(
        id="BL001",
        title="Bitwise AND (&) used in boolean context",
        description=(
            "A single ampersand (&) is used where a logical AND (&&) was likely intended. "
            "Bitwise AND does not short-circuit and evaluates both operands. In boolean "
            "context, this can cause unexpected behavior and null pointer exceptions."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-480"],
        category="operator_error",
        patterns={
            "javascript": LanguagePattern(
                r'if\s*\([^)]*[^&]&[^&][^)]*\)',
            ),
            "java": LanguagePattern(
                r'if\s*\([^)]*(?:true|false|\w+\s*(?:==|!=))[^)]*[^&]&[^&][^)]*\)',
            ),
            "csharp": LanguagePattern(
                r'if\s*\([^)]*(?:true|false|\w+\s*(?:==|!=))[^)]*[^&]&[^&][^)]*\)',
            ),
            "cpp": LanguagePattern(
                r'if\s*\([^)]*[^&]&[^&][^)]*\)',
            ),
            "php": LanguagePattern(
                r'if\s*\([^)]*[^&]&[^&][^)]*\)',
            ),
        },
        fix_suggestion="Use && for logical AND in conditions. The single & is bitwise AND and does not short-circuit.",
        false_positive_patterns=[
            r'&\s*0x', r'&\s*\d+', r'FLAG', r'MASK',  # Intentional bitwise operations
        ],
    ),

    # =========================================================================
    # BL002: Bitwise OR in Boolean Context (CWE-480)
    # =========================================================================
    BooleanLogicRule(
        id="BL002",
        title="Bitwise OR (|) used in boolean context",
        description=(
            "A single pipe (|) is used where a logical OR (||) was likely intended. "
            "Bitwise OR does not short-circuit and evaluates both operands. This can "
            "cause unexpected behavior and performance issues."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-480"],
        category="operator_error",
        patterns={
            "javascript": LanguagePattern(
                r'if\s*\([^)]*[^|]\|[^|][^)]*\)',
            ),
            "java": LanguagePattern(
                r'if\s*\([^)]*(?:true|false|\w+\s*(?:==|!=))[^)]*[^|]\|[^|][^)]*\)',
            ),
            "csharp": LanguagePattern(
                r'if\s*\([^)]*(?:true|false|\w+\s*(?:==|!=))[^)]*[^|]\|[^|][^)]*\)',
            ),
            "cpp": LanguagePattern(
                r'if\s*\([^)]*[^|]\|[^|][^)]*\)',
            ),
            "php": LanguagePattern(
                r'if\s*\([^)]*[^|]\|[^|][^)]*\)',
            ),
        },
        fix_suggestion="Use || for logical OR in conditions. The single | is bitwise OR and does not short-circuit.",
        false_positive_patterns=[
            r'\|\s*0x', r'\|\s*\d+', r'FLAG', r'MASK',  # Intentional bitwise operations
        ],
    ),

    # =========================================================================
    # BL010: Operator Precedence Issue (CWE-783)
    # =========================================================================
    BooleanLogicRule(
        id="BL010",
        title="Operator precedence may cause unexpected behavior",
        description=(
            "An expression mixes bitwise operators with comparison operators without "
            "explicit parentheses. Comparison operators (== != < >) have higher precedence "
            "than bitwise operators (& | ^), which often leads to unexpected results."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-783"],
        category="precedence_error",
        patterns={
            "javascript": LanguagePattern(
                r'\w+\s*[&|^]\s*\w+\s*(?:==|!=|<|>)',
            ),
            "java": LanguagePattern(
                r'\w+\s*[&|^]\s*\w+\s*(?:==|!=|<|>)',
            ),
            "csharp": LanguagePattern(
                r'\w+\s*[&|^]\s*\w+\s*(?:==|!=|<|>)',
            ),
            "cpp": LanguagePattern(
                r'\w+\s*[&|^]\s*\w+\s*(?:==|!=|<|>)',
            ),
        },
        fix_suggestion="Use explicit parentheses to clarify intent: (a & b) == c or a & (b == c)",
    ),

    # =========================================================================
    # BL011: AND/OR Precedence Ambiguity (CWE-783)
    # =========================================================================
    BooleanLogicRule(
        id="BL011",
        title="AND/OR precedence ambiguity without parentheses",
        description=(
            "An expression mixes && and || without parentheses. && has higher precedence "
            "than ||, so 'a || b && c' evaluates as 'a || (b && c)', not '(a || b) && c'. "
            "This is a common source of logic bugs."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-783"],
        category="precedence_error",
        patterns={
            "javascript": LanguagePattern(
                r'\w+\s*\|\|\s*\w+\s*&&\s*\w+',
            ),
            "java": LanguagePattern(
                r'\w+\s*\|\|\s*\w+\s*&&\s*\w+',
            ),
            "csharp": LanguagePattern(
                r'\w+\s*\|\|\s*\w+\s*&&\s*\w+',
            ),
            "cpp": LanguagePattern(
                r'\w+\s*\|\|\s*\w+\s*&&\s*\w+',
            ),
            "python": LanguagePattern(
                r'\w+\s+or\s+\w+\s+and\s+\w+',
            ),
            "php": LanguagePattern(
                r'\w+\s*\|\|\s*\w+\s*&&\s*\w+',
            ),
        },
        fix_suggestion="Use explicit parentheses to clarify intent: (a || b) && c or a || (b && c)",
        false_positive_patterns=[
            r'\(\s*\w+\s*\|\|\s*\w+\s*\)\s*&&',  # Already has (a || b) &&
            r'&&\s*\(\s*\w+\s*\|\|\s*\w+\s*\)',  # Already has && (a || b)
        ],
    ),

    # =========================================================================
    # BL020: == Instead of === in JavaScript (CWE-843)
    # =========================================================================
    BooleanLogicRule(
        id="BL020",
        title="Loose equality (==) instead of strict equality (===)",
        description=(
            "JavaScript's == operator performs type coercion which can lead to unexpected "
            "results: '0' == false is true, null == undefined is true. "
            "Always use === for predictable comparisons."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-843"],
        category="comparison_error",
        patterns={
            "javascript": LanguagePattern(
                r'(?:if|while|return|\?|&&|\|\|)\s*\([^)]*[^!=<>]==[^=][^)]*\)',
            ),
        },
        fix_suggestion="Use === instead of == for strict equality comparison without type coercion.",
        false_positive_patterns=[
            r'null\s*==', r'==\s*null',  # null check is a valid use of ==
        ],
    ),

    # =========================================================================
    # BL021: Float Equality Comparison (CWE-1077)
    # =========================================================================
    BooleanLogicRule(
        id="BL021",
        title="Direct equality comparison of floating-point numbers",
        description=(
            "Floating-point numbers are compared using == or !=. Due to precision issues, "
            "values that appear equal may differ slightly (e.g., 0.1 + 0.2 != 0.3). "
            "This leads to unexpected comparison results."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1077"],
        category="comparison_error",
        patterns={
            "python": LanguagePattern(
                r'(?:float\s*\([^)]+\)|[\d]+\.[\d]+)\s*(?:==|!=)',
            ),
            "javascript": LanguagePattern(
                r'(?:parseFloat\s*\([^)]+\)|[\d]+\.[\d]+)\s*(?:===|!==|==|!=)',
            ),
            "java": LanguagePattern(
                r'(?:float|double)\s+\w+[^;]*(?:==|!=)',
            ),
            "csharp": LanguagePattern(
                r'(?:float|double|decimal)\s+\w+[^;]*(?:==|!=)',
            ),
            "cpp": LanguagePattern(
                r'(?:float|double)\s+\w+[^;]*(?:==|!=)',
            ),
        },
        fix_suggestion="Use epsilon comparison: Math.abs(a - b) < epsilon instead of a == b",
    ),

    # =========================================================================
    # BL022: Chained Comparison in Non-Python Languages (CWE-480)
    # =========================================================================
    BooleanLogicRule(
        id="BL022",
        title="Chained comparison does not work as expected",
        description=(
            "A chained comparison like 'a < b < c' is used in a language where it does not "
            "work as in Python. In JavaScript, 'a < b < c' evaluates as '(a < b) < c', "
            "where the left result is a boolean, leading to unexpected behavior."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-480"],
        category="comparison_error",
        patterns={
            "javascript": LanguagePattern(
                r'\w+\s*(?:<|>|<=|>=)\s*\w+\s*(?:<|>|<=|>=)\s*\w+',
            ),
            "java": LanguagePattern(
                r'\w+\s*(?:<|>|<=|>=)\s*\w+\s*(?:<|>|<=|>=)\s*\w+',
            ),
            "csharp": LanguagePattern(
                r'\w+\s*(?:<|>|<=|>=)\s*\w+\s*(?:<|>|<=|>=)\s*\w+',
            ),
            "cpp": LanguagePattern(
                r'\w+\s*(?:<|>|<=|>=)\s*\w+\s*(?:<|>|<=|>=)\s*\w+',
            ),
        },
        fix_suggestion="Use explicit logical AND: (a < b && b < c) instead of a < b < c",
    ),

    # =========================================================================
    # BL023: String Comparison with == in Java (CWE-480)
    # =========================================================================
    BooleanLogicRule(
        id="BL023",
        title="String compared with == instead of .equals() in Java",
        description=(
            "Strings are compared using == or != which compares object references, not "
            "content. Two strings with the same content may be different objects. "
            "Always use .equals() for string content comparison."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-480"],
        category="comparison_error",
        patterns={
            "java": LanguagePattern(
                r'(?:String\s+)?\w+\s*(?:==|!=)\s*(?:"[^"]*"|\w+(?!\.equals))',
            ),
        },
        fix_suggestion="Use .equals() for string comparison: str1.equals(str2) instead of str1 == str2",
        false_positive_patterns=[
            r'==\s*null', r'null\s*==', r'!=\s*null', r'null\s*!=',
        ],
    ),

    # =========================================================================
    # BL030: Null Check AFTER Dereference (CWE-476)
    # =========================================================================
    BooleanLogicRule(
        id="BL030",
        title="Null check performed after pointer/reference is already used",
        description=(
            "A null check is performed after the object has already been dereferenced. "
            "If the object is null, the code will have already thrown a NullPointerException "
            "before the check is reached."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-476"],
        category="null_error",
        patterns={
            "java": LanguagePattern(
                r'(\w+)\.(?:\w+\(\)|\w+)[^;]*;\s*(?:\n\s*)?if\s*\(\s*\1\s*(?:==|!=)\s*null',
                flags=re.MULTILINE
            ),
            "csharp": LanguagePattern(
                r'(\w+)\.(?:\w+\(\)|\w+)[^;]*;\s*(?:\n\s*)?if\s*\(\s*\1\s*(?:==|!=)\s*null',
                flags=re.MULTILINE
            ),
            "javascript": LanguagePattern(
                r'(\w+)\.(?:\w+\(\)|\w+)[^;]*;\s*(?:\n\s*)?if\s*\(\s*\1\s*(?:===?|!==?)\s*(?:null|undefined)',
                flags=re.MULTILINE
            ),
        },
        fix_suggestion="Move the null check before using the object: if (obj != null) { obj.method(); }",
    ),

    # =========================================================================
    # BL031: Side Effect in Short-Circuit Evaluation (CWE-768)
    # =========================================================================
    BooleanLogicRule(
        id="BL031",
        title="Side effect in short-circuit evaluation may be skipped",
        description=(
            "An expression with side effects (function call, increment, assignment) is used "
            "in a short-circuit evaluation (&&, ||). If the left operand determines the "
            "result, the right operand (with side effects) may not be evaluated."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-768"],
        category="evaluation_error",
        patterns={
            "javascript": LanguagePattern(
                r'(?:&&|\|\|)\s*(?:\w+\(\)|[+][+]|--|\w+\s*=)',
            ),
            "java": LanguagePattern(
                r'(?:&&|\|\|)\s*(?:\w+\(\)|[+][+]|--)',
            ),
            "csharp": LanguagePattern(
                r'(?:&&|\|\|)\s*(?:\w+\(\)|[+][+]|--)',
            ),
            "cpp": LanguagePattern(
                r'(?:&&|\|\|)\s*(?:\w+\(\)|[+][+]|--)',
            ),
        },
        fix_suggestion="Move side effects outside the conditional expression. Evaluate before the condition if both must execute.",
        false_positive_patterns=[
            r'&&\s*return', r'\|\|\s*return', r'&&\s*throw', r'\|\|\s*throw',
        ],
    ),

    # =========================================================================
    # BL040: Tautology - Always True (CWE-571)
    # =========================================================================
    BooleanLogicRule(
        id="BL040",
        title="Condition is always true (tautology)",
        description=(
            "A condition will always evaluate to true regardless of input. "
            "This usually indicates a logic error or dead code. "
            "Common examples: x >= 0 when x is unsigned, or x == x."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-571"],
        category="logic_error",
        patterns={
            "javascript": LanguagePattern(
                r'(?:if|while)\s*\(\s*(?:true|1\s*==\s*1|\w+\s*==\s*\w+)\s*\)',
            ),
            "java": LanguagePattern(
                r'(?:if|while)\s*\(\s*(?:true|1\s*==\s*1|(\w+)\s*==\s*\1)\s*\)',
            ),
            "csharp": LanguagePattern(
                r'(?:if|while)\s*\(\s*(?:true|1\s*==\s*1|(\w+)\s*==\s*\1)\s*\)',
            ),
            "cpp": LanguagePattern(
                r'(?:if|while)\s*\(\s*(?:true|1\s*==\s*1|(\w+)\s*==\s*\1)\s*\)',
            ),
            "python": LanguagePattern(
                r'(?:if|while)\s+(?:True|1\s*==\s*1)\s*:',
            ),
        },
        fix_suggestion="Remove the always-true condition or fix the logic error.",
        false_positive_patterns=[
            r'while\s*\(\s*true\s*\).*break',  # Intentional infinite loop with break
        ],
    ),

    # =========================================================================
    # BL041: Contradiction - Always False (CWE-570)
    # =========================================================================
    BooleanLogicRule(
        id="BL041",
        title="Condition is always false (contradiction)",
        description=(
            "A condition will always evaluate to false regardless of input. "
            "This makes the code inside unreachable (dead code). "
            "Common examples: x < 0 when x is unsigned, or x != x (except NaN)."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-570"],
        category="logic_error",
        patterns={
            "javascript": LanguagePattern(
                r'if\s*\(\s*(?:false|1\s*==\s*2|(\w+)\s*!=\s*\1)\s*\)',
            ),
            "java": LanguagePattern(
                r'if\s*\(\s*(?:false|1\s*==\s*2|(\w+)\s*!=\s*\1)\s*\)',
            ),
            "csharp": LanguagePattern(
                r'if\s*\(\s*(?:false|1\s*==\s*2|(\w+)\s*!=\s*\1)\s*\)',
            ),
            "cpp": LanguagePattern(
                r'if\s*\(\s*(?:false|1\s*==\s*2|(\w+)\s*!=\s*\1)\s*\)',
            ),
            "python": LanguagePattern(
                r'if\s+(?:False|1\s*==\s*2)\s*:',
            ),
        },
        fix_suggestion="Remove the dead code or fix the logic error causing the condition to always be false.",
    ),

    # =========================================================================
    # KB2/KB3/KB4 PATTERNS - Added from Python-Errors and LogicalErrors repos
    # =========================================================================

    # =========================================================================
    # BL050: Python 'is' vs '==' for Value Comparison (CWE-595)
    # =========================================================================
    BooleanLogicRule(
        id="BL050",
        title="Using 'is' operator for value comparison instead of '=='",
        description=(
            "The 'is' operator checks identity (same object in memory), not equality. "
            "While it works for small integers (-5 to 256) and interned strings due to "
            "Python's caching, it fails for larger values. Use '==' for value comparison."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-595", "CWE-480"],
        category="comparison_error",
        patterns={
            "python": LanguagePattern(
                r'if\s+\w+\s+is\s+(?:\d{4,}|["\'][^"\']{2,}["\']|\[|\{|\()',
            ),
        },
        fix_suggestion="Use '==' for value comparison. Reserve 'is' for identity checks (None, True, False, singletons).",
        false_positive_patterns=[
            r'is\s+None', r'is\s+True', r'is\s+False', r'is\s+not\s+None',
        ],
    ),

    # =========================================================================
    # BL051: Mutable Default Argument (CWE-547)
    # =========================================================================
    BooleanLogicRule(
        id="BL051",
        title="Mutable default argument in function definition",
        description=(
            "A mutable object (list, dict, set) is used as a default argument. "
            "Default arguments are evaluated once at function definition, not at each call. "
            "Mutations persist across calls, causing unexpected behavior."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-547"],
        category="logic_error",
        patterns={
            "python": LanguagePattern(
                r'def\s+\w+\s*\([^)]*=\s*(?:\[\]|\{\}|set\(\))',
            ),
        },
        fix_suggestion="Use None as default and create the mutable object inside the function: def func(items=None): items = items or []",
    ),

    # =========================================================================
    # BL052: Division by Zero Risk (CWE-369)
    # =========================================================================
    BooleanLogicRule(
        id="BL052",
        title="Potential division by zero without guard",
        description=(
            "A division operation uses a variable that could be zero without "
            "a preceding check. Division by zero causes ZeroDivisionError in Python, "
            "undefined behavior in C/C++, and ArithmeticException in Java/C#."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-369"],
        category="arithmetic_error",
        patterns={
            "python": LanguagePattern(
                r'(?<!/)\s*/\s*(?!\*|/)\s*\w+(?!\s*(?:!=|>|if\s+\w+))',
                flags=re.MULTILINE
            ),
            "javascript": LanguagePattern(
                r'(?<!/)\s*/\s*(?!/)\s*\w+(?!\s*(?:!==?|>|&&))',
            ),
            "java": LanguagePattern(
                r'(?<!/)\s*/\s*(?!/)\s*\w+(?!\s*(?:!=|>|&&))',
            ),
            "csharp": LanguagePattern(
                r'(?<!/)\s*/\s*(?!/)\s*\w+(?!\s*(?:!=|>|&&))',
            ),
            "cpp": LanguagePattern(
                r'(?<!/)\s*/\s*(?!/)\s*\w+(?!\s*(?:!=|>|&&))',
            ),
        },
        fix_suggestion="Add a zero check before division: if (divisor != 0) { result = dividend / divisor; }",
        false_positive_patterns=[
            r'if\s*\([^)]*!=\s*0', r'if\s*\([^)]*>\s*0', r'\.length', r'\.size',
        ],
    ),

    # =========================================================================
    # BL053: Integer Literal Comparison with 'is' (Python) (CWE-595)
    # =========================================================================
    BooleanLogicRule(
        id="BL053",
        title="Comparing integers using 'is' instead of '=='",
        description=(
            "Python caches small integers (-5 to 256), so 'is' works for them by accident. "
            "For larger integers, 'is' fails because Python creates new objects. "
            "This leads to bugs that only manifest with certain values."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-595"],
        category="comparison_error",
        patterns={
            "python": LanguagePattern(
                r'\w+\s+is\s+(?:25[7-9]|2[6-9]\d|[3-9]\d{2,}|\d{4,})',
            ),
        },
        fix_suggestion="Always use '==' for integer comparison. 'is' only checks object identity.",
    ),

    # =========================================================================
    # BL054: String Concatenation in Loop (Performance Anti-Pattern)
    # =========================================================================
    BooleanLogicRule(
        id="BL054",
        title="String concatenation inside loop (performance issue)",
        description=(
            "Strings are immutable, so concatenation creates new objects each iteration. "
            "For N iterations, this is O(N^2) complexity. Use list.append() + ''.join() "
            "or StringBuilder/StringBuffer for O(N) performance."
        ),
        severity=Severity.LOW,
        cwe_ids=["CWE-407"],
        category="performance_error",
        patterns={
            "python": LanguagePattern(
                r'for\s+.*:\s*\n(?:[^\n]*\n)*?[^\n]*\w+\s*\+=\s*["\']',
                flags=re.MULTILINE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'for\s*\([^)]+\)\s*\{[^}]*\w+\s*\+=\s*["\']',
                flags=re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'for(?:each)?\s*\([^)]+\)\s*\{[^}]*\w+\s*\+=\s*["\']',
                flags=re.DOTALL
            ),
        },
        fix_suggestion="Use StringBuilder (Java/C#) or list.append() + ''.join() (Python) for string building in loops.",
    ),

    # =========================================================================
    # BL055: Late Binding Closure in Loop (Python) (CWE-758)
    # =========================================================================
    BooleanLogicRule(
        id="BL055",
        title="Late binding closure captures loop variable",
        description=(
            "A lambda or nested function inside a loop captures the loop variable by reference. "
            "All closures will see the final value of the loop variable, not the value at creation. "
            "This is a common source of bugs in callbacks and event handlers."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-758"],
        category="logic_error",
        patterns={
            "python": LanguagePattern(
                r'for\s+(\w+)\s+in\s+.*:\s*\n(?:[^\n]*\n)*?[^\n]*lambda[^:]*:\s*[^\n]*\1',
                flags=re.MULTILINE
            ),
        },
        fix_suggestion="Capture the value with a default argument: lambda x=i: x, or use functools.partial().",
    ),

    # =========================================================================
    # BL056: Modifying Collection While Iterating (CWE-672)
    # =========================================================================
    BooleanLogicRule(
        id="BL056",
        title="Modifying collection while iterating over it",
        description=(
            "Adding or removing items from a collection while iterating causes "
            "RuntimeError in Python, ConcurrentModificationException in Java, "
            "or undefined behavior in C++. Iterate over a copy instead."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-672"],
        category="logic_error",
        patterns={
            "python": LanguagePattern(
                r'for\s+\w+\s+in\s+(\w+)\s*:\s*\n(?:[^\n]*\n)*?[^\n]*\1\.(?:append|remove|pop|clear|insert)',
                flags=re.MULTILINE
            ),
            "java": LanguagePattern(
                r'for\s*\([^)]+:\s*(\w+)\)\s*\{[^}]*\1\.(?:add|remove|clear)',
                flags=re.DOTALL
            ),
        },
        fix_suggestion="Iterate over a copy: for item in list(items): or collect modifications and apply after loop.",
    ),

    # =========================================================================
    # BL057: Accidental Boolean Expression (C#/Java) (CWE-480)
    # =========================================================================
    BooleanLogicRule(
        id="BL057",
        title="Semicolon after if/while creates empty body",
        description=(
            "A semicolon immediately after if/while condition creates an empty statement body. "
            "The intended block executes unconditionally. This is a common typo that compiles "
            "but produces wrong behavior."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-480", "CWE-483"],
        category="logic_error",
        patterns={
            "csharp": LanguagePattern(
                r'if\s*\([^)]+\)\s*;',
            ),
            "java": LanguagePattern(
                r'if\s*\([^)]+\)\s*;',
            ),
            "cpp": LanguagePattern(
                r'if\s*\([^)]+\)\s*;',
            ),
        },
        fix_suggestion="Remove the semicolon and add braces: if (condition) { statement; }",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class BooleanLogicDetector(BaseScanner):
    """
    Detects boolean logic and comparison errors in code.

    Scans for operator confusion, precedence issues, comparison mistakes,
    null checking errors, and tautologies/contradictions.
    """

    SCANNER_VERSION = "1.1.0"  # KB2/KB3/KB4 patterns added

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in BOOLEAN_LOGIC_RULES:
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
        return ScannerType.BOOLEAN_LOGIC

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
        context: str = ""
    ) -> bool:
        """Check if match is a false positive."""
        fp_patterns = self._compiled_fp_patterns.get(rule_id, [])
        full_text = matched_text + " " + context

        for fp_pattern in fp_patterns:
            if fp_pattern.search(full_text):
                return True
        return False

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute boolean logic scan."""
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

                for rule in BOOLEAN_LOGIC_RULES:
                    # Get language-specific pattern
                    compiled_pattern = self._compiled_patterns.get(rule.id, {}).get(language)
                    if not compiled_pattern:
                        continue

                    for match in compiled_pattern.finditer(content):
                        # Calculate line number
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        # Get snippet
                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet = "\n".join(lines[snippet_start:snippet_end])

                        # Check for false positives
                        if self._is_false_positive(rule.id, match.group(), snippet):
                            continue

                        finding = SecurityFinding(
                            id=f"bl-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "boolean-logic"},
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
            "total_rules": len(BOOLEAN_LOGIC_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in BOOLEAN_LOGIC_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_boolean_logic_detector() -> BooleanLogicDetector:
    """Factory function to create boolean logic detector."""
    return BooleanLogicDetector()
