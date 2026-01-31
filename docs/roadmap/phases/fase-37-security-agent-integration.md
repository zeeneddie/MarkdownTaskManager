# Fase 37: Security Scanner Agent Integration

**Project:** MarQed AI Agent Software Platform
**Week:** KW12-KW18 [w165-171] (Q1 2026, geschat 7 weken)
**Priority:** CRITICAL
**Status:** PLANNED
**ROI Score:** 9.5 (hoogste prioriteit - security gap)
**Created:** 2026-01-16
**Author:** Claude Code (Gap Analysis Session)

---

## Executive Summary

### Probleem
De `SecurityScanOrchestrator` (9 scanners, 150+ CWEs, 30+ talen) is gebouwd maar **NIET geïntegreerd** in de AI-agent workflows. Agents gebruiken momenteel `MigrationSecurityService` die alleen OWASP pattern matching biedt (~20% van de capaciteit).

### Oplossing
Integreer `SecurityScanOrchestrator` in alle 6 workflow touchpoints zodat Quinn agent en andere workflows volledige security scanning capaciteit hebben.

### Impact
- Van 20% naar 100% security scanner dekking
- Van ~30 naar 150+ CWE detectie
- Van 1 scanner naar 9 parallelle scanners
- Alle AI-agent workflows security-enabled

---

## Gap Analysis Samenvatting

### Huidige Staat (PROBLEEM)

```
QuinnExtension (quinn_extension.py)
        │
        ▼
MigrationSecurityService
        │
        ▼
    OWASP Patterns Only (~30 patterns)

    NIET BESCHIKBAAR:
    ✗ OpenGrep (100+ CWEs)
    ✗ Bandit (Python - 69 CWEs)
    ✗ Gosec (Go - 37 CWEs)
    ✗ Trivy (Dependencies/CVEs)
    ✗ SecretScanner (Credentials)
    ✗ GenericSecurityScanner
    ✗ CodeQualityScanner
    ✗ ClassicASPScanner
```

### Gewenste Staat (OPLOSSING)

```
QuinnExtension (quinn_extension.py)
        │
        ▼
SecurityScanOrchestrator
        │
        ├── Language Detection (30+ talen)
        ├── Context-Aware Scanner Selection
        │
        ▼
┌─────────────────────────────────────────┐
│         PARALLEL EXECUTION              │
├─────────┬─────────┬─────────┬──────────┤
│ OpenGrep│ Bandit  │ Gosec   │ Trivy    │
│ OWASP   │ Secret  │ Generic │ ASP      │
│ CodeQual│         │         │          │
└─────────┴─────────┴─────────┴──────────┘
        │
        ▼
    SARIF Output (150+ CWEs)
```

---

## 6 Workflow Touchpoints

### Touchpoint 1: QuinnExtension (PRIORITEIT 1)

**Locatie:** `backend/app/confucius/extensions/quinn_extension.py`

**Huidige Code (lines 77-87):**
```python
def _get_security_service(self):
    """Lazy load security service."""
    if self._security_service is None:
        try:
            from app.services.migration_security_service import (
                MigrationSecurityService,
            )
            self._security_service = MigrationSecurityService()
        except ImportError as e:
            logger.warning(f"Could not import MigrationSecurityService: {e}")
    return self._security_service
```

**Nieuwe Code:**
```python
def _get_security_service(self):
    """Lazy load security orchestrator."""
    if self._security_service is None:
        try:
            from app.services.security_scanner import (
                SecurityScanOrchestrator,
                create_security_orchestrator,
            )
            self._security_service = create_security_orchestrator()
            logger.info("SecurityScanOrchestrator initialized for Quinn")
        except ImportError as e:
            logger.warning(f"Could not import SecurityScanOrchestrator: {e}")
            # Fallback to MigrationSecurityService
            try:
                from app.services.migration_security_service import MigrationSecurityService
                self._security_service = MigrationSecurityService()
                logger.warning("Falling back to MigrationSecurityService")
            except ImportError:
                pass
    return self._security_service
```

