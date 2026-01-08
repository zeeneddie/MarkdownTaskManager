# Standards System Architecture (Agent OS Integration)

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 59-60 COMPLETE
**Last Updated:** 2025-12-17

---

## Overview

De Standards System integreert coding standards als auto-loaded context voor agents, gebaseerd op [Agent OS](https://github.com/zeeneddie/agent-os) concepten.

---

## .standards/ Folder Structure

```
.standards/
├── global/                    # Altijd geladen voor alle workflows
│   ├── git-conventions.md     # Branch naming, commit messages
│   ├── code-review.md         # Review checklist
│   └── naming-conventions.md  # Variable/function naming
├── backend/                   # Geladen bij backend werk
│   ├── python-fastapi.md      # FastAPI patterns, Pydantic
│   ├── sqlalchemy.md          # ORM patterns, relationships
│   └── api-design.md          # REST conventions
├── frontend/                  # Geladen bij frontend werk
│   ├── html-accessibility.md  # A11y guidelines
│   └── css-conventions.md     # Styling standards
├── testing/                   # Geladen bij test-gerelateerd werk
│   ├── unit-test-patterns.md  # pytest patterns, fixtures
│   └── e2e-strategies.md      # Playwright strategies
├── security/                  # Geladen bij security-gerelateerd werk
│   └── owasp-top-10.md        # Security checklist
└── workflows/                 # Workflow-specifieke standaarden
    ├── project-analysis.md    # Workflow 1 standaard
    ├── migration-planning.md  # Workflow 2 standaard
    ├── full-assessment.md     # Workflow 3 standaard
    └── quality-criteria.md    # Kwaliteitscriteria
```

---

## Workflow → Standards Mapping

| Workflow | Standards Auto-Loaded |
|----------|----------------------|
| GREEN_PAPER | global/ |
| BROWN_PAPER | global/, backend/, frontend/, security/ |
| MAINTENANCE | global/, backend/, testing/ |
| BUG | global/, testing/ |
| NEW_FEATURE | global/, backend/, frontend/, testing/ |
| QUALITY_AUDIT | global/, security/, testing/ |
| MIGRATION | global/, backend/, security/ |
| TESTING | global/, testing/ |
| ENHANCEMENT | global/, backend/, frontend/ |
| PROJECT_DEFINITION | global/ |

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STANDARDS INTEGRATION                             │
│                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
│  │ .standards/ │ --> │ Standards   │ --> │ Agent       │            │
│  │ MD files    │     │ Loader      │     │ Context     │            │
│  └─────────────┘     └─────────────┘     └─────────────┘            │
│                              │                    │                  │
│                              ↓                    ↓                  │
│                      ┌─────────────┐     ┌─────────────┐            │
│                      │ Quality     │     │ LLM         │            │
│                      │ Gates       │     │ Prompts     │            │
│                      └─────────────┘     └─────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## StandardsLoaderService

```python
# Located in: backend/app/services/standards_loader_service.py

class StandardsLoaderService:
    """Load and inject standards into agent context."""

    def __init__(self, standards_dir: str = ".standards"):
        self.standards_dir = Path(standards_dir)

    async def load_standards_for_workflow(self, workflow_type: str) -> List[Standard]:
        """Load all applicable standards for a workflow."""
        categories = WORKFLOW_STANDARDS_MAP.get(workflow_type, ["global"])
        standards = []

        for category in categories:
            category_path = self.standards_dir / category
            if category_path.exists():
                for md_file in category_path.glob("*.md"):
                    content = await self.read_standard(md_file)
                    standards.append(Standard(
                        name=md_file.stem,
                        category=category,
                        content=content
                    ))

        return standards

    async def inject_into_prompt(self, base_prompt: str, standards: List[Standard]) -> str:
        """Inject standards into agent prompt."""
        standards_section = self._format_standards(standards)
        return f"{base_prompt}\n\n## Applicable Standards\n\n{standards_section}"

    async def validate_against_standards(self, output: str, standards: List[Standard]) -> ValidationResult:
        """Validate agent output against loaded standards."""
        violations = []
        for standard in standards:
            rules = self._extract_rules(standard)
            for rule in rules:
                if not self._check_rule(output, rule):
                    violations.append(Violation(
                        standard=standard.name,
                        rule=rule,
                        severity=rule.severity
                    ))
        return ValidationResult(passed=len(violations) == 0, violations=violations)
```

---

## Agent OS Concepten Geïntegreerd (8 total)

| # | Concept | Bron in Agent OS | MarQed Integratie |
|---|---------|------------------|-------------------|
| 1 | Standards-as-files | `.standards/` folder | StandardsLoaderService |
| 2 | Visuele asset validatie | verify-spec Check 2-3 | Quality Gates extension |
| 3 | Reusability check | verify-spec Check 7 | Spec verification |
| 4 | Verplichte visuals folder | research-spec | BMAD workflows |
| 5 | Strikte scope beperking | implement-tasks | All workflow executions |
| 6 | Skill description rewriting | improve-skills | /improve-skills command |
| 7 | Spec Shaping Loop | spec-shaper | Spec-Kit Wizard |
| 8 | Quick Spec Templates | Agent OS patterns | Spec-Kit Wizard |

---

## API Endpoints

```python
GET  /api/standards/                    # List all standards
GET  /api/standards/{category}          # Get category standards
GET  /api/standards/workflow/{type}     # Get standards for workflow
POST /api/standards/{category}/{name}   # Create/update standard
DELETE /api/standards/{category}/{name} # Delete standard
POST /api/standards/validate            # Validate output against standards
```

---

## Kwalitatieve Vergelijking met Agent OS

**Agent OS is ANDERS, niet BETER of SLECHTER dan MarQed:**

| Aspect | Agent OS | MarQed | Conclusie |
|--------|----------|--------|-----------|
| Visual-first | ✅ Sterk | ❌ Gap | TOEVOEGEN |
| Standards | ✅ Files | ✅ Files | GELIJK |
| Spec iteration | ✅ Loop | ✅ Spec-Kit | GELIJK |
| Multi-LLM | ❌ Claude only | ✅ 7 providers | MarQed beter |
| Learning | ❌ Geen | ✅ ChromaDB | MarQed beter |
| Validation | 7 checks | 42 rules | MarQed beter |

---

## Example Standard File

```markdown
# Python FastAPI Standards

## API Design

- Use plural nouns for resource endpoints (`/users`, `/projects`)
- Use kebab-case for multi-word endpoints (`/user-profiles`)
- Return 201 for POST create operations
- Return 204 for DELETE operations

## Pydantic Models

- Use `Field()` for all model fields with descriptions
- Create separate `Create`, `Update`, and `Response` schemas
- Use `Optional[]` explicitly for nullable fields

## Error Handling

- Use HTTPException with appropriate status codes
- Include detail message in all exceptions
- Log errors before raising HTTPException

## Testing

- Write unit tests for all endpoints
- Use pytest fixtures for database sessions
- Mock external services in tests
```

---

## Quality Gates Integration

Standards worden automatisch gevalideerd door Quality Gates:

```python
QUALITY_GATE_CHECKS = {
    "standards_compliance": {
        "description": "Check compliance with loaded standards",
        "severity": "medium",
        "auto_fail": False,
        "checker": "StandardsComplianceChecker"
    }
}
```

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [quality-gates.md](./quality-gates.md) - Quality Gates system
- [validation-framework.md](./validation-framework.md) - Validation framework
