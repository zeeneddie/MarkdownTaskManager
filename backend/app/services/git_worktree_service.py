"""
Git Worktree Service - Week 79

Manages parallel agent workspaces using Git worktrees.
Each agent can work in an isolated branch without conflicts.
"""

import subprocess
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.ccpm import GitWorktree, WorktreeStatus, MergeStatus


class WorktreeInfo:
    """Worktree information container."""
    def __init__(
        self,
        id: UUID,
        agent_id: str,
        worktree_path: str,
        base_branch: str,
        work_branch: str,
        status: str,
        commit_count: int = 0,
        files_changed: int = 0,
        last_commit_sha: Optional[str] = None
    ):
        self.id = id
        self.agent_id = agent_id
        self.worktree_path = worktree_path
        self.base_branch = base_branch
        self.work_branch = work_branch
        self.status = status
        self.commit_count = commit_count
        self.files_changed = files_changed
        self.last_commit_sha = last_commit_sha


class MergeResult:
    """Result of a merge operation."""
    def __init__(
        self,
        success: bool,
        status: str,
        merge_commit_sha: Optional[str] = None,
        conflicts: Optional[List[str]] = None,
        message: str = ""
    ):
        self.success = success
        self.status = status
        self.merge_commit_sha = merge_commit_sha
        self.conflicts = conflicts or []
        self.message = message


