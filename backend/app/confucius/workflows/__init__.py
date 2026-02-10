"""
Confucius Workflow Orchestrations.

Integrates existing MarQed workflows with the Confucius orchestrator
for unified agent coordination, quality gates, and cross-session learning.

Workflows:
- BrownPaperWorkflow: Legacy code analysis (bottom-up)
- MigrationWorkflow: MarQed 8-question migration planning
- GreenPaperWorkflow: Greenfield project specification
- QualityWorkflow: Quality gate and scanning orchestration
- OnboardingWorkflow: Unified onboarding (consolidates A-F workflows)
"""

from .base import (
    WorkflowOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
)

from .brown_paper import BrownPaperOrchestrator
from .migration import MigrationOrchestrator
from .green_paper import GreenPaperOrchestrator
from .quality import QualityOrchestrator
from .onboarding import OnboardingOrchestrator


__all__ = [
    # Base
    "WorkflowOrchestrator",
    "WorkflowStage",
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowStatus",
    # Workflows
    "BrownPaperOrchestrator",
    "MigrationOrchestrator",
    "GreenPaperOrchestrator",
    "QualityOrchestrator",
    "OnboardingOrchestrator",
]
