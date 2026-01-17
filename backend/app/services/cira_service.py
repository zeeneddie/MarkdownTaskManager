# backend/app/services/cira_service.py
"""
CiRA Service - Causality Detection in Requirements Artifacts

Week 123: CiRA PoC & Evaluation
Week 124: Full BERT Integration, Fine-tuning Pipeline
Week 125: Pipeline Integration with HierarchicalStoryExtractionService

Based on:
- Paper: arXiv:2101.10766 - REFSQ 2021
- Repository: github.com/fischJan/CiRA
- Performance: 82% macro-F1 score
"""

import re
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.causality import (
    CausalSession,
    CausalClassification,
    CausalRelation,
    CausalDependencyGraph,
    CausalTestCase,
    CausalSessionStatus,
    CausalSourceType,
    CausalRelationType,
    ExtractionMethod,
    TestCaseType,
    TestCaseStatus,
    TestPriority,
    GraphType,
    GraphFormat,
    CAUSAL_MARKERS,
    detect_causal_markers,
    classify_relation_type,
)

# Week 124: Import BERT classifier
from app.services.bert_causal_classifier import (
    BERTCausalClassifier,
    ClassificationResult,
    POSTagger,
)

logger = logging.getLogger(__name__)


# ============== BERT INTEGRATION (Week 124) ==============

# Global classifier instance (singleton pattern for efficiency)
_classifier_instance: Optional[BERTCausalClassifier] = None
_pos_tagger_instance: Optional[POSTagger] = None


def get_classifier() -> BERTCausalClassifier:
    """
    Get or create the global BERT classifier instance.

    Week 124: Uses settings for configuration.
    """
    global _classifier_instance

    if _classifier_instance is None:
        _classifier_instance = BERTCausalClassifier(
            model_name=settings.CIRA_MODEL_NAME,
            model_path=settings.CIRA_MODEL_PATH if settings.CIRA_MODEL_PATH else None,
            device=settings.CIRA_DEVICE,
            max_length=settings.CIRA_MAX_LENGTH,
            batch_size=settings.CIRA_BATCH_SIZE,
            temperature=settings.CIRA_TEMPERATURE,
        )

    return _classifier_instance


async def get_pos_tagger() -> Optional[POSTagger]:
    """Get or create the POS tagger if enabled."""
    global _pos_tagger_instance

    if not settings.CIRA_USE_POS_TAGS:
        return None

    if _pos_tagger_instance is None:
        _pos_tagger_instance = POSTagger()
        await _pos_tagger_instance.load()

    return _pos_tagger_instance


async def ensure_classifier_loaded() -> BERTCausalClassifier:
    """Ensure the classifier model is loaded."""
    classifier = get_classifier()

    if not classifier.is_loaded and settings.CIRA_USE_BERT:
        await classifier.load_model()

    return classifier


# ============== CAUSAL RELATION EXTRACTOR ==============

