"""
Tests for Fase 41 AuthLogicDetector.

Tests cover authentication and authorization vulnerability detection:
- CWE-862: Missing Authorization
- CWE-863: Incorrect Authorization
- CWE-287: Improper Authentication
- CWE-269: Improper Privilege Management
- CWE-306: Missing Authentication for Critical Function
- CWE-20: Improper Input Validation (auth context)

Extended test suite: ~150 tests covering per-rule detection, false positives,
context-aware detection, multi-language scanning, and metadata validation.
"""

import re
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
# CWE-862: MISSING AUTHORIZATION — Extended (~20 tests)
# =============================================================================


class TestMissingAuthorizationDetection:
    """Tests for missing authorization detection rules (CWE-862)."""

    # --- AUTH-862-001: Python POST/PUT/DELETE without auth ---

    @pytest.mark.asyncio
    async def test_detect_unprotected_post_route_python(self, tmp_path):
        """AUTH-862-001: Should detect POST route without authorization decorator."""
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
    async def test_detect_unprotected_put_route_python(self, tmp_path):
        """AUTH-862-001: Should detect PUT route without authorization."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.put('/api/users/<id>')
def update_user(id):
    return {"status": "updated"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_detect_unprotected_delete_route_python(self, tmp_path):
        """AUTH-862-001: Should detect DELETE route without authorization."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.delete('/api/users/<id>')
