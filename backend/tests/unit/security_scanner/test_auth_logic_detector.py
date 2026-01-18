"""
Tests for Fase 41 AuthLogicDetector.

Tests cover authentication and authorization vulnerability detection:
- CWE-862: Missing Authorization
- CWE-863: Incorrect Authorization
- CWE-287: Improper Authentication
- CWE-269: Improper Privilege Management
- CWE-306: Missing Authentication for Critical Function
- CWE-20: Improper Input Validation (auth context)
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.auth_logic_detector import (
    AuthLogicDetector,
    AuthLogicRule,
    ALL_AUTH_LOGIC_RULES,
    MISSING_AUTHZ_RULES,
    INCORRECT_AUTHZ_RULES,
    IMPROPER_AUTH_RULES,
    PRIVILEGE_MGMT_RULES,
    MISSING_AUTH_RULES,
    INPUT_VALIDATION_RULES,
    create_auth_logic_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestAuthLogicDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = AuthLogicDetector()
        assert scanner.scanner_type == ScannerType.AUTH_LOGIC

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = AuthLogicDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = AuthLogicDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_expected_rules(self):
        """Should have expected number of auth logic detection rules."""
        assert len(ALL_AUTH_LOGIC_RULES) >= 25

    def test_supported_languages(self):
        """Should support expected languages."""
        scanner = AuthLogicDetector()
        languages = scanner.supported_languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "python" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "php" in languages
        assert "ruby" in languages
        assert "go" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = AuthLogicDetector()
        extensions = scanner.supported_extensions
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".py" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions
        assert ".php" in extensions
        assert ".rb" in extensions
        assert ".go" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_auth_logic_detector()
        assert isinstance(scanner, AuthLogicDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in ALL_AUTH_LOGIC_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in ALL_AUTH_LOGIC_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_target_cwes(self):
        """Should cover the target CWEs for Fase 41 Tier 3."""
        cwe_coverage = set()
        for rule in ALL_AUTH_LOGIC_RULES:
            cwe_coverage.update(rule.cwe_ids)

        # Auth and AuthZ CWEs
        assert "CWE-862" in cwe_coverage, "CWE-862 (Missing Authorization) not covered"
        assert "CWE-863" in cwe_coverage, "CWE-863 (Incorrect Authorization) not covered"
        assert "CWE-287" in cwe_coverage, "CWE-287 (Improper Authentication) not covered"
        assert "CWE-269" in cwe_coverage, "CWE-269 (Improper Privilege Management) not covered"
        assert "CWE-306" in cwe_coverage, "CWE-306 (Missing Authentication) not covered"


# =============================================================================
# CWE-862: MISSING AUTHORIZATION
# =============================================================================


class TestMissingAuthorizationDetection:
    """Tests for missing authorization detection rules."""

    @pytest.mark.asyncio
    async def test_detect_unprotected_post_route_python(self, tmp_path):
        """Should detect POST route without authorization decorator."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from flask import Flask
app = Flask(__name__)

@app.post('/api/users')
def create_user():
    # No authorization check
    return {"status": "created"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "862" in f.rule_id), None)
        assert finding is not None
        assert "CWE-862" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_unprotected_express_route_js(self, tmp_path):
        """Should detect Express route without auth middleware."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
const express = require('express');
const router = express.Router();

router.delete('/api/users/:id', async (req, res) => {
    await User.deleteOne({ _id: req.params.id });
    res.json({ success: true });
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "862" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_skip_protected_route_python(self, tmp_path):
        """Should not flag route with @login_required decorator."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.post('/api/users')
@login_required
def create_user():
    return {"status": "created"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        # Should be filtered out as false positive
        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) == 0


# =============================================================================
# CWE-863: INCORRECT AUTHORIZATION
# =============================================================================


class TestIncorrectAuthorizationDetection:
    """Tests for incorrect authorization detection rules."""

    @pytest.mark.asyncio
    async def test_detect_idor_python(self, tmp_path):
        """Should detect IDOR vulnerability pattern."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def get_document(request):
    doc = Document.get(id=request.args['id'])  # Direct access without verification
    return doc.to_dict()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "863" in f.rule_id), None)
        assert finding is not None
        assert "CWE-863" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_idor_js(self, tmp_path):
        """Should detect IDOR in JavaScript."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
async function getOrder(req, res) {
    const order = await Order.findById(req.params.orderId);
    // No check if order belongs to user
    res.json(order);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_weak_role_check_js(self, tmp_path):
        """Should detect weak role comparison."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
function checkAdmin(user) {
    if (user.role == "admin") {  // Weak comparison
        return true;
    }
    return false;
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CWE-287: IMPROPER AUTHENTICATION
# =============================================================================


class TestImproperAuthenticationDetection:
    """Tests for improper authentication detection rules."""

    @pytest.mark.asyncio
    async def test_detect_hardcoded_password_python(self, tmp_path):
        """Should detect hardcoded password comparison."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def authenticate(username, password):
    if password == "admin123":
        return True
    return False
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "287" in f.rule_id), None)
        assert finding is not None
        assert "CWE-287" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_plaintext_password_comparison_python(self, tmp_path):
        """Should detect plain text password comparison."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def login(username, password):
    user = User.get(username)
    if user.password == password:  # Plaintext comparison!
        return create_session(user)
    return None
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_weak_jwt_secret_python(self, tmp_path):
        """Should detect weak/short JWT secret."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
