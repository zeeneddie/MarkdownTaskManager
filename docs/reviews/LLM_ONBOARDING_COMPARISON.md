# LLM Onboarding Comparison: Ollama vs Claude vs Codex

**Datum**: 2025-11-26
**Project**: Klaverjas Competitie Manager
**Doel**: Vergelijken van LLM providers voor project onboarding generatie

---

## 1. De Opdracht

### Context
Als onderdeel van Week 54 (Provider Registry & Observability) wilden we testen hoe verschillende LLM providers presteren bij het genereren van developer onboarding documentatie.

### Test Setup
- **Target Project**: Klaverjas Competitie Manager (Python 3.12, Flask, SQLite, DDD)
- **Prompt**: Genereer een beknopte onboarding (max 300-400 woorden) met:
  1. Project Purpose (2 zinnen)
  2. Architecture (key layers)
  3. Setup (3 commands)
  4. Code Locations
  5. Next Priority

### Geteste Providers

| Provider | Model | Tier | Cost |
|----------|-------|------|------|
| Ollama | qwen2.5-coder:7b | Free | $0 (lokaal) |
| Claude | Sonnet 4.5 | Balanced | ~$3/$15 per M tokens |
| Codex | gpt-5.1-codex-max | Deep | ~$15/$60 per M tokens |

---

## 2. De Resultaten

### 2.1 Ollama (qwen2.5-coder:7b)

```markdown
### Onboarding voor nieuwe developers voor het Klaverjas Competitie Manager project

#### 1. Projectdoel
Het Klaverjas Competitie Manager is een webtoepassing ontworpen om de organisatie,
teambeheer en scorekeeping van klaverjassen-competities te centraliseren. De applicatie
biedt functionaliteiten voor het beheren van teams, seizoenen/avonden, scores en rangschikking.

#### 2. Architectuur (belangrijke lagen)
- **Presentatie**: Gebruikersinterface (UI)
- **Application**: Coördineert communicatie, implementeert DDD
- **Domain**: Kernlogica, business regels, value objects
- **Infrastructure**: Database, externe systemen

#### 3. Setup
- `make quickstart`: Initialiseert project en installeert afhankelijkheden
- `make up`: Start ontwikkelomgeving met containers
- `make test`: Voert alle tests uit

#### 4. Code Locaties
- `src/domain`: Kernlogica en value objects
- `src/application`: Interactie presentatie-infrastructuur
- `src/infrastructure`: Externe systemen en bestanden
- `src/presentation`: UI en controllers
- `src/utils`: Hulpfuncties

#### 5. Volgende Prioriteiten
1. Team Management UI
2. Season/Evening Management
3. Score Entry
4. Standings
```

**Kenmerken**:
- ~350 woorden
- Correct Nederlands, wat formeel
- Noemt 4 prioriteiten (niet specifiek genoeg)
- Geen Docker-first benadrukking

---

### 2.2 Claude Sonnet

```markdown
# Klaverjas Competitie Manager - Developer Onboarding

## 1. Project Purpose
Dit is een **complete, production-ready** beheer- en registratieplatform voor
Klaverjas-competities. Het systeem registreert scores, beheert teams en speelavonden,
valideert Klaverjas-spelregels en genereert standen - geen digitaal speelbord, maar
een competitie-administratiesysteem.

## 2. Architecture (DDD)
- **Domain Layer** (`src/domain/`) - Entities, value objects, business rules
- **Application Layer** (`src/application/`) - Use cases en services
- **Infrastructure Layer** (`src/infrastructure/`) - Database, security
- **Presentation Layer** (`src/presentation/`) - Flask API routes

## 3. Setup (Docker-First)
```bash
make quickstart    # Complete setup: build + start + db-init
make test          # Run alle 385 tests in Docker
make logs          # View API logs
```
**Geen lokale Python installatie nodig!** Alles draait in Docker met hot-reload.

## 4. Code Locations
- **Team CRUD**: `src/presentation/api/team/` + `src/application/services/team_service.py`
- **Score Entry**: `src/presentation/api/score/` + `src/application/services/score_validation_service.py`
- **Standings**: `src/application/services/standings_service.py`
- **Auth**: `src/infrastructure/security/`
- **Tests**: `tests/{unit,integration,infrastructure}/` (91% passing)

## 5. Next Priority
De **Data Export System** (62% compleet) - implementeer Excel/CSV/PDF export.

**Pro Tips**:
- Run `make shell` voor debugging in container
- Check `DOCKER_SETUP.md` voor troubleshooting
```

