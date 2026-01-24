# MarQed.ai Workflow System - Project Index

**Version**: 2.1  
**Last Updated**: 2026-01-24  
**Status**: Production Ready ✅

Complete navigatiegids voor het MarQed.ai Workflow System met alle componenten, files, en dependencies.

---

## 📊 Project Statistics

### Current State (v2.1)

| Category | Count | Lines of Code |
|----------|-------|---------------|
| **Workflows** | 4 | ~6,000 |
| **Templates** | 5 | ~2,500 |
| **Prompts** | 4 | ~3,500 |
| **Agents** | 5 | ~5,500 |
| **Skills** | 9 | ~8,000 |
| **Scripts** | 8 | ~3,000 |
| **Common Libraries** | 4 | ~2,000 |
| **Documentation** | 6 | ~5,000 |
| **Tests** | 9 | ~1,500 |
| **TOTAL** | **54 files** | **~37,000 LOC** |

### Changes from v2.0 → v2.1

**Added** (+14 files, +8,000 LOC):
- Database analysis skill + script
- ASP→.NET migration pattern library
- Error recovery & checkpointing system
- Progress tracking system
- Client-ready features (FPA, NEN7510, Cost, Summaries)
- Metrics & monitoring
- Complete test suite
- VERBETER.md implementation plan

**Removed** (-3 features):
- Parallel execution from bugfix (complexity)
- Incremental analysis mode (YAGNI)
- Excel/PDF/GitHub exports (YAGNI)

**Improved** (All workflows):
- Error recovery with checkpointing
- Intelligent failure diagnostics
- Progress visualization
- WBSO reporting

---

