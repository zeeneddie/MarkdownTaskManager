# Resource Leak Detection Framework

**Datum**: 2026-01-06
**Status**: DESIGN PROPOSAL
**Owner**: MarQed AI Platform

---

## Executive Summary

Generieke resource leak detectie framework met taal-specifieke plugins.
Volgt het bestaande `BaseBusinessRuleExtractor` patroon.

---

## Architecture Overview

```
                    ┌─────────────────────────────┐
                    │  ResourceLeakDetectorService │
                    │  (Orchestrator)              │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  BaseResourceLeakDetector   │
                    │  (Abstract Base Class)      │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────┬───────────┬───┴───┬───────────┬──────────┐
        ▼          ▼           ▼       ▼           ▼          ▼
   ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ClassicASP│ │  PHP   │ │ Java   │ │ VB.NET │ │  C#    │ │ Python │
   │Detector │ │Detector│ │Detector│ │Detector│ │Detector│ │Detector│
   └─────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

---

## 1. Generic Resource Types

```python
from enum import Enum

class ResourceType(Enum):
    DATABASE_CONNECTION = "database_connection"
    RECORDSET = "recordset"
    FILE_HANDLE = "file_handle"
    HTTP_CONNECTION = "http_connection"
    SOCKET = "socket"
    STREAM = "stream"
    COM_OBJECT = "com_object"
    MEMORY_BUFFER = "memory_buffer"
    TRANSACTION = "transaction"
```

---

## 2. Generic Leak Pattern Types

```python
class LeakPatternType(Enum):
    # Resource created but never released
    NEVER_CLOSED = "never_closed"

    # Resource created in loop without per-iteration cleanup
    LOOP_LEAK = "loop_leak"

    # Resource created in function without cleanup before return
    FUNCTION_LEAK = "function_leak"

    # Resource orphaned by early exit (Response.End, return, throw)
    EARLY_EXIT_LEAK = "early_exit_leak"

    # More closes than opens (indicates logic error)
    OVER_CLOSING = "over_closing"

    # Resource assigned but condition prevents closure
    CONDITIONAL_LEAK = "conditional_leak"
```

---

## 3. Base Detector Interface

```python
# backend/app/services/static_analysis/base_resource_leak_detector.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class ResourceOperation:
    """A single resource open or close operation."""
    line_number: int
    operation_type: str  # 'open' or 'close'
    resource_type: ResourceType
    variable_name: str
    in_loop: bool = False
    in_function: Optional[str] = None
    code_snippet: str = ""

@dataclass
class LeakFinding:
    """A detected resource leak."""
    file_path: str
    line_number: int
    resource_type: ResourceType
    variable_name: str
    leak_pattern: LeakPatternType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    suggested_fix: str

@dataclass
class LeakReport:
    """Report for a single file."""
    file_path: str
    language: str
    opens: List[ResourceOperation]
    closes: List[ResourceOperation]
    balance: int  # opens - closes
    findings: List[LeakFinding]
    risk_rating: str  # CRITICAL, HIGH, MEDIUM, LOW, CLEAN


class BaseResourceLeakDetector(ABC):
    """
    Abstract base class for language-specific resource leak detectors.

    Subclasses must implement:
    - get_supported_extensions()
    - get_language()
    - get_open_patterns() -> Dict[ResourceType, List[str]]
    - get_close_patterns() -> Dict[ResourceType, List[str]]
    - detect_loops() -> List[Tuple[int, int]]  # start_line, end_line
    - detect_early_exits() -> List[int]  # line numbers
    """

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        pass

    @abstractmethod
    def get_language(self) -> str:
        """Return language name."""
        pass

    @abstractmethod
    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        """Return regex patterns for resource opening operations."""
        pass

    @abstractmethod
    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        """Return regex patterns for resource closing operations."""
        pass

    def analyze_file(self, file_path: str) -> LeakReport:
        """Analyze a single file for resource leaks."""
        # Implementation in base class - calls abstract methods
        pass

    def analyze_directory(self, dir_path: str) -> List[LeakReport]:
        """Analyze all files in directory."""
        pass
```

---

## 4. Language-Specific Implementations

### 4.1 Classic ASP Detector

```python
# backend/app/services/static_analysis/classic_asp_leak_detector.py

