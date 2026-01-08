# backend/app/services/foundation_detection_service.py
"""
Foundation Detection Service - Phase 1.5

Identifies foundation/infrastructure modules in legacy codebases based on:
1. Hub Module Detection: Modules with highest reference counts
2. Cross-cutting Pattern Detection: Auth, logging, error handling, caching
3. Shared UI Component Detection: Headers, footers, forms, navigation
4. Foundation Epic Generation: Automatic EPIC-000-foundation structure

Used by:
- BROWN_PAPER workflow
- BROWN_PAPER_ENHANCED workflow
- MIGRATION_ENHANCED workflow
- BACKLOG_GENERATION workflow

Author: Claude (AI Agent)
Created: 2025-12-31
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class FoundationCategory(Enum):
    """Categories of foundation modules."""
    SECURITY = "security"
    DATABASE = "database"
    UI_COMPONENTS = "ui_components"
    SHARED_SERVICES = "shared_services"
    INFRASTRUCTURE = "infrastructure"
    ADMIN = "admin"


@dataclass
class FoundationModule:
    """A detected foundation module."""
    name: str
    path: str
    category: FoundationCategory
    reference_count: int
    referenced_by: List[str]
    patterns_matched: List[str]
    confidence: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "category": self.category.value,
            "reference_count": self.reference_count,
            "referenced_by": self.referenced_by[:10],  # Top 10
            "patterns_matched": self.patterns_matched,
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class FoundationFeature:
    """A feature within the foundation epic."""
    id: str
    name: str
    category: FoundationCategory
    description: str
    modules: List[FoundationModule]
    estimated_loc: int
    priority: int  # 0 = highest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "modules": [m.to_dict() for m in self.modules],
            "estimated_loc": self.estimated_loc,
            "priority": self.priority,
        }


@dataclass
class FoundationEpic:
    """The generated foundation epic."""
    id: str = "EPIC-000-foundation"
    name: str = "Foundation Infrastructure"
    description: str = "Core infrastructure and shared services migrated first"
    features: List[FoundationFeature] = field(default_factory=list)
    total_modules: int = 0
    total_loc: int = 0
    migration_order: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "features": [f.to_dict() for f in self.features],
            "total_modules": self.total_modules,
            "total_loc": self.total_loc,
            "migration_order": self.migration_order,
        }


@dataclass
class FoundationDetectionResult:
    """Result of foundation detection."""
    success: bool = True
    foundation_modules: List[FoundationModule] = field(default_factory=list)
    foundation_epic: Optional[FoundationEpic] = None
    non_foundation_modules: List[str] = field(default_factory=list)
    detection_stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "foundation_modules": [m.to_dict() for m in self.foundation_modules],
            "foundation_epic": self.foundation_epic.to_dict() if self.foundation_epic else None,
            "non_foundation_modules": self.non_foundation_modules,
            "detection_stats": self.detection_stats,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
        }


class FoundationDetectionService:
    """
    Service for detecting foundation/infrastructure modules in legacy codebases.

    Detection Strategy:
    1. Hub Detection: Modules referenced by > threshold% of codebase
    2. Pattern Matching: Known foundation patterns (security, db, etc.)
    3. Naming Conventions: Common foundation folder/file names
    4. Cross-cutting Analysis: Modules used across many domains
    """

    # Threshold: modules referenced by more than this % are foundation candidates
    HUB_THRESHOLD_PERCENT = 5.0

    # Minimum reference count for hub detection
    MIN_REFERENCE_COUNT = 50

    # Pattern definitions for each foundation category
    FOUNDATION_PATTERNS: Dict[FoundationCategory, Dict[str, List[str]]] = {
        FoundationCategory.SECURITY: {
            "path_patterns": [
                "security", "auth", "authentication", "authorization",
                "permission", "login", "session", "identity", "oauth",
                "jwt", "token", "credential", "password", "role", "access"
            ],
            "code_patterns": [
                r"CanView|CanEdit|CanDelete|CanAdd",
                r"IsAuthenticated|IsAuthorized|HasPermission",
                r"CheckPermission|ValidateToken|VerifyCredential",
                r"Login|Logout|SignIn|SignOut",
                r"Session\(|Session\[",
            ],
        },
        FoundationCategory.DATABASE: {
            "path_patterns": [
                "database", "db", "data", "repository", "dal",
                "persistence", "storage", "connection", "query",
                "sql", "orm", "entity", "model"
            ],
            "code_patterns": [
                r"Connection|Recordset|Command",
                r"Execute|Query|Select|Insert|Update|Delete",
                r"ADODB|SqlConnection|DbContext",
                r"Transaction|Commit|Rollback",
                r"OpenConnection|CloseConnection",
            ],
        },
        FoundationCategory.UI_COMPONENTS: {
            "path_patterns": [
                "include", "shared", "common", "component", "control",
                "header", "footer", "menu", "navigation", "nav",
                "layout", "template", "master", "form", "element",
                "widget", "partial"
            ],
            "code_patterns": [
                r"RenderControl|CreateElement",
                r"BuildForm|GenerateHTML|WriteHTML",
                r"MasterPage|Layout|Template",
                r"#include|Server\.Execute",
            ],
        },
        FoundationCategory.SHARED_SERVICES: {
            "path_patterns": [
                "procedure", "function", "helper", "util", "utility",
                "service", "handler", "manager", "provider", "factory",
                "standard", "base", "core", "common", "shared", "lib"
            ],
            "code_patterns": [
                r"FormatDate|FormatNumber|FormatCurrency",
                r"ValidateInput|SanitizeInput",
                r"LogError|LogInfo|WriteLog",
                r"SendEmail|SendNotification",
                r"GetConfig|GetSetting",
            ],
        },
        FoundationCategory.INFRASTRUCTURE: {
            "path_patterns": [
                "config", "setting", "environment", "constant",
                "logging", "log", "trace", "debug", "error",
                "cache", "caching", "mail", "email", "notification",
                "file", "upload", "download", "export", "import"
            ],
            "code_patterns": [
                r"Application\(|Server\.",
                r"Cache\(|Cache\[",
                r"Error|Exception|OnError",
                r"FileSystem|FileUpload",
                r"SendMail|CDOSYS|CDO\.",
            ],
        },
        FoundationCategory.ADMIN: {
            "path_patterns": [
                "admin", "beheer", "management", "system",
                "configuration", "setup", "install", "maintenance"
            ],
            "code_patterns": [
                r"IsAdmin|IsSuperUser|IsSystemAdmin",
                r"SystemSetting|GlobalConfig",
                r"Maintenance|Cleanup|Purge",
            ],
        },
    }

    def __init__(
        self,
        hub_threshold_percent: float = None,
        min_reference_count: int = None
    ):
        """
        Initialize the Foundation Detection Service.

        Args:
            hub_threshold_percent: Override default hub threshold (5%)
            min_reference_count: Override minimum reference count (50)
        """
        self.hub_threshold = hub_threshold_percent or self.HUB_THRESHOLD_PERCENT
        self.min_refs = min_reference_count or self.MIN_REFERENCE_COUNT

    def detect_foundation(
        self,
        dependency_graph: Dict[str, Any],
        code_metrics: Optional[Dict[str, Any]] = None,
        project_path: Optional[str] = None
    ) -> FoundationDetectionResult:
        """
        Main entry point: Detect foundation modules from dependency graph.

        Args:
            dependency_graph: Output from DependencyGraphService.analyze_directory()
            code_metrics: Optional code analysis metrics
            project_path: Optional project root path for additional analysis

        Returns:
            FoundationDetectionResult with detected modules and generated epic
        """
        import time
        start_time = time.time()

        result = FoundationDetectionResult()

        try:
            # Step 1: Extract module reference counts from graph
            module_refs = self._extract_module_references(dependency_graph)

            # Step 2: Detect hub modules (high reference count)
            hub_modules = self._detect_hub_modules(module_refs, dependency_graph)

            # Step 3: Detect pattern-based foundation modules
            pattern_modules = self._detect_pattern_modules(dependency_graph, project_path)

            # Step 4: Merge and deduplicate
            all_foundation = self._merge_detections(hub_modules, pattern_modules)

            # Step 5: Calculate confidence scores
            for module in all_foundation:
                module.confidence = self._calculate_confidence(module, module_refs)

            # Step 6: Sort by reference count and confidence
            all_foundation.sort(key=lambda m: (-m.reference_count, -m.confidence))

            result.foundation_modules = all_foundation

            # Step 7: Generate Foundation Epic structure
            result.foundation_epic = self._generate_foundation_epic(all_foundation, code_metrics)

            # Step 8: Identify non-foundation modules
            all_module_names = set(module_refs.keys())
            foundation_names = {m.name for m in all_foundation}
            result.non_foundation_modules = sorted(all_module_names - foundation_names)

            # Step 9: Generate statistics
            result.detection_stats = {
                "total_modules": len(module_refs),
                "foundation_modules": len(all_foundation),
                "non_foundation_modules": len(result.non_foundation_modules),
                "hub_detected": len(hub_modules),
                "pattern_detected": len(pattern_modules),
                "categories": self._count_by_category(all_foundation),
                "hub_threshold_percent": self.hub_threshold,
                "min_reference_count": self.min_refs,
            }

            logger.info(
                f"Foundation detection complete: {len(all_foundation)} foundation modules, "
                f"{len(result.non_foundation_modules)} business modules"
            )

        except Exception as e:
            logger.error(f"Foundation detection failed: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _extract_module_references(
        self,
        dependency_graph: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Extract reference counts for each module from dependency graph.

        Returns dict of module_name -> reference_count (inbound edges)
        """
        refs: Dict[str, int] = {}

        # Handle different graph formats
        edges = dependency_graph.get("edges", [])
        modules = dependency_graph.get("modules", {})

        # If modules dict has reference counts directly
        if isinstance(modules, dict):
            for name, info in modules.items():
                if isinstance(info, dict):
                    refs[name] = info.get("reference_count", 0)
                    # Also check "referenced_by" list length
                    if "referenced_by" in info:
                        refs[name] = max(refs[name], len(info["referenced_by"]))

        # Count from edges (target = referenced module)
        for edge in edges:
            target = edge.get("target", edge.get("to", ""))
            if target:
                refs[target] = refs.get(target, 0) + 1

        # Also check hub_modules if present
        hub_modules = dependency_graph.get("hub_modules", [])
        for hub in hub_modules:
            if isinstance(hub, dict):
                name = hub.get("name", hub.get("module", ""))
                count = hub.get("reference_count", hub.get("refs", 0))
                if name:
                    refs[name] = max(refs.get(name, 0), count)

        return refs

    def _detect_hub_modules(
        self,
        module_refs: Dict[str, int],
        dependency_graph: Dict[str, Any]
    ) -> List[FoundationModule]:
        """
        Detect hub modules based on high reference counts.
        """
        if not module_refs:
            return []

        total_modules = len(module_refs)
        threshold_count = max(
            self.min_refs,
            int(total_modules * (self.hub_threshold / 100))
        )

        hub_modules = []

        for name, ref_count in module_refs.items():
            if ref_count >= threshold_count:
                # Determine category from name patterns
                category = self._categorize_by_name(name)

                # Get referenced_by list if available
                modules_data = dependency_graph.get("modules", {})
                referenced_by = []
                if isinstance(modules_data, dict) and name in modules_data:
                    mod_info = modules_data[name]
                    if isinstance(mod_info, dict):
                        referenced_by = mod_info.get("referenced_by", [])

                hub_modules.append(FoundationModule(
                    name=name,
                    path=self._get_module_path(name, dependency_graph),
                    category=category,
                    reference_count=ref_count,
                    referenced_by=referenced_by[:20],  # Top 20
                    patterns_matched=["hub_detection"],
                    confidence=0.0,  # Calculated later
                    description=f"Hub module with {ref_count} references"
                ))

        return hub_modules

    def _detect_pattern_modules(
        self,
        dependency_graph: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> List[FoundationModule]:
        """
        Detect foundation modules based on naming patterns.
        """
        pattern_modules = []
        modules = dependency_graph.get("modules", {})
        module_refs = self._extract_module_references(dependency_graph)

        # Handle both dict and list formats
        if isinstance(modules, dict):
            module_names = list(modules.keys())
        elif isinstance(modules, list):
            module_names = [m.get("name", m) if isinstance(m, dict) else str(m) for m in modules]
        else:
            module_names = []

        for name in module_names:
            name_lower = name.lower()
            matched_patterns = []
            detected_category = None

            # Check each category's patterns
            for category, patterns in self.FOUNDATION_PATTERNS.items():
                path_patterns = patterns.get("path_patterns", [])

                for pattern in path_patterns:
                    if pattern in name_lower:
                        matched_patterns.append(f"{category.value}:{pattern}")
                        if detected_category is None:
                            detected_category = category
                        break

            if matched_patterns and detected_category:
                ref_count = module_refs.get(name, 0)

                pattern_modules.append(FoundationModule(
                    name=name,
                    path=self._get_module_path(name, dependency_graph),
                    category=detected_category,
                    reference_count=ref_count,
                    referenced_by=[],
                    patterns_matched=matched_patterns,
                    confidence=0.0,
                    description=f"Pattern-detected {detected_category.value} module"
                ))

        return pattern_modules

    def _merge_detections(
        self,
        hub_modules: List[FoundationModule],
        pattern_modules: List[FoundationModule]
    ) -> List[FoundationModule]:
        """
        Merge hub and pattern detections, preferring hub data.
        """
        merged: Dict[str, FoundationModule] = {}

        # Add pattern modules first
        for module in pattern_modules:
            merged[module.name] = module

        # Merge/override with hub modules
        for module in hub_modules:
            if module.name in merged:
                existing = merged[module.name]
                # Merge patterns
                all_patterns = list(set(existing.patterns_matched + module.patterns_matched))
                # Use hub's ref count (more accurate)
                existing.reference_count = max(existing.reference_count, module.reference_count)
                existing.patterns_matched = all_patterns
                existing.referenced_by = module.referenced_by or existing.referenced_by
            else:
                merged[module.name] = module

        return list(merged.values())

    def _categorize_by_name(self, name: str) -> FoundationCategory:
        """Categorize a module by its name using patterns."""
        name_lower = name.lower()

        for category, patterns in self.FOUNDATION_PATTERNS.items():
            path_patterns = patterns.get("path_patterns", [])
            for pattern in path_patterns:
                if pattern in name_lower:
                    return category

        return FoundationCategory.SHARED_SERVICES  # Default

    def _get_module_path(
        self,
        name: str,
        dependency_graph: Dict[str, Any]
    ) -> str:
        """Get the file path for a module from the graph."""
        modules = dependency_graph.get("modules", {})

        if isinstance(modules, dict) and name in modules:
            mod_info = modules[name]
            if isinstance(mod_info, dict):
                return mod_info.get("path", name)

        return name

    def _calculate_confidence(
        self,
        module: FoundationModule,
        module_refs: Dict[str, int]
    ) -> float:
        """
        Calculate confidence score for a foundation module.

        Factors:
        - Reference count (higher = more confident)
        - Number of patterns matched (more = more confident)
        - Category clarity (single clear match = more confident)
        """
        confidence = 0.5  # Base

        # Reference count factor (0-0.3)
        max_refs = max(module_refs.values()) if module_refs else 1
        max_refs = max(max_refs, 1)  # Prevent division by zero
        ref_ratio = module.reference_count / max_refs
        confidence += ref_ratio * 0.3

        # Pattern match factor (0-0.2)
        pattern_count = len(module.patterns_matched)
        if pattern_count >= 3:
            confidence += 0.2
        elif pattern_count >= 2:
            confidence += 0.15
        elif pattern_count >= 1:
            confidence += 0.1

        # Hub detection bonus
        if "hub_detection" in module.patterns_matched:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_foundation_epic(
        self,
        foundation_modules: List[FoundationModule],
        code_metrics: Optional[Dict[str, Any]] = None
    ) -> FoundationEpic:
        """
        Generate EPIC-000-foundation structure from detected modules.
        """
        epic = FoundationEpic()

        # Group modules by category
        by_category: Dict[FoundationCategory, List[FoundationModule]] = {}
        for module in foundation_modules:
            if module.category not in by_category:
                by_category[module.category] = []
            by_category[module.category].append(module)

        # Create features for each category
        feature_priority = {
            FoundationCategory.SECURITY: 0,
            FoundationCategory.DATABASE: 1,
            FoundationCategory.SHARED_SERVICES: 2,
            FoundationCategory.UI_COMPONENTS: 3,
            FoundationCategory.INFRASTRUCTURE: 4,
            FoundationCategory.ADMIN: 5,
        }

        feature_descriptions = {
            FoundationCategory.SECURITY: "Authentication, authorization, and permission system",
            FoundationCategory.DATABASE: "Database access layer and data operations",
            FoundationCategory.SHARED_SERVICES: "Shared procedures, utilities, and helpers",
            FoundationCategory.UI_COMPONENTS: "Shared UI components, layouts, and templates",
            FoundationCategory.INFRASTRUCTURE: "Configuration, logging, caching, and file handling",
            FoundationCategory.ADMIN: "Administration and system management modules",
        }

        for category, modules in by_category.items():
            # Estimate LOC from module count (rough estimate)
            estimated_loc = sum(m.reference_count * 50 for m in modules)  # Rough heuristic

            feature = FoundationFeature(
                id=f"FEATURE-00{feature_priority[category] + 1}-{category.value}",
                name=f"{category.value.replace('_', ' ').title()} Migration",
                category=category,
                description=feature_descriptions.get(category, f"Migrate {category.value} modules"),
                modules=modules,
                estimated_loc=estimated_loc,
                priority=feature_priority[category],
            )
            epic.features.append(feature)

        # Sort features by priority
        epic.features.sort(key=lambda f: f.priority)

        # Calculate totals
        epic.total_modules = len(foundation_modules)
        epic.total_loc = sum(f.estimated_loc for f in epic.features)

        # Generate migration order (by priority, then by reference count within priority)
        epic.migration_order = [
            f"{f.id}: {f.name}"
            for f in epic.features
        ]

        return epic

    def _count_by_category(
        self,
        modules: List[FoundationModule]
    ) -> Dict[str, int]:
        """Count modules per category."""
        counts: Dict[str, int] = {}
        for module in modules:
            cat = module.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts


# Singleton instance for easy access
_foundation_service: Optional[FoundationDetectionService] = None


def get_foundation_detection_service() -> FoundationDetectionService:
    """Get or create the Foundation Detection Service singleton."""
    global _foundation_service
    if _foundation_service is None:
        _foundation_service = FoundationDetectionService()
    return _foundation_service
