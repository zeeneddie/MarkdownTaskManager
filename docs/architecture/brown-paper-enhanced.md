# Brown Paper Enhanced - Deep Analysis Integration

**Versie:** 1.0
**Datum:** 2025-12-30
**Status:** PLANNED (Week 128-129)
**Origin:** Week 125 HCI-CRS Afspraak module analyse

---

## Executive Summary

Uitbreiding van de BROWN_PAPER workflow met integratie van alle beschikbare deep analysis services. Dit lost de huidige situatie op waarbij BrownPaperService eigen simpele regex-based analyse heeft terwijl 5 rijke analyse services parallel zijn ontwikkeld maar niet worden gebruikt.

---

## Probleem

### Huidige Situatie (Week 125)

```
BrownPaperService IMPORTS:
├── application_registry_service  ✅ (metadata)
├── brown_paper_estimation_service ✅ (FP/SP)
└── EIGEN regex analyse           ⚠️ (duplicatie)

BESCHIKBAAR MAAR NIET GEBRUIKT:
├── CodeAnalysisAggregatorService ❌ (complexity, coupling, cohesion)
├── DeepExtractionService         ❌ (multi-LLM council, INVEST)
├── HierarchicalStoryExtractionService ❌ (multi-level, CiRA)
├── LayeredAnalysisService        ❌ (VBScript, SWOT, stored procs)
└── DependencyGraphService        ❌ (graph structure, circular deps)
```

### Impact

- **Duplicatie:** BrownPaperService doet eigen code analyse terwijl betere services bestaan
- **Incomplete analyse:** Belangrijke metrics (complexity, coupling) worden niet meegenomen
- **Geen hierarchie:** Epic/Feature/Story extractie niet geïntegreerd
- **Geen validatie:** INVEST validation niet toegepast
- **Geen CiRA:** Causale relaties niet gedetecteerd

---

## Oplossing: 6-Phase Enhanced Workflow

### Workflow Diagram

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    BROWN PAPER ENHANCED WORKFLOW                                │
│                                                                                 │
│  PHASE 1: CODE UNDERSTANDING                                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┐                       │
│  │ DependencyGraph │ CodeAnalysis    │ LayeredAnalysis │                       │
│  │ Service         │ Aggregator      │ Service         │                       │
│  ├─────────────────┼─────────────────┼─────────────────┤                       │
│  │ • Graph struct  │ • Complexity    │ • VBScript      │                       │
│  │ • Circular deps │ • Coupling      │ • Stored procs  │                       │
│  │ • Fan-in/out    │ • Cohesion      │ • ASP patterns  │                       │
│  └────────┬────────┴────────┬────────┴────────┬────────┘                       │
│           │                 │                 │                                 │
│           └─────────────────┴─────────────────┘                                 │
│                             │                                                   │
│  PHASE 2: DOMAIN EXTRACTION │ Agent: Peter (Product Owner)                      │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ • Identificeer business domains uit code patterns        │                  │
│  │ • Map naar CAFCR categorieën                             │                  │
│  │ • Bepaal module boundaries                               │                  │
│  │ • Extract business rules (hybrid extractors)             │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 3: HIERARCHICAL STORY EXTRACTION │ Agent: Felix (Architect)             │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ HierarchicalStoryExtractionService:                      │                  │
│  │ • System-level → Epic                                    │                  │
│  │ • Module-level → Feature                                 │                  │
│  │ • Class-level → User Story                               │                  │
│  │ • Function-level → Task                                  │                  │
│  │ • CiRA causality relations                               │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 4: DEEP EXTRACTION   │ Agent: Quinn (Quality) + LLM Council             │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ DeepExtractionService:                                   │                  │
│  │ • Multi-tier LLM analysis (tier-aware)                   │                  │
│  │ • INVEST validation per story                            │                  │
│  │ • Conflict detection across extractors                   │                  │
│  │ • Confidence scoring                                     │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 5: ESTIMATION        │ Agent: Eliza (Estimation)                        │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ brown_paper_estimation_service (existing):               │                  │
│  │ • Function Points (IFPUG)                                │                  │
│  │ • Story Points                                           │                  │
│  │ • Effort estimation                                      │                  │
│  │ • Risk assessment (enhanced with complexity metrics)     │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 6: OUTPUT            │ Agent: Diana (Documentation)                     │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ Consolidated Output:                                     │                  │
│  │ • Dependency graph visualization data                    │                  │
│  │ • Epic/Feature/Story hierarchy                           │                  │
│  │ • Traceability matrix                                    │                  │
│  │ • Migration roadmap                                      │                  │
│  │ • Risk register                                          │                  │
│  │ • Estimation breakdown                                   │                  │
│  └──────────────────────────────────────────────────────────┘                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Assignments

