# Fase 42: Advanced False Negative Detection

**Status:** PLANNED
**Priority:** HIGH
**Week:** KW6-KW7 [w159-160] (Q1 2026, na Fase 41 ✅)
**Dependencies:** Fase 41 (Injection Scanners + FN Remediation) ✅ COMPLETE
**ROI:** 8.5 (pushes detection from 95% → 98%+)

---

## Overview

Na Fase 41 blijft ~5% false negatives over. Deze fase richt zich op het detecteren van de meest hardnekkige patterns die regex-based scanners missen.

### Target Categories

| Category | Current Miss Rate | Target Miss Rate | Approach |
|----------|-------------------|------------------|----------|
| Complex Data Flow | 2.0% | 0.5% | AST-based taint tracking |
| Dynamic Language Features | 1.25% | 0.5% | Heuristic detection |
| Framework-Specific | 1.0% | 0.2% | Framework plugins |
| Obfuscation | 0.5% | 0.3% | Entropy + deobfuscation |
| Novel Patterns | 0.25% | 0.25% | Accept as limit |

**Goal:** Reduce overall FN rate from **<5%** to **<2%**

---

## Category 1: Complex Data Flow (40% of remaining FN)

### Problem Statement

```python
# Multi-step data flow - often missed by regex
def get_user_input():
    return request.args.get('query')

def process_data(data):
    return data.upper()  # Transform but still tainted

def execute_query():
    user_data = get_user_input()      # Step 1: Source
    processed = process_data(user_data)  # Step 2: Transform
    cursor.execute(f"SELECT * FROM t WHERE x='{processed}'")  # Step 3: Sink
```

Current scanners miss this because the taint flows through multiple functions.

### Solution: AST-Based Taint Tracking

