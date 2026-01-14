# GEMMA Informatiebeveiliging User Stories - NFR Checklist

**Bron:** [GEMMA Online - User stories voor informatiebeveiliging](https://gemmaonline.nl/wiki/User_stories_voor_informatiebeveiliging)
**Datum:** 2026-01-13
**Doel:** Non-functional requirements voor informatiebeveiliging bij analyse, ontwerp en bouw

---

## Overzicht Categorieën

| Categorie | Aantal Stories | Focus |
|-----------|----------------|-------|
| Mens/Personeel | 3 | Fouten voorkomen, training, procedures |
| Programmatuur | 3 | OWASP/CVE, versiebeheer, documentatie |
| Gegevens | 4 | Authenticatie, encryptie, logging |
| Organisatie | 4 | Kwaliteitsborging, capaciteit, acceptatie |

---

## NFR-001: Mens/Personeel

### NFR-001.1: Onbedoelde Onjuiste Handelingen

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-001.1 |
| **Categorie** | Mens/Personeel |
| **Schade** | Medium |
| **Kans** | Hoog |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik maak software die fouten zoals onwetendheid en onoplettendheid opvangt en duidelijke schermmeldingen geeft" |
| Eindgebruiker | "Ik wil dat fouten worden opgevangen door software zodat ik zonder fouten kan werken" |
| Organisatie | "Wij zorgen voor goed opgeleide architecten en ontwikkelaars om foutkans te minimaliseren" |

**Verificatie Checklist:**
- [ ] Input validatie op alle gebruikersinvoer
- [ ] Duidelijke foutmeldingen in gebruikerstaal
- [ ] Bevestigingsdialogen voor kritieke acties
- [ ] Undo functionaliteit waar mogelijk
- [ ] Contextgevoelige help beschikbaar

---

### NFR-001.2: Gebrekkige Procedures

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-001.2 |
| **Categorie** | Mens/Personeel |
| **Schade** | Medium |
| **Kans** | Medium |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik werk volgens vastgestelde procedures en maak voldoende productdocumentatie" |
| Eindgebruiker | "Ik wil begeleiding via software-instructies en training" |
| Organisatie | "Wij stellen procedures vast en communiceren deze om schade door fouten te minimaliseren" |

**Verificatie Checklist:**
- [ ] Ontwikkelprocedures gedocumenteerd
- [ ] Code review proces ingericht
- [ ] Deployment procedures vastgelegd
- [ ] Gebruikersdocumentatie aanwezig
- [ ] Training materiaal beschikbaar

---

### NFR-001.3: Complexe, Foutgevoelige Bediening

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-001.3 |
| **Categorie** | Mens/Personeel |
| **Schade** | Medium |
| **Kans** | Medium |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik maak gebruiksvriendelijke software passend bij de doelgroep" |
| Eindgebruiker | "Ik wil eenvoudige software die foutkans vermindert" |
| Organisatie | "Software moet eenvoudig te gebruiken zijn" |

**Verificatie Checklist:**
- [ ] UX review uitgevoerd
- [ ] Wizard-flows voor complexe taken
- [ ] Consistente UI patterns
- [ ] Toegankelijkheid (WCAG) getest
- [ ] Gebruikerstest uitgevoerd

---

## NFR-002: Programmatuur

### NFR-002.1: Ontwerp-/Programmeerfouten (KRITIEK)

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-002.1 |
| **Categorie** | Programmatuur |
| **Schade** | **HOOG** |
| **Kans** | Medium |
| **Prioriteit** | **P0 - KRITIEK** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik ontwikkel applicaties die bekende OWASP Top 20 en CVE kwetsbaarheden vermijden" |
| Tester | "Ik test tegen OWASP Top 20 en CWE lijsten, niet alleen happy-path scenario's" |
| Organisatie | "Wij stellen ontwikkelstandaarden vast en voeren architectuur reviews uit" |

**Verificatie Checklist:**
- [ ] OWASP Top 10 review uitgevoerd
- [ ] CWE Top 25 coverage geanalyseerd
- [ ] SQL Injection preventie (CWE-89)
- [ ] XSS preventie (CWE-79)
- [ ] Path Traversal preventie (CWE-22)
- [ ] Command Injection preventie (CWE-78)
- [ ] Authentication mechanismen (CWE-287, CWE-306)
- [ ] Secure coding guidelines gevolgd
- [ ] Static analysis (SAST) uitgevoerd
- [ ] Dynamic analysis (DAST) uitgevoerd
- [ ] Dependency vulnerability scan

**MarQed Scanner Mapping:**
| Check | Scanner | Status |
|-------|---------|--------|
| SQL Injection | SQLInjectionDetector | 🔴 Planned (Fase 31.1) |
| XSS | XSSDetector | 🔴 Planned (Fase 31.1) |
| Path Traversal | PathTraversalDetector | 🔴 Planned (Fase 31.1) |
| Command Injection | OSCommandInjectionDetector | 🔴 Planned (Fase 31.1) |
| Authentication | MissingAuthenticationDetector | 🔴 Planned (Fase 31.2) |
| Resource Leaks | ResourceLeakDetector | 🟢 Beschikbaar |

---

### NFR-002.2: Versiebeheersfouten

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-002.2 |
| **Categorie** | Programmatuur |
| **Schade** | Medium |
| **Kans** | Medium |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik zorg voor correct versiebeheer om foutkans te verminderen" |
| Eindgebruiker | "Ik kan softwareversies verifiëren om correctheid te bevestigen" |
| Organisatie | "Wij implementeren versiebeheer procedures en deployment automatisering" |

**Verificatie Checklist:**
- [ ] Git branching strategie gedocumenteerd
- [ ] Semantic versioning toegepast
- [ ] Changelog bijgehouden
- [ ] Versie zichtbaar in applicatie
- [ ] Rollback procedure beschikbaar
- [ ] CI/CD pipeline ingericht

---

### NFR-002.3: Onvoldoende Documentatie

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-002.3 |
| **Categorie** | Programmatuur |
| **Schade** | Medium |
| **Kans** | Medium |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik lever gereviewde documentatie: functioneel, technisch, beheer, gebruikershandleiding en trainingsmateriaal" |
| Eindgebruiker | "Ik ontvang documentatie die correct softwaregebruik ondersteunt" |
| Organisatie | "Alle deliverables ondergaan kwaliteitsborging voor documentatiestandaarden" |

**Verificatie Checklist:**
- [ ] API documentatie compleet
- [ ] Architectuur documentatie actueel
- [ ] Installatie handleiding aanwezig
- [ ] Beheerhandleiding aanwezig
- [ ] Gebruikershandleiding aanwezig
- [ ] Code comments aanwezig (SIG standaard)

**MarQed Scanner Mapping:**
| Check | Scanner | Status |
|-------|---------|--------|
| Comment Ratio | CommentsAnalyzer | 🟢 Beschikbaar |
| Documentation Quality | - | 🔴 Niet beschikbaar |

---

## NFR-003: Gegevens (KRITIEK)

### NFR-003.1: Ongeautoriseerde Toegang tot Gegevens

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-003.1 |
| **Categorie** | Gegevens |
| **Schade** | **HOOG** |
| **Kans** | Medium |
| **Prioriteit** | **P0 - KRITIEK** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik implementeer authenticatie/autorisatie die ongeautoriseerde toegang voorkomt; ik log alle toegangspogingen" |
| Eindgebruiker | "Ik heb duidelijke authenticatie nodig, correcte autorisatie, en activiteitenlogging" |
| Organisatie | "Wij stellen encryptiestandaarden en verificatieprocedures vast" |

**Verificatie Checklist:**
- [ ] Authenticatie mechanisme geïmplementeerd
- [ ] Autorisatie op basis van rollen (RBAC)
- [ ] Session management veilig
- [ ] Toegangspogingen gelogd
- [ ] Failed login attempts gelimiteerd
- [ ] Account lockout na X pogingen
- [ ] Password policy geïmplementeerd

**MarQed Scanner Mapping:**
| Check | Scanner | Status |
|-------|---------|--------|
| Missing Auth | MissingAuthenticationDetector | 🔴 Planned (Fase 31.2) |
| Access Control | AccessControlDetector | 🔴 Planned (Fase 31.2) |

---

### NFR-003.2: Gebrekkige of Ontbrekende Encryptie

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-003.2 |
| **Categorie** | Gegevens |
| **Schade** | **HOOG** |
| **Kans** | Medium |
| **Prioriteit** | **P0 - KRITIEK** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik zorg dat producten gevoelige data versleutelen tijdens transport en opslag met geaccepteerde technieken" |
| Organisatie | "Wij specificeren verplichte encryptievormen met duidelijke implementatierichtlijnen" |

**Verificatie Checklist:**
- [ ] TLS 1.2+ voor alle verbindingen
- [ ] Gevoelige data versleuteld at-rest
- [ ] Geen zwakke algoritmes (MD5, SHA1, DES)
- [ ] Secure key management
- [ ] Certificate validation correct
- [ ] No hardcoded credentials

**MarQed Scanner Mapping:**
| Check | Scanner | Status |
|-------|---------|--------|
| Missing Encryption | MissingEncryptionDetector | 🔴 Planned (Fase 31.3) |
| Weak Crypto | WeakCryptoDetector | 🔴 Planned (Fase 31.3) |
| Hardcoded Credentials | HardcodedCredentialsDetector | 🟡 Deels (Fase 31.3) |

---

### NFR-003.3: Ongeautoriseerde Toegang door Onbevoegden

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-003.3 |
| **Categorie** | Gegevens |
| **Schade** | **HOOG** |
| **Kans** | Laag |
| **Prioriteit** | **P1 - HOOG** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik implementeer authenticatie/autorisatie; voor bijzondere persoonsgegevens eis ik 2FA vanuit andere zones; ik log alle inlogpogingen en informatietoegang" |
| Eindgebruiker | "Ik heb mechanismen nodig die ongeautoriseerde toegang voorkomen" |
| Organisatie | "Wij definiëren toegestane authenticatie/autorisatie mechanismen" |

**Verificatie Checklist:**
- [ ] 2FA voor gevoelige data/acties
- [ ] Session timeout geïmplementeerd
- [ ] IP-based access restrictions (waar relevant)
- [ ] Audit logging voor alle data access
- [ ] Privilege escalation preventie
- [ ] Least privilege principe toegepast

**MarQed Scanner Mapping:**
| Check | Scanner | Status |
|-------|---------|--------|
| CSRF | CSRFDetector | 🔴 Planned (Fase 31.2) |
| Privilege Management | PrivilegeDetector | 🔴 Planned (Fase 31.2) |

---

### NFR-003.4: Ongeautoriseerd Kopiëren van Gegevens

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-003.4 |
| **Categorie** | Gegevens |
| **Schade** | **HOOG** |
| **Kans** | Laag |
| **Prioriteit** | **P1 - HOOG** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Organisatie | "Ik kan data-kopiëren detecteren en loggen voor auditcontrole" |

**Verificatie Checklist:**
- [ ] Data export functionaliteit gelogd
- [ ] Bulk download detectie
- [ ] Copy/paste tracking (waar relevant)
- [ ] Print functionaliteit gecontroleerd
- [ ] Screenshot preventie (waar vereist)

---

## NFR-004: Organisatie

### NFR-004.1: Ontbrekende of Verouderde Documentatie

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-004.1 |
| **Categorie** | Organisatie |
| **Schade** | Medium |
| **Kans** | Medium |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Developer | "Ik documenteer alle deliverables volgens acceptatiecriteria" |
| Eindgebruiker | "Opgeleverde producten hebben voldoende documentatie" |
| Organisatie | "Alle producten voldoen aan vooraf gestelde acceptatiecriteria voor beheeroverdracht" |

**Verificatie Checklist:**
- [ ] Definition of Done bevat documentatie
- [ ] Acceptatiecriteria expliciet
- [ ] Review proces voor documentatie
- [ ] Versioning van documentatie
- [ ] Archivering procedure

---

### NFR-004.2: Onvoldoende Personele Capaciteit

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-004.2 |
| **Categorie** | Organisatie |
| **Schade** | **HOOG** |
| **Kans** | **HOOG** |
| **Prioriteit** | **P0 - KRITIEK** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Organisatie | "Wij behouden kern experts om kwaliteit en continuïteit te waarborgen" |

**Verificatie Checklist:**
- [ ] Knowledge sharing ingericht
- [ ] Bus factor > 1 voor kritieke componenten
- [ ] Documentatie voor onboarding
- [ ] Cross-training gepland

---

### NFR-004.3: Gebrekkige Kwaliteitsborging

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-004.3 |
| **Categorie** | Organisatie |
| **Schade** | **HOOG** |
| **Kans** | Medium |
| **Prioriteit** | **P1 - HOOG** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Organisatie | "Kwaliteitsborging processen zorgen dat producten geschikt zijn voor gemeenten" |

**Verificatie Checklist:**
- [ ] Code review verplicht
- [ ] Automated testing (unit, integration)
- [ ] Security review proces
- [ ] Performance testing
- [ ] Accessibility testing
- [ ] SIG maintainability score acceptabel

**MarQed Scanner Mapping:**
| Check | Scanner | Status |
|-------|---------|--------|
| Complexity | ComplexityAnalyzer | 🟢 Beschikbaar |
| Duplication | DuplicationAnalyzer | 🟢 Beschikbaar |
| Coupling | CouplingAnalyzer | 🟢 Beschikbaar |
| Volume | DotNetVolumeScanner | 🟢 Beschikbaar |

---

### NFR-004.4: Dienstverlening Niet Conform Afspraken

| Aspect | Requirement |
|--------|-------------|
| **ID** | NFR-004.4 |
| **Categorie** | Organisatie |
| **Schade** | **HOOG** |
| **Kans** | Medium |
| **Prioriteit** | **P1 - HOOG** |

**User Stories:**

| Perspectief | User Story |
|-------------|------------|
| Organisatie | "Producten zijn duidelijk gespecificeerd met security non-functionals; wij handhaven kwaliteitscontrole en beheeracceptatiecriteria" |

**Verificatie Checklist:**
- [ ] SLA gedefinieerd
- [ ] Security requirements gedocumenteerd
- [ ] Acceptance criteria meetbaar
- [ ] Quality gates gedefinieerd
- [ ] Monitoring en alerting ingericht

---

## Fase-gebaseerde Verificatie

### Bij Analyse (Brown Paper Fase 1-2)
```
□ NFR-002.1: OWASP/CWE scan uitvoeren
□ NFR-002.3: Documentatie coverage meten
□ NFR-003.2: Encryptie gebruik analyseren
□ NFR-004.3: SIG metrics verzamelen
```

### Bij Design/Architectuur (Brown Paper Fase 3)
```
□ NFR-001.1: Error handling strategie
□ NFR-001.3: UX complexity beoordelen
□ NFR-003.1: Authenticatie architectuur
□ NFR-003.2: Encryptie strategie
□ NFR-003.3: Autorisatie model
```

### Bij Bouw/Verificatie (Brown Paper Fase 4-5)
```
□ NFR-002.1: Security tests uitgevoerd
□ NFR-002.2: Versiebeheer correct
□ NFR-003.1: Auth/Authz geïmplementeerd
□ NFR-003.2: Encryptie toegepast
□ NFR-004.3: Quality gates gehaald
□ NFR-004.4: Acceptatie criteria voldaan
```

---

## Mapping naar CWE Top 25

| NFR | Gerelateerde CWE's |
|-----|-------------------|
| NFR-002.1 | CWE-89 (SQLi), CWE-79 (XSS), CWE-78 (Cmd Inj), CWE-22 (Path Trav) |
| NFR-003.1 | CWE-287 (Auth), CWE-306 (Missing Auth), CWE-285 (Access Control) |
| NFR-003.2 | CWE-311 (No Encryption), CWE-327 (Weak Crypto), CWE-798 (Hardcoded) |
| NFR-003.3 | CWE-352 (CSRF), CWE-269 (Privilege) |

---

## Referenties

- [GEMMA Online - User stories voor informatiebeveiliging](https://gemmaonline.nl/wiki/User_stories_voor_informatiebeveiliging)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [cwe-top25-coverage-analysis.md](../plans/cwe-top25-coverage-analysis.md)

---

*Document versie: 1.0*
*Gegenereerd: 2026-01-13*
*MarQed AI Agent Platform*
