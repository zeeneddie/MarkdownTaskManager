"""
Library Migration Mapper Service - Fase 26: Migration Execution

Week 140-141: Maps legacy libraries to modern equivalents across different stacks.
Identifies high-risk libraries without direct equivalents.

Agent: Felix (Feature Architect)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


# ==================== Enums ====================

class TargetStack(Enum):
    """Target technology stacks"""
    DOTNET_8 = "dotnet8"
    PYTHON_DJANGO = "python_django"
    PYTHON_FASTAPI = "python_fastapi"
    NODEJS_NESTJS = "nodejs_nestjs"
    JAVA_SPRING = "java_spring"
    GO_FIBER = "go_fiber"
    RUST_ACTIX = "rust_actix"


class MigrationEffort(Enum):
    """Migration effort levels"""
    TRIVIAL = "trivial"  # Drop-in replacement
    LOW = "low"  # Minor API changes
    MEDIUM = "medium"  # Significant refactoring
    HIGH = "high"  # Major rewrite
    CRITICAL = "critical"  # No equivalent, custom implementation


class RiskLevel(Enum):
    """Migration risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LibraryCategory(Enum):
    """Library functional categories"""
    DATABASE = "database"
    HTTP_CLIENT = "http_client"
    AUTHENTICATION = "authentication"
    REPORTING = "reporting"
    OFFICE = "office"
    EMAIL = "email"
    LOGGING = "logging"
    CACHING = "caching"
    SERIALIZATION = "serialization"
    TESTING = "testing"
    UI_COMPONENTS = "ui_components"
    FILE_IO = "file_io"
    CRYPTO = "crypto"
    SCHEDULING = "scheduling"
    MESSAGING = "messaging"
    VALIDATION = "validation"
    IMAGING = "imaging"
    PDF = "pdf"
    XML = "xml"
    OTHER = "other"


# ==================== Data Classes ====================

@dataclass
class LegacyLibrary:
    """Detected legacy library usage"""
    name: str
    version: Optional[str]
    category: LibraryCategory
    usage_count: int
    usage_patterns: List[str]
    file_locations: List[str]
    import_statements: List[str]
    detected_features: List[str] = field(default_factory=list)
    is_deprecated: bool = False
    security_issues: List[str] = field(default_factory=list)


@dataclass
class ModernEquivalent:
    """Modern library equivalent"""
    name: str
    package_name: str  # e.g., "pip install xxx" or "npm install xxx"
    stack: TargetStack
    version: Optional[str]
    migration_effort: MigrationEffort
    api_similarity: float  # 0.0 to 1.0
    documentation_url: Optional[str]
    notes: str = ""
    breaking_changes: List[str] = field(default_factory=list)
    additional_dependencies: List[str] = field(default_factory=list)


@dataclass
class LibraryMapping:
    """Complete mapping from legacy to modern"""
    legacy: LegacyLibrary
    equivalents: Dict[TargetStack, List[ModernEquivalent]]
    risk_level: RiskLevel
    recommended_stack: Optional[TargetStack]
    migration_notes: str = ""
    requires_custom_implementation: bool = False
    estimated_hours: float = 0.0


@dataclass
class UsagePattern:
    """Detected usage pattern for a library"""
    pattern_name: str
    code_sample: str
    file_path: str
    line_number: int
    migration_strategy: str
    target_code_sample: Optional[str] = None


@dataclass
class MigrationRule:
    """Rule for automated code transformation"""
    id: str
    legacy_pattern: str  # Regex pattern
    replacement_template: str
    target_stack: TargetStack
    description: str
    confidence: float = 1.0
    requires_review: bool = False


@dataclass
class LibraryScanResult:
    """Result of scanning a codebase for libraries"""
    scan_id: str
    project_path: str
    scan_timestamp: datetime
    libraries_found: List[LegacyLibrary]
    mappings: List[LibraryMapping]
    total_files_scanned: int
    total_usage_count: int
    high_risk_count: int
    unmapped_count: int


# ==================== Built-in Mappings ====================

