# Generic Epic Searcher: Folder-Based Epic Generation

**Created:** Week 158 (2026-01-20)
**Priority:** HIGH
**Status:** TODO - Fase 24.8

---

## Executive Summary

Create a **generic, industry-agnostic Epic Searcher** that automatically detects business epics from any codebase by scanning folder structures and applying configurable domain vocabularies.

**Key Principles:**
- Works for ANY project (not tied to healthcare, finance, or any specific industry)
- Uses folder structure as primary epic source
- Industry vocabularies are optional configuration, not requirements
- Integrates with existing BrownPaperService and DomainVocabulary patterns

---

## Problem Statement

### Current Behavior

`IntakeToBacklogService._detect_domain_from_component()` uses hardcoded keywords:

```python
DOMAIN_KEYWORDS = {
    "patient": "Patient Management",
    "user": "User Management",
    "auth": "Authentication & Authorization",
    ...
}
```

**Result:** Projects with custom folder names (e.g., `Dossier`, `Afspraken`, `OrderProcessing`) all get mapped to "General".

### Desired Behavior

1. **Scan standard source folders** (`src`, `WEB`, `app`, `lib`, `modules`)
2. **Use folder names as epic candidates** (primary strategy)
3. **Apply optional industry vocabulary** for grouping (secondary strategy)
4. **Detect architecture patterns** to create infrastructure epics

---

## Architecture Design

### Core Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GenericEpicSearcher                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐    │
│  │ FolderScanner   │  │ PatternMatcher   │  │ DomainGrouper       │    │
│  │                 │  │                  │  │                     │    │
│  │ - Scan src/     │  │ - MODULE_TYPE    │  │ - Optional vocab    │    │
│  │ - Scan app/     │  │ - ARCHITECTURE   │  │ - Configurable      │    │
│  │ - Scan lib/     │  │ - DOC_PATTERNS   │  │ - Industry-specific │    │
│  │ - Detect depth  │  │                  │  │                     │    │
│  └────────┬────────┘  └────────┬─────────┘  └──────────┬──────────┘    │
│           │                    │                        │               │
│           └────────────────────┼────────────────────────┘               │
│                                │                                        │
│                    ┌───────────▼───────────┐                           │
│                    │    EpicGenerator      │                           │
│                    │                       │                           │
│                    │ - Group folders       │                           │
│                    │ - Create hierarchy    │                           │
│                    │ - Generate features   │                           │
│                    └───────────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### 1. Standard Source Folder Detection

Scan common source code locations automatically:

```python
# Standard source folders (industry-agnostic)
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

# Infrastructure folders (always create infrastructure epics)
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
```

### 2. Module Type Detection (from BrownPaperService)

Reuse existing patterns:

```python
# From brown_paper_service.py - MODULE_TYPE_PATTERNS
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
```

### 3. Architecture Pattern Detection (from BrownPaperService)

```python
# From brown_paper_service.py - ARCHITECTURE_PATTERNS
ARCHITECTURE_PATTERNS = {
    "ddd": ["domain", "aggregate", "value_object", "repository", "entity"],
    "mvc": ["model", "view", "controller"],
    "layered": ["presentation", "application", "domain", "infrastructure"],
    "microservices": ["service", "gateway", "discovery", "config"],
    "cqrs": ["command", "query", "handler", "event"],
    "hexagonal": ["port", "adapter", "application", "domain"],
}
```

### 4. Generic Epic Searcher Class

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
import re


class EpicGenerationStrategy(Enum):
    """How to generate epics from folder structure."""
    FOLDER_BASED = "folder"         # 1 epic per top-level folder
    GROUPED = "grouped"             # Group related folders into epics
    LAYER_BASED = "layer"           # Group by architectural layer
    HYBRID = "hybrid"               # Combine folder + grouping


@dataclass
class EpicSearchConfig:
    """Configuration for epic detection."""
    # Required
    project_path: str

    # Optional: Industry vocabulary (can be None for generic detection)
    domain_vocabulary: Optional["DomainVocabulary"] = None

    # Strategy
    strategy: EpicGenerationStrategy = EpicGenerationStrategy.FOLDER_BASED

    # Folder scanning options
    source_folders: List[str] = field(default_factory=lambda: STANDARD_SOURCE_FOLDERS)
    infrastructure_folders: List[str] = field(default_factory=lambda: INFRASTRUCTURE_FOLDERS)
    max_depth: int = 2  # How deep to scan for sub-epics
    min_files_for_epic: int = 3  # Minimum files to create an epic

    # Grouping options (for GROUPED/HYBRID strategies)
    grouping_rules: Dict[str, List[str]] = field(default_factory=dict)

    # Output options
    include_infrastructure_epic: bool = True
    include_test_epic: bool = False


@dataclass
class DetectedFolder:
    """A folder detected as potential epic source."""
    name: str
    path: str
    depth: int
    file_count: int
    module_type: Optional[str] = None
    subfolders: List["DetectedFolder"] = field(default_factory=list)


@dataclass
class DetectedEpic:
    """An epic detected from folder analysis."""
    id: str
    name: str
    description: str
    source_folders: List[str]
    features: List["DetectedFeature"] = field(default_factory=list)
    file_count: int = 0
    category: str = "business"  # business, infrastructure, integration, test
    confidence: float = 1.0


@dataclass
class DetectedFeature:
    """A feature detected within an epic."""
    id: str
    name: str
    description: str
    source_folder: str
    epic_id: str
    estimated_stories: int = 0