| Phase | Primary Agent | Supporting Agents | Responsibilities | Output |
|-------|---------------|-------------------|------------------|--------|
| **1. Code Understanding** | Miguel | Quinn | Run DependencyGraph, CodeAnalysis, LayeredAnalysis | Metrics, graphs, patterns |
| **2. Domain Extraction** | Peter | Miguel | Identify business domains, CAFCR mapping | Domain model, boundaries |
| **3. Hierarchical Extraction** | Felix | Peter | Multi-level story extraction with CiRA | Epic/Feature/Story/Task |
| **4. Deep Extraction** | Quinn | LLM Council | INVEST validation, conflict detection | Validated, conflict-free backlog |
| **5. Estimation** | Eliza | Paul | FP/SP calculation with complexity adjustment | Estimates, risk assessment |
| **6. Output** | Diana | All | Consolidate all outputs into documentation | Migration documentation |

---

## Service Integration Details

### Phase 1: Code Understanding

#### DependencyGraphService

**Location:** `backend/app/services/dependency_graph_service.py`

**Models:**
- `ModuleNode`: Node in dependency graph
- `DependencyEdge`: Edge between modules
- `CircularDependency`: Detected circular dependencies
- `DependencyMetrics`: Aggregate metrics

**Output:**
```json
{
  "nodes": [{"id": "module_a", "type": "class", "size": 1500}],
  "edges": [{"source": "module_a", "target": "module_b", "weight": 5}],
  "circular_dependencies": [["module_a", "module_b", "module_c"]],
  "metrics": {
    "average_coupling": 3.2,
    "max_fan_in": 12,
    "max_fan_out": 8,
    "cohesion_score": 0.72
  }
}
```

#### CodeAnalysisAggregatorService

**Location:** `backend/app/services/code_analysis_aggregator_service.py`

**Metrics:**
- Cyclomatic complexity per function
- Coupling metrics (afferent, efferent)
- Cohesion metrics (LCOM)
- Documentation coverage

**Output:**
```json
{
  "complexity_profile": {
    "low": 45,
    "medium": 30,
    "high": 20,
    "very_high": 5
  },
  "coupling_analysis": {
    "average_afferent": 2.3,
    "average_efferent": 3.1,
    "instability_index": 0.57
  },
  "documentation_coverage": 0.35
}
```

#### LayeredAnalysisService

**Location:** `backend/app/services/layered_analysis_service.py`

**Capabilities:**
- VBScript analysis
- Stored procedure detection
- Classic ASP pattern recognition
- SWOT generation

**Output:**
```json
{
  "vbscript_files": 23,
  "stored_procedures": 45,
  "asp_patterns": ["include", "session_management", "database_access"],
  "swot": {
    "strengths": ["Well-structured DAL"],
    "weaknesses": ["No unit tests"],
    "opportunities": ["Migrate to .NET Core"],
    "threats": ["EOL technologies"]
  }
}
```

### Phase 2: Domain Extraction

**Agent:** Peter (Product Owner)

**Process:**
1. Analyze code patterns for business domain indicators
2. Map detected modules to CAFCR categories:
   - **C**ustomer: User-facing modules
   - **A**pplication: Business logic
   - **F**unctional: Core features
   - **C**onceptual: Domain model
   - **R**ealization: Infrastructure
3. Determine module boundaries based on coupling analysis
4. Extract business rules using hybrid extractors (12 languages)

### Phase 3: Hierarchical Story Extraction

**Service:** `HierarchicalStoryExtractionService`
**Location:** `backend/app/services/hierarchical_story_extraction_service.py`

**Extraction Levels:**
| Level | Maps To | Example |
|-------|---------|---------|
| System | Epic | "Appointment Management System" |
| Module | Feature | "Calendar View" |
| Class | User Story | "As a user, I can view my appointments" |
| Function | Task | "Implement getAppointmentsByDate()" |

**CiRA Integration:**
- Detect causal relations between requirements
- Build dependency graph of stories
- Generate test cases from causality

### Phase 4: Deep Extraction

**Service:** `DeepExtractionService`
**Location:** `backend/app/services/deep_extraction_service.py`

**Features:**
- Multi-tier LLM analysis (tier-aware)
- INVEST validation per story:
  - **I**ndependent
  - **N**egotiable
  - **V**aluable
  - **E**stimable
  - **S**mall
  - **T**estable
- Conflict detection across extractors
- Confidence scoring per extraction

### Phase 5: Estimation

**Service:** `brown_paper_estimation_service.py` (enhanced)
**Location:** `backend/app/services/brown_paper_estimation_service.py`

**Enhancements:**
- Use complexity metrics from Phase 1 as effort multiplier
- Adjust risk based on circular dependencies
- Factor in SWOT threats for timeline
- Use CiRA dependencies for sequencing

### Phase 6: Output

**Agent:** Diana (Documentation Writer)

**Consolidated Output:**
1. **Dependency Graph Visualization** - D3.js compatible JSON
2. **Epic/Feature/Story Hierarchy** - Markdown + JSON
3. **Traceability Matrix** - Story → Code → Test mapping
4. **Migration Roadmap** - Phased plan with dependencies
5. **Risk Register** - Identified risks with mitigation
6. **Estimation Breakdown** - FP, SP, hours per component

---

## Tier-Aware Analysis

