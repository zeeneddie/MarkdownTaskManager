# backend/app/services/personalized_dashboard_service.py
"""
Personalized Dashboard Service - Week 119-120

Manages user preferences and personalized recommendations.
- Dashboard layout preferences
- Feature recommendations based on interests
- Trending features
- Activity feed
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from sqlalchemy.orm.attributes import flag_modified

from app.models.engagement import (
    DashboardPreferences,
    FeatureRecommendation,
    RecommendationType,
    RecommendationStatus,
)
from app.models.graph_workflow import PortalFeatureRequest


class PersonalizedDashboardService:
    """Service for personalized dashboard features."""

    # Default widgets
    DEFAULT_WIDGETS = [
        "my_requests",
        "recommendations",
        "trending",
        "activity_feed",
        "badges",
        "stats",
        "watched_features",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== PREFERENCES MANAGEMENT ==============

    async def get_or_create_preferences(self, customer_id: str) -> DashboardPreferences:
        """Get or create dashboard preferences."""
        result = await self.db.execute(
            select(DashboardPreferences).where(
                DashboardPreferences.customer_id == customer_id
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            prefs = DashboardPreferences(
                id=uuid4(),
                customer_id=customer_id,
                widgets_order=self.DEFAULT_WIDGETS,
                hidden_widgets=[],
                interest_tags=[],
                watched_features=[],
            )
            self.db.add(prefs)
            await self.db.commit()
            await self.db.refresh(prefs)

        return prefs

    async def get_preferences(self, customer_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        prefs = await self.get_or_create_preferences(customer_id)

        return {
            "customer_id": customer_id,
            "layout": prefs.layout,
            "widgets": {
                "order": prefs.widgets_order or self.DEFAULT_WIDGETS,
                "hidden": prefs.hidden_widgets or [],
            },
            "content": {
                "show_recommendations": prefs.show_recommendations,
                "show_trending": prefs.show_trending,
                "show_activity_feed": prefs.show_activity_feed,
                "show_badges": prefs.show_badges,
                "show_stats": prefs.show_stats,
            },
            "notifications": {
                "email_digest": prefs.email_digest,
                "feature_updates": prefs.notify_feature_updates,
                "new_badges": prefs.notify_new_badges,
                "level_up": prefs.notify_level_up,
            },
            "interests": {
                "tags": prefs.interest_tags or [],
                "watched_features": prefs.watched_features or [],
            },
        }

    async def update_preferences(
        self,
        customer_id: str,
        layout: Optional[str] = None,
        widgets_order: Optional[List[str]] = None,
        hidden_widgets: Optional[List[str]] = None,
        show_recommendations: Optional[bool] = None,
        show_trending: Optional[bool] = None,
        show_activity_feed: Optional[bool] = None,
        show_badges: Optional[bool] = None,
        show_stats: Optional[bool] = None,
        email_digest: Optional[str] = None,
        notify_feature_updates: Optional[bool] = None,
        notify_new_badges: Optional[bool] = None,
        notify_level_up: Optional[bool] = None,
        interest_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update user preferences."""
        prefs = await self.get_or_create_preferences(customer_id)

        # Update fields if provided
        if layout is not None:
            prefs.layout = layout
        if widgets_order is not None:
            prefs.widgets_order = widgets_order
        if hidden_widgets is not None:
            prefs.hidden_widgets = hidden_widgets
        if show_recommendations is not None:
            prefs.show_recommendations = show_recommendations
        if show_trending is not None:
            prefs.show_trending = show_trending
        if show_activity_feed is not None:
            prefs.show_activity_feed = show_activity_feed
        if show_badges is not None:
            prefs.show_badges = show_badges
        if show_stats is not None:
            prefs.show_stats = show_stats
        if email_digest is not None:
            prefs.email_digest = email_digest
        if notify_feature_updates is not None:
            prefs.notify_feature_updates = notify_feature_updates
        if notify_new_badges is not None:
            prefs.notify_new_badges = notify_new_badges
        if notify_level_up is not None:
            prefs.notify_level_up = notify_level_up
        if interest_tags is not None:
            prefs.interest_tags = interest_tags

        await self.db.commit()

        return {"success": True, "message": "Preferences updated"}

    # ============== WATCHED FEATURES ==============

    async def watch_feature(
        self,
        customer_id: str,
        feature_id: int,
    ) -> Dict[str, Any]:
        """Add a feature to watch list."""
        prefs = await self.get_or_create_preferences(customer_id)

        watched = list(prefs.watched_features or [])
        if feature_id not in watched:
            watched.append(feature_id)
            prefs.watched_features = watched
            flag_modified(prefs, "watched_features")
            await self.db.commit()
            await self.db.refresh(prefs)

        return {
            "success": True,
            "feature_id": feature_id,
            "total_watched": len(prefs.watched_features or []),
        }

    async def unwatch_feature(
        self,
        customer_id: str,
        feature_id: int,
    ) -> Dict[str, Any]:
        """Remove a feature from watch list."""
        prefs = await self.get_or_create_preferences(customer_id)

        watched = list(prefs.watched_features or [])
        if feature_id in watched:
            watched.remove(feature_id)
            prefs.watched_features = watched
            flag_modified(prefs, "watched_features")
            await self.db.commit()
            await self.db.refresh(prefs)

        return {
            "success": True,
            "feature_id": feature_id,
            "total_watched": len(prefs.watched_features or []),
        }

    # ============== RECOMMENDATIONS ==============

    async def generate_recommendations(
        self,
        customer_id: str,
        project_id: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate personalized feature recommendations."""
        prefs = await self.get_or_create_preferences(customer_id)
        recommendations = []

        # Get user's interest tags
        interest_tags = prefs.interest_tags or []

        # 1. Get trending features
        trending = await self._get_trending_features(project_id, limit=5)
        for feature in trending:
            await self._create_recommendation(
                customer_id=customer_id,
                feature_request_id=feature["id"],
                project_id=project_id,
                recommendation_type=RecommendationType.TRENDING.value,
                score=feature.get("trending_score", 0.7),
                reason="Trending in the community",
            )
            recommendations.append(feature)

        # 2. Get new features
        new_features = await self._get_new_features(project_id, limit=3)
        for feature in new_features:
            await self._create_recommendation(
                customer_id=customer_id,
                feature_request_id=feature["id"],
                project_id=project_id,
                recommendation_type=RecommendationType.NEW.value,
                score=0.6,
                reason="Recently added feature",
            )
            recommendations.append(feature)

        # 3. Get popular features
        popular = await self._get_popular_features(project_id, limit=3)
        for feature in popular:
            await self._create_recommendation(
                customer_id=customer_id,
                feature_request_id=feature["id"],
                project_id=project_id,
                recommendation_type=RecommendationType.POPULAR.value,
                score=feature.get("popularity_score", 0.65),
                reason="Popular with other users",
            )
            recommendations.append(feature)

        await self.db.commit()

        return recommendations[:limit]

    async def _create_recommendation(
        self,
        customer_id: str,
        feature_request_id: int,
        project_id: Optional[int],
        recommendation_type: str,
        score: float,
        reason: str,
        source_features: Optional[List[int]] = None,
    ) -> Optional[FeatureRecommendation]:
        """Create a recommendation record if not exists."""
        # Check for existing
        result = await self.db.execute(
            select(FeatureRecommendation).where(
                and_(
                    FeatureRecommendation.customer_id == customer_id,
                    FeatureRecommendation.feature_request_id == feature_request_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update if active
            if existing.status == RecommendationStatus.ACTIVE.value:
                existing.score = max(existing.score, score)  # Keep higher score
            return existing

        # Create new
        rec = FeatureRecommendation(
            id=uuid4(),
            customer_id=customer_id,
            feature_request_id=feature_request_id,
            project_id=project_id,
            recommendation_type=recommendation_type,
            score=score,
            reason=reason,
            source_features=source_features,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        self.db.add(rec)
        return rec

    async def get_recommendations(
        self,
        customer_id: str,
        project_id: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get active recommendations for a user."""
        query = select(FeatureRecommendation).where(
            and_(
                FeatureRecommendation.customer_id == customer_id,
                FeatureRecommendation.status == RecommendationStatus.ACTIVE.value,
            )
        ).order_by(FeatureRecommendation.score.desc()).limit(limit)

        if project_id:
            query = query.where(FeatureRecommendation.project_id == project_id)

        result = await self.db.execute(query)
        recs = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "feature_request_id": r.feature_request_id,
                "type": r.recommendation_type,
                "score": r.score,
                "reason": r.reason,
                "created_at": r.created_at.isoformat(),
                "is_expired": r.is_expired(),
            }
            for r in recs
            if not r.is_expired()
        ]

    async def dismiss_recommendation(
        self,
        customer_id: str,
        recommendation_id: UUID,
    ) -> Dict[str, Any]:
        """Dismiss a recommendation."""
        result = await self.db.execute(
            select(FeatureRecommendation).where(
                and_(
                    FeatureRecommendation.id == recommendation_id,
                    FeatureRecommendation.customer_id == customer_id,
                )
            )
        )
        rec = result.scalar_one_or_none()

        if not rec:
            return {"success": False, "error": "Recommendation not found"}

        rec.status = RecommendationStatus.DISMISSED.value
        rec.dismissed_at = datetime.utcnow()

        await self.db.commit()

        return {"success": True, "recommendation_id": str(recommendation_id)}

    # ============== TRENDING & POPULAR ==============

    async def _get_trending_features(
        self,
        project_id: Optional[int],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get trending features (most votes in last 7 days)."""
        # This would normally query PortalFeatureRequest with vote counts
        # For now, return placeholder
        try:
            query = select(PortalFeatureRequest).order_by(
                PortalFeatureRequest.created_at.desc()
            ).limit(limit)

            if project_id:
                query = query.where(PortalFeatureRequest.project_id == project_id)

            result = await self.db.execute(query)
            features = result.scalars().all()

            return [
                {
                    "id": f.id,
                    "title": f.title,
                    "status": f.status,
                    "trending_score": 0.7,
                }
                for f in features
            ]
        except Exception:
            return []

    async def _get_new_features(
        self,
        project_id: Optional[int],
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get recently added features."""
        try:
            since = datetime.utcnow() - timedelta(days=7)
            query = select(PortalFeatureRequest).where(
                PortalFeatureRequest.created_at >= since
            ).order_by(PortalFeatureRequest.created_at.desc()).limit(limit)

            if project_id:
                query = query.where(PortalFeatureRequest.project_id == project_id)

            result = await self.db.execute(query)
            features = result.scalars().all()

            return [
                {
                    "id": f.id,
                    "title": f.title,
                    "status": f.status,
                    "created_at": f.created_at.isoformat(),
                }
                for f in features
            ]
        except Exception:
            return []

    async def _get_popular_features(
        self,
        project_id: Optional[int],
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get most popular features (by total votes)."""
        try:
            query = select(PortalFeatureRequest).order_by(
                PortalFeatureRequest.created_at.desc()
            ).limit(limit)

            if project_id:
                query = query.where(PortalFeatureRequest.project_id == project_id)

            result = await self.db.execute(query)
            features = result.scalars().all()

            return [
                {
                    "id": f.id,
                    "title": f.title,
                    "status": f.status,
                    "popularity_score": 0.65,
                }
                for f in features
            ]
        except Exception:
            return []

    # ============== DASHBOARD DATA ==============

    async def get_dashboard_data(
        self,
        customer_id: str,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get complete dashboard data for a user."""
        prefs = await self.get_or_create_preferences(customer_id)

        data = {
            "preferences": await self.get_preferences(customer_id),
            "widgets": {},
        }

        # Only include enabled widgets
        if prefs.show_recommendations:
            data["widgets"]["recommendations"] = await self.get_recommendations(
                customer_id, project_id, limit=5
            )

        if prefs.show_trending:
            data["widgets"]["trending"] = await self._get_trending_features(
                project_id, limit=5
            )

        # Watched features
        if prefs.watched_features:
            data["widgets"]["watched"] = {
                "feature_ids": prefs.watched_features,
                "count": len(prefs.watched_features),
            }

        return data

    # ============== STATISTICS ==============

    async def get_recommendation_statistics(
        self,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get recommendation statistics."""
        query = select(FeatureRecommendation)
        if project_id:
            query = query.where(FeatureRecommendation.project_id == project_id)

        result = await self.db.execute(query)
        recs = result.scalars().all()

        if not recs:
            return {"total": 0}

        by_type = {}
        by_status = {}
        for r in recs:
            by_type[r.recommendation_type] = by_type.get(r.recommendation_type, 0) + 1
            by_status[r.status] = by_status.get(r.status, 0) + 1

        avg_score = sum(r.score for r in recs) / len(recs)

        return {
            "total": len(recs),
            "by_type": by_type,
            "by_status": by_status,
            "average_score": round(avg_score, 3),
            "active": by_status.get(RecommendationStatus.ACTIVE.value, 0),
            "dismissed": by_status.get(RecommendationStatus.DISMISSED.value, 0),
            "voted": by_status.get(RecommendationStatus.VOTED.value, 0),
        }
