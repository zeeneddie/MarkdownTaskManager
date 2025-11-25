"""
Agent Validation Loop Service

Week 50 Day 4: Implements the validation iteration loop for AI agents.

This service:
1. Takes code from an agent
2. Runs validation through quality gates
3. If failed, provides structured feedback for agent to fix
4. Iterates until pass or max iterations reached
5. Logs all attempts for learning

Based on AGENTS.md validation capabilities:
- Each agent has specific validation phases
- Max iterations configurable per workflow
- Integration with quality gate configuration

Author: Claude Code (Week 50 Day 4)
Date: 2025-11-24
"""

from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.validation_pipeline_service import (
    ValidationPipelineService,
    ValidationConfig,
    ValidationResult,
    ValidationPhase,
    ValidationError,
    Language
)
from app.services.quality_gate_integration_service import (
    QualityGateIntegrationService,
    QualityGateResult,
    WORK_TYPE_PHASES
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

class LoopStatus(str, Enum):
    """Status of validation loop"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"
    CANCELLED = "cancelled"


@dataclass
class ValidationAttempt:
    """Record of a single validation attempt"""
    iteration: int
    timestamp: datetime
    code_hash: str
    validation_result: ValidationResult
    gate_result: QualityGateResult
    errors_fixed: int
    errors_remaining: int
    feedback_provided: str


@dataclass
class FixSuggestion:
    """Structured suggestion for fixing validation error"""
    phase: str
    error_message: str
    severity: str
    file: Optional[str]
    line: Optional[int]
    suggestion: str
    example_fix: Optional[str] = None


@dataclass
class ValidationLoopResult:
    """Final result of validation loop"""
    status: LoopStatus
    workflow_type: str
    total_iterations: int
    max_iterations: int
    final_code: Optional[str]
    final_validation: Optional[ValidationResult]
    final_gate_result: Optional[QualityGateResult]
    attempts: List[ValidationAttempt]
    total_errors_fixed: int
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "workflow_type": self.workflow_type,
            "total_iterations": self.total_iterations,
            "max_iterations": self.max_iterations,
            "passed": self.status == LoopStatus.PASSED,
            "total_errors_fixed": self.total_errors_fixed,
            "duration_seconds": self.duration_seconds,
            "attempts_summary": [
                {
                    "iteration": a.iteration,
                    "errors_remaining": a.errors_remaining,
                    "errors_fixed": a.errors_fixed
                }
                for a in self.attempts
            ]
        }


# ============================================================================
# FIX SUGGESTION GENERATOR
# ============================================================================

class FixSuggestionGenerator:
    """Generates fix suggestions from validation errors."""

    SUGGESTION_TEMPLATES = {
        "linting": {
            "missing semicolon": "Add semicolon at end of statement",
            "unused variable": "Remove unused variable or prefix with underscore (_)",
            "undefined": "Import or define the missing symbol",
            "indentation": "Fix indentation to match code style (4 spaces for Python, 2 for TS)",
            "import": "Add missing import statement at top of file",
        },
        "type_check": {
            "not assignable": "Change the type annotation or cast the value",
            "missing return": "Add return statement or change return type to void/None",
            "incompatible": "Ensure types match or add proper type conversion",
            "undefined": "Add type declaration or import the type",
        },
        "style": {
            "formatting": "Run auto-formatter (black for Python, prettier for TS)",
            "line too long": "Break long line into multiple lines",
            "trailing whitespace": "Remove trailing whitespace",
        },
        "unit_tests": {
            "assertion": "Fix the expected value or the implementation",
            "failed": "Review test logic and implementation",
            "timeout": "Optimize test or increase timeout",
            "import": "Fix import path in test file",
        },
        "e2e_tests": {
            "connection": "Ensure service is running and accessible",
            "timeout": "Increase timeout or optimize endpoint",
            "status code": "Fix endpoint to return expected status",
            "response": "Fix endpoint response format",
        }
    }

    def generate_suggestions(
        self,
        errors: List[ValidationError],
        phase: ValidationPhase
    ) -> List[FixSuggestion]:
        """Generate fix suggestions for validation errors."""
        suggestions = []
        phase_templates = self.SUGGESTION_TEMPLATES.get(phase.value, {})

        for error in errors:
            suggestion = self._match_suggestion(error.message, phase_templates)

            suggestions.append(FixSuggestion(
                phase=phase.value,
                error_message=error.message,
                severity=error.severity,
                file=error.file,
                line=error.line,
                suggestion=suggestion,
                example_fix=self._get_example_fix(error, phase)
            ))

        return suggestions

    def _match_suggestion(self, message: str, templates: Dict[str, str]) -> str:
        """Match error message to suggestion template."""
        message_lower = message.lower()

        for pattern, suggestion in templates.items():
            if pattern in message_lower:
                return suggestion

        return "Review the error message and fix accordingly"

    def _get_example_fix(
        self,
        error: ValidationError,
        phase: ValidationPhase
    ) -> Optional[str]:
        """Generate example fix for common errors."""
        message_lower = error.message.lower()

        if phase == ValidationPhase.LINTING:
            if "import" in message_lower:
                return "# Add at top of file:\nfrom module import symbol"
            if "unused" in message_lower:
                return "# Either remove or prefix with underscore:\n_unused_var = value"

        elif phase == ValidationPhase.TYPE_CHECK:
            if "optional" in message_lower:
                return "# Use Optional type:\nfrom typing import Optional\nvar: Optional[str] = None"

        return None


# ============================================================================
# AGENT VALIDATION LOOP SERVICE
# ============================================================================

class AgentValidationLoopService:
    """
    Manages the validation iteration loop for AI agents.

    Usage:
        service = AgentValidationLoopService(db_session)

        result = await service.run_validation_loop(
            workflow_type="NEW_FEATURE",
            initial_code=code,
            language=Language.PYTHON,
            fix_callback=agent_fix_function
        )

        if result.status == LoopStatus.PASSED:
            # Code is validated
            deploy(result.final_code)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.gate_service = QualityGateIntegrationService(db)
        self.validation_service = ValidationPipelineService()
        self.suggestion_generator = FixSuggestionGenerator()

    async def run_validation_loop(
        self,
        workflow_type: str,
        initial_code: str,
        language: Language,
        fix_callback: Optional[Callable[[str, List[FixSuggestion]], Awaitable[str]]] = None,
        file_path: Optional[str] = None,
        max_iterations_override: Optional[int] = None
    ) -> ValidationLoopResult:
        """
        Run the validation loop until pass or max iterations.

        Args:
            workflow_type: e.g., "NEW_FEATURE", "BUG"
            initial_code: The code to validate
            language: Python or TypeScript
            fix_callback: Async function to fix code given suggestions
            file_path: Optional path for context
            max_iterations_override: Override max iterations from config

        Returns:
            ValidationLoopResult with final status and all attempts
        """
        start_time = datetime.utcnow()
        attempts: List[ValidationAttempt] = []
        current_code = initial_code
        total_errors_fixed = 0

        # Get validation config
        config = await self.gate_service.get_validation_config(workflow_type)
        max_iterations = max_iterations_override or config.max_iterations

        logger.info(f"Starting validation loop for {workflow_type} (max {max_iterations} iterations)")

        for iteration in range(1, max_iterations + 1):
            logger.info(f"Validation iteration {iteration}/{max_iterations}")

            # Run validation
            validation_result = await self._run_validation(
                current_code, language, config, file_path
            )

            # Evaluate quality gate
            gate_result = await self.gate_service.evaluate_gate(
                workflow_type, validation_result
            )

            # Count errors
            errors_remaining = len(gate_result.blocking_issues)

            # Calculate errors fixed from previous iteration
            errors_fixed = 0
            if attempts:
                prev_errors = attempts[-1].errors_remaining
                errors_fixed = max(0, prev_errors - errors_remaining)
                total_errors_fixed += errors_fixed

            # Create attempt record
            attempt = ValidationAttempt(
                iteration=iteration,
                timestamp=datetime.utcnow(),
                code_hash=hash(current_code),
                validation_result=validation_result,
                gate_result=gate_result,
                errors_fixed=errors_fixed,
                errors_remaining=errors_remaining,
                feedback_provided=""
            )

            # Check if passed
            if gate_result.passed:
                attempts.append(attempt)
                duration = (datetime.utcnow() - start_time).total_seconds()

                logger.info(f"Validation PASSED after {iteration} iteration(s)")

                return ValidationLoopResult(
                    status=LoopStatus.PASSED,
                    workflow_type=workflow_type,
                    total_iterations=iteration,
                    max_iterations=max_iterations,
                    final_code=current_code,
                    final_validation=validation_result,
                    final_gate_result=gate_result,
                    attempts=attempts,
                    total_errors_fixed=total_errors_fixed,
                    duration_seconds=duration
                )

            # Generate fix suggestions
            suggestions = self._generate_all_suggestions(validation_result)
            attempt.feedback_provided = self._format_feedback(suggestions)
            attempts.append(attempt)

            # If no fix callback or last iteration, stop
            if not fix_callback or iteration == max_iterations:
                continue

            # Call agent to fix code
            try:
                logger.info(f"Requesting fix for {len(suggestions)} issues")
                current_code = await fix_callback(current_code, suggestions)
            except Exception as e:
                logger.error(f"Fix callback failed: {e}")
                break

        # Max iterations reached
        duration = (datetime.utcnow() - start_time).total_seconds()

        logger.warning(f"Validation FAILED after {max_iterations} iterations")

        return ValidationLoopResult(
            status=LoopStatus.MAX_ITERATIONS,
            workflow_type=workflow_type,
            total_iterations=max_iterations,
            max_iterations=max_iterations,
            final_code=current_code,
            final_validation=validation_result if attempts else None,
            final_gate_result=gate_result if attempts else None,
            attempts=attempts,
            total_errors_fixed=total_errors_fixed,
            duration_seconds=duration
        )

    async def _run_validation(
        self,
        code: str,
        language: Language,
        config: ValidationConfig,
        file_path: Optional[str]
    ) -> ValidationResult:
        """Run validation pipeline on code."""
        return await self.validation_service.run_validation(
            code=code,
            language=language,
            config=config,
            file_path=file_path
        )

    def _generate_all_suggestions(
        self,
        result: ValidationResult
    ) -> List[FixSuggestion]:
        """Generate suggestions for all validation errors."""
        suggestions = []

        for phase_result in result.phases:
            if not phase_result.passed and phase_result.errors:
                phase_suggestions = self.suggestion_generator.generate_suggestions(
                    phase_result.errors,
                    phase_result.phase
                )
                suggestions.extend(phase_suggestions)

        return suggestions

    def _format_feedback(self, suggestions: List[FixSuggestion]) -> str:
        """Format suggestions as feedback string."""
        if not suggestions:
            return "No specific suggestions available."

        lines = [f"Found {len(suggestions)} issue(s) to fix:\n"]

        for i, s in enumerate(suggestions, 1):
            location = ""
            if s.file:
                location = f" at {s.file}"
                if s.line:
                    location += f":{s.line}"

            lines.append(f"{i}. [{s.phase}] {s.error_message}{location}")
            lines.append(f"   Suggestion: {s.suggestion}")

            if s.example_fix:
                lines.append(f"   Example:\n   {s.example_fix}")

            lines.append("")

        return "\n".join(lines)

    async def get_validation_status(
        self,
        workflow_type: str,
        code: str,
        language: Language
    ) -> Dict[str, Any]:
        """
        Quick validation check without iteration loop.

        Returns current validation status and suggestions.
        """
        config = await self.gate_service.get_validation_config(workflow_type)

        validation_result = await self._run_validation(
            code, language, config, None
        )

        gate_result = await self.gate_service.evaluate_gate(
            workflow_type, validation_result
        )

        suggestions = self._generate_all_suggestions(validation_result)

        return {
            "passed": gate_result.passed,
            "workflow_type": workflow_type,
            "blocking_count": len(gate_result.blocking_issues),
            "warning_count": len(gate_result.warnings),
            "coverage_met": gate_result.coverage_met,
            "suggestions": [
                {
                    "phase": s.phase,
                    "message": s.error_message,
                    "severity": s.severity,
                    "suggestion": s.suggestion
                }
                for s in suggestions
            ]
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def run_agent_validation(
    db: AsyncSession,
    workflow_type: str,
    code: str,
    language: Language,
    fix_callback: Optional[Callable[[str, List[FixSuggestion]], Awaitable[str]]] = None
) -> ValidationLoopResult:
    """
    Convenience function to run validation loop.

    Usage:
        result = await run_agent_validation(
            db, "NEW_FEATURE", code, Language.PYTHON
        )
    """
    service = AgentValidationLoopService(db)
    return await service.run_validation_loop(
        workflow_type=workflow_type,
        initial_code=code,
        language=language,
        fix_callback=fix_callback
    )


async def quick_validate(
    db: AsyncSession,
    workflow_type: str,
    code: str,
    language: Language
) -> Dict[str, Any]:
    """
    Quick validation without iteration loop.

    Usage:
        status = await quick_validate(db, "BUG", code, Language.PYTHON)
        if not status["passed"]:
            print(status["suggestions"])
    """
    service = AgentValidationLoopService(db)
    return await service.get_validation_status(workflow_type, code, language)
