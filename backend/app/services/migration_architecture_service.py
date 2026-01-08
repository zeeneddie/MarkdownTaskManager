"""
Migration Architecture Service - Felix Integration

Week 68 Day 3-4: Target architecture recommendations for legacy migrations
Felix agent specializes in system design, API design, and work breakdown.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from pathlib import Path
import re
import uuid
from datetime import datetime


# ==================== Enums ====================

class ArchitecturePattern(Enum):
    """Modern architecture patterns"""
    MONOLITH = "monolith"
    MODULAR_MONOLITH = "modular_monolith"
    MICROSERVICES = "microservices"
    EVENT_DRIVEN = "event_driven"
    SERVERLESS = "serverless"
    CQRS = "cqrs"
    HEXAGONAL = "hexagonal"
    CLEAN_ARCHITECTURE = "clean_architecture"


class ComponentLayer(Enum):
    """Application component layers"""
    PRESENTATION = "presentation"
    API_GATEWAY = "api_gateway"
    APPLICATION = "application"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    DATA_ACCESS = "data_access"
    INTEGRATION = "integration"
    CROSS_CUTTING = "cross_cutting"


class TechnologyChoice(Enum):
    """Modern technology choices"""
    # Backend
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_DJANGO = "python_django"
    DOTNET_MINIMAL = "dotnet_minimal_api"
    NODEJS_NESTJS = "nodejs_nestjs"
    JAVA_SPRING = "java_spring_boot"
    GO_GIN = "go_gin"
    RUST_ACTIX = "rust_actix"
    # Frontend
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    NEXTJS = "nextjs"
    BLAZOR = "blazor"
    # Database
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"
    # Infrastructure
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class MigrationStrategy(Enum):
    """Migration strategy patterns"""
    STRANGLER_FIG = "strangler_fig"
    BIG_BANG = "big_bang"
    PARALLEL_RUN = "parallel_run"
    INCREMENTAL = "incremental"
    PHASED = "phased"
    BLUE_GREEN = "blue_green"


class DesignPrinciple(Enum):
    """Key design principles to apply"""
    SOLID = "solid"
    DRY = "dry"
    KISS = "kiss"
    YAGNI = "yagni"
    SEPARATION_OF_CONCERNS = "separation_of_concerns"
    DEPENDENCY_INVERSION = "dependency_inversion"
    INTERFACE_SEGREGATION = "interface_segregation"


# ==================== Data Classes ====================

@dataclass
class LegacyComponent:
    """Detected component in legacy system"""
    name: str
    layer: ComponentLayer
    file_paths: List[str]
    dependencies: List[str]
    complexity: str  # low, medium, high
    business_logic_density: float  # 0.0 - 1.0
    data_access_patterns: List[str]
    external_integrations: List[str]


@dataclass
class TargetComponent:
    """Recommended target component"""
    name: str
    layer: ComponentLayer
    technology: TechnologyChoice
    description: str
    responsibilities: List[str]
    interfaces: List[str]
    dependencies: List[str]
    migration_priority: int  # 1-10
    estimated_effort_hours: float


@dataclass
class ArchitectureDecision:
    """Architecture Decision Record (ADR)"""
    id: str
    title: str
    context: str
    decision: str
    rationale: str
    consequences: List[str]
    alternatives_considered: List[str]
    status: str  # proposed, accepted, deprecated


@dataclass
class APIContract:
    """API contract specification"""
    endpoint: str
    method: str
    description: str
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    legacy_equivalent: Optional[str]
    breaking_changes: List[str]


@dataclass
class DataMigrationPlan:
    """Data migration strategy"""
    source_table: str
    target_table: str
    transformation_rules: List[str]
    validation_rules: List[str]
    estimated_row_count: int
    migration_order: int
    dependencies: List[str]


@dataclass
class FelixContext:
    """Context for Felix agent review"""
    summary: str
    key_decisions: List[str]
    risks: List[str]
    questions_for_review: List[str]
    recommended_patterns: List[str]
    technology_stack: Dict[str, str]


@dataclass
class ArchitectureRecommendation:
    """Complete architecture recommendation"""
    recommendation_id: str
    created_at: str
    source_analysis: Dict[str, Any]

    # Architecture decisions
    recommended_pattern: ArchitecturePattern
    migration_strategy: MigrationStrategy
    design_principles: List[DesignPrinciple]

    # Components
    legacy_components: List[LegacyComponent]
    target_components: List[TargetComponent]

    # Technical specifications
    api_contracts: List[APIContract]
    data_migration_plan: List[DataMigrationPlan]
    architecture_decisions: List[ArchitectureDecision]

    # Felix context
    felix_context: FelixContext

    # Metadata
    confidence_score: float
    total_effort_hours: float
    risks: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "created_at": self.created_at,
            "source_analysis": self.source_analysis,
            "architecture": {
                "pattern": self.recommended_pattern.value,
                "migration_strategy": self.migration_strategy.value,
                "design_principles": [p.value for p in self.design_principles]
            },
            "legacy_components": [
                {
                    "name": c.name,
                    "layer": c.layer.value,
                    "file_count": len(c.file_paths),
                    "complexity": c.complexity,
                    "dependencies": c.dependencies
                }
                for c in self.legacy_components
            ],
            "target_components": [
                {
                    "name": c.name,
                    "layer": c.layer.value,
                    "technology": c.technology.value,
                    "description": c.description,
                    "responsibilities": c.responsibilities,
                    "migration_priority": c.migration_priority,
                    "effort_hours": c.estimated_effort_hours
                }
                for c in self.target_components
            ],
            "api_contracts": [
                {
                    "endpoint": a.endpoint,
                    "method": a.method,
                    "description": a.description,
                    "legacy_equivalent": a.legacy_equivalent
                }
                for a in self.api_contracts
            ],
            "data_migration": [
                {
                    "source": d.source_table,
                    "target": d.target_table,
                    "order": d.migration_order,
                    "transformations": len(d.transformation_rules)
                }
                for d in self.data_migration_plan
            ],
            "architecture_decisions": [
                {
                    "id": d.id,
                    "title": d.title,
                    "decision": d.decision,
                    "status": d.status
                }
                for d in self.architecture_decisions
            ],
            "felix_context": {
                "summary": self.felix_context.summary,
                "key_decisions": self.felix_context.key_decisions,
                "risks": self.felix_context.risks,
                "questions_for_review": self.felix_context.questions_for_review,
                "recommended_patterns": self.felix_context.recommended_patterns,
                "technology_stack": self.felix_context.technology_stack
            },
            "metrics": {
                "confidence_score": self.confidence_score,
                "total_effort_hours": self.total_effort_hours,
                "component_count": len(self.target_components),
                "api_count": len(self.api_contracts),
                "table_count": len(self.data_migration_plan)
            },
            "risks": self.risks,
            "recommendations": self.recommendations
        }


# ==================== Pattern Detection ====================

LAYER_PATTERNS = {
    # Presentation layer patterns
    ComponentLayer.PRESENTATION: [
        (r'\.asp$', 'Classic ASP page'),
        (r'\.aspx$', 'WebForms page'),
        (r'\.cshtml$', 'Razor view'),
        (r'\.php$', 'PHP page'),
        (r'\.jsp$', 'JSP page'),
        (r'\.html$', 'HTML template'),
        (r'Default\.aspx', 'Entry point'),
        (r'Master\.aspx', 'Master page'),
        (r'_Layout', 'Layout template'),
    ],
    # Application layer patterns
    ComponentLayer.APPLICATION: [
        (r'Service\.cs$', '.NET service'),
        (r'Handler\.cs$', 'Command handler'),
        (r'Manager\.cs$', 'Business manager'),
        (r'Controller\.cs$', 'MVC controller'),
        (r'Facade\.cs$', 'Facade pattern'),
        (r'Orchestrator', 'Orchestrator'),
    ],
    # Domain layer patterns
    ComponentLayer.DOMAIN: [
        (r'Entity\.cs$', 'Domain entity'),
        (r'Model\.cs$', 'Domain model'),
        (r'Aggregate', 'DDD aggregate'),
        (r'ValueObject', 'Value object'),
        (r'DomainService', 'Domain service'),
        (r'Specification', 'Specification pattern'),
    ],
    # Data access patterns
    ComponentLayer.DATA_ACCESS: [
        (r'Repository\.cs$', 'Repository'),
        (r'DAL\.cs$', 'Data access layer'),
        (r'Context\.cs$', 'DbContext'),
        (r'Mapper\.cs$', 'Data mapper'),
        (r'\.sql$', 'SQL script'),
        (r'StoredProc', 'Stored procedure'),
    ],
    # Integration patterns
    ComponentLayer.INTEGRATION: [
        (r'Client\.cs$', 'External client'),
        (r'Gateway\.cs$', 'Gateway'),
        (r'Adapter\.cs$', 'Adapter'),
        (r'Connector', 'Connector'),
        (r'WebService', 'Web service'),
        (r'SOAP', 'SOAP service'),
    ],
    # Cross-cutting patterns
    ComponentLayer.CROSS_CUTTING: [
        (r'Logger', 'Logging'),
        (r'Cache', 'Caching'),
        (r'Auth', 'Authentication'),
        (r'Security', 'Security'),
        (r'Validation', 'Validation'),
        (r'Exception', 'Exception handling'),
    ],
}

# Target architecture templates
TARGET_TEMPLATES = {
    "small": {  # < 50 screens, < 20 tables
        "pattern": ArchitecturePattern.MODULAR_MONOLITH,
        "strategy": MigrationStrategy.INCREMENTAL,
        "layers": [
            ComponentLayer.PRESENTATION,
            ComponentLayer.APPLICATION,
            ComponentLayer.DOMAIN,
            ComponentLayer.DATA_ACCESS,
        ]
    },
    "medium": {  # 50-200 screens, 20-100 tables
        "pattern": ArchitecturePattern.CLEAN_ARCHITECTURE,
        "strategy": MigrationStrategy.STRANGLER_FIG,
        "layers": [
            ComponentLayer.API_GATEWAY,
            ComponentLayer.PRESENTATION,
            ComponentLayer.APPLICATION,
            ComponentLayer.DOMAIN,
            ComponentLayer.INFRASTRUCTURE,
            ComponentLayer.DATA_ACCESS,
            ComponentLayer.INTEGRATION,
        ]
    },
    "large": {  # > 200 screens, > 100 tables
        "pattern": ArchitecturePattern.MICROSERVICES,
        "strategy": MigrationStrategy.STRANGLER_FIG,
        "layers": [
            ComponentLayer.API_GATEWAY,
            ComponentLayer.PRESENTATION,
            ComponentLayer.APPLICATION,
            ComponentLayer.DOMAIN,
            ComponentLayer.INFRASTRUCTURE,
            ComponentLayer.DATA_ACCESS,
            ComponentLayer.INTEGRATION,
            ComponentLayer.CROSS_CUTTING,
        ]
    }
}


# ==================== Service Implementation ====================

class MigrationArchitectureService:
    """
    Felix integration for migration architecture recommendations.

    Analyzes legacy systems and generates:
    - Target architecture recommendations
    - Component mapping (legacy -> target)
    - API contract specifications
    - Data migration plans
    - Architecture Decision Records (ADRs)
    """

    def __init__(self):
        self.supported_patterns = list(ArchitecturePattern)
        self.supported_strategies = list(MigrationStrategy)

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "MigrationArchitectureService",
            "version": "1.0.0",
            "agent": "Felix",
            "capabilities": [
                "Architecture pattern recommendation",
                "Component mapping",
                "API contract generation",
                "Data migration planning",
                "ADR generation"
            ],
            "supported_patterns": [p.value for p in self.supported_patterns],
            "supported_strategies": [s.value for s in self.supported_strategies],
            "supported_technologies": [t.value for t in TechnologyChoice]
        }

    def analyze_directory(
        self,
        directory: str,
        target_technology: TechnologyChoice = TechnologyChoice.PYTHON_FASTAPI,
        preferred_pattern: Optional[ArchitecturePattern] = None
    ) -> ArchitectureRecommendation:
        """
        Analyze legacy directory and generate architecture recommendations.

        Args:
            directory: Path to source code
            target_technology: Preferred target technology stack
            preferred_pattern: Optional preferred architecture pattern

        Returns:
            Complete architecture recommendation
        """
        # Collect files
        files = self._collect_files(directory)

        # Detect legacy components
        legacy_components = self._detect_legacy_components(files)

        # Determine system size
        screen_count = sum(1 for c in legacy_components if c.layer == ComponentLayer.PRESENTATION)
        table_count = len([f for f in files if '.sql' in f.lower() or 'table' in f.lower()])

        size = "small" if screen_count < 50 else "medium" if screen_count < 200 else "large"
        template = TARGET_TEMPLATES[size]

        # Use preferred pattern or template default
        pattern = preferred_pattern or template["pattern"]
        strategy = template["strategy"]

        # Generate target components
        target_components = self._generate_target_components(
            legacy_components,
            target_technology,
            pattern,
            template["layers"]
        )

        # Generate API contracts
        api_contracts = self._generate_api_contracts(legacy_components, target_components)

        # Generate data migration plan
        data_migration = self._generate_data_migration_plan(files)

        # Generate ADRs
        adrs = self._generate_architecture_decisions(
            pattern,
            strategy,
            target_technology,
            legacy_components
        )

        # Calculate metrics
        total_effort = sum(c.estimated_effort_hours for c in target_components)
        confidence = self._calculate_confidence(legacy_components, files)

        # Generate Felix context
        felix_context = self._generate_felix_context(
            pattern,
            strategy,
            target_technology,
            legacy_components,
            target_components
        )

        # Generate risks and recommendations
        risks = self._identify_risks(legacy_components, pattern)
        recommendations = self._generate_recommendations(legacy_components, pattern, strategy)

        return ArchitectureRecommendation(
            recommendation_id=str(uuid.uuid4()),
            created_at=datetime.now().isoformat(),
            source_analysis={
                "directory": directory,
                "total_files": len(files),
                "screen_count": screen_count,
                "estimated_tables": table_count,
                "system_size": size
            },
            recommended_pattern=pattern,
            migration_strategy=strategy,
            design_principles=[
                DesignPrinciple.SOLID,
                DesignPrinciple.SEPARATION_OF_CONCERNS,
                DesignPrinciple.DEPENDENCY_INVERSION
            ],
            legacy_components=legacy_components,
            target_components=target_components,
            api_contracts=api_contracts,
            data_migration_plan=data_migration,
            architecture_decisions=adrs,
            felix_context=felix_context,
            confidence_score=confidence,
            total_effort_hours=total_effort,
            risks=risks,
            recommendations=recommendations
        )

    def _collect_files(self, directory: str) -> List[str]:
        """Collect all relevant files from directory"""
        files = []
        extensions = [
            '.asp', '.aspx', '.cs', '.vb', '.php', '.java', '.jsp',
            '.html', '.htm', '.sql', '.xml', '.config', '.json'
        ]

        path = Path(directory)
        if not path.exists():
            return []

        for ext in extensions:
            files.extend([str(f) for f in path.rglob(f'*{ext}')])

        return files[:500]  # Limit for performance

    def _detect_legacy_components(self, files: List[str]) -> List[LegacyComponent]:
        """Detect components in legacy system"""
        components = []
        layer_files: Dict[ComponentLayer, List[str]] = {layer: [] for layer in ComponentLayer}

        # Categorize files by layer
        for file_path in files:
            for layer, patterns in LAYER_PATTERNS.items():
                for pattern, description in patterns:
                    if re.search(pattern, file_path, re.IGNORECASE):
                        layer_files[layer].append(file_path)
                        break

        # Create components from grouped files
        for layer, layer_file_list in layer_files.items():
            if layer_file_list:
                # Group by directory
                dirs: Dict[str, List[str]] = {}
                for f in layer_file_list:
                    dir_name = str(Path(f).parent.name) or "root"
                    if dir_name not in dirs:
                        dirs[dir_name] = []
                    dirs[dir_name].append(f)

                for dir_name, dir_files in dirs.items():
                    complexity = "high" if len(dir_files) > 20 else "medium" if len(dir_files) > 5 else "low"

                    components.append(LegacyComponent(
                        name=f"{dir_name}_{layer.value}",
                        layer=layer,
                        file_paths=dir_files,
                        dependencies=[],  # Would need deeper analysis
                        complexity=complexity,
                        business_logic_density=0.5 if layer == ComponentLayer.APPLICATION else 0.3,
                        data_access_patterns=["direct_sql"] if layer == ComponentLayer.DATA_ACCESS else [],
                        external_integrations=[]
                    ))

        return components

    def _generate_target_components(
        self,
        legacy_components: List[LegacyComponent],
        target_tech: TechnologyChoice,
        pattern: ArchitecturePattern,
        layers: List[ComponentLayer]
    ) -> List[TargetComponent]:
        """Generate recommended target components"""
        target_components = []
        priority = 1

        # Map technology to specific implementations
        tech_specifics = self._get_tech_specifics(target_tech)

        for layer in layers:
            # Find legacy components for this layer
            legacy_for_layer = [c for c in legacy_components if c.layer == layer]

            if layer == ComponentLayer.API_GATEWAY:
                target_components.append(TargetComponent(
                    name="api_gateway",
                    layer=layer,
                    technology=target_tech,
                    description="Central API gateway for routing and authentication",
                    responsibilities=[
                        "Request routing",
                        "Authentication/Authorization",
                        "Rate limiting",
                        "Request/response transformation"
                    ],
                    interfaces=["REST API", "OpenAPI specification"],
                    dependencies=[],
                    migration_priority=priority,
                    estimated_effort_hours=40
                ))

            elif layer == ComponentLayer.PRESENTATION:
                target_components.append(TargetComponent(
                    name="frontend_app",
                    layer=layer,
                    technology=TechnologyChoice.REACT if target_tech != TechnologyChoice.BLAZOR else TechnologyChoice.BLAZOR,
                    description="Modern SPA frontend application",
                    responsibilities=[
                        "User interface rendering",
                        "State management",
                        "API communication",
                        "Form validation"
                    ],
                    interfaces=["REST API consumer", "WebSocket client"],
                    dependencies=["api_gateway"],
                    migration_priority=priority + 1,
                    estimated_effort_hours=len(legacy_for_layer) * 8
                ))

            elif layer == ComponentLayer.APPLICATION:
                target_components.append(TargetComponent(
                    name="application_services",
                    layer=layer,
                    technology=target_tech,
                    description=f"Application services using {tech_specifics['framework']}",
                    responsibilities=[
                        "Use case orchestration",
                        "Transaction management",
                        "DTO mapping",
                        "Business rule enforcement"
                    ],
                    interfaces=["Service interfaces", "Command/Query handlers"],
                    dependencies=["domain_layer"],
                    migration_priority=priority + 2,
                    estimated_effort_hours=len(legacy_for_layer) * 16
                ))

            elif layer == ComponentLayer.DOMAIN:
                target_components.append(TargetComponent(
                    name="domain_layer",
                    layer=layer,
                    technology=target_tech,
                    description="Domain model with business logic",
                    responsibilities=[
                        "Domain entities",
                        "Value objects",
                        "Domain services",
                        "Business rules"
                    ],
                    interfaces=["Repository interfaces", "Domain events"],
                    dependencies=[],
                    migration_priority=priority + 3,
                    estimated_effort_hours=len(legacy_for_layer) * 24
                ))

            elif layer == ComponentLayer.DATA_ACCESS:
                target_components.append(TargetComponent(
                    name="data_access_layer",
                    layer=layer,
                    technology=target_tech,
                    description=f"Data access using {tech_specifics['orm']}",
                    responsibilities=[
                        "Database operations",
                        "Query optimization",
                        "Connection management",
                        "Migration support"
                    ],
                    interfaces=["Repository implementations", "Unit of Work"],
                    dependencies=["domain_layer"],
                    migration_priority=priority + 4,
                    estimated_effort_hours=len(legacy_for_layer) * 12
                ))

            elif layer == ComponentLayer.INFRASTRUCTURE:
                target_components.append(TargetComponent(
                    name="infrastructure",
                    layer=layer,
                    technology=target_tech,
                    description="Infrastructure concerns (logging, caching, etc.)",
                    responsibilities=[
                        "Logging",
                        "Caching",
                        "Configuration",
                        "External service clients"
                    ],
                    interfaces=["Infrastructure interfaces"],
                    dependencies=[],
                    migration_priority=priority + 5,
                    estimated_effort_hours=32
                ))

            elif layer == ComponentLayer.INTEGRATION:
                target_components.append(TargetComponent(
                    name="integration_layer",
                    layer=layer,
                    technology=target_tech,
                    description="External system integrations",
                    responsibilities=[
                        "External API clients",
                        "Message queue consumers",
                        "Event publishers",
                        "Data synchronization"
                    ],
                    interfaces=["Integration contracts", "Event schemas"],
                    dependencies=["application_services"],
                    migration_priority=priority + 6,
                    estimated_effort_hours=len(legacy_for_layer) * 20
                ))

            elif layer == ComponentLayer.CROSS_CUTTING:
                target_components.append(TargetComponent(
                    name="cross_cutting",
                    layer=layer,
                    technology=target_tech,
                    description="Cross-cutting concerns",
                    responsibilities=[
                        "Authentication middleware",
                        "Exception handling",
                        "Validation",
                        "Audit logging"
                    ],
                    interfaces=["Middleware interfaces", "Aspect definitions"],
                    dependencies=[],
                    migration_priority=priority + 7,
                    estimated_effort_hours=24
                ))

            priority += 1

        return target_components

    def _get_tech_specifics(self, tech: TechnologyChoice) -> Dict[str, str]:
        """Get technology-specific implementation details"""
        specs = {
            TechnologyChoice.PYTHON_FASTAPI: {
                "framework": "FastAPI",
                "orm": "SQLAlchemy",
                "testing": "pytest",
                "package_manager": "pip/poetry"
            },
            TechnologyChoice.PYTHON_DJANGO: {
                "framework": "Django",
                "orm": "Django ORM",
                "testing": "pytest-django",
                "package_manager": "pip/poetry"
            },
            TechnologyChoice.DOTNET_MINIMAL: {
                "framework": ".NET Minimal API",
                "orm": "Entity Framework Core",
                "testing": "xUnit",
                "package_manager": "NuGet"
            },
            TechnologyChoice.NODEJS_NESTJS: {
                "framework": "NestJS",
                "orm": "TypeORM/Prisma",
                "testing": "Jest",
                "package_manager": "npm/yarn"
            },
            TechnologyChoice.JAVA_SPRING: {
                "framework": "Spring Boot",
                "orm": "Spring Data JPA",
                "testing": "JUnit",
                "package_manager": "Maven/Gradle"
            },
            TechnologyChoice.GO_GIN: {
                "framework": "Gin",
                "orm": "GORM",
                "testing": "go test",
                "package_manager": "go modules"
            },
            TechnologyChoice.RUST_ACTIX: {
                "framework": "Actix-web",
                "orm": "Diesel/SQLx",
                "testing": "cargo test",
                "package_manager": "cargo"
            }
        }
        return specs.get(tech, specs[TechnologyChoice.PYTHON_FASTAPI])

    def _generate_api_contracts(
        self,
        legacy_components: List[LegacyComponent],
        target_components: List[TargetComponent]
    ) -> List[APIContract]:
        """Generate API contract specifications"""
        contracts = []

        # Generate CRUD endpoints for each presentation component
        for legacy in legacy_components:
            if legacy.layer == ComponentLayer.PRESENTATION:
                entity_name = legacy.name.replace("_presentation", "").lower()

                # GET collection
                contracts.append(APIContract(
                    endpoint=f"/api/{entity_name}s",
                    method="GET",
                    description=f"List all {entity_name} resources",
                    request_schema={"query": {"page": "int", "limit": "int"}},
                    response_schema={"items": "array", "total": "int"},
                    legacy_equivalent=f"{legacy.name} list view",
                    breaking_changes=[]
                ))

                # GET single
                contracts.append(APIContract(
                    endpoint=f"/api/{entity_name}s/{{id}}",
                    method="GET",
                    description=f"Get single {entity_name} by ID",
                    request_schema={},
                    response_schema={"id": "string", "data": "object"},
                    legacy_equivalent=f"{legacy.name} detail view",
                    breaking_changes=[]
                ))

                # POST create
                contracts.append(APIContract(
                    endpoint=f"/api/{entity_name}s",
                    method="POST",
                    description=f"Create new {entity_name}",
                    request_schema={"body": {"required": [], "optional": []}},
                    response_schema={"id": "string", "created": "boolean"},
                    legacy_equivalent=f"{legacy.name} create form",
                    breaking_changes=[]
                ))

                # PUT update
                contracts.append(APIContract(
                    endpoint=f"/api/{entity_name}s/{{id}}",
                    method="PUT",
                    description=f"Update {entity_name} by ID",
                    request_schema={"body": {"required": [], "optional": []}},
                    response_schema={"id": "string", "updated": "boolean"},
                    legacy_equivalent=f"{legacy.name} edit form",
                    breaking_changes=[]
                ))

                # DELETE
                contracts.append(APIContract(
                    endpoint=f"/api/{entity_name}s/{{id}}",
                    method="DELETE",
                    description=f"Delete {entity_name} by ID",
                    request_schema={},
                    response_schema={"deleted": "boolean"},
                    legacy_equivalent=f"{legacy.name} delete action",
                    breaking_changes=[]
                ))

        return contracts[:50]  # Limit for readability

    def _generate_data_migration_plan(self, files: List[str]) -> List[DataMigrationPlan]:
        """Generate data migration plan from detected SQL files"""
        migrations = []
        order = 1

        # Detect table names from SQL files
        table_patterns = [
            r'CREATE TABLE\s+(\w+)',
            r'FROM\s+(\w+)',
            r'INTO\s+(\w+)',
            r'UPDATE\s+(\w+)'
        ]

        tables: Set[str] = set()
        for file_path in files:
            if '.sql' in file_path.lower():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in table_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            tables.update(matches)
                except:
                    pass

        # Generate migration plan for each table
        for table in sorted(tables)[:30]:  # Limit
            migrations.append(DataMigrationPlan(
                source_table=table,
                target_table=self._snake_case(table),
                transformation_rules=[
                    "Convert column names to snake_case",
                    "Add audit columns (created_at, updated_at)",
                    "Convert datetime formats",
                    "Apply data validation rules"
                ],
                validation_rules=[
                    "Verify row counts match",
                    "Validate foreign key integrity",
                    "Check data type conversions"
                ],
                estimated_row_count=10000,  # Placeholder
                migration_order=order,
                dependencies=[]
            ))
            order += 1

        return migrations

    def _snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _generate_architecture_decisions(
        self,
        pattern: ArchitecturePattern,
        strategy: MigrationStrategy,
        technology: TechnologyChoice,
        legacy_components: List[LegacyComponent]
    ) -> List[ArchitectureDecision]:
        """Generate Architecture Decision Records"""
        adrs = []

        # ADR 001: Architecture Pattern
        adrs.append(ArchitectureDecision(
            id="ADR-001",
            title="Architecture Pattern Selection",
            context=f"Legacy system has {len(legacy_components)} components that need modernization",
            decision=f"Adopt {pattern.value} architecture pattern",
            rationale=self._get_pattern_rationale(pattern, len(legacy_components)),
            consequences=[
                f"Clear separation of concerns with {pattern.value}",
                "Improved testability through dependency injection",
                "Easier maintenance and scaling"
            ],
            alternatives_considered=[
                p.value for p in ArchitecturePattern if p != pattern
            ][:3],
            status="proposed"
        ))

        # ADR 002: Migration Strategy
        adrs.append(ArchitectureDecision(
            id="ADR-002",
            title="Migration Strategy",
            context="Need to migrate legacy system with minimal business disruption",
            decision=f"Use {strategy.value} migration strategy",
            rationale=self._get_strategy_rationale(strategy),
            consequences=[
                "Gradual migration reduces risk",
                "Both systems run in parallel during transition",
                "Rollback capability if issues arise"
            ],
            alternatives_considered=[
                s.value for s in MigrationStrategy if s != strategy
            ][:3],
            status="proposed"
        ))

        # ADR 003: Technology Stack
        adrs.append(ArchitectureDecision(
            id="ADR-003",
            title="Target Technology Stack",
            context="Selection of modern technology stack for target system",
            decision=f"Use {technology.value} as primary backend technology",
            rationale=self._get_tech_specifics(technology)["framework"] + " provides modern development experience",
            consequences=[
                "Modern async/await patterns",
                "Strong typing and IDE support",
                "Active community and ecosystem"
            ],
            alternatives_considered=[
                t.value for t in TechnologyChoice if t != technology
            ][:3],
            status="proposed"
        ))

        # ADR 004: Database Strategy
        adrs.append(ArchitectureDecision(
            id="ADR-004",
            title="Database Strategy",
            context="Need to decide on database technology and migration approach",
            decision="Use PostgreSQL with code-first migrations",
            rationale="PostgreSQL offers robust features, excellent performance, and open-source licensing",
            consequences=[
                "Schema changes tracked in version control",
                "Database migrations are repeatable",
                "Support for complex queries and JSON data"
            ],
            alternatives_considered=["MySQL", "MongoDB", "SQL Server"],
            status="proposed"
        ))

        return adrs

    def _get_pattern_rationale(self, pattern: ArchitecturePattern, component_count: int) -> str:
        """Get rationale for architecture pattern"""
        rationales = {
            ArchitecturePattern.MONOLITH: "Simple deployment for small systems",
            ArchitecturePattern.MODULAR_MONOLITH: "Balance between simplicity and modularity",
            ArchitecturePattern.MICROSERVICES: f"Component count ({component_count}) justifies service separation",
            ArchitecturePattern.CLEAN_ARCHITECTURE: "Clear boundaries between business and infrastructure",
            ArchitecturePattern.HEXAGONAL: "Ports and adapters isolate business logic",
            ArchitecturePattern.EVENT_DRIVEN: "Loose coupling through async events",
            ArchitecturePattern.SERVERLESS: "Cost-effective for variable workloads",
            ArchitecturePattern.CQRS: "Separate read/write models for complex domains"
        }
        return rationales.get(pattern, "Standard industry practice")

    def _get_strategy_rationale(self, strategy: MigrationStrategy) -> str:
        """Get rationale for migration strategy"""
        rationales = {
            MigrationStrategy.STRANGLER_FIG: "Gradually replace legacy with new system",
            MigrationStrategy.BIG_BANG: "Complete replacement at single cutover point",
            MigrationStrategy.PARALLEL_RUN: "Run both systems simultaneously for validation",
            MigrationStrategy.INCREMENTAL: "Migrate feature by feature",
            MigrationStrategy.PHASED: "Migrate in planned phases",
            MigrationStrategy.BLUE_GREEN: "Zero-downtime deployment with instant rollback"
        }
        return rationales.get(strategy, "Industry best practice")

    def _generate_felix_context(
        self,
        pattern: ArchitecturePattern,
        strategy: MigrationStrategy,
        technology: TechnologyChoice,
        legacy_components: List[LegacyComponent],
        target_components: List[TargetComponent]
    ) -> FelixContext:
        """Generate context for Felix agent review"""
        tech_specs = self._get_tech_specifics(technology)

        return FelixContext(
            summary=f"Migration to {pattern.value} using {strategy.value} strategy with {technology.value}",
            key_decisions=[
                f"Architecture: {pattern.value}",
                f"Migration: {strategy.value}",
                f"Technology: {tech_specs['framework']}",
                f"ORM: {tech_specs['orm']}",
                f"Testing: {tech_specs['testing']}"
            ],
            risks=[
                "Data integrity during migration",
                "Business continuity during transition",
                "Knowledge transfer from legacy system",
                "Performance parity with legacy"
            ],
            questions_for_review=[
                "Is the architecture pattern appropriate for this scale?",
                "Are there missing components in the target architecture?",
                "Is the migration order optimal?",
                "What integration points need special attention?",
                "Are there undocumented business rules in legacy code?"
            ],
            recommended_patterns=[
                "Repository Pattern for data access",
                "CQRS for complex queries",
                "Event sourcing for audit trails",
                "Circuit breaker for external integrations"
            ],
            technology_stack={
                "backend": technology.value,
                "framework": tech_specs['framework'],
                "orm": tech_specs['orm'],
                "testing": tech_specs['testing'],
                "frontend": "React/TypeScript",
                "database": "PostgreSQL",
                "cache": "Redis",
                "messaging": "RabbitMQ/Kafka"
            }
        )

    def _calculate_confidence(
        self,
        legacy_components: List[LegacyComponent],
        files: List[str]
    ) -> float:
        """Calculate confidence score for recommendations"""
        # Base confidence
        confidence = 0.5

        # More files = more confidence (up to 0.2)
        file_factor = min(len(files) / 100, 1.0) * 0.2
        confidence += file_factor

        # More component diversity = more confidence (up to 0.2)
        layers = set(c.layer for c in legacy_components)
        layer_factor = len(layers) / len(ComponentLayer) * 0.2
        confidence += layer_factor

        # Known patterns = more confidence (up to 0.1)
        known_patterns = sum(1 for c in legacy_components if c.complexity != "high")
        pattern_factor = known_patterns / max(len(legacy_components), 1) * 0.1
        confidence += pattern_factor

        return min(confidence, 1.0)

    def _identify_risks(
        self,
        legacy_components: List[LegacyComponent],
        pattern: ArchitecturePattern
    ) -> List[str]:
        """Identify migration risks"""
        risks = []

        # High complexity components
        high_complexity = [c for c in legacy_components if c.complexity == "high"]
        if high_complexity:
            risks.append(f"{len(high_complexity)} high-complexity components require extra attention")

        # Data access patterns
        direct_sql = any("direct_sql" in c.data_access_patterns for c in legacy_components)
        if direct_sql:
            risks.append("Direct SQL access needs ORM migration")

        # Pattern-specific risks
        if pattern == ArchitecturePattern.MICROSERVICES:
            risks.append("Distributed system complexity requires operational maturity")
            risks.append("Service boundaries may need refinement during migration")

        # Integration risks
        integration_components = [c for c in legacy_components if c.layer == ComponentLayer.INTEGRATION]
        if integration_components:
            risks.append(f"{len(integration_components)} integration points need contract testing")

        # General risks
        risks.extend([
            "Hidden business rules in legacy code",
            "Undocumented dependencies",
            "Data format inconsistencies",
            "Performance regression"
        ])

        return risks

    def _generate_recommendations(
        self,
        legacy_components: List[LegacyComponent],
        pattern: ArchitecturePattern,
        strategy: MigrationStrategy
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        # Strategy-based recommendations
        if strategy == MigrationStrategy.STRANGLER_FIG:
            recommendations.append("Start with low-risk, self-contained modules")
            recommendations.append("Implement anti-corruption layer between old and new")

        if strategy == MigrationStrategy.PARALLEL_RUN:
            recommendations.append("Set up data synchronization between systems")
            recommendations.append("Implement comprehensive comparison testing")

        # Pattern-based recommendations
        if pattern == ArchitecturePattern.CLEAN_ARCHITECTURE:
            recommendations.append("Define clear dependency rules between layers")
            recommendations.append("Use interfaces for all cross-layer dependencies")

        if pattern == ArchitecturePattern.MICROSERVICES:
            recommendations.append("Start with API gateway and authentication service")
            recommendations.append("Implement centralized logging and tracing")

        # Component-based recommendations
        data_access = [c for c in legacy_components if c.layer == ComponentLayer.DATA_ACCESS]
        if data_access:
            recommendations.append("Create database migration scripts early")
            recommendations.append("Implement data validation at migration boundaries")

        # General recommendations
        recommendations.extend([
            "Establish automated testing pipeline before migration",
            "Document all legacy business rules",
            "Create rollback procedures for each phase",
            "Train team on target technology stack"
        ])

        return recommendations[:10]

    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get all available architecture patterns"""
        return [
            {
                "id": p.value,
                "name": p.name.replace("_", " ").title(),
                "description": self._get_pattern_rationale(p, 50),
                "suitable_for": self._get_pattern_suitability(p)
            }
            for p in ArchitecturePattern
        ]

    def _get_pattern_suitability(self, pattern: ArchitecturePattern) -> str:
        """Get suitability description for pattern"""
        suitability = {
            ArchitecturePattern.MONOLITH: "Small teams, simple domains, quick delivery",
            ArchitecturePattern.MODULAR_MONOLITH: "Medium complexity, growing teams",
            ArchitecturePattern.MICROSERVICES: "Large teams, complex domains, scalability needs",
            ArchitecturePattern.CLEAN_ARCHITECTURE: "Long-term maintainability, testability focus",
            ArchitecturePattern.HEXAGONAL: "Multiple interfaces, integration-heavy systems",
            ArchitecturePattern.EVENT_DRIVEN: "Async workflows, eventual consistency acceptable",
            ArchitecturePattern.SERVERLESS: "Variable loads, event-triggered processing",
            ArchitecturePattern.CQRS: "Complex queries, high read/write ratio difference"
        }
        return suitability.get(pattern, "General purpose")

    def get_strategies(self) -> List[Dict[str, Any]]:
        """Get all available migration strategies"""
        return [
            {
                "id": s.value,
                "name": s.name.replace("_", " ").title(),
                "description": self._get_strategy_rationale(s),
                "risk_level": self._get_strategy_risk(s)
            }
            for s in MigrationStrategy
        ]

    def _get_strategy_risk(self, strategy: MigrationStrategy) -> str:
        """Get risk level for strategy"""
        risk_levels = {
            MigrationStrategy.STRANGLER_FIG: "Low",
            MigrationStrategy.BIG_BANG: "High",
            MigrationStrategy.PARALLEL_RUN: "Medium",
            MigrationStrategy.INCREMENTAL: "Low",
            MigrationStrategy.PHASED: "Medium",
            MigrationStrategy.BLUE_GREEN: "Low"
        }
        return risk_levels.get(strategy, "Medium")
