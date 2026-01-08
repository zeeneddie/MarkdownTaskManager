"""
Rule Deduplication Service - Week 101

Detects and removes duplicate business rules extracted from code.
Supports both exact matching and semantic similarity detection.

Usage:
    service = RuleDeduplicationService()

    # Deduplicate a list of rules
    unique_rules = service.deduplicate(extracted_rules)

    # Find duplicates with details
    duplicates = service.find_duplicates(extracted_rules)

    # Check if two rules are duplicates
    is_dup = service.are_duplicates(rule1, rule2)
"""

import hashlib
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


class DuplicateType(Enum):
    """Type of duplicate detection."""
    EXACT = "exact"              # Identical text
    NORMALIZED = "normalized"    # Same after normalization
    SEMANTIC = "semantic"        # Same meaning, different words
    STRUCTURAL = "structural"    # Same structure/pattern


@dataclass
class ExtractedRule:
    """Represents an extracted business rule."""
    id: str
    text: str
    source_file: str
    source_line: int
    rule_type: str  # validation, authorization, calculation, workflow
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class DuplicateMatch:
    """Represents a duplicate match between rules."""
    rule1_id: str
    rule2_id: str
    duplicate_type: DuplicateType
    similarity_score: float
    details: str


@dataclass
class DeduplicationResult:
    """Result of deduplication process."""
    unique_rules: List[ExtractedRule]
    duplicate_groups: List[List[str]]  # Groups of duplicate rule IDs
    matches: List[DuplicateMatch]
    total_input: int
    total_unique: int
    total_duplicates: int


