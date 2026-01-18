# marqed.ai SP-FP Conversie Methodiek

**Versie:** 1.0
**Datum:** 15 januari 2025
**Status:** ACTIEF
**Auteur:** marqed.ai Platform Team

---

## 1. Aanleiding

Bij security maintenance, bug fixes en technische refactoring meet IFPUG Function Point Analysis vaak **0 FP**, terwijl er wel significante werkzaamheden nodig zijn. Dit creëert een **scheve verhouding** tussen meetbare functionaliteit en daadwerkelijke effort.

### 1.1 Het Probleem

```
┌─────────────────────────────────────────────────────────────────────┐
│  IFPUG FP-ANALYSE BEPERKING                                        │
│                                                                     │
│  IFPUG meet alleen USER-VISIBLE functionaliteit:                   │
│  - Nieuwe schermen (EI/EO/EQ)                                      │
│  - Nieuwe databestanden (ILF/EIF)                                  │
│                                                                     │
│  IFPUG meet NIET:                                                  │
│  - Bug fixes (0 FP)                                                │
│  - Security patches (0 FP)                                         │
│  - Algoritme verbeteringen (0 FP)                                  │
│  - Interne refactoring (0 FP)                                      │
│                                                                     │
│  RESULTAAT: 0 FP ≠ 0 werk                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Praktijkvoorbeeld (CVD-2025-001)

| Kwetsbaarheid | IFPUG FP | Werkelijke Uren | Ratio |
|---------------|----------|-----------------|-------|
| CWE-337 Predictable Tokens | **0 FP** | 4 uur | ∞ |
| CWE-602 Security Bypass | **0 FP** | 3 uur | ∞ |
| CWE-521 Weak Password | **0 FP** | 5 uur | ∞ |
| DoS Account Recovery | 1-2 FP | 8 uur | 4-8:1 |

**Conclusie:** IFPUG alleen is onvoldoende voor maintenance/security werk.

---

## 2. De Oplossing: SP-FP Conversie

### 2.1 Wanneer Toepassen?

De SP-FP conversie wordt toegepast wanneer:

1. **IFPUG meet 0 FP** maar er is reëel ontwikkelwerk
2. **Scheve verhouding** tussen FP en uren (ratio > 5:1)
3. **Maintenance werk** zonder nieuwe user-visible functionaliteit
4. **Security fixes** die interne implementatie wijzigen

### 2.2 Conversie Formules

```
┌─────────────────────────────────────────────────────────────────────┐
│  MARQED.AI SP-FP CONVERSIE                                         │
│                                                                     │
│  Stap 1: Story Points bepalen                                      │
│  ─────────────────────────────────                                 │
│  SP = f(complexiteit, onzekerheid, afhankelijkheden)               │
│                                                                     │
│  Stap 2: Uren berekenen                                            │
│  ─────────────────────────────────                                 │
│  Uren = SP × 2 uur/SP (conservatieve schatting)                    │
│                                                                     │
│  Stap 3: FP equivalent bepalen                                     │
│  ─────────────────────────────────                                 │
│  FP_eq = Uren ÷ 3 uur/FP (ISBSG benchmark)                         │
│                                                                     │
│  Vereenvoudigd:                                                    │
│  FP_eq ≈ SP × 0.67 (conservatieve conversie)                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Conversie Constanten

| Parameter | Waarde | Bron |
|-----------|--------|------|
| **1 SP** | 2-4 uur | Agile benchmark (gemiddeld team) |
| **1 SP** | **2 uur** (conservatief) | marqed.ai standaard |
| **1 FP** | 3 uur | ISBSG industry benchmark |
| **SP:FP ratio** | **0.67:1** | Afgeleide (2÷3) |

> **Noot:** marqed.ai hanteert bewust een **conservatieve** conversie van 2 uur/SP om overschatting te voorkomen bij maintenance werk.

---

## 3. Story Points Schaal

### 3.1 Fibonacci Schaal (Aanbevolen)

| SP | Complexiteit | Uren (range) | Typische Voorbeelden |
|----|--------------|--------------|----------------------|
| 1 | Triviaal | 2-4 uur | 1-2 regels code, simpele bug fix |
| 2 | Laag | 4-8 uur | Bekende oplossing, 1 component |
| 3 | Laag-Medium | 6-12 uur | Meerdere bestanden, standaard patroon |
| 5 | Medium | 10-20 uur | Nieuwe flow, design beslissingen |
| 8 | Medium-Hoog | 16-32 uur | Cross-component, integratie |
| 13 | Hoog | 26-52 uur | Architectuur impact, onzekerheden |

### 3.2 Factoren voor SP Bepaling

| Factor | Verhoogt SP | Verlaagt SP |
|--------|-------------|-------------|
| Bekendheid oplossing | - | ✓ |
| Aantal bestanden | ✓ | - |
| Cross-component afhankelijkheden | ✓ | - |
| Test complexiteit | ✓ | - |
| Design beslissingen nodig | ✓ | - |
| Documentatie vereist | ✓ | - |
| Bekende patronen | - | ✓ |

