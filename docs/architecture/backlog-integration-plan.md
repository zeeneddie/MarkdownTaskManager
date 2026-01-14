# Backlog Integration Plan: Brown Paper met Bestaande Backlog

**Document:** Architecture Decision Record
**Status:** DRAFT - Awaiting Validation
**Created:** Week 144 (2026-01-09)
**Author:** Claude Opus 4.5
**Related:** [workflow-separation-plan.md](./workflow-separation-plan.md)

---

## Executive Summary

Dit document beschrijft het plan van aanpak voor het integreren van een bestaande backlog in de Brown Paper workflow. Wanneer een bestaand project wordt geanalyseerd via Brown Paper, heeft dit project vaak al een bekende backlog (bugs, feature requests, tech debt). Deze items moeten worden gecombineerd met de door Brown Paper gegenereerde epics/stories.

---

## Probleemstelling

### Huidige Situatie

```
BROWN_PAPER                         BESTAANDE BACKLOG
(code analyse)                      (al bekend bij team)
      │                                   │
      ▼                                   ▼
Gegenereerde items:                 Bestaande items:
- Epics vanuit code                 - Bekende bugs
- Stories vanuit modules            - Feature requests
- Tech debt vanuit analyse          - Geplande verbeteringen
      │                                   │
      ▼                                   │
   KANBAN ◄───────────────────────────────┘
      │                              (handmatig?)
      ▼
 MAINTENANCE
```

### Probleem

1. **Geen formele intake** voor bestaande backlog in Brown Paper flow
2. **Duplicaten mogelijk** tussen gegenereerde en bestaande items
3. **Prioritering onduidelijk** - hoe wegen we bestaand vs gegenereerd?
4. **Context verlies** - backlog items missen code-analyse context
5. **Geen validatie** - bestaande items worden niet getoetst aan huidige codebase

### Gewenste Situatie

```
BROWN_PAPER Sessie
├── Input 1: project_path (code)
├── Input 2: application_id (metadata)
└── Input 3: backlog_source (NIEUW)
         │
         ▼
┌─────────────────────────────────────────┐
│     Unified Analysis & Integration       │
│                                          │
│  Code Analysis    +    Backlog Import    │
│       │                     │            │
│       └────────┬────────────┘            │
│                ▼                         │
│         Matching Engine                  │
│         - Duplicaat detectie             │
│         - Relevantie scoring             │
│         - Context enrichment             │
│                │                         │
│                ▼                         │
│         Unified Backlog                  │
│         (validated & prioritized)        │
└─────────────────────────────────────────┘
         │
         ▼
      KANBAN (single source of truth)
```

---

## Analyse van Opties

### Optie A: Backlog Import tijdens Brown Paper

**Beschrijving:** Backlog wordt geïmporteerd als onderdeel van de Brown Paper sessie.

```
Brown Paper Sessie Start
         │
         ├── Stap 1: Session aanmaken
         ├── Stap 2: Code analyse (Phase 1-6)
         ├── Stap 3: Backlog import (NIEUW)
         ├── Stap 4: Matching & deduplicatie
         └── Stap 5: Unified output
```

| Voordeel | Nadeel |
|----------|--------|
| Code-context beschikbaar voor validatie | Complexere Brown Paper flow |
| Duplicaten direct detecteerbaar | Tight coupling met backlog formaat |
| Single workflow voor alles | Brown Paper wordt "zwaarder" |
| Prioritering geïnformeerd door analyse | Kan bestaande flow verstoren |

**Geschatte impact:** Medium-High

---

### Optie B: Backlog als Parallelle Intake

**Beschrijving:** Backlog import is een aparte workflow die samenkomt bij KANBAN.

```
    BROWN_PAPER              BACKLOG_IMPORT
    (analyse)                (aparte flow)
         │                        │
         ▼                        ▼
    Gegenereerde             Geïmporteerde
    Items                    Items
         │                        │
         └────────┬───────────────┘
                  ▼
              KANBAN
         (merge point)
                  │
                  ▼
           MAINTENANCE
```

| Voordeel | Nadeel |
|----------|--------|
| Loose coupling | Geen code-context bij import |
| Brown Paper blijft focused | Duplicaat detectie achteraf |
| Flexibel timing | Twee intake flows te beheren |
| Incrementeel implementeerbaar | Merge logic nodig in KANBAN |

**Geschatte impact:** Medium

---

### Optie C: Backlog via MAINTENANCE Context

**Beschrijving:** Backlog wordt geladen als context wanneer project MAINTENANCE fase bereikt.

