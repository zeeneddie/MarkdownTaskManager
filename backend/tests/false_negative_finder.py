"""
False Negative Finder for Fase 39 Security Scanners.

Tests vulnerable code patterns that SHOULD be detected but might slip through.
"""

import asyncio
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from app.services.security_scanner.adapters.web_security_detector import (
    WebSecurityDetector, create_web_security_detector
)
from app.services.security_scanner.adapters.path_security_detector import (
    PathSecurityDetector, create_path_security_detector
)


@dataclass
class FalseNegativeTest:
    """A test case for finding false negatives."""
    cwe: str
    name: str
    description: str
    filename: str
    code: str
    expected_rule_ids: List[str]


# =============================================================================
# CWE-1321: PROTOTYPE POLLUTION FALSE NEGATIVE TESTS
# =============================================================================

CWE_1321_TESTS = [
    # Test 1: Spread operator with user input (common real-world pattern)
    FalseNegativeTest(
        cwe="CWE-1321",
        name="Spread operator prototype pollution",
        description="Using spread operator with user input can copy __proto__",
        filename="spread.js",
        code='''
function mergeConfig(userInput) {
    const defaults = { theme: 'dark' };
    return { ...defaults, ...userInput };  // Vulnerable: copies __proto__
}
''',
        expected_rule_ids=["WS003", "WS004"],
    ),

    # Test 2: Lodash/underscore merge (very common in Node.js apps)
    FalseNegativeTest(
        cwe="CWE-1321",
        name="Lodash merge prototype pollution",
        description="lodash.merge with user input is a known prototype pollution vector",
        filename="lodash.js",
        code='''
const _ = require('lodash');

app.post('/settings', (req, res) => {
    const config = {};
    _.merge(config, req.body);  // Vulnerable: CVE-2019-10744
    res.json(config);
});
''',
        expected_rule_ids=["WS003"],
    ),

    # Test 3: Deep clone/extend patterns
    FalseNegativeTest(
        cwe="CWE-1321",
        name="jQuery extend prototype pollution",
        description="$.extend with deep copy can pollute prototype",
        filename="jquery.js",
        code='''
function updateSettings(userSettings) {
    $.extend(true, globalConfig, userSettings);  // Vulnerable when deep=true
}
''',
        expected_rule_ids=["WS003"],
    ),

    # Test 4: Reflect.set with user-controlled key
    FalseNegativeTest(
        cwe="CWE-1321",
        name="Reflect.set prototype pollution",
        description="Reflect.set allows setting __proto__ on objects",
        filename="reflect.js",
        code='''
function setProperty(obj, key, value) {
    Reflect.set(obj, key, value);  // Vulnerable if key = '__proto__'
}

// Called with user input
setProperty({}, req.body.key, req.body.value);
''',
        expected_rule_ids=["WS004"],
    ),

    # Test 5: Object.defineProperty with user input
    FalseNegativeTest(
        cwe="CWE-1321",
        name="Object.defineProperty pollution",
        description="Object.defineProperty can modify prototype chain",
        filename="define.js",
        code='''
function setProp(obj, prop, val) {
    Object.defineProperty(obj, prop, { value: val, writable: true });
}

// User controls prop name
setProp(target, userInput.propertyName, userInput.value);
''',
        expected_rule_ids=["WS004"],
    ),

    # Test 6: JSON.parse into object merge
    FalseNegativeTest(
        cwe="CWE-1321",
        name="JSON.parse prototype pollution",
        description="Parsed JSON with __proto__ merged into objects",
        filename="json.js",
        code='''
const payload = JSON.parse(req.body);  // {"__proto__": {"admin": true}}
Object.keys(payload).forEach(key => {
    config[key] = payload[key];  // Pollutes prototype
});
''',
        expected_rule_ids=["WS004"],
    ),
]


# =============================================================================
# CWE-1236: CSV INJECTION FALSE NEGATIVE TESTS
# =============================================================================

