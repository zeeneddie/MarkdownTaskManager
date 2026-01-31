"""
AST-Based Taint Tracker - Cross-Function Data Flow Analysis.

Fase 42: Tracks tainted data from sources to sinks across functions.

Dual approach:
- Python: Uses `ast` module for real taint tracking (0.85 confidence)
- Other languages (JS, Java, C#, PHP, Ruby, Go): Regex source-to-sink heuristics (0.6-0.7)

Categories (~150 rules):
- SQL taint (20), XSS taint (18), CMD taint (15), Path traversal (12)
- Deserialization (10), SSRF (10), LDAP/NoSQL (8), Code injection (10)
- Log injection (8), Header injection (8), Email injection (6), Regex injection (5)
- Cross-function Python AST (20)

No external dependencies: Only stdlib (ast, re, math)
"""

import re
import ast
import math
import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
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
    "python": LanguageDefinition(name="Python", extensions={".py", ".pyw"}),
    "javascript": LanguageDefinition(name="JavaScript", extensions={".js", ".jsx", ".mjs", ".cjs"}),
    "typescript": LanguageDefinition(name="TypeScript", extensions={".ts", ".tsx"}),
    "java": LanguageDefinition(name="Java", extensions={".java", ".jsp"}),
    "csharp": LanguageDefinition(name="C#", extensions={".cs", ".cshtml"}),
    "php": LanguageDefinition(name="PHP", extensions={".php", ".phtml"}),
    "ruby": LanguageDefinition(name="Ruby", extensions={".rb", ".erb"}),
    "go": LanguageDefinition(name="Go", extensions={".go"}),
}


# =============================================================================
# RULE DATA STRUCTURE
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class TaintRule:
    """A taint tracking rule with source-sink heuristic patterns."""
    id: str
    title: str
    description: str
    severity: Severity
    cwe_ids: List[str]
    category: str

    # Combined source-near-sink regex patterns per language
    patterns: Dict[str, LanguagePattern]

    fix_suggestion: str
    confidence: float = 0.65

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)

    # Sanitizer patterns that indicate safe usage
    sanitizer_patterns: List[str] = field(default_factory=list)


# =============================================================================
# PYTHON AST TAINT TRACKING DATA STRUCTURES
# =============================================================================

@dataclass
class TaintSource:
    """A source of tainted data in Python AST."""
    variable: str
    function: str
    line: int
    source_type: str  # 'request', 'input', 'argv', 'env'


@dataclass
class TaintSink:
    """A dangerous sink where tainted data shouldn't flow."""
    function_call: str
    line: int
    cwe: str
    category: str
    arg_index: int = 0  # Which argument position is dangerous


@dataclass
class FunctionSignature:
    """Track function parameters and return values."""
    name: str
    parameters: List[str]
    returns_tainted: bool = False
    tainted_params: Set[int] = field(default_factory=set)


# Python AST taint source patterns
PYTHON_TAINT_SOURCES = [
    ("request.args", "request"), ("request.form", "request"), ("request.json", "request"),
    ("request.data", "request"), ("request.values", "request"), ("request.files", "request"),
    ("request.GET", "request"), ("request.POST", "request"), ("request.META", "request"),
    ("request.getParameter", "request"), ("request.get_json", "request"),
    ("input(", "stdin"), ("raw_input(", "stdin"),
    ("sys.argv", "argv"), ("sys.stdin", "stdin"),
    ("os.environ", "env"), ("os.getenv", "env"),
]

# Python AST taint sinks (function → CWE)
PYTHON_TAINT_SINKS = [
    ("cursor.execute", "CWE-89", "sql_injection"),
    ("connection.execute", "CWE-89", "sql_injection"),
    (".raw(", "CWE-89", "sql_injection"),
    ("os.system", "CWE-78", "command_injection"),
    ("os.popen", "CWE-78", "command_injection"),
    ("subprocess.call", "CWE-78", "command_injection"),
    ("subprocess.run", "CWE-78", "command_injection"),
    ("subprocess.Popen", "CWE-78", "command_injection"),
    ("eval(", "CWE-94", "code_injection"),
    ("exec(", "CWE-94", "code_injection"),
    ("compile(", "CWE-94", "code_injection"),
    ("open(", "CWE-22", "path_traversal"),
    ("pickle.loads", "CWE-502", "deserialization"),
    ("yaml.load", "CWE-502", "deserialization"),
    ("marshal.loads", "CWE-502", "deserialization"),
    ("requests.get", "CWE-918", "ssrf"),
    ("requests.post", "CWE-918", "ssrf"),
    ("urllib.request.urlopen", "CWE-918", "ssrf"),
    ("render_template_string", "CWE-79", "xss"),
    ("Markup(", "CWE-79", "xss"),
    ("mark_safe(", "CWE-79", "xss"),
    (".innerHTML", "CWE-79", "xss"),
    ("ldap.search", "CWE-90", "ldap_injection"),
    ("smtplib.sendmail", "CWE-93", "email_injection"),
    ("re.compile(", "CWE-1333", "regex_injection"),
]

# Sanitizers that break taint flow
PYTHON_SANITIZERS = [
    "html.escape", "markupsafe.escape", "bleach.clean", "cgi.escape",
    "shlex.quote", "pipes.quote",
    "os.path.basename", "pathlib.Path.name", "secure_filename",
    "int(", "float(", "bool(",
    "parameterize", "sanitize", "escape", "encode",
    "html_escape", "url_quote", "quote_plus",
]


# =============================================================================
# SQL TAINT RULES (20)
# =============================================================================

