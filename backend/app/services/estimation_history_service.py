"""
Estimation History Service (Async)

Handles logging and retrieval of estimation data for ML training.
Automatically logs all estimation API calls and provides methods
to record actual results for training data.

Week 143: Vector DB Integration for context-aware estimation.

Author: Claude Code (Week 15 Day 5)
Date: 2025-11-21
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.models.estimation_history import (
    EstimationProject,
    FunctionPointEstimate,
    StoryPointEstimate,
    MLModelVersion,
    TechStack
)

# Week 143: Vector DB Integration
logger = logging.getLogger(__name__)

try:
    from app.services.chroma_service import ChromaService
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaService not available - Vector DB context disabled for estimation")


class EstimationHistoryService:
    """Async service for managing estimation history and ML training data"""

    def __init__(self, db: AsyncSession, project_id: int = 1000):
        self.db = db
        self.project_id = project_id  # Week 143: Vector DB project reference

        # Week 143: Vector DB service (lazy initialization)
        self._chroma_service: Optional["ChromaService"] = None

    def _get_chroma_service(self) -> Optional["ChromaService"]:
        """Get or create ChromaDB service instance (lazy init)."""
        if not CHROMA_AVAILABLE:
            return None
        if self._chroma_service is None:
            try:
                self._chroma_service = ChromaService()
                logger.info("ChromaDB service initialized for EstimationHistoryService")
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}. Vector context disabled.")
                return None
        return self._chroma_service

    def _fetch_estimation_context(
        self,
        estimation_type: str,  # "fp" or "sp"
        tech_stack: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch relevant context from Vector DB for estimation calibration.

        Args:
            estimation_type: "fp" for Function Points, "sp" for Story Points
            tech_stack: Technology stack for context filtering
            topics: Optional list of topics to search for

        Returns:
            Dict with similar estimates, patterns, and calibration hints
        """
        chroma = self._get_chroma_service()
        if not chroma:
            return None

        try:
            context = {
                "similar_estimates": [],
                "complexity_patterns": [],
                "calibration_hints": [],
                "tech_stack_context": []
            }

            # Build queries based on estimation type
            queries = []
            if estimation_type == "fp":
                queries = [
                    "function point estimation patterns",
                    "IFPUG complexity assessment",
                    "legacy code migration effort"
                ]
            elif estimation_type == "sp":
                queries = [
                    "story point estimation",
                    "agile estimation patterns",
                    "sprint velocity calculation"
                ]

            # Add tech stack specific queries
            if tech_stack:
                queries.append(f"{tech_stack} estimation patterns")
                queries.append(f"{tech_stack} complexity factors")

            # Add topic-specific queries
            if topics:
                for topic in topics[:2]:
                    queries.append(f"{topic} estimation")

            # Fetch from Vector DB
            for query in queries[:5]:
                results = chroma.query_project_knowledge(
                    project_id=self.project_id,
                    query=query,
                    n_results=3
                )

                if results and "documents" in results:
                    for doc in results.get("documents", [[]])[0]:
                        if doc and len(doc) > 50:
                            doc_lower = doc.lower()
                            if any(x in doc_lower for x in ["function point", "fp", "ifpug", "story point", "sp", "estimate"]):
                                if doc not in context["similar_estimates"]:
                                    context["similar_estimates"].append(doc[:400])
                            elif any(x in doc_lower for x in ["complex", "high", "medium", "low"]):
                                if doc not in context["complexity_patterns"]:
                                    context["complexity_patterns"].append(doc[:400])
                            elif tech_stack and tech_stack.lower() in doc_lower:
                                if doc not in context["tech_stack_context"]:
                                    context["tech_stack_context"].append(doc[:400])

            # Limit results
            for key in context:
                context[key] = context[key][:3]

            total_items = sum(len(v) for v in context.values())
            if total_items > 0:
                logger.info(f"Fetched {total_items} context items for {estimation_type} estimation")
                return context

            return None

        except Exception as e:
            logger.warning(f"Error fetching estimation context: {e}")
            return None

    def get_estimation_context(
        self,
        estimation_type: str,
        tech_stack: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Public method to get Vector DB context for estimation."""
        return self._fetch_estimation_context(estimation_type, tech_stack)

    # =========================================================================
    # Project Management
    # =========================================================================

    async def get_or_create_project(
        self,
        name: str,
        description: Optional[str] = None,
        external_id: Optional[str] = None,
        **kwargs
    ) -> EstimationProject:
        """Get existing project or create new one"""
        # Try to find by external_id first
        if external_id:
            result = await self.db.execute(
                select(EstimationProject).where(
                    EstimationProject.external_id == external_id
                )
            )
            project = result.scalar_one_or_none()
            if project:
                return project

        # Try to find by name
        result = await self.db.execute(
            select(EstimationProject).where(EstimationProject.name == name)
        )
        project = result.scalar_one_or_none()

        if project:
            return project

        # Convert TechStack enum to string value if present
        if 'tech_stack' in kwargs and kwargs['tech_stack'] is not None:
            if isinstance(kwargs['tech_stack'], TechStack):
                kwargs['tech_stack'] = kwargs['tech_stack'].value

        # Create new project
        project = EstimationProject(
            name=name,
            description=description,
            external_id=external_id,
            **kwargs
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update_project_metadata(
        self,
        project_id: int,
        **kwargs
    ) -> Optional[EstimationProject]:
        """Update project metadata for ML features"""
        result = await self.db.execute(
            select(EstimationProject).where(EstimationProject.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return None

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    # =========================================================================
    # Function Point Logging
    # =========================================================================

    async def log_function_point_estimate(
        self,
        request_dict: Dict[str, Any],
        response_dict: Dict[str, Any],
        project_id: Optional[int] = None,
        source: str = "api"
    ) -> FunctionPointEstimate:
        """
        Log a Function Point estimation for ML training.

        Args:
            request_dict: The full FP calculation request
            response_dict: The full FP calculation response
            project_id: Optional link to EstimationProject
            source: Source of estimation (api, ui, import)

        Returns:
            Created FunctionPointEstimate record
        """
        # Extract complexity distribution from response
        summary = response_dict.get("summary", {})
        complexity_dist = summary.get("complexity_distribution", {})

        # Create estimate record
        estimate = FunctionPointEstimate(
            project_id=project_id,
            input_project_name=request_dict.get("project_name", "Unknown"),

            # Component counts
            ilf_count=len(request_dict.get("ilfs", [])),
            eif_count=len(request_dict.get("eifs", [])),
            ei_count=len(request_dict.get("eis", [])),
            eo_count=len(request_dict.get("eos", [])),
            eq_count=len(request_dict.get("eqs", [])),

            # Complexity distribution
            low_complexity_count=complexity_dist.get("low", 0),
            average_complexity_count=complexity_dist.get("average", 0),
            high_complexity_count=complexity_dist.get("high", 0),

            # Results
            unadjusted_fp=response_dict.get("unadjusted_fp", 0),
            vaf=response_dict.get("vaf", 1.0),
            adjusted_fp=response_dict.get("adjusted_fp", 0),

            # VAF details
            vaf_applied=request_dict.get("use_vaf", False),
            gsc_ratings=request_dict.get("gsc_ratings"),

            # Full data for debugging
            full_request=request_dict,
            full_response=response_dict,

            # Metadata
            source=source
        )

        self.db.add(estimate)
        await self.db.flush()
        await self.db.refresh(estimate)
        return estimate

    async def record_fp_actuals(
        self,
        estimate_id: int,
        actual_effort_hours: Optional[float] = None,
        actual_person_days: Optional[float] = None,
        actual_duration_days: Optional[int] = None,
        actual_team_size: Optional[int] = None,
        actual_completion_date: Optional[datetime] = None
    ) -> Optional[FunctionPointEstimate]:
        """Record actual results for a Function Point estimate."""
        result = await self.db.execute(
            select(FunctionPointEstimate).where(
                FunctionPointEstimate.id == estimate_id
            )
        )
        estimate = result.scalar_one_or_none()

        if not estimate:
            return None

        # Update actuals
        if actual_effort_hours is not None:
            estimate.actual_effort_hours = actual_effort_hours
        if actual_person_days is not None:
            estimate.actual_person_days = actual_person_days
        if actual_duration_days is not None:
            estimate.actual_duration_days = actual_duration_days
        if actual_team_size is not None:
            estimate.actual_team_size = actual_team_size
        if actual_completion_date is not None:
            estimate.actual_completion_date = actual_completion_date

        # Calculate accuracy if we have enough data
        if actual_effort_hours and estimate.adjusted_fp:
            # Industry benchmark: ~8 hours per FP for average complexity
            estimated_hours = estimate.adjusted_fp * 8
            accuracy = 1 - abs(actual_effort_hours - estimated_hours) / max(actual_effort_hours, estimated_hours)
            estimate.estimation_accuracy = max(0, min(1, accuracy)) * 100

        estimate.actuals_recorded_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(estimate)
        return estimate

    # =========================================================================
    # Story Point Logging
    # =========================================================================

    async def log_story_point_estimate(
        self,
        request_dict: Dict[str, Any],
        response_dict: Dict[str, Any],
        project_id: Optional[int] = None,
        source: str = "api"
    ) -> StoryPointEstimate:
        """
        Log a Story Point estimation for ML training.

        Args:
            request_dict: The full SP estimation request
            response_dict: The full SP estimation response
            project_id: Optional link to EstimationProject
            source: Source of estimation (api, ui, import)

        Returns:
            Created StoryPointEstimate record
        """
        # Extract complexity factors
        factors = request_dict.get("complexity_factors", {})
        three_point = request_dict.get("three_point", {})
        hours_estimate = response_dict.get("hours_estimate", {})

        # Create estimate record
        estimate = StoryPointEstimate(
            project_id=project_id,
            input_story_title=request_dict.get("story_name", "Unknown"),
            input_story_description=request_dict.get("description"),

            # Complexity factors
            technical_complexity=factors.get("technical_complexity", 5),
            business_value=factors.get("business_value", 5),
            risk_level=factors.get("risk_level", 5),
            uncertainty=factors.get("uncertainty", 5),
            dependencies=factors.get("dependencies", 0),

            # PERT inputs
            pert_optimistic=three_point.get("optimistic_hours") if three_point else None,
            pert_most_likely=three_point.get("most_likely_hours") if three_point else None,
            pert_pessimistic=three_point.get("pessimistic_hours") if three_point else None,
            pert_expected=hours_estimate.get("pert_estimate") if hours_estimate else None,
            pert_std_dev=hours_estimate.get("standard_deviation") if hours_estimate else None,

            # Results
            story_points=response_dict.get("fibonacci_points", 0),
            confidence=response_dict.get("complexity_score", 0),

            # Confidence ranges
            confidence_range_low=int(response_dict.get("confidence_narrow", {}).get("min", 0)) if response_dict.get("confidence_narrow") else None,
            confidence_range_high=int(response_dict.get("confidence_narrow", {}).get("max", 0)) if response_dict.get("confidence_narrow") else None,

            # Risk assessment
            risk_factors=response_dict.get("risk_factors"),
            recommendations=response_dict.get("recommendations"),

            # Full data
            full_request=request_dict,
            full_response=response_dict,

            # Metadata
            source=source
        )

        self.db.add(estimate)
        await self.db.flush()
        await self.db.refresh(estimate)
        return estimate

    async def record_sp_actuals(
        self,
        estimate_id: int,
        actual_effort_hours: Optional[float] = None,
        actual_person_days: Optional[float] = None,
        actual_duration_days: Optional[int] = None,
        actual_story_points: Optional[int] = None,
        actual_completion_date: Optional[datetime] = None
    ) -> Optional[StoryPointEstimate]:
        """Record actual results for a Story Point estimate."""
        result = await self.db.execute(
            select(StoryPointEstimate).where(StoryPointEstimate.id == estimate_id)
        )
        estimate = result.scalar_one_or_none()

        if not estimate:
            return None

        # Update actuals
        if actual_effort_hours is not None:
            estimate.actual_effort_hours = actual_effort_hours
        if actual_person_days is not None:
            estimate.actual_person_days = actual_person_days
        if actual_duration_days is not None:
            estimate.actual_duration_days = actual_duration_days
        if actual_story_points is not None:
            estimate.actual_story_points = actual_story_points
        if actual_completion_date is not None:
            estimate.actual_completion_date = actual_completion_date

        # Calculate velocity factor (hours per story point)
        if actual_effort_hours and estimate.story_points:
            estimate.velocity_factor = actual_effort_hours / estimate.story_points

        # Calculate accuracy
        if actual_story_points and estimate.story_points:
            estimate.estimation_accuracy = (
                1 - abs(actual_story_points - estimate.story_points)
                / max(actual_story_points, estimate.story_points)
            ) * 100

        estimate.actuals_recorded_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(estimate)
        return estimate

    # =========================================================================
    # ML Training Data Retrieval
    # =========================================================================

    async def get_fp_training_data(
        self,
        min_samples: int = 10,
        has_actuals_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get Function Point data formatted for ML training."""
        query = select(FunctionPointEstimate).options(
            selectinload(FunctionPointEstimate.project)
        )

        if has_actuals_only:
            query = query.where(
                FunctionPointEstimate.actual_effort_hours.isnot(None)
            )

        query = query.order_by(desc(FunctionPointEstimate.estimated_at))
        result = await self.db.execute(query)
        estimates = result.scalars().all()

        if len(estimates) < min_samples:
            return []

        training_data = []
        for est in estimates:
            # Get project metadata if available
            project_features = {}
            if est.project:
                project_features = {
                    "tech_stack": est.project.tech_stack.value if est.project.tech_stack else None,
                    "team_size": est.project.team_size,
                    "experience_level": est.project.experience_level,
                    "domain_complexity": est.project.domain_complexity,
                    "has_legacy": est.project.has_legacy_integration,
                    "has_external_apis": est.project.has_external_apis,
                    "is_greenfield": est.project.is_greenfield
                }

            training_data.append({
                # Features
                "ilf_count": est.ilf_count,
                "eif_count": est.eif_count,
                "ei_count": est.ei_count,
                "eo_count": est.eo_count,
                "eq_count": est.eq_count,
                "low_complexity": est.low_complexity_count,
                "avg_complexity": est.average_complexity_count,
                "high_complexity": est.high_complexity_count,
                "unadjusted_fp": est.unadjusted_fp,
                "vaf": est.vaf,
                "adjusted_fp": est.adjusted_fp,
                **project_features,

                # Target (what we want to predict)
                "actual_hours": est.actual_effort_hours,
                "actual_days": est.actual_person_days
            })

        return training_data

    async def get_sp_training_data(
        self,
        min_samples: int = 10,
        has_actuals_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get Story Point data formatted for ML training."""
        query = select(StoryPointEstimate)

        if has_actuals_only:
            query = query.where(
                StoryPointEstimate.actual_effort_hours.isnot(None)
            )

        query = query.order_by(desc(StoryPointEstimate.estimated_at))
        result = await self.db.execute(query)
        estimates = result.scalars().all()

        if len(estimates) < min_samples:
            return []

        training_data = []
        for est in estimates:
            training_data.append({
                # Features
                "technical_complexity": est.technical_complexity,
                "business_value": est.business_value,
                "risk_level": est.risk_level,
                "uncertainty": est.uncertainty,
                "dependencies": est.dependencies,
                "story_points": est.story_points,
                "pert_expected": est.pert_expected,
                "pert_std_dev": est.pert_std_dev,

                # Target
                "actual_hours": est.actual_effort_hours,
                "actual_days": est.actual_person_days,
                "actual_sp": est.actual_story_points,
                "velocity_factor": est.velocity_factor
            })

        return training_data

    # =========================================================================
    # Statistics & Analytics
    # =========================================================================

    async def get_estimation_statistics(self) -> Dict[str, Any]:
        """Get overall estimation statistics for dashboard"""
        # FP counts
        fp_total_result = await self.db.execute(
            select(func.count(FunctionPointEstimate.id))
        )
        fp_total = fp_total_result.scalar() or 0

        fp_actuals_result = await self.db.execute(
            select(func.count(FunctionPointEstimate.id)).where(
                FunctionPointEstimate.actual_effort_hours.isnot(None)
            )
        )
        fp_with_actuals = fp_actuals_result.scalar() or 0

        # SP counts
        sp_total_result = await self.db.execute(
            select(func.count(StoryPointEstimate.id))
        )
        sp_total = sp_total_result.scalar() or 0

        sp_actuals_result = await self.db.execute(
            select(func.count(StoryPointEstimate.id)).where(
                StoryPointEstimate.actual_effort_hours.isnot(None)
            )
        )
        sp_with_actuals = sp_actuals_result.scalar() or 0

        # Project count
        projects_result = await self.db.execute(
            select(func.count(EstimationProject.id))
        )
        projects = projects_result.scalar() or 0

        return {
            "function_points": {
                "total_estimates": fp_total,
                "with_actuals": fp_with_actuals,
                "training_ready": fp_with_actuals >= 10
            },
            "story_points": {
                "total_estimates": sp_total,
                "with_actuals": sp_with_actuals,
                "training_ready": sp_with_actuals >= 10
            },
            "projects": projects,
            "ml_ready": fp_with_actuals >= 10 or sp_with_actuals >= 10
        }

    async def get_recent_estimates(
        self,
        limit: int = 20,
        estimation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent estimation records"""
        results = []

        if estimation_type in (None, "function_points"):
            fp_result = await self.db.execute(
                select(FunctionPointEstimate).order_by(
                    desc(FunctionPointEstimate.estimated_at)
                ).limit(limit)
            )
            fp_estimates = fp_result.scalars().all()

            for est in fp_estimates:
                results.append({
                    "type": "function_points",
                    "id": est.id,
                    "project_name": est.input_project_name,
                    "result": est.adjusted_fp,
                    "has_actuals": est.actual_effort_hours is not None,
                    "estimated_at": est.estimated_at.isoformat(),
                    "source": est.source
                })

        if estimation_type in (None, "story_points"):
            sp_result = await self.db.execute(
                select(StoryPointEstimate).order_by(
                    desc(StoryPointEstimate.estimated_at)
                ).limit(limit)
            )
            sp_estimates = sp_result.scalars().all()

            for est in sp_estimates:
                results.append({
                    "type": "story_points",
                    "id": est.id,
                    "story_name": est.input_story_title,
                    "result": est.story_points,
                    "has_actuals": est.actual_effort_hours is not None,
                    "estimated_at": est.estimated_at.isoformat(),
                    "source": est.source
                })

        # Sort by date
        results.sort(key=lambda x: x["estimated_at"], reverse=True)
        return results[:limit]
