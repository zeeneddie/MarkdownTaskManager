"""
Provider Registry - Multi-LLM Routing

Central registry for all LLM providers with intelligent task-based routing.

Week 90: Extended with 5 new cloud providers for Deep Extraction Pipeline
- Groq: Ultra-fast inference (300-840 TPS)
- Gemini: 1M context window, cross-enrichment
- OpenAI: Coding specialist (GPT-4o, o1)
- Anthropic: Deep reasoning and synthesis (Claude Opus 4.5)
- Qwen: Cost-effective bulk processing (10M context)

Week 102: Integrated with LLMContextAdapter for provider-specific formatting
"""

import logging
from typing import Dict, List, Literal, Optional
from .base import LLMProvider, LLMRequest, ProviderConfig

logger = logging.getLogger(__name__)

# Week 102: Import LLMContextAdapter (optional, graceful fallback)
try:
    from app.services.llm import LLMContextAdapter
    from app.services.llm.project_context import ProjectContext
    CONTEXT_ADAPTER_AVAILABLE = True
except ImportError:
    CONTEXT_ADAPTER_AVAILABLE = False
    LLMContextAdapter = None
    ProjectContext = None
from .ollama_provider import OllamaProvider
from .codex_provider import CodexProvider
from .claude_provider import ClaudeProvider

# Week 90: New cloud providers for Deep Extraction
from .groq_provider import GroqProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .qwen_provider import QwenProvider


TaskType = Literal[
    # Original task types
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
    "planning",
    "estimation",
    # Week 90: Deep Extraction task types
    "bulk_extraction",      # Cycle 1: Bulk code analysis
    "cross_enrichment",     # Cycle 2: Cross-enrichment
    "conflict_detection",   # Cycle 3: Conflict detection
    "quality_synthesis",    # Cycle 4: Quality synthesis
    "final_synthesis",      # Cycle 5: Final synthesis (premium)
]


# Task-to-Provider routing configuration
# Priority: Ollama (free) -> Claude (balanced) -> Codex (deep)
TASK_ROUTING: Dict[TaskType, str] = {
    # Free tier (Ollama - local)
    "simple_generation": "ollama",      # Free, fast
    "quick_fix": "ollama",              # Free, local
    "documentation": "ollama",          # Mistral is good at docs
    "debugging": "ollama",              # Codellama specializes

    # Balanced tier (Claude Sonnet)
    "standard_work": "claude_sonnet",   # Good quality, reasonable cost
    "code_review": "claude_sonnet",     # Balanced analysis
    "planning": "claude_sonnet",        # Project planning
    "estimation": "claude_sonnet",      # Effort estimation

    # Deep tier (Codex or Claude Opus)
    "architecture": "codex",            # Complex multi-file reasoning
    "security_audit": "codex",          # Critical analysis
    "complex_analysis": "codex",        # Deep investigation
    "refactoring": "codex",             # Structural changes

    # Week 90: Deep Extraction Pipeline routing
    # Cycle 1: Bulk analysis - Ollama (free) or Qwen (cheap)
    "bulk_extraction": "qwen",          # Ultra-cheap: $0.05/M, 1M context

    # Cycle 2: Cross-enrichment - Gemini (large context) or Groq (fast)
    "cross_enrichment": "gemini",       # 1M context, good at cross-referencing

    # Cycle 3: Conflict detection - OpenAI (coding)
    "conflict_detection": "openai",     # GPT-4o best for code conflicts

    # Cycle 4: Quality synthesis - Gemini Pro or OpenAI
    "quality_synthesis": "gemini_pro",  # Balanced quality/cost

    # Cycle 5: Final synthesis - Anthropic (premium)
    "final_synthesis": "anthropic",     # Claude Opus 4.5 for final synthesis
}

# Default models per provider
DEFAULT_MODELS = {
    # Original providers
    "ollama": "qwen2.5-coder:7b",
    "codex": "gpt-5.1-codex-max",
    "claude_haiku": "haiku",
    "claude_sonnet": "sonnet",
    "claude_opus": "opus",
    # Week 90: New cloud providers
    "groq": "llama-3.3-70b-versatile",      # Best balance of speed/quality
    "groq_fast": "llama-3.1-8b-instant",    # 840 TPS, ultra-fast
    "gemini": "gemini-2.5-flash",           # 1M context, balanced
    "gemini_pro": "gemini-2.5-pro",         # Higher quality
    "openai": "gpt-4o",                     # Best for coding
    "openai_fast": "gpt-4o-mini",           # Fast and cheap
    "anthropic": "claude-opus-4-5-20251101", # Premium synthesis
    "anthropic_fast": "claude-3-5-haiku-20241022",  # Fast Claude
    "qwen": "qwen-turbo",                   # Ultra-cheap bulk
    "qwen_long": "qwen-long",               # 10M context
}


# Provider name to adapter name mapping
PROVIDER_TO_ADAPTER = {
    "ollama": "ollama",
    "codex": "codex",
    "claude": "claude",
    "claude_haiku": "claude",
    "claude_sonnet": "claude",
    "claude_opus": "claude",
    "groq": "groq",
    "groq_fast": "groq",
    "gemini": "gemini",
    "gemini_pro": "gemini",
    "openai": "codex",  # OpenAI uses similar format to Codex
    "openai_fast": "codex",
    "anthropic": "claude",  # Anthropic uses Claude format
    "anthropic_fast": "claude",
    "qwen": "qwen",
    "qwen_long": "qwen",
}


