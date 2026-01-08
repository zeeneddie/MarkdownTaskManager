"""
Week 88: Portal Feature Request Service

Handles customer feature requests from the client portal:
- Feature submission and validation
- Peter agent classification (work type determination)
- Epic/feature mapping to existing projects
- Status tracking and workflow integration
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload
import logging
import uuid

from app.models.graph_workflow import (
    PortalFeatureRequest,
    FEATURE_REQUEST_STATUSES,
    WORK_TYPES,
    WORKFLOW_GRAPH_INTEGRATIONS,
)
from app.models.project import Project
from app.models.task_hierarchy import Epic, Feature

logger = logging.getLogger(__name__)


class PortalFeatureRequestService:
    """
    Service for managing customer portal feature requests.

    Integrates with:
    - Peter agent for work type classification
    - Epic/Feature mapping for project integration
    - Kanban system for workflow tracking
    - Sprint planning for resource allocation
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Feature Request CRUD
    # =========================================================================

    async def submit_feature_request(
        self,
        user_email: str,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        user_name: Optional[str] = None,
        organization: Optional[str] = None,
        external_id: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Submit a new feature request from the customer portal.

        Returns the created request with initial status 'submitted'.
        """
        try:
            # Validate priority
            valid_priorities = ["low", "medium", "high", "critical"]
            if priority not in valid_priorities:
                priority = "medium"

            # Create feature request
            request = PortalFeatureRequest(
                external_id=external_id,
                user_email=user_email,
                user_name=user_name,
                organization=organization,
                title=title,
                description=description,
                priority=priority,
                category=category,
                attachments=attachments,
                status="submitted",
            )

            self.db.add(request)
            await self.db.commit()
            await self.db.refresh(request)

            logger.info(f"Feature request submitted: {request.id} - {title}")

            return {
                "success": True,
                "request": request.to_dict(),
                "message": "Feature request submitted successfully",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to submit feature request: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_feature_request(
        self,
        request_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a feature request by ID."""
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if request:
                return request.to_dict()
            return None

        except Exception as e:
            logger.error(f"Failed to get feature request: {e}")
            return None

    async def list_feature_requests(
        self,
        status: Optional[str] = None,
        user_email: Optional[str] = None,
        organization: Optional[str] = None,
        project_id: Optional[int] = None,
        work_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List feature requests with optional filters."""
        try:
            stmt = select(PortalFeatureRequest)

            # Apply filters
            filters = []
            if status:
                filters.append(PortalFeatureRequest.status == status)
            if user_email:
                filters.append(PortalFeatureRequest.user_email == user_email)
            if organization:
                filters.append(PortalFeatureRequest.organization == organization)
            if project_id:
                filters.append(PortalFeatureRequest.mapped_project_id == project_id)
            if work_type:
                filters.append(PortalFeatureRequest.work_type == work_type)

            if filters:
                stmt = stmt.where(and_(*filters))

            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar() or 0

            # Apply pagination and ordering
            stmt = stmt.order_by(PortalFeatureRequest.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)

            result = await self.db.execute(stmt)
            requests = result.scalars().all()

            return {
                "requests": [r.to_dict() for r in requests],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Failed to list feature requests: {e}")
            return {"requests": [], "total": 0, "error": str(e)}

    async def update_feature_request(
        self,
        request_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a feature request."""
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return {"success": False, "error": "Request not found"}

            # Apply updates
            allowed_fields = [
                "title", "description", "priority", "category",
                "status", "kanban_item_id", "sprint_id",
            ]

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(request, field, value)

            # Handle status transitions
            if "status" in updates:
                if updates["status"] == "done":
                    request.completed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(request)

            return {
                "success": True,
                "request": request.to_dict(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update feature request: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Peter Agent Classification
    # =========================================================================

    async def classify_feature_request(
        self,
        request_id: str,
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Classify a feature request using Peter agent.

        Determines:
        - Work type (GREEN_PAPER, BROWN_PAPER, BUG, NEW_FEATURE, etc.)
        - Classification confidence
        - Recommended workflow
        """
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return {"success": False, "error": "Request not found"}

            # Update status to analyzing
            request.status = "analyzing"
            await self.db.commit()

            # Perform classification
            if use_llm:
                classification = await self._classify_with_llm(request)
            else:
                classification = self._classify_with_rules(request)

            # Update request with classification
            request.work_type = classification["work_type"]
            request.classification_confidence = classification["confidence"]
            request.classification_reasoning = classification["reasoning"]
            request.classified_at = datetime.utcnow()
            request.classified_by = "peter_agent" if use_llm else "rule_engine"
            request.status = "classified"

            await self.db.commit()
            await self.db.refresh(request)

            logger.info(
                f"Classified request {request_id} as {classification['work_type']} "
                f"with confidence {classification['confidence']}"
            )

            return {
                "success": True,
                "request": request.to_dict(),
                "classification": classification,
                "recommended_workflow": WORKFLOW_GRAPH_INTEGRATIONS.get(
                    classification["work_type"], []
                ),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to classify feature request: {e}")
            return {"success": False, "error": str(e)}

    async def _classify_with_llm(
        self,
        request: PortalFeatureRequest,
    ) -> Dict[str, Any]:
        """
        Classify using Peter agent LLM.

        TODO: Integrate with actual LLM provider
        """
        # Prepare context for classification
        context = {
            "title": request.title,
            "description": request.description or "",
            "priority": request.priority,
            "category": request.category,
        }

        # Analyze keywords and patterns
        title_lower = request.title.lower()
        desc_lower = (request.description or "").lower()
        combined = f"{title_lower} {desc_lower}"

        # Pattern matching for work types
        patterns = {
            "BUG": ["bug", "error", "crash", "fix", "broken", "issue", "problem", "defect"],
            "NEW_FEATURE": ["add", "new", "create", "implement", "feature", "build"],
            "ENHANCEMENT": ["improve", "enhance", "better", "update", "upgrade", "optimize"],
            "MAINTENANCE": ["refactor", "cleanup", "deprecate", "remove", "tech debt"],
            "MIGRATION": ["migrate", "upgrade", "convert", "move", "transfer"],
            "TESTING": ["test", "coverage", "qa", "validation", "verify"],
            "QUALITY_AUDIT": ["audit", "review", "security", "compliance", "assess"],
            "GREEN_PAPER": ["new project", "greenfield", "from scratch", "new system"],
            "BROWN_PAPER": ["legacy", "existing", "migration", "modernize"],
        }

        # Score each work type
        scores = {}
        for work_type, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > 0:
                scores[work_type] = score

        # Determine work type
        if scores:
            work_type = max(scores, key=scores.get)
            max_score = scores[work_type]
            # Calculate confidence based on match strength
            confidence = min(0.95, 0.5 + (max_score * 0.1))
        else:
            work_type = "NEW_FEATURE"  # Default
            confidence = 0.5

        # Generate reasoning
        reasoning = self._generate_classification_reasoning(
            request, work_type, scores
        )

        return {
            "work_type": work_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "pattern_scores": scores,
        }

    def _classify_with_rules(
        self,
        request: PortalFeatureRequest,
    ) -> Dict[str, Any]:
        """Simple rule-based classification fallback."""
        title_lower = request.title.lower()

        if any(kw in title_lower for kw in ["bug", "fix", "error", "crash"]):
            return {
                "work_type": "BUG",
                "confidence": 0.7,
                "reasoning": "Title contains bug-related keywords",
            }
        elif any(kw in title_lower for kw in ["improve", "enhance", "better"]):
            return {
                "work_type": "ENHANCEMENT",
                "confidence": 0.6,
                "reasoning": "Title suggests improvement to existing feature",
            }
        elif any(kw in title_lower for kw in ["add", "new", "create"]):
            return {
                "work_type": "NEW_FEATURE",
                "confidence": 0.7,
                "reasoning": "Title suggests new feature development",
            }
        else:
            return {
                "work_type": "NEW_FEATURE",
                "confidence": 0.5,
                "reasoning": "Default classification - review recommended",
            }

    def _generate_classification_reasoning(
        self,
        request: PortalFeatureRequest,
        work_type: str,
        scores: Dict[str, int],
    ) -> str:
        """Generate human-readable classification reasoning."""
        reasons = []

        if work_type == "BUG":
            reasons.append("Request describes a defect or error in existing functionality")
        elif work_type == "NEW_FEATURE":
            reasons.append("Request describes new functionality to be added")
        elif work_type == "ENHANCEMENT":
            reasons.append("Request describes improvements to existing features")
        elif work_type == "MAINTENANCE":
            reasons.append("Request relates to technical debt or code maintenance")
        elif work_type == "MIGRATION":
            reasons.append("Request involves technology or platform migration")
        elif work_type == "GREEN_PAPER":
            reasons.append("Request describes a new greenfield project")
        elif work_type == "BROWN_PAPER":
            reasons.append("Request involves legacy system modernization")

        if scores:
            top_3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
            pattern_info = ", ".join([f"{wt}({s})" for wt, s in top_3])
            reasons.append(f"Pattern matches: {pattern_info}")

        if request.category:
            reasons.append(f"Category: {request.category}")

        if request.priority in ["high", "critical"]:
            reasons.append(f"Priority: {request.priority} - may require expedited handling")

        return " | ".join(reasons)

    # =========================================================================
    # Epic/Feature Mapping
    # =========================================================================

    async def map_to_epic(
        self,
        request_id: str,
        project_id: int,
        auto_suggest: bool = True,
    ) -> Dict[str, Any]:
        """
        Map a feature request to an existing epic/feature in a project.

        Can auto-suggest mappings based on similarity analysis.
        """
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return {"success": False, "error": "Request not found"}

            # Verify project exists
            project_stmt = select(Project).where(Project.id == project_id)
            project_result = await self.db.execute(project_stmt)
            project = project_result.scalar_one_or_none()

            if not project:
                return {"success": False, "error": "Project not found"}

            # Get suggestions if requested
            suggestions = []
            if auto_suggest:
                suggestions = await self._find_epic_suggestions(
                    request, project_id
                )

            # Update request with project mapping
            request.mapped_project_id = project_id
            request.mapping_suggestions = suggestions

            if suggestions:
                # Auto-map to best suggestion
                best = suggestions[0]
                request.mapped_epic_id = best.get("epic_id")
                request.mapped_feature_id = best.get("feature_id")
                request.mapping_confidence = best.get("confidence", 0.0)
                request.status = "mapped"
            else:
                request.status = "classified"  # No mapping found

            await self.db.commit()
            await self.db.refresh(request)

            return {
                "success": True,
                "request": request.to_dict(),
                "suggestions": suggestions,
                "project": {"id": project.id, "name": project.name},
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to map feature request: {e}")
            return {"success": False, "error": str(e)}

    async def _find_epic_suggestions(
        self,
        request: PortalFeatureRequest,
        project_id: int,
    ) -> List[Dict[str, Any]]:
        """Find matching epics/features based on similarity."""
        suggestions = []

        try:
            # Get epics for the project
            epic_stmt = select(Epic).where(Epic.project_id == project_id)
            epic_result = await self.db.execute(epic_stmt)
            epics = epic_result.scalars().all()

            request_text = f"{request.title} {request.description or ''}".lower()

            for epic in epics:
                epic_text = f"{epic.name} {epic.description or ''}".lower()

                # Simple word overlap similarity
                request_words = set(request_text.split())
                epic_words = set(epic_text.split())
                overlap = len(request_words & epic_words)

                if overlap > 0:
                    confidence = min(0.9, overlap * 0.1)
                    suggestions.append({
                        "epic_id": str(epic.id),
                        "epic_name": epic.name,
                        "confidence": confidence,
                        "matching_words": list(request_words & epic_words)[:5],
                    })

            # Sort by confidence
            suggestions.sort(key=lambda x: -x["confidence"])

            return suggestions[:5]  # Top 5 suggestions

        except Exception as e:
            logger.error(f"Failed to find epic suggestions: {e}")
            return []

    async def confirm_mapping(
        self,
        request_id: str,
        epic_id: str,
        feature_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Confirm the mapping of a feature request to an epic."""
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return {"success": False, "error": "Request not found"}

            request.mapped_epic_id = epic_id
            request.mapped_feature_id = feature_id
            request.mapping_confidence = 1.0  # User confirmed
            request.status = "mapped"

            await self.db.commit()
            await self.db.refresh(request)

            return {
                "success": True,
                "request": request.to_dict(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to confirm mapping: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Sprint/Kanban Integration
    # =========================================================================

    async def assign_to_sprint(
        self,
        request_id: str,
        sprint_id: int,
    ) -> Dict[str, Any]:
        """Assign a feature request to a sprint."""
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return {"success": False, "error": "Request not found"}

            request.sprint_id = sprint_id
            request.status = "planned"

            await self.db.commit()
            await self.db.refresh(request)

            logger.info(f"Assigned request {request_id} to sprint {sprint_id}")

            return {
                "success": True,
                "request": request.to_dict(),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to assign to sprint: {e}")
            return {"success": False, "error": str(e)}

    async def create_kanban_item(
        self,
        request_id: str,
    ) -> Dict[str, Any]:
        """Create a kanban item from a feature request."""
        try:
            request_uuid = uuid.UUID(request_id)
            stmt = select(PortalFeatureRequest).where(
                PortalFeatureRequest.id == request_uuid
            )
            result = await self.db.execute(stmt)
            request = result.scalar_one_or_none()

            if not request:
                return {"success": False, "error": "Request not found"}

            # TODO: Create actual kanban item via kanban service
            # For now, we'll generate a mock ID
            kanban_item_id = int(datetime.utcnow().timestamp())

            request.kanban_item_id = kanban_item_id
            request.status = "in_progress"

            await self.db.commit()
            await self.db.refresh(request)

            return {
                "success": True,
                "request": request.to_dict(),
                "kanban_item_id": kanban_item_id,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create kanban item: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Statistics and Reporting
    # =========================================================================

    async def get_statistics(
        self,
        organization: Optional[str] = None,
        project_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get feature request statistics."""
        try:
            since = datetime.utcnow() - timedelta(days=days)

            base_filter = PortalFeatureRequest.created_at >= since
            filters = [base_filter]

            if organization:
                filters.append(PortalFeatureRequest.organization == organization)
            if project_id:
                filters.append(PortalFeatureRequest.mapped_project_id == project_id)

            # Total requests
            total_stmt = select(func.count()).where(and_(*filters))
            total = await self.db.execute(total_stmt)
            total_count = total.scalar() or 0

            # By status
            status_stmt = select(
                PortalFeatureRequest.status,
                func.count()
            ).where(and_(*filters)).group_by(PortalFeatureRequest.status)
            status_result = await self.db.execute(status_stmt)
            by_status = {row[0]: row[1] for row in status_result.fetchall()}

            # By work type
            type_stmt = select(
                PortalFeatureRequest.work_type,
                func.count()
            ).where(
                and_(*filters, PortalFeatureRequest.work_type.isnot(None))
            ).group_by(PortalFeatureRequest.work_type)
            type_result = await self.db.execute(type_stmt)
            by_type = {row[0]: row[1] for row in type_result.fetchall()}

            # By priority
            priority_stmt = select(
                PortalFeatureRequest.priority,
                func.count()
            ).where(and_(*filters)).group_by(PortalFeatureRequest.priority)
            priority_result = await self.db.execute(priority_stmt)
            by_priority = {row[0]: row[1] for row in priority_result.fetchall()}

            # Average classification confidence
            conf_stmt = select(
                func.avg(PortalFeatureRequest.classification_confidence)
            ).where(
                and_(*filters, PortalFeatureRequest.classification_confidence.isnot(None))
            )
            conf_result = await self.db.execute(conf_stmt)
            avg_confidence = conf_result.scalar() or 0.0

            # Completed requests
            completed_count = by_status.get("done", 0)
            completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0

            return {
                "period_days": days,
                "total_requests": total_count,
                "by_status": by_status,
                "by_work_type": by_type,
                "by_priority": by_priority,
                "average_classification_confidence": round(avg_confidence, 2),
                "completion_rate": round(completion_rate, 1),
                "completed_count": completed_count,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    async def get_user_requests(
        self,
        user_email: str,
        include_completed: bool = True,
    ) -> Dict[str, Any]:
        """Get all requests for a specific user."""
        filters = [PortalFeatureRequest.user_email == user_email]

        if not include_completed:
            filters.append(PortalFeatureRequest.status != "done")

        stmt = select(PortalFeatureRequest).where(
            and_(*filters)
        ).order_by(PortalFeatureRequest.created_at.desc())

        result = await self.db.execute(stmt)
        requests = result.scalars().all()

        return {
            "user_email": user_email,
            "requests": [r.to_dict() for r in requests],
            "total": len(requests),
        }

    # =========================================================================
    # Workflow Orchestration
    # =========================================================================

    async def process_feature_request(
        self,
        request_id: str,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Full processing pipeline for a feature request.

        Steps:
        1. Classify with Peter agent
        2. Map to epic (if project provided)
        3. Return recommended next actions
        """
        try:
            # Step 1: Classify
            classify_result = await self.classify_feature_request(
                request_id, use_llm=True
            )

            if not classify_result.get("success"):
                return classify_result

            # Step 2: Map to epic if project provided
            mapping_result = None
            if project_id:
                mapping_result = await self.map_to_epic(
                    request_id, project_id, auto_suggest=True
                )

            # Get final request state
            request = await self.get_feature_request(request_id)

            # Determine recommended actions
            actions = []
            if request.get("status") == "classified":
                actions.append({
                    "action": "map_to_epic",
                    "description": "Map this request to a project epic",
                })
            elif request.get("status") == "mapped":
                actions.append({
                    "action": "assign_to_sprint",
                    "description": "Assign to a sprint for development",
                })

            return {
                "success": True,
                "request": request,
                "classification": classify_result.get("classification"),
                "mapping": mapping_result,
                "recommended_actions": actions,
                "workflow_integrations": classify_result.get("recommended_workflow", []),
            }

        except Exception as e:
            logger.error(f"Failed to process feature request: {e}")
            return {"success": False, "error": str(e)}
