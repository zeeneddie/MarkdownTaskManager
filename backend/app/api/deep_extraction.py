"""
Deep Extraction API - Week 82

REST API endpoints for the Deep Extraction Pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.deep_extraction import (
    ExtractionTier,
    ExtractionStatus,
    ConsensusStatus,
    ConflictStatus,
)
from app.schemas.deep_extraction import (
    ExtractionStartRequest,
    ExtractionRerunRequest,
    ConflictResolveRequest,
    ConsensusDecisionRequest,
    BulkResolveRequest,
    ExtractionSessionResponse,
    ExtractionRunResponse,
    ConsensusItemResponse,
    ConflictResponse,
    ExtractionProgressResponse,
    TierComparisonResponse,
    TierInfo,
    DashboardStatsResponse,
)
from app.services.deep_extraction_service import DeepExtractionService
from app.services.tier_provider_selector import compare_tiers, create_tier_selector


router = APIRouter(prefix="/api/deep-extraction", tags=["deep-extraction"])


# ============================================================================
# TIER INFORMATION
# ============================================================================

@router.get("/tiers", response_model=TierComparisonResponse)
async def get_tier_comparison():
    """
    Get comparison of all extraction tiers.

    Use this to display tier options to customers.
    """
    tiers = compare_tiers()

    return TierComparisonResponse(
        tiers=[
            TierInfo(
                tier=ExtractionTier(t["tier"]),
                price_usd=t["price_usd"],
                confidence_target=t["confidence_target"],
                llm_count=t["llm_count"],
                human_review=t["human_review"],
                llms=t["llms"],
            )
            for t in tiers
        ],
        recommended=ExtractionTier.STANDARD,
        estimated_loc=None,
        estimated_costs={t["tier"]: t["price_usd"] for t in tiers},
    )


@router.get("/tiers/{tier}/providers")
async def get_tier_providers(tier: ExtractionTier):
    """Get detailed provider info for a specific tier."""
    selector = create_tier_selector(tier)

    return {
        "tier": tier.value,
        "providers": selector.get_provider_ids(),
        "provider_count": selector.get_provider_count(),
        "categories": selector.get_providers_by_category(),
        "price_usd": selector.get_price_usd(),
        "confidence_target": selector.get_confidence_target(),
        "includes_human_review": selector.includes_human_review(),
    }


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@router.post("/sessions", response_model=ExtractionSessionResponse)
async def start_extraction(
    request: ExtractionStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new extraction session.

    This creates a session and prepares the pipeline for execution.
    Call /sessions/{id}/run to begin the extraction cycles.
    """
    service = DeepExtractionService(db)

    session = await service.start_extraction(
        project_id=request.project_id,
        source_path=request.source_path,
        tier=request.tier,
        workflow_type=request.workflow_type,
    )

    return ExtractionSessionResponse(
        id=session.id,
        project_id=session.project_id,
        workflow_type=session.workflow_type,
        status=ExtractionStatus(session.status),
        current_cycle=session.current_cycle,
        tier=ExtractionTier(session.tier),
        tier_price_usd=session.tier_price_usd,
        tier_confidence_target=session.tier_confidence_target,
        source_path=session.source_path,
        total_files=session.total_files,
        total_lines=session.total_lines,
        total_epics=session.total_epics,
        total_features=session.total_features,
        total_stories=session.total_stories,
        total_tasks=session.total_tasks,
        total_function_points=session.total_function_points,
        avg_confidence=session.avg_confidence,
        items_auto_accepted=session.items_auto_accepted,
        items_human_reviewed=session.items_human_reviewed,
        actual_cost_usd=session.actual_cost_usd,
        margin_usd=session.margin_usd,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get("/sessions", response_model=List[ExtractionSessionResponse])
async def list_sessions(
    project_id: Optional[int] = Query(None),
    status: Optional[ExtractionStatus] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List extraction sessions with optional filters."""
    service = DeepExtractionService(db)
    sessions = await service.list_sessions(
        project_id=project_id,
        status=status,
        limit=limit,
    )

    return [
        ExtractionSessionResponse(
            id=s.id,
            project_id=s.project_id,
            workflow_type=s.workflow_type,
            status=ExtractionStatus(s.status),
            current_cycle=s.current_cycle,
            tier=ExtractionTier(s.tier),
            tier_price_usd=s.tier_price_usd,
            tier_confidence_target=s.tier_confidence_target,
            source_path=s.source_path,
            total_files=s.total_files,
            total_lines=s.total_lines,
            total_epics=s.total_epics,
            total_features=s.total_features,
            total_stories=s.total_stories,
            total_tasks=s.total_tasks,
            total_function_points=s.total_function_points,
            avg_confidence=s.avg_confidence,
            items_auto_accepted=s.items_auto_accepted,
            items_human_reviewed=s.items_human_reviewed,
            actual_cost_usd=s.actual_cost_usd,
            margin_usd=s.margin_usd,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get extraction session details."""
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ExtractionSessionResponse(
        id=session.id,
        project_id=session.project_id,
        workflow_type=session.workflow_type,
        status=ExtractionStatus(session.status),
        current_cycle=session.current_cycle,
        tier=ExtractionTier(session.tier),
        tier_price_usd=session.tier_price_usd,
        tier_confidence_target=session.tier_confidence_target,
        source_path=session.source_path,
        total_files=session.total_files,
        total_lines=session.total_lines,
        total_epics=session.total_epics,
        total_features=session.total_features,
        total_stories=session.total_stories,
        total_tasks=session.total_tasks,
        total_function_points=session.total_function_points,
        avg_confidence=session.avg_confidence,
        items_auto_accepted=session.items_auto_accepted,
        items_human_reviewed=session.items_human_reviewed,
        actual_cost_usd=session.actual_cost_usd,
        margin_usd=session.margin_usd,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get("/sessions/{session_id}/progress")
async def get_session_progress(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed progress for a session including cycle status."""
    service = DeepExtractionService(db)
    progress = await service.get_session_progress(session_id)

    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress["error"])

    return progress


# ============================================================================
# EXTRACTION EXECUTION
# ============================================================================

@router.post("/sessions/{session_id}/run")
async def run_extraction(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the full extraction pipeline.

    Executes all 5 cycles. May pause at cycle 4 if human review is required.
    """
    service = DeepExtractionService(db)
    result = await service.run_full_extraction(session_id)
    return result


@router.post("/sessions/{session_id}/cycles/{cycle}")
async def run_cycle(
    session_id: UUID,
    cycle: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Run a specific extraction cycle.

    Cycles:
    - 1: Independent Analysis
    - 2: Cross-Enrichment
    - 3: Conflict Detection
    - 4: Human Decision (use /complete-review instead)
    - 5: Final Synthesis
    """
    if cycle < 1 or cycle > 5:
        raise HTTPException(status_code=400, detail="Cycle must be 1-5")

    if cycle == 4:
        raise HTTPException(
            status_code=400,
            detail="Cycle 4 is human review. Use POST /sessions/{id}/complete-review"
        )

    service = DeepExtractionService(db)

    cycle_methods = {
        1: service.run_cycle_1,
        2: service.run_cycle_2,
        3: service.run_cycle_3,
        5: service.run_cycle_5,
    }

    result = await cycle_methods[cycle](session_id)
    return result


@router.post("/sessions/{session_id}/complete-review")
async def complete_human_review(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Complete cycle 4 (human review).

    Call this after resolving all conflicts and reviewing consensus items.
    """
    service = DeepExtractionService(db)
    result = await service.complete_human_review(session_id)
    return result


# ============================================================================
# TIER UPGRADE
# ============================================================================

@router.post("/sessions/{session_id}/upgrade")
async def upgrade_tier(
    session_id: UUID,
    request: ExtractionRerunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Upgrade session to a higher tier.

    Creates a new extraction run with credit from previous tier payment.
    Re-runs extraction with additional LLMs from the new tier.
    """
    service = DeepExtractionService(db)

    try:
        result = await service.upgrade_tier(session_id, request.new_tier)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CONFLICT RESOLUTION
# ============================================================================

@router.get("/sessions/{session_id}/conflicts")
async def get_conflicts(
    session_id: UUID,
    status: Optional[ConflictStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get conflicts for a session."""
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    conflicts = session.conflicts
    if status:
        conflicts = [c for c in conflicts if c.status == status.value]

    return [
        ConflictResponse(
            id=c.id,
            session_id=c.session_id,
            conflict_type=c.conflict_type,
            item_type=c.item_type,
            option_a=c.option_a,
            option_b=c.option_b,
            option_c=c.option_c,
            option_d=c.option_d,
            llm_recommendation=c.llm_recommendation,
            recommendation_reasoning=c.recommendation_reasoning,
            status=c.status,
            human_choice=c.human_choice,
            human_custom=c.human_custom,
            human_reasoning=c.human_reasoning,
            resolved_at=c.resolved_at,
            resolved_by=c.resolved_by,
            created_at=c.created_at,
        )
        for c in conflicts
    ]


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: UUID,
    request: ConflictResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resolve a conflict with human decision."""
    service = DeepExtractionService(db)

    try:
        conflict = await service.resolve_conflict(
            conflict_id=conflict_id,
            choice=request.choice,
            custom_resolution=request.custom_resolution,
            reasoning=request.reasoning,
        )

        return ConflictResponse(
            id=conflict.id,
            session_id=conflict.session_id,
            conflict_type=conflict.conflict_type,
            item_type=conflict.item_type,
            option_a=conflict.option_a,
            option_b=conflict.option_b,
            option_c=conflict.option_c,
            option_d=conflict.option_d,
            llm_recommendation=conflict.llm_recommendation,
            recommendation_reasoning=conflict.recommendation_reasoning,
            status=conflict.status,
            human_choice=conflict.human_choice,
            human_custom=conflict.human_custom,
            human_reasoning=conflict.human_reasoning,
            resolved_at=conflict.resolved_at,
            resolved_by=conflict.resolved_by,
            created_at=conflict.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# CONSENSUS ITEMS
# ============================================================================

@router.get("/sessions/{session_id}/consensus")
async def get_consensus_items(
    session_id: UUID,
    status: Optional[ConsensusStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get consensus items for a session."""
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    items = session.consensus_items
    if status:
        items = [i for i in items if i.status == status.value]

    return [
        ConsensusItemResponse(
            id=i.id,
            session_id=i.session_id,
            item_type=i.item_type,
            item_title=i.item_title,
            item_description=i.item_description,
            supporting_llms=i.supporting_llms,
            confidence_score=i.confidence_score,
            confidence_breakdown=i.confidence_breakdown,
            status=i.status,
            human_decision=i.human_decision,
            human_feedback=i.human_feedback,
            decided_at=i.decided_at,
            decided_by=i.decided_by,
            item_data=i.item_data,
            created_at=i.created_at,
        )
        for i in items
    ]


@router.post("/consensus/{consensus_id}/decide")
async def decide_consensus(
    consensus_id: UUID,
    request: ConsensusDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Make decision on a consensus item (accept/reject)."""
    service = DeepExtractionService(db)

    try:
        item = await service.decide_consensus(
            consensus_id=consensus_id,
            decision=request.decision,
            feedback=request.feedback,
        )

        return ConsensusItemResponse(
            id=item.id,
            session_id=item.session_id,
            item_type=item.item_type,
            item_title=item.item_title,
            item_description=item.item_description,
            supporting_llms=item.supporting_llms,
            confidence_score=item.confidence_score,
            confidence_breakdown=item.confidence_breakdown,
            status=item.status,
            human_decision=item.human_decision,
            human_feedback=item.human_feedback,
            decided_at=item.decided_at,
            decided_by=item.decided_by,
            item_data=item.item_data,
            created_at=item.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# DASHBOARD & STATISTICS
# ============================================================================

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics across all extraction sessions."""
    service = DeepExtractionService(db)
    stats = await service.get_dashboard_stats()

    return DashboardStatsResponse(
        total_sessions=stats["total_sessions"],
        sessions_by_status=stats["sessions_by_status"],
        sessions_by_tier=stats["sessions_by_tier"],
        avg_confidence_by_tier={},  # TODO: Calculate in service
        total_items_extracted=stats["total_items_extracted"],
        total_cost_usd=stats["total_cost_usd"],
        total_revenue_usd=stats["total_revenue_usd"],
        margin_percentage=stats["margin_percentage"],
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================

# ============================================================================
# BULK OPERATIONS (Week 85)
# ============================================================================

@router.post("/sessions/{session_id}/bulk-resolve-conflicts")
async def bulk_resolve_conflicts(
    session_id: UUID,
    request: BulkResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk resolve multiple conflicts at once.

    Efficient for human reviewers working through a queue.
    """
    service = DeepExtractionService(db)

    # Convert to expected format
    resolutions = [
        {
            "conflict_id": d.get("item_id") or d.get("conflict_id"),
            "choice": d.get("decision") or d.get("choice"),
            "reasoning": d.get("reasoning"),
            "custom_resolution": d.get("custom_resolution"),
        }
        for d in request.decisions
    ]

    result = await service.bulk_resolve_conflicts(
        session_id=session_id,
        resolutions=resolutions,
        resolved_by="human",
    )
    return result


@router.post("/sessions/{session_id}/bulk-decide-consensus")
async def bulk_decide_consensus(
    session_id: UUID,
    request: BulkResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk decide on multiple consensus items at once.

    Efficient for accepting/rejecting multiple items.
    """
    service = DeepExtractionService(db)

    # Convert to expected format
    decisions = [
        {
            "consensus_id": d.get("item_id") or d.get("consensus_id"),
            "decision": d["decision"],
            "feedback": d.get("feedback"),
        }
        for d in request.decisions
    ]

    result = await service.bulk_decide_consensus(
        session_id=session_id,
        decisions=decisions,
        decided_by="human",
    )
    return result


@router.post("/sessions/{session_id}/auto-resolve")
async def auto_resolve_conflicts(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-resolve all conflicts using LLM recommendations.

    Useful for lower-tier customers who don't want manual review,
    or as a quick start before human fine-tuning.
    """
    service = DeepExtractionService(db)
    result = await service.auto_resolve_llm_recommendations(session_id)
    return result


# ============================================================================
# HUMAN REVIEW QUEUE (Week 85)
# ============================================================================

@router.get("/sessions/{session_id}/review-queue")
async def get_review_queue(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get items pending human review.

    Returns both conflicts and low-confidence consensus items.
    """
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get pending conflicts
    pending_conflicts = [
        {
            "type": "conflict",
            "id": str(c.id),
            "conflict_type": c.conflict_type,
            "item_type": c.item_type,
            "options": {
                "a": c.option_a,
                "b": c.option_b,
                "c": c.option_c,
                "d": c.option_d,
            },
            "llm_recommendation": c.llm_recommendation,
            "recommendation_reasoning": c.recommendation_reasoning,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in session.conflicts
        if c.status == ConflictStatus.PENDING.value
    ]

    # Get items needing human review
    pending_consensus = [
        {
            "type": "consensus",
            "id": str(i.id),
            "item_type": i.item_type,
            "title": i.item_title,
            "description": i.item_description,
            "confidence_score": i.confidence_score,
            "supporting_llms": i.supporting_llms,
            "confidence_breakdown": i.confidence_breakdown,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in session.consensus_items
        if i.status == ConsensusStatus.HUMAN_REVIEW.value
    ]

    return {
        "session_id": str(session_id),
        "tier": session.tier,
        "total_pending": len(pending_conflicts) + len(pending_consensus),
        "conflicts": pending_conflicts,
        "consensus_items": pending_consensus,
        "can_complete_review": len(pending_conflicts) == 0,
    }


# ============================================================================
# DELTA COMPARISON (Week 85)
# ============================================================================

@router.get("/sessions/{session_id}/delta")
async def get_extraction_delta(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get delta between current and previous extraction run.

    Shows what new items were found after tier upgrade.
    """
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get runs sorted by run_number
    runs = sorted(session.runs, key=lambda r: r.run_number) if session.runs else []

    if len(runs) < 2:
        return {
            "session_id": str(session_id),
            "has_previous_run": False,
            "message": "No previous run to compare",
            "current_run": {
                "id": str(runs[0].id) if runs else None,
                "tier": runs[0].tier if runs else session.tier,
                "epics": session.total_epics,
                "features": session.total_features,
                "stories": session.total_stories,
                "tasks": session.total_tasks,
                "confidence": session.avg_confidence,
            } if runs else None,
        }

    current_run = runs[-1]
    previous_run = runs[-2]

    return {
        "session_id": str(session_id),
        "has_previous_run": True,
        "tier_upgrade": f"{previous_run.tier} → {current_run.tier}",
        "previous_run": {
            "id": str(previous_run.id),
            "tier": previous_run.tier,
            "epics": previous_run.delta_epics,
            "features": previous_run.delta_features,
            "stories": previous_run.delta_stories,
            "tasks": previous_run.delta_tasks,
        },
        "current_run": {
            "id": str(current_run.id),
            "tier": current_run.tier,
            "epics": current_run.delta_epics,
            "features": current_run.delta_features,
            "stories": current_run.delta_stories,
            "tasks": current_run.delta_tasks,
        },
        "delta": {
            "new_epics": current_run.delta_epics - previous_run.delta_epics,
            "new_features": current_run.delta_features - previous_run.delta_features,
            "new_stories": current_run.delta_stories - previous_run.delta_stories,
            "new_tasks": current_run.delta_tasks - previous_run.delta_tasks,
        },
        "confidence_improvement": current_run.confidence_improvement,
        "cost": {
            "credit_applied": current_run.credit_from_previous,
            "amount_charged": current_run.amount_charged,
        },
    }


# ============================================================================
# RE-RUN CAPABILITY (Week 85)
# ============================================================================

@router.post("/sessions/{session_id}/rerun")
async def rerun_extraction(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-run extraction with the same tier.

    Useful when source code has changed.
    """
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Reset session for re-run
    session.status = ExtractionStatus.STARTED.value
    session.current_cycle = 0
    session.cycle_1_completed_at = None
    session.cycle_2_completed_at = None
    session.cycle_3_completed_at = None
    session.cycle_4_completed_at = None
    session.cycle_5_completed_at = None

    await db.commit()

    # Run extraction
    result = await service.run_full_extraction(session_id)
    return result


# ============================================================================
# TIER PRICING & ONBOARDING (Week 86-87)
# ============================================================================

@router.get("/pricing")
async def get_pricing_info():
    """
    Get detailed pricing information for all tiers.

    Includes LOC-based calculations and feature comparison.
    """
    from app.services.tier_provider_selector import compare_tiers, TIER_CONFIG

    tiers = compare_tiers()

    return {
        "base_loc": 50000,
        "tiers": [
            {
                **t,
                "features": {
                    "parallel_llms": t["llm_count"],
                    "human_review": t["human_review"],
                    "cross_enrichment": t["tier"] != "FREE",
                    "conflict_detection": True,
                    "function_points": True,
                    "team_sizing": t["tier"] in ["PROFESSIONAL", "PREMIUM"],
                    "risk_analysis": t["tier"] == "PREMIUM",
                    "priority_support": t["tier"] in ["PROFESSIONAL", "PREMIUM"],
                },
                "recommended": t["tier"] == "STANDARD",
            }
            for t in tiers
        ],
        "loc_multipliers": {
            "0-25K": 0.5,
            "25-50K": 1.0,
            "50-100K": 1.8,
            "100-250K": 3.5,
            "250K+": "Contact sales",
        },
        "complexity_multipliers": {
            "simple": 0.8,
            "moderate": 1.0,
            "complex": 1.3,
            "legacy": 1.5,
        },
    }


@router.post("/estimate-cost")
async def estimate_extraction_cost(
    lines_of_code: int = Query(..., ge=1000),
    tier: ExtractionTier = Query(default=ExtractionTier.STANDARD),
    complexity: str = Query(default="moderate", pattern="^(simple|moderate|complex|legacy)$"),
):
    """
    Estimate extraction cost for a project.

    Takes into account LOC, tier, and complexity.
    """
    from app.services.tier_provider_selector import TIER_CONFIG

    base_price = TIER_CONFIG[tier]["price_usd"]
    base_loc = 50000

    # LOC multiplier
    if lines_of_code <= 25000:
        loc_mult = 0.5
    elif lines_of_code <= 50000:
        loc_mult = 1.0
    elif lines_of_code <= 100000:
        loc_mult = 1.8
    elif lines_of_code <= 250000:
        loc_mult = 3.5
    else:
        loc_mult = 5.0  # Contact sales for exact

    # Complexity multiplier
    complexity_mults = {
        "simple": 0.8,
        "moderate": 1.0,
        "complex": 1.3,
        "legacy": 1.5,
    }
    comp_mult = complexity_mults.get(complexity, 1.0)

    # Calculate
    estimated_cost = base_price * loc_mult * comp_mult

    return {
        "tier": tier.value,
        "lines_of_code": lines_of_code,
        "complexity": complexity,
        "base_price_usd": base_price,
        "loc_multiplier": loc_mult,
        "complexity_multiplier": comp_mult,
        "estimated_cost_usd": round(estimated_cost, 2),
        "confidence_target": TIER_CONFIG[tier]["confidence_target"],
        "llm_count": TIER_CONFIG[tier]["llm_count"],
        "upgrade_options": [
            {
                "tier": t.value,
                "additional_cost": round(TIER_CONFIG[t]["price_usd"] * loc_mult * comp_mult - estimated_cost, 2),
                "confidence_gain": TIER_CONFIG[t]["confidence_target"] - TIER_CONFIG[tier]["confidence_target"],
            }
            for t in ExtractionTier
            if TIER_CONFIG[t]["price_usd"] > base_price
        ],
    }


@router.get("/onboarding/recommended-tier")
async def get_recommended_tier(
    lines_of_code: int = Query(None),
    has_tests: bool = Query(default=True),
    is_legacy: bool = Query(default=False),
    budget_usd: float = Query(None),
):
    """
    Get recommended tier based on project characteristics.

    Uses smart heuristics to suggest the best tier.
    """
    from app.services.tier_provider_selector import TIER_CONFIG

    # Start with STANDARD as default
    recommended = ExtractionTier.STANDARD
    reasoning = []

    # Adjust based on factors
    if is_legacy:
        recommended = ExtractionTier.PROFESSIONAL
        reasoning.append("Legacy codebase benefits from more LLM perspectives")

    if not has_tests:
        if recommended == ExtractionTier.FREE:
            recommended = ExtractionTier.BASIC
        reasoning.append("Without tests, higher confidence extraction is valuable")

    if lines_of_code and lines_of_code > 100000:
        if recommended in [ExtractionTier.FREE, ExtractionTier.BASIC]:
            recommended = ExtractionTier.STANDARD
        reasoning.append("Large codebase benefits from cross-enrichment")

    if budget_usd:
        # Find best tier within budget
        for tier in reversed(list(ExtractionTier)):
            if TIER_CONFIG[tier]["price_usd"] <= budget_usd:
                if tier.value > recommended.value:
                    recommended = tier
                    reasoning.append(f"Maximizing value within ${budget_usd} budget")
                break

    if not reasoning:
        reasoning.append("STANDARD tier provides best value for most projects")

    return {
        "recommended_tier": recommended.value,
        "reasoning": reasoning,
        "tier_details": {
            "price_usd": TIER_CONFIG[recommended]["price_usd"],
            "confidence_target": TIER_CONFIG[recommended]["confidence_target"],
            "llm_count": TIER_CONFIG[recommended]["llm_count"],
            "human_review": TIER_CONFIG[recommended]["human_review"],
        },
        "alternatives": [
            {
                "tier": t.value,
                "price_usd": TIER_CONFIG[t]["price_usd"],
                "confidence": TIER_CONFIG[t]["confidence_target"],
                "why_consider": "Lower cost" if TIER_CONFIG[t]["price_usd"] < TIER_CONFIG[recommended]["price_usd"] else "Higher confidence",
            }
            for t in ExtractionTier
            if t != recommended
        ],
    }


# ============================================================================
# LLM RESULTS (Week 85)
# ============================================================================

@router.get("/sessions/{session_id}/llm-results")
async def get_llm_results(
    session_id: UUID,
    cycle: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get LLM results for a session."""
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    results = session.llm_results
    if cycle:
        results = [r for r in results if r.cycle == cycle]

    return [
        {
            "id": str(r.id),
            "cycle": r.cycle,
            "provider": r.llm_provider,
            "model": r.llm_model,
            "analysis_type": r.analysis_type,
            "epics_found": len(r.extracted_epics or []),
            "features_found": len(r.extracted_features or []),
            "stories_found": len(r.extracted_stories or []),
            "tasks_found": len(r.extracted_tasks or []),
            "tokens_input": r.tokens_input,
            "tokens_output": r.tokens_output,
            "latency_ms": r.latency_ms,
            "cost_usd": r.cost_usd,
            "parsed_output": r.parsed_output,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]


# ============================================================================
# FINAL RESULTS (Week 86)
# ============================================================================

@router.get("/sessions/{session_id}/results")
async def get_extraction_results(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get final extraction results.

    Returns complete hierarchy with function points and recommendations.
    """
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != ExtractionStatus.COMPLETED.value:
        return {
            "session_id": str(session_id),
            "status": session.status,
            "message": "Extraction not yet completed",
            "current_cycle": session.current_cycle,
        }

    # Get accepted items
    accepted = [
        i for i in session.consensus_items
        if i.status in [ConsensusStatus.AUTO_ACCEPTED.value, ConsensusStatus.ACCEPTED.value]
    ]

    epics = [i for i in accepted if i.item_type == "epic"]
    features = [i for i in accepted if i.item_type == "feature"]
    stories = [i for i in accepted if i.item_type == "story"]
    tasks = [i for i in accepted if i.item_type == "task"]

    # Calculate team sizing (rough estimate)
    total_fp = session.total_function_points or 0
    recommended_team = max(2, min(10, total_fp // 200))
    estimated_weeks = max(4, total_fp // (recommended_team * 10))

    return {
        "session_id": str(session_id),
        "tier": session.tier,
        "status": "completed",
        "confidence": {
            "average": session.avg_confidence,
            "target": session.tier_confidence_target,
            "met_target": (session.avg_confidence or 0) >= (session.tier_confidence_target or 0),
        },
        "summary": {
            "total_epics": len(epics),
            "total_features": len(features),
            "total_stories": len(stories),
            "total_tasks": len(tasks),
            "total_function_points": total_fp,
        },
        "epics": [
            {
                "id": str(e.id),
                "title": e.item_title,
                "description": e.item_description,
                "confidence": e.confidence_score,
                "data": e.item_data,
            }
            for e in epics
        ],
        "features": [
            {
                "id": str(f.id),
                "title": f.item_title,
                "description": f.item_description,
                "confidence": f.confidence_score,
            }
            for f in features
        ],
        "stories": [
            {
                "id": str(s.id),
                "title": s.item_title,
                "description": s.item_description,
                "confidence": s.confidence_score,
            }
            for s in stories
        ],
        "tasks": [
            {
                "id": str(t.id),
                "title": t.item_title,
                "confidence": t.confidence_score,
            }
            for t in tasks
        ],
        "recommendations": {
            "team_size": recommended_team,
            "estimated_duration_weeks": estimated_weeks,
            "suggested_sprints": max(1, estimated_weeks // 2),
        },
        "cost": {
            "tier_price_usd": session.tier_price_usd,
            "actual_cost_usd": session.actual_cost_usd,
            "margin_usd": session.margin_usd,
        },
    }


# ============================================================================
# PROJECT EXPORT
# ============================================================================

@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: UUID,
    output_dir: str = Query(..., description="Output directory for markdown files"),
    include_tasks: bool = Query(True, description="Include tasks in story files"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a completed extraction session to markdown project structure.

    Creates:
    - project-summary.md
    - EPIC-{NNN}/epic.md
    - EPIC-{NNN}/FEAT-{NNN}/feature.md
    - EPIC-{NNN}/FEAT-{NNN}/STORY-{NNN}.md
    """
    from pathlib import Path
    from app.services.project_export_service import ProjectExportService

    # Validate output directory
    output_path = Path(output_dir)
    if not output_path.parent.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Parent directory does not exist: {output_path.parent}"
        )

    export_service = ProjectExportService(db)

    try:
        result = await export_service.export_session(
            session_id=session_id,
            output_dir=output_path,
            include_tasks=include_tasks,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/sessions/{session_id}/export-preview")
async def preview_export(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Preview what would be exported without creating files.

    Returns the hierarchical structure that would be generated.
    """
    from app.services.project_export_service import ProjectExportService

    export_service = ProjectExportService(db)

    # Get session
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Get accepted items
    accepted_items = [
        item for item in session.consensus_items
        if item.status in [ConsensusStatus.AUTO_ACCEPTED.value, ConsensusStatus.ACCEPTED.value]
    ]

    # Build hierarchy
    hierarchy = export_service._build_hierarchy_from_synthesis(session, accepted_items)

    return {
        "session_id": str(session_id),
        "tier": session.tier,
        "status": session.status,
        "hierarchy": hierarchy,
        "would_create_files": _count_files_to_create(hierarchy),
    }


def _count_files_to_create(hierarchy: dict) -> int:
    """Count total files that would be created."""
    count = 1  # project-summary.md
    for epic in hierarchy.get("epics", []):
        count += 1  # epic.md
        for feature in epic.get("features", []):
            count += 1  # feature.md
            count += len(feature.get("stories", []))  # STORY-{NNN}.md
    return count


# ============================================================================
# TIER CONFIGURATION (Week 87) - Granular Tier Selection
# ============================================================================

@router.get("/sessions/{session_id}/tier-config")
async def get_tier_config(session_id: UUID, db = Depends(get_db)):
    """
    Get full tier configuration hierarchy for a session.

    Returns tree structure with tier info for each epic, feature, and story.
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.get_hierarchy_config(session_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.put("/sessions/{session_id}/tier-config")
async def update_session_tier_settings(
    session_id: UUID,
    settings: dict,
    db = Depends(get_db)
):
    """
    Update session-level tier settings.

    Settings can include:
    - tier: Default tier for the session (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)
    - allow_epic_override: Y/N - Allow tier override at epic level
    - allow_feature_override: Y/N - Allow tier override at feature level
    - allow_story_override: Y/N - Allow tier override at story level
    - tier_config_locked: Y/N - Lock all tier changes
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.update_session_tier_settings(session_id, settings)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.patch("/items/{item_id}/tier")
async def set_item_tier_override(
    item_id: UUID,
    tier: Optional[str] = None,
    cascade: bool = True,
    db = Depends(get_db)
):
    """
    Set tier override for a specific item (epic, feature, or story).

    Args:
        item_id: The consensus item ID to update
        tier: The tier to set (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)
              Use null/None to clear override and inherit from parent
        cascade: Whether to update children's effective tiers (default: True)
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.set_item_tier_override(item_id, tier, cascade)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/sessions/{session_id}/tier-config/bulk")
async def bulk_set_tier_overrides(
    session_id: UUID,
    overrides: dict,
    db = Depends(get_db)
):
    """
    Set tier overrides for multiple items at once.

    Request body should be a dict of item_id -> tier:
    {
        "item-uuid-1": "PREMIUM",
        "item-uuid-2": "FREE",
        "item-uuid-3": null  // Clear override
    }
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.bulk_set_tier_overrides(session_id, overrides)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/sessions/{session_id}/tier-config/reset")
async def reset_all_tier_overrides(session_id: UUID, db = Depends(get_db)):
    """
    Reset all tier overrides to inherit from session default.
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.reset_all_overrides(session_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/sessions/{session_id}/tier-config/preview")
async def preview_expected_outcomes(
    session_id: UUID,
    tier_overrides: Optional[dict] = None,
    db = Depends(get_db)
):
    """
    Preview expected outcomes for a session with optional tier overrides.

    Returns summary of expected confidence, cost, and LLM counts
    without actually applying the changes.

    Request body (optional):
    {
        "item-uuid-1": "PREMIUM",
        "item-uuid-2": "FREE"
    }
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.get_expected_outcomes_preview(session_id, tier_overrides)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/items/{item_id}/tier-comparison")
async def compare_tiers_for_item(item_id: UUID, db = Depends(get_db)):
    """
    Compare all tier options for a specific item.

    Returns expected outcomes for each tier to help user decide.
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.compare_tiers_for_item(item_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/sessions/{session_id}/tier-config/recalculate")
async def recalculate_hierarchy_tiers(session_id: UUID, db = Depends(get_db)):
    """
    Recalculate effective tiers for all items in a session.

    Use this after making changes to refresh the tier inheritance.
    """
    from app.services.tier_config_service import TierConfigService
    service = TierConfigService(db)
    result = service.recalculate_hierarchy_tiers(session_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


# ============================================================================
# WEEK 100: CYCLE 0 (STATIC ANALYSIS) ENDPOINTS
# ============================================================================

@router.get("/sessions/{session_id}/cycle-0")
async def get_cycle_0_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get Cycle 0 (Static Analysis) status and results.

    Returns static analysis metrics, business rules detected,
    NFR findings, and compliance status.
    """
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": str(session_id),
        "cycle_0_completed": session.cycle_0_completed_at is not None,
        "completed_at": session.cycle_0_completed_at.isoformat() if session.cycle_0_completed_at else None,
        "static_analysis_id": session.static_analysis_id,
        "metrics": {
            "domain_coverage": session.static_domain_coverage,
            "nfr_coverage": session.static_nfr_coverage,
            "compliance_score": session.static_compliance_score,
        },
        "counts": {
            "business_rules": session.static_business_rules_count,
            "nfr_detections": session.static_nfr_count,
            "compliance_violations": session.static_compliance_violations_count,
            "high_confidence_findings": session.static_high_confidence_count,
            "low_confidence_findings": session.static_low_confidence_count,
        },
        "tier_includes_static": session.tier not in ["FREE"],
    }


@router.post("/sessions/{session_id}/cycle-0/run")
async def run_cycle_0(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Run Cycle 0 (Static Analysis) for a session.

    Executes static analysis including:
    - Program slicing
    - Variable classification
    - Business rule extraction
    - NFR detection
    - Compliance checking
    """
    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check tier eligibility
    from app.models.deep_extraction import tier_includes_static_analysis
    if not tier_includes_static_analysis(ExtractionTier(session.tier)):
        raise HTTPException(
            status_code=400,
            detail=f"Tier {session.tier} does not include static analysis. Upgrade to BASIC or higher."
        )

    result = await service.run_cycle_0(session_id)
    return result


# ============================================================================
# WEEK 100: STATIC-LLM CONFLICT ENDPOINTS
# ============================================================================

@router.get("/sessions/{session_id}/static-llm-conflicts")
async def get_static_llm_conflicts(
    session_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status: pending, auto_resolved, human_review, resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Static-LLM conflicts for a session.

    Returns conflicts between static analysis (Cycle 0) and LLM results,
    including confidence threshold violations (72.5%).
    """
    from sqlalchemy import select
    from app.models.deep_extraction import StaticLLMConflict

    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build query
    query = select(StaticLLMConflict).where(StaticLLMConflict.session_id == session_id)

    if status:
        query = query.where(StaticLLMConflict.status == status)
    if severity:
        query = query.where(StaticLLMConflict.severity == severity)
    if conflict_type:
        query = query.where(StaticLLMConflict.conflict_type == conflict_type)

    query = query.order_by(StaticLLMConflict.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    conflicts = result.scalars().all()

    return {
        "session_id": str(session_id),
        "total_conflicts": session.total_conflicts or 0,
        "auto_resolved": session.conflicts_auto_resolved or 0,
        "pending_review": session.conflicts_pending_review or 0,
        "human_resolved": session.conflicts_human_resolved or 0,
        "conflicts": [
            {
                "id": str(c.id),
                "item_id": c.item_id,
                "item_type": c.item_type,
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "static": {
                    "classification": c.static_classification,
                    "confidence": c.static_confidence,
                    "data": c.static_data,
                    "source_file": c.static_source_file,
                    "source_line": c.static_source_line,
                },
                "llm": {
                    "classification": c.llm_classification,
                    "confidence": c.llm_confidence,
                    "data": c.llm_data,
                    "provider": c.llm_provider,
                    "model": c.llm_model,
                },
                "description": c.description,
                "impact_assessment": c.impact_assessment,
                "recommendations": c.recommendations,
                "status": c.status,
                "resolution": c.resolution,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                "resolved_by": c.resolved_by,
                "resolution_notes": c.resolution_notes,
                "final_value": c.final_value,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in conflicts
        ],
    }


@router.get("/static-llm-conflicts/{conflict_id}")
async def get_static_llm_conflict(
    conflict_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific Static-LLM conflict with full details."""
    from sqlalchemy import select
    from app.models.deep_extraction import StaticLLMConflict

    result = await db.execute(
        select(StaticLLMConflict).where(StaticLLMConflict.id == conflict_id)
    )
    conflict = result.scalar_one_or_none()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    return {
        "id": str(conflict.id),
        "session_id": str(conflict.session_id),
        "item_id": conflict.item_id,
        "item_type": conflict.item_type,
        "conflict_type": conflict.conflict_type,
        "severity": conflict.severity,
        "static": {
            "classification": conflict.static_classification,
            "confidence": conflict.static_confidence,
            "data": conflict.static_data,
            "source_file": conflict.static_source_file,
            "source_line": conflict.static_source_line,
        },
        "llm": {
            "classification": conflict.llm_classification,
            "confidence": conflict.llm_confidence,
            "data": conflict.llm_data,
            "provider": conflict.llm_provider,
            "model": conflict.llm_model,
        },
        "description": conflict.description,
        "impact_assessment": conflict.impact_assessment,
        "recommendations": conflict.recommendations,
        "status": conflict.status,
        "resolution": conflict.resolution,
        "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
        "resolved_by": conflict.resolved_by,
        "resolution_notes": conflict.resolution_notes,
        "final_value": conflict.final_value,
        "final_classification": conflict.final_classification,
        "final_confidence": conflict.final_confidence,
        "created_at": conflict.created_at.isoformat() if conflict.created_at else None,
        "updated_at": conflict.updated_at.isoformat() if conflict.updated_at else None,
    }


@router.post("/static-llm-conflicts/{conflict_id}/resolve")
async def resolve_static_llm_conflict(
    conflict_id: UUID,
    resolution: str = Query(..., description="Resolution type: human_selected_static, human_selected_llm, human_merged, human_rejected_both"),
    final_value: Optional[dict] = None,
    notes: str = Query("", description="Resolution notes"),
    resolved_by: str = Query("human", description="User ID or 'human'"),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve a Static-LLM conflict with human decision.

    Resolution options:
    - human_selected_static: Accept static analysis result
    - human_selected_llm: Accept LLM result
    - human_merged: Accept merged/custom result (provide final_value)
    - human_rejected_both: Reject both results
    """
    from sqlalchemy import select
    from datetime import datetime
    from app.models.deep_extraction import (
        StaticLLMConflict,
        StaticLLMConflictStatus,
        StaticLLMConflictResolution,
        ConflictResolutionHistory,
        ExtractionSession,
    )

    # Validate resolution type
    valid_resolutions = [r.value for r in StaticLLMConflictResolution]
    if resolution not in valid_resolutions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resolution. Must be one of: {valid_resolutions}"
        )

    # Get conflict
    result = await db.execute(
        select(StaticLLMConflict).where(StaticLLMConflict.id == conflict_id)
    )
    conflict = result.scalar_one_or_none()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if conflict.status == StaticLLMConflictStatus.RESOLVED.value:
        raise HTTPException(status_code=400, detail="Conflict already resolved")

    # Store previous state for history
    previous_status = conflict.status
    previous_resolution = conflict.resolution

    # Update conflict
    conflict.status = StaticLLMConflictStatus.RESOLVED.value
    conflict.resolution = resolution
    conflict.resolved_at = datetime.utcnow()
    conflict.resolved_by = resolved_by
    conflict.resolution_notes = notes

    # Set final value based on resolution
    if resolution == StaticLLMConflictResolution.HUMAN_SELECTED_STATIC.value:
        conflict.final_value = conflict.static_data
        conflict.final_classification = conflict.static_classification
        conflict.final_confidence = conflict.static_confidence
    elif resolution == StaticLLMConflictResolution.HUMAN_SELECTED_LLM.value:
        conflict.final_value = conflict.llm_data
        conflict.final_classification = conflict.llm_classification
        conflict.final_confidence = conflict.llm_confidence
    elif resolution == StaticLLMConflictResolution.HUMAN_MERGED.value:
        if not final_value:
            raise HTTPException(status_code=400, detail="final_value required for merged resolution")
        conflict.final_value = final_value
        conflict.final_classification = final_value.get("classification")
        conflict.final_confidence = final_value.get("confidence", 0.8)

    # Create history entry
    history = ConflictResolutionHistory(
        conflict_id=conflict_id,
        action="resolved",
        action_by=resolved_by,
        action_data={"resolution": resolution, "notes": notes},
        previous_status=previous_status,
        new_status=conflict.status,
        previous_resolution=previous_resolution,
        new_resolution=conflict.resolution,
        notes=notes,
    )
    db.add(history)

    # Update session counts
    session_result = await db.execute(
        select(ExtractionSession).where(ExtractionSession.id == conflict.session_id)
    )
    session = session_result.scalar_one_or_none()
    if session:
        session.conflicts_pending_review = max(0, (session.conflicts_pending_review or 0) - 1)
        session.conflicts_human_resolved = (session.conflicts_human_resolved or 0) + 1

    await db.commit()
    await db.refresh(conflict)

    return {
        "id": str(conflict.id),
        "status": conflict.status,
        "resolution": conflict.resolution,
        "resolved_at": conflict.resolved_at.isoformat(),
        "resolved_by": conflict.resolved_by,
        "final_value": conflict.final_value,
        "final_classification": conflict.final_classification,
        "final_confidence": conflict.final_confidence,
    }


@router.post("/sessions/{session_id}/static-llm-conflicts/bulk-resolve")
async def bulk_resolve_static_llm_conflicts(
    session_id: UUID,
    resolutions: list,
    resolved_by: str = Query("human"),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk resolve multiple Static-LLM conflicts.

    Request body:
    [
        {"conflict_id": "uuid", "resolution": "human_selected_static", "notes": "..."},
        {"conflict_id": "uuid", "resolution": "human_selected_llm"}
    ]
    """
    from sqlalchemy import select
    from datetime import datetime
    from app.models.deep_extraction import (
        StaticLLMConflict,
        StaticLLMConflictStatus,
        StaticLLMConflictResolution,
        ConflictResolutionHistory,
        ExtractionSession,
    )

    resolved_count = 0
    errors = []

    for item in resolutions:
        conflict_id = item.get("conflict_id")
        resolution = item.get("resolution")
        notes = item.get("notes", "")

        try:
            result = await db.execute(
                select(StaticLLMConflict).where(StaticLLMConflict.id == conflict_id)
            )
            conflict = result.scalar_one_or_none()

            if not conflict:
                errors.append({"conflict_id": conflict_id, "error": "Not found"})
                continue

            if conflict.session_id != session_id:
                errors.append({"conflict_id": conflict_id, "error": "Wrong session"})
                continue

            # Update conflict
            conflict.status = StaticLLMConflictStatus.RESOLVED.value
            conflict.resolution = resolution
            conflict.resolved_at = datetime.utcnow()
            conflict.resolved_by = resolved_by
            conflict.resolution_notes = notes

            # Set final value
            if resolution == StaticLLMConflictResolution.HUMAN_SELECTED_STATIC.value:
                conflict.final_value = conflict.static_data
                conflict.final_classification = conflict.static_classification
                conflict.final_confidence = conflict.static_confidence
            elif resolution == StaticLLMConflictResolution.HUMAN_SELECTED_LLM.value:
                conflict.final_value = conflict.llm_data
                conflict.final_classification = conflict.llm_classification
                conflict.final_confidence = conflict.llm_confidence

            # Create history
            history = ConflictResolutionHistory(
                conflict_id=conflict_id,
                action="bulk_resolved",
                action_by=resolved_by,
                action_data={"resolution": resolution},
                previous_status="pending",
                new_status=conflict.status,
                new_resolution=conflict.resolution,
            )
            db.add(history)
            resolved_count += 1

        except Exception as e:
            errors.append({"conflict_id": conflict_id, "error": str(e)})

    # Update session counts
    session_result = await db.execute(
        select(ExtractionSession).where(ExtractionSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if session:
        session.conflicts_pending_review = max(0, (session.conflicts_pending_review or 0) - resolved_count)
        session.conflicts_human_resolved = (session.conflicts_human_resolved or 0) + resolved_count

    await db.commit()

    return {
        "session_id": str(session_id),
        "resolved_count": resolved_count,
        "error_count": len(errors),
        "errors": errors,
    }


@router.get("/sessions/{session_id}/static-llm-conflicts/summary")
async def get_static_llm_conflicts_summary(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary of Static-LLM conflicts for a session.

    Provides dashboard-friendly statistics including
    counts by type, severity, and resolution status.
    """
    from sqlalchemy import select, func
    from app.models.deep_extraction import StaticLLMConflict

    service = DeepExtractionService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Count by status
    status_result = await db.execute(
        select(
            StaticLLMConflict.status,
            func.count(StaticLLMConflict.id)
        ).where(
            StaticLLMConflict.session_id == session_id
        ).group_by(StaticLLMConflict.status)
    )
    by_status = {row[0]: row[1] for row in status_result.fetchall()}

    # Count by severity
    severity_result = await db.execute(
        select(
            StaticLLMConflict.severity,
            func.count(StaticLLMConflict.id)
        ).where(
            StaticLLMConflict.session_id == session_id
        ).group_by(StaticLLMConflict.severity)
    )
    by_severity = {row[0]: row[1] for row in severity_result.fetchall()}

    # Count by type
    type_result = await db.execute(
        select(
            StaticLLMConflict.conflict_type,
            func.count(StaticLLMConflict.id)
        ).where(
            StaticLLMConflict.session_id == session_id
        ).group_by(StaticLLMConflict.conflict_type)
    )
    by_type = {row[0]: row[1] for row in type_result.fetchall()}

    # Count by resolution
    resolution_result = await db.execute(
        select(
            StaticLLMConflict.resolution,
            func.count(StaticLLMConflict.id)
        ).where(
            StaticLLMConflict.session_id == session_id,
            StaticLLMConflict.resolution.isnot(None)
        ).group_by(StaticLLMConflict.resolution)
    )
    by_resolution = {row[0]: row[1] for row in resolution_result.fetchall()}

    return {
        "session_id": str(session_id),
        "total_conflicts": session.total_conflicts or 0,
        "by_status": by_status,
        "by_severity": by_severity,
        "by_type": by_type,
        "by_resolution": by_resolution,
        "progress": {
            "pending": by_status.get("pending", 0),
            "auto_resolved": session.conflicts_auto_resolved or 0,
            "human_resolved": session.conflicts_human_resolved or 0,
            "completion_percentage": round(
                ((session.conflicts_auto_resolved or 0) + (session.conflicts_human_resolved or 0))
                / max(session.total_conflicts or 1, 1) * 100,
                1
            ),
        },
        "confidence_threshold": 0.725,  # 72.5%
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check for the deep extraction service."""
    return {
        "status": "healthy",
        "service": "deep-extraction",
        "version": "5.0.0",  # Updated for Week 100 - Static-LLM Conflicts
        "tiers_available": [t.value for t in ExtractionTier],
        "features": [
            "bulk_operations",
            "auto_resolve",
            "tier_upgrade",
            "delta_tracking",
            "pricing_calculator",
            "onboarding_recommendations",
            "claude_opus_synthesis",
            "confidence_explanations",
            "project_export",
            "granular_tier_selection",
            "tier_inheritance",
            "expected_outcomes_preview",
            "cycle_0_static_analysis",  # NEW Week 100
            "static_llm_conflicts",  # NEW Week 100
            "72.5_percent_threshold",  # NEW Week 100
            "conflict_resolution_history",  # NEW Week 100
        ],
    }
