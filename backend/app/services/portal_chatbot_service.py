# backend/app/services/portal_chatbot_service.py
"""
Portal Chatbot Service - Week 121

LLM-powered conversational interface for the Client Portal.
Uses Peter agent for understanding, Diana agent for response generation.
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chatbot_journey import (
    ChatSession, ChatMessage, ChatSessionStatus, ChatRole,
    ChatContentType, ChatIntent, ChatAgent, ChatActionType,
    INTENT_PATTERNS, AGENT_TEMPLATES
)
from app.providers.ollama_provider import OllamaProvider
from app.providers.base import LLMRequest


# Agent LLM configurations
AGENT_MODELS = {
    ChatAgent.PETER.value: "qwen2.5-coder:7b",   # Product Owner - Classification
    ChatAgent.DIANA.value: "mistral:latest",     # Documentation - Message generation
    ChatAgent.FELIX.value: "qwen2.5-coder:7b",   # Architect - Technical questions
    ChatAgent.ELIZA.value: "deepseek-r1:latest", # Estimation - ETA calculations
    ChatAgent.PAUL.value: "qwen2.5:7b",          # Project Lead - Sprint questions
    ChatAgent.TESSA.value: "qwen2.5-coder:7b",   # Test Engineer - Test questions
}


class PortalChatbotService:
    """
    LLM-powered conversational interface for Client Portal.

    Features:
    - Intent classification (Peter agent)
    - Human-friendly responses (Diana agent)
    - Feature status queries
    - ETA calculations
    - New request flow initiation
    - Context-aware conversations
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._providers: Dict[str, OllamaProvider] = {}

    def _get_provider(self, agent: str) -> OllamaProvider:
        """Get or create provider for agent."""
        if agent not in self._providers:
            model = AGENT_MODELS.get(agent, "qwen2.5-coder:7b")
            self._providers[agent] = OllamaProvider(model=model)
        return self._providers[agent]

    # ============== SESSION MANAGEMENT ==============

    async def create_session(
        self,
        customer_id: str,
        project_id: Optional[int] = None,
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            id=uuid4(),
            customer_id=customer_id,
            project_id=project_id,
            status=ChatSessionStatus.ACTIVE.value,
            primary_agent=ChatAgent.PETER.value,
            agents_involved=[ChatAgent.PETER.value],
            context={},
            feature_ids_mentioned=[],
            message_count=0,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """Get session by ID."""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_customer_sessions(
        self,
        customer_id: str,
        limit: int = 10,
        active_only: bool = False,
    ) -> List[ChatSession]:
        """Get sessions for a customer."""
        query = select(ChatSession).where(
            ChatSession.customer_id == customer_id
        )
        if active_only:
            query = query.where(
                ChatSession.status == ChatSessionStatus.ACTIVE.value
            )
        query = query.order_by(ChatSession.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def close_session(
        self,
        session_id: UUID,
        rating: Optional[int] = None,
    ) -> ChatSession:
        """Close a chat session."""
        session = await self.get_session(session_id)
        if session:
            session.close(rating)
            await self.db.commit()
            await self.db.refresh(session)
        return session

    # ============== MESSAGE HANDLING ==============

    async def handle_message(
        self,
        session_id: UUID,
        message: str,
        feature_context: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """
        Process user message and generate response.

        Args:
            session_id: Chat session ID
            message: User's message
            feature_context: Optional context about features

        Returns:
            Assistant's response message
        """
        session = await self.get_session(session_id)
        if not session or not session.is_active():
            raise ValueError("Session not found or not active")

        # Store user message
        user_message = await self._store_message(
            session_id=session_id,
            customer_id=session.customer_id,
            role=ChatRole.USER.value,
            content=message,
        )

        # Classify intent with Peter
        intent, confidence, entities = await self._classify_intent(
            message, session.context
        )

        # Update user message with intent
        user_message.detected_intent = intent
        user_message.intent_confidence = confidence
        user_message.entities = entities

        # Route to appropriate agent and generate response
        response_agent, response_content, action_type, action_data = await self._route_and_respond(
            intent=intent,
            message=message,
            entities=entities,
            session=session,
            feature_context=feature_context,
        )

        # Store and return assistant response
        assistant_message = await self._store_message(
            session_id=session_id,
            customer_id=session.customer_id,
            role=ChatRole.ASSISTANT.value,
            content=response_content,
            agent=response_agent,
            detected_intent=intent,
            action_type=action_type,
            action_data=action_data,
        )

        # Update session
        session.add_message()
        session.add_message()  # Two messages (user + assistant)
        session.add_agent(response_agent)

        # Extract and store feature IDs mentioned
        if entities and "feature_id" in entities:
            session.add_feature_mention(entities["feature_id"])

        await self.db.commit()

        return assistant_message

    async def _store_message(
        self,
        session_id: UUID,
        customer_id: str,
        role: str,
        content: str,
        agent: Optional[str] = None,
        detected_intent: Optional[str] = None,
        action_type: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """Store a chat message."""
        message = ChatMessage(
            id=uuid4(),
            session_id=session_id,
            customer_id=customer_id,
            role=role,
            content=content,
            content_type=ChatContentType.TEXT.value,
            agent=agent,
            detected_intent=detected_intent,
            action_type=action_type,
            action_data=action_data,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(message)
        await self.db.flush()

        return message

    # ============== INTENT CLASSIFICATION ==============

    async def _classify_intent(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify user intent using Peter agent.

        Returns:
            Tuple of (intent, confidence, extracted_entities)
        """
        # First try pattern matching for quick classification
        pattern_intent, pattern_confidence = self._pattern_match_intent(message)

        if pattern_confidence >= 0.8:
            entities = self._extract_entities(message, pattern_intent)
            return pattern_intent, pattern_confidence, entities

        # Use LLM for complex classification
        provider = self._get_provider(ChatAgent.PETER.value)

        system_prompt = """Je bent Peter, de product owner agent. Je taak is om de intentie van gebruikersvragen te classificeren.

Classificeer het bericht naar een van deze intenties:
- status_query: Vragen over status van een feature ("hoe staat het met", "status van", "waar is")
- eta_query: Vragen over timing/wanneer ("wanneer", "hoe lang nog", "deadline")
- new_request: Verzoek voor nieuwe feature ("ik wil", "nieuwe feature", "aanvragen")
- feature_search: Zoeken naar features ("zoek", "vind", "waar kan ik")
- help: Hulpvragen ("help", "hoe werkt", "wat kan ik")
- feedback: Feedback geven ("feedback", "klacht", "suggestie")
- voting: Stemmen op features ("stem", "vote", "ondersteunen")
- general: Overige vragen

Antwoord alleen met een JSON object:
{"intent": "<intent>", "confidence": 0.0-1.0, "entities": {"feature_id": null, "feature_title": null}}

Extraheer ook entities zoals feature ID's of titels uit de vraag."""

        request = LLMRequest(
            prompt=f"Classificeer dit bericht: \"{message}\"",
            system=system_prompt,
            temperature=0.1,
            max_tokens=200,
            timeout=30,
        )

        response = await provider.generate(request)

        if response.success:
            try:
                import json
                result = json.loads(response.content)
                return (
                    result.get("intent", ChatIntent.GENERAL.value),
                    result.get("confidence", 0.7),
                    result.get("entities", {}),
                )
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback to pattern match
        entities = self._extract_entities(message, pattern_intent)
        return pattern_intent, max(0.5, pattern_confidence), entities

    def _pattern_match_intent(self, message: str) -> Tuple[str, float]:
        """Quick pattern-based intent matching."""
        message_lower = message.lower()

        for intent, patterns in INTENT_PATTERNS.items():
            matches = sum(1 for p in patterns if p in message_lower)
            if matches > 0:
                confidence = min(0.5 + (matches * 0.15), 0.9)
                return intent, confidence

        return ChatIntent.GENERAL.value, 0.3

    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Extract entities from message."""
        entities = {}

        # Extract feature IDs (numbers after # or "feature")
        id_match = re.search(r'#(\d+)|feature\s*(\d+)', message.lower())
        if id_match:
            entities["feature_id"] = int(id_match.group(1) or id_match.group(2))

        # Extract quoted text as potential feature title
        title_match = re.search(r'"([^"]+)"|\'([^\']+)\'', message)
        if title_match:
            entities["feature_title"] = title_match.group(1) or title_match.group(2)

        return entities

    # ============== RESPONSE ROUTING ==============

    async def _route_and_respond(
        self,
        intent: str,
        message: str,
        entities: Dict[str, Any],
        session: ChatSession,
        feature_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Route to appropriate agent and generate response.

        Returns:
            Tuple of (agent, response_content, action_type, action_data)
        """
        if intent == ChatIntent.STATUS_QUERY.value:
            return await self._handle_status_query(
                message, entities, feature_context
            )

        elif intent == ChatIntent.ETA_QUERY.value:
            return await self._handle_eta_query(
                message, entities, feature_context
            )

        elif intent == ChatIntent.NEW_REQUEST.value:
            return await self._handle_new_request(message)

        elif intent == ChatIntent.FEATURE_SEARCH.value:
            return await self._handle_feature_search(message, entities)

        elif intent == ChatIntent.HELP.value:
            return await self._handle_help(message)

        elif intent == ChatIntent.FEEDBACK.value:
            return await self._handle_feedback(message, entities)

        elif intent == ChatIntent.VOTING.value:
            return await self._handle_voting(message, entities)

        else:
            return await self._handle_general(message, session)

    async def _handle_status_query(
        self,
        message: str,
        entities: Dict[str, Any],
        feature_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle status query using Diana for response generation."""
        feature_id = entities.get("feature_id")
        feature_title = entities.get("feature_title")

        if feature_context:
            # We have context - generate friendly status message
            response = await self._generate_diana_response(
                template_key="status_update",
                context={
                    "feature_title": feature_context.get("title", "je feature"),
                    "status": feature_context.get("status", "in progress"),
                    "additional_info": feature_context.get("description", ""),
                }
            )
            return (
                ChatAgent.DIANA.value,
                response,
                ChatActionType.SHOW_STATUS.value,
                {"feature_id": feature_id},
            )
        elif feature_id or feature_title:
            # We need to look up the feature
            return (
                ChatAgent.PETER.value,
                f"Even kijken naar {'#' + str(feature_id) if feature_id else feature_title}...\n\n"
                "Ik heb wat meer informatie nodig om je te helpen. Kun je de exacte feature ID geven?",
                ChatActionType.SHOW_STATUS.value,
                {"feature_id": feature_id, "feature_title": feature_title},
            )
        else:
            return (
                ChatAgent.PETER.value,
                AGENT_TEMPLATES[ChatAgent.PETER.value]["status_not_found"],
                None,
                None,
            )

    async def _handle_eta_query(
        self,
        message: str,
        entities: Dict[str, Any],
        feature_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle ETA query using Eliza for estimation."""
        feature_id = entities.get("feature_id")

        if feature_context and "eta" in feature_context:
            response = await self._generate_diana_response(
                template_key="eta_response",
                context={
                    "title": feature_context.get("title", "je feature"),
                    "eta": feature_context.get("eta", "binnenkort"),
                }
            )
            return (
                ChatAgent.DIANA.value,
                response,
                ChatActionType.SHOW_ETA.value,
                {"feature_id": feature_id, "eta": feature_context.get("eta")},
            )
        else:
            return (
                ChatAgent.ELIZA.value,
                "Om een accurate inschatting te geven, heb ik het feature ID nodig. "
                "Welke feature wil je weten wanneer klaar is?",
                None,
                None,
            )

    async def _handle_new_request(
        self,
        message: str,
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle new feature request initiation."""
        return (
            ChatAgent.PETER.value,
            AGENT_TEMPLATES[ChatAgent.PETER.value]["new_request_start"] +
            "\n\nVertel me kort wat je wilt: wat is het doel en voor wie is het bedoeld?",
            ChatActionType.START_REQUEST.value,
            {"message": message},
        )

    async def _handle_feature_search(
        self,
        message: str,
        entities: Dict[str, Any],
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle feature search."""
        search_term = entities.get("feature_title") or message

        return (
            ChatAgent.PETER.value,
            f"Ik zoek voor je naar features die matchen met '{search_term}'.\n\n"
            "Kun je me vertellen in welke categorie je zoekt? "
            "(bijv. authenticatie, export, UI, etc.)",
            None,
            {"search_term": search_term},
        )

    async def _handle_help(
        self,
        message: str,
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle help request."""
        help_response = """Ik kan je helpen met:

**Feature Requests:**
- Status opvragen: "Hoe staat het met #123?"
- Nieuwe aanvraag: "Ik wil een nieuwe feature"
- Zoeken: "Zoek features over dark mode"

**Informatie:**
- ETA opvragen: "Wanneer is mijn feature klaar?"
- Stemmen: "Ik wil stemmen op #456"
- Feedback: "Ik wil feedback geven"

Stel gerust je vraag!"""

        return (
            ChatAgent.DIANA.value,
            help_response,
            None,
            None,
        )

    async def _handle_feedback(
        self,
        message: str,
        entities: Dict[str, Any],
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle feedback intent."""
        feature_id = entities.get("feature_id")

        if feature_id:
            return (
                ChatAgent.DIANA.value,
                f"Fijn dat je feedback wilt geven over feature #{feature_id}!\n\n"
                "Gebruik de feedback knop op de feature pagina, of vertel me hier "
                "je ervaring. Was je tevreden met het resultaat?",
                ChatActionType.FEEDBACK.value,
                {"feature_id": feature_id},
            )
        else:
            return (
                ChatAgent.DIANA.value,
                "Ik help je graag met feedback! Over welke feature wil je feedback geven?\n\n"
                "Geef het feature nummer (bijv. #123) of beschrijf welke feature je bedoelt.",
                None,
                None,
            )

    async def _handle_voting(
        self,
        message: str,
        entities: Dict[str, Any],
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle voting intent."""
        feature_id = entities.get("feature_id")

        if feature_id:
            return (
                ChatAgent.DIANA.value,
                f"Je wilt stemmen op feature #{feature_id}? Goed idee!\n\n"
                "Ik kan je helpen om te stemmen. Klik op de knop hieronder.",
                ChatActionType.VOTE.value,
                {"feature_id": feature_id},
            )
        else:
            return (
                ChatAgent.DIANA.value,
                "Op welke feature wil je stemmen?\n\n"
                "Geef het feature nummer (bijv. #123) of zoek naar een feature.",
                None,
                None,
            )

    async def _handle_general(
        self,
        message: str,
        session: ChatSession,
    ) -> Tuple[str, str, Optional[str], Optional[Dict[str, Any]]]:
        """Handle general/unclassified message using Diana."""
        response = await self._generate_diana_response(
            template_key="clarification",
            context={},
            custom_message=message,
        )
        return (
            ChatAgent.DIANA.value,
            response,
            None,
            None,
        )

    # ============== DIANA RESPONSE GENERATION ==============

    async def _generate_diana_response(
        self,
        template_key: str,
        context: Dict[str, Any],
        custom_message: Optional[str] = None,
    ) -> str:
        """Generate human-friendly response using Diana agent."""
        provider = self._get_provider(ChatAgent.DIANA.value)

        # Check for template
        template = AGENT_TEMPLATES.get(ChatAgent.DIANA.value, {}).get(template_key)

        if template and not custom_message:
            try:
                return template.format(**context)
            except KeyError:
                pass

        # Generate custom response with LLM
        system_prompt = """Je bent Diana, de documentatie en communicatie agent.
Je genereert vriendelijke, menselijke berichten voor klanten.

Regels:
- Schrijf in informeel Nederlands
- Wees kort en bondig (max 3 zinnen)
- Gebruik emoji's spaarzaam (max 1)
- Wees behulpzaam en positief
- Als je iets niet weet, zeg dat eerlijk"""

        prompt = f"Genereer een vriendelijk antwoord voor deze situatie:\nContext: {context}\nBericht: {custom_message or template_key}"

        request = LLMRequest(
            prompt=prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=200,
            timeout=30,
        )

        response = await provider.generate(request)

        if response.success and response.content:
            return response.content

        # Fallback
        return "Ik begrijp je vraag. Kun je wat specifieker zijn zodat ik je beter kan helpen?"

    # ============== MESSAGE HISTORY ==============

    async def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Get messages for a session."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_message_helpful(
        self,
        message_id: UUID,
        helpful: bool,
        feedback: Optional[str] = None,
    ) -> Optional[ChatMessage]:
        """Mark a message as helpful or not."""
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message:
            message.mark_helpful(helpful, feedback)
            await self.db.commit()
            await self.db.refresh(message)

        return message

    # ============== STATISTICS ==============

    async def get_chatbot_stats(
        self,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get chatbot usage statistics."""
        base_query = select(ChatSession)
        if customer_id:
            base_query = base_query.where(ChatSession.customer_id == customer_id)

        # Total sessions
        result = await self.db.execute(base_query)
        sessions = list(result.scalars().all())

        total_sessions = len(sessions)
        active_sessions = sum(1 for s in sessions if s.is_active())
        closed_sessions = sum(1 for s in sessions if s.status == ChatSessionStatus.CLOSED.value)

        # Calculate averages
        total_messages = sum(s.message_count for s in sessions)
        avg_messages = total_messages / total_sessions if total_sessions > 0 else 0

        # Satisfaction
        rated_sessions = [s for s in sessions if s.satisfaction_rating is not None]
        avg_rating = (
            sum(s.satisfaction_rating for s in rated_sessions) / len(rated_sessions)
            if rated_sessions else 0
        )

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "closed_sessions": closed_sessions,
            "total_messages": total_messages,
            "avg_messages_per_session": round(avg_messages, 2),
            "avg_satisfaction_rating": round(avg_rating, 2),
            "rated_sessions": len(rated_sessions),
        }


# Factory function
def get_portal_chatbot_service(db: AsyncSession) -> PortalChatbotService:
    """Get PortalChatbotService instance."""
    return PortalChatbotService(db)
