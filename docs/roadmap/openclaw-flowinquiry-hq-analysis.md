# OpenClaw + FlowInquiry HQ voor MarQed.ai

**Week:** 162 (2026-01-31)
**Status:** Analyse
**Type:** Architectuur & Integratie Plan

---

## 1. Executive Summary

Dit document beschrijft de architectuur en het implementatieplan voor de integratie van **OpenClaw** (executive assistant / sync-bot) en **FlowInquiry** (SLA administratie) met het bestaande **MarQed.ai** platform. De kern: OpenClaw fungeert als sync-laag tussen externe input (email, portal, Telegram) en MarQed's bestaande REST API (720+ endpoints), terwijl FlowInquiry de SLA-administratie en audit trail verzorgt.

**Geschatte effort:** ~64h, gefaseerd met security eerst.

---

## 2. Architectuur

```
                INTERNET-FACING (DMZ)                    INTERN NETWERK
                ---------------------                    ---------------

Email ──┐
         │    ┌──────────┐     ┌─────────────┐     ┌──────────────────────┐
Portal ──┼───►│ OpenClaw │────►│ FlowInquiry │     │  MarQed.ai Platform  │
         │    │ (Exec.   │◄───►│ (SLA admin) │     │                      │
Telegram─┘    │ Assistant)│     └─────────────┘     │  Confucius, Ralph,   │
 (jij)        └────┬─────┘                          │  12 agents,          │
                   │                                │  29 services         │
                   │    REST API (direct, intern)   │                      │
                   └───────────────────────────────►│  /confucius/workflows│
                   │◄───────────────────────────────│  /api/* endpoints    │
                   │    (status, resultaten)         │                      │
                   │                                └──────────────────────┘
                   ▼
            Sync terug naar:
            - FlowInquiry (ticket status)
            - Portal (resultaat overzichten)
            - Jou via Telegram (alerts)
```

### 2.1 Rollen

| Component | Rol | Wat het NIET is |
|-----------|-----|-----------------|
| **OpenClaw** | Executive assistant / sync-bot | NIET developer, NIET orchestrator |
| **FlowInquiry** | SLA administratie, ticket management, audit trail | NIET de executie-engine |
| **MarQed.ai** | Technische executie via bestaande REST API (720+ endpoints) | Ongewijzigd |
| **Telegram** | Jouw kanaal naar OpenClaw (alerts, SLA-rapportages, overrides) | NIET het primaire input-kanaal |

### 2.2 Omgevingen

| Omgeving | Doel | Componenten |
|----------|------|-------------|
| **Laptop 2** | Ontwikkeling | FlowInquiry + OpenClaw (skills, config, testing) |
| **Productieserver** | Runtime | MarQed.ai + FlowInquiry + OpenClaw (alle 3 naast elkaar) |

---

## 3. Security First — Fase 0 (Prio 1, niet overslaan)

> **Kritiek punt:** Security Fase 0 is niet optioneel. OpenClaw heeft bewezen kwetsbaarheden (prompt injection via email, plaintext credentials). Zonder S1-S10 is het systeem onacceptabel risicovol.

### 3.1 Maatregelen

| # | Maatregel | Waarom | Hoe |
|---|-----------|--------|-----|
| S1 | **OpenClaw op dedicated VM/container** | Isolatie van MarQed bij compromise | Docker container met beperkte network access |
| S2 | **Geen direct internet exposure** | OpenClaw mag niet van buitenaf bereikbaar zijn | Alleen outbound: IMAP, Telegram API, intern naar MarQed/FlowInquiry |
| S3 | **Secrets in Vault/1Password** | OpenClaw slaat credentials standaard in plaintext op | 1Password skill of HashiCorp Vault, NOOIT plaintext API keys |
| S4 | **Email skill: read-only + allowlist** | Bewezen prompt injection via email (Vectra AI research) | himalaya skill alleen read, alleen van bekende afzenders verwerken |
| S5 | **MarQed API: token-authenticated** | OpenClaw mag niet onbeperkt MarQed aanroepen | Dedicated API token met rate limiting, alleen workflow-start endpoints |
| S6 | **FlowInquiry: RBAC** | Beperkte toegang tot SLA data | OpenClaw krijgt eigen service account met minimale rechten |
| S7 | **Audit logging** | Alles wat OpenClaw doet moet traceerbaar zijn | OpenClaw session logs + FlowInquiry change log + MarQed CCTrace |
| S8 | **Sandboxed skill execution** | Custom skills mogen geen shell access hebben | OpenClaw sandbox mode: `agents.defaults.sandbox.mode: "non-main"` |
| S9 | **Request validatie** | OpenClaw mag niet blind email-content doorsturen naar MarQed | Classifier skill valideert en sanitized input voordat het naar MarQed gaat |
| S10 | **Netwerk segmentatie** | FlowInquiry/OpenClaw in DMZ, MarQed intern | Firewall rules: OpenClaw → MarQed alleen op specifieke API ports |

