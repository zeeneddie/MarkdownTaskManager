"""
GitHub Issues Service - Week 79

Bidirectional synchronization between local tasks and GitHub Issues.
Supports creating, updating, and syncing issues with local task management.
"""

import os
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from app.models.ccpm import GitHubIssueSync, SyncDirection, SyncStatus


class GitHubIssue:
    """GitHub Issue representation."""
    def __init__(
        self,
        number: int,
        title: str,
        body: Optional[str] = None,
        state: str = "open",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[str] = None,
        url: Optional[str] = None,
        github_id: Optional[int] = None
    ):
        self.number = number
        self.title = title
        self.body = body
        self.state = state
        self.labels = labels or []
        self.assignees = assignees or []
        self.milestone = milestone
        self.url = url
        self.github_id = github_id


class SyncResult:
    """Result of a sync operation."""
    def __init__(
        self,
        success: bool,
        created: int = 0,
        updated: int = 0,
        conflicts: int = 0,
        errors: List[str] = None,
        message: str = ""
    ):
        self.success = success
        self.created = created
        self.updated = updated
        self.conflicts = conflicts
        self.errors = errors or []
        self.message = message


class GitHubIssuesService:
    """
    Manages bidirectional synchronization with GitHub Issues.

    Features:
    - Sync GitHub issues to local task system
    - Create GitHub issues from local tasks
    - Bidirectional sync with conflict detection
    - Label and milestone mapping
    - Assignee synchronization
    """

    # Label to local task type mapping
    LABEL_TO_TYPE = {
        "epic": "epic",
        "feature": "feature",
        "story": "story",
        "user-story": "story",
        "task": "task",
        "bug": "bug",
        "enhancement": "feature",
        "documentation": "task"
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"

    async def sync_issues(
        self,
        repo: str,
        project_id: Optional[int] = None,
        direction: str = "bidirectional",
        labels_filter: Optional[List[str]] = None
    ) -> SyncResult:
        """
        Synchronize issues between GitHub and local system.

        Args:
            repo: Repository in "owner/repo" format
            project_id: Optional project association
            direction: Sync direction (github_to_local, local_to_github, bidirectional)
            labels_filter: Only sync issues with these labels

        Returns:
            SyncResult with counts and errors
        """
        if not self.github_token:
            return SyncResult(
                success=False,
                message="GitHub token not configured (GITHUB_TOKEN env var)"
            )

        created = 0
        updated = 0
        conflicts = 0
        errors = []

        try:
            if direction in ["github_to_local", "bidirectional"]:
                result = await self._sync_from_github(
                    repo, project_id, labels_filter
                )
                created += result.created
                updated += result.updated
                conflicts += result.conflicts
                errors.extend(result.errors)

            if direction in ["local_to_github", "bidirectional"]:
                result = await self._sync_to_github(repo, project_id)
                created += result.created
                updated += result.updated
                conflicts += result.conflicts
                errors.extend(result.errors)

            return SyncResult(
                success=len(errors) == 0,
                created=created,
                updated=updated,
                conflicts=conflicts,
                errors=errors,
                message=f"Sync complete: {created} created, {updated} updated, {conflicts} conflicts"
            )

        except Exception as e:
            return SyncResult(
                success=False,
                errors=[str(e)],
                message=f"Sync failed: {e}"
            )

    async def _sync_from_github(
        self,
        repo: str,
        project_id: Optional[int],
        labels_filter: Optional[List[str]]
    ) -> SyncResult:
        """Sync issues from GitHub to local."""
        created = 0
        updated = 0
        errors = []

        # Fetch issues from GitHub
        issues = await self._fetch_github_issues(repo, labels_filter)

        for issue in issues:
            try:
                # Check if issue already synced
                existing = await self._get_synced_issue(
                    repo, issue["number"]
                )

                if existing:
                    # Update if GitHub is newer
                    github_updated = datetime.fromisoformat(
                        issue["updated_at"].replace("Z", "+00:00")
                    )

                    if existing.github_updated_at and github_updated > existing.github_updated_at:
                        await self._update_local_from_github(existing, issue)
                        updated += 1
                else:
                    # Create new sync record
                    await self._create_sync_record(repo, issue, project_id)
                    created += 1

            except Exception as e:
                errors.append(f"Issue #{issue['number']}: {e}")

        return SyncResult(
            success=len(errors) == 0,
            created=created,
            updated=updated,
            errors=errors
        )

    async def _sync_to_github(
        self,
        repo: str,
        project_id: Optional[int]
    ) -> SyncResult:
        """Sync local tasks to GitHub issues."""
        created = 0
        updated = 0
        errors = []

        # Get local tasks that need syncing
        query = select(GitHubIssueSync).where(
            and_(
                GitHubIssueSync.github_repo == repo,
                GitHubIssueSync.sync_status == SyncStatus.PENDING.value
            )
        )

        if project_id:
            query = query.where(GitHubIssueSync.project_id == project_id)

        result = await self.db.execute(query)
        pending_syncs = result.scalars().all()

        for sync_record in pending_syncs:
            try:
                if sync_record.github_issue_number:
                    # Update existing issue
                    await self._update_github_issue(
                        repo,
                        sync_record.github_issue_number,
                        sync_record
                    )
                    updated += 1
                else:
                    # Create new issue
                    issue = await self._create_github_issue(repo, sync_record)
                    sync_record.github_issue_number = issue["number"]
                    sync_record.github_issue_id = issue["id"]
                    sync_record.github_url = issue["html_url"]
                    created += 1

                sync_record.sync_status = SyncStatus.SYNCED.value
                sync_record.last_synced_at = datetime.utcnow()
                sync_record.sync_error = None

            except Exception as e:
                errors.append(f"Task {sync_record.id}: {e}")
                sync_record.sync_status = SyncStatus.ERROR.value
                sync_record.sync_error = str(e)

        await self.db.commit()

        return SyncResult(
            success=len(errors) == 0,
            created=created,
            updated=updated,
            errors=errors
        )

    async def create_issue_from_task(
        self,
        task_id: UUID,
        task_type: str,
        title: str,
        body: str,
        repo: str,
        project_id: Optional[int] = None,
        labels: Optional[List[str]] = None
    ) -> GitHubIssue:
        """
        Create a GitHub issue from a local task.

        Args:
            task_id: Local task identifier
            task_type: Type of task (epic, feature, story, task)
            title: Issue title
            body: Issue body
            repo: Target repository
            project_id: Optional project association
            labels: Additional labels

        Returns:
            Created GitHubIssue
        """
        if not self.github_token:
            raise ValueError("GitHub token not configured")

        # Add type label
        all_labels = [task_type] if task_type else []
        if labels:
            all_labels.extend(labels)

        # Create on GitHub
        issue_data = {
            "title": title,
            "body": body,
            "labels": all_labels
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/repos/{repo}/issues",
                headers=self._get_headers(),
                json=issue_data
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create issue: {error}")

                issue = await response.json()

        # Create sync record
        sync_record = GitHubIssueSync(
            id=uuid.uuid4(),
            project_id=project_id,
            github_repo=repo,
            github_issue_number=issue["number"],
            github_issue_id=issue["id"],
            local_task_id=task_id,
            local_task_type=task_type,
            title=title,
            body=body,
            state=issue["state"],
            labels=[l["name"] for l in issue.get("labels", [])],
            assignees=[a["login"] for a in issue.get("assignees", [])],
            github_url=issue["html_url"],
            sync_direction=SyncDirection.LOCAL_TO_GITHUB.value,
            sync_status=SyncStatus.SYNCED.value,
            last_synced_at=datetime.utcnow(),
            github_updated_at=datetime.fromisoformat(
                issue["updated_at"].replace("Z", "+00:00")
            )
        )

        self.db.add(sync_record)
        await self.db.commit()

        return GitHubIssue(
            number=issue["number"],
            title=issue["title"],
            body=issue.get("body"),
            state=issue["state"],
            labels=[l["name"] for l in issue.get("labels", [])],
            url=issue["html_url"],
            github_id=issue["id"]
        )

    async def update_task_from_issue(
        self,
        repo: str,
        issue_number: int
    ) -> Optional[GitHubIssueSync]:
        """
        Update local task from GitHub issue.

        Returns:
            Updated sync record or None
        """
        sync_record = await self._get_synced_issue(repo, issue_number)
        if not sync_record:
            return None

        # Fetch latest from GitHub
        issue = await self._fetch_single_issue(repo, issue_number)
        if not issue:
            return None

        await self._update_local_from_github(sync_record, issue)
        return sync_record

    async def get_synced_issues(
        self,
        repo: Optional[str] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[GitHubIssueSync]:
        """Get synced issues with optional filters."""
        query = select(GitHubIssueSync)

        if repo:
            query = query.where(GitHubIssueSync.github_repo == repo)
        if project_id:
            query = query.where(GitHubIssueSync.project_id == project_id)
        if status:
            query = query.where(GitHubIssueSync.sync_status == status)

        query = query.order_by(GitHubIssueSync.updated_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def detect_conflicts(self, repo: str) -> List[Dict[str, Any]]:
        """
        Detect sync conflicts between local and GitHub.

        Returns:
            List of conflicting issues
        """
        conflicts = []

        synced = await self.get_synced_issues(repo=repo)

        for sync_record in synced:
            issue = await self._fetch_single_issue(
                repo, sync_record.github_issue_number
            )

            if not issue:
                continue

            github_updated = datetime.fromisoformat(
                issue["updated_at"].replace("Z", "+00:00")
            )

            # Both sides modified since last sync
            if (
                sync_record.last_synced_at and
                sync_record.local_updated_at and
                github_updated > sync_record.last_synced_at and
                sync_record.local_updated_at > sync_record.last_synced_at
            ):
                conflicts.append({
                    "issue_number": sync_record.github_issue_number,
                    "title": sync_record.title,
                    "github_updated": github_updated.isoformat(),
                    "local_updated": sync_record.local_updated_at.isoformat(),
                    "last_synced": sync_record.last_synced_at.isoformat()
                })

        return conflicts

    async def resolve_conflict(
        self,
        repo: str,
        issue_number: int,
        resolution: str  # "use_github" or "use_local"
    ) -> GitHubIssueSync:
        """
        Resolve a sync conflict.

        Args:
            repo: Repository
            issue_number: Issue number
            resolution: Which version to keep

        Returns:
            Resolved sync record
        """
        sync_record = await self._get_synced_issue(repo, issue_number)
        if not sync_record:
            raise ValueError(f"Issue #{issue_number} not found in sync records")

        if resolution == "use_github":
            issue = await self._fetch_single_issue(repo, issue_number)
            await self._update_local_from_github(sync_record, issue)

        elif resolution == "use_local":
            await self._update_github_issue(repo, issue_number, sync_record)
            sync_record.sync_status = SyncStatus.SYNCED.value
            sync_record.last_synced_at = datetime.utcnow()
            await self.db.commit()

        else:
            raise ValueError(f"Invalid resolution: {resolution}")

        return sync_record

    async def get_statistics(
        self,
        repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sync statistics."""
        query = select(GitHubIssueSync)
        if repo:
            query = query.where(GitHubIssueSync.github_repo == repo)

        result = await self.db.execute(query)
        records = result.scalars().all()

        status_counts = {}
        type_counts = {}
        repos = set()

        for record in records:
            status_counts[record.sync_status] = status_counts.get(record.sync_status, 0) + 1
            if record.local_task_type:
                type_counts[record.local_task_type] = type_counts.get(record.local_task_type, 0) + 1
            repos.add(record.github_repo)

        return {
            "total_synced": len(records),
            "status_counts": status_counts,
            "type_counts": type_counts,
            "repositories": list(repos),
            "synced_count": status_counts.get(SyncStatus.SYNCED.value, 0),
            "pending_count": status_counts.get(SyncStatus.PENDING.value, 0),
            "error_count": status_counts.get(SyncStatus.ERROR.value, 0),
            "conflict_count": status_counts.get(SyncStatus.CONFLICT.value, 0)
        }

    # Private helper methods

    def _get_headers(self) -> Dict[str, str]:
        """Get GitHub API headers."""
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def _fetch_github_issues(
        self,
        repo: str,
        labels: Optional[List[str]] = None,
        state: str = "all"
    ) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub API."""
        params = {"state": state, "per_page": 100}
        if labels:
            params["labels"] = ",".join(labels)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/repos/{repo}/issues",
                headers=self._get_headers(),
                params=params
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to fetch issues: {error}")

                issues = await response.json()
                # Filter out pull requests
                return [i for i in issues if "pull_request" not in i]

    async def _fetch_single_issue(
        self,
        repo: str,
        issue_number: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single issue from GitHub."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/repos/{repo}/issues/{issue_number}",
                headers=self._get_headers()
            ) as response:
                if response.status == 404:
                    return None
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to fetch issue: {error}")

                return await response.json()

    async def _get_synced_issue(
        self,
        repo: str,
        issue_number: int
    ) -> Optional[GitHubIssueSync]:
        """Get sync record for an issue."""
        result = await self.db.execute(
            select(GitHubIssueSync).where(
                and_(
                    GitHubIssueSync.github_repo == repo,
                    GitHubIssueSync.github_issue_number == issue_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def _create_sync_record(
        self,
        repo: str,
        issue: Dict[str, Any],
        project_id: Optional[int]
    ) -> GitHubIssueSync:
        """Create a new sync record from GitHub issue."""
        labels = [l["name"] for l in issue.get("labels", [])]

        # Determine task type from labels
        task_type = None
        for label in labels:
            label_lower = label.lower()
            if label_lower in self.LABEL_TO_TYPE:
                task_type = self.LABEL_TO_TYPE[label_lower]
                break

        sync_record = GitHubIssueSync(
            id=uuid.uuid4(),
            project_id=project_id,
            github_repo=repo,
            github_issue_number=issue["number"],
            github_issue_id=issue["id"],
            title=issue["title"],
            body=issue.get("body"),
            state=issue["state"],
            labels=labels,
            assignees=[a["login"] for a in issue.get("assignees", [])],
            milestone=issue.get("milestone", {}).get("title") if issue.get("milestone") else None,
            github_url=issue["html_url"],
            local_task_type=task_type,
            sync_direction=SyncDirection.GITHUB_TO_LOCAL.value,
            sync_status=SyncStatus.SYNCED.value,
            last_synced_at=datetime.utcnow(),
            github_updated_at=datetime.fromisoformat(
                issue["updated_at"].replace("Z", "+00:00")
            )
        )

        self.db.add(sync_record)
        await self.db.commit()
        await self.db.refresh(sync_record)

        return sync_record

    async def _update_local_from_github(
        self,
        sync_record: GitHubIssueSync,
        issue: Dict[str, Any]
    ) -> None:
        """Update local sync record from GitHub issue."""
        sync_record.title = issue["title"]
        sync_record.body = issue.get("body")
        sync_record.state = issue["state"]
        sync_record.labels = [l["name"] for l in issue.get("labels", [])]
        sync_record.assignees = [a["login"] for a in issue.get("assignees", [])]
        sync_record.milestone = (
            issue.get("milestone", {}).get("title")
            if issue.get("milestone") else None
        )
        sync_record.github_updated_at = datetime.fromisoformat(
            issue["updated_at"].replace("Z", "+00:00")
        )
        sync_record.last_synced_at = datetime.utcnow()
        sync_record.sync_status = SyncStatus.SYNCED.value
        sync_record.sync_error = None

        await self.db.commit()

    async def _update_github_issue(
        self,
        repo: str,
        issue_number: int,
        sync_record: GitHubIssueSync
    ) -> None:
        """Update GitHub issue from local record."""
        update_data = {
            "title": sync_record.title,
            "body": sync_record.body or "",
            "state": sync_record.state,
            "labels": sync_record.labels or []
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.api_base}/repos/{repo}/issues/{issue_number}",
                headers=self._get_headers(),
                json=update_data
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(f"Failed to update issue: {error}")

    async def _create_github_issue(
        self,
        repo: str,
        sync_record: GitHubIssueSync
    ) -> Dict[str, Any]:
        """Create new GitHub issue from local record."""
        issue_data = {
            "title": sync_record.title,
            "body": sync_record.body or "",
            "labels": sync_record.labels or []
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/repos/{repo}/issues",
                headers=self._get_headers(),
                json=issue_data
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise RuntimeError(f"Failed to create issue: {error}")

                return await response.json()
