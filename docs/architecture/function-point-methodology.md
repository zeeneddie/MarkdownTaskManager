# Function Point Methodology - IFPUG CPM 4.3.1

**Doel**: Gestandaardiseerde FP berekening voor Brown Paper workflow
**Doelgroep**: Agents, developers, project managers
**Versie**: 1.0
**Last Updated**: 2025-11-28

---

## Overview

Function Point Analysis (FPA) is een standaard methode om software grootte te meten, onafhankelijk van de gebruikte technologie. Het MarQed Agent SD Platform gebruikt **IFPUG CPM 4.3.1** (International Function Point Users Group - Counting Practices Manual) voor:

1. **Brown Paper workflow** - Analyse van bestaande code
2. **Green Paper workflow** - Schatting van nieuwe features
3. **Sprint planning** - Capaciteitsplanning

---

## De 5 FP Component Types

### 1. ILF - Internal Logical File (7-15 FP)

**Definitie**: Groep logisch gerelateerde data die door de applicatie wordt onderhouden.

| Complexiteit | RETs | DETs 1-19 | DETs 20-50 | DETs 51+ |
|--------------|------|-----------|------------|----------|
| **Low** | 1 | 7 | 7 | 10 |
| **Average** | 2-5 | 7 | 10 | 15 |
| **High** | 6+ | 10 | 15 | 15 |

**Voorbeelden**:
- Database tabellen met CRUD operaties
- Configuratie bestanden die door de app worden gewijzigd
- Interne caches met persistentie

```
ILF Identificatie Checklist:
□ Wordt onderhouden door de applicatie (INSERT/UPDATE/DELETE)
□ Is logisch gerelateerd (1 entiteit of concept)
□ Kan RETs en DETs identificeren
```

### 2. EIF - External Interface File (5-10 FP)

**Definitie**: Groep logisch gerelateerde data die door een andere applicatie wordt onderhouden maar door deze applicatie wordt gelezen.

| Complexiteit | RETs | DETs 1-19 | DETs 20-50 | DETs 51+ |
|--------------|------|-----------|------------|----------|
| **Low** | 1 | 5 | 5 | 7 |
| **Average** | 2-5 | 5 | 7 | 10 |
| **High** | 6+ | 7 | 10 | 10 |

**Voorbeelden**:
- Externe API's (read-only)
- SOAP/REST services van derden
- Gedeelde databases (alleen lezen)

```
EIF Identificatie Checklist:
□ Wordt NIET onderhouden door de applicatie
□ Wordt WEL gelezen door de applicatie
□ Is eigendom van extern systeem
```

### 3. EI - External Input (3-6 FP)

**Definitie**: Elementair proces dat data van buiten de applicatie grenzen ontvangt en verwerkt.

| Complexiteit | FTRs | DETs 1-4 | DETs 5-15 | DETs 16+ |
|--------------|------|----------|-----------|----------|
| **Low** | 0-1 | 3 | 3 | 4 |
| **Average** | 2 | 3 | 4 | 6 |
| **High** | 3+ | 4 | 6 | 6 |

**Voorbeelden**:
- Form submissions
- File uploads
- API POST/PUT/DELETE endpoints
- Message queue consumers

```
EI Identificatie Checklist:
□ Komt van buiten de applicatie
□ Wijzigt ILF of gedrag
□ Is elementair (volledig, zelfstandig proces)
□ Bevat business logica
```

### 4. EO - External Output (4-7 FP)

**Definitie**: Elementair proces dat data naar buiten de applicatie grenzen stuurt, met afgeleide data of berekeningen.

| Complexiteit | FTRs | DETs 1-5 | DETs 6-19 | DETs 20+ |
|--------------|------|----------|-----------|----------|
| **Low** | 0-1 | 4 | 4 | 5 |
| **Average** | 2-3 | 4 | 5 | 7 |
| **High** | 4+ | 5 | 7 | 7 |

**Voorbeelden**:
- Rapporten met berekeningen
- Export functies (PDF, Excel)
- Dashboards met aggregaties
- Notificaties met dynamische content

```
EO Identificatie Checklist:
□ Stuurt data naar buiten
□ Bevat BEREKENDE of AFGELEIDE data
□ Is meer dan alleen ophalen (dat is EQ)
```

### 5. EQ - External Inquiry (3-6 FP)