class ProviderRegistry:
    """
    Central registry for LLM providers.

    Manages provider instances and routes tasks to optimal providers
    based on task type, cost, and availability.

    Week 102: Now includes LLMContextAdapter for provider-specific prompt formatting.

    Usage:
        registry = ProviderRegistry()

        # Route automatically
        provider = registry.route_task("architecture")
        response = await provider.generate(request)

        # Get specific provider
        codex = registry.get_provider("codex")

        # Week 102: Adapt context for provider
        adapted_prompt = registry.adapt_context(context, "claude")
    """

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._context_adapter = None
        self._initialize_providers()
        self._initialize_context_adapter()

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

        # Claude variants (Anthropic CLI)
        self._providers["claude_haiku"] = ClaudeProvider(model="haiku")
        self._providers["claude_sonnet"] = ClaudeProvider(model="sonnet")
        self._providers["claude_opus"] = ClaudeProvider(model="opus")

        # Alias for default Claude
        self._providers["claude"] = self._providers["claude_sonnet"]

        # Week 90: New cloud providers for Deep Extraction
        # Groq - Ultra-fast inference (300-840 TPS)
        self._providers["groq"] = GroqProvider(
            model=DEFAULT_MODELS["groq"]
        )
        self._providers["groq_fast"] = GroqProvider(
            model=DEFAULT_MODELS["groq_fast"]
        )

        # Gemini - Google, 1M context window
        self._providers["gemini"] = GeminiProvider(
            model=DEFAULT_MODELS["gemini"]
        )
        self._providers["gemini_pro"] = GeminiProvider(
            model=DEFAULT_MODELS["gemini_pro"]
        )

        # OpenAI - Native API (GPT-4o, o1)
        self._providers["openai"] = OpenAIProvider(
            model=DEFAULT_MODELS["openai"]
        )
        self._providers["openai_fast"] = OpenAIProvider(
            model=DEFAULT_MODELS["openai_fast"]
        )

        # Anthropic - Native API (Claude Opus 4.5)
        self._providers["anthropic"] = AnthropicProvider(
            model=DEFAULT_MODELS["anthropic"]
        )
        self._providers["anthropic_fast"] = AnthropicProvider(
            model=DEFAULT_MODELS["anthropic_fast"]
        )

        # Qwen - Alibaba, ultra-cheap bulk processing
        self._providers["qwen"] = QwenProvider(
            model=DEFAULT_MODELS["qwen"]
        )
        self._providers["qwen_long"] = QwenProvider(
            model=DEFAULT_MODELS["qwen_long"]
        )

    def _initialize_context_adapter(self) -> None:
        """Week 102: Initialize LLMContextAdapter for provider-specific formatting."""
        if not CONTEXT_ADAPTER_AVAILABLE:
            logger.info("LLMContextAdapter not available - running without context adaptation")
            self._context_adapter = None
            return

        try:
            self._context_adapter = LLMContextAdapter()
            logger.debug("Initialized LLMContextAdapter with providers: %s",
                        self._context_adapter.supported_providers)
        except Exception as e:
            logger.warning(f"Failed to initialize LLMContextAdapter: {e}")
            self._context_adapter = None

    def adapt_context(self, context, provider_name: str) -> Optional[str]:
        """
        Week 102: Adapt ProjectContext for a specific provider.

        Args:
            context: ProjectContext object or dict with context data
            provider_name: Target provider name

        Returns:
            Provider-optimized context string, or None if adaptation not available
        """
        if not self._context_adapter:
            return None

        # Get adapter name for this provider
        adapter_name = PROVIDER_TO_ADAPTER.get(provider_name, "universal")

        try:
            # If context is a dict, convert to ProjectContext
            if isinstance(context, dict) and ProjectContext:
                context = ProjectContext(
                    project_name=context.get("project_name", ""),
                    description=context.get("description", ""),
                    tech_stack=context.get("tech_stack", []),
                    ground_rules=context.get("ground_rules", []),
                    code_conventions=context.get("code_conventions", []),
                    architecture_notes=context.get("architecture_notes", ""),
                    active_context=context.get("active_context", []),
                )

            return self._context_adapter.adapt(context, adapter_name)
        except Exception as e:
            logger.warning(f"Context adaptation failed for {provider_name}: {e}")
            return None

    def create_adapted_request(
        self,
        provider_name: str,
        prompt: str,
        context = None,
        **kwargs
    ) -> LLMRequest:
        """
        Week 102: Create an LLMRequest with provider-adapted context.

        Args:
            provider_name: Target provider name
            prompt: The main prompt/question
            context: Optional ProjectContext to adapt
            **kwargs: Additional LLMRequest parameters

        Returns:
            LLMRequest with adapted system prompt
        """
        system_prompt = kwargs.pop("system", "")

        # Adapt context if provided
        if context:
            adapted = self.adapt_context(context, provider_name)
            if adapted:
                if system_prompt:
                    system_prompt = f"{adapted}\n\n{system_prompt}"
                else:
                    system_prompt = adapted

        return LLMRequest(
            prompt=prompt,
            system=system_prompt if system_prompt else None,
            **kwargs
        )

    async def generate_with_adapted_context(
        self,
        provider_name: str,
        prompt: str,
        context = None,
        **kwargs
    ):
        """
        Week 102: Generate response using provider with adapted context.

        Convenience method that adapts context and generates in one call.

        Args:
            provider_name: Target provider name
            prompt: The main prompt/question
            context: Optional ProjectContext to adapt
            **kwargs: Additional LLMRequest parameters

        Returns:
            LLMResponse from the provider
        """
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        request = self.create_adapted_request(provider_name, prompt, context, **kwargs)
        return await provider.generate(request)

    @property
    def context_adapter_available(self) -> bool:
        """Check if context adapter is available."""
        return self._context_adapter is not None

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
