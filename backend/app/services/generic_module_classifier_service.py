"""
Generic Module Classifier Service

Week 129: Classifies modules as generic (foundation) or specific (business-domain).

Generic modules are used across multiple epics/features/stories.
They are typically:
- High in-degree (many modules depend on them)
- Hub modules in the dependency graph
- Contain cross-cutting concerns like auth, logging, caching

Classification Categories (from AGENTS.md):
- foundation_technical: Hub modules (logging, db, cache)
- foundation_user: Auth, session, profile patterns
- foundation_ui: Shared UI components
- foundation_integration: External API connectors
- business: Domain-specific modules

Usage:
    classifier = GenericModuleClassifierService()
    result = await classifier.classify_modules(project_path)

    # Result includes:
    # - generic_modules: List of foundation modules
    # - specific_modules: List of business modules
    # - classification_details: Why each module was classified
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ModuleCategory(str, Enum):
    """Classification category for a module."""
    FOUNDATION_TECHNICAL = "foundation_technical"
    FOUNDATION_USER = "foundation_user"
    FOUNDATION_UI = "foundation_ui"
    FOUNDATION_INTEGRATION = "foundation_integration"
    BUSINESS = "business"
    UNKNOWN = "unknown"


@dataclass
class ClassifiedModule:
    """A module with its classification."""
    name: str
    path: str
    category: ModuleCategory
    is_generic: bool  # True = foundation, False = business/specific
    confidence: float  # 0.0 - 1.0
    reasons: List[str] = field(default_factory=list)

    # Graph metrics
    imported_by_count: int = 0  # How many modules use this
    imports_count: int = 0  # How many modules this uses
    afferent_coupling: int = 0  # Ca
    efferent_coupling: int = 0  # Ce

    # Pattern matches
    matched_patterns: List[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Result of module classification."""
    project_path: str
    total_modules: int
    generic_count: int
    specific_count: int

    generic_modules: List[ClassifiedModule] = field(default_factory=list)
    specific_modules: List[ClassifiedModule] = field(default_factory=list)

    # By category breakdown
    by_category: Dict[str, List[ClassifiedModule]] = field(default_factory=dict)

    # Statistics
    avg_generic_imported_by: float = 0.0
    avg_specific_imported_by: float = 0.0

    # Warnings/issues
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "project_path": self.project_path,
            "total_modules": self.total_modules,
            "generic_count": self.generic_count,
            "specific_count": self.specific_count,
            "generic_modules": [
                {
                    "name": m.name,
                    "path": m.path,
                    "category": m.category.value,
                    "confidence": m.confidence,
                    "reasons": m.reasons,
                    "imported_by_count": m.imported_by_count,
                }
                for m in self.generic_modules
            ],
            "specific_modules": [
                {
                    "name": m.name,
                    "path": m.path,
                    "category": m.category.value,
                    "confidence": m.confidence,
                    "imported_by_count": m.imported_by_count,
                }
                for m in self.specific_modules[:20]  # Limit for API response
            ],
            "by_category": {
                cat: len(modules) for cat, modules in self.by_category.items()
            },
            "statistics": {
                "avg_generic_imported_by": round(self.avg_generic_imported_by, 2),
                "avg_specific_imported_by": round(self.avg_specific_imported_by, 2),
            },
            "warnings": self.warnings,
        }