CWE_1236_TESTS = [
    # Test 1: Direct string concatenation CSV
    FalseNegativeTest(
        cwe="CWE-1236",
        name="String concatenation CSV export",
        description="Building CSV manually without escaping formulas",
        filename="csv_concat.py",
        code='''
def export_csv(users):
    csv_content = "Name,Email\\n"
    for user in users:
        csv_content += f"{user.name},{user.email}\\n"  # Vulnerable
    return csv_content
''',
        expected_rule_ids=["WS010", "WS011"],
    ),

    # Test 2: pandas to_csv without sanitization
    FalseNegativeTest(
        cwe="CWE-1236",
        name="Pandas DataFrame to_csv",
        description="Pandas export with user data without formula escaping",
        filename="pandas_csv.py",
        code='''
import pandas as pd

def export_report(df):
    df.to_csv('report.csv', index=False)  # User data may contain formulas
''',
        expected_rule_ids=["WS010"],
    ),

    # Test 3: Node.js csv-stringify
    FalseNegativeTest(
        cwe="CWE-1236",
        name="csv-stringify export",
        description="Using csv-stringify with user input",
        filename="stringify.js",
        code='''
const stringify = require('csv-stringify');

function exportData(records) {
    stringify(records, { header: true }, (err, output) => {
        res.attachment('export.csv');
        res.send(output);  // User data not sanitized
    });
}
''',
        expected_rule_ids=["WS010"],
    ),

    # Test 4: Response header CSV download
    FalseNegativeTest(
        cwe="CWE-1236",
        name="CSV response download",
        description="Sending CSV response without formula sanitization",
        filename="download.py",
        code='''
from flask import Response

@app.route('/export')
def export_data():
    data = get_user_submitted_data()
    csv_data = generate_csv(data)
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=export.csv'}
    )
''',
        expected_rule_ids=["WS010"],
    ),

    # Test 5: DictWriter without sanitization
    FalseNegativeTest(
        cwe="CWE-1236",
        name="DictWriter CSV export",
        description="Python DictWriter with user data",
        filename="dictwriter.py",
        code='''
import csv

def export_users(users, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'comment'])
        writer.writeheader()
        for user in users:
            writer.writerow(user)  # User 'comment' may start with =@+-
''',
        expected_rule_ids=["WS011"],
    ),
]


# =============================================================================
# CWE-1284: INVALID QUANTITY FALSE NEGATIVE TESTS
# =============================================================================

CWE_1284_TESTS = [
    # Test 1: slice with user input
    FalseNegativeTest(
        cwe="CWE-1284",
        name="Array slice with user input",
        description="Using slice() with user-controlled bounds",
        filename="slice.py",
        code='''
def get_page(items, request):
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', 10))
    return items[start:end]  # No validation on start/end
''',
        expected_rule_ids=["WS020"],
    ),

    # Test 2: List multiplication
    FalseNegativeTest(
        cwe="CWE-1284",
        name="List multiplication DoS",
        description="Multiplying list by user-controlled number",
        filename="multiply.py",
        code='''
def repeat_items(item, request):
    count = int(request.json['repeat_count'])
    return [item] * count  # Can cause memory exhaustion
''',
        expected_rule_ids=["WS022", "WS023"],
    ),

    # Test 3: String repetition
    FalseNegativeTest(
        cwe="CWE-1284",
        name="String multiplication DoS",
        description="Repeating string by user-controlled count",
        filename="string_repeat.js",
        code='''
function padString(str, count) {
    const times = parseInt(req.query.repeat);
    return str.repeat(times);  // DoS vector
}
''',
        expected_rule_ids=["WS022"],
    ),

    # Test 4: Database LIMIT/OFFSET
    FalseNegativeTest(
        cwe="CWE-1284",
        name="Unchecked LIMIT/OFFSET",
        description="Database query with user-controlled limit",
        filename="limit.py",
        code='''
def get_records(request):
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    return db.query(f"SELECT * FROM users LIMIT {limit} OFFSET {offset}")
''',
        expected_rule_ids=["WS020", "WS023"],
    ),

    # Test 5: Array construction from user size
    FalseNegativeTest(
        cwe="CWE-1284",
        name="Array constructor size",
        description="Creating array with user-controlled size",
        filename="array_size.js",
        code='''
function createGrid(req) {
    const rows = parseInt(req.params.rows);
    const cols = parseInt(req.params.cols);
    return new Array(rows).fill(new Array(cols).fill(0));
}
''',
        expected_rule_ids=["WS022"],
    ),
]


