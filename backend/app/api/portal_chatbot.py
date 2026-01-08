# backend/app/api/portal_chatbot.py
"""
Portal Chatbot API - Week 121

Conversational interface endpoints for Client Portal 2.0.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.portal_chatbot_service import PortalChatbotService
from app.services.journey_analytics_service import JourneyAnalyticsService

router = APIRouter(prefix="/api/portal", tags=["Portal Chatbot"])


# ============== REQUEST/RESPONSE SCHEMAS ==============

class CreateSessionRequest(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    project_id: Optional[int] = Field(None, description="Related project ID")


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    feature_context: Optional[dict] = Field(None, description="Feature context for responses")


class CloseSessionRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Session satisfaction rating")


class MessageFeedbackRequest(BaseModel):
    helpful: bool = Field(..., description="Whether message was helpful")
    feedback: Optional[str] = Field(None, max_length=500, description="Optional feedback text")


class ChatSessionResponse(BaseModel):
    id: str
    customer_id: str
    project_id: Optional[int]
    title: Optional[str]
    status: str
    primary_agent: str
    agents_involved: List[str]
    message_count: int
    resolved: bool
    satisfaction_rating: Optional[int]
    created_at: datetime
    last_message_at: Optional[datetime]
    closed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    content_type: str
    agent: Optional[str]
    detected_intent: Optional[str]
    intent_confidence: Optional[float]
    action_type: Optional[str]
    action_data: Optional[dict]
    helpful: Optional[bool]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatStatsResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    closed_sessions: int
    total_messages: int
    avg_messages_per_session: float
    avg_satisfaction_rating: float
    rated_sessions: int


# ============== ENDPOINTS ==============

@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    service = PortalChatbotService(db)

    session = await service.create_session(
        customer_id=request.customer_id,
        project_id=request.project_id,
    )

    # Track journey event
    journey_service = JourneyAnalyticsService(db)
    await journey_service.track_event(
        customer_id=request.customer_id,
        event_type="chatbot_opened",
        event_data={"session_id": str(session.id)},
        project_id=request.project_id,
    )

    return ChatSessionResponse(
        id=str(session.id),
        customer_id=session.customer_id,
        project_id=session.project_id,
        title=session.title,
        status=session.status,
        primary_agent=session.primary_agent,
        agents_involved=session.agents_involved or [],
        message_count=session.message_count,
        resolved=session.resolved,
        satisfaction_rating=session.satisfaction_rating,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
        closed_at=session.closed_at,
    )


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a chat session by ID."""
    service = PortalChatbotService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ChatSessionResponse(
        id=str(session.id),
        customer_id=session.customer_id,
        project_id=session.project_id,
        title=session.title,
        status=session.status,
        primary_agent=session.primary_agent,
        agents_involved=session.agents_involved or [],
        message_count=session.message_count,
        resolved=session.resolved,
        satisfaction_rating=session.satisfaction_rating,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
        closed_at=session.closed_at,
    )