**Aanpassingen _security_review():**
```python
async def _security_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute security review using SecurityScanOrchestrator."""
    service = self._get_security_service()

    if hasattr(service, 'scan'):
        # New SecurityScanOrchestrator
        try:
            project_path = context.get("project_path") or context.get("source_path")
            if not project_path:
                return {"issues": [], "error": "No project path provided"}

            report = await service.scan(project_path)

            return {
                "issues": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "severity": f.severity.value,
                        "cwe_id": f.cwe_ids[0] if f.cwe_ids else None,
                        "category": f.category,
                        "file": f.location.file_path,
                        "line": f.location.start_line,
                        "description": f.description,
                        "remediation": f.remediation,
                        "scanner": f.scanner,
                    }
                    for f in report.findings
                ],
                "summary": {
                    "total": report.summary.total_findings,
                    "critical": report.summary.critical,
                    "high": report.summary.high,
                    "scanners_used": report.scanners_used,
                    "languages_detected": report.languages_detected,
                },
                "cwe_coverage": report.cwe_coverage,
                "risk_level": self._calculate_risk_level(report),
            }
        except Exception as e:
            logger.error(f"SecurityScanOrchestrator scan failed: {e}")
            return {"issues": [], "error": str(e)}

    # Fallback for legacy MigrationSecurityService
    return {"issues": [], "risk_level": "unknown"}
```

**Effort:** 16 uur
**Tests:** 25 nieuwe tests

---

### Touchpoint 2: ProjectAssessmentOrchestrator (PRIORITEIT 2)

**Locatie:** `backend/app/services/project_assessment_orchestrator.py`

**Huidige Code (lines 1017-1032):**
```python
async def _run_security_phase(self, assessment: ProjectAssessment) -> PhaseResult:
    """Phase 4: Security Analysis (Quinn)"""
    # Use MigrationSecurityService for OWASP pattern scanning
    from app.services.migration_security_service import (
        get_migration_security_service,
        SecuritySeverity
    )
    security_service = get_migration_security_service()
    security_result = security_service.analyze_directory(
        directory=assessment.directory_path,
        stacks=None,
        severity_threshold=SecuritySeverity.LOW
    )
```

