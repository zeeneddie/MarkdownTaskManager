# Fase 40: Hybrid False Positive Reduction System

## Executive Summary

Een 3-laags systeem om false positives te reduceren zonder detectiekracht te verliezen:

| Laag | Naam | Snelheid | Lokaal | Doel |
|------|------|----------|--------|------|
| 1 | Regex Scan | <100ms | ✅ | Alle potentiële issues vinden |
| 2 | Heuristic Filter | <10ms/finding | ✅ | Bekende safe patterns uitsluiten |
| 3 | LLM Verification | 1-3s/finding | ❌ | Semantische analyse voor twijfelgevallen |

**Doel:** False positive rate van ~40% naar <10% reduceren.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SecurityScanOrchestrator                         │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ WebSecurity  │    │ PathSecurity │    │ MemorySafety │   ...    │
│  │  Detector    │    │  Detector    │    │  Detector    │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         └───────────────────┴───────────────────┘                   │
│                             │                                        │
│                             ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 FindingFilterPipeline                        │   │
│  │                                                              │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │   │
│  │  │ HeuristicFilter│→ │ ConfidenceScorer│→ │ LLMVerifier   │  │   │
│  │  │ (Fase 2)       │  │                 │  │ (Fase 3)      │  │   │
│  │  └────────────────┘  └────────────────┘  └───────────────┘  │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│                      Filtered Findings                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: HeuristicFilter

### Purpose
Snel uitsluiten van bekende false positive patterns zonder LLM calls.

### Heuristic Categories

#### 1.1 Context Exclusions
```python
CONTEXT_EXCLUSIONS = {
    "test_file": {
        "patterns": [
            r"test[s]?/",
            r"_test\.py$",
            r"\.test\.[jt]sx?$",
            r"spec\.[jt]sx?$",
            r"__tests__/",
        ],
        "action": "reduce_severity",  # of "exclude"
        "reason": "Finding in test code - likely intentional vulnerable example"
    },
    "mock_data": {
        "patterns": [
            r"mock[s]?/",
            r"fixture[s]?/",
            r"fake[s]?/",
            r"stub[s]?/",
        ],
        "action": "exclude",
        "reason": "Mock/fixture data - not production code"
    },
    "documentation": {
        "patterns": [
            r"example[s]?/",
            r"doc[s]?/",
            r"README",
            r"\.md$",
        ],
        "action": "exclude",
        "reason": "Documentation/example code"
    },
    "vendor_code": {
        "patterns": [
            r"vendor/",
            r"node_modules/",
            r"third[_-]?party/",
            r"external/",
        ],
        "action": "exclude",
        "reason": "Third-party code - not our responsibility"
    },
}
```

#### 1.2 Safe Pattern Recognition
```python
SAFE_PATTERNS = {
    # CWE-1321: Prototype Pollution - Safe patterns
    "prototype_pollution_safe": {
        "cwe": "CWE-1321",
        "safe_indicators": [
            r"Object\.create\(null\)",           # Null prototype
            r"Object\.freeze\(",                  # Frozen object
            r"hasOwnProperty\.call\(",           # Property check
            r"Object\.keys\([^)]+\)\.includes",  # Validated keys
            r"structuredClone\(",                # Safe cloning
        ],
        "context_lines": 5,  # Check 5 lines before/after
    },

    # CWE-327: Weak Crypto - Safe patterns
    "weak_crypto_safe": {
        "cwe": "CWE-327",
        "safe_indicators": [
            r"#.*(?:hash|checksum|fingerprint|cache)",  # Comment indicates non-security use
            r"(?:etag|cache[_-]?key|file[_-]?hash)",    # Non-security context
            r"test|mock|fake|stub",                      # Test context
        ],
        "context_lines": 3,
    },

    # CWE-330: Weak PRNG - Safe patterns
    "weak_prng_safe": {
        "cwe": "CWE-330",
        "safe_indicators": [
            r"(?:shuffle|sample|choice).*(?:display|ui|color|animation)",
            r"#.*(?:not.*security|non.*crypto|display|visual)",
            r"(?:game|animation|color|style|css)",
        ],
        "context_lines": 3,
    },

    # CWE-1333: ReDoS - Safe patterns
    "redos_safe": {
        "cwe": "CWE-1333",
        "safe_indicators": [
            r"re\.compile\([^)]+,\s*re\.TIMEOUT",       # Timeout protection
            r"timeout\s*=",                              # Explicit timeout
            r"max[_-]?len(?:gth)?\s*[=<]",              # Length limit before regex
            r"[:]\d+\]",                                 # String slicing before regex
        ],
        "context_lines": 5,
    },
}
```

