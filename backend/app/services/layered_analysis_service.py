"""
LayeredAnalysisService - Orchestrates the 4-Layer Analysis Pipeline

Week 77: Coordinates VBScript, Stored Procedure, SWOT, and Improvement Planning.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.layered_analysis import (
    LayeredAnalysisSession,
    VBScriptAnalysis,
    StoredProcedureAnalysis,
    SWOTAnalysis,
    ImprovementItem as ImprovementItemModel,
    AnalysisReport
)
from app.services.vbscript_analyzer_service import VBScriptAnalyzerService
from app.services.stored_procedure_analyzer_service import StoredProcedureAnalyzerService
from app.services.swot_generator_service import SWOTGeneratorService
from app.services.improvement_planner_service import (
    ImprovementPlannerService,
    PlanningConstraints,
    ImprovementCategory
)

logger = logging.getLogger(__name__)


class LayeredAnalysisService:
    """
    Orchestrates the 4-layer analysis pipeline:

    Layer 1: VBScript Analysis (ASP Classic code)
    Layer 2: Stored Procedure Analysis (SQL Server)
    Layer 3: SWOT Generation (from analysis findings)
    Layer 4: Improvement Planning (actionable backlog)
    """

    def __init__(self, db: Session):
        self.db = db
        self.vbscript_analyzer = VBScriptAnalyzerService()
        self.sp_analyzer = StoredProcedureAnalyzerService()
        self.swot_generator = SWOTGeneratorService()
        self.improvement_planner = ImprovementPlannerService()

    async def create_session(
        self,
        project_id: UUID,
        name: str,
        description: Optional[str] = None,
        source_path: Optional[str] = None
    ) -> LayeredAnalysisSession:
        """Create a new layered analysis session.

        Note: description is accepted for API compatibility but not stored
        (model only has source_path, not description).
        """
        session = LayeredAnalysisSession(
            id=uuid4(),
            project_id=None,  # Model expects Integer, we store None for adhoc
            name=name,
            source_path=source_path or description,  # Store description in source_path
            status="created",
            current_phase="initialization",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Created layered analysis session: {session.id}")
        return session

    async def run_full_analysis(
        self,
        session_id: UUID,
        vbscript_code: Optional[str] = None,
        sp_code: Optional[str] = None,
        constraints: Optional[PlanningConstraints] = None
    ) -> Dict[str, Any]:
        """
        Run all 4 layers of analysis in sequence.

        Args:
            session_id: Analysis session ID
            vbscript_code: Optional VBScript/ASP code to analyze
            sp_code: Optional stored procedure code
            constraints: Optional planning constraints

        Returns:
            Complete analysis results across all layers
        """
        session = self.db.get(LayeredAnalysisSession, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "running"
        session.started_at = datetime.now(timezone.utc)
        self.db.commit()

        results = {
            "session_id": str(session_id),
            "layers": {},
            "errors": []
        }

        try:
            # Layer 1: VBScript Analysis
            if vbscript_code:
                session.current_layer = 1
                self.db.commit()

                vb_result = await self._run_vbscript_layer(session_id, vbscript_code)
                results["layers"]["vbscript"] = vb_result

            # Layer 2: Stored Procedure Analysis
            if sp_code:
                session.current_layer = 2
                self.db.commit()

                sp_result = await self._run_sp_layer(session_id, sp_code)
                results["layers"]["stored_procedures"] = sp_result

            # Layer 3: SWOT Generation
            session.current_layer = 3
            self.db.commit()

            swot_result = await self._run_swot_layer(
                session_id,
                results["layers"].get("vbscript"),
                results["layers"].get("stored_procedures")
            )
            results["layers"]["swot"] = swot_result

            # Layer 4: Improvement Planning
            session.current_layer = 4
            self.db.commit()

            plan_result = await self._run_improvement_layer(
                session_id,
                swot_result,
                constraints
            )
            results["layers"]["improvement_plan"] = plan_result

            # Mark session complete
            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            results["status"] = "completed"

        except Exception as e:
            logger.error(f"Analysis failed at layer {session.current_layer}: {e}")
            session.status = "failed"
            session.error_message = str(e)
            self.db.commit()

            results["status"] = "failed"
            results["errors"].append(str(e))

        return results

    async def _run_vbscript_layer(
        self,
        session_id: UUID,
        code: str
    ) -> Dict[str, Any]:
        """Run Layer 1: VBScript Analysis."""
        logger.info(f"Running Layer 1: VBScript Analysis for session {session_id}")

        # Run analysis
        analysis = await self.vbscript_analyzer.analyze(code)
        result = analysis.to_dict()

        # Store in database
        db_analysis = VBScriptAnalysis(
            id=uuid4(),
            session_id=session_id,
            file_count=result.get("file_count", 1),
            total_lines=analysis.total_lines,
            security_findings=result.get("security_findings", []),
            complexity_score=analysis.complexity_score,
            modernization_score=analysis.modernization_score,
            includes_analysis=result.get("includes_analysis", {}),
            sql_patterns=result.get("sql_patterns", {}),
            recommendations=result.get("recommendations", []),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(db_analysis)
        self.db.commit()

        return result

    async def _run_sp_layer(
        self,
        session_id: UUID,
        code: str
    ) -> Dict[str, Any]:
        """Run Layer 2: Stored Procedure Analysis."""
        logger.info(f"Running Layer 2: Stored Procedure Analysis for session {session_id}")

        # Run analysis
        analysis = await self.sp_analyzer.analyze(code)
        result = analysis.to_dict()

        # Store in database
        db_analysis = StoredProcedureAnalysis(
            id=uuid4(),
            session_id=session_id,
            procedure_count=len(analysis.procedures),
            total_lines=analysis.total_lines,
            complexity_metrics=result.get("complexity_metrics", {}),
            vendor_specific_patterns=result.get("vendor_specific", {}),
            dynamic_sql_findings=result.get("dynamic_sql_findings", []),
            cursor_usage=result.get("cursor_usage", {}),
            transaction_patterns=result.get("transaction_patterns", {}),
            recommendations=result.get("recommendations", []),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(db_analysis)
        self.db.commit()

        return result

    async def _run_swot_layer(
        self,
        session_id: UUID,
        vb_analysis: Optional[Dict[str, Any]],
        sp_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run Layer 3: SWOT Generation."""
        logger.info(f"Running Layer 3: SWOT Generation for session {session_id}")

        # Generate SWOT matrix
        swot = await self.swot_generator.generate_swot(vb_analysis, sp_analysis)
        result = swot.to_dict()

        # Store in database
        db_swot = SWOTAnalysis(
            id=uuid4(),
            session_id=session_id,
            strengths=result.get("matrix", {}).get("strengths", []),
            weaknesses=result.get("matrix", {}).get("weaknesses", []),
            opportunities=result.get("matrix", {}).get("opportunities", []),
            threats=result.get("matrix", {}).get("threats", []),
            prioritization=result.get("prioritization", {}),
            migration_readiness=result.get("migration_readiness", {}),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(db_swot)
        self.db.commit()

        return result

    async def _run_improvement_layer(
        self,
        session_id: UUID,
        swot_result: Dict[str, Any],
        constraints: Optional[PlanningConstraints]
    ) -> Dict[str, Any]:
        """Run Layer 4: Improvement Planning."""
        logger.info(f"Running Layer 4: Improvement Planning for session {session_id}")

        # Generate improvement plan
        plan = await self.improvement_planner.create_improvement_plan(
            swot_result,
            constraints
        )
        result = plan.to_dict()

        # Store improvement items in database
        for item in plan.items:
            db_item = ImprovementItemModel(
                id=uuid4(),
                session_id=session_id,
                title=item.title,
                description=item.description,
                category=item.category.value,
                item_type=item.item_type.value,
                priority=item.priority,
                effort_days=item.effort_days,
                business_impact=item.business_impact.value,
                risk_if_not_done=item.risk_if_not_done.value,
                implementation_notes=item.implementation_notes,
                status=item.status,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(db_item)

        self.db.commit()

        return result

    async def get_session(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get session details with all analysis results."""
        session = self.db.get(LayeredAnalysisSession, session_id)
        if not session:
            return None

        # Get all layer results
        vb_analysis = self.db.execute(
            select(VBScriptAnalysis).where(VBScriptAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        sp_analysis = self.db.execute(
            select(StoredProcedureAnalysis).where(StoredProcedureAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        swot_analysis = self.db.execute(
            select(SWOTAnalysis).where(SWOTAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        improvements = self.db.execute(
            select(ImprovementItemModel).where(ImprovementItemModel.session_id == session_id)
        ).scalars().all()

        return {
            "id": str(session.id),
            "project_id": str(session.project_id),
            "name": session.name,
            "description": session.description,
            "status": session.status,
            "current_layer": session.current_layer,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "error_message": session.error_message,
            "layers": {
                "vbscript": self._serialize_vb_analysis(vb_analysis) if vb_analysis else None,
                "stored_procedures": self._serialize_sp_analysis(sp_analysis) if sp_analysis else None,
                "swot": self._serialize_swot_analysis(swot_analysis) if swot_analysis else None,
                "improvement_items": [
                    self._serialize_improvement(item) for item in improvements
                ]
            }
        }

    def _serialize_vb_analysis(self, analysis: VBScriptAnalysis) -> Dict[str, Any]:
        """Serialize VBScript analysis to dict."""
        return {
            "id": str(analysis.id),
            "file_count": analysis.file_count,
            "total_lines": analysis.total_lines,
            "security_findings": analysis.security_findings,
            "complexity_score": analysis.complexity_score,
            "modernization_score": analysis.modernization_score,
            "includes_analysis": analysis.includes_analysis,
            "sql_patterns": analysis.sql_patterns,
            "recommendations": analysis.recommendations,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }

    def _serialize_sp_analysis(self, analysis: StoredProcedureAnalysis) -> Dict[str, Any]:
        """Serialize stored procedure analysis to dict."""
        return {
            "id": str(analysis.id),
            "procedure_count": analysis.procedure_count,
            "total_lines": analysis.total_lines,
            "complexity_metrics": analysis.complexity_metrics,
            "vendor_specific_patterns": analysis.vendor_specific_patterns,
            "dynamic_sql_findings": analysis.dynamic_sql_findings,
            "cursor_usage": analysis.cursor_usage,
            "transaction_patterns": analysis.transaction_patterns,
            "recommendations": analysis.recommendations,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }

    def _serialize_swot_analysis(self, analysis: SWOTAnalysis) -> Dict[str, Any]:
        """Serialize SWOT analysis to dict."""
        return {
            "id": str(analysis.id),
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "opportunities": analysis.opportunities,
            "threats": analysis.threats,
            "prioritization": analysis.prioritization,
            "migration_readiness": analysis.migration_readiness,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }

    def _serialize_improvement(self, item: ImprovementItemModel) -> Dict[str, Any]:
        """Serialize improvement item to dict."""
        return {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "item_type": item.item_type,
            "priority": item.priority,
            "effort_days": item.effort_days,
            "business_impact": item.business_impact,
            "risk_if_not_done": item.risk_if_not_done,
            "implementation_notes": item.implementation_notes,
            "status": item.status,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }

    async def list_sessions(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List analysis sessions with optional filters."""
        query = select(LayeredAnalysisSession)

        if project_id:
            query = query.where(LayeredAnalysisSession.project_id == project_id)
        if status:
            query = query.where(LayeredAnalysisSession.status == status)

        query = query.order_by(LayeredAnalysisSession.created_at.desc()).limit(limit)

        sessions = self.db.execute(query).scalars().all()

        return [
            {
                "id": str(s.id),
                "project_id": str(s.project_id),
                "name": s.name,
                "status": s.status,
                "current_layer": s.current_layer,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in sessions
        ]

    async def run_single_layer(
        self,
        session_id: UUID,
        layer: int,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a single layer of analysis."""
        session = self.db.get(LayeredAnalysisSession, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if layer == 1:
            if not code:
                raise ValueError("VBScript code required for Layer 1")
            return await self._run_vbscript_layer(session_id, code)

        elif layer == 2:
            if not code:
                raise ValueError("Stored procedure code required for Layer 2")
            return await self._run_sp_layer(session_id, code)

        elif layer == 3:
            # Get previous layer results
            vb_analysis = self.db.execute(
                select(VBScriptAnalysis).where(VBScriptAnalysis.session_id == session_id)
            ).scalar_one_or_none()

            sp_analysis = self.db.execute(
                select(StoredProcedureAnalysis).where(StoredProcedureAnalysis.session_id == session_id)
            ).scalar_one_or_none()

            return await self._run_swot_layer(
                session_id,
                self._serialize_vb_analysis(vb_analysis) if vb_analysis else None,
                self._serialize_sp_analysis(sp_analysis) if sp_analysis else None
            )

        elif layer == 4:
            # Get SWOT results
            swot_analysis = self.db.execute(
                select(SWOTAnalysis).where(SWOTAnalysis.session_id == session_id)
            ).scalar_one_or_none()

            if not swot_analysis:
                raise ValueError("SWOT analysis required for Layer 4")

            return await self._run_improvement_layer(
                session_id,
                self._serialize_swot_analysis(swot_analysis),
                None
            )

        else:
            raise ValueError(f"Invalid layer: {layer}. Must be 1-4")

    async def update_improvement_status(
        self,
        item_id: UUID,
        status: str
    ) -> Dict[str, Any]:
        """Update the status of an improvement item."""
        item = self.db.get(ImprovementItemModel, item_id)
        if not item:
            raise ValueError(f"Improvement item not found: {item_id}")

        valid_statuses = ["identified", "planned", "in_progress", "completed", "deferred"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        item.status = status
        item.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        return self._serialize_improvement(item)

    async def get_session_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get a summary of the analysis session."""
        session = self.db.get(LayeredAnalysisSession, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Count items in each layer
        vb_count = self.db.execute(
            select(VBScriptAnalysis).where(VBScriptAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        sp_count = self.db.execute(
            select(StoredProcedureAnalysis).where(StoredProcedureAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        swot = self.db.execute(
            select(SWOTAnalysis).where(SWOTAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        improvements = self.db.execute(
            select(ImprovementItemModel).where(ImprovementItemModel.session_id == session_id)
        ).scalars().all()

        # Calculate summary stats
        total_effort = sum(i.effort_days for i in improvements) if improvements else 0
        by_priority = {}
        by_category = {}
        by_status = {}

        for item in improvements:
            by_priority[item.priority] = by_priority.get(item.priority, 0) + 1
            by_category[item.category] = by_category.get(item.category, 0) + 1
            by_status[item.status] = by_status.get(item.status, 0) + 1

        return {
            "session_id": str(session_id),
            "name": session.name,
            "status": session.status,
            "layer_status": {
                "vbscript": "completed" if vb_count else "not_run",
                "stored_procedures": "completed" if sp_count else "not_run",
                "swot": "completed" if swot else "not_run",
                "improvements": "completed" if improvements else "not_run"
            },
            "metrics": {
                "vbscript_lines": vb_count.total_lines if vb_count else 0,
                "stored_procedure_count": sp_count.procedure_count if sp_count else 0,
                "weakness_count": len(swot.weaknesses) if swot else 0,
                "improvement_count": len(improvements),
                "total_effort_days": total_effort
            },
            "improvements_by_priority": by_priority,
            "improvements_by_category": by_category,
            "improvements_by_status": by_status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
