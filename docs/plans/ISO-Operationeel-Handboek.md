# ISO Operationeel Handboek
## Complete Procedure- en Evidence-gids voor 1-2 personen

---

## Overzicht: Wat moet je precies doen?

Dit document geeft voor elke verplichte procedure:
1. **WAT** - Wat moet je doen?
2. **WANNEER** - Hoe vaak?
3. **EVIDENCE** - Wat moet je bewaren?
4. **HOE** - Praktische aanpak

---

## DEEL 1: GEDEELDE PROCEDURES (Alle normen)

### 1.1 Documentbeheer

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Alle beleidsdocumenten en procedures beheren |
| **Frequentie** | Doorlopend + jaarlijkse review |
| **Evidence** | Versiegeschiedenis, goedkeuringsdata |

**Procedure:**
```
1. Elk document heeft:
   - Unieke naam/nummer
   - Versienummer (v1.0, v1.1, v2.0)
   - Datum laatste wijziging
   - Auteur/goedkeurder

2. Wijzigingen:
   - Verhoog minor versie bij kleine aanpassingen (v1.0 → v1.1)
   - Verhoog major versie bij significante wijzigingen (v1.1 → v2.0)
   - Noteer wijziging in document (changelog sectie)

3. Opslag:
   - Centrale locatie (Notion/Drive/Git)
   - Oude versies bewaren (minimaal vorige versie)
```

**Evidence template:**

| Document | Versie | Datum | Gewijzigd door | Wijziging |
|----------|--------|-------|----------------|-----------|
| ISMS Beleid | v1.0 | 2026-01-15 | [Naam] | Initiële versie |
| ISMS Beleid | v1.1 | 2026-06-01 | [Naam] | Scope uitgebreid |

---

### 1.2 Risicobeoordeling

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Identificeren en beoordelen van risico's |
| **Frequentie** | Jaarlijks volledig + bij significante wijzigingen |
| **Evidence** | Risico register met datums en beoordelingen |

**Procedure:**
```
1. Identificeer assets (systemen, data, processen)
2. Identificeer dreigingen per asset
3. Scoor risico: Kans (1-5) x Impact (1-5) = Risicoscore
4. Bepaal behandeling: Accepteren / Mitigeren / Vermijden / Overdragen
5. Documenteer maatregelen
6. Review minimaal jaarlijks
```

**Risico Register Template (Excel/Notion):**

| ID | Asset | Dreiging | Kans (1-5) | Impact (1-5) | Score | Behandeling | Maatregel | Eigenaar | Status | Datum |
|----|-------|----------|------------|--------------|-------|-------------|-----------|----------|--------|-------|
| R001 | Klantendata | Datalek | 3 | 5 | 15 | Mitigeren | Encryptie + access control | [Naam] | Open | 2026-01-15 |
| R002 | Website | DDoS | 2 | 4 | 8 | Overdragen | Cloudflare | [Naam] | Gesloten | 2026-01-15 |

**Wanneer opnieuw beoordelen:**
- [ ] Jaarlijks (volledig)
- [ ] Bij nieuwe systemen/diensten
- [ ] Na een incident
- [ ] Bij significante organisatiewijzigingen

---

### 1.3 Competentiebeheer

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Aantonen dat personeel competent is |
| **Frequentie** | Bij aanname + jaarlijks awareness |
| **Evidence** | CV's, certificaten, trainingsregistratie |

**Procedure:**
```
1. Per rol vastleggen welke competenties nodig zijn
2. Bewijs van competentie verzamelen:
   - CV
   - Diploma's/certificaten
   - Werkervaring
   - Training records
3. Jaarlijks awareness training volgen
4. Registreren in competentiematrix
```

**Competentiematrix Template:**

| Persoon | Rol | Vereiste competenties | Bewijs | Datum verificatie |
|---------|-----|----------------------|--------|-------------------|
| [Naam] | Eigenaar/Security | - ISO 27001 kennis<br>- Security awareness | - Certificaat X<br>- Training Y | 2026-01-15 |