class ClassicASPLeakDetector(BaseResourceLeakDetector):

    SUPPORTED_EXTENSIONS = ['.asp', '.asa']

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'Set\s+(\w+)\s*=\s*CreateCusCon\(\)',
                r'Set\s+(\w+)\s*=\s*CreateCon\(\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ADODB\.Connection',
                r'(\w+)\.Open\s+',  # connection.Open
            ],
            ResourceType.RECORDSET: [
                r'Set\s+(\w+)\s*=\s*CreateRecordset\(\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ADODB\.Recordset',
                r'Set\s+(\w+)\s*=\s*\w+\.Execute\s*\(',  # con.Execute
            ],
            ResourceType.COM_OBJECT: [
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(',
                r'Set\s+(\w+)\s*=\s*CreateObject\s*\(',
            ],
            ResourceType.HTTP_CONNECTION: [
                r'Set\s+(\w+)\s*=\s*.*XMLHTTP',
                r'Set\s+(\w+)\s*=\s*.*ServerXMLHTTP',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\.Close\s*\(\s*\)',
                r'Call\s+(\w+)\.Close\s*\(\s*\)',
                r'Call\s+TryCloseConnection\s*\(\s*(\w+)\s*\)',
            ],
            ResourceType.RECORDSET: [
                r'(\w+)\.Close\s*\(\s*\)',
                r'Call\s+(\w+)\.Close\s*\(\s*\)',
                r'Call\s+TryDispose\s*\(\s*(\w+)\s*\)',
            ],
            ResourceType.COM_OBJECT: [
                r'Set\s+(\w+)\s*=\s*Nothing',
            ],
        }

    def get_early_exit_patterns(self) -> List[str]:
        return [
            r'Response\.End\s*\(\s*\)',
            r'Response\.Redirect\s+',
            r'Exit\s+Sub',
            r'Exit\s+Function',
        ]

    def get_loop_patterns(self) -> List[Tuple[str, str]]:
        return [
            (r'Do\s+While', r'Loop'),
            (r'Do\s+Until', r'Loop'),
            (r'For\s+', r'Next'),
            (r'While\s+', r'Wend'),
        ]
```

### 4.2 PHP Detector

```python
# backend/app/services/static_analysis/php_leak_detector.py

class PHPLeakDetector(BaseResourceLeakDetector):

    SUPPORTED_EXTENSIONS = ['.php', '.php5', '.phtml']

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'\$(\w+)\s*=\s*mysqli_connect\s*\(',
                r'\$(\w+)\s*=\s*new\s+mysqli\s*\(',
                r'\$(\w+)\s*=\s*new\s+PDO\s*\(',
                r'\$(\w+)\s*=\s*pg_connect\s*\(',
                r'\$(\w+)\s*=\s*oci_connect\s*\(',
            ],
            ResourceType.RECORDSET: [
                r'\$(\w+)\s*=\s*mysqli_query\s*\(',
                r'\$(\w+)\s*=\s*\$\w+->query\s*\(',
                r'\$(\w+)\s*=\s*pg_query\s*\(',
            ],
            ResourceType.FILE_HANDLE: [
                r'\$(\w+)\s*=\s*fopen\s*\(',
                r'\$(\w+)\s*=\s*gzopen\s*\(',
            ],
            ResourceType.HTTP_CONNECTION: [
                r'\$(\w+)\s*=\s*curl_init\s*\(',
                r'\$(\w+)\s*=\s*fsockopen\s*\(',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'mysqli_close\s*\(\s*\$(\w+)',
                r'\$(\w+)->close\s*\(',
                r'pg_close\s*\(\s*\$(\w+)',
                r'oci_close\s*\(\s*\$(\w+)',
            ],
            ResourceType.RECORDSET: [
                r'mysqli_free_result\s*\(\s*\$(\w+)',
                r'\$(\w+)->free\s*\(',
                r'pg_free_result\s*\(\s*\$(\w+)',
            ],
            ResourceType.FILE_HANDLE: [
                r'fclose\s*\(\s*\$(\w+)',
                r'gzclose\s*\(\s*\$(\w+)',
            ],
            ResourceType.HTTP_CONNECTION: [
                r'curl_close\s*\(\s*\$(\w+)',
            ],
        }
```

### 4.3 Java Detector

```python
# backend/app/services/static_analysis/java_leak_detector.py