```
BROWN_PAPER → KANBAN → MAINTENANCE
                            │
                            ├── Pre-load bestaande backlog
                            ├── Combineer met uitgevoerde items
                            └── Unified view
```

| Voordeel | Nadeel |
|----------|--------|
| Past in bestaande hiërarchie | Laat in de flow |
| MAINTENANCE is logische plek | Mist Brown Paper context |
| Minimale wijzigingen | Items komen pas laat beschikbaar |
| Backward compatible | Geen validatie tegen code |

**Geschatte impact:** Low

---

### Aanbevolen Optie: A (Backlog Import tijdens Brown Paper)

**Rationale:**
1. Brown Paper heeft de code-context om backlog items te valideren
2. Duplicaat detectie is het meest effectief met volledige analyse
3. Prioritering kan worden geïnformeerd door complexity/risk scoring
4. Single point of entry voorkomt merge problemen downstream
5. Past bij het "analyse eerst" principe van Brown Paper

---

## Gedetailleerde Uitwerking (Optie A)

### Nieuwe Brown Paper Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BROWN PAPER SESSIE (Enhanced)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 0: Session Start (bestaand)                                       │
│  ├── Input: project_path, application_id                                │
│  └── Output: session_id                                                  │
│                                                                          │
│  PHASE 1-6: Code Analysis (bestaand)                                     │
│  ├── Dependency analysis                                                 │
│  ├── Domain extraction                                                   │
│  ├── Hierarchical extraction                                             │
│  ├── Deep extraction (LLM Council)                                       │
│  ├── Estimation (Eliza)                                                  │
│  └── Output consolidation                                                │
│                                                                          │
│  PHASE 7: Backlog Integration (NIEUW)                                    │
│  ├── Step 7.1: Backlog Source Configuration                              │
│  ├── Step 7.2: Backlog Import                                            │
│  ├── Step 7.3: Item Normalization                                        │
│  ├── Step 7.4: Matching & Deduplication                                  │
│  ├── Step 7.5: Context Enrichment                                        │
│  ├── Step 7.6: Priority Calculation                                      │
│  └── Step 7.7: Unified Backlog Output                                    │
│                                                                          │
│  OUTPUT: AnalysisContract + UnifiedBacklog                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Step 7.1: Backlog Source Configuration

**Doel:** Definieer waar de bestaande backlog vandaan komt.

**Ondersteunde bronnen:**

| Bron Type | Formaat | Beschrijving |
|-----------|---------|--------------|
| `json_file` | JSON | Lokaal JSON bestand met items |
| `csv_file` | CSV | Spreadsheet export |
| `markdown` | MD | Markdown bestand (bijv. BACKLOG.md) |
| `jira_api` | API | Jira project import |
| `github_issues` | API | GitHub Issues import |
| `azure_devops` | API | Azure DevOps work items |
| `internal_db` | DB | Bestaande items in MarQed database |

**API Request:**

```json
POST /api/brown-paper/sessions/{session_id}/backlog-source
{
    "source_type": "json_file",
    "source_config": {
        "file_path": "/path/to/backlog.json"
    },
    "mapping": {
        "id_field": "ticket_id",
        "title_field": "summary",
        "description_field": "description",
        "type_field": "issue_type",
        "priority_field": "priority",
        "status_field": "status"
    },
    "filters": {
        "statuses": ["open", "in_progress", "backlog"],
        "types": ["bug", "feature", "tech_debt"]
    }
}
```

**Database:**

```sql
CREATE TABLE backlog_sources (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    source_type VARCHAR(50) NOT NULL,
    source_config JSONB NOT NULL,
    field_mapping JSONB NOT NULL,
    filters JSONB,
    status VARCHAR(20) DEFAULT 'configured',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Step 7.2: Backlog Import

**Doel:** Haal items op uit de geconfigureerde bron.

**Service:**

```python
class BacklogImportService:
    async def import_backlog(
        self,
        session_id: str,
        source_config: BacklogSourceConfig
    ) -> List[RawBacklogItem]:
        """
        Import backlog items from configured source.

        Supported adapters:
        - JsonFileAdapter
        - CsvFileAdapter
        - MarkdownAdapter
        - JiraAdapter
        - GitHubAdapter
        - AzureDevOpsAdapter
        - InternalDbAdapter
        """
        adapter = self._get_adapter(source_config.source_type)
        raw_items = await adapter.fetch(source_config)

        return raw_items
```

**Output Model:**

```python
@dataclass
class RawBacklogItem:
    external_id: str          # ID in source system
    title: str
    description: Optional[str]
    item_type: str            # bug, feature, tech_debt, enhancement
    priority: Optional[str]   # high, medium, low
    status: Optional[str]
    labels: List[str]
    created_at: Optional[datetime]
    source_metadata: Dict     # Original data for reference
