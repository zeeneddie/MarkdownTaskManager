# backend/app/services/rmtoo_adapter_service.py
"""
rmtoo Adapter Service - Week 117

Converts MarQed extracted requirements to rmtoo format and vice versa.

Features:
- Convert business rules, functional, NFR, compliance requirements
- Generate .req file content
- Create topic hierarchy
- Handle category prefixes (REQ-BR, REQ-FR, etc.)
- Link to MarQed extraction sessions
"""

from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import re
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.rmtoo import (
    RmtooRequirement,
    RmtooTopic,
    RmtooSyncSession,
    RmtooTraceabilityLink,
    RequirementCategory,
    RequirementStatus,
    SourceType,
    SyncDirection,
    SyncStatus,
    LinkType,
)
from app.models.hybrid_extraction import (
    HybridExtractedRule,
    HybridExtractionSession,
    RuleType,
)


# Category to rmtoo prefix mapping
CATEGORY_PREFIXES = {
    RequirementCategory.BR: "REQ-BR",   # Business Rule
    RequirementCategory.FR: "REQ-FR",   # Functional Requirement
    RequirementCategory.NFR: "REQ-NFR",  # Non-Functional Requirement
    RequirementCategory.TR: "REQ-TR",   # Technical Requirement
    RequirementCategory.CMP: "REQ-CMP",  # Compliance Requirement
}

# Rule type to category mapping
RULE_TYPE_TO_CATEGORY = {
    RuleType.VALIDATION: RequirementCategory.BR,
    RuleType.AUTHORIZATION: RequirementCategory.NFR,
    RuleType.SCHEDULING: RequirementCategory.BR,
    RuleType.WORKFLOW: RequirementCategory.FR,
    RuleType.BRANCHING: RequirementCategory.BR,
    RuleType.THRESHOLD: RequirementCategory.BR,
    RuleType.DATA_ACCESS: RequirementCategory.TR,
    RuleType.STATE_MANAGEMENT: RequirementCategory.FR,
    RuleType.ERROR_HANDLING: RequirementCategory.NFR,
    RuleType.NAVIGATION: RequirementCategory.FR,
    RuleType.CALCULATION: RequirementCategory.BR,
    RuleType.CONSTRAINT: RequirementCategory.BR,
    RuleType.DERIVATION: RequirementCategory.BR,
}

# Default topic structure
DEFAULT_TOPICS = [
    {"name": "BusinessRules", "title": "Business Rules", "description": "Core business logic and validation rules"},
    {"name": "FunctionalRequirements", "title": "Functional Requirements", "description": "System functionality and features"},
    {"name": "NonFunctional", "title": "Non-Functional Requirements", "description": "Performance, security, usability"},
    {"name": "Technical", "title": "Technical Requirements", "description": "Infrastructure and technical constraints"},
    {"name": "Compliance", "title": "Compliance Requirements", "description": "Regulatory and standards compliance"},
]


