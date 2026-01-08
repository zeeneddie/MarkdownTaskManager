"""
Project Assessment Orchestrator (Workflow 1)

Week 69: Gestandaardiseerde Project Workflows
Orchestrates the complete project health assessment workflow:
1. Registration (ApplicationRegistry scan)
2. AS-IS Architecture (Miguel agent)
3. Code Analysis (CodeRAG)
4. Security Analysis (Quinn)
5. Quality Analysis (Quinn)
6. Health Report Generation (Diana)

This is the standalone analysis workflow that can be used without migration planning.

Author: Claude Code (Week 69)
Date: 2025-12-15
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project_assessment import ProjectAssessment, AssessmentPhase
from app.services.asis_architecture_service import get_asis_architecture_service, ASISArchitecture
from app.services.stack_detection_service import StackDetectionService

logger = logging.getLogger(__name__)

# Optional: LLM Provider for agent reasoning
try:
    from app.providers.registry import get_provider_registry
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM Provider not available. Running in rule-based mode.")

# Optional: ChromaDB for historical context
try:
    from app.services.chroma_service import get_chroma_service
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Running without historical context.")

# Optional: Knowledge Graph for code understanding (Week 74)
try:
    from app.services.knowledge_graph_service import KnowledgeGraphService, EntityType
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GRAPH_AVAILABLE = False
    logger.warning("KnowledgeGraphService not available. Running with basic code analysis.")

# Week 113 FIX-2: QualityScanService for real quality scanning
try:
    from app.services.quality_scan_service import QualityScanService
    QUALITY_SCAN_AVAILABLE = True
except ImportError:
    QUALITY_SCAN_AVAILABLE = False
    logger.warning("QualityScanService not available. Running with basic quality metrics.")

# Week 113 FIX-3: CodeRAGService for semantic code analysis (all languages)
try:
    from app.services.code_rag_service import CodeRAGService
    CODE_RAG_AVAILABLE = True
except ImportError:
    CODE_RAG_AVAILABLE = False
    logger.warning("CodeRAGService not available. Running without semantic code indexing.")

# Week 113 FIX-5: DeepExtractionService for requirements extraction
try:
    from app.services.deep_extraction_service import DeepExtractionService
    from app.models.deep_extraction import ExtractionTier
    DEEP_EXTRACTION_AVAILABLE = True
except ImportError:
    DEEP_EXTRACTION_AVAILABLE = False
    logger.warning("DeepExtractionService not available. Running without requirements extraction.")


@dataclass
class PhaseResult:
    """Result from a single assessment phase"""
    success: bool
    phase_name: str
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: int = 0
    items_processed: int = 0
    items_found: int = 0


@dataclass
class VerboseConfig:
    """Configuration for verbose workflow logging.

    Week 113: Added to enable detailed step-by-step logging of workflow execution.

    Usage:
        orchestrator = ProjectAssessmentOrchestrator(db, verbose=VerboseConfig(enabled=True))
        # or simply:
        orchestrator = ProjectAssessmentOrchestrator(db, verbose=True)
    """
    enabled: bool = False
    log_input: bool = True       # Log phase input parameters
    log_steps: bool = True       # Log intermediate steps within phases
    log_output: bool = True      # Log phase output/results
    log_timing: bool = True      # Log timing for each step
    log_to_file: bool = False    # Also write to a log file
    log_file_path: Optional[str] = None  # Path to log file if log_to_file=True
    include_data_samples: bool = True    # Include sample data in logs (truncated)
    max_sample_length: int = 500         # Max length for sample data


@dataclass
class VerboseLogEntry:
    """A single verbose log entry for workflow tracing."""
    timestamp: str
    phase: str
    step: str
    level: str  # INPUT, STEP, OUTPUT, ERROR, TIMING
    message: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None


class ProjectAssessmentOrchestrator:
    """
    Orchestrates Workflow 1: Project Analysis

    This workflow performs a comprehensive health check on an existing project
    without migration planning. It can be used standalone or as a prerequisite
    for Workflow 2 (Migration Planning).

    Phases:
    1. Registration - Scan and register project in ApplicationRegistry
    2. AS-IS Architecture - Analyze current architecture patterns (Miguel)
    3. Code Analysis - Analyze code quality and patterns (CodeRAG)
    4. Security Analysis - OWASP Top 10 security scan (Quinn)
    5. Quality Analysis - Code quality and tech debt (Quinn)
    6. Report Generation - Create health summary (Diana)
    """

    def __init__(
        self,
        db: AsyncSession,
        use_llm: bool = False,
        verbose: Optional[VerboseConfig | bool] = None
    ):
        self.db = db
        # StackDetectionService is created per-assessment with the actual repo path
        self.asis_service = get_asis_architecture_service()
        self.use_llm = use_llm and LLM_AVAILABLE

        # Week 113: Initialize verbose mode
        if verbose is True:
            self.verbose = VerboseConfig(enabled=True)
        elif isinstance(verbose, VerboseConfig):
            self.verbose = verbose
        else:
            self.verbose = VerboseConfig(enabled=False)

        self._verbose_logs: List[VerboseLogEntry] = []
        self._verbose_file = None

        if self.verbose.enabled:
            self._log_verbose("init", "SYSTEM", "Verbose mode enabled", {
                "log_input": self.verbose.log_input,
                "log_steps": self.verbose.log_steps,
                "log_output": self.verbose.log_output,
                "log_timing": self.verbose.log_timing
            })
            if self.verbose.log_to_file and self.verbose.log_file_path:
                try:
                    self._verbose_file = open(self.verbose.log_file_path, 'a')
                    self._log_verbose("init", "SYSTEM", f"Logging to file: {self.verbose.log_file_path}")
                except Exception as e:
                    logger.warning(f"Could not open verbose log file: {e}")

        # Initialize ChromaDB for historical context
        self.chroma = None
        if CHROMA_AVAILABLE:
            try:
                self.chroma = get_chroma_service()
                logger.info("ChromaDB service initialized for historical context")
                self._log_verbose("init", "SYSTEM", "ChromaDB initialized")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}")
                self._log_verbose("init", "ERROR", f"ChromaDB init failed: {e}")

        # Initialize LLM provider if requested
        self.llm_provider = None
        if self.use_llm:
            try:
                registry = get_provider_registry()
                self.llm_provider = registry.get_provider("ollama")  # Default to local
                logger.info("LLM provider initialized for agent reasoning")
                self._log_verbose("init", "SYSTEM", "LLM provider initialized (ollama)")
            except Exception as e:
                logger.warning(f"LLM provider initialization failed: {e}")
                self._log_verbose("init", "ERROR", f"LLM init failed: {e}")
                self.use_llm = False

    def _log_verbose(
        self,
        phase: str,
        level: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Log a verbose entry if verbose mode is enabled.

        Args:
            phase: Current phase name (e.g., 'registration', 'security')
            level: Log level (INPUT, STEP, OUTPUT, ERROR, TIMING, SYSTEM)
            message: Human-readable message
            data: Optional data to include (will be truncated if too large)
            duration_ms: Optional duration in milliseconds
        """
        if not self.verbose.enabled:
            return

        # Check if we should log this type
        if level == "INPUT" and not self.verbose.log_input:
            return
        if level == "STEP" and not self.verbose.log_steps:
            return
        if level == "OUTPUT" and not self.verbose.log_output:
            return
        if level == "TIMING" and not self.verbose.log_timing:
            return

        # Truncate data samples if needed
        log_data = None
        if data and self.verbose.include_data_samples:
            log_data = self._truncate_data(data, self.verbose.max_sample_length)

        entry = VerboseLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            phase=phase,
            step=level,
            level=level,
            message=message,
            data=log_data,
            duration_ms=duration_ms
        )

        self._verbose_logs.append(entry)

        # Format log message
        timing_str = f" [{duration_ms}ms]" if duration_ms else ""
        data_str = ""
        if log_data:
            import json
            try:
                data_str = f"\n    Data: {json.dumps(log_data, default=str, indent=2)[:500]}"
            except:
                data_str = f"\n    Data: {str(log_data)[:500]}"

        log_line = f"[VERBOSE] [{entry.timestamp}] [{phase.upper()}] [{level}]{timing_str} {message}{data_str}"

        # Log to console
        if level == "ERROR":
            logger.error(log_line)
        elif level in ("INPUT", "OUTPUT"):
            logger.info(log_line)
        else:
            logger.debug(log_line)

        # Log to file if configured
        if self._verbose_file:
            try:
                self._verbose_file.write(log_line + "\n")
                self._verbose_file.flush()
            except:
                pass

    def _truncate_data(self, data: Any, max_length: int) -> Any:
        """Truncate data to max_length for logging."""
        if isinstance(data, str):
            return data[:max_length] + "..." if len(data) > max_length else data
        elif isinstance(data, dict):
            result = {}
            total_len = 0
            for k, v in data.items():
                if total_len > max_length:
                    result["...truncated..."] = f"({len(data) - len(result)} more keys)"
                    break
                truncated = self._truncate_data(v, max_length // 4)
                result[k] = truncated
                total_len += len(str(truncated))
            return result
        elif isinstance(data, list):
            if len(data) > 10:
                return data[:10] + [f"... and {len(data) - 10} more items"]
            return data
        else:
            s = str(data)
            return s[:max_length] + "..." if len(s) > max_length else s

    def get_verbose_logs(self) -> List[Dict[str, Any]]:
        """Get all verbose log entries as dictionaries."""
        return [
            {
                "timestamp": e.timestamp,
                "phase": e.phase,
                "step": e.step,
                "level": e.level,
                "message": e.message,
                "data": e.data,
                "duration_ms": e.duration_ms
            }
            for e in self._verbose_logs
        ]

    def clear_verbose_logs(self) -> None:
        """Clear all verbose log entries."""
        self._verbose_logs = []

    def __del__(self):
        """Cleanup: close verbose log file if open."""
        if self._verbose_file:
            try:
                self._verbose_file.close()
            except:
                pass

    async def start_assessment(
        self,
        project_name: str,
        directory_path: str,
        application_id: Optional[int] = None
    ) -> ProjectAssessment:
        """
        Start a new project assessment

        Args:
            project_name: Name of the project
            directory_path: Path to the project source code
            application_id: Optional ID if already registered in ApplicationRegistry

        Returns:
            Created ProjectAssessment with 'running' status
        """
        # Validate path exists
        if not os.path.exists(directory_path):
            raise ValueError(f"Directory path does not exist: {directory_path}")

        # Create assessment record
        assessment = ProjectAssessment(
            project_name=project_name,
            directory_path=directory_path,
            application_id=application_id,
            status="running",
            current_phase="registration",
            progress_percent=0,
            started_at=datetime.utcnow()
        )

        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)

        return assessment

    async def run_assessment(self, assessment_id: UUID) -> ProjectAssessment:
        """
        Run the complete assessment workflow

        Args:
            assessment_id: ID of the assessment to run

        Returns:
            Updated ProjectAssessment with results
        """
        workflow_start = datetime.utcnow()
        self._log_verbose("workflow", "INPUT", "Starting assessment workflow", {
            "assessment_id": str(assessment_id)
        })

        # Get assessment
        result = await self.db.execute(
            select(ProjectAssessment).where(ProjectAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()

        if not assessment:
            self._log_verbose("workflow", "ERROR", f"Assessment not found: {assessment_id}")
            raise ValueError(f"Assessment not found: {assessment_id}")

        self._log_verbose("workflow", "STEP", "Assessment loaded", {
            "project_name": assessment.project_name,
            "directory": assessment.directory_path,
            "status": assessment.status
        })

        if assessment.status == "completed":
            self._log_verbose("workflow", "OUTPUT", "Assessment already completed, returning cached result")
            return assessment

        try:
            # Phase 1: Registration
            self._log_verbose("workflow", "STEP", "Starting Phase 1: Registration")
            await self._update_phase(assessment, "registration", 1)
            reg_result = await self._run_registration_phase(assessment)
            await self._save_phase_result(assessment, reg_result, 1)
            assessment.progress_percent = 16
            self._log_verbose("workflow", "STEP", f"Phase 1 complete: {reg_result.items_found} stacks detected",
                             duration_ms=reg_result.duration_seconds * 1000)

            # Phase 2: AS-IS Architecture
            self._log_verbose("workflow", "STEP", "Starting Phase 2: AS-IS Architecture")
            await self._update_phase(assessment, "as_is", 2)
            asis_result = await self._run_asis_phase(assessment)
            await self._save_phase_result(assessment, asis_result, 2)
            assessment.progress_percent = 33
            self._log_verbose("workflow", "STEP", f"Phase 2 complete: {asis_result.items_found} components",
                             duration_ms=asis_result.duration_seconds * 1000)

            # Phase 3: Code Analysis
            self._log_verbose("workflow", "STEP", "Starting Phase 3: Code Analysis")
            await self._update_phase(assessment, "code", 3)
            code_result = await self._run_code_analysis_phase(assessment)
            await self._save_phase_result(assessment, code_result, 3)
            assessment.progress_percent = 50
            self._log_verbose("workflow", "STEP", f"Phase 3 complete: {code_result.items_found} entities",
                             duration_ms=code_result.duration_seconds * 1000)

            # Phase 4: Security Analysis
            self._log_verbose("workflow", "STEP", "Starting Phase 4: Security Analysis")
            await self._update_phase(assessment, "security", 4)
            security_result = await self._run_security_phase(assessment)
            await self._save_phase_result(assessment, security_result, 4)
            assessment.progress_percent = 66
            self._log_verbose("workflow", "STEP", f"Phase 4 complete: {security_result.items_found} findings",
                             duration_ms=security_result.duration_seconds * 1000)

            # Phase 5: Quality Analysis
            self._log_verbose("workflow", "STEP", "Starting Phase 5: Quality Analysis")
            await self._update_phase(assessment, "quality", 5)
            quality_result = await self._run_quality_phase(assessment)
            await self._save_phase_result(assessment, quality_result, 5)
            assessment.progress_percent = 70
            self._log_verbose("workflow", "STEP", f"Phase 5 complete: {quality_result.items_found} issues",
                             duration_ms=quality_result.duration_seconds * 1000)

            # Phase 6: Requirements Extraction (Week 113 FIX-5)
            if DEEP_EXTRACTION_AVAILABLE:
                self._log_verbose("workflow", "STEP", "Starting Phase 6: Requirements Extraction")
                await self._update_phase(assessment, "requirements", 6)
                req_result = await self._run_requirements_phase(assessment)
                await self._save_phase_result(assessment, req_result, 6)
                self._log_verbose("workflow", "STEP", f"Phase 6 complete: {req_result.items_found} requirements",
                                 duration_ms=req_result.duration_seconds * 1000)
            else:
                self._log_verbose("workflow", "STEP", "Phase 6 skipped: DeepExtractionService not available")
            assessment.progress_percent = 85

            # Phase 7: Report Generation
            self._log_verbose("workflow", "STEP", "Starting Phase 7: Report Generation")
            await self._update_phase(assessment, "report", 7)
            report_result = await self._run_report_phase(assessment)
            await self._save_phase_result(assessment, report_result, 7)
            assessment.progress_percent = 100
            self._log_verbose("workflow", "STEP", f"Phase 7 complete: {report_result.items_found} recommendations",
                             duration_ms=report_result.duration_seconds * 1000)

            # Mark completed
            assessment.status = "completed"
            assessment.completed_at = datetime.utcnow()
            assessment.current_phase = "completed"

            # Calculate overall score and grade
            await self._calculate_overall_scores(assessment)

            await self.db.commit()

            # Calculate total workflow duration
            workflow_duration_ms = int((datetime.utcnow() - workflow_start).total_seconds() * 1000)
            self._log_verbose("workflow", "OUTPUT", "Assessment workflow completed", {
                "overall_grade": assessment.overall_grade,
                "overall_score": assessment.overall_health_score,
                "total_phases": 7,
                "blockers": len(assessment.blockers) if assessment.blockers else 0
            }, duration_ms=workflow_duration_ms)

            return assessment

        except Exception as e:
            self._log_verbose("workflow", "ERROR", f"Workflow failed: {str(e)}")
            assessment.status = "failed"
            assessment.error_message = str(e)
            await self.db.commit()
            raise

    async def _update_phase(self, assessment: ProjectAssessment, phase: str, phase_num: int):
        """Update current phase in assessment"""
        assessment.current_phase = phase
        await self.db.commit()

    async def _save_phase_result(
        self,
        assessment: ProjectAssessment,
        result: PhaseResult,
        phase_number: int
    ):
        """Save phase execution result"""
        phase = AssessmentPhase(
            assessment_id=assessment.id,
            workflow="assessment",
            phase_number=phase_number,
            phase_name=result.phase_name,
            agent_name=self._get_agent_for_phase(result.phase_name),
            status="completed" if result.success else "failed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=result.duration_seconds,
            result_summary=result.error if not result.success else f"Processed {result.items_processed} items, found {result.items_found}",
            result_data=result.data,
            error_message=result.error,
            items_processed=result.items_processed,
            items_found=result.items_found
        )
        self.db.add(phase)
        await self.db.commit()

    def _get_agent_for_phase(self, phase_name: str) -> str:
        """Get the responsible agent for each phase"""
        agent_mapping = {
            "registration": "system",
            "as_is": "miguel",
            "code": "coderag",
            "security": "quinn",
            "quality": "quinn",
            "requirements": "peter",  # Week 113 FIX-5: Peter handles requirements extraction
            "report": "diana"
        }
        return agent_mapping.get(phase_name, "unknown")

    # ========== Phase Implementations ==========

    async def _run_registration_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 1: Scan and register project"""
        start_time = datetime.utcnow()

        self._log_verbose("registration", "INPUT", "Starting registration phase", {
            "directory": assessment.directory_path,
            "project_name": assessment.project_name
        })

        try:
            # Create StackDetectionService with the actual repo path
            self._log_verbose("registration", "STEP", "Initializing StackDetectionService")
            stack_service = StackDetectionService(assessment.directory_path)

            self._log_verbose("registration", "STEP", "Scanning directory for files and tech stacks")
            scan_result = stack_service.scan()

            self._log_verbose("registration", "STEP", f"Scan complete: {scan_result.total_files} files, {scan_result.total_loc} LOC", {
                "stacks_detected": list(scan_result.stack_detections.keys()),
                "primary_stack": scan_result.primary_stack
            })

            # Update assessment with registration data
            assessment.detected_stacks = list(scan_result.stack_detections.keys())
            assessment.primary_stack = scan_result.primary_stack
            assessment.file_count = scan_result.total_files
            assessment.line_count = scan_result.total_loc

            duration = (datetime.utcnow() - start_time).seconds

            result = PhaseResult(
                success=True,
                phase_name="registration",
                data={
                    "detected_stacks": assessment.detected_stacks,
                    "primary_stack": assessment.primary_stack,
                    "file_count": assessment.file_count,
                    "line_count": assessment.line_count,
                    "file_inventory": dict(scan_result.file_inventory)
                },
                duration_seconds=duration,
                items_processed=scan_result.total_files,
                items_found=len(scan_result.stack_detections)
            )

            self._log_verbose("registration", "OUTPUT", "Registration phase complete", {
                "detected_stacks": assessment.detected_stacks,
                "file_count": assessment.file_count,
                "line_count": assessment.line_count
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("registration", "ERROR", f"Registration failed: {str(e)}")
            return PhaseResult(
                success=False,
                phase_name="registration",
                data={},
                error=str(e)
            )

    async def _run_asis_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 2: AS-IS Architecture Analysis (Miguel)"""
        start_time = datetime.utcnow()

        self._log_verbose("as_is", "INPUT", "Starting AS-IS architecture analysis", {
            "directory": assessment.directory_path,
            "primary_stack": assessment.primary_stack
        })

        try:
            # Run Miguel's AS-IS analysis
            self._log_verbose("as_is", "STEP", "Running Miguel's architecture analyzer")
            asis_result = self.asis_service.analyze(assessment.directory_path)

            self._log_verbose("as_is", "STEP", f"Architecture analysis complete", {
                "pattern": asis_result.detected_pattern.value,
                "confidence": f"{asis_result.pattern_confidence:.0%}",
                "layers": len(asis_result.layers),
                "components": len(asis_result.components),
                "issues": len(asis_result.issues)
            })

            # Get historical context from ChromaDB (similar projects)
            similar_projects = []
            if self.chroma:
                try:
                    self._log_verbose("as_is", "STEP", "Querying ChromaDB for similar projects")
                    context_query = f"{assessment.primary_stack or ''} {asis_result.detected_pattern.value}"
                    similar = self.chroma.find_similar_projects(
                        project_description=context_query,
                        top_k=3
                    )
                    similar_projects = similar.get("similar_projects", [])
                    self._log_verbose("as_is", "STEP", f"Found {len(similar_projects)} similar projects")
                    logger.info(f"Found {len(similar_projects)} similar historical projects")
                except Exception as e:
                    self._log_verbose("as_is", "STEP", f"ChromaDB lookup failed: {e}")
                    logger.warning(f"Historical context lookup failed: {e}")

            # Optional: LLM-enhanced analysis (Miguel agent reasoning)
            llm_insights = None
            if self.use_llm and self.llm_provider:
                try:
                    self._log_verbose("as_is", "STEP", "Getting Miguel's LLM insights")
                    llm_insights = await self._get_miguel_insights(asis_result, similar_projects)
                    self._log_verbose("as_is", "STEP", "LLM insights generated", llm_insights)
                except Exception as e:
                    self._log_verbose("as_is", "STEP", f"LLM insight generation failed: {e}")
                    logger.warning(f"LLM insight generation failed: {e}")

            # Update assessment with architecture data
            assessment.as_is_architecture = asis_result.to_dict()
            assessment.architecture_pattern = asis_result.detected_pattern.value
            assessment.architecture_layers = [
                {"name": l.name, "type": l.layer_type.value, "files": l.file_count}
                for l in asis_result.layers
            ]
            assessment.architecture_components = [
                {"name": c.name, "type": c.component_type, "layer": c.layer}
                for c in asis_result.components[:50]  # Limit to 50
            ]
            assessment.architecture_score = asis_result.architecture_score
            assessment.architecture_issues = [
                {"type": i.issue_type, "severity": i.severity, "title": i.title, "description": i.description}
                for i in asis_result.issues
            ]

            # Add historical context and LLM insights to result
            result_data = asis_result.to_dict()
            result_data["similar_projects"] = [
                {"name": p.get("metadata", {}).get("project_name", "Unknown"), "similarity": p.get("similarity", 0)}
                for p in similar_projects
            ]
            if llm_insights:
                result_data["llm_insights"] = llm_insights

            duration = (datetime.utcnow() - start_time).seconds

            result = PhaseResult(
                success=True,
                phase_name="as_is",
                data=result_data,
                duration_seconds=duration,
                items_processed=asis_result.total_files,
                items_found=len(asis_result.components)
            )

            self._log_verbose("as_is", "OUTPUT", "AS-IS analysis complete", {
                "architecture_pattern": assessment.architecture_pattern,
                "architecture_score": assessment.architecture_score,
                "layers": len(asis_result.layers),
                "components_found": len(asis_result.components),
                "issues_found": len(asis_result.issues)
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("as_is", "ERROR", f"AS-IS analysis failed: {str(e)}")
            return PhaseResult(
                success=False,
                phase_name="as_is",
                data={},
                error=str(e)
            )

    async def _get_miguel_insights(
        self,
        asis_result: ASISArchitecture,
        similar_projects: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Get Miguel agent's LLM-enhanced architecture insights"""
        if not self.llm_provider:
            return None

        prompt = f"""You are Miguel, the Migration Architect agent. Analyze this architecture:

**Detected Pattern**: {asis_result.detected_pattern.value}
**Confidence**: {asis_result.pattern_confidence:.0%}
**Architecture Score**: {asis_result.architecture_score}/100
**Layers**: {len(asis_result.layers)}
**Components**: {len(asis_result.components)}
**Issues**: {len(asis_result.issues)}

Top Issues:
{chr(10).join(f"- [{i.severity}] {i.title}" for i in asis_result.issues[:5])}

Similar Historical Projects:
{chr(10).join(f"- {p.get('metadata', {}).get('project_name', 'Unknown')} (similarity: {p.get('similarity', 0):.0%})" for p in similar_projects[:3]) if similar_projects else "No similar projects found"}

Provide a brief analysis (2-3 sentences) covering:
1. Architecture health assessment
2. Migration readiness
3. Key recommendations

Respond in JSON format:
{{"health_assessment": "...", "migration_readiness": "low|medium|high", "key_recommendation": "..."}}"""

        try:
            response = await self.llm_provider.generate(prompt)
            # Parse JSON from response
            import json
            # Find JSON in response
            json_match = response.find('{')
            if json_match >= 0:
                json_end = response.rfind('}') + 1
                return json.loads(response[json_match:json_end])
        except Exception as e:
            logger.warning(f"Miguel insight parsing failed: {e}")
        return None

    async def _run_code_analysis_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 3: Code Analysis (CodeRAG + Knowledge Graph)

        Week 74 Enhancement: Integrates KnowledgeGraphService for deep code understanding:
        - Class hierarchy extraction
        - Import dependency graph
        - Method complexity analysis
        - Cross-file relationships
        """
        start_time = datetime.utcnow()

        self._log_verbose("code", "INPUT", "Starting code analysis phase", {
            "directory": assessment.directory_path,
            "file_count": assessment.file_count,
            "primary_stack": assessment.primary_stack
        })

        try:
            code_analysis = {
                "patterns_detected": [],
                "dependencies": [],
                "complexity": {},
                "duplication": None,
                "test_coverage": None,
                # Week 74 additions
                "class_count": 0,
                "function_count": 0,
                "method_count": 0,
                "import_count": 0,
                "class_hierarchy": [],
                "module_dependencies": [],
                "complexity_hotspots": [],
                "knowledge_graph_summary": None
            }

            # Try to detect test coverage from common patterns
            test_files = 0
            total_files = assessment.file_count or 1

            for root, dirs, files in os.walk(assessment.directory_path):
                for f in files:
                    if "test" in f.lower() or "_test" in f.lower() or "spec" in f.lower():
                        test_files += 1

            if test_files > 0:
                code_analysis["test_coverage"] = min(100, (test_files / total_files) * 300)

            # Week 74: Knowledge Graph Analysis
            if KNOWLEDGE_GRAPH_AVAILABLE:
                try:
                    self._log_verbose("code", "STEP", "Initializing Knowledge Graph service")
                    kg_service = KnowledgeGraphService(self.db)

                    # Build the knowledge graph for the project
                    self._log_verbose("code", "STEP", "Building knowledge graph from source code")
                    await asyncio.to_thread(
                        kg_service.build_graph,
                        assessment.directory_path,
                        assessment.id or 0,
                        ["python"]  # Start with Python support
                    )

                    # Extract entity counts
                    classes = kg_service.get_entities_by_type(EntityType.CLASS)
                    functions = kg_service.get_entities_by_type(EntityType.FUNCTION)
                    methods = kg_service.get_entities_by_type(EntityType.METHOD)
                    imports = kg_service.get_entities_by_type(EntityType.IMPORT)
                    modules = kg_service.get_entities_by_type(EntityType.MODULE)

                    code_analysis["class_count"] = len(classes)
                    code_analysis["function_count"] = len(functions)
                    code_analysis["method_count"] = len(methods)
                    code_analysis["import_count"] = len(imports)

                    # Extract class hierarchy (top 10 most connected)
                    class_hierarchy = []
                    for cls in classes[:10]:
                        hierarchy = kg_service.get_class_hierarchy(cls.name)
                        if hierarchy:
                            class_hierarchy.append({
                                "name": cls.name,
                                "file": cls.file_path,
                                "bases": hierarchy.get("bases", []),
                                "method_count": len([m for m in methods if cls.name in m.name])
                            })
                    code_analysis["class_hierarchy"] = class_hierarchy

                    # Extract module dependencies (imports between modules)
                    module_deps = []
                    for module in modules[:20]:
                        deps = kg_service.get_relations_for_entity(module.id, direction="outgoing")
                        if deps:
                            module_deps.append({
                                "module": module.name,
                                "imports": [d.target_id.split(":")[-1] for d in deps[:5]]
                            })
                    code_analysis["module_dependencies"] = module_deps

                    # Find complexity hotspots (functions/methods with most incoming references)
                    hotspots = []
                    for func in (functions + methods)[:50]:
                        refs = kg_service.get_relations_for_entity(func.id, direction="incoming")
                        if len(refs) > 3:
                            hotspots.append({
                                "name": func.name,
                                "file": func.file_path,
                                "reference_count": len(refs),
                                "complexity": func.metadata.get("complexity", "unknown")
                            })
                    # Sort by reference count
                    hotspots.sort(key=lambda x: x["reference_count"], reverse=True)
                    code_analysis["complexity_hotspots"] = hotspots[:10]

                    # Summary statistics
                    code_analysis["knowledge_graph_summary"] = {
                        "total_entities": len(kg_service._entities),
                        "total_relations": len(kg_service._relations),
                        "modules_analyzed": len(modules),
                        "average_methods_per_class": round(len(methods) / max(len(classes), 1), 1)
                    }

                    # Update dependencies list from imports
                    external_deps = set()
                    for imp in imports:
                        module_name = imp.name.split(".")[0]
                        if module_name not in ["os", "sys", "typing", "datetime", "json", "re"]:
                            external_deps.add(module_name)
                    code_analysis["dependencies"] = list(external_deps)[:20]

                    self._log_verbose("code", "STEP", f"Knowledge Graph complete", {
                        "classes": len(classes),
                        "functions": len(functions),
                        "methods": len(methods),
                        "imports": len(imports),
                        "modules": len(modules)
                    })
                    logger.info(f"Knowledge Graph analysis complete: {len(classes)} classes, {len(functions)} functions")

                except Exception as kg_error:
                    self._log_verbose("code", "STEP", f"Knowledge Graph failed: {kg_error}")
                    logger.warning(f"Knowledge Graph analysis failed: {kg_error}")
                    code_analysis["knowledge_graph_summary"] = {"error": str(kg_error)}

            # Week 113 FIX-3: CodeRAGService for semantic indexing (all 15+ languages)
            if CODE_RAG_AVAILABLE:
                try:
                    self._log_verbose("code", "STEP", "Initializing CodeRAG service")
                    code_rag = CodeRAGService()

                    if code_rag.is_available:
                        self._log_verbose("code", "STEP", f"Indexing repository with CodeRAG")
                        logger.info(f"Indexing repository with CodeRAG: {assessment.directory_path}")

                        # Index the repository for semantic search
                        rag_stats = await asyncio.to_thread(
                            code_rag.index_repository,
                            assessment.directory_path,
                            assessment.id
                        )

                        if "error" not in rag_stats:
                            code_analysis["code_rag"] = {
                                "indexed": True,
                                "files_processed": rag_stats.get("files_processed", 0),
                                "chunks_created": rag_stats.get("chunks_created", 0),
                                "languages_detected": rag_stats.get("languages", {}),
                                "errors": len(rag_stats.get("errors", []))
                            }

                            # Update language breakdown
                            languages = rag_stats.get("languages", {})
                            if languages:
                                code_analysis["language_breakdown"] = languages
                                # Most common language
                                primary_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else None
                                if primary_lang:
                                    code_analysis["primary_language"] = primary_lang

                            self._log_verbose("code", "STEP", f"CodeRAG indexing complete", {
                                "files_processed": rag_stats.get('files_processed', 0),
                                "chunks_created": rag_stats.get('chunks_created', 0),
                                "languages": list(languages.keys())
                            })
                            logger.info(
                                f"CodeRAG indexed {rag_stats.get('files_processed', 0)} files, "
                                f"{rag_stats.get('chunks_created', 0)} chunks across {len(languages)} languages"
                            )
                        else:
                            self._log_verbose("code", "STEP", f"CodeRAG indexing failed: {rag_stats.get('error', 'unknown')}")
                            code_analysis["code_rag"] = {"indexed": False, "error": rag_stats["error"]}
                    else:
                        self._log_verbose("code", "STEP", "CodeRAG unavailable: ChromaDB not available")
                        code_analysis["code_rag"] = {"indexed": False, "error": "ChromaDB not available"}

                except Exception as rag_error:
                    self._log_verbose("code", "STEP", f"CodeRAG exception: {rag_error}")
                    logger.warning(f"CodeRAG indexing failed: {rag_error}")
                    code_analysis["code_rag"] = {"indexed": False, "error": str(rag_error)}
            else:
                self._log_verbose("code", "STEP", "CodeRAG skipped: service not installed")
                code_analysis["code_rag"] = {"indexed": False, "error": "CodeRAGService not installed"}

            # Update assessment with all metrics
            assessment.code_analysis = code_analysis
            assessment.code_patterns = code_analysis["patterns_detected"]
            assessment.code_dependencies = code_analysis["dependencies"]
            assessment.code_complexity = code_analysis["complexity"]
            assessment.code_test_coverage_percent = code_analysis["test_coverage"]

            duration = (datetime.utcnow() - start_time).seconds

            # items_found includes: test files + KG entities
            total_found = test_files + code_analysis.get("class_count", 0) + code_analysis.get("function_count", 0)

            result = PhaseResult(
                success=True,
                phase_name="code",
                data=code_analysis,
                duration_seconds=duration,
                items_processed=assessment.file_count or 0,
                items_found=max(total_found, test_files)  # At minimum, report test files found
            )

            self._log_verbose("code", "OUTPUT", "Code analysis phase complete", {
                "classes": code_analysis.get("class_count", 0),
                "functions": code_analysis.get("function_count", 0),
                "test_coverage": code_analysis.get("test_coverage"),
                "coderag_indexed": code_analysis.get("code_rag", {}).get("indexed", False),
                "languages": list(code_analysis.get("language_breakdown", {}).keys())
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("code", "ERROR", f"Code analysis failed: {str(e)}")
            logger.error(f"Code analysis phase failed: {e}")
            return PhaseResult(
                success=False,
                phase_name="code",
                data={},
                error=str(e)
            )

    async def _run_security_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 4: Security Analysis (Quinn)

        Week 113 Fix: Now properly calls MigrationSecurityService.analyze_directory()
        instead of non-existent scan_security() method.
        """
        start_time = datetime.utcnow()

        self._log_verbose("security", "INPUT", "Starting security analysis phase", {
            "directory": assessment.directory_path,
            "file_count": assessment.file_count
        })

        try:
            # Use MigrationSecurityService for OWASP pattern scanning
            self._log_verbose("security", "STEP", "Initializing MigrationSecurityService")
            from app.services.migration_security_service import (
                get_migration_security_service,
                SecuritySeverity
            )
            security_service = get_migration_security_service()

            # Run actual security analysis on the directory
            self._log_verbose("security", "STEP", "Running OWASP pattern scanning")
            security_result = security_service.analyze_directory(
                directory=assessment.directory_path,
                stacks=None,  # Auto-detect stacks
                severity_threshold=SecuritySeverity.LOW
            )

            self._log_verbose("security", "STEP", f"Security scan complete", {
                "findings_count": len(security_result.findings),
                "files_scanned": security_result.files_scanned,
                "risk_score": security_result.risk_score.total_score
            })

            # Map findings to assessment format
            findings_list = []
            for finding in security_result.findings:
                findings_list.append({
                    "pattern_id": finding.pattern_id,
                    "pattern_name": finding.pattern_name,
                    "owasp_category": finding.owasp_category.value,
                    "severity": finding.severity.value,
                    "file_path": finding.file_path,
                    "line_number": finding.line_number,
                    "code_snippet": finding.code_snippet[:200] if finding.code_snippet else "",
                    "description": finding.description,
                    "remediation": finding.remediation,
                    "cwe_id": finding.cwe_id,
                    "confidence": finding.confidence
                })

            assessment.security_findings = findings_list
            assessment.security_finding_count = len(findings_list)
            assessment.security_critical_count = security_result.risk_score.critical_count
            assessment.security_high_count = security_result.risk_score.high_count
            assessment.security_medium_count = security_result.risk_score.medium_count
            assessment.security_low_count = security_result.risk_score.low_count
            assessment.security_risk_score = security_result.risk_score.total_score
            assessment.owasp_coverage = security_result.risk_score.owasp_coverage

            # Calculate grade based on risk score
            risk = security_result.risk_score.total_score
            if risk <= 20:
                assessment.security_grade = "A"
            elif risk <= 40:
                assessment.security_grade = "B"
            elif risk <= 60:
                assessment.security_grade = "C"
            elif risk <= 80:
                assessment.security_grade = "D"
            else:
                assessment.security_grade = "F"

            # Store Quinn context for detailed review
            assessment.security_findings.append({
                "_quinn_context": {
                    "summary": security_result.quinn_context.summary,
                    "focus_areas": security_result.quinn_context.focus_areas,
                    "priority_files": security_result.quinn_context.priority_files[:10],
                    "recommended_tools": security_result.quinn_context.recommended_tools
                }
            })

            duration = (datetime.utcnow() - start_time).seconds

            logger.info(f"Security scan completed: {len(findings_list)} findings, grade {assessment.security_grade}")

            result = PhaseResult(
                success=True,
                phase_name="security",
                data={
                    "findings": findings_list,
                    "grade": assessment.security_grade,
                    "risk_score": assessment.security_risk_score,
                    "owasp_coverage": assessment.owasp_coverage,
                    "recommendations": security_result.recommendations
                },
                duration_seconds=duration,
                items_processed=assessment.file_count or 0,
                items_found=len(findings_list)
            )

            self._log_verbose("security", "OUTPUT", "Security analysis complete", {
                "grade": assessment.security_grade,
                "risk_score": assessment.security_risk_score,
                "findings": len(findings_list),
                "critical": assessment.security_critical_count,
                "high": assessment.security_high_count,
                "medium": assessment.security_medium_count,
                "low": assessment.security_low_count
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("security", "ERROR", f"Security analysis failed: {str(e)}")
            logger.error(f"Security phase failed: {e}")
            return PhaseResult(
                success=False,
                phase_name="security",
                data={},
                error=str(e)
            )

    async def _run_quality_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 5: Quality Analysis (Quinn)

        Week 113 FIX-2: Now uses QualityScanService for real code scanning
        instead of only using architecture issues as baseline.
        """
        start_time = datetime.utcnow()

        self._log_verbose("quality", "INPUT", "Starting quality analysis phase", {
            "directory": assessment.directory_path,
            "primary_stack": assessment.primary_stack,
            "detected_stacks": assessment.detected_stacks
        })

        try:
            quality_issues = []
            tech_debt_hours = 0
            scanner_results = {}
            files_scanned = 0

            # Week 113 FIX-2: Run actual quality scan using QualityScanService
            if QUALITY_SCAN_AVAILABLE:
                try:
                    self._log_verbose("quality", "STEP", "Initializing QualityScanService")
                    quality_scanner = QualityScanService()

                    # Detect tech stack from assessment or auto-detect
                    tech_stack = None
                    if assessment.primary_stack:
                        tech_stack = [assessment.primary_stack]
                        if assessment.detected_stacks:
                            tech_stack.extend(assessment.detected_stacks)

                    self._log_verbose("quality", "STEP", f"Running quality scan with stack: {tech_stack}")
                    logger.info(f"Running quality scan on {assessment.directory_path} with stack: {tech_stack}")

                    # Run the actual scan
                    scan_result = await quality_scanner.run_scan(
                        project_path=assessment.directory_path,
                        tech_stack=tech_stack
                    )

                    self._log_verbose("quality", "STEP", "Quality scan complete", {
                        "success": scan_result.get("success", True),
                        "files_scanned": scan_result.get("metrics", {}).get("files_scanned", 0),
                        "total_findings": len(scan_result.get("all_findings", []))
                    })

                    # Extract findings from scan result
                    if scan_result.get("success", True):
                        scanner_results = scan_result
                        files_scanned = scan_result.get("metrics", {}).get("files_scanned", 0)

                        # Convert scan findings to quality issues
                        for finding in scan_result.get("all_findings", []):
                            quality_issues.append({
                                "type": finding.get("type", "code_quality"),
                                "severity": finding.get("severity", "medium"),
                                "title": finding.get("rule_id", finding.get("message", "Unknown issue")[:50]),
                                "description": finding.get("message", ""),
                                "file": finding.get("file_path", ""),
                                "line": finding.get("line_number", 0),
                                "scanner": finding.get("scanner", "unknown"),
                                "recommendation": finding.get("recommendation", "")
                            })

                            # Calculate tech debt based on severity
                            severity = finding.get("severity", "medium").lower()
                            if severity == "critical":
                                tech_debt_hours += 8  # Critical issues take longest
                            elif severity == "high":
                                tech_debt_hours += 4
                            elif severity == "medium":
                                tech_debt_hours += 2
                            else:
                                tech_debt_hours += 0.5

                        # Use scanner's quality score if available
                        if "scores" in scan_result:
                            scanner_quality_score = scan_result["scores"].get("quality", 0)
                            scanner_security_score = scan_result["scores"].get("security", 0)

                        self._log_verbose("quality", "STEP", f"Findings extracted: {len(quality_issues)} issues")
                        logger.info(f"Quality scan complete: {len(quality_issues)} findings from {files_scanned} files")

                except Exception as scan_error:
                    self._log_verbose("quality", "STEP", f"Quality scan failed, using fallback: {scan_error}")
                    logger.warning(f"Quality scan failed, falling back to basic metrics: {scan_error}")

            # Also include architecture issues as quality indicators
            if assessment.architecture_issues:
                for issue in assessment.architecture_issues:
                    quality_issues.append({
                        "type": "architecture",
                        "severity": issue.get("severity", "medium"),
                        "title": issue.get("title", "Unknown issue"),
                        "description": issue.get("description", ""),
                        "scanner": "architecture_analyzer"
                    })
                    # Estimate tech debt hours based on severity
                    if issue.get("severity") == "critical":
                        tech_debt_hours += 40
                    elif issue.get("severity") == "high":
                        tech_debt_hours += 16
                    elif issue.get("severity") == "medium":
                        tech_debt_hours += 8
                    else:
                        tech_debt_hours += 4

            # Calculate maintainability index
            lines = assessment.line_count or 1000
            arch_score = assessment.architecture_score or 50

            # Adjusted calculation: also factor in quality issues
            issue_penalty = min(30, len(quality_issues) * 0.5)  # Max 30 point penalty
            maintainability = 100 - (lines / 10000) * 20 + (arch_score - 50) * 0.5 - issue_penalty
            maintainability = max(0, min(100, maintainability))

            # Calculate quality score based on findings and scanner results
            if scanner_results.get("scores", {}).get("overall"):
                quality_score = int(scanner_results["scores"]["overall"])
            else:
                # Fallback calculation
                quality_score = int(100 - len(quality_issues) * 2 - (tech_debt_hours / 20))
            quality_score = max(0, min(100, quality_score))

            # Determine grade
            if quality_score >= 90:
                quality_grade = "A"
            elif quality_score >= 75:
                quality_grade = "B"
            elif quality_score >= 60:
                quality_grade = "C"
            elif quality_score >= 40:
                quality_grade = "D"
            else:
                quality_grade = "F"

            # Count by severity for reporting
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            for issue in quality_issues:
                sev = issue.get("severity", "medium").lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1

            # Update assessment
            assessment.quality_report = {
                "issues": quality_issues,
                "tech_debt_hours": tech_debt_hours,
                "maintainability_index": maintainability,
                "scanner_results": scanner_results,
                "files_scanned": files_scanned,
                "severity_breakdown": severity_counts
            }
            assessment.quality_issues = quality_issues
            assessment.quality_issue_count = len(quality_issues)
            assessment.tech_debt_hours = tech_debt_hours
            assessment.maintainability_index = maintainability
            assessment.quality_score = quality_score
            assessment.quality_grade = quality_grade

            duration = (datetime.utcnow() - start_time).seconds

            result = PhaseResult(
                success=True,
                phase_name="quality",
                data={
                    "issues": quality_issues,
                    "score": quality_score,
                    "grade": quality_grade,
                    "tech_debt_hours": tech_debt_hours,
                    "files_scanned": files_scanned,
                    "severity_breakdown": severity_counts,
                    "scanner_used": QUALITY_SCAN_AVAILABLE
                },
                duration_seconds=duration,
                items_processed=files_scanned or assessment.file_count or 0,
                items_found=len(quality_issues)
            )

            self._log_verbose("quality", "OUTPUT", "Quality analysis complete", {
                "grade": quality_grade,
                "score": quality_score,
                "total_issues": len(quality_issues),
                "tech_debt_hours": tech_debt_hours,
                "files_scanned": files_scanned,
                "severity_breakdown": severity_counts
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("quality", "ERROR", f"Quality analysis failed: {str(e)}")
            logger.error(f"Quality phase failed: {e}")
            return PhaseResult(
                success=False,
                phase_name="quality",
                data={},
                error=str(e)
            )

    async def _run_requirements_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 6: Requirements Extraction (Peter + Deep Extraction Pipeline)

        Week 113 FIX-5: Connect DeepExtractionService to Workflow 1
        Extracts business rules, functional requirements, and non-functional requirements
        from source code using the 6-cycle hybrid extraction pipeline.
        """
        start_time = datetime.utcnow()

        self._log_verbose("requirements", "INPUT", "Starting requirements extraction phase", {
            "directory": assessment.directory_path,
            "line_count": assessment.line_count,
            "deep_extraction_available": DEEP_EXTRACTION_AVAILABLE
        })

        try:
            extraction_results = {
                "epics_found": 0,
                "features_found": 0,
                "stories_found": 0,
                "nfr_count": 0,
                "business_rules_found": 0,
                "extraction_tier": "BASIC",
                "extraction_session_id": None,
                "extraction_status": "not_started"
            }

            if not DEEP_EXTRACTION_AVAILABLE:
                self._log_verbose("requirements", "OUTPUT", "Requirements phase skipped: service not available")
                return PhaseResult(
                    success=True,
                    phase_name="requirements",
                    data={"skipped": True, "reason": "DeepExtractionService not available"},
                    duration_seconds=0,
                    items_processed=0,
                    items_found=0
                )

            try:
                # Initialize DeepExtractionService with db session
                self._log_verbose("requirements", "STEP", "Initializing DeepExtractionService")
                deep_service = DeepExtractionService(self.db)

                # Determine tier based on project size and tier config
                lines = assessment.line_count or 1000
                if lines > 100000:
                    extraction_tier = ExtractionTier.STANDARD
                elif lines > 500000:
                    extraction_tier = ExtractionTier.PROFESSIONAL
                else:
                    extraction_tier = ExtractionTier.BASIC

                extraction_results["extraction_tier"] = extraction_tier.value

                self._log_verbose("requirements", "STEP", f"Extraction tier determined: {extraction_tier.value}", {
                    "line_count": lines,
                    "tier": extraction_tier.value
                })
                logger.info(
                    f"Starting requirements extraction for {assessment.project_name} "
                    f"with tier {extraction_tier.value}"
                )

                # Start extraction session
                # Note: DeepExtractionService needs a project_id from the database
                # We use assessment.id as a reference
                self._log_verbose("requirements", "STEP", "Starting extraction session")
                extraction_session = await deep_service.start_extraction(
                    project_id=assessment.id,
                    source_path=assessment.directory_path,
                    tier=extraction_tier
                )

                if extraction_session:
                    extraction_results["extraction_session_id"] = str(extraction_session.id)
                    extraction_results["extraction_status"] = "started"
                    self._log_verbose("requirements", "STEP", f"Extraction session started: {extraction_session.id}")

                    # Run Cycle 0 (Static Analysis) and Cycle 1 (Independent Analysis)
                    # Full extraction is async and may take time, so we just trigger it
                    try:
                        # Run static analysis (Cycle 0)
                        self._log_verbose("requirements", "STEP", "Running Cycle 0: Static Analysis")
                        await deep_service.run_cycle_0(extraction_session.id)

                        # For now, just mark as "in_progress" - full extraction is async
                        extraction_results["extraction_status"] = "cycle_0_complete"

                        # Get preliminary results from static analysis
                        session_after_c0 = await deep_service.get_session(extraction_session.id)
                        if session_after_c0 and session_after_c0.static_analysis_results:
                            static_results = session_after_c0.static_analysis_results
                            extraction_results["business_rules_found"] = static_results.get(
                                "business_rules_count", 0
                            )
                            extraction_results["nfr_count"] = static_results.get(
                                "nfr_count", 0
                            )

                        self._log_verbose("requirements", "STEP", "Cycle 0 complete", {
                            "business_rules": extraction_results['business_rules_found'],
                            "nfrs": extraction_results['nfr_count']
                        })
                        logger.info(
                            f"Cycle 0 complete: {extraction_results['business_rules_found']} "
                            f"business rules, {extraction_results['nfr_count']} NFRs"
                        )

                    except Exception as cycle_error:
                        self._log_verbose("requirements", "STEP", f"Cycle error: {cycle_error}")
                        logger.warning(f"Extraction cycle error: {cycle_error}")
                        extraction_results["extraction_status"] = "cycle_error"
                        extraction_results["error"] = str(cycle_error)

            except Exception as deep_error:
                self._log_verbose("requirements", "STEP", f"Deep extraction failed: {deep_error}")
                logger.warning(f"Deep extraction failed: {deep_error}")
                extraction_results["extraction_status"] = "failed"
                extraction_results["error"] = str(deep_error)

            # Store results in assessment
            if not hasattr(assessment, 'requirements_extraction') or assessment.requirements_extraction is None:
                assessment.requirements_extraction = {}
            assessment.requirements_extraction = extraction_results

            duration = (datetime.utcnow() - start_time).seconds

            total_found = (
                extraction_results.get("epics_found", 0) +
                extraction_results.get("features_found", 0) +
                extraction_results.get("stories_found", 0) +
                extraction_results.get("nfr_count", 0) +
                extraction_results.get("business_rules_found", 0)
            )

            result = PhaseResult(
                success=extraction_results.get("extraction_status") != "failed",
                phase_name="requirements",
                data=extraction_results,
                duration_seconds=duration,
                items_processed=assessment.file_count or 0,
                items_found=total_found
            )

            self._log_verbose("requirements", "OUTPUT", "Requirements extraction complete", {
                "status": extraction_results.get("extraction_status"),
                "tier": extraction_results.get("extraction_tier"),
                "epics": extraction_results.get("epics_found", 0),
                "features": extraction_results.get("features_found", 0),
                "stories": extraction_results.get("stories_found", 0),
                "nfrs": extraction_results.get("nfr_count", 0),
                "business_rules": extraction_results.get("business_rules_found", 0)
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("requirements", "ERROR", f"Requirements extraction failed: {str(e)}")
            logger.error(f"Requirements extraction phase failed: {e}")
            return PhaseResult(
                success=False,
                phase_name="requirements",
                data={"error": str(e)},
                error=str(e)
            )

    async def _run_report_phase(self, assessment: ProjectAssessment) -> PhaseResult:
        """Phase 7: Health Report Generation (Diana)"""
        start_time = datetime.utcnow()

        self._log_verbose("report", "INPUT", "Starting report generation phase", {
            "project_name": assessment.project_name,
            "architecture_score": assessment.architecture_score,
            "security_grade": assessment.security_grade,
            "quality_grade": assessment.quality_grade
        })

        try:
            self._log_verbose("report", "STEP", "Generating health summary")
            # Generate health summary
            summary_lines = [
                f"# Project Health Report: {assessment.project_name}",
                "",
                f"**Assessment Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                "",
                "## Overview",
                f"- **Primary Stack**: {assessment.primary_stack or 'Unknown'}",
                f"- **Total Files**: {assessment.file_count:,}",
                f"- **Total Lines**: {assessment.line_count:,}",
                "",
                "## Architecture",
                f"- **Pattern**: {assessment.architecture_pattern or 'Unknown'}",
                f"- **Score**: {assessment.architecture_score}/100",
                f"- **Layers**: {len(assessment.architecture_layers or [])}",
                "",
                "## Security",
                f"- **Grade**: {assessment.security_grade or 'N/A'}",
                f"- **Findings**: {assessment.security_finding_count}",
                f"  - Critical: {assessment.security_critical_count}",
                f"  - High: {assessment.security_high_count}",
                f"  - Medium: {assessment.security_medium_count}",
                f"  - Low: {assessment.security_low_count}",
                "",
                "## Quality",
                f"- **Grade**: {assessment.quality_grade or 'N/A'}",
                f"- **Score**: {assessment.quality_score}/100",
                f"- **Tech Debt**: {assessment.tech_debt_hours:.1f} hours",
                f"- **Maintainability Index**: {assessment.maintainability_index:.1f}",
            ]

            # Add recommendations
            self._log_verbose("report", "STEP", "Generating recommendations")
            recommendations = []
            if assessment.security_critical_count > 0:
                recommendations.append({
                    "category": "security",
                    "priority": "critical",
                    "title": "Critical Security Issues",
                    "description": f"Address {assessment.security_critical_count} critical security findings immediately"
                })

            if assessment.architecture_score and assessment.architecture_score < 60:
                recommendations.append({
                    "category": "architecture",
                    "priority": "high",
                    "title": "Architecture Improvements Needed",
                    "description": "Consider restructuring code to improve layer separation and reduce coupling"
                })

            if assessment.tech_debt_hours and assessment.tech_debt_hours > 100:
                recommendations.append({
                    "category": "quality",
                    "priority": "medium",
                    "title": "Technical Debt Reduction",
                    "description": f"Plan to address {assessment.tech_debt_hours:.0f} hours of technical debt"
                })

            self._log_verbose("report", "STEP", f"Generated {len(recommendations)} recommendations")
            assessment.recommendations = recommendations
            assessment.health_summary = "\n".join(summary_lines)

            # Identify blockers (critical issues that would block migration)
            self._log_verbose("report", "STEP", "Identifying migration blockers")
            blockers = []
            if assessment.security_critical_count > 5:
                blockers.append({
                    "type": "security",
                    "title": "Too many critical security issues",
                    "description": "Reduce critical security issues to below 5 before migration"
                })

            if assessment.architecture_score and assessment.architecture_score < 30:
                blockers.append({
                    "type": "architecture",
                    "title": "Architecture quality too low",
                    "description": "Improve architecture score to at least 30 before migration"
                })

            self._log_verbose("report", "STEP", f"Identified {len(blockers)} blockers")
            assessment.blockers = blockers

            duration = (datetime.utcnow() - start_time).seconds

            result = PhaseResult(
                success=True,
                phase_name="report",
                data={
                    "summary": assessment.health_summary,
                    "recommendations": recommendations,
                    "blockers": blockers
                },
                duration_seconds=duration,
                items_processed=1,
                items_found=len(recommendations) + len(blockers)
            )

            self._log_verbose("report", "OUTPUT", "Report generation complete", {
                "recommendations_count": len(recommendations),
                "blockers_count": len(blockers),
                "summary_length": len(assessment.health_summary)
            }, duration_ms=duration * 1000)

            return result

        except Exception as e:
            self._log_verbose("report", "ERROR", f"Report generation failed: {str(e)}")
            return PhaseResult(
                success=False,
                phase_name="report",
                data={},
                error=str(e)
            )

    async def _calculate_overall_scores(self, assessment: ProjectAssessment):
        """Calculate overall health score and grade"""
        scores = []
        weights = []

        # Architecture (weight: 0.30)
        if assessment.architecture_score:
            scores.append(assessment.architecture_score)
            weights.append(0.30)

        # Security (weight: 0.35)
        if assessment.security_risk_score is not None:
            # Convert risk score to health score (inverse)
            security_health = 100 - assessment.security_risk_score
            scores.append(max(0, security_health))
            weights.append(0.35)

        # Quality (weight: 0.35)
        if assessment.quality_score:
            scores.append(assessment.quality_score)
            weights.append(0.35)

        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            assessment.overall_health_score = int(weighted_sum / total_weight)
        else:
            assessment.overall_health_score = 50

        # Determine overall grade
        score = assessment.overall_health_score
        if score >= 90:
            assessment.overall_grade = "A"
        elif score >= 75:
            assessment.overall_grade = "B"
        elif score >= 60:
            assessment.overall_grade = "C"
        elif score >= 40:
            assessment.overall_grade = "D"
        else:
            assessment.overall_grade = "F"

    async def get_assessment_status(self, assessment_id: UUID) -> Dict[str, Any]:
        """Get current status of an assessment"""
        result = await self.db.execute(
            select(ProjectAssessment).where(ProjectAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()

        if not assessment:
            return {"error": "Assessment not found"}

        return {
            "id": str(assessment.id),
            "project_name": assessment.project_name,
            "status": assessment.status,
            "current_phase": assessment.current_phase,
            "progress_percent": assessment.progress_percent,
            "error_message": assessment.error_message,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None
        }


async def run_project_assessment(
    db: AsyncSession,
    project_name: str,
    directory_path: str,
    application_id: Optional[int] = None,
    use_llm: bool = False
) -> ProjectAssessment:
    """
    Convenience function to run a complete project assessment

    Args:
        db: Database session
        project_name: Name of the project
        directory_path: Path to project source
        application_id: Optional ApplicationRegistry ID
        use_llm: Enable LLM-enhanced analysis (default: False)

    Returns:
        Completed ProjectAssessment
    """
    orchestrator = ProjectAssessmentOrchestrator(db, use_llm=use_llm)
    assessment = await orchestrator.start_assessment(
        project_name=project_name,
        directory_path=directory_path,
        application_id=application_id
    )
    return await orchestrator.run_assessment(assessment.id)