```

**Database:**

```sql
CREATE TABLE imported_backlog_items (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    source_id UUID REFERENCES backlog_sources(id),
    external_id VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT,
    item_type VARCHAR(50),
    priority VARCHAR(20),
    status VARCHAR(50),
    labels JSONB DEFAULT '[]',
    source_metadata JSONB,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(session_id, external_id)
);
```

---

### Step 7.3: Item Normalization

**Doel:** Converteer raw items naar gestandaardiseerd formaat.

**Normalisatie regels:**

| Veld | Normalisatie |
|------|--------------|
| `item_type` | Map naar: `bug`, `feature`, `tech_debt`, `enhancement`, `epic`, `story` |
| `priority` | Map naar: `critical`, `high`, `medium`, `low` |
| `status` | Map naar: `backlog`, `ready`, `in_progress`, `done`, `archived` |
| `description` | Clean HTML, normalize whitespace, extract key phrases |

**Service:**

```python
class BacklogNormalizationService:
    def normalize(
        self,
        raw_items: List[RawBacklogItem],
        mapping_config: FieldMapping
    ) -> List[NormalizedBacklogItem]:
        """
        Normalize raw backlog items to standard format.

        - Type normalization (bug → bug, defect → bug, etc.)
        - Priority normalization (P1 → critical, etc.)
        - Status normalization
        - Description cleaning
        - Keyword extraction for matching
        """
        pass
```

**Output Model:**

```python
@dataclass
class NormalizedBacklogItem:
    id: str                   # Internal UUID
    external_id: str          # Original ID
    title: str
    description: str
    item_type: ItemType       # Enum: bug, feature, tech_debt, etc.
    priority: Priority        # Enum: critical, high, medium, low
    status: BacklogStatus     # Enum: backlog, ready, etc.
    labels: List[str]
    keywords: List[str]       # Extracted for matching
    source_system: str
    created_at: datetime
```

---

### Step 7.4: Matching & Deduplication

**Doel:** Detecteer duplicaten tussen geïmporteerde items en gegenereerde epics/stories.

**Matching Strategieën:**

| Strategie | Beschrijving | Score Weight |
|-----------|--------------|--------------|
| **Exact Title** | Exacte titel match | 1.0 |
| **Fuzzy Title** | Levenshtein distance < 0.3 | 0.8 |
| **Keyword Overlap** | >= 70% keyword overlap | 0.6 |
| **Module Match** | Zelfde module/component | 0.4 |
| **Semantic** | Embedding similarity > 0.85 | 0.7 |

**Matching Algorithm:**

```python
class BacklogMatchingService:
    def find_matches(
        self,
        imported_items: List[NormalizedBacklogItem],
        generated_items: List[GeneratedEpic]
    ) -> List[MatchResult]:
        """
        Find potential duplicates between imported and generated items.

        Returns matches with confidence scores.
        """
        matches = []

        for imported in imported_items:
            for generated in generated_items:
                score = self._calculate_match_score(imported, generated)

                if score >= self.threshold:  # Default: 0.6
                    matches.append(MatchResult(
                        imported_item=imported,
                        generated_item=generated,
                        confidence=score,
                        match_reasons=self._get_match_reasons(imported, generated)
                    ))

        return matches
```

**Match Result Model:**

```python
@dataclass
class MatchResult:
    imported_item_id: str
    generated_item_id: str
    confidence: float         # 0.0 - 1.0
    match_reasons: List[str]  # ["fuzzy_title", "keyword_overlap"]
    recommended_action: str   # "merge", "keep_both", "review"
