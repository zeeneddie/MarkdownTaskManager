"""
MigrationAnalyzer Service - Miguel Orchestrator

Week 65: MigrationAnalyzer Multi-Agent System
Orchestrates legacy code and database migration analysis using specialized agents.

Workflow Phases:
1. DETECTION - Scan repo, identify stacks
2. STACK_ANALYSIS - Run relevant stack analyzers (conditional)
3. DB_ANALYSIS - Analyze database schemas (if detected)
4. CROSS_CUTTING - Security, FP estimation, architecture analysis
5. OUTPUT - Generate documentation and BROWN_PAPER input

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.migration_analysis import (
    MigrationAnalysis,
    MigrationModule,
    MigrationDBSchema,
    LegacyPattern,
    DBCompatibilityIssue,
    MigrationRecommendation,
    FPBreakdown,
    RiskAssessment
)
from app.services.stack_detection_service import (
    StackDetectionService,
    get_stack_detection_service,
    ScanResult,
    StackDetection,
    STACK_DEFINITIONS
)
from app.services.dotnet_analyzer_service import (
    DotNetAnalyzerService,
    get_dotnet_analyzer_service,
    DotNetAnalysisResult
)
from app.services.frontend_analyzer_service import (
    FrontendAnalyzerService,
    get_frontend_analyzer_service,
    FrontendAnalysisResult
)
from app.services.php_analyzer_service import (
    PHPAnalyzerService,
    get_php_analyzer_service,
    PHPAnalysisResult
)
from app.services.database_analyzer_service import (
    DatabaseAnalyzerService,
    get_database_analyzer_service,
    DatabaseAnalysisResult
)

logger = logging.getLogger(__name__)


class AnalysisPhase(str, Enum):
    """Analysis workflow phases"""
    PENDING = "pending"
    DETECTION = "detection"
    STACK_ANALYSIS = "stack_analysis"
    DB_ANALYSIS = "db_analysis"
    CROSS_CUTTING = "cross_cutting"
    OUTPUT = "output"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """Analysis status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Stack detection patterns
STACK_PATTERNS: Dict[str, Dict[str, Any]] = {
    # .NET stacks
    "aspnet_webforms": {
        "extensions": [".aspx", ".aspx.cs", ".aspx.vb", ".ascx", ".master"],
        "patterns": ["ViewState", "runat=\"server\"", "Page_Load", "System.Web.UI"],
        "analyzer": "DotNetAnalyzer"
    },
    "asp_classic": {
        "extensions": [".asp"],
        "patterns": ["<%", "Response.Write", "Request.Form", "Server.CreateObject"],
        "analyzer": "DotNetAnalyzer"
    },
    "aspnet_mvc": {
        "extensions": [".cshtml", ".vbhtml"],
        "patterns": ["@Html.", "@Model", "ActionResult", "Controller"],
        "analyzer": "DotNetAnalyzer"
    },
    "wcf": {
        "extensions": [".svc"],
        "patterns": ["ServiceContract", "OperationContract", "DataContract"],
        "analyzer": "DotNetAnalyzer"
    },
    # Frontend stacks
    "angularjs": {
        "extensions": [".js", ".html"],
        "patterns": ["ng-app", "ng-controller", "ng-model", "$scope", "angular.module"],
        "analyzer": "FrontendAnalyzer"
    },
    "angular": {
        "extensions": [".ts", ".html"],
        "patterns": ["@Component", "@NgModule", "@Injectable", "import.*@angular"],
        "analyzer": "FrontendAnalyzer"
    },
    "vue2": {
        "extensions": [".vue", ".js"],
        "patterns": ["new Vue", "Vue.component", "Vue.extend", "this.$"],
        "analyzer": "FrontendAnalyzer"
    },
    "react_class": {
        "extensions": [".jsx", ".tsx", ".js"],
        "patterns": ["extends React.Component", "extends Component", "componentDidMount"],
        "analyzer": "FrontendAnalyzer"
    },
    "jquery": {
        "extensions": [".js", ".html"],
        "patterns": ["$(", "jQuery(", ".ajax(", ".click(", ".ready("],
        "analyzer": "FrontendAnalyzer"
    },
    # PHP stacks
    "php_legacy": {
        "extensions": [".php"],
        "patterns": ["mysql_", "ereg(", "split(", "global $"],
        "analyzer": "PHPAnalyzer"
    },
    "laravel": {
        "extensions": [".php", ".blade.php"],
        "patterns": ["Illuminate\\", "artisan", "Route::", "Eloquent"],
        "analyzer": "PHPAnalyzer"
    },
    # Java stacks
    "java_legacy": {
        "extensions": [".java", ".jsp"],
        "patterns": ["javax.servlet", "HttpServlet", "doGet", "doPost"],
        "analyzer": "JavaAnalyzer"
    },
    "spring": {
        "extensions": [".java"],
        "patterns": ["@SpringBootApplication", "@Controller", "@Service", "@Repository"],
        "analyzer": "JavaAnalyzer"
    },
    "struts": {
        "extensions": [".java", ".xml"],
        "patterns": ["struts-config.xml", "ActionForm", "ActionMapping"],
        "analyzer": "JavaAnalyzer"
    }
}