# VB.NET / .NET Framework to Modern Stack mappings
LEGACY_LIBRARY_MAPPINGS: Dict[str, Dict[str, Any]] = {
    # Database
    "ADODB": {
        "category": LibraryCategory.DATABASE,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "Entity Framework Core 8", "package": "Microsoft.EntityFrameworkCore",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.3},
                {"name": "Dapper", "package": "Dapper", "effort": MigrationEffort.LOW, "similarity": 0.5},
            ],
            TargetStack.PYTHON_DJANGO: [
                {"name": "Django ORM", "package": "django", "effort": MigrationEffort.MEDIUM, "similarity": 0.3},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "SQLAlchemy", "package": "sqlalchemy", "effort": MigrationEffort.MEDIUM, "similarity": 0.4},
            ],
        },
        "notes": "Recordset to ORM migration requires query rewrite",
    },
    "System.Data.SqlClient": {
        "category": LibraryCategory.DATABASE,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "Microsoft.Data.SqlClient", "package": "Microsoft.Data.SqlClient",
                 "effort": MigrationEffort.TRIVIAL, "similarity": 0.95},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "pyodbc", "package": "pyodbc", "effort": MigrationEffort.LOW, "similarity": 0.6},
            ],
        },
    },

    # HTTP Client
    "MSXML2.XMLHTTP": {
        "category": LibraryCategory.HTTP_CLIENT,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "HttpClient", "package": "System.Net.Http",
                 "effort": MigrationEffort.LOW, "similarity": 0.6},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "httpx", "package": "httpx", "effort": MigrationEffort.LOW, "similarity": 0.5},
                {"name": "aiohttp", "package": "aiohttp", "effort": MigrationEffort.MEDIUM, "similarity": 0.4},
            ],
        },
    },
    "WinHttp.WinHttpRequest": {
        "category": LibraryCategory.HTTP_CLIENT,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "HttpClient", "package": "System.Net.Http",
                 "effort": MigrationEffort.LOW, "similarity": 0.5},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "requests", "package": "requests", "effort": MigrationEffort.LOW, "similarity": 0.5},
            ],
        },
    },

    # Office/Excel
    "Microsoft.Office.Interop.Excel": {
        "category": LibraryCategory.OFFICE,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "ClosedXML", "package": "ClosedXML",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.6},
                {"name": "EPPlus", "package": "EPPlus", "effort": MigrationEffort.MEDIUM, "similarity": 0.5},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "openpyxl", "package": "openpyxl", "effort": MigrationEffort.MEDIUM, "similarity": 0.5},
                {"name": "pandas", "package": "pandas", "effort": MigrationEffort.MEDIUM, "similarity": 0.4},
            ],
        },
        "notes": "COM Interop to pure library migration. May require Office on server for full compatibility.",
    },

    # Reporting
    "CrystalDecisions.CrystalReports": {
        "category": LibraryCategory.REPORTING,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "FastReport.Net", "package": "FastReport.Net",
                 "effort": MigrationEffort.HIGH, "similarity": 0.4},
                {"name": "RDLC", "package": "Microsoft.Reporting",
                 "effort": MigrationEffort.HIGH, "similarity": 0.3},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "ReportLab", "package": "reportlab",
                 "effort": MigrationEffort.HIGH, "similarity": 0.2},
                {"name": "WeasyPrint", "package": "weasyprint",
                 "effort": MigrationEffort.HIGH, "similarity": 0.2},
            ],
        },
        "notes": "Crystal Reports migration is high-risk. Report definitions need recreation.",
        "risk": RiskLevel.HIGH,
    },

    # Authentication
    "System.Web.Security.FormsAuthentication": {
        "category": LibraryCategory.AUTHENTICATION,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "ASP.NET Core Identity", "package": "Microsoft.AspNetCore.Identity",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.4},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "FastAPI Security", "package": "fastapi[security]",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.3},
            ],
        },
    },

    # Email
    "System.Web.Mail": {
        "category": LibraryCategory.EMAIL,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "MailKit", "package": "MailKit",
                 "effort": MigrationEffort.LOW, "similarity": 0.7},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "fastapi-mail", "package": "fastapi-mail",
                 "effort": MigrationEffort.LOW, "similarity": 0.6},
            ],
        },
    },
    "System.Net.Mail": {
        "category": LibraryCategory.EMAIL,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "MailKit", "package": "MailKit",
                 "effort": MigrationEffort.TRIVIAL, "similarity": 0.8},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "aiosmtplib", "package": "aiosmtplib",
                 "effort": MigrationEffort.LOW, "similarity": 0.6},
            ],
        },
    },

    # XML
    "MSXML2.DOMDocument": {
        "category": LibraryCategory.XML,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "System.Xml.Linq", "package": "System.Xml.Linq",
                 "effort": MigrationEffort.LOW, "similarity": 0.6},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "lxml", "package": "lxml", "effort": MigrationEffort.LOW, "similarity": 0.5},
            ],
        },
    },

    # Caching
    "System.Web.Caching": {
        "category": LibraryCategory.CACHING,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "IMemoryCache", "package": "Microsoft.Extensions.Caching.Memory",
                 "effort": MigrationEffort.LOW, "similarity": 0.7},
                {"name": "Redis", "package": "StackExchange.Redis",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.5},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "redis-py", "package": "redis", "effort": MigrationEffort.LOW, "similarity": 0.5},
            ],
        },
    },

    # Imaging
    "System.Drawing": {
        "category": LibraryCategory.IMAGING,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "ImageSharp", "package": "SixLabors.ImageSharp",
                 "effort": MigrationEffort.LOW, "similarity": 0.6},
                {"name": "SkiaSharp", "package": "SkiaSharp",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.5},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "Pillow", "package": "Pillow", "effort": MigrationEffort.LOW, "similarity": 0.5},
            ],
        },
        "notes": "System.Drawing is Windows-only in .NET Core. Cross-platform alternatives needed.",
    },

    # PDF
    "iTextSharp": {
        "category": LibraryCategory.PDF,
        "equivalents": {
            TargetStack.DOTNET_8: [
                {"name": "iText 7", "package": "itext7",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.6},
                {"name": "QuestPDF", "package": "QuestPDF",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.4},
            ],
            TargetStack.PYTHON_FASTAPI: [
                {"name": "reportlab", "package": "reportlab",
                 "effort": MigrationEffort.MEDIUM, "similarity": 0.4},
                {"name": "PyPDF2", "package": "PyPDF2", "effort": MigrationEffort.MEDIUM, "similarity": 0.3},
            ],
        },
    },
}


