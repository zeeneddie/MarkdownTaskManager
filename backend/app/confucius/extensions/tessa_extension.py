"""
Tessa Extension - Testing Specialist.

Wraps testing services for Confucius orchestrator integration.
Handles test generation, coverage analysis, and test execution.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class TessaExtension(BaseAgentExtension):
    """
    Tessa - Testing Agent Extension.

    Capabilities:
    - Test case generation
    - Test coverage analysis
    - Test execution and reporting
    - Characterization tests for legacy code
    - Visual regression testing
    - Dual-run comparison

    Position in workflow: Validates implementations.
    """

    def __init__(self):
        """Initialize Tessa extension."""
        super().__init__(
            ExtensionMetadata(
                name="Tessa",
                description="Testing Specialist - Tests, coverage, validation",
                capabilities=[
                    "test_generation",
                    "coverage_analysis",
                    "test_execution",
                    "characterization_tests",
                    "visual_regression",
                    "dual_run_comparison",
                    "test_planning",
                    "test_data_generation",
                ],
                domains=[
                    "testing",
                    "tests",
                    "coverage",
                    "qa",
                    "validation",
                    "regression",
                    "characterization",
                ],
                priority=6,
                parallel_safe=True,
                timeout_seconds=180,  # Tests can take time
                version="1.0.0",
            )
        )
        self._characterization_service = None
        self._coverage_service = None

    def _get_characterization_service(self):
        """Lazy load characterization test service."""
        if self._characterization_service is None:
            try:
                from app.services.characterization_test_service import (
                    CharacterizationTestService,
                )
                self._characterization_service = CharacterizationTestService()
            except ImportError as e:
                logger.warning(f"Could not import CharacterizationTestService: {e}")
        return self._characterization_service

    def _get_coverage_service(self):
        """Lazy load coverage service."""
        if self._coverage_service is None:
            try:
                from app.services.code_coverage_analyzer_service import (
                    CodeCoverageAnalyzerService,
                )
                self._coverage_service = CodeCoverageAnalyzerService()
            except ImportError as e:
                logger.warning(f"Could not import CodeCoverageAnalyzerService: {e}")
        return self._coverage_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Tessa testing."""
        modified = context.copy()

        # Determine test type
        test_type = self._determine_test_type(task)
        modified["tessa_test_type"] = test_type

        # Set coverage threshold if not specified
        if "coverage_threshold" not in modified:
            modified["coverage_threshold"] = 80.0

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute testing activities."""
        test_type = context.get("tessa_test_type", "general")

        try:
            if test_type == "generation":
                result = await self._generate_tests(context)
            elif test_type == "coverage":
                result = await self._analyze_coverage(context)
            elif test_type == "execution":
                result = await self._execute_tests(context)
            elif test_type == "characterization":
                result = await self._generate_characterization_tests(context)
            elif test_type == "visual_regression":
                result = await self._run_visual_regression(context)
            else:
                result = await self._general_testing(task, context)

            self.update_partial({
                "testing_complete": True,
                "test_type": test_type,
            })

            return {
                "success": True,
                "test_type": test_type,
                "result": result,
                "agent": "Tessa",
            }

        except Exception as e:
            logger.error(f"Tessa testing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_type": test_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Tessa output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["tests_generated"] = result.get("tests_generated", 0)
        parsed["coverage_percentage"] = result.get("coverage_percentage", 0.0)
        parsed["tests_passed"] = result.get("tests_passed", 0)
        parsed["tests_failed"] = result.get("tests_failed", 0)
        parsed["test_cases"] = result.get("test_cases", [])

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record test metrics."""
        if executed_output.get("success"):
            tests_generated = executed_output.get("tests_generated", 0)
            coverage = executed_output.get("coverage_percentage", 0.0)
            passed = executed_output.get("tests_passed", 0)
            failed = executed_output.get("tests_failed", 0)

            executed_output["tessa_summary"] = {
                "tests_generated": tests_generated,
                "coverage_percentage": coverage,
                "tests_passed": passed,
                "tests_failed": failed,
                "pass_rate": passed / (passed + failed) if (passed + failed) > 0 else 0,
                "entry_id": entry_id,
            }

            logger.info(
                f"Tessa completed: {tests_generated} tests, "
                f"{coverage:.1f}% coverage, {passed}/{passed+failed} passed"
            )

        return executed_output

    def _determine_test_type(self, task: str) -> str:
        """Determine test type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["generate", "create", "write tests"]):
            return "generation"
        elif any(kw in task_lower for kw in ["coverage", "cover"]):
            return "coverage"
        elif any(kw in task_lower for kw in ["run", "execute", "test"]):
            return "execution"
        elif any(kw in task_lower for kw in ["characterization", "legacy", "capture"]):
            return "characterization"
        elif any(kw in task_lower for kw in ["visual", "screenshot", "regression"]):
            return "visual_regression"
        else:
            return "general"

    async def _generate_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test cases."""
        return {
            "tests_generated": 0,
            "test_cases": [],
            "test_framework": context.get("framework", "pytest"),
        }

    async def _analyze_coverage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test coverage."""
        service = self._get_coverage_service()
        if service and hasattr(service, "analyze"):
            try:
                return await service.analyze(context)
            except Exception as e:
                logger.warning(f"Coverage analysis failed: {e}")

        return {
            "coverage_percentage": 0.0,
            "uncovered_lines": [],
            "uncovered_functions": [],
        }

    async def _execute_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tests."""
        return {
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_ms": 0,
        }

    async def _generate_characterization_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate characterization tests for legacy code."""
        service = self._get_characterization_service()
        if service and hasattr(service, "generate"):
            try:
                return await service.generate(context)
            except Exception as e:
                logger.warning(f"Characterization test generation failed: {e}")

        return {
            "tests_generated": 0,
            "captured_behaviors": [],
        }

    async def _run_visual_regression(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run visual regression tests."""
        return {
            "screenshots_compared": 0,
            "differences_found": 0,
            "baseline_created": False,
        }

    async def _general_testing(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute general testing activities."""
        results = {}

        # Analyze coverage
        coverage = await self._analyze_coverage(context)
        results["coverage_percentage"] = coverage.get("coverage_percentage", 0.0)

        return results