#### 1.3 Variable Name Heuristics
```python
VARIABLE_NAME_HEURISTICS = {
    "likely_safe_names": [
        r"(?:test|mock|fake|stub|dummy|example|sample|demo)",
        r"(?:constant|config|default|static|readonly)",
        r"(?:template|placeholder|fallback)",
    ],
    "likely_dangerous_names": [
        r"(?:user|input|request|param|query|body|form)",
        r"(?:untrusted|unsafe|raw|external)",
        r"(?:password|secret|token|key|credential)",
    ],
}
```

#### 1.4 Comment Analysis
```python
COMMENT_INDICATORS = {
    "intentional_vulnerability": [
        r"#.*(?:nosec|noqa|ignore|skip|disable)",
        r"//.*(?:eslint-disable|@ts-ignore)",
        r"#.*(?:intentional|deliberate|for\s+testing)",
        r"#.*(?:TODO|FIXME|HACK).*(?:security|vuln)",
    ],
    "security_acknowledged": [
        r"#.*(?:validated|sanitized|escaped|safe)",
        r"#.*(?:trusted\s+source|internal\s+only)",
    ],
}
```

### HeuristicFilter Implementation

```python
@dataclass
class FilterResult:
    finding: Finding
    action: Literal["keep", "exclude", "reduce_severity"]
    reason: str
    confidence_adjustment: float  # -1.0 to +1.0
    heuristics_matched: List[str]


class HeuristicFilter:
    """Fast local filtering of obvious false positives."""

    def __init__(self, config: FilterConfig):
        self.config = config
        self.context_exclusions = CONTEXT_EXCLUSIONS
        self.safe_patterns = SAFE_PATTERNS
        self.variable_heuristics = VARIABLE_NAME_HEURISTICS
        self.comment_indicators = COMMENT_INDICATORS

    async def filter_findings(
        self,
        findings: List[Finding],
        file_contents: Dict[Path, str]
    ) -> List[FilterResult]:
        """Filter findings using heuristics."""
        results = []
        for finding in findings:
            result = await self._evaluate_finding(finding, file_contents)
            results.append(result)
        return results

    async def _evaluate_finding(
        self,
        finding: Finding,
        file_contents: Dict[Path, str]
    ) -> FilterResult:
        heuristics_matched = []
        confidence_adjustment = 0.0

        # 1. Check context exclusions (file path)
        context_result = self._check_context_exclusions(finding)
        if context_result:
            heuristics_matched.append(context_result.heuristic)
            if context_result.action == "exclude":
                return FilterResult(
                    finding=finding,
                    action="exclude",
                    reason=context_result.reason,
                    confidence_adjustment=-1.0,
                    heuristics_matched=heuristics_matched,
                )
            confidence_adjustment += context_result.adjustment

        # 2. Check safe patterns in surrounding code
        content = file_contents.get(finding.file_path, "")
        safe_result = self._check_safe_patterns(finding, content)
        if safe_result:
            heuristics_matched.append(safe_result.heuristic)
            confidence_adjustment += safe_result.adjustment

        # 3. Check variable names
        var_result = self._check_variable_names(finding, content)
        if var_result:
            heuristics_matched.append(var_result.heuristic)
            confidence_adjustment += var_result.adjustment

        # 4. Check comments
        comment_result = self._check_comments(finding, content)
        if comment_result:
            heuristics_matched.append(comment_result.heuristic)
            confidence_adjustment += comment_result.adjustment

        # Determine final action
        if confidence_adjustment <= -0.7:
            action = "exclude"
        elif confidence_adjustment <= -0.3:
            action = "reduce_severity"
        else:
            action = "keep"

        return FilterResult(
            finding=finding,
            action=action,
            reason=self._build_reason(heuristics_matched),
            confidence_adjustment=confidence_adjustment,
            heuristics_matched=heuristics_matched,
        )
```

