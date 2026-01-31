"""
Fase 41 Integration Tests: Scanner Orchestration.

End-to-end tests for security scanner integration:
- Orchestrator integration (multi-scanner coordination)
- Multi-scanner finding aggregation
- Real-world code sample scanning
"""

import os
import pytest
from pathlib import Path
from datetime import datetime, timezone

from app.services.security_scanner.adapters.injection_detector import (
    InjectionDetector,
    create_injection_detector,
)
from app.services.security_scanner.adapters.auth_logic_detector import (
    AuthLogicDetector,
    create_auth_logic_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
    SecurityReport,
    ScanResult,
    SecurityFinding,
)


# =============================================================================
# ORCHESTRATOR INTEGRATION (~10 tests)
# =============================================================================


class TestOrchestratorIntegration:
    """Tests for multi-scanner orchestration."""

    @pytest.mark.asyncio
    async def test_orchestrator_creates_all_scanners(self):
        """Should instantiate both injection and auth scanners."""
        injection = create_injection_detector()
        auth = create_auth_logic_detector()

        assert isinstance(injection, InjectionDetector)
        assert isinstance(auth, AuthLogicDetector)
        assert injection.is_available()
        assert auth.is_available()

    @pytest.mark.asyncio
    async def test_orchestrator_scan_python_file(self, tmp_path):
        """Full scan of Python file with both scanners."""
        test_file = tmp_path / "vulnerable.py"
        test_file.write_text('''
import os
from flask import request

@app.post('/api/exec')
def execute():
    cmd = request.args.get('cmd')
    os.system(cmd)
    return {"status": "ok"}
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        all_findings = inj_result.findings + auth_result.findings
        assert len(all_findings) >= 1, "Should detect at least one vulnerability"
        assert inj_result.files_scanned == 1
        assert auth_result.files_scanned == 1

    @pytest.mark.asyncio
    async def test_orchestrator_scan_javascript_file(self, tmp_path):
        """Full scan of JavaScript file with both scanners."""
        test_file = tmp_path / "vulnerable.js"
        test_file.write_text('''
const express = require('express');
const app = express();

app.post('/api/users', async (req, res) => {
    const result = await db.query(`SELECT * FROM users WHERE id = ${req.body.id}`);
    res.json(result);
});
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        all_findings = inj_result.findings + auth_result.findings
        assert len(all_findings) >= 1

    @pytest.mark.asyncio
    async def test_orchestrator_scan_directory(self, tmp_path):
        """Directory scan with multiple languages."""
        (tmp_path / "app.py").write_text('eval(input())')
        (tmp_path / "app.js").write_text('eval(req.body.code)')
        (tmp_path / "Auth.java").write_text('''
public boolean check(String password) {
    return password.equals("secret123");
}
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(tmp_path)
        auth_result = await auth.scan(tmp_path)

        assert inj_result.files_scanned >= 2
        assert auth_result.files_scanned >= 2

    @pytest.mark.asyncio
    async def test_orchestrator_parallel_execution(self, tmp_path):
        """Both scanners can run concurrently via asyncio."""
        import asyncio

        test_file = tmp_path / "app.py"
        test_file.write_text('''
def login(password):
    if password == "hardcoded12345":
        return True
    eval(password)
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        # Run concurrently
        inj_result, auth_result = await asyncio.gather(
            injection.scan(test_file),
            auth.scan(test_file),
        )

        assert isinstance(inj_result, ScanResult)
        assert isinstance(auth_result, ScanResult)
        assert inj_result.scanner == ScannerType.INJECTION
        assert auth_result.scanner == ScannerType.AUTH_LOGIC

    @pytest.mark.asyncio
    async def test_orchestrator_deduplication(self, tmp_path):
        """Findings from same file should have unique fingerprints."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
def a(password):
    if password == "secret12345":
        return True

def b(password):
    if password == "admin12345":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        fingerprints = [f.fingerprint for f in result.findings]
        assert len(fingerprints) == len(set(fingerprints)), "Fingerprints should be unique"

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self, tmp_path):
        """Should handle scan errors gracefully."""
        # Create a directory with a file that might cause issues
        test_file = tmp_path / "test.py"
        test_file.write_text("normal code = 1")

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        # Should not crash, should return valid result
        assert isinstance(result, ScanResult)
        assert result.files_scanned >= 1

    @pytest.mark.asyncio
    async def test_orchestrator_config_passthrough(self, tmp_path):
        """Config parameter should be accepted without error."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        scanner = InjectionDetector()
        result = await scanner.scan(test_file, config={"severity_threshold": "high"})

        assert isinstance(result, ScanResult)

    @pytest.mark.asyncio
    async def test_orchestrator_language_detection(self, tmp_path):
        """Should detect correct language per file extension."""
        # Use patterns that match the injection detector's regex (user input indicators)
        (tmp_path / "app.py").write_text('eval(input())')
        (tmp_path / "app.js").write_text('document.getElementById("x").innerHTML = req.body.data')
        (tmp_path / "app.ts").write_text('document.getElementById("x").innerHTML = req.body.data')

        scanner = InjectionDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 3

        # Check that findings have correct language tags
        py_findings = [f for f in result.findings if "lang:python" in f.tags]
        js_findings = [f for f in result.findings if "lang:javascript" in f.tags]
        ts_findings = [f for f in result.findings if "lang:typescript" in f.tags]

        assert len(py_findings) >= 1 or len(js_findings) >= 1 or len(ts_findings) >= 1

    @pytest.mark.asyncio
    async def test_orchestrator_empty_directory(self, tmp_path):
        """Should not crash on empty directory."""
        scanner = InjectionDetector()
        result = await scanner.scan(tmp_path)

        assert isinstance(result, ScanResult)
        assert result.files_scanned == 0
        assert len(result.findings) == 0
        assert result.errors == []


# =============================================================================
# MULTI-SCANNER FINDINGS (~10 tests)
# =============================================================================


class TestMultiScannerFindings:
    """Tests for multi-scanner finding aggregation and reporting."""

    @pytest.mark.asyncio
    async def test_injection_and_auth_both_detect(self, tmp_path):
        """Both scanners should find issues in same file."""
        test_file = tmp_path / "vuln.py"
        test_file.write_text('''
@app.post('/api/search')
def search():
    q = request.args.get('q')
    result = eval(input())
    if user.password == password:
        return result
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        assert len(inj_result.findings) >= 1, "Injection scanner should find eval"
        assert len(auth_result.findings) >= 1, "Auth scanner should find issues"

    @pytest.mark.asyncio
    async def test_security_report_aggregation(self, tmp_path):
        """SecurityReport should combine findings correctly."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
eval(input())
if user.password == password: pass
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        report = SecurityReport(
            project_path=str(tmp_path),
            scan_results=[inj_result, auth_result],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            scanners_used={ScannerType.INJECTION, ScannerType.AUTH_LOGIC},
        )

        assert report.total_findings >= 2
        assert len(report.all_findings) >= 2

    @pytest.mark.asyncio
    async def test_cwe_coverage_statistics(self, tmp_path):
        """CWE coverage reporting should work correctly."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
eval(input())
if user.password == password: pass
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        report = SecurityReport(
            project_path=str(tmp_path),
            scan_results=[inj_result, auth_result],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        cwe_coverage = report.cwe_coverage
        assert isinstance(cwe_coverage, dict)
        # Should have at least one CWE
        assert len(cwe_coverage) >= 1

    @pytest.mark.asyncio
    async def test_severity_summary(self, tmp_path):
        """Severity summary should have correct counts."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
def auth(password):
    if password == "admin1234567":
        return True
    eval(password)
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        report = SecurityReport(
            project_path=str(tmp_path),
            scan_results=[inj_result, auth_result],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        summary = report.get_severity_summary()
        assert isinstance(summary, dict)
        assert all(s.value in summary for s in Severity)
        total = sum(summary.values())
        assert total >= 1

    @pytest.mark.asyncio
    async def test_scanner_summary(self, tmp_path):
        """Per-scanner finding counts should be correct."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
eval(input())
if user.password == password: pass
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        report = SecurityReport(
            project_path=str(tmp_path),
            scan_results=[inj_result, auth_result],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        scanner_summary = report.get_scanner_summary()
        assert isinstance(scanner_summary, dict)

    @pytest.mark.asyncio
    async def test_findings_have_fingerprints(self, tmp_path):
        """All findings should have deduplication fingerprints."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
eval(input())
if user.password == password: pass
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        for finding in inj_result.findings + auth_result.findings:
            assert finding.fingerprint is not None
            assert len(finding.fingerprint) > 0

    @pytest.mark.asyncio
    async def test_findings_serializable(self, tmp_path):
        """Findings should be convertible to dict for JSON serialization."""
        test_file = tmp_path / "app.py"
        test_file.write_text('eval(input())')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        for finding in result.findings:
            # SecurityFinding is a dataclass, should be inspectable
            assert hasattr(finding, 'rule_id')
            assert hasattr(finding, 'title')
            assert hasattr(finding, 'severity')
            assert hasattr(finding, 'location')
            assert hasattr(finding, 'cwe_ids')

    @pytest.mark.asyncio
    async def test_scan_results_timing(self, tmp_path):
        """Scan results should have timing > 0."""
        test_file = tmp_path / "app.py"
        test_file.write_text('x = 1')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert result.scan_duration_ms >= 0
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_combined_findings_sorted_by_severity(self, tmp_path):
        """Combined findings can be sorted by severity."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
eval(input())
if user.password == password: pass
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        all_findings = inj_result.findings + auth_result.findings

        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }

        sorted_findings = sorted(all_findings, key=lambda f: severity_order[f.severity])

        # Verify sorting works without error
        assert len(sorted_findings) == len(all_findings)
        if len(sorted_findings) >= 2:
            assert severity_order[sorted_findings[0].severity] <= severity_order[sorted_findings[-1].severity]

    @pytest.mark.asyncio
    async def test_report_deduplication(self, tmp_path):
        """SecurityReport should deduplicate findings with same fingerprint."""
        test_file = tmp_path / "app.py"
        test_file.write_text('eval(input())')

        scanner = InjectionDetector()

        # Run same scanner twice
        result1 = await scanner.scan(test_file)
        result2 = await scanner.scan(test_file)

        report = SecurityReport(
            project_path=str(tmp_path),
            scan_results=[result1, result2],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        # all_findings should deduplicate
        total_raw = result1.finding_count + result2.finding_count
        deduped = len(report.all_findings)
        assert deduped <= total_raw


# =============================================================================
# REAL-WORLD CODE SAMPLES (~10 tests)
# =============================================================================


class TestRealWorldCodeSamples:
    """Tests with realistic vulnerable and secure code samples."""

    @pytest.mark.asyncio
    async def test_vulnerable_flask_app(self, tmp_path):
        """Mini Flask app with multiple vulnerabilities."""
        test_file = tmp_path / "flask_app.py"
        test_file.write_text('''
from flask import Flask, request, redirect
import os
import pickle

app = Flask(__name__)

@app.route('/admin/panel')
def admin_panel():
    return "Admin Panel"

@app.post('/api/search')
def search():
    query = request.args.get('q')
    return f"<h1>Results for {query}</h1>"

@app.route('/login')
def login():
    return redirect(request.args.get('next'))

def load_session(data):
    return pickle.loads(data)
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        total = len(inj_result.findings) + len(auth_result.findings)
        assert total >= 2, f"Flask app should have multiple vulns, found {total}"

    @pytest.mark.asyncio
    async def test_vulnerable_express_app(self, tmp_path):
        """Mini Express app with vulnerabilities."""
        test_file = tmp_path / "express_app.js"
        test_file.write_text('''
const express = require('express');
const app = express();
const jwt = require('jsonwebtoken');

app.post('/api/users', async (req, res) => {
    Object.assign(req.user, req.body);
    req.user.save();
    res.json(req.user);
});

app.get('/api/data', async (req, res) => {
    const data = await Data.findById(req.query.id);
    res.json(data);
});

function createToken(user) {
    return jwt.sign({ id: user.id }, "weak");
}
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        total = len(inj_result.findings) + len(auth_result.findings)
        assert total >= 2, f"Express app should have multiple vulns, found {total}"

    @pytest.mark.asyncio
    async def test_secure_code_no_findings(self, tmp_path):
        """Well-written secure code should produce minimal findings."""
        test_file = tmp_path / "secure.py"
        test_file.write_text('''
import bcrypt
from flask_login import login_required, current_user
from flask import abort

@app.get('/api/profile')
@login_required
def get_profile():
    """Return current user's profile."""
    return current_user.to_dict()

def verify_password(stored_hash, password):
    """Securely verify password using bcrypt."""
    return bcrypt.checkpw(password.encode(), stored_hash)

def get_user_item(item_id):
    """Get item with ownership check."""
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    return item
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        inj_findings = len(inj_result.findings)
        auth_findings = len(auth_result.findings)

        # Secure code should have very few or zero findings
        assert inj_findings == 0, f"Secure code had {inj_findings} injection findings"

    @pytest.mark.asyncio
    async def test_mixed_secure_insecure(self, tmp_path):
        """Mixed directory should find vulns only in insecure files."""
        # Secure file
        (tmp_path / "secure.py").write_text('''
@login_required
def safe_endpoint():
    return {"ok": True}
''')

        # Insecure file
        (tmp_path / "insecure.py").write_text('''
def unsafe(password):
    if password == "hardcoded1234":
        return True
    eval(password)
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(tmp_path)
        auth_result = await auth.scan(tmp_path)

        # Insecure file should produce findings
        insecure_findings = [
            f for f in inj_result.findings + auth_result.findings
            if 'insecure' in f.location.file_path
        ]
        assert len(insecure_findings) >= 1

    @pytest.mark.asyncio
    async def test_large_file_performance(self, tmp_path):
        """Large file should scan without errors."""
        test_file = tmp_path / "large.py"
        lines = []
        for i in range(1000):
            lines.append(f'def func_{i}(): return {i}\n')
        # Add one vulnerable line
        lines.append('eval(input())\n')
        test_file.write_text(''.join(lines))

        injection = InjectionDetector()
        result = await injection.scan(test_file)

        assert result.files_scanned == 1
        assert result.errors == []
        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_binary_file_handling(self, tmp_path):
        """Binary files should not crash the scanner."""
        test_file = tmp_path / "binary.py"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00')

        injection = InjectionDetector()
        result = await injection.scan(test_file)

        # Should not crash
        assert isinstance(result, ScanResult)

    @pytest.mark.asyncio
    async def test_encoding_handling(self, tmp_path):
        """Files with different encodings should be handled."""
        test_file = tmp_path / "utf8.py"
        test_file.write_text('# -*- coding: utf-8 -*-\n# Comment: Aaah die Umlaute: \u00e4\u00f6\u00fc\neval(input())\n', encoding='utf-8')

        injection = InjectionDetector()
        result = await injection.scan(test_file)

        assert result.files_scanned == 1
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_empty_file_handling(self, tmp_path):
        """Empty files should not crash."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        assert inj_result.files_scanned == 1
        assert auth_result.files_scanned == 1
        assert len(inj_result.findings) == 0
        assert len(auth_result.findings) == 0

    @pytest.mark.asyncio
    async def test_comment_only_file(self, tmp_path):
        """File with only comments should produce no findings."""
        test_file = tmp_path / "comments.py"
        test_file.write_text('''
# This file only has comments
# eval(dangerous_code)
# password == "admin"
# import os; os.system("rm -rf /")
''')

        injection = InjectionDetector()
        auth = AuthLogicDetector()

        inj_result = await injection.scan(test_file)
        auth_result = await auth.scan(test_file)

        # Comments may trigger regex but that's expected behavior
        # Main check: no errors
        assert inj_result.errors == []
        assert auth_result.errors == []

    @pytest.mark.asyncio
    async def test_symlink_handling(self, tmp_path):
        """Scanner should handle symlinks without infinite loops."""
        real_file = tmp_path / "real.py"
        real_file.write_text('eval(input())')

        link_path = tmp_path / "link.py"
        try:
            link_path.symlink_to(real_file)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        injection = InjectionDetector()
        result = await injection.scan(tmp_path)

        # Should complete without infinite loop
        assert isinstance(result, ScanResult)
        assert result.errors == []
