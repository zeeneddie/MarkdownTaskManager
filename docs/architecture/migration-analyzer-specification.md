# MigrationAnalyzer - Multi-Agent System Specification

**Document**: MigrationAnalyzer Complete Specification
**Version**: 2.0
**Created**: 2025-12-09
**Updated**: 2025-12-09 - Multi-Agent Architecture + Database Analysis + Tool Integration
**Status**: APPROVED - Ready for Implementation
**Target**: Week 65-70

---

## Executive Summary

De MigrationAnalyzer is een **multi-agent systeem** dat legacy codebases én databases automatisch analyseert en gestructureerde input genereert voor het BROWN_PAPER workflow. Het systeem integreert bewezen open-source tools en gebruikt gespecialiseerde agents die alleen worden geactiveerd wanneer relevant.

### Design Principles

1. **Minimale Context per Agent** - Elke agent krijgt alleen relevante data
2. **Conditional Activation** - Stack analyzers alleen indien gedetecteerd
3. **Tool Reuse** - Bewezen open-source tools waar mogelijk
4. **Cost Efficient** - ~65% minder tokens dan single mega-agent
5. **Database-Aware** - Volledige DB schema en versie analyse

### Business Case

| Metric | Handmatig (Nu) | Met MigrationAnalyzer |
|--------|----------------|----------------------|
| Code analyse tijd | 3-5 dagen | 2-4 uur |
| Database analyse | 1-2 dagen | 30 min |
| Documentatie output | Handmatig schrijven | Auto-generated |
| FP Schatting | Expert guess | Data-driven + tools |
| Consistentie | Varieert per analist | Gestandaardiseerd |

---

## Multi-Agent Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MIGRATION ANALYZER - MULTI-AGENT SYSTEM                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ORCHESTRATOR: Miguel (Migration)                  │   │
│  │                                                                      │   │
│  │  Context: ~5KB (file inventory only)                                │   │
│  │  • Detecteert source stack(s)                                       │   │
│  │  • Activeert relevante specialist agents                            │   │
│  │  • Aggregeert resultaten                                            │   │
│  │  • Genereert BROWN_PAPER input (Q1-Q4)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│         ┌────────────────────┼────────────────────┐                         │
│         ▼                    ▼                    ▼                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │ STACK ANALYZERS │ │ DATABASE        │ │ CROSS-CUTTING   │               │
│  │ (Conditional)   │ │ ANALYZER (New)  │ │ (Always Active) │               │
│  │                 │ │                 │ │                 │               │
│  │ • DotNetAnalyze │ │ • Schema scan   │ │ • Quinn (Sec)   │               │
│  │ • FrontendAnaly │ │ • Version check │ │ • Eliza (FP)    │               │
│  │ • PHPAnalyzer   │ │ • Migration est │ │ • Felix (Arch)  │               │
│  │ • JavaAnalyzer  │ │ • Compatibility │ │                 │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      OUTPUT AGENTS (Final Phase)                     │   │
│  │                                                                      │   │
│  │  Diana (Documentation)              Peter (Business Context)         │   │
│  │  • Analysis reports                 • Problem statement              │   │
│  │  • Module inventory                 • Success criteria               │   │
│  │  • Risk register                    • Stakeholder map                │   │
│  │  • Pattern report                   • BROWN_PAPER Q5-Q7              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Specifications

#### 1. Miguel (Orchestrator) - Minimale Context

| Aspect | Details |
|--------|---------|
| **Rol** | Migration workflow orchestrator |
| **Context** | ~5KB - Alleen repo path + file inventory |
| **Skills** | `migration_orchestration`, `stack_detection` |
| **Tools** | FileScanner, Agent coordinator |
| **Output** | Aggregated analysis, BROWN_PAPER Q1-4 |
| **LLM** | Ollama qwen2.5-coder:7b (local) |

**Miguel krijgt NIET**: Volledige code, AST details, Security details

#### 2. Stack Analyzer Agents (Conditional)

##### DotNetAnalyzer

| Aspect | Details |
|--------|---------|
| **Activatie** | `IF detected_stack IN [aspnet_webforms, asp_classic, aspnet_mvc, wcf, asmx]` |
| **Context** | ~50KB - Alleen .NET gerelateerde files |
| **Skills** | `dotnet_analysis`, `webforms_patterns`, `asp_classic_patterns` |
| **Tools** | Roslyn, .NET Upgrade Assistant, Lizard, WebFormsParser, ASPClassicParser |
| **Output** | .NET patterns, modules, complexity, upgrade compatibility |
| **LLM** | Ollama qwen2.5-coder:7b |

##### FrontendAnalyzer

| Aspect | Details |
|--------|---------|
| **Activatie** | `IF detected_stack IN [angularjs, angular, vue, react, jquery]` |
| **Context** | ~30KB - Alleen frontend files |
| **Skills** | `frontend_analysis`, `angularjs_patterns`, `vue_patterns`, `react_patterns` |
| **Tools** | tree-sitter, Lizard, Legacy2Modern concepts |
| **Output** | Frontend patterns, components, migration paths |
| **LLM** | Ollama qwen2.5-coder:7b |

##### PHPAnalyzer

| Aspect | Details |
|--------|---------|
| **Activatie** | `IF detected_stack IN [php, laravel, symfony, wordpress]` |
| **Context** | ~40KB - Alleen PHP files |
| **Skills** | `php_analysis`, `php_legacy_patterns` |
| **Tools** | tree-sitter-php, Lizard |
| **Output** | PHP patterns, framework detection, security issues |
| **LLM** | Ollama qwen2.5-coder:7b |

##### JavaAnalyzer

| Aspect | Details |
|--------|---------|
| **Activatie** | `IF detected_stack IN [java, spring, struts, ejb]` |
| **Context** | ~40KB - Alleen Java files |
| **Skills** | `java_analysis`, `spring_patterns`, `ejb_patterns` |
| **Tools** | tree-sitter-java, Lizard |
| **Output** | Java patterns, framework detection, migration paths |
| **LLM** | Ollama qwen2.5-coder:7b |

#### 3. DatabaseAnalyzer (NEW)

| Aspect | Details |
|--------|---------|
| **Activatie** | `IF repo contains [*.sql, *.mdf, schema files, connection strings, stored procedures]` |
| **Context** | ~30KB - Schema files + connection info |
| **Skills** | `database_analysis`, `schema_extraction`, `migration_assessment` |
| **Tools** | Ora2Pg, SQLines, pgLoader, Google DMA concepts |
| **Output** | Schema inventory, SP complexity, migration difficulty (A-E), compatibility issues |
| **LLM** | Ollama deepseek-r1:latest |

#### 4. Cross-Cutting Agents (Always Active)

##### Quinn (Security)

| Aspect | Details |
|--------|---------|
| **Context** | ~10KB - Pattern matches + suspicious code snippets |
| **Skills** | `migration_security_scan` |
| **Input** | Gefilterde patterns van Stack Analyzers + DB credentials |
| **Output** | Security risks, SQL injection, XSS, critical vulnerabilities |
| **LLM** | Ollama deepseek-r1:latest |

##### Eliza (Estimation)

| Aspect | Details |
|--------|---------|
| **Context** | ~20KB - Module inventory + complexity metrics |
| **Skills** | `migration_fp_estimation` |
| **Input** | Metrics van alle analyzers + Ora2Pg cost assessment |
| **Output** | FP per module, total FP, sprint estimate, confidence |
| **LLM** | Ollama deepseek-r1:latest |

##### Felix (Architecture)

| Aspect | Details |
|--------|---------|
| **Context** | ~15KB - Module list + references |
| **Skills** | `migration_dependency_analysis` |
| **Input** | Symbol references van Serena + DB foreign keys |
| **Output** | Dependency graph, migration order, coupling metrics |
| **LLM** | Ollama qwen2.5-coder:7b |