```python
# adapters/ast_taint_tracker.py

"""
AST-Based Taint Tracking for Cross-Function Data Flow

Uses Python's ast module (and equivalents for other languages) to:
1. Build a call graph
2. Track data flow from sources to sinks
3. Propagate taint through function calls
"""

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from pathlib import Path


@dataclass
class TaintSource:
    """A source of tainted data."""
    variable: str
    function: str
    line: int
    source_type: str  # 'request', 'input', 'argv', etc.


@dataclass
class TaintSink:
    """A dangerous sink where tainted data shouldn't flow."""
    function_call: str
    line: int
    cwe: str


@dataclass
class FunctionSignature:
    """Track function parameters and return values."""
    name: str
    parameters: List[str]
    returns_tainted: bool = False
    tainted_params: Set[int] = field(default_factory=set)  # Indices of tainted params


class ASTTaintTracker:
    """
    Tracks taint flow through AST analysis.

    Supports:
    - Python (ast module)
    - JavaScript/TypeScript (via tree-sitter or esprima bindings)
    - Java (via javalang)
    """

    # Known taint sources by language
    SOURCES = {
        "python": [
            ("request.args.get", "request"),
            ("request.form.get", "request"),
            ("request.json", "request"),
            ("input(", "stdin"),
            ("sys.argv", "argv"),
            ("os.environ", "env"),
        ],
        "javascript": [
            ("req.body", "request"),
            ("req.query", "request"),
            ("req.params", "request"),
            ("process.argv", "argv"),
            ("process.env", "env"),
        ],
    }

    # Known taint sinks (CWE mapping)
    SINKS = {
        "python": [
            ("cursor.execute", "CWE-89"),
            ("os.system", "CWE-78"),
            ("subprocess.call", "CWE-78"),
            ("eval(", "CWE-94"),
            ("exec(", "CWE-94"),
            ("open(", "CWE-22"),
            ("pickle.loads", "CWE-502"),
        ],
        "javascript": [
            ("eval(", "CWE-94"),
            (".innerHTML", "CWE-79"),
            ("child_process.exec", "CWE-78"),
            ("fs.readFile", "CWE-22"),
        ],
    }

    def __init__(self, language: str):
        self.language = language
        self.call_graph: Dict[str, List[str]] = {}
        self.function_sigs: Dict[str, FunctionSignature] = {}
        self.taint_map: Dict[str, Set[str]] = {}  # var -> set of taint sources

    async def analyze_file(self, file_path: Path, content: str) -> List[Finding]:
        """Analyze a file for cross-function taint flow."""
        findings = []

        if self.language == "python":
            findings = await self._analyze_python(content, file_path)
        elif self.language in ("javascript", "typescript"):
            findings = await self._analyze_javascript(content, file_path)

        return findings

    async def _analyze_python(self, content: str, file_path: Path) -> List[Finding]:
        """Analyze Python code using ast module."""
        findings = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        # Phase 1: Build function signatures and call graph
        self._build_call_graph_python(tree)

        # Phase 2: Find taint sources
        sources = self._find_sources_python(tree)

        # Phase 3: Propagate taint through call graph
        self._propagate_taint(sources)

        # Phase 4: Check if tainted data reaches sinks
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                sink_match = self._is_sink_python(node)
                if sink_match:
                    # Check if any argument is tainted
                    for arg in node.args:
                        arg_name = self._get_name(arg)
                        if arg_name and self._is_tainted(arg_name):
                            findings.append(Finding(
                                rule_id=f"AST-TAINT-{sink_match[1]}",
                                title=f"Tainted data flows to {sink_match[0]}",
                                description=f"Data from {self.taint_map.get(arg_name, 'unknown source')} "
                                           f"flows to dangerous sink via cross-function data flow",
                                severity=Severity.HIGH,
                                cwe_ids=[sink_match[1]],
                                file_path=file_path,
                                line_number=node.lineno,
                                evidence=ast.get_source_segment(content, node) or "",
                                scanner_type=ScannerType.AST_TAINT,
                            ))

        return findings

    def _build_call_graph_python(self, tree: ast.AST):
        """Build call graph from Python AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                params = [arg.arg for arg in node.args.args]
                self.function_sigs[func_name] = FunctionSignature(
                    name=func_name,
                    parameters=params
                )

                # Find calls within this function
                calls = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = self._get_call_name(child)
                        if call_name:
                            calls.append(call_name)

                self.call_graph[func_name] = calls

    def _propagate_taint(self, sources: List[TaintSource]):
        """Propagate taint through the call graph."""
        # Initialize taint from sources
        for source in sources:
            if source.variable not in self.taint_map:
                self.taint_map[source.variable] = set()
            self.taint_map[source.variable].add(source.source_type)

        # Iteratively propagate until fixed point
        changed = True
        iterations = 0
        max_iterations = 100  # Prevent infinite loops

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for func_name, sig in self.function_sigs.items():
                # If any parameter is tainted, mark return as potentially tainted
                for i, param in enumerate(sig.parameters):
                    if self._is_tainted(param) and not sig.returns_tainted:
                        sig.returns_tainted = True
                        sig.tainted_params.add(i)
                        changed = True

                # Propagate to callers
                for caller, callees in self.call_graph.items():
                    if func_name in callees and sig.returns_tainted:
                        # Mark the result variable as tainted
                        # (simplified - would need assignment tracking)
                        pass

    def _is_tainted(self, var_name: str) -> bool:
        """Check if a variable is tainted."""
        return var_name in self.taint_map and len(self.taint_map[var_name]) > 0
```

### Implementation Plan for Category 1

| Week | Task | Deliverable |
|------|------|-------------|
| 169 | Python AST taint tracker | `ast_taint_tracker.py` |
| 170 | JavaScript/TS taint tracker | tree-sitter integration |
| 171 | Java taint tracker | javalang integration |
| 172 | Cross-function propagation | Call graph analysis |

**Expected Improvement:** 2.0% → 0.5% (75% reduction)

---

## Category 2: Dynamic Language Features (25% of remaining FN)

### Problem Statement

