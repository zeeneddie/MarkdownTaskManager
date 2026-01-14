# 12 Coding Mistakes Every Developer Should Avoid

**Bron:** Techvalens (LinkedIn, 26 dec 2023)
**Doel:** Quality checklist voor code reviews, rapportages en automated detection
**Integratie:** MarQed AI Agent Platform

---

## Overview & Scanner Mapping

| # | Coding Mistake | MarQed Scanner | Status | SIG Metric |
|---|----------------|----------------|--------|------------|
| 1 | Ignoring Code Readability | CommentsAnalyzer | 🟢 | Code Comments |
| 2 | Overlooking Testing | TestCoverageAnalyzer | 🔴 N/A | Test Coverage |
| 3 | Not Embracing Modularity | CouplingAnalyzer, BalanceAnalyzer | 🟢 | Coupling, Balance |
| 4 | Lack of Error Handling | ExceptionalConditionDetector | 🔴 Planned | - |
| 5 | Disregarding Security | CWE Top 25 Suite | 🔴 Planned | - |
| 6 | Reinventing the Wheel | DuplicationAnalyzer | 🟢 | Duplication |
| 7 | Poor Version Control | - | ⚪ External | - |
| 8 | Neglecting Performance | ComplexityAnalyzer | 🟢 | Complexity |
| 9 | Not Keeping DRY | DuplicationAnalyzer | 🟢 | Duplication |
| 10 | Foregoing Documentation | CommentsAnalyzer | 🟢 | Code Comments |
| 11 | Ignoring User Experience | - | ⚪ Manual | - |
| 12 | Not Seeking Feedback | - | ⚪ Process | - |

**Coverage:** 7/12 automated (58%), 2 planned, 3 out of scope

---

## Detailed Mapping

### 1. Ignoring Code Readability

> *"Code is not just for machines; it's for humans too. Neglecting readability hampers collaboration and maintenance."*

**Detection:**
- CommentsAnalyzer: Comment ratio < 10% = Warning
- NamingConventionAnalyzer: Inconsistent naming patterns
- LineLengthAnalyzer: Lines > 120 characters

**Report Template:**
```markdown
### Code Readability Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Comment Ratio | {value}% | >10% | {status} |
| Avg Line Length | {value} | <80 | {status} |
| Descriptive Names | {value}% | >90% | {status} |

**Recommendations:**
- Add descriptive comments to complex logic sections
- Use meaningful variable names (avoid single letters except loops)
- Break long lines for better readability
```

**MarQed Scanner:** `CommentsAnalyzer` 🟢
**SIG Rating Impact:** Code Comments metric

---

### 2. Overlooking Testing

> *"Rushing through testing or skipping it entirely invites bugs and glitches."*

**Detection:**
- Test file presence check
- Test coverage percentage (if available)
- Test-to-code ratio

**Report Template:**
```markdown
### Testing Coverage Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Test Files | {count} | >0 | {status} |
| Test Coverage | {value}% | >70% | {status} |
| Test/Code Ratio | {value} | >0.3 | {status} |

**Recommendations:**
- Implement unit tests for critical business logic
- Add integration tests for API endpoints
- Consider characterization tests for legacy code
```

**MarQed Scanner:** `TestCoverageAnalyzer` 🔴 (not available for Classic ASP)
**SIG Rating Impact:** Test Coverage, Test Quality

---

### 3. Not Embracing Modularity

> *"Monolithic code becomes unwieldy. Embrace modularity by breaking code into smaller, reusable components."*

**Detection:**
- CouplingAnalyzer: High fan-in/fan-out
- BalanceAnalyzer: Uneven component distribution
- ComplexityAnalyzer: God classes/files

**Report Template:**
```markdown
### Modularity Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg Module Size | {value} LOC | <500 | {status} |
| Component Balance | {rating}/5 | >3 | {status} |
| Coupling Score | {value} | <0.3 | {status} |
| God Files (>1000 LOC) | {count} | 0 | {status} |

**Top Monolithic Files:**
{list_of_large_files}

**Recommendations:**
- Extract reusable functions into shared modules
- Apply Single Responsibility Principle
- Consider microservices for independent domains
```

**MarQed Scanner:** `CouplingAnalyzer`, `BalanceAnalyzer` 🟢
**SIG Rating Impact:** Module Coupling, Component Balance

---

### 4. Lack of Error Handling

> *"Failing to anticipate and handle errors leads to unpredictable behavior."*

**Detection:**
- ExceptionalConditionDetector: Missing try-catch
- Error pattern analysis: `On Error Resume Next` without check
- Database operations without error handling

