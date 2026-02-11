"""
Migration Estimation Service - Eliza Integration for IFPUG Migration Costing

Week 68 Day 2-3: Integration of Eliza (Estimation Engine) with MigrationAnalyzer
for comprehensive effort estimation using IFPUG Function Point methodology.

Provides:
- Function Point calculation for legacy components
- Migration complexity multipliers
- Effort estimation by migration phase
- Risk-adjusted estimates
- Historical comparison capabilities
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime
from collections import defaultdict
import math


class MigrationPhase(Enum):
    """Migration project phases"""
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DATA_MIGRATION = "data_migration"
    DEPLOYMENT = "deployment"
    PARALLEL_RUN = "parallel_run"
    CUTOVER = "cutover"


class ComponentType(Enum):
    """IFPUG Function Point component types"""
    EI = "External Input"          # Data entry, transactions
    EO = "External Output"         # Reports, screens, messages
    EQ = "External Inquiry"        # Search, lookup, retrieval
    ILF = "Internal Logical File"  # Main data entities
    EIF = "External Interface File"  # External data accessed


class ComplexityLevel(Enum):
    """IFPUG complexity weights"""
    LOW = "low"
    AVERAGE = "average"
    HIGH = "high"


class TechnologyStack(Enum):
    """Technology stacks for migration"""
    CLASSIC_ASP = "classic_asp"
    VB_NET_WEBFORMS = "vb_net_webforms"
    CSHARP_WEBFORMS = "csharp_webforms"
    PHP_LEGACY = "php_legacy"
    JAVA_LEGACY = "java_legacy"
    COBOL = "cobol"
    ORACLE_FORMS = "oracle_forms"
    POWERBUILDER = "powerbuilder"
    PYTHON_WEB = "python_web"  # Flask, Django, FastAPI, etc.


@dataclass
class FunctionPointComponent:
    """Single function point component"""
    name: str
    component_type: ComponentType
    complexity: ComplexityLevel
    det_count: int  # Data Element Types
    ret_count: int  # Record Element Types / File Types Referenced
    unadjusted_fp: float
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    notes: str = ""


@dataclass
class MigrationFactor:
    """Factor affecting migration effort"""
    name: str
    category: str  # "technical", "process", "risk"
    value: float  # Multiplier (1.0 = neutral)
    description: str
    source: str  # Where this factor was detected


@dataclass
class PhaseEstimate:
    """Effort estimate for a migration phase"""
    phase: MigrationPhase
    base_hours: float
    adjusted_hours: float
    fp_basis: float  # Function points driving this phase
    multiplier: float
    risk_buffer_hours: float
    total_hours: float
    activities: List[str]


@dataclass
class MigrationEstimationResult:
    """Complete migration estimation result"""
    project_path: str
    source_stack: TechnologyStack
    target_stack: str
    total_unadjusted_fp: float
    value_adjustment_factor: float
    total_adjusted_fp: float
    components: List[FunctionPointComponent]
    migration_factors: List[MigrationFactor]
    phase_estimates: List[PhaseEstimate]
    total_effort_hours: float
    total_effort_person_days: float
    confidence_level: float  # 0.0 - 1.0
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    estimation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "source_stack": self.source_stack.value,
            "target_stack": self.target_stack,
            "function_points": {
                "unadjusted": round(self.total_unadjusted_fp, 1),
                "vaf": round(self.value_adjustment_factor, 2),
                "adjusted": round(self.total_adjusted_fp, 1)
            },
            "components": {
                "total": len(self.components),
                "by_type": self._group_by_type(),
                "details": [
                    {
                        "name": c.name,
                        "type": c.component_type.value,
                        "complexity": c.complexity.value,
                        "fp": c.unadjusted_fp,
                        "file": c.file_path
                    }
                    for c in self.components[:50]  # Limit for response size
                ]
            },
            "migration_factors": [
                {
                    "name": f.name,
                    "category": f.category,
                    "value": f.value,
                    "description": f.description
                }
                for f in self.migration_factors
            ],
            "phase_estimates": [
                {
                    "phase": p.phase.value,
                    "base_hours": round(p.base_hours, 1),
                    "adjusted_hours": round(p.adjusted_hours, 1),
                    "risk_buffer": round(p.risk_buffer_hours, 1),
                    "total_hours": round(p.total_hours, 1),
                    "activities": p.activities
                }
                for p in self.phase_estimates
            ],
            "total_effort": {
                "hours": round(self.total_effort_hours, 1),
                "person_days": round(self.total_effort_person_days, 1),
                "person_months": round(self.total_effort_person_days / 20, 1)
            },
            "confidence_level": round(self.confidence_level, 2),
            "risk_assessment": self.risk_assessment,
            "recommendations": self.recommendations,
            "estimation_timestamp": self.estimation_timestamp
        }

    def _group_by_type(self) -> Dict[str, int]:
        """Group components by type"""
        counts = defaultdict(int)
        for c in self.components:
            counts[c.component_type.value] += 1
        return dict(counts)


# IFPUG Complexity Weights (standard weights)
IFPUG_WEIGHTS: Dict[ComponentType, Dict[ComplexityLevel, int]] = {
    ComponentType.EI: {ComplexityLevel.LOW: 3, ComplexityLevel.AVERAGE: 4, ComplexityLevel.HIGH: 6},
    ComponentType.EO: {ComplexityLevel.LOW: 4, ComplexityLevel.AVERAGE: 5, ComplexityLevel.HIGH: 7},
    ComponentType.EQ: {ComplexityLevel.LOW: 3, ComplexityLevel.AVERAGE: 4, ComplexityLevel.HIGH: 6},
    ComponentType.ILF: {ComplexityLevel.LOW: 7, ComplexityLevel.AVERAGE: 10, ComplexityLevel.HIGH: 15},
    ComponentType.EIF: {ComplexityLevel.LOW: 5, ComplexityLevel.AVERAGE: 7, ComplexityLevel.HIGH: 10},
}

# Migration complexity multipliers by source stack
STACK_COMPLEXITY_MULTIPLIERS: Dict[TechnologyStack, float] = {
    TechnologyStack.CLASSIC_ASP: 1.8,      # High complexity, no structure
    TechnologyStack.VB_NET_WEBFORMS: 1.4,  # Moderate, event-driven
    TechnologyStack.CSHARP_WEBFORMS: 1.3,  # Moderate
    TechnologyStack.PHP_LEGACY: 1.5,       # Variable quality
    TechnologyStack.JAVA_LEGACY: 1.2,      # Generally structured
    TechnologyStack.COBOL: 2.0,            # Very different paradigm
    TechnologyStack.ORACLE_FORMS: 1.7,     # Proprietary
    TechnologyStack.POWERBUILDER: 1.6,     # Proprietary DataWindow
    TechnologyStack.PYTHON_WEB: 1.2,       # Well-structured, modern
}

# Hours per function point by phase (industry average)
HOURS_PER_FP_BY_PHASE: Dict[MigrationPhase, float] = {
    MigrationPhase.DISCOVERY: 0.5,
    MigrationPhase.ANALYSIS: 1.0,
    MigrationPhase.PLANNING: 0.3,
    MigrationPhase.DESIGN: 1.5,
    MigrationPhase.DEVELOPMENT: 4.0,
    MigrationPhase.TESTING: 2.5,
    MigrationPhase.DATA_MIGRATION: 1.5,
    MigrationPhase.DEPLOYMENT: 0.5,
    MigrationPhase.PARALLEL_RUN: 0.5,
    MigrationPhase.CUTOVER: 0.2,
}

# Risk buffer percentages by confidence
RISK_BUFFER_BY_CONFIDENCE: Dict[str, float] = {
    "high": 0.10,    # 10% buffer
    "medium": 0.25,  # 25% buffer
    "low": 0.50,     # 50% buffer
}

# Pattern matchers for component detection
COMPONENT_PATTERNS: Dict[TechnologyStack, Dict[ComponentType, List[Tuple[str, str]]]] = {
    TechnologyStack.CLASSIC_ASP: {
        ComponentType.EI: [
            (r"Request\.Form\s*\(", "Form input processing"),
            (r"<form.*method.*post", "POST form"),
            (r"INSERT\s+INTO", "Database insert"),
            (r"UPDATE\s+.*SET", "Database update"),
        ],
        ComponentType.EO: [
            (r"Response\.Write", "Output generation"),
            (r"<%=.*%>", "Inline output"),
            (r"SELECT.*FROM.*ORDER\s+BY", "Sorted report"),
        ],
        ComponentType.EQ: [
            (r"SELECT.*WHERE.*=.*Request", "Query with parameter"),
            (r"Recordset\.Open", "Data retrieval"),
        ],
        ComponentType.ILF: [
            (r"CREATE\s+TABLE", "Table definition"),
            (r"ALTER\s+TABLE", "Table modification"),
        ],
        ComponentType.EIF: [
            (r"XMLHTTP", "External HTTP call"),
            (r"ServerXMLHTTP", "External API"),
        ],
    },
    TechnologyStack.VB_NET_WEBFORMS: {
        ComponentType.EI: [
            (r"Protected\s+Sub\s+\w+_Click", "Button click handler"),
            (r"\.Insert\(", "Data insert"),
            (r"\.Update\(", "Data update"),
            (r"GridView.*DataSource", "Grid data binding"),
        ],
        ComponentType.EO: [
            (r"\.DataBind\(\)", "Data output binding"),
            (r"ReportViewer", "Report generation"),
            (r"Response\.Write", "Direct output"),
        ],
        ComponentType.EQ: [
            (r"\.Select\(", "Data query"),
            (r"DataReader", "Data retrieval"),
            (r"SqlCommand.*SELECT", "SQL query"),
        ],
        ComponentType.ILF: [
            (r"Public\s+Class\s+\w+\s*\n.*Property", "Entity class"),
            (r"DataSet", "Data structure"),
        ],
        ComponentType.EIF: [
            (r"WebClient", "External web call"),
            (r"WebRequest", "External HTTP"),
            (r"WebService", "External service"),
        ],
    },
    TechnologyStack.PHP_LEGACY: {
        ComponentType.EI: [
            (r"\$_POST\s*\[", "POST input"),
            (r"mysql_query.*INSERT", "Database insert"),
            (r"mysql_query.*UPDATE", "Database update"),
        ],
        ComponentType.EO: [
            (r"echo\s+", "Output statement"),
            (r"print\s+", "Print statement"),
            (r"fwrite\s*\(", "File output"),
        ],
        ComponentType.EQ: [
            (r"mysql_query.*SELECT", "Database query"),
            (r"mysql_fetch", "Result retrieval"),
        ],
        ComponentType.ILF: [
            (r"CREATE\s+TABLE", "Table definition"),
            (r"class\s+\w+\s*{", "Class definition"),
        ],
        ComponentType.EIF: [
            (r"file_get_contents\s*\(\s*['\"]http", "External HTTP"),
            (r"curl_exec", "External curl call"),
        ],
    },
    TechnologyStack.JAVA_LEGACY: {
        ComponentType.EI: [
            (r"doPost\s*\(", "POST handler"),
            (r"PreparedStatement.*INSERT", "Database insert"),
            (r"PreparedStatement.*UPDATE", "Database update"),
        ],
        ComponentType.EO: [
            (r"PrintWriter.*print", "Output generation"),
            (r"response\.getWriter", "Response output"),
            (r"JasperReport", "Report generation"),
        ],
        ComponentType.EQ: [
            (r"PreparedStatement.*SELECT", "Database query"),
            (r"ResultSet", "Result processing"),
        ],
        ComponentType.ILF: [
            (r"@Entity", "JPA Entity"),
            (r"public\s+class\s+\w+DAO", "Data access"),
        ],
        ComponentType.EIF: [
            (r"HttpURLConnection", "External HTTP"),
            (r"WebService", "External service"),
        ],
    },
    TechnologyStack.PYTHON_WEB: {
        ComponentType.EI: [
            (r"@app\.route.*methods.*POST", "Flask POST endpoint"),
            (r"@router\.post\s*\(", "FastAPI POST endpoint"),
            (r"request\.form", "Flask form input"),
            (r"request\.json|request\.get_json", "Flask JSON input"),
            (r"def\s+post\s*\(\s*self\s*,\s*request", "Django CBV POST"),
            (r"db\.session\.add\s*\(", "SQLAlchemy insert"),
            (r"\.save\s*\(\s*\)", "Django ORM save"),
            (r"\.create\s*\(", "ORM create"),
            (r"INSERT\s+INTO", "Raw SQL insert"),
        ],
        ComponentType.EO: [
            (r"return\s+jsonify\s*\(", "Flask JSON response"),
            (r"return\s+JsonResponse\s*\(", "Django JSON response"),
            (r"render_template\s*\(", "Flask template rendering"),
            (r"render\s*\(\s*request\s*,", "Django template rendering"),
            (r"StreamingResponse\s*\(", "FastAPI streaming response"),
            (r"FileResponse\s*\(", "FastAPI file response"),
            (r"SELECT.*ORDER\s+BY", "Sorted report query"),
        ],
        ComponentType.EQ: [
            (r"@app\.route.*methods.*GET", "Flask GET endpoint"),
            (r"@router\.get\s*\(", "FastAPI GET endpoint"),
            (r"\.query\.filter", "SQLAlchemy query filter"),
            (r"\.objects\.filter\s*\(", "Django ORM filter"),
            (r"\.objects\.get\s*\(", "Django ORM get"),
            (r"SELECT.*WHERE", "Parameterized SQL query"),
            (r"def\s+get\s*\(\s*self\s*,\s*request", "Django CBV GET"),
        ],
        ComponentType.ILF: [
            (r"class\s+\w+\s*\(\s*db\.Model\s*\)", "SQLAlchemy model"),
            (r"class\s+\w+\s*\(\s*models\.Model\s*\)", "Django model"),
            (r"class\s+\w+\s*\(\s*Base\s*\)", "SQLAlchemy declarative model"),
            (r"class\s+\w+\s*\(\s*BaseModel\s*\)", "Pydantic model"),
            (r"CREATE\s+TABLE", "SQL table definition"),
        ],
        ComponentType.EIF: [
            (r"requests\.get\s*\(", "External HTTP GET"),
            (r"requests\.post\s*\(", "External HTTP POST"),
            (r"httpx\.", "Async HTTP client"),
            (r"aiohttp\.ClientSession", "Async HTTP session"),
            (r"urlopen\s*\(", "Stdlib HTTP call"),
            (r"urllib\.request", "Stdlib urllib"),
        ],
    },
}

# Value Adjustment Factor (VAF) characteristics
VAF_CHARACTERISTICS = [
    "data_communications",
    "distributed_data",
    "performance",
    "heavily_used_configuration",
    "transaction_rate",
    "online_data_entry",
    "end_user_efficiency",
    "online_update",
    "complex_processing",
    "reusability",
    "installation_ease",
    "operational_ease",
    "multiple_sites",
    "facilitate_change",
]


class MigrationEstimationService:
    """Service for IFPUG-based migration effort estimation"""

    def __init__(self):
        self.component_patterns = COMPONENT_PATTERNS

    def analyze_directory(
        self,
        directory: str,
        source_stack: TechnologyStack,
        target_stack: str = "modern_web",
        include_risk_buffer: bool = True
    ) -> MigrationEstimationResult:
        """
        Analyze directory and estimate migration effort

        Args:
            directory: Path to source code directory
            source_stack: Source technology stack
            target_stack: Target technology (e.g., "ASP.NET Core", "Node.js")
            include_risk_buffer: Include risk-adjusted buffer in estimates

        Returns:
            MigrationEstimationResult with complete effort breakdown
        """
        path = Path(directory)
        if not path.exists():
            return self._empty_result(directory, source_stack, target_stack,
                                      "Directory does not exist")

        # Collect source files
        files = self._collect_files(path, source_stack)

        if not files:
            return self._empty_result(directory, source_stack, target_stack,
                                      "No source files found")

        # Detect function point components
        components = self._detect_components(files, source_stack)

        # Calculate unadjusted function points
        total_ufp = sum(c.unadjusted_fp for c in components)

        # Calculate Value Adjustment Factor
        vaf = self._calculate_vaf(components, source_stack)

        # Calculate adjusted function points
        total_afp = total_ufp * vaf

        # Identify migration factors
        migration_factors = self._identify_migration_factors(
            files, source_stack, components
        )

        # Calculate overall complexity multiplier
        complexity_multiplier = self._calculate_complexity_multiplier(
            source_stack, migration_factors
        )

        # Estimate effort by phase
        phase_estimates = self._estimate_phases(
            total_afp, complexity_multiplier, include_risk_buffer
        )

        # Calculate totals
        total_hours = sum(p.total_hours for p in phase_estimates)
        total_days = total_hours / 8  # 8-hour workday

        # Calculate confidence level
        confidence = self._calculate_confidence(components, files)

        # Risk assessment
        risk_assessment = self._assess_risks(
            components, migration_factors, source_stack
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            source_stack, target_stack, components, migration_factors, risk_assessment
        )

        return MigrationEstimationResult(
            project_path=str(directory),
            source_stack=source_stack,
            target_stack=target_stack,
            total_unadjusted_fp=total_ufp,
            value_adjustment_factor=vaf,
            total_adjusted_fp=total_afp,
            components=components,
            migration_factors=migration_factors,
            phase_estimates=phase_estimates,
            total_effort_hours=total_hours,
            total_effort_person_days=total_days,
            confidence_level=confidence,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )

    def _collect_files(
        self,
        path: Path,
        stack: TechnologyStack
    ) -> Dict[str, str]:
        """Collect relevant source files for stack"""
        files = {}

        # Extension mapping by stack
        extensions = {
            TechnologyStack.CLASSIC_ASP: [".asp", ".inc", ".asa"],
            TechnologyStack.VB_NET_WEBFORMS: [".aspx", ".aspx.vb", ".vb", ".ascx"],
            TechnologyStack.CSHARP_WEBFORMS: [".aspx", ".aspx.cs", ".cs", ".ascx"],
            TechnologyStack.PHP_LEGACY: [".php", ".php3", ".php4", ".phtml"],
            TechnologyStack.JAVA_LEGACY: [".java", ".jsp", ".jspx"],
            TechnologyStack.COBOL: [".cob", ".cbl", ".cpy"],
            TechnologyStack.ORACLE_FORMS: [".fmb", ".fmx", ".pll"],
            TechnologyStack.POWERBUILDER: [".pbl", ".pbt", ".pbw"],
            TechnologyStack.PYTHON_WEB: [".py"],
        }

        for ext in extensions.get(stack, []):
            for file_path in path.rglob(f"*{ext}"):
                if any(skip in str(file_path) for skip in [
                    "node_modules", ".git", "vendor", "bin", "obj",
                    ".venv", "__pycache__", "site-packages", "migrations"
                ]):
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    files[str(file_path.relative_to(path))] = content
                except Exception:
                    continue

        return files

    def _detect_components(
        self,
        files: Dict[str, str],
        stack: TechnologyStack
    ) -> List[FunctionPointComponent]:
        """Detect function point components from source code"""
        components = []
        patterns = self.component_patterns.get(stack, {})

        component_counter: Dict[str, int] = defaultdict(int)

        for file_path, content in files.items():
            lines = content.splitlines()

            for comp_type, type_patterns in patterns.items():
                for pattern, description in type_patterns:
                    try:
                        regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                component_counter[comp_type.name] += 1

                                # Determine complexity based on context
                                complexity = self._estimate_complexity(
                                    content, pattern, i
                                )

                                # Calculate DET and RET counts (simplified)
                                det, ret = self._estimate_det_ret(
                                    content, comp_type, i
                                )

                                # Get IFPUG weight
                                weight = IFPUG_WEIGHTS[comp_type][complexity]

                                component_name = f"{comp_type.name}_{component_counter[comp_type.name]:03d}"

                                components.append(FunctionPointComponent(
                                    name=component_name,
                                    component_type=comp_type,
                                    complexity=complexity,
                                    det_count=det,
                                    ret_count=ret,
                                    unadjusted_fp=weight,
                                    file_path=file_path,
                                    line_number=i,
                                    notes=description
                                ))
                    except re.error:
                        continue

        return components

    def _estimate_complexity(
        self,
        content: str,
        pattern: str,
        line_number: int
    ) -> ComplexityLevel:
        """Estimate component complexity from context"""
        lines = content.splitlines()
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 20)
        context = "\n".join(lines[start:end])

        # Heuristics for complexity
        complexity_indicators = {
            "high": [
                r"(?:LEFT|RIGHT|FULL)\s+(?:OUTER\s+)?JOIN",
                r"GROUP\s+BY.*HAVING",
                r"UNION\s+(?:ALL)?",
                r"cursor|CURSOR",
                r"transaction|TRANSACTION",
                r"(?:try|catch|finally)",
                r"(?:async|await)",
            ],
            "low": [
                r"SELECT\s+\*\s+FROM\s+\w+\s+WHERE\s+\w+\s*=",
                r"INSERT\s+INTO\s+\w+\s+VALUES",
                r"UPDATE\s+\w+\s+SET\s+\w+\s*=",
            ]
        }

        # Check for high complexity indicators
        for pattern in complexity_indicators["high"]:
            if re.search(pattern, context, re.IGNORECASE):
                return ComplexityLevel.HIGH

        # Check for low complexity indicators
        low_matches = 0
        for pattern in complexity_indicators["low"]:
            if re.search(pattern, context, re.IGNORECASE):
                low_matches += 1

        if low_matches >= 2:
            return ComplexityLevel.LOW

        return ComplexityLevel.AVERAGE

    def _estimate_det_ret(
        self,
        content: str,
        comp_type: ComponentType,
        line_number: int
    ) -> Tuple[int, int]:
        """Estimate DET and RET counts (simplified IFPUG approach)"""
        lines = content.splitlines()
        start = max(0, line_number - 5)
        end = min(len(lines), line_number + 15)
        context = "\n".join(lines[start:end])

        # Count fields/parameters as DET approximation
        det = len(re.findall(r"[\w]+\s*=", context))
        det = max(1, min(det, 20))  # Clamp to reasonable range

        # Count table references as RET approximation
        ret = len(re.findall(r"\bFROM\s+(\w+)", context, re.IGNORECASE))
        ret = max(1, min(ret, 5))

        return det, ret

    def _calculate_vaf(
        self,
        components: List[FunctionPointComponent],
        stack: TechnologyStack
    ) -> float:
        """Calculate Value Adjustment Factor"""
        # Base VAF characteristics for legacy systems (0-5 scale each)
        # Total influence degree typically 0-70
        # VAF = 0.65 + (TDI / 100)

        # Estimate influence degrees based on stack
        vaf_scores = {
            TechnologyStack.CLASSIC_ASP: 35,       # Moderate complexity
            TechnologyStack.VB_NET_WEBFORMS: 40,   # Higher complexity
            TechnologyStack.CSHARP_WEBFORMS: 38,   # Moderate-high
            TechnologyStack.PHP_LEGACY: 32,        # Lower structure
            TechnologyStack.JAVA_LEGACY: 42,       # Higher complexity
            TechnologyStack.COBOL: 48,             # High complexity
            TechnologyStack.ORACLE_FORMS: 45,      # Proprietary complexity
            TechnologyStack.POWERBUILDER: 44,      # Proprietary
            TechnologyStack.PYTHON_WEB: 36,           # Moderate complexity
        }

        tdi = vaf_scores.get(stack, 35)
        vaf = 0.65 + (tdi / 100)

        return vaf

    def _identify_migration_factors(
        self,
        files: Dict[str, str],
        stack: TechnologyStack,
        components: List[FunctionPointComponent]
    ) -> List[MigrationFactor]:
        """Identify factors affecting migration effort"""
        factors = []

        # Base stack complexity
        stack_multiplier = STACK_COMPLEXITY_MULTIPLIERS.get(stack, 1.0)
        factors.append(MigrationFactor(
            name="Stack Complexity",
            category="technical",
            value=stack_multiplier,
            description=f"Base complexity for {stack.value} migration",
            source="stack_definition"
        ))

        # Check for specific complexity patterns
        all_content = "\n".join(files.values())

        # Database complexity
        if re.search(r"(?:stored\s+procedure|trigger|function)", all_content, re.I):
            factors.append(MigrationFactor(
                name="Database Logic",
                category="technical",
                value=1.3,
                description="Stored procedures/triggers require manual migration",
                source="pattern_detection"
            ))

        # Security concerns
        if re.search(r"(?:password|secret|api_key)\s*=\s*[\"']", all_content, re.I):
            factors.append(MigrationFactor(
                name="Hardcoded Secrets",
                category="risk",
                value=1.15,
                description="Credentials need secure handling in target",
                source="pattern_detection"
            ))

        # External integrations
        ext_count = len(re.findall(r"(?:http|ftp|soap|wsdl)://", all_content, re.I))
        if ext_count > 5:
            factors.append(MigrationFactor(
                name="External Integrations",
                category="technical",
                value=1.0 + (ext_count * 0.02),
                description=f"{ext_count} external service integrations detected",
                source="pattern_detection"
            ))

        # File count factor
        file_count = len(files)
        if file_count > 100:
            factors.append(MigrationFactor(
                name="Large Codebase",
                category="process",
                value=1.1 + (file_count / 1000),
                description=f"{file_count} files increase coordination effort",
                source="file_analysis"
            ))

        # Component variety
        comp_types = len(set(c.component_type for c in components))
        if comp_types >= 4:
            factors.append(MigrationFactor(
                name="Component Variety",
                category="technical",
                value=1.1,
                description="Multiple component types increase complexity",
                source="component_analysis"
            ))

        return factors

    def _calculate_complexity_multiplier(
        self,
        stack: TechnologyStack,
        factors: List[MigrationFactor]
    ) -> float:
        """Calculate overall complexity multiplier from factors"""
        # Start with base multiplier
        multiplier = 1.0

        # Apply all factors (multiplicative)
        for factor in factors:
            multiplier *= factor.value

        # Cap at reasonable range
        return min(max(multiplier, 1.0), 4.0)

    def _estimate_phases(
        self,
        adjusted_fp: float,
        complexity_multiplier: float,
        include_risk_buffer: bool
    ) -> List[PhaseEstimate]:
        """Estimate effort for each migration phase"""
        estimates = []

        for phase, base_hours_per_fp in HOURS_PER_FP_BY_PHASE.items():
            base_hours = adjusted_fp * base_hours_per_fp
            adjusted_hours = base_hours * complexity_multiplier

            # Risk buffer based on phase
            if include_risk_buffer:
                # Higher risk for development and testing phases
                if phase in [MigrationPhase.DEVELOPMENT, MigrationPhase.TESTING]:
                    risk_pct = 0.25
                elif phase in [MigrationPhase.DATA_MIGRATION, MigrationPhase.CUTOVER]:
                    risk_pct = 0.30
                else:
                    risk_pct = 0.15
                risk_buffer = adjusted_hours * risk_pct
            else:
                risk_buffer = 0

            total = adjusted_hours + risk_buffer

            # Phase-specific activities
            activities = self._get_phase_activities(phase)

            estimates.append(PhaseEstimate(
                phase=phase,
                base_hours=base_hours,
                adjusted_hours=adjusted_hours,
                fp_basis=adjusted_fp,
                multiplier=complexity_multiplier,
                risk_buffer_hours=risk_buffer,
                total_hours=total,
                activities=activities
            ))

        return estimates

    def _get_phase_activities(self, phase: MigrationPhase) -> List[str]:
        """Get typical activities for each phase"""
        activities = {
            MigrationPhase.DISCOVERY: [
                "Stakeholder interviews",
                "Dependency mapping",
                "Technical assessment"
            ],
            MigrationPhase.ANALYSIS: [
                "Code analysis",
                "Database schema review",
                "Integration point identification"
            ],
            MigrationPhase.PLANNING: [
                "Migration strategy",
                "Resource planning",
                "Risk mitigation planning"
            ],
            MigrationPhase.DESIGN: [
                "Target architecture design",
                "Data model mapping",
                "API design"
            ],
            MigrationPhase.DEVELOPMENT: [
                "Code migration",
                "New feature implementation",
                "Integration development"
            ],
            MigrationPhase.TESTING: [
                "Unit testing",
                "Integration testing",
                "UAT support"
            ],
            MigrationPhase.DATA_MIGRATION: [
                "Data mapping",
                "ETL development",
                "Data validation"
            ],
            MigrationPhase.DEPLOYMENT: [
                "Environment setup",
                "Configuration",
                "Deployment automation"
            ],
            MigrationPhase.PARALLEL_RUN: [
                "Parallel operation",
                "Comparison testing",
                "Issue resolution"
            ],
            MigrationPhase.CUTOVER: [
                "Final data sync",
                "Go-live execution",
                "Rollback preparation"
            ],
        }
        return activities.get(phase, [])

    def _calculate_confidence(
        self,
        components: List[FunctionPointComponent],
        files: Dict[str, str]
    ) -> float:
        """Calculate estimation confidence level"""
        # Factors affecting confidence
        confidence = 1.0

        # More components = higher confidence (better sample)
        if len(components) < 20:
            confidence *= 0.7
        elif len(components) < 50:
            confidence *= 0.85

        # File coverage
        if len(files) < 10:
            confidence *= 0.8

        # Component variety
        comp_types = len(set(c.component_type for c in components))
        if comp_types < 3:
            confidence *= 0.85

        return min(max(confidence, 0.3), 0.95)

    def _assess_risks(
        self,
        components: List[FunctionPointComponent],
        factors: List[MigrationFactor],
        stack: TechnologyStack
    ) -> Dict[str, Any]:
        """Assess migration risks"""
        risks = []

        # High complexity components
        high_complexity = sum(1 for c in components if c.complexity == ComplexityLevel.HIGH)
        if high_complexity > 10:
            risks.append({
                "category": "technical",
                "severity": "high",
                "description": f"{high_complexity} high-complexity components detected",
                "mitigation": "Consider phased migration with parallel development"
            })

        # Stack-specific risks
        if stack in [TechnologyStack.COBOL, TechnologyStack.ORACLE_FORMS]:
            risks.append({
                "category": "knowledge",
                "severity": "high",
                "description": "Specialized legacy knowledge required",
                "mitigation": "Ensure team includes legacy experts"
            })

        # Risk factors
        risk_factors = [f for f in factors if f.category == "risk"]
        for rf in risk_factors:
            risks.append({
                "category": "technical",
                "severity": "medium" if rf.value < 1.2 else "high",
                "description": rf.description,
                "mitigation": "Address in migration planning phase"
            })

        # Overall risk score
        risk_score = len([r for r in risks if r["severity"] == "high"]) * 3 + \
                     len([r for r in risks if r["severity"] == "medium"]) * 1

        return {
            "overall_level": "high" if risk_score >= 5 else "medium" if risk_score >= 2 else "low",
            "risk_count": len(risks),
            "risks": risks
        }

    def _generate_recommendations(
        self,
        source_stack: TechnologyStack,
        target_stack: str,
        components: List[FunctionPointComponent],
        factors: List[MigrationFactor],
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate migration recommendations"""
        recommendations = []

        # Stack-specific recommendations
        if source_stack == TechnologyStack.CLASSIC_ASP:
            recommendations.append(
                "Classic ASP: Consider complete rewrite rather than line-by-line migration"
            )
        elif source_stack == TechnologyStack.VB_NET_WEBFORMS:
            recommendations.append(
                "WebForms: Use Microsoft's WebForms to Blazor migration guidance"
            )
        elif source_stack == TechnologyStack.PHP_LEGACY:
            recommendations.append(
                "PHP Legacy: Upgrade to PHP 8+ first, then refactor to modern framework"
            )

        # Component-based recommendations
        ilf_count = sum(1 for c in components if c.component_type == ComponentType.ILF)
        if ilf_count > 20:
            recommendations.append(
                f"Large data model ({ilf_count} ILFs): Plan comprehensive data migration strategy"
            )

        eif_count = sum(1 for c in components if c.component_type == ComponentType.EIF)
        if eif_count > 5:
            recommendations.append(
                f"Multiple external interfaces ({eif_count}): Create integration test suite early"
            )

        # Risk-based recommendations
        if risk_assessment["overall_level"] == "high":
            recommendations.append(
                "High risk assessment: Recommend proof-of-concept before full migration"
            )

        # General recommendations
        recommendations.append(
            "Implement comprehensive logging in target for post-migration validation"
        )
        recommendations.append(
            "Create automated regression test suite before starting migration"
        )

        return recommendations

    def _empty_result(
        self,
        directory: str,
        source_stack: TechnologyStack,
        target_stack: str,
        message: str
    ) -> MigrationEstimationResult:
        """Create empty result with message"""
        return MigrationEstimationResult(
            project_path=directory,
            source_stack=source_stack,
            target_stack=target_stack,
            total_unadjusted_fp=0,
            value_adjustment_factor=1.0,
            total_adjusted_fp=0,
            components=[],
            migration_factors=[],
            phase_estimates=[],
            total_effort_hours=0,
            total_effort_person_days=0,
            confidence_level=0,
            risk_assessment={"overall_level": "unknown", "risks": []},
            recommendations=[message]
        )

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "supported_stacks": [s.value for s in TechnologyStack],
            "phases": [p.value for p in MigrationPhase],
            "component_types": [c.value for c in ComponentType],
            "hours_per_fp_total": sum(HOURS_PER_FP_BY_PHASE.values())
        }