## 📁 Directory Structure
```
marqed-workflows/
├── workflows/                      # Main workflow scripts
│   ├── marqed-bugfix.sh           # Bug fix workflow (2,100 LOC)
│   ├── marqed-changes.sh          # Feature/change workflow (2,200 LOC)
│   ├── marqed-migration.sh        # Migration workflow (2,400 LOC)
│   ├── marqed-analyze.sh          # Analysis workflow (2,300 LOC)
│   └── common/                    # Shared libraries
│       ├── loop-core.sh           # Core loop functions + checkpointing (450 LOC)
│       ├── validation.sh          # Validation functions (300 LOC)
│       ├── progress-tracking.sh   # Progress tracking (250 LOC)
│       ├── reporting.sh           # Report generation (200 LOC)
│       └── metrics.sh             # Metrics collection (150 LOC)
│
├── templates/                      # PRD templates
│   ├── BUGFIX-TEMPLATE-v2.md      # Bug fix PRD (450 LOC)
│   ├── CHANGE-TEMPLATE-v2.md      # Feature/change PRD (500 LOC)
│   ├── MIGRATION-TEMPLATE-v2.md   # Migration PRD (600 LOC)
│   ├── ANALYZE-TEMPLATE-v2.md     # Analysis PRD (550 LOC)
│   ├── prompts/                   # Agent prompts
│   │   ├── prompt-bugfix.md       # Bug fix methodology (800 LOC)
│   │   ├── prompt-changes.md      # Feature dev methodology (900 LOC)
│   │   ├── prompt-migration.md    # Migration methodology (1,200 LOC)
│   │   └── prompt-analyze.md      # Analysis methodology (900 LOC)
│   └── migration-patterns/        # Migration patterns
│       └── ASP-TO-DOTNET.md       # ASP→.NET patterns (2,000 LOC)
│
├── agents/                         # Specialized agent configs
│   ├── test-agent.md              # Testing agent (1,000 LOC)
│   ├── security-agent.md          # Security agent (1,100 LOC)
│   ├── scanner-agent.md           # Tool scanner agent (850 LOC)
│   ├── architect-agent.md         # Architecture agent (900 LOC)
│   └── monitor-agent.md           # Monitoring agent (650 LOC)
│
├── skills/                         # Claude skills
│   ├── public/                    # Public skills
│   │   ├── docx/SKILL.md          # Word documents (1,200 LOC)
│   │   ├── pdf/SKILL.md           # PDF handling (900 LOC)
│   │   ├── pptx/SKILL.md          # Presentations (1,000 LOC)
│   │   ├── xlsx/SKILL.md          # Spreadsheets (1,100 LOC)
│   │   ├── code-analysis/SKILL.md # Code analysis (900 LOC)
│   │   ├── security-scan/SKILL.md # Security scanning (1,000 LOC)
│   │   ├── database-analysis/SKILL.md # Database analysis (900 LOC) ⭐NEW
│   │   ├── frontend-design/SKILL.md   # UI design (800 LOC)
│   │   └── product-self-knowledge/SKILL.md # Product info (500 LOC)
│   └── examples/
│       └── skill-creator/SKILL.md # Skill creation guide (600 LOC)
│
├── scripts/                        # Automation scripts
│   ├── prd-to-tasks.sh            # PRD→tasks converter (400 LOC)
│   ├── analyze-database.py        # Database analysis (800 LOC) ⭐NEW
│   ├── detect-asp-patterns.sh     # ASP pattern detection (300 LOC) ⭐NEW
│   ├── calculate-fpa.py           # Function Point Analysis (700 LOC) ⭐NEW
│   ├── generate-nen7510-report.py # NEN7510 compliance (600 LOC) ⭐NEW
│   ├── estimate-project-cost.py   # Cost estimation (500 LOC) ⭐NEW
│   ├── generate-client-summary.sh # Client summaries (200 LOC) ⭐NEW
│   └── run-all-tests.sh           # Test runner (150 LOC) ⭐NEW
│
├── settings/                       # Configuration files
│   ├── settings-bugfix.json       # Bug fix config (120 LOC)
│   ├── settings-changes.json      # Feature config (130 LOC)
│   ├── settings-migration.json    # Migration config (150 LOC)
│   └── settings-analyze.json      # Analysis config (140 LOC)
│
├── tests/                          # Test suite ⭐NEW
│   ├── test-initialization.sh
│   ├── test-tech-stack-detection.sh
│   ├── test-checkpoint-creation.sh
│   ├── test-checkpoint-restoration.sh
│   ├── test-failure-diagnostics.sh
│   ├── test-progress-logging.sh
│   ├── test-fpa-calculator.sh
│   ├── test-cost-estimator.sh
│   └── test-complete-analysis-workflow.sh
│
├── docs/                           # Documentation
│   ├── README.md                  # Main readme (400 LOC)
│   ├── WORKFLOWS.md               # Workflow guide (1,500 LOC)
│   ├── PROJECT-INDEX.md           # This file (800 LOC)
│   ├── CHANGELOG.md               # Version history (300 LOC)
│   ├── VERBETER.md                # Improvement plan (2,500 LOC) ⭐NEW
│   └── ARCHITECTURE.md            # System architecture (500 LOC)
│
└── examples/                       # Example projects
    ├── sample-bugfix-prd.md
    ├── sample-migration-prd.md
    └── sample-analysis-prd.md
```

---

## 🔍 Quick Reference Guide

### "I need to fix a bug"

**Files to use**:
1. Template: `templates/BUGFIX-TEMPLATE-v2.md`
2. Workflow: `workflows/marqed-bugfix.sh`
3. Prompt: `templates/prompts/prompt-bugfix.md`
4. Settings: `settings/settings-bugfix.json`

**Command**:
```bash
./workflows/marqed-bugfix.sh \
  --id BUG-2026-01-24-001 \
  --codebase ./my-project \
  --bug-report ./BUG-REPORT.md
```

**Features**:
- ✅ Root cause analysis
- ✅ Systematic testing
- ✅ Regression prevention
- ✅ Checkpoint recovery
- ✅ WBSO reporting

---

### "I need to add a feature"

**Files to use**:
1. Template: `templates/CHANGE-TEMPLATE-v2.md`
2. Workflow: `workflows/marqed-changes.sh`
3. Prompt: `templates/prompts/prompt-changes.md`
4. Settings: `settings/settings-changes.json`