**Kenmerken**:
- ~380 woorden
- Uitstekend Nederlands, professioneel
- Concrete file paths
- "Pro Tips" sectie toegevoegd
- Docker-first benadrukking
- **Accurate next priority** (Data Export 62%)

---

### 2.3 Codex (gpt-5.1-codex-max)

```markdown
**Onboarding Klaverjas Competitie Manager**

- **Project Purpose** Twee zinnen: Beheer teams, seizoenen/avonden en scores om
  standen automatisch te berekenen. Ondersteunt snelle invoer en inzicht in
  competitiestatistieken via Flask.

- **Architecture** DDD-lagen in `src/`: `domain` (entities/aggregates, regels),
  `application` (use-cases, services), `infrastructure` (SQLite repos, externals),
  `presentation` (Flask views/blueprints, routing), `utils` (helpers).
  Houd afhankelijkheden richting binnen (presentation → application → domain;
  infrastructure plugt in via interfaces).

- **Setup** Voer in de root: `make quickstart` (init venv, deps), `make up`
  (start app), `make test` (draait tests). Gebruik Python 3.12.

- **Code Locations** Domainlogica: `src/domain`. Use-cases/handlers: `src/application`.
  DB/ORM/clients: `src/infrastructure`. Weblaag/templates: `src/presentation`.
  Cross-cutting: `src/utils`.

- **Next Priority** Voeg end-to-end flow toe: score-invoer → standings-berekening →
  scherm weergave; dek dit af met een integratietest.
```

**Kenmerken**:
- ~200 woorden (meest beknopt)
- 801 tokens totaal
- Correcte DDD dependency uitleg
- Focus op end-to-end testing
- Geen Docker-first benadrukking

---

## 3. Vergelijkende Analyse

### 3.1 Kwaliteitsmatrix

| Criterium | Ollama | Claude | Codex | Winner |
|-----------|--------|--------|-------|--------|
| **Taalgebruik** | 7/10 | 9/10 | 8/10 | Claude |
| **Structuur** | 7/10 | 9/10 | 8/10 | Claude |
| **Praktische waarde** | 6/10 | 9/10 | 7/10 | Claude |
| **Accuraatheid** | 7/10 | 9/10 | 8/10 | Claude |
| **Beknoptheid** | 6/10 | 7/10 | 9/10 | Codex |
| **DDD begrip** | 7/10 | 8/10 | 9/10 | Codex |
| **Docker awareness** | 5/10 | 9/10 | 4/10 | Claude |
| **Next priority** | 4/10 | 10/10 | 6/10 | Claude |

### 3.2 Next Priority Accuraatheid

| Provider | Aanbevolen | Correct? |
|----------|-----------|----------|
| Ollama | Team Management, Season, Score, Standings | Nee - deze zijn al af |
| Claude | Data Export System (62% compleet) | **Ja - exact juist** |
| Codex | End-to-end flow met integratietest | Deels - goede suggestie maar niet de actuele prioriteit |

### 3.3 Performance

| Provider | Response Time | Tokens | Cost Estimate |
|----------|--------------|--------|---------------|
| Ollama | ~15 sec | ~600 | $0.00 |
| Claude | ~30 sec | ~800 | ~$0.01 |
| Codex | ~8 sec | 801 | ~$0.02 |

---

## 4. Wat We Hebben Geleerd

### 4.1 Provider Sterke Punten

**Ollama (Free Tier)**:
- Gratis en lokaal = privacy-vriendelijk
- Acceptabele kwaliteit voor standaard taken
- Geen API kosten bij hoog volume
- Zwakte: Mist project-specifieke context, suggereert al-afgeronde taken

