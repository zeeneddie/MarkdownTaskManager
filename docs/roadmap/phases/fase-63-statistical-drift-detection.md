# Fase 63: Statistical Drift Detection

**Status:** PLANNED
**Priority:** P2
**Timeline:** Week 207-212
**Effort:** ~72 uur (~5 weken)
**Dependencies:** Fase 60 (Observability Foundation), ThinkingPatternStore ✅, CheckAlignmentService ✅
**Source:** [Tracer/BART Gap Analyse](../tracer-bart-gap-analysis.md)

---

## Executive Summary

Statistische embedding drift detection naast de bestaande keyword-based detectie in CheckAlignmentService. Gebruik vector similarity om subtiele agent afdwaling te detecteren die keyword matching mist.

**Het Probleem:**
> CheckAlignmentService detecteert drift via 4 DriftTypes met keyword/pattern matching. Dit mist subtiele semantische drift waar een agent wel de juiste keywords gebruikt maar inhoudelijk afdwaalt (bijv. correct vocabulaire maar verkeerde architectuurbeslissingen).

**De Oplossing:**
```
Agent Output ──► EmbeddingService ──► Current Embedding
                                           │
                                           ▼
                                    StatisticalDriftDetector
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                 Cosine Distance    Distribution Shift   Centroid Drift
                 vs Expected        (KL Divergence)      Analysis
                        │                  │                  │
                        ▼                  ▼                  ▼
                 ┌─────────────────────────────────────────────┐
                 │  CheckAlignmentService (extend)              │
                 │  + STATISTICAL_DRIFT type                    │
                 │  → Confucius PIV loop triggered              │
                 └─────────────────────────────────────────────┘
```

---

## Taken

### T4.1: Arize Phoenix Integratie (Hoog)

**Bestanden:** `backend/app/services/thinking_pattern_store.py`
**Effort:** 28 uur

Integreer Arize Phoenix voor embedding drift analyse:
- Installeer `arize-phoenix` als dependency
- Configureer Phoenix als lokale evaluator (geen cloud vereist)
- Gebruik ThinkingPatternStore's bestaande ChromaDB embeddings als baseline distributies
- Phoenix Embedding Drift module voor automatic distribution comparison
- Drift threshold configuratie per workflow type en stage

**Baseline Management:**
- Per workflow type + stage: opbouw van baseline embedding distributie
- Minimum 50 samples voor betrouwbare baseline
- Rolling window (laatste 100 runs) voor adaptieve baselines
- Outlier detection voor baseline vervuiling

### T4.2: StatisticalDriftDetector Service (Hoog)

**Bestanden:** Nieuw: `backend/app/services/statistical_drift_detector_service.py`, extend: `check_alignment_service.py`
**Effort:** 28 uur

Nieuwe service met drie drift detectie methoden:

| Methode | Wat het detecteert | Sensitivity |
|---------|-------------------|-------------|
| **Cosine Distance** | Afwijking van verwachte output richting | Hoog - detecteert topic drift |
| **KL Divergence** | Verschuiving in output distributie | Medium - detecteert stijl drift |
| **Centroid Drift** | Verschuiving van cluster centrum over tijd | Laag - detecteert geleidelijke drift |

**Integratie met CheckAlignmentService:**
- Nieuw DriftType: `STATISTICAL_DRIFT`
- Combineert keyword score (bestaand) met embedding score (nieuw)
- Weighted scoring: `combined_score = 0.6 * keyword_score + 0.4 * embedding_score`
- Configureerbare thresholds per methode

**API Endpoints:**
- `POST /api/drift/analyze` - Analyze embedding drift voor een specifieke output
- `GET /api/drift/baselines/{workflow_type}` - Baseline distributie stats
- `POST /api/drift/baselines/rebuild` - Herbereken baselines
- `GET /api/drift/history/{ticket_id}` - Drift history per ticket

### T4.3: Drift Alerting Hooks in Confucius (Medium)

**Bestanden:** `backend/app/confucius/orchestrator.py`
**Effort:** 16 uur

Hooks in Confucius Orchestrator:
- Na elke stage output: automatisch StatisticalDriftDetector aanroepen
- Bij significante drift (score < threshold): automatisch PIV loop triggeren
- Drift events emitteren naar OTLP (Fase 47) voor Langfuse visualisatie
- Drift alerts toevoegen aan ProgressDashboard events (Fase 48)

**Escalatie Logic:**
```
Embedding Drift Score:
  > 0.85: GEEN ACTIE (normaal)
  0.70-0.85: WARNING (log, geen PIV)
  0.50-0.70: PIV TRIGGER (automatic correction)
  < 0.50: HUMAN_NEEDED (te ver afgedwaald)
```

---

## Resultaat

Na implementatie:
- Subtiele agent drift detectie op basis van vector similarity
- Drie complementaire drift methoden (cosine, KL, centroid)
- Automatische PIV loop trigger bij significante drift
- Drift history per ticket voor post-mortem analyse
- Visueel in Langfuse en Progress Dashboard

## Success Criteria

- [ ] Detecteert semantische drift die keyword matching mist (validatie met bekende drift scenarios)
- [ ] False positive rate < 10% op normale workflow outputs
- [ ] Baseline opbouw correct na 50+ samples per stage
- [ ] PIV loop trigger werkt correct bij embedding drift
- [ ] Drift data zichtbaar in Langfuse traces
- [ ] 30+ unit tests

---

*Created: Week 162 (2026-01-31)*