SQL_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-SQL-001", title="Python tainted data in SQL execute",
        description="User input flows to cursor.execute() via string formatting, enabling SQL injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"python": LanguagePattern(r'(?:request\.|input\(|sys\.argv|os\.environ).*?(?:cursor|conn|db|session)\.execute\s*\(\s*(?:f["\']|["\'].*%|.*\.format\(|.*\+)', flags=re.DOTALL | re.MULTILINE)},
        fix_suggestion="Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id=%s', [user_id]).",
        confidence=0.7,
        false_positive_patterns=[r'execute\s*\(\s*["\'][^"\']*["\']\s*,\s*[\[\(]', r'parameterize', r'# nosec'],
        sanitizer_patterns=["parameterized", "prepared_statement"],
    ),
    TaintRule(
        id="TAINT-SQL-002", title="Python f-string in SQL query",
        description="F-string used in SQL query with user-derived variable enables SQL injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"python": LanguagePattern(r'\.execute\s*\(\s*f["\'](?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)')},
        fix_suggestion="Replace f-string with parameterized query using %s or ? placeholders.",
        confidence=0.8,
        false_positive_patterns=[r'# test', r'# nosec'],
    ),
    TaintRule(
        id="TAINT-SQL-003", title="Python .format() in SQL query",
        description="String .format() in SQL query enables SQL injection when parameters contain user input.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"python": LanguagePattern(r'\.execute\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE).*\.format\s*\(')},
        fix_suggestion="Use parameterized queries instead of string formatting.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SQL-004", title="Python string concat in SQL query",
        description="String concatenation in SQL query with variables enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"python": LanguagePattern(r'\.execute\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\']\s*\+')},
        fix_suggestion="Use parameterized queries with placeholder syntax.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SQL-005", title="Python % formatting in SQL query",
        description="% string formatting in SQL query enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"python": LanguagePattern(r'\.execute\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*%s[^"\']*["\']\s*%')},
        fix_suggestion="Use parameterized queries: cursor.execute(sql, params) instead of sql % params.",
        confidence=0.7,
        false_positive_patterns=[r'\.execute\s*\(\s*["\'][^"\']*["\']\s*,\s*[\[\(]'],
    ),
    TaintRule(
        id="TAINT-SQL-006", title="JS tainted data in SQL query",
        description="User input from req.body/query/params flows to database query.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:req\.(?:body|query|params)|request\.(?:body|query)).*?(?:\.query|\.execute)\s*\(\s*(?:`|["\'].*\+|\$\{)', flags=re.DOTALL | re.MULTILINE),
            "typescript": LanguagePattern(r'(?:req\.(?:body|query|params)|request\.(?:body|query)).*?(?:\.query|\.execute)\s*\(\s*(?:`|["\'].*\+|\$\{)', flags=re.DOTALL | re.MULTILINE),
        },
        fix_suggestion="Use parameterized queries: db.query('SELECT * FROM t WHERE id = $1', [userId]).",
        confidence=0.65,
        false_positive_patterns=[r'\.query\s*\(\s*["\'][^"\']*["\']\s*,\s*\[', r'prepared'],
    ),
    TaintRule(
        id="TAINT-SQL-007", title="JS template literal in SQL",
        description="Template literal with user input in SQL query enables injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={
            "javascript": LanguagePattern(r'\.query\s*\(\s*`(?:SELECT|INSERT|UPDATE|DELETE).*\$\{'),
            "typescript": LanguagePattern(r'\.query\s*\(\s*`(?:SELECT|INSERT|UPDATE|DELETE).*\$\{'),
        },
        fix_suggestion="Use parameterized queries instead of template literals for SQL.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SQL-008", title="JS string concat in SQL",
        description="String concatenation in SQL query with user input enables injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={
            "javascript": LanguagePattern(r'\.query\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\']\s*\+'),
            "typescript": LanguagePattern(r'\.query\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\']\s*\+'),
        },
        fix_suggestion="Use parameterized queries with placeholder syntax.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SQL-009", title="JS Sequelize raw query with input",
        description="Sequelize raw query or literal with user input enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:sequelize\.query|Sequelize\.literal)\s*\(\s*(?:`.*\$\{|["\'].*\+)'),
            "typescript": LanguagePattern(r'(?:sequelize\.query|Sequelize\.literal)\s*\(\s*(?:`.*\$\{|["\'].*\+)'),
        },
        fix_suggestion="Use Sequelize query with replacements: sequelize.query(sql, { replacements: { id } }).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-SQL-010", title="JS Knex raw query with input",
        description="Knex.raw with user input enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:knex|db)\.raw\s*\(\s*(?:`.*\$\{|["\'].*\+)'),
            "typescript": LanguagePattern(r'(?:knex|db)\.raw\s*\(\s*(?:`.*\$\{|["\'].*\+)'),
        },
        fix_suggestion="Use Knex bindings: knex.raw('SELECT * FROM t WHERE id = ?', [id]).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-SQL-011", title="Java Statement with string concat",
        description="Statement.execute with string concatenation enables SQL injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"java": LanguagePattern(r'(?:statement|stmt)\.(?:execute|executeQuery|executeUpdate)\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use PreparedStatement with parameterized queries.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-SQL-012", title="Java PreparedStatement from concat",
        description="Building PreparedStatement SQL with concatenation then executing enables injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"java": LanguagePattern(r'prepareStatement\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use ? placeholders in PreparedStatement: prepareStatement('SELECT * FROM t WHERE id = ?').",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-SQL-013", title="Java JPA native query with concat",
        description="JPA createNativeQuery with string concatenation enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"java": LanguagePattern(r'createNativeQuery\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use named parameters: em.createNativeQuery('SELECT * FROM t WHERE id = :id').",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-SQL-014", title="Java Spring JDBC with concat",
        description="Spring JdbcTemplate with string concatenation enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"java": LanguagePattern(r'jdbcTemplate\.(?:query|update|execute)\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use parameterized queries: jdbcTemplate.query(sql, new Object[]{param}, mapper).",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-SQL-015", title="Java Hibernate HQL with concat",
        description="Hibernate createQuery with string concatenation enables HQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"java": LanguagePattern(r'createQuery\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use named parameters: session.createQuery('FROM User u WHERE u.name = :name').",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-SQL-016", title="PHP mysql query with variable",
        description="PHP mysql/mysqli query with user variable enables SQL injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"php": LanguagePattern(r'(?:mysql_query|mysqli_query|->query)\s*\(\s*["\'][^"\']*["\']\s*\.\s*\$')},
        fix_suggestion="Use prepared statements: $stmt = $pdo->prepare('SELECT * FROM t WHERE id = ?').",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-SQL-017", title="PHP PDO query with variable",
        description="PDO query with direct variable interpolation enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"php": LanguagePattern(r'->query\s*\(\s*["\'][^"\']*\$(?:_GET|_POST|_REQUEST|[a-z]+)')},
        fix_suggestion="Use PDO prepared statements: $stmt = $pdo->prepare(sql); $stmt->execute([$param]).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-SQL-018", title="PHP string interpolation in SQL",
        description="PHP double-quoted SQL string with variable interpolation enables injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"php": LanguagePattern(r'(?:->query|mysql_query|mysqli_query)\s*\(\s*"(?:SELECT|INSERT|UPDATE|DELETE)[^"]*\$')},
        fix_suggestion="Use prepared statements with bound parameters.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-SQL-019", title="C# SqlCommand with concat",
        description="C# SqlCommand with string concatenation enables SQL injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"csharp": LanguagePattern(r'(?:SqlCommand|SqlDataAdapter)\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use SqlParameter: cmd.Parameters.AddWithValue('@param', value).",
        confidence=0.9,
    ),
    TaintRule(
        id="TAINT-SQL-020", title="Ruby ActiveRecord with interpolation",
        description="Ruby ActiveRecord query with string interpolation enables SQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-89"], category="sql_injection",
        patterns={"ruby": LanguagePattern(r'\.(?:where|find_by_sql|order|having|select)\s*\(\s*["\'].*\#\{')},
        fix_suggestion="Use parameterized queries: where('name = ?', params[:name]).",
        confidence=0.85,
    ),
]


# =============================================================================
# XSS TAINT RULES (18)
# =============================================================================

XSS_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-XSS-001", title="JS user input to innerHTML",
        description="User input from request flows to innerHTML assignment, enabling XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={
            "javascript": LanguagePattern(r'(?:req\.(?:body|query|params)|request\.(?:body|query)).*?\.innerHTML\s*=', flags=re.DOTALL | re.MULTILINE),
            "typescript": LanguagePattern(r'(?:req\.(?:body|query|params)|request\.(?:body|query)).*?\.innerHTML\s*=', flags=re.DOTALL | re.MULTILINE),
        },
        fix_suggestion="Use textContent instead of innerHTML. Or sanitize with DOMPurify.",
        confidence=0.65,
        false_positive_patterns=[r'DOMPurify', r'sanitize', r'textContent'],
    ),
    TaintRule(
        id="TAINT-XSS-002", title="JS user input to document.write",
        description="User input passed to document.write enables XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={
            "javascript": LanguagePattern(r'document\.write(?:ln)?\s*\(\s*(?:req\.|request\.|params|query|input|user)'),
            "typescript": LanguagePattern(r'document\.write(?:ln)?\s*\(\s*(?:req\.|request\.|params|query|input|user)'),
        },
        fix_suggestion="Avoid document.write. Use DOM manipulation with textContent.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-XSS-003", title="JS user input to outerHTML",
        description="User input assigned to outerHTML enables XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={
            "javascript": LanguagePattern(r'\.outerHTML\s*=\s*(?:req\.|request\.|params|query|input|user)'),
            "typescript": LanguagePattern(r'\.outerHTML\s*=\s*(?:req\.|request\.|params|query|input|user)'),
        },
        fix_suggestion="Avoid direct outerHTML assignment with user data. Sanitize input first.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-XSS-004", title="JS insertAdjacentHTML with user input",
        description="insertAdjacentHTML with user input enables XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={
            "javascript": LanguagePattern(r'\.insertAdjacentHTML\s*\(\s*[^,]+,\s*(?:req\.|request\.|params|query|input|user)'),
            "typescript": LanguagePattern(r'\.insertAdjacentHTML\s*\(\s*[^,]+,\s*(?:req\.|request\.|params|query|input|user)'),
        },
        fix_suggestion="Use insertAdjacentText or sanitize HTML with DOMPurify.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-XSS-005", title="JS res.send with user input",
        description="Express res.send/res.end with user input in HTML response enables XSS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={
            "javascript": LanguagePattern(r'res\.(?:send|end|write)\s*\(\s*(?:req\.|request\.(?:body|query|params))'),
            "typescript": LanguagePattern(r'res\.(?:send|end|write)\s*\(\s*(?:req\.|request\.(?:body|query|params))'),
        },
        fix_suggestion="Sanitize output. Set Content-Type to application/json for API responses.",
        confidence=0.65,
        false_positive_patterns=[r'json\(\)', r'Content-Type.*application/json'],
    ),
    TaintRule(
        id="TAINT-XSS-006", title="JS template literal in response",
        description="Template literal with user input in HTML response enables XSS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={
            "javascript": LanguagePattern(r'res\.send\s*\(\s*`.*<.*\$\{.*req\.'),
            "typescript": LanguagePattern(r'res\.send\s*\(\s*`.*<.*\$\{.*req\.'),
        },
        fix_suggestion="Use a template engine with auto-escaping instead of template literals for HTML.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-XSS-007", title="Python render with user input",
        description="Flask/Django render with unsanitized user data enables XSS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={"python": LanguagePattern(r'render_template_string\s*\(\s*(?:request|f["\']|.*\.format)')},
        fix_suggestion="Use render_template with file templates. Jinja2 auto-escapes by default.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-XSS-008", title="Python Markup with user input",
        description="Markup() or mark_safe() with user data disables auto-escaping, enabling XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"python": LanguagePattern(r'(?:Markup|mark_safe)\s*\(\s*(?:request|user|input|f["\']|.*\.format\()')},
        fix_suggestion="Use Markup.escape() on user input. Or let the template engine auto-escape.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-XSS-009", title="Python Response with user data",
        description="Direct HTTP response with user data without escaping enables XSS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={"python": LanguagePattern(r'(?:HttpResponse|Response|make_response)\s*\(\s*(?:request|user|input|f["\'])')},
        fix_suggestion="Use template rendering with auto-escape. Or html.escape() for direct responses.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-XSS-010", title="Python format string in template",
        description="Python format string used as template with user data enables XSS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={"python": LanguagePattern(r'(?:return|response)\s*.*f["\']<.*\{.*request\.')},
        fix_suggestion="Use proper template engine instead of f-strings for HTML output.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-XSS-011", title="Java PrintWriter with user input",
        description="Servlet PrintWriter.print/println with user input enables XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"java": LanguagePattern(r'(?:getWriter|out)\.(?:print|println|write)\s*\([^)]*(?:request\.getParameter|getHeader|getAttribute)')},
        fix_suggestion="Encode output with OWASP encoder: Encode.forHtml(userInput).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-XSS-012", title="Java response output with concat",
        description="Response output stream with string concatenation containing user data.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"java": LanguagePattern(r'\.(?:print|println|write)\s*\(\s*["\']<.*["\']\s*\+.*request')},
        fix_suggestion="Use OWASP Java Encoder or template engine with auto-escaping.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-XSS-013", title="Java JSP expression with request",
        description="JSP expression outputting request parameters directly enables XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"java": LanguagePattern(r'<%=\s*request\.getParameter\s*\(')},
        fix_suggestion="Use JSTL <c:out> tag or fn:escapeXml() for output encoding.",
        confidence=0.9,
    ),
    TaintRule(
        id="TAINT-XSS-014", title="Java ModelAndView with user input",
        description="Spring ModelAndView with unsanitized user input enables XSS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={"java": LanguagePattern(r'(?:addObject|addAttribute)\s*\(\s*[^,]+,\s*(?:request\.getParameter|input)')},
        fix_suggestion="Sanitize data before adding to model. Use Thymeleaf's th:text for auto-escaping.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-XSS-015", title="PHP echo with user input",
        description="PHP echo/print with unsanitized user input enables XSS.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"php": LanguagePattern(r'(?:echo|print)\s+\$_(?:GET|POST|REQUEST)\s*\[')},
        fix_suggestion="Use htmlspecialchars(): echo htmlspecialchars($_GET['input'], ENT_QUOTES, 'UTF-8').",
        confidence=0.9,
    ),
    TaintRule(
        id="TAINT-XSS-016", title="PHP string interpolation with user input",
        description="PHP double-quoted string with user input variable in HTML output.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"php": LanguagePattern(r'echo\s+"[^"]*<[^"]*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Escape user input: htmlspecialchars($input, ENT_QUOTES, 'UTF-8').",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-XSS-017", title="Ruby ERB with unescaped user input",
        description="ERB <%== %> or raw() with user input bypasses escaping.",
        severity=Severity.HIGH, cwe_ids=["CWE-79"], category="xss",
        patterns={"ruby": LanguagePattern(r'(?:<%==|raw\s*\(\s*(?:params|request|input))')},
        fix_suggestion="Use <%= %> for auto-escaped output. Use sanitize() for safe HTML.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-XSS-018", title="Go template with unescaped user input",
        description="Go html/template used without auto-escaping or with template.HTML type.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-79"], category="xss",
        patterns={"go": LanguagePattern(r'template\.HTML\s*\(\s*(?:r\.FormValue|r\.URL\.Query|input)')},
        fix_suggestion="Use html/template (not text/template) which auto-escapes. Don't cast to template.HTML.",
        confidence=0.8,
    ),
]