```javascript
// Dynamic property access - hard to track statically
const prop = getUserInput();  // e.g., "innerHTML"
element[prop] = data;  // Could be XSS if prop is "innerHTML"

// Computed function calls
const func = getFunction();  // e.g., "eval"
window[func](userInput);  // Could be code injection
```

### Solution: Heuristic Detection

```python
# adapters/dynamic_feature_detector.py

"""
Detects dangerous use of dynamic language features.

Strategy: Flag patterns that COULD be dangerous, with lower confidence.
User review required, but catches what regex misses.
"""

class DynamicFeatureDetector:
    """
    Detects potentially dangerous dynamic language features.

    Flags:
    - Dynamic property access on DOM elements
    - Computed function calls with user input
    - Reflection/meta-programming with external data
    - Dynamic imports/requires
    """

    scanner_type = ScannerType.DYNAMIC_ANALYSIS

    # Patterns for dynamic feature detection
    DYNAMIC_PATTERNS = {
        "javascript": [
            # Dynamic property access that could be innerHTML/outerHTML
            DynamicRule(
                id="DYN-JS-001",
                title="Dynamic property access on DOM element",
                pattern=r'(?:element|el|node|dom)\s*\[\s*(\w+)\s*\]\s*=',
                context_check=lambda ctx: "innerHTML" not in ctx and "outerHTML" not in ctx,
                cwe="CWE-79",
                severity=Severity.MEDIUM,  # Lower confidence
                description="Dynamic property access could set innerHTML if variable contains 'innerHTML'",
            ),

            # Computed function call
            DynamicRule(
                id="DYN-JS-002",
                title="Computed function call",
                pattern=r'(?:window|global|this)\s*\[\s*(\w+)\s*\]\s*\(',
                cwe="CWE-94",
                severity=Severity.MEDIUM,
            ),

            # Dynamic require/import
            DynamicRule(
                id="DYN-JS-003",
                title="Dynamic module loading",
                pattern=r'(?:require|import)\s*\(\s*(?![\'"]).+\)',
                cwe="CWE-94",
                severity=Severity.LOW,
            ),
        ],

        "python": [
            # getattr with user input
            DynamicRule(
                id="DYN-PY-001",
                title="Dynamic attribute access",
                pattern=r'getattr\s*\(\s*\w+\s*,\s*(?:request|input|user)',
                cwe="CWE-94",
                severity=Severity.HIGH,
            ),

            # __import__ with variable
            DynamicRule(
                id="DYN-PY-002",
                title="Dynamic import",
                pattern=r'__import__\s*\(\s*(?![\'"]).+\)',
                cwe="CWE-94",
                severity=Severity.MEDIUM,
            ),

            # globals()/locals() access
            DynamicRule(
                id="DYN-PY-003",
                title="Dynamic globals/locals access",
                pattern=r'(?:globals|locals)\s*\(\s*\)\s*\[',
                cwe="CWE-94",
                severity=Severity.MEDIUM,
            ),
        ],

        "java": [
            # Reflection with user input
            DynamicRule(
                id="DYN-JAVA-001",
                title="Reflection with external input",
                pattern=r'Class\.forName\s*\(\s*(?:request|input|user)',
                cwe="CWE-470",
                severity=Severity.HIGH,
            ),

            # Method.invoke with variable
            DynamicRule(
                id="DYN-JAVA-002",
                title="Dynamic method invocation",
                pattern=r'\.invoke\s*\(\s*\w+\s*,.*(?:request|input)',
                cwe="CWE-470",
                severity=Severity.HIGH,
            ),
        ],
    }
```

### Implementation Plan for Category 2

| Week | Task | Deliverable |
|------|------|-------------|
| 170 | JS/TS dynamic patterns | 15 heuristic rules |
| 171 | Python dynamic patterns | 10 heuristic rules |
| 172 | Java reflection patterns | 8 heuristic rules |

**Expected Improvement:** 1.25% → 0.5% (60% reduction)

---

