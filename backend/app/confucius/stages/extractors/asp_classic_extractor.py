"""
ASP Classic Journey Extractor.

Extracts user journey data from ASP Classic applications including:
- VBScript-based ASP pages
- Include files
- Session-based authentication
"""

import re
from typing import Dict, Any, List
from .base import BaseJourneyExtractor


class AspClassicExtractor(BaseJourneyExtractor):
    """
    Extract user journey data from ASP Classic applications.

    Analyzes:
    - Session("UserRole") checks
    - .asp files for screens
    - Include files for navigation
    - Response.Redirect for flows
    - Server.Execute for includes
    - Database role tables
    """

    def __init__(self):
        """Initialize extractor."""
        super().__init__()
        self.supported_extensions = [".asp", ".inc", ".asa"]

    def supports_stack(self, tech_stack: List[str]) -> bool:
        """Check if this extractor supports the given tech stack."""
        asp_classic_identifiers = [
            "asp", "asp classic", "classic asp", "vbscript",
            "asp3", "asp 3.0", "iis classic"
        ]
        return any(
            t.lower() in asp_classic_identifiers
            for t in tech_stack
        )

    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract user journey data from ASP Classic files."""
        result = self._get_empty_result()

        asp_files = self._find_files_by_extension(files, [".asp", ".inc", ".asa"])

        for f in asp_files:
            self._extract_from_asp(f, result)

        # Build navigation graph from redirects
        self._build_navigation_graph(result)

        return result

    def _extract_from_asp(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from ASP Classic file."""
        content = file.get("content", "")
        path = file.get("path", "")

        if not content:
            return

        # Determine file type
        is_include = path.lower().endswith(".inc")
        is_global = "global.asa" in path.lower()

        # Extract session role checks
        self._extract_session_role_checks(content, path, result)

        # Extract redirects for navigation
        self._extract_redirects(content, path, result)

        # Extract includes
        self._extract_includes(content, path, result)

        # Extract screens (skip include files)
        if not is_include and not is_global:
            self._extract_screen(content, path, result)

        # Extract API-like endpoints (if it's a handler)
        if self._is_ajax_handler(content):
            self._extract_ajax_endpoint(content, path, result)

        # Extract database role queries
        self._extract_db_role_queries(content, path, result)

    def _extract_session_role_checks(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract Session-based role checks."""
        role_patterns = [
            # Session("UserRole") = "Admin"
            r'Session\s*\(\s*"(?:User)?Role"\s*\)\s*=\s*"(\w+)"',
            # Session("UserType") = "Customer"
            r'Session\s*\(\s*"(?:User)?Type"\s*\)\s*=\s*"(\w+)"',
            # If Session("UserRole") = "Admin" Then
            r'If\s+Session\s*\(\s*"(?:User)?Role"\s*\)\s*=\s*"(\w+)"',
            # Case "Admin"
            r'Select\s+Case\s+Session\s*\([^)]+\).*?Case\s+"(\w+)"',
            # CheckRole("Admin")
            r'CheckRole\s*\(\s*"(\w+)"\s*\)',
            # IsInRole("Admin")
            r'IsInRole\s*\(\s*"(\w+)"\s*\)',
            # Session("Rol")
            r'Session\s*\(\s*"Rol"\s*\)\s*=\s*"(\w+)"',
            # Session("Gebruikerstype")
            r'Session\s*\(\s*"Gebruikerstype"\s*\)\s*=\s*"(\w+)"',
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for role in matches:
                self._add_role(role, path, "session_check", result)

        # Also extract role assignment
        assignment_patterns = [
            r'Session\s*\(\s*"(?:User)?Role"\s*\)\s*=\s*(\w+)',
            r'Session\s*\(\s*"Rol"\s*\)\s*=\s*(\w+)',
        ]

        for pattern in assignment_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for role_var in matches:
                # Check if it's a string literal we missed
                if role_var.startswith('"') or role_var.startswith("'"):
                    role = role_var.strip("\"'")
                    self._add_role(role, path, "session_assignment", result)

    def _extract_redirects(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract Response.Redirect and Server.Transfer for navigation."""
        redirect_patterns = [
            # Response.Redirect "page.asp"
            r'Response\.Redirect\s+["\'"]([^"\']+)["\']',
            # Response.Redirect("page.asp")
            r'Response\.Redirect\s*\(\s*["\'"]([^"\']+)["\']',
            # Server.Transfer "page.asp"
            r'Server\.Transfer\s+["\'"]([^"\']+)["\']',
            # Server.Transfer("page.asp")
            r'Server\.Transfer\s*\(\s*["\'"]([^"\']+)["\']',
            # Server.Execute "page.asp"
            r'Server\.Execute\s+["\'"]([^"\']+)["\']',
            # Server.Execute("page.asp")
            r'Server\.Execute\s*\(\s*["\'"]([^"\']+)["\']',
        ]

        for pattern in redirect_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for target in matches:
                # Skip if it's a variable
                if not target.startswith("&") and not target.startswith("%"):
                    result["navigation"].append({
                        "from": path,
                        "to": target,
                        "type": "redirect",
                    })

    def _extract_includes(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract include files."""
        include_patterns = [
            # <!-- #include file="..." -->
            r'<!--\s*#include\s+file\s*=\s*["\'"]([^"\']+)["\'"]',
            # <!-- #include virtual="..." -->
            r'<!--\s*#include\s+virtual\s*=\s*["\'"]([^"\']+)["\'"]',
        ]

        for pattern in include_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for include_path in matches:
                result["navigation"].append({
                    "from": path,
                    "to": include_path,
                    "type": "include",
                })

    def _extract_screen(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract screen information from ASP page."""
        screen_name = self._extract_screen_name_from_path(path)
        screen_id = f"screen_{self._safe_hash(path)}"

        screen = {
            "id": screen_id,
            "name": screen_name,
            "display_name": self._generate_display_name(screen_name),
            "file_path": path,
            "screen_type": self._determine_screen_type(content),
            "requires_auth": self._detect_auth_requirement(content),
            "allowed_roles": self._extract_allowed_roles(content),
            "forms": [],
            "buttons": [],
            "input_fields": [],
            "navigation_links": [],
            "data_displays": [],
        }

        # Extract forms
        self._extract_forms(content, screen)

        # Extract input fields
        self._extract_input_fields(content, screen)

        # Extract buttons
        self._extract_buttons(content, screen)

        # Extract navigation links
        self._extract_navigation_links(content, path, screen, result)

        # Extract data displays
        self._extract_data_displays(content, screen)

        result["screens"].append(screen)

    def _extract_forms(self, content: str, screen: Dict[str, Any]):
        """Extract form information."""
        form_patterns = [
            # <form action="..." method="...">
            r'<form[^>]*action\s*=\s*["\'"]([^"\']*)["\'][^>]*method\s*=\s*["\'"](\w+)["\']',
            r'<form[^>]*method\s*=\s*["\'"](\w+)["\'][^>]*action\s*=\s*["\'"]([^"\']*)["\']',
            r'<form[^>]*action\s*=\s*["\'"]([^"\']*)["\'][^>]*>',
        ]

        for pattern in form_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        action = match[0] if "." in str(match[0]) else match[1]
                        method = match[1] if "." in str(match[0]) else match[0]
                        screen["forms"].append({
                            "action": action,
                            "method": method.upper() if method else "POST",
                        })
                else:
                    screen["forms"].append({
                        "action": match,
                        "method": "POST",
                    })

    def _extract_input_fields(self, content: str, screen: Dict[str, Any]):
        """Extract input field information."""
        input_patterns = [
            # <input name="..." type="...">
            r'<input[^>]*name\s*=\s*["\'"]([^"\']*)["\'][^>]*type\s*=\s*["\'"](\w+)["\']',
            r'<input[^>]*type\s*=\s*["\'"](\w+)["\'][^>]*name\s*=\s*["\'"]([^"\']*)["\']',
            r'<input[^>]*name\s*=\s*["\'"]([^"\']*)["\'][^>]*>',
            # <textarea name="...">
            r'<textarea[^>]*name\s*=\s*["\'"]([^"\']*)["\']',
            # <select name="...">
            r'<select[^>]*name\s*=\s*["\'"]([^"\']*)["\']',
        ]

        for pattern in input_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0] if not match[0].isalpha() or len(match[0]) > 2 else match[1]
                    field_type = match[1] if not match[0].isalpha() or len(match[0]) > 2 else match[0]
                else:
                    name = match
                    field_type = "text"

                if name and not name.startswith("<%"):
                    screen["input_fields"].append({
                        "name": name,
                        "type": field_type.lower() if field_type else "text",
                    })

    def _extract_buttons(self, content: str, screen: Dict[str, Any]):
        """Extract button information."""
        button_patterns = [
            # <input type="submit" value="...">
            r'<input[^>]*type\s*=\s*["\'"]submit["\'][^>]*value\s*=\s*["\'"]([^"\']*)["\']',
            r'<input[^>]*value\s*=\s*["\'"]([^"\']*)["\'][^>]*type\s*=\s*["\'"]submit["\']',
            # <input type="button" value="...">
            r'<input[^>]*type\s*=\s*["\'"]button["\'][^>]*value\s*=\s*["\'"]([^"\']*)["\']',
            # <button>...</button>
            r'<button[^>]*>([^<]+)</button>',
        ]

        for pattern in button_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                label = match.strip()
                if label and not label.startswith("<%"):
                    screen["buttons"].append({"label": label})

    def _extract_navigation_links(
        self,
        content: str,
        path: str,
        screen: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract navigation links."""
        link_patterns = [
            # <a href="...">...</a>
            r'<a[^>]*href\s*=\s*["\'"]([^"\']*)["\'][^>]*>([^<]*)</a>',
        ]

        for pattern in link_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                url, text = match
                if url and not url.startswith("<%") and not url.startswith("#"):
                    screen["navigation_links"].append(url)
                    result["navigation"].append({
                        "from": path,
                        "to": url,
                        "label": text.strip(),
                        "type": "link",
                    })

    def _extract_data_displays(self, content: str, screen: Dict[str, Any]):
        """Extract data display components."""
        # Check for recordset loops (common ASP pattern)
        if re.search(r'\.MoveNext|Do\s+(?:While|Until)\s+Not\s+\w+\.EOF', content, re.IGNORECASE):
            screen["data_displays"].append({
                "id": "recordset_list",
                "type": "list",
            })

        # Check for tables
        if re.search(r'<table[^>]*class\s*=\s*["\'][^"\']*(?:grid|data|list)[^"\']*["\']', content, re.IGNORECASE):
            screen["data_displays"].append({
                "id": "data_table",
                "type": "table",
            })

    def _extract_ajax_endpoint(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract AJAX-style endpoint from handler page."""
        # Check for Response.Write with JSON-like output
        if re.search(r'Response\.Write.*?{.*?}', content, re.DOTALL):
            result["api_endpoints"].append({
                "path": path,
                "method": "POST",
                "type": "ajax_handler",
            })

    def _extract_db_role_queries(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract role definitions from database queries."""
        db_patterns = [
            # SELECT * FROM Users WHERE Role = 'Admin'
            r"(?:WHERE|AND)\s+(?:\w+\.)?Role\s*=\s*'(\w+)'",
            r"(?:WHERE|AND)\s+(?:\w+\.)?UserType\s*=\s*'(\w+)'",
            # Stored procedure parameters
            r"@Role\s*=\s*'(\w+)'",
            r"@UserType\s*=\s*'(\w+)'",
        ]

        for pattern in db_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for role in matches:
                self._add_role(role, path, "db_query", result)

    def _extract_allowed_roles(self, content: str) -> List[str]:
        """Extract roles that are allowed to access this page."""
        roles = []

        # Check for role checks at the top of the file
        auth_check_pattern = (
            r'<%\s*'
            r'(?:If|Select\s+Case)\s+'
            r'Session\s*\(\s*["\'"](?:User)?Role["\']'
        )

        if re.search(auth_check_pattern, content[:500], re.IGNORECASE):
            # Extract the specific roles
            role_pattern = r'=\s*["\'"](\w+)["\']|Case\s+["\'"](\w+)["\']'
            matches = re.findall(role_pattern, content[:1000], re.IGNORECASE)
            for match in matches:
                role = match[0] or match[1]
                if role and role not in roles:
                    roles.append(role)

        return roles

    def _detect_auth_requirement(self, content: str) -> bool:
        """Detect if page requires authentication."""
        # Check for session checks near the top of the file
        auth_indicators = [
            r'Session\s*\(\s*["\'"](?:User)?(?:ID|Name|Role|Logged)',
            r'If\s+.*?Session\s*\(',
            r'CheckLogin',
            r'RequireLogin',
            r'IsAuthenticated',
        ]

        # Only check first 1000 chars (usually auth is at top)
        header = content[:1000]

        for pattern in auth_indicators:
            if re.search(pattern, header, re.IGNORECASE):
                return True

        return False

    def _is_ajax_handler(self, content: str) -> bool:
        """Check if file is an AJAX handler."""
        indicators = [
            r'Response\.ContentType\s*=\s*["\'"]application/json["\']',
            r'Response\.ContentType\s*=\s*["\'"]text/xml["\']',
            r'Response\.Write.*?JSON',
            r'XMLHTTP',
        ]

        for pattern in indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _build_navigation_graph(self, result: Dict[str, Any]):
        """Build navigation graph from extracted data."""
        # Group navigations by source
        nav_by_source: Dict[str, List[str]] = {}
        for nav in result["navigation"]:
            source = nav.get("from", "")
            target = nav.get("to", "")
            if source and target:
                if source not in nav_by_source:
                    nav_by_source[source] = []
                if target not in nav_by_source[source]:
                    nav_by_source[source].append(target)

        # Add to screens
        for screen in result["screens"]:
            path = screen.get("file_path", "")
            if path in nav_by_source:
                screen["navigation_targets"] = nav_by_source[path]

    def _add_role(
        self,
        role: str,
        source: str,
        check_type: str,
        result: Dict[str, Any],
    ):
        """Add role to result if not already present."""
        role = self._normalize_role_name(role)
        if not role:
            return

        # Add to roles list
        existing_roles = [r.get("name", "").upper() for r in result["roles"]]
        if role not in existing_roles:
            result["roles"].append({
                "name": role,
                "source": source,
                "check_type": check_type,
            })

        # Add auth check
        result["auth_checks"].append({
            "role": role,
            "file": source,
            "type": check_type,
        })

    def _generate_display_name(self, screen_name: str) -> str:
        """Generate human-readable display name from screen name."""
        # Convert underscores and hyphens to spaces
        name = screen_name.replace("_", " ").replace("-", " ")
        # Capitalize words
        name = " ".join(word.capitalize() for word in name.split())
        return name