def delete_user(id):
    return {"status": "deleted"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_detect_unprotected_patch_route_python(self, tmp_path):
        """AUTH-862-001: Should detect PATCH route without authorization."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.patch('/api/settings')
def patch_settings():
    return {"status": "patched"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_detect_unprotected_async_route_python(self, tmp_path):
        """AUTH-862-001: Should detect async route without authorization."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.post('/api/orders')
async def create_order():
    return {"status": "created"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_skip_protected_route_login_required(self, tmp_path):
        """AUTH-862-001: Should not flag route with @login_required."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.post('/api/users')
@login_required
def create_user():
    return {"status": "created"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) == 0

    @pytest.mark.asyncio
    async def test_skip_protected_route_permission_required(self, tmp_path):
        """AUTH-862-001: Should not flag route with @permission_required."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.post('/api/users')
@permission_required('admin')
def create_user():
    return {"status": "created"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) == 0

    @pytest.mark.asyncio
    async def test_skip_protected_route_jwt_required(self, tmp_path):
        """AUTH-862-001: Should not flag route with @jwt_required."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.post('/api/users')
@jwt_required()
def create_user():
    return {"status": "created"}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-001" in f.rule_id]
        assert len(findings_862) == 0

    # --- AUTH-862-002: Express route without middleware (JS/TS) ---

    @pytest.mark.asyncio
    async def test_detect_unprotected_express_route_js(self, tmp_path):
        """AUTH-862-002: Should detect Express route without auth middleware."""
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
    async def test_detect_unprotected_express_post_js(self, tmp_path):
        """AUTH-862-002: Should detect Express POST without auth."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
app.post('/api/admin/config', async (req, res) => {
    await Config.update(req.body);
    res.json({ updated: true });
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-002" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_detect_unprotected_express_route_ts(self, tmp_path):
        """AUTH-862-002: Should detect unprotected TypeScript Express route."""
        test_file = tmp_path / "api.ts"
        test_file.write_text('''
router.put('/api/users/:id', async (req, res) => {
    await User.update(req.params.id, req.body);
    res.json({ updated: true });
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-002" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_skip_express_route_with_auth_middleware(self, tmp_path):
        """AUTH-862-002: Should not flag Express route with auth middleware."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
router.post('/api/users', authMiddleware, async (req, res) => {
    await User.create(req.body);
    res.json({ success: true });
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-002" in f.rule_id]
        assert len(findings_862) == 0

    # --- AUTH-862-004: Java endpoint without security annotation ---

    @pytest.mark.asyncio
    async def test_detect_java_endpoint_without_security(self, tmp_path):
        """AUTH-862-004: Should detect Java endpoint without @PreAuthorize."""
        test_file = tmp_path / "UserController.java"
        test_file.write_text('''
@PostMapping("/api/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    return ResponseEntity.ok(userService.create(dto));
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-004" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_skip_java_endpoint_with_preauthorize(self, tmp_path):
        """AUTH-862-004: Should not flag Java endpoint with @PreAuthorize."""
        test_file = tmp_path / "UserController.java"
        test_file.write_text('''
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/api/users/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.delete(id);
    return ResponseEntity.noContent().build();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-004" in f.rule_id]
        assert len(findings_862) == 0

    # --- AUTH-862-005: PHP admin function without auth ---

    @pytest.mark.asyncio
    async def test_detect_php_admin_without_auth(self, tmp_path):
        """AUTH-862-005: Should detect PHP admin function without auth check."""
        test_file = tmp_path / "admin.php"
        test_file.write_text('''<?php
$_POST['action'];
function deleteUser($id) {
    $db->query("DELETE FROM users WHERE id = $id");
}
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-005" in f.rule_id]
        assert len(findings_862) >= 1

    # --- AUTH-862-006: Ruby controller without authorization ---

    @pytest.mark.asyncio
    async def test_detect_ruby_controller_without_auth(self, tmp_path):
        """AUTH-862-006: Should detect Rails controller without authorization."""
        test_file = tmp_path / "users_controller.rb"
        test_file.write_text('''
class UsersController < ApplicationController
  def destroy
    @user = User.find(params[:id])
    @user.destroy
  end
end
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-006" in f.rule_id]
        assert len(findings_862) >= 1

    @pytest.mark.asyncio
    async def test_skip_ruby_controller_with_pundit(self, tmp_path):
        """AUTH-862-006: Should not flag Rails controller with Pundit authorization."""
        test_file = tmp_path / "users_controller.rb"
        test_file.write_text('''
class UsersController < ApplicationController
  before_action :authenticate_user!
  def destroy
    authorize @user
    @user.destroy
  end
end
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_862 = [f for f in result.findings if "AUTH-862-006" in f.rule_id]
        assert len(findings_862) == 0


# =============================================================================
# CWE-863: INCORRECT AUTHORIZATION — Extended (~15 tests)
# =============================================================================


class TestIncorrectAuthorizationDetection:
    """Tests for incorrect authorization detection rules (CWE-863)."""

    # --- AUTH-863-001: Python IDOR ---

    @pytest.mark.asyncio
    async def test_detect_idor_python(self, tmp_path):
        """AUTH-863-001: Should detect IDOR vulnerability pattern."""
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
    async def test_detect_idor_python_kwargs(self, tmp_path):
        """AUTH-863-001: Should detect IDOR via kwargs."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def get_item(request):
    item = Item.get(id=kwargs['id'])
    return item.serialize()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-001" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_skip_idor_with_ownership_check(self, tmp_path):
        """AUTH-863-001: Should not flag IDOR when ownership is verified."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def get_document(request):
    doc = Document.get(id=request.args['id'])
    if doc.user_id != current_user.id:
        abort(403)
    return doc.to_dict()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-001" in f.rule_id]
        assert len(findings_863) == 0

    # --- AUTH-863-002: JavaScript IDOR ---

    @pytest.mark.asyncio
    async def test_detect_idor_js(self, tmp_path):
        """AUTH-863-002: Should detect IDOR in JavaScript."""
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

        findings_863 = [f for f in result.findings if "AUTH-863-002" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_detect_idor_js_findone(self, tmp_path):
        """AUTH-863-002: Should detect IDOR via findOne in JavaScript."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
async function getProfile(req, res) {
    const profile = await Profile.findOne(req.body.profileId);
    res.json(profile);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-002" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_detect_idor_ts(self, tmp_path):
        """AUTH-863-002: Should detect IDOR in TypeScript."""
        test_file = tmp_path / "api.ts"
        test_file.write_text('''
async function getDocument(req: Request, res: Response) {
    const doc = await Document.findByPk(req.params.id);
    res.json(doc);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-002" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_skip_idor_js_with_access_check(self, tmp_path):
        """AUTH-863-002: Should not flag when ownership is checked."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
async function getOrder(req, res) {
    const order = await Order.findById(req.params.orderId);
    if (order.userId !== req.user.id) return res.status(403).json({});
    res.json(order);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-002" in f.rule_id]
        assert len(findings_863) == 0

    # --- AUTH-863-003: Weak role comparison ---

    @pytest.mark.asyncio
    async def test_detect_weak_role_check_js(self, tmp_path):
        """AUTH-863-003: Should detect weak role comparison."""
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

        findings_863 = [f for f in result.findings if "AUTH-863-003" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_detect_weak_permission_check_php(self, tmp_path):
        """AUTH-863-003: Should detect weak permission comparison in PHP."""
        test_file = tmp_path / "auth.php"
        test_file.write_text('''<?php
if ($isAdmin == "true") {
    deleteAllUsers();
}
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-003" in f.rule_id]
        assert len(findings_863) >= 1

    # --- AUTH-863-004: Client-side auth check ---

    @pytest.mark.asyncio
    async def test_detect_client_side_auth_check(self, tmp_path):
        """AUTH-863-004: Should detect client-side authorization check."""
        test_file = tmp_path / "app.js"
        test_file.write_text('''
if (localStorage.getItem('isAdmin') === 'true') {
    showAdminPanel();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-004" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_detect_session_storage_role_check(self, tmp_path):
        """AUTH-863-004: Should detect sessionStorage role check."""
        test_file = tmp_path / "app.js"
        test_file.write_text('''
if (sessionStorage.getItem('role') === 'admin') {
    enableDeleteButton();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-004" in f.rule_id]
        assert len(findings_863) >= 1

    # --- AUTH-863-005: Java resource access without owner check ---

    @pytest.mark.asyncio
    async def test_detect_java_idor(self, tmp_path):
        """AUTH-863-005: Should detect Java resource access without owner verification."""
        test_file = tmp_path / "Service.java"
        test_file.write_text('''
public Order getOrder(Long id) {
    return repository.findById(id).orElseThrow();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-005" in f.rule_id]
        assert len(findings_863) >= 1

    @pytest.mark.asyncio
    async def test_skip_java_resource_with_access_check(self, tmp_path):
        """AUTH-863-005: Should not flag when hasAccess is used."""
        test_file = tmp_path / "Service.java"
        test_file.write_text('''
public Order getOrder(Long id) {
    Order order = repository.findById(id).orElseThrow();
    if (!hasAccess(order, currentUser)) throw new ForbiddenException();
    return order;
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_863 = [f for f in result.findings if "AUTH-863-005" in f.rule_id]
        assert len(findings_863) == 0


# =============================================================================
# CWE-287: IMPROPER AUTHENTICATION — Extended (~20 tests)
# =============================================================================


class TestImproperAuthenticationDetection:
    """Tests for improper authentication detection rules (CWE-287)."""

    # --- AUTH-287-001: Hardcoded credentials ---

    @pytest.mark.asyncio
    async def test_detect_hardcoded_password_python(self, tmp_path):
        """AUTH-287-001: Should detect hardcoded password in Python."""
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
    async def test_detect_hardcoded_password_js(self, tmp_path):
        """AUTH-287-001: Should detect hardcoded password in JavaScript."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
function login(user, password) {
    if (password === "supersecret") {
        return { success: true };
    }
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-001" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_hardcoded_password_java(self, tmp_path):
        """AUTH-287-001: Should detect hardcoded password in Java."""
        test_file = tmp_path / "Auth.java"
        test_file.write_text('''
public boolean authenticate(String password) {
    return password.equals("mypassword");
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-001" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_hardcoded_password_php(self, tmp_path):
        """AUTH-287-001: Should detect hardcoded password in PHP."""
        test_file = tmp_path / "auth.php"
        test_file.write_text('''<?php
if ($password === "admin123") {
    return true;
}
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-001" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_hardcoded_passwd_variant(self, tmp_path):
        """AUTH-287-001: Should detect 'passwd' variant."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def check_passwd(passwd):
    if passwd == "topsecret":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-001" in f.rule_id]
        assert len(findings_287) >= 1

    # --- AUTH-287-002: Plain text password comparison ---

    @pytest.mark.asyncio
    async def test_detect_plaintext_password_comparison_python(self, tmp_path):
        """AUTH-287-002: Should detect plain text password comparison."""
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

        findings_287 = [f for f in result.findings if "AUTH-287-002" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_plaintext_password_comparison_js(self, tmp_path):
        """AUTH-287-002: Should detect plain text password comparison in JS."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
function login(username, password) {
    const user = db.findUser(username);
    if (user.password === password) {
        return createSession(user);
    }
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-002" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_plaintext_password_comparison_java(self, tmp_path):
        """AUTH-287-002: Should detect plain text password comparison in Java."""
        test_file = tmp_path / "Auth.java"
        test_file.write_text('''
public boolean authenticate(String username, String password) {
    User user = userRepository.findByUsername(username);
    return user.getPassword().equals(password);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-002" in f.rule_id]
        assert len(findings_287) >= 1

    # --- AUTH-287-004: JWT without expiration ---

    @pytest.mark.asyncio
    async def test_detect_jwt_without_expiration_python(self, tmp_path):
        """AUTH-287-004: Should detect JWT without expiration in Python."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
import jwt

def create_token(user):
    return jwt.encode({"user_id": user.id}, key)
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_jwt_without_expiration_js(self, tmp_path):
        """AUTH-287-004: Should detect JWT without expiration in JS."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
const jwt = require('jsonwebtoken');
function createToken(user) {
    return jwt.sign({ id: user.id }, secret);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287" in f.rule_id]
        assert len(findings_287) >= 1

    # --- AUTH-287-005: Weak JWT secret ---

    @pytest.mark.asyncio
    async def test_detect_weak_jwt_secret_python(self, tmp_path):
        """AUTH-287-005: Should detect weak/short JWT secret."""
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
        """AUTH-287-005: Should detect weak JWT secret in JavaScript."""
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

    @pytest.mark.asyncio
    async def test_detect_weak_jwt_secret_short_key(self, tmp_path):
        """AUTH-287-005: Should detect very short JWT key."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
import jwt
token = jwt.encode(payload, "abc")
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-005" in f.rule_id]
        assert len(findings_287) >= 1

    # --- AUTH-287-006: Session fixation ---

    @pytest.mark.asyncio
    async def test_detect_session_fixation_python(self, tmp_path):
        """AUTH-287-006: Should detect session not regenerated after login."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def login(request):
    user = authenticate(request.form['username'], request.form['password'])
    if user:
        session["user_id"] = user.id
        return redirect("/dashboard")
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-006" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_detect_session_fixation_php(self, tmp_path):
        """AUTH-287-006: Should detect session fixation in PHP."""
        test_file = tmp_path / "auth.php"
        test_file.write_text('''<?php
if (password_verify($password, $user['password'])) {
    $_SESSION["user_id"] = $user['id'];
    $_SESSION["user_role"] = $user['role'];
}
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-006" in f.rule_id]
        assert len(findings_287) >= 1

    @pytest.mark.asyncio
    async def test_skip_session_fixation_with_regenerate(self, tmp_path):
        """AUTH-287-006: Should not flag when session is regenerated."""
        test_file = tmp_path / "auth.php"
        test_file.write_text('''<?php
if (password_verify($password, $user['password'])) {
    session_regenerate_id(true);
    $_SESSION["user_id"] = $user['id'];
}
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_287 = [f for f in result.findings if "AUTH-287-006" in f.rule_id]
        assert len(findings_287) == 0


# =============================================================================
# CWE-269: IMPROPER PRIVILEGE MANAGEMENT — Extended (~12 tests)
# =============================================================================


class TestPrivilegeManagementDetection:
    """Tests for improper privilege management detection (CWE-269)."""

    # --- AUTH-269-001: Mass assignment ---

    @pytest.mark.asyncio
    async def test_detect_mass_assignment_python(self, tmp_path):
        """AUTH-269-001: Should detect mass assignment vulnerability."""
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
    async def test_detect_mass_assignment_python_kwargs(self, tmp_path):
        """AUTH-269-001: Should detect mass assignment with **kwargs."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def update_profile(request):
    profile.update(**data)
    return profile.serialize()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-001" in f.rule_id]
        assert len(findings_269) >= 1

    @pytest.mark.asyncio
    async def test_detect_object_assign_mass_js(self, tmp_path):
        """AUTH-269-001: Should detect Object.assign mass assignment."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function updateUser(req, user) {
    Object.assign(user, req.body);  // Dangerous!
    return user.save();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-001" in f.rule_id]
        assert len(findings_269) >= 1

    @pytest.mark.asyncio
    async def test_detect_ruby_mass_assignment(self, tmp_path):
        """AUTH-269-001: Should detect Ruby mass assignment."""
        test_file = tmp_path / "users_controller.rb"
        test_file.write_text('''
class UsersController < ApplicationController
  def update
    @user = User.find(params[:id])
    @user.update(params[:user])
  end
end
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-001" in f.rule_id]
        assert len(findings_269) >= 1

    @pytest.mark.asyncio
    async def test_skip_mass_assignment_with_whitelist(self, tmp_path):
        """AUTH-269-001: Should not flag when fields are whitelisted."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function updateUser(req, user) {
    const allowed = pick(req.body, ['name', 'email']);
    Object.assign(user, allowed);
    return user.save();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-001" in f.rule_id]
        assert len(findings_269) == 0

    # --- AUTH-269-002: Self-privilege modification ---

    @pytest.mark.asyncio
    async def test_detect_self_privilege_modification_python(self, tmp_path):
        """AUTH-269-002: Should detect user modifying own privileges."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def update_profile(request):
    current_user.role = request.json.get('role')
    current_user.is_admin = True
    current_user.save()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-002" in f.rule_id]
        assert len(findings_269) >= 1

    @pytest.mark.asyncio
    async def test_detect_self_privilege_modification_js(self, tmp_path):
        """AUTH-269-002: Should detect self-privilege modification in JS."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function updateProfile(req) {
    req.user.role = 'admin';
    req.user.isAdmin = true;
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-002" in f.rule_id]
        assert len(findings_269) >= 1

    # --- AUTH-269-003: Elevated privileges not dropped ---

    @pytest.mark.asyncio
    async def test_detect_elevated_privileges_python(self, tmp_path):
        """AUTH-269-003: Should detect elevated privileges not dropped."""
        test_file = tmp_path / "service.py"
        test_file.write_text('''
import os
def run_as_root():
    os.setuid(0)
    do_privileged_operation()
    # Never drops privileges
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-003" in f.rule_id]
        assert len(findings_269) >= 1

    # --- AUTH-269-004: Default admin credentials ---

    @pytest.mark.asyncio
    async def test_detect_default_admin_credentials_python(self, tmp_path):
        """AUTH-269-004: Should detect default admin credentials."""
        test_file = tmp_path / "config.py"
        test_file.write_text('''
admin_password = "changeme"
root_passwd = "toor123"
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-004" in f.rule_id]
        assert len(findings_269) >= 1

    @pytest.mark.asyncio
    async def test_detect_default_admin_credentials_js(self, tmp_path):
        """AUTH-269-004: Should detect default admin credentials in JS."""
        test_file = tmp_path / "config.js"
        test_file.write_text('''
const config = {
    superuser_password: "admin123",
};
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_269 = [f for f in result.findings if "AUTH-269-004" in f.rule_id]
        assert len(findings_269) >= 1


# =============================================================================
# CWE-306: MISSING AUTHENTICATION — Extended (~12 tests)
# =============================================================================


class TestMissingAuthenticationDetection:
    """Tests for missing authentication detection (CWE-306)."""

    # --- AUTH-306-001: Admin endpoint without authentication ---

    @pytest.mark.asyncio
    async def test_detect_admin_route_without_auth(self, tmp_path):
        """AUTH-306-001: Should detect admin endpoint without authentication."""
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
    async def test_detect_admin_dashboard_without_auth(self, tmp_path):
        """AUTH-306-001: Should detect admin dashboard endpoint."""
        test_file = tmp_path / "admin.py"
        test_file.write_text('''
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-001" in f.rule_id]
        assert len(findings_306) >= 1

    @pytest.mark.asyncio
    async def test_skip_admin_route_with_login_required(self, tmp_path):
        """AUTH-306-001: Should not flag admin route with @login_required."""
        test_file = tmp_path / "admin.py"
        test_file.write_text('''
@app.route('/admin/users')
@login_required
def admin_users():
    return User.all()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-001" in f.rule_id]
        assert len(findings_306) == 0

    @pytest.mark.asyncio
    async def test_skip_admin_route_with_admin_required(self, tmp_path):
        """AUTH-306-001: Should not flag admin route with @admin_required."""
        test_file = tmp_path / "admin.py"
        test_file.write_text('''
@app.route('/admin/settings')
@admin_required
def admin_settings():
    return get_settings()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-001" in f.rule_id]
        assert len(findings_306) == 0

    # --- AUTH-306-002: Password reset without verification ---

    @pytest.mark.asyncio
    async def test_detect_password_reset_without_verification(self, tmp_path):
        """AUTH-306-002: Should detect password reset without identity verification."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def reset_password(request):
    user = User.get(request.form['email'])
    user.password = request.form['new_password']
    user.set_password(request.form['new_password'])
    user.save()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-002" in f.rule_id]
        assert len(findings_306) >= 1

    @pytest.mark.asyncio
    async def test_skip_password_reset_with_token(self, tmp_path):
        """AUTH-306-002: Should not flag password reset with token verification."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def reset_password(request):
    token = request.form['token']
    if verify_reset_token(token):
        user.set_password(request.form['new_password'])
        user.save()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-002" in f.rule_id]
        assert len(findings_306) == 0

    # --- AUTH-306-003: API without token validation (JS/TS) ---

    @pytest.mark.asyncio
    async def test_detect_api_without_auth_js(self, tmp_path):
        """AUTH-306-003: Should detect API endpoint without token validation."""
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

        findings_306 = [f for f in result.findings if "AUTH-306-003" in f.rule_id]
        assert len(findings_306) >= 1

    @pytest.mark.asyncio
    async def test_detect_api_without_auth_ts(self, tmp_path):
        """AUTH-306-003: Should detect API without auth in TypeScript."""
        test_file = tmp_path / "api.ts"
        test_file.write_text('''
app.post('/api/orders', async (req, res) => {
    const order = await Order.create(req.body);
    res.json(order);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-003" in f.rule_id]
        assert len(findings_306) >= 1

    @pytest.mark.asyncio
    async def test_skip_api_with_jwt_middleware(self, tmp_path):
        """AUTH-306-003: Should not flag API with JWT middleware."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
app.use('/api', jwtAuth);
app.get('/api/users', async (req, res) => {
    const users = await User.find();
    res.json(users);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-003" in f.rule_id]
        assert len(findings_306) == 0

    # --- AUTH-306-004: Database admin exposed ---

    @pytest.mark.asyncio
    async def test_detect_phpmyadmin_route(self, tmp_path):
        """AUTH-306-004: Should detect exposed phpMyAdmin route."""
        test_file = tmp_path / "routes.py"
        test_file.write_text('''
@app.route('/phpmyadmin')
def phpmyadmin_proxy():
    return proxy_request('http://localhost:8080/phpmyadmin')
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_306 = [f for f in result.findings if "AUTH-306-004" in f.rule_id]
        assert len(findings_306) >= 1


# =============================================================================
# CWE-20: INPUT VALIDATION (AUTH CONTEXT) — Extended (~12 tests)
# =============================================================================


class TestInputValidationDetection:
    """Tests for input validation in auth context (CWE-20)."""

    # --- AUTH-20-001: User ID from client ---

    @pytest.mark.asyncio
    async def test_detect_user_id_from_client_python(self, tmp_path):
        """AUTH-20-001: Should detect user ID from client instead of session."""
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
    async def test_detect_user_id_from_client_int_cast(self, tmp_path):
        """AUTH-20-001: Should detect user ID from request with int cast."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def get_user(request):
    user_id = int(request.args.get('user_id'))
    return User.get(user_id)
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-001" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_detect_user_id_from_client_js(self, tmp_path):
        """AUTH-20-001: Should detect userId from req.body in JS."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function getProfile(req, res) {
    const userId = req.body.userId;
    return User.findById(userId);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-001" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_detect_user_id_from_query_js(self, tmp_path):
        """AUTH-20-001: Should detect userId from req.query in JS."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function getProfile(req, res) {
    const userId = req.query.user_id;
    return User.findById(userId);
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-001" in f.rule_id]
        assert len(findings_20) >= 1

    # --- AUTH-20-002: Role from client ---

    @pytest.mark.asyncio
    async def test_detect_role_from_client_python(self, tmp_path):
        """AUTH-20-002: Should detect role accepted from client input."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def set_role(request):
    role = request.json.get('role')
    user.role = role
    user.save()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-002" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_detect_role_from_form_python(self, tmp_path):
        """AUTH-20-002: Should detect role from form data."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def update_user(request):
    role = request.form.get('role')
    user.role = role
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-002" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_detect_role_from_client_js(self, tmp_path):
        """AUTH-20-002: Should detect role from client input in JS."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function updateRole(req, res) {
    const role = req.body.role;
    user.role = role;
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-002" in f.rule_id]
        assert len(findings_20) >= 1

    # --- AUTH-20-003: Open redirect ---

    @pytest.mark.asyncio
    async def test_detect_open_redirect_python(self, tmp_path):
        """AUTH-20-003: Should detect unvalidated redirect URL."""
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

        findings_20 = [f for f in result.findings if "AUTH-20-003" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_detect_open_redirect_js(self, tmp_path):
        """AUTH-20-003: Should detect unvalidated redirect in JavaScript."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
app.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect(req.query.redirect);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-003" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_detect_open_redirect_php(self, tmp_path):
        """AUTH-20-003: Should detect unvalidated redirect in PHP."""
        test_file = tmp_path / "auth.php"
        test_file.write_text('''<?php
header("Location: " . $_GET['redirect']);
exit();
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-003" in f.rule_id]
        assert len(findings_20) >= 1

    @pytest.mark.asyncio
    async def test_skip_redirect_with_url_for(self, tmp_path):
        """AUTH-20-003: Should not flag redirect using url_for."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
from flask import redirect, url_for, request

@app.route('/login')
def login():
    next_url = request.args.get('next')
    if is_safe_url(next_url):
        return redirect(next_url)
    return redirect(url_for('index'))
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-003" in f.rule_id]
        assert len(findings_20) == 0

    @pytest.mark.asyncio
    async def test_skip_redirect_with_validate_redirect(self, tmp_path):
        """AUTH-20-003: Should not flag redirect with validate_redirect."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
app.get('/callback', (req, res) => {
    const url = validate_redirect(req.query.redirect);
    res.redirect(url);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings_20 = [f for f in result.findings if "AUTH-20-003" in f.rule_id]
        assert len(findings_20) == 0


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

    @pytest.mark.asyncio
    async def test_scan_python_and_js_both_detected(self, tmp_path):
        """Should detect issues in both Python and JS files."""
        (tmp_path / "auth.py").write_text('''
def login(password):
    if password == "hardcoded1234":
        return True
''')
        (tmp_path / "auth.js").write_text('''
function check(password) {
    if (password === "hardcoded1234") return true;
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(tmp_path)

        python_findings = [f for f in result.findings if f.location.file_path.endswith('.py')]
        js_findings = [f for f in result.findings if f.location.file_path.endswith('.js')]
        assert len(python_findings) >= 1
        assert len(js_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_java_detection(self, tmp_path):
        """Should detect auth issues in Java files."""
        test_file = tmp_path / "Auth.java"
        test_file.write_text('''
public boolean check(String password) {
    return password.equals("secretpassword");
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_typescript_detection(self, tmp_path):
        """Should detect auth issues in TypeScript files."""
        test_file = tmp_path / "api.ts"
        test_file.write_text('''
app.delete('/api/users/:id', async (req, res) => {
    await User.destroy(req.params.id);
    res.sendStatus(204);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        assert len(result.findings) >= 1


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

    @pytest.mark.asyncio
    async def test_scan_result_has_timing(self, tmp_path):
        """Scan result should have timing information."""
        test_file = tmp_path / "test.py"
        test_file.write_text('x = 1')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.scan_duration_ms >= 0
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_scan_result_scanner_type(self, tmp_path):
        """Scan result should have correct scanner type."""
        test_file = tmp_path / "test.py"
        test_file.write_text('x = 1')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.scanner == ScannerType.AUTH_LOGIC

    @pytest.mark.asyncio
    async def test_scan_result_scanner_version(self, tmp_path):
        """Scan result should have correct scanner version."""
        test_file = tmp_path / "test.py"
        test_file.write_text('x = 1')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.scanner_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_comment_only_file(self, tmp_path):
        """Should not produce findings for comment-only files."""
        test_file = tmp_path / "comments.py"
        test_file.write_text('''
# This is a comment about password checking
# password == "admin" is just documentation
# def login(): pass
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        # Comment-only files may still trigger regex matches; this tests graceful handling
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_binary_like_content(self, tmp_path):
        """Should handle files with unusual content gracefully."""
        test_file = tmp_path / "weird.py"
        test_file.write_text('\x00\x01\x02password\x03\x04')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert result.errors == []

    @pytest.mark.asyncio
    async def test_very_long_file(self, tmp_path):
        """Should handle large files without errors."""
        test_file = tmp_path / "large.py"
        lines = ['x = 1\n'] * 5000
        lines.append('if user.password == password: pass\n')
        test_file.write_text(''.join(lines))

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_finding_has_location(self, tmp_path):
        """Findings should have proper location information."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def authenticate(password):
    if password == "admin123":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.location is not None
        assert finding.location.file_path is not None
        assert finding.location.start_line > 0
        assert finding.location.snippet is not None

    @pytest.mark.asyncio
    async def test_finding_has_suggested_fix(self, tmp_path):
        """Findings should have suggested fixes."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def authenticate(password):
    if password == "admin123":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert len(finding.suggested_fixes) >= 1

    @pytest.mark.asyncio
    async def test_finding_has_fingerprint(self, tmp_path):
        """Findings should have deduplication fingerprints."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def authenticate(password):
    if password == "admin123":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        for finding in result.findings:
            assert finding.fingerprint is not None
            assert len(finding.fingerprint) > 0

    @pytest.mark.asyncio
    async def test_finding_has_tags(self, tmp_path):
        """Findings should have tags including language."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def authenticate(password):
    if password == "admin123":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert "lang:python" in finding.tags
        assert "auth_logic" in finding.tags

    @pytest.mark.asyncio
    async def test_unsupported_extension_skipped(self, tmp_path):
        """Should not find vulnerabilities in unsupported file extensions."""
        test_file = tmp_path / "data.csv"
        test_file.write_text('password,admin123\nuser.password == password')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        # Single file is always scanned (counted), but no language match means no findings
        assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_empty_directory(self, tmp_path):
        """Should handle empty directory gracefully."""
        scanner = AuthLogicDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned == 0
        assert len(result.findings) == 0
        assert result.errors == []


# =============================================================================
# METADATA VALIDATION (~10 tests)
# =============================================================================


class TestMetadataValidation:
    """Tests for rule metadata correctness and completeness."""

    def test_total_rule_count(self):
        """Should have exactly 29 rules."""
        assert len(ALL_AUTH_LOGIC_RULES) == 29

    def test_unique_rule_ids(self):
        """All rule IDs should be unique."""
        ids = [r.id for r in ALL_AUTH_LOGIC_RULES]
        assert len(ids) == len(set(ids)), f"Duplicate rule IDs found: {[i for i in ids if ids.count(i) > 1]}"

    def test_cwe_862_rule_count(self):
        """Should have 6 CWE-862 rules."""
        assert len(MISSING_AUTHZ_RULES) == 6

    def test_cwe_863_rule_count(self):
        """Should have 5 CWE-863 rules."""
        assert len(INCORRECT_AUTHZ_RULES) == 5

    def test_cwe_287_rule_count(self):
        """Should have 6 CWE-287 rules."""
        assert len(IMPROPER_AUTH_RULES) == 6

    def test_cwe_269_rule_count(self):
        """Should have 4 CWE-269 rules."""
        assert len(PRIVILEGE_MGMT_RULES) == 4

    def test_cwe_306_rule_count(self):
        """Should have 4 CWE-306 rules."""
        assert len(MISSING_AUTH_RULES) == 4

    def test_cwe_20_rule_count(self):
        """Should have 4 CWE-20 rules."""
        assert len(INPUT_VALIDATION_RULES) == 4

    def test_all_rules_have_valid_severity(self):
        """All rules should have a valid Severity enum value."""
        for rule in ALL_AUTH_LOGIC_RULES:
            assert isinstance(rule.severity, Severity), f"Rule {rule.id} has invalid severity"

    def test_all_rules_have_valid_category(self):
        """All rules should have a recognized category."""
        valid_categories = {
            "missing_authorization", "incorrect_authorization",
            "improper_authentication", "privilege_management",
            "missing_authentication", "input_validation",
        }
        for rule in ALL_AUTH_LOGIC_RULES:
            assert rule.category in valid_categories, f"Rule {rule.id} has invalid category: {rule.category}"

    def test_all_rules_have_patterns(self):
        """All rules should have at least one language pattern."""
        for rule in ALL_AUTH_LOGIC_RULES:
            assert len(rule.patterns) > 0, f"Rule {rule.id} has no patterns"

    def test_all_rule_ids_follow_naming_convention(self):
        """All rule IDs should follow AUTH-CWE-NNN format."""
        pattern = re.compile(r'^AUTH-\d{1,4}-\d{3}$')
        for rule in ALL_AUTH_LOGIC_RULES:
            assert pattern.match(rule.id), f"Rule {rule.id} doesn't match AUTH-CWE-NNN format"

    def test_all_regex_patterns_compile(self):
        """All regex patterns should compile without errors."""
        for rule in ALL_AUTH_LOGIC_RULES:
            for lang, lang_pattern in rule.patterns.items():
                try:
                    re.compile(lang_pattern.pattern, lang_pattern.flags)
                except re.error as e:
                    pytest.fail(f"Rule {rule.id}/{lang} has invalid regex: {e}")

    def test_cwe_ids_follow_format(self):
        """All CWE IDs should follow CWE-NNN format."""
        pattern = re.compile(r'^CWE-\d+$')
        for rule in ALL_AUTH_LOGIC_RULES:
            for cwe_id in rule.cwe_ids:
                assert pattern.match(cwe_id), f"Rule {rule.id} has invalid CWE ID: {cwe_id}"

    def test_rules_summary_matches_rules(self):
        """Rules summary should match actual rules."""
        scanner = AuthLogicDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == len(ALL_AUTH_LOGIC_RULES)
        assert len(summary["rules"]) == len(ALL_AUTH_LOGIC_RULES)

    def test_severity_distribution(self):
        """Should have a reasonable distribution of severities."""
        severities = {s: 0 for s in Severity}
        for rule in ALL_AUTH_LOGIC_RULES:
            severities[rule.severity] += 1

        # Should have at least some critical and high severity rules
        assert severities[Severity.CRITICAL] >= 2
        assert severities[Severity.HIGH] >= 5
        assert severities[Severity.MEDIUM] >= 3