class RmtooAdapterService:
    """Service for converting between MarQed and rmtoo formats."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._requirement_counters: Dict[str, int] = {}

    async def initialize_topics(self, project_id: int) -> List[RmtooTopic]:
        """Initialize default topic structure for a project."""
        topics = []
        for idx, topic_data in enumerate(DEFAULT_TOPICS):
            # Check if topic exists
            result = await self.db.execute(
                select(RmtooTopic).where(
                    and_(
                        RmtooTopic.project_id == project_id,
                        RmtooTopic.name == topic_data["name"]
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                topics.append(existing)
            else:
                topic = RmtooTopic(
                    id=uuid4(),
                    project_id=project_id,
                    name=topic_data["name"],
                    title=topic_data["title"],
                    description=topic_data["description"],
                    level=0,
                    order_index=idx,
                )
                self.db.add(topic)
                topics.append(topic)

        await self.db.flush()
        return topics

    async def _get_next_requirement_id(self, project_id: int, category: RequirementCategory) -> str:
        """Generate next requirement ID for a category."""
        prefix = CATEGORY_PREFIXES[category]
        cache_key = f"{project_id}_{category.value}"

        if cache_key not in self._requirement_counters:
            # Get max existing ID
            result = await self.db.execute(
                select(func.max(RmtooRequirement.name)).where(
                    and_(
                        RmtooRequirement.project_id == project_id,
                        RmtooRequirement.category == category.value
                    )
                )
            )
            max_name = result.scalar_one_or_none()

            if max_name:
                # Extract number from REQ-BR-001 format
                match = re.search(r'-(\d+)$', max_name)
                if match:
                    self._requirement_counters[cache_key] = int(match.group(1))
                else:
                    self._requirement_counters[cache_key] = 0
            else:
                self._requirement_counters[cache_key] = 0

        self._requirement_counters[cache_key] += 1
        return f"{prefix}-{self._requirement_counters[cache_key]:03d}"

    def _get_topic_for_category(self, category: RequirementCategory) -> str:
        """Get topic name for a category."""
        topic_map = {
            RequirementCategory.BR: "BusinessRules",
            RequirementCategory.FR: "FunctionalRequirements",
            RequirementCategory.NFR: "NonFunctional",
            RequirementCategory.TR: "Technical",
            RequirementCategory.CMP: "Compliance",
        }
        return topic_map.get(category, "BusinessRules")

    async def convert_extracted_rule_to_requirement(
        self,
        rule: HybridExtractedRule,
        session: HybridExtractionSession,
    ) -> RmtooRequirement:
        """Convert a HybridExtractedRule to RmtooRequirement."""
        # Determine category
        rule_type_str = rule.rule_type if isinstance(rule.rule_type, str) else rule.rule_type.value
        try:
            rule_type = RuleType(rule_type_str.upper()) if rule_type_str else RuleType.VALIDATION
        except ValueError:
            rule_type = RuleType.VALIDATION

        category = RULE_TYPE_TO_CATEGORY.get(rule_type, RequirementCategory.BR)

        # Generate requirement ID
        req_id = await self._get_next_requirement_id(session.project_id, category)

        # Build description
        description = rule.description or rule.pattern_code or "No description available"

        # Build rationale from context
        rationale_parts = []
        if rule.source_file:
            rationale_parts.append(f"Extracted from: {rule.source_file}")
        if rule.source_line:
            rationale_parts.append(f"Line: {rule.source_line}")
        if rule.extraction_method:
            rationale_parts.append(f"Method: {rule.extraction_method}")
        rationale = " | ".join(rationale_parts) if rationale_parts else None

        # Get topic
        topic_name = self._get_topic_for_category(category)

        # Find topic ID
        result = await self.db.execute(
            select(RmtooTopic).where(
                and_(
                    RmtooTopic.project_id == session.project_id,
                    RmtooTopic.name == topic_name
                )
            )
        )
        topic = result.scalar_one_or_none()

        requirement = RmtooRequirement(
            id=uuid4(),
            project_id=session.project_id,
            name=req_id,
            req_type="requirement",
            description=description,
            rationale=rationale,
            invented_on=date.today(),
            invented_by="MarQed Extraction",
            owner="development",
            status=RequirementStatus.NOT_DONE.value,
            priority=f"development:{5 - min(4, int((rule.confidence or 0.5) * 5))}",
            effort_estimation=self._estimate_effort(rule),
            topic=topic_name,
            topic_id=topic.id if topic else None,
            category=category.value,
            source_type=SourceType.EXTRACTED.value,
            source_file=rule.source_file,
            source_line=rule.source_line,
            extraction_session_id=session.id,
            confidence=rule.confidence,
            validated=False,
        )

        # Generate rmtoo content
        requirement.rmtoo_content = requirement.to_rmtoo_format()

        return requirement

    def _estimate_effort(self, rule: HybridExtractedRule) -> int:
        """Estimate effort in story points based on rule complexity."""
        base_effort = 3

        # Adjust based on rule type complexity
        complex_types = {
            RuleType.WORKFLOW.value: 2,
            RuleType.STATE_MANAGEMENT.value: 2,
            RuleType.AUTHORIZATION.value: 1,
            RuleType.CALCULATION.value: 1,
        }

        rule_type_str = rule.rule_type if isinstance(rule.rule_type, str) else (rule.rule_type.value if rule.rule_type else "")
        adjustment = complex_types.get(rule_type_str.upper(), 0)

        # Adjust based on code length
        if rule.pattern_code:
            lines = len(rule.pattern_code.split('\n'))
            if lines > 20:
                adjustment += 2
            elif lines > 10:
                adjustment += 1

        return base_effort + adjustment

    async def import_from_extraction_session(
        self,
        extraction_session_id: UUID,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """Import all rules from a hybrid extraction session as requirements."""
        # Get extraction session
        result = await self.db.execute(
            select(HybridExtractionSession).where(
                HybridExtractionSession.id == extraction_session_id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Extraction session not found: {extraction_session_id}")

        # Initialize topics if needed
        await self.initialize_topics(session.project_id)

        # Get rules
        result = await self.db.execute(
            select(HybridExtractedRule).where(
                and_(
                    HybridExtractedRule.session_id == extraction_session_id,
                    HybridExtractedRule.confidence >= min_confidence
                )
            )
        )
        rules = result.scalars().all()

        stats = {
            "total_rules": len(rules),
            "requirements_created": 0,
            "requirements_by_category": {},
            "skipped_low_confidence": 0,
        }

        for rule in rules:
            try:
                requirement = await self.convert_extracted_rule_to_requirement(rule, session)
                self.db.add(requirement)

                # Track stats
                stats["requirements_created"] += 1
                cat = requirement.category
                stats["requirements_by_category"][cat] = stats["requirements_by_category"].get(cat, 0) + 1

            except Exception as e:
                stats["skipped_low_confidence"] += 1

        await self.db.commit()
        return stats

    async def get_requirements_by_project(
        self,
        project_id: int,
        category: Optional[RequirementCategory] = None,
        status: Optional[RequirementStatus] = None,
        validated_only: bool = False,
    ) -> List[RmtooRequirement]:
        """Get requirements for a project with optional filters."""
        query = select(RmtooRequirement).where(
            RmtooRequirement.project_id == project_id
        )

        if category:
            query = query.where(RmtooRequirement.category == category.value)
        if status:
            query = query.where(RmtooRequirement.status == status.value)
        if validated_only:
            query = query.where(RmtooRequirement.validated == True)

        query = query.order_by(RmtooRequirement.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_requirement_by_name(
        self,
        project_id: int,
        name: str,
    ) -> Optional[RmtooRequirement]:
        """Get a specific requirement by name."""
        result = await self.db.execute(
            select(RmtooRequirement).where(
                and_(
                    RmtooRequirement.project_id == project_id,
                    RmtooRequirement.name == name
                )
            )
        )
        return result.scalar_one_or_none()

    async def validate_requirement(
        self,
        requirement_id: UUID,
        validated_by: str,
    ) -> RmtooRequirement:
        """Mark a requirement as validated."""
        result = await self.db.execute(
            select(RmtooRequirement).where(RmtooRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            raise ValueError(f"Requirement not found: {requirement_id}")

        requirement.validated = True
        requirement.validated_by = validated_by
        requirement.validated_at = datetime.now(timezone.utc)
        requirement.status = RequirementStatus.APPROVED.value

        # Regenerate rmtoo content
        requirement.rmtoo_content = requirement.to_rmtoo_format()

        await self.db.commit()
        return requirement

    async def add_dependency(
        self,
        requirement_id: UUID,
        solved_by_name: str,
    ) -> RmtooRequirement:
        """Add a 'Solved by' dependency to a requirement."""
        result = await self.db.execute(
            select(RmtooRequirement).where(RmtooRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            raise ValueError(f"Requirement not found: {requirement_id}")

        solved_by = requirement.solved_by or []
        if solved_by_name not in solved_by:
            solved_by.append(solved_by_name)
            requirement.solved_by = solved_by
            requirement.rmtoo_content = requirement.to_rmtoo_format()

        await self.db.commit()
        return requirement

    async def create_traceability_link(
        self,
        requirement_id: UUID,
        entity_type: str,
        entity_id: str,
        entity_name: Optional[str] = None,
        link_type: LinkType = LinkType.IMPLEMENTS,
        confidence: Optional[float] = None,
    ) -> RmtooTraceabilityLink:
        """Create a traceability link between requirement and MarQed entity."""
        result = await self.db.execute(
            select(RmtooRequirement).where(RmtooRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            raise ValueError(f"Requirement not found: {requirement_id}")

        link = RmtooTraceabilityLink(
            id=uuid4(),
            project_id=requirement.project_id,
            requirement_id=requirement_id,
            requirement_name=requirement.name,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            link_type=link_type.value,
            confidence=confidence,
        )
        self.db.add(link)
        await self.db.commit()
        return link

    async def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """Get statistics for a project's requirements."""
        # Count by category
        result = await self.db.execute(
            select(
                RmtooRequirement.category,
                func.count(RmtooRequirement.id)
            ).where(
                RmtooRequirement.project_id == project_id
            ).group_by(RmtooRequirement.category)
        )
        by_category = {row[0]: row[1] for row in result.all()}

        # Count by status
        result = await self.db.execute(
            select(
                RmtooRequirement.status,
                func.count(RmtooRequirement.id)
            ).where(
                RmtooRequirement.project_id == project_id
            ).group_by(RmtooRequirement.status)
        )
        by_status = {row[0]: row[1] for row in result.all()}

        # Count validated
        result = await self.db.execute(
            select(func.count(RmtooRequirement.id)).where(
                and_(
                    RmtooRequirement.project_id == project_id,
                    RmtooRequirement.validated == True
                )
            )
        )
        validated_count = result.scalar() or 0

        # Count total
        result = await self.db.execute(
            select(func.count(RmtooRequirement.id)).where(
                RmtooRequirement.project_id == project_id
            )
        )
        total_count = result.scalar() or 0

        # Average confidence
        result = await self.db.execute(
            select(func.avg(RmtooRequirement.confidence)).where(
                and_(
                    RmtooRequirement.project_id == project_id,
                    RmtooRequirement.confidence.isnot(None)
                )
            )
        )
        avg_confidence = result.scalar() or 0

        # Count traceability links
        result = await self.db.execute(
            select(func.count(RmtooTraceabilityLink.id)).where(
                RmtooTraceabilityLink.project_id == project_id
            )
        )
        link_count = result.scalar() or 0

        return {
            "total_requirements": total_count,
            "by_category": by_category,
            "by_status": by_status,
            "validated_count": validated_count,
            "validation_percentage": (validated_count / total_count * 100) if total_count > 0 else 0,
            "average_confidence": round(avg_confidence, 2) if avg_confidence else 0,
            "traceability_links": link_count,
        }

    def parse_rmtoo_file(self, content: str) -> Dict[str, Any]:
        """Parse rmtoo .req file content into a dictionary."""
        result = {}
        current_key = None
        current_value = []

        for line in content.split('\n'):
            # Skip comments
            if line.startswith('#'):
                continue

            # Check for new key-value pair
            if ':' in line and not line.startswith(' '):
                # Save previous key if exists
                if current_key:
                    result[current_key] = '\n'.join(current_value).strip()

                key, value = line.split(':', 1)
                current_key = key.strip()
                current_value = [value.strip()]
            elif line.startswith(' ') and current_key:
                # Continuation line
                current_value.append(line.strip())

        # Save last key
        if current_key:
            result[current_key] = '\n'.join(current_value).strip()

        return result

    async def import_from_rmtoo_file(
        self,
        project_id: int,
        file_content: str,
        source_path: Optional[str] = None,
    ) -> RmtooRequirement:
        """Import a requirement from rmtoo .req file content."""
        parsed = self.parse_rmtoo_file(file_content)

        if 'Name' not in parsed:
            raise ValueError("Missing required field: Name")
        if 'Description' not in parsed:
            raise ValueError("Missing required field: Description")

        # Determine category from name prefix
        name = parsed['Name']
        category = RequirementCategory.BR  # Default
        for cat, prefix in CATEGORY_PREFIXES.items():
            if name.startswith(prefix):
                category = cat
                break

        # Parse invented_on date
        invented_on = None
        if 'Invented on' in parsed:
            try:
                invented_on = date.fromisoformat(parsed['Invented on'])
            except ValueError:
                pass

        # Parse effort estimation
        effort = None
        if 'Effort estimation' in parsed:
            try:
                effort = int(parsed['Effort estimation'])
            except ValueError:
                pass

        # Parse solved_by
        solved_by = []
        if 'Solved by' in parsed:
            solved_by = parsed['Solved by'].split()

        # Parse depends_on
        depends_on = []
        if 'Depends on' in parsed:
            depends_on = parsed['Depends on'].split()

        # Get topic
        topic_name = parsed.get('Topic', self._get_topic_for_category(category))
        result = await self.db.execute(
            select(RmtooTopic).where(
                and_(
                    RmtooTopic.project_id == project_id,
                    RmtooTopic.name == topic_name
                )
            )
        )
        topic = result.scalar_one_or_none()

        requirement = RmtooRequirement(
            id=uuid4(),
            project_id=project_id,
            name=name,
            req_type=parsed.get('Type', 'requirement'),
            description=parsed['Description'],
            rationale=parsed.get('Rationale'),
            invented_on=invented_on,
            invented_by=parsed.get('Invented by'),
            owner=parsed.get('Owner', 'development'),
            status=parsed.get('Status', RequirementStatus.NOT_DONE.value),
            priority=parsed.get('Priority'),
            effort_estimation=effort,
            topic=topic_name,
            topic_id=topic.id if topic else None,
            solved_by=solved_by,
            depends_on=depends_on,
            category=category.value,
            source_type=SourceType.IMPORTED.value,
            source_file=source_path,
            rmtoo_content=file_content,
        )

        self.db.add(requirement)
        await self.db.commit()
        return requirement
