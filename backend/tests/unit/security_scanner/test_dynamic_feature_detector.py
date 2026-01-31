"""
Tests for DynamicFeatureDetector.

Tests cover dynamic language feature detection rules:
- JS Dynamic Property Access (DYN-PROP-001 to DYN-PROP-005): CWE-79, CWE-94, CWE-1321
- JS Dynamic Calls (DYN-CALL-001 to DYN-CALL-004): CWE-94
- JS Dynamic Imports (DYN-IMPORT-001 to DYN-IMPORT-003): CWE-94, CWE-22
- JS Eval-Adjacent (DYN-EVAL-001 to DYN-EVAL-003): CWE-79, CWE-94, CWE-918
- Python Reflection (DYN-REFL-001 to DYN-REFL-004): CWE-94
- Python Exec (DYN-EXEC-001 to DYN-EXEC-003): CWE-94
- Python Meta (DYN-META-001 to DYN-META-003): CWE-94
- Java Reflection (DYN-REFL-J001 to DYN-REFL-J004): CWE-470
- Java Deserialization (DYN-DESER-J001 to DYN-DESER-J002): CWE-94, CWE-502
- Java Proxy (DYN-PROXY-J001 to DYN-PROXY-J002): CWE-470
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.dynamic_feature_detector import (
    DynamicFeatureDetector,
    DynamicFeatureRule,
    ALL_DYNAMIC_FEATURE_RULES,
    JS_DYNAMIC_PROPERTY_RULES,
    JS_DYNAMIC_CALL_RULES,
    JS_DYNAMIC_IMPORT_RULES,
    JS_EVAL_ADJACENT_RULES,
    PYTHON_REFLECTION_RULES,
    PYTHON_EXEC_RULES,
    PYTHON_META_RULES,
    JAVA_REFLECTION_RULES,
    JAVA_DESERIALIZATION_RULES,
    JAVA_PROXY_RULES,
    create_dynamic_feature_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestDynamicFeatureDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = DynamicFeatureDetector()
        assert scanner.scanner_type == ScannerType.DYNAMIC_FEATURE

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = DynamicFeatureDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = DynamicFeatureDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_expected_rules(self):
        """Should have expected number of dynamic feature detection rules."""
        # Total rules across all categories: 5+4+3+3+4+3+3+4+2+2 = 33
        assert len(ALL_DYNAMIC_FEATURE_RULES) >= 30

    def test_supported_languages(self):
        """Should support expected languages."""
        scanner = DynamicFeatureDetector()
        languages = scanner.supported_languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "python" in languages
        assert "java" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = DynamicFeatureDetector()
        extensions = scanner.supported_extensions
        assert ".js" in extensions
        assert ".jsx" in extensions
        assert ".ts" in extensions
        assert ".tsx" in extensions
        assert ".py" in extensions
        assert ".java" in extensions
        assert ".jsp" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_dynamic_feature_detector()
        assert isinstance(scanner, DynamicFeatureDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in ALL_DYNAMIC_FEATURE_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in ALL_DYNAMIC_FEATURE_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_target_cwes(self):
        """Should cover the target CWEs for dynamic feature detection."""
        cwe_coverage = set()
        for rule in ALL_DYNAMIC_FEATURE_RULES:
            cwe_coverage.update(rule.cwe_ids)

        assert "CWE-79" in cwe_coverage, "CWE-79 (XSS) not covered"
        assert "CWE-94" in cwe_coverage, "CWE-94 (Code Injection) not covered"
        assert "CWE-470" in cwe_coverage, "CWE-470 (Unsafe Reflection) not covered"
        assert "CWE-502" in cwe_coverage, "CWE-502 (Deserialization) not covered"
        assert "CWE-1321" in cwe_coverage, "CWE-1321 (Prototype Pollution) not covered"

    def test_rule_categories(self):
        """All rules should have valid categories."""
        valid_categories = {
            "dynamic_property_access", "dynamic_call", "dynamic_import",
            "eval_adjacent", "python_reflection", "python_exec", "python_meta",
            "java_reflection", "java_deserialization", "java_proxy",
        }
        for rule in ALL_DYNAMIC_FEATURE_RULES:
            assert rule.category in valid_categories, (
                f"Rule {rule.id} has invalid category: {rule.category}"
            )

    def test_rule_list_counts(self):
        """Each category list should have expected count."""
        assert len(JS_DYNAMIC_PROPERTY_RULES) == 5
        assert len(JS_DYNAMIC_CALL_RULES) == 4
        assert len(JS_DYNAMIC_IMPORT_RULES) == 3
        assert len(JS_EVAL_ADJACENT_RULES) == 3
        assert len(PYTHON_REFLECTION_RULES) == 4
        assert len(PYTHON_EXEC_RULES) == 3
        assert len(PYTHON_META_RULES) == 3
        assert len(JAVA_REFLECTION_RULES) == 4
        assert len(JAVA_DESERIALIZATION_RULES) == 2
        assert len(JAVA_PROXY_RULES) == 2

    def test_rules_summary(self):
        """get_rules_summary should return structured data."""
        scanner = DynamicFeatureDetector()
        summary = scanner.get_rules_summary()
        assert "total_rules" in summary
        assert summary["total_rules"] >= 30
        assert "rules_by_category" in summary
        assert "supported_languages" in summary
        assert "cwe_coverage" in summary


# =============================================================================
# JS DYNAMIC PROPERTY ACCESS (DYN-PROP)
# =============================================================================


class TestJSDynamicPropertyAccess:
    """Tests for JS dynamic property access detection rules."""

    @pytest.mark.asyncio
    async def test_detect_bracket_notation_dom(self, tmp_path):
        """Should detect bracket notation on DOM elements (DYN-PROP-001)."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function setProperty(userInput, value) {
    var element = document.getElementById("target");
    element[userInput] = value;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-001"), None)
        assert finding is not None
        assert "CWE-79" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_dynamic_property_deletion(self, tmp_path):
        """Should detect dynamic property deletion (DYN-PROP-002)."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function cleanupObject(obj, req) {
    delete obj[req.body.key];
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-002"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_computed_property_assignment(self, tmp_path):
        """Should detect computed property assignment with user data (DYN-PROP-003)."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function updateConfig(req) {
    config[req.body.key] = req.body.value;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_object_define_property(self, tmp_path):
        """Should detect Object.defineProperty with user input (DYN-PROP-004)."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function addProp(obj, req) {
    Object.defineProperty(obj, req.body.propName, {
        value: req.body.propValue,
        writable: true,
    });
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-004"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_prototype_access_bracket(self, tmp_path):
        """Should detect prototype access via bracket notation (DYN-PROP-005)."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function merge(target, input) {
    var key = "__proto__";
    target["__proto__"] = input;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-005"), None)
        assert finding is not None
        assert "CWE-1321" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_constructor_bracket_access(self, tmp_path):
        """Should detect constructor bracket access for prototype pollution."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function pollute(obj, input) {
    obj["constructor"] = input;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-005"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_define_properties_dynamic(self, tmp_path):
        """Should detect Object.defineProperties with user input."""
        test_file = tmp_path / "prop.js"
        test_file.write_text('''
function addProps(obj, req) {
    Object.defineProperties(obj, input);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-004"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_dynamic_deletion_query_param(self, tmp_path):
        """Should detect delete with query param."""
        test_file = tmp_path / "prop.ts"
        test_file.write_text('''
function removeProp(obj: any, req: Request) {
    delete obj[query.field];
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROP-002"), None)
        assert finding is not None


# =============================================================================
# JS DYNAMIC CALLS (DYN-CALL)
# =============================================================================


class TestJSComputedCalls:
    """Tests for JS dynamic/computed call detection rules."""

    @pytest.mark.asyncio
    async def test_detect_window_bracket_call(self, tmp_path):
        """Should detect window[variable]() computed call (DYN-CALL-001)."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
