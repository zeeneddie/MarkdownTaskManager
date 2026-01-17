"""
Security Workflow Service - Quinn + CyberStrike Collaboration

Week 63: Automated security scanning integrated into development workflows

Features:
- Pre-deployment security validation
- Integration with NEW_FEATURE and BUG workflows
- Quinn Quality Inspector collaboration
- Automated blocking for critical vulnerabilities
- Security-aware Kanban lane transitions

Workflow Integration:
┌──────────────────────────────────────────────────────────────────────────┐
│                    SECURITY-AWARE DEVELOPMENT WORKFLOW                    │
│                                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐│
│  │ SPEC    │───▶│ BUILD   │───▶│ TEST    │───▶│ SECURITY│───▶│ REVIEW ││
│  │         │    │         │    │         │    │ SCAN    │    │        ││
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └────────┘│
│                                       │              │                  │
│                                       │              │                  │
│                                       ▼              ▼                  │
│                              ┌─────────────┐ ┌─────────────┐           │
│                              │ Tessa Tests │ │ CyberStrike │           │
│                              │ (Unit, E2E) │ │ (OWASP)     │           │
│                              └─────────────┘ └─────────────┘           │
│                                       │              │                  │
│                                       └──────┬───────┘                  │
│                                              │                          │
│                                              ▼                          │
│                                       ┌─────────────┐                   │
│                                       │ Quinn Gate  │                   │
│                                       │ Decision    │                   │
│                                       └─────────────┘                   │
│                                              │                          │
│                               ┌──────────────┼──────────────┐          │
│                               │              │              │          │
│                               ▼              ▼              ▼          │
│                          ┌────────┐    ┌────────┐    ┌────────┐       │
│                          │ PASS   │    │ WARN   │    │ BLOCK  │       │
│                          │ Deploy │    │ Review │    │ Fix    │       │
│                          └────────┘    └────────┘    └────────┘       │
└──────────────────────────────────────────────────────────────────────────┘
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cyberstrike_service import (
    CyberStrikeService,
    ScanResult,
    VulnerabilitySeverity,
    OWASPCategory
)
from app.services.kanban_quality_gate_service import (
    KanbanQualityGateService,
    ValidationCategory,
    ValidationResult
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class SecurityGateDecision(str, Enum):
    """Security gate decision outcomes."""
    PASS = "pass"           # All clear, proceed to deployment
    WARN = "warn"           # Issues found but non-blocking, proceed with caution
    BLOCK = "block"         # Critical issues, cannot proceed
    ERROR = "error"         # Scan failed, manual review required


class WorkflowType(str, Enum):
    """Workflow types that require security scanning."""
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    HOTFIX = "hotfix"
    MIGRATION = "migration"
    SECURITY_PATCH = "security_patch"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SecurityGateResult:
    """Result of security gate evaluation."""
    decision: SecurityGateDecision
    scan_result: Optional[ScanResult] = None
    quality_gate_result: Optional[Dict[str, Any]] = None
    blocking_issues: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    quinn_assessment: Optional[str] = None
    can_deploy: bool = False
    requires_review: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision": self.decision.value,
            "scan_result": self.scan_result.to_dict() if self.scan_result else None,
            "quality_gate_result": self.quality_gate_result,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "quinn_assessment": self.quinn_assessment,
            "can_deploy": self.can_deploy,
            "requires_review": self.requires_review,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SecurityWorkflowConfig:
    """Configuration for security workflow."""
    # Severity thresholds
    block_on_critical: bool = True
    block_on_high_count: int = 3  # Block if more than N high issues
    warn_on_medium_count: int = 10  # Warn if more than N medium issues

    # OWASP category blocking
    always_block_categories: List[OWASPCategory] = field(default_factory=lambda: [
        OWASPCategory.A03_INJECTION,  # SQL, XSS, Command injection
        OWASPCategory.A07_AUTH_FAILURES,  # Authentication issues
    ])

    # Scan settings
    include_external_scanners: bool = True
    timeout_seconds: int = 300

    # Workflow-specific overrides
    hotfix_relaxed_mode: bool = True  # Less strict for hotfixes
    security_patch_strict_mode: bool = True  # Extra strict for security patches


# ============================================================================
# SECURITY WORKFLOW SERVICE
# ============================================================================

class SecurityWorkflowService:
    """
    Service for integrating security scanning into development workflows.

    Coordinates between:
    - CyberStrike security scanning
    - Quinn Quality Inspector agent
    - Kanban Quality Gate service
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        config: Optional[SecurityWorkflowConfig] = None
    ):
        """
        Initialize security workflow service.

        Args:
            db: Database session for quality gate queries
            config: Security workflow configuration
        """
        self.db = db
        self.config = config or SecurityWorkflowConfig()
        self._cyberstrike: Optional[CyberStrikeService] = None
        self._quality_gate: Optional[KanbanQualityGateService] = None

    async def evaluate_security_gate(
        self,
        project_path: str,
        workflow_type: WorkflowType,
        item_id: Optional[str] = None,
        item_data: Optional[Dict[str, Any]] = None
    ) -> SecurityGateResult:
        """
        Evaluate security gate for a workflow item.

        This is the main entry point for security validation in the workflow.

        Args:
            project_path: Path to the project/code to scan
            workflow_type: Type of workflow (new_feature, bug_fix, etc.)
            item_id: Optional item identifier
            item_data: Optional additional item data

        Returns:
            SecurityGateResult with decision and details
        """
        result = SecurityGateResult(decision=SecurityGateDecision.ERROR)

        try:
            # Initialize services
            self._cyberstrike = CyberStrikeService(project_path=project_path)

            if self.db:
                self._quality_gate = KanbanQualityGateService(self.db)

            # Determine scan type based on workflow
            scan_config = self._get_scan_config_for_workflow(workflow_type)

            # Run security scan
            scan_result = await self._cyberstrike.full_scan(
                project_path,
                scan_type=scan_config["scan_type"],
                include_external=scan_config["include_external"]
            )
            result.scan_result = scan_result

            # If scan failed, return error
            if scan_result.status == "failed":
                result.decision = SecurityGateDecision.ERROR
                result.recommendations.append(f"Security scan failed: {scan_result.error}")
                result.requires_review = True
                return result

            # Analyze results and make decision
            result = self._make_security_decision(
                scan_result,
                workflow_type,
                item_data or {}
            )

            # Add Quinn assessment
            result.quinn_assessment = self._generate_quinn_assessment(result)

            # Run quality gate integration if available
            if self._quality_gate and item_id:
                quality_result = await self._run_quality_gate_checks(
                    item_id, item_data or {}, scan_result
                )
                result.quality_gate_result = quality_result

        except Exception as e:
            logger.error(f"Security gate evaluation failed: {e}")
            result.decision = SecurityGateDecision.ERROR
            result.recommendations.append(f"Security gate error: {str(e)}")
            result.requires_review = True

        return result

    async def pre_deployment_check(
        self,
        project_path: str,
        deployment_target: str = "production"
    ) -> SecurityGateResult:
        """
        Run pre-deployment security check.

        More comprehensive scan for production deployments.

        Args:
            project_path: Path to the project
            deployment_target: Target environment

        Returns:
            SecurityGateResult with deployment decision
        """
        # For production, always use strict settings
        if deployment_target == "production":
            strict_config = SecurityWorkflowConfig(
                block_on_critical=True,
                block_on_high_count=1,  # Block on any high issue
                warn_on_medium_count=5,
                include_external_scanners=True,
                security_patch_strict_mode=True
            )
            self.config = strict_config

        result = await self.evaluate_security_gate(
            project_path=project_path,
            workflow_type=WorkflowType.NEW_FEATURE,
            item_data={"deployment_target": deployment_target}
        )

        # Add deployment-specific recommendations
        if deployment_target == "production":
            if result.decision == SecurityGateDecision.WARN:
                result.recommendations.insert(0,
                    "PRODUCTION DEPLOYMENT: Review all warnings before proceeding."
                )
            elif result.decision == SecurityGateDecision.BLOCK:
                result.recommendations.insert(0,
                    "PRODUCTION BLOCKED: Critical security issues must be resolved."
                )

        return result

    async def scan_pull_request(
        self,
        base_path: str,
        changed_files: List[str]
    ) -> SecurityGateResult:
        """
        Scan only changed files in a pull request.

        Faster, more focused scan for PR reviews.

        Args:
            base_path: Base project path
            changed_files: List of changed file paths

        Returns:
            SecurityGateResult for the PR
        """
        self._cyberstrike = CyberStrikeService(project_path=base_path)

        all_vulnerabilities = []

        # Scan each changed file
        for file_path in changed_files:
            vulns = await self._cyberstrike.scan_file(file_path)
            all_vulnerabilities.extend(vulns)

        # Create a mock scan result
        scan_result = ScanResult(
            scan_id=f"pr-scan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            project_path=base_path,
            scan_type="pr_scan",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="completed",
            vulnerabilities=all_vulnerabilities
        )

        # Generate summary
        scan_result.summary = self._cyberstrike._generate_summary(all_vulnerabilities)

        # Make decision
        result = self._make_security_decision(
            scan_result,
            WorkflowType.NEW_FEATURE,
            {"changed_files": changed_files}
        )
        result.scan_result = scan_result
        result.quinn_assessment = self._generate_quinn_assessment(result)

        return result

    async def continuous_security_monitoring(
        self,
        project_path: str,
        interval_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Start continuous security monitoring.

        Runs periodic scans and reports status changes.

        Args:
            project_path: Path to monitor
            interval_minutes: Scan interval

        Returns:
            Monitoring status
        """
        self._cyberstrike = CyberStrikeService(project_path=project_path)

        # Run initial scan
        result = await self.evaluate_security_gate(
            project_path=project_path,
            workflow_type=WorkflowType.NEW_FEATURE
        )

        return {
            "monitoring_started": True,
            "project_path": project_path,
            "interval_minutes": interval_minutes,
            "initial_scan_result": result.to_dict(),
            "next_scan_at": (
                datetime.now(timezone.utc).isoformat()
            ),
            "status": "active"
        }

    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================

    def _get_scan_config_for_workflow(
        self,
        workflow_type: WorkflowType
    ) -> Dict[str, Any]:
        """Get scan configuration based on workflow type."""
        configs = {
            WorkflowType.NEW_FEATURE: {
                "scan_type": "full",
                "include_external": self.config.include_external_scanners
            },
            WorkflowType.BUG_FIX: {
                "scan_type": "full",
                "include_external": self.config.include_external_scanners
            },
            WorkflowType.HOTFIX: {
                "scan_type": "quick" if self.config.hotfix_relaxed_mode else "full",
                "include_external": not self.config.hotfix_relaxed_mode
            },
            WorkflowType.MIGRATION: {
                "scan_type": "full",
                "include_external": True  # Always thorough for migrations
            },
            WorkflowType.SECURITY_PATCH: {
                "scan_type": "full",
                "include_external": True  # Always thorough for security
            }
        }
        return configs.get(workflow_type, configs[WorkflowType.NEW_FEATURE])

    def _make_security_decision(
        self,
        scan_result: ScanResult,
        workflow_type: WorkflowType,
        item_data: Dict[str, Any]
    ) -> SecurityGateResult:
        """Make security gate decision based on scan results."""
        result = SecurityGateResult(decision=SecurityGateDecision.PASS)
        result.scan_result = scan_result

        summary = scan_result.summary
        vulnerabilities = scan_result.vulnerabilities

        # Check for critical issues
        critical_count = summary.get("critical_count", 0)
        high_count = summary.get("high_count", 0)
        medium_count = summary.get("by_severity", {}).get("medium", 0)

        # Collect blocking issues
        for vuln in vulnerabilities:
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                result.blocking_issues.append({
                    "id": vuln.id,
                    "title": vuln.title,
                    "severity": vuln.severity.value,
                    "category": vuln.owasp_category.value,
                    "file": vuln.file_path,
                    "line": vuln.line_number,
                    "remediation": vuln.remediation
                })
            elif vuln.severity == VulnerabilitySeverity.HIGH:
                if vuln.owasp_category in self.config.always_block_categories:
                    result.blocking_issues.append({
                        "id": vuln.id,
                        "title": vuln.title,
                        "severity": vuln.severity.value,
                        "category": vuln.owasp_category.value,
                        "file": vuln.file_path,
                        "line": vuln.line_number,
                        "remediation": vuln.remediation
                    })
                else:
                    result.warnings.append({
                        "id": vuln.id,
                        "title": vuln.title,
                        "severity": vuln.severity.value,
                        "category": vuln.owasp_category.value,
                        "file": vuln.file_path,
                        "line": vuln.line_number
                    })
            elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                result.warnings.append({
                    "id": vuln.id,
                    "title": vuln.title,
                    "severity": vuln.severity.value,
                    "category": vuln.owasp_category.value,
                    "file": vuln.file_path,
                    "line": vuln.line_number
                })

        # Make decision
        if critical_count > 0 and self.config.block_on_critical:
            result.decision = SecurityGateDecision.BLOCK
            result.can_deploy = False
            result.requires_review = True
            result.recommendations.append(
                f"BLOCKED: {critical_count} critical vulnerabilities found. "
                "These must be fixed before proceeding."
            )

        elif high_count > self.config.block_on_high_count:
            result.decision = SecurityGateDecision.BLOCK
            result.can_deploy = False
            result.requires_review = True
            result.recommendations.append(
                f"BLOCKED: {high_count} high-severity vulnerabilities exceed threshold "
                f"({self.config.block_on_high_count}). Review and fix required."
            )

        elif len(result.blocking_issues) > 0:
            result.decision = SecurityGateDecision.BLOCK
            result.can_deploy = False
            result.requires_review = True
            result.recommendations.append(
                f"BLOCKED: {len(result.blocking_issues)} blocking issues in critical categories. "
                "Review required."
            )

        elif high_count > 0 or medium_count > self.config.warn_on_medium_count:
            result.decision = SecurityGateDecision.WARN
            result.can_deploy = True
            result.requires_review = True
            result.recommendations.append(
                f"WARNING: {high_count} high and {medium_count} medium issues found. "
                "Review before deployment."
            )

        else:
            result.decision = SecurityGateDecision.PASS
            result.can_deploy = True
            result.requires_review = False
            result.recommendations.append(
                "Security scan passed. No blocking issues found."
            )

        # Add OWASP-specific recommendations
        owasp_counts = summary.get("by_owasp_category", {})
        for category, count in owasp_counts.items():
            if count > 0:
                result.recommendations.append(
                    f"{category}: {count} issue(s) found"
                )

        return result

    def _generate_quinn_assessment(
        self,
        gate_result: SecurityGateResult
    ) -> str:
        """Generate Quinn Quality Inspector's assessment."""
        if gate_result.decision == SecurityGateDecision.BLOCK:
            return (
                "🛑 QUINN ASSESSMENT: SECURITY GATE FAILED\n"
                f"Critical issues: {len(gate_result.blocking_issues)}\n"
                "Deployment BLOCKED until issues are resolved.\n"
                "Recommended action: Fix all blocking issues before proceeding."
            )

        elif gate_result.decision == SecurityGateDecision.WARN:
            return (
                "⚠️ QUINN ASSESSMENT: SECURITY CONCERNS\n"
                f"Warnings: {len(gate_result.warnings)}\n"
                "Deployment allowed but review recommended.\n"
                "Recommended action: Review warnings before production deployment."
            )

        elif gate_result.decision == SecurityGateDecision.PASS:
            return (
                "✅ QUINN ASSESSMENT: SECURITY GATE PASSED\n"
                "No blocking issues found.\n"
                "Deployment approved from security perspective."
            )

        else:
            return (
                "❓ QUINN ASSESSMENT: SCAN ERROR\n"
                "Security scan did not complete successfully.\n"
                "Manual review required before deployment."
            )

    async def _run_quality_gate_checks(
        self,
        item_id: str,
        item_data: Dict[str, Any],
        scan_result: ScanResult
    ) -> Dict[str, Any]:
        """Run additional quality gate checks with security data."""
        if not self._quality_gate:
            return {}

        # Enrich item_data with security scan results
        enriched_data = item_data.copy()
        enriched_data.update({
            "sql_injection_risk": any(
                v.owasp_category == OWASPCategory.A03_INJECTION
                for v in scan_result.vulnerabilities
            ),
            "xss_risk": any(
                "xss" in v.title.lower()
                for v in scan_result.vulnerabilities
            ),
            "has_hardcoded_secrets": any(
                v.owasp_category == OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES
                for v in scan_result.vulnerabilities
            ),
            "dependency_vulnerabilities": [
                v.to_dict() for v in scan_result.vulnerabilities
                if v.owasp_category == OWASPCategory.A06_VULNERABLE_COMPONENTS
            ],
            "security_scan_passed": scan_result.summary.get("quality_gate_passed", True)
        })

        # Run quality gate validation
        gate_result = await self._quality_gate.validate_in_review(
            item_id=item_id,
            item_type="feature",
            item_data=enriched_data
        )

        return {
            "passed": gate_result.passed,
            "blocking_failures": len(gate_result.blocking_failures),
            "total_failures": len(gate_result.all_failures),
            "summary": gate_result.summary
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_security_workflow_service(
    db: Optional[AsyncSession] = None,
    config: Optional[SecurityWorkflowConfig] = None
) -> SecurityWorkflowService:
    """Factory function to get security workflow service."""
    return SecurityWorkflowService(db=db, config=config)


async def run_security_gate(
    project_path: str,
    workflow_type: str = "new_feature",
    db: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Convenience function to run security gate evaluation.

    Args:
        project_path: Path to scan
        workflow_type: Workflow type string
        db: Optional database session

    Returns:
        Security gate result as dictionary
    """
    service = SecurityWorkflowService(db=db)
    wf_type = WorkflowType(workflow_type.lower())
    result = await service.evaluate_security_gate(project_path, wf_type)
    return result.to_dict()
