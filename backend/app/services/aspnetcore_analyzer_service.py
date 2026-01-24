"""
ASP.NET Core Analyzer Service

Fase 24 GAP Item B5: ASP.NET Core Analyzer
Week 159 - Modern .NET analysis for ASP.NET Core applications.

Features:
- ASP.NET Core MVC/Web API controller analysis
- Minimal API endpoint detection (.NET 6+)
- Razor Pages analysis
- Blazor component detection
- gRPC service analysis
- Dependency Injection pattern detection
- Middleware pipeline analysis
- Entity Framework Core context detection
- Configuration pattern analysis

This complements the existing dotnet_analyzer_service.py which focuses
on legacy .NET (WebForms, WCF).

Author: Claude Code (Week 159)
Date: 2026-01-24
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class AspNetCoreVersion(str, Enum):
    """ASP.NET Core version detection."""
    NETCORE_2_1 = "netcoreapp2.1"
    NETCORE_3_1 = "netcoreapp3.1"
    NET_5 = "net5.0"
    NET_6 = "net6.0"
    NET_7 = "net7.0"
    NET_8 = "net8.0"
    NET_9 = "net9.0"
    UNKNOWN = "unknown"


class ControllerType(str, Enum):
    """Type of ASP.NET Core controller."""
    API_CONTROLLER = "api_controller"
    MVC_CONTROLLER = "mvc_controller"
    RAZOR_PAGE = "razor_page"
    MINIMAL_API = "minimal_api"


class EndpointMethod(str, Enum):
    """HTTP methods for endpoints."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ServiceLifetime(str, Enum):
    """DI service lifetime."""
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AspNetCoreEndpoint:
    """Represents an API endpoint."""
    route: str
    http_method: EndpointMethod
    action_name: str
    controller_name: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_async: bool = False
    requires_authorization: bool = False
    authorization_policy: Optional[str] = None
    file_path: str = ""
    line_number: int = 0


@dataclass
class AspNetCoreController:
    """Represents an ASP.NET Core controller."""
    file_path: str
    class_name: str
    controller_type: ControllerType
    base_route: Optional[str] = None
    namespace: Optional[str] = None
    base_class: Optional[str] = None
    endpoints: List[AspNetCoreEndpoint] = field(default_factory=list)
    injected_services: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    uses_model_binding: bool = False
    uses_validation: bool = False
    loc: int = 0
    complexity: float = 0.0


@dataclass
class MinimalApiEndpoint:
    """Represents a Minimal API endpoint (.NET 6+)."""
    route: str
    http_method: EndpointMethod
    handler_type: str  # "lambda", "method_group", "local_function"
    file_path: str
    line_number: int
    return_type: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    is_async: bool = False
    uses_results: bool = False  # Uses Results.Ok(), etc.
    endpoint_filters: List[str] = field(default_factory=list)
    requires_authorization: bool = False


@dataclass
class RazorPage:
    """Represents a Razor Page."""
    file_path: str
    page_name: str
    route: Optional[str] = None
    page_model_path: Optional[str] = None
    page_model_class: Optional[str] = None
    handlers: List[str] = field(default_factory=list)  # OnGet, OnPost, etc.
    injected_services: List[str] = field(default_factory=list)
    uses_tag_helpers: bool = False
    uses_view_components: bool = False
    layout: Optional[str] = None
    loc: int = 0


@dataclass
class BlazorComponent:
    """Represents a Blazor component."""
    file_path: str
    component_name: str
    component_type: str  # "server", "wasm", "hybrid"
    namespace: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    cascading_parameters: List[str] = field(default_factory=list)
    injected_services: List[str] = field(default_factory=list)
    event_callbacks: List[str] = field(default_factory=list)
    lifecycle_methods: List[str] = field(default_factory=list)
    renders_fragment: bool = False
    uses_js_interop: bool = False
    loc: int = 0


@dataclass
class GrpcService:
    """Represents a gRPC service."""
    file_path: str
    service_name: str
    proto_file: Optional[str] = None
    namespace: Optional[str] = None
    methods: List[Dict[str, Any]] = field(default_factory=list)
    base_class: Optional[str] = None
    uses_streaming: bool = False
    injected_services: List[str] = field(default_factory=list)
    loc: int = 0