# Pattern definitions for each category
CATEGORY_PATTERNS = {
    ModuleCategory.FOUNDATION_TECHNICAL: {
        "name_patterns": [
            r"(?i)(log|logger|logging)",
            r"(?i)(cache|caching|redis|memcache)",
            r"(?i)(database|db|dal|data.?access)",
            r"(?i)(util|utils|utility|utilities|helper|helpers)",
            r"(?i)(common|shared|core|base|foundation)",
            r"(?i)(config|configuration|settings)",
            r"(?i)(exception|error|errors)",
            r"(?i)(context|appcontext)",
            r"(?i)(factory|provider|registry)",
            r"(?i)(serializ|deserializ|json|xml)",
            r"(?i)(encrypt|decrypt|crypto|hash)",
            r"(?i)(validate|validator|validation)",
            r"(?i)(messaging|message.?queue|mq)",
            r"(?i)(event|events|bus)",
        ],
        "path_patterns": [
            r"(?i)(/lib/|/libs/|/common/|/shared/|/core/|/foundation/)",
            r"(?i)(/infrastructure/|/utils/|/helpers/)",
        ],
    },
    ModuleCategory.FOUNDATION_USER: {
        "name_patterns": [
            r"(?i)(auth|authentication|authenticat)",
            r"(?i)(authoriz|authorization|permission|acl)",
            r"(?i)(session|sessions)",
            r"(?i)(login|logout|signin|signout)",
            r"(?i)(user|users|account|accounts)",
            r"(?i)(identity|principal|claim)",
            r"(?i)(role|roles|rbac)",
            r"(?i)(token|jwt|oauth)",
            r"(?i)(password|credential)",
            r"(?i)(security|secure)",
            r"(?i)(profile|preferences)",
            r"(?i)(member|membership)",
        ],
        "path_patterns": [
            r"(?i)(/security/|/auth/|/identity/|/account/)",
        ],
    },
    ModuleCategory.FOUNDATION_UI: {
        "name_patterns": [
            r"(?i)(ui|component|components)",
            r"(?i)(layout|layouts|template|templates)",
            r"(?i)(master|masterpage)",
            r"(?i)(header|footer|sidebar|menu)",
            r"(?i)(navigation|nav|navbar)",
            r"(?i)(modal|dialog|popup)",
            r"(?i)(grid|table|list|form)",
            r"(?i)(button|input|control)",
            r"(?i)(style|styles|css|theme)",
            r"(?i)(page|pages|view|views)",
            r"(?i)(widget|widgets)",
            r"(?i)(sitemap|breadcrumb)",
        ],
        "path_patterns": [
            r"(?i)(/ui/|/components/|/controls/|/views/|/layouts/)",
            r"(?i)(/shared.?ui/|/common.?ui/)",
        ],
    },
    ModuleCategory.FOUNDATION_INTEGRATION: {
        "name_patterns": [
            r"(?i)(api|apis|rest|soap|graphql)",
            r"(?i)(client|clients|http|web.?client)",
            r"(?i)(service|services|wcf|webservice)",
            r"(?i)(integration|integrations|connector)",
            r"(?i)(adapter|adapters)",
            r"(?i)(gateway|proxy)",
            r"(?i)(external|third.?party)",
            r"(?i)(webhook|callback)",
            r"(?i)(mail|email|smtp|notification)",
            r"(?i)(sms|push|notify)",
            r"(?i)(ftp|sftp|file.?transfer)",
            r"(?i)(import|export|sync)",
        ],
        "path_patterns": [
            r"(?i)(/integrations/|/connectors/|/adapters/|/services/)",
            r"(?i)(/external/|/api/|/clients/)",
        ],
    },
}

# Minimum imported_by threshold for considering a module as generic
MIN_IMPORTED_BY_FOR_GENERIC = 3

# Hub threshold multiplier
HUB_THRESHOLD_MULTIPLIER = 2.0


