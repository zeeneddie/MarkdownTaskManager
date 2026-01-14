# ISO Procedures - Schaalbaar van 1-10 personen
## Minimaal maar compliant

---

## Ontwerpprincipes

```
1. Eén procedure = één A4 (max)
2. Geen procedures voor vanzelfsprekende zaken
3. Automatiseer waar mogelijk
4. Schaal op met rollen, niet met documenten
5. Wekelijkse check van 30 min is het maximum
```

---

## Schaalniveaus

| Fase | Teamgrootte | Aanpak |
|------|-------------|--------|
| **Start** | 1-2 | Alles zelf, minimale admin |
| **Groei** | 3-5 | Rollen toewijzen, kruislings review |
| **Schaal** | 6-10 | Leads per domein, centrale coördinatie |

---

## PROCEDURE 1: Documentbeheer

**Doel:** Weten welke versie geldig is

### Hoe (alle schalen)

```
Bestandsnaam conventie:
[Naam]_v[versie].md

Voorbeeld:
ISMS-Beleid_v1.2.md

Dat is alles.
```

**Geen apart register nodig** - versiegeschiedenis zit in bestandsnaam + Git/Notion history.

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| Iedereen mag wijzigen | Eigenaar per document | Goedkeuring door Lead |

---

## PROCEDURE 2: Risicobeheer

**Doel:** Weten wat je risico's zijn en wat je eraan doet

### Hoe

**Eén spreadsheet, vier kolommen die ertoe doen:**

| Risico | Impact (1-5) | Maatregel | Eigenaar |
|--------|--------------|-----------|----------|
| Laptop kwijt | 5 | Encryptie + backup + remote wipe | [Naam] |
| API-key lekt | 4 | Secrets manager + rotatie | [Naam] |
| Phishing | 3 | MFA + awareness | Allen |

**Frequentie:**
- Toevoegen: bij nieuwe situatie
- Review: kwartaal (15 min scan)
- Volledig: jaarlijks

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| 1 register | 1 register + eigenaren | Risk owner per domein |

---

## PROCEDURE 3: Toegangsbeheer

**Doel:** Juiste mensen, juiste rechten

### Hoe

**Eén tabel:**

| Systeem | Wie | Niveau | Sinds | Review |
|---------|-----|--------|-------|--------|
| AWS | Anna | Admin | Jan-26 | Apr-26 |
| GitHub | Bob | Write | Feb-26 | Mei-26 |

**Regels:**
1. Nieuwe toegang → tabel updaten
2. Vertrek → dezelfde dag rechten intrekken
3. Kwartaal → tabel doorlopen: "nog nodig?"

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| Alles zichtbaar | Per systeem eigenaar | IT beheert centraal |

---

## PROCEDURE 4: Incidenten

**Doel:** Leren van wat misgaat

### Hoe

**Bij een incident:**

```
1. Los het op
2. Log in 1 minuut:

| Wanneer | Wat | Hoe opgelost | Leren we iets? |
|---------|-----|--------------|----------------|
| 10-feb  | Phishing mail | Geblokkeerd | Filter aanscherpen |
```

**Dat is alles voor 90% van de incidenten.**

**Bij ernstig incident (datalek, hack):**
- Uitgebreidere analyse
- Tijdlijn documenteren
- Root cause bepalen
- Melden aan AP indien datalek (72 uur)

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| Zelf loggen | Centraal loggen | Incident manager |

---

## PROCEDURE 5: Interne Audit

**Doel:** Controleren of je systeem werkt

### Hoe

**Eén keer per jaar, 4-8 uur totaal:**

1. Pak checklist (zie onder)
2. Loop door per onderdeel
3. Noteer: OK / Niet OK / Verbeterpunt
4. Maak actielijst van Niet OK

**Checklist kernpunten:**