# =============================================================================
# COMMAND INJECTION TAINT RULES (15)
# =============================================================================

CMD_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-CMD-001", title="Python os.system with user input",
        description="os.system() with user-derived data enables OS command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"python": LanguagePattern(r'os\.system\s*\(\s*(?:f["\']|["\'].*%|.*\.format\(|.*\+\s*(?:request|input|user))')},
        fix_suggestion="Use subprocess with list args: subprocess.run(['cmd', arg], shell=False).",
        confidence=0.8,
        false_positive_patterns=[r'shlex\.quote', r'pipes\.quote'],
    ),
    TaintRule(
        id="TAINT-CMD-002", title="Python subprocess with shell=True",
        description="subprocess with shell=True and user input enables command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"python": LanguagePattern(r'subprocess\.(?:call|run|Popen|check_output)\s*\([^)]*shell\s*=\s*True')},
        fix_suggestion="Use shell=False with list arguments: subprocess.run(['cmd', arg]).",
        confidence=0.75,
        false_positive_patterns=[r'shell\s*=\s*False'],
    ),
    TaintRule(
        id="TAINT-CMD-003", title="Python os.popen with user input",
        description="os.popen() with user-derived data enables command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"python": LanguagePattern(r'os\.popen\s*\(\s*(?:f["\']|["\'].*%|.*\.format\(|.*\+)')},
        fix_suggestion="Use subprocess.run() with shell=False and list arguments.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-CMD-004", title="Python eval/exec with user input",
        description="eval()/exec() with user input enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94", "CWE-78"], category="command_injection",
        patterns={"python": LanguagePattern(r'(?:eval|exec)\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Never use eval/exec with user input. Use ast.literal_eval for safe expression parsing.",
        confidence=0.85,
        false_positive_patterns=[r'ast\.literal_eval', r'# safe'],
    ),
    TaintRule(
        id="TAINT-CMD-005", title="Python compile with user input",
        description="compile() with user input enables code injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-94"], category="command_injection",
        patterns={"python": LanguagePattern(r'compile\s*\(\s*(?:request|input|user)')},
        fix_suggestion="Avoid compile() with user input. Use safe alternatives.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-CMD-006", title="JS child_process.exec with user input",
        description="child_process.exec with user input enables OS command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:exec|execSync)\s*\(\s*(?:`.*\$\{.*req\.|["\'].*\+.*req\.|req\.)'),
            "typescript": LanguagePattern(r'(?:exec|execSync)\s*\(\s*(?:`.*\$\{.*req\.|["\'].*\+.*req\.|req\.)'),
        },
        fix_suggestion="Use execFile with arguments array: execFile('cmd', [arg1, arg2]).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-CMD-007", title="JS child_process.spawn with shell",
        description="child_process.spawn with shell:true and user input enables injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-78"], category="command_injection",
        patterns={
            "javascript": LanguagePattern(r'spawn\s*\([^)]*(?:req\.|request\.|params|query|body).*shell\s*:\s*true'),
            "typescript": LanguagePattern(r'spawn\s*\([^)]*(?:req\.|request\.|params|query|body).*shell\s*:\s*true'),
        },
        fix_suggestion="Use spawn without shell: spawn('cmd', [arg1, arg2]).",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-CMD-008", title="JS eval with user input",
        description="eval() with user-controlled data enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="command_injection",
        patterns={
            "javascript": LanguagePattern(r'eval\s*\(\s*(?:req\.|request\.|params|query|body|input|user)'),
            "typescript": LanguagePattern(r'eval\s*\(\s*(?:req\.|request\.|params|query|body|input|user)'),
        },
        fix_suggestion="Never use eval with user input. Use JSON.parse for data, or a sandboxed VM.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CMD-009", title="JS vm.runInContext with user input",
        description="Node.js vm module with user input enables sandbox escape.",
        severity=Severity.HIGH, cwe_ids=["CWE-94"], category="command_injection",
        patterns={
            "javascript": LanguagePattern(r'vm\.(?:runIn(?:New|This)?Context|compileFunction|Script)\s*\(\s*(?:req\.|request\.|input|user)'),
            "typescript": LanguagePattern(r'vm\.(?:runIn(?:New|This)?Context|compileFunction|Script)\s*\(\s*(?:req\.|request\.|input|user)'),
        },
        fix_suggestion="Avoid vm module with user input. Use isolated-vm or worker threads.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-CMD-010", title="Java Runtime.exec with user input",
        description="Runtime.exec with user-controlled string enables command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"java": LanguagePattern(r'Runtime\.getRuntime\s*\(\s*\)\s*\.exec\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use ProcessBuilder with argument list: new ProcessBuilder('cmd', arg1, arg2).",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CMD-011", title="Java ProcessBuilder with user input",
        description="ProcessBuilder with user-controlled command string enables injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"java": LanguagePattern(r'ProcessBuilder\s*\(\s*(?:Arrays\.asList\s*\()?[^)]*(?:request\.getParameter|input)')},
        fix_suggestion="Validate and allowlist command arguments. Never construct commands from user input.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-CMD-012", title="Java ScriptEngine eval with input",
        description="ScriptEngine.eval with user input enables code injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-94"], category="command_injection",
        patterns={"java": LanguagePattern(r'(?:scriptEngine|engine)\.eval\s*\(\s*(?:request|input|param)')},
        fix_suggestion="Avoid eval with user input. Use Nashorn/GraalJS with sandboxing if needed.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CMD-013", title="PHP system/exec with user input",
        description="PHP shell functions with user input enable command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"php": LanguagePattern(r'(?:system|exec|passthru|shell_exec|popen|proc_open)\s*\([^)]*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Use escapeshellarg() and escapeshellcmd(). Or avoid shell commands entirely.",
        confidence=0.9,
        false_positive_patterns=[r'escapeshellarg', r'escapeshellcmd'],
    ),
    TaintRule(
        id="TAINT-CMD-014", title="Ruby system/exec with interpolation",
        description="Ruby shell execution with string interpolation enables command injection.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"ruby": LanguagePattern(r'(?:system|exec|`|%x)\s*["\'\(]?[^"\']*\#\{(?:params|request|input)')},
        fix_suggestion="Use array form: system('cmd', arg1, arg2) to avoid shell interpretation.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CMD-015", title="Go os/exec with user input",
        description="Go exec.Command with user input in arguments enables injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-78"], category="command_injection",
        patterns={"go": LanguagePattern(r'exec\.Command\s*\(\s*(?:r\.FormValue|r\.URL\.Query|input|userInput)')},
        fix_suggestion="Validate and allowlist commands. Use separate args: exec.Command('cmd', arg1, arg2).",
        confidence=0.8,
    ),
]