**Nieuwe Code:**
```python
async def _run_security_phase(self, assessment: ProjectAssessment) -> PhaseResult:
    """Phase 4: Security Analysis (Quinn) - Full Scanner Suite"""
    start_time = datetime.utcnow()

    self._log_verbose("security", "INPUT", "Starting security analysis phase", {
        "directory": assessment.directory_path,
        "file_count": assessment.file_count
    })

    try:
        # Use SecurityScanOrchestrator for comprehensive scanning
        from app.services.security_scanner import (
            SecurityScanOrchestrator,
            create_security_orchestrator,
        )

        orchestrator = create_security_orchestrator()
        self._log_verbose("security", "STEP", "Running SecurityScanOrchestrator (9 scanners)")

        # Run full security scan
        report = await orchestrator.scan(assessment.directory_path)

        self._log_verbose("security", "STEP", f"Scan complete", {
            "findings_count": report.summary.total_findings,
            "scanners_used": report.scanners_used,
            "languages_detected": report.languages_detected,
            "cwe_coverage": len(report.cwe_coverage.get("all", []))
        })

        # Map findings to assessment format
        findings_list = []
        for finding in report.findings:
            findings_list.append({
                "id": finding.id,
                "rule_id": finding.rule_id,
                "scanner": finding.scanner,
                "title": finding.title,
                "description": finding.description,
                "severity": finding.severity.value,
                "category": finding.category,
                "cwe_ids": finding.cwe_ids,
                "is_cwe_top_25": finding.is_cwe_top_25,
                "file_path": finding.location.file_path,
                "line_number": finding.location.start_line,
                "code_snippet": finding.location.code_snippet[:200] if finding.location.code_snippet else "",
                "remediation": finding.remediation,
            })

        # Update assessment
        assessment.security_findings = findings_list
        assessment.security_finding_count = len(findings_list)
        assessment.security_critical_count = report.summary.critical
        assessment.security_high_count = report.summary.high
        assessment.security_medium_count = report.summary.by_severity.get("medium", 0)
        assessment.security_low_count = report.summary.by_severity.get("low", 0)
        assessment.security_scanners_used = report.scanners_used
        assessment.security_languages_detected = report.languages_detected
        assessment.security_cwe_coverage = report.cwe_coverage

        # Calculate risk score based on findings
        risk = (
            report.summary.critical * 10 +
            report.summary.high * 5 +
            report.summary.by_severity.get("medium", 0) * 2 +
            report.summary.by_severity.get("low", 0) * 0.5
        )
        assessment.security_risk_score = min(100, risk)

        # Grade calculation
        if risk <= 10:
            assessment.security_grade = "A"
        elif risk <= 25:
            assessment.security_grade = "B"
        elif risk <= 50:
            assessment.security_grade = "C"
        elif risk <= 75:
            assessment.security_grade = "D"
        else:
            assessment.security_grade = "F"

        # Store Quinn context
        assessment.security_findings.append({
            "_quinn_context": {
                "summary": f"{len(findings_list)} findings from {len(report.scanners_used)} scanners",
                "focus_areas": self._extract_focus_areas(findings_list),
                "priority_files": self._extract_priority_files(findings_list)[:10],
                "recommended_tools": report.scanners_used,
                "cwe_top_25_coverage": report.cwe_coverage.get("top_25", []),
            }
        })

        duration = (datetime.utcnow() - start_time).seconds

        return PhaseResult(
            success=True,
            phase_name="security",
            data={
                "findings": findings_list,
                "grade": assessment.security_grade,
                "risk_score": assessment.security_risk_score,
                "scanners_used": report.scanners_used,
                "cwe_coverage": report.cwe_coverage,
            },
            duration_seconds=duration,
            items_processed=report.summary.total_findings,
            items_found=len(findings_list),
        )

    except ImportError as e:
        # Fallback to MigrationSecurityService
        logger.warning(f"SecurityScanOrchestrator not available: {e}, falling back")
        return await self._run_security_phase_legacy(assessment)
    except Exception as e:
        logger.error(f"Security phase failed: {e}")
        return PhaseResult(
            success=False,
            phase_name="security",
            data={},
            error=str(e),
        )
```

**Effort:** 24 uur
**Tests:** 30 nieuwe tests

---

### Touchpoint 3: KanbanQualityGateService (PRIORITEIT 3)

**Locatie:** `backend/app/services/kanban_quality_gate_service.py`

**Probleem:** Security rules sec-001 t/m sec-010 zijn placeholder functies die geen echte scanning doen.

**Nieuwe Implementatie:**

