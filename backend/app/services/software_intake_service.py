"""
Software Intake Service - Code-Driven Analysis Facade.

Week 158 - Fase 1: SoftwareIntakeService

This service orchestrates all existing code analyzers to produce a comprehensive
IntakeReport without requiring any user input (questions).

Architecture:
    SoftwareIntakeService (facade)
    ├── Stack Detection (5%)
    ├── Code Metrics via CodeAnalysisAggregatorService (25%)
    ├── Security via MigrationSecurityService + GenericSecurityScanner (45%)
    ├── Estimation via MigrationEstimationService (60%)
    ├── Architecture via MigrationArchitectureService (75%)
    ├── Dependencies via DependencyGraphService (85%)
    ├── Business Rules via DeepExtractionService (95%)
    └── Aggregation & Scoring (100%)

Output:
    IntakeReport JSON - complete analysis ready for frontend display
    and as input for MigrationPlanningService (future)
"""

import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Awaitable
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

# Schemas
from app.schemas.intake import (
    IntakeReport,
    IntakeOptions,
    IntakeStatus,
    IntakeSummary,
    FindingsReport,
    FindingSummary,
    CategoryFindings,
    Finding,
    FindingCategory,
    Severity,
    Location,
    CodeMetrics,
    LanguageMetrics,
    DirectoryMetrics,
    ComplexityDistribution,
    SecurityReport,
    OWASPCoverage,
    CWECoverage,
    EstimationReport,
    PhaseEstimate,
    FunctionPointComponent,
    ArchitectureReport,
    DetectedLayer,
    ComponentMapping,
    DependencyReport,
    InternalDependency,
    ExternalLibrary,
    EOLStatus,
    LicenseRisk,
    BusinessRulesReport,
    ExtractedBusinessRule,
    TechnicalDebtReport,
    DebtCategory,
    EOLAnalysisReport,
    EOLComponent,
    LicenseComplianceReport,
    LicenseIssue,
    PrivacyAnalysisReport,
    TestCoverageReport,
    APISurfaceReport,
    PerformanceHotspotsReport,
    SkillsAssessmentReport,
    QuickWin,
    TCOComparisonReport,
    TCOScenario,
    Recommendation,
    Complexity,
    ConfidenceLevel,
    RoadmapPhase,
    GeneratedCodeReport,
    GeneratedFileInfo,
)

# Generated code detection
from app.services.generated_code_detector import (
    GeneratedCodeDetector,
    GeneratedCodeSummary,
    GeneratorType,
)

# Existing services
from app.services.migration_security_service import (
    MigrationSecurityService,
    MigrationSecurityResult,
    LegacyStack,
)
from app.services.migration_estimation_service import (
    MigrationEstimationService,
    TechnologyStack,
)
from app.services.migration_architecture_service import (
    MigrationArchitectureService,
    TechnologyChoice,
)
from app.services.dependency_graph_service import DependencyGraphService

logger = logging.getLogger(__name__)


# =============================================================================
# PROGRESS TRACKING
# =============================================================================

@dataclass
class AnalysisPhase:
    """Represents a phase in the analysis pipeline."""
    name: str
    weight: int  # Percentage of total
    status: str = "pending"  # pending, running, completed, failed, skipped
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class AnalysisProgress:
    """Tracks overall analysis progress."""
    intake_id: UUID
    status: IntakeStatus = IntakeStatus.PENDING
    current_phase: Optional[str] = None
    progress_percent: int = 0
    phases: Dict[str, AnalysisPhase] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def update_phase(self, phase_name: str, status: str, error: Optional[str] = None):
        """Update a phase's status and recalculate overall progress."""
        if phase_name in self.phases:
            phase = self.phases[phase_name]
            phase.status = status
            if status == "running":
                phase.start_time = datetime.now(timezone.utc)
                self.current_phase = phase_name
            elif status in ("completed", "failed", "skipped"):
                phase.end_time = datetime.now(timezone.utc)
            if error:
                phase.error = error

        # Recalculate progress
        completed_weight = sum(
            p.weight for p in self.phases.values()
            if p.status in ("completed", "skipped")
        )
        self.progress_percent = min(completed_weight, 100)


# Progress callback type
ProgressCallback = Callable[[AnalysisProgress], Awaitable[None]]


# =============================================================================
# STACK MAPPING
# =============================================================================

# Map detected stacks to estimation TechnologyStack
STACK_MAPPING = {
    "aspnet_webforms": TechnologyStack.VB_NET_WEBFORMS,
    "vb_webforms": TechnologyStack.VB_NET_WEBFORMS,
    "csharp_webforms": TechnologyStack.CSHARP_WEBFORMS,
    "classic_asp": TechnologyStack.CLASSIC_ASP,
    "php": TechnologyStack.PHP_LEGACY,
    "php_legacy": TechnologyStack.PHP_LEGACY,
    "java": TechnologyStack.JAVA_LEGACY,
    "java_legacy": TechnologyStack.JAVA_LEGACY,
    "cobol": TechnologyStack.COBOL,
    "oracle_forms": TechnologyStack.ORACLE_FORMS,
    "powerbuilder": TechnologyStack.POWERBUILDER,
}

# Skill mappings for assessment
STACK_SKILLS = {
    "aspnet_webforms": ["VB.NET", "WebForms", "SQL Server", "IIS"],
    "vb_webforms": ["VB.NET", "WebForms", "SQL Server"],
    "csharp_webforms": ["C#", "WebForms", "SQL Server", "IIS"],
    "classic_asp": ["VBScript", "Classic ASP", "SQL Server", "IIS"],
    "php": ["PHP", "MySQL", "Apache"],
    "java": ["Java", "JSP", "Servlets", "Oracle"],
}

TARGET_STACK_SKILLS = {
    "dotnet8": [".NET 8", "C#", "Blazor/Razor", "Entity Framework Core", "PostgreSQL"],
    "python_fastapi": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
    "nodejs_nestjs": ["TypeScript", "NestJS", "TypeORM", "PostgreSQL"],
    "java_spring": ["Java 21", "Spring Boot", "JPA", "PostgreSQL"],
}