class JavaLeakDetector(BaseResourceLeakDetector):

    SUPPORTED_EXTENSIONS = ['.java']

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\s*=\s*DriverManager\.getConnection\s*\(',
                r'(\w+)\s*=\s*dataSource\.getConnection\s*\(',
            ],
            ResourceType.RECORDSET: [
                r'(\w+)\s*=\s*\w+\.executeQuery\s*\(',
                r'(\w+)\s*=\s*\w+\.executeUpdate\s*\(',
                r'ResultSet\s+(\w+)\s*=',
                r'PreparedStatement\s+(\w+)\s*=',
            ],
            ResourceType.FILE_HANDLE: [
                r'(\w+)\s*=\s*new\s+FileInputStream\s*\(',
                r'(\w+)\s*=\s*new\s+FileOutputStream\s*\(',
                r'(\w+)\s*=\s*new\s+BufferedReader\s*\(',
            ],
            ResourceType.STREAM: [
                r'(\w+)\s*=\s*new\s+\w*Stream\s*\(',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\.close\s*\(\s*\)',
            ],
            ResourceType.RECORDSET: [
                r'(\w+)\.close\s*\(\s*\)',
            ],
            ResourceType.FILE_HANDLE: [
                r'(\w+)\.close\s*\(\s*\)',
            ],
        }

    def detect_try_with_resources(self, source: str) -> List[str]:
        """Detect Java 7+ try-with-resources (auto-close)."""
        # try (Connection con = ...) { } - auto closed
        pattern = r'try\s*\(\s*\w+\s+(\w+)\s*='
        return re.findall(pattern, source)
```

### 4.4 VB.NET / C# Detector

```python
# backend/app/services/static_analysis/dotnet_leak_detector.py

class DotNetLeakDetector(BaseResourceLeakDetector):

    SUPPORTED_EXTENSIONS = ['.vb', '.cs']

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\s*=\s*new\s+SqlConnection\s*\(',
                r'(\w+)\s*=\s*new\s+OracleConnection\s*\(',
                r'(\w+)\s*=\s*new\s+\w*Connection\s*\(',
                r'(\w+)\.Open\s*\(',
            ],
            ResourceType.RECORDSET: [
                r'(\w+)\s*=\s*\w+\.ExecuteReader\s*\(',
                r'SqlDataReader\s+(\w+)',
            ],
            ResourceType.FILE_HANDLE: [
                r'(\w+)\s*=\s*File\.Open\s*\(',
                r'(\w+)\s*=\s*new\s+StreamReader\s*\(',
                r'(\w+)\s*=\s*new\s+StreamWriter\s*\(',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\.Close\s*\(\s*\)',
                r'(\w+)\.Dispose\s*\(\s*\)',
            ],
            ResourceType.RECORDSET: [
                r'(\w+)\.Close\s*\(\s*\)',
                r'(\w+)\.Dispose\s*\(\s*\)',
            ],
        }

    def detect_using_blocks(self, source: str) -> List[str]:
        """Detect C#/VB.NET using blocks (auto-dispose)."""
        # using (var con = new SqlConnection()) { } - auto disposed
        pattern = r'using\s*\(\s*(?:var\s+)?(\w+)\s*='
        return re.findall(pattern, source, re.IGNORECASE)
```

### 4.5 Python Detector

```python
# backend/app/services/static_analysis/python_leak_detector.py

class PythonLeakDetector(BaseResourceLeakDetector):

    SUPPORTED_EXTENSIONS = ['.py']

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\s*=\s*psycopg2\.connect\s*\(',
                r'(\w+)\s*=\s*mysql\.connector\.connect\s*\(',
                r'(\w+)\s*=\s*sqlite3\.connect\s*\(',
                r'(\w+)\s*=\s*\w+\.connect\s*\(',
            ],
            ResourceType.FILE_HANDLE: [
                r'(\w+)\s*=\s*open\s*\(',
            ],
            ResourceType.HTTP_CONNECTION: [
                r'(\w+)\s*=\s*requests\.\w+\s*\(',  # requests library
                r'(\w+)\s*=\s*urllib\.request\.urlopen\s*\(',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.DATABASE_CONNECTION: [
                r'(\w+)\.close\s*\(\s*\)',
            ],
            ResourceType.FILE_HANDLE: [
                r'(\w+)\.close\s*\(\s*\)',
            ],
        }

    def detect_context_managers(self, source: str) -> List[str]:
        """Detect Python with statements (auto-close)."""
        # with open('file') as f: - auto closed
        pattern = r'with\s+.*\s+as\s+(\w+)'
        return re.findall(pattern, source)
```

---

## 5. API Integration

```python
# backend/app/api/resource_leak_analysis.py

