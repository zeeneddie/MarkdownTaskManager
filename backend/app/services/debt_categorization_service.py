"""
Debt Categorization Service

Links technical debt items to backlog hierarchy (epic/feature/story)
for categorized issue tracking and weak spot identification.

Week 80+: Implements file-to-backlog mapping and statistics aggregation.
"""

import logging
import fnmatch
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technical_debt import (
    TechnicalDebtItem,
    TechnicalDebtSnapshot,
    DebtSeverity,
    DebtType,
)
from app.models.task_hierarchy import Epic, Feature, Story, Task

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class FileBacklogMapping:
    """Represents a file pattern to backlog item mapping."""

    def __init__(
        self,
        id: int,
        project_id: int,
        file_pattern: str,
        epic_id: Optional[UUID] = None,
        feature_id: Optional[UUID] = None,
        story_id: Optional[UUID] = None,
        priority: int = 0,
    ):
        self.id = id
        self.project_id = project_id
        self.file_pattern = file_pattern
        self.epic_id = epic_id
        self.feature_id = feature_id
        self.story_id = story_id
        self.priority = priority


class BacklogDebtStats:
    """Statistics for debt items linked to a backlog item."""

    def __init__(
        self,
        backlog_type: str,  # epic, feature, story
        backlog_id: UUID,
        backlog_title: str,
        total_issues: int = 0,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        total_principal: float = 0.0,
        total_interest: float = 0.0,
        issues_by_type: Optional[Dict[str, int]] = None,
        health_score: float = 100.0,
    ):
        self.backlog_type = backlog_type
        self.backlog_id = backlog_id
        self.backlog_title = backlog_title
        self.total_issues = total_issues
        self.critical_count = critical_count
        self.high_count = high_count
        self.medium_count = medium_count
        self.low_count = low_count
        self.total_principal = total_principal
        self.total_interest = total_interest
        self.issues_by_type = issues_by_type or {}
        self.health_score = health_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backlog_type": self.backlog_type,
            "backlog_id": str(self.backlog_id),
            "backlog_title": self.backlog_title,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "total_principal": self.total_principal,
            "total_interest": self.total_interest,
            "issues_by_type": self.issues_by_type,
            "health_score": self.health_score,
        }


# ============================================================================
# MAIN SERVICE (ASYNC)
# ============================================================================

