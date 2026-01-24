# Security Scan Skill

**Comprehensive security vulnerability detection and compliance verification for healthcare IT systems**

---

## Overview

This skill provides systematic security analysis including vulnerability detection, OWASP Top 10 verification, healthcare compliance checking (NEN7510, ISO27001, GDPR), and risk-based prioritization.

### What This Skill Does

- ✅ OWASP Top 10 vulnerability detection
- ✅ Healthcare compliance verification (NEN7510, ISO27001, GDPR)
- ✅ Dependency vulnerability scanning
- ✅ Code-level security analysis
- ✅ Authentication & authorization checks
- ✅ Data protection assessment
- ✅ Risk-based prioritization

### When to Use This Skill

Use this skill when you need to:
- Identify security vulnerabilities in code
- Verify compliance with healthcare regulations
- Assess security posture before deployment
- Prioritize security fixes by risk
- Generate security audit reports
- Prepare for security certifications

---

## Core Capabilities

### 1. OWASP Top 10 Detection

**A01: Broken Access Control**
```python
def check_access_control(codebase):
    """Detect missing or broken access control"""
    
    issues = []
    
    # Find endpoints
    endpoints = find_endpoints(codebase)
    
    for endpoint in endpoints:
        # Check for authorization
        if not has_authorization(endpoint):
            issues.append({
                'type': 'missing_authorization',
                'severity': 'high',
                'location': endpoint['file'],
                'line': endpoint['line'],
                'owasp': 'A01:2021',
                'remediation': 'Add [Authorize] attribute or equivalent'
            })
        
        # Check for IDOR
        if has_direct_object_reference(endpoint) and not validates_ownership(endpoint):
            issues.append({
                'type': 'idor',
                'severity': 'high',
                'location': endpoint['file'],
                'owasp': 'A01:2021',
                'remediation': 'Validate user ownership before access'
            })
    
    return issues
```

**A02: Cryptographic Failures**
```bash
# Detect weak cryptography
check_weak_crypto() {
    # Weak hashing algorithms
    grep -rn "MD5\|SHA1\|DES\b" src/ > weak-crypto.txt
    
    # Hardcoded secrets
    grep -rni "password\s*=\s*['\"].*['\"]" src/ > hardcoded-secrets.txt
    grep -rni "api[_-]?key\s*=\s*['\"]" src/ > hardcoded-keys.txt
    
    # Check TLS configuration
    check_tls_version src/
}
```

**A03: Injection**
```python
def detect_sql_injection(codebase):
    """Detect SQL injection vulnerabilities"""
    
    patterns = {
        'csharp': [
            r'Execute\s*\(\s*["\'].*?\+',
            r'SqlCommand\s*\(["\'].*?\+',
        ],
        'python': [
            r'execute\s*\(["\'].*?%\s*\(',
            r'execute\s*\(["\'].*?\+',
        ],
        'java': [
            r'executeQuery\s*\(["\'].*?\+',
            r'prepareStatement\s*\(["\'].*?\+',
        ]
    }
    
    issues = []
    stack = detect_stack(codebase)
    
    for pattern in patterns.get(stack, []):
        matches = grep_pattern(codebase, pattern)
        for match in matches:
            issues.append({
                'type': 'sql_injection',
                'severity': 'critical',
                'file': match['file'],
                'line': match['line'],
                'owasp': 'A03:2021',
                'cwe': 'CWE-89',
                'cvss': 9.8
            })
    
    return issues
```

### 2. Healthcare Compliance (NEN7510)

**Access Control Requirements**
```python
def verify_nen7510_access_control(codebase):
    """Verify NEN7510 Requirement 9 - Access Control"""
    
    compliance = {
        'user_authentication': check_authentication(codebase),
        'role_based_access': check_rbac(codebase),
        'session_management': check_session_security(codebase),
        'password_policy': check_password_requirements(codebase),
        'account_lockout': check_lockout_mechanism(codebase)
    }
    
    score = sum(1 for v in compliance.values() if v['compliant']) / len(compliance) * 100
    
    return {
        'requirement': 'NEN7510-9 Access Control',
        'score': score,
        'compliant': score >= 90,  # Must meet 90% for compliance
        'details': compliance,
        'gaps': [k for k, v in compliance.items() if not v['compliant']]
    }

def check_authentication(codebase):
    """Check authentication implementation"""
    
    # Look for authentication logic
    has_auth = any([
        find_pattern(codebase, 'Authenticate'),
        find_pattern(codebase, 'Login'),
        find_pattern(codebase, 'SignIn')
    ])
    
    if not has_auth:
        return {'compliant': False, 'issue': 'No authentication found'}
    
    # Check for weak authentication
    weak_patterns = [
        'password.*==.*Request',  # Direct password comparison
        'MD5.*password',          # Weak hashing
    ]
    
    has_weak = any(find_pattern(codebase, p) for p in weak_patterns)
    
    return {
        'compliant': has_auth and not has_weak,
        'method': 'detected' if has_auth else 'missing',
        'strength': 'weak' if has_weak else 'acceptable'
    }
```

