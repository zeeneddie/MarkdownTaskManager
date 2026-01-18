# Fase 45: Reverse Traceability Service

**Status:** PLANNED
**Priority:** HIGH (ROI 7.5)
**Effort:** 160 uur (~5 weken)
**Timeline:** Week 193-200
**Dependencies:** Fase 44 (AI Code Complaints Strategy)

---

## Executive Summary

Implementatie van een **Reverse Traceability Service** die code automatisch koppelt aan requirements, met **persistente database opslag** en **requirements document generatie**. Dit vult een kritieke gap in het MarQed platform: hoewel er veel services bestaan voor code-analyse en requirement-extractie, ontbreekt een geunificeerde service die code → requirements traceability automatiseert.

### Toepassingsgebieden

| Modus | Beschrijving | Use Case |
|-------|--------------|----------|
| **Standalone** | Analyse van willekeurige source repo | Quick assessment, externe projecten |
| **Brown Paper** | Geïntegreerd in Brown Paper workflow | Legacy modernisatie |
| **Project** | Gekoppeld aan MarQed project | Volledige traceability |

### Probleem

```
HUIDIGE SITUATIE (Silos):

┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ TraceabilityMatrix  │   │ BusinessRuleExtract │   │ DeepExtraction      │
│ Service             │   │ or                  │   │ Service             │
├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤
│ Code→Story links    │   │ Code→Rules extract  │   │ 6-cycle hybrid      │
│ Orphan detection    │   │ IF-THEN patterns    │   │ Static+LLM analysis │
│ Impact analysis     │   │ ✗ NO linking        │   │ ✗ NO requirements   │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
         │                         │                         │
         └─────────────── GEEN ORKESTRATIE ──────────────────┘
```

### Oplossing

```
FASE 45: ReverseTraceabilityService

┌─────────────────────────────────────────────────────────────────────┐
│                   ReverseTraceabilityService                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT: Code Paths                                                   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────┐                                                │
│  │ 1. Rule         │  BusinessRuleExtractor                         │
│  │    Extraction   │  → IF-THEN rules, validation, auth             │
│  └────────┬────────┘                                                │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │ 2. Deep         │  DeepExtractionService                         │
│  │    Extraction   │  → 6-cycle hybrid analysis                     │
│  └────────┬────────┘                                                │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │ 3. Requirement  │  NEW: RequirementGenerator                     │
│  │    Generation   │  → Rules + Context → User Stories              │
│  └────────┬────────┘                                                │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │ 4. Traceability │  TraceabilityMatrixService                     │
│  │    Linking      │  → Code ↔ Story bidirectional links            │
│  └────────┬────────┘                                                │
│           ▼                                                          │
│  OUTPUT: ReverseTraceabilityResult                                   │
│          - extracted_rules: List[BusinessRule]                       │
│          - generated_requirements: List[StoryReference]              │
│          - traceability_matrix: TraceabilityMatrixResult             │
│          - coverage_metrics: CoverageMetrics                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## GAP Analysis

### Identified Gaps

| ID | Gap | Description | Impact |
|----|-----|-------------|--------|
| **G1** | Brown Paper ↔ TraceabilityMatrix | Brown Paper genereert epics maar linkt niet aan broncode | Geen traceability voor gegenereerde requirements |
| **G2** | Business Rules niet gelinkt | BusinessRuleExtractor extraheert rules maar maakt geen requirement links | Rules bestaan in isolatie |
| **G3** | Geen reverse traceability workflow | Kan niet beantwoorden: "welke requirements implementeert deze code?" | Compliance en audit gaps |
| **G4** | DeepExtraction niet verbonden | 6-cycle pipeline stopt bij extractie, geen requirement generatie | Onbenut analysepotentieel |
| **G5** | Geen unified service | Services bestaan apart, niet georkestreerd | Manuele integratie nodig |

### Existing Services to Orchestrate

| Service | Location | Capability | Gap |
|---------|----------|------------|-----|
| `TraceabilityMatrixService` | `services/traceability_matrix_service.py` | Code↔Story linking, impact analysis | Niet geintegreerd met Brown Paper |
| `TraceabilityService` | `services/traceability_service.py` | Rule↔Story/Feature/Epic links | Alleen voor pre-extracted rules |
| `BusinessRuleExtractor` | `services/static_analysis/business_rule_extractor.py` | IF-THEN rule extraction | Geen requirement generatie |
| `CodeToFunctionalityMapper` | `services/quality_impact/code_to_functionality_mapper.py` | Code→Epic/Feature/Story mapping | Geen bidirectional links |
| `DeepExtractionService` | `services/deep_extraction_service.py` | 6-cycle hybrid extraction | Stopt bij extractie |

---

## Bestaande Database Modellen (Huidige Situatie)

### Analyse van Bestaande Opslag

```
GREEN PAPER FLOW:
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ GreenPaperSession   │────►│ Constitution        │────►│ Specification       │
│ (answers)           │     │ (content_json)      │     │ (content_json)      │
└─────────────────────┘     └─────────────────────┘     └──────────┬──────────┘
                                                                   │
                                                                   ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ Task (task_tasks)   │◄────│ Story (task_stories)│◄────│ Feature             │◄──┐