---

## Component 2: ConfidenceScorer

### Purpose
Bereken een confidence score voor elke finding gebaseerd op meerdere factoren.

### Scoring Factors

```python
@dataclass
class ConfidenceFactors:
    # Pattern match quality (0.0 - 1.0)
    pattern_specificity: float      # Hoe specifiek is de regex match?

    # Context factors (-0.5 to +0.5)
    dangerous_context: float        # User input, request handling, etc.
    safe_context: float             # Test code, constants, etc.

    # Code quality indicators (-0.3 to +0.3)
    has_validation_nearby: float    # Input validation in scope
    has_sanitization: float         # Sanitization/escaping present

    # Historical factors (-0.2 to +0.2)
    rule_precision: float           # Historical precision of this rule

    @property
    def total_score(self) -> float:
        """Calculate final confidence score (0.0 - 1.0)."""
        base = self.pattern_specificity
        adjustments = (
            self.dangerous_context +
            self.safe_context +
            self.has_validation_nearby +
            self.has_sanitization +
            self.rule_precision
        )
        return max(0.0, min(1.0, base + adjustments))


class ConfidenceScorer:
    """Calculate confidence scores for findings."""

    # Historical precision per rule (updated over time)
    RULE_PRECISION = {
        "WS001": 0.85,  # __proto__ assignment - high precision
        "WS003": 0.60,  # Object.assign - medium precision
        "WS004": 0.45,  # Dynamic property access - lower precision
        "PS020": 0.70,  # Nested quantifiers - decent precision
        "PS023": 0.55,  # User input in regex - medium precision
        # ... more rules
    }

    async def score_finding(
        self,
        finding: Finding,
        content: str,
        heuristic_result: FilterResult
    ) -> float:
        factors = ConfidenceFactors(
            pattern_specificity=self._calc_pattern_specificity(finding),
            dangerous_context=self._calc_dangerous_context(finding, content),
            safe_context=self._calc_safe_context(finding, content),
            has_validation_nearby=self._check_validation(finding, content),
            has_sanitization=self._check_sanitization(finding, content),
            rule_precision=self.RULE_PRECISION.get(finding.rule_id, 0.5),
        )

        # Apply heuristic adjustment
        base_score = factors.total_score
        adjusted_score = base_score + (heuristic_result.confidence_adjustment * 0.3)

        return max(0.0, min(1.0, adjusted_score))
```

### Confidence Thresholds

```python
class ConfidenceThresholds:
    """Configurable thresholds for finding handling."""

    # Findings below this are auto-excluded
    AUTO_EXCLUDE: float = 0.25

    # Findings between AUTO_EXCLUDE and this need LLM verification
    LLM_VERIFY: float = 0.60

    # Findings above this are kept without LLM
    AUTO_KEEP: float = 0.60

    # Severity adjustments based on confidence
    SEVERITY_REDUCTION_THRESHOLD: float = 0.45
```

---

## Component 3: LLMVerifier

### Purpose
Semantische analyse voor findings met medium confidence (0.25 - 0.60).

### Design Principles

1. **Minimal LLM calls** - Alleen voor twijfelgevallen
2. **Caching** - Identieke code snippets cachen
3. **Batching** - Meerdere findings per call waar mogelijk
4. **Timeout** - Max 5 seconden per verificatie
5. **Fallback** - Bij LLM failure, keep finding met warning

### LLM Prompt Template

```python
LLM_VERIFICATION_PROMPT = """
You are a security code reviewer. Analyze this potential vulnerability finding.

## Finding Details
- **Rule**: {rule_id} - {rule_title}
- **CWE**: {cwe_ids}
- **Severity**: {severity}
- **File**: {file_path}:{line_number}

## Code Context
```{language}
{code_context}
```

## Matched Pattern
Line {line_number}: `{matched_line}`

## Analysis Required
Determine if this is a TRUE POSITIVE (real vulnerability) or FALSE POSITIVE (safe code).

Consider:
1. Is user/external input actually reaching this code path?
2. Is there validation/sanitization before this point?
3. Is this in test/mock/example code?
4. Is there a security control nearby that mitigates this?
5. Is the variable name suggesting it's already safe/trusted?

## Response Format (JSON only)
{{
    "verdict": "TRUE_POSITIVE" | "FALSE_POSITIVE" | "UNCERTAIN",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation (max 100 words)",
    "mitigating_factors": ["list", "of", "factors"] | null,
    "recommendation": "Keep as-is" | "Exclude" | "Reduce severity" | "Needs manual review"
}}
"""
```

