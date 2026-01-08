# Multi-Language Business Rule Extractors

**Status:** PLANNED - Next Priority
**Created:** 2025-12-25
**Author:** Claude Code
**Related:** [ROADMAP.md](../../ROADMAP.md), [HCI-CRS Agenda Analysis](#hci-crs-agenda-analysis)

---

## Executive Summary

Dit document beschrijft de architectuur voor taal-specifieke business rule extractors met ondersteuning voor:
- VB.NET (.aspx.vb, .vb)
- Classic ASP/VBScript (.asp)
- C# (.cs)
- Stored Procedures (T-SQL, PL/SQL)
- JavaScript/TypeScript (.js, .ts)
- Python (.py) - bestaand

Plus een nieuwe **Business Rule Correlation** feature om regels te koppelen aan use cases/workflows.

---

## Problem Statement

### Huidige Situatie
De bestaande `BusinessRuleExtractor` in `app/services/static_analysis/business_rule_extractor.py`:
- Gebruikt Python AST als primaire parser
- Heeft beperkte regex fallback voor andere talen
- Vindt 0 regels in VB.NET/ASP code (zie HCI-CRS analyse)

### HCI-CRS Agenda Analyse (2025-12-25)
| Metric | Standalone Extractor | Bestaande Component |
|--------|---------------------|---------------------|
| Default.aspx.vb (1543 LOC) | 235 business rules | 0 |
| Agenda.asp (1788 LOC) | 329 business rules | 0 |
| **Totaal** | **564 business rules** | **0** |

### Business Rules per Type (HCI-CRS)
| Type | Count | Beschrijving |
|------|-------|--------------|
| validation | 236 | IF-THEN beslissingslogica |
| scheduling | 93 | Datum/tijd afspraaklogica |
| branching | 83 | Select Case status-handling |
| threshold | 61 | Numerieke grenzen |
| data_access | 37 | Database operaties |
| state_management | 21 | Session/Request handling |
| error_handling | 20 | Foutafhandeling |
| navigation | 9 | Redirects |
| authorization | 4 | Toegangscontrole |

---

## Solution Architecture

### 1. Extractor Class Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BaseBusinessRuleExtractor                                │
│                        (Abstract Base Class)                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ + extract_from_file(path, source) -> List[BusinessRule]              │  │
│  │ + extract_from_directory(path) -> Dict[str, List[BusinessRule]]      │  │
│  │ + detect_rule_type(code_block) -> RuleType                           │  │
│  │ + generate_natural_language(rule) -> str                             │  │
│  │ + get_supported_extensions() -> List[str]                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│    ┌───────────┬───────────┬───────┴───────┬───────────┬───────────┐       │
│    ▼           ▼           ▼               ▼           ▼           ▼       │
│ ┌───────┐ ┌───────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│ │Python │ │VB.NET │ │ClassicASP │ │  CSharp   │ │JavaScript │ │StoredPrc│ │
│ │Extract│ │Extract│ │ Extractor │ │ Extractor │ │ Extractor │ │Extractor│ │
│ │  or   │ │  or   │ │           │ │           │ │           │ │         │ │
│ └───────┘ └───────┘ └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
│  .py       .vb       .asp          .cs          .js/.ts      .sql         │
│            .aspx.vb  .asa                       .jsx/.tsx    .prc         │
│            .aspx.cs                                          .pkg         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ExtractorFactory                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ + get_extractor(file_path: str) -> BaseBusinessRuleExtractor         │  │
│  │ + register_extractor(extensions: List[str], extractor_class)         │  │
│  │ + get_all_extractors() -> Dict[str, BaseBusinessRuleExtractor]       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BusinessRule (Unified Output)                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ id: str                    # "BR-001"                                 │  │
│  │ rule_type: RuleType        # validation, authorization, scheduling   │  │
│  │ condition: str             # "If Not tablePermissions.CanView Then"  │  │
│  │ action: str                # "Response.Redirect(...)"                │  │
│  │ source_file: str           # "Agenda.asp"                            │  │
│  │ source_lines: Tuple[int]   # (12, 15)                                │  │
│  │ confidence: float          # 0.85                                    │  │
│  │ natural_language: str      # "IF user cannot view THEN redirect"     │  │
│  │ variables_involved: List   # ["tablePermissions", "strRedirect"]     │  │
│  │ related_entities: List     # ["Afspraak", "Hulpverlener"]            │  │
│  │ workflow_context: str      # "appointment_create" (NEW)              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Language-Specific Implementations

#### 2.1 VB.NET Extractor
```python
class VBNetBusinessRuleExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from VB.NET code (.vb, .aspx.vb, .aspx.cs)

    Detection patterns:
    - If-Then-Else blocks
    - Select Case statements
    - Property getters/setters with validation
    - Event handlers with authorization checks
    - Try-Catch error handling
    """

    SUPPORTED_EXTENSIONS = ['.vb', '.aspx.vb', '.ascx.vb']

    PATTERNS = {
        'validation': r'If\s+(.+?)\s+Then',
        'authorization': r'(CanView|CanEdit|CanDelete|CanAdd|intCan\w+)',
        'scheduling': r'(StartTime|EndTime|Duration|Interval|Datum\w*)',
        'branching': r'(Select\s+Case|Case\s+\d+|Case\s+Else)',
        'workflow': r'(Status|State)\s*(=|<>|Is)',
        'navigation': r'Response\.Redirect',
        'data_access': r'(\.Execute|Recordset|DataReader)',
    }
```

#### 2.2 Stored Procedure Extractor
```python
class StoredProcedureExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from SQL stored procedures.

    Supports:
    - T-SQL (SQL Server)
    - PL/SQL (Oracle)
    - PL/pgSQL (PostgreSQL)

    Detection patterns:
    - IF-ELSE blocks
    - CASE WHEN statements
    - Constraint checks
    - Transaction boundaries
    - Error handling (TRY-CATCH, EXCEPTION)
    """

    SUPPORTED_EXTENSIONS = ['.sql', '.prc', '.pkg', '.pkb', '.pks']

    PATTERNS = {
        'validation': r'IF\s+(.+?)\s+(BEGIN|THEN)',
        'constraint': r'CHECK\s*\((.+?)\)',
        'branching': r'CASE\s+WHEN\s+(.+?)\s+THEN',
        'transaction': r'(BEGIN\s+TRAN|COMMIT|ROLLBACK)',
        'error_handling': r'(TRY|CATCH|EXCEPTION|RAISERROR)',
        'authorization': r'(EXECUTE\s+AS|GRANT|DENY|HAS_PERMS)',
    }
```

---

## 3. Business Rule Correlation (NEW FEATURE)

### Problem: Isolated Rules
Momenteel extraheren we losse regels zonder context. Bijvoorbeeld:
- BR-001: `If intCanView = 0 Then ...` (authorization)
- BR-015: `If AgendaStartTime > AgendaEndTime Then ...` (validation)
- BR-042: `rst.Execute("INSERT INTO taAfspraak...")` (data_access)

Deze regels horen samen in de workflow "Afspraak Plannen".

### Solution: Workflow-Based Rule Grouping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BusinessRuleCorrelator                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ + correlate_rules(rules: List[BusinessRule]) -> List[RuleWorkflow]   │  │
│  │ + detect_workflows(rules: List[BusinessRule]) -> List[WorkflowDef]   │  │
│  │ + build_dependency_graph(rules) -> RuleDependencyGraph               │  │
│  │ + generate_workflow_diagram(workflow: RuleWorkflow) -> str           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RuleWorkflow                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ id: str                      # "WF-001"                               │  │
│  │ name: str                    # "Afspraak Plannen"                     │  │
│  │ description: str             # "Plan een nieuwe afspraak in agenda"   │  │
│  │ trigger: str                 # "User clicks 'Nieuwe Afspraak'"        │  │
│  │ rules: List[BusinessRule]    # Ordered list of rules in workflow      │  │
│  │ rule_sequence: List[str]     # ["BR-001", "BR-015", "BR-042"]         │  │
│  │ entities: List[str]          # ["Afspraak", "Hulpverlener", "Client"] │  │
│  │ success_outcome: str         # "Afspraak opgeslagen en bevestigd"     │  │
│  │ failure_outcomes: List[str]  # ["Geen rechten", "Tijdslot bezet"]     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Correlation Strategies

#### Strategy 1: Entity-Based Grouping
Groepeer regels die dezelfde entiteiten manipuleren:
```python
# Regels met "Afspraak" entity
afspraak_rules = [r for r in rules if "Afspraak" in r.related_entities]

# Cluster op CRUD operatie
create_rules = [r for r in afspraak_rules if is_create_operation(r)]
read_rules = [r for r in afspraak_rules if is_read_operation(r)]
update_rules = [r for r in afspraak_rules if is_update_operation(r)]
delete_rules = [r for r in afspraak_rules if is_delete_operation(r)]
```

#### Strategy 2: Call Graph Analysis
Volg function calls om execution paths te bepalen:
```
Page_Load
├── CheckTableAccess (authorization)
├── LoadCalendar
│   ├── ValidateDateRange (validation)
│   └── GetAfspraken (data_access)
└── BindGrid
```

#### Strategy 3: Control Flow Tracing
Volg branches en conditionals:
```
IF authorization_check THEN
    IF validation_check THEN
        IF availability_check THEN
            DO create_appointment
        ELSE
            SHOW "Tijdslot bezet"
        END IF
    ELSE
        SHOW "Validatie fout"
    END IF
ELSE
    REDIRECT "NoAccess.asp"
END IF
```

### Example Workflows for HCI-CRS Agenda

#### Workflow 1: Afspraak Plannen
```yaml
id: WF-001
name: Afspraak Plannen
trigger: User clicks 'Nieuwe Afspraak' button
entities: [Afspraak, Hulpverlener, Client, Agenda]

steps:
  1_authorization:
    type: authorization
    rules: [BR-001, BR-002]
    check: "Heeft gebruiker rechten om in deze agenda te plannen?"
    fail_action: "Redirect naar NoAccess.asp"

  2_hulpverlener_access:
    type: authorization
    rules: [BR-003]
    check: "Heeft gebruiker toegang tot deze hulpverlener?"
    fail_action: "Redirect naar NoAccess.asp met foutmelding"

  3_slot_validation:
    type: scheduling
    rules: [BR-015, BR-016, BR-017]
    check: "Is tijdslot binnen agenda-uren? Start < Eind?"
    fail_action: "Toon validatiefout"

  4_availability:
    type: data_access
    rules: [BR-042, BR-043]
    check: "Is het tijdslot nog beschikbaar?"
    fail_action: "Toon 'Tijdslot bezet' melding"

  5_save:
    type: data_access
    rules: [BR-050]
    action: "INSERT INTO taAfspraak"

  6_confirm:
    type: navigation
    rules: [BR-055]
    action: "Redirect naar bevestigingspagina"

success_outcome: "Afspraak succesvol gepland"
failure_outcomes:
  - "Geen rechten voor deze agenda"
  - "Geen toegang tot hulpverlener"
  - "Ongeldige tijden opgegeven"
  - "Tijdslot is bezet"
```

#### Workflow 2: Afspraak Bekijken (VIEW)
```yaml
id: WF-002
name: Afspraak Bekijken
trigger: User clicks op bestaande afspraak in agenda
entities: [Afspraak, Hulpverlener, Client]

steps:
  1_authorization:
    type: authorization
    rules: [BR-060, BR-061]
    check: "Heeft gebruiker VIEW rechten (intCanView)?"
    fail_action: "Redirect naar NoAccess.asp"

  2_record_access:
    type: authorization
    rules: [BR-062]
    check: "Heeft gebruiker toegang tot deze specifieke afspraak?"
    call: "GetPrivilegesRecord_Afspraak_ByID"
    fail_action: "Toon 'Geen toegang tot dit dossier'"

  3_load_data:
    type: data_access
    rules: [BR-063, BR-064]
    action: "SELECT * FROM taAfspraak WHERE AfspraakID = :id"
    load: ["Afspraak", "Client", "Hulpverlener", "Registratiegegevens"]

  4_render:
    type: navigation
    rules: [BR-065]
    action: "Render afspraak details in read-only modus"

success_outcome: "Afspraak details getoond"
failure_outcomes:
  - "Geen view rechten"
  - "Geen toegang tot dit dossier"
  - "Afspraak niet gevonden"
```

#### Workflow 3: Afspraak Wijzigen (EDIT)
```yaml
id: WF-003
name: Afspraak Wijzigen
trigger: User clicks 'Wijzigen' op bestaande afspraak
entities: [Afspraak, Hulpverlener, Client, Agenda]

steps:
  1_authorization:
    type: authorization
    rules: [BR-070, BR-071]
    check: "Heeft gebruiker EDIT rechten (intCanEdit)?"
    fail_action: "Redirect met 'U heeft geen rechten om gegevens te wijzigen'"

  2_record_access:
    type: authorization
    rules: [BR-072]
    check: "Heeft gebruiker toegang tot deze specifieke afspraak?"
    call: "GetPrivilegesRecord_Afspraak_ByID"
    fail_action: "Toon 'Geen wijzigingsrechten voor dit dossier'"

  3_status_check:
    type: workflow
    rules: [BR-073]
    check: "Is afspraak niet al verwerkt/gefactureerd?"
    fail_action: "Toon 'Verwerkte afspraken kunnen niet worden gewijzigd'"

  4_load_data:
    type: data_access
    rules: [BR-074]
    action: "SELECT * FROM taAfspraak WHERE AfspraakID = :id"
    mode: "Render in EDIT mode (formulier invulbaar)"

  5_registration_validation:
    type: validation
    rules: [BR-075, BR-076, BR-077]
    check: "Valideer registratievelden voor DBC/BGGZ/Jeugdtraject"
    conditional: "Afhankelijk van registratie type"

  6_slot_validation:
    type: scheduling
    rules: [BR-078, BR-079]
    check: "Is nieuw tijdslot geldig? Start < Eind? Binnen agenda-uren?"
    fail_action: "Toon validatiefout"

  7_availability_check:
    type: data_access
    rules: [BR-080]
    check: "Is nieuw tijdslot beschikbaar (exclusief huidige afspraak)?"
    fail_action: "Toon 'Tijdslot is bezet'"

  8_save:
    type: data_access
    rules: [BR-081]
    action: "UPDATE taAfspraak SET ... WHERE AfspraakID = :id"

  9_confirm:
    type: navigation
    rules: [BR-082]
    action: "Redirect naar bevestiging of terug naar agenda"

success_outcome: "Afspraak succesvol gewijzigd"
failure_outcomes:
  - "Geen wijzigingsrechten"
  - "Geen toegang tot dit dossier"
  - "Afspraak is al verwerkt"
  - "Ongeldige registratiegegevens"
  - "Ongeldige tijden opgegeven"
  - "Nieuw tijdslot is bezet"
```

#### Workflow 4: Afspraak Verwijderen (DELETE)
```yaml
id: WF-004
name: Afspraak Verwijderen
trigger: User clicks 'Verwijderen' op afspraak
entities: [Afspraak]

steps:
  1_authorization:
    type: authorization
    rules: [BR-090]
    check: "Heeft gebruiker DELETE rechten (intCanDelete)?"
    fail_action: "Toon 'Geen rechten' melding"

  2_record_access:
    type: authorization
    rules: [BR-091]
    check: "Heeft gebruiker toegang tot deze specifieke afspraak?"
    call: "GetPrivilegesRecord_Afspraak_ByID"
    fail_action: "Toon 'Geen verwijderrechten voor dit dossier'"

  3_status_check:
    type: workflow
    rules: [BR-092]
    check: "Is afspraak status niet 'Verwerkt'?"
    fail_action: "Toon 'Verwerkte afspraken kunnen niet worden verwijderd'"

  4_delete:
    type: data_access
    rules: [BR-093]
    action: "UPDATE taAfspraak SET Deleted=1"
    note: "Soft delete, niet fysieke verwijdering"

  5_refresh:
    type: navigation
    rules: [BR-094]
    action: "Refresh calendar view"

success_outcome: "Afspraak verwijderd"
failure_outcomes:
  - "Geen delete rechten"
  - "Geen toegang tot dit dossier"
  - "Afspraak is al verwerkt"
```

### CRUD Workflow Summary

| # | Workflow | Mode | Key Authorization | Key Validation |
|---|----------|------|-------------------|----------------|
| WF-001 | Afspraak Plannen | INSERT | intCanAdd + hulpverlener access | Tijdslot geldig + beschikbaar |
| WF-002 | Afspraak Bekijken | VIEW | intCanView + record access | - |
| WF-003 | Afspraak Wijzigen | EDIT | intCanEdit + record access | Status + tijdslot + registratie |
| WF-004 | Afspraak Verwijderen | DELETE | intCanDelete + record access | Status niet verwerkt |

### Afgeleide Workflow Patterns

Naast de 4 core CRUD workflows bestaan er **afgeleide patterns** die business rules van meerdere workflows combineren:

#### Pattern: COPY (Afspraak Kopiëren)
```yaml
pattern: COPY
derived_from: [VIEW, INSERT]
description: Kopieer bestaande afspraak naar nieuwe

implementation:
  mode: "INSERT"           # Wordt behandeld als INSERT
  source: "CopyKey param"  # ID van bron-afspraak
  authorization: intCanEdit # Nodig om bron te lezen (regel 1168)
  save: DB_Insert          # Maakt nieuw record (regel 5230)

rule_composition:
  from_VIEW:
    - BR-062: Record access check (lezen bron-afspraak)
    - BR-063: Load source data
  from_INSERT:
    - BR-001: Table access check (intCanAdd)
    - BR-015: Slot validation (nieuwe tijden)
    - BR-042: Availability check
    - BR-050: DB_Insert

unique_aspects:
  - Pre-filled form data van bron
  - Nieuwe AfspraakID gegenereerd
  - Kan naar andere datum/tijd gekopieerd worden
```

**Waarom geen apart workflow?**
- Geen unieke business rules (hergebruikt VIEW + INSERT)
- Technisch hetzelfde als INSERT met `CopyKey` parameter
- Authorization volgt bestaande patronen

---

## 4. Hybrid Extraction Architecture

### 3-Tier Extraction Strategy

De oplossing gebruikt een **hybride aanpak** die de beste methode per situatie selecteert:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID BUSINESS RULE EXTRACTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIER 1: AST-BASED (Hoogste precisie, waar beschikbaar)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Python      → Python AST (bestaand)                    confidence: 95% ││
│  │ C#          → Roslyn Compiler API                      confidence: 95% ││
│  │ JavaScript  → @babel/parser of tree-sitter             confidence: 90% ││
│  │ TypeScript  → TypeScript Compiler API                  confidence: 90% ││
│  │ Java        → JavaParser                               confidence: 90% ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                          ↓ Fallback als geen AST beschikbaar                │
│  TIER 2: REGEX-ENHANCED (Legacy talen, pattern-based)                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ VB.NET       → Regex + Sub/Function/Class detection    confidence: 80% ││
│  │ Classic ASP  → Regex + VBScript structure tracking     confidence: 75% ││
│  │ VBScript     → Regex patterns                          confidence: 70% ││
│  │ T-SQL        → Regex + statement boundaries            confidence: 80% ││
│  │ PL/SQL       → Regex + block detection                 confidence: 80% ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                          ↓ Optional enhancement (customer tier-afhankelijk) │
│  TIER 3: LLM-ASSISTED (Complex/ambiguous cases)                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Ambiguous patterns  → Ollama classification            confidence: 85% ││
│  │ Natural language    → Gemini extraction                confidence: 80% ││
│  │ Cross-validation    → Multi-LLM consensus              confidence: 90% ││
│  │ Premium synthesis   → Claude Opus final pass           confidence: 95% ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  OUTPUT: Unified BusinessRule format met confidence + extraction_method     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Customer Tier vs Extraction Capability

| Customer Tier | Price | AST (Tier 1) | Regex (Tier 2) | LLM (Tier 3) | Target Confidence |
|---------------|-------|--------------|----------------|--------------|-------------------|
| **FREE** | $0 | ✅ | ✅ | ❌ | 70-75% |
| **BASIC** | $5 | ✅ | ✅ | Ollama only | 75-80% |
| **STANDARD** ★ | $25 | ✅ | ✅ | + Groq/Gemini | 80-85% |
| **PROFESSIONAL** | $75 | ✅ | ✅ | + GPT-5.2 | 85-90% |
| **PREMIUM** | $150 | ✅ | ✅ | + Claude Opus | 90-95% |

*Alle tiers krijgen AST + Regex. LLM-validatie escaleert per tier.*

### LLM Provider Mapping

```python
from enum import Enum
from typing import List

class CustomerTier(Enum):
    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"

TIER_LLM_MAPPING: dict[CustomerTier, List[str]] = {
    CustomerTier.FREE: [],                                          # No LLM assistance
    CustomerTier.BASIC: ["ollama"],                                 # Local LLMs only
    CustomerTier.STANDARD: ["ollama", "groq", "gemini"],
    CustomerTier.PROFESSIONAL: ["ollama", "groq", "gemini", "openai"],
    CustomerTier.PREMIUM: ["ollama", "groq", "gemini", "openai", "anthropic"],
}
```

---

## 5. Implementation Plan

### Phase 1: Hybrid Core Architecture (Week 111)
**Effort:** 24 uur

| Task | Uur | Output | Tier |
|------|-----|--------|------|
| Abstract base class with tier support | 4 | `base_extractor.py` | Core |
| ExtractionTier enum + ExtractionResult | 2 | `models.py` | Core |
| VB.NET extractor (regex-enhanced) | 6 | `vbnet_extractor.py` | Tier 2 |
| Classic ASP extractor (regex-enhanced) | 4 | `asp_extractor.py` | Tier 2 |
| Extractor factory with tier selection | 4 | `extractor_factory.py` | Core |
| Unit tests + HCI-CRS validation | 4 | `test_extractors.py` | - |

### Phase 2: Stored Procedure Support (Week 111-112)
**Effort:** 16 uur

| Task | Uur | Output | Tier |
|------|-----|--------|------|
| T-SQL extractor | 6 | `tsql_extractor.py` | Tier 2 |
| PL/SQL extractor | 4 | `plsql_extractor.py` | Tier 2 |
| Procedure call graph | 4 | `procedure_graph.py` | Tier 2 |
| Tests | 2 | `test_stored_procedures.py` | - |

### Phase 2.5: LLM-Assisted Extraction (Week 112) ⭐ NEW
**Effort:** 20 uur

| Task | Uur | Output | Customer Tier |
|------|-----|--------|---------------|
| LLM Rule Classifier | 6 | `llm_classifier.py` | BASIC+ |
| LLM Rule Extractor | 6 | `llm_extractor.py` | STANDARD+ |
| Multi-LLM Validator | 4 | `multi_llm_validator.py` | PROFESSIONAL+ |
| Tier-aware Orchestrator | 2 | `tier_orchestrator.py` | All |
| Tests | 2 | `test_llm_extraction.py` | - |

**Use Cases voor LLM-Assisted Extraction:**
1. **Ambiguous Regex Match** - Regex vindt `If condition Then` maar LLM bepaalt of het echte business rule is
2. **Comment Extraction** - `' Check if user has permission` → BR-xxx authorization rule
3. **Natural Language** - VBScript met Nederlandse teksten in MsgBox calls
4. **Cross-Validation** - 3 LLMs moeten het eens zijn voor confidence boost

### Phase 3: Business Rule Correlation (Week 112)
**Effort:** 24 uur

| Task | Uur | Output |
|------|-----|--------|
| Entity detection | 4 | `entity_detector.py` |
| Call graph builder | 6 | `call_graph_builder.py` |
| Workflow correlator | 8 | `rule_correlator.py` |
| Workflow diagram generator | 4 | `workflow_diagram.py` |
| Tests | 2 | `test_correlation.py` |

### Phase 4: Integration & Dashboard (Week 112-113)
**Effort:** 16 uur

| Task | Uur | Output |
|------|-----|--------|
| API endpoints | 4 | `api/business_rules.py` |
| Database models | 2 | `models/business_rule.py` |
| Frontend dashboard | 6 | `business-rules-dashboard.html` |
| Workflow viewer | 4 | Mermaid/D3 visualization |

### Total Effort Summary

| Phase | Uren | Focus |
|-------|------|-------|
| Phase 1: Hybrid Core Architecture | 24 | Base + VB.NET + ASP + Factory |
| Phase 2: Stored Procedures | 16 | T-SQL + PL/SQL |
| Phase 2.5: LLM-Assisted ⭐ | 20 | Classifier + Validator + Orchestrator |
| Phase 3: Business Rule Correlation | 24 | Workflow detection + Mermaid |
| Phase 4: Integration | 16 | API + DB + Dashboard |
| Phase 4.5: Traceability ⭐ | 12 | Epic/Feature/Story/Rule linkage |
| Phase 5: Agent/Workflow Integration ⭐ | 16 | BROWN_PAPER, MIGRATION, BACKLOG_GENERATION |
| **TOTAAL** | **128 uur** | **~4 weken full-time** |

### Phase 4.5: Traceability Implementation (Week 113) ⭐ NEW
**Effort:** 12 uur

De traceability laag linkt business rules aan de epic/feature/story hiërarchie:

| Task | Uur | Output |
|------|-----|--------|
| Database tabellen + migratie | 3 | `epics`, `features`, `user_stories`, `story_business_rules` |
| API endpoints | 4 | CRUD voor traceability, matrix export |
| Traceability views | 2 | `v_traceability_matrix`, `v_rule_impact` |
| Integration met extraction pipeline | 2 | Auto-link suggesties na rule extraction |
| Impact analysis queries | 1 | Welke stories/epics geraakt bij rule wijziging |

#### Traceability Functionaliteit

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRACEABILITY LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EXTRACTION PIPELINE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Business Rules →  Auto-suggest links  →  Manual review  →  Linkage     ││
│  │ (564 rules)       (pattern matching)     (confidence)     (persistent) ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  QUERY CAPABILITIES                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ "Welke rules bij feature X?"       → /api/features/{id}/stories/rules  ││
│  │ "Impact van BR-042 wijziging?"     → /api/rules/{id}/impact            ││
│  │ "Export matrix voor audit?"        → /api/traceability/{project}/matrix││
│  │ "Alle authorization rules plannen" → /api/traceability/search?type=... ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  OUTPUT FORMATS                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ JSON API         → Dashboard integration                                ││
│  │ CSV/Excel        → Compliance audit export                              ││
│  │ Markdown         → Documentation generation                             ││
│  │ Mermaid          → Visual traceability graphs                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 5: Agent & Workflow Integration (Week 113-114) ⭐ NEW
**Effort:** 16 uur

De Business Rule Extraction moet geïntegreerd worden in de bestaande MarQed workflows:

| Workflow | Integration Point | Agent | Output |
|----------|-------------------|-------|--------|
| **BROWN_PAPER** | Step 2: Code Analysis | Miguel | Business rules als input voor migration planning |
| **MIGRATION** | Step 3: Impact Analysis | Miguel | Welke rules moeten worden gemigreerd |
| **BACKLOG_GENERATION** | Step 1: Code Scan | Peter | Rules → User Stories mapping |
| **PROJECT_DEFINITION** | Step 4: Architecture | Felix | Rules als architectural constraints |

#### Integration Tasks

| Task | Uur | Output | Touches |
|------|-----|--------|---------|
| BROWN_PAPER workflow hook | 4 | `workflows/brown_paper.py` update | Miguel agent |
| MIGRATION workflow hook | 4 | `workflows/migration.py` update | Miguel agent |
| BACKLOG_GENERATION integration | 4 | `services/backlog_service.py` update | Peter agent |
| Agent prompt updates | 2 | Agent prompts voor rule context | Felix, Miguel, Peter |
| Integration tests | 2 | `test_workflow_integration.py` | - |

#### Workflow Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXISTING WORKFLOWS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BROWN_PAPER (Legacy Migration)                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 1: Intake → Step 2: Code Analysis → Step 3: Planning → ...        ││
│  │                          ↓                                              ││
│  │              ┌──────────────────────┐                                   ││
│  │              │ Business Rule        │                                   ││
│  │              │ Extraction (NEW)     │                                   ││
│  │              │ - VB.NET/ASP scan    │                                   ││
│  │              │ - SQL procedures     │                                   ││
│  │              │ - Workflow detection │                                   ││
│  │              └──────────────────────┘                                   ││
│  │                          ↓                                              ││
│  │              Miguel receives: 500+ rules, 4 CRUD workflows              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  MIGRATION (Platform Migration)                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 1: Source Analysis → Step 2: Target Design → Step 3: Impact       ││
│  │              ↓                                              ↓           ││
│  │   ┌──────────────────┐                         ┌──────────────────────┐ ││
│  │   │ Extract rules    │                         │ Which rules need     │ ││
│  │   │ from legacy code │                         │ migration?           │ ││
│  │   └──────────────────┘                         │ - authorization      │ ││
│  │                                                │ - validation         │ ││
│  │                                                │ - data_access        │ ││
│  │                                                └──────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  BACKLOG_GENERATION (Code → Stories)                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 1: Code Scan → Step 2: Feature Detection → Step 3: Story Gen      ││
│  │              ↓                                                          ││
│  │   ┌──────────────────────────────────────────────────────────────────┐  ││
│  │   │ Business Rules → User Stories                                     │  ││
│  │   │                                                                   │  ││
│  │   │ WF-001 "Afspraak Plannen"  →  Epic: "Appointment Management"     │  ││
│  │   │   BR-001 authorization     →  Story: "User can schedule if auth" │  ││
│  │   │   BR-015 scheduling        →  Story: "Validate time slot"        │  ││
│  │   │   BR-042 data_access       →  Story: "Save appointment to DB"    │  ││
│  │   └──────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Agent Context Enrichment

Agents ontvangen business rule context in hun prompts:

```python
# Example: Miguel agent receives rule context for BROWN_PAPER
miguel_context = {
    "project": "HCI-CRS",
    "business_rules": {
        "total": 564,
        "by_type": {
            "validation": 236,
            "scheduling": 93,
            "branching": 83,
            "authorization": 4,
            # ...
        }
    },
    "workflows_detected": [
        {
            "id": "WF-001",
            "name": "Afspraak Plannen",
            "rules_count": 6,
            "complexity": "high"
        },
        # ...
    ],
    "migration_impact": {
        "rules_requiring_rewrite": 45,
        "rules_portable": 519,
        "high_risk_rules": 12
    }
}
```

---

## 5. Epic-Feature-Story-Rule Traceability Model

### Concept

Business rules moeten traceerbaar zijn naar epics, features en user stories. Dit maakt het mogelijk om:
- **Impact analyse**: Welke stories worden geraakt als een rule wijzigt?
- **Compliance**: Aantonen dat alle business rules getest zijn
- **Migration planning**: Welke rules moeten mee naar het nieuwe systeem?
- **Documentatie**: Alles bij elkaar lezen in context

### Hiërarchie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EPIC (EP-001)                                                              │
│  "Agenda Management"                                                        │
│                                                                             │
│  ├── FEATURE (FT-001)                                                       │
│  │   "Afspraak Plannen"                                                     │
│  │   │                                                                      │
│  │   ├── USER STORY (US-001)                                                │
│  │   │   "Als hulpverlener wil ik een afspraak plannen..."                 │
│  │   │   │                                                                  │
│  │   │   ├── BUSINESS RULE (BR-001) ─── authorization                      │
│  │   │   ├── BUSINESS RULE (BR-002) ─── authorization                      │
│  │   │   ├── BUSINESS RULE (BR-015) ─── scheduling                         │
│  │   │   ├── BUSINESS RULE (BR-042) ─── data_access                        │
│  │   │   └── BUSINESS RULE (BR-050) ─── data_access                        │
│  │   │                                                                      │
│  │   └── USER STORY (US-002)                                                │
│  │       "Als hulpverlener wil ik een foutmelding zien..."                 │
│  │       │                                                                  │
│  │       ├── BUSINESS RULE (BR-042) ─── (hergebruik)                       │
│  │       └── BUSINESS RULE (BR-043) ─── error_handling                     │
│  │                                                                          │
│  ├── FEATURE (FT-002)                                                       │
│  │   "Afspraak Wijzigen"                                                    │
│  │   └── ...                                                                │
│  │                                                                          │
│  └── FEATURE (FT-003)                                                       │
│      "Afspraak Verwijderen"                                                 │
│      └── ...                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Voorbeeld: Complete Leesbare View

```yaml
# ═══════════════════════════════════════════════════════════════════════════
# EPIC: EP-001 - Agenda Management
# ═══════════════════════════════════════════════════════════════════════════
epic:
  id: EP-001
  name: Agenda Management
  description: "Complete beheer van afspraken in de hulpverlener agenda"
  business_value: "Efficiënte planning van client-contactmomenten"
  entities: [Afspraak, Hulpverlener, Client, Agenda]
  source_files:
    - /opt/projecten/hci-crs/src/EPD/WEB/Tabellen/Afspraak.asp
    - /opt/projecten/hci-crs/src/EPD/WEB/Agenda2/Default.aspx.vb

  features:
    # ═══════════════════════════════════════════════════════════════════════
    - id: FT-001
      name: Afspraak Plannen
      description: "Nieuwe afspraak aanmaken in de agenda"
      workflow: WF-001

      user_stories:
        # ───────────────────────────────────────────────────────────────────
        - id: US-001
          title: "Afspraak inplannen"
          as_a: "hulpverlener"
          i_want: "een afspraak kunnen plannen"
          so_that: "ik mijn agenda kan beheren"

          acceptance_criteria:
            - "Gebruiker ziet beschikbare tijdslots"
            - "Systeem valideert dat tijdslot niet bezet is"
            - "Afspraak wordt opgeslagen na bevestiging"

          business_rules:
            - id: BR-001
              type: authorization
              condition: "intCanAdd = 1"
              natural_language: "Gebruiker moet INSERT rechten hebben op taAfspraak"
              source: "Afspraak.asp:1166"
              code_snippet: |
                if intCanAdd=0 then
                    strError="U heeft geen rechten om gegevens in te voeren"
                end if

            - id: BR-002
              type: authorization
              condition: "HasHulpverlenerAccess(hvID)"
              natural_language: "Gebruiker moet toegang hebben tot de hulpverlener"
              source: "Afspraak.asp:1125"

            - id: BR-015
              type: scheduling
              condition: "StartTime < EndTime"
              natural_language: "Starttijd moet voor eindtijd liggen"
              source: "Default.aspx.vb:234"
              validation_message: "Eindtijd moet na starttijd liggen"

            - id: BR-042
              type: data_access
              condition: "NOT EXISTS(SELECT * FROM taAfspraak WHERE overlap)"
              natural_language: "Tijdslot mag niet overlappen met bestaande afspraken"
              source: "Afspraak.asp:3174"

            - id: BR-050
              type: data_access
              action: "INSERT INTO taAfspraak"
              natural_language: "Afspraak opslaan in database"
              source: "Afspraak.asp:5230-5231"

          test_cases: [TC-001, TC-002, TC-003]
          screens: [SCR-AGENDA-NEW]

    # ═══════════════════════════════════════════════════════════════════════
    - id: FT-002
      name: Afspraak Wijzigen
      description: "Bestaande afspraak aanpassen"
      workflow: WF-003

      user_stories:
        - id: US-003
          title: "Afspraak verplaatsen"
          as_a: "hulpverlener"
          i_want: "een afspraak naar een ander tijdstip verplaatsen"
          so_that: "ik flexibel kan plannen"

          preconditions:
            - "Afspraak is niet verwerkt (status ≠ VERWERKT)"
            - "Gebruiker heeft EDIT rechten"

          business_rules:
            - id: BR-070
              type: authorization
              condition: "intCanEdit = 1"
              natural_language: "Gebruiker moet EDIT rechten hebben"
              source: "Afspraak.asp:1131"

            - id: BR-073
              type: workflow
              condition: "Status <> 'VERWERKT'"
              natural_language: "Verwerkte afspraken kunnen niet worden gewijzigd"
              source: "Afspraak.asp:5936"
              rationale: "Facturatieprocessen zijn al gestart"

            - id: BR-081
              type: data_access
              action: "UPDATE taAfspraak SET ..."
              natural_language: "Wijzigingen opslaan in database"
              source: "Afspraak.asp:5232-5234"
```

### Traceability Matrix

Voor rapportage, compliance en impact analyse:

| Epic | Feature | User Story | Business Rule | Type | Source | Test |
|------|---------|------------|---------------|------|--------|------|
| EP-001 Agenda | FT-001 Plannen | US-001 Inplannen | BR-001 | authorization | Afspraak.asp:1166 | TC-001 |
| EP-001 Agenda | FT-001 Plannen | US-001 Inplannen | BR-002 | authorization | Afspraak.asp:1125 | TC-001 |
| EP-001 Agenda | FT-001 Plannen | US-001 Inplannen | BR-015 | scheduling | Default.aspx.vb:234 | TC-002 |
| EP-001 Agenda | FT-001 Plannen | US-001 Inplannen | BR-042 | data_access | Afspraak.asp:3174 | TC-003 |
| EP-001 Agenda | FT-001 Plannen | US-002 Foutmelding | BR-042 | data_access | Afspraak.asp:3174 | TC-004 |
| EP-001 Agenda | FT-001 Plannen | US-002 Foutmelding | BR-043 | error_handling | Afspraak.asp:3180 | TC-004 |
| EP-001 Agenda | FT-002 Wijzigen | US-003 Verplaatsen | BR-070 | authorization | Afspraak.asp:1131 | TC-005 |
| EP-001 Agenda | FT-002 Wijzigen | US-003 Verplaatsen | BR-073 | workflow | Afspraak.asp:5936 | TC-006 |
| EP-001 Agenda | FT-002 Wijzigen | US-003 Verplaatsen | BR-081 | data_access | Afspraak.asp:5232 | TC-007 |

### Use Cases voor Traceability

| Vraag | Query | Antwoord |
|-------|-------|----------|
| "Welke business rules horen bij plannen?" | `rules WHERE story.feature = 'FT-001'` | BR-001, BR-002, BR-015, BR-042, BR-050 |
| "Welke stories geraakt als BR-042 wijzigt?" | `stories WHERE rules CONTAINS 'BR-042'` | US-001, US-002 |
| "Waar zit de autorisatie voor wijzigen?" | `rules WHERE story.feature = 'FT-002' AND type = 'authorization'` | BR-070 → Afspraak.asp:1131 |
| "Welke tests dekken scheduling validatie?" | `tests WHERE rules.type = 'scheduling'` | TC-002 (via BR-015 → US-001) |
| "Impact als we taAfspraak hernoemen?" | `rules WHERE source LIKE '%taAfspraak%'` | BR-050, BR-081 moeten aangepast |

---

## 6. Database Schema

### Core Tables

```sql
-- Business Rules table
CREATE TABLE business_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    rule_id VARCHAR(20) NOT NULL,           -- "BR-001"
    rule_type VARCHAR(50) NOT NULL,         -- validation, authorization, etc.
    condition TEXT NOT NULL,
    action TEXT,
    source_file VARCHAR(500) NOT NULL,
    source_line_start INTEGER,
    source_line_end INTEGER,
    confidence FLOAT DEFAULT 0.8,
    natural_language TEXT,
    variables_involved JSONB DEFAULT '[]',
    related_entities JSONB DEFAULT '[]',
    language VARCHAR(20),                   -- python, vbnet, asp, sql
    created_at TIMESTAMP DEFAULT NOW()
);

-- Rule Workflows table
CREATE TABLE rule_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    workflow_id VARCHAR(20) NOT NULL,       -- "WF-001"
    name VARCHAR(200) NOT NULL,             -- "Afspraak Plannen"
    description TEXT,
    trigger_description TEXT,
    entities JSONB DEFAULT '[]',
    success_outcome TEXT,
    failure_outcomes JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workflow-Rule junction table
CREATE TABLE workflow_rule_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES rule_workflows(id),
    rule_id UUID REFERENCES business_rules(id),
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100),
    step_type VARCHAR(50),                  -- authorization, validation, etc.
    check_description TEXT,
    fail_action TEXT,
    UNIQUE(workflow_id, step_number)
);

-- Indexes
CREATE INDEX idx_rules_project ON business_rules(project_id);
CREATE INDEX idx_rules_type ON business_rules(rule_type);
CREATE INDEX idx_rules_file ON business_rules(source_file);
CREATE INDEX idx_workflows_project ON rule_workflows(project_id);
```

### Traceability Tables

```sql
-- Epics table
CREATE TABLE epics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    epic_id VARCHAR(20) NOT NULL,              -- "EP-001"
    name VARCHAR(200) NOT NULL,                -- "Agenda Management"
    description TEXT,
    business_value TEXT,
    entities JSONB DEFAULT '[]',               -- ["Afspraak", "Hulpverlener", "Client"]
    source_files JSONB DEFAULT '[]',           -- bronbestanden
    status VARCHAR(50) DEFAULT 'draft',        -- draft, active, completed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, epic_id)
);

-- Features table
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_id UUID REFERENCES epics(id) ON DELETE CASCADE,
    feature_id VARCHAR(20) NOT NULL,           -- "FT-001"
    name VARCHAR(200) NOT NULL,                -- "Afspraak Plannen"
    description TEXT,
    workflow_id UUID REFERENCES rule_workflows(id),  -- Link naar WF-001
    priority VARCHAR(20) DEFAULT 'medium',     -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(epic_id, feature_id)
);

-- User Stories table
CREATE TABLE user_stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_id UUID REFERENCES features(id) ON DELETE CASCADE,
    story_id VARCHAR(20) NOT NULL,             -- "US-001"
    title VARCHAR(200) NOT NULL,               -- "Afspraak inplannen"
    as_a VARCHAR(100),                         -- "hulpverlener"
    i_want TEXT,                               -- "een afspraak kunnen plannen"
    so_that TEXT,                              -- "ik mijn agenda kan beheren"
    acceptance_criteria JSONB DEFAULT '[]',    -- ["Systeem valideert...", ...]
    preconditions JSONB DEFAULT '[]',
    test_cases JSONB DEFAULT '[]',             -- ["TC-001", "TC-002"]
    screens JSONB DEFAULT '[]',                -- ["SCR-AGENDA-NEW"]
    story_points INTEGER,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'draft',        -- draft, ready, in_progress, done
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(feature_id, story_id)
);

-- Story-BusinessRule junction table (N:M relationship)
CREATE TABLE story_business_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID REFERENCES user_stories(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES business_rules(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,          -- Primaire rule voor deze story
    coverage_type VARCHAR(50),                 -- full, partial, inherited
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(story_id, rule_id)
);

-- Traceability indexes
CREATE INDEX idx_epics_project ON epics(project_id);
CREATE INDEX idx_features_epic ON features(epic_id);
CREATE INDEX idx_stories_feature ON user_stories(feature_id);
CREATE INDEX idx_story_rules_story ON story_business_rules(story_id);
CREATE INDEX idx_story_rules_rule ON story_business_rules(rule_id);

-- Traceability views voor queries
CREATE VIEW v_traceability_matrix AS
SELECT
    e.epic_id,
    e.name AS epic_name,
    f.feature_id,
    f.name AS feature_name,
    s.story_id,
    s.title AS story_title,
    r.rule_id,
    r.rule_type,
    r.source_file,
    r.source_line_start,
    r.natural_language AS rule_description
FROM epics e
JOIN features f ON f.epic_id = e.id
JOIN user_stories s ON s.feature_id = f.id
JOIN story_business_rules sbr ON sbr.story_id = s.id
JOIN business_rules r ON r.id = sbr.rule_id
ORDER BY e.epic_id, f.feature_id, s.story_id, r.rule_id;

-- Impact analysis view: welke stories geraakt als rule wijzigt
CREATE VIEW v_rule_impact AS
SELECT
    r.rule_id,
    r.rule_type,
    r.natural_language,
    array_agg(DISTINCT s.story_id) AS impacted_stories,
    array_agg(DISTINCT f.feature_id) AS impacted_features,
    array_agg(DISTINCT e.epic_id) AS impacted_epics
FROM business_rules r
JOIN story_business_rules sbr ON sbr.rule_id = r.id
JOIN user_stories s ON s.id = sbr.story_id
JOIN features f ON f.id = s.feature_id
JOIN epics e ON e.id = f.epic_id
GROUP BY r.id, r.rule_id, r.rule_type, r.natural_language;
```

---

## 7. API Endpoints

```
POST   /api/business-rules/extract
       Body: { project_id, path, languages: ["vbnet", "asp", "sql"] }
       Returns: { rules: [...], statistics: {...} }

GET    /api/business-rules/{project_id}
       Returns: List of all rules for project

GET    /api/business-rules/{project_id}/by-type/{type}
       Returns: Rules filtered by type

POST   /api/business-rules/correlate
       Body: { project_id, correlation_strategy: "entity|callgraph|controlflow" }
       Returns: { workflows: [...] }

GET    /api/workflows/{project_id}
       Returns: List of detected workflows

GET    /api/workflows/{workflow_id}/diagram
       Returns: Mermaid diagram of workflow

# Traceability Endpoints
GET    /api/epics/{project_id}
       Returns: List of all epics for project

GET    /api/epics/{epic_id}/features
       Returns: Features for epic with story counts

GET    /api/features/{feature_id}/stories
       Returns: User stories with linked business rules

GET    /api/stories/{story_id}/rules
       Returns: All business rules linked to story

GET    /api/rules/{rule_id}/impact
       Returns: Impact analysis (stories, features, epics affected)

GET    /api/traceability/{project_id}/matrix
       Returns: Complete traceability matrix (Excel/CSV export supported)

POST   /api/traceability/link
       Body: { story_id, rule_id, is_primary?, coverage_type?, notes? }
       Returns: Created link

DELETE /api/traceability/link/{story_id}/{rule_id}
       Returns: Deleted link confirmation

GET    /api/traceability/search
       Query: ?project_id=X&rule_type=authorization&feature=FT-001
       Returns: Filtered traceability results
```

---

## 8. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| VB.NET rule detection | 0 | 90%+ of manual count |
| ASP rule detection | 0 | 85%+ of manual count |
| SQL rule detection | N/A | 80%+ of manual count |
| Workflow correlation accuracy | N/A | 75%+ correct groupings |
| False positive rate | N/A | <15% |

---

## 9. Dependencies

| Component | Purpose | Status |
|-----------|---------|--------|
| `static_analysis/` | Base infrastructure | ✅ Exists |
| `extraction/` | NFR detection | ✅ Exists |
| Tree-sitter | Multi-language parsing (optional) | 📋 To evaluate |
| Mermaid.js | Workflow diagrams | ✅ Available |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex patterns miss rules | Medium | Combine with AST where possible |
| False positives in correlation | Medium | Add confidence scores, manual review |
| Complex stored procedures | High | Start with simple patterns, iterate |
| Language edge cases | Low | Comprehensive test suite |

---

## Related Documents

- [ROADMAP.md](../../ROADMAP.md) - Project roadmap
- [business_rule_extractor.py](../../backend/app/services/static_analysis/business_rule_extractor.py) - Current implementation
- [HCI-CRS Agenda Analysis](../../backend/tests/services/extraction/analyze_hci_agenda.py) - Analysis script

---

**Next Steps:**
1. Review and approve this specification
2. Add to ROADMAP.md as Week 111-113 priority
3. Create implementation tickets
4. Start with Phase 1: Core Extractors