class CausalRelationExtractor:
    """
    Extracts cause-effect relations from causal sentences.

    Uses pattern matching and NLP to identify:
    - Cause clause
    - Effect clause
    - Causal marker
    - Relation type
    """

    # Patterns for cause-effect extraction
    CAUSE_EFFECT_PATTERNS = [
        # if X then Y
        (r"if\s+(.+?),?\s*then\s+(.+)", "if_then"),
        # when X, Y
        (r"when\s+(.+?),\s*(.+)", "when"),
        # X because Y
        (r"(.+?)\s+because\s+(.+)", "because"),
        # X therefore Y
        (r"(.+?)\s+therefore\s+(.+)", "therefore"),
        # X leads to Y
        (r"(.+?)\s+leads?\s+to\s+(.+)", "leads_to"),
        # X causes Y
        (r"(.+?)\s+causes?\s+(.+)", "causes"),
        # X results in Y
        (r"(.+?)\s+results?\s+in\s+(.+)", "results_in"),
        # X enables Y
        (r"(.+?)\s+enables?\s+(.+)", "enables"),
        # X allows Y
        (r"(.+?)\s+allows?\s+(.+)", "allows"),
        # X requires Y
        (r"(.+?)\s+requires?\s+(.+)", "requires"),
        # X depends on Y
        (r"(.+?)\s+depends?\s+on\s+(.+)", "depends_on"),
        # in order to X, Y
        (r"in\s+order\s+to\s+(.+?),\s*(.+)", "in_order_to"),
        # so that X, Y
        (r"(.+?)\s+so\s+that\s+(.+)", "so_that"),
        # provided that X, Y
        (r"(.+?)\s+provided\s+that\s+(.+)", "provided_that"),
    ]

    def extract_relations(self, sentence: str, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract causal relations from a sentence.

        Returns list of relations with cause/effect texts and metadata.
        """
        relations = []
        sentence_lower = sentence.lower().strip()

        for pattern, pattern_type in self.CAUSE_EFFECT_PATTERNS:
            matches = re.finditer(pattern, sentence_lower, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    # Determine cause and effect based on pattern
                    if pattern_type in ["because"]:
                        # "X because Y" -> Y causes X
                        effect_text = groups[0].strip()
                        cause_text = groups[1].strip()
                    elif pattern_type in ["requires", "depends_on"]:
                        # "X requires Y" -> Y enables X
                        effect_text = groups[0].strip()
                        cause_text = groups[1].strip()
                    else:
                        # Default: first group is cause, second is effect
                        cause_text = groups[0].strip()
                        effect_text = groups[1].strip()

                    # Determine relation type
                    relation_type = self._determine_relation_type(pattern_type)

                    # Calculate confidence based on pattern clarity
                    confidence = self._calculate_extraction_confidence(pattern_type, cause_text, effect_text)

                    relations.append({
                        "cause_text": cause_text,
                        "effect_text": effect_text,
                        "causal_marker": pattern_type,
                        "relation_type": relation_type,
                        "confidence": confidence,
                        "source_id": source_id,
                        "pattern_matched": pattern,
                    })

        return relations

    def _determine_relation_type(self, pattern_type: str) -> str:
        """Map pattern type to CausalRelationType."""
        type_mapping = {
            "if_then": CausalRelationType.CAUSES.value,
            "when": CausalRelationType.CAUSES.value,
            "because": CausalRelationType.CAUSES.value,
            "therefore": CausalRelationType.CAUSES.value,
            "leads_to": CausalRelationType.CAUSES.value,
            "causes": CausalRelationType.CAUSES.value,
            "results_in": CausalRelationType.CAUSES.value,
            "enables": CausalRelationType.ENABLES.value,
            "allows": CausalRelationType.ENABLES.value,
            "requires": CausalRelationType.DEPENDS_ON.value,
            "depends_on": CausalRelationType.DEPENDS_ON.value,
            "in_order_to": CausalRelationType.ENABLES.value,
            "so_that": CausalRelationType.CAUSES.value,
            "provided_that": CausalRelationType.DEPENDS_ON.value,
        }
        return type_mapping.get(pattern_type, CausalRelationType.CAUSES.value)

    def _calculate_extraction_confidence(self, pattern_type: str, cause: str, effect: str) -> float:
        """Calculate confidence score for extraction."""
        base_confidence = 0.7

        # Boost for clear patterns
        clear_patterns = ["if_then", "because", "causes", "leads_to"]
        if pattern_type in clear_patterns:
            base_confidence += 0.1

        # Reduce for very short clauses
        if len(cause) < 10 or len(effect) < 10:
            base_confidence -= 0.1

        # Boost for longer, complete clauses
        if len(cause) > 30 and len(effect) > 30:
            base_confidence += 0.05

        return min(max(base_confidence, 0.4), 0.95)


# ============== GRAPH BUILDER ==============

class CausalGraphBuilder:
    """
    Builds dependency graphs from causal relations.

    Provides:
    - Node/edge representation
    - Critical path analysis
    - Cycle detection
    - Topological ordering
    - Sprint planning suggestions
    """

    def build_graph(self, relations: List[CausalRelation], session_id: UUID) -> Dict[str, Any]:
        """
        Build a causal dependency graph from relations.

        Returns graph structure with nodes, edges, and analysis results.
        """
        nodes = {}
        edges = []

        # Build nodes from unique sources
        node_id_map = {}

        for relation in relations:
            # Add cause node
            cause_key = relation.cause_source_id or relation.cause_text[:50]
            if cause_key not in node_id_map:
                node_id = str(uuid4())
                node_id_map[cause_key] = node_id
                nodes[node_id] = {
                    "id": node_id,
                    "label": relation.cause_text[:100],
                    "source_id": relation.cause_source_id,
                    "type": "requirement",
                }

            # Add effect node
            effect_key = relation.effect_source_id or relation.effect_text[:50]
            if effect_key not in node_id_map:
                node_id = str(uuid4())
                node_id_map[effect_key] = node_id
                nodes[node_id] = {
                    "id": node_id,
                    "label": relation.effect_text[:100],
                    "source_id": relation.effect_source_id,
                    "type": "requirement",
                }

            # Add edge
            edges.append({
                "id": str(relation.id),
                "source": node_id_map[cause_key],
                "target": node_id_map[effect_key],
                "relation_type": relation.relation_type,
                "confidence": relation.confidence,
                "label": relation.causal_marker or relation.relation_type,
            })

        # Analyze graph
        root_nodes = self._find_root_nodes(nodes, edges)
        leaf_nodes = self._find_leaf_nodes(nodes, edges)
        cycles = self._detect_cycles(nodes, edges)
        topological_order = self._topological_sort(nodes, edges) if not cycles else None
        critical_path = self._find_critical_path(nodes, edges)
        suggested_sprints = self._suggest_sprint_order(nodes, edges, topological_order)

        return {
            "session_id": str(session_id),
            "nodes": list(nodes.values()),
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "root_nodes": root_nodes,
            "leaf_nodes": leaf_nodes,
            "cycles": cycles,
            "topological_order": topological_order,
            "critical_path": critical_path,
            "suggested_sprint_order": suggested_sprints,
        }

    def _find_root_nodes(self, nodes: Dict, edges: List[Dict]) -> List[str]:
        """Find nodes with no incoming edges."""
        targets = {e["target"] for e in edges}
        return [n["id"] for n in nodes.values() if n["id"] not in targets]

    def _find_leaf_nodes(self, nodes: Dict, edges: List[Dict]) -> List[str]:
        """Find nodes with no outgoing edges."""
        sources = {e["source"] for e in edges}
        return [n["id"] for n in nodes.values() if n["id"] not in sources]

    def _detect_cycles(self, nodes: Dict, edges: List[Dict]) -> List[List[str]]:
        """Detect cycles in the graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        # Build adjacency list
        adj = {n: [] for n in nodes.keys()}
        for e in edges:
            if e["source"] in adj:
                adj[e["source"]].append(e["target"])

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for node in nodes.keys():
            if node not in visited:
                dfs(node, [])

        return cycles

    def _topological_sort(self, nodes: Dict, edges: List[Dict]) -> Optional[List[str]]:
        """Perform topological sort on the graph."""
        # Calculate in-degrees
        in_degree = {n: 0 for n in nodes.keys()}
        adj = {n: [] for n in nodes.keys()}

        for e in edges:
            if e["target"] in in_degree:
                in_degree[e["target"]] += 1
            if e["source"] in adj:
                adj[e["source"]].append(e["target"])

        # Start with nodes of in-degree 0
        queue = [n for n, d in in_degree.items() if d == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(nodes):
            return None  # Graph has cycle

        return result

    def _find_critical_path(self, nodes: Dict, edges: List[Dict]) -> Optional[List[str]]:
        """Find the longest path in the graph (critical path)."""
        if not nodes or not edges:
            return None

        # Build adjacency list with edge weights (using confidence as weight)
        adj = {n: [] for n in nodes.keys()}
        for e in edges:
            if e["source"] in adj:
                adj[e["source"]].append((e["target"], 1))  # Weight = 1 for path length

        # Find longest path using dynamic programming
        longest = {}

        def dfs(node: str) -> int:
            if node in longest:
                return longest[node]

            max_length = 0
            for neighbor, weight in adj.get(node, []):
                max_length = max(max_length, dfs(neighbor) + weight)

            longest[node] = max_length
            return max_length

        # Calculate longest path from each node
        for node in nodes.keys():
            if node not in longest:
                dfs(node)

        if not longest:
            return None

        # Find the starting node of the critical path
        start_node = max(longest.keys(), key=lambda n: longest[n])

        # Reconstruct path
        path = [start_node]
        current = start_node
        while adj.get(current):
            neighbors = adj[current]
            if not neighbors:
                break
            # Choose neighbor with longest remaining path
            next_node = max(neighbors, key=lambda x: longest.get(x[0], 0))
            path.append(next_node[0])
            current = next_node[0]

        return path

    def _suggest_sprint_order(self, nodes: Dict, edges: List[Dict],
                               topological_order: Optional[List[str]]) -> Optional[List[List[str]]]:
        """Suggest sprint groupings based on dependencies."""
        if not topological_order:
            return None

        # Calculate levels (distance from root)
        levels = {}
        for node in topological_order:
            incoming = [e for e in edges if e["target"] == node]
            if not incoming:
                levels[node] = 0
            else:
                levels[node] = max(levels.get(e["source"], 0) for e in incoming) + 1

        # Group by level (sprint)
        max_level = max(levels.values()) if levels else 0
        sprints = []
        for level in range(max_level + 1):
            sprint_nodes = [n for n, l in levels.items() if l == level]
            if sprint_nodes:
                sprints.append(sprint_nodes)

        return sprints


# ============== TEST CASE GENERATOR ==============

class CausalTestGenerator:
    """
    Generates test cases from causal relations.

    For each cause-effect pair, generates:
    - Positive test: verify cause leads to effect
    - Negative test: verify without cause, no effect
    - Boundary tests: edge cases
    """

    def generate_tests(self, relation: CausalRelation) -> List[Dict[str, Any]]:
        """Generate test cases for a causal relation."""
        tests = []

        # Positive test
        tests.append({
            "test_type": TestCaseType.POSITIVE.value,
            "test_name": f"Verify: {relation.cause_text[:50]} → {relation.effect_text[:50]}",
            "description": f"Verify that when {relation.cause_text}, then {relation.effect_text}",
            "preconditions": [relation.cause_text],
            "trigger": f"Execute: {relation.cause_text}",
            "expected_result": relation.effect_text,
            "test_steps": [
                {"step": 1, "action": "Setup preconditions", "expected": "System in initial state"},
                {"step": 2, "action": f"Trigger: {relation.cause_text[:80]}", "expected": "Action executed"},
                {"step": 3, "action": "Verify outcome", "expected": relation.effect_text[:80]},
            ],
            "priority": self._determine_priority(relation),
            "tags": [relation.relation_type, "positive", "automated"],
        })

        # Negative test
        tests.append({
            "test_type": TestCaseType.NEGATIVE.value,
            "test_name": f"Verify absence: NOT {relation.cause_text[:40]} → NOT {relation.effect_text[:40]}",
            "description": f"Verify that without {relation.cause_text}, {relation.effect_text} does not occur",
            "preconditions": [f"Ensure {relation.cause_text} is NOT present/executed"],
            "trigger": "Verify system state without trigger",
            "expected_result": f"{relation.effect_text} should NOT occur",
            "test_steps": [
                {"step": 1, "action": "Setup without cause condition", "expected": "Cause absent"},
                {"step": 2, "action": "Wait/verify state", "expected": "No state change"},
                {"step": 3, "action": f"Verify: {relation.effect_text[:60]} NOT present", "expected": "Effect absent"},
            ],
            "priority": self._determine_priority(relation, is_negative=True),
            "tags": [relation.relation_type, "negative", "manual"],
        })

        # Boundary test (if applicable)
        if relation.relation_type == CausalRelationType.DEPENDS_ON.value:
            tests.append({
                "test_type": TestCaseType.BOUNDARY.value,
                "test_name": f"Boundary: Partial {relation.cause_text[:40]}",
                "description": f"Test boundary conditions for dependency",
                "preconditions": ["Setup partial dependency state"],
                "trigger": f"Attempt: {relation.effect_text[:60]}",
                "expected_result": "System handles partial dependency gracefully",
                "test_steps": [
                    {"step": 1, "action": "Setup partial state", "expected": "Partial setup"},
                    {"step": 2, "action": "Attempt dependent action", "expected": "Graceful handling"},
                    {"step": 3, "action": "Verify error handling", "expected": "Clear error message"},
                ],
                "priority": TestPriority.LOW.value,
                "tags": [relation.relation_type, "boundary", "edge-case"],
            })

        return tests

    def _determine_priority(self, relation: CausalRelation, is_negative: bool = False) -> str:
        """Determine test priority based on relation properties."""
        if relation.relation_type == CausalRelationType.BLOCKS.value:
            return TestPriority.HIGH.value
        if relation.relation_type == CausalRelationType.DEPENDS_ON.value:
            return TestPriority.HIGH.value
        if relation.confidence >= 0.85:
            return TestPriority.HIGH.value
        if is_negative:
            return TestPriority.LOW.value
        return TestPriority.MEDIUM.value


# ============== MAIN SERVICE ==============

class CiRAService:
    """
    Main CiRA Service for causality detection and analysis.

    Week 124 Updates:
    - Full BERT model integration
    - Fine-tuning support
    - Confidence calibration
    - POS tag features

    Provides:
    - Session management
    - Causality classification (BERT + rule-based fallback)
    - Relation extraction
    - Dependency graph building
    - Test case generation
    - Model fine-tuning
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.classifier = get_classifier()  # Week 124: Use configured classifier
        self.extractor = CausalRelationExtractor()
        self.graph_builder = CausalGraphBuilder()
        self.test_generator = CausalTestGenerator()
        self._model_loaded = False

    async def ensure_model_loaded(self) -> None:
        """Ensure the BERT model is loaded before inference."""
        if not self._model_loaded and settings.CIRA_USE_BERT:
            await self.classifier.load_model()
            self._model_loaded = self.classifier.is_loaded

    # ============== SESSION MANAGEMENT ==============

    async def create_session(
        self,
        project_id: Optional[int] = None,
        extraction_id: Optional[UUID] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        source_type: str = CausalSourceType.REQUIREMENTS.value,
        confidence_threshold: float = 0.6,
        settings: Optional[Dict[str, Any]] = None
    ) -> CausalSession:
        """Create a new causality analysis session."""
        session = CausalSession(
            id=uuid4(),
            project_id=project_id,
            extraction_id=extraction_id,
            name=name or f"Causality Analysis {datetime.now(timezone.utc).isoformat()}",
            description=description,
            status=CausalSessionStatus.PENDING.value,
            source_type=source_type,
            confidence_threshold=confidence_threshold,
            settings=settings or {},
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Created causal session: {session.id}")
        return session

    async def get_session(self, session_id: UUID) -> Optional[CausalSession]:
        """Get a causality session by ID."""
        result = await self.db.execute(
            select(CausalSession)
            .options(
                selectinload(CausalSession.classifications),
                selectinload(CausalSession.relations),
                selectinload(CausalSession.dependency_graphs),
            )
            .where(CausalSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CausalSession]:
        """List causality sessions with optional filters."""
        query = select(CausalSession)

        if project_id:
            query = query.where(CausalSession.project_id == project_id)
        if status:
            query = query.where(CausalSession.status == status)

        query = query.order_by(CausalSession.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============== ANALYSIS ==============

    async def analyze_sentences(
        self,
        session_id: UUID,
        sentences: List[str],
        source_ids: Optional[List[str]] = None,
        source_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentences for causality.

        Week 124: Uses BERT model if available, with rule-based fallback.

        Args:
            session_id: The analysis session ID
            sentences: List of sentences to analyze
            source_ids: Optional list of source IDs (e.g., story IDs)
            source_type: Type of source (story, feature, etc.)

        Returns:
            Analysis results with classifications and relations
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Start processing
        session.start_processing()
        session.input_count = len(sentences)

        try:
            # Week 124: Ensure BERT model is loaded
            await self.ensure_model_loaded()

            # Classify sentences (returns ClassificationResult objects)
            prediction_results = await self.classifier.predict(sentences)

            # Convert ClassificationResult to dict for backward compatibility
            predictions = []
            for result in prediction_results:
                predictions.append({
                    "is_causal": result.is_causal,
                    "confidence": result.confidence,
                    "probability_causal": result.probability_causal,
                    "probability_non_causal": result.probability_non_causal,
                    "markers": result.markers,
                })

            classifications = []
            all_relations = []
            causal_count = 0
            non_causal_count = 0
            total_confidence = 0.0

            for i, (sentence, pred) in enumerate(zip(sentences, predictions)):
                source_id = source_ids[i] if source_ids and i < len(source_ids) else None

                # Create classification
                classification = CausalClassification(
                    id=uuid4(),
                    session_id=session_id,
                    project_id=session.project_id,
                    source_id=source_id,
                    source_type=source_type,
                    sentence=sentence,
                    sentence_index=i,
                    is_causal=pred["is_causal"],
                    confidence=pred["confidence"],
                    probability_causal=pred["probability_causal"],
                    probability_non_causal=pred["probability_non_causal"],
                    markers=pred.get("markers", []),
                )

                self.db.add(classification)
                classifications.append(classification)

                if pred["is_causal"]:
                    causal_count += 1
                    total_confidence += pred["confidence"]

                    # Extract relations from causal sentences
                    if pred["confidence"] >= session.confidence_threshold:
                        relations = self.extractor.extract_relations(sentence, source_id)

                        # Week 124: Determine extraction method based on classifier state
                        extraction_method = (
                            ExtractionMethod.BERT.value
                            if self.classifier.is_loaded
                            else ExtractionMethod.RULE_BASED.value
                        )

                        for rel_data in relations:
                            relation = CausalRelation(
                                id=uuid4(),
                                session_id=session_id,
                                classification_id=classification.id,
                                project_id=session.project_id,
                                relation_type=rel_data["relation_type"],
                                confidence=rel_data["confidence"],
                                cause_source_id=source_id,
                                cause_text=rel_data["cause_text"],
                                effect_source_id=source_id,
                                effect_text=rel_data["effect_text"],
                                causal_marker=rel_data["causal_marker"],
                                extraction_method=extraction_method,
                            )
                            self.db.add(relation)
                            all_relations.append(relation)
                else:
                    non_causal_count += 1

            # Update session with results
            avg_confidence = total_confidence / causal_count if causal_count > 0 else 0.0
            session.complete(
                causal_count=causal_count,
                non_causal_count=non_causal_count,
                relation_count=len(all_relations),
                avg_confidence=avg_confidence
            )

            await self.db.commit()

            logger.info(
                f"Analysis complete for session {session_id}: "
                f"{causal_count} causal, {non_causal_count} non-causal, "
                f"{len(all_relations)} relations extracted"
            )

            return {
                "session_id": str(session_id),
                "status": session.status,
                "input_count": len(sentences),
                "causal_count": causal_count,
                "non_causal_count": non_causal_count,
                "relation_count": len(all_relations),
                "avg_confidence": avg_confidence,
                "causal_percentage": session.get_causal_percentage(),
                "classifications": [
                    {
                        "sentence": c.sentence,
                        "is_causal": c.is_causal,
                        "confidence": c.confidence,
                        "markers": c.markers,
                    }
                    for c in classifications
                ],
                "relations": [
                    {
                        "cause_text": r.cause_text,
                        "effect_text": r.effect_text,
                        "relation_type": r.relation_type,
                        "confidence": r.confidence,
                    }
                    for r in all_relations
                ],
            }

        except Exception as e:
            session.fail(str(e))
            await self.db.commit()
            logger.error(f"Analysis failed for session {session_id}: {e}")
            raise

    # ============== GRAPH OPERATIONS ==============

    async def build_dependency_graph(self, session_id: UUID) -> CausalDependencyGraph:
        """Build and store dependency graph for a session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.relations:
            raise ValueError("No relations found in session")

        # Build graph structure
        graph_data = self.graph_builder.build_graph(session.relations, session_id)

        # Store graph
        graph = CausalDependencyGraph(
            id=uuid4(),
            session_id=session_id,
            project_id=session.project_id,
            name=f"Dependency Graph - {session.name}",
            graph_type=GraphType.CAUSAL.value,
            nodes=graph_data["nodes"],
            edges=graph_data["edges"],
            node_count=graph_data["node_count"],
            edge_count=graph_data["edge_count"],
            critical_path=graph_data["critical_path"],
            root_nodes=graph_data["root_nodes"],
            leaf_nodes=graph_data["leaf_nodes"],
            cycles=graph_data["cycles"],
            topological_order=graph_data["topological_order"],
            suggested_sprint_order=graph_data["suggested_sprint_order"],
            graph_format=GraphFormat.JSON.value,
            serialized_graph=json.dumps(graph_data),
        )

        self.db.add(graph)
        await self.db.commit()
        await self.db.refresh(graph)

        logger.info(
            f"Built dependency graph for session {session_id}: "
            f"{graph.node_count} nodes, {graph.edge_count} edges"
        )

        return graph

    async def get_dependency_graph(self, session_id: UUID) -> Optional[CausalDependencyGraph]:
        """Get dependency graph for a session."""
        result = await self.db.execute(
            select(CausalDependencyGraph)
            .where(CausalDependencyGraph.session_id == session_id)
            .order_by(CausalDependencyGraph.created_at.desc())
        )
        return result.scalar_one_or_none()

    # ============== TEST GENERATION ==============

    async def generate_test_cases(self, session_id: UUID) -> List[CausalTestCase]:
        """Generate test cases for all relations in a session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        test_cases = []

        for relation in session.relations:
            tests_data = self.test_generator.generate_tests(relation)

            for test_data in tests_data:
                test_case = CausalTestCase(
                    id=uuid4(),
                    relation_id=relation.id,
                    session_id=session_id,
                    project_id=session.project_id,
                    test_type=test_data["test_type"],
                    test_name=test_data["test_name"],
                    description=test_data["description"],
                    preconditions=test_data["preconditions"],
                    trigger=test_data["trigger"],
                    expected_result=test_data["expected_result"],
                    test_steps=test_data["test_steps"],
                    priority=test_data["priority"],
                    tags=test_data["tags"],
                    status=TestCaseStatus.GENERATED.value,
                )

                self.db.add(test_case)
                test_cases.append(test_case)

        await self.db.commit()

        logger.info(f"Generated {len(test_cases)} test cases for session {session_id}")
        return test_cases

    async def get_test_cases(
        self,
        session_id: UUID,
        test_type: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[CausalTestCase]:
        """Get test cases for a session with optional filters."""
        query = select(CausalTestCase).where(CausalTestCase.session_id == session_id)

        if test_type:
            query = query.where(CausalTestCase.test_type == test_type)
        if status:
            query = query.where(CausalTestCase.status == status)
        if priority:
            query = query.where(CausalTestCase.priority == priority)

        query = query.order_by(CausalTestCase.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============== RELATION MANAGEMENT ==============

    async def get_relations(
        self,
        session_id: UUID,
        relation_type: Optional[str] = None,
        validated: Optional[bool] = None,
        min_confidence: Optional[float] = None
    ) -> List[CausalRelation]:
        """Get relations for a session with optional filters."""
        query = select(CausalRelation).where(CausalRelation.session_id == session_id)

        if relation_type:
            query = query.where(CausalRelation.relation_type == relation_type)
        if validated is not None:
            query = query.where(CausalRelation.human_validated == validated)
        if min_confidence:
            query = query.where(CausalRelation.confidence >= min_confidence)

        query = query.order_by(CausalRelation.confidence.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def validate_relation(
        self,
        relation_id: UUID,
        approved: bool,
        notes: Optional[str] = None
    ) -> CausalRelation:
        """Validate a causal relation (human review)."""
        result = await self.db.execute(
            select(CausalRelation).where(CausalRelation.id == relation_id)
        )
        relation = result.scalar_one_or_none()

        if not relation:
            raise ValueError(f"Relation {relation_id} not found")

        relation.validate(approved, notes)
        await self.db.commit()
        await self.db.refresh(relation)

        logger.info(f"Validated relation {relation_id}: approved={approved}")
        return relation

    # ============== STATISTICS ==============

    async def get_session_statistics(self, session_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for a session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Relation type distribution
        relation_types = {}
        for relation in session.relations:
            rel_type = relation.relation_type
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1

        # Confidence distribution
        confidence_buckets = {
            "high (>0.8)": 0,
            "medium (0.6-0.8)": 0,
            "low (<0.6)": 0,
        }
        for classification in session.classifications:
            if classification.confidence > 0.8:
                confidence_buckets["high (>0.8)"] += 1
            elif classification.confidence >= 0.6:
                confidence_buckets["medium (0.6-0.8)"] += 1
            else:
                confidence_buckets["low (<0.6)"] += 1

        # Validation status
        validated_count = sum(1 for r in session.relations if r.human_validated)
        approved_count = sum(1 for r in session.relations if r.is_approved())

        return {
            "session_id": str(session_id),
            "status": session.status,
            "input_count": session.input_count,
            "causal_count": session.causal_count,
            "non_causal_count": session.non_causal_count,
            "relation_count": session.relation_count,
            "causal_percentage": session.get_causal_percentage(),
            "avg_confidence": session.avg_confidence,
            "relation_type_distribution": relation_types,
            "confidence_distribution": confidence_buckets,
            "validation_status": {
                "total": len(session.relations),
                "validated": validated_count,
                "approved": approved_count,
                "pending": len(session.relations) - validated_count,
            },
            "processing_time_ms": session.processing_time_ms,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

    # ============== FINE-TUNING (Week 124) ==============

    async def fine_tune_model(
        self,
        project_id: int,
        use_validated_only: bool = True,
        epochs: int = 3,
        learning_rate: float = 2e-5,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune the BERT model on project-specific validated relations.

        Week 124: Uses human-validated causal relations as training data.

        Args:
            project_id: Project to use for training data
            use_validated_only: Only use human-validated relations
            epochs: Number of training epochs
            learning_rate: Learning rate for fine-tuning
            save_path: Path to save the fine-tuned model

        Returns:
            Training results including accuracy and F1 score
        """
        await self.ensure_model_loaded()

        # Collect training data from validated relations
        query = select(CausalRelation).where(
            CausalRelation.project_id == project_id
        )

        if use_validated_only:
            query = query.where(CausalRelation.human_validated == True)

        result = await self.db.execute(query)
        relations = result.scalars().all()

        if len(relations) < 10:
            raise ValueError(
                f"Not enough training data: {len(relations)} relations. "
                "Need at least 10 validated relations for fine-tuning."
            )

        # Prepare training data from classifications
        train_sentences = []
        train_labels = []

        # Get all classifications for these relations
        classification_ids = [r.classification_id for r in relations if r.classification_id]

        if classification_ids:
            class_query = select(CausalClassification).where(
                CausalClassification.id.in_(classification_ids)
            )
            class_result = await self.db.execute(class_query)
            classifications = class_result.scalars().all()

            for c in classifications:
                train_sentences.append(c.sentence)
                train_labels.append(1 if c.is_causal else 0)

        # Add some non-causal examples for balance
        non_causal_query = select(CausalClassification).where(
            and_(
                CausalClassification.project_id == project_id,
                CausalClassification.is_causal == False
            )
        ).limit(len(train_sentences))

        non_causal_result = await self.db.execute(non_causal_query)
        non_causal = non_causal_result.scalars().all()

        for c in non_causal:
            train_sentences.append(c.sentence)
            train_labels.append(0)

        # Split into train/val (80/20)
        split_idx = int(len(train_sentences) * 0.8)
        val_sentences = train_sentences[split_idx:]
        val_labels = train_labels[split_idx:]
        train_sentences = train_sentences[:split_idx]
        train_labels = train_labels[:split_idx]

        logger.info(
            f"Fine-tuning with {len(train_sentences)} training samples, "
            f"{len(val_sentences)} validation samples"
        )

        # Set default save path
        if save_path is None:
            import os
            save_path = os.path.join(
                settings.PROJECTS_ROOT,
                f"project_{project_id}",
                "models",
                "cira_finetuned"
            )

        # Fine-tune
        results = await self.classifier.fine_tune(
            train_sentences=train_sentences,
            train_labels=train_labels,
            val_sentences=val_sentences,
            val_labels=val_labels,
            epochs=epochs,
            learning_rate=learning_rate,
            save_path=save_path
        )

        logger.info(f"Fine-tuning complete: {results}")
        return results

    async def calibrate_confidence(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Calibrate confidence scores using temperature scaling.

        Week 124: Uses validated relations to find optimal temperature.

        Args:
            project_id: Project to use for calibration data

        Returns:
            Calibration results including optimal temperature
        """
        await self.ensure_model_loaded()

        # Get validated classifications
        query = select(CausalClassification).where(
            and_(
                CausalClassification.project_id == project_id,
                CausalClassification.session_id.in_(
                    select(CausalSession.id).where(
                        CausalSession.project_id == project_id
                    )
                )
            )
        ).limit(500)

        result = await self.db.execute(query)
        classifications = result.scalars().all()

        if len(classifications) < 50:
            raise ValueError(
                f"Not enough data for calibration: {len(classifications)}. "
                "Need at least 50 classified sentences."
            )

        sentences = [c.sentence for c in classifications]
        labels = [1 if c.is_causal else 0 for c in classifications]

        optimal_temp = await self.classifier.calibrate_temperature(
            val_sentences=sentences,
            val_labels=labels
        )

        return {
            "optimal_temperature": optimal_temp,
            "calibration_samples": len(sentences),
            "project_id": project_id,
        }

    async def get_model_status(self) -> Dict[str, Any]:
        """
        Get the current status of the BERT model.

        Week 124: Returns model loading status, configuration, and metadata.
        """
        return {
            "is_loaded": self.classifier.is_loaded,
            "model_name": self.classifier.model_name,
            "model_path": self.classifier.model_path,
            "device": str(self.classifier.device),
            "temperature": self.classifier.temperature,
            "max_length": self.classifier.max_length,
            "batch_size": self.classifier.batch_size,
            "metadata": (
                {
                    "trained_on": self.classifier.metadata.trained_on,
                    "accuracy": self.classifier.metadata.accuracy,
                    "f1_score": self.classifier.metadata.f1_score,
                }
                if self.classifier.metadata
                else None
            ),
            "config": {
                "CIRA_ENABLED": settings.CIRA_ENABLED,
                "CIRA_USE_BERT": settings.CIRA_USE_BERT,
                "CIRA_USE_POS_TAGS": settings.CIRA_USE_POS_TAGS,
                "CIRA_CONFIDENCE_THRESHOLD": settings.CIRA_CONFIDENCE_THRESHOLD,
            }
        }
