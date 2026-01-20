"""
Result Aggregator Service - B12 (Fase 24)

Combines results from multiple agents using various strategies.

Strategies:
- FIRST: Take first successful result
- BEST: Select best by confidence/score
- MERGE: Combine all results
- VOTE: Majority voting for categorical results
- WEIGHTED: Weight by agent reliability
- CONSENSUS: Require agreement threshold

Integrates with:
- LLMCouncilService: Uses similar consensus concepts
- GhostCrewService: Aggregates security findings

Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import Counter
from uuid import UUID

from .collaboration_types import (
    AgentResult,
    AggregatedResult,
    AggregationStrategy,
    CollaborationSession
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class AggregationConfig:
    """
    Configuration for result aggregation.

    Attributes:
        strategy: Aggregation strategy to use
        min_results: Minimum results required before aggregating
        consensus_threshold: Agreement threshold for CONSENSUS (0.0-1.0)
        weight_by_confidence: Multiply weights by result confidence
        merge_strategy: How to merge dict results ("shallow", "deep", "list")
        timeout_ms: Max time to wait for results
        required_agents: Agents that must respond
    """
    strategy: AggregationStrategy = AggregationStrategy.BEST
    min_results: int = 1
    consensus_threshold: float = 0.7
    weight_by_confidence: bool = True
    merge_strategy: str = "shallow"
    timeout_ms: int = 30000
    required_agents: List[str] = field(default_factory=list)


class ResultAggregator:
    """
    Aggregates results from multiple agents.

    Usage:
        aggregator = ResultAggregator()

        # Configure aggregation
        config = AggregationConfig(
            strategy=AggregationStrategy.CONSENSUS,
            consensus_threshold=0.8
        )

        # Add results
        aggregator.add_result(session_id, result1)
        aggregator.add_result(session_id, result2)
        aggregator.add_result(session_id, result3)

        # Aggregate
        final_result = aggregator.aggregate(session_id, config)
    """

    def __init__(self):
        # Results per session: session_id -> list of AgentResult
        self._results: Dict[UUID, List[AgentResult]] = {}

        # Agent reliability scores (can be updated based on history)
        self._agent_weights: Dict[str, float] = {}

        # Aggregation history for analytics
        self._history: List[Dict[str, Any]] = []

        logger.info("ResultAggregator initialized")

    def add_result(self, session_id: UUID, result: AgentResult) -> None:
        """Add a result from an agent."""
        if session_id not in self._results:
            self._results[session_id] = []
        self._results[session_id].append(result)
        logger.debug(f"Added result from {result.agent_id} to session {session_id}")

    def get_results(self, session_id: UUID) -> List[AgentResult]:
        """Get all results for a session."""
        return self._results.get(session_id, [])

    def get_successful_results(self, session_id: UUID) -> List[AgentResult]:
        """Get only successful results for a session."""
        return [r for r in self.get_results(session_id) if r.success]

    def set_agent_weight(self, agent_id: str, weight: float) -> None:
        """Set reliability weight for an agent."""
        self._agent_weights[agent_id] = max(0.0, min(2.0, weight))  # Clamp 0-2

    def get_agent_weight(self, agent_id: str) -> float:
        """Get reliability weight for an agent (default 1.0)."""
        return self._agent_weights.get(agent_id, 1.0)

    def _aggregate_first(
        self,
        results: List[AgentResult],
        config: AggregationConfig
    ) -> Optional[Any]:
        """Take first successful result."""
        for result in results:
            if result.success:
                return result.output
        return None

    def _aggregate_best(
        self,
        results: List[AgentResult],
        config: AggregationConfig
    ) -> Optional[Any]:
        """Select result with highest confidence."""
        successful = [r for r in results if r.success]
        if not successful:
            return None

        # Score by confidence * agent weight
        def score(r: AgentResult) -> float:
            weight = self.get_agent_weight(r.agent_id)
            return r.confidence * weight

        best = max(successful, key=score)
        return best.output

    def _merge_dicts(
        self,
        dicts: List[Dict],
        strategy: str = "shallow"
    ) -> Dict:
        """Merge multiple dictionaries."""
        if not dicts:
            return {}

        if strategy == "shallow":
            # Simple update (last wins for conflicts)
            result = {}
            for d in dicts:
                result.update(d)
            return result

        if strategy == "deep":
            # Deep merge (recursive for nested dicts)
            result = {}
            for d in dicts:
                self._deep_merge(result, d)
            return result

        if strategy == "list":
            # Collect all values for same key into lists
            result: Dict[str, List] = {}
            for d in dicts:
                for k, v in d.items():
                    if k not in result:
                        result[k] = []
                    result[k].append(v)
            return result

        return dicts[0] if dicts else {}

    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """Recursively merge update into base."""
        for key, value in update.items():
            if (
                key in base and
                isinstance(base[key], dict) and
                isinstance(value, dict)
            ):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _merge_lists(self, lists: List[List]) -> List:
        """Merge multiple lists (deduplicated if hashable)."""
        result = []
        seen = set()

        for lst in lists:
            for item in lst:
                try:
                    item_hash = hash(str(item))
                    if item_hash not in seen:
                        seen.add(item_hash)
                        result.append(item)
                except TypeError:
                    # Unhashable item, just append
                    result.append(item)

        return result

    def _aggregate_merge(
        self,
        results: List[AgentResult],
        config: AggregationConfig
    ) -> Any:
        """Merge all successful results."""
        successful = [r for r in results if r.success]
        if not successful:
            return None

        outputs = [r.output for r in successful]

        # Determine merge approach based on output types
        if all(isinstance(o, dict) for o in outputs):
            return self._merge_dicts(outputs, config.merge_strategy)

        if all(isinstance(o, list) for o in outputs):
            return self._merge_lists(outputs)

        if all(isinstance(o, str) for o in outputs):
            # For strings, concatenate with separator
            return "\n---\n".join(outputs)

        # Mixed types - return list of outputs
        return outputs

    def _aggregate_vote(
        self,
        results: List[AgentResult],
        config: AggregationConfig
    ) -> Any:
        """Majority voting for categorical/boolean results."""
        successful = [r for r in results if r.success]
        if not successful:
            return None

        # Weight votes by agent reliability and confidence
        weighted_votes: Dict[str, float] = {}

        for result in successful:
            # Convert output to string for counting
            vote_key = str(result.output)
            weight = self.get_agent_weight(result.agent_id)
            if config.weight_by_confidence:
                weight *= result.confidence

            weighted_votes[vote_key] = weighted_votes.get(vote_key, 0) + weight

        if not weighted_votes:
            return None

        # Return output with highest weighted votes
        winner_key = max(weighted_votes, key=weighted_votes.get)

        # Find original output (not string representation)
        for result in successful:
            if str(result.output) == winner_key:
                return result.output

        return winner_key

    def _aggregate_weighted(
        self,
        results: List[AgentResult],
        config: AggregationConfig
    ) -> Any:
        """Weighted combination (for numeric results)."""
        successful = [r for r in results if r.success]
        if not successful:
            return None

        # Check if all outputs are numeric
        try:
            numeric_results = []
            total_weight = 0.0

            for result in successful:
                if isinstance(result.output, (int, float)):
                    weight = self.get_agent_weight(result.agent_id)
                    if config.weight_by_confidence:
                        weight *= result.confidence
                    numeric_results.append((result.output, weight))
                    total_weight += weight

            if numeric_results and total_weight > 0:
                weighted_sum = sum(v * w for v, w in numeric_results)
                return weighted_sum / total_weight

        except (TypeError, ValueError):
            pass

        # Fall back to BEST for non-numeric
        return self._aggregate_best(results, config)

    def _aggregate_consensus(
        self,
        results: List[AgentResult],
        config: AggregationConfig
    ) -> Optional[Any]:
        """
        Require agreement threshold.

        Returns result only if enough agents agree.
        """
        successful = [r for r in results if r.success]
        if not successful:
            return None

        total_weight = 0.0
        vote_weights: Dict[str, float] = {}

        for result in successful:
            vote_key = str(result.output)
            weight = self.get_agent_weight(result.agent_id)
            if config.weight_by_confidence:
                weight *= result.confidence

            vote_weights[vote_key] = vote_weights.get(vote_key, 0) + weight
            total_weight += weight

        if total_weight == 0:
            return None

        # Check if any option meets threshold
        for vote_key, vote_weight in vote_weights.items():
            agreement = vote_weight / total_weight
            if agreement >= config.consensus_threshold:
                # Find original output
                for result in successful:
                    if str(result.output) == vote_key:
                        return result.output
                return vote_key

        # No consensus reached
        logger.warning(
            f"No consensus reached. Highest agreement: "
            f"{max(vote_weights.values()) / total_weight:.2%}"
        )
        return None

    def aggregate(
        self,
        session_id: UUID,
        config: Optional[AggregationConfig] = None
    ) -> AggregatedResult:
        """
        Aggregate results for a session.

        Args:
            session_id: Session to aggregate results for
            config: Aggregation configuration (defaults to BEST)

        Returns:
            AggregatedResult with combined output
        """
        if config is None:
            config = AggregationConfig()

        results = self.get_results(session_id)
        successful = [r for r in results if r.success]

        # Check minimum results
        if len(successful) < config.min_results:
            logger.warning(
                f"Not enough results for aggregation: "
                f"{len(successful)} < {config.min_results}"
            )

        # Check required agents
        result_agents = {r.agent_id for r in results}
        missing_required = set(config.required_agents) - result_agents
        if missing_required:
            logger.warning(f"Missing results from required agents: {missing_required}")

        # Apply aggregation strategy
        strategy_map = {
            AggregationStrategy.FIRST: self._aggregate_first,
            AggregationStrategy.BEST: self._aggregate_best,
            AggregationStrategy.MERGE: self._aggregate_merge,
            AggregationStrategy.VOTE: self._aggregate_vote,
            AggregationStrategy.WEIGHTED: self._aggregate_weighted,
            AggregationStrategy.CONSENSUS: self._aggregate_consensus,
        }

        aggregator_fn = strategy_map.get(config.strategy, self._aggregate_best)
        final_output = aggregator_fn(results, config)

        # Calculate overall confidence
        if successful:
            avg_confidence = sum(r.confidence for r in successful) / len(successful)
            if config.strategy == AggregationStrategy.CONSENSUS:
                # Lower confidence if consensus was close
                vote_counts = Counter(str(r.output) for r in successful)
                if vote_counts:
                    max_votes = max(vote_counts.values())
                    consensus_ratio = max_votes / len(successful)
                    avg_confidence *= consensus_ratio
        else:
            avg_confidence = 0.0

        # Build aggregated result
        aggregated = AggregatedResult(
            session_id=session_id,
            strategy=config.strategy,
            final_output=final_output,
            confidence=avg_confidence,
            contributing_agents=[r.agent_id for r in successful],
            individual_results=results,
            aggregation_metadata={
                "total_results": len(results),
                "successful_results": len(successful),
                "strategy": config.strategy.value,
                "consensus_threshold": config.consensus_threshold,
                "missing_required": list(missing_required)
            }
        )

        # Log to history
        self._history.append({
            "session_id": str(session_id),
            "strategy": config.strategy.value,
            "result_count": len(results),
            "success_count": len(successful),
            "confidence": avg_confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        logger.info(
            f"Aggregated {len(successful)}/{len(results)} results for session {session_id} "
            f"using {config.strategy.value} strategy"
        )

        return aggregated

    def aggregate_session(
        self,
        session: CollaborationSession,
        config: Optional[AggregationConfig] = None
    ) -> AggregatedResult:
        """
        Aggregate results from a CollaborationSession.

        Convenience method that adds session results and aggregates.
        """
        # Add results from session
        for result in session.results:
            if session.session_id not in self._results:
                self._results[session.session_id] = []
            if result not in self._results[session.session_id]:
                self._results[session.session_id].append(result)

        return self.aggregate(session.session_id, config)

    def clear_session(self, session_id: UUID) -> None:
        """Clear results for a session."""
        if session_id in self._results:
            del self._results[session_id]
            logger.debug(f"Cleared results for session {session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregation statistics."""
        if not self._history:
            return {"total_aggregations": 0}

        strategy_counts = Counter(h["strategy"] for h in self._history)
        avg_confidence = sum(h["confidence"] for h in self._history) / len(self._history)
        avg_success_rate = sum(
            h["success_count"] / h["result_count"]
            for h in self._history
            if h["result_count"] > 0
        ) / len(self._history)

        return {
            "total_aggregations": len(self._history),
            "strategy_distribution": dict(strategy_counts),
            "average_confidence": avg_confidence,
            "average_success_rate": avg_success_rate,
            "active_sessions": len(self._results),
            "agent_weights": dict(self._agent_weights)
        }


# Singleton instance
_aggregator_instance: Optional[ResultAggregator] = None


def get_result_aggregator() -> ResultAggregator:
    """Get or create singleton ResultAggregator."""
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = ResultAggregator()
    return _aggregator_instance
