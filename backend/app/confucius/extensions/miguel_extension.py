"""
Miguel Extension - Metrics Specialist.

Wraps metrics services for Confucius orchestrator integration.
Handles code metrics, project analytics, and performance tracking.

Week 158: Fixed to use local Ollama LLM for analysis.
"""

from typing import Dict, Any, Optional, List
import logging
import json
from pathlib import Path

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class MiguelExtension(BaseAgentExtension):
    """
    Miguel - Metrics Agent Extension.

    Capabilities:
    - Code metrics collection (LOC, complexity, coupling)
    - Project analytics and KPIs
    - Performance tracking
    - Trend analysis
    - Dashboard data generation
    - Health scoring

    Position in workflow: Provides data for all other agents.
    """

    def __init__(self):
        """Initialize Miguel extension."""
        super().__init__(
            ExtensionMetadata(
                name="Miguel",
                description="Metrics Specialist - Analytics, KPIs, health scores",
                capabilities=[
                    "code_metrics",
                    "project_analytics",
                    "performance_tracking",
                    "trend_analysis",
                    "dashboard_generation",
                    "health_scoring",
                    "complexity_metrics",
                    "coupling_analysis",
                ],
                domains=[
                    "metrics",
                    "analytics",
                    "kpi",
                    "performance",
                    "trends",
                    "dashboard",
                    "statistics",
                ],
                priority=7,  # High - other agents depend on metrics
                parallel_safe=True,
                timeout_seconds=60,
                version="1.0.0",
            )
        )
        self._evolution_service = None

    def _get_evolution_service(self):
        """Lazy load evolution metrics service."""
        if self._evolution_service is None:
            try:
                from app.services.evolution_metrics_service import (
                    EvolutionMetricsService,
                )
                self._evolution_service = EvolutionMetricsService()
            except ImportError as e:
                logger.warning(f"Could not import EvolutionMetricsService: {e}")
        return self._evolution_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Miguel metrics collection."""
        modified = context.copy()

        # Determine metrics type
        metrics_type = self._determine_metrics_type(task)
        modified["miguel_metrics_type"] = metrics_type

        # Set time range if not specified
        if "time_range" not in modified:
            modified["time_range"] = "30d"

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute metrics collection."""
        metrics_type = context.get("miguel_metrics_type", "general")

        try:
            if metrics_type == "code":
                result = await self._collect_code_metrics(context)
            elif metrics_type == "project":
                result = await self._collect_project_metrics(context)
            elif metrics_type == "performance":
                result = await self._collect_performance_metrics(context)
            elif metrics_type == "trends":
                result = await self._analyze_trends(context)
            elif metrics_type == "health":
                result = await self._calculate_health_score(context)
            else:
                result = await self._collect_general_metrics(task, context)

            self.update_partial({
                "metrics_complete": True,
                "metrics_type": metrics_type,
            })

            return {
                "success": True,
                "metrics_type": metrics_type,
                "result": result,
                "agent": "Miguel",
            }

        except Exception as e:
            logger.error(f"Miguel metrics collection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "metrics_type": metrics_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Miguel output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["metrics"] = result.get("metrics", {})
        parsed["health_score"] = result.get("health_score", 0.0)
        parsed["trends"] = result.get("trends", [])
        parsed["kpis"] = result.get("kpis", {})

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record metrics snapshot."""
        if executed_output.get("success"):
            metrics_count = len(executed_output.get("metrics", {}))
            health_score = executed_output.get("health_score", 0.0)

            executed_output["miguel_summary"] = {
                "metrics_collected": metrics_count,
                "health_score": health_score,
                "metrics_type": executed_output.get("metrics_type"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Miguel completed: {metrics_count} metrics, "
                f"health={health_score:.2f}"
            )

        return executed_output

    def _determine_metrics_type(self, task: str) -> str:
        """Determine metrics type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["code", "loc", "complexity", "coupling"]):
            return "code"
        elif any(kw in task_lower for kw in ["project", "kpi", "progress"]):
            return "project"
        elif any(kw in task_lower for kw in ["performance", "speed", "latency"]):
            return "performance"
        elif any(kw in task_lower for kw in ["trend", "history", "evolution"]):
            return "trends"
        elif any(kw in task_lower for kw in ["health", "score", "overall"]):
            return "health"
        else:
            return "general"

    def _scan_codebase(self, scan_path: str) -> Dict[str, Any]:
        """Scan codebase for basic metrics (sync, no LLM)."""
        path = Path(scan_path)
        if not path.exists():
            return {"error": f"Path not found: {scan_path}"}

        # Count files and lines
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.cs', '.go', '.java', '.vb', '.asp', '.aspx'}
        total_files = 0
        total_loc = 0
        files_by_type = {}

        for ext in extensions:
            files = list(path.rglob(f"*{ext}"))
            files = [f for f in files if 'node_modules' not in str(f) and '__pycache__' not in str(f)]
            if files:
                files_by_type[ext] = len(files)
                total_files += len(files)
                for f in files[:50]:  # Sample first 50 files
                    try:
                        total_loc += len(f.read_text(errors='ignore').splitlines())
                    except Exception:
                        pass

        return {
            "total_files": total_files,
            "total_loc": total_loc,
            "files_by_type": files_by_type,
            "scan_path": scan_path,
        }

    async def _collect_code_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect code metrics using filesystem scan and LLM analysis."""
        scan_path = context.get("scan_path", "")
        tech_stack = context.get("tech_stack", [])

        # First do a filesystem scan
        scan_result = self._scan_codebase(scan_path) if scan_path else {}

        prompt = f"""Analyze the following codebase metrics and provide quality assessment.