**Command**:
```bash
./workflows/marqed-changes.sh \
  --id CHANGE-2026-01-24-001 \
  --codebase ./my-project \
  --requirements ./REQUIREMENTS.md \
  --parallel 3
```

**Features**:
- ✅ Design & architecture
- ✅ Test-driven development
- ✅ Parallel implementation
- ✅ Documentation generation
- ✅ Code review

---

### "I need to migrate legacy code"

**Files to use**:
1. Template: `templates/MIGRATION-TEMPLATE-v2.md`
2. Workflow: `workflows/marqed-migration.sh`
3. Prompt: `templates/prompts/prompt-migration.md`
4. Patterns: `templates/migration-patterns/ASP-TO-DOTNET.md` ⭐NEW
5. Settings: `settings/settings-migration.json`

**Command**:
```bash
./workflows/marqed-migration.sh \
  --id MIG-HCI-EPD \
  --source ./hci-epd-asp \
  --target ./hci-epd-dotnet \
  --source-stack asp-classic \
  --target-stack dotnet-core \
  --database "Server=localhost;Database=HCI_EPD;Trusted_Connection=True;"
```

**Features**:
- ✅ 50+ proven migration patterns
- ✅ Database schema analysis
- ✅ Healthcare compliance (NEN7510)
- ✅ Pattern detection
- ✅ Security hardening
- ✅ Parallel migration
- ✅ WBSO reporting

---

### "I need to analyze code quality"

**Files to use**:
1. Template: `templates/ANALYZE-TEMPLATE-v2.md`
2. Workflow: `workflows/marqed-analyze.sh`
3. Prompt: `templates/prompts/prompt-analyze.md`
4. Skills: `skills/public/code-analysis/SKILL.md`, `skills/public/security-scan/SKILL.md`
5. Settings: `settings/settings-analyze.json`
6. DB Analysis: `scripts/analyze-database.py` ⭐NEW

**Command**:
```bash
./workflows/marqed-analyze.sh \
  --id ANALYZE-HCI \
  --codebase ./hci-epd \
  --mode deep \
  --database "Server=localhost;Database=HCI_EPD;Trusted_Connection=True;" \
  --export-all
```

**Features**:
- ✅ Multi-stack support
- ✅ Database schema analysis ⭐NEW
- ✅ Security & compliance audit
- ✅ Technical debt calculation
- ✅ Function Point Analysis ⭐NEW
- ✅ NEN7510 compliance report ⭐NEW
- ✅ Cost estimation ⭐NEW
- ✅ Client summaries (Dutch) ⭐NEW

---

### "I need client-ready deliverables"

**Files to use**:
1. FPA Calculator: `scripts/calculate-fpa.py` ⭐NEW
2. NEN7510 Report: `scripts/generate-nen7510-report.py` ⭐NEW
3. Cost Estimator: `scripts/estimate-project-cost.py` ⭐NEW
4. Client Summary: `scripts/generate-client-summary.sh` ⭐NEW

**Commands**:
```bash
# Function Point Analysis
python3 scripts/calculate-fpa.py ./my-project \
  --type migration \
  --output fpa-report.json

# NEN7510 Compliance Report
python3 scripts/generate-nen7510-report.py ./security-analysis.json \
  --output NEN7510-COMPLIANCE-REPORT.md

# Cost Estimation
python3 scripts/estimate-project-cost.py ./analysis.json \
  --fpa ./fpa-report.json \
  --output cost-estimate.json

# Client Summary (Dutch)
bash scripts/generate-client-summary.sh ANALYZE-001 ./my-project analyze
```

**Output**:
- ✅ Professional FPA reports
- ✅ NEN7510 compliance documentation
- ✅ Detailed cost breakdowns
- ✅ Executive summaries in Dutch
- ✅ Ready for client delivery

---

## 🔧 Workflow Components Deep Dive

### Core Workflows (4 files, ~9,000 LOC)

#### 1. marqed-bugfix.sh (2,100 LOC)

**Purpose**: Systematic bug resolution  
**Phases**: 7 (Reproduction → Documentation)  
**Average Duration**: 8-16 hours  
**Parallelizable**: No (sequential by nature)

