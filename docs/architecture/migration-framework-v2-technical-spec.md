# Applicatie Migratie Framework v2.0 - Technische Specificatie

**Document**: Technical Specification for MarQed Platform Integration
**Versie**: 2.0 (Layered Analysis Update)
**Datum**: 2025-12-16
**Status**: UPDATED - Layered Analysis Service Added

---

## 1. Executive Summary

### 1.1 Platform Status Assessment

**MarQed AI Agent Development Platform - Status: PRODUCTION-GRADE MATURE**

| Dimension | Metric | Assessment |
|-----------|--------|------------|
| **Backend Services** | 78 service classes | Enterprise-scale |
| **API Surface** | 400+ endpoints (70 modules) | Comprehensive |
| **Data Layer** | 103+ tables (31 migrations) | Well-structured |
| **Agent System** | 10 core + stack templates | Production-ready |
| **Test Coverage** | 582+ tests | Solid foundation |
| **Observability** | CCTrace + Cost Management | Full visibility |
| **Memory System** | Claude-Mem (Week 76) | Cutting-edge |
| **Graph Analysis** | Graph Persistence (Week 75) | Advanced |

**Maturity Classification**: **Tier 3 - Enterprise Platform**
- Tier 1: MVP (proof of concept)
- Tier 2: Production (single use-case)
- **Tier 3: Enterprise (multi-tenant, extensible)** ← Current
- Tier 4: Platform (ecosystem, marketplace)

### 1.2 Integration Scope

Het Migratie Framework v2.0 integreert als **uitbreiding** op het bestaande platform, niet als vervanging.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MARQED PLATFORM (Existing)                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    NEW: MIGRATION FRAMEWORK v2.0             │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │    │
│  │  │  Discovery  │ │  Spec Gen   │ │  Parity Validation  │    │    │
│  │  │   Engine    │ │   Engine    │ │       Engine        │    │    │
│  │  └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘    │    │
│  └─────────┼───────────────┼───────────────────┼───────────────┘    │
│            │               │                   │                     │
│  ┌─────────▼───────────────▼───────────────────▼───────────────┐    │
│  │                EXISTING SERVICES (Extend)                    │    │
│  │  MigrationAnalyzer │ BrownPaper │ Quinn │ Eliza │ Claude-Mem │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Layered Analysis Philosophy (Week 77-78 Update)

**BELANGRIJK**: Dit framework implementeert een **Layered Analysis** benadering, NIET een "simplified" of "MVP" aanpak.

#### 1.3.1 Core Principles

| Principe | Betekenis | Anti-Pattern |
|----------|-----------|--------------|
| **100% Coverage** | Elke regel, elke file, elk symbool wordt geanalyseerd | "Smart coverage" die dingen overslaat |
| **Layered Output** | 3 diepteniveaus voor verschillende stakeholders | One-size-fits-all rapportage |
| **Analyse ≠ Migratie** | Standalone analyse met OPTIONELE migratie | Analyse alleen als migratie-voorbereiding |
| **First-Class Legacy** | VBScript, Classic ASP, VB6 volledig ondersteund | Legacy als "edge case" behandelen |

#### 1.3.2 Decoupled Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYERED ANALYSIS APPROACH                                 │
│                                                                              │
│   FASE 1: ANALYSE (Standalone)                                              │
│   ───────────────────────────────────                                        │
│   │ Inventory → Deep Analysis → SWOT → Improvement Plan                     │
│   │                                                                          │
│   │ OUTPUT:                                                                  │
│   │ • Complete code coverage (100%)                                         │
│   │ • SWOT Matrix (Strengths, Weaknesses, Opportunities, Threats)           │
│   │ • Prioritized Improvement Backlog                                       │
│   │ • Executive / Management / Technical Reports                            │
│   └──────────────────────────────────────────────────────────────────────────│
│                                       │                                       │
│                                       ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐│
│   │                         DECISION POINT                                   ││
│   │   ○ IMPROVE IN PLACE - Use improvement backlog to fix current stack     ││
│   │   ○ MIGRATE - Continue to Migration Phase with analysis as foundation   ││
│   │   ○ REPLACE - Consider greenfield replacement based on analysis         ││
│   └─────────────────────────────────────────────────────────────────────────┘│
│                                       │                                       │
│                                       ▼ (Optional)                           │
│   FASE 2: MIGRATIE (If GO decision)                                         │
│   ──────────────────────────────────────                                     │
│   │ Target Architecture → Migration Plan → Execution → Parity Verification  │
│   └──────────────────────────────────────────────────────────────────────────│
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.3.3 VBScriptAnalyzerService (First-Class Support)

Classic ASP en VBScript krijgen **volledige** analyseondersteuning, niet als "legacy edge case":

```python
class VBScriptAnalyzerService:
    """
    Complete VBScript/Classic ASP analyzer.
    100% coverage, geen shortcuts.
    """

    # File parsing
    async def analyze(self, source_dir: str) -> VBScriptAnalysis
    async def extract_includes(self, file_path: str) -> List[IncludeRef]
    async def extract_functions(self, content: str) -> List[FunctionDef]

    # Pattern detection
    async def extract_sql_patterns(self, content: str) -> List[SQLPattern]
    async def detect_com_objects(self, content: str) -> List[COMObject]
    async def analyze_session_state(self, content: str) -> SessionAnalysis

    # Flow analysis
    async def map_data_flow(self, source_dir: str) -> DataFlowGraph
    async def trace_request_response(self, file_path: str) -> RequestResponseTrace
```

**Ondersteunde VBScript Constructies:**

| VBScript Construct | Analyse Support |
|-------------------|-----------------|
| `Function/Sub` definitions | ✅ Full extraction + parameters |
| `<!-- #include file/virtual -->` | ✅ Both include types |
| `Server.CreateObject` | ✅ COM object mapping |
| `ADODB.Connection/Recordset` | ✅ Database access patterns |
| Inline SQL strings | ✅ SQL injection detection |
| `Session/Application` vars | ✅ State management mapping |
| `Response.Write` | ✅ Output tracking |
| `Request.Form/QueryString` | ✅ Input source detection |
| `On Error Resume Next` | ✅ Error flow analysis |
| Include dependencies | ✅ Full dependency graph |

#### 1.3.4 SWOT Generator Service

Automatische sterkte/zwakte analyse:

```python
class SWOTGeneratorService:
    """Generate SWOT matrix from analysis results."""

    async def generate(self, analysis: ProjectAnalysis) -> SWOTMatrix:
        return SWOTMatrix(
            strengths=self._extract_strengths(analysis),
            weaknesses=self._extract_weaknesses(analysis),
            opportunities=self._identify_opportunities(analysis),
            threats=self._assess_threats(analysis)
        )

    async def prioritize_weaknesses(
        self, weaknesses: List[Weakness]
    ) -> List[PrioritizedWeakness]:
        """
        Prioriteer op basis van:
        - Business impact (high/medium/low)
        - Fix effort (days)
        - Risk if not fixed
        - Dependencies
        """
```

