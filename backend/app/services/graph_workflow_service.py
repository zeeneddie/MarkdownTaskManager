"""
Graph Workflow Service - Week 88

Integrates Graph Persistence and CodeWiki into workflow pipelines:

NEW_FEATURE & MAINTENANCE: graph_impact_analysis()
- Analyze impact of proposed changes
- Identify affected modules and files
- Risk assessment based on coupling

BUG: graph_dependency_check()
- Check dependencies of buggy component
- Find related entities for root cause
- Impact radius for bug fixes

QUALITY_AUDIT & QUALITY_IMPROVEMENT: graph_coupling_metrics()
- Module coupling analysis
- Circular dependency detection
- Refactoring recommendations

TESTING: graph_test_coverage_map()
- Map tests to code entities
- Identify untested high-impact code
- Suggest test priorities

ENHANCEMENT: graph_enhancement_scope()
- Scope analysis for feature enhancements
- Dependency impact for changes
- Risk assessment

CodeWiki Integration:
- Auto-documentation after graph sync
- Agent context enrichment
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.graph_persistence_service import GraphPersistenceService
from app.services.codewiki_service import CodeWikiService

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Supported workflow types for graph integration."""
    GREEN_PAPER = "GREEN_PAPER"
    BROWN_PAPER = "BROWN_PAPER"
    NEW_FEATURE = "NEW_FEATURE"
    BUG = "BUG"
    MAINTENANCE = "MAINTENANCE"
    MIGRATION = "MIGRATION"
    QUALITY_AUDIT = "QUALITY_AUDIT"
    QUALITY_IMPROVEMENT = "QUALITY_IMPROVEMENT"
    TESTING = "TESTING"
    ENHANCEMENT = "ENHANCEMENT"
    PROJECT_DEFINITION = "PROJECT_DEFINITION"