#### 5. Output Agents (Final Phase)

##### Diana (Documentation)

| Aspect | Details |
|--------|---------|
| **Context** | ~30KB - Aggregated results |
| **Skills** | `migration_documentation` |
| **Output** | 8 markdown documents |
| **LLM** | Ollama mistral:latest |

##### Peter (Business Context)

| Aspect | Details |
|--------|---------|
| **Context** | ~10KB - Summary only |
| **Skills** | `migration_business_context` |
| **Output** | Problem statement, success criteria, stakeholders (BROWN_PAPER Q5-7) |
| **LLM** | Ollama deepseek-r1:latest |

### Context Efficiency Analysis

| Agent | Context Size | When Active | Token Savings |
|-------|--------------|-------------|---------------|
| Miguel | ~5KB | Always | Baseline |
| DotNetAnalyzer | ~50KB | If .NET detected | vs 500KB full |
| FrontendAnalyzer | ~30KB | If frontend detected | vs 500KB full |
| DatabaseAnalyzer | ~30KB | If DB detected | vs 500KB full |
| Quinn | ~10KB | Always | vs 500KB full |
| Eliza | ~20KB | Always | vs 500KB full |
| Felix | ~15KB | Always | vs 500KB full |
| Diana | ~30KB | Final phase | vs 500KB full |
| Peter | ~10KB | Final phase | vs 500KB full |

**Totaal multi-agent: ~200KB max (gedistribueerd)**
**Single mega-agent: ~500KB+ (alles tegelijk)**
**Besparing: ~60-65% tokens**

---

## Workflow Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW SEQUENCE                                    │
│                                                                              │
│  FASE 1: DETECTION (Miguel only) ─────────────────────────────────────────  │
│  ├── Input: repo_path                                                       │
│  ├── Action: FileScanner.scan() + DBScanner.detect()                       │
│  ├── Output: file_inventory, detected_stacks, db_detected                  │
│  └── Decision: Which Stack Analyzers + DatabaseAnalyzer to activate        │
│                                                                              │
│  FASE 2: STACK ANALYSIS (Parallel, conditional) ──────────────────────────  │
│  ├── IF dotnet: DotNetAnalyzer.analyze(dotnet_files)                       │
│  ├── IF frontend: FrontendAnalyzer.analyze(frontend_files)                 │
│  ├── IF php: PHPAnalyzer.analyze(php_files)                                │
│  ├── IF java: JavaAnalyzer.analyze(java_files)                             │
│  └── IF database: DatabaseAnalyzer.analyze(db_files, connection_strings)   │
│                                                                              │
│  FASE 3: CROSS-CUTTING (Parallel, always) ────────────────────────────────  │
│  ├── Quinn.security_scan(patterns_from_phase2, db_credentials)             │
│  ├── Felix.dependency_analysis(modules_from_phase2, db_foreign_keys)       │
│  └── Eliza.fp_estimation(modules + complexity + patterns + db_assessment)  │
│                                                                              │
│  FASE 4: OUTPUT (Sequential) ─────────────────────────────────────────────  │
│  ├── Miguel.aggregate_results()                                            │
│  ├── Diana.generate_documentation(aggregated)                              │
│  ├── Peter.generate_business_context(aggregated)                           │
│  └── Miguel.generate_brown_paper_input()                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Open Source Tool Integration

