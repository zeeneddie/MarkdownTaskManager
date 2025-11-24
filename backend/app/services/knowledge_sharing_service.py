"""
Knowledge Sharing Service

Week 25-26: AgentEvolver Integration - Cross-Agent Knowledge Sharing
Based on: github.com/zeeneddie/AgentEvolver

Enables agents to learn from each other:
1. Share successful patterns between agents
2. Broadcast important learnings
3. Request knowledge from other agents
4. Get recommended knowledge

Author: Claude Code (Week 25 Day 5)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging

from app.services.experience_store_service import (
    ExperienceStoreService,
    get_experience_store,
    Experience,
    SuccessfulPattern,
    AgentRole,
    WorkType,
    Outcome
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class ShareType(str, Enum):
    """Types of knowledge sharing"""
    PATTERN = "pattern"
    EXPERIENCE = "experience"
    LEARNING = "learning"
    WARNING = "warning"


class ShareStatus(str, Enum):
    """Status of a share"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"


class RecommendationType(str, Enum):
    """Types of recommendations"""
    PATTERN = "pattern"
    LEARNING = "learning"
    SKILL = "skill"
    COLLABORATION = "collaboration"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Learning:
    """A learning that can be shared"""
    id: str
    agent_id: str
    content: str
    context: str
    work_type: WorkType
    importance: float  # 0-1
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "content": self.content,
            "context": self.context,
            "work_type": self.work_type.value,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }


@dataclass
class ShareResult:
    """Result of sharing knowledge"""
    share_id: str
    from_agent: str
    to_agents: List[str]
    share_type: ShareType
    content_id: str
    status: ShareStatus
    accepted_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "share_id": self.share_id,
            "from_agent": self.from_agent,
            "to_agents": self.to_agents,
            "share_type": self.share_type.value,
            "content_id": self.content_id,
            "status": self.status.value,
            "accepted_by": self.accepted_by,
            "rejected_by": self.rejected_by,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class BroadcastResult:
    """Result of broadcasting knowledge"""
    broadcast_id: str
    learning: Learning
    recipients: List[str]
    relevance_scores: Dict[str, float]
    delivered_count: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "broadcast_id": self.broadcast_id,
            "learning": self.learning.to_dict(),
            "recipients": self.recipients,
            "relevance_scores": self.relevance_scores,
            "delivered_count": self.delivered_count,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class KnowledgeRequest:
    """A request for knowledge from another agent"""
    id: str
    requesting_agent: str
    topic: str
    work_type: Optional[WorkType] = None
    urgency: str = "normal"  # low, normal, high
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "requesting_agent": self.requesting_agent,
            "topic": self.topic,
            "work_type": self.work_type.value if self.work_type else None,
            "urgency": self.urgency,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class KnowledgeResponse:
    """Response to a knowledge request"""
    request_id: str
    responding_agents: List[str]
    patterns: List[SuccessfulPattern]
    learnings: List[Learning]
    experiences: List[Experience]
    relevance_score: float
    response_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "responding_agents": self.responding_agents,
            "patterns_count": len(self.patterns),
            "learnings_count": len(self.learnings),
            "experiences_count": len(self.experiences),
            "relevance_score": self.relevance_score,
            "response_time_ms": self.response_time_ms
        }


@dataclass
class Recommendation:
    """A knowledge recommendation for an agent"""
    id: str
    for_agent: str
    recommendation_type: RecommendationType
    title: str
    description: str
    source_agent: Optional[str] = None
    relevance_score: float = 0.0
    content_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "for_agent": self.for_agent,
            "recommendation_type": self.recommendation_type.value,
            "title": self.title,
            "description": self.description,
            "source_agent": self.source_agent,
            "relevance_score": self.relevance_score,
            "content_id": self.content_id,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# KNOWLEDGE SHARING SERVICE
# ============================================================================