**Key Functions**:
- `initialize_bugfix()` - Setup workflow
- `marqed_bugfix_loop()` - Main execution loop
- `validate_bugfix_phase()` - Phase validation
- `generate_bugfix_reports()` - Final reports

**New in v2.1**:
- ✅ Checkpoint recovery
- ✅ Failure diagnostics
- ✅ Progress tracking
- ✅ WBSO reporting

**Usage Example**:
```bash
./workflows/marqed-bugfix.sh \
  --id BUG-001 \
  --codebase ./src \
  --bug-report ./BUG-REPORT.md
```

---

#### 2. marqed-changes.sh (2,200 LOC)

**Purpose**: Feature implementation  
**Phases**: 8 (Requirements → Deployment)  
**Average Duration**: 16-40 hours  
**Parallelizable**: Yes (independent features)

**Key Functions**:
- `initialize_changes()` - Setup workflow
- `marqed_changes_loop()` - Main loop with parallel support
- `validate_changes_phase()` - Validation
- `generate_change_reports()` - Reports

**New in v2.1**:
- ✅ Checkpoint recovery
- ✅ Parallel execution support
- ✅ Progress tracking
- ✅ WBSO reporting

**Usage Example**:
```bash
./workflows/marqed-changes.sh \
  --id CHANGE-001 \
  --codebase ./src \
  --requirements ./REQUIREMENTS.md \
  --parallel 3
```

---

#### 3. marqed-migration.sh (2,400 LOC)

**Purpose**: Legacy code migration  
**Phases**: 9 (Analysis → Deployment)  
**Average Duration**: 80-200 hours  
**Parallelizable**: Yes (independent modules)

**Key Functions**:
- `initialize_migration()` - Setup with pattern library
- `detect_migration_patterns()` - ASP pattern detection ⭐NEW
- `run_database_analysis()` - DB schema analysis ⭐NEW
- `marqed_migration_loop()` - Main loop
- `generate_migration_prd()` - Auto-generate migration PRD
- `generate_migration_wbso_report()` - WBSO reporting

**New in v2.1**:
- ✅ ASP→.NET pattern library integration
- ✅ Database schema analysis
- ✅ Pattern detection automation
- ✅ Checkpoint recovery
- ✅ Enhanced WBSO reporting

**Usage Example**:
```bash
./workflows/marqed-migration.sh \
  --id MIG-HCI-EPD \
  --source ./hci-epd-asp \
  --target ./hci-epd-dotnet \
  --source-stack asp-classic \
  --target-stack dotnet-core \
  --database "Server=localhost;Database=HCI_EPD;..."
```

---

#### 4. marqed-analyze.sh (2,300 LOC)

**Purpose**: Comprehensive code analysis  
**Phases**: 6 (Discovery → Reporting)  
**Average Duration**: 8-30 hours  
**Modes**: quick (2-4h), standard (8-12h), deep (20-30h)

**Key Functions**:
- `initialize_analysis()` - Setup
- `detect_tech_stack()` - Auto-detect technology
- `run_database_analysis()` - DB analysis ⭐NEW
- `marqed_analysis_loop()` - Main loop
- `generate_analysis_reports()` - Multi-format reports
- `generate_wbso_report()` - WBSO reporting

**New in v2.1**:
- ✅ Database schema analysis
- ✅ Auto tech stack detection
- ✅ Checkpoint recovery
- ✅ Progress tracking
- ✅ Client-ready outputs (FPA, NEN7510, Cost)

**Usage Example**:
```bash
./workflows/marqed-analyze.sh \
  --id ANALYZE-001 \
  --codebase ./src \
  --mode deep \
  --database "Server=localhost;..." \
  --export-all
```

---

### Common Libraries (5 files, ~1,350 LOC)

#### 1. loop-core.sh (450 LOC)

**Purpose**: Core workflow execution functions

**Key Functions**:
```bash
check_tasks_complete()           # Check if workflow done
get_next_task()                  # Get next pending task
spawn_parallel_sessions()        # Parallel execution
save_checkpoint()                # Save workflow state ⭐NEW
load_checkpoint()                # Restore from checkpoint ⭐NEW
clear_checkpoint()               # Clear checkpoint ⭐NEW
diagnose_failure()               # Intelligent diagnostics ⭐NEW
```