### Tool Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPEN SOURCE TOOL INTEGRATION                              │
│                                                                              │
│  CODE ANALYSIS TOOLS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Lizard (pip install lizard)              Genese Complexity         │   │
│  │  ├── Cyclomatic complexity                ├── Cognitive complexity  │   │
│  │  ├── LOC, NLOC, CCN                       ├── HTML reports          │   │
│  │  ├── 15+ languages                        └── Heatmaps              │   │
│  │  └── Function-level metrics                                         │   │
│  │                                                                      │   │
│  │  tree-sitter (multi-language AST)         Serena MCP                │   │
│  │  ├── tree-sitter-javascript               ├── Symbol extraction     │   │
│  │  ├── tree-sitter-typescript               ├── Reference finding     │   │
│  │  ├── tree-sitter-php                      └── Cross-file analysis   │   │
│  │  ├── tree-sitter-java                                               │   │
│  │  ├── tree-sitter-vue                                                │   │
│  │  └── tree-sitter-go                                                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  .NET SPECIFIC TOOLS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  .NET Upgrade Assistant (Microsoft)       Roslyn (C#/VB.NET AST)    │   │
│  │  ├── API compatibility analysis           ├── Full semantic model   │   │
│  │  ├── NuGet package updates                ├── Code-behind parsing   │   │
│  │  ├── Dependency analysis                  └── Symbol resolution     │   │
│  │  └── JSON output for integration                                    │   │
│  │                                                                      │   │
│  │  DotVVM (Alternative target)              BlazorWebFormsComponents  │   │
│  │  ├── Incremental migration                ├── WebForms → Blazor     │   │
│  │  └── ASPX → DotVVM pages                  └── Component mapping     │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  DATABASE TOOLS                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Ora2Pg (Oracle → PostgreSQL)             SQLines (Multi-DB)        │   │
│  │  ├── Schema conversion                    ├── DDL conversion        │   │
│  │  ├── PL/SQL → PL/pgSQL                    ├── DML conversion        │   │
│  │  ├── Migration cost assessment            ├── Stored procedures     │   │
│  │  ├── Difficulty rating (A-E)              └── Cross-DB support      │   │
│  │  └── Man-days estimation                                            │   │
│  │                                                                      │   │
│  │  pgLoader (Data migration)                Google DMA Concepts       │   │
│  │  ├── Parallel data loading                ├── Effort estimation     │   │
│  │  ├── Schema conversion                    ├── ROI calculation       │   │
│  │  └── MySQL/SQLite/MSSQL → PG              └── Risk assessment       │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tool Integration Code

#### Lizard Integration (`app/services/tools/lizard_wrapper.py`)

```python
import lizard
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ComplexityMetrics:
    cyclomatic: float
    cognitive: float  # From Genese if available
    loc: int
    nloc: int  # Non-comment lines
    function_count: int
    avg_complexity: float
    max_complexity: float
    high_complexity_functions: List[str]

class LizardWrapper:
    """
    Wrapper around Lizard complexity analyzer.
    Supports: C#, Java, JavaScript, Python, PHP, Go, Ruby, TypeScript
    """

    COMPLEXITY_THRESHOLDS = {
        "low": 10,
        "medium": 20,
        "high": 50,
    }

    def analyze_file(self, file_path: str) -> ComplexityMetrics:
        """Analyze single file complexity."""
        analysis = lizard.analyze_file(file_path)

        high_complexity = [
            f.name for f in analysis.function_list
            if f.cyclomatic_complexity > self.COMPLEXITY_THRESHOLDS["medium"]
        ]

        return ComplexityMetrics(
            cyclomatic=sum(f.cyclomatic_complexity for f in analysis.function_list),
            cognitive=0,  # Will be filled by Genese if available
            loc=analysis.nloc,
            nloc=analysis.nloc,
            function_count=len(analysis.function_list),
            avg_complexity=analysis.average_cyclomatic_complexity,
            max_complexity=max((f.cyclomatic_complexity for f in analysis.function_list), default=0),
            high_complexity_functions=high_complexity,
        )

    def analyze_directory(self, dir_path: str, extensions: List[str] = None) -> dict:
        """Analyze all files in directory."""
        results = {}
        for analysis in lizard.analyze(
            [dir_path],
            exts=extensions or lizard.get_extensions([])
        ):
            results[analysis.filename] = self.analyze_file(analysis.filename)
        return results

    def get_migration_difficulty(self, metrics: ComplexityMetrics) -> str:
        """Map complexity to migration difficulty."""
        if metrics.avg_complexity < 10 and metrics.max_complexity < 20:
            return "easy"
        elif metrics.avg_complexity < 20 and metrics.max_complexity < 50:
            return "medium"
        elif metrics.avg_complexity < 30:
            return "hard"
        return "complex"
```

#### .NET Upgrade Assistant Integration (`app/services/tools/dotnet_upgrade_wrapper.py`)

```python
import subprocess
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class UpgradeAssessment:
    project_path: str
    current_framework: str
    target_framework: str
    compatibility_score: float  # 0-100
    blocking_issues: List[str]
    warnings: List[str]
    nuget_updates: List[Dict]
    api_changes: List[Dict]
    estimated_effort: str  # low, medium, high

class DotNetUpgradeWrapper:
    """
    Wrapper around .NET Upgrade Assistant for migration assessment.
    """

    def __init__(self):
        self._ensure_tool_installed()

    def _ensure_tool_installed(self):
        """Ensure upgrade-assistant is installed."""
        try:
            subprocess.run(
                ["upgrade-assistant", "--version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            subprocess.run(
                ["dotnet", "tool", "install", "-g", "upgrade-assistant"],
                check=True
            )

    def analyze_project(self, project_path: str, target: str = "net8.0") -> UpgradeAssessment:
        """
        Run upgrade-assistant analyze on a project.

        Args:
            project_path: Path to .csproj or .sln
            target: Target framework (net8.0, net9.0)
        """
        result = subprocess.run(
            [
                "upgrade-assistant", "analyze",
                project_path,
                "--target-tfm-support", target,
                "--format", "json"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Upgrade assistant failed: {result.stderr}")

        analysis = json.loads(result.stdout)

        return UpgradeAssessment(
            project_path=project_path,
            current_framework=analysis.get("currentTfm", "unknown"),
            target_framework=target,
            compatibility_score=self._calculate_compatibility(analysis),
            blocking_issues=analysis.get("blockingIssues", []),
            warnings=analysis.get("warnings", []),
            nuget_updates=analysis.get("packageUpdates", []),
            api_changes=analysis.get("apiChanges", []),
            estimated_effort=self._estimate_effort(analysis),
        )

    def _calculate_compatibility(self, analysis: dict) -> float:
        """Calculate compatibility score 0-100."""
        blocking = len(analysis.get("blockingIssues", []))
        warnings = len(analysis.get("warnings", []))

        if blocking > 0:
            return max(0, 50 - (blocking * 10))
        return max(0, 100 - (warnings * 5))

    def _estimate_effort(self, analysis: dict) -> str:
        """Estimate migration effort."""
        blocking = len(analysis.get("blockingIssues", []))
        api_changes = len(analysis.get("apiChanges", []))

        if blocking > 5 or api_changes > 50:
            return "high"
        elif blocking > 0 or api_changes > 20:
            return "medium"
        return "low"
```

#### Database Tools Integration (`app/services/tools/database_tools.py`)

```python
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class MigrationDifficulty(Enum):
    A = "Trivial"      # Automatic conversion
    B = "Easy"         # Minor manual adjustments
    C = "Medium"       # Significant manual work
    D = "Hard"         # Major rewrite needed
    E = "Very Hard"    # Complete redesign

@dataclass
class DatabaseAssessment:
    source_db: str  # oracle, sqlserver, mysql
    source_version: str
    target_db: str  # postgresql, mysql, sqlserver
    target_version: str

    # Schema metrics
    table_count: int
    view_count: int
    stored_procedure_count: int
    function_count: int
    trigger_count: int
    index_count: int

    # Assessment
    difficulty: MigrationDifficulty
    estimated_man_days: float
    compatibility_issues: List[Dict]
    auto_convertible_percent: float

    # Recommendations
    recommendations: List[str]
    blocking_features: List[str]

class Ora2PgWrapper:
    """
    Wrapper around Ora2Pg for Oracle → PostgreSQL migration assessment.

    Ora2Pg provides:
    - Schema extraction and conversion
    - PL/SQL → PL/pgSQL conversion
    - Migration cost assessment with difficulty rating
    """

    def __init__(self, ora2pg_path: str = "ora2pg"):
        self.ora2pg_path = ora2pg_path

    def assess_migration(
        self,
        oracle_dsn: str,
        oracle_user: str,
        oracle_password: str
    ) -> DatabaseAssessment:
        """
        Run Ora2Pg migration assessment.

        Returns difficulty rating A-E and man-days estimate.
        """
        # Run ora2pg in assessment mode
        result = subprocess.run(
            [
                self.ora2pg_path,
                "--type", "SHOW_REPORT",
                "--source", oracle_dsn,
                "--user", oracle_user,
                "--password", oracle_password,
            ],
            capture_output=True,
            text=True
        )

        return self._parse_report(result.stdout)

    def assess_from_dump(self, dump_file: str) -> DatabaseAssessment:
        """
        Assess migration from SQL dump file (no live connection needed).
        """
        result = subprocess.run(
            [
                self.ora2pg_path,
                "--type", "SHOW_REPORT",
                "--input_file", dump_file,
            ],
            capture_output=True,
            text=True
        )

        return self._parse_report(result.stdout)

    def _parse_report(self, report: str) -> DatabaseAssessment:
        """Parse Ora2Pg report output."""
        # Extract metrics from report
        difficulty_match = re.search(r"Migration level\s*:\s*([A-E])", report)
        man_days_match = re.search(r"Estimated cost\s*:\s*([\d.]+)", report)

        # Parse object counts
        tables = int(re.search(r"Tables\s*:\s*(\d+)", report).group(1) or 0)
        views = int(re.search(r"Views\s*:\s*(\d+)", report).group(1) or 0)
        procedures = int(re.search(r"Procedures\s*:\s*(\d+)", report).group(1) or 0)
        functions = int(re.search(r"Functions\s*:\s*(\d+)", report).group(1) or 0)
        triggers = int(re.search(r"Triggers\s*:\s*(\d+)", report).group(1) or 0)

        difficulty = MigrationDifficulty[difficulty_match.group(1)] if difficulty_match else MigrationDifficulty.C
        man_days = float(man_days_match.group(1)) if man_days_match else 0

        return DatabaseAssessment(
            source_db="oracle",
            source_version="",  # Extracted from report
            target_db="postgresql",
            target_version="16",
            table_count=tables,
            view_count=views,
            stored_procedure_count=procedures,
            function_count=functions,
            trigger_count=triggers,
            index_count=0,
            difficulty=difficulty,
            estimated_man_days=man_days,
            compatibility_issues=self._extract_issues(report),
            auto_convertible_percent=self._calculate_auto_convert(report),
            recommendations=self._extract_recommendations(report),
            blocking_features=self._extract_blocking(report),
        )

    def _extract_issues(self, report: str) -> List[Dict]:
        """Extract compatibility issues from report."""
        issues = []
        # Parse issue sections
        return issues

    def _calculate_auto_convert(self, report: str) -> float:
        """Calculate percentage that can be auto-converted."""
        # Based on difficulty rating
        auto_convert_map = {
            "A": 95.0,
            "B": 80.0,
            "C": 60.0,
            "D": 40.0,
            "E": 20.0,
        }
        match = re.search(r"Migration level\s*:\s*([A-E])", report)
        if match:
            return auto_convert_map.get(match.group(1), 50.0)
        return 50.0

    def _extract_recommendations(self, report: str) -> List[str]:
        """Extract recommendations from report."""
        return []

    def _extract_blocking(self, report: str) -> List[str]:
        """Extract blocking features that need manual work."""
        return []


class SQLinesWrapper:
    """
    Wrapper around SQLines for multi-database conversion.

    Supports: SQL Server, Oracle, MySQL, PostgreSQL, IBM DB2, Sybase
    """

    def convert_schema(
        self,
        source_file: str,
        source_db: str,
        target_db: str,
        output_file: str
    ) -> Dict:
        """
        Convert SQL schema from source to target database.
        """
        result = subprocess.run(
            [
                "sqlines",
                "-s", source_db,
                "-t", target_db,
                "-in", source_file,
                "-out", output_file,
            ],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "output_file": output_file,
            "warnings": self._parse_warnings(result.stdout),
            "errors": self._parse_errors(result.stderr),
        }

    def _parse_warnings(self, output: str) -> List[str]:
        return [line for line in output.split("\n") if "warning" in line.lower()]

    def _parse_errors(self, output: str) -> List[str]:
        return [line for line in output.split("\n") if "error" in line.lower()]


class DatabaseVersionDetector:
    """
    Detects database version from connection strings, config files, and scripts.
    """

    VERSION_PATTERNS = {
        "sql_server": {
            "2008": r"SQL Server 2008|MSSQL10|Version 10\.",
            "2012": r"SQL Server 2012|MSSQL11|Version 11\.",
            "2014": r"SQL Server 2014|MSSQL12|Version 12\.",
            "2016": r"SQL Server 2016|MSSQL13|Version 13\.",
            "2017": r"SQL Server 2017|MSSQL14|Version 14\.",
            "2019": r"SQL Server 2019|MSSQL15|Version 15\.",
            "2022": r"SQL Server 2022|MSSQL16|Version 16\.",
        },
        "oracle": {
            "10g": r"Oracle.*10g|10\.2\.",
            "11g": r"Oracle.*11g|11\.2\.",
            "12c": r"Oracle.*12c|12\.1\.|12\.2\.",
            "18c": r"Oracle.*18c|18\.",
            "19c": r"Oracle.*19c|19\.",
            "21c": r"Oracle.*21c|21\.",
        },
        "mysql": {
            "5.5": r"MySQL.*5\.5",
            "5.6": r"MySQL.*5\.6",
            "5.7": r"MySQL.*5\.7",
            "8.0": r"MySQL.*8\.0",
        },
        "postgresql": {
            "9.6": r"PostgreSQL.*9\.6",
            "10": r"PostgreSQL.*10\.",
            "11": r"PostgreSQL.*11\.",
            "12": r"PostgreSQL.*12\.",
            "13": r"PostgreSQL.*13\.",
            "14": r"PostgreSQL.*14\.",
            "15": r"PostgreSQL.*15\.",
            "16": r"PostgreSQL.*16\.",
        }
    }

    def detect_from_connection_string(self, conn_string: str) -> Dict:
        """Detect database type and version from connection string."""
        result = {"type": "unknown", "version": "unknown"}

        # SQL Server patterns
        if "sqlserver" in conn_string.lower() or "mssql" in conn_string.lower():
            result["type"] = "sql_server"
        elif "oracle" in conn_string.lower():
            result["type"] = "oracle"
        elif "mysql" in conn_string.lower():
            result["type"] = "mysql"
        elif "postgres" in conn_string.lower():
            result["type"] = "postgresql"

        return result

    def detect_from_scripts(self, sql_content: str) -> Dict:
        """Detect database type from SQL syntax patterns."""
        indicators = {
            "sql_server": [
                r"\bGO\b", r"SET NOCOUNT", r"@@IDENTITY",
                r"NVARCHAR", r"GETDATE\(\)", r"TOP \d+"
            ],
            "oracle": [
                r"SYSDATE", r"NVL\(", r"ROWNUM",
                r"VARCHAR2", r"NUMBER\(", r"PL/SQL"
            ],
            "mysql": [
                r"ENGINE\s*=\s*InnoDB", r"AUTO_INCREMENT",
                r"LIMIT \d+", r"`\w+`"
            ],
            "postgresql": [
                r"SERIAL", r"RETURNING", r"::text",
                r"NOW\(\)", r"ILIKE"
            ],
        }

        scores = {db: 0 for db in indicators}
        for db, patterns in indicators.items():
            for pattern in patterns:
                if re.search(pattern, sql_content, re.IGNORECASE):
                    scores[db] += 1

        detected = max(scores, key=scores.get)
        return {"type": detected, "confidence": scores[detected] / len(indicators[detected])}
```

---

## Supported Technology Stacks

### Backend Stacks

| Stack | File Extensions | Parser | Tools |
|-------|-----------------|--------|-------|
| **C# / .NET** | `*.cs`, `*.csproj`, `*.sln` | Roslyn | .NET Upgrade Assistant, Lizard |
| **VB.NET** | `*.vb`, `*.vbproj` | Roslyn | .NET Upgrade Assistant |
| **ASP.NET WebForms** | `*.aspx`, `*.aspx.cs`, `*.ascx`, `*.master` | Custom + Roslyn | BlazorWebFormsComponents |
| **ASP Classic** | `*.asp`, `*.inc` | Custom regex | - |
| **Java** | `*.java`, `pom.xml`, `build.gradle` | tree-sitter-java | Lizard |
| **Python** | `*.py`, `requirements.txt` | Built-in `ast` | Lizard |
| **PHP** | `*.php`, `composer.json` | tree-sitter-php | Lizard |
| **Node.js** | `*.js`, `*.mjs`, `package.json` | tree-sitter-javascript | Lizard |
| **Go** | `*.go`, `go.mod` | tree-sitter-go | Lizard |
| **Ruby** | `*.rb`, `Gemfile` | tree-sitter-ruby | Lizard |

### Frontend Stacks

| Stack | File Extensions | Parser | Migration Target |
|-------|-----------------|--------|------------------|
| **AngularJS (1.x)** | `*.js` + `ng-*` directives | tree-sitter + custom | Angular 17+ / React / Vue 3 |
| **Angular (2-16)** | `*.ts`, `*.component.ts` | tree-sitter-typescript | Angular 17+ |
| **Vue.js (1.x/2.x)** | `*.vue`, `*.js` | tree-sitter-vue | Vue 3 Composition API |
| **React (Class)** | `*.jsx`, `*.tsx` | tree-sitter-tsx | React Hooks |
| **jQuery** | `*.js` + `$()` patterns | tree-sitter + custom | Vanilla JS / Modern framework |

### Database Stacks

| Source DB | Versions Detected | Target | Migration Tool |
|-----------|-------------------|--------|----------------|
| **SQL Server** | 2008, 2012, 2014, 2016, 2017, 2019, 2022 | PostgreSQL 16 / SQL Server 2022 | SQLines, pgLoader |
| **Oracle** | 10g, 11g, 12c, 18c, 19c, 21c | PostgreSQL 16 | Ora2Pg |
| **MySQL** | 5.5, 5.6, 5.7, 8.0 | PostgreSQL 16 / MySQL 8.0 | pgLoader, SQLines |
| **PostgreSQL** | 9.6 - 16 | PostgreSQL 16 | Native upgrade |

---

## Database Analysis Deep Dive

### DatabaseAnalyzer Agent

```python
class DatabaseAnalyzerAgent:
    """
    Specialized agent for database schema and migration analysis.

    Responsibilities:
    - Detect database type and version
    - Extract schema inventory
    - Analyze stored procedure complexity
    - Assess migration difficulty
    - Identify compatibility issues
    - Generate migration recommendations
    """

    def __init__(self):
        self.ora2pg = Ora2PgWrapper()
        self.sqlines = SQLinesWrapper()
        self.version_detector = DatabaseVersionDetector()
        self.lizard = LizardWrapper()  # For SP complexity

    async def analyze(
        self,
        repo_path: str,
        db_files: List[str],
        connection_strings: List[str]
    ) -> DatabaseAnalysisReport:
        """
        Full database analysis.

        Steps:
        1. Detect database type and version
        2. Extract schema from SQL files or live connection
        3. Analyze stored procedures complexity
        4. Run migration assessment tool
        5. Identify compatibility issues
        6. Generate recommendations
        """

        # Step 1: Detect database
        db_info = self._detect_database(db_files, connection_strings)

        # Step 2: Extract schema
        schema = await self._extract_schema(db_files, db_info)

        # Step 3: Analyze SP complexity
        sp_complexity = await self._analyze_stored_procedures(schema.stored_procedures)

        # Step 4: Run migration assessment
        if db_info["type"] == "oracle":
            assessment = self.ora2pg.assess_from_dump(db_files[0])
        else:
            assessment = self._generic_assessment(schema, db_info)

        # Step 5: Compatibility issues
        issues = self._identify_compatibility_issues(schema, db_info)

        # Step 6: Recommendations
        recommendations = self._generate_recommendations(schema, assessment, issues)

        return DatabaseAnalysisReport(
            source_database=db_info,
            schema_inventory=schema,
            sp_complexity=sp_complexity,
            migration_assessment=assessment,
            compatibility_issues=issues,
            recommendations=recommendations,
        )

    def _detect_database(self, db_files: List[str], conn_strings: List[str]) -> Dict:
        """Detect database type and version."""
        # Try connection strings first
        for conn in conn_strings:
            result = self.version_detector.detect_from_connection_string(conn)
            if result["type"] != "unknown":
                return result

        # Fall back to SQL script analysis
        for db_file in db_files:
            with open(db_file) as f:
                content = f.read()
            result = self.version_detector.detect_from_scripts(content)
            if result["confidence"] > 0.5:
                return result

        return {"type": "unknown", "version": "unknown"}

    async def _analyze_stored_procedures(self, procedures: List[str]) -> SPComplexityReport:
        """
        Analyze stored procedure complexity.

        Uses Lizard for T-SQL/PL-SQL complexity metrics.
        """
        results = []
        for sp in procedures:
            # Write SP to temp file for Lizard analysis
            complexity = self.lizard.analyze_file(sp)
            results.append({
                "name": sp,
                "complexity": complexity,
                "migration_difficulty": self.lizard.get_migration_difficulty(complexity),
            })

        return SPComplexityReport(
            total_procedures=len(procedures),
            avg_complexity=sum(r["complexity"].cyclomatic for r in results) / len(results) if results else 0,
            high_complexity_count=len([r for r in results if r["complexity"].cyclomatic > 20]),
            procedures=results,
        )
```

### Database Compatibility Matrix

```python
DB_COMPATIBILITY_MATRIX = {
    "sql_server_to_postgresql": {
        "data_types": {
            "NVARCHAR": {"target": "VARCHAR", "auto": True},
            "NTEXT": {"target": "TEXT", "auto": True},
            "DATETIME": {"target": "TIMESTAMP", "auto": True},
            "DATETIME2": {"target": "TIMESTAMP", "auto": True},
            "MONEY": {"target": "NUMERIC(19,4)", "auto": True},
            "BIT": {"target": "BOOLEAN", "auto": True},
            "UNIQUEIDENTIFIER": {"target": "UUID", "auto": True},
            "IMAGE": {"target": "BYTEA", "auto": True},
            "XML": {"target": "XML", "auto": True, "note": "Different functions"},
            "GEOGRAPHY": {"target": "GEOMETRY", "auto": False, "note": "PostGIS required"},
            "HIERARCHYID": {"target": "LTREE", "auto": False, "note": "Extension required"},
        },
        "features": {
            "IDENTITY": {"target": "SERIAL/GENERATED", "auto": True},
            "CLUSTERED INDEX": {"target": "Regular index", "auto": True, "note": "No clustered concept"},
            "LINKED SERVERS": {"target": "FDW", "auto": False, "effort": "high"},
            "SYNONYMS": {"target": "Schema + search_path", "auto": False, "effort": "medium"},
            "TRIGGERS (INSTEAD OF)": {"target": "RULES", "auto": False, "effort": "medium"},
            "CTEs (recursive)": {"target": "WITH RECURSIVE", "auto": True},
            "MERGE": {"target": "INSERT ON CONFLICT", "auto": False, "effort": "medium"},
            "PIVOT/UNPIVOT": {"target": "crosstab()", "auto": False, "effort": "medium"},
        },
        "procedural": {
            "T-SQL": {"target": "PL/pgSQL", "auto": False, "effort": "high"},
            "CURSOR": {"target": "CURSOR", "auto": True, "note": "Different syntax"},
            "TRY-CATCH": {"target": "EXCEPTION", "auto": False, "effort": "low"},
            "RAISERROR": {"target": "RAISE", "auto": False, "effort": "low"},
            "@@IDENTITY": {"target": "lastval()", "auto": True},
            "@@ROWCOUNT": {"target": "ROW_COUNT", "auto": True},
        },
    },
    "oracle_to_postgresql": {
        "data_types": {
            "VARCHAR2": {"target": "VARCHAR", "auto": True},
            "NUMBER": {"target": "NUMERIC", "auto": True},
            "DATE": {"target": "TIMESTAMP", "auto": True, "note": "Oracle DATE has time"},
            "CLOB": {"target": "TEXT", "auto": True},
            "BLOB": {"target": "BYTEA", "auto": True},
            "RAW": {"target": "BYTEA", "auto": True},
            "LONG": {"target": "TEXT", "auto": True},
            "ROWID": {"target": "ctid", "auto": False, "note": "Different behavior"},
        },
        "features": {
            "PACKAGES": {"target": "Schemas + functions", "auto": False, "effort": "high"},
            "SEQUENCES": {"target": "SEQUENCE", "auto": True, "note": "Different syntax"},
            "SYNONYMS": {"target": "Search path", "auto": False, "effort": "medium"},
            "DBLINKS": {"target": "FDW", "auto": False, "effort": "high"},
            "MATERIALIZED VIEWS": {"target": "MATERIALIZED VIEW", "auto": True},
            "PARTITIONING": {"target": "Declarative partitioning", "auto": False, "effort": "medium"},
        },
        "procedural": {
            "PL/SQL": {"target": "PL/pgSQL", "auto": False, "effort": "medium"},
            "DECODE": {"target": "CASE", "auto": True},
            "NVL": {"target": "COALESCE", "auto": True},
            "SYSDATE": {"target": "NOW()", "auto": True},
            "ROWNUM": {"target": "LIMIT/row_number()", "auto": False, "effort": "low"},
            "CONNECT BY": {"target": "WITH RECURSIVE", "auto": False, "effort": "medium"},
        },
        "extensions": {
            "orafce": "Oracle compatibility functions for PostgreSQL",
        },
    },
    "mysql_to_postgresql": {
        "data_types": {
            "TINYINT": {"target": "SMALLINT", "auto": True},
            "MEDIUMINT": {"target": "INTEGER", "auto": True},
            "DOUBLE": {"target": "DOUBLE PRECISION", "auto": True},
            "ENUM": {"target": "VARCHAR + CHECK", "auto": False, "effort": "low"},
            "SET": {"target": "ARRAY", "auto": False, "effort": "low"},
            "DATETIME": {"target": "TIMESTAMP", "auto": True},
            "YEAR": {"target": "SMALLINT", "auto": True},
        },
        "features": {
            "AUTO_INCREMENT": {"target": "SERIAL", "auto": True},
            "ENGINE": {"target": "N/A", "auto": True, "note": "Ignored"},
            "FULLTEXT INDEX": {"target": "tsvector + GIN", "auto": False, "effort": "medium"},
            "SPATIAL INDEX": {"target": "PostGIS", "auto": False, "effort": "high"},
        },
    },
}
```

---

## Pattern Recognition

### Legacy Pattern Definitions

```python
LEGACY_PATTERNS = {
    # ASP.NET WebForms patterns
    "aspnet_webforms": {
        "viewstate": {
            "regex": r"ViewState\[|EnableViewState",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Replace with Blazor state management"
        },
        "session_state": {
            "regex": r"Session\[|HttpContext\.Session",
            "risk": "medium",
            "fp_multiplier": 1.15,
            "migration_note": "Replace with distributed cache or JWT claims"
        },
        "code_behind_logic": {
            "regex": r"protected void .+_Click|Page_Load|Page_Init",
            "risk": "high",
            "fp_multiplier": 1.4,
            "migration_note": "Extract to services, use Blazor @onclick"
        },
        "updatepanel": {
            "regex": r"<asp:UpdatePanel|ScriptManager",
            "risk": "high",
            "fp_multiplier": 1.3,
            "migration_note": "Replace with Blazor SignalR"
        },
        "gridview_datasource": {
            "regex": r"<asp:GridView.*DataSourceID|ObjectDataSource",
            "risk": "medium",
            "fp_multiplier": 1.25,
            "migration_note": "Replace with Blazor QuickGrid"
        },
        "inline_sql": {
            "regex": r"SqlCommand|SqlConnection|ExecuteReader|ExecuteNonQuery",
            "risk": "high",
            "fp_multiplier": 1.3,
            "migration_note": "Replace with EF Core + Repository pattern"
        },
    },

    # ASP Classic patterns
    "asp_classic": {
        "adodb_connection": {
            "regex": r"ADODB\.Connection|CreateObject.*ADODB",
            "risk": "high",
            "fp_multiplier": 1.5,
            "migration_note": "Complete rewrite to EF Core"
        },
        "inline_sql_concatenation": {
            "regex": r"(SELECT|INSERT|UPDATE|DELETE).*&.*Request",
            "risk": "critical",
            "fp_multiplier": 1.8,
            "migration_note": "SQL injection risk! Use parameterized queries"
        },
        "response_write": {
            "regex": r"Response\.Write",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Replace with Razor/Blazor templates"
        },
        "on_error_resume": {
            "regex": r"On Error Resume Next",
            "risk": "high",
            "fp_multiplier": 1.3,
            "migration_note": "Replace with proper try/catch"
        },
    },

    # AngularJS patterns
    "angularjs": {
        "scope_usage": {
            "regex": r"\$scope\.",
            "risk": "high",
            "fp_multiplier": 1.4,
            "migration_note": "Replace with component state"
        },
        "rootscope": {
            "regex": r"\$rootScope",
            "risk": "critical",
            "fp_multiplier": 1.6,
            "migration_note": "Replace with service/store"
        },
        "http_legacy": {
            "regex": r"\$http\.(get|post|put|delete)",
            "risk": "low",
            "fp_multiplier": 1.1,
            "migration_note": "Replace with HttpClient or fetch"
        },
    },

    # Vue 2.x patterns
    "vue_legacy": {
        "options_api": {
            "regex": r"export default\s*\{\s*(data|methods|computed|watch)\s*[:\(]",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Migrate to Composition API"
        },
        "vuex_modules": {
            "regex": r"new Vuex\.Store|mapState|mapGetters",
            "risk": "medium",
            "fp_multiplier": 1.25,
            "migration_note": "Migrate to Pinia"
        },
        "mixins_usage": {
            "regex": r"mixins:\s*\[",
            "risk": "high",
            "fp_multiplier": 1.4,
            "migration_note": "Replace with composables"
        },
    },

    # React class patterns
    "react_legacy": {
        "class_component": {
            "regex": r"class\s+\w+\s+extends\s+(React\.)?Component",
            "risk": "medium",
            "fp_multiplier": 1.3,
            "migration_note": "Convert to functional component"
        },
        "lifecycle_methods": {
            "regex": r"componentDidMount|componentWillUnmount|componentDidUpdate",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Replace with useEffect"
        },
        "redux_connect": {
            "regex": r"connect\s*\(\s*mapStateToProps",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Replace with hooks"
        },
    },

    # jQuery patterns
    "jquery": {
        "jquery_selector": {
            "regex": r"\$\s*\(['\"].*?['\"]\)|jQuery\s*\(",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Replace with querySelector or framework"
        },
        "jquery_ajax": {
            "regex": r"\$\.(ajax|get|post|getJSON)",
            "risk": "low",
            "fp_multiplier": 1.1,
            "migration_note": "Replace with fetch"
        },
        "jquery_dom_manipulation": {
            "regex": r"\$\(.*\)\.(html|text|append|prepend|remove)\s*\(",
            "risk": "medium",
            "fp_multiplier": 1.25,
            "migration_note": "Replace with framework data binding"
        },
    },

    # PHP legacy patterns
    "php_legacy": {
        "mysql_functions": {
            "regex": r"mysql_(connect|query|fetch|select_db)",
            "risk": "critical",
            "fp_multiplier": 1.5,
            "migration_note": "Replace with PDO (mysql_* removed in PHP 7)"
        },
        "sql_injection": {
            "regex": r"(SELECT|INSERT|UPDATE|DELETE).*\$_(GET|POST|REQUEST)",
            "risk": "critical",
            "fp_multiplier": 1.8,
            "migration_note": "Use prepared statements"
        },
        "global_variables": {
            "regex": r"global\s+\$",
            "risk": "medium",
            "fp_multiplier": 1.2,
            "migration_note": "Replace with DI"
        },
    },

    # Java legacy patterns
    "java_legacy": {
        "jdbc_direct": {
            "regex": r"DriverManager\.getConnection|PreparedStatement|ResultSet",
            "risk": "high",
            "fp_multiplier": 1.3,
            "migration_note": "Replace with JPA/Spring Data"
        },
        "struts_action": {
            "regex": r"extends Action|ActionForm|struts-config",
            "risk": "high",
            "fp_multiplier": 1.4,
            "migration_note": "Rewrite to Spring Boot"
        },
    },

    # Database patterns (in code)
    "database_in_code": {
        "hardcoded_connection": {
            "regex": r"(Data Source|Server|Host)=[\w\.]+.*(Database|Initial Catalog)=",
            "risk": "critical",
            "fp_multiplier": 1.1,
            "migration_note": "Move to configuration/secrets"
        },
        "hardcoded_credentials": {
            "regex": r"(Password|Pwd|User ID|UID)=[^;]+",
            "risk": "critical",
            "fp_multiplier": 1.1,
            "migration_note": "Use Azure Key Vault or similar"
        },
    },
}
```

---

## Database Models

### Migration Analysis Models (`app/models/migration_analysis.py`)

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

class MigrationAnalysis(Base):
    """Main analysis record for a repository."""
    __tablename__ = "migration_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("projects.id"))
    repo_path = Column(String(500), nullable=False)

    # Detected stacks
    source_stack = Column(String(50))  # Primary: aspnet_webforms, java, php
    secondary_stacks = Column(JSONB)   # ["jquery", "asp_classic", "angularjs"]

    # Target
    target_stack = Column(String(50))  # dotnet8, python, nodejs
    target_db = Column(String(50))     # postgresql, mysql, sqlserver

    # Code Metrics
    total_files = Column(Integer)
    total_loc = Column(Integer)
    total_modules = Column(Integer)
    estimated_fp = Column(Integer)
    complexity_score = Column(Float)
    risk_score = Column(Float)

    # Database Metrics
    db_type = Column(String(50))       # oracle, sqlserver, mysql
    db_version = Column(String(20))
    db_table_count = Column(Integer)
    db_sp_count = Column(Integer)
    db_migration_difficulty = Column(String(1))  # A-E
    db_estimated_days = Column(Float)

    # JSON fields
    file_inventory = Column(JSONB)
    module_inventory = Column(JSONB)
    dependency_graph = Column(JSONB)
    pattern_matches = Column(JSONB)
    risk_register = Column(JSONB)
    frontend_analysis = Column(JSONB)
    database_analysis = Column(JSONB)

    # Status
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(20))  # pending, running, completed, failed

    # Relationships
    modules = relationship("MigrationModule", back_populates="analysis")
    project = relationship("Project", back_populates="migration_analyses")