from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/resource-leaks", tags=["resource-leaks"])

@router.post("/analyze")
async def analyze_for_leaks(
    project_id: int,
    file_paths: Optional[List[str]] = None,
    severity_threshold: str = "MEDIUM"
) -> dict:
    """Analyze project files for resource leaks."""
    pass

@router.get("/report/{project_id}")
async def get_leak_report(project_id: int) -> dict:
    """Get leak analysis report for project."""
    pass

@router.get("/summary/{project_id}")
async def get_leak_summary(project_id: int) -> dict:
    """Get summary statistics."""
    return {
        "total_files_analyzed": 100,
        "files_with_leaks": 12,
        "critical_leaks": 3,
        "high_leaks": 5,
        "medium_leaks": 4,
        "estimated_daily_leak_count": 1200,
        "top_offenders": [...],
    }
```

---

## 6. Integration Points

### 6.1 Brown Paper Workflow
- Add leak analysis as optional step after code scanning
- Include in migration assessment

### 6.2 Quality Gates
- Block deployments if CRITICAL leaks detected
- Configurable thresholds per project

### 6.3 Technical Debt Tracking
- Auto-create tech debt items for detected leaks
- Track fixes over time

### 6.4 GhostCrew Integration
- Include memory leak detection in security scans
- Resource exhaustion = DoS vulnerability

---

## 7. Implementation Phases

### Phase 1: Core Framework (Week 143)
- [ ] Base detector class
- [ ] Classic ASP detector (priority - FysioOne)
- [ ] API endpoints
- [ ] Basic reporting

### Phase 2: Additional Languages (Week 144)
- [ ] PHP detector (FRM project)
- [ ] VB.NET detector (future migrations)
- [ ] Java detector

### Phase 3: Integration (Week 145)
- [ ] Brown Paper integration
- [ ] Quality Gate integration
- [ ] Dashboard visualizations

---

## 8. Database Schema

```sql
CREATE TABLE resource_leak_scans (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    scan_date TIMESTAMP DEFAULT NOW(),
    total_files INTEGER,
    files_with_leaks INTEGER,
    critical_count INTEGER,
    high_count INTEGER,
    medium_count INTEGER,
    low_count INTEGER
);

CREATE TABLE resource_leak_findings (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES resource_leak_scans(id),
    file_path TEXT,
    line_number INTEGER,
    resource_type VARCHAR(50),
    variable_name VARCHAR(100),
    leak_pattern VARCHAR(50),
    severity VARCHAR(20),
    description TEXT,
    suggested_fix TEXT,
    fixed_at TIMESTAMP,
    fixed_by INTEGER REFERENCES users(id)
);
```

---

## 9. Wrapper Function Analysis (Cross-File .Close())

**Kritieke bevinding**: `.Close()` calls kunnen in andere bestanden gebeuren via helper functions!

### 9.1 Gevonden Wrapper Patterns in FysioOne

| Type | Locatie | Functie |
|------|---------|---------|
| Global | `include/functions_database.asp:218` | `TryCloseConnection(connection)` |
| Global | `include/functions.asp:215` | `TryDispose(obj)` |
| Local | 76 bestanden | `CloseAndDispose()` - **per bestand anders!** |

### 9.2 Analysis Strategie

```python
@dataclass
class WrapperFunction:
    """A cleanup helper function that wraps .Close() calls."""
    name: str
    file_path: str
    line_number: int
    closes_resources: List[ResourceType]  # What types does it close?
    parameter_names: List[str]  # Which parameters get closed?
    is_global: bool  # In include file = global

class WrapperFunctionAnalyzer:
    """Analyzes cleanup helper functions to understand what they close."""

    def find_wrapper_functions(self, source: str, file_path: str) -> List[WrapperFunction]:
        """Find all cleanup helper functions in a file."""
        patterns = [
            r'(?:Sub|Function)\s+(CloseAndDispose|TryDispose|TryCloseConnection|Cleanup)\s*\(([^)]*)\)',
            r'(?:Sub|Function)\s+(\w*(?:Close|Dispose|Cleanup)\w*)\s*\(([^)]*)\)',
        ]
        # Parse function body to see what .Close() calls are made
        pass

    def analyze_wrapper_body(self, function_body: str) -> Dict[str, List[str]]:
        """
        Analyze what a wrapper function closes.

        Returns mapping: parameter_name -> [close_operations]
        Example: {'Con': ['.Close()', 'Set = Nothing'], 'RS': ['.Close()']}
        """
        pass

    def resolve_wrapper_call(self, call: str, wrappers: List[WrapperFunction]) -> List[str]:
        """
        Given a wrapper call like 'Call TryCloseConnection(MasCon)',
        determine which resources are being closed.
        """
        pass
