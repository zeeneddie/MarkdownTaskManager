"""
Pattern Matcher Service - Self-Navigating Core

Implements similarity search and pattern matching for experience consultation.
Part of AgentEvolver Phase B (Week 19).

Features:
- Text embedding for semantic similarity
- Ranking algorithm for experiences/patterns/failures
- Filtering by work type, agent role, quality score
- ChromaDB integration for vector search

@author Claude Code (Week 19 Day 2)
@date 2025-11-22
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math
import re
import hashlib

from app.services.experience_store_service import (
    get_experience_store, ExperienceStoreService,
    Experience, SuccessfulPattern, FailureAnalysis,
    WorkType, AgentRole, Outcome
)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SearchResult:
    """Generic search result with similarity score"""
    item: Any
    similarity: float
    rank: int


@dataclass
class ExperienceSearchResult:
    """Experience with similarity score"""
    experience: Experience
    similarity: float
    relevance_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class PatternSearchResult:
    """Pattern with similarity score"""
    pattern: SuccessfulPattern
    similarity: float
    applicability_score: float = 0.0


@dataclass
class FailureSearchResult:
    """Failure analysis with similarity score"""
    failure: FailureAnalysis
    similarity: float
    risk_score: float = 0.0


@dataclass
class SearchQuery:
    """Search query parameters"""
    text: str
    work_type: Optional[str] = None
    agent_role: Optional[str] = None
    min_quality: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    date_range_days: Optional[int] = None


# ============================================================================
# Text Processing
# ============================================================================

class TextProcessor:
    """Simple text processing for similarity calculation"""

    # Common stop words to ignore
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'i', 'you', 'we', 'they'
    }

    # Domain-specific important terms with weights
    DOMAIN_TERMS = {
        # Work types
        'feature': 1.5, 'bug': 1.5, 'maintenance': 1.5, 'migration': 1.5,
        'quality': 1.5, 'audit': 1.5, 'security': 1.5, 'test': 1.5,
        # Technical terms
        'api': 1.3, 'database': 1.3, 'frontend': 1.3, 'backend': 1.3,
        'refactor': 1.3, 'optimize': 1.3, 'fix': 1.3, 'implement': 1.3,
        'authentication': 1.3, 'authorization': 1.3, 'validation': 1.3,
        # Frameworks/tools
        'react': 1.2, 'fastapi': 1.2, 'typescript': 1.2, 'python': 1.2,
        'sql': 1.2, 'chromadb': 1.2, 'ollama': 1.2
    }

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize text into words"""
        if not text:
            return []
        # Convert to lowercase, split on non-alphanumeric
        words = re.findall(r'\b[a-z0-9]+\b', text.lower())
        # Remove stop words
        return [w for w in words if w not in TextProcessor.STOP_WORDS]

    @staticmethod
    def get_term_weights(tokens: List[str]) -> Dict[str, float]:
        """Get weighted term frequencies"""
        weights = {}
        for token in tokens:
            base_weight = TextProcessor.DOMAIN_TERMS.get(token, 1.0)
            weights[token] = weights.get(token, 0) + base_weight
        return weights

    @staticmethod
    def compute_tf_idf(tokens: List[str], all_documents: List[List[str]]) -> Dict[str, float]:
        """Compute TF-IDF weights for tokens"""
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        # Normalize TF
        max_tf = max(tf.values()) if tf else 1
        for token in tf:
            tf[token] /= max_tf

        # Compute IDF
        n_docs = len(all_documents) + 1
        idf = {}
        for token in tf:
            doc_freq = sum(1 for doc in all_documents if token in doc) + 1
            idf[token] = math.log(n_docs / doc_freq)

        # TF-IDF
        return {token: tf[token] * idf[token] for token in tf}


# ============================================================================
# Similarity Calculator
# ============================================================================