#### 1.3.5 Improvement Planner Service

Van zwaktes naar actionable backlog:

```python
class ImprovementPlannerService:
    """Convert SWOT weaknesses to prioritized improvement backlog."""

    async def create_improvement_plan(
        self,
        swot: SWOTMatrix,
        constraints: PlanningConstraints = None
    ) -> ImprovementPlan:
        """
        OUTPUT:
        - Geprioriteerde backlog van verbeteringen
        - Effort schattingen per item
        - Dependencies tussen items
        - Quick wins vs strategic improvements
        """
```

---

## 2. Discovery Engine - Technische Specificatie

### 2.1 Component Overview

```python
# backend/app/services/discovery_engine_service.py

class DiscoveryEngineService:
    """
    Unified discovery engine integrating framework components with
    existing MarQed analyzers.

    Responsibilities:
    - Orchestrate route crawling, code analysis, DB scanning
    - Integrate with existing DotNetAnalyzer, PHPAnalyzer, etc.
    - Feed results into BROWN_PAPER workflow
    - Store discoveries in Claude-Mem for progressive disclosure
    """
```

### 2.2 Route Crawler Specification

#### 2.2.1 Supported Frameworks

| Framework | Detection Pattern | Route Extraction Method |
|-----------|------------------|------------------------|
| ASP.NET MVC | `*.cshtml`, `RouteConfig.cs` | Attribute + Convention routing |
| ASP.NET WebForms | `*.aspx`, `*.aspx.cs` | Page-based URL mapping |
| ASP Classic | `*.asp` | File-based + QueryString parsing |
| PHP (Laravel) | `routes/*.php` | Route facade parsing |
| PHP (Legacy) | `*.php` | File-based URL mapping |
| Node.js (Express) | `app.get/post/put/delete` | AST extraction |

#### 2.2.2 Route Model

```python
@dataclass
class DiscoveredRoute:
    """Unified route representation across all frameworks"""

    # Identity
    route_id: str                      # UUID
    path: str                          # "/api/users/{id}"
    method: HttpMethod                 # GET, POST, PUT, DELETE, PATCH

    # Source
    source_file: str                   # "Controllers/UserController.cs"
    source_line: int                   # 45
    source_framework: FrameworkType    # ASP_NET_MVC, PHP_LARAVEL, etc.

    # Handler
    handler_class: Optional[str]       # "UserController"
    handler_method: Optional[str]      # "GetUser"
    handler_signature: Optional[str]   # "public async Task<IActionResult> GetUser(int id)"

    # Parameters
    path_params: List[RouteParam]      # [{name: "id", type: "int", required: True}]
    query_params: List[RouteParam]     # [{name: "include", type: "string", required: False}]
    body_schema: Optional[Dict]        # JSON Schema for request body

    # Response
    response_types: List[ResponseType] # [{status: 200, schema: {...}}, {status: 404, ...}]

    # Analysis Metadata
    complexity_score: float            # 0.0 - 1.0 (computed)
    security_flags: List[str]          # ["requires_auth", "sql_injection_risk"]
    business_rules: List[str]          # Extracted business rule IDs

    # Confidence
    extraction_confidence: float       # 0.0 - 1.0
    requires_manual_review: bool       # True if confidence < 0.7
```

#### 2.2.3 Route Crawler Implementation

```python
class RouteCrawlerService:
    """
    Multi-framework route discovery service.

    Extends existing MigrationAnalyzerService with deep route extraction.
    """

    def __init__(
        self,
        migration_analyzer: MigrationAnalyzerService,
        dotnet_analyzer: DotNetAnalyzerService,
        php_analyzer: PhpAnalyzerService,
        frontend_analyzer: FrontendAnalyzerService,
        graph_service: GraphPersistenceService,
        claude_mem: ClaudeMemService
    ):
        self.analyzers = {
            FrameworkType.ASP_NET_MVC: dotnet_analyzer,
            FrameworkType.ASP_NET_WEBFORMS: dotnet_analyzer,
            FrameworkType.PHP_LARAVEL: php_analyzer,
            FrameworkType.PHP_LEGACY: php_analyzer,
        }
        self.graph = graph_service
        self.memory = claude_mem

    async def crawl_routes(
        self,
        project_path: str,
        session_id: str
    ) -> RouteCrawlResult:
        """
        Main entry point for route discovery.

        Returns:
            RouteCrawlResult with all discovered routes and analysis
        """
        # 1. Detect framework(s) in use
        frameworks = await self._detect_frameworks(project_path)

        # 2. Run framework-specific crawlers in parallel
        route_tasks = [
            self._crawl_framework(project_path, fw)
            for fw in frameworks
        ]
        framework_routes = await asyncio.gather(*route_tasks)

        # 3. Merge and deduplicate routes
        all_routes = self._merge_routes(framework_routes)

        # 4. Enrich with security analysis (Quinn integration)
        enriched = await self._enrich_with_security(all_routes)

        # 5. Build route dependency graph
        await self.graph.store_route_graph(session_id, enriched)

        # 6. Store in Claude-Mem for later retrieval
        await self._store_in_memory(session_id, enriched)

        # 7. Generate analysis report
        return RouteCrawlResult(
            routes=enriched,
            framework_summary=self._summarize_frameworks(frameworks),
            security_summary=self._summarize_security(enriched),
            complexity_analysis=self._analyze_complexity(enriched),
            recommendations=await self._generate_recommendations(enriched)
        )

    async def _crawl_asp_net_mvc(
        self,
        project_path: str
    ) -> List[DiscoveredRoute]:
        """
        Extract routes from ASP.NET MVC projects.

        Handles:
        - Attribute routing: [Route("api/[controller]")]
        - Convention routing: RouteConfig.cs
        - Area routing: [Area("Admin")]
        """
        routes = []

        # Find all controllers
        controllers = await self._find_controllers(project_path, "*.cs")

        for controller_path in controllers:
            ast = await self._parse_csharp(controller_path)

            # Extract class-level route prefix
            class_route = self._extract_class_route(ast)

            # Extract action methods
            for method in self._find_action_methods(ast):
                route = DiscoveredRoute(
                    route_id=str(uuid4()),
                    path=self._combine_route(class_route, method.route),
                    method=self._map_http_method(method),
                    source_file=controller_path,
                    source_line=method.line,
                    source_framework=FrameworkType.ASP_NET_MVC,
                    handler_class=ast.class_name,
                    handler_method=method.name,
                    handler_signature=method.signature,
                    path_params=self._extract_path_params(method),
                    query_params=self._extract_query_params(method),
                    body_schema=self._extract_body_schema(method),
                    response_types=self._extract_responses(method),
                    complexity_score=self._calculate_complexity(method),
                    security_flags=[],  # Filled by Quinn
                    business_rules=[],  # Filled by rule extractor
                    extraction_confidence=0.9,
                    requires_manual_review=False
                )
                routes.append(route)

        return routes
```

