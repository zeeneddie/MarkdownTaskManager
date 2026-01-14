# ISO Certificering Roadmap
## Pragmatische aanpak voor 1-2 personen

---

## Jouw Situatie

| Factor | Status | Impact op aanpak |
|--------|--------|------------------|
| Teamgrootte nu | 1 persoon | Alle rollen gecombineerd |
| Teamgrootte straks | 2 personen | Kruislings reviewen mogelijk |
| Beschikbare tijd | Beperkt | Focus op essentials |
| Budget | Proportioneel | Geen enterprise tooling |

---

## Aanbevolen Volgorde

```
NIET: ISO 9001 → ISO 27001 → ISO 42001 (traditioneel)

WEL: ISO 27001 → ISO 42001 → ISO 9001 (strategisch)
     ─────────────────────────────────────────────────
     Hoogste      AI-differentiator   Alleen als
     marktwaarde  + EU AI Act prep    klanten vragen
```

**Waarom deze volgorde?**
- ISO 27001 wordt gevraagd door 80% van enterprise-klanten
- ISO 42001 is zeldzaam (<5% heeft het) - competitief voordeel
- ISO 9001 is "commodity" - minder onderscheidend voor tech

---

## Visuele Roadmap (12-18 maanden)

```
2026                                              2027
Q1          Q2          Q3          Q4            Q1
Jan-Mar     Apr-Jun     Jul-Sep     Okt-Dec       Jan-Mar
│           │           │           │             │
├───────────┼───────────┼───────────┼─────────────┤
│           │           │           │             │
│ ████████████████████████                        │
│ FASE 1: ISO 27001                               │
│ Maand 1-8                                       │
│           │           ↓ CERT                    │
│           │                                     │
│           │   ████████████████████              │
│           │   FASE 2: ISO 42001                 │
│           │   Maand 5-11                        │
│           │           │           ↓ CERT        │
│           │           │                         │
│           │           │       ██████████████████│
│           │           │       FASE 3: ISO 9001  │
│           │           │       (optioneel)       │
│           │           │       Maand 10-16       │
│           │           │                   ↓ CERT│
│           │           │                         │
└───────────┴───────────┴───────────┴─────────────┘
     ↑               ↑
   SOLO          +1 COLLEGA
   (jij)         (schaalt op)
```

---

## Fase 0: Fundament (Week 1-2)

**Doel:** Eenmalige opzet van gedeelde basis

### Acties

| # | Actie | Tijd | Output |
|---|-------|------|--------|
| 0.1 | Kies centrale tool (Notion/Obsidian) | 2u | Werkruimte ingericht |
| 0.2 | Maak mappenstructuur | 1u | Folder template |
| 0.3 | Schrijf context-document | 2u | Wie zijn we, wat doen we |
| 0.4 | Inventariseer huidige situatie | 4u | Gap-overzicht |

### Minimale Folder Structuur

```
📁 Management Systeem/
├── 📄 Context_en_Beleid.md          ← 1 document voor alles
├── 📁 Risicos/
│   └── 📊 Risicoregister.xlsx       ← Geïntegreerd voor alle normen
├── 📁 Processen/
│   └── 📄 Kernprocessen.md          ← Max 5 processen beschreven
├── 📁 Evidence/
│   ├── 📁 Audits/
│   ├── 📁 Reviews/
│   └── 📁 Incidenten/
└── 📁 Certificering/
    └── 📁 Audit_Rapporten/
```

---

## Fase 1: ISO 27001 (Maand 1-8)

### Waarom eerst?
- Hoogste ROI voor tech/AI-bedrijven
- Bouwt security-fundament voor ISO 42001
- Dwingt je om basis op orde te krijgen

### Maand-voor-maand

