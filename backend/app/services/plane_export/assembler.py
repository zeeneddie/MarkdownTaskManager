"""
Plane Export Assembler - Assembles rich M8+M9+Peter data into PlaneExportPackage.

Takes the FULL M8 dataclasses (not the lossy dicts from _epic_to_dict),
M9 estimation results, and Peter enrichments to produce a complete
export package with all data preserved.

This is the key integration point: output from earlier pipeline stages
flows into this assembler to enrich the final export.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    ExportAcceptanceCriterion,
    ExportEpic,
    ExportFeature,
    ExportProjectSummary,
    ExportRelation,
    ExportSourceReference,
    ExportStory,
    PlanePriority,
    PlaneExportPackage,
    PlaneStatus,
    RelationType,
)
from .priority_mapper import PriorityMapper

logger = logging.getLogger(__name__)


class PlaneExportAssembler:
    """
    Assembles a PlaneExportPackage from full pipeline data.

    Input sources:
    - M8 StoryGenerationResult (full dataclasses with acceptance_criteria, source_refs)
    - M9 EstimationResult (IFPUG FP, effort estimates, team recommendations)
    - Peter enrichments (business priority, context)
    - M7 domain data (confidence scores, for priority inference)
    """

    def __init__(self):
        self._priority_mapper = PriorityMapper()

    def assemble(
        self,
        generation_result,  # M8 StoryGenerationResult (from business_driven_story_generator_service)
        estimation_result=None,  # M9 EstimationResult (from onboarding.py)
        peter_enrichments: Optional[Dict] = None,
        project_context: Optional[Dict] = None,
        session_id: Optional[str] = None,
        domain_data: Optional[Dict] = None,  # M7 domain extraction for confidence scores
    ) -> PlaneExportPackage:
        """
        Assemble a complete PlaneExportPackage.

        Args:
            generation_result: M8 result with full GeneratedEpic trees
            estimation_result: M9 EstimationResult with FP analysis
            peter_enrichments: Peter agent business enrichments
            project_context: Project answers, path, etc.
            session_id: Workflow session ID for traceability
            domain_data: M7 domain extraction with confidence scores
        """
        project_path = ""
        if project_context:
            project_path = project_context.get("project_path", "")
        elif estimation_result and hasattr(estimation_result, "project_path"):
            project_path = estimation_result.project_path

        # Build domain confidence lookup from M7 data
        domain_confidence_map = self._build_domain_confidence_map(domain_data)

        # Build Peter priority lookup
        peter_priority_map = self._build_peter_priority_map(peter_enrichments)

        # Assemble epics with full data preservation
        export_epics = []
        all_relations = []

        for epic in generation_result.epics:
            domain_confidence = domain_confidence_map.get(epic.domain_name)
            export_epic, epic_relations = self._assemble_epic(
                epic, domain_confidence, peter_priority_map
            )
            export_epics.append(export_epic)
            all_relations.extend(epic_relations)

        # Build project summary with M9 data
        project_summary = self._build_project_summary(
            project_path, generation_result, estimation_result
        )

        # Build stage versions for traceability
        stage_versions = {
            "m8_story_generation": "w159",
            "plane_export": "1.0.0",
        }
        if estimation_result:
            stage_versions["m9_estimation"] = "ifpug"
        if peter_enrichments:
            stage_versions["peter_enrichment"] = "v1"

        return PlaneExportPackage(
            version="1.0.0",
            exported_at=datetime.now(timezone.utc),
            session_id=session_id,
            source="marqed",
            project_summary=project_summary,
            epics=export_epics,
            relations=all_relations,
            stage_versions=stage_versions,
            generation_metadata={
                "generation_time_ms": generation_result.generation_time_ms,
                "domains_processed": generation_result.metadata.get("domains_processed", 0),
                "has_peter_enrichments": peter_enrichments is not None,
                "has_estimation": estimation_result is not None,
                "has_domain_confidence": bool(domain_confidence_map),
            },
        )

    def _assemble_epic(
        self,
        epic,  # GeneratedEpic dataclass
        domain_confidence: Optional[float],
        peter_priority_map: Dict[str, str],
    ) -> tuple:
        """Assemble an ExportEpic from a GeneratedEpic, preserving all data."""
        export_features = []
        all_relations = []
        feature_priorities = []

        for feature in epic.features:
            export_feature, feature_relations = self._assemble_feature(
                feature, domain_confidence, peter_priority_map
            )
            export_features.append(export_feature)
            all_relations.extend(feature_relations)
            feature_priorities.append(export_feature.priority)

        epic_priority = self._priority_mapper.map_epic_priority(
            epic_complexity=epic.complexity,
            domain_confidence=domain_confidence,
            feature_priorities=feature_priorities,
        )

        export_epic = ExportEpic(
            id=epic.id,
            title=epic.title,
            description=epic.description,
            domain_name=epic.domain_name,
            features=export_features,
            source_modules=epic.source_modules,
            estimated_story_points=epic.estimated_story_points,
            estimated_weeks=epic.estimated_weeks,
            complexity=epic.complexity,
            priority=epic_priority,
            status=PlaneStatus(epic.status) if epic.status in PlaneStatus.__members__ else PlaneStatus.backlog,
            metadata={
                **epic.metadata,
                "domain_confidence": domain_confidence,
            },
        )

        return export_epic, all_relations

    def _assemble_feature(
        self,
        feature,  # GeneratedFeature dataclass
        domain_confidence: Optional[float],
        peter_priority_map: Dict[str, str],
    ) -> tuple:
        """Assemble an ExportFeature from a GeneratedFeature."""
        export_stories = []
        all_relations = []
        story_priorities = []

        for story in feature.stories:
            export_story = self._assemble_story(
                story, domain_confidence, peter_priority_map
            )
            export_stories.append(export_story)
            story_priorities.append(export_story.priority)

            # Collect blocked_by relations
            for blocked_by_id in story.blocked_by:
                all_relations.append(ExportRelation(
                    source_id=story.id,
                    target_id=blocked_by_id,
                    relation_type=RelationType.blocked_by,
                    reason="CRUD dependency chain",
                ))

        feature_priority = self._priority_mapper.map_feature_priority(
            feature_complexity=feature.complexity,
            story_priorities=story_priorities,
            domain_confidence=domain_confidence,
        )

        export_feature = ExportFeature(
            id=feature.id,
            title=feature.title,
            description=feature.description,
            epic_id=feature.epic_id,
            stories=export_stories,
            source_modules=feature.source_modules,
            estimated_story_points=feature.estimated_story_points,
            complexity=feature.complexity,
            priority=feature_priority,
            status=PlaneStatus(feature.status) if feature.status in PlaneStatus.__members__ else PlaneStatus.backlog,
        )

        return export_feature, all_relations

    def _assemble_story(
        self,
        story,  # GeneratedStory dataclass
        domain_confidence: Optional[float],
        peter_priority_map: Dict[str, str],
    ) -> ExportStory:
        """
        Assemble an ExportStory from a GeneratedStory.

        This is where data that _epic_to_dict() discards is PRESERVED:
        - acceptance_criteria (full list)
        - source_references (full list with line numbers)
        - legacy_functionality
        - target_implementation
        - blocked_by dependencies
        """
        # Map acceptance criteria
        export_criteria = [
            ExportAcceptanceCriterion(
                id=ac.id,
                description=ac.description,
                test_type=ac.test_type,
                source_hint=ac.source_hint,
            )
            for ac in story.acceptance_criteria
        ]

        # Map source references
        export_refs = [
            ExportSourceReference(
                file_path=ref.file_path,
                line_start=ref.line_start,
                line_end=ref.line_end,
                code_snippet=ref.code_snippet,
                element_type=ref.element_type,
            )
            for ref in story.source_references
        ]

        # Get Peter priority for this story (if available)
        peter_priority = peter_priority_map.get(story.id)

        # Determine priority using all available signals
        story_priority = self._priority_mapper.map_story_priority(
            story_priority=story.priority,
            story_type=story.story_type,
            complexity=story.complexity,
            peter_priority=peter_priority,
            domain_confidence=domain_confidence,
        )

        return ExportStory(
            id=story.id,
            title=story.title,
            description=story.description,
            feature_id=story.feature_id,
            story_points=story.story_points,
            complexity=story.complexity,
            story_type=story.story_type,
            priority=story_priority,
            status=PlaneStatus(story.status) if story.status in PlaneStatus.__members__ else PlaneStatus.backlog,
            acceptance_criteria=export_criteria,
            source_references=export_refs,
            legacy_functionality=story.legacy_functionality,
            target_implementation=story.target_implementation,
            business_value=story.business_value,
            blocked_by=story.blocked_by,
            relations=[
                ExportRelation(
                    source_id=story.id,
                    target_id=blocked_id,
                    relation_type=RelationType.blocked_by,
                    reason="CRUD dependency chain",
                )
                for blocked_id in story.blocked_by
            ],
            metadata=story.metadata,
        )

    def _build_project_summary(
        self,
        project_path: str,
        generation_result,
        estimation_result,
    ) -> ExportProjectSummary:
        """Build project summary from M8 + M9 data."""
        import os

        summary = ExportProjectSummary(
            project_path=project_path,
            project_name=os.path.basename(project_path) if project_path else "",
            total_epics=len(generation_result.epics),
            total_features=generation_result.total_features,
            total_stories=generation_result.total_stories,
            total_story_points=generation_result.total_story_points,
        )

        # Enrich with M9 estimation data if available
        if estimation_result:
            summary.estimated_weeks_low = getattr(estimation_result, "estimated_weeks_low", 0)
            summary.estimated_weeks_high = getattr(estimation_result, "estimated_weeks_high", 0)
            summary.estimated_weeks_likely = getattr(estimation_result, "estimated_weeks_likely", 0)
            summary.unadjusted_fp = getattr(estimation_result, "unadjusted_fp", 0.0)
            summary.adjusted_fp = getattr(estimation_result, "adjusted_fp", 0.0)
            summary.total_effort_person_days = getattr(estimation_result, "total_effort_person_days", 0.0)
            summary.recommended_team_size = getattr(estimation_result, "recommended_team_size", 0)
            summary.estimation_confidence = getattr(estimation_result, "confidence_level", 0.0)
            summary.risk_factors = getattr(estimation_result, "risk_factors", []) or []
            summary.recommendations = getattr(estimation_result, "recommendations", []) or []

        return summary

    def _build_domain_confidence_map(
        self, domain_data: Optional[Dict],
    ) -> Dict[str, float]:
        """Build a lookup of domain_name -> confidence from M7 data."""
        if not domain_data:
            return {}

        confidence_map = {}

        # M7 domain extraction stores domains as list of dicts
        domains = domain_data.get("domains", [])
        for domain in domains:
            name = domain.get("name", "")
            confidence = domain.get("confidence", 0.0)
            if name:
                confidence_map[name] = confidence

        return confidence_map

    def _build_peter_priority_map(
        self, peter_enrichments: Optional[Dict],
    ) -> Dict[str, str]:
        """Build a lookup of story_id -> priority from Peter enrichments."""
        if not peter_enrichments:
            return {}

        priority_map = {}

        # Peter enrichments may contain story-level priorities
        story_enrichments = peter_enrichments.get("story_enrichments", {})
        for story_id, enrichment in story_enrichments.items():
            priority = enrichment.get("priority")
            if priority:
                priority_map[story_id] = priority

        # Also check enriched_stories format
        enriched_stories = peter_enrichments.get("enriched_stories", [])
        for story in enriched_stories:
            story_id = story.get("id", "")
            priority = story.get("priority")
            if story_id and priority:
                priority_map[story_id] = priority

        return priority_map