### 2.3 Business Rule Extractor Specification

#### 2.3.1 Rule Model

```python
@dataclass
class BusinessRule:
    """Extracted business rule from legacy code"""

    rule_id: str                       # "BR-001"
    name: str                          # "OrderMinimumAmount"
    description: str                   # Human-readable description

    # Source
    source_file: str
    source_lines: Tuple[int, int]      # Start, end line
    source_code: str                   # Original code snippet

    # Classification
    rule_type: RuleType                # VALIDATION, CALCULATION, WORKFLOW, ACCESS_CONTROL
    domain: str                        # "Orders", "Customers", "Inventory"
    criticality: Criticality           # CRITICAL, HIGH, MEDIUM, LOW

    # Extraction
    extraction_method: str             # "pattern_match", "llm_analysis", "manual"
    confidence: float                  # 0.0 - 1.0

    # Dependencies
    depends_on: List[str]              # Other rule IDs
    affects_entities: List[str]        # ["Order", "Customer"]

    # Migration
    migration_complexity: str          # "simple", "moderate", "complex"
    suggested_implementation: str      # Modern implementation suggestion
    test_scenarios: List[str]          # Test cases to verify
```

#### 2.3.2 AI-Powered Rule Extraction

```python
class BusinessRuleExtractorService:
    """
    Extracts business rules from legacy code using pattern matching
    and LLM analysis.

    Integrates with:
    - LLMCouncilService: Multi-model validation of extracted rules
    - ClaudeMemService: Progressive rule discovery across sessions
    - GraphPersistenceService: Rule dependency tracking
    """

    # Pattern-based extraction for common rule types
    RULE_PATTERNS = {
        RuleType.VALIDATION: [
            r"if\s*\(\s*(\w+)\s*[<>=!]+\s*(\d+)\s*\)",  # Numeric comparisons
            r"\.Length\s*[<>=]+\s*(\d+)",               # Length checks
            r"Regex\.IsMatch\s*\(",                      # Format validation
            r"throw\s+new\s+\w*Exception",              # Business exceptions
        ],
        RuleType.CALCULATION: [
            r"(\w+)\s*=\s*(\w+)\s*[\+\-\*\/]\s*(\w+)",  # Arithmetic
            r"\.Sum\(|\.Average\(|\.Max\(|\.Min\(",     # Aggregations
            r"Math\.\w+\(",                             # Math operations
        ],
        RuleType.WORKFLOW: [
            r"if\s*\(\s*Status\s*==",                   # State checks
            r"\.State\s*=\s*\w+State\.",                # State transitions
            r"await\s+\w+Service\.",                    # Service calls
        ],
        RuleType.ACCESS_CONTROL: [
            r"\[Authorize",                             # Auth attributes
            r"User\.IsInRole\(",                        # Role checks
            r"\.HasPermission\(",                       # Permission checks
        ]
    }

    async def extract_rules(
        self,
        project_path: str,
        session_id: str,
        use_llm: bool = True
    ) -> RuleExtractionResult:
        """
        Extract business rules from legacy codebase.

        Strategy:
        1. Pattern matching for quick wins (high confidence)
        2. LLM analysis for complex rules (validated by council)
        3. Human review queue for uncertain extractions
        """
        rules = []

        # Phase 1: Pattern-based extraction
        pattern_rules = await self._extract_by_patterns(project_path)
        rules.extend(pattern_rules)

        # Phase 2: LLM-powered extraction (if enabled)
        if use_llm:
            # Find code sections not covered by patterns
            uncovered = await self._find_uncovered_sections(
                project_path,
                pattern_rules
            )

            # Use LLM Council for multi-model validation
            for section in uncovered:
                llm_rules = await self._extract_with_llm(section)

                # Validate with council (requires consensus)
                validated = await self.council.validate_rules(
                    llm_rules,
                    require_consensus=True,
                    min_confidence=0.7
                )
                rules.extend(validated)

        # Phase 3: Build rule dependency graph
        await self.graph.store_rule_dependencies(session_id, rules)

        # Phase 4: Store in Claude-Mem
        await self._store_rules_in_memory(session_id, rules)

        # Generate improvement recommendations from rules
        improvements = self._generate_improvements_from_rules(rules)

        return RuleExtractionResult(
            rules=rules,
            by_type=self._group_by_type(rules),
            by_domain=self._group_by_domain(rules),
            dependency_graph=await self.graph.get_rule_graph(session_id),
            improvements=improvements,  # NEW: Analysis → Improvements
            human_review_queue=self._get_uncertain_rules(rules)
        )

    def _generate_improvements_from_rules(
        self,
        rules: List[BusinessRule]
    ) -> List[MigrationImprovement]:
        """
        Convert detected weaknesses in rules into actionable improvements.

        This transforms "problems found" into "improvements recommended".
        """
        improvements = []

        for rule in rules:
            # Weakness: Hardcoded values
            if self._has_hardcoded_values(rule):
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-{rule.rule_id}-001",
                    source_rule=rule.rule_id,
                    weakness_detected="Hardcoded business values in code",
                    improvement_type=ImprovementType.CONFIGURATION,
                    recommendation="Extract to configuration/database",
                    implementation_hint="Use IOptions<T> pattern in .NET 8",
                    priority=Priority.HIGH,
                    effort_estimate="2-4 hours"
                ))

            # Weakness: Missing validation
            if rule.rule_type == RuleType.VALIDATION and rule.confidence < 0.8:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-{rule.rule_id}-002",
                    source_rule=rule.rule_id,
                    weakness_detected="Incomplete validation coverage",
                    improvement_type=ImprovementType.VALIDATION,
                    recommendation="Implement FluentValidation with complete rules",
                    implementation_hint="Create dedicated Validator class",
                    priority=Priority.CRITICAL,
                    effort_estimate="4-8 hours"
                ))

            # Weakness: Complex conditional logic
            if rule.complexity_score > 0.7:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-{rule.rule_id}-003",
                    source_rule=rule.rule_id,
                    weakness_detected=f"High cyclomatic complexity ({rule.complexity_score:.2f})",
                    improvement_type=ImprovementType.REFACTORING,
                    recommendation="Apply Strategy or State pattern",
                    implementation_hint="Extract to dedicated policy classes",
                    priority=Priority.MEDIUM,
                    effort_estimate="1-2 days"
                ))

            # Weakness: Security concern
            if any(flag in rule.security_flags for flag in ["sql_injection_risk", "xss_risk"]):
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-{rule.rule_id}-004",
                    source_rule=rule.rule_id,
                    weakness_detected=f"Security vulnerability: {rule.security_flags}",
                    improvement_type=ImprovementType.SECURITY,
                    recommendation="Implement parameterized queries and input sanitization",
                    implementation_hint="Use EF Core with LINQ, apply HtmlEncoder",
                    priority=Priority.CRITICAL,
                    effort_estimate="4-8 hours per occurrence"
                ))

        return improvements
```