class MigrationModule(Base):
    """Individual module within an analysis."""
    __tablename__ = "migration_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("migration_analyses.id"))

    name = Column(String(200))
    module_type = Column(String(50))  # page, service, model, controller, component
    stack_type = Column(String(50))   # aspnet_webforms, angularjs, vue
    file_count = Column(Integer)
    loc = Column(Integer)

    # Complexity (from Lizard)
    cyclomatic_complexity = Column(Float)
    cognitive_complexity = Column(Float)
    max_complexity = Column(Float)
    function_count = Column(Integer)

    # Migration
    estimated_fp = Column(Integer)
    migration_difficulty = Column(String(20))  # easy, medium, hard, complex
    migration_target = Column(String(100))     # "Blazor component", "Vue 3"
    dependencies = Column(JSONB)

    # Patterns
    legacy_patterns = Column(JSONB)
    pattern_multiplier = Column(Float, default=1.0)

    # Relationship
    analysis = relationship("MigrationAnalysis", back_populates="modules")


class DatabaseSchema(Base):
    """Database schema analysis."""
    __tablename__ = "migration_db_schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("migration_analyses.id"))

    # Source
    source_type = Column(String(50))   # oracle, sqlserver, mysql
    source_version = Column(String(20))

    # Inventory
    table_count = Column(Integer)
    view_count = Column(Integer)
    stored_procedure_count = Column(Integer)
    function_count = Column(Integer)
    trigger_count = Column(Integer)
    index_count = Column(Integer)
    sequence_count = Column(Integer)

    # Stored procedure complexity
    sp_avg_complexity = Column(Float)
    sp_max_complexity = Column(Float)
    sp_high_complexity_count = Column(Integer)

    # Assessment
    migration_difficulty = Column(String(1))  # A-E (Ora2Pg scale)
    estimated_man_days = Column(Float)
    auto_convertible_percent = Column(Float)

    # Details
    compatibility_issues = Column(JSONB)
    blocking_features = Column(JSONB)
    recommendations = Column(JSONB)
    data_type_mappings = Column(JSONB)
