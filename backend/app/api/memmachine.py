"""
Week 73: MemMachine - Persistent Agent Memory API

REST endpoints for agent memory management:
- Session management (create, end, get)
- Memory storage (conversations, facts, preferences)
- Memory retrieval and search
- Memory management (compress, cleanup)
- Statistics and status

Endpoints:
- POST /api/memmachine/sessions - Create session
- POST /api/memmachine/sessions/{id}/end - End session
- GET /api/memmachine/sessions/{id} - Get session
- POST /api/memmachine/memories - Store memory
- POST /api/memmachine/conversations - Store conversation
- GET /api/memmachine/memories/{agent_id} - Get agent memories
- GET /api/memmachine/conversations/{session_id} - Get conversation history
- POST /api/memmachine/search - Search memories
- POST /api/memmachine/learn - Learn a fact
- POST /api/memmachine/preferences - Store preference
- GET /api/memmachine/preferences/{agent_id} - Get preferences
- DELETE /api/memmachine/memories/{id} - Delete memory
- POST /api/memmachine/compress - Compress memories
- POST /api/memmachine/cleanup - Cleanup expired
- GET /api/memmachine/stats/{agent_id} - Get agent stats
- GET /api/memmachine/status - System status
- GET /api/memmachine/health - Health check
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.memmachine_service import MemMachineService, MemoryType, MemoryPriority


router = APIRouter(prefix="/api/memmachine", tags=["MemMachine Agent Memory"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a memory session."""
    agent_id: str = Field(..., description="Agent ID (e.g., 'felix', 'quinn')")
    project_id: Optional[UUID] = Field(None, description="Optional project context")
    context: Optional[Dict[str, Any]] = Field(None, description="Initial context")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "agent_id": "felix",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "context": {"task": "code_review"}
            }
        })


class EndSessionRequest(BaseModel):
    """Request to end a session."""
    summary: Optional[str] = Field(None, description="Optional session summary")