### 2.4 Database Scanner Integration

```python
class EnhancedDatabaseScannerService:
    """
    Extends existing DatabaseAnalyzerService with:
    - Stored procedure analysis
    - Trigger dependency mapping
    - Data quality profiling
    - Migration complexity scoring
    """

    def __init__(
        self,
        base_analyzer: DatabaseAnalyzerService,
        graph_service: GraphPersistenceService
    ):
        self.base = base_analyzer
        self.graph = graph_service

    async def deep_scan(
        self,
        connection_string: str,
        session_id: str
    ) -> DatabaseScanResult:
        """
        Comprehensive database analysis for migration planning.
        """
        # Use existing analyzer for base schema
        base_result = await self.base.analyze_schema(connection_string)

        # Enhanced analysis
        stored_procs = await self._analyze_stored_procedures(connection_string)
        triggers = await self._analyze_triggers(connection_string)
        views = await self._analyze_views(connection_string)

        # Build dependency graph
        await self.graph.store_database_graph(
            session_id,
            tables=base_result.tables,
            procedures=stored_procs,
            triggers=triggers,
            views=views
        )

        # Generate data migration plan
        migration_plan = self._generate_migration_plan(
            base_result,
            stored_procs,
            triggers
        )

        # Identify improvements from weaknesses
        improvements = self._generate_db_improvements(
            base_result,
            stored_procs,
            triggers
        )

        return DatabaseScanResult(
            schema=base_result,
            stored_procedures=stored_procs,
            triggers=triggers,
            views=views,
            dependency_graph=await self.graph.get_database_graph(session_id),
            migration_plan=migration_plan,
            improvements=improvements,
            estimated_effort=self._estimate_migration_effort(migration_plan)
        )

    def _generate_db_improvements(
        self,
        schema: SchemaAnalysis,
        procs: List[StoredProcedure],
        triggers: List[Trigger]
    ) -> List[MigrationImprovement]:
        """
        Convert database weaknesses into improvement recommendations.
        """
        improvements = []

        # Weakness: Missing indexes
        for table in schema.tables:
            missing = self._find_missing_indexes(table)
            for col in missing:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-DB-{table.name}-IDX-{col}",
                    weakness_detected=f"Missing index on frequently queried column: {table.name}.{col}",
                    improvement_type=ImprovementType.PERFORMANCE,
                    recommendation=f"Add index on {table.name}.{col}",
                    implementation_hint="CREATE INDEX IX_{table}_{col} ON {table}({col})",
                    priority=Priority.MEDIUM,
                    effort_estimate="15 minutes + testing"
                ))

        # Weakness: Complex stored procedures
        for proc in procs:
            if proc.line_count > 200:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-DB-PROC-{proc.name}",
                    weakness_detected=f"Complex stored procedure: {proc.name} ({proc.line_count} lines)",
                    improvement_type=ImprovementType.REFACTORING,
                    recommendation="Migrate business logic to application layer",
                    implementation_hint="Create dedicated service class with EF Core",
                    priority=Priority.HIGH,
                    effort_estimate=f"{proc.line_count // 50} hours"
                ))

        # Weakness: Triggers (anti-pattern for modern apps)
        for trigger in triggers:
            improvements.append(MigrationImprovement(
                improvement_id=f"IMP-DB-TRIG-{trigger.name}",
                weakness_detected=f"Database trigger: {trigger.name} on {trigger.table}",
                improvement_type=ImprovementType.ARCHITECTURE,
                recommendation="Replace with domain events or application-level hooks",
                implementation_hint="Use MediatR notifications or EF Core interceptors",
                priority=Priority.HIGH,
                effort_estimate="2-4 hours"
            ))

        return improvements
```

---

## 3. Specification Generation Engine

### 3.1 OpenAPI Generator

```python
class OpenAPIGeneratorService:
    """
    Generates OpenAPI 3.1 specifications from discovered routes.

    Integrates with:
    - RouteCrawlerService: Source of route information
    - BusinessRuleExtractorService: Validation rules for schemas
    - LLMCouncilService: AI-assisted description generation
    """

    async def generate_spec(
        self,
        routes: List[DiscoveredRoute],
        rules: List[BusinessRule],
        session_id: str
    ) -> OpenAPISpec:
        """
        Generate complete OpenAPI specification from discoveries.
        """
        spec = OpenAPISpec(
            openapi="3.1.0",
            info=self._generate_info(session_id),
            servers=[],
            paths={},
            components=Components(schemas={}, securitySchemes={})
        )

        # Group routes by path
        path_groups = self._group_by_path(routes)

        for path, path_routes in path_groups.items():
            path_item = PathItem()

            for route in path_routes:
                operation = await self._generate_operation(route, rules)
                setattr(path_item, route.method.lower(), operation)

            spec.paths[path] = path_item

        # Generate component schemas from body schemas
        spec.components.schemas = self._generate_schemas(routes, rules)

        # Generate security schemes
        spec.components.securitySchemes = self._generate_security_schemes(routes)

        # Validate generated spec
        validation_result = await self._validate_spec(spec)

        return OpenAPIGenerationResult(
            spec=spec,
            validation=validation_result,
            coverage_report=self._calculate_coverage(routes, spec),
            manual_review_items=self._get_review_items(routes, spec)
        )

    async def _generate_operation(
        self,
        route: DiscoveredRoute,
        rules: List[BusinessRule]
    ) -> Operation:
        """
        Generate OpenAPI Operation from discovered route.
        """
        # Use LLM to generate human-readable descriptions
        description = await self.llm.generate_description(
            route.handler_method,
            route.source_code_context
        )

        # Map parameters
        parameters = []
        for param in route.path_params + route.query_params:
            parameters.append(Parameter(
                name=param.name,
                in_="path" if param in route.path_params else "query",
                required=param.required,
                schema=self._map_type_to_schema(param.type),
                description=await self.llm.generate_param_description(param)
            ))

        # Map request body
        request_body = None
        if route.body_schema:
            request_body = RequestBody(
                required=True,
                content={
                    "application/json": MediaType(
                        schema=self._enhance_schema_with_rules(
                            route.body_schema,
                            rules
                        )
                    )
                }
            )

        # Map responses
        responses = {}
        for resp in route.response_types:
            responses[str(resp.status)] = Response(
                description=self._get_status_description(resp.status),
                content={
                    "application/json": MediaType(schema=resp.schema)
                } if resp.schema else None
            )

        return Operation(
            operationId=self._generate_operation_id(route),
            summary=route.handler_method,
            description=description,
            parameters=parameters,
            requestBody=request_body,
            responses=responses,
            tags=[route.handler_class],
            security=self._get_security_requirements(route)
        )
```