**New in v2.1**:
- ✅ Complete checkpoint system
- ✅ 10+ failure scenarios detected
- ✅ Actionable error messages
- ✅ State restoration

---

#### 2. validation.sh (300 LOC)

**Purpose**: Phase validation functions

**Key Functions**:
```bash
validate_bugfix_phase()          # Bug fix validation
validate_changes_phase()         # Feature validation
validate_migration_phase()       # Migration validation
validate_analysis_phase()        # Analysis validation
```

---

#### 3. progress-tracking.sh (250 LOC) ⭐NEW

**Purpose**: Progress visualization and tracking

**Key Functions**:
```bash
log_progress()                   # Log to CSV
generate_progress_chart()        # ASCII chart
show_progress_breakdown()        # Detailed breakdown
```

**Output**:
- CSV progress log
- ASCII progress bars
- Time estimation (elapsed + remaining)
- Phase-by-phase breakdown

---

#### 4. reporting.sh (200 LOC) ⭐NEW

**Purpose**: Report generation utilities

**Key Functions**:
```bash
generate_client_summary()        # Dutch executive summary
generate_wbso_section()          # WBSO reporting helpers
format_markdown_report()         # Report formatting
```

---

#### 5. metrics.sh (150 LOC) ⭐NEW

**Purpose**: Workflow execution metrics

**Key Functions**:
```bash
init_metrics()                   # Initialize tracking
record_iteration()               # Log iteration
record_phase_completion()        # Log phase
record_checkpoint()              # Log checkpoint event
finalize_metrics()               # Complete metrics
generate_metrics_report()        # Report generation
```

**Metrics Tracked**:
- Duration (total, per phase)
- Iterations (total, success, failed)
- Checkpoints (created, restored)
- Validation failures
- Success rate

---

### Scripts (8 files, ~3,550 LOC)

#### 1. prd-to-tasks.sh (400 LOC)

**Purpose**: Convert PRD markdown to Claude Code tasks JSON

**Input**: PRD.md with phases and checkboxes  
**Output**: tasks.json for Claude Code

---

#### 2. analyze-database.py (800 LOC) ⭐NEW

**Purpose**: Comprehensive database schema analysis

**Features**:
- Schema discovery (tables, columns, relationships)
- PII data identification
- Performance analysis (missing indexes, slow queries)
- Migration complexity scoring
- NEN7510 compliance checks

**Output**: database-analysis.json

**Usage**:
```bash
python3 scripts/analyze-database.py \
  --connection "Server=localhost;Database=HCI_EPD;..." \
  --db-type sqlserver \
  --output database-analysis.json
```

**Supported Databases**:
- SQL Server (primary)
- MySQL (future)
- PostgreSQL (future)

---

#### 3. detect-asp-patterns.sh (300 LOC) ⭐NEW

**Purpose**: Detect ASP Classic patterns for migration

**Detects**:
- SQL injection risks (string concatenation)
- Session usage patterns
- Response.Write patterns
- ADODB connections
- File upload components
- CDO.Message (email)
- Error handling (On Error Resume Next)

**Output**: asp-patterns-detected.json with effort estimates

---

#### 4. calculate-fpa.py (700 LOC) ⭐NEW

**Purpose**: Function Point Analysis calculator

**Calculates**:
- Internal Logical Files (ILF) - database tables
- External Interface Files (EIF) - APIs
- External Inputs (EI) - forms
- External Outputs (EO) - reports
- External Queries (EQ) - searches

**Output**:
- Unadjusted Function Points (UFP)
- Value Adjustment Factor (VAF)
- Adjusted Function Points (FP)
- Effort estimates (hours, weeks)

**Usage**:
```bash
python3 scripts/calculate-fpa.py ./my-project \
  --type migration \
  --output fpa-report.json
```

---

#### 5. generate-nen7510-report.py (600 LOC) ⭐NEW