@dataclass
class MiddlewareComponent:
    """Represents middleware in the pipeline."""
    name: str
    registration_type: str  # "UseXxx", "MapXxx", "custom"
    file_path: str
    line_number: int
    order: int = 0
    is_terminal: bool = False
    is_branching: bool = False
    conditions: List[str] = field(default_factory=list)
    is_custom: bool = False
    custom_class: Optional[str] = None


@dataclass
class DiRegistration:
    """Represents a DI service registration."""
    service_type: str
    implementation_type: Optional[str] = None
    lifetime: ServiceLifetime = ServiceLifetime.SCOPED
    registration_method: str = ""  # AddScoped, AddSingleton, etc.
    file_path: str = ""
    line_number: int = 0
    is_generic: bool = False
    is_factory: bool = False


@dataclass
class EfCoreDbContext:
    """Represents an Entity Framework Core DbContext."""
    file_path: str
    class_name: str
    namespace: Optional[str] = None
    db_sets: List[Dict[str, str]] = field(default_factory=list)  # name, entity_type
    uses_fluent_api: bool = False
    uses_conventions: bool = False
    has_seed_data: bool = False
    connection_string_name: Optional[str] = None
    database_provider: Optional[str] = None  # SqlServer, PostgreSQL, etc.
    loc: int = 0


@dataclass
class ConfigurationSection:
    """Represents a configuration section."""
    name: str
    source: str  # "appsettings.json", "environment", "user_secrets"
    bound_type: Optional[str] = None
    is_options_pattern: bool = False
    validation_enabled: bool = False


@dataclass
class AspNetCoreProject:
    """Represents an ASP.NET Core project."""
    project_path: str
    project_name: str
    target_framework: AspNetCoreVersion = AspNetCoreVersion.UNKNOWN
    sdk: str = "Microsoft.NET.Sdk.Web"
    nullable_enabled: bool = False
    implicit_usings: bool = False
    is_aot: bool = False
    package_references: List[Dict[str, str]] = field(default_factory=list)
    project_references: List[str] = field(default_factory=list)


@dataclass
class AspNetCorePattern:
    """Detected ASP.NET Core pattern."""
    pattern_name: str
    pattern_category: str  # "modern", "legacy", "anti-pattern"
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: Optional[str] = None
    severity: str = "info"  # info, warning, error


@dataclass
class AspNetCoreAnalysisResult:
    """Complete ASP.NET Core analysis result."""
    # Project info
    projects: List[AspNetCoreProject] = field(default_factory=list)

    # Controllers and endpoints
    controllers: List[AspNetCoreController] = field(default_factory=list)
    minimal_api_endpoints: List[MinimalApiEndpoint] = field(default_factory=list)
    razor_pages: List[RazorPage] = field(default_factory=list)

    # Components
    blazor_components: List[BlazorComponent] = field(default_factory=list)
    grpc_services: List[GrpcService] = field(default_factory=list)

    # Infrastructure
    middleware_pipeline: List[MiddlewareComponent] = field(default_factory=list)
    di_registrations: List[DiRegistration] = field(default_factory=list)
    db_contexts: List[EfCoreDbContext] = field(default_factory=list)
    configuration_sections: List[ConfigurationSection] = field(default_factory=list)

    # Patterns and recommendations
    patterns: List[AspNetCorePattern] = field(default_factory=list)

    # Statistics
    total_endpoints: int = 0
    total_controllers: int = 0
    total_services_registered: int = 0
    total_loc: int = 0

    # Metadata
    analysis_version: str = "1.0.0"
    scan_duration_ms: float = 0.0


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

