# Design OS Integration - Design-First Workflow Enhancement

**Version**: 1.0
**Created**: 2025-12-21
**Updated**: 2025-12-21
**Status**: PLANNED (Week 96-98 - Fase 14)
**Owner**: Architecture Team
**Source**: [github.com/zeeneddie/design-os](https://github.com/zeeneddie/design-os)

---

## Executive Summary

De Design OS Integration voegt een **design-first fase** toe aan alle relevante workflows, met een nieuwe agent **Vicky (Visual Designer)**. Dit verbetert de kwaliteit van epics, features en user stories door gestructureerde design specificaties vóór implementatie.

**Key Principles**:
- **Design Before Code**: Visuele specificaties vóór architectuur beslissingen
- **Tier-Aware Design**: Design output schaalt met extraction tier (FREE → PREMIUM)
- **Sample Data Generation**: Realistische testdata voor validatie
- **Implementation Prompts**: Ready-to-use prompts voor coding agents

---

## Problem Statement

### Huidige Situatie

```
Peter (Product) → Felix (Architecture) → Diana (Docs)
       │                    │                  │
       ▼                    ▼                  ▼
   User Stories     Technical Specs     Documentation

   PROBLEEM: Geen visuele design fase → inconsistente UI output
```

### Gewenste Situatie

```
Peter (Product) → Vicky (Design) → Felix (Architecture) → Tessa (Test) → Diana (Docs)
       │               │                   │                   │              │
       ▼               ▼                   ▼                   ▼              ▼
   User Stories   Design Tokens     Technical Specs      Sample Data   Documentation
                  UI Specs          API Contracts        Test Cases    Impl Prompts
                  Wireframes
```

---

## New Agent: Vicky (Visual Designer)

### Agent Profile

| Aspect | Details |
|--------|---------|
| **Name** | Vicky |
| **Role** | Visual Designer |
| **LLM** | mistral (local via Ollama) |
| **Position in Workflow** | Between Peter (Product) and Felix (Architecture) |
| **Primary Output** | Design tokens, wireframes, UI specs, sample data structures |

### Capabilities

| Capability | Description | Output |
|------------|-------------|--------|
| **Shape Section** | Define purpose, user flows, UI requirements | `ui-spec.md` |
| **Design Tokens** | Colors, typography, spacing, application shell | `design-tokens.json` |
| **Screen Specs** | Wireframes, responsive design, dark mode | `wireframes/` folder |
| **Scope Definition** | What's IN scope, what's OUT of scope | Embedded in spec |

### Agent Configuration

```yaml
# agents/vicky.yaml
name: vicky
role: visual_designer
llm:
  provider: ollama
  model: mistral
  temperature: 0.7
capabilities:
  - shape_section
  - design_tokens
  - screen_specs
  - sample_data_structure
tools:
  - Read
  - Write
  - WebFetch
  - Bash
position:
  after: peter
  before: felix
```

---

## 4-Phase Design Process

Gebaseerd op Design OS methodologie van Brian Casel.

### Phase 1: Product Planning (Peter)

| Step | Output | Description |
|------|--------|-------------|
| **Vision** | `vision.md` | Product name, problems solved, key features |
| **Roadmap** | Epics in DB | 3-5 sections representing feature areas |
| **Data Model** | `data-model.md` | Conceptual entities and relationships |

### Phase 2: Design System (Vicky)

| Step | Output | Description |
|------|--------|-------------|
| **Design Tokens** | `design-tokens.json` | Colors (primary, secondary, neutral), typography (heading, body, mono) |
| **Application Shell** | `shell-config.json` | Navigation pattern (sidebar, top nav, minimal) |
| **Component Library** | `components.md` | Reusable UI patterns |

### Phase 3: Section Design (Vicky + Tessa)

| Step | Output | Owner | Description |
|------|--------|-------|-------------|
| **Shape Section** | `section-spec.md` | Vicky | Purpose, user flows, UI requirements, scope |
| **Sample Data** | `sample-data.ts` | Tessa | TypeScript interfaces, 5-10 realistic records |
| **Screen Specs** | `wireframes/` | Vicky | Responsive wireframes, dark mode variants |

### Phase 4: Export (Diana)

| Artifact | Format | Description |
|----------|--------|-------------|
| `design-tokens.json` | JSON | Kleuren, fonts, spacing |
| `sample-data.ts` | TypeScript | Interfaces + mock records |
| `ui-spec.md` | Markdown | User flows, scope, screen descriptions |
| `implementation-prompt.md` | Markdown | Ready-to-use prompt voor coding agents |
| `wireframes/` | SVG/PNG | Screen wireframes per section |

---

## Tier-Aware Design Output

Design output schaalt met de geselecteerde extraction tier:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIER → DESIGN OUTPUT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FREE ($0)                                                                   │
│  ├── Basic wireframes (low-fidelity sketches)                               │
│  ├── Minimal tokens (primary color only)                                    │
│  └── No sample data generation                                              │
│                                                                              │
│  BASIC ($5)                                                                  │
│  ├── + Color palette (primary, secondary)                                   │
│  ├── + Typography (heading, body)                                           │
│  └── + Basic data model                                                     │
│                                                                              │
│  STANDARD ($25) ★ RECOMMENDED                                                │
│  ├── + Full design tokens (colors, spacing, typography)                     │
│  ├── + Sample data generation (5 records)                                   │
│  ├── + TypeScript interfaces                                                │
│  └── + User flow diagrams                                                   │
│                                                                              │
│  PROFESSIONAL ($75)                                                          │
│  ├── + Application shell configuration                                      │
│  ├── + Screen specifications (all states)                                   │
│  ├── + Responsive wireframes                                                │
│  └── + Dark mode variants                                                   │
│                                                                              │
│  PREMIUM ($150)                                                              │
│  ├── + Vicky design review (quality check)                                  │
│  ├── + Implementation prompts (per section)                                 │
│  ├── + Component library suggestions                                        │
│  └── + Design handoff documentation                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Updated Workflow Sequences

### Affected Workflows (4)

| Workflow | Current Sequence | New Sequence (Week 98+) |
|----------|------------------|-------------------------|
| **GREEN_PAPER** | Peter → Felix → Diana | Peter → **Vicky** → Felix → Tessa → Diana |
| **BROWN_PAPER** | Miguel → Peter → Felix | Miguel → Peter → **Vicky** → Felix → Tessa → Diana |
| **NEW_FEATURE** | Peter → Felix → Diana | Peter → **Vicky** → Felix → Tessa → Diana |
| **ENHANCEMENT** | Felix → Tessa → Diana | Felix → **Vicky** → Tessa → Diana |

### Unaffected Workflows (7)

| Workflow | Reason |
|----------|--------|
| **BUG** | Bug fixes don't require new design |
| **MAINTENANCE** | Refactoring existing code, no new UI |
| **MIGRATION** | Technical migration, UI unchanged |
| **QUALITY_AUDIT** | Code review, no design output |
| **QUALITY_IMPROVEMENT** | Code quality, no UI changes |
| **TESTING** | Test strategy, no design needed |
| **PROJECT_DEFINITION** | High-level planning, design comes later |

---

## Services Architecture

### New Services (5)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DESIGN OS SERVICES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DesignTokenService (400 LOC)                                                │
│  ├── create_tokens(project_id, tier)                                        │
│  ├── get_tokens(project_id)                                                 │
│  ├── update_tokens(project_id, tokens)                                      │
│  └── get_preset_libraries() → ["shadcn", "tailwind", "material"]            │
│                                                                              │
│  ApplicationShellService (300 LOC)                                           │
│  ├── configure_shell(project_id, pattern) → sidebar | top_nav | minimal    │
│  ├── get_shell_config(project_id)                                           │
│  └── generate_shell_components(project_id)                                  │
│                                                                              │
│  SampleDataGenerationService (350 LOC)                                       │
│  ├── generate_sample_data(feature_id, count=10)                             │
│  ├── create_typescript_interfaces(data_model)                               │
│  └── validate_sample_data(data, interfaces)                                 │
│                                                                              │
│  UISpecificationService (500 LOC)                                            │
│  ├── shape_section(section_id) → interactive Vicky session                  │
│  ├── define_user_flows(section_id, flows)                                   │
│  ├── set_scope_boundaries(section_id, in_scope, out_scope)                  │
│  └── generate_screen_specs(section_id)                                      │
│                                                                              │
│  ImplementationPromptService (400 LOC)                                       │
│  ├── generate_prompt(epic_id | feature_id)                                  │
│  ├── export_all_prompts(project_id) → zip file                              │
│  └── get_one_shot_prompt(project_id) → full build prompt                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Integration

```python
# Example: GREEN_PAPER workflow with Vicky
class GreenPaperWorkflow:
    async def execute(self, project_id: int, tier: str):
        # Phase 1: Peter - Product Vision
        vision = await self.peter.create_vision(project_id)

        # Phase 2: Vicky - Design System (NEW)
        tokens = await self.design_token_service.create_tokens(project_id, tier)
        shell = await self.application_shell_service.configure_shell(project_id)

        # Phase 3: Felix - Architecture
        architecture = await self.felix.design_architecture(project_id, tokens)

        # Phase 4: Tessa - Sample Data (NEW)
        sample_data = await self.sample_data_service.generate(project_id)

        # Phase 5: Diana - Export
        prompts = await self.implementation_prompt_service.export_all(project_id)
        return prompts
```

---

## Database Schema

### New Tables (6)

```sql
-- Design tokens per project
CREATE TABLE design_tokens (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    tier VARCHAR(20) NOT NULL,
    colors JSONB NOT NULL,          -- {primary, secondary, neutral, accent}
    typography JSONB NOT NULL,       -- {heading, body, mono}
    spacing JSONB,                   -- {xs, sm, md, lg, xl}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Application shell configurations
CREATE TABLE application_shells (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    pattern VARCHAR(20) NOT NULL,    -- sidebar | top_nav | minimal
    config JSONB NOT NULL,           -- navigation items, layout settings
    responsive_breakpoints JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated sample data
CREATE TABLE sample_data_sets (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER REFERENCES features(id),
    typescript_interface TEXT NOT NULL,
    sample_records JSONB NOT NULL,   -- Array of 5-10 records
    validated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- UI specifications per section
CREATE TABLE ui_specifications (
    id SERIAL PRIMARY KEY,
    section_id INTEGER,              -- Feature or Epic ID
    section_type VARCHAR(20),        -- epic | feature
    purpose TEXT NOT NULL,
    user_flows JSONB NOT NULL,       -- Array of flow definitions
    in_scope JSONB NOT NULL,         -- What's included
    out_scope JSONB NOT NULL,        -- What's excluded
    screen_descriptions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Screen wireframes
CREATE TABLE screen_wireframes (
    id SERIAL PRIMARY KEY,
    spec_id INTEGER REFERENCES ui_specifications(id),
    name VARCHAR(255) NOT NULL,
    wireframe_svg TEXT,
    wireframe_png BYTEA,
    responsive_variant VARCHAR(20),  -- mobile | tablet | desktop
    dark_mode BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Implementation prompts
CREATE TABLE implementation_prompts (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    scope_type VARCHAR(20),          -- project | epic | feature
    scope_id INTEGER,
    prompt_type VARCHAR(20),         -- one_shot | section | component
    prompt_content TEXT NOT NULL,
    tokens_estimated INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Design Tokens (6 endpoints)

```
POST /api/design/projects/{id}/tokens       - Create/update design tokens
GET  /api/design/projects/{id}/tokens       - Get design tokens
GET  /api/design/tokens/presets             - List preset libraries
GET  /api/design/tokens/presets/{name}      - Get preset details
PUT  /api/design/projects/{id}/tokens       - Update tokens
DELETE /api/design/projects/{id}/tokens     - Reset to defaults
```

### Application Shell (4 endpoints)

```
POST /api/design/projects/{id}/shell        - Configure shell
GET  /api/design/projects/{id}/shell        - Get shell config
PUT  /api/design/projects/{id}/shell        - Update shell
GET  /api/design/shell/patterns             - List available patterns
```

### Sample Data (4 endpoints)

```
POST /api/design/features/{id}/sample-data  - Generate sample data
GET  /api/design/features/{id}/sample-data  - Get sample data
PUT  /api/design/features/{id}/sample-data  - Update sample data
POST /api/design/sample-data/validate       - Validate against interface
```

### UI Specifications (6 endpoints)

```
POST /api/design/sections/shape             - Start Vicky shaping session
GET  /api/design/sections/{id}/spec         - Get UI specification
PUT  /api/design/sections/{id}/spec         - Update specification
POST /api/design/sections/{id}/user-flows   - Define user flows
POST /api/design/sections/{id}/scope        - Set scope boundaries
POST /api/design/sections/{id}/wireframes   - Generate wireframes
```

### Export (4 endpoints)

```
POST /api/design/projects/{id}/export       - Full design export (zip)
GET  /api/design/projects/{id}/prompts      - List implementation prompts
GET  /api/design/prompts/{id}               - Get specific prompt
POST /api/design/projects/{id}/one-shot     - Generate one-shot prompt
```

**Total: 24 new endpoints**

---

## Week Planning

| Week | Focus | Deliverables | Estimated LOC |
|------|-------|--------------|---------------|
| **96** | Vicky Agent + Design Tokens | Agent config, DesignTokenService, ApplicationShellService, Migration, 10 endpoints | ~800 |
| **97** | Sample Data + UI Specs | SampleDataGenerationService, UISpecificationService, 10 endpoints | ~900 |
| **98** | Export + Workflow Integration | ImplementationPromptService, Workflow updates, Dashboard, 4 endpoints | ~700 |
| **Total** | | | **~2,400** |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Design Phase Adoption** | 80% of GREEN_PAPER/NEW_FEATURE workflows | Dashboard tracking |
| **UI Rework Reduction** | -30% fewer UI-related revisions | Issue tracking |
| **Sample Data Usage** | 90% of features with sample data | Database query |
| **Implementation Prompt Quality** | 4.5/5 developer satisfaction | Survey |
| **Token Usage** | 60-80% context reduction vs raw specs | Claude-Mem metrics |

---

## Migration Strategy

### Phase 1: Parallel Operation (Week 96-97)

- Vicky available but optional
- Existing workflows unchanged
- Early adopters test new design phase

### Phase 2: Default Integration (Week 98)

- Vicky inserted into 4 workflows
- Feature flag for opt-out
- Gradual rollout (10% → 50% → 100%)

### Phase 3: Full Integration (Week 99+)

- All new projects use design phase
- Legacy projects can opt-in
- Design tokens become standard

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [ROADMAP.md](../../ROADMAP.md) | Fase 14 planning |
| [AGENTS.md](../../AGENTS.md) | Vicky agent definition |
| [deep-extraction-pipeline.md](./deep-extraction-pipeline.md) | Tier system reference |
| [client-portal.md](./client-portal.md) | Customer-facing integration |

---

## Appendix: Design OS Source

This integration is based on the [Design OS](https://github.com/buildermethods/design-os) methodology by Brian Casel:

> "Design OS transforms AI coding agents from confused interns into productive developers by providing structured specifications before implementation begins."

**Key adaptations for MarQed platform**:
1. Multi-agent instead of single-agent workflow
2. Tier-aware design output (aligned with extraction tiers)
3. Integration with existing 11 agents
4. Database-backed design artifacts (not file-only)
5. LLM Council validation for design decisions (PREMIUM tier)