### LLMVerifier Implementation

```python
@dataclass
class LLMVerificationResult:
    verdict: Literal["TRUE_POSITIVE", "FALSE_POSITIVE", "UNCERTAIN"]
    confidence: float
    reasoning: str
    mitigating_factors: Optional[List[str]]
    recommendation: str
    cached: bool = False
    latency_ms: int = 0


class LLMVerifier:
    """LLM-based verification for uncertain findings."""

    def __init__(
        self,
        provider: Literal["openai", "anthropic", "local"] = "anthropic",
        model: str = "claude-3-haiku-20240307",  # Fast & cheap
        cache_ttl: int = 3600,  # 1 hour cache
        timeout: float = 5.0,
        max_concurrent: int = 5,
    ):
        self.provider = provider
        self.model = model
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def verify_findings(
        self,
        findings: List[Tuple[Finding, float]],  # (finding, confidence)
        file_contents: Dict[Path, str],
    ) -> Dict[Finding, LLMVerificationResult]:
        """Verify multiple findings with LLM."""
        results = {}

        # Filter to only uncertain findings
        uncertain = [
            (f, c) for f, c in findings
            if ConfidenceThresholds.AUTO_EXCLUDE < c < ConfidenceThresholds.LLM_VERIFY
        ]

        # Check cache first
        to_verify = []
        for finding, confidence in uncertain:
            cache_key = self._cache_key(finding, file_contents)
            if cache_key in self.cache:
                results[finding] = self.cache[cache_key]
                results[finding].cached = True
            else:
                to_verify.append((finding, confidence, cache_key))

        # Verify uncached findings
        if to_verify:
            verification_tasks = [
                self._verify_single(f, c, ck, file_contents)
                for f, c, ck in to_verify
            ]
            verified = await asyncio.gather(*verification_tasks, return_exceptions=True)

            for (finding, _, cache_key), result in zip(to_verify, verified):
                if isinstance(result, Exception):
                    # Fallback: keep finding with warning
                    result = LLMVerificationResult(
                        verdict="UNCERTAIN",
                        confidence=0.5,
                        reasoning=f"LLM verification failed: {result}",
                        mitigating_factors=None,
                        recommendation="Needs manual review",
                    )
                results[finding] = result
                self.cache[cache_key] = result

        return results

    async def _verify_single(
        self,
        finding: Finding,
        confidence: float,
        cache_key: str,
        file_contents: Dict[Path, str],
    ) -> LLMVerificationResult:
        """Verify a single finding with LLM."""
        async with self.semaphore:
            start = time.monotonic()

            # Build context
            content = file_contents.get(finding.file_path, "")
            code_context = self._extract_context(content, finding.line_number, window=10)

            prompt = LLM_VERIFICATION_PROMPT.format(
                rule_id=finding.rule_id,
                rule_title=finding.title,
                cwe_ids=", ".join(finding.cwe_ids),
                severity=finding.severity.value,
                file_path=finding.file_path,
                line_number=finding.line_number,
                language=finding.file_path.suffix.lstrip("."),
                code_context=code_context,
                matched_line=finding.evidence,
            )

            try:
                response = await self._call_llm(prompt)
                result = self._parse_response(response)
                result.latency_ms = int((time.monotonic() - start) * 1000)
                return result
            except asyncio.TimeoutError:
                raise Exception(f"LLM timeout after {self.timeout}s")

    def _cache_key(self, finding: Finding, file_contents: Dict[Path, str]) -> str:
        """Generate cache key based on code content and rule."""
        content = file_contents.get(finding.file_path, "")
        context = self._extract_context(content, finding.line_number, window=5)
        return hashlib.sha256(
            f"{finding.rule_id}:{context}".encode()
        ).hexdigest()[:16]
```

### LLM Provider Abstraction

