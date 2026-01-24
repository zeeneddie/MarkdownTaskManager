# Unified Architecture Diagram - MarQed.ai Platform + mq Workflows

**Auteur**: Felix (Feature Architect)
**Datum**: 2026-01-24
**Versie**: 1.0
**Status**: Goedgekeurd

---

## 1. Unified Entry Point - Alle Workflow Types

```
+===============================================================================+
|                                                                               |
|                    MARQED.AI UNIFIED WORKFLOW ENTRY POINTS                    |
|                                                                               |
+===============================================================================+
|                                                                               |
|  DEVELOPER TERMINAL                     WEB INTERFACES                        |
|  ==================                     ==============                        |
|                                                                               |
|  +---------------------------+          +---------------------------+         |
|  |  $ mq bugfix              |          |  Hub Portal               |         |
|  |  $ mq changes             |          |  localhost:8000/          |         |
|  |  $ mq migration           |          |  (40 dashboards)          |         |
|  |  $ mq analyze             |          +---------------------------+         |
|  +---------------------------+                    |                           |
|              |                          +---------------------------+         |
|              |                          |  Customer Portal          |         |
|              |                          |  Feature Requests         |         |
|              |                          |  Progress Tracking        |         |
|              |                          +---------------------------+         |
|              |                                    |                           |
|              |                          +---------------------------+         |
|              |                          |  Progress Dashboard       |         |
|              |                          |  /dashboard/workflows     |         |
|              |                          |  [NIEUW - V1]             |         |
|              |                          +---------------------------+         |
|              |                                    |                           |
|              +------------------------------------+                           |
|                              |                                                |
|                              v                                                |
|  +-----------------------------------------------------------------------+   |
|  |                    UNIFIED WORKFLOW DISPATCHER                         |   |
|  |                    (platform-api.sh / API Gateway)                     |   |
|  +-----------------------------------------------------------------------+   |
|              |               |               |               |                |
|              v               v               v               v                |
|  +---------------+  +---------------+  +---------------+  +---------------+   |
|  | BUGFIX        |  | CHANGES       |  | MIGRATION     |  | ANALYZE       |   |
|  | 7 fasen       |  | 8 fasen       |  | 9 fasen       |  | 6 fasen       |   |
|  | Sequentieel   |  | Parallel opt. |  | Strangler Fig |  | Quick/Deep    |   |
|  +---------------+  +---------------+  +---------------+  +---------------+   |
|                                                                               |
+===============================================================================+
```

---

## 2. Workflow Type Details

### 2.1 Bugfix Workflow (marqed-bugfix.sh)

```
+===============================================================================+
|  BUGFIX WORKFLOW - 7 Fasen (Sequentieel)                                      |
+===============================================================================+
|                                                                               |
|  INPUT                                                                        |
|  +------------------+    +------------------+    +------------------+         |
|  | Bug Report       |--->| PRD.md           |--->| Codebase         |         |
|  | (optional)       |    |                  |    | Directory        |         |
|  +------------------+    +------------------+    +------------------+         |
|                                   |                                           |
|                                   v                                           |
|  FASES                                                                        |
|  +------------------------------------------------------------------------+  |
|  | Phase 1: Bug Reproduction              | 1-2h  | Betty Agent           |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 2: Root Cause Analysis           | 2-4h  | Betty + Quinn         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 3: Fix Implementation            | 2-6h  | Felix + Marcus        |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 4: Unit Testing                  | 1-2h  | Tessa                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 5: Integration Testing           | 1-2h  | Tessa + Quinn         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 6: Code Review                   | 0.5-1h| Quinn                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 7: Documentation                 | 0.5-1h| Diana                 |  |
|  +------------------------------------------------------------------------+  |
|                                                                               |
|  PLATFORM SERVICES AANGEROEPEN:                                               |
|  - CWE Scanner Suite (security check)                                         |
|  - Testing Services (regression)                                              |
|  - Quality Gates (validation)                                                 |
|                                                                               |
+===============================================================================+
```

### 2.2 Changes Workflow (marqed-changes.sh)

