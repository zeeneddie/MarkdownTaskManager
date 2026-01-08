"""
StandardsLoaderService - Load coding standards based on workflow context and tech stack

Standards are loaded from .standards/ folder and injected into agent prompts.
This implements the Agent OS "standards-as-files" concept.

Week 59: Agent OS Integration
Source: github.com/zeeneddie/agent-os

Tech Stack Filtering:
- Not all standards are loaded for every project
- Standards are filtered by project's tech stack (python, javascript, dotnet, java, go, rust)
- Global standards are always loaded
- Stack-specific standards (e.g., dotnet-migration-patterns.md) only load for matching stacks
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StandardCategory(str, Enum):
    """Categories of coding standards."""
    GLOBAL = "global"
    BACKEND = "backend"
    FRONTEND = "frontend"
    TESTING = "testing"
    SECURITY = "security"
    STACKS = "stacks"  # Stack-specific coding principles (NASA Power of 10 adapted)


class TechStack(str, Enum):
    """Supported technology stacks."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    DOTNET = "dotnet"
    CSHARP = "csharp"
    VBNET = "vbnet"
    ASP_CLASSIC = "asp-classic"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    ANGULAR = "angular"
    VUE = "vue"
    REACT = "react"


# Standard name patterns → Tech stack mapping
# Used to filter which standards apply to which tech stacks
STANDARD_STACK_PATTERNS: Dict[str, Set[TechStack]] = {
    # Python standards
    "python": {TechStack.PYTHON},
    "fastapi": {TechStack.PYTHON},
    "django": {TechStack.PYTHON},
    "flask": {TechStack.PYTHON},
    "pytest": {TechStack.PYTHON},

    # .NET standards
    "dotnet": {TechStack.DOTNET, TechStack.CSHARP, TechStack.VBNET},
    "csharp": {TechStack.CSHARP, TechStack.DOTNET},
    "vbnet": {TechStack.VBNET, TechStack.DOTNET},
    "blazor": {TechStack.DOTNET, TechStack.CSHARP},
    "aspnet": {TechStack.DOTNET, TechStack.CSHARP},
    "webforms": {TechStack.DOTNET, TechStack.VBNET, TechStack.CSHARP},
    "asp-classic": {TechStack.ASP_CLASSIC},

    # Java standards
    "java": {TechStack.JAVA},
    "spring": {TechStack.JAVA},
    "struts": {TechStack.JAVA},
    "ejb": {TechStack.JAVA},
    "jakarta": {TechStack.JAVA},

    # JavaScript/TypeScript standards
    "javascript": {TechStack.JAVASCRIPT},
    "typescript": {TechStack.TYPESCRIPT, TechStack.JAVASCRIPT},
    "react": {TechStack.REACT, TechStack.TYPESCRIPT, TechStack.JAVASCRIPT},
    "vue": {TechStack.VUE, TechStack.TYPESCRIPT, TechStack.JAVASCRIPT},
    "angular": {TechStack.ANGULAR, TechStack.TYPESCRIPT},
    "nodejs": {TechStack.JAVASCRIPT, TechStack.TYPESCRIPT},
    "jest": {TechStack.JAVASCRIPT, TechStack.TYPESCRIPT},

    # Go standards
    "golang": {TechStack.GO},
    "go-": {TechStack.GO},
    "go": {TechStack.GO},

    # Rust standards
    "rust": {TechStack.RUST},
    "cargo": {TechStack.RUST},
}

# Stack name to coding principles file mapping
# Maps detected stacks to their corresponding .standards/stacks/*.md files
STACK_TO_PRINCIPLES_FILE: Dict[TechStack, str] = {
    TechStack.PYTHON: "python",
    TechStack.TYPESCRIPT: "typescript",
    TechStack.JAVASCRIPT: "typescript",  # Use TypeScript principles for JS too
    TechStack.CSHARP: "csharp",
    TechStack.VBNET: "vbnet",
    TechStack.ASP_CLASSIC: "asp-classic",
    TechStack.DOTNET: "csharp",  # Default to C# for generic .NET
    TechStack.JAVA: "java",
    TechStack.GO: "go",
    TechStack.ANGULAR: "angular",
    TechStack.VUE: "vue",
    TechStack.REACT: "react",
}