**Jaarlijkse Awareness (minimaal):**
- Security awareness training (1-2 uur)
- AI ethics awareness (bij ISO 42001)
- Opfrissen incident response

---

### 1.4 Interne Audit

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Onafhankelijke beoordeling of systeem werkt |
| **Frequentie** | Minimaal 1x per jaar (voor elke norm) |
| **Evidence** | Auditplan, auditrapport, bevindingen, corrigerende acties |

**Procedure:**
```
1. Maak auditplan (welke onderdelen, wanneer, door wie)
2. Voer audit uit met checklist
3. Noteer bevindingen (conformiteiten + afwijkingen)
4. Classificeer afwijkingen:
   - Major: Systeem faalt op norm-eis
   - Minor: Verbetering nodig, geen systeemfalen
   - Observatie: Aanbeveling, geen afwijking
5. Maak corrigerende actieplan
6. Volg acties op
```

**Auditplan Template:**

| Audit ID | Scope | Auditor | Datum | Status |
|----------|-------|---------|-------|--------|
| IA-2026-01 | ISO 27001 volledig | Extern / Kruislings | 2026-10-15 | Gepland |
| IA-2026-02 | ISO 42001 volledig | Extern / Kruislings | 2026-11-15 | Gepland |

**Auditrapport Template:**

```markdown
# Interne Audit Rapport

**Audit ID:** IA-2026-01
**Datum:** 2026-10-15
**Auditor:** [Naam]
**Scope:** ISO 27001 ISMS

## Samenvatting
- Aantal geaudite clausules: X
- Bevindingen: Y conformiteiten, Z afwijkingen

## Bevindingen

| # | Clausule | Bevinding | Type | Actie vereist |
|---|----------|-----------|------|---------------|
| 1 | 5.1 | Beleid is gedocumenteerd en actueel | Conformiteit | - |
| 2 | 6.1.2 | Risicobeoordeling niet geüpdatet na nieuwe dienst | Minor | Ja |

## Corrigerende Acties

| Bevinding | Actie | Eigenaar | Deadline | Status |
|-----------|-------|----------|----------|--------|
| #2 | Risicobeoordeling updaten met nieuwe dienst | [Naam] | 2026-10-30 | Open |

## Conclusie
Het ISMS functioneert [effectief / met verbeterpunten].

**Auditor:** [Handtekening/Naam]
**Datum:** 2026-10-15
```

**Opties voor "onafhankelijke" audit bij 1-2 personen:**
1. Externe auditor inhuren (€500-1500)
2. Kruislings auditen (persoon A auditeert werk persoon B)
3. Peer uit netwerk vragen
4. Consultant pre-audit laten doen

---

### 1.5 Management Review (Directiebeoordeling)

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Evaluatie effectiviteit managementsysteem door directie |
| **Frequentie** | Minimaal 1x per jaar (aanbevolen: per kwartaal) |
| **Evidence** | Agenda, notulen, beslissingen, actielijst |

**Verplichte Agenda-items (alle normen):**
```
INPUT (moet besproken):
□ Status acties vorige review
□ Wijzigingen in externe/interne issues
□ Feedback van stakeholders
□ Niet-conformiteiten en corrigerende acties
□ Monitoring- en meetresultaten
□ Auditresultaten
□ Prestaties van leveranciers
□ Adequaatheid van middelen
□ Effectiviteit van genomen acties
□ Mogelijkheden voor verbetering

OUTPUT (moet besloten):
□ Beslissingen over verbetermogelijkheden
□ Benodigde wijzigingen aan het managementsysteem
□ Benodigde middelen
```

**Management Review Template:**

