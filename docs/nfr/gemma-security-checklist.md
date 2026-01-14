# GEMMA Security Checklist - Quick Reference

**Gebruik:** Snelle verificatie bij code reviews, analyses en deployments

---

## P0 - KRITIEK (Altijd Controleren)

### Programmatuur (NFR-002.1)
- [ ] **SQL Injection** - Prepared statements/parameterized queries
- [ ] **XSS** - Output encoding, CSP headers
- [ ] **Command Injection** - Input sanitization, geen shell exec met user input
- [ ] **Path Traversal** - Pad validatie, geen `..` in user input
- [ ] **OWASP Top 10** - Geen bekende kwetsbaarheden

### Gegevens (NFR-003.1, NFR-003.2)
- [ ] **Authenticatie** - Sterke wachtwoorden, account lockout
- [ ] **Autorisatie** - RBAC, least privilege
- [ ] **Encryptie** - TLS 1.2+, geen MD5/SHA1/DES
- [ ] **Credentials** - Geen hardcoded passwords/keys
- [ ] **Logging** - Alle toegangspogingen gelogd

---

## P1 - HOOG (Controleren bij Nieuwe Features)

### Gegevens (NFR-003.3, NFR-003.4)
- [ ] **2FA** - Voor gevoelige data/acties
- [ ] **Session** - Timeout, secure cookies
- [ ] **Audit** - Data access logging
- [ ] **Export** - Bulk download detectie

### Organisatie (NFR-004.3, NFR-004.4)
- [ ] **Code Review** - Verplicht voor merge
- [ ] **Tests** - Unit + integration + security
- [ ] **Quality Gates** - SIG score acceptabel
- [ ] **Documentatie** - API docs, handleidingen

---

## P2 - MEDIUM (Periodiek Controleren)

### Mens/Personeel (NFR-001.x)
- [ ] **Error Handling** - Duidelijke meldingen, geen stack traces
- [ ] **UX** - Gebruiksvriendelijk, bevestigingsdialogen
- [ ] **Procedures** - Gedocumenteerd, gecommuniceerd

### Programmatuur (NFR-002.2, NFR-002.3)
- [ ] **Versiebeheer** - Semantic versioning, changelog
- [ ] **Documentatie** - Compleet en actueel

---

## MarQed Scanner Status

| Categorie | Scanner | Status |
|-----------|---------|--------|
| **Beschikbaar** |||
| Resource Leaks | ResourceLeakDetector | 🟢 |
| Complexity | ComplexityAnalyzer | 🟢 |
| Duplication | DuplicationAnalyzer | 🟢 |
| Comments | CommentsAnalyzer | 🟢 |
| Coupling | CouplingAnalyzer | 🟢 |
| **Gepland (Fase 31)** |||
| SQL Injection | SQLInjectionDetector | 🔴 Week 145-147 |
| XSS | XSSDetector | 🔴 Week 145-147 |
| Authentication | AuthDetector | 🔴 Week 148-150 |
| Encryption | EncryptionDetector | 🔴 Week 151-153 |

---

## Code Review Vragen

1. **Kan user input SQL/commands uitvoeren?**
2. **Wordt output correct ge-escaped?**
3. **Is authenticatie/autorisatie gecontroleerd?**
4. **Zijn gevoelige data versleuteld?**
5. **Zijn fouten correct afgehandeld (zonder info leak)?**
6. **Is de code gedocumenteerd en testbaar?**

---

*Bron: [GEMMA Informatiebeveiliging](https://gemmaonline.nl/wiki/User_stories_voor_informatiebeveiliging)*