# =============================================================================
# SOFTWARE INTAKE SERVICE
# =============================================================================

class SoftwareIntakeService:
    """
    Facade service for code-driven software analysis.

    Orchestrates multiple analyzers to produce a comprehensive IntakeReport
    without requiring user input (100% automated from project_path).

    Usage:
        service = SoftwareIntakeService(db_session)
        report = await service.analyze("/path/to/legacy/code")
    """

    # Phase weights (must sum to 100)
    PHASE_WEIGHTS = {
        "stack_detection": 5,
        "generated_code_detection": 5,  # NEW: detect generated code after stack detection
        "code_metrics": 18,  # Reduced from 20
        "security": 18,  # Reduced from 20 (includes generated code!)
        "estimation": 14,  # Reduced from 15
        "architecture": 14,  # Reduced from 15
        "dependencies": 10,
        "business_rules": 10,
        "aggregation": 6,
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize SoftwareIntakeService.

        Args:
            db: Optional async database session for persistence
        """
        self.db = db

        # Initialize stateless services
        self._security_service = MigrationSecurityService()
        self._estimation_service = MigrationEstimationService()
        self._architecture_service = MigrationArchitectureService()
        self._dependency_service = DependencyGraphService()
        self._generated_code_detector = GeneratedCodeDetector()

        # In-memory storage for active analyses
        self._active_analyses: Dict[UUID, AnalysisProgress] = {}

        # Per-analysis generated file tracking (reset per analyze() call)
        self._generated_file_paths: set[str] = set()

    async def analyze(
        self,
        project_path: str,
        options: Optional[IntakeOptions] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> IntakeReport:
        """
        Execute complete software intake analysis.

        Args:
            project_path: Absolute path to source code directory
            options: Analysis options (depth, included sections)
            progress_callback: Optional async callback for progress updates

        Returns:
            IntakeReport with all analysis results
        """
        options = options or IntakeOptions()
        intake_id = uuid4()
        start_time = datetime.now(timezone.utc)

        # Initialize progress tracking
        progress = AnalysisProgress(
            intake_id=intake_id,
            status=IntakeStatus.ANALYZING,
            started_at=start_time,
            phases={
                name: AnalysisPhase(name=name, weight=weight)
                for name, weight in self.PHASE_WEIGHTS.items()
            }
        )
        self._active_analyses[intake_id] = progress

        # Validate project path
        path = Path(project_path)
        if not path.exists():
            return self._error_report(
                intake_id, project_path, start_time,
                f"Project path does not exist: {project_path}"
            )

        if not path.is_dir():
            return self._error_report(
                intake_id, project_path, start_time,
                f"Project path is not a directory: {project_path}"
            )

        # Initialize report
        report = IntakeReport(
            id=intake_id,
            project_path=project_path,
            project_name=path.name,
            analyzed_at=start_time,
            status=IntakeStatus.ANALYZING,
            progress_percent=0,
            analysis_options=options.model_dump(),
        )

        try:
            # Reset generated file tracking for this analysis
            self._generated_file_paths = set()

            # Phase 1: Stack Detection
            await self._run_phase(
                progress, "stack_detection", progress_callback,
                self._detect_stacks, report, path
            )

            # Phase 2: Generated Code Detection (always run, right after stack detection)
            await self._run_phase(
                progress, "generated_code_detection", progress_callback,
                self._detect_generated_code, report, path
            )

            # Phase 3: Code Metrics (excludes generated code for quality metrics)
            if options.include_security or options.include_estimation:
                await self._run_phase(
                    progress, "code_metrics", progress_callback,
                    self._analyze_code_metrics, report, path
                )
            else:
                progress.update_phase("code_metrics", "skipped")

            # Phase 4: Security Analysis (INCLUDES generated code!)
            if options.include_security:
                await self._run_phase(
                    progress, "security", progress_callback,
                    self._analyze_security, report, path
                )
            else:
                progress.update_phase("security", "skipped")

            # Phase 5: Estimation
            if options.include_estimation:
                await self._run_phase(
                    progress, "estimation", progress_callback,
                    self._analyze_estimation, report, path, options
                )
            else:
                progress.update_phase("estimation", "skipped")

            # Phase 6: Architecture
            if options.include_architecture:
                await self._run_phase(
                    progress, "architecture", progress_callback,
                    self._analyze_architecture, report, path, options
                )
            else:
                progress.update_phase("architecture", "skipped")

            # Phase 7: Dependencies
            if options.include_dependencies:
                await self._run_phase(
                    progress, "dependencies", progress_callback,
                    self._analyze_dependencies, report, path
                )
            else:
                progress.update_phase("dependencies", "skipped")

            # Phase 8: Business Rules
            if options.include_business_rules:
                await self._run_phase(
                    progress, "business_rules", progress_callback,
                    self._extract_business_rules, report, path
                )
            else:
                progress.update_phase("business_rules", "skipped")

            # Phase 9: Aggregation & Scoring
            await self._run_phase(
                progress, "aggregation", progress_callback,
                self._aggregate_and_score, report, options
            )

            # Finalize
            report.status = IntakeStatus.COMPLETED
            report.progress_percent = 100
            report.analysis_duration_seconds = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()

            progress.status = IntakeStatus.COMPLETED
            progress.completed_at = datetime.now(timezone.utc)

            if progress_callback:
                await progress_callback(progress)

            logger.info(f"Intake analysis completed: {intake_id}")
            return report

        except Exception as e:
            logger.exception(f"Intake analysis failed: {intake_id}")
            report.status = IntakeStatus.FAILED
            report.error_message = str(e)
            progress.status = IntakeStatus.FAILED
            progress.error_message = str(e)

            if progress_callback:
                await progress_callback(progress)

            return report

        finally:
            # Clean up active analysis tracking
            self._active_analyses.pop(intake_id, None)

    async def _run_phase(
        self,
        progress: AnalysisProgress,
        phase_name: str,
        callback: Optional[ProgressCallback],
        func: Callable,
        *args,
        **kwargs
    ):
        """Run a single analysis phase with progress tracking."""
        progress.update_phase(phase_name, "running")
        if callback:
            await callback(progress)

        try:
            await func(*args, **kwargs)
            progress.update_phase(phase_name, "completed")
        except Exception as e:
            logger.error(f"Phase {phase_name} failed: {e}")
            progress.update_phase(phase_name, "failed", str(e))
            raise

        if callback:
            await callback(progress)

    def get_progress(self, intake_id: UUID) -> Optional[AnalysisProgress]:
        """Get current progress for an active analysis."""
        return self._active_analyses.get(intake_id)

    # =========================================================================
    # PHASE IMPLEMENTATIONS
    # =========================================================================

    async def _detect_stacks(self, report: IntakeReport, path: Path):
        """Phase 1: Detect technology stacks from file extensions and patterns."""
        logger.info(f"Detecting stacks in {path}")

        # Count files by extension
        extension_counts: Dict[str, int] = {}
        total_files = 0

        for file_path in path.rglob("*"):
            if file_path.is_file() and not self._should_skip_path(file_path):
                total_files += 1
                ext = file_path.suffix.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1

        # Detect languages
        languages = []
        frameworks = []

        # VB.NET / WebForms
        if extension_counts.get(".vb", 0) > 0:
            languages.append("VB.NET")
            if extension_counts.get(".aspx", 0) > 0:
                frameworks.append("WebForms")

        # C#
        if extension_counts.get(".cs", 0) > 0:
            languages.append("C#")
            if extension_counts.get(".aspx", 0) > 0 and "WebForms" not in frameworks:
                frameworks.append("WebForms")

        # Classic ASP
        if extension_counts.get(".asp", 0) > 0:
            languages.append("VBScript")
            frameworks.append("Classic ASP")

        # JavaScript/TypeScript
        if extension_counts.get(".js", 0) > 0 or extension_counts.get(".ts", 0) > 0:
            languages.append("JavaScript" if extension_counts.get(".js", 0) > extension_counts.get(".ts", 0) else "TypeScript")

        # PHP
        if extension_counts.get(".php", 0) > 0:
            languages.append("PHP")

        # Java
        if extension_counts.get(".java", 0) > 0:
            languages.append("Java")

        # SQL
        if extension_counts.get(".sql", 0) > 0:
            languages.append("T-SQL")

        # Python
        if extension_counts.get(".py", 0) > 0:
            languages.append("Python")

        # Detect databases from connection strings (simplified)
        databases = []
        db_keywords = {
            "SQL Server": ["sqlserver", "mssql", "System.Data.SqlClient"],
            "Oracle": ["oracle", "OracleConnection"],
            "MySQL": ["mysql", "MySqlConnection"],
            "PostgreSQL": ["postgresql", "npgsql"],
        }

        # Quick scan for database indicators
        for config_file in path.rglob("*.config"):
            try:
                content = config_file.read_text(errors="ignore").lower()
                for db, keywords in db_keywords.items():
                    if any(kw.lower() in content for kw in keywords):
                        if db not in databases:
                            databases.append(db)
            except Exception:
                pass

        # Update summary
        report.summary.total_files = total_files
        report.summary.languages = languages[:5]  # Top 5
        report.summary.frameworks = frameworks[:5]
        report.summary.databases = databases
        report.summary.primary_language = languages[0] if languages else None
        report.summary.primary_framework = frameworks[0] if frameworks else None

        # Store detected stack for later phases
        report.scanners_used.append("stack_detection")

        logger.info(f"Detected: {languages}, {frameworks}, {databases}")

    async def _detect_generated_code(self, report: IntakeReport, path: Path):
        """
        Phase 2: Detect generated code.

        Identifies auto-generated code to enable proper metric handling:
        - Generated code: Include in SECURITY scans and VOLUME metrics
        - Generated code: EXCLUDE from QUALITY metrics (complexity, duplication, etc.)
        """
        logger.info(f"Detecting generated code in {path}")

        # Determine which file extensions to check based on detected languages
        code_extensions = {
            ".vb", ".cs", ".asp", ".aspx", ".js", ".ts", ".jsx", ".tsx",
            ".php", ".java", ".sql", ".py", ".html", ".css", ".xml", ".json",
            ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".swift", ".kt",
        }

        # Run detection (check_content=True for thorough detection)
        summary = self._generated_code_detector.analyze_directory(
            str(path),
            check_content=True,
            file_extensions=code_extensions,
        )

        # Store generated file paths for exclusion in quality metrics
        self._generated_file_paths = {
            match.file_path for match in summary.generated_file_list
        }

        # Build the report
        generated_report = GeneratedCodeReport(
            total_files=summary.total_files,
            generated_files=summary.generated_files,
            handwritten_files=summary.handwritten_files,
            generated_loc=summary.generated_loc,
            handwritten_loc=summary.handwritten_loc,
            generated_percentage=(
                (summary.generated_files / summary.total_files * 100)
                if summary.total_files > 0 else 0.0
            ),
            by_generator_type=summary.by_generator_type,
            by_directory=summary.by_directory,
            by_detection_method=summary.by_detection_method,
            top_generated_directories=sorted(
                summary.by_directory.keys(),
                key=lambda d: summary.by_directory.get(d, 0),
                reverse=True
            )[:10],
            # Limit file list to first 100 for performance
            generated_file_list=[
                GeneratedFileInfo(
                    file_path=str(Path(match.file_path).relative_to(path)),
                    generator_type=match.generator_type.value,
                    detection_method=match.detection_method,
                    matched_pattern=match.matched_pattern,
                    confidence=match.confidence,
                )
                for match in summary.generated_file_list[:100]
            ],
        )

        # Update report
        report.generated_code = generated_report
        report.summary.generated_files_count = summary.generated_files
        report.summary.generated_loc = summary.generated_loc
        report.summary.generated_percentage = (
            (summary.generated_loc / (summary.generated_loc + summary.handwritten_loc) * 100)
            if (summary.generated_loc + summary.handwritten_loc) > 0 else 0.0
        )

        report.scanners_used.append("generated_code_detection")

        logger.info(
            f"Generated code detection: {summary.generated_files}/{summary.total_files} files "
            f"({summary.generated_loc:,} LOC, {generated_report.generated_percentage:.1f}%)"
        )

    def _is_generated_file(self, file_path: Path) -> bool:
        """Check if a file was detected as generated code."""
        return str(file_path) in self._generated_file_paths

    async def _analyze_code_metrics(self, report: IntakeReport, path: Path):
        """Phase 3: Analyze code metrics (LOC, complexity, etc.)."""
        logger.info(f"Analyzing code metrics in {path}")

        metrics = CodeMetrics()
        language_stats: Dict[str, Dict[str, int]] = {}
        total_loc = 0
        total_blank = 0
        total_comment = 0

        # Extension to language mapping
        ext_to_lang = {
            ".vb": "VB.NET", ".cs": "C#", ".asp": "Classic ASP",
            ".aspx": "ASPX", ".js": "JavaScript", ".ts": "TypeScript",
            ".php": "PHP", ".java": "Java", ".sql": "SQL",
            ".py": "Python", ".html": "HTML", ".css": "CSS",
            ".xml": "XML", ".json": "JSON",
        }

        for file_path in path.rglob("*"):
            # Exclude generated code from quality metrics (LOC still counted in volume)
            if not file_path.is_file() or self._should_skip_path(file_path, exclude_generated=True):
                continue

            ext = file_path.suffix.lower()
            lang = ext_to_lang.get(ext)
            if not lang:
                continue

            try:
                content = file_path.read_text(errors="ignore")
                lines = content.split("\n")

                loc = 0
                blank = 0
                comment = 0

                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        blank += 1
                    elif self._is_comment_line(stripped, lang):
                        comment += 1
                    else:
                        loc += 1

                if lang not in language_stats:
                    language_stats[lang] = {"files": 0, "loc": 0, "blank": 0, "comment": 0}

                language_stats[lang]["files"] += 1
                language_stats[lang]["loc"] += loc
                language_stats[lang]["blank"] += blank
                language_stats[lang]["comment"] += comment

                total_loc += loc
                total_blank += blank
                total_comment += comment

            except Exception:
                pass

        # Build language metrics
        for lang, stats in sorted(language_stats.items(), key=lambda x: -x[1]["loc"]):
            percentage = (stats["loc"] / total_loc * 100) if total_loc > 0 else 0
            metrics.by_language.append(LanguageMetrics(
                language=lang,
                file_count=stats["files"],
                loc=stats["loc"],
                blank_lines=stats["blank"],
                comment_lines=stats["comment"],
                percentage=round(percentage, 1),
            ))

        # Update report
        report.code_metrics = metrics
        report.summary.total_loc = total_loc
        report.summary.total_blank_lines = total_blank
        report.summary.total_comment_lines = total_comment

        report.scanners_used.append("code_metrics")
        logger.info(f"Code metrics: {total_loc} LOC across {len(language_stats)} languages")

    async def _analyze_security(self, report: IntakeReport, path: Path):
        """Phase 3: Security analysis using MigrationSecurityService."""
        logger.info(f"Analyzing security in {path}")

        # Run security scan
        result = self._security_service.analyze_directory(str(path))

        # Convert to schema
        security_report = SecurityReport(
            risk_score=result.risk_score.total_score if result.risk_score else 0.0,
            estimated_remediation_hours=result.risk_score.estimated_remediation_hours if result.risk_score else 0.0,
            scanners_used=["MigrationSecurityService"],
        )

        # Map findings
        for finding in result.findings[:50]:  # Limit to top 50
            severity = self._map_severity(finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity))

            intake_finding = Finding(
                id=f"SEC-{finding.pattern_id}",
                severity=severity,
                category=FindingCategory.SECURITY,
                title=finding.pattern_name,
                description=finding.description,
                location=Location(
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                ),
                cwe_id=f"CWE-{finding.cwe_id}" if finding.cwe_id else None,
                owasp_category=finding.owasp_category.value if hasattr(finding.owasp_category, 'value') else str(finding.owasp_category),
                remediation=finding.remediation,
                effort_hours=self._estimate_remediation_hours(finding.remediation_effort.value if hasattr(finding.remediation_effort, 'value') else "medium"),
                scanner="MigrationSecurityService",
            )

            security_report.top_findings.append(intake_finding)

            # Add to centralized findings
            report.findings.by_category[FindingCategory.SECURITY.value].items.append(intake_finding)

        # Update counts
        security_report.findings_by_severity = {
            "critical": result.risk_score.critical_count if result.risk_score else 0,
            "high": result.risk_score.high_count if result.risk_score else 0,
            "medium": result.risk_score.medium_count if result.risk_score else 0,
            "low": result.risk_score.low_count if result.risk_score else 0,
        }

        cat_findings = report.findings.by_category[FindingCategory.SECURITY.value]
        cat_findings.count = len(result.findings)
        cat_findings.critical = security_report.findings_by_severity["critical"]
        cat_findings.high = security_report.findings_by_severity["high"]
        cat_findings.medium = security_report.findings_by_severity["medium"]
        cat_findings.low = security_report.findings_by_severity["low"]

        report.security = security_report
        report.summary.security_issues_count = len(result.findings)
        report.scanners_used.append("security_scan")

        logger.info(f"Security: {len(result.findings)} findings, risk score: {security_report.risk_score}")

    async def _analyze_estimation(self, report: IntakeReport, path: Path, options: IntakeOptions):
        """Phase 4: Function Point estimation using MigrationEstimationService."""
        logger.info(f"Analyzing estimation in {path}")

        # Determine source stack
        primary_lang = report.summary.primary_language
        primary_fw = report.summary.primary_framework

        source_stack = TechnologyStack.VB_NET_WEBFORMS  # Default

        if primary_fw == "Classic ASP":
            source_stack = TechnologyStack.CLASSIC_ASP
        elif primary_lang == "PHP":
            source_stack = TechnologyStack.PHP_LEGACY
        elif primary_lang == "Java":
            source_stack = TechnologyStack.JAVA_LEGACY
        elif primary_lang == "C#" and primary_fw == "WebForms":
            source_stack = TechnologyStack.CSHARP_WEBFORMS

        # Run estimation
        result = self._estimation_service.analyze_directory(
            str(path),
            source_stack=source_stack,
            target_stack=options.target_stack or "dotnet8",
        )

        # Convert to schema
        estimation = EstimationReport(
            function_points_unadjusted=int(result.total_unadjusted_fp),
            value_adjustment_factor=result.value_adjustment_factor,
            function_points_adjusted=int(result.total_adjusted_fp),
            effort_hours=result.total_effort_hours,
            effort_person_days=result.total_effort_person_days,
            effort_person_months=result.total_effort_person_days / 20,  # 20 working days/month
            confidence=self._map_confidence(result.confidence_level),
            source_stack=source_stack.value if hasattr(source_stack, 'value') else str(source_stack),
            target_stack=options.target_stack or "dotnet8",
        )

        # Map phases
        for phase in result.phase_estimates:
            estimation.phases.append(PhaseEstimate(
                phase=phase.phase.value if hasattr(phase.phase, 'value') else str(phase.phase),
                description=phase.phase.value if hasattr(phase.phase, 'value') else str(phase.phase),
                activities=phase.activities if hasattr(phase, 'activities') else [],
                base_hours=phase.base_hours,
                risk_buffer_hours=phase.risk_buffer_hours,
                total_hours=phase.total_hours,
                percentage_of_total=round(phase.total_hours / result.total_effort_hours * 100, 1) if result.total_effort_hours > 0 else 0,
            ))

        report.estimation = estimation
        report.scanners_used.append("estimation")

        logger.info(f"Estimation: {estimation.function_points_adjusted} FP, {estimation.effort_hours:.0f} hours")

    async def _analyze_architecture(self, report: IntakeReport, path: Path, options: IntakeOptions):
        """Phase 5: Architecture analysis using MigrationArchitectureService."""
        logger.info(f"Analyzing architecture in {path}")

        # Determine target technology
        target_tech = TechnologyChoice.DOTNET_MINIMAL  # Default to .NET
        if options.target_stack == "python_fastapi":
            target_tech = TechnologyChoice.PYTHON_FASTAPI
        elif options.target_stack == "nodejs_nestjs":
            target_tech = TechnologyChoice.NODEJS_NESTJS
        elif options.target_stack == "java_spring":
            target_tech = TechnologyChoice.JAVA_SPRING

        # Run architecture analysis
        result = self._architecture_service.analyze_directory(
            str(path),
            target_technology=target_tech,
        )

        # Convert to schema - use correct ArchitectureRecommendation fields
        architecture = ArchitectureReport(
            recommended_pattern=result.recommended_pattern.value if hasattr(result.recommended_pattern, 'value') else str(result.recommended_pattern),
            recommended_strategy=result.migration_strategy.value if hasattr(result.migration_strategy, 'value') else str(result.migration_strategy),
        )

        # Extract layers from legacy_components
        layer_stats = {}  # Group by layer
        for comp in result.legacy_components:
            layer_name = comp.layer.value if hasattr(comp.layer, 'value') else str(comp.layer)
            if layer_name not in layer_stats:
                layer_stats[layer_name] = {'file_count': 0, 'components': []}
            layer_stats[layer_name]['file_count'] += 1
            layer_stats[layer_name]['components'].append(comp.name)

        # Build detected layers from legacy components
        for layer_name, stats in layer_stats.items():
            architecture.detected_layers.append(DetectedLayer(
                name=layer_name,
                description=f"Contains {stats['file_count']} components",
                file_count=stats['file_count'],
                loc=0,  # LOC not tracked per layer
            ))

        # Map legacy -> target component mappings
        for legacy_comp in result.legacy_components[:20]:  # Limit
            # Find matching target component
            target_comp = None
            for tc in result.target_components:
                if legacy_comp.name.lower() in tc.name.lower():
                    target_comp = tc
                    break

            architecture.component_mapping.append(ComponentMapping(
                legacy_component=legacy_comp.name,
                legacy_type=legacy_comp.layer.value if hasattr(legacy_comp.layer, 'value') else str(legacy_comp.layer),
                legacy_location=legacy_comp.file_path if hasattr(legacy_comp, 'file_path') else "",
                target_component=target_comp.name if target_comp else f"New{legacy_comp.name}",
                target_type=target_comp.layer.value if target_comp and hasattr(target_comp.layer, 'value') else "service",
                migration_strategy="refactor",
                effort_hours=target_comp.estimated_effort_hours if target_comp and hasattr(target_comp, 'estimated_effort_hours') else 8,
            ))

        # Add risks as architecture findings
        for i, risk in enumerate(result.risks[:10]):  # Limit
            finding = Finding(
                id=f"ARCH-{i + 1:03d}",
                severity=Severity.MEDIUM,
                category=FindingCategory.ARCHITECTURE,
                title="Architecture Risk",
                description=risk,
            )
            architecture.architecture_issues.append(finding)
            report.findings.by_category[FindingCategory.ARCHITECTURE.value].items.append(finding)

        # Add architecture decisions as context (INFO level, not issues)
        for decision in result.architecture_decisions[:5]:
            finding = Finding(
                id=f"ARCH-DEC-{len(architecture.architecture_issues) + 1:03d}",
                severity=Severity.INFO,
                category=FindingCategory.ARCHITECTURE,
                title=decision.decision_type if hasattr(decision, 'decision_type') else "Architecture Decision",
                description=decision.rationale if hasattr(decision, 'rationale') else str(decision),
            )
            # Decisions are informational, add to issues for visibility
            architecture.architecture_issues.append(finding)

        report.architecture = architecture
        report.scanners_used.append("architecture")

        logger.info(f"Architecture: pattern={architecture.recommended_pattern}, {len(architecture.detected_layers)} layers")

    async def _analyze_dependencies(self, report: IntakeReport, path: Path):
        """Phase 6: Dependency analysis using DependencyGraphService."""
        logger.info(f"Analyzing dependencies in {path}")

        # Run dependency analysis
        result = self._dependency_service.analyze_directory(str(path))

        # Convert to schema
        dependencies = DependencyReport(
            total_dependencies=len(result.get('dependencies', [])) if isinstance(result, dict) else 0,
        )

        # Map internal dependencies
        for dep in result.get('internal_dependencies', [])[:50] if isinstance(result, dict) else []:
            dependencies.internal_dependencies.append(InternalDependency(
                source_module=dep.get('source', ''),
                target_module=dep.get('target', ''),
                dependency_type=dep.get('type', 'import'),
            ))

        # Check for circular dependencies
        dependencies.circular_dependencies = result.get('circular', []) if isinstance(result, dict) else []

        # Add circular dependency findings
        for cycle in dependencies.circular_dependencies[:5]:
            finding = Finding(
                id=f"DEP-CYCLE-{len(report.findings.by_category[FindingCategory.ARCHITECTURE.value].items) + 1:03d}",
                severity=Severity.HIGH,
                category=FindingCategory.ARCHITECTURE,
                title="Circular Dependency Detected",
                description=f"Circular dependency: {' -> '.join(cycle)}",
                remediation="Break the cycle by introducing interfaces or reorganizing modules",
            )
            report.findings.by_category[FindingCategory.ARCHITECTURE.value].items.append(finding)

        report.dependencies = dependencies
        report.scanners_used.append("dependencies")

        logger.info(f"Dependencies: {dependencies.total_dependencies} total, {len(dependencies.circular_dependencies)} cycles")

    async def _extract_business_rules(self, report: IntakeReport, path: Path):
        """Phase 7: Business rules extraction (simplified)."""
        logger.info(f"Extracting business rules in {path}")

        # Simplified business rules detection
        business_rules = BusinessRulesReport()

        # Look for validation patterns
        validation_patterns = [
            (r"if.*\.length\s*[<>=]", "Length validation"),
            (r"if.*==\s*null|if.*is\s+nothing", "Null check"),
            (r"if.*>\s*0|if.*<\s*0", "Numeric validation"),
            (r"regex|regexp|pattern\.match", "Pattern validation"),
        ]

        import re

        for file_path in path.rglob("*"):
            if not file_path.is_file() or self._should_skip_path(file_path):
                continue

            if file_path.suffix.lower() not in [".vb", ".cs", ".asp", ".php", ".java", ".py"]:
                continue

            try:
                content = file_path.read_text(errors="ignore")

                for pattern, rule_type in validation_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        for i, match in enumerate(matches[:3]):  # Limit per file
                            rule = ExtractedBusinessRule(
                                id=f"BR-{business_rules.extracted_count + 1:04d}",
                                name=f"{rule_type} in {file_path.name}",
                                description=f"Detected {rule_type.lower()} pattern",
                                rule_type="validation",
                                location=Location(file_path=str(file_path.relative_to(path))),
                                confidence=0.7,
                            )
                            business_rules.validation_rules.append(rule)
                            business_rules.extracted_count += 1

                            if business_rules.extracted_count >= 100:
                                break

                if business_rules.extracted_count >= 100:
                    break

            except Exception:
                pass

        business_rules.by_type = {
            "validation": len(business_rules.validation_rules),
            "calculation": len(business_rules.calculations),
            "workflow": len(business_rules.workflows),
            "constraint": len(business_rules.constraints),
        }

        report.business_rules = business_rules
        report.scanners_used.append("business_rules")

        logger.info(f"Business rules: {business_rules.extracted_count} extracted")

    async def _aggregate_and_score(self, report: IntakeReport, options: IntakeOptions):
        """Phase 8: Aggregate all findings and calculate scores."""
        logger.info("Aggregating results and calculating scores")

        # Aggregate finding counts
        total_findings = 0
        total_critical = 0
        total_high = 0
        total_medium = 0
        total_low = 0

        for category in FindingCategory:
            cat_data = report.findings.by_category.get(category.value, CategoryFindings())
            total_findings += cat_data.count
            total_critical += cat_data.critical
            total_high += cat_data.high
            total_medium += cat_data.medium
            total_low += cat_data.low

        report.findings.summary = FindingSummary(
            total=total_findings,
            critical=total_critical,
            high=total_high,
            medium=total_medium,
            low=total_low,
        )

        # Calculate health score (0-100, higher = healthier)
        # Start at 100, deduct points for issues
        health_score = 100
        health_score -= total_critical * 10
        health_score -= total_high * 5
        health_score -= total_medium * 2
        health_score -= total_low * 0.5

        # Additional deductions
        if report.security and report.security.risk_score > 50:
            health_score -= 10

        if report.dependencies and len(report.dependencies.circular_dependencies) > 0:
            health_score -= 5 * len(report.dependencies.circular_dependencies)

        report.findings.health_score = max(0, min(100, int(health_score)))
        report.summary.health_score = report.findings.health_score

        # Determine migration complexity
        if report.estimation:
            fp = report.estimation.function_points_adjusted
            if fp < 200:
                report.summary.migration_complexity = Complexity.LOW
            elif fp < 500:
                report.summary.migration_complexity = Complexity.MEDIUM
            elif fp < 1000:
                report.summary.migration_complexity = Complexity.HIGH
            else:
                report.summary.migration_complexity = Complexity.VERY_HIGH

        # Generate top priority findings
        all_findings = []
        for category in FindingCategory:
            all_findings.extend(report.findings.by_category.get(category.value, CategoryFindings()).items)

        # Sort by severity (critical first)
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
        all_findings.sort(key=lambda f: severity_order.get(f.severity, 5))
        report.findings.top_10_priority = all_findings[:10]

        # Generate quick wins
        report.quick_wins = self._generate_quick_wins(report)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        # Generate TCO comparison if requested
        if options.include_tco and report.estimation:
            report.tco_comparison = self._generate_tco(report, options)

        # Generate skills assessment if requested
        if options.include_skills_assessment:
            report.skills_assessment = self._generate_skills_assessment(report, options)

        # Generate technical debt report
        if options.include_technical_debt:
            report.technical_debt = self._generate_technical_debt(report, options)

        logger.info(f"Aggregation complete: health_score={report.findings.health_score}")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _should_skip_path(
        self,
        path: Path,
        exclude_generated: bool = False
    ) -> bool:
        """
        Check if path should be skipped during analysis.

        Args:
            path: The path to check
            exclude_generated: If True, also skip files detected as generated code.
                              Use for QUALITY metrics, not for SECURITY or VOLUME.

        Returns:
            True if the path should be skipped
        """
        skip_dirs = {
            # Version control
            ".git", ".svn", ".hg",
            # IDE/Editor
            ".vs", ".idea", ".vscode",
            # .NET build output
            "bin", "obj", "packages",
            # Python
            "__pycache__", ".venv", "venv", "site-packages",
            # JavaScript/Node
            "node_modules", "bower_components",
            # Frontend build output (bundled/minified JS frameworks)
            "dist", "build", ".next", ".nuxt", "out",
            # Vendor/third-party libraries
            "vendor", "libs", "lib", "third_party", "external",
            # Coverage/test output
            "coverage", ".nyc_output",
        }
        skip_extensions = {
            # Binaries
            ".dll", ".exe", ".pdb", ".so", ".dylib",
            # Cache/temp
            ".cache", ".tmp",
            # Lock files (dependency manifests, not code)
            ".lock",
            # Minified files (generated, not handwritten)
            ".min.js", ".min.css",
            # Source maps
            ".map",
        }

        parts = path.parts
        if any(part in skip_dirs for part in parts):
            return True

        # Check simple extensions
        if path.suffix.lower() in skip_extensions:
            return True

        # Check compound extensions (e.g., .min.js, .min.css)
        filename = path.name.lower()
        if any(filename.endswith(ext) for ext in skip_extensions if ext.count('.') > 1):
            return True

        # Optionally exclude generated code (for quality metrics)
        if exclude_generated and self._is_generated_file(path):
            return True

        return False

    def get_generated_file_paths(self) -> set[str]:
        """
        Get the set of generated file paths detected during analysis.

        Can be used by external analyzers to exclude generated code from quality metrics.

        Returns:
            Set of absolute file paths detected as generated code
        """
        return self._generated_file_paths.copy()

    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if line is a comment."""
        comment_prefixes = {
            "VB.NET": ["'", "rem "],
            "C#": ["//", "/*", "*"],
            "Classic ASP": ["'", "rem "],
            "JavaScript": ["//", "/*", "*"],
            "TypeScript": ["//", "/*", "*"],
            "PHP": ["//", "#", "/*", "*"],
            "Java": ["//", "/*", "*"],
            "SQL": ["--", "/*", "*"],
            "Python": ["#"],
        }

        prefixes = comment_prefixes.get(language, [])
        lower_line = line.lower()
        return any(lower_line.startswith(p) for p in prefixes)

    def _map_severity(self, severity_str: str) -> Severity:
        """Map string severity to Severity enum."""
        mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
        }
        return mapping.get(severity_str.lower(), Severity.MEDIUM)

    def _map_confidence(self, confidence_value) -> ConfidenceLevel:
        """Map confidence value (float or string) to ConfidenceLevel enum."""
        # Handle float (0.0-1.0)
        if isinstance(confidence_value, (int, float)):
            if confidence_value >= 0.7:
                return ConfidenceLevel.HIGH
            elif confidence_value >= 0.4:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW

        # Handle string
        if isinstance(confidence_value, str):
            mapping = {
                "high": ConfidenceLevel.HIGH,
                "medium": ConfidenceLevel.MEDIUM,
                "low": ConfidenceLevel.LOW,
            }
            return mapping.get(confidence_value.lower(), ConfidenceLevel.MEDIUM)

        return ConfidenceLevel.MEDIUM

    def _estimate_remediation_hours(self, effort_level: str) -> float:
        """Estimate remediation hours from effort level."""
        mapping = {
            "trivial": 0.5,
            "low": 2.0,
            "medium": 8.0,
            "high": 24.0,
            "very_high": 80.0,
        }
        return mapping.get(effort_level.lower(), 8.0)

    def _generate_quick_wins(self, report: IntakeReport) -> List[QuickWin]:
        """Generate quick win recommendations."""
        quick_wins = []

        # Security quick wins
        if report.security and report.security.findings_by_severity.get("low", 0) > 0:
            quick_wins.append(QuickWin(
                title="Fix low-severity security issues",
                description="Address simple security issues that can be fixed quickly",
                effort_hours=4.0,
                impact=Severity.MEDIUM,
                reduces_risk=["security"],
            ))

        # Dependency updates
        if report.dependencies and report.dependencies.outdated_dependencies > 0:
            quick_wins.append(QuickWin(
                title="Update outdated dependencies",
                description=f"Update {report.dependencies.outdated_dependencies} outdated packages",
                effort_hours=8.0,
                impact=Severity.MEDIUM,
                reduces_risk=["security", "eol"],
            ))

        # Code documentation
        if report.code_metrics:
            total_loc = report.summary.total_loc
            comment_ratio = report.summary.total_comment_lines / total_loc if total_loc > 0 else 0
            if comment_ratio < 0.05:
                quick_wins.append(QuickWin(
                    title="Add code documentation",
                    description="Add comments to critical business logic sections",
                    effort_hours=16.0,
                    impact=Severity.LOW,
                    reduces_risk=["maintainability"],
                ))

        return quick_wins[:5]

    def _generate_recommendations(self, report: IntakeReport) -> List[Recommendation]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Critical security
        if report.findings.summary.critical > 0:
            recommendations.append(Recommendation(
                id="REC-001",
                priority=Severity.CRITICAL,
                category=FindingCategory.SECURITY,
                title="Fix critical security vulnerabilities",
                description=f"Address {report.findings.summary.critical} critical security issues before migration",
                effort_hours=report.findings.summary.critical * 8.0,
                impact="Prevents potential security breaches",
            ))

        # Architecture issues
        if report.dependencies and len(report.dependencies.circular_dependencies) > 0:
            recommendations.append(Recommendation(
                id="REC-002",
                priority=Severity.HIGH,
                category=FindingCategory.ARCHITECTURE,
                title="Resolve circular dependencies",
                description=f"Break {len(report.dependencies.circular_dependencies)} circular dependency cycles",
                effort_hours=len(report.dependencies.circular_dependencies) * 16.0,
                impact="Improves testability and maintainability",
            ))

        # Migration strategy
        if report.architecture:
            recommendations.append(Recommendation(
                id="REC-003",
                priority=Severity.MEDIUM,
                category=FindingCategory.ARCHITECTURE,
                title=f"Follow {report.architecture.recommended_strategy} migration strategy",
                description=f"Use {report.architecture.recommended_pattern} pattern for target architecture",
                impact="Reduces migration risk",
            ))

        return recommendations

    def _generate_tco(self, report: IntakeReport, options: IntakeOptions) -> TCOComparisonReport:
        """Generate TCO comparison."""
        hourly_rate = options.hourly_rate_eur

        # Estimate annual maintenance cost (15-25% of initial development)
        initial_hours = report.estimation.effort_hours if report.estimation else 0
        annual_maintenance = initial_hours * hourly_rate * 0.20  # 20% annually

        maintain = TCOScenario(
            name="Maintain As-Is",
            one_time_cost_eur=0,
            annual_cost_eur=annual_maintenance * 1.5,  # Higher for legacy
            five_year_cost_eur=annual_maintenance * 1.5 * 5,
            risks=["EOL technologies", "Security vulnerabilities", "Talent scarcity"],
            benefits=["No upfront investment", "Known system"],
        )

        migrate = TCOScenario(
            name="Migrate to Modern Stack",
            one_time_cost_eur=initial_hours * hourly_rate,
            annual_cost_eur=annual_maintenance,
            five_year_cost_eur=initial_hours * hourly_rate + annual_maintenance * 5,
            risks=["Migration risk", "Learning curve", "Parallel run period"],
            benefits=["Modern stack", "Cloud native", "Talent availability", "Lower maintenance"],
        )

        # Calculate break-even
        annual_savings = maintain.annual_cost_eur - migrate.annual_cost_eur
        break_even = migrate.one_time_cost_eur / annual_savings if annual_savings > 0 else None

        recommendation = "migrate" if migrate.five_year_cost_eur < maintain.five_year_cost_eur else "maintain"

        return TCOComparisonReport(
            maintain_as_is=maintain,
            migrate=migrate,
            break_even_years=break_even,
            recommendation=recommendation,
            recommendation_reason=f"{'Migration' if recommendation == 'migrate' else 'Maintenance'} is more cost-effective over 5 years",
            assumptions=[
                f"Hourly rate: EUR {hourly_rate}",
                "Annual maintenance: 20% of development effort",
                "Legacy maintenance premium: 50%",
            ],
        )

    def _generate_skills_assessment(self, report: IntakeReport, options: IntakeOptions) -> SkillsAssessmentReport:
        """Generate skills assessment for modernization."""
        current_skills = []
        target_skills = []

        # Determine current skills from detected stack
        primary_fw = report.summary.primary_framework
        if primary_fw in STACK_SKILLS:
            current_skills = STACK_SKILLS[primary_fw]
        elif report.summary.primary_language:
            current_skills = [report.summary.primary_language]

        # Determine target skills
        target_stack = options.target_stack or "dotnet8"
        target_skills = TARGET_STACK_SKILLS.get(target_stack, [".NET 8", "C#", "PostgreSQL"])

        # Calculate training estimate (rough: 20 hours per new skill)
        new_skills = [s for s in target_skills if s not in current_skills]
        training_hours = len(new_skills) * 20

        return SkillsAssessmentReport(
            current_stack_skills=current_skills,
            target_stack_skills=target_skills,
            training_hours_estimate=training_hours,
            training_cost_estimate_eur=training_hours * 50,  # EUR 50/hour training cost
            recommended_training=new_skills,
        )

    def _generate_technical_debt(self, report: IntakeReport, options: IntakeOptions) -> TechnicalDebtReport:
        """Generate technical debt report."""
        hourly_rate = options.hourly_rate_eur

        categories = []
        total_hours = 0

        # Security debt
        if report.security:
            security_hours = report.security.estimated_remediation_hours
            categories.append(DebtCategory(
                category="security",
                hours=security_hours,
                cost_eur=security_hours * hourly_rate,
                finding_count=len(report.security.top_findings),
            ))
            total_hours += security_hours

        # Architecture debt (circular dependencies, etc.)
        arch_findings = len(report.findings.by_category.get(FindingCategory.ARCHITECTURE.value, CategoryFindings()).items)
        if arch_findings > 0:
            arch_hours = arch_findings * 8  # 8 hours per issue
            categories.append(DebtCategory(
                category="architecture",
                hours=arch_hours,
                cost_eur=arch_hours * hourly_rate,
                finding_count=arch_findings,
            ))
            total_hours += arch_hours

        # Code quality debt
        quality_findings = len(report.findings.by_category.get(FindingCategory.QUALITY.value, CategoryFindings()).items)
        if quality_findings > 0:
            quality_hours = quality_findings * 4
            categories.append(DebtCategory(
                category="code_quality",
                hours=quality_hours,
                cost_eur=quality_hours * hourly_rate,
                finding_count=quality_findings,
            ))
            total_hours += quality_hours

        # Calculate debt ratio
        total_loc = report.summary.total_loc
        estimated_dev_hours = total_loc / 50  # Rough: 50 LOC/hour historically
        debt_ratio = total_hours / estimated_dev_hours if estimated_dev_hours > 0 else 0

        return TechnicalDebtReport(
            total_hours=total_hours,
            total_cost_eur=total_hours * hourly_rate,
            hourly_rate_eur=hourly_rate,
            by_category=categories,
            debt_ratio=min(debt_ratio, 1.0),
            payoff_recommendation="Address security debt first, then architecture issues",
        )

    def _error_report(
        self,
        intake_id: UUID,
        project_path: str,
        start_time: datetime,
        error_message: str
    ) -> IntakeReport:
        """Create an error report."""
        return IntakeReport(
            id=intake_id,
            project_path=project_path,
            analyzed_at=start_time,
            status=IntakeStatus.FAILED,
            progress_percent=0,
            error_message=error_message,
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_software_intake_service(db: Optional[AsyncSession] = None) -> SoftwareIntakeService:
    """Factory function to get SoftwareIntakeService instance."""
    return SoftwareIntakeService(db)
