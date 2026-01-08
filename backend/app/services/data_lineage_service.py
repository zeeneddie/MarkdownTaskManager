"""
DataLineageService - Track data flow from Brown Paper specs to code

This service tracks the complete lineage:
Brown Paper Session → Domain → Entity → Field → Epic → Story → Test → Code

Key capabilities:
- Build lineage graph from Brown Paper output
- Track field mappings between legacy and new
- Impact analysis for changes
- Traceability reports

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.models.data_architecture import (
    LineageNodeType, LineageEdgeType, TransformationType,
    LineageNode, LineageEdge, FieldMapping, ImpactAnalysisResult, LineageGraph,
    DataLineageSession, DataLineageFieldMapping
)

logger = logging.getLogger(__name__)


class DataLineageService:
    """
    Service for tracking data lineage from extraction to implementation.

    The rebuild strategy requires complete traceability:
    - Where did this spec come from? (Brown Paper extraction)
    - What code implements this spec? (new codebase)
    - What tests validate this spec? (TDD tests)
    - If this changes, what else is affected? (impact analysis)
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self._graphs: Dict[str, LineageGraph] = {}  # In-memory cache

    # ============================================
    # Session Management
    # ============================================

    async def create_session(
        self,
        name: str,
        project_id: Optional[str] = None,
        brown_paper_session_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Create a new lineage tracking session."""
        session_id = str(uuid.uuid4())

        graph = LineageGraph(
            session_id=session_id,
            project_id=project_id or "",
            nodes=[],
            edges=[],
            field_mappings=[]
        )
        self._graphs[session_id] = graph

        if self.db:
            db_session = DataLineageSession(
                id=session_id,
                project_id=project_id,
                brown_paper_session_id=brown_paper_session_id,
                name=name,
                description=description,
                status="active"
            )
            self.db.add(db_session)
            await self.db.commit()

        logger.info(f"Created lineage session: {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[LineageGraph]:
        """Get lineage graph for session."""
        if session_id in self._graphs:
            return self._graphs[session_id]

        if self.db:
            result = await self.db.execute(
                select(DataLineageSession).where(DataLineageSession.id == session_id)
            )
            db_session = result.scalar_one_or_none()
            if db_session and db_session.graph_data:
                # Reconstruct graph from JSON
                graph = self._deserialize_graph(db_session.graph_data, session_id, db_session.project_id or "")
                self._graphs[session_id] = graph
                return graph

        return None

    async def save_session(self, session_id: str) -> bool:
        """Persist session to database."""
        graph = self._graphs.get(session_id)
        if not graph or not self.db:
            return False

        graph_data = self._serialize_graph(graph)

        await self.db.execute(
            update(DataLineageSession)
            .where(DataLineageSession.id == session_id)
            .values(
                graph_data=graph_data,
                node_count=len(graph.nodes),
                edge_count=len(graph.edges),
                field_mapping_count=len(graph.field_mappings),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        return True

    # ============================================
    # Node Management
    # ============================================

    async def add_node(
        self,
        session_id: str,
        node_type: LineageNodeType,
        name: str,
        description: Optional[str] = None,
        source_path: Optional[str] = None,
        source_line: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a node to the lineage graph."""
        graph = await self.get_session(session_id)
        if not graph:
            raise ValueError(f"Session {session_id} not found")

        node_id = str(uuid.uuid4())
        node = LineageNode(
            id=node_id,
            node_type=node_type,
            name=name,
            description=description,
            source_path=source_path,
            source_line=source_line,
            metadata=metadata or {}
        )
        graph.nodes.append(node)

        logger.debug(f"Added node: {node_type.value}/{name}")
        return node_id

    async def add_nodes_batch(
        self,
        session_id: str,
        nodes: List[Dict[str, Any]]
    ) -> List[str]:
        """Add multiple nodes at once."""
        node_ids = []
        for node_data in nodes:
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType(node_data["node_type"]),
                name=node_data["name"],
                description=node_data.get("description"),
                source_path=node_data.get("source_path"),
                source_line=node_data.get("source_line"),
                metadata=node_data.get("metadata")
            )
            node_ids.append(node_id)
        return node_ids

    async def find_nodes(
        self,
        session_id: str,
        node_type: Optional[LineageNodeType] = None,
        name_pattern: Optional[str] = None
    ) -> List[LineageNode]:
        """Find nodes by type and/or name pattern."""
        graph = await self.get_session(session_id)
        if not graph:
            return []

        nodes = graph.nodes

        if node_type:
            nodes = [n for n in nodes if n.node_type == node_type]

        if name_pattern:
            pattern = name_pattern.lower()
            nodes = [n for n in nodes if pattern in n.name.lower()]

        return nodes

    # ============================================
    # Edge Management
    # ============================================

    async def add_edge(
        self,
        session_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_type: LineageEdgeType,
        transformation: Optional[TransformationType] = None,
        transformation_rule: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add an edge connecting two nodes."""
        graph = await self.get_session(session_id)
        if not graph:
            raise ValueError(f"Session {session_id} not found")

        # Validate nodes exist
        if not graph.get_node(source_node_id):
            raise ValueError(f"Source node {source_node_id} not found")
        if not graph.get_node(target_node_id):
            raise ValueError(f"Target node {target_node_id} not found")

        edge_id = str(uuid.uuid4())
        edge = LineageEdge(
            id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            transformation=transformation,
            transformation_rule=transformation_rule,
            confidence=confidence,
            metadata=metadata or {}
        )
        graph.edges.append(edge)

        logger.debug(f"Added edge: {edge_type.value} from {source_node_id[:8]} to {target_node_id[:8]}")
        return edge_id

    async def connect_chain(
        self,
        session_id: str,
        node_ids: List[str],
        edge_type: LineageEdgeType
    ) -> List[str]:
        """Connect a chain of nodes with the same edge type."""
        edge_ids = []
        for i in range(len(node_ids) - 1):
            edge_id = await self.add_edge(
                session_id=session_id,
                source_node_id=node_ids[i],
                target_node_id=node_ids[i + 1],
                edge_type=edge_type
            )
            edge_ids.append(edge_id)
        return edge_ids

    # ============================================
    # Field Mapping
    # ============================================

    async def add_field_mapping(
        self,
        session_id: str,
        legacy_table: str,
        legacy_field: str,
        legacy_type: str,
        new_table: str,
        new_field: str,
        new_type: str,
        transformation: TransformationType,
        transformation_rule: Optional[str] = None,
        nullable_legacy: bool = True,
        nullable_new: bool = True,
        default_value: Optional[str] = None,
        validation_rule: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Add a field mapping between legacy and new schema."""
        graph = await self.get_session(session_id)
        if not graph:
            raise ValueError(f"Session {session_id} not found")

        mapping = FieldMapping(
            legacy_table=legacy_table,
            legacy_field=legacy_field,
            legacy_type=legacy_type,
            new_table=new_table,
            new_field=new_field,
            new_type=new_type,
            transformation=transformation,
            transformation_rule=transformation_rule,
            nullable_legacy=nullable_legacy,
            nullable_new=nullable_new,
            default_value=default_value,
            validation_rule=validation_rule,
            notes=notes
        )
        graph.field_mappings.append(mapping)

        # Also persist to separate table if DB available
        if self.db:
            db_mapping = DataLineageFieldMapping(
                id=str(uuid.uuid4()),
                session_id=session_id,
                legacy_table=legacy_table,
                legacy_field=legacy_field,
                legacy_type=legacy_type,
                new_table=new_table,
                new_field=new_field,
                new_type=new_type,
                transformation_type=transformation.value,
                transformation_rule=transformation_rule,
                nullable_legacy=nullable_legacy,
                nullable_new=nullable_new,
                default_value=default_value,
                validation_rule=validation_rule,
                notes=notes
            )
            self.db.add(db_mapping)
            await self.db.commit()
            return db_mapping.id

        return str(uuid.uuid4())

    async def get_field_mappings(
        self,
        session_id: str,
        table_filter: Optional[str] = None
    ) -> List[FieldMapping]:
        """Get field mappings, optionally filtered by table."""
        graph = await self.get_session(session_id)
        if not graph:
            return []

        mappings = graph.field_mappings

        if table_filter:
            mappings = [
                m for m in mappings
                if table_filter.lower() in m.legacy_table.lower() or
                   table_filter.lower() in m.new_table.lower()
            ]

        return mappings

    async def suggest_field_mappings(
        self,
        session_id: str,
        legacy_schema: Dict[str, Dict[str, str]],
        new_schema: Dict[str, Dict[str, str]]
    ) -> List[FieldMapping]:
        """
        Suggest field mappings based on name similarity.

        Args:
            legacy_schema: {table_name: {field_name: field_type}}
            new_schema: {table_name: {field_name: field_type}}

        Returns:
            List of suggested mappings with confidence scores
        """
        suggestions = []

        for legacy_table, legacy_fields in legacy_schema.items():
            # Find matching table in new schema
            new_table = self._find_similar_name(legacy_table, list(new_schema.keys()))
            if not new_table:
                continue

            for legacy_field, legacy_type in legacy_fields.items():
                new_field = self._find_similar_name(legacy_field, list(new_schema[new_table].keys()))
                if not new_field:
                    continue

                new_type = new_schema[new_table][new_field]

                # Determine transformation type
                if legacy_type.lower() == new_type.lower():
                    transformation = TransformationType.DIRECT_COPY
                elif legacy_field.lower() != new_field.lower():
                    transformation = TransformationType.RENAME
                else:
                    transformation = TransformationType.TYPE_CHANGE

                mapping = FieldMapping(
                    legacy_table=legacy_table,
                    legacy_field=legacy_field,
                    legacy_type=legacy_type,
                    new_table=new_table,
                    new_field=new_field,
                    new_type=new_type,
                    transformation=transformation
                )
                suggestions.append(mapping)

        return suggestions

    def _find_similar_name(self, name: str, candidates: List[str], threshold: float = 0.6) -> Optional[str]:
        """Find most similar name from candidates."""
        name_lower = name.lower().replace("_", "").replace("-", "")

        best_match = None
        best_score = threshold

        for candidate in candidates:
            candidate_lower = candidate.lower().replace("_", "").replace("-", "")

            # Exact match
            if name_lower == candidate_lower:
                return candidate

            # Substring match
            if name_lower in candidate_lower or candidate_lower in name_lower:
                score = min(len(name_lower), len(candidate_lower)) / max(len(name_lower), len(candidate_lower))
                if score > best_score:
                    best_score = score
                    best_match = candidate

        return best_match

    # ============================================
    # Impact Analysis
    # ============================================

    async def analyze_impact(
        self,
        session_id: str,
        node_id: str
    ) -> ImpactAnalysisResult:
        """
        Analyze the impact of changing a node.

        Traces all downstream dependencies:
        - If a field changes, which stories are affected?
        - If a story changes, which tests need updates?
        - If code changes, which specs need review?
        """
        graph = await self.get_session(session_id)
        if not graph:
            raise ValueError(f"Session {session_id} not found")

        node = graph.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # BFS to find all affected nodes
        affected_nodes = []
        affected_edges = []
        visited = {node_id}
        queue = [node_id]

        while queue:
            current_id = queue.pop(0)
            downstream = graph.get_downstream(current_id)

            for downstream_node in downstream:
                if downstream_node.id not in visited:
                    visited.add(downstream_node.id)
                    queue.append(downstream_node.id)
                    affected_nodes.append(downstream_node)

                    # Find the edge
                    for edge in graph.edges:
                        if edge.source_node_id == current_id and edge.target_node_id == downstream_node.id:
                            affected_edges.append(edge)

        # Categorize affected items
        test_cases = [n.name for n in affected_nodes if n.node_type == LineageNodeType.TEST_CASE]
        code_files = [n.source_path for n in affected_nodes if n.node_type in (LineageNodeType.CODE_FILE, LineageNodeType.CODE_CLASS) and n.source_path]
        stories = [n.name for n in affected_nodes if n.node_type == LineageNodeType.USER_STORY]

        # Determine risk level
        if len(affected_nodes) > 20 or len(test_cases) > 10:
            risk_level = "critical"
        elif len(affected_nodes) > 10 or len(test_cases) > 5:
            risk_level = "high"
        elif len(affected_nodes) > 5:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate recommendations
        recommendations = []
        if test_cases:
            recommendations.append(f"Update {len(test_cases)} test case(s): {', '.join(test_cases[:3])}")
        if stories:
            recommendations.append(f"Review {len(stories)} user story/stories for accuracy")
        if code_files:
            recommendations.append(f"Check {len(code_files)} code file(s) for compatibility")
        if risk_level in ("high", "critical"):
            recommendations.append("Consider phased rollout due to high impact")

        return ImpactAnalysisResult(
            changed_node_id=node_id,
            changed_node_name=node.name,
            affected_nodes=affected_nodes,
            affected_edges=affected_edges,
            test_cases_affected=test_cases,
            code_files_affected=code_files,
            stories_affected=stories,
            risk_level=risk_level,
            recommendations=recommendations
        )

    # ============================================
    # Brown Paper Integration
    # ============================================

    async def import_from_brown_paper(
        self,
        session_id: str,
        brown_paper_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Import lineage from Brown Paper Enhanced output.

        Expects structure from Phase 3 (Hierarchical Extraction):
        {
            "domains": [...],
            "entities": [...],
            "epics": [...],
            "features": [...],
            "stories": [...],
            "acceptance_criteria": [...]
        }
        """
        graph = await self.get_session(session_id)
        if not graph:
            raise ValueError(f"Session {session_id} not found")

        counts = {"nodes": 0, "edges": 0}
        node_map = {}  # old_id -> new_node_id

        # Add domains
        for domain in brown_paper_data.get("domains", []):
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType.DOMAIN,
                name=domain.get("name", "Unknown"),
                description=domain.get("description"),
                metadata=domain
            )
            node_map[domain.get("id", domain["name"])] = node_id
            counts["nodes"] += 1

        # Add entities
        for entity in brown_paper_data.get("entities", []):
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType.ENTITY,
                name=entity.get("name", "Unknown"),
                description=entity.get("description"),
                source_path=entity.get("source_file"),
                metadata=entity
            )
            node_map[entity.get("id", entity["name"])] = node_id
            counts["nodes"] += 1

            # Link to domain if specified
            domain_id = entity.get("domain_id")
            if domain_id and domain_id in node_map:
                await self.add_edge(
                    session_id=session_id,
                    source_node_id=node_map[domain_id],
                    target_node_id=node_id,
                    edge_type=LineageEdgeType.DEFINES
                )
                counts["edges"] += 1

        # Add epics
        for epic in brown_paper_data.get("epics", []):
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType.EPIC,
                name=epic.get("title", epic.get("name", "Unknown")),
                description=epic.get("description"),
                metadata=epic
            )
            node_map[epic.get("id", epic.get("title", ""))] = node_id
            counts["nodes"] += 1

        # Add features
        for feature in brown_paper_data.get("features", []):
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType.FEATURE,
                name=feature.get("title", feature.get("name", "Unknown")),
                description=feature.get("description"),
                metadata=feature
            )
            node_map[feature.get("id", feature.get("title", ""))] = node_id
            counts["nodes"] += 1

            # Link to epic
            epic_id = feature.get("epic_id")
            if epic_id and epic_id in node_map:
                await self.add_edge(
                    session_id=session_id,
                    source_node_id=node_map[epic_id],
                    target_node_id=node_id,
                    edge_type=LineageEdgeType.DEFINES
                )
                counts["edges"] += 1

        # Add stories
        for story in brown_paper_data.get("stories", []):
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType.USER_STORY,
                name=story.get("title", story.get("name", "Unknown")),
                description=story.get("description"),
                metadata=story
            )
            node_map[story.get("id", story.get("title", ""))] = node_id
            counts["nodes"] += 1

            # Link to feature
            feature_id = story.get("feature_id")
            if feature_id and feature_id in node_map:
                await self.add_edge(
                    session_id=session_id,
                    source_node_id=node_map[feature_id],
                    target_node_id=node_id,
                    edge_type=LineageEdgeType.DEFINES
                )
                counts["edges"] += 1

        # Add acceptance criteria
        for ac in brown_paper_data.get("acceptance_criteria", []):
            node_id = await self.add_node(
                session_id=session_id,
                node_type=LineageNodeType.ACCEPTANCE_CRITERIA,
                name=ac.get("title", ac.get("criteria", "Unknown")),
                description=ac.get("description", ac.get("criteria")),
                metadata=ac
            )
            node_map[ac.get("id", "")] = node_id
            counts["nodes"] += 1

            # Link to story
            story_id = ac.get("story_id")
            if story_id and story_id in node_map:
                await self.add_edge(
                    session_id=session_id,
                    source_node_id=node_map[story_id],
                    target_node_id=node_id,
                    edge_type=LineageEdgeType.DEFINES
                )
                counts["edges"] += 1

        logger.info(f"Imported from Brown Paper: {counts['nodes']} nodes, {counts['edges']} edges")
        return counts

    # ============================================
    # Traceability Reports
    # ============================================

    async def generate_traceability_matrix(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate a traceability matrix showing relationships.

        Returns a matrix showing:
        - Requirements → Stories → Tests → Code
        """
        graph = await self.get_session(session_id)
        if not graph:
            return {}

        matrix = {
            "epics": [],
            "features": [],
            "stories": [],
            "tests": [],
            "summary": {
                "total_epics": 0,
                "total_features": 0,
                "total_stories": 0,
                "total_tests": 0,
                "coverage": {
                    "stories_with_tests": 0,
                    "stories_without_tests": 0
                }
            }
        }

        # Gather nodes by type
        epics = [n for n in graph.nodes if n.node_type == LineageNodeType.EPIC]
        features = [n for n in graph.nodes if n.node_type == LineageNodeType.FEATURE]
        stories = [n for n in graph.nodes if n.node_type == LineageNodeType.USER_STORY]
        tests = [n for n in graph.nodes if n.node_type == LineageNodeType.TEST_CASE]

        matrix["summary"]["total_epics"] = len(epics)
        matrix["summary"]["total_features"] = len(features)
        matrix["summary"]["total_stories"] = len(stories)
        matrix["summary"]["total_tests"] = len(tests)

        # Build matrix entries
        for epic in epics:
            epic_features = graph.get_downstream(epic.id)
            matrix["epics"].append({
                "id": epic.id,
                "name": epic.name,
                "feature_count": len(epic_features),
                "features": [f.name for f in epic_features if f.node_type == LineageNodeType.FEATURE]
            })

        for story in stories:
            story_tests = [n for n in graph.get_downstream(story.id) if n.node_type == LineageNodeType.TEST_CASE]
            has_tests = len(story_tests) > 0

            matrix["stories"].append({
                "id": story.id,
                "name": story.name,
                "has_tests": has_tests,
                "test_count": len(story_tests),
                "tests": [t.name for t in story_tests]
            })

            if has_tests:
                matrix["summary"]["coverage"]["stories_with_tests"] += 1
            else:
                matrix["summary"]["coverage"]["stories_without_tests"] += 1

        # Calculate coverage percentage
        if stories:
            matrix["summary"]["coverage"]["percentage"] = round(
                matrix["summary"]["coverage"]["stories_with_tests"] / len(stories) * 100, 1
            )
        else:
            matrix["summary"]["coverage"]["percentage"] = 0.0

        return matrix

    # ============================================
    # Serialization Helpers
    # ============================================

    def _serialize_graph(self, graph: LineageGraph) -> Dict[str, Any]:
        """Serialize LineageGraph to JSON-compatible dict."""
        return {
            "session_id": graph.session_id,
            "project_id": graph.project_id,
            "nodes": [
                {
                    "id": n.id,
                    "node_type": n.node_type.value,
                    "name": n.name,
                    "description": n.description,
                    "source_path": n.source_path,
                    "source_line": n.source_line,
                    "metadata": n.metadata,
                    "created_at": n.created_at.isoformat()
                }
                for n in graph.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "edge_type": e.edge_type.value,
                    "transformation": e.transformation.value if e.transformation else None,
                    "transformation_rule": e.transformation_rule,
                    "confidence": e.confidence,
                    "metadata": e.metadata
                }
                for e in graph.edges
            ],
            "field_mappings": [asdict(m) for m in graph.field_mappings],
            "created_at": graph.created_at.isoformat(),
            "updated_at": graph.updated_at.isoformat()
        }

    def _deserialize_graph(self, data: Dict[str, Any], session_id: str, project_id: str) -> LineageGraph:
        """Deserialize JSON to LineageGraph."""
        nodes = [
            LineageNode(
                id=n["id"],
                node_type=LineageNodeType(n["node_type"]),
                name=n["name"],
                description=n.get("description"),
                source_path=n.get("source_path"),
                source_line=n.get("source_line"),
                metadata=n.get("metadata", {}),
                created_at=datetime.fromisoformat(n["created_at"]) if n.get("created_at") else datetime.utcnow()
            )
            for n in data.get("nodes", [])
        ]

        edges = [
            LineageEdge(
                id=e["id"],
                source_node_id=e["source_node_id"],
                target_node_id=e["target_node_id"],
                edge_type=LineageEdgeType(e["edge_type"]),
                transformation=TransformationType(e["transformation"]) if e.get("transformation") else None,
                transformation_rule=e.get("transformation_rule"),
                confidence=e.get("confidence", 1.0),
                metadata=e.get("metadata", {})
            )
            for e in data.get("edges", [])
        ]

        field_mappings = [
            FieldMapping(**m) if isinstance(m.get("transformation"), str) else
            FieldMapping(
                legacy_table=m["legacy_table"],
                legacy_field=m["legacy_field"],
                legacy_type=m["legacy_type"],
                new_table=m["new_table"],
                new_field=m["new_field"],
                new_type=m["new_type"],
                transformation=TransformationType(m["transformation"]),
                transformation_rule=m.get("transformation_rule"),
                nullable_legacy=m.get("nullable_legacy", True),
                nullable_new=m.get("nullable_new", True),
                default_value=m.get("default_value"),
                validation_rule=m.get("validation_rule"),
                notes=m.get("notes")
            )
            for m in data.get("field_mappings", [])
        ]

        return LineageGraph(
            session_id=session_id,
            project_id=project_id,
            nodes=nodes,
            edges=edges,
            field_mappings=field_mappings
        )

    # ============================================
    # Statistics
    # ============================================

    async def get_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a lineage session."""
        graph = await self.get_session(session_id)
        if not graph:
            return {}

        node_counts = {}
        for node in graph.nodes:
            node_type = node.node_type.value
            node_counts[node_type] = node_counts.get(node_type, 0) + 1

        edge_counts = {}
        for edge in graph.edges:
            edge_type = edge.edge_type.value
            edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1

        transformation_counts = {}
        for mapping in graph.field_mappings:
            trans_type = mapping.transformation.value
            transformation_counts[trans_type] = transformation_counts.get(trans_type, 0) + 1

        return {
            "session_id": session_id,
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "total_field_mappings": len(graph.field_mappings),
            "nodes_by_type": node_counts,
            "edges_by_type": edge_counts,
            "transformations_by_type": transformation_counts
        }