```

---

## API Endpoints

### Migration Analyzer API (`app/api/migration_analyzer.py`)

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from uuid import UUID
from typing import List, Optional

router = APIRouter(prefix="/api/migration", tags=["Migration Analyzer"])

# ============ Analysis Endpoints ============

@router.post("/analyze")
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Start a new migration analysis.

    Request body:
    - repo_path: Path to repository
    - target_stack: Target framework (dotnet8, python, nodejs)
    - target_db: Target database (postgresql, mysql, sqlserver)
    - options: Analysis options (include_db, include_frontend, etc.)
    """
    pass

@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: UUID) -> MigrationAnalysisReport:
    """Get complete analysis results."""
    pass

@router.get("/analyses/{analysis_id}/status")
async def get_analysis_status(analysis_id: UUID) -> AnalysisStatus:
    """Get analysis progress status."""
    pass

# ============ Module Endpoints ============

@router.get("/analyses/{analysis_id}/modules")
async def get_modules(
    analysis_id: UUID,
    stack_filter: Optional[str] = None,
    difficulty_filter: Optional[str] = None
) -> List[MigrationModule]:
    """Get module breakdown with optional filters."""
    pass

@router.get("/analyses/{analysis_id}/modules/{module_id}")
async def get_module_detail(
    analysis_id: UUID,
    module_id: UUID
) -> MigrationModuleDetail:
    """Get detailed module information including patterns."""
    pass

# ============ Database Endpoints ============

@router.get("/analyses/{analysis_id}/database")
async def get_database_analysis(analysis_id: UUID) -> DatabaseAnalysisReport:
    """Get database-specific analysis."""
    pass

@router.get("/analyses/{analysis_id}/database/compatibility")
async def get_db_compatibility(analysis_id: UUID) -> CompatibilityReport:
    """Get database compatibility issues and mappings."""
    pass

@router.get("/analyses/{analysis_id}/database/stored-procedures")
async def get_sp_analysis(analysis_id: UUID) -> SPAnalysisReport:
    """Get stored procedure complexity analysis."""
    pass

# ============ Dependency Endpoints ============

@router.get("/analyses/{analysis_id}/dependencies")
async def get_dependencies(analysis_id: UUID) -> DependencyGraph:
    """Get code dependency graph."""
    pass

@router.get("/analyses/{analysis_id}/dependencies/migration-order")
async def get_migration_order(analysis_id: UUID) -> List[MigrationModule]:
    """Get recommended migration order (topological sort)."""
    pass

# ============ Risk & Pattern Endpoints ============

@router.get("/analyses/{analysis_id}/risks")
async def get_risks(analysis_id: UUID) -> RiskAssessment:
    """Get risk assessment with mitigation recommendations."""
    pass

@router.get("/analyses/{analysis_id}/patterns")
async def get_patterns(analysis_id: UUID) -> PatternReport:
    """Get detected legacy patterns."""
    pass

@router.get("/analyses/{analysis_id}/security")
async def get_security_issues(analysis_id: UUID) -> SecurityReport:
    """Get security vulnerabilities found."""
    pass

# ============ Output Endpoints ============

@router.post("/analyses/{analysis_id}/generate-brown-paper")
async def generate_brown_paper(analysis_id: UUID) -> BrownPaperInput:
    """Generate BROWN_PAPER workflow input from analysis."""
    pass

@router.get("/analyses/{analysis_id}/export")
async def export_analysis(
    analysis_id: UUID,
    format: str = "markdown"  # markdown, json, pdf
) -> ExportResponse:
    """Export analysis to documents."""
    pass

@router.get("/analyses/{analysis_id}/export/documents")
async def get_exported_documents(analysis_id: UUID) -> List[DocumentInfo]:
    """List generated documents."""
    pass

# ============ Tool Integration Endpoints ============

@router.post("/tools/lizard/analyze")
async def run_lizard_analysis(request: LizardRequest) -> LizardResponse:
    """Run Lizard complexity analysis on files."""
    pass

@router.post("/tools/ora2pg/assess")
async def run_ora2pg_assessment(request: Ora2PgRequest) -> Ora2PgResponse:
    """Run Ora2Pg migration assessment."""
    pass

@router.post("/tools/upgrade-assistant/analyze")
async def run_upgrade_assistant(request: UpgradeAssistantRequest) -> UpgradeAssistantResponse:
    """Run .NET Upgrade Assistant analysis."""
    pass
```