```markdown
# Management Review

**Datum:** 2026-Q1
**Aanwezig:** [Namen]
**Voorzitter:** [Naam]

## 1. Status Acties Vorige Review
| Actie | Eigenaar | Status | Opmerking |
|-------|----------|--------|-----------|
| Risico X mitigeren | [Naam] | Afgerond | - |

## 2. Wijzigingen Context
- Nieuwe klant met hogere security-eisen
- Geen wijzigingen in wetgeving

## 3. Prestatie-indicatoren
| KPI | Target | Actueel | Trend |
|-----|--------|---------|-------|
| Security incidenten | 0 | 0 | ✓ |
| Uptime | >99% | 99.8% | ✓ |
| Klanttevredenheid | >8 | 8.5 | ✓ |

## 4. Incidenten & Non-conformiteiten
- 1 minor incident (phishing poging, geblokkeerd)
- 0 non-conformiteiten

## 5. Audit Resultaten
- Interne audit: 2 minors, beide opgelost
- Geen externe audit dit kwartaal

## 6. Verbetermogelijkheden
- Automatisering backup-monitoring

## 7. Beslissingen
| Beslissing | Actie | Eigenaar | Deadline |
|------------|-------|----------|----------|
| Backup monitoring automatiseren | Tool implementeren | [Naam] | 2026-04-30 |

## 8. Benodigde Middelen
- €200 voor monitoring tool

**Volgende review:** 2026-Q2
```

---

### 1.6 Non-conformiteiten & Corrigerende Acties (CAPA)

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Afwijkingen registreren en oplossen |
| **Frequentie** | Bij elk voorval |
| **Evidence** | NC-register, root cause analyse, acties, verificatie |

**Procedure:**
```
1. DETECTIE
   - Afwijking geconstateerd (audit, incident, klacht, etc.)
   - Registreer in NC-register

2. ANALYSE
   - Beschrijf de non-conformiteit
   - Bepaal root cause (5x waarom)
   - Bepaal impact

3. CORRECTIE (directe actie)
   - Los het directe probleem op

4. CORRIGERENDE ACTIE (voorkom herhaling)
   - Pak de root cause aan
   - Implementeer structurele verbetering

5. VERIFICATIE
   - Controleer of actie effectief was
   - Sluit NC af
```

**NC-Register Template:**

| NC-ID | Datum | Bron | Beschrijving | Root Cause | Correctie | Corr. Actie | Eigenaar | Deadline | Verificatie | Status |
|-------|-------|------|--------------|------------|-----------|-------------|----------|----------|-------------|--------|
| NC-001 | 2026-02-10 | Interne audit | Backup niet getest | Geen procedure | Test uitgevoerd | Maandelijkse test ingepland | [Naam] | 2026-02-28 | 2026-03-15 OK | Gesloten |

---

### 1.7 Continue Verbetering

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Proactief verbeteren van het managementsysteem |
| **Frequentie** | Doorlopend + kwartaal review |
| **Evidence** | Verbeterregister, implementatie-bewijs |

**Bronnen voor verbetering:**
- Interne audits
- Management reviews
- Incidenten
- Klantfeedback
- Markt/technologie ontwikkelingen
- Eigen observaties

**Verbeterregister Template:**

| ID | Datum | Bron | Verbetering | Prioriteit | Actie | Eigenaar | Status |
|----|-------|------|-------------|------------|-------|----------|--------|
| V-001 | 2026-03-01 | Eigen obs. | Automatiseer wachtwoord-reset | Medium | Tool implementeren | [Naam] | Open |

---

## DEEL 2: ISO 27001 SPECIFIEKE PROCEDURES

### 2.1 Asset Management

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Inventaris van informatie-assets |
| **Frequentie** | Doorlopend bijhouden + kwartaal review |
| **Evidence** | Asset register met classificatie |

**Asset Register Template:**

| Asset ID | Naam | Type | Eigenaar | Classificatie | Locatie | Criticality |
|----------|------|------|----------|---------------|---------|-------------|
| A-001 | Klantendatabase | Data | [Naam] | Vertrouwelijk | AWS RDS | Hoog |
| A-002 | Laptop 1 | Hardware | [Naam] | Intern | Thuiskantoor | Medium |
| A-003 | GitHub repo | Code | [Naam] | Vertrouwelijk | GitHub | Hoog |
| A-004 | Google Workspace | SaaS | [Naam] | Vertrouwelijk | Cloud | Hoog |

**Classificatieniveaus:**
- **Openbaar**: Geen restricties
- **Intern**: Alleen medewerkers
- **Vertrouwelijk**: Need-to-know basis
- **Strikt vertrouwelijk**: Zeer beperkte toegang

