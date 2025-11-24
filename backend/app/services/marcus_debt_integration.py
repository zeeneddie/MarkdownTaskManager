"""
Marcus-Technical Debt Integration Service

Bridges Marcus Agent with the Technical Debt Management system:
- Runs automated debt detection scans
- Creates remediation tasks for Marcus
- Tracks resolution progress
- Provides AI-assisted debt analysis

Author: Claude Code (Week 18 Day 4)
Date: 2025-11-22
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.marcus_integration import (
    get_marcus_agent, MarcusAgent, FocusArea, MaintenanceScope, Urgency
)
from app.services.technical_debt_service import (
    get_technical_debt_service, TechnicalDebtService, PrioritizedItem
)
from app.models.technical_debt import (
    TechnicalDebtItem, TechnicalDebtSnapshot, RemediationPlan,
    DebtResolution, QualityGateResult,
    DebtType, DebtSeverity, DebtStatus
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class MarcusTaskType(str, Enum):
    """Types of tasks Marcus can handle"""
    SCAN = "scan"
    FIX = "fix"
    REFACTOR = "refactor"
    ANALYZE = "analyze"
    VERIFY = "verify"


DEBT_TYPE_TO_FOCUS_AREA = {
    DebtType.CODE_SMELL: FocusArea.CODE_QUALITY,
    DebtType.SECURITY: FocusArea.SECURITY,
    DebtType.PERFORMANCE: FocusArea.PERFORMANCE,
    DebtType.DEPENDENCY: FocusArea.DEPENDENCIES,
    DebtType.TEST_GAP: FocusArea.TESTING,
    DebtType.DOCUMENTATION: FocusArea.DOCUMENTATION,
    DebtType.ARCHITECTURE: FocusArea.CODE_QUALITY,
    DebtType.DUPLICATION: FocusArea.CODE_QUALITY,
}

SEVERITY_TO_URGENCY = {
    DebtSeverity.CRITICAL: Urgency.CRITICAL,
    DebtSeverity.HIGH: Urgency.HIGH,
    DebtSeverity.MEDIUM: Urgency.MEDIUM,
    DebtSeverity.LOW: Urgency.LOW,
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class MarcusTask:
    """A task for Marcus to execute"""
    id: str
    task_type: MarcusTaskType
    debt_item_id: Optional[int]
    description: str
    priority: int
    estimated_hours: float
    file_path: Optional[str]
    context: Dict[str, Any]
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


@dataclass
class DebtAnalysisResult:
    """Result of Marcus analyzing debt"""
    debt_item_id: int
    analysis: Dict[str, Any]
    fix_suggestion: Optional[str]
    estimated_effort: float
    confidence: float
    can_auto_fix: bool


# ============================================================================
# Marcus-Debt Integration Service
# ============================================================================

class MarcusDebtIntegration:
    """
    Integration between Marcus Agent and Technical Debt Management.

    Coordinates:
    - Automated scanning via Marcus
    - AI-assisted debt analysis
    - Remediation task creation
    - Progress tracking and reporting
    """

    def __init__(self, db: AsyncSession, project_path: str = "."):
        self.db = db
        self.project_path = project_path
        self.marcus = get_marcus_agent()
        self.debt_service = get_technical_debt_service(db, project_path)
        self._task_queue: List[MarcusTask] = []

    # ========================================================================
    # Automated Scanning
    # ========================================================================

    async def run_comprehensive_scan(
        self,
        project_id: Optional[int] = None,
        urgency: Urgency = Urgency.MEDIUM
    ) -> Dict[str, Any]:
        """
        Run a comprehensive debt scan combining scanner tools and Marcus AI.

        1. Run technical scanners (ruff, bandit, eslint)
        2. Have Marcus analyze results
        3. Generate prioritized remediation plan
        """
        start_time = datetime.utcnow()

        logger.info("Starting comprehensive debt scan with Marcus")

        # Step 1: Run technical scanners
        snapshot = await self.debt_service.scan_codebase(
            scanners=["ruff", "bandit"],
            project_id=project_id
        )

        logger.info(f"Scanner found {snapshot.total_items} debt items")

        # Step 2: Have Marcus analyze high-priority items
        marcus_available = await self.marcus.check_availability()
        marcus_insights = []

        if marcus_available and snapshot.critical_count + snapshot.high_count > 0:
            # Get critical and high severity items
            result = await self.db.execute(
                select(TechnicalDebtItem).where(
                    TechnicalDebtItem.snapshot_id == snapshot.id,
                    TechnicalDebtItem.severity.in_([
                        DebtSeverity.CRITICAL,
                        DebtSeverity.HIGH
                    ])
                ).limit(10)  # Analyze top 10
            )
            high_priority_items = result.scalars().all()

            for item in high_priority_items:
                analysis = await self._analyze_debt_item_with_marcus(item)
                if analysis:
                    marcus_insights.append(analysis)

        # Step 3: Generate summary
        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "scan_id": f"comprehensive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "snapshot_id": snapshot.id,
            "total_items": snapshot.total_items,
            "debt_ratio": snapshot.debt_ratio,
            "critical_count": snapshot.critical_count,
            "high_count": snapshot.high_count,
            "security_issues": snapshot.security_issues,
            "marcus_available": marcus_available,
            "marcus_insights": marcus_insights,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "recommendations": self._generate_recommendations(snapshot, marcus_insights)
        }

    async def _analyze_debt_item_with_marcus(
        self,
        item: TechnicalDebtItem
    ) -> Optional[Dict[str, Any]]:
        """Have Marcus analyze a specific debt item"""
        try:
            # Determine focus area
            focus_area = DEBT_TYPE_TO_FOCUS_AREA.get(
                item.debt_type,
                FocusArea.CODE_QUALITY
            )

            # Build context for Marcus
            content = f"""
