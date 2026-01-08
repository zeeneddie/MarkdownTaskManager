"""
Council Human Review API Routes

Week 55: Human-in-the-Loop Council
REST API for the 6-phase council workflow with human validation.

Endpoints:
- POST   /sessions                    - Create new session
- GET    /sessions                    - List sessions
- GET    /sessions/{id}               - Get session details
- POST   /sessions/{id}/generate      - Phase 1: Start generation
- POST   /sessions/{id}/peer-review   - Phase 2: Start peer review
- POST   /sessions/{id}/consensus     - Phase 3: Create consensus
- POST   /sessions/{id}/human-review  - Phase 4: Submit human feedback
- POST   /sessions/{id}/finalize      - Phase 5: Final synthesis
- POST   /sessions/{id}/approve       - Phase 6: Approve
- POST   /sessions/{id}/reject        - Phase 6: Reject
- GET    /statistics                  - Get session statistics
- GET    /documents                   - List documents
- GET    /documents/{path}/history    - Document version history
- POST   /documents/sync              - Sync file to database
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.council_human_review_service import CouncilHumanReviewService
from app.services.document_sync_service import DocumentSyncService
from app.models.council_human_review import SessionStatus, DocumentType

router = APIRouter(prefix="/api/council-human-review", tags=["Council Human Review"])


# =============================================================================
# Request/Response Models
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new council session."""
    document_type: str = Field(..., description="Type of document (onboarding, architecture, etc.)")
    project_id: Optional[int] = Field(None, description="Optional project ID")
    document_name: Optional[str] = Field(None, description="Custom document name")
    providers_config: Optional[dict] = Field(None, description="Custom provider configuration")


class GenerateRequest(BaseModel):
    """Request to start generation phase."""
    prompt: str = Field(..., description="Generation prompt")
    context: Optional[dict] = Field(None, description="Additional context")


class HumanFeedbackRequest(BaseModel):
    """Request to submit human feedback."""
    feedback: dict = Field(..., description="General feedback/corrections")
    marked_correct: Optional[dict] = Field(None, description="Items marked correct per provider")
    conflicts_resolved: Optional[dict] = Field(None, description="How conflicts were resolved")
    additions: Optional[str] = Field(None, description="What human added that all LLMs missed")


class ApproveRequest(BaseModel):
    """Request to approve consensus."""
    approved_by: str = Field(..., description="Who approved")
    write_to_file: bool = Field(True, description="Write MD file to filesystem")
    git_commit: bool = Field(False, description="Create Git commit")


class RejectRequest(BaseModel):
    """Request to reject consensus."""
    rejected_by: str = Field(..., description="Who rejected")
    reason: str = Field(..., description="Rejection reason")


class SyncFileRequest(BaseModel):
    """Request to sync a file to database."""
    document_path: str = Field(..., description="Relative path to document")
    document_type: str = Field(..., description="Type of document")
    project_id: Optional[int] = Field(None, description="Optional project ID")


class SessionResponse(BaseModel):
    """Standard session response."""
    id: str
    project_id: Optional[int]
    document_type: str
    document_name: Optional[str]
    status: str
    created_at: str
    updated_at: str


# =============================================================================
# Session Endpoints
# =============================================================================

