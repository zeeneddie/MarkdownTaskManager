"""
Confucius Agent Extensions.

Each MarQed agent is wrapped as an extension with four lifecycle hooks:
1. on_input_messages: Modify prompts before LLM invocation
2. on_llm_output: Parse LLM responses into actions
3. on_execute: Execute actions (tool calls)
4. on_post: Record outcomes to memory/artifacts

Available Extensions:
- Felix: Architecture Specialist
- Quinn: Quality Specialist
- Eliza: Estimation Specialist
- Diana: Documentation Specialist
- Marcus: Maintenance Specialist
- Miguel: Metrics Specialist
- Tessa: Testing Specialist
- Peter: Product Owner
- Paul: Planning Specialist
- Betty: Business Analyst
- Vicky: Visual Designer/Validator
- StageReview: Automatic Stage-Based LLM Council Review (Fase 23.6)
"""

from .base import (
    BaseAgentExtension,
    ExtensionMetadata,
    ExtensionResult,
)
from .router import (
    ExtensionRouter,
    WorkflowRouter,
    RouteDecision,
    create_default_router,
)

# Agent Extensions
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
from .stage_review_extension import StageReviewExtension


__all__ = [
    # Base classes
    "BaseAgentExtension",
    "ExtensionMetadata",
    "ExtensionResult",
    # Router
    "ExtensionRouter",
    "WorkflowRouter",
    "RouteDecision",
    "create_default_router",
    # Agent Extensions
    "FelixExtension",
    "QuinnExtension",
    "ElizaExtension",
    "DianaExtension",
    "MarcusExtension",
    "MiguelExtension",
    "TessaExtension",
    "PeterExtension",
    "PaulExtension",
    "BettyExtension",
    "VickyExtension",
    # System Extensions
    "StageReviewExtension",
]


# Extension registry for quick lookup
EXTENSION_REGISTRY = {
    "Felix": FelixExtension,
    "Quinn": QuinnExtension,
    "Eliza": ElizaExtension,
    "Diana": DianaExtension,
    "Marcus": MarcusExtension,
    "Miguel": MiguelExtension,
    "Tessa": TessaExtension,
    "Peter": PeterExtension,
    "Paul": PaulExtension,
    "Betty": BettyExtension,
    "Vicky": VickyExtension,
    # System Extensions
    "StageReview": StageReviewExtension,
}


def get_extension_class(name: str) -> type:
    """
    Get extension class by name.

    Args:
        name: Agent name (e.g., "Felix", "Quinn")

    Returns:
        Extension class

    Raises:
        KeyError: If extension not found
    """
    return EXTENSION_REGISTRY[name]


def create_extension(name: str, **kwargs) -> BaseAgentExtension:
    """
    Create extension instance by name.

    Args:
        name: Agent name (e.g., "Felix", "Quinn")
        **kwargs: Arguments to pass to extension constructor

    Returns:
        Extension instance

    Raises:
        KeyError: If extension not found
    """
    cls = get_extension_class(name)
    return cls(**kwargs)