```
M1          M2          M3          M4          M5          M6          M7          M8
├───────────┼───────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│           │           │           │           │           │           │           │
│ SCOPE &   │ RISICO    │ CONTROLS  │ IMPLEMENT │ IMPLEMENT │ INTERN    │ PREP      │ AUDIT
│ BELEID    │ ANALYSE   │ SELECTIE  │ TECHNISCH │ PROCEDUR. │ AUDIT     │ EXTERN    │ CERT.
│           │           │           │           │           │           │           │
│ • ISMS    │ • Assets  │ • SoA     │ • MFA     │ • Policies│ • Zelf of │ • Fixes   │ • Stage 1
│   scope   │   lijst   │   maken   │ • Backup  │ • Incident│   extern  │ • Evidence│ • Stage 2
│ • Beleid  │ • Threats │ • Risk    │ • Encrypt │   proces  │   auditor │   compleet│ • Cert!
│   draft   │ • Risico's│   treat-  │ • Endpoint│ • Access  │ • Rapport │           │
│           │   scoren  │   ment    │   security│   control │ • NCR's   │           │
│           │           │           │           │           │   fixen   │           │
└───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
 8-12u       12-16u      8-12u       16-24u      12-16u      8-16u       8u          Audit
```

### Verplichte Documenten (minimum)

| Document | Omvang | Template |
|----------|--------|----------|
| ISMS Scope | 1/2 A4 | "Scope omvat alle informatiesystemen van [bedrijf] voor [diensten]" |
| Informatiebeveiligingsbeleid | 1 A4 | Commitment + principes + verantwoordelijkheden |
| Risicobeoordeling | Excel | Asset → Dreiging → Risico → Maatregel |
| Statement of Applicability | Excel | 93 controls: Ja/Nee/N.v.t. + onderbouwing |
| Risk Treatment Plan | 1-2 A4 | Welke maatregelen, wanneer, door wie |
| Incident Response Procedure | 1 A4 | Detect → Respond → Learn |

### Controls die je WEL nodig hebt (micro-bedrijf)

```
MUST-HAVE CONTROLS (focus hierop):
├── A.5.1  Policies for information security
├── A.5.15 Access control
├── A.5.24 Incident management planning
├── A.5.29 Information security during disruption
├── A.5.31 Legal, regulatory requirements
├── A.8.1  User endpoint devices
├── A.8.5  Secure authentication
├── A.8.7  Protection against malware
├── A.8.13 Information backup
├── A.8.24 Use of cryptography
└── A.8.9  Configuration management
```

### Controls die NIET van toepassing zijn (1-2 personen)

```
VAAK N.V.T. (documenteer waarom in SoA):
├── A.6.1  Screening (geen personeel)
├── A.6.4  Disciplinary process (geen personeel)
├── A.6.5  Responsibilities after termination
├── A.7.*  Physical security (thuiswerker niveau)
├── A.5.9  Inventory of information (kan minimaal)
└── A.8.25-8.34 Secure development (alleen als je ontwikkelt)
```

### Sturingsinstrumenten Fase 1

| Instrument | Frequentie | Tijdsinvestering | Tool |
|------------|------------|------------------|------|
| Security log check | Wekelijks | 15 min | Spreadsheet |
| Incident registratie | Bij voorval | 10 min | Notion/Excel |
| Risico review | Maandelijks | 30 min | Excel |
| Management review | Kwartaal | 1 uur | Notities in Notion |
| Interne audit | Jaarlijks | 8-12 uur | Checklist |

---

## Fase 2: ISO 42001 (Maand 5-11)

### Waarom overlappen met Fase 1?
- Bouwt voort op ISO 27001 security-basis
- Veel gedeelde controls en processen
- Efficiënter dan sequentieel

### Maand-voor-maand (start maand 5)