---

### 2.2 Access Control

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Beheer van toegangsrechten |
| **Frequentie** | Bij wijzigingen + kwartaal review |
| **Evidence** | Access matrix, review logs |

**Procedure:**
```
1. Nieuwe toegang aanvragen:
   - Bepaal welke systemen nodig
   - Bepaal minimaal benodigde rechten (least privilege)
   - Implementeer toegang
   - Registreer in access matrix

2. Toegang intrekken:
   - Bij vertrek of rolwijziging
   - Binnen 24 uur uitvoeren
   - Registreer in access matrix

3. Periodieke review:
   - Kwartaal: alle toegangsrechten reviewen
   - Vraag: Is deze toegang nog nodig?
   - Documenteer review
```

**Access Matrix Template:**

| Systeem | [Persoon 1] | [Persoon 2] | Laatste review |
|---------|-------------|-------------|----------------|
| AWS Console | Admin | Read-only | 2026-01-15 |
| GitHub | Admin | Write | 2026-01-15 |
| Google Workspace | Admin | User | 2026-01-15 |
| Klantportaal | Admin | - | 2026-01-15 |

**Access Review Log:**

| Datum | Reviewer | Systemen | Wijzigingen | Volgende review |
|-------|----------|----------|-------------|-----------------|
| 2026-01-15 | [Naam] | Alle | Geen | 2026-04-15 |

---

### 2.3 Incident Management

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Detecteren, reageren en leren van security incidenten |
| **Frequentie** | Bij elk incident |
| **Evidence** | Incident register, response logs, lessons learned |

**Incident Response Procedure:**

```
FASE 1: DETECTIE & RAPPORTAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Incident gedetecteerd (alert, melding, observatie)
- Registreer direct in incident log
- Bepaal initiële classificatie

FASE 2: CLASSIFICATIE
━━━━━━━━━━━━━━━━━━━━━
Severity bepalen:
- KRITIEK: Datalek, ransomware, volledige uitval
  → Directe actie, binnen 1 uur response
- HOOG: Poging tot inbraak, malware gedetecteerd
  → Dezelfde dag response
- MEDIUM: Phishing geblokkeerd, mislukte login pogingen
  → Binnen 48 uur evalueren
- LAAG: Spam, false positives
  → Loggen, geen actie vereist

FASE 3: RESPONSE
━━━━━━━━━━━━━━━━
1. Contain: Beperk de schade (isoleer systeem, blokkeer account)
2. Eradicate: Verwijder de dreiging
3. Recover: Herstel normale operatie
4. Documenteer alle acties met timestamps

FASE 4: POST-INCIDENT
━━━━━━━━━━━━━━━━━━━━━
1. Root cause analyse
2. Lessons learned documenteren
3. Verbeteracties bepalen
4. Incident afsluiten
```

**Incident Register Template:**

| Inc-ID | Datum/Tijd | Melder | Beschrijving | Severity | Status | Eigenaar |
|--------|------------|--------|--------------|----------|--------|----------|
| INC-001 | 2026-02-10 14:30 | [Naam] | Phishing e-mail ontvangen | Medium | Gesloten | [Naam] |

**Incident Detail Template:**

```markdown
# Incident Report

**Incident ID:** INC-001
**Datum detectie:** 2026-02-10 14:30
**Datum gesloten:** 2026-02-10 16:00

## Beschrijving
Phishing e-mail ontvangen met malafide link naar nep-inlogpagina.

## Classificatie
- **Severity:** Medium
- **Type:** Phishing

## Timeline
| Tijd | Actie |
|------|-------|
| 14:30 | E-mail ontvangen en herkend als phishing |
| 14:35 | Gemeld en geregistreerd |
| 14:40 | E-mail verwijderd, afzender geblokkeerd |
| 15:00 | Controle of link is geklikt: Nee |
| 16:00 | Incident gesloten |

## Impact
- Geen data gelekt
- Geen systemen gecompromitteerd

## Root Cause
Phishing e-mail passeerde spam filter.

## Acties
| Actie | Eigenaar | Deadline | Status |
|-------|----------|----------|--------|
| Spam filter regels aanscherpen | [Naam] | 2026-02-15 | Open |

## Lessons Learned
- Herkenning phishing werkt
- Spam filter verbetering nodig
```

