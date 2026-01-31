"""
Framework Security Plugin - Framework-Specific Vulnerability Detection.

Fase 42: Detects framework-specific security misconfigurations and vulnerabilities
across 7 major web frameworks:

- Django (15 rules): raw SQL, mark_safe, CSRF exempt, DEBUG mode
- Flask (10 rules): template injection, debug mode, session security
- Express (12 rules): helmet, CORS, CSRF, cookie security
- Spring (15 rules): SpEL injection, CSRF disable, actuator exposure
- Rails (10 rules): find_by_sql, html_safe, mass assignment
- Laravel (12 rules): DB::raw, Blade unescaped, guarded empty
- ASP.NET (10 rules): SqlCommand concat, Html.Raw, validateRequest

Total: 84 rules with framework auto-detection
Confidence: 0.75-0.9
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
    "python": LanguageDefinition(name="Python", extensions={".py", ".pyw"}),
    "javascript": LanguageDefinition(name="JavaScript", extensions={".js", ".jsx", ".mjs", ".cjs"}),
    "typescript": LanguageDefinition(name="TypeScript", extensions={".ts", ".tsx"}),
    "java": LanguageDefinition(name="Java", extensions={".java", ".jsp"}),
    "ruby": LanguageDefinition(name="Ruby", extensions={".rb", ".erb"}),
    "php": LanguageDefinition(name="PHP", extensions={".php", ".phtml"}),
    "csharp": LanguageDefinition(name="C#", extensions={".cs", ".cshtml"}),
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
class FrameworkSecurityRule:
    """A framework-specific security rule."""
    id: str
    title: str
    description: str
    severity: Severity
    cwe_ids: List[str]
    category: str
    framework: str

    # Language-specific regex patterns
    patterns: Dict[str, LanguagePattern]

    # Fix suggestions
    fix_suggestion: str

    # Confidence for this rule
    confidence: float = 0.8

    # Context keywords for reducing false positives
    context_keywords: List[str] = field(default_factory=list)
    require_context: bool = False
    context_window_lines: int = 10

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)


# =============================================================================
# FRAMEWORK DETECTION INDICATORS
# =============================================================================

FRAMEWORK_INDICATORS: Dict[str, List[str]] = {
    "django": ["from django", "import django", "django.db", "INSTALLED_APPS", "django.conf"],
    "flask": ["from flask", "import flask", "Flask(__name__)", "flask.Flask"],
    "express": ["require('express')", 'require("express")', "import express", "express()", "app.use(", "router."],
    "spring": ["@SpringBootApplication", "@RestController", "@Autowired", "import org.springframework"],
    "rails": ["ActiveRecord", "ActionController", "ApplicationController", "Rails.application"],
    "laravel": ["Illuminate\\", "use App\\", "Route::", "Eloquent", "artisan"],
    "aspnet": ["using System.Web", "using Microsoft.AspNetCore", "[HttpGet]", "[ApiController]", "IActionResult"],
}


# =============================================================================
# DJANGO RULES (15)
# =============================================================================

DJANGO_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-DJ-001",
        title="Django raw SQL with f-string or format",
        description="Using raw()/extra() with f-strings or .format() enables SQL injection in Django ORM.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="django",
        patterns={"python": LanguagePattern(r'\.(?:raw|extra)\s*\(\s*(?:f["\']|["\'].*%|.*\.format\()')},
        fix_suggestion="Use QuerySet filter/exclude with parameterized queries: Model.objects.filter(field=value).",
        confidence=0.9,
        false_positive_patterns=[r'\.raw\s*\(\s*["\'][^"\']*["\'](?:\s*\)|\s*,\s*\[)', r'# nosec'],
    ),
    FrameworkSecurityRule(
        id="FW-DJ-002",
        title="Django mark_safe with user input",
        description="mark_safe() on user-controlled data disables Django's auto-escaping, enabling XSS.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="django",
        patterns={"python": LanguagePattern(r'mark_safe\s*\(\s*(?:request|user|input|f["\']|.*\.format\()')},
        fix_suggestion="Avoid mark_safe with user input. Use conditional_escape() or format_html() instead.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-003",
        title="Django autoescape disabled in template",
        description="Disabling autoescape removes XSS protection in Django templates.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="django",
        patterns={"python": LanguagePattern(r'\{%\s*autoescape\s+off\s*%\}')},
        fix_suggestion="Keep autoescape on. Use |safe filter selectively on trusted content only.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-004",
        title="Django @csrf_exempt decorator",
        description="@csrf_exempt disables CSRF protection on a view, making it vulnerable to CSRF attacks.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-352"],
        category="csrf",
        framework="django",
        patterns={"python": LanguagePattern(r'@csrf_exempt')},
        fix_suggestion="Remove @csrf_exempt. If API endpoint, use token-based authentication instead.",
        confidence=0.85,
        false_positive_patterns=[r'# API endpoint', r'# webhook'],
    ),
    FrameworkSecurityRule(
        id="FW-DJ-005",
        title="Django view missing @login_required",
        description="View functions handling sensitive data without @login_required may be accessible anonymously.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-862"],
        category="authorization",
        framework="django",
        patterns={"python": LanguagePattern(r'^def\s+(?:update|delete|edit|admin|manage|create)\w*\s*\(\s*request')},
        fix_suggestion="Add @login_required or @permission_required decorator to sensitive views.",
        confidence=0.75,
        require_context=True,
        context_keywords=["def get", "def post", "request"],
        false_positive_patterns=[r'@login_required', r'@permission_required', r'LoginRequiredMixin', r'@staff_member_required'],
    ),
    FrameworkSecurityRule(
        id="FW-DJ-006",
        title="Django DEBUG=True in settings",
        description="DEBUG=True exposes detailed error pages with stack traces, settings, and sensitive data.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-215"],
        category="configuration",
        framework="django",
        patterns={"python": LanguagePattern(r'^\s*DEBUG\s*=\s*True')},
        fix_suggestion="Set DEBUG=False in production. Use environment variable: DEBUG=os.environ.get('DEBUG', 'False').",
        confidence=0.8,
        false_positive_patterns=[r'# development', r'# test', r'os\.environ'],
    ),
    FrameworkSecurityRule(
        id="FW-DJ-007",
        title="Django ALLOWED_HOSTS wildcard",
        description="ALLOWED_HOSTS=['*'] allows any host header, enabling host header injection attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-16"],
        category="configuration",
        framework="django",
        patterns={"python": LanguagePattern(r'ALLOWED_HOSTS\s*=\s*\[\s*["\']?\*["\']?\s*\]')},
        fix_suggestion="Set ALLOWED_HOSTS to specific domain names: ALLOWED_HOSTS=['example.com'].",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-008",
        title="Django SECRET_KEY hardcoded",
        description="Hardcoded SECRET_KEY in settings exposes the key in version control.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-798"],
        category="secrets",
        framework="django",
        patterns={"python": LanguagePattern(r'SECRET_KEY\s*=\s*["\'][^"\']{10,}["\']')},
        fix_suggestion="Load SECRET_KEY from environment: SECRET_KEY=os.environ['DJANGO_SECRET_KEY'].",
        confidence=0.8,
        false_positive_patterns=[r'os\.environ', r'os\.getenv', r'config\(', r'# example'],
    ),
    FrameworkSecurityRule(
        id="FW-DJ-009",
        title="Django session cookie without httponly",
        description="Session cookies without HttpOnly flag are accessible to JavaScript, enabling session theft via XSS.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-1004"],
        category="session",
        framework="django",
        patterns={"python": LanguagePattern(r'SESSION_COOKIE_HTTPONLY\s*=\s*False')},
        fix_suggestion="Set SESSION_COOKIE_HTTPONLY=True (default) to prevent JavaScript access.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-010",
        title="Django render_template_string usage",
        description="render_template_string with user input enables server-side template injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-1336"],
        category="template_injection",
        framework="django",
        patterns={"python": LanguagePattern(r'Template\s*\(\s*(?:request|user|input|f["\'])')},
        fix_suggestion="Use render() with template files instead of constructing templates from user input.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-011",
        title="Django JsonResponse with unsanitized data",
        description="JsonResponse with user-controlled data without proper serialization may leak sensitive info.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="django",
        patterns={"python": LanguagePattern(r'JsonResponse\s*\(\s*\{[^}]*request\.')},
        fix_suggestion="Validate and sanitize data before passing to JsonResponse. Use serializers.",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-012",
        title="Django FileSystemStorage with user path",
        description="FileSystemStorage or default_storage with user-controlled paths enables path traversal.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        framework="django",
        patterns={"python": LanguagePattern(r'(?:FileSystemStorage|default_storage)\s*\([^)]*(?:request|user|input)')},
        fix_suggestion="Validate file paths with os.path.basename(). Use Django's FileField for uploads.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-013",
        title="Django ModelForm without fields restriction",
        description="ModelForm without explicit fields or exclude allows mass assignment attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-915"],
        category="mass_assignment",
        framework="django",
        patterns={"python": LanguagePattern(r'class\s+\w+\s*\([^)]*ModelForm[^)]*\).*?fields\s*=\s*["\']__all__["\']', flags=re.DOTALL | re.MULTILINE)},
        fix_suggestion="Explicitly list allowed fields: fields = ['name', 'email']. Never use '__all__'.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-DJ-014",
        title="Django raw SQL via connection.cursor",
        description="Direct SQL via connection.cursor() with string formatting enables SQL injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="django",
        patterns={"python": LanguagePattern(r'cursor\.execute\s*\(\s*(?:f["\']|["\'].*%|.*\.format\()')},
        fix_suggestion="Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id=%s', [user_id]).",
        confidence=0.9,
        false_positive_patterns=[r'cursor\.execute\s*\(\s*["\'][^"\']*["\']\s*,\s*[\[\(]'],
    ),
    FrameworkSecurityRule(
        id="FW-DJ-015",
        title="Django unsafe redirect",
        description="HttpResponseRedirect with user-controlled URL enables open redirect attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-601"],
        category="open_redirect",
        framework="django",
        patterns={"python": LanguagePattern(r'HttpResponseRedirect\s*\(\s*(?:request|user|input)')},
        fix_suggestion="Validate redirect URL against allowlist. Use django.utils.http.url_has_allowed_host_and_scheme().",
        confidence=0.8,
        false_positive_patterns=[r'url_has_allowed_host', r'is_safe_url'],
    ),
]


# =============================================================================
# FLASK RULES (10)
# =============================================================================

FLASK_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-FL-001",
        title="Flask render_template_string with user input",
        description="render_template_string with user data enables server-side template injection (SSTI).",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-1336"],
        category="template_injection",
        framework="flask",
        patterns={"python": LanguagePattern(r'render_template_string\s*\(\s*(?:request|user|input|f["\'])')},
        fix_suggestion="Use render_template() with template files. Never pass user input to render_template_string().",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-FL-002",
        title="Flask Markup with user data",
        description="Markup() marks content as safe HTML, bypassing auto-escaping. User input causes XSS.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="flask",
        patterns={"python": LanguagePattern(r'Markup\s*\(\s*(?:request|user|input|f["\']|.*\.format\()')},
        fix_suggestion="Use Markup.escape() on user input before wrapping. Or use Jinja2 auto-escaping.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-FL-003",
        title="Flask secret_key hardcoded",
        description="Hardcoded secret_key in Flask app exposes session signing key.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-798"],
        category="secrets",
        framework="flask",
        patterns={"python": LanguagePattern(r'(?:app\.secret_key|app\.config\s*\[\s*["\']SECRET_KEY["\']\s*\])\s*=\s*["\'][^"\']{5,}["\']')},
        fix_suggestion="Load secret_key from environment: app.secret_key = os.environ['FLASK_SECRET_KEY'].",
        confidence=0.8,
        false_positive_patterns=[r'os\.environ', r'os\.getenv', r'# example', r'# test'],
    ),
    FrameworkSecurityRule(
        id="FW-FL-004",
        title="Flask debug mode enabled",
        description="app.run(debug=True) exposes Werkzeug debugger with code execution capability.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-215"],
        category="configuration",
        framework="flask",
        patterns={"python": LanguagePattern(r'app\.run\s*\([^)]*debug\s*=\s*True')},
        fix_suggestion="Never enable debug in production. Use FLASK_DEBUG environment variable for development.",
        confidence=0.85,
        false_positive_patterns=[r'if\s+__name__', r'# development'],
    ),
    FrameworkSecurityRule(
        id="FW-FL-005",
        title="Flask send_file with user-controlled path",
        description="send_file/send_from_directory with user input enables path traversal to read arbitrary files.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        framework="flask",
        patterns={"python": LanguagePattern(r'send_(?:file|from_directory)\s*\([^)]*(?:request|user|input)')},
        fix_suggestion="Use send_from_directory() with fixed base path. Validate filename with secure_filename().",
        confidence=0.85,
        false_positive_patterns=[r'secure_filename', r'os\.path\.basename'],
    ),
    FrameworkSecurityRule(
        id="FW-FL-006",
        title="Flask Response with user data",
        description="Creating Response objects directly with user data without escaping may cause XSS.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="flask",
        patterns={"python": LanguagePattern(r'(?:Response|make_response)\s*\(\s*(?:request|user|input|f["\'])')},
        fix_suggestion="Use render_template() for HTML responses. Escape user data with markupsafe.escape().",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-FL-007",
        title="Flask route without methods restriction",
        description="Routes accepting all HTTP methods may expose unintended functionality.",
        severity=Severity.LOW,
        cwe_ids=["CWE-16"],
        category="configuration",
        framework="flask",
        patterns={"python": LanguagePattern(r'@app\.route\s*\(\s*["\'][^"\']+["\']\s*\)')},
        fix_suggestion="Specify allowed methods: @app.route('/path', methods=['GET', 'POST']).",
        confidence=0.75,
        false_positive_patterns=[r'methods\s*='],
    ),
    FrameworkSecurityRule(
        id="FW-FL-008",
        title="Flask CORS allow all origins",
        description="CORS with allow_all_origins permits any website to make cross-origin requests.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-942"],
        category="cors",
        framework="flask",
        patterns={"python": LanguagePattern(r'CORS\s*\(\s*app\s*\)|origins\s*=\s*["\']?\*["\']?')},
        fix_suggestion="Configure specific allowed origins: CORS(app, origins=['https://example.com']).",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-FL-009",
        title="Flask Jinja2 autoescape disabled",
        description="Jinja2 Environment with autoescape=False disables automatic XSS protection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="flask",
        patterns={"python": LanguagePattern(r'Environment\s*\([^)]*autoescape\s*=\s*False')},
        fix_suggestion="Enable autoescape: Environment(autoescape=select_autoescape(['html', 'xml'])).",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-FL-010",
        title="Flask-Login without session protection",
        description="Flask-Login without session protection mode allows session fixation attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-384"],
        category="session",
        framework="flask",
        patterns={"python": LanguagePattern(r'login_manager\.session_protection\s*=\s*None')},
        fix_suggestion="Set session_protection to 'strong': login_manager.session_protection = 'strong'.",
        confidence=0.85,
    ),
]


# =============================================================================
# EXPRESS RULES (12)
# =============================================================================

EXPRESS_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-EX-001",
        title="Express app without helmet middleware",
        description="Missing helmet middleware leaves Express app without security headers (CSP, HSTS, etc.).",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-16"],
        category="configuration",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'app\s*=\s*express\s*\(\s*\)(?:(?!helmet).)*$', flags=re.MULTILINE),
            "typescript": LanguagePattern(r'app\s*=\s*express\s*\(\s*\)(?:(?!helmet).)*$', flags=re.MULTILINE),
        },
        fix_suggestion="Install and use helmet: app.use(helmet()). This sets multiple security headers.",
        confidence=0.75,
        false_positive_patterns=[r'helmet', r'app\.use\s*\(\s*helmet'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-002",
        title="Express without rate limiting",
        description="No rate limiting middleware exposes the API to brute-force and DoS attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-770"],
        category="configuration",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'app\.(?:post|put)\s*\(\s*["\']\/(?:login|auth|api)', flags=re.MULTILINE),
            "typescript": LanguagePattern(r'app\.(?:post|put)\s*\(\s*["\']\/(?:login|auth|api)', flags=re.MULTILINE),
        },
        fix_suggestion="Add rate limiting: app.use(rateLimit({ windowMs: 15*60*1000, max: 100 })).",
        confidence=0.75,
        false_positive_patterns=[r'rateLimit', r'rate-limit', r'express-rate-limit', r'slowDown'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-003",
        title="Express CORS allow all origins",
        description="cors() without configuration or cors({origin: '*'}) allows any website to access the API.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-942"],
        category="cors",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'(?:app\.use\s*\(\s*cors\s*\(\s*\)|origin\s*:\s*["\']?\*["\']?|origin\s*:\s*true)'),
            "typescript": LanguagePattern(r'(?:app\.use\s*\(\s*cors\s*\(\s*\)|origin\s*:\s*["\']?\*["\']?|origin\s*:\s*true)'),
        },
        fix_suggestion="Configure specific origins: cors({ origin: ['https://example.com'] }).",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-EX-004",
        title="Express without CSRF protection",
        description="Missing CSRF middleware on state-changing routes allows cross-site request forgery.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-352"],
        category="csrf",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'app\.(?:post|put|delete)\s*\(\s*["\']'),
            "typescript": LanguagePattern(r'app\.(?:post|put|delete)\s*\(\s*["\']'),
        },
        fix_suggestion="Use csurf middleware: app.use(csrf({ cookie: true })). Or use SameSite cookies.",
        confidence=0.75,
        false_positive_patterns=[r'csrf', r'csurf', r'csrfProtection', r'SameSite'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-005",
        title="Express EJS render with user input",
        description="ejs.render/renderFile with user-controlled template enables server-side template injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-1336"],
        category="template_injection",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'ejs\.render(?:File)?\s*\(\s*(?:req\.|params|query|body)'),
            "typescript": LanguagePattern(r'ejs\.render(?:File)?\s*\(\s*(?:req\.|params|query|body)'),
        },
        fix_suggestion="Never pass user input as template. Use res.render() with template files.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-EX-006",
        title="Express cookie without secure flags",
        description="Cookies without secure/httpOnly/sameSite flags are vulnerable to theft and CSRF.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-614"],
        category="session",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'res\.cookie\s*\(\s*["\'][^"\']+["\']\s*,\s*[^,]+\s*(?:\)|,\s*\{(?:(?!secure|httpOnly).)*\})'),
            "typescript": LanguagePattern(r'res\.cookie\s*\(\s*["\'][^"\']+["\']\s*,\s*[^,]+\s*(?:\)|,\s*\{(?:(?!secure|httpOnly).)*\})'),
        },
        fix_suggestion="Set secure flags: res.cookie('name', value, { secure: true, httpOnly: true, sameSite: 'strict' }).",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-EX-007",
        title="Express static serving sensitive directories",
        description="express.static serving root or sensitive directories exposes source code and configuration.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-538"],
        category="information_exposure",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'express\.static\s*\(\s*(?:["\']\.?/?["\']|__dirname\s*\)|["\']/)'),
            "typescript": LanguagePattern(r'express\.static\s*\(\s*(?:["\']\.?/?["\']|__dirname\s*\)|["\']/)'),
        },
        fix_suggestion="Serve only specific directories: express.static(path.join(__dirname, 'public')).",
        confidence=0.75,
        false_positive_patterns=[r'public', r'static', r'assets', r'dist'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-008",
        title="Express redirect with user URL",
        description="res.redirect with user-controlled URL enables open redirect attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-601"],
        category="open_redirect",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'res\.redirect\s*\(\s*(?:req\.|params|query|body)'),
            "typescript": LanguagePattern(r'res\.redirect\s*\(\s*(?:req\.|params|query|body)'),
        },
        fix_suggestion="Validate redirect URL against an allowlist of trusted domains.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-EX-009",
        title="Express MongoDB query injection",
        description="Passing req.body directly to MongoDB query enables NoSQL injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-943"],
        category="nosql_injection",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'\.(?:find|findOne|findOneAndUpdate|deleteOne|updateOne)\s*\(\s*req\.(?:body|query|params)'),
            "typescript": LanguagePattern(r'\.(?:find|findOne|findOneAndUpdate|deleteOne|updateOne)\s*\(\s*req\.(?:body|query|params)'),
        },
        fix_suggestion="Validate and sanitize input. Use express-mongo-sanitize or manual $-prefix stripping.",
        confidence=0.85,
        false_positive_patterns=[r'sanitize', r'validate', r'joi\.', r'express-mongo-sanitize'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-010",
        title="Express JWT without algorithm verification",
        description="JWT verification without specifying algorithm allows algorithm confusion attacks.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-347"],
        category="authentication",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'jwt\.verify\s*\(\s*[^,]+\s*,\s*[^,]+\s*\)'),
            "typescript": LanguagePattern(r'jwt\.verify\s*\(\s*[^,]+\s*,\s*[^,]+\s*\)'),
        },
        fix_suggestion="Specify algorithm: jwt.verify(token, secret, { algorithms: ['HS256'] }).",
        confidence=0.8,
        false_positive_patterns=[r'algorithms\s*:', r'algorithm\s*:'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-011",
        title="Express multer without file filter",
        description="multer without file filter allows upload of any file type including executables.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-434"],
        category="file_upload",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'multer\s*\(\s*\{(?:(?!fileFilter).)*\}\s*\)'),
            "typescript": LanguagePattern(r'multer\s*\(\s*\{(?:(?!fileFilter).)*\}\s*\)'),
        },
        fix_suggestion="Add fileFilter to validate file types: multer({ fileFilter: (req, file, cb) => ... }).",
        confidence=0.75,
        false_positive_patterns=[r'fileFilter'],
    ),
    FrameworkSecurityRule(
        id="FW-EX-012",
        title="Express body-parser without size limit",
        description="body-parser without size limit enables denial-of-service via large payloads.",
        severity=Severity.LOW,
        cwe_ids=["CWE-400"],
        category="dos",
        framework="express",
        patterns={
            "javascript": LanguagePattern(r'(?:bodyParser|express)\.(?:json|urlencoded)\s*\(\s*(?:\)|\{\s*(?:(?!limit).)*\})'),
            "typescript": LanguagePattern(r'(?:bodyParser|express)\.(?:json|urlencoded)\s*\(\s*(?:\)|\{\s*(?:(?!limit).)*\})'),
        },
        fix_suggestion="Set size limit: express.json({ limit: '10mb' }).",
        confidence=0.75,
        false_positive_patterns=[r'limit\s*:'],
    ),
]


# =============================================================================
# SPRING RULES (15)
# =============================================================================

SPRING_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-SP-001",
        title="Spring SpEL injection from user input",
        description="Spring Expression Language with user input enables remote code execution.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-917"],
        category="code_injection",
        framework="spring",
        patterns={"java": LanguagePattern(r'(?:SpelExpressionParser|ExpressionParser)\s*\(\s*\).*\.parseExpression\s*\(\s*(?:request|input|param)')},
        fix_suggestion="Never pass user input to SpEL parser. Use parameterized queries or validated input.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-SP-002",
        title="Spring @Query with string concatenation",
        description="JPQL/HQL @Query with string concatenation enables SQL injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="spring",
        patterns={"java": LanguagePattern(r'@Query\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use named parameters: @Query('SELECT u FROM User u WHERE u.name = :name').",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-SP-003",
        title="Spring JdbcTemplate with string concatenation",
        description="JdbcTemplate query with string concatenation enables SQL injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="spring",
        patterns={"java": LanguagePattern(r'jdbcTemplate\.(?:query|update|execute)\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use parameterized queries: jdbcTemplate.query(sql, new Object[]{param}, mapper).",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-SP-004",
        title="Spring Security CSRF disabled",
        description="csrf().disable() removes CSRF protection from the application.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-352"],
        category="csrf",
        framework="spring",
        patterns={"java": LanguagePattern(r'\.csrf\s*\(\s*\)\s*\.disable\s*\(\s*\)')},
        fix_suggestion="Enable CSRF protection. For REST APIs, use token-based CSRF protection.",
        confidence=0.85,
        false_positive_patterns=[r'// stateless', r'// REST API', r'// token auth'],
    ),
    FrameworkSecurityRule(
        id="FW-SP-005",
        title="Spring actuator exposed without authentication",
        description="Spring Boot Actuator endpoints expose sensitive data without authentication.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-200"],
        category="information_exposure",
        framework="spring",
        patterns={"java": LanguagePattern(r'management\.endpoints\.web\.exposure\.include\s*=\s*\*')},
        fix_suggestion="Restrict actuator: management.endpoints.web.exposure.include=health,info.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-SP-006",
        title="Spring @CrossOrigin without specific origins",
        description="@CrossOrigin without specifying origins allows any website to access the endpoint.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-942"],
        category="cors",
        framework="spring",
        patterns={"java": LanguagePattern(r'@CrossOrigin\s*(?:\(\s*\)|\s*$)')},
        fix_suggestion="Specify allowed origins: @CrossOrigin(origins = 'https://example.com').",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-SP-007",
        title="Spring ResponseEntity with user input",
        description="ResponseEntity.body with unsanitized user input may enable XSS in HTML responses.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="spring",
        patterns={"java": LanguagePattern(r'ResponseEntity\.(?:ok|status)\s*\([^)]*(?:request|input|param)')},
        fix_suggestion="Sanitize user input before including in response body. Use content-type application/json.",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-SP-008",
        title="Spring RestTemplate with user URL",
        description="RestTemplate with user-controlled URL enables SSRF attacks.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-918"],
        category="ssrf",
        framework="spring",
        patterns={"java": LanguagePattern(r'restTemplate\.(?:getForObject|getForEntity|postForObject|exchange)\s*\(\s*(?:request|input|param|url)')},
        fix_suggestion="Validate URL against allowlist. Block internal/private IP ranges.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-SP-009",
        title="Spring ObjectMapper without type validation",
        description="ObjectMapper deserializing user input without type restrictions enables RCE via gadget chains.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-502"],
        category="deserialization",
        framework="spring",
        patterns={"java": LanguagePattern(r'objectMapper\.(?:readValue|readTree)\s*\(\s*(?:request|input|body)')},
        fix_suggestion="Enable default typing restrictions. Use @JsonTypeInfo with allowlisted types.",
        confidence=0.75,
        false_positive_patterns=[r'activateDefaultTyping', r'PolymorphicTypeValidator'],
    ),
    FrameworkSecurityRule(
        id="FW-SP-010",
        title="Spring log injection",
        description="Logging user input without sanitization enables log injection/forging attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-117"],
        category="log_injection",
        framework="spring",
        patterns={"java": LanguagePattern(r'(?:log|logger|LOG)\.(?:info|warn|error|debug)\s*\([^)]*(?:request\.getParameter|input|\.getHeader\()')},
        fix_suggestion="Sanitize log data: remove newlines and ANSI codes from user input before logging.",
        confidence=0.75,
        false_positive_patterns=[r'StringEscapeUtils', r'sanitize', r'replace\s*\(\s*["\']\\n'],
    ),
    FrameworkSecurityRule(
        id="FW-SP-011",
        title="Spring @RequestMapping without method",
        description="@RequestMapping without method accepts all HTTP methods including unsafe ones.",
        severity=Severity.LOW,
        cwe_ids=["CWE-16"],
        category="configuration",
        framework="spring",
        patterns={"java": LanguagePattern(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\'](?:(?!method).)*["\'](?:\s*\))'),
        },
        fix_suggestion="Use @GetMapping, @PostMapping, etc. or specify method in @RequestMapping.",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-SP-012",
        title="Spring Security permitAll on sensitive paths",
        description="permitAll() on sensitive paths (admin, api, user) bypasses authentication.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-862"],
        category="authorization",
        framework="spring",
        patterns={"java": LanguagePattern(r'\.(?:antMatchers|requestMatchers)\s*\(\s*["\'](?:/admin|/api|/user|/account)["\'].*\.permitAll\s*\(\s*\)')},
        fix_suggestion="Use .authenticated() or .hasRole() for sensitive paths.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-SP-013",
        title="Spring PropertySource with external file",
        description="PropertySource loading configuration from user-controlled path enables file read attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        framework="spring",
        patterns={"java": LanguagePattern(r'@PropertySource\s*\(\s*["\'](?:file:|classpath:).*\$\{')},
        fix_suggestion="Validate property source paths. Avoid using variables in @PropertySource paths.",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-SP-014",
        title="Spring multipart without size limit",
        description="Multipart file upload without size limit enables denial-of-service.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-400"],
        category="dos",
        framework="spring",
        patterns={"java": LanguagePattern(r'spring\.servlet\.multipart\.max-file-size\s*=\s*-1')},
        fix_suggestion="Set max size: spring.servlet.multipart.max-file-size=10MB.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-SP-015",
        title="Spring CORS configuration allow all",
        description="WebMvcConfigurer with allowedOrigins('*') allows all cross-origin requests.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-942"],
        category="cors",
        framework="spring",
        patterns={"java": LanguagePattern(r'\.allowedOrigins\s*\(\s*["\']?\*["\']?\s*\)')},
        fix_suggestion="Specify allowed origins: .allowedOrigins('https://example.com').",
        confidence=0.85,
    ),
]


# =============================================================================
# RAILS RULES (10)
# =============================================================================

RAILS_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-RA-001",
        title="Rails find_by_sql with interpolation",
        description="find_by_sql with string interpolation enables SQL injection.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'find_by_sql\s*\(\s*["\'].*\#\{')},
        fix_suggestion="Use parameterized queries: find_by_sql(['SELECT * FROM users WHERE id = ?', id]).",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-RA-002",
        title="Rails html_safe on user input",
        description="html_safe marks string as safe HTML, bypassing Rails auto-escaping. User input causes XSS.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'(?:params|request|input)\s*(?:\[.*\])?\s*\.html_safe')},
        fix_suggestion="Never call html_safe on user input. Use sanitize() or content_tag() helpers.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-RA-003",
        title="Rails skip_before_action verify_authenticity_token",
        description="Skipping authenticity token verification disables CSRF protection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-352"],
        category="csrf",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'skip_before_action\s*:verify_authenticity_token')},
        fix_suggestion="Keep CSRF protection. For API endpoints, use token-based authentication.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-RA-004",
        title="Rails mass assignment with permit!",
        description="permit! allows all parameters through strong parameters, enabling mass assignment.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-915"],
        category="mass_assignment",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'params\.(?:require\s*\([^)]+\)\s*\.)?permit!')},
        fix_suggestion="Explicitly list allowed parameters: params.require(:user).permit(:name, :email).",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-RA-005",
        title="Rails render inline with user input",
        description="render inline with user-controlled template string enables SSTI.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-1336"],
        category="template_injection",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'render\s+inline\s*:\s*(?:params|request|input)')},
        fix_suggestion="Use render with template files, not inline user content.",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-RA-006",
        title="Rails send_file with user path",
        description="send_file/send_data with user-controlled path enables arbitrary file read.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'send_(?:file|data)\s*(?:\(|\s)(?:params|request|input)')},
        fix_suggestion="Validate file path with File.basename(). Restrict to specific directory.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-RA-007",
        title="Rails redirect_to with user URL",
        description="redirect_to with user-controlled URL enables open redirect attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-601"],
        category="open_redirect",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'redirect_to\s*(?:\(|\s)(?:params|request)\s*\[')},
        fix_suggestion="Validate redirect URL against allowlist. Use url_for() for internal redirects.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-RA-008",
        title="Rails raw SQL with interpolation",
        description="ActiveRecord where/order/select with string interpolation enables SQL injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'\.(?:where|order|select|having|group)\s*\(\s*["\'].*\#\{')},
        fix_suggestion="Use parameterized queries: where('name = ?', params[:name]).",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-RA-009",
        title="Rails force_ssl disabled",
        description="config.force_ssl = false allows unencrypted HTTP connections.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-319"],
        category="transport_security",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'config\.force_ssl\s*=\s*false')},
        fix_suggestion="Set config.force_ssl = true in production to enforce HTTPS.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-RA-010",
        title="Rails YAML deserialization",
        description="YAML.load with untrusted input enables remote code execution via Ruby object instantiation.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-502"],
        category="deserialization",
        framework="rails",
        patterns={"ruby": LanguagePattern(r'YAML\.load\s*\(\s*(?:params|request|input|File\.read)')},
        fix_suggestion="Use YAML.safe_load() instead of YAML.load() for untrusted input.",
        confidence=0.85,
        false_positive_patterns=[r'safe_load', r'permitted_classes'],
    ),
]


# =============================================================================
# LARAVEL RULES (12)
# =============================================================================

LARAVEL_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-LA-001",
        title="Laravel DB::raw with user input",
        description="DB::raw with user-controlled data enables SQL injection in Eloquent queries.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="laravel",
        patterns={"php": LanguagePattern(r'DB::raw\s*\(\s*(?:\$_(?:GET|POST|REQUEST)|.*\$request|\$[a-z]+.*\.\s*\$)')},
        fix_suggestion="Use query bindings: DB::raw('SELECT * FROM t WHERE id = ?', [$id]).",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-LA-002",
        title="Laravel whereRaw with variable",
        description="whereRaw with user-controlled strings enables SQL injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="laravel",
        patterns={"php": LanguagePattern(r'->whereRaw\s*\(\s*(?:[\'"]\s*\.|\$[a-z])')},
        fix_suggestion="Use bindings in whereRaw: ->whereRaw('id = ?', [$id]).",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-LA-003",
        title="Laravel Blade unescaped output",
        description="{!! $variable !!} outputs data without escaping in Blade templates, enabling XSS.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="laravel",
        patterns={"php": LanguagePattern(r'\{!!\s*\$(?:request|input|_GET|_POST|_REQUEST)')},
        fix_suggestion="Use {{ $variable }} for auto-escaped output. Only use {!! !!} for trusted HTML.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-LA-004",
        title="Laravel APP_DEBUG enabled",
        description="APP_DEBUG=true in production exposes detailed error pages with sensitive information.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-215"],
        category="configuration",
        framework="laravel",
        patterns={"php": LanguagePattern(r'APP_DEBUG\s*=\s*true')},
        fix_suggestion="Set APP_DEBUG=false in production .env file.",
        confidence=0.8,
        false_positive_patterns=[r'\.env\.example', r'# '],
    ),
    FrameworkSecurityRule(
        id="FW-LA-005",
        title="Laravel empty $guarded array",
        description="$guarded = [] makes all model attributes mass-assignable, enabling mass assignment attacks.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-915"],
        category="mass_assignment",
        framework="laravel",
        patterns={"php": LanguagePattern(r'\$guarded\s*=\s*\[\s*\]')},
        fix_suggestion="Define $fillable with allowed fields: protected $fillable = ['name', 'email'];",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-LA-006",
        title="Laravel route without auth middleware",
        description="Routes handling sensitive data without auth middleware may be accessible anonymously.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-862"],
        category="authorization",
        framework="laravel",
        patterns={"php": LanguagePattern(r'Route::(?:post|put|delete)\s*\(\s*["\']\/(?:admin|user|account|api\/(?:admin|user))')},
        fix_suggestion="Add auth middleware: Route::post('/admin/...')->middleware('auth').",
        confidence=0.75,
        false_positive_patterns=[r"->middleware\s*\(\s*['\"]auth", r"->middleware\s*\(\s*\[.*auth"],
    ),
    FrameworkSecurityRule(
        id="FW-LA-007",
        title="Laravel cookie without encryption",
        description="Cookies added to EncryptCookies $except list are sent unencrypted.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-311"],
        category="encryption",
        framework="laravel",
        patterns={"php": LanguagePattern(r'\$except\s*=\s*\[\s*["\'][^"\']+["\']')},
        fix_suggestion="Remove sensitive cookies from $except. Let Laravel encrypt all cookies.",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-LA-008",
        title="Laravel CORS allow all origins",
        description="CORS configuration with allowed_origins=['*'] permits any website to access the API.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-942"],
        category="cors",
        framework="laravel",
        patterns={"php": LanguagePattern(r'allowed_origins\s*.*=>\s*\[\s*["\']?\*["\']?\s*\]')},
        fix_suggestion="Specify allowed origins: 'allowed_origins' => ['https://example.com'].",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-LA-009",
        title="Laravel file upload without validation",
        description="Storing uploaded files without validation allows malicious file uploads.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-434"],
        category="file_upload",
        framework="laravel",
        patterns={"php": LanguagePattern(r'\$request->file\s*\([^)]+\)->store(?:As)?\s*\(')},
        fix_suggestion="Validate files: $request->validate(['file' => 'required|mimes:jpg,png|max:2048']).",
        confidence=0.75,
        false_positive_patterns=[r'->validate\s*\(', r'mimes:', r'mimetypes:'],
    ),
    FrameworkSecurityRule(
        id="FW-LA-010",
        title="Laravel redirect with user URL",
        description="redirect() with user-controlled URL enables open redirect attacks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-601"],
        category="open_redirect",
        framework="laravel",
        patterns={"php": LanguagePattern(r'redirect\s*\(\s*\$request->(?:input|get|query)')},
        fix_suggestion="Validate redirect URL against allowlist. Use redirect()->route() for named routes.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-LA-011",
        title="Laravel view with user template",
        description="view()->make/view() with user-controlled template name enables template injection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-1336"],
        category="template_injection",
        framework="laravel",
        patterns={"php": LanguagePattern(r'(?:view|View::make)\s*\(\s*\$(?:request|_GET|_POST)')},
        fix_suggestion="Never use user input as template name. Use a validated mapping of template names.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-LA-012",
        title="Laravel config cache with debug",
        description="Running config:cache with debug enabled bakes debug mode into cached config.",
        severity=Severity.LOW,
        cwe_ids=["CWE-215"],
        category="configuration",
        framework="laravel",
        patterns={"php": LanguagePattern(r"'debug'\s*=>\s*(?:true|env\s*\(\s*'APP_DEBUG'\s*,\s*true\))")},
        fix_suggestion="Set debug to false in production: 'debug' => env('APP_DEBUG', false).",
        confidence=0.75,
        false_positive_patterns=[r"env\s*\(\s*'APP_DEBUG'\s*,\s*false\s*\)"],
    ),
]


# =============================================================================
# ASP.NET RULES (10)
# =============================================================================

ASPNET_RULES: List[FrameworkSecurityRule] = [
    FrameworkSecurityRule(
        id="FW-AN-001",
        title="ASP.NET SqlCommand with string concatenation",
        description="SqlCommand with string concatenation enables SQL injection.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-89"],
        category="sql_injection",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'(?:SqlCommand|SqlDataAdapter)\s*\(\s*["\'][^"\']*["\']\s*\+')},
        fix_suggestion="Use parameterized queries: cmd.Parameters.AddWithValue('@param', value).",
        confidence=0.9,
    ),
    FrameworkSecurityRule(
        id="FW-AN-002",
        title="ASP.NET Html.Raw with user data",
        description="@Html.Raw() outputs HTML without encoding, enabling XSS with user input.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'Html\.Raw\s*\(\s*(?:Model\.|ViewBag\.|ViewData\[|Request\.|input)')},
        fix_suggestion="Use @Html.Encode() or Razor's default encoding. Only use Html.Raw for trusted HTML.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-AN-003",
        title="ASP.NET validateRequest disabled",
        description="validateRequest='false' disables ASP.NET's built-in XSS request validation.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-20"],
        category="input_validation",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'(?:validateRequest\s*=\s*["\']?false|ValidateInput\s*\(\s*false\s*\))')},
        fix_suggestion="Keep request validation enabled. Use [AllowHtml] on specific model properties if needed.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-AN-004",
        title="ASP.NET controller missing [Authorize]",
        description="Controller handling sensitive operations without [Authorize] is publicly accessible.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-862"],
        category="authorization",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'public\s+class\s+(?:Admin|User|Account|Manage)\w*Controller(?:(?!\[Authorize\]).)*\{', flags=re.DOTALL | re.MULTILINE)},
        fix_suggestion="Add [Authorize] attribute to controllers or actions handling sensitive operations.",
        confidence=0.75,
        false_positive_patterns=[r'\[Authorize\]', r'\[AllowAnonymous\]'],
    ),
    FrameworkSecurityRule(
        id="FW-AN-005",
        title="ASP.NET Response.Write with user input",
        description="Response.Write with user data without encoding enables XSS.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'Response\.Write\s*\(\s*(?:Request|input|user|Model\.)')},
        fix_suggestion="Use HttpUtility.HtmlEncode() or Server.HtmlEncode() before writing user data.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-AN-006",
        title="ASP.NET Directory.GetFiles with user path",
        description="Directory operations with user-controlled paths enable path traversal.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-22"],
        category="path_traversal",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'(?:Directory|File)\.(?:GetFiles|ReadAllText|ReadAllBytes|Exists|Delete)\s*\([^)]*(?:Request|input|user)')},
        fix_suggestion="Validate and canonicalize paths. Use Path.GetFullPath() and verify within allowed directory.",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-AN-007",
        title="ASP.NET FormsAuthentication without SSL",
        description="Forms authentication without requireSSL sends credentials over unencrypted connections.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-319"],
        category="transport_security",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'requireSSL\s*=\s*["\']?false')},
        fix_suggestion="Set requireSSL='true' in forms authentication configuration.",
        confidence=0.8,
    ),
    FrameworkSecurityRule(
        id="FW-AN-008",
        title="ASP.NET ViewBag/ViewData with unsanitized data",
        description="Passing user input via ViewBag/ViewData without sanitization may enable XSS.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-79"],
        category="xss",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'(?:ViewBag|ViewData)\s*\[?\s*["\']?\w+["\']?\]?\s*=\s*(?:Request|input|user)')},
        fix_suggestion="Sanitize data before setting ViewBag/ViewData. Use HtmlEncoder in the view.",
        confidence=0.75,
    ),
    FrameworkSecurityRule(
        id="FW-AN-009",
        title="ASP.NET CORS AllowAnyOrigin",
        description="CORS policy with AllowAnyOrigin permits any website to access the API.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-942"],
        category="cors",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'\.AllowAnyOrigin\s*\(\s*\)')},
        fix_suggestion="Use WithOrigins: policy.WithOrigins('https://example.com').",
        confidence=0.85,
    ),
    FrameworkSecurityRule(
        id="FW-AN-010",
        title="ASP.NET BinaryFormatter deserialization",
        description="BinaryFormatter deserializing untrusted data enables remote code execution.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-502"],
        category="deserialization",
        framework="aspnet",
        patterns={"csharp": LanguagePattern(r'BinaryFormatter\s*\(\s*\).*\.Deserialize\s*\(')},
        fix_suggestion="Use System.Text.Json or DataContractSerializer instead of BinaryFormatter.",
        confidence=0.9,
    ),
]


# =============================================================================
# COMBINED RULES
# =============================================================================

ALL_FRAMEWORK_SECURITY_RULES: List[FrameworkSecurityRule] = (
    DJANGO_RULES +
    FLASK_RULES +
    EXPRESS_RULES +
    SPRING_RULES +
    RAILS_RULES +
    LARAVEL_RULES +
    ASPNET_RULES
)


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class FrameworkSecurityPlugin(BaseScanner):
    """
    Detects framework-specific security vulnerabilities.

    Covers 7 major frameworks: Django, Flask, Express, Spring, Rails, Laravel, ASP.NET.
    Uses lightweight framework detection to apply only relevant rules per file.

    Total: 84 rules with framework auto-detection.
    Confidence: 0.75-0.9 (framework-specific patterns are high confidence).
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in ALL_FRAMEWORK_SECURITY_RULES:
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
        return ScannerType.FRAMEWORK_SECURITY

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

    def _detect_frameworks(self, content: str, language: str) -> Set[str]:
        """Detect which frameworks are present in the file content."""
        detected = set()
        content_lower = content.lower()

        # Map languages to possible frameworks
        lang_frameworks = {
            "python": ["django", "flask"],
            "javascript": ["express"],
            "typescript": ["express"],
            "java": ["spring"],
            "ruby": ["rails"],
            "php": ["laravel"],
            "csharp": ["aspnet"],
        }

        possible_frameworks = lang_frameworks.get(language, [])

        for framework in possible_frameworks:
            indicators = FRAMEWORK_INDICATORS.get(framework, [])
            for indicator in indicators:
                if indicator.lower() in content_lower:
                    detected.add(framework)
                    break

        return detected

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
        """Execute framework security scan."""
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

                # Detect frameworks in this file
                detected_frameworks = self._detect_frameworks(content, language)

                for rule in ALL_FRAMEWORK_SECURITY_RULES:
                    # Only apply rules for detected frameworks (or all if none detected)
                    if detected_frameworks and rule.framework not in detected_frameworks:
                        continue

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
                            id=f"framework-{rule.id}-{file_path}:{line_start}",
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
                            confidence=rule.confidence,
                            tags={f"lang:{language}", f"framework:{rule.framework}", rule.category},
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
        frameworks = {}
        for rule in ALL_FRAMEWORK_SECURITY_RULES:
            if rule.framework not in frameworks:
                frameworks[rule.framework] = 0
            frameworks[rule.framework] += 1

        categories = {}
        for rule in ALL_FRAMEWORK_SECURITY_RULES:
            if rule.category not in categories:
                categories[rule.category] = 0
            categories[rule.category] += 1

        cwe_coverage = set()
        for rule in ALL_FRAMEWORK_SECURITY_RULES:
            cwe_coverage.update(rule.cwe_ids)

        return {
            "total_rules": len(ALL_FRAMEWORK_SECURITY_RULES),
            "rules_by_framework": frameworks,
            "rules_by_category": categories,
            "supported_frameworks": list(FRAMEWORK_INDICATORS.keys()),
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": sorted(cwe_coverage),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_framework_security_plugin() -> FrameworkSecurityPlugin:
    """Factory function to create framework security plugin."""
    return FrameworkSecurityPlugin()
