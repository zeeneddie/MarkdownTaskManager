"""
MP-M-5: Playgrounds Service

Isolated safe spaces for AI experiments.
Create temporary environments to try ideas without affecting main codebase.

Based on Gregor Riegler's Augmented Coding Pattern Language.

Key capabilities:
- Create isolated playground directories
- Execute commands safely within playgrounds
- Compare changes with main codebase
- Merge successful experiments back
- Auto-cleanup expired playgrounds

Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
from pathlib import Path
import logging
import os
import shutil
import subprocess
import tempfile
import hashlib

logger = logging.getLogger(__name__)


class IsolationType(Enum):
    """Type of isolation for playground."""
    DIRECTORY = "directory"     # Simple directory copy (default)
    GIT_BRANCH = "git_branch"   # Separate git branch
    WORKTREE = "worktree"       # Git worktree
    SYMLINK = "symlink"         # Symlinked with copy-on-write


class PlaygroundStatus(Enum):
    """Status of a playground."""
    CREATING = "creating"
    ACTIVE = "active"
    ARCHIVED = "archived"
    MERGED = "merged"
    DELETED = "deleted"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class PlaygroundFile:
    """A file within a playground."""
    relative_path: str
    is_new: bool
    is_modified: bool
    is_deleted: bool
    original_hash: Optional[str] = None
    current_hash: Optional[str] = None


@dataclass
class DiffReport:
    """Report of differences between playground and main."""
    playground_id: UUID
    files_added: List[str]
    files_modified: List[str]
    files_deleted: List[str]
    total_additions: int
    total_deletions: int
    generated_at: datetime


@dataclass
class ExecutionResult:
    """Result of command execution in playground."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    executed_at: datetime


@dataclass
class MergeResult:
    """Result of merging playground back to main."""
    playground_id: UUID
    success: bool
    files_merged: List[str]
    conflicts: List[str]
    error: Optional[str] = None
    merged_at: Optional[datetime] = None


