# MarQed.ai — Roadmap Afhankelijkheidsdiagram

**Week:** 162 (2026-01-31)
**Type:** Visueel overzicht

---

## Fase-afhankelijkheden

```mermaid
graph TD
    %% ── Styling ──
    classDef done fill:#2d6a4f,stroke:#1b4332,color:#fff
    classDef active fill:#e76f51,stroke:#9c3a1a,color:#fff
    classDef planned fill:#457b9d,stroke:#1d3557,color:#fff
    classDef future fill:#6c757d,stroke:#495057,color:#fff
    classDef strategic fill:#7209b7,stroke:#3a0ca3,color:#fff
    classDef journey fill:#e9c46a,stroke:#b08c2a,color:#000

    %% ── Afgerond (Fase 1-21) ──
    F1_21["Fase 1-21<br/>Foundation → ASP Stability<br/>720+ endpoints · 170+ services<br/>Week 46-143 ✅"]:::done

    %% ── Huidig ──
    F24["Fase 24 · Quick Wins<br/>A1 Quickscan · CWE · FP · Context<br/>Confucius PIV · Quality Impact<br/>Week 157 · 60%"]:::active

    %% ── GAP Track (Platform) ──
    GAP24["GAP-24 · Quick Wins & Foundation<br/>15 items<br/>Week 163-174"]:::planned
    GAP25["GAP-25 · Core Platform Enhancement<br/>18 items<br/>Week 175-190"]:::planned
    GAP26["GAP-26 · AI & Automation<br/>12 items (LLM-heavy)<br/>Week 191-204"]:::planned
    GAP27["GAP-27 · Testing Excellence<br/>8 items<br/>Week 205-214"]:::planned
    GAP28["GAP-28 · Advanced Integrations<br/>10 items<br/>Week 215-226"]:::planned
    GAP29["GAP-29 · Innovation & Scale<br/>9 items<br/>Week 227-244"]:::future

    %% ── Tracer/BART Track ──
    F60["Fase 60 · Observability Foundation<br/>OTLP + Langfuse<br/>P0 · Week 179-182"]:::planned
    F61["Fase 61 · Progress Dashboard<br/>Real-time voortgang + kosten<br/>P1 · Week 183-188"]:::planned
    F62["Fase 62 · Conversational Intake<br/>Epic Mode chat-based<br/>P1 · Week 193-198"]:::planned
    F63["Fase 63 · Statistical Drift Detection<br/>Embedding-based<br/>P2 · Week 207-212"]:::planned
    F64["Fase 64 · Self-Evolution<br/>Agent self-improvement<br/>P3 · Week 229-234"]:::future

    %% ── Strategische documenten ──
    CSJ["Client Service Journey<br/>5 fases · 4 swim-lanes<br/>11 secties incl. klanttevredenheid"]:::journey
    OC["OpenClaw + FlowInquiry HQ<br/>Architectuur & integratie<br/>64-uur fasering"]:::strategic
    TB["Tracer/BART Gap Analysis<br/>5 nieuwe fases gedefinieerd"]:::strategic
    MAL["Multi-Agent Landscape<br/>Strategisch advies"]:::strategic
    MPC["Migration Pattern Catalog<br/>25 patronen (10 actief)"]:::strategic

    %% ── Parallelle workstreams ──
    PAR_AE["AgentEvolver<br/>Integration"]:::future
    PAR_LC["LLM Council<br/>Integration"]:::future
    PAR_VF["Validation<br/>Framework"]:::future

    %% ── Afhankelijkheden: hoofdketen ──
    F1_21 --> F24
    F24 --> GAP24
    GAP24 --> GAP25
    GAP25 --> GAP26
    GAP26 --> GAP27
    GAP27 --> GAP28
    GAP28 --> GAP29

    %% ── Afhankelijkheden: Tracer/BART track ──
    GAP24 --> F60
    F60 --> F61
    F61 --> F62
    F60 --> F63
    F63 --> F64

    %% ── Cross-track afhankelijkheden ──
    GAP25 -.->|infra| F60
    F61 -.->|dashboard data| GAP26
    F62 -.->|intake verrijking| CSJ
    GAP29 -.->|stabiliteit| F64

    %% ── Strategische docs voeden fases ──
    TB -->|definieert| F60
    TB -->|definieert| F61
    TB -->|definieert| F62
    TB -->|definieert| F63
    TB -->|definieert| F64
    OC -.->|architectuur| CSJ
    MPC -.->|patronen| GAP25
    MAL -.->|positionering| GAP29

    %% ── Journey integratie ──
    CSJ -.->|operationeel| F24
    CSJ -.->|feedback loop| F61

    %% ── Parallelle streams ──
    F24 -.-> PAR_AE
    F24 -.-> PAR_LC
    F24 -.-> PAR_VF
    PAR_AE -.-> F64
    PAR_LC -.-> F63
```

## Legenda

| Kleur | Betekenis |
|-------|-----------|
| 🟢 Groen | Afgerond (Fase 1-21) |
| 🟠 Oranje | Actief / in uitvoering |
| 🔵 Blauw | Gepland (concrete weken) |
| ⚫ Grijs | Toekomst (week 227+) |
| 🟣 Paars | Strategische documenten |
| 🟡 Geel | Client Service Journey |

**Doorgetrokken lijn** = directe afhankelijkheid
**Stippellijn** = indirecte relatie / informatie-stroom

---

## Twee parallelle tracks

| Track | Fases | Focus | Doorlooptijd |
|-------|-------|-------|--------------|
| **Platform (GAP)** | GAP-24 → GAP-29 | 75 gaps, core platform opbouw | Week 163-244 (82 weken) |
| **Tracer/BART** | Fase 60 → 64 | Observability, dashboard, AI intake, drift, self-evolution | Week 179-234 (55 weken) |

Beide tracks starten vanuit **GAP-24** en convergeren bij **GAP-29 / Fase 64** (Innovation & Scale + Self-Evolution).
