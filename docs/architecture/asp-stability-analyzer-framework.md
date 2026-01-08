# ASP Application Stability Analyzer Framework

**Datum**: 2026-01-06
**Status**: DESIGN PROPOSAL
**Owner**: MarQed AI Platform
**Scope**: Classic ASP, PHP, VB.NET legacy applications

---

## Executive Summary

Uitgebreid stability analysis framework dat **alle** potentiele crash-oorzaken detecteert, niet alleen ADO leaks.

### 8 Detection Categories

| # | Category | Detectors | Priority |
|---|----------|-----------|----------|
| 1 | ADO/Database Leaks | Connection, Recordset, Transaction | CRITICAL |
| 2 | COM Object Leaks | XMLHTTP, PDF, XMLDOM, Custom | HIGH |
| 3 | External Service Risks | Timeout, Retry, Circuit Breaker | HIGH |
| 4 | Memory Intensive Ops | PDF Gen, Large Arrays, Caching | MEDIUM |
| 5 | File Handle Leaks | FileSystemObject, TextStream | MEDIUM |
| 6 | Session State Issues | Size, Timeout, Serialization | LOW |
| 7 | Exception Handling | On Error, Error Propagation | MEDIUM |
| 8 | SQL Performance | Deadlocks, Blocking, N+1 | MEDIUM |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              ASPStabilityAnalyzerService                        │
│              (Main Orchestrator)                                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  IncludeFile  │       │    Symbol     │       │   Pattern     │
│   Resolver    │       │   Analyzer    │       │   Matcher     │
└───────────────┘       └───────────────┘       └───────────────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────┐
│                          DETECTORS                                │
├─────────────┬─────────────┬─────────────┬─────────────┬──────────┤
│ ADO Leak    │ COM Object  │ External    │ Memory      │ File     │
│ Detector    │ Detector    │ Service     │ Analyzer    │ Handle   │
│             │             │ Analyzer    │             │ Detector │
├─────────────┼─────────────┼─────────────┼─────────────┼──────────┤
│ Session     │ Exception   │ SQL         │             │          │
│ Analyzer    │ Handler     │ Analyzer    │             │          │
│             │ Analyzer    │             │             │          │
└─────────────┴─────────────┴─────────────┴─────────────┴──────────┘
```

---

## 1. ADO Leak Detector (Extends Resource Leak Framework)

See: [resource-leak-detection-framework.md](./resource-leak-detection-framework.md)

### Enhanced with Wrapper Analysis

```python
class ADOLeakDetector(BaseResourceLeakDetector):
    """
    Detects ADO connection and recordset leaks with wrapper function support.
    """

    def get_open_patterns(self) -> Dict[str, List[str]]:
        return {
            'connection': [
                r'Set\s+(\w+)\s*=\s*CreateCusCon\(\)',
                r'Set\s+(\w+)\s*=\s*CreateCon\(\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(["\']ADODB\.Connection',
            ],
            'recordset': [
                r'Set\s+(\w+)\s*=\s*CreateRecordset\(\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(["\']ADODB\.Recordset',
            ],
        }

    def get_close_patterns(self) -> Dict[str, List[str]]:
        return {
            'direct': [r'(\w+)\.Close\s*\(\s*\)'],
            'wrapper': [
                r'Call\s+TryCloseConnection\s*\(\s*(\w+)\s*\)',
                r'Call\s+TryDispose\s*\(\s*(\w+)\s*\)',
                r'Call\s+CloseAndDispose\s*\(\s*\)',  # Needs body analysis
            ],
        }

    def analyze_wrapper_function(self, wrapper_name: str, file_content: str) -> List[str]:
        """Extract which variables a wrapper function closes."""
        # Parse Sub/Function body to find .Close() calls
        pass
```

---

## 2. COM Object Leak Detector

```python
class COMObjectLeakDetector:
    """
    Detects COM object leaks (XMLHTTP, PDF, XMLDOM, etc.)
    """

    COM_OBJECT_TYPES = {
        'xmlhttp': {
            'create': [r'Server\.CreateObject\s*\(["\']Msxml2\.ServerXMLHTTP'],
            'cleanup': [r'(\w+)\.abort\s*\(', r'Set\s+(\w+)\s*=\s*Nothing'],
            'risk': 'HIGH',
            'memory_impact': 'MEDIUM',
        },
        'abcpdf': {
            'create': [r'Server\.CreateObject\s*\(["\']ABCpdf\d*\.Doc'],
            'cleanup': [r'(\w+)\.Clear\s*\(', r'Set\s+(\w+)\s*=\s*Nothing'],
            'risk': 'HIGH',
            'memory_impact': 'HIGH',  # 10-100MB per instance
        },
        'xmldom': {
            'create': [r'Server\.CreateObject\s*\(["\']Microsoft\.XMLDOM'],
            'cleanup': [r'Set\s+(\w+)\s*=\s*Nothing'],
            'risk': 'MEDIUM',
            'memory_impact': 'MEDIUM',
        },
        'custom': {
            'create': [r'Server\.CreateObject\s*\(["\']SOM\.|SpotOnMedics\.'],
            'cleanup': [r'Set\s+(\w+)\s*=\s*Nothing'],
            'risk': 'MEDIUM',
            'memory_impact': 'UNKNOWN',
        },
    }

    def analyze(self, file_path: str) -> List[COMLeakFinding]:
        findings = []
        for obj_type, patterns in self.COM_OBJECT_TYPES.items():
            creates = self._find_creates(patterns['create'])
            cleanups = self._find_cleanups(patterns['cleanup'])
            leaks = self._calculate_leaks(creates, cleanups)
            if leaks:
                findings.append(COMLeakFinding(
                    object_type=obj_type,
                    leaked_vars=leaks,
                    risk=patterns['risk'],
                    memory_impact=patterns['memory_impact'],
                ))
        return findings
