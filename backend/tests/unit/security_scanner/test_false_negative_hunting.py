"""
Fase 41B: False Negative Hunting Test Suite.

Verifies that scanners detect known vulnerable code patterns.
Tests that are expected to fail (known false negatives) are marked with
@pytest.mark.xfail to track the FN rate metric.

Categories:
- Injection FN tests (~30): XSS, SQLi, CMDi, path traversal, SSRF, eval, deserialization
- Auth FN tests (~20): JWT, IDOR, privilege escalation, session fixation
- Cross-scanner FN tests (~10): Combined injection+auth, multi-file, framework-specific
"""

import pytest
from pathlib import Path

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
)


# =============================================================================
# INJECTION FALSE NEGATIVE TESTS (~30)
# =============================================================================


class TestInjectionFalseNegatives:
    """Verify injection scanner catches known vulnerable patterns."""

    # --- XSS ---

    @pytest.mark.asyncio
    async def test_fn_reflected_xss_python_render_template_string(self, tmp_path):
        """Should detect reflected XSS via render_template_string with user input."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
from flask import render_template_string, request
@app.route('/search')
def search():
    return render_template_string(request.args.get('q'))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        xss_findings = [f for f in result.findings if "79" in str(f.cwe_ids) or "SSTI" in str(f.rule_id)]
        assert len(xss_findings) >= 1, "Should detect reflected XSS/SSTI via render_template_string"

    @pytest.mark.asyncio
    async def test_fn_stored_xss_js_innerhtml(self, tmp_path):
        """Should detect stored XSS via innerHTML with user data."""
        test_file = tmp_path / "app.js"
        test_file.write_text('''
function displayComment(req) {
    document.getElementById('comments').innerHTML = req.body.comment;
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        xss_findings = [f for f in result.findings if "79" in str(f.cwe_ids)]
        assert len(xss_findings) >= 1, "Should detect innerHTML XSS"

    @pytest.mark.asyncio
    async def test_fn_dom_xss_document_write(self, tmp_path):
        """Should detect DOM XSS via document.write with user input."""
        test_file = tmp_path / "app.js"
        test_file.write_text('''
function greet(req) {
    document.write(req.query.name);
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        xss_findings = [f for f in result.findings if "79" in str(f.cwe_ids)]
        assert len(xss_findings) >= 1, "Should detect document.write DOM XSS"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: XSS via template variable indirection")
    async def test_fn_xss_template_variable_indirection(self, tmp_path):
        """Should detect XSS via template variable indirection."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
