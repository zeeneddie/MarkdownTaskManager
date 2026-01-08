"""
Graph Persistence Service - Week 75

Extends KnowledgeGraphService with PostgreSQL persistence for:
- Entity storage and versioning
- Impact analysis via recursive CTEs
- Circular dependency detection
- Module coupling metrics
- Graph snapshots for comparison
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set, Tuple
from uuid import UUID
import hashlib
import logging

from sqlalchemy import text, select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.code_graph import (
    CodeGraphEntity,
    CodeGraphRelation,
    CodeGraphSnapshot,
    CodeGraphImpactCache,
    CodeGraphModuleCoupling
)
from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    EntityType,
    RelationType,
    CodeEntity,
    EntityRelation
)

logger = logging.getLogger(__name__)


class GraphPersistenceService:
    """
    Persistent code graph service with PostgreSQL storage.

    Builds on KnowledgeGraphService and adds:
    - Database persistence for entities and relations
    - Impact analysis with recursive queries
    - Circular dependency detection
    - Module coupling analysis
    - Graph snapshots for version comparison
    """

    def __init__(self, db: AsyncSession):
        """Initialize with async database session."""
        self.db = db
        self._cache_ttl = timedelta(hours=1)

    # =========================================================================
    # SECTION 1: Graph Sync & Persistence
    # =========================================================================

    async def sync_project_graph(
        self,
        project_id: int,
        repo_path: str,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Sync a project's code graph to the database.

        Uses KnowledgeGraphService to parse, then persists to PostgreSQL.

        Args:
            project_id: Project ID
            repo_path: Path to repository
            languages: Languages to analyze (default: ["python"])

        Returns:
            Sync statistics
        """
        languages = languages or ["python"]

        # Use KnowledgeGraphService to build in-memory graph
        kg_service = KnowledgeGraphService(None)
        graph_result = kg_service.build_graph(repo_path, project_id, languages)

        if "error" in graph_result:
            return graph_result

        # Track statistics
        stats = {
            "entities_added": 0,
            "entities_updated": 0,
            "relations_added": 0,
            "files_processed": graph_result.get("files_analyzed", 0)
        }

        # Persist entities
        for entity_id, entity in kg_service._entities.items():
            db_entity = await self._upsert_entity(project_id, entity)
            if db_entity:
                stats["entities_added" if db_entity.created_at == db_entity.updated_at else "entities_updated"] += 1

        # Persist relations
        for relation in kg_service._relations:
            await self._upsert_relation(project_id, relation, kg_service._entities)
            stats["relations_added"] += 1

        # Update module coupling
        await self._calculate_module_coupling(project_id)

        await self.db.commit()

        return {
            "success": True,
            "project_id": project_id,
            "repo_path": repo_path,
            **stats
        }

    async def _upsert_entity(
        self,
        project_id: int,
        entity: CodeEntity
    ) -> Optional[CodeGraphEntity]:
        """Insert or update a code entity."""
        # Calculate content hash
        content_hash = self._calculate_entity_hash(entity)

        # Check if exists
        stmt = select(CodeGraphEntity).where(
            and_(
                CodeGraphEntity.project_id == project_id,
                CodeGraphEntity.qualified_name == entity.id
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update if hash changed
            if existing.hash != content_hash:
                existing.entity_type = entity.entity_type.value
                existing.name = entity.name
                existing.file_path = entity.file_path
                existing.start_line = entity.start_line
                existing.end_line = entity.end_line
                existing.docstring = entity.docstring
                existing.entity_data = entity.metadata
                existing.hash = content_hash
                existing.last_synced = datetime.utcnow()
            return existing
        else:
            # Insert new
            db_entity = CodeGraphEntity(
                project_id=project_id,
                entity_type=entity.entity_type.value,
                name=entity.name,
                qualified_name=entity.id,
                file_path=entity.file_path,
                start_line=entity.start_line,
                end_line=entity.end_line,
                docstring=entity.docstring,
                entity_data=entity.metadata,
                hash=content_hash,
                last_synced=datetime.utcnow()
            )
            self.db.add(db_entity)
            await self.db.flush()
            return db_entity

    async def _upsert_relation(
        self,
        project_id: int,
        relation: EntityRelation,
        entities: Dict[str, CodeEntity]
    ) -> Optional[CodeGraphRelation]:
        """Insert or update a relation between entities."""
        # Find source and target entities in DB
        source_stmt = select(CodeGraphEntity).where(
            and_(
                CodeGraphEntity.project_id == project_id,
                CodeGraphEntity.qualified_name == relation.source_id
            )
        )
        source_result = await self.db.execute(source_stmt)
        source_entity = source_result.scalar_one_or_none()

        target_stmt = select(CodeGraphEntity).where(
            and_(
                CodeGraphEntity.project_id == project_id,
                CodeGraphEntity.qualified_name == relation.target_id
            )
        )
        target_result = await self.db.execute(target_stmt)
        target_entity = target_result.scalar_one_or_none()

        if not source_entity or not target_entity:
            return None

        # Check if relation exists
        rel_stmt = select(CodeGraphRelation).where(
            and_(
                CodeGraphRelation.source_entity_id == source_entity.id,
                CodeGraphRelation.target_entity_id == target_entity.id,
                CodeGraphRelation.relation_type == relation.relation_type.value
            )
        )
        rel_result = await self.db.execute(rel_stmt)
        existing = rel_result.scalar_one_or_none()

        if existing:
            existing.relation_data = relation.metadata
            return existing
        else:
            db_relation = CodeGraphRelation(
                project_id=project_id,
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relation_type=relation.relation_type.value,
                relation_data=relation.metadata
            )
            self.db.add(db_relation)
            await self.db.flush()
            return db_relation

    def _calculate_entity_hash(self, entity: CodeEntity) -> str:
        """Calculate hash for change detection."""
        content = f"{entity.entity_type.value}:{entity.name}:{entity.file_path}:{entity.start_line}:{entity.end_line}"
        return hashlib.sha256(content.encode()).hexdigest()[:64]

    # =========================================================================
    # SECTION 2: Impact Analysis
    # =========================================================================

    async def get_impact_analysis(
        self,
        project_id: int,
        entity_id: UUID,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Perform impact analysis for an entity.

        Uses recursive CTE to find all affected entities.

        Args:
            project_id: Project ID
            entity_id: Entity to analyze
            max_depth: Maximum depth to traverse

        Returns:
            Impact analysis results
        """
        # Check cache first
        cached = await self._get_cached_impact(entity_id, "transitive")
        if cached and cached.cache_valid_until > datetime.utcnow():
            return {
                "entity_id": str(entity_id),
                "affected_entities": cached.affected_entities,
                "affected_files": cached.affected_files,
                "impact_score": cached.impact_score,
                "depth": cached.depth,
                "from_cache": True
            }

        # Recursive CTE for transitive dependencies
        cte_query = text("""
            WITH RECURSIVE impact_chain AS (
                -- Base case: direct dependencies
                SELECT
                    r.target_entity_id as entity_id,
                    1 as depth,
                    ARRAY[r.source_entity_id] as path
                FROM code_graph_relations r
                WHERE r.source_entity_id = :entity_id
                  AND r.project_id = :project_id

                UNION ALL

                -- Recursive case: indirect dependencies
                SELECT
                    r.target_entity_id,
                    ic.depth + 1,
                    ic.path || r.source_entity_id
                FROM code_graph_relations r
                INNER JOIN impact_chain ic ON r.source_entity_id = ic.entity_id
                WHERE ic.depth < :max_depth
                  AND NOT r.target_entity_id = ANY(ic.path)  -- Prevent cycles
                  AND r.project_id = :project_id
            )
            SELECT DISTINCT
                e.id,
                e.name,
                e.entity_type,
                e.file_path,
                MIN(ic.depth) as min_depth
            FROM impact_chain ic
            JOIN code_graph_entities e ON e.id = ic.entity_id
            GROUP BY e.id, e.name, e.entity_type, e.file_path
            ORDER BY min_depth, e.name
        """)

        result = await self.db.execute(
            cte_query,
            {"entity_id": str(entity_id), "project_id": project_id, "max_depth": max_depth}
        )
        affected = result.fetchall()

        # Build result
        affected_entities = [
            {
                "id": str(row.id),
                "name": row.name,
                "type": row.entity_type,
                "file_path": row.file_path,
                "depth": row.min_depth
            }
            for row in affected
        ]

        affected_files = list(set(row.file_path for row in affected))

        # Calculate impact score (weighted by depth)
        impact_score = sum(1.0 / (row.min_depth + 1) for row in affected)
        max_depth_found = max((row.min_depth for row in affected), default=0)

        # Cache result
        await self._cache_impact(
            project_id=project_id,
            entity_id=entity_id,
            impact_type="transitive",
            affected_entities=[str(row.id) for row in affected],
            affected_files=affected_files,
            impact_score=impact_score,
            depth=max_depth_found
        )

        return {
            "entity_id": str(entity_id),
            "affected_entities": affected_entities,
            "affected_files": affected_files,
            "impact_score": impact_score,
            "depth": max_depth_found,
            "from_cache": False
        }

    async def get_direct_dependencies(
        self,
        project_id: int,
        entity_id: UUID
    ) -> Dict[str, Any]:
        """Get direct dependencies of an entity."""
        stmt = select(CodeGraphRelation, CodeGraphEntity).join(
            CodeGraphEntity,
            CodeGraphRelation.target_entity_id == CodeGraphEntity.id
        ).where(
            and_(
                CodeGraphRelation.source_entity_id == entity_id,
                CodeGraphRelation.project_id == project_id
            )
        )

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        dependencies = [
            {
                "id": str(entity.id),
                "name": entity.name,
                "type": entity.entity_type,
                "file_path": entity.file_path,
                "relation_type": relation.relation_type
            }
            for relation, entity in rows
        ]

        return {
            "entity_id": str(entity_id),
            "dependencies": dependencies,
            "count": len(dependencies)
        }

    async def get_dependents(
        self,
        project_id: int,
        entity_id: UUID
    ) -> Dict[str, Any]:
        """Get entities that depend on this entity."""
        stmt = select(CodeGraphRelation, CodeGraphEntity).join(
            CodeGraphEntity,
            CodeGraphRelation.source_entity_id == CodeGraphEntity.id
        ).where(
            and_(
                CodeGraphRelation.target_entity_id == entity_id,
                CodeGraphRelation.project_id == project_id
            )
        )

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        dependents = [
            {
                "id": str(entity.id),
                "name": entity.name,
                "type": entity.entity_type,
                "file_path": entity.file_path,
                "relation_type": relation.relation_type
            }
            for relation, entity in rows
        ]

        return {
            "entity_id": str(entity_id),
            "dependents": dependents,
            "count": len(dependents)
        }

    # =========================================================================
    # SECTION 3: Circular Dependency Detection
    # =========================================================================

    async def detect_circular_dependencies(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Detect circular dependencies in the project.

        Uses recursive CTE with cycle detection.

        Returns:
            List of cycles found
        """
        cte_query = text("""
            WITH RECURSIVE dep_chain AS (
                -- Base case: all relations
                SELECT
                    r.source_entity_id,
                    r.target_entity_id,
                    ARRAY[r.source_entity_id, r.target_entity_id] as path,
                    FALSE as is_cycle
                FROM code_graph_relations r
                WHERE r.project_id = :project_id

                UNION ALL

                -- Recursive case
                SELECT
                    dc.source_entity_id,
                    r.target_entity_id,
                    dc.path || r.target_entity_id,
                    r.target_entity_id = dc.source_entity_id as is_cycle
                FROM dep_chain dc
                JOIN code_graph_relations r ON r.source_entity_id = dc.target_entity_id
                WHERE NOT r.target_entity_id = ANY(dc.path[2:])  -- Allow first element to repeat (cycle)
                  AND array_length(dc.path, 1) < 10  -- Limit path length
                  AND r.project_id = :project_id
            )
            SELECT DISTINCT
                source_entity_id,
                path
            FROM dep_chain
            WHERE is_cycle = TRUE
        """)

        result = await self.db.execute(cte_query, {"project_id": project_id})
        cycles = result.fetchall()

        # Enrich with entity names
        enriched_cycles = []
        for row in cycles:
            cycle_entities = []
            for entity_id in row.path:
                stmt = select(CodeGraphEntity).where(CodeGraphEntity.id == entity_id)
                entity_result = await self.db.execute(stmt)
                entity = entity_result.scalar_one_or_none()
                if entity:
                    cycle_entities.append({
                        "id": str(entity.id),
                        "name": entity.name,
                        "type": entity.entity_type
                    })

            enriched_cycles.append({
                "entities": cycle_entities,
                "length": len(cycle_entities)
            })

        return {
            "project_id": project_id,
            "cycles_found": len(enriched_cycles),
            "cycles": enriched_cycles
        }

    # =========================================================================
    # SECTION 4: Module Coupling Analysis
    # =========================================================================

    async def _calculate_module_coupling(self, project_id: int) -> None:
        """Calculate and store module coupling metrics."""
        # Get all entities grouped by module
        stmt = text("""
            SELECT DISTINCT
                CASE
                    WHEN position('/' in file_path) > 0
                    THEN substring(file_path from 1 for position('/' in file_path) - 1)
                    ELSE file_path
                END as module_path,
                id
            FROM code_graph_entities
            WHERE project_id = :project_id
        """)

        result = await self.db.execute(stmt, {"project_id": project_id})
        entity_modules = {str(row.id): row.module_path for row in result.fetchall()}

        # Get all relations and group by module
        coupling_query = text("""
            SELECT
                source_module,
                target_module,
                COUNT(*) as coupling_count,
                array_agg(DISTINCT relation_type) as relation_types
            FROM (
                SELECT
                    CASE
                        WHEN position('/' in se.file_path) > 0
                        THEN substring(se.file_path from 1 for position('/' in se.file_path) - 1)
                        ELSE se.file_path
                    END as source_module,
                    CASE
                        WHEN position('/' in te.file_path) > 0
                        THEN substring(te.file_path from 1 for position('/' in te.file_path) - 1)
                        ELSE te.file_path
                    END as target_module,
                    r.relation_type
                FROM code_graph_relations r
                JOIN code_graph_entities se ON r.source_entity_id = se.id
                JOIN code_graph_entities te ON r.target_entity_id = te.id
                WHERE r.project_id = :project_id
            ) sub
            WHERE source_module != target_module
            GROUP BY source_module, target_module
        """)

        result = await self.db.execute(coupling_query, {"project_id": project_id})
        couplings = result.fetchall()

        # Upsert coupling records
        for row in couplings:
            stmt = select(CodeGraphModuleCoupling).where(
                and_(
                    CodeGraphModuleCoupling.project_id == project_id,
                    CodeGraphModuleCoupling.source_module == row.source_module,
                    CodeGraphModuleCoupling.target_module == row.target_module
                )
            )
            existing_result = await self.db.execute(stmt)
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.coupling_count = row.coupling_count
                existing.coupling_data = {"relation_types": row.relation_types}
            else:
                coupling = CodeGraphModuleCoupling(
                    project_id=project_id,
                    source_module=row.source_module,
                    target_module=row.target_module,
                    coupling_count=row.coupling_count,
                    coupling_type="mixed" if len(row.relation_types) > 1 else row.relation_types[0],
                    coupling_data={"relation_types": row.relation_types}
                )
                self.db.add(coupling)

    async def get_module_coupling(
        self,
        project_id: int,
        sort_by: str = "coupling_count"
    ) -> Dict[str, Any]:
        """Get module coupling metrics."""
        stmt = select(CodeGraphModuleCoupling).where(
            CodeGraphModuleCoupling.project_id == project_id
        ).order_by(getattr(CodeGraphModuleCoupling, sort_by).desc())

        result = await self.db.execute(stmt)
        couplings = result.scalars().all()

        # Calculate metrics
        total_coupling = sum(c.coupling_count for c in couplings)
        modules = set()
        for c in couplings:
            modules.add(c.source_module)
            modules.add(c.target_module)

        avg_coupling = total_coupling / len(couplings) if couplings else 0

        return {
            "project_id": project_id,
            "total_modules": len(modules),
            "total_connections": len(couplings),
            "total_coupling_strength": total_coupling,
            "average_coupling": avg_coupling,
            "couplings": [c.to_dict() for c in couplings]
        }

    async def get_highly_coupled_modules(
        self,
        project_id: int,
        threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """Get modules with coupling above threshold."""
        stmt = select(CodeGraphModuleCoupling).where(
            and_(
                CodeGraphModuleCoupling.project_id == project_id,
                CodeGraphModuleCoupling.coupling_count >= threshold
            )
        ).order_by(CodeGraphModuleCoupling.coupling_count.desc())

        result = await self.db.execute(stmt)
        couplings = result.scalars().all()

        return [c.to_dict() for c in couplings]

    # =========================================================================
    # SECTION 5: Graph Snapshots
    # =========================================================================

    async def create_snapshot(
        self,
        project_id: int,
        snapshot_name: str = None,
        git_commit: str = None
    ) -> Dict[str, Any]:
        """
        Create a snapshot of the current graph state.

        Used for comparing graph evolution over time.
        """
        # Count entities by type
        entity_count_query = text("""
            SELECT entity_type, COUNT(*) as count
            FROM code_graph_entities
            WHERE project_id = :project_id
            GROUP BY entity_type
        """)
        result = await self.db.execute(entity_count_query, {"project_id": project_id})
        entity_counts = {row.entity_type: row.count for row in result.fetchall()}

        # Count relations by type
        relation_count_query = text("""
            SELECT relation_type, COUNT(*) as count
            FROM code_graph_relations
            WHERE project_id = :project_id
            GROUP BY relation_type
        """)
        result = await self.db.execute(relation_count_query, {"project_id": project_id})
        relation_counts = {row.relation_type: row.count for row in result.fetchall()}

        # Count files
        file_count_query = text("""
            SELECT COUNT(DISTINCT file_path) as count
            FROM code_graph_entities
            WHERE project_id = :project_id
        """)
        result = await self.db.execute(file_count_query, {"project_id": project_id})
        file_count = result.scalar()

        # Create snapshot
        snapshot = CodeGraphSnapshot(
            project_id=project_id,
            snapshot_name=snapshot_name,
            git_commit=git_commit,
            entity_count=sum(entity_counts.values()),
            relation_count=sum(relation_counts.values()),
            file_count=file_count,
            summary_stats={
                "entity_counts": entity_counts,
                "relation_counts": relation_counts
            }
        )

        self.db.add(snapshot)
        await self.db.commit()

        return snapshot.to_dict()

    async def get_snapshots(
        self,
        project_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent snapshots for a project."""
        stmt = select(CodeGraphSnapshot).where(
            CodeGraphSnapshot.project_id == project_id
        ).order_by(CodeGraphSnapshot.created_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        snapshots = result.scalars().all()

        return [s.to_dict() for s in snapshots]

    async def compare_snapshots(
        self,
        snapshot_id_1: UUID,
        snapshot_id_2: UUID
    ) -> Dict[str, Any]:
        """Compare two snapshots."""
        stmt1 = select(CodeGraphSnapshot).where(CodeGraphSnapshot.id == snapshot_id_1)
        stmt2 = select(CodeGraphSnapshot).where(CodeGraphSnapshot.id == snapshot_id_2)

        result1 = await self.db.execute(stmt1)
        result2 = await self.db.execute(stmt2)

        snap1 = result1.scalar_one_or_none()
        snap2 = result2.scalar_one_or_none()

        if not snap1 or not snap2:
            return {"error": "One or both snapshots not found"}

        # Calculate differences
        stats1 = snap1.summary_stats or {}
        stats2 = snap2.summary_stats or {}

        entity_diff = {}
        for key in set(stats1.get("entity_counts", {}).keys()) | set(stats2.get("entity_counts", {}).keys()):
            old_val = stats1.get("entity_counts", {}).get(key, 0)
            new_val = stats2.get("entity_counts", {}).get(key, 0)
            if old_val != new_val:
                entity_diff[key] = {"old": old_val, "new": new_val, "change": new_val - old_val}

        relation_diff = {}
        for key in set(stats1.get("relation_counts", {}).keys()) | set(stats2.get("relation_counts", {}).keys()):
            old_val = stats1.get("relation_counts", {}).get(key, 0)
            new_val = stats2.get("relation_counts", {}).get(key, 0)
            if old_val != new_val:
                relation_diff[key] = {"old": old_val, "new": new_val, "change": new_val - old_val}

        return {
            "snapshot_1": snap1.to_dict(),
            "snapshot_2": snap2.to_dict(),
            "entity_changes": entity_diff,
            "relation_changes": relation_diff,
            "total_entity_change": snap2.entity_count - snap1.entity_count,
            "total_relation_change": snap2.relation_count - snap1.relation_count,
            "total_file_change": snap2.file_count - snap1.file_count
        }

    # =========================================================================
    # SECTION 6: Query & Statistics
    # =========================================================================

    async def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a project's code graph."""
        # Entity counts
        entity_query = text("""
            SELECT entity_type, COUNT(*) as count
            FROM code_graph_entities
            WHERE project_id = :project_id
            GROUP BY entity_type
        """)
        result = await self.db.execute(entity_query, {"project_id": project_id})
        entity_counts = {row.entity_type: row.count for row in result.fetchall()}

        # Relation counts
        relation_query = text("""
            SELECT relation_type, COUNT(*) as count
            FROM code_graph_relations
            WHERE project_id = :project_id
            GROUP BY relation_type
        """)
        result = await self.db.execute(relation_query, {"project_id": project_id})
        relation_counts = {row.relation_type: row.count for row in result.fetchall()}

        # File count
        file_query = text("""
            SELECT COUNT(DISTINCT file_path) as count
            FROM code_graph_entities
            WHERE project_id = :project_id
        """)
        result = await self.db.execute(file_query, {"project_id": project_id})
        file_count = result.scalar()

        # Top referenced entities
        top_referenced_query = text("""
            SELECT e.id, e.name, e.entity_type, COUNT(r.id) as reference_count
            FROM code_graph_entities e
            LEFT JOIN code_graph_relations r ON r.target_entity_id = e.id
            WHERE e.project_id = :project_id
            GROUP BY e.id, e.name, e.entity_type
            ORDER BY reference_count DESC
            LIMIT 10
        """)
        result = await self.db.execute(top_referenced_query, {"project_id": project_id})
        top_referenced = [
            {"id": str(row.id), "name": row.name, "type": row.entity_type, "references": row.reference_count}
            for row in result.fetchall()
        ]

        return {
            "project_id": project_id,
            "total_entities": sum(entity_counts.values()),
            "total_relations": sum(relation_counts.values()),
            "total_files": file_count,
            "entity_counts": entity_counts,
            "relation_counts": relation_counts,
            "top_referenced_entities": top_referenced
        }

    async def search_entities(
        self,
        project_id: int,
        query: str,
        entity_type: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for entities by name."""
        stmt = select(CodeGraphEntity).where(
            and_(
                CodeGraphEntity.project_id == project_id,
                CodeGraphEntity.name.ilike(f"%{query}%")
            )
        )

        if entity_type:
            stmt = stmt.where(CodeGraphEntity.entity_type == entity_type)

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        entities = result.scalars().all()

        return [e.to_dict() for e in entities]

    async def get_entity_by_id(
        self,
        entity_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get a single entity by ID."""
        stmt = select(CodeGraphEntity).where(CodeGraphEntity.id == entity_id)
        result = await self.db.execute(stmt)
        entity = result.scalar_one_or_none()

        if entity:
            return entity.to_dict()
        return None

    async def get_entities_by_file(
        self,
        project_id: int,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Get all entities in a specific file."""
        stmt = select(CodeGraphEntity).where(
            and_(
                CodeGraphEntity.project_id == project_id,
                CodeGraphEntity.file_path == file_path
            )
        ).order_by(CodeGraphEntity.start_line)

        result = await self.db.execute(stmt)
        entities = result.scalars().all()

        return [e.to_dict() for e in entities]

    # =========================================================================
    # SECTION 7: Cache Management
    # =========================================================================

    async def _get_cached_impact(
        self,
        entity_id: UUID,
        impact_type: str
    ) -> Optional[CodeGraphImpactCache]:
        """Get cached impact analysis if valid."""
        stmt = select(CodeGraphImpactCache).where(
            and_(
                CodeGraphImpactCache.entity_id == entity_id,
                CodeGraphImpactCache.impact_type == impact_type
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _cache_impact(
        self,
        project_id: int,
        entity_id: UUID,
        impact_type: str,
        affected_entities: List[str],
        affected_files: List[str],
        impact_score: float,
        depth: int
    ) -> None:
        """Cache impact analysis results."""
        stmt = select(CodeGraphImpactCache).where(
            and_(
                CodeGraphImpactCache.entity_id == entity_id,
                CodeGraphImpactCache.impact_type == impact_type
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        cache_valid_until = datetime.utcnow() + self._cache_ttl

        if existing:
            existing.affected_entities = affected_entities
            existing.affected_files = affected_files
            existing.impact_score = impact_score
            existing.depth = depth
            existing.cache_valid_until = cache_valid_until
        else:
            cache = CodeGraphImpactCache(
                project_id=project_id,
                entity_id=entity_id,
                impact_type=impact_type,
                affected_entities=affected_entities,
                affected_files=affected_files,
                impact_score=impact_score,
                depth=depth,
                cache_valid_until=cache_valid_until
            )
            self.db.add(cache)

        await self.db.flush()

    async def invalidate_cache(
        self,
        project_id: int,
        entity_id: UUID = None
    ) -> int:
        """Invalidate impact cache for a project or specific entity."""
        if entity_id:
            stmt = select(CodeGraphImpactCache).where(
                CodeGraphImpactCache.entity_id == entity_id
            )
        else:
            stmt = select(CodeGraphImpactCache).where(
                CodeGraphImpactCache.project_id == project_id
            )

        result = await self.db.execute(stmt)
        cached = result.scalars().all()

        count = 0
        for cache in cached:
            await self.db.delete(cache)
            count += 1

        await self.db.flush()
        return count

    # =========================================================================
    # SECTION 8: Graph Export
    # =========================================================================

    async def export_graph_for_visualization(
        self,
        project_id: int,
        format: str = "d3"
    ) -> Dict[str, Any]:
        """
        Export graph data for visualization.

        Formats:
        - d3: D3.js force-directed graph format
        - dot: GraphViz DOT format
        """
        # Get all entities
        entities_stmt = select(CodeGraphEntity).where(
            CodeGraphEntity.project_id == project_id
        )
        entities_result = await self.db.execute(entities_stmt)
        entities = entities_result.scalars().all()

        # Get all relations
        relations_stmt = select(CodeGraphRelation).where(
            CodeGraphRelation.project_id == project_id
        )
        relations_result = await self.db.execute(relations_stmt)
        relations = relations_result.scalars().all()

        if format == "d3":
            return {
                "nodes": [
                    {
                        "id": str(e.id),
                        "name": e.name,
                        "type": e.entity_type,
                        "file": e.file_path,
                        "group": hash(e.file_path) % 10  # Color grouping by file
                    }
                    for e in entities
                ],
                "links": [
                    {
                        "source": str(r.source_entity_id),
                        "target": str(r.target_entity_id),
                        "type": r.relation_type,
                        "weight": r.weight
                    }
                    for r in relations
                ]
            }
        elif format == "dot":
            lines = ["digraph CodeGraph {"]
            lines.append("  rankdir=LR;")

            for e in entities:
                shape = "box" if e.entity_type == "class" else "ellipse"
                lines.append(f'  "{e.id}" [label="{e.name}" shape={shape}];')

            for r in relations:
                style = "dashed" if r.relation_type == "imports" else "solid"
                lines.append(f'  "{r.source_entity_id}" -> "{r.target_entity_id}" [style={style}];')

            lines.append("}")
            return {"dot": "\n".join(lines)}

        return {"error": f"Unknown format: {format}"}