# =============================================================================
# CWE-427: UNCONTROLLED SEARCH PATH FALSE NEGATIVE TESTS
# =============================================================================

CWE_427_TESTS = [
    # Test 1: exec/spawn without absolute path
    FalseNegativeTest(
        cwe="CWE-427",
        name="exec without absolute path",
        description="Executing commands by name relies on PATH",
        filename="exec.py",
        code='''
import subprocess

def run_tool():
    # Relies on PATH - attacker can place malicious 'mytool' earlier
    subprocess.run(['mytool', '--version'])
''',
        expected_rule_ids=["PS001", "PS002"],
    ),

    # Test 2: Node.js child_process.exec
    FalseNegativeTest(
        cwe="CWE-427",
        name="child_process exec",
        description="Node.js exec relies on shell PATH",
        filename="child.js",
        code='''
const { exec } = require('child_process');

exec('imagemagick convert input.png output.jpg', (err, stdout) => {
    console.log(stdout);  // Relies on PATH
});
''',
        expected_rule_ids=["PS001"],
    ),

    # Test 3: PYTHONPATH modification
    FalseNegativeTest(
        cwe="CWE-427",
        name="PYTHONPATH modification",
        description="Modifying PYTHONPATH allows module hijacking",
        filename="pythonpath.py",
        code='''
import os
import sys

# Add user-controlled directory to Python path
user_plugins = os.environ.get('PLUGIN_DIR', '/tmp/plugins')
sys.path.insert(0, user_plugins)  # Vulnerable
''',
        expected_rule_ids=["PS003"],
    ),

    # Test 4: Node require with relative path
    FalseNegativeTest(
        cwe="CWE-427",
        name="require with relative path",
        description="Node.js require searches node_modules",
        filename="require.js",
        code='''
// This searches up the directory tree
const plugin = require('user-plugin');  // Could load from cwd/node_modules
''',
        expected_rule_ids=["PS001"],
    ),

    # Test 5: LD_LIBRARY_PATH modification
    FalseNegativeTest(
        cwe="CWE-427",
        name="LD_LIBRARY_PATH modification",
        description="Modifying LD_LIBRARY_PATH allows library hijacking",
        filename="ldpath.c",
        code='''
#include <stdlib.h>

void add_lib_path(const char* path) {
    char* current = getenv("LD_LIBRARY_PATH");
    char* new_path = malloc(strlen(current) + strlen(path) + 2);
    sprintf(new_path, "%s:%s", path, current);
    setenv("LD_LIBRARY_PATH", new_path, 1);  // Vulnerable
}
''',
        expected_rule_ids=["PS002"],
    ),
]


# =============================================================================
# CWE-428: UNQUOTED SEARCH PATH FALSE NEGATIVE TESTS
# =============================================================================

