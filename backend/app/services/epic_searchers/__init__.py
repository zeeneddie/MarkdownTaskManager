"""
Epic Searchers - Journey-based and Folder-based Epic Detection

This module provides industry-agnostic epic detection for any codebase:
- JourneyBasedEpicSearcher: Detects epics from user journeys through the application
- GenericEpicSearcher: Detects epics from folder structure
- CombinedEpicSearcher: Combines both approaches for comprehensive detection

Created: Week 158 (2026-01-21)
Fase: 24.8 - Epic Generation Fix
"""

from .models import (
    EpicGenerationStrategy,
    EpicSearchConfig,
    JourneySearchConfig,
    CombinedSearchConfig,
    DetectedScreen,
    DetectedJourney,
    DetectedFolder,
    DetectedEpic,
    DetectedFeature,
)
from .journey_epic_searcher import JourneyBasedEpicSearcher
from .generic_epic_searcher import GenericEpicSearcher
from .combined_epic_searcher import CombinedEpicSearcher

__all__ = [
    # Config classes
    "EpicGenerationStrategy",
    "EpicSearchConfig",
    "JourneySearchConfig",
    "CombinedSearchConfig",
    # Data models
    "DetectedScreen",
    "DetectedJourney",
    "DetectedFolder",
    "DetectedEpic",
    "DetectedFeature",
    # Searchers
    "JourneyBasedEpicSearcher",
    "GenericEpicSearcher",
    "CombinedEpicSearcher",
]