@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def list_customer_sessions(
    customer_id: str,
    limit: int = 10,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List chat sessions for a customer."""
    service = PortalChatbotService(db)
    sessions = await service.get_customer_sessions(
        customer_id=customer_id,
        limit=limit,
        active_only=active_only,
    )

    return [
        ChatSessionResponse(
            id=str(s.id),
            customer_id=s.customer_id,
            project_id=s.project_id,
            title=s.title,
            status=s.status,
            primary_agent=s.primary_agent,
            agents_involved=s.agents_involved or [],
            message_count=s.message_count,
            resolved=s.resolved,
            satisfaction_rating=s.satisfaction_rating,
            created_at=s.created_at,
            last_message_at=s.last_message_at,
            closed_at=s.closed_at,
        )
        for s in sessions
    ]


@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the chatbot."""
    service = PortalChatbotService(db)

    try:
        message = await service.handle_message(
            session_id=session_id,
            message=request.message,
            feature_context=request.feature_context,
        )

        # Track journey event
        session = await service.get_session(session_id)
        if session:
            journey_service = JourneyAnalyticsService(db)
            await journey_service.track_chatbot_event(
                customer_id=session.customer_id,
                event_type="chatbot_message_sent",
                session_id=str(session_id),
                event_data={
                    "intent": message.detected_intent,
                    "agent": message.agent,
                },
            )

        return ChatMessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role,
            content=message.content,
            content_type=message.content_type,
            agent=message.agent,
            detected_intent=message.detected_intent,
            intent_confidence=message.intent_confidence,
            action_type=message.action_type,
            action_data=message.action_data,
            helpful=message.helpful,
            created_at=message.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get message history for a session."""
    service = PortalChatbotService(db)
    messages = await service.get_session_messages(
        session_id=session_id,
        limit=limit,
    )

    return [
        ChatMessageResponse(
            id=str(m.id),
            session_id=str(m.session_id),
            role=m.role,
            content=m.content,
            content_type=m.content_type,
            agent=m.agent,
            detected_intent=m.detected_intent,
            intent_confidence=m.intent_confidence,
            action_type=m.action_type,
            action_data=m.action_data,
            helpful=m.helpful,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/chat/sessions/{session_id}/close", response_model=ChatSessionResponse)
async def close_chat_session(
    session_id: UUID,
    request: CloseSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Close a chat session with optional rating."""
    service = PortalChatbotService(db)
    session = await service.close_session(
        session_id=session_id,
        rating=request.rating,
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Track journey event
    journey_service = JourneyAnalyticsService(db)
    await journey_service.track_chatbot_event(
        customer_id=session.customer_id,
        event_type="chatbot_closed",
        session_id=str(session_id),
        event_data={"rating": request.rating},
    )

    return ChatSessionResponse(
        id=str(session.id),
        customer_id=session.customer_id,
        project_id=session.project_id,
        title=session.title,
        status=session.status,
        primary_agent=session.primary_agent,
        agents_involved=session.agents_involved or [],
        message_count=session.message_count,
        resolved=session.resolved,
        satisfaction_rating=session.satisfaction_rating,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
        closed_at=session.closed_at,
    )


@router.post("/chat/messages/{message_id}/feedback")
async def submit_message_feedback(
    message_id: UUID,
    request: MessageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on a message."""
    service = PortalChatbotService(db)
    message = await service.mark_message_helpful(
        message_id=message_id,
        helpful=request.helpful,
        feedback=request.feedback,
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"success": True, "message_id": str(message_id)}


@router.get("/chat/stats", response_model=ChatStatsResponse)
async def get_chatbot_stats(
    customer_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get chatbot usage statistics."""
    service = PortalChatbotService(db)
    stats = await service.get_chatbot_stats(customer_id=customer_id)
    return ChatStatsResponse(**stats)


# ============== ALIAS ENDPOINTS FOR SPEC COMPATIBILITY ==============

@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    request: SendMessageRequest,
    customer_id: str,
    session_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Send chat message (spec-compatible endpoint).

    If session_id is not provided, creates a new session.
    """
    service = PortalChatbotService(db)

    # Create session if needed
    if session_id is None:
        session = await service.create_session(customer_id=customer_id)
        session_id = session.id

    message = await service.handle_message(
        session_id=session_id,
        message=request.message,
        feature_context=request.feature_context,
    )

    return ChatMessageResponse(
        id=str(message.id),
        session_id=str(message.session_id),
        role=message.role,
        content=message.content,
        content_type=message.content_type,
        agent=message.agent,
        detected_intent=message.detected_intent,
        intent_confidence=message.intent_confidence,
        action_type=message.action_type,
        action_data=message.action_data,
        helpful=message.helpful,
        created_at=message.created_at,
    )


@router.get("/chat/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    customer_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a customer (spec-compatible endpoint)."""
    service = PortalChatbotService(db)

    # Get most recent session
    sessions = await service.get_customer_sessions(
        customer_id=customer_id,
        limit=1,
    )

    if not sessions:
        return []

    messages = await service.get_session_messages(
        session_id=sessions[0].id,
        limit=limit,
    )

    return [
        ChatMessageResponse(
            id=str(m.id),
            session_id=str(m.session_id),
            role=m.role,
            content=m.content,
            content_type=m.content_type,
            agent=m.agent,
            detected_intent=m.detected_intent,
            intent_confidence=m.intent_confidence,
            action_type=m.action_type,
            action_data=m.action_data,
            helpful=m.helpful,
            created_at=m.created_at,
        )
        for m in messages
    ]