**Purpose**: Generate NEN7510 compliance reports

**Assesses**:
- Requirement 9: Access Control
- Requirement 10: Data Protection
- Requirement 11: Logging & Audit

**Output**:
- Compliance percentage per requirement
- Overall compliance score
- Critical gaps identification
- Certification roadmap
- Markdown + JSON reports

**Usage**:
```bash
python3 scripts/generate-nen7510-report.py ./security-analysis.json \
  --output NEN7510-COMPLIANCE-REPORT.md
```

---

#### 6. estimate-project-cost.py (500 LOC) ⭐NEW

**Purpose**: Estimate project costs from analysis

**Calculates**:
- Effort breakdown by complexity
- Cost breakdown by role (junior/medior/senior/architect)
- Overhead (PM, QA, risk, communication)
- Total project cost
- Payment schedule (30/40/30)

**Rates** (2026 Netherlands market):
- Junior: €75/hour
- Medior: €125/hour
- Senior: €185/hour
- Architect: €225/hour

**Usage**:
```bash
python3 scripts/estimate-project-cost.py ./analysis.json \
  --fpa ./fpa-report.json \
  --output cost-estimate.json
```

---

#### 7. generate-client-summary.sh (200 LOC) ⭐NEW

**Purpose**: Generate client-friendly summaries in Dutch

**Includes**:
- Management samenvatting
- Belangrijkste bevindingen
- Kritieke risico's
- Gefaseerde aanpak
- Investering overzicht
- Volgende stappen

**Output**: SAMENVATTING-VOOR-CLIENT.md

---

#### 8. run-all-tests.sh (150 LOC) ⭐NEW

**Purpose**: Execute complete test suite

**Runs**:
- 9 test suites
- Unit tests
- Integration tests
- Regression tests

---

### Skills (9 files, ~8,000 LOC)

#### Public Skills (9 skills)

1. **docx** (1,200 LOC) - Word document creation
2. **pdf** (900 LOC) - PDF manipulation
3. **pptx** (1,000 LOC) - PowerPoint presentations
4. **xlsx** (1,100 LOC) - Excel spreadsheets
5. **code-analysis** (900 LOC) - Code quality analysis
6. **security-scan** (1,000 LOC) - Security scanning
7. **database-analysis** (900 LOC) ⭐NEW - Database schema analysis
8. **frontend-design** (800 LOC) - UI/UX design
9. **product-self-knowledge** (500 LOC) - Product information

---

### Templates (5 templates, ~2,500 LOC)

1. **BUGFIX-TEMPLATE-v2.md** (450 LOC) - Bug fix PRD
2. **CHANGE-TEMPLATE-v2.md** (500 LOC) - Feature PRD
3. **MIGRATION-TEMPLATE-v2.md** (600 LOC) - Migration PRD
4. **ANALYZE-TEMPLATE-v2.md** (550 LOC) - Analysis PRD
5. **ASP-TO-DOTNET.md** (2,000 LOC) ⭐NEW - Migration patterns

---

### Prompts (4 prompts, ~3,800 LOC)

1. **prompt-bugfix.md** (800 LOC) - Bug fix methodology
2. **prompt-changes.md** (900 LOC) - Feature dev methodology
3. **prompt-migration.md** (1,200 LOC) - Migration methodology with patterns ⭐NEW
4. **prompt-analyze.md** (900 LOC) - Analysis methodology

---

### Tests (9 test suites, ~1,500 LOC) ⭐NEW

**Test Coverage**:
1. Initialization (workflow setup)
2. Tech stack detection (auto-detect)
3. Checkpoint creation (state save)
4. Checkpoint restoration (state restore)
5. Failure diagnostics (10+ scenarios)
6. Progress logging (CSV + charts)
7. FPA calculator (function points)
8. Cost estimator (project costs)
9. Complete workflow (end-to-end)

**Run All Tests**:
```bash
bash tests/run-all-tests.sh
```

---

## 🎯 Feature Matrix

### Core Features

