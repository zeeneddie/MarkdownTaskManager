"""
Tier Configuration Service - Week 87

Handles granular tier selection at project, epic, feature, and story level.
Calculates expected outcomes (confidence, cost, LLM count) based on tier configuration.

Features:
- Tier override inheritance (project -> epic -> feature -> story)
- Expected outcomes calculation per item
- Cost estimation for tier combinations
- Tier comparison previews
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.deep_extraction import (
    ExtractionSession, ExtractionConsensus, ExtractionTier, TIER_CONFIG
)


class TierConfigService:
    """Service for managing granular tier configuration."""

    # Cost per 1K LOC per tier (base rates)
    COST_PER_1K_LOC = {
        ExtractionTier.FREE: 0.0,
        ExtractionTier.BASIC: 0.10,
        ExtractionTier.STANDARD: 0.50,
        ExtractionTier.PROFESSIONAL: 1.50,
        ExtractionTier.PREMIUM: 3.00,
    }

    # Item type multipliers for cost estimation
    ITEM_TYPE_MULTIPLIERS = {
        "epic": 1.5,      # Epics are larger, cost more
        "feature": 1.0,   # Features are baseline
        "story": 0.5,     # Stories are smaller
        "task": 0.2,      # Tasks are smallest
    }

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # TIER INHERITANCE
    # ========================================================================

    def get_effective_tier(
        self,
        item: ExtractionConsensus,
        session: ExtractionSession
    ) -> str:
        """
        Calculate effective tier for an item based on inheritance chain.

        Inheritance order:
        1. Item's own tier_override (if set)
        2. Parent's effective tier (if has parent)
        3. Session's default tier
        """
        # Check item's own override
        if item.tier_override:
            return item.tier_override

        # Check parent's effective tier
        if item.parent_id:
            parent = self.db.query(ExtractionConsensus).filter(
                ExtractionConsensus.id == item.parent_id
            ).first()
            if parent and parent.tier_effective:
                return parent.tier_effective

        # Fall back to session tier
        return session.tier

    def recalculate_hierarchy_tiers(self, session_id: UUID) -> Dict[str, Any]:
        """
        Recalculate effective tiers for all items in a session.

        Returns summary of tier distribution.
        """
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == session_id
        ).first()

        if not session:
            return {"error": "Session not found"}

        # Get all items ordered by hierarchy (epics first, then features, etc.)
        items = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.session_id == session_id
        ).order_by(ExtractionConsensus.item_type).all()

        # Build parent lookup
        item_lookup = {str(item.id): item for item in items}

        # Calculate effective tiers
        tier_counts = {tier.value: 0 for tier in ExtractionTier}
        updated_count = 0

        for item in items:
            effective = self.get_effective_tier(item, session)
            if item.tier_effective != effective:
                item.tier_effective = effective
                updated_count += 1

            # Update expected outcomes
            self._update_expected_outcomes(item, effective)

            tier_counts[effective] += 1

        self.db.commit()

        return {
            "session_id": str(session_id),
            "items_updated": updated_count,
            "tier_distribution": tier_counts,
            "total_items": len(items)
        }

    # ========================================================================
    # TIER OVERRIDE MANAGEMENT
    # ========================================================================

    def set_item_tier_override(
        self,
        item_id: UUID,
        tier: Optional[str],
        cascade: bool = True
    ) -> Dict[str, Any]:
        """
        Set tier override for a specific item.

        Args:
            item_id: The item to update
            tier: The tier to set (None to clear override and inherit)
            cascade: Whether to recalculate children's effective tiers
        """
        item = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.id == item_id
        ).first()

        if not item:
            return {"error": "Item not found"}

        # Validate tier
        if tier and tier not in [t.value for t in ExtractionTier]:
            return {"error": f"Invalid tier: {tier}"}

        # Check if override is allowed for this item type
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == item.session_id
        ).first()

        if session.tier_config_locked == 'Y':
            return {"error": "Tier configuration is locked for this session"}

        if item.item_type == "epic" and session.allow_epic_override != 'Y':
            return {"error": "Epic tier override is disabled for this session"}
        elif item.item_type == "feature" and session.allow_feature_override != 'Y':
            return {"error": "Feature tier override is disabled for this session"}
        elif item.item_type == "story" and session.allow_story_override != 'Y':
            return {"error": "Story tier override is disabled for this session"}

        # Set the override
        old_tier = item.tier_override
        item.tier_override = tier
        item.tier_effective = tier if tier else self.get_effective_tier(item, session)

        # Update expected outcomes
        self._update_expected_outcomes(item, item.tier_effective)

        # Cascade to children if requested
        children_updated = 0
        if cascade:
            children_updated = self._cascade_tier_update(item, session)

        self.db.commit()

        return {
            "item_id": str(item_id),
            "old_tier_override": old_tier,
            "new_tier_override": tier,
            "tier_effective": item.tier_effective,
            "children_updated": children_updated
        }

    def _cascade_tier_update(
        self,
        parent: ExtractionConsensus,
        session: ExtractionSession
    ) -> int:
        """Update effective tiers for all children of an item."""
        children = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.parent_id == parent.id
        ).all()

        updated = 0
        for child in children:
            # Only update if child doesn't have its own override
            if not child.tier_override:
                child.tier_effective = parent.tier_effective
                self._update_expected_outcomes(child, child.tier_effective)
                updated += 1
                # Recursively update grandchildren
                updated += self._cascade_tier_update(child, session)

        return updated

    # ========================================================================
    # EXPECTED OUTCOMES
    # ========================================================================

    def _update_expected_outcomes(self, item: ExtractionConsensus, tier: str) -> None:
        """Update expected outcomes for an item based on its effective tier."""
        tier_enum = ExtractionTier(tier)
        config = TIER_CONFIG.get(tier_enum, TIER_CONFIG[ExtractionTier.FREE])

        item.expected_confidence = config["confidence_target"]
        item.expected_llm_count = config["llm_count"]
        item.expected_cost_usd = self._estimate_item_cost(item, tier_enum)

    def _estimate_item_cost(
        self,
        item: ExtractionConsensus,
        tier: ExtractionTier
    ) -> float:
        """Estimate extraction cost for a single item."""
        base_cost = self.COST_PER_1K_LOC.get(tier, 0.0)
        multiplier = self.ITEM_TYPE_MULTIPLIERS.get(item.item_type, 1.0)

        # Estimate LOC based on item type
        estimated_loc = {
            "epic": 10000,    # Epics typically span ~10K LOC
            "feature": 3000,  # Features ~3K LOC
            "story": 500,     # Stories ~500 LOC
            "task": 100,      # Tasks ~100 LOC
        }.get(item.item_type, 1000)

        return round((estimated_loc / 1000) * base_cost * multiplier, 2)

    def get_expected_outcomes_preview(
        self,
        session_id: UUID,
        tier_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Preview expected outcomes for a session with optional tier overrides.

        Args:
            session_id: The session to preview
            tier_overrides: Optional dict of item_id -> tier to preview

        Returns:
            Summary of expected outcomes including confidence, cost, and LLM counts
        """
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == session_id
        ).first()

        if not session:
            return {"error": "Session not found"}

        items = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.session_id == session_id
        ).all()

        # Apply preview overrides
        preview_tiers = {}
        for item in items:
            if tier_overrides and str(item.id) in tier_overrides:
                preview_tiers[str(item.id)] = tier_overrides[str(item.id)]
            elif item.tier_override:
                preview_tiers[str(item.id)] = item.tier_override
            elif item.tier_effective:
                preview_tiers[str(item.id)] = item.tier_effective
            else:
                preview_tiers[str(item.id)] = session.tier

        # Calculate totals
        total_cost = 0.0
        avg_confidence = 0.0
        tier_distribution = {tier.value: {"count": 0, "cost": 0.0} for tier in ExtractionTier}
        items_by_type = {"epic": [], "feature": [], "story": [], "task": []}

        for item in items:
            tier_str = preview_tiers.get(str(item.id), session.tier)
            tier_enum = ExtractionTier(tier_str)
            config = TIER_CONFIG.get(tier_enum, TIER_CONFIG[ExtractionTier.FREE])

            item_cost = self._estimate_item_cost(item, tier_enum)
            total_cost += item_cost
            avg_confidence += config["confidence_target"]

            tier_distribution[tier_str]["count"] += 1
            tier_distribution[tier_str]["cost"] += item_cost

            items_by_type[item.item_type].append({
                "id": str(item.id),
                "title": item.item_title,
                "tier": tier_str,
                "expected_confidence": config["confidence_target"],
                "expected_cost": item_cost,
                "llm_count": config["llm_count"]
            })

        avg_confidence = avg_confidence / len(items) if items else 0.0

        return {
            "session_id": str(session_id),
            "total_items": len(items),
            "total_cost_usd": round(total_cost, 2),
            "average_confidence": round(avg_confidence, 2),
            "tier_distribution": tier_distribution,
            "items_by_type": items_by_type,
            "session_tier": session.tier
        }

    # ========================================================================
    # TIER COMPARISON
    # ========================================================================

    def compare_tiers_for_item(self, item_id: UUID) -> Dict[str, Any]:
        """
        Compare all tier options for a specific item.

        Returns expected outcomes for each tier.
        """
        item = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.id == item_id
        ).first()

        if not item:
            return {"error": "Item not found"}

        comparisons = {}
        for tier in ExtractionTier:
            config = TIER_CONFIG[tier]
            cost = self._estimate_item_cost(item, tier)

            comparisons[tier.value] = {
                "price_usd": config["price_usd"],
                "confidence_target": config["confidence_target"],
                "llm_count": config["llm_count"],
                "human_review": config["human_review"],
                "estimated_cost": cost,
                "llms": config["llms"]
            }

        return {
            "item_id": str(item_id),
            "item_title": item.item_title,
            "item_type": item.item_type,
            "current_tier": item.tier_effective or item.tier_override,
            "comparisons": comparisons
        }

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    def bulk_set_tier_overrides(
        self,
        session_id: UUID,
        overrides: Dict[str, Optional[str]]
    ) -> Dict[str, Any]:
        """
        Set tier overrides for multiple items at once.

        Args:
            session_id: The session containing the items
            overrides: Dict of item_id -> tier (or None to clear)

        Returns:
            Summary of changes made
        """
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == session_id
        ).first()

        if not session:
            return {"error": "Session not found"}

        if session.tier_config_locked == 'Y':
            return {"error": "Tier configuration is locked"}

        updated = 0
        errors = []

        for item_id_str, tier in overrides.items():
            try:
                item_id = UUID(item_id_str)
                result = self.set_item_tier_override(item_id, tier, cascade=False)
                if "error" in result:
                    errors.append({"item_id": item_id_str, "error": result["error"]})
                else:
                    updated += 1
            except Exception as e:
                errors.append({"item_id": item_id_str, "error": str(e)})

        # Recalculate all effective tiers
        self.recalculate_hierarchy_tiers(session_id)

        return {
            "session_id": str(session_id),
            "items_updated": updated,
            "errors": errors
        }

    def reset_all_overrides(self, session_id: UUID) -> Dict[str, Any]:
        """Reset all tier overrides to inherit from session default."""
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == session_id
        ).first()

        if not session:
            return {"error": "Session not found"}

        items = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.session_id == session_id
        ).all()

        for item in items:
            item.tier_override = None
            item.tier_effective = session.tier
            self._update_expected_outcomes(item, session.tier)

        self.db.commit()

        return {
            "session_id": str(session_id),
            "items_reset": len(items),
            "default_tier": session.tier
        }

    # ========================================================================
    # SESSION SETTINGS
    # ========================================================================

    def update_session_tier_settings(
        self,
        session_id: UUID,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update session-level tier settings.

        Settings can include:
        - tier: Default tier for the session
        - allow_epic_override: Y/N
        - allow_feature_override: Y/N
        - allow_story_override: Y/N
        - tier_config_locked: Y/N
        """
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == session_id
        ).first()

        if not session:
            return {"error": "Session not found"}

        updated_fields = []

        if "tier" in settings:
            if settings["tier"] not in [t.value for t in ExtractionTier]:
                return {"error": f"Invalid tier: {settings['tier']}"}
            session.tier = settings["tier"]
            config = TIER_CONFIG[ExtractionTier(settings["tier"])]
            session.tier_price_usd = config["price_usd"]
            session.tier_confidence_target = config["confidence_target"]
            updated_fields.append("tier")

        for field in ["allow_epic_override", "allow_feature_override",
                      "allow_story_override", "tier_config_locked"]:
            if field in settings:
                if settings[field] not in ['Y', 'N']:
                    return {"error": f"Invalid value for {field}: must be 'Y' or 'N'"}
                setattr(session, field, settings[field])
                updated_fields.append(field)

        self.db.commit()

        # Recalculate if tier changed
        if "tier" in settings:
            self.recalculate_hierarchy_tiers(session_id)

        return {
            "session_id": str(session_id),
            "updated_fields": updated_fields,
            "current_settings": {
                "tier": session.tier,
                "allow_epic_override": session.allow_epic_override,
                "allow_feature_override": session.allow_feature_override,
                "allow_story_override": session.allow_story_override,
                "tier_config_locked": session.tier_config_locked
            }
        }

    def get_hierarchy_config(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get full hierarchy configuration for a session.

        Returns tree structure with tier info for each item.
        """
        session = self.db.query(ExtractionSession).filter(
            ExtractionSession.id == session_id
        ).first()

        if not session:
            return {"error": "Session not found"}

        items = self.db.query(ExtractionConsensus).filter(
            ExtractionConsensus.session_id == session_id
        ).all()

        # Build tree structure
        items_by_parent = {}
        root_items = []

        for item in items:
            item_data = {
                "id": str(item.id),
                "title": item.item_title,
                "type": item.item_type,
                "tier_override": item.tier_override,
                "tier_effective": item.tier_effective or session.tier,
                "tier_locked": item.tier_locked == 'Y',
                "expected_confidence": item.expected_confidence,
                "expected_cost_usd": item.expected_cost_usd,
                "estimated_fp": item.estimated_fp,
                "children": []
            }

            if item.parent_id:
                parent_key = str(item.parent_id)
                if parent_key not in items_by_parent:
                    items_by_parent[parent_key] = []
                items_by_parent[parent_key].append(item_data)
            else:
                root_items.append(item_data)

        # Attach children recursively
        def attach_children(item_data):
            item_id = item_data["id"]
            if item_id in items_by_parent:
                item_data["children"] = items_by_parent[item_id]
                for child in item_data["children"]:
                    attach_children(child)

        for root in root_items:
            attach_children(root)

        return {
            "session_id": str(session_id),
            "session_tier": session.tier,
            "settings": {
                "allow_epic_override": session.allow_epic_override == 'Y',
                "allow_feature_override": session.allow_feature_override == 'Y',
                "allow_story_override": session.allow_story_override == 'Y',
                "tier_config_locked": session.tier_config_locked == 'Y'
            },
            "hierarchy": root_items,
            "total_items": len(items)
        }