# =============================================================================
# PATH TRAVERSAL TAINT RULES (12)
# =============================================================================

PATH_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-PATH-001", title="Python open with user path",
        description="open() with user-controlled path enables arbitrary file read/write.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"python": LanguagePattern(r'open\s*\(\s*(?:f["\'][^"\']*\{|[^)]*(?:request|input|user|params))')},
        fix_suggestion="Use os.path.basename() and validate against allowed directories.",
        confidence=0.7,
        false_positive_patterns=[r'os\.path\.basename', r'secure_filename', r'\.resolve\(\)'],
    ),
    TaintRule(
        id="TAINT-PATH-002", title="Python pathlib with user input",
        description="Path operations with user input enable directory traversal.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"python": LanguagePattern(r'Path\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Resolve path and verify it's within allowed directory: path.resolve().relative_to(base).",
        confidence=0.65,
        false_positive_patterns=[r'\.resolve\(\)', r'\.relative_to\('],
    ),
    TaintRule(
        id="TAINT-PATH-003", title="Python os.path.join with user input",
        description="os.path.join with user input can be bypassed with absolute paths.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"python": LanguagePattern(r'os\.path\.join\s*\([^)]*(?:request|input|user)')},
        fix_suggestion="Validate basename only: os.path.join(base, os.path.basename(user_input)).",
        confidence=0.6,
        false_positive_patterns=[r'os\.path\.basename'],
    ),
    TaintRule(
        id="TAINT-PATH-004", title="Python shutil with user path",
        description="shutil operations with user-controlled paths enable file manipulation.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"python": LanguagePattern(r'shutil\.(?:copy|move|rmtree|copytree)\s*\([^)]*(?:request|input|user)')},
        fix_suggestion="Validate and restrict paths to allowed directories.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-PATH-005", title="JS fs operations with user input",
        description="Node.js fs module operations with user-controlled paths enable traversal.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={
            "javascript": LanguagePattern(r'fs\.(?:readFile|writeFile|readFileSync|writeFileSync|unlink|rmdir|mkdir|access|stat)\s*(?:Sync)?\s*\([^)]*(?:req\.|request\.|params|query)'),
            "typescript": LanguagePattern(r'fs\.(?:readFile|writeFile|readFileSync|writeFileSync|unlink|rmdir|mkdir|access|stat)\s*(?:Sync)?\s*\([^)]*(?:req\.|request\.|params|query)'),
        },
        fix_suggestion="Use path.resolve() and verify within allowed directory.",
        confidence=0.75,
        false_positive_patterns=[r'path\.resolve', r'path\.normalize', r'\.startsWith\('],
    ),
    TaintRule(
        id="TAINT-PATH-006", title="JS path.join with user input",
        description="path.join with user input can be bypassed with ../ sequences.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={
            "javascript": LanguagePattern(r'path\.join\s*\([^)]*(?:req\.|request\.|params|query)'),
            "typescript": LanguagePattern(r'path\.join\s*\([^)]*(?:req\.|request\.|params|query)'),
        },
        fix_suggestion="Use path.resolve() then verify result starts with allowed base directory.",
        confidence=0.6,
        false_positive_patterns=[r'path\.basename', r'\.startsWith\('],
    ),
    TaintRule(
        id="TAINT-PATH-007", title="JS Express sendFile with user path",
        description="res.sendFile with user-controlled path enables arbitrary file read.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={
            "javascript": LanguagePattern(r'res\.sendFile\s*\(\s*(?:req\.|request\.|params|query|path\.join.*req\.)'),
            "typescript": LanguagePattern(r'res\.sendFile\s*\(\s*(?:req\.|request\.|params|query|path\.join.*req\.)'),
        },
        fix_suggestion="Use res.sendFile with root option: res.sendFile(filename, { root: publicDir }).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-PATH-008", title="JS Express static with user input",
        description="express.static with user-controlled directory enables directory traversal.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={
            "javascript": LanguagePattern(r'express\.static\s*\(\s*(?:req\.|request\.|process\.env)'),
            "typescript": LanguagePattern(r'express\.static\s*\(\s*(?:req\.|request\.|process\.env)'),
        },
        fix_suggestion="Use fixed, validated directory paths for express.static.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-PATH-009", title="Java File with user input",
        description="Java File constructor with user-controlled path enables traversal.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"java": LanguagePattern(r'new\s+File\s*\([^)]*(?:request\.getParameter|getHeader|input)')},
        fix_suggestion="Canonicalize and validate: file.getCanonicalPath().startsWith(baseDir).",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-PATH-010", title="Java Files/Paths with user input",
        description="Java NIO Paths/Files with user input enables path traversal.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"java": LanguagePattern(r'(?:Paths\.get|Files\.(?:read|write|delete|copy|move))\s*\([^)]*(?:request|input|param)')},
        fix_suggestion="Normalize path and verify within allowed directory using toRealPath().",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-PATH-011", title="PHP file operations with user input",
        description="PHP file functions with user-controlled paths enable LFI/RFI.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-22", "CWE-98"], category="path_traversal",
        patterns={"php": LanguagePattern(r'(?:file_get_contents|fopen|readfile|include|require)(?:_once)?\s*\([^)]*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Use basename() and realpath(). Never include files based on user input.",
        confidence=0.85,
        false_positive_patterns=[r'basename', r'realpath'],
    ),
    TaintRule(
        id="TAINT-PATH-012", title="Go file operations with user input",
        description="Go os/ioutil file operations with user input enable path traversal.",
        severity=Severity.HIGH, cwe_ids=["CWE-22"], category="path_traversal",
        patterns={"go": LanguagePattern(r'(?:os\.(?:Open|Create|Remove|ReadFile)|ioutil\.(?:ReadFile|WriteFile))\s*\(\s*(?:r\.FormValue|r\.URL\.Query|filepath\.Join.*r\.)')},
        fix_suggestion="Use filepath.Clean() and verify path is within allowed directory.",
        confidence=0.75,
    ),
]


# =============================================================================
# DESERIALIZATION TAINT RULES (10)
# =============================================================================

DESER_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-DESER-001", title="Python pickle with user data",
        description="pickle.loads/load with user-controlled data enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"python": LanguagePattern(r'pickle\.(?:loads?|Unpickler)\s*\(\s*(?:request|input|user|data)')},
        fix_suggestion="Never unpickle untrusted data. Use JSON or other safe serialization formats.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-DESER-002", title="Python yaml.load without SafeLoader",
        description="yaml.load without SafeLoader enables arbitrary code execution.",
        severity=Severity.HIGH, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"python": LanguagePattern(r'yaml\.load\s*\(\s*(?:request|input|user|data|open)')},
        fix_suggestion="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader).",
        confidence=0.8,
        false_positive_patterns=[r'SafeLoader', r'safe_load'],
    ),
    TaintRule(
        id="TAINT-DESER-003", title="Python marshal with user data",
        description="marshal.loads with untrusted data can cause crashes or code execution.",
        severity=Severity.HIGH, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"python": LanguagePattern(r'marshal\.loads?\s*\(\s*(?:request|input|user|data)')},
        fix_suggestion="Avoid marshal for untrusted data. Use JSON or msgpack.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-DESER-004", title="Java ObjectInputStream with user data",
        description="ObjectInputStream.readObject with untrusted data enables RCE via gadget chains.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"java": LanguagePattern(r'ObjectInputStream\s*\([^)]*(?:request|input|socket|stream)')},
        fix_suggestion="Use ObjectInputFilter or avoid Java serialization. Use JSON/protobuf instead.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-DESER-005", title="Java XMLDecoder with user data",
        description="XMLDecoder with untrusted input enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"java": LanguagePattern(r'XMLDecoder\s*\(\s*(?:request|input|new\s+BufferedInputStream)')},
        fix_suggestion="Avoid XMLDecoder with untrusted input. Use JAXB or other safe XML parsers.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-DESER-006", title="Java XStream with user data",
        description="XStream deserialization without type restrictions enables RCE.",
        severity=Severity.HIGH, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"java": LanguagePattern(r'xstream\.fromXML\s*\(\s*(?:request|input|body)')},
        fix_suggestion="Configure XStream security: xstream.addPermission(NoTypePermission.NONE).",
        confidence=0.8,
        false_positive_patterns=[r'addPermission', r'allowTypes'],
    ),
    TaintRule(
        id="TAINT-DESER-007", title="PHP unserialize with user data",
        description="PHP unserialize with user-controlled data enables code execution via magic methods.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"php": LanguagePattern(r'unserialize\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)')},
        fix_suggestion="Use json_decode() instead. If unserialize needed, use allowed_classes option.",
        confidence=0.9,
    ),
    TaintRule(
        id="TAINT-DESER-008", title="PHP unserialize from database/file",
        description="PHP unserialize from database or file that may contain user data.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"php": LanguagePattern(r'unserialize\s*\(\s*(?:\$row|\$data|\$result|file_get_contents)')},
        fix_suggestion="Use json_decode() or set allowed_classes: unserialize($data, ['allowed_classes' => false]).",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-DESER-009", title="JS JSON.parse with eval-like usage",
        description="Deserializing user data and using it in eval-like context.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-502"], category="deserialization",
        patterns={
            "javascript": LanguagePattern(r'JSON\.parse\s*\(\s*(?:req\.|request\.).*?(?:eval|Function|setTimeout|setInterval)\s*\(', flags=re.DOTALL | re.MULTILINE),
            "typescript": LanguagePattern(r'JSON\.parse\s*\(\s*(?:req\.|request\.).*?(?:eval|Function|setTimeout|setInterval)\s*\(', flags=re.DOTALL | re.MULTILINE),
        },
        fix_suggestion="Validate parsed data structure. Never pass deserialized data to eval.",
        confidence=0.6,
    ),
    TaintRule(
        id="TAINT-DESER-010", title="C# BinaryFormatter deserialize",
        description="BinaryFormatter.Deserialize with untrusted data enables RCE.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-502"], category="deserialization",
        patterns={"csharp": LanguagePattern(r'BinaryFormatter\s*\(\s*\).*?\.Deserialize\s*\(', flags=re.DOTALL | re.MULTILINE)},
        fix_suggestion="Use System.Text.Json or DataContractSerializer instead of BinaryFormatter.",
        confidence=0.85,
    ),
]