### 3.2 Screen Flow Generator

```python
class ScreenFlowGeneratorService:
    """
    Generates UI flow documentation from WebForms/ASP pages.

    Output formats:
    - Mermaid diagrams (for documentation)
    - JSON flow definitions (for tooling)
    - Markdown documentation
    """

    async def generate_flows(
        self,
        project_path: str,
        session_id: str
    ) -> ScreenFlowResult:
        """
        Analyze UI files and generate flow documentation.
        """
        # Find all UI files
        aspx_files = await self._find_files(project_path, "*.aspx")
        cshtml_files = await self._find_files(project_path, "*.cshtml")

        # Extract screens
        screens = []
        for file in aspx_files + cshtml_files:
            screen = await self._analyze_screen(file)
            screens.append(screen)

        # Build navigation graph
        nav_graph = self._build_navigation_graph(screens)

        # Detect user journeys
        journeys = self._detect_user_journeys(nav_graph)

        # Generate Mermaid diagrams
        diagrams = self._generate_mermaid_diagrams(nav_graph, journeys)

        # Identify UI improvements
        improvements = self._generate_ui_improvements(screens)

        return ScreenFlowResult(
            screens=screens,
            navigation_graph=nav_graph,
            user_journeys=journeys,
            mermaid_diagrams=diagrams,
            improvements=improvements,
            migration_recommendations=self._generate_ui_migration_plan(screens)
        )

    def _generate_ui_improvements(
        self,
        screens: List[Screen]
    ) -> List[MigrationImprovement]:
        """
        Identify UI weaknesses and recommend improvements.
        """
        improvements = []

        for screen in screens:
            # Weakness: ViewState usage
            if screen.uses_viewstate:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-UI-{screen.name}-VS",
                    weakness_detected="ViewState dependency (performance impact)",
                    improvement_type=ImprovementType.ARCHITECTURE,
                    recommendation="Migrate to Blazor component state or API calls",
                    implementation_hint="Use @inject services and OnInitializedAsync",
                    priority=Priority.HIGH,
                    effort_estimate="4-8 hours per screen"
                ))

            # Weakness: Inline JavaScript
            if screen.inline_js_count > 5:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-UI-{screen.name}-JS",
                    weakness_detected=f"Excessive inline JavaScript ({screen.inline_js_count} blocks)",
                    improvement_type=ImprovementType.CODE_QUALITY,
                    recommendation="Extract to TypeScript modules",
                    implementation_hint="Create dedicated .ts files, use ES modules",
                    priority=Priority.MEDIUM,
                    effort_estimate="2-4 hours"
                ))

            # Weakness: No responsive design
            if not screen.has_responsive_meta:
                improvements.append(MigrationImprovement(
                    improvement_id=f"IMP-UI-{screen.name}-RWD",
                    weakness_detected="Missing responsive design",
                    improvement_type=ImprovementType.UX,
                    recommendation="Implement mobile-first responsive layout",
                    implementation_hint="Use Tailwind CSS or Bootstrap 5 grid",
                    priority=Priority.MEDIUM,
                    effort_estimate="2-4 hours per screen"
                ))

        return improvements
```

---

## 4. Parity Verification Engine

### 4.1 Overview

```python
class ParityVerificationService:
    """
    Continuous validation that migrated application maintains
    functional parity with legacy system.

    Integrates with:
    - Playwright MCP: Browser automation for E2E tests
    - Tessa Agent: Test strategy and coverage
    - Claude-Mem: Test result history and patterns
    """
```

### 4.2 Parity Test Generator

```python
class ParityTestGeneratorService:
    """
    Auto-generates Playwright tests from discovered routes and screens.
    """

    async def generate_tests(
        self,
        routes: List[DiscoveredRoute],
        screens: List[Screen],
        rules: List[BusinessRule],
        session_id: str
    ) -> ParityTestSuite:
        """
        Generate comprehensive parity test suite.
        """
        tests = []

        # API parity tests
        for route in routes:
            test = await self._generate_api_test(route, rules)
            tests.append(test)

        # UI parity tests
        for screen in screens:
            test = await self._generate_ui_test(screen)
            tests.append(test)

        # Business rule tests
        for rule in rules:
            test = await self._generate_rule_test(rule)
            tests.append(test)

        return ParityTestSuite(
            tests=tests,
            playwright_config=self._generate_playwright_config(),
            ci_config=self._generate_ci_config(),
            coverage_targets=self._calculate_coverage_targets(routes, screens, rules)
        )

    async def _generate_api_test(
        self,
        route: DiscoveredRoute,
        rules: List[BusinessRule]
    ) -> ParityTest:
        """
        Generate API parity test comparing legacy vs new responses.
        """
        # Find applicable business rules
        applicable_rules = [r for r in rules if r.affects_route(route)]

        # Generate test scenarios
        scenarios = []

        # Happy path
        scenarios.append(TestScenario(
            name=f"{route.handler_method}_success",
            type="happy_path",
            input=self._generate_valid_input(route),
            expected_status=200
        ))

        # Validation scenarios from rules
        for rule in applicable_rules:
            if rule.rule_type == RuleType.VALIDATION:
                scenarios.append(TestScenario(
                    name=f"{route.handler_method}_validation_{rule.name}",
                    type="validation",
                    input=self._generate_invalid_input(route, rule),
                    expected_status=400,
                    expected_error=rule.error_message
                ))

        # Edge cases
        scenarios.extend(self._generate_edge_cases(route))

        return ParityTest(
            test_id=f"PARITY-API-{route.route_id}",
            route=route,
            scenarios=scenarios,
            playwright_code=self._generate_playwright_api_test(route, scenarios)
        )

    def _generate_playwright_api_test(
        self,
        route: DiscoveredRoute,
        scenarios: List[TestScenario]
    ) -> str:
        """
        Generate Playwright test code for API parity verification.
        """
        return f'''
import {{ test, expect }} from '@playwright/test';

test.describe('{route.handler_class} - {route.handler_method}', () => {{
  const LEGACY_URL = process.env.LEGACY_BASE_URL;
  const NEW_URL = process.env.NEW_BASE_URL;

  {self._generate_scenario_tests(route, scenarios)}

  test('response structure parity', async ({{ request }}) => {{
    // Call both systems with same input
    const legacyResponse = await request.{route.method.lower()}(
      `${{LEGACY_URL}}{route.path}`,
      {self._generate_request_options(route)}
    );

    const newResponse = await request.{route.method.lower()}(
      `${{NEW_URL}}{route.path}`,
      {self._generate_request_options(route)}
    );

    // Compare status codes
    expect(newResponse.status()).toBe(legacyResponse.status());

    // Compare response structure (not exact values for dynamic data)
    const legacyBody = await legacyResponse.json();
    const newBody = await newResponse.json();

    expect(Object.keys(newBody).sort()).toEqual(Object.keys(legacyBody).sort());
  }});

  test('performance parity', async ({{ request }}) => {{
    const iterations = 10;
    let legacyTimes = [];
    let newTimes = [];

    for (let i = 0; i < iterations; i++) {{
      const legacyStart = Date.now();
      await request.{route.method.lower()}(`${{LEGACY_URL}}{route.path}`);
      legacyTimes.push(Date.now() - legacyStart);

      const newStart = Date.now();
      await request.{route.method.lower()}(`${{NEW_URL}}{route.path}`);
      newTimes.push(Date.now() - newStart);
    }}

    const legacyAvg = legacyTimes.reduce((a, b) => a + b) / iterations;
    const newAvg = newTimes.reduce((a, b) => a + b) / iterations;

    // New system should not be more than 20% slower
    expect(newAvg).toBeLessThan(legacyAvg * 1.2);
  }});
}});
'''
```