```
+===============================================================================+
|  CHANGES WORKFLOW - 8 Fasen (Parallel Optioneel)                              |
+===============================================================================+
|                                                                               |
|  INPUT                                                                        |
|  +------------------+    +------------------+    +------------------+         |
|  | Requirements.md  |--->| PRD.md           |--->| Codebase         |         |
|  | (optional)       |    |                  |    | Directory        |         |
|  +------------------+    +------------------+    +------------------+         |
|                                   |                                           |
|                                   v                                           |
|  FASES                                                                        |
|  +------------------------------------------------------------------------+  |
|  | Phase 1: Requirements Analysis         | 2-4h  | Peter                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 2: Design & Architecture         | 3-6h  | Felix + Vicky         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 3: Implementation                | 8-24h | Felix + Marcus        |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 4: Unit Testing                  | 2-4h  | Tessa                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 5: Integration Testing           | 2-4h  | Tessa + Quinn         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 6: Documentation                 | 1-2h  | Diana                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 7: Code Review                   | 1-2h  | Quinn                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 8: Deployment Preparation        | 1-2h  | Paul                  |  |
|  +------------------------------------------------------------------------+  |
|                                                                               |
|  PLATFORM SERVICES AANGEROEPEN:                                               |
|  - Deep Extraction Pipeline (requirements -> stories)                         |
|  - FP Methodology (IFPUG estimation)                                          |
|  - Hierarchical Story Extraction                                              |
|  - Quality Gates (validation)                                                 |
|                                                                               |
+===============================================================================+
```

### 2.3 Migration Workflow (marqed-migration.sh)

```
+===============================================================================+
|  MIGRATION WORKFLOW - 9 Fasen (Strangler Fig Pattern)                         |
+===============================================================================+
|                                                                               |
|  INPUT                                                                        |
|  +------------------+    +------------------+    +------------------+         |
|  | Source Codebase  |--->| PRD.md           |--->| Database Conn.   |         |
|  | (ASP/VB6/Java)   |    |                  |    | (optional)       |         |
|  +------------------+    +------------------+    +------------------+         |
|                                   |                                           |
|                                   v                                           |
|  FASES                                                                        |
|  +------------------------------------------------------------------------+  |
|  | Phase 1: Analysis & Planning           | 8h    | Miguel + Peter        |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 2: Infrastructure Setup          | 4h    | Felix                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 3: Database Migration            | 24h   | Miguel                |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 4: Core Application Migration    | 120h  | Miguel + Felix        |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 5: Testing & Validation          | 40h   | Tessa + Quinn         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 6: Security & Compliance         | 24h   | Quinn                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 7: Performance Optimization      | 16h   | Felix + Eliza         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 8: Documentation                 | 8h    | Diana                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 9: Deployment Preparation        | 8h    | Paul                  |  |
|  +------------------------------------------------------------------------+  |
|                                                                               |
|  PLATFORM SERVICES AANGEROEPEN:                                               |
|  - Brown Paper Service (6-fase enhanced analysis)                             |
|  - Business Rule Extractors (12 extractors)                                   |
|  - Migration Enhanced (7-fase execution)                                      |
|  - Dual-Run Comparison Service                                                |
|  - Data Lineage Service                                                       |
|  - Visual Regression Service                                                  |
|                                                                               |
+===============================================================================+
```

### 2.4 Analyze Workflow (marqed-analyze.sh)

```
+===============================================================================+
|  ANALYZE WORKFLOW - 6 Fasen (Quick/Standard/Deep modes)                       |
+===============================================================================+
|                                                                               |
|  INPUT                                                                        |
|  +------------------+    +------------------+    +------------------+         |
|  | Codebase Dir     |--->| Mode: quick/     |--->| Database Conn.   |         |
|  |                  |    | standard/deep    |    | (optional)       |         |
|  +------------------+    +------------------+    +------------------+         |
|                                   |                                           |
|                                   v                                           |
|  FASES                                                                        |
|  +------------------------------------------------------------------------+  |
|  | Phase 1: Tech Stack Detection          | Auto  | Miguel                |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 2: Automated Analysis Tools      | Varies| Quinn + Felix         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 3: Deep Code Analysis            | Varies| Quinn                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 4: Security & Compliance Audit   | Varies| Quinn                 |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 5: Prioritize Findings           | 2-4h  | Peter + Eliza         |  |
|  +------------------------------------------------------------------------+  |
|  | Phase 6: Generate Reports              | 1-2h  | Diana                 |  |
|  +------------------------------------------------------------------------+  |
|                                                                               |
|  OUTPUT SCENARIOS:                                                            |
|  A. Analysis Report only (default)                                            |
|  B. Generate Migration PRD (--generate-migration-prd)                         |
|  C. Create Backlog PRDs (--create-backlog)                                    |
|                                                                               |
|  PLATFORM SERVICES AANGEROEPEN:                                               |
|  - Hybrid Static-LLM Pipeline                                                 |
|  - CWE Scanner Suite (95% coverage)                                           |
|  - Compliance Frameworks (NEN7510, ISO27001, GDPR, HIPAA, SOC2, PCI-DSS)     |
|  - DevOps Analysis Services (Hot Spots, PR Patterns, CI/CD Health)            |
|  - CiRA Causality Detection                                                   |
|                                                                               |
+===============================================================================+
```