# Database detection patterns
DB_PATTERNS: Dict[str, Dict[str, Any]] = {
    "sqlserver": {
        "extensions": [".sql"],
        "patterns": ["NVARCHAR", "IDENTITY", "@@ROWCOUNT", "sp_", "DECLARE @"],
        "connection_patterns": ["Server=", "Data Source=", "SqlConnection"]
    },
    "oracle": {
        "extensions": [".sql", ".pls", ".pck"],
        "patterns": ["VARCHAR2", "NUMBER(", "DBMS_", "PL/SQL", "SYSDATE"],
        "connection_patterns": ["OracleConnection", "Data Source=", "ODP.NET"]
    },
    "mysql": {
        "extensions": [".sql"],
        "patterns": ["AUTO_INCREMENT", "ENGINE=InnoDB", "ENUM(", "mysql_"],
        "connection_patterns": ["MySqlConnection", "server=", "mysql://"]
    }
}


class MigrationAnalyzerService:
    """
    Miguel Orchestrator - Coordinates multi-agent migration analysis

    This service implements the Migration Analyzer workflow:
    1. Detection phase - Identify source stacks and database types
    2. Stack analysis - Run relevant analyzers (conditional activation)
    3. Database analysis - Analyze schemas if DB detected
    4. Cross-cutting - Security, FP estimation, architecture
    5. Output - Generate documentation and BROWN_PAPER input
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._current_analysis: Optional[MigrationAnalysis] = None

    async def create_analysis(
        self,
        repo_path: str,
        target_stack: Optional[str] = None,
        target_db: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> MigrationAnalysis:
        """
        Create a new migration analysis session

        Args:
            repo_path: Path to the repository to analyze
            target_stack: Target technology stack (e.g., 'dotnet8', 'python')
            target_db: Target database (e.g., 'postgresql')
            project_id: Optional project ID to link analysis to

        Returns:
            MigrationAnalysis: Created analysis record
        """
        # Extract repo name from path
        repo_name = Path(repo_path).name

        analysis = MigrationAnalysis(
            repo_path=repo_path,
            repo_name=repo_name,
            target_stack=target_stack,
            target_db=target_db or "postgresql",
            project_id=project_id,
            status=AnalysisStatus.PENDING,
            current_phase=AnalysisPhase.PENDING,
            progress_percent=0
        )

        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)

        logger.info(f"Created analysis {analysis.id} for {repo_path}")
        return analysis

    async def get_analysis(self, analysis_id: UUID) -> Optional[MigrationAnalysis]:
        """Get an analysis by ID with all related data"""
        result = await self.db.execute(
            select(MigrationAnalysis)
            .options(
                selectinload(MigrationAnalysis.modules),
                selectinload(MigrationAnalysis.patterns),
                selectinload(MigrationAnalysis.recommendations),
                selectinload(MigrationAnalysis.risk_assessments)
            )
            .where(MigrationAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def list_analyses(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MigrationAnalysis]:
        """List analyses with optional filtering"""
        query = select(MigrationAnalysis).order_by(MigrationAnalysis.created_at.desc())

        if status:
            query = query.where(MigrationAnalysis.status == status)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def run_analysis(self, analysis_id: UUID) -> MigrationAnalysis:
        """
        Execute the full analysis workflow

        Phases:
        1. Detection (0-20%) - Scan files, detect stacks
        2. Stack Analysis (20-50%) - Run relevant analyzers
        3. DB Analysis (50-70%) - Analyze database schemas
        4. Cross-Cutting (70-90%) - Security, FP, architecture
        5. Output (90-100%) - Generate reports

        Args:
            analysis_id: UUID of the analysis to run

        Returns:
            Updated MigrationAnalysis with results
        """
        analysis = await self.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        self._current_analysis = analysis

        try:
            # Update status to running
            analysis.status = AnalysisStatus.RUNNING
            analysis.started_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Phase 1: Detection
            await self._run_detection_phase(analysis)

            # Phase 2: Stack Analysis (conditional)
            await self._run_stack_analysis_phase(analysis)

            # Phase 3: Database Analysis (if DB detected)
            await self._run_db_analysis_phase(analysis)

            # Phase 4: Cross-Cutting Analysis
            await self._run_cross_cutting_phase(analysis)

            # Phase 5: Output Generation
            await self._run_output_phase(analysis)

            # Mark as completed
            analysis.status = AnalysisStatus.COMPLETED
            analysis.current_phase = AnalysisPhase.COMPLETED
            analysis.progress_percent = 100
            analysis.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.info(f"Analysis {analysis_id} completed successfully")

        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {e}")
            analysis.status = AnalysisStatus.FAILED
            analysis.current_phase = AnalysisPhase.FAILED
            analysis.error_message = str(e)
            await self.db.commit()
            raise

        return analysis

    async def _run_detection_phase(self, analysis: MigrationAnalysis) -> None:
        """
        Phase 1: Detection (using StackDetectionService)
        - Scan repository for files using comprehensive stack detection
        - Detect source stacks based on patterns, configs, and confidence scoring
        - Detect database types from connection strings and SQL patterns
        - Build file inventory with extension breakdown
        """
        analysis.current_phase = AnalysisPhase.DETECTION
        analysis.progress_percent = 5
        await self.db.commit()

        logger.info(f"Starting detection phase for {analysis.repo_path}")

        repo_path = Path(analysis.repo_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        # Use StackDetectionService for comprehensive scanning
        try:
            stack_service = get_stack_detection_service(str(repo_path))
            scan_result: ScanResult = stack_service.scan()
        except Exception as e:
            logger.warning(f"StackDetectionService failed, falling back: {e}")
            # Fallback to basic scanning
            file_inventory = await self._scan_files(repo_path)
            analysis.file_inventory = file_inventory
            analysis.total_files = file_inventory.get("total_files", 0)
            analysis.total_loc = file_inventory.get("total_loc", 0)
            detected_stacks = await self._detect_stacks(repo_path, file_inventory)
            if detected_stacks:
                primary_stack = max(detected_stacks.items(), key=lambda x: x[1]["matches"])[0]
                analysis.source_stack = primary_stack
                analysis.secondary_stacks = [s for s in detected_stacks.keys() if s != primary_stack]
            analysis.progress_percent = 20
            await self.db.commit()
            return

        # Map scan results to analysis
        analysis.total_files = scan_result.total_files
        analysis.total_loc = scan_result.total_loc
        analysis.file_inventory = {
            "total_files": scan_result.total_files,
            "total_loc": scan_result.total_loc,
            "by_extension": scan_result.file_inventory,
            "errors": scan_result.errors
        }

        analysis.progress_percent = 10
        await self.db.commit()

        # Map detected stacks
        analysis.source_stack = scan_result.primary_stack
        analysis.secondary_stacks = scan_result.secondary_stacks

        # Store detailed stack detections for later phases
        if scan_result.stack_detections:
            analysis.file_inventory["stack_detections"] = {
                name: {
                    "confidence": det.confidence,
                    "file_count": det.file_count,
                    "pattern_matches": det.pattern_matches,
                    "config_files": det.config_files
                }
                for name, det in scan_result.stack_detections.items()
            }

        analysis.progress_percent = 15
        await self.db.commit()

        # Map database detection
        if scan_result.database_type:
            analysis.db_type = scan_result.database_type

        # Store complexity metrics if available
        if scan_result.complexity:
            analysis.file_inventory["complexity"] = {
                "avg_cyclomatic": scan_result.complexity.avg_cyclomatic,
                "max_cyclomatic": scan_result.complexity.max_cyclomatic,
                "total_functions": scan_result.complexity.total_functions,
                "high_complexity_count": scan_result.complexity.high_complexity_count
            }

        analysis.progress_percent = 20
        await self.db.commit()

        logger.info(
            f"Detection complete: source={analysis.source_stack}, "
            f"secondary={analysis.secondary_stacks}, db={analysis.db_type}, "
            f"files={analysis.total_files}, loc={analysis.total_loc}"
        )

    async def _run_stack_analysis_phase(self, analysis: MigrationAnalysis) -> None:
        """
        Phase 2: Stack Analysis (Conditional)
        - Activate relevant stack analyzers based on detected stacks
        - Run complexity analysis with Lizard
        - Detect legacy patterns
        """
        analysis.current_phase = AnalysisPhase.STACK_ANALYSIS
        analysis.progress_percent = 25
        await self.db.commit()

        logger.info(f"Starting stack analysis for {analysis.source_stack}")

        all_stacks = [analysis.source_stack] + (analysis.secondary_stacks or [])
        all_stacks = [s for s in all_stacks if s]  # Filter None

        # Determine which analyzers to run
        analyzers_to_run: Set[str] = set()
        for stack in all_stacks:
            if stack in STACK_PATTERNS:
                analyzers_to_run.add(STACK_PATTERNS[stack]["analyzer"])

        logger.info(f"Activating analyzers: {analyzers_to_run}")

        # Run each analyzer
        progress_per_analyzer = 25 / max(len(analyzers_to_run), 1)
        current_progress = 25

        for analyzer_name in analyzers_to_run:
            await self._run_stack_analyzer(analysis, analyzer_name)
            current_progress += progress_per_analyzer
            analysis.progress_percent = int(current_progress)
            await self.db.commit()

        # Calculate totals
        modules = await self._get_analysis_modules(analysis.id)
        analysis.total_modules = len(modules)

        # Build module inventory
        analysis.module_inventory = {
            "modules": [m.to_dict() for m in modules],
            "by_type": self._group_modules_by_type(modules),
            "by_stack": self._group_modules_by_stack(modules)
        }

        analysis.progress_percent = 50
        await self.db.commit()

        logger.info(f"Stack analysis complete: {len(modules)} modules detected")

    async def _run_db_analysis_phase(self, analysis: MigrationAnalysis) -> None:
        """
        Phase 3: Database Analysis
        - Analyze database schemas using DatabaseAnalyzerService
        - Detect stored procedures complexity
        - Identify compatibility issues
        """
        analysis.current_phase = AnalysisPhase.DB_ANALYSIS
        analysis.progress_percent = 55
        await self.db.commit()

        repo_path = Path(analysis.repo_path)

        # Check if there are SQL files to analyze
        sql_files = list(repo_path.rglob("*.sql"))
        if not sql_files and not analysis.db_type:
            logger.info("No SQL files or database detected, skipping DB analysis")
            analysis.progress_percent = 70
            await self.db.commit()
            return

        logger.info(f"Starting database analysis (detected type: {analysis.db_type})")

        # Use DatabaseAnalyzerService for comprehensive analysis
        db_analyzer = get_database_analyzer_service(self.db)
        db_result = await db_analyzer.analyze(analysis, repo_path)

        analysis.progress_percent = 60
        await self.db.commit()

        # Store analysis results
        if db_result:
            # Update analysis with database info
            if not analysis.db_type and db_result.source_database != "unknown":
                analysis.db_type = db_result.source_database

            # Store in module_inventory
            analysis.module_inventory = analysis.module_inventory or {}
            analysis.module_inventory["database_analysis"] = {
                "source_database": db_result.source_database,
                "source_version": db_result.source_version,
                "total_tables": db_result.total_tables,
                "total_procedures": db_result.total_procedures,
                "total_views": db_result.total_views,
                "total_sql_files": db_result.total_sql_files,
                "total_loc": db_result.total_loc,
                "legacy_patterns": len(db_result.legacy_patterns),
                "migration_difficulty": db_result.migration_difficulty,
                "estimated_conversion_hours": db_result.estimated_conversion_hours,
                "ora2pg_compatibility": db_result.ora2pg_compatibility,
            }

            # Create DB schema record for backwards compatibility
            db_schema = MigrationDBSchema(
                analysis_id=analysis.id,
                source_type=db_result.source_database,
                source_version=db_result.source_version,
                table_count=db_result.total_tables,
                stored_procedure_count=db_result.total_procedures,
            )
            self.db.add(db_schema)
            await self.db.commit()

            analysis.progress_percent = 65
            await self.db.commit()

            # Map difficulty to A-E scale for Ora2Pg compatibility
            difficulty_map = {
                "easy": "A",
                "medium": "B",
                "hard": "C",
                "complex": "D",
            }
            difficulty = difficulty_map.get(db_result.migration_difficulty, "C")
            estimated_days = db_result.estimated_conversion_hours / 8.0  # Convert hours to days

            analysis.db_table_count = db_result.total_tables
            analysis.db_sp_count = db_result.total_procedures
            analysis.db_migration_difficulty = difficulty
            analysis.db_estimated_days = estimated_days

            logger.info(
                f"DatabaseAnalyzer complete: {db_result.source_database}, "
                f"{db_result.total_tables} tables, {db_result.total_procedures} procedures, "
                f"difficulty={difficulty}, {db_result.estimated_conversion_hours:.1f} hours"
            )

        analysis.progress_percent = 70
        await self.db.commit()

    async def _run_cross_cutting_phase(self, analysis: MigrationAnalysis) -> None:
        """
        Phase 4: Cross-Cutting Analysis
        - Security scan (Quinn agent)
        - FP estimation (Eliza agent)
        - Dependency analysis (Felix agent)
        """
        analysis.current_phase = AnalysisPhase.CROSS_CUTTING
        analysis.progress_percent = 72
        await self.db.commit()

        logger.info("Starting cross-cutting analysis")

        # Security scan
        await self._run_security_scan(analysis)
        analysis.progress_percent = 78
        await self.db.commit()

        # FP estimation
        await self._run_fp_estimation(analysis)
        analysis.progress_percent = 84
        await self.db.commit()

        # Dependency analysis
        await self._run_dependency_analysis(analysis)
        analysis.progress_percent = 90
        await self.db.commit()

        logger.info("Cross-cutting analysis complete")

    async def _run_output_phase(self, analysis: MigrationAnalysis) -> None:
        """
        Phase 5: Output Generation
        - Generate recommendations
        - Build risk register
        - Aggregate summaries
        """
        analysis.current_phase = AnalysisPhase.OUTPUT
        analysis.progress_percent = 92
        await self.db.commit()

        logger.info("Starting output generation")

        # Generate recommendations
        await self._generate_recommendations(analysis)
        analysis.progress_percent = 95
        await self.db.commit()

        # Build risk summary
        risks = await self._get_analysis_risks(analysis.id)
        analysis.risk_summary = {
            "total_risks": len(risks),
            "by_category": self._group_risks_by_category(risks),
            "high_risk_count": sum(1 for r in risks if r.risk_score and r.risk_score >= 50)
        }

        # Build pattern summary
        patterns = await self._get_analysis_patterns(analysis.id)
        analysis.pattern_summary = {
            "total_patterns": len(patterns),
            "by_category": self._group_patterns_by_category(patterns),
            "security_issues": sum(1 for p in patterns if p.is_security_issue)
        }

        # Calculate overall scores
        analysis.complexity_score = await self._calculate_complexity_score(analysis)
        analysis.risk_score = await self._calculate_risk_score(analysis)

        analysis.progress_percent = 100
        await self.db.commit()

        logger.info("Output generation complete")

    # ========== Helper Methods ==========

    async def _scan_files(self, repo_path: Path) -> Dict[str, Any]:
        """Scan repository and build file inventory"""
        inventory = {
            "total_files": 0,
            "total_loc": 0,
            "by_extension": {},
            "by_directory": {}
        }

        ignore_dirs = {".git", "node_modules", "vendor", "bin", "obj", "packages", "__pycache__"}

        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                # Skip ignored directories
                if any(ignored in file_path.parts for ignored in ignore_dirs):
                    continue

                inventory["total_files"] += 1

                # Count by extension
                ext = file_path.suffix.lower()
                if ext not in inventory["by_extension"]:
                    inventory["by_extension"][ext] = {"count": 0, "loc": 0}
                inventory["by_extension"][ext]["count"] += 1

                # Count lines (for text files)
                try:
                    if ext in [".cs", ".vb", ".aspx", ".ascx", ".js", ".ts", ".jsx", ".tsx",
                               ".php", ".java", ".py", ".sql", ".html", ".css", ".vue"]:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            loc = sum(1 for line in f if line.strip())
                            inventory["total_loc"] += loc
                            inventory["by_extension"][ext]["loc"] += loc
                except Exception:
                    pass

        return inventory

    async def _detect_stacks(
        self,
        repo_path: Path,
        file_inventory: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Detect technology stacks based on file patterns"""
        detected = {}

        for stack_name, stack_info in STACK_PATTERNS.items():
            matches = 0

            # Check extensions
            for ext in stack_info["extensions"]:
                if ext in file_inventory.get("by_extension", {}):
                    matches += file_inventory["by_extension"][ext]["count"]

            # Check content patterns (sample files)
            if matches > 0:
                pattern_matches = await self._check_content_patterns(
                    repo_path,
                    stack_info["extensions"],
                    stack_info["patterns"]
                )
                matches += pattern_matches

            if matches > 0:
                detected[stack_name] = {
                    "matches": matches,
                    "analyzer": stack_info["analyzer"]
                }

        return detected

    async def _check_content_patterns(
        self,
        repo_path: Path,
        extensions: List[str],
        patterns: List[str]
    ) -> int:
        """Check file content for patterns (sample-based)"""
        matches = 0
        files_checked = 0
        max_files = 20  # Sample limit

        for ext in extensions:
            for file_path in repo_path.rglob(f"*{ext}"):
                if files_checked >= max_files:
                    break

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern in patterns:
                        if pattern.lower() in content.lower():
                            matches += 1
                    files_checked += 1
                except Exception:
                    continue

        return matches

    async def _detect_database(
        self,
        repo_path: Path,
        file_inventory: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Detect database type from SQL files and connection strings"""
        for db_type, db_info in DB_PATTERNS.items():
            # Check SQL file patterns
            sql_files = list(repo_path.rglob("*.sql"))[:10]  # Sample

            for sql_file in sql_files:
                try:
                    content = sql_file.read_text(encoding="utf-8", errors="ignore")
                    for pattern in db_info["patterns"]:
                        if pattern.lower() in content.lower():
                            return {"type": db_type, "version": None}
                except Exception:
                    continue

            # Check connection strings in config files
            config_files = list(repo_path.rglob("*.config")) + list(repo_path.rglob("appsettings*.json"))
            for config_file in config_files[:5]:
                try:
                    content = config_file.read_text(encoding="utf-8", errors="ignore")
                    for pattern in db_info.get("connection_patterns", []):
                        if pattern.lower() in content.lower():
                            return {"type": db_type, "version": None}
                except Exception:
                    continue

        return None

    async def _run_stack_analyzer(
        self,
        analysis: MigrationAnalysis,
        analyzer_name: str
    ) -> None:
        """Run a specific stack analyzer"""
        logger.info(f"Running {analyzer_name}")

        repo_path = Path(analysis.repo_path)

        # Use specialized analyzers where available
        if analyzer_name == "DotNetAnalyzer":
            # Use the specialized DotNetAnalyzerService
            dotnet_analyzer = get_dotnet_analyzer_service(self.db)
            result = await dotnet_analyzer.analyze(analysis, repo_path)

            # Store summary in analysis
            if result:
                analysis.module_inventory = analysis.module_inventory or {}
                analysis.module_inventory["dotnet_analysis"] = {
                    "webforms_pages": len(result.webforms_pages),
                    "wcf_services": len(result.wcf_services),
                    "user_controls": len(result.user_controls),
                    "master_pages": len(result.master_pages),
                    "legacy_patterns": len(result.legacy_patterns),
                    "migration_difficulty": result.migration_difficulty,
                    "total_loc": result.total_loc,
                    "avg_complexity": result.avg_complexity,
                }
                logger.info(
                    f"DotNetAnalyzer complete: {len(result.webforms_pages)} pages, "
                    f"{len(result.wcf_services)} WCF services, "
                    f"{len(result.legacy_patterns)} patterns"
                )
            return

        # Frontend Analyzer (AngularJS, Vue 2, React class, jQuery)
        if analyzer_name == "FrontendAnalyzer":
            frontend_analyzer = get_frontend_analyzer_service(self.db)
            result = await frontend_analyzer.analyze(analysis, repo_path)

            # Store summary in analysis
            if result:
                analysis.module_inventory = analysis.module_inventory or {}
                analysis.module_inventory["frontend_analysis"] = {
                    "angularjs_modules": len(result.angularjs_modules),
                    "vue_components": len(result.vue_components),
                    "react_components": len(result.react_components),
                    "jquery_usages": len(result.jquery_usages),
                    "legacy_patterns": len(result.legacy_patterns),
                    "primary_framework": result.primary_framework,
                    "migration_difficulty": result.migration_difficulty,
                    "total_loc": result.total_loc,
                    "total_js_files": result.total_js_files,
                    "total_ts_files": result.total_ts_files,
                    "total_vue_files": result.total_vue_files,
                    "total_jsx_files": result.total_jsx_files,
                }
                logger.info(
                    f"FrontendAnalyzer complete: {len(result.angularjs_modules)} AngularJS, "
                    f"{len(result.vue_components)} Vue, {len(result.react_components)} React, "
                    f"{len(result.jquery_usages)} jQuery files, "
                    f"primary: {result.primary_framework}"
                )
            return

        # PHP Analyzer (PHP 4/5, Laravel, Symfony, CodeIgniter)
        if analyzer_name == "PHPAnalyzer":
            php_analyzer = get_php_analyzer_service(self.db)
            result = await php_analyzer.analyze(analysis, repo_path)

            # Store summary in analysis
            if result:
                analysis.module_inventory = analysis.module_inventory or {}
                analysis.module_inventory["php_analysis"] = {
                    "php_classes": len(result.php_classes),
                    "php_functions": len(result.php_functions),
                    "laravel_components": len(result.laravel_components),
                    "symfony_components": len(result.symfony_components),
                    "legacy_patterns": len(result.legacy_patterns),
                    "framework_detected": result.framework_detected,
                    "php_version_detected": result.php_version_detected,
                    "migration_difficulty": result.migration_difficulty,
                    "total_loc": result.total_loc,
                    "total_php_files": result.total_php_files,
                    "security_issues_count": result.security_issues_count,
                }
                logger.info(
                    f"PHPAnalyzer complete: {len(result.php_classes)} classes, "
                    f"{len(result.laravel_components)} Laravel, {len(result.symfony_components)} Symfony, "
                    f"{len(result.legacy_patterns)} patterns, {result.security_issues_count} security issues"
                )
            return

        # Generic analyzer for other stacks
        if analyzer_name == "JavaAnalyzer":
            extensions = [".java", ".jsp"]
        else:
            return

        # Find and analyze files with generic approach
        for ext in extensions:
            for file_path in repo_path.rglob(f"*{ext}"):
                if any(ignored in str(file_path) for ignored in [".git", "node_modules", "vendor"]):
                    continue

                # Create module record
                module = await self._analyze_file_as_module(
                    analysis_id=analysis.id,
                    file_path=file_path,
                    stack_type=analysis.source_stack or "unknown"
                )

                if module:
                    # Detect patterns in this module
                    await self._detect_module_patterns(analysis.id, module)

    async def _analyze_file_as_module(
        self,
        analysis_id: UUID,
        file_path: Path,
        stack_type: str
    ) -> Optional[MigrationModule]:
        """Analyze a file and create a module record"""
        try:
            # Determine module type from file
            module_type = self._get_module_type(file_path)

            # Count lines
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            loc = sum(1 for line in content.splitlines() if line.strip())

            # Simple complexity estimation (more sophisticated analysis in Day 3-5)
            function_count = content.lower().count("function") + content.count("def ") + content.count("public ")

            module = MigrationModule(
                analysis_id=analysis_id,
                name=file_path.stem,
                module_type=module_type,
                stack_type=stack_type,
                file_path=str(file_path),
                file_count=1,
                loc=loc,
                function_count=function_count
            )

            self.db.add(module)
            await self.db.commit()
            await self.db.refresh(module)

            return module

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")
            return None

    def _get_module_type(self, file_path: Path) -> str:
        """Determine module type from file path and extension"""
        name_lower = file_path.name.lower()
        ext = file_path.suffix.lower()

        if "controller" in name_lower:
            return "controller"
        elif "service" in name_lower:
            return "service"
        elif "model" in name_lower or "entity" in name_lower:
            return "model"
        elif "repository" in name_lower or "dal" in name_lower:
            return "repository"
        elif ext in [".aspx", ".cshtml", ".html", ".vue", ".jsx"]:
            return "page"
        elif ext in [".ascx"]:
            return "component"
        elif ext == ".master":
            return "layout"
        else:
            return "module"

    async def _detect_module_patterns(
        self,
        analysis_id: UUID,
        module: MigrationModule
    ) -> None:
        """Detect legacy patterns in a module"""
        try:
            content = Path(module.file_path).read_text(encoding="utf-8", errors="ignore")

            # Check for common legacy patterns
            patterns_to_check = [
                ("viewstate", "ViewState", "aspnet_webforms", "high", "Consider Blazor state management"),
                ("code_behind", "CodeBehind=", "aspnet_webforms", "medium", "Migrate to Razor components"),
                ("inline_script", "<script.*runat", "aspnet_webforms", "medium", "Move to component scripts"),
                ("scope_usage", "$scope", "angularjs", "high", "Migrate to Angular/Vue 3"),
                ("ng_repeat", "ng-repeat", "angularjs", "medium", "Use *ngFor or v-for"),
                ("jquery_ajax", "$.ajax", "jquery", "low", "Use fetch API"),
                ("sql_injection", "+ sql", "security", "critical", "Use parameterized queries"),
            ]

            for pattern_name, search_pattern, category, risk, note in patterns_to_check:
                if search_pattern.lower() in content.lower():
                    pattern = LegacyPattern(
                        analysis_id=analysis_id,
                        module_id=module.id,
                        pattern_name=pattern_name,
                        pattern_category=category,
                        file_path=module.file_path,
                        risk_level=risk,
                        migration_note=note,
                        is_security_issue=(category == "security" or risk == "critical")
                    )
                    self.db.add(pattern)

            await self.db.commit()

        except Exception as e:
            logger.warning(f"Failed to detect patterns in {module.file_path}: {e}")

    async def _analyze_sql_files(
        self,
        db_schema: MigrationDBSchema,
        sql_files: List[Path]
    ) -> None:
        """Analyze SQL files to extract schema information"""
        tables = []
        stored_procedures = []
        total_sp_loc = 0

        for sql_file in sql_files:
            try:
                content = sql_file.read_text(encoding="utf-8", errors="ignore")

                # Simple pattern matching (more sophisticated in Week 66)
                # Count CREATE TABLE
                table_matches = content.upper().count("CREATE TABLE")
                for _ in range(table_matches):
                    tables.append({"file": str(sql_file), "name": "detected"})

                # Count stored procedures
                sp_matches = content.upper().count("CREATE PROCEDURE") + content.upper().count("CREATE PROC")
                for _ in range(sp_matches):
                    stored_procedures.append({"file": str(sql_file), "name": "detected"})
                    total_sp_loc += len(content.splitlines())

            except Exception as e:
                logger.warning(f"Failed to analyze SQL file {sql_file}: {e}")

        db_schema.table_count = len(tables)
        db_schema.stored_procedure_count = len(stored_procedures)
        db_schema.tables = tables
        db_schema.stored_procedures = stored_procedures
        db_schema.sp_total_loc = total_sp_loc

        await self.db.commit()

    async def _detect_db_compatibility_issues(
        self,
        db_schema: MigrationDBSchema,
        target_db: str
    ) -> None:
        """Detect database compatibility issues"""
        issues = []

        # Common SQL Server → PostgreSQL issues
        if db_schema.source_type == "sqlserver" and target_db == "postgresql":
            common_issues = [
                ("datatype", "NVARCHAR", "VARCHAR", True, "low"),
                ("datatype", "DATETIME", "TIMESTAMP", True, "low"),
                ("datatype", "MONEY", "DECIMAL", True, "low"),
                ("feature", "IDENTITY", "SERIAL/GENERATED", True, "low"),
                ("feature", "TOP N", "LIMIT N", True, "low"),
                ("procedural", "T-SQL", "PL/pgSQL", False, "high"),
            ]

            for issue_type, source, target, auto, effort in common_issues:
                issue = DBCompatibilityIssue(
                    schema_id=db_schema.id,
                    issue_type=issue_type,
                    source_feature=source,
                    target_equivalent=target,
                    auto_convertible=auto,
                    conversion_effort=effort
                )
                self.db.add(issue)
                issues.append(issue)

        await self.db.commit()

    async def _calculate_db_migration_difficulty(
        self,
        db_schema: MigrationDBSchema
    ) -> tuple[str, float]:
        """Calculate DB migration difficulty (A-E scale like Ora2Pg)"""
        score = 0

        # Factors that increase difficulty
        if db_schema.table_count:
            score += min(db_schema.table_count / 10, 5)

        if db_schema.stored_procedure_count:
            score += min(db_schema.stored_procedure_count / 5, 10)

        if db_schema.sp_total_loc and db_schema.sp_total_loc > 1000:
            score += 5

        # Map score to difficulty
        if score < 5:
            difficulty = "A"
            estimated_days = 1
        elif score < 10:
            difficulty = "B"
            estimated_days = 5
        elif score < 15:
            difficulty = "C"
            estimated_days = 15
        elif score < 20:
            difficulty = "D"
            estimated_days = 30
        else:
            difficulty = "E"
            estimated_days = 60

        db_schema.migration_difficulty = difficulty
        db_schema.estimated_man_days = estimated_days

        return difficulty, estimated_days

    async def _run_security_scan(self, analysis: MigrationAnalysis) -> None:
        """Run security scan (Quinn agent simulation)"""
        # Security patterns will be fully implemented in Week 67
        logger.info("Running security scan (basic)")

        patterns = await self._get_analysis_patterns(analysis.id)
        security_patterns = [p for p in patterns if p.is_security_issue]

        for pattern in security_patterns:
            # Create risk assessment for security issues
            risk = RiskAssessment(
                analysis_id=analysis.id,
                risk_id=f"SEC-{len(await self._get_analysis_risks(analysis.id)) + 1:03d}",
                title=f"Security Issue: {pattern.pattern_name}",
                description=pattern.migration_note,
                category="security",
                probability=4,
                impact=5,
                detectability=2,
                risk_score=40,  # 4 * 5 * 2
                identified_by="quinn"
            )
            self.db.add(risk)

        await self.db.commit()

    async def _run_fp_estimation(self, analysis: MigrationAnalysis) -> None:
        """Run Function Point estimation (Eliza agent simulation)"""
        logger.info("Running FP estimation (basic)")

        modules = await self._get_analysis_modules(analysis.id)
        total_fp = 0

        for module in modules:
            # Basic FP estimation based on module type and LOC
            base_fp = self._estimate_module_fp(module)

            # Apply legacy multiplier
            legacy_multiplier = 1.0 + (module.pattern_count or 0) * 0.1
            adjusted_fp = base_fp * legacy_multiplier

            # Create FP breakdown
            fp_breakdown = FPBreakdown(
                analysis_id=analysis.id,
                module_id=module.id,
                fp_type="EI" if module.module_type in ["controller", "service"] else "ILF",
                fp_name=module.name,
                complexity_rating="average",
                unadjusted_fp=base_fp,
                legacy_multiplier=legacy_multiplier,
                adjusted_fp=adjusted_fp,
                source_file=module.file_path,
                detected_by="eliza"
            )
            self.db.add(fp_breakdown)

            total_fp += adjusted_fp
            module.estimated_fp = int(adjusted_fp)

        analysis.estimated_fp = int(total_fp)
        await self.db.commit()

    def _estimate_module_fp(self, module: MigrationModule) -> int:
        """Estimate FP for a module based on type and LOC"""
        # Simple estimation based on IFPUG guidelines
        type_multipliers = {
            "controller": 5,
            "service": 7,
            "model": 3,
            "repository": 4,
            "page": 6,
            "component": 4,
            "layout": 2,
            "module": 4
        }

        base = type_multipliers.get(module.module_type, 4)
        loc_factor = (module.loc or 0) / 100

        return int(base + loc_factor)

    async def _run_dependency_analysis(self, analysis: MigrationAnalysis) -> None:
        """Run dependency analysis (Felix agent simulation)"""
        logger.info("Running dependency analysis (basic)")

        # Build simple dependency graph
        modules = await self._get_analysis_modules(analysis.id)

        dependency_graph = {
            "nodes": [{"id": str(m.id), "name": m.name, "type": m.module_type} for m in modules],
            "edges": []  # Full implementation in Week 68
        }

        analysis.dependency_graph = dependency_graph
        await self.db.commit()

    async def _generate_recommendations(self, analysis: MigrationAnalysis) -> None:
        """Generate migration recommendations"""
        logger.info("Generating recommendations")

        recommendations = []

        # Architecture recommendation
        if analysis.source_stack in ["aspnet_webforms", "asp_classic"]:
            rec = MigrationRecommendation(
                analysis_id=analysis.id,
                category="architecture",
                priority="high",
                title="Migrate to Blazor or ASP.NET Core MVC",
                description="The legacy WebForms/ASP Classic architecture should be migrated to modern .NET patterns.",
                source_agent="felix",
                estimated_effort="weeks"
            )
            self.db.add(rec)

        # Database recommendation
        if analysis.db_migration_difficulty and analysis.db_migration_difficulty >= "C":
            rec = MigrationRecommendation(
                analysis_id=analysis.id,
                category="database",
                priority="critical",
                title="Database Migration Requires Significant Effort",
                description=f"DB migration difficulty is {analysis.db_migration_difficulty}. Plan for {analysis.db_estimated_days} days of DB work.",
                source_agent="miguel",
                estimated_effort="days"
            )
            self.db.add(rec)

        # Security recommendation
        patterns = await self._get_analysis_patterns(analysis.id)
        security_count = sum(1 for p in patterns if p.is_security_issue)
        if security_count > 0:
            rec = MigrationRecommendation(
                analysis_id=analysis.id,
                category="security",
                priority="critical",
                title=f"Address {security_count} Security Issues",
                description="Security vulnerabilities detected in legacy code must be fixed during migration.",
                source_agent="quinn",
                estimated_effort="days"
            )
            self.db.add(rec)

        await self.db.commit()

    async def _calculate_complexity_score(self, analysis: MigrationAnalysis) -> float:
        """Calculate overall complexity score (0-100)"""
        score = 0.0

        # File count factor
        if analysis.total_files:
            score += min(analysis.total_files / 100, 20)

        # LOC factor
        if analysis.total_loc:
            score += min(analysis.total_loc / 10000, 30)

        # Module count factor
        if analysis.total_modules:
            score += min(analysis.total_modules / 50, 20)

        # Legacy pattern factor
        patterns = await self._get_analysis_patterns(analysis.id)
        score += min(len(patterns) / 10, 20)

        # DB complexity factor
        if analysis.db_migration_difficulty:
            difficulty_scores = {"A": 2, "B": 5, "C": 10, "D": 15, "E": 20}
            score += difficulty_scores.get(analysis.db_migration_difficulty, 0)

        return min(score, 100)

    async def _calculate_risk_score(self, analysis: MigrationAnalysis) -> float:
        """Calculate overall risk score (0-100)"""
        risks = await self._get_analysis_risks(analysis.id)

        if not risks:
            return 0.0

        # Average risk score normalized to 0-100
        total = sum(r.risk_score or 0 for r in risks)
        avg = total / len(risks)

        # Risk scores are probability * impact * detectability (1-5 each = max 125)
        return min((avg / 125) * 100, 100)

    # ========== Query Helpers ==========

    async def _get_analysis_modules(self, analysis_id: UUID) -> List[MigrationModule]:
        """Get all modules for an analysis"""
        result = await self.db.execute(
            select(MigrationModule).where(MigrationModule.analysis_id == analysis_id)
        )
        return list(result.scalars().all())

    async def _get_analysis_patterns(self, analysis_id: UUID) -> List[LegacyPattern]:
        """Get all patterns for an analysis"""
        result = await self.db.execute(
            select(LegacyPattern).where(LegacyPattern.analysis_id == analysis_id)
        )
        return list(result.scalars().all())

    async def _get_analysis_risks(self, analysis_id: UUID) -> List[RiskAssessment]:
        """Get all risks for an analysis"""
        result = await self.db.execute(
            select(RiskAssessment).where(RiskAssessment.analysis_id == analysis_id)
        )
        return list(result.scalars().all())

    # ========== Grouping Helpers ==========

    def _group_modules_by_type(self, modules: List[MigrationModule]) -> Dict[str, int]:
        """Group modules by type"""
        result: Dict[str, int] = {}
        for module in modules:
            t = module.module_type or "unknown"
            result[t] = result.get(t, 0) + 1
        return result

    def _group_modules_by_stack(self, modules: List[MigrationModule]) -> Dict[str, int]:
        """Group modules by stack type"""
        result: Dict[str, int] = {}
        for module in modules:
            s = module.stack_type or "unknown"
            result[s] = result.get(s, 0) + 1
        return result

    def _group_risks_by_category(self, risks: List[RiskAssessment]) -> Dict[str, int]:
        """Group risks by category"""
        result: Dict[str, int] = {}
        for risk in risks:
            c = risk.category or "unknown"
            result[c] = result.get(c, 0) + 1
        return result

    def _group_patterns_by_category(self, patterns: List[LegacyPattern]) -> Dict[str, int]:
        """Group patterns by category"""
        result: Dict[str, int] = {}
        for pattern in patterns:
            c = pattern.pattern_category or "unknown"
            result[c] = result.get(c, 0) + 1
        return result


# Singleton instance factory
def get_migration_analyzer_service(db_session: AsyncSession) -> MigrationAnalyzerService:
    """Factory function for MigrationAnalyzerService"""
    return MigrationAnalyzerService(db_session)
