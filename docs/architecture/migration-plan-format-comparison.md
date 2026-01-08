# Vergelijking: Hand-Written vs Auto-Generated Migration Plan

**Datum:** 2025-12-31
**Doel:** Objectieve vergelijking van twee formaten voor migratieplannen

---

## 1. Overzicht

| Aspect | Hand-Written (hci-crs-migration-plan.md) | Auto-Generated (MigrationPlan.to_markdown()) |
|--------|------------------------------------------|----------------------------------------------|
| **Bron** | Handmatig geschreven door Claude + gebruiker | Gegenereerd uit database model |
| **Lengte** | ~650 regels | ~200-300 regels (afhankelijk van data) |
| **Onderhoud** | Handmatig bijwerken | Automatisch bij model update |
| **Traceability** | Geen directe link naar data | `brown_paper_session_id`, `id` links |

---

## 2. Sectie-voor-Sectie Vergelijking

### 2.1 Projectoverzicht

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **LOC, bestanden, modules** | Gedetailleerd met metrics | Basis (LOC, file_count) | Hand-Written |
| **Technologie stack** | Source + 2 Target stacks uitgebreid | Target stacks in tabel | Hand-Written |
| **Dependency info** | Top 9 foundation modules met counts | Foundation summary | Hand-Written |
| **Traceability** | Geen session ID | `brown_paper_session_id` link | Auto-Generated |

**Conclusie:** Hand-written heeft meer detail, maar auto-generated heeft betere traceability.

### 2.2 Migratiestrategie

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **Visuele diagrammen** | ASCII art flow diagrams | Geen | Hand-Written |
| **Fase breakdown** | Gedetailleerd met LOC per fase | `migration_phases` array | Gelijk |
| **Module volgorde** | Top 10 modules met deps | `component_mapping` | Hand-Written |
| **Sync punten** | Dual-stack sync indicators | `evaluation_mode` field | Gelijk |

**Conclusie:** Hand-written heeft visuele diagrammen die auto-generated mist.

### 2.3 Epic/Story Structuur

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **Epic breakdown** | Tree structure met features | Niet aanwezig | Hand-Written |
| **Story sizing rules** | INVEST criteria uitgelegd | Niet aanwezig | Hand-Written |
| **Test coverage** | Expliciete 90% requirement | Niet aanwezig | Hand-Written |

**Conclusie:** Hand-written bevat project management context die auto-generated mist.

### 2.4 Foundation Analyse

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **Module counts** | Per categorie | `foundation_summary` met by_category | Gelijk |
| **Structuur** | ASCII art tree | ASCII art tree | Gelijk |
| **Migratie implicatie** | Aanwezig | Aanwezig | Gelijk |

**Conclusie:** Gelijkwaardig - auto-generated bevat dezelfde informatie.

### 2.5 Schattingen

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **Function Points** | Niet aanwezig | IFPUG met VAF, UFP, AFP | Auto-Generated |
| **Effort breakdown** | Niet aanwezig | Uren, dagen, weken | Auto-Generated |
| **Team sizing** | Niet aanwezig | team_size_recommended | Auto-Generated |
| **Phase breakdown** | LOC per fase | Percentage/uren per fase | Auto-Generated |

**Conclusie:** Auto-generated heeft betere schatting sectie (vanuit Eliza agent).

### 2.6 Risico's

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **Structuur** | Tabel met 8 risico's | Tabel met probability/impact/mitigation | Gelijk |
| **Dual-stack risico's** | Specifiek voor dual-migration | Generiek | Hand-Written |

**Conclusie:** Hand-written heeft project-specifieke risico's.

### 2.7 Setup Commando's

| Criterium | Hand-Written | Auto-Generated | Winnaar |
|-----------|--------------|----------------|---------|
| **Stack A setup** | Volledige bash commands | Niet aanwezig | Hand-Written |
| **Stack B setup** | Volledige bash commands | Niet aanwezig | Hand-Written |
| **Platform tools** | Lijst met services | Niet aanwezig | Hand-Written |