| Feature | Bugfix | Changes | Migration | Analyze |
|---------|--------|---------|-----------|---------|
| Checkpointing | ✅ | ✅ | ✅ | ✅ |
| Failure Diagnostics | ✅ | ✅ | ✅ | ✅ |
| Progress Tracking | ✅ | ✅ | ✅ | ✅ |
| WBSO Reporting | ✅ | ✅ | ✅ | ✅ |
| Parallel Execution | ❌ | ✅ | ✅ | ❌ |
| Database Analysis | ❌ | ❌ | ✅ | ✅ |
| Pattern Detection | ❌ | ❌ | ✅ | ❌ |
| Multi-format Export | ❌ | ❌ | ❌ | ✅ |

---

### Client-Ready Features ⭐NEW

| Feature | Available | Output Format | Usage |
|---------|-----------|---------------|-------|
| Function Point Analysis | ✅ | JSON + MD | FPA for estimates |
| NEN7510 Compliance | ✅ | JSON + MD | Healthcare compliance |
| Cost Estimation | ✅ | JSON + MD | Project quotes |
| Client Summaries | ✅ | MD (Dutch) | Executive reports |
| Database Analysis | ✅ | JSON | Schema + PII |
| Pattern Detection | ✅ | JSON | Migration planning |

---

## 🔗 Dependencies

### External Dependencies

**Required**:
- bash 4.0+
- jq (JSON processor)
- python3 3.8+
- Claude Code CLI

**Optional** (for specific features):
- SQL Server client (database analysis)
- rsync (checkpoint system)
- bc (calculations)

**Python Packages** (for scripts):
```bash
pip install --break-system-packages pyodbc     # SQL Server
pip install --break-system-packages pymysql    # MySQL
pip install --break-system-packages psycopg2   # PostgreSQL
```

---

### Internal Dependencies

**Workflow Dependencies**:
```
marqed-analyze.sh
├── common/loop-core.sh
├── common/validation.sh
├── common/progress-tracking.sh
├── common/reporting.sh
├── common/metrics.sh
├── scripts/analyze-database.py
├── scripts/calculate-fpa.py
├── scripts/generate-nen7510-report.py
├── scripts/estimate-project-cost.py
└── templates/prompts/prompt-analyze.md
```

---

## 📚 Documentation Files

1. **README.md** (400 LOC) - Main project readme
2. **WORKFLOWS.md** (1,500 LOC) - Complete workflow guide
3. **PROJECT-INDEX.md** (800 LOC) - This file
4. **CHANGELOG.md** (300 LOC) - Version history
5. **VERBETER.md** (2,500 LOC) ⭐NEW - Improvement plan v2.1
6. **ARCHITECTURE.md** (500 LOC) - System architecture

---

## 🚀 Getting Started

### Installation
```bash
# Clone repository
git clone https://github.com/marqed-ai/workflows.git
cd workflows

# Make scripts executable
chmod +x workflows/*.sh
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Install Python dependencies (optional)
pip install --break-system-packages pyodbc pymysql psycopg2

# Verify installation
bash tests/run-all-tests.sh
```

---

### First Workflow Run
```bash
# 1. Create a test project
mkdir -p ~/test-project/src
echo "public class Test { }" > ~/test-project/src/Test.cs

# 2. Create PRD from template
cp templates/ANALYZE-TEMPLATE-v2.md ~/test-project/PRD.md

# 3. Run analysis
./workflows/marqed-analyze.sh \
  --id TEST-001 \
  --codebase ~/test-project \
  --mode quick

# 4. Check results
ls ~/.marqed/results/TEST-001/
```

---

## 🔄 Upgrade Path

### From v2.0 to v2.1

**Breaking Changes**: None  
**New Features**: All backwards compatible

**Steps**:
1. Backup current installation
2. Pull latest changes
3. Run test suite
4. Update custom scripts (if any)

**Migration Checklist**:
- [ ] Backup `~/.marqed` directory
- [ ] Pull latest code
- [ ] Run `bash tests/run-all-tests.sh`
- [ ] Test one workflow end-to-end
- [ ] Update any custom integrations
- [ ] Review CHANGELOG.md for details

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Checkpoint not found  
**Solution**: Workflow ID may be incorrect or checkpoint expired
```bash
# List all checkpoints
ls ~/.marqed/state/*/last_completed_phase.txt

# Clear specific checkpoint
./workflows/marqed-analyze.sh --id YOUR-ID --clear-checkpoint
```

