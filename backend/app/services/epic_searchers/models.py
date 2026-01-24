"""
Data models for Epic Detection

Contains all dataclasses and configuration objects for:
- Screen detection
- Journey detection
- Folder-based detection
- Epic and feature generation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# Constants - Standard Folder Patterns
# =============================================================================

STANDARD_SOURCE_FOLDERS = [
    # Primary source folders
    "src",
    "source",
    "app",
    "application",
    # Web applications
    "WEB",
    "web",
    "webapp",
    "www",
    "public",
    # Libraries and modules
    "lib",
    "libs",
    "library",
    "modules",
    "packages",
    # Backend/Frontend separation
    "backend",
    "frontend",
    "server",
    "client",
    # Domain-driven folders
    "domain",
    "core",
    "features",
    "components",
    # .NET specific
    "Controllers",
    "Services",
    "Models",
    "Views",
]

INFRASTRUCTURE_FOLDERS = [
    "api",
    "database",
    "db",
    "scripts",
    "migrations",
    "config",
    "infrastructure",
    "shared",
    "common",
    "utils",
    "helpers",
    "tests",
]

# Module type patterns (reused from BrownPaperService)
MODULE_TYPE_PATTERNS = {
    "service": [r"service", r"svc", r"_service\.py$"],
    "repository": [r"repository", r"repo", r"_repository\.py$"],
    "model": [r"model", r"entity", r"_model\.py$"],
    "controller": [r"controller", r"handler", r"_controller\.py$"],
    "api": [r"api", r"endpoint", r"_api\.py$"],
    "util": [r"util", r"helper", r"_util\.py$"],
    "config": [r"config", r"settings", r"_config\.py$"],
    "test": [r"test", r"spec", r"_test\.py$"],
    "migration": [r"migration", r"alembic"],
    "form": [r"Form\.vb$", r"\.aspx", r"UserControl"],
    "data_access": [r"DataAccess", r"DAL", r"Data\.vb$"],
}

# Architecture patterns (reused from BrownPaperService)
ARCHITECTURE_PATTERNS = {
    "ddd": ["domain", "aggregate", "value_object", "repository", "entity"],
    "mvc": ["model", "view", "controller"],
    "layered": ["presentation", "application", "domain", "infrastructure"],
    "microservices": ["service", "gateway", "discovery", "config"],
    "cqrs": ["command", "query", "handler", "event"],
    "hexagonal": ["port", "adapter", "application", "domain"],
}


# =============================================================================
# Enums
# =============================================================================

class EpicGenerationStrategy(Enum):
    """How to generate epics from folder structure."""
    FOLDER_BASED = "folder"         # 1 epic per top-level folder
    GROUPED = "grouped"             # Group related folders into epics
    LAYER_BASED = "layer"           # Group by architectural layer
    HYBRID = "hybrid"               # Combine folder + grouping


# =============================================================================
# Screen and Journey Detection Models
# =============================================================================

@dataclass
class DetectedScreen:
    """A screen/page detected in the application."""
    id: str
    name: str
    file_path: str
    screen_type: str  # menu, form, list, detail, edit, dashboard, login, report, create

    # Navigation
    entry_points: List[str] = field(default_factory=list)   # Where can you come from?
    exit_points: List[str] = field(default_factory=list)    # Where can you go to?

    # Interactions
    forms: List[str] = field(default_factory=list)          # Forms on this screen
    buttons: List[str] = field(default_factory=list)        # Buttons/actions
    messages: List[str] = field(default_factory=list)       # Messages/validations/alerts

    # Context
    data_entities: List[str] = field(default_factory=list)  # Which data is shown/edited?
    required_role: Optional[str] = None


@dataclass
class DetectedJourney:
    """A user journey through the application."""
    id: str
    name: str
    description: str

    # Journey path
    start_screen: str
    screen_path: List[str] = field(default_factory=list)    # Screens in order
    end_screens: List[str] = field(default_factory=list)    # Possible end points

    # User context
    persona: str = "User"
    goal: str = ""

    # Interactions discovered
    available_actions: List[str] = field(default_factory=list)   # All buttons/actions in journey
    possible_messages: List[str] = field(default_factory=list)   # All messages that can appear
    validations: List[str] = field(default_factory=list)         # Validation rules

    # Outcomes
    success_outcomes: List[str] = field(default_factory=list)
    error_outcomes: List[str] = field(default_factory=list)


# =============================================================================
# Folder Detection Models
# =============================================================================

@dataclass
class DetectedFolder:
    """A folder detected as potential epic source."""
    name: str
    path: str
    depth: int
    file_count: int
    module_type: Optional[str] = None
    subfolders: List["DetectedFolder"] = field(default_factory=list)


# =============================================================================
# Epic and Feature Models
# =============================================================================

@dataclass
class DetectedFeature:
    """A feature detected within an epic."""
    id: str
    name: str
    description: str
    source_folder: str
    epic_id: str
    estimated_stories: int = 0


@dataclass
class DetectedEpic:
    """An epic detected from folder/journey analysis."""
    id: str
    name: str
    description: str
    source_folders: List[str]
    features: List[DetectedFeature] = field(default_factory=list)
    file_count: int = 0
    category: str = "business"  # business, infrastructure, integration, test
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Configuration Classes
# =============================================================================

@dataclass
class EpicSearchConfig:
    """Configuration for folder-based epic detection."""
    # Required
    project_path: str

    # Optional: Industry vocabulary (can be None for generic detection)
    domain_vocabulary: Optional[Any] = None

    # Strategy
    strategy: EpicGenerationStrategy = EpicGenerationStrategy.FOLDER_BASED

    # Folder scanning options
    source_folders: List[str] = field(default_factory=lambda: STANDARD_SOURCE_FOLDERS.copy())
    infrastructure_folders: List[str] = field(default_factory=lambda: INFRASTRUCTURE_FOLDERS.copy())
    max_depth: int = 2  # How deep to scan for sub-epics
    min_files_for_epic: int = 3  # Minimum files to create an epic

    # Grouping options (for GROUPED/HYBRID strategies)
    grouping_rules: Dict[str, List[str]] = field(default_factory=dict)

    # Output options
    include_infrastructure_epic: bool = True
    include_test_epic: bool = False


@dataclass
class JourneySearchConfig:
    """Configuration for journey-based epic detection."""
    project_path: str
    max_journey_depth: int = 6
    min_screens_per_journey: int = 2

    # Which technologies to scan
    scan_aspx: bool = True
    scan_vb: bool = True
    scan_razor: bool = True
    scan_jsx: bool = True
    scan_vue: bool = True
    scan_html: bool = True


@dataclass
class CombinedSearchConfig:
    """Configuration for combined epic detection."""
    project_path: str

    # Journey detection settings
    max_journey_depth: int = 6
    min_screens_per_journey: int = 2

    # Folder detection settings (for infrastructure)
    source_folders: List[str] = field(default_factory=lambda: STANDARD_SOURCE_FOLDERS.copy())
    infrastructure_folders: List[str] = field(default_factory=lambda: INFRASTRUCTURE_FOLDERS.copy())

    # Output settings
    include_infrastructure: bool = True
    include_uncovered_folders: bool = True
    min_confidence: float = 0.5
