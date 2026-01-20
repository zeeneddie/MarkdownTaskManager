# MarQed.ai Functionaliteit & Workflow Mapping

> Gegenereerd: 2026-01-19

## 1. BMAD Agents (Wezens) Overzicht

```mermaid
mindmap
  root((BMAD Agents))
    Core
      BMad Master
        ::icon(fa fa-magic)
        Orchestrator
        Knowledge Custodian
    BMM - Method
      Mary - Analyst
        ::icon(fa fa-chart-bar)
        Requirements
        Market Research
      John - PM
        ::icon(fa fa-tasks)
        Product Strategy
        Prioritization
      Winston - Architect
        ::icon(fa fa-building)
        System Design
        Tech Selection
      Sally - UX Designer
        ::icon(fa fa-paint-brush)
        User Experience
        Interaction Design
      Bob - Scrum Master
        ::icon(fa fa-running)
        Story Prep
        Sprint Planning
      Amelia - Developer
        ::icon(fa fa-code)
        Implementation
        Testing
      Murat - TEA
        ::icon(fa fa-flask)
        Test Architecture
        Quality Gates
      Paige - Tech Writer
        ::icon(fa fa-book)
        Documentation
      Barry - Quick Flow
        ::icon(fa fa-rocket)
        Solo Development
    CIS - Creative
      Carson - Brainstorm
        ::icon(fa fa-brain)
        Innovation
      Dr Quinn - Problem Solver
        ::icon(fa fa-puzzle-piece)
        Root Cause Analysis
      Maya - Design Thinking
        ::icon(fa fa-lightbulb)
        Empathy Mapping
      Victor - Innovation
        ::icon(fa fa-bolt)
        Disruption Strategy
      Caravaggio - Presentation
        ::icon(fa fa-tv)
        Visual Communication
      Sophia - Storyteller
        ::icon(fa fa-feather)
        Narrative Design
    BMGD - Game Dev
      Game Architect
      Game Designer
      Game Developer
      Game Scrum Master
    BMB - Builder
      BMad Builder
        ::icon(fa fa-hammer)
        Agent Creation
        Workflow Creation
```

## 2. Workflow Fases & MarQed.ai Functionaliteit Koppeling

```mermaid
flowchart TB
    subgraph Phase1["Fase 1: Analysis"]
        W1A[create-product-brief]
        W1B[research]
        W1A --> W1B
    end

    subgraph Phase2["Fase 2: Planning"]
        W2A[create-prd]
        W2B[create-ux-design]
        W2A --> W2B
    end

    subgraph Phase3["Fase 3: Solutioning"]
        W3A[create-architecture]
        W3B[create-epics-stories]
        W3C[check-implementation-readiness]
        W3A --> W3B --> W3C
    end

    subgraph Phase4["Fase 4: Implementation"]
        W4A[sprint-planning]
        W4B[create-story]
        W4C[dev-story]
        W4D[code-review]
        W4E[retrospective]
        W4A --> W4B --> W4C --> W4D --> W4E
    end

    subgraph MarQed["MarQed.ai Platform Services"]
        subgraph CodeAnalysis["Code Analysis"]
            CA1[dependency_graph_service]
            CA2[complexity_analyzer_service]
            CA3[code_analysis_aggregator]
        end

        subgraph Security["Security Scanning"]
            S1[security_scanner/]
            S2[risk_heatmap_service]
            S3[vulnerability_detector]
        end

        subgraph Migration["Legacy Migration"]
            M1[strangler_fig_service]
            M2[hci_crs_services]
            M3[migration_patterns]
        end

        subgraph Quality["Quality Management"]
            Q1[technical_debt_service]
            Q2[code_quality_service]
            Q3[health_check_suite]
        end

        subgraph LLM["LLM Integration"]
            L1[extraction_llm_adapter]
            L2[llm_resilience]
            L3[stage_review_service]
        end

        subgraph Viz["Visualization"]
            V1[codecharta_exporter]
            V2[visual_dependency_graph]
            V3[treemap_generator]
        end
    end

    Phase1 --> Phase2 --> Phase3 --> Phase4

    W1B -.->|Market Research| L1
    W3A -.->|Architecture Analysis| CA1
    W3A -.->|Security Review| S1
    W3C -.->|Quality Check| Q1
    W4C -.->|Code Analysis| CA3
    W4D -.->|Code Review AI| L3
    W4D -.->|Security Scan| S2
    W4E -.->|Metrics Dashboard| V1
```

## 3. Agent-Workflow Mapping

```mermaid
graph LR
    subgraph Agents["BMAD Agents"]
        A1[Mary - Analyst]
        A2[John - PM]
        A3[Winston - Architect]
        A4[Sally - UX]
        A5[Bob - SM]
        A6[Amelia - Dev]
        A7[Murat - TEA]
    end

    subgraph Workflows["Workflows"]
        W1[product-brief]
        W2[research]
        W3[create-prd]
        W4[create-ux-design]
        W5[create-architecture]
        W6[create-epics-stories]
        W7[sprint-planning]
        W8[create-story]
        W9[dev-story]
        W10[code-review]
        W11[testarch-*]
    end

    A1 --> W1
    A1 --> W2
    A2 --> W3
    A4 --> W4
    A3 --> W5
    A5 --> W6
    A5 --> W7
    A5 --> W8
    A6 --> W9
    A6 --> W10
    A7 --> W11
```

## 4. MarQed.ai Service-to-Workflow Integration Matrix

