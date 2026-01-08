# Human-in-the-Loop Council Architecture

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 55 IN PROGRESS (UI done)
**Last Updated:** 2025-12-17

---

## Overview

Het Human-in-the-Loop Council systeem breidt de LLM Council (Week 52) uit met menselijke validatie en correctie. Dit zorgt voor:

- **Hogere accuraatheid**: LLM consensus (~95%) + Human review = ~99% accuraatheid
- **Transparantie**: Human kan zien wat elke provider bijdroeg
- **Leervermogen**: Human feedback wordt opgeslagen voor toekomstige verbetering

---

## 6-Fase Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HUMAN-IN-THE-LOOP COUNCIL WORKFLOW                   │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ 1. PROVIDER  │ -> │ 2. PEER      │ -> │ 3. ORCHESTR. │              │
│  │    GENERATIE │    │    REVIEW    │    │    SYNTHESE  │              │
│  │              │    │              │    │              │              │
│  │ 3 providers  │    │ Round-robin  │    │ Consensus    │              │
│  │ parallel     │    │ 3x reviews   │    │ document     │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│          │                   │                   │                      │
│          v                   v                   v                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    4. HUMAN REVIEW                           │      │
│  │                                                              │      │
│  │  ☑ Provider A: Correct: [DDD uitleg] [Commands]              │      │
│  │  ☑ Provider B: Correct: [Docker-first] [Pro Tips]            │      │
│  │  ☑ Provider C: Correct: [Dependency direction]               │      │
│  │                                                              │      │
│  │  Conflicten: _______ (human lost op)                         │      │
│  │  Ontbrekend: _______ (human voegt toe)                       │      │
│  │  Nuances: __________ (human corrigeert)                      │      │
│  └──────────────────────────────────────────────────────────────┘      │
│          │                                                              │
│          v                                                              │
│  ┌──────────────┐    ┌──────────────┐                                  │
│  │ 5. FINAL     │ -> │ 6. STORAGE   │                                  │
│  │    SYNTHESE  │    │    & SYNC    │                                  │
│  │              │    │              │                                  │
│  │ LLM verwerkt │    │ MD + DB      │                                  │
│  │ human input  │    │ Git commit   │                                  │
│  └──────────────┘    └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Fase Details

### Fase 1: Provider Generatie

3 providers genereren content parallel:
- **Ollama** (local): qwen2.5-coder, deepseek-r1
- **Claude CLI**: Sonnet (balanced)
- **Codex CLI**: gpt-5.1-codex-max

### Fase 2: Peer Review

Round-robin evaluatie waarbij elke provider de anderen beoordeelt:
- Provider A beoordeelt B en C
- Provider B beoordeelt A en C
- Provider C beoordeelt A en B

### Fase 3: Orchestrator Synthese

Een orchestrator LLM (Opus of Gemini Pro) creëert consensus document.

### Fase 4: Human Review

De mens markeert:
- ☑ Correcte items per provider
- Conflicten die moeten worden opgelost
- Ontbrekende informatie
- Nuances en correcties

### Fase 5: Final Synthese

LLM verwerkt human feedback in finaal document.

### Fase 6: Storage & Sync

- Opslaan in database
- Genereren van MD file
- Git commit

---

## Database Schema

```sql
-- Council sessie tracking
CREATE TABLE council_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    document_type VARCHAR(50) NOT NULL,  -- 'onboarding', 'architecture', 'adr'
    status VARCHAR(20) DEFAULT 'draft',   -- draft, in_review, approved, rejected
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(100)
);

-- Council consensus met versioning
CREATE TABLE council_consensus (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    version INTEGER DEFAULT 1,
    consensus_content TEXT NOT NULL,       -- Het consensus document
    human_feedback JSONB,                  -- Human correcties/aanvullingen
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document versies (MD files synced)
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    document_path VARCHAR(500) NOT NULL,   -- 'docs/ONBOARDING.md'
    version INTEGER DEFAULT 1,
    content TEXT NOT NULL,
    council_session_id UUID REFERENCES council_sessions(id),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## DocumentSyncService

```python
# Located in: backend/app/services/document_sync_service.py

class DocumentSyncService:
    """Bi-directional sync between MD files and database."""

    async def sync_to_database(self, project_id: int, file_path: str) -> DocumentVersion:
        """Parse MD file and store in database."""
        content = await self.read_md_file(file_path)
        metadata = self.extract_metadata(content)

        return await self.document_repo.create_version(
            project_id=project_id,
            document_path=file_path,
            content=content,
            metadata=metadata
        )

    async def sync_to_file(self, document_version: DocumentVersion) -> Path:
        """Generate MD file from database record."""
        content = self.generate_md_content(document_version)
        file_path = self.get_project_path(document_version.project_id) / document_version.document_path

        await self.write_md_file(file_path, content)
        await self.git_commit(file_path, f"Council approved: {document_version.document_path}")

        return file_path

    async def on_council_approve(self, session_id: UUID):
        """Hook called when council session is approved."""
        session = await self.council_repo.get_session(session_id)
        consensus = await self.council_repo.get_approved_consensus(session_id)

        # Generate final document incorporating human feedback
        final_content = await self.merge_human_feedback(
            consensus.consensus_content,
            consensus.human_feedback
        )

        # Store in database
        doc_version = await self.create_document_version(
            project_id=session.project_id,
            document_path=self.get_document_path(session.document_type),
            content=final_content,
            council_session_id=session_id
        )

        # Sync to MD file
        await self.sync_to_file(doc_version)
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/council/sessions` | POST | Start nieuwe council sessie |
| `/api/council/sessions/{id}` | GET | Haal sessie details op |
| `/api/council/sessions/{id}/consensus` | GET | Haal consensus document op |
| `/api/council/sessions/{id}/review` | POST | Submit human review (checkboxes + feedback) |
| `/api/council/sessions/{id}/approve` | POST | Approve & finalize document |
| `/api/council/sessions/{id}/reject` | POST | Reject met reden |

---

## Example Use Cases

### 1. Onboarding Documentation

```
3 providers + human validation → ~99% accuracy

Input: "Generate onboarding doc for klaverjas-competitie project"
Output: Validated onboarding document with correct commands, architecture, priorities
```

### 2. Architecture Decisions

```
Multi-model debate + human tiebreaker

Input: "Should we use microservices or monolith for this project?"
Output: ADR with pros/cons from multiple perspectives + human decision
```

### 3. Project Specifications

```
Council consensus + human nuances

Input: "Create project specification for HCI-CRS migration"
Output: Specification with business context, technical constraints, human domain knowledge
```

---

## Benefits

| Aspect | Council Only | + Human-in-the-Loop |
|--------|--------------|---------------------|
| Accuracy | ~95% | ~99% |
| Token cost | 3x base | 3.5x base |
| Human effort | 0 | ~15 min review |
| Trust level | Medium | High |
| Learning | None | Feedback stored |

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [llm-council.md](./llm-council.md) - LLM Council base architecture
- [project-documentation-standard.md](./project-documentation-standard.md) - Full specification