class StoreMemoryRequest(BaseModel):
    """Request to store a memory."""
    session_id: str = Field(..., description="Current session ID")
    agent_id: str = Field(..., description="Agent ID")
    content: str = Field(..., description="Memory content")
    memory_type: str = Field(MemoryType.FACT, description="Type of memory")
    priority: str = Field(MemoryPriority.MEDIUM, description="Retention priority")
    tags: Optional[List[str]] = Field(None, description="Searchable tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class StoreConversationRequest(BaseModel):
    """Request to store a conversation message."""
    session_id: str = Field(..., description="Current session ID")
    agent_id: str = Field(..., description="Agent ID")
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchMemoriesRequest(BaseModel):
    """Request to search memories."""
    agent_id: str = Field(..., description="Agent to search for")
    query: str = Field(..., description="Search query")
    memory_types: Optional[List[str]] = Field(None, description="Filter by types")
    limit: int = Field(20, ge=1, le=100, description="Max results")


class LearnFactRequest(BaseModel):
    """Request to learn a fact."""
    agent_id: str = Field(..., description="Learning agent")
    session_id: str = Field(..., description="Current session")
    fact: str = Field(..., description="Fact to learn")
    source: str = Field(..., description="Source of the fact")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence level")


class StorePreferenceRequest(BaseModel):
    """Request to store a preference."""
    agent_id: str = Field(..., description="Agent ID")
    session_id: str = Field(..., description="Current session")
    preference_key: str = Field(..., description="Preference key")
    preference_value: Any = Field(..., description="Preference value")


class CompressMemoriesRequest(BaseModel):
    """Request to compress memories."""
    agent_id: str = Field(..., description="Agent to compress for")
    memory_type: str = Field(MemoryType.CONVERSATION, description="Type to compress")


class SessionResponse(BaseModel):
    """Response with session details."""
    id: str
    agent_id: str
    project_id: Optional[str] = None
    context: Dict[str, Any]
    created_at: str
    last_activity: str
    message_count: int
    memory_count: int
    status: str
    restored_memories: Optional[int] = None


class MemoryResponse(BaseModel):
    """Response with memory details."""
    id: str
    session_id: str
    agent_id: str
    content: str
    memory_type: str
    priority: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: str
    access_count: int


class StatusResponse(BaseModel):
    """System status response."""
    status: str
    total_sessions: int
    active_sessions: int
    total_memories: int
    unique_agents: int
    features: List[str]
    version: str


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new memory session for an agent.

    Sessions provide context for memory storage and retrieval.
    Previous memories from the same agent are restored automatically.
    """
    service = MemMachineService(db)
    session = await service.create_session(
        agent_id=request.agent_id,
        project_id=request.project_id,
        context=request.context
    )
    return SessionResponse(**session)


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str = Path(..., description="Session ID to end"),
    request: EndSessionRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """
    End a memory session.

    Persists important memories and generates session summary.
    """
    service = MemMachineService(db)
    summary = request.summary if request else None
    result = await service.end_session(session_id, summary)
    return result


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str = Path(..., description="Session ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get session details."""
    service = MemMachineService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ============================================================================
# MEMORY STORAGE ENDPOINTS
# ============================================================================

@router.post("/memories")
async def store_memory(
    request: StoreMemoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Store a memory for an agent.

    Memories can be facts, preferences, skills, or context.
    Priority determines retention period.
    """
    service = MemMachineService(db)
    memory = await service.store_memory(
        session_id=request.session_id,
        agent_id=request.agent_id,
        content=request.content,
        memory_type=request.memory_type,
        priority=request.priority,
        tags=request.tags,
        metadata=request.metadata
    )
    return memory


@router.post("/conversations")
async def store_conversation(
    request: StoreConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Store a conversation message.

    Automatically tracks message count and session activity.
    """
    service = MemMachineService(db)
    memory = await service.store_conversation(
        session_id=request.session_id,
        agent_id=request.agent_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata
    )
    return memory


# ============================================================================
# MEMORY RETRIEVAL ENDPOINTS
# ============================================================================

@router.get("/memories/{agent_id}")
async def get_agent_memories(
    agent_id: str = Path(..., description="Agent ID"),
    project_id: Optional[UUID] = Query(None, description="Project filter"),
    memory_types: Optional[str] = Query(None, description="Comma-separated types"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    min_priority: Optional[str] = Query(None, description="Minimum priority"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve memories for an agent.

    Supports filtering by type, tags, and priority.
    """
    service = MemMachineService(db)

    type_list = memory_types.split(",") if memory_types else None
    tag_list = tags.split(",") if tags else None

    memories = await service.get_agent_memories(
        agent_id=agent_id,
        project_id=project_id,
        memory_types=type_list,
        tags=tag_list,
        min_priority=min_priority,
        limit=limit
    )
    return {"agent_id": agent_id, "count": len(memories), "memories": memories}


@router.get("/conversations/{session_id}")
async def get_conversation_history(
    session_id: str = Path(..., description="Session ID"),
    limit: int = Query(50, ge=1, le=200, description="Max messages"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history for a session.

    Returns messages in chronological order.
    """
    service = MemMachineService(db)
    history = await service.get_conversation_history(
        session_id=session_id,
        limit=limit
    )
    return {"session_id": session_id, "count": len(history), "messages": history}


@router.post("/search")
async def search_memories(
    request: SearchMemoriesRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search memories using keywords.

    Returns matches with relevance scores.
    """
    service = MemMachineService(db)
    results = await service.search_memories(
        agent_id=request.agent_id,
        query=request.query,
        memory_types=request.memory_types,
        limit=request.limit
    )
    return {"query": request.query, "count": len(results), "results": results}


# ============================================================================
# LEARNING ENDPOINTS
# ============================================================================

@router.post("/learn")
async def learn_fact(
    request: LearnFactRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Store a learned fact for an agent.

    Higher confidence facts get higher retention priority.
    """
    service = MemMachineService(db)
    memory = await service.learn_fact(
        agent_id=request.agent_id,
        session_id=request.session_id,
        fact=request.fact,
        source=request.source,
        confidence=request.confidence
    )
    return memory


@router.post("/preferences")
async def store_preference(
    request: StorePreferenceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Store a preference for an agent.

    Preferences have high retention priority.
    """
    service = MemMachineService(db)
    memory = await service.store_preference(
        agent_id=request.agent_id,
        session_id=request.session_id,
        preference_key=request.preference_key,
        preference_value=request.preference_value
    )
    return memory


@router.get("/preferences/{agent_id}")
async def get_preferences(
    agent_id: str = Path(..., description="Agent ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all preferences for an agent."""
    service = MemMachineService(db)
    preferences = await service.get_preferences(agent_id)
    return {"agent_id": agent_id, "preferences": preferences}


# ============================================================================
# MEMORY MANAGEMENT ENDPOINTS
# ============================================================================

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str = Path(..., description="Memory ID to delete"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific memory."""
    service = MemMachineService(db)
    result = await service.forget_memory(memory_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/compress")
async def compress_memories(
    request: CompressMemoriesRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compress old memories into summaries.

    Reduces memory count while preserving key information.
    """
    service = MemMachineService(db)
    result = await service.compress_memories(
        agent_id=request.agent_id,
        memory_type=request.memory_type
    )
    return result


@router.post("/cleanup")
async def cleanup_expired(
    db: AsyncSession = Depends(get_db)
):
    """
    Remove all expired memories.

    Should be run periodically to maintain memory health.
    """
    service = MemMachineService(db)
    result = await service.cleanup_expired()
    return result


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/{agent_id}")
async def get_agent_stats(
    agent_id: str = Path(..., description="Agent ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get memory statistics for an agent."""
    service = MemMachineService(db)
    stats = await service.get_agent_stats(agent_id)
    return stats


@router.get("/status", response_model=StatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """Get overall MemMachine system status."""
    service = MemMachineService(db)
    status = await service.get_system_status()
    return StatusResponse(**status)


@router.get("/health")
async def health_check():
    """Health check endpoint for MemMachine service."""
    return {
        "status": "healthy",
        "service": "memmachine",
        "version": "1.0.0",
        "features": [
            "conversation_history",
            "fact_learning",
            "preference_storage",
            "memory_compression",
            "cross_session_continuity"
        ]
    }