```

### 9.3 Include File Resolution

```python
class IncludeResolver:
    """Resolves include file dependencies for ASP/PHP."""

    def find_includes(self, file_path: str) -> List[str]:
        """
        Find all include statements in a file.

        ASP: <!-- #include file="..." --> or <!-- #include virtual="..." -->
        PHP: include, include_once, require, require_once
        """
        pass

    def build_include_tree(self, entry_file: str) -> Dict[str, List[str]]:
        """Build full include dependency tree."""
        pass

    def get_global_wrappers(self, include_tree: Dict) -> List[WrapperFunction]:
        """Get all wrapper functions available via includes."""
        pass
```

### 9.4 Updated Detection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Parse include statements → Build include tree               │
├─────────────────────────────────────────────────────────────────┤
│  2. Analyze include files → Extract global wrapper functions    │
├─────────────────────────────────────────────────────────────────┤
│  3. Analyze target file → Extract local wrapper functions       │
├─────────────────────────────────────────────────────────────────┤
│  4. Find resource OPEN operations                               │
├─────────────────────────────────────────────────────────────────┤
│  5. Find DIRECT .Close() calls                                  │
├─────────────────────────────────────────────────────────────────┤
│  6. Find WRAPPER calls → Resolve to actual close operations     │
├─────────────────────────────────────────────────────────────────┤
│  7. Calculate balance: Opens - (Direct closes + Wrapper closes) │
├─────────────────────────────────────────────────────────────────┤
│  8. Generate findings with accurate leak detection              │
└─────────────────────────────────────────────────────────────────┘
```

### 9.5 Example: Verkoop_update.asp Analysis

```
FILE: Verkoop_update.asp

OPENS:
- Line 54: Set Con = CreateCusCon()     → DATABASE_CONNECTION
- Line 55: Set MasCon = CreateCusCon()  → DATABASE_CONNECTION
- Line 57: Set RS = CreateRecordset()   → RECORDSET
- Line 58: Set MasRS = CreateRecordset() → RECORDSET

DIRECT CLOSES:
- (none found)

LOCAL WRAPPER (line 204):
Sub CloseAndDispose()
    Call TryCloseConnection(Con)  → Closes: Con
    Call TryDispose(RS)           → Closes: RS
End Sub

WRAPPER CALLS:
- Line 210: Call CloseAndDispose() → Closes Con, RS

FINAL BALANCE:
- Con:    OPEN(54) - CLOSE(210 via wrapper) = 0 ✓
- MasCon: OPEN(55) - NO CLOSE              = +1 LEAK!
- RS:     OPEN(57) - CLOSE(210 via wrapper) = 0 ✓
- MasRS:  OPEN(58) - NO CLOSE              = +1 LEAK!

RESULT: 2 leaks (MasCon, MasRS never closed)
```

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Detection accuracy | >90% |
| False positive rate | <5% |
| Analysis speed | <1s per file |
| Language coverage | 6+ languages |

---

## 11. Lessons Learned from Peer Review (FysioOne Audit 2026-01-06)

⚠️ **Kritieke bevindingen uit 2-ronde peer review met Codex GPT-5-codex**

### 11.1 Case Sensitivity in Pattern Matching

```python
# FOUT - VBScript/ASP is case-insensitive!
pattern = r'\.Close\(\)'  # Mist: rs.close(), RS.CLOSE()

# CORRECT - Altijd case-insensitive matching
pattern = r'(?i)\.close\s*\(\s*\)'

# In grep commands:
# FOUT:  grep "\.Close()" file.asp
# GOED:  grep -i "\.close" file.asp
```

**Implementatie in detector:**
```python
class BaseResourceLeakDetector:
    def compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        """Compile patterns with case-insensitive flag for relevant languages."""
        flags = re.IGNORECASE if self.is_case_insensitive_language() else 0
        return [re.compile(p, flags) for p in patterns]

    def is_case_insensitive_language(self) -> bool:
        """Override in subclass. VBScript, ASP, SQL are case-insensitive."""
        return False

class ClassicASPLeakDetector(BaseResourceLeakDetector):
    def is_case_insensitive_language(self) -> bool:
        return True  # VBScript is case-insensitive!
```

