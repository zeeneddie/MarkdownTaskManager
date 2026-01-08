"""
API Inventory Service - Fase 26: Migration Execution (Week 140-141)

Extract and catalog internal and external APIs from source code.
Supports multiple frameworks: FastAPI, Flask, Django, Express, ASP.NET, Spring, Laravel.

Author: Claude Code (Week 140 - Fase 26)
Date: 2026-01-01
"""

import re
import os
import logging
import time
from dataclasses import field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from urllib.parse import urlparse
import uuid

from app.models.api_inventory import (
    HTTPMethod,
    ParameterLocation,
    AuthType,
    APIType,
    APIFramework,
    Parameter,
    Endpoint,
    ExternalAPI,
    ExternalAPICall,
    FrameworkDetection,
    APIInventorySession,
    APIInventoryResult,
    categorize_external_api,
)

logger = logging.getLogger(__name__)


class APIInventoryService:
    """Extract and catalog internal and external APIs from source code."""

    # Framework detection patterns
    FRAMEWORK_DETECTION: Dict[APIFramework, List[Tuple[str, str]]] = {
        APIFramework.FASTAPI: [
            (r"from\s+fastapi\s+import", "import statement"),
            (r"FastAPI\s*\(", "app instantiation"),
            (r"@(app|router)\.(get|post|put|patch|delete)", "route decorator"),
        ],
        APIFramework.FLASK: [
            (r"from\s+flask\s+import", "import statement"),
            (r"Flask\s*\(__name__\)", "app instantiation"),
            (r"@(app|blueprint)\.route", "route decorator"),
        ],
        APIFramework.DJANGO: [
            (r"from\s+django", "import statement"),
            (r"path\s*\(", "urlpatterns"),
            (r"@api_view", "DRF decorator"),
        ],
        APIFramework.EXPRESS: [
            (r"require\s*\(\s*['\"]express['\"]", "require statement"),
            (r"import\s+.*\s+from\s+['\"]express['\"]", "import statement"),
            (r"express\s*\(\s*\)", "app instantiation"),
        ],
        APIFramework.NESTJS: [
            (r"@Controller\s*\(", "controller decorator"),
            (r"@(Get|Post|Put|Patch|Delete)\s*\(", "route decorator"),
            (r"from\s+['\"]@nestjs/common['\"]", "import statement"),
        ],
        APIFramework.ASPNET: [
            (r"\[Http(Get|Post|Put|Patch|Delete)", "route attribute"),
            (r"\[Route\s*\(", "route attribute"),
            (r"MapGet|MapPost|MapPut|MapDelete", "minimal API"),
            (r"Controller\s*:\s*ControllerBase", "controller inheritance"),
        ],
        APIFramework.SPRING: [
            (r"@(GetMapping|PostMapping|PutMapping|DeleteMapping)", "mapping annotation"),
            (r"@RequestMapping", "request mapping"),
            (r"@RestController", "controller annotation"),
        ],
        APIFramework.LARAVEL: [
            (r"Route::(get|post|put|patch|delete)", "route definition"),
            (r"use\s+Illuminate\\", "illuminate import"),
        ],
    }

    # Route extraction patterns per framework
    ROUTE_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
        "fastapi": [
            # @app.get("/path") or @router.get("/path")
            (r'@(app|router)\.(get|post|put|patch|delete|head|options)\s*\(\s*["\']([^"\']+)["\']', "decorator"),
            # @app.api_route("/path", methods=["GET", "POST"])
            (r'@(app|router)\.api_route\s*\(\s*["\']([^"\']+)["\']', "api_route"),
        ],
        "flask": [
            # @app.route("/path", methods=["GET", "POST"])
            (r'@(app|blueprint|bp)\.route\s*\(\s*["\']([^"\']+)["\'](?:[^)]*methods\s*=\s*\[([^\]]+)\])?', "route"),
            # @app.get("/path"), @app.post("/path") - Flask 2.0+
            (r'@(app|blueprint|bp)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', "method_decorator"),
        ],
        "django": [
            # path("users/", views.user_list)
            (r'path\s*\(\s*["\']([^"\']+)["\']', "path"),
            # url(r"^users/$", views.user_list)
            (r'url\s*\(\s*r?["\']([^"\']+)["\']', "url"),
            # @api_view(["GET", "POST"])
            (r'@api_view\s*\(\s*\[([^\]]+)\]', "api_view"),
        ],
        "express": [
            # app.get("/path", handler) or router.get("/path", handler)
            (r'(app|router)\.(get|post|put|patch|delete|all)\s*\(\s*["\']([^"\']+)["\']', "method"),
            # app.use("/api", router)
            (r'(app|router)\.use\s*\(\s*["\']([^"\']+)["\']', "use"),
        ],
        "nestjs": [
            # @Get("path"), @Post("path"), etc.
            (r'@(Get|Post|Put|Patch|Delete)\s*\(\s*["\']?([^"\')\s]*)["\']?\s*\)', "decorator"),
            # @Controller("path")
            (r'@Controller\s*\(\s*["\']([^"\']+)["\']', "controller"),
        ],
        "aspnet": [
            # [HttpGet("path")], [HttpPost("path")], etc.
            (r'\[(Http(?:Get|Post|Put|Patch|Delete))(?:\s*\(\s*["\']([^"\']+)["\']\s*\))?\]', "http_attribute"),
            # [Route("path")]
            (r'\[Route\s*\(\s*["\']([^"\']+)["\']\s*\)\]', "route_attribute"),
            # app.MapGet("/path", handler)
            (r'\.(Map(?:Get|Post|Put|Patch|Delete))\s*\(\s*["\']([^"\']+)["\']', "minimal_api"),
        ],
        "spring": [
            # @GetMapping("/path"), @PostMapping("/path"), etc.
            (r'@(Get|Post|Put|Patch|Delete)Mapping\s*\(\s*(?:value\s*=\s*)?["\']?([^"\')\s,]+)?', "mapping"),
            # @RequestMapping(value = "/path", method = RequestMethod.GET)
            (r'@RequestMapping\s*\([^)]*value\s*=\s*["\']([^"\']+)["\']', "request_mapping"),
        ],
        "laravel": [
            # Route::get("/path", [Controller::class, "method"])
            (r'Route::(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', "route"),
            # Route::apiResource("/path", Controller::class)
            (r'Route::apiResource\s*\(\s*["\']([^"\']+)["\']', "api_resource"),
        ],
    }

    # External API call patterns per language
    EXTERNAL_CALL_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
        "python": [
            # requests.get("url"), requests.post("url", ...)
            (r'requests\.(get|post|put|patch|delete|head|options)\s*\(\s*[f]?["\']([^"\']+)["\']', "requests"),
            # httpx.get("url"), httpx.post("url", ...)
            (r'httpx\.(get|post|put|patch|delete|head|options)\s*\(\s*["\']([^"\']+)["\']', "httpx"),
            # async with aiohttp.ClientSession() as session: await session.get("url")
            (r'session\.(get|post|put|patch|delete)\s*\(\s*[f]?["\']([^"\']+)["\']', "aiohttp"),
            # urllib.request.urlopen("url")
            (r'urlopen\s*\(\s*["\']([^"\']+)["\']', "urllib"),
            # http.client connections
            (r'HTTPConnection\s*\(\s*["\']([^"\']+)["\']', "http.client"),
        ],
        "javascript": [
            # fetch("url")
            (r'fetch\s*\(\s*[`"\']([^`"\']+)[`"\']', "fetch"),
            # axios.get("url"), axios.post("url", ...)
            (r'axios\.(get|post|put|patch|delete)\s*\(\s*[`"\']([^`"\']+)[`"\']', "axios"),
            # $.ajax({url: "url"})
            (r'\$\.ajax\s*\(\s*\{[^}]*url\s*:\s*[`"\']([^`"\']+)[`"\']', "jquery"),
            # $.get("url"), $.post("url")
            (r'\$\.(get|post)\s*\(\s*[`"\']([^`"\']+)[`"\']', "jquery_shorthand"),
            # new XMLHttpRequest() ... open("GET", "url")
            (r'\.open\s*\(\s*["\'](\w+)["\']\s*,\s*[`"\']([^`"\']+)[`"\']', "xhr"),
        ],
        "csharp": [
            # HttpClient.GetAsync("url"), PostAsync("url"), etc.
            (r'\.(Get|Post|Put|Patch|Delete)Async\s*\(\s*["\']([^"\']+)["\']', "httpclient"),
            # WebClient.DownloadString("url")
            (r'\.(DownloadString|UploadString)\s*\(\s*["\']([^"\']+)["\']', "webclient"),
            # RestClient.Get("url")
            (r'RestClient.*?\.(Get|Post|Put|Delete)\s*\(\s*["\']([^"\']+)["\']', "restsharp"),
            # WebRequest.Create("url")
            (r'WebRequest\.Create\s*\(\s*["\']([^"\']+)["\']', "webrequest"),
        ],
        "vbnet": [
            # CreateObject("MSXML2.XMLHTTP")
            (r'CreateObject\s*\(\s*["\']MSXML2\.XMLHTTP', "xmlhttp"),
            # WebRequest.Create("url")
            (r'WebRequest\.Create\s*\(\s*["\']([^"\']+)["\']', "webrequest"),
            # HttpWebRequest
            (r'HttpWebRequest.*?["\']([^"\']+http[^"\']+)["\']', "httpwebrequest"),
        ],
        "php": [
            # file_get_contents("url")
            (r'file_get_contents\s*\(\s*["\']([^"\']+)["\']', "file_get_contents"),
            # curl_init("url")
            (r'curl_init\s*\(\s*["\']([^"\']+)["\']', "curl"),
            # Guzzle: $client->get("url")
            (r'\$\w+->(?:get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', "guzzle"),
        ],
        "java": [
            # HttpURLConnection / URL("url")
            (r'new\s+URL\s*\(\s*["\']([^"\']+)["\']', "url"),
            # RestTemplate.getForObject("url", ...)
            (r'RestTemplate.*?\.(getForObject|postForObject)\s*\(\s*["\']([^"\']+)["\']', "resttemplate"),
            # WebClient.create("url")
            (r'WebClient\.create\s*\(\s*["\']([^"\']+)["\']', "webclient"),
            # OkHttp
            (r'Request\.Builder\s*\(\s*\)\.url\s*\(\s*["\']([^"\']+)["\']', "okhttp"),
        ],
    }

    # Authentication pattern detection
    AUTH_PATTERNS: Dict[AuthType, List[str]] = {
        AuthType.JWT: [
            r"@jwt_required",
            r"JWTAuth",
            r"Bearer\s+",
            r"jsonwebtoken",
            r"PyJWT",
        ],
        AuthType.OAUTH2: [
            r"OAuth2",
            r"oauth2",
            r"@oauth_required",
            r"passport\.authenticate",
        ],
        AuthType.API_KEY: [
            r"api[_-]?key",
            r"x-api-key",
            r"apikey",
        ],
        AuthType.BASIC: [
            r"Basic\s+",
            r"HTTPBasicAuth",
            r"basic_auth",
        ],
        AuthType.SESSION: [
            r"session\[",
            r"@login_required",
            r"IsAuthenticated",
        ],
    }

    def __init__(self, db=None):
        """Initialize the API Inventory Service."""
        self.db = db
        self.sessions: Dict[str, APIInventorySession] = {}
        self.results: Dict[str, APIInventoryResult] = {}

    async def create_session(
        self,
        project_id: str = "",
        name: str = "",
    ) -> str:
        """Create a new API inventory session."""
        session = APIInventorySession(
            project_id=project_id,
            name=name or f"API Inventory {datetime.utcnow().isoformat()}",
        )
        self.sessions[session.session_id] = session
        logger.info(f"Created API inventory session: {session.session_id}")
        return session.session_id

    async def get_session(self, session_id: str) -> Optional[APIInventoryResult]:
        """Get session results by ID."""
        return self.results.get(session_id)

    async def scan_codebase(
        self,
        session_id: str,
        project_path: str,
        file_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> APIInventoryResult:
        """Scan codebase for API endpoints and external calls."""
        start_time = time.time()

        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session.status = "scanning"

        # Default file extensions
        if file_extensions is None:
            file_extensions = [
                ".py", ".js", ".ts", ".jsx", ".tsx",
                ".cs", ".vb", ".java", ".php",
                ".go", ".rs",
            ]

        # Default exclude patterns
        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules", "__pycache__", ".git", ".venv",
                "venv", "dist", "build", "target", "bin", "obj",
            ]

        # Collect files
        files: Dict[str, str] = {}
        files_scanned = 0
        errors: List[str] = []
        warnings: List[str] = []
        languages: Set[str] = set()

        try:
            for root, dirs, filenames in os.walk(project_path):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(
                    pattern in d for pattern in exclude_patterns
                )]

                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in file_extensions:
                        filepath = os.path.join(root, filename)
                        rel_path = os.path.relpath(filepath, project_path)

                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                files[rel_path] = content
                                files_scanned += 1
                                languages.add(self._get_language(ext))
                        except Exception as e:
                            errors.append(f"Error reading {rel_path}: {str(e)}")

        except Exception as e:
            errors.append(f"Error scanning directory: {str(e)}")
            session.status = "error"
            session.error_message = str(e)

        # Detect frameworks
        frameworks = await self.detect_frameworks(files)

        # Extract internal endpoints
        internal_endpoints = await self.extract_internal_endpoints(
            files,
            framework=frameworks[0].framework.value if frameworks else None
        )

        # Extract external APIs
        external_apis = await self.extract_external_apis(files)

        # Calculate duration
        duration = time.time() - start_time

        # Create result
        result = APIInventoryResult(
            session_id=session_id,
            project_id=session.project_id,
            internal_endpoints=internal_endpoints,
            external_apis=external_apis,
            frameworks_detected=frameworks,
            languages_scanned=list(languages),
            files_scanned=files_scanned,
            scan_duration_seconds=round(duration, 2),
            errors=errors,
            warnings=warnings,
        )

        self.results[session_id] = result
        session.status = "completed"

        logger.info(
            f"Scan complete: {result.total_internal} internal endpoints, "
            f"{result.total_external} external APIs in {duration:.2f}s"
        )

        return result

    async def detect_frameworks(
        self,
        files: Dict[str, str],
    ) -> List[FrameworkDetection]:
        """Detect web frameworks used in the codebase."""
        detections: List[FrameworkDetection] = []
        framework_scores: Dict[APIFramework, Tuple[float, str, List[str]]] = {}

        for filepath, content in files.items():
            for framework, patterns in self.FRAMEWORK_DETECTION.items():
                matched_patterns = []
                for pattern, description in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        matched_patterns.append(description)

                if matched_patterns:
                    # Calculate confidence based on number of patterns matched
                    confidence = min(0.5 + (len(matched_patterns) * 0.2), 1.0)

                    if framework not in framework_scores:
                        framework_scores[framework] = (confidence, filepath, matched_patterns)
                    else:
                        existing = framework_scores[framework]
                        if confidence > existing[0]:
                            framework_scores[framework] = (confidence, filepath, matched_patterns)

        for framework, (confidence, filepath, patterns) in framework_scores.items():
            detections.append(FrameworkDetection(
                framework=framework,
                confidence=confidence,
                detection_file=filepath,
                detection_patterns=patterns,
            ))

        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)
        return detections

    async def extract_internal_endpoints(
        self,
        files: Dict[str, str],
        framework: Optional[str] = None,
    ) -> List[Endpoint]:
        """Extract route definitions from source files."""
        endpoints: List[Endpoint] = []

        # Determine which frameworks to check
        frameworks_to_check = [framework] if framework else list(self.ROUTE_PATTERNS.keys())

        for filepath, content in files.items():
            lines = content.split("\n")

            for fw in frameworks_to_check:
                if fw not in self.ROUTE_PATTERNS:
                    continue

                for pattern, pattern_type in self.ROUTE_PATTERNS[fw]:
                    for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                        endpoint = self._parse_route_match(
                            match, pattern_type, fw, filepath, lines, content
                        )
                        if endpoint:
                            endpoints.append(endpoint)

        # Deduplicate endpoints
        seen = set()
        unique_endpoints = []
        for ep in endpoints:
            key = (ep.path, tuple(ep.methods), ep.source_file)
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)

        return unique_endpoints

    def _parse_route_match(
        self,
        match: re.Match,
        pattern_type: str,
        framework: str,
        filepath: str,
        lines: List[str],
        content: str,
    ) -> Optional[Endpoint]:
        """Parse a route pattern match into an Endpoint."""
        groups = match.groups()

        # Extract path and method based on pattern type
        path = ""
        methods = []

        if framework == "fastapi":
            if pattern_type == "decorator" and len(groups) >= 3:
                method_str = groups[1].upper()
                path = groups[2]
                methods = [HTTPMethod[method_str]]
            elif pattern_type == "api_route" and len(groups) >= 2:
                path = groups[1]
                methods = [HTTPMethod.GET, HTTPMethod.POST]

        elif framework == "flask":
            if pattern_type == "route" and len(groups) >= 2:
                path = groups[1]
                if len(groups) >= 3 and groups[2]:
                    methods = self._parse_method_list(groups[2])
                else:
                    methods = [HTTPMethod.GET]
            elif pattern_type == "method_decorator" and len(groups) >= 3:
                method_str = groups[1].upper()
                path = groups[2]
                methods = [HTTPMethod[method_str]]

        elif framework == "django":
            if len(groups) >= 1:
                path = "/" + groups[0].lstrip("^").rstrip("$")
                methods = [HTTPMethod.GET]

        elif framework in ("express", "nestjs"):
            if len(groups) >= 3:
                method_str = groups[1].upper()
                path = groups[2] or "/"
                methods = [HTTPMethod[method_str]] if method_str in HTTPMethod.__members__ else [HTTPMethod.GET]

        elif framework == "aspnet":
            if pattern_type == "http_attribute" and len(groups) >= 1:
                method_str = groups[0].replace("Http", "").upper()
                path = groups[1] if len(groups) > 1 and groups[1] else "/"
                methods = [HTTPMethod[method_str]] if method_str in HTTPMethod.__members__ else [HTTPMethod.GET]
            elif pattern_type == "minimal_api" and len(groups) >= 2:
                method_str = groups[0].replace("Map", "").upper()
                path = groups[1]
                methods = [HTTPMethod[method_str]] if method_str in HTTPMethod.__members__ else [HTTPMethod.GET]

        elif framework == "spring":
            if len(groups) >= 1:
                method_str = groups[0].replace("Mapping", "").upper()
                path = "/" + (groups[1] if len(groups) > 1 and groups[1] else "").lstrip("/")
                methods = [HTTPMethod[method_str]] if method_str in HTTPMethod.__members__ else [HTTPMethod.GET]

        elif framework == "laravel":
            if len(groups) >= 2:
                method_str = groups[0].upper()
                path = groups[1]
                methods = [HTTPMethod[method_str]] if method_str in HTTPMethod.__members__ else [HTTPMethod.GET]

        if not path:
            return None

        # Find line number
        line_start = content[:match.start()].count("\n") + 1

        # Extract handler function name (look for function definition nearby)
        handler_func = self._extract_handler_name(lines, line_start, framework)

        # Detect authentication
        auth_type = self._detect_auth_type(content, match.start(), match.end())

        return Endpoint(
            path=path,
            methods=methods,
            handler_function=handler_func,
            source_file=filepath,
            source_line_start=line_start,
            framework=APIFramework(framework) if framework in APIFramework.__members__.values() else APIFramework.UNKNOWN,
            authentication=auth_type,
        )

    def _parse_method_list(self, method_str: str) -> List[HTTPMethod]:
        """Parse a method list string like ['GET', 'POST']."""
        methods = []
        for m in re.findall(r'["\'](\w+)["\']', method_str):
            if m.upper() in HTTPMethod.__members__:
                methods.append(HTTPMethod[m.upper()])
        return methods or [HTTPMethod.GET]

    def _extract_handler_name(
        self,
        lines: List[str],
        line_num: int,
        framework: str,
    ) -> str:
        """Extract the handler function name from nearby code."""
        # Look at next few lines for function definition
        for i in range(line_num, min(line_num + 5, len(lines))):
            line = lines[i] if i < len(lines) else ""

            # Python: def function_name(
            match = re.search(r'def\s+(\w+)\s*\(', line)
            if match:
                return match.group(1)

            # Python: async def function_name(
            match = re.search(r'async\s+def\s+(\w+)\s*\(', line)
            if match:
                return match.group(1)

            # JavaScript/TypeScript: function name( or async function name(
            match = re.search(r'(?:async\s+)?function\s+(\w+)\s*\(', line)
            if match:
                return match.group(1)

            # Arrow function: const name = async (
            match = re.search(r'(?:const|let|var)\s+(\w+)\s*=', line)
            if match:
                return match.group(1)

            # C#/Java: public async Task<T> MethodName(
            match = re.search(r'(?:public|private|protected).*?\s+(\w+)\s*\(', line)
            if match:
                return match.group(1)

        return "unknown_handler"

    def _detect_auth_type(
        self,
        content: str,
        start: int,
        end: int,
    ) -> AuthType:
        """Detect authentication type from nearby code."""
        # Check a window around the match
        window_start = max(0, start - 500)
        window_end = min(len(content), end + 500)
        window = content[window_start:window_end]

        for auth_type, patterns in self.AUTH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, window, re.IGNORECASE):
                    return auth_type

        return AuthType.NONE

    async def extract_external_apis(
        self,
        files: Dict[str, str],
        language: Optional[str] = None,
    ) -> List[ExternalAPI]:
        """Detect external API calls in source code."""
        external_apis: Dict[str, ExternalAPI] = {}

        for filepath, content in files.items():
            file_ext = os.path.splitext(filepath)[1].lower()
            file_lang = self._get_language(file_ext)

            # Determine which patterns to use
            if language:
                langs_to_check = [language]
            else:
                langs_to_check = [file_lang] if file_lang in self.EXTERNAL_CALL_PATTERNS else list(self.EXTERNAL_CALL_PATTERNS.keys())

            lines = content.split("\n")

            for lang in langs_to_check:
                if lang not in self.EXTERNAL_CALL_PATTERNS:
                    continue

                for pattern, library in self.EXTERNAL_CALL_PATTERNS[lang]:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        api_call = self._parse_external_call(
                            match, library, filepath, lines, content
                        )
                        if api_call:
                            domain = api_call.detected_domain
                            if domain not in external_apis:
                                external_apis[domain] = api_call
                            else:
                                # Merge call locations
                                existing = external_apis[domain]
                                existing.call_locations.extend(api_call.call_locations)
                                existing.endpoints_called = list(set(
                                    existing.endpoints_called + api_call.endpoints_called
                                ))
                                existing.http_methods = list(set(
                                    existing.http_methods + api_call.http_methods
                                ))

        return list(external_apis.values())

    def _parse_external_call(
        self,
        match: re.Match,
        library: str,
        filepath: str,
        lines: List[str],
        content: str,
    ) -> Optional[ExternalAPI]:
        """Parse an external API call match."""
        groups = match.groups()

        # Extract URL and method
        url = ""
        method = HTTPMethod.GET

        if len(groups) >= 2:
            # Pattern has method and url
            method_str = groups[0].upper()
            url = groups[1]
            if method_str in HTTPMethod.__members__:
                method = HTTPMethod[method_str]
        elif len(groups) >= 1:
            url = groups[0]

        # Skip internal URLs and variables
        if not url or url.startswith("{") or url.startswith("$"):
            return None

        # Try to parse URL
        try:
            # Handle f-strings and template literals
            url = re.sub(r'\{[^}]+\}', '{param}', url)
            url = re.sub(r'\$\{[^}]+\}', '{param}', url)

            parsed = urlparse(url)
            domain = parsed.netloc or ""

            # Skip if no domain or local
            if not domain or domain in ("localhost", "127.0.0.1", "0.0.0.0"):
                return None

            # Get path
            path = parsed.path or "/"

        except Exception:
            return None

        # Find line number
        line_num = content[:match.start()].count("\n") + 1

        # Create call location
        call_location = ExternalAPICall(
            url=url,
            method=method,
            source_file=filepath,
            source_line=line_num,
        )

        # Categorize the API
        category = categorize_external_api(domain)

        return ExternalAPI(
            name=domain.split(".")[0] if "." in domain else domain,
            base_url=f"{parsed.scheme}://{domain}" if parsed.scheme else f"https://{domain}",
            detected_domain=domain,
            endpoints_called=[path] if path else [],
            call_locations=[call_location],
            http_methods=[method],
            category=category,
        )

    def _get_language(self, ext: str) -> str:
        """Map file extension to language."""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "javascript",
            ".jsx": "javascript",
            ".tsx": "javascript",
            ".cs": "csharp",
            ".vb": "vbnet",
            ".java": "java",
            ".php": "php",
            ".go": "go",
            ".rs": "rust",
        }
        return mapping.get(ext.lower(), "unknown")

    async def link_to_business_rules(
        self,
        endpoints: List[Endpoint],
        business_rules: List[Any],
    ) -> List[Endpoint]:
        """Link endpoints to extracted business rules by file and function."""
        for endpoint in endpoints:
            matching_rules = []
            for rule in business_rules:
                # Match by file
                if hasattr(rule, "source_file") and rule.source_file == endpoint.source_file:
                    # Match by line range if available
                    if hasattr(rule, "line_number"):
                        if endpoint.source_line_start <= rule.line_number <= endpoint.source_line_start + 50:
                            if hasattr(rule, "id"):
                                matching_rules.append(rule.id)
                            elif hasattr(rule, "rule_id"):
                                matching_rules.append(rule.rule_id)

            endpoint.business_rules = matching_rules

        return endpoints

    async def generate_openapi_spec(
        self,
        endpoints: List[Endpoint],
        info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 spec from extracted endpoints."""
        spec = {
            "openapi": "3.0.0",
            "info": info or {
                "title": "Extracted API",
                "version": "1.0.0",
                "description": "API specification generated from source code",
            },
            "paths": {},
        }

        for endpoint in endpoints:
            path = endpoint.path
            if path not in spec["paths"]:
                spec["paths"][path] = {}

            for method in endpoint.methods:
                method_lower = method.value.lower()
                operation = {
                    "summary": endpoint.handler_function,
                    "operationId": f"{endpoint.handler_function}_{method_lower}",
                    "responses": {
                        str(code): {"description": f"Response {code}"}
                        for code in endpoint.response_status_codes
                    },
                }

                if endpoint.documentation:
                    operation["description"] = endpoint.documentation

                if endpoint.tags:
                    operation["tags"] = endpoint.tags

                if endpoint.deprecated:
                    operation["deprecated"] = True

                if endpoint.authentication != AuthType.NONE:
                    operation["security"] = [{"auth": []}]

                # Add parameters
                if endpoint.parameters:
                    operation["parameters"] = [
                        {
                            "name": p.name,
                            "in": p.location.value,
                            "required": p.required,
                            "schema": {"type": p.type_hint or "string"},
                        }
                        for p in endpoint.parameters
                        if p.location != ParameterLocation.BODY
                    ]

                    # Add request body if present
                    body_params = [p for p in endpoint.parameters if p.location == ParameterLocation.BODY]
                    if body_params or endpoint.request_body_type:
                        operation["requestBody"] = {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }

                spec["paths"][path][method_lower] = operation

        return spec

    def to_markdown_report(self, result: APIInventoryResult) -> str:
        """Export inventory as Markdown documentation."""
        lines = [
            "# API Inventory Report",
            "",
            f"**Scan Date:** {result.scan_date.isoformat()}",
            f"**Files Scanned:** {result.files_scanned}",
            f"**Duration:** {result.scan_duration_seconds}s",
            "",
            "## Summary",
            "",
            f"- **Internal Endpoints:** {result.total_internal}",
            f"- **External APIs:** {result.total_external}",
            f"- **Frameworks Detected:** {', '.join(f.framework.value for f in result.frameworks_detected)}",
            f"- **Languages:** {', '.join(result.languages_scanned)}",
            "",
        ]

        # Internal endpoints
        if result.internal_endpoints:
            lines.extend([
                "## Internal Endpoints",
                "",
                "| Path | Methods | Handler | Auth | File |",
                "|------|---------|---------|------|------|",
            ])
            for ep in result.internal_endpoints:
                methods = ", ".join(m.value for m in ep.methods)
                auth = ep.authentication.value if ep.authentication != AuthType.NONE else "-"
                lines.append(f"| {ep.path} | {methods} | {ep.handler_function} | {auth} | {ep.source_file} |")
            lines.append("")

        # External APIs
        if result.external_apis:
            lines.extend([
                "## External APIs",
                "",
                "| Name | Domain | Category | Methods | Endpoints |",
                "|------|--------|----------|---------|-----------|",
            ])
            for api in result.external_apis:
                methods = ", ".join(m.value for m in api.http_methods)
                endpoints = ", ".join(api.endpoints_called[:3])
                if len(api.endpoints_called) > 3:
                    endpoints += f" (+{len(api.endpoints_called) - 3} more)"
                lines.append(f"| {api.name} | {api.detected_domain} | {api.category} | {methods} | {endpoints} |")
            lines.append("")

        # Errors
        if result.errors:
            lines.extend([
                "## Errors",
                "",
            ])
            for error in result.errors:
                lines.append(f"- {error}")
            lines.append("")

        return "\n".join(lines)

    def to_csv(self, result: APIInventoryResult) -> str:
        """Export endpoints as CSV for analysis."""
        lines = ["path,methods,handler,auth,framework,file,line"]

        for ep in result.internal_endpoints:
            methods = "|".join(m.value for m in ep.methods)
            lines.append(
                f'"{ep.path}","{methods}","{ep.handler_function}",'
                f'"{ep.authentication.value}","{ep.framework.value}",'
                f'"{ep.source_file}",{ep.source_line_start}'
            )

        return "\n".join(lines)