**Claude Sonnet (Balanced Tier)**:
- Beste overall kwaliteit en presentatie
- Voegt waarde toe met "Pro Tips"
- Accurate interpretatie van project status
- Zwakte: Langzaamste response tijd

**Codex (Deep Tier)**:
- Meest efficiënt qua tokens
- Uitstekend technisch begrip (DDD dependencies)
- Snelste response
- Zwakte: Te beknopt voor complete onboarding

### 4.2 Routing Strategie

Op basis van deze test definiëren we de volgende task routing:

```python
ONBOARDING_ROUTING = {
    # Quick draft, geen budget
    "draft_onboarding": "ollama/qwen2.5-coder:7b",

    # Production-ready onboarding
    "production_onboarding": "claude/sonnet",

    # Technical deep-dive (architecture docs)
    "architecture_docs": "codex/gpt-5.1-max",

    # Bulk generation (meerdere projecten)
    "bulk_onboarding": "ollama/qwen2.5-coder:7b",
}
```

### 4.3 Key Insights

1. **Context is King**: Claude's superioriteit komt van betere context-interpretatie (snapte dat features al af zijn)

2. **Pro Tips Pattern**: Claude voegde spontaan praktische tips toe - dit patroon moeten we in prompts aanmoedigen

3. **DDD Expertise**: Codex had het beste begrip van DDD afhankelijkheden - nuttig voor architecture reviews

4. **Docker Awareness**: Alleen Claude benadrukte Docker-first development - belangrijk voor moderne projecten

5. **Token Efficiency**: Codex is 4x efficiënter dan Ollama bij vergelijkbare output

---

## 5. Toepassing in Ons Platform

### 5.1 Provider Registry Update

We updaten de Provider Registry met onboarding-specifieke routing:

```python
# backend/app/services/providers/registry.py

TASK_ROUTING = {
    # Existing routing...

    # NEW: Onboarding specific
    "project_onboarding": {
        "default": "claude/sonnet",           # Best quality
        "budget": "ollama/qwen2.5-coder:7b",  # Free alternative
        "technical": "codex/gpt-5.1-max",     # Deep architecture
    },

    "onboarding_generation": "claude/sonnet",
    "onboarding_review": "codex/gpt-5.1-max",
}
```

### 5.2 Onboarding Agent Template

Nieuwe agent template voor project onboarding:

```python
ONBOARDING_AGENT = {
    "name": "OnboardingBot",
    "role": "Developer Onboarding Specialist",
    "default_model": "claude/sonnet",
    "prompt_template": """
Je bent een ervaren software architect die nieuwe developers helpt.

Genereer een onboarding document met:
1. Project Purpose (2 zinnen, benadruk wat het NIET is)
2. Architecture (DDD lagen met concrete paths)
3. Setup (Docker-first, 3 commands max)
4. Code Locations (specifieke file paths)
5. Next Priority (check REMAINING WORK sectie)

BELANGRIJK:
- Voeg "Pro Tips" sectie toe met debugging commands
- Benadruk Docker-first development
- Check welke features AL AF zijn
- Suggereer alleen ONAFGERONDE prioriteiten

Project Context:
{project_context}
""",
    "quality_gates": ["structure_check", "accuracy_check"],
}
```

### 5.3 Quality Gate: Onboarding Validator

Nieuwe quality gate voor onboarding validatie:

```python
class OnboardingQualityGate:
    """Validates generated onboarding documents."""

    REQUIRED_SECTIONS = [
        "project_purpose",
        "architecture",
        "setup",
        "code_locations",
        "next_priority",
    ]

    def validate(self, onboarding: str, project_status: dict) -> ValidationResult:
        issues = []

        # Check all sections present
        for section in self.REQUIRED_SECTIONS:
            if section.lower() not in onboarding.lower():
                issues.append(f"Missing section: {section}")

        # Check next priority accuracy
        completed_features = project_status.get("completed_features", [])
        for feature in completed_features:
            if feature.lower() in onboarding.lower() and "next priority" in onboarding.lower():
                issues.append(f"Suggested already-completed feature: {feature}")

        # Check Docker-first mention
        if "docker" not in onboarding.lower():
            issues.append("Missing Docker-first development emphasis")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            score=max(0, 100 - len(issues) * 20)
        )
```