```
□ Beleid actueel en bekend?
□ Risico's recent beoordeeld?
□ Toegang alleen voor wie nodig?
□ Backups werken en getest?
□ Incidenten gelogd?
□ Training/awareness gedaan?
□ Leveranciers beoordeeld?
□ AI-systemen geïnventariseerd? (42001)
□ Bias checks uitgevoerd? (42001)
```

### Wie auditeert?

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| Extern of peer | Kruislings | Interne auditor |

**Optie extern:** €500-1500 voor pre-audit

---

## PROCEDURE 6: Management Review

**Doel:** Directie kijkt of systeem effectief is

### Hoe

**Per kwartaal, 30-60 minuten:**

```markdown
## Management Review Q[X] 2026

**Datum:** [datum]
**Aanwezig:** [namen]

### Incidenten afgelopen kwartaal
- [Lijst of "geen"]

### Risico's - wijzigingen
- [Nieuwe risico's of "geen wijzigingen"]

### Resultaten
- Security: [# incidenten, status]
- AI: [performance OK/niet OK]
- Klanten: [feedback]

### Acties vorige keer
| Actie | Status |
|-------|--------|
| [X] | Afgerond/Open |

### Nieuwe acties
| Actie | Wie | Wanneer |
|-------|-----|---------|
| [Y] | [Naam] | [Datum] |

### Beslissingen
- [Eventuele besluiten]
```

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| Solo reflectie (30 min) | Team sync (45 min) | Formele meeting (60 min) |

---

## PROCEDURE 7: Competenties & Training

**Doel:** Bewijs dat je weet wat je doet

### Hoe

**Eén overzicht:**

| Persoon | Rol | Relevante kennis | Bewijs | Laatste training |
|---------|-----|------------------|--------|------------------|
| Anna | Security | ISO 27001, AWS | Cert AWS, Cursus ISO | Dec-25 |
| Bob | AI | ML, Python | MSc, Coursera | Jan-26 |

**Jaarlijks:**
- Security awareness (1-2 uur, online)
- AI ethics (als 42001, 1-2 uur)

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| CV + certificaten | Centrale lijst | Training planning |

---

## PROCEDURE 8: Leveranciers

**Doel:** Weten dat kritieke leveranciers betrouwbaar zijn

### Hoe

**Alleen voor kritieke leveranciers (hosting, data-verwerking):**

| Leverancier | Dienst | Kritiek? | Certificering | Check |
|-------------|--------|----------|---------------|-------|
| AWS | Hosting | Ja | ISO 27001, SOC2 | Jan-26 |
| OpenAI | AI API | Ja | SOC2 | Jan-26 |
| Mailchimp | Email | Nee | - | - |

**Check = jaarlijks:**
- Hebben ze nog certificeringen?
- Zijn er incidenten geweest?
- Is contract/AVG nog actueel?

### Schaling

Blijft hetzelfde - leverancierslijst groeit niet snel.

---

## PROCEDURE 9: AI Governance (ISO 42001)

**Doel:** Verantwoord AI-gebruik

### 9A: AI Register

**Eén lijst:**

| AI Systeem | Type | Leverancier | Doel | Data | Risico |
|------------|------|-------------|------|------|--------|
| ChatGPT | LLM | OpenAI | Content | Geen PII | Laag |
| Eigen model | ML | Zelf | Scoring | Klantdata | Hoog |

### 9B: Impact Assessment

**Per hoog-risico AI, eenmalig + jaarlijkse review:**

```markdown
## AI Impact Assessment: [Naam]

**Systeem:** [Beschrijving]
**Risico niveau:** Hoog

### Risico's
| Risico | Maatregel |
|--------|-----------|
| Bias in output | Maandelijkse bias check |
| Privacy | Geen PII in training |
| Foutieve beslissing | Human review boven threshold |

### Human oversight
- Confidence < 80% → handmatige review
- Klachten → herbeoordeling door mens

### Monitoring
- Wekelijks: accuracy check
- Maandelijks: bias metrics

**Laatste review:** [Datum]
**Volgende review:** [Datum + 1 jaar]
```