---

## 3. Frontend <-> Backend Connectie

```
+===============================================================================+
|                                                                               |
|                    FRONTEND <-> BACKEND ARCHITECTURE                          |
|                                                                               |
+===============================================================================+
|                                                                               |
|  LAYER 0: USER INTERFACES                                                     |
|  ========================                                                     |
|                                                                               |
|  +-------------------------+     +-------------------------+                  |
|  |      CLI LAYER          |     |      WEB LAYER          |                  |
|  |      (mq workflows)     |     |      (Portals)          |                  |
|  +-------------------------+     +-------------------------+                  |
|  |                         |     |                         |                  |
|  | marqed-bugfix.sh        |     | Hub Portal (40 views)   |                  |
|  |   |                     |     |   localhost:8000/       |                  |
|  | marqed-changes.sh       |     |                         |                  |
|  |   |                     |     | Customer Portal         |                  |
|  | marqed-migration.sh     |     |   (Strapi CMS)          |                  |
|  |   |                     |     |                         |                  |
|  | marqed-analyze.sh       |     | Progress Dashboard      |                  |
|  |   |                     |     |   /dashboard/workflows  |                  |
|  |   v                     |     |                         |                  |
|  | +-------------------+   |     |                         |                  |
|  | | platform-api.sh   |   |     |                         |                  |
|  | | (CLI -> API)      |   |     |                         |                  |
|  | +-------------------+   |     |                         |                  |
|  +------------|------------+     +-------------|------------+                 |
|               |                               |                               |
|               +---------------+---------------+                               |
|                               |                                               |
|                               v                                               |
|  LAYER 1: API GATEWAY                                                         |
|  ====================                                                         |
|                                                                               |
|  +-----------------------------------------------------------------------+   |
|  |                    FastAPI Gateway (700+ endpoints)                    |   |
|  |                    localhost:8000/api/                                 |   |
|  +-----------------------------------------------------------------------+   |
|  |                                                                        |   |
|  |  +-------------+  +-------------+  +-------------+  +-------------+   |   |
|  |  | Workflow    |  | Knowledge   |  | Validation  |  | Token       |   |   |
|  |  | API         |  | API         |  | API         |  | Context     |   |   |
|  |  | [NIEUW]     |  | [NIEUW]     |  | [NIEUW]     |  | API         |   |   |
|  |  +-------------+  +-------------+  +-------------+  +-------------+   |   |
|  |                                                                        |   |
|  |  +-------------+  +-------------+  +-------------+  +-------------+   |   |
|  |  | Brown Paper |  | Extraction  |  | Migration   |  | Testing     |   |   |
|  |  | API         |  | API         |  | API         |  | API         |   |   |
|  |  +-------------+  +-------------+  +-------------+  +-------------+   |   |
|  |                                                                        |   |
|  |  +-------------+  +-------------+  +-------------+  +-------------+   |   |
|  |  | Security    |  | Compliance  |  | CodeCharta  |  | DevOps      |   |   |
|  |  | API         |  | API         |  | API         |  | Analysis    |   |   |
|  |  +-------------+  +-------------+  +-------------+  +-------------+   |   |
|  |                                                                        |   |
|  +-----------------------------------------------------------------------+   |
|                               |                                               |
|                               v                                               |
|  LAYER 2: BACKEND SERVICES (290+ Services)                                    |
|  =========================================                                    |
|                                                                               |
|  +-----------------------------------------------------------------------+   |
|  |  ANALYSIS         | EXTRACTION       | KNOWLEDGE       | TESTING      |   |
|  |  SERVICES         | SERVICES         | SERVICES        | SERVICES     |   |
|  +-------------------+------------------+-----------------+--------------+   |
|  | Brown Paper       | Deep Extraction  | Tech Stack KB   | Charact.Test |   |
|  | CWE Scanner       | Hierarchical     | Experience      | Visual Regr. |   |
|  | FP Methodology    | Business Rules   | Continuous      | Dual-Run     |   |
|  | Confucius Orch.   | CiRA Causality   | Learning        | Performance  |   |
|  +-------------------+------------------+-----------------+--------------+   |
|                                                                               |
+===============================================================================+
```