**Report Template:**
```markdown
### Error Handling Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Unhandled DB Operations | {count} | 0 | {status} |
| Silent Error Ignoring | {count} | 0 | {status} |
| Missing Error Logging | {count} | 0 | {status} |

**Critical Gaps:**
{list_of_unhandled_errors}

**Recommendations:**
- Wrap all database operations in error handlers
- Log errors server-side before showing user message
- Never expose stack traces or SQL to users
```

**MarQed Scanner:** `ExceptionalConditionDetector` 🔴 Planned (Fase 31.5)
**CWE Mapping:** CWE-754 (Improper Check for Exceptional Conditions)

---

### 5. Disregarding Security Measures

> *"Avoid hardcoded credentials, SQL injection, XSS attacks, and other common security loopholes."*

**Detection:**
- SQLInjectionDetector: Unparameterized queries
- XSSDetector: Unescaped output
- HardcodedCredentialsDetector: Passwords in code
- Full CWE Top 25 suite

**Report Template:**
```markdown
### Security Assessment

| Vulnerability | Count | Severity | CWE |
|---------------|-------|----------|-----|
| SQL Injection | {count} | CRITICAL | CWE-89 |
| XSS | {count} | CRITICAL | CWE-79 |
| Hardcoded Credentials | {count} | CRITICAL | CWE-798 |
| Missing Authentication | {count} | HIGH | CWE-306 |
| Missing Encryption | {count} | HIGH | CWE-311 |

**OWASP Top 10 Coverage:** {percentage}%

**Recommendations:**
- Use parameterized queries for all database access
- Encode all user-controlled output
- Store credentials in secure configuration
- Implement proper authentication/authorization
```

**MarQed Scanner:** CWE Top 25 Suite 🔴 Planned (Fase 31.1-31.5)
**NFR Mapping:** NFR-002.1, NFR-003.1, NFR-003.2

---

### 6. Reinventing the Wheel

> *"While it's tempting to create everything from scratch, leveraging existing libraries saves time and effort."*

**Detection:**
- DuplicationAnalyzer: Repeated implementations
- Pattern detection: Common algorithms reimplemented
- Library availability analysis

**Report Template:**
```markdown
### Code Reuse Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Clone Instances | {count} | <100 | {status} |
| Duplication % | {value}% | <5% | {status} |
| Reimplemented Patterns | {count} | 0 | {status} |

**Common Reimplementations Found:**
{list_of_reimplementations}

**Recommendations:**
- Use standard libraries for common operations
- Create shared utility modules for repeated patterns
- Consider established frameworks before custom solutions
```

**MarQed Scanner:** `DuplicationAnalyzer` 🟢
**SIG Rating Impact:** Duplication

---

### 7. Poor Version Control Practices

> *"Inadequate version control can result in chaos. Utilize Git effectively."*

**Detection:**
- Git history analysis
- Commit message quality
- Branch strategy compliance

**Report Template:**
```markdown
### Version Control Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Meaningful Commits | {value}% | >90% | {status} |
| Branch Strategy | {status} | Defined | {status} |
| Merge Conflicts | {count}/month | <5 | {status} |

**Recommendations:**
- Write descriptive commit messages
- Follow established branching strategy (GitFlow, trunk-based)
- Commit frequently with atomic changes
```

**MarQed Scanner:** ⚪ External (Git analysis tools)
**Integration:** Can be added via Git history parsing

---

### 8. Neglecting Performance Optimization

> *"Inefficient algorithms and poorly optimized code can slow down your application."*

**Detection:**
- ComplexityAnalyzer: High cyclomatic complexity
- Algorithm analysis: O(n²) or worse patterns
- Resource usage patterns

**Report Template:**
```markdown
### Performance Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg Complexity | {value} | <15 | {status} |
| High Complexity Files | {count} | 0 | {status} |
| Nested Loops (>2 deep) | {count} | <10 | {status} |
| Unbounded Loops | {count} | 0 | {status} |

**Performance Hotspots:**
{list_of_complex_files}

**Recommendations:**
- Refactor methods with CC > 20
- Add iteration limits to loops
- Consider caching for expensive operations
```

**MarQed Scanner:** `ComplexityAnalyzer` 🟢
**SIG Rating Impact:** Unit Complexity

---

### 9. Not Keeping Codebase DRY

> *"Repeated code leads to maintenance nightmares. Follow the Don't Repeat Yourself principle."*

**Detection:**
- DuplicationAnalyzer: Type 1, 2, 3 clones
- Similar pattern detection
- Copy-paste indicators

