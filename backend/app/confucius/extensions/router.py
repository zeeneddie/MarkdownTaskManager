"""
Extension Router for Confucius Orchestrator.

Routes tasks to appropriate agent extensions based on task matching,
context analysis, and extension priorities.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .base import BaseAgentExtension, ExtensionResult

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    """Result of routing decision."""
    extensions: List[BaseAgentExtension]
    scores: Dict[str, float]
    reasoning: str
    parallel_execution: bool = True


class ExtensionRouter:
    """
    Routes tasks to appropriate agent extensions.

    Routing algorithm:
    1. Calculate match scores for all extensions
    2. Filter by minimum threshold
    3. Sort by score * priority
    4. Select top N extensions
    5. Determine parallel vs sequential execution

    Example:
    ```python
    router = ExtensionRouter()
    router.register(FelixExtension())
    router.register(QuinnExtension())

    decision = router.route("Analyze architecture", context)
    for ext in decision.extensions:
        result = await ext.run_full_lifecycle(task, context, entry_id)
    ```
    """

    def __init__(
        self,
        threshold: float = 0.2,
        max_extensions: int = 5,
    ):
        """
        Initialize router.

        Args:
            threshold: Minimum match score to consider an extension
            max_extensions: Maximum extensions to invoke per task
        """
        self._extensions: Dict[str, BaseAgentExtension] = {}
        self._threshold = threshold
        self._max_extensions = max_extensions

    def register(self, extension: BaseAgentExtension) -> None:
        """
        Register an extension with the router.

        Args:
            extension: Extension to register
        """
        self._extensions[extension.name] = extension
        logger.info(f"Registered extension: {extension.name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister an extension.

        Args:
            name: Name of extension to remove

        Returns:
            True if extension was removed, False if not found
        """
        if name in self._extensions:
            del self._extensions[name]
            logger.info(f"Unregistered extension: {name}")
            return True
        return False

    def get_extension(self, name: str) -> Optional[BaseAgentExtension]:
        """Get extension by name."""
        return self._extensions.get(name)

    def list_extensions(self) -> List[str]:
        """List all registered extension names."""
        return list(self._extensions.keys())

    def route(
        self,
        task: str,
        context: Dict[str, Any],
        required_extensions: Optional[List[str]] = None,
        excluded_extensions: Optional[List[str]] = None,
    ) -> RouteDecision:
        """
        Route task to appropriate extensions.

        Args:
            task: Task description
            context: Task context
            required_extensions: Extensions that must be included
            excluded_extensions: Extensions to exclude

        Returns:
            RouteDecision with selected extensions
        """
        required_extensions = required_extensions or []
        excluded_extensions = excluded_extensions or []

        # Calculate scores for all extensions
        scores: Dict[str, float] = {}
        for name, ext in self._extensions.items():
            if name in excluded_extensions:
                continue

            score = ext.matches_task(task, context)
            # Boost score by priority
            effective_score = score * (1 + ext.priority * 0.1)
            scores[name] = effective_score

        # Select extensions
        selected = self._select_extensions(
            scores,
            required_extensions,
        )

        # Determine execution strategy
        parallel = self._can_execute_parallel(selected)

        # Build reasoning
        reasoning = self._build_reasoning(task, scores, selected)

        return RouteDecision(
            extensions=selected,
            scores={ext.name: scores.get(ext.name, 0) for ext in selected},
            reasoning=reasoning,
            parallel_execution=parallel,
        )

    def route_by_domain(
        self,
        domain: str,
        context: Dict[str, Any],
    ) -> List[BaseAgentExtension]:
        """
        Route by domain directly.

        Args:
            domain: Domain to match (e.g., "architecture", "testing")
            context: Task context

        Returns:
            List of extensions matching the domain
        """
        matching = []
        for ext in self._extensions.values():
            if domain.lower() in [d.lower() for d in ext.metadata.domains]:
                matching.append(ext)

        # Sort by priority
        matching.sort(key=lambda x: x.priority, reverse=True)
        return matching

    def route_by_capability(
        self,
        capability: str,
        context: Dict[str, Any],
    ) -> List[BaseAgentExtension]:
        """
        Route by capability directly.

        Args:
            capability: Capability to match (e.g., "test_generation")
            context: Task context

        Returns:
            List of extensions with the capability
        """
        matching = []
        for ext in self._extensions.values():
            if capability.lower() in [c.lower() for c in ext.metadata.capabilities]:
                matching.append(ext)

        # Sort by priority
        matching.sort(key=lambda x: x.priority, reverse=True)
        return matching

    def _select_extensions(
        self,
        scores: Dict[str, float],
        required: List[str],
    ) -> List[BaseAgentExtension]:
        """Select extensions based on scores and requirements."""
        selected = []

        # Add required extensions first
        for name in required:
            if name in self._extensions:
                selected.append(self._extensions[name])
                scores.pop(name, None)

        # Sort remaining by score
        sorted_scores = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Add extensions above threshold
        for name, score in sorted_scores:
            if score >= self._threshold and len(selected) < self._max_extensions:
                selected.append(self._extensions[name])

        return selected

    def _can_execute_parallel(
        self,
        extensions: List[BaseAgentExtension],
    ) -> bool:
        """Determine if extensions can run in parallel."""
        # All must be marked as parallel_safe
        return all(ext.metadata.parallel_safe for ext in extensions)

    def _build_reasoning(
        self,
        task: str,
        scores: Dict[str, float],
        selected: List[BaseAgentExtension],
    ) -> str:
        """Build reasoning explanation for routing decision."""
        if not selected:
            return f"No extensions matched task: '{task[:50]}...'"

        parts = [f"Routed to {len(selected)} extension(s):"]
        for ext in selected:
            score = scores.get(ext.name, 0)
            parts.append(
                f"  - {ext.name} (score={score:.2f}, priority={ext.priority})"
            )

        return "\n".join(parts)