---

## 4. Data Flow - Bugfix Request (Voorbeeld)

```
+===============================================================================+
|                                                                               |
|              DATA FLOW: BUGFIX REQUEST -> COMPLETION                          |
|                                                                               |
+===============================================================================+
|                                                                               |
|  STEP 1: REQUEST INITIATION                                                   |
|  ==========================                                                   |
|                                                                               |
|  Developer                                                                    |
|      |                                                                        |
|      | $ mq bugfix --id BUG-2026-01-24-001 --codebase ./src                   |
|      |                                                                        |
|      v                                                                        |
|  +-------------------+                                                        |
|  | marqed-bugfix.sh  |                                                        |
|  +-------------------+                                                        |
|      |                                                                        |
|      | 1. Source common functions                                             |
|      | 2. check_platform_required()                                           |
|      |                                                                        |
|      v                                                                        |
|  +-------------------+     HTTP GET     +-------------------+                 |
|  | platform-api.sh   |----------------->| /health           |                 |
|  +-------------------+                  +-------------------+                 |
|      |                                                                        |
|      | 3. Platform OK? Continue                                               |
|      |                                                                        |
+===============================================================================+
|                                                                               |
|  STEP 2: WORKFLOW CREATION                                                    |
|  =========================                                                    |
|                                                                               |
|  +-------------------+     HTTP POST    +-------------------+                 |
|  | platform-api.sh   |----------------->| /api/v2/workflow  |                 |
|  | create_workflow() |                  +-------------------+                 |
|  +-------------------+                           |                            |
|                                                  v                            |
|                                         +-------------------+                 |
|                                         | WorkflowService   |                 |
|                                         +-------------------+                 |
|                                                  |                            |
|                                                  | Insert workflow record     |
|                                                  v                            |
|                                         +-------------------+                 |
|                                         | PostgreSQL        |                 |
|                                         | workflow table    |                 |
|                                         +-------------------+                 |
|                                                                               |
+===============================================================================+
|                                                                               |
|  STEP 3: KNOWLEDGE LOOKUP [V2]                                                |
|  =============================                                                |
|                                                                               |
|  +-------------------+     HTTP POST    +------------------------+            |
|  | platform-api.sh   |----------------->| /api/v2/knowledge/     |            |
|  | lookup_knowledge()|                  | lookup                 |            |
|  +-------------------+                  +------------------------+            |
|                                                  |                            |
|                                                  v                            |
|                                         +------------------------+            |
|                                         | TechStackKnowledge     |            |
|                                         | Service                |            |
|                                         +------------------------+            |
|                                                  |                            |
|                           +----------------------+----------------------+     |
|                           |                      |                      |     |
|                           v                      v                      v     |
|                  +----------------+    +----------------+    +----------------+|
|                  | Experience     |    | Continuous     |    | ChromaDB       ||
|                  | Store          |    | Learning Svc   |    | Similarity     ||
|                  +----------------+    +----------------+    +----------------+|
|                           |                      |                      |     |
|                           +----------------------+----------------------+     |
|                                                  |                            |
|                                                  v                            |
|                                         +------------------------+            |
|                                         | KnowledgeResult:       |            |
|                                         | - Similar projects     |            |
|                                         | - Known pitfalls       |            |
|                                         | - Effort estimate      |            |
|                                         | - Recommendations      |            |
|                                         +------------------------+            |
|                                                                               |
+===============================================================================+
|                                                                               |
|  STEP 4: PHASE EXECUTION (Per Phase)                                          |
|  ===================================                                          |
|                                                                               |
|  +-------------------+                                                        |
|  | marqed-bugfix.sh  |                                                        |
|  | Phase 1: Repro    |                                                        |
|  +-------------------+                                                        |
|          |                                                                    |
|          | Claude Code task execution                                         |
|          v                                                                    |
|  +-------------------+                  +-------------------+                 |
|  | Claude CLI        |   CLI-First     | Claude Opus 4.5   |                 |
|  | claude --print    |---------------->| (Max Subscription)|                 |
|  +-------------------+                  +-------------------+                 |
|          |                                                                    |
|          | Task completed                                                     |
|          v                                                                    |
|  +-------------------+     HTTP PATCH   +-------------------+                 |
|  | platform-api.sh   |----------------->| /api/v2/workflow/ |                 |
|  | update_task()     |                  | {id}/tasks/{tid}  |                 |
|  +-------------------+                  +-------------------+                 |
|          |                                                                    |
|          | Broadcast to dashboard via WebSocket                               |
|          v                                                                    |
|  +-------------------+     WebSocket    +-------------------+                 |
|  | Progress          |<-----------------| Real-time update  |                 |
|  | Dashboard         |                  +-------------------+                 |
|  +-------------------+                                                        |
|                                                                               |
+===============================================================================+
|                                                                               |
|  STEP 5: SECURITY SCANNING (During Code Review Phase)                         |
|  ====================================================                         |
|                                                                               |
|  +-------------------+     HTTP POST    +-------------------+                 |
|  | platform-api.sh   |----------------->| /api/v2/security/ |                 |
|  | run_security_scan |                  | scan              |                 |
|  +-------------------+                  +-------------------+                 |
|                                                  |                            |
|                                                  v                            |
|                                         +-------------------+                 |
|                                         | CWE Scanner Suite |                 |
|                                         | - OpenGrep        |                 |
|                                         | - Bandit          |                 |
|                                         | - Trivy           |                 |
|                                         | - Custom ASP      |                 |
|                                         +-------------------+                 |
|                                                  |                            |
|                                                  v                            |
|                                         +-------------------+                 |
|                                         | Security Report   |                 |
|                                         | - Vulnerabilities |                 |
|                                         | - CWE IDs         |                 |
|                                         | - Severity        |                 |
|                                         +-------------------+                 |
|                                                                               |
+===============================================================================+
|                                                                               |
|  STEP 6: VALIDATION & COMPLETION                                              |
|  ===============================                                              |
|                                                                               |
|  +-------------------+     HTTP POST    +------------------------+            |
|  | platform-api.sh   |----------------->| /api/v2/validation/    |            |
|  | run_validation()  |                  | visual-regression      |            |
|  +-------------------+                  +------------------------+            |
|                                                  |                            |
|                                                  v                            |
|                                         +------------------------+            |
|                                         | VisualRegressionService|            |
|                                         | - Screenshot capture   |            |
|                                         | - Diff analysis        |            |
|                                         +------------------------+            |
|                                                  |                            |
|                                                  v                            |
|  +-------------------+     HTTP PATCH   +-------------------+                 |
|  | platform-api.sh   |----------------->| /api/v2/workflow/ |                 |
|  | complete_workflow |                  | {id}/complete     |                 |
|  +-------------------+                  +-------------------+                 |
|          |                                                                    |
|          | Final status update                                                |
|          v                                                                    |
|  +-------------------+                  +-------------------+                 |
|  | Progress          |   Shows "DONE"  | Customer Portal   |                 |
|  | Dashboard         |   Real-time     | Status: Resolved  |                 |
|  +-------------------+                  +-------------------+                 |
|                                                                               |
+===============================================================================+
```

