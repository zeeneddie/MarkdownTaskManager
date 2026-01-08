"""
Sync Engine - Bidirectional synchronization between Markdown files and PostgreSQL database
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import logging

from parser import MultiFileProjectParser
from generator import MultiFileProjectGenerator

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Handles bidirectional sync between markdown files and database.

    Markdown is the source of truth for structure and content.
    Database tracks timestamps and provides query capabilities.
    """

    def __init__(self, project_root: Path, db_session: AsyncSession):
        self.project_root = Path(project_root)
        self.parser = MultiFileProjectParser(project_root)
        self.generator = MultiFileProjectGenerator(project_root)
        self.db = db_session

    async def sync_from_markdown(self, incremental: bool = False) -> Dict:
        """
        Parse markdown files and sync to database.

        Args:
            incremental: If True, only sync changed files (check file mtime)

        Returns:
            Dict with sync statistics
        """
        logger.info("Starting sync from markdown to database")

        stats = {
            "epics_created": 0,
            "epics_updated": 0,
            "features_created": 0,
            "features_updated": 0,
            "stories_created": 0,
            "stories_updated": 0,
            "tasks_created": 0,
            "tasks_updated": 0,
            "errors": []
        }

        try:
            # Parse entire project structure
            project_data = self.parser.parse_project()

            # Sync epics
            for epic in project_data.get("epics", []):
                try:
                    result = await self._sync_epic_to_db(epic)
                    if result == "created":
                        stats["epics_created"] += 1
                    elif result == "updated":
                        stats["epics_updated"] += 1

                    # Sync nested features
                    for feature in epic.get("features", []):
                        result = await self._sync_feature_to_db(feature)
                        if result == "created":
                            stats["features_created"] += 1
                        elif result == "updated":
                            stats["features_updated"] += 1

                        # Sync nested stories
                        for story in feature.get("stories", []):
                            result = await self._sync_story_to_db(story)
                            if result == "created":
                                stats["stories_created"] += 1
                            elif result == "updated":
                                stats["stories_updated"] += 1

                            # Sync nested tasks
                            for task in story.get("tasks", []):
                                result = await self._sync_task_to_db(task)
                                if result == "created":
                                    stats["tasks_created"] += 1
                                elif result == "updated":
                                    stats["tasks_updated"] += 1

                except Exception as e:
                    error_msg = f"Error syncing epic {epic.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

            await self.db.commit()

        except Exception as e:
            error_msg = f"Fatal error during sync: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            await self.db.rollback()

        logger.info(f"Sync from markdown complete: {stats}")
        return stats

    async def sync_from_database(self, epic_ids: Optional[List[str]] = None) -> Dict:
        """
        Query database and generate markdown files.

        Args:
            epic_ids: Optional list of epic IDs to sync. If None, sync all.

        Returns:
            Dict with sync statistics
        """
        logger.info("Starting sync from database to markdown")

        stats = {
            "epics_generated": 0,
            "features_generated": 0,
            "stories_generated": 0,
            "tasks_generated": 0,
            "errors": []
        }

        try:
            # Query epics from database
            # TODO: Implement actual database queries once models are defined
            # For now, this is a placeholder structure

            # Example structure (to be replaced with actual DB queries):
            # epics = await self._query_epics(epic_ids)
            # for epic in epics:
            #     self.generator.generate_epic(epic)
            #     stats["epics_generated"] += 1

            logger.warning("Database sync not yet implemented - waiting for database models")

        except Exception as e:
            error_msg = f"Fatal error during sync: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

        logger.info(f"Sync from database complete: {stats}")
        return stats

    async def _sync_epic_to_db(self, epic: Dict) -> str:
        """
        Sync single epic to database.

        Returns:
            'created', 'updated', or 'unchanged'
        """
        # TODO: Implement once Epic model is defined
        # Check if epic exists
        # If exists, check if updated (compare timestamps)
        # If not exists or updated, insert/update

        logger.debug(f"Syncing epic {epic.get('id')} to database")
        return "created"  # Placeholder

    async def _sync_feature_to_db(self, feature: Dict) -> str:
        """Sync single feature to database"""
        logger.debug(f"Syncing feature {feature.get('id')} to database")
        return "created"  # Placeholder

    async def _sync_story_to_db(self, story: Dict) -> str:
        """Sync single story to database"""
        logger.debug(f"Syncing story {story.get('id')} to database")
        return "created"  # Placeholder

    async def _sync_task_to_db(self, task: Dict) -> str:
        """Sync single task to database"""
        logger.debug(f"Syncing task {task.get('id')} to database")
        return "created"  # Placeholder

    async def detect_conflicts(self) -> List[Dict]:
        """
        Detect conflicts between markdown files and database.

        A conflict occurs when:
        - Markdown file updated_at > database updated_at AND
        - Database updated_at > last sync time

        Returns:
            List of conflict dicts with details
        """
        conflicts = []

        # TODO: Implement conflict detection
        # Compare markdown file mtimes with database timestamps
        # Return list of items with conflicts

        return conflicts

    async def resolve_conflicts(self, resolution: str = "markdown_wins"):
        """
        Resolve conflicts between markdown and database.

        Args:
            resolution: Strategy for conflict resolution
                - "markdown_wins": Markdown always takes precedence (default)
                - "database_wins": Database always takes precedence
                - "latest_wins": Most recent timestamp wins
                - "manual": Raise exception for manual resolution
        """
        conflicts = await self.detect_conflicts()

        if not conflicts:
            logger.info("No conflicts to resolve")
            return

        logger.info(f"Resolving {len(conflicts)} conflicts with strategy: {resolution}")

        for conflict in conflicts:
            if resolution == "markdown_wins":
                # Re-sync from markdown
                await self.sync_from_markdown()
            elif resolution == "database_wins":
                # Re-generate markdown
                await self.sync_from_database()
            elif resolution == "latest_wins":
                # Compare timestamps and choose winner
                # TODO: Implement timestamp comparison
                pass
            elif resolution == "manual":
                raise ValueError(f"Manual conflict resolution required: {conflict}")


# Convenience functions for API endpoints

async def sync_markdown_to_db(project_root: Path, db_session: AsyncSession) -> Dict:
    """
    Convenience function to sync markdown to database.

    Usage in FastAPI endpoint:
        stats = await sync_markdown_to_db(project_root, db)
    """
    engine = SyncEngine(project_root, db_session)
    return await engine.sync_from_markdown()


async def sync_db_to_markdown(project_root: Path, db_session: AsyncSession,
                               epic_ids: Optional[List[str]] = None) -> Dict:
    """
    Convenience function to sync database to markdown.

    Usage in FastAPI endpoint:
        stats = await sync_db_to_markdown(project_root, db, ["EPIC-001"])
    """
    engine = SyncEngine(project_root, db_session)
    return await engine.sync_from_database(epic_ids)