---

## Implementation Timeline

### Updated Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MIGRATION ANALYZER IMPLEMENTATION TIMELINE                │
│                                                                              │
│  Week 65: Foundation + Tool Setup (40h)                                      │
│  ├── Day 1: Database migration 023, base models                    (8h)     │
│  ├── Day 2: FileScanner + stack detection                         (8h)     │
│  ├── Day 3: Lizard wrapper + tree-sitter setup                    (8h)     │
│  ├── Day 4: API endpoints (12 endpoints)                          (8h)     │
│  └── Day 5: Miguel orchestrator agent                             (8h)     │
│                                                                              │
│  Week 66: Stack Analyzer Agents (48h)                                        │
│  ├── Day 1: DotNetAnalyzer + .NET Upgrade Assistant wrapper       (8h)     │
│  ├── Day 2: WebForms parser + ASP Classic parser                  (10h)    │
│  ├── Day 3: FrontendAnalyzer (AngularJS, Vue, React, jQuery)      (10h)    │
│  ├── Day 4: PHPAnalyzer + JavaAnalyzer                            (8h)     │
│  └── Day 5: Agent activation logic + integration tests            (8h)     │
│                                                                              │
│  Week 67: Database Analyzer + Pattern Recognition (48h)                      │
│  ├── Day 1: DatabaseAnalyzer agent + version detection            (8h)     │
│  ├── Day 2: Ora2Pg wrapper + assessment integration               (8h)     │
│  ├── Day 3: SQLines wrapper + pgLoader integration                (8h)     │
│  ├── Day 4: DB compatibility matrix + SP complexity               (8h)     │
│  ├── Day 5: Pattern recognizer (50+ patterns)                     (8h)     │
│  └── Day 6: Cross-cutting agents (Quinn, Eliza, Felix) skills     (8h)     │
│                                                                              │
│  Week 68: FP Estimation + Output Generation (40h)                            │
│  ├── Day 1: FP estimator with tool integration                    (8h)     │
│  ├── Day 2: Risk assessor + dependency graph                      (8h)     │
│  ├── Day 3: BrownPaperGenerator (8 questions auto-fill)           (8h)     │
│  ├── Day 4: Document export (8 markdown templates)                (8h)     │
│  └── Day 5: Dashboard UI (migration-analyzer.html)                (8h)     │
│                                                                              │
│  Week 69: Output Agents + Integration (32h)                                  │
│  ├── Day 1: Diana documentation skills                            (8h)     │
│  ├── Day 2: Peter business context skills                         (8h)     │
│  ├── Day 3: Full workflow integration                             (8h)     │
│  └── Day 4: E2E tests with multi-stack repos                      (8h)     │
│                                                                              │
│  Week 70: Validation + Polish (24h)                                          │
│  ├── Day 1: HCI-CRS validation (full analysis)                    (8h)     │
│  ├── Day 2: Compare with manual analysis, accuracy tuning         (8h)     │
│  └── Day 3: Documentation, performance optimization               (8h)     │
│                                                                              │
│  TOTAL: 232 uur (~6 weken @ 40h/week)                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Week-by-Week Deliverables

