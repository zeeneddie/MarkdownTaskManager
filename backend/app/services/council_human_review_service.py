"""
Council Human Review Service

Week 55: Human-in-the-Loop Council
Orchestrates the 6-phase council process with human validation.

Phases:
1. GENERATION - 3 providers generate content in parallel
2. PEER_REVIEW - Round-robin evaluation
3. ORCHESTRATING - Create consensus document
4. HUMAN_REVIEW - Mark correct items, add missing info
5. FINALIZING - LLM incorporates human feedback
6. APPROVED/REJECTED - Storage & sync
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.council_human_review import (
    CouncilHumanSession,
    CouncilProviderResponse,
    CouncilPeerReview,
    CouncilConsensus,
    DocumentVersion,
    SessionStatus,
    DocumentType
)
from app.services.llm_council_service import LLMCouncilService
from app.services.document_sync_service import DocumentSyncService


class CouncilHumanReviewService:
    """
    Service for Human-in-the-Loop Council workflow.

    Manages the complete 6-phase process from generation through human approval.
    """

    def __init__(self, db: AsyncSession, base_path: Optional[str] = None):
        """
        Initialize the service.

        Args:
            db: SQLAlchemy async database session
            base_path: Base path for document sync
        """
        self.db = db
        self.llm_council = LLMCouncilService(db)
        self.doc_sync = DocumentSyncService(db, base_path)

    # =========================================================================
    # Phase 1: Session Creation & Generation
    # =========================================================================

    async def create_session(
        self,
        document_type: str,
        project_id: Optional[int] = None,
        document_name: Optional[str] = None,
        providers_config: Optional[Dict[str, Any]] = None
    ) -> CouncilHumanSession:
        """
        Create a new council session.

        Args:
            document_type: Type of document to generate
            project_id: Optional project ID
            document_name: Custom name for document
            providers_config: Custom provider configuration

        Returns:
            New CouncilHumanSession
        """
        session = CouncilHumanSession(
            id=uuid4(),
            project_id=project_id,
            document_type=document_type,
            document_name=document_name,
            status=SessionStatus.DRAFT.value,
            providers_config=providers_config or self._default_providers_config()
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    def _default_providers_config(self) -> Dict[str, Any]:
        """Get default provider configuration."""
        return {
            "providers": [
                {"name": "ollama/qwen2.5-coder:7b", "role": "generator"},
                {"name": "claude/sonnet", "role": "generator"},
                {"name": "codex/gpt-5.1-max", "role": "generator"}
            ],
            "orchestrator": "claude/sonnet",
            "timeout_seconds": 120
        }

    async def start_generation(
        self,
        session_id: UUID,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[CouncilProviderResponse]:
        """
        Phase 1: Start parallel generation from all providers.

        Args:
            session_id: Session ID
            prompt: Generation prompt
            context: Additional context for generation

        Returns:
            List of provider responses
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update status
        session.status = SessionStatus.GENERATING.value
        await self.db.commit()

        # Generate from each provider (in production, this would be async)
        responses = []
        providers = session.providers_config.get("providers", [])

        for provider in providers:
            if provider.get("role") != "generator":
                continue

            try:
                # Call LLM Council service for generation
                start_time = datetime.utcnow()
                content = await self._generate_from_provider(
                    provider["name"],
                    prompt,
                    context
                )
                end_time = datetime.utcnow()

                response = CouncilProviderResponse(
                    id=uuid4(),
                    session_id=session_id,
                    provider_name=provider["name"],
                    content=content,
                    generation_time_ms=int((end_time - start_time).total_seconds() * 1000),
                    extra_data={"context": context}
                )

                self.db.add(response)
                responses.append(response)

            except Exception as e:
                # Log error but continue with other providers
                error_response = CouncilProviderResponse(
                    id=uuid4(),
                    session_id=session_id,
                    provider_name=provider["name"],
                    content=f"ERROR: {str(e)}",
                    extra_data={"error": str(e)}
                )
                self.db.add(error_response)
                responses.append(error_response)

        await self.db.commit()

        # Move to peer review if we have responses
        if any(not r.content.startswith("ERROR:") for r in responses):
            session.status = SessionStatus.PEER_REVIEW.value
            await self.db.commit()

        return responses

    async def _generate_from_provider(
        self,
        provider_name: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content from a specific provider."""
        # This would integrate with actual LLM providers
        # For now, return placeholder
        return f"[Generated by {provider_name}]\n\n{prompt}\n\n[Content would be here]"

    # =========================================================================
    # Phase 2: Peer Review
    # =========================================================================

    async def start_peer_review(self, session_id: UUID) -> List[CouncilPeerReview]:
        """
        Phase 2: Start round-robin peer review.

        Each provider reviews all other providers' responses.

        Args:
            session_id: Session ID

        Returns:
            List of peer reviews
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get all responses
        stmt = select(CouncilProviderResponse).where(
            CouncilProviderResponse.session_id == session_id
        )
        result = await self.db.execute(stmt)
        responses = result.scalars().all()

        if len(responses) < 2:
            raise ValueError("Need at least 2 provider responses for peer review")

        reviews = []

        # Each provider reviews all others
        for reviewer_response in responses:
            for reviewed_response in responses:
                if reviewer_response.id == reviewed_response.id:
                    continue  # Don't review yourself

                review = await self._create_peer_review(
                    session_id,
                    reviewer_response.provider_name,
                    reviewed_response
                )
                reviews.append(review)

        await self.db.commit()

        # Move to orchestration phase
        session.status = SessionStatus.ORCHESTRATING.value
        await self.db.commit()

        return reviews

    async def _create_peer_review(
        self,
        session_id: UUID,
        reviewer_provider: str,
        reviewed_response: CouncilProviderResponse
    ) -> CouncilPeerReview:
        """Create a peer review from one provider reviewing another's response."""
        # In production, this would call the reviewer LLM
        # For now, create placeholder review

        review = CouncilPeerReview(
            id=uuid4(),
            session_id=session_id,
            reviewer_provider=reviewer_provider,
            reviewed_provider=reviewed_response.provider_name,
            score=75,  # Placeholder
            strengths=["Clear structure", "Good coverage"],
            weaknesses=["Missing edge cases"],
            suggestions=["Add more examples"],
            consensus_contribution="Keep the main structure, add examples",
            extra_data={"reviewed_content_length": len(reviewed_response.content)}
        )

        self.db.add(review)
        return review

    # =========================================================================
    # Phase 3: Orchestration (Consensus Creation)
    # =========================================================================

    async def create_consensus(
        self,
        session_id: UUID,
        orchestrator_override: Optional[str] = None
    ) -> CouncilConsensus:
        """
        Phase 3: Create consensus document from peer reviews.

        Args:
            session_id: Session ID
            orchestrator_override: Optional custom orchestrator

        Returns:
            Initial consensus document
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get all responses
        stmt = select(CouncilProviderResponse).where(
            CouncilProviderResponse.session_id == session_id
        )
        result = await self.db.execute(stmt)
        responses = result.scalars().all()

        # Get all reviews
        stmt = select(CouncilPeerReview).where(
            CouncilPeerReview.session_id == session_id
        )
        result = await self.db.execute(stmt)
        reviews = result.scalars().all()

        # Synthesize consensus (in production, call orchestrator LLM)
        consensus_content = await self._synthesize_consensus(
            responses,
            reviews,
            orchestrator_override or session.providers_config.get("orchestrator")
        )

        # Create consensus record
        consensus = CouncilConsensus(
            session_id=session_id,
            version=1,
            consensus_content=consensus_content,
            orchestrator_notes=self._generate_orchestrator_notes(reviews)
        )

        self.db.add(consensus)
        await self.db.commit()
        await self.db.refresh(consensus)

        # Move to human review
        session.status = SessionStatus.HUMAN_REVIEW.value
        await self.db.commit()

        return consensus

    async def _synthesize_consensus(
        self,
        responses: List[CouncilProviderResponse],
        reviews: List[CouncilPeerReview],
        orchestrator: str
    ) -> str:
        """Synthesize consensus from responses and reviews."""
        # In production, call orchestrator LLM with all context
        # For now, combine the best parts based on reviews

        # Calculate average score per provider
        provider_scores = {}
        for review in reviews:
            if review.reviewed_provider not in provider_scores:
                provider_scores[review.reviewed_provider] = []
            provider_scores[review.reviewed_provider].append(review.score)

        avg_scores = {
            p: sum(scores) / len(scores)
            for p, scores in provider_scores.items()
        }

        # Get best response
        best_provider = max(avg_scores, key=avg_scores.get) if avg_scores else None
        best_response = next(
            (r for r in responses if r.provider_name == best_provider),
            responses[0] if responses else None
        )

        return f"""# Consensus Document

## Source
Based on synthesis of {len(responses)} provider responses and {len(reviews)} peer reviews.

## Content
{best_response.content if best_response else 'No content available'}

## Peer Review Summary
Average scores: {avg_scores}

## Suggested Improvements
{self._collect_suggestions(reviews)}
"""

    def _generate_orchestrator_notes(self, reviews: List[CouncilPeerReview]) -> str:
        """Generate orchestrator notes from reviews."""
        notes = ["## Orchestrator Notes\n"]

        # Collect all consensus contributions
        contributions = [r.consensus_contribution for r in reviews if r.consensus_contribution]

        notes.append("### Consensus Contributions:")
        for i, contribution in enumerate(contributions, 1):
            notes.append(f"{i}. {contribution}")

        return "\n".join(notes)

    def _collect_suggestions(self, reviews: List[CouncilPeerReview]) -> str:
        """Collect all suggestions from reviews."""
        suggestions = []
        for review in reviews:
            if review.suggestions:
                suggestions.extend(review.suggestions)

        unique_suggestions = list(set(suggestions))
        return "\n".join(f"- {s}" for s in unique_suggestions)

    # =========================================================================
    # Phase 4: Human Review
    # =========================================================================

    async def submit_human_feedback(
        self,
        session_id: UUID,
        feedback: Dict[str, Any],
        marked_correct: Optional[Dict[str, List[str]]] = None,
        conflicts_resolved: Optional[Dict[str, str]] = None,
        additions: Optional[str] = None
    ) -> CouncilConsensus:
        """
        Phase 4: Submit human review feedback.

        Args:
            session_id: Session ID
            feedback: General feedback/corrections
            marked_correct: Items marked correct per provider
            conflicts_resolved: How conflicts were resolved
            additions: What human added that all LLMs missed

        Returns:
            Updated consensus with human feedback
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get latest consensus
        stmt = select(CouncilConsensus).where(
            CouncilConsensus.session_id == session_id
        ).order_by(desc(CouncilConsensus.version))
        result = await self.db.execute(stmt)
        consensus = result.scalars().first()

        if not consensus:
            raise ValueError("No consensus found for session")

        # Update with human feedback
        consensus.human_feedback = feedback
        consensus.human_marked_correct = marked_correct
        consensus.human_conflicts_resolved = conflicts_resolved
        consensus.human_additions = additions

        await self.db.commit()
        await self.db.refresh(consensus)

        # Move to finalizing
        session.status = SessionStatus.FINALIZING.value
        await self.db.commit()

        return consensus

    # =========================================================================
    # Phase 5: Final Synthesis
    # =========================================================================

    async def finalize_consensus(self, session_id: UUID) -> CouncilConsensus:
        """
        Phase 5: LLM incorporates human feedback into final document.

        Args:
            session_id: Session ID

        Returns:
            Final consensus document
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get consensus with human feedback
        stmt = select(CouncilConsensus).where(
            CouncilConsensus.session_id == session_id
        ).order_by(desc(CouncilConsensus.version))
        result = await self.db.execute(stmt)
        current_consensus = result.scalars().first()

        if not current_consensus:
            raise ValueError("No consensus found")

        # Incorporate human feedback (in production, call LLM)
        final_content = await self._incorporate_human_feedback(current_consensus)

        # Create new version with final content
        final_consensus = CouncilConsensus(
            session_id=session_id,
            version=current_consensus.version + 1,
            consensus_content=final_content,
            orchestrator_notes=f"Final version incorporating human feedback from v{current_consensus.version}",
            human_feedback=current_consensus.human_feedback,
            human_marked_correct=current_consensus.human_marked_correct,
            human_conflicts_resolved=current_consensus.human_conflicts_resolved,
            human_additions=current_consensus.human_additions
        )

        self.db.add(final_consensus)
        await self.db.commit()
        await self.db.refresh(final_consensus)

        return final_consensus

    async def _incorporate_human_feedback(self, consensus: CouncilConsensus) -> str:
        """Incorporate human feedback into content."""
        # In production, call LLM with original content + human feedback
        content = consensus.consensus_content

        if consensus.human_additions:
            content += f"\n\n## Human Additions\n{consensus.human_additions}"

        if consensus.human_conflicts_resolved:
            content += f"\n\n## Resolved Conflicts\n"
            for conflict, resolution in consensus.human_conflicts_resolved.items():
                content += f"- **{conflict}**: {resolution}\n"

        return content

    # =========================================================================
    # Phase 6: Approval / Rejection
    # =========================================================================

    async def approve_consensus(
        self,
        session_id: UUID,
        approved_by: str,
        write_to_file: bool = True,
        git_commit: bool = False
    ) -> Dict[str, Any]:
        """
        Phase 6: Approve and optionally write to filesystem.

        Args:
            session_id: Session ID
            approved_by: Who approved
            write_to_file: Write MD file to filesystem
            git_commit: Create Git commit

        Returns:
            Result with file path and optional commit hash
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get final consensus
        stmt = select(CouncilConsensus).where(
            CouncilConsensus.session_id == session_id
        ).order_by(desc(CouncilConsensus.version))
        result = await self.db.execute(stmt)
        consensus = result.scalars().first()

        if not consensus:
            raise ValueError("No consensus found")

        # Mark as approved
        now = datetime.utcnow()
        consensus.is_approved = True
        consensus.approved_at = now

        session.status = SessionStatus.APPROVED.value
        session.approved_at = now
        session.approved_by = approved_by

        await self.db.commit()

        result = {
            "session_id": str(session_id),
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": session.approved_at.isoformat()
        }

        # Write to filesystem if requested
        if write_to_file:
            file_path = await self.doc_sync.write_council_consensus_to_file(session_id)
            if file_path:
                result["file_path"] = str(file_path)

                # Git commit if requested
                if git_commit:
                    commit_hash = await self.doc_sync.git_commit_document(
                        str(file_path.relative_to(self.doc_sync.base_path)),
                        f"docs: {session.document_type} via Council (approved by {approved_by})"
                    )
                    if commit_hash:
                        result["commit_hash"] = commit_hash

        return result

    async def reject_consensus(
        self,
        session_id: UUID,
        rejected_by: str,
        reason: str
    ) -> CouncilHumanSession:
        """
        Phase 6 (alternate): Reject consensus.

        Args:
            session_id: Session ID
            rejected_by: Who rejected
            reason: Rejection reason

        Returns:
            Updated session
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = SessionStatus.REJECTED.value
        session.rejected_at = datetime.utcnow()
        session.rejected_by = rejected_by
        session.rejection_reason = reason

        await self.db.commit()
        await self.db.refresh(session)

        return session

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def _get_session(self, session_id: UUID) -> Optional[CouncilHumanSession]:
        """Get session by ID."""
        stmt = select(CouncilHumanSession).where(
            CouncilHumanSession.id == session_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_session_details(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get full session details including all related data."""
        session = await self._get_session(session_id)
        if not session:
            return None

        # Get responses
        stmt = select(CouncilProviderResponse).where(
            CouncilProviderResponse.session_id == session_id
        )
        result = await self.db.execute(stmt)
        responses = result.scalars().all()

        # Get reviews
        stmt = select(CouncilPeerReview).where(
            CouncilPeerReview.session_id == session_id
        )
        result = await self.db.execute(stmt)
        reviews = result.scalars().all()

        # Get consensus versions
        stmt = select(CouncilConsensus).where(
            CouncilConsensus.session_id == session_id
        ).order_by(CouncilConsensus.version)
        result = await self.db.execute(stmt)
        consensus_versions = result.scalars().all()

        return {
            "session": session.to_dict(),
            "provider_responses": [r.to_dict() for r in responses],
            "peer_reviews": [r.to_dict() for r in reviews],
            "consensus_versions": [c.to_dict() for c in consensus_versions]
        }

    async def list_sessions(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 50
    ) -> List[CouncilHumanSession]:
        """List sessions with optional filters."""
        stmt = select(CouncilHumanSession)

        if project_id is not None:
            stmt = stmt.where(CouncilHumanSession.project_id == project_id)
        if status:
            stmt = stmt.where(CouncilHumanSession.status == status)
        if document_type:
            stmt = stmt.where(CouncilHumanSession.document_type == document_type)

        stmt = stmt.order_by(desc(CouncilHumanSession.created_at)).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_session_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics for council sessions."""
        # Build base filter
        base_filter = []
        if project_id is not None:
            base_filter.append(CouncilHumanSession.project_id == project_id)

        # Count by status
        stmt = select(
            CouncilHumanSession.status,
            func.count(CouncilHumanSession.id)
        ).group_by(CouncilHumanSession.status)
        if base_filter:
            stmt = stmt.where(*base_filter)
        result = await self.db.execute(stmt)
        status_counts = dict(result.all())

        # Count by document type
        stmt = select(
            CouncilHumanSession.document_type,
            func.count(CouncilHumanSession.id)
        ).group_by(CouncilHumanSession.document_type)
        if base_filter:
            stmt = stmt.where(*base_filter)
        result = await self.db.execute(stmt)
        type_counts = dict(result.all())

        # Total count
        stmt = select(func.count(CouncilHumanSession.id))
        if base_filter:
            stmt = stmt.where(*base_filter)
        result = await self.db.execute(stmt)
        total = result.scalar() or 0

        return {
            "total_sessions": total,
            "by_status": status_counts,
            "by_document_type": type_counts,
            "approval_rate": (
                status_counts.get(SessionStatus.APPROVED.value, 0) / total * 100
                if total > 0 else 0
            )
        }