```
M5          M6          M7          M8          M9          M10         M11
├───────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│           │           │           │           │           │           │
│ AI INVENT │ IMPACT    │ GOVERNANCE│ MONITORING│ INTERN    │ PREP      │ AUDIT
│ & SCOPE   │ ASSESS    │ IMPLEMENT │ SETUP     │ AUDIT     │ EXTERN    │ CERT.
│           │           │           │           │           │           │
│ • AI      │ • Per AI  │ • Bias    │ • Model   │ • AIMS    │ • Fixes   │ • Audit
│   systemen│   systeem │   checks  │   drift   │   audit   │ • Evidence│ • Cert!
│   lijst   │ • Risico's│ • Human-  │ • KPI's   │           │           │
│ • AIMS    │ • Fairness│   in-loop │ • Alerts  │           │           │
│   scope   │ • Privacy │ • Trans-  │           │           │           │
│           │           │   parantie│           │           │           │
└───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
 8-12u       12-16u      12-16u      8-12u       6-8u        4u          Audit
```

### Verplichte Documenten (minimum)

| Document | Omvang | Inhoud |
|----------|--------|--------|
| AIMS Scope | 1/2 A4 | Welke AI-systemen vallen eronder |
| AI Beleid | 1 A4 | Principes voor verantwoord AI-gebruik |
| AI Systeem Register | Excel | Lijst van alle AI-systemen + classificatie |
| Impact Assessment | Per systeem | Risico's voor individuen/maatschappij |
| Human Oversight Procedure | 1 A4 | Hoe blijft mens in control |
| Bias Monitoring Aanpak | 1 A4 | Hoe detecteer je oneerlijke uitkomsten |

### AI Systeem Classificatie

```
┌────────────────────────────────────────────────────────────┐
│ VRAAG: Gebruik je AI of ontwikkel je AI?                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ALLEEN GEBRUIKER (bijv. ChatGPT, Copilot, API's)          │
│ ├── Focus: Vendor due diligence                           │
│ ├── Focus: Usage policies                                  │
│ ├── Focus: Data naar AI-systemen                          │
│ └── Minder: Development lifecycle                          │
│                                                            │
│ ONTWIKKELAAR (eigen modellen/fine-tuning)                 │
│ ├── Volledige lifecycle documentatie                      │
│ ├── Training data governance                               │
│ ├── Model versioning                                       │
│ └── Uitgebreide impact assessments                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Sturingsinstrumenten Fase 2

| Instrument | Frequentie | Tijdsinvestering | Tool |
|------------|------------|------------------|------|
| AI performance check | Wekelijks | 15 min | Dashboard/logs |
| Bias monitoring | Maandelijks | 30 min | Metrics review |
| AI incident registratie | Bij voorval | 15 min | Notion/Excel |
| Impact assessment review | Kwartaal | 1 uur | Document review |

---

## Fase 3: ISO 9001 (Optioneel - Maand 10-16)

### Alleen doen als:
- Klanten het expliciet vragen
- Je aanbestedingen wilt doen
- Je team groeit naar 3+ personen

### Wat je al hebt na Fase 1 & 2:
- 70% van ISO 9001 is al gedekt
- Context, beleid, risico's, audits, reviews
- Procesdenken, documentbeheer, verbetering

### Extra nodig voor ISO 9001:

| Document | Omvang | Nieuw werk |
|----------|--------|------------|
| Kwaliteitsdoelstellingen | 1/2 A4 | Minimaal |
| Klanttevredenheid meting | Methode | Enquête opzetten |
| Leveranciersbeoordeling | Excel | Indien relevant |
| Product/dienst vrijgave | Criteria | Indien relevant |

---

## Geïntegreerd Sturingssysteem

### Voor 1 persoon (nu)

```
┌────────────────────────────────────────────────────────────┐
│  WEKELIJKS RITME (30 minuten - vrijdagmiddag)             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  □ Security check                                          │
│    └── Backup OK? Verdachte activiteit? Patches?          │
│                                                            │
│  □ AI check (zodra relevant)                               │
│    └── Model performance OK? Feedback van gebruikers?     │
│                                                            │
│  □ Incidenten deze week?                                   │
│    └── Zo ja: loggen en actie bepalen                     │
│                                                            │
│  □ Notitie in weeklog                                      │
│    └── 2-3 zinnen: wat speelde er?                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Voor 2 personen (straks)