**Data Protection Requirements**
```python
def verify_nen7510_data_protection(codebase):
    """Verify NEN7510 Requirement 10 - Data Protection"""
    
    compliance = {
        'encryption_at_rest': check_encryption_at_rest(codebase),
        'encryption_in_transit': check_encryption_in_transit(codebase),
        'data_minimization': check_data_minimization(codebase),
        'pseudonymization': check_pseudonymization(codebase),
        'retention_policy': check_retention_policy(codebase)
    }
    
    return {
        'requirement': 'NEN7510-10 Data Protection',
        'score': calculate_compliance_score(compliance),
        'details': compliance
    }

def check_encryption_at_rest(codebase):
    """Check if sensitive data is encrypted at rest"""
    
    # Find database connections
    db_configs = find_database_configs(codebase)
    
    for config in db_configs:
        # Check for encryption settings
        if 'encrypt' not in config.lower() or 'tde' not in config.lower():
            return {
                'compliant': False,
                'issue': 'Database encryption not configured',
                'location': config['file']
            }
    
    return {'compliant': True}
```

**Audit & Logging Requirements**
```python
def verify_nen7510_audit_logging(codebase):
    """Verify NEN7510 Requirement 11 - Audit & Logging"""
    
    required_events = [
        'login_success',
        'login_failure',
        'logout',
        'data_access',
        'data_modification',
        'permission_change',
        'admin_action'
    ]
    
    logged_events = []
    
    for event in required_events:
        if has_logging_for_event(codebase, event):
            logged_events.append(event)
    
    coverage = len(logged_events) / len(required_events) * 100
    
    return {
        'requirement': 'NEN7510-11 Audit & Logging',
        'coverage': coverage,
        'compliant': coverage >= 90,
        'logged_events': logged_events,
        'missing_events': [e for e in required_events if e not in logged_events]
    }
```

### 3. ISO27001 Control Verification
```python
def verify_iso27001_controls(codebase):
    """Verify key ISO27001 controls"""
    
    controls = {
        'A.9': verify_access_control(codebase),
        'A.10': verify_cryptography(codebase),
        'A.12': verify_operations_security(codebase),
        'A.14': verify_secure_development(codebase)
    }
    
    return {
        'standard': 'ISO27001:2013',
        'controls_checked': len(controls),
        'controls_passed': sum(1 for c in controls.values() if c['implemented']),
        'compliance_percentage': calculate_percentage(controls),
        'details': controls
    }

def verify_access_control(codebase):
    """Verify ISO27001 A.9 - Access Control"""
    
    subclauses = {
        'A.9.1.1': check_access_control_policy(codebase),
        'A.9.2.1': check_user_registration(codebase),
        'A.9.2.3': check_privileged_access(codebase),
        'A.9.4.1': check_access_restriction(codebase)
    }
    
    return {
        'control': 'A.9 Access Control',
        'implemented': all(s['implemented'] for s in subclauses.values()),
        'subclauses': subclauses
    }
```