### 4.3 Side-by-Side Runner

```python
class SideBySideRunnerService:
    """
    Orchestrates parallel execution against legacy and new systems.
    """

    async def run_parity_check(
        self,
        test_suite: ParityTestSuite,
        legacy_url: str,
        new_url: str,
        session_id: str
    ) -> ParityCheckResult:
        """
        Execute parity tests and compare results.
        """
        results = []

        for test in test_suite.tests:
            # Run against both systems
            legacy_result = await self._execute_test(test, legacy_url)
            new_result = await self._execute_test(test, new_url)

            # Compare results
            comparison = self._compare_results(legacy_result, new_result)

            results.append(ParityTestResult(
                test=test,
                legacy_result=legacy_result,
                new_result=new_result,
                comparison=comparison,
                passed=comparison.is_equivalent
            ))

        # Calculate overall parity score
        parity_score = self._calculate_parity_score(results)

        # Store results in Claude-Mem
        await self.claude_mem.capture_observation(
            session_id=session_id,
            content=f"Parity check completed: {parity_score:.1%} equivalent",
            tags=["parity", "testing", "migration"],
            priority="high" if parity_score < 0.95 else "normal"
        )

        # Generate improvement recommendations from failures
        improvements = self._generate_improvements_from_failures(results)

        return ParityCheckResult(
            session_id=session_id,
            total_tests=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if not r.passed),
            parity_score=parity_score,
            results=results,
            improvements=improvements,
            recommendation=self._generate_recommendation(parity_score)
        )

    def _generate_improvements_from_failures(
        self,
        results: List[ParityTestResult]
    ) -> List[MigrationImprovement]:
        """
        Convert test failures into actionable improvements.
        """
        improvements = []

        for result in results:
            if not result.passed:
                comparison = result.comparison

                if comparison.status_mismatch:
                    improvements.append(MigrationImprovement(
                        improvement_id=f"IMP-PARITY-{result.test.test_id}-STATUS",
                        weakness_detected=f"Status code mismatch: legacy={comparison.legacy_status}, new={comparison.new_status}",
                        improvement_type=ImprovementType.FUNCTIONAL,
                        recommendation="Align response status codes with legacy behavior",
                        implementation_hint=f"Check {result.test.route.handler_method} implementation",
                        priority=Priority.CRITICAL,
                        effort_estimate="2-4 hours"
                    ))

                if comparison.response_structure_diff:
                    improvements.append(MigrationImprovement(
                        improvement_id=f"IMP-PARITY-{result.test.test_id}-STRUCT",
                        weakness_detected=f"Response structure differs: missing={comparison.missing_fields}",
                        improvement_type=ImprovementType.FUNCTIONAL,
                        recommendation="Ensure response DTOs match legacy structure",
                        implementation_hint="Add missing properties to response model",
                        priority=Priority.HIGH,
                        effort_estimate="1-2 hours"
                    ))

                if comparison.performance_regression:
                    improvements.append(MigrationImprovement(
                        improvement_id=f"IMP-PARITY-{result.test.test_id}-PERF",
                        weakness_detected=f"Performance regression: {comparison.performance_diff_percent:.0%} slower",
                        improvement_type=ImprovementType.PERFORMANCE,
                        recommendation="Optimize query or add caching",
                        implementation_hint="Profile with dotnet-trace, check N+1 queries",
                        priority=Priority.MEDIUM,
                        effort_estimate="4-8 hours"
                    ))

        return improvements
```

---

## 5. Workflow Integration

### 5.1 BROWN_PAPER Integration

```python
class EnhancedBrownPaperWorkflow:
    """
    Enhanced BROWN_PAPER workflow with Discovery Engine integration.

    The Discovery Engine pre-populates answers and generates
    improvement recommendations automatically.
    """

    async def start_enhanced_session(
        self,
        project_path: str,
        project_name: str
    ) -> EnhancedBrownPaperSession:
        """
        Start BROWN_PAPER session with automatic discovery.
        """
        session_id = str(uuid4())

        # Run Discovery Engine
        discovery = await self.discovery_engine.full_discovery(
            project_path=project_path,
            session_id=session_id
        )

        # Pre-populate BMAD answers from discovery
        pre_populated_answers = {
            # Q1: Current System Overview
            1: self._format_system_overview(discovery),

            # Q2: Pain Points (from detected weaknesses)
            2: self._format_pain_points(discovery.improvements),

            # Q3: Target State (from standards analysis)
            3: self._format_target_state(discovery.standards_gaps),

            # Q4: Data Migration (from DB scanner)
            4: self._format_data_migration(discovery.database_scan),

            # Q5: Risks (from complexity analysis)
            5: self._format_risks(discovery.complexity_analysis),

            # Q6: Timeline (from Eliza estimates)
            6: self._format_timeline(discovery.estimates),

            # Q7: Resources (from effort analysis)
            7: self._format_resources(discovery.effort_analysis),

            # Q8: Go/No-Go Criteria
            8: self._format_criteria(discovery)
        }

        # Create session with pre-populated data
        session = EnhancedBrownPaperSession(
            session_id=session_id,
            project_name=project_name,
            project_path=project_path,
            discovery_result=discovery,
            pre_populated_answers=pre_populated_answers,
            improvements=discovery.all_improvements,  # All discovered improvements
            status=BrownPaperStatus.QUESTIONS
        )

        return session

    def _format_pain_points(
        self,
        improvements: List[MigrationImprovement]
    ) -> str:
        """
        Format discovered improvements as pain points for BMAD Q2.
        """
        critical = [i for i in improvements if i.priority == Priority.CRITICAL]
        high = [i for i in improvements if i.priority == Priority.HIGH]

        lines = ["## Automatisch Gedetecteerde Pain Points\n"]

        if critical:
            lines.append("### Kritieke Issues")
            for imp in critical:
                lines.append(f"- **{imp.weakness_detected}**")
                lines.append(f"  - Aanbeveling: {imp.recommendation}")
                lines.append(f"  - Geschatte effort: {imp.effort_estimate}")

        if high:
            lines.append("\n### Hoge Prioriteit Issues")
            for imp in high:
                lines.append(f"- {imp.weakness_detected}")
                lines.append(f"  - Aanbeveling: {imp.recommendation}")

        return "\n".join(lines)
```

