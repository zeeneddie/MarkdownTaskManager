"""
Confucius Code Agent Orchestrator Module.

This module implements the Confucius orchestration pattern for MarQed,
providing hierarchical memory, cross-session learning, and quality gates
for all 11 AI agents.

Based on Meta/Harvard CCA Research (December 2025).

Components:
- orchestrator: Main ConfuciusOrchestrator class
- config: Configuration management
- extensions: Agent extension wrappers
- memory: Hierarchical working memory
- quality: Quality gate evaluation
"""

from .orchestrator import ConfuciusOrchestrator, OrchestratorState, ExecutionResult
from .config import ConfuciusConfig

__all__ = [
    "ConfuciusOrchestrator",
    "ConfuciusConfig",
    "OrchestratorState",
    "ExecutionResult",
]
