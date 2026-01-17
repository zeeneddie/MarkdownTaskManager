"""
Observability Service - Agent Action Logging & Performance Tracking

Week 54: Core observability functionality for multi-LLM agent monitoring.
Tracks every agent action, decision point, and aggregates daily performance.
"""

from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import (
    LLMProvider,
    AgentAction,
    DecisionTrace,
    AgentPerformanceDaily,
)


class ObservabilityService:
    """
    Central service for agent observability.

    Provides:
    - Action logging for every agent operation
    - Decision trace recording for debugging
    - Daily performance aggregation
    - Provider health monitoring
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== PROVIDER MANAGEMENT ====================

    async def get_all_providers(self) -> List[LLMProvider]:
        """Get all registered LLM providers."""
        result = await self.db.execute(
            select(LLMProvider).order_by(LLMProvider.tier, LLMProvider.name)
        )
        return list(result.scalars().all())

    async def get_active_providers(self) -> List[LLMProvider]:
        """Get only active providers."""
        result = await self.db.execute(
            select(LLMProvider)
            .where(LLMProvider.is_active == True)
            .order_by(LLMProvider.tier, LLMProvider.name)
        )
        return list(result.scalars().all())

    async def get_provider_by_name(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by its unique name."""
        result = await self.db.execute(
            select(LLMProvider).where(LLMProvider.name == name)
        )
        return result.scalar_one_or_none()

    async def get_providers_by_tier(self, tier: str) -> List[LLMProvider]:
        """Get providers filtered by tier (free, fast, balanced, deep)."""
        result = await self.db.execute(
            select(LLMProvider)
            .where(and_(
                LLMProvider.tier == tier,
                LLMProvider.is_active == True
            ))
            .order_by(LLMProvider.name)
        )
        return list(result.scalars().all())

    async def update_provider_status(
        self,
        name: str,
        is_active: bool
    ) -> Optional[LLMProvider]:
        """Enable or disable a provider."""
        provider = await self.get_provider_by_name(name)
        if provider:
            provider.is_active = is_active
            provider.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(provider)
        return provider

    # ==================== ACTION LOGGING ====================

    async def log_action(
        self,
        agent_id: str,
        action_type: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        task_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        input_summary: Optional[str] = None,
        output_summary: Optional[str] = None,
        decision_rationale: Optional[str] = None,
        token_input: int = 0,
        token_output: int = 0,
        duration_ms: int = 0,
        cost_cents: float = 0.0,
        success: bool = True,
        error: Optional[str] = None,
        confidence_score: Optional[float] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> AgentAction:
        """
        Log an agent action.

        This is the primary method for recording agent operations.
        Should be called for every significant agent action.
        """
        action = AgentAction(
            task_id=task_id,
            session_id=session_id or uuid4(),
            agent_id=agent_id,
            action_type=action_type,
            provider=provider,
            model=model,
            input_summary=self._truncate(input_summary, 1000),
            output_summary=self._truncate(output_summary, 2000),
            decision_rationale=decision_rationale,
            token_input=token_input,
            token_output=token_output,
            duration_ms=duration_ms,
            cost_cents=Decimal(str(cost_cents)),
            success=success,
            error=error,
            confidence_score=Decimal(str(confidence_score)) if confidence_score else None,
            extra_data=extra_data or {},
        )

        self.db.add(action)
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def get_recent_actions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> List[AgentAction]:
        """Get recent agent actions with optional filtering."""
        query = select(AgentAction)

        conditions = []
        if agent_id:
            conditions.append(AgentAction.agent_id == agent_id)
        if since:
            conditions.append(AgentAction.created_at >= since)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AgentAction.created_at)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_actions_by_task(self, task_id: UUID) -> List[AgentAction]:
        """Get all actions for a specific task."""
        result = await self.db.execute(
            select(AgentAction)
            .where(AgentAction.task_id == task_id)
            .order_by(AgentAction.created_at)
        )
        return list(result.scalars().all())

    async def get_actions_by_session(self, session_id: UUID) -> List[AgentAction]:
        """Get all actions in a session."""
        result = await self.db.execute(
            select(AgentAction)
            .where(AgentAction.session_id == session_id)
            .order_by(AgentAction.created_at)
        )
        return list(result.scalars().all())

    # ==================== DECISION TRACING ====================

    async def log_decision(
        self,
        agent_id: str,
        decision_point: str,
        task_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        selected_option: Optional[str] = None,
        selection_rationale: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_details: Optional[Dict[str, Any]] = None,
    ) -> DecisionTrace:
        """
        Log a decision point for debugging and analysis.

        Decision points include:
        - model_selection: Which LLM to use
        - quality_gate: Pass/fail decisions
        - routing: Workflow routing decisions
        - retry: Retry vs escalate decisions
        """
        # Get sequence number for this task
        sequence = 1
        if task_id:
            result = await self.db.execute(
                select(func.max(DecisionTrace.sequence_number))
                .where(DecisionTrace.task_id == task_id)
            )
            max_seq = result.scalar()
            if max_seq is not None:
                sequence = max_seq + 1

        trace = DecisionTrace(
            task_id=task_id,
            session_id=session_id or uuid4(),
            sequence_number=sequence,
            agent_id=agent_id,
            decision_point=decision_point,
            options=options,
            selected_option=selected_option,
            selection_rationale=selection_rationale,
            outcome=outcome,
            outcome_details=outcome_details,
        )

        self.db.add(trace)
        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def get_decision_trace(self, task_id: UUID) -> List[DecisionTrace]:
        """Get the full decision trace for a task."""
        result = await self.db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.task_id == task_id)
            .order_by(DecisionTrace.sequence_number)
        )
        return list(result.scalars().all())

    # ==================== PERFORMANCE AGGREGATION ====================

    async def aggregate_daily_performance(
        self,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Aggregate daily performance metrics from agent actions.

        Should be run daily (via cron or scheduled task) to pre-compute
        performance summaries for fast dashboard queries.
        """
        target_date = target_date or date.today()
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

        # Get aggregated stats per agent per provider
        result = await self.db.execute(
            select(
                AgentAction.agent_id,
                AgentAction.provider,
                func.count(AgentAction.id).label('total_actions'),
                func.sum(func.cast(AgentAction.success, sa.Integer)).label('successful_actions'),
                func.avg(AgentAction.duration_ms).label('avg_duration_ms'),
                func.sum(AgentAction.token_input).label('total_tokens_input'),
                func.sum(AgentAction.token_output).label('total_tokens_output'),
                func.sum(AgentAction.cost_cents).label('total_cost_cents'),
                func.avg(AgentAction.confidence_score).label('avg_confidence'),
            )
            .where(and_(
                AgentAction.created_at >= start_dt,
                AgentAction.created_at < end_dt
            ))
            .group_by(AgentAction.agent_id, AgentAction.provider)
        )

        stats = []
        for row in result.all():
            # Upsert daily performance record
            existing = await self.db.execute(
                select(AgentPerformanceDaily)
                .where(and_(
                    AgentPerformanceDaily.agent_id == row.agent_id,
                    AgentPerformanceDaily.provider == row.provider,
                    AgentPerformanceDaily.date == target_date
                ))
            )
            perf = existing.scalar_one_or_none()

            if perf:
                # Update existing
                perf.total_actions = row.total_actions
                perf.successful_actions = row.successful_actions or 0
                perf.failed_actions = row.total_actions - (row.successful_actions or 0)
                perf.avg_duration_ms = int(row.avg_duration_ms or 0)
                perf.total_tokens_input = row.total_tokens_input or 0
                perf.total_tokens_output = row.total_tokens_output or 0
                perf.total_cost_cents = Decimal(str(row.total_cost_cents or 0))
                perf.avg_confidence = Decimal(str(row.avg_confidence)) if row.avg_confidence else None
                perf.updated_at = datetime.now(timezone.utc)
            else:
                # Create new
                perf = AgentPerformanceDaily(
                    agent_id=row.agent_id,
                    provider=row.provider,
                    date=target_date,
                    total_actions=row.total_actions,
                    successful_actions=row.successful_actions or 0,
                    failed_actions=row.total_actions - (row.successful_actions or 0),
                    avg_duration_ms=int(row.avg_duration_ms or 0),
                    total_tokens_input=row.total_tokens_input or 0,
                    total_tokens_output=row.total_tokens_output or 0,
                    total_cost_cents=Decimal(str(row.total_cost_cents or 0)),
                    avg_confidence=Decimal(str(row.avg_confidence)) if row.avg_confidence else None,
                )
                self.db.add(perf)

            stats.append({
                "agent_id": row.agent_id,
                "provider": row.provider,
                "total_actions": row.total_actions,
                "successful_actions": row.successful_actions or 0,
            })

        await self.db.commit()

        return {
            "date": target_date.isoformat(),
            "agents_processed": len(stats),
            "stats": stats,
        }

    async def get_daily_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        agent_id: Optional[str] = None,
    ) -> List[AgentPerformanceDaily]:
        """Get daily performance records with optional filtering."""
        query = select(AgentPerformanceDaily)

        conditions = []
        if start_date:
            conditions.append(AgentPerformanceDaily.date >= start_date)
        if end_date:
            conditions.append(AgentPerformanceDaily.date <= end_date)
        if agent_id:
            conditions.append(AgentPerformanceDaily.agent_id == agent_id)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AgentPerformanceDaily.date))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== STATISTICS ====================

    async def get_agent_statistics(
        self,
        agent_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get comprehensive statistics for an agent."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Recent actions
        result = await self.db.execute(
            select(
                func.count(AgentAction.id).label('total_actions'),
                func.sum(func.cast(AgentAction.success, sa.Integer)).label('successful'),
                func.avg(AgentAction.duration_ms).label('avg_duration'),
                func.sum(AgentAction.token_input + AgentAction.token_output).label('total_tokens'),
                func.sum(AgentAction.cost_cents).label('total_cost'),
            )
            .where(and_(
                AgentAction.agent_id == agent_id,
                AgentAction.created_at >= since
            ))
        )
        stats = result.one()

        # Provider breakdown
        provider_result = await self.db.execute(
            select(
                AgentAction.provider,
                func.count(AgentAction.id).label('count')
            )
            .where(and_(
                AgentAction.agent_id == agent_id,
                AgentAction.created_at >= since
            ))
            .group_by(AgentAction.provider)
        )
        provider_breakdown = {
            row.provider: row.count
            for row in provider_result.all()
            if row.provider
        }

        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_actions": stats.total_actions or 0,
            "successful_actions": stats.successful or 0,
            "success_rate": (
                (stats.successful / stats.total_actions * 100)
                if stats.total_actions else 0
            ),
            "avg_duration_ms": int(stats.avg_duration or 0),
            "total_tokens": stats.total_tokens or 0,
            "total_cost_cents": float(stats.total_cost or 0),
            "provider_breakdown": provider_breakdown,
        }

    async def get_platform_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get platform-wide statistics."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Overall stats
        result = await self.db.execute(
            select(
                func.count(AgentAction.id).label('total_actions'),
                func.sum(func.cast(AgentAction.success, sa.Integer)).label('successful'),
                func.count(func.distinct(AgentAction.agent_id)).label('active_agents'),
                func.sum(AgentAction.cost_cents).label('total_cost'),
            )
            .where(AgentAction.created_at >= since)
        )
        stats = result.one()

        # Top agents
        top_agents_result = await self.db.execute(
            select(
                AgentAction.agent_id,
                func.count(AgentAction.id).label('action_count')
            )
            .where(AgentAction.created_at >= since)
            .group_by(AgentAction.agent_id)
            .order_by(desc(func.count(AgentAction.id)))
            .limit(5)
        )
        top_agents = [
            {"agent_id": row.agent_id, "actions": row.action_count}
            for row in top_agents_result.all()
        ]

        return {
            "period_days": days,
            "total_actions": stats.total_actions or 0,
            "successful_actions": stats.successful or 0,
            "success_rate": (
                (stats.successful / stats.total_actions * 100)
                if stats.total_actions else 0
            ),
            "active_agents": stats.active_agents or 0,
            "total_cost_cents": float(stats.total_cost or 0),
            "top_agents": top_agents,
        }

    # ==================== HELPERS ====================

    def _truncate(self, text: Optional[str], max_length: int) -> Optional[str]:
        """Truncate text to max length for storage."""
        if text is None:
            return None
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


# Import sqlalchemy for type hint in aggregate query
import sqlalchemy as sa
