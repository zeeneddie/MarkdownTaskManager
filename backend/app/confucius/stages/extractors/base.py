"""
Base Journey Extractor.

Abstract base class for tech-stack specific journey extractors.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseJourneyExtractor(ABC):
    """
    Base class for tech-stack specific journey extractors.

    Each extractor analyzes code files for a specific technology stack
    and extracts:
    - Roles and permissions
    - Screens and UI components
    - Forms and input handling
    - Navigation patterns
    - Authorization checks
    - API endpoints
    - Event handlers

    Subclasses implement extraction logic for their specific tech stack.
    """

    def __init__(self):
        """Initialize extractor."""
        self.name = self.__class__.__name__
        self.supported_extensions: List[str] = []

    @abstractmethod
    def supports_stack(self, tech_stack: List[str]) -> bool:
        """
        Check if this extractor supports the given tech stack.

        Args:
            tech_stack: List of technology identifiers (e.g., ["aspnet", "sql"])

        Returns:
            True if this extractor can handle the tech stack
        """
        pass

    @abstractmethod
    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract user journey data from files.

        Args:
            files: List of file dicts with path, content, etc.
            code_analysis: Additional code analysis data

        Returns:
            Dict with keys:
            - roles: List of role definitions
            - screens: List of screen definitions
            - forms: List of form definitions
            - navigation: List of navigation links
            - auth_checks: List of authorization checks
            - api_endpoints: List of API endpoints
            - event_handlers: List of event handlers
        """
        pass

    def _find_files_by_extension(
        self,
        files: List[Dict[str, Any]],
        extensions: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Filter files by extension.

        Args:
            files: List of file dicts
            extensions: List of extensions to match (e.g., [".cs", ".aspx"])

        Returns:
            Filtered list of files
        """
        return [
            f for f in files
            if any(
                f.get("path", "").lower().endswith(ext.lower())
                for ext in extensions
            )
        ]

    def _extract_with_pattern(
        self,
        content: str,
        pattern: str,
        flags: int = re.MULTILINE | re.IGNORECASE,
    ) -> List[str]:
        """
        Extract matches using regex pattern.

        Args:
            content: Text content to search
            pattern: Regex pattern
            flags: Regex flags (default: MULTILINE | IGNORECASE)

        Returns:
            List of matches
        """
        return re.findall(pattern, content, flags)

    def _extract_groups_with_pattern(
        self,
        content: str,
        pattern: str,
        flags: int = re.MULTILINE | re.IGNORECASE,
    ) -> List[tuple]:
        """
        Extract match groups using regex pattern.

        Args:
            content: Text content to search
            pattern: Regex pattern with groups
            flags: Regex flags

        Returns:
            List of match tuples
        """
        return re.findall(pattern, content, flags)

    def _get_empty_result(self) -> Dict[str, Any]:
        """
        Get empty result structure.

        Returns:
            Empty result dict with all required keys
        """
        return {
            "roles": [],
            "screens": [],
            "forms": [],
            "navigation": [],
            "auth_checks": [],
            "api_endpoints": [],
            "event_handlers": [],
        }

    def _safe_hash(self, value: str) -> str:
        """
        Generate safe hash string for IDs.

        Args:
            value: Value to hash

        Returns:
            Hash string suitable for IDs
        """
        return str(abs(hash(value)))[:12]

    def _normalize_role_name(self, role: str) -> str:
        """
        Normalize role name for consistency.

        Args:
            role: Raw role name

        Returns:
            Normalized role name (uppercase, trimmed)
        """
        return role.strip().upper().replace(" ", "_")

    def _extract_screen_name_from_path(self, path: str) -> str:
        """
        Extract screen name from file path.

        Args:
            path: File path

        Returns:
            Screen name derived from filename
        """
        filename = path.split("/")[-1].split("\\")[-1]
        # Remove common extensions
        for ext in [".aspx", ".cshtml", ".razor", ".asp", ".html", ".tsx", ".jsx", ".vue"]:
            filename = filename.replace(ext, "")
        return filename

    def _determine_screen_type(self, content: str) -> str:
        """
        Determine screen type from content analysis.

        Args:
            content: File content

        Returns:
            Screen type: "form", "list", "dashboard", "wizard", "view"
        """
        content_lower = content.lower()

        # Check for form indicators
        if "<form" in content_lower or "runat=\"server\"" in content_lower:
            # Check if it's a wizard
            if "wizard" in content_lower or "step" in content_lower:
                return "wizard"
            return "form"

        # Check for list/grid indicators
        if any(keyword in content_lower for keyword in [
            "gridview", "listview", "datagrid", "table",
            "repeater", ".map(", "ng-repeat", "v-for"
        ]):
            return "list"

        # Check for dashboard indicators
        if any(keyword in content_lower for keyword in [
            "dashboard", "overview", "summary", "statistics", "chart"
        ]):
            return "dashboard"

        return "view"