class GitWorktreeService:
    """
    Manages Git worktrees for parallel agent development.

    Features:
    - Create isolated worktrees for agents
    - Automatic branch creation and management
    - Merge worktrees back to target branch
    - Conflict detection and reporting
    - Cleanup of abandoned worktrees
    """

    def __init__(self, db: AsyncSession, repo_path: Optional[str] = None):
        self.db = db
        self.repo_path = repo_path or os.getcwd()
        self.worktrees_base = os.path.join(self.repo_path, ".agent-worktrees")

    async def create_worktree(
        self,
        agent_id: str,
        base_branch: str = "main",
        project_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorktreeInfo:
        """
        Create a new worktree for an agent.

        Args:
            agent_id: Identifier for the agent (e.g., "felix", "quinn")
            base_branch: Branch to base work on (default: main)
            project_id: Optional project association
            metadata: Additional metadata for the worktree

        Returns:
            WorktreeInfo with worktree details
        """
        # Generate unique branch name
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        work_branch = f"agent/{agent_id}/{timestamp}"
        worktree_path = os.path.join(self.worktrees_base, f"{agent_id}-{timestamp}")

        # Ensure base directory exists
        os.makedirs(self.worktrees_base, exist_ok=True)

        try:
            # Fetch latest from remote
            await self._run_git_command(["fetch", "origin", base_branch])

            # Create the worktree with a new branch
            await self._run_git_command([
                "worktree", "add",
                "-b", work_branch,
                worktree_path,
                f"origin/{base_branch}"
            ])

            # Create database record
            worktree = GitWorktree(
                id=uuid.uuid4(),
                project_id=project_id,
                agent_id=agent_id,
                worktree_path=worktree_path,
                base_branch=base_branch,
                work_branch=work_branch,
                status=WorktreeStatus.ACTIVE.value,
                commit_count=0,
                files_changed=0,
                worktree_metadata=metadata or {}
            )

            self.db.add(worktree)
            await self.db.commit()
            await self.db.refresh(worktree)

            return WorktreeInfo(
                id=worktree.id,
                agent_id=worktree.agent_id,
                worktree_path=worktree.worktree_path,
                base_branch=worktree.base_branch,
                work_branch=worktree.work_branch,
                status=worktree.status,
                commit_count=worktree.commit_count,
                files_changed=worktree.files_changed
            )

        except Exception as e:
            # Cleanup on failure
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise RuntimeError(f"Failed to create worktree: {e}")

    async def get_worktree(self, worktree_id: UUID) -> Optional[GitWorktree]:
        """Get worktree by ID."""
        result = await self.db.execute(
            select(GitWorktree).where(GitWorktree.id == worktree_id)
        )
        return result.scalar_one_or_none()

    async def get_agent_worktree(self, agent_id: str) -> Optional[GitWorktree]:
        """Get active worktree for an agent."""
        result = await self.db.execute(
            select(GitWorktree)
            .where(GitWorktree.agent_id == agent_id)
            .where(GitWorktree.status == WorktreeStatus.ACTIVE.value)
            .order_by(GitWorktree.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def list_active_worktrees(
        self,
        project_id: Optional[int] = None
    ) -> List[GitWorktree]:
        """List all active worktrees."""
        query = select(GitWorktree).where(
            GitWorktree.status == WorktreeStatus.ACTIVE.value
        )

        if project_id:
            query = query.where(GitWorktree.project_id == project_id)

        query = query.order_by(GitWorktree.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def commit_changes(
        self,
        worktree_id: UUID,
        message: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Commit changes in a worktree.

        Args:
            worktree_id: Worktree identifier
            message: Commit message
            files: Specific files to commit (None = all changes)

        Returns:
            Commit info including SHA
        """
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            raise ValueError(f"Worktree {worktree_id} not found")

        if worktree.status != WorktreeStatus.ACTIVE.value:
            raise ValueError(f"Worktree is not active: {worktree.status}")

        cwd = worktree.worktree_path

        # Stage files
        if files:
            for file in files:
                await self._run_git_command(["add", file], cwd=cwd)
        else:
            await self._run_git_command(["add", "-A"], cwd=cwd)

        # Check if there are changes to commit
        status = await self._run_git_command(["status", "--porcelain"], cwd=cwd)
        if not status.strip():
            return {"committed": False, "message": "No changes to commit"}

        # Commit
        await self._run_git_command(["commit", "-m", message], cwd=cwd)

        # Get commit info
        sha = await self._run_git_command(
            ["rev-parse", "HEAD"], cwd=cwd
        )
        sha = sha.strip()

        # Count changed files
        diff_stat = await self._run_git_command(
            ["diff", "--stat", "HEAD~1", "HEAD"], cwd=cwd
        )
        files_changed = len([l for l in diff_stat.split('\n') if '|' in l])

        # Update database
        worktree.last_commit_sha = sha
        worktree.last_commit_message = message[:500]
        worktree.commit_count = (worktree.commit_count or 0) + 1
        worktree.files_changed = (worktree.files_changed or 0) + files_changed

        await self.db.commit()

        return {
            "committed": True,
            "sha": sha,
            "message": message,
            "files_changed": files_changed
        }

    async def merge_worktree(
        self,
        worktree_id: UUID,
        target_branch: str = "main",
        delete_after: bool = True
    ) -> MergeResult:
        """
        Merge worktree branch back to target branch.

        Args:
            worktree_id: Worktree identifier
            target_branch: Branch to merge into
            delete_after: Delete worktree after successful merge

        Returns:
            MergeResult with status
        """
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            raise ValueError(f"Worktree {worktree_id} not found")

        worktree.merge_target = target_branch
        worktree.merge_status = MergeStatus.PENDING.value
        await self.db.commit()

        try:
            # Switch to target branch in main repo
            await self._run_git_command(["checkout", target_branch])
            await self._run_git_command(["pull", "origin", target_branch])

            # Merge the work branch
            merge_output = await self._run_git_command(
                ["merge", worktree.work_branch, "--no-ff", "-m",
                 f"Merge {worktree.work_branch} into {target_branch}"],
                check=False
            )

            # Check for conflicts
            if "CONFLICT" in merge_output:
                # Abort the merge
                await self._run_git_command(["merge", "--abort"], check=False)

                worktree.status = WorktreeStatus.CONFLICT.value
                worktree.merge_status = MergeStatus.CONFLICT.value
                await self.db.commit()

                # Extract conflict files
                conflicts = [
                    line.split(":")[-1].strip()
                    for line in merge_output.split('\n')
                    if "CONFLICT" in line
                ]

                return MergeResult(
                    success=False,
                    status="conflict",
                    conflicts=conflicts,
                    message="Merge conflicts detected"
                )

            # Get merge commit SHA
            merge_sha = await self._run_git_command(["rev-parse", "HEAD"])
            merge_sha = merge_sha.strip()

            # Push to remote
            await self._run_git_command(["push", "origin", target_branch])

            # Update status
            worktree.status = WorktreeStatus.MERGED.value
            worktree.merge_status = MergeStatus.MERGED.value
            worktree.merged_at = datetime.utcnow()
            await self.db.commit()

            # Cleanup if requested
            if delete_after:
                await self.cleanup_worktree(worktree_id)

            return MergeResult(
                success=True,
                status="merged",
                merge_commit_sha=merge_sha,
                message=f"Successfully merged to {target_branch}"
            )

        except Exception as e:
            worktree.merge_status = MergeStatus.REJECTED.value
            await self.db.commit()

            return MergeResult(
                success=False,
                status="error",
                message=str(e)
            )

    async def cleanup_worktree(self, worktree_id: UUID) -> bool:
        """
        Remove a worktree and its branch.

        Args:
            worktree_id: Worktree identifier

        Returns:
            True if cleanup successful
        """
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            return False

        try:
            # Remove git worktree
            await self._run_git_command(
                ["worktree", "remove", worktree.worktree_path, "--force"],
                check=False
            )

            # Remove the branch if not merged
            if worktree.status != WorktreeStatus.MERGED.value:
                await self._run_git_command(
                    ["branch", "-D", worktree.work_branch],
                    check=False
                )

            # Remove directory if it still exists
            if os.path.exists(worktree.worktree_path):
                shutil.rmtree(worktree.worktree_path, ignore_errors=True)

            # Mark as abandoned if not merged
            if worktree.status != WorktreeStatus.MERGED.value:
                worktree.status = WorktreeStatus.ABANDONED.value

            await self.db.commit()
            return True

        except Exception as e:
            print(f"Cleanup error: {e}")
            return False

    async def get_worktree_status(self, worktree_id: UUID) -> Dict[str, Any]:
        """
        Get detailed status of a worktree.

        Returns:
            Dictionary with status info, uncommitted changes, etc.
        """
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            raise ValueError(f"Worktree {worktree_id} not found")

        cwd = worktree.worktree_path

        # Get git status
        status_output = await self._run_git_command(
            ["status", "--porcelain"], cwd=cwd, check=False
        )

        # Parse status
        modified = []
        added = []
        deleted = []

        for line in status_output.strip().split('\n'):
            if not line:
                continue
            status_code = line[:2]
            filename = line[3:]

            if 'M' in status_code:
                modified.append(filename)
            elif 'A' in status_code or '?' in status_code:
                added.append(filename)
            elif 'D' in status_code:
                deleted.append(filename)

        # Get commit log
        log_output = await self._run_git_command(
            ["log", "--oneline", "-10"], cwd=cwd, check=False
        )

        commits = [
            {"sha": line.split()[0], "message": " ".join(line.split()[1:])}
            for line in log_output.strip().split('\n')
            if line
        ]

        return {
            "id": str(worktree.id),
            "agent_id": worktree.agent_id,
            "work_branch": worktree.work_branch,
            "status": worktree.status,
            "uncommitted_changes": {
                "modified": modified,
                "added": added,
                "deleted": deleted,
                "total": len(modified) + len(added) + len(deleted)
            },
            "recent_commits": commits,
            "commit_count": worktree.commit_count,
            "files_changed": worktree.files_changed
        }

    async def sync_with_base(self, worktree_id: UUID) -> Dict[str, Any]:
        """
        Sync worktree with latest changes from base branch.

        Returns:
            Sync result with potential conflicts
        """
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            raise ValueError(f"Worktree {worktree_id} not found")

        cwd = worktree.worktree_path

        # Fetch latest
        await self._run_git_command(["fetch", "origin"], cwd=cwd)

        # Try to rebase onto base branch
        try:
            rebase_output = await self._run_git_command(
                ["rebase", f"origin/{worktree.base_branch}"],
                cwd=cwd,
                check=False
            )

            if "CONFLICT" in rebase_output:
                # Abort rebase
                await self._run_git_command(["rebase", "--abort"], cwd=cwd)
                return {
                    "success": False,
                    "conflicts": True,
                    "message": "Conflicts detected during rebase"
                }

            return {
                "success": True,
                "conflicts": False,
                "message": f"Synced with {worktree.base_branch}"
            }

        except Exception as e:
            return {
                "success": False,
                "conflicts": False,
                "message": str(e)
            }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get worktree usage statistics."""
        # Count by status
        result = await self.db.execute(
            select(GitWorktree.status, GitWorktree.id)
        )
        worktrees = result.all()

        status_counts = {}
        for status, _ in worktrees:
            status_counts[status] = status_counts.get(status, 0) + 1

        # Agent activity
        result = await self.db.execute(
            select(GitWorktree.agent_id, GitWorktree.id)
            .where(GitWorktree.status == WorktreeStatus.ACTIVE.value)
        )
        agent_worktrees = result.all()

        active_agents = list(set(agent for agent, _ in agent_worktrees))

        return {
            "total_worktrees": len(worktrees),
            "status_counts": status_counts,
            "active_agents": active_agents,
            "active_count": status_counts.get(WorktreeStatus.ACTIVE.value, 0),
            "merged_count": status_counts.get(WorktreeStatus.MERGED.value, 0),
            "conflict_count": status_counts.get(WorktreeStatus.CONFLICT.value, 0)
        }

    async def _run_git_command(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        check: bool = True
    ) -> str:
        """Run a git command asynchronously."""
        cwd = cwd or self.repo_path

        process = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        stdout, _ = await process.communicate()
        output = stdout.decode('utf-8')

        if check and process.returncode != 0:
            raise RuntimeError(f"Git command failed: git {' '.join(args)}\n{output}")

        return output
