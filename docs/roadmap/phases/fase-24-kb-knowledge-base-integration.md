# Fase 24-KB: Knowledge Base Integration (Week 159-165)

**Goal:** Integreer externe bug/error/pattern repositories in ChromaDB kennisbank voor AI agent context
**Status:** PLANNED
**Priority:** HIGH (verbetert agent accuracy en pattern detection)
**Effort:** ~80 uur (5 KB items)
**Dependencies:** Fase 23 (Context Engineering), ChromaDB infrastructure

---

## Executive Summary

Integratie van 5 externe kennisbronnen in de MarQed ChromaDB vectordatabase:
- **KB1:** Famous-Bugs - Historische software failures
- **KB2:** Python-Errors - 13 categorieën Python errors
- **KB3:** Logical Errors C# - .NET pattern voorbeelden
- **KB4:** Logical Errors C/Python - Multi-language voorbeelden
- **KB5:** Post-Mortems - 11.9k⭐ production outage patterns

**Doel:** AI agents (Betty, Diana, Marcus) krijgen contextuele kennis over bekende bugs, errors en anti-patterns voor betere code analyse.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE BASE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   GitHub    │  │   GitHub    │  │   GitHub    │  │   GitHub    │    │
│  │ famous-bugs │  │python-errors│  │logicalErrors│  │post-mortems │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│         ▼                ▼                ▼                ▼            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    KB Ingestion Pipeline                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │ GitHub   │  │ Markdown │  │ Code     │  │ Metadata         │ │   │
│  │  │ Fetcher  │→ │ Parser   │→ │ Extractor│→ │ Enricher (CWE)   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     ChromaDB Collections                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │   │
│  │  │ bug_patterns    │  │ error_reference │  │ postmortem_     │  │   │
│  │  │ (KB1, KB3, KB4) │  │ (KB2)           │  │ knowledge (KB5) │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Context Engineering (Fase 23) Integration           │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │   │
│  │  │  Betty    │  │  Diana    │  │  Marcus   │  │CWE Scanner│    │   │
│  │  │ (Quality) │  │(Security) │  │  (Arch)   │  │           │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## New ChromaDB Collections

### Collection 1: `bug_patterns`
**Purpose:** Historische bugs, logical errors, code voorbeelden
**Sources:** KB1 (famous-bugs), KB3 (logicalErrors), KB4 (correctLogicalErrors)

```python
{
    "name": "bug_patterns",
    "metadata": {
        "description": "Historical bugs, logical errors, and anti-patterns",
        "hnsw:space": "cosine"
    },
    "document_schema": {
        "id": "kb1-famous-bugs-ariane5-001",
        "content": "Ariane 5 rocket explosion caused by integer overflow...",
        "metadata": {
            "source": "famous-bugs",           # KB source
            "category": "integer_overflow",     # Bug category
            "language": "ada",                  # Programming language
            "severity": "critical",             # Impact severity
            "cwe_ids": ["CWE-190"],             # Mapped CWE IDs
            "year": 1996,                       # When it occurred
            "impact": "$500M loss",             # Business impact
            "root_cause": "64-bit to 16-bit conversion",
            "prevention": "Range checking, safe integer operations",
            "tags": ["overflow", "type-conversion", "aerospace"]
        }
    }
}
```

### Collection 2: `error_reference`
**Purpose:** Gestructureerde error documentatie per taal
**Sources:** KB2 (python-errors)

```python
{
    "name": "error_reference",
    "metadata": {
        "description": "Structured error documentation by language",
        "hnsw:space": "cosine"
    },
    "document_schema": {
        "id": "kb2-python-TypeError-001",
        "content": "TypeError occurs when an operation is applied to an object of inappropriate type...",
        "metadata": {
            "source": "python-errors",
            "language": "python",
            "error_type": "TypeError",
            "category": "type_errors",
            "common_causes": ["wrong argument type", "incompatible operations"],
            "solution_patterns": ["type checking", "isinstance()", "type hints"],
            "related_errors": ["AttributeError", "ValueError"],
            "frequency": "very_common"
        }
    }
}
```

### Collection 3: `postmortem_knowledge`
**Purpose:** Production incident patterns en lessons learned
**Sources:** KB5 (danluu/post-mortems)