class RuleDeduplicationService:
    """
    Service for detecting and removing duplicate business rules.

    Supports multiple detection strategies:
    - Exact: Identical rule text
    - Normalized: Same text after normalization (whitespace, case)
    - Semantic: Similar meaning detected via text similarity
    - Structural: Same pattern/structure with different values
    """

    # Configurable thresholds
    SEMANTIC_THRESHOLD = 0.85  # Minimum similarity for semantic match
    STRUCTURAL_THRESHOLD = 0.75  # Minimum similarity for structural match

    # Common patterns to normalize
    NORMALIZATION_PATTERNS = [
        (r"\s+", " "),           # Multiple whitespace to single space
        (r"['\"]", ""),          # Remove quotes
        (r"\b(the|a|an)\b", ""), # Remove articles
        (r"\bshould\b", "must"), # Normalize modals
        (r"\bshall\b", "must"),
        (r"\bneeds? to\b", "must"),
        (r"\brequired to\b", "must"),
    ]

    # Structural patterns for parameterized rules
    STRUCTURAL_PATTERNS = [
        # "X must be between Y and Z"
        (r"(\w+)\s+must\s+be\s+between\s+(\d+)\s+and\s+(\d+)",
         "{field} must be between {min} and {max}"),
        # "X cannot exceed Y"
        (r"(\w+)\s+cannot\s+exceed\s+(\d+)",
         "{field} cannot exceed {limit}"),
        # "X is required"
        (r"(\w+)\s+is\s+required",
         "{field} is required"),
        # "Only X can Y"
        (r"only\s+(\w+)\s+can\s+(\w+)",
         "only {role} can {action}"),
        # "X must have Y"
        (r"(\w+)\s+must\s+have\s+(?:a\s+)?(\w+)",
         "{entity} must have {attribute}"),
    ]

    def __init__(
        self,
        semantic_threshold: float = None,
        structural_threshold: float = None,
    ):
        """
        Initialize the deduplication service.

        Args:
            semantic_threshold: Custom threshold for semantic matching
            structural_threshold: Custom threshold for structural matching
        """
        self.semantic_threshold = semantic_threshold or self.SEMANTIC_THRESHOLD
        self.structural_threshold = structural_threshold or self.STRUCTURAL_THRESHOLD

        # Cache for normalized texts
        self._normalized_cache: Dict[str, str] = {}
        self._hash_cache: Dict[str, str] = {}
        self._structural_cache: Dict[str, str] = {}

    # =========================================================================
    # Main API
    # =========================================================================

    def deduplicate(
        self,
        rules: List[ExtractedRule],
        strategies: Optional[List[DuplicateType]] = None,
    ) -> DeduplicationResult:
        """
        Remove duplicate rules from a list.

        Args:
            rules: List of extracted rules
            strategies: Duplicate detection strategies to use
                       (default: all strategies)

        Returns:
            DeduplicationResult with unique rules and duplicate info
        """
        if strategies is None:
            strategies = list(DuplicateType)

        # Find all duplicates
        matches = self.find_duplicates(rules, strategies)

        # Build duplicate groups using Union-Find
        groups = self._build_duplicate_groups(rules, matches)

        # Select representative from each group (highest confidence)
        unique_rules = []
        seen_groups: Set[int] = set()

        rule_to_group = {}
        for i, group in enumerate(groups):
            for rule_id in group:
                rule_to_group[rule_id] = i

        for rule in rules:
            group_id = rule_to_group.get(rule.id, -1)
            if group_id == -1 or group_id not in seen_groups:
                unique_rules.append(rule)
                if group_id != -1:
                    seen_groups.add(group_id)

        # Sort unique rules by confidence
        unique_rules.sort(key=lambda r: r.confidence, reverse=True)

        return DeduplicationResult(
            unique_rules=unique_rules,
            duplicate_groups=groups,
            matches=matches,
            total_input=len(rules),
            total_unique=len(unique_rules),
            total_duplicates=len(rules) - len(unique_rules),
        )

    def find_duplicates(
        self,
        rules: List[ExtractedRule],
        strategies: Optional[List[DuplicateType]] = None,
    ) -> List[DuplicateMatch]:
        """
        Find all duplicate pairs in a list of rules.

        Args:
            rules: List of extracted rules
            strategies: Strategies to use for detection

        Returns:
            List of DuplicateMatch objects
        """
        if strategies is None:
            strategies = list(DuplicateType)

        matches: List[DuplicateMatch] = []

        # Compare all pairs
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i + 1:]:
                match = self._check_duplicate_pair(rule1, rule2, strategies)
                if match:
                    matches.append(match)

        return matches

    def are_duplicates(
        self,
        rule1: ExtractedRule,
        rule2: ExtractedRule,
        strategies: Optional[List[DuplicateType]] = None,
    ) -> Tuple[bool, Optional[DuplicateMatch]]:
        """
        Check if two rules are duplicates.

        Args:
            rule1: First rule
            rule2: Second rule
            strategies: Strategies to use

        Returns:
            Tuple of (is_duplicate, match_details)
        """
        if strategies is None:
            strategies = list(DuplicateType)

        match = self._check_duplicate_pair(rule1, rule2, strategies)
        return (match is not None, match)

    # =========================================================================
    # Detection Strategies
    # =========================================================================

    def _check_duplicate_pair(
        self,
        rule1: ExtractedRule,
        rule2: ExtractedRule,
        strategies: List[DuplicateType],
    ) -> Optional[DuplicateMatch]:
        """Check if two rules are duplicates using given strategies."""

        # Try exact match first (fastest)
        if DuplicateType.EXACT in strategies:
            if self._is_exact_match(rule1.text, rule2.text):
                return DuplicateMatch(
                    rule1_id=rule1.id,
                    rule2_id=rule2.id,
                    duplicate_type=DuplicateType.EXACT,
                    similarity_score=1.0,
                    details="Identical text",
                )

        # Try normalized match
        if DuplicateType.NORMALIZED in strategies:
            if self._is_normalized_match(rule1.text, rule2.text):
                return DuplicateMatch(
                    rule1_id=rule1.id,
                    rule2_id=rule2.id,
                    duplicate_type=DuplicateType.NORMALIZED,
                    similarity_score=1.0,
                    details="Same text after normalization",
                )

        # Try structural match
        if DuplicateType.STRUCTURAL in strategies:
            is_structural, pattern = self._is_structural_match(rule1.text, rule2.text)
            if is_structural:
                return DuplicateMatch(
                    rule1_id=rule1.id,
                    rule2_id=rule2.id,
                    duplicate_type=DuplicateType.STRUCTURAL,
                    similarity_score=0.9,
                    details=f"Same structure: {pattern}",
                )

        # Try semantic match (slowest)
        if DuplicateType.SEMANTIC in strategies:
            similarity = self._semantic_similarity(rule1.text, rule2.text)
            if similarity >= self.semantic_threshold:
                return DuplicateMatch(
                    rule1_id=rule1.id,
                    rule2_id=rule2.id,
                    duplicate_type=DuplicateType.SEMANTIC,
                    similarity_score=similarity,
                    details=f"Semantic similarity: {similarity:.2%}",
                )

        return None

    def _is_exact_match(self, text1: str, text2: str) -> bool:
        """Check for exact text match using hash."""
        hash1 = self._get_hash(text1)
        hash2 = self._get_hash(text2)
        return hash1 == hash2

    def _is_normalized_match(self, text1: str, text2: str) -> bool:
        """Check for match after text normalization."""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        return norm1 == norm2

    def _is_structural_match(
        self,
        text1: str,
        text2: str,
    ) -> Tuple[bool, Optional[str]]:
        """Check if rules have same structure with different values."""
        struct1 = self._extract_structure(text1)
        struct2 = self._extract_structure(text2)

        if struct1 and struct2 and struct1 == struct2:
            return True, struct1

        return False, None

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        # Use normalized texts for comparison
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)

        # Use SequenceMatcher for similarity
        # In production, this could be replaced with embeddings
        return SequenceMatcher(None, norm1, norm2).ratio()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_hash(self, text: str) -> str:
        """Get or compute hash for text."""
        if text not in self._hash_cache:
            self._hash_cache[text] = hashlib.md5(
                text.encode()
            ).hexdigest()
        return self._hash_cache[text]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if text in self._normalized_cache:
            return self._normalized_cache[text]

        normalized = text.lower().strip()

        for pattern, replacement in self.NORMALIZATION_PATTERNS:
            normalized = re.sub(pattern, replacement, normalized)

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        self._normalized_cache[text] = normalized
        return normalized

    def _extract_structure(self, text: str) -> Optional[str]:
        """Extract structural pattern from text."""
        if text in self._structural_cache:
            return self._structural_cache[text]

        text_lower = text.lower()

        for pattern, template in self.STRUCTURAL_PATTERNS:
            match = re.match(pattern, text_lower)
            if match:
                self._structural_cache[text] = template
                return template

        self._structural_cache[text] = None
        return None

    def _build_duplicate_groups(
        self,
        rules: List[ExtractedRule],
        matches: List[DuplicateMatch],
    ) -> List[List[str]]:
        """Build groups of duplicate rules using Union-Find."""
        # Initialize Union-Find
        parent: Dict[str, str] = {r.id: r.id for r in rules}
        rank: Dict[str, int] = {r.id: 0 for r in rules}

        def find(x: str) -> str:
            if parent[x] != x:
                parent[x] = find(parent[x])  # Path compression
            return parent[x]

        def union(x: str, y: str) -> None:
            px, py = find(x), find(y)
            if px == py:
                return
            # Union by rank
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1

        # Union all duplicate pairs
        for match in matches:
            union(match.rule1_id, match.rule2_id)

        # Group by root
        groups: Dict[str, List[str]] = defaultdict(list)
        for rule in rules:
            root = find(rule.id)
            groups[root].append(rule.id)

        # Return only groups with more than one member
        return [group for group in groups.values() if len(group) > 1]

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._normalized_cache.clear()
        self._hash_cache.clear()
        self._structural_cache.clear()

    # =========================================================================
    # Statistics and Reporting
    # =========================================================================

    def get_duplication_stats(
        self,
        result: DeduplicationResult,
    ) -> Dict:
        """Get statistics about deduplication result."""
        type_counts: Dict[DuplicateType, int] = defaultdict(int)
        for match in result.matches:
            type_counts[match.duplicate_type] += 1

        return {
            "total_input": result.total_input,
            "total_unique": result.total_unique,
            "total_duplicates": result.total_duplicates,
            "deduplication_rate": (
                result.total_duplicates / result.total_input
                if result.total_input > 0
                else 0
            ),
            "duplicate_groups": len(result.duplicate_groups),
            "by_type": {
                dtype.value: count
                for dtype, count in type_counts.items()
            },
            "average_group_size": (
                sum(len(g) for g in result.duplicate_groups) /
                len(result.duplicate_groups)
                if result.duplicate_groups
                else 0
            ),
        }


# Convenience functions
def deduplicate_rules(rules: List[ExtractedRule]) -> List[ExtractedRule]:
    """Quick function to deduplicate a list of rules."""
    service = RuleDeduplicationService()
    result = service.deduplicate(rules)
    return result.unique_rules


def find_rule_duplicates(rules: List[ExtractedRule]) -> List[DuplicateMatch]:
    """Quick function to find duplicates in a list of rules."""
    service = RuleDeduplicationService()
    return service.find_duplicates(rules)