Technical Debt Item Analysis Request:
- Title: {item.title}
- Type: {item.debt_type.value}
- Severity: {item.severity.value}
- File: {item.file_path}
- Line: {item.line_start}
- Detection Rule: {item.detection_rule}
- Message: {item.detection_message}

Please analyze this debt item and provide:
1. Root cause analysis
2. Suggested fix approach
3. Estimated effort to fix
4. Risk assessment if not fixed
5. Whether this can be auto-fixed
"""

            result = await self.marcus.analyze(
                focus_area=focus_area,
                content=content,
                context={
                    "debt_item_id": item.id,
                    "task_type": "debt_analysis"
                }
            )

            if result.get("success"):
                return {
                    "debt_item_id": item.id,
                    "title": item.title,
                    "debt_type": item.debt_type.value,
                    "severity": item.severity.value,
                    "marcus_analysis": result.get("analysis", {}),
                    "analyzed_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Marcus analysis failed for item {item.id}: {e}")

        return None

    def _generate_recommendations(
        self,
        snapshot: TechnicalDebtSnapshot,
        marcus_insights: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations from scan results"""
        recommendations = []

        # Critical issues
        if snapshot.critical_count > 0:
            recommendations.append(
                f"URGENT: Address {snapshot.critical_count} critical debt items immediately"
            )

        # Security
        if snapshot.security_issues > 0:
            recommendations.append(
                f"Security: Review and fix {snapshot.security_issues} security vulnerabilities"
            )

        # Debt ratio
        if snapshot.debt_ratio > 15:
            recommendations.append(
                f"Debt ratio ({snapshot.debt_ratio:.1f}%) exceeds healthy threshold (10%). "
                "Create a remediation plan to reduce debt."
            )
        elif snapshot.debt_ratio > 10:
            recommendations.append(
                f"Debt ratio ({snapshot.debt_ratio:.1f}%) is elevated. "
                "Schedule maintenance sprint."
            )

        # Delta
        if snapshot.items_delta > 10:
            recommendations.append(
                f"New debt increased by {snapshot.items_delta} items. "
                "Review recent commits for quality issues."
            )

        # Marcus insights
        for insight in marcus_insights:
            analysis = insight.get("marcus_analysis", {})
            if "immediate_actions" in analysis:
                recommendations.extend(analysis["immediate_actions"][:2])

        return recommendations

    # ========================================================================
    # Task Management
    # ========================================================================

    async def create_remediation_tasks(
        self,
        plan_id: int,
        max_tasks: int = 10
    ) -> List[MarcusTask]:
        """
        Create Marcus tasks for items in a remediation plan.
        """
        # Get the plan
        plan = await self.debt_service.get_remediation_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Get items from the plan
        if not plan.item_ids:
            return []

        result = await self.db.execute(
            select(TechnicalDebtItem).where(
                TechnicalDebtItem.id.in_(plan.item_ids[:max_tasks]),
                TechnicalDebtItem.status != DebtStatus.RESOLVED
            )
        )
        items = result.scalars().all()

        # Create tasks
        tasks = []
        for i, item in enumerate(items):
            task = MarcusTask(
                id=f"marcus_task_{plan_id}_{item.id}",
                task_type=self._determine_task_type(item),
                debt_item_id=item.id,
                description=f"Fix: {item.title}",
                priority=i + 1,
                estimated_hours=item.principal,
                file_path=item.file_path,
                context={
                    "plan_id": plan_id,
                    "debt_type": item.debt_type.value,
                    "severity": item.severity.value,
                    "detection_rule": item.detection_rule
                }
            )
            tasks.append(task)
            self._task_queue.append(task)

        logger.info(f"Created {len(tasks)} Marcus tasks for plan {plan_id}")

        return tasks

    def _determine_task_type(self, item: TechnicalDebtItem) -> MarcusTaskType:
        """Determine appropriate task type for a debt item"""
        if item.debt_type == DebtType.SECURITY:
            return MarcusTaskType.FIX
        elif item.debt_type in [DebtType.CODE_SMELL, DebtType.DUPLICATION]:
            return MarcusTaskType.REFACTOR
        elif item.debt_type == DebtType.TEST_GAP:
            return MarcusTaskType.ANALYZE  # Needs test writing
        else:
            return MarcusTaskType.FIX

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a Marcus task (analyze/plan but not actually modify code).
        """
        # Find task
        task = next((t for t in self._task_queue if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = "in_progress"

        try:
            # Get the debt item
            if task.debt_item_id:
                result = await self.db.execute(
                    select(TechnicalDebtItem).where(
                        TechnicalDebtItem.id == task.debt_item_id
                    )
                )
                item = result.scalar_one_or_none()

                if item:
                    # Have Marcus analyze and provide fix guidance
                    analysis = await self._analyze_debt_item_with_marcus(item)

                    task.result = {
                        "success": True,
                        "analysis": analysis,
                        "fix_guidance": self._generate_fix_guidance(item, analysis),
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    task.status = "completed"

                    return task.result

            task.status = "failed"
            task.result = {"success": False, "error": "No debt item found"}
            return task.result

        except Exception as e:
            task.status = "failed"
            task.result = {"success": False, "error": str(e)}
            logger.error(f"Task {task_id} execution failed: {e}")
            return task.result

    def _generate_fix_guidance(
        self,
        item: TechnicalDebtItem,
        analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate detailed fix guidance for a debt item"""
        guidance = {
            "item_id": item.id,
            "title": item.title,
            "file_path": item.file_path,
            "line": item.line_start,
            "steps": []
        }

        # Type-specific guidance
        if item.debt_type == DebtType.SECURITY:
            guidance["steps"] = [
                "Review the security vulnerability details",
                "Check OWASP guidelines for this vulnerability type",
                "Apply the recommended fix pattern",
                "Add security test to prevent regression",
                "Document the fix in commit message"
            ]
        elif item.debt_type == DebtType.CODE_SMELL:
            guidance["steps"] = [
                "Analyze the code smell pattern",
                "Identify the best refactoring approach",
                "Create tests if not present",
                "Apply refactoring incrementally",
                "Verify tests still pass"
            ]
        elif item.debt_type == DebtType.TEST_GAP:
            guidance["steps"] = [
                "Identify the untested functionality",
                "Write unit tests for happy path",
                "Add edge case tests",
                "Add negative tests",
                "Verify coverage improvement"
            ]
        else:
            guidance["steps"] = [
                "Review the debt item details",
                "Understand the impact",
                "Plan the fix approach",
                "Implement fix",
                "Verify fix is complete"
            ]

        # Add Marcus insights if available
        if analysis:
            marcus_analysis = analysis.get("marcus_analysis", {})
            if "fix_suggestion" in marcus_analysis:
                guidance["marcus_suggestion"] = marcus_analysis["fix_suggestion"]
            if "risk_assessment" in marcus_analysis:
                guidance["risk_note"] = marcus_analysis["risk_assessment"]

        return guidance

    # ========================================================================
    # Progress Tracking
    # ========================================================================

    async def get_task_queue_status(self) -> Dict[str, Any]:
        """Get current task queue status"""
        pending = [t for t in self._task_queue if t.status == "pending"]
        in_progress = [t for t in self._task_queue if t.status == "in_progress"]
        completed = [t for t in self._task_queue if t.status == "completed"]
        failed = [t for t in self._task_queue if t.status == "failed"]

        return {
            "total_tasks": len(self._task_queue),
            "pending": len(pending),
            "in_progress": len(in_progress),
            "completed": len(completed),
            "failed": len(failed),
            "tasks": [
                {
                    "id": t.id,
                    "type": t.task_type.value,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority
                }
                for t in self._task_queue
            ]
        }

    async def record_resolution(
        self,
        task_id: str,
        actual_hours: float,
        commit_hash: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record that a task has been resolved"""
        # Find task
        task = next((t for t in self._task_queue if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if not task.debt_item_id:
            raise ValueError("Task has no associated debt item")

        # Create resolution
        resolution = await self.debt_service.resolve_debt_item(
            item_id=task.debt_item_id,
            resolution_type="fix",
            resolved_by_agent="marcus",
            actual_hours=actual_hours,
            commit_hash=commit_hash,
            notes=notes
        )

        # Update task status
        task.status = "completed"
        task.result = {
            "resolution_id": resolution.id,
            "completed_at": datetime.utcnow().isoformat()
        }

        # Update plan progress if task is part of a plan
        if task.context.get("plan_id"):
            await self.debt_service.update_plan_progress(
                plan_id=task.context["plan_id"],
                resolved_item_id=task.debt_item_id,
                actual_hours=actual_hours
            )

        return resolution.to_dict()

    # ========================================================================
    # Reporting
    # ========================================================================

    async def get_marcus_activity_report(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Generate a report of Marcus's debt management activity"""
        since = datetime.utcnow() - timedelta(days=days)

        # Get resolutions by Marcus
        result = await self.db.execute(
            select(DebtResolution).where(
                DebtResolution.resolved_by_agent == "marcus",
                DebtResolution.completed_at >= since
            )
        )
        resolutions = result.scalars().all()

        # Get scans
        scan_result = await self.db.execute(
            select(TechnicalDebtSnapshot).where(
                TechnicalDebtSnapshot.timestamp >= since
            )
        )
        scans = scan_result.scalars().all()

        # Calculate metrics
        total_hours_saved = sum(r.interest_eliminated or 0 for r in resolutions)
        total_hours_spent = sum(r.actual_hours or 0 for r in resolutions)

        return {
            "period_days": days,
            "items_resolved": len(resolutions),
            "total_hours_spent": total_hours_spent,
            "interest_eliminated": total_hours_saved,
            "efficiency_ratio": total_hours_saved / total_hours_spent if total_hours_spent > 0 else 0,
            "scans_performed": len(scans),
            "average_debt_ratio": sum(s.debt_ratio for s in scans) / len(scans) if scans else 0,
            "resolution_breakdown": {
                "by_type": self._count_by_field(resolutions, "resolution_type"),
            },
            "task_queue": await self.get_task_queue_status(),
            "marcus_available": await self.marcus.check_availability()
        }

    def _count_by_field(
        self,
        items: List[Any],
        field: str
    ) -> Dict[str, int]:
        """Count items by a field value"""
        counts = {}
        for item in items:
            value = getattr(item, field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts


# ============================================================================
# Factory Function
# ============================================================================

def get_marcus_debt_integration(
    db: AsyncSession,
    project_path: str = "."
) -> MarcusDebtIntegration:
    """Factory function to create Marcus-Debt Integration service"""
    return MarcusDebtIntegration(db, project_path)


# ============================================================================
# Scheduler Integration
# ============================================================================

async def run_scheduled_debt_scan(
    db: AsyncSession,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Entry point for scheduled debt scans.
    Called by scheduler_service.
    """
    integration = get_marcus_debt_integration(db)
    return await integration.run_comprehensive_scan(
        project_id=project_id,
        urgency=Urgency.MEDIUM
    )