```python
class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def complete(self, prompt: str, timeout: float) -> str:
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, timeout: float) -> str:
        response = await asyncio.wait_for(
            self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            ),
            timeout=timeout,
        )
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, timeout: float) -> str:
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            ),
            timeout=timeout,
        )
        return response.choices[0].message.content


class LocalLLMProvider(LLMProvider):
    """Local LLM provider (Ollama, llama.cpp, etc.)."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def complete(self, prompt: str, timeout: float) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                data = await response.json()
                return data["response"]
```

---

## Component 4: FindingFilterPipeline

### Purpose
Orchestratie van alle filter componenten.

```python
@dataclass
class PipelineConfig:
    """Configuration for the filter pipeline."""

    # Heuristic filter settings
    enable_heuristics: bool = True
    exclude_test_files: bool = True
    exclude_vendor_files: bool = True

    # Confidence scoring
    enable_confidence_scoring: bool = True

    # LLM verification settings
    enable_llm_verification: bool = False  # Opt-in
    llm_provider: Literal["anthropic", "openai", "local"] = "anthropic"
    llm_model: str = "claude-3-haiku-20240307"
    llm_timeout: float = 5.0
    llm_max_concurrent: int = 5
    llm_cache_ttl: int = 3600

    # Thresholds
    auto_exclude_threshold: float = 0.25
    llm_verify_threshold: float = 0.60
    severity_reduction_threshold: float = 0.45


@dataclass
class PipelineResult:
    """Result of the filter pipeline."""

    original_count: int
    filtered_count: int
    excluded_count: int
    severity_reduced_count: int
    llm_verified_count: int

    findings: List[Finding]  # Final filtered findings
    excluded: List[Tuple[Finding, str]]  # (finding, reason)

    # Metrics
    processing_time_ms: int
    llm_calls: int
    llm_cache_hits: int

    @property
    def reduction_rate(self) -> float:
        if self.original_count == 0:
            return 0.0
        return (self.original_count - self.filtered_count) / self.original_count


class FindingFilterPipeline:
    """Main pipeline orchestrating all filter components."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.heuristic_filter = HeuristicFilter(config)
        self.confidence_scorer = ConfidenceScorer()
        self.llm_verifier = None

        if config.enable_llm_verification:
            self.llm_verifier = LLMVerifier(
                provider=config.llm_provider,
                model=config.llm_model,
                timeout=config.llm_timeout,
                max_concurrent=config.llm_max_concurrent,
                cache_ttl=config.llm_cache_ttl,
            )

    async def process(
        self,
        findings: List[Finding],
        file_contents: Dict[Path, str],
    ) -> PipelineResult:
        """Process findings through the filter pipeline."""
        start = time.monotonic()

        original_count = len(findings)
        excluded = []
        llm_verified = 0
        llm_cache_hits = 0
        severity_reduced = 0

        # Phase 1: Heuristic filtering
        if self.config.enable_heuristics:
            heuristic_results = await self.heuristic_filter.filter_findings(
                findings, file_contents
            )
        else:
            heuristic_results = [
                FilterResult(f, "keep", "", 0.0, []) for f in findings
            ]

        # Phase 2: Confidence scoring
        scored_findings = []
        for hresult in heuristic_results:
            if hresult.action == "exclude":
                excluded.append((hresult.finding, hresult.reason))
                continue

            if self.config.enable_confidence_scoring:
                confidence = await self.confidence_scorer.score_finding(
                    hresult.finding,
                    file_contents.get(hresult.finding.file_path, ""),
                    hresult,
                )
            else:
                confidence = 0.7  # Default high confidence

            # Auto-exclude low confidence
            if confidence < self.config.auto_exclude_threshold:
                excluded.append((hresult.finding, f"Low confidence: {confidence:.2f}"))
                continue

            scored_findings.append((hresult.finding, confidence, hresult))

        # Phase 3: LLM verification (for uncertain findings)
        final_findings = []
        if self.llm_verifier and self.config.enable_llm_verification:
            # Separate certain from uncertain
            certain = [(f, c, h) for f, c, h in scored_findings
                      if c >= self.config.llm_verify_threshold]
            uncertain = [(f, c, h) for f, c, h in scored_findings
                        if c < self.config.llm_verify_threshold]

            # Add certain findings directly
            for finding, confidence, hresult in certain:
                if confidence < self.config.severity_reduction_threshold:
                    finding = self._reduce_severity(finding)
                    severity_reduced += 1
                final_findings.append(finding)

            # Verify uncertain findings with LLM
            if uncertain:
                llm_results = await self.llm_verifier.verify_findings(
                    [(f, c) for f, c, _ in uncertain],
                    file_contents,
                )

                for finding, confidence, hresult in uncertain:
                    llm_result = llm_results.get(finding)
                    if llm_result:
                        if llm_result.cached:
                            llm_cache_hits += 1
                        else:
                            llm_verified += 1

                        if llm_result.verdict == "FALSE_POSITIVE":
                            excluded.append((finding, f"LLM: {llm_result.reasoning}"))
                        elif llm_result.recommendation == "Reduce severity":
                            final_findings.append(self._reduce_severity(finding))
                            severity_reduced += 1
                        else:
                            final_findings.append(finding)
                    else:
                        # LLM failed, keep finding
                        final_findings.append(finding)
        else:
            # No LLM, use confidence-based filtering
            for finding, confidence, hresult in scored_findings:
                if confidence < self.config.severity_reduction_threshold:
                    finding = self._reduce_severity(finding)
                    severity_reduced += 1
                final_findings.append(finding)

        processing_time = int((time.monotonic() - start) * 1000)

        return PipelineResult(
            original_count=original_count,
            filtered_count=len(final_findings),
            excluded_count=len(excluded),
            severity_reduced_count=severity_reduced,
            llm_verified_count=llm_verified,
            findings=final_findings,
            excluded=excluded,
            processing_time_ms=processing_time,
            llm_calls=llm_verified,
            llm_cache_hits=llm_cache_hits,
        )

    def _reduce_severity(self, finding: Finding) -> Finding:
        """Reduce finding severity by one level."""
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        current_idx = severity_order.index(finding.severity)
        if current_idx > 0:
            new_severity = severity_order[current_idx - 1]
            return finding.model_copy(update={"severity": new_severity})
        return finding
```