### 9C: Bias Monitoring

**Maandelijks voor hoog-risico (15 min):**

```
□ Accuracy nog OK? (target: >X%)
□ Verschil tussen groepen acceptabel?
□ Klachten ontvangen?
□ Noteer in log
```

### Schaling

| 1-2 pers | 3-5 pers | 6-10 pers |
|----------|----------|-----------|
| AI-eigenaar doet alles | Per AI een eigenaar | AI governance lead |

---

## PROCEDURE 10: Continue Verbetering

**Doel:** Beter worden zonder bureaucratie

### Hoe

**Eén simpele lijst:**

| Datum | Idee | Prioriteit | Status |
|-------|------|------------|--------|
| Feb-26 | Backup automatiseren | Hoog | Open |
| Feb-26 | Betere phishing training | Medium | Gepland |

**Input komt van:**
- Incidenten (wat kunnen we voorkomen?)
- Audits (wat moeten we verbeteren?)
- Team (wat irriteert?)
- Klanten (wat missen ze?)

**Per kwartaal:** Top 3 pakken

### Schaling

Blijft hetzelfde - lijst wordt langer, pakt meer tegelijk.

---

## WEEKRITME (30 min vrijdag)

```
┌─────────────────────────────────────────────────────────┐
│  WEKELIJKSE CHECK                                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  □ Security: Iets verdachts gezien? Alerts?            │
│    → Zo ja: loggen                                      │
│                                                         │
│  □ AI: Output nog OK? Klachten?                        │
│    → Zo ja: loggen                                      │
│                                                         │
│  □ Incidenten: Iets gebeurd deze week?                 │
│    → Zo ja: al gelogd? Check.                          │
│                                                         │
│  □ Klaar                                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Bij 3+ mensen: rouleren

Week 1: Anna checkt
Week 2: Bob checkt
Week 3: Charlie checkt
...

---

## MAANDRITME (1 uur)

```
┌─────────────────────────────────────────────────────────┐
│  MAANDELIJKSE REVIEW                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  □ Risico's: Nieuwe situaties? Oude opgelost?          │
│                                                         │
│  □ Toegang: Nieuwe mensen? Vertrokken?                 │
│                                                         │
│  □ AI monitoring: Bias check (hoog-risico)             │
│                                                         │
│  □ Verbeteracties: Voortgang?                          │
│                                                         │
│  □ Documentatie: Nog actueel?                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## KWARTAALRITME (2 uur)

```
┌─────────────────────────────────────────────────────────┐
│  KWARTAAL: Management Review                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  □ Review template invullen (zie procedure 6)          │
│                                                         │
│  □ Toegangsrechten volledig doorlopen                  │
│                                                         │
│  □ Leveranciers checken                                │
│                                                         │
│  □ Acties vorig kwartaal: status                       │
│                                                         │
│  □ Volgende kwartaal: prioriteiten                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## JAARRITME (16-24 uur verspreid)

```
┌─────────────────────────────────────────────────────────┐
│  JAARLIJKS                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  □ Interne audit (of extern)           8-12 uur        │
│                                                         │
│  □ Risicobeoordeling volledig          2-3 uur         │
│                                                         │
│  □ Beleid reviewen                     1 uur           │
│                                                         │
│  □ Alle AI impact assessments          2-4 uur         │
│                                                         │
│  □ Backup restore test                 1 uur           │
│                                                         │
│  □ Training/awareness                  2 uur           │
│                                                         │
│  □ Prep surveillance audit             2 uur           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ROLLEN BIJ GROEI

### 1-2 personen

```
[Eigenaar]
├── Security
├── AI Governance
├── Kwaliteit
└── Alles
```

### 3-5 personen