**Definitie**: Elementair proces dat data ophaalt zonder berekeningen of wijzigingen.

| Complexiteit | FTRs | DETs 1-5 | DETs 6-19 | DETs 20+ |
|--------------|------|----------|-----------|----------|
| **Low** | 0-1 | 3 | 3 | 4 |
| **Average** | 2-3 | 3 | 4 | 6 |
| **High** | 4+ | 4 | 6 | 6 |

**Voorbeelden**:
- Zoekfuncties
- Detail pagina's
- API GET endpoints
- Dropdown lijsten

```
EQ Identificatie Checklist:
□ Stuurt data naar buiten
□ Haalt data op ZONDER berekeningen
□ Wijzigt geen ILF
```

---

## Terminology

| Term | Definitie |
|------|-----------|
| **RET** | Record Element Type - Subgroep binnen ILF/EIF |
| **DET** | Data Element Type - Uniek veld/attribuut |
| **FTR** | File Type Referenced - Aantal ILF/EIF dat wordt gebruikt |
| **UFP** | Unadjusted Function Points - Raw count |
| **AFP** | Adjusted Function Points - UFP × VAF |
| **VAF** | Value Adjustment Factor - 0.65-1.35 |

---

## VAF Berekening (14 GSCs)

Value Adjustment Factor wordt berekend via 14 General System Characteristics:

| # | GSC | 0-5 Score |
|---|-----|-----------|
| 1 | Data Communications | Aantal communicatie types |
| 2 | Distributed Data Processing | Gedistribueerde verwerking |
| 3 | Performance | Performance vereisten |
| 4 | Heavily Used Configuration | Hardware beperkingen |
| 5 | Transaction Rate | Transactie volume |
| 6 | Online Data Entry | Online invoer % |
| 7 | End-User Efficiency | Gebruiksvriendelijkheid |
| 8 | Online Update | Online updates |
| 9 | Complex Processing | Complexe verwerking |
| 10 | Reusability | Herbruikbaarheid |
| 11 | Installation Ease | Installatie gemak |
| 12 | Operational Ease | Operationeel gemak |
| 13 | Multiple Sites | Meerdere locaties |
| 14 | Facilitate Change | Flexibiliteit |

**Formule**: `VAF = 0.65 + (Σ GSC × 0.01)`

**Range**: 0.65 (minimaal) tot 1.35 (maximaal)

---

## FP → SP Conversie

### Conversie Ratio's

| Type | Ratio | Toelichting |
|------|-------|-------------|
| **Conservatief** | 1 FP = 0.19-0.25 SP | Legacy code, veel onzekerheid |
| **Standaard** | 1 FP = 0.30-0.40 SP | Normale projecten |
| **Agressief** | 1 FP = 0.50-0.60 SP | Bekende technologie, ervaren team |

### Brown Paper Default

Voor bestaande code analyse (Brown Paper workflow) gebruiken we **Conservative** ratio:

```
SP = FP × 0.19
```

Dit resulteert in hogere Story Points voor dezelfde functionaliteit, wat rekening houdt met:
- Code comprehension overhead
- Legacy code complexity
- Documentatie achterstand
- Test coverage gaps

---

## Brown Paper Code Analysis

### Stap 1: Component Detectie

```python
# Pseudo-code voor automatische FP detectie
def analyze_code(source_code):
    components = {
        'ILF': detect_data_stores(source_code),      # Database tables, config
        'EIF': detect_external_systems(source_code), # API calls, SOAP clients
        'EI': detect_inputs(source_code),            # Form handlers, POST
        'EO': detect_outputs(source_code),           # Reports, exports
        'EQ': detect_queries(source_code),           # GET, searches
    }
    return components
```

### Stap 2: Complexiteit Classificatie

| Pattern | Complexiteit | Indicatoren |
|---------|--------------|-------------|
| Simple CRUD | Low | < 5 velden, 1 tabel |
| Standard ops | Average | 5-15 velden, 2-3 tabellen |
| Complex logic | High | 15+ velden, 4+ tabellen, berekeningen |

### Stap 3: FP Berekening