class KnowledgeSharingService:
    """
    Service for cross-agent knowledge sharing.

    Enables agents to:
    - Share successful patterns with each other
    - Broadcast important learnings
    - Request knowledge on specific topics
    - Receive personalized recommendations
    """

    # Agent expertise mapping
    AGENT_EXPERTISE = {
        "felix": ["architecture", "design", "api", "microservices", "system_design"],
        "marcus": ["maintenance", "refactoring", "tech_debt", "dependencies", "code_health"],
        "quinn": ["security", "quality", "auditing", "vulnerabilities", "testing"],
        "betty": ["debugging", "bugs", "root_cause", "error_handling", "troubleshooting"],
        "eliza": ["estimation", "planning", "complexity", "effort", "prediction"],
        "tessa": ["testing", "coverage", "automation", "e2e", "unit_tests"],
        "miguel": ["migration", "upgrades", "compatibility", "data_migration"],
        "diana": ["documentation", "api_docs", "user_guides", "technical_writing"],
        "peter": ["requirements", "user_stories", "product", "business_analysis"],
        "paul": ["planning", "coordination", "risk", "resources", "sprints"]
    }

    def __init__(self):
        self._experience_store: Optional[ExperienceStoreService] = None

        # In-memory storage
        self._shares: Dict[str, ShareResult] = {}
        self._broadcasts: Dict[str, BroadcastResult] = {}
        self._requests: Dict[str, KnowledgeRequest] = {}
        self._learnings: Dict[str, Learning] = {}
        self._recommendations: Dict[str, List[Recommendation]] = {}

    async def _get_experience_store(self) -> ExperienceStoreService:
        """Get or create experience store instance"""
        if self._experience_store is None:
            self._experience_store = await get_experience_store()
        return self._experience_store

    # -------------------------------------------------------------------------
    # PATTERN SHARING
    # -------------------------------------------------------------------------

    async def share_pattern(
        self,
        from_agent: str,
        to_agents: List[str],
        pattern_id: str
    ) -> ShareResult:
        """
        Share a successful pattern between agents.

        Args:
            from_agent: Agent sharing the pattern
            to_agents: Agents to share with
            pattern_id: ID of the pattern to share
        """
        share_id = str(uuid.uuid4())

        # Validate pattern exists
        experience_store = await self._get_experience_store()
        patterns = await experience_store.get_successful_patterns(
            work_types=None,
            min_success_count=1
        )

        pattern = next((p for p in patterns if p.id == pattern_id), None)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")

        # Check relevance for each recipient
        accepted = []
        rejected = []

        for agent in to_agents:
            relevance = self._calculate_pattern_relevance(agent, pattern)
            if relevance > 0.5:
                accepted.append(agent)
            else:
                rejected.append(agent)

        # Determine overall status
        if len(accepted) == len(to_agents):
            status = ShareStatus.ACCEPTED
        elif len(accepted) > 0:
            status = ShareStatus.PENDING
        else:
            status = ShareStatus.REJECTED

        result = ShareResult(
            share_id=share_id,
            from_agent=from_agent,
            to_agents=to_agents,
            share_type=ShareType.PATTERN,
            content_id=pattern_id,
            status=status,
            accepted_by=accepted,
            rejected_by=rejected
        )

        self._shares[share_id] = result

        logger.info(f"Pattern {pattern_id} shared from {from_agent} to {len(accepted)}/{len(to_agents)} agents")

        return result

    def _calculate_pattern_relevance(
        self,
        agent_id: str,
        pattern: SuccessfulPattern
    ) -> float:
        """Calculate how relevant a pattern is for an agent"""
        agent_expertise = self.AGENT_EXPERTISE.get(agent_id.lower(), [])

        # Check work type match
        work_type_match = any(
            wt.value.lower() in [e.lower() for e in agent_expertise]
            for wt in pattern.work_types
        )

        # Check context match
        context_words = set(' '.join(pattern.applicable_contexts).lower().split())
        expertise_match = len(context_words & set(agent_expertise)) / max(1, len(agent_expertise))

        # Calculate relevance
        relevance = (0.5 if work_type_match else 0.0) + (expertise_match * 0.5)

        return min(1.0, relevance)

    # -------------------------------------------------------------------------
    # BROADCAST LEARNINGS
    # -------------------------------------------------------------------------

    async def broadcast_learning(
        self,
        learning: Learning,
        relevance_filter: Optional[Dict[str, Any]] = None
    ) -> BroadcastResult:
        """
        Broadcast an important learning to relevant agents.

        Args:
            learning: The learning to broadcast
            relevance_filter: Optional filter for recipients
        """
        broadcast_id = str(uuid.uuid4())

        # Store the learning
        self._learnings[learning.id] = learning

        # Find relevant agents
        all_agents = list(self.AGENT_EXPERTISE.keys())
        recipients = []
        relevance_scores = {}

        for agent in all_agents:
            if agent.lower() == learning.agent_id.lower():
                continue  # Don't send to self

            relevance = self._calculate_learning_relevance(agent, learning)

            # Apply filter if provided
            if relevance_filter:
                min_relevance = relevance_filter.get("min_relevance", 0.3)
                if relevance < min_relevance:
                    continue

            if relevance > 0.3:
                recipients.append(agent)
                relevance_scores[agent] = relevance

        result = BroadcastResult(
            broadcast_id=broadcast_id,
            learning=learning,
            recipients=recipients,
            relevance_scores=relevance_scores,
            delivered_count=len(recipients)
        )

        self._broadcasts[broadcast_id] = result

        logger.info(f"Learning broadcast from {learning.agent_id} to {len(recipients)} agents")

        return result

    def _calculate_learning_relevance(
        self,
        agent_id: str,
        learning: Learning
    ) -> float:
        """Calculate how relevant a learning is for an agent"""
        agent_expertise = self.AGENT_EXPERTISE.get(agent_id.lower(), [])

        # Check tag overlap
        tag_match = len(set(learning.tags) & set(agent_expertise)) / max(1, len(learning.tags))

        # Check work type relevance
        work_type_match = learning.work_type.value.lower() in [e.lower() for e in agent_expertise]

        # Factor in importance
        importance_factor = learning.importance

        relevance = (tag_match * 0.4) + (0.3 if work_type_match else 0.0) + (importance_factor * 0.3)

        return min(1.0, relevance)

    # -------------------------------------------------------------------------
    # KNOWLEDGE REQUESTS
    # -------------------------------------------------------------------------

    async def request_knowledge(
        self,
        agent_id: str,
        topic: str,
        work_type: Optional[WorkType] = None
    ) -> KnowledgeResponse:
        """
        Request knowledge from other agents on a topic.

        Args:
            agent_id: Agent requesting knowledge
            topic: Topic to get knowledge about
            work_type: Optional work type filter
        """
        import time
        start_time = time.time()

        request_id = str(uuid.uuid4())

        request = KnowledgeRequest(
            id=request_id,
            requesting_agent=agent_id,
            topic=topic,
            work_type=work_type
        )
        self._requests[request_id] = request

        # Find experts on this topic
        expert_agents = self._find_experts(topic, agent_id)

        # Gather relevant knowledge
        experience_store = await self._get_experience_store()

        # Get patterns
        patterns = await experience_store.get_successful_patterns(
            work_types=[work_type] if work_type else None,
            min_success_count=1
        )

        # Filter by topic relevance
        relevant_patterns = [
            p for p in patterns
            if self._is_relevant_to_topic(p.description, topic)
        ][:5]

        # Get learnings
        relevant_learnings = [
            l for l in self._learnings.values()
            if self._is_relevant_to_topic(l.content, topic)
        ][:5]

        # Get experiences
        experiences = await experience_store.get_experiences(
            work_type=work_type,
            limit=100
        )

        relevant_experiences = [
            e for e in experiences
            if self._is_relevant_to_topic(e.task_description, topic)
        ][:5]

        # Calculate overall relevance
        total_items = len(relevant_patterns) + len(relevant_learnings) + len(relevant_experiences)
        relevance_score = min(1.0, total_items / 10)

        response_time = int((time.time() - start_time) * 1000)

        response = KnowledgeResponse(
            request_id=request_id,
            responding_agents=expert_agents,
            patterns=relevant_patterns,
            learnings=relevant_learnings,
            experiences=relevant_experiences,
            relevance_score=relevance_score,
            response_time_ms=response_time
        )

        logger.info(f"Knowledge request from {agent_id} about '{topic}': {total_items} items found")

        return response

    def _find_experts(self, topic: str, exclude_agent: str) -> List[str]:
        """Find agents who are experts on a topic"""
        topic_words = set(topic.lower().split())
        experts = []

        for agent, expertise in self.AGENT_EXPERTISE.items():
            if agent.lower() == exclude_agent.lower():
                continue

            # Calculate expertise match
            match_score = len(topic_words & set(e.lower() for e in expertise))
            if match_score > 0:
                experts.append(agent)

        return experts

    def _is_relevant_to_topic(self, text: str, topic: str) -> bool:
        """Check if text is relevant to a topic"""
        topic_words = set(topic.lower().split())
        text_words = set(text.lower().split())

        overlap = len(topic_words & text_words)
        return overlap > 0 or topic.lower() in text.lower()

    # -------------------------------------------------------------------------
    # RECOMMENDATIONS
    # -------------------------------------------------------------------------

    async def get_recommendations(
        self,
        agent_id: str,
        limit: int = 5
    ) -> List[Recommendation]:
        """
        Get personalized knowledge recommendations for an agent.

        Recommendations are based on:
        - Agent's recent failures
        - Patterns from successful agents
        - Complementary skills
        """
        recommendations = []

        # 1. Find patterns from high-performing agents
        experience_store = await self._get_experience_store()

        all_patterns = await experience_store.get_successful_patterns(
            work_types=None,
            min_success_count=3
        )

        # Find patterns the agent hasn't used
        agent_expertise = self.AGENT_EXPERTISE.get(agent_id.lower(), [])

        for pattern in all_patterns[:3]:
            relevance = self._calculate_pattern_relevance(agent_id, pattern)
            if relevance > 0.4:
                recommendations.append(Recommendation(
                    id=str(uuid.uuid4()),
                    for_agent=agent_id,
                    recommendation_type=RecommendationType.PATTERN,
                    title=f"Learn pattern: {pattern.name}",
                    description=pattern.description,
                    source_agent=pattern.created_by,
                    relevance_score=relevance,
                    content_id=pattern.id
                ))

        # 2. Find complementary skills
        complementary_agents = self._find_complementary_agents(agent_id)
        for comp_agent in complementary_agents[:2]:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                for_agent=agent_id,
                recommendation_type=RecommendationType.COLLABORATION,
                title=f"Collaborate with {comp_agent.capitalize()}",
                description=f"Agent {comp_agent} has complementary expertise that could help",
                source_agent=comp_agent,
                relevance_score=0.7
            ))

        # 3. Add learnings from broadcasts
        for learning in list(self._learnings.values())[:3]:
            if learning.agent_id.lower() != agent_id.lower():
                relevance = self._calculate_learning_relevance(agent_id, learning)
                if relevance > 0.5:
                    recommendations.append(Recommendation(
                        id=str(uuid.uuid4()),
                        for_agent=agent_id,
                        recommendation_type=RecommendationType.LEARNING,
                        title=f"Learning from {learning.agent_id}",
                        description=learning.content[:200],
                        source_agent=learning.agent_id,
                        relevance_score=relevance,
                        content_id=learning.id
                    ))

        # Sort by relevance and limit
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)

        # Store for agent
        self._recommendations[agent_id] = recommendations[:limit]

        return recommendations[:limit]

    def _find_complementary_agents(self, agent_id: str) -> List[str]:
        """Find agents with complementary skills"""
        agent_expertise = set(self.AGENT_EXPERTISE.get(agent_id.lower(), []))
        complementary = []

        for other_agent, other_expertise in self.AGENT_EXPERTISE.items():
            if other_agent.lower() == agent_id.lower():
                continue

            # Find agents with different expertise
            overlap = len(agent_expertise & set(other_expertise))
            if overlap < 2:  # Low overlap = complementary
                complementary.append(other_agent)

        return complementary

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    async def get_sharing_stats(self) -> Dict[str, Any]:
        """Get statistics about knowledge sharing"""
        total_shares = len(self._shares)
        total_broadcasts = len(self._broadcasts)
        total_requests = len(self._requests)
        total_learnings = len(self._learnings)

        # Calculate acceptance rate
        accepted = sum(1 for s in self._shares.values() if s.status == ShareStatus.ACCEPTED)
        acceptance_rate = accepted / total_shares if total_shares > 0 else 0

        # Most active sharers
        sharer_counts = {}
        for share in self._shares.values():
            sharer_counts[share.from_agent] = sharer_counts.get(share.from_agent, 0) + 1

        top_sharers = sorted(sharer_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_shares": total_shares,
            "total_broadcasts": total_broadcasts,
            "total_requests": total_requests,
            "total_learnings": total_learnings,
            "acceptance_rate": acceptance_rate,
            "top_sharers": dict(top_sharers)
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_knowledge_sharing_service: Optional[KnowledgeSharingService] = None


async def get_knowledge_sharing_service() -> KnowledgeSharingService:
    """Get or create knowledge sharing service instance"""
    global _knowledge_sharing_service
    if _knowledge_sharing_service is None:
        _knowledge_sharing_service = KnowledgeSharingService()
    return _knowledge_sharing_service
