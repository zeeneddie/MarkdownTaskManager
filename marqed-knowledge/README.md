# MarQed Knowledge Base

**Version:** 1.0.0 | **Week:** 104

A structured knowledge repository for AI-powered development.

---

## Directory Structure

```
marqed-knowledge/
├── README.md                    # This file
├── templates/                   # Reusable templates
│   ├── agents/                  # Agent-specific templates (6)
│   ├── ground-rules-template.md
│   ├── project-context-template.md
│   ├── code-generation-order.md
│   └── git-aliases.md
├── legacy-patterns/             # Patterns for legacy systems
│   ├── vb6/
│   ├── cobol/
│   ├── asp-classic/
│   └── delphi/
├── modern-patterns/             # Modern development patterns
│   ├── python/
│   ├── typescript/
│   ├── go/
│   └── rust/
├── domain-vocabularies/         # Domain-specific terminology
│   ├── healthcare.json
│   ├── finance.json
│   ├── ecommerce.json
│   └── generic.json
├── compliance/                  # Compliance requirements
│   ├── nen7510.md
│   ├── hipaa.md
│   ├── gdpr.md
│   └── pci-dss.md
└── projects/                    # Project-specific knowledge
    └── {project-name}/
        ├── context.md
        ├── patterns.md
        └── vocabulary.json
```

---

## Usage

### 1. Templates

Use templates as starting points for common documentation:

```python
from pathlib import Path

templates_dir = Path("marqed-knowledge/templates")
template = (templates_dir / "agents/felix-architect-template.md").read_text()
```

### 2. Domain Vocabularies

Load domain-specific terms for extraction:

```python
import json
from pathlib import Path

vocab_file = Path("marqed-knowledge/domain-vocabularies/healthcare.json")
vocabulary = json.loads(vocab_file.read_text())
```

### 3. Project Context

Each project should have its own context in `projects/{name}/`:

```python
project_name = "my-project"
context_file = Path(f"marqed-knowledge/projects/{project_name}/context.md")
```

---

## Contributing

1. Add patterns to the appropriate category
2. Use consistent naming conventions
3. Include examples with each pattern
4. Update this README when adding new categories

---

## Categories

### Templates

| Template | Purpose | Location |
|----------|---------|----------|
| Felix | Architecture & design | `templates/agents/felix-architect-template.md` |
| Quinn | Quality & security | `templates/agents/quinn-quality-template.md` |
| Eliza | Estimation | `templates/agents/eliza-estimation-template.md` |
| Betty | Bug hunting | `templates/agents/betty-bughunter-template.md` |
| Diana | Documentation | `templates/agents/diana-docs-template.md` |
| Marcus | Maintenance | `templates/agents/marcus-maintenance-template.md` |

### Domain Vocabularies

| Domain | Terms | Compliance |
|--------|-------|------------|
| Healthcare | patient, diagnosis, prescription | NEN7510, HIPAA |
| Finance | account, transaction, payment | PCI-DSS, SOX |
| E-Commerce | product, cart, checkout | GDPR, CCPA |
| Generic | user, role, authentication | GDPR |

### Patterns

| Category | Examples |
|----------|----------|
| Legacy | VB6 forms → React, COBOL CICS → REST |
| Modern | Result pattern, Guard clauses, Repository |