│ - technical work    │     │ - user_type         │     │ (task_features)     │   │
│ - estimated_hours   │     │ - acceptance_crit   │     │ - technical_approach│   │
│ - code_files        │     │ - story_points      │     │ - api_endpoints     │   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘   │
                                                                                   │
                                                        ┌─────────────────────┐   │
                                                        │ Epic (task_epics)   │───┘
                                                        │ - business_value    │
                                                        │ - user_personas     │
                                                        └─────────────────────┘

BROWN PAPER FLOW:
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ BrownPaperSession   │────►│ BrownPaperAnalysis  │────►│ BrownPaperConst.    │
│ - application_id    │     │ - modules (JSONB)   │     │ - content_json      │
│ - patterns_detected │     │ - domains (JSONB)   │     │ - content_markdown  │
└─────────────────────┘     └─────────────────────┘     └──────────┬──────────┘
                                                                   │
                                                                   ▼
                                                        ┌─────────────────────┐
                                                        │ BrownPaperEpic      │
                                                        │ ✗ features = JSONB  │ ← GAP: Niet genormaliseerd!
                                                        │ ✗ NO stories        │ ← GAP: Geen stories!
                                                        │ ✗ NO tasks          │ ← GAP: Geen tasks!
                                                        └─────────────────────┘

TRACEABILITY (Week 113):
┌─────────────────────┐
│ StoryBusinessRule   │  Story ↔ BusinessRule (many-to-many)
│ FeatureBusinessRule │  Feature ↔ BusinessRule
│ EpicBusinessRule    │  Epic ↔ BusinessRule
│ RuleWorkflow        │  CRUD workflow grouping
└─────────────────────┘
```

### Geïdentificeerde Gaps in Database

| Gap | Beschrijving | Impact |
|-----|--------------|--------|
| **DB-G1** | BrownPaperEpic.features is JSONB, niet genormaliseerd | Geen relaties, geen queries op features |
| **DB-G2** | Geen BrownPaperFeature tabel | Features niet apart opvraagbaar |
| **DB-G3** | Geen BrownPaperStory tabel | Stories niet gegenereerd voor Brown Paper |
| **DB-G4** | Geen link tussen BrownPaper en task_* tabellen | Brown Paper output niet gelinkt aan taak hierarchie |
| **DB-G5** | Geen standalone repo sessie model | Kan niet zonder project/application werken |

---

## Nieuwe Database Modellen

### 1. Reverse Traceability Session

```python
# backend/app/models/reverse_traceability.py

class ReverseTraceabilitySession(Base):
    """
    Sessie voor reverse traceability analyse.
    Kan standalone, via Brown Paper, of project-gekoppeld werken.
    """
    __tablename__ = "reverse_traceability_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Flexibele koppeling (één van deze is gevuld)
    project_id = Column(String(50), ForeignKey("items.id"), nullable=True, index=True)
    application_id = Column(Integer, nullable=True, index=True)  # Application Registry
    brown_paper_session_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_sessions.id"), nullable=True)

    # Voor standalone analyse
    source_path = Column(String(500), nullable=True)  # /path/to/repo
    source_name = Column(String(200), nullable=True)  # "my-legacy-app"

    # Status
    status = Column(String(20), nullable=False, default="analyzing", index=True)
    # analyzing, extracting, generating, linking, completed, failed

    # Metrics
    total_files_analyzed = Column(Integer, default=0)
    total_rules_extracted = Column(Integer, default=0)
    total_requirements_generated = Column(Integer, default=0)
    traceability_coverage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, default=0)

    # Relationships
    requirements = relationship("GeneratedRequirement", back_populates="session", cascade="all, delete-orphan")
    traceability_links = relationship("CodeRequirementLink", back_populates="session", cascade="all, delete-orphan")
    documents = relationship("RequirementsDocument", back_populates="session", cascade="all, delete-orphan")