## Category 3: Framework-Specific Patterns (20% of remaining FN)

### Problem Statement

```python
# Django ORM - safe? depends on usage
User.objects.raw(f"SELECT * FROM users WHERE name='{name}'")  # UNSAFE
User.objects.filter(name=name)  # SAFE

# SQLAlchemy - many ways to be unsafe
session.execute(text(f"SELECT * FROM users WHERE id={user_id}"))  # UNSAFE

# Express.js template engines
res.render('template', { data: userInput });  # May or may not be safe
```

### Solution: Framework Plugins

```python
# adapters/framework_plugins/

"""
Framework-specific security scanners.

Each plugin understands:
1. Framework-specific sources (e.g., Django request.GET)
2. Framework-specific sinks (e.g., Django ORM raw())
3. Framework-specific sanitizers (e.g., Django mark_safe)
"""

# --- Django Plugin ---
class DjangoSecurityPlugin:
    """Django-specific security patterns."""

    RULES = [
        # Django ORM unsafe patterns
        FrameworkRule(
            id="DJANGO-001",
            title="Django raw SQL with user input",
            pattern=r'\.(?:raw|extra)\s*\(\s*(?:f["\']|["\'].*%|.*\.format)',
            cwe="CWE-89",
            framework="django",
            safe_alternative="Use QuerySet filter/exclude with named parameters",
        ),

        # Django mark_safe misuse
        FrameworkRule(
            id="DJANGO-002",
            title="mark_safe with user input",
            pattern=r'mark_safe\s*\(\s*(?:request|user|input)',
            cwe="CWE-79",
            framework="django",
        ),

        # Django template autoescape disabled
        FrameworkRule(
            id="DJANGO-003",
            title="Autoescape disabled in template",
            pattern=r'\{%\s*autoescape\s+off\s*%\}',
            cwe="CWE-79",
            framework="django",
            file_pattern="*.html",
        ),
    ]


# --- Flask Plugin ---
class FlaskSecurityPlugin:
    """Flask-specific security patterns."""

    RULES = [
        # Flask Markup without escaping
        FrameworkRule(
            id="FLASK-001",
            title="Markup with user input",
            pattern=r'Markup\s*\(\s*(?:request|user|input|f["\'])',
            cwe="CWE-79",
            framework="flask",
        ),

        # render_template_string
        FrameworkRule(
            id="FLASK-002",
            title="render_template_string with user input",
            pattern=r'render_template_string\s*\(\s*(?:request|user|input|f["\'])',
            cwe="CWE-1336",
            framework="flask",
        ),
    ]


# --- Express.js Plugin ---
class ExpressSecurityPlugin:
    """Express.js-specific security patterns."""

    RULES = [
        # res.send without sanitization
        FrameworkRule(
            id="EXPRESS-001",
            title="Direct user input in response",
            pattern=r'res\.send\s*\(\s*req\.(?:body|query|params)',
            cwe="CWE-79",
            framework="express",
        ),

        # SQL in Sequelize literal
        FrameworkRule(
            id="EXPRESS-002",
            title="Sequelize literal with user input",
            pattern=r'Sequelize\.literal\s*\(\s*[`"\'].*\$\{',
            cwe="CWE-89",
            framework="sequelize",
        ),
    ]


# --- Spring Boot Plugin ---
class SpringSecurityPlugin:
    """Spring Boot-specific security patterns."""

    RULES = [
        # JdbcTemplate with string concat
        FrameworkRule(
            id="SPRING-001",
            title="JdbcTemplate with string concatenation",
            pattern=r'jdbcTemplate\.(?:query|update)\s*\(\s*["\'].*\+',
            cwe="CWE-89",
            framework="spring",
        ),

        # @ResponseBody without encoding
        FrameworkRule(
            id="SPRING-002",
            title="ResponseBody returns user input",
            pattern=r'@ResponseBody.*return.*(?:request|input)',
            cwe="CWE-79",
            framework="spring",
        ),
    ]


