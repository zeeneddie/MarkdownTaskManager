# Code Analysis PRD Template - MarQed.ai Methodology

**Project**: [Project Name]  
**Analysis ID**: [ANALYZE-YYYY-MM-DD-NNN]  
**Date**: [Date]  
**Analyst**: [Name/Team]

---

## 🎯 Analysis Objectives

### Primary Goals
- [ ] Code quality assessment
- [ ] Security vulnerability identification
- [ ] Performance bottleneck detection
- [ ] Architecture review
- [ ] Technical debt quantification
- [ ] Compliance verification (NEN7510, ISO27001, GDPR)
- [ ] Migration readiness assessment

### Deliverables
- [ ] Comprehensive analysis report
- [ ] Security audit findings
- [ ] Technical debt roadmap
- [ ] WBSO verantwoordingsrapportage
- [ ] Migration PRD (if applicable)
- [ ] Prioritized backlog (if applicable)

---

## 📊 Codebase Information

### Source Details
**Location**: [Path to codebase]  
**Repository**: [Git URL if applicable]  
**Branch/Version**: [Branch name or version]

### Technology Stack
**Detected Stack**: [To be auto-detected]  
- Primary Language: [ASP Classic / C# / Java / Python / Other]
- Framework: [Version]
- Database: [Type and version]
- Dependencies: [Key dependencies]

### Size & Complexity
**Lines of Code**: [To be measured]  
**File Count**: [To be counted]  
**Complexity Estimate**: [Small < 10K / Medium 10K-100K / Large 100K-1M / Enterprise > 1M]

---

## 🔍 Analysis Scope

### What to Analyze
- [ ] **Code Quality**: Complexity, duplication, maintainability
- [ ] **Security**: Vulnerabilities, OWASP Top 10, dependencies
- [ ] **Performance**: Bottlenecks, slow queries, memory issues
- [ ] **Architecture**: Structure, coupling, layering, patterns
- [ ] **Technical Debt**: TODO's, deprecated code, legacy patterns
- [ ] **Compliance**: NEN7510, ISO27001, GDPR requirements
- [ ] **Documentation**: Coverage, quality, completeness
- [ ] **Testing**: Coverage, quality, test types

### What to Exclude
[List any areas to skip, e.g., "Third-party libraries", "Generated code"]

---

## 🎛️ Analysis Configuration

### Mode Selection
- [ ] **Quick** (2-4h): Basic metrics, high-level overview
- [ ] **Standard** (8-12h): Comprehensive analysis, all areas
- [ ] **Deep** (20-30h): Everything + manual review + expert analysis
- [ ] **Incremental**: Only analyze changes since last run
- [ ] **Focused**: Specific areas only [specify which]

### Execution Options
- [ ] **Pausable**: Enable stop/resume capability
- [ ] **Parallel**: Use multiple analysis sessions
- [ ] **Continuous**: Watch mode for live updates

---

## 📈 Expected Outcomes

### Scenario Selection
- [ ] **Scenario A**: Standalone analysis with reports only
- [ ] **Scenario B**: Analysis → Auto-generate Migration PRD
- [ ] **Scenario C**: Analysis → Prioritized backlog (multiple PRDs)

### Report Formats
- [x] **Markdown** (always generated)
- [ ] **JSON** export for tooling integration
- [ ] **HTML** dashboard for stakeholders
- [ ] **Excel** export for spreadsheet analysis
- [ ] **PDF** executive summary
- [ ] **GitHub Issues** auto-creation

---

## ✅ Validation Phases

### Phase 1: Discovery & Detection
**Duration**: ~2 hours  
**Objective**: Understand codebase structure and technology

**Tasks**:
```json
{
  "id": "analyze-phase1-discovery",
  "title": "Discover codebase structure and tech stack",
  "description": "Auto-detect technology stack, map file structure, identify entry points and dependencies",
  "dependencies": [],
  "estimatedTime": "2h",
  "parallelizable": false
}
```

**Activities**:
1. **Tech Stack Detection**:
```bash
   # Detect based on file patterns
   - .csproj/.sln → .NET
   - package.json → JavaScript/Node
   - requirements.txt → Python
   - *.asp/*.vbs → ASP Classic
   - pom.xml → Java
   - composer.json → PHP
```

2. **File Structure Mapping**:
   - Count files by type
   - Identify directory structure
   - Map entry points (Main, startup files)
   - Document project organization

3. **Dependency Analysis**:
   - Extract package references
   - Identify external integrations
   - Map internal dependencies
   - Document API contracts

4. **Statistics Collection**:
   - Total lines of code
   - Files per language
   - Average file size
   - Largest files/modules

**Validation**:
- [ ] Tech stack correctly identified
- [ ] File structure documented
- [ ] Entry points identified
- [ ] Dependencies mapped
- [ ] Statistics collected

**Passes**: false  
**Notes**: []

---

### Phase 2: Automated Analysis
**Duration**: ~4-8 hours (depends on codebase size)  
**Objective**: Run automated analysis tools

**Tasks**:
```json
{
  "id": "analyze-phase2-automated",
  "title": "Execute automated analysis tools",
  "description": "Run static analysis, security scanners, quality metrics, and compliance checks",
  "dependencies": ["analyze-phase1-discovery"],
  "estimatedTime": "6h",
  "parallelizable": true
}
```

**Activities**:

1. **Static Code Analysis**:
   
   **ASP Classic**:
```bash
   # Custom pattern detection
   - SQL injection patterns
   - XSS vulnerabilities
   - Hardcoded credentials
   - Response.Write usage
   - Session management issues
```
   
   **.NET/C#**:
```bash
   # Roslyn Analyzers
   dotnet format --verify-no-changes --severity info
   
   # SonarScanner
   sonar-scanner \
     -Dsonar.projectKey=${PROJECT_KEY} \
     -Dsonar.sources=. \
     -Dsonar.host.url=${SONAR_HOST}
```
   
   **Java**:
```bash
   # SpotBugs
   spotbugs -textui -effort:max -html -output report.html ./target/classes
   
   # PMD
   pmd -d ./src -R rulesets/java/quickstart.xml -f html -r pmd-report.html
   
   # Checkstyle
   checkstyle -c /google_checks.xml src/
```
   
   **Python**:
```bash
   # Pylint
   pylint --output-format=json src/ > pylint-report.json
   
   # Flake8
   flake8 --format=html --htmldir=flake8-report src/
   
   # Mypy (type checking)
   mypy --html-report mypy-report src/
```

2. **Security Scanning**:
   
   **Dependency Vulnerabilities**:
```bash
   # .NET
   dotnet list package --vulnerable --include-transitive
   
   # Java
   mvn dependency-check:check
   
   # Python
   safety check --json > safety-report.json
   pip-audit --format json > pip-audit.json
   
   # Node.js
   npm audit --json > npm-audit.json
```
   
   **Code Vulnerabilities**:
```bash
   # Bandit (Python)
   bandit -r src/ -f json -o bandit-report.json
   
   # Semgrep (multi-language)
   semgrep --config=auto --json src/ > semgrep-report.json
   
   # Snyk (multi-language)
   snyk test --json > snyk-report.json
```

3. **Code Quality Metrics**:
```bash
   # Complexity
   - Cyclomatic complexity per function
   - Cognitive complexity
   - Nesting depth
   
   # Duplication
   - Duplicate code blocks
   - Clone detection
   - Similar code patterns
   
   # Maintainability
   - Maintainability index
   - Technical debt ratio
   - Code smells count
```

4. **Performance Analysis**:
```bash
   # Identify potential bottlenecks
   - N+1 query patterns
   - Large loops
   - Inefficient algorithms
   - Memory-intensive operations
   - Synchronous blocking calls
```

**Validation**:
- [ ] All tools executed successfully
- [ ] Results collected and parsed
- [ ] No tool execution errors
- [ ] Data ready for deep analysis

**Passes**: false  
**Notes**: []

---

### Phase 3: Deep Analysis
**Duration**: ~6-12 hours  
**Objective**: Expert-level code analysis

**Tasks**:
```json
{
  "id": "analyze-phase3-deep",
  "title": "Perform deep code analysis",
  "description": "Architecture review, pattern detection, technical debt scoring, and data flow analysis",
  "dependencies": ["analyze-phase2-automated"],
  "estimatedTime": "8h",
  "parallelizable": true
}
```

**Activities**:

1. **Architecture Review**:
   - Identify architectural patterns (MVC, layered, microservices, etc.)
   - Map component dependencies
   - Analyze coupling and cohesion
   - Document architecture violations
   - Identify circular dependencies

2. **Design Pattern Analysis**:
   - Detect patterns in use (Singleton, Factory, Repository, etc.)
   - Identify anti-patterns (God Object, Spaghetti Code, etc.)
   - Document pattern violations
   - Recommend pattern improvements

3. **Technical Debt Identification**:
   
   **Code Smells**:
   - Long methods (>50 lines)
   - Large classes (>500 lines)
   - Long parameter lists (>5 params)
   - Duplicated code
   - Dead code
   - Commented-out code
   - Magic numbers/strings
   - Poor naming
   
   **TODO/FIXME Analysis**:
```bash
   # Find all TODOs and FIXMEs
   grep -r "TODO\|FIXME\|HACK\|XXX" src/ > todos.txt
   
   # Categorize by severity
   - Critical (security, data loss risk)
   - High (functionality broken)
   - Medium (technical debt)
   - Low (nice-to-have improvements)
```
   
   **Deprecated Code**:
   - Find usage of deprecated APIs
   - Identify legacy patterns
   - Document migration paths

4. **Data Flow Analysis**:
   - Map data sources and sinks
   - Identify sensitive data handling
   - Document data transformations
   - Check data validation points

5. **Business Logic Extraction**:
   - Identify core business rules
   - Document critical algorithms
   - Map workflow implementations
   - Highlight complex logic areas

**Validation**:
- [ ] Architecture documented
- [ ] Patterns identified
- [ ] Technical debt catalogued
- [ ] Data flows mapped
- [ ] Business logic extracted

**Passes**: false  
**Notes**: []

---

### Phase 4: Security & Compliance Deep Dive
**Duration**: ~4-8 hours  
**Objective**: Comprehensive security and compliance assessment

**Tasks**:
```json
{
  "id": "analyze-phase4-security",
  "title": "Security and compliance audit",
  "description": "OWASP verification, healthcare compliance checks, vulnerability prioritization",
  "dependencies": ["analyze-phase2-automated", "analyze-phase3-deep"],
  "estimatedTime": "6h",
  "parallelizable": true
}
```

**Activities**:

1. **OWASP Top 10 Verification**:
   
   **A01: Broken Access Control**:
   - Check authorization on all endpoints
   - Verify role-based access control
   - Test for privilege escalation
   
   **A02: Cryptographic Failures**:
   - Identify sensitive data in transit/rest
   - Check encryption usage
   - Verify TLS configuration
   
   **A03: Injection**:
   - SQL injection patterns
   - Command injection risks
   - LDAP injection
   - XML injection
   
   **A04: Insecure Design**:
   - Missing security controls
   - Threat modeling gaps
   - Trust boundary violations
   
   **A05: Security Misconfiguration**:
   - Default credentials
   - Unnecessary features enabled
   - Error message disclosure
   - Missing security headers
   
   **A06: Vulnerable Components**:
   - Outdated dependencies
   - Known CVEs in libraries
   - Unmaintained packages
   
   **A07: Authentication Failures**:
   - Weak password policies
   - Session management issues
   - Missing MFA
   - Credential exposure
   
   **A08: Data Integrity Failures**:
   - Missing integrity checks
   - Insecure deserialization
   - Missing digital signatures
   
   **A09: Logging Failures**:
   - Insufficient logging
   - Missing audit trails
   - Log injection vulnerabilities
   
   **A10: SSRF**:
   - Server-side request forgery risks
   - URL validation issues

2. **Healthcare Compliance (NEN7510)**:
   
   **Access Control**:
   - [ ] Role-based access control implemented
   - [ ] User authentication strong
   - [ ] Session management secure
   - [ ] Audit logging present
   
   **Data Protection**:
   - [ ] Patient data encrypted at rest
   - [ ] Patient data encrypted in transit
   - [ ] Data minimization applied
   - [ ] Retention policies implemented
   
   **Audit & Logging**:
   - [ ] All access logged
   - [ ] Logs tamper-proof
   - [ ] Log retention compliant
   - [ ] Privacy logs separate
   
   **Availability**:
   - [ ] Backup procedures documented
   - [ ] Disaster recovery plan exists
   - [ ] System redundancy present

3. **ISO27001 Control Mapping**:
   
   **A.9 Access Control**:
   - User access management
   - User responsibilities
   - System access control
   
   **A.10 Cryptography**:
   - Cryptographic controls
   - Key management
   
   **A.12 Operations Security**:
   - Operational procedures
   - Protection from malware
   - Backup
   - Logging and monitoring
   
   **A.14 System Acquisition**:
   - Security in development
   - Secure development policy
   - System change control

4. **GDPR/AVG Compliance**:
   
   **Personal Data Inventory**:
   - Identify all personal data fields
   - Document data sources
   - Map data flows
   - Check data minimization
   
   **Legal Basis**:
   - Verify consent mechanisms
   - Check legitimate interest
   - Document data processing purposes
   
   **Data Subject Rights**:
   - [ ] Right to access implemented
   - [ ] Right to rectification supported
   - [ ] Right to erasure (deletion) supported
   - [ ] Right to data portability implemented
   
   **Security Measures**:
   - [ ] Pseudonymization used where applicable
   - [ ] Encryption for sensitive data
   - [ ] Access controls in place
   - [ ] Data breach notification process

5. **Vulnerability Prioritization**:
   
   **Scoring Matrix**:
```
   Priority = Severity × Impact × Exploitability
   
   Severity:
   - Critical (10): Data breach, RCE, authentication bypass
   - High (7): XSS, CSRF, sensitive data exposure
   - Medium (5): Information disclosure, DoS
   - Low (3): Configuration issues, minor bugs
   
   Impact:
   - Critical (10): Patient data, financial data
   - High (7): Business operations
   - Medium (5): User experience
   - Low (3): Cosmetic issues
   
   Exploitability:
   - Critical (10): Publicly known, easy to exploit
   - High (7): Requires some skill
   - Medium (5): Requires specific conditions
   - Low (3): Theoretical or very difficult
```

**Validation**:
- [ ] OWASP Top 10 checked
- [ ] NEN7510 compliance assessed
- [ ] ISO27001 controls mapped
- [ ] GDPR compliance verified
- [ ] Vulnerabilities prioritized

**Passes**: false  
**Notes**: []

---

### Phase 5: Prioritization & Roadmap
**Duration**: ~4 hours  
**Objective**: Create actionable remediation roadmap

**Tasks**:
```json
{
  "id": "analyze-phase5-roadmap",
  "title": "Prioritize findings and create roadmap",
  "description": "Score all findings, create priority matrix, estimate efforts, generate roadmap",
  "dependencies": ["analyze-phase3-deep", "analyze-phase4-security"],
  "estimatedTime": "4h",
  "parallelizable": false
}
```

**Activities**:

1. **Finding Consolidation**:
   - Merge duplicate findings
   - Group related issues
   - Remove false positives
   - Validate with context

2. **Priority Scoring**:
   
   **Scoring Formula**:
```
   Priority Score = (Severity × 10) + (Impact × 5) + (Effort × -2) + (Risk × 8)
   
   Where:
   - Severity: 1-10 (security/stability risk)
   - Impact: 1-10 (business/user impact)
   - Effort: 1-10 (time to fix, inverse scored)
   - Risk: 1-10 (probability of occurrence)
```
   
   **Priority Levels**:
   - **P0 - Critical**: Score > 80, fix immediately
   - **P1 - High**: Score 60-80, fix this sprint
   - **P2 - Medium**: Score 40-60, fix next quarter
   - **P3 - Low**: Score < 40, backlog

3. **Effort Estimation**:
   
   **T-Shirt Sizing**:
   - **XS** (< 2h): Quick fix, single file
   - **S** (2-8h): Simple change, few files
   - **M** (1-3 days): Module change, testing needed
   - **L** (1-2 weeks): Significant refactor
   - **XL** (> 2 weeks): Major redesign/migration
   
   **Story Points** (if using Agile):
   - 1 point = 2-4 hours
   - 2 points = 4-8 hours
   - 3 points = 1-2 days
   - 5 points = 3-5 days
   - 8 points = 1-2 weeks
   - 13 points = 2-4 weeks

4. **Roadmap Generation**:
   
   **Short-term (0-3 months)**:
   - All P0 items
   - High-impact quick wins
   - Security critical issues
   
   **Mid-term (3-6 months)**:
   - All P1 items
   - Technical debt reduction
   - Performance improvements
   
   **Long-term (6-12 months)**:
   - P2 items
   - Architectural improvements
   - Migration preparation (if applicable)
   
   **Backlog**:
   - P3 items
   - Nice-to-have improvements
   - Future enhancements

5. **Migration Assessment** (if applicable):
   
   **Migration Complexity Score**:
```
   Complexity = (LOC / 10000) + (Dependencies × 2) + (Technical Debt × 3)
   
   Scoring:
   - Low (< 50): Straightforward migration
   - Medium (50-100): Moderate challenges
   - High (100-200): Significant effort
   - Very High (> 200): Multi-phase project
```
   
   **Migration Phases**:
   - Phase 1: Critical modules (highest risk/value)
   - Phase 2: Core business logic
   - Phase 3: UI and integration
   - Phase 4: Supporting modules
   
   **Migration Estimate**:
   - Total effort in hours/weeks
   - Resource requirements
   - Timeline projection
   - Risk factors

**Validation**:
- [ ] All findings scored
- [ ] Priority matrix complete
- [ ] Efforts estimated
- [ ] Roadmap created
- [ ] Migration plan (if applicable)

**Passes**: false  
**Notes**: []

---

### Phase 6: Reporting & Deliverables
**Duration**: ~2-4 hours  
**Objective**: Generate comprehensive reports

**Tasks**:
```json
{
  "id": "analyze-phase6-reporting",
  "title": "Generate reports and deliverables",
  "description": "Create markdown report, executive summary, export formats, WBSO documentation",
  "dependencies": ["analyze-phase5-roadmap"],
  "estimatedTime": "3h",
  "parallelizable": false
}
```

**Activities**:

1. **Comprehensive Analysis Report** (Markdown):
   
   **Structure**:
```markdown
   # Code Analysis Report - [Project Name]
   
   ## Executive Summary
   - Overall health score
   - Critical findings count
   - Top 5 recommendations
   
   ## Codebase Overview
   - Technology stack
   - Size metrics
   - Complexity overview
   
   ## Code Quality
   - Maintainability score
   - Complexity metrics
   - Duplication percentage
   - Code smells
   
   ## Security Findings
   - Vulnerabilities by severity
   - OWASP Top 10 status
   - Dependency risks
   - Compliance gaps
   
   ## Technical Debt
   - Total debt (hours)
   - Debt ratio
   - Top debt areas
   - Remediation priorities
   
   ## Architecture Analysis
   - Current architecture
   - Pattern usage
   - Dependency graph
   - Architecture violations
   
   ## Compliance Status
   - NEN7510 compliance %
   - ISO27001 gaps
   - GDPR compliance
   
   ## Recommendations
   - Prioritized action items
   - Quick wins
   - Long-term improvements
   
   ## Roadmap
   - Short-term plan
   - Mid-term plan
   - Long-term plan
   
   ## Migration Assessment (if applicable)
   - Migration complexity
   - Recommended approach
   - Effort estimate
   - Risk factors
```

2. **Executive Summary** (PDF):
   - 2-3 page overview
   - Key metrics dashboard
   - Top findings
   - Recommended actions
   - Investment required

3. **Export Formats** (optional):
   
   **JSON Export**:
```json
   {
     "analysis_id": "ANALYZE-2026-01-23-001",
     "timestamp": "2026-01-23T10:00:00Z",
     "codebase": {
       "stack": "ASP Classic",
       "loc": 1380000,
       "files": 1245
     },
     "findings": [
       {
         "id": "SEC-001",
         "category": "security",
         "severity": "critical",
         "title": "SQL Injection vulnerability",
         "priority": 95,
         "effort": "M"
       }
     ],
     "metrics": { ... },
     "roadmap": { ... }
   }
```
   
   **HTML Dashboard**:
   - Interactive charts
   - Filterable findings
   - Drill-down details
   - Export to PDF
   
   **Excel Export**:
   - Findings spreadsheet
   - Metrics dashboard
   - Roadmap timeline
   - Effort estimates
   
   **GitHub Issues** (if enabled):
   - Create issue per P0/P1 finding
   - Labels: security, tech-debt, bug, etc.
   - Assignee: team lead
   - Milestone: based on roadmap

4. **WBSO Verantwoordingsrapportage**:
   
   **R&D Activities Documentation**:
```markdown
   # WBSO Verantwoordingsrapportage - Code Analysis
   
   **Project**: [Project Name]
   **Period**: [Date Range]
   **Analysis ID**: [ANALYZE-ID]
   
   ## Samenvatting
   Uitgebreide code analyse uitgevoerd op legacy codebase
   om technische schuld, security risico's en migratie
   complexiteit te bepalen.
   
   ## S&O Werkzaamheden
   
   ### Technisch Onderzoek
   - Geautomatiseerde code analyse (6 uur)
     * Static analysis tools uitgevoerd
     * Security scanners toegepast
     * Metrics verzameld en geanalyseerd
   
   - Architectuur analyse (8 uur)
     * Legacy patterns geïdentificeerd
     * Dependencies in kaart gebracht
     * Modernisatie strategieën onderzocht
   
   - Security audit (6 uur)
     * OWASP Top 10 verificatie
     * NEN7510 compliance check
     * Vulnerability prioritization
   
   ### Experimentele Ontwikkeling
   - Pattern detectie algoritmen (4 uur)
     * Custom regex patterns ontwikkeld
     * ASP Classic specifieke checks
     * Automated remediation scripts
   
   ### Nieuwe Inzichten
   - Migration complexity scoring methodologie
   - Healthcare compliance automation
   - Technical debt quantification model
   
   ## Tijdsinvestering
   **Totaal**: 24 uur
   - Fase 1 (Discovery): 2 uur
   - Fase 2 (Automated): 6 uur
   - Fase 3 (Deep Analysis): 8 uur
   - Fase 4 (Security): 6 uur
   - Fase 5 (Roadmap): 4 uur
   - Fase 6 (Reporting): 3 uur
   
   ## Innovatie Elementen
   1. Agnostische analyse framework ontwikkeld
   2. Healthcare-specifieke compliance checks
   3. Geautomatiseerde prioritering algoritme
   4. Multi-format rapportage systeem
   
   ## Technische Uitdagingen
   - Legacy ASP Classic pattern detection
   - Multi-stack analysis orchestration
   - Compliance mapping automation
   - Accurate effort estimation
   
   ## Resultaten
   - [N] kritieke bevindingen geïdentificeerd
   - [X]% technical debt reduction mogelijk
   - [Y] uur migratie geschat
   - Gedetailleerde roadmap geleverd
   
   ## Kwalificatie WBSO
   Dit project kwalificeert voor WBSO onder:
   - Technische onzekerheid (nieuwe analysemethoden)
   - Systematisch onderzoek (gestructureerde aanpak)
   - Nieuwe kennis generatie (patterns, metrics)
   - Innovatie in software ontwikkeling proces
```

5. **Follow-up PRD Generation** (if requested):
   
   **Scenario B - Migration PRD**:
   - Use MIGRATION-TEMPLATE-v2.md
   - Pre-fill with analysis findings
   - Include complexity estimates
   - Reference analysis report
   
   **Scenario C - Prioritized Backlog**:
   - Generate multiple PRDs:
     * BUG-[ID]-[DESC].md for each P0/P1 bug
     * CHANGE-[ID]-[DESC].md for improvements
   - Include effort estimates
   - Link to analysis findings
   - Set priorities

**Validation**:
- [ ] Markdown report complete
- [ ] Executive summary generated
- [ ] Requested exports created
- [ ] WBSO rapport compleet
- [ ] Follow-up PRDs generated (if applicable)

**Passes**: false  
**Notes**: []

---

## 📊 Success Metrics

### Analysis Quality
- [ ] All requested areas analyzed
- [ ] Findings actionable and specific
- [ ] Priorities justified
- [ ] Efforts realistic
- [ ] Roadmap achievable

### Deliverable Quality
- [ ] Reports comprehensive
- [ ] Executive summary clear
- [ ] Exports functional
- [ ] WBSO documentation complete
- [ ] Follow-ups ready (if applicable)

### Healthcare Compliance
- [ ] NEN7510 compliance assessed
- [ ] ISO27001 controls mapped
- [ ] GDPR compliance verified
- [ ] Audit trail documented

---

## 🔮 Future Integration Points

### TODO: External Platform Integration

**Analysis Tool Platform** (to be implemented):
```yaml
integration_points:
  input:
    - fetch_codebase_from_repo_api
    - retrieve_previous_analysis_results
    - load_custom_analysis_rules
    
  processing:
    - stream_analysis_progress_to_dashboard
    - update_metrics_in_real_time
    - trigger_custom_webhooks
    
  output:
    - store_results_in_database
    - push_findings_to_issue_tracker
    - update_project_dashboard
    - notify_stakeholders
```

**Database Schema** (placeholder):
```sql
-- To be implemented on analysis platform
CREATE TABLE analysis_runs (
  id UUID PRIMARY KEY,
  project_id UUID,
  codebase_path TEXT,
  analysis_mode TEXT,
  status TEXT,
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE TABLE findings (
  id UUID PRIMARY KEY,
  analysis_id UUID REFERENCES analysis_runs(id),
  category TEXT,
  severity TEXT,
  priority INTEGER,
  title TEXT,
  description TEXT,
  file_path TEXT,
  line_number INTEGER,
  remediation TEXT,
  effort TEXT
);

CREATE TABLE metrics (
  id UUID PRIMARY KEY,
  analysis_id UUID REFERENCES analysis_runs(id),
  metric_name TEXT,
  metric_value JSONB,
  timestamp TIMESTAMP
);
```

**API Endpoints** (to be designed):
```yaml
# POST /api/analysis/start
# GET /api/analysis/{id}/status
# GET /api/analysis/{id}/findings
# GET /api/analysis/{id}/metrics
# POST /api/analysis/{id}/export
```

---

## 📝 Notes & Observations

### Analysis Challenges
[Document any specific challenges for this codebase]

### Assumptions Made
[List assumptions during analysis]

### Limitations
[Document any limitations or areas not covered]

### Recommendations for Next Analysis
[Suggestions for future analysis runs]

---

## 🔄 MarQed.ai Workflow Integration

This analysis follows the MarQed.ai methodology:

1. **Initialization**: `prd-to-tasks.sh` converts this PRD to Claude Code tasks
2. **Execution**: `marqed-analyze.sh` runs the analysis workflow
3. **Validation**: Each phase validated before progression
4. **Persistence**: All state tracked in Claude Code tasks
5. **Reporting**: Auto-generated reports + WBSO documentation

### Task List ID
```bash
TASK_LIST_ID="ANALYZE-[YYYY-MM-DD-NNN]"
```

### Related Files
- **Workflow Script**: `workflows/marqed-analyze.sh`
- **Prompt**: `templates/prompts/prompt-analyze.md`
- **Settings**: `settings/settings-analyze.json`
- **Skills**: `skills/public/code-analysis/`, `skills/public/security-scan/`
- **Agents**: `agents/scanner-agent.md`, `agents/security-agent.md`

---

**Template Version**: 2.0  
**Last Updated**: January 23, 2026  
**Methodology**: MarQed.ai AI-Driven Code Analysis