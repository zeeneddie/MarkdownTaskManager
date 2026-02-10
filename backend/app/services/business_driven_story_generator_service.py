"""
Business Driven Story Generator Service

Week 159: Generate stories based on actual code structure.

This service creates:
- Epic per business domain
- Feature per module cluster
- Story per screen/form/API endpoint/business rule
- Enriched with source references and acceptance criteria

Key Features:
- Stories reference actual source files
- Acceptance criteria derived from code analysis
- Story points based on complexity metrics
- Traceability from story to legacy code

Used by Brown Paper workflow to generate more meaningful epics/stories.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import hashlib

from app.services.business_domain_extractor_service import (
    BusinessDomainCandidate,
    BusinessDomainExtractionResult,
    ExtractedEntity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class SourceReference:
    """Reference to source code location."""
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    element_type: str = "file"  # file, function, class, form


@dataclass
class AcceptanceCriterion:
    """An acceptance criterion for a story."""
    id: str
    description: str
    test_type: str = "functional"  # functional, validation, integration
    source_hint: Optional[str] = None  # Where in code this came from


@dataclass
class GeneratedStory:
    """A generated user story with source references."""
    id: str
    title: str
    description: str
    feature_id: str
    story_points: int
    acceptance_criteria: List[AcceptanceCriterion]
    source_references: List[SourceReference]
    complexity: str  # low, medium, high
    story_type: str  # crud, form, api, business_rule, migration
    legacy_functionality: Optional[str] = None
    target_implementation: Optional[str] = None
    priority: str = "medium"  # critical, high, medium, low
    status: str = "backlog"  # backlog, todo, in_progress, done
    business_value: Optional[str] = None
    blocked_by: List[str] = field(default_factory=list)  # story IDs
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedFeature:
    """A generated feature with stories."""
    id: str
    title: str
    description: str
    epic_id: str
    stories: List[GeneratedStory]
    source_modules: List[str]
    estimated_story_points: int
    complexity: str
    priority: str = "medium"  # critical, high, medium, low
    status: str = "backlog"  # backlog, todo, in_progress, done


@dataclass
class GeneratedEpic:
    """A generated epic with features."""
    id: str
    title: str
    description: str
    domain_name: str
    features: List[GeneratedFeature]
    source_modules: List[str]
    estimated_story_points: int
    estimated_weeks: int
    complexity: str
    priority: str = "medium"  # critical, high, medium, low
    status: str = "backlog"  # backlog, todo, in_progress, done
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StoryGenerationResult:
    """Result of story generation."""
    epics: List[GeneratedEpic]
    total_stories: int
    total_story_points: int
    total_features: int
    generation_time_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# STORY PATTERNS AND TEMPLATES
# =============================================================================


# Story templates for different types
STORY_TEMPLATES = {
    "crud_create": {
        "title": "Migreer {entity} aanmaken functionaliteit",
        "description": "Migreer de legacy functionaliteit voor het aanmaken van een nieuwe {entity} naar het moderne platform.",
        "acceptance_criteria": [
            "Alle velden uit legacy form zijn beschikbaar in nieuwe UI",
            "Validatie regels zijn behouden",
            "Data wordt correct opgeslagen in nieuwe database",
            "Foutafhandeling is gebruikersvriendelijk",
        ],
        "base_points": 5,
    },
    "crud_read": {
        "title": "Migreer {entity} ophalen/tonen",
        "description": "Migreer de legacy functionaliteit voor het ophalen en tonen van {entity} gegevens.",
        "acceptance_criteria": [
            "Alle legacy velden worden correct getoond",
            "Performance is gelijk of beter dan legacy",
            "Filtering/sortering werkt correct",
        ],
        "base_points": 3,
    },
    "crud_update": {
        "title": "Migreer {entity} wijzigen",
        "description": "Migreer de legacy functionaliteit voor het wijzigen van bestaande {entity} gegevens.",
        "acceptance_criteria": [
            "Alle wijzigbare velden zijn beschikbaar",
            "Validatie regels zijn behouden",
            "Wijzigingen worden correct opgeslagen",
            "Audit trail wordt bijgehouden indien nodig",
        ],
        "base_points": 5,
    },
    "crud_delete": {
        "title": "Migreer {entity} verwijderen",
        "description": "Migreer de legacy functionaliteit voor het verwijderen van {entity} records.",
        "acceptance_criteria": [
            "Soft delete of hard delete volgens business rules",
            "Cascade regels zijn behouden",
            "Bevestigingsdialoog aanwezig",
        ],
        "base_points": 3,
    },
    "form_migration": {
        "title": "Migreer {form_name} scherm",
        "description": "Migreer het legacy {form_name} scherm naar het moderne platform met behoud van functionaliteit.",
        "acceptance_criteria": [
            "Alle functionaliteit van legacy scherm is beschikbaar",
            "Look & feel past bij moderne applicatie",
            "Gebruikersinteractie is intuïtief",
            "Responsive design waar van toepassing",
        ],
        "base_points": 8,
    },
    "api_endpoint": {
        "title": "Implementeer {endpoint_name} API endpoint",
        "description": "Implementeer REST API endpoint voor {endpoint_name} functionaliteit ter vervanging van legacy webservice.",
        "acceptance_criteria": [
            "API endpoint is RESTful en gedocumenteerd",
            "Request/response formaat is gedefinieerd",
            "Authenticatie en autorisatie zijn geïmplementeerd",
            "Error handling is consistent",
        ],
        "base_points": 5,
    },
    "business_rule": {
        "title": "Implementeer {rule_name} business rule",
        "description": "Implementeer de {rule_name} business rule in het moderne platform.",
        "acceptance_criteria": [
            "Business rule logica is correct geïmplementeerd",
            "Alle edge cases zijn afgehandeld",
            "Unit tests dekken alle scenarios",
        ],
        "base_points": 5,
    },
    "validation": {
        "title": "Implementeer {validation_name} validatie",
        "description": "Implementeer de {validation_name} validatie met behoud van legacy regels.",
        "acceptance_criteria": [
            "Validatie regels zijn identiek aan legacy",
            "Foutmeldingen zijn gebruikersvriendelijk",
            "Validatie werkt zowel client- als server-side",
        ],
        "base_points": 3,
    },
    "integration": {
        "title": "Implementeer {integration_name} integratie",
        "description": "Implementeer de integratie met {integration_name} systeem.",
        "acceptance_criteria": [
            "Integratie werkt correct met externe systeem",
            "Error handling bij connectieproblemen",
            "Retry mechanisme waar nodig",
            "Logging van integratie activiteiten",
        ],
        "base_points": 8,
    },
    "data_migration": {
        "title": "Migreer {table_name} data",
        "description": "Migreer de data uit legacy {table_name} tabel naar nieuwe database structuur.",
        "acceptance_criteria": [
            "Alle records zijn correct gemigreerd",
            "Data integriteit is behouden",
            "Relaties zijn correct gekoppeld",
            "Rollback mogelijkheid aanwezig",
        ],
        "base_points": 5,
    },
}

# Points multipliers based on complexity
COMPLEXITY_MULTIPLIERS = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.5,
    "very_high": 2.0,
}


# =============================================================================
# BUSINESS DRIVEN STORY GENERATOR SERVICE
# =============================================================================


class BusinessDrivenStoryGeneratorService:
    """
    Generate stories based on actual code structure.

    Creates:
    - Epic per business domain
    - Feature per module cluster
    - Story per screen/form/API endpoint/business rule
    """

    def __init__(
        self,
        story_templates: Optional[Dict[str, Dict]] = None,
        default_velocity: int = 20,  # Story points per week
    ):
        """
        Initialize the generator.

        Args:
            story_templates: Custom story templates (optional)
            default_velocity: Default team velocity for estimation
        """
        self.story_templates = story_templates or STORY_TEMPLATES
        self.default_velocity = default_velocity
        self._story_counter = 0
        self._feature_counter = 0
        self._epic_counter = 0

    async def generate_stories(
        self,
        domain_result: BusinessDomainExtractionResult,
        code_analysis: Optional[Dict[str, Any]] = None,
        migration_context: Optional[Dict[str, Any]] = None,
    ) -> StoryGenerationResult:
        """
        Generate stories from domain extraction results.

        Args:
            domain_result: Result from BusinessDomainExtractorService
            code_analysis: Optional Phase 1 code analysis result
            migration_context: Optional migration analysis context

        Returns:
            StoryGenerationResult with epics, features, and stories
        """
        import time
        start_time = time.time()

        logger.info(f"Starting story generation for {len(domain_result.domains)} domains")

        # Reset counters
        self._story_counter = 0
        self._feature_counter = 0
        self._epic_counter = 0

        epics = []
        total_stories = 0
        total_points = 0

        for domain in domain_result.domains:
            epic = self._generate_epic_for_domain(
                domain,
                domain_result.module_clusters,
                code_analysis,
            )
            epics.append(epic)
            total_stories += sum(len(f.stories) for f in epic.features)
            total_points += epic.estimated_story_points

        # Post-process: set CRUD dependency chains (blocked_by)
        for epic in epics:
            for feature in epic.features:
                self._set_crud_dependencies(feature.stories)

        generation_time_ms = int((time.time() - start_time) * 1000)

        result = StoryGenerationResult(
            epics=epics,
            total_stories=total_stories,
            total_story_points=total_points,
            total_features=sum(len(e.features) for e in epics),
            generation_time_ms=generation_time_ms,
            metadata={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "domains_processed": len(domain_result.domains),
                "velocity_used": self.default_velocity,
            },
        )

        logger.info(
            f"Generated {total_stories} stories in {len(epics)} epics "
            f"({total_points} story points) in {generation_time_ms}ms"
        )

        return result

    def _generate_epic_for_domain(
        self,
        domain: BusinessDomainCandidate,
        clusters: List[Any],
        code_analysis: Optional[Dict[str, Any]],
    ) -> GeneratedEpic:
        """Generate an epic for a business domain."""
        self._epic_counter += 1
        epic_id = f"EPIC-{self._epic_counter:03d}"

        # Generate features for the domain
        features = self._generate_features_for_domain(
            domain, epic_id, code_analysis
        )

        # Calculate totals
        total_points = sum(f.estimated_story_points for f in features)
        estimated_weeks = max(1, total_points // self.default_velocity)

        epic = GeneratedEpic(
            id=epic_id,
            title=f"{domain.name} Migratie",
            description=f"Migratie van alle {domain.name.lower()} gerelateerde functionaliteit naar het moderne platform.",
            domain_name=domain.name,
            features=features,
            source_modules=domain.modules,
            estimated_story_points=total_points,
            estimated_weeks=estimated_weeks,
            complexity=domain.complexity,
            metadata={
                "domain_confidence": domain.confidence,
                "entity_count": len(domain.entities),
                "use_case_count": len(domain.use_cases),
                "source_file_count": len(domain.source_files),
            },
        )

        return epic

    def _generate_features_for_domain(
        self,
        domain: BusinessDomainCandidate,
        epic_id: str,
        code_analysis: Optional[Dict[str, Any]],
    ) -> List[GeneratedFeature]:
        """Generate features for a domain."""
        features = []

        # 1. Generate CRUD feature if entities exist
        if domain.entities:
            crud_feature = self._generate_crud_feature(
                domain.entities, epic_id, domain
            )
            if crud_feature:
                features.append(crud_feature)

        # 2. Generate form migration features
        form_entities = [e for e in domain.entities if e.entity_type == "form"]
        if form_entities:
            form_feature = self._generate_form_migration_feature(
                form_entities, epic_id, domain
            )
            if form_feature:
                features.append(form_feature)

        # 3. Generate use case features
        for use_case in domain.use_cases:
            if not self._is_crud_use_case(use_case):
                uc_feature = self._generate_use_case_feature(
                    use_case, epic_id, domain
                )
                if uc_feature:
                    features.append(uc_feature)

        # 4. Generate module-based features for remaining modules
        assigned_modules = set()
        for f in features:
            assigned_modules.update(f.source_modules)

        remaining_modules = [m for m in domain.modules if m not in assigned_modules]
        if remaining_modules:
            module_feature = self._generate_module_feature(
                remaining_modules, epic_id, domain
            )
            if module_feature:
                features.append(module_feature)

        return features

    def _generate_crud_feature(
        self,
        entities: List[ExtractedEntity],
        epic_id: str,
        domain: BusinessDomainCandidate,
    ) -> Optional[GeneratedFeature]:
        """Generate CRUD operations feature for entities."""
        self._feature_counter += 1
        feature_id = f"FEAT-{self._epic_counter:03d}-{self._feature_counter:03d}"

        stories = []

        # Filter to class/table entities only
        data_entities = [e for e in entities if e.entity_type in ("class", "table")]

        for entity in data_entities[:5]:  # Limit to 5 main entities
            # Create, Read, Update, Delete stories
            for crud_type in ["crud_create", "crud_read", "crud_update", "crud_delete"]:
                story = self._generate_story_from_template(
                    template_name=crud_type,
                    feature_id=feature_id,
                    entity=entity,
                    domain=domain,
                )
                stories.append(story)

        if not stories:
            return None

        total_points = sum(s.story_points for s in stories)

        return GeneratedFeature(
            id=feature_id,
            title=f"{domain.name} Data Beheer",
            description=f"CRUD operaties voor {domain.name.lower()} entiteiten",
            epic_id=epic_id,
            stories=stories,
            source_modules=[e.source_file for e in data_entities],
            estimated_story_points=total_points,
            complexity=self._determine_complexity(len(data_entities)),
        )

    def _generate_form_migration_feature(
        self,
        form_entities: List[ExtractedEntity],
        epic_id: str,
        domain: BusinessDomainCandidate,
    ) -> Optional[GeneratedFeature]:
        """Generate feature for form migrations."""
        self._feature_counter += 1
        feature_id = f"FEAT-{self._epic_counter:03d}-{self._feature_counter:03d}"

        stories = []

        for form_entity in form_entities:
            story = self._generate_story_from_template(
                template_name="form_migration",
                feature_id=feature_id,
                entity=form_entity,
                domain=domain,
                replacements={"form_name": form_entity.name},
            )
            stories.append(story)

        if not stories:
            return None

        total_points = sum(s.story_points for s in stories)

        return GeneratedFeature(
            id=feature_id,
            title=f"{domain.name} Schermen",
            description=f"Migratie van {domain.name.lower()} user interface schermen",
            epic_id=epic_id,
            stories=stories,
            source_modules=[e.source_file for e in form_entities],
            estimated_story_points=total_points,
            complexity=self._determine_complexity(len(form_entities)),
        )

    def _generate_use_case_feature(
        self,
        use_case: str,
        epic_id: str,
        domain: BusinessDomainCandidate,
    ) -> Optional[GeneratedFeature]:
        """Generate feature for a specific use case."""
        self._feature_counter += 1
        feature_id = f"FEAT-{self._epic_counter:03d}-{self._feature_counter:03d}"

        # Determine story type based on use case keywords
        story_type = self._determine_story_type(use_case)
        template_name = self._get_template_for_story_type(story_type)

        # Generate single story for this use case
        self._story_counter += 1
        story_id = f"STORY-{self._epic_counter:03d}-{self._feature_counter:03d}-{self._story_counter:03d}"

        template = self.story_templates.get(template_name, self.story_templates["business_rule"])

        # Calculate points with complexity modifier
        multiplier = COMPLEXITY_MULTIPLIERS.get(domain.complexity, 1.0)
        story_points = int(template["base_points"] * multiplier)

        # Generate acceptance criteria
        criteria = []
        for i, ac in enumerate(template.get("acceptance_criteria", [])):
            criteria.append(AcceptanceCriterion(
                id=f"AC-{story_id}-{i+1:02d}",
                description=ac,
                test_type="functional",
            ))

        # Add use case specific criterion
        criteria.append(AcceptanceCriterion(
            id=f"AC-{story_id}-{len(criteria)+1:02d}",
            description=f"{use_case} functionaliteit werkt correct",
            test_type="functional",
        ))

        story = GeneratedStory(
            id=story_id,
            title=f"Implementeer {use_case}",
            description=f"Implementeer de {use_case.lower()} functionaliteit in het nieuwe systeem.",
            feature_id=feature_id,
            story_points=story_points,
            acceptance_criteria=criteria,
            source_references=[
                SourceReference(file_path=f)
                for f in domain.source_files[:3]
            ],
            complexity=domain.complexity,
            story_type=story_type,
        )

        return GeneratedFeature(
            id=feature_id,
            title=use_case,
            description=f"Implementatie van {use_case.lower()} functionaliteit",
            epic_id=epic_id,
            stories=[story],
            source_modules=domain.source_files[:3],
            estimated_story_points=story_points,
            complexity=domain.complexity,
        )

    def _generate_module_feature(
        self,
        modules: List[str],
        epic_id: str,
        domain: BusinessDomainCandidate,
    ) -> Optional[GeneratedFeature]:
        """Generate feature for remaining modules."""
        self._feature_counter += 1
        feature_id = f"FEAT-{self._epic_counter:03d}-{self._feature_counter:03d}"

        stories = []

        for module_path in modules[:5]:  # Limit to 5 modules
            module_name = Path(module_path).stem

            self._story_counter += 1
            story_id = f"STORY-{self._epic_counter:03d}-{self._feature_counter:03d}-{self._story_counter:03d}"

            story = GeneratedStory(
                id=story_id,
                title=f"Migreer {module_name} module",
                description=f"Migreer de {module_name} module functionaliteit naar het moderne platform.",
                feature_id=feature_id,
                story_points=5,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id=f"AC-{story_id}-01",
                        description=f"Alle functionaliteit van {module_name} is gemigreerd",
                        test_type="functional",
                    ),
                    AcceptanceCriterion(
                        id=f"AC-{story_id}-02",
                        description="Code is voorzien van unit tests",
                        test_type="functional",
                    ),
                ],
                source_references=[
                    SourceReference(
                        file_path=module_path,
                        element_type="module",
                    )
                ],
                complexity="medium",
                story_type="migration",
            )
            stories.append(story)

        if not stories:
            return None

        total_points = sum(s.story_points for s in stories)

        return GeneratedFeature(
            id=feature_id,
            title=f"{domain.name} Overige Modules",
            description=f"Migratie van overige {domain.name.lower()} modules",
            epic_id=epic_id,
            stories=stories,
            source_modules=modules,
            estimated_story_points=total_points,
            complexity=self._determine_complexity(len(modules)),
        )

    def _generate_story_from_template(
        self,
        template_name: str,
        feature_id: str,
        entity: ExtractedEntity,
        domain: BusinessDomainCandidate,
        replacements: Optional[Dict[str, str]] = None,
    ) -> GeneratedStory:
        """Generate a story from a template."""
        self._story_counter += 1
        story_id = f"STORY-{self._epic_counter:03d}-{self._feature_counter:03d}-{self._story_counter:03d}"

        template = self.story_templates.get(template_name, self.story_templates["business_rule"])

        # Prepare replacements
        all_replacements = {
            "entity": entity.name,
            "form_name": entity.name,
            "endpoint_name": entity.name,
            "rule_name": entity.name,
            "validation_name": entity.name,
            "integration_name": entity.name,
            "table_name": entity.name,
        }
        if replacements:
            all_replacements.update(replacements)

        # Apply template
        title = template["title"].format(**all_replacements)
        description = template["description"].format(**all_replacements)

        # Calculate points
        multiplier = COMPLEXITY_MULTIPLIERS.get(domain.complexity, 1.0)
        story_points = int(template["base_points"] * multiplier)

        # Generate acceptance criteria
        criteria = []
        for i, ac in enumerate(template.get("acceptance_criteria", [])):
            criteria.append(AcceptanceCriterion(
                id=f"AC-{story_id}-{i+1:02d}",
                description=ac,
                test_type="functional",
            ))

        # Create source reference
        source_refs = [
            SourceReference(
                file_path=entity.source_file,
                line_start=entity.line_number,
                element_type=entity.entity_type,
            )
        ]

        return GeneratedStory(
            id=story_id,
            title=title,
            description=description,
            feature_id=feature_id,
            story_points=story_points,
            acceptance_criteria=criteria,
            source_references=source_refs,
            complexity=domain.complexity,
            story_type=self._template_to_story_type(template_name),
            legacy_functionality=f"Legacy: {entity.source_file}",
        )

    def _set_crud_dependencies(self, stories: List[GeneratedStory]) -> None:
        """
        Set blocked_by relations for CRUD stories within the same feature.

        Dependency rules:
        - Read depends on Create (can't read what doesn't exist)
        - Update depends on Create (can't update what doesn't exist)
        - Delete depends on Read (should verify before deleting)

        Stories are matched by entity name extracted from their title.
        """
        # Group CRUD stories by entity (extracted from title pattern)
        entity_crud_map: Dict[str, Dict[str, str]] = {}  # entity -> {crud_type: story_id}

        for story in stories:
            if story.story_type != "crud":
                continue

            title_lower = story.title.lower()
            # Detect CRUD operation from title
            crud_type = None
            if "aanmaken" in title_lower or "create" in title_lower:
                crud_type = "create"
            elif "ophalen" in title_lower or "tonen" in title_lower or "read" in title_lower:
                crud_type = "read"
            elif "wijzigen" in title_lower or "update" in title_lower:
                crud_type = "update"
            elif "verwijderen" in title_lower or "delete" in title_lower:
                crud_type = "delete"

            if crud_type:
                # Extract entity name: use metadata if set, otherwise derive from feature_id
                # (all CRUD stories for same entity share the same feature_id)
                entity_name = story.metadata.get("entity_name", story.feature_id)
                if entity_name not in entity_crud_map:
                    entity_crud_map[entity_name] = {}
                entity_crud_map[entity_name][crud_type] = story.id

        # Apply dependency rules
        for entity_name, crud_ids in entity_crud_map.items():
            create_id = crud_ids.get("create")
            read_id = crud_ids.get("read")

            if not create_id:
                continue

            # Read depends on Create
            if read_id:
                for story in stories:
                    if story.id == read_id and create_id not in story.blocked_by:
                        story.blocked_by.append(create_id)

            # Update depends on Create
            update_id = crud_ids.get("update")
            if update_id:
                for story in stories:
                    if story.id == update_id and create_id not in story.blocked_by:
                        story.blocked_by.append(create_id)

            # Delete depends on Read
            delete_id = crud_ids.get("delete")
            if delete_id and read_id:
                for story in stories:
                    if story.id == delete_id and read_id not in story.blocked_by:
                        story.blocked_by.append(read_id)

    def _is_crud_use_case(self, use_case: str) -> bool:
        """Check if use case is a CRUD operation."""
        crud_keywords = ["create", "read", "update", "delete", "aanmaken", "ophalen", "wijzigen", "verwijderen"]
        return any(kw in use_case.lower() for kw in crud_keywords)

    def _determine_story_type(self, use_case: str) -> str:
        """Determine story type from use case text."""
        use_case_lower = use_case.lower()

        if any(kw in use_case_lower for kw in ["validatie", "validate", "check"]):
            return "validation"
        elif any(kw in use_case_lower for kw in ["integratie", "koppeling", "api"]):
            return "integration"
        elif any(kw in use_case_lower for kw in ["scherm", "form", "pagina"]):
            return "form"
        elif any(kw in use_case_lower for kw in ["endpoint", "service", "rest"]):
            return "api"
        else:
            return "business_rule"

    def _get_template_for_story_type(self, story_type: str) -> str:
        """Get template name for story type."""
        type_to_template = {
            "validation": "validation",
            "integration": "integration",
            "form": "form_migration",
            "api": "api_endpoint",
            "business_rule": "business_rule",
            "migration": "data_migration",
        }
        return type_to_template.get(story_type, "business_rule")

    def _template_to_story_type(self, template_name: str) -> str:
        """Convert template name to story type."""
        if template_name.startswith("crud_"):
            return "crud"
        elif template_name == "form_migration":
            return "form"
        elif template_name == "api_endpoint":
            return "api"
        elif template_name == "data_migration":
            return "migration"
        else:
            return "business_rule"

    def _determine_complexity(self, count: int) -> str:
        """Determine complexity based on count."""
        if count > 10:
            return "very_high"
        elif count > 5:
            return "high"
        elif count > 2:
            return "medium"
        else:
            return "low"

    def to_task_hierarchy_format(
        self,
        result: StoryGenerationResult,
        specification_id: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Convert generation result to task hierarchy format.

        Compatible with existing Epic/Feature/Story database models.
        """
        output = {
            "epics": [],
            "metadata": {
                "total_epics": len(result.epics),
                "total_features": result.total_features,
                "total_stories": result.total_stories,
                "total_story_points": result.total_story_points,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generated_by": "BusinessDrivenStoryGenerator",
            },
        }

        for i, epic in enumerate(result.epics):
            epic_data = {
                "id": epic.id,
                "specification_id": specification_id,
                "project_id": project_id,
                "title": epic.title,
                "description": epic.description,
                "status": "draft",
                "priority": "medium",
                "business_value": f"Migratie van {epic.domain_name} domein",
                "estimated_story_points": epic.estimated_story_points,
                "estimated_weeks": epic.estimated_weeks,
                "sequence_number": i + 1,
                "generated_by": "BusinessDrivenStoryGenerator",
                "metadata": {
                    "domain_name": epic.domain_name,
                    "source_modules": epic.source_modules,
                    "complexity": epic.complexity,
                    **epic.metadata,
                },
                "features": [],
            }

            for j, feature in enumerate(epic.features):
                feature_data = {
                    "id": feature.id,
                    "epic_id": epic.id,
                    "project_id": project_id,
                    "title": feature.title,
                    "description": feature.description,
                    "status": "draft",
                    "priority": "medium",
                    "estimated_story_points": feature.estimated_story_points,
                    "complexity": feature.complexity,
                    "sequence_number": j + 1,
                    "generated_by": "BusinessDrivenStoryGenerator",
                    "metadata": {
                        "source_modules": feature.source_modules,
                    },
                    "stories": [],
                }

                for k, story in enumerate(feature.stories):
                    story_data = {
                        "id": story.id,
                        "feature_id": feature.id,
                        "project_id": project_id,
                        "title": story.title,
                        "description": story.description,
                        "status": "draft",
                        "priority": "medium",
                        "story_points": story.story_points,
                        "acceptance_criteria": [
                            {"id": ac.id, "description": ac.description, "test_type": ac.test_type}
                            for ac in story.acceptance_criteria
                        ],
                        "sequence_number": k + 1,
                        "generated_by": "BusinessDrivenStoryGenerator",
                        "metadata": {
                            "story_type": story.story_type,
                            "complexity": story.complexity,
                            "legacy_functionality": story.legacy_functionality,
                            "source_references": [
                                {
                                    "file_path": sr.file_path,
                                    "line_start": sr.line_start,
                                    "element_type": sr.element_type,
                                }
                                for sr in story.source_references
                            ],
                        },
                    }
                    feature_data["stories"].append(story_data)

                epic_data["features"].append(feature_data)

            output["epics"].append(epic_data)

        return output


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_business_driven_story_generator(
    custom_templates: Optional[Dict[str, Dict]] = None,
    velocity: int = 20,
) -> BusinessDrivenStoryGeneratorService:
    """
    Factory function to create BusinessDrivenStoryGeneratorService.

    Args:
        custom_templates: Additional story templates
        velocity: Team velocity in story points per week

    Returns:
        Configured BusinessDrivenStoryGeneratorService instance
    """
    templates = STORY_TEMPLATES.copy()
    if custom_templates:
        templates.update(custom_templates)

    return BusinessDrivenStoryGeneratorService(
        story_templates=templates,
        default_velocity=velocity,
    )