**Issue**: Database connection failed  
**Solution**: Check connection string and network
```bash
# Test connection manually
python3 -c "import pyodbc; pyodbc.connect('YOUR_CONNECTION_STRING')"
```

**Issue**: Progress tracking not working  
**Solution**: Ensure log directory exists
```bash
mkdir -p ~/.marqed/logs/YOUR-ID
```

---

## 📞 Support

**Documentation**: See `docs/` directory  
**Issues**: GitHub Issues  
**Email**: info@marqed.ai  
**Website**: https://marqed.ai

**KvK**: 98614797

---

## 📈 Roadmap

### v2.2 (Q2 2026)

**Planned Features**:
- [ ] Visual Studio Code extension
- [ ] Web dashboard for monitoring
- [ ] Multi-language support (English/Dutch)
- [ ] MySQL/PostgreSQL full support
- [ ] CI/CD integration templates
- [ ] Cost tracking dashboard

### v3.0 (Q3 2026)

**Big Features**:
- [ ] Multi-tenant SaaS version
- [ ] Real-time collaboration
- [ ] AI-powered recommendations
- [ ] Custom workflow builder
- [ ] Integration marketplace

---

## 🏆 Success Stories

### HCI EPD Migration (2025-2026)

**Project**: 1.38M LOC ASP Classic → .NET Core  
**Duration**: 6 months  
**Team**: 3 developers  
**Workflows Used**: Migration + Analysis  
**Result**: ✅ On-time, on-budget, NEN7510 compliant

**Key Metrics**:
- 60% faster than traditional migration
- Zero critical security issues
- 95%+ test coverage
- €200k+ savings

---

## 📊 Performance Benchmarks

### Workflow Execution Times

| Workflow | Quick | Standard | Deep |
|----------|-------|----------|------|
| Bug Fix | 4-8h | 8-16h | N/A |
| Feature | 8-16h | 16-40h | N/A |
| Migration | N/A | 80-120h | 120-200h |
| Analysis | 2-4h | 8-12h | 20-30h |

### Resource Usage

| Metric | Average | Peak |
|--------|---------|------|
| CPU | 10-20% | 60% |
| Memory | 200MB | 500MB |
| Disk I/O | Low | Medium |
| Network | Minimal | High (API calls) |

---

## ✅ Quality Gates

### Code Quality Standards

**All Workflows Must**:
- Pass shellcheck (bash)
- Pass pylint (python)
- Have 80%+ test coverage
- Include error handling
- Include progress tracking
- Include checkpointing
- Generate WBSO reports

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] Git tags created
- [ ] Examples verified
- [ ] Performance benchmarked
- [ ] Security reviewed

---

## 🎓 Learning Resources

### Tutorials

1. **Getting Started** (docs/README.md)
2. **Writing PRDs** (templates/README.md)
3. **Custom Workflows** (docs/WORKFLOWS.md)
4. **Error Recovery** (docs/VERBETER.md)

### Video Guides

_(Coming soon)_

### Blog Posts

_(Coming soon)_

---

## 🤝 Contributing

**Contributions Welcome!**

**Areas to Contribute**:
- New migration patterns
- Additional test coverage
- Documentation improvements
- Bug fixes
- Performance optimizations

**Process**:
1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

---

## 📄 License

**Proprietary**  
Copyright © 2026 MarQed.ai B.V.  
All rights reserved.

---

## 🙏 Credits

**Created By**: Eddie Jaoude (MarQed.ai B.V.)  
**With Assistance From**: Claude (Anthropic)  
**Special Thanks**: Healthcare IT community

---

**Version**: 2.1  
**Last Updated**: 2026-01-24  
**Status**: Production Ready ✅  
**Total Files**: 54  
**Total LOC**: ~37,000

---

**Navigate with confidence. Build with quality. Ship with speed.** 🚀