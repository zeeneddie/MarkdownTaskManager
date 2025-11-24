"""
Attribution Service - Business Logic for Self-Attributing Agents
Week 21-22 Implementation
"""

import json
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, desc, select

from app.models.attribution import (
    TaskOutcome,
    Attribution,
    AttributionFeedback,
    QualityGateStats
)
from app.schemas.attribution import (
    TaskOutcomeInput,
    AttributionResponse,
    AttributionFeedbackResponse,
    AgentPerformanceMetricsResponse,
    AttributionQuery,
    FeedbackQuery,
    AttributionListResponse,
    AttributionSummary,
    AgentSummary,
    OutcomeType,
    ConfidenceLevel,
    CausalFactorType,
    FeedbackType
)


class AttributionService:
    """Service for managing attribution analysis and feedback."""

    def __init__(self, db: AsyncSession, agent_service_url: str = "http://localhost:3001"):
        self.db = db
        self.agent_service_url = agent_service_url

    # =========================================================================
    # Task Outcome Recording
    # =========================================================================

    async def record_task_outcome(self, outcome_input: TaskOutcomeInput) -> TaskOutcome:
        """Record a task outcome for later attribution analysis."""
        task_outcome = TaskOutcome(
            task_id=outcome_input.task_id,
            workflow_id=outcome_input.workflow_id,
            agent_id=outcome_input.agent_id,
            agent_name=outcome_input.agent_name,
            outcome_type=outcome_input.outcome_type.value,
            steps_data=json.dumps([s.model_dump() for s in outcome_input.steps]),
            quality_gate_results=json.dumps([q.model_dump() for q in outcome_input.quality_gate_results]),
            validation_history=json.dumps([v.model_dump() for v in outcome_input.validation_history]),
            duration_ms=outcome_input.duration_ms
        )
        self.db.add(task_outcome)
        await self.db.commit()
        await self.db.refresh(task_outcome)
        return task_outcome

    # =========================================================================
    # Attribution Analysis
    # =========================================================================

    async def analyze_task(self, task_outcome_id: UUID) -> Attribution:
        """Trigger attribution analysis for a recorded task outcome."""
        # Get task outcome
        result = await self.db.execute(
            select(TaskOutcome).where(TaskOutcome.id == task_outcome_id)
        )
        task_outcome = result.scalar_one_or_none()

        if not task_outcome:
            raise ValueError(f"Task outcome {task_outcome_id} not found")

        # Call TypeScript attribution processor via HTTP
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_service_url}/api/attribution/analyze",
                    json={
                        "taskId": task_outcome.task_id,
                        "workflowId": task_outcome.workflow_id,
                        "agentId": task_outcome.agent_id,
                        "agentName": task_outcome.agent_name,
                        "outcome": task_outcome.outcome_type,
                        "steps": json.loads(task_outcome.steps_data or "[]"),
                        "qualityGateResults": json.loads(task_outcome.quality_gate_results or "[]"),
                        "validationHistory": json.loads(task_outcome.validation_history or "[]")
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                attribution_data = response.json()
        except httpx.HTTPError as e:
            # Fallback to local analysis if TypeScript service unavailable
            attribution_data = self._local_analyze(task_outcome)

        # Store attribution result
        attribution = Attribution(
            task_id=task_outcome.task_id,
            workflow_id=task_outcome.workflow_id,
            agent_id=task_outcome.agent_id,
            agent_name=task_outcome.agent_name,
            outcome=attribution_data.get("outcome", task_outcome.outcome_type),
            key_steps=json.dumps(attribution_data.get("keySteps", [])),
            causal_factors=json.dumps(attribution_data.get("causalFactors", [])),
            quality_gate_results=json.dumps(attribution_data.get("qualityGateResults", [])),
            validation_history=json.dumps(attribution_data.get("validationHistory", [])),
            confidence=attribution_data.get("confidence", 0.5),
            confidence_level=attribution_data.get("confidenceLevel", "MEDIUM")
        )
        self.db.add(attribution)
        await self.db.commit()
        await self.db.refresh(attribution)
        return attribution

    def _local_analyze(self, task_outcome: TaskOutcome) -> Dict[str, Any]:
        """Local fallback analysis when TypeScript service is unavailable."""
        steps = json.loads(task_outcome.steps_data or "[]")
        quality_gates = json.loads(task_outcome.quality_gate_results or "[]")
        validations = json.loads(task_outcome.validation_history or "[]")

        # Simple local analysis
        key_steps = []
        for step in steps:
            impact_score = 0.3 if step.get("succeeded") else -0.5
            if step.get("experience_consulted") and step.get("succeeded"):
                impact_score += 0.2
            if step.get("retry_count", 0) > 0:
                impact_score -= step.get("retry_count", 0) * 0.1

            key_steps.append({
                "stepId": step.get("id"),
                "stepName": step.get("name"),
                "agentId": step.get("agent_id"),
                "impact": "IMPORTANT" if abs(impact_score) > 0.3 else "MINOR",
                "impactScore": max(-1, min(1, impact_score)),
                "reasoning": "Local analysis - TypeScript service unavailable",
                "duration": step.get("duration", 0),
                "retryCount": step.get("retry_count", 0),
                "experienceUsed": step.get("experience_consulted", False),
                "patternApplied": step.get("pattern_used")
            })

        # Extract causal factors
        causal_factors = []
        experience_steps = [s for s in steps if s.get("experience_consulted")]
        if experience_steps:
            causal_factors.append({
                "factorId": f"factor_{datetime.now().timestamp()}_exp",
                "factorType": "PATTERN_REUSE",
                "description": f"Experience consulted in {len(experience_steps)} steps",
                "contribution": 0.3 if task_outcome.outcome_type == "SUCCESS" else 0.1,
                "evidence": [s.get("name") for s in experience_steps],
                "relatedSteps": [s.get("id") for s in experience_steps]
            })

        # Calculate confidence
        confidence = 0.5
        confidence += min(0.2, len(steps) * 0.02)
        confidence += min(0.15, len(causal_factors) * 0.03)
        if task_outcome.outcome_type != "PARTIAL":
            confidence += 0.1

        return {
            "outcome": task_outcome.outcome_type,
            "keySteps": key_steps,
            "causalFactors": causal_factors,
            "qualityGateResults": quality_gates,
            "validationHistory": validations,
            "confidence": min(1, confidence),
            "confidenceLevel": "HIGH" if confidence >= 0.8 else "MEDIUM" if confidence >= 0.5 else "LOW"
        }

    # =========================================================================
    # Feedback Generation
    # =========================================================================

    async def generate_feedback(self, attribution_id: UUID) -> AttributionFeedback:
        """Generate feedback for an agent based on attribution analysis."""
        result = await self.db.execute(
            select(Attribution).where(Attribution.id == attribution_id)
        )
        attribution = result.scalar_one_or_none()

        if not attribution:
            raise ValueError(f"Attribution {attribution_id} not found")

        # Try TypeScript service first
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_service_url}/api/attribution/feedback",
                    json={
                        "attributionId": str(attribution.id),
                        "agentId": attribution.agent_id,
                        "outcome": attribution.outcome,
                        "keySteps": json.loads(attribution.key_steps or "[]"),
                        "causalFactors": json.loads(attribution.causal_factors or "[]"),
                        "confidence": attribution.confidence
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                feedback_data = response.json()
        except httpx.HTTPError:
            # Fallback to local feedback generation
            feedback_data = self._local_generate_feedback(attribution)

        # Store feedback
        feedback = AttributionFeedback(
            attribution_id=attribution.id,
            agent_id=attribution.agent_id,
            feedback_type=feedback_data.get("feedbackType", "PATTERN_UPDATE"),
            lessons=json.dumps(feedback_data.get("lessons", [])),
            recommended_adjustments=json.dumps(feedback_data.get("recommendedAdjustments", [])),
            delivered=False
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    def _local_generate_feedback(self, attribution: Attribution) -> Dict[str, Any]:
        """Local fallback feedback generation."""
        key_steps = json.loads(attribution.key_steps or "[]")
        causal_factors = json.loads(attribution.causal_factors or "[]")

        lessons = []
        adjustments = []

        # Extract lessons from successful patterns
        successful_patterns = [s for s in key_steps if s.get("impactScore", 0) > 0.2 and s.get("patternApplied")]
        for step in successful_patterns[:3]:
            lessons.append({
                "lessonId": f"lesson_{datetime.now().timestamp()}",
                "lessonType": "DO_MORE",
                "description": f"Pattern '{step.get('patternApplied')}' was effective",
                "context": step.get("reasoning", ""),
                "confidence": abs(step.get("impactScore", 0))
            })

        # Extract lessons from failures
        failed_steps = [s for s in key_steps if s.get("impactScore", 0) < -0.2]
        for step in failed_steps[:3]:
            lessons.append({
                "lessonId": f"lesson_{datetime.now().timestamp()}",
                "lessonType": "AVOID",
                "description": f"Step '{step.get('stepName')}' caused issues",
                "context": step.get("reasoning", ""),
                "confidence": abs(step.get("impactScore", 0))
            })

        # Recommend adjustments
        experience_helpful = len([s for s in key_steps if s.get("experienceUsed") and s.get("impactScore", 0) > 0])
        if experience_helpful > 2:
            adjustments.append({
                "adjustmentType": "WEIGHT_UPDATE",
                "target": "experienceWeight",
                "currentValue": "0.5",
                "recommendedValue": "0.7",
                "reasoning": f"Experience consultation was helpful in {experience_helpful} steps"
            })

        return {
            "feedbackType": "SUCCESS_REINFORCEMENT" if attribution.outcome == "SUCCESS" else "FAILURE_CORRECTION",
            "lessons": lessons,
            "recommendedAdjustments": adjustments
        }

    async def deliver_feedback(self, feedback_id: UUID) -> bool:
        """Deliver feedback to the agent's experience store."""
        result = await self.db.execute(
            select(AttributionFeedback).where(AttributionFeedback.id == feedback_id)
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")

        # Send to agent service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_service_url}/api/attribution/deliver-feedback",
                    json={
                        "feedbackId": str(feedback.id),
                        "agentId": feedback.agent_id,
                        "feedbackType": feedback.feedback_type,
                        "lessons": json.loads(feedback.lessons or "[]"),
                        "adjustments": json.loads(feedback.recommended_adjustments or "[]")
                    },
                    timeout=30.0
                )
                response.raise_for_status()

                # Mark as delivered
                feedback.delivered = True
                feedback.delivered_at = datetime.now()
                await self.db.commit()
                return True
        except httpx.HTTPError as e:
            print(f"Failed to deliver feedback: {e}")
            return False

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def get_attribution(self, attribution_id: UUID) -> Optional[Attribution]:
        """Get a single attribution by ID."""
        result = await self.db.execute(
            select(Attribution).where(Attribution.id == attribution_id)
        )
        return result.scalar_one_or_none()

    async def list_attributions(self, query: AttributionQuery) -> AttributionListResponse:
        """List attributions with filtering and pagination."""
        stmt = select(Attribution)

        if query.agent_id:
            stmt = stmt.where(Attribution.agent_id == query.agent_id)
        if query.workflow_id:
            stmt = stmt.where(Attribution.workflow_id == query.workflow_id)
        if query.outcome:
            stmt = stmt.where(Attribution.outcome == query.outcome.value)
        if query.min_confidence:
            stmt = stmt.where(Attribution.confidence >= query.min_confidence)
        if query.start_date:
            stmt = stmt.where(Attribution.created_at >= query.start_date)
        if query.end_date:
            stmt = stmt.where(Attribution.created_at <= query.end_date)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        pages = (total + query.page_size - 1) // query.page_size

        # Get paginated items
        stmt = stmt.order_by(desc(Attribution.created_at)).offset(
            (query.page - 1) * query.page_size
        ).limit(query.page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return AttributionListResponse(
            items=[self._attribution_to_response(a) for a in items],
            total=total,
            page=query.page,
            page_size=query.page_size,
            pages=pages
        )

    def _attribution_to_response(self, attribution: Attribution) -> AttributionResponse:
        """Convert Attribution model to response schema."""
        return AttributionResponse(
            id=str(attribution.id),
            task_id=attribution.task_id,
            workflow_id=attribution.workflow_id,
            agent_id=attribution.agent_id,
            agent_name=attribution.agent_name,
            outcome=OutcomeType(attribution.outcome),
            key_steps=json.loads(attribution.key_steps or "[]"),
            causal_factors=json.loads(attribution.causal_factors or "[]"),
            quality_gate_results=json.loads(attribution.quality_gate_results or "[]"),
            validation_history=json.loads(attribution.validation_history or "[]"),
            confidence=attribution.confidence,
            confidence_level=ConfidenceLevel(attribution.confidence_level),
            created_at=attribution.created_at,
            analyzed_at=attribution.analyzed_at
        )

    async def get_feedback(self, feedback_id: UUID) -> Optional[AttributionFeedback]:
        """Get a single feedback by ID."""
        result = await self.db.execute(
            select(AttributionFeedback).where(AttributionFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def list_pending_feedback(self, agent_id: Optional[str] = None) -> List[AttributionFeedback]:
        """List undelivered feedback."""
        stmt = select(AttributionFeedback).where(AttributionFeedback.delivered == False)
        if agent_id:
            stmt = stmt.where(AttributionFeedback.agent_id == agent_id)
        stmt = stmt.order_by(AttributionFeedback.created_at)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # Analytics & Metrics
    # =========================================================================

    async def get_agent_metrics(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AgentPerformanceMetricsResponse:
        """Get performance metrics for an agent."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        stmt = select(Attribution).where(
            and_(
                Attribution.agent_id == agent_id,
                Attribution.created_at >= start_date,
                Attribution.created_at <= end_date
            )
        )
        result = await self.db.execute(stmt)
        attributions = list(result.scalars().all())

        if not attributions:
            return AgentPerformanceMetricsResponse(
                agent_id=agent_id,
                agent_name="Unknown",
                period_start=start_date,
                period_end=end_date,
                total_tasks=0,
                successful_tasks=0,
                failed_tasks=0,
                partial_tasks=0,
                success_rate=0.0,
                average_confidence=0.0,
                top_success_factors=[],
                top_failure_patterns=[],
                quality_gate_effectiveness=[],
                improvement_trend=0.0
            )

        # Calculate metrics
        total = len(attributions)
        successful = len([a for a in attributions if a.outcome == "SUCCESS"])
        failed = len([a for a in attributions if a.outcome == "FAILURE"])
        partial = len([a for a in attributions if a.outcome == "PARTIAL"])
        avg_confidence = sum(a.confidence for a in attributions) / total

        # Extract top factors
        success_factors = {}
        failure_factors = {}
        for attr in attributions:
            factors = json.loads(attr.causal_factors or "[]")
            for factor in factors:
                factor_type = factor.get("factorType")
                contribution = factor.get("contribution", 0)
                if contribution > 0:
                    if factor_type not in success_factors:
                        success_factors[factor_type] = {"count": 0, "total": 0}
                    success_factors[factor_type]["count"] += 1
                    success_factors[factor_type]["total"] += contribution
                else:
                    if factor_type not in failure_factors:
                        failure_factors[factor_type] = {"count": 0, "total": 0}
                    failure_factors[factor_type]["count"] += 1
                    failure_factors[factor_type]["total"] += abs(contribution)

        top_success = sorted(
            [
                {
                    "factor": k,
                    "description": k.replace("_", " ").title(),
                    "frequency": v["count"],
                    "average_contribution": v["total"] / v["count"],
                    "rank": 0
                }
                for k, v in success_factors.items()
            ],
            key=lambda x: x["average_contribution"],
            reverse=True
        )[:5]
        for i, f in enumerate(top_success):
            f["rank"] = i + 1

        top_failure = sorted(
            [
                {
                    "factor": k,
                    "description": k.replace("_", " ").title(),
                    "frequency": v["count"],
                    "average_contribution": -v["total"] / v["count"],
                    "rank": 0
                }
                for k, v in failure_factors.items()
            ],
            key=lambda x: abs(x["average_contribution"]),
            reverse=True
        )[:5]
        for i, f in enumerate(top_failure):
            f["rank"] = i + 1

        # Calculate trend (compare last 7 days to previous 7 days)
        recent = [a for a in attributions if a.created_at >= end_date - timedelta(days=7)]
        older = [a for a in attributions if a.created_at < end_date - timedelta(days=7)]

        recent_success = len([a for a in recent if a.outcome == "SUCCESS"]) / max(1, len(recent))
        older_success = len([a for a in older if a.outcome == "SUCCESS"]) / max(1, len(older))
        trend = recent_success - older_success

        return AgentPerformanceMetricsResponse(
            agent_id=agent_id,
            agent_name=attributions[0].agent_name if attributions else "Unknown",
            period_start=start_date,
            period_end=end_date,
            total_tasks=total,
            successful_tasks=successful,
            failed_tasks=failed,
            partial_tasks=partial,
            success_rate=successful / total if total > 0 else 0,
            average_confidence=avg_confidence,
            top_success_factors=top_success,
            top_failure_patterns=top_failure,
            quality_gate_effectiveness=[],
            improvement_trend=trend
        )

    async def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AttributionSummary:
        """Get overall attribution summary."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        base_filter = and_(
            Attribution.created_at >= start_date,
            Attribution.created_at <= end_date
        )

        # Total count
        count_stmt = select(func.count()).select_from(Attribution).where(base_filter)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Success count
        success_stmt = select(func.count()).select_from(Attribution).where(
            and_(base_filter, Attribution.outcome == "SUCCESS")
        )
        success_count = (await self.db.execute(success_stmt)).scalar() or 0

        # Failure count
        failure_stmt = select(func.count()).select_from(Attribution).where(
            and_(base_filter, Attribution.outcome == "FAILURE")
        )
        failure_count = (await self.db.execute(failure_stmt)).scalar() or 0

        # Partial count
        partial_stmt = select(func.count()).select_from(Attribution).where(
            and_(base_filter, Attribution.outcome == "PARTIAL")
        )
        partial_count = (await self.db.execute(partial_stmt)).scalar() or 0

        # Average confidence
        avg_stmt = select(func.avg(Attribution.confidence)).where(base_filter)
        avg_confidence = (await self.db.execute(avg_stmt)).scalar() or 0

        return AttributionSummary(
            total_attributions=total,
            success_count=success_count,
            failure_count=failure_count,
            partial_count=partial_count,
            average_confidence=float(avg_confidence),
            top_success_factor=None,
            top_failure_factor=None
        )

    async def get_agent_summaries(self) -> List[AgentSummary]:
        """Get summary for all agents."""
        # Get unique agents
        stmt = select(Attribution.agent_id, Attribution.agent_name).distinct()
        result = await self.db.execute(stmt)
        agents = result.all()

        summaries = []
        for agent_id, agent_name in agents:
            # Count attributions by outcome
            attr_stmt = select(Attribution).where(Attribution.agent_id == agent_id)
            attr_result = await self.db.execute(attr_stmt)
            attrs = list(attr_result.scalars().all())

            total = len(attrs)
            success = len([a for a in attrs if a.outcome == "SUCCESS"])
            failure = len([a for a in attrs if a.outcome == "FAILURE"])
            partial = len([a for a in attrs if a.outcome == "PARTIAL"])
            avg_conf = sum(a.confidence for a in attrs) / total if total > 0 else 0

            # Count pending feedback
            fb_stmt = select(func.count()).select_from(AttributionFeedback).where(
                and_(
                    AttributionFeedback.agent_id == agent_id,
                    AttributionFeedback.delivered == False
                )
            )
            pending = (await self.db.execute(fb_stmt)).scalar() or 0

            summaries.append(AgentSummary(
                agent_id=agent_id,
                agent_name=agent_name or "Unknown",
                total_attributions=total,
                success_count=success,
                failure_count=failure,
                partial_count=partial,
                average_confidence=avg_conf,
                pending_feedback=pending
            ))

        return summaries