# =============================================================================
# SSRF TAINT RULES (10)
# =============================================================================

SSRF_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-SSRF-001", title="Python requests with user URL",
        description="Python requests library with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"python": LanguagePattern(r'requests\.(?:get|post|put|delete|head|patch)\s*\(\s*(?:request|input|user|f["\']|.*\.format\()')},
        fix_suggestion="Validate URL against allowlist. Block private/internal IP ranges.",
        confidence=0.75,
        false_positive_patterns=[r'validate_url', r'allowlist', r'whitelist'],
    ),
    TaintRule(
        id="TAINT-SSRF-002", title="Python urllib with user URL",
        description="urllib.request with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"python": LanguagePattern(r'urllib\.request\.(?:urlopen|urlretrieve|Request)\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Validate URL against allowlist. Resolve DNS and block internal IPs.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SSRF-003", title="Python httpx/aiohttp with user URL",
        description="HTTP client with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"python": LanguagePattern(r'(?:httpx|aiohttp)\.(?:get|post|request|ClientSession)\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Validate URL against allowlist. Block private/internal IP ranges.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-SSRF-004", title="JS fetch/axios with user URL",
        description="HTTP request with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={
            "javascript": LanguagePattern(r'(?:fetch|axios\.(?:get|post|put|delete)|http\.(?:get|request))\s*\(\s*(?:req\.|request\.|params|query|input|user|`.*\$\{.*req\.)'),
            "typescript": LanguagePattern(r'(?:fetch|axios\.(?:get|post|put|delete)|http\.(?:get|request))\s*\(\s*(?:req\.|request\.|params|query|input|user|`.*\$\{.*req\.)'),
        },
        fix_suggestion="Validate URL against allowlist. Use URL parser to block internal addresses.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-SSRF-005", title="JS got/superagent with user URL",
        description="HTTP client library with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={
            "javascript": LanguagePattern(r'(?:got|superagent|needle|request)\s*(?:\.\w+)?\s*\(\s*(?:req\.|request\.|params|query|input|user)'),
            "typescript": LanguagePattern(r'(?:got|superagent|needle|request)\s*(?:\.\w+)?\s*\(\s*(?:req\.|request\.|params|query|input|user)'),
        },
        fix_suggestion="Validate URL against allowlist before making request.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-SSRF-006", title="JS URL redirect with user input",
        description="URL constructor/parse with user input may be used for SSRF.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-918"], category="ssrf",
        patterns={
            "javascript": LanguagePattern(r'new\s+URL\s*\(\s*(?:req\.|request\.|params|query)'),
            "typescript": LanguagePattern(r'new\s+URL\s*\(\s*(?:req\.|request\.|params|query)'),
        },
        fix_suggestion="Validate constructed URL hostname against allowlist.",
        confidence=0.6,
    ),
    TaintRule(
        id="TAINT-SSRF-007", title="Java HttpClient with user URL",
        description="Java HTTP client with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"java": LanguagePattern(r'(?:HttpClient|RestTemplate|WebClient).*(?:URI\.create|new\s+URL)\s*\(\s*(?:request|input|param)')},
        fix_suggestion="Validate URL against allowlist. Block internal/private addresses.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SSRF-008", title="Java URLConnection with user URL",
        description="URLConnection with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"java": LanguagePattern(r'new\s+URL\s*\(\s*(?:request|input|param).*\.openConnection\s*\(')},
        fix_suggestion="Validate URL before opening connection. Block internal IP ranges.",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-SSRF-009", title="PHP cURL with user URL",
        description="PHP cURL with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"php": LanguagePattern(r'curl_setopt\s*\([^)]*CURLOPT_URL[^)]*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Validate URL against allowlist. Block private/internal IP ranges.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-SSRF-010", title="Ruby HTTP with user URL",
        description="Ruby HTTP library with user-controlled URL enables SSRF.",
        severity=Severity.HIGH, cwe_ids=["CWE-918"], category="ssrf",
        patterns={"ruby": LanguagePattern(r'(?:Net::HTTP|URI\.parse|open-uri|Faraday|HTTParty).*(?:params|request|input)')},
        fix_suggestion="Validate URL against allowlist. Resolve and block internal IPs.",
        confidence=0.65,
    ),
]


# =============================================================================
# LDAP/NoSQL TAINT RULES (8)
# =============================================================================

LDAP_NOSQL_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-LDAP-001", title="Python LDAP with user input",
        description="LDAP query with user input enables LDAP injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-90"], category="ldap_injection",
        patterns={"python": LanguagePattern(r'(?:ldap|ldap3)\..*search\s*\([^)]*(?:request|input|user|f["\'])')},
        fix_suggestion="Use LDAP filter escaping: ldap.filter.escape_filter_chars(user_input).",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-LDAP-002", title="Java LDAP with user input",
        description="Java LDAP search with user input enables LDAP injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-90"], category="ldap_injection",
        patterns={"java": LanguagePattern(r'(?:dirContext|ctx)\.search\s*\([^)]*(?:request|input|param).*\+')},
        fix_suggestion="Escape LDAP special characters in user input before building filter.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-LDAP-003", title="C# LDAP with user input",
        description="C# DirectorySearcher with user input enables LDAP injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-90"], category="ldap_injection",
        patterns={"csharp": LanguagePattern(r'DirectorySearcher.*Filter\s*=\s*[^;]*(?:Request|input|user)\s*\+')},
        fix_suggestion="Escape LDAP special characters. Use parameterized LDAP search.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-LDAP-004", title="PHP LDAP with user input",
        description="PHP ldap_search with user input in filter enables LDAP injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-90"], category="ldap_injection",
        patterns={"php": LanguagePattern(r'ldap_search\s*\([^)]*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Use ldap_escape() to sanitize user input in LDAP filters.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-NOSQL-001", title="Python MongoDB with user input",
        description="MongoDB query with user input enables NoSQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-943"], category="nosql_injection",
        patterns={"python": LanguagePattern(r'\.(?:find|find_one|update|delete)\s*\(\s*(?:request\.(?:json|form|args)|json\.loads)')},
        fix_suggestion="Validate query structure. Strip $-prefix keys from user input.",
        confidence=0.75,
        false_positive_patterns=[r'sanitize', r'validate'],
    ),
    TaintRule(
        id="TAINT-NOSQL-002", title="JS MongoDB with user input",
        description="MongoDB query with request data enables NoSQL injection via $gt/$ne operators.",
        severity=Severity.HIGH, cwe_ids=["CWE-943"], category="nosql_injection",
        patterns={
            "javascript": LanguagePattern(r'\.(?:find|findOne|findOneAndUpdate|deleteOne|updateOne)\s*\(\s*(?:req\.(?:body|query|params)|JSON\.parse)'),
            "typescript": LanguagePattern(r'\.(?:find|findOne|findOneAndUpdate|deleteOne|updateOne)\s*\(\s*(?:req\.(?:body|query|params)|JSON\.parse)'),
        },
        fix_suggestion="Use mongo-sanitize or manually strip $-prefix keys from input.",
        confidence=0.75,
        false_positive_patterns=[r'sanitize', r'mongo-sanitize'],
    ),
    TaintRule(
        id="TAINT-NOSQL-003", title="Java MongoDB with user input",
        description="Java MongoDB driver with user input in filter enables NoSQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-943"], category="nosql_injection",
        patterns={"java": LanguagePattern(r'(?:Filters|BasicDBObject|Document).*(?:request|input|param)')},
        fix_suggestion="Validate query structure. Use typed filter builders.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-NOSQL-004", title="PHP MongoDB with user input",
        description="PHP MongoDB query with user input enables NoSQL injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-943"], category="nosql_injection",
        patterns={"php": LanguagePattern(r'->(?:find|findOne|aggregate)\s*\(\s*(?:\$_(?:GET|POST|REQUEST)|json_decode)')},
        fix_suggestion="Validate query structure. Strip $-prefix keys from user input.",
        confidence=0.75,
    ),
]


# =============================================================================
# CODE INJECTION TAINT RULES (10)
# =============================================================================