class GeneratedRequirement(Base):
    """
    Requirement gegenereerd uit code analyse.
    Kan Epic, Feature, of Story zijn.
    """
    __tablename__ = "generated_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("reverse_traceability_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Requirement type
    requirement_type = Column(String(20), nullable=False, index=True)
    # epic, feature, story, business_rule, constraint

    # Hierarchie
    parent_id = Column(UUID(as_uuid=True), ForeignKey("generated_requirements.id"), nullable=True, index=True)
    sequence_number = Column(Integer, default=1)

    # Content
    identifier = Column(String(50), nullable=False)  # REQ-001, EPIC-001, STORY-001
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    acceptance_criteria = Column(JSONB, default=[])  # ["Given..When..Then"]

    # User Story specific
    user_type = Column(String(100), nullable=True)  # "Administrator", "End User"
    user_goal = Column(Text, nullable=True)
    user_benefit = Column(Text, nullable=True)

    # Source traceability
    source_rules = Column(JSONB, default=[])  # ["RULE-001", "RULE-002"]
    source_files = Column(JSONB, default=[])  # ["auth/login.py:45-67"]
    source_functions = Column(JSONB, default=[])  # ["validate_email", "check_password"]

    # Metadata
    confidence = Column(Float, default=0.5)
    priority = Column(String(20), default="medium")
    complexity = Column(String(20), nullable=True)
    estimated_story_points = Column(Integer, nullable=True)
    tags = Column(JSONB, default=[])

    # Link naar task hierarchie (na goedkeuring)
    linked_epic_id = Column(UUID(as_uuid=True), ForeignKey("task_epics.id"), nullable=True)
    linked_feature_id = Column(UUID(as_uuid=True), ForeignKey("task_features.id"), nullable=True)
    linked_story_id = Column(UUID(as_uuid=True), ForeignKey("task_stories.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("ReverseTraceabilitySession", back_populates="requirements")
    parent = relationship("GeneratedRequirement", remote_side=[id], backref="children")
    code_links = relationship("CodeRequirementLink", back_populates="requirement", cascade="all, delete-orphan")


class CodeRequirementLink(Base):
    """
    Bidirectionele link tussen code element en requirement.
    """
    __tablename__ = "code_requirement_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("reverse_traceability_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("generated_requirements.id", ondelete="CASCADE"), nullable=False, index=True)

    # Code element
    file_path = Column(String(500), nullable=False, index=True)
    element_type = Column(String(50), nullable=False)  # file, class, function, method
    element_name = Column(String(200), nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)

    # Link metadata
    link_type = Column(String(30), nullable=False, default="implements")
    # implements, validates, triggers, references
    confidence = Column(Float, default=0.5)
    evidence = Column(JSONB, default=[])  # Why this link was created
    linked_by = Column(String(50), default="auto")  # auto, manual, llm

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String(100), nullable=True)

    # Relationships
    session = relationship("ReverseTraceabilitySession", back_populates="traceability_links")
    requirement = relationship("GeneratedRequirement", back_populates="code_links")


class RequirementsDocument(Base):
    """
    Gegenereerd requirements document.
    """
    __tablename__ = "requirements_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("reverse_traceability_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document info
    title = Column(String(300), nullable=False)
    version = Column(String(20), default="1.0")
    document_type = Column(String(50), nullable=False, default="requirements_specification")
    # requirements_specification, software_requirements_spec, user_stories_document

    # Content
    content_markdown = Column(Text, nullable=False)
    content_json = Column(JSONB, nullable=True)  # Structured version

    # Sections included
    sections = Column(JSONB, default=[])
    # ["executive_summary", "epics", "features", "stories", "traceability_matrix"]

    # Statistics
    total_epics = Column(Integer, default=0)
    total_features = Column(Integer, default=0)
    total_stories = Column(Integer, default=0)
    word_count = Column(Integer, default=0)

    # Export tracking
    exported_at = Column(DateTime, nullable=True)
    export_format = Column(String(20), nullable=True)  # pdf, docx, html

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("ReverseTraceabilitySession", back_populates="documents")
```

### 2. Requirements Document Generator

```python
# backend/app/services/reverse_traceability/requirements_document_generator.py