```
[Eigenaar] - Eindverantwoordelijk
├── [Persoon A] - Security focus
└── [Persoon B] - AI focus

Kruislings reviewen:
- A auditeert B's werk
- B auditeert A's werk
```

### 6-10 personen

```
[Eigenaar/Directie] - Goedkeuring beleid
│
├── [Security Lead]
│   └── Security procedures
│   └── Incident response
│   └── Access beheer
│
├── [AI Lead]
│   └── AI register
│   └── Impact assessments
│   └── Bias monitoring
│
└── [Operations]
    └── Dagelijkse checks
    └── Logging
    └── Support

Interne auditor: Rouleren of extern
```

---

## EVIDENCE MINIMUMLIJST

### Voor ISO 27001 audit

| Evidence | Hoe verzamelen |
|----------|----------------|
| Beleid (getekend) | PDF met datum |
| Risico register | Export spreadsheet |
| SoA | Spreadsheet |
| Toegangsmatrix | Export spreadsheet |
| Incident log | Export uit systeem |
| Audit rapport | Word/PDF |
| Management review notulen | Word/PDF |
| Training records | Certificaten + lijst |
| Backup test bewijs | Screenshot + datum |

### Voor ISO 42001 audit

| Evidence | Hoe verzamelen |
|----------|----------------|
| AI Beleid | PDF |
| AI Register | Spreadsheet |
| Impact assessments | Per AI document |
| Bias monitoring logs | Spreadsheet/exports |
| Human oversight bewijs | Proces + voorbeelden |

---

## TOOLING (Schaalbaar)

### Start (1-2 personen)

```
Notion (gratis)
├── Beleid & procedures (pages)
├── Risico register (database)
├── Incident log (database)
├── AI register (database)
└── Checklists (templates)

+
Spreadsheet voor complexe tabellen
+
Git voor code/versioning
```

### Groei (3-5 personen)

```
Notion (team, €8-10/user/mnd)
├── Alles van start
├── Gedeelde workspaces
└── Permissies per sectie

+
Bitwarden Teams (wachtwoorden)
```

### Schaal (6-10 personen)

```
Optie A: Notion schalen
├── Meer structuur
├── Automations
└── Integraties

Optie B: Dedicated tool
├── Vanta/Drata (als budget)
└── Of blijf bij Notion
```

**Vuistregel:** Verander pas van tool als je pijn voelt, niet vooraf.

---

## WAARSCHUWINGSSIGNALEN

### Je doet te weinig

```
⚠️ Geen incident log in 6 maanden (ook positief loggen!)
⚠️ Risico register niet bijgewerkt in >6 maanden
⚠️ Geen management review in >6 maanden
⚠️ AI monitoring niet gedaan (hoog-risico)
⚠️ Training >1 jaar geleden
```

### Je doet te veel

```
⚠️ Meer dan 2 uur per week aan compliance (buiten projecten)
⚠️ Documenten die niemand leest
⚠️ Procedures voor dingen die vanzelfsprekend zijn
⚠️ Rapportages zonder actie
⚠️ Vergaderingen over vergaderingen
```

---

## QUICK START TEMPLATE

### Dag 1: Minimale setup

1. **Maak Notion workspace** (of alternatief)
2. **Creëer databases:**
   - Risico's
   - Incidenten
   - Toegang
   - AI systemen
3. **Schrijf basisbeleid** (1 A4 gecombineerd)
4. **Vul risico register** (top 10)

### Week 1: Operationeel

5. **Vul toegangsmatrix**
6. **Vul AI register**
7. **Plan eerste kwartaal review**
8. **Zet wekelijkse reminder** (vrijdag 16:00)

### Maand 1: Compleet

9. **Schrijf SoA** (27001)
10. **Schrijf impact assessments** (42001)
11. **Eerste wekelijkse checks gedaan**
12. **Voer eerste maandelijkse review uit**

---

*Versie 1.0 - Januari 2026*
*Schaalbaar: 1-10 personen*