CODE_INJECTION_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-CODE-001", title="Python eval with formatted input",
        description="eval() with formatted user input enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"python": LanguagePattern(r'eval\s*\(\s*(?:f["\']|.*\.format\(|.*%|request|input|user)')},
        fix_suggestion="Use ast.literal_eval() for safe expression parsing. Avoid eval entirely.",
        confidence=0.85,
        false_positive_patterns=[r'ast\.literal_eval', r'# safe', r'# nosec'],
    ),
    TaintRule(
        id="TAINT-CODE-002", title="Python exec with user input",
        description="exec() with user input enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"python": LanguagePattern(r'exec\s*\(\s*(?:request|input|user|f["\']|compile)')},
        fix_suggestion="Never exec user input. Use safe alternatives or sandboxed execution.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CODE-003", title="Python importlib with user input",
        description="Dynamic import with user-controlled module name enables code execution.",
        severity=Severity.HIGH, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"python": LanguagePattern(r'(?:importlib\.import_module|__import__)\s*\(\s*(?:request|input|user)')},
        fix_suggestion="Use an allowlist of importable modules. Never import user-specified modules.",
        confidence=0.8,
    ),
    TaintRule(
        id="TAINT-CODE-004", title="Python pickle code execution",
        description="Pickle deserialization with __reduce__ enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"python": LanguagePattern(r'pickle\.(?:loads?|Unpickler)\s*\(')},
        fix_suggestion="Never unpickle untrusted data. Use JSON or MessagePack.",
        confidence=0.7,
        false_positive_patterns=[r'trusted', r'internal', r'# nosec'],
    ),
    TaintRule(
        id="TAINT-CODE-005", title="JS eval with user input",
        description="eval() with user-controlled data enables arbitrary code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={
            "javascript": LanguagePattern(r'eval\s*\(\s*(?:req\.|request\.|input|user|`.*\$\{)'),
            "typescript": LanguagePattern(r'eval\s*\(\s*(?:req\.|request\.|input|user|`.*\$\{)'),
        },
        fix_suggestion="Never eval user input. Use JSON.parse for data. Use VM2 for sandboxed execution.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CODE-006", title="JS new Function with user input",
        description="new Function() with user data creates executable code.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={
            "javascript": LanguagePattern(r'new\s+Function\s*\(\s*(?:req\.|request\.|input|user|`.*\$\{)'),
            "typescript": LanguagePattern(r'new\s+Function\s*\(\s*(?:req\.|request\.|input|user|`.*\$\{)'),
        },
        fix_suggestion="Avoid new Function with user input. Use safe expression parsers.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CODE-007", title="JS setTimeout/setInterval with string",
        description="setTimeout/setInterval with string argument executes as eval.",
        severity=Severity.HIGH, cwe_ids=["CWE-94"], category="code_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:setTimeout|setInterval)\s*\(\s*(?:req\.|request\.|input|user|["\'].*\+)'),
            "typescript": LanguagePattern(r'(?:setTimeout|setInterval)\s*\(\s*(?:req\.|request\.|input|user|["\'].*\+)'),
        },
        fix_suggestion="Use function reference instead of string: setTimeout(() => ..., delay).",
        confidence=0.75,
    ),
    TaintRule(
        id="TAINT-CODE-008", title="Java ScriptEngine with user input",
        description="Java ScriptEngine eval with user input enables code injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"java": LanguagePattern(r'(?:ScriptEngine|engine)\.eval\s*\(\s*(?:request|input|param)')},
        fix_suggestion="Avoid eval with user input. Use sandboxed script engines.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CODE-009", title="Java SpEL with user input",
        description="Spring Expression Language with user input enables RCE.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"java": LanguagePattern(r'parseExpression\s*\(\s*(?:request|input|param)')},
        fix_suggestion="Never parse user input as SpEL. Use SimpleEvaluationContext for restrictions.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-CODE-010", title="PHP preg_replace /e with user input",
        description="PHP preg_replace with /e modifier and user input enables code execution.",
        severity=Severity.CRITICAL, cwe_ids=["CWE-94"], category="code_injection",
        patterns={"php": LanguagePattern(r'preg_replace\s*\(\s*["\'][^"\']*\/e["\'].*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Use preg_replace_callback() instead of /e modifier.",
        confidence=0.9,
    ),
]


# =============================================================================
# LOG INJECTION TAINT RULES (8)
# =============================================================================

LOG_INJECTION_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-LOG-001", title="Python log with user input (format)",
        description="Logging user input with format strings enables log injection/forging.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-117"], category="log_injection",
        patterns={"python": LanguagePattern(r'(?:logging|logger)\.\w+\s*\(\s*f["\'][^"\']*\{.*request')},
        fix_suggestion="Use logging parameters: logger.info('User: %s', user_input) instead of f-strings.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-LOG-002", title="Python log with unsanitized input",
        description="Logging unsanitized user input enables log injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-117"], category="log_injection",
        patterns={"python": LanguagePattern(r'(?:logging|logger)\.\w+\s*\(\s*["\'].*["\']\s*%\s*(?:request|input)')},
        fix_suggestion="Sanitize log data: remove newlines/CRLF before logging user input.",
        confidence=0.6,
    ),
    TaintRule(
        id="TAINT-LOG-003", title="Python print with user input",
        description="Print statements with user input may end up in logs.",
        severity=Severity.LOW, cwe_ids=["CWE-117"], category="log_injection",
        patterns={"python": LanguagePattern(r'print\s*\(\s*(?:f["\'][^"\']*\{.*request|.*request\.)')},
        fix_suggestion="Use proper logging instead of print. Sanitize user input.",
        confidence=0.5,
    ),
    TaintRule(
        id="TAINT-LOG-004", title="JS console.log with user input",
        description="Logging user input to console without sanitization.",
        severity=Severity.LOW, cwe_ids=["CWE-117"], category="log_injection",
        patterns={
            "javascript": LanguagePattern(r'console\.(?:log|warn|error|info)\s*\(\s*(?:req\.(?:body|query|params)|`.*\$\{.*req\.)'),
            "typescript": LanguagePattern(r'console\.(?:log|warn|error|info)\s*\(\s*(?:req\.(?:body|query|params)|`.*\$\{.*req\.)'),
        },
        fix_suggestion="Sanitize user input before logging. Use structured logging libraries.",
        confidence=0.5,
    ),
    TaintRule(
        id="TAINT-LOG-005", title="JS winston/pino with user input",
        description="Production logger with unsanitized user input.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-117"], category="log_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:winston|pino|bunyan|log4js).*\.(?:info|warn|error)\s*\(\s*(?:req\.(?:body|query)|`.*\$\{)'),
            "typescript": LanguagePattern(r'(?:winston|pino|bunyan|log4js).*\.(?:info|warn|error)\s*\(\s*(?:req\.(?:body|query)|`.*\$\{)'),
        },
        fix_suggestion="Use structured logging with separate fields for user data.",
        confidence=0.6,
    ),
    TaintRule(
        id="TAINT-LOG-006", title="JS morgan custom format with user input",
        description="Morgan HTTP logger with custom format including user input.",
        severity=Severity.LOW, cwe_ids=["CWE-117"], category="log_injection",
        patterns={
            "javascript": LanguagePattern(r'morgan\s*\(\s*(?:function|\([^)]*\)\s*=>)'),
            "typescript": LanguagePattern(r'morgan\s*\(\s*(?:function|\([^)]*\)\s*=>)'),
        },
        fix_suggestion="Use predefined morgan formats. Sanitize custom tokens.",
        confidence=0.5,
    ),
    TaintRule(
        id="TAINT-LOG-007", title="Java log with user input",
        description="Java logger with user-controlled data enables log injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-117"], category="log_injection",
        patterns={"java": LanguagePattern(r'(?:log|logger|LOG)\.(?:info|warn|error|debug)\s*\([^)]*(?:request\.getParameter|\.getHeader\()')},
        fix_suggestion="Sanitize log data. Use parameterized logging: logger.info('User: {}', sanitize(input)).",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-LOG-008", title="Java log4j JNDI lookup",
        description="Log4j with user input may trigger JNDI lookup (Log4Shell - CVE-2021-44228).",
        severity=Severity.CRITICAL, cwe_ids=["CWE-917", "CWE-20"], category="log_injection",
        patterns={"java": LanguagePattern(r'(?:log|logger)\.(?:info|error|warn|debug|fatal)\s*\(\s*(?:request\.getParameter|request\.getHeader|input)')},
        fix_suggestion="Upgrade log4j to 2.17+. Set -Dlog4j2.formatMsgNoLookups=true. Sanitize all logged input.",
        confidence=0.6,
    ),
]


# =============================================================================
# HEADER INJECTION TAINT RULES (8)
# =============================================================================