class GenericEpicSearcher:
    """
    Industry-agnostic epic searcher that works for any project.

    Detection Strategy:
    1. Find standard source folders (src, app, WEB, lib, etc.)
    2. Scan top-level subfolders as epic candidates
    3. Apply optional grouping rules
    4. Create infrastructure epic from common folders
    5. Generate features from subfolders
    """

    def __init__(self, config: EpicSearchConfig):
        self.config = config
        self._detected_folders: List[DetectedFolder] = []
        self._epics: List[DetectedEpic] = []

    def search(self) -> List[DetectedEpic]:
        """
        Execute the epic search.

        Returns:
            List of detected epics with features
        """
        # Step 1: Find source root(s)
        source_roots = self._find_source_roots()

        # Step 2: Scan folders at each root
        for root in source_roots:
            folders = self._scan_folder(root, depth=0)
            self._detected_folders.extend(folders)

        # Step 3: Apply strategy to create epics
        if self.config.strategy == EpicGenerationStrategy.FOLDER_BASED:
            self._epics = self._create_folder_based_epics()
        elif self.config.strategy == EpicGenerationStrategy.GROUPED:
            self._epics = self._create_grouped_epics()
        elif self.config.strategy == EpicGenerationStrategy.LAYER_BASED:
            self._epics = self._create_layer_based_epics()
        else:  # HYBRID
            self._epics = self._create_hybrid_epics()

        # Step 4: Add infrastructure epic if configured
        if self.config.include_infrastructure_epic:
            self._add_infrastructure_epic()

        # Step 5: Generate features for each epic
        for epic in self._epics:
            self._generate_features(epic)

        return self._epics

    def _find_source_roots(self) -> List[Path]:
        """Find all standard source folders in the project."""
        project_path = Path(self.config.project_path)
        roots = []

        for folder_name in self.config.source_folders:
            # Check direct child
            candidate = project_path / folder_name
            if candidate.is_dir():
                roots.append(candidate)

            # Check one level deep (e.g., project/src/main)
            for child in project_path.iterdir():
                if child.is_dir():
                    nested = child / folder_name
                    if nested.is_dir():
                        roots.append(nested)

        # If no standard folders found, use project root
        if not roots:
            roots = [project_path]

        return roots

    def _scan_folder(self, folder: Path, depth: int) -> List[DetectedFolder]:
        """Recursively scan a folder for epic candidates."""
        if depth > self.config.max_depth:
            return []

        results = []

        for item in folder.iterdir():
            if not item.is_dir():
                continue

            # Skip hidden folders and common non-code folders
            if item.name.startswith('.') or item.name in ['node_modules', 'bin', 'obj', '__pycache__', 'venv']:
                continue

            # Count files in this folder
            file_count = sum(1 for f in item.rglob('*') if f.is_file() and not f.name.startswith('.'))

            # Skip folders with too few files
            if file_count < self.config.min_files_for_epic and depth == 0:
                continue

            # Detect module type
            module_type = self._detect_module_type(item)

            # Create folder entry
            detected = DetectedFolder(
                name=item.name,
                path=str(item),
                depth=depth,
                file_count=file_count,
                module_type=module_type,
            )

            # Scan subfolders
            if depth < self.config.max_depth:
                detected.subfolders = self._scan_folder(item, depth + 1)

            results.append(detected)

        return results

    def _detect_module_type(self, folder: Path) -> Optional[str]:
        """Detect the module type based on patterns."""
        folder_name = folder.name.lower()

        for module_type, patterns in MODULE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, folder_name, re.IGNORECASE):
                    return module_type

        return None

    def _create_folder_based_epics(self) -> List[DetectedEpic]:
        """Create one epic per top-level folder."""
        epics = []
        epic_counter = 1

        for folder in self._detected_folders:
            if folder.depth > 0:
                continue

            # Determine category
            category = "business"
            if folder.name.lower() in [f.lower() for f in self.config.infrastructure_folders]:
                category = "infrastructure"

            epic = DetectedEpic(
                id=f"EPIC-{epic_counter:03d}",
                name=self._humanize_folder_name(folder.name),
                description=f"Functionality related to {folder.name}",
                source_folders=[folder.path],
                file_count=folder.file_count,
                category=category,
            )
            epics.append(epic)
            epic_counter += 1

        return epics

    def _create_grouped_epics(self) -> List[DetectedEpic]:
        """Group related folders into epics using grouping rules."""
        epics = []
        epic_counter = 1
        grouped_folders: Set[str] = set()

        # Apply grouping rules
        for group_name, folder_patterns in self.config.grouping_rules.items():
            matched_folders = []

            for folder in self._detected_folders:
                if folder.depth > 0:
                    continue

                for pattern in folder_patterns:
                    if re.search(pattern, folder.name, re.IGNORECASE):
                        matched_folders.append(folder)
                        grouped_folders.add(folder.path)
                        break

            if matched_folders:
                epic = DetectedEpic(
                    id=f"EPIC-{epic_counter:03d}",
                    name=group_name,
                    description=f"Grouped functionality: {', '.join(f.name for f in matched_folders)}",
                    source_folders=[f.path for f in matched_folders],
                    file_count=sum(f.file_count for f in matched_folders),
                    category="business",
                )
                epics.append(epic)
                epic_counter += 1

        # Create individual epics for ungrouped folders
        for folder in self._detected_folders:
            if folder.depth > 0 or folder.path in grouped_folders:
                continue

            epic = DetectedEpic(
                id=f"EPIC-{epic_counter:03d}",
                name=self._humanize_folder_name(folder.name),
                description=f"Functionality related to {folder.name}",
                source_folders=[folder.path],
                file_count=folder.file_count,
                category="business",
            )
            epics.append(epic)
            epic_counter += 1

        return epics

    def _create_layer_based_epics(self) -> List[DetectedEpic]:
        """Group folders by architectural layer."""
        layers = {
            "Presentation": [],
            "Application": [],
            "Domain": [],
            "Infrastructure": [],
            "Other": [],
        }

        for folder in self._detected_folders:
            if folder.depth > 0:
                continue

            # Determine layer based on module type and name
            layer = self._determine_layer(folder)
            layers[layer].append(folder)

        epics = []
        epic_counter = 1

        for layer_name, folders in layers.items():
            if not folders:
                continue

            epic = DetectedEpic(
                id=f"EPIC-{epic_counter:03d}",
                name=f"{layer_name} Layer",
                description=f"All {layer_name.lower()} layer components",
                source_folders=[f.path for f in folders],
                file_count=sum(f.file_count for f in folders),
                category="infrastructure" if layer_name == "Infrastructure" else "business",
            )
            epics.append(epic)
            epic_counter += 1

        return epics

    def _create_hybrid_epics(self) -> List[DetectedEpic]:
        """Combine folder-based and grouped strategies."""
        # Start with grouped epics
        epics = self._create_grouped_epics()

        # Apply vocabulary-based grouping if available
        if self.config.domain_vocabulary:
            epics = self._apply_vocabulary_grouping(epics)

        return epics

    def _determine_layer(self, folder: DetectedFolder) -> str:
        """Determine which architectural layer a folder belongs to."""
        name_lower = folder.name.lower()

        # Check module type first
        if folder.module_type:
            if folder.module_type in ["controller", "form"]:
                return "Presentation"
            elif folder.module_type in ["service"]:
                return "Application"
            elif folder.module_type in ["model", "repository"]:
                return "Domain"
            elif folder.module_type in ["config", "migration", "util"]:
                return "Infrastructure"

        # Check folder name patterns
        for pattern in ARCHITECTURE_PATTERNS.get("layered", []):
            if pattern in name_lower:
                if pattern == "presentation":
                    return "Presentation"
                elif pattern == "application":
                    return "Application"
                elif pattern == "domain":
                    return "Domain"
                elif pattern == "infrastructure":
                    return "Infrastructure"

        return "Other"

    def _add_infrastructure_epic(self) -> None:
        """Add an infrastructure epic for common folders."""
        infra_folders = []

        for folder in self._detected_folders:
            if folder.depth > 0:
                continue

            if folder.name.lower() in [f.lower() for f in self.config.infrastructure_folders]:
                # Check if not already in an epic
                already_assigned = any(
                    folder.path in epic.source_folders
                    for epic in self._epics
                )
                if not already_assigned:
                    infra_folders.append(folder)

        if infra_folders:
            epic = DetectedEpic(
                id=f"EPIC-{len(self._epics) + 1:03d}",
                name="Infrastructure & Shared",
                description="Infrastructure, utilities, and shared components",
                source_folders=[f.path for f in infra_folders],
                file_count=sum(f.file_count for f in infra_folders),
                category="infrastructure",
            )
            self._epics.append(epic)

    def _generate_features(self, epic: DetectedEpic) -> None:
        """Generate features for an epic from its subfolders."""
        feature_counter = 1

        for folder_path in epic.source_folders:
            folder = next((f for f in self._detected_folders if f.path == folder_path), None)
            if not folder:
                continue

            for subfolder in folder.subfolders:
                feature = DetectedFeature(
                    id=f"{epic.id}-FEAT-{feature_counter:03d}",
                    name=self._humanize_folder_name(subfolder.name),
                    description=f"{subfolder.name} functionality",
                    source_folder=subfolder.path,
                    epic_id=epic.id,
                    estimated_stories=max(1, subfolder.file_count // 5),
                )
                epic.features.append(feature)
                feature_counter += 1

    def _humanize_folder_name(self, name: str) -> str:
        """Convert folder name to human-readable epic name."""
        # Handle CamelCase
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        # Handle snake_case
        result = result.replace('_', ' ')
        # Handle kebab-case
        result = result.replace('-', ' ')
        # Capitalize words
        return ' '.join(word.capitalize() for word in result.split())

    def _apply_vocabulary_grouping(self, epics: List[DetectedEpic]) -> List[DetectedEpic]:
        """Apply domain vocabulary to group epics (optional)."""
        if not self.config.domain_vocabulary:
            return epics

        # This is where industry-specific vocabularies can be applied
        # But it's OPTIONAL - the searcher works without it
        # Implementation depends on DomainVocabulary interface
        return epics
```

---

## Integration with Existing Services

### 1. BrownPaperService Integration

```python
# In BrownPaperService.analyze_code_structure()
def analyze_code_structure(self, app: Application) -> BrownPaperAnalysis:
    # Use GenericEpicSearcher for epic detection
    config = EpicSearchConfig(
        project_path=app.root_path,
        strategy=EpicGenerationStrategy.FOLDER_BASED,
    )
    searcher = GenericEpicSearcher(config)
    detected_epics = searcher.search()

    # Convert to BrownPaper format
    for epic in detected_epics:
        self._add_epic_to_analysis(epic)
```

### 2. IntakeToBacklogService Integration

```python
# In IntakeToBacklogService._extract_domains()
def _extract_domains(self, report: IntakeReport) -> List[ExtractedDomain]:
    # Use folder structure from report
    if report.architecture and report.architecture.detected_layers:
        config = EpicSearchConfig(
            project_path=report.project_path,
            strategy=EpicGenerationStrategy.HYBRID,
            # Optional: Add industry vocabulary if configured
            domain_vocabulary=self._get_project_vocabulary(report),
        )
        searcher = GenericEpicSearcher(config)
        detected_epics = searcher.search()

        return self._convert_epics_to_domains(detected_epics)
```

### 3. DomainVocabulary Integration (Optional)

```python
# Only used when industry-specific grouping is desired
# NOT required for basic epic detection

# Example: Healthcare project configuration
healthcare_config = EpicSearchConfig(
    project_path="/path/to/project",
    strategy=EpicGenerationStrategy.GROUPED,
    domain_vocabulary=DomainVocabularyLoader().get_vocabulary("healthcare"),
    grouping_rules={
        "Patient Management": ["patient", "dossier", "client"],
        "Scheduling": ["appointment", "calendar", "schedule"],
        "Billing": ["invoice", "payment", "claim"],
    }
)

# Example: Generic project (no vocabulary)
generic_config = EpicSearchConfig(
    project_path="/path/to/project",
    strategy=EpicGenerationStrategy.FOLDER_BASED,
    # No domain_vocabulary - uses folder names directly
)
```

---

## Journey-Based Epic Detection

### Concept

User journeys als **primaire bron** voor epic detectie - veel gebruikersgerichter dan alleen folder structuur.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Combined Epic Detection Strategy                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │   JOURNEY-BASED (Primary)       │  │   FOLDER-BASED (Secondary)      │  │
│  │                                 │  │                                 │  │
│  │   User perspective:             │  │   Code perspective:             │  │
│  │   - What can users DO?          │  │   - What code exists?           │  │
│  │   - Which screens visited?      │  │   - Which folders?              │  │
│  │   - What messages shown?        │  │   - Infrastructure code?        │  │
│  │                                 │  │                                 │  │
│  │   Output:                       │  │   Output:                       │  │
│  │   - Business Epics              │  │   - Infrastructure Epics        │  │
│  │   - User Workflows              │  │   - Uncovered Code              │  │
│  └────────────────┬────────────────┘  └────────────────┬────────────────┘  │
│                   │                                    │                    │
│                   └──────────────┬─────────────────────┘                    │
│                                  ▼                                          │
│                    ┌─────────────────────────┐                              │
│                    │   MERGED EPIC LIST      │                              │
│                    │                         │                              │
│                    │   Business Epics        │  ← from journeys             │
│                    │   + Infrastructure      │  ← from folders              │
│                    │   + Uncovered modules   │  ← folders not in journeys   │
│                    └─────────────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JourneyBasedEpicSearcher

```python
@dataclass
class DetectedScreen:
    """A screen/page detected in the application."""
    id: str
    name: str
    file_path: str
    screen_type: str  # menu, form, list, detail, edit, dashboard

    # Navigation
    entry_points: List[str]   # Waar kom je vandaan?
    exit_points: List[str]    # Waar kun je naartoe?

    # Interactions
    forms: List[str]          # Formulieren op dit scherm
    buttons: List[str]        # Knoppen/acties
    messages: List[str]       # Meldingen/validaties/alerts

    # Context
    data_entities: List[str]  # Welke data wordt getoond/bewerkt?
    required_role: Optional[str]


@dataclass
class DetectedJourney:
    """A user journey through the application."""
    id: str
    name: str
    description: str

    # Journey path
    start_screen: str
    screen_path: List[str]    # Schermen in volgorde
    end_screens: List[str]    # Mogelijke eindpunten

    # User context
    persona: str
    goal: str

    # Interactions discovered
    available_actions: List[str]   # Alle knoppen/acties in journey
    possible_messages: List[str]   # Alle meldingen die kunnen verschijnen
    validations: List[str]         # Validatieregels

    # Outcomes
    success_outcomes: List[str]
    error_outcomes: List[str]


class JourneyBasedEpicSearcher:
    """
    Epic detection based on user journeys through the application.

    Strategy:
    1. Scan all screens (ASPX, VB Forms, Razor, etc.)
    2. Build navigation graph (screen → screen)
    3. Find entry points (menus, start pages)
    4. Trace all possible paths through the application
    5. Extract actions and messages at each screen
    6. Group related journeys into epics
    """

    # Screen file patterns per technology
    SCREEN_PATTERNS = {
        'aspx': ['*.aspx', '*.ascx'],           # ASP.NET WebForms
        'asp': ['*.asp'],                        # Classic ASP
        'vb': ['*Form.vb', '*Page.vb'],         # VB.NET Forms
        'razor': ['*.cshtml', '*.razor'],        # ASP.NET MVC/Blazor
        'jsx': ['*.jsx', '*.tsx'],               # React
        'vue': ['*.vue'],                        # Vue.js
        'html': ['*.html', '*.htm'],             # Static HTML
    }

    # Navigation patterns to extract
    NAVIGATION_PATTERNS = {
        'aspnet': [
            r'Response\.Redirect\s*\(\s*"([^"]+)"',
            r'Server\.Transfer\s*\(\s*"([^"]+)"',
            r'NavigateUrl\s*=\s*"([^"]+)"',
            r'PostBackUrl\s*=\s*"([^"]+)"',
            r'href\s*=\s*"([^"]+\.aspx[^"]*)"',
        ],
        'javascript': [
            r'window\.location\s*=\s*["\']([^"\']+)',
            r'location\.href\s*=\s*["\']([^"\']+)',
            r'navigate\s*\(\s*["\']([^"\']+)',
            r'router\.push\s*\(\s*["\']([^"\']+)',
        ],
        'vbnet': [
            r'Me\.Navigate\s*\(\s*"([^"]+)"',
            r'Process\.Start\s*\(\s*"([^"]+)"',
        ],
    }

    # Button/action patterns
    BUTTON_PATTERNS = [
        r'<asp:Button[^>]+Text\s*=\s*"([^"]+)"',
        r'<asp:LinkButton[^>]+Text\s*=\s*"([^"]+)"',
        r'<asp:ImageButton[^>]+AlternateText\s*=\s*"([^"]+)"',
        r'<input[^>]+value\s*=\s*"([^"]+)"[^>]+type\s*=\s*"submit"',
        r'<button[^>]*>([^<]+)</button>',
        r'CommandName\s*=\s*"([^"]+)"',
        r'OnClick\s*=\s*"btn([^"]+)_Click"',
        r'\.Click\s*\+=.*Sub\s+(\w+)',  # VB.NET event handlers
    ]

    # Message/alert patterns
    MESSAGE_PATTERNS = [
        r'MsgBox\s*\(\s*"([^"]+)"',
        r'MessageBox\.Show\s*\(\s*"([^"]+)"',
        r'alert\s*\(\s*["\']([^"\']+)',
        r'lblError\.Text\s*=\s*"([^"]+)"',
        r'lblMessage\.Text\s*=\s*"([^"]+)"',
        r'litMessage\.Text\s*=\s*"([^"]+)"',
        r'ValidationMessage\s*=\s*"([^"]+)"',
        r'ErrorMessage\s*=\s*"([^"]+)"',
        r'ToolTip\s*=\s*"([^"]+)"',
        r'toast\s*\(\s*["\']([^"\']+)',
        r'notify\s*\(\s*["\']([^"\']+)',
    ]

    def __init__(self, config: "JourneySearchConfig"):
        self.config = config
        self.screens: Dict[str, DetectedScreen] = {}
        self.navigation_graph: Dict[str, Set[str]] = {}
        self.journeys: List[DetectedJourney] = []

    def search(self) -> List[DetectedJourney]:
        """Execute journey detection."""
        # Step 1: Scan all screen files
        self._scan_all_screens()

        # Step 2: Build navigation graph
        self._build_navigation_graph()

        # Step 3: Find entry points
        entry_points = self._find_entry_points()

        # Step 4: Trace journeys from each entry point
        for entry in entry_points:
            paths = self._trace_all_paths(entry, max_depth=self.config.max_journey_depth)
            for path in paths:
                journey = self._create_journey_from_path(path)
                if journey:
                    self.journeys.append(journey)

        # Step 5: Deduplicate and merge similar journeys
        self.journeys = self._merge_similar_journeys(self.journeys)

        return self.journeys

    def _scan_all_screens(self):
        """Scan project for all screen files."""
        project_path = Path(self.config.project_path)

        for tech, patterns in self.SCREEN_PATTERNS.items():
            for pattern in patterns:
                for file_path in project_path.rglob(pattern):
                    # Skip generated/test folders
                    if self._should_skip(file_path):
                        continue

                    screen = self._parse_screen(file_path)
                    if screen:
                        self.screens[screen.id] = screen

    def _parse_screen(self, file_path: Path) -> Optional[DetectedScreen]:
        """Parse a screen file to extract navigation and interactions."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

        screen_id = file_path.stem

        return DetectedScreen(
            id=screen_id,
            name=self._humanize_name(screen_id),
            file_path=str(file_path),
            screen_type=self._detect_screen_type(file_path, content),
            entry_points=[],
            exit_points=self._extract_navigation_targets(content),
            forms=self._extract_forms(content),
            buttons=self._extract_buttons(content),
            messages=self._extract_messages(content),
            data_entities=self._extract_entities(content),
            required_role=self._extract_required_role(content),
        )

    def _extract_navigation_targets(self, content: str) -> List[str]:
        """Extract all navigation targets from screen content."""
        targets = set()

        for patterns in self.NAVIGATION_PATTERNS.values():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Normalize to screen ID
                    target_id = Path(match).stem
                    if target_id and not target_id.startswith(('#', 'javascript', 'http')):
                        targets.add(target_id)

        return list(targets)

    def _extract_buttons(self, content: str) -> List[str]:
        """Extract button/action names from screen."""
        buttons = set()

        for pattern in self.BUTTON_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            buttons.update(matches)

        return [b for b in buttons if len(b) > 1 and len(b) < 50]

    def _extract_messages(self, content: str) -> List[str]:
        """Extract all possible messages from screen."""
        messages = set()

        for pattern in self.MESSAGE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            messages.update(matches)

        return [m for m in messages if len(m) > 3 and len(m) < 200]

    def _detect_screen_type(self, file_path: Path, content: str) -> str:
        """Detect the type of screen."""
        name_lower = file_path.stem.lower()
        content_lower = content.lower()

        # Check name patterns
        if any(kw in name_lower for kw in ['menu', 'nav', 'home', 'index', 'default', 'main']):
            return 'menu'
        if any(kw in name_lower for kw in ['dashboard', 'overview', 'start']):
            return 'dashboard'
        if any(kw in name_lower for kw in ['list', 'overzicht', 'search', 'zoek']):
            return 'list'
        if any(kw in name_lower for kw in ['detail', 'view', 'bekijk', 'show']):
            return 'detail'
        if any(kw in name_lower for kw in ['edit', 'bewerk', 'wijzig', 'update']):
            return 'edit'
        if any(kw in name_lower for kw in ['new', 'nieuw', 'add', 'create', 'toevoeg']):
            return 'create'
        if any(kw in name_lower for kw in ['login', 'logon', 'signin', 'auth']):
            return 'login'
        if any(kw in name_lower for kw in ['report', 'rapport', 'print', 'export']):
            return 'report'

        # Check content patterns
        if '<asp:GridView' in content or '<asp:Repeater' in content:
            return 'list'
        if '<asp:FormView' in content or '<asp:DetailsView' in content:
            return 'detail'

        return 'form'

    def _find_entry_points(self) -> List[str]:
        """Find application entry points."""
        entry_points = []

        for screen_id, screen in self.screens.items():
            # Screens with no incoming navigation
            if not screen.entry_points:
                entry_points.append(screen_id)

            # Menu/dashboard screens are always entry points
            if screen.screen_type in ['menu', 'dashboard', 'login']:
                if screen_id not in entry_points:
                    entry_points.append(screen_id)

            # Common entry point names
            if any(kw in screen_id.lower() for kw in ['default', 'index', 'home', 'main', 'menu']):
                if screen_id not in entry_points:
                    entry_points.append(screen_id)

        return entry_points

    def _build_navigation_graph(self):
        """Build bidirectional navigation graph."""
        for screen_id, screen in self.screens.items():
            if screen_id not in self.navigation_graph:
                self.navigation_graph[screen_id] = set()

            for target in screen.exit_points:
                # Add forward link
                self.navigation_graph[screen_id].add(target)

                # Add reverse link (entry point)
                if target in self.screens:
                    self.screens[target].entry_points.append(screen_id)

    def _trace_all_paths(
        self,
        start: str,
        max_depth: int = 6
    ) -> List[List[str]]:
        """Trace all possible paths from a start screen."""
        paths = []

        def trace(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current in path:  # Cycle detection
                return

            path = path + [current]
            next_screens = self.navigation_graph.get(current, set())

            if not next_screens or depth == max_depth:
                # End of path
                if len(path) >= 2:
                    paths.append(path)
            else:
                for next_screen in next_screens:
                    trace(next_screen, path, depth + 1)

        trace(start, [], 0)
        return paths

    def _create_journey_from_path(self, path: List[str]) -> Optional[DetectedJourney]:
        """Create a journey from a screen path."""
        if len(path) < 2:
            return None

        screens_in_path = [self.screens[s] for s in path if s in self.screens]
        if len(screens_in_path) < 2:
            return None

        # Collect all interactions from the journey
        all_actions = []
        all_messages = []
        all_validations = []

        for screen in screens_in_path:
            all_actions.extend(screen.buttons)
            all_messages.extend(screen.messages)

        # Determine journey name from main screen (usually second in path)
        main_screen = screens_in_path[1] if len(screens_in_path) > 1 else screens_in_path[0]

        # Determine goal based on screen types
        goal = self._infer_journey_goal(screens_in_path)

        return DetectedJourney(
            id=f"JOURNEY-{len(self.journeys) + 1:03d}",
            name=f"{main_screen.name}",
            description=f"Journey: {' → '.join(s.name for s in screens_in_path)}",
            start_screen=path[0],
            screen_path=path,
            end_screens=[path[-1]],
            persona="User",
            goal=goal,
            available_actions=list(set(all_actions)),
            possible_messages=list(set(all_messages)),
            validations=list(set(all_validations)),
            success_outcomes=[f"{main_screen.name} completed"],
            error_outcomes=[m for m in all_messages if any(kw in m.lower() for kw in ['error', 'fout', 'mislukt', 'invalid'])],
        )

    def _infer_journey_goal(self, screens: List[DetectedScreen]) -> str:
        """Infer the user's goal from screen types."""
        screen_types = [s.screen_type for s in screens]

        if 'create' in screen_types:
            return "Create new record"
        if 'edit' in screen_types:
            return "Edit existing record"
        if 'detail' in screen_types and 'list' in screen_types:
            return "View record details"
        if 'report' in screen_types:
            return "Generate report"
        if 'list' in screen_types:
            return "Browse and search records"

        return "Complete workflow"

    def _merge_similar_journeys(self, journeys: List[DetectedJourney]) -> List[DetectedJourney]:
        """Merge journeys that share the same main screen."""
        merged: Dict[str, DetectedJourney] = {}

        for journey in journeys:
            # Use first non-menu screen as key
            key = journey.screen_path[1] if len(journey.screen_path) > 1 else journey.screen_path[0]

            if key not in merged:
                merged[key] = journey
            else:
                # Merge actions and messages
                existing = merged[key]
                existing.available_actions = list(set(existing.available_actions + journey.available_actions))
                existing.possible_messages = list(set(existing.possible_messages + journey.possible_messages))
                existing.end_screens = list(set(existing.end_screens + journey.end_screens))

        return list(merged.values())

    def _humanize_name(self, name: str) -> str:
        """Convert screen ID to readable name."""
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        result = result.replace('_', ' ').replace('-', ' ')
        return ' '.join(word.capitalize() for word in result.split())

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ['node_modules', 'bin', 'obj', 'test', 'backup', '.git']
        return any(p in str(file_path).lower() for p in skip_patterns)
```

### CombinedEpicSearcher

```python
@dataclass
class CombinedSearchConfig:
    """Configuration for combined epic detection."""
    project_path: str

    # Journey detection settings
    max_journey_depth: int = 6
    min_screens_per_journey: int = 2

    # Folder detection settings (for infrastructure)
    source_folders: List[str] = field(default_factory=lambda: STANDARD_SOURCE_FOLDERS)
    infrastructure_folders: List[str] = field(default_factory=lambda: INFRASTRUCTURE_FOLDERS)

    # Output settings
    include_infrastructure: bool = True
    include_uncovered_folders: bool = True
    min_confidence: float = 0.5


class CombinedEpicSearcher:
    """
    Combined journey-based and folder-based epic detection.

    Strategy:
    1. Journey-based: Primary source for BUSINESS epics
       - Traces user paths through the application
       - Extracts actions, messages, validations
       - Groups related journeys into epics

    2. Folder-based: Secondary source for INFRASTRUCTURE epics
       - Catches code not reachable via UI (APIs, libraries, utils)
       - Detects infrastructure patterns
       - Fills gaps from journey detection
    """

    def __init__(self, config: CombinedSearchConfig):
        self.config = config

    def search(self) -> List[DetectedEpic]:
        """Execute combined epic detection."""

        # =====================================================================
        # PHASE 1: Journey-based detection (Business Epics)
        # =====================================================================
        journey_config = JourneySearchConfig(
            project_path=self.config.project_path,
            max_journey_depth=self.config.max_journey_depth,
        )
        journey_searcher = JourneyBasedEpicSearcher(journey_config)
        journeys = journey_searcher.search()

        # Convert journeys to epics
        business_epics = self._journeys_to_epics(journeys, journey_searcher.screens)

        # Track which files are covered by journeys
        covered_files = set()
        for epic in business_epics:
            covered_files.update(epic.source_folders)

        # =====================================================================
        # PHASE 2: Folder-based detection (Infrastructure + Gaps)
        # =====================================================================
        folder_config = EpicSearchConfig(
            project_path=self.config.project_path,
            source_folders=self.config.source_folders,
            infrastructure_folders=self.config.infrastructure_folders,
        )
        folder_searcher = GenericEpicSearcher(folder_config)
        folder_epics = folder_searcher.search()

        # =====================================================================
        # PHASE 3: Merge results
        # =====================================================================
        final_epics = business_epics.copy()

        for epic in folder_epics:
            # Always include infrastructure
            if epic.category == "infrastructure":
                if self.config.include_infrastructure:
                    final_epics.append(epic)

            # Include business folders not covered by journeys
            elif self.config.include_uncovered_folders:
                uncovered = [f for f in epic.source_folders if f not in covered_files]
                if uncovered:
                    epic.source_folders = uncovered
                    epic.name = f"{epic.name} (Additional)"
                    epic.confidence = 0.6  # Lower confidence for uncovered
                    final_epics.append(epic)

        return final_epics

    def _journeys_to_epics(
        self,
        journeys: List[DetectedJourney],
        screens: Dict[str, DetectedScreen]
    ) -> List[DetectedEpic]:
        """Convert journeys to epics by grouping."""

        # Group journeys by domain (main screen)
        domain_journeys: Dict[str, List[DetectedJourney]] = {}

        for journey in journeys:
            # Extract domain from main screen
            if len(journey.screen_path) > 1:
                main_screen_id = journey.screen_path[1]
            else:
                main_screen_id = journey.screen_path[0]

            domain = self._extract_domain(main_screen_id)

            if domain not in domain_journeys:
                domain_journeys[domain] = []
            domain_journeys[domain].append(journey)

        # Create epics from journey groups
        epics = []
        for domain, domain_j in domain_journeys.items():
            epic = self._create_epic_from_journeys(domain, domain_j, screens)
            epics.append(epic)

        return epics

    def _create_epic_from_journeys(
        self,
        domain: str,
        journeys: List[DetectedJourney],
        screens: Dict[str, DetectedScreen]
    ) -> DetectedEpic:
        """Create an epic from related journeys."""

        # Collect all screens, actions, messages
        all_files = set()
        all_actions = set()
        all_messages = set()

        for journey in journeys:
            for screen_id in journey.screen_path:
                if screen_id in screens:
                    all_files.add(screens[screen_id].file_path)
            all_actions.update(journey.available_actions)
            all_messages.update(journey.possible_messages)

        # Create features from journeys
        features = []
        for journey in journeys[:10]:  # Max 10 features
            feature = DetectedFeature(
                id=f"{domain}-FEAT-{len(features)+1:03d}",
                name=journey.name,
                description=f"Journey: {journey.goal}",
                source_folder=screens[journey.screen_path[0]].file_path if journey.screen_path else "",
                epic_id="",
                estimated_stories=len(journey.available_actions),
            )
            features.append(feature)

        return DetectedEpic(
            id=f"EPIC-{domain[:3].upper()}-001",
            name=domain,
            description=f"All {domain} functionality ({len(journeys)} user journeys)",
            source_folders=list(all_files),
            features=features,
            file_count=len(all_files),
            category="business",
            confidence=0.9,
            metadata={
                "journey_count": len(journeys),
                "actions": list(all_actions)[:20],
                "messages": list(all_messages)[:20],
            }
        )

    def _extract_domain(self, screen_id: str) -> str:
        """Extract domain name from screen ID."""
        # Remove common prefixes/suffixes
        name = screen_id
        for suffix in ['List', 'Detail', 'Edit', 'New', 'Overview', 'Form', 'Page']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        for prefix in ['frm', 'pg', 'uc', 'ctrl']:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]

        # Humanize
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        return result.strip()
```

### Output Example

```
═══════════════════════════════════════════════════════════════════════════════
                         COMBINED EPIC DETECTION RESULTS