import jwt

def create_token(user):
    return jwt.encode({"user_id": user.id}, "secret")
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_weak_jwt_secret_js(self, tmp_path):
        """Should detect weak JWT secret in JavaScript."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
const jwt = require('jsonwebtoken');

function generateToken(user) {
    return jwt.sign({ userId: user.id }, "mysecret");
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CWE-269: IMPROPER PRIVILEGE MANAGEMENT
# =============================================================================


class TestPrivilegeManagementDetection:
    """Tests for improper privilege management detection."""

    @pytest.mark.asyncio
    async def test_detect_mass_assignment_python(self, tmp_path):
        """Should detect mass assignment vulnerability."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def update_user(request):
    user = User.get(request.user.id)
    user.update(**request.json)  # Mass assignment!
    return user.to_dict()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "269" in f.rule_id), None)
        assert finding is not None
        assert "CWE-269" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_object_assign_mass_js(self, tmp_path):
        """Should detect Object.assign mass assignment."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function updateUser(req, user) {
    Object.assign(user, req.body);  // Dangerous!
    return user.save();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_self_privilege_modification_python(self, tmp_path):
        """Should detect user modifying own privileges."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def update_profile(request):
    current_user.role = request.json.get('role')
    current_user.is_admin = True
    current_user.save()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CWE-306: MISSING AUTHENTICATION FOR CRITICAL FUNCTION
# =============================================================================


class TestMissingAuthenticationDetection:
    """Tests for missing authentication detection."""

    @pytest.mark.asyncio
    async def test_detect_admin_route_without_auth(self, tmp_path):
        """Should detect admin endpoint without authentication."""
        test_file = tmp_path / "admin.py"
        test_file.write_text('''
@app.route('/admin/users')
def admin_users():
    return User.all()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "306" in f.rule_id), None)
        assert finding is not None
        assert "CWE-306" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_api_without_auth_js(self, tmp_path):
        """Should detect API endpoint without token validation."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
const express = require('express');
const app = express();

app.get('/api/users', async (req, res) => {
    const users = await User.find();
    res.json(users);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CWE-20: IMPROPER INPUT VALIDATION (AUTH CONTEXT)
# =============================================================================


class TestInputValidationDetection:
    """Tests for input validation in auth context."""

    @pytest.mark.asyncio
    async def test_detect_user_id_from_client_python(self, tmp_path):
        """Should detect user ID from client instead of session."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def get_profile(request):
    user_id = request.args.get('user_id')
    return User.get(user_id)
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "20" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_role_from_client_python(self, tmp_path):
        """Should detect role accepted from client input."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def set_role(request):
    role = request.json.get('role')
    user.role = role
    user.save()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_open_redirect_python(self, tmp_path):
        """Should detect unvalidated redirect URL."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
from flask import redirect, request

@app.route('/login')
def login():
    # After login, redirect to user-provided URL
    return redirect(request.args.get('next'))
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_open_redirect_js(self, tmp_path):
        """Should detect unvalidated redirect in JavaScript."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
app.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect(req.query.redirect);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# MULTI-LANGUAGE TESTS
# =============================================================================


class TestMultiLanguageSupport:
    """Tests for multi-language support."""

    @pytest.mark.asyncio
    async def test_scan_multiple_languages(self, tmp_path):
        """Should scan multiple language files correctly."""
        # Python auth issue
        (tmp_path / "auth.py").write_text('if user.password == password: pass')
        # JavaScript auth issue
        (tmp_path / "auth.js").write_text('if (user.role == "admin") { }')
        # PHP auth issue
        (tmp_path / "auth.php").write_text('<?php if ($password === "admin123") { } ?>')
        # Ignored file
        (tmp_path / "readme.txt").write_text('password == admin')

        scanner = AuthLogicDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned == 3  # Only code files
        assert len(result.findings) >= 2


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and false positive handling."""

    @pytest.mark.asyncio
    async def test_empty_file(self, tmp_path):
        """Should handle empty files gracefully."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        assert len(result.findings) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_get_rules_summary(self):
        """Should return correct rules summary."""
        scanner = AuthLogicDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] >= 25
        assert len(summary["rules"]) >= 25
        assert "CWE-862" in summary["cwe_coverage"]
        assert "CWE-863" in summary["cwe_coverage"]
        assert "CWE-287" in summary["cwe_coverage"]

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan all files in directory."""
        (tmp_path / "auth1.py").write_text('if user.password == password: pass')
        (tmp_path / "auth2.js").write_text('jwt.sign(payload, "weak")')

        scanner = AuthLogicDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned == 2
        assert len(result.findings) >= 2