@router.post("/sessions", response_model=dict)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new council session."""
    service = CouncilHumanReviewService(db)
    try:
        session = await service.create_session(
            document_type=request.document_type,
            project_id=request.project_id,
            document_name=request.document_name,
            providers_config=request.providers_config
        )
        return session.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.get("/sessions")
async def list_sessions(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    status: Optional[str] = Query(None, description="Filter by status"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(50, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """List council sessions with optional filters."""
    service = CouncilHumanReviewService(db)
    try:
        sessions = await service.list_sessions(
            project_id=project_id,
            status=status,
            document_type=document_type,
            limit=limit
        )
        return {"sessions": [s.to_dict() for s in sessions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get full session details including responses, reviews, and consensus."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        details = await service.get_session_details(uuid)
        if not details:
            raise HTTPException(status_code=404, detail="Session not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


# =============================================================================
# Phase Endpoints
# =============================================================================

@router.post("/sessions/{session_id}/generate")
async def start_generation(
    session_id: str,
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Phase 1: Start parallel generation from all providers."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        responses = await service.start_generation(
            session_id=uuid,
            prompt=request.prompt,
            context=request.context
        )
        return {
            "phase": "generation",
            "status": "completed",
            "responses": [r.to_dict() for r in responses]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/sessions/{session_id}/peer-review")
async def start_peer_review(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Phase 2: Start round-robin peer review."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        reviews = await service.start_peer_review(uuid)
        return {
            "phase": "peer_review",
            "status": "completed",
            "reviews": [r.to_dict() for r in reviews]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/sessions/{session_id}/consensus")
async def create_consensus(
    session_id: str,
    orchestrator_override: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Phase 3: Create consensus document from peer reviews."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        consensus = await service.create_consensus(uuid, orchestrator_override)
        return {
            "phase": "orchestrating",
            "status": "completed",
            "consensus": consensus.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/sessions/{session_id}/human-review")
async def submit_human_feedback(
    session_id: str,
    request: HumanFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Phase 4: Submit human review feedback."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        consensus = await service.submit_human_feedback(
            session_id=uuid,
            feedback=request.feedback,
            marked_correct=request.marked_correct,
            conflicts_resolved=request.conflicts_resolved,
            additions=request.additions
        )
        return {
            "phase": "human_review",
            "status": "completed",
            "consensus": consensus.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/sessions/{session_id}/finalize")
async def finalize_consensus(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Phase 5: LLM incorporates human feedback into final document."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        consensus = await service.finalize_consensus(uuid)
        return {
            "phase": "finalizing",
            "status": "completed",
            "consensus": consensus.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/sessions/{session_id}/approve")
async def approve_consensus(
    session_id: str,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Phase 6: Approve consensus and optionally write to filesystem."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        result = await service.approve_consensus(
            session_id=uuid,
            approved_by=request.approved_by,
            write_to_file=request.write_to_file,
            git_commit=request.git_commit
        )
        return {
            "phase": "approved",
            "status": "completed",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/sessions/{session_id}/reject")
async def reject_consensus(
    session_id: str,
    request: RejectRequest,
    db: AsyncSession = Depends(get_db)
):
    """Phase 6 (alternate): Reject consensus."""
    service = CouncilHumanReviewService(db)
    try:
        uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session ID format")

    try:
        session = await service.reject_consensus(
            session_id=uuid,
            rejected_by=request.rejected_by,
            reason=request.reason
        )
        return {
            "phase": "rejected",
            "status": "completed",
            "session": session.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


# =============================================================================
# Statistics & Documents
# =============================================================================

@router.get("/statistics")
async def get_statistics(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db)
):
    """Get session statistics."""
    service = CouncilHumanReviewService(db)
    try:
        return await service.get_session_statistics(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.get("/documents")
async def list_documents(
    document_type: Optional[str] = Query(None, description="Filter by type"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db)
):
    """List documents by type."""
    sync_service = DocumentSyncService(db)

    try:
        if document_type:
            documents = await sync_service.get_documents_by_type(document_type, project_id)
        else:
            # Get all document types
            documents = []
            for dt in DocumentType:
                docs = await sync_service.get_documents_by_type(dt.value, project_id)
                documents.extend(docs)

        return {"documents": [d.to_dict() for d in documents]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.get("/documents/history")
async def get_document_history(
    document_path: str = Query(..., description="Document path"),
    project_id: Optional[int] = Query(None, description="Project ID"),
    limit: int = Query(10, description="Max versions"),
    db: AsyncSession = Depends(get_db)
):
    """Get version history for a document."""
    sync_service = DocumentSyncService(db)
    try:
        versions = await sync_service.get_document_history(document_path, project_id, limit)
        return {"versions": [v.to_dict() for v in versions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.post("/documents/sync")
async def sync_file_to_db(
    request: SyncFileRequest,
    db: AsyncSession = Depends(get_db)
):
    """Sync a file from filesystem to database."""
    sync_service = DocumentSyncService(db)
    try:
        version = await sync_service.sync_file_to_db(
            document_path=request.document_path,
            document_type=request.document_type,
            project_id=request.project_id
        )

        if version:
            return {
                "status": "synced",
                "version": version.to_dict()
            }
        else:
            return {
                "status": "unchanged",
                "message": "File has not changed since last sync"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")


@router.get("/documents/compare")
async def compare_versions(
    document_path: str = Query(..., description="Document path"),
    version1: int = Query(..., description="First version"),
    version2: int = Query(..., description="Second version"),
    project_id: Optional[int] = Query(None, description="Project ID"),
    db: AsyncSession = Depends(get_db)
):
    """Compare two versions of a document."""
    sync_service = DocumentSyncService(db)
    comparison = await sync_service.compare_versions(document_path, version1, version2, project_id)

    if not comparison:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    return comparison


@router.post("/documents/rollback")
async def rollback_document(
    document_path: str = Body(..., embed=True),
    target_version: int = Body(..., embed=True),
    project_id: Optional[int] = Body(None, embed=True),
    reason: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Rollback a document to a previous version."""
    sync_service = DocumentSyncService(db)
    version = await sync_service.rollback_to_version(
        document_path=document_path,
        target_version=target_version,
        project_id=project_id,
        reason=reason
    )

    if not version:
        raise HTTPException(status_code=404, detail="Target version not found")

    return {
        "status": "rolled_back",
        "version": version.to_dict()
    }


# =============================================================================
# Health & Meta
# =============================================================================

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "council-human-review",
        "version": "1.0.0",
        "phases": [
            "1. GENERATION - 3 providers generate in parallel",
            "2. PEER_REVIEW - Round-robin evaluation",
            "3. ORCHESTRATING - Create consensus",
            "4. HUMAN_REVIEW - Mark correct, add missing",
            "5. FINALIZING - Incorporate feedback",
            "6. APPROVED/REJECTED - Storage & sync"
        ],
        "document_types": [dt.value for dt in DocumentType],
        "session_statuses": [ss.value for ss in SessionStatus]
    }