| Week | Deliverables | Tools Integrated | Tests |
|------|--------------|------------------|-------|
| **65** | Foundation + Miguel agent | Lizard, tree-sitter | Unit tests |
| **66** | 4 Stack Analyzer agents | .NET Upgrade Assistant, Roslyn | Agent tests |
| **67** | DatabaseAnalyzer + Patterns | Ora2Pg, SQLines, pgLoader | DB tests |
| **68** | FP Estimation + Output | Google DMA concepts | Integration |
| **69** | Diana + Peter skills | - | Workflow tests |
| **70** | Validation | All tools | E2E with HCI-CRS |

---

## Output Documents

### Generated Documents (8 total)

1. **MIGRATION_ANALYSIS.md** - Executive summary
2. **MODULE_INVENTORY.md** - All modules with FP estimates
3. **DATABASE_ANALYSIS.md** - Schema, SP, compatibility
4. **DEPENDENCY_GRAPH.md** - Mermaid diagram + migration order
5. **PATTERN_REPORT.md** - Legacy patterns found
6. **RISK_REGISTER.md** - Prioritized risks
7. **FP_ESTIMATION.md** - Detailed breakdown
8. **SECURITY_REPORT.md** - Vulnerabilities found

### BROWN_PAPER Auto-Fill

| Question | Source Agent | Auto-Fill Quality |
|----------|--------------|-------------------|
| Q1: Legacy System Analysis | Miguel + Stack Analyzers | 90% |
| Q2: Migration Target | Miguel | 85% |
| Q3: Migration Strategy | Miguel + Felix | 80% |
| Q4: Data Migration | DatabaseAnalyzer | 95% |
| Q5: Problem Statement | Peter | 70% (needs review) |
| Q6: Stakeholders | Peter | 60% (needs input) |
| Q7: Success Criteria | Peter + Eliza | 75% |
| Q8: Timeline | Eliza | 85% |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code analysis time | <5 min per 10K LOC | Benchmark |
| DB analysis time | <2 min per 100 tables | Benchmark |
| FP accuracy | ±20% vs manual | Compare with HCI-CRS |
| Pattern detection | >90% recall | Manual validation |
| DB compatibility | >95% issues found | Expert review |
| Risk identification | >80% of known risks | Compare with experts |
| BROWN_PAPER quality | 70%+ usable without edits | User feedback |
| Token savings | >60% vs mega-agent | Token counting |

