# backend/app/services/traceability_service.py
"""
Week 113: Traceability Service

Business logic for:
- Linking business rules to stories/features/epics
- Impact analysis: "Which stories are affected if BR-042 changes?"
- Traceability matrix generation
- Auto-linking suggestions based on entity/keyword matching
- CRUD workflow detection and grouping
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.traceability import (
    StoryBusinessRule,
    FeatureBusinessRule,
    EpicBusinessRule,
    RuleWorkflow,
    RuleWorkflowMember,
    LinkType,
    WorkflowType,
    CRUDOperation,
    TraceabilityMatrixRow,
    RuleImpact,
    TraceabilitySummary,
)
from app.models.static_analysis import BusinessRule
from app.models.task_hierarchy import Epic, Feature, Story

logger = logging.getLogger(__name__)


class TraceabilityService:
    """
    Service for managing traceability between business rules and work items.

    Supports:
    - Manual linking (user creates links)
    - Auto-linking (based on entity/keyword matching)
    - Impact analysis (which work items are affected by a rule change)
    - Traceability matrix export
    - CRUD workflow detection
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # LINK MANAGEMENT
    # =========================================================================

    async def link_rule_to_story(
        self,
        story_id: UUID,
        rule_id: str,
        link_type: LinkType = LinkType.IMPLEMENTS,
        confidence: Optional[float] = None,
        linked_by: str = "user",
        link_reason: Optional[str] = None,
    ) -> StoryBusinessRule:
        """
        Link a business rule to a user story.

        Args:
            story_id: UUID of the story
            rule_id: ID of the business rule (e.g., "BR-001")
            link_type: Type of relationship (implements, validates, triggers)
            confidence: Confidence score for auto-links (0.0-1.0)
            linked_by: Who created the link ("auto", "user_xyz", "peter")
            link_reason: Why this link was created

        Returns:
            The created StoryBusinessRule record
        """
        link = StoryBusinessRule(
            story_id=story_id,
            rule_id=rule_id,
            link_type=link_type.value,
            confidence=confidence,
            linked_by=linked_by,
            link_reason=link_reason,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        logger.info(f"Linked rule {rule_id} to story {story_id} ({link_type.value})")
        return link

    async def link_rule_to_feature(
        self,
        feature_id: UUID,
        rule_id: str,
        link_type: LinkType = LinkType.CONTAINS,
        confidence: Optional[float] = None,
        linked_by: str = "user",
        link_reason: Optional[str] = None,
    ) -> FeatureBusinessRule:
        """Link a business rule to a feature."""
        link = FeatureBusinessRule(
            feature_id=feature_id,
            rule_id=rule_id,
            link_type=link_type.value,
            confidence=confidence,
            linked_by=linked_by,
            link_reason=link_reason,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        logger.info(f"Linked rule {rule_id} to feature {feature_id}")
        return link

    async def link_rule_to_epic(
        self,
        epic_id: UUID,
        rule_id: str,
        link_type: LinkType = LinkType.GOVERNS,
        confidence: Optional[float] = None,
        linked_by: str = "user",
        link_reason: Optional[str] = None,
    ) -> EpicBusinessRule:
        """Link a business rule to an epic."""
        link = EpicBusinessRule(
            epic_id=epic_id,
            rule_id=rule_id,
            link_type=link_type.value,
            confidence=confidence,
            linked_by=linked_by,
            link_reason=link_reason,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        logger.info(f"Linked rule {rule_id} to epic {epic_id}")
        return link

    async def unlink_rule_from_story(self, story_id: UUID, rule_id: str) -> bool:
        """Remove a link between a rule and a story."""
        result = await self.db.execute(
            select(StoryBusinessRule).where(
                and_(
                    StoryBusinessRule.story_id == story_id,
                    StoryBusinessRule.rule_id == rule_id,
                )
            )
        )
        link = result.scalar_one_or_none()
        if link:
            await self.db.delete(link)
            await self.db.commit()
            logger.info(f"Unlinked rule {rule_id} from story {story_id}")
            return True
        return False

    async def get_rules_for_story(self, story_id: UUID) -> List[Dict[str, Any]]:
        """Get all business rules linked to a story."""
        result = await self.db.execute(
            select(StoryBusinessRule, BusinessRule)
            .join(BusinessRule, StoryBusinessRule.rule_id == BusinessRule.id)
            .where(StoryBusinessRule.story_id == story_id)
        )
        rows = result.all()
        return [
            {
                **link.to_dict(),
                "rule": rule.to_dict() if rule else None,
            }
            for link, rule in rows
        ]

    async def get_stories_for_rule(self, rule_id: str) -> List[Dict[str, Any]]:
        """Get all stories linked to a business rule."""
        result = await self.db.execute(
            select(StoryBusinessRule, Story)
            .join(Story, StoryBusinessRule.story_id == Story.id)
            .where(StoryBusinessRule.rule_id == rule_id)
        )
        rows = result.all()
        return [
            {
                **link.to_dict(),
                "story": {
                    "id": str(story.id),
                    "title": story.title,
                    "status": story.status,
                    "story_points": story.story_points,
                } if story else None,
            }
            for link, story in rows
        ]

    # =========================================================================
    # IMPACT ANALYSIS
    # =========================================================================

    async def get_rule_impact(self, rule_id: str) -> RuleImpact:
        """
        Analyze the impact of changing a business rule.

        Returns:
            RuleImpact with counts and lists of affected work items
        """
        # Get the rule
        rule_result = await self.db.execute(
            select(BusinessRule).where(BusinessRule.id == rule_id)
        )
        rule = rule_result.scalar_one_or_none()

        if not rule:
            return RuleImpact(
                rule_id=rule_id,
                rule_type="unknown",
                rule_description="Rule not found",
            )

        # Get affected stories via v_rule_impact view
        # Note: Using raw SQL for the view query
        impact_query = text("""
            SELECT
                story_count,
                feature_count,
                epic_count,
                affected_stories,
                affected_features,
                affected_epics
            FROM v_rule_impact
            WHERE rule_id = :rule_id
        """)

        try:
            result = await self.db.execute(impact_query, {"rule_id": rule_id})
            row = result.first()

            if row:
                return RuleImpact(
                    rule_id=rule_id,
                    rule_type=rule.rule_type,
                    rule_description=rule.natural_language,
                    source_file=rule.source_file,
                    entity_name=getattr(rule, 'entity_name', None),
                    story_count=row.story_count or 0,
                    feature_count=row.feature_count or 0,
                    epic_count=row.epic_count or 0,
                    affected_stories=row.affected_stories or [],
                    affected_features=row.affected_features or [],
                    affected_epics=row.affected_epics or [],
                )
        except Exception as e:
            logger.warning(f"View query failed, using fallback: {e}")

        # Fallback: Manual query if view doesn't exist
        stories = await self.get_stories_for_rule(rule_id)

        return RuleImpact(
            rule_id=rule_id,
            rule_type=rule.rule_type,
            rule_description=rule.natural_language,
            source_file=rule.source_file,
            entity_name=getattr(rule, 'entity_name', None),
            story_count=len(stories),
            affected_stories=[s["story"]["title"] for s in stories if s.get("story")],
        )

    async def get_multi_rule_impact(self, rule_ids: List[str]) -> Dict[str, RuleImpact]:
        """Get impact analysis for multiple rules."""
        return {
            rule_id: await self.get_rule_impact(rule_id)
            for rule_id in rule_ids
        }

    # =========================================================================
    # TRACEABILITY MATRIX
    # =========================================================================

    async def get_traceability_matrix(
        self,
        project_id: Optional[str] = None,
        epic_id: Optional[UUID] = None,
        feature_id: Optional[UUID] = None,
    ) -> List[TraceabilityMatrixRow]:
        """
        Generate a traceability matrix.

        Returns rows linking epics → features → stories → rules.
        """
        # Build query using the view
        query = text("""
            SELECT
                epic_id, epic_title,
                feature_id, feature_title,
                story_id, story_title,
                rule_id, rule_type, rule_description, rule_confidence,
                link_type, linked_by, project_id
            FROM v_traceability_matrix
            WHERE 1=1
            """ + (f" AND project_id = :project_id" if project_id else "") + """
            """ + (f" AND epic_id = :epic_id" if epic_id else "") + """
            """ + (f" AND feature_id = :feature_id" if feature_id else "") + """
            ORDER BY epic_title, feature_title, story_title, rule_id
        """)

        params = {}
        if project_id:
            params["project_id"] = project_id
        if epic_id:
            params["epic_id"] = str(epic_id)
        if feature_id:
            params["feature_id"] = str(feature_id)

        try:
            result = await self.db.execute(query, params)
            rows = result.all()

            return [
                TraceabilityMatrixRow(
                    epic_id=str(row.epic_id) if row.epic_id else None,
                    epic_title=row.epic_title,
                    feature_id=str(row.feature_id) if row.feature_id else None,
                    feature_title=row.feature_title,
                    story_id=str(row.story_id) if row.story_id else None,
                    story_title=row.story_title,
                    rule_id=row.rule_id,
                    rule_type=row.rule_type,
                    rule_description=row.rule_description,
                    rule_confidence=row.rule_confidence,
                    link_type=row.link_type,
                    linked_by=row.linked_by,
                )
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"Matrix view query failed: {e}")
            return []

    async def export_matrix_csv(
        self,
        project_id: Optional[str] = None,
    ) -> str:
        """Export traceability matrix as CSV."""
        rows = await self.get_traceability_matrix(project_id=project_id)

        csv_lines = [
            "Epic ID,Epic Title,Feature ID,Feature Title,Story ID,Story Title,Rule ID,Rule Type,Rule Description,Confidence,Link Type"
        ]
        for row in rows:
            csv_lines.append(
                f'"{row.epic_id or ""}","{row.epic_title or ""}","{row.feature_id or ""}","{row.feature_title or ""}",'
                f'"{row.story_id or ""}","{row.story_title or ""}","{row.rule_id or ""}","{row.rule_type or ""}",'
                f'"{row.rule_description or ""}",{row.rule_confidence or ""},"{row.link_type or ""}"'
            )

        return "\n".join(csv_lines)

    # =========================================================================
    # SUMMARY STATISTICS
    # =========================================================================

    async def get_traceability_summary(self, project_id: Optional[int] = None) -> TraceabilitySummary:
        """Get summary statistics for traceability coverage."""
        # Total rules
        rules_query = select(func.count(BusinessRule.id))
        if project_id:
            rules_query = rules_query.join(
                StoryBusinessRule, BusinessRule.id == StoryBusinessRule.rule_id, isouter=True
            )
        rules_result = await self.db.execute(rules_query)
        total_rules = rules_result.scalar() or 0

        # Linked rules (rules with at least one story link)
        linked_query = select(func.count(func.distinct(StoryBusinessRule.rule_id)))
        linked_result = await self.db.execute(linked_query)
        linked_rules = linked_result.scalar() or 0

        # Total stories
        stories_query = select(func.count(Story.id))
        stories_result = await self.db.execute(stories_query)
        total_stories = stories_result.scalar() or 0

        # Stories with rules
        stories_with_rules_query = select(func.count(func.distinct(StoryBusinessRule.story_id)))
        stories_with_rules_result = await self.db.execute(stories_with_rules_query)
        stories_with_rules = stories_with_rules_result.scalar() or 0

        # Workflows
        workflows_query = select(func.count(RuleWorkflow.id))
        if project_id:
            workflows_query = workflows_query.where(RuleWorkflow.project_id == project_id)
        workflows_result = await self.db.execute(workflows_query)
        workflows_count = workflows_result.scalar() or 0

        # Calculate averages
        avg_rules = linked_rules / max(stories_with_rules, 1)
        coverage = (linked_rules / max(total_rules, 1)) * 100

        return TraceabilitySummary(
            total_rules=total_rules,
            linked_rules=linked_rules,
            unlinked_rules=total_rules - linked_rules,
            total_stories=total_stories,
            stories_with_rules=stories_with_rules,
            stories_without_rules=total_stories - stories_with_rules,
            avg_rules_per_story=round(avg_rules, 2),
            workflows_detected=workflows_count,
            coverage_percentage=round(coverage, 1),
        )

    # =========================================================================
    # AUTO-LINKING SUGGESTIONS
    # =========================================================================

    async def suggest_links_for_story(
        self,
        story_id: UUID,
        min_confidence: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Suggest business rules that might be related to a story.

        Uses keyword/entity matching to find potential links.
        """
        # Get the story
        story_result = await self.db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = story_result.scalar_one_or_none()

        if not story:
            return []

        # Extract keywords from story title and description
        story_text = f"{story.title} {story.description or ''}".lower()
        keywords = self._extract_keywords(story_text)

        # Find rules with matching keywords
        suggestions = []
        rules_result = await self.db.execute(select(BusinessRule))
        rules = rules_result.scalars().all()

        for rule in rules:
            rule_text = f"{rule.natural_language} {rule.condition} {rule.action}".lower()
            score = self._calculate_match_score(keywords, rule_text)

            if score >= min_confidence:
                # Check if already linked
                existing = await self.db.execute(
                    select(StoryBusinessRule).where(
                        and_(
                            StoryBusinessRule.story_id == story_id,
                            StoryBusinessRule.rule_id == rule.id,
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                suggestions.append({
                    "rule_id": rule.id,
                    "rule_type": rule.rule_type,
                    "rule_description": rule.natural_language,
                    "confidence": round(score, 2),
                    "match_reason": f"Keyword match: {', '.join(keywords[:3])}",
                })

        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:10]  # Top 10 suggestions

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant keywords from text."""
        # Simple keyword extraction - in production, use NLP
        stopwords = {"a", "an", "the", "is", "are", "was", "were", "be", "been",
                     "being", "have", "has", "had", "do", "does", "did", "will",
                     "would", "could", "should", "may", "might", "must", "shall",
                     "can", "to", "of", "in", "for", "on", "with", "at", "by",
                     "from", "as", "into", "through", "during", "before", "after",
                     "above", "below", "between", "under", "again", "further",
                     "then", "once", "here", "there", "when", "where", "why",
                     "how", "all", "each", "few", "more", "most", "other", "some",
                     "such", "no", "nor", "not", "only", "own", "same", "so",
                     "than", "too", "very", "just", "and", "but", "if", "or",
                     "because", "until", "while", "this", "that", "these", "those",
                     "i", "want", "user", "als", "wil", "zodat", "ik", "een"}

        words = text.split()
        keywords = [w.strip(".,;:!?\"'()[]{}") for w in words
                   if len(w) > 2 and w.lower() not in stopwords]
        return list(set(keywords))[:20]

    def _calculate_match_score(self, keywords: List[str], text: str) -> float:
        """Calculate match score between keywords and text."""
        if not keywords:
            return 0.0

        matches = sum(1 for kw in keywords if kw in text)
        return matches / len(keywords)

    # =========================================================================
    # CRUD WORKFLOW DETECTION
    # =========================================================================

    async def detect_crud_workflows(
        self,
        project_id: int,
        analysis_id: Optional[str] = None,
    ) -> List[RuleWorkflow]:
        """
        Detect CRUD workflows from business rules.

        Groups rules by entity and operation (create/read/update/delete).
        """
        # Get all rules for the project's analysis
        query = select(BusinessRule)
        if analysis_id:
            query = query.where(BusinessRule.analysis_id == analysis_id)

        result = await self.db.execute(query)
        rules = result.scalars().all()

        # Group rules by entity
        entity_rules: Dict[str, Dict[str, List[BusinessRule]]] = {}

        for rule in rules:
            entity = getattr(rule, 'entity_name', None) or self._infer_entity(rule)
            if not entity:
                continue

            if entity not in entity_rules:
                entity_rules[entity] = {
                    "create": [], "read": [], "update": [], "delete": [],
                    "validate": [], "authorize": []
                }

            # Classify the rule's operation
            operation = self._classify_operation(rule)
            entity_rules[entity][operation].append(rule)

        # Create workflow records
        workflows = []
        for entity, ops in entity_rules.items():
            # Only create workflow if we have at least 2 operations
            ops_with_rules = [op for op, rules in ops.items() if rules]
            if len(ops_with_rules) < 2:
                continue

            # Build operations JSONB
            operations = {
                op: [r.id for r in rules]
                for op, rules in ops.items() if rules
            }

            workflow = RuleWorkflow(
                project_id=project_id,
                name=f"{entity} CRUD",
                workflow_type=WorkflowType.CRUD.value,
                entity_name=entity,
                description=f"CRUD operations for {entity} entity",
                rule_count=sum(len(rules) for rules in ops.values()),
                operations=operations,
            )

            # Generate Mermaid diagram
            workflow.mermaid_diagram = workflow.generate_mermaid()

            self.db.add(workflow)
            workflows.append(workflow)

        await self.db.commit()

        # Refresh and add members
        for workflow in workflows:
            await self.db.refresh(workflow)
            for op, rule_ids in workflow.operations.items():
                for i, rule_id in enumerate(rule_ids):
                    member = RuleWorkflowMember(
                        workflow_id=workflow.id,
                        rule_id=rule_id,
                        operation=op,
                        sequence_order=i + 1,
                    )
                    self.db.add(member)

        await self.db.commit()

        logger.info(f"Detected {len(workflows)} CRUD workflows for project {project_id}")
        return workflows

    def _infer_entity(self, rule: BusinessRule) -> Optional[str]:
        """Infer the entity name from rule content."""
        # Look for common patterns in Dutch/English
        text = f"{rule.condition} {rule.action}".lower()

        # Table prefixes (ta = table in Dutch systems)
        import re
        table_match = re.search(r'\b(ta|tbl|table)([a-z_]+)\b', text)
        if table_match:
            return table_match.group(2).title()

        # Common entities
        entities = ["user", "afspraak", "client", "patient", "order", "product",
                   "account", "session", "document", "file", "report", "invoice"]
        for entity in entities:
            if entity in text:
                return entity.title()

        return None

    def _classify_operation(self, rule: BusinessRule) -> str:
        """Classify a rule into a CRUD operation."""
        text = f"{rule.rule_type} {rule.condition} {rule.action}".lower()

        # Authorization patterns
        if any(kw in text for kw in ["authorize", "permission", "can_", "isallowed", "hasrole"]):
            return "authorize"

        # Validation patterns
        if rule.rule_type == "VALIDATION" or any(kw in text for kw in ["validate", "check", "verify", "must be"]):
            return "validate"

        # CRUD patterns
        if any(kw in text for kw in ["insert", "create", "add", "new", "toevoegen"]):
            return "create"
        if any(kw in text for kw in ["select", "read", "get", "fetch", "retrieve", "load", "ophalen"]):
            return "read"
        if any(kw in text for kw in ["update", "modify", "change", "edit", "wijzigen"]):
            return "update"
        if any(kw in text for kw in ["delete", "remove", "destroy", "verwijderen"]):
            return "delete"

        return "validate"  # Default

    async def get_workflow(self, workflow_id: int) -> Optional[RuleWorkflow]:
        """Get a workflow by ID."""
        result = await self.db.execute(
            select(RuleWorkflow)
            .options(selectinload(RuleWorkflow.members))
            .where(RuleWorkflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def get_project_workflows(self, project_id: int) -> List[RuleWorkflow]:
        """Get all workflows for a project."""
        result = await self.db.execute(
            select(RuleWorkflow)
            .options(selectinload(RuleWorkflow.members))
            .where(RuleWorkflow.project_id == project_id)
        )
        return list(result.scalars().all())


# Factory function
def get_traceability_service(db: AsyncSession) -> TraceabilityService:
    """Get a TraceabilityService instance."""
    return TraceabilityService(db)