CWE_428_TESTS = [
    # Test 1: f-string path with spaces
    FalseNegativeTest(
        cwe="CWE-428",
        name="f-string path not quoted",
        description="Building path with spaces in f-string",
        filename="fstring.py",
        code='''
import subprocess

def run_app():
    app_path = "C:\\\\Program Files\\\\MyApp\\\\run.exe"
    # Path has spaces but may not be properly quoted when used
    subprocess.Popen(f'{app_path} --config settings.ini', shell=True)
''',
        expected_rule_ids=["PS010"],
    ),

    # Test 2: Windows service binary path
    FalseNegativeTest(
        cwe="CWE-428",
        name="Service binary path",
        description="Windows service with unquoted binary path",
        filename="service.cs",
        code='''
using System.ServiceProcess;

public class MyService : ServiceBase
{
    protected override void OnStart(string[] args)
    {
        // Service executable path with spaces - may be unquoted in registry
        string binaryPath = @"C:\\Program Files\\MyCompany\\Service\\svc.exe";
        // When installed, ImagePath might be unquoted
    }
}
''',
        expected_rule_ids=["PS011"],
    ),

    # Test 3: Shell script variable unquoted
    FalseNegativeTest(
        cwe="CWE-428",
        name="Unquoted variable in shell",
        description="Shell variable with spaces not quoted",
        filename="script.sh",
        code='''
#!/bin/bash
APP_DIR="/opt/My Application"
cd $APP_DIR  # Unquoted - breaks on spaces
$APP_DIR/run.sh  # Unquoted execution
''',
        expected_rule_ids=["PS012"],
    ),

    # Test 4: Environment variable path
    FalseNegativeTest(
        cwe="CWE-428",
        name="Unquoted env var path",
        description="Environment variable used unquoted in path",
        filename="env_path.py",
        code='''
import os
import subprocess

def run_from_env():
    tool_path = os.environ.get('TOOL_PATH', '/default/path')
    # If TOOL_PATH contains spaces, command breaks
    subprocess.call(tool_path + ' --run', shell=True)
''',
        expected_rule_ids=["PS010", "PS012"],
    ),
]


# =============================================================================
# CWE-1333: ReDoS FALSE NEGATIVE TESTS
# =============================================================================

CWE_1333_TESTS = [
    # Test 1: Backtracking in email regex
    FalseNegativeTest(
        cwe="CWE-1333",
        name="Email regex backtracking",
        description="Common email regex with catastrophic backtracking",
        filename="email.py",
        code='''
import re

# Common vulnerable email pattern
EMAIL_PATTERN = re.compile(r'^([a-zA-Z0-9_\\.-]+)@([\\da-zA-Z\\.-]+)\\.([a-zA-Z\\.]{2,6})$')

def validate_email(email):
    return EMAIL_PATTERN.match(email)  # ReDoS on malformed input
''',
        expected_rule_ids=["PS020", "PS022"],
    ),

    # Test 2: URL validation regex
    FalseNegativeTest(
        cwe="CWE-1333",
        name="URL regex ReDoS",
        description="URL validation with nested quantifiers",
        filename="url.js",
        code='''
const URL_REGEX = /^(https?:\\/\\/)?([\\da-z\\.-]+)\\.([a-z\\.]{2,6})([\\/\\w \\.-]*)*\\/?$/;

function validateUrl(url) {
    return URL_REGEX.test(url);  // Nested quantifier
}
''',
        expected_rule_ids=["PS020"],
    ),

    # Test 3: HTML tag regex
    FalseNegativeTest(
        cwe="CWE-1333",
        name="HTML tag stripping regex",
        description="HTML tag regex with backtracking",
        filename="strip.py",
        code='''
import re

def strip_html(text):
    # Vulnerable to ReDoS on malformed HTML
    return re.sub(r'<[^>]*>', '', text)
''',
        expected_rule_ids=["PS022"],
    ),

    # Test 4: Phone number regex
    FalseNegativeTest(
        cwe="CWE-1333",
        name="Phone number regex",
        description="Phone validation with alternation",
        filename="phone.java",
        code='''
import java.util.regex.Pattern;

public class Validator {
    // Overlapping alternations cause backtracking
    private static final Pattern PHONE = Pattern.compile(
        "^(\\\\+\\\\d{1,3}[- ]?)?\\\\(?\\\\d{1,4}\\\\)?[- ]?\\\\d{1,4}[- ]?\\\\d{1,4}$"
    );

    public boolean validatePhone(String phone) {
        return PHONE.matcher(phone).matches();
    }
}
''',
        expected_rule_ids=["PS020", "PS021"],
    ),

    # Test 5: Regex from config file
    FalseNegativeTest(
        cwe="CWE-1333",
        name="Regex from configuration",
        description="Regex loaded from config (could be user-influenced)",
        filename="config_regex.py",
        code='''
import re
import yaml

def load_validators():
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    # Patterns from config - could be DoS patterns
    return {
        name: re.compile(pattern)
        for name, pattern in config['validators'].items()
    }
''',
        expected_rule_ids=["PS023"],
    ),
]