---

### 2.4 Business Continuity

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Plannen voor continuïteit bij verstoringen |
| **Frequentie** | Jaarlijks reviewen + testen |
| **Evidence** | BCP document, testresultaten |

**Minimaal BCP voor micro-onderneming:**

```markdown
# Business Continuity Plan

## 1. Kritieke Processen
| Proces | Max downtime | Herstelprioriteit |
|--------|--------------|-------------------|
| Klantdienstverlening | 4 uur | 1 |
| E-mail | 8 uur | 2 |
| Administratie | 24 uur | 3 |

## 2. Backup Strategie
| Systeem | Backup frequentie | Locatie | Retentie |
|---------|-------------------|---------|----------|
| Klantdata | Dagelijks | Backblaze B2 | 30 dagen |
| Code | Continue (Git) | GitHub | Onbeperkt |
| Documenten | Realtime sync | Google Drive | 30 dagen |

## 3. Herstelstappen
Bij volledige laptop-uitval:
1. Nieuwe laptop aanschaffen (< 24 uur)
2. OS installeren + essentiële software
3. Restore van backup
4. Toegang herstellen (password manager)

## 4. Contact bij Calamiteit
| Type | Contact | Nummer |
|------|---------|--------|
| IT Support | [Provider] | [Nummer] |
| Hosting | [Provider] | [Nummer] |
```

**Jaarlijkse Test:**
- [ ] Backup restore test (1 bestand terughalen)
- [ ] Verificatie backup integriteit
- [ ] Controle contactgegevens

---

### 2.5 Leveranciersbeoordeling

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Beoordelen van security bij leveranciers |
| **Frequentie** | Bij selectie + jaarlijks voor kritieke leveranciers |
| **Evidence** | Leveranciersregister, beoordelingen |

**Leveranciersregister Template:**

| Leverancier | Dienst | Criticality | Certificeringen | Laatste review | Volgende review |
|-------------|--------|-------------|-----------------|----------------|-----------------|
| AWS | Hosting | Kritiek | ISO 27001, SOC 2 | 2026-01-15 | 2027-01-15 |
| GitHub | Code hosting | Kritiek | SOC 2 | 2026-01-15 | 2027-01-15 |
| Mailchimp | E-mail marketing | Medium | - | 2026-01-15 | 2027-01-15 |

**Beoordelingscriteria:**
- [ ] Heeft leverancier security-certificeringen?
- [ ] Is er een verwerkersovereenkomst (AVG)?
- [ ] Waar staat data opgeslagen?
- [ ] Wat zijn de SLA's?
- [ ] Wat is het incident response proces?

---

## DEEL 3: ISO 42001 SPECIFIEKE PROCEDURES

### 3.1 AI Systeem Inventaris

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Register van alle AI-systemen |
| **Frequentie** | Doorlopend bijhouden |
| **Evidence** | AI register met classificatie |

**AI Systeem Register Template:**

| AI-ID | Naam | Type | Leverancier | Doel | Data input | Output | Risico niveau | Status |
|-------|------|------|-------------|------|------------|--------|---------------|--------|
| AI-001 | ChatGPT | LLM (extern) | OpenAI | Tekst generatie | Prompts | Tekst | Medium | Actief |
| AI-002 | Copilot | Code assist | GitHub/MS | Code suggesties | Code context | Code | Medium | Actief |
| AI-003 | Eigen model X | ML (intern) | Zelf | Classificatie | Klantdata | Scores | Hoog | Development |

**Classificatie risico niveau:**
- **Hoog**: Beslissingen over mensen, gevoelige data, autonome acties
- **Medium**: Ondersteunend, mens-in-de-loop, beperkte impact
- **Laag**: Geen impact op mensen, puur intern, experimenteel

---

