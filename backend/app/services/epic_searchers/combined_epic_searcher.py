"""
Combined Epic Searcher - Journey + Folder Based Detection

Combines journey-based and folder-based epic detection:
1. Journey-based: Primary source for BUSINESS epics
   - Traces user paths through the application
   - Extracts actions, messages, validations
   - Groups related journeys into epics

2. Folder-based: Secondary source for INFRASTRUCTURE epics
   - Catches code not reachable via UI (APIs, libraries, utils)
   - Detects infrastructure patterns
   - Fills gaps from journey detection
"""

import logging
import re
from typing import Dict, List, Set

from .generic_epic_searcher import GenericEpicSearcher
from .journey_epic_searcher import JourneyBasedEpicSearcher
from .models import (
    CombinedSearchConfig,
    DetectedEpic,
    DetectedFeature,
    DetectedJourney,
    DetectedScreen,
    EpicSearchConfig,
    JourneySearchConfig,
)

logger = logging.getLogger(__name__)


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
        self._journey_searcher: JourneyBasedEpicSearcher | None = None
        self._folder_searcher: GenericEpicSearcher | None = None

    def search(self) -> List[DetectedEpic]:
        """Execute combined epic detection."""
        logger.info(f"Starting combined epic search in {self.config.project_path}")

        # =====================================================================
        # PHASE 1: Journey-based detection (Business Epics)
        # =====================================================================
        journey_config = JourneySearchConfig(
            project_path=self.config.project_path,
            max_journey_depth=self.config.max_journey_depth,
            min_screens_per_journey=self.config.min_screens_per_journey,
        )
        self._journey_searcher = JourneyBasedEpicSearcher(journey_config)
        journeys = self._journey_searcher.search()

        logger.info(f"Journey-based search found {len(journeys)} journeys")

        # Convert journeys to epics
        business_epics = self._journeys_to_epics(journeys, self._journey_searcher.screens)

        # Track which files are covered by journeys
        covered_files: Set[str] = set()
        for epic in business_epics:
            covered_files.update(epic.source_folders)

        logger.info(f"Converted to {len(business_epics)} business epics covering {len(covered_files)} files")

        # =====================================================================
        # PHASE 2: Folder-based detection (Infrastructure + Gaps)
        # =====================================================================
        folder_config = EpicSearchConfig(
            project_path=self.config.project_path,
            source_folders=self.config.source_folders,
            infrastructure_folders=self.config.infrastructure_folders,
        )
        self._folder_searcher = GenericEpicSearcher(folder_config)
        folder_epics = self._folder_searcher.search()

        logger.info(f"Folder-based search found {len(folder_epics)} folder epics")

        # =====================================================================
        # PHASE 3: Merge results
        # =====================================================================
        final_epics = business_epics.copy()

        for epic in folder_epics:
            # Always include infrastructure
            if epic.category == "infrastructure":
                if self.config.include_infrastructure:
                    # Renumber to avoid ID conflicts
                    epic.id = f"EPIC-INFRA-{len(final_epics) + 1:03d}"
                    final_epics.append(epic)

            # Include business folders not covered by journeys
            elif self.config.include_uncovered_folders:
                uncovered = [f for f in epic.source_folders if f not in covered_files]
                if uncovered:
                    epic.source_folders = uncovered
                    epic.name = f"{epic.name} (Additional)"
                    epic.confidence = 0.6  # Lower confidence for uncovered
                    epic.id = f"EPIC-ADD-{len(final_epics) + 1:03d}"
                    final_epics.append(epic)

        logger.info(f"Combined result: {len(final_epics)} total epics")
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
        epics: List[DetectedEpic] = []
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
        all_files: Set[str] = set()
        all_actions: Set[str] = set()
        all_messages: Set[str] = set()

        for journey in journeys:
            for screen_id in journey.screen_path:
                if screen_id in screens:
                    all_files.add(screens[screen_id].file_path)
            all_actions.update(journey.available_actions)
            all_messages.update(journey.possible_messages)

        # Create features from journeys
        features: List[DetectedFeature] = []
        for journey in journeys[:10]:  # Max 10 features per epic
            source_folder = ""
            if journey.screen_path and journey.screen_path[0] in screens:
                source_folder = screens[journey.screen_path[0]].file_path

            feature = DetectedFeature(
                id=f"{domain[:3].upper()}-FEAT-{len(features)+1:03d}",
                name=journey.name,
                description=f"Journey: {journey.goal}",
                source_folder=source_folder,
                epic_id="",
                estimated_stories=max(1, len(journey.available_actions)),
            )
            features.append(feature)

        # Create safe epic ID from domain
        safe_domain = re.sub(r'[^a-zA-Z0-9]', '', domain)[:3].upper() or "GEN"

        return DetectedEpic(
            id=f"EPIC-{safe_domain}-001",
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
        name = screen_id

        # Remove common prefixes
        for prefix in ['frm', 'pg', 'uc', 'ctrl', 'wf', 'asp']:
            if name.lower().startswith(prefix) and len(name) > len(prefix):
                name = name[len(prefix):]

        # Remove common suffixes
        for suffix in ['List', 'Detail', 'Edit', 'New', 'Overview', 'Form', 'Page', 'View', 'Control']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Humanize
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        return result.strip() or "General"

    @property
    def screens(self) -> Dict[str, DetectedScreen]:
        """Get all detected screens from the journey searcher."""
        if self._journey_searcher:
            return self._journey_searcher.screens
        return {}

    @property
    def journeys(self) -> List[DetectedJourney]:
        """Get all detected journeys."""
        if self._journey_searcher:
            return self._journey_searcher.journeys
        return []

    def get_summary(self) -> str:
        """Generate a human-readable summary of the detection results."""
        lines = [
            "=" * 79,
            "                    COMBINED EPIC DETECTION RESULTS",
            "=" * 79,
            "",
        ]

        if not self._journey_searcher:
            return "No search has been performed yet."

        # Business Epics
        lines.append("BUSINESS EPICS (from User Journeys)")
        lines.append("-" * 79)

        business_count = 0
        for journey in self._journey_searcher.journeys:
            lines.append(f"\nJourney: {journey.name}")
            lines.append(f"├── Path: {' → '.join(journey.screen_path[:5])}")
            if journey.available_actions:
                actions = journey.available_actions[:5]
                lines.append(f"├── Actions: [{', '.join(actions)}]")
            if journey.possible_messages:
                messages = journey.possible_messages[:3]
                lines.append(f"└── Messages: {messages}")
            business_count += 1

        # Summary
        lines.extend([
            "",
            "-" * 79,
            "SUMMARY",
            "-" * 79,
            f"Total Screens:   {len(self._journey_searcher.screens)}",
            f"Total Journeys:  {len(self._journey_searcher.journeys)}",
        ])

        if self._journey_searcher.journeys:
            all_actions = set()
            all_messages = set()
            for j in self._journey_searcher.journeys:
                all_actions.update(j.available_actions)
                all_messages.update(j.possible_messages)
            lines.append(f"Total Actions:   {len(all_actions)} unique actions discovered")
            lines.append(f"Total Messages:  {len(all_messages)} unique messages discovered")

        return "\n".join(lines)