```python
# Toevoegen aan KanbanQualityGateService class

async def _run_security_checks(
    self,
    item_data: Dict[str, Any],
    project_id: Optional[int] = None
) -> List[ValidationResult]:
    """
    Run actual security scanning for sec-001 through sec-010.
    Uses SecurityScanOrchestrator for real CWE detection.
    """
    results = []

    # Get changed files from item data
    changed_files = item_data.get("changed_files", [])
    project_path = item_data.get("project_path")

    if not changed_files and not project_path:
        return results

    try:
        from app.services.security_scanner import create_security_orchestrator

        orchestrator = create_security_orchestrator()

        # Scan changed files or project
        if changed_files:
            report = await orchestrator.scan_files(changed_files)
        else:
            report = await orchestrator.scan(project_path)

        # Map findings to validation rules
        cwe_rule_mapping = {
            "CWE-89": "sec-001",   # SQL Injection
            "CWE-79": "sec-002",   # XSS
            "CWE-352": "sec-003",  # CSRF
            "CWE-287": "sec-004",  # Authentication
            "CWE-862": "sec-005",  # Authorization
            "CWE-798": "sec-006",  # Hardcoded Secrets
            "CWE-1104": "sec-007", # Vulnerable Dependencies
            "CWE-20": "sec-008",   # Input Validation
            "CWE-319": "sec-009",  # Secure Communication
            "CWE-532": "sec-010",  # Log Security
        }

        # Group findings by CWE
        findings_by_rule = {}
        for finding in report.findings:
            for cwe_id in finding.cwe_ids:
                if cwe_id in cwe_rule_mapping:
                    rule_id = cwe_rule_mapping[cwe_id]
                    if rule_id not in findings_by_rule:
                        findings_by_rule[rule_id] = []
                    findings_by_rule[rule_id].append(finding)

        # Create validation results for each security rule
        for rule in [r for r in VALIDATION_RULES if r.category == ValidationCategory.SECURITY]:
            rule_findings = findings_by_rule.get(rule.id, [])

            passed = len(rule_findings) == 0
            severity = "critical" if any(f.severity.value == "critical" for f in rule_findings) else \
                       "high" if any(f.severity.value == "high" for f in rule_findings) else \
                       "medium"

            results.append(ValidationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                category=rule.category.value,
                passed=passed,
                severity=severity,
                message=f"Found {len(rule_findings)} issues" if not passed else "No issues found",
                details={
                    "findings": [
                        {
                            "file": f.location.file_path,
                            "line": f.location.start_line,
                            "title": f.title,
                            "scanner": f.scanner,
                        }
                        for f in rule_findings[:5]  # Limit to 5 examples
                    ],
                    "total_count": len(rule_findings),
                },
                blocking=rule.blocking and not passed,
            ))

        return results

    except ImportError:
        logger.warning("SecurityScanOrchestrator not available for quality gate")
        return results
    except Exception as e:
        logger.error(f"Security checks failed: {e}")
        return results
```

**Update validate_lane_transition():**
```python
async def validate_lane_transition(
    self,
    item_id: str,
    item_type: str,
    from_lane: str,
    to_lane: str,
    item_data: Dict[str, Any],
    project_id: Optional[int] = None
) -> GateValidationResult:
    """Validate quality gates for a lane transition."""

    # ... existing code ...

    # For IN_REVIEW lane, run actual security scanning
    if to_lane == KanbanLane.IN_REVIEW.value:
        security_results = await self._run_security_checks(item_data, project_id)
        all_results.extend(security_results)

    # ... rest of validation ...
```

**Effort:** 20 uur
**Tests:** 25 nieuwe tests

---

### Touchpoint 4: Green Paper Workflow (PRIORITEIT 4)

**Locatie:** `backend/app/confucius/workflows/green_paper.py`

**Probleem:** Geen security review stage voor nieuwe projecten.

**Nieuwe Stage Toevoegen:**

```python
# Voeg toe aan get_stages()

WorkflowStage(
    name="security_requirements",
    description="Review architecture security requirements",
    agents=["Quinn"],  # Security specialist
    required=True,
    quality_threshold=0.80,
    max_iterations=2,
    depends_on=["generate_spec"],  # Na Felix specificatie
),
```

**Nieuwe Stage Handler:**

```python
async def _security_requirements(
    self,
    context: WorkflowContext,
) -> Dict[str, Any]:
    """Execute security requirements review for new project."""

    # Get specification from Felix
    spec = context.shared_data.get("specification", {})

    # Analyze architecture for security concerns
    architecture = spec.get("architecture", {})
    tech_stack = spec.get("tech_stack", [])

    # Get Quinn to review
    agent_results = await self.router.route_task(
        task=f"Review security requirements for new {', '.join(tech_stack)} project architecture",
        context={
            "architecture": architecture,
            "tech_stack": tech_stack,
            "review_type": "security_requirements",
        },
        required_capabilities=["security_review", "owasp_scanning"],
    )

    # Extract security requirements
    security_requirements = {
        "authentication": agent_results.get("auth_requirements", []),
        "authorization": agent_results.get("authz_requirements", []),
        "data_protection": agent_results.get("data_requirements", []),
        "input_validation": agent_results.get("input_requirements", []),
        "logging_audit": agent_results.get("logging_requirements", []),
        "dependency_policy": agent_results.get("dependency_policy", {}),
        "recommended_scanners": agent_results.get("recommended_scanners", []),
        "cwe_focus_areas": agent_results.get("cwe_focus", []),
    }

    # Store in shared data for Diana
    context.shared_data["security_requirements"] = security_requirements

    return {
        "success": True,
        "security_requirements": security_requirements,
        "passes_gate": agent_results.get("passes_gate", True),
    }
```