class GraphWorkflowService:
    """
    Service for integrating Graph Persistence into workflow pipelines.

    Provides graph-aware tools for each workflow type:
    - Impact analysis for change planning
    - Dependency checks for debugging
    - Coupling metrics for quality
    - Test coverage mapping
    - Enhancement scoping
    """

    def __init__(self, db: AsyncSession):
        """Initialize with async database session."""
        self.db = db
        self._graph_service: Optional[GraphPersistenceService] = None
        self._codewiki_service: Optional[CodeWikiService] = None

    @property
    def graph(self) -> GraphPersistenceService:
        """Lazy-load Graph Persistence service."""
        if self._graph_service is None:
            self._graph_service = GraphPersistenceService(self.db)
        return self._graph_service

    @property
    def codewiki(self) -> CodeWikiService:
        """Lazy-load CodeWiki service."""
        if self._codewiki_service is None:
            # CodeWiki uses sync session, need adapter
            self._codewiki_service = CodeWikiService(self.db)
        return self._codewiki_service

    # =========================================================================
    # SECTION 1: Impact Analysis (NEW_FEATURE, MAINTENANCE)
    # =========================================================================

    async def graph_impact_analysis(
        self,
        project_id: int,
        changes: List[str],
        workflow_type: str = "NEW_FEATURE",
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze impact of proposed changes on the codebase.

        Used by NEW_FEATURE and MAINTENANCE workflows to understand
        the blast radius of changes before implementation.

        Args:
            project_id: Project ID
            changes: List of file paths or entity names to change
            workflow_type: NEW_FEATURE or MAINTENANCE
            max_depth: Maximum depth for transitive impact

        Returns:
            ImpactReport with affected entities, files, and risk score
        """
        logger.info(f"Running impact analysis for {workflow_type}: {len(changes)} changes")

        result = {
            "workflow_type": workflow_type,
            "project_id": project_id,
            "changes_analyzed": len(changes),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "affected_entities": [],
            "affected_files": set(),
            "impact_summary": {
                "total_affected": 0,
                "direct_impact": 0,
                "transitive_impact": 0,
                "max_depth_reached": 0,
            },
            "risk_assessment": {
                "level": "low",
                "score": 0.0,
                "factors": [],
            },
            "recommendations": [],
        }

        try:
            # Get statistics first
            stats = await self.graph.get_project_statistics(project_id)
            if stats.get("total_entities", 0) == 0:
                result["warning"] = "Graph not synced - run sync_project_graph first"
                return result

            # Search for each change target
            all_affected = []
            all_files = set()

            for change in changes:
                # Search for entity by name
                entities = await self.graph.search_entities(
                    project_id=project_id,
                    query=change,
                    limit=5
                )

                for entity in entities:
                    entity_id = UUID(entity["id"])

                    # Get impact analysis
                    impact = await self.graph.get_impact_analysis(
                        project_id=project_id,
                        entity_id=entity_id,
                        max_depth=max_depth
                    )

                    # Collect affected
                    for affected in impact.get("affected_entities", []):
                        affected["source_change"] = change
                        all_affected.append(affected)

                    all_files.update(impact.get("affected_files", []))

                    result["impact_summary"]["max_depth_reached"] = max(
                        result["impact_summary"]["max_depth_reached"],
                        impact.get("depth", 0)
                    )

            # Deduplicate and summarize
            unique_affected = {a["id"]: a for a in all_affected}
            result["affected_entities"] = list(unique_affected.values())
            result["affected_files"] = list(all_files)

            # Count by depth
            direct = len([a for a in unique_affected.values() if a.get("depth", 0) == 1])
            transitive = len(unique_affected) - direct

            result["impact_summary"]["total_affected"] = len(unique_affected)
            result["impact_summary"]["direct_impact"] = direct
            result["impact_summary"]["transitive_impact"] = transitive

            # Risk assessment
            result["risk_assessment"] = self._calculate_impact_risk(
                total_affected=len(unique_affected),
                affected_files=len(all_files),
                max_depth=result["impact_summary"]["max_depth_reached"],
                project_total=stats.get("total_entities", 1)
            )

            # Generate recommendations
            result["recommendations"] = self._generate_impact_recommendations(
                result["risk_assessment"],
                result["impact_summary"],
                workflow_type
            )

            logger.info(
                f"Impact analysis complete: {len(unique_affected)} entities, "
                f"risk={result['risk_assessment']['level']}"
            )

        except Exception as e:
            logger.error(f"Impact analysis failed: {e}")
            result["error"] = str(e)

        return result

    def _calculate_impact_risk(
        self,
        total_affected: int,
        affected_files: int,
        max_depth: int,
        project_total: int
    ) -> Dict[str, Any]:
        """Calculate risk score based on impact metrics."""
        factors = []

        # Factor 1: Percentage of codebase affected
        affected_pct = (total_affected / project_total) * 100 if project_total > 0 else 0
        if affected_pct > 20:
            factors.append(f"High blast radius: {affected_pct:.1f}% of codebase affected")
        elif affected_pct > 10:
            factors.append(f"Moderate blast radius: {affected_pct:.1f}% of codebase affected")

        # Factor 2: Depth of impact
        if max_depth >= 4:
            factors.append(f"Deep dependency chain: {max_depth} levels deep")

        # Factor 3: File spread
        if affected_files > 20:
            factors.append(f"Wide file spread: {affected_files} files affected")

        # Calculate score (0-100)
        score = min(100, (
            (affected_pct * 2) +
            (max_depth * 10) +
            (affected_files * 0.5)
        ))

        # Determine level
        if score >= 70:
            level = "critical"
        elif score >= 50:
            level = "high"
        elif score >= 25:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": round(score, 1),
            "factors": factors,
            "affected_percentage": round(affected_pct, 1),
        }

    def _generate_impact_recommendations(
        self,
        risk: Dict[str, Any],
        summary: Dict[str, Any],
        workflow_type: str
    ) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []

        if risk["level"] in ("critical", "high"):
            recommendations.append("Consider breaking changes into smaller PRs")
            recommendations.append("Add comprehensive test coverage before changes")

            if workflow_type == "NEW_FEATURE":
                recommendations.append("Review architecture - feature may need different approach")
            elif workflow_type == "MAINTENANCE":
                recommendations.append("Create rollback plan before deployment")

        if summary["transitive_impact"] > summary["direct_impact"] * 2:
            recommendations.append("High transitive impact - verify all affected components")

        if summary["max_depth_reached"] >= 4:
            recommendations.append("Consider refactoring to reduce dependency depth")

        if risk["affected_percentage"] > 15:
            recommendations.append("Schedule change during low-traffic period")

        return recommendations

    # =========================================================================
    # SECTION 2: Dependency Check (BUG workflow)
    # =========================================================================

    async def graph_dependency_check(
        self,
        project_id: int,
        entity_name: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check dependencies for bug investigation.

        Used by BUG workflow to understand what a buggy component
        depends on and what depends on it.

        Args:
            project_id: Project ID
            entity_name: Name of buggy entity (class, function, etc.)
            file_path: Optional file path to narrow search

        Returns:
            DependencyReport with upstream/downstream dependencies
        """
        logger.info(f"Running dependency check for BUG: {entity_name}")

        result = {
            "workflow_type": "BUG",
            "project_id": project_id,
            "entity_name": entity_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity_found": False,
            "upstream_dependencies": [],  # What this entity depends on
            "downstream_dependents": [],  # What depends on this entity
            "circular_dependencies": [],
            "investigation_hints": [],
        }

        try:
            # Search for the entity
            entities = await self.graph.search_entities(
                project_id=project_id,
                query=entity_name,
                limit=10
            )

            if file_path:
                entities = [e for e in entities if e.get("file_path") == file_path]

            if not entities:
                result["error"] = f"Entity '{entity_name}' not found in graph"
                return result

            # Use first match (most relevant)
            entity = entities[0]
            entity_id = UUID(entity["id"])
            result["entity_found"] = True
            result["entity"] = entity

            # Get upstream dependencies (what this entity uses)
            deps = await self.graph.get_direct_dependencies(
                project_id=project_id,
                entity_id=entity_id
            )
            result["upstream_dependencies"] = deps.get("dependencies", [])

            # Get downstream dependents (what uses this entity)
            dependents = await self.graph.get_dependents(
                project_id=project_id,
                entity_id=entity_id
            )
            result["downstream_dependents"] = dependents.get("dependents", [])

            # Check for circular dependencies in this area
            circular = await self.graph.detect_circular_dependencies(project_id)
            relevant_cycles = [
                c for c in circular.get("cycles", [])
                if any(e.get("name") == entity_name for e in c.get("entities", []))
            ]
            result["circular_dependencies"] = relevant_cycles

            # Generate investigation hints
            result["investigation_hints"] = self._generate_bug_hints(
                entity=entity,
                upstream=result["upstream_dependencies"],
                downstream=result["downstream_dependents"],
                circular=relevant_cycles
            )

            logger.info(
                f"Dependency check complete: {len(result['upstream_dependencies'])} upstream, "
                f"{len(result['downstream_dependents'])} downstream"
            )

        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            result["error"] = str(e)

        return result

    def _generate_bug_hints(
        self,
        entity: Dict[str, Any],
        upstream: List[Dict],
        downstream: List[Dict],
        circular: List[Dict]
    ) -> List[str]:
        """Generate investigation hints for bug fixing."""
        hints = []

        # Check for circular dependencies
        if circular:
            hints.append(
                f"CIRCULAR DEPENDENCY DETECTED: Entity is part of {len(circular)} cycle(s). "
                "This may cause initialization or state issues."
            )

        # Check upstream dependencies
        if len(upstream) > 10:
            hints.append(
                f"HIGH DEPENDENCY COUNT: Entity depends on {len(upstream)} other entities. "
                "Bug may be caused by one of these dependencies."
            )

        # Check if highly depended upon
        if len(downstream) > 10:
            hints.append(
                f"HIGH DEPENDENTS: {len(downstream)} entities depend on this. "
                "Bug may have wide impact - consider regression testing."
            )

        # Type-specific hints
        entity_type = entity.get("type", "unknown")
        if entity_type == "class":
            hints.append("Check class initialization (__init__) and state management")
        elif entity_type == "function":
            hints.append("Check parameter handling and return value edge cases")

        # File location hint
        if entity.get("file_path"):
            hints.append(f"Source file: {entity['file_path']}")
            if entity.get("start_line"):
                hints.append(f"Start line: {entity['start_line']}")

        return hints

    # =========================================================================
    # SECTION 3: Coupling Metrics (QUALITY_AUDIT, QUALITY_IMPROVEMENT)
    # =========================================================================

    async def graph_coupling_metrics(
        self,
        project_id: int,
        coupling_threshold: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze module coupling for quality assessment.

        Used by QUALITY_AUDIT and QUALITY_IMPROVEMENT workflows
        to identify tightly coupled modules that need refactoring.

        Args:
            project_id: Project ID
            coupling_threshold: Threshold for "high coupling" alert

        Returns:
            CouplingMetrics with module coupling analysis
        """
        logger.info(f"Running coupling metrics for QUALITY_AUDIT: project {project_id}")

        result = {
            "workflow_type": "QUALITY_AUDIT",
            "project_id": project_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "coupling_summary": {},
            "high_coupling_modules": [],
            "circular_dependencies": [],
            "quality_score": 100,  # Start perfect, deduct for issues
            "improvement_suggestions": [],
        }

        try:
            # Get module coupling
            coupling = await self.graph.get_module_coupling(
                project_id=project_id,
                sort_by="coupling_count"
            )

            result["coupling_summary"] = {
                "total_modules": coupling.get("total_modules", 0),
                "total_connections": coupling.get("total_connections", 0),
                "total_coupling_strength": coupling.get("total_coupling_strength", 0),
                "average_coupling": coupling.get("average_coupling", 0),
            }

            # Get highly coupled modules
            high_coupled = await self.graph.get_highly_coupled_modules(
                project_id=project_id,
                threshold=coupling_threshold
            )
            result["high_coupling_modules"] = high_coupled

            # Check for circular dependencies
            circular = await self.graph.detect_circular_dependencies(project_id)
            result["circular_dependencies"] = circular.get("cycles", [])

            # Calculate quality score
            quality_score = 100

            # Deduct for high coupling
            high_coupling_count = len(high_coupled)
            quality_score -= min(30, high_coupling_count * 5)

            # Deduct for circular dependencies
            circular_count = circular.get("cycles_found", 0)
            quality_score -= min(40, circular_count * 10)

            # Deduct for high average coupling
            avg_coupling = coupling.get("average_coupling", 0)
            if avg_coupling > 15:
                quality_score -= 20
            elif avg_coupling > 10:
                quality_score -= 10

            result["quality_score"] = max(0, quality_score)

            # Generate improvement suggestions
            result["improvement_suggestions"] = self._generate_coupling_suggestions(
                high_coupled=high_coupled,
                circular=result["circular_dependencies"],
                avg_coupling=avg_coupling,
                quality_score=result["quality_score"]
            )

            logger.info(
                f"Coupling metrics complete: score={result['quality_score']}, "
                f"{high_coupling_count} high-coupling modules"
            )

        except Exception as e:
            logger.error(f"Coupling metrics failed: {e}")
            result["error"] = str(e)

        return result

    def _generate_coupling_suggestions(
        self,
        high_coupled: List[Dict],
        circular: List[Dict],
        avg_coupling: float,
        quality_score: int
    ) -> List[str]:
        """Generate improvement suggestions for coupling issues."""
        suggestions = []

        # Critical issues first
        if circular:
            suggestions.append(
                f"CRITICAL: Remove {len(circular)} circular dependency cycle(s). "
                "These prevent clean module boundaries and make testing difficult."
            )
            for i, cycle in enumerate(circular[:3]):  # Show first 3
                entities = [e.get("name", "?") for e in cycle.get("entities", [])]
                suggestions.append(f"  Cycle {i+1}: {' → '.join(entities)}")

        # High coupling modules
        if high_coupled:
            suggestions.append(
                f"REFACTOR: {len(high_coupled)} module pairs have high coupling. Consider:"
            )
            for coupling in high_coupled[:5]:  # Top 5
                source = coupling.get("source_module", "?")
                target = coupling.get("target_module", "?")
                count = coupling.get("coupling_count", 0)
                suggestions.append(
                    f"  - {source} ↔ {target}: {count} connections - "
                    "extract shared interface or merge modules"
                )

        # General suggestions based on average
        if avg_coupling > 15:
            suggestions.append(
                "HIGH AVERAGE COUPLING: Consider applying SOLID principles and "
                "introducing abstraction layers between modules."
            )
        elif avg_coupling > 10:
            suggestions.append(
                "MODERATE COUPLING: Look for opportunities to introduce "
                "dependency injection or facade patterns."
            )

        # Overall quality guidance
        if quality_score < 50:
            suggestions.append(
                "URGENT: Architecture needs significant restructuring. "
                "Prioritize breaking circular dependencies."
            )
        elif quality_score < 70:
            suggestions.append(
                "ATTENTION: Plan incremental refactoring to reduce coupling. "
                "Focus on modules with most connections first."
            )

        return suggestions

    # =========================================================================
    # SECTION 4: Test Coverage Map (TESTING workflow)
    # =========================================================================

    async def graph_test_coverage_map(
        self,
        project_id: int,
        test_file_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Map test files to code entities for coverage analysis.

        Used by TESTING workflow to identify untested code
        and suggest test priorities based on code importance.

        Args:
            project_id: Project ID
            test_file_patterns: Patterns to identify test files

        Returns:
            CoverageMap with test-to-code mapping and priorities
        """
        logger.info(f"Running test coverage map for TESTING: project {project_id}")

        if test_file_patterns is None:
            test_file_patterns = ["test_", "_test.py", ".test.", "spec."]

        result = {
            "workflow_type": "TESTING",
            "project_id": project_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_files": [],
            "tested_entities": [],
            "untested_entities": [],
            "coverage_summary": {
                "total_entities": 0,
                "tested_count": 0,
                "untested_count": 0,
                "coverage_percentage": 0.0,
            },
            "test_priorities": [],
        }

        try:
            # Get project statistics
            stats = await self.graph.get_project_statistics(project_id)
            total_entities = stats.get("total_entities", 0)

            if total_entities == 0:
                result["warning"] = "Graph not synced - run sync_project_graph first"
                return result

            # Search for test files/entities
            test_entities = []
            for pattern in test_file_patterns:
                entities = await self.graph.search_entities(
                    project_id=project_id,
                    query=pattern,
                    limit=100
                )
                test_entities.extend(entities)

            result["test_files"] = [
                e["file_path"] for e in test_entities
                if e.get("file_path")
            ]

            # Get top referenced entities (most important to test)
            top_referenced = stats.get("top_referenced_entities", [])

            # Identify tested vs untested among top referenced
            test_file_paths = set(result["test_files"])
            tested_names = set()

            # Simple heuristic: if entity name appears in test file, consider tested
            for test_entity in test_entities:
                if test_entity.get("name"):
                    # Extract what's being tested (e.g., test_UserService -> UserService)
                    name = test_entity["name"]
                    for prefix in ["test_", "Test"]:
                        if name.startswith(prefix):
                            tested_names.add(name[len(prefix):])
                    for suffix in ["Test", "_test", "Spec"]:
                        if name.endswith(suffix):
                            tested_names.add(name[:-len(suffix)])

            # Categorize entities
            result["tested_entities"] = [
                e for e in top_referenced
                if e.get("name") in tested_names
            ]
            result["untested_entities"] = [
                e for e in top_referenced
                if e.get("name") not in tested_names
            ]

            # Coverage summary
            tested_count = len(result["tested_entities"])
            untested_count = len(result["untested_entities"])
            total_checked = tested_count + untested_count

            result["coverage_summary"] = {
                "total_entities": total_entities,
                "top_referenced_checked": total_checked,
                "tested_count": tested_count,
                "untested_count": untested_count,
                "coverage_percentage": round(
                    (tested_count / total_checked * 100) if total_checked > 0 else 0,
                    1
                ),
            }

            # Generate test priorities (untested + high references)
            result["test_priorities"] = self._calculate_test_priorities(
                untested=result["untested_entities"],
                all_entities=top_referenced
            )

            logger.info(
                f"Test coverage map complete: {result['coverage_summary']['coverage_percentage']}% "
                f"of top entities covered"
            )

        except Exception as e:
            logger.error(f"Test coverage map failed: {e}")
            result["error"] = str(e)

        return result

    def _calculate_test_priorities(
        self,
        untested: List[Dict],
        all_entities: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Calculate test priorities based on importance and coverage."""
        priorities = []

        for entity in untested[:10]:  # Top 10 priorities
            priority_score = entity.get("references", 0) * 10

            reason = []
            if entity.get("references", 0) > 5:
                reason.append(f"High references ({entity['references']})")
            if entity.get("type") == "class":
                reason.append("Core class")
                priority_score += 20

            priorities.append({
                "entity_name": entity.get("name"),
                "entity_type": entity.get("type"),
                "priority_score": priority_score,
                "reason": ", ".join(reason) if reason else "Untested code",
                "file_path": entity.get("file_path"),
            })

        return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)

    # =========================================================================
    # SECTION 5: Enhancement Scope (ENHANCEMENT workflow)
    # =========================================================================

    async def graph_enhancement_scope(
        self,
        project_id: int,
        feature_name: str,
        target_entities: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze scope of a feature enhancement.

        Used by ENHANCEMENT workflow to understand the scope
        and impact of enhancing existing functionality.

        Args:
            project_id: Project ID
            feature_name: Name/description of enhancement
            target_entities: Specific entities to enhance (optional)

        Returns:
            ScopeReport with affected scope and risk assessment
        """
        logger.info(f"Running enhancement scope for: {feature_name}")

        result = {
            "workflow_type": "ENHANCEMENT",
            "project_id": project_id,
            "feature_name": feature_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scope_analysis": {
                "entities_in_scope": [],
                "files_affected": [],
                "modules_affected": [],
            },
            "dependency_analysis": {
                "upstream_count": 0,
                "downstream_count": 0,
                "cross_module_dependencies": [],
            },
            "risk_assessment": {
                "level": "low",
                "score": 0,
                "factors": [],
            },
            "enhancement_plan": [],
        }

        try:
            # Search for related entities
            search_terms = target_entities if target_entities else [feature_name]
            all_entities = []
            all_files = set()
            all_modules = set()

            for term in search_terms:
                entities = await self.graph.search_entities(
                    project_id=project_id,
                    query=term,
                    limit=20
                )
                all_entities.extend(entities)

                for entity in entities:
                    if entity.get("file_path"):
                        all_files.add(entity["file_path"])
                        # Extract module from path
                        parts = entity["file_path"].split("/")
                        if len(parts) > 1:
                            all_modules.add(parts[0])

            # Deduplicate entities
            unique_entities = {e["id"]: e for e in all_entities}
            result["scope_analysis"]["entities_in_scope"] = list(unique_entities.values())
            result["scope_analysis"]["files_affected"] = list(all_files)
            result["scope_analysis"]["modules_affected"] = list(all_modules)

            # Analyze dependencies for each entity
            total_upstream = 0
            total_downstream = 0
            cross_module = []

            for entity in list(unique_entities.values())[:10]:  # Limit analysis
                entity_id = UUID(entity["id"])

                deps = await self.graph.get_direct_dependencies(
                    project_id=project_id,
                    entity_id=entity_id
                )
                total_upstream += len(deps.get("dependencies", []))

                dependents = await self.graph.get_dependents(
                    project_id=project_id,
                    entity_id=entity_id
                )
                total_downstream += len(dependents.get("dependents", []))

                # Check for cross-module dependencies
                entity_module = entity.get("file_path", "").split("/")[0]
                for dep in deps.get("dependencies", []):
                    dep_module = dep.get("file_path", "").split("/")[0]
                    if dep_module and dep_module != entity_module:
                        cross_module.append({
                            "from": entity["name"],
                            "to": dep.get("name"),
                            "from_module": entity_module,
                            "to_module": dep_module,
                        })

            result["dependency_analysis"]["upstream_count"] = total_upstream
            result["dependency_analysis"]["downstream_count"] = total_downstream
            result["dependency_analysis"]["cross_module_dependencies"] = cross_module[:10]

            # Risk assessment
            result["risk_assessment"] = self._calculate_enhancement_risk(
                entities_count=len(unique_entities),
                files_count=len(all_files),
                modules_count=len(all_modules),
                downstream_count=total_downstream,
                cross_module_count=len(cross_module)
            )

            # Generate enhancement plan
            result["enhancement_plan"] = self._generate_enhancement_plan(
                scope=result["scope_analysis"],
                risk=result["risk_assessment"],
                feature_name=feature_name
            )

            logger.info(
                f"Enhancement scope complete: {len(unique_entities)} entities, "
                f"risk={result['risk_assessment']['level']}"
            )

        except Exception as e:
            logger.error(f"Enhancement scope failed: {e}")
            result["error"] = str(e)

        return result

    def _calculate_enhancement_risk(
        self,
        entities_count: int,
        files_count: int,
        modules_count: int,
        downstream_count: int,
        cross_module_count: int
    ) -> Dict[str, Any]:
        """Calculate risk for enhancement scope."""
        factors = []
        score = 0

        # Factor: Scope size
        if entities_count > 20:
            score += 30
            factors.append(f"Large scope: {entities_count} entities")
        elif entities_count > 10:
            score += 15
            factors.append(f"Moderate scope: {entities_count} entities")

        # Factor: Cross-module changes
        if modules_count > 3:
            score += 25
            factors.append(f"Multi-module change: {modules_count} modules affected")

        # Factor: Downstream dependents
        if downstream_count > 20:
            score += 30
            factors.append(f"High downstream impact: {downstream_count} dependents")
        elif downstream_count > 10:
            score += 15
            factors.append(f"Moderate downstream impact: {downstream_count} dependents")

        # Factor: Cross-module dependencies
        if cross_module_count > 5:
            score += 20
            factors.append(f"Cross-module dependencies: {cross_module_count}")

        # Determine level
        if score >= 60:
            level = "high"
        elif score >= 30:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": score,
            "factors": factors,
        }

    def _generate_enhancement_plan(
        self,
        scope: Dict[str, Any],
        risk: Dict[str, Any],
        feature_name: str
    ) -> List[Dict[str, Any]]:
        """Generate enhancement implementation plan."""
        plan = []
        step = 1

        # Step 1: Always start with tests
        plan.append({
            "step": step,
            "action": "Write Tests First",
            "description": "Create test cases for expected behavior before modifying code",
            "entities": scope["entities_in_scope"][:3],
            "priority": "high",
        })
        step += 1

        # Step 2: Based on risk level
        if risk["level"] == "high":
            plan.append({
                "step": step,
                "action": "Create Feature Branch",
                "description": "Work in isolated branch due to high risk",
                "priority": "high",
            })
            step += 1

            plan.append({
                "step": step,
                "action": "Implement Incrementally",
                "description": "Break enhancement into smaller PRs for safer rollout",
                "priority": "high",
            })
            step += 1

        # Step 3: Module-by-module approach if multi-module
        if len(scope["modules_affected"]) > 1:
            for module in scope["modules_affected"][:3]:
                plan.append({
                    "step": step,
                    "action": f"Update Module: {module}",
                    "description": f"Implement enhancement changes in {module}",
                    "priority": "medium",
                })
                step += 1

        # Step 4: Integration
        plan.append({
            "step": step,
            "action": "Integration Testing",
            "description": "Verify all modules work together after enhancement",
            "priority": "high",
        })

        return plan

    # =========================================================================
    # SECTION 6: CodeWiki Integration
    # =========================================================================

    async def sync_and_document(
        self,
        project_id: int,
        repo_path: str,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Sync project graph and generate CodeWiki documentation.

        Combines graph sync with auto-documentation for a complete
        project understanding update.

        Args:
            project_id: Project ID
            repo_path: Repository path
            languages: Languages to analyze

        Returns:
            Combined sync and documentation result
        """
        logger.info(f"Running sync and document for project {project_id}")

        result = {
            "project_id": project_id,
            "repo_path": repo_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "graph_sync": {},
            "codewiki_analysis": {},
        }

        try:
            # Step 1: Sync graph
            sync_result = await self.graph.sync_project_graph(
                project_id=project_id,
                repo_path=repo_path,
                languages=languages
            )
            result["graph_sync"] = sync_result

            # Step 2: Create CodeWiki analysis
            analysis = self.codewiki.create_analysis(
                project_id=project_id,
                repository_path=repo_path,
                branch="main"
            )

            # Step 3: Run CodeWiki analysis
            completed_analysis = await self.codewiki.run_analysis(analysis.id)

            result["codewiki_analysis"] = {
                "analysis_id": completed_analysis.id,
                "status": completed_analysis.status.value,
                "total_modules": completed_analysis.total_modules,
                "total_files": completed_analysis.total_files,
                "languages": completed_analysis.languages_detected,
            }

            logger.info(f"Sync and document complete for project {project_id}")

        except Exception as e:
            logger.error(f"Sync and document failed: {e}")
            result["error"] = str(e)

        return result

    async def get_workflow_context(
        self,
        project_id: int,
        workflow_type: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get graph and CodeWiki context for a workflow.

        Provides combined context from graph analysis and CodeWiki
        for enhanced workflow processing.

        Args:
            project_id: Project ID
            workflow_type: Type of workflow
            agent_name: Optional specific agent (felix, miguel, quinn, diana)

        Returns:
            Combined context for workflow
        """
        result = {
            "project_id": project_id,
            "workflow_type": workflow_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "graph_context": {},
            "codewiki_context": {},
        }

        try:
            # Graph context
            stats = await self.graph.get_project_statistics(project_id)
            result["graph_context"] = {
                "total_entities": stats.get("total_entities", 0),
                "total_relations": stats.get("total_relations", 0),
                "total_files": stats.get("total_files", 0),
                "top_referenced": stats.get("top_referenced_entities", [])[:5],
            }

            # Coupling info for quality workflows
            if workflow_type in ("QUALITY_AUDIT", "QUALITY_IMPROVEMENT"):
                coupling = await self.graph.get_module_coupling(project_id)
                result["graph_context"]["coupling"] = {
                    "total_modules": coupling.get("total_modules", 0),
                    "average_coupling": coupling.get("average_coupling", 0),
                }

            # CodeWiki context
            latest_analysis = self.codewiki.get_latest_analysis(project_id)
            if latest_analysis:
                result["codewiki_context"]["analysis_id"] = latest_analysis.id
                result["codewiki_context"]["overview"] = latest_analysis.overview_md

                # Agent-specific context
                if agent_name:
                    agent_ctx = self.codewiki.get_agent_context(
                        analysis_id=latest_analysis.id,
                        agent_name=agent_name
                    )
                    if agent_ctx:
                        result["codewiki_context"]["agent_context"] = {
                            "summary": agent_ctx.context_summary,
                            "type": agent_ctx.context_type,
                        }

        except Exception as e:
            logger.error(f"Get workflow context failed: {e}")
            result["error"] = str(e)

        return result


# =========================================================================
# Factory Function
# =========================================================================

def get_graph_workflow_service(db: AsyncSession) -> GraphWorkflowService:
    """Get graph workflow service instance."""
    return GraphWorkflowService(db)
