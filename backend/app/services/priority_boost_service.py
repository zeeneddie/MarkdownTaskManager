# backend/app/services/priority_boost_service.py
"""
Priority Boost Service - Week 118

Manages customer priority boosts for feature requests.
- Monthly allowance tracking per customer tier
- Boost usage and expiration
- Priority recalculation
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.portal_enhancements import (
    BoostAllowance,
    PriorityBoost,
    CustomerTier,
    BoostStatus,
)


class PriorityBoostService:
    """Service for managing priority boosts."""

    # Boost configuration
    BOOST_DURATION_DAYS = 30  # How long a boost remains active
    PRIORITY_LEVELS = ["P0", "P1", "P2", "P3", "P4"]  # P0 = highest

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_allowance(
        self,
        customer_id: str,
        tier: str = CustomerTier.STANDARD.value,
    ) -> BoostAllowance:
        """Get or create monthly boost allowance for customer."""
        # Calculate current period (monthly)
        today = date.today()
        period_start = today.replace(day=1)
        if today.month == 12:
            period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # Check for existing allowance
        result = await self.db.execute(
            select(BoostAllowance).where(
                and_(
                    BoostAllowance.customer_id == customer_id,
                    BoostAllowance.period_start == period_start,
                )
            )
        )
        allowance = result.scalar_one_or_none()

        if allowance:
            return allowance

        # Create new allowance
        quota = BoostAllowance.get_tier_quota(tier)
        allowance = BoostAllowance(
            id=uuid4(),
            customer_id=customer_id,
            period_start=period_start,
            period_end=period_end,
            total_boosts=quota,
            used_boosts=0,
            remaining_boosts=quota,
            tier=tier,
        )
        self.db.add(allowance)
        await self.db.commit()
        await self.db.refresh(allowance)
        return allowance

    async def get_allowance_status(self, customer_id: str) -> Dict[str, Any]:
        """Get current boost allowance status for customer."""
        allowance = await self.get_or_create_allowance(customer_id)

        # Get active boosts
        result = await self.db.execute(
            select(PriorityBoost).where(
                and_(
                    PriorityBoost.customer_id == customer_id,
                    PriorityBoost.status == BoostStatus.ACTIVE.value,
                )
            )
        )
        active_boosts = result.scalars().all()

        return {
            "customer_id": customer_id,
            "tier": allowance.tier,
            "period": {
                "start": allowance.period_start.isoformat(),
                "end": allowance.period_end.isoformat(),
            },
            "quota": {
                "total": allowance.total_boosts,
                "used": allowance.used_boosts,
                "remaining": allowance.remaining_boosts,
            },
            "can_boost": allowance.remaining_boosts > 0,
            "active_boosts": [
                {
                    "id": str(b.id),
                    "feature_id": b.feature_request_id,
                    "feature_title": b.feature_title,
                    "created_at": b.created_at.isoformat(),
                    "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                }
                for b in active_boosts
            ],
        }

    async def use_boost(
        self,
        customer_id: str,
        feature_request_id: int,
        feature_title: Optional[str] = None,
        current_priority: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Use a boost on a feature request."""
        # Get allowance
        allowance = await self.get_or_create_allowance(customer_id)

        if not allowance.can_boost():
            return {
                "success": False,
                "error": "no_boosts_remaining",
                "message": f"No boosts remaining. You have used {allowance.used_boosts}/{allowance.total_boosts} boosts this period.",
                "next_reset": allowance.period_end.isoformat(),
            }

        # Check if feature already boosted
        result = await self.db.execute(
            select(PriorityBoost).where(
                and_(
                    PriorityBoost.feature_request_id == feature_request_id,
                    PriorityBoost.customer_id == customer_id,
                    PriorityBoost.status == BoostStatus.ACTIVE.value,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return {
                "success": False,
                "error": "already_boosted",
                "message": "This feature is already boosted.",
                "boost_id": str(existing.id),
            }

        # Calculate new priority
        boosted_priority = self._calculate_boosted_priority(current_priority)

        # Use the boost
        allowance.use_boost()

        # Create boost record
        boost = PriorityBoost(
            id=uuid4(),
            allowance_id=allowance.id,
            feature_request_id=feature_request_id,
            feature_title=feature_title,
            customer_id=customer_id,
            reason=reason,
            original_priority=current_priority,
            boosted_priority=boosted_priority,
            priority_delta=1,
            status=BoostStatus.ACTIVE.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.BOOST_DURATION_DAYS),
        )
        self.db.add(boost)
        await self.db.commit()
        await self.db.refresh(boost)

        return {
            "success": True,
            "boost_id": str(boost.id),
            "feature_request_id": feature_request_id,
            "original_priority": current_priority,
            "boosted_priority": boosted_priority,
            "expires_at": boost.expires_at.isoformat(),
            "remaining_boosts": allowance.remaining_boosts,
            "message": f"Feature priority boosted from {current_priority or 'unset'} to {boosted_priority}",
        }

    def _calculate_boosted_priority(self, current: Optional[str]) -> str:
        """Calculate new priority after boost (move up one level)."""
        if not current or current not in self.PRIORITY_LEVELS:
            return "P2"  # Default to P2 if unknown

        current_index = self.PRIORITY_LEVELS.index(current)
        new_index = max(0, current_index - 1)  # Move up (lower number = higher priority)
        return self.PRIORITY_LEVELS[new_index]

    async def get_boost_history(
        self,
        customer_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get boost history for customer."""
        result = await self.db.execute(
            select(PriorityBoost)
            .where(PriorityBoost.customer_id == customer_id)
            .order_by(PriorityBoost.created_at.desc())
            .limit(limit)
        )
        boosts = result.scalars().all()

        return [
            {
                "id": str(b.id),
                "feature_request_id": b.feature_request_id,
                "feature_title": b.feature_title,
                "original_priority": b.original_priority,
                "boosted_priority": b.boosted_priority,
                "status": b.status,
                "reason": b.reason,
                "created_at": b.created_at.isoformat(),
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "completed_at": b.completed_at.isoformat() if b.completed_at else None,
            }
            for b in boosts
        ]

    async def expire_old_boosts(self) -> int:
        """Expire boosts that have passed their expiration date."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(PriorityBoost).where(
                and_(
                    PriorityBoost.status == BoostStatus.ACTIVE.value,
                    PriorityBoost.expires_at < now,
                )
            )
        )
        expired_boosts = result.scalars().all()

        for boost in expired_boosts:
            boost.status = BoostStatus.EXPIRED.value

        await self.db.commit()
        return len(expired_boosts)

    async def complete_boost(
        self,
        boost_id: UUID,
    ) -> Dict[str, Any]:
        """Mark a boost as completed (feature delivered)."""
        result = await self.db.execute(
            select(PriorityBoost).where(PriorityBoost.id == boost_id)
        )
        boost = result.scalar_one_or_none()

        if not boost:
            return {"success": False, "error": "Boost not found"}

        boost.status = BoostStatus.COMPLETED.value
        boost.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "success": True,
            "boost_id": str(boost.id),
            "feature_request_id": boost.feature_request_id,
            "completed_at": boost.completed_at.isoformat(),
        }

    async def get_boosted_features(
        self,
        project_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all currently boosted features."""
        query = select(PriorityBoost).where(
            PriorityBoost.status == BoostStatus.ACTIVE.value
        )

        result = await self.db.execute(query.order_by(PriorityBoost.created_at.desc()))
        boosts = result.scalars().all()

        return [
            {
                "boost_id": str(b.id),
                "feature_request_id": b.feature_request_id,
                "feature_title": b.feature_title,
                "customer_id": b.customer_id,
                "boosted_priority": b.boosted_priority,
                "original_priority": b.original_priority,
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "days_remaining": (b.expires_at - datetime.now(timezone.utc)).days if b.expires_at else None,
            }
            for b in boosts
        ]
