"""
ASP.NET Journey Extractor.

Extracts user journey data from ASP.NET applications including:
- MVC (.NET Framework and .NET Core)
- Web Forms
- Razor Pages
- Blazor
"""

import re
from typing import Dict, Any, List
from .base import BaseJourneyExtractor


class AspNetExtractor(BaseJourneyExtractor):
    """
    Extract user journey data from ASP.NET applications.

    Analyzes:
    - [Authorize] attributes and policies
    - Controllers and Actions
    - .aspx/.cshtml/.razor files for screens
    - Web.config/appsettings.json for roles
    - Route configurations
    - Form handlers and validators
    """

    def __init__(self):
        """Initialize extractor."""
        super().__init__()
        self.supported_extensions = [
            ".cs", ".aspx", ".cshtml", ".razor", ".config", ".json"
        ]

    def supports_stack(self, tech_stack: List[str]) -> bool:
        """Check if this extractor supports the given tech stack."""
        aspnet_identifiers = [
            "aspnet", "asp.net", "dotnet", ".net", "mvc",
            "razor", "blazor", "webforms", "web forms",
            "csharp", "c#"
        ]
        return any(
            t.lower() in aspnet_identifiers
            for t in tech_stack
        )

    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract user journey data from ASP.NET files."""
        result = self._get_empty_result()

        # Extract from controllers
        controllers = self._find_files_by_extension(files, [".cs"])
        for f in controllers:
            path = f.get("path", "")
            if "Controller" in path:
                self._extract_from_controller(f, result)
            elif "Service" in path or "Handler" in path:
                self._extract_from_service(f, result)

        # Extract from views
        views = self._find_files_by_extension(
            files, [".aspx", ".cshtml", ".razor"]
        )
        for f in views:
            self._extract_from_view(f, result)

        # Extract from configuration
        configs = [
            f for f in files
            if any(cfg in f.get("path", "").lower() for cfg in [
                "web.config", "appsettings.json", "startup.cs", "program.cs"
            ])
        ]
        for f in configs:
            self._extract_from_config(f, result)

        return result

    def _extract_from_controller(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from ASP.NET controller."""
        content = file.get("content", "")
        path = file.get("path", "")

        if not content:
            return

        # Extract controller name
        controller_match = re.search(r'class\s+(\w+)Controller', content)
        controller_name = controller_match.group(1) if controller_match else "Unknown"

        # Extract class-level authorization
        class_auth = self._extract_class_authorization(content, path, result)

        # Extract [Authorize] attributes on methods
        self._extract_authorize_attributes(content, path, result)

        # Extract API endpoints
        self._extract_api_endpoints(content, path, controller_name, result)

        # Extract action methods for navigation
        self._extract_action_methods(content, path, controller_name, result)

        # Extract role-based checks in code
        self._extract_inline_role_checks(content, path, result)

    def _extract_class_authorization(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ) -> List[str]:
        """Extract class-level authorization attributes."""
        class_roles = []

        # Find class-level Authorize attributes
        class_pattern = r'\[Authorize(?:\([^)]*Roles\s*=\s*"([^"]+)"[^)]*\))?\]\s*(?:\[.*?\]\s*)*public\s+class'
        matches = re.findall(class_pattern, content, re.DOTALL)

        for match in matches:
            if match:  # Has roles
                for role in match.split(","):
                    role = role.strip()
                    class_roles.append(role)
                    self._add_role(role, path, "class_authorize", result)

        return class_roles

    def _extract_authorize_attributes(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract [Authorize] attributes."""
        patterns = [
            # [Authorize(Roles = "Admin,Manager")]
            r'\[Authorize\s*\(\s*Roles\s*=\s*"([^"]+)"\s*\)\]',
            # [Authorize(Policy = "RequireAdmin")]
            r'\[Authorize\s*\(\s*Policy\s*=\s*"([^"]+)"\s*\)\]',
            # [Authorize("AdminPolicy")]
            r'\[Authorize\s*\(\s*"([^"]+)"\s*\)\]',
            # [AllowAnonymous] - mark as guest access
            r'\[AllowAnonymous\]',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match:  # Not AllowAnonymous
                    for role in match.split(","):
                        role = role.strip()
                        self._add_role(role, path, "authorize_attribute", result)
                else:
                    # AllowAnonymous found
                    self._add_role("ANONYMOUS", path, "allow_anonymous", result)

    def _extract_api_endpoints(
        self,
        content: str,
        path: str,
        controller_name: str,
        result: Dict[str, Any],
    ):
        """Extract API endpoints."""
        # HTTP method attributes
        http_patterns = [
            (r'\[Http(Get|Post|Put|Delete|Patch)\s*\("([^"]*)"\)\]', True),
            (r'\[Http(Get|Post|Put|Delete|Patch)\]', False),
            (r'\[Route\s*\("([^"]+)"\)\]', None),
        ]

        for pattern, has_route in http_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if has_route is True:
                    method, route = match
                    result["api_endpoints"].append({
                        "method": method.upper(),
                        "path": route,
                        "controller": controller_name,
                        "file": path,
                    })
                elif has_route is False:
                    method = match
                    result["api_endpoints"].append({
                        "method": method.upper(),
                        "path": f"/{controller_name}",
                        "controller": controller_name,
                        "file": path,
                    })
                elif has_route is None:
                    route = match
                    result["api_endpoints"].append({
                        "method": "ANY",
                        "path": route,
                        "controller": controller_name,
                        "file": path,
                    })

    def _extract_action_methods(
        self,
        content: str,
        path: str,
        controller_name: str,
        result: Dict[str, Any],
    ):
        """Extract action methods as potential navigation targets."""
        # Match public methods returning ActionResult/IActionResult/Task<>
        action_pattern = (
            r'public\s+(?:async\s+)?(?:Task<)?'
            r'(?:IActionResult|ActionResult|ViewResult|JsonResult|'
            r'RedirectResult|PartialViewResult|ContentResult)'
            r'[>\s]+(\w+)\s*\('
        )
        actions = re.findall(action_pattern, content)

        for action in actions:
            result["navigation"].append({
                "controller": controller_name,
                "action": action,
                "route": f"/{controller_name}/{action}",
                "file": path,
                "type": "action_method",
            })

    def _extract_inline_role_checks(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract role checks in code (User.IsInRole, etc.)."""
        patterns = [
            # User.IsInRole("Admin")
            r'User\.IsInRole\s*\(\s*"([^"]+)"\s*\)',
            # User.HasClaim("role", "Admin")
            r'User\.HasClaim\s*\(\s*"[^"]*"\s*,\s*"([^"]+)"\s*\)',
            # _authorizationService.AuthorizeAsync
            r'AuthorizeAsync\s*\([^,]+,\s*"([^"]+)"\s*\)',
            # ClaimTypes.Role
            r'ClaimTypes\.Role[^"]*"([^"]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self._add_role(match, path, "code_check", result)
                result["auth_checks"].append({
                    "role": match,
                    "file": path,
                    "type": "code_check",
                })

    def _extract_from_view(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from ASP.NET view."""
        content = file.get("content", "")
        path = file.get("path", "")

        if not content:
            return

        screen_name = self._extract_screen_name_from_path(path)
        screen_id = f"screen_{self._safe_hash(path)}"

        screen = {
            "id": screen_id,
            "name": screen_name,
            "display_name": self._generate_display_name(screen_name),
            "file_path": path,
            "screen_type": self._determine_screen_type(content),
            "requires_auth": self._detect_auth_requirement(content),
            "allowed_roles": [],
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

        # Extract data displays (grids, lists)
        self._extract_data_displays(content, screen)

        # Extract Razor authorization
        self._extract_razor_auth(content, path, screen, result)

        result["screens"].append(screen)

    def _extract_forms(self, content: str, screen: Dict[str, Any]):
        """Extract form information."""
        form_patterns = [
            # HTML forms
            r'<form[^>]*action="([^"]*)"[^>]*method="(\w+)"',
            r'<form[^>]*action="([^"]*)"[^>]*>',
            # Razor forms
            r'@using\s*\(\s*Html\.BeginForm\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"',
            r'<form[^>]*asp-action="([^"]*)"[^>]*asp-controller="([^"]*)"',
        ]

        for pattern in form_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        action, controller_or_method = match
                        screen["forms"].append({
                            "action": action,
                            "target": controller_or_method,
                        })
                else:
                    screen["forms"].append({"action": match})

    def _extract_input_fields(self, content: str, screen: Dict[str, Any]):
        """Extract input field information."""
        input_patterns = [
            # HTML inputs
            r'<input[^>]*(?:name|id)="([^"]*)"[^>]*type="(\w+)"',
            r'<input[^>]*type="(\w+)"[^>]*(?:name|id)="([^"]*)"',
            # ASP.NET controls
            r'<asp:TextBox[^>]*ID="([^"]*)"',
            r'<asp:DropDownList[^>]*ID="([^"]*)"',
            # Razor helpers
            r'@Html\.(?:TextBoxFor|EditorFor|DropDownListFor)\s*\(\s*[^,]+\s*=>\s*\w+\.(\w+)',
            r'<input[^>]*asp-for="([^"]*)"',
        ]

        for pattern in input_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0] if match[0] else match[1]
                    field_type = match[1] if match[0] else "text"
                else:
                    name = match
                    field_type = "text"

                screen["input_fields"].append({
                    "name": name,
                    "type": field_type,
                })

    def _extract_buttons(self, content: str, screen: Dict[str, Any]):
        """Extract button information."""
        button_patterns = [
            # HTML buttons
            r'<button[^>]*>([^<]+)</button>',
            r'<input[^>]*type="submit"[^>]*value="([^"]*)"',
            r'<input[^>]*value="([^"]*)"[^>]*type="submit"',
            # ASP.NET buttons
            r'<asp:Button[^>]*Text="([^"]*)"',
            r'<asp:LinkButton[^>]*Text="([^"]*)"',
        ]

        for pattern in button_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.strip():
                    screen["buttons"].append({
                        "label": match.strip(),
                    })

    def _extract_navigation_links(
        self,
        content: str,
        path: str,
        screen: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract navigation links."""
        link_patterns = [
            # Standard links
            r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>',
            # ASP.NET
            r'<asp:HyperLink[^>]*NavigateUrl="([^"]*)"[^>]*Text="([^"]*)"',
            # Razor
            r'@Html\.ActionLink\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"',
            r'<a[^>]*asp-action="([^"]*)"[^>]*asp-controller="([^"]*)"',
        ]

        for pattern in link_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    url, text = match[0], match[1]
                    screen["navigation_links"].append(url)
                    result["navigation"].append({
                        "from": path,
                        "to": url,
                        "label": text,
                        "type": "link",
                    })

    def _extract_data_displays(self, content: str, screen: Dict[str, Any]):
        """Extract data display components (grids, lists)."""
        display_patterns = [
            (r'<asp:GridView[^>]*ID="([^"]*)"', "grid"),
            (r'<asp:ListView[^>]*ID="([^"]*)"', "list"),
            (r'<asp:Repeater[^>]*ID="([^"]*)"', "repeater"),
            (r'<asp:DataList[^>]*ID="([^"]*)"', "datalist"),
            (r'<table[^>]*class="[^"]*(?:grid|table)[^"]*"', "table"),
        ]

        for pattern, display_type in display_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                screen["data_displays"].append({
                    "id": match if match else f"{display_type}_auto",
                    "type": display_type,
                })

    def _extract_razor_auth(
        self,
        content: str,
        path: str,
        screen: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract Razor authorization directives."""
        auth_patterns = [
            # @if (User.IsInRole("Admin"))
            r'User\.IsInRole\s*\(\s*"([^"]+)"\s*\)',
            # @attribute [Authorize(Roles = "Admin")]
            r'@attribute\s*\[Authorize\s*\(\s*Roles\s*=\s*"([^"]+)"\s*\)\]',
            # <AuthorizeView Roles="Admin">
            r'<AuthorizeView[^>]*Roles="([^"]+)"',
        ]

        for pattern in auth_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                for role in match.split(","):
                    role = role.strip()
                    if role not in screen["allowed_roles"]:
                        screen["allowed_roles"].append(role)
                    self._add_role(role, path, "view_check", result)

    def _extract_from_config(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract roles from configuration files."""
        content = file.get("content", "")
        path = file.get("path", "").lower()

        if not content:
            return

        if "web.config" in path:
            self._extract_from_web_config(content, result)
        elif "appsettings" in path:
            self._extract_from_appsettings(content, result)
        elif "startup.cs" in path or "program.cs" in path:
            self._extract_from_startup(content, path, result)

    def _extract_from_web_config(self, content: str, result: Dict[str, Any]):
        """Extract from web.config."""
        # Role definitions
        role_patterns = [
            r'<add\s+name="(\w+)"[^/]*/?>',
            r'<role\s+name="(\w+)"',
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for role in matches:
                self._add_role(role, "web.config", "config", result)

        # Authorization rules
        auth_patterns = [
            r'<allow\s+roles="([^"]+)"',
            r'<deny\s+roles="([^"]+)"',
        ]

        for pattern in auth_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for roles_str in matches:
                for role in roles_str.split(","):
                    self._add_role(role.strip(), "web.config", "config_auth", result)

    def _extract_from_appsettings(self, content: str, result: Dict[str, Any]):
        """Extract from appsettings.json."""
        # Look for role definitions in JSON
        role_patterns = [
            r'"Roles"\s*:\s*\[(.*?)\]',
            r'"roles"\s*:\s*\[(.*?)\]',
            r'"AllowedRoles"\s*:\s*\[(.*?)\]',
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                roles = re.findall(r'"(\w+)"', match)
                for role in roles:
                    self._add_role(role, "appsettings.json", "config", result)

    def _extract_from_startup(
        self,
        content: str,
        path: str,
        result: Dict[str, Any],
    ):
        """Extract from Startup.cs / Program.cs."""
        # Policy definitions
        policy_patterns = [
            r'AddPolicy\s*\(\s*"(\w+)"',
            r'RequireRole\s*\(\s*"([^"]+)"',
        ]

        for pattern in policy_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                for role in match.split(","):
                    self._add_role(role.strip(), path, "policy", result)

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

    def _detect_auth_requirement(self, content: str) -> bool:
        """Detect if page requires authentication."""
        auth_indicators = [
            r'@attribute\s*\[Authorize',
            r'User\.Identity\.IsAuthenticated',
            r'User\.IsInRole',
            r'<AuthorizeView',
            r'RequireAuthorization',
        ]

        for pattern in auth_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # Check for anonymous indicators
        anon_indicators = [
            r'\[AllowAnonymous\]',
            r'@attribute\s*\[AllowAnonymous\]',
        ]

        for pattern in anon_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return False

        return True  # Default to requiring auth

    def _generate_display_name(self, screen_name: str) -> str:
        """Generate human-readable display name from screen name."""
        # Convert PascalCase/camelCase to spaces
        name = re.sub(r'([A-Z])', r' \1', screen_name).strip()
        # Remove common suffixes
        for suffix in ["View", "Page", "Form", "Screen", "Component"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        return name