ASPNETCORE_PATTERNS = {
    # Controller patterns
    "api_controller": {
        "pattern": r'\[ApiController\]',
        "category": "modern",
        "description": "API Controller attribute for automatic model validation"
    },
    "route_attribute": {
        "pattern": r'\[Route\s*\(\s*["\']([^"\']+)["\']\s*\)\]',
        "category": "modern",
        "description": "Route attribute for endpoint routing"
    },
    "http_get": {
        "pattern": r'\[HttpGet(?:\s*\(\s*["\']([^"\']*)["\'])?\s*\)\]',
        "category": "modern",
        "description": "HTTP GET endpoint"
    },
    "http_post": {
        "pattern": r'\[HttpPost(?:\s*\(\s*["\']([^"\']*)["\'])?\s*\)\]',
        "category": "modern",
        "description": "HTTP POST endpoint"
    },
    "http_put": {
        "pattern": r'\[HttpPut(?:\s*\(\s*["\']([^"\']*)["\'])?\s*\)\]',
        "category": "modern",
        "description": "HTTP PUT endpoint"
    },
    "http_delete": {
        "pattern": r'\[HttpDelete(?:\s*\(\s*["\']([^"\']*)["\'])?\s*\)\]',
        "category": "modern",
        "description": "HTTP DELETE endpoint"
    },
    "http_patch": {
        "pattern": r'\[HttpPatch(?:\s*\(\s*["\']([^"\']*)["\'])?\s*\)\]',
        "category": "modern",
        "description": "HTTP PATCH endpoint"
    },

    # Authorization
    "authorize_attribute": {
        "pattern": r'\[Authorize(?:\s*\([^)]*\))?\]',
        "category": "modern",
        "description": "Authorization requirement"
    },
    "allow_anonymous": {
        "pattern": r'\[AllowAnonymous\]',
        "category": "modern",
        "description": "Allow anonymous access"
    },

    # Minimal API
    "minimal_api_map": {
        "pattern": r'app\.Map(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']+)["\']',
        "category": "modern",
        "description": "Minimal API endpoint mapping"
    },
    "minimal_api_group": {
        "pattern": r'app\.MapGroup\s*\(\s*["\']([^"\']+)["\']',
        "category": "modern",
        "description": "Minimal API route group"
    },

    # DI patterns
    "add_scoped": {
        "pattern": r'services\.AddScoped<([^>]+)(?:,\s*([^>]+))?>\s*\(',
        "category": "modern",
        "description": "Scoped service registration"
    },
    "add_singleton": {
        "pattern": r'services\.AddSingleton<([^>]+)(?:,\s*([^>]+))?>\s*\(',
        "category": "modern",
        "description": "Singleton service registration"
    },
    "add_transient": {
        "pattern": r'services\.AddTransient<([^>]+)(?:,\s*([^>]+))?>\s*\(',
        "category": "modern",
        "description": "Transient service registration"
    },

    # Middleware
    "use_middleware": {
        "pattern": r'app\.Use(\w+)\s*\(',
        "category": "modern",
        "description": "Middleware registration"
    },

    # EF Core
    "dbcontext": {
        "pattern": r'class\s+(\w+)\s*:\s*DbContext',
        "category": "modern",
        "description": "Entity Framework Core DbContext"
    },
    "dbset": {
        "pattern": r'public\s+(?:virtual\s+)?DbSet<(\w+)>\s+(\w+)',
        "category": "modern",
        "description": "Entity Framework Core DbSet"
    },

    # Blazor
    "blazor_component": {
        "pattern": r'@inherits\s+ComponentBase|@code\s*\{',
        "category": "modern",
        "description": "Blazor component"
    },
    "blazor_parameter": {
        "pattern": r'\[Parameter\]',
        "category": "modern",
        "description": "Blazor component parameter"
    },
    "blazor_inject": {
        "pattern": r'@inject\s+(\w+)\s+(\w+)',
        "category": "modern",
        "description": "Blazor service injection"
    },

    # gRPC
    "grpc_service": {
        "pattern": r'class\s+(\w+)\s*:\s*(\w+)\.(\w+)Base',
        "category": "modern",
        "description": "gRPC service implementation"
    },

    # Anti-patterns
    "service_locator": {
        "pattern": r'IServiceProvider\.GetService|GetRequiredService',
        "category": "anti-pattern",
        "description": "Service locator pattern - prefer constructor injection",
        "recommendation": "Use constructor injection instead of service locator"
    },
    "sync_over_async": {
        "pattern": r'\.Result\b|\.Wait\(\)',
        "category": "anti-pattern",
        "description": "Synchronous wait on async - can cause deadlocks",
        "recommendation": "Use async/await pattern throughout"
    },
}


# ============================================================================
# SERVICE CLASS
# ============================================================================