**Conclusie:** Hand-written bevat praktische setup instructies.

---

## 3. Score Matrix

| Criterium | Gewicht | Hand-Written | Auto-Generated |
|-----------|---------|--------------|----------------|
| **Volledigheid van context** | 20% | 9/10 | 6/10 |
| **Visuele diagrammen** | 15% | 10/10 | 2/10 |
| **Traceability naar data** | 15% | 3/10 | 10/10 |
| **Onderhoudbaarheid** | 15% | 4/10 | 10/10 |
| **Schattingen (FP/SP)** | 10% | 2/10 | 9/10 |
| **Setup instructies** | 10% | 10/10 | 0/10 |
| **Risico analyse** | 10% | 8/10 | 6/10 |
| **Epic/Story structuur** | 5% | 10/10 | 0/10 |

### Gewogen Scores

| Document | Score |
|----------|-------|
| **Hand-Written** | 6.95/10 |
| **Auto-Generated** | 5.90/10 |

---

## 4. Sterke Punten per Type

### Hand-Written Sterke Punten
1. Visuele ASCII diagrammen voor flow understanding
2. Project-specifieke context en nuances
3. Setup commando's direct bruikbaar
4. Epic/Story/Task breakdown voor Kanban
5. INVEST criteria en test coverage rules
6. Dual-stack sync punten expliciet

### Auto-Generated Sterke Punten
1. Altijd consistent format
2. Direct gekoppeld aan database (traceability)
3. Automatisch bijgewerkt bij data changes
4. Bevat IFPUG schattingen uit Eliza
5. Geen menselijke fouten in structuur
6. Reproduceerbaar en versioneerbaar

---

## 5. Gaps in Auto-Generated (Te Verbeteren)

Om auto-generated gelijkwaardig te maken, moeten we toevoegen:

| Gap | Prioriteit | Implementatie |
|-----|------------|---------------|
| **Visuele diagrammen** | P1 | Toevoegen aan `to_markdown()` als ASCII art |
| **Setup commando's** | P1 | Nieuw veld `setup_commands` (JSONB) |
| **Epic/Story structure** | P2 | Link naar `HierarchicalStoryExtraction` output |
| **Test coverage rules** | P2 | Veld `test_requirements` toevoegen |
| **Module volgorde** | P3 | Uit `component_mapping` sorteren op deps |
| **INVEST criteria** | P3 | Standaard template tekst |

---

## 6. Aanbeveling

### Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AANBEVOLEN: HYBRID DOCUMENT STRATEGIE                                           │
│                                                                                  │
│  1. BASE: Auto-generated uit MigrationPlan.to_markdown()                         │
│     └── Garandeert consistentie en traceability                                 │
│                                                                                  │
│  2. ENRICHMENT: Handmatige toevoegingen                                          │
│     ├── Visuele diagrammen (sectie 2.1)                                         │
│     ├── Project-specifieke context                                               │
│     └── Setup commando's (sectie Appendix)                                       │
│                                                                                  │
│  3. SYNC: Bij model update → regenerate base, merge enrichments                  │
│                                                                                  │
│  RESULTAAT: Beste van beide werelden                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Volgende Stappen

1. **Extend to_markdown()** met:
   - ASCII diagram support
   - Setup commands section
   - Link naar hierarchical extraction

2. **Keep hand-written sections** voor:
   - Project-specifieke context
   - Visuele flows
   - Team/process info

3. **Create merge tool** die:
   - Auto-generated base genereert
   - Hand-written enrichments preserveert
   - Conflicts detecteert

---

**Conclusie:** Het auto-generated document is een goede basis, maar de hand-written versie bevat waardevolle context die niet uit data alleen komt. Een hybrid approach combineert de sterke punten van beide.