async def run_tests():
    """Run all false negative tests."""
    web_scanner = create_web_security_detector()
    path_scanner = create_path_security_detector()

    all_tests = [
        ("CWE-1321 (Prototype Pollution)", CWE_1321_TESTS, web_scanner),
        ("CWE-1236 (CSV Injection)", CWE_1236_TESTS, web_scanner),
        ("CWE-1284 (Invalid Quantity)", CWE_1284_TESTS, web_scanner),
        ("CWE-427 (Uncontrolled Search Path)", CWE_427_TESTS, path_scanner),
        ("CWE-428 (Unquoted Search Path)", CWE_428_TESTS, path_scanner),
        ("CWE-1333 (ReDoS)", CWE_1333_TESTS, path_scanner),
    ]

    results = []

    for cwe_name, tests, scanner in all_tests:
        print(f"\n{'='*60}")
        print(f"Testing {cwe_name}")
        print(f"{'='*60}")

        cwe_results = []

        for test in tests:
            with tempfile.TemporaryDirectory() as tmpdir:
                test_file = Path(tmpdir) / test.filename
                test_file.write_text(test.code)

                result = await scanner.scan(test_file)

                detected_rules = [f.rule_id for f in result.findings]

                # Check if ANY expected rule was detected
                detected_expected = [r for r in test.expected_rule_ids if r in detected_rules]
                is_false_negative = len(detected_expected) == 0

                status = "❌ FALSE NEGATIVE" if is_false_negative else "✓ Detected"
                print(f"\n{status}: {test.name}")
                print(f"  Expected: {test.expected_rule_ids}")
                print(f"  Detected: {detected_rules}")

                if is_false_negative:
                    cwe_results.append({
                        'test': test,
                        'detected_rules': detected_rules,
                    })

        results.append({
            'cwe': cwe_name,
            'false_negatives': cwe_results,
        })

    return results


def generate_report(results):
    """Generate markdown report of false negatives."""
    report = ["# Fase 39 False Negative Analysis Report\n"]
    report.append(f"Generated from automated testing of vulnerable code patterns.\n\n")

    total_false_negatives = 0

    for cwe_result in results:
        cwe = cwe_result['cwe']
        false_negatives = cwe_result['false_negatives']

        report.append(f"## {cwe}\n\n")

        if not false_negatives:
            report.append("✓ **No false negatives found** - all test patterns were detected.\n\n")
        else:
            total_false_negatives += len(false_negatives)
            report.append(f"**{len(false_negatives)} false negative(s) found:**\n\n")

            for fn in false_negatives:
                test = fn['test']
                report.append(f"### {test.name}\n\n")
                report.append(f"**Description:** {test.description}\n\n")
                report.append(f"**Expected Rules:** {', '.join(test.expected_rule_ids)}\n\n")
                report.append(f"**Detected Rules:** {', '.join(fn['detected_rules']) or 'None'}\n\n")
                report.append(f"**Vulnerable Code ({test.filename}):**\n")
                report.append(f"```{test.filename.split('.')[-1]}\n{test.code.strip()}\n```\n\n")

    report.append(f"---\n\n## Summary\n\n")
    report.append(f"**Total False Negatives Found:** {total_false_negatives}\n\n")

    for cwe_result in results:
        cwe = cwe_result['cwe']
        count = len(cwe_result['false_negatives'])
        status = "✓" if count == 0 else f"❌ {count}"
        report.append(f"- {cwe}: {status}\n")

    return '\n'.join(report)


if __name__ == '__main__':
    results = asyncio.run(run_tests())
    report = generate_report(results)

    # Write report
    report_path = Path(__file__).parent / 'false_negative_report.md'
    report_path.write_text(report)
    print(f"\n\nReport written to: {report_path}")