# --- Framework Plugin Registry ---
FRAMEWORK_PLUGINS = {
    "django": DjangoSecurityPlugin,
    "flask": FlaskSecurityPlugin,
    "express": ExpressSecurityPlugin,
    "spring": SpringSecurityPlugin,
    "rails": RailsSecurityPlugin,
    "laravel": LaravelSecurityPlugin,
    "asp.net": AspNetSecurityPlugin,
}


class FrameworkDetector:
    """Detects which frameworks are used in a project."""

    FRAMEWORK_INDICATORS = {
        "django": ["django", "settings.py", "urls.py", "INSTALLED_APPS"],
        "flask": ["flask", "Flask(__name__)", "@app.route"],
        "express": ["express", "app.use(", "app.get(", "app.post("],
        "spring": ["@SpringBootApplication", "@RestController", "@Autowired"],
        "rails": ["Rails.application", "ActiveRecord", "ActionController"],
        "laravel": ["Illuminate\\", "artisan", "Laravel"],
    }

    def detect_frameworks(self, project_path: Path) -> Set[str]:
        """Detect which frameworks are used in the project."""
        detected = set()
        # Implementation: scan package files and source code
        return detected
```

### Supported Frameworks (Initial)

| Framework | Language | Plugin Rules | Priority |
|-----------|----------|--------------|----------|
| Django | Python | 15 | HIGH |
| Flask | Python | 10 | HIGH |
| Express | JavaScript | 12 | HIGH |
| Spring Boot | Java | 15 | HIGH |
| Rails | Ruby | 10 | MEDIUM |
| Laravel | PHP | 12 | MEDIUM |
| ASP.NET | C# | 10 | MEDIUM |

### Implementation Plan for Category 3

| Week | Task | Deliverable |
|------|------|-------------|
| 173 | Django + Flask plugins | 25 rules |
| 174 | Express + Spring plugins | 27 rules |
| 175 | Rails + Laravel + ASP.NET plugins | 32 rules |
| 176 | Framework auto-detection | `FrameworkDetector` |

**Expected Improvement:** 1.0% → 0.2% (80% reduction)

---

## Category 4: Obfuscation Detection (10% of remaining FN)

### Problem Statement

```javascript
// String obfuscation
const cmd = 'ev' + 'al';
window[cmd](userInput);  // Obfuscated eval

// Encoding tricks
const encoded = atob('ZXZhbA==');  // "eval"
window[encoded](data);

// Unicode escaping
const fn = '\u0065\u0076\u0061\u006c';  // "eval"
```

### Solution: Deobfuscation + Entropy Analysis

```python
# adapters/obfuscation_detector.py

"""
Detects obfuscated code patterns that might hide vulnerabilities.

Approaches:
1. String concatenation that builds dangerous function names
2. Base64/hex encoded strings that decode to dangerous patterns
3. Unicode escape sequences
4. High entropy variable names (possible minified code)
5. Unusual control flow patterns
"""

import base64
import re
from typing import List, Tuple