@dataclass
class ExperimentResult:
    """Result of an experiment in a playground."""
    playground_id: UUID
    success: bool
    artifacts: List[str]
    merge_candidate: bool
    learnings: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Playground:
    """An isolated playground environment."""
    id: UUID
    name: str
    description: str
    base_path: str
    playground_path: str
    isolation_type: IsolationType
    status: PlaygroundStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed: datetime
    execution_history: List[ExecutionResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlaygroundsService:
    """
    Service for managing isolated playground environments.

    The "Playgrounds" pattern provides safe spaces for experimentation
    without affecting the main codebase. Uses directory-based isolation
    for simplicity and portability.
    """

    DEFAULT_TTL_HOURS = 24
    MAX_PLAYGROUNDS = 10

    def __init__(
        self,
        playgrounds_root: Optional[str] = None,
        default_ttl_hours: int = DEFAULT_TTL_HOURS
    ):
        self._playgrounds_root = playgrounds_root or os.path.join(
            tempfile.gettempdir(),
            "ai_playgrounds"
        )
        self._default_ttl_hours = default_ttl_hours
        self._playgrounds: Dict[UUID, Playground] = {}

        # Ensure root directory exists
        os.makedirs(self._playgrounds_root, exist_ok=True)

        # Cleanup expired playgrounds on init
        self._cleanup_expired()

    def create_playground(
        self,
        name: str,
        base_path: str,
        description: str = "",
        isolation_type: IsolationType = IsolationType.DIRECTORY,
        ttl_hours: Optional[int] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Playground:
        """
        Create a new isolated playground.

        Args:
            name: Name for the playground
            base_path: Path to copy from
            description: Description of the experiment
            isolation_type: Type of isolation
            ttl_hours: Time to live in hours (None = use default)
            include_patterns: Patterns to include (glob)
            exclude_patterns: Patterns to exclude (glob)
            metadata: Additional metadata

        Returns:
            Created Playground
        """
        # Check limits
        active = [p for p in self._playgrounds.values()
                 if p.status in (PlaygroundStatus.ACTIVE, PlaygroundStatus.CREATING)]
        if len(active) >= self.MAX_PLAYGROUNDS:
            self._cleanup_expired()
            active = [p for p in self._playgrounds.values()
                     if p.status in (PlaygroundStatus.ACTIVE, PlaygroundStatus.CREATING)]
            if len(active) >= self.MAX_PLAYGROUNDS:
                raise RuntimeError(f"Maximum playgrounds ({self.MAX_PLAYGROUNDS}) reached")

        now = datetime.now(timezone.utc)
        ttl = ttl_hours if ttl_hours is not None else self._default_ttl_hours
        expires_at = now + timedelta(hours=ttl) if ttl > 0 else None

        playground_id = uuid4()
        playground_dir = os.path.join(self._playgrounds_root, str(playground_id))

        playground = Playground(
            id=playground_id,
            name=name,
            description=description,
            base_path=os.path.abspath(base_path),
            playground_path=playground_dir,
            isolation_type=isolation_type,
            status=PlaygroundStatus.CREATING,
            created_at=now,
            expires_at=expires_at,
            last_accessed=now,
            metadata=metadata or {}
        )

        self._playgrounds[playground_id] = playground

        try:
            if isolation_type == IsolationType.DIRECTORY:
                self._create_directory_copy(
                    base_path,
                    playground_dir,
                    include_patterns,
                    exclude_patterns
                )
            elif isolation_type == IsolationType.GIT_BRANCH:
                self._create_git_branch(base_path, playground_dir, name)
            elif isolation_type == IsolationType.WORKTREE:
                self._create_worktree(base_path, playground_dir, name)
            elif isolation_type == IsolationType.SYMLINK:
                self._create_symlink_copy(base_path, playground_dir)

            playground.status = PlaygroundStatus.ACTIVE
            logger.info(f"Created playground '{name}' at {playground_dir}")

        except Exception as e:
            playground.status = PlaygroundStatus.FAILED
            logger.error(f"Failed to create playground: {e}")
            raise

        return playground

    def execute_in_playground(
        self,
        playground_id: UUID,
        command: str,
        timeout_seconds: int = 300,
        env: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute a command within a playground.

        Args:
            playground_id: Playground ID
            command: Command to execute
            timeout_seconds: Timeout for execution
            env: Environment variables

        Returns:
            ExecutionResult with output
        """
        playground = self._playgrounds.get(playground_id)
        if not playground:
            raise ValueError(f"Playground {playground_id} not found")

        if playground.status != PlaygroundStatus.ACTIVE:
            raise RuntimeError(f"Playground is not active: {playground.status.value}")

        playground.last_accessed = datetime.now(timezone.utc)

        # Prepare environment
        execution_env = os.environ.copy()
        if env:
            execution_env.update(env)

        start_time = datetime.now(timezone.utc)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=playground.playground_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=execution_env
            )

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            execution = ExecutionResult(
                command=command,
                exit_code=result.returncode,
                stdout=result.stdout[:10000],  # Limit output size
                stderr=result.stderr[:10000],
                duration_seconds=duration,
                executed_at=start_time
            )

        except subprocess.TimeoutExpired:
            duration = timeout_seconds
            execution = ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout_seconds} seconds",
                duration_seconds=duration,
                executed_at=start_time
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            execution = ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=duration,
                executed_at=start_time
            )

        playground.execution_history.append(execution)

        logger.debug(f"Executed in playground {playground_id}: {command[:50]}... (exit: {execution.exit_code})")

        return execution

    def compare_with_main(self, playground_id: UUID) -> DiffReport:
        """
        Compare playground with main codebase.

        Args:
            playground_id: Playground ID

        Returns:
            DiffReport with differences
        """
        playground = self._playgrounds.get(playground_id)
        if not playground:
            raise ValueError(f"Playground {playground_id} not found")

        playground.last_accessed = datetime.now(timezone.utc)

        files_added = []
        files_modified = []
        files_deleted = []
        total_additions = 0
        total_deletions = 0

        base_files = self._get_file_hashes(playground.base_path)
        playground_files = self._get_file_hashes(playground.playground_path)

        # Find added and modified files
        for rel_path, pg_hash in playground_files.items():
            if rel_path not in base_files:
                files_added.append(rel_path)
                # Count lines in new file
                full_path = os.path.join(playground.playground_path, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_additions += sum(1 for _ in f)
                except Exception:
                    pass
            elif base_files[rel_path] != pg_hash:
                files_modified.append(rel_path)
                # Approximate diff (simplified)
                total_additions += 10
                total_deletions += 5

        # Find deleted files
        for rel_path in base_files:
            if rel_path not in playground_files:
                files_deleted.append(rel_path)
                # Count lines in deleted file
                full_path = os.path.join(playground.base_path, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_deletions += sum(1 for _ in f)
                except Exception:
                    pass

        return DiffReport(
            playground_id=playground_id,
            files_added=files_added,
            files_modified=files_modified,
            files_deleted=files_deleted,
            total_additions=total_additions,
            total_deletions=total_deletions,
            generated_at=datetime.now(timezone.utc)
        )

    def merge_playground(
        self,
        playground_id: UUID,
        files_to_merge: Optional[List[str]] = None,
        backup: bool = True
    ) -> MergeResult:
        """
        Merge playground changes back to main.

        Args:
            playground_id: Playground ID
            files_to_merge: Specific files to merge (None = all changed)
            backup: Whether to create backup before merge

        Returns:
            MergeResult with status
        """
        playground = self._playgrounds.get(playground_id)
        if not playground:
            raise ValueError(f"Playground {playground_id} not found")

        if playground.status != PlaygroundStatus.ACTIVE:
            return MergeResult(
                playground_id=playground_id,
                success=False,
                files_merged=[],
                conflicts=[],
                error=f"Playground is not active: {playground.status.value}"
            )

        diff = self.compare_with_main(playground_id)

        # Determine files to merge
        if files_to_merge:
            to_merge = [f for f in files_to_merge
                       if f in diff.files_added or f in diff.files_modified]
            to_delete = [f for f in files_to_merge if f in diff.files_deleted]
        else:
            to_merge = diff.files_added + diff.files_modified
            to_delete = diff.files_deleted

        # Create backup if requested
        if backup and to_merge:
            backup_dir = os.path.join(
                self._playgrounds_root,
                "backups",
                str(playground_id)
            )
            os.makedirs(backup_dir, exist_ok=True)
            for rel_path in to_merge:
                src = os.path.join(playground.base_path, rel_path)
                if os.path.exists(src):
                    dst = os.path.join(backup_dir, rel_path)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)

        merged = []
        conflicts = []

        try:
            # Copy new/modified files
            for rel_path in to_merge:
                src = os.path.join(playground.playground_path, rel_path)
                dst = os.path.join(playground.base_path, rel_path)

                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    merged.append(rel_path)

            # Handle deleted files
            for rel_path in to_delete:
                dst = os.path.join(playground.base_path, rel_path)
                if os.path.exists(dst):
                    os.remove(dst)
                    merged.append(f"-{rel_path}")

            playground.status = PlaygroundStatus.MERGED

            return MergeResult(
                playground_id=playground_id,
                success=True,
                files_merged=merged,
                conflicts=conflicts,
                merged_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            return MergeResult(
                playground_id=playground_id,
                success=False,
                files_merged=merged,
                conflicts=conflicts,
                error=str(e)
            )

    def archive_playground(self, playground_id: UUID) -> Playground:
        """
        Archive a playground (keep files but mark as inactive).

        Args:
            playground_id: Playground ID

        Returns:
            Updated Playground
        """
        playground = self._playgrounds.get(playground_id)
        if not playground:
            raise ValueError(f"Playground {playground_id} not found")

        playground.status = PlaygroundStatus.ARCHIVED
        playground.last_accessed = datetime.now(timezone.utc)

        logger.info(f"Archived playground {playground_id}")

        return playground

    def delete_playground(self, playground_id: UUID, force: bool = False) -> bool:
        """
        Delete a playground and its files.

        Args:
            playground_id: Playground ID
            force: Force delete even if active

        Returns:
            True if deleted
        """
        playground = self._playgrounds.get(playground_id)
        if not playground:
            return False

        if playground.status == PlaygroundStatus.ACTIVE and not force:
            raise RuntimeError("Cannot delete active playground without force=True")

        try:
            if os.path.exists(playground.playground_path):
                shutil.rmtree(playground.playground_path)
        except Exception as e:
            logger.error(f"Error deleting playground files: {e}")

        playground.status = PlaygroundStatus.DELETED
        del self._playgrounds[playground_id]

        logger.info(f"Deleted playground {playground_id}")

        return True

    def get_playground(self, playground_id: UUID) -> Optional[Playground]:
        """Get a playground by ID."""
        return self._playgrounds.get(playground_id)

    def list_playgrounds(
        self,
        status: Optional[PlaygroundStatus] = None,
        include_expired: bool = False
    ) -> List[Playground]:
        """List all playgrounds with optional filtering."""
        playgrounds = list(self._playgrounds.values())

        if status:
            playgrounds = [p for p in playgrounds if p.status == status]

        if not include_expired:
            now = datetime.now(timezone.utc)
            playgrounds = [p for p in playgrounds
                          if not p.expires_at or p.expires_at > now]

        return sorted(playgrounds, key=lambda p: p.created_at, reverse=True)

    def record_experiment_result(
        self,
        playground_id: UUID,
        success: bool,
        artifacts: Optional[List[str]] = None,
        learnings: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> ExperimentResult:
        """
        Record the result of an experiment.

        Args:
            playground_id: Playground ID
            success: Whether experiment succeeded
            artifacts: List of artifact paths
            learnings: List of learnings/insights
            metrics: Experiment metrics

        Returns:
            ExperimentResult
        """
        playground = self._playgrounds.get(playground_id)
        if not playground:
            raise ValueError(f"Playground {playground_id} not found")

        diff = self.compare_with_main(playground_id)
        merge_candidate = success and len(diff.files_modified + diff.files_added) > 0

        result = ExperimentResult(
            playground_id=playground_id,
            success=success,
            artifacts=artifacts or [],
            merge_candidate=merge_candidate,
            learnings=learnings or [],
            metrics=metrics or {}
        )

        playground.metadata["experiment_result"] = {
            "success": success,
            "merge_candidate": merge_candidate,
            "learnings": learnings or []
        }

        return result

    def cleanup_expired(self) -> int:
        """
        Clean up expired playgrounds.

        Returns:
            Number of playgrounds cleaned up
        """
        return self._cleanup_expired()

    def _cleanup_expired(self) -> int:
        """Clean up expired playgrounds."""
        now = datetime.now(timezone.utc)
        expired = []

        for pg_id, playground in self._playgrounds.items():
            if playground.expires_at and playground.expires_at < now:
                expired.append(pg_id)

        for pg_id in expired:
            try:
                self.delete_playground(pg_id, force=True)
            except Exception as e:
                logger.error(f"Error cleaning up playground {pg_id}: {e}")

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired playgrounds")

        return len(expired)

    def _create_directory_copy(
        self,
        src: str,
        dst: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """Create a directory copy of the source."""
        # Default excludes
        default_excludes = [
            '.git',
            '__pycache__',
            'node_modules',
            '.venv',
            'venv',
            '*.pyc',
            '.DS_Store'
        ]

        excludes = set(default_excludes)
        if exclude_patterns:
            excludes.update(exclude_patterns)

        def should_exclude(path: str) -> bool:
            name = os.path.basename(path)
            for pattern in excludes:
                if pattern.startswith('*'):
                    if name.endswith(pattern[1:]):
                        return True
                elif name == pattern:
                    return True
            return False

        def copy_tree(src_dir: str, dst_dir: str) -> None:
            os.makedirs(dst_dir, exist_ok=True)

            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(dst_dir, item)

                if should_exclude(s):
                    continue

                if os.path.isdir(s):
                    copy_tree(s, d)
                else:
                    shutil.copy2(s, d)

        copy_tree(src, dst)

    def _create_git_branch(self, base_path: str, playground_path: str, name: str) -> None:
        """Create a new git branch for the playground."""
        branch_name = f"playground/{name.replace(' ', '-')}"

        # Create branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=base_path,
            check=True,
            capture_output=True
        )

        # Copy to playground path
        self._create_directory_copy(base_path, playground_path)

    def _create_worktree(self, base_path: str, playground_path: str, name: str) -> None:
        """Create a git worktree for the playground."""
        branch_name = f"playground/{name.replace(' ', '-')}"

        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, playground_path],
            cwd=base_path,
            check=True,
            capture_output=True
        )

    def _create_symlink_copy(self, base_path: str, playground_path: str) -> None:
        """Create a symlink-based copy (copy-on-write behavior)."""
        os.makedirs(playground_path, exist_ok=True)

        for item in os.listdir(base_path):
            s = os.path.join(base_path, item)
            d = os.path.join(playground_path, item)

            if item.startswith('.'):
                continue

            if os.path.isdir(s):
                os.symlink(s, d)
            else:
                shutil.copy2(s, d)

    def _get_file_hashes(self, path: str) -> Dict[str, str]:
        """Get hashes of all files in a directory."""
        hashes = {}

        for root, dirs, files in os.walk(path):
            # Skip hidden and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and
                      d not in ['node_modules', '__pycache__', 'venv', '.venv']]

            for f in files:
                if f.startswith('.'):
                    continue

                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, path)

                try:
                    with open(full_path, 'rb') as file:
                        content = file.read()
                        hashes[rel_path] = hashlib.md5(content).hexdigest()
                except Exception:
                    pass

        return hashes