```python
{
    "name": "postmortem_knowledge",
    "metadata": {
        "description": "Production incident patterns and lessons learned",
        "hnsw:space": "cosine"
    },
    "document_schema": {
        "id": "kb5-postmortem-gitlab-2017-001",
        "content": "GitLab database deletion incident: 300GB data loss, 18-hour outage...",
        "metadata": {
            "source": "post-mortems",
            "company": "GitLab",
            "year": 2017,
            "incident_type": "data_loss",
            "category": "database",
            "duration_hours": 18,
            "root_cause": "accidental deletion during maintenance",
            "contributing_factors": ["unclear documentation", "fatigue", "missing backups"],
            "prevention_measures": ["automated backups", "deletion safeguards", "runbook clarity"],
            "impact_level": "severe",
            "tags": ["database", "backup", "human-error", "postgresql"]
        }
    }
}
```

---

## Implementation Phases

### Phase KB.1: Infrastructure & Pipeline (Week 159) - 16 uur

| Task | Description | Effort |
|------|-------------|--------|
| **KB.1.1** | Create `KnowledgeBaseIngestionService` | 4h |
| **KB.1.2** | Add 3 new ChromaDB collections | 2h |
| **KB.1.3** | Create GitHub content fetcher | 4h |
| **KB.1.4** | Create markdown parser with metadata extraction | 4h |
| **KB.1.5** | Unit tests for pipeline | 2h |

**Deliverables:**
- `backend/app/services/knowledge_base/kb_ingestion_service.py`
- `backend/app/services/knowledge_base/github_fetcher.py`
- `backend/app/services/knowledge_base/markdown_parser.py`
- `backend/app/services/knowledge_base/metadata_enricher.py`
- Updated `chroma_service.py` with 3 new collections

### Phase KB.2: KB1 - Famous-Bugs Integration (Week 160) - 12 uur

| Task | Description | Effort |
|------|-------------|--------|
| **KB.2.1** | Clone/fetch famous-bugs repository | 1h |
| **KB.2.2** | Parse README.md structure (Problems, Outages, Bugs, AI) | 4h |
| **KB.2.3** | Extract individual bug entries with metadata | 3h |
| **KB.2.4** | Map to CWE IDs where applicable | 2h |
| **KB.2.5** | Ingest into `bug_patterns` collection | 1h |
| **KB.2.6** | Integration tests | 1h |

**Source Structure (famous-bugs):**
```
README.md
├── Problems
│   ├── Thundering Herd Problem
│   ├── N+1 Query Problem
│   ├── Single Point of Failure
│   └── Year 2000 Problem
├── Outages and Hacks
│   ├── YouTube 32-bit overflow
│   ├── GitLab database deletion
│   ├── Facebook Oct 2021
│   └── Stack Overflow ReDoS
├── Bugs and Worms
│   ├── First computer bug (1947)
│   ├── Ariane 5 explosion
│   ├── Mars Climate Orbiter
│   ├── Morris Worm
│   └── Log4Shell
└── AI
    └── Microsoft Tay
```

**CWE Mapping:**
| Bug | CWE |
|-----|-----|
| Integer overflow (YouTube, Ariane 5) | CWE-190 |
| SQL Injection patterns | CWE-89 |
| ReDoS (Stack Overflow) | CWE-1333 |
| Log4Shell | CWE-917 |
| N+1 Query | CWE-400 (performance) |

### Phase KB.3: KB2 - Python-Errors Integration (Week 161) - 12 uur

| Task | Description | Effort |
|------|-------------|--------|
| **KB.3.1** | Fetch python-errors repository | 1h |
| **KB.3.2** | Parse 13 error category folders | 4h |
| **KB.3.3** | Extract error descriptions, causes, solutions | 3h |
| **KB.3.4** | Create error relationship graph | 2h |
| **KB.3.5** | Ingest into `error_reference` collection | 1h |
| **KB.3.6** | Integration tests | 1h |

**Error Categories:**
```
python-errors/
├── syntax_errors/
│   ├── IndentationError.md
│   ├── SyntaxError.md
│   └── NameError.md
├── type_errors/
│   ├── TypeError.md
│   └── AttributeError.md
├── value_errors/
│   ├── ValueError.md
│   └── IndexError.md
├── import_errors/
│   ├── ImportError.md
│   └── ModuleNotFoundError.md
├── io_errors/
│   ├── FileNotFoundError.md
│   └── IOError.md
└── runtime_errors/
    ├── ZeroDivisionError.md
    └── OverflowError.md
```

### Phase KB.4: KB3 & KB4 - Logical Errors Integration (Week 162) - 16 uur

