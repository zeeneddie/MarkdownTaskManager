# backend/app/services/gamification_service.py
"""
Gamification Service - Week 119-120

Manages badges, points, levels, and streaks.
- Award points for actions
- Check and award badges
- Track user levels and progression
- Maintain activity streaks
"""

from datetime import datetime, date, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.engagement import (
    BadgeDefinition,
    UserBadge,
    UserLevel,
    UserPointsHistory,
    ActionType,
    BadgeCategory,
    BadgeTier,
    LEVEL_DEFINITIONS,
    POINT_VALUES,
    DEFAULT_BADGES,
)


class GamificationService:
    """Service for gamification features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== USER LEVEL MANAGEMENT ==============

    async def get_or_create_user_level(self, customer_id: str) -> UserLevel:
        """Get or create user level record."""
        result = await self.db.execute(
            select(UserLevel).where(UserLevel.customer_id == customer_id)
        )
        user_level = result.scalar_one_or_none()

        if not user_level:
            user_level = UserLevel(
                id=uuid4(),
                customer_id=customer_id,
                current_level=1,
                level_name=LEVEL_DEFINITIONS[1]["name"],
                total_points=0,
                points_to_next_level=LEVEL_DEFINITIONS[2]["points_required"],
            )
            self.db.add(user_level)
            await self.db.commit()
            await self.db.refresh(user_level)

        return user_level

    async def get_user_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get complete user gamification profile."""
        user_level = await self.get_or_create_user_level(customer_id)
        badges = await self.get_user_badges(customer_id)
        recent_points = await self.get_points_history(customer_id, limit=10)

        # Calculate progress to next level
        current_level_points = LEVEL_DEFINITIONS.get(user_level.current_level, {}).get("points_required", 0)
        next_level = user_level.current_level + 1
        next_level_points = LEVEL_DEFINITIONS.get(next_level, {}).get("points_required", user_level.total_points)

        if next_level_points > current_level_points:
            progress_percent = ((user_level.total_points - current_level_points) /
                              (next_level_points - current_level_points)) * 100
        else:
            progress_percent = 100

        return {
            "customer_id": customer_id,
            "level": {
                "current": user_level.current_level,
                "name": user_level.level_name,
                "color": LEVEL_DEFINITIONS.get(user_level.current_level, {}).get("color", "#9CA3AF"),
                "total_points": user_level.total_points,
                "points_to_next": user_level.points_to_next_level,
                "progress_percent": round(min(progress_percent, 100), 1),
                "is_max_level": user_level.current_level >= max(LEVEL_DEFINITIONS.keys()),
            },
            "stats": user_level.get_stats(),
            "streak": {
                "current": user_level.current_streak_days,
                "longest": user_level.longest_streak_days,
                "last_activity": user_level.last_activity_date.isoformat() if user_level.last_activity_date else None,
            },
            "badges": {
                "total": len(badges),
                "recent": badges[:5],
            },
            "recent_points": recent_points,
        }

    # ============== POINTS MANAGEMENT ==============

    async def award_points(
        self,
        customer_id: str,
        action_type: str,
        points: Optional[int] = None,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Award points for an action."""
        user_level = await self.get_or_create_user_level(customer_id)

        # Get points from config if not specified
        if points is None:
            points = POINT_VALUES.get(action_type, 0)

        if points == 0:
            return {"success": True, "points_awarded": 0, "message": "No points for this action"}

        # Update user stats based on action type
        if action_type == ActionType.FEATURE_REQUEST.value:
            user_level.features_requested += 1
        elif action_type == ActionType.FEEDBACK.value:
            user_level.feedback_given += 1
        elif action_type == ActionType.VOTE.value:
            user_level.votes_cast += 1
        elif action_type == ActionType.COMMENT.value:
            user_level.comments_made += 1

        # Update streak
        user_level.update_streak()

        # Add points and check for level up
        leveled_up = user_level.add_points(points)

        # Record transaction
        history = UserPointsHistory(
            id=uuid4(),
            customer_id=customer_id,
            points=points,
            reason=reason or f"Points for {action_type}",
            action_type=action_type,
            reference_id=reference_id,
            reference_type=reference_type,
            balance_after=user_level.total_points,
        )
        self.db.add(history)

        await self.db.commit()

        # Check for new badges
        new_badges = await self.check_and_award_badges(customer_id)

        result = {
            "success": True,
            "points_awarded": points,
            "total_points": user_level.total_points,
            "current_level": user_level.current_level,
            "level_name": user_level.level_name,
            "leveled_up": leveled_up,
            "new_badges": new_badges,
        }

        if leveled_up:
            # Award level up bonus
            await self._award_level_up_bonus(customer_id, user_level.current_level)
            result["level_up_message"] = f"Congratulations! You reached level {user_level.current_level}: {user_level.level_name}!"

        return result

    async def _award_level_up_bonus(self, customer_id: str, new_level: int) -> None:
        """Award bonus points for leveling up."""
        bonus_points = POINT_VALUES.get(ActionType.LEVEL_UP.value, 25)

        history = UserPointsHistory(
            id=uuid4(),
            customer_id=customer_id,
            points=bonus_points,
            reason=f"Level up bonus: reached level {new_level}",
            action_type=ActionType.LEVEL_UP.value,
            reference_id=str(new_level),
            reference_type="level",
            balance_after=0,  # Will be updated
        )
        self.db.add(history)

    async def get_points_history(
        self,
        customer_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get points transaction history."""
        result = await self.db.execute(
            select(UserPointsHistory).where(
                UserPointsHistory.customer_id == customer_id
            ).order_by(UserPointsHistory.created_at.desc()).limit(limit)
        )
        history = result.scalars().all()

        return [
            {
                "id": str(h.id),
                "points": h.points,
                "reason": h.reason,
                "action_type": h.action_type,
                "balance_after": h.balance_after,
                "created_at": h.created_at.isoformat(),
            }
            for h in history
        ]

    # ============== BADGE MANAGEMENT ==============

    async def initialize_default_badges(self) -> int:
        """Initialize default badge definitions."""
        count = 0
        for badge_data in DEFAULT_BADGES:
            # Check if exists
            result = await self.db.execute(
                select(BadgeDefinition).where(BadgeDefinition.name == badge_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                badge = BadgeDefinition(
                    id=uuid4(),
                    **badge_data,
                )
                self.db.add(badge)
                count += 1

        await self.db.commit()
        return count

    async def get_all_badges(self, include_secret: bool = False) -> List[Dict[str, Any]]:
        """Get all available badges."""
        query = select(BadgeDefinition).where(BadgeDefinition.is_active == True)
        if not include_secret:
            query = query.where(BadgeDefinition.is_secret == False)

        result = await self.db.execute(query.order_by(BadgeDefinition.tier, BadgeDefinition.name))
        badges = result.scalars().all()

        return [
            {
                "id": str(b.id),
                "name": b.name,
                "display_name": b.display_name,
                "description": b.description,
                "icon": b.icon,
                "color": b.color,
                "category": b.category,
                "tier": b.tier,
                "points_awarded": b.points_awarded,
            }
            for b in badges
        ]

    async def get_user_badges(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all badges earned by a user."""
        result = await self.db.execute(
            select(UserBadge, BadgeDefinition).join(
                BadgeDefinition, UserBadge.badge_id == BadgeDefinition.id
            ).where(
                UserBadge.customer_id == customer_id
            ).order_by(UserBadge.earned_at.desc())
        )
        rows = result.all()

        return [
            {
                "id": str(ub.id),
                "badge_id": str(bd.id),
                "name": bd.name,
                "display_name": bd.display_name,
                "description": bd.description,
                "icon": bd.icon,
                "color": bd.color,
                "tier": bd.tier,
                "points_awarded": bd.points_awarded,
                "earned_at": ub.earned_at.isoformat(),
                "earned_for": ub.earned_for,
                "is_displayed": ub.is_displayed,
            }
            for ub, bd in rows
        ]

    async def check_and_award_badges(self, customer_id: str) -> List[Dict[str, Any]]:
        """Check all badges and award any that are newly earned."""
        user_level = await self.get_or_create_user_level(customer_id)
        user_stats = user_level.get_stats()

        # Get all active badges
        result = await self.db.execute(
            select(BadgeDefinition).where(BadgeDefinition.is_active == True)
        )
        all_badges = result.scalars().all()

        # Get already earned badges
        result = await self.db.execute(
            select(UserBadge.badge_id).where(UserBadge.customer_id == customer_id)
        )
        earned_badge_ids = {row[0] for row in result.all()}

        new_badges = []
        for badge in all_badges:
            if badge.id in earned_badge_ids:
                continue

            if badge.check_criteria(user_stats):
                # Award badge
                user_badge = UserBadge(
                    id=uuid4(),
                    customer_id=customer_id,
                    badge_id=badge.id,
                    earned_at=datetime.now(timezone.utc),
                    earned_for=f"Met criteria: {badge.criteria_target} >= {badge.criteria_value}",
                    progress_snapshot=user_stats,
                )
                self.db.add(user_badge)

                # Award badge points
                if badge.points_awarded > 0:
                    user_level.total_points += badge.points_awarded
                    history = UserPointsHistory(
                        id=uuid4(),
                        customer_id=customer_id,
                        points=badge.points_awarded,
                        reason=f"Earned badge: {badge.display_name}",
                        action_type=ActionType.BADGE.value,
                        reference_id=str(badge.id),
                        reference_type="badge",
                        balance_after=user_level.total_points,
                    )
                    self.db.add(history)

                new_badges.append({
                    "badge_id": str(badge.id),
                    "name": badge.name,
                    "display_name": badge.display_name,
                    "icon": badge.icon,
                    "tier": badge.tier,
                    "points_awarded": badge.points_awarded,
                })

        if new_badges:
            await self.db.commit()

        return new_badges

    async def award_badge_manually(
        self,
        customer_id: str,
        badge_name: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Manually award a badge to a user."""
        # Find badge
        result = await self.db.execute(
            select(BadgeDefinition).where(BadgeDefinition.name == badge_name)
        )
        badge = result.scalar_one_or_none()

        if not badge:
            return {"success": False, "error": f"Badge not found: {badge_name}"}

        # Check if already earned
        result = await self.db.execute(
            select(UserBadge).where(
                and_(
                    UserBadge.customer_id == customer_id,
                    UserBadge.badge_id == badge.id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return {"success": False, "error": "User already has this badge"}

        # Award badge
        user_badge = UserBadge(
            id=uuid4(),
            customer_id=customer_id,
            badge_id=badge.id,
            earned_at=datetime.now(timezone.utc),
            earned_for=reason or "Manually awarded",
        )
        self.db.add(user_badge)

        # Award points
        user_level = await self.get_or_create_user_level(customer_id)
        if badge.points_awarded > 0:
            user_level.total_points += badge.points_awarded
            history = UserPointsHistory(
                id=uuid4(),
                customer_id=customer_id,
                points=badge.points_awarded,
                reason=f"Earned badge: {badge.display_name}",
                action_type=ActionType.BADGE.value,
                reference_id=str(badge.id),
                reference_type="badge",
                balance_after=user_level.total_points,
            )
            self.db.add(history)

        await self.db.commit()

        return {
            "success": True,
            "badge": {
                "id": str(badge.id),
                "name": badge.name,
                "display_name": badge.display_name,
                "points_awarded": badge.points_awarded,
            },
        }

    # ============== LEADERBOARD ==============

    async def get_leaderboard(
        self,
        limit: int = 10,
        timeframe: str = "all_time",
    ) -> List[Dict[str, Any]]:
        """Get points leaderboard."""
        result = await self.db.execute(
            select(UserLevel).order_by(
                UserLevel.total_points.desc()
            ).limit(limit)
        )
        users = result.scalars().all()

        return [
            {
                "rank": i + 1,
                "customer_id": u.customer_id,
                "level": u.current_level,
                "level_name": u.level_name,
                "total_points": u.total_points,
                "badges_earned": await self._count_badges(u.customer_id),
                "current_streak": u.current_streak_days,
            }
            for i, u in enumerate(users)
        ]

    async def _count_badges(self, customer_id: str) -> int:
        """Count badges for a user."""
        result = await self.db.execute(
            select(func.count(UserBadge.id)).where(
                UserBadge.customer_id == customer_id
            )
        )
        return result.scalar() or 0

    # ============== STATISTICS ==============

    async def get_gamification_statistics(self) -> Dict[str, Any]:
        """Get overall gamification statistics."""
        # Total users
        result = await self.db.execute(select(func.count(UserLevel.id)))
        total_users = result.scalar() or 0

        # Total points awarded
        result = await self.db.execute(
            select(func.sum(UserPointsHistory.points)).where(
                UserPointsHistory.points > 0
            )
        )
        total_points = result.scalar() or 0

        # Total badges earned
        result = await self.db.execute(select(func.count(UserBadge.id)))
        total_badges = result.scalar() or 0

        # Level distribution
        result = await self.db.execute(
            select(UserLevel.current_level, func.count(UserLevel.id)).group_by(
                UserLevel.current_level
            )
        )
        level_dist = {row[0]: row[1] for row in result.all()}

        # Most popular badges
        result = await self.db.execute(
            select(BadgeDefinition.name, func.count(UserBadge.id)).join(
                BadgeDefinition, UserBadge.badge_id == BadgeDefinition.id
            ).group_by(BadgeDefinition.name).order_by(
                func.count(UserBadge.id).desc()
            ).limit(5)
        )
        popular_badges = [{"name": row[0], "count": row[1]} for row in result.all()]

        return {
            "total_users": total_users,
            "total_points_awarded": total_points,
            "total_badges_earned": total_badges,
            "level_distribution": level_dist,
            "popular_badges": popular_badges,
            "level_definitions": LEVEL_DEFINITIONS,
        }