```
┌────────────────────────────────────────────────────────────┐
│  WEKELIJKS RITME (45 minuten - vrijdagmiddag)             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  PERSOON 1 (Security Lead)          PERSOON 2 (AI Lead)   │
│  ────────────────────────           ───────────────────    │
│  □ Security monitoring              □ AI monitoring        │
│  □ Access review                    □ Bias checks          │
│  □ Incident triage                  □ Model performance    │
│                                                            │
│  SAMEN (15 min sync)                                       │
│  ─────────────────────                                     │
│  □ Incidenten bespreken                                    │
│  □ Kruislings review (A checkt B's werk)                  │
│  □ Weeklog bijwerken                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Maandelijks

```
┌────────────────────────────────────────────────────────────┐
│  MAANDELIJKSE REVIEW (1 uur - laatste vrijdag)            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  □ Risico register doornemen                               │
│    └── Nieuwe risico's? Risico's verdwenen?               │
│                                                            │
│  □ KPI's checken                                           │
│    └── Security: incidenten, uptime                       │
│    └── AI: performance, bias metrics                      │
│    └── Kwaliteit: klanttevredenheid (indien 9001)         │
│                                                            │
│  □ Documentatie nog actueel?                               │
│    └── Processen veranderd? Policies nog kloppend?        │
│                                                            │
│  □ Training/learning                                       │
│    └── Iets nieuws geleerd? Vastleggen.                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Kwartaal (Management Review)

```
┌────────────────────────────────────────────────────────────┐
│  KWARTAAL REVIEW (2 uur)                                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  AGENDA:                                                   │
│  1. Status van acties vorige review (10 min)              │
│  2. Incidenten & non-conformiteiten (15 min)              │
│  3. Risico's: nieuwe, gewijzigde, gesloten (20 min)       │
│  4. Doelstellingen: voortgang (15 min)                    │
│  5. Feedback stakeholders/klanten (15 min)                │
│  6. Verbetermogelijkheden (15 min)                        │
│  7. Beslissingen & acties (20 min)                        │
│                                                            │
│  OUTPUT:                                                   │
│  • Notities (= bewijs voor auditor)                       │
│  • Actielijst met eigenaar + deadline                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Tooling Aanbeveling

### Gratis / Goedkoop Stack

```
┌────────────────────────────────────────────────────────────┐
│  CENTRALE HUB: Notion (gratis/€8-10/mnd)                  │
├────────────────────────────────────────────────────────────┤
│  • Policies & procedures (pages)                          │
│  • Risk register (database)                                │
│  • Incident log (database)                                 │
│  • Meeting notes (pages)                                   │
│  • Audit checklists (templates)                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ALTERNATIEF: Obsidian + Git (gratis)                     │
│  • Markdown files in Git repo                              │
│  • Automatische versiegeschiedenis                         │
│  • Werkt offline                                           │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  SECURITY TOOLING                                          │
├────────────────────────────────────────────────────────────┤
│  • Bitwarden (gratis/€10/jaar) - wachtwoordbeheer         │
│  • Backblaze B2 (€5-10/mnd) - backup                      │
│  • Cloudflare (gratis) - basis security                   │
│  • GitHub (gratis) - code + versioning                    │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  MONITORING                                                │
├────────────────────────────────────────────────────────────┤
│  • UptimeRobot (gratis) - uptime monitoring               │
│  • Sentry (gratis tier) - error tracking                  │
│  • Simple Analytics (€9/mnd) - privacy-friendly analytics │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Wat je NIET nodig hebt
- GRC platforms (ServiceNow, OneTrust) → €€€€
- Enterprise ISMS software → overkill
- Dedicated audit management → spreadsheet volstaat
- Compliance automation (Vanta/Drata) → pas bij 5+ mensen

---

## Kosten Overzicht

### Scenario: ISO 27001 + ISO 42001