---

## 5. Complete System Architecture

```
+===============================================================================================+
|                                                                                               |
|                    MARQED.AI UNIFIED PLATFORM ARCHITECTURE                                    |
|                    Platform v8.6 + mq Workflows v2.1                                          |
|                                                                                               |
+===============================================================================================+
|                                                                                               |
|  LAAG 0: GEBRUIKERSINTERFACE                                                                  |
|  ===========================                                                                  |
|                                                                                               |
|  +---------------------------+              +------------------------------------------+      |
|  |  DEVELOPER                |              |  KLANT                                   |      |
|  |  (vim/VSCode + Terminal)  |              |  (Browser)                               |      |
|  |                           |              |                                          |      |
|  |  - mq bugfix             -+              |  - Feature Requests                      |      |
|  |  - mq changes            -+              |  - Progress Tracking                     |      |
|  |  - mq migration          -+              |  - Roadmap View                          |      |
|  |  - mq analyze            -+              |  - Test Results                          |      |
|  +------------|--------------+              +------------------|-----------------------+      |
|               |                                                |                              |
+===============|================================================|==============================+
|               |                                                |                              |
|  LAAG 1: CLI & WEB LAYER                                                                      |
|  =======================                                                                      |
|               |                                                |                              |
|  +------------v--------------+              +------------------v-----------------------+      |
|  |  mq CLI LAYER             |              |  WEB LAYER                               |      |
|  +---------------------------+              +------------------------------------------+      |
|  |                           |              |                                          |      |
|  |  marqed-bugfix.sh         |              |  Hub Portal (40 views)                   |      |
|  |  marqed-changes.sh        |              |  localhost:8000/                         |      |
|  |  marqed-migration.sh      |              |                                          |      |
|  |  marqed-analyze.sh        |              |  Customer Portal (Strapi)                |      |
|  |         |                 |              |                                          |      |
|  |  +------v------+          |              |  Progress Dashboard [V1]                 |      |
|  |  | platform-   |          |              |  /dashboard/workflows                    |      |
|  |  | api.sh      |          |              |                                          |      |
|  |  | (CLI->API)  |          |              |                                          |      |
|  |  +------+------+          |              +------------------+-----------------------+      |
|  +---------|--|--------------+                                 |                              |
|            |  |                                                |                              |
|            |  +------------------------------------------------+                              |
|            |                           |                                                      |
+============|===========================|======================================================+
|            |                           |                                                      |
|  LAAG 2: API GATEWAY (FastAPI - 700+ endpoints)                                               |
|  ==============================================                                               |
|            |                           |                                                      |
|            +-------------+-------------+                                                      |
|                          |                                                                    |
|  +-----------------------v---------------------------------------------------------------+   |
|  |                           MarQed.ai API Gateway                                        |   |
|  |                           localhost:8000/api/                                          |   |
|  +---------------------------------------------------------------------------------------+   |
|  |                                                                                        |   |
|  |  NEW ENDPOINTS (voor mq integratie)      |  EXISTING ENDPOINTS                         |   |
|  |  ======================================  |  ==========================================  |   |
|  |                                          |                                             |   |
|  |  POST /api/v2/workflow/                  |  POST /api/bmad/{id}/enhanced-analyze      |   |
|  |  GET  /api/v2/workflow/{id}              |  GET  /api/brown-paper/metrics             |   |
|  |  GET  /api/v2/workflow/active            |  POST /api/extraction/start                |   |
|  |  PATCH /api/v2/workflow/{id}/tasks/{tid} |  GET  /api/migration/{id}/status           |   |
|  |                                          |  POST /api/testing/dual-run/start          |   |
|  |  POST /api/v2/knowledge/lookup           |  POST /api/security/scan                   |   |
|  |  GET  /api/v2/knowledge/patterns         |  GET  /api/codecharta/export               |   |
|  |                                          |  POST /api/compliance/check                |   |
|  |  POST /api/v2/validation/visual-regr     |  GET  /api/devops-analysis/{id}            |   |
|  |  POST /api/v2/validation/performance     |  POST /api/cira/causality                  |   |
|  |                                          |                                             |   |
|  +---------------------------------------------------------------------------------------+   |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 3: AGENT ARCHITECTUUR (11 Core + Stack Templates)                                       |
|  ======================================================                                       |
|                          |                                                                    |
|  +-----------------------v---------------------------------------------------------------+   |
|  |                                                                                        |   |
|  |  CORE AGENTS (11 - Cross-Stack)                                                        |   |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+  +--------+               |   |
|  |  | Felix  |  | Quinn  |  | Betty  |  | Eliza  |  | Diana  |  | Vicky  |               |   |
|  |  | Arch.  |  | Quality|  | Bugs   |  | Estim. |  | Docs   |  | Design |               |   |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+  +--------+               |   |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+                           |   |
|  |  | Marcus |  | Tessa  |  | Miguel |  | Peter  |  | Paul   |                           |   |
|  |  | Maint. |  | Test   |  | Migrate|  | Product|  | Plan   |                           |   |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+                           |   |
|  |                                                                                        |   |
|  |  STACK TEMPLATES: Python | TypeScript | .NET | Java | Go | Rust                       |   |
|  |  PLATFORM AGENTS: ObservabilityEngineer | PromptEngineer | ContextManager             |   |
|  |                                                                                        |   |
|  +---------------------------------------------------------------------------------------+   |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 4: BACKEND SERVICES (290+ Services)                                                     |
|  ========================================                                                     |
|                          |                                                                    |
|  +-----------------------v---------------------------------------------------------------+   |
|  |                                                                                        |   |
|  |  ANALYSIS SERVICES           |  EXTRACTION SERVICES        |  KNOWLEDGE SERVICES      |   |
|  |  ===================         |  ====================       |  ==================      |   |
|  |  Brown Paper (6-fase)        |  Deep Extraction Pipeline   |  Tech Stack KB [NIEUW]   |   |
|  |  CWE Scanner Suite (95%)     |  Hierarchical Story Extr.   |  Experience Store        |   |
|  |  FP Methodology (IFPUG)      |  Business Rule Extractors   |  Continuous Learning     |   |
|  |  Confucius Orchestrator      |  CiRA Causality Detection   |  Workflow Task Store     |   |
|  |  Stability Analysis (8 cat)  |  Static Analysis Orch.      |                          |   |
|  |  DevOps Analysis (7 svc)     |  NFR Detector               |                          |   |
|  |                              |                              |                          |   |
|  |  TESTING SERVICES            |  VALIDATION SERVICES         |  MIGRATION SERVICES      |   |
|  |  =================           |  ===================         |  ==================      |   |
|  |  Characterization Tests      |  Visual Regression           |  Migration Enhanced      |   |
|  |  Dual-Run Comparison         |  Performance Baseline        |  Strangler Fig           |   |
|  |  Code Coverage Analyzer      |  Quality Gates (42 rules)    |  Library Mapping         |   |
|  |  Dead Code Detector          |  Compliance (6 frameworks)   |  Data Lineage            |   |
|  |                              |                              |                          |   |
|  +---------------------------------------------------------------------------------------+   |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 5: LLM PROVIDER LAYER (CLI-First + 7 API Providers)                                     |
|  ========================================================                                     |
|                          |                                                                    |
|  +-----------------------v---------------------------------------------------------------+   |
|  |                                                                                        |   |
|  |  CLI-FIRST (mq Workflows)                         PRIORITEIT: PRIMAIR                  |   |
|  |  +----------------------------------------------------------------------------------+  |   |
|  |  |  claude --print --model {haiku|sonnet|opus}                                      |  |   |
|  |  |  - Max Subscription (EUR100/maand) = voorspelbare kosten                         |  |   |
|  |  |  - Hogere rate limits                                                            |  |   |
|  |  |  - Native integratie met mq workflows                                            |  |   |
|  |  +----------------------------------------------------------------------------------+  |   |
|  |                                                                                        |   |
|  |  API PROVIDERS (Platform Services)                PRIORITEIT: SECUNDAIR               |   |
|  |  +----------+  +----------+  +----------+  +----------+  +----------+  +----------+   |   |
|  |  | Ollama   |  | Groq     |  | Alibaba  |  | Gemini   |  | OpenAI   |  | Anthropic|   |   |
|  |  | (Local)  |  | (Fast)   |  | (Qwen)   |  | (Google) |  | (GPT)    |  | (Fallback|   |   |
|  |  | FREE     |  | 840 TPS  |  | 1M ctx   |  | Flash/Pro|  | 5.2 Code |  |  API)    |   |   |
|  |  +----------+  +----------+  +----------+  +----------+  +----------+  +----------+   |   |
|  |                                                                                        |   |
|  +---------------------------------------------------------------------------------------+   |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 6: DATA & OBSERVABILITY                                                                 |
|  ============================                                                                 |
|                          |                                                                    |
|  +-----------------------v---------------------------------------------------------------+   |
|  |                                                                                        |   |
|  |  DATABASES                            |  OBSERVABILITY                                 |   |
|  |  =========                            |  =============                                 |   |
|  |  +------------------+                 |  +------------------+  +------------------+    |   |
|  |  | PostgreSQL       |                 |  | CCTrace          |  | Claude-Mem       |    |   |
|  |  | (198+ tables)    |                 |  | (thinking blocks)|  | (11 auto-tags)   |    |   |
|  |  | Port: 5433       |                 |  +------------------+  +------------------+    |   |
|  |  +------------------+                 |                                                |   |
|  |  +------------------+                 |  +------------------+  +------------------+    |   |
|  |  | ChromaDB         |                 |  | Self-Evolution   |  | Token Cache      |    |   |
|  |  | (Vector Store)   |                 |  | (Experience Str) |  | Metrics          |    |   |
|  |  | Port: 8001       |                 |  | (5 collections)  |  |                  |    |   |
|  |  +------------------+                 |  +------------------+  +------------------+    |   |
|  |  +------------------+                 |                                                |   |
|  |  | Redis            |                 |                                                |   |
|  |  | (Celery Queue)   |                 |                                                |   |
|  |  +------------------+                 |                                                |   |
|  |  +------------------+                 |                                                |   |
|  |  | JSON Files       |                 |                                                |   |
|  |  | (mq task state)  |                 |                                                |   |
|  |  | ~/.marqed/       |                 |                                                |   |
|  |  +------------------+                 |                                                |   |
|  |                                                                                        |   |
|  +---------------------------------------------------------------------------------------+   |
|                                                                                               |
+===============================================================================================+
```

