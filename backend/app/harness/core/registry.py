"""
Plugin Registry - Central registry for harness modules.

Supports:
- Plug-and-play module mounting
- Hot-swapping at runtime
- Health checking
- Multiple adapter implementations
"""

from typing import Dict, Type, Optional, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModuleType(str, Enum):
    """Types of harness modules."""
    CONSTRAINTS = "constraints"
    CONTEXT = "context"
    TOOLS = "tools"
    VERSIONING = "versioning"


class PluginRegistry:
    """
    Central registry for harness modules.

    Singleton pattern ensures consistent state across application.

    Usage:
        from app.harness import registry, ModuleType

        # Register an adapter
        registry.register_adapter(
            "langchain_guardrails",
            LangChainGuardrailsAdapter,
            ModuleType.CONSTRAINTS
        )

        # Mount as active module
        registry.mount(
            ModuleType.CONSTRAINTS,
            "langchain_guardrails",
            {"model": "gpt-4"}
        )

        # Use the module
        constraints = registry.get(ModuleType.CONSTRAINTS)
        result = await constraints.check_action(...)

        # Hot-swap at runtime
        registry.swap(ModuleType.CONSTRAINTS, "nemo_guardrails")
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules: Dict[ModuleType, Any] = {}
            cls._instance._adapters: Dict[str, Type] = {}
            cls._instance._adapter_metadata: Dict[str, Dict[str, Any]] = {}
        return cls._instance

    def register_adapter(
        self,
        name: str,
        adapter_class: Type,
        module_type: ModuleType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register an adapter implementation.

        Args:
            name: Unique adapter name (e.g., "langchain_guardrails")
            adapter_class: The adapter class implementing the protocol
            module_type: Which module type this adapter is for
            metadata: Optional metadata (version, author, description)

        Example:
            registry.register_adapter(
                "langchain_guardrails",
                LangChainGuardrailsAdapter,
                ModuleType.CONSTRAINTS,
                {"version": "1.0", "author": "MarQed"}
            )
        """
        key = f"{module_type.value}:{name}"
        self._adapters[key] = adapter_class
        self._adapter_metadata[key] = metadata or {}
        logger.info(f"Registered adapter: {key}")

    def unregister_adapter(
        self,
        name: str,
        module_type: ModuleType
    ) -> bool:
        """Remove an adapter registration."""
        key = f"{module_type.value}:{name}"
        if key in self._adapters:
            del self._adapters[key]
            del self._adapter_metadata[key]
            logger.info(f"Unregistered adapter: {key}")
            return True
        return False

    def list_adapters(
        self,
        module_type: Optional[ModuleType] = None
    ) -> List[Dict[str, Any]]:
        """
        List all registered adapters.

        Args:
            module_type: Filter by module type, or None for all

        Returns:
            List of adapter info dicts
        """
        result = []
        for key, adapter_class in self._adapters.items():
            mt, name = key.split(":", 1)
            if module_type is None or mt == module_type.value:
                result.append({
                    "name": name,
                    "module_type": mt,
                    "class": adapter_class.__name__,
                    "metadata": self._adapter_metadata.get(key, {}),
                    "mounted": self._modules.get(ModuleType(mt)) is not None
                })
        return result

    def mount(
        self,
        module_type: ModuleType,
        adapter_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Mount an adapter as the active module.

        Args:
            module_type: Which module slot to mount into
            adapter_name: Name of registered adapter
            config: Configuration dict passed to adapter __init__

        Returns:
            The mounted adapter instance

        Raises:
            ValueError: If adapter is not registered

        Example:
            registry.mount(
                ModuleType.CONSTRAINTS,
                "langchain_guardrails",
                {"model": "gpt-4"}
            )
        """
        key = f"{module_type.value}:{adapter_name}"

        if key not in self._adapters:
            available = [k for k in self._adapters if k.startswith(module_type.value)]
            raise ValueError(
                f"Unknown adapter: {key}. "
                f"Available for {module_type.value}: {available}"
            )

        adapter_class = self._adapters[key]
        instance = adapter_class(**(config or {}))

        self._modules[module_type] = instance
        logger.info(f"Mounted {adapter_name} for {module_type.value}")

        return instance

    def unmount(self, module_type: ModuleType) -> bool:
        """
        Unmount the current module.

        Calls cleanup() on the module if available.
        """
        if module_type in self._modules:
            module = self._modules[module_type]
            if hasattr(module, 'cleanup'):
                module.cleanup()
            del self._modules[module_type]
            logger.info(f"Unmounted module for {module_type.value}")
            return True
        return False

    def get(self, module_type: ModuleType) -> Any:
        """
        Get the currently mounted module.

        Raises:
            ValueError: If no module is mounted for the type
        """
        if module_type not in self._modules:
            raise ValueError(
                f"No module mounted for {module_type.value}. "
                f"Use registry.mount() first."
            )
        return self._modules[module_type]

    def get_optional(self, module_type: ModuleType) -> Optional[Any]:
        """Get module if mounted, None otherwise."""
        return self._modules.get(module_type)

    def swap(
        self,
        module_type: ModuleType,
        adapter_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Hot-swap a module at runtime.

        Safely unmounts current module before mounting new one.

        Returns:
            The newly mounted adapter instance
        """
        self.unmount(module_type)
        return self.mount(module_type, adapter_name, config)

    def is_mounted(self, module_type: ModuleType) -> bool:
        """Check if a module is mounted."""
        return module_type in self._modules

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all mounted modules.

        Returns:
            Dict mapping module type to health status
        """
        results = {}
        for module_type in ModuleType:
            if module_type in self._modules:
                module = self._modules[module_type]
                try:
                    if hasattr(module, 'health_check'):
                        results[module_type.value] = module.health_check()
                    else:
                        results[module_type.value] = True
                except Exception as e:
                    logger.error(f"Health check failed for {module_type}: {e}")
                    results[module_type.value] = False
            else:
                results[module_type.value] = None  # Not mounted
        return results

    def get_status(self) -> Dict[str, Any]:
        """Get full status of the registry."""
        return {
            "mounted_modules": {
                mt.value: type(self._modules[mt]).__name__
                for mt in ModuleType
                if mt in self._modules
            },
            "registered_adapters": len(self._adapters),
            "health": self.health_check()
        }

    def reset(self) -> None:
        """
        Reset the registry (for testing).

        Unmounts all modules and clears adapter registrations.
        """
        for module_type in list(self._modules.keys()):
            self.unmount(module_type)
        self._adapters.clear()
        self._adapter_metadata.clear()
        logger.info("Registry reset")


# Global singleton instance
registry = PluginRegistry()