---

## Integration with Orchestrator

### Modified SecurityScanOrchestrator

```python
class SecurityScanOrchestrator:
    """Main orchestrator with filter pipeline integration."""

    def __init__(
        self,
        filter_config: Optional[PipelineConfig] = None,
    ):
        self.scanners = self._initialize_scanners()
        self.filter_pipeline = FindingFilterPipeline(
            filter_config or PipelineConfig()
        )

    async def scan(
        self,
        path: Path,
        enable_filtering: bool = True,
    ) -> ScanReport:
        """Scan code and optionally filter findings."""

        # Phase 1: Run all scanners
        raw_findings = await self._run_scanners(path)

        # Phase 2: Filter findings (if enabled)
        if enable_filtering:
            file_contents = await self._load_file_contents(path)
            filter_result = await self.filter_pipeline.process(
                raw_findings, file_contents
            )
            findings = filter_result.findings

            # Add filter metrics to report
            filter_metrics = {
                "original_findings": filter_result.original_count,
                "filtered_findings": filter_result.filtered_count,
                "excluded_findings": filter_result.excluded_count,
                "reduction_rate": f"{filter_result.reduction_rate:.1%}",
                "llm_calls": filter_result.llm_calls,
                "llm_cache_hits": filter_result.llm_cache_hits,
                "filter_time_ms": filter_result.processing_time_ms,
            }
        else:
            findings = raw_findings
            filter_metrics = None

        return ScanReport(
            findings=findings,
            filter_metrics=filter_metrics,
            # ... rest of report
        )
```

---

## Configuration

### Environment Variables

```bash
# LLM Provider Configuration
SECURITY_SCANNER_LLM_ENABLED=false
SECURITY_SCANNER_LLM_PROVIDER=anthropic  # anthropic, openai, local
SECURITY_SCANNER_LLM_MODEL=claude-3-haiku-20240307
SECURITY_SCANNER_LLM_TIMEOUT=5.0
SECURITY_SCANNER_LLM_MAX_CONCURRENT=5

# API Keys (if using cloud LLM)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Local LLM (if using Ollama/llama.cpp)
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3

# Filter Thresholds
SECURITY_SCANNER_AUTO_EXCLUDE_THRESHOLD=0.25
SECURITY_SCANNER_LLM_VERIFY_THRESHOLD=0.60
```