function dispatch(action) {
    window[action]();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-001"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_globalthis_bracket_call(self, tmp_path):
        """Should detect globalThis[variable]() computed call."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
function execute(name) {
    globalThis[name]();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_this_bracket_method_call(self, tmp_path):
        """Should detect this[variable]() computed method call (DYN-CALL-002)."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
class Controller {
    handleRequest(req) {
        this[action](req);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_function_constructor(self, tmp_path):
        """Should detect new Function() constructor (DYN-CALL-003)."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
function createHandler(req) {
    var fn = new Function("return " + req.body.expression);
    return fn();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-003"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_function_constructor_template_literal(self, tmp_path):
        """Should detect new Function() with template literal."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
function dynamicFunc(userCode) {
    var fn = new Function(`return ${userCode}`);
    return fn();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_settimeout_string(self, tmp_path):
        """Should detect setTimeout with string containing user input (DYN-CALL-004)."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
function delayExec(req) {
    setTimeout(`${req.body.code}`, 1000);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-004"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_setinterval_template(self, tmp_path):
        """Should detect setInterval with template literal string."""
        test_file = tmp_path / "call.js"
        test_file.write_text('''
function repeat(code) {
    setInterval(`${code}`, 5000);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-004"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_window_bracket_with_req(self, tmp_path):
        """Should detect window bracket access with req parameter."""
        test_file = tmp_path / "call.ts"
        test_file.write_text('''
function runAction(req: Request) {
    window[req.body.action]();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-CALL-001"), None)
        assert finding is not None


# =============================================================================
# JS DYNAMIC IMPORTS (DYN-IMPORT)
# =============================================================================


class TestJSDynamicImports:
    """Tests for JS dynamic import detection rules."""

    @pytest.mark.asyncio
    async def test_detect_require_variable(self, tmp_path):
        """Should detect require() with variable (DYN-IMPORT-001)."""
        test_file = tmp_path / "imports.js"
        test_file.write_text('''
function loadPlugin(req) {
    var plugin = require(req.body.moduleName);
    plugin.init();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-001"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_require_template_literal(self, tmp_path):
        """Should detect require() with template literal."""
        test_file = tmp_path / "imports.js"
        test_file.write_text('''
function loadModule(name) {
    var mod = require(`./plugins/${name}`);
    return mod;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_dynamic_import_variable(self, tmp_path):
        """Should detect dynamic import() with variable (DYN-IMPORT-002)."""
        test_file = tmp_path / "imports.js"
        test_file.write_text('''
async function loadComponent(req) {
    var component = await import(req.query.component);
    return component.default;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_dynamic_import_template(self, tmp_path):
        """Should detect dynamic import() with template literal."""
        test_file = tmp_path / "imports.ts"
        test_file.write_text('''
async function loadPlugin(name: string) {
    const mod = await import(`./plugins/${name}`);
    return mod;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_require_resolve_user_input(self, tmp_path):
        """Should detect require.resolve with user input (DYN-IMPORT-003)."""
        test_file = tmp_path / "imports.js"
        test_file.write_text('''
function resolvePath(req) {
    var resolved = require.resolve(req.query.module);
    return resolved;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-003"), None)
        assert finding is not None
        assert "CWE-22" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_require_concatenation(self, tmp_path):
        """Should detect require() with string concatenation."""
        test_file = tmp_path / "imports.js"
        test_file.write_text('''
function loadDynamic(name) {
    var mod = require(name + "/index");
    return mod;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-001"), None)
        assert finding is not None


# =============================================================================
# JS EVAL-ADJACENT (DYN-EVAL)
# =============================================================================


class TestJSEvalAdjacent:
    """Tests for JS eval-adjacent pattern detection rules."""

    @pytest.mark.asyncio
    async def test_detect_document_write_variable(self, tmp_path):
        """Should detect document.write with variable (DYN-EVAL-001)."""
        test_file = tmp_path / "eval.js"
        test_file.write_text('''
function render(content) {
    document.write(content + "</div>");
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-001"), None)
        assert finding is not None
        assert "CWE-79" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_document_writeln_template(self, tmp_path):
        """Should detect document.writeln with template literal."""
        test_file = tmp_path / "eval.js"
        test_file.write_text('''
function display(name) {
    document.writeln(`<h1>Welcome ${name}</h1>`);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_script_src_assignment(self, tmp_path):
        """Should detect script.src assignment from variable (DYN-EVAL-002)."""
        test_file = tmp_path / "eval.js"
        test_file.write_text('''
function loadScript(req) {
    var script = document.createElement("script");
    script.src = req.query.scriptUrl;
    document.body.appendChild(script);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-002"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_script_src_user_url(self, tmp_path):
        """Should detect script.src with user-controlled URL."""
        test_file = tmp_path / "eval.js"
        test_file.write_text('''
function injectScript(url) {
    var s = document.createElement("script");
    s.src = url;
    document.head.appendChild(s);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_websocket_user_url(self, tmp_path):
        """Should detect WebSocket URL from user input (DYN-EVAL-003)."""
        test_file = tmp_path / "eval.js"
        test_file.write_text('''
function connect(req) {
    var ws = new WebSocket(req.query.endpoint);
    ws.onmessage = handleMessage;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-003"), None)
        assert finding is not None
        assert "CWE-918" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_websocket_template_literal(self, tmp_path):
        """Should detect WebSocket with template literal URL."""
        test_file = tmp_path / "eval.ts"
        test_file.write_text('''
function createSocket(endpoint: string) {
    const ws = new WebSocket(`wss://${endpoint}/socket`);
    return ws;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_websocket_user_input_variable(self, tmp_path):
        """Should detect WebSocket with user input variable."""
        test_file = tmp_path / "eval.js"
        test_file.write_text('''
function connectToServer(req) {
    var ws = new WebSocket(input + "/ws");
    return ws;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EVAL-003"), None)
        assert finding is not None


# =============================================================================
# PYTHON REFLECTION (DYN-REFL)
# =============================================================================


class TestPythonReflection:
    """Tests for Python reflection detection rules."""

    @pytest.mark.asyncio
    async def test_detect_getattr_user_input(self, tmp_path):
        """Should detect getattr() with user-controlled attribute (DYN-REFL-001)."""
        test_file = tmp_path / "reflect.py"
        test_file.write_text('''
from flask import request

def call_method(obj):
    attr_name = request.args.get("method")
    method = getattr(obj, request.args.get("attr"))
    return method()
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-001"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_setattr_user_input(self, tmp_path):
        """Should detect setattr() with user-controlled attribute (DYN-REFL-002)."""
        test_file = tmp_path / "reflect.py"
        test_file.write_text('''
from flask import request

def update_object(obj):
    attr = request.form.get("attribute")
    value = request.form.get("value")
    setattr(obj, request.form.get("field"), value)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_dunder_import_variable(self, tmp_path):
        """Should detect __import__() with user-controlled module (DYN-REFL-003)."""
        test_file = tmp_path / "reflect.py"
        test_file.write_text('''
from flask import request

def load_plugin():
    module_name = request.args.get("plugin")
    mod = __import__(request.args.get("module"))
    return mod
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_globals_user_key(self, tmp_path):
        """Should detect globals() access with user key (DYN-REFL-004)."""
        test_file = tmp_path / "reflect.py"
        test_file.write_text('''
from flask import request

def call_function():
    func_name = request.args.get("func")
    func = globals()[request.args.get("function")]
    return func()
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-004"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_locals_user_key(self, tmp_path):
        """Should detect locals() access with user key."""
        test_file = tmp_path / "reflect.py"
        test_file.write_text('''
from flask import request

def get_local_var():
    x = 42
    y = 100
    result = locals()[request.args.get("var")]
    return result
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-004"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_getattr_with_data_bracket(self, tmp_path):
        """Should detect getattr with data[] access pattern."""
        test_file = tmp_path / "reflect.py"
        test_file.write_text('''
def dynamic_dispatch(obj, data):
    method = getattr(obj, data["method_name"])
    return method()
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-001"), None)
        assert finding is not None


# =============================================================================
# PYTHON EXECUTION (DYN-EXEC)
# =============================================================================


class TestPythonExecution:
    """Tests for Python exec/eval/compile detection rules."""

    @pytest.mark.asyncio
    async def test_detect_compile_user_input(self, tmp_path):
        """Should detect compile() with user data (DYN-EXEC-001)."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
from flask import request

def run_code():
    code = request.form.get("code")
    compiled = compile(request.form.get("source"), "<string>", "exec")
    exec(compiled)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-001"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_exec_fstring(self, tmp_path):
        """Should detect exec() with f-string (DYN-EXEC-002)."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
def run_dynamic(variable_name, value):
    exec(f"{variable_name} = {value}")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_exec_format(self, tmp_path):
        """Should detect exec() with .format() method."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
def execute_template(name, code):
    exec("{} = {}".format(name, code))
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_exec_concatenation(self, tmp_path):
        """Should detect exec() with string concatenation and user input."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
def run_user_code(user_code):
    exec("result = " + str(user_code))
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_eval_user_input(self, tmp_path):
        """Should detect eval() with user input (DYN-EXEC-003)."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
from flask import request

def calculate():
    expression = request.args.get("expr")
    result = eval(request.args.get("expression"))
    return str(result)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_eval_fstring(self, tmp_path):
        """Should detect eval() with f-string."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
def dynamic_eval(var):
    return eval(f"config['{var}']")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_eval_format(self, tmp_path):
        """Should detect eval() with .format()."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
def compute(expression):
    return eval("{} + 1".format(expression))
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_compile_with_data_bracket(self, tmp_path):
        """Should detect compile() with data[] access."""
        test_file = tmp_path / "execution.py"
        test_file.write_text('''
def compile_code(data):
    code_obj = compile(data["source_code"], "<user>", "exec")
    exec(code_obj)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-EXEC-001"), None)
        assert finding is not None


# =============================================================================
# PYTHON META (DYN-META)
# =============================================================================


class TestPythonMetaclass:
    """Tests for Python metaclass/class hierarchy abuse detection rules."""

    @pytest.mark.asyncio
    async def test_detect_type_three_arg(self, tmp_path):
        """Should detect type() three-arg form with user input (DYN-META-001)."""
        test_file = tmp_path / "meta.py"
        test_file.write_text('''
from flask import request

def create_class():
    class_name = request.args.get("name")
    klass = type(request.args.get("classname"), (object,), {"run": lambda self: None})
    return klass()
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-META-001"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_subclasses_enumeration(self, tmp_path):
        """Should detect __subclasses__() call in user context (DYN-META-002)."""
        test_file = tmp_path / "meta.py"
        test_file.write_text('''
from flask import request, render_template_string

def exploit():
    user_input = request.args.get("payload")
    classes = ().__class__.__subclasses__()
    for cls in classes:
        if "Popen" in cls.__name__:
            return cls(["id"])
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-META-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_class_bases_access(self, tmp_path):
        """Should detect __class__.__bases__ access (DYN-META-003)."""
        test_file = tmp_path / "meta.py"
        test_file.write_text('''
from flask import request

def sandbox_escape():
    user_template = request.args.get("tpl")
    base = "".__class__.__bases__[0]
    return render(user_template)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-META-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_mro_access(self, tmp_path):
        """Should detect __mro__ access in user context."""
        test_file = tmp_path / "meta.py"
        test_file.write_text('''
from flask import request

def traverse_mro():
    payload = request.args.get("p")
    chain = "".__class__.__mro__
    return eval(payload)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-META-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_type_with_data_get(self, tmp_path):
        """Should detect type() with .get() data access."""
        test_file = tmp_path / "meta.py"
        test_file.write_text('''
def make_class(params):
    name = params.get("name")
    klass = type(params.get("cls"), (Base,), methods)
    return klass
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-META-001"), None)
        assert finding is not None


# =============================================================================
# JAVA REFLECTION (DYN-REFL-J)
# =============================================================================


class TestJavaReflection:
    """Tests for Java reflection detection rules."""

    @pytest.mark.asyncio
    async def test_detect_class_forname(self, tmp_path):
        """Should detect Class.forName() with user input (DYN-REFL-J001)."""
        test_file = tmp_path / "Reflect.java"
        test_file.write_text('''
public class PluginLoader {
    public Object loadPlugin(String input) throws Exception {
        Class<?> clazz = Class.forName(input);
        return clazz.newInstance();
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-J001"), None)
        assert finding is not None
        assert "CWE-470" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_class_forname_request(self, tmp_path):
        """Should detect Class.forName with request.getParameter."""
        test_file = tmp_path / "Reflect.java"
        test_file.write_text('''
public class DynamicLoader {
    public void handle(HttpServletRequest request) throws Exception {
        String className = request.getParameter("class");
        Class<?> clazz = Class.forName(request.getParameter("type"));
        Object instance = clazz.getDeclaredConstructor().newInstance();
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-J001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_method_invoke(self, tmp_path):
        """Should detect Method.invoke() with user arguments (DYN-REFL-J002)."""
        test_file = tmp_path / "Reflect.java"
        test_file.write_text('''
public class Dispatcher {
    public Object dispatch(HttpServletRequest request) throws Exception {
        Class<?> clazz = Class.forName("com.app.Handler");
        Method method = clazz.getDeclaredMethod("handle");
        return method.invoke(null, request);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-J002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_constructor_newinstance(self, tmp_path):
        """Should detect Constructor.newInstance() with user data (DYN-REFL-J003)."""
        test_file = tmp_path / "Reflect.java"
        test_file.write_text('''
public class Factory {
    public Object create(String input) throws Exception {
        Class<?> clazz = Class.forName("com.app.Widget");
        Constructor<?> ctor = clazz.getConstructor(String.class);
        return ctor.newInstance(input);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-J003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_field_set_user_data(self, tmp_path):
        """Should detect Field.set() with user-controlled value (DYN-REFL-J004)."""
        test_file = tmp_path / "Reflect.java"
        test_file.write_text('''
public class FieldUpdater {
    public void update(Object obj, String param) throws Exception {
        Field field = obj.getClass().getDeclaredField("config");
        field.set(obj, param);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-J004"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_method_invoke_with_input(self, tmp_path):
        """Should detect Method.invoke with input parameter."""
        test_file = tmp_path / "Reflect.java"
        test_file.write_text('''
public class ReflectiveHandler {
    public void handle(Object target, String input) throws Exception {
        Method m = target.getClass().getMethod("process");
        m.invoke(target, input);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-REFL-J002"), None)
        assert finding is not None


# =============================================================================
# JAVA DESERIALIZATION (DYN-DESER-J)
# =============================================================================


class TestJavaDeserialization:
    """Tests for Java deserialization detection rules."""

    @pytest.mark.asyncio
    async def test_detect_urlclassloader_user_url(self, tmp_path):
        """Should detect URLClassLoader with user URL (DYN-DESER-J001)."""
        test_file = tmp_path / "Deser.java"
        test_file.write_text('''
public class RemoteLoader {
    public Object loadRemote(HttpServletRequest request) throws Exception {
        URL url = new URL(request.getParameter("url"));
        URLClassLoader loader = new URLClassLoader(new URL[]{new URL(request.getParameter("jar"))});
        Class<?> cls = loader.loadClass("RemotePlugin");
        return cls.newInstance();
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-DESER-J001"), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_object_input_stream_readobject(self, tmp_path):
        """Should detect ObjectInputStream.readObject (DYN-DESER-J002)."""
        test_file = tmp_path / "Deser.java"
        test_file.write_text('''
public class DataProcessor {
    public Object process(InputStream input) throws Exception {
        ObjectInputStream ois = new ObjectInputStream(input);
        Object data = ois.readObject();
        return data;
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-DESER-J002"), None)
        assert finding is not None
        assert "CWE-502" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_ois_readobject_network(self, tmp_path):
        """Should detect OIS readObject from network stream."""
        test_file = tmp_path / "Deser.java"
        test_file.write_text('''
public class NetworkHandler {
    public void handleSocket(Socket socket) throws Exception {
        ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
        Object command = ois.readObject();
        processCommand(command);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-DESER-J002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_urlclassloader_input_param(self, tmp_path):
        """Should detect URLClassLoader with input parameter."""
        test_file = tmp_path / "Deser.java"
        test_file.write_text('''
public class PluginLoader {
    public void loadPlugin(String input) throws Exception {
        URL pluginUrl = new URL(input);
        URLClassLoader cl = URLClassLoader.newInstance(new URL[]{new URL(input)});
        Class<?> pluginClass = cl.loadClass("Plugin");
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-DESER-J001"), None)
        assert finding is not None


# =============================================================================
# JAVA PROXY (DYN-PROXY-J)
# =============================================================================


class TestJavaProxy:
    """Tests for Java proxy/method handle detection rules."""

    @pytest.mark.asyncio
    async def test_detect_proxy_new_proxy_instance(self, tmp_path):
        """Should detect Proxy.newProxyInstance with user data (DYN-PROXY-J001)."""
        test_file = tmp_path / "ProxyTest.java"
        test_file.write_text('''
public class DynamicProxy {
    public Object createProxy(String input) throws Exception {
        return Proxy.newProxyInstance(null, new Class[]{Runnable.class}, new UserHandler(input));
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROXY-J001"), None)
        assert finding is not None
        assert "CWE-470" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_proxy_with_request_param(self, tmp_path):
        """Should detect Proxy.newProxyInstance with request parameter."""
        test_file = tmp_path / "ProxyTest.java"
        test_file.write_text('''
public class ServiceProxy {
    public Object create(HttpServletRequest request) {
        return Proxy.newProxyInstance(null, interfaces, new Handler(request));
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROXY-J001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_method_handle_invoke(self, tmp_path):
        """Should detect MethodHandle.invoke with user args (DYN-PROXY-J002)."""
        test_file = tmp_path / "HandleTest.java"
        test_file.write_text('''
public class HandleInvoker {
    public Object invoke(HttpServletRequest request) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        MethodHandle mh = lookup.findVirtual(String.class, "concat", MethodType.methodType(String.class, String.class));
        return mh.invoke(request.getParameter("value"));
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROXY-J002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_method_handle_invoke_with_arguments(self, tmp_path):
        """Should detect MethodHandle.invokeWithArguments with user data."""
        test_file = tmp_path / "HandleTest.java"
        test_file.write_text('''
public class DynInvoker {
    public Object run(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        MethodHandle methodHandle = lookup.findStatic(Math.class, "abs", MethodType.methodType(int.class, int.class));
        return methodHandle.invokeWithArguments(args);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROXY-J002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_method_handle_invoke_exact(self, tmp_path):
        """Should detect MethodHandle.invokeExact with user data."""
        test_file = tmp_path / "HandleTest.java"
        test_file.write_text('''
public class ExactInvoker {
    public Object exec(Object data) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        MethodHandle mh = lookup.findVirtual(String.class, "length", MethodType.methodType(int.class));
        return mh.invokeExact(data);
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-PROXY-J002"), None)
        assert finding is not None


# =============================================================================
# FALSE POSITIVE TESTS - JAVASCRIPT
# =============================================================================


class TestJSFalsePositives:
    """Tests ensuring safe JS patterns are not flagged."""

    @pytest.mark.asyncio
    async def test_no_flag_static_require(self, tmp_path):
        """Static require with string literal should not be flagged."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
const express = require("express");
const path = require("path");
const fs = require("fs");
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        import_findings = [f for f in result.findings if "DYN-IMPORT" in f.rule_id]
        assert len(import_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_settimeout_function(self, tmp_path):
        """setTimeout with function reference should not be flagged."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
setTimeout(function() {
    console.log("hello");
}, 1000);

setTimeout(() => doSomething(), 500);
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        call_findings = [f for f in result.findings if f.rule_id == "DYN-CALL-004"]
        assert len(call_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_static_import(self, tmp_path):
        """Static import() with string literal should not be flagged."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
const mod = await import("./myModule");
const other = await import("lodash");
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        import_findings = [f for f in result.findings if f.rule_id == "DYN-IMPORT-002"]
        assert len(import_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_style_bracket_access(self, tmp_path):
        """element.style[] access should not be flagged as DOM property abuse."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
function setStyle(el, prop, value) {
    el.style[prop] = value;
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        prop_findings = [f for f in result.findings if f.rule_id == "DYN-PROP-001"]
        assert len(prop_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_static_websocket(self, tmp_path):
        """WebSocket with static URL should not be flagged."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
const ws = new WebSocket("wss://api.example.com/ws");
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if f.rule_id == "DYN-EVAL-003"]
        assert len(eval_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_static_script_src(self, tmp_path):
        """Static script.src assignment should not be flagged."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
var script = document.createElement("script");
script.src = "https://cdn.example.com/lib.js";
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        eval_findings = [f for f in result.findings if f.rule_id == "DYN-EVAL-002"]
        assert len(eval_findings) == 0


# =============================================================================
# FALSE POSITIVE TESTS - PYTHON
# =============================================================================


class TestPythonFalsePositives:
    """Tests ensuring safe Python patterns are not flagged."""

    @pytest.mark.asyncio
    async def test_no_flag_regex_compile(self, tmp_path):
        """re.compile should not be flagged as code compile."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
import re
pattern = re.compile(r"^[a-z]+$")
match = pattern.match("hello")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        exec_findings = [f for f in result.findings if f.rule_id == "DYN-EXEC-001"]
        assert len(exec_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_ast_literal_eval(self, tmp_path):
        """ast.literal_eval should not be flagged as dangerous eval."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
import ast
data = ast.literal_eval(request.args.get("data"))
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        exec_findings = [f for f in result.findings if f.rule_id == "DYN-EXEC-003"]
        assert len(exec_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_static_import(self, tmp_path):
        """Static __import__ with string literal should not be flagged."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
json_mod = __import__("json")
os_mod = __import__("os")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        refl_findings = [f for f in result.findings if f.rule_id == "DYN-REFL-003"]
        assert len(refl_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_getattr_with_default(self, tmp_path):
        """getattr with safe default and literal should not be flagged."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
value = getattr(obj, attr_name, None)
other = getattr(config, "setting", False)
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        refl_findings = [f for f in result.findings if f.rule_id == "DYN-REFL-001"]
        assert len(refl_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_type_check(self, tmp_path):
        """type() used for type checking should not be flagged."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
if type(value) == int:
    print("integer")
if type(obj) is str:
    print("string")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        meta_findings = [f for f in result.findings if f.rule_id == "DYN-META-001"]
        assert len(meta_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_static_eval(self, tmp_path):
        """eval() with string literal should not be flagged."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
result = eval("2 + 3")
other = eval("True")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        exec_findings = [f for f in result.findings if f.rule_id == "DYN-EXEC-003"]
        assert len(exec_findings) == 0


# =============================================================================
# FALSE POSITIVE TESTS - JAVA
# =============================================================================


class TestJavaFalsePositives:
    """Tests ensuring safe Java patterns are not flagged."""

    @pytest.mark.asyncio
    async def test_no_flag_static_class_forname(self, tmp_path):
        """Class.forName with string literal should not be flagged."""
        test_file = tmp_path / "Safe.java"
        test_file.write_text('''
public class DriverLoader {
    static {
        Class.forName("com.mysql.cj.jdbc.Driver");
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        refl_findings = [f for f in result.findings if f.rule_id == "DYN-REFL-J001"]
        assert len(refl_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_newinstance_no_args(self, tmp_path):
        """newInstance() with no args should not be flagged for DYN-REFL-J003."""
        test_file = tmp_path / "Safe.java"
        test_file.write_text('''
public class Factory {
    public Object create(Class<?> clazz) throws Exception {
        return clazz.getDeclaredConstructor().newInstance();
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        refl_findings = [f for f in result.findings if f.rule_id == "DYN-REFL-J003"]
        assert len(refl_findings) == 0

    @pytest.mark.asyncio
    async def test_no_flag_object_input_filter(self, tmp_path):
        """ObjectInputStream with ObjectInputFilter should not be flagged."""
        test_file = tmp_path / "Safe.java"
        test_file.write_text('''
public class SafeDeser {
    public Object deserialize(InputStream in) throws Exception {
        ObjectInputStream ois = new ObjectInputStream(in);
        ObjectInputFilter filter = ObjectInputFilter.Config.createFilter("com.app.*;!*");
        ois.setObjectInputFilter(filter);
        return ois.readObject();
    }
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        deser_findings = [f for f in result.findings if f.rule_id == "DYN-DESER-J002"]
        assert len(deser_findings) == 0


# =============================================================================
# CROSS-LANGUAGE & EDGE CASES
# =============================================================================


class TestCrossLanguageEdgeCases:
    """Tests for edge cases and cross-language scenarios."""

    @pytest.mark.asyncio
    async def test_unsupported_extension_no_findings(self, tmp_path):
        """Unsupported file extension should produce no findings."""
        test_file = tmp_path / "code.rb"
        test_file.write_text('''
eval(params[:code])
system(params[:cmd])
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_empty_file_no_findings(self, tmp_path):
        """Empty file should produce no findings."""
        test_file = tmp_path / "empty.js"
        test_file.write_text("")

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) == 0
        assert result.files_scanned == 1

    @pytest.mark.asyncio
    async def test_typescript_shares_js_rules(self, tmp_path):
        """TypeScript should trigger the same JS rules."""
        test_file = tmp_path / "dynamic.ts"
        test_file.write_text('''
function loadPlugin(req: Request): void {
    const mod = require(req.body.moduleName);
    mod.init();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "DYN-IMPORT-001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_multiple_findings_single_file(self, tmp_path):
        """Should detect multiple different vulnerabilities in one file."""
        test_file = tmp_path / "multi.py"
        test_file.write_text('''
from flask import request

def dangerous():
    mod = __import__(request.args.get("module"))
    result = eval(f"{request.args.get('expr')}")
    func = globals()[request.args.get("func")]
    setattr(obj, request.form.get("attr"), "pwned")
    return result
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        rule_ids = {f.rule_id for f in result.findings}
        assert len(rule_ids) >= 3

    @pytest.mark.asyncio
    async def test_scan_result_metadata(self, tmp_path):
        """Scan result should contain proper metadata."""
        test_file = tmp_path / "meta.js"
        test_file.write_text('''
function exec(name) {
    window[name]();
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert result.scanner == ScannerType.DYNAMIC_FEATURE
        assert result.scanner_version == "1.0.0"
        assert result.files_scanned == 1
        assert result.scan_duration_ms >= 0
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_findings_have_location(self, tmp_path):
        """Each finding should have proper location info."""
        test_file = tmp_path / "loc.py"
        test_file.write_text('''
from flask import request
result = eval(f"{request.args.get('x')}")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        for finding in result.findings:
            assert finding.location is not None
            assert finding.location.file_path is not None
            assert finding.location.start_line >= 1
            assert finding.location.snippet is not None

    @pytest.mark.asyncio
    async def test_findings_have_suggested_fixes(self, tmp_path):
        """Each finding should have at least one suggested fix."""
        test_file = tmp_path / "fix.js"
        test_file.write_text('''
function load(req) {
    require(req.body.module);
}
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        for finding in result.findings:
            assert len(finding.suggested_fixes) >= 1

    @pytest.mark.asyncio
    async def test_findings_have_tags(self, tmp_path):
        """Each finding should have language and category tags."""
        test_file = tmp_path / "tags.py"
        test_file.write_text('''
from flask import request
eval(f"{request.args.get('expr')}")
''')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        for finding in result.findings:
            assert "dynamic_feature" in finding.tags
            assert any(tag.startswith("lang:") for tag in finding.tags)

    @pytest.mark.asyncio
    async def test_directory_scan(self, tmp_path):
        """Should scan all supported files in a directory."""
        js_file = tmp_path / "app.js"
        js_file.write_text('function f(name) { window[name](); }')

        py_file = tmp_path / "app.py"
        py_file.write_text('from flask import request\neval(f"{request.args.get(\'x\')}")')

        scanner = DynamicFeatureDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 2
        languages_found = set()
        for finding in result.findings:
            for tag in finding.tags:
                if tag.startswith("lang:"):
                    languages_found.add(tag)
        assert len(languages_found) >= 2
