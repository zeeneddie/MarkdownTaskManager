# rmtoo Requirements Management - Implementation Plan

**Document**: Track 3 Implementation Plan
**Version**: 1.1
**Date**: 2025-12-27
**Status**: APPROVED FOR IMPLEMENTATION
**Weeks**: 117-118 (follows Hybrid Business Rule Extraction)
**Estimated Effort**: 40 hours (POC: 16 hours)

---

## 1. Executive Summary

Dit document beschrijft de gedetailleerde implementatie van rmtoo (Requirements Management Tool) integratie in het MarQed AI Agent Platform. De integratie maakt het mogelijk om geëxtraheerde business rules automatisch om te zetten naar formele requirements met volledige traceability.

### 1.1 Business Value

| Benefit | Description | Impact |
|---------|-------------|--------|
| **Compliance** | Audit-ready requirement documentation | HIGH |
| **Traceability** | Code → Requirement → Test mapping | HIGH |
| **Professionalism** | PDF/HTML deliverables voor klanten | MEDIUM |
| **Impact Analysis** | Dependency graphs voor change management | MEDIUM |

### 1.2 Strategic Alignment

```
Week 101-103: Business Rule Extraction (TierOrchestrator) ─────┐
Week 104-106: Rule Correlation & Validation ───────────────────┤
Week 116: Agent & Workflow Integration ────────────────────────┤
                                                               ▼
Week 117-118: rmtoo Requirements Management ◄──────────────────┘
              (THIS IMPLEMENTATION)
```

---

## 2. Technical Overview

### 2.1 What is rmtoo?

rmtoo is een open-source, text-based requirements management tool:

- **Repository**: https://github.com/florath/rmtoo
- **License**: GPL v3
- **Language**: Python
- **Format**: Plain text (.req, .topic files)
- **Outputs**: LaTeX/PDF, HTML, GraphViz, XML, CSV

### 2.2 rmtoo Requirement Format

```
# Voorbeeld .req bestand

Name: REQ-AUTH-001
Type: requirement
Description: Het systeem moet gebruikers authenticeren via OAuth2
    voordat toegang wordt verleend tot beschermde resources.
Priority: stakeholder:10
Owner: Security Team
Status: approved
Invented on: 2025-12-27
Invented by: Miguel (migration-analysis)
Rationale: Vereist voor multi-tenant security en compliance met
    SOC2 standaarden.
Depends on: REQ-SESSION-001 REQ-DATABASE-001
Solved by: src/infrastructure/auth/oauth_handler.py:45-120
Class: implementable
```