### 4. GDPR Compliance Verification
```python
def verify_gdpr_compliance(codebase):
    """Verify GDPR data subject rights implementation"""
    
    rights = {
        'right_to_access': check_data_export(codebase),           # Art. 15
        'right_to_rectification': check_data_update(codebase),   # Art. 16
        'right_to_erasure': check_data_deletion(codebase),       # Art. 17
        'right_to_portability': check_data_portability(codebase) # Art. 20
    }
    
    # Check for consent mechanism
    consent = check_consent_mechanism(codebase)
    
    # Check for data breach notification
    breach_notification = check_breach_notification(codebase)
    
    return {
        'regulation': 'GDPR',
        'data_subject_rights': rights,
        'consent_mechanism': consent,
        'breach_notification': breach_notification,
        'compliant': all([
            all(r['implemented'] for r in rights.values()),
            consent['implemented'],
            breach_notification['implemented']
        ])
    }

def check_data_export(codebase):
    """Check if user can export their data (Art. 15)"""
    
    export_endpoints = find_patterns(codebase, [
        'export.*user.*data',
        'download.*profile',
        'get.*my.*data'
    ])
    
    return {
        'implemented': len(export_endpoints) > 0,
        'endpoints': export_endpoints,
        'format': check_export_format(export_endpoints)  # Should be machine-readable
    }
```

### 5. Dependency Vulnerability Scanning
```python
def scan_dependencies(codebase, stack):
    """Scan dependencies for known vulnerabilities"""
    
    scanners = {
        'dotnet': scan_nuget_packages,
        'java': scan_maven_dependencies,
        'python': scan_pip_packages,
        'nodejs': scan_npm_packages
    }
    
    scanner = scanners.get(stack)
    if not scanner:
        return {'error': f'No scanner for stack: {stack}'}
    
    vulnerabilities = scanner(codebase)
    
    # Enrich with CVE data
    enriched = []
    for vuln in vulnerabilities:
        cve_data = fetch_cve_data(vuln['cve_id'])
        enriched.append({
            **vuln,
            'cvss_score': cve_data['cvss'],
            'exploitability': cve_data['exploitability'],
            'patch_available': check_patch_available(vuln['package'], vuln['version'])
        })
    
    return {
        'total_vulnerabilities': len(enriched),
        'by_severity': categorize_by_severity(enriched),
        'vulnerabilities': enriched
    }

def scan_nuget_packages(codebase):
    """Scan .NET NuGet packages"""
    
    result = subprocess.run(
        ['dotnet', 'list', 'package', '--vulnerable', '--include-transitive', '--format', 'json'],
        cwd=codebase,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return []
    
    data = json.loads(result.stdout)
    vulnerabilities = []
    
    for project in data.get('projects', []):
        for framework in project.get('frameworks', []):
            for vuln in framework.get('topLevelPackages', []):
                if 'vulnerabilities' in vuln:
                    vulnerabilities.extend(vuln['vulnerabilities'])
    
    return vulnerabilities
```

### 6. Risk Prioritization
```python
def prioritize_vulnerabilities(vulnerabilities):
    """Prioritize vulnerabilities by risk score"""
    
    for vuln in vulnerabilities:
        # Calculate risk score
        risk_score = calculate_risk_score(
            severity=vuln['severity'],
            exploitability=vuln.get('exploitability', 'medium'),
            impact=vuln.get('impact', 'medium'),
            age_days=vuln.get('age_days', 0),
            patch_available=vuln.get('patch_available', False)
        )
        
        vuln['risk_score'] = risk_score
        vuln['priority'] = categorize_priority(risk_score)
    
    # Sort by risk score (highest first)
    return sorted(vulnerabilities, key=lambda v: v['risk_score'], reverse=True)

def calculate_risk_score(severity, exploitability, impact, age_days, patch_available):
    """
    Risk Score = (Severity × 10) + (Exploitability × 7) + (Impact × 8) + (Age × 2) - (Patch × 5)
    """
    
    severity_scores = {'critical': 10, 'high': 7, 'medium': 5, 'low': 3}
    exploit_scores = {'easy': 10, 'medium': 7, 'difficult': 3}
    impact_scores = {'critical': 10, 'high': 8, 'medium': 5, 'low': 3}
    
    age_penalty = min(age_days / 30, 10)  # 1 point per month, max 10
    patch_bonus = 5 if patch_available else 0
    
    score = (
        severity_scores.get(severity, 5) * 10 +
        exploit_scores.get(exploitability, 7) * 7 +
        impact_scores.get(impact, 5) * 8 +
        age_penalty * 2 -
        patch_bonus
    )
    
    return max(0, min(score, 300))  # Clamp to 0-300

def categorize_priority(risk_score):
    """Categorize by priority level"""
    if risk_score >= 250:
        return 'P0-Critical'
    elif risk_score >= 200:
        return 'P1-High'
    elif risk_score >= 150:
        return 'P2-Medium'
    else:
        return 'P3-Low'
```

