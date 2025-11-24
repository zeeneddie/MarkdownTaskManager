"""
Self-Navigating API Endpoints

Enhanced API for the Experience Consultant.
Part of AgentEvolver Phase B (Week 19).

Provides:
- Experience search with similarity scoring
- Pattern search with applicability scoring
- Failure search with risk scoring
- Comprehensive guidance endpoint
- Outcome logging

These endpoints are specifically designed for the TypeScript
ExperienceConsultant client.

Author: Claude Code (Week 19 Day 5)
Date: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import uuid

from app.services.pattern_matcher_service import (
    get_pattern_matcher,
    PatternMatcherService,
    ExperienceSearchResult,
    PatternSearchResult,
    FailureSearchResult
)
from app.services.experience_store_service import (
    get_experience_store,
    Experience,
    SuccessfulPattern,
    FailureAnalysis,
    KeyDecision,
    WorkType,
    AgentRole,
    Outcome
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evolution", tags=["self-navigating"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExperienceSearchRequest(BaseModel):
    """Request for experience search"""
    query: str = Field(..., description="Search query (task description)")
    work_type: Optional[str] = Field(None, description="Filter by work type")
    agent_role: Optional[str] = Field(None, description="Filter by agent role")
    limit: int = Field(default=10, ge=1, le=50, description="Max results")
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0, description="Min similarity threshold")
    min_quality: Optional[float] = Field(None, ge=0.0, le=100.0, description="Min quality score")


class ExperienceSearchResponse(BaseModel):
    """Response with experience search results"""
    experiences: List[Dict[str, Any]]
    query: str
    count: int
    filters_applied: Dict[str, Any]


class PatternSearchRequest(BaseModel):
    """Request for pattern search"""
    query: str = Field(..., description="Search query")
    work_type: Optional[str] = Field(None, description="Filter by work type")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0, description="Min similarity threshold")
    min_success_rate: float = Field(default=0.6, ge=0.0, le=1.0, description="Min success rate")


class PatternSearchResponse(BaseModel):
    """Response with pattern search results"""
    patterns: List[Dict[str, Any]]
    query: str
    count: int


class FailureSearchRequest(BaseModel):
    """Request for failure search"""
    query: str = Field(..., description="Search query")
    work_type: Optional[str] = Field(None, description="Filter by work type")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    min_similarity: float = Field(default=0.4, ge=0.0, le=1.0, description="Min similarity threshold")


class FailureSearchResponse(BaseModel):
    """Response with failure search results"""
    failures: List[Dict[str, Any]]
    query: str
    count: int


class ComprehensiveSearchRequest(BaseModel):
    """Request for comprehensive search across all types"""
    query: str = Field(..., description="Search query")
    work_type: Optional[str] = Field(None, description="Filter by work type")
    agent_role: Optional[str] = Field(None, description="Filter by agent role")
    max_experiences: int = Field(default=5, ge=0, le=20)
    max_patterns: int = Field(default=3, ge=0, le=10)
    max_failures: int = Field(default=3, ge=0, le=10)
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0)


class ComprehensiveSearchResponse(BaseModel):
    """Response with comprehensive search results"""
    experiences: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float
    query: str


class LogOutcomeRequest(BaseModel):
    """Request to log a task outcome"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_role: str = Field(..., description="Agent role")
    work_type: str = Field(..., description="Work type")
    task_id: str = Field(..., description="Task identifier")
    task_description: str = Field(..., description="Task description")
    approach: str = Field(..., description="Approach taken")
    outcome: str = Field(..., description="Outcome: SUCCESS, PARTIAL, FAILURE")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Quality score 0-100")
    lessons_learned: List[str] = Field(default=[], description="Lessons learned")
    key_decisions: List[Dict[str, Any]] = Field(default=[], description="Key decisions made")
    duration: Optional[int] = Field(None, description="Duration in seconds")


class LogOutcomeResponse(BaseModel):
    """Response after logging outcome"""
    experience_id: str
    logged: bool
    message: str