═══════════════════════════════════════════════════════════════════════════════

BUSINESS EPICS (from User Journeys)
───────────────────────────────────────────────────────────────────────────────

EPIC: Dossier
├── Source: 12 screens, 8 journeys
├── Actions: [Zoeken, Openen, Bewerken, Opslaan, Verwijderen, Afdrukken]
├── Messages: ["Dossier opgeslagen", "Verplichte velden", "Wilt u verwijderen?"]
│
├── Feature: Dossier Overzicht
│   └── Journey: Menu → DossierList → DossierDetail
│   └── Actions: [Zoeken, Filteren, Sorteren]
│
├── Feature: Dossier Bewerken
│   └── Journey: DossierDetail → DossierEdit → DossierDetail
│   └── Actions: [Bewerken, Opslaan, Annuleren]
│
└── Feature: Nieuw Dossier
    └── Journey: Menu → DossierNieuw → DossierDetail
    └── Actions: [Aanmaken, Valideren, Opslaan]

EPIC: Afspraken
├── Source: 8 screens, 5 journeys
├── Actions: [Inplannen, Verzetten, Annuleren, Bevestigen]
├── Messages: ["Tijdslot bezet", "Afspraak bevestigd", "Patient geïnformeerd"]
│
├── Feature: Agenda Bekijken
├── Feature: Afspraak Inplannen
└── Feature: Afspraak Wijzigen