# Workflow → Standards mapping
# Determines which standards categories are loaded for each workflow type
# STACKS category is included for code-related workflows (Week 59+)
WORKFLOW_STANDARDS_MAP: Dict[str, List[StandardCategory]] = {
    "GREEN_PAPER": [StandardCategory.GLOBAL],
    "BROWN_PAPER": [
        StandardCategory.GLOBAL,
        StandardCategory.BACKEND,
        StandardCategory.FRONTEND,
        StandardCategory.SECURITY,
        StandardCategory.STACKS,
    ],
    "NEW_FEATURE": [
        StandardCategory.GLOBAL,
        StandardCategory.BACKEND,
        StandardCategory.FRONTEND,
        StandardCategory.TESTING,
        StandardCategory.STACKS,
    ],
    "BUG": [StandardCategory.GLOBAL, StandardCategory.TESTING, StandardCategory.STACKS],
    "MAINTENANCE": [
        StandardCategory.GLOBAL,
        StandardCategory.BACKEND,
        StandardCategory.TESTING,
        StandardCategory.STACKS,
    ],
    "QUALITY_AUDIT": [
        StandardCategory.GLOBAL,
        StandardCategory.SECURITY,
        StandardCategory.TESTING,
        StandardCategory.STACKS,
    ],
    "MIGRATION": [
        StandardCategory.GLOBAL,
        StandardCategory.BACKEND,
        StandardCategory.FRONTEND,
        StandardCategory.SECURITY,
        StandardCategory.STACKS,
    ],
    "TESTING": [StandardCategory.GLOBAL, StandardCategory.TESTING, StandardCategory.STACKS],
    "QUALITY_IMPROVEMENT": [
        StandardCategory.GLOBAL,
        StandardCategory.BACKEND,
        StandardCategory.TESTING,
        StandardCategory.STACKS,
    ],
    "ENHANCEMENT": [
        StandardCategory.GLOBAL,
        StandardCategory.BACKEND,
        StandardCategory.TESTING,
        StandardCategory.STACKS,
    ],
    "PROJECT_DEFINITION": [StandardCategory.GLOBAL],
}