# ============================================================================
# Experience Search Endpoint
# ============================================================================

@router.post("/experiences/search", response_model=ExperienceSearchResponse)
async def search_experiences(request: ExperienceSearchRequest):
    """
    Search for similar experiences.

    Uses semantic similarity matching with weighted scoring:
    - Text similarity (50%)
    - Context match (30%)
    - Quality factor (20%)
    """
    try:
        matcher = get_pattern_matcher()

        results = matcher.search_experiences(
            query=request.query,
            work_type=request.work_type,
            agent_role=request.agent_role,
            limit=request.limit,
            min_similarity=request.min_similarity,
            min_quality=request.min_quality
        )

        experiences = []
        for result in results:
            exp = result.experience
            experiences.append({
                "id": exp.id,
                "agent_id": exp.agent_id,
                "agent_role": exp.agent_role.value if isinstance(exp.agent_role, AgentRole) else str(exp.agent_role),
                "work_type": exp.work_type.value if isinstance(exp.work_type, WorkType) else str(exp.work_type),
                "task_description": exp.task_description,
                "approach": exp.approach,
                "outcome": exp.outcome.value if isinstance(exp.outcome, Outcome) else str(exp.outcome),
                "quality_score": exp.quality_score,
                "lessons_learned": exp.lessons_learned,
                "key_decisions": [
                    {
                        "decision": kd.decision,
                        "reasoning": kd.reasoning,
                        "alternatives": kd.alternatives,
                        "outcome": kd.outcome,
                        "impact_score": kd.impact_score
                    }
                    for kd in (exp.key_decisions or [])
                ],
                "duration": exp.duration,
                "created_at": exp.timestamp.isoformat() if exp.timestamp else None,
                "similarity": result.similarity,
                "relevance_factors": result.relevance_factors
            })

        return ExperienceSearchResponse(
            experiences=experiences,
            query=request.query,
            count=len(experiences),
            filters_applied={
                "work_type": request.work_type,
                "agent_role": request.agent_role,
                "min_similarity": request.min_similarity,
                "min_quality": request.min_quality
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching experiences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pattern Search Endpoint
# ============================================================================

@router.post("/patterns/search", response_model=PatternSearchResponse)
async def search_patterns(request: PatternSearchRequest):
    """
    Search for applicable patterns.

    Uses similarity matching with:
    - Text similarity (40%)
    - Work type match (30%)
    - Success rate (30%)
    """
    try:
        matcher = get_pattern_matcher()

        results = matcher.search_patterns(
            query=request.query,
            work_type=request.work_type,
            limit=request.limit,
            min_similarity=request.min_similarity,
            min_success_rate=request.min_success_rate
        )

        patterns = []
        for result in results:
            pattern = result.pattern
            patterns.append({
                "id": pattern.id,
                "name": pattern.name,
                "description": pattern.description,
                "work_types": [wt.value if isinstance(wt, WorkType) else str(wt) for wt in (pattern.work_types or [])],
                "applicable_contexts": pattern.applicable_contexts,
                "steps": pattern.steps,
                "success_rate": pattern.success_rate,
                "usage_count": pattern.success_count + pattern.failure_count,
                "last_used": pattern.last_used.isoformat() if pattern.last_used else None,
                "similarity": result.similarity,
                "applicability_score": result.applicability_score
            })

        return PatternSearchResponse(
            patterns=patterns,
            query=request.query,
            count=len(patterns)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Failure Search Endpoint
# ============================================================================

@router.post("/failures/search", response_model=FailureSearchResponse)
async def search_failures(request: FailureSearchRequest):
    """
    Search for relevant failure analyses.

    Uses similarity matching with risk scoring to identify
    potential pitfalls and prevention strategies.
    """
    try:
        matcher = get_pattern_matcher()

        results = matcher.search_failures(
            query=request.query,
            work_type=request.work_type,
            limit=request.limit,
            min_similarity=request.min_similarity
        )

        failures = []
        for result in results:
            failure = result.failure
            failures.append({
                "id": failure.id,
                "agent_id": failure.agent_id,
                "work_type": failure.work_type.value if isinstance(failure.work_type, WorkType) else str(failure.work_type),
                "failure_type": failure.failure_type.value if hasattr(failure.failure_type, 'value') else str(failure.failure_type),
                "description": getattr(failure, 'description', failure.root_cause),
                "root_cause": failure.root_cause,
                "contributing_factors": failure.contributing_factors,
                "prevention_strategies": failure.prevention_strategies,
                "similar_failures": failure.similar_failures,
                "similarity": result.similarity,
                "risk_score": result.risk_score
            })

        return FailureSearchResponse(
            failures=failures,
            query=request.query,
            count=len(failures)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching failures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Comprehensive Search Endpoint (Main Guidance API)
# ============================================================================

@router.post("/comprehensive-search", response_model=ComprehensiveSearchResponse)
async def comprehensive_search(request: ComprehensiveSearchRequest):
    """
    Comprehensive search across experiences, patterns, and failures.

    This is the main endpoint for the Experience Consultant.
    Returns:
    - Relevant experiences with similarity scores
    - Applicable patterns with success rates
    - Failure warnings with risk scores
    - Generated recommendations
    - Overall confidence score
    """
    try:
        matcher = get_pattern_matcher()

        search_results = matcher.comprehensive_search(
            query=request.query,
            work_type=request.work_type,
            agent_role=request.agent_role,
            max_experiences=request.max_experiences,
            max_patterns=request.max_patterns,
            max_failures=request.max_failures,
            min_similarity=request.min_similarity
        )

        # Format experiences
        experiences = []
        for result in search_results['experiences']:
            exp = result.experience
            experiences.append({
                "id": exp.id,
                "agent_id": exp.agent_id,
                "agent_role": exp.agent_role.value if isinstance(exp.agent_role, AgentRole) else str(exp.agent_role),
                "work_type": exp.work_type.value if isinstance(exp.work_type, WorkType) else str(exp.work_type),
                "task_description": exp.task_description,
                "approach": exp.approach,
                "outcome": exp.outcome.value if isinstance(exp.outcome, Outcome) else str(exp.outcome),
                "quality_score": exp.quality_score,
                "similarity": result.similarity
            })

        # Format patterns
        patterns = []
        for result in search_results['patterns']:
            pattern = result.pattern
            patterns.append({
                "id": pattern.id,
                "name": pattern.name,
                "description": pattern.description,
                "steps": pattern.steps,
                "success_rate": pattern.success_rate,
                "similarity": result.similarity
            })

        # Format failures
        failures = []
        for result in search_results['failures']:
            failure = result.failure
            failures.append({
                "id": failure.id,
                "failure_type": failure.failure_type.value if hasattr(failure.failure_type, 'value') else str(failure.failure_type),
                "description": getattr(failure, 'description', failure.root_cause),
                "root_cause": failure.root_cause,
                "prevention_strategies": failure.prevention_strategies,
                "similarity": result.similarity,
                "risk_score": result.risk_score
            })

        # Generate recommendations
        recommendations = _generate_recommendations(experiences, patterns, failures)

        # Calculate confidence score
        confidence = _calculate_confidence(experiences, patterns, failures)

        return ComprehensiveSearchResponse(
            experiences=experiences,
            patterns=patterns,
            failures=failures,
            recommendations=recommendations,
            confidence_score=confidence,
            query=request.query
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in comprehensive search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Outcome Logging Endpoint
# ============================================================================

@router.post("/experiences", response_model=LogOutcomeResponse)
async def log_outcome(request: LogOutcomeRequest):
    """
    Log a task outcome for future learning.

    This is part of Self-Attributing: recording outcomes for
    experience-based learning.
    """
    try:
        store = get_experience_store()

        # Convert key decisions
        key_decisions = []
        for kd in request.key_decisions:
            key_decisions.append(KeyDecision(
                decision=kd.get("decision", ""),
                reasoning=kd.get("reasoning", ""),
                alternatives=kd.get("alternatives", []),
                outcome=kd.get("outcome", "neutral"),
                impact_score=kd.get("impact_score", 0.5)
            ))

        # Map outcome string to Outcome enum
        outcome_map = {
            "SUCCESS": Outcome.SUCCESS,
            "PARTIAL": Outcome.PARTIAL,
            "FAILURE": Outcome.FAILURE
        }
        outcome = outcome_map.get(request.outcome.upper(), Outcome.PARTIAL)

        experience = Experience(
            id=str(uuid.uuid4()),
            agent_id=request.agent_id,
            agent_role=AgentRole(request.agent_role),
            work_type=WorkType(request.work_type),
            task_description=request.task_description,
            approach=request.approach,
            outcome=outcome,
            lessons_learned=request.lessons_learned,
            key_decisions=key_decisions,
            duration=request.duration or 0,
            quality_score=request.quality_score,
            timestamp=datetime.utcnow(),
            metadata={"task_id": request.task_id}
        )

        experience_id = await store.add_experience(experience)

        return LogOutcomeResponse(
            experience_id=experience_id,
            logged=True,
            message=f"Experience logged successfully with ID {experience_id}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error logging outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

def _generate_recommendations(
    experiences: List[Dict],
    patterns: List[Dict],
    failures: List[Dict]
) -> List[str]:
    """Generate recommendations from search results"""
    recommendations = []

    # From successful experiences
    successful_exps = [e for e in experiences if e.get('outcome') == 'SUCCESS' and e.get('quality_score', 0) >= 70]
    if successful_exps:
        top_exp = successful_exps[0]
        recommendations.append(
            f"Consider approach from similar successful task: \"{top_exp.get('approach', '')[:100]}...\""
        )

    # From patterns
    for pattern in patterns[:2]:
        if pattern.get('success_rate', 0) >= 0.7:
            recommendations.append(
                f"Apply \"{pattern.get('name')}\" pattern ({int(pattern.get('success_rate', 0) * 100)}% success rate)"
            )

    # From failures (warnings)
    for failure in failures:
        prevention = failure.get('prevention_strategies', [])
        if prevention:
            recommendations.append(
                f"AVOID: {failure.get('failure_type', 'Unknown')} - {prevention[0]}"
            )

    # Default if no data
    if not recommendations:
        recommendations.append("No specific historical guidance available. Proceed with standard approach.")
        recommendations.append("Consider documenting this experience for future reference.")

    return recommendations


def _calculate_confidence(
    experiences: List[Dict],
    patterns: List[Dict],
    failures: List[Dict]
) -> float:
    """Calculate confidence score based on data quality"""
    score = 0.3  # Base confidence

    # More experiences = higher confidence
    if experiences:
        score += min(0.2, len(experiences) * 0.04)
        # High similarity experiences boost confidence
        avg_similarity = sum(e.get('similarity', 0) for e in experiences) / len(experiences)
        score += avg_similarity * 0.15
        # Successful experiences boost more
        success_rate = len([e for e in experiences if e.get('outcome') == 'SUCCESS']) / len(experiences)
        score += success_rate * 0.1

    # Patterns boost confidence
    if patterns:
        score += min(0.15, len(patterns) * 0.05)
        avg_success_rate = sum(p.get('success_rate', 0) for p in patterns) / len(patterns)
        score += avg_success_rate * 0.1

    # Failures (knowing what to avoid) increase confidence
    if failures:
        score += min(0.1, len(failures) * 0.03)

    return min(1.0, score)


# ============================================================================
# Health Check
# ============================================================================

@router.get("/self-navigating/health")
async def self_navigating_health():
    """Check self-navigating service health"""
    try:
        matcher = get_pattern_matcher()
        store = get_experience_store()

        return {
            "status": "healthy",
            "services": {
                "pattern_matcher": "available" if matcher else "unavailable",
                "experience_store": "available" if store else "unavailable"
            },
            "capabilities": [
                "experience_search",
                "pattern_search",
                "failure_search",
                "comprehensive_search",
                "outcome_logging"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