**Effort:** 16 uur
**Tests:** 20 nieuwe tests

---

### Touchpoint 5: Maintenance Workflow (PRIORITEIT 5)

**Locatie:** `agents/workflows/maintenanceWorkflow.ts`

**Probleem:** Security focus area roept geen scanner aan.

**TypeScript Update:**

```typescript
// maintenanceWorkflow.ts

export interface MaintenanceRequest {
  // ... existing fields ...
  focusAreas?: ('dependencies' | 'code_quality' | 'security' | 'performance' | 'tests' | 'documentation')[];
}

// Add security scanning when 'security' is in focusAreas
async function executeSecurityScan(request: MaintenanceRequest): Promise<SecurityScanResult> {
  // Call Python backend
  const response = await fetch('/api/security/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_path: request.modulePath || request.targetFiles?.[0],
      scan_type: 'full',
      include_dependencies: true,
    }),
  });

  return await response.json();
}

// In executeMaintenanceWorkflow:
if (request.focusAreas?.includes('security')) {
  console.log('🔒 Running security scan via SecurityScanOrchestrator...');
  const securityResult = await executeSecurityScan(request);

  // Add security findings to maintenance report
  result.analysisReport.dependencyVulnerabilities = securityResult.summary?.critical || 0;

  // Add CVE findings
  result.findings.push(...securityResult.findings?.map(f => ({
    category: 'security' as const,
    severity: f.severity as 'critical' | 'high' | 'medium' | 'low',
    issue: f.title,
    location: `${f.file}:${f.line}`,
    recommendation: f.remediation,
    effortSP: f.severity === 'critical' ? 3 : f.severity === 'high' ? 2 : 1,
    risk: f.severity === 'critical' ? 'high' : f.severity === 'high' ? 'medium' : 'low',
  })) || []);
}
```

**Effort:** 12 uur
**Tests:** 15 nieuwe tests

---

### Touchpoint 6: Migration Workflow Security Phase

**Locatie:** `backend/app/confucius/workflows/migration.py`

**Verbetering:** Versterk bestaande security phase met volledige scanner.

```python
# Update _security_analysis stage in MigrationOrchestrator

async def _security_analysis(
    self,
    context: WorkflowContext,
) -> Dict[str, Any]:
    """Execute security analysis for migration assessment."""

    source_path = context.input_data.get("source_path")

    try:
        from app.services.security_scanner import create_security_orchestrator

        orchestrator = create_security_orchestrator()
        report = await orchestrator.scan(source_path)

        # Analyze legacy-specific security issues
        legacy_findings = [f for f in report.findings if f.scanner in ["asp_scanner", "owasp_scanner"]]
        modern_findings = [f for f in report.findings if f.scanner not in ["asp_scanner", "owasp_scanner"]]

        # Route to Quinn for detailed review
        agent_results = await self.router.route_task(
            task="Review security findings for migration planning",
            context={
                "legacy_findings": len(legacy_findings),
                "modern_findings": len(modern_findings),
                "total_findings": report.summary.total_findings,
                "critical_count": report.summary.critical,
                "scanners_used": report.scanners_used,
                "cwe_top_25": report.cwe_coverage.get("top_25", []),
            },
            required_capabilities=["security_review"],
        )

        # Store for migration planning
        context.shared_data["security_analysis"] = {
            "findings": report.findings,
            "summary": report.summary,
            "legacy_specific": legacy_findings,
            "migration_blockers": [f for f in report.findings if f.severity.value == "critical"],
            "quinn_recommendations": agent_results.get("recommendations", []),
        }

        return {
            "success": True,
            "findings_count": report.summary.total_findings,
            "migration_blockers": len([f for f in report.findings if f.severity.value == "critical"]),
        }

    except Exception as e:
        logger.error(f"Security analysis failed: {e}")
        return {"success": False, "error": str(e)}
```

