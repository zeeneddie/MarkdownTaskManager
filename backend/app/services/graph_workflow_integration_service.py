"""
Week 88: Graph Workflow Integration Service

Integrates graph-based code analysis into all 11 workflows.
Provides impact analysis, dependency checking, coupling metrics, and test coverage mapping.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.graph_workflow import (
    GraphAnalysisCache,
    WorkflowGraphIntegration,
    WORKFLOW_GRAPH_INTEGRATIONS,
    ANALYSIS_TYPES,
)

logger = logging.getLogger(__name__)


class GraphWorkflowIntegrationService:
    """
    Service for integrating graph analysis into workflows.

    Provides:
    - Impact analysis for code changes
    - Dependency checking for affected entities
    - Coupling/cohesion metrics for quality assessment
    - Test-to-source mapping for coverage analysis
    - Enhancement scope determination
    """

    # Cache TTL in hours per analysis type
    CACHE_TTL = {
        "impact_analysis": 1,
        "dependency_check": 2,
        "coupling_metrics": 24,
        "test_coverage_map": 12,
        "enhancement_scope": 1,
    }

    def __init__(self, db: Session):
        self.db = db

    # ==================== Impact Analysis ====================

    async def graph_impact_analysis(
        self,
        project_id: int,
        changes: List[str],
        workflow_type: str = None,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Analyze impact of code changes on the dependency graph.

        Used by: NEW_FEATURE, MAINTENANCE, QUALITY_IMPROVEMENT, ENHANCEMENT

        Args:
            project_id: Project ID
            changes: List of changed file paths or entity IDs
            workflow_type: Optional workflow type for tracking
            session_id: Optional workflow session ID

        Returns:
            Impact report with affected modules, ripple effects, risk score
        """
        start_time = datetime.utcnow()

        # Check cache first
        cache_key = f"impact:{','.join(sorted(changes[:5]))}"
        cached = self._get_cached_result(project_id, "impact_analysis", cache_key)
        if cached:
            return cached

        try:
            # Analyze impact via graph
            impact_result = await self._compute_impact_analysis(project_id, changes)

            # Cache result
            self._cache_result(
                project_id,
                "impact_analysis",
                cache_key,
                impact_result
            )

            # Track integration if workflow provided
            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "impact_analysis",
                    {"changes": changes},
                    impact_result,
                    start_time,
                )

            return impact_result

        except Exception as e:
            logger.error(f"Impact analysis failed: {e}")
            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "impact_analysis",
                    {"changes": changes},
                    None,
                    start_time,
                    error=str(e),
                )
            raise

    async def _compute_impact_analysis(
        self,
        project_id: int,
        changes: List[str],
    ) -> Dict[str, Any]:
        """Compute impact analysis using graph data."""
        # Get graph entities for changed files
        affected_entities = []
        ripple_effects = []

        for change in changes:
            # Find direct dependencies
            direct_deps = await self._find_dependencies(project_id, change, depth=1)
            affected_entities.extend(direct_deps)

            # Find indirect dependencies (ripple effect)
            indirect_deps = await self._find_dependencies(project_id, change, depth=3)
            ripple_effects.extend([d for d in indirect_deps if d not in direct_deps])

        # Calculate risk score based on impact breadth
        unique_affected = list(set(affected_entities))
        unique_ripple = list(set(ripple_effects))

        risk_score = self._calculate_risk_score(
            len(changes),
            len(unique_affected),
            len(unique_ripple),
        )

        return {
            "changes_count": len(changes),
            "directly_affected": unique_affected[:50],  # Limit for response size
            "directly_affected_count": len(unique_affected),
            "ripple_effects": unique_ripple[:50],
            "ripple_effects_count": len(unique_ripple),
            "risk_score": risk_score,
            "risk_level": self._risk_level(risk_score),
            "recommendations": self._impact_recommendations(risk_score, unique_affected),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Dependency Check ====================

    async def graph_dependency_check(
        self,
        project_id: int,
        entity_id: str,
        entity_type: str = "module",
        workflow_type: str = None,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Check dependencies for a specific entity.

        Used by: BUG, MIGRATION, NEW_FEATURE

        Args:
            project_id: Project ID
            entity_id: Entity identifier (file path, class name, etc.)
            entity_type: Type of entity (module, class, function, file)
            workflow_type: Optional workflow type
            session_id: Optional workflow session ID

        Returns:
            Dependency report with upstream/downstream deps, circular detection
        """
        start_time = datetime.utcnow()

        cache_key = f"deps:{entity_id}:{entity_type}"
        cached = self._get_cached_result(project_id, "dependency_check", cache_key)
        if cached:
            return cached

        try:
            result = await self._compute_dependency_check(project_id, entity_id, entity_type)

            self._cache_result(project_id, "dependency_check", cache_key, result)

            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "dependency_check",
                    {"entity_id": entity_id, "entity_type": entity_type},
                    result,
                    start_time,
                )

            return result

        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "dependency_check",
                    {"entity_id": entity_id, "entity_type": entity_type},
                    None,
                    start_time,
                    error=str(e),
                )
            raise

    async def _compute_dependency_check(
        self,
        project_id: int,
        entity_id: str,
        entity_type: str,
    ) -> Dict[str, Any]:
        """Compute dependency check using graph data."""
        # Find upstream dependencies (what this entity depends on)
        upstream = await self._find_dependencies(project_id, entity_id, direction="upstream")

        # Find downstream dependencies (what depends on this entity)
        downstream = await self._find_dependencies(project_id, entity_id, direction="downstream")

        # Check for circular dependencies
        circular = self._detect_circular_dependencies(entity_id, upstream, downstream)

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "upstream_dependencies": upstream[:100],
            "upstream_count": len(upstream),
            "downstream_dependencies": downstream[:100],
            "downstream_count": len(downstream),
            "has_circular_dependencies": len(circular) > 0,
            "circular_dependencies": circular[:10],
            "dependency_depth": self._calculate_dependency_depth(upstream),
            "fan_in": len(downstream),  # How many entities depend on this
            "fan_out": len(upstream),    # How many entities this depends on
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Coupling Metrics ====================

    async def graph_coupling_metrics(
        self,
        project_id: int,
        module_filter: str = None,
        workflow_type: str = None,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Calculate module coupling and cohesion metrics.

        Used by: QUALITY_AUDIT, QUALITY_IMPROVEMENT, MIGRATION, MAINTENANCE

        Args:
            project_id: Project ID
            module_filter: Optional filter for specific module
            workflow_type: Optional workflow type
            session_id: Optional workflow session ID

        Returns:
            Coupling metrics with instability, abstractness, distance from main sequence
        """
        start_time = datetime.utcnow()

        cache_key = f"coupling:{module_filter or 'all'}"
        cached = self._get_cached_result(project_id, "coupling_metrics", cache_key)
        if cached:
            return cached

        try:
            result = await self._compute_coupling_metrics(project_id, module_filter)

            self._cache_result(project_id, "coupling_metrics", cache_key, result)

            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "coupling_metrics",
                    {"module_filter": module_filter},
                    result,
                    start_time,
                )

            return result

        except Exception as e:
            logger.error(f"Coupling metrics failed: {e}")
            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "coupling_metrics",
                    {"module_filter": module_filter},
                    None,
                    start_time,
                    error=str(e),
                )
            raise

    async def _compute_coupling_metrics(
        self,
        project_id: int,
        module_filter: str = None,
    ) -> Dict[str, Any]:
        """Compute coupling and cohesion metrics."""
        modules = await self._get_project_modules(project_id, module_filter)

        module_metrics = []
        for module in modules:
            fan_in = await self._count_incoming_deps(project_id, module)
            fan_out = await self._count_outgoing_deps(project_id, module)

            # Instability = Fan-out / (Fan-in + Fan-out)
            total = fan_in + fan_out
            instability = fan_out / total if total > 0 else 0.5

            # Abstractness (placeholder - would need actual abstract class data)
            abstractness = 0.3  # Default

            # Distance from main sequence: |A + I - 1|
            distance = abs(abstractness + instability - 1)

            module_metrics.append({
                "module": module,
                "fan_in": fan_in,
                "fan_out": fan_out,
                "instability": round(instability, 3),
                "abstractness": round(abstractness, 3),
                "distance_from_main_sequence": round(distance, 3),
                "coupling_score": self._coupling_score(fan_in, fan_out),
            })

        # Sort by coupling score (highest first - most problematic)
        module_metrics.sort(key=lambda x: x["coupling_score"], reverse=True)

        # Calculate project-level metrics
        avg_instability = sum(m["instability"] for m in module_metrics) / len(module_metrics) if module_metrics else 0
        avg_coupling = sum(m["coupling_score"] for m in module_metrics) / len(module_metrics) if module_metrics else 0

        return {
            "project_id": project_id,
            "total_modules": len(module_metrics),
            "average_instability": round(avg_instability, 3),
            "average_coupling_score": round(avg_coupling, 3),
            "highly_coupled_modules": [m for m in module_metrics if m["coupling_score"] > 0.7][:10],
            "stable_modules": [m for m in module_metrics if m["instability"] < 0.3][:10],
            "unstable_modules": [m for m in module_metrics if m["instability"] > 0.7][:10],
            "module_metrics": module_metrics[:50],
            "recommendations": self._coupling_recommendations(module_metrics),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Test Coverage Map ====================

    async def graph_test_coverage_map(
        self,
        project_id: int,
        source_filter: str = None,
        workflow_type: str = None,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Map test files to source files via graph analysis.

        Used by: TESTING, BUG

        Args:
            project_id: Project ID
            source_filter: Optional filter for specific source path
            workflow_type: Optional workflow type
            session_id: Optional workflow session ID

        Returns:
            Coverage map with test-to-source mappings, gaps, recommendations
        """
        start_time = datetime.utcnow()

        cache_key = f"coverage:{source_filter or 'all'}"
        cached = self._get_cached_result(project_id, "test_coverage_map", cache_key)
        if cached:
            return cached

        try:
            result = await self._compute_test_coverage_map(project_id, source_filter)

            self._cache_result(project_id, "test_coverage_map", cache_key, result)

            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "test_coverage_map",
                    {"source_filter": source_filter},
                    result,
                    start_time,
                )

            return result

        except Exception as e:
            logger.error(f"Test coverage map failed: {e}")
            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "test_coverage_map",
                    {"source_filter": source_filter},
                    None,
                    start_time,
                    error=str(e),
                )
            raise

    async def _compute_test_coverage_map(
        self,
        project_id: int,
        source_filter: str = None,
    ) -> Dict[str, Any]:
        """Compute test-to-source mapping."""
        # Get all source files
        source_files = await self._get_source_files(project_id, source_filter)

        # Get all test files
        test_files = await self._get_test_files(project_id)

        # Map tests to sources
        mappings = []
        covered_sources = set()

        for test_file in test_files:
            # Find source files this test imports/references
            tested_sources = await self._find_tested_sources(project_id, test_file)

            if tested_sources:
                mappings.append({
                    "test_file": test_file,
                    "tests_sources": tested_sources,
                    "coverage_count": len(tested_sources),
                })
                covered_sources.update(tested_sources)

        # Find uncovered source files
        uncovered = [s for s in source_files if s not in covered_sources]

        coverage_percentage = (len(covered_sources) / len(source_files) * 100) if source_files else 0

        return {
            "project_id": project_id,
            "total_source_files": len(source_files),
            "total_test_files": len(test_files),
            "covered_source_files": len(covered_sources),
            "uncovered_source_files": len(uncovered),
            "coverage_percentage": round(coverage_percentage, 1),
            "test_mappings": mappings[:50],
            "uncovered_files": uncovered[:30],
            "critical_gaps": self._identify_critical_gaps(uncovered, project_id),
            "recommendations": self._coverage_recommendations(coverage_percentage, uncovered),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Enhancement Scope ====================

    async def graph_enhancement_scope(
        self,
        project_id: int,
        feature_id: str,
        workflow_type: str = None,
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Determine enhancement scope via graph analysis.

        Used by: ENHANCEMENT

        Args:
            project_id: Project ID
            feature_id: Feature identifier to enhance
            workflow_type: Optional workflow type
            session_id: Optional workflow session ID

        Returns:
            Scope report with affected files, estimated effort, boundaries
        """
        start_time = datetime.utcnow()

        cache_key = f"scope:{feature_id}"
        cached = self._get_cached_result(project_id, "enhancement_scope", cache_key)
        if cached:
            return cached

        try:
            result = await self._compute_enhancement_scope(project_id, feature_id)

            self._cache_result(project_id, "enhancement_scope", cache_key, result)

            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "enhancement_scope",
                    {"feature_id": feature_id},
                    result,
                    start_time,
                )

            return result

        except Exception as e:
            logger.error(f"Enhancement scope failed: {e}")
            if workflow_type:
                self._track_integration(
                    workflow_type,
                    session_id,
                    project_id,
                    "enhancement_scope",
                    {"feature_id": feature_id},
                    None,
                    start_time,
                    error=str(e),
                )
            raise

    async def _compute_enhancement_scope(
        self,
        project_id: int,
        feature_id: str,
    ) -> Dict[str, Any]:
        """Compute enhancement scope boundaries."""
        # Find all entities related to this feature
        feature_entities = await self._find_feature_entities(project_id, feature_id)

        # Find boundaries (what touches other features)
        boundary_entities = []
        internal_entities = []

        for entity in feature_entities:
            deps = await self._find_dependencies(project_id, entity, direction="both")
            external_deps = [d for d in deps if d not in feature_entities]

            if external_deps:
                boundary_entities.append({
                    "entity": entity,
                    "external_connections": len(external_deps),
                    "connected_to": external_deps[:5],
                })
            else:
                internal_entities.append(entity)

        # Estimate effort based on scope
        scope_size = len(feature_entities)
        boundary_complexity = len(boundary_entities)

        effort_estimate = self._estimate_enhancement_effort(scope_size, boundary_complexity)

        return {
            "feature_id": feature_id,
            "scope_size": scope_size,
            "internal_entities": internal_entities[:30],
            "boundary_entities": boundary_entities[:20],
            "boundary_complexity": boundary_complexity,
            "isolation_score": 1 - (boundary_complexity / scope_size) if scope_size > 0 else 1,
            "effort_estimate": effort_estimate,
            "safe_to_modify": internal_entities[:20],
            "requires_caution": [b["entity"] for b in boundary_entities][:10],
            "recommendations": self._scope_recommendations(boundary_entities, scope_size),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Workflow Integration ====================

    def get_integrations_for_workflow(self, workflow_type: str) -> List[str]:
        """Get list of graph integrations available for a workflow type."""
        return WORKFLOW_GRAPH_INTEGRATIONS.get(workflow_type, [])

    async def run_workflow_integrations(
        self,
        workflow_type: str,
        project_id: int,
        session_id: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run all graph integrations for a workflow.

        Args:
            workflow_type: Type of workflow (NEW_FEATURE, BUG, etc.)
            project_id: Project ID
            session_id: Workflow session ID
            context: Workflow context with changes, entity_id, etc.

        Returns:
            Combined results from all integrations
        """
        integrations = self.get_integrations_for_workflow(workflow_type)
        results = {}

        for integration in integrations:
            try:
                if integration == "impact_analysis" and "changes" in context:
                    results["impact_analysis"] = await self.graph_impact_analysis(
                        project_id,
                        context["changes"],
                        workflow_type,
                        session_id,
                    )

                elif integration == "dependency_check" and "entity_id" in context:
                    results["dependency_check"] = await self.graph_dependency_check(
                        project_id,
                        context["entity_id"],
                        context.get("entity_type", "module"),
                        workflow_type,
                        session_id,
                    )

                elif integration == "coupling_metrics":
                    results["coupling_metrics"] = await self.graph_coupling_metrics(
                        project_id,
                        context.get("module_filter"),
                        workflow_type,
                        session_id,
                    )

                elif integration == "test_coverage_map":
                    results["test_coverage_map"] = await self.graph_test_coverage_map(
                        project_id,
                        context.get("source_filter"),
                        workflow_type,
                        session_id,
                    )

                elif integration == "enhancement_scope" and "feature_id" in context:
                    results["enhancement_scope"] = await self.graph_enhancement_scope(
                        project_id,
                        context["feature_id"],
                        workflow_type,
                        session_id,
                    )

            except Exception as e:
                logger.error(f"Integration {integration} failed for {workflow_type}: {e}")
                results[integration] = {"error": str(e), "status": "failed"}

        return {
            "workflow_type": workflow_type,
            "project_id": project_id,
            "session_id": session_id,
            "integrations_run": list(results.keys()),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Statistics ====================

    async def get_integration_statistics(
        self,
        project_id: int = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get statistics on graph integration usage."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(WorkflowGraphIntegration)
        if project_id:
            query = query.filter(WorkflowGraphIntegration.project_id == project_id)

        query = query.filter(WorkflowGraphIntegration.created_at >= cutoff)
        integrations = query.all()

        # Count by type
        type_counts = {}
        workflow_counts = {}
        success_count = 0
        total_duration = 0

        for i in integrations:
            type_counts[i.integration_type] = type_counts.get(i.integration_type, 0) + 1
            workflow_counts[i.workflow_type] = workflow_counts.get(i.workflow_type, 0) + 1

            if i.status == "completed":
                success_count += 1
            if i.duration_ms:
                total_duration += i.duration_ms

        return {
            "period_days": days,
            "total_integrations": len(integrations),
            "successful_integrations": success_count,
            "success_rate": round(success_count / len(integrations) * 100, 1) if integrations else 0,
            "average_duration_ms": round(total_duration / len(integrations)) if integrations else 0,
            "by_integration_type": type_counts,
            "by_workflow_type": workflow_counts,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ==================== Cache Management ====================

    def _get_cached_result(
        self,
        project_id: int,
        analysis_type: str,
        entity_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached result if valid."""
        cache = self.db.query(GraphAnalysisCache).filter(
            and_(
                GraphAnalysisCache.project_id == project_id,
                GraphAnalysisCache.analysis_type == analysis_type,
                GraphAnalysisCache.entity_id == entity_id,
                GraphAnalysisCache.expires_at > datetime.utcnow(),
            )
        ).first()

        if cache:
            cache.cache_hit_count += 1
            self.db.commit()
            return cache.result
        return None

    def _cache_result(
        self,
        project_id: int,
        analysis_type: str,
        entity_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Cache analysis result."""
        ttl_hours = self.CACHE_TTL.get(analysis_type, 1)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Delete old cache entry if exists
        self.db.query(GraphAnalysisCache).filter(
            and_(
                GraphAnalysisCache.project_id == project_id,
                GraphAnalysisCache.analysis_type == analysis_type,
                GraphAnalysisCache.entity_id == entity_id,
            )
        ).delete()

        cache = GraphAnalysisCache(
            project_id=project_id,
            analysis_type=analysis_type,
            entity_id=entity_id,
            result=result,
            expires_at=expires_at,
        )
        self.db.add(cache)
        self.db.commit()

    # ==================== Integration Tracking ====================

    def _track_integration(
        self,
        workflow_type: str,
        session_id: str,
        project_id: int,
        integration_type: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        start_time: datetime,
        error: str = None,
    ) -> None:
        """Track integration execution."""
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        integration = WorkflowGraphIntegration(
            workflow_type=workflow_type,
            workflow_session_id=session_id,
            project_id=project_id,
            integration_type=integration_type,
            input_data=input_data,
            output_data=output_data,
            status="completed" if not error else "failed",
            error_message=error,
            started_at=start_time,
            completed_at=end_time,
            duration_ms=duration_ms,
        )
        self.db.add(integration)
        self.db.commit()

    # ==================== Helper Methods ====================

    async def _find_dependencies(
        self,
        project_id: int,
        entity_id: str,
        direction: str = "both",
        depth: int = 1,
    ) -> List[str]:
        """Find dependencies for an entity. Placeholder - would use actual graph data."""
        # In real implementation, query code_graph_entities and code_graph_relationships
        # For now, return placeholder data
        return [f"dep_{i}_{entity_id[:20]}" for i in range(min(depth * 3, 10))]

    async def _get_project_modules(
        self,
        project_id: int,
        module_filter: str = None,
    ) -> List[str]:
        """Get list of modules in project. Placeholder."""
        return [f"module_{i}" for i in range(10)]

    async def _count_incoming_deps(self, project_id: int, module: str) -> int:
        """Count incoming dependencies (fan-in). Placeholder."""
        return hash(module) % 20

    async def _count_outgoing_deps(self, project_id: int, module: str) -> int:
        """Count outgoing dependencies (fan-out). Placeholder."""
        return hash(module + "out") % 15

    async def _get_source_files(self, project_id: int, filter_path: str = None) -> List[str]:
        """Get source files. Placeholder."""
        return [f"src/file_{i}.py" for i in range(20)]

    async def _get_test_files(self, project_id: int) -> List[str]:
        """Get test files. Placeholder."""
        return [f"tests/test_{i}.py" for i in range(10)]

    async def _find_tested_sources(self, project_id: int, test_file: str) -> List[str]:
        """Find sources tested by a test file. Placeholder."""
        idx = int(test_file.split("_")[1].split(".")[0]) if "_" in test_file else 0
        return [f"src/file_{idx}.py", f"src/file_{idx + 1}.py"]

    async def _find_feature_entities(self, project_id: int, feature_id: str) -> List[str]:
        """Find entities belonging to a feature. Placeholder."""
        return [f"{feature_id}_entity_{i}" for i in range(8)]

    def _detect_circular_dependencies(
        self,
        entity_id: str,
        upstream: List[str],
        downstream: List[str],
    ) -> List[Dict[str, Any]]:
        """Detect circular dependencies."""
        circular = []
        overlap = set(upstream) & set(downstream)
        for entity in overlap:
            circular.append({
                "entity": entity_id,
                "circular_with": entity,
                "type": "mutual_dependency",
            })
        return circular

    def _calculate_dependency_depth(self, deps: List[str]) -> int:
        """Calculate max dependency depth."""
        return min(len(deps) // 3 + 1, 5)

    def _calculate_risk_score(
        self,
        changes: int,
        affected: int,
        ripple: int,
    ) -> float:
        """Calculate risk score 0-1."""
        # Simple formula: more changes and ripple = higher risk
        base = min(changes / 10, 1.0) * 0.3
        direct = min(affected / 50, 1.0) * 0.3
        indirect = min(ripple / 100, 1.0) * 0.4
        return round(base + direct + indirect, 2)

    def _risk_level(self, score: float) -> str:
        """Convert risk score to level."""
        if score < 0.3:
            return "low"
        elif score < 0.6:
            return "medium"
        elif score < 0.8:
            return "high"
        return "critical"

    def _coupling_score(self, fan_in: int, fan_out: int) -> float:
        """Calculate coupling score 0-1."""
        total = fan_in + fan_out
        if total == 0:
            return 0
        return round(min(total / 30, 1.0), 2)

    def _estimate_enhancement_effort(
        self,
        scope_size: int,
        boundary_complexity: int,
    ) -> Dict[str, Any]:
        """Estimate effort for enhancement."""
        base_hours = scope_size * 0.5
        complexity_factor = 1 + (boundary_complexity * 0.2)
        total_hours = base_hours * complexity_factor

        return {
            "estimated_hours": round(total_hours, 1),
            "story_points": round(total_hours / 4),
            "complexity": "low" if total_hours < 8 else "medium" if total_hours < 24 else "high",
        }

    def _impact_recommendations(self, risk_score: float, affected: List[str]) -> List[str]:
        """Generate recommendations based on impact."""
        recs = []
        if risk_score > 0.7:
            recs.append("High impact change - consider breaking into smaller PRs")
        if risk_score > 0.5:
            recs.append("Recommend thorough code review")
        if len(affected) > 20:
            recs.append("Many files affected - ensure comprehensive testing")
        return recs or ["Standard review process sufficient"]

    def _coupling_recommendations(self, modules: List[Dict]) -> List[str]:
        """Generate recommendations for coupling issues."""
        recs = []
        highly_coupled = [m for m in modules if m["coupling_score"] > 0.7]
        if highly_coupled:
            recs.append(f"{len(highly_coupled)} highly coupled modules need refactoring")
        unstable = [m for m in modules if m["instability"] > 0.8]
        if unstable:
            recs.append(f"{len(unstable)} unstable modules - consider interface stabilization")
        return recs or ["Coupling levels acceptable"]

    def _coverage_recommendations(self, coverage: float, uncovered: List[str]) -> List[str]:
        """Generate test coverage recommendations."""
        recs = []
        if coverage < 50:
            recs.append("Critical: Test coverage below 50%")
        elif coverage < 70:
            recs.append("Warning: Test coverage below 70%")
        if len(uncovered) > 10:
            recs.append(f"Add tests for {len(uncovered)} uncovered files")
        return recs or ["Test coverage adequate"]

    def _scope_recommendations(self, boundaries: List[Dict], size: int) -> List[str]:
        """Generate scope recommendations."""
        recs = []
        if len(boundaries) > size * 0.5:
            recs.append("Feature has many external dependencies - consider interface redesign")
        if size > 20:
            recs.append("Large scope - consider splitting into sub-features")
        return recs or ["Scope is well-contained"]

    def _identify_critical_gaps(self, uncovered: List[str], project_id: int) -> List[str]:
        """Identify critical test coverage gaps."""
        # In real implementation, would identify critical paths
        critical_patterns = ["auth", "payment", "security", "core"]
        gaps = []
        for file in uncovered:
            for pattern in critical_patterns:
                if pattern in file.lower():
                    gaps.append(file)
                    break
        return gaps[:10]

    # ==================== Cache Clearing ====================

    async def clear_cache(
        self,
        project_id: int,
        analysis_type: str = None,
    ) -> Dict[str, Any]:
        """
        Clear cached analysis results for a project.

        Args:
            project_id: Project ID
            analysis_type: Optional specific analysis type to clear

        Returns:
            Info about cleared cache entries
        """
        try:
            query = self.db.query(GraphAnalysisCache).filter(
                GraphAnalysisCache.project_id == project_id
            )

            if analysis_type:
                query = query.filter(GraphAnalysisCache.analysis_type == analysis_type)

            count = query.count()
            query.delete()
            self.db.commit()

            return {
                "success": True,
                "project_id": project_id,
                "analysis_type": analysis_type or "all",
                "cleared_entries": count,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to clear cache: {e}")
            return {
                "success": False,
                "error": str(e),
            }