### 3.2 AI Impact Assessment

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Beoordeling impact AI-systeem op individuen/maatschappij |
| **Frequentie** | Bij implementatie + jaarlijks voor hoog-risico |
| **Evidence** | Impact assessment documenten |

**AI Impact Assessment Template:**

```markdown
# AI Impact Assessment

**AI Systeem:** [Naam]
**Datum:** 2026-XX-XX
**Beoordelaar:** [Naam]

## 1. Systeem Beschrijving
- **Doel:** [Waarvoor wordt het gebruikt]
- **Type:** [Classificatie, Generatie, Predictie, etc.]
- **Scope:** [Wie/wat wordt beïnvloed]

## 2. Data Governance
| Vraag | Antwoord |
|-------|----------|
| Welke data wordt gebruikt? | |
| Bevat data persoonsgegevens? | Ja/Nee |
| Waar komt data vandaan? | |
| Hoe is datakwaliteit geborgd? | |

## 3. Risico Analyse

### 3.1 Bias & Fairness
| Risico | Kans | Impact | Maatregel |
|--------|------|--------|-----------|
| Discriminatie op basis van [X] | | | |
| Onderrepresentatie groep [Y] | | | |

### 3.2 Privacy
| Risico | Kans | Impact | Maatregel |
|--------|------|--------|-----------|
| Onbedoelde data exposure | | | |
| Data naar derde partij | | | |

### 3.3 Veiligheid
| Risico | Kans | Impact | Maatregel |
|--------|------|--------|-----------|
| Foutieve output | | | |
| Manipulatie/adversarial | | | |

### 3.4 Transparantie
| Vraag | Antwoord |
|-------|----------|
| Is uitlegbaar hoe beslissingen tot stand komen? | |
| Weten gebruikers dat ze met AI interacteren? | |

## 4. Human Oversight
- **Niveau:** [Volledig autonoom / Human-in-the-loop / Human-on-the-loop]
- **Escalatieprocedure:** [Hoe/wanneer escaleert naar mens]

## 5. Monitoring
| Metric | Frequentie | Threshold | Actie bij overschrijding |
|--------|------------|-----------|--------------------------|
| Accuracy | Wekelijks | >95% | Review model |
| Bias metric X | Maandelijks | <5% | Onderzoek |

## 6. Conclusie
- **Risico niveau:** [Laag / Medium / Hoog]
- **Goedkeuring:** [Ja / Nee / Voorwaardelijk]
- **Voorwaarden:** [Indien van toepassing]

**Beoordelaar:** [Naam]
**Datum:** [Datum]
**Volgende review:** [Datum]
```

---

### 3.3 Bias Monitoring

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Detecteren van oneerlijke uitkomsten |
| **Frequentie** | Afhankelijk van risico niveau (zie tabel) |
| **Evidence** | Monitoring logs, bias rapporten |

**Frequentie per risico niveau:**

| Risico niveau | Monitoring frequentie | Uitgebreide review |
|---------------|----------------------|-------------------|
| Hoog | Wekelijks | Maandelijks |
| Medium | Maandelijks | Kwartaal |
| Laag | Kwartaal | Jaarlijks |

**Bias Monitoring Checklist:**

```markdown
# Bias Monitoring Check

**AI Systeem:** [Naam]
**Periode:** [Datum range]
**Reviewer:** [Naam]

## Metrics Review
| Metric | Vorige periode | Deze periode | Trend | OK? |
|--------|----------------|--------------|-------|-----|
| Overall accuracy | 96% | 95% | ↓ | ✓ |
| Accuracy groep A | 95% | 94% | ↓ | ✓ |
| Accuracy groep B | 97% | 96% | ↓ | ✓ |
| Verschil A-B | 2% | 2% | = | ✓ |

## Steekproef Output Review
| Sample | Input | Output | Verwacht | Correct? | Opmerkingen |
|--------|-------|--------|----------|----------|-------------|
| 1 | [X] | [Y] | [Z] | Ja/Nee | |

## Klachten/Feedback
| Datum | Klacht | Gerelateerd aan bias? | Actie |
|-------|--------|----------------------|-------|
| | | | |

## Conclusie
- [ ] Geen bias gedetecteerd
- [ ] Potentiële bias, onderzoek nodig
- [ ] Bias bevestigd, actie vereist

**Volgende check:** [Datum]
```

