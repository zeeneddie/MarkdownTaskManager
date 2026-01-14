"""
Custom Classic ASP/VBScript Security Scanner.

A pattern-based scanner for Classic ASP code that detects
CWE Top 25 vulnerabilities in legacy VBScript applications.

This scanner is necessary because no open-source SAST tools
support Classic ASP (VBScript) properly.
"""

from pathlib import Path
from typing import Dict, Any, List, Set

from ..models.findings import ScannerType, Severity
from .base import CustomPatternScanner


class ClassicASPScanner(CustomPatternScanner):
    """
    Custom security scanner for Classic ASP (VBScript).

    Detects CWE Top 25 vulnerabilities:
    - CWE-89: SQL Injection
    - CWE-79: Cross-Site Scripting (XSS)
    - CWE-78: OS Command Injection
    - CWE-22: Path Traversal
    - CWE-94: Code Injection
    - CWE-287: Improper Authentication
    - CWE-798: Hardcoded Credentials
    - CWE-200: Information Exposure
    - CWE-434: Unrestricted File Upload
    - And more...
    """

    SUPPORTED_LANGUAGES = {"asp", "vbscript"}
    SUPPORTED_EXTENSIONS = {".asp", ".asa", ".inc", ".vbs"}

    # Security rules for Classic ASP
    SECURITY_RULES = [
        # =================================================================
        # CWE-89: SQL Injection
        # =================================================================
        {
            "id": "ASP-CWE-89-001",
            "pattern": r'(?:Execute|\.Execute)\s*\(\s*["\']?\s*(?:SELECT|INSERT|UPDATE|DELETE|EXEC)\s+.*?\s*&\s*(?:Request|Session)\s*\(',
            "severity": Severity.CRITICAL,
            "title": "SQL Injection via Request/Session concatenation",
            "description": "SQL query built using string concatenation with user input from Request or Session. Use parameterized queries instead.",
            "cwe_ids": ["CWE-89"],
            "category": "injection",
            "fix_suggestion": "Use ADODB.Command with Parameters collection for parameterized queries."
        },
        {
            "id": "ASP-CWE-89-002",
            "pattern": r'(?:Execute|ExecuteNonQuery|Open)\s*\([^)]*["\']?\s*(?:SELECT|INSERT|UPDATE|DELETE)\s+[^"\']*\s*["\']?\s*&',
            "severity": Severity.CRITICAL,
            "title": "SQL Injection via string concatenation",
            "description": "SQL query constructed using string concatenation. This pattern is vulnerable to SQL injection attacks.",
            "cwe_ids": ["CWE-89"],
            "category": "injection",
            "fix_suggestion": "Replace string concatenation with parameterized queries using ADODB.Command."
        },
        {
            "id": "ASP-CWE-89-003",
            "pattern": r'sql\s*=\s*["\'][^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\']\s*&\s*',
            "severity": Severity.HIGH,
            "title": "SQL string built with concatenation",
            "description": "Variable containing SQL is built using string concatenation, indicating potential SQL injection.",
            "cwe_ids": ["CWE-89"],
            "category": "injection",
            "fix_suggestion": "Use parameterized queries or stored procedures."
        },

        # =================================================================
        # CWE-79: Cross-Site Scripting (XSS)
        # =================================================================
        {
            "id": "ASP-CWE-79-001",
            "pattern": r'Response\.Write\s*\(\s*Request(?:\.(?:QueryString|Form|Cookies|ServerVariables))?\s*\(',
            "severity": Severity.HIGH,
            "title": "XSS via direct Response.Write of Request data",
            "description": "User input from Request is directly written to response without encoding, enabling XSS attacks.",
            "cwe_ids": ["CWE-79"],
            "category": "xss",
            "fix_suggestion": "Use Server.HTMLEncode() to encode user input before writing to response."
        },
        {
            "id": "ASP-CWE-79-002",
            "pattern": r'<%\s*=\s*Request(?:\.(?:QueryString|Form|Cookies))?\s*\(',
            "severity": Severity.HIGH,
            "title": "XSS via inline output of Request data",
            "description": "User input directly output using <%= %> shorthand without encoding.",
            "cwe_ids": ["CWE-79"],
            "category": "xss",
            "fix_suggestion": "Use <%= Server.HTMLEncode(Request(...)) %> to encode output."
        },
        {
            "id": "ASP-CWE-79-003",
            "pattern": r'document\.write\s*\([^)]*(?:Request|location\.search|location\.hash)',
            "severity": Severity.HIGH,
            "title": "DOM-based XSS",
            "description": "Client-side script writes user-controlled data to DOM without sanitization.",
            "cwe_ids": ["CWE-79"],
            "category": "xss",
            "fix_suggestion": "Sanitize and encode user input before DOM manipulation."
        },

        # =================================================================
        # CWE-78: OS Command Injection
        # =================================================================
        {
            "id": "ASP-CWE-78-001",
            "pattern": r'(?:WScript\.Shell|Shell\.Application).*\.(?:Run|Exec)\s*\([^)]*Request',
            "severity": Severity.CRITICAL,
            "title": "Command Injection via WScript.Shell",
            "description": "Shell command executed with user input, enabling command injection attacks.",
            "cwe_ids": ["CWE-78"],
            "category": "injection",
            "fix_suggestion": "Avoid executing shell commands with user input. If necessary, use strict allowlists."
        },
        {
            "id": "ASP-CWE-78-002",
            "pattern": r'Shell\s*=\s*CreateObject\s*\(\s*["\']WScript\.Shell["\']\s*\)',
            "severity": Severity.MEDIUM,
            "title": "WScript.Shell object creation",
            "description": "WScript.Shell object created - review for command injection vulnerabilities.",
            "cwe_ids": ["CWE-78"],
            "category": "injection",
            "fix_suggestion": "Audit all uses of this Shell object for user input handling."
        },

        # =================================================================
        # CWE-22: Path Traversal
        # =================================================================
        {
            "id": "ASP-CWE-22-001",
            "pattern": r'Server\.MapPath\s*\([^)]*Request(?:\.(?:QueryString|Form))?\s*\(',
            "severity": Severity.HIGH,
            "title": "Path Traversal via Server.MapPath",
            "description": "File path constructed using user input, enabling directory traversal attacks.",
            "cwe_ids": ["CWE-22"],
            "category": "path_traversal",
            "fix_suggestion": "Validate and sanitize file paths. Use allowlists for permitted directories."
        },
        {
            "id": "ASP-CWE-22-002",
            "pattern": r'(?:FileSystemObject|FSO).*\.(?:OpenTextFile|GetFile|FileExists|FolderExists)\s*\([^)]*Request',
            "severity": Severity.HIGH,
            "title": "File access with user-controlled path",
            "description": "File system operation uses user input in path, enabling path traversal.",
            "cwe_ids": ["CWE-22"],
            "category": "path_traversal",
            "fix_suggestion": "Sanitize paths and restrict to specific directories."
        },

        # =================================================================
        # CWE-94: Code Injection
        # =================================================================
        {
            "id": "ASP-CWE-94-001",
            "pattern": r'(?:Execute|ExecuteGlobal|Eval)\s*\([^)]*Request',
            "severity": Severity.CRITICAL,
            "title": "Code Injection via Execute/Eval",
            "description": "Dynamic code execution with user input enables arbitrary code injection.",
            "cwe_ids": ["CWE-94"],
            "category": "injection",
            "fix_suggestion": "Never execute user-supplied code. Refactor to use safe alternatives."
        },
        {
            "id": "ASP-CWE-94-002",
            "pattern": r'(?:Execute|ExecuteGlobal|Eval)\s*\(\s*[^)]+\s*&',
            "severity": Severity.HIGH,
            "title": "Dynamic code execution with concatenation",
            "description": "Execute/Eval called with string concatenation, potential code injection vector.",
            "cwe_ids": ["CWE-94"],
            "category": "injection",
            "fix_suggestion": "Avoid dynamic code execution entirely."
        },

        # =================================================================
        # CWE-798: Hardcoded Credentials
        # =================================================================
        {
            "id": "ASP-CWE-798-001",
            "pattern": r'(?:password|passwd|pwd|secret|api_?key|apikey)\s*=\s*["\'][^"\']{4,}["\']',
            "severity": Severity.HIGH,
            "title": "Hardcoded password/secret",
            "description": "Credentials appear to be hardcoded in source code.",
            "cwe_ids": ["CWE-798"],
            "category": "credentials",
            "fix_suggestion": "Store credentials in secure configuration or environment variables."
        },
        {
            "id": "ASP-CWE-798-002",
            "pattern": r'(?:ConnectionString|Provider)\s*=\s*["\'][^"\']*(?:password|pwd)\s*=\s*[^;"\'\s]+',
            "severity": Severity.HIGH,
            "title": "Hardcoded database credentials",
            "description": "Database connection string contains hardcoded credentials.",
            "cwe_ids": ["CWE-798"],
            "category": "credentials",
            "fix_suggestion": "Use Windows authentication or secure credential storage."
        },

        # =================================================================
        # CWE-200: Information Exposure
        # =================================================================
        {
            "id": "ASP-CWE-200-001",
            "pattern": r'On\s+Error\s+Resume\s+Next',
            "severity": Severity.MEDIUM,
            "title": "Error suppression enabled",
            "description": "Error handling suppresses errors, potentially hiding security issues.",
            "cwe_ids": ["CWE-200", "CWE-209"],
            "category": "error_handling",
            "fix_suggestion": "Implement proper error handling and logging."
        },
        {
            "id": "ASP-CWE-200-002",
            "pattern": r'Response\.Write\s*\(\s*Err\.(?:Description|Number|Source)',
            "severity": Severity.MEDIUM,
            "title": "Error details exposed to user",
            "description": "Detailed error information written to response, aiding attackers.",
            "cwe_ids": ["CWE-200", "CWE-209"],
            "category": "error_handling",
            "fix_suggestion": "Log errors server-side; show generic messages to users."
        },

        # =================================================================
        # CWE-434: Unrestricted File Upload
        # =================================================================
        {
            "id": "ASP-CWE-434-001",
            "pattern": r'\.SaveAs\s*\([^)]*Request',
            "severity": Severity.HIGH,
            "title": "File upload with user-controlled filename",
            "description": "File saved with user-provided filename without proper validation.",
            "cwe_ids": ["CWE-434"],
            "category": "file_upload",
            "fix_suggestion": "Validate file extensions, use generated filenames, scan uploads."
        },
        {
            "id": "ASP-CWE-434-002",
            "pattern": r'(?:Upload|FileUpload|BinaryRead).*(?:\.asp|\.asa|\.inc)',
            "severity": Severity.CRITICAL,
            "title": "Potential ASP file upload",
            "description": "File upload may allow executable ASP files to be uploaded.",
            "cwe_ids": ["CWE-434"],
            "category": "file_upload",
            "fix_suggestion": "Block executable file extensions (.asp, .asa, .exe, etc.)."
        },

        # =================================================================
        # CWE-352: Cross-Site Request Forgery (CSRF)
        # =================================================================
        {
            "id": "ASP-CWE-352-001",
            "pattern": r'If\s+Request\.Form\s*\(\s*["\'][^"\']+["\']\s*\)\s*<>\s*["\']["\']\s*Then',
            "severity": Severity.MEDIUM,
            "title": "Form processing without CSRF protection",
            "description": "Form submission processed without apparent CSRF token validation.",
            "cwe_ids": ["CWE-352"],
            "category": "csrf",
            "fix_suggestion": "Implement CSRF tokens for all state-changing operations."
        },

        # =================================================================
        # CWE-287: Improper Authentication
        # =================================================================
        {
            "id": "ASP-CWE-287-001",
            "pattern": r'Session\s*\(\s*["\'](?:user|login|auth|logged)[^"\']*["\']\s*\)\s*=\s*(?:True|1|["\'])',
            "severity": Severity.MEDIUM,
            "title": "Simple session-based authentication",
            "description": "Authentication relies on simple session flag without proper validation.",
            "cwe_ids": ["CWE-287"],
            "category": "authentication",
            "fix_suggestion": "Implement robust authentication with proper session management."
        },

        # =================================================================
        # CWE-311: Missing Encryption
        # =================================================================
        {
            "id": "ASP-CWE-311-001",
            "pattern": r'Response\.(?:Cookies|AddHeader)\s*\([^)]*\)\s*(?!.*(?:Secure|HttpOnly))',
            "severity": Severity.MEDIUM,
            "title": "Cookie without security flags",
            "description": "Cookie set without Secure or HttpOnly flags.",
            "cwe_ids": ["CWE-311", "CWE-614"],
            "category": "cryptography",
            "fix_suggestion": "Add Secure and HttpOnly flags to sensitive cookies."
        },

        # =================================================================
        # CWE-601: Open Redirect
        # =================================================================
        {
            "id": "ASP-CWE-601-001",
            "pattern": r'Response\.Redirect\s*\(\s*Request(?:\.(?:QueryString|Form))?\s*\(',
            "severity": Severity.MEDIUM,
            "title": "Open Redirect vulnerability",
            "description": "Redirect URL taken directly from user input, enabling phishing attacks.",
            "cwe_ids": ["CWE-601"],
            "category": "redirect",
            "fix_suggestion": "Validate redirect URLs against an allowlist of permitted destinations."
        },
    ]

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.CUSTOM_ASP

    @property
    def supported_languages(self) -> Set[str]:
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_extensions(self) -> Set[str]:
        return self.SUPPORTED_EXTENSIONS

    @property
    def rules(self) -> List[Dict[str, Any]]:
        return self.SECURITY_RULES


def create_asp_scanner() -> ClassicASPScanner:
    """Factory function to create Classic ASP scanner."""
    return ClassicASPScanner()