class WorkflowRouter(ExtensionRouter):
    """
    Specialized router for workflow-based routing.

    Maps workflow types to predefined extension sequences.
    """

    WORKFLOW_MAPPINGS = {
        "brown_paper": [
            "Miguel",  # Metrics first
            "Felix",   # Architecture
            "Quinn",   # Quality
            "Eliza",   # Estimation
            "Diana",   # Documentation
        ],
        "migration": [
            "Felix",   # Architecture analysis
            "Marcus",  # Maintenance assessment
            "Paul",    # Planning
            "Tessa",   # Testing strategy
            "Quinn",   # Quality gates
        ],
        "green_paper": [
            "Peter",   # Requirements
            "Betty",   # Business analysis
            "Vicky",   # UI/UX design
            "Felix",   # Architecture
            "Paul",    # Planning
        ],
        "quality_audit": [
            "Quinn",   # Quality analysis
            "Miguel",  # Metrics
            "Tessa",   # Testing
            "Marcus",  # Maintenance
        ],
        "estimation": [
            "Eliza",   # Primary estimation
            "Felix",   # Architecture complexity
            "Miguel",  # Metrics for reference
        ],
    }

    # Model preferences per workflow (all Ollama/local by default)
    WORKFLOW_MODEL_PREFERENCES = {
        "brown_paper": {
            "Miguel": "qwen2.5-coder:7b",      # Code metrics
            "Peter": "qwen2.5:7b",             # Product Owner
            "Betty": "qwen2.5:7b",             # Business Analyst
            "Vicky": "qwen2.5:7b",             # UX Designer
            "Felix": "deepseek-r1:7b",         # Architecture
            "Quinn": "deepseek-r1:7b",         # Quality
            "Marcus": "deepseek-r1:7b",        # Maintenance
            "Eliza": "qwen2.5:7b",             # Estimation
            "Diana": "mistral:latest",         # Documentation
        },
        "migration": {
            "Miguel": "qwen2.5-coder:7b",
            "Peter": "qwen2.5:7b",
            "Betty": "qwen2.5:7b",
            "Vicky": "qwen2.5:7b",
            "Felix": "deepseek-r1:7b",
            "Quinn": "deepseek-r1:7b",
            "Marcus": "deepseek-r1:7b",
            "Eliza": "qwen2.5:7b",
            "Diana": "mistral:latest",
            "Paul": "qwen2.5:7b",
            "Tessa": "qwen2.5-coder:7b",
        },
    }

    def route_workflow(
        self,
        workflow_type: str,
        context: Dict[str, Any],
    ) -> RouteDecision:
        """
        Route based on workflow type.

        Args:
            workflow_type: Type of workflow (e.g., "brown_paper")
            context: Workflow context

        Returns:
            RouteDecision with workflow-specific extensions
        """
        extension_names = self.WORKFLOW_MAPPINGS.get(
            workflow_type.lower(),
            [],
        )

        extensions = []
        scores = {}

        for name in extension_names:
            ext = self.get_extension(name)
            if ext:
                extensions.append(ext)
                scores[name] = 1.0  # Workflow mapping is explicit

        # Workflows typically run sequentially
        return RouteDecision(
            extensions=extensions,
            scores=scores,
            reasoning=f"Workflow '{workflow_type}' maps to {len(extensions)} extensions",
            parallel_execution=False,  # Workflow steps are sequential
        )


def create_default_router() -> ExtensionRouter:
    """
    Create router with all default extensions registered.

    Returns:
        Router with all 11 agent extensions
    """
    from .felix_extension import FelixExtension
    from .quinn_extension import QuinnExtension
    from .eliza_extension import ElizaExtension
    from .diana_extension import DianaExtension
    from .marcus_extension import MarcusExtension
    from .miguel_extension import MiguelExtension
    from .tessa_extension import TessaExtension
    from .peter_extension import PeterExtension
    from .paul_extension import PaulExtension
    from .betty_extension import BettyExtension
    from .vicky_extension import VickyExtension

    router = WorkflowRouter()

    # Register all extensions
    router.register(FelixExtension())
    router.register(QuinnExtension())
    router.register(ElizaExtension())
    router.register(DianaExtension())
    router.register(MarcusExtension())
    router.register(MiguelExtension())
    router.register(TessaExtension())
    router.register(PeterExtension())
    router.register(PaulExtension())
    router.register(BettyExtension())
    router.register(VickyExtension())

    logger.info("Created default router with 11 extensions")
    return router