class GenericModuleClassifierService:
    """
    Classifies modules as generic (foundation) or specific (business).

    Uses multiple signals:
    1. Dependency graph metrics (imported_by count, hub status)
    2. Name pattern matching
    3. Path pattern matching
    4. Combined scoring
    """

    def __init__(self):
        self._dependency_graph_service = None

    def _get_dependency_service(self):
        """Lazy load dependency graph service."""
        if self._dependency_graph_service is None:
            from app.services.dependency_graph_service import DependencyGraphService
            self._dependency_graph_service = DependencyGraphService()
        return self._dependency_graph_service

    async def classify_modules(
        self,
        project_path: str,
        dependency_graph: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classify all modules in a project as generic or specific.

        Args:
            project_path: Path to the project root
            dependency_graph: Optional pre-computed dependency graph

        Returns:
            ClassificationResult with all classified modules
        """
        logger.info(f"Classifying modules in {project_path}")

        # Get or build dependency graph
        if dependency_graph is None:
            dep_service = self._get_dependency_service()
            graph = await dep_service.analyze_project(project_path)
            dependency_graph = graph.to_dict() if hasattr(graph, 'to_dict') else graph

        # Extract modules from graph
        modules_data = self._extract_modules_from_graph(dependency_graph)

        if not modules_data:
            logger.warning(f"No modules found in {project_path}")
            return ClassificationResult(
                project_path=project_path,
                total_modules=0,
                generic_count=0,
                specific_count=0,
                warnings=["No modules found in dependency graph"]
            )

        # Calculate thresholds
        avg_imported_by = sum(m.get("imported_by", 0) for m in modules_data.values()) / len(modules_data)
        hub_threshold = avg_imported_by * HUB_THRESHOLD_MULTIPLIER

        # Classify each module
        classified_modules: List[ClassifiedModule] = []

        for name, module_info in modules_data.items():
            classified = self._classify_single_module(
                name=name,
                module_info=module_info,
                hub_threshold=hub_threshold,
                avg_imported_by=avg_imported_by
            )
            classified_modules.append(classified)

        # Build result
        generic_modules = [m for m in classified_modules if m.is_generic]
        specific_modules = [m for m in classified_modules if not m.is_generic]

        # Calculate statistics
        avg_generic_imported = (
            sum(m.imported_by_count for m in generic_modules) / len(generic_modules)
            if generic_modules else 0
        )
        avg_specific_imported = (
            sum(m.imported_by_count for m in specific_modules) / len(specific_modules)
            if specific_modules else 0
        )

        # Group by category
        by_category: Dict[str, List[ClassifiedModule]] = {}
        for module in classified_modules:
            cat = module.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(module)

        result = ClassificationResult(
            project_path=project_path,
            total_modules=len(classified_modules),
            generic_count=len(generic_modules),
            specific_count=len(specific_modules),
            generic_modules=sorted(generic_modules, key=lambda m: m.imported_by_count, reverse=True),
            specific_modules=sorted(specific_modules, key=lambda m: m.imported_by_count, reverse=True),
            by_category=by_category,
            avg_generic_imported_by=avg_generic_imported,
            avg_specific_imported_by=avg_specific_imported,
        )

        logger.info(
            f"Classification complete: {result.generic_count} generic, "
            f"{result.specific_count} specific modules"
        )

        return result

    def _extract_modules_from_graph(
        self,
        dependency_graph: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract module information from dependency graph."""
        modules = {}

        # Try to get modules from graph structure
        if "modules" in dependency_graph:
            for module in dependency_graph["modules"]:
                name = module.get("name", "")
                if name:
                    modules[name] = {
                        "path": module.get("path", ""),
                        "imported_by": module.get("imported_by_count", 0),
                        "imports": module.get("imports_count", 0),
                        "afferent": module.get("afferent_coupling", 0),
                        "efferent": module.get("efferent_coupling", 0),
                    }

        # Also check hub_modules from metrics
        if "metrics" in dependency_graph:
            metrics = dependency_graph["metrics"]
            hub_modules = metrics.get("hub_modules", [])
            for hub in hub_modules:
                if hub not in modules:
                    modules[hub] = {
                        "path": "",
                        "imported_by": metrics.get("avg_imports", 5) * 2,  # Estimate
                        "imports": 0,
                        "is_hub": True,
                    }
                else:
                    modules[hub]["is_hub"] = True

        return modules

    def _classify_single_module(
        self,
        name: str,
        module_info: Dict[str, Any],
        hub_threshold: float,
        avg_imported_by: float
    ) -> ClassifiedModule:
        """Classify a single module."""
        path = module_info.get("path", "")
        imported_by = module_info.get("imported_by", 0)
        imports = module_info.get("imports", 0)
        is_hub = module_info.get("is_hub", False)

        # Score components
        scores: Dict[ModuleCategory, float] = {cat: 0.0 for cat in ModuleCategory}
        reasons: List[str] = []
        matched_patterns: List[str] = []

        # 1. Check name patterns
        for category, patterns in CATEGORY_PATTERNS.items():
            for pattern in patterns.get("name_patterns", []):
                if re.search(pattern, name):
                    scores[category] += 0.3
                    matched_patterns.append(f"name:{pattern}")

        # 2. Check path patterns
        for category, patterns in CATEGORY_PATTERNS.items():
            for pattern in patterns.get("path_patterns", []):
                if re.search(pattern, path):
                    scores[category] += 0.2
                    matched_patterns.append(f"path:{pattern}")

        # 3. Hub/high-connectivity bonus
        if is_hub or imported_by > hub_threshold:
            # More likely to be generic
            scores[ModuleCategory.FOUNDATION_TECHNICAL] += 0.2
            reasons.append(f"Hub module (imported_by={imported_by} > threshold={hub_threshold:.1f})")

        # 4. High imported_by count bonus
        if imported_by >= MIN_IMPORTED_BY_FOR_GENERIC:
            generic_bonus = min(0.3, (imported_by - MIN_IMPORTED_BY_FOR_GENERIC) * 0.05)
            for cat in [ModuleCategory.FOUNDATION_TECHNICAL, ModuleCategory.FOUNDATION_USER,
                       ModuleCategory.FOUNDATION_UI, ModuleCategory.FOUNDATION_INTEGRATION]:
                scores[cat] += generic_bonus
            reasons.append(f"High reuse (imported_by={imported_by})")

        # Determine best category
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # If no pattern matches, classify by connectivity
        if best_score < 0.1:
            if imported_by >= MIN_IMPORTED_BY_FOR_GENERIC:
                best_category = ModuleCategory.FOUNDATION_TECHNICAL
                best_score = 0.5
                reasons.append("High connectivity without pattern match")
            else:
                best_category = ModuleCategory.BUSINESS
                best_score = 0.7
                reasons.append("Low connectivity, assumed business module")

        # Determine if generic (foundation) or specific (business)
        is_generic = best_category != ModuleCategory.BUSINESS and best_category != ModuleCategory.UNKNOWN

        # Calculate confidence
        confidence = min(1.0, best_score + 0.3)  # Base confidence
        if len(matched_patterns) > 2:
            confidence = min(1.0, confidence + 0.1)

        return ClassifiedModule(
            name=name,
            path=path,
            category=best_category,
            is_generic=is_generic,
            confidence=confidence,
            reasons=reasons,
            imported_by_count=imported_by,
            imports_count=imports,
            afferent_coupling=module_info.get("afferent", 0),
            efferent_coupling=module_info.get("efferent", 0),
            matched_patterns=matched_patterns,
        )

    def classify_for_epic_generation(
        self,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Prepare classification results for epic generation.

        Returns a structure optimized for the backlog generation workflow:
        - Foundation epics (P0/P1)
        - Business epics (P2)
        - Dependencies between them
        """
        foundation_epics = []

        # Group foundation modules by category
        for category, modules in classification.by_category.items():
            if category == "business" or category == "unknown":
                continue

            if not modules:
                continue

            # Create a foundation epic for this category
            epic = {
                "type": category,
                "priority": "P0" if category in ["foundation_technical", "foundation_user"] else "P1",
                "name": self._epic_name_for_category(category),
                "description": self._epic_description_for_category(category),
                "modules": [
                    {
                        "name": m.name,
                        "path": m.path,
                        "imported_by": m.imported_by_count,
                        "confidence": m.confidence,
                    }
                    for m in sorted(modules, key=lambda x: x.imported_by_count, reverse=True)
                ],
                "estimated_complexity": self._estimate_complexity(modules),
            }
            foundation_epics.append(epic)

        # Business modules become their own epics
        business_epics = []
        business_modules = classification.by_category.get("business", [])

        # Group business modules by domain (using path)
        domains: Dict[str, List[ClassifiedModule]] = {}
        for module in business_modules:
            domain = self._extract_domain_from_path(module.path)
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(module)

        for domain, modules in domains.items():
            if len(modules) < 2:
                continue  # Skip tiny domains

            epic = {
                "type": "business",
                "priority": "P2",
                "name": f"{domain} Domain",
                "description": f"Business logic for {domain}",
                "modules": [
                    {
                        "name": m.name,
                        "path": m.path,
                        "confidence": m.confidence,
                    }
                    for m in modules
                ],
                "estimated_complexity": self._estimate_complexity(modules),
                "dependencies": self._find_foundation_dependencies(modules, classification),
            }
            business_epics.append(epic)

        return {
            "foundation_epics": sorted(foundation_epics, key=lambda e: e["priority"]),
            "business_epics": business_epics,
            "summary": {
                "total_foundation_modules": classification.generic_count,
                "total_business_modules": classification.specific_count,
                "foundation_epic_count": len(foundation_epics),
                "business_epic_count": len(business_epics),
            }
        }

    def _epic_name_for_category(self, category: str) -> str:
        """Generate epic name for a category."""
        names = {
            "foundation_technical": "Technical Foundation",
            "foundation_user": "User Management & Security",
            "foundation_ui": "UI Components & Layouts",
            "foundation_integration": "External Integrations",
        }
        return names.get(category, category.replace("_", " ").title())

    def _epic_description_for_category(self, category: str) -> str:
        """Generate epic description for a category."""
        descriptions = {
            "foundation_technical": "Core technical infrastructure: logging, caching, database access, utilities",
            "foundation_user": "Authentication, authorization, session management, user profiles",
            "foundation_ui": "Shared UI components, layouts, templates, navigation",
            "foundation_integration": "External API clients, service connectors, adapters",
        }
        return descriptions.get(category, f"Foundation modules for {category}")

    def _estimate_complexity(self, modules: List[ClassifiedModule]) -> str:
        """Estimate complexity based on module count and connectivity."""
        total = len(modules)
        avg_coupling = sum(m.imported_by_count + m.imports_count for m in modules) / max(total, 1)

        if total > 20 or avg_coupling > 10:
            return "HIGH"
        elif total > 10 or avg_coupling > 5:
            return "MEDIUM"
        else:
            return "LOW"

    def _extract_domain_from_path(self, path: str) -> str:
        """Extract domain name from file path."""
        # Common patterns: /Domain/Module, /Modules/Domain, /Features/Domain
        parts = path.replace("\\", "/").split("/")

        # Skip common prefixes
        skip = {"src", "app", "lib", "modules", "features", "domain", "domains"}

        for part in parts:
            if part.lower() not in skip and part and not part.startswith("."):
                return part

        return "Core"

    def _find_foundation_dependencies(
        self,
        business_modules: List[ClassifiedModule],
        classification: ClassificationResult
    ) -> List[str]:
        """Find which foundation categories a business domain depends on."""
        # This would require the full import graph to implement properly
        # For now, return a placeholder
        return ["foundation_technical", "foundation_user"]


# Singleton instance
_classifier_service: Optional[GenericModuleClassifierService] = None


def get_generic_module_classifier_service() -> GenericModuleClassifierService:
    """Get or create the singleton classifier service."""
    global _classifier_service
    if _classifier_service is None:
        _classifier_service = GenericModuleClassifierService()
    return _classifier_service