### 5.2 Full Migration Workflow

```python
class FullMigrationWorkflowService:
    """
    Complete migration workflow: Discovery → Spec → Code → Verify

    Integrates all framework components with MarQed agents.
    """

    WORKFLOW_STAGES = [
        ("discovery", "Miguel", "Route and code analysis"),
        ("specification", "Felix", "OpenAPI and flow documentation"),
        ("planning", "Paul", "Sprint planning and resource allocation"),
        ("implementation", "Stack Agents", "Code generation and migration"),
        ("verification", "Tessa", "Parity testing and validation"),
        ("security", "Quinn", "Security audit and hardening"),
        ("documentation", "Diana", "Final documentation"),
    ]

    async def execute_full_workflow(
        self,
        project_path: str,
        target_stack: str = "dotnet8_blazor"
    ) -> FullMigrationResult:
        """
        Execute complete migration workflow with all agents.
        """
        session_id = str(uuid4())
        improvements = []

        # Stage 1: Discovery
        await self._update_status(session_id, "discovery", "in_progress")
        discovery = await self.discovery_engine.full_discovery(
            project_path, session_id
        )
        improvements.extend(discovery.improvements)
        await self._update_status(session_id, "discovery", "complete")

        # Stage 2: Specification Generation
        await self._update_status(session_id, "specification", "in_progress")
        specs = await self.spec_generator.generate_all(
            routes=discovery.routes,
            screens=discovery.screens,
            rules=discovery.business_rules,
            session_id=session_id
        )
        improvements.extend(specs.improvements)
        await self._update_status(session_id, "specification", "complete")

        # Stage 3: Planning (with LLM Council validation)
        await self._update_status(session_id, "planning", "in_progress")
        plan = await self.planning_service.create_migration_plan(
            discovery=discovery,
            specs=specs,
            target_stack=target_stack
        )

        # Council validation of plan
        council_result = await self.council.validate_plan(
            plan=plan,
            require_consensus=True
        )

        if not council_result.approved:
            # Human review required
            await self._request_human_review(session_id, council_result)

        await self._update_status(session_id, "planning", "complete")

        # Stage 4: Implementation (scaffold generation)
        await self._update_status(session_id, "implementation", "in_progress")
        implementation = await self.code_generator.generate_scaffold(
            specs=specs,
            target_stack=target_stack
        )
        await self._update_status(session_id, "implementation", "complete")

        # Stage 5: Parity Verification
        await self._update_status(session_id, "verification", "in_progress")
        parity = await self.parity_service.run_parity_check(
            test_suite=specs.parity_tests,
            legacy_url=discovery.detected_urls.legacy,
            new_url=implementation.deployed_url,
            session_id=session_id
        )
        improvements.extend(parity.improvements)
        await self._update_status(session_id, "verification", "complete")

        # Stage 6: Security Audit
        await self._update_status(session_id, "security", "in_progress")
        security = await self.security_service.audit(
            implementation.generated_code,
            owasp_check=True,
            healthcare_compliance=True
        )
        improvements.extend(security.improvements)
        await self._update_status(session_id, "security", "complete")

        # Stage 7: Documentation
        await self._update_status(session_id, "documentation", "in_progress")
        docs = await self.doc_generator.generate_all(
            discovery=discovery,
            specs=specs,
            implementation=implementation,
            parity=parity
        )
        await self._update_status(session_id, "documentation", "complete")

        # Consolidate all improvements
        consolidated_improvements = self._consolidate_improvements(improvements)

        return FullMigrationResult(
            session_id=session_id,
            discovery=discovery,
            specifications=specs,
            plan=plan,
            implementation=implementation,
            parity_result=parity,
            security_audit=security,
            documentation=docs,
            improvements=consolidated_improvements,  # All improvements in one place
            overall_status=self._calculate_overall_status(parity, security)
        )
```

---

## 6. API Endpoints

### 6.1 New Endpoints

```python
# backend/app/api/migration_framework.py

router = APIRouter(prefix="/api/migration-framework", tags=["Migration Framework v2"])

# Discovery Engine
@router.post("/discovery/start")
async def start_discovery(request: DiscoveryRequest) -> DiscoverySession

@router.get("/discovery/{session_id}/status")
async def get_discovery_status(session_id: str) -> DiscoveryStatus

@router.get("/discovery/{session_id}/routes")
async def get_discovered_routes(session_id: str) -> List[DiscoveredRoute]

@router.get("/discovery/{session_id}/rules")
async def get_business_rules(session_id: str) -> List[BusinessRule]

@router.get("/discovery/{session_id}/improvements")
async def get_improvements(session_id: str) -> List[MigrationImprovement]

# Specification Generation
@router.post("/specs/generate")
async def generate_specifications(request: SpecGenerationRequest) -> SpecGenerationResult

@router.get("/specs/{session_id}/openapi")
async def get_openapi_spec(session_id: str) -> OpenAPISpec

@router.get("/specs/{session_id}/screenflows")
async def get_screen_flows(session_id: str) -> ScreenFlowResult

# Parity Verification
@router.post("/parity/generate-tests")
async def generate_parity_tests(request: ParityTestRequest) -> ParityTestSuite

@router.post("/parity/run")
async def run_parity_check(request: ParityRunRequest) -> ParityCheckResult

@router.get("/parity/{session_id}/results")
async def get_parity_results(session_id: str) -> ParityCheckResult

# Full Workflow
@router.post("/workflow/start")
async def start_full_workflow(request: FullWorkflowRequest) -> WorkflowSession

@router.get("/workflow/{session_id}/status")
async def get_workflow_status(session_id: str) -> WorkflowStatus

@router.post("/workflow/{session_id}/approve-stage")
async def approve_workflow_stage(session_id: str, stage: str) -> WorkflowStatus
```

