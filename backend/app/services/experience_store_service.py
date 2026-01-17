"""
Experience Store Service

Week 17: AgentEvolver Integration - Experience Storage
Based on: github.com/zeeneddie/AgentEvolver

Manages 5 ChromaDB collections for agent learning:
1. agent_experiences - Cross-task learnings per agent
2. successful_patterns - Reusable success patterns
3. failure_analysis - What went wrong and why
4. estimation_accuracy - Predicted vs actual comparison
5. quality_metrics - Code quality over time

Author: Claude Code (Week 17 Day 2)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import logging
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class AgentRole(str, Enum):
    FEATURE_ARCHITECT = "Feature Architect"
    MAINTENANCE_SPECIALIST = "Maintenance Specialist"
    QUALITY_INSPECTOR = "Quality Inspector"
    BUG_HUNTER = "Bug Hunter"
    ESTIMATION_ENGINE = "Estimation Engine"
    TEST_ENGINEER = "Test Engineer"
    MIGRATION_ARCHITECT = "Migration Architect"
    DOCUMENTATION_WRITER = "Documentation Writer"
    PRODUCT_OWNER = "Product Owner"
    PROJECT_LEAD = "Project Lead"


class WorkType(str, Enum):
    NEW_FEATURE = "NEW_FEATURE"
    MAINTENANCE = "MAINTENANCE"
    BUG = "BUG"
    QUALITY_AUDIT = "QUALITY_AUDIT"
    ENHANCEMENT = "ENHANCEMENT"
    MIGRATION = "MIGRATION"
    QUALITY_IMPROVEMENT = "QUALITY_IMPROVEMENT"
    TESTING = "TESTING"
    PROJECT_DEFINITION = "PROJECT_DEFINITION"


class Outcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class FailureType(str, Enum):
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    QUALITY = "quality"
    LOGIC = "logic"
    UNKNOWN = "unknown"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class KeyDecision:
    """A key decision made during task execution"""
    decision: str
    reasoning: str
    alternatives: List[str]
    outcome: str  # 'positive', 'neutral', 'negative'
    impact_score: float  # -1 to 1


@dataclass
class Experience:
    """A single experience record"""
    id: str
    agent_id: str
    agent_role: AgentRole
    work_type: WorkType
    task_description: str
    approach: str
    outcome: Outcome
    lessons_learned: List[str]
    key_decisions: List[KeyDecision]
    duration: int  # milliseconds
    quality_score: float  # 0-100
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_role": self.agent_role.value,
            "work_type": self.work_type.value,
            "task_description": self.task_description,
            "approach": self.approach,
            "outcome": self.outcome.value,
            "lessons_learned": self.lessons_learned,
            "key_decisions": [asdict(kd) for kd in self.key_decisions],
            "duration": self.duration,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class SuccessfulPattern:
    """A reusable success pattern"""
    id: str
    name: str
    description: str
    work_types: List[WorkType]
    applicable_contexts: List[str]
    steps: List[str]
    success_count: int
    failure_count: int
    average_quality: float
    created_at: datetime
    last_used: datetime
    created_by: str  # agent_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "work_types": [wt.value for wt in self.work_types],
            "applicable_contexts": self.applicable_contexts,
            "steps": self.steps,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_quality": self.average_quality,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "created_by": self.created_by
        }

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class FailureAnalysis:
    """Analysis of a failed task"""
    id: str
    agent_id: str
    task_id: str
    work_type: WorkType
    failure_type: FailureType
    root_cause: str
    contributing_factors: List[str]
    prevention_strategies: List[str]
    similar_failures: List[str]  # IDs of related failures
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "work_type": self.work_type.value,
            "failure_type": self.failure_type.value,
            "root_cause": self.root_cause,
            "contributing_factors": self.contributing_factors,
            "prevention_strategies": self.prevention_strategies,
            "similar_failures": self.similar_failures,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EstimationAccuracy:
    """Record of estimation accuracy"""
    id: str
    agent_id: str
    task_id: str
    work_type: WorkType
    estimated_hours: float
    actual_hours: float
    estimated_complexity: Complexity
    actual_complexity: Complexity
    factors: List[str]
    underestimated_aspects: List[str]
    overestimated_aspects: List[str]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "work_type": self.work_type.value,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "estimated_complexity": self.estimated_complexity.value,
            "actual_complexity": self.actual_complexity.value,
            "factors": self.factors,
            "underestimated_aspects": self.underestimated_aspects,
            "overestimated_aspects": self.overestimated_aspects,
            "timestamp": self.timestamp.isoformat()
        }

    @property
    def accuracy_percent(self) -> float:
        """Calculate estimation accuracy as percentage"""
        if self.actual_hours == 0:
            return 100.0 if self.estimated_hours == 0 else 0.0
        error = abs(self.estimated_hours - self.actual_hours) / self.actual_hours
        return max(0, 100 - (error * 100))


@dataclass
class QualityMetricsRecord:
    """Record of code quality metrics"""
    id: str
    agent_id: str
    task_id: str
    work_type: WorkType
    code_quality_score: float  # 0-100
    test_coverage: Optional[float]  # 0-100
    linting_errors: int
    type_errors: int
    security_issues: int
    performance_score: Optional[float]  # 0-100
    documentation_score: Optional[float]  # 0-100
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "work_type": self.work_type.value,
            "code_quality_score": self.code_quality_score,
            "test_coverage": self.test_coverage,
            "linting_errors": self.linting_errors,
            "type_errors": self.type_errors,
            "security_issues": self.security_issues,
            "performance_score": self.performance_score,
            "documentation_score": self.documentation_score,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# EXPERIENCE STORE SERVICE
# ============================================================================

class ExperienceStoreService:
    """
    Service for managing agent experiences in ChromaDB.

    Provides CRUD operations for 5 collections:
    1. agent_experiences
    2. successful_patterns
    3. failure_analysis
    4. estimation_accuracy
    5. quality_metrics
    """

    # Collection names
    EXPERIENCES = "agent_experiences"
    PATTERNS = "successful_patterns"
    FAILURES = "failure_analysis"
    ESTIMATIONS = "estimation_accuracy"
    QUALITY = "quality_metrics"

    def __init__(self, chroma_client=None, embedding_service=None):
        """
        Initialize the experience store.

        Args:
            chroma_client: ChromaDB client (optional, creates mock if None)
            embedding_service: Service for generating embeddings
        """
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service
        self._collections: Dict[str, Any] = {}
        self._mock_data: Dict[str, List[Dict]] = {
            self.EXPERIENCES: [],
            self.PATTERNS: [],
            self.FAILURES: [],
            self.ESTIMATIONS: [],
            self.QUALITY: []
        }
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize ChromaDB collections"""
        try:
            if self.chroma_client:
                # Create or get collections
                self._collections[self.EXPERIENCES] = self.chroma_client.get_or_create_collection(
                    name=self.EXPERIENCES,
                    metadata={"description": "Cross-task learnings per agent"}
                )
                self._collections[self.PATTERNS] = self.chroma_client.get_or_create_collection(
                    name=self.PATTERNS,
                    metadata={"description": "Successful patterns that can be reused"}
                )
                self._collections[self.FAILURES] = self.chroma_client.get_or_create_collection(
                    name=self.FAILURES,
                    metadata={"description": "Failure analysis for learning"}
                )
                self._collections[self.ESTIMATIONS] = self.chroma_client.get_or_create_collection(
                    name=self.ESTIMATIONS,
                    metadata={"description": "Estimation accuracy tracking"}
                )
                self._collections[self.QUALITY] = self.chroma_client.get_or_create_collection(
                    name=self.QUALITY,
                    metadata={"description": "Code quality metrics over time"}
                )
                logger.info("Experience store initialized with ChromaDB")
            else:
                logger.info("Experience store initialized with in-memory mock")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize experience store: {e}")
            return False

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.embedding_service:
            return self.embedding_service.embed(text)
        # Mock embedding (random 384-dim vector normalized)
        import random
        vec = [random.gauss(0, 1) for _ in range(384)]
        norm = sum(x*x for x in vec) ** 0.5
        return [x / norm for x in vec]

    # =========================================================================
    # EXPERIENCE OPERATIONS
    # =========================================================================

    async def add_experience(self, experience: Experience) -> str:
        """Add a new experience to the store"""
        doc = experience.to_dict()
        doc_text = f"{experience.task_description} {experience.approach} {' '.join(experience.lessons_learned)}"

        if self.chroma_client and self.EXPERIENCES in self._collections:
            embedding = self._generate_embedding(doc_text)
            self._collections[self.EXPERIENCES].add(
                ids=[experience.id],
                documents=[doc_text],
                embeddings=[embedding],
                metadatas=[doc]
            )
        else:
            self._mock_data[self.EXPERIENCES].append(doc)

        logger.info(f"Added experience {experience.id} for agent {experience.agent_id}")
        return experience.id

    async def get_experience(self, experience_id: str) -> Optional[Experience]:
        """Get an experience by ID"""
        if self.chroma_client and self.EXPERIENCES in self._collections:
            result = self._collections[self.EXPERIENCES].get(ids=[experience_id])
            if result and result['metadatas']:
                return self._dict_to_experience(result['metadatas'][0])
        else:
            for exp in self._mock_data[self.EXPERIENCES]:
                if exp['id'] == experience_id:
                    return self._dict_to_experience(exp)
        return None

    async def find_similar_experiences(
        self,
        task_description: str,
        work_type: Optional[WorkType] = None,
        agent_role: Optional[AgentRole] = None,
        limit: int = 10
    ) -> List[Tuple[Experience, float]]:
        """Find experiences similar to the given task description"""
        results = []

        if self.chroma_client and self.EXPERIENCES in self._collections:
            embedding = self._generate_embedding(task_description)
            where_filter = {}
            if work_type:
                where_filter["work_type"] = work_type.value
            if agent_role:
                where_filter["agent_role"] = agent_role.value

            query_result = self._collections[self.EXPERIENCES].query(
                query_embeddings=[embedding],
                n_results=limit,
                where=where_filter if where_filter else None
            )

            if query_result and query_result['metadatas']:
                for i, meta in enumerate(query_result['metadatas'][0]):
                    experience = self._dict_to_experience(meta)
                    distance = query_result['distances'][0][i] if query_result['distances'] else 0
                    # Convert distance to similarity (assuming cosine distance)
                    similarity = 1 - distance
                    results.append((experience, similarity))
        else:
            # Mock search: simple keyword matching
            keywords = task_description.lower().split()
            for exp_dict in self._mock_data[self.EXPERIENCES]:
                if work_type and exp_dict['work_type'] != work_type.value:
                    continue
                if agent_role and exp_dict['agent_role'] != agent_role.value:
                    continue

                exp_text = f"{exp_dict['task_description']} {exp_dict['approach']}".lower()
                matches = sum(1 for kw in keywords if kw in exp_text)
                if matches > 0:
                    similarity = matches / len(keywords)
                    experience = self._dict_to_experience(exp_dict)
                    results.append((experience, similarity))

            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:limit]

        return results

    async def get_agent_experiences(
        self,
        agent_id: str,
        work_type: Optional[WorkType] = None,
        outcome: Optional[Outcome] = None,
        limit: int = 50
    ) -> List[Experience]:
        """Get all experiences for an agent"""
        results = []

        if self.chroma_client and self.EXPERIENCES in self._collections:
            where_filter = {"agent_id": agent_id}
            if work_type:
                where_filter["work_type"] = work_type.value
            if outcome:
                where_filter["outcome"] = outcome.value

            query_result = self._collections[self.EXPERIENCES].get(
                where=where_filter,
                limit=limit
            )

            if query_result and query_result['metadatas']:
                for meta in query_result['metadatas']:
                    results.append(self._dict_to_experience(meta))
        else:
            for exp_dict in self._mock_data[self.EXPERIENCES]:
                if exp_dict['agent_id'] != agent_id:
                    continue
                if work_type and exp_dict['work_type'] != work_type.value:
                    continue
                if outcome and exp_dict['outcome'] != outcome.value:
                    continue
                results.append(self._dict_to_experience(exp_dict))
                if len(results) >= limit:
                    break

        return results

    def _dict_to_experience(self, d: Dict) -> Experience:
        """Convert dictionary to Experience object"""
        return Experience(
            id=d['id'],
            agent_id=d['agent_id'],
            agent_role=AgentRole(d['agent_role']),
            work_type=WorkType(d['work_type']),
            task_description=d['task_description'],
            approach=d['approach'],
            outcome=Outcome(d['outcome']),
            lessons_learned=d['lessons_learned'],
            key_decisions=[KeyDecision(**kd) for kd in d.get('key_decisions', [])],
            duration=d['duration'],
            quality_score=d['quality_score'],
            timestamp=datetime.fromisoformat(d['timestamp']) if isinstance(d['timestamp'], str) else d['timestamp'],
            metadata=d.get('metadata', {})
        )

    # =========================================================================
    # PATTERN OPERATIONS
    # =========================================================================

    async def add_pattern(self, pattern: SuccessfulPattern) -> str:
        """Add a new successful pattern"""
        doc = pattern.to_dict()
        doc_text = f"{pattern.name} {pattern.description} {' '.join(pattern.steps)}"

        if self.chroma_client and self.PATTERNS in self._collections:
            embedding = self._generate_embedding(doc_text)
            self._collections[self.PATTERNS].add(
                ids=[pattern.id],
                documents=[doc_text],
                embeddings=[embedding],
                metadatas=[doc]
            )
        else:
            self._mock_data[self.PATTERNS].append(doc)

        logger.info(f"Added pattern {pattern.id}: {pattern.name}")
        return pattern.id

    async def find_applicable_patterns(
        self,
        context: str,
        work_type: WorkType,
        limit: int = 5
    ) -> List[Tuple[SuccessfulPattern, float]]:
        """Find patterns applicable to the given context"""
        results = []

        if self.chroma_client and self.PATTERNS in self._collections:
            embedding = self._generate_embedding(context)
            query_result = self._collections[self.PATTERNS].query(
                query_embeddings=[embedding],
                n_results=limit * 2  # Get more, filter later
            )

            if query_result and query_result['metadatas']:
                for i, meta in enumerate(query_result['metadatas'][0]):
                    # Check if work_type matches
                    if work_type.value in meta.get('work_types', []):
                        pattern = self._dict_to_pattern(meta)
                        distance = query_result['distances'][0][i] if query_result['distances'] else 0
                        similarity = 1 - distance
                        results.append((pattern, similarity))
        else:
            for pat_dict in self._mock_data[self.PATTERNS]:
                if work_type.value in pat_dict.get('work_types', []):
                    pattern = self._dict_to_pattern(pat_dict)
                    # Simple relevance based on success rate
                    relevance = pattern.success_rate
                    results.append((pattern, relevance))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def update_pattern_usage(
        self,
        pattern_id: str,
        success: bool,
        quality_score: float
    ) -> bool:
        """Update pattern usage statistics"""
        if self.chroma_client and self.PATTERNS in self._collections:
            result = self._collections[self.PATTERNS].get(ids=[pattern_id])
            if result and result['metadatas']:
                meta = result['metadatas'][0]
                if success:
                    meta['success_count'] += 1
                else:
                    meta['failure_count'] += 1
                # Update average quality
                total = meta['success_count'] + meta['failure_count']
                meta['average_quality'] = (
                    (meta['average_quality'] * (total - 1) + quality_score) / total
                )
                meta['last_used'] = datetime.now(timezone.utc).isoformat()

                self._collections[self.PATTERNS].update(
                    ids=[pattern_id],
                    metadatas=[meta]
                )
                return True
        else:
            for pat in self._mock_data[self.PATTERNS]:
                if pat['id'] == pattern_id:
                    if success:
                        pat['success_count'] += 1
                    else:
                        pat['failure_count'] += 1
                    total = pat['success_count'] + pat['failure_count']
                    pat['average_quality'] = (
                        (pat['average_quality'] * (total - 1) + quality_score) / total
                    )
                    pat['last_used'] = datetime.now(timezone.utc).isoformat()
                    return True
        return False

    def _dict_to_pattern(self, d: Dict) -> SuccessfulPattern:
        """Convert dictionary to SuccessfulPattern object"""
        return SuccessfulPattern(
            id=d['id'],
            name=d['name'],
            description=d['description'],
            work_types=[WorkType(wt) for wt in d['work_types']],
            applicable_contexts=d['applicable_contexts'],
            steps=d['steps'],
            success_count=d['success_count'],
            failure_count=d['failure_count'],
            average_quality=d['average_quality'],
            created_at=datetime.fromisoformat(d['created_at']) if isinstance(d['created_at'], str) else d['created_at'],
            last_used=datetime.fromisoformat(d['last_used']) if isinstance(d['last_used'], str) else d['last_used'],
            created_by=d['created_by']
        )

    # =========================================================================
    # FAILURE ANALYSIS OPERATIONS
    # =========================================================================

    async def add_failure_analysis(self, failure: FailureAnalysis) -> str:
        """Add a failure analysis record"""
        doc = failure.to_dict()
        doc_text = f"{failure.root_cause} {' '.join(failure.contributing_factors)}"

        if self.chroma_client and self.FAILURES in self._collections:
            embedding = self._generate_embedding(doc_text)
            self._collections[self.FAILURES].add(
                ids=[failure.id],
                documents=[doc_text],
                embeddings=[embedding],
                metadatas=[doc]
            )
        else:
            self._mock_data[self.FAILURES].append(doc)

        logger.info(f"Added failure analysis {failure.id}")
        return failure.id

    async def find_similar_failures(
        self,
        root_cause: str,
        work_type: Optional[WorkType] = None,
        limit: int = 5
    ) -> List[Tuple[FailureAnalysis, float]]:
        """Find similar past failures"""
        results = []

        if self.chroma_client and self.FAILURES in self._collections:
            embedding = self._generate_embedding(root_cause)
            where_filter = {}
            if work_type:
                where_filter["work_type"] = work_type.value

            query_result = self._collections[self.FAILURES].query(
                query_embeddings=[embedding],
                n_results=limit,
                where=where_filter if where_filter else None
            )

            if query_result and query_result['metadatas']:
                for i, meta in enumerate(query_result['metadatas'][0]):
                    failure = self._dict_to_failure(meta)
                    distance = query_result['distances'][0][i] if query_result['distances'] else 0
                    similarity = 1 - distance
                    results.append((failure, similarity))
        else:
            keywords = root_cause.lower().split()
            for fail_dict in self._mock_data[self.FAILURES]:
                if work_type and fail_dict['work_type'] != work_type.value:
                    continue
                fail_text = f"{fail_dict['root_cause']}".lower()
                matches = sum(1 for kw in keywords if kw in fail_text)
                if matches > 0:
                    similarity = matches / len(keywords)
                    failure = self._dict_to_failure(fail_dict)
                    results.append((failure, similarity))

            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:limit]

        return results

    def _dict_to_failure(self, d: Dict) -> FailureAnalysis:
        """Convert dictionary to FailureAnalysis object"""
        return FailureAnalysis(
            id=d['id'],
            agent_id=d['agent_id'],
            task_id=d['task_id'],
            work_type=WorkType(d['work_type']),
            failure_type=FailureType(d['failure_type']),
            root_cause=d['root_cause'],
            contributing_factors=d['contributing_factors'],
            prevention_strategies=d['prevention_strategies'],
            similar_failures=d['similar_failures'],
            timestamp=datetime.fromisoformat(d['timestamp']) if isinstance(d['timestamp'], str) else d['timestamp']
        )

    # =========================================================================
    # ESTIMATION ACCURACY OPERATIONS
    # =========================================================================

    async def add_estimation_accuracy(self, estimation: EstimationAccuracy) -> str:
        """Add an estimation accuracy record"""
        doc = estimation.to_dict()

        if self.chroma_client and self.ESTIMATIONS in self._collections:
            self._collections[self.ESTIMATIONS].add(
                ids=[estimation.id],
                documents=[f"Estimated: {estimation.estimated_hours}h, Actual: {estimation.actual_hours}h"],
                metadatas=[doc]
            )
        else:
            self._mock_data[self.ESTIMATIONS].append(doc)

        logger.info(f"Added estimation accuracy {estimation.id}: {estimation.accuracy_percent:.1f}%")
        return estimation.id

    async def get_agent_estimation_stats(
        self,
        agent_id: str,
        work_type: Optional[WorkType] = None
    ) -> Dict[str, Any]:
        """Get estimation statistics for an agent"""
        records = []

        if self.chroma_client and self.ESTIMATIONS in self._collections:
            where_filter = {"agent_id": agent_id}
            if work_type:
                where_filter["work_type"] = work_type.value

            result = self._collections[self.ESTIMATIONS].get(where=where_filter)
            if result and result['metadatas']:
                records = result['metadatas']
        else:
            for est in self._mock_data[self.ESTIMATIONS]:
                if est['agent_id'] != agent_id:
                    continue
                if work_type and est['work_type'] != work_type.value:
                    continue
                records.append(est)

        if not records:
            return {
                "total_estimates": 0,
                "average_accuracy": 0,
                "underestimate_rate": 0,
                "overestimate_rate": 0,
                "common_underestimated": [],
                "common_overestimated": []
            }

        # Calculate statistics
        accuracies = []
        underestimates = 0
        overestimates = 0
        underestimated_aspects = []
        overestimated_aspects = []

        for rec in records:
            est_h = rec['estimated_hours']
            act_h = rec['actual_hours']
            if act_h > 0:
                accuracy = max(0, 100 - abs(est_h - act_h) / act_h * 100)
                accuracies.append(accuracy)
                if est_h < act_h:
                    underestimates += 1
                    underestimated_aspects.extend(rec.get('underestimated_aspects', []))
                elif est_h > act_h:
                    overestimates += 1
                    overestimated_aspects.extend(rec.get('overestimated_aspects', []))

        total = len(records)
        return {
            "total_estimates": total,
            "average_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
            "underestimate_rate": underestimates / total if total > 0 else 0,
            "overestimate_rate": overestimates / total if total > 0 else 0,
            "common_underestimated": self._get_top_items(underestimated_aspects, 5),
            "common_overestimated": self._get_top_items(overestimated_aspects, 5)
        }

    def _get_top_items(self, items: List[str], n: int) -> List[str]:
        """Get top n most common items"""
        from collections import Counter
        return [item for item, _ in Counter(items).most_common(n)]

    # =========================================================================
    # QUALITY METRICS OPERATIONS
    # =========================================================================

    async def add_quality_metrics(self, metrics: QualityMetricsRecord) -> str:
        """Add a quality metrics record"""
        doc = metrics.to_dict()

        if self.chroma_client and self.QUALITY in self._collections:
            self._collections[self.QUALITY].add(
                ids=[metrics.id],
                documents=[f"Quality: {metrics.code_quality_score}, Coverage: {metrics.test_coverage}"],
                metadatas=[doc]
            )
        else:
            self._mock_data[self.QUALITY].append(doc)

        logger.info(f"Added quality metrics {metrics.id}: score={metrics.code_quality_score}")
        return metrics.id

    async def get_quality_trend(
        self,
        agent_id: str,
        work_type: Optional[WorkType] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get quality trend for an agent over time"""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        records = []

        if self.chroma_client and self.QUALITY in self._collections:
            where_filter = {"agent_id": agent_id}
            if work_type:
                where_filter["work_type"] = work_type.value

            result = self._collections[self.QUALITY].get(where=where_filter)
            if result and result['metadatas']:
                for meta in result['metadatas']:
                    ts = datetime.fromisoformat(meta['timestamp']) if isinstance(meta['timestamp'], str) else meta['timestamp']
                    if ts >= cutoff:
                        records.append(meta)
        else:
            for qm in self._mock_data[self.QUALITY]:
                if qm['agent_id'] != agent_id:
                    continue
                if work_type and qm['work_type'] != work_type.value:
                    continue
                ts = datetime.fromisoformat(qm['timestamp']) if isinstance(qm['timestamp'], str) else qm['timestamp']
                if ts >= cutoff:
                    records.append(qm)

        if not records:
            return {
                "total_records": 0,
                "average_quality": 0,
                "trend": "stable",
                "average_coverage": None,
                "error_trend": "stable"
            }

        # Sort by timestamp
        records.sort(key=lambda x: x['timestamp'])

        # Calculate metrics
        qualities = [r['code_quality_score'] for r in records]
        coverages = [r['test_coverage'] for r in records if r.get('test_coverage') is not None]
        errors = [r['linting_errors'] + r['type_errors'] for r in records]

        # Determine trends
        def get_trend(values: List[float]) -> str:
            if len(values) < 2:
                return "stable"
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            diff = second_half - first_half
            if diff > 5:
                return "improving"
            elif diff < -5:
                return "declining"
            return "stable"

        return {
            "total_records": len(records),
            "average_quality": sum(qualities) / len(qualities),
            "trend": get_trend(qualities),
            "average_coverage": sum(coverages) / len(coverages) if coverages else None,
            "error_trend": get_trend([-e for e in errors])  # Negative because fewer errors = improving
        }

    # =========================================================================
    # AGGREGATE OPERATIONS
    # =========================================================================

    async def get_agent_performance_summary(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive performance summary for an agent"""
        experiences = await self.get_agent_experiences(agent_id, limit=100)
        estimation_stats = await self.get_agent_estimation_stats(agent_id)
        quality_trend = await self.get_quality_trend(agent_id)

        if not experiences:
            return {
                "agent_id": agent_id,
                "total_tasks": 0,
                "success_rate": 0,
                "average_quality": 0,
                "estimation_accuracy": 0,
                "quality_trend": "unknown"
            }

        # Calculate from experiences
        total = len(experiences)
        successes = sum(1 for e in experiences if e.outcome == Outcome.SUCCESS)
        avg_quality = sum(e.quality_score for e in experiences) / total

        return {
            "agent_id": agent_id,
            "total_tasks": total,
            "success_rate": successes / total,
            "average_quality": avg_quality,
            "estimation_accuracy": estimation_stats.get('average_accuracy', 0),
            "quality_trend": quality_trend.get('trend', 'unknown'),
            "experience_count": total,
            "pattern_usage": 0  # TODO: Track pattern usage
        }

    async def get_collection_stats(self) -> Dict[str, int]:
        """Get counts for all collections"""
        stats = {}

        for collection_name in [self.EXPERIENCES, self.PATTERNS, self.FAILURES, self.ESTIMATIONS, self.QUALITY]:
            if self.chroma_client and collection_name in self._collections:
                stats[collection_name] = self._collections[collection_name].count()
            else:
                stats[collection_name] = len(self._mock_data.get(collection_name, []))

        return stats


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_experience_store: Optional[ExperienceStoreService] = None


def get_experience_store() -> ExperienceStoreService:
    """Get or create the experience store singleton"""
    global _experience_store
    if _experience_store is None:
        _experience_store = ExperienceStoreService()
    return _experience_store


async def initialize_experience_store(
    chroma_client=None,
    embedding_service=None
) -> ExperienceStoreService:
    """Initialize the experience store with optional ChromaDB client"""
    global _experience_store
    _experience_store = ExperienceStoreService(chroma_client, embedding_service)
    await _experience_store.initialize()
    return _experience_store