**Effort:** 12 uur
**Tests:** 15 nieuwe tests

---

## Implementation Phases

### Phase 1: Core Integration (KW12-13 [w165-166])
- [ ] Touchpoint 1: QuinnExtension integratie
- [ ] Unit tests voor Quinn + SecurityScanOrchestrator
- [ ] Integration tests

### Phase 2: Workflow Integration (KW14-15 [w167-168])
- [ ] Touchpoint 2: ProjectAssessmentOrchestrator
- [ ] Touchpoint 6: Migration Workflow
- [ ] Tests en documentatie

### Phase 3: Quality Gate Integration (KW16-17 [w169-170])
- [ ] Touchpoint 3: KanbanQualityGateService
- [ ] Touchpoint 5: Maintenance Workflow
- [ ] E2E tests voor lane transitions

### Phase 4: New Project Integration (KW18 [w171])
- [ ] Touchpoint 4: Green Paper Workflow
- [ ] Documentatie update
- [ ] Performance testing
- [ ] Production deployment

---

## Effort Summary

| Touchpoint | Effort (uur) | Tests | Priority |
|------------|--------------|-------|----------|
| 1. QuinnExtension | 16 | 25 | P1 |
| 2. ProjectAssessmentOrchestrator | 24 | 30 | P2 |
| 3. KanbanQualityGateService | 20 | 25 | P3 |
| 4. Green Paper Workflow | 16 | 20 | P4 |
| 5. Maintenance Workflow | 12 | 15 | P5 |
| 6. Migration Workflow | 12 | 15 | P6 |
| **TOTAAL** | **100 uur** | **130 tests** | - |

---

## Success Criteria

### Functioneel
- [ ] Quinn agent kan alle 9 scanners aanroepen
- [ ] 150+ CWEs detecteerbaar via agent workflows
- [ ] Alle 6 touchpoints geïntegreerd
- [ ] Fallback naar legacy service bij errors

### Performance
- [ ] Security scan < 5 minuten voor gemiddeld project
- [ ] Parallel scanner execution
- [ ] Caching voor herhaalde scans

### Quality
- [ ] 130 nieuwe unit tests
- [ ] 90%+ code coverage op nieuwe code
- [ ] Alle bestaande tests blijven groen

---

## Dependencies

### Vereist (moet al bestaan)
- [x] SecurityScanOrchestrator (Fase 31)
- [x] OpenGrepAdapter
- [x] BanditAdapter
- [x] GosecAdapter
- [x] TrivyAdapter
- [x] SecretScanner
- [x] OWASPScanner
- [x] GenericSecurityScanner
- [x] CodeQualityScanner
- [x] ClassicASPScanner

### Verbetert
- Fase 34: Advanced Error Detectors
- Fase 35: Data Integrity Scanners
- Fase 36: Logic & Crypto Scanner

---

## Rollback Plan

Bij kritieke issues:
1. Feature flag `SECURITY_ORCHESTRATOR_ENABLED=false`
2. Fallback naar `MigrationSecurityService`
3. Alle code changes zijn backward compatible

---

## Documentation Updates

Na completion:
- [ ] Update AGENT_SPECIFICATIONS.md
- [ ] Update Confucius workflow docs
- [ ] Update API documentation
- [ ] Add troubleshooting guide

---

## Related Documents

- [fase-31-cwe-security-scanners.md](fase-31-cwe-security-scanners.md) - SecurityScanOrchestrator implementatie
- [cwe-coverage-matrix-complete.md](../../research/cwe-coverage-matrix-complete.md) - CWE dekking overzicht
- [gap-analysis-agent-security.md](../../research/gap-analysis-agent-security.md) - Volledige gap analysis