```
┌────────────────────────────────────────────────────────────┐
│  JAAR 1 - INITIËLE CERTIFICERING                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Certificeringsaudits                                      │
│  ├── ISO 27001 (Stage 1 + 2)         €3.000 - 5.000       │
│  └── ISO 42001 (Stage 1 + 2)         €3.500 - 6.000       │
│                                       ─────────────────    │
│                                       €6.500 - 11.000      │
│                                                            │
│  Consultancy (optioneel maar slim)                        │
│  └── Gap analysis + begeleiding      €3.000 - 6.000       │
│                                                            │
│  Tooling                                                   │
│  └── Notion + Bitwarden + Backup     €300 - 600/jaar      │
│                                                            │
│  ═══════════════════════════════════════════════════════   │
│  TOTAAL JAAR 1:                      €10.000 - 18.000     │
│  + eigen tijd:                       150-250 uur          │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  JAAR 2+ - ONDERHOUD                                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Surveillance audits                                       │
│  ├── ISO 27001                       €1.500 - 2.500       │
│  └── ISO 42001                       €1.500 - 2.500       │
│                                       ─────────────────    │
│                                       €3.000 - 5.000       │
│                                                            │
│  Tooling                             €300 - 600/jaar      │
│                                                            │
│  ═══════════════════════════════════════════════════════   │
│  TOTAAL PER JAAR:                    €3.500 - 6.000       │
│  + eigen tijd:                       50-80 uur/jaar       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Eerste 30 Dagen - Concrete Acties

### Week 1
- [ ] Kies tooling (Notion of Obsidian)
- [ ] Maak folder structuur
- [ ] Schrijf context document (wie zijn we)
- [ ] Begin asset inventaris

### Week 2
- [ ] Schrijf ISMS scope (1/2 A4)
- [ ] Draft informatiebeveiligingsbeleid
- [ ] Inventariseer AI-systemen (welke gebruik/bouw je)
- [ ] Start risico-identificatie

### Week 3
- [ ] Completeer risico-analyse (top 10 risico's)
- [ ] Begin Statement of Applicability
- [ ] Implementeer basis security (MFA, backup check)
- [ ] Draft incident response procedure

### Week 4
- [ ] Completeer SoA (alle 93 controls: ja/nee/n.v.t.)
- [ ] Maak risk treatment plan
- [ ] Plan eerste kwartaal-review
- [ ] Contacteer certification body voor offerte

---

## Checklist: Ben je klaar voor audit?

### ISO 27001

- [ ] Scope gedocumenteerd
- [ ] Beleid goedgekeurd
- [ ] Risicobeoordeling uitgevoerd
- [ ] SoA compleet met onderbouwing
- [ ] Risk treatment plan aanwezig
- [ ] Minimaal 3 maanden "evidence" verzameld
- [ ] Interne audit uitgevoerd
- [ ] Management review gehouden
- [ ] Non-conformiteiten behandeld

### ISO 42001

- [ ] AIMS scope gedocumenteerd
- [ ] AI beleid goedgekeurd
- [ ] AI systeem inventaris compleet
- [ ] Impact assessments per systeem
- [ ] Bias monitoring ingericht
- [ ] Human oversight mechanismen beschreven
- [ ] Interne audit AIMS uitgevoerd
- [ ] Management review AIMS gehouden

---

## Contact Certification Bodies (NL/BE)

| Organisatie | Website | Opmerking |
|-------------|---------|-----------|
| DEKRA | dekra.nl | Vaak scherp geprijsd |
| TÜV Nederland | tuv.nl | Bekend, breed portfolio |
| BSI | bsigroup.com | Internationaal erkend |
| Brand Compliance | brandcompliance.com | Gespecialiseerd in klein MKB |
| Kiwa | kiwa.com | Nederlands, pragmatisch |

**Tip:** Vraag offertes bij minimaal 3 partijen. Prijsverschillen van 30-50% zijn normaal.

---

*Document versie: 1.0*
*Gemaakt: Januari 2026*
*Voor: Micro-onderneming (1-2 personen)*