```python
def calculate_fp(components):
    fp_table = {
        'ILF': {'Low': 7, 'Average': 10, 'High': 15},
        'EIF': {'Low': 5, 'Average': 7, 'High': 10},
        'EI': {'Low': 3, 'Average': 4, 'High': 6},
        'EO': {'Low': 4, 'Average': 5, 'High': 7},
        'EQ': {'Low': 3, 'Average': 4, 'High': 6},
    }

    total_ufp = 0
    for comp_type, items in components.items():
        for item in items:
            total_ufp += fp_table[comp_type][item.complexity]

    return total_ufp
```

---

## Confidence Score Systeem

De automatische analyse genereert een confidence score:

| Score | Level | Actie |
|-------|-------|-------|
| 90-100% | High | Automatisch accepteren |
| 70-89% | Medium | Review aanbevolen |
| 50-69% | Low | Handmatige review vereist |
| < 50% | Very Low | Heranalyse nodig |

### Factoren die Confidence beïnvloeden

| Factor | Impact | Score Modifier |
|--------|--------|----------------|
| Clear patterns | + | +10-20% |
| Documentation | + | +5-15% |
| Test coverage | + | +5-10% |
| Complex logic | - | -10-20% |
| Legacy code | - | -5-15% |
| Dynamic typing | - | -5-10% |

---

## ROM Module Voorbeeld

### Analyse Resultaat (HCI-CRS ROM)

| Component | Type | Complexity | FP |
|-----------|------|------------|-----|
| Amacura interface | EIF | Average | 7 |
| NetQ interface | EIF | Average | 7 |
| Telepsy interface | EIF | Average | 7 |
| BergOp interface | EIF | Low | 5 |
| QuestPro interface | EIF | Low | 5 |
| VitalHealth interface | EIF | Low | 5 |
| MijnIndigo interface | EIF | Low | 5 |
| ROM test records | ILF | Average | 10 |
| Non-response reasons | ILF | Low | 7 |
| ClientInfo data | ILF | Average | 10 |
| CSV bulk import | EI | High | 6 |
| Provider selection | EI | Average | 4 |
| Delete test | EI | Average | 4 |
| ... | ... | ... | ... |
| **Totaal UFP** | | | **173** |
| **VAF** | | | **1.05** |
| **AFP** | | | **182** |
| **SP (×0.19)** | | | **34** |

---

## API Integration

### Request FP Analysis

```http
POST /api/brown-paper/analyze
Content-Type: application/json

{
  "application_id": 1,
  "paths": ["src/EPD/WEB/ROM/"],
  "include_subfolders": true,
  "confidence_threshold": 70
}
```

### Response

```json
{
  "analysis_id": "abc123",
  "total_ufp": 173,
  "vaf": 1.05,
  "total_afp": 182,
  "estimated_sp": 34,
  "confidence_score": 85,
  "components": {
    "ILF": [{"name": "ROM test records", "complexity": "Average", "fp": 10}],
    "EIF": [{"name": "Telepsy service", "complexity": "High", "fp": 10}],
    "EI": [{"name": "CSV import", "complexity": "High", "fp": 6}],
    "EO": [{"name": "Excel export", "complexity": "Average", "fp": 5}],
    "EQ": [{"name": "Test lookup", "complexity": "Low", "fp": 3}]
  },
  "low_confidence_items": [
    {"component": "Complex parsing", "score": 65, "reason": "Dynamic logic"}
  ]
}
```

---

## Best Practices

### DO's

1. **Tel alleen unieke functionaliteit** - Geen duplicaten voor vergelijkbare operaties
2. **Gebruik consistente complexiteit** - Zelfde criteria voor alle componenten
3. **Documenteer aannames** - Vooral bij twijfelgevallen
4. **Valideer met experts** - Bij lage confidence scores
5. **Itereer** - Verbeter schattingen met historische data

### DON'Ts

1. **Tel geen technische implementatie** - FP meet functionaliteit, niet code
2. **Geen batch als meerdere** - Batch = 1 transactie
3. **Geen generiek tellen** - Elke unieke functie telt apart
4. **Niet blind automatiseren** - Altijd review bij lage confidence

---

## References

- IFPUG CPM 4.3.1 Manual
- ISO/IEC 20926:2009
- [IFPUG Website](https://www.ifpug.org/)
- [NESMA Guidelines](https://www.nesma.org/)

---

**Last Updated**: 2025-11-28
**Version**: 1.0
**Generated By**: MarQed Agent SD Platform - Brown Paper Workflow
