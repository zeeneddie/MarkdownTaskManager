"""
Priority Mapper - Infer Plane-compatible priorities from MarQed signals.

Uses data from multiple pipeline stages to determine priority:
- Peter enrichment priority (M5/M8 - if available, highest confidence)
- Domain confidence from M7 (high confidence = core domain = higher priority)
- Complexity from M8 (very_high = needs early attention)
- Story type hierarchy (data_migration > business_rule > crud > validation)
- Direct mapping from MarQed priority strings to Plane enums
"""

import logging
from typing import Any, Dict, Optional

from .models import PlanePriority

logger = logging.getLogger(__name__)

# Direct mapping from MarQed priority strings to Plane priorities
_MARQED_TO_PLANE = {
    "critical": PlanePriority.urgent,
    "urgent": PlanePriority.urgent,
    "high": PlanePriority.high,
    "medium": PlanePriority.medium,
    "low": PlanePriority.low,
    "none": PlanePriority.none,
}

# Story types ranked by typical migration importance
_STORY_TYPE_PRIORITY = {
    "data_migration": PlanePriority.high,
    "integration": PlanePriority.high,
    "business_rule": PlanePriority.medium,
    "api": PlanePriority.medium,
    "crud": PlanePriority.medium,
    "form": PlanePriority.medium,
    "validation": PlanePriority.low,
    "migration": PlanePriority.medium,
}

# Complexity -> priority boost (very_high needs early attention for risk mitigation)
_COMPLEXITY_PRIORITY = {
    "very_high": PlanePriority.high,
    "high": PlanePriority.medium,
    "medium": PlanePriority.medium,
    "low": PlanePriority.low,
}

# Numeric values for priority comparison (higher = more urgent)
_PRIORITY_VALUE = {
    PlanePriority.urgent: 4,
    PlanePriority.high: 3,
    PlanePriority.medium: 2,
    PlanePriority.low: 1,
    PlanePriority.none: 0,
}


def _max_priority(*priorities: PlanePriority) -> PlanePriority:
    """Return the highest priority from the given values."""
    return max(priorities, key=lambda p: _PRIORITY_VALUE[p])


class PriorityMapper:
    """
    Maps MarQed signals to Plane-compatible priorities.

    Priority inference chain (highest confidence first):
    1. Peter enrichment (explicit business priority)
    2. Domain confidence (core domains = higher priority)
    3. Story type (data_migration > business_rule > crud)
    4. Complexity (very_high gets priority boost)
    5. Default: medium
    """

    def map_story_priority(
        self,
        story_priority: str = "medium",
        story_type: str = "",
        complexity: str = "medium",
        peter_priority: Optional[str] = None,
        domain_confidence: Optional[float] = None,
    ) -> PlanePriority:
        """
        Determine priority for a story using all available signals.

        Args:
            story_priority: Priority from M8 GeneratedStory (if explicitly set)
            story_type: Story type (crud, form, api, business_rule, etc.)
            complexity: Story complexity level
            peter_priority: Priority from Peter enrichment (highest confidence)
            domain_confidence: Domain confidence from M7 (0.0-1.0)
        """
        # Signal 1: Peter enrichment (highest confidence - explicit business input)
        if peter_priority:
            mapped = _MARQED_TO_PLANE.get(peter_priority.lower())
            if mapped:
                return mapped

        # Signal 2: Explicit priority from M8 (if not default)
        if story_priority and story_priority != "medium":
            mapped = _MARQED_TO_PLANE.get(story_priority.lower())
            if mapped:
                return mapped

        # Signal 3: Composite from story type + complexity + domain confidence
        type_priority = _STORY_TYPE_PRIORITY.get(story_type, PlanePriority.medium)
        complexity_priority = _COMPLEXITY_PRIORITY.get(complexity, PlanePriority.medium)

        # Domain confidence boost: >0.85 = core domain = priority bump
        domain_priority = PlanePriority.medium
        if domain_confidence is not None:
            if domain_confidence >= 0.85:
                domain_priority = PlanePriority.high
            elif domain_confidence <= 0.4:
                domain_priority = PlanePriority.low

        return _max_priority(type_priority, complexity_priority, domain_priority)

    def map_feature_priority(
        self,
        feature_complexity: str = "medium",
        story_priorities: Optional[list] = None,
        domain_confidence: Optional[float] = None,
    ) -> PlanePriority:
        """
        Determine priority for a feature (derived from its stories).

        Feature priority is the highest priority among its stories,
        with domain confidence as additional signal.
        """
        candidates = [_COMPLEXITY_PRIORITY.get(feature_complexity, PlanePriority.medium)]

        if story_priorities:
            candidates.extend(story_priorities)

        if domain_confidence is not None and domain_confidence >= 0.85:
            candidates.append(PlanePriority.high)

        return _max_priority(*candidates) if candidates else PlanePriority.medium

    def map_epic_priority(
        self,
        epic_complexity: str = "medium",
        domain_confidence: Optional[float] = None,
        feature_priorities: Optional[list] = None,
    ) -> PlanePriority:
        """
        Determine priority for an epic (derived from domain and features).

        Epic priority is driven by domain confidence (core domains first)
        and the highest feature priority.
        """
        candidates = [_COMPLEXITY_PRIORITY.get(epic_complexity, PlanePriority.medium)]

        # Domain confidence is the primary signal for epics
        if domain_confidence is not None:
            if domain_confidence >= 0.85:
                candidates.append(PlanePriority.high)
            elif domain_confidence >= 0.70:
                candidates.append(PlanePriority.medium)
            elif domain_confidence <= 0.4:
                candidates.append(PlanePriority.low)

        if feature_priorities:
            candidates.extend(feature_priorities)

        return _max_priority(*candidates) if candidates else PlanePriority.medium