class RequirementsDocumentGenerator:
    """
    Genereert requirements documenten uit extracted requirements.

    Ondersteunt:
    - SRS (Software Requirements Specification)
    - User Stories Document
    - Traceability Matrix Document
    - Executive Summary
    """

    DOCUMENT_TEMPLATES = {
        "srs": {
            "title": "Software Requirements Specification",
            "sections": [
                "introduction",
                "overall_description",
                "functional_requirements",
                "non_functional_requirements",
                "traceability_matrix",
                "appendices"
            ]
        },
        "user_stories": {
            "title": "User Stories Document",
            "sections": [
                "executive_summary",
                "user_personas",
                "epics_overview",
                "feature_breakdown",
                "user_stories",
                "acceptance_criteria"
            ]
        }
    }

    async def generate_document(
        self,
        session_id: str,
        document_type: str = "srs",
        include_traceability: bool = True,
    ) -> RequirementsDocument:
        """Generate a complete requirements document."""
        pass

    def _generate_markdown(
        self,
        requirements: List[GeneratedRequirement],
        template: Dict[str, Any],
    ) -> str:
        """Generate markdown content from requirements."""
        pass

    async def export_to_format(
        self,
        document_id: str,
        format: str,  # pdf, docx, html
    ) -> bytes:
        """Export document to specified format."""
        pass
```

---

## Technical Design

### 1. Core Service

```python
# backend/app/services/reverse_traceability_service.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from app.services.static_analysis.business_rule_extractor import (
    BusinessRuleExtractor,
    BusinessRule,
    RuleExtractionResult,
)
from app.services.deep_extraction_service import (
    DeepExtractionService,
    DeepExtractionResult,
)
from app.services.traceability_matrix_service import (
    TraceabilityMatrixService,
    TraceabilityMatrixResult,
    StoryReference,
    CodeElement,
)
from app.services.traceability_service import (
    TraceabilityService,
    LinkType,
)


@dataclass
class ReverseTraceabilityResult:
    """Complete result of reverse traceability analysis."""
    session_id: str
    project_id: int
    created_at: datetime

    # Extracted data
    extracted_rules: List[BusinessRule]
    deep_extraction: Optional[DeepExtractionResult]

    # Generated outputs
    generated_requirements: List[StoryReference]
    requirement_to_rule_links: Dict[str, List[str]]  # req_id → [rule_ids]

    # Traceability
    traceability_matrix: TraceabilityMatrixResult

    # Metrics
    total_rules_extracted: int
    total_requirements_generated: int
    traceability_coverage: float  # % code linked to requirements
    rule_coverage: float  # % rules linked to requirements

    # Processing info
    processing_time_ms: int
    phases_completed: List[str]