---

### 3.4 Human Oversight Procedure

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Borgen dat mens controle houdt over AI |
| **Frequentie** | Doorlopend + kwartaal review |
| **Evidence** | Oversight logs, escalatierecords |

**Human Oversight Niveaus:**

```
NIVEAU 1: Human-in-the-loop
━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI doet voorstel, mens beslist
Voorbeelden: Content review, credit scoring review

NIVEAU 2: Human-on-the-loop
━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI beslist, mens monitort en kan ingrijpen
Voorbeelden: Spam filter, fraud detection met alerts

NIVEAU 3: Human-over-the-loop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI werkt autonoom, mens evalueert periodiek
Voorbeelden: Recommendation engines, prijsoptimalisatie
```

**Escalatiematrix:**

| Situatie | Actie | Verantwoordelijke |
|----------|-------|-------------------|
| AI-output onzeker (confidence <X%) | Handmatige review | [Naam] |
| Klacht over AI-beslissing | Herbeoordeling door mens | [Naam] |
| Bias gedetecteerd | Systeem pauzeren, onderzoek | [Naam] |
| Veiligheidsincident | Onmiddellijk stoppen | [Naam] |

---

## DEEL 4: ISO 9001 SPECIFIEKE PROCEDURES

*(Alleen als je besluit ISO 9001 te doen)*

### 4.1 Klanttevredenheid

| Aspect | Vereiste |
|--------|----------|
| **Wat** | Meten en verbeteren van klanttevredenheid |
| **Frequentie** | Na elk project/kwartaal |
| **Evidence** | Enquête resultaten, feedback log |

**Methodes (kies 1-2):**
- Post-project enquête (NPS of 1-10 score)
- Kwartaal check-in gesprekken
- Review van klachten/complimenten

**Klanttevredenheid Log:**

| Datum | Klant | Score | Feedback | Actie |
|-------|-------|-------|----------|-------|
| 2026-02-15 | Klant A | 9/10 | "Snelle levering" | - |
| 2026-02-20 | Klant B | 7/10 | "Documentatie kan beter" | Docs verbeteren |

---

## DEEL 5: OPERATIONEEL RITME

### Dagelijks (5 minuten)

```
□ Snelle security check (alerts, logs)
□ Incident? → Registreren
```

### Wekelijks (30-45 minuten, vrijdag)

```
□ Security monitoring review
□ AI monitoring review (indien van toepassing)
□ Incidenten van de week doornemen
□ Access/wijzigingen registreren
□ Weeklog bijwerken
```

### Maandelijks (1-2 uur)

```
□ Risico register review
□ Bias monitoring (hoog-risico AI)
□ KPI's bijwerken
□ Leveranciers check (nieuws, incidenten)
□ Documentatie nog actueel?
```

### Kwartaal (2-4 uur)

```
□ Management Review uitvoeren
□ Access review alle systemen
□ Doelstellingen voortgang
□ Training/awareness
□ Verbeteracties reviewen
```

### Jaarlijks (16-24 uur verspreid)

```
□ Interne audit (of extern laten doen)
□ Risicobeoordeling volledig updaten
□ Beleid en doelstellingen herzien
□ Leveranciersbeoordelingen
□ BCP test (backup restore)
□ Alle AI impact assessments reviewen
□ Competenties/training bijwerken
□ Voorbereiding surveillance audit
```

---

## DEEL 6: EVIDENCE CHECKLIST PER AUDIT

### Voor ISO 27001 Audit