| Task | Description | Effort |
|------|-------------|--------|
| **KB.4.1** | Fetch logicalErrors (C#) repository | 1h |
| **KB.4.2** | Parse 5 progressive modules | 3h |
| **KB.4.3** | Extract C# code examples with errors | 3h |
| **KB.4.4** | Fetch correctLogicalErrors (C/Python) | 1h |
| **KB.4.5** | Parse src/, trials/, sample files | 3h |
| **KB.4.6** | Extract multi-language code examples | 3h |
| **KB.4.7** | Ingest into `bug_patterns` collection | 1h |
| **KB.4.8** | Integration tests | 1h |

**Code Example Schema:**
```python
{
    "id": "kb3-csharp-logical-001",
    "content": "// Off-by-one error example\nfor(int i = 0; i <= array.Length; i++) { ... }",
    "metadata": {
        "source": "logicalErrors",
        "language": "csharp",
        "error_type": "off_by_one",
        "module": "bledyLogiczne2",
        "difficulty": "intermediate",
        "correct_version": "for(int i = 0; i < array.Length; i++) { ... }",
        "explanation": "Array index goes out of bounds when i equals Length"
    }
}
```

### Phase KB.5: KB5 - Post-Mortems Integration (Week 163-164) - 20 uur

| Task | Description | Effort |
|------|-------------|--------|
| **KB.5.1** | Fetch danluu/post-mortems repository | 1h |
| **KB.5.2** | Parse categorized incident list | 4h |
| **KB.5.3** | Fetch linked post-mortem documents | 6h |
| **KB.5.4** | Extract incident metadata (company, date, root cause) | 4h |
| **KB.5.5** | Categorize by incident type | 2h |
| **KB.5.6** | Ingest into `postmortem_knowledge` collection | 2h |
| **KB.5.7** | Integration tests | 1h |

**Incident Categories:**
| Category | Examples | Count |
|----------|----------|-------|
| Config Errors | AWS S3 outage, Facebook 2021 | ~25% |
| Database | GitLab deletion, MongoDB corruption | ~15% |
| Network | Cloudflare, DNS failures | ~15% |
| Hardware | Power failures, disk corruption | ~10% |
| Time-related | Leap seconds, Y2K variants | ~5% |
| Security | Breaches, DDoS | ~10% |
| Human Error | Fat-finger, wrong commands | ~20% |

### Phase KB.6: Agent Integration & API (Week 165) - 8 uur

| Task | Description | Effort |
|------|-------------|--------|
| **KB.6.1** | Create `KnowledgeBaseQueryService` | 2h |
| **KB.6.2** | Integrate with Context Engineering (Fase 23) | 2h |
| **KB.6.3** | Add API endpoints for KB queries | 2h |
| **KB.6.4** | Update agent prompts with KB context | 1h |
| **KB.6.5** | End-to-end tests | 1h |

---

## File Structure

```
backend/app/services/knowledge_base/
├── __init__.py
├── kb_ingestion_service.py      # Main ingestion orchestrator
├── github_fetcher.py            # GitHub API/raw content fetcher
├── markdown_parser.py           # Markdown to structured data parser
├── code_extractor.py            # Code block extraction
├── metadata_enricher.py         # CWE mapping, categorization
├── kb_query_service.py          # Query interface for agents
└── parsers/
    ├── __init__.py
    ├── famous_bugs_parser.py    # KB1 specific parser
    ├── python_errors_parser.py  # KB2 specific parser
    ├── logical_errors_parser.py # KB3/KB4 parser
    └── postmortem_parser.py     # KB5 specific parser

backend/app/api/
└── knowledge_base.py            # New API routes

backend/tests/unit/knowledge_base/
├── test_kb_ingestion_service.py
├── test_github_fetcher.py
├── test_markdown_parser.py
└── test_parsers/
    ├── test_famous_bugs_parser.py
    ├── test_python_errors_parser.py
    ├── test_logical_errors_parser.py
    └── test_postmortem_parser.py
```

---

## API Endpoints

```python
# New API routes in backend/app/api/knowledge_base.py

# Ingestion
POST /api/v1/knowledge-base/ingest/{source}
# source: famous-bugs, python-errors, logical-errors-csharp, logical-errors-multi, post-mortems

# Query
POST /api/v1/knowledge-base/query
{
    "query": "integer overflow prevention",
    "collections": ["bug_patterns", "error_reference"],
    "filters": {
        "language": "python",
        "severity": "critical"
    },
    "top_k": 10
}

# Statistics
GET /api/v1/knowledge-base/stats

# Agent context (used by Context Engineering)
GET /api/v1/knowledge-base/agent-context/{agent_name}
# Returns relevant KB context for specific agent (Betty, Diana, Marcus)
```

---

## Agent Integration

### Betty (Code Quality Agent)
**Receives context from:**
- `bug_patterns`: Code smells, anti-patterns, N+1 queries
- `error_reference`: Common error patterns per language
- `postmortem_knowledge`: Quality-related incidents

**Example prompt augmentation:**
```
When analyzing code quality, consider these known anti-patterns:
- N+1 Query Problem: {context from KB1}
- Common Python TypeError causes: {context from KB2}
- Quality-related incidents: {context from KB5}
```

### Diana (Security Agent)
**Receives context from:**
- `bug_patterns`: Security vulnerabilities (Log4Shell, injection patterns)
- `postmortem_knowledge`: Security breaches, DDoS incidents

**Example prompt augmentation:**
```
When analyzing security, be aware of these historical vulnerabilities:
- Log4Shell (CWE-917): {context from KB1}
- SQL Injection patterns: {context from KB1}
- Security incident patterns: {context from KB5}
```

### Marcus (Architecture Agent)
**Receives context from:**
- `bug_patterns`: Architectural failures (Ariane 5, single point of failure)
- `postmortem_knowledge`: Infrastructure outages, scaling failures

**Example prompt augmentation:**
```
When reviewing architecture, consider these historical failures:
- Single Point of Failure: {context from KB1}
- Thundering Herd Problem: {context from KB1}
- Infrastructure incidents: {context from KB5}
```

---

## Data Volume Estimates

| KB | Source | Est. Documents | Est. Chunks | Storage |
|----|--------|---------------|-------------|---------|
| KB1 | famous-bugs | ~50 entries | ~200 | ~1 MB |
| KB2 | python-errors | ~13 errors × 3 sections | ~100 | ~0.5 MB |
| KB3 | logicalErrors | ~50 C# examples | ~150 | ~0.5 MB |
| KB4 | correctLogicalErrors | ~100 C/Python examples | ~300 | ~1 MB |
| KB5 | post-mortems | ~200 incidents | ~1000 | ~5 MB |
| **Total** | | **~400 entries** | **~1750 chunks** | **~8 MB** |

---

## Testing Strategy

### Unit Tests (~40 tests)
- GitHub fetcher: mock responses, rate limiting
- Markdown parser: various formats, edge cases
- Code extractor: multi-language support
- Metadata enricher: CWE mapping accuracy

### Integration Tests (~20 tests)
- Full ingestion pipeline per KB source
- ChromaDB collection operations
- Query accuracy and relevance

### End-to-End Tests (~10 tests)
- Agent context retrieval
- API endpoint responses
- Performance benchmarks

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Documents ingested | >400 |
| Query latency (p95) | <200ms |
| Agent context relevance | >80% relevant results |
| CWE mapping coverage | >50% of security bugs |
| Test coverage | >90% |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub rate limiting | Ingestion fails | Use raw.githubusercontent.com, caching |
| Large post-mortems | Memory issues | Streaming parser, chunking |
| Stale content | Outdated knowledge | Periodic re-ingestion (monthly) |
| Low query relevance | Poor agent context | Tuning embeddings, metadata filters |

---

## Timeline

```
Week 159: KB.1 - Infrastructure & Pipeline
Week 160: KB.2 - Famous-Bugs (KB1)
Week 161: KB.3 - Python-Errors (KB2)
Week 162: KB.4 - Logical Errors (KB3, KB4)
Week 163-164: KB.5 - Post-Mortems (KB5)
Week 165: KB.6 - Agent Integration & API
```

**Total Effort:** ~80 uur (2 weken full-time equivalent)

---

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Fase 23 - Context Engineering](fase-23-context-engineering.md)
- [famous-bugs](https://github.com/zeeneddie/famous-bugs)
- [python-errors](https://github.com/zeeneddie/python-errors)
- [logicalErrors](https://github.com/zeeneddie/logicalErrors)
- [correctLogicalErrors](https://github.com/zeeneddie/correctLogicalErrors)
- [danluu/post-mortems](https://github.com/danluu/post-mortems)
