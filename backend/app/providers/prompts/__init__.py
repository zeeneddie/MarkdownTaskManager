"""
Deep Extraction Prompt Templates

Week 90: Structured prompts for the 5-cycle extraction pipeline.

Each cycle has specialized prompts optimized for its task and LLM provider.
"""

from .cycle1_bulk import CYCLE1_PROMPTS
from .cycle2_enrichment import CYCLE2_PROMPTS
from .cycle3_conflicts import CYCLE3_PROMPTS
from .cycle4_quality import CYCLE4_PROMPTS
from .cycle5_synthesis import CYCLE5_PROMPTS

__all__ = [
    "CYCLE1_PROMPTS",
    "CYCLE2_PROMPTS",
    "CYCLE3_PROMPTS",
    "CYCLE4_PROMPTS",
    "CYCLE5_PROMPTS",
]