```

---

## 3. External Service Analyzer

```python
class ExternalServiceAnalyzer:
    """
    Analyzes external service calls for timeout/failure risks.
    """

    def analyze(self, file_path: str) -> List[ExternalServiceFinding]:
        findings = []

        # Find XMLHTTP calls
        http_calls = self._find_http_calls()

        for call in http_calls:
            issues = []

            # Check timeout configuration
            if not self._has_timeout_config(call):
                issues.append('NO_TIMEOUT')

            # Check error handling
            if not self._has_error_handling(call):
                issues.append('NO_ERROR_HANDLING')

            # Check retry logic
            if not self._has_retry_logic(call):
                issues.append('NO_RETRY')

            if issues:
                findings.append(ExternalServiceFinding(
                    line=call.line,
                    url_pattern=call.url,
                    issues=issues,
                    recommendation=self._get_recommendation(issues),
                ))

        return findings

    TIMEOUT_PATTERN = r'setTimeouts\s*\(\s*\d+'
    ERROR_HANDLING_PATTERN = r'If\s+.*Status\s*[<>!=]'
```

---

## 4. Memory Intensive Operations Analyzer

```python
class MemoryAnalyzer:
    """
    Detects memory-intensive operations that could cause OOM.
    """

    MEMORY_PATTERNS = {
        'pdf_generation': {
            'pattern': r'ABCpdf\d*\.Doc',
            'risk': 'HIGH',
            'mitigation': 'Limit concurrent PDF generation, add .Clear()',
        },
        'large_recordset': {
            'pattern': r'\.GetRows\s*\(',
            'risk': 'MEDIUM',
            'mitigation': 'Use pagination, streaming',
        },
        'string_concatenation_loop': {
            'pattern': r'(Do While|For\s+).*\n.*\w+\s*=\s*\w+\s*&',
            'risk': 'MEDIUM',
            'mitigation': 'Use StringBuilder or array Join',
        },
        'large_array': {
            'pattern': r'ReDim\s+Preserve',
            'risk': 'MEDIUM',
            'mitigation': 'Pre-allocate array size',
        },
    }
```

---

## 5. File Handle Leak Detector

```python
class FileHandleDetector:
    """
    Detects file handle leaks from FileSystemObject usage.
    """

    def get_open_patterns(self) -> List[str]:
        return [
            r'(\w+)\.OpenTextFile\s*\(',
            r'(\w+)\.CreateTextFile\s*\(',
            r'(\w+)\.OpenAsTextStream\s*\(',
        ]

    def get_close_patterns(self) -> List[str]:
        return [
            r'(\w+)\.Close\s*\(',
            r'Set\s+(\w+)\s*=\s*Nothing',
        ]
```

---

## 6. Session State Analyzer

```python
class SessionAnalyzer:
    """
    Analyzes Session usage for potential issues.
    """

    def analyze(self, file_path: str) -> List[SessionFinding]:
        findings = []

        # Check for large objects in Session
        session_assigns = self._find_session_assignments()
        for assign in session_assigns:
            if self._is_large_object(assign.value):
                findings.append(SessionFinding(
                    issue='LARGE_OBJECT_IN_SESSION',
                    line=assign.line,
                    recommendation='Store reference/ID instead of full object',
                ))

        # Check for Session without timeout handling
        if self._has_session_dependency_without_check():
            findings.append(SessionFinding(
                issue='NO_SESSION_CHECK',
                recommendation='Add Session timeout handling',
            ))

        return findings
```

---

## 7. Exception Handler Analyzer

```python
class ExceptionAnalyzer:
    """
    Analyzes error handling patterns for silent failures.
    """

    def analyze(self, file_path: str) -> List[ExceptionFinding]:
        findings = []

        # Find "On Error Resume Next" blocks
        error_blocks = self._find_on_error_blocks()

        for block in error_blocks:
            issues = []

            # Check for Err.Number check
            if not self._has_err_check(block):
                issues.append('NO_ERR_CHECK')

            # Check for Err.Clear
            if not self._has_err_clear(block):
                issues.append('NO_ERR_CLEAR')

            # Check for logging
            if not self._has_error_logging(block):
                issues.append('NO_ERROR_LOGGING')

            # Check for "On Error Goto 0" to reset
            if not self._has_error_reset(block):
                issues.append('NO_ERROR_RESET')

            if issues:
                findings.append(ExceptionFinding(
                    line=block.start_line,
                    issues=issues,
                    scope_lines=block.end_line - block.start_line,
                ))

        return findings
