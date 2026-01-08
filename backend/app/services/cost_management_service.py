"""
Cost Management Service - Budget tracking and cost control

Week 61: Enhanced Observability Integration

Features:
- Budget configuration per project/agent
- Real-time cost tracking
- Threshold alerts
- Fallback chain management
- Cost optimization recommendations
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from sqlalchemy import func
from sqlalchemy.orm import Session
import logging

from app.models.cctrace import BudgetConfig
from app.models.observability import AgentAction

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Budget alert levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


class CostManagementService:
    """
    Service for managing LLM costs and budgets.

    Provides:
    - Budget configuration (daily, weekly, monthly)
    - Real-time cost tracking
    - Threshold-based alerts
    - Provider fallback recommendations
    - Cost optimization insights
    """

    # Default pricing ($ per million tokens)
    DEFAULT_PRICING = {
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "ollama": {"input": 0.0, "output": 0.0},  # Local = free
        "qwen2.5-coder:7b": {"input": 0.0, "output": 0.0},
        "deepseek-r1": {"input": 0.0, "output": 0.0},
        "codellama": {"input": 0.0, "output": 0.0},
    }

    # Fallback chains (cheaper alternatives)
    FALLBACK_CHAINS = {
        "claude-3-opus": ["claude-3-sonnet", "claude-3-haiku", "ollama"],
        "claude-3-sonnet": ["claude-3-haiku", "ollama"],
        "claude-3-haiku": ["ollama"],
        "gpt-4": ["gpt-4-turbo", "gpt-3.5-turbo", "ollama"],
        "gpt-4-turbo": ["gpt-3.5-turbo", "ollama"],
    }

    def __init__(self, db: Session):
        """Initialize cost management service."""
        self.db = db

    def create_budget(
        self,
        name: str,
        daily_limit: Optional[float] = None,
        weekly_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95,
        project_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        allowed_providers: Optional[List[str]] = None,
        fallback_chain: Optional[List[str]] = None
    ) -> BudgetConfig:
        """
        Create a new budget configuration.

        Args:
            name: Budget name
            daily_limit: Daily spending limit in USD
            weekly_limit: Weekly spending limit in USD
            monthly_limit: Monthly spending limit in USD
            warning_threshold: Warning alert at this % of limit (0-1)
            critical_threshold: Critical alert at this % of limit (0-1)
            project_id: Scope to specific project
            agent_name: Scope to specific agent
            allowed_providers: List of allowed LLM providers
            fallback_chain: Ordered list of fallback providers

        Returns:
            Created BudgetConfig
        """
        config = BudgetConfig(
            name=name,
            daily_limit=daily_limit,
            weekly_limit=weekly_limit,
            monthly_limit=monthly_limit,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            project_id=project_id,
            agent_name=agent_name,
            allowed_providers=allowed_providers or [],
            fallback_chain=fallback_chain or [],
            is_active=True,
        )
        self.db.add(config)
        self.db.commit()
        return config

    def get_budget(self, budget_id: int) -> Optional[BudgetConfig]:
        """Get budget by ID."""
        return self.db.query(BudgetConfig).filter(
            BudgetConfig.id == budget_id
        ).first()

    def get_budgets(
        self,
        project_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[BudgetConfig]:
        """Get budgets with optional filters."""
        query = self.db.query(BudgetConfig)

        if project_id:
            query = query.filter(BudgetConfig.project_id == project_id)
        if agent_name:
            query = query.filter(BudgetConfig.agent_name == agent_name)
        if active_only:
            query = query.filter(BudgetConfig.is_active == True)

        return query.all()

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_created: int = 0,
        cache_read: int = 0
    ) -> float:
        """
        Calculate cost for a request.

        Args:
            model: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens
            cache_created: Tokens written to cache (25% premium)
            cache_read: Tokens read from cache (90% discount)

        Returns:
            Cost in USD
        """
        pricing = self._get_pricing(model)

        # Base cost
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        # Cache adjustments (Claude-specific)
        cache_write_cost = (cache_created / 1_000_000) * pricing["input"] * 1.25
        cache_read_cost = (cache_read / 1_000_000) * pricing["input"] * 0.10

        return input_cost + output_cost + cache_write_cost + cache_read_cost

    def get_current_spend(
        self,
        budget_id: int,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get current spend for a budget period.

        Args:
            budget_id: Budget configuration ID
            period: Period type (daily, weekly, monthly)

        Returns:
            Dict with spend details and alerts
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}

        # Determine time range
        now = datetime.utcnow()
        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            limit = budget.daily_limit
        elif period == "weekly":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            limit = budget.weekly_limit
        else:  # monthly
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            limit = budget.monthly_limit

        # Query costs
        query = self.db.query(
            func.sum(AgentAction.cost).label("total_cost"),
            func.sum(AgentAction.input_tokens).label("input_tokens"),
            func.sum(AgentAction.output_tokens).label("output_tokens"),
            func.count(AgentAction.id).label("action_count"),
        ).filter(
            AgentAction.created_at >= start
        )

        if budget.project_id:
            query = query.filter(AgentAction.project_id == budget.project_id)
        if budget.agent_name:
            query = query.filter(AgentAction.agent_name == budget.agent_name)

        result = query.first()

        total_cost = result.total_cost or 0.0
        input_tokens = result.input_tokens or 0
        output_tokens = result.output_tokens or 0
        action_count = result.action_count or 0

        # Calculate percentages and alerts
        if limit and limit > 0:
            usage_percent = total_cost / limit
            alert_level = self._get_alert_level(
                usage_percent,
                budget.warning_threshold,
                budget.critical_threshold
            )
        else:
            usage_percent = 0
            alert_level = AlertLevel.INFO

        return {
            "budget_id": budget_id,
            "budget_name": budget.name,
            "period": period,
            "period_start": start.isoformat(),
            "current_spend": round(total_cost, 4),
            "limit": limit,
            "usage_percent": round(usage_percent * 100, 2) if limit else None,
            "remaining": round(limit - total_cost, 4) if limit else None,
            "alert_level": alert_level.value,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
            },
            "action_count": action_count,
        }

    def check_budget_available(
        self,
        budget_id: int,
        estimated_cost: float
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Check if budget allows a request.

        Args:
            budget_id: Budget configuration ID
            estimated_cost: Estimated cost of request

        Returns:
            Tuple of (allowed, reason, recommended_fallback)
        """
        budget = self.get_budget(budget_id)
        if not budget or not budget.is_active:
            return (True, "No active budget", None)

        # Check all periods
        for period, limit_attr in [
            ("daily", "daily_limit"),
            ("weekly", "weekly_limit"),
            ("monthly", "monthly_limit"),
        ]:
            limit = getattr(budget, limit_attr)
            if not limit:
                continue

            spend = self.get_current_spend(budget_id, period)
            remaining = spend.get("remaining", float("inf"))

            if remaining < estimated_cost:
                # Budget exceeded - recommend fallback
                fallback = self._get_fallback_recommendation(budget)
                return (
                    False,
                    f"{period.title()} budget would be exceeded. Remaining: ${remaining:.4f}",
                    fallback
                )

        return (True, "Budget available", None)

    def get_cost_breakdown(
        self,
        project_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost breakdown by model and agent.

        Args:
            project_id: Filter by project
            days: Number of days to analyze

        Returns:
            Detailed cost breakdown
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(
            AgentAction.model,
            AgentAction.agent_name,
            func.sum(AgentAction.cost).label("total_cost"),
            func.sum(AgentAction.input_tokens).label("input_tokens"),
            func.sum(AgentAction.output_tokens).label("output_tokens"),
            func.count(AgentAction.id).label("action_count"),
        ).filter(
            AgentAction.created_at >= since
        )

        if project_id:
            query = query.filter(AgentAction.project_id == project_id)

        results = query.group_by(
            AgentAction.model,
            AgentAction.agent_name
        ).all()

        by_model = {}
        by_agent = {}
        total_cost = 0.0

        for row in results:
            cost = row.total_cost or 0.0
            total_cost += cost

            # By model
            model = row.model or "unknown"
            if model not in by_model:
                by_model[model] = {"cost": 0.0, "actions": 0, "tokens": 0}
            by_model[model]["cost"] += cost
            by_model[model]["actions"] += row.action_count or 0
            by_model[model]["tokens"] += (row.input_tokens or 0) + (row.output_tokens or 0)

            # By agent
            agent = row.agent_name or "unknown"
            if agent not in by_agent:
                by_agent[agent] = {"cost": 0.0, "actions": 0, "tokens": 0}
            by_agent[agent]["cost"] += cost
            by_agent[agent]["actions"] += row.action_count or 0
            by_agent[agent]["tokens"] += (row.input_tokens or 0) + (row.output_tokens or 0)

        return {
            "period_days": days,
            "total_cost": round(total_cost, 4),
            "by_model": {k: {**v, "cost": round(v["cost"], 4)} for k, v in by_model.items()},
            "by_agent": {k: {**v, "cost": round(v["cost"], 4)} for k, v in by_agent.items()},
        }

    def get_optimization_recommendations(
        self,
        project_id: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations.

        Args:
            project_id: Filter by project
            days: Days to analyze

        Returns:
            List of optimization recommendations
        """
        recommendations = []
        breakdown = self.get_cost_breakdown(project_id, days)

        # Check for expensive models that could use cheaper alternatives
        for model, data in breakdown["by_model"].items():
            if model in self.FALLBACK_CHAINS and data["cost"] > 1.0:
                fallbacks = self.FALLBACK_CHAINS[model]
                if fallbacks:
                    cheaper = fallbacks[0]
                    cheaper_pricing = self._get_pricing(cheaper)
                    current_pricing = self._get_pricing(model)

                    savings_ratio = (
                        current_pricing["input"] / cheaper_pricing["input"]
                        if cheaper_pricing["input"] > 0 else float("inf")
                    )

                    if savings_ratio > 2:
                        recommendations.append({
                            "type": "model_switch",
                            "current": model,
                            "recommended": cheaper,
                            "current_cost": data["cost"],
                            "potential_savings_percent": round((1 - 1/savings_ratio) * 100, 1),
                            "message": f"Consider using {cheaper} instead of {model} for suitable tasks. "
                                      f"Potential savings: {round((1 - 1/savings_ratio) * 100, 1)}%",
                        })

        # Check for agents with high costs
        high_cost_threshold = breakdown["total_cost"] * 0.5  # 50% of total
        for agent, data in breakdown["by_agent"].items():
            if data["cost"] > high_cost_threshold:
                recommendations.append({
                    "type": "agent_optimization",
                    "agent": agent,
                    "cost": data["cost"],
                    "percent_of_total": round(data["cost"] / breakdown["total_cost"] * 100, 1),
                    "message": f"Agent '{agent}' accounts for {round(data['cost'] / breakdown['total_cost'] * 100, 1)}% "
                              f"of total costs. Consider optimizing prompts or using caching.",
                })

        # Check if local models could be used more
        local_usage = sum(
            data["cost"] for model, data in breakdown["by_model"].items()
            if "ollama" in model.lower() or self._get_pricing(model)["input"] == 0
        )
        cloud_usage = breakdown["total_cost"] - local_usage

        if cloud_usage > local_usage * 3 and cloud_usage > 5.0:
            recommendations.append({
                "type": "local_adoption",
                "cloud_cost": cloud_usage,
                "local_cost": local_usage,
                "message": "Consider using more local models (Ollama) for simple tasks "
                          "to reduce cloud API costs.",
            })

        return recommendations

    def _get_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for model."""
        model_lower = model.lower()
        for key in self.DEFAULT_PRICING:
            if key in model_lower:
                return self.DEFAULT_PRICING[key]
        return self.DEFAULT_PRICING.get("claude-3-sonnet", {"input": 3.0, "output": 15.0})

    def _get_alert_level(
        self,
        usage_percent: float,
        warning_threshold: float,
        critical_threshold: float
    ) -> AlertLevel:
        """Determine alert level from usage percentage."""
        if usage_percent >= 1.0:
            return AlertLevel.EXCEEDED
        elif usage_percent >= critical_threshold:
            return AlertLevel.CRITICAL
        elif usage_percent >= warning_threshold:
            return AlertLevel.WARNING
        return AlertLevel.INFO

    def _get_fallback_recommendation(self, budget: BudgetConfig) -> Optional[str]:
        """Get fallback provider recommendation."""
        if budget.fallback_chain:
            return budget.fallback_chain[0]

        # Try to find from default chains
        if budget.allowed_providers:
            for provider in budget.allowed_providers:
                if provider in self.FALLBACK_CHAINS:
                    fallbacks = self.FALLBACK_CHAINS[provider]
                    for fallback in fallbacks:
                        if fallback in budget.allowed_providers:
                            return fallback

        return "ollama"  # Default to local
