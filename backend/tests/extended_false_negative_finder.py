"""
Extended False Negative Finder for ALL Security Scanners.

Tests vulnerable code patterns across all implemented scanners:
- Fase 36: Crypto, Control Flow, Boolean Logic
- Fase 38: Memory Safety, Concurrency
- Generic Security Scanner
"""

import asyncio
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

# Import all scanners
from app.services.security_scanner.adapters.memory_safety_detector import (
    MemorySafetyDetector, create_memory_safety_detector
)
from app.services.security_scanner.adapters.concurrency_error_detector import (
    ConcurrencyErrorDetector, create_concurrency_error_detector
)
from app.services.security_scanner.adapters.crypto_error_detector import (
    CryptoErrorDetector, create_crypto_error_detector
)
from app.services.security_scanner.adapters.control_flow_logic_detector import (
    ControlFlowLogicDetector, create_control_flow_logic_detector
)
from app.services.security_scanner.adapters.boolean_logic_detector import (
    BooleanLogicDetector, create_boolean_logic_detector
)
from app.services.security_scanner.adapters.generic_security_scanner import (
    GenericSecurityScanner, create_generic_security_scanner
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
# FASE 38: MEMORY SAFETY FALSE NEGATIVE TESTS
# =============================================================================

MEMORY_SAFETY_TESTS = [
    # Test 1: strncat still vulnerable
    FalseNegativeTest(
        cwe="CWE-119",
        name="strncat improper size",
        description="strncat with wrong size calculation still overflows",
        filename="strncat.c",
        code='''
char dest[10] = "Hello";
void concat(const char *src) {
    strncat(dest, src, sizeof(dest));  // Wrong! Should be sizeof(dest)-strlen(dest)-1
}
''',
        expected_rule_ids=["MS001", "MS004"],
    ),

    # Test 2: realloc without null check
    FalseNegativeTest(
        cwe="CWE-416",
        name="realloc without null check",
        description="realloc failure loses original pointer",
        filename="realloc.c",
        code='''
void resize(char **buf, size_t newsize) {
    *buf = realloc(*buf, newsize);  // If realloc fails, original is leaked
    if (*buf == NULL) return;
}
''',
        expected_rule_ids=["MS005"],
    ),

    # Test 3: Array decay loses size
    FalseNegativeTest(
        cwe="CWE-119",
        name="Array decay sizeof",
        description="sizeof on pointer gives wrong size",
        filename="sizeof.c",
        code='''
void process(char *buf) {
    char local[100];
    memcpy(local, buf, sizeof(buf));  // sizeof(buf) is 8, not buffer size
}
''',
        expected_rule_ids=["MS004"],
    ),

    # Test 4: snprintf truncation not checked
    FalseNegativeTest(
        cwe="CWE-119",
        name="snprintf truncation unchecked",
        description="snprintf return value not checked for truncation",
        filename="snprintf.c",
        code='''
void format(char *dest, size_t size, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(dest, size, fmt, args);  // Truncation silently ignored
    va_end(args);
}
''',
        expected_rule_ids=["MS001"],
    ),

    # Test 5: Integer underflow in size
    FalseNegativeTest(
        cwe="CWE-190",
        name="Integer underflow in size calc",
        description="Subtraction can underflow to huge value",
        filename="underflow.c",
        code='''
void copy_data(char *dest, size_t dest_size, char *src, size_t header_size) {
    size_t data_size = dest_size - header_size;  // Underflow if header_size > dest_size
    memcpy(dest, src, data_size);
}
''',
        expected_rule_ids=["MS008"],
    ),
]


# =============================================================================
# FASE 38: CONCURRENCY FALSE NEGATIVE TESTS
# =============================================================================

CONCURRENCY_TESTS = [
    # Test 1: Check-then-act without lock
    FalseNegativeTest(
        cwe="CWE-362",
        name="Check-then-act race",
        description="Check and modify without atomicity",
        filename="check_act.py",
        code='''
import threading

counter = 0
def increment():
    global counter
    if counter < 100:  # Check
        counter += 1   # Act - race between check and act
''',
        expected_rule_ids=["CC001", "CC008"],
    ),

    # Test 2: Double-checked locking broken
    FalseNegativeTest(
        cwe="CWE-362",
        name="Broken double-checked locking",
        description="Classic broken double-checked locking pattern",
        filename="dcl.java",
        code='''
public class Singleton {
    private static Singleton instance;

    public static Singleton getInstance() {
        if (instance == null) {  // First check
            synchronized(Singleton.class) {
                if (instance == null) {  // Second check
                    instance = new Singleton();  // Can be reordered!
                }
            }
        }
        return instance;
    }
}
''',
        expected_rule_ids=["CC001", "CC007"],
    ),

    # Test 3: asyncio without proper sync
    FalseNegativeTest(
        cwe="CWE-362",
        name="asyncio shared state",
        description="Asyncio coroutines sharing mutable state",
        filename="async_race.py",
        code='''
import asyncio

shared_list = []

async def producer():
    for i in range(100):
        shared_list.append(i)  # Not thread-safe in asyncio with threads

async def consumer():
    while len(shared_list) > 0:
        shared_list.pop()  # Race condition
''',
        expected_rule_ids=["CC001"],
    ),

    # Test 4: Goroutine closure variable
    FalseNegativeTest(
        cwe="CWE-362",
        name="Goroutine closure capture",
        description="Go closure captures loop variable by reference",
        filename="closure.go",
        code='''
package main

func main() {
    for i := 0; i < 10; i++ {
        go func() {
            println(i)  // Captures i by reference, race condition
        }()
    }
}
''',
        expected_rule_ids=["CC001"],
    ),

    # Test 5: Read-modify-write without atomic
    FalseNegativeTest(
        cwe="CWE-362",
        name="Non-atomic increment",
        description="Increment is not atomic operation",
        filename="nonatomic.cpp",
        code='''
#include <thread>

int counter = 0;

void increment() {
    for (int i = 0; i < 1000; i++) {
        counter++;  // Read-modify-write is not atomic
    }
}
''',
        expected_rule_ids=["CC001", "CC008"],
    ),
]


# =============================================================================
# FASE 36: CRYPTO FALSE NEGATIVE TESTS
# =============================================================================

CRYPTO_TESTS = [
    # Test 1: Base64 used as encryption
    FalseNegativeTest(
        cwe="CWE-327",
        name="Base64 as encryption",
        description="Base64 encoding used thinking it's encryption",
        filename="base64_crypto.py",
        code='''
import base64

def encrypt_password(password):
    return base64.b64encode(password.encode()).decode()  # NOT encryption!

def decrypt_password(encoded):
    return base64.b64decode(encoded).decode()
''',
        expected_rule_ids=["CR006"],
    ),

    # Test 2: XOR "encryption"
    FalseNegativeTest(
        cwe="CWE-327",
        name="XOR cipher",
        description="Simple XOR used for 'encryption'",
        filename="xor.py",
        code='''
def xor_encrypt(data, key):
    return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))
''',
        expected_rule_ids=["CR006"],
    ),

    # Test 3: AES-CBC without HMAC
    FalseNegativeTest(
        cwe="CWE-327",
        name="AES-CBC without authentication",
        description="CBC mode without MAC is vulnerable to padding oracle",
        filename="cbc.py",
        code='''
from Crypto.Cipher import AES

def encrypt(key, plaintext):
    cipher = AES.new(key, AES.MODE_CBC)
    return cipher.iv + cipher.encrypt(pad(plaintext))
''',
        expected_rule_ids=["CR007"],
    ),

    # Test 4: Static IV
    FalseNegativeTest(
        cwe="CWE-329",
        name="Static IV in encryption",
        description="Using constant IV defeats encryption",
        filename="static_iv.py",
        code='''
from Crypto.Cipher import AES

IV = b'0000000000000000'  # Static IV!

def encrypt(key, plaintext):
    cipher = AES.new(key, AES.MODE_CBC, IV)
    return cipher.encrypt(pad(plaintext))
''',
        expected_rule_ids=["CR007", "CR008"],
    ),

    # Test 5: bcrypt with low cost
    FalseNegativeTest(
        cwe="CWE-916",
        name="bcrypt low cost factor",
        description="bcrypt with cost < 10 is too fast",
        filename="bcrypt.py",
        code='''
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4))  # Too low!
''',
        expected_rule_ids=["CR009"],
    ),
]


# =============================================================================
# FASE 36: CONTROL FLOW FALSE NEGATIVE TESTS
# =============================================================================

CONTROL_FLOW_TESTS = [
    # Test 1: Loop with side-effect in condition
    FalseNegativeTest(
        cwe="CWE-835",
        name="Side effect in loop condition",
        description="Function call in loop condition may cause infinite loop",
        filename="side_effect.js",
        code='''
function process(items) {
    while (items.pop()) {  // Relies on truthiness, may loop forever with 0
        console.log("processing");
    }
}
''',
        expected_rule_ids=["CF002"],
    ),

    # Test 2: Unreachable code after return
    FalseNegativeTest(
        cwe="CWE-561",
        name="Unreachable code",
        description="Code after return is never executed",
        filename="unreachable.js",
        code='''
function calculate(x) {
    return x * 2;
    console.log("This never runs");  // Dead code
    return x * 3;
}
''',
        expected_rule_ids=["CF021"],
    ),

    # Test 3: switch with intentional fallthrough comment missing
    FalseNegativeTest(
        cwe="CWE-484",
        name="Switch fallthrough ambiguous",
        description="Intentional fallthrough without comment",
        filename="switch.java",
        code='''
public void handle(int code) {
    switch (code) {
        case 1:
            doA();
        case 2:  // Is fallthrough intentional?
            doB();
            break;
    }
}
''',
        expected_rule_ids=["CF020"],
    ),

    # Test 4: Nested ternary confusion
    FalseNegativeTest(
        cwe="CWE-783",
        name="Nested ternary operators",
        description="Nested ternary is hard to read and error-prone",
        filename="ternary.js",
        code='''
function getValue(a, b, c) {
    return a > 0 ? b > 0 ? b : c : c > 0 ? c : 0;  // What does this even do?
}
''',
        expected_rule_ids=["CF011"],
    ),

    # Test 5: Exception swallowing
    FalseNegativeTest(
        cwe="CWE-390",
        name="Empty exception handler",
        description="Exception caught but not handled",
        filename="swallow.py",
        code='''
def load_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except Exception:
        pass  # Silently swallows ALL exceptions
''',
        expected_rule_ids=["CF030"],
    ),
]


# =============================================================================
# FASE 36: BOOLEAN LOGIC FALSE NEGATIVE TESTS
# =============================================================================

BOOLEAN_LOGIC_TESTS = [
    # Test 1: Always true/false condition
    FalseNegativeTest(
        cwe="CWE-570",
        name="Always false condition",
        description="Condition that is always false",
        filename="always_false.js",
        code='''
function check(x) {
    if (x > 10 && x < 5) {  // Impossible condition
        console.log("Never reached");
    }
}
''',
        expected_rule_ids=["BL030"],
    ),

    # Test 2: Null check after dereference
    FalseNegativeTest(
        cwe="CWE-476",
        name="Null check after use",
        description="Object used before null check",
        filename="null_check.java",
        code='''
public void process(String s) {
    int len = s.length();  // Dereference
    if (s != null) {       // Null check after use!
        System.out.println(len);
    }
}
''',
        expected_rule_ids=["BL040"],
    ),

    # Test 3: Boolean assignment instead of comparison
    FalseNegativeTest(
        cwe="CWE-480",
        name="Boolean assignment",
        description="Assigning boolean instead of comparing",
        filename="bool_assign.py",
        code='''
def is_valid(x):
    valid = True
    if valid = False:  # Assignment! Not comparison (Python won't allow this actually)
        return False
''',
        expected_rule_ids=["BL001"],
    ),

    # Test 4: De Morgan's law violation
    FalseNegativeTest(
        cwe="CWE-480",
        name="Incorrect De Morgan",
        description="Incorrect negation of compound condition",
        filename="demorgan.js",
        code='''
function check(a, b) {
    // Wrong: !(a && b) should be (!a || !b), not (!a && !b)
    if (!a && !b) {  // May be incorrect depending on intent
        console.log("neither");
    }
}
''',
        expected_rule_ids=["BL010"],
    ),

    # Test 5: Yoda conditions can hide bugs
    FalseNegativeTest(
        cwe="CWE-480",
        name="Yoda condition hiding error",
        description="Yoda style can hide assignment bugs",
        filename="yoda.c",
        code='''
void check(int x) {
    if (NULL = ptr) {  // Assignment to NULL, always false
        process(ptr);
    }
}
''',
        expected_rule_ids=["BL001"],
    ),
]


# =============================================================================
# GENERIC SECURITY FALSE NEGATIVE TESTS
# =============================================================================

GENERIC_SECURITY_TESTS = [
    # Test 1: UUID as token
    FalseNegativeTest(
        cwe="CWE-330",
        name="UUID as security token",
        description="UUID v1/v4 used as security token",
        filename="uuid_token.py",
        code='''
import uuid

def generate_reset_token():
    return str(uuid.uuid4())  # UUID4 is not cryptographically secure for tokens
''',
        expected_rule_ids=["GEN-CWE-337-001"],
    ),

    # Test 2: Auth check without return
    FalseNegativeTest(
        cwe="CWE-602",
        name="Auth check continues",
        description="Authentication failure doesn't stop execution",
        filename="auth.py",
        code='''
def admin_page(request):
    if not request.user.is_admin:
        flash("Not authorized")  # Warning shown but execution continues!

    return render_admin_dashboard()  # Executed even for non-admins
''',
        expected_rule_ids=["GEN-CWE-602-001"],
    ),

    # Test 3: Permission check logged only
    FalseNegativeTest(
        cwe="CWE-602",
        name="Permission check logs only",
        description="Permission failure only logs, doesn't block",
        filename="perm.java",
        code='''
public void deleteUser(User actor, User target) {
    if (!actor.hasPermission("delete_users")) {
        logger.warn("Unauthorized delete attempt by " + actor.getId());
    }

    userRepository.delete(target);  // Executed anyway!
}
''',
        expected_rule_ids=["GEN-CWE-602-001"],
    ),

    # Test 4: Timing attack in password comparison
    FalseNegativeTest(
        cwe="CWE-208",
        name="Timing attack vulnerable",
        description="String comparison leaks password length",
        filename="timing.py",
        code='''
def verify_password(input_password, stored_password):
    return input_password == stored_password  # Timing attack vulnerable
''',
        expected_rule_ids=["GEN-CWE-208-001"],
    ),

    # Test 5: Math.random for session ID
    FalseNegativeTest(
        cwe="CWE-330",
        name="Math.random for session",
        description="Predictable session ID generation",
        filename="session.js",
        code='''
function generateSessionId() {
    return Math.random().toString(36).substring(2);
}
''',
        expected_rule_ids=["GEN-CWE-337-001"],
    ),
]


async def run_scanner_tests(scanner, tests: List[FalseNegativeTest], scanner_name: str):
    """Run tests for a specific scanner."""
    print(f"\n{'='*60}")
    print(f"Testing {scanner_name}")
    print(f"{'='*60}")

    results = []

    for test in tests:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / test.filename
            test_file.write_text(test.code)

            try:
                result = await scanner.scan(test_file)
                detected_rules = [f.rule_id for f in result.findings]
            except Exception as e:
                print(f"  ERROR scanning {test.name}: {e}")
                detected_rules = []

            detected_expected = [r for r in test.expected_rule_ids if r in detected_rules]
            is_false_negative = len(detected_expected) == 0

            status = "❌ FALSE NEGATIVE" if is_false_negative else "✓ Detected"
            print(f"\n{status}: {test.name}")
            print(f"  CWE: {test.cwe}")
            print(f"  Expected: {test.expected_rule_ids}")
            print(f"  Detected: {detected_rules}")

            if is_false_negative:
                results.append({
                    'test': test,
                    'detected_rules': detected_rules,
                })

    return results


async def run_all_tests():
    """Run all false negative tests."""
    all_results = {}

    # Fase 38: Memory Safety
    memory_scanner = create_memory_safety_detector()
    all_results["Memory Safety (CWE-119, CWE-416, CWE-190)"] = await run_scanner_tests(
        memory_scanner, MEMORY_SAFETY_TESTS, "Fase 38: Memory Safety Detector"
    )

    # Fase 38: Concurrency
    concurrency_scanner = create_concurrency_error_detector()
    all_results["Concurrency (CWE-362, CWE-367, CWE-833)"] = await run_scanner_tests(
        concurrency_scanner, CONCURRENCY_TESTS, "Fase 38: Concurrency Error Detector"
    )

    # Fase 36: Crypto
    crypto_scanner = create_crypto_error_detector()
    all_results["Crypto (CWE-327, CWE-328, CWE-321, CWE-798)"] = await run_scanner_tests(
        crypto_scanner, CRYPTO_TESTS, "Fase 36: Crypto Error Detector"
    )

    # Fase 36: Control Flow
    control_flow_scanner = create_control_flow_logic_detector()
    all_results["Control Flow (CWE-193, CWE-481, CWE-484, CWE-835)"] = await run_scanner_tests(
        control_flow_scanner, CONTROL_FLOW_TESTS, "Fase 36: Control Flow Logic Detector"
    )

    # Fase 36: Boolean Logic
    boolean_scanner = create_boolean_logic_detector()
    all_results["Boolean Logic (CWE-480, CWE-783, CWE-843)"] = await run_scanner_tests(
        boolean_scanner, BOOLEAN_LOGIC_TESTS, "Fase 36: Boolean Logic Detector"
    )

    # Generic Security
    generic_scanner = create_generic_security_scanner()
    all_results["Generic Security (CWE-337, CWE-602, CWE-208)"] = await run_scanner_tests(
        generic_scanner, GENERIC_SECURITY_TESTS, "Generic Security Scanner"
    )

    return all_results


def generate_report(results: Dict[str, List[Any]]) -> str:
    """Generate markdown report of all false negatives."""
    report = ["# Extended False Negative Analysis Report\n"]
    report.append("Analysis of all security scanners beyond Fase 39.\n\n")

    total_false_negatives = 0

    for category, false_negatives in results.items():
        report.append(f"## {category}\n\n")

        if not false_negatives:
            report.append("✓ **No false negatives found** - all test patterns were detected.\n\n")
        else:
            total_false_negatives += len(false_negatives)
            report.append(f"**{len(false_negatives)} false negative(s) found:**\n\n")

            for fn in false_negatives:
                test = fn['test']
                report.append(f"### {test.name}\n\n")
                report.append(f"**CWE:** {test.cwe}\n\n")
                report.append(f"**Description:** {test.description}\n\n")
                report.append(f"**Expected Rules:** {', '.join(test.expected_rule_ids)}\n\n")
                report.append(f"**Detected Rules:** {', '.join(fn['detected_rules']) or 'None'}\n\n")
                ext = test.filename.split('.')[-1]
                report.append(f"**Vulnerable Code ({test.filename}):**\n")
                report.append(f"```{ext}\n{test.code.strip()}\n```\n\n")

    report.append(f"---\n\n## Summary\n\n")
    report.append(f"**Total False Negatives Found:** {total_false_negatives}\n\n")

    for category, false_negatives in results.items():
        count = len(false_negatives)
        status = "✓" if count == 0 else f"❌ {count}"
        report.append(f"- {category}: {status}\n")

    return '\n'.join(report)


if __name__ == '__main__':
    results = asyncio.run(run_all_tests())
    report = generate_report(results)

    report_path = Path(__file__).parent / 'extended_false_negative_report.md'
    report_path.write_text(report)
    print(f"\n\nReport written to: {report_path}")