### Config File (security_scanner.yaml)

```yaml
filter_pipeline:
  enable_heuristics: true
  enable_confidence_scoring: true
  enable_llm_verification: false  # Opt-in

  heuristics:
    exclude_test_files: true
    exclude_vendor_files: true
    exclude_documentation: true
    check_safe_patterns: true
    check_variable_names: true
    check_comments: true

  thresholds:
    auto_exclude: 0.25
    llm_verify: 0.60
    severity_reduction: 0.45

  llm:
    provider: anthropic
    model: claude-3-haiku-20240307
    timeout: 5.0
    max_concurrent: 5
    cache_ttl: 3600
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `services/security_scanner/filters/__init__.py` | Package exports |
| `services/security_scanner/filters/heuristic_filter.py` | Heuristic-based filtering |
| `services/security_scanner/filters/confidence_scorer.py` | Confidence scoring |
| `services/security_scanner/filters/llm_verifier.py` | LLM verification |
| `services/security_scanner/filters/pipeline.py` | Filter pipeline orchestration |
| `services/security_scanner/filters/config.py` | Configuration dataclasses |
| `services/security_scanner/filters/providers/__init__.py` | LLM provider exports |
| `services/security_scanner/filters/providers/base.py` | Abstract provider |
| `services/security_scanner/filters/providers/anthropic.py` | Anthropic provider |
| `services/security_scanner/filters/providers/openai.py` | OpenAI provider |
| `services/security_scanner/filters/providers/local.py` | Local LLM provider |

## Files to Modify

| File | Changes |
|------|---------|
| `services/security_scanner/orchestrator.py` | Integrate filter pipeline |
| `services/security_scanner/models/findings.py` | Add confidence field to Finding |
| `services/security_scanner/models/report.py` | Add filter_metrics to ScanReport |

---

## Unit Tests

### Test Files to Create

| File | Tests |
|------|-------|
| `tests/unit/security_scanner/filters/test_heuristic_filter.py` | ~30 tests |
| `tests/unit/security_scanner/filters/test_confidence_scorer.py` | ~20 tests |
| `tests/unit/security_scanner/filters/test_llm_verifier.py` | ~15 tests (mocked) |
| `tests/unit/security_scanner/filters/test_pipeline.py` | ~20 tests |

### Example Tests

```python
class TestHeuristicFilter:
    """Tests for HeuristicFilter."""

    async def test_excludes_test_files(self):
        """Findings in test files should be excluded."""
        finding = Finding(
            file_path=Path("tests/test_auth.py"),
            rule_id="WS001",
            # ...
        )
        filter = HeuristicFilter(FilterConfig())
        result = await filter._evaluate_finding(finding, {})
        assert result.action == "exclude"
        assert "test_file" in result.heuristics_matched

    async def test_detects_safe_pattern(self):
        """Safe patterns should reduce confidence."""
        finding = Finding(
            file_path=Path("src/auth.py"),
            line_number=10,
            rule_id="WS001",
            cwe_ids=["CWE-1321"],
        )
        content = """
        def merge(obj, input):
            if hasOwnProperty.call(input, key):  # Safe check
                obj[key] = input[key]
        """
        filter = HeuristicFilter(FilterConfig())
        result = await filter._evaluate_finding(finding, {finding.file_path: content})
        assert result.confidence_adjustment < 0

    async def test_detects_nosec_comment(self):
        """nosec comments should exclude findings."""
        finding = Finding(file_path=Path("src/legacy.py"), line_number=5)
        content = """
        # nosec: intentional for backwards compatibility
        md5_hash = hashlib.md5(data)
        """
        filter = HeuristicFilter(FilterConfig())
        result = await filter._evaluate_finding(finding, {finding.file_path: content})
        assert result.action == "exclude"


