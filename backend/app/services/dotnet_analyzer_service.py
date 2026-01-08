"""
DotNet Analyzer Service

Week 65 Day 4: Specialized analyzer for .NET legacy code.
Detects ASP.NET WebForms, WCF, and other legacy .NET patterns.

Features:
- ASP.NET WebForms pattern detection (ViewState, PostBack, runat="server")
- WCF service analysis (ServiceContract, OperationContract, bindings)
- Code-behind complexity analysis
- Legacy pattern detection with migration recommendations
- Module extraction from .aspx/.ascx files

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migration_analysis import (
    MigrationAnalysis,
    MigrationModule,
    LegacyPattern,
    FPBreakdown
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class WebFormsPage:
    """Represents an ASP.NET WebForms page"""
    file_path: str
    page_name: str
    code_behind: Optional[str] = None
    master_page: Optional[str] = None
    controls: List[str] = field(default_factory=list)
    viewstate_usage: bool = False
    postback_handlers: List[str] = field(default_factory=list)
    data_bindings: List[str] = field(default_factory=list)
    loc: int = 0
    code_behind_loc: int = 0
    complexity: float = 0.0


@dataclass
class WCFService:
    """Represents a WCF service"""
    file_path: str
    service_name: str
    contracts: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    bindings: List[str] = field(default_factory=list)
    data_contracts: List[str] = field(default_factory=list)
    loc: int = 0
    complexity: float = 0.0


@dataclass
class LegacyPatternMatch:
    """A detected legacy pattern"""
    pattern_name: str
    pattern_category: str
    file_path: str
    line_number: int
    code_snippet: str
    risk_level: str  # low, medium, high, critical
    migration_note: str
    migration_target: str
    fp_multiplier: float = 1.0
    is_security_issue: bool = False
    owasp_category: Optional[str] = None


@dataclass
class DotNetAnalysisResult:
    """Complete .NET analysis result"""
    webforms_pages: List[WebFormsPage] = field(default_factory=list)
    wcf_services: List[WCFService] = field(default_factory=list)
    user_controls: List[str] = field(default_factory=list)
    master_pages: List[str] = field(default_factory=list)
    legacy_patterns: List[LegacyPatternMatch] = field(default_factory=list)
    total_aspx_files: int = 0
    total_code_behind_files: int = 0
    total_wcf_services: int = 0
    total_loc: int = 0
    avg_complexity: float = 0.0
    migration_difficulty: str = "medium"  # easy, medium, hard, complex


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

# ASP.NET WebForms patterns
WEBFORMS_PATTERNS = {
    "viewstate": {
        "pattern": r'EnableViewState\s*=\s*["\']?true|ViewState\[|__VIEWSTATE',
        "risk": "medium",
        "note": "ViewState creates large hidden fields and state management issues",
        "target": "Blazor Server state or client-side state management",
        "multiplier": 1.3,
    },
    "postback": {
        "pattern": r'IsPostBack|__doPostBack|AutoPostBack\s*=\s*["\']?true',
        "risk": "medium",
        "note": "PostBack model requires full page lifecycle understanding",
        "target": "Blazor component events or REST API calls",
        "multiplier": 1.2,
    },
    "page_lifecycle": {
        "pattern": r'Page_Load|Page_Init|Page_PreRender|OnLoad|OnInit',
        "risk": "medium",
        "note": "Page lifecycle events need conversion to component lifecycle",
        "target": "Blazor OnInitialized/OnParametersSet",
        "multiplier": 1.2,
    },
    "server_controls": {
        "pattern": r'<asp:(GridView|DataGrid|Repeater|FormView|DetailsView)',
        "risk": "high",
        "note": "Complex data-bound server controls require significant rework",
        "target": "Blazor DataGrid or third-party component",
        "multiplier": 1.5,
    },
    "updatepanel": {
        "pattern": r'<asp:UpdatePanel|<asp:ScriptManager',
        "risk": "medium",
        "note": "UpdatePanel partial postbacks need conversion to proper AJAX",
        "target": "Blazor SignalR or fetch API",
        "multiplier": 1.3,
    },
    "session_state": {
        "pattern": r'Session\[|HttpContext\.Current\.Session',
        "risk": "medium",
        "note": "Session state management differs in modern architectures",
        "target": "Distributed cache or JWT tokens",
        "multiplier": 1.2,
    },
    "code_behind_coupling": {
        "pattern": r'FindControl\(|Controls\.Add\(|Controls\[',
        "risk": "high",
        "note": "Dynamic control manipulation is hard to migrate",
        "target": "Blazor dynamic components or RenderFragment",
        "multiplier": 1.4,
    },
    "inline_sql": {
        "pattern": r'SqlCommand|SqlDataAdapter|ExecuteNonQuery|ExecuteReader',
        "risk": "high",
        "note": "Inline SQL should be converted to parameterized queries or ORM",
        "target": "Entity Framework Core or Dapper",
        "multiplier": 1.3,
        "security": True,
        "owasp": "A03",  # Injection
    },
    "response_write": {
        "pattern": r'Response\.Write\(|<%=.*%>',
        "risk": "medium",
        "note": "Direct response writing needs XSS protection",
        "target": "Razor syntax with automatic encoding",
        "multiplier": 1.1,
        "security": True,
        "owasp": "A03",  # Injection (XSS)
    },
}

# WCF patterns
WCF_PATTERNS = {
    "service_contract": {
        "pattern": r'\[ServiceContract\]|\[ServiceContract\(',
        "risk": "medium",
        "note": "WCF services need conversion to gRPC or REST API",
        "target": "ASP.NET Core Web API or gRPC",
        "multiplier": 1.3,
    },
    "operation_contract": {
        "pattern": r'\[OperationContract\]|\[OperationContract\(',
        "risk": "low",
        "note": "Operation contracts map to API endpoints",
        "target": "Controller actions or gRPC methods",
        "multiplier": 1.1,
    },
    "data_contract": {
        "pattern": r'\[DataContract\]|\[DataMember\]',
        "risk": "low",
        "note": "Data contracts can often be simplified to POCOs",
        "target": "Record types or simple DTOs",
        "multiplier": 1.0,
    },
    "basichttp_binding": {
        "pattern": r'basicHttpBinding|BasicHttpBinding',
        "risk": "low",
        "note": "Basic HTTP binding is straightforward to migrate",
        "target": "REST API with JSON",
        "multiplier": 1.0,
    },
    "wshttp_binding": {
        "pattern": r'wsHttpBinding|WSHttpBinding',
        "risk": "high",
        "note": "WS-* protocols require careful security migration",
        "target": "OAuth2/OIDC with HTTPS",
        "multiplier": 1.4,
    },
    "nettcp_binding": {
        "pattern": r'netTcpBinding|NetTcpBinding',
        "risk": "medium",
        "note": "TCP binding needs conversion to gRPC for performance",
        "target": "gRPC with HTTP/2",
        "multiplier": 1.3,
    },
    "duplex_channel": {
        "pattern": r'IDuplexSession|CallbackContract|DuplexClientBase',
        "risk": "high",
        "note": "Duplex communication requires SignalR or WebSocket",
        "target": "SignalR Hub or WebSocket",
        "multiplier": 1.5,
    },
}

# ASP Classic patterns
ASP_CLASSIC_PATTERNS = {
    "response_write": {
        "pattern": r'Response\.Write',
        "risk": "medium",
        "note": "Classic ASP Response.Write needs encoding",
        "target": "Razor with automatic encoding",
        "multiplier": 1.2,
    },
    "request_form": {
        "pattern": r'Request\.Form|Request\.QueryString|Request\(',
        "risk": "high",
        "note": "Unvalidated input - potential security risk",
        "target": "Model binding with validation",
        "multiplier": 1.3,
        "security": True,
        "owasp": "A03",
    },
    "server_createobject": {
        "pattern": r'Server\.CreateObject',
        "risk": "high",
        "note": "COM object creation needs .NET equivalent",
        "target": ".NET libraries or NuGet packages",
        "multiplier": 1.4,
    },
    "adodb": {
        "pattern": r'ADODB\.|Recordset|Connection\.Open',
        "risk": "high",
        "note": "ADO Classic needs conversion to ADO.NET or EF",
        "target": "Entity Framework Core",
        "multiplier": 1.5,
        "security": True,
        "owasp": "A03",
    },
    "include_file": {
        "pattern": r'<!--\s*#include\s+(file|virtual)',
        "risk": "medium",
        "note": "Include files need conversion to partial views",
        "target": "Razor partial views or components",
        "multiplier": 1.2,
    },
}


# ============================================================================
# DOTNET ANALYZER SERVICE
# ============================================================================

class DotNetAnalyzerService:
    """
    Specialized analyzer for .NET legacy code.
    
    Analyzes:
    - ASP.NET WebForms (.aspx, .ascx, .master)
    - WCF Services (.svc)
    - ASP Classic (.asp)
    - Code-behind files (.aspx.cs, .aspx.vb)
    """

    # File extensions to analyze
    WEBFORMS_EXTENSIONS = {".aspx", ".ascx", ".master"}
    CODE_BEHIND_EXTENSIONS = {".aspx.cs", ".aspx.vb", ".ascx.cs", ".ascx.vb"}
    WCF_EXTENSIONS = {".svc"}
    ASP_CLASSIC_EXTENSIONS = {".asp"}
    CSHARP_EXTENSIONS = {".cs"}
    VB_EXTENSIONS = {".vb"}

    # Directories to skip
    SKIP_DIRS = {"bin", "obj", "packages", ".git", "node_modules"}

    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
        self.result = DotNetAnalysisResult()

    async def analyze(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> DotNetAnalysisResult:
        """
        Perform complete .NET analysis.
        
        Args:
            analysis: Parent MigrationAnalysis record
            repo_path: Path to repository
            
        Returns:
            DotNetAnalysisResult with all findings
        """
        logger.info(f"Starting .NET analysis for {repo_path}")

        # Phase 1: Scan for WebForms pages
        await self._analyze_webforms(analysis, repo_path)

        # Phase 2: Scan for WCF services
        await self._analyze_wcf_services(analysis, repo_path)

        # Phase 3: Scan for ASP Classic
        await self._analyze_asp_classic(analysis, repo_path)

        # Phase 4: Detect legacy patterns across all files
        await self._detect_legacy_patterns(analysis, repo_path)

        # Phase 5: Calculate complexity and difficulty
        self._calculate_metrics()

        logger.info(
            f".NET analysis complete: {len(self.result.webforms_pages)} pages, "
            f"{len(self.result.wcf_services)} WCF services, "
            f"{len(self.result.legacy_patterns)} patterns"
        )

        return self.result

    async def _analyze_webforms(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze ASP.NET WebForms pages"""
        logger.info("Analyzing WebForms pages...")

        for ext in self.WEBFORMS_EXTENSIONS:
            for file_path in repo_path.rglob(f"*{ext}"):
                if self._should_skip(file_path):
                    continue

                page = await self._parse_webforms_page(file_path, repo_path)
                if page:
                    self.result.webforms_pages.append(page)
                    self.result.total_aspx_files += 1

                    # Create module record
                    module = MigrationModule(
                        analysis_id=analysis.id,
                        name=page.page_name,
                        module_type="webforms_page" if ext == ".aspx" else "user_control",
                        stack_type="aspnet_webforms",
                        file_path=str(file_path.relative_to(repo_path)),
                        loc=page.loc + page.code_behind_loc,
                        cyclomatic_complexity=page.complexity,
                        migration_difficulty=self._assess_page_difficulty(page),
                        migration_target="Blazor component",
                        legacy_patterns=[p.pattern_name for p in self.result.legacy_patterns if p.file_path == str(file_path)],
                    )
                    self.db.add(module)

        # Track user controls and master pages
        self.result.user_controls = [
            p.page_name for p in self.result.webforms_pages
            if p.file_path.endswith(".ascx")
        ]
        self.result.master_pages = [
            p.page_name for p in self.result.webforms_pages
            if p.file_path.endswith(".master")
        ]

        await self.db.commit()

    async def _parse_webforms_page(
        self,
        file_path: Path,
        repo_path: Path
    ) -> Optional[WebFormsPage]:
        """Parse a WebForms page and extract metadata"""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return None

        page = WebFormsPage(
            file_path=str(file_path.relative_to(repo_path)),
            page_name=file_path.stem,
            loc=len([l for l in content.splitlines() if l.strip()]),
        )

        # Extract page directive info
        page_directive = re.search(r'<%@\s*Page[^%]*%>', content, re.IGNORECASE)
        if page_directive:
            directive = page_directive.group()
            
            # Code behind
            cb_match = re.search(r'CodeBehind\s*=\s*["\']([^"\']+)["\']', directive)
            if cb_match:
                page.code_behind = cb_match.group(1)
                cb_path = file_path.parent / cb_match.group(1)
                if cb_path.exists():
                    try:
                        cb_content = cb_path.read_text(encoding="utf-8", errors="ignore")
                        page.code_behind_loc = len([l for l in cb_content.splitlines() if l.strip()])
                        self.result.total_code_behind_files += 1
                    except Exception:
                        pass

            # Master page
            master_match = re.search(r'MasterPageFile\s*=\s*["\']([^"\']+)["\']', directive)
            if master_match:
                page.master_page = master_match.group(1)

        # Detect ViewState usage
        if re.search(r'EnableViewState\s*=\s*["\']?true|ViewState\[', content, re.IGNORECASE):
            page.viewstate_usage = True

        # Find server controls
        controls = re.findall(r'<asp:(\w+)', content)
        page.controls = list(set(controls))

        # Find postback handlers
        handlers = re.findall(r'On(\w+)\s*=\s*["\'](\w+)["\']', content)
        page.postback_handlers = [h[1] for h in handlers]

        # Find data bindings
        bindings = re.findall(r'<%#\s*([^%]+)\s*%>', content)
        page.data_bindings = bindings

        return page

    async def _analyze_wcf_services(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze WCF services"""
        logger.info("Analyzing WCF services...")

        # Find .svc files
        for svc_path in repo_path.rglob("*.svc"):
            if self._should_skip(svc_path):
                continue

            service = await self._parse_wcf_service(svc_path, repo_path)
            if service:
                self.result.wcf_services.append(service)
                self.result.total_wcf_services += 1

                # Create module record
                module = MigrationModule(
                    analysis_id=analysis.id,
                    name=service.service_name,
                    module_type="wcf_service",
                    stack_type="wcf",
                    file_path=str(svc_path.relative_to(repo_path)),
                    loc=service.loc,
                    cyclomatic_complexity=service.complexity,
                    migration_difficulty=self._assess_wcf_difficulty(service),
                    migration_target="gRPC service or REST API",
                    dependencies=service.contracts,
                )
                self.db.add(module)

        # Also scan for ServiceContract in .cs files
        for cs_path in repo_path.rglob("*.cs"):
            if self._should_skip(cs_path):
                continue

            try:
                content = cs_path.read_text(encoding="utf-8", errors="ignore")
                if "[ServiceContract]" in content:
                    # Parse as potential WCF contract
                    service = self._parse_wcf_contract(cs_path, content, repo_path)
                    if service and service.service_name not in [s.service_name for s in self.result.wcf_services]:
                        self.result.wcf_services.append(service)
            except Exception:
                pass

        await self.db.commit()

    async def _parse_wcf_service(
        self,
        svc_path: Path,
        repo_path: Path
    ) -> Optional[WCFService]:
        """Parse a WCF .svc file"""
        try:
            content = svc_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        service = WCFService(
            file_path=str(svc_path.relative_to(repo_path)),
            service_name=svc_path.stem,
        )

        # Extract service directive
        service_match = re.search(r'Service\s*=\s*["\']([^"\']+)["\']', content)
        if service_match:
            service.service_name = service_match.group(1).split(".")[-1]

        # Look for associated .cs file
        cs_file = svc_path.with_suffix(".svc.cs")
        if not cs_file.exists():
            cs_file = svc_path.parent / f"{svc_path.stem}.cs"

        if cs_file.exists():
            try:
                cs_content = cs_file.read_text(encoding="utf-8", errors="ignore")
                service.loc = len([l for l in cs_content.splitlines() if l.strip()])
                
                # Extract contracts and operations
                service.contracts = re.findall(r'\[ServiceContract[^\]]*\]\s*(?:public\s+)?interface\s+(\w+)', cs_content)
                service.operations = re.findall(r'\[OperationContract[^\]]*\]\s*[^;]+\s+(\w+)\s*\(', cs_content)
                service.data_contracts = re.findall(r'\[DataContract[^\]]*\]\s*(?:public\s+)?class\s+(\w+)', cs_content)
            except Exception:
                pass

        return service

    def _parse_wcf_contract(
        self,
        cs_path: Path,
        content: str,
        repo_path: Path
    ) -> Optional[WCFService]:
        """Parse WCF contract from C# file"""
        service = WCFService(
            file_path=str(cs_path.relative_to(repo_path)),
            service_name=cs_path.stem,
            loc=len([l for l in content.splitlines() if l.strip()]),
        )

        service.contracts = re.findall(r'\[ServiceContract[^\]]*\]\s*(?:public\s+)?interface\s+(\w+)', content)
        service.operations = re.findall(r'\[OperationContract[^\]]*\]\s*[^;]+\s+(\w+)\s*\(', content)
        service.data_contracts = re.findall(r'\[DataContract[^\]]*\]\s*(?:public\s+)?class\s+(\w+)', content)

        if service.contracts or service.operations:
            return service
        return None

    async def _analyze_asp_classic(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze ASP Classic files"""
        logger.info("Analyzing ASP Classic files...")

        for asp_path in repo_path.rglob("*.asp"):
            if self._should_skip(asp_path):
                continue

            try:
                content = asp_path.read_text(encoding="utf-8", errors="ignore")
                loc = len([l for l in content.splitlines() if l.strip()])

                # Create module record
                module = MigrationModule(
                    analysis_id=analysis.id,
                    name=asp_path.stem,
                    module_type="asp_classic",
                    stack_type="asp_classic",
                    file_path=str(asp_path.relative_to(repo_path)),
                    loc=loc,
                    migration_difficulty="hard",  # ASP Classic is always hard
                    migration_target="Razor Page or Blazor",
                )
                self.db.add(module)

                # Detect ASP Classic patterns
                for pattern_name, pattern_def in ASP_CLASSIC_PATTERNS.items():
                    matches = list(re.finditer(pattern_def["pattern"], content, re.IGNORECASE))
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        self.result.legacy_patterns.append(LegacyPatternMatch(
                            pattern_name=pattern_name,
                            pattern_category="asp_classic",
                            file_path=str(asp_path.relative_to(repo_path)),
                            line_number=line_num,
                            code_snippet=match.group()[:100],
                            risk_level=pattern_def["risk"],
                            migration_note=pattern_def["note"],
                            migration_target=pattern_def["target"],
                            fp_multiplier=pattern_def.get("multiplier", 1.0),
                            is_security_issue=pattern_def.get("security", False),
                            owasp_category=pattern_def.get("owasp"),
                        ))

            except Exception as e:
                logger.warning(f"Failed to analyze {asp_path}: {e}")

        await self.db.commit()

    async def _detect_legacy_patterns(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Detect legacy patterns across all .NET files"""
        logger.info("Detecting legacy patterns...")

        # Scan WebForms patterns
        all_patterns = {
            **{f"webforms_{k}": {**v, "category": "aspnet_webforms"} for k, v in WEBFORMS_PATTERNS.items()},
            **{f"wcf_{k}": {**v, "category": "wcf"} for k, v in WCF_PATTERNS.items()},
        }

        extensions = [".aspx", ".ascx", ".master", ".cs", ".vb", ".svc"]

        for ext in extensions:
            for file_path in repo_path.rglob(f"*{ext}"):
                if self._should_skip(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                for pattern_name, pattern_def in all_patterns.items():
                    matches = list(re.finditer(pattern_def["pattern"], content, re.IGNORECASE))
                    
                    for match in matches[:5]:  # Limit matches per pattern per file
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Create pattern match
                        pattern_match = LegacyPatternMatch(
                            pattern_name=pattern_name,
                            pattern_category=pattern_def["category"],
                            file_path=str(file_path.relative_to(repo_path)),
                            line_number=line_num,
                            code_snippet=match.group()[:100],
                            risk_level=pattern_def["risk"],
                            migration_note=pattern_def["note"],
                            migration_target=pattern_def["target"],
                            fp_multiplier=pattern_def.get("multiplier", 1.0),
                            is_security_issue=pattern_def.get("security", False),
                            owasp_category=pattern_def.get("owasp"),
                        )
                        self.result.legacy_patterns.append(pattern_match)

                        # Store in database
                        db_pattern = LegacyPattern(
                            analysis_id=analysis.id,
                            pattern_name=pattern_name,
                            pattern_category=pattern_def["category"],
                            file_path=str(file_path.relative_to(repo_path)),
                            line_number=line_num,
                            code_snippet=match.group()[:200],
                            risk_level=pattern_def["risk"],
                            fp_multiplier=pattern_def.get("multiplier", 1.0),
                            migration_note=pattern_def["note"],
                            migration_target=pattern_def["target"],
                            is_security_issue=pattern_def.get("security", False),
                            owasp_category=pattern_def.get("owasp"),
                        )
                        self.db.add(db_pattern)

        await self.db.commit()

    def _calculate_metrics(self) -> None:
        """Calculate overall metrics and difficulty"""
        # Total LOC
        self.result.total_loc = sum(
            p.loc + p.code_behind_loc for p in self.result.webforms_pages
        ) + sum(s.loc for s in self.result.wcf_services)

        # Average complexity
        complexities = [p.complexity for p in self.result.webforms_pages if p.complexity > 0]
        complexities += [s.complexity for s in self.result.wcf_services if s.complexity > 0]
        if complexities:
            self.result.avg_complexity = sum(complexities) / len(complexities)

        # Migration difficulty assessment
        high_risk_patterns = sum(1 for p in self.result.legacy_patterns if p.risk_level in ["high", "critical"])
        security_issues = sum(1 for p in self.result.legacy_patterns if p.is_security_issue)

        if high_risk_patterns > 50 or security_issues > 20 or len(self.result.wcf_services) > 10:
            self.result.migration_difficulty = "complex"
        elif high_risk_patterns > 20 or security_issues > 10 or len(self.result.webforms_pages) > 50:
            self.result.migration_difficulty = "hard"
        elif high_risk_patterns > 5 or len(self.result.webforms_pages) > 20:
            self.result.migration_difficulty = "medium"
        else:
            self.result.migration_difficulty = "easy"

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        return any(skip in file_path.parts for skip in self.SKIP_DIRS)

    def _assess_page_difficulty(self, page: WebFormsPage) -> str:
        """Assess migration difficulty for a single page"""
        score = 0
        
        if page.viewstate_usage:
            score += 2
        if len(page.postback_handlers) > 5:
            score += 2
        if len(page.controls) > 10:
            score += 2
        if page.code_behind_loc > 500:
            score += 2
        if any(c in ["GridView", "DataGrid", "Repeater"] for c in page.controls):
            score += 3

        if score >= 7:
            return "complex"
        elif score >= 4:
            return "hard"
        elif score >= 2:
            return "medium"
        return "easy"

    def _assess_wcf_difficulty(self, service: WCFService) -> str:
        """Assess migration difficulty for a WCF service"""
        if "duplex" in str(service.bindings).lower():
            return "complex"
        if len(service.operations) > 20:
            return "hard"
        if len(service.operations) > 10:
            return "medium"
        return "easy"


def get_dotnet_analyzer_service(db: AsyncSession) -> DotNetAnalyzerService:
    """Factory function to create DotNetAnalyzerService instance"""
    return DotNetAnalyzerService(db)