EPIC: Beheer
├── Source: 15 screens, 6 journeys
├── Actions: [Toevoegen, Wijzigen, Verwijderen, Importeren, Exporteren]
└── ...

───────────────────────────────────────────────────────────────────────────────
INFRASTRUCTURE EPICS (from Folder Structure)
───────────────────────────────────────────────────────────────────────────────

EPIC: CRS Libraries
├── Source: /src/CRSLibrary, /src/CRSBusiness
├── Category: infrastructure
└── Features: [Business Logic, Utilities, Extensions]

EPIC: API Layer
├── Source: /src/HCI_EPD_API
├── Category: infrastructure
└── Features: [Controllers, Services, Models]

EPIC: Database
├── Source: /src/DatabaseScripts
├── Category: infrastructure
└── Features: [Migrations, Stored Procedures, Views]

───────────────────────────────────────────────────────────────────────────────
SUMMARY
───────────────────────────────────────────────────────────────────────────────
Total Epics:     18 (12 business + 6 infrastructure)
Total Features:  67
Total Journeys:  45
Total Actions:   234 unique actions discovered
Total Messages:  89 unique messages discovered
Coverage:        94% of screens covered by journeys
```

---

## Phase Plan

### Fase 24.8.1: Screen Scanner & Parser (4 hours)

**Objective:** Create screen detection and parsing

**Tasks:**
1. Create `backend/app/services/journey_epic_searcher.py`
2. Implement `DetectedScreen` and `DetectedJourney` dataclasses
3. Implement multi-technology screen patterns (ASPX, VB, Razor, etc.)
4. Implement `_scan_all_screens()` - find all screen files
5. Implement `_parse_screen()` - extract navigation, buttons, messages
6. Add unit tests for screen parsing

**Output:**
```python
searcher = JourneyBasedEpicSearcher(config)
searcher._scan_all_screens()
# screens = {"DossierList": DetectedScreen(...), "DossierDetail": ...}
```

### Fase 24.8.2: Navigation Graph & Path Tracing (4 hours)

**Objective:** Build navigation graph and trace user paths

**Tasks:**
1. Implement `_build_navigation_graph()` - screen → screen links
2. Implement `_find_entry_points()` - detect menus, start pages
3. Implement `_trace_all_paths()` - recursive path finding with cycle detection
4. Implement `_create_journey_from_path()` - convert path to journey
5. Implement `_merge_similar_journeys()` - deduplicate
6. Add visualization/debug output for navigation graph

**Output:**
```python
# Navigation graph
graph = {
    "Menu": ["DossierList", "AfsprakenList", "Beheer"],
    "DossierList": ["DossierDetail", "DossierNieuw"],
    "DossierDetail": ["DossierEdit", "DossierList"],
}