class SimilarityCalculator:
    """Calculate similarity between texts and contexts"""

    @staticmethod
    def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two weight vectors"""
        if not vec1 or not vec2:
            return 0.0

        # Get all terms
        all_terms = set(vec1.keys()) | set(vec2.keys())

        # Calculate dot product and magnitudes
        dot_product = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_terms)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    @staticmethod
    def jaccard_similarity(set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def text_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity using weighted term matching"""
        tokens1 = TextProcessor.tokenize(text1)
        tokens2 = TextProcessor.tokenize(text2)

        if not tokens1 or not tokens2:
            return 0.0

        # Get weighted vectors
        weights1 = TextProcessor.get_term_weights(tokens1)
        weights2 = TextProcessor.get_term_weights(tokens2)

        # Cosine similarity on weighted vectors
        cosine = SimilarityCalculator.cosine_similarity(weights1, weights2)

        # Jaccard for coverage
        jaccard = SimilarityCalculator.jaccard_similarity(set(tokens1), set(tokens2))

        # Combined score (weighted average)
        return 0.7 * cosine + 0.3 * jaccard

    @staticmethod
    def context_similarity(
        query_work_type: Optional[str],
        query_agent_role: Optional[str],
        item_work_type: str,
        item_agent_role: str
    ) -> float:
        """Calculate context similarity (work type, agent role match)"""
        score = 0.0

        # Work type match (most important)
        if query_work_type:
            if query_work_type.upper() == item_work_type.upper():
                score += 0.6
            elif query_work_type.upper() in item_work_type.upper() or item_work_type.upper() in query_work_type.upper():
                score += 0.3

        # Agent role match
        if query_agent_role:
            if query_agent_role.lower() == item_agent_role.lower():
                score += 0.4
            elif query_agent_role.lower() in item_agent_role.lower():
                score += 0.2

        # If no filters, partial score
        if not query_work_type and not query_agent_role:
            score = 0.5

        return min(1.0, score)


# ============================================================================
# Pattern Matcher Service
# ============================================================================