HEADER_INJECTION_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-HDR-001", title="Python response header with user input",
        description="Setting response headers with user input enables header injection / HTTP response splitting.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-113"], category="header_injection",
        patterns={"python": LanguagePattern(r'(?:response|headers)\s*\[\s*["\'][^"\']+["\']\s*\]\s*=\s*(?:request|input|user)')},
        fix_suggestion="Strip CRLF characters from header values. Validate against expected format.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-HDR-002", title="Python Set-Cookie with user input",
        description="Setting cookies with user-controlled values enables header injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-113"], category="header_injection",
        patterns={"python": LanguagePattern(r'(?:set_cookie|response\.cookies)\s*\([^)]*(?:request|input|user)')},
        fix_suggestion="Validate and sanitize cookie values. Remove CRLF and special characters.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-HDR-003", title="Python redirect with user input",
        description="Redirect with user-controlled URL enables header injection and open redirect.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-601", "CWE-113"], category="header_injection",
        patterns={"python": LanguagePattern(r'redirect\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Validate redirect URL against allowlist of trusted domains.",
        confidence=0.7,
        false_positive_patterns=[r'url_has_allowed_host', r'is_safe_url', r'validate_url'],
    ),
    TaintRule(
        id="TAINT-HDR-004", title="JS response header with user input",
        description="Setting HTTP headers with user input enables header injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-113"], category="header_injection",
        patterns={
            "javascript": LanguagePattern(r'res\.(?:setHeader|header|set)\s*\(\s*[^,]+,\s*(?:req\.|request\.|params|query|input)'),
            "typescript": LanguagePattern(r'res\.(?:setHeader|header|set)\s*\(\s*[^,]+,\s*(?:req\.|request\.|params|query|input)'),
        },
        fix_suggestion="Validate header values. Strip CRLF characters from user input.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-HDR-005", title="JS cookie with user input",
        description="Setting cookies with user-controlled values enables header injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-113"], category="header_injection",
        patterns={
            "javascript": LanguagePattern(r'res\.cookie\s*\(\s*[^,]+,\s*(?:req\.|request\.|params|query|input)'),
            "typescript": LanguagePattern(r'res\.cookie\s*\(\s*[^,]+,\s*(?:req\.|request\.|params|query|input)'),
        },
        fix_suggestion="Sanitize cookie values. Use signed/encrypted cookies.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-HDR-006", title="JS Location header with user input",
        description="Setting Location header with user input enables open redirect.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-601"], category="header_injection",
        patterns={
            "javascript": LanguagePattern(r'res\.(?:redirect|location)\s*\(\s*(?:req\.|request\.|params|query|input)'),
            "typescript": LanguagePattern(r'res\.(?:redirect|location)\s*\(\s*(?:req\.|request\.|params|query|input)'),
        },
        fix_suggestion="Validate redirect URL against allowlist.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-HDR-007", title="Java response header with user input",
        description="Setting response headers with user input in Java enables header injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-113"], category="header_injection",
        patterns={"java": LanguagePattern(r'(?:response|httpServletResponse)\.(?:setHeader|addHeader|sendRedirect)\s*\([^)]*(?:request|input|param)')},
        fix_suggestion="Validate and encode header values. Use OWASP encoder for header values.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-HDR-008", title="PHP header with user input",
        description="PHP header() with user input enables header injection / HTTP response splitting.",
        severity=Severity.HIGH, cwe_ids=["CWE-113"], category="header_injection",
        patterns={"php": LanguagePattern(r'header\s*\(\s*["\'][^"\']*["\']\s*\.\s*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Strip CRLF from user input: str_replace([\"\\r\", \"\\n\"], '', $input).",
        confidence=0.8,
    ),
]


# =============================================================================
# EMAIL INJECTION TAINT RULES (6)
# =============================================================================

EMAIL_INJECTION_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-EMAIL-001", title="Python smtplib with user input",
        description="SMTP email headers with user input enables email header injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-93"], category="email_injection",
        patterns={"python": LanguagePattern(r'(?:smtplib|MIMEText|MIMEMultipart|EmailMessage).*(?:request|input|user)')},
        fix_suggestion="Validate email addresses. Strip newlines from all header values.",
        confidence=0.6,
    ),
    TaintRule(
        id="TAINT-EMAIL-002", title="Python Django send_mail with user input",
        description="Django send_mail with user-controlled subject/from enables header injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-93"], category="email_injection",
        patterns={"python": LanguagePattern(r'send_mail\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Validate and sanitize email subjects and addresses. Strip CRLF characters.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-EMAIL-003", title="JS nodemailer with user input",
        description="Nodemailer with user-controlled headers enables email injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-93"], category="email_injection",
        patterns={
            "javascript": LanguagePattern(r'(?:transporter|mailer)\.sendMail\s*\(\s*\{[^}]*(?:req\.|request\.|input|user)'),
            "typescript": LanguagePattern(r'(?:transporter|mailer)\.sendMail\s*\(\s*\{[^}]*(?:req\.|request\.|input|user)'),
        },
        fix_suggestion="Validate email addresses and subjects. Strip newlines from headers.",
        confidence=0.6,
    ),
    TaintRule(
        id="TAINT-EMAIL-004", title="JS SendGrid with user input",
        description="SendGrid email with user-controlled fields enables injection.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-93"], category="email_injection",
        patterns={
            "javascript": LanguagePattern(r'sgMail\.send\s*\(\s*\{[^}]*(?:req\.|request\.|input|user)'),
            "typescript": LanguagePattern(r'sgMail\.send\s*\(\s*\{[^}]*(?:req\.|request\.|input|user)'),
        },
        fix_suggestion="Validate email fields. Sanitize subject and body content.",
        confidence=0.55,
    ),
    TaintRule(
        id="TAINT-EMAIL-005", title="PHP mail with user input",
        description="PHP mail() with user-controlled headers enables email injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-93"], category="email_injection",
        patterns={"php": LanguagePattern(r'mail\s*\(\s*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Validate email addresses. Use PHPMailer or SwiftMailer for safe email sending.",
        confidence=0.85,
    ),
    TaintRule(
        id="TAINT-EMAIL-006", title="PHP additional headers with user input",
        description="PHP mail() additional_headers with user data enables header injection.",
        severity=Severity.HIGH, cwe_ids=["CWE-93"], category="email_injection",
        patterns={"php": LanguagePattern(r'mail\s*\([^)]*,[^)]*,[^)]*,\s*[^)]*\$_(?:GET|POST|REQUEST)')},
        fix_suggestion="Never put user input directly in email headers. Validate and sanitize.",
        confidence=0.8,
    ),
]


# =============================================================================
# REGEX INJECTION TAINT RULES (5)
# =============================================================================

REGEX_INJECTION_TAINT_RULES: List[TaintRule] = [
    TaintRule(
        id="TAINT-REGEX-001", title="Python re.compile with user pattern",
        description="re.compile with user-controlled pattern enables ReDoS attacks.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-1333"], category="regex_injection",
        patterns={"python": LanguagePattern(r're\.compile\s*\(\s*(?:request|input|user|f["\'])')},
        fix_suggestion="Validate regex complexity. Use re2 for safe regex or set timeout.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-REGEX-002", title="Python re.search/match with user pattern",
        description="regex functions with user-controlled pattern enable ReDoS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-1333"], category="regex_injection",
        patterns={"python": LanguagePattern(r're\.(?:search|match|findall|finditer|sub)\s*\(\s*(?:request|input|user)')},
        fix_suggestion="Escape user input with re.escape() or use fixed patterns.",
        confidence=0.65,
        false_positive_patterns=[r're\.escape'],
    ),
    TaintRule(
        id="TAINT-REGEX-003", title="JS RegExp with user pattern",
        description="new RegExp with user input enables ReDoS attacks.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-1333"], category="regex_injection",
        patterns={
            "javascript": LanguagePattern(r'new\s+RegExp\s*\(\s*(?:req\.|request\.|input|user|params|query)'),
            "typescript": LanguagePattern(r'new\s+RegExp\s*\(\s*(?:req\.|request\.|input|user|params|query)'),
        },
        fix_suggestion="Escape user input or use fixed patterns. Consider using RE2 for safe regex.",
        confidence=0.7,
    ),
    TaintRule(
        id="TAINT-REGEX-004", title="JS string.match/replace with user pattern",
        description="String regex methods with user pattern enable ReDoS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-1333"], category="regex_injection",
        patterns={
            "javascript": LanguagePattern(r'\.(?:match|replace|search|split)\s*\(\s*new\s+RegExp\s*\(\s*(?:req\.|request\.)'),
            "typescript": LanguagePattern(r'\.(?:match|replace|search|split)\s*\(\s*new\s+RegExp\s*\(\s*(?:req\.|request\.)'),
        },
        fix_suggestion="Use string methods like includes() or indexOf() instead of regex for user input.",
        confidence=0.65,
    ),
    TaintRule(
        id="TAINT-REGEX-005", title="Java Pattern.compile with user pattern",
        description="Java Pattern.compile with user input enables ReDoS.",
        severity=Severity.MEDIUM, cwe_ids=["CWE-1333"], category="regex_injection",
        patterns={"java": LanguagePattern(r'Pattern\.compile\s*\(\s*(?:request|input|param)')},
        fix_suggestion="Escape user input with Pattern.quote(). Or use fixed patterns.",
        confidence=0.7,
        false_positive_patterns=[r'Pattern\.quote'],
    ),
]


# =============================================================================
# COMBINED RULES
# =============================================================================