| Tier | Price (50K LOC) | Services Used | Confidence Target |
|------|-----------------|---------------|-------------------|
| **FREE** | $0 | DependencyGraph + CodeAnalysis (Ollama) | 60% |
| **BASIC** | $5 | + LayeredAnalysis (Groq, Qwen) | 70% |
| **STANDARD** | $25 | + HierarchicalExtraction (Gemini) | 80% |
| **PROFESSIONAL** | $75 | + DeepExtraction (GPT-5.2) | 90% |
| **PREMIUM** | $150 | + Human Review + Opus synthesis | 95% |

---

## API Endpoints

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/brown-paper/bmad/{id}/enhanced-analyze` | POST | Start full 6-phase analysis |
| `/api/brown-paper/bmad/{id}/dependency-graph` | GET | Graph visualization data |
| `/api/brown-paper/bmad/{id}/hierarchy` | GET | Epic/Feature/Story tree |
| `/api/brown-paper/bmad/{id}/conflicts` | GET | Detected conflicts |
| `/api/brown-paper/bmad/{id}/metrics` | GET | Code quality metrics |

### Request: Enhanced Analyze

```json
POST /api/brown-paper/bmad/{session_id}/enhanced-analyze
{
  "tier": "STANDARD",
  "include_phases": [1, 2, 3, 4, 5, 6],
  "options": {
    "skip_vbscript": false,
    "include_cira": true,
    "generate_tests": true
  }
}
```

### Response: Enhanced Analyze

```json
{
  "session_id": "uuid",
  "status": "completed",
  "phases_completed": [1, 2, 3, 4, 5, 6],
  "confidence": 0.82,
  "summary": {
    "epics": 5,
    "features": 23,
    "stories": 89,
    "tasks": 234,
    "total_fp": 450,
    "total_sp": 320,
    "estimated_hours": 1200
  },
  "outputs": {
    "dependency_graph": "/api/brown-paper/bmad/{id}/dependency-graph",
    "hierarchy": "/api/brown-paper/bmad/{id}/hierarchy",
    "metrics": "/api/brown-paper/bmad/{id}/metrics"
  }
}
```

---

## Implementation Plan

### Week 128 Deliverables

| Component | Location | Description | Hours |
|-----------|----------|-------------|-------|
| **BrownPaperService refactor** | `brown_paper_service.py` | Add service imports, phase orchestration | 8 |
| **Phase 1 Integration** | `brown_paper_service.py` | DependencyGraph + CodeAnalysis + Layered calls | 8 |
| **Phase 2-3 Integration** | `brown_paper_service.py` | Domain extraction + Hierarchical calls | 8 |
| **Unit Tests** | `tests/services/week128/` | 30+ tests for phases 1-3 | 8 |

### Week 129 Deliverables

| Component | Location | Description | Hours |
|-----------|----------|-------------|-------|
| **Phase 4 Integration** | `brown_paper_service.py` | DeepExtraction + LLM Council | 8 |
| **Phase 5-6 Integration** | `brown_paper_service.py` | Estimation enhancement, output consolidation | 8 |
| **API Updates** | `brown_paper.py` | New endpoints for enhanced analysis | 4 |
| **Dashboard Updates** | `frontend/` | Visualization for enhanced output | 8 |
| **Integration Tests** | `tests/services/week129/` | E2E workflow tests | 8 |

**Total Effort:** 68 hours (~2 weeks full-time)

---

## Success Criteria

| Criterium | Target | Measurement |
|-----------|--------|-------------|
| **Service Integration** | 5 services connected | Code review |
| **Agent Coverage** | 6 agents in workflow | Workflow trace |
| **Confidence Increase** | +20% vs current | A/B test on HCI-CRS |
| **New Endpoints** | 5 new API endpoints | API documentation |
| **Tests** | 60+ unit/integration tests | pytest results |
| **HCI-CRS Validation** | Complete Afspraak analysis | Manual validation |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 18 (CiRA) | ✅ COMPLETE | CiRA relations in hierarchical extraction |
| Fase 19 (Metrics) | 📋 PLANNED | Complexity metrics enhance Phase 1 |
| DeepExtractionService | ✅ EXISTS | Ready for integration |
| HierarchicalStoryExtractionService | ✅ EXISTS | Ready for integration |
| LayeredAnalysisService | ✅ EXISTS | Ready for integration |
| DependencyGraphService | ✅ EXISTS | Ready for integration |
| CodeAnalysisAggregatorService | ✅ EXISTS | Ready for integration |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [ROADMAP.md](../../ROADMAP.md) | Fase 20 planning |
| [AGENTS.md](../../AGENTS.md) | Agent workflow assignments |
| [ARCHITECTURE.md](../../ARCHITECTURE.md) | System architecture |
| [deep-extraction-pipeline.md](./deep-extraction-pipeline.md) | Deep extraction details |
| [cira-causality-detection.md](./cira-causality-detection.md) | CiRA integration |
| [project-workflows-standard.md](./project-workflows-standard.md) | Workflow standards |

---

**Archived**: This specification created during Week 125 HCI-CRS Afspraak module analysis.