### 11.2 Set = Nothing ≠ .Close()

**Kritiek onderscheid voor ADO/COM objecten:**

| Operatie | Effect | Connection Pool | Memory |
|----------|--------|-----------------|--------|
| `obj.Close()` | Releases connection to pool | ✅ Released | ✅ Freed |
| `Set obj = Nothing` | Dereferences object | ❌ Connection stays open! | ⏳ Waits for GC |

```python
# In pattern matching - BEIDE nodig voor correcte cleanup
PROPER_CLEANUP_PATTERNS = {
    'full_cleanup': r'(\w+)\.Close\s*\(\s*\).*Set\s+\1\s*=\s*Nothing',
    'close_only': r'(\w+)\.Close\s*\(\s*\)',
    'nothing_only': r'Set\s+(\w+)\s*=\s*Nothing',  # INCOMPLETE cleanup!
}

class LeakSeverityCalculator:
    def calculate_severity(self, has_close: bool, has_nothing: bool) -> str:
        if has_close and has_nothing:
            return "CLEAN"
        elif has_close:
            return "LOW"  # Memory may leak but connection released
        elif has_nothing:
            return "HIGH"  # Connection leak! Pool exhaustion risk
        else:
            return "CRITICAL"  # Nothing at all
```

### 11.3 Recordset Reopen Pattern Detection

**Nieuw leak pattern ontdekt:**
```vbscript
' LEAK PATTERN: Open-Close-Open zonder finale Close
RS.Open(sql1, Con)     ' Line 16
RS.Close()             ' Line 20 - First RS closed ✓
RS.Open(sql2, Con)     ' Line 25 - RS REOPENED!
' NO SECOND CLOSE!     ' ❌ RS leaks after line 25
```

```python
class ReopenPatternDetector:
    """Detect resources that are closed then reopened without final close."""

    def detect_reopen_leaks(self, operations: List[ResourceOperation]) -> List[LeakFinding]:
        findings = []
        for var_name in self.get_unique_variables(operations):
            ops = self.get_operations_for_var(operations, var_name)

            # Track state: CREATED -> CLOSED -> REOPENED -> ?
            state = "CREATED"
            reopen_line = None

            for op in sorted(ops, key=lambda x: x.line_number):
                if op.operation_type == 'close':
                    state = "CLOSED"
                elif op.operation_type == 'open' and state == "CLOSED":
                    state = "REOPENED"
                    reopen_line = op.line_number

            # If final state is REOPENED, we have a leak
            if state == "REOPENED":
                findings.append(LeakFinding(
                    variable_name=var_name,
                    leak_pattern=LeakPatternType.REOPEN_LEAK,
                    line_number=reopen_line,
                    description=f"{var_name} reopened at line {reopen_line} but never closed again",
                    severity="HIGH"
                ))

        return findings
```

### 11.4 Connection Leaks vs Recordset Leaks

**Prioriteit verschil:**

| Type | Pool Impact | Memory Impact | Severity |
|------|-------------|---------------|----------|
| Connection leak | Pool exhaustion (crashes) | Medium | **CRITICAL** |
| Recordset leak | None (no pooling) | High per record | **HIGH** |
| COM Object leak | None | Very High | **HIGH** |

```python
class LeakPrioritizer:
    SEVERITY_WEIGHTS = {
        ResourceType.DATABASE_CONNECTION: 100,  # Highest priority
        ResourceType.TRANSACTION: 90,
        ResourceType.HTTP_CONNECTION: 80,
        ResourceType.RECORDSET: 70,
        ResourceType.FILE_HANDLE: 60,
        ResourceType.COM_OBJECT: 50,
        ResourceType.STREAM: 40,
    }

    def prioritize_findings(self, findings: List[LeakFinding]) -> List[LeakFinding]:
        return sorted(findings,
                     key=lambda f: self.SEVERITY_WEIGHTS.get(f.resource_type, 0),
                     reverse=True)
```

### 11.5 Peer Review als Kwaliteitsmaatregel

