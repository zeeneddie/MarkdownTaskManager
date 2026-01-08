"""
LLM Context Adapter Service - Week 101

Main service that transforms universal PROJECT_CONTEXT.md
to LLM-specific formats for multi-LLM support.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from .project_context import ProjectContext, ProjectContextParser
from .adapters.base import BaseAdapter, UniversalAdapter
from .adapters.claude_adapter import ClaudeAdapter
from .adapters.codex_adapter import CodexAdapter
from .adapters.ollama_adapter import OllamaAdapter
from .adapters.qwen_adapter import QwenAdapter
from .adapters.gemini_adapter import GeminiAdapter
from .adapters.groq_adapter import GroqAdapter

logger = logging.getLogger(__name__)


class LLMContextAdapter:
    """
    Transform universal PROJECT_CONTEXT.md to LLM-specific formats.

    This service reads a universal project context file and generates
    provider-specific context files optimized for each LLM.

    Providers:
    - claude: XML-structured, detailed reasoning
    - codex: Comment-block style, code completion focus
    - ollama: Minimal system prompt, efficiency focus
    - qwen: Structured sections, bilingual support
    - gemini: JSON-friendly, structured data
    - groq: Speed-optimized, minimal tokens

    Usage:
        adapter = LLMContextAdapter()

        # Generate for single provider
        content = adapter.adapt_for_provider(context, "claude")

        # Generate all provider files
        files = adapter.generate_all(context, output_dir="/project/root")

        # Parse and generate from file
        files = adapter.process_context_file("PROJECT_CONTEXT.md", "/output")
    """

    # Registry of available adapters
    ADAPTERS: Dict[str, Type[BaseAdapter]] = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "ollama": OllamaAdapter,
        "qwen": QwenAdapter,
        "gemini": GeminiAdapter,
        "groq": GroqAdapter,
        "universal": UniversalAdapter,
    }

    # Provider aliases for convenience
    ALIASES: Dict[str, str] = {
        "anthropic": "claude",
        "gpt": "codex",
        "openai": "codex",
        "local": "ollama",
        "alibaba": "qwen",
        "google": "gemini",
    }

    def __init__(self):
        """Initialize the context adapter with all registered adapters."""
        self._adapters: Dict[str, BaseAdapter] = {}
        self._parser = ProjectContextParser()

        # Instantiate all adapters
        for name, adapter_cls in self.ADAPTERS.items():
            self._adapters[name] = adapter_cls()

    @property
    def supported_providers(self) -> List[str]:
        """Return list of supported provider names."""
        return list(self.ADAPTERS.keys())

    def get_adapter(self, provider: str) -> BaseAdapter:
        """
        Get adapter for a specific provider.

        Args:
            provider: Provider name or alias

        Returns:
            BaseAdapter instance for the provider

        Raises:
            ValueError: If provider is not supported
        """
        # Resolve aliases
        provider_key = self.ALIASES.get(provider.lower(), provider.lower())

        if provider_key not in self._adapters:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: {', '.join(self.supported_providers)}"
            )

        return self._adapters[provider_key]

    def adapt(self, context: ProjectContext, provider: str) -> str:
        """
        Transform context for specific LLM provider.

        Args:
            context: Universal ProjectContext object
            provider: Provider name (claude, codex, ollama, qwen, gemini, groq)

        Returns:
            String content in provider-specific format
        """
        adapter = self.get_adapter(provider)
        return adapter.transform(context)

    def adapt_for_provider(self, context: ProjectContext, provider: str) -> str:
        """Alias for adapt() for backward compatibility."""
        return self.adapt(context, provider)

    def generate_all(
        self,
        context: ProjectContext,
        output_dir: str,
        providers: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generate context files for all (or specified) providers.

        Args:
            context: Universal ProjectContext object
            output_dir: Root directory for output files
            providers: Optional list of providers to generate for
                      (default: all supported providers)

        Returns:
            Dict mapping provider names to output file paths
        """
        output_root = Path(output_dir)
        generated_files: Dict[str, str] = {}

        # Use all providers if none specified
        target_providers = providers or list(self._adapters.keys())

        for provider_name in target_providers:
            if provider_name not in self._adapters:
                logger.warning(f"Skipping unknown provider: {provider_name}")
                continue

            adapter = self._adapters[provider_name]

            try:
                # Generate content
                content = adapter.transform(context)

                # Determine output path
                output_path = output_root / adapter.get_output_path()

                # Ensure directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                output_path.write_text(content, encoding="utf-8")

                generated_files[provider_name] = str(output_path)
                logger.info(f"Generated {provider_name} context: {output_path}")

            except Exception as e:
                logger.error(f"Failed to generate {provider_name} context: {e}")

        return generated_files

    def process_context_file(
        self,
        context_file: str,
        output_dir: str,
        providers: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Parse context file and generate all provider-specific files.

        Args:
            context_file: Path to PROJECT_CONTEXT.md
            output_dir: Root directory for output files
            providers: Optional list of providers to generate for

        Returns:
            Dict mapping provider names to output file paths
        """
        # Parse context file
        context = self._parser.parse_file(context_file)

        # Generate all files
        return self.generate_all(context, output_dir, providers)

    def get_provider_info(self, provider: str) -> Dict[str, str]:
        """
        Get information about a provider adapter.

        Args:
            provider: Provider name

        Returns:
            Dict with provider info (name, output_path, description)
        """
        adapter = self.get_adapter(provider)

        return {
            "name": adapter.provider_name,
            "output_directory": adapter.output_directory,
            "output_filename": adapter.output_filename,
            "output_path": adapter.get_output_path(),
        }

    def list_providers(self) -> List[Dict[str, str]]:
        """
        List all available providers with their info.

        Returns:
            List of provider info dicts
        """
        return [
            self.get_provider_info(name)
            for name in self.supported_providers
        ]


# Convenience function for quick adaptation
def adapt_context(
    context_file: str,
    provider: str,
    output_dir: Optional[str] = None,
) -> str:
    """
    Quick function to adapt a context file for a specific provider.

    Args:
        context_file: Path to PROJECT_CONTEXT.md
        provider: Target provider name
        output_dir: Optional output directory (if None, returns content only)

    Returns:
        Generated content string
    """
    adapter_service = LLMContextAdapter()
    parser = ProjectContextParser()

    context = parser.parse_file(context_file)
    content = adapter_service.adapt(context, provider)

    if output_dir:
        adapter = adapter_service.get_adapter(provider)
        output_path = Path(output_dir) / adapter.get_output_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
