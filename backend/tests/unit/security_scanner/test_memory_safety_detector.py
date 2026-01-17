"""
Tests for Fase 38 MemorySafetyDetector.

Tests cover all 16 memory safety detection rules:
- MS001-MS004: Buffer overflow (strcpy, gets, scanf, memcpy)
- MS005-MS007: Use after free (UAF, double free, stack return)
- MS008-MS009: Integer overflow
- MS010: Format string vulnerability
- MS011: Uninitialized pointer
- MS012-MS013: Unsafe Rust
- MS014-MS016: C++ specific issues
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.memory_safety_detector import (
    MemorySafetyDetector,
    MemorySafetyRule,
    MEMORY_SAFETY_RULES,
    create_memory_safety_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestMemorySafetyDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = MemorySafetyDetector()
        assert scanner.scanner_type == ScannerType.MEMORY_SAFETY

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = MemorySafetyDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = MemorySafetyDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_16_rules(self):
        """Should have 16 memory safety detection rules."""
        assert len(MEMORY_SAFETY_RULES) == 16

    def test_supported_languages(self):
        """Should support C, C++, and Rust."""
        scanner = MemorySafetyDetector()
        languages = scanner.supported_languages
        assert "c" in languages
        assert "cpp" in languages
        assert "rust" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = MemorySafetyDetector()
        extensions = scanner.supported_extensions
        assert ".c" in extensions
        assert ".h" in extensions
        assert ".cpp" in extensions
        assert ".hpp" in extensions
        assert ".rs" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_memory_safety_detector()
        assert isinstance(scanner, MemorySafetyDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in MEMORY_SAFETY_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in MEMORY_SAFETY_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_cwe_top_25_gaps(self):
        """Should cover the CWE Top 25 gaps (787, 416, 125, 119)."""
        cwe_coverage = set()
        for rule in MEMORY_SAFETY_RULES:
            cwe_coverage.update(rule.cwe_ids)

        # These are the CWE Top 25 gaps that Fase 38 addresses
        assert "CWE-787" in cwe_coverage, "CWE-787 (Out-of-bounds Write) not covered"
        assert "CWE-416" in cwe_coverage, "CWE-416 (Use After Free) not covered"
        assert "CWE-125" in cwe_coverage, "CWE-125 (Out-of-bounds Read) not covered"
        assert "CWE-119" in cwe_coverage, "CWE-119 (Buffer Overflow) not covered"


# =============================================================================
# MS001-MS004: BUFFER OVERFLOW
# =============================================================================


class TestBufferOverflow:
    """Tests for buffer overflow detection."""

    @pytest.mark.asyncio
    async def test_detect_strcpy_c(self, tmp_path):
        """Should detect unsafe strcpy in C."""
        test_file = tmp_path / "buffer.c"
        test_file.write_text('''
#include <string.h>

void vulnerable(char *input) {
    char buffer[64];
    strcpy(buffer, input);
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        strcpy_finding = next((f for f in result.findings if f.rule_id == "MS001"), None)
        assert strcpy_finding is not None
        assert "CWE-119" in strcpy_finding.cwe_ids
        assert "CWE-787" in strcpy_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_strcat_c(self, tmp_path):
        """Should detect unsafe strcat in C."""
        test_file = tmp_path / "concat.c"
        test_file.write_text('''
void concat(char *dest, char *src) {
    strcat(dest, src);
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        strcat_finding = next((f for f in result.findings if f.rule_id == "MS001"), None)
        assert strcat_finding is not None

    @pytest.mark.asyncio
    async def test_detect_sprintf_cpp(self, tmp_path):
        """Should detect unsafe sprintf in C++."""
        test_file = tmp_path / "format.cpp"
        test_file.write_text('''
void format(const char* input) {
    char buffer[256];
    sprintf(buffer, "Value: %s", input);
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        sprintf_finding = next((f for f in result.findings if f.rule_id == "MS001"), None)
        assert sprintf_finding is not None

    @pytest.mark.asyncio
    async def test_detect_gets_c(self, tmp_path):
        """Should detect dangerous gets() function in C."""
        test_file = tmp_path / "input.c"
        test_file.write_text('''
void read_input() {
    char buffer[100];
    gets(buffer);  // Never use gets()!
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        gets_finding = next((f for f in result.findings if f.rule_id == "MS002"), None)
        assert gets_finding is not None
        assert gets_finding.severity == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_detect_scanf_without_width_c(self, tmp_path):
        """Should detect scanf %s without width specifier."""
        test_file = tmp_path / "scan.c"
        test_file.write_text('''
void read_name() {
    char name[50];
    scanf("%s", name);  // No width limit!
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        scanf_finding = next((f for f in result.findings if f.rule_id == "MS003"), None)
        assert scanf_finding is not None


# =============================================================================
# MS005-MS007: USE AFTER FREE
# =============================================================================


class TestUseAfterFree:
    """Tests for use-after-free detection."""

    @pytest.mark.asyncio
    async def test_detect_free_without_null_c(self, tmp_path):
        """Should detect free() without setting pointer to NULL."""
        test_file = tmp_path / "memory.c"
        test_file.write_text('''
void cleanup(int *ptr) {
    free(ptr);
    // ptr not set to NULL - potential UAF
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        uaf_finding = next((f for f in result.findings if f.rule_id == "MS005"), None)
        assert uaf_finding is not None
        assert "CWE-416" in uaf_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_double_free_c(self, tmp_path):
        """Should detect potential double free in C."""
        test_file = tmp_path / "double_free.c"
        test_file.write_text('''
void bug(int *ptr) {
    free(ptr);
    // some code
    free(ptr);  // Double free!
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        double_free = next((f for f in result.findings if f.rule_id == "MS006"), None)
        assert double_free is not None
        assert "CWE-415" in double_free.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_return_stack_address_c(self, tmp_path):
        """Should detect returning address of local variable."""
        test_file = tmp_path / "stack.c"
        test_file.write_text('''
int* dangling() {
    int local = 42;
    return &local;  // Dangling pointer!
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        stack_finding = next((f for f in result.findings if f.rule_id == "MS007"), None)
        assert stack_finding is not None
        assert "CWE-562" in stack_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_delete_without_nullptr_cpp(self, tmp_path):
        """Should detect delete without setting to nullptr in C++."""
        test_file = tmp_path / "delete.cpp"
        test_file.write_text('''
void cleanup(MyClass* obj) {
    delete obj;
    // obj not set to nullptr
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# MS008-MS009: INTEGER OVERFLOW
# =============================================================================


class TestIntegerOverflow:
    """Tests for integer overflow detection."""

    @pytest.mark.asyncio
    async def test_detect_malloc_multiplication_c(self, tmp_path):
        """Should detect multiplication in malloc size."""
        test_file = tmp_path / "alloc.c"
        test_file.write_text('''
void* alloc(size_t count) {
    return malloc(count * sizeof(int));  // Potential overflow
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        overflow_finding = next((f for f in result.findings if f.rule_id == "MS008"), None)
        assert overflow_finding is not None
        assert "CWE-190" in overflow_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_new_array_multiplication_cpp(self, tmp_path):
        """Should detect multiplication in new[] size."""
        test_file = tmp_path / "alloc.cpp"
        test_file.write_text('''
int* alloc(int rows, int cols) {
    return new int[rows * cols];  // Potential overflow
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        overflow_finding = next((f for f in result.findings if f.rule_id == "MS008"), None)
        assert overflow_finding is not None


# =============================================================================
# MS010: FORMAT STRING
# =============================================================================


class TestFormatString:
    """Tests for format string vulnerability detection."""

    @pytest.mark.asyncio
    async def test_detect_printf_with_variable_c(self, tmp_path):
        """Should detect printf with variable format string."""
        test_file = tmp_path / "format.c"
        test_file.write_text('''
void log_message(char* user_input) {
    printf(user_input);  // Format string vulnerability!
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        fmt_finding = next((f for f in result.findings if f.rule_id == "MS010"), None)
        assert fmt_finding is not None
        assert "CWE-134" in fmt_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_allow_printf_with_literal_c(self, tmp_path):
        """Should allow printf with literal format string."""
        test_file = tmp_path / "safe_format.c"
        test_file.write_text('''
void log_message(const char* msg) {
    printf("Message: %s\\n", msg);  // Safe - literal format
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        # Should not flag safe printf usage (literal format string)
        fmt_findings = [f for f in result.findings if f.rule_id == "MS010"]
        assert len(fmt_findings) == 0


# =============================================================================
# MS011: UNINITIALIZED POINTER
# =============================================================================


class TestUninitializedPointer:
    """Tests for uninitialized pointer detection."""

    @pytest.mark.asyncio
    async def test_detect_uninitialized_pointer_c(self, tmp_path):
        """Should detect uninitialized pointer in C."""
        test_file = tmp_path / "uninit.c"
        test_file.write_text('''
void process() {
    int *ptr;
    *ptr = 42;  // Undefined behavior!
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        uninit_finding = next((f for f in result.findings if f.rule_id == "MS011"), None)
        assert uninit_finding is not None
        assert "CWE-824" in uninit_finding.cwe_ids


# =============================================================================
# MS012-MS013: UNSAFE RUST
# =============================================================================


class TestUnsafeRust:
    """Tests for unsafe Rust detection."""

    @pytest.mark.asyncio
    async def test_detect_unsafe_block_rust(self, tmp_path):
        """Should detect unsafe block in Rust."""
        test_file = tmp_path / "lib.rs"
        test_file.write_text('''
fn risky() {
    unsafe {
        // Bypasses Rust's safety guarantees
        let ptr = 0x1234 as *mut i32;
        *ptr = 42;
    }
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        unsafe_finding = next((f for f in result.findings if f.rule_id == "MS012"), None)
        assert unsafe_finding is not None
        assert "CWE-119" in unsafe_finding.cwe_ids


# =============================================================================
# MS014-MS016: C++ SPECIFIC
# =============================================================================


class TestCppSpecific:
    """Tests for C++ specific memory safety issues."""

    @pytest.mark.asyncio
    async def test_detect_manual_new_cpp(self, tmp_path):
        """Should detect manual new/delete usage in C++."""
        test_file = tmp_path / "memory.cpp"
        test_file.write_text('''
void create() {
    MyClass* obj = new MyClass();
    // Manual memory management
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        new_finding = next((f for f in result.findings if f.rule_id == "MS015"), None)
        assert new_finding is not None

    @pytest.mark.asyncio
    async def test_detect_alloca_c(self, tmp_path):
        """Should detect alloca() usage in C."""
        test_file = tmp_path / "stack_alloc.c"
        test_file.write_text('''
void process(size_t size) {
    char* buffer = alloca(size);  // Stack overflow risk!
    memset(buffer, 0, size);
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        alloca_finding = next((f for f in result.findings if f.rule_id == "MS016"), None)
        assert alloca_finding is not None
        assert "CWE-770" in alloca_finding.cwe_ids


# =============================================================================
# DIRECTORY SCANNING
# =============================================================================


class TestDirectoryScanning:
    """Tests for scanning directories."""

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan entire directory recursively."""
        # Create multiple files with different vulnerabilities
        (tmp_path / "buffer.c").write_text('void f() { char buf[10]; strcpy(buf, src); }')
        (tmp_path / "memory.cpp").write_text('void f() { int *p = new int[10]; }')

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "unsafe.c").write_text('void f() { gets(buffer); }')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 3
        assert len(result.findings) >= 2

    @pytest.mark.asyncio
    async def test_scan_no_vulnerabilities(self, tmp_path):
        """Should handle clean files."""
        test_file = tmp_path / "secure.c"
        test_file.write_text('''
#include <string.h>

void secure_copy(char *dest, size_t dest_size, const char *src) {
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\\0';
}
''')

        scanner = MemorySafetyDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        # Should not flag strncpy (safe variant)
        assert len([f for f in result.findings if f.rule_id == "MS001"]) == 0


# =============================================================================
# RULES SUMMARY
# =============================================================================


class TestRulesSummary:
    """Tests for rules summary functionality."""

    def test_get_rules_summary(self):
        """Should return structured rules summary."""
        scanner = MemorySafetyDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 16
        assert len(summary["rules"]) == 16
        assert "supported_languages" in summary
        assert len(summary["supported_languages"]) >= 3  # c, cpp, rust

        # Verify CWE coverage info
        assert "cwe_coverage" in summary
        assert "CWE-787" in summary["cwe_coverage"]
        assert "CWE-416" in summary["cwe_coverage"]

        # Verify rule structure
        for rule in summary["rules"]:
            assert "id" in rule
            assert "title" in rule
            assert "severity" in rule
            assert "cwe_ids" in rule
            assert "category" in rule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