# Traced journeys
journeys = [
    Journey("Dossier Bekijken", path=["Menu", "DossierList", "DossierDetail"]),
    Journey("Dossier Bewerken", path=["DossierDetail", "DossierEdit", "DossierDetail"]),
]
```

### Fase 24.8.3: Action & Message Extraction (3 hours)

**Objective:** Extract all user interactions from screens

**Tasks:**
1. Implement button/action extraction patterns (ASP.NET, VB.NET, JavaScript)
2. Implement message/alert extraction patterns
3. Implement validation rule extraction
4. Implement form detection
5. Link actions to screen types (CRUD operations)
6. Add tests for extraction patterns

**Output:**
```python
screen.buttons = ["Opslaan", "Annuleren", "Verwijderen"]
screen.messages = ["Dossier opgeslagen", "Verplichte velden ontbreken"]
screen.validations = ["BSN moet 9 cijfers zijn", "Geboortedatum verplicht"]
```

### Fase 24.8.4: Folder-Based Searcher (3 hours)

**Objective:** Create infrastructure/fallback folder detection

**Tasks:**
1. Create `backend/app/services/generic_epic_searcher.py`
2. Implement `STANDARD_SOURCE_FOLDERS` and `INFRASTRUCTURE_FOLDERS`
3. Implement `_find_source_roots()` and `_scan_folder()`
4. Implement folder-based epic generation
5. Add infrastructure detection (API, database, libraries)
6. Add tests

**Output:**
```python
folder_searcher = GenericEpicSearcher(config)
folder_epics = folder_searcher.search()
# [Epic("CRS Libraries"), Epic("API Layer"), Epic("Database")]
```

### Fase 24.8.5: Combined Searcher & Epic Generation (4 hours)

**Objective:** Merge journey-based and folder-based results

**Tasks:**
1. Create `CombinedEpicSearcher` class
2. Implement `_journeys_to_epics()` - group journeys by domain
3. Implement coverage tracking (which files are in journeys)
4. Implement merge logic (business + infrastructure + gaps)
5. Implement feature generation from journeys
6. Add confidence scoring

**Output:**
```python
combined = CombinedEpicSearcher(config)
epics = combined.search()
# Business epics from journeys + Infrastructure from folders
```

### Fase 24.8.6: Service Integration (3 hours)

**Objective:** Integrate with existing services

**Tasks:**
1. Integrate with `IntakeToBacklogService._extract_domains()`
2. Integrate with `BrownPaperService.analyze_code_structure()`
3. Update `_extract_user_journeys()` to use detected journeys
4. Make existing story/feature generation use journey data
5. Add integration tests with real project

**Output:**
```python
# IntakeToBacklogService now uses CombinedEpicSearcher
result = service.generate_backlog(report)
# Epics based on user journeys, not hardcoded keywords
```

### Fase 24.8.7: Testing & Documentation (3 hours)

**Objective:** Complete testing and documentation

**Tasks:**
1. End-to-end test with HCI-CRS project
2. Test with different project types (React, .NET Core, etc.)
3. Add docstrings to all classes/methods
4. Create example configurations
5. Update API documentation
6. Performance testing (large codebases)

---

## Test Criteria

### Unit Tests

```python
def test_screen_parsing():
    """Test screen file parsing extracts navigation and actions."""
    content = '''
    <asp:Button ID="btnSave" Text="Opslaan" OnClick="btnSave_Click" />
    <asp:Button ID="btnCancel" Text="Annuleren" PostBackUrl="List.aspx" />
    '''
    screen = searcher._parse_screen_content(content)

    assert "Opslaan" in screen.buttons
    assert "List" in screen.exit_points