class ObfuscationDetector:
    """Detects potential code obfuscation hiding vulnerabilities."""

    scanner_type = ScannerType.OBFUSCATION

    # Dangerous function names to check for
    DANGEROUS_FUNCTIONS = {
        "eval", "exec", "system", "popen", "spawn",
        "innerHTML", "outerHTML", "write", "writeln",
        "Function", "setTimeout", "setInterval",
        "execSync", "execFile", "fork",
    }

    RULES = [
        # String concatenation building function names
        ObfuscationRule(
            id="OBF-001",
            title="String concatenation may build dangerous function",
            pattern=r'[\'"][a-z]{2,4}[\'"]\s*\+\s*[\'"][a-z]{2,4}[\'"]',
            check_func="_check_concat_to_dangerous",
        ),

        # Base64 encoded dangerous strings
        ObfuscationRule(
            id="OBF-002",
            title="Base64 may decode to dangerous function",
            pattern=r'(?:atob|base64\.b64decode|Base64\.decode)\s*\(\s*[\'"]([A-Za-z0-9+/=]+)[\'"]',
            check_func="_check_base64_dangerous",
        ),

        # Unicode escapes
        ObfuscationRule(
            id="OBF-003",
            title="Unicode escapes may hide dangerous code",
            pattern=r'\\u[0-9a-fA-F]{4}(?:\\u[0-9a-fA-F]{4})+',
            check_func="_check_unicode_dangerous",
        ),

        # Hex encoded strings
        ObfuscationRule(
            id="OBF-004",
            title="Hex string may hide dangerous code",
            pattern=r'\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2})+',
            check_func="_check_hex_dangerous",
        ),

        # High entropy variable names
        ObfuscationRule(
            id="OBF-005",
            title="High entropy names suggest obfuscation",
            pattern=r'\b[a-zA-Z_][a-zA-Z0-9_]{10,}\b',
            check_func="_check_entropy",
            min_entropy=4.0,
        ),
    ]

    def _check_concat_to_dangerous(self, match: re.Match, content: str) -> bool:
        """Check if string concatenation results in dangerous function."""
        # Extract the concatenated parts
        line = self._get_line(content, match.start())
        # Try to evaluate the concatenation
        parts = re.findall(r'[\'"]([^\'"]+)[\'"]', line)
        result = ''.join(parts)
        return result.lower() in {f.lower() for f in self.DANGEROUS_FUNCTIONS}

    def _check_base64_dangerous(self, match: re.Match, content: str) -> bool:
        """Check if Base64 decodes to dangerous string."""
        try:
            encoded = match.group(1)
            decoded = base64.b64decode(encoded).decode('utf-8', errors='ignore')
            return decoded.lower() in {f.lower() for f in self.DANGEROUS_FUNCTIONS}
        except:
            return False

    def _check_unicode_dangerous(self, match: re.Match, content: str) -> bool:
        """Check if Unicode escapes form dangerous function."""
        try:
            escaped = match.group(0)
            decoded = escaped.encode().decode('unicode_escape')
            return decoded.lower() in {f.lower() for f in self.DANGEROUS_FUNCTIONS}
        except:
            return False

    def _calculate_entropy(self, s: str) -> float:
        """Calculate Shannon entropy of a string."""
        import math
        from collections import Counter

        if not s:
            return 0

        freq = Counter(s)
        length = len(s)
        entropy = -sum(
            (count/length) * math.log2(count/length)
            for count in freq.values()
        )
        return entropy
```

### Implementation Plan for Category 4

| Week | Task | Deliverable |
|------|------|-------------|
| 175 | String deobfuscation | Concat, Base64, Unicode, Hex |
| 176 | Entropy analysis | Minification detection |

**Expected Improvement:** 0.5% → 0.3% (40% reduction)

---

## Category 5: Novel Patterns (5% of remaining FN)

### Reality Check

**Novel patterns (zero-days, new attack vectors) cannot be detected by static rules.**

This 0.25% will always remain as a fundamental limit of pattern-based detection.

### Mitigation Strategies

1. **Regular Rule Updates**
   - Monthly review of new CVEs and attack techniques
   - Community contribution for new patterns

2. **ML-Based Anomaly Detection** (Future - Fase 50+)
   - Train on known-good code to detect anomalies
   - Semantic similarity to known vulnerability patterns

3. **Defense in Depth**
   - Runtime protection (WAF, RASP)
   - Security testing in CI/CD
   - Bug bounty programs

---

## Complete Implementation Timeline

```
KW6 [w159]: AST Taint Tracker (Python) + AST Taint Tracker (JS/TS)
            Dynamic Patterns (JS) + Dynamic Patterns (Python)
KW7 [w160]: AST Taint Tracker (Java) + Call Graph Analysis + Dynamic Patterns (Java)
            Framework Plugins (Django, Flask, Express, Spring)
            Rails + Laravel + ASP.NET + Obfuscation + Integration
