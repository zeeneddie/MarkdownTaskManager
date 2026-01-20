"""
Confucius Data Models.

Models for workflow stages and extraction results.
"""

from .user_journey import (
    # Enums
    PersonaType,
    JourneyComplexity,
    InteractionType,
    # Core models
    Persona,
    ScreenInfo,
    JourneyStep,
    ErrorPath,
    UserJourney,
    ScreenFlow,
    RolePermissionMatrix,
    # Result
    UserJourneyExtractionResult,
)

__all__ = [
    # Enums
    "PersonaType",
    "JourneyComplexity",
    "InteractionType",
    # Core models
    "Persona",
    "ScreenInfo",
    "JourneyStep",
    "ErrorPath",
    "UserJourney",
    "ScreenFlow",
    "RolePermissionMatrix",
    # Result
    "UserJourneyExtractionResult",
]
