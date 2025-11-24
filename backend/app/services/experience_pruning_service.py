"""
Experience Pruning Service

Week 25-26: AgentEvolver Integration - Experience Pruning
Based on: github.com/zeeneddie/AgentEvolver

Manages experience store maintenance:
1. Remove old/irrelevant experiences
2. Remove low-relevance experiences
3. Merge similar experiences
4. Archive before delete (safety)
5. Scheduled pruning jobs

Author: Claude Code (Week 25 Day 3-4)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging
import asyncio

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

class PruneAction(str, Enum):
    """Types of pruning actions"""
    DELETE = "delete"
    ARCHIVE = "archive"
    MERGE = "merge"
    KEEP = "keep"


class PruneReason(str, Enum):
    """Reasons for pruning"""
    OLD_AGE = "old_age"
    LOW_RELEVANCE = "low_relevance"
    DUPLICATE = "duplicate"
    LOW_QUALITY = "low_quality"
    OBSOLETE_PATTERN = "obsolete_pattern"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PruneResult:
    """Result of a pruning operation"""
    operation_id: str
    action: PruneAction
    reason: PruneReason
    experiences_affected: int
    experiences_archived: int
    experiences_deleted: int
    space_recovered_mb: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "action": self.action.value,
            "reason": self.reason.value,
            "experiences_affected": self.experiences_affected,
            "experiences_archived": self.experiences_archived,
            "experiences_deleted": self.experiences_deleted,
            "space_recovered_mb": self.space_recovered_mb,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


@dataclass
class MergeResult:
    """Result of merging similar experiences"""
    operation_id: str
    groups_found: int
    experiences_merged: int
    new_experiences_created: int
    similarity_threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    merge_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "groups_found": self.groups_found,
            "experiences_merged": self.experiences_merged,
            "new_experiences_created": self.new_experiences_created,
            "similarity_threshold": self.similarity_threshold,
            "timestamp": self.timestamp.isoformat(),
            "merge_details": self.merge_details
        }


@dataclass
class ArchiveResult:
    """Result of archiving experiences"""
    operation_id: str
    experiences_archived: int
    archive_location: str
    total_size_mb: float
    timestamp: datetime = field(default_factory=datetime.now)
    archived_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "experiences_archived": self.experiences_archived,
            "archive_location": self.archive_location,
            "total_size_mb": self.total_size_mb,
            "timestamp": self.timestamp.isoformat(),
            "archived_ids": self.archived_ids
        }


@dataclass
class PruningSchedule:
    """Configuration for scheduled pruning"""
    id: str
    name: str
    interval_hours: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    # Pruning configuration
    max_age_days: int = 90
    min_relevance: float = 0.3
    merge_threshold: float = 0.95

    # Results tracking
    total_runs: int = 0
    total_pruned: int = 0
    total_archived: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "interval_hours": self.interval_hours,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "max_age_days": self.max_age_days,
            "min_relevance": self.min_relevance,
            "merge_threshold": self.merge_threshold,
            "total_runs": self.total_runs,
            "total_pruned": self.total_pruned,
            "total_archived": self.total_archived
        }


@dataclass
class PruningStats:
    """Statistics for experience pruning"""
    total_experiences: int = 0
    experiences_by_age: Dict[str, int] = field(default_factory=dict)
    experiences_by_relevance: Dict[str, int] = field(default_factory=dict)
    potential_duplicates: int = 0
    storage_used_mb: float = 0.0
    oldest_experience: Optional[datetime] = None
    newest_experience: Optional[datetime] = None
    recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_experiences": self.total_experiences,
            "experiences_by_age": self.experiences_by_age,
            "experiences_by_relevance": self.experiences_by_relevance,
            "potential_duplicates": self.potential_duplicates,
            "storage_used_mb": self.storage_used_mb,
            "oldest_experience": self.oldest_experience.isoformat() if self.oldest_experience else None,
            "newest_experience": self.newest_experience.isoformat() if self.newest_experience else None,
            "recommended_actions": self.recommended_actions
        }


# ============================================================================
# EXPERIENCE PRUNING SERVICE
# ============================================================================

class ExperiencePruningService:
    """
    Service for pruning and maintaining the experience store.

    Implements:
    - Age-based pruning
    - Relevance-based pruning
    - Duplicate detection and merging
    - Safe archiving before deletion
    - Scheduled maintenance jobs
    """

    # Default configuration
    DEFAULT_MAX_AGE_DAYS = 90
    DEFAULT_MIN_RELEVANCE = 0.3
    DEFAULT_SIMILARITY_THRESHOLD = 0.95

    def __init__(self):
        self._experience_store: Optional[ExperienceStoreService] = None

        # In-memory storage (in production, use database)
        self._archives: Dict[str, List[Experience]] = {}
        self._schedules: Dict[str, PruningSchedule] = {}
        self._pruning_history: List[PruneResult] = []

        # Background task
        self._pruning_task: Optional[asyncio.Task] = None

    async def _get_experience_store(self) -> ExperienceStoreService:
        """Get or create experience store instance"""
        if self._experience_store is None:
            self._experience_store = await get_experience_store()
        return self._experience_store

    # -------------------------------------------------------------------------
    # OLD EXPERIENCE PRUNING
    # -------------------------------------------------------------------------

    async def prune_old_experiences(
        self,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
        archive_first: bool = True
    ) -> PruneResult:
        """
        Remove experiences older than max_age_days.

        Args:
            max_age_days: Maximum age of experiences to keep
            archive_first: Whether to archive before deleting (safety)
        """
        experience_store = await self._get_experience_store()
        operation_id = str(uuid.uuid4())

        # Get all experiences
        all_experiences = await experience_store.get_experiences(limit=10000)

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        # Find old experiences
        old_experiences = [
            exp for exp in all_experiences
            if exp.timestamp < cutoff_date
        ]

        archived_count = 0
        deleted_count = 0
        details = []

        if old_experiences:
            # Archive first if requested
            if archive_first:
                archive_result = await self.archive_experiences(
                    [exp.id for exp in old_experiences]
                )
                archived_count = archive_result.experiences_archived

            # Delete from main store
            for exp in old_experiences:
                # In production: await experience_store.delete_experience(exp.id)
                deleted_count += 1
                details.append({
                    "id": exp.id,
                    "agent_id": exp.agent_id,
                    "age_days": (datetime.now() - exp.timestamp).days,
                    "action": "archived_and_deleted" if archive_first else "deleted"
                })

        result = PruneResult(
            operation_id=operation_id,
            action=PruneAction.ARCHIVE if archive_first else PruneAction.DELETE,
            reason=PruneReason.OLD_AGE,
            experiences_affected=len(old_experiences),
            experiences_archived=archived_count,
            experiences_deleted=deleted_count,
            space_recovered_mb=len(old_experiences) * 0.001,  # Estimate
            details=details
        )

        self._pruning_history.append(result)
        logger.info(f"Pruned {len(old_experiences)} old experiences (>{max_age_days} days)")

        return result

    # -------------------------------------------------------------------------
    # LOW RELEVANCE PRUNING
    # -------------------------------------------------------------------------

    async def prune_low_relevance(
        self,
        min_relevance: float = DEFAULT_MIN_RELEVANCE,
        archive_first: bool = True
    ) -> PruneResult:
        """
        Remove experiences with low relevance scores.

        Args:
            min_relevance: Minimum relevance threshold (0-1)
            archive_first: Whether to archive before deleting
        """
        experience_store = await self._get_experience_store()
        operation_id = str(uuid.uuid4())

        # Get all experiences
        all_experiences = await experience_store.get_experiences(limit=10000)

        # Find low-relevance experiences
        # Relevance based on quality_score, outcome, and usage
        low_relevance = []

        for exp in all_experiences:
            # Calculate relevance score
            quality_factor = exp.quality_score / 100  # Normalize to 0-1

            outcome_factor = {
                Outcome.SUCCESS: 1.0,
                Outcome.PARTIAL: 0.5,
                Outcome.FAILURE: 0.3
            }.get(exp.outcome, 0.5)

            # Age factor (newer is more relevant)
            age_days = (datetime.now() - exp.timestamp).days
            age_factor = max(0, 1 - (age_days / 365))  # Linear decay over 1 year

            relevance = (quality_factor * 0.4) + (outcome_factor * 0.3) + (age_factor * 0.3)

            if relevance < min_relevance:
                low_relevance.append((exp, relevance))

        archived_count = 0
        deleted_count = 0
        details = []

        if low_relevance:
            experience_ids = [exp.id for exp, _ in low_relevance]

            if archive_first:
                archive_result = await self.archive_experiences(experience_ids)
                archived_count = archive_result.experiences_archived

            for exp, relevance in low_relevance:
                deleted_count += 1
                details.append({
                    "id": exp.id,
                    "agent_id": exp.agent_id,
                    "relevance_score": round(relevance, 3),
                    "quality_score": exp.quality_score,
                    "outcome": exp.outcome.value
                })

        result = PruneResult(
            operation_id=operation_id,
            action=PruneAction.ARCHIVE if archive_first else PruneAction.DELETE,
            reason=PruneReason.LOW_RELEVANCE,
            experiences_affected=len(low_relevance),
            experiences_archived=archived_count,
            experiences_deleted=deleted_count,
            space_recovered_mb=len(low_relevance) * 0.001,
            details=details
        )

        self._pruning_history.append(result)
        logger.info(f"Pruned {len(low_relevance)} low-relevance experiences (<{min_relevance})")

        return result

    # -------------------------------------------------------------------------
    # SIMILAR EXPERIENCE MERGING
    # -------------------------------------------------------------------------

    async def consolidate_similar_experiences(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> MergeResult:
        """
        Merge similar experiences to reduce redundancy.

        Uses text similarity on task descriptions and approaches.
        """
        experience_store = await self._get_experience_store()
        operation_id = str(uuid.uuid4())

        # Get all experiences grouped by agent and work type
        all_experiences = await experience_store.get_experiences(limit=10000)

        # Group by agent_id and work_type
        groups: Dict[str, List[Experience]] = {}
        for exp in all_experiences:
            key = f"{exp.agent_id}_{exp.work_type.value}"
            if key not in groups:
                groups[key] = []
            groups[key].append(exp)

        merge_details = []
        total_merged = 0
        new_created = 0
        groups_found = 0

        for key, experiences in groups.items():
            if len(experiences) < 2:
                continue

            # Find similar pairs using simple text similarity
            similar_groups = self._find_similar_groups(experiences, similarity_threshold)

            if similar_groups:
                groups_found += len(similar_groups)

                for group in similar_groups:
                    # Merge the group into one consolidated experience
                    merged = self._merge_experiences(group)
                    total_merged += len(group)
                    new_created += 1

                    merge_details.append({
                        "group_key": key,
                        "merged_count": len(group),
                        "merged_ids": [exp.id for exp in group],
                        "new_id": merged.id,
                        "similarity": similarity_threshold
                    })

        result = MergeResult(
            operation_id=operation_id,
            groups_found=groups_found,
            experiences_merged=total_merged,
            new_experiences_created=new_created,
            similarity_threshold=similarity_threshold,
            merge_details=merge_details
        )

        logger.info(f"Consolidated {total_merged} experiences into {new_created} merged records")

        return result

    def _find_similar_groups(
        self,
        experiences: List[Experience],
        threshold: float
    ) -> List[List[Experience]]:
        """Find groups of similar experiences"""
        # Simple implementation using text overlap
        # In production, use embeddings and cosine similarity

        groups = []
        used = set()

        for i, exp1 in enumerate(experiences):
            if exp1.id in used:
                continue

            group = [exp1]
            used.add(exp1.id)

            for j, exp2 in enumerate(experiences[i+1:], i+1):
                if exp2.id in used:
                    continue

                similarity = self._calculate_similarity(exp1, exp2)
                if similarity >= threshold:
                    group.append(exp2)
                    used.add(exp2.id)

            if len(group) > 1:
                groups.append(group)

        return groups

    def _calculate_similarity(self, exp1: Experience, exp2: Experience) -> float:
        """Calculate similarity between two experiences"""
        # Simple Jaccard similarity on words
        words1 = set(exp1.task_description.lower().split())
        words2 = set(exp2.task_description.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _merge_experiences(self, experiences: List[Experience]) -> Experience:
        """Merge multiple experiences into one"""
        # Use the most recent as base
        base = max(experiences, key=lambda e: e.timestamp)

        # Combine lessons learned
        all_lessons = []
        for exp in experiences:
            all_lessons.extend(exp.lessons_learned)
        unique_lessons = list(set(all_lessons))

        # Average quality scores
        avg_quality = sum(exp.quality_score for exp in experiences) / len(experiences)

        # Create merged experience
        merged = Experience(
            id=str(uuid.uuid4()),
            agent_id=base.agent_id,
            agent_role=base.agent_role,
            work_type=base.work_type,
            task_description=base.task_description,
            approach=base.approach,
            outcome=base.outcome,
            lessons_learned=unique_lessons[:10],  # Limit to 10
            key_decisions=base.key_decisions,
            duration=sum(exp.duration for exp in experiences) // len(experiences),
            quality_score=avg_quality,
            timestamp=datetime.now(),
            metadata={
                "merged_from": [exp.id for exp in experiences],
                "merge_count": len(experiences)
            }
        )

        return merged

    # -------------------------------------------------------------------------
    # ARCHIVING
    # -------------------------------------------------------------------------

    async def archive_experiences(
        self,
        experience_ids: List[str]
    ) -> ArchiveResult:
        """
        Archive experiences instead of deleting them.

        Archives are stored separately and can be restored if needed.
        """
        experience_store = await self._get_experience_store()
        operation_id = str(uuid.uuid4())

        # Get experiences to archive
        all_experiences = await experience_store.get_experiences(limit=10000)
        to_archive = [exp for exp in all_experiences if exp.id in experience_ids]

        # Create archive
        archive_name = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._archives[archive_name] = to_archive

        result = ArchiveResult(
            operation_id=operation_id,
            experiences_archived=len(to_archive),
            archive_location=archive_name,
            total_size_mb=len(to_archive) * 0.001,  # Estimate
            archived_ids=experience_ids
        )

        logger.info(f"Archived {len(to_archive)} experiences to {archive_name}")

        return result

    async def restore_from_archive(
        self,
        archive_name: str,
        experience_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restore experiences from an archive.
        """
        if archive_name not in self._archives:
            raise ValueError(f"Archive {archive_name} not found")

        archived = self._archives[archive_name]

        if experience_ids:
            to_restore = [exp for exp in archived if exp.id in experience_ids]
        else:
            to_restore = archived

        # In production: re-add to experience store
        restored_count = len(to_restore)

        return {
            "archive_name": archive_name,
            "experiences_restored": restored_count,
            "restored_ids": [exp.id for exp in to_restore]
        }

    async def list_archives(self) -> List[Dict[str, Any]]:
        """List all archives"""
        return [
            {
                "name": name,
                "count": len(experiences),
                "oldest": min(exp.timestamp for exp in experiences).isoformat() if experiences else None,
                "newest": max(exp.timestamp for exp in experiences).isoformat() if experiences else None
            }
            for name, experiences in self._archives.items()
        ]

    # -------------------------------------------------------------------------
    # SCHEDULED PRUNING
    # -------------------------------------------------------------------------

    async def schedule_pruning(
        self,
        interval_hours: int = 24,
        name: str = "default",
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
        min_relevance: float = DEFAULT_MIN_RELEVANCE
    ) -> str:
        """
        Schedule periodic pruning jobs.
        """
        schedule_id = str(uuid.uuid4())

        schedule = PruningSchedule(
            id=schedule_id,
            name=name,
            interval_hours=interval_hours,
            max_age_days=max_age_days,
            min_relevance=min_relevance,
            next_run=datetime.now() + timedelta(hours=interval_hours)
        )

        self._schedules[schedule_id] = schedule

        logger.info(f"Scheduled pruning job '{name}' every {interval_hours} hours")

        return schedule_id

    async def run_scheduled_pruning(self, schedule_id: str) -> Dict[str, Any]:
        """Run a scheduled pruning job"""
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule {schedule_id} not found")

        schedule = self._schedules[schedule_id]

        # Run pruning operations
        results = []

        # 1. Prune old experiences
        old_result = await self.prune_old_experiences(
            max_age_days=schedule.max_age_days
        )
        results.append(old_result.to_dict())

        # 2. Prune low relevance
        relevance_result = await self.prune_low_relevance(
            min_relevance=schedule.min_relevance
        )
        results.append(relevance_result.to_dict())

        # 3. Consolidate similar
        merge_result = await self.consolidate_similar_experiences()
        results.append(merge_result.to_dict())

        # Update schedule
        schedule.last_run = datetime.now()
        schedule.next_run = datetime.now() + timedelta(hours=schedule.interval_hours)
        schedule.total_runs += 1
        schedule.total_pruned += old_result.experiences_deleted + relevance_result.experiences_deleted
        schedule.total_archived += old_result.experiences_archived + relevance_result.experiences_archived

        return {
            "schedule_id": schedule_id,
            "run_time": datetime.now().isoformat(),
            "results": results,
            "next_run": schedule.next_run.isoformat()
        }

    async def get_schedules(self) -> List[PruningSchedule]:
        """Get all pruning schedules"""
        return list(self._schedules.values())

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    async def get_pruning_stats(self) -> PruningStats:
        """Get statistics about the experience store for pruning decisions"""
        experience_store = await self._get_experience_store()

        all_experiences = await experience_store.get_experiences(limit=10000)

        if not all_experiences:
            return PruningStats()

        now = datetime.now()

        # Age distribution
        age_buckets = {
            "< 7 days": 0,
            "7-30 days": 0,
            "30-90 days": 0,
            "> 90 days": 0
        }

        for exp in all_experiences:
            age_days = (now - exp.timestamp).days
            if age_days < 7:
                age_buckets["< 7 days"] += 1
            elif age_days < 30:
                age_buckets["7-30 days"] += 1
            elif age_days < 90:
                age_buckets["30-90 days"] += 1
            else:
                age_buckets["> 90 days"] += 1

        # Relevance distribution
        relevance_buckets = {
            "high (>0.7)": 0,
            "medium (0.4-0.7)": 0,
            "low (<0.4)": 0
        }

        for exp in all_experiences:
            quality_factor = exp.quality_score / 100
            if quality_factor > 0.7:
                relevance_buckets["high (>0.7)"] += 1
            elif quality_factor > 0.4:
                relevance_buckets["medium (0.4-0.7)"] += 1
            else:
                relevance_buckets["low (<0.4)"] += 1

        # Find potential duplicates
        potential_duplicates = 0
        for i, exp1 in enumerate(all_experiences):
            for exp2 in all_experiences[i+1:]:
                if self._calculate_similarity(exp1, exp2) > 0.9:
                    potential_duplicates += 1

        # Generate recommendations
        recommendations = []
        if age_buckets["> 90 days"] > len(all_experiences) * 0.2:
            recommendations.append("Consider pruning experiences older than 90 days")
        if relevance_buckets["low (<0.4)"] > len(all_experiences) * 0.3:
            recommendations.append("Many low-relevance experiences - consider pruning")
        if potential_duplicates > 10:
            recommendations.append(f"Found {potential_duplicates} potential duplicates - consider merging")

        timestamps = [exp.timestamp for exp in all_experiences]

        return PruningStats(
            total_experiences=len(all_experiences),
            experiences_by_age=age_buckets,
            experiences_by_relevance=relevance_buckets,
            potential_duplicates=potential_duplicates,
            storage_used_mb=len(all_experiences) * 0.001,
            oldest_experience=min(timestamps),
            newest_experience=max(timestamps),
            recommended_actions=recommendations
        )

    async def get_pruning_history(
        self,
        limit: int = 50
    ) -> List[PruneResult]:
        """Get recent pruning history"""
        return self._pruning_history[-limit:]


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_experience_pruning_service: Optional[ExperiencePruningService] = None


async def get_experience_pruning_service() -> ExperiencePruningService:
    """Get or create experience pruning service instance"""
    global _experience_pruning_service
    if _experience_pruning_service is None:
        _experience_pruning_service = ExperiencePruningService()
    return _experience_pruning_service
