"""
Context Engineering Module for Confucius Orchestrator.

Provides intelligent reference loading and context optimization
for token-efficient agent execution.

Components:
- ReferenceSelector: Semantic matching for reference docs
- ReferenceRegistry: Management of available references
- ContextOptimizer: Token reduction via selective loading
"""

from .reference_selector import (
    ReferenceSelector,
    Reference,
    ReferenceMatch,
    ReferenceCategory,
    create_reference_selector,
)
from .reference_registry import (
    ReferenceRegistry,
    create_reference_registry,
)
from .context_optimizer import (
    ContextOptimizer,
    OptimizedContext,
    create_context_optimizer,
)

__all__ = [
    # Reference Selector
    "ReferenceSelector",
    "Reference",
    "ReferenceMatch",
    "ReferenceCategory",
    "create_reference_selector",
    # Reference Registry
    "ReferenceRegistry",
    "create_reference_registry",
    # Context Optimizer
    "ContextOptimizer",
    "OptimizedContext",
    "create_context_optimizer",
]