**Aanbevolen workflow voor audits:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Initial Audit (Claude/Primary LLM)                      │
│     - Run detection patterns                                │
│     - Generate findings                                     │
├─────────────────────────────────────────────────────────────┤
│  2. Peer Review Round 1 (Codex/Secondary LLM)              │
│     - Challenge all findings                                │
│     - Verify with actual grep -i commands                   │
│     - Find false positives/negatives                        │
├─────────────────────────────────────────────────────────────┤
│  3. Counter-Challenge (Primary LLM)                         │
│     - Defend valid findings with evidence                   │
│     - Accept valid corrections                              │
├─────────────────────────────────────────────────────────────┤
│  4. Peer Review Round 2 (Secondary LLM)                    │
│     - Verify corrections applied                            │
│     - Check for remaining issues                            │
├─────────────────────────────────────────────────────────────┤
│  5. Final Verification                                      │
│     - "AUDIT VERIFIED - NO FURTHER ISSUES"                  │
│     - Document accuracy metrics                             │
└─────────────────────────────────────────────────────────────┘
```

**API endpoint voor peer review:**
```python
@router.post("/peer-review/{scan_id}")
async def request_peer_review(
    scan_id: int,
    reviewer_model: str = "gpt-5-codex",
    include_source_verification: bool = True
) -> PeerReviewResult:
    """Request peer review of scan findings from secondary LLM."""
    pass
```

---

## 12. Structural Fix Approach (Algemeen)

### 12.1 Fix Priority Matrix

```
┌────────────────────────────────────────────────────────────────────┐
│                    RESOURCE LEAK FIX PRIORITIES                    │
├──────────────┬─────────────────┬───────────────┬──────────────────┤
│   Severity   │   Fix Timeline  │  Verification │   Gate Block     │
├──────────────┼─────────────────┼───────────────┼──────────────────┤
│ CRITICAL++   │ Immediate       │ Per-commit    │ Deploy blocked   │
│ (Loop leaks) │ (same day)      │               │                  │
├──────────────┼─────────────────┼───────────────┼──────────────────┤
│ CRITICAL     │ This sprint     │ Daily scan    │ Deploy blocked   │
│ (Zero close) │ (< 1 week)      │               │                  │
├──────────────┼─────────────────┼───────────────┼──────────────────┤
│ HIGH         │ Next sprint     │ Weekly scan   │ Warning only     │
│ (Partial)    │ (< 2 weeks)     │               │                  │
├──────────────┼─────────────────┼───────────────┼──────────────────┤
│ MEDIUM       │ Within month    │ Monthly scan  │ No block         │
│              │                 │               │                  │
└──────────────┴─────────────────┴───────────────┴──────────────────┘
```

### 12.2 Standardized Cleanup Pattern (Template)

```vbscript
'================================================================
' STANDARD CLEANUP PATTERN FOR ASP/VBScript
' Copy this template to every ASP file
'================================================================

Sub CleanupAllResources()
    On Error Resume Next

    ' Close ALL recordsets first (before connections!)
    If IsObject(RS) Then If Not RS Is Nothing Then RS.Close : Set RS = Nothing
    If IsObject(RS1) Then If Not RS1 Is Nothing Then RS1.Close : Set RS1 = Nothing
    If IsObject(MasRS) Then If Not MasRS Is Nothing Then MasRS.Close : Set MasRS = Nothing

    ' Then close connections
    If IsObject(Con) Then If Not Con Is Nothing Then Con.Close : Set Con = Nothing
    If IsObject(MasCon) Then If Not MasCon Is Nothing Then MasCon.Close : Set MasCon = Nothing

    On Error Goto 0
End Sub

' USAGE:
' 1. Call at END of every page
' 2. Call BEFORE every Response.End
' 3. Call BEFORE every Response.Redirect
```

### 12.3 Safe Exit Helpers (Global Include)

```vbscript
'================================================================
' include/SafeExit.asp - Add to ALL pages via include
'================================================================

Sub SafeEnd()
    Call CleanupAllResources()
    Response.End
End Sub

Sub SafeRedirect(url)
    Call CleanupAllResources()
    Response.Redirect url
End Sub

Function SafeExecute(sql, connection)
    On Error Resume Next
    Set SafeExecute = connection.Execute(sql)
    If Err.Number <> 0 Then
        Call LogError("SQL Error: " & Err.Description & " in: " & sql)
        Set SafeExecute = Nothing
    End If
    On Error Goto 0