class TestConfidenceScorer:
    """Tests for ConfidenceScorer."""

    async def test_high_confidence_for_dangerous_context(self):
        """User input context should increase confidence."""
        finding = Finding(
            rule_id="WS001",
            evidence="obj[req.body.key] = value",
        )
        scorer = ConfidenceScorer()
        score = await scorer.score_finding(finding, "obj[req.body.key] = value", None)
        assert score > 0.7

    async def test_low_confidence_for_safe_names(self):
        """Safe variable names should reduce confidence."""
        finding = Finding(
            rule_id="WS001",
            evidence="testObj[mockKey] = value",
        )
        scorer = ConfidenceScorer()
        score = await scorer.score_finding(finding, "testObj[mockKey] = value", None)
        assert score < 0.5


class TestLLMVerifier:
    """Tests for LLMVerifier (mocked)."""

    async def test_caches_identical_findings(self):
        """Identical code contexts should be cached."""
        verifier = LLMVerifier(provider="anthropic")
        verifier._call_llm = AsyncMock(return_value='{"verdict": "FALSE_POSITIVE", ...}')

        finding1 = Finding(file_path=Path("a.py"), line_number=10)
        finding2 = Finding(file_path=Path("b.py"), line_number=20)
        content = {"a.py": "same code", "b.py": "same code"}

        await verifier.verify_findings([(finding1, 0.4)], content)
        await verifier.verify_findings([(finding2, 0.4)], content)

        # Should only call LLM once due to caching
        assert verifier._call_llm.call_count == 1

    async def test_fallback_on_timeout(self):
        """LLM timeout should keep finding with warning."""
        verifier = LLMVerifier(provider="anthropic", timeout=0.1)
        verifier._call_llm = AsyncMock(side_effect=asyncio.TimeoutError())

        finding = Finding(file_path=Path("a.py"), line_number=10)
        results = await verifier.verify_findings([(finding, 0.4)], {"a.py": "code"})

        assert results[finding].verdict == "UNCERTAIN"
        assert "timeout" in results[finding].reasoning.lower()
```

---

## Execution Order

### Phase 1: Foundation (Day 1)
1. Create `filters/` package structure
2. Implement `config.py` with all dataclasses
3. Add confidence field to Finding model

### Phase 2: Heuristic Filter (Day 2)
1. Implement `heuristic_filter.py`
2. Define all heuristic patterns
3. Write 30 unit tests

### Phase 3: Confidence Scorer (Day 3)
1. Implement `confidence_scorer.py`
2. Define scoring factors
3. Write 20 unit tests

### Phase 4: LLM Verifier (Day 4)
1. Implement provider abstraction
2. Implement `llm_verifier.py` with caching
3. Write 15 unit tests (mocked)

### Phase 5: Pipeline Integration (Day 5)
1. Implement `pipeline.py`
2. Integrate with orchestrator
3. Write 20 integration tests

### Phase 6: Testing & Tuning (Day 6)
1. Run against real codebase
2. Tune thresholds based on results
3. Document configuration options

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| False Positive Reduction | >50% | (excluded + severity_reduced) / original |
| True Positive Retention | >95% | verified by manual review |
| Heuristic Filter Speed | <10ms/finding | processing_time / finding_count |
| LLM Verification Speed | <3s/finding | average LLM call latency |
| LLM Cache Hit Rate | >30% | cache_hits / total_llm_calls |
| Overall Processing Overhead | <20% | filter_time / scan_time |

---

## Cost Estimation (LLM)

### Per-Finding Costs (Anthropic Claude 3 Haiku)

| Scenario | Input Tokens | Output Tokens | Cost |
|----------|--------------|---------------|------|
| Average finding | ~500 | ~200 | $0.0003 |
| Complex finding | ~1000 | ~300 | $0.0006 |

### Monthly Estimate

| Usage | Findings/Month | LLM Verified (30%) | Cost |
|-------|----------------|-------------------|------|
| Light | 1,000 | 300 | ~$0.10 |
| Medium | 10,000 | 3,000 | ~$1.00 |
| Heavy | 100,000 | 30,000 | ~$10.00 |

*Note: With caching, actual costs are typically 30-50% lower.*

---

## Future Enhancements

1. **Learning from feedback** - Track user overrides to improve heuristics
2. **Custom rules** - Allow users to define project-specific safe patterns
3. **Batch LLM verification** - Group multiple findings per LLM call
4. **Fine-tuned model** - Train on security code review data
5. **IDE integration** - Inline false positive dismissal with learning
