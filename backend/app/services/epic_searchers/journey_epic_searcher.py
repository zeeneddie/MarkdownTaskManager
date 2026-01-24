"""
Journey-Based Epic Searcher

Detects epics based on user journeys through the application by:
1. Scanning all screen files (ASPX, VB Forms, Razor, JSX, Vue, HTML)
2. Building a navigation graph (screen → screen)
3. Finding entry points (menus, start pages)
4. Tracing all possible paths through the application
5. Extracting actions and messages at each screen
6. Grouping related journeys into epics
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import DetectedJourney, DetectedScreen, JourneySearchConfig

logger = logging.getLogger(__name__)


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
        'html': [
            r'href\s*=\s*["\']([^"\']+\.(?:html?|aspx?|php)[^"\']*)["\']',
        ],
    }

    # Button/action patterns
    BUTTON_PATTERNS = [
        r'<asp:Button[^>]+Text\s*=\s*"([^"]+)"',
        r'<asp:LinkButton[^>]+Text\s*=\s*"([^"]+)"',
        r'<asp:ImageButton[^>]+AlternateText\s*=\s*"([^"]+)"',
        r'<input[^>]+value\s*=\s*"([^"]+)"[^>]+type\s*=\s*"submit"',
        r'<input[^>]+type\s*=\s*"submit"[^>]+value\s*=\s*"([^"]+)"',
        r'<button[^>]*>([^<]+)</button>',
        r'CommandName\s*=\s*"([^"]+)"',
        r'OnClick\s*=\s*"btn([^"]+)_Click"',
        r'\.Click\s*\+=.*Sub\s+(\w+)',  # VB.NET event handlers
        # React/Vue buttons
        r'onClick\s*=\s*\{[^}]*\}\s*>\s*([^<]+)<',
        r'@click\s*=\s*"[^"]*"\s*>\s*([^<]+)<',
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
        r'console\.log\s*\(\s*["\']([^"\']+)',  # Debug messages
    ]

    # Form detection patterns
    FORM_PATTERNS = [
        r'<asp:TextBox[^>]+ID\s*=\s*"([^"]+)"',
        r'<asp:DropDownList[^>]+ID\s*=\s*"([^"]+)"',
        r'<asp:CheckBox[^>]+ID\s*=\s*"([^"]+)"',
        r'<asp:RadioButton[^>]+ID\s*=\s*"([^"]+)"',
        r'<input[^>]+name\s*=\s*"([^"]+)"',
        r'<select[^>]+name\s*=\s*"([^"]+)"',
    ]

    # Entity/data patterns
    ENTITY_PATTERNS = [
        r'DataSource\s*=\s*"([^"]+)"',
        r'DataMember\s*=\s*"([^"]+)"',
        r'DataBind\s*\(\s*([^)]+)\s*\)',
        r'GridView1\.DataSource\s*=\s*(\w+)',
        r'\.Select\s*\(\s*"([^"]+)"',
        r'FROM\s+(\w+)',
    ]

    def __init__(self, config: JourneySearchConfig):
        self.config = config
        self.screens: Dict[str, DetectedScreen] = {}
        self.navigation_graph: Dict[str, Set[str]] = {}
        self.journeys: List[DetectedJourney] = []

    def search(self) -> List[DetectedJourney]:
        """Execute journey detection."""
        logger.info(f"Starting journey-based epic search in {self.config.project_path}")

        # Step 1: Scan all screen files
        self._scan_all_screens()
        logger.info(f"Found {len(self.screens)} screens")

        # Step 2: Build navigation graph
        self._build_navigation_graph()
        logger.info(f"Built navigation graph with {sum(len(v) for v in self.navigation_graph.values())} edges")

        # Step 3: Find entry points
        entry_points = self._find_entry_points()
        logger.info(f"Found {len(entry_points)} entry points")

        # Step 4: Trace journeys from each entry point
        for entry in entry_points:
            paths = self._trace_all_paths(entry, max_depth=self.config.max_journey_depth)
            for path in paths:
                journey = self._create_journey_from_path(path)
                if journey:
                    self.journeys.append(journey)

        logger.info(f"Traced {len(self.journeys)} raw journeys")

        # Step 5: Deduplicate and merge similar journeys
        self.journeys = self._merge_similar_journeys(self.journeys)
        logger.info(f"After merging: {len(self.journeys)} journeys")

        return self.journeys

    def _scan_all_screens(self) -> None:
        """Scan project for all screen files."""
        project_path = Path(self.config.project_path)

        for tech, patterns in self.SCREEN_PATTERNS.items():
            # Check if this technology should be scanned
            scan_attr = f"scan_{tech}"
            if hasattr(self.config, scan_attr) and not getattr(self.config, scan_attr):
                continue

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
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
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
        targets: Set[str] = set()

        for patterns in self.NAVIGATION_PATTERNS.values():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Normalize to screen ID
                    target_id = Path(match).stem
                    if target_id and not target_id.startswith(('#', 'javascript', 'http', 'mailto')):
                        # Filter out common non-page targets
                        if not any(ext in target_id.lower() for ext in ['.css', '.js', '.png', '.jpg', '.gif']):
                            targets.add(target_id)

        return list(targets)

    def _extract_buttons(self, content: str) -> List[str]:
        """Extract button/action names from screen."""
        buttons: Set[str] = set()

        for pattern in self.BUTTON_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            buttons.update(matches)

        # Filter and clean
        return [b.strip() for b in buttons if len(b.strip()) > 1 and len(b.strip()) < 50]

    def _extract_messages(self, content: str) -> List[str]:
        """Extract all possible messages from screen."""
        messages: Set[str] = set()

        for pattern in self.MESSAGE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            messages.update(matches)

        # Filter and clean
        return [m.strip() for m in messages if len(m.strip()) > 3 and len(m.strip()) < 200]

    def _extract_forms(self, content: str) -> List[str]:
        """Extract form field names from screen."""
        forms: Set[str] = set()

        for pattern in self.FORM_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            forms.update(matches)

        return [f.strip() for f in forms if len(f.strip()) > 1]

    def _extract_entities(self, content: str) -> List[str]:
        """Extract data entity names from screen."""
        entities: Set[str] = set()

        for pattern in self.ENTITY_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.update(matches)

        return [e.strip() for e in entities if len(e.strip()) > 1 and len(e.strip()) < 50]

    def _extract_required_role(self, content: str) -> Optional[str]:
        """Extract required role/permission from screen."""
        # Common patterns for role-based access
        patterns = [
            r'Roles\s*=\s*"([^"]+)"',
            r'RequireRole\s*\(\s*"([^"]+)"',
            r'Authorize\s*\(\s*Roles\s*=\s*"([^"]+)"',
            r'IsInRole\s*\(\s*"([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _detect_screen_type(self, file_path: Path, content: str) -> str:
        """Detect the type of screen."""
        name_lower = file_path.stem.lower()
        content_lower = content.lower()

        # Check name patterns
        if any(kw in name_lower for kw in ['menu', 'nav', 'home', 'index', 'default', 'main']):
            return 'menu'
        if any(kw in name_lower for kw in ['dashboard', 'overview', 'start']):
            return 'dashboard'
        if any(kw in name_lower for kw in ['list', 'overzicht', 'search', 'zoek', 'grid']):
            return 'list'
        if any(kw in name_lower for kw in ['detail', 'view', 'bekijk', 'show']):
            return 'detail'
        if any(kw in name_lower for kw in ['edit', 'bewerk', 'wijzig', 'update', 'modify']):
            return 'edit'
        if any(kw in name_lower for kw in ['new', 'nieuw', 'add', 'create', 'toevoeg', 'insert']):
            return 'create'
        if any(kw in name_lower for kw in ['login', 'logon', 'signin', 'auth', 'inlog']):
            return 'login'
        if any(kw in name_lower for kw in ['report', 'rapport', 'print', 'export']):
            return 'report'

        # Check content patterns
        if '<asp:GridView' in content or '<asp:Repeater' in content or 'DataGrid' in content:
            return 'list'
        if '<asp:FormView' in content or '<asp:DetailsView' in content:
            return 'detail'

        return 'form'

    def _find_entry_points(self) -> List[str]:
        """Find application entry points."""
        entry_points: List[str] = []

        for screen_id, screen in self.screens.items():
            # Menu/dashboard screens are always entry points
            if screen.screen_type in ['menu', 'dashboard', 'login']:
                if screen_id not in entry_points:
                    entry_points.append(screen_id)

            # Common entry point names
            if any(kw in screen_id.lower() for kw in ['default', 'index', 'home', 'main', 'menu', 'start']):
                if screen_id not in entry_points:
                    entry_points.append(screen_id)

        # Also add screens with no incoming navigation (orphan screens may be entry points)
        all_targets = set()
        for screen in self.screens.values():
            all_targets.update(screen.exit_points)

        for screen_id in self.screens.keys():
            if screen_id not in all_targets and screen_id not in entry_points:
                entry_points.append(screen_id)

        return entry_points

    def _build_navigation_graph(self) -> None:
        """Build bidirectional navigation graph."""
        for screen_id, screen in self.screens.items():
            if screen_id not in self.navigation_graph:
                self.navigation_graph[screen_id] = set()

            for target in screen.exit_points:
                # Add forward link
                self.navigation_graph[screen_id].add(target)

                # Add reverse link (entry point) - only if target exists
                if target in self.screens:
                    self.screens[target].entry_points.append(screen_id)

    def _trace_all_paths(self, start: str, max_depth: int = 6) -> List[List[str]]:
        """Trace all possible paths from a start screen."""
        paths: List[List[str]] = []

        def trace(current: str, path: List[str], depth: int) -> None:
            if depth > max_depth:
                return
            if current in path:  # Cycle detection
                return

            path = path + [current]
            next_screens = self.navigation_graph.get(current, set())

            if not next_screens or depth == max_depth:
                # End of path
                if len(path) >= self.config.min_screens_per_journey:
                    paths.append(path)
            else:
                for next_screen in next_screens:
                    trace(next_screen, path, depth + 1)

        trace(start, [], 0)
        return paths

    def _create_journey_from_path(self, path: List[str]) -> Optional[DetectedJourney]:
        """Create a journey from a screen path."""
        if len(path) < self.config.min_screens_per_journey:
            return None

        screens_in_path = [self.screens[s] for s in path if s in self.screens]
        if len(screens_in_path) < self.config.min_screens_per_journey:
            return None

        # Collect all interactions from the journey
        all_actions: List[str] = []
        all_messages: List[str] = []
        all_validations: List[str] = []

        for screen in screens_in_path:
            all_actions.extend(screen.buttons)
            all_messages.extend(screen.messages)

        # Determine journey name from main screen (usually second in path)
        main_screen = screens_in_path[1] if len(screens_in_path) > 1 else screens_in_path[0]

        # Determine goal based on screen types
        goal = self._infer_journey_goal(screens_in_path)

        return DetectedJourney(
            id=f"JOURNEY-{len(self.journeys) + 1:03d}",
            name=main_screen.name,
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
            error_outcomes=[m for m in all_messages if any(kw in m.lower() for kw in ['error', 'fout', 'mislukt', 'invalid', 'fail'])],
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
        if 'login' in screen_types:
            return "Authenticate user"

        return "Complete workflow"

    def _merge_similar_journeys(self, journeys: List[DetectedJourney]) -> List[DetectedJourney]:
        """Merge journeys that share the same main screen."""
        merged: Dict[str, DetectedJourney] = {}

        for journey in journeys:
            # Use first non-menu screen as key
            key_screen = None
            for screen_id in journey.screen_path:
                if screen_id in self.screens:
                    screen = self.screens[screen_id]
                    if screen.screen_type not in ['menu', 'dashboard', 'login']:
                        key_screen = screen_id
                        break

            if not key_screen:
                key_screen = journey.screen_path[1] if len(journey.screen_path) > 1 else journey.screen_path[0]

            if key_screen not in merged:
                merged[key_screen] = journey
            else:
                # Merge actions and messages
                existing = merged[key_screen]
                existing.available_actions = list(set(existing.available_actions + journey.available_actions))
                existing.possible_messages = list(set(existing.possible_messages + journey.possible_messages))
                existing.end_screens = list(set(existing.end_screens + journey.end_screens))
                existing.error_outcomes = list(set(existing.error_outcomes + journey.error_outcomes))

        return list(merged.values())

    def _humanize_name(self, name: str) -> str:
        """Convert screen ID to readable name."""
        # Remove common prefixes
        for prefix in ['frm', 'pg', 'uc', 'ctrl', 'wf', 'asp']:
            if name.lower().startswith(prefix) and len(name) > len(prefix):
                name = name[len(prefix):]

        # Remove common suffixes
        for suffix in ['Form', 'Page', 'Control', 'View']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Handle CamelCase
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        # Handle snake_case
        result = result.replace('_', ' ')
        # Handle kebab-case
        result = result.replace('-', ' ')
        # Capitalize words
        return ' '.join(word.capitalize() for word in result.split())

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            'node_modules', 'bin', 'obj', 'test', 'backup', '.git',
            '__pycache__', 'venv', 'dist', 'build', '.vs', 'packages'
        ]
        path_str = str(file_path).lower()
        return any(p in path_str for p in skip_patterns)