## Scan Results
{json.dumps(scan_result, indent=2, default=str)}

## Tech Stack
{json.dumps(tech_stack, indent=2, default=str)}

## Task
Calculate code quality metrics:
1. Lines of Code (LOC) - total and by language
2. Estimated cyclomatic complexity (1-10 scale)
3. Coupling estimate (1-10 scale)
4. Cohesion estimate (1-10 scale)
5. Overall health score (0-1)

## Output Schema
Return JSON:
{{
    "metrics": {{
        "loc": {scan_result.get("total_loc", 0)},
        "files": {scan_result.get("total_files", 0)},
        "complexity": 5,
        "coupling": 5,
        "cohesion": 5
    }},
    "health_score": 0.7,
    "analysis": "Brief analysis of the codebase quality"
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "metrics": scan_result,
            "health_score": 0.5,
        }

    async def _collect_project_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect project metrics using LLM."""
        code_analysis = context.get("code_analysis", {})

        prompt = f"""Analyze project metrics from the following code analysis.

## Code Analysis
{json.dumps(code_analysis, indent=2, default=str)[:6000]}

## Task
Calculate project KPIs:
1. Estimated velocity (story points/sprint)
2. Technical debt ratio (0-1)
3. Code coverage estimate
4. Documentation completeness

## Output Schema
Return JSON:
{{
    "metrics": {{}},
    "kpis": {{
        "velocity": 20,
        "burndown": 0.8,
        "tech_debt_ratio": 0.3,
        "coverage_estimate": 0.5
    }}
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "metrics": {},
            "kpis": {"velocity": 0, "burndown": 0, "tech_debt_ratio": 0},
        }

    async def _collect_performance_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect performance metrics using LLM analysis."""
        code_analysis = context.get("code_analysis", {})

        prompt = f"""Analyze potential performance characteristics of this codebase.

## Code Analysis
{json.dumps(code_analysis, indent=2, default=str)[:6000]}

## Task
Estimate performance characteristics:
1. Expected response times
2. Potential bottlenecks
3. Scalability concerns

## Output Schema
Return JSON:
{{
    "metrics": {{
        "response_time_p50": 100,
        "response_time_p95": 500,
        "error_rate": 0.01,
        "throughput": 1000
    }},
    "bottlenecks": [],
    "recommendations": []
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "metrics": {"response_time_p50": 0, "response_time_p95": 0, "error_rate": 0, "throughput": 0},
        }

    async def _analyze_trends(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics trends."""
        service = self._get_evolution_service()
        if service and hasattr(service, "get_trends"):
            try:
                return await service.get_trends(context)
            except Exception as e:
                logger.warning(f"Trend analysis failed: {e}")

        # Fallback to LLM analysis
        prompt = """Based on typical software project patterns, provide trend analysis.

## Output Schema
Return JSON:
{
    "trends": [
        {"metric": "code_quality", "direction": "improving", "confidence": 0.7}
    ],
    "direction": "stable",
    "analysis": "Brief trend analysis"
}"""

        result = await self.call_llm(prompt)
        return result if result else {"trends": [], "direction": "stable"}

    async def _calculate_health_score(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall health score using LLM."""
        code_analysis = context.get("code_analysis", {})
        metrics = context.get("metrics", {})

        prompt = f"""Calculate overall codebase health score.

## Code Analysis
{json.dumps(code_analysis, indent=2, default=str)[:4000]}

## Collected Metrics
{json.dumps(metrics, indent=2, default=str)[:2000]}

## Task
Calculate health scores (0-1) for:
1. Code quality
2. Test coverage estimate
3. Documentation completeness
4. Security posture
5. Overall health

## Output Schema
Return JSON:
{{
    "health_score": 0.7,
    "components": {{
        "code_quality": 0.7,
        "test_coverage": 0.5,
        "documentation": 0.6,
        "security": 0.6
    }},
    "recommendations": []
}}"""

        result = await self.call_llm(prompt)
        return result if result else {
            "health_score": 0.5,
            "components": {"code_quality": 0.5, "test_coverage": 0.5, "documentation": 0.5, "security": 0.5},
        }

    async def _collect_general_metrics(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Collect general metrics using all available sources."""
        results = {}

        # Aggregate all metric types
        code = await self._collect_code_metrics(context)
        project = await self._collect_project_metrics(context)
        health = await self._calculate_health_score(context)

        results["metrics"] = {
            **code.get("metrics", {}),
            **project.get("metrics", {}),
        }
        results["kpis"] = project.get("kpis", {})
        results["health_score"] = health.get("health_score", 0.0)
        results["components"] = health.get("components", {})

        return results
