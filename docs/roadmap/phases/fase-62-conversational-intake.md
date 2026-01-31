# Fase 62: Conversational Intake (Tracer Epic Mode)

**Status:** PLANNED
**Priority:** P1
**Timeline:** Week 193-198
**Effort:** ~80 uur (~5 weken)
**Dependencies:** SpecShapingService ✅, IntakeToBacklogService ✅, HierarchicalMemoryManager ✅
**Source:** [Tracer/BART Gap Analyse](../tracer-bart-gap-analysis.md)

---

## Executive Summary

Tracer "Epic Mode" equivalent: chat-based requirements gathering die automatisch specs en tickets genereert. Gebruiker beschrijft in natuurlijke taal wat hij wilt bouwen, systeem stelt follow-up vragen, en genereert automatisch complete epic/feature/story hierarchie.

**Het Probleem:**
> MarQed heeft SpecShapingService (validatie), IntakeToBacklogService (ticket generatie), en Peter/Felix pipelines (spec generatie). Maar er is geen conversationele interface die deze services verbindt als een vloeiende chat-ervaring.

**De Oplossing:**
```
User Chat ──► ConversationalIntakeService ──► SpecShapingService (validatie)
                    │                              │
                    │  (state machine)             ▼
                    │                         Peter (Constitution)
                    │                              │
                    ▼                              ▼
              Follow-up vragen            Felix (Specification)
              Domain templates                     │
              Context memory                       ▼
                    │                   IntakeToBacklogService
                    │                              │
                    ▼                              ▼
              Chat response             Epic/Feature/Story hierarchy
```

---

## Taken

### T3.1: ConversationalIntakeService (Hoog)

**Bestanden:** Nieuw: `backend/app/services/conversational_intake_service.py`, extend: `spec_shaping_service.py`
**Effort:** 24 uur

Chat state machine met volgende states:

```
GREETING ──► DOMAIN_DETECTION ──► REQUIREMENTS_GATHERING ──► CLARIFICATION
                                         │                        │
                                         ▼                        ▼
                                    SPEC_REVIEW ◄────────── REFINEMENT
                                         │
                                         ▼
                                    TICKET_GENERATION ──► COMPLETE
```

**State Machine Details:**

| State | Trigger | Actie |
|-------|---------|-------|
| `GREETING` | Session start | Welkom, vraag om projectbeschrijving |
| `DOMAIN_DETECTION` | Eerste bericht ontvangen | Detecteer domein (web, mobile, API, migration, etc.) |
| `REQUIREMENTS_GATHERING` | Domein vastgesteld | Stel domein-specifieke vragen (zie T3.2) |
| `CLARIFICATION` | Ambiguiteit gedetecteerd | Gerichte follow-up vraag |
| `SPEC_REVIEW` | Alle verplichte velden ingevuld | Toon samenvatting, vraag bevestiging |
| `REFINEMENT` | Gebruiker wil aanpassen | Pas specifieke secties aan |
| `TICKET_GENERATION` | Spec goedgekeurd | Genereer epic/feature/story via IntakeToBacklogService |
| `COMPLETE` | Tickets gegenereerd | Toon overzicht met links |

**Integratie met bestaande services:**
- `SpecShapingService.CheckCategory` voor validatie per sectie
- `SoftwareIntakeService` voor intake structuur
- LLM calls voor natural language understanding en follow-up vraag generatie

### T3.2: Gestructureerde Follow-Up Templates per Domein (Medium)

**Bestanden:** Extend: `ConversationalIntakeService`
**Effort:** 16 uur

Domein-specifieke vraag templates:

| Domein | Verplichte Vragen | Optionele Vragen |
|--------|-------------------|-------------------|
| **Web App** | Doelgroep, kernfunctionaliteit, auth vereist? | Performance eisen, multi-taal, mobiel-eerst? |
| **API** | Consumenten, data model, auth methode | Rate limiting, versioning, backward compat? |
| **Migration** | Bron technologie, doel stack, data omvang | Downtime tolerantie, rollback strategie? |
| **Mobile** | Platform (iOS/Android/both), offline? | Push notifications, biometrics, camera? |
| **Integration** | Externe systemen, protocol, frequentie | Error handling, idempotency, retry? |

Per domein: 5-8 verplichte vragen, 3-5 optionele follow-ups.
Elke vraag heeft: label, example_answer, validation_rule, importance_weight.

### T3.3: Koppeling Chat -> IntakeToBacklogService (Medium)

**Bestanden:** `backend/app/services/intake_to_backlog_service.py`
**Effort:** 14 uur

Transformatie van chat-verzamelde requirements naar IntakeToBacklogService input:
- Map chat antwoorden naar `IntakeDocument` structuur
- Genereer epic titel en beschrijving uit chat context
- Stel automatische feature/story breakdown voor
- Gebruiker kan breakdown aanpassen in REFINEMENT state
- Respecteer bestaande IntakeToBacklogService scoring en prioritering

### T3.4: WebSocket Chat API Endpoint (Medium)

**Bestanden:** Nieuw: `backend/app/api/conversational_intake.py`
**Effort:** 14 uur

Endpoints:
- `ws://host/ws/intake/{session_id}` - Chat WebSocket
- `POST /api/intake/sessions` - Start nieuwe sessie
- `GET /api/intake/sessions/{id}` - Sessie status
- `GET /api/intake/sessions/{id}/spec` - Gegenereerde spec
- `GET /api/intake/sessions/{id}/tickets` - Gegenereerde tickets
- `POST /api/intake/sessions/{id}/approve` - Goedkeur en genereer tickets

**WebSocket Message Format:**
```json
// Client -> Server
{ "type": "user_message", "content": "Ik wil een patiëntdossier systeem bouwen" }

// Server -> Client
{ "type": "assistant_message", "content": "...", "state": "REQUIREMENTS_GATHERING", "progress": 0.4 }
{ "type": "spec_preview", "spec": { ... }, "missing_fields": ["auth_method", "data_retention"] }
{ "type": "tickets_generated", "epic": { ... }, "features": [...], "stories": [...] }
```

### T3.5: Context Memory voor Multi-Turn Conversations (Medium)

**Bestanden:** Extend: `HierarchicalMemoryManager`
**Effort:** 12 uur

Extend bestaande HierarchicalMemoryManager met:
- `conversation_memory` layer voor chat context (short-term, per sessie)
- Conversation history summarization bij context window druk
- Cross-session memory: als gebruiker eerder een project beschreef, hergebruik context
- Max context tokens per chat sessie: configureerbaar (default 50K)

---

## Resultaat

Na implementatie:
- Gebruiker kan in natuurlijke taal beschrijven wat hij wilt bouwen
- Systeem stelt intelligente follow-up vragen per domein
- Automatische spec generatie met review stap
- Automatische epic/feature/story generatie via bestaande pipeline
- Chat history bewaard voor cross-session context

## Success Criteria

- [ ] Chat sessie van 5-8 berichten leidt tot complete spec
- [ ] Domein-detectie correct in 90%+ van gevallen
- [ ] Gegenereerde tickets passeren IntakeToBacklogService validatie
- [ ] WebSocket chat stabiel voor 30+ minuten sessies
- [ ] Follow-up vragen relevant en niet repetitief
- [ ] 40+ unit tests voor ConversationalIntakeService

## Relatie met Fase 32 (Ralph Wiggum)

De ConversationalIntakeService output kan als input dienen voor Ralph's PRP framework:
1. Chat genereert spec + tickets
2. Spec wordt PRP Document (PRPGeneratorService)
3. Ralph voert PRP Document autonoom uit

---

*Created: Week 162 (2026-01-31)*