### 3.2 Security Verificatie Checklist (voor go-live)

- [ ] OpenClaw draait in isolated container
- [ ] Geen plaintext credentials in config files
- [ ] Email allowlist geconfigureerd (alleen bekende client domeinen)
- [ ] MarQed API token met rate limiting actief
- [ ] Prompt injection test uitgevoerd (stuur malicious email, verify geen executie)
- [ ] Network segmentatie getest (OpenClaw kan NIET bij MarQed DB/filesystem)
- [ ] FlowInquiry RBAC geconfigureerd
- [ ] Audit logging actief en geverifieerd
- [ ] Sandbox mode actief voor custom skills
- [ ] Tailscale/WireGuard tunnel getest (laptop 2 → productieserver)

---

## 4. Flow: Client Request → Resultaat

```
1. Client stuurt email of vult portal-formulier in
2. OpenClaw detecteert (email via himalaya IMAP poll / portal via webhook)
3. OpenClaw classificeert: type, urgentie, SLA-tier (met input sanitization)
4. OpenClaw maakt ticket aan in FlowInquiry via REST API
5. OpenClaw start MarQed workflow via REST API (authenticated)
6. OpenClaw pollt MarQed status (cron) → update FlowInquiry + Portal
7. SLA monitoring: escalatie bij 75% / 90% / 100% deadline
8. Bij voltooiing: resultaat → FlowInquiry DONE → client notificatie → Telegram rapport
```

---

## 5. Custom OpenClaw Skills (te bouwen op laptop 2)

| Skill | Doel | Effort |
|-------|------|--------|
| `marqed-connector` | MarQed REST API wrapper, workflow start/status/result, status mapping | ~8h |
| `flowinquiry-connector` | FlowInquiry ticket CRUD, SLA monitoring, escalatie-regels | ~8h |
| `request-classifier` | Email/portal parsing, classificatie, input sanitization | ~4h |
| `portal-sync` | Resultaten terugkoppelen naar marqed.ai portal | ~4h |

---

## 6. Fasering

| Fase | Wat | Effort | Voorwaarde |
|------|-----|--------|------------|
| **0: Security** | Hardening S1-S10, netwerk segmentatie, secrets management | ~12h | MOET EERST |
| **A: Basis** | OpenClaw installatie + marqed-connector + Telegram setup | ~20h | Fase 0 compleet |
| **B: SLA** | FlowInquiry installatie + flowinquiry-connector + SLA config | ~20h | Fase A compleet |
| **C: Automatisering** | Email monitoring + request-classifier + portal-sync | ~12h | Fase B compleet |
| **Totaal** | | **~64h** | |

---

## 7. Risico's

| # | Risico | Impact | Mitigatie |
|---|--------|--------|-----------|
| 1 | **Prompt injection via email** | HOOG | Read-only email, allowlist, input sanitization in classifier (S4, S9) |
| 2 | **OpenClaw credential leak** | HOOG | 1Password/Vault, geen plaintext, isolated container (S2, S3) |
| 3 | **MarQed API misuse via OpenClaw** | HOOG | Dedicated token, rate limiting, alleen workflow endpoints (S5) |
| 4 | **FlowInquiry instabiliteit** | MEDIUM | OpenClaw houdt local state als fallback |
| 5 | **OpenClaw update breekt skills** | MEDIUM | Pin versie, test op laptop 2 eerst |

---

## 8. Conclusie

Het model is **logisch en haalbaar**:

- OpenClaw als sync-bot past bij waarvoor het gebouwd is
- MarQed hoeft niet aangepast te worden (bestaande API)
- FlowInquiry vult de SLA-gap
- ~64h totale effort, gefaseerd met security eerst

**Kritiek punt:** Security Fase 0 is niet optioneel. OpenClaw heeft bewezen kwetsbaarheden (prompt injection via email, plaintext credentials). Zonder S1-S10 is het systeem onacceptabel risicovol.

---

## 9. Bronnen

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Skills](https://github.com/VoltAgent/awesome-openclaw-skills)
- [FlowInquiry GitHub](https://github.com/flowinquiry/flowinquiry)
- [FlowInquiry Docs](https://docs.flowinquiry.io/)
- [DarkReading: OpenClaw Security](https://www.darkreading.com/application-security/openclaw-ai-runs-wild-business-environments)
- [Vectra AI: Prompt Injection](https://www.vectra.ai/blog/clawdbot-to-moltbot-to-openclaw-when-automation-becomes-a-digital-backdoor)
- [IBM: OpenClaw Analysis](https://www.ibm.com/think/news/clawdbot-ai-agent-testing-limits-vertical-integration)
