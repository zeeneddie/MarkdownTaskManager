"""
Checkpoint Service for Restartable Workflows

Week 158 - Fase 24.6: Restartable Workflows

Provides checkpoint/resume functionality for all MarQed workflow types:
- Brown Paper (7 stages)
- Migration (8 stages)
- Green Paper (7 stages)
- Quality (5 stages)

Features:
- Save checkpoint after each stage
- Resume from failure point
- Idempotent stages (skip completed on resume)
- Error context for debugging
- Backward compatible (optional feature)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal

from app.models.workflow_checkpoint import (
    WorkflowCheckpoint,
    CheckpointStatus,
    CheckpointResponse,
    CheckpointStatusResponse,
)

logger = logging.getLogger(__name__)


class CheckpointService:
    """
    Service for managing workflow checkpoints.

    Enables restartable workflows by persisting state after each stage.
    """

    async def save_checkpoint(
        self,
        session_id: str,
        workflow_type: str,
        workflow_id: str,
        current_stage: str,
        completed_stages: List[str],
        stage_result: Dict[str, Any],
        shared_data: Dict[str, Any],
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowCheckpoint:
        """
        Save or update a checkpoint after a successful stage.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow (brown_paper, migration, etc.)
            workflow_id: Unique workflow execution ID
            current_stage: Name of the just-completed stage
            completed_stages: List of all completed stage names
            stage_result: Result data from the completed stage
            shared_data: Shared context data to preserve
            input_data: Original input data (only on first save)
            metadata: Additional metadata

        Returns:
            Updated WorkflowCheckpoint
        """
        async with AsyncSessionLocal() as db:
            # Check for existing checkpoint
            result = await db.execute(
                select(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.session_id == session_id,
                    WorkflowCheckpoint.workflow_type == workflow_type,
                    WorkflowCheckpoint.workflow_id == workflow_id,
                )
            )
            checkpoint = result.scalar_one_or_none()

            now = datetime.now(timezone.utc)

            if checkpoint:
                # Update existing checkpoint
                existing_results = checkpoint.stage_results or {}
                existing_results[current_stage] = stage_result

                checkpoint.current_stage = current_stage
                checkpoint.completed_stages = completed_stages
                checkpoint.stage_results = existing_results
                checkpoint.shared_data = shared_data
                checkpoint.checkpoint_version += 1
                checkpoint.updated_at = now
                checkpoint.last_checkpoint_at = now
                checkpoint.status = CheckpointStatus.RUNNING.value

                # Clear any previous error on successful save
                checkpoint.last_error = None
                checkpoint.error_stage = None
                checkpoint.error_context = None

                logger.info(
                    f"Updated checkpoint {checkpoint.id} for workflow {workflow_id} "
                    f"at stage {current_stage} (version {checkpoint.checkpoint_version})"
                )
            else:
                # Create new checkpoint
                checkpoint = WorkflowCheckpoint(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    workflow_type=workflow_type,
                    workflow_id=workflow_id,
                    current_stage=current_stage,
                    completed_stages=completed_stages,
                    stage_results={current_stage: stage_result},
                    shared_data=shared_data,
                    input_data=input_data or {},
                    checkpoint_metadata=metadata,
                    checkpoint_version=1,
                    status=CheckpointStatus.RUNNING.value,
                    created_at=now,
                    updated_at=now,
                    started_at=now,
                    last_checkpoint_at=now,
                )
                db.add(checkpoint)

                logger.info(
                    f"Created checkpoint {checkpoint.id} for workflow {workflow_id} "
                    f"at stage {current_stage}"
                )

            await db.commit()
            await db.refresh(checkpoint)
            return checkpoint

    async def load_checkpoint(
        self,
        session_id: str,
        workflow_type: str,
        workflow_id: Optional[str] = None,
    ) -> Optional[WorkflowCheckpoint]:
        """
        Load the most recent checkpoint for a session/workflow.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow
            workflow_id: Optional specific workflow ID

        Returns:
            WorkflowCheckpoint if found, None otherwise
        """
        async with AsyncSessionLocal() as db:
            query = select(WorkflowCheckpoint).where(
                WorkflowCheckpoint.session_id == session_id,
                WorkflowCheckpoint.workflow_type == workflow_type,
            )

            if workflow_id:
                query = query.where(WorkflowCheckpoint.workflow_id == workflow_id)
            else:
                # Get the most recent one
                query = query.order_by(WorkflowCheckpoint.created_at.desc())

            result = await db.execute(query)
            checkpoint = result.scalar_one_or_none()

            if checkpoint:
                logger.debug(
                    f"Loaded checkpoint {checkpoint.id} for session {session_id}, "
                    f"workflow {workflow_type}, stage {checkpoint.current_stage}"
                )

            return checkpoint

    async def get_resume_point(
        self,
        session_id: str,
        workflow_type: str,
    ) -> Optional[str]:
        """
        Get the stage name to resume from.

        Returns the next stage after the last completed one,
        or the failed stage if there was an error.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow

        Returns:
            Stage name to resume from, or None if no checkpoint
        """
        checkpoint = await self.load_checkpoint(session_id, workflow_type)

        if not checkpoint:
            return None

        return checkpoint.resume_stage

    async def restore_context(
        self,
        checkpoint: WorkflowCheckpoint,
    ) -> Dict[str, Any]:
        """
        Restore workflow context from a checkpoint.

        Returns a dictionary with all preserved state needed to resume.

        Args:
            checkpoint: The checkpoint to restore from

        Returns:
            Dictionary with restored context
        """
        return {
            "workflow_id": checkpoint.workflow_id,
            "workflow_type": checkpoint.workflow_type,
            "session_id": checkpoint.session_id,
            "started_at": checkpoint.started_at,
            "current_stage": checkpoint.current_stage,
            "completed_stages": checkpoint.completed_stages or [],
            "stage_results": checkpoint.stage_results or {},
            "shared_data": checkpoint.shared_data or {},
            "input_data": checkpoint.input_data or {},
            "metadata": checkpoint.checkpoint_metadata or {},
        }

    async def record_error(
        self,
        session_id: str,
        workflow_type: str,
        workflow_id: str,
        stage_name: str,
        error: str,
        error_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowCheckpoint]:
        """
        Record an error that occurred during stage execution.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow
            workflow_id: Workflow execution ID
            stage_name: Stage where error occurred
            error: Error message
            error_context: Additional error context

        Returns:
            Updated WorkflowCheckpoint
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.session_id == session_id,
                    WorkflowCheckpoint.workflow_type == workflow_type,
                    WorkflowCheckpoint.workflow_id == workflow_id,
                )
            )
            checkpoint = result.scalar_one_or_none()

            if not checkpoint:
                logger.warning(
                    f"Cannot record error: no checkpoint found for workflow {workflow_id}"
                )
                return None

            now = datetime.now(timezone.utc)

            checkpoint.last_error = error
            checkpoint.error_stage = stage_name
            checkpoint.error_context = error_context
            checkpoint.retry_count += 1
            checkpoint.status = CheckpointStatus.FAILED.value
            checkpoint.updated_at = now

            logger.error(
                f"Recorded error for workflow {workflow_id} at stage {stage_name}: {error}"
            )

            await db.commit()
            await db.refresh(checkpoint)
            return checkpoint

    async def mark_completed(
        self,
        session_id: str,
        workflow_type: str,
        workflow_id: str,
        final_output: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowCheckpoint]:
        """
        Mark a workflow as completed successfully.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow
            workflow_id: Workflow execution ID
            final_output: Optional final output to store

        Returns:
            Updated WorkflowCheckpoint
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.session_id == session_id,
                    WorkflowCheckpoint.workflow_type == workflow_type,
                    WorkflowCheckpoint.workflow_id == workflow_id,
                )
            )
            checkpoint = result.scalar_one_or_none()

            if not checkpoint:
                logger.warning(
                    f"Cannot mark completed: no checkpoint found for workflow {workflow_id}"
                )
                return None

            now = datetime.now(timezone.utc)

            checkpoint.status = CheckpointStatus.COMPLETED.value
            checkpoint.updated_at = now
            checkpoint.last_checkpoint_at = now

            if final_output:
                metadata = checkpoint.checkpoint_metadata or {}
                metadata["final_output"] = final_output
                checkpoint.checkpoint_metadata = metadata

            logger.info(f"Marked workflow {workflow_id} as completed")

            await db.commit()
            await db.refresh(checkpoint)
            return checkpoint

    async def mark_cancelled(
        self,
        session_id: str,
        workflow_type: str,
        workflow_id: str,
        reason: Optional[str] = None,
    ) -> Optional[WorkflowCheckpoint]:
        """
        Mark a workflow as cancelled.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow
            workflow_id: Workflow execution ID
            reason: Optional cancellation reason

        Returns:
            Updated WorkflowCheckpoint
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.session_id == session_id,
                    WorkflowCheckpoint.workflow_type == workflow_type,
                    WorkflowCheckpoint.workflow_id == workflow_id,
                )
            )
            checkpoint = result.scalar_one_or_none()

            if not checkpoint:
                return None

            now = datetime.now(timezone.utc)

            checkpoint.status = CheckpointStatus.CANCELLED.value
            checkpoint.updated_at = now

            if reason:
                metadata = checkpoint.checkpoint_metadata or {}
                metadata["cancellation_reason"] = reason
                checkpoint.checkpoint_metadata = metadata

            logger.info(f"Marked workflow {workflow_id} as cancelled: {reason}")

            await db.commit()
            await db.refresh(checkpoint)
            return checkpoint

    async def clear_checkpoints(
        self,
        session_id: str,
        workflow_type: str,
    ) -> int:
        """
        Clear all checkpoints for a session/workflow type.

        Used when restarting a workflow from scratch.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow

        Returns:
            Number of checkpoints deleted
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.session_id == session_id,
                    WorkflowCheckpoint.workflow_type == workflow_type,
                )
            )
            deleted_count = result.rowcount
            await db.commit()

            logger.info(
                f"Cleared {deleted_count} checkpoints for session {session_id}, "
                f"workflow {workflow_type}"
            )

            return deleted_count

    async def list_checkpoints(
        self,
        session_id: Optional[str] = None,
        workflow_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowCheckpoint]:
        """
        List checkpoints with optional filters.

        Args:
            session_id: Optional session filter
            workflow_type: Optional workflow type filter
            status: Optional status filter
            limit: Maximum results to return
            offset: Results offset for pagination

        Returns:
            List of matching WorkflowCheckpoints
        """
        async with AsyncSessionLocal() as db:
            query = select(WorkflowCheckpoint)

            if session_id:
                query = query.where(WorkflowCheckpoint.session_id == session_id)
            if workflow_type:
                query = query.where(WorkflowCheckpoint.workflow_type == workflow_type)
            if status:
                query = query.where(WorkflowCheckpoint.status == status)

            query = query.order_by(WorkflowCheckpoint.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            return list(result.scalars().all())

    async def list_failed_checkpoints(
        self,
        limit: int = 50,
    ) -> List[WorkflowCheckpoint]:
        """
        List all failed checkpoints for monitoring.

        Args:
            limit: Maximum results to return

        Returns:
            List of failed WorkflowCheckpoints
        """
        return await self.list_checkpoints(
            status=CheckpointStatus.FAILED.value,
            limit=limit,
        )

    async def get_checkpoint_status(
        self,
        workflow_id: str,
    ) -> Optional[CheckpointStatusResponse]:
        """
        Get compact status for a workflow.

        Args:
            workflow_id: Workflow execution ID

        Returns:
            CheckpointStatusResponse or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.workflow_id == workflow_id,
                )
            )
            checkpoint = result.scalar_one_or_none()

            if not checkpoint:
                return None

            return CheckpointStatusResponse(
                workflow_id=checkpoint.workflow_id,
                workflow_type=checkpoint.workflow_type,
                status=checkpoint.status,
                current_stage=checkpoint.current_stage,
                stages_completed=checkpoint.stages_completed_count,
                can_resume=checkpoint.can_resume,
                resume_stage=checkpoint.resume_stage,
                has_error=checkpoint.has_error,
                last_error=checkpoint.last_error,
                retry_count=checkpoint.retry_count,
                started_at=checkpoint.started_at.isoformat() if checkpoint.started_at else None,
                last_checkpoint_at=checkpoint.last_checkpoint_at.isoformat() if checkpoint.last_checkpoint_at else None,
            )

    async def prepare_for_resume(
        self,
        session_id: str,
        workflow_type: str,
        workflow_id: str,
        skip_failed_stage: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Prepare context for resuming a workflow.

        Clears error state and optionally marks failed stage as completed.

        Args:
            session_id: Session identifier
            workflow_type: Type of workflow
            workflow_id: Workflow execution ID
            skip_failed_stage: If True, skip the stage that failed

        Returns:
            Restored context dictionary, or None if no checkpoint
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowCheckpoint).where(
                    WorkflowCheckpoint.session_id == session_id,
                    WorkflowCheckpoint.workflow_type == workflow_type,
                    WorkflowCheckpoint.workflow_id == workflow_id,
                )
            )
            checkpoint = result.scalar_one_or_none()

            if not checkpoint:
                return None

            if not checkpoint.can_resume:
                logger.warning(
                    f"Cannot resume workflow {workflow_id}: status is {checkpoint.status}"
                )
                return None

            now = datetime.now(timezone.utc)

            # If skipping failed stage, add it to completed
            if skip_failed_stage and checkpoint.error_stage:
                completed = checkpoint.completed_stages or []
                if checkpoint.error_stage not in completed:
                    completed.append(checkpoint.error_stage)
                    checkpoint.completed_stages = completed

            # Clear error state for resume
            checkpoint.last_error = None
            checkpoint.error_stage = None
            checkpoint.error_context = None
            checkpoint.status = CheckpointStatus.RUNNING.value
            checkpoint.updated_at = now

            # Record resume in metadata
            metadata = checkpoint.checkpoint_metadata or {}
            resumes = metadata.get("resumes", [])
            resumes.append({
                "resumed_at": now.isoformat(),
                "skip_failed_stage": skip_failed_stage,
                "retry_count": checkpoint.retry_count,
            })
            metadata["resumes"] = resumes
            checkpoint.checkpoint_metadata = metadata

            await db.commit()
            await db.refresh(checkpoint)

            logger.info(
                f"Prepared workflow {workflow_id} for resume from stage {checkpoint.resume_stage}"
            )

            return await self.restore_context(checkpoint)


# Singleton instance
_checkpoint_service: Optional[CheckpointService] = None


def get_checkpoint_service() -> CheckpointService:
    """Get the singleton CheckpointService instance."""
    global _checkpoint_service
    if _checkpoint_service is None:
        _checkpoint_service = CheckpointService()
    return _checkpoint_service