class StandardsLoaderService:
    """
    Service for loading coding standards based on workflow context.

    Standards are markdown files stored in .standards/ folder, organized by category.
    When a workflow starts, relevant standards are loaded and injected into agent prompts.
    """

    def __init__(self, standards_path: Optional[str] = None):
        """
        Initialize the standards loader.

        Args:
            standards_path: Path to .standards/ folder. Defaults to project root.
        """
        if standards_path:
            self.standards_path = Path(standards_path)
        else:
            # Default: project root/.standards/
            # backend/app/services/ -> project root
            self.standards_path = Path(__file__).parent.parent.parent.parent / ".standards"

        self._cache: Dict[str, str] = {}
        self._load_all_standards()

    def _load_all_standards(self) -> None:
        """Load all standards into cache on initialization."""
        if not self.standards_path.exists():
            logger.warning(f"Standards path does not exist: {self.standards_path}")
            return

        for category in StandardCategory:
            category_path = self.standards_path / category.value
            if category_path.exists():
                for file in category_path.glob("*.md"):
                    key = f"{category.value}/{file.stem}"
                    try:
                        self._cache[key] = file.read_text(encoding="utf-8")
                        logger.debug(f"Loaded standard: {key}")
                    except Exception as e:
                        logger.error(f"Failed to load standard {key}: {e}")

        logger.info(f"Loaded {len(self._cache)} standards from {self.standards_path}")

    def get_standards_for_workflow(
        self,
        workflow_type: str,
        tech_stacks: Optional[List[str]] = None
    ) -> str:
        """
        Get concatenated standards for a specific workflow type, filtered by tech stack.

        Args:
            workflow_type: The workflow type (e.g., "NEW_FEATURE", "BUG")
            tech_stacks: Optional list of tech stacks to filter by (e.g., ["python", "javascript"])
                         If None, all standards for the workflow categories are returned.

        Returns:
            Concatenated markdown string of all relevant standards
        """
        categories = WORKFLOW_STANDARDS_MAP.get(
            workflow_type.upper(), [StandardCategory.GLOBAL]
        )

        # Convert tech_stacks to TechStack enum set
        stack_filter: Optional[Set[TechStack]] = None
        if tech_stacks:
            stack_filter = set()
            for stack in tech_stacks:
                try:
                    stack_filter.add(TechStack(stack.lower()))
                except ValueError:
                    logger.warning(f"Unknown tech stack: {stack}")

        standards_content = []
        loaded_standards = []

        for category in categories:
            category_standards = self._get_category_standards(category, stack_filter)
            if category_standards:
                standards_content.append(f"## {category.value.upper()} STANDARDS\n")
                standards_content.append(category_standards)
                standards_content.append("\n---\n")
                loaded_standards.append(category.value)

        if loaded_standards:
            stack_info = f" (stacks: {tech_stacks})" if tech_stacks else ""
            logger.debug(f"Loaded standards for {workflow_type}{stack_info}: {loaded_standards}")

        return "\n".join(standards_content)

    def _get_category_standards(
        self,
        category: StandardCategory,
        stack_filter: Optional[Set[TechStack]] = None
    ) -> str:
        """
        Get all standards for a specific category, optionally filtered by tech stack.

        Args:
            category: The category to load standards from
            stack_filter: Optional set of TechStack enums to filter by

        Returns:
            Concatenated standards content
        """
        content = []
        for key, value in sorted(self._cache.items()):
            if key.startswith(category.value + "/"):
                # Check if this standard matches the tech stack filter
                if stack_filter:
                    standard_name = key.split("/")[1].lower()
                    if not self._standard_matches_stacks(standard_name, stack_filter):
                        continue
                content.append(value)
        return "\n\n".join(content)

    def _standard_matches_stacks(
        self,
        standard_name: str,
        stack_filter: Set[TechStack]
    ) -> bool:
        """
        Check if a standard matches any of the given tech stacks.

        Global standards (those not matching any pattern) always match.
        Stack-specific standards only match if their stack is in the filter.

        Args:
            standard_name: Name of the standard (e.g., "python-fastapi", "dotnet-migration-patterns")
            stack_filter: Set of TechStack enums to match against

        Returns:
            True if the standard should be included
        """
        # Check which tech stacks this standard belongs to
        standard_stacks: Set[TechStack] = set()

        for pattern, stacks in STANDARD_STACK_PATTERNS.items():
            if pattern in standard_name:
                standard_stacks.update(stacks)

        # If no patterns matched, it's a generic standard - always include
        if not standard_stacks:
            return True

        # Include if any of the standard's stacks match the filter
        return bool(standard_stacks & stack_filter)

    def get_stack_coding_principles(
        self,
        tech_stacks: List[str],
        include_base: bool = True
    ) -> str:
        """
        Get coding principles for specific tech stacks.

        This loads the NASA Power of 10 adapted principles from .standards/stacks/*.md
        files based on the detected technology stack.

        Args:
            tech_stacks: List of tech stacks (e.g., ["python", "typescript"])
            include_base: Whether to include global/coding-principles-base.md

        Returns:
            Concatenated markdown string of coding principles
        """
        content_parts = []

        # 1. Load base principles if requested
        if include_base:
            base_key = "global/coding-principles-base"
            if base_key in self._cache:
                content_parts.append("# BASE CODING PRINCIPLES (NASA Power of 10)\n")
                content_parts.append(self._cache[base_key])
                content_parts.append("\n---\n")

        # 2. Load stack-specific principles
        loaded_stacks = []
        for stack_str in tech_stacks:
            try:
                stack = TechStack(stack_str.lower())
                principles_file = STACK_TO_PRINCIPLES_FILE.get(stack)
                if principles_file:
                    key = f"stacks/{principles_file}"
                    if key in self._cache:
                        content_parts.append(f"\n# {stack.value.upper()} CODING PRINCIPLES\n")
                        content_parts.append(self._cache[key])
                        content_parts.append("\n---\n")
                        loaded_stacks.append(stack.value)
            except ValueError:
                logger.warning(f"Unknown tech stack for coding principles: {stack_str}")

        if loaded_stacks:
            logger.info(f"Loaded coding principles for stacks: {loaded_stacks}")

        return "\n".join(content_parts)

    def get_quality_gate_rules(self, tech_stacks: List[str]) -> List[Dict[str, any]]:
        """
        Extract quality gate rules from stack coding principles.

        These rules are used by Quinn to validate code quality.

        Args:
            tech_stacks: List of tech stacks to get rules for

        Returns:
            List of quality gate rule definitions
        """
        rules = []

        for stack_str in tech_stacks:
            try:
                stack = TechStack(stack_str.lower())
                principles_file = STACK_TO_PRINCIPLES_FILE.get(stack)
                if principles_file:
                    key = f"stacks/{principles_file}"
                    if key in self._cache:
                        # Parse quality gate table from markdown
                        content = self._cache[key]
                        stack_rules = self._parse_quality_gate_rules(content, stack.value)
                        rules.extend(stack_rules)
            except ValueError:
                continue

        return rules

    def _parse_quality_gate_rules(
        self,
        content: str,
        stack_name: str
    ) -> List[Dict[str, any]]:
        """
        Parse quality gate rules from markdown content.

        Looks for tables with columns: Check ID, Rule, Threshold, Severity
        """
        rules = []
        lines = content.split("\n")
        in_table = False
        header_found = False

        for line in lines:
            # Detect quality gate table
            if "Quality Gate" in line and "Check" in line:
                in_table = True
                continue

            if in_table:
                # Skip header separator
                if line.startswith("|--") or line.startswith("| --"):
                    header_found = True
                    continue

                # Parse table rows
                if header_found and line.startswith("|"):
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 4:
                        rules.append({
                            "check_id": parts[0],
                            "rule": parts[1],
                            "threshold": parts[2],
                            "severity": parts[3].lower(),
                            "stack": stack_name
                        })

                # End of table
                if not line.startswith("|") and header_found:
                    in_table = False
                    header_found = False

        return rules

    def get_standard(self, category: str, name: str) -> Optional[str]:
        """
        Get a specific standard by category and name.

        Args:
            category: Standard category (e.g., "global", "backend")
            name: Standard name without extension (e.g., "git-conventions")

        Returns:
            Standard content or None if not found
        """
        key = f"{category}/{name}"
        return self._cache.get(key)

    def list_standards(self) -> List[Dict[str, str]]:
        """
        List all available standards.

        Returns:
            List of dicts with key, category, and name for each standard
        """
        return [
            {
                "key": key,
                "category": key.split("/")[0],
                "name": key.split("/")[1],
                "size": len(self._cache[key])
            }
            for key in sorted(self._cache.keys())
        ]

    def list_categories(self) -> List[Dict[str, any]]:
        """
        List all categories with their standard counts.

        Returns:
            List of dicts with category name and count
        """
        category_counts = {}
        for key in self._cache.keys():
            category = key.split("/")[0]
            category_counts[category] = category_counts.get(category, 0) + 1

        return [
            {"category": cat, "count": count}
            for cat, count in sorted(category_counts.items())
        ]

    def reload(self) -> int:
        """
        Reload all standards from disk.

        Returns:
            Count of loaded standards
        """
        self._cache.clear()
        self._load_all_standards()
        logger.info(f"Reloaded {len(self._cache)} standards")
        return len(self._cache)

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Search standards by content.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching standards with snippets
        """
        query_lower = query.lower()
        results = []

        for key, content in self._cache.items():
            if query_lower in content.lower():
                # Find snippet around match
                idx = content.lower().find(query_lower)
                start = max(0, idx - 50)
                end = min(len(content), idx + len(query) + 50)
                snippet = content[start:end].replace("\n", " ")

                results.append({
                    "key": key,
                    "category": key.split("/")[0],
                    "name": key.split("/")[1],
                    "snippet": f"...{snippet}..."
                })

        return results

    def get_workflow_mapping(self) -> Dict[str, List[str]]:
        """
        Get the workflow to standards category mapping.

        Returns:
            Dict mapping workflow types to category lists
        """
        return {
            workflow: [cat.value for cat in categories]
            for workflow, categories in WORKFLOW_STANDARDS_MAP.items()
        }

    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about loaded standards.

        Returns:
            Dict with statistics
        """
        total_size = sum(len(content) for content in self._cache.values())
        return {
            "total_standards": len(self._cache),
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2),
            "categories": self.list_categories(),
            "standards_path": str(self.standards_path),
            "path_exists": self.standards_path.exists()
        }


# Singleton instance
_standards_loader: Optional[StandardsLoaderService] = None


def get_standards_loader() -> StandardsLoaderService:
    """
    Get or create the standards loader singleton.

    Returns:
        StandardsLoaderService instance
    """
    global _standards_loader
    if _standards_loader is None:
        _standards_loader = StandardsLoaderService()
    return _standards_loader


def reset_standards_loader() -> None:
    """Reset the singleton (useful for testing)."""
    global _standards_loader
    _standards_loader = None