**Report Template:**
```markdown
### DRY Principle Assessment

| Clone Type | Count | Description |
|------------|-------|-------------|
| Type 1 (Exact) | {count} | Identical code blocks |
| Type 2 (Renamed) | {count} | Same structure, different names |
| Type 3 (Similar) | {count} | Similar logic, minor variations |

**Duplication Percentage:** {value}%
**Target:** <5%

**Top Duplication Hotspots:**
{list_of_duplicated_code}

**Recommendations:**
- Extract common code into shared functions
- Use inheritance or composition for similar classes
- Create configuration-driven solutions instead of copies
```

**MarQed Scanner:** `DuplicationAnalyzer` 🟢
**SIG Rating Impact:** Duplication

---

### 10. Foregoing Documentation

> *"Clear and updated documentation is a lifeline for developers."*

**Detection:**
- CommentsAnalyzer: Comment coverage
- API documentation presence
- README/inline doc quality

**Report Template:**
```markdown
### Documentation Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Comment Ratio | {value}% | >15% | {status} |
| Public API Docs | {value}% | 100% | {status} |
| README Present | {status} | Yes | {status} |
| Architecture Docs | {status} | Yes | {status} |

**Undocumented Critical Components:**
{list_of_undocumented}

**Recommendations:**
- Add header comments to all public functions
- Document complex business logic inline
- Maintain up-to-date API documentation
- Create architecture decision records (ADRs)
```

**MarQed Scanner:** `CommentsAnalyzer` 🟢
**SIG Rating Impact:** Code Comments
**NFR Mapping:** NFR-002.3, NFR-004.1

---

### 11. Ignoring User Experience

> *"Pay attention to usability, accessibility, and design principles."*

**Detection:**
- Accessibility checker (WCAG)
- UI consistency analysis
- Error message quality

**Report Template:**
```markdown
### User Experience Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| WCAG Compliance | {level} | AA | {status} |
| Error Message Quality | {value}% | >90% | {status} |
| Responsive Design | {status} | Yes | {status} |

**Recommendations:**
- Follow WCAG 2.1 AA guidelines
- Provide clear, actionable error messages
- Test with real users for usability feedback
```

**MarQed Scanner:** ⚪ Manual review required
**NFR Mapping:** NFR-001.3 (Complex Operation)

---

### 12. Not Seeking Feedback

> *"Embrace constructive criticism, perform code reviews, and seek input from peers."*

**Detection:**
- Code review metrics
- PR review coverage
- Feedback implementation rate

**Report Template:**
```markdown
### Feedback & Review Assessment

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Code Review Coverage | {value}% | 100% | {status} |
| Avg Review Comments | {value} | >2 | {status} |
| Review Turnaround | {hours}h | <24h | {status} |

**Recommendations:**
- Require code reviews for all changes
- Use automated tools to supplement manual review
- Create psychological safety for honest feedback
```

**MarQed Scanner:** ⚪ Process metric (external)
**NFR Mapping:** NFR-004.3 (Quality Assurance)

---

## Consolidated Report Template

```markdown
# Code Quality Report - {PROJECT_NAME}

**Date:** {DATE}
**Analyzed by:** MarQed AI Agent Platform
**Files:** {FILE_COUNT} | **Lines:** {LOC_COUNT}

## Executive Summary

| Category | Score | Status |
|----------|-------|--------|
| Readability | {score}/5 | {status} |
| Testing | {score}/5 | {status} |
| Modularity | {score}/5 | {status} |
| Error Handling | {score}/5 | {status} |
| Security | {score}/5 | {status} |
| DRY/Reuse | {score}/5 | {status} |
| Performance | {score}/5 | {status} |
| Documentation | {score}/5 | {status} |
| **Overall** | **{score}/5** | **{status}** |

## Critical Findings

{critical_findings_table}

## Recommendations Priority

1. **Immediate:** {immediate_actions}
2. **Short-term:** {short_term_actions}
3. **Long-term:** {long_term_actions}

---
*Generated by MarQed AI Agent Platform*
*Based on: 12 Coding Mistakes (Techvalens) + SIG Top 10 + CWE Top 25*
```

---

## Integration Points

### Brown Paper Workflow
- Phase 1: All automated metrics collected
- Phase 2: Domain-specific quality patterns
- Phase 6: Report generation using templates

### API Endpoints
```
GET /api/quality-report/{project_id}/coding-mistakes
GET /api/quality-report/{project_id}/consolidated
POST /api/quality-report/{project_id}/generate-pdf
```

---

## References

- [Techvalens - 12 Coding Mistakes](https://linkedin.com/pulse/12-coding-mistakes-techvalens) (Dec 2023)
- [SIG Top 10 Maintainability](https://www.softwareimprovementgroup.com/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [GEMMA Informatiebeveiliging](../nfr/gemma-informatiebeveiliging-userstories.md)

---

*Document Version: 1.0*
*Created: 2026-01-13*
*MarQed AI Agent Platform*