```

**Database:**

```sql
CREATE TABLE backlog_matches (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    imported_item_id UUID REFERENCES imported_backlog_items(id),
    generated_item_id UUID,  -- Reference to generated epic/story
    confidence DECIMAL(3,2),
    match_reasons JSONB,
    recommended_action VARCHAR(20),
    user_decision VARCHAR(20),  -- merge, keep_both, keep_imported, keep_generated
    decided_at TIMESTAMP,
    decided_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Step 7.5: Context Enrichment

**Doel:** Verrijk backlog items met informatie uit de code-analyse.

**Enrichment Types:**

| Type | Bron | Toegevoegde Info |
|------|------|------------------|
| **Module Mapping** | Phase 2 Domains | Welke module(s) zijn affected |
| **Complexity Score** | Phase 4 Analysis | Geschatte complexity |
| **Risk Assessment** | Phase 1 Dependencies | Dependency risks |
| **Related Code** | Phase 1 Graph | Gerelateerde bestanden |
| **Effort Estimate** | Phase 5 Eliza | FP/SP schatting |

**Service:**

```python
class BacklogEnrichmentService:
    def enrich(
        self,
        items: List[NormalizedBacklogItem],
        analysis_results: BrownPaperAnalysis
    ) -> List[EnrichedBacklogItem]:
        """
        Enrich backlog items with code analysis context.

        - Map items to affected modules
        - Add complexity scores
        - Identify dependency risks
        - Link to related code files
        - Estimate effort
        """
        pass
```

**Output Model:**

```python
@dataclass
class EnrichedBacklogItem:
    # Base fields from NormalizedBacklogItem
    id: str
    external_id: str
    title: str
    description: str
    item_type: ItemType
    priority: Priority
    status: BacklogStatus

    # Enrichment fields (NIEUW)
    affected_modules: List[str]
    affected_files: List[str]
    complexity_score: float       # 1-10
    risk_level: str              # low, medium, high, critical
    dependency_count: int
    estimated_story_points: int
    estimated_function_points: float
    related_generated_items: List[str]
    enrichment_metadata: Dict
```

---

### Step 7.6: Priority Calculation

**Doel:** Bereken unified priority score voor alle items.

**Priority Formula:**

```
priority_score = (
    base_priority_weight * priority_value +
    complexity_weight * (10 - complexity_score) +
    risk_weight * risk_value +
    age_weight * age_factor +
    business_value_weight * business_value
)
```

**Weging configuratie:**

```python
@dataclass
class PriorityWeights:
    base_priority: float = 0.30    # Original priority
    complexity: float = 0.15       # Lower complexity = higher priority
    risk: float = 0.20            # Higher risk = higher priority
    age: float = 0.10             # Older items get slight boost
    business_value: float = 0.25  # If available
```

**Service:**

```python
class BacklogPriorityService:
    def calculate_priorities(
        self,
        items: List[EnrichedBacklogItem],
        weights: PriorityWeights
    ) -> List[PrioritizedBacklogItem]:
        """
        Calculate unified priority scores.

        Combines:
        - Original priority from source system
        - Code complexity from analysis
        - Risk assessment
        - Item age
        - Business value (if provided)
        """
        pass
```

---

### Step 7.7: Unified Backlog Output

**Doel:** Combineer alle items in één unified backlog.

**Output Structure:**

```python
@dataclass
class UnifiedBacklog:
    session_id: str
    generated_at: datetime

    # Statistics
    total_items: int
    imported_count: int
    generated_count: int
    merged_count: int

    # Items by category
    items: List[UnifiedBacklogItem]

    # Groupings
    by_type: Dict[str, List[UnifiedBacklogItem]]
    by_module: Dict[str, List[UnifiedBacklogItem]]
    by_priority: Dict[str, List[UnifiedBacklogItem]]

    # Pending decisions
    pending_matches: List[MatchResult]  # Need user decision

    # Metadata
    sources: List[str]
    analysis_version: str
```

**Database:**

```sql
CREATE TABLE unified_backlog (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),

    -- Statistics
    total_items INTEGER,
    imported_count INTEGER,
    generated_count INTEGER,
    merged_count INTEGER,

    -- Full data
    items JSONB NOT NULL,
    by_type JSONB,
    by_module JSONB,
    by_priority JSONB,

    -- Pending
    pending_matches JSONB,

    -- Audit
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported_to_kanban BOOLEAN DEFAULT FALSE,
    exported_at TIMESTAMP
);
```

---

## API Endpoints (Nieuw)

| Method | Endpoint | Beschrijving |
|--------|----------|--------------|
| POST | `/api/brown-paper/sessions/{id}/backlog-source` | Configure backlog source |
| GET | `/api/brown-paper/sessions/{id}/backlog-source` | Get source config |
| POST | `/api/brown-paper/sessions/{id}/backlog/import` | Trigger import |
| GET | `/api/brown-paper/sessions/{id}/backlog/imported` | Get imported items |
| GET | `/api/brown-paper/sessions/{id}/backlog/matches` | Get detected matches |
| POST | `/api/brown-paper/sessions/{id}/backlog/matches/{match_id}/decide` | User decision on match |
| GET | `/api/brown-paper/sessions/{id}/backlog/unified` | Get unified backlog |
| POST | `/api/brown-paper/sessions/{id}/backlog/export-to-kanban` | Export to KANBAN |

---

## Database Schema Overzicht

```
┌─────────────────────────┐
│  brown_paper_sessions   │
│  (bestaand)             │
└───────────┬─────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│    backlog_sources      │      │  imported_backlog_items │
│                         │      │                         │
│  - source_type          │ 1:N  │  - external_id          │
│  - source_config        │─────►│  - title                │
│  - field_mapping        │      │  - description          │
│  - filters              │      │  - item_type            │
└─────────────────────────┘      │  - priority             │
                                 │  - source_metadata      │
                                 └───────────┬─────────────┘
                                             │
                                             │ 1:N
                                             ▼
                                 ┌─────────────────────────┐
                                 │    backlog_matches      │
                                 │                         │
                                 │  - imported_item_id     │
                                 │  - generated_item_id    │
                                 │  - confidence           │
                                 │  - recommended_action   │
                                 │  - user_decision        │
                                 └─────────────────────────┘
                                             │
                                             │
                                             ▼
                                 ┌─────────────────────────┐
                                 │    unified_backlog      │
                                 │                         │
                                 │  - items (JSONB)        │
                                 │  - by_type              │
                                 │  - by_module            │
                                 │  - pending_matches      │
                                 └─────────────────────────┘
```

---

## Documentatie Updates

| Document | Wijziging |
|----------|-----------|
| `02-BROWN-PAPER-WORKFLOW.md` | Phase 7: Backlog Integration toevoegen |
| `00-WORKFLOW-MASTER-OVERVIEW.md` | Backlog intake vermelden |
| `workflow-separation-plan.md` | Backlog in AnalysisContract |
| API documentatie | Nieuwe endpoints documenteren |

---

## Implementatie Fasen

### Fase 1: Foundation (Week 1)
- [ ] Database schema aanmaken
- [ ] BacklogSource model en repository
- [ ] Basis API endpoints

### Fase 2: Import Adapters (Week 1-2)
- [ ] JsonFileAdapter
- [ ] CsvFileAdapter
- [ ] MarkdownAdapter
- [ ] InternalDbAdapter

### Fase 3: Normalization (Week 2)
- [ ] Type mapping configuratie
- [ ] Priority normalization
- [ ] Keyword extraction

### Fase 4: Matching (Week 2-3)
- [ ] Exact matching
- [ ] Fuzzy matching
- [ ] Keyword overlap matching
- [ ] Match review UI

### Fase 5: Enrichment (Week 3)
- [ ] Module mapping
- [ ] Complexity scoring
- [ ] Risk assessment
- [ ] Effort estimation

### Fase 6: Priority & Output (Week 3-4)
- [ ] Priority calculation service
- [ ] Unified backlog generation
- [ ] Export to KANBAN

### Fase 7: External Adapters (Optional, Week 4+)
- [ ] JiraAdapter
- [ ] GitHubAdapter
- [ ] AzureDevOpsAdapter

---

## Validatie Checklist

Voordat implementatie start, valideer:

- [ ] Zijn de ondersteunde bronnen correct? (JSON, CSV, MD, API's)
- [ ] Klopt de matching strategie? (thresholds, weights)
- [ ] Is de priority formule acceptabel?
- [ ] Past Phase 7 in de bestaande Brown Paper flow?
- [ ] Zijn alle database relaties correct?
- [ ] Is de API consistent met bestaande endpoints?
- [ ] Wordt backward compatibility behouden?

---

## Open Vragen

| # | Vraag | Impact |
|---|-------|--------|
| 1 | Moet backlog import verplicht of optioneel zijn? | API design |
| 2 | Wat als er geen backlog is? (nieuw project) | Flow logic |
| 3 | Hoe lang bewaren we match decisions? | Data retention |
| 4 | Willen we real-time sync met external systems? | Scope |
| 5 | Moet unified backlog ook naar external system terug? | Bi-directional sync |

---

## Risico's

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Complexe matching logic | High | Start met simple matching, itereer |
| External API rate limits | Medium | Caching, batch imports |
| Data formaat inconsistenties | Medium | Robuuste normalization |
| User overwhelm bij veel matches | Medium | Smart defaults, bulk actions |

---

## Gerelateerde Documenten

| Document | Relatie |
|----------|---------|
| [workflow-separation-plan.md](./workflow-separation-plan.md) | AnalysisContract uitbreiding |
| [02-BROWN-PAPER-WORKFLOW.md](../workflows/02-BROWN-PAPER-WORKFLOW.md) | Phase 7 toevoeging |
| [brown-paper-enhanced.md](./brown-paper-enhanced.md) | Service integratie |

---

*Document Status: DRAFT - Ready for Validation*
*Generated: Week 144 (2026-01-09)*