---

## 4. Toepassing in Rapportages

### 4.1 Rapportage Structuur

Elke rapportage met 0 FP (of scheve ratio) bevat een extra sectie:

```markdown
## X. Story Points Analyse

### X.1 Story Point Schatting

| Metric | Waarde |
|--------|--------|
| **Story Points** | **N SP** |
| Complexiteit | [Triviaal/Laag/Medium/Hoog] |
| Onzekerheid | [Geen/Laag/Medium/Hoog] |
| Team niveau | Gemiddeld tot ervaren |

### X.2 Onderbouwing

| Factor | Beoordeling |
|--------|-------------|
| [Factor 1] | [✅/⚠️] [Toelichting] |
| [Factor 2] | [✅/⚠️] [Toelichting] |

### X.3 SP-FP Conversie (marqed.ai Methodiek)

| Conversie | Berekening |
|-----------|------------|
| Story Points | N SP |
| Uren equivalent | N SP × 3 uur = **X uur** |
| FP equivalent | X uur ÷ 3 uur/FP = **Y FP equivalent** |
```

### 4.2 Communicatie naar Klanten

Bij facturatie of offertes:

```
┌─────────────────────────────────────────────────────────────────────┐
│  KLANT COMMUNICATIE                                                │
│                                                                     │
│  "De IFPUG functiepunten analyse meet 0 FP voor deze security      │
│  fix omdat het een interne implementatie wijziging betreft zonder  │
│  nieuwe user-visible functionaliteit.                              │
│                                                                     │
│  Om de daadwerkelijke effort te reflecteren, past marqed.ai de    │
│  SP-FP conversie toe:                                              │
│                                                                     │
│  - Story Points: 2 SP                                              │
│  - Uren equivalent: 6 uur                                          │
│  - FP equivalent: 2 FP                                             │
│                                                                     │
│  Dit is conform de marqed.ai SP-FP Conversie Methodiek v1.0."     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Validatie & Governance

### 5.1 Dubbele Validatie

Elke SP-FP conversie wordt gevalideerd door:

1. **marqed.ai FP Analyst** - Initiële schatting
2. **AI Verificatie** (Codex/Claude) - Onafhankelijke controle
3. **Peer Review** - Bij >5 SP of controversiële cases

### 5.2 Audit Trail

Voor elke conversie wordt vastgelegd:

| Veld | Beschrijving |
|------|--------------|
| Datum | Datum van schatting |
| IFPUG FP | Originele FP meting |
| Story Points | SP schatting |
| FP Equivalent | Berekende FP equivalent |
| Validatoren | Wie heeft gevalideerd |
| Onderbouwing | Rationale voor SP keuze |

---

## 6. Totaaloverzicht CVD-2025-001

### 6.1 Vergelijking IFPUG vs SP-FP (Conservatieve Conversie)

| Kwetsbaarheid | IFPUG FP | SP | Uren (SP×2) | FP Equivalent |
|---------------|----------|-----|-------------|---------------|
| CWE-337 Predictable Tokens | 0 | 2 | 4 | 1.3 |
| CWE-602 Security Bypass | 0 | 1 | 2 | 0.7 |
| CWE-521 Weak Password | 0 | 3 | 6 | 2.0 |
| DoS Account Recovery | 1-2 | 5 | 10 | 3.3 |
| **Totaal** | **1-2 FP** | **11 SP** | **22 uur** | **7 FP eq** |

### 6.2 Conclusie

| Methode | Resultaat | Uren Equivalent |
|---------|-----------|-----------------|
| IFPUG alleen | 1-2 FP | 3-6 uur |
| SP-FP Conversie (conservatief) | **7 FP equivalent** | **22 uur** |
| Realistische schatting | - | 27-39 uur |

> **Noot:** De conservatieve SP-FP conversie (7 FP eq) ligt onder de realistische schatting (27-39 uur), wat bevestigt dat de conversie voorzichtig is en geen overschatting geeft.

**De SP-FP conversie geeft een veel realistischer beeld van de werkelijke effort.**

---

## 7. Referenties

| Bron | Beschrijving |
|------|--------------|
| IFPUG CPM 4.3.1 | Function Point Counting Practices Manual |
| ISBSG | Industry benchmark: 1 FP ≈ 3 uur |
| Agile Alliance | Story Points best practices |
| COSMIC-FFP | Alternatieve sizing methode (voor toekomstig onderzoek) |

---

## 8. Versiebeheer

| Versie | Datum | Wijzigingen | Auteur |
|--------|-------|-------------|--------|
| 1.0 | 15-01-2025 | Initiële versie | marqed.ai |

---

*Dit document is eigendom van marqed.ai en mag worden gebruikt voor klantcommunicatie.*