def test_journey_tracing():
    """Test journey path tracing."""
    searcher.screens = {
        "Menu": DetectedScreen(exit_points=["List"]),
        "List": DetectedScreen(exit_points=["Detail"]),
        "Detail": DetectedScreen(exit_points=[]),
    }
    searcher._build_navigation_graph()

    paths = searcher._trace_all_paths("Menu", max_depth=5)
    assert ["Menu", "List", "Detail"] in paths

def test_combined_searcher():
    """Test combined journey + folder detection."""
    config = CombinedSearchConfig(project_path="/tmp/test")
    searcher = CombinedEpicSearcher(config)
    epics = searcher.search()

    # Should have both business and infrastructure epics
    categories = [e.category for e in epics]
    assert "business" in categories
    assert "infrastructure" in categories

def test_message_extraction():
    """Test message/alert extraction from code."""
    content = '''
    MsgBox("Dossier opgeslagen")
    lblError.Text = "Verplichte velden ontbreken"
    '''
    messages = searcher._extract_messages(content)

    assert "Dossier opgeslagen" in messages
    assert "Verplichte velden ontbreken" in messages
```

### Integration Tests

```python
async def test_real_project_detection():
    """Test with actual HCI-CRS project."""
    config = CombinedSearchConfig(
        project_path="/opt/projecten/hci-crs/src/EPD/WEB"
    )
    searcher = CombinedEpicSearcher(config)
    epics = searcher.search()

    # Should detect major business domains
    epic_names = [e.name for e in epics]
    assert any("Dossier" in name for name in epic_names)
    assert any("Afspraken" in name or "Agenda" in name for name in epic_names)

    # Should have actions and messages
    for epic in epics:
        if epic.category == "business":
            assert len(epic.metadata.get("actions", [])) > 0

