"""
Authentication and Authorization Logic Detector.

Fase 41 Tier 3: Detects authentication and authorization vulnerabilities:

- CWE-862: Missing Authorization
- CWE-863: Incorrect Authorization
- CWE-287: Improper Authentication
- CWE-269: Improper Privilege Management
- CWE-20: Improper Input Validation (auth context)
- CWE-306: Missing Authentication for Critical Function

Multi-language support: Python, JavaScript, TypeScript, Java, C#, PHP, Ruby, Go
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
}


# =============================================================================
# AUTH LOGIC RULES DATA STRUCTURE
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class AuthLogicRule:
    """An authentication/authorization rule with language-specific patterns."""
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
# CWE-862: Missing Authorization - 6 rules
# =============================================================================

MISSING_AUTHZ_RULES: List[AuthLogicRule] = [
    # AUTH-862-001: Endpoint without authorization decorator (Python)
    AuthLogicRule(
        id="AUTH-862-001",
        title="API endpoint without authorization check",
        description=(
            "HTTP endpoint that handles state-changing operations without visible authorization. "
            "Attackers can access functionality they shouldn't have permission to use."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-862"],
        category="missing_authorization",
        patterns={
            "python": LanguagePattern(
                r'@(?:app|router)\.(?:post|put|delete|patch)\s*\([^)]*\)\s*\n(?:async\s+)?def\s+\w+',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Add @login_required, @permission_required, or custom authorization decorator.",
        false_positive_patterns=[
            r'@login_required', r'@permission_required', r'@requires_auth',
            r'@jwt_required', r'@auth', r'@authorize', r'@roles_required',
            r'current_user', r'get_current_user', r'request\.user',
        ],
    ),

    # AUTH-862-002: Express route without middleware (JavaScript)
    AuthLogicRule(
        id="AUTH-862-002",
        title="Express route without auth middleware",
        description=(
            "Express routes handling sensitive operations without authentication middleware."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-862"],
        category="missing_authorization",
        patterns={
            "javascript": LanguagePattern(
                r'(?:router|app)\.(?:post|put|delete|patch)\s*\(\s*[\'"][^"\']+[\'"],\s*(?:async\s*)?\(',
            ),
            "typescript": LanguagePattern(
                r'(?:router|app)\.(?:post|put|delete|patch)\s*\(\s*[\'"][^"\']+[\'"],\s*(?:async\s*)?\(',
            ),
        },
        fix_suggestion="Add authentication middleware: router.post('/path', authMiddleware, handler)",
        false_positive_patterns=[
            r'auth', r'authenticate', r'isAuth', r'requireAuth',
            r'verifyToken', r'passport', r'jwt',
        ],
    ),

    # AUTH-862-003: Direct database modification without auth (Python)
    AuthLogicRule(
        id="AUTH-862-003",
        title="Database modification without authorization check",
        description=(
            "Database write operations without visible authorization checks can allow unauthorized data modification."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-862"],
        category="missing_authorization",
        patterns={
            "python": LanguagePattern(
                r'(?:db\.session\.(?:add|delete|commit)|\.save\(\)|\.delete\(\)|\.update\()',
            ),
        },
        fix_suggestion="Ensure authorization is checked before database modifications. Verify user has permission.",
        context_keywords=["request", "api", "endpoint", "route", "view"],
        require_context=True,
        false_positive_patterns=[r'current_user', r'is_authenticated', r'has_permission', r'@login_required'],
    ),

    # AUTH-862-004: Java endpoint without security annotation
    AuthLogicRule(
        id="AUTH-862-004",
        title="Java endpoint without security annotation",
        description=(
            "Spring/JAX-RS endpoints without @PreAuthorize, @Secured, or @RolesAllowed annotations."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-862"],
        category="missing_authorization",
        patterns={
            "java": LanguagePattern(
                r'@(?:Post|Put|Delete|Patch)Mapping\s*\([^)]*\)\s*\n\s*public',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Add @PreAuthorize, @Secured, or @RolesAllowed annotation with appropriate role check.",
        false_positive_patterns=[
            r'@PreAuthorize', r'@Secured', r'@RolesAllowed', r'@WithMockUser',
            r'SecurityContext', r'Authentication',
        ],
    ),

    # AUTH-862-005: PHP admin action without auth check
    AuthLogicRule(
        id="AUTH-862-005",
        title="PHP admin function without authentication check",
        description=(
            "Administrative functionality without explicit authentication verification."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-862"],
        category="missing_authorization",
        patterns={
            "php": LanguagePattern(
                r'function\s+(?:admin|delete|update|create|modify)\w*\s*\(',
            ),
        },
        fix_suggestion="Add authentication and authorization checks at the start of admin functions.",
        context_keywords=["$_POST", "$_GET", "Route", "Controller"],
        require_context=True,
        false_positive_patterns=[
            r'auth', r'isAdmin', r'checkAuth', r'->user', r'Auth::',
            r'session\[', r'isAuthenticated',
        ],
    ),

    # AUTH-862-006: Ruby controller without authorization
    AuthLogicRule(
        id="AUTH-862-006",
        title="Rails controller action without authorization",
        description=(
            "Rails controller actions modifying data without visible authorization checks."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-862"],
        category="missing_authorization",
        patterns={
            "ruby": LanguagePattern(
                r'def\s+(?:create|update|destroy|delete)\s*\n',
            ),
        },
        fix_suggestion="Add before_action :authorize! or use Pundit/CanCanCan for authorization.",
        context_keywords=["Controller", "ApplicationController", "params"],
        require_context=True,
        false_positive_patterns=[
            r'authorize', r'can\?', r'current_user', r'before_action.*auth',
            r'authenticate_user', r'pundit',
        ],
    ),
]


# =============================================================================
# CWE-863: Incorrect Authorization - 5 rules
# =============================================================================

INCORRECT_AUTHZ_RULES: List[AuthLogicRule] = [
    # AUTH-863-001: Direct object reference without ownership check
    AuthLogicRule(
        id="AUTH-863-001",
        title="Direct object reference without ownership verification",
        description=(
            "Accessing objects by ID without verifying the current user owns or has access to the object. "
            "This enables Insecure Direct Object Reference (IDOR) attacks."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-863", "CWE-639"],
        category="incorrect_authorization",
        patterns={
            "python": LanguagePattern(
                r'\.get\s*\(\s*(?:id\s*=\s*)?(?:request|args|params|kwargs).*\[.*id',
            ),
        },
        fix_suggestion="Always verify object ownership: obj = Model.get(id); if obj.user_id != current_user.id: abort(403)",
        false_positive_patterns=[r'user_id.*current_user', r'owner', r'belongs_to', r'authorized'],
    ),

    # AUTH-863-002: JavaScript IDOR pattern
    AuthLogicRule(
        id="AUTH-863-002",
        title="Object lookup without authorization check",
        description=(
            "Fetching objects by user-provided ID without verifying access permissions."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-863", "CWE-639"],
        category="incorrect_authorization",
        patterns={
            "javascript": LanguagePattern(
                r'(?:findById|findOne|findByPk)\s*\(\s*(?:req\.|params\.|body\.)',
            ),
            "typescript": LanguagePattern(
                r'(?:findById|findOne|findByPk)\s*\(\s*(?:req\.|params\.|body\.)',
            ),
        },
        fix_suggestion="Add ownership check: const obj = await Model.findById(id); if (obj.userId !== req.user.id) return res.status(403)",
        false_positive_patterns=[r'userId.*req\.user', r'owner', r'belongsTo', r'checkAccess'],
    ),

    # AUTH-863-003: Role check bypass
    AuthLogicRule(
        id="AUTH-863-003",
        title="Weak role comparison",
        description=(
            "Role checks using equality operators that can be bypassed with type coercion or manipulation."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-863"],
        category="incorrect_authorization",
        patterns={
            "javascript": LanguagePattern(
                r'(?:role|isAdmin|permission)\s*==\s*[\'"]',
            ),
            "php": LanguagePattern(
                r'\$(?:role|isAdmin|permission)\s*==\s*[\'"]',
            ),
        },
        fix_suggestion="Use strict equality (===) and validate role is from trusted source.",
    ),

    # AUTH-863-004: Client-side authorization check
    AuthLogicRule(
        id="AUTH-863-004",
        title="Authorization check in client-side code",
        description=(
            "Authorization logic in client-side JavaScript can be bypassed by attackers. "
            "Server-side verification is always required."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-863", "CWE-602"],
        category="incorrect_authorization",
        patterns={
            "javascript": LanguagePattern(
                r'if\s*\(\s*(?:localStorage|sessionStorage)\.(?:getItem|get)\s*\(\s*[\'"](?:role|isAdmin|permission)',
            ),
        },
        fix_suggestion="Always perform authorization on the server. Client-side checks are only for UX.",
    ),

    # AUTH-863-005: Java missing resource owner check
    AuthLogicRule(
        id="AUTH-863-005",
        title="Resource access without owner verification",
        description=(
            "Accessing resources by ID without checking if the authenticated user has access."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-863"],
        category="incorrect_authorization",
        patterns={
            "java": LanguagePattern(
                r'repository\.find(?:ById|One)\s*\(\s*(?:id|request\.getParameter)',
            ),
        },
        fix_suggestion="Add ownership verification: verify user has access to the resource before returning.",
        false_positive_patterns=[r'getOwner', r'getUserId', r'hasAccess', r'isAuthorized'],
    ),
]


# =============================================================================
# CWE-287: Improper Authentication - 6 rules
# =============================================================================

IMPROPER_AUTH_RULES: List[AuthLogicRule] = [
    # AUTH-287-001: Hardcoded credentials
    AuthLogicRule(
        id="AUTH-287-001",
        title="Hardcoded password in authentication",
        description=(
            "Hardcoded passwords in authentication logic are easily discoverable and cannot be changed without code deployment."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-287", "CWE-798"],
        category="improper_authentication",
        patterns={
            "python": LanguagePattern(
                r'(?:password|passwd|pwd)\s*==\s*["\'][^"\']{4,}["\']',
            ),
            "javascript": LanguagePattern(
                r'(?:password|passwd|pwd)\s*===?\s*["\'][^"\']{4,}["\']',
            ),
            "java": LanguagePattern(
                r'(?:password|passwd|pwd)\.equals\s*\(\s*["\'][^"\']{4,}["\']',
            ),
            "php": LanguagePattern(
                r'\$(?:password|passwd|pwd)\s*===?\s*["\'][^"\']{4,}["\']',
            ),
        },
        fix_suggestion="Store hashed passwords in database. Use bcrypt/argon2 for password verification.",
    ),

    # AUTH-287-002: Weak password comparison
    AuthLogicRule(
        id="AUTH-287-002",
        title="Plain text password comparison",
        description=(
            "Comparing passwords in plain text instead of using secure hashing indicates passwords are stored insecurely."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-287", "CWE-256"],
        category="improper_authentication",
        patterns={
            "python": LanguagePattern(
                r'(?:user|account)\.password\s*==\s*(?:password|request|input)',
            ),
            "javascript": LanguagePattern(
                r'(?:user|account)\.password\s*===?\s*(?:password|req\.|body)',
            ),
            "java": LanguagePattern(
                r'(?:user|account)\.getPassword\(\)\.equals\s*\(\s*(?:password|request)',
            ),
        },
        fix_suggestion="Never compare passwords directly. Use bcrypt.compare() or equivalent secure comparison.",
    ),

    # AUTH-287-003: Missing brute force protection
    AuthLogicRule(
        id="AUTH-287-003",
        title="Login endpoint without rate limiting",
        description=(
            "Authentication endpoints without rate limiting are vulnerable to brute force attacks."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-287", "CWE-307"],
        category="improper_authentication",
        patterns={
            "python": LanguagePattern(
                r'def\s+login.*\n.*(?:check_password|authenticate)',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Implement rate limiting, account lockout, or CAPTCHA after failed attempts.",
        context_keywords=["login", "authenticate", "signin"],
        require_context=True,
        false_positive_patterns=[r'rate_limit', r'throttle', r'RateLimiter', r'lockout'],
    ),

    # AUTH-287-004: JWT without expiration
    AuthLogicRule(
        id="AUTH-287-004",
        title="JWT token without expiration",
        description=(
            "JWT tokens without expiration remain valid indefinitely, increasing the risk of token theft."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-287", "CWE-613"],
        category="improper_authentication",
        patterns={
            "python": LanguagePattern(
                r'jwt\.encode\s*\([^)]*\)(?!.*exp)',
            ),
            "javascript": LanguagePattern(
                r'jwt\.sign\s*\([^)]+\)(?!.*expiresIn)',
            ),
        },
        fix_suggestion="Always set token expiration: jwt.encode(payload, key, algorithm='HS256'), with 'exp' in payload.",
        false_positive_patterns=[r'exp', r'expiresIn', r'expiration'],
    ),

    # AUTH-287-005: Weak JWT secret
    AuthLogicRule(
        id="AUTH-287-005",
        title="Weak or hardcoded JWT secret",
        description=(
            "JWT signed with weak or hardcoded secrets can be forged by attackers."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-287", "CWE-321"],
        category="improper_authentication",
        patterns={
            "python": LanguagePattern(
                r'jwt\.(?:encode|decode)\s*\([^,]+,\s*["\'][^"\']{1,20}["\']',
            ),
            "javascript": LanguagePattern(
                r'jwt\.(?:sign|verify)\s*\([^,]+,\s*["\'][^"\']{1,20}["\']',
            ),
        },
        fix_suggestion="Use a long, random secret from environment variables: process.env.JWT_SECRET",
    ),

    # AUTH-287-006: Session fixation vulnerability
    AuthLogicRule(
        id="AUTH-287-006",
        title="Session not regenerated after authentication",
        description=(
            "Not regenerating session ID after login enables session fixation attacks."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-287", "CWE-384"],
        category="improper_authentication",
        patterns={
            "python": LanguagePattern(
                r'def\s+login.*session\[["\']user',
                flags=re.MULTILINE | re.DOTALL,
            ),
            "php": LanguagePattern(
                r'\$_SESSION\[["\']user.*=.*(?!session_regenerate_id)',
            ),
        },
        fix_suggestion="Regenerate session after authentication: session.regenerate() or session_regenerate_id(true)",
        false_positive_patterns=[r'regenerate', r'session_regenerate_id'],
    ),
]


# =============================================================================
# CWE-269: Improper Privilege Management - 4 rules
# =============================================================================

PRIVILEGE_MGMT_RULES: List[AuthLogicRule] = [
    # AUTH-269-001: Privilege escalation via mass assignment
    AuthLogicRule(
        id="AUTH-269-001",
        title="Mass assignment allows role modification",
        description=(
            "Accepting user input for role/admin fields enables privilege escalation via mass assignment."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-269", "CWE-915"],
        category="privilege_management",
        patterns={
            "python": LanguagePattern(
                r'\.update\s*\(\s*\*\*(?:request|kwargs|data)',
            ),
            "javascript": LanguagePattern(
                r'Object\.assign\s*\(\s*\w+,\s*(?:req\.body|body|data)\s*\)',
            ),
            "ruby": LanguagePattern(
                r'\.update\s*\(\s*params(?:\[:\w+\])?\s*\)',
            ),
        },
        fix_suggestion="Explicitly whitelist allowed fields: user.update(name=data['name'], email=data['email'])",
        false_positive_patterns=[r'permit', r'slice', r'pick', r'whitelist', r'allowlist'],
    ),

    # AUTH-269-002: Self-assigned privilege
    AuthLogicRule(
        id="AUTH-269-002",
        title="User can modify own privileges",
        description=(
            "Users should not be able to modify their own role or permission level."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-269"],
        category="privilege_management",
        patterns={
            "python": LanguagePattern(
                r'current_user\.(?:role|is_admin|permissions?)\s*=',
            ),
            "javascript": LanguagePattern(
                r'req\.user\.(?:role|isAdmin|permissions?)\s*=',
            ),
        },
        fix_suggestion="Only allow admins to modify user privileges. Verify modifier has higher privilege level.",
    ),

    # AUTH-269-003: Elevated privileges not dropped
    AuthLogicRule(
        id="AUTH-269-003",
        title="Elevated privileges not properly dropped",
        description=(
            "Code running with elevated privileges that doesn't drop them after the privileged operation."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-269", "CWE-271"],
        category="privilege_management",
        patterns={
            "python": LanguagePattern(
                r'os\.(?:setuid|seteuid|setreuid)\s*\(\s*0\s*\)',
            ),
            "c": LanguagePattern(
                r'setuid\s*\(\s*0\s*\)',
            ),
        },
        fix_suggestion="Drop privileges as soon as they're no longer needed. Use setuid() to non-privileged user.",
    ),

    # AUTH-269-004: Default admin account
    AuthLogicRule(
        id="AUTH-269-004",
        title="Default admin credentials in code",
        description=(
            "Default admin accounts with known credentials are a common attack vector."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-269", "CWE-1188"],
        category="privilege_management",
        patterns={
            "python": LanguagePattern(
                r'(?:admin|root|superuser).*(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']+["\']',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
            "javascript": LanguagePattern(
                r'(?:admin|root|superuser).*(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']+["\']',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Never hardcode admin credentials. Force admin password change on first login.",
    ),
]


# =============================================================================
# CWE-306: Missing Authentication for Critical Function - 4 rules
# =============================================================================

MISSING_AUTH_RULES: List[AuthLogicRule] = [
    # AUTH-306-001: Admin endpoint without authentication
    AuthLogicRule(
        id="AUTH-306-001",
        title="Admin endpoint without authentication",
        description=(
            "Administrative endpoints must always require authentication. Unauthenticated admin access is critical."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-306"],
        category="missing_authentication",
        patterns={
            "python": LanguagePattern(
                r'@.*(?:route|api)\s*\([^)]*["\']\/admin',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Add authentication decorator: @login_required before all admin routes.",
        false_positive_patterns=[r'@login_required', r'@admin_required', r'@requires_auth'],
    ),

    # AUTH-306-002: Password reset without verification
    AuthLogicRule(
        id="AUTH-306-002",
        title="Password reset without identity verification",
        description=(
            "Password reset functionality that doesn't properly verify user identity."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-306", "CWE-640"],
        category="missing_authentication",
        patterns={
            "python": LanguagePattern(
                r'def\s+(?:reset_password|password_reset|change_password).*\n.*(?:user\.password|set_password)',
                flags=re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Verify identity with secure token, old password, or multi-factor authentication.",
        false_positive_patterns=[r'token', r'verify', r'old_password', r'current_password'],
    ),

    # AUTH-306-003: API endpoint without token validation
    AuthLogicRule(
        id="AUTH-306-003",
        title="API endpoint without token validation",
        description=(
            "API endpoints that don't validate authentication tokens allow unauthorized access."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-306"],
        category="missing_authentication",
        patterns={
            "javascript": LanguagePattern(
                r'app\.(?:get|post|put|delete)\s*\(\s*[\'"]\/api\/',
            ),
            "typescript": LanguagePattern(
                r'app\.(?:get|post|put|delete)\s*\(\s*[\'"]\/api\/',
            ),
        },
        fix_suggestion="Add authentication middleware to validate tokens on all API endpoints.",
        false_positive_patterns=[r'auth', r'token', r'jwt', r'verify', r'passport'],
    ),

    # AUTH-306-004: Database admin without authentication
    AuthLogicRule(
        id="AUTH-306-004",
        title="Database admin interface exposed",
        description=(
            "Database administration endpoints or interfaces without authentication protection."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-306"],
        category="missing_authentication",
        patterns={
            "python": LanguagePattern(
                r'(?:route|endpoint).*(?:phpmyadmin|adminer|pgadmin|dbadmin)',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        fix_suggestion="Never expose database admin interfaces publicly. Require authentication and IP restrictions.",
    ),
]


# =============================================================================
# CWE-20: Improper Input Validation (Auth Context) - 4 rules
# =============================================================================

INPUT_VALIDATION_RULES: List[AuthLogicRule] = [
    # AUTH-20-001: User ID from client trusted
    AuthLogicRule(
        id="AUTH-20-001",
        title="User ID from client used without verification",
        description=(
            "Trusting user ID from client input instead of server session allows identity spoofing."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-20", "CWE-639"],
        category="input_validation",
        patterns={
            "python": LanguagePattern(
                r'user_id\s*=\s*(?:request\.|int\(request)',
            ),
            "javascript": LanguagePattern(
                r'userId\s*=\s*req\.(?:body|params|query)\.(?:userId|user_id)',
            ),
        },
        fix_suggestion="Get user ID from authenticated session: user_id = current_user.id, not from request.",
    ),

    # AUTH-20-002: Role from client trusted
    AuthLogicRule(
        id="AUTH-20-002",
        title="Role/permission from client input",
        description=(
            "Accepting role or permission values from client allows privilege escalation."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-20", "CWE-269"],
        category="input_validation",
        patterns={
            "python": LanguagePattern(
                r'role\s*=\s*request\.(?:args|form|json|data)',
            ),
            "javascript": LanguagePattern(
                r'role\s*=\s*req\.(?:body|params|query)\.role',
            ),
        },
        fix_suggestion="Never accept role from client. Get role from authenticated user session.",
    ),

    # AUTH-20-003: Unvalidated redirect URL
    AuthLogicRule(
        id="AUTH-20-003",
        title="Unvalidated redirect URL",
        description=(
            "Redirecting to a URL from user input without validation enables open redirect attacks. "
            "Attackers can use this for phishing by redirecting to malicious sites."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-20", "CWE-601"],
        category="input_validation",
        patterns={
            "python": LanguagePattern(
                r'redirect\s*\(\s*(?:request\.args\.get|request\.form\.get)\s*\([\'"](?:next|url|redirect|return)',
            ),
            "javascript": LanguagePattern(
                r'res\.redirect\s*\(\s*req\.(?:query|body)\.(?:next|url|redirect|return)',
            ),
            "php": LanguagePattern(
                r'header\s*\(\s*[\'"]Location:\s*[\'"]?\s*\.\s*\$_(?:GET|POST)\[',
            ),
        },
        fix_suggestion="Validate redirect URL is relative or matches allowlist of domains.",
        false_positive_patterns=[r'url_for', r'is_safe_url', r'validate_redirect'],
    ),

    # AUTH-20-004: Email not verified before password reset
    AuthLogicRule(
        id="AUTH-20-004",
        title="Password reset without email verification",
        description=(
            "Password reset that doesn't verify the email belongs to the user making the request."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-20", "CWE-640"],
        category="input_validation",
        patterns={
            "python": LanguagePattern(
                r'email\s*=\s*request.*reset.*password',
                flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
            ),
        },
        fix_suggestion="Send reset link to email on file. Verify token before allowing password change.",
        false_positive_patterns=[r'send.*email', r'token', r'verify'],
    ),
]


# =============================================================================
# ALL RULES COMBINED
# =============================================================================

ALL_AUTH_LOGIC_RULES: List[AuthLogicRule] = (
    MISSING_AUTHZ_RULES +
    INCORRECT_AUTHZ_RULES +
    IMPROPER_AUTH_RULES +
    PRIVILEGE_MGMT_RULES +
    MISSING_AUTH_RULES +
    INPUT_VALIDATION_RULES
)


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class AuthLogicDetector(BaseScanner):
    """
    Detects authentication and authorization vulnerabilities.

    Covers CWE weaknesses related to authentication and authorization:
    - CWE-862: Missing Authorization
    - CWE-863: Incorrect Authorization
    - CWE-287: Improper Authentication
    - CWE-269: Improper Privilege Management
    - CWE-306: Missing Authentication for Critical Function
    - CWE-20: Improper Input Validation (auth context)

    Multi-language: Python, JavaScript, TypeScript, Java, C#, PHP, Ruby, Go
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in ALL_AUTH_LOGIC_RULES:
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
        return ScannerType.AUTH_LOGIC

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
        """Execute authentication/authorization logic scan."""
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

                for rule in ALL_AUTH_LOGIC_RULES:
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
                            id=f"authlogic-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}", "auth_logic", rule.category},
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
        for rule in ALL_AUTH_LOGIC_RULES:
            if rule.category not in categories:
                categories[rule.category] = 0
            categories[rule.category] += 1

        cwe_coverage = set()
        for rule in ALL_AUTH_LOGIC_RULES:
            cwe_coverage.update(rule.cwe_ids)

        return {
            "total_rules": len(ALL_AUTH_LOGIC_RULES),
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
                for rule in ALL_AUTH_LOGIC_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": sorted(cwe_coverage),
            "category_descriptions": {
                "missing_authorization": "CWE-862: Missing Authorization",
                "incorrect_authorization": "CWE-863: Incorrect Authorization",
                "improper_authentication": "CWE-287: Improper Authentication",
                "privilege_management": "CWE-269: Improper Privilege Management",
                "missing_authentication": "CWE-306: Missing Authentication for Critical Function",
                "input_validation": "CWE-20: Improper Input Validation (auth context)",
            },
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_auth_logic_detector() -> AuthLogicDetector:
    """Factory function to create auth logic detector."""
    return AuthLogicDetector()