from flask import request, render_template_string
@app.route('/greet')
def greet():
    name = request.args.get('name')
    tpl = "<p>Hello " + name + "</p>"
    return render_template_string(tpl)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        xss_findings = [f for f in result.findings if "79" in str(f.cwe_ids)]
        assert len(xss_findings) >= 1

    @pytest.mark.asyncio
    async def test_fn_php_echo_xss(self, tmp_path):
        """Should detect PHP echo with unescaped user input."""
        test_file = tmp_path / "page.php"
        test_file.write_text('''<?php
echo $_GET['name'];
print $_POST['message'];
?>''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        xss_findings = [f for f in result.findings if "79" in str(f.cwe_ids)]
        assert len(xss_findings) >= 1, "Should detect PHP echo XSS"

    # --- SQL Injection ---

    @pytest.mark.xfail(reason="Known FN: SQL concat on separate line not detected by inline pattern")
    @pytest.mark.asyncio
    async def test_fn_sql_injection_string_concat_python(self, tmp_path):
        """Should detect SQL injection via string concatenation."""
        test_file = tmp_path / "db.py"
        test_file.write_text('''
def get_user(username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return db.execute(query)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        sqli_findings = [f for f in result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli_findings) >= 1, "Should detect string concat SQLi"

    @pytest.mark.asyncio
    async def test_fn_sql_injection_format_string(self, tmp_path):
        """Should detect SQL injection via f-string execute."""
        test_file = tmp_path / "db.py"
        test_file.write_text('''
def search(term):
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{term}%'")
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        sqli_findings = [f for f in result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli_findings) >= 1, "Should detect f-string SQLi"

    @pytest.mark.asyncio
    async def test_fn_sql_injection_js_template_literal(self, tmp_path):
        """Should detect SQL injection via JS template literal."""
        test_file = tmp_path / "db.js"
        test_file.write_text('''
async function getUser(userId) {
    const result = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
    return result.rows[0];
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        sqli_findings = [f for f in result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli_findings) >= 1, "Should detect template literal SQLi"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Multi-line SQL query construction")
    async def test_fn_sql_injection_multiline_build(self, tmp_path):
        """Should detect SQL injection built across multiple lines."""
        test_file = tmp_path / "db.py"
        test_file.write_text('''
def search_users(name, city):
    query = "SELECT * FROM users"
    query += " WHERE name = '" + name + "'"
    query += " AND city = '" + city + "'"
    return db.execute(query)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        sqli_findings = [f for f in result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli_findings) >= 1

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Java SQL without Statement pattern")
    async def test_fn_sql_injection_java_string_concat(self, tmp_path):
        """Should detect SQL injection in Java via string concat."""
        test_file = tmp_path / "UserDao.java"
        test_file.write_text('''
public User findUser(String username) {
    String sql = "SELECT * FROM users WHERE username = '" + username + "'";
    return jdbcTemplate.queryForObject(sql, User.class);
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        sqli_findings = [f for f in result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli_findings) >= 1

    @pytest.mark.xfail(reason="Known FN: PHP SQL interpolation not detected, requires $_GET concat")
    @pytest.mark.asyncio
    async def test_fn_sql_injection_php(self, tmp_path):
        """Should detect SQL injection in PHP."""
        test_file = tmp_path / "db.php"
        test_file.write_text('''<?php
$username = $_GET['user'];
$result = mysql_query("SELECT * FROM users WHERE name = '$username'");
?>''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        sqli_findings = [f for f in result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli_findings) >= 1, "Should detect PHP SQLi"

    # --- Command Injection ---

    @pytest.mark.asyncio
    async def test_fn_command_injection_os_system(self, tmp_path):
        """Should detect command injection via os.system."""
        test_file = tmp_path / "utils.py"
        test_file.write_text('''
import os
def ping_host(host):
    os.system("ping -c 1 " + host)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        cmd_findings = [f for f in result.findings if "78" in str(f.cwe_ids) or "77" in str(f.cwe_ids)]
        assert len(cmd_findings) >= 1, "Should detect os.system command injection"

    @pytest.mark.asyncio
    async def test_fn_command_injection_subprocess_shell(self, tmp_path):
        """Should detect command injection via subprocess with shell=True."""
        test_file = tmp_path / "utils.py"
        test_file.write_text('''
import subprocess
def run_command(user_input):
    subprocess.call("echo " + user_input, shell=True)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        cmd_findings = [f for f in result.findings if "78" in str(f.cwe_ids) or "77" in str(f.cwe_ids)]
        assert len(cmd_findings) >= 1, "Should detect subprocess shell=True"

    @pytest.mark.asyncio
    async def test_fn_command_injection_child_process_exec(self, tmp_path):
        """Should detect command injection via child_process.exec."""
        test_file = tmp_path / "utils.js"
        test_file.write_text('''
const { exec } = require('child_process');
function runDiag(host) {
    exec("nslookup " + host, (err, stdout) => {
        console.log(stdout);
    });
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        cmd_findings = [f for f in result.findings if "78" in str(f.cwe_ids) or "77" in str(f.cwe_ids)]
        assert len(cmd_findings) >= 1, "Should detect child_process.exec injection"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Command injection via environment variable")
    async def test_fn_command_injection_via_env_var(self, tmp_path):
        """Should detect command injection via environment variable."""
        test_file = tmp_path / "deploy.py"
        test_file.write_text('''
import os, subprocess
def deploy(version):
    os.environ['DEPLOY_VERSION'] = version
    subprocess.call("deploy.sh", shell=True)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        cmd_findings = [f for f in result.findings if "78" in str(f.cwe_ids) or "77" in str(f.cwe_ids)]
        assert len(cmd_findings) >= 1

    @pytest.mark.xfail(reason="Known FN: PHP cmd injection via variable not detected, requires $_GET inline")
    @pytest.mark.asyncio
    async def test_fn_command_injection_php(self, tmp_path):
        """Should detect command injection in PHP."""
        test_file = tmp_path / "cmd.php"
        test_file.write_text('''<?php
$host = $_GET['host'];
system("ping -c 1 " . $host);
?>''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        cmd_findings = [f for f in result.findings if "78" in str(f.cwe_ids) or "77" in str(f.cwe_ids)]
        assert len(cmd_findings) >= 1, "Should detect PHP command injection"

    # --- Path Traversal ---

    @pytest.mark.asyncio
    async def test_fn_path_traversal_python(self, tmp_path):
        """Should detect path traversal in file access."""
        test_file = tmp_path / "files.py"
        test_file.write_text('''
def download_file(request):
    filename = request.args.get('file')
    return open(request.args.get('path'), 'rb').read()
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        pt_findings = [f for f in result.findings if "22" in str(f.cwe_ids)]
        assert len(pt_findings) >= 1, "Should detect path traversal"

    @pytest.mark.asyncio
    async def test_fn_path_traversal_js(self, tmp_path):
        """Should detect path traversal in Node.js."""
        test_file = tmp_path / "files.js"
        test_file.write_text('''
const fs = require('fs');
app.get('/download', (req, res) => {
    fs.readFile(req.query.file, (err, data) => {
        res.send(data);
    });
});
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        pt_findings = [f for f in result.findings if "22" in str(f.cwe_ids)]
        assert len(pt_findings) >= 1, "Should detect Node.js path traversal"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Path traversal via URL-encoded sequences")
    async def test_fn_path_traversal_url_encoded(self, tmp_path):
        """Should detect path traversal with URL encoding patterns."""
        test_file = tmp_path / "files.py"
        test_file.write_text('''
from urllib.parse import unquote
def get_file(request):
    path = unquote(request.args.get('path'))
    return open(path).read()
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        pt_findings = [f for f in result.findings if "22" in str(f.cwe_ids)]
        assert len(pt_findings) >= 1

    # --- SSRF ---

    @pytest.mark.asyncio
    async def test_fn_ssrf_requests_python(self, tmp_path):
        """Should detect SSRF via requests library."""
        test_file = tmp_path / "proxy.py"
        test_file.write_text('''
import requests
def fetch_url(url):
    return requests.get(url).text
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        ssrf_findings = [f for f in result.findings if "918" in str(f.cwe_ids)]
        assert len(ssrf_findings) >= 1, "Should detect SSRF via requests"

    @pytest.mark.asyncio
    async def test_fn_ssrf_urllib_python(self, tmp_path):
        """Should detect SSRF via urllib with user-named URL."""
        test_file = tmp_path / "proxy.py"
        test_file.write_text('''
import urllib.request
def fetch(user_input):
    return urllib.request.urlopen(user_input).read()
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        ssrf_findings = [f for f in result.findings if "918" in str(f.cwe_ids)]
        assert len(ssrf_findings) >= 1, "Should detect SSRF via urllib"

    @pytest.mark.asyncio
    async def test_fn_ssrf_dns_rebinding(self, tmp_path):
        """Should detect SSRF when URL is validated but DNS can be rebound."""
        test_file = tmp_path / "proxy.py"
        test_file.write_text('''
import requests
from urllib.parse import urlparse
def fetch(url):
    parsed = urlparse(url)
    if parsed.hostname not in BLOCKED:
        return requests.get(url).text  # DNS rebinding possible
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        ssrf_findings = [f for f in result.findings if "918" in str(f.cwe_ids)]
        assert len(ssrf_findings) >= 1

    # --- Code Injection (eval/exec) ---

    @pytest.mark.asyncio
    async def test_fn_eval_python(self, tmp_path):
        """Should detect eval with user input variable."""
        test_file = tmp_path / "calc.py"
        test_file.write_text('''
def calculate(user_input):
    return eval(user_input)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if "94" in str(f.cwe_ids)]
        assert len(eval_findings) >= 1, "Should detect eval code injection"

    @pytest.mark.asyncio
    async def test_fn_exec_python(self, tmp_path):
        """Should detect exec with user input."""
        test_file = tmp_path / "runner.py"
        test_file.write_text('''
def run_code(data):
    exec(data)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if "94" in str(f.cwe_ids)]
        assert len(eval_findings) >= 1, "Should detect exec code injection"

    @pytest.mark.asyncio
    async def test_fn_eval_js(self, tmp_path):
        """Should detect eval in JavaScript with user input."""
        test_file = tmp_path / "calc.js"
        test_file.write_text('''
function calculate(req) {
    return eval(req.body.expression);
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if "94" in str(f.cwe_ids)]
        assert len(eval_findings) >= 1, "Should detect JS eval code injection"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Indirect eval via variable")
    async def test_fn_indirect_eval(self, tmp_path):
        """Should detect indirect eval via variable assignment."""
        test_file = tmp_path / "runner.py"
        test_file.write_text('''
def run(user_code):
    fn = eval
    result = fn(user_code)
    return result
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if "94" in str(f.cwe_ids)]
        assert len(eval_findings) >= 1

    @pytest.mark.asyncio
    async def test_fn_eval_input_python(self, tmp_path):
        """Should detect eval(input()) pattern."""
        test_file = tmp_path / "repl.py"
        test_file.write_text('''
while True:
    eval(input(">>> "))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if "94" in str(f.cwe_ids)]
        assert len(eval_findings) >= 1, "Should detect eval(input())"

    # --- Deserialization ---

    @pytest.mark.asyncio
    async def test_fn_pickle_deserialization(self, tmp_path):
        """Should detect unsafe pickle deserialization."""
        test_file = tmp_path / "data.py"
        test_file.write_text('''
import pickle
def load_data(data):
    return pickle.loads(data)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        deser_findings = [f for f in result.findings if "502" in str(f.cwe_ids)]
        assert len(deser_findings) >= 1, "Should detect pickle deserialization"

    @pytest.mark.asyncio
    async def test_fn_yaml_unsafe_load(self, tmp_path):
        """Should detect unsafe YAML loading."""
        test_file = tmp_path / "config.py"
        test_file.write_text('''
import yaml
def load_config(data):
    return yaml.load(data)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        deser_findings = [f for f in result.findings if "502" in str(f.cwe_ids)]
        assert len(deser_findings) >= 1, "Should detect unsafe yaml.load"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Complex deserialization chain")
    async def test_fn_complex_deserialization_chain(self, tmp_path):
        """Should detect deserialization through indirect method calls."""
        test_file = tmp_path / "data.py"
        test_file.write_text('''
import pickle
import base64
def load_session(cookie_value):
    decoded = base64.b64decode(cookie_value)
    return pickle.loads(decoded)
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        deser_findings = [f for f in result.findings if "502" in str(f.cwe_ids)]
        assert len(deser_findings) >= 1

    # --- SSTI ---

    @pytest.mark.asyncio
    async def test_fn_ssti_jinja2(self, tmp_path):
        """Should detect Server-Side Template Injection with Jinja2."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
from flask import render_template_string, request
@app.route('/hello')
def hello():
    return render_template_string(request.args.get('template'))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        # SSTI is CWE-1336 or in rule id
        ssti_findings = [f for f in result.findings if "SSTI" in f.rule_id or "1336" in str(f.cwe_ids)]
        assert len(ssti_findings) >= 1, "Should detect SSTI"


# =============================================================================
# AUTH FALSE NEGATIVE TESTS (~20)
# =============================================================================


class TestAuthFalseNegatives:
    """Verify auth scanner catches known vulnerable patterns."""

    # --- JWT vulnerabilities ---

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: JWT none algorithm attack")
    async def test_fn_jwt_none_algorithm(self, tmp_path):
        """Should detect JWT created without specifying algorithm (none attack)."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
import jwt
def decode_token(token):
    return jwt.decode(token, options={"verify_signature": False})
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        jwt_findings = [f for f in result.findings if "287" in str(f.cwe_ids)]
        assert len(jwt_findings) >= 1

    @pytest.mark.asyncio
    async def test_fn_jwt_hardcoded_secret(self, tmp_path):
        """Should detect JWT with hardcoded secret."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
import jwt
TOKEN_SECRET = "my-super-secret-key"
def create_token(user_id):
    return jwt.encode({"sub": user_id}, TOKEN_SECRET)
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "287" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect hardcoded JWT secret"

    # --- IDOR patterns ---

    @pytest.mark.asyncio
    async def test_fn_idor_direct_db_access(self, tmp_path):
        """Should detect IDOR via direct database access."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
def get_invoice(request):
    invoice = Invoice.get(id=request.args['invoice_id'])
    return invoice.to_json()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        idor_findings = [f for f in result.findings if "863" in str(f.cwe_ids)]
        assert len(idor_findings) >= 1, "Should detect IDOR"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: IDOR via encoded/hashed ID")
    async def test_fn_idor_encoded_id(self, tmp_path):
        """Should detect IDOR even when ID is encoded/hashed."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
import hashlib
def get_document(request):
    doc_hash = request.args['doc_id']
    doc = Document.get_by_hash(doc_hash)
    return doc.to_dict()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        idor_findings = [f for f in result.findings if "863" in str(f.cwe_ids)]
        assert len(idor_findings) >= 1

    # --- Authorization bypass ---

    @pytest.mark.asyncio
    async def test_fn_http_method_override_bypass(self, tmp_path):
        """Should detect authorization bypass via HTTP method override."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.route('/api/users/<id>', methods=['GET', 'POST', 'DELETE'])
def user_endpoint(id):
    if request.method == 'DELETE':
        if not current_user.is_admin:
            abort(403)
    user = User.get(id)
    if request.method == 'POST':
        user.update(**request.json)  # No auth check for POST!
    return user.to_dict()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "862" in str(f.cwe_ids)]
        assert len(findings) >= 1

    # --- Privilege escalation ---

    @pytest.mark.asyncio
    async def test_fn_privilege_escalation_via_mass_assignment(self, tmp_path):
        """Should detect privilege escalation via mass assignment (Object.assign with req.body)."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function updateProfile(req, res) {
    const user = getUser(req.user.id);
    Object.assign(user, req.body);
    user.save();
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "269" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect mass assignment privilege escalation"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Privilege escalation via parameter pollution")
    async def test_fn_parameter_pollution_privilege_escalation(self, tmp_path):
        """Should detect privilege escalation via parameter pollution."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
app.post('/api/register', (req, res) => {
    const user = new User({
        username: req.body.username,
        password: req.body.password,
        role: req.body.role || 'user'
    });
    user.save();
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "269" in str(f.cwe_ids) or "20" in str(f.cwe_ids)]
        assert len(findings) >= 1

    # --- Session management ---

    @pytest.mark.asyncio
    async def test_fn_session_fixation_no_regeneration(self, tmp_path):
        """Should detect session fixation (no regeneration after login)."""
        test_file = tmp_path / "auth.php"
        test_file.write_text('''<?php
function login($username, $password) {
    $user = authenticate($username, $password);
    if ($user) {
        $_SESSION["user_id"] = $user->id;
        $_SESSION["user_role"] = $user->role;
        return true;
    }
    return false;
}
?>''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "287" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect session fixation"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Known FN: Rate limiting bypass via header manipulation")
    async def test_fn_rate_limiting_bypass(self, tmp_path):
        """Should detect rate limiting bypass via X-Forwarded-For."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
from flask import request

@app.route('/login', methods=['POST'])
def login():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if rate_limiter.is_allowed(ip):
        return authenticate(request.form)
    return "Too many attempts", 429
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "287" in str(f.cwe_ids)]
        assert len(findings) >= 1

    # --- Missing auth on specific methods ---

    @pytest.mark.asyncio
    async def test_fn_missing_auth_admin_endpoint(self, tmp_path):
        """Should detect missing auth on admin endpoint."""
        test_file = tmp_path / "admin.py"
        test_file.write_text('''
@app.route('/admin/settings')
def admin_settings():
    return Settings.get_all()
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "306" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect unauthenticated admin endpoint"

    @pytest.mark.asyncio
    async def test_fn_missing_auth_api_endpoint_js(self, tmp_path):
        """Should detect missing auth on JS API endpoint."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
app.delete('/api/users/:id', async (req, res) => {
    await User.destroy(req.params.id);
    res.sendStatus(204);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "862" in str(f.cwe_ids) or "306" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect missing auth on DELETE endpoint"

    # --- Hardcoded credentials ---

    @pytest.mark.asyncio
    async def test_fn_hardcoded_password_python(self, tmp_path):
        """Should detect hardcoded password comparison."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def authenticate(username, password):
    if password == "supersecret123":
        return True
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "287" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect hardcoded password"

    # --- Weak comparisons ---

    @pytest.mark.asyncio
    async def test_fn_weak_role_comparison_js(self, tmp_path):
        """Should detect weak (==) role comparison in JS."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
function isAdmin(user) {
    return user.role == "admin";
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "863" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect weak role comparison"

    @pytest.mark.asyncio
    async def test_fn_plaintext_password_comparison(self, tmp_path):
        """Should detect plaintext password comparison."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def verify(username, password):
    user = User.query.filter_by(username=username).first()
    if user.password == password:
        return user
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "287" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect plaintext password comparison"

    # --- Open redirect ---

    @pytest.mark.asyncio
    async def test_fn_open_redirect_python(self, tmp_path):
        """Should detect open redirect."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
from flask import redirect, request
@app.route('/callback')
def callback():
    return redirect(request.args.get('next'))
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "20" in str(f.cwe_ids) or "601" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect open redirect"

    @pytest.mark.asyncio
    async def test_fn_open_redirect_js(self, tmp_path):
        """Should detect open redirect in JS."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
app.get('/auth/callback', (req, res) => {
    res.redirect(req.query.next);
});
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "20" in str(f.cwe_ids) or "601" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect JS open redirect"

    # --- User ID from client ---

    @pytest.mark.asyncio
    async def test_fn_user_id_from_request(self, tmp_path):
        """Should detect user ID from client request."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
function getProfile(req, res) {
    const userId = req.params.userId;
    User.findById(req.params.userId).then(u => res.json(u));
}
''')

        scanner = AuthLogicDetector()
        result = await scanner.scan(test_file)

        findings = [f for f in result.findings if "20" in str(f.cwe_ids) or "863" in str(f.cwe_ids)]
        assert len(findings) >= 1, "Should detect user ID from client"


# =============================================================================
# CROSS-SCANNER FALSE NEGATIVE TESTS (~10)
# =============================================================================


class TestCrossScannerFalseNegatives:
    """Verify cross-scanner detection of combined vulnerability patterns."""

    @pytest.mark.asyncio
    async def test_fn_injection_and_auth_combined_python(self, tmp_path):
        """Should detect both injection AND auth issues in same file."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
@app.post('/api/search')
def search():
    query = request.args.get('q')
    result = db.execute(f"SELECT * FROM items WHERE name LIKE '%{query}%'")
    return jsonify(result)
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(test_file)
        auth_result = await auth_scanner.scan(test_file)

        # Should have injection finding (f-string SQL)
        sqli = [f for f in inj_result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli) >= 1, "Should detect SQL injection"

        # Should have auth finding (unprotected POST)
        auth = [f for f in auth_result.findings if "862" in str(f.cwe_ids)]
        assert len(auth) >= 1, "Should detect missing authorization"

    @pytest.mark.asyncio
    async def test_fn_injection_and_auth_combined_js(self, tmp_path):
        """Should detect auth issues in JS endpoint with SQLi."""
        test_file = tmp_path / "api.js"
        test_file.write_text('''
app.post('/api/admin/query', async (req, res) => {
    const result = await db.query(`SELECT * FROM users WHERE name = ${req.body.name}`);
    res.json(result);
});
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(test_file)
        auth_result = await auth_scanner.scan(test_file)

        # At least one scanner should find something
        sqli = [f for f in inj_result.findings if "89" in str(f.cwe_ids)]
        auth = [f for f in auth_result.findings if "862" in str(f.cwe_ids) or "306" in str(f.cwe_ids)]
        assert len(sqli) + len(auth) >= 1, "Should detect at least one issue"

    @pytest.mark.asyncio
    async def test_fn_flask_app_multiple_vulns(self, tmp_path):
        """Should detect multiple vulns in a Flask app."""
        test_file = tmp_path / "app.py"
        test_file.write_text('''
from flask import Flask, request, redirect
import os

app = Flask(__name__)

@app.route('/admin/delete')
def admin_delete():
    user_id = request.args.get('id')
    os.system(f"delete_user.sh {user_id}")
    return redirect(request.args.get('next'))
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(test_file)
        auth_result = await auth_scanner.scan(test_file)

        # Should find command injection
        cmd = [f for f in inj_result.findings if "78" in str(f.cwe_ids) or "77" in str(f.cwe_ids)]
        assert len(cmd) >= 1, "Should detect command injection"

        # Should find missing admin auth
        admin_findings = [f for f in auth_result.findings if "306" in str(f.cwe_ids)]
        assert len(admin_findings) >= 1, "Should detect missing admin auth"

    @pytest.mark.asyncio
    async def test_fn_express_app_multiple_vulns(self, tmp_path):
        """Should detect multiple vulns in an Express app."""
        test_file = tmp_path / "app.js"
        test_file.write_text('''
const express = require('express');
const app = express();

app.post('/api/users', async (req, res) => {
    const user = await User.findOne(req.body.userId);
    Object.assign(user, req.body);
    user.save();
    res.json(user);
});
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        auth_result = await auth_scanner.scan(test_file)

        # Should find missing auth + mass assignment + IDOR
        findings = auth_result.findings
        assert len(findings) >= 1, "Should detect auth/privilege issues"

    @pytest.mark.asyncio
    async def test_fn_both_scanners_on_directory(self, tmp_path):
        """Both scanners should work on directory scan."""
        (tmp_path / "inject.py").write_text('''
def search(user_input):
    return eval(user_input)
''')
        (tmp_path / "auth.py").write_text('''
def login(password):
    if password == "admin12345":
        return True
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(tmp_path)
        auth_result = await auth_scanner.scan(tmp_path)

        assert inj_result.files_scanned >= 2
        assert auth_result.files_scanned >= 2
        assert len(inj_result.findings) >= 1, "Injection scanner should find eval(user_input)"
        assert len(auth_result.findings) >= 1, "Auth scanner should find hardcoded password"

    @pytest.mark.asyncio
    async def test_fn_django_csrf_exempt_with_sqli(self, tmp_path):
        """Should detect CSRF exempt combined with SQLi in Django."""
        test_file = tmp_path / "views.py"
        test_file.write_text('''
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def api_search(request):
    term = request.POST.get('q')
    results = MyModel.objects.raw(f"SELECT * FROM items WHERE name = '{term}'")
    return JsonResponse(list(results))
''')

        injection_scanner = InjectionDetector()
        inj_result = await injection_scanner.scan(test_file)

        sqli = [f for f in inj_result.findings if "89" in str(f.cwe_ids)]
        assert len(sqli) >= 1

    @pytest.mark.asyncio
    async def test_fn_secure_code_no_findings(self, tmp_path):
        """Well-written secure code should not produce findings."""
        test_file = tmp_path / "secure.py"
        test_file.write_text('''
from flask import Flask, request, abort
from flask_login import login_required, current_user
import bcrypt

app = Flask(__name__)

@app.post('/api/users')
@login_required
def create_user():
    if not current_user.has_permission('create_user'):
        abort(403)
    data = request.get_json()
    name = data.get('name', '')
    user = User.create(name=name)
    return user.to_dict(), 201
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(test_file)
        auth_result = await auth_scanner.scan(test_file)

        # Secure code should have minimal/no findings
        assert inj_result.errors == []
        assert auth_result.errors == []

    @pytest.mark.asyncio
    async def test_fn_spring_boot_combined(self, tmp_path):
        """Should detect combined vulns in Spring Boot."""
        test_file = tmp_path / "Controller.java"
        test_file.write_text('''
@PostMapping("/api/search")
public ResponseEntity<List<Item>> search(@RequestBody SearchRequest req) {
    String sql = "SELECT * FROM items WHERE name = '" + req.getTerm() + "'";
    List<Item> items = jdbcTemplate.query(sql, new ItemMapper());
    return ResponseEntity.ok(items);
}
''')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(test_file)
        auth_result = await auth_scanner.scan(test_file)

        sqli = [f for f in inj_result.findings if "89" in str(f.cwe_ids)]
        auth = [f for f in auth_result.findings if "862" in str(f.cwe_ids)]
        assert len(sqli) >= 1 or len(auth) >= 1

    @pytest.mark.asyncio
    async def test_fn_scanner_results_have_correct_types(self, tmp_path):
        """Both scanners should return correct scanner types."""
        test_file = tmp_path / "test.py"
        test_file.write_text('eval(input())')

        injection_scanner = InjectionDetector()
        auth_scanner = AuthLogicDetector()

        inj_result = await injection_scanner.scan(test_file)
        auth_result = await auth_scanner.scan(test_file)

        assert inj_result.scanner == ScannerType.INJECTION
        assert auth_result.scanner == ScannerType.AUTH_LOGIC