```

---

## 8. SQL Performance Analyzer

```python
class SQLAnalyzer:
    """
    Analyzes SQL patterns for performance issues.
    """

    ANTIPATTERNS = {
        'n_plus_1': {
            'pattern': r'(Do While|For\s+).*\n.*\.Open.*SELECT',
            'risk': 'HIGH',
            'mitigation': 'Use JOIN or batch query',
        },
        'select_star': {
            'pattern': r'SELECT\s+\*\s+FROM',
            'risk': 'MEDIUM',
            'mitigation': 'Select only needed columns',
        },
        'no_where_clause': {
            'pattern': r'SELECT.*FROM\s+\w+\s*$',
            'risk': 'HIGH',
            'mitigation': 'Add WHERE clause or LIMIT',
        },
        'string_concat_sql': {
            'pattern': r'"\s*&\s*\w+\s*&\s*".*SELECT|INSERT|UPDATE|DELETE',
            'risk': 'CRITICAL',  # SQL Injection!
            'mitigation': 'Use parameterized queries',
        },
    }
```

---

## API Endpoints

```python
# backend/app/api/stability_analysis.py

router = APIRouter(prefix="/api/stability", tags=["stability"])

@router.post("/analyze")
async def analyze_stability(
    project_id: int,
    categories: List[str] = None,  # All if None
) -> StabilityReport:
    """Run full stability analysis on project."""
    pass

@router.get("/report/{project_id}")
async def get_stability_report(project_id: int) -> StabilityReport:
    """Get latest stability report."""
    pass

@router.get("/categories")
async def list_categories() -> List[CategoryInfo]:
    """List available analysis categories."""
    return [
        {"id": "ado_leaks", "name": "ADO Connection Leaks", "severity": "CRITICAL"},
        {"id": "com_objects", "name": "COM Object Leaks", "severity": "HIGH"},
        {"id": "external_services", "name": "External Service Risks", "severity": "HIGH"},
        {"id": "memory_ops", "name": "Memory Intensive Operations", "severity": "MEDIUM"},
        {"id": "file_handles", "name": "File Handle Leaks", "severity": "MEDIUM"},
        {"id": "session_state", "name": "Session State Issues", "severity": "LOW"},
        {"id": "exceptions", "name": "Exception Handling", "severity": "MEDIUM"},
        {"id": "sql_performance", "name": "SQL Performance", "severity": "MEDIUM"},
    ]

@router.post("/fix-suggestions/{finding_id}")
async def get_fix_suggestions(finding_id: int) -> FixSuggestion:
    """Get AI-generated fix suggestions for a finding."""
    pass
```

---

## Database Schema

```sql
CREATE TABLE stability_scans (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    scan_date TIMESTAMP DEFAULT NOW(),
    total_files INTEGER,
    categories_analyzed TEXT[],
    overall_risk VARCHAR(20)  -- CRITICAL, HIGH, MEDIUM, LOW
);

CREATE TABLE stability_findings (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES stability_scans(id),
    category VARCHAR(50),
    file_path TEXT,
    line_number INTEGER,
    finding_type VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    suggested_fix TEXT,
    fixed_at TIMESTAMP,
    fixed_by INTEGER REFERENCES users(id)
);

CREATE TABLE stability_metrics (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    metric_date DATE,
    ado_leak_count INTEGER,
    com_leak_count INTEGER,
    file_leak_count INTEGER,
    exception_issues INTEGER,
    overall_score INTEGER  -- 0-100
);
```

---

## Integration Points

### 1. Brown Paper Workflow
- Add stability scan as step after code extraction
- Include in migration risk assessment

### 2. Quality Gates
- Block deployment if CRITICAL findings
- Configurable thresholds per category

### 3. Technical Debt Dashboard
- Auto-create debt items for findings
- Track remediation progress

### 4. CI/CD Pipeline
- Pre-commit hook for new leaks
- PR blocking for CRITICAL issues

---

## Implementation Phases

### Fase 21A: Core Stability Framework (Week 143)
- [ ] Base analyzer architecture
- [ ] ADO Leak Detector (enhanced)
- [ ] COM Object Detector
- [ ] API endpoints

### Fase 21B: Additional Detectors (Week 144)
- [ ] External Service Analyzer
- [ ] Memory Analyzer
- [ ] File Handle Detector
- [ ] Exception Analyzer

### Fase 21C: Integration & Dashboard (Week 145)
- [ ] SQL Analyzer
- [ ] Session Analyzer
- [ ] Stability Dashboard
- [ ] Brown Paper integration
- [ ] Quality Gate integration

**Total: 3 weeks, 84 hours**

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Detection accuracy | >90% |
| False positive rate | <5% |
| Analysis speed | <2s per file |
| Categories covered | 8 |
| Fix suggestion accuracy | >80% |

---

*ASP Application Stability Analyzer Framework - MarQed AI Platform*