---

## 6. Workflow Mapping Matrix

| mq Workflow | Platform Workflow Type | Primaire Agents | Backend Services |
|-------------|------------------------|-----------------|------------------|
| `marqed-bugfix.sh` | BUG | Betty -> Tessa -> Diana | CWE Scanner, Testing Services, Quality Gates |
| `marqed-changes.sh` | NEW_FEATURE / ENHANCEMENT | Peter -> Felix -> Tessa -> Diana | Deep Extraction, FP Methodology, Hierarchical Story |
| `marqed-migration.sh` | BROWN_PAPER_ENHANCED + MIGRATION_ENHANCED | Miguel -> Peter -> Felix -> Quinn -> Eliza -> Diana | Brown Paper (6-fase), Business Rule Extractors (12), Migration Enhanced (7-fase), Dual-Run Comparison, Data Lineage |
| `marqed-analyze.sh` | QUALITY_AUDIT | Quinn -> Felix -> Marcus | Hybrid Static-LLM Pipeline, CWE Scanner Suite (95%), Compliance Frameworks (6), DevOps Analysis (7 svc), CiRA Causality |

---

## 7. Key Integration Points

### 7.1 Nieuwe API Endpoints (V1-V3 Integratie)

```
# Workflow Management (V4 - Foundation)
POST /api/v2/workflow/                    # Create workflow
GET  /api/v2/workflow/{id}                # Get workflow status
GET  /api/v2/workflow/active              # List active workflows
PATCH /api/v2/workflow/{id}/tasks/{tid}   # Update task status

# Knowledge Lookup (V2 - Tech Stack Knowledge)
POST /api/v2/knowledge/lookup             # Find similar projects/pitfalls
GET  /api/v2/knowledge/patterns/{stack}   # Get proven patterns

# Validation (V3 - Self-Validation)
POST /api/v2/validation/visual-regression # Run visual diff
POST /api/v2/validation/performance       # Check performance baseline
```

### 7.2 CLI Bridge Functions (platform-api.sh)

```bash
# Connection
check_platform_required()      # Verify platform is running

# Workflow
create_workflow()              # Create new workflow
get_workflow()                 # Get workflow status
update_task_status()           # Update task progress
sync_tasks_to_platform()       # Sync Claude tasks to DB

# Knowledge
lookup_existing_knowledge()    # Find similar projects

# Security
run_security_scan()            # Trigger CWE Scanner

# Validation
run_visual_regression()        # Visual diff check
run_performance_baseline()     # Performance check
```

---

**Einde Document**

*Felix - Feature Architect*
*MarQed.ai Platform Team*
