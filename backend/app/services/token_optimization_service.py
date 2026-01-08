"""
Token Optimization Service

Week 143: Optimize Vector DB context for efficient LLM token usage.
Provides smart truncation, relevance scoring, and context budgeting.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TokenBudget(Enum):
    """Predefined token budgets for different use cases."""
    MINIMAL = 500       # Quick lookups
    COMPACT = 1000      # Standard context
    STANDARD = 2000     # Default for most operations
    EXTENDED = 4000     # Complex analysis
    FULL = 8000         # Comprehensive context


@dataclass
class OptimizedContext:
    """Container for optimized context with metadata."""
    content: str
    token_count: int
    items_included: int
    items_truncated: int
    relevance_scores: List[float]
    budget_used_percent: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "token_count": self.token_count,
            "items_included": self.items_included,
            "items_truncated": self.items_truncated,
            "avg_relevance": sum(self.relevance_scores) / len(self.relevance_scores) if self.relevance_scores else 0,
            "budget_used_percent": round(self.budget_used_percent, 1)
        }


class TokenOptimizationService:
    """
    Service for optimizing Vector DB context to fit within token budgets.

    Features:
    - Approximate token counting (4 chars ≈ 1 token for English)
    - Relevance-based prioritization
    - Smart truncation with sentence boundaries
    - Context compression and summarization hints
    """

    # Approximate chars per token (conservative estimate)
    CHARS_PER_TOKEN = 4

    # Priority weights for different content types
    CONTENT_PRIORITIES = {
        "code_pattern": 1.0,
        "similar_issue": 0.9,
        "best_practice": 0.85,
        "documentation": 0.8,
        "example": 0.75,
        "historical": 0.6,
        "metadata": 0.4
    }

    def __init__(self, default_budget: TokenBudget = TokenBudget.STANDARD):
        self.default_budget = default_budget

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        if not text:
            return 0
        return len(text) // self.CHARS_PER_TOKEN + 1

    def calculate_relevance_score(
        self,
        item: Dict[str, Any],
        query_terms: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> float:
        """
        Calculate relevance score for a context item.

        Factors:
        - Content type priority
        - Query term matches
        - Recency (if timestamp available)
        - Explicit relevance score (if provided)
        """
        score = 0.5  # Base score

        # Content type priority
        if content_type and content_type in self.CONTENT_PRIORITIES:
            score = self.CONTENT_PRIORITIES[content_type]

        # Query term matching
        if query_terms:
            content = str(item.get("content", "") or item.get("text", "")).lower()
            matches = sum(1 for term in query_terms if term.lower() in content)
            term_boost = min(matches * 0.1, 0.3)  # Max 30% boost
            score += term_boost

        # Use provided similarity/relevance score if available
        if "similarity" in item and item["similarity"] is not None:
            score = (score + item["similarity"]) / 2
        elif "relevance" in item and item["relevance"] is not None:
            score = (score + item["relevance"]) / 2

        # Recency boost (if timestamp available)
        if "timestamp" in item or "created_at" in item:
            score += 0.05  # Small boost for having timestamp

        return min(score, 1.0)

    def truncate_at_boundary(self, text: str, max_chars: int) -> str:
        """Truncate text at sentence or word boundary."""
        if len(text) <= max_chars:
            return text

        # Try to find sentence boundary
        truncated = text[:max_chars]

        # Look for sentence end
        for end_char in ['. ', '.\n', '! ', '? ']:
            last_sentence = truncated.rfind(end_char)
            if last_sentence > max_chars * 0.7:  # At least 70% of content
                return truncated[:last_sentence + 1].strip()

        # Fall back to word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.8:
            return truncated[:last_space] + "..."

        return truncated + "..."

    def compress_context(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compress context items by removing redundant information.

        - Remove duplicate content
        - Strip excessive whitespace
        - Consolidate similar items
        """
        seen_content = set()
        compressed = []

        for item in items:
            content = str(item.get("content", "") or item.get("text", ""))

            # Normalize whitespace
            normalized = re.sub(r'\s+', ' ', content.strip())

            # Skip duplicates (using hash of first 200 chars)
            content_hash = hash(normalized[:200])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            # Create compressed item
            compressed_item = {
                **item,
                "content": normalized if "content" in item else item.get("content"),
                "text": normalized if "text" in item else item.get("text")
            }
            compressed.append(compressed_item)

        return compressed

    def optimize_context(
        self,
        items: List[Dict[str, Any]],
        budget: Optional[TokenBudget] = None,
        query_terms: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        preserve_structure: bool = True
    ) -> OptimizedContext:
        """
        Optimize a list of context items to fit within token budget.

        Args:
            items: List of context items with 'content' or 'text' fields
            budget: Token budget to use (default: STANDARD)
            query_terms: Terms to boost relevance scoring
            content_type: Type of content for priority weighting
            preserve_structure: Keep item boundaries vs merge into single text

        Returns:
            OptimizedContext with optimized content and metadata
        """
        if not items:
            return OptimizedContext(
                content="",
                token_count=0,
                items_included=0,
                items_truncated=0,
                relevance_scores=[],
                budget_used_percent=0.0
            )

        budget = budget or self.default_budget
        max_tokens = budget.value
        max_chars = max_tokens * self.CHARS_PER_TOKEN

        # Step 1: Compress and deduplicate
        compressed = self.compress_context(items)

        # Step 2: Score and sort by relevance
        scored_items = []
        for item in compressed:
            score = self.calculate_relevance_score(item, query_terms, content_type)
            scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Step 3: Select items within budget
        selected_items = []
        selected_scores = []
        current_chars = 0
        items_truncated = 0

        for score, item in scored_items:
            content = str(item.get("content", "") or item.get("text", ""))
            item_chars = len(content)

            if current_chars + item_chars <= max_chars:
                # Full item fits
                selected_items.append(content)
                selected_scores.append(score)
                current_chars += item_chars
            elif current_chars < max_chars * 0.9:
                # Truncate item to fit remaining budget
                remaining = max_chars - current_chars
                truncated = self.truncate_at_boundary(content, remaining)
                if len(truncated) > 50:  # Only add if meaningful
                    selected_items.append(truncated)
                    selected_scores.append(score)
                    current_chars += len(truncated)
                    items_truncated += 1
                break
            else:
                break

        # Step 4: Format output
        if preserve_structure:
            formatted_content = "\n---\n".join(selected_items)
        else:
            formatted_content = "\n".join(selected_items)

        token_count = self.estimate_tokens(formatted_content)

        return OptimizedContext(
            content=formatted_content,
            token_count=token_count,
            items_included=len(selected_items),
            items_truncated=items_truncated,
            relevance_scores=selected_scores,
            budget_used_percent=(token_count / max_tokens) * 100
        )

    def optimize_for_llm(
        self,
        context_dict: Dict[str, List[Dict[str, Any]]],
        budget: Optional[TokenBudget] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize a structured context dictionary for LLM consumption.

        Distributes budget across context categories based on priority.

        Args:
            context_dict: Dict with category keys and lists of items
            budget: Total token budget
            query: Query string for relevance boosting

        Returns:
            Optimized context dict with metadata
        """
        budget = budget or self.default_budget
        total_tokens = budget.value

        # Extract query terms
        query_terms = query.split() if query else None

        # Define category budgets (proportional allocation)
        category_priorities = {
            "code_patterns": 0.30,
            "similar_issues": 0.25,
            "best_practices": 0.20,
            "documentation": 0.15,
            "examples": 0.10
        }

        optimized_result = {
            "categories": {},
            "metadata": {
                "total_budget": total_tokens,
                "categories_processed": 0,
                "total_items_included": 0,
                "total_items_truncated": 0
            }
        }

        for category, items in context_dict.items():
            if not items:
                continue

            # Determine budget for this category
            priority = category_priorities.get(category, 0.1)
            category_budget_tokens = int(total_tokens * priority)

            # Map category to content type
            content_type_map = {
                "code_patterns": "code_pattern",
                "similar_issues": "similar_issue",
                "best_practices": "best_practice",
                "documentation": "documentation",
                "examples": "example"
            }
            content_type = content_type_map.get(category, "metadata")

            # Create appropriate budget enum
            if category_budget_tokens <= 500:
                cat_budget = TokenBudget.MINIMAL
            elif category_budget_tokens <= 1000:
                cat_budget = TokenBudget.COMPACT
            elif category_budget_tokens <= 2000:
                cat_budget = TokenBudget.STANDARD
            else:
                cat_budget = TokenBudget.EXTENDED

            # Optimize this category
            optimized = self.optimize_context(
                items=items,
                budget=cat_budget,
                query_terms=query_terms,
                content_type=content_type
            )

            optimized_result["categories"][category] = {
                "content": optimized.content,
                "token_count": optimized.token_count,
                "items_included": optimized.items_included
            }

            optimized_result["metadata"]["categories_processed"] += 1
            optimized_result["metadata"]["total_items_included"] += optimized.items_included
            optimized_result["metadata"]["total_items_truncated"] += optimized.items_truncated

        # Calculate total tokens used
        total_used = sum(
            cat["token_count"]
            for cat in optimized_result["categories"].values()
        )
        optimized_result["metadata"]["tokens_used"] = total_used
        optimized_result["metadata"]["budget_used_percent"] = round(
            (total_used / total_tokens) * 100, 1
        )

        return optimized_result


# Singleton instance
_token_optimization_service: Optional[TokenOptimizationService] = None


def get_token_optimization_service() -> TokenOptimizationService:
    """Get or create the token optimization service singleton."""
    global _token_optimization_service
    if _token_optimization_service is None:
        _token_optimization_service = TokenOptimizationService()
    return _token_optimization_service