---

## Usage Examples

### Example 1: Basic Security Scan
```python
from security_scan import scan_codebase

# Scan for vulnerabilities
results = scan_codebase(
    path='./my-app',
    stack='python',
    checks=['owasp', 'dependencies']
)

print(f"Vulnerabilities: {results['total_vulnerabilities']}")
print(f"Critical: {results['by_severity']['critical']}")
```

### Example 2: Healthcare Compliance Check
```python
from security_scan import verify_healthcare_compliance

# Check NEN7510 compliance
compliance = verify_healthcare_compliance(
    codebase='./healthcare-app',
    standards=['nen7510', 'iso27001', 'gdpr']
)

print(f"NEN7510: {compliance['nen7510']['score']}%")
print(f"ISO27001: {compliance['iso27001']['compliance_percentage']}%")
print(f"GDPR: {'Compliant' if compliance['gdpr']['compliant'] else 'Non-compliant'}")
```

### Example 3: Prioritized Vulnerability Report
```python
from security_scan import generate_vulnerability_report

# Generate prioritized report
report = generate_vulnerability_report(
    codebase='./app',
    format='markdown',
    include_remediation=True
)

# Outputs: SECURITY-REPORT.md with prioritized findings
```

---

## Integration Points

### With code-analysis Skill
```python
# Combined analysis
results = {
    'quality': code_analysis.analyze(codebase),
    'security': security_scan.scan(codebase)
}

# Calculate overall health score
health_score = (
    results['quality']['score'] * 0.6 +
    results['security']['score'] * 0.4
)
```

### With MarQed.ai Workflows
```yaml
workflow_integration:
  analyze_workflow:
    - phase: "Phase 4 - Security & Compliance"
      uses: security-scan skill
      outputs:
        - vulnerability_report
        - compliance_status
        - prioritized_findings
```

---

## Best Practices

### 1. Scan Frequently
```bash
# Daily automated scans
0 2 * * * /usr/local/bin/security-scan --quick

# Pre-deployment comprehensive scan
security-scan --deep --compliance-check --export-report
```

### 2. Prioritize Fixes

Focus on:
1. **P0 (Critical)**: Fix immediately (< 24h)
2. **P1 (High)**: Fix this sprint (< 1 week)
3. **P2 (Medium)**: Plan for next quarter
4. **P3 (Low)**: Backlog

### 3. Track Remediation
```python
# Track vulnerability lifecycle
vulnerability_tracking = {
    'SEC-001': {
        'discovered': '2026-01-23',
        'severity': 'critical',
        'status': 'fixed',
        'fixed_date': '2026-01-24',
        'time_to_fix': '24h'
    }
}
```

---

## Output Formats

### Security Report Structure
```markdown
# Security Scan Report

## Executive Summary
- **Scan Date**: 2026-01-23
- **Total Vulnerabilities**: 15
- **Critical**: 2
- **High**: 5
- **Medium**: 6
- **Low**: 2

## OWASP Top 10 Status
- ✅ A01: Broken Access Control - No issues
- ❌ A02: Cryptographic Failures - 2 critical issues
- ❌ A03: Injection - 1 high issue
- ✅ A04-A10: No issues

## Healthcare Compliance
- **NEN7510**: 85% compliant (3 gaps)
- **ISO27001**: 92% compliant (2 gaps)
- **GDPR**: Compliant

## Priority Actions
1. **P0**: Fix SQL injection in UserService (24h)
2. **P0**: Replace MD5 password hashing (24h)
3. **P1**: Add NEN7510 audit logging (1 week)

[... detailed findings ...]
```

---

## Troubleshooting

### Scanner Not Detecting Issues
```python
# Increase scan depth
scan_codebase(
    path='./app',
    depth='deep',
    custom_rules='./security-rules.yml'
)
```

### False Positives
```python
# Configure whitelist
configure_scan(
    whitelist_patterns=[
        'test/*',           # Ignore test code
        '*/migrations/*'    # Ignore migrations
    ],
    false_positive_threshold=0.3
)
```

---

**Skill Version**: 2.0  
**Last Updated**: January 23, 2026  
**Maintained By**: MarQed.ai B.V.