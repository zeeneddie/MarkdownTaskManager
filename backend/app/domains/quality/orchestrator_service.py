# Quality Orchestrator Service
# Orchestrates quality scanning across 3 execution modes
#
# Modes:
# 1. Standalone: Direct scan on project_path (via API)
# 2. Integrated: Automatic during Brown Paper analysis
# 3. Scheduled: Periodic scans via QualitySchedulerService
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 Phase 4 (Week 145-146)

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ...contracts import (
    QualityScanResult,
    QualityGateResult,
    QualityGateStatus,
    QualityRuleViolation,
)

logger = logging.getLogger(__name__)


class ScanMode(Enum):
    """Quality scan execution modes."""
    STANDALONE = "standalone"    # Direct API call
    INTEGRATED = "integrated"    # Part of Brown Paper
    SCHEDULED = "scheduled"      # Periodic via scheduler


@dataclass
class ScanContext:
    """Context for quality scan execution."""
    project_id: str
    project_path: str
    mode: ScanMode
    triggered_by: str = "manual"
    focus_areas: List[str] = field(default_factory=list)
    include_stability: bool = True
    threshold: int = 80


class QualityOrchestratorService:
    """
    Orchestrates quality scanning across all execution modes.

    Features:
    - Unified scan execution regardless of mode
    - Multi-scanner integration (SonarQube, security scanners)
    - Quality gate evaluation
    - Result persistence and history

    Usage:
        orchestrator = QualityOrchestratorService()

        # Mode 1: Standalone scan
        result = await orchestrator.run_standalone_scan(
            project_path="/path/to/project",
            project_id="my-project"
        )

        # Mode 2: Integrated scan (called from Brown Paper)
        result = await orchestrator.run_integrated_scan(
            project_path="/path/to/project",
            brown_paper_session_id="session-123"
        )

        # Mode 3: Scheduled scan (called from scheduler)
        result = await orchestrator.run_scheduled_scan(
            project_path="/path/to/project",
            project_id="my-project",
            schedule_id="schedule-123"
        )
    """

    # Default quality thresholds
    DEFAULT_THRESHOLDS = {
        'overall_score': 80,
        'security_score': 85,
        'max_blockers': 0,
        'max_critical': 3,
        'max_major': 20,
    }

    # Focus area scanners
    FOCUS_SCANNERS = {
        'security': '_scan_security',
        'performance': '_scan_performance',
        'maintainability': '_scan_maintainability',
        'reliability': '_scan_reliability',
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize the orchestrator."""
        self.db = db
        self._scanner_registry: Dict[str, Any] = {}

    def register_scanner(self, name: str, scanner: Any):
        """Register an external scanner (SonarQube, security scanner, etc.)."""
        self._scanner_registry[name] = scanner
        logger.info(f"Registered scanner: {name}")

    async def run_standalone_scan(
        self,
        project_path: str,
        project_id: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        include_stability: bool = True,
    ) -> QualityScanResult:
        """
        Run a standalone quality scan (Mode 1).

        This mode is triggered via direct API call and runs
        independently of any Brown Paper or Migration context.

        Args:
            project_path: Path to project to scan
            project_id: Optional project identifier
            focus_areas: Areas to focus on (security, performance, etc.)
            include_stability: Whether to include stability analysis

        Returns:
            QualityScanResult with scan findings
        """
        project_id = project_id or project_path.split("/")[-1]

        context = ScanContext(
            project_id=project_id,
            project_path=project_path,
            mode=ScanMode.STANDALONE,
            triggered_by="api",
            focus_areas=focus_areas or [],
            include_stability=include_stability,
        )

        return await self._execute_scan(context)

    async def run_integrated_scan(
        self,
        project_path: str,
        brown_paper_session_id: str,
        focus_areas: Optional[List[str]] = None,
    ) -> QualityScanResult:
        """
        Run an integrated quality scan (Mode 2).

        This mode is triggered automatically during Brown Paper
        analysis Phase 1 (Code Understanding).

        Args:
            project_path: Path to project to scan
            brown_paper_session_id: Brown Paper session for context
            focus_areas: Areas to focus on

        Returns:
            QualityScanResult to include in AnalysisContract
        """
        context = ScanContext(
            project_id=f"bp:{brown_paper_session_id}",
            project_path=project_path,
            mode=ScanMode.INTEGRATED,
            triggered_by=f"brown_paper:{brown_paper_session_id}",
            focus_areas=focus_areas or ['security', 'maintainability'],
            include_stability=True,
        )

        return await self._execute_scan(context)

    async def run_scheduled_scan(
        self,
        project_path: str,
        project_id: str,
        schedule_id: str,
        focus_areas: Optional[List[str]] = None,
    ) -> QualityScanResult:
        """
        Run a scheduled quality scan (Mode 3).

        This mode is triggered by QualitySchedulerService
        according to configured schedule (daily, weekly, interval).

        Args:
            project_path: Path to project to scan
            project_id: Project identifier
            schedule_id: Schedule that triggered this scan
            focus_areas: Areas to focus on

        Returns:
            QualityScanResult with audit trail
        """
        context = ScanContext(
            project_id=project_id,
            project_path=project_path,
            mode=ScanMode.SCHEDULED,
            triggered_by=f"schedule:{schedule_id}",
            focus_areas=focus_areas or ['security', 'performance', 'maintainability', 'reliability'],
            include_stability=True,
        )

        result = await self._execute_scan(context)

        # Update schedule last_run in database
        if self.db:
            await self._update_schedule_last_run(schedule_id)

        return result

    async def evaluate_gate(
        self,
        scan_result: QualityScanResult,
        thresholds: Optional[Dict[str, int]] = None,
    ) -> QualityGateResult:
        """
        Evaluate quality gate based on scan result.

        Args:
            scan_result: The scan result to evaluate
            thresholds: Optional custom thresholds

        Returns:
            QualityGateResult with pass/fail status
        """
        thresholds = thresholds or self.DEFAULT_THRESHOLDS

        checks = []
        blocking_issues = []

        # Check overall score
        overall_check = {
            "name": "Overall Score",
            "status": "passed" if scan_result.overall_score >= thresholds['overall_score'] else "failed",
            "value": scan_result.overall_score,
            "threshold": thresholds['overall_score'],
        }
        checks.append(overall_check)
        if overall_check["status"] == "failed":
            blocking_issues.append(f"Overall score {scan_result.overall_score} below threshold {thresholds['overall_score']}")

        # Check blockers
        blocker_check = {
            "name": "No Blockers",
            "status": "passed" if scan_result.blocker_count <= thresholds['max_blockers'] else "failed",
            "value": scan_result.blocker_count,
            "threshold": thresholds['max_blockers'],
        }
        checks.append(blocker_check)
        if blocker_check["status"] == "failed":
            blocking_issues.append(f"{scan_result.blocker_count} blocker issues found")

        # Check critical issues
        critical_check = {
            "name": "Critical Issues",
            "status": "passed" if scan_result.critical_count <= thresholds['max_critical'] else "failed",
            "value": scan_result.critical_count,
            "threshold": thresholds['max_critical'],
        }
        checks.append(critical_check)
        if critical_check["status"] == "failed":
            blocking_issues.append(f"{scan_result.critical_count} critical issues (max {thresholds['max_critical']})")

        # Check security score
        if scan_result.security_score < thresholds.get('security_score', 85):
            checks.append({
                "name": "Security Score",
                "status": "warning",
                "value": scan_result.security_score,
                "threshold": thresholds.get('security_score', 85),
            })

        # Determine overall status
        if blocking_issues:
            status = QualityGateStatus.FAILED
        elif any(c["status"] == "warning" for c in checks):
            status = QualityGateStatus.WARNING
        else:
            status = QualityGateStatus.PASSED

        return QualityGateResult(
            project_id=scan_result.project_id,
            gate_name="default",
            status=status,
            score=scan_result.overall_score,
            threshold=thresholds['overall_score'],
            checks=checks,
            blocking_issues=blocking_issues,
            scan_id=scan_result.scan_id,
        )

    async def _execute_scan(self, context: ScanContext) -> QualityScanResult:
        """Execute quality scan with given context."""
        logger.info(f"Executing {context.mode.value} scan for {context.project_id}")
        start_time = time.time()

        scan_id = str(uuid.uuid4())
        violations: List[QualityRuleViolation] = []

        # Collect violations from all relevant scanners
        scores = {
            'security': 100,
            'performance': 100,
            'maintainability': 100,
            'reliability': 100,
        }

        # Run focus area scanners
        focus_areas = context.focus_areas or list(self.FOCUS_SCANNERS.keys())
        for area in focus_areas:
            if area in self.FOCUS_SCANNERS:
                area_violations, area_score = await self._run_area_scan(
                    area, context.project_path
                )
                violations.extend(area_violations)
                scores[area] = area_score

        # Calculate severity counts
        blocker_count = sum(1 for v in violations if v.severity == "blocker")
        critical_count = sum(1 for v in violations if v.severity == "critical")
        major_count = sum(1 for v in violations if v.severity == "major")
        minor_count = sum(1 for v in violations if v.severity == "minor")

        # Calculate overall score
        overall_score = int(sum(scores.values()) / len(scores))

        # Adjust score based on severity counts
        overall_score -= blocker_count * 10
        overall_score -= critical_count * 5
        overall_score -= major_count * 2
        overall_score = max(0, min(100, overall_score))

        scan_duration = time.time() - start_time

        result = QualityScanResult(
            scan_id=scan_id,
            project_id=context.project_id,
            project_path=context.project_path,
            overall_score=overall_score,
            security_score=scores['security'],
            performance_score=scores['performance'],
            maintainability_score=scores['maintainability'],
            reliability_score=scores['reliability'],
            blocker_count=blocker_count,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            violations=violations,
            files_scanned=self._count_files(context.project_path),
            rules_evaluated=42,  # Number of rules checked
            scan_duration_seconds=scan_duration,
            scan_timestamp=datetime.now(timezone.utc),
            triggered_by=context.triggered_by,
        )

        # Persist result
        if self.db:
            await self._persist_result(result, context.mode)

        logger.info(
            f"Scan complete: score={overall_score}, "
            f"violations={len(violations)}, duration={scan_duration:.2f}s"
        )

        return result

    async def _run_area_scan(
        self,
        area: str,
        project_path: str,
    ) -> Tuple[List[QualityRuleViolation], int]:
        """
        Run scan for a specific focus area.

        In production, this would integrate with real scanners.
        Currently returns simulated results.
        """
        violations = []
        score = 100

        # Check for registered external scanner
        if area in self._scanner_registry:
            scanner = self._scanner_registry[area]
            try:
                return await scanner.scan(project_path)
            except Exception as e:
                logger.error(f"External scanner {area} failed: {e}")

        # Simulated scan results (replace with real scanner integration)
        if area == "security":
            # Simulate security findings
            violations.append(QualityRuleViolation(
                rule_id="SEC-001",
                rule_name="SQL Injection Risk",
                severity="critical",
                file_path=f"{project_path}/src/db.py",
                line_number=42,
                message="Potential SQL injection vulnerability detected",
                suggestion="Use parameterized queries",
                category="security",
            ))
            score = 90

        elif area == "maintainability":
            # Simulate maintainability findings
            violations.append(QualityRuleViolation(
                rule_id="MAINT-001",
                rule_name="High Complexity",
                severity="major",
                file_path=f"{project_path}/src/service.py",
                line_number=150,
                message="Function cyclomatic complexity is 25 (max 15)",
                suggestion="Refactor into smaller functions",
                category="maintainability",
            ))
            score = 85

        return violations, score

    def _count_files(self, project_path: str) -> int:
        """Count scannable files in project."""
        # Simplified - in production would walk the file tree
        return 150

    async def _persist_result(self, result: QualityScanResult, mode: ScanMode):
        """Persist scan result to database."""
        if not self.db:
            return

        try:
            await self.db.execute(text("""
                INSERT INTO quality_scan_results (
                    scan_id, project_id, project_path, status, overall_score,
                    result_data, triggered_by, scan_duration_seconds, created_at
                ) VALUES (
                    :scan_id, :project_id, :project_path, :status, :overall_score,
                    :result_data, :triggered_by, :scan_duration_seconds, :created_at
                )
            """), {
                "scan_id": result.scan_id,
                "project_id": result.project_id,
                "project_path": result.project_path,
                "status": "completed",
                "overall_score": result.overall_score,
                "result_data": result.to_dict(),
                "triggered_by": result.triggered_by,
                "scan_duration_seconds": result.scan_duration_seconds,
                "created_at": result.scan_timestamp,
            })
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to persist scan result: {e}")

    async def _update_schedule_last_run(self, schedule_id: str):
        """Update schedule last run time."""
        if not self.db:
            return

        try:
            await self.db.execute(text("""
                UPDATE quality_schedules
                SET last_run_at = :last_run_at
                WHERE schedule_id = :schedule_id
            """), {
                "schedule_id": schedule_id,
                "last_run_at": datetime.now(timezone.utc),
            })
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update schedule last run: {e}")
