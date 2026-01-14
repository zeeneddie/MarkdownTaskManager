"""
Confucius Hierarchical Memory System.

Three memory scopes:
1. session_scope: Cross-task insights (permanent)
2. entry_scope: Per-task summaries (30 days)
3. runnable_scope: Tool execution outputs (7 days)

Components:
- types: Memory dataclasses
- hierarchical: Main HierarchicalMemory class
- repository: Database persistence
- compressor: Context compression
- note_taker: Cross-session learning
"""

from .types import (
    MemoryScope,
    MemoryNode,
    SessionMemory,
    EntryMemory,
    RunnableMemory,
    RelevantMemory,
)
from .hierarchical import HierarchicalMemory
from .compressor import ContextCompressor, CompressionResult, RelevanceLevel
from .note_taker import NoteTaker, Note, NoteType

__all__ = [
    # Types
    "MemoryScope",
    "MemoryNode",
    "SessionMemory",
    "EntryMemory",
    "RunnableMemory",
    "RelevantMemory",
    # Classes
    "HierarchicalMemory",
    "ContextCompressor",
    "CompressionResult",
    "RelevanceLevel",
    "NoteTaker",
    "Note",
    "NoteType",
]