---

## Dependencies

| Dependency | Purpose | Install | Status |
|------------|---------|---------|--------|
| Lizard | Complexity analysis | `pip install lizard` | 📦 To install |
| tree-sitter | Multi-language AST | `pip install tree-sitter` | 📦 To install |
| tree-sitter-* | Language grammars | Per language | 📦 To install |
| Ora2Pg | Oracle assessment | System package | 📦 To install |
| SQLines | SQL conversion | Download binary | 📦 To install |
| pgLoader | Data migration | System package | 📦 To install |
| .NET Upgrade Assistant | .NET analysis | `dotnet tool install` | 📦 To install |
| Serena MCP | Symbol extraction | ✅ Available | ✅ Ready |
| ChromaDB | CodeRAG storage | ✅ Available | ✅ Ready |

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Tool installation complexity | Medium | Medium | Docker containers for tools |
| Ora2Pg requires Oracle client | High | High | Use dump file mode |
| AST parsing edge cases | Medium | Medium | Fallback to regex |
| Large repo performance | Medium | Low | Parallel processing |
| FP estimation accuracy | Medium | Medium | Calibrate with HCI-CRS data |
| Agent coordination overhead | Low | Medium | Efficient message passing |

---

## References

### Open Source Tools

- [Lizard - Code Complexity Analyzer](https://github.com/terryyin/lizard)
- [Genese Complexity](https://github.com/geneseframework/complexity)
- [.NET Upgrade Assistant](https://github.com/dotnet/upgrade-assistant)
- [Ora2Pg](https://github.com/darold/ora2pg)
- [SQLines](https://github.com/dmtolpeko/sqlines)
- [pgLoader](https://github.com/dimitri/pgloader)
- [tree-sitter](https://github.com/tree-sitter/tree-sitter)

### Educational Resources

- [Jeff Fritz - WebForms to Blazor](https://youtu.be/TpUFAfcim6w)
- [BlazorWebFormsComponents](https://github.com/FritzAndFriends/BlazorWebFormsComponents)
- [DotVVM Modernization](https://www.dotvvm.com/modernize)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

### Research

- [LLM Agents for Code Migration](https://www.aviator.co/blog/llm-agents-for-code-migration-a-real-world-case-study/)
- [RepoAgent](https://github.com/OpenBMB/RepoAgent)
- [GPT-Migrate](https://github.com/joshpxyne/gpt-migrate)

---

**Document Status**: APPROVED
**Version**: 2.0
**Next Step**: Add to ROADMAP.md, create implementation tickets
**Owner**: Miguel (Orchestrator) + Felix (Architecture)
**Reviewers**: Quinn (Security), Eliza (Estimation), All Stack Analyzer agents