```

---

## Architecture

### New Components

```
backend/app/services/security_scanner/
├── adapters/
│   ├── ast_taint_tracker.py          # Cross-function taint analysis
│   ├── dynamic_feature_detector.py   # Dynamic language heuristics
│   ├── obfuscation_detector.py       # Deobfuscation + entropy
│   └── framework_plugins/
│       ├── __init__.py
│       ├── base.py
│       ├── django_plugin.py
│       ├── flask_plugin.py
│       ├── express_plugin.py
│       ├── spring_plugin.py
│       ├── rails_plugin.py
│       ├── laravel_plugin.py
│       └── aspnet_plugin.py
├── models/
│   └── findings.py                    # Add new ScannerTypes
└── orchestrator.py                    # Register new scanners
```

### New ScannerTypes

```python
class ScannerType(str, Enum):
    # ... existing ...

    # Fase 42: Advanced FN Detection
    AST_TAINT = "ast_taint"           # Cross-function taint tracking
    DYNAMIC_ANALYSIS = "dynamic"       # Dynamic language features
    FRAMEWORK = "framework"            # Framework-specific patterns
    OBFUSCATION = "obfuscation"       # Deobfuscation detection
```

---

## Expected Results

### False Negative Reduction

| Phase | Overall FN Rate | Improvement |
|-------|-----------------|-------------|
| After Fase 41 | <5% | Baseline |
| + AST Taint | <4% | -1% |
| + Dynamic Features | <3.5% | -0.5% |
| + Framework Plugins | <2.5% | -1% |
| + Obfuscation | <2% | -0.5% |
| **Final** | **<2%** | **-3%** |

### Detection Capability

```
┌─────────────────────────────────────────────────────────────┐
│              DETECTION CAPABILITY AFTER FASE 42              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  100% ┬──────────────────────────────────────────────────   │
│       │  ████████████████████████████ Theoretical Max       │
│   98% ┼──────────────────────────────────────────────────   │
│       │  ██████████████████████████ After Fase 42 (~98%)    │
│   95% ┼──────────────────────────────────────────────────   │
│       │  ████████████████████ After Fase 41 (~95%)          │
│   90% ┼──────────────────────────────────────────────────   │
│       │                                                      │
│       └──────────────────────────────────────────────────   │
│         Fase 41    + AST     + Plugins   + Obfusc   Max     │
│                   Taint     (Framework)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Overall FN Rate | **<2%** |
| Cross-function Detection | >75% of data flow FN eliminated |
| Framework Coverage | 7 major frameworks |
| Obfuscation Detection | >40% of obfuscated patterns |
| New Detection Rules | ~150 |
| Unit Tests | >200 |

---

## Dependencies

- **Fase 41:** Injection Scanners (must be complete)
- **Python:** `ast` module (standard library)
- **JavaScript:** `tree-sitter` or `esprima` for AST parsing
- **Java:** `javalang` for Java AST parsing

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| AST parsing errors | Medium | Low | Graceful fallback to regex |
| False positives from heuristics | Medium | Medium | Confidence scoring, user review |
| Framework detection errors | Low | Low | Allow manual override |
| Performance impact | Low | Medium | Lazy loading, caching |

---

## Future Considerations (Fase 50+)

### ML-Based Detection
- Train on labeled vulnerability datasets
- Semantic code similarity
- Zero-shot vulnerability detection

### Symbolic Execution
- Path-sensitive analysis
- Constraint solving for reachability

### Inter-File Analysis
- Project-wide data flow
- Module boundary crossing

---

## References

- [tree-sitter](https://tree-sitter.github.io/tree-sitter/) - Multi-language parsing
- [javalang](https://github.com/c2nes/javalang) - Java AST parser
- [Bandit](https://bandit.readthedocs.io/) - Python AST security linter
- [Semgrep](https://semgrep.dev/) - Semantic code analysis patterns
