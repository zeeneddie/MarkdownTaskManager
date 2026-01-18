"""
Injection Vulnerability Detector - Complete CWE Top 25 Injection Coverage.

Fase 41: Detects injection vulnerabilities across multiple languages:

TIER 1 (CRITICAL):
- CWE-79: Cross-site Scripting (XSS)
- CWE-89: SQL Injection
- CWE-78: OS Command Injection
- CWE-22: Path Traversal
- CWE-502: Deserialization of Untrusted Data
- CWE-918: Server-Side Request Forgery (SSRF)

TIER 2 (HIGH):
- CWE-94: Code Injection (eval/exec)
- CWE-611: XML External Entity (XXE)
- CWE-90: LDAP Injection
- CWE-943: NoSQL Injection
- CWE-1336: Server-Side Template Injection (SSTI)
- CWE-352: Cross-Site Request Forgery (CSRF)
- CWE-434: Unrestricted File Upload
- CWE-77: Command Injection (generic)

Multi-language support: Python, JavaScript, TypeScript, Java, C#, PHP, Ruby, Go, C, C++
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
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs", ".cshtml"},
    ),
    "php": LanguageDefinition(
        name="PHP",
        extensions={".php", ".phtml"},
    ),
    "ruby": LanguageDefinition(
        name="Ruby",
        extensions={".rb", ".erb"},
    ),
    "go": LanguageDefinition(
        name="Go",
        extensions={".go"},
    ),
    "c": LanguageDefinition(
        name="C",
        extensions={".c", ".h"},
    ),
    "cpp": LanguageDefinition(
        name="C++",
        extensions={".cpp", ".hpp", ".cc", ".cxx"},
    ),
}


# =============================================================================
# INJECTION RULES DATA STRUCTURE
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class InjectionRule:
    """An injection vulnerability rule with language-specific patterns."""
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
# TIER 1: CRITICAL INJECTION RULES
# =============================================================================

# -----------------------------------------------------------------------------
# CWE-79: Cross-site Scripting (XSS) - 8 rules
# -----------------------------------------------------------------------------

XSS_RULES: List[InjectionRule] = [
    # INJ-XSS-001: innerHTML with user input (JS/TS)
    InjectionRule(
        id="INJ-XSS-001",
        title="innerHTML assignment with user input",
        description=(
            "Direct assignment to innerHTML with user-controlled data enables XSS. "
            "Attackers can inject malicious scripts that execute in the victim's browser."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "javascript": LanguagePattern(
                r'\.innerHTML\s*=\s*(?:req\.|params\.|query\.|body\.|input|user|data)',
            ),
            "typescript": LanguagePattern(
                r'\.innerHTML\s*=\s*(?:req\.|params\.|query\.|body\.|input|user|data)',
            ),
        },
        fix_suggestion="Use textContent for text, or sanitize HTML with DOMPurify before setting innerHTML.",
        false_positive_patterns=[r'DOMPurify', r'sanitize', r'escape'],
    ),

    # INJ-XSS-002: innerHTML with template literal
    InjectionRule(
        id="INJ-XSS-002",
        title="innerHTML with template literal containing user data",
        description=(
            "Template literals in innerHTML allow script injection when containing user input."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "javascript": LanguagePattern(
                r'\.innerHTML\s*=\s*`[^`]*\$\{(?:req\.|params\.|body\.|query\.|input|user|data)',
            ),
            "typescript": LanguagePattern(
                r'\.innerHTML\s*=\s*`[^`]*\$\{(?:req\.|params\.|body\.|query\.|input|user|data)',
            ),
        },
        fix_suggestion="Use textContent or sanitize the interpolated values with DOMPurify.",
    ),

    # INJ-XSS-003: document.write with user input
    InjectionRule(
        id="INJ-XSS-003",
        title="document.write with user input",
        description=(
            "document.write with user data can execute arbitrary scripts. "
            "This is a legacy API that should be avoided entirely."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "javascript": LanguagePattern(
                r'document\.write(?:ln)?\s*\(\s*(?:req\.|params\.|input|user|`[^`]*\$\{)',
            ),
        },
        fix_suggestion="Avoid document.write entirely. Use DOM manipulation methods instead.",
    ),

    # INJ-XSS-004: jQuery .html() with user input
    InjectionRule(
        id="INJ-XSS-004",
        title="jQuery .html() with user input",
        description=(
            "jQuery html() method with user input enables XSS. "
            "The html() method parses and executes scripts in the provided HTML."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "javascript": LanguagePattern(
                r'\$\([^)]+\)\.html\s*\(\s*(?:req\.|data\.|input|user|response)',
            ),
        },
        fix_suggestion="Use .text() for text content or sanitize HTML before using .html().",
    ),

    # INJ-XSS-005: React dangerouslySetInnerHTML
    InjectionRule(
        id="INJ-XSS-005",
        title="React dangerouslySetInnerHTML with user data",
        description=(
            "Using dangerouslySetInnerHTML with user input bypasses React's built-in XSS protection. "
            "This API exists for specific use cases and should be used with sanitized content only."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "javascript": LanguagePattern(
                r'dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*(?:props\.|state\.|data\.|user|input)',
            ),
            "typescript": LanguagePattern(
                r'dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*(?:props\.|state\.|data\.|user|input)',
            ),
        },
        fix_suggestion="Sanitize content with DOMPurify before passing to dangerouslySetInnerHTML.",
        false_positive_patterns=[r'DOMPurify', r'sanitize'],
    ),

    # INJ-XSS-006: Python Flask/Jinja without escaping
    InjectionRule(
        id="INJ-XSS-006",
        title="Jinja2 template rendering without auto-escaping",
        description=(
            "Rendering user input in Jinja2 templates without escaping enables XSS. "
            "The |safe filter and Markup() bypass auto-escaping."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "python": LanguagePattern(
                r'render_template_string\s*\(\s*(?:request|input|user|f["\'])',
            ),
        },
        fix_suggestion="Use render_template with auto-escaping. Never pass user input to render_template_string.",
    ),

    # INJ-XSS-007: Python Markup/safe filter
    InjectionRule(
        id="INJ-XSS-007",
        title="Marking user input as safe HTML",
        description=(
            "Using Markup() or |safe filter on user input bypasses HTML escaping, enabling XSS."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "python": LanguagePattern(
                r'Markup\s*\(\s*(?:request|input|user|data)',
            ),
        },
        fix_suggestion="Never mark user input as safe. Sanitize with bleach before marking as Markup.",
        false_positive_patterns=[r'bleach', r'sanitize', r'escape'],
    ),

    # INJ-XSS-008: PHP echo/print with user input
    InjectionRule(
        id="INJ-XSS-008",
        title="PHP output with unescaped user input",
        description=(
            "Echoing user input without htmlspecialchars enables XSS. "
            "Always escape output in HTML context."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "php": LanguagePattern(
                r'(?:echo|print)\s+\$_(?:GET|POST|REQUEST|COOKIE)\s*\[',
            ),
        },
        fix_suggestion="Use htmlspecialchars($_GET['param'], ENT_QUOTES, 'UTF-8') for output.",
        false_positive_patterns=[r'htmlspecialchars', r'htmlentities', r'strip_tags'],
    ),

    # INJ-XSS-009: PHP short echo tag
    InjectionRule(
        id="INJ-XSS-009",
        title="PHP short echo tag with user input",
        description=(
            "Short echo tags (<?=) with user input enable XSS without escaping."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "php": LanguagePattern(
                r'<\?=\s*\$_(?:GET|POST|REQUEST|COOKIE)',
            ),
        },
        fix_suggestion="Use <?= htmlspecialchars($var, ENT_QUOTES, 'UTF-8') ?>.",
    ),

    # INJ-XSS-010: Java Servlet response writer
    InjectionRule(
        id="INJ-XSS-010",
        title="Java servlet response with unescaped user input",
        description=(
            "Writing user input directly to servlet response enables XSS."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "java": LanguagePattern(
                r'(?:getWriter|getOutputStream)\s*\(\s*\)\.(?:print|println|write)\s*\(\s*(?:request\.getParameter|input|user)',
            ),
        },
        fix_suggestion="Use OWASP Java Encoder: Encode.forHtml(userInput) before output.",
        false_positive_patterns=[r'Encode\.', r'escapeHtml', r'StringEscapeUtils'],
    ),

    # INJ-XSS-011: C# Response.Write
    InjectionRule(
        id="INJ-XSS-011",
        title="ASP.NET Response.Write with user input",
        description=(
            "Response.Write with unencoded user input enables XSS."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "csharp": LanguagePattern(
                r'Response\.Write\s*\(\s*Request(?:\[|\.(?:QueryString|Form|Params))',
            ),
        },
        fix_suggestion="Use HttpUtility.HtmlEncode() or Server.HtmlEncode() before output.",
        false_positive_patterns=[r'HtmlEncode', r'AntiXss'],
    ),

    # INJ-XSS-012: C# Html.Raw
    InjectionRule(
        id="INJ-XSS-012",
        title="ASP.NET MVC Html.Raw with user input",
        description=(
            "@Html.Raw() bypasses Razor's automatic HTML encoding, enabling XSS."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        patterns={
            "csharp": LanguagePattern(
                r'@?Html\.Raw\s*\(\s*(?:Model\.|ViewBag\.|ViewData\[|input|user)',
            ),
        },
        fix_suggestion="Remove Html.Raw() to use default encoding, or sanitize with AntiXss library.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-89: SQL Injection - 10 rules
# -----------------------------------------------------------------------------

SQL_INJECTION_RULES: List[InjectionRule] = [
    # INJ-SQL-001: Python string concatenation
    InjectionRule(
        id="INJ-SQL-001",
        title="SQL query with string concatenation",
        description=(
            "Building SQL queries with string concatenation allows injection. "
            "Attackers can modify query logic or extract unauthorized data."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:cursor|db|conn|connection|engine)\.execute\s*\(\s*["\'][^"\']*["\']\s*\+',
            ),
        },
        fix_suggestion="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
        false_positive_patterns=[r'%s', r'\?', r':\w+'],
    ),

    # INJ-SQL-002: Python f-string in SQL
    InjectionRule(
        id="INJ-SQL-002",
        title="SQL query with f-string interpolation",
        description=(
            "Using f-strings for SQL query construction allows injection attacks."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:execute|raw)\s*\(\s*f["\'](?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Never use f-strings for SQL. Use parameterized queries with placeholders.",
    ),

    # INJ-SQL-003: Python .format() in SQL
    InjectionRule(
        id="INJ-SQL-003",
        title="SQL query with .format() string building",
        description=(
            "Using .format() for SQL query construction allows injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "python": LanguagePattern(
                r'["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\']\.format\s*\(',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Replace .format() with parameterized queries using ? or %s placeholders.",
    ),

    # INJ-SQL-004: Python % string formatting in SQL
    InjectionRule(
        id="INJ-SQL-004",
        title="SQL query with % string operator",
        description=(
            "Using % operator for SQL query formatting allows injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "python": LanguagePattern(
                r'execute\s*\(\s*["\'][^"\']*%[sd][^"\']*["\'].*%\s*(?:\(|[^,)]+)',
            ),
        },
        fix_suggestion="Use parameterized queries. The database driver handles escaping.",
    ),

    # INJ-SQL-005: JavaScript template literal in SQL
    InjectionRule(
        id="INJ-SQL-005",
        title="SQL query with template literal",
        description=(
            "Template literals in SQL queries allow injection via interpolated values."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "javascript": LanguagePattern(
                r'(?:query|execute)\s*\(\s*`(?:SELECT|INSERT|UPDATE|DELETE)[^`]*\$\{',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'(?:query|execute)\s*\(\s*`(?:SELECT|INSERT|UPDATE|DELETE)[^`]*\$\{',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Use parameterized queries: db.query('SELECT * FROM users WHERE id = $1', [userId])",
    ),

    # INJ-SQL-006: JavaScript string concatenation in SQL
    InjectionRule(
        id="INJ-SQL-006",
        title="SQL query with string concatenation",
        description=(
            "String concatenation in SQL queries enables injection attacks."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "javascript": LanguagePattern(
                r'(?:query|execute)\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\'].*\+',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r'(?:query|execute)\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\'].*\+',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Use parameterized queries with placeholders ($1, $2 or ?).",
    ),

    # INJ-SQL-007: Java Statement (not PreparedStatement)
    InjectionRule(
        id="INJ-SQL-007",
        title="Java Statement with string concatenation",
        description=(
            "Using Statement instead of PreparedStatement with user input enables SQL injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "java": LanguagePattern(
                r'(?:Statement|createStatement).*(?:executeQuery|executeUpdate|execute)\s*\(\s*["\'][^"\']*["\']\s*\+',
            ),
        },
        fix_suggestion="Use PreparedStatement with setString/setInt for parameter binding.",
    ),

    # INJ-SQL-008: Java createQuery with concatenation
    InjectionRule(
        id="INJ-SQL-008",
        title="JPA/Hibernate createQuery with concatenation",
        description=(
            "Creating queries with string concatenation in JPA/Hibernate enables injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "java": LanguagePattern(
                r'createQuery\s*\(\s*["\'][^"\']*\+.*(?:request|input|getParameter)',
            ),
        },
        fix_suggestion="Use named parameters: createQuery('SELECT u FROM User u WHERE u.id = :id').setParameter('id', userId)",
    ),

    # INJ-SQL-009: PHP mysql/mysqli with concatenation
    InjectionRule(
        id="INJ-SQL-009",
        title="PHP SQL query with user input",
        description=(
            "Building SQL queries with user input in PHP enables injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "php": LanguagePattern(
                r'(?:mysql_query|mysqli_query|query)\s*\(\s*[^,]*["\'][^"\']*\.\s*\$_(?:GET|POST|REQUEST)',
            ),
        },
        fix_suggestion="Use prepared statements: $stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?'); $stmt->execute([$id]);",
    ),

    # INJ-SQL-010: C# SqlCommand with concatenation
    InjectionRule(
        id="INJ-SQL-010",
        title="C# SqlCommand with string concatenation",
        description=(
            "Building SqlCommand with string concatenation enables SQL injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "csharp": LanguagePattern(
                r'(?:new\s+SqlCommand|CommandText\s*=)\s*\(\s*["\'][^"\']*\+.*(?:Request|input|user)',
            ),
        },
        fix_suggestion="Use SqlParameter: cmd.Parameters.AddWithValue('@id', userId);",
    ),

    # INJ-SQL-011: Ruby ActiveRecord interpolation
    InjectionRule(
        id="INJ-SQL-011",
        title="Ruby ActiveRecord with string interpolation",
        description=(
            "String interpolation in ActiveRecord queries enables SQL injection."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "ruby": LanguagePattern(
                r'(?:where|find_by_sql|execute)\s*\(\s*["\'][^"\']*\#\{(?:params|request|input)',
            ),
        },
        fix_suggestion="Use parameterized queries: where('id = ?', params[:id]) or where(id: params[:id])",
    ),

    # INJ-SQL-012: Go SQL with fmt.Sprintf
    InjectionRule(
        id="INJ-SQL-012",
        title="Go SQL query with fmt.Sprintf",
        description=(
            "Using fmt.Sprintf to build SQL queries enables injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        patterns={
            "go": LanguagePattern(
                r'(?:Query|Exec)\s*\(\s*fmt\.Sprintf\s*\(\s*["`](?:SELECT|INSERT|UPDATE|DELETE)',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Use parameterized queries: db.Query('SELECT * FROM users WHERE id = $1', userId)",
    ),
]


# -----------------------------------------------------------------------------
# CWE-78: OS Command Injection - 8 rules
# -----------------------------------------------------------------------------

COMMAND_INJECTION_RULES: List[InjectionRule] = [
    # INJ-CMD-001: Python os.system
    InjectionRule(
        id="INJ-CMD-001",
        title="os.system with user input",
        description=(
            "Passing user input to os.system enables command injection. "
            "Attackers can execute arbitrary shell commands."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78", "CWE-77"],
        category="command_injection",
        patterns={
            "python": LanguagePattern(
                r'os\.system\s*\(\s*(?:f["\']|.*\+|.*%.*%|.*\.format)',
            ),
        },
        fix_suggestion="Use subprocess with shell=False and argument list: subprocess.run(['ls', '-l', path])",
    ),

    # INJ-CMD-002: Python os.popen
    InjectionRule(
        id="INJ-CMD-002",
        title="os.popen with user input",
        description=(
            "os.popen executes commands through the shell, enabling injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "python": LanguagePattern(
                r'os\.popen\s*\(\s*(?:f["\']|.*\+|.*%)',
            ),
        },
        fix_suggestion="Use subprocess.run() with shell=False instead of os.popen().",
    ),

    # INJ-CMD-003: Python subprocess with shell=True
    InjectionRule(
        id="INJ-CMD-003",
        title="subprocess with shell=True and user input",
        description=(
            "Using shell=True with user input enables command injection via shell metacharacters."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "python": LanguagePattern(
                r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            ),
        },
        fix_suggestion="Remove shell=True and pass command as list: subprocess.run(['cmd', arg1, arg2])",
        context_keywords=["request", "input", "user", "params", "f\"", "f'", "+"],
        require_context=True,
    ),

    # INJ-CMD-004: Node.js child_process.exec
    InjectionRule(
        id="INJ-CMD-004",
        title="child_process.exec with user input",
        description=(
            "exec() runs commands through shell, enabling injection via shell metacharacters."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "javascript": LanguagePattern(
                r'(?:exec|execSync)\s*\(\s*(?:`[^`]*\$\{|["\'].*\+)',
            ),
            "typescript": LanguagePattern(
                r'(?:exec|execSync)\s*\(\s*(?:`[^`]*\$\{|["\'].*\+)',
            ),
        },
        fix_suggestion="Use execFile or spawn with argument array: spawn('ls', ['-l', dir])",
    ),

    # INJ-CMD-005: PHP shell functions
    InjectionRule(
        id="INJ-CMD-005",
        title="PHP shell execution with user input",
        description=(
            "PHP shell functions with user input enable command injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "php": LanguagePattern(
                r'(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*\$_(?:GET|POST|REQUEST)',
            ),
        },
        fix_suggestion="Use escapeshellarg() and escapeshellcmd() to sanitize input, or avoid shell entirely.",
        false_positive_patterns=[r'escapeshellarg', r'escapeshellcmd'],
    ),

    # INJ-CMD-006: PHP backtick execution
    InjectionRule(
        id="INJ-CMD-006",
        title="PHP backtick command execution",
        description=(
            "PHP backtick operator executes shell commands. User input in backticks enables injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "php": LanguagePattern(
                r'`[^`]*\$_(?:GET|POST|REQUEST)[^`]*`',
            ),
        },
        fix_suggestion="Avoid backtick execution. Use escapeshellarg() with exec() if shell is necessary.",
    ),

    # INJ-CMD-007: Java Runtime.exec
    InjectionRule(
        id="INJ-CMD-007",
        title="Java Runtime.exec with string concatenation",
        description=(
            "Runtime.exec with string concatenation enables command injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "java": LanguagePattern(
                r'Runtime\.getRuntime\s*\(\s*\)\.exec\s*\(\s*["\'][^"\']*\+',
            ),
        },
        fix_suggestion="Use ProcessBuilder with explicit argument list, not string concatenation.",
    ),

    # INJ-CMD-008: Ruby system/exec
    InjectionRule(
        id="INJ-CMD-008",
        title="Ruby system/exec with string interpolation",
        description=(
            "Ruby shell execution with string interpolation enables command injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-78"],
        category="command_injection",
        patterns={
            "ruby": LanguagePattern(
                r'(?:system|exec|`|%x)\s*["\'\(]?[^"\']*\#\{(?:params|request|input)',
            ),
        },
        fix_suggestion="Use array form: system('ls', '-l', user_path) to avoid shell interpretation.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-22: Path Traversal - 6 rules
# -----------------------------------------------------------------------------

PATH_TRAVERSAL_RULES: List[InjectionRule] = [
    # INJ-PATH-001: Python file operations
    InjectionRule(
        id="INJ-PATH-001",
        title="File operation with user-controlled path",
        description=(
            "Opening files based on user input without validation allows path traversal. "
            "Attackers can access files outside the intended directory using ../ sequences."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        patterns={
            "python": LanguagePattern(
                r'open\s*\(\s*(?:f["\'][^"\']*\{|[^)]*(?:request|input|user|params))',
            ),
        },
        fix_suggestion="Use os.path.basename() to extract filename, and validate against allowlist. Use pathlib for safe path operations.",
        false_positive_patterns=[r'os\.path\.basename', r'secure_filename', r'\.resolve\(\)'],
    ),

    # INJ-PATH-002: Python send_file/send_from_directory
    InjectionRule(
        id="INJ-PATH-002",
        title="Flask file serving with user input",
        description=(
            "Serving files based on user input can expose sensitive files via path traversal."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        patterns={
            "python": LanguagePattern(
                r'send_(?:file|from_directory)\s*\([^)]*(?:request|input|user)',
            ),
        },
        fix_suggestion="Use send_from_directory with a fixed base directory. Validate filename with secure_filename().",
    ),

    # INJ-PATH-003: Node.js fs operations
    InjectionRule(
        id="INJ-PATH-003",
        title="Node.js file operation with user input",
        description=(
            "File system operations with user-controlled paths enable directory traversal attacks."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        patterns={
            "javascript": LanguagePattern(
                r'fs\.(?:readFile|writeFile|readFileSync|writeFileSync|createReadStream|unlink|rmdir)\s*\([^)]*(?:req\.|params|query)',
            ),
            "typescript": LanguagePattern(
                r'fs\.(?:readFile|writeFile|readFileSync|writeFileSync|createReadStream|unlink|rmdir)\s*\([^)]*(?:req\.|params|query)',
            ),
        },
        fix_suggestion="Validate and sanitize paths. Use path.resolve() and verify the result is within allowed directory.",
    ),

    # INJ-PATH-004: Java File operations
    InjectionRule(
        id="INJ-PATH-004",
        title="Java file operation with user input",
        description=(
            "Creating File objects from user-controlled strings enables path traversal."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        patterns={
            "java": LanguagePattern(
                r'new\s+File\s*\([^)]*(?:request\.getParameter|input|getParameter)',
            ),
        },
        fix_suggestion="Canonicalize path and verify it's within allowed base directory using getCanonicalPath().",
    ),

    # INJ-PATH-005: PHP file operations
    InjectionRule(
        id="INJ-PATH-005",
        title="PHP file operation with user input",
        description=(
            "PHP file functions with user-controlled paths enable directory traversal and LFI/RFI."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-22", "CWE-98"],
        category="path_traversal",
        patterns={
            "php": LanguagePattern(
                r'(?:file_get_contents|file_put_contents|fopen|readfile|include|require)(?:_once)?\s*\([^)]*\$_(?:GET|POST|REQUEST)',
            ),
        },
        fix_suggestion="Use basename() and validate against allowlist. Never include files based on user input.",
        false_positive_patterns=[r'basename', r'realpath'],
    ),

    # INJ-PATH-006: C# file operations
    InjectionRule(
        id="INJ-PATH-006",
        title="C# file operation with user input",
        description=(
            "File operations with user-controlled paths in C# enable directory traversal."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        patterns={
            "csharp": LanguagePattern(
                r'(?:File\.|StreamReader|StreamWriter|FileStream)\s*[.(]\s*[^)]*(?:Request|input|user)',
            ),
        },
        fix_suggestion="Use Path.GetFullPath() and verify result is within allowed base directory.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-502: Deserialization of Untrusted Data - 7 rules
# -----------------------------------------------------------------------------

DESERIALIZATION_RULES: List[InjectionRule] = [
    # INJ-DESER-001: Python pickle
    InjectionRule(
        id="INJ-DESER-001",
        title="Pickle deserialization of untrusted data",
        description=(
            "Deserializing pickle data from untrusted sources enables arbitrary code execution. "
            "Pickle can execute __reduce__ methods during deserialization."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "python": LanguagePattern(
                r'pickle\.loads?\s*\(',
            ),
        },
        fix_suggestion="Use JSON or other safe serialization formats. Never unpickle untrusted data.",
        context_keywords=["request", "input", "user", "data", "body", "upload", "file"],
        require_context=True,
    ),

    # INJ-DESER-002: Python yaml.load
    InjectionRule(
        id="INJ-DESER-002",
        title="YAML unsafe load",
        description=(
            "yaml.load or yaml.unsafe_load can execute arbitrary Python code via YAML tags. "
            "This enables RCE when loading untrusted YAML."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "python": LanguagePattern(
                r'yaml\.(?:load|unsafe_load)\s*\([^)]*(?:request|input|data|file)',
            ),
        },
        fix_suggestion="Use yaml.safe_load() instead of yaml.load().",
    ),

    # INJ-DESER-003: Python yaml.load without SafeLoader
    InjectionRule(
        id="INJ-DESER-003",
        title="YAML load without SafeLoader",
        description=(
            "yaml.load without explicit SafeLoader can execute arbitrary code."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "python": LanguagePattern(
                r'yaml\.load\s*\([^)]+\)(?!\s*,\s*Loader\s*=)',
            ),
        },
        fix_suggestion="Always specify Loader: yaml.load(data, Loader=yaml.SafeLoader) or use yaml.safe_load().",
        false_positive_patterns=[r'SafeLoader', r'safe_load'],
    ),

    # INJ-DESER-004: Java ObjectInputStream
    InjectionRule(
        id="INJ-DESER-004",
        title="Java ObjectInputStream deserialization",
        description=(
            "Deserializing Java objects from untrusted sources can lead to RCE via gadget chains."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "java": LanguagePattern(
                r'ObjectInputStream.*\.readObject\s*\(',
            ),
        },
        fix_suggestion="Use allowlisting ObjectInputFilter or avoid native Java serialization entirely.",
        context_keywords=["request", "input", "socket", "network", "upload", "file"],
        require_context=True,
    ),

    # INJ-DESER-005: PHP unserialize
    InjectionRule(
        id="INJ-DESER-005",
        title="PHP unserialize with user input",
        description=(
            "unserialize() with user data can lead to object injection and RCE via __wakeup/__destruct."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "php": LanguagePattern(
                r'unserialize\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)',
            ),
        },
        fix_suggestion="Use JSON encoding or explicitly validate before unserialize with allowed_classes.",
    ),

    # INJ-DESER-006: C# BinaryFormatter
    InjectionRule(
        id="INJ-DESER-006",
        title="C# BinaryFormatter deserialization",
        description=(
            "BinaryFormatter is inherently unsafe for untrusted data and can lead to RCE."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "csharp": LanguagePattern(
                r'BinaryFormatter\s*\(\s*\)\.Deserialize\s*\(',
            ),
        },
        fix_suggestion="Use DataContractSerializer or System.Text.Json with proper settings. BinaryFormatter is obsolete.",
    ),

    # INJ-DESER-007: C# TypeNameHandling
    InjectionRule(
        id="INJ-DESER-007",
        title="JSON.NET with TypeNameHandling enabled",
        description=(
            "TypeNameHandling.All/Auto/Objects in JSON.NET can deserialize arbitrary types, enabling RCE."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-502"],
        category="deserialization",
        patterns={
            "csharp": LanguagePattern(
                r'TypeNameHandling\s*=\s*TypeNameHandling\.(?:All|Auto|Objects|Arrays)',
            ),
        },
        fix_suggestion="Avoid TypeNameHandling. If needed, use TypeNameHandling.None with a custom SerializationBinder.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-918: Server-Side Request Forgery (SSRF) - 6 rules
# -----------------------------------------------------------------------------

SSRF_RULES: List[InjectionRule] = [
    # INJ-SSRF-001: Python requests with user URL
    InjectionRule(
        id="INJ-SSRF-001",
        title="HTTP request with user-controlled URL",
        description=(
            "Making HTTP requests to user-provided URLs enables SSRF. "
            "Attackers can access internal services, cloud metadata APIs, or perform port scanning."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        patterns={
            "python": LanguagePattern(
                r'requests\.(?:get|post|put|delete|head|patch|request)\s*\(\s*(?:f["\']|request\.|input|user|url)',
            ),
        },
        fix_suggestion="Validate URLs against an allowlist of hosts/domains. Block internal IPs (127.0.0.1, 10.*, 192.168.*, etc.).",
        false_positive_patterns=[r'allowlist', r'whitelist', r'validate_url'],
    ),

    # INJ-SSRF-002: Python urllib
    InjectionRule(
        id="INJ-SSRF-002",
        title="urllib request with user URL",
        description=(
            "urllib.request.urlopen with user-controlled URLs enables SSRF attacks."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        patterns={
            "python": LanguagePattern(
                r'urllib\.request\.urlopen\s*\(\s*(?:request|input|user|url)',
            ),
        },
        fix_suggestion="Validate and sanitize URLs. Use a URL allowlist for external services.",
    ),

    # INJ-SSRF-003: JavaScript fetch/axios
    InjectionRule(
        id="INJ-SSRF-003",
        title="HTTP client with user-controlled URL",
        description=(
            "Server-side fetch/axios with user URLs enables SSRF. Can access internal services or cloud metadata."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        patterns={
            "javascript": LanguagePattern(
                r'(?:fetch|axios\.(?:get|post|put|delete)|got|request)\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|url)',
            ),
            "typescript": LanguagePattern(
                r'(?:fetch|axios\.(?:get|post|put|delete)|got|request)\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user|url)',
            ),
        },
        fix_suggestion="Validate URLs against allowlist. Block private IP ranges and localhost.",
    ),

    # INJ-SSRF-004: Java URL/HttpClient
    InjectionRule(
        id="INJ-SSRF-004",
        title="Java HTTP request with user URL",
        description=(
            "Creating URLs from user input enables SSRF attacks in Java applications."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        patterns={
            "java": LanguagePattern(
                r'new\s+URL\s*\(\s*(?:request\.getParameter|input|user)',
            ),
        },
        fix_suggestion="Validate URL host against allowlist. Use URL parsing to extract and validate hostname.",
    ),

    # INJ-SSRF-005: PHP cURL/file_get_contents
    InjectionRule(
        id="INJ-SSRF-005",
        title="PHP HTTP request with user URL",
        description=(
            "PHP URL functions with user input enable SSRF attacks."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        patterns={
            "php": LanguagePattern(
                r'(?:file_get_contents|curl_setopt.*CURLOPT_URL|fopen)\s*\([^)]*\$_(?:GET|POST|REQUEST)',
            ),
        },
        fix_suggestion="Validate URL scheme (http/https only) and host against allowlist.",
    ),

    # INJ-SSRF-006: Ruby HTTP requests
    InjectionRule(
        id="INJ-SSRF-006",
        title="Ruby HTTP request with user URL",
        description=(
            "Ruby HTTP libraries with user-controlled URLs enable SSRF."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        patterns={
            "ruby": LanguagePattern(
                r'(?:Net::HTTP|HTTParty|Faraday|RestClient)\.(?:get|post|put)\s*\([^)]*(?:params|request|input)',
            ),
        },
        fix_suggestion="Validate URLs against allowlist. Use ssrf_filter gem for protection.",
    ),
]


# =============================================================================
# TIER 2: HIGH PRIORITY INJECTION RULES
# =============================================================================

# -----------------------------------------------------------------------------
# CWE-94: Code Injection (eval/exec) - 5 rules
# -----------------------------------------------------------------------------

CODE_INJECTION_RULES: List[InjectionRule] = [
    # INJ-CODE-001: Python eval/exec
    InjectionRule(
        id="INJ-CODE-001",
        title="Python eval/exec with user input",
        description=(
            "Executing user-controlled code strings enables arbitrary code execution."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-94"],
        category="code_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:eval|exec)\s*\(\s*(?:f["\']|request|input|user|data)',
            ),
        },
        fix_suggestion="Never use eval/exec with user input. Use ast.literal_eval for safe literal parsing.",
    ),

    # INJ-CODE-002: Python compile
    InjectionRule(
        id="INJ-CODE-002",
        title="Python compile with user input",
        description=(
            "compile() followed by exec() with user input enables code injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-94"],
        category="code_injection",
        patterns={
            "python": LanguagePattern(
                r'compile\s*\(\s*(?:request|input|user|data)',
            ),
        },
        fix_suggestion="Avoid compiling user input. Use a sandbox or DSL for user-defined logic.",
    ),

    # INJ-CODE-003: JavaScript eval
    InjectionRule(
        id="INJ-CODE-003",
        title="JavaScript eval with user input",
        description=(
            "eval() with user data enables arbitrary JavaScript execution."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-94"],
        category="code_injection",
        patterns={
            "javascript": LanguagePattern(
                r'eval\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user)',
            ),
            "typescript": LanguagePattern(
                r'eval\s*\(\s*(?:req\.|params\.|body\.|query\.|input|user)',
            ),
        },
        fix_suggestion="Never use eval with user input. Use JSON.parse for data parsing.",
    ),

    # INJ-CODE-004: JavaScript new Function
    InjectionRule(
        id="INJ-CODE-004",
        title="JavaScript new Function with user input",
        description=(
            "new Function() constructor with user input enables code injection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-94"],
        category="code_injection",
        patterns={
            "javascript": LanguagePattern(
                r'new\s+Function\s*\(\s*(?:req\.|params\.|input|user|`)',
            ),
            "typescript": LanguagePattern(
                r'new\s+Function\s*\(\s*(?:req\.|params\.|input|user|`)',
            ),
        },
        fix_suggestion="Avoid dynamic function creation. Use a safe expression parser for user logic.",
    ),

    # INJ-CODE-005: PHP eval/assert
    InjectionRule(
        id="INJ-CODE-005",
        title="PHP code execution with user input",
        description=(
            "PHP eval/assert with user data enables arbitrary PHP execution."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-94"],
        category="code_injection",
        patterns={
            "php": LanguagePattern(
                r'(?:eval|assert|create_function)\s*\(\s*\$_(?:GET|POST|REQUEST)',
            ),
        },
        fix_suggestion="Never use eval/assert with user input. Disable dangerous functions in php.ini.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-611: XML External Entity (XXE) - 5 rules
# -----------------------------------------------------------------------------

XXE_RULES: List[InjectionRule] = [
    # INJ-XXE-001: Python XML parsers
    InjectionRule(
        id="INJ-XXE-001",
        title="Python XML parsing vulnerable to XXE",
        description=(
            "Standard library XML parsers process external entities by default, enabling XXE attacks. "
            "Attackers can read local files or perform SSRF via external entity references."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-611"],
        category="xxe",
        patterns={
            "python": LanguagePattern(
                r'(?:etree\.parse|xml\.dom\.minidom\.parse|xml\.sax\.parse|ElementTree\.parse)\s*\(',
            ),
        },
        fix_suggestion="Use defusedxml library instead of standard xml: from defusedxml import ElementTree",
        false_positive_patterns=[r'defusedxml', r'defused'],
        context_keywords=["request", "input", "user", "upload", "file", "data"],
        require_context=True,
    ),

    # INJ-XXE-002: Python lxml without safe settings
    InjectionRule(
        id="INJ-XXE-002",
        title="lxml parsing without disabling external entities",
        description=(
            "lxml parses external entities unless explicitly disabled, enabling XXE."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-611"],
        category="xxe",
        patterns={
            "python": LanguagePattern(
                r'lxml\.etree\.(?:parse|fromstring)\s*\(',
            ),
        },
        fix_suggestion="Use defusedxml.lxml or disable entities: parser = lxml.etree.XMLParser(resolve_entities=False)",
        false_positive_patterns=[r'resolve_entities\s*=\s*False', r'defusedxml'],
    ),

    # INJ-XXE-003: Java DocumentBuilder
    InjectionRule(
        id="INJ-XXE-003",
        title="Java XML parsing without XXE protection",
        description=(
            "Java XML parsers need explicit configuration to prevent XXE attacks."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-611"],
        category="xxe",
        patterns={
            "java": LanguagePattern(
                r'DocumentBuilderFactory\.newInstance\s*\(\s*\)',
            ),
        },
        fix_suggestion=(
            "Disable external entities: factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true); "
            "factory.setFeature('http://apache.org/xml/features/disallow-doctype-decl', true);"
        ),
        false_positive_patterns=[r'setFeature.*SECURE_PROCESSING', r'disallow-doctype-decl'],
    ),

    # INJ-XXE-004: PHP XML functions
    InjectionRule(
        id="INJ-XXE-004",
        title="PHP XML parsing without entity protection",
        description=(
            "PHP XML functions can process external entities unless explicitly disabled."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-611"],
        category="xxe",
        patterns={
            "php": LanguagePattern(
                r'(?:simplexml_load_string|simplexml_load_file|DOMDocument.*loadXML)\s*\(',
            ),
        },
        fix_suggestion="Disable entity loading: libxml_disable_entity_loader(true); before parsing XML.",
        false_positive_patterns=[r'libxml_disable_entity_loader'],
        context_keywords=["$_", "input", "upload", "file", "request"],
        require_context=True,
    ),

    # INJ-XXE-005: C# XML parsing
    InjectionRule(
        id="INJ-XXE-005",
        title="C# XML parsing without secure settings",
        description=(
            "XmlReader/XmlDocument in C# can be vulnerable to XXE without proper settings."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-611"],
        category="xxe",
        patterns={
            "csharp": LanguagePattern(
                r'(?:XmlReader\.Create|XmlDocument.*Load|XDocument\.Load)\s*\(',
            ),
        },
        fix_suggestion="Use XmlReaderSettings with DtdProcessing = DtdProcessing.Prohibit and XmlResolver = null.",
        false_positive_patterns=[r'DtdProcessing\.Prohibit', r'XmlResolver\s*=\s*null'],
    ),
]


# -----------------------------------------------------------------------------
# CWE-1336: Server-Side Template Injection (SSTI) - 4 rules
# -----------------------------------------------------------------------------

SSTI_RULES: List[InjectionRule] = [
    # INJ-SSTI-001: Python Jinja2 template from user
    InjectionRule(
        id="INJ-SSTI-001",
        title="Jinja2 template rendering from user input",
        description=(
            "Rendering user-controlled templates enables SSTI and remote code execution. "
            "Attackers can execute arbitrary Python code via Jinja2 template syntax."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-1336"],
        category="ssti",
        patterns={
            "python": LanguagePattern(
                r'(?:Template|Environment\s*\(\s*\)\.from_string)\s*\(\s*(?:request|input|user|data)',
            ),
        },
        fix_suggestion="Never render user-provided templates. Use a sandboxed environment or template allowlist.",
    ),

    # INJ-SSTI-002: Flask render_template_string
    InjectionRule(
        id="INJ-SSTI-002",
        title="Flask render_template_string with user input",
        description=(
            "render_template_string with user input enables SSTI in Flask applications."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-1336"],
        category="ssti",
        patterns={
            "python": LanguagePattern(
                r'render_template_string\s*\(\s*(?:f["\']|request\.|input|user)',
            ),
        },
        fix_suggestion="Use render_template with static template files, not user-provided strings.",
    ),

    # INJ-SSTI-003: JavaScript template engines
    InjectionRule(
        id="INJ-SSTI-003",
        title="Template engine rendering user input",
        description=(
            "Server-side template rendering with user data can enable code execution."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1336"],
        category="ssti",
        patterns={
            "javascript": LanguagePattern(
                r'(?:ejs|pug|handlebars|mustache|nunjucks)\.(?:render|compile|renderString)\s*\(\s*(?:req\.|input|user|body)',
            ),
            "typescript": LanguagePattern(
                r'(?:ejs|pug|handlebars|mustache|nunjucks)\.(?:render|compile|renderString)\s*\(\s*(?:req\.|input|user|body)',
            ),
        },
        fix_suggestion="Never render user-controlled templates. Use static templates with parameterized data.",
    ),

    # INJ-SSTI-004: Java template engines
    InjectionRule(
        id="INJ-SSTI-004",
        title="Java template engine with user input",
        description=(
            "Server-side template injection in Java template engines (Velocity, FreeMarker, Thymeleaf)."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-1336"],
        category="ssti",
        patterns={
            "java": LanguagePattern(
                r'(?:Velocity|VelocityEngine|FreeMarker|Thymeleaf).*(?:evaluate|process|merge)\s*\([^)]*(?:request|input|getParameter)',
            ),
        },
        fix_suggestion="Never process user-provided template content. Use static templates.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-90: LDAP Injection - 3 rules
# -----------------------------------------------------------------------------

LDAP_INJECTION_RULES: List[InjectionRule] = [
    # INJ-LDAP-001: Python LDAP search
    InjectionRule(
        id="INJ-LDAP-001",
        title="LDAP search with user input",
        description=(
            "Building LDAP filters with user input enables LDAP injection. "
            "Attackers can bypass authentication or extract directory data."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-90"],
        category="ldap_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:search|search_s|search_st)\s*\([^)]*(?:f["\']|\.format|%.*%|request|input)',
            ),
        },
        fix_suggestion="Use parameterized LDAP queries or escape special characters: ldap.filter.escape_filter_chars()",
    ),

    # INJ-LDAP-002: Java LDAP
    InjectionRule(
        id="INJ-LDAP-002",
        title="Java LDAP query with user input",
        description=(
            "LDAP queries with string concatenation enable injection attacks."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-90"],
        category="ldap_injection",
        patterns={
            "java": LanguagePattern(
                r'(?:DirContext|LdapContext).*search\s*\([^)]*\+.*(?:request|input|getParameter)',
            ),
        },
        fix_suggestion="Use SearchControls with parameterized filter or escape special LDAP characters.",
    ),

    # INJ-LDAP-003: C# LDAP
    InjectionRule(
        id="INJ-LDAP-003",
        title="C# LDAP query with user input",
        description=(
            "DirectorySearcher with user-controlled filter enables LDAP injection."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-90"],
        category="ldap_injection",
        patterns={
            "csharp": LanguagePattern(
                r'DirectorySearcher.*Filter\s*=\s*["\'][^"\']*\+.*(?:Request|input|user)',
            ),
        },
        fix_suggestion="Use parameterized filters or escape LDAP special characters (*, (, ), \\, NUL).",
    ),
]


# -----------------------------------------------------------------------------
# CWE-943: NoSQL Injection - 4 rules
# -----------------------------------------------------------------------------

NOSQL_INJECTION_RULES: List[InjectionRule] = [
    # INJ-NOSQL-001: MongoDB query with user input
    InjectionRule(
        id="INJ-NOSQL-001",
        title="MongoDB query with user-controlled operators",
        description=(
            "Passing user input directly to MongoDB queries enables operator injection. "
            "Attackers can use $gt, $ne, $regex operators to bypass authentication or extract data."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-943"],
        category="nosql_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:find|find_one|update|delete)\s*\(\s*(?:\{[^}]*(?:request|input|user)|request\.(?:json|args|form))',
            ),
            "javascript": LanguagePattern(
                r'(?:find|findOne|updateOne|deleteOne)\s*\(\s*(?:\{[^}]*(?:req\.|body\.|params)|req\.body)',
            ),
        },
        fix_suggestion="Validate query structure and reject operator keys ($). Use explicit field matching.",
    ),

    # INJ-NOSQL-002: MongoDB $where clause
    InjectionRule(
        id="INJ-NOSQL-002",
        title="MongoDB $where with user input",
        description=(
            "$where clause executes JavaScript, enabling code injection with user input."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-943", "CWE-94"],
        category="nosql_injection",
        patterns={
            "javascript": LanguagePattern(
                r'\$where\s*:\s*(?:`[^`]*\$\{|["\'][^"\']*\+|req\.|input|user)',
            ),
            "python": LanguagePattern(
                r'\$where\s*:\s*(?:f["\']|.*\+.*(?:request|input)|request)',
            ),
        },
        fix_suggestion="Avoid $where entirely. Use standard query operators or aggregation pipeline instead.",
    ),

    # INJ-NOSQL-003: Redis command injection
    InjectionRule(
        id="INJ-NOSQL-003",
        title="Redis command with user input",
        description=(
            "Building Redis commands with user input can enable command injection."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-943"],
        category="nosql_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:redis|r)\.(?:execute_command|eval)\s*\([^)]*(?:f["\']|request|input)',
            ),
            "javascript": LanguagePattern(
                r'(?:redis|client)\.(?:sendCommand|send_command|eval)\s*\([^)]*(?:`[^`]*\$\{|req\.|input)',
            ),
        },
        fix_suggestion="Use parameterized Redis commands. Avoid EVAL with user input.",
    ),

    # INJ-NOSQL-004: Elasticsearch query injection
    InjectionRule(
        id="INJ-NOSQL-004",
        title="Elasticsearch query with user input",
        description=(
            "Building Elasticsearch queries with user input enables query injection."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-943"],
        category="nosql_injection",
        patterns={
            "python": LanguagePattern(
                r'(?:es|elasticsearch|client)\.search\s*\([^)]*(?:f["\']|request|input|json\.loads)',
            ),
            "javascript": LanguagePattern(
                r'(?:client|es)\.search\s*\(\s*\{[^}]*(?:req\.|body\.|JSON\.parse)',
            ),
        },
        fix_suggestion="Use Elasticsearch query DSL builders. Validate and sanitize user input.",
    ),
]


# -----------------------------------------------------------------------------
# CWE-352: Cross-Site Request Forgery (CSRF) - 3 rules
# -----------------------------------------------------------------------------

CSRF_RULES: List[InjectionRule] = [
    # INJ-CSRF-001: Missing CSRF token validation
    InjectionRule(
        id="INJ-CSRF-001",
        title="State-changing endpoint without CSRF protection",
        description=(
            "POST/PUT/DELETE endpoints without CSRF token validation are vulnerable to CSRF attacks. "
            "Attackers can trick users into performing unintended actions."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-352"],
        category="csrf",
        patterns={
            "python": LanguagePattern(
                r'@(?:app\.route|router\.|api_view)\s*\([^)]*methods\s*=\s*\[[^]]*(?:POST|PUT|DELETE|PATCH)',
                flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Enable CSRF protection: Flask-WTF for Flask, @csrf_protect for Django.",
        false_positive_patterns=[r'csrf', r'CSRFProtect', r'csrf_exempt', r'@api_view'],
        context_keywords=["csrf", "token"],
        require_context=False,  # Flag all state-changing routes, FP filtering handles exemptions
    ),

    # INJ-CSRF-002: Disabled CSRF protection
    InjectionRule(
        id="INJ-CSRF-002",
        title="CSRF protection explicitly disabled",
        description=(
            "CSRF protection is explicitly disabled, leaving the endpoint vulnerable."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-352"],
        category="csrf",
        patterns={
            "python": LanguagePattern(
                r'@csrf_exempt',
            ),
            "javascript": LanguagePattern(
                r'csrf\s*:\s*false',
            ),
            "csharp": LanguagePattern(
                r'\[IgnoreAntiforgeryToken\]',
            ),
        },
        fix_suggestion="Re-enable CSRF protection. Only disable for truly stateless API endpoints with other auth.",
    ),

    # INJ-CSRF-003: SameSite cookie not set
    InjectionRule(
        id="INJ-CSRF-003",
        title="Session cookie without SameSite attribute",
        description=(
            "Cookies without SameSite attribute can be sent in cross-site requests, enabling CSRF."
        ),
        severity=Severity.LOW,
        cwe_ids=["CWE-352"],
        category="csrf",
        patterns={
            "python": LanguagePattern(
                r'set_cookie\s*\([^)]+\)(?!.*samesite)',
                flags=re.IGNORECASE | re.DOTALL,
            ),
            "javascript": LanguagePattern(
                r'(?:res\.cookie|cookies\.set)\s*\([^)]+\)(?!.*[Ss]ame[Ss]ite)',
            ),
        },
        fix_suggestion="Set SameSite=Strict or SameSite=Lax on session cookies.",
        false_positive_patterns=[r'[Ss]ame[Ss]ite'],
    ),
]


# -----------------------------------------------------------------------------
# CWE-434: Unrestricted File Upload - 4 rules
# -----------------------------------------------------------------------------

FILE_UPLOAD_RULES: List[InjectionRule] = [
    # INJ-UPLOAD-001: File upload without extension validation
    InjectionRule(
        id="INJ-UPLOAD-001",
        title="File upload without extension validation",
        description=(
            "Accepting file uploads without validating extensions can allow malicious file uploads. "
            "Attackers can upload executable files (PHP, JSP, ASPX) to achieve code execution."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-434"],
        category="file_upload",
        patterns={
            "python": LanguagePattern(
                r'(?:request\.files|upload|file).*\.save\s*\(',
            ),
        },
        fix_suggestion="Validate file extensions against allowlist. Use werkzeug.utils.secure_filename().",
        false_positive_patterns=[r'secure_filename', r'allowed_extensions', r'ALLOWED_EXTENSIONS'],
        context_keywords=["request.files", "upload", "FileField"],
        require_context=True,
    ),

    # INJ-UPLOAD-002: File upload with user-controlled filename
    InjectionRule(
        id="INJ-UPLOAD-002",
        title="File saved with user-controlled filename",
        description=(
            "Using user-provided filenames can lead to path traversal or overwriting critical files."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-434", "CWE-22"],
        category="file_upload",
        patterns={
            "python": LanguagePattern(
                r'\.save\s*\(\s*(?:os\.path\.join\s*\([^)]*(?:filename|request)|f["\'].*\{.*filename)',
            ),
            "javascript": LanguagePattern(
                r'(?:writeFile|createWriteStream)\s*\([^)]*(?:req\.file|filename|originalname)',
            ),
        },
        fix_suggestion="Generate a random filename server-side. Never use user-provided filenames directly.",
    ),

    # INJ-UPLOAD-003: PHP file upload
    InjectionRule(
        id="INJ-UPLOAD-003",
        title="PHP file upload without validation",
        description=(
            "PHP file uploads without proper validation can lead to remote code execution."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-434"],
        category="file_upload",
        patterns={
            "php": LanguagePattern(
                r'move_uploaded_file\s*\(\s*\$_FILES',
            ),
        },
        fix_suggestion="Validate MIME type, extension, and file content. Store uploads outside web root.",
        false_positive_patterns=[r'pathinfo.*PATHINFO_EXTENSION', r'mime_content_type'],
    ),

    # INJ-UPLOAD-004: Java file upload
    InjectionRule(
        id="INJ-UPLOAD-004",
        title="Java file upload without validation",
        description=(
            "Java file uploads need proper validation of content type and filename."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-434"],
        category="file_upload",
        patterns={
            "java": LanguagePattern(
                r'(?:MultipartFile|Part).*(?:transferTo|write)\s*\(',
            ),
        },
        fix_suggestion="Validate content type, extension, and use a secure random filename.",
        false_positive_patterns=[r'getContentType', r'getAllowedExtensions'],
    ),
]


# =============================================================================
# ALL RULES COMBINED
# =============================================================================

ALL_INJECTION_RULES: List[InjectionRule] = (
    XSS_RULES +
    SQL_INJECTION_RULES +
    COMMAND_INJECTION_RULES +
    PATH_TRAVERSAL_RULES +
    DESERIALIZATION_RULES +
    SSRF_RULES +
    CODE_INJECTION_RULES +
    XXE_RULES +
    SSTI_RULES +
    LDAP_INJECTION_RULES +
    NOSQL_INJECTION_RULES +
    CSRF_RULES +
    FILE_UPLOAD_RULES
)


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class InjectionDetector(BaseScanner):
    """
    Detects injection vulnerabilities across multiple languages.

    Covers CWE Top 25 injection-related weaknesses including:
    - CWE-79: Cross-site Scripting (XSS)
    - CWE-89: SQL Injection
    - CWE-78/77: Command Injection
    - CWE-22: Path Traversal
    - CWE-502: Deserialization
    - CWE-918: SSRF
    - CWE-94: Code Injection
    - CWE-611: XXE
    - CWE-90: LDAP Injection
    - CWE-943: NoSQL Injection
    - CWE-1336: Template Injection
    - CWE-352: CSRF
    - CWE-434: File Upload

    Multi-language: Python, JavaScript, TypeScript, Java, C#, PHP, Ruby, Go, C, C++
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in ALL_INJECTION_RULES:
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
        return ScannerType.INJECTION

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
        """Execute injection vulnerability scan."""
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

                for rule in ALL_INJECTION_RULES:
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
                            id=f"injection-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "injection", rule.category},
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
        categories = {}
        for rule in ALL_INJECTION_RULES:
            if rule.category not in categories:
                categories[rule.category] = 0
            categories[rule.category] += 1

        cwe_coverage = set()
        for rule in ALL_INJECTION_RULES:
            cwe_coverage.update(rule.cwe_ids)

        return {
            "total_rules": len(ALL_INJECTION_RULES),
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
                for rule in ALL_INJECTION_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": sorted(cwe_coverage),
            "category_descriptions": {
                "xss": "CWE-79: Cross-site Scripting",
                "sql_injection": "CWE-89: SQL Injection",
                "command_injection": "CWE-78/77: OS Command Injection",
                "path_traversal": "CWE-22: Path Traversal",
                "deserialization": "CWE-502: Deserialization of Untrusted Data",
                "ssrf": "CWE-918: Server-Side Request Forgery",
                "code_injection": "CWE-94: Code Injection",
                "xxe": "CWE-611: XML External Entity",
                "ssti": "CWE-1336: Server-Side Template Injection",
                "ldap_injection": "CWE-90: LDAP Injection",
                "nosql_injection": "CWE-943: NoSQL Injection",
                "csrf": "CWE-352: Cross-Site Request Forgery",
                "file_upload": "CWE-434: Unrestricted File Upload",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_injection_detector() -> InjectionDetector:
    """Factory function to create injection detector."""
    return InjectionDetector()