| Workflow | MarQed Service | Functionaliteit |
|----------|---------------|-----------------|
| **research** | `chroma_service` | Vector search voor market research |
| | `extraction_llm_adapter` | LLM-powered research synthesis |
| **create-architecture** | `dependency_graph_service` | Architectuur visualisatie |
| | `complexity_analyzer_service` | Complexity hotspot detection |
| | `visual_dependency_graph_service` | D3.js/Cytoscape graphs |
| **create-epics-stories** | `technical_debt_service` | Tech debt impact inschatting |
| | `code_analysis_aggregator` | Codebase overview |
| **sprint-planning** | `health_check_suite_service` | System health monitoring |
| | `strangler_fig_service` | Migration progress tracking |
| **dev-story** | `extraction_llm_adapter` | Code generation assistance |
| | `llm_resilience` | Retry/circuit breaker voor LLM calls |
| **code-review** | `stage_review_service` | Multi-model council review |
| | `security_scanner/` | OWASP vulnerability scan |
| | `risk_heatmap_service` | Security risk visualization |
| **testarch-*** | `test_coverage_service` | Coverage analysis |
| | `code_quality_service` | Quality metrics |
| **retrospective** | `codecharta_exporter` | 3D codebase visualization |
| | `complexity_dashboard_service` | Metrics dashboard |

## 5. Complete Agent (Wezen) Catalogus

### BMM Module (Business Method Module)

| Agent | Naam | Rol | Principes |
|-------|------|-----|-----------|
| `analyst` | Mary | Business Analyst | Evidence-based analysis, stakeholder alignment |
| `pm` | John | Product Manager | WHY-driven, data-sharp, ruthless prioritization |
| `architect` | Winston | System Architect | Boring technology, scalable patterns |
| `ux-designer` | Sally | UX Designer | User-first, empathy-driven |
| `sm` | Bob | Scrum Master | Story prep specialist, zero ambiguity |
| `dev` | Amelia | Developer | Story file = truth, red-green-refactor |
| `tea` | Murat | Test Architect | Risk-based testing, quality gates |
| `tech-writer` | Paige | Technical Writer | Clarity above all |
| `quick-flow-solo-dev` | Barry | Quick Flow Dev | Ship early, ship often |

### CIS Module (Creative Innovation Suite)

| Agent | Naam | Rol | Principes |
|-------|------|-----|-----------|
| `brainstorming-coach` | Carson | Brainstorm Facilitator | YES AND, psychological safety |
| `creative-problem-solver` | Dr. Quinn | Problem Solver | TRIZ, root cause hunting |
| `design-thinking-coach` | Maya | Design Thinking Expert | Empathy mapping, validate with users |
| `innovation-strategist` | Victor | Innovation Oracle | Blue Ocean, JTBD |
| `presentation-master` | Caravaggio | Visual Communication | 3-second rule, visual hierarchy |
| `storyteller` | Sophia | Master Storyteller | Timeless human truths |

### BMGD Module (Game Development)

| Agent | Naam | Rol | Principes |
|-------|------|-----|-----------|
| `game-architect` | Cloud Dragonborn | Game Systems Architect | Delay decisions until data |
| `game-designer` | Samus Shepard | Lead Game Designer | Design what players FEEL |
| `game-dev` | Link Freeman | Senior Game Developer | 60fps non-negotiable |
| `game-scrum-master` | Max | Game Dev Scrum Master | Every sprint = playable increment |

### Core & Builder

| Agent | Naam | Rol | Principes |
|-------|------|-----|-----------|
| `bmad-master` | BMad Master | Orchestrator | Runtime resource loading |
| `bmad-builder` | BMad Builder | System Maintainer | Practical implementation |

## 6. Workflow Lifecycle Diagram

```mermaid
stateDiagram-v2
    [*] --> Analysis

    state Analysis {
        [*] --> ProductBrief
        ProductBrief --> Research
        Research --> [*]
    }

    state Planning {
        [*] --> PRD
        PRD --> UXDesign
        UXDesign --> [*]
    }

    state Solutioning {
        [*] --> Architecture
        Architecture --> EpicsStories
        EpicsStories --> ReadinessCheck
        ReadinessCheck --> [*]
    }

    state Implementation {
        [*] --> SprintPlanning
        SprintPlanning --> CreateStory
        CreateStory --> DevStory
        DevStory --> CodeReview
        CodeReview --> TestArch
        TestArch --> Retrospective
        Retrospective --> SprintPlanning: Next Sprint
        Retrospective --> [*]: Epic Complete
    }

    Analysis --> Planning
    Planning --> Solutioning
    Solutioning --> Implementation
    Implementation --> [*]: Project Complete
```

## 7. MarQed.ai Platform Capabilities per Fase

```mermaid
pie title MarQed.ai Service Distribution per Development Phase
    "Analysis" : 15
    "Planning" : 10
    "Solutioning" : 25
    "Implementation" : 35
    "Monitoring" : 15
```

### Per Fase Breakdown

**Analysis (15%)**
- Research automation via LLM
- Market analysis tools
- Competitive intelligence

**Planning (10%)**
- PRD templates
- UX pattern library
- Wireframe generation

**Solutioning (25%)**
- Dependency graph visualization
- Architecture analysis
- Technical debt assessment
- Security pre-scan

**Implementation (35%)**
- Multi-model code review (Stage Review)
- LLM resilience (retry, circuit breaker)
- SSE streaming
- Security scanning (OWASP)
- Health check suite
- Strangler fig migration

**Monitoring (15%)**
- CodeCharta 3D visualization
- Complexity dashboard
- Risk heatmaps
- Performance tracking
