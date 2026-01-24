"""
Generic Epic Searcher - Folder-Based Epic Detection

Industry-agnostic epic searcher that works for any project by:
1. Finding standard source folders (src, app, WEB, lib, etc.)
2. Scanning top-level subfolders as epic candidates
3. Applying optional grouping rules
4. Creating infrastructure epic from common folders
5. Generating features from subfolders
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Set

from .models import (
    ARCHITECTURE_PATTERNS,
    INFRASTRUCTURE_FOLDERS,
    MODULE_TYPE_PATTERNS,
    STANDARD_SOURCE_FOLDERS,
    DetectedEpic,
    DetectedFeature,
    DetectedFolder,
    EpicGenerationStrategy,
    EpicSearchConfig,
)

logger = logging.getLogger(__name__)


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
        logger.info(f"Starting folder-based epic search in {self.config.project_path}")

        # Step 1: Find source root(s)
        source_roots = self._find_source_roots()
        logger.info(f"Found {len(source_roots)} source roots")

        # Step 2: Scan folders at each root
        for root in source_roots:
            folders = self._scan_folder(root, depth=0)
            self._detected_folders.extend(folders)

        logger.info(f"Detected {len(self._detected_folders)} folders")

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

        logger.info(f"Generated {len(self._epics)} epics")
        return self._epics

    def _find_source_roots(self) -> List[Path]:
        """Find all standard source folders in the project."""
        project_path = Path(self.config.project_path)
        roots: List[Path] = []

        for folder_name in self.config.source_folders:
            # Check direct child
            candidate = project_path / folder_name
            if candidate.is_dir():
                roots.append(candidate)

            # Check one level deep (e.g., project/src/main)
            for child in project_path.iterdir():
                if child.is_dir() and not child.name.startswith('.'):
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

        results: List[DetectedFolder] = []

        try:
            items = list(folder.iterdir())
        except PermissionError:
            logger.warning(f"Permission denied: {folder}")
            return []

        for item in items:
            if not item.is_dir():
                continue

            # Skip hidden folders and common non-code folders
            if item.name.startswith('.') or item.name in [
                'node_modules', 'bin', 'obj', '__pycache__', 'venv',
                '.git', '.vs', 'packages', 'dist', 'build', 'coverage'
            ]:
                continue

            # Count files in this folder
            try:
                file_count = sum(1 for f in item.rglob('*') if f.is_file() and not f.name.startswith('.'))
            except Exception:
                file_count = 0

            # Skip folders with too few files (only for top-level)
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
        epics: List[DetectedEpic] = []
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
        epics: List[DetectedEpic] = []
        epic_counter = 1
        grouped_folders: Set[str] = set()

        # Apply grouping rules
        for group_name, folder_patterns in self.config.grouping_rules.items():
            matched_folders: List[DetectedFolder] = []

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
        layers: dict[str, List[DetectedFolder]] = {
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

        epics: List[DetectedEpic] = []
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
        infra_folders: List[DetectedFolder] = []

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