ALL_TAINT_RULES: List[TaintRule] = (
    SQL_TAINT_RULES +
    XSS_TAINT_RULES +
    CMD_TAINT_RULES +
    PATH_TAINT_RULES +
    DESER_TAINT_RULES +
    SSRF_TAINT_RULES +
    LDAP_NOSQL_TAINT_RULES +
    CODE_INJECTION_TAINT_RULES +
    LOG_INJECTION_TAINT_RULES +
    HEADER_INJECTION_TAINT_RULES +
    EMAIL_INJECTION_TAINT_RULES +
    REGEX_INJECTION_TAINT_RULES
)


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class ASTTaintTracker(BaseScanner):
    """
    Tracks tainted data from sources to sinks using dual approach:

    1. Python: Real AST-based taint tracking using Python's ast module (0.85 confidence)
    2. Other languages: Regex-based source-near-sink heuristics (0.6-0.7 confidence)

    Covers ~150 taint rules across SQL, XSS, CMD, Path, Deser, SSRF, LDAP, NoSQL,
    Code injection, Log injection, Header injection, Email injection, Regex injection.

    Multi-language: Python, JavaScript, TypeScript, Java, C#, PHP, Ruby, Go
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compiled_sanitizer_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in ALL_TAINT_RULES:
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

            # Compile sanitizer patterns
            self._compiled_sanitizer_patterns[rule.id] = []
            for san_pattern in rule.sanitizer_patterns:
                try:
                    self._compiled_sanitizer_patterns[rule.id].append(
                        re.compile(san_pattern, re.IGNORECASE)
                    )
                except re.error:
                    pass

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.AST_TAINT

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
        context_lines: str
    ) -> bool:
        """Check if match is a false positive."""
        full_text = matched_text + " " + context_lines

        # Check FP patterns
        for fp_pattern in self._compiled_fp_patterns.get(rule_id, []):
            if fp_pattern.search(full_text):
                return True

        # Check sanitizer patterns
        for san_pattern in self._compiled_sanitizer_patterns.get(rule_id, []):
            if san_pattern.search(full_text):
                return True

        return False

    # =========================================================================
    # PYTHON AST TAINT ANALYSIS
    # =========================================================================

    def _analyze_python_ast(
        self,
        content: str,
        file_path: Path,
    ) -> List[SecurityFinding]:
        """Analyze Python code using AST-based taint tracking."""
        findings = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        lines = content.split("\n")

        # Phase 1: Build function signatures
        function_sigs: Dict[str, FunctionSignature] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [arg.arg for arg in node.args.args]
                function_sigs[node.name] = FunctionSignature(
                    name=node.name,
                    parameters=params,
                )

        # Phase 2: Find taint sources (variable assignments from tainted data)
        taint_map: Dict[str, Set[str]] = {}  # var -> set of source types

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if RHS contains a taint source
                rhs_source = self._get_source_segment_safe(content, node.value)
                if rhs_source:
                    for source_pattern, source_type in PYTHON_TAINT_SOURCES:
                        if source_pattern in rhs_source:
                            for target in node.targets:
                                var_name = self._get_ast_name(target)
                                if var_name:
                                    if var_name not in taint_map:
                                        taint_map[var_name] = set()
                                    taint_map[var_name].add(source_type)

        # Phase 3: Propagate taint through assignments
        changed = True
        iterations = 0
        while changed and iterations < 50:
            changed = False
            iterations += 1
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    rhs_source = self._get_source_segment_safe(content, node.value)
                    if rhs_source:
                        for tainted_var in list(taint_map.keys()):
                            if tainted_var in rhs_source:
                                for target in node.targets:
                                    var_name = self._get_ast_name(target)
                                    if var_name and var_name not in taint_map:
                                        taint_map[var_name] = taint_map[tainted_var].copy()
                                        changed = True

        # Phase 4: Check sinks for tainted arguments
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_source = self._get_source_segment_safe(content, node)
                if not call_source:
                    continue

                for sink_pattern, cwe, category in PYTHON_TAINT_SINKS:
                    if sink_pattern not in call_source:
                        continue

                    # Check if any tainted variable appears in the call
                    for tainted_var, sources in taint_map.items():
                        if tainted_var in call_source:
                            # Check if sanitizer is present
                            context_start = max(0, node.lineno - 5)
                            context_end = min(len(lines), node.lineno + 3)
                            context = "\n".join(lines[context_start:context_end])

                            is_sanitized = any(
                                san in context for san in PYTHON_SANITIZERS
                            )
                            if is_sanitized:
                                continue

                            snippet_start = max(0, node.lineno - 2)
                            snippet_end = min(len(lines), node.lineno + 3)
                            snippet = "\n".join(lines[snippet_start:snippet_end])

                            finding = SecurityFinding(
                                id=f"ast-taint-{cwe}-{file_path}:{node.lineno}",
                                rule_id=f"TAINT-AST-{cwe}",
                                title=f"Tainted data flows to {sink_pattern}",
                                description=(
                                    f"Data from {', '.join(sources)} source(s) flows to dangerous sink "
                                    f"{sink_pattern} via variable '{tainted_var}'. "
                                    f"Cross-function taint tracking detected this data flow."
                                ),
                                severity=Severity.HIGH,
                                scanner=self.scanner_type,
                                location=Location(
                                    file_path=str(file_path),
                                    start_line=node.lineno,
                                    end_line=getattr(node, 'end_lineno', node.lineno),
                                    snippet=snippet,
                                ),
                                cwe_ids=[cwe],
                                category=category,
                                confidence=0.85,
                                tags={"lang:python", "ast_taint", category},
                            )

                            finding.suggested_fixes.append(
                                SuggestedFix(
                                    description=f"Sanitize '{tainted_var}' before passing to {sink_pattern}. "
                                    f"Use appropriate escaping for {category}."
                                )
                            )

                            findings.append(finding)
                            break  # One finding per sink call

        # Phase 5: Direct source-to-sink in same expression
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_source = self._get_source_segment_safe(content, node)
                if not call_source:
                    continue

                for sink_pattern, cwe, category in PYTHON_TAINT_SINKS:
                    if sink_pattern not in call_source:
                        continue

                    for source_pattern, source_type in PYTHON_TAINT_SOURCES:
                        if source_pattern in call_source:
                            # Direct source in sink
                            snippet_start = max(0, node.lineno - 2)
                            snippet_end = min(len(lines), node.lineno + 3)
                            snippet = "\n".join(lines[snippet_start:snippet_end])

                            # Check sanitizers
                            is_sanitized = any(san in call_source for san in PYTHON_SANITIZERS)
                            if is_sanitized:
                                continue

                            finding = SecurityFinding(
                                id=f"ast-taint-direct-{cwe}-{file_path}:{node.lineno}",
                                rule_id=f"TAINT-AST-DIRECT-{cwe}",
                                title=f"Direct tainted data in {sink_pattern}",
                                description=(
                                    f"Data from {source_type} source ({source_pattern}) is passed "
                                    f"directly to dangerous sink {sink_pattern}."
                                ),
                                severity=Severity.CRITICAL,
                                scanner=self.scanner_type,
                                location=Location(
                                    file_path=str(file_path),
                                    start_line=node.lineno,
                                    end_line=getattr(node, 'end_lineno', node.lineno),
                                    snippet=snippet,
                                ),
                                cwe_ids=[cwe],
                                category=category,
                                confidence=0.9,
                                tags={"lang:python", "ast_taint", "direct", category},
                            )

                            finding.suggested_fixes.append(
                                SuggestedFix(
                                    description=f"Never pass {source_type} data directly to {sink_pattern}. "
                                    f"Sanitize input appropriately for {category}."
                                )
                            )

                            findings.append(finding)
                            break

        return findings

    def _get_source_segment_safe(self, content: str, node: ast.AST) -> Optional[str]:
        """Safely get source segment for an AST node."""
        try:
            return ast.get_source_segment(content, node) or ""
        except (TypeError, ValueError):
            return ""

    def _get_ast_name(self, node: ast.AST) -> Optional[str]:
        """Get the name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_ast_name(node.value)}.{node.attr}" if self._get_ast_name(node.value) else node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_ast_name(node.value)
        return None

    # =========================================================================
    # MAIN SCAN METHOD
    # =========================================================================

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute taint tracking scan with dual approach."""
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

                # Python: Use AST-based taint tracking
                if language == "python":
                    ast_findings = self._analyze_python_ast(content, file_path)
                    findings.extend(ast_findings)

                # All languages: Apply regex-based taint rules
                for rule in ALL_TAINT_RULES:
                    compiled_pattern = self._compiled_patterns.get(rule.id, {}).get(language)
                    if not compiled_pattern:
                        continue

                    for match in compiled_pattern.finditer(content):
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet = "\n".join(lines[snippet_start:snippet_end])

                        if self._is_false_positive(rule.id, match.group(), snippet):
                            continue

                        # Adjust confidence for Python (AST provides better coverage)
                        confidence = rule.confidence
                        if language == "python":
                            confidence = min(confidence, 0.65)  # Lower for regex if AST already ran

                        finding = SecurityFinding(
                            id=f"taint-{rule.id}-{file_path}:{line_start}",
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
                            confidence=confidence,
                            tags={f"lang:{language}", "taint", rule.category},
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
        """Get summary of all taint rules."""
        categories = {}
        for rule in ALL_TAINT_RULES:
            if rule.category not in categories:
                categories[rule.category] = 0
            categories[rule.category] += 1

        cwe_coverage = set()
        for rule in ALL_TAINT_RULES:
            cwe_coverage.update(rule.cwe_ids)

        return {
            "total_rules": len(ALL_TAINT_RULES),
            "rules_by_category": categories,
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": sorted(cwe_coverage),
            "ast_languages": ["python"],
            "regex_languages": [l for l in SUPPORTED_LANGUAGES.keys() if l != "python"],
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_ast_taint_tracker() -> ASTTaintTracker:
    """Factory function to create AST taint tracker."""
    return ASTTaintTracker()
