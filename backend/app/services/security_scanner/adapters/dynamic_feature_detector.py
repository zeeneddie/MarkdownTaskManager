"""
Dynamic Language Feature Detector - Unsafe Dynamic Code Patterns.

Detects security-sensitive dynamic language features across multiple languages:

JS Dynamic Property Access (5):
- DYN-PROP-001 to DYN-PROP-005: Bracket notation, dynamic deletion, computed
  property assignment, Object.defineProperty, prototype access

JS Dynamic Calls (4):
- DYN-CALL-001 to DYN-CALL-004: Computed function calls, computed method calls,
  Function constructor, setTimeout/setInterval with string

JS Dynamic Imports (3):
- DYN-IMPORT-001 to DYN-IMPORT-003: Variable require(), dynamic import(),
  require.resolve with user input

JS Eval-Adjacent (3):
- DYN-EVAL-001 to DYN-EVAL-003: document.write, script.src assignment,
  WebSocket URL from user input

Python Reflection (4):
- DYN-REFL-001 to DYN-REFL-004: getattr, setattr, __import__, globals/locals
  access with user input

Python Exec (3):
- DYN-EXEC-001 to DYN-EXEC-003: compile(), exec(), eval() with user data

Python Meta (3):
- DYN-META-001 to DYN-META-003: type() three-arg, __subclasses__(),
  __class__.__bases__ manipulation

Java Reflection (4):
- DYN-REFL-J001 to DYN-REFL-J004: Class.forName, Method.invoke,
  Constructor.newInstance, Field.set with user input

Java Deserialization (2):
- DYN-DESER-J001 to DYN-DESER-J002: URLClassLoader, ObjectInputStream.readObject

Java Proxy (2):
- DYN-PROXY-J001 to DYN-PROXY-J002: Proxy.newProxyInstance, MethodHandle.invokeWithArguments

Multi-language support: JavaScript, TypeScript, Python, Java
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
        extensions={".java", ".jsp"},
    ),
}


# =============================================================================
# DYNAMIC FEATURE RULES DATA STRUCTURE
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class DynamicFeatureRule:
    """A dynamic feature vulnerability rule with language-specific patterns."""
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
# JS DYNAMIC PROPERTY ACCESS (5 rules)
# =============================================================================

JS_DYNAMIC_PROPERTY_RULES: List[DynamicFeatureRule] = [
    # DYN-PROP-001: Bracket notation on DOM elements
    DynamicFeatureRule(
        id="DYN-PROP-001",
        title="Bracket notation property access on DOM elements",
        description=(
            "Using bracket notation with a variable to set properties on DOM elements "
            "can lead to XSS if the property name or value is user-controlled. "
            "Attackers may set innerHTML, outerHTML, or event handler properties."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-79"],
        category="dynamic_property_access",
        patterns={
            "javascript": LanguagePattern(
                r'(?:element|el|node|dom|document\.(?:getElementById|querySelector)\s*\([^)]*\))\s*\[\s*(?:variable|userInput|input|param|key|prop|attr|name)\s*\]\s*=',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'(?:element|el|node|dom|document\.(?:getElementById|querySelector)\s*\([^)]*\))\s*\[\s*(?:variable|userInput|input|param|key|prop|attr|name)\s*\]\s*=',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use an allowlist of safe property names. Validate the property name against "
            "known safe attributes before setting it on DOM elements."
        ),
        false_positive_patterns=[
            r'//\s*.*\[',
            r'\*\s+.*\[',
            r'test\(',
            r'describe\(',
            r'\.style\[',
            r'\.dataset\[',
        ],
        context_keywords=["request", "input", "user", "param", "query", "body"],
    ),

    # DYN-PROP-002: Dynamic property deletion
    DynamicFeatureRule(
        id="DYN-PROP-002",
        title="Dynamic property deletion with user-controlled key",
        description=(
            "Using the delete operator with a user-controlled property name allows "
            "attackers to remove arbitrary properties from objects, potentially "
            "disrupting application logic or security checks."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94"],
        category="dynamic_property_access",
        patterns={
            "javascript": LanguagePattern(
                r'delete\s+\w+\s*\[\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|key)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'delete\s+\w+\s*\[\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|key)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Validate the property key against an allowlist before deletion. "
            "Never allow user input to control which properties are deleted."
        ),
        false_positive_patterns=[
            r'//\s*delete',
            r'test\(',
            r'describe\(',
            r'\.hasOwnProperty\(',
        ],
    ),

    # DYN-PROP-003: Computed property assignment with user data
    DynamicFeatureRule(
        id="DYN-PROP-003",
        title="Computed property assignment with user-controlled data",
        description=(
            "Assigning values to dynamically computed object properties using user "
            "input can lead to prototype pollution or overwriting security-critical "
            "properties such as __proto__, constructor, or toString."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-79"],
        category="dynamic_property_access",
        patterns={
            "javascript": LanguagePattern(
                r'\w+\s*\[\s*(?:req\.(?:body|query|params)|input|userInput|data)\s*(?:\.\w+)?\s*\]\s*=\s*(?:req\.|input|user|data)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'\w+\s*\[\s*(?:req\.(?:body|query|params)|input|userInput|data)\s*(?:\.\w+)?\s*\]\s*=\s*(?:req\.|input|user|data)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use a Map or a validated allowlist of property names. "
            "Reject keys like __proto__, constructor, and prototype."
        ),
        false_positive_patterns=[
            r'//\s*\w+\[',
            r'Object\.freeze',
            r'Object\.seal',
            r'test\(',
        ],
    ),

    # DYN-PROP-004: Object.defineProperty with dynamic descriptor
    DynamicFeatureRule(
        id="DYN-PROP-004",
        title="Object.defineProperty with dynamic descriptor from user input",
        description=(
            "Using Object.defineProperty with user-controlled property name or "
            "descriptor allows attackers to redefine property behavior, including "
            "getters, setters, and configurability, leading to code injection."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94"],
        category="dynamic_property_access",
        patterns={
            "javascript": LanguagePattern(
                r'Object\.definePropert(?:y|ies)\s*\(\s*\w+\s*,\s*(?:req\.|params\.|body\.|query\.|input|user|data|key|prop)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'Object\.definePropert(?:y|ies)\s*\(\s*\w+\s*,\s*(?:req\.|params\.|body\.|query\.|input|user|data|key|prop)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never use user-controlled values as property names or descriptors "
            "in Object.defineProperty. Use a strict allowlist of property names."
        ),
        false_positive_patterns=[
            r'//\s*Object\.define',
            r'test\(',
            r'typeof\s+\w+\s*===',
        ],
    ),

    # DYN-PROP-005: Prototype access via bracket notation
    DynamicFeatureRule(
        id="DYN-PROP-005",
        title="Prototype access via bracket notation with user input",
        description=(
            "Accessing __proto__ or prototype via bracket notation with user-controlled "
            "keys enables prototype pollution attacks. Attackers can inject properties "
            "into Object.prototype, affecting all objects in the application."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1321"],
        category="dynamic_property_access",
        patterns={
            "javascript": LanguagePattern(
                r'\w+\s*\[\s*(?:["\']__proto__["\']|["\']prototype["\']|["\']constructor["\'])\s*\]',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'\w+\s*\[\s*(?:["\']__proto__["\']|["\']prototype["\']|["\']constructor["\'])\s*\]',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Reject keys matching __proto__, prototype, and constructor. "
            "Use Object.create(null) for lookup maps to avoid prototype chain access."
        ),
        false_positive_patterns=[
            r'//\s*.*__proto__',
            r'test\(',
            r'describe\(',
            r'hasOwnProperty',
            r'Object\.create\(null\)',
        ],
        context_keywords=["req", "input", "user", "body", "params", "query", "merge", "assign", "extend"],
        require_context=True,
        context_window_lines=5,
    ),
]


# =============================================================================
# JS DYNAMIC CALLS (4 rules)
# =============================================================================

JS_DYNAMIC_CALL_RULES: List[DynamicFeatureRule] = [
    # DYN-CALL-001: window[variable]() computed function call
    DynamicFeatureRule(
        id="DYN-CALL-001",
        title="Computed function call via window bracket notation",
        description=(
            "Calling functions via window[variable]() allows user-controlled strings "
            "to determine which global function executes. This is functionally "
            "equivalent to eval when the variable is user-controlled."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="dynamic_call",
        patterns={
            "javascript": LanguagePattern(
                r'(?:window|globalThis|global|self)\s*\[\s*(?:req\.|params\.|body\.|query\.|input|user|data|name|func|method|action)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'(?:window|globalThis|global|self)\s*\[\s*(?:req\.|params\.|body\.|query\.|input|user|data|name|func|method|action)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use a dispatch map of allowed function names: "
            "const handlers = { save: saveFunc, load: loadFunc }; handlers[action]?.()"
        ),
        false_positive_patterns=[
            r'//\s*window\[',
            r'test\(',
            r'typeof\s+window\[',
        ],
    ),

    # DYN-CALL-002: this[variable]() computed method call
    DynamicFeatureRule(
        id="DYN-CALL-002",
        title="Computed method call via this bracket notation",
        description=(
            "Using this[variable]() to invoke methods dynamically allows attackers "
            "to call arbitrary methods on the current object when the variable "
            "is user-controlled, potentially accessing private or dangerous methods."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="dynamic_call",
        patterns={
            "javascript": LanguagePattern(
                r'this\s*\[\s*(?:req\.|params\.|body\.|query\.|input|user|data|method|action|name)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'this\s*\[\s*(?:req\.|params\.|body\.|query\.|input|user|data|method|action|name)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use a Map or switch statement to dispatch to allowed methods. "
            "Validate method names against an explicit allowlist."
        ),
        false_positive_patterns=[
            r'//\s*this\[',
            r'test\(',
            r'describe\(',
        ],
        context_keywords=["request", "input", "user", "param", "query", "body"],
        require_context=True,
        context_window_lines=10,
    ),

    # DYN-CALL-003: new Function() constructor
    DynamicFeatureRule(
        id="DYN-CALL-003",
        title="Function constructor with dynamic code string",
        description=(
            "The Function constructor creates a new function from a string argument, "
            "similar to eval(). When the string is user-controlled, this enables "
            "arbitrary code execution in the application context."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="dynamic_call",
        patterns={
            "javascript": LanguagePattern(
                r'new\s+Function\s*\(\s*(?:[^)]*(?:req\.|params\.|body\.|query\.|input|user|data|\+|`[^`]*\$\{))',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'new\s+Function\s*\(\s*(?:[^)]*(?:req\.|params\.|body\.|query\.|input|user|data|\+|`[^`]*\$\{))',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never create functions from user-controlled strings. "
            "Use a safe expression evaluator or DSL parser instead."
        ),
        false_positive_patterns=[
            r'//\s*new\s+Function',
            r'test\(',
            r'describe\(',
            r'eslint-disable',
        ],
    ),

    # DYN-CALL-004: setTimeout/setInterval with string arg
    DynamicFeatureRule(
        id="DYN-CALL-004",
        title="setTimeout/setInterval with string argument",
        description=(
            "Passing a string to setTimeout or setInterval causes it to be evaluated "
            "as code, similar to eval(). When the string contains user input, this "
            "enables code injection."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="dynamic_call",
        patterns={
            "javascript": LanguagePattern(
                r'(?:setTimeout|setInterval)\s*\(\s*(?:["\'][^"\']*(?:req\.|input|user)|`[^`]*\$\{|["\'][^"\']*\+)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'(?:setTimeout|setInterval)\s*\(\s*(?:["\'][^"\']*(?:req\.|input|user)|`[^`]*\$\{|["\'][^"\']*\+)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Always pass a function reference to setTimeout/setInterval, never a string. "
            "Use: setTimeout(() => doSomething(param), delay)"
        ),
        false_positive_patterns=[
            r'//\s*setTimeout',
            r'setTimeout\s*\(\s*(?:function|\(\)|=>)',
            r'test\(',
        ],
    ),
]


# =============================================================================
# JS DYNAMIC IMPORTS (3 rules)
# =============================================================================

JS_DYNAMIC_IMPORT_RULES: List[DynamicFeatureRule] = [
    # DYN-IMPORT-001: require() with variable argument
    DynamicFeatureRule(
        id="DYN-IMPORT-001",
        title="Dynamic require() with variable argument",
        description=(
            "Using require() with a user-controlled path allows attackers to load "
            "arbitrary modules, potentially executing malicious code or accessing "
            "sensitive internal modules."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="dynamic_import",
        patterns={
            "javascript": LanguagePattern(
                r'require\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'require\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use a mapping object for allowed modules: "
            "const modules = { a: require('./a'), b: require('./b') }; "
            "Never pass user input directly to require()."
        ),
        false_positive_patterns=[
            r'//\s*require',
            r'require\s*\(\s*["\'][^"\']+["\']\s*\)',
            r'test\(',
            r'jest\.mock',
        ],
    ),

    # DYN-IMPORT-002: import() with variable argument
    DynamicFeatureRule(
        id="DYN-IMPORT-002",
        title="Dynamic import() with variable argument",
        description=(
            "Dynamic import() with user-controlled specifiers can load arbitrary "
            "modules at runtime, enabling code injection or information disclosure "
            "through loading of unintended internal modules."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="dynamic_import",
        patterns={
            "javascript": LanguagePattern(
                r'import\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'import\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use a switch/map pattern for allowed dynamic imports. "
            "Validate import paths against a strict allowlist of module specifiers."
        ),
        false_positive_patterns=[
            r'//\s*import\(',
            r'import\s*\(\s*["\'][^"\']+["\']\s*\)',
            r'test\(',
            r'describe\(',
        ],
    ),

    # DYN-IMPORT-003: require.resolve with user input
    DynamicFeatureRule(
        id="DYN-IMPORT-003",
        title="require.resolve with user-controlled path",
        description=(
            "Using require.resolve with user input can reveal the filesystem layout "
            "and enable path traversal to access files outside the intended directory."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-22"],
        category="dynamic_import",
        patterns={
            "javascript": LanguagePattern(
                r'require\.resolve\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'require\.resolve\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|data\[|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Validate module paths against an allowlist. Do not expose require.resolve "
            "results to users. Use path.resolve with a fixed base directory."
        ),
        false_positive_patterns=[
            r'//\s*require\.resolve',
            r'test\(',
            r'jest\.',
        ],
    ),
]


# =============================================================================
# JS EVAL-ADJACENT (3 rules)
# =============================================================================

JS_EVAL_ADJACENT_RULES: List[DynamicFeatureRule] = [
    # DYN-EVAL-001: document.write with variable
    DynamicFeatureRule(
        id="DYN-EVAL-001",
        title="document.write with dynamic variable content",
        description=(
            "document.write with variable content can inject arbitrary HTML and "
            "scripts into the page. This is a legacy API that inherently enables "
            "XSS when content is not strictly controlled."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="eval_adjacent",
        patterns={
            "javascript": LanguagePattern(
                r'document\.write(?:ln)?\s*\(\s*(?:\w+(?:\s*\+|\s*,)|`[^`]*\$\{)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'document\.write(?:ln)?\s*\(\s*(?:\w+(?:\s*\+|\s*,)|`[^`]*\$\{)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Avoid document.write entirely. Use DOM manipulation methods "
            "(createElement, textContent, appendChild) for safe DOM updates."
        ),
        false_positive_patterns=[
            r'//\s*document\.write',
            r'test\(',
            r'describe\(',
            r'document\.write\s*\(\s*["\'][^"\']*["\']\s*\)',
        ],
    ),

    # DYN-EVAL-002: script.src assignment from variable
    DynamicFeatureRule(
        id="DYN-EVAL-002",
        title="Script src assignment from user-controlled variable",
        description=(
            "Setting script.src to a user-controlled value allows attackers to load "
            "and execute arbitrary JavaScript from an external source, leading to "
            "complete application compromise."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="eval_adjacent",
        patterns={
            "javascript": LanguagePattern(
                r'\.src\s*=\s*(?:req\.|params\.|body\.|query\.|input|user|data|url|`[^`]*\$\{)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'\.src\s*=\s*(?:req\.|params\.|body\.|query\.|input|user|data|url|`[^`]*\$\{)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never assign user-controlled values to script.src. Use a Content Security "
            "Policy (CSP) to restrict allowed script sources. Use subresource integrity."
        ),
        false_positive_patterns=[
            r'//\s*\.src',
            r'test\(',
            r'\.src\s*=\s*["\'][^"\']+["\']\s*;',
            r'img\.src',
            r'image\.src',
        ],
        context_keywords=["script", "createElement", "appendChild"],
        require_context=True,
        context_window_lines=5,
    ),

    # DYN-EVAL-003: WebSocket URL from user input
    DynamicFeatureRule(
        id="DYN-EVAL-003",
        title="WebSocket URL constructed from user input",
        description=(
            "Creating WebSocket connections with user-controlled URLs enables "
            "server-side request forgery (SSRF) via WebSocket protocol. Attackers "
            "can redirect connections to internal services."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-918"],
        category="eval_adjacent",
        patterns={
            "javascript": LanguagePattern(
                r'new\s+WebSocket\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'new\s+WebSocket\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|`[^`]*\$\{|\w+\s*\+)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Validate WebSocket URLs against an allowlist of trusted hosts. "
            "Ensure the URL scheme is wss:// and the host is an expected value."
        ),
        false_positive_patterns=[
            r'//\s*new\s+WebSocket',
            r'test\(',
            r'new\s+WebSocket\s*\(\s*["\'][^"\']+["\']\s*\)',
            r'mock',
        ],
    ),
]


# =============================================================================
# PYTHON REFLECTION (4 rules)
# =============================================================================

PYTHON_REFLECTION_RULES: List[DynamicFeatureRule] = [
    # DYN-REFL-001: getattr with user input
    DynamicFeatureRule(
        id="DYN-REFL-001",
        title="getattr() with user-controlled attribute name",
        description=(
            "Using getattr() with user-controlled attribute names allows attackers "
            "to access arbitrary object attributes, including private methods, "
            "dunder attributes, or sensitive properties not intended to be exposed."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_reflection",
        patterns={
            "python": LanguagePattern(
                r'getattr\s*\(\s*\w+\s*,\s*(?:request\.|input|user|data\[|params|f["\']|.*\.get\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Validate attribute names against an explicit allowlist before calling getattr. "
            "Use a dispatch dict: handlers = {'save': obj.save, 'load': obj.load}"
        ),
        false_positive_patterns=[
            r'getattr\s*\(\s*\w+\s*,\s*\w+\s*,\s*(?:None|False|True|0|["\'])',
            r'#\s*.*getattr',
            r'test_',
            r'def\s+test',
            r'isinstance\(',
            r'hasattr\(',
        ],
    ),

    # DYN-REFL-002: setattr with user input
    DynamicFeatureRule(
        id="DYN-REFL-002",
        title="setattr() with user-controlled attribute name",
        description=(
            "Using setattr() with user-controlled attribute names allows attackers "
            "to overwrite arbitrary attributes, including methods and security-critical "
            "properties, potentially leading to code execution or privilege escalation."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_reflection",
        patterns={
            "python": LanguagePattern(
                r'setattr\s*\(\s*\w+\s*,\s*(?:request\.|input|user|data\[|params|f["\']|.*\.get\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Validate attribute names against a strict allowlist. "
            "Consider using a dictionary for dynamic attribute storage instead of setattr."
        ),
        false_positive_patterns=[
            r'#\s*.*setattr',
            r'test_',
            r'def\s+test',
            r'mock\.',
        ],
    ),

    # DYN-REFL-003: __import__ with variable
    DynamicFeatureRule(
        id="DYN-REFL-003",
        title="__import__() with user-controlled module name",
        description=(
            "Using __import__() with user-controlled module names allows attackers "
            "to import arbitrary Python modules, potentially enabling code execution "
            "or access to sensitive system functionality."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_reflection",
        patterns={
            "python": LanguagePattern(
                r'__import__\s*\(\s*(?:request\.|input|user|data\[|params|f["\']|.*\.get\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use importlib.import_module with a strict allowlist of permitted module names. "
            "Never allow user input to control which modules are imported."
        ),
        false_positive_patterns=[
            r'#\s*.*__import__',
            r'test_',
            r'def\s+test',
            r'__import__\s*\(\s*["\'][^"\']+["\']\s*\)',
        ],
    ),

    # DYN-REFL-004: globals()[variable] / locals()[variable] access
    DynamicFeatureRule(
        id="DYN-REFL-004",
        title="globals() or locals() access with user-controlled key",
        description=(
            "Accessing globals() or locals() with user-controlled keys allows "
            "attackers to read or modify arbitrary variables in the current scope, "
            "including function references and security-sensitive values."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_reflection",
        patterns={
            "python": LanguagePattern(
                r'(?:globals|locals)\s*\(\s*\)\s*\[\s*(?:request\.|input|user|data\[|params|f["\']|.*\.get\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never use globals() or locals() with user-controlled keys. "
            "Use an explicit dispatch dictionary for dynamic function lookup."
        ),
        false_positive_patterns=[
            r'#\s*.*globals',
            r'#\s*.*locals',
            r'test_',
            r'def\s+test',
        ],
    ),
]


# =============================================================================
# PYTHON EXEC (3 rules)
# =============================================================================

PYTHON_EXEC_RULES: List[DynamicFeatureRule] = [
    # DYN-EXEC-001: compile() with user data
    DynamicFeatureRule(
        id="DYN-EXEC-001",
        title="compile() with user-controlled source code",
        description=(
            "Using compile() with user-provided source strings creates executable "
            "code objects that can be run with exec(). This enables arbitrary code "
            "execution when the source is user-controlled."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_exec",
        patterns={
            "python": LanguagePattern(
                r'compile\s*\(\s*(?:request\.|input|user|data\[|params|f["\']|.*\.get\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never compile user-provided source code. Use ast.literal_eval for safe "
            "literal evaluation, or implement a restricted DSL with a safe parser."
        ),
        false_positive_patterns=[
            r're\.compile',
            r'#\s*.*compile',
            r'test_',
            r'def\s+test',
            r'template\.compile',
            r'pattern\.compile',
        ],
    ),

    # DYN-EXEC-002: exec() with formatted string
    DynamicFeatureRule(
        id="DYN-EXEC-002",
        title="exec() with dynamically formatted string",
        description=(
            "Using exec() with f-strings, .format(), or string concatenation "
            "that includes user input enables arbitrary code execution. "
            "The entire Python runtime is available to the attacker."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_exec",
        patterns={
            "python": LanguagePattern(
                r'exec\s*\(\s*(?:f["\']|[^)]*\.format\s*\(|[^)]*%|[^)]*\+\s*(?:request|input|user|data|str\())',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never use exec() with user input. Use ast.literal_eval for data parsing, "
            "or implement a sandboxed execution environment with RestrictedPython."
        ),
        false_positive_patterns=[
            r'#\s*.*exec',
            r'test_',
            r'def\s+test',
            r'exec\s*\(\s*["\'][^"\']+["\']\s*\)',
        ],
    ),

    # DYN-EXEC-003: eval() with non-literal
    DynamicFeatureRule(
        id="DYN-EXEC-003",
        title="eval() with non-literal expression",
        description=(
            "Using eval() with any non-literal string is dangerous. When the "
            "expression contains user input, attackers can execute arbitrary Python "
            "code including os.system, __import__, and other dangerous functions."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="python_exec",
        patterns={
            "python": LanguagePattern(
                r'eval\s*\(\s*(?:f["\']|[^)]*\.format\s*\(|[^)]*%|request\.|input|user|data\[|params|.*\.get\s*\()',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace eval() with ast.literal_eval() for safe literal parsing. "
            "For math expressions, use a safe math evaluator library."
        ),
        false_positive_patterns=[
            r'#\s*.*eval',
            r'test_',
            r'def\s+test',
            r'ast\.literal_eval',
            r'eval\s*\(\s*["\'][^"\']+["\']\s*\)',
        ],
    ),
]


# =============================================================================
# PYTHON META (3 rules)
# =============================================================================

PYTHON_META_RULES: List[DynamicFeatureRule] = [
    # DYN-META-001: type() three-arg form (dynamic class creation)
    DynamicFeatureRule(
        id="DYN-META-001",
        title="Dynamic class creation via type() three-argument form",
        description=(
            "Using type(name, bases, dict) with user-controlled arguments creates "
            "arbitrary classes at runtime. Attackers can define classes with "
            "malicious __init__, __del__, or __getattr__ methods."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94"],
        category="python_meta",
        patterns={
            "python": LanguagePattern(
                r'type\s*\(\s*(?:request\.|input|user|data\[|params|f["\']|.*\.get\s*\()[^,]*,[^,]+,',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Avoid dynamic class creation with user input. Use factory functions "
            "with predefined class hierarchies instead of type() calls."
        ),
        false_positive_patterns=[
            r'#\s*.*type\(',
            r'test_',
            r'def\s+test',
            r'isinstance\(',
            r'type\s*\(\s*\w+\s*\)\s*(?:==|is|!=)',
        ],
    ),

    # DYN-META-002: __subclasses__() enumeration
    DynamicFeatureRule(
        id="DYN-META-002",
        title="__subclasses__() enumeration for code execution",
        description=(
            "Enumerating __subclasses__() allows discovery and instantiation of "
            "all subclasses of a type, which is a common sandbox escape technique. "
            "Attackers use this to find dangerous classes like subprocess.Popen."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94"],
        category="python_meta",
        patterns={
            "python": LanguagePattern(
                r'__subclasses__\s*\(\s*\)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Avoid exposing __subclasses__() to user-controlled code paths. "
            "Use RestrictedPython or a custom sandbox that blocks dunder access."
        ),
        false_positive_patterns=[
            r'#\s*.*__subclasses__',
            r'test_',
            r'def\s+test',
            r'class\s+\w+Test',
            r'pytest',
            r'unittest',
        ],
        context_keywords=["request", "input", "user", "eval", "exec", "template", "render", "jinja"],
        require_context=True,
        context_window_lines=15,
    ),

    # DYN-META-003: __class__.__bases__ manipulation
    DynamicFeatureRule(
        id="DYN-META-003",
        title="__class__.__bases__ access or manipulation",
        description=(
            "Accessing __class__.__bases__ allows traversal of the class hierarchy, "
            "which can be combined with __subclasses__() to escape sandboxes and "
            "access arbitrary Python classes for code execution."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94"],
        category="python_meta",
        patterns={
            "python": LanguagePattern(
                r'__(?:class|bases|mro)__',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Block access to dunder attributes in user-facing code. "
            "Use attribute allowlists and deny patterns matching __*__ in templates."
        ),
        false_positive_patterns=[
            r'#\s*.*__class__',
            r'#\s*.*__bases__',
            r'#\s*.*__mro__',
            r'test_',
            r'def\s+test',
            r'class\s+Meta\b',
            r'isinstance\(',
            r'issubclass\(',
            r'ABCMeta',
            r'abc\.ABC',
            r'typing\.',
        ],
        context_keywords=["request", "input", "user", "eval", "exec", "template", "render", "jinja"],
        require_context=True,
        context_window_lines=15,
    ),
]


# =============================================================================
# JAVA REFLECTION (4 rules)
# =============================================================================

JAVA_REFLECTION_RULES: List[DynamicFeatureRule] = [
    # DYN-REFL-J001: Class.forName with variable
    DynamicFeatureRule(
        id="DYN-REFL-J001",
        title="Class.forName() with user-controlled class name",
        description=(
            "Using Class.forName() with user-controlled strings allows instantiation "
            "of arbitrary classes. Attackers can load dangerous classes like "
            "Runtime, ProcessBuilder, or URLClassLoader for code execution."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-470"],
        category="java_reflection",
        patterns={
            "java": LanguagePattern(
                r'Class\.forName\s*\(\s*(?:request\.getParameter|input|user|data|param|args)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Validate class names against a strict allowlist. "
            "Use a factory pattern with predefined class mappings instead of dynamic class loading."
        ),
        false_positive_patterns=[
            r'//\s*Class\.forName',
            r'Class\.forName\s*\(\s*"[^"]+"\s*\)',
            r'@Test',
            r'test\w+\s*\(',
        ],
    ),

    # DYN-REFL-J002: Method.invoke with user input
    DynamicFeatureRule(
        id="DYN-REFL-J002",
        title="Method.invoke() with user-controlled arguments",
        description=(
            "Using Method.invoke() with user input allows calling arbitrary methods "
            "on objects via reflection. Combined with Class.forName, this enables "
            "full code execution by invoking methods like Runtime.exec()."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-470"],
        category="java_reflection",
        patterns={
            "java": LanguagePattern(
                r'\.invoke\s*\(\s*(?:\w+\s*,\s*)?(?:request|input|user|data|param|args)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use a dispatch pattern with explicit method references. "
            "Validate method names against an allowlist before invoking via reflection."
        ),
        false_positive_patterns=[
            r'//\s*\.invoke',
            r'@Test',
            r'test\w+\s*\(',
            r'MockitoAnnotations',
        ],
        context_keywords=["getMethod", "getDeclaredMethod", "Class.forName", "request", "getParameter"],
        require_context=True,
        context_window_lines=10,
    ),

    # DYN-REFL-J003: Constructor.newInstance with user data
    DynamicFeatureRule(
        id="DYN-REFL-J003",
        title="Constructor.newInstance() with user-controlled arguments",
        description=(
            "Using Constructor.newInstance() with user-controlled arguments allows "
            "instantiation of arbitrary classes with controlled constructor parameters, "
            "enabling code execution or bypass of security restrictions."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-470"],
        category="java_reflection",
        patterns={
            "java": LanguagePattern(
                r'\.newInstance\s*\(\s*(?:request|input|user|data|param|args)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use factory methods with a predefined set of allowed classes. "
            "Validate class types before reflective instantiation."
        ),
        false_positive_patterns=[
            r'//\s*\.newInstance',
            r'@Test',
            r'test\w+\s*\(',
            r'\.newInstance\s*\(\s*\)',
        ],
    ),

    # DYN-REFL-J004: Field.set with user input
    DynamicFeatureRule(
        id="DYN-REFL-J004",
        title="Field.set() with user-controlled value via reflection",
        description=(
            "Using Field.set() with user-controlled values allows modification of "
            "arbitrary object fields, including private and final fields. This can "
            "bypass access controls and modify security-critical state."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-470"],
        category="java_reflection",
        patterns={
            "java": LanguagePattern(
                r'(?:Field|field)\s*.*\.set\s*\(\s*\w+\s*,\s*(?:request|input|user|data|param)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use setter methods with validation instead of reflective field access. "
            "Validate field names against an allowlist before setting values."
        ),
        false_positive_patterns=[
            r'//\s*\.set\(',
            r'@Test',
            r'test\w+\s*\(',
            r'setAccessible',
        ],
        context_keywords=["getDeclaredField", "getField", "setAccessible", "request", "getParameter"],
        require_context=True,
        context_window_lines=10,
    ),
]


# =============================================================================
# JAVA DESERIALIZATION (2 rules)
# =============================================================================

JAVA_DESERIALIZATION_RULES: List[DynamicFeatureRule] = [
    # DYN-DESER-J001: URLClassLoader with user URL
    DynamicFeatureRule(
        id="DYN-DESER-J001",
        title="URLClassLoader with user-controlled URL",
        description=(
            "Creating a URLClassLoader with user-controlled URLs allows loading "
            "and executing arbitrary Java bytecode from remote sources. "
            "This enables complete remote code execution."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-94"],
        category="java_deserialization",
        patterns={
            "java": LanguagePattern(
                r'(?:new\s+URLClassLoader|URLClassLoader\.newInstance)\s*\(\s*(?:new\s+URL\s*\[\s*\]\s*\{[^}]*(?:request|input|user|param)|.*(?:request|input|user|param))',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Never create URLClassLoaders with user-controlled URLs. "
            "Use a strict allowlist of trusted code sources and validate URL schemes."
        ),
        false_positive_patterns=[
            r'//\s*URLClassLoader',
            r'@Test',
            r'test\w+\s*\(',
        ],
    ),

    # DYN-DESER-J002: ObjectInputStream.readObject without validation
    DynamicFeatureRule(
        id="DYN-DESER-J002",
        title="ObjectInputStream.readObject() without type validation",
        description=(
            "Deserializing Java objects via ObjectInputStream without type filtering "
            "allows attackers to exploit gadget chains for remote code execution. "
            "This is one of the most dangerous Java vulnerability patterns."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-502"],
        category="java_deserialization",
        patterns={
            "java": LanguagePattern(
                r'(?:ObjectInputStream|OIS|ois)\s*.*\.readObject\s*\(\s*\)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use ObjectInputFilter (Java 9+) to restrict allowed types. "
            "Prefer JSON or Protocol Buffers over native Java serialization."
        ),
        false_positive_patterns=[
            r'//\s*readObject',
            r'@Test',
            r'test\w+\s*\(',
            r'ObjectInputFilter',
            r'setObjectInputFilter',
            r'serialFilter',
        ],
        context_keywords=["socket", "network", "request", "input", "stream", "upload", "file"],
        require_context=True,
        context_window_lines=15,
    ),
]


# =============================================================================
# JAVA PROXY (2 rules)
# =============================================================================

JAVA_PROXY_RULES: List[DynamicFeatureRule] = [
    # DYN-PROXY-J001: Proxy.newProxyInstance with dynamic handler
    DynamicFeatureRule(
        id="DYN-PROXY-J001",
        title="Proxy.newProxyInstance with user-influenced handler",
        description=(
            "Creating dynamic proxies with user-influenced InvocationHandlers "
            "allows interception and redirection of method calls. When handler "
            "logic is user-controlled, this enables arbitrary method invocation."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-470"],
        category="java_proxy",
        patterns={
            "java": LanguagePattern(
                r'Proxy\.newProxyInstance\s*\(\s*[^)]*(?:request|input|user|param|data)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use typed proxy implementations instead of dynamic proxies with user input. "
            "Validate all proxy interface types against an allowlist."
        ),
        false_positive_patterns=[
            r'//\s*Proxy\.newProxy',
            r'@Test',
            r'test\w+\s*\(',
            r'Mockito',
        ],
    ),

    # DYN-PROXY-J002: MethodHandle.invokeWithArguments
    DynamicFeatureRule(
        id="DYN-PROXY-J002",
        title="MethodHandle.invokeWithArguments with user-controlled arguments",
        description=(
            "Using MethodHandle.invokeWithArguments with user-controlled data "
            "allows invocation of arbitrary methods with attacker-specified arguments. "
            "MethodHandles bypass standard access checks when setAccessible is used."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-470"],
        category="java_proxy",
        patterns={
            "java": LanguagePattern(
                r'(?:MethodHandle|methodHandle|mh)\s*.*\.invoke(?:WithArguments|Exact)?\s*\(\s*(?:request|input|user|data|param|args)',
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use typed method references instead of dynamic MethodHandles. "
            "Validate method targets and arguments before invocation."
        ),
        false_positive_patterns=[
            r'//\s*invoke',
            r'@Test',
            r'test\w+\s*\(',
        ],
        context_keywords=["lookup", "findVirtual", "findStatic", "request", "getParameter"],
        require_context=True,
        context_window_lines=10,
    ),
]


# =============================================================================
# ALL RULES COMBINED
# =============================================================================

ALL_DYNAMIC_FEATURE_RULES: List[DynamicFeatureRule] = (
    JS_DYNAMIC_PROPERTY_RULES +
    JS_DYNAMIC_CALL_RULES +
    JS_DYNAMIC_IMPORT_RULES +
    JS_EVAL_ADJACENT_RULES +
    PYTHON_REFLECTION_RULES +
    PYTHON_EXEC_RULES +
    PYTHON_META_RULES +
    JAVA_REFLECTION_RULES +
    JAVA_DESERIALIZATION_RULES +
    JAVA_PROXY_RULES
)


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class DynamicFeatureDetector(BaseScanner):
    """
    Detects unsafe dynamic language feature usage across multiple languages.

    Covers dynamic code patterns that become security vulnerabilities when
    user input influences their behavior:

    JavaScript:
    - Dynamic property access (CWE-79, CWE-94, CWE-1321)
    - Computed function/method calls (CWE-94)
    - Dynamic imports (CWE-94, CWE-22)
    - Eval-adjacent patterns (CWE-79, CWE-94, CWE-918)

    Python:
    - Reflection (getattr/setattr/__import__/globals) (CWE-94)
    - Exec/eval/compile with user data (CWE-94)
    - Metaclass and class hierarchy abuse (CWE-94)

    Java:
    - Reflection (Class.forName, Method.invoke, etc.) (CWE-470)
    - Unsafe deserialization and class loading (CWE-94, CWE-502)
    - Dynamic proxies and method handles (CWE-470)

    Multi-language: JavaScript, TypeScript, Python, Java
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in ALL_DYNAMIC_FEATURE_RULES:
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
        return ScannerType.DYNAMIC_FEATURE

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

    def _get_confidence(self, rule: DynamicFeatureRule, language: str) -> float:
        """Determine confidence score based on rule category and language."""
        category = rule.category

        # Python exec/eval patterns are most certain
        if category == "python_exec":
            return 0.7

        # Python reflection with user input is fairly certain
        if category == "python_reflection":
            return 0.65

        # Python meta patterns need more context
        if category == "python_meta":
            return 0.5

        # Java reflection patterns
        if category in ("java_reflection", "java_proxy"):
            return 0.6

        # Java deserialization is well-understood
        if category == "java_deserialization":
            return 0.65

        # JS dynamic calls and eval-adjacent are high confidence
        if category in ("dynamic_call", "eval_adjacent"):
            return 0.6

        # JS dynamic imports
        if category == "dynamic_import":
            return 0.55

        # JS dynamic property access has more false positives
        if category == "dynamic_property_access":
            return 0.5

        return 0.5

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
        """Execute dynamic feature vulnerability scan."""
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

                for rule in ALL_DYNAMIC_FEATURE_RULES:
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

                        confidence = self._get_confidence(rule, language)

                        finding = SecurityFinding(
                            id=f"dynamic-feature-{rule.id}-{file_path}:{line_start}",
                            rule_id=rule.id,
                            title=rule.title,
                            description=rule.description,
                            severity=rule.severity,
                            confidence=confidence,
                            scanner=self.scanner_type,
                            location=Location(
                                file_path=str(file_path),
                                start_line=line_start,
                                end_line=line_end,
                                snippet=snippet,
                            ),
                            cwe_ids=rule.cwe_ids,
                            category=rule.category,
                            tags={f"lang:{language}", "dynamic_feature", rule.category},
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
        """Get summary of all dynamic feature detection rules."""
        categories = {}
        for rule in ALL_DYNAMIC_FEATURE_RULES:
            if rule.category not in categories:
                categories[rule.category] = 0
            categories[rule.category] += 1

        cwe_coverage = set()
        for rule in ALL_DYNAMIC_FEATURE_RULES:
            cwe_coverage.update(rule.cwe_ids)

        return {
            "total_rules": len(ALL_DYNAMIC_FEATURE_RULES),
            "rules_by_category": categories,
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in ALL_DYNAMIC_FEATURE_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": sorted(cwe_coverage),
            "category_descriptions": {
                "dynamic_property_access": "JS Dynamic Property Access (CWE-79, CWE-94, CWE-1321)",
                "dynamic_call": "JS Dynamic Function/Method Calls (CWE-94)",
                "dynamic_import": "JS Dynamic Imports (CWE-94, CWE-22)",
                "eval_adjacent": "JS Eval-Adjacent Patterns (CWE-79, CWE-94, CWE-918)",
                "python_reflection": "Python Reflection (CWE-94)",
                "python_exec": "Python Exec/Eval/Compile (CWE-94)",
                "python_meta": "Python Metaclass/Class Hierarchy Abuse (CWE-94)",
                "java_reflection": "Java Reflection (CWE-470)",
                "java_deserialization": "Java Deserialization/ClassLoading (CWE-94, CWE-502)",
                "java_proxy": "Java Dynamic Proxies/MethodHandles (CWE-470)",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_dynamic_feature_detector() -> DynamicFeatureDetector:
    """Factory function to create dynamic feature detector."""
    return DynamicFeatureDetector()