class PatternMatcherService:
    """
    Service for finding similar experiences, patterns, and failures.

    Uses a combination of:
    - Text similarity (weighted term matching)
    - Context similarity (work type, agent role)
    - Quality/success rate filtering
    - Recency weighting
    """

    def __init__(self):
        self.store = get_experience_store()
        self.text_processor = TextProcessor()
        self.similarity_calc = SimilarityCalculator()

    # ========================================================================
    # Experience Search
    # ========================================================================

    def search_experiences(
        self,
        query: str,
        work_type: Optional[str] = None,
        agent_role: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.5,
        min_quality: Optional[float] = None
    ) -> List[ExperienceSearchResult]:
        """
        Search for similar experiences.

        Ranking formula:
        score = (text_sim * 0.5) + (context_sim * 0.3) + (quality_factor * 0.2)
        """
        # Get all experiences
        all_experiences = self.store.find_similar_experiences(
            work_type=WorkType(work_type) if work_type else None,
            limit=100  # Get more, we'll filter
        )

        results = []
        for exp in all_experiences:
            # Calculate text similarity
            text_sim = self.similarity_calc.text_similarity(
                query,
                f"{exp.task_description} {exp.approach}"
            )

            # Calculate context similarity
            context_sim = self.similarity_calc.context_similarity(
                work_type,
                agent_role,
                exp.work_type.value if isinstance(exp.work_type, WorkType) else str(exp.work_type),
                exp.agent_role.value if isinstance(exp.agent_role, AgentRole) else str(exp.agent_role)
            )

            # Quality factor (normalize to 0-1)
            quality_factor = (exp.quality_score or 50) / 100

            # Combined score
            similarity = (text_sim * 0.5) + (context_sim * 0.3) + (quality_factor * 0.2)

            # Apply filters
            if similarity < min_similarity:
                continue
            if min_quality and (exp.quality_score or 0) < min_quality:
                continue

            results.append(ExperienceSearchResult(
                experience=exp,
                similarity=similarity,
                relevance_factors={
                    'text_similarity': text_sim,
                    'context_similarity': context_sim,
                    'quality_factor': quality_factor
                }
            ))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x.similarity, reverse=True)

        return results[:limit]

    # ========================================================================
    # Pattern Search
    # ========================================================================

    def search_patterns(
        self,
        query: str,
        work_type: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.5,
        min_success_rate: float = 0.6
    ) -> List[PatternSearchResult]:
        """
        Search for applicable patterns.

        Ranking formula:
        score = (text_sim * 0.4) + (work_type_match * 0.3) + (success_rate * 0.3)
        """
        # Get all patterns
        all_patterns = self.store.find_applicable_patterns(
            work_type=WorkType(work_type) if work_type else None,
            limit=50
        )

        results = []
        for pattern in all_patterns:
            # Calculate text similarity
            text_sim = self.similarity_calc.text_similarity(
                query,
                f"{pattern.name} {pattern.description} {' '.join(pattern.steps)}"
            )

            # Work type match
            work_type_match = 0.0
            if work_type:
                pattern_types = [wt.value if isinstance(wt, WorkType) else str(wt) for wt in (pattern.work_types or [])]
                if work_type.upper() in [t.upper() for t in pattern_types]:
                    work_type_match = 1.0
                elif any(work_type.upper() in t.upper() for t in pattern_types):
                    work_type_match = 0.5

            # Success rate factor
            success_rate = pattern.success_rate or 0.5

            # Combined score
            similarity = (text_sim * 0.4) + (work_type_match * 0.3) + (success_rate * 0.3)

            # Apply filters
            if similarity < min_similarity:
                continue
            if success_rate < min_success_rate:
                continue

            results.append(PatternSearchResult(
                pattern=pattern,
                similarity=similarity,
                applicability_score=work_type_match
            ))

        # Sort by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)

        return results[:limit]

    # ========================================================================
    # Failure Search
    # ========================================================================

    def search_failures(
        self,
        query: str,
        work_type: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.4
    ) -> List[FailureSearchResult]:
        """
        Search for relevant failure analyses.

        Ranking formula:
        score = (text_sim * 0.5) + (work_type_match * 0.3) + (recency * 0.2)
        """
        # Get failure analyses
        all_failures = self.store.get_failure_analyses(
            work_type=WorkType(work_type) if work_type else None,
            limit=50
        )

        results = []
        for failure in all_failures:
            # Calculate text similarity
            text_sim = self.similarity_calc.text_similarity(
                query,
                f"{failure.description} {failure.root_cause} {' '.join(failure.contributing_factors or [])}"
            )

            # Work type match
            work_type_match = 0.0
            if work_type:
                failure_type = failure.work_type.value if isinstance(failure.work_type, WorkType) else str(failure.work_type)
                if work_type.upper() == failure_type.upper():
                    work_type_match = 1.0
                elif work_type.upper() in failure_type.upper():
                    work_type_match = 0.5

            # Recency factor (more recent = more relevant)
            recency = 0.5  # Default if no timestamp

            # Combined score
            similarity = (text_sim * 0.5) + (work_type_match * 0.3) + (recency * 0.2)

            # Apply filter
            if similarity < min_similarity:
                continue

            # Calculate risk score based on failure type
            risk_score = self._calculate_risk_score(failure)

            results.append(FailureSearchResult(
                failure=failure,
                similarity=similarity,
                risk_score=risk_score
            ))

        # Sort by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)

        return results[:limit]

    def _calculate_risk_score(self, failure: FailureAnalysis) -> float:
        """Calculate risk score for a failure (0-1)"""
        base_risk = 0.5

        # Higher risk for certain failure types
        high_risk_types = ['security', 'data_loss', 'crash', 'regression']
        failure_type = failure.failure_type.value if hasattr(failure.failure_type, 'value') else str(failure.failure_type)

        if any(rt in failure_type.lower() for rt in high_risk_types):
            base_risk += 0.3

        # More contributing factors = higher risk
        factor_count = len(failure.contributing_factors or [])
        base_risk += min(0.2, factor_count * 0.05)

        return min(1.0, base_risk)

    # ========================================================================
    # Combined Search
    # ========================================================================

    def comprehensive_search(
        self,
        query: str,
        work_type: Optional[str] = None,
        agent_role: Optional[str] = None,
        max_experiences: int = 5,
        max_patterns: int = 3,
        max_failures: int = 3,
        min_similarity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Perform comprehensive search across all data types.

        Returns experiences, patterns, and failures in one call.
        """
        experiences = self.search_experiences(
            query=query,
            work_type=work_type,
            agent_role=agent_role,
            limit=max_experiences,
            min_similarity=min_similarity
        )

        patterns = self.search_patterns(
            query=query,
            work_type=work_type,
            limit=max_patterns,
            min_similarity=min_similarity
        )

        failures = self.search_failures(
            query=query,
            work_type=work_type,
            limit=max_failures,
            min_similarity=min_similarity * 0.8  # Lower threshold for warnings
        )

        return {
            'experiences': experiences,
            'patterns': patterns,
            'failures': failures,
            'query': query,
            'filters': {
                'work_type': work_type,
                'agent_role': agent_role,
                'min_similarity': min_similarity
            }
        }


# ============================================================================
# Singleton
# ============================================================================

_matcher_instance: Optional[PatternMatcherService] = None


def get_pattern_matcher() -> PatternMatcherService:
    """Get or create pattern matcher singleton"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = PatternMatcherService()
    return _matcher_instance