**Verplicht aan te tonen:**
- [ ] ISMS Scope document
- [ ] Informatiebeveiligingsbeleid (goedgekeurd)
- [ ] Risicobeoordeling (resultaten)
- [ ] Risk Treatment Plan
- [ ] Statement of Applicability
- [ ] Doelstellingen + monitoring
- [ ] Competentie-evidence (CV's, certificaten)
- [ ] Awareness training records
- [ ] Asset register
- [ ] Access control records + reviews
- [ ] Incident logs
- [ ] Interne audit rapport + acties
- [ ] Management review notulen
- [ ] Non-conformiteiten register + CAPA
- [ ] Backup test evidence
- [ ] Leveranciersbeoordelingen

### Voor ISO 42001 Audit

**Verplicht aan te tonen:**
- [ ] AIMS Scope document
- [ ] AI Beleid (goedgekeurd)
- [ ] AI Systeem register
- [ ] Impact assessments per AI-systeem
- [ ] Bias monitoring records
- [ ] Human oversight procedures + evidence
- [ ] Data governance documentatie
- [ ] AI-gerelateerde incident logs
- [ ] Interne audit rapport AIMS
- [ ] Management review (AI-specifiek)
- [ ] Training records (AI ethics)

### Voor ISO 9001 Audit

**Verplicht aan te tonen:**
- [ ] QMS Scope document
- [ ] Kwaliteitsbeleid (goedgekeurd)
- [ ] Kwaliteitsdoelstellingen + monitoring
- [ ] Risico's en kansen analyse
- [ ] Procesbeschrijvingen
- [ ] Competentie-evidence
- [ ] Klanttevredenheid data
- [ ] Interne audit rapport + acties
- [ ] Management review notulen
- [ ] Non-conformiteiten register + CAPA
- [ ] Product/dienst vrijgave records

---

## DEEL 7: QUICK REFERENCE CARDS

### Security Incident Response

```
┌─────────────────────────────────────────────────────────┐
│  SECURITY INCIDENT - WAT TE DOEN                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. STOP - Blijf kalm, handel weloverwogen             │
│                                                         │
│  2. CONTAIN                                             │
│     □ Isoleer getroffen systeem (netwerk uit)          │
│     □ Wijzig wachtwoorden indien nodig                 │
│     □ Revoke verdachte sessies/tokens                  │
│                                                         │
│  3. DOCUMENTEER                                         │
│     □ Log in incident register (tijd, acties)          │
│     □ Maak screenshots                                  │
│     □ Bewaar logs                                       │
│                                                         │
│  4. ANALYSEER                                           │
│     □ Wat is er gebeurd?                               │
│     □ Wat is de impact?                                │
│     □ Wat is de root cause?                            │
│                                                         │
│  5. HERSTEL                                             │
│     □ Verwijder dreiging                               │
│     □ Herstel systemen                                 │
│     □ Test of alles werkt                              │
│                                                         │
│  6. LEER                                                │
│     □ Wat kunnen we verbeteren?                        │
│     □ Welke maatregelen nemen?                         │
│                                                         │
│  BIJ DATALEK: Meld binnen 72 uur aan AP!               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### AI Issue Response

```
┌─────────────────────────────────────────────────────────┐
│  AI PROBLEEM - WAT TE DOEN                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  BIAS/DISCRIMINATIE GEDETECTEERD:                       │
│  □ Pauzeer AI-systeem indien mogelijk                  │
│  □ Documenteer voorbeelden                              │
│  □ Analyseer root cause                                 │
│  □ Corrigeer model/data/thresholds                     │
│  □ Test correctie                                       │
│  □ Hervat met monitoring                               │
│                                                         │
│  FOUTIEVE OUTPUT:                                       │
│  □ Escaleer naar handmatige verwerking                 │
│  □ Documenteer fout                                     │
│  □ Analyseer frequentie                                 │
│  □ Pas confidence thresholds aan indien nodig          │
│                                                         │
│  PRIVACY CONCERN:                                       │
│  □ Stop data-verwerking                                │
│  □ Evalueer welke data is verwerkt                     │
│  □ Neem contact op met betrokkenen indien nodig        │
│  □ Pas data governance aan                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

*Document versie: 1.0*
*Gemaakt: Januari 2026*
*Voor: Micro-onderneming (1-2 personen)*
*Normen: ISO 27001:2022, ISO 42001:2023, ISO 9001:2015*