class DebtCategorizationService:
    """
    Service for categorizing technical debt items by backlog hierarchy.

    Features:
    - Auto-categorize debt items based on file paths
    - Calculate statistics per epic/feature/story
    - Identify weak spots in the codebase
    - Generate health scores for backlog items
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # FILE PATH MAPPING
    # ========================================================================

    async def create_file_mapping(
        self,
        project_id: int,
        file_pattern: str,
        epic_id: Optional[UUID] = None,
        feature_id: Optional[UUID] = None,
        story_id: Optional[UUID] = None,
        priority: int = 0,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a mapping between a file pattern and a backlog item.

        File patterns support glob syntax:
        - '*' matches any characters within a path segment
        - '**' matches any path segments
        - '?' matches a single character

        Examples:
        - 'src/auth/*' -> All files in src/auth/
        - 'src/api/**/*.php' -> All PHP files under src/api/
        - 'src/models/User.php' -> Exact file
        """
        result = await self.db.execute(
            text("""
                INSERT INTO file_backlog_mappings
                (project_id, file_pattern, epic_id, feature_id, story_id, priority, created_by)
                VALUES (:project_id, :file_pattern, :epic_id, :feature_id, :story_id, :priority, :created_by)
                RETURNING id
            """),
            {
                "project_id": project_id,
                "file_pattern": file_pattern,
                "epic_id": str(epic_id) if epic_id else None,
                "feature_id": str(feature_id) if feature_id else None,
                "story_id": str(story_id) if story_id else None,
                "priority": priority,
                "created_by": created_by,
            }
        )
        await self.db.commit()
        row = result.fetchone()
        mapping_id = row[0] if row else 0

        return {
            "id": mapping_id,
            "project_id": project_id,
            "file_pattern": file_pattern,
            "epic_id": str(epic_id) if epic_id else None,
            "feature_id": str(feature_id) if feature_id else None,
            "story_id": str(story_id) if story_id else None,
            "priority": priority,
        }

    async def get_file_mappings(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all file mappings for a project."""
        result = await self.db.execute(
            text("""
                SELECT id, project_id, file_pattern, epic_id, feature_id, story_id, priority, created_at
                FROM file_backlog_mappings
                WHERE project_id = :project_id
                ORDER BY priority DESC, created_at
            """),
            {"project_id": project_id}
        )

        return [
            {
                "id": row[0],
                "project_id": row[1],
                "file_pattern": row[2],
                "epic_id": str(row[3]) if row[3] else None,
                "feature_id": str(row[4]) if row[4] else None,
                "story_id": str(row[5]) if row[5] else None,
                "priority": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
            }
            for row in result.fetchall()
        ]

    async def delete_file_mapping(self, mapping_id: int) -> bool:
        """Delete a file mapping."""
        result = await self.db.execute(
            text("DELETE FROM file_backlog_mappings WHERE id = :id"),
            {"id": mapping_id}
        )
        await self.db.commit()
        return result.rowcount > 0

    async def find_backlog_for_file(
        self,
        project_id: int,
        file_path: str
    ) -> Optional[Tuple[Optional[UUID], Optional[UUID], Optional[UUID]]]:
        """
        Find the best matching backlog item for a file path.

        Returns tuple of (epic_id, feature_id, story_id) or None.
        Uses priority ordering for multiple matches.
        """
        # Get all mappings for this project ordered by priority
        result = await self.db.execute(
            text("""
                SELECT file_pattern, epic_id, feature_id, story_id, priority
                FROM file_backlog_mappings
                WHERE project_id = :project_id
                ORDER BY priority DESC
            """),
            {"project_id": project_id}
        )

        best_match = None
        best_priority = -1

        for row in result.fetchall():
            pattern, epic_id, feature_id, story_id, priority = row

            # Check if file matches pattern
            if self._matches_pattern(file_path, pattern):
                if priority > best_priority:
                    best_priority = priority
                    best_match = (epic_id, feature_id, story_id)

        return best_match

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if a file path matches a glob pattern."""
        # Normalize paths
        file_path = file_path.replace("\\", "/")
        pattern = pattern.replace("\\", "/")

        # Handle ** for recursive matching
        if "**" in pattern:
            # Split on ** and match parts
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                if prefix and not file_path.startswith(prefix.rstrip("/")):
                    return False
                if suffix and not fnmatch.fnmatch(file_path, f"*{suffix}"):
                    return False
                return True

        # Use fnmatch for standard glob patterns
        return fnmatch.fnmatch(file_path, pattern)

    # ========================================================================
    # AUTO-CATEGORIZATION
    # ========================================================================

    async def auto_categorize_debt_items(
        self,
        project_id: int,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Auto-categorize uncategorized debt items based on file mappings.

        Returns statistics about categorization.
        """
        # Get uncategorized debt items
        result = await self.db.execute(
            text("""
                SELECT id, file_path
                FROM technical_debt_items
                WHERE project_id = :project_id
                  AND epic_id IS NULL
                  AND feature_id IS NULL
                  AND story_id IS NULL
                LIMIT :limit
            """),
            {"project_id": project_id, "limit": limit}
        )

        items = result.fetchall()
        categorized = 0
        skipped = 0

        for item_id, file_path in items:
            if not file_path:
                skipped += 1
                continue

            backlog = await self.find_backlog_for_file(project_id, file_path)
            if backlog:
                epic_id, feature_id, story_id = backlog
                await self.db.execute(
                    text("""
                        UPDATE technical_debt_items
                        SET epic_id = :epic_id,
                            feature_id = :feature_id,
                            story_id = :story_id,
                            categorization_source = 'auto',
                            categorized_at = :now
                        WHERE id = :id
                    """),
                    {
                        "id": item_id,
                        "epic_id": str(epic_id) if epic_id else None,
                        "feature_id": str(feature_id) if feature_id else None,
                        "story_id": str(story_id) if story_id else None,
                        "now": datetime.utcnow(),
                    }
                )
                categorized += 1
            else:
                skipped += 1

        await self.db.commit()

        return {
            "total_processed": len(items),
            "categorized": categorized,
            "skipped": skipped,
            "project_id": project_id,
        }

    async def manually_categorize_debt_item(
        self,
        item_id: int,
        epic_id: Optional[UUID] = None,
        feature_id: Optional[UUID] = None,
        story_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Manually assign a debt item to a backlog item."""
        await self.db.execute(
            text("""
                UPDATE technical_debt_items
                SET epic_id = :epic_id,
                    feature_id = :feature_id,
                    story_id = :story_id,
                    categorization_source = 'manual',
                    categorized_at = :now
                WHERE id = :id
            """),
            {
                "id": item_id,
                "epic_id": str(epic_id) if epic_id else None,
                "feature_id": str(feature_id) if feature_id else None,
                "story_id": str(story_id) if story_id else None,
                "now": datetime.utcnow(),
            }
        )
        await self.db.commit()

        return {"item_id": item_id, "categorized": True}

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_stats_by_epic(self, project_id: int) -> List[Dict[str, Any]]:
        """Get debt statistics aggregated by epic."""
        result = await self.db.execute(
            text("""
                SELECT
                    tdi.epic_id,
                    e.title as epic_title,
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN tdi.severity = 'critical' THEN 1 ELSE 0 END) as critical_count,
                    SUM(CASE WHEN tdi.severity = 'high' THEN 1 ELSE 0 END) as high_count,
                    SUM(CASE WHEN tdi.severity = 'medium' THEN 1 ELSE 0 END) as medium_count,
                    SUM(CASE WHEN tdi.severity = 'low' THEN 1 ELSE 0 END) as low_count,
                    COALESCE(SUM(tdi.principal), 0) as total_principal,
                    COALESCE(SUM(tdi.principal * tdi.interest_rate), 0) as total_interest
                FROM technical_debt_items tdi
                LEFT JOIN task_epics e ON tdi.epic_id = e.id
                WHERE tdi.project_id = :project_id
                  AND tdi.epic_id IS NOT NULL
                GROUP BY tdi.epic_id, e.title
                ORDER BY total_issues DESC
            """),
            {"project_id": project_id}
        )

        stats = []
        for row in result.fetchall():
            total = row[2]
            critical = row[3]
            high = row[4]

            # Calculate health score (100 = perfect, 0 = very bad)
            # Weighted: critical = -10, high = -5, medium = -2, low = -1
            penalty = (critical * 10) + (high * 5) + (row[5] * 2) + (row[6] * 1)
            health = max(0, 100 - min(penalty, 100))

            stats.append({
                "backlog_type": "epic",
                "backlog_id": str(row[0]) if row[0] else None,
                "backlog_title": row[1] or "Uncategorized",
                "total_issues": total,
                "critical_count": critical,
                "high_count": high,
                "medium_count": row[5],
                "low_count": row[6],
                "total_principal": round(row[7], 2),
                "total_interest": round(row[8], 2),
                "health_score": round(health, 1),
            })

        return stats

    async def get_stats_by_feature(self, project_id: int, epic_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get debt statistics aggregated by feature."""
        query = """
            SELECT
                tdi.feature_id,
                f.title as feature_title,
                tdi.epic_id,
                COUNT(*) as total_issues,
                SUM(CASE WHEN tdi.severity = 'critical' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN tdi.severity = 'high' THEN 1 ELSE 0 END) as high_count,
                SUM(CASE WHEN tdi.severity = 'medium' THEN 1 ELSE 0 END) as medium_count,
                SUM(CASE WHEN tdi.severity = 'low' THEN 1 ELSE 0 END) as low_count,
                COALESCE(SUM(tdi.principal), 0) as total_principal,
                COALESCE(SUM(tdi.principal * tdi.interest_rate), 0) as total_interest
            FROM technical_debt_items tdi
            LEFT JOIN task_features f ON tdi.feature_id = f.id
            WHERE tdi.project_id = :project_id
              AND tdi.feature_id IS NOT NULL
        """

        params = {"project_id": project_id}
        if epic_id:
            query += " AND tdi.epic_id = :epic_id"
            params["epic_id"] = str(epic_id)

        query += " GROUP BY tdi.feature_id, f.title, tdi.epic_id ORDER BY total_issues DESC"

        result = await self.db.execute(text(query), params)

        stats = []
        for row in result.fetchall():
            total = row[3]
            critical = row[4]
            high = row[5]

            penalty = (critical * 10) + (high * 5) + (row[6] * 2) + (row[7] * 1)
            health = max(0, 100 - min(penalty, 100))

            stats.append({
                "backlog_type": "feature",
                "backlog_id": str(row[0]) if row[0] else None,
                "backlog_title": row[1] or "Uncategorized",
                "epic_id": str(row[2]) if row[2] else None,
                "total_issues": total,
                "critical_count": critical,
                "high_count": high,
                "medium_count": row[6],
                "low_count": row[7],
                "total_principal": round(row[8], 2),
                "total_interest": round(row[9], 2),
                "health_score": round(health, 1),
            })

        return stats

    async def get_stats_by_story(self, project_id: int, feature_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get debt statistics aggregated by story."""
        query = """
            SELECT
                tdi.story_id,
                s.title as story_title,
                tdi.feature_id,
                COUNT(*) as total_issues,
                SUM(CASE WHEN tdi.severity = 'critical' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN tdi.severity = 'high' THEN 1 ELSE 0 END) as high_count,
                SUM(CASE WHEN tdi.severity = 'medium' THEN 1 ELSE 0 END) as medium_count,
                SUM(CASE WHEN tdi.severity = 'low' THEN 1 ELSE 0 END) as low_count,
                COALESCE(SUM(tdi.principal), 0) as total_principal,
                COALESCE(SUM(tdi.principal * tdi.interest_rate), 0) as total_interest
            FROM technical_debt_items tdi
            LEFT JOIN task_stories s ON tdi.story_id = s.id
            WHERE tdi.project_id = :project_id
              AND tdi.story_id IS NOT NULL
        """

        params = {"project_id": project_id}
        if feature_id:
            query += " AND tdi.feature_id = :feature_id"
            params["feature_id"] = str(feature_id)

        query += " GROUP BY tdi.story_id, s.title, tdi.feature_id ORDER BY total_issues DESC"

        result = await self.db.execute(text(query), params)

        stats = []
        for row in result.fetchall():
            total = row[3]
            critical = row[4]
            high = row[5]

            penalty = (critical * 10) + (high * 5) + (row[6] * 2) + (row[7] * 1)
            health = max(0, 100 - min(penalty, 100))

            stats.append({
                "backlog_type": "story",
                "backlog_id": str(row[0]) if row[0] else None,
                "backlog_title": row[1] or "Uncategorized",
                "feature_id": str(row[2]) if row[2] else None,
                "total_issues": total,
                "critical_count": critical,
                "high_count": high,
                "medium_count": row[6],
                "low_count": row[7],
                "total_principal": round(row[8], 2),
                "total_interest": round(row[9], 2),
                "health_score": round(health, 1),
            })

        return stats

    async def get_uncategorized_stats(self, project_id: int) -> Dict[str, Any]:
        """Get statistics for uncategorized debt items."""
        result = await self.db.execute(
            text("""
                SELECT
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_count,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_count,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium_count,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_count,
                    COALESCE(SUM(principal), 0) as total_principal,
                    COALESCE(SUM(principal * interest_rate), 0) as total_interest
                FROM technical_debt_items
                WHERE project_id = :project_id
                  AND epic_id IS NULL
                  AND feature_id IS NULL
                  AND story_id IS NULL
            """),
            {"project_id": project_id}
        )

        row = result.fetchone()
        if not row:
            return {
                "total_issues": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "total_principal": 0,
                "total_interest": 0,
            }

        return {
            "total_issues": row[0] or 0,
            "critical_count": row[1] or 0,
            "high_count": row[2] or 0,
            "medium_count": row[3] or 0,
            "low_count": row[4] or 0,
            "total_principal": round(row[5] or 0, 2),
            "total_interest": round(row[6] or 0, 2),
        }

    async def get_issues_for_backlog_item(
        self,
        project_id: int,
        backlog_type: str,
        backlog_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get all debt items linked to a specific backlog item."""
        # Map backlog type to column name
        column_map = {
            "epic": "epic_id",
            "feature": "feature_id",
            "story": "story_id",
        }

        if backlog_type not in column_map:
            raise ValueError(f"Invalid backlog_type: {backlog_type}")

        column = column_map[backlog_type]

        result = await self.db.execute(
            text(f"""
                SELECT id, title, description, debt_type, severity, status,
                       file_path, line_start, line_end, function_name,
                       principal, interest_rate, detection_rule, first_detected
                FROM technical_debt_items
                WHERE project_id = :project_id
                  AND {column} = :backlog_id
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    principal DESC
                LIMIT :limit OFFSET :offset
            """),
            {"project_id": project_id, "backlog_id": str(backlog_id), "limit": limit, "offset": offset}
        )

        items = []
        for row in result.fetchall():
            items.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "debt_type": row[3],
                "severity": row[4],
                "status": row[5],
                "file_path": row[6],
                "line_start": row[7],
                "line_end": row[8],
                "function_name": row[9],
                "principal": row[10],
                "interest_rate": row[11],
                "roi": (row[10] * row[11] * 12) / row[10] if row[10] and row[10] > 0 else 0,
                "detection_rule": row[12],
                "first_detected": row[13].isoformat() if row[13] else None,
            })

        return items

    async def get_weak_spots(self, project_id: int, top_n: int = 10) -> Dict[str, Any]:
        """
        Identify weak spots in the codebase.

        Returns the top N backlog items with the most issues,
        grouped by type (epic, feature, story).
        """
        epic_stats = (await self.get_stats_by_epic(project_id))[:top_n]
        feature_stats = (await self.get_stats_by_feature(project_id))[:top_n]
        story_stats = (await self.get_stats_by_story(project_id))[:top_n]
        uncategorized = await self.get_uncategorized_stats(project_id)

        # Sort by health score (lowest first = worst)
        epic_stats.sort(key=lambda x: x["health_score"])
        feature_stats.sort(key=lambda x: x["health_score"])
        story_stats.sort(key=lambda x: x["health_score"])

        return {
            "project_id": project_id,
            "weak_epics": epic_stats[:5],  # Top 5 weakest
            "weak_features": feature_stats[:5],
            "weak_stories": story_stats[:5],
            "uncategorized": uncategorized,
            "summary": {
                "total_epics_with_issues": len(epic_stats),
                "total_features_with_issues": len(feature_stats),
                "total_stories_with_issues": len(story_stats),
                "uncategorized_issues": uncategorized["total_issues"],
            }
        }


# ============================================================================
# FACTORY
# ============================================================================

def get_debt_categorization_service(db: AsyncSession) -> DebtCategorizationService:
    """Factory function to get service instance."""
    return DebtCategorizationService(db)
