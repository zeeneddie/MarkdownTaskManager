"""
Provider Registry - Multi-LLM Routing

Central registry for all LLM providers with intelligent task-based routing.
"""

from typing import Dict, List, Literal, Optional
from .base import LLMProvider, ProviderConfig
from .ollama_provider import OllamaProvider
from .codex_provider import CodexProvider


TaskType = Literal[
    "simple_generation",
    "quick_fix",
    "code_review",
    "standard_work",
    "architecture",
    "security_audit",
    "complex_analysis",
    "refactoring",
    "documentation",
    "debugging",
]


# Task-to-Provider routing configuration
TASK_ROUTING: Dict[TaskType, str] = {
    "simple_generation": "ollama",      # Free, fast
    "quick_fix": "ollama",              # Free, local
    "documentation": "ollama",          # Mistral is good at docs
    "debugging": "ollama",              # Codellama specializes
    "code_review": "codex",             # Deep analysis needed
    "standard_work": "ollama",          # Default to free
    "architecture": "codex",            # Complex reasoning
    "security_audit": "codex",          # Critical analysis
    "complex_analysis": "codex",        # Multi-file understanding
    "refactoring": "codex",             # Structural changes
}

# Default models per provider
DEFAULT_MODELS = {
    "ollama": "qwen2.5-coder:7b",
    "codex": "gpt-5.1-codex-max",
}


class ProviderRegistry:
    """
    Central registry for LLM providers.

    Manages provider instances and routes tasks to optimal providers
    based on task type, cost, and availability.

    Usage:
        registry = ProviderRegistry()

        # Route automatically
        provider = registry.route_task("architecture")
        response = await provider.generate(request)

        # Get specific provider
        codex = registry.get_provider("codex")
    """

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize default providers."""
        # Ollama (local, free)
        self._providers["ollama"] = OllamaProvider(
            model=DEFAULT_MODELS["ollama"]
        )

        # Codex (OpenAI, deep analysis)
        self._providers["codex"] = CodexProvider(
            model=DEFAULT_MODELS["codex"],
            reasoning_effort="medium",
            sandbox_mode="read-only"
        )

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """
        Get a specific provider by name.

        Args:
            name: Provider name ("ollama", "codex", "claude")

        Returns:
            LLMProvider instance or None if not found
        """
        return self._providers.get(name)

    def route_task(
        self,
        task_type: TaskType,
        prefer_local: bool = False,
        max_cost_cents: Optional[float] = None
    ) -> LLMProvider:
        """
        Route a task to the optimal provider.

        Args:
            task_type: Type of task to route
            prefer_local: If True, prefer Ollama even for complex tasks
            max_cost_cents: Maximum cost threshold (will fallback to local)

        Returns:
            Optimal LLMProvider for the task
        """
        # Get recommended provider
        recommended = TASK_ROUTING.get(task_type, "ollama")

        # Override to local if requested
        if prefer_local:
            return self._providers["ollama"]

        # Check cost threshold
        provider = self._providers.get(recommended)
        if max_cost_cents is not None and provider:
            if not provider.config.is_local:
                # Estimate: if task might exceed cost, use local
                # (Simple heuristic: non-local providers are "expensive")
                return self._providers["ollama"]

        return provider or self._providers["ollama"]

    def list_providers(self) -> List[ProviderConfig]:
        """List all registered providers with their configs."""
        return [p.config for p in self._providers.values()]

    async def healthcheck_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        for name, provider in self._providers.items():
            results[name] = await provider.healthcheck()
        return results

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register a custom provider."""
        self._providers[name] = provider

    def get_routing_table(self) -> Dict[TaskType, str]:
        """Get the current task routing configuration."""
        return TASK_ROUTING.copy()


# Singleton instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def get_provider(name: str) -> Optional[LLMProvider]:
    """Convenience function to get a provider from the global registry."""
    return get_registry().get_provider(name)