class ReverseTraceabilityService:
    """
    Unified Code-to-Requirements reverse traceability service.

    Orchestrates:
    - BusinessRuleExtractor → rule extraction from code
    - DeepExtractionService → hybrid static+LLM analysis
    - RequirementGenerator → rules → user stories
    - TraceabilityMatrixService → bidirectional linking
    - TraceabilityService → rule-to-requirement links

    Can be used:
    1. Standalone: POST /api/reverse-traceability/analyze
    2. Integrated: Called from BrownPaperService with options.include_traceability
    """

    def __init__(
        self,
        rule_extractor: Optional[BusinessRuleExtractor] = None,
        deep_extractor: Optional[DeepExtractionService] = None,
        traceability_matrix: Optional[TraceabilityMatrixService] = None,
        traceability_service: Optional[TraceabilityService] = None,
        db=None,
    ):
        self.rule_extractor = rule_extractor or BusinessRuleExtractor()
        self.deep_extractor = deep_extractor or DeepExtractionService()
        self.traceability_matrix = traceability_matrix or TraceabilityMatrixService(db)
        self.traceability_service = traceability_service or TraceabilityService()
        self.db = db

    async def generate_requirements_from_code(
        self,
        project_id: int,
        code_paths: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> ReverseTraceabilityResult:
        """
        Complete pipeline: Code → Business Rules → Requirements → Links

        Args:
            project_id: Project ID for linking
            code_paths: List of file/directory paths to analyze
            options: Optional configuration:
                - include_deep_extraction: bool (default True)
                - semantic_threshold: float (default 0.7)
                - generate_acceptance_criteria: bool (default True)
                - link_to_existing_stories: bool (default True)

        Returns:
            ReverseTraceabilityResult with full traceability chain
        """
        # Implementation in Phase 2
        pass

    async def link_code_to_existing_requirements(
        self,
        project_id: int,
        code_elements: List[Dict[str, Any]],
        existing_stories: List[Dict[str, Any]],
    ) -> TraceabilityMatrixResult:
        """
        Link code to existing requirements without generating new ones.

        Useful for:
        - Existing projects with requirements
        - Compliance audits
        - Gap analysis
        """
        pass

    async def get_requirements_for_code(
        self,
        file_path: str,
        line_range: Optional[tuple] = None,
    ) -> List[StoryReference]:
        """
        Answer: "What requirements does this code implement?"

        The key reverse traceability query.
        """
        pass

    async def get_code_for_requirement(
        self,
        story_id: str,
    ) -> List[CodeElement]:
        """
        Answer: "What code implements this requirement?"

        Forward traceability query (already in TraceabilityMatrixService).
        """
        pass
```

### 2. Requirement Generator

```python
# backend/app/services/reverse_traceability/requirement_generator.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

from app.services.static_analysis.business_rule_extractor import BusinessRule, RuleType


class RequirementType(str, Enum):
    """Type of generated requirement."""
    USER_STORY = "user_story"
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS_RULE = "business_rule"
    CONSTRAINT = "constraint"


@dataclass
class GeneratedRequirement:
    """A requirement generated from code analysis."""
    id: str
    requirement_type: RequirementType
    title: str
    description: str
    acceptance_criteria: List[str]
    source_rules: List[str]  # BusinessRule IDs
    source_files: List[str]
    confidence: float
    priority: str  # high, medium, low
    tags: List[str]


class RequirementGenerator:
    """
    Generates user stories and requirements from extracted business rules.

    Transformation patterns:
    - VALIDATION rules → "As a user, I should see an error when..."
    - AUTHORIZATION rules → "As an admin, I can..."
    - CALCULATION rules → "The system shall calculate..."
    - WORKFLOW rules → "When X happens, Y should..."
    """

    # Templates for different rule types
    STORY_TEMPLATES = {
        RuleType.VALIDATION: "As a {actor}, I should see an error when {condition} so that {benefit}",
        RuleType.AUTHORIZATION: "As a {role}, I can {action} so that {benefit}",
        RuleType.CALCULATION: "The system shall calculate {calculation} when {trigger}",
        RuleType.WORKFLOW: "When {trigger}, the system shall {action}",
        RuleType.CONSTRAINT: "The system shall enforce that {constraint}",
        RuleType.DERIVATION: "The {derived_field} shall be derived from {source_fields}",
    }

    async def generate_from_rules(
        self,
        rules: List[BusinessRule],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GeneratedRequirement]:
        """
        Generate requirements from extracted business rules.

        Uses:
        1. Rule type → template selection
        2. Natural language from rule → description
        3. Compliance tags → priority/tags
        4. LLM enhancement for acceptance criteria
        """
        pass

    async def enhance_with_llm(
        self,
        requirement: GeneratedRequirement,
    ) -> GeneratedRequirement:
        """
        Use LLM to enhance generated requirement with:
        - Better acceptance criteria
        - Edge cases
        - Related scenarios
        """
        pass

    def _rule_to_story(self, rule: BusinessRule) -> GeneratedRequirement:
        """Convert a single business rule to a user story."""
        pass
```

### 3. Brown Paper Integration

```python
# Update to backend/app/services/brown_paper_service.py

class BrownPaperService:

    async def run_enhanced_analysis(
        self,
        project_id: int,
        options: EnhancedAnalysisOptions,
    ) -> EnhancedAnalysisResponse:
        """Enhanced analysis with optional reverse traceability."""

        # ... existing analysis code ...

        # NEW: Phase 6 - Reverse Traceability (Optional)
        if options.include_reverse_traceability:
            from app.services.reverse_traceability_service import (
                get_reverse_traceability_service,
            )

            reverse_trace_service = get_reverse_traceability_service(self.db)

            reverse_result = await reverse_trace_service.generate_requirements_from_code(
                project_id=project_id,
                code_paths=[m.path for m in analysis.modules],
                options={
                    "link_to_generated_epics": True,
                    "epic_ids": [e.id for e in result.epics],
                },
            )

            result.reverse_traceability = reverse_result
            result.traceability_matrix = reverse_result.traceability_matrix
            result.business_rules = reverse_result.extracted_rules

        return result
```

---

## API Endpoints

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reverse-traceability/analyze` | Full reverse traceability analysis |
| `POST` | `/api/reverse-traceability/link` | Link code to existing requirements |
| `GET` | `/api/reverse-traceability/code/{path}` | Get requirements for code file |
| `GET` | `/api/reverse-traceability/requirement/{id}` | Get code for requirement |
| `GET` | `/api/reverse-traceability/matrix/{project_id}` | Get full traceability matrix |
| `POST` | `/api/reverse-traceability/validate` | Validate traceability links |

### Request/Response Examples

```json
// POST /api/reverse-traceability/analyze
{
    "project_id": 123,
    "code_paths": ["backend/app/services/"],
    "options": {
        "include_deep_extraction": true,
        "semantic_threshold": 0.7,
        "generate_acceptance_criteria": true,
        "link_to_existing_stories": true
    }
}

// Response
{
    "session_id": "rt-123-456",
    "total_rules_extracted": 47,
    "total_requirements_generated": 23,
    "traceability_coverage": 78.5,
    "rule_coverage": 91.2,
    "generated_requirements": [
        {
            "id": "REQ-001",
            "type": "user_story",
            "title": "User validation on registration",
            "description": "As a user, I should see an error when email format is invalid",
            "acceptance_criteria": [
                "Given invalid email, When submit, Then show error",
                "Given valid email, When submit, Then proceed"
            ],
            "source_rules": ["RULE-VAL-001", "RULE-VAL-002"],
            "source_files": ["auth/registration.py:45-67"],
            "confidence": 0.85
        }
    ],
    "traceability_matrix": {
        "total_links": 156,
        "high_confidence": 89,
        "medium_confidence": 45,
        "low_confidence": 22,
        "orphan_code": 12,
        "unimplemented_stories": 3
    }
}
```

---

## Implementation Phases

### Phase 1: Database Models & Core Service (Week 193-194) - 40 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| Database models (4 nieuwe tabellen) | 12 | Alembic migrations, models |
| ReverseTraceabilityService skeleton | 8 | Base class with interfaces |
| Service orchestration logic | 12 | Pipeline coordination |
| Unit tests | 8 | 25+ tests |

### Phase 2: Requirement Generator (Week 195-196) - 40 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| RequirementGenerator implementation | 16 | Rule→Story transformation |
| LLM enhancement integration | 12 | Acceptance criteria generation |
| Template system | 8 | Configurable story templates |
| Unit tests | 4 | 20+ tests |

### Phase 3: Document Generator (Week 197-198) - 40 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| RequirementsDocumentGenerator | 16 | SRS & User Stories doc generation |
| Export to PDF/DOCX/HTML | 12 | Multi-format export |
| Traceability Matrix rendering | 8 | Visual matrix generation |
| Unit tests | 4 | 15+ tests |

### Phase 4: API & Integration (Week 199-200) - 40 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| API endpoints | 12 | 8 REST endpoints |
| Brown Paper integration | 8 | Optional phase 6 |
| Standalone repo support | 8 | Source path analysis |
| BMAD workflow | 4 | Standalone workflow option |
| Documentation | 4 | API docs, integration guide |
| Integration tests | 4 | E2E tests |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Traceability Coverage | >= 80% | % code elements linked to requirements |
| Rule-to-Requirement Linking | >= 90% | % extracted rules linked |
| Requirement Generation Accuracy | >= 75% | Human review acceptance rate |
| Processing Time | < 5 min | Per 10K LOC |
| False Positive Rate | < 15% | Invalid links generated |

---

## Dependencies

### Required Services (Existing)

- `BusinessRuleExtractor` - Fase 15
- `DeepExtractionService` - Fase 15
- `TraceabilityMatrixService` - Week 85
- `TraceabilityService` - Core

### Required by

- Fase 44: AI Code Complaints (context preservation)
- Brown Paper Enhanced Analysis
- Compliance Audit Reports

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Low extraction accuracy | Medium | High | Configurable thresholds, manual override |
| Performance on large codebases | Medium | Medium | Incremental processing, caching |
| Over-generation of requirements | Medium | Medium | Deduplication, confidence filtering |
| Integration complexity | Low | Medium | Adapter pattern, clear interfaces |

---

## References

- [TraceabilityMatrixService](../../backend/app/services/traceability_matrix_service.py) - Week 85
- [BusinessRuleExtractor](../../backend/app/services/static_analysis/business_rule_extractor.py) - Fase 15
- [DeepExtractionService](../../backend/app/services/deep_extraction_service.py) - Fase 15
- [Brown Paper Service](../../backend/app/services/brown_paper_service.py) - Week 57

---

*Created: Week 158 (2026-01-18)*