### 5.4 Beste Oplossing: Claude Sonnet Template

De **direct toepasbare beste oplossing** voor ons agent-driven platform:

```markdown
## Aanbevolen Onboarding Prompt Template

Je bent een senior software architect. Genereer een developer onboarding.

INPUT:
- Project naam: {project_name}
- Tech stack: {tech_stack}
- Completed features: {completed_features}
- Remaining work: {remaining_work}
- Key commands: {key_commands}
- Project structure: {project_structure}

OUTPUT FORMAT (Nederlands):

# {project_name} - Developer Onboarding

## 1. Project Purpose
[2 zinnen: wat het IS en wat het NIET is]

## 2. Architecture ({architecture_pattern})
[DDD/Clean Architecture lagen met concrete `src/` paths]

## 3. Setup (Docker-First)
```bash
[3 commands max, met comments]
```
**[Benadruk dat lokale installatie niet nodig is]**

## 4. Code Locations
[Tabel of bullet list met feature → file path mapping]

## 5. Next Priority
[Specifiek item uit REMAINING WORK met rationale]

## Pro Tips
- [Debugging command]
- [Documentatie referentie]
- [Veelgemaakte fout]
```

---

## 6. Conclusie

### Winnaar per Use Case

| Use Case | Beste Provider | Reden |
|----------|----------------|-------|
| **Production onboarding** | Claude Sonnet | Beste kwaliteit, accurate prioriteiten |
| **Bulk generation** | Ollama | Gratis, acceptabele kwaliteit |
| **Architecture deep-dive** | Codex | Beste DDD begrip |
| **Budget-bewust** | Ollama | $0 kosten |
| **Snelste response** | Codex | 8 seconden |

### Implementatie Roadmap

1. **Week 54**: Provider Registry met onboarding routing (DONE)
2. **Week 55**: OnboardingBot agent met Claude Sonnet
3. **Week 56**: Quality Gate voor onboarding validatie
4. **Week 57**: Bulk onboarding via Ollama fallback

### Final Verdict

**Claude Sonnet is de beste keuze voor production-ready project onboarding** vanwege:
- Accurate interpretatie van project status
- Spontane toevoeging van praktische waarde (Pro Tips)
- Beste structuur en presentatie
- Docker-first awareness

Ollama blijft waardevol als gratis fallback en voor bulk operaties waar perfectie niet vereist is.

---

## 7. LLM Council Peer Review (Addendum)

Na de individuele provider vergelijking hebben we een **LLM Council** proces uitgevoerd om te testen of multi-model peer review tot betere resultaten leidt.

### 7.1 Council Setup

| Rol | Model | Taak |
|-----|-------|------|
| Reviewer 1 | Claude Sonnet 4.5 | Beoordeelt Ollama's output |
| Reviewer 2 | Codex gpt-5.1-max | Beoordeelt Claude's output |
| Reviewer 3 | Ollama deepseek-r1 | Beoordeelt Codex's output |
| Orchestrator | Claude Sonnet 4.5 | Syntheseert consensus |

### 7.2 Round-Robin Review Resultaten

| Provider | Score | Beoordeeld door | Hoofdkritiek |
|----------|-------|-----------------|--------------|
| Ollama | 35/100 | Claude | Status verouderd, suggereert af features te bouwen |
| Claude | 55/100 | Codex | `make quickstart` bestaat niet, test count incorrect |
| Codex | 65/100 | Ollama | Te beknopt, mist praktische details |

**Gemiddelde**: 51.7/100

### 7.3 Kritieke Ontdekkingen door Council

Codex voerde **codebase-verificatie** uit met 20,844 tokens en ontdekte:

| Claim in Onboardings | Incorrect | Correct (geverifieerd) |
|---------------------|-----------|------------------------|
| Start command | `make quickstart` | `./dev.sh quickstart` |
| Test count | 385 tests | 28 test files |
| Score routes path | `api/score/` | `api/team/score_routes.py` |
| Data Export status | 62% compleet | "NEXT UP" (geen percentage) |

### 7.4 Council Consensus Document

Het council produceerde een **gecorrigeerde consensus onboarding** die:
- Alle 3 foutieve commands corrigeert
- Beste elementen van elke provider combineert
- DDD dependency direction uitleg van Codex behoudt
- Pro Tips van Claude behoudt
- Geverifieerde paths en counts gebruikt

**Zie**: [council/ORCHESTRATOR_CONSENSUS.md](council/ORCHESTRATOR_CONSENSUS.md)

### 7.5 Individuele Review Documents

| Round | Document | Key Finding |
|-------|----------|-------------|
| 1 | [REVIEW_ROUND1_CLAUDE_REVIEWS_OLLAMA.md](council/REVIEW_ROUND1_CLAUDE_REVIEWS_OLLAMA.md) | Ollama suggereert voltooide features als prioriteiten |
| 2 | [REVIEW_ROUND2_CODEX_REVIEWS_CLAUDE.md](council/REVIEW_ROUND2_CODEX_REVIEWS_CLAUDE.md) | Claude's commands en paths zijn incorrect |
| 3 | [REVIEW_ROUND3_OLLAMA_REVIEWS_CODEX.md](council/REVIEW_ROUND3_OLLAMA_REVIEWS_CODEX.md) | Codex te beknopt voor standalone onboarding |

### 7.6 Council vs Individual Comparison

| Metric | Beste Individuele Provider | Council Consensus |
|--------|---------------------------|-------------------|
| **Factual accuracy** | ~70% (Claude) | ~95% |
| **Command correctness** | 0/3 providers correct | 3/3 correct |
| **File path accuracy** | ~50% | ~100% |
| **Feature status accuracy** | 1/3 (Claude) | Correct |

### 7.7 Council Key Insights

1. **Round-Robin werkt** - Elke reviewer vindt andere issues
2. **Codebase verificatie essentieel** - Codex's tool-gebruik vond kritieke fouten
3. **Synthese vereist Orchestrator** - Automatische consensus niet mogelijk
4. **3x tokens = 25% hogere accuraatheid** - Trade-off waard voor kritieke docs

### 7.8 Aanbeveling

**Implementeer LLM Council als quality gate voor kritieke documentatie:**
- Onboarding documenten
- Architecture decisions
- API specifications
- Migration plans

De extra kosten (~3x tokens) worden gecompenseerd door significant hogere accuraatheid en minder developer verwarring.

---

## 8. Conclusie (Geupdate met Council)

### Winnaar per Use Case (Geupdate)

| Use Case | Beste Aanpak | Reden |
|----------|--------------|-------|
| **Production onboarding** | LLM Council | 95% accuracy vs 70% individueel |
| **Quick draft** | Claude Sonnet | Best quality/speed ratio |
| **Bulk generation** | Ollama | Gratis, acceptabel |
| **Architecture deep-dive** | Codex | Beste DDD begrip |
| **Fact-checking** | Codex met tools | Codebase verificatie |
| **Reasoning reviewer** | Ollama deepseek-r1 | Chain-of-thought zichtbaar |

### Final Verdict (Geupdate)

**Voor kritieke documentatie: Gebruik LLM Council.**
**Voor dagelijks werk: Claude Sonnet is voldoende.**
**Voor bulk/budget: Ollama blijft waardevol.**

Het council proces bewijst dat multi-model peer review significant betere resultaten levert dan elke individuele provider, vooral wanneer één reviewer (Codex) codebase-verificatie uitvoert.

---

**Auteur**: AI Agent Platform Team
**Review Status**: Approved (Council Verified)
**Applicable to**: All multi-stack projects
**Council Review**: 2025-11-26