# ==================== Service ====================

class LibraryMigrationMapperService:
    """
    Maps legacy libraries to modern equivalents across different technology stacks.

    Features:
    - Library detection from code patterns
    - Multi-stack mapping (target stack recommendations)
    - Risk assessment for unmapped/high-effort libraries
    - Migration rule generation
    - Usage pattern analysis
    """

    def __init__(self):
        self.library_mappings = LEGACY_LIBRARY_MAPPINGS
        self.custom_mappings: Dict[str, Dict[str, Any]] = {}
        self.scan_results: Dict[str, LibraryScanResult] = {}

    # ==================== Library Detection ====================

    async def scan_codebase(
        self,
        project_path: str,
        file_extensions: Optional[List[str]] = None
    ) -> LibraryScanResult:
        """
        Scan codebase to detect legacy library usage.

        Supports: .vb, .cs, .asp, .aspx, .config files
        """
        import os
        from uuid import uuid4

        if file_extensions is None:
            file_extensions = [".vb", ".cs", ".asp", ".aspx", ".config", ".csproj", ".vbproj"]

        scan_id = str(uuid4())[:8]
        libraries_found: Dict[str, LegacyLibrary] = {}
        total_files = 0

        # Patterns to detect library usage
        detection_patterns = {
            # VB.NET / VB6
            r"Imports\s+(\w+(?:\.\w+)*)": "import",
            r"CreateObject\s*\(\s*[\"']([^\"']+)[\"']\s*\)": "com_create",
            r"Dim\s+\w+\s+As\s+(?:New\s+)?(\w+(?:\.\w+)*)": "declaration",
            # C#
            r"using\s+(\w+(?:\.\w+)*)\s*;": "using",
            r"new\s+(\w+(?:\.\w+)*)\s*\(": "instantiation",
            # Config references
            r"<add\s+assembly=\"([^\"]+)\"": "assembly_ref",
            r"<Reference\s+Include=\"([^\"]+)\"": "project_ref",
        }

        try:
            for root, _, files in os.walk(project_path):
                for filename in files:
                    if not any(filename.endswith(ext) for ext in file_extensions):
                        continue

                    file_path = os.path.join(root, filename)
                    total_files += 1

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for pattern, pattern_type in detection_patterns.items():
                            for match in re.finditer(pattern, content, re.IGNORECASE):
                                lib_name = match.group(1)
                                base_lib = lib_name.split('.')[0]

                                # Check if this is a known library
                                known_lib = self._find_known_library(lib_name)

                                if known_lib or self._is_likely_external_library(lib_name):
                                    key = known_lib or lib_name

                                    if key not in libraries_found:
                                        category = self._categorize_library(lib_name)
                                        libraries_found[key] = LegacyLibrary(
                                            name=key,
                                            version=None,
                                            category=category,
                                            usage_count=0,
                                            usage_patterns=[],
                                            file_locations=[],
                                            import_statements=[],
                                        )

                                    lib = libraries_found[key]
                                    lib.usage_count += 1
                                    if file_path not in lib.file_locations:
                                        lib.file_locations.append(file_path)
                                    if match.group(0) not in lib.import_statements:
                                        lib.import_statements.append(match.group(0))

                    except Exception as e:
                        logger.debug(f"Error scanning {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error scanning codebase: {e}")

        # Generate mappings for found libraries
        libraries_list = list(libraries_found.values())
        mappings = await self.generate_mappings(libraries_list)

        result = LibraryScanResult(
            scan_id=scan_id,
            project_path=project_path,
            scan_timestamp=datetime.now(),
            libraries_found=libraries_list,
            mappings=mappings,
            total_files_scanned=total_files,
            total_usage_count=sum(lib.usage_count for lib in libraries_list),
            high_risk_count=sum(1 for m in mappings if m.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]),
            unmapped_count=sum(1 for m in mappings if m.requires_custom_implementation),
        )

        self.scan_results[scan_id] = result
        logger.info(f"Scan complete: {len(libraries_list)} libraries, {result.high_risk_count} high-risk")

        return result

    def _find_known_library(self, lib_name: str) -> Optional[str]:
        """Find matching known library."""
        for known in self.library_mappings:
            if known.lower() in lib_name.lower() or lib_name.lower() in known.lower():
                return known
        return None

    def _is_likely_external_library(self, lib_name: str) -> bool:
        """Check if library name suggests external/third-party library."""
        # Skip common .NET framework namespaces that aren't migration targets
        skip_prefixes = ["System.Collections", "System.Linq", "System.Text", "System.Threading"]
        for prefix in skip_prefixes:
            if lib_name.startswith(prefix):
                return False

        # Known external indicators
        external_indicators = [
            "ADODB", "MSXML", "Crystal", "Interop", "WinHttp",
            "Scripting", "CDO", "MAPI",
        ]
        return any(ind in lib_name for ind in external_indicators)

    def _categorize_library(self, lib_name: str) -> LibraryCategory:
        """Categorize library by name patterns."""
        name_lower = lib_name.lower()

        category_patterns = {
            LibraryCategory.DATABASE: ["sql", "data", "ado", "db", "oracle", "mysql"],
            LibraryCategory.HTTP_CLIENT: ["http", "web", "rest", "soap", "xml"],
            LibraryCategory.AUTHENTICATION: ["auth", "security", "identity", "oauth"],
            LibraryCategory.REPORTING: ["report", "crystal", "rdlc"],
            LibraryCategory.OFFICE: ["office", "excel", "word", "interop"],
            LibraryCategory.EMAIL: ["mail", "smtp", "mapi", "cdo"],
            LibraryCategory.CACHING: ["cache", "redis", "memcach"],
            LibraryCategory.IMAGING: ["image", "drawing", "graphics", "gdi"],
            LibraryCategory.PDF: ["pdf", "itext"],
            LibraryCategory.XML: ["xml", "xslt", "xpath"],
        }

        for category, patterns in category_patterns.items():
            if any(p in name_lower for p in patterns):
                return category

        return LibraryCategory.OTHER

    # ==================== Mapping Generation ====================

    async def generate_mappings(
        self,
        libraries: List[LegacyLibrary],
        target_stacks: Optional[List[TargetStack]] = None
    ) -> List[LibraryMapping]:
        """Generate mappings for detected libraries."""
        if target_stacks is None:
            target_stacks = list(TargetStack)

        mappings = []

        for lib in libraries:
            mapping = await self.get_library_mapping(lib, target_stacks)
            mappings.append(mapping)

        return mappings

    async def get_library_mapping(
        self,
        library: LegacyLibrary,
        target_stacks: List[TargetStack]
    ) -> LibraryMapping:
        """Get mapping for a single library."""
        equivalents: Dict[TargetStack, List[ModernEquivalent]] = {}
        best_stack: Optional[TargetStack] = None
        best_similarity = 0.0

        # Check built-in mappings
        mapping_data = self.library_mappings.get(library.name) or \
                       self.custom_mappings.get(library.name)

        if mapping_data:
            for stack in target_stacks:
                if stack in mapping_data.get("equivalents", {}):
                    stack_equivalents = []
                    for eq in mapping_data["equivalents"][stack]:
                        equiv = ModernEquivalent(
                            name=eq["name"],
                            package_name=eq["package"],
                            stack=stack,
                            version=eq.get("version"),
                            migration_effort=eq.get("effort", MigrationEffort.MEDIUM),
                            api_similarity=eq.get("similarity", 0.5),
                            documentation_url=eq.get("docs"),
                            notes=eq.get("notes", ""),
                        )
                        stack_equivalents.append(equiv)

                        if equiv.api_similarity > best_similarity:
                            best_similarity = equiv.api_similarity
                            best_stack = stack

                    equivalents[stack] = stack_equivalents

        # Determine risk level
        risk = self._calculate_risk_level(library, equivalents)

        # Estimate hours
        hours = self._estimate_migration_hours(library, equivalents)

        return LibraryMapping(
            legacy=library,
            equivalents=equivalents,
            risk_level=risk,
            recommended_stack=best_stack,
            migration_notes=mapping_data.get("notes", "") if mapping_data else "",
            requires_custom_implementation=len(equivalents) == 0,
            estimated_hours=hours,
        )

    def _calculate_risk_level(
        self,
        library: LegacyLibrary,
        equivalents: Dict[TargetStack, List[ModernEquivalent]]
    ) -> RiskLevel:
        """Calculate migration risk level."""
        if not equivalents:
            return RiskLevel.CRITICAL

        # Find best available effort
        best_effort = MigrationEffort.CRITICAL
        for stack_equivs in equivalents.values():
            for eq in stack_equivs:
                if eq.migration_effort.value < best_effort.value:
                    best_effort = eq.migration_effort

        effort_to_risk = {
            MigrationEffort.TRIVIAL: RiskLevel.LOW,
            MigrationEffort.LOW: RiskLevel.LOW,
            MigrationEffort.MEDIUM: RiskLevel.MEDIUM,
            MigrationEffort.HIGH: RiskLevel.HIGH,
            MigrationEffort.CRITICAL: RiskLevel.CRITICAL,
        }

        # Adjust for usage count
        risk = effort_to_risk[best_effort]
        if library.usage_count > 50 and risk == RiskLevel.MEDIUM:
            risk = RiskLevel.HIGH

        return risk

    def _estimate_migration_hours(
        self,
        library: LegacyLibrary,
        equivalents: Dict[TargetStack, List[ModernEquivalent]]
    ) -> float:
        """Estimate migration hours based on library and usage."""
        base_hours = {
            MigrationEffort.TRIVIAL: 1,
            MigrationEffort.LOW: 4,
            MigrationEffort.MEDIUM: 16,
            MigrationEffort.HIGH: 40,
            MigrationEffort.CRITICAL: 80,
        }

        if not equivalents:
            return 80 + (library.usage_count * 0.5)

        best_effort = MigrationEffort.CRITICAL
        for stack_equivs in equivalents.values():
            for eq in stack_equivs:
                if eq.migration_effort.value < best_effort.value:
                    best_effort = eq.migration_effort

        hours = base_hours[best_effort]

        # Scale by usage
        usage_multiplier = 1 + (library.usage_count / 100)
        hours *= min(usage_multiplier, 3.0)  # Cap at 3x

        return round(hours, 1)

    # ==================== Migration Rules ====================

    async def generate_migration_rules(
        self,
        library: LegacyLibrary,
        target_stack: TargetStack
    ) -> List[MigrationRule]:
        """Generate code transformation rules for a library migration."""
        rules = []

        # Common patterns for known libraries
        if library.name == "ADODB" and target_stack == TargetStack.DOTNET_8:
            rules.extend([
                MigrationRule(
                    id="adodb-recordset-to-ef",
                    legacy_pattern=r"Set\s+(\w+)\s*=\s*(\w+)\.Execute\s*\(",
                    replacement_template=r"var \1 = await context.\2.ToListAsync(",
                    target_stack=target_stack,
                    description="Convert ADODB.Recordset.Execute to EF Core ToListAsync",
                    confidence=0.7,
                    requires_review=True,
                ),
                MigrationRule(
                    id="adodb-connection-string",
                    legacy_pattern=r"Provider=SQLOLEDB",
                    replacement_template=r"Server=",
                    target_stack=target_stack,
                    description="Convert OLEDB connection string to SqlClient format",
                    confidence=0.9,
                ),
            ])

        elif library.name == "MSXML2.XMLHTTP" and target_stack == TargetStack.DOTNET_8:
            rules.extend([
                MigrationRule(
                    id="xmlhttp-to-httpclient",
                    legacy_pattern=r"Set\s+(\w+)\s*=\s*CreateObject\s*\(\s*[\"']MSXML2\.XMLHTTP[\"']\s*\)",
                    replacement_template=r"using var \1 = new HttpClient()",
                    target_stack=target_stack,
                    description="Replace XMLHTTP COM object with HttpClient",
                    confidence=0.8,
                ),
                MigrationRule(
                    id="xmlhttp-open",
                    legacy_pattern=r"(\w+)\.Open\s+[\"'](\w+)[\"']\s*,\s*[\"']([^\"']+)[\"']",
                    replacement_template=r"var response = await \1.SendAsync(new HttpRequestMessage(HttpMethod.\2, \"\3\"))",
                    target_stack=target_stack,
                    description="Convert XMLHTTP.Open to HttpClient.SendAsync",
                    confidence=0.6,
                    requires_review=True,
                ),
            ])

        elif library.name == "Microsoft.Office.Interop.Excel" and target_stack == TargetStack.DOTNET_8:
            rules.extend([
                MigrationRule(
                    id="excel-interop-to-closedxml",
                    legacy_pattern=r"New\s+Excel\.Application\s*\(\s*\)",
                    replacement_template=r"new XLWorkbook()",
                    target_stack=target_stack,
                    description="Replace Excel COM to ClosedXML",
                    confidence=0.7,
                    requires_review=True,
                ),
            ])

        return rules

    # ==================== Reporting ====================

    def get_risk_summary(
        self,
        scan_result: LibraryScanResult
    ) -> Dict[str, Any]:
        """Get risk summary for a scan result."""
        risk_counts = {level.value: 0 for level in RiskLevel}
        category_counts = {cat.value: 0 for cat in LibraryCategory}

        for mapping in scan_result.mappings:
            risk_counts[mapping.risk_level.value] += 1
            category_counts[mapping.legacy.category.value] += 1

        total_hours = sum(m.estimated_hours for m in scan_result.mappings)

        return {
            "scan_id": scan_result.scan_id,
            "libraries_found": len(scan_result.libraries_found),
            "risk_distribution": risk_counts,
            "category_distribution": category_counts,
            "high_risk_libraries": [
                m.legacy.name for m in scan_result.mappings
                if m.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            ],
            "unmapped_libraries": [
                m.legacy.name for m in scan_result.mappings
                if m.requires_custom_implementation
            ],
            "total_estimated_hours": total_hours,
            "total_usage_count": scan_result.total_usage_count,
        }

    def to_markdown_report(
        self,
        scan_result: LibraryScanResult,
        target_stack: Optional[TargetStack] = None
    ) -> str:
        """Generate markdown report for library mappings."""
        lines = [
            f"# Library Migration Report",
            f"",
            f"**Scan ID:** {scan_result.scan_id}",
            f"**Project:** {scan_result.project_path}",
            f"**Scanned:** {scan_result.scan_timestamp.isoformat()}",
            f"**Files Scanned:** {scan_result.total_files_scanned}",
            f"",
            f"## Summary",
            f"",
            f"- **Libraries Found:** {len(scan_result.libraries_found)}",
            f"- **Total Usage:** {scan_result.total_usage_count}",
            f"- **High Risk:** {scan_result.high_risk_count}",
            f"- **Unmapped:** {scan_result.unmapped_count}",
            f"",
            f"## Library Mappings",
            f"",
            f"| Legacy Library | Category | Usage | Risk | Target | Effort | Hours |",
            f"|----------------|----------|-------|------|--------|--------|-------|",
        ]

        for mapping in sorted(scan_result.mappings, key=lambda m: m.risk_level.value, reverse=True):
            lib = mapping.legacy
            stack = target_stack or mapping.recommended_stack

            if stack and stack in mapping.equivalents:
                target_lib = mapping.equivalents[stack][0].name if mapping.equivalents[stack] else "Custom"
                effort = mapping.equivalents[stack][0].migration_effort.value if mapping.equivalents[stack] else "critical"
            else:
                target_lib = "No mapping"
                effort = "N/A"

            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
            lines.append(
                f"| {lib.name} | {lib.category.value} | {lib.usage_count} | "
                f"{risk_emoji.get(mapping.risk_level.value, '⚪')} {mapping.risk_level.value} | "
                f"{target_lib} | {effort} | {mapping.estimated_hours:.0f}h |"
            )

        # High risk section
        high_risk = [m for m in scan_result.mappings if m.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if high_risk:
            lines.extend([
                f"",
                f"## High Risk Libraries",
                f"",
            ])
            for mapping in high_risk:
                lines.append(f"### {mapping.legacy.name}")
                lines.append(f"")
                lines.append(f"- **Category:** {mapping.legacy.category.value}")
                lines.append(f"- **Usage Count:** {mapping.legacy.usage_count}")
                lines.append(f"- **Risk:** {mapping.risk_level.value}")
                if mapping.migration_notes:
                    lines.append(f"- **Notes:** {mapping.migration_notes}")
                lines.append(f"- **Estimated Hours:** {mapping.estimated_hours:.0f}")
                lines.append(f"")

        return "\n".join(lines)

    # ==================== Custom Mappings ====================

    async def add_custom_mapping(
        self,
        library_name: str,
        category: LibraryCategory,
        equivalents: Dict[TargetStack, List[Dict[str, Any]]],
        notes: str = ""
    ) -> None:
        """Add a custom library mapping."""
        self.custom_mappings[library_name] = {
            "category": category,
            "equivalents": equivalents,
            "notes": notes,
        }
        logger.info(f"Added custom mapping for: {library_name}")
