"""
CCPM Workflow Integration Service - Week 89

Integrates Git Worktrees with AI Agent Workflows for parallel development.
Each workflow type has specific worktree strategies for optimal agent collaboration.

Supported Workflows:
1. GREEN_PAPER - Greenfield project worktrees (analysis, design, implementation phases)
2. BROWN_PAPER - Legacy analysis worktrees (assessment, planning, migration)
3. MIGRATION - Component-based worktrees (per migration target)
4. NEW_FEATURE - Feature branch worktrees (per feature/story)
5. BUG - Hotfix branch worktrees (per bug fix)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.services.git_worktree_service import GitWorktreeService, WorktreeInfo, MergeResult
from app.models.ccpm import GitWorktree, WorktreeStatus


# Workflow-specific worktree configurations
# Week 94-95: Added Vicky (Visual Designer) to design-first workflows
WORKFLOW_WORKTREE_CONFIGS = {
    "GREEN_PAPER": {
        "phases": ["analysis", "design", "architecture", "implementation"],
        "agents": ["peter", "vicky", "felix", "tessa", "diana"],  # Vicky added after Peter
        "base_branch": "main",
        "merge_strategy": "sequential",  # Merge in order
        "auto_cleanup": True
    },
    "BROWN_PAPER": {
        "phases": ["assessment", "design", "current_state", "migration_plan"],
        "agents": ["miguel", "peter", "vicky", "felix", "tessa", "diana"],  # Vicky added after Peter
        "base_branch": "main",
        "merge_strategy": "sequential",
        "auto_cleanup": True
    },
    "MIGRATION": {
        "phases": ["analysis", "conversion", "validation"],
        "agents": ["miguel", "felix", "tessa"],
        "base_branch": "main",
        "merge_strategy": "parallel",  # Merge when ready
        "auto_cleanup": True
    },
    "NEW_FEATURE": {
        "phases": ["design", "development"],
        "agents": ["peter", "vicky", "felix", "tessa", "diana"],  # Vicky added after Peter
        "base_branch": "develop",
        "merge_strategy": "pr_required",  # Via pull request
        "auto_cleanup": False
    },
    "ENHANCEMENT": {
        "phases": ["design", "development"],
        "agents": ["felix", "vicky", "tessa", "diana"],  # Vicky added after Felix
        "base_branch": "develop",
        "merge_strategy": "pr_required",
        "auto_cleanup": False
    },
    "BUG": {
        "phases": ["hotfix"],
        "agents": ["betty", "tessa"],
        "base_branch": "main",
        "merge_strategy": "immediate",  # Direct merge
        "auto_cleanup": True
    }
}


class WorkflowWorktreeSession:
    """Represents an active worktree session for a workflow."""

    def __init__(
        self,
        id: UUID,
        workflow_type: str,
        project_id: int,
        worktrees: List[WorktreeInfo],
        status: str,
        created_at: datetime,
        metadata: Dict[str, Any]
    ):
        self.id = id
        self.workflow_type = workflow_type
        self.project_id = project_id
        self.worktrees = worktrees
        self.status = status
        self.created_at = created_at
        self.metadata = metadata


class CCPMWorkflowIntegrationService:
    """
    Integrates CCPM worktrees with AI agent workflows.

    Features:
    - Automatic worktree creation for workflow phases
    - Agent-specific workspace isolation
    - Parallel development support
    - Automatic merge and cleanup
    - Workflow-aware branch naming
    """

    def __init__(self, db: AsyncSession, repo_path: Optional[str] = None):
        self.db = db
        self.worktree_service = GitWorktreeService(db, repo_path)

    async def start_workflow_session(
        self,
        workflow_type: str,
        project_id: int,
        context: Dict[str, Any] = None
    ) -> WorkflowWorktreeSession:
        """
        Start a new worktree session for a workflow.

        Creates isolated worktrees for each phase/agent based on workflow type.

        Args:
            workflow_type: Type of workflow (GREEN_PAPER, BROWN_PAPER, etc.)
            project_id: Project identifier
            context: Additional workflow context

        Returns:
            WorkflowWorktreeSession with created worktrees
        """
        if workflow_type not in WORKFLOW_WORKTREE_CONFIGS:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        config = WORKFLOW_WORKTREE_CONFIGS[workflow_type]
        worktrees = []

        # Create worktree for each phase-agent combination
        for i, phase in enumerate(config["phases"]):
            agent = config["agents"][i] if i < len(config["agents"]) else config["agents"][0]

            try:
                worktree = await self.worktree_service.create_worktree(
                    agent_id=agent,
                    base_branch=config["base_branch"],
                    project_id=project_id,
                    metadata={
                        "workflow_type": workflow_type,
                        "phase": phase,
                        "context": context or {}
                    }
                )
                worktrees.append(worktree)
            except Exception as e:
                # Cleanup any created worktrees on failure
                for wt in worktrees:
                    await self.worktree_service.cleanup_worktree(wt.id)
                raise RuntimeError(f"Failed to create worktree for phase {phase}: {e}")

        return WorkflowWorktreeSession(
            id=worktrees[0].id if worktrees else None,
            workflow_type=workflow_type,
            project_id=project_id,
            worktrees=worktrees,
            status="active",
            created_at=datetime.now(timezone.utc),
            metadata={
                "config": config,
                "context": context or {}
            }
        )

    async def get_workflow_worktree(
        self,
        workflow_type: str,
        project_id: int,
        agent_id: str
    ) -> Optional[WorktreeInfo]:
        """
        Get the active worktree for a specific workflow, project, and agent.

        Args:
            workflow_type: Type of workflow
            project_id: Project identifier
            agent_id: Agent identifier

        Returns:
            WorktreeInfo or None if not found
        """
        # Find worktree matching criteria
        result = await self.db.execute(
            select(GitWorktree).where(
                and_(
                    GitWorktree.project_id == project_id,
                    GitWorktree.agent_id == agent_id,
                    GitWorktree.status == WorktreeStatus.ACTIVE.value
                )
            ).order_by(GitWorktree.created_at.desc())
        )

        worktree = result.scalar_one_or_none()

        if worktree:
            # Verify workflow type matches
            metadata = worktree.worktree_metadata or {}
            if metadata.get("workflow_type") == workflow_type:
                return WorktreeInfo(
                    id=worktree.id,
                    agent_id=worktree.agent_id,
                    worktree_path=worktree.worktree_path,
                    base_branch=worktree.base_branch,
                    work_branch=worktree.work_branch,
                    status=worktree.status,
                    commit_count=worktree.commit_count,
                    files_changed=worktree.files_changed,
                    last_commit_sha=worktree.last_commit_sha
                )

        return None

    async def list_workflow_worktrees(
        self,
        workflow_type: str,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        List all worktrees for a workflow session.

        Args:
            workflow_type: Type of workflow
            project_id: Project identifier

        Returns:
            List of worktree info dicts
        """
        result = await self.db.execute(
            select(GitWorktree).where(
                and_(
                    GitWorktree.project_id == project_id,
                    GitWorktree.status.in_([
                        WorktreeStatus.ACTIVE.value,
                        WorktreeStatus.MERGED.value
                    ])
                )
            ).order_by(GitWorktree.created_at.desc())
        )

        worktrees = result.scalars().all()

        # Filter by workflow type
        workflow_worktrees = []
        for wt in worktrees:
            metadata = wt.worktree_metadata or {}
            if metadata.get("workflow_type") == workflow_type:
                workflow_worktrees.append({
                    "id": str(wt.id),
                    "agent_id": wt.agent_id,
                    "phase": metadata.get("phase"),
                    "worktree_path": wt.worktree_path,
                    "work_branch": wt.work_branch,
                    "status": wt.status,
                    "commit_count": wt.commit_count,
                    "files_changed": wt.files_changed,
                    "last_commit_sha": wt.last_commit_sha
                })

        return workflow_worktrees

    async def complete_phase(
        self,
        worktree_id: UUID,
        message: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Complete a workflow phase by committing changes.

        Args:
            worktree_id: Worktree identifier
            message: Commit message
            files: Specific files to commit

        Returns:
            Commit result
        """
        # Commit changes
        result = await self.worktree_service.commit_changes(
            worktree_id=worktree_id,
            message=message,
            files=files
        )

        # Get worktree for metadata
        worktree = await self.worktree_service.get_worktree(worktree_id)
        if worktree and worktree.worktree_metadata:
            result["phase"] = worktree.worktree_metadata.get("phase")
            result["workflow_type"] = worktree.worktree_metadata.get("workflow_type")

        return result

    async def merge_workflow_session(
        self,
        workflow_type: str,
        project_id: int,
        target_branch: str = None
    ) -> Dict[str, Any]:
        """
        Merge all workflow worktrees back to target branch.

        Uses workflow-specific merge strategy:
        - sequential: Merge in phase order
        - parallel: Merge independently when ready
        - pr_required: Create PR for each
        - immediate: Direct merge

        Args:
            workflow_type: Type of workflow
            project_id: Project identifier
            target_branch: Override target branch

        Returns:
            Merge results for all worktrees
        """
        if workflow_type not in WORKFLOW_WORKTREE_CONFIGS:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        config = WORKFLOW_WORKTREE_CONFIGS[workflow_type]
        target = target_branch or config["base_branch"]
        strategy = config["merge_strategy"]

        # Get all active worktrees for this workflow
        worktrees = await self.list_workflow_worktrees(workflow_type, project_id)
        active_worktrees = [wt for wt in worktrees if wt["status"] == "active"]

        results = {
            "workflow_type": workflow_type,
            "strategy": strategy,
            "target_branch": target,
            "worktrees": [],
            "success": True
        }

        if strategy == "sequential":
            # Merge in order
            for wt in active_worktrees:
                merge_result = await self.worktree_service.merge_worktree(
                    worktree_id=UUID(wt["id"]),
                    target_branch=target,
                    delete_after=config["auto_cleanup"]
                )
                results["worktrees"].append({
                    "id": wt["id"],
                    "phase": wt.get("phase"),
                    "success": merge_result.success,
                    "status": merge_result.status,
                    "conflicts": merge_result.conflicts
                })
                if not merge_result.success:
                    results["success"] = False
                    break  # Stop on conflict for sequential

        elif strategy == "parallel":
            # Merge all independently
            merge_tasks = []
            for wt in active_worktrees:
                merge_tasks.append(
                    self.worktree_service.merge_worktree(
                        worktree_id=UUID(wt["id"]),
                        target_branch=target,
                        delete_after=config["auto_cleanup"]
                    )
                )

            merge_results = await asyncio.gather(*merge_tasks, return_exceptions=True)

            for i, merge_result in enumerate(merge_results):
                wt = active_worktrees[i]
                if isinstance(merge_result, Exception):
                    results["worktrees"].append({
                        "id": wt["id"],
                        "phase": wt.get("phase"),
                        "success": False,
                        "status": "error",
                        "error": str(merge_result)
                    })
                    results["success"] = False
                else:
                    results["worktrees"].append({
                        "id": wt["id"],
                        "phase": wt.get("phase"),
                        "success": merge_result.success,
                        "status": merge_result.status,
                        "conflicts": merge_result.conflicts
                    })
                    if not merge_result.success:
                        results["success"] = False

        elif strategy == "immediate":
            # Quick merge for hotfixes
            for wt in active_worktrees:
                merge_result = await self.worktree_service.merge_worktree(
                    worktree_id=UUID(wt["id"]),
                    target_branch=target,
                    delete_after=True
                )
                results["worktrees"].append({
                    "id": wt["id"],
                    "phase": wt.get("phase"),
                    "success": merge_result.success,
                    "status": merge_result.status
                })
                if not merge_result.success:
                    results["success"] = False

        elif strategy == "pr_required":
            # Don't merge, just report status for PR creation
            for wt in active_worktrees:
                status = await self.worktree_service.get_worktree_status(UUID(wt["id"]))
                results["worktrees"].append({
                    "id": wt["id"],
                    "phase": wt.get("phase"),
                    "work_branch": wt["work_branch"],
                    "status": "ready_for_pr",
                    "uncommitted_changes": status.get("uncommitted_changes", {}),
                    "recent_commits": status.get("recent_commits", [])
                })
            results["message"] = "Create pull requests for each worktree branch"

        return results

    async def cleanup_workflow_session(
        self,
        workflow_type: str,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Cleanup all worktrees for a workflow session.

        Args:
            workflow_type: Type of workflow
            project_id: Project identifier

        Returns:
            Cleanup results
        """
        worktrees = await self.list_workflow_worktrees(workflow_type, project_id)

        results = {
            "workflow_type": workflow_type,
            "cleaned": [],
            "failed": []
        }

        for wt in worktrees:
            if wt["status"] != "merged":
                try:
                    success = await self.worktree_service.cleanup_worktree(UUID(wt["id"]))
                    if success:
                        results["cleaned"].append(wt["id"])
                    else:
                        results["failed"].append({"id": wt["id"], "reason": "cleanup failed"})
                except Exception as e:
                    results["failed"].append({"id": wt["id"], "reason": str(e)})

        return results

    async def sync_workflow_worktrees(
        self,
        workflow_type: str,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Sync all workflow worktrees with their base branches.

        Args:
            workflow_type: Type of workflow
            project_id: Project identifier

        Returns:
            Sync results for each worktree
        """
        worktrees = await self.list_workflow_worktrees(workflow_type, project_id)
        active_worktrees = [wt for wt in worktrees if wt["status"] == "active"]

        results = {
            "workflow_type": workflow_type,
            "synced": [],
            "conflicts": []
        }

        for wt in active_worktrees:
            try:
                sync_result = await self.worktree_service.sync_with_base(UUID(wt["id"]))
                if sync_result["success"]:
                    results["synced"].append({
                        "id": wt["id"],
                        "phase": wt.get("phase")
                    })
                elif sync_result.get("conflicts"):
                    results["conflicts"].append({
                        "id": wt["id"],
                        "phase": wt.get("phase"),
                        "message": sync_result.get("message")
                    })
            except Exception as e:
                results["conflicts"].append({
                    "id": wt["id"],
                    "phase": wt.get("phase"),
                    "error": str(e)
                })

        return results

    async def get_workflow_statistics(
        self,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get workflow worktree statistics.

        Args:
            project_id: Optional project filter

        Returns:
            Statistics by workflow type
        """
        base_stats = await self.worktree_service.get_statistics()

        # Get workflow-specific stats
        query = select(GitWorktree)
        if project_id:
            query = query.where(GitWorktree.project_id == project_id)

        result = await self.db.execute(query)
        worktrees = result.scalars().all()

        workflow_stats = {}
        for workflow_type in WORKFLOW_WORKTREE_CONFIGS.keys():
            workflow_stats[workflow_type] = {
                "active": 0,
                "merged": 0,
                "total_commits": 0,
                "total_files_changed": 0
            }

        for wt in worktrees:
            metadata = wt.worktree_metadata or {}
            workflow_type = metadata.get("workflow_type")

            if workflow_type in workflow_stats:
                if wt.status == WorktreeStatus.ACTIVE.value:
                    workflow_stats[workflow_type]["active"] += 1
                elif wt.status == WorktreeStatus.MERGED.value:
                    workflow_stats[workflow_type]["merged"] += 1

                workflow_stats[workflow_type]["total_commits"] += wt.commit_count or 0
                workflow_stats[workflow_type]["total_files_changed"] += wt.files_changed or 0

        return {
            **base_stats,
            "by_workflow": workflow_stats,
            "supported_workflows": list(WORKFLOW_WORKTREE_CONFIGS.keys())
        }

    async def inject_worktree_context(
        self,
        workflow_type: str,
        project_id: int,
        agent_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Inject worktree information into workflow context.

        This is called by AgentService to add worktree context before
        executing workflow steps.

        Args:
            workflow_type: Type of workflow
            project_id: Project identifier
            agent_id: Agent executing the step
            context: Existing workflow context

        Returns:
            Enhanced context with worktree info
        """
        # Get or create worktree for this agent
        worktree = await self.get_workflow_worktree(workflow_type, project_id, agent_id)

        if not worktree:
            # Check if workflow type supports worktrees
            if workflow_type in WORKFLOW_WORKTREE_CONFIGS:
                config = WORKFLOW_WORKTREE_CONFIGS[workflow_type]

                # Determine phase for this agent
                agent_index = config["agents"].index(agent_id) if agent_id in config["agents"] else 0
                phase = config["phases"][agent_index] if agent_index < len(config["phases"]) else config["phases"][0]

                # Create worktree for agent
                worktree = await self.worktree_service.create_worktree(
                    agent_id=agent_id,
                    base_branch=config["base_branch"],
                    project_id=project_id,
                    metadata={
                        "workflow_type": workflow_type,
                        "phase": phase,
                        "auto_created": True
                    }
                )

        if worktree:
            context["worktree"] = {
                "id": str(worktree.id),
                "path": worktree.worktree_path,
                "branch": worktree.work_branch,
                "base_branch": worktree.base_branch,
                "status": worktree.status,
                "commit_count": worktree.commit_count or 0,
                "files_changed": worktree.files_changed or 0
            }

            # Add workflow-specific context
            if workflow_type in WORKFLOW_WORKTREE_CONFIGS:
                config = WORKFLOW_WORKTREE_CONFIGS[workflow_type]
                context["worktree"]["merge_strategy"] = config["merge_strategy"]
                context["worktree"]["auto_cleanup"] = config["auto_cleanup"]

        return context


# Constants for external use
SUPPORTED_WORKFLOW_TYPES = list(WORKFLOW_WORKTREE_CONFIGS.keys())