class AspNetCoreAnalyzerService:
    """
    Analyzer for modern ASP.NET Core applications.

    Detects and analyzes:
    - Controllers (API and MVC)
    - Minimal APIs
    - Razor Pages
    - Blazor components
    - gRPC services
    - Dependency Injection
    - Middleware pipeline
    - Entity Framework Core
    """

    # File extensions to scan
    CSHARP_EXTENSIONS = {".cs"}
    RAZOR_EXTENSIONS = {".cshtml", ".razor"}
    PROJECT_EXTENSIONS = {".csproj"}
    CONFIG_FILES = {"appsettings.json", "appsettings.Development.json", "appsettings.Production.json"}

    # Directories to skip
    SKIP_DIRS = {"bin", "obj", "node_modules", ".git", "packages", ".vs", ".idea"}

    def __init__(self):
        """Initialize the analyzer."""
        self._compiled_patterns = {
            name: re.compile(info["pattern"], re.MULTILINE | re.IGNORECASE)
            for name, info in ASPNETCORE_PATTERNS.items()
        }
        logger.info("AspNetCoreAnalyzerService initialized")

    async def analyze(
        self,
        project_path: str,
        include_patterns: bool = True,
        include_di_analysis: bool = True,
        include_middleware: bool = True
    ) -> AspNetCoreAnalysisResult:
        """
        Analyze an ASP.NET Core project.

        Args:
            project_path: Path to the project root
            include_patterns: Whether to detect patterns
            include_di_analysis: Whether to analyze DI registrations
            include_middleware: Whether to analyze middleware pipeline

        Returns:
            Complete analysis result
        """
        import time
        start_time = time.time()

        result = AspNetCoreAnalysisResult()
        path = Path(project_path)

        if not path.exists():
            logger.error(f"Project path does not exist: {project_path}")
            return result

        # Scan for project files
        result.projects = await self._scan_projects(path)

        # Scan C# files
        cs_files = self._find_files(path, self.CSHARP_EXTENSIONS)
        for cs_file in cs_files:
            await self._analyze_csharp_file(cs_file, result, include_patterns)

        # Scan Razor files
        razor_files = self._find_files(path, self.RAZOR_EXTENSIONS)
        for razor_file in razor_files:
            await self._analyze_razor_file(razor_file, result)

        # Scan config files
        for config_name in self.CONFIG_FILES:
            config_path = path / config_name
            if config_path.exists():
                await self._analyze_config_file(config_path, result)

        # Calculate statistics
        result.total_controllers = len(result.controllers)
        result.total_endpoints = (
            sum(len(c.endpoints) for c in result.controllers) +
            len(result.minimal_api_endpoints)
        )
        result.total_services_registered = len(result.di_registrations)

        result.scan_duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"ASP.NET Core analysis complete: {result.total_controllers} controllers, "
            f"{result.total_endpoints} endpoints, {result.total_services_registered} DI registrations"
        )

        return result

    def _find_files(self, root: Path, extensions: Set[str]) -> List[Path]:
        """Find all files with given extensions."""
        files = []
        for ext in extensions:
            for f in root.rglob(f"*{ext}"):
                if not any(skip in f.parts for skip in self.SKIP_DIRS):
                    files.append(f)
        return files

    async def _scan_projects(self, root: Path) -> List[AspNetCoreProject]:
        """Scan for .csproj files and extract project info."""
        projects = []

        for csproj in root.rglob("*.csproj"):
            if any(skip in csproj.parts for skip in self.SKIP_DIRS):
                continue

            try:
                content = csproj.read_text(encoding="utf-8")
                project = AspNetCoreProject(
                    project_path=str(csproj),
                    project_name=csproj.stem
                )

                # Detect target framework
                tf_match = re.search(r'<TargetFramework>([^<]+)</TargetFramework>', content)
                if tf_match:
                    tf = tf_match.group(1).lower()
                    for version in AspNetCoreVersion:
                        if version.value in tf:
                            project.target_framework = version
                            break

                # Detect SDK
                sdk_match = re.search(r'<Project\s+Sdk="([^"]+)"', content)
                if sdk_match:
                    project.sdk = sdk_match.group(1)

                # Detect nullable
                if '<Nullable>enable</Nullable>' in content:
                    project.nullable_enabled = True

                # Detect implicit usings
                if '<ImplicitUsings>enable</ImplicitUsings>' in content:
                    project.implicit_usings = True

                # Detect AOT
                if '<PublishAot>true</PublishAot>' in content:
                    project.is_aot = True

                # Extract package references
                for pkg_match in re.finditer(
                    r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"',
                    content
                ):
                    project.package_references.append({
                        "name": pkg_match.group(1),
                        "version": pkg_match.group(2)
                    })

                projects.append(project)

            except Exception as e:
                logger.warning(f"Failed to parse {csproj}: {e}")

        return projects

    async def _analyze_csharp_file(
        self,
        file_path: Path,
        result: AspNetCoreAnalysisResult,
        include_patterns: bool
    ) -> None:
        """Analyze a C# file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            result.total_loc += len(lines)

            # Detect controllers
            controller = self._detect_controller(file_path, content)
            if controller:
                result.controllers.append(controller)

            # Detect Minimal API endpoints (usually in Program.cs)
            if file_path.name.lower() in ("program.cs", "startup.cs"):
                endpoints = self._detect_minimal_api(file_path, content)
                result.minimal_api_endpoints.extend(endpoints)

                # Detect middleware
                middleware = self._detect_middleware(file_path, content)
                result.middleware_pipeline.extend(middleware)

                # Detect DI registrations
                registrations = self._detect_di_registrations(file_path, content)
                result.di_registrations.extend(registrations)

            # Detect DbContext
            dbcontext = self._detect_dbcontext(file_path, content)
            if dbcontext:
                result.db_contexts.append(dbcontext)

            # Detect gRPC services
            grpc = self._detect_grpc_service(file_path, content)
            if grpc:
                result.grpc_services.append(grpc)

            # Detect patterns
            if include_patterns:
                patterns = self._detect_patterns(file_path, content)
                result.patterns.extend(patterns)

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")

    def _detect_controller(self, file_path: Path, content: str) -> Optional[AspNetCoreController]:
        """Detect ASP.NET Core controller."""
        # Check for controller class
        class_match = re.search(
            r'(?:\[ApiController\][\s\S]*?)?'
            r'(?:\[Route\s*\(\s*["\']([^"\']+)["\']\s*\)\][\s\S]*?)?'
            r'public\s+class\s+(\w+Controller)\s*:\s*(\w+)',
            content
        )

        if not class_match:
            return None

        route = class_match.group(1) or ""
        class_name = class_match.group(2)
        base_class = class_match.group(3)

        # Determine controller type
        is_api = "[ApiController]" in content
        controller_type = ControllerType.API_CONTROLLER if is_api else ControllerType.MVC_CONTROLLER

        controller = AspNetCoreController(
            file_path=str(file_path),
            class_name=class_name,
            controller_type=controller_type,
            base_route=route,
            base_class=base_class,
            loc=len(content.split("\n"))
        )

        # Detect attributes
        if "[ApiController]" in content:
            controller.attributes.append("ApiController")
        if "[Authorize" in content:
            controller.attributes.append("Authorize")

        # Detect endpoints
        controller.endpoints = self._detect_endpoints(file_path, content, class_name)

        # Detect injected services (constructor injection)
        ctor_match = re.search(
            rf'public\s+{class_name}\s*\(([^)]+)\)',
            content
        )
        if ctor_match:
            params = ctor_match.group(1)
            for param in params.split(","):
                param = param.strip()
                if param:
                    type_match = re.match(r'(\w+(?:<[^>]+>)?)\s+\w+', param)
                    if type_match:
                        controller.injected_services.append(type_match.group(1))

        return controller

    def _detect_endpoints(
        self,
        file_path: Path,
        content: str,
        controller_name: str
    ) -> List[AspNetCoreEndpoint]:
        """Detect endpoints in a controller."""
        endpoints = []

        # Pattern for action methods
        action_pattern = re.compile(
            r'(\[(?:Http(?:Get|Post|Put|Delete|Patch)|Route)\s*(?:\([^)]*\))?\][\s\S]*?)*'
            r'public\s+(?:async\s+)?(?:Task<)?(?:IActionResult|ActionResult(?:<[^>]+>)?|'
            r'IResult|Results|Ok|Created|NoContent|BadRequest|NotFound|\w+Result|'
            r'(?:\w+))\>?\s+(\w+)\s*\(([^)]*)\)',
            re.MULTILINE
        )

        for match in action_pattern.finditer(content):
            attributes_block = match.group(1) or ""
            action_name = match.group(2)
            parameters = match.group(3)

            # Skip non-action methods
            if action_name.startswith("_") or action_name in ("Dispose", "ToString"):
                continue

            # Determine HTTP method
            http_method = EndpointMethod.GET  # default
            route = ""

            if "[HttpPost" in attributes_block:
                http_method = EndpointMethod.POST
            elif "[HttpPut" in attributes_block:
                http_method = EndpointMethod.PUT
            elif "[HttpDelete" in attributes_block:
                http_method = EndpointMethod.DELETE
            elif "[HttpPatch" in attributes_block:
                http_method = EndpointMethod.PATCH

            # Extract route
            route_match = re.search(r'\[(?:Http\w+|Route)\s*\(\s*["\']([^"\']+)["\']', attributes_block)
            if route_match:
                route = route_match.group(1)

            endpoint = AspNetCoreEndpoint(
                route=route,
                http_method=http_method,
                action_name=action_name,
                controller_name=controller_name,
                is_async="async" in match.group(0),
                requires_authorization="[Authorize" in attributes_block,
                file_path=str(file_path),
                line_number=content[:match.start()].count("\n") + 1
            )

            # Parse parameters
            if parameters.strip():
                for param in parameters.split(","):
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            endpoint.parameters.append({
                                "type": parts[-2],
                                "name": parts[-1]
                            })

            endpoints.append(endpoint)

        return endpoints

    def _detect_minimal_api(self, file_path: Path, content: str) -> List[MinimalApiEndpoint]:
        """Detect Minimal API endpoints."""
        endpoints = []

        pattern = re.compile(
            r'app\.Map(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']+)["\']',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            method_str = match.group(1).upper()
            route = match.group(2)

            http_method = EndpointMethod[method_str]

            endpoint = MinimalApiEndpoint(
                route=route,
                http_method=http_method,
                handler_type="lambda",  # Simplified detection
                file_path=str(file_path),
                line_number=content[:match.start()].count("\n") + 1,
                is_async="async" in content[match.end():match.end()+100]
            )

            endpoints.append(endpoint)

        return endpoints

    def _detect_middleware(self, file_path: Path, content: str) -> List[MiddlewareComponent]:
        """Detect middleware registrations."""
        middleware = []
        order = 0

        # Pattern for app.Use* calls
        pattern = re.compile(r'app\.(Use\w+|Map\w+)\s*\(', re.MULTILINE)

        for match in pattern.finditer(content):
            name = match.group(1)
            order += 1

            mw = MiddlewareComponent(
                name=name,
                registration_type=name,
                file_path=str(file_path),
                line_number=content[:match.start()].count("\n") + 1,
                order=order,
                is_terminal=name in ("UseEndpoints", "MapControllers", "MapRazorPages"),
                is_branching=name.startswith("Map")
            )

            middleware.append(mw)

        return middleware

    def _detect_di_registrations(self, file_path: Path, content: str) -> List[DiRegistration]:
        """Detect DI service registrations."""
        registrations = []

        patterns = [
            (r'services\.AddScoped<([^>]+)(?:,\s*([^>]+))?>\s*\(', ServiceLifetime.SCOPED),
            (r'services\.AddSingleton<([^>]+)(?:,\s*([^>]+))?>\s*\(', ServiceLifetime.SINGLETON),
            (r'services\.AddTransient<([^>]+)(?:,\s*([^>]+))?>\s*\(', ServiceLifetime.TRANSIENT),
            (r'builder\.Services\.AddScoped<([^>]+)(?:,\s*([^>]+))?>\s*\(', ServiceLifetime.SCOPED),
            (r'builder\.Services\.AddSingleton<([^>]+)(?:,\s*([^>]+))?>\s*\(', ServiceLifetime.SINGLETON),
            (r'builder\.Services\.AddTransient<([^>]+)(?:,\s*([^>]+))?>\s*\(', ServiceLifetime.TRANSIENT),
        ]

        for pattern, lifetime in patterns:
            for match in re.finditer(pattern, content):
                service_type = match.group(1)
                impl_type = match.group(2) if match.lastindex >= 2 else None

                reg = DiRegistration(
                    service_type=service_type,
                    implementation_type=impl_type,
                    lifetime=lifetime,
                    registration_method=f"Add{lifetime.value.capitalize()}",
                    file_path=str(file_path),
                    line_number=content[:match.start()].count("\n") + 1,
                    is_generic="<" in service_type
                )

                registrations.append(reg)

        return registrations

    def _detect_dbcontext(self, file_path: Path, content: str) -> Optional[EfCoreDbContext]:
        """Detect Entity Framework Core DbContext."""
        match = re.search(r'class\s+(\w+)\s*:\s*DbContext', content)
        if not match:
            return None

        class_name = match.group(1)

        dbcontext = EfCoreDbContext(
            file_path=str(file_path),
            class_name=class_name,
            loc=len(content.split("\n"))
        )

        # Detect DbSets
        for dbset_match in re.finditer(r'public\s+(?:virtual\s+)?DbSet<(\w+)>\s+(\w+)', content):
            dbcontext.db_sets.append({
                "entity_type": dbset_match.group(1),
                "name": dbset_match.group(2)
            })

        # Detect Fluent API usage
        if "OnModelCreating" in content and "modelBuilder" in content:
            dbcontext.uses_fluent_api = True

        # Detect seed data
        if "HasData(" in content:
            dbcontext.has_seed_data = True

        # Detect database provider
        if "UseSqlServer" in content:
            dbcontext.database_provider = "SqlServer"
        elif "UseNpgsql" in content or "UsePostgreSQL" in content:
            dbcontext.database_provider = "PostgreSQL"
        elif "UseSqlite" in content:
            dbcontext.database_provider = "SQLite"
        elif "UseMySql" in content:
            dbcontext.database_provider = "MySQL"

        return dbcontext

    def _detect_grpc_service(self, file_path: Path, content: str) -> Optional[GrpcService]:
        """Detect gRPC service implementation."""
        match = re.search(r'class\s+(\w+)\s*:\s*(\w+)\.(\w+)Base', content)
        if not match:
            return None

        class_name = match.group(1)
        proto_service = match.group(2)

        service = GrpcService(
            file_path=str(file_path),
            service_name=class_name,
            base_class=f"{proto_service}.{match.group(3)}Base",
            loc=len(content.split("\n"))
        )

        # Detect override methods (gRPC operations)
        for method_match in re.finditer(
            r'public\s+override\s+(?:async\s+)?Task<(\w+)>\s+(\w+)',
            content
        ):
            service.methods.append({
                "name": method_match.group(2),
                "return_type": method_match.group(1)
            })

        # Detect streaming
        if "IAsyncStreamReader" in content or "IServerStreamWriter" in content:
            service.uses_streaming = True

        return service

    async def _analyze_razor_file(self, file_path: Path, result: AspNetCoreAnalysisResult) -> None:
        """Analyze Razor/Blazor files."""
        try:
            content = file_path.read_text(encoding="utf-8")

            if file_path.suffix == ".razor":
                # Blazor component
                component = self._detect_blazor_component(file_path, content)
                if component:
                    result.blazor_components.append(component)
            else:
                # Razor Page
                page = self._detect_razor_page(file_path, content)
                if page:
                    result.razor_pages.append(page)

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")

    def _detect_blazor_component(self, file_path: Path, content: str) -> Optional[BlazorComponent]:
        """Detect Blazor component."""
        component = BlazorComponent(
            file_path=str(file_path),
            component_name=file_path.stem,
            component_type="unknown",
            loc=len(content.split("\n"))
        )

        # Detect component type
        if "@rendermode InteractiveServer" in content:
            component.component_type = "server"
        elif "@rendermode InteractiveWebAssembly" in content:
            component.component_type = "wasm"
        elif "@rendermode InteractiveAuto" in content:
            component.component_type = "hybrid"

        # Detect parameters
        for match in re.finditer(r'\[Parameter\]\s*public\s+(\w+)\s+(\w+)', content):
            component.parameters.append({
                "type": match.group(1),
                "name": match.group(2)
            })

        # Detect injected services
        for match in re.finditer(r'@inject\s+(\w+)\s+(\w+)', content):
            component.injected_services.append(match.group(1))

        # Detect lifecycle methods
        lifecycle = ["OnInitialized", "OnParametersSet", "OnAfterRender", "ShouldRender"]
        for method in lifecycle:
            if method in content or f"{method}Async" in content:
                component.lifecycle_methods.append(method)

        # Detect JS interop
        if "IJSRuntime" in content or "JSRuntime" in content:
            component.uses_js_interop = True

        return component

    def _detect_razor_page(self, file_path: Path, content: str) -> Optional[RazorPage]:
        """Detect Razor Page."""
        page = RazorPage(
            file_path=str(file_path),
            page_name=file_path.stem,
            loc=len(content.split("\n"))
        )

        # Detect @page directive
        page_match = re.search(r'@page\s*"?([^"\n]*)"?', content)
        if page_match:
            page.route = page_match.group(1).strip() or f"/{file_path.stem}"

        # Detect @model
        model_match = re.search(r'@model\s+(\w+)', content)
        if model_match:
            page.page_model_class = model_match.group(1)

        # Detect layout
        layout_match = re.search(r'@\{\s*Layout\s*=\s*"([^"]+)"', content)
        if layout_match:
            page.layout = layout_match.group(1)

        # Detect tag helpers
        if "@addTagHelper" in content or "asp-" in content:
            page.uses_tag_helpers = True

        return page

    async def _analyze_config_file(self, file_path: Path, result: AspNetCoreAnalysisResult) -> None:
        """Analyze configuration files."""
        try:
            content = file_path.read_text(encoding="utf-8")
            config = json.loads(content)

            # Extract top-level sections
            for key in config.keys():
                if key not in ("$schema", "Logging"):
                    section = ConfigurationSection(
                        name=key,
                        source=file_path.name
                    )
                    result.configuration_sections.append(section)

        except Exception as e:
            logger.warning(f"Failed to parse config {file_path}: {e}")

    def _detect_patterns(self, file_path: Path, content: str) -> List[AspNetCorePattern]:
        """Detect ASP.NET Core patterns and anti-patterns."""
        patterns = []

        for name, info in ASPNETCORE_PATTERNS.items():
            compiled = self._compiled_patterns[name]

            for match in compiled.finditer(content):
                pattern = AspNetCorePattern(
                    pattern_name=name,
                    pattern_category=info["category"],
                    file_path=str(file_path),
                    line_number=content[:match.start()].count("\n") + 1,
                    code_snippet=match.group(0)[:100],
                    recommendation=info.get("recommendation"),
                    severity="warning" if info["category"] == "anti-pattern" else "info"
                )
                patterns.append(pattern)

        return patterns

    def get_summary(self, result: AspNetCoreAnalysisResult) -> Dict[str, Any]:
        """Get a summary of the analysis result."""
        return {
            "projects": len(result.projects),
            "target_frameworks": list(set(
                p.target_framework.value for p in result.projects
            )),
            "controllers": {
                "total": result.total_controllers,
                "api": sum(1 for c in result.controllers if c.controller_type == ControllerType.API_CONTROLLER),
                "mvc": sum(1 for c in result.controllers if c.controller_type == ControllerType.MVC_CONTROLLER)
            },
            "endpoints": {
                "total": result.total_endpoints,
                "controller_actions": sum(len(c.endpoints) for c in result.controllers),
                "minimal_api": len(result.minimal_api_endpoints)
            },
            "components": {
                "blazor": len(result.blazor_components),
                "razor_pages": len(result.razor_pages),
                "grpc_services": len(result.grpc_services)
            },
            "infrastructure": {
                "di_registrations": result.total_services_registered,
                "middleware": len(result.middleware_pipeline),
                "db_contexts": len(result.db_contexts)
            },
            "patterns": {
                "total": len(result.patterns),
                "anti_patterns": sum(1 for p in result.patterns if p.pattern_category == "anti-pattern")
            },
            "loc": result.total_loc,
            "scan_duration_ms": result.scan_duration_ms
        }