### 6.2 Endpoint Count

| Category | New Endpoints | Existing Endpoints | Total |
|----------|---------------|-------------------|-------|
| Discovery | 5 | 0 | 5 |
| Specifications | 3 | 0 | 3 |
| Parity | 3 | 0 | 3 |
| Workflow | 3 | 0 | 3 |
| **Total New** | **14** | - | **14** |
| **Platform Total** | - | 400+ | **414+** |

---

## 7. Database Schema

### 7.1 New Tables

```sql
-- Migration 032: Migration Framework v2 Tables

-- Discovery Sessions
CREATE TABLE discovery_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    project_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Discovered Routes
CREATE TABLE discovered_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) REFERENCES discovery_sessions(session_id),
    route_id VARCHAR(100) UNIQUE NOT NULL,
    path TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    source_file TEXT,
    source_line INTEGER,
    source_framework VARCHAR(50),
    handler_class TEXT,
    handler_method TEXT,
    parameters JSONB DEFAULT '[]',
    response_types JSONB DEFAULT '[]',
    complexity_score FLOAT,
    security_flags JSONB DEFAULT '[]',
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Business Rules
CREATE TABLE business_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) REFERENCES discovery_sessions(session_id),
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_file TEXT,
    source_lines INT4RANGE,
    source_code TEXT,
    rule_type VARCHAR(50),
    domain VARCHAR(100),
    criticality VARCHAR(20),
    confidence FLOAT,
    depends_on JSONB DEFAULT '[]',
    migration_complexity VARCHAR(20),
    suggested_implementation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Migration Improvements
CREATE TABLE migration_improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) REFERENCES discovery_sessions(session_id),
    improvement_id VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50),  -- 'route', 'rule', 'database', 'ui', 'parity'
    source_id VARCHAR(100),   -- Reference to source item
    weakness_detected TEXT NOT NULL,
    improvement_type VARCHAR(50),
    recommendation TEXT NOT NULL,
    implementation_hint TEXT,
    priority VARCHAR(20),
    effort_estimate VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Parity Test Results
CREATE TABLE parity_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) REFERENCES discovery_sessions(session_id),
    test_id VARCHAR(100) NOT NULL,
    route_id VARCHAR(100) REFERENCES discovered_routes(route_id),
    legacy_status INTEGER,
    new_status INTEGER,
    status_match BOOLEAN,
    response_match BOOLEAN,
    performance_legacy_ms INTEGER,
    performance_new_ms INTEGER,
    performance_regression BOOLEAN,
    passed BOOLEAN,
    failure_details JSONB,
    executed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_routes_session ON discovered_routes(session_id);
CREATE INDEX ix_rules_session ON business_rules(session_id);
CREATE INDEX ix_improvements_session ON migration_improvements(session_id);
CREATE INDEX ix_improvements_priority ON migration_improvements(priority);
CREATE INDEX ix_parity_session ON parity_test_results(session_id);
```

### 7.2 Table Summary

| New Tables | Purpose |
|------------|---------|
| discovery_sessions | Discovery workflow tracking |
| discovered_routes | Extracted routes from legacy code |
| business_rules | Extracted business rules |
| migration_improvements | Weakness → Improvement mapping |
| parity_test_results | Side-by-side test results |
| **Total New** | **5 tables** |
| **Platform Total** | **108+ tables** |

---

## 8. Implementation Roadmap

### Phase 1: Discovery Engine (Week 77-78)

| Day | Deliverable | Effort |
|-----|-------------|--------|
| 1 | RouteCrawlerService base + ASP.NET MVC | 8h |
| 2 | VBScript/Classic ASP parser | 8h |
| 3 | BusinessRuleExtractorService + patterns | 8h |
| 4 | LLM-powered rule extraction | 6h |
| 5 | EnhancedDatabaseScanner | 6h |
| 6 | Improvement generation from weaknesses | 4h |
| 7 | API endpoints + tests (25) | 8h |
| 8 | Integration with BROWN_PAPER | 6h |
| 9 | Claude-Mem integration | 4h |
| 10 | Documentation + final tests | 4h |

**Deliverables**: ~2,500 lines, 55 tests

### Phase 2: Specification Generation (Week 79)

| Day | Deliverable | Effort |
|-----|-------------|--------|
| 1 | OpenAPIGeneratorService | 8h |
| 2 | ScreenFlowGeneratorService | 6h |
| 3 | LLM description generation | 4h |
| 4 | UI improvement detection | 4h |
| 5 | API endpoints + tests (20) | 6h |

**Deliverables**: ~1,200 lines, 30 tests

### Phase 3: Parity Verification (Week 80)

| Day | Deliverable | Effort |
|-----|-------------|--------|
| 1 | ParityTestGeneratorService | 6h |
| 2 | Playwright test templates | 6h |
| 3 | SideBySideRunnerService | 6h |
| 4 | Improvement extraction from failures | 4h |
| 5 | API endpoints + tests (15) | 6h |

**Deliverables**: ~1,000 lines, 25 tests

### Phase 4: Workflow Integration (Week 81)

| Day | Deliverable | Effort |
|-----|-------------|--------|
| 1 | EnhancedBrownPaperWorkflow | 6h |
| 2 | FullMigrationWorkflowService | 8h |
| 3 | Council integration | 4h |
| 4 | Dashboard updates | 6h |
| 5 | E2E tests + documentation | 6h |

**Deliverables**: ~1,000 lines, 20 tests

---

## 9. Summary

### 9.1 Totals

| Metric | Value |
|--------|-------|
| New Services | 8 |
| New API Endpoints | 14 |
| New Database Tables | 5 |
| New Lines of Code | ~5,700 |
| New Tests | 130 |
| Implementation Weeks | 4-5 |

### 9.2 Key Innovation: Weakness → Improvement Pipeline

Het belangrijkste verschil met het originele framework is de **automatische transformatie van gedetecteerde zwaktes naar concrete verbetervoorstellen**:

```
Legacy Code → Discovery → Weaknesses → Improvements → BROWN_PAPER → Migration Plan
                           ↓
                    [Automatic]
                    - Security issues → Security fixes
                    - Complexity → Refactoring suggestions
                    - Missing tests → Test recommendations
                    - Performance → Optimization hints
```

Dit zorgt ervoor dat de analyse niet alleen problemen identificeert, maar direct bruikbare verbetervoorstellen genereert die in de migratieplanning worden opgenomen.

---

**Document Status**: Ready for Review
**Next Action**: Approval and Phase 1 Implementation Start