async def test_intake_service_integration():
    """Test IntakeToBacklogService uses new searcher."""
    service = IntakeToBacklogService()
    report = await create_test_intake_report()

    result = await service.generate_backlog(report)

    # Should NOT have "General" as only epic
    assert not (len(result.epics) == 1 and result.epics[0].name == "General")

    # Should have meaningful epic names
    for epic in result.epics:
        assert epic.title != "General"
        assert len(epic.features) > 0
```

---

## Files to Create/Modify

### New Files
- `backend/app/services/journey_epic_searcher.py` - Journey-based detection
- `backend/app/services/generic_epic_searcher.py` - Folder-based detection
- `backend/app/services/combined_epic_searcher.py` - Combined searcher
- `backend/tests/services/test_journey_epic_searcher.py` - Journey tests
- `backend/tests/services/test_combined_epic_searcher.py` - Combined tests

### Files to Modify
- `backend/app/services/intake_to_backlog_service.py` - Use CombinedEpicSearcher
- `backend/app/services/brown_paper_service.py` - Use CombinedEpicSearcher

---

## Summary

| Fase | Beschrijving | Uren |
|------|--------------|------|
| 24.8.1 | Screen Scanner & Parser | 4 |
| 24.8.2 | Navigation Graph & Path Tracing | 4 |
| 24.8.3 | Action & Message Extraction | 3 |
| 24.8.4 | Folder-Based Searcher | 3 |
| 24.8.5 | Combined Searcher & Epic Generation | 4 |
| 24.8.6 | Service Integration | 3 |
| 24.8.7 | Testing & Documentation | 3 |
| **Totaal** | | **24 uur** |

---

## Key Benefits

### Journey-Based Detection
1. **User-centric** - Epics gebaseerd op wat gebruikers DOEN
2. **Alle acties zichtbaar** - Knoppen, formulieren, navigatie
3. **Alle meldingen ontdekt** - Validaties, foutmeldingen, bevestigingen
4. **E2E test scenarios** - Journeys zijn direct testbare paden
5. **Betere prioritering** - Meest gebruikte journeys = hoogste prioriteit

### Folder-Based Detection
1. **Vangt infrastructuur** - API's, libraries, database scripts
2. **Fallback** - Code niet bereikbaar via UI
3. **Compleetheid** - Geen code gemist

### Combined Approach
1. **Best of both worlds** - User journeys + code coverage
2. **94%+ coverage** - Bijna alle code gekoppeld aan epics
3. **Betekenisvolle epics** - Niet "General" maar echte business domeinen
4. **Rijke metadata** - Actions, messages, validations per epic