### 2.3 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RMTOO INTEGRATION ARCHITECTURE                       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        EXISTING INFRASTRUCTURE                          │ │
│  │                                                                         │ │
│  │  TierOrchestrator ──▶ RuleCorrelationService ──▶ BusinessRuleWorkflow  │ │
│  │        │                      │                         │               │ │
│  │        ▼                      ▼                         ▼               │ │
│  │  [Business Rules]     [Correlations]           [Agent Contexts]         │ │
│  └────────┬──────────────────────┬─────────────────────────┬──────────────┘ │
│           │                      │                         │                │
│           └──────────────────────┼─────────────────────────┘                │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         NEW: RMTOO LAYER                                │ │
│  │                                                                         │ │
│  │  ┌─────────────────────┐    ┌─────────────────────┐                    │ │
│  │  │ RmtooConversionSvc  │    │ RmtooGeneratorSvc   │                    │ │
│  │  │                     │    │                     │                    │ │
│  │  │ • rule_to_req()     │───▶│ • generate_pdf()    │                    │ │
│  │  │ • story_to_req()    │    │ • generate_graph()  │                    │ │
│  │  │ • epic_to_topic()   │    │ • generate_matrix() │                    │ │
│  │  │ • link_traceability │    │ • validate_reqs()   │                    │ │
│  │  └─────────────────────┘    └─────────────────────┘                    │ │
│  │           │                          │                                  │ │
│  │           ▼                          ▼                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                    /api/rmtoo/ Endpoints                         │   │ │
│  │  │  POST /convert  POST /generate/*  GET /validate  GET /export    │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         OUTPUT ARTIFACTS                                │ │
│  │                                                                         │ │
│  │  📄 requirements.pdf    📊 dependency-graph.svg    📋 traceability.xlsx │ │
│  │  📁 .req files          🔗 solved-by links         ✅ validation.json   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase 1: Research & Environment Setup (8 hours)

#### 3.1.1 Tasks

| ID | Task | Hours | Owner | Deliverable |
|----|------|-------|-------|-------------|
| P1-01 | Install rmtoo en dependencies | 2 | Dev | Working installation |
| P1-02 | Study rmtoo documentation | 2 | Dev | Knowledge doc |
| P1-03 | Create sample .req files manually | 1 | Dev | Sample files |
| P1-04 | Test rmtoo CLI outputs | 1 | Dev | Sample outputs |
| P1-05 | Define conversion mapping spec | 2 | Dev | Mapping document |

#### 3.1.2 Environment Setup Commands

```bash
# System dependencies
sudo apt-get install graphviz texlive-latex-base texlive-latex-extra

# Python dependencies
pip install rmtoo graphviz python-docx openpyxl

# Verify installation
rmtoo --version
dot -V  # GraphViz
```

#### 3.1.3 Conversion Mapping Specification

| MarQed Entity | rmtoo Entity | Mapping Rules |
|---------------|--------------|---------------|
| Epic | Topic | Name → topic name, description → content |
| User Story | Requirement | Title → Name, AC → Description |
| Business Rule | Requirement | Rule text → Description, entities → Rationale |
| Code Reference | Solved by | file:line format |
| Dependency | Depends on | Entity relationships |
| Agent Attribution | Invented by | Agent name + workflow |

#### 3.1.4 Acceptance Criteria

- [ ] rmtoo CLI generates PDF from sample .req files
- [ ] GraphViz dependency graph renders correctly
- [ ] Conversion mapping covers 90% of MarQed entities

---

### Phase 2: Conversion Service (12 hours)

#### 3.2.1 Service Structure

```
backend/app/services/rmtoo/
├── __init__.py
├── rmtoo_conversion_service.py    # Main conversion logic
├── rmtoo_generator_service.py     # Output generation
├── rmtoo_validator_service.py     # Requirement validation
├── templates/
│   ├── requirement.req.j2         # Jinja2 template for .req
│   ├── topic.topic.j2             # Jinja2 template for .topic
│   └── config.rmtoo.j2            # rmtoo configuration template
└── models/
    ├── requirement.py             # Requirement dataclass
    ├── topic.py                   # Topic dataclass
    └── traceability.py            # Traceability link model
```

#### 3.2.2 Tasks

| ID | Task | Hours | Deliverable |
|----|------|-------|-------------|
| P2-01 | Create service directory structure | 0.5 | Directory + __init__.py |
| P2-02 | Define Requirement dataclass | 1 | requirement.py |
| P2-03 | Define Topic dataclass | 0.5 | topic.py |
| P2-04 | Define Traceability model | 1 | traceability.py |
| P2-05 | Create Jinja2 templates | 1 | .j2 templates |
| P2-06 | Implement RmtooConversionService | 4 | Conversion service |
| P2-07 | Implement business_rule_to_requirement() | 2 | Tested method |
| P2-08 | Implement story_to_requirement() | 1 | Tested method |
| P2-09 | Implement create_traceability_links() | 1 | Link generator |

#### 3.2.3 RmtooConversionService Interface

```python
# backend/app/services/rmtoo/rmtoo_conversion_service.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import date

class RequirementStatus(str, Enum):
    NOT_DONE = "not done"
    APPROVED = "approved"
    FINISHED = "finished"

class RequirementClass(str, Enum):
    IMPLEMENTABLE = "implementable"
    DETAILABLE = "detailable"
    SELECTED = "selected"

@dataclass
class Requirement:
    """rmtoo Requirement representation."""
    name: str                          # REQ-XXX-NNN format
    description: str                   # Multi-line description
    req_type: str = "requirement"      # requirement, design_decision, constraint
    priority: int = 5                  # 1-10 (stakeholder priority)
    owner: Optional[str] = None        # Team or person
    status: RequirementStatus = RequirementStatus.NOT_DONE
    invented_on: date = None           # Discovery date
    invented_by: Optional[str] = None  # Agent or person
    rationale: Optional[str] = None    # Why this requirement
    depends_on: List[str] = None       # List of requirement IDs
    solved_by: List[str] = None        # Code references (file:line)
    req_class: RequirementClass = RequirementClass.DETAILABLE
    tags: List[str] = None             # Custom tags

    def to_rmtoo_format(self) -> str:
        """Generate rmtoo .req file content."""
        ...

@dataclass
class Topic:
    """rmtoo Topic (groups requirements)."""
    name: str
    title: str
    subtitle: Optional[str] = None
    requirements: List[str] = None     # Requirement IDs in this topic

    def to_rmtoo_format(self) -> str:
        """Generate rmtoo .topic file content."""
        ...

class RmtooConversionService:
    """Converts MarQed entities to rmtoo format."""

    def __init__(self, db: Session, project_id: str):
        self.db = db
        self.project_id = project_id
        self._requirement_counter: Dict[str, int] = {}

    async def business_rule_to_requirement(
        self,
        rule: Dict[str, Any],
        category: str = "BUS"
    ) -> Requirement:
        """
        Convert extracted business rule to rmtoo Requirement.

        Args:
            rule: Business rule from TierOrchestrator
            category: Requirement category prefix

        Returns:
            Requirement object ready for .req generation
        """
        ...

    async def story_to_requirement(
        self,
        story: Dict[str, Any],
        epic_id: str
    ) -> Requirement:
        """
        Convert user story to rmtoo Requirement.

        Args:
            story: User story from backlog
            epic_id: Parent epic for categorization

        Returns:
            Requirement object
        """
        ...

    async def epic_to_topic(
        self,
        epic: Dict[str, Any]
    ) -> Topic:
        """
        Convert epic to rmtoo Topic (requirement grouping).

        Args:
            epic: Epic from backlog

        Returns:
            Topic object with linked requirements
        """
        ...

    async def create_traceability_links(
        self,
        requirements: List[Requirement],
        code_refs: Dict[str, List[str]]
    ) -> List[Requirement]:
        """
        Add solved_by links from code references.

        Args:
            requirements: List of requirements
            code_refs: Mapping of requirement ID to code locations

        Returns:
            Requirements with solved_by populated
        """
        ...

    async def convert_project(
        self,
        include_stories: bool = True,
        include_rules: bool = True
    ) -> Tuple[List[Requirement], List[Topic]]:
        """
        Convert entire project to rmtoo format.

        Returns:
            Tuple of (requirements, topics)
        """
        ...

    def generate_requirement_id(self, category: str) -> str:
        """Generate unique requirement ID like REQ-AUTH-001."""
        ...
```

#### 3.2.4 Jinja2 Template: requirement.req.j2

```jinja2
{# rmtoo Requirement Template #}
Name: {{ requirement.name }}
Type: {{ requirement.req_type }}
Description: {{ requirement.description | wordwrap(70) | indent(4) }}
Priority: stakeholder:{{ requirement.priority }}
{% if requirement.owner %}
Owner: {{ requirement.owner }}
{% endif %}
Status: {{ requirement.status.value }}
{% if requirement.invented_on %}
Invented on: {{ requirement.invented_on.isoformat() }}
{% endif %}
{% if requirement.invented_by %}
Invented by: {{ requirement.invented_by }}
{% endif %}
{% if requirement.rationale %}
Rationale: {{ requirement.rationale | wordwrap(70) | indent(4) }}
{% endif %}
{% if requirement.depends_on %}
Depends on: {{ requirement.depends_on | join(' ') }}
{% endif %}
{% if requirement.solved_by %}
Solved by: {{ requirement.solved_by | join(' ') }}
{% endif %}
Class: {{ requirement.req_class.value }}
{% if requirement.tags %}
{% for tag in requirement.tags %}
Tag: {{ tag }}
{% endfor %}
{% endif %}
```

#### 3.2.5 Acceptance Criteria

- [ ] All MarQed entity types convert to valid rmtoo format
- [ ] Generated .req files pass rmtoo validation
- [ ] Requirement IDs are unique and follow naming convention
- [ ] Traceability links correctly reference source code

---

### Phase 3: Generator Service (8 hours)

#### 3.3.1 Tasks

| ID | Task | Hours | Deliverable |
|----|------|-------|-------------|
| P3-01 | Create RmtooGeneratorService skeleton | 1 | Service class |
| P3-02 | Implement generate_req_files() | 1 | File writer |
| P3-03 | Implement generate_pdf() | 2 | PDF generation |
| P3-04 | Implement generate_dependency_graph() | 2 | GraphViz SVG |
| P3-05 | Implement generate_traceability_matrix() | 2 | Excel/HTML export |

#### 3.3.2 RmtooGeneratorService Interface

```python
# backend/app/services/rmtoo/rmtoo_generator_service.py

from pathlib import Path
from typing import List, Optional, Literal
import subprocess
import tempfile

class RmtooGeneratorService:
    """Generates outputs using rmtoo CLI."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self._ensure_rmtoo_available()

    async def generate_req_files(
        self,
        requirements: List[Requirement],
        topics: List[Topic]
    ) -> Path:
        """
        Write .req and .topic files to output directory.

        Returns:
            Path to requirements directory
        """
        ...

    async def generate_pdf(
        self,
        requirements_dir: Path,
        output_name: str = "requirements-spec"
    ) -> Path:
        """
        Generate PDF specification document.

        Uses rmtoo + LaTeX pipeline.

        Returns:
            Path to generated PDF
        """
        ...

    async def generate_dependency_graph(
        self,
        requirements_dir: Path,
        format: Literal["svg", "png", "pdf"] = "svg"
    ) -> Path:
        """
        Generate requirement dependency graph using GraphViz.

        Returns:
            Path to generated graph image
        """
        ...

    async def generate_traceability_matrix(
        self,
        requirements: List[Requirement],
        format: Literal["xlsx", "html", "csv"] = "xlsx"
    ) -> Path:
        """
        Generate traceability matrix.

        Columns: Requirement | Description | Status | Code Refs | Tests

        Returns:
            Path to generated matrix file
        """
        ...

    async def generate_html_report(
        self,
        requirements_dir: Path
    ) -> Path:
        """
        Generate interactive HTML requirements report.

        Returns:
            Path to HTML directory
        """
        ...

class RmtooValidatorService:
    """Validates requirements for completeness and consistency."""

    async def validate_requirements(
        self,
        requirements: List[Requirement]
    ) -> ValidationResult:
        """
        Validate requirement set.

        Checks:
        - All dependencies exist
        - No circular dependencies
        - Required fields present
        - Naming convention followed

        Returns:
            ValidationResult with issues
        """
        ...

    async def check_coverage(
        self,
        requirements: List[Requirement],
        code_files: List[str]
    ) -> CoverageReport:
        """
        Check requirement-to-code coverage.

        Returns:
            CoverageReport with metrics
        """
        ...
```

#### 3.3.3 rmtoo Configuration Template

```yaml
# config.rmtoo.j2 - rmtoo configuration file

[rmtoo]
  input_dirs = ["requirements"]

[topic_graph]
  output_format = svg
  output_file = output/dependency-graph.svg

[latex2]
  output_file = output/requirements-spec.tex

[html]
  output_dir = output/html

[stats]
  output_file = output/statistics.csv
```

#### 3.3.4 Acceptance Criteria

- [ ] PDF generation produces readable document
- [ ] Dependency graph shows all requirement relationships
- [ ] Traceability matrix includes all columns
- [ ] HTML report is navigable and searchable

---

### Phase 4: API & Agent Integration (8 hours)

#### 3.4.1 Tasks

| ID | Task | Hours | Deliverable |
|----|------|-------|-------------|
| P4-01 | Create API router /api/rmtoo | 2 | Router + endpoints |
| P4-02 | Implement POST /convert endpoint | 1 | Conversion endpoint |
| P4-03 | Implement POST /generate/* endpoints | 2 | Generation endpoints |
| P4-04 | Implement GET /validate endpoint | 1 | Validation endpoint |
| P4-05 | Diana agent prompt integration | 2 | Updated prompts |

#### 3.4.2 API Endpoints

```python
# backend/app/api/rmtoo.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal

router = APIRouter(prefix="/api/rmtoo", tags=["rmtoo"])

class ConvertRequest(BaseModel):
    project_id: str
    include_stories: bool = True
    include_rules: bool = True
    include_code_refs: bool = True

class ConvertResponse(BaseModel):
    requirements_count: int
    topics_count: int
    output_dir: str
    conversion_time_ms: int

class GenerateRequest(BaseModel):
    project_id: str
    format: Literal["pdf", "html", "xlsx"] = "pdf"
    include_graph: bool = True

class GenerateResponse(BaseModel):
    output_files: List[str]
    generation_time_ms: int

class ValidationIssue(BaseModel):
    requirement_id: str
    issue_type: str
    message: str
    severity: Literal["error", "warning", "info"]

class ValidateResponse(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue]
    statistics: dict

# Endpoints

@router.post("/convert", response_model=ConvertResponse)
async def convert_project_to_rmtoo(request: ConvertRequest):
    """
    Convert project backlog and business rules to rmtoo format.

    Creates .req and .topic files in project output directory.
    """
    ...

@router.post("/generate/pdf")
async def generate_pdf_spec(
    project_id: str,
    background_tasks: BackgroundTasks
):
    """
    Generate PDF specification document.

    Runs asynchronously, returns job ID for polling.
    """
    ...

@router.post("/generate/graph")
async def generate_dependency_graph(
    project_id: str,
    format: Literal["svg", "png", "pdf"] = "svg"
):
    """Generate requirement dependency graph."""
    ...

@router.post("/generate/matrix")
async def generate_traceability_matrix(
    project_id: str,
    format: Literal["xlsx", "html", "csv"] = "xlsx"
):
    """Generate traceability matrix."""
    ...

@router.get("/validate/{project_id}", response_model=ValidateResponse)
async def validate_requirements(project_id: str):
    """Validate project requirements for completeness."""
    ...

@router.get("/export/{project_id}")
async def export_requirements_zip(project_id: str):
    """
    Export all requirements as ZIP archive.

    Contains: .req files, PDF, graph, matrix
    """
    ...
```

#### 3.4.3 Diana Agent Integration

Diana agent prompt update voor rmtoo-compatible output:

```python
# Addition to Diana agent prompts

DIANA_RMTOO_PROMPT = """
When generating requirements documentation, format output as rmtoo-compatible:

1. Use structured requirement format:
   - Name: REQ-{CATEGORY}-{NNN}
   - Clear Description (what, not how)
   - Priority: 1-10 scale
   - Depends on: list related requirements
   - Rationale: why this requirement exists

2. Group requirements into Topics (by epic/feature)

3. Include traceability:
   - Reference source code locations (file:line)
   - Link to test cases
   - Note original business rule source

4. Ensure SMART criteria:
   - Specific: unambiguous
   - Measurable: testable
   - Achievable: technically feasible
   - Relevant: business value
   - Time-bound: sprint/release target

Example output format:
```
Name: REQ-AUTH-001
Type: requirement
Description: The system shall authenticate users via OAuth2 before
    granting access to protected resources.
Priority: stakeholder:9
Status: approved
Invented by: Diana (documentation-workflow)
Rationale: Required for multi-tenant security compliance (SOC2).
Depends on: REQ-SESSION-001 REQ-DATABASE-001
Class: implementable
```
"""
```

#### 3.4.4 Acceptance Criteria

- [ ] All API endpoints return correct responses
- [ ] Background jobs complete and notify
- [ ] ZIP export contains all artifacts
- [ ] Diana generates valid rmtoo format

---

### Phase 5: Testing & Documentation (4 hours)

#### 3.5.1 Tasks

| ID | Task | Hours | Deliverable |
|----|------|-------|-------------|
| P5-01 | Unit tests for conversion service | 1 | Test file |
| P5-02 | Integration tests for API | 1 | Test file |
| P5-03 | End-to-end test with sample project | 1 | E2E test |
| P5-04 | User documentation | 1 | Usage guide |

#### 3.5.2 Test Structure

```
backend/tests/services/week117/
├── __init__.py
├── test_rmtoo_conversion_service.py
├── test_rmtoo_generator_service.py
├── test_rmtoo_validator_service.py
└── test_rmtoo_api.py
```

#### 3.5.3 Sample Test Cases

```python
# backend/tests/services/week117/test_rmtoo_conversion_service.py

import pytest
from app.services.rmtoo import RmtooConversionService, Requirement

class TestRmtooConversionService:

    @pytest.fixture
    def service(self, db_session):
        return RmtooConversionService(db_session, "test-project")

    async def test_business_rule_to_requirement(self, service):
        """Test business rule conversion."""
        rule = {
            "rule_text": "All orders over $100 get free shipping",
            "entities": ["Order", "Shipping"],
            "source_file": "order_service.py",
            "source_line": 45,
            "confidence": 0.95
        }

        req = await service.business_rule_to_requirement(rule, "BUS")

        assert req.name.startswith("REQ-BUS-")
        assert "free shipping" in req.description.lower()
        assert "order_service.py:45" in req.solved_by

    async def test_requirement_id_uniqueness(self, service):
        """Test that generated IDs are unique."""
        ids = set()
        for _ in range(100):
            req_id = service.generate_requirement_id("TEST")
            assert req_id not in ids
            ids.add(req_id)

    async def test_to_rmtoo_format(self, service):
        """Test .req file generation."""
        req = Requirement(
            name="REQ-TEST-001",
            description="Test requirement",
            priority=8,
            status="approved"
        )

        content = req.to_rmtoo_format()

        assert "Name: REQ-TEST-001" in content
        assert "Priority: stakeholder:8" in content
        assert "Status: approved" in content
```

#### 3.5.4 User Documentation Outline

```markdown
# rmtoo Integration - User Guide

## Quick Start
1. Configure project for rmtoo export
2. Run conversion from backlog
3. Generate outputs

## Conversion Options
- Include/exclude stories
- Include/exclude business rules
- Code traceability linking

## Output Formats
- PDF Specification
- Dependency Graph
- Traceability Matrix
- HTML Report

## Best Practices
- Requirement naming conventions
- Priority assignment
- Traceability maintenance

## Troubleshooting
- Common errors
- LaTeX issues
- GraphViz problems
```

#### 3.5.5 Acceptance Criteria

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Documentation complete
- [ ] E2E test demonstrates full workflow

---

## 4. POC Scope (16 hours)

Voor een snelle validatie, focus op minimale viable:

```
POC DELIVERABLES (16 hours)
├── P1: Environment Setup (2h)
│   ├── rmtoo installation
│   └── Basic configuration
│
├── P2: Core Conversion (6h)
│   ├── Requirement dataclass
│   ├── business_rule_to_requirement()
│   └── to_rmtoo_format()
│
├── P3: Basic Generation (4h)
│   ├── generate_req_files()
│   └── generate_pdf() - basic
│
├── P4: Single API Endpoint (2h)
│   └── POST /api/rmtoo/convert
│
└── P5: Validation (2h)
    └── Test with sample project
```

### POC Success Criteria

| Criterion | Target |
|-----------|--------|
| Business rules convert to .req | 100% |
| rmtoo validates .req files | 100% |
| PDF generates successfully | Yes |
| API endpoint works | Yes |
| End-to-end test passes | Yes |

---

## 5. Dependencies

### 5.1 System Dependencies

```bash
# Required
apt-get install graphviz         # For dependency graphs
apt-get install texlive-base     # For PDF generation
apt-get install texlive-latex-extra  # Additional LaTeX packages

# Optional (for enhanced PDF)
apt-get install texlive-fonts-recommended
```

### 5.2 Python Dependencies

```txt
# requirements-rmtoo.txt
rmtoo>=24.3.0
graphviz>=0.20
Jinja2>=3.1.0
openpyxl>=3.1.0          # Excel export
python-docx>=0.8.11      # Word export alternative
```

### 5.3 Docker Updates

```dockerfile
# Additions to Dockerfile
RUN apt-get update && apt-get install -y \
    graphviz \
    texlive-latex-base \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*
```

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| rmtoo unmaintained | Low | Medium | Fork if needed; core stable |
| LaTeX complexity | Medium | Low | Offer HTML/Word alternatives |
| Large project performance | Medium | Medium | Async processing, caching |
| Complex dependency graphs | Low | Low | Limit depth, pagination |

---

## 7. Timeline

### Full Implementation (40 hours) - Week 117-118

| Week | Day | Phase | Hours | Deliverables |
|------|-----|-------|-------|--------------|
| **117** | 1-2 | Phase 1: Setup | 8 | Environment, mapping spec |
| **117** | 3-5 | Phase 2: Conversion | 12 | Conversion service |
| **118** | 1-2 | Phase 3: Generation | 8 | Generator service |
| **118** | 3-4 | Phase 4: API | 8 | Endpoints, Diana integration |
| **118** | 5 | Phase 5: Testing | 4 | Tests, documentation |

### POC Only (16 hours) - Week 117

| Day | Phase | Hours | Deliverables |
|-----|-------|-------|--------------|
| 1 | Setup + Core | 8 | Environment, basic conversion |
| 2 | Generation + API | 8 | PDF generation, single endpoint |

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Conversion accuracy | 95% | Manual review of 50 samples |
| PDF quality | Professional | Customer feedback |
| API response time | < 5s | Conversion endpoint |
| Test coverage | > 80% | pytest-cov |
| Documentation completeness | 100% | Checklist |

---

## 9. Future Enhancements (Post-MVP)

| Enhancement | Priority | Effort |
|-------------|----------|--------|
| Bidirectional sync (rmtoo → MarQed) | P2 | 16h |
| Version control integration | P2 | 8h |
| Baseline comparison | P3 | 12h |
| Compliance templates (ISO, SOC2) | P3 | 8h |
| Interactive HTML editor | P3 | 20h |

---

## 10. Approval & Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Technical Lead | | | |
| Product Owner | | | |
| QA Lead | | | |

---

**Document Status**: Ready for Implementation
**Next Action**: Begin Phase 1 (POC) or Full Implementation based on approval
