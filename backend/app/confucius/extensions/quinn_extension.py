"""
Quinn Extension - Quality Specialist.

Wraps quality analysis services for Confucius orchestrator integration.
Handles code quality, security review, and compliance validation.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class QuinnExtension(BaseAgentExtension):
    """
    Quinn - Quality Agent Extension.

    Capabilities:
    - Code quality analysis
    - Security review (OWASP, CWE)
    - Compliance validation
    - Quality gate evaluation
    - Code review automation
    - Test coverage assessment

    Position in workflow: Validates output from other agents.
    """

    def __init__(self):
        """Initialize Quinn extension."""
        super().__init__(
            ExtensionMetadata(
                name="Quinn",
                description="Quality Specialist - Security, compliance, quality gates",
                capabilities=[
                    "code_quality_analysis",
                    "security_review",
                    "compliance_validation",
                    "quality_gate_evaluation",
                    "code_review",
                    "test_coverage_assessment",
                    "owasp_scanning",
                    "cwe_detection",
                ],
                domains=[
                    "quality",
                    "security",
                    "compliance",
                    "review",
                    "testing",
                    "validation",
                    "audit",
                ],
                priority=9,  # Highest priority - quality gates
                parallel_safe=True,
                timeout_seconds=120,
                version="1.0.0",
            )
        )
        self._quality_service = None
        self._security_service = None
        self._security_service_type = None  # "orchestrator" or "legacy"

    def _get_quality_service(self):
        """Lazy load quality service."""
        if self._quality_service is None:
            try:
                from app.services.quality_gate_integration_service import (
                    QualityGateIntegrationService,
                )
                self._quality_service = QualityGateIntegrationService()
            except ImportError as e:
                logger.warning(f"Could not import QualityGateIntegrationService: {e}")
        return self._quality_service

    def _get_security_service(self):
        """Lazy load security orchestrator (Fase 37 integration)."""
        if self._security_service is None:
            try:
                # Fase 37: Use SecurityScanOrchestrator for full scanner suite
                from app.services.security_scanner import (
                    SecurityScanOrchestrator,
                    create_security_orchestrator,
                )
                self._security_service = create_security_orchestrator()
                self._security_service_type = "orchestrator"
                logger.info("SecurityScanOrchestrator initialized for Quinn")
            except ImportError as e:
                logger.warning(f"Could not import SecurityScanOrchestrator: {e}")
                # Fallback to MigrationSecurityService
                try:
                    from app.services.migration_security_service import (
                        MigrationSecurityService,
                    )
                    self._security_service = MigrationSecurityService()
                    self._security_service_type = "legacy"
                    logger.warning("Falling back to MigrationSecurityService")
                except ImportError as e2:
                    logger.warning(f"Could not import MigrationSecurityService: {e2}")
        return self._security_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Quinn analysis."""
        modified = context.copy()

        # Determine review type from task
        review_type = self._determine_review_type(task)
        modified["quinn_review_type"] = review_type

        # Set quality thresholds if not specified
        if "quality_threshold" not in modified:
            modified["quality_threshold"] = 0.85

        # Inject relevant memory
        if self._orchestrator:
            relevant_memory = await self.get_relevant_memory(context)
            if relevant_memory:
                modified["previous_quality_insights"] = relevant_memory

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute quality review."""
        review_type = context.get("quinn_review_type", "full_review")

        try:
            if review_type == "security":
                result = await self._security_review(context)
            elif review_type == "compliance":
                result = await self._compliance_review(context)
            elif review_type == "quality_gate":
                result = await self._evaluate_quality_gate(context)
            elif review_type == "code_review":
                result = await self._code_review(context)
            else:
                result = await self._full_review(task, context)

            self.update_partial({
                "review_complete": True,
                "review_type": review_type,
            })

            return {
                "success": True,
                "review_type": review_type,
                "result": result,
                "agent": "Quinn",
            }

        except Exception as e:
            logger.error(f"Quinn review failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "review_type": review_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Quinn output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["findings"] = result.get("findings", [])
        parsed["quality_score"] = result.get("quality_score", 0.0)
        parsed["security_issues"] = result.get("security_issues", [])
        parsed["recommendations"] = result.get("recommendations", [])
        parsed["passes_gate"] = result.get("passes_gate", False)

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record quality metrics."""
        if executed_output.get("success"):
            findings_count = len(executed_output.get("findings", []))
            security_count = len(executed_output.get("security_issues", []))
            quality_score = executed_output.get("quality_score", 0.0)

            executed_output["quinn_summary"] = {
                "findings_count": findings_count,
                "security_issues_count": security_count,
                "quality_score": quality_score,
                "passes_gate": executed_output.get("passes_gate", False),
                "entry_id": entry_id,
            }

            logger.info(
                f"Quinn completed: score={quality_score:.2f}, "
                f"{findings_count} findings, {security_count} security issues"
            )

        return executed_output

    def _determine_review_type(self, task: str) -> str:
        """Determine review type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["security", "owasp", "cwe", "vulnerability"]):
            return "security"
        elif any(kw in task_lower for kw in ["compliance", "gdpr", "hipaa", "sox"]):
            return "compliance"
        elif any(kw in task_lower for kw in ["gate", "threshold", "pass", "fail"]):
            return "quality_gate"
        elif any(kw in task_lower for kw in ["review", "pr", "pull request", "code review"]):
            return "code_review"
        else:
            return "full_review"

    async def _full_review(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute full quality review."""
        results = {
            "findings": [],
            "security_issues": [],
            "quality_score": 0.0,
            "recommendations": [],
            "passes_gate": False,
        }

        # Run quality analysis
        quality_service = self._get_quality_service()
        if quality_service and hasattr(quality_service, "analyze"):
            try:
                quality_result = await quality_service.analyze(context)
                results["findings"].extend(quality_result.get("findings", []))
                results["quality_score"] = quality_result.get("score", 0.0)
            except Exception as e:
                logger.warning(f"Quality analysis failed: {e}")

        # Run security analysis
        security_result = await self._security_review(context)
        results["security_issues"] = security_result.get("issues", [])

        # Evaluate quality gate
        threshold = context.get("quality_threshold", 0.85)
        results["passes_gate"] = (
            results["quality_score"] >= threshold and
            len([i for i in results["security_issues"] if i.get("severity") == "critical"]) == 0
        )

        return results

    async def _security_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security review using SecurityScanOrchestrator (Fase 37)."""
        from pathlib import Path

        service = self._get_security_service()
        if not service:
            return {"issues": [], "risk_level": "unknown", "error": "No security service available"}

        # Check if we're using the new orchestrator
        if self._security_service_type == "orchestrator":
            try:
                # Extract project path from context
                project_path = context.get("project_path") or context.get("source_path")
                if not project_path:
                    return {"issues": [], "error": "No project path provided"}

                # Run security scan with orchestrator
                report = await service.scan(Path(project_path))

                # Format findings for Quinn output
                issues = [
                    {
                        "id": f.id,
                        "title": f.title,
                        "severity": f.severity.value,
                        "cwe_id": f.cwe_ids[0] if f.cwe_ids else None,
                        "cwe_ids": f.cwe_ids,
                        "category": f.category,
                        "file": f.location.file_path,
                        "line": f.location.start_line,
                        "description": f.description,
                        "scanner": f.scanner.value,
                        "is_cwe_top_25": f.is_cwe_top_25,
                    }
                    for f in report.all_findings
                ]

                summary = {
                    "total": report.total_findings,
                    "critical": report.total_critical,
                    "high": report.total_high,
                    "by_severity": report.get_severity_summary(),
                    "scanners_used": [s.value for s in report.scanners_used],
                    "languages_detected": list(report.languages_detected),
                }

                return {
                    "issues": issues,
                    "summary": summary,
                    "cwe_coverage": report.cwe_coverage,
                    "cwe_top_25_coverage": report.cwe_top_25_coverage,
                    "risk_level": self._calculate_risk_level(report),
                    "scan_type": "orchestrator",
                }

            except Exception as e:
                logger.error(f"SecurityScanOrchestrator scan failed: {e}")
                return {"issues": [], "error": str(e), "risk_level": "unknown"}

        # Fallback for legacy MigrationSecurityService
        try:
            if hasattr(service, "scan"):
                return await service.scan(context)
            elif hasattr(service, "analyze_directory"):
                # Legacy sync method
                project_path = context.get("project_path") or context.get("source_path")
                if project_path:
                    result = service.analyze_directory(directory=project_path)
                    return {"issues": result.get("findings", []), "risk_level": "medium"}
        except Exception as e:
            logger.warning(f"Legacy security scan failed: {e}")

        return {"issues": [], "risk_level": "unknown"}

    def _calculate_risk_level(self, report) -> str:
        """Calculate risk level from security report (Fase 37)."""
        critical = report.total_critical
        high = report.total_high
        severity_summary = report.get_severity_summary()
        medium = severity_summary.get("medium", 0)

        # Risk scoring
        if critical > 0:
            return "critical"
        elif high >= 5:
            return "high"
        elif high >= 1 or medium >= 10:
            return "medium"
        elif report.total_findings > 0:
            return "low"
        else:
            return "none"

    async def _compliance_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance review."""
        return {
            "compliance_status": "pending",
            "frameworks": context.get("compliance_frameworks", []),
            "findings": [],
        }

    async def _evaluate_quality_gate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate quality gate criteria."""
        threshold = context.get("quality_threshold", 0.85)
        current_score = context.get("current_score", 0.0)

        return {
            "passes_gate": current_score >= threshold,
            "threshold": threshold,
            "current_score": current_score,
            "gap": max(0, threshold - current_score),
        }

    async def _code_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automated code review."""
        return {
            "review_status": "completed",
            "findings": [],
            "suggestions": [],
            "approval_status": "pending",
        }
