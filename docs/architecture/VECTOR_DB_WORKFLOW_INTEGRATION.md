# Vector DB Workflow Integration Analyse

**Datum**: 2025-12-01
**Doel**: Identificeer waar de HCI-CRS ChromaDB kennis kan worden geïntegreerd in bestaande workflows

---

## 1. Huidige Situatie

### Geïndexeerde Data
- **48 markdown bestanden** in ChromaDB
- **254 chunks** met embeddings (all-MiniLM-L6-v2)
- **Document types**: project_overview, architecture, epic, feature, user_story, task

### API Endpoints Beschikbaar
| Endpoint | Doel |
|----------|------|
| `POST /api/hci-crs/query` | Semantische kennis query |
| `GET /api/hci-crs/query/simple` | Quick search |
| `POST /api/hci-crs/code-location` | Code locatie lookup |
| `POST /api/hci-crs/agent-context` | Context voor AI agents |
| `GET /api/hci-crs/stats` | Index statistieken |

---

## 2. Workflow Integratie Mogelijkheden

### 2.1 Brown Paper Workflow (Hoge Prioriteit)

**Huidige service**: `brown_paper_service.py`
**Doel**: Reverse engineering van bestaande projecten

**Integratie punt**:
- Bij start van brown paper sessie, automatisch relevante docs ophalen
- Context pre-populeren met architecture info
- Code locations direct beschikbaar stellen

```python
# In BrownPaperService
async def start_session(self, project_id: int, scope: str):
    # NIEUW: Haal project context op uit vector DB
    context = await hci_crs_api.get_agent_context(
        task_description=scope,
        include_architecture=True,
        include_code_locations=True
    )
    # Pre-populate session met relevante docs
    session.architecture_context = context.architecture_context
    session.code_locations = context.code_locations
```

**Impact**: Agents hebben direct relevante context, minder hallucinatie

---

### 2.2 Spec Review Workflow (Hoge Prioriteit)

**Huidige service**: `spec_review_service.py`
**Agents**: Quinn (Quality), Felix (Architecture)

**Integratie punt**:
- Quinn raadpleegt vector DB voor bestaande acceptance criteria
- Felix haalt architecture patterns op uit docs
- Vergelijk nieuwe specs met bestaande user stories

```python
# In SpecReviewService
async def review_specification(self, spec_content: str):
    # NIEUW: Zoek vergelijkbare user stories
    similar = await hci_crs_api.query({
        "query": spec_content,
        "document_types": ["user_story", "feature"],
        "top_k": 5
    })
    # Voeg toe aan Quinn's context
    quinn_context["similar_specs"] = similar.results
```

**Impact**: Consistentere specs, geen duplicate user stories

---

### 2.3 Task Generation Workflow (Medium Prioriteit)

**Huidige service**: `task_generation_service.py`
**Bron**: `backend/app/services/week11/`

**Integratie punt**:
- Bij task generation, referentie naar bestaande task patterns
- Automatisch code locations toevoegen aan gegenereerde tasks
- Story point schatting baseren op vergelijkbare tasks

```python
# In TaskGenerationService
async def generate_tasks_for_story(self, story_id: int, description: str):
    # NIEUW: Vind vergelijkbare stories met hun tasks
    similar = await hci_crs_api.query({
        "query": description,
        "document_types": ["user_story", "task"],
        "top_k": 10
    })
    # Extract task patterns
    task_patterns = extract_task_patterns(similar.results)
```

**Impact**: Betere task breakdown, realistischere schattingen

---

### 2.4 Agent Evolution Workflow (Medium Prioriteit)

**Huidige service**: `agent_evolution_service.py`
**Focus**: Self-improvement van agents

**Integratie punt**:
- Agents leren van gedocumenteerde patterns
- Architecture kennis als "ground truth" voor validatie
- Track welke docs leiden tot succesvolle task completion

```python
# In AgentEvolutionService
async def store_successful_pattern(self, agent: str, task_id: int):
    # NIEUW: Link successful pattern to relevant docs
    relevant_docs = await hci_crs_api.query({
        "query": task.description,
        "top_k": 3
    })
    # Store relationship voor future learning
    await store_doc_task_correlation(
        doc_ids=relevant_docs.doc_ids,
        task_success=True
    )
```

**Impact**: Agents leren welke docs relevant zijn per task type

---

### 2.5 Estimation Service (Medium Prioriteit)

**Huidige service**: `estimation_history_service.py`
**Focus**: Function Points en Story Points

**Integratie punt**:
- Bij nieuwe schatting, vergelijk met vergelijkbare historische items
- Story points van gemigreerde user stories als referentie
- Function points valideren tegen gedocumenteerde complexity

```python
# In EstimationService
async def estimate_story_points(self, story: str):
    # NIEUW: Vind vergelijkbare stories met bekende SP
    similar = await hci_crs_api.query({
        "query": story,
        "document_types": ["user_story"],
        "top_k": 5
    })
    # Extract SP from similar stories
    reference_points = [
        extract_sp(doc) for doc in similar.results
    ]
    # Use as calibration
```

**Impact**: Betere schatting accuracy door historische referentie

---

### 2.6 LLM Council Workflow (Low Prioriteit - Future)

**Huidige service**: `llm_council_service.py`
**Focus**: Multi-model decision making

**Integratie punt**:
- Council krijgt project context als shared knowledge base
- Alle LLMs hebben dezelfde referentie docs
- Consensus building met gemeenschappelijke ground truth

---

## 3. Implementatie Roadmap

### Week 1: Brown Paper + Spec Review
1. Integreer `hci_crs_knowledge.py` in `brown_paper_service.py`
2. Add context pre-population bij sessie start
3. Test met echte brown paper sessie

### Week 2: Task Generation
1. Connect task generation met vector search
2. Implement task pattern extraction
3. Add code location auto-population

### Week 3: Estimation + Evolution
1. SP/FP referentie lookup
2. Doc-task correlation tracking
3. Agent learning metrics

---

## 4. API Verbeteringen (Backlog)

| Verbetering | Reden | Prioriteit |
|-------------|-------|------------|
| Batch query support | Meerdere queries in 1 call | MEDIUM |
| Metadata filtering fix | ChromaDB compound filter bug | HIGH |
| Incremental embedding | Alleen nieuwe/gewijzigde docs | MEDIUM |
| Cross-project search | Meerdere projecten doorzoeken | LOW |

---

## 5. Metrics voor Succes

| Metric | Target | Meetmethode |
|--------|--------|-------------|
| Context relevance | >80% | User feedback |
| Query latency | <100ms | API monitoring |
| Agent task success | +15% | Before/after comparison |
| Duplicate story detection | 100% | Manual audit |

---

## Conclusie

De vector DB integratie kan significante waarde toevoegen aan:
1. **Brown Paper** - Direct context voor reverse engineering
2. **Spec Review** - Consistentie met bestaande specs
3. **Task Generation** - Betere breakdown patterns
4. **Estimation** - Historische referentie data

**Aanbeveling**: Start met Brown Paper integratie (hoogste ROI).