End Function
```

### 12.4 Automated Verification Checklist

```python
class StructuralFixVerifier:
    """Verify that structural fixes are correctly applied."""

    REQUIRED_PATTERNS = {
        'cleanup_sub': r'Sub\s+CleanupAllResources\s*\(\s*\)',
        'cleanup_call_end': r'Call\s+CleanupAllResources.*Response\.End',
        'cleanup_call_redirect': r'Call\s+CleanupAllResources.*Response\.Redirect',
        'safe_exit_include': r'#include.*SafeExit\.asp',
    }

    def verify_file(self, file_path: str) -> VerificationResult:
        """Check if file has proper structural fixes."""
        source = self.read_file(file_path)

        checks = {
            'has_cleanup_sub': bool(re.search(self.REQUIRED_PATTERNS['cleanup_sub'], source, re.I)),
            'cleanup_before_end': self._check_cleanup_before_exits(source, 'Response.End'),
            'cleanup_before_redirect': self._check_cleanup_before_exits(source, 'Response.Redirect'),
            'uses_safe_helpers': bool(re.search(r'SafeEnd|SafeRedirect', source, re.I)),
            'no_orphan_exits': self._check_no_orphan_exits(source),
        }

        return VerificationResult(
            file_path=file_path,
            passed=all(checks.values()),
            checks=checks
        )

    def _check_no_orphan_exits(self, source: str) -> bool:
        """Check that no Response.End/Redirect exists without cleanup."""
        # Find all exits
        exits = re.findall(r'Response\.(End|Redirect)', source, re.I)
        # Find all safe exits
        safe_exits = re.findall(r'(SafeEnd|SafeRedirect|CleanupAllResources)', source, re.I)
        # Should have at least as many safe patterns as exits
        return len(safe_exits) >= len(exits)
```

### 12.5 CI/CD Quality Gate Integration

```yaml
# .github/workflows/resource-leak-check.yml
name: Resource Leak Detection

on:
  pull_request:
    paths:
      - '**.asp'
      - '**.php'
      - '**.vb'

jobs:
  leak-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Leak Detection
        run: |
          curl -X POST "${{ secrets.MARQED_API }}/api/resource-leaks/analyze" \
            -H "Authorization: Bearer ${{ secrets.MARQED_TOKEN }}" \
            -d '{"project_id": ${{ vars.PROJECT_ID }}, "severity_threshold": "HIGH"}'

      - name: Check Results
        run: |
          CRITICAL=$(curl -s "${{ secrets.MARQED_API }}/api/resource-leaks/summary/${{ vars.PROJECT_ID }}" | jq '.critical_leaks')
          if [ "$CRITICAL" -gt 0 ]; then
            echo "::error::CRITICAL resource leaks detected! Blocking merge."
            exit 1
          fi
```

### 12.6 Ongoing Monitoring Dashboard

```python
@router.get("/dashboard/leak-trends/{project_id}")
async def get_leak_trends(project_id: int, days: int = 30) -> dict:
    """Track leak trends over time to ensure fixes stick."""
    return {
        "project_id": project_id,
        "trend": [
            {"date": "2026-01-01", "critical": 5, "high": 10, "medium": 15},
            {"date": "2026-01-08", "critical": 3, "high": 8, "medium": 12},
            {"date": "2026-01-15", "critical": 1, "high": 5, "medium": 10},
            # ...
        ],
        "fix_velocity": 2.5,  # Leaks fixed per week
        "regression_count": 0,  # New leaks introduced
        "estimated_zero_date": "2026-02-15",  # When all fixed
    }
```

---

## 13. Prevention Checklist (Post-Fix)

### Voor Developers

- [ ] Gebruik `SafeEnd()` ipv `Response.End`
- [ ] Gebruik `SafeRedirect(url)` ipv `Response.Redirect`
- [ ] Voeg `CleanupAllResources()` toe aan einde van elke pagina
- [ ] Sluit recordsets VOOR connections
- [ ] Gebruik `grep -i` voor case-insensitive checks

### Voor Code Review

- [ ] Check: Elk `CreateRecordset` heeft matching `.Close()`
- [ ] Check: Elk `CreateCusCon/CreateCon` heeft matching `.Close()`
- [ ] Check: Geen `Response.End` zonder voorafgaande cleanup
- [ ] Check: Loops hebben geen resource creatie zonder cleanup
- [ ] Check: `Set = Nothing` ALLEEN na `.Close()`

### Voor CI/CD

- [ ] Pre-commit hook: Leak detection scan
- [ ] PR check: Block on CRITICAL leaks
- [ ] Weekly scan: Report on trends
- [ ] Monthly audit: Full peer review

---

*Design by Claude Opus 4.5 - Resource Leak Detection Framework*
*Updated: 2026-01-06 with Peer Review Learnings*
