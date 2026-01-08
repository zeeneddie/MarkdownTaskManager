# backend/app/api/traceability.py
"""
Week 113: Traceability API

Links business rules to epic/feature/story hierarchy for:
- Impact analysis: "Which stories are affected if BR-042 changes?"
- Compliance: "Prove all authorization rules are tested"
- Migration: "Which rules must migrate to new system?"
- CRUD workflow detection: Group related business rules
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
import io

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.traceability_service import TraceabilityService
from app.models.traceability import LinkType, WorkflowType, CRUDOperation

router = APIRouter(prefix="/api/traceability", tags=["Traceability"])


# ============================================================================
# Request/Response Models
# ============================================================================

class LinkRuleRequest(BaseModel):
    """Request to link a business rule to a work item."""
    rule_id: str = Field(..., description="Business rule ID (e.g., 'BR-042')")
    entity_type: str = Field(..., description="'story', 'feature', or 'epic'")
    entity_id: str = Field(..., description="UUID of the story/feature/epic")
    link_type: Optional[str] = Field(None, description="Link type: implements, validates, triggers, contains, governs")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Link confidence (0.0-1.0)")
    linked_by: Optional[str] = Field("api", description="Who/what created the link")
    link_reason: Optional[str] = Field(None, description="Reason for this link")


class UnlinkRuleRequest(BaseModel):
    """Request to unlink a business rule from a work item."""
    rule_id: str
    entity_type: str = Field(..., description="'story', 'feature', or 'epic'")
    entity_id: str


class RuleLinkResponse(BaseModel):
    """Response for a rule link."""
    id: int
    rule_id: str
    entity_id: str
    entity_type: str
    link_type: str
    confidence: Optional[float]
    linked_by: Optional[str]
    link_reason: Optional[str]
    created_at: Optional[str]


class RuleResponse(BaseModel):
    """Business rule details."""
    id: str
    rule_type: str
    natural_language: Optional[str]
    source_file: Optional[str]
    entity_name: Optional[str]
    confidence: Optional[float]
    link_type: str
    linked_by: Optional[str]


class RuleImpactResponse(BaseModel):
    """Impact analysis for a business rule."""
    rule_id: str
    rule_type: str
    rule_description: str
    source_file: Optional[str]
    entity_name: Optional[str]
    story_count: int
    feature_count: int
    epic_count: int
    affected_stories: List[str]
    affected_features: List[str]
    affected_epics: List[str]


class TraceabilityMatrixRowResponse(BaseModel):
    """Single row in the traceability matrix."""
    epic_id: Optional[str]
    epic_title: Optional[str]
    feature_id: Optional[str]
    feature_title: Optional[str]
    story_id: Optional[str]
    story_title: Optional[str]
    rule_id: Optional[str]
    rule_type: Optional[str]
    rule_description: Optional[str]
    rule_confidence: Optional[float]
    link_type: Optional[str]
    linked_by: Optional[str]


class TraceabilitySummaryResponse(BaseModel):
    """Summary statistics for traceability."""
    total_rules: int
    linked_rules: int
    unlinked_rules: int
    total_stories: int
    stories_with_rules: int
    stories_without_rules: int
    avg_rules_per_story: float
    workflows_detected: int
    coverage_percentage: float


class SuggestLinksResponse(BaseModel):
    """Suggested links for a story."""
    story_id: str
    suggestions: List[Dict[str, Any]]
    suggestion_count: int


class WorkflowResponse(BaseModel):
    """CRUD workflow grouping."""
    id: int
    name: str
    workflow_type: str
    entity_name: Optional[str]
    description: Optional[str]
    rule_count: int
    operations: Optional[Dict[str, List[str]]]
    mermaid_diagram: Optional[str]
    created_at: Optional[str]


class DetectWorkflowsRequest(BaseModel):
    """Request to detect CRUD workflows."""
    project_id: int
    min_rules_per_workflow: int = Field(2, ge=1, description="Minimum rules to form a workflow")


# ============================================================================
# Service Dependency
# ============================================================================

def get_traceability_service(session: AsyncSession = Depends(get_db)) -> TraceabilityService:
    """Get traceability service instance."""
    return TraceabilityService(session)


# ============================================================================
# Link Management Endpoints
# ============================================================================

@router.post("/link", response_model=RuleLinkResponse)
async def link_rule(
    request: LinkRuleRequest,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Link a business rule to a story, feature, or epic.

    Creates a traceability link for impact analysis and compliance tracking.
    """
    try:
        entity_id = UUID(request.entity_id)
        link_type_enum = LinkType(request.link_type) if request.link_type else None

        if request.entity_type == "story":
            link = await service.link_rule_to_story(
                story_id=entity_id,
                rule_id=request.rule_id,
                link_type=link_type_enum,
                confidence=request.confidence,
                linked_by=request.linked_by,
                link_reason=request.link_reason
            )
        elif request.entity_type == "feature":
            link = await service.link_rule_to_feature(
                feature_id=entity_id,
                rule_id=request.rule_id,
                link_type=link_type_enum,
                confidence=request.confidence,
                linked_by=request.linked_by,
                link_reason=request.link_reason
            )
        elif request.entity_type == "epic":
            link = await service.link_rule_to_epic(
                epic_id=entity_id,
                rule_id=request.rule_id,
                link_type=link_type_enum,
                confidence=request.confidence,
                linked_by=request.linked_by,
                link_reason=request.link_reason
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid entity_type: {request.entity_type}")

        return RuleLinkResponse(
            id=link.id,
            rule_id=link.rule_id,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            link_type=link.link_type,
            confidence=link.confidence,
            linked_by=link.linked_by,
            link_reason=link.link_reason,
            created_at=link.created_at.isoformat() if link.created_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create link: {str(e)}")


@router.delete("/link")
async def unlink_rule(
    request: UnlinkRuleRequest,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Remove a traceability link between a business rule and work item.
    """
    try:
        entity_id = UUID(request.entity_id)

        if request.entity_type == "story":
            success = await service.unlink_rule_from_story(entity_id, request.rule_id)
        elif request.entity_type == "feature":
            success = await service.unlink_rule_from_feature(entity_id, request.rule_id)
        elif request.entity_type == "epic":
            success = await service.unlink_rule_from_epic(entity_id, request.rule_id)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid entity_type: {request.entity_type}")

        if not success:
            raise HTTPException(status_code=404, detail="Link not found")

        return {"status": "success", "message": "Link removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove link: {str(e)}")


# ============================================================================
# Query Endpoints
# ============================================================================

@router.get("/story/{story_id}/rules", response_model=List[RuleResponse])
async def get_rules_for_story(
    story_id: UUID,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get all business rules linked to a story.
    """
    try:
        rules = await service.get_rules_for_story(story_id)
        return [
            RuleResponse(
                id=r["id"],
                rule_type=r.get("rule_type", ""),
                natural_language=r.get("natural_language"),
                source_file=r.get("source_file"),
                entity_name=r.get("entity_name"),
                confidence=r.get("link_confidence"),
                link_type=r.get("link_type", "implements"),
                linked_by=r.get("linked_by")
            ) for r in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature/{feature_id}/rules", response_model=List[RuleResponse])
async def get_rules_for_feature(
    feature_id: UUID,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get all business rules linked to a feature.
    """
    try:
        rules = await service.get_rules_for_feature(feature_id)
        return [
            RuleResponse(
                id=r["id"],
                rule_type=r.get("rule_type", ""),
                natural_language=r.get("natural_language"),
                source_file=r.get("source_file"),
                entity_name=r.get("entity_name"),
                confidence=r.get("link_confidence"),
                link_type=r.get("link_type", "contains"),
                linked_by=r.get("linked_by")
            ) for r in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/epic/{epic_id}/rules", response_model=List[RuleResponse])
async def get_rules_for_epic(
    epic_id: UUID,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get all business rules linked to an epic.
    """
    try:
        rules = await service.get_rules_for_epic(epic_id)
        return [
            RuleResponse(
                id=r["id"],
                rule_type=r.get("rule_type", ""),
                natural_language=r.get("natural_language"),
                source_file=r.get("source_file"),
                entity_name=r.get("entity_name"),
                confidence=r.get("link_confidence"),
                link_type=r.get("link_type", "governs"),
                linked_by=r.get("linked_by")
            ) for r in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}/stories")
async def get_stories_for_rule(
    rule_id: str,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get all stories that implement a specific business rule.
    """
    try:
        stories = await service.get_stories_for_rule(rule_id)
        return {"rule_id": rule_id, "stories": stories, "count": len(stories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Impact Analysis Endpoints
# ============================================================================

@router.get("/rule/{rule_id}/impact", response_model=RuleImpactResponse)
async def get_rule_impact(
    rule_id: str,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get impact analysis for a business rule change.

    Shows all stories, features, and epics that would be affected
    if this business rule changes.
    """
    try:
        impact = await service.get_rule_impact(rule_id)
        if not impact:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        return RuleImpactResponse(
            rule_id=impact.rule_id,
            rule_type=impact.rule_type,
            rule_description=impact.rule_description,
            source_file=impact.source_file,
            entity_name=impact.entity_name,
            story_count=impact.story_count,
            feature_count=impact.feature_count,
            epic_count=impact.epic_count,
            affected_stories=impact.affected_stories,
            affected_features=impact.affected_features,
            affected_epics=impact.affected_epics
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/impact")
async def get_multi_rule_impact(
    rule_ids: List[str],
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get impact analysis for multiple business rules.

    Useful for analyzing the combined impact of a set of related rules.
    """
    try:
        impacts = await service.get_multi_rule_impact(rule_ids)
        return {
            "rule_ids": rule_ids,
            "impacts": [
                {
                    "rule_id": i.rule_id,
                    "rule_type": i.rule_type,
                    "story_count": i.story_count,
                    "feature_count": i.feature_count,
                    "epic_count": i.epic_count,
                } for i in impacts
            ],
            "total_stories_affected": len(set(s for i in impacts for s in i.affected_stories)),
            "total_features_affected": len(set(f for i in impacts for f in i.affected_features)),
            "total_epics_affected": len(set(e for i in impacts for e in i.affected_epics)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Traceability Matrix Endpoints
# ============================================================================

@router.get("/matrix/{project_id}", response_model=List[TraceabilityMatrixRowResponse])
async def get_traceability_matrix(
    project_id: int,
    epic_id: Optional[UUID] = None,
    feature_id: Optional[UUID] = None,
    rule_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get traceability matrix showing epic → feature → story → rule relationships.

    Optional filters:
    - epic_id: Filter to a specific epic
    - feature_id: Filter to a specific feature
    - rule_type: Filter to a specific rule type (authorization, validation, etc.)
    """
    try:
        rows = await service.get_traceability_matrix(
            project_id=project_id,
            epic_id=epic_id,
            feature_id=feature_id,
            rule_type=rule_type,
            limit=limit,
            offset=offset
        )
        return [
            TraceabilityMatrixRowResponse(
                epic_id=r.epic_id,
                epic_title=r.epic_title,
                feature_id=r.feature_id,
                feature_title=r.feature_title,
                story_id=r.story_id,
                story_title=r.story_title,
                rule_id=r.rule_id,
                rule_type=r.rule_type,
                rule_description=r.rule_description,
                rule_confidence=r.rule_confidence,
                link_type=r.link_type,
                linked_by=r.linked_by
            ) for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matrix/{project_id}/export")
async def export_traceability_matrix(
    project_id: int,
    format: str = Query("csv", pattern="^(csv|json)$"),
    epic_id: Optional[UUID] = None,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Export traceability matrix to CSV or JSON format.
    """
    try:
        if format == "csv":
            csv_content = await service.export_matrix_csv(project_id, epic_id)
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=traceability_matrix_{project_id}.csv"
                }
            )
        else:
            rows = await service.get_traceability_matrix(project_id, epic_id)
            return {
                "project_id": project_id,
                "row_count": len(rows),
                "matrix": [
                    {
                        "epic_id": r.epic_id,
                        "epic_title": r.epic_title,
                        "feature_id": r.feature_id,
                        "feature_title": r.feature_title,
                        "story_id": r.story_id,
                        "story_title": r.story_title,
                        "rule_id": r.rule_id,
                        "rule_type": r.rule_type,
                        "rule_description": r.rule_description,
                    } for r in rows
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{project_id}", response_model=TraceabilitySummaryResponse)
async def get_traceability_summary(
    project_id: int,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get summary statistics for traceability coverage.

    Shows:
    - Total rules vs linked rules
    - Stories with/without rules
    - Average rules per story
    - Coverage percentage
    """
    try:
        summary = await service.get_traceability_summary(project_id)
        return TraceabilitySummaryResponse(
            total_rules=summary.total_rules,
            linked_rules=summary.linked_rules,
            unlinked_rules=summary.unlinked_rules,
            total_stories=summary.total_stories,
            stories_with_rules=summary.stories_with_rules,
            stories_without_rules=summary.stories_without_rules,
            avg_rules_per_story=summary.avg_rules_per_story,
            workflows_detected=summary.workflows_detected,
            coverage_percentage=summary.coverage_percentage
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Auto-Linking Endpoints
# ============================================================================

@router.post("/suggest-links/{story_id}", response_model=SuggestLinksResponse)
async def suggest_links_for_story(
    story_id: UUID,
    project_id: int,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get auto-generated link suggestions for a story.

    Uses keyword matching between story content and business rule descriptions
    to suggest potential links. Suggestions are ranked by confidence.
    """
    try:
        suggestions = await service.suggest_links_for_story(
            story_id=story_id,
            project_id=project_id,
            min_confidence=min_confidence,
            limit=limit
        )
        return SuggestLinksResponse(
            story_id=str(story_id),
            suggestions=suggestions,
            suggestion_count=len(suggestions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-link/{story_id}")
async def auto_link_story(
    story_id: UUID,
    project_id: int,
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
    max_links: int = Query(5, ge=1, le=20),
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Automatically create links for a story based on keyword matching.

    Only creates links above the minimum confidence threshold.
    """
    try:
        suggestions = await service.suggest_links_for_story(
            story_id=story_id,
            project_id=project_id,
            min_confidence=min_confidence,
            limit=max_links
        )

        created_links = []
        for suggestion in suggestions:
            link = await service.link_rule_to_story(
                story_id=story_id,
                rule_id=suggestion["rule_id"],
                link_type=LinkType.IMPLEMENTS,
                confidence=suggestion["confidence"],
                linked_by="auto",
                link_reason=f"Auto-linked: {', '.join(suggestion.get('matched_keywords', []))}"
            )
            created_links.append({
                "rule_id": link.rule_id,
                "confidence": link.confidence,
                "link_reason": link.link_reason
            })

        return {
            "story_id": str(story_id),
            "links_created": len(created_links),
            "links": created_links
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Detection Endpoints
# ============================================================================

@router.post("/detect-workflows/{project_id}")
async def detect_crud_workflows(
    project_id: int,
    min_rules: int = Query(2, ge=1, description="Minimum rules per workflow"),
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Detect CRUD workflows by grouping business rules by entity.

    Groups rules like:
    - "Afspraak CRUD": BR-001 (create), BR-015 (read), BR-042 (update), BR-099 (delete)
    - "User Authentication": BR-100 (login), BR-101 (logout), BR-102 (password reset)
    """
    try:
        workflows = await service.detect_crud_workflows(project_id, min_rules)
        return {
            "project_id": project_id,
            "workflows_detected": len(workflows),
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "workflow_type": w.workflow_type,
                    "entity_name": w.entity_name,
                    "rule_count": w.rule_count,
                    "operations": w.operations,
                    "mermaid_diagram": w.mermaid_diagram
                } for w in workflows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{project_id}", response_model=List[WorkflowResponse])
async def get_project_workflows(
    project_id: int,
    workflow_type: Optional[str] = None,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get all detected workflows for a project.
    """
    try:
        workflows = await service.get_project_workflows(project_id, workflow_type)
        return [
            WorkflowResponse(
                id=w.id,
                name=w.name,
                workflow_type=w.workflow_type,
                entity_name=w.entity_name,
                description=w.description,
                rule_count=w.rule_count,
                operations=w.operations,
                mermaid_diagram=w.mermaid_diagram,
                created_at=w.created_at.isoformat() if w.created_at else None
            ) for w in workflows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get a specific workflow by ID.
    """
    try:
        workflow = await service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        return WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            workflow_type=workflow.workflow_type,
            entity_name=workflow.entity_name,
            description=workflow.description,
            rule_count=workflow.rule_count,
            operations=workflow.operations,
            mermaid_diagram=workflow.mermaid_diagram,
            created_at=workflow.created_at.isoformat() if workflow.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}/mermaid")
async def get_workflow_mermaid(
    workflow_id: int,
    service: TraceabilityService = Depends(get_traceability_service)
):
    """
    Get Mermaid diagram for a workflow visualization.
    """
    try:
        workflow = await service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        # Generate if not cached
        if not workflow.mermaid_diagram:
            mermaid = workflow.generate_mermaid()
        else:
            mermaid = workflow.mermaid_diagram

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "mermaid": mermaid
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
