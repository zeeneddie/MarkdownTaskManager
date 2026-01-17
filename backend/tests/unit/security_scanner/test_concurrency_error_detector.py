"""
Tests for Fase 38 ConcurrencyErrorDetector.

Tests cover all 8 concurrency/race condition detection rules:
- CC001: Thread creation with shared data
- CC002: TOCTOU (time-of-check time-of-use) race
- CC003: Signal handler race
- CC004: Nested locks (potential deadlock)
- CC005: Lock not released on error path
- CC006: Thread-unsafe function usage
- CC007: Volatile misuse for synchronization
- CC008: Data race on shared flag
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.concurrency_error_detector import (
    ConcurrencyErrorDetector,
    ConcurrencyRule,
    CONCURRENCY_RULES,
    create_concurrency_error_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestConcurrencyErrorDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = ConcurrencyErrorDetector()
        assert scanner.scanner_type == ScannerType.CONCURRENCY_ERROR

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = ConcurrencyErrorDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = ConcurrencyErrorDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_8_rules(self):
        """Should have 8 concurrency detection rules."""
        assert len(CONCURRENCY_RULES) == 8

    def test_supported_languages(self):
        """Should support C, C++, Java, Python, and Go."""
        scanner = ConcurrencyErrorDetector()
        languages = scanner.supported_languages
        assert "c" in languages
        assert "cpp" in languages
        assert "java" in languages
        assert "python" in languages
        assert "go" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = ConcurrencyErrorDetector()
        extensions = scanner.supported_extensions
        assert ".c" in extensions
        assert ".cpp" in extensions
        assert ".java" in extensions
        assert ".py" in extensions
        assert ".go" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_concurrency_error_detector()
        assert isinstance(scanner, ConcurrencyErrorDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in CONCURRENCY_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in CONCURRENCY_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_cwe_362(self):
        """Should cover CWE-362 (Race Condition) from CWE Top 25."""
        cwe_coverage = set()
        for rule in CONCURRENCY_RULES:
            cwe_coverage.update(rule.cwe_ids)

        # CWE-362 is the CWE Top 25 gap that Fase 38 addresses
        assert "CWE-362" in cwe_coverage, "CWE-362 (Race Condition) not covered"


# =============================================================================
# CC001: THREAD CREATION WITH SHARED DATA
# =============================================================================


class TestThreadCreation:
    """Tests for thread creation with shared data detection."""

    @pytest.mark.asyncio
    async def test_detect_pthread_create_with_global_c(self, tmp_path):
        """Should detect pthread_create accessing global variable."""
        test_file = tmp_path / "threads.c"
        test_file.write_text('''
#include <pthread.h>

int global_counter = 0;  // shared mutable state

void* worker(void* arg) {
    global_counter++;
    return NULL;
}

int main() {
    pthread_t thread;
    pthread_create(&thread, NULL, worker, NULL);
    return 0;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        thread_finding = next((f for f in result.findings if f.rule_id == "CC001"), None)
        assert thread_finding is not None
        assert "CWE-362" in thread_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_std_thread_cpp(self, tmp_path):
        """Should detect std::thread with shared class member."""
        test_file = tmp_path / "threads.cpp"
        test_file.write_text('''
#include <thread>

class Counter {
    int mutable value = 0;  // shared mutable state

    void worker() {
        value++;
    }

public:
    void start() {
        std::thread t(&Counter::worker, this);
    }
};
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_threading_python(self, tmp_path):
        """Should detect threading.Thread with shared state."""
        test_file = tmp_path / "threads.py"
        test_file.write_text('''
import threading

shared_data = []  # global shared state

def worker():
    shared_data.append(1)

t = threading.Thread(target=worker)
t.start()
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_goroutine_go(self, tmp_path):
        """Should detect goroutine with shared variable."""
        test_file = tmp_path / "concurrent.go"
        test_file.write_text('''
package main

var shared = 0  // global shared state

func main() {
    go func() {
        shared++
    }()
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CC002: TOCTOU (TIME-OF-CHECK TIME-OF-USE)
# =============================================================================


class TestTOCTOU:
    """Tests for TOCTOU race condition detection."""

    @pytest.mark.asyncio
    async def test_detect_toctou_access_open_c(self, tmp_path):
        """Should detect TOCTOU with access() then open()."""
        test_file = tmp_path / "toctou.c"
        test_file.write_text('''
#include <unistd.h>
#include <fcntl.h>

void unsafe_open(const char* path) {
    if (access(path, R_OK) == 0) {
        // Race window between check and use!
        int fd = open(path, O_RDONLY);
    }
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        toctou_finding = next((f for f in result.findings if f.rule_id == "CC002"), None)
        assert toctou_finding is not None
        assert "CWE-367" in toctou_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_toctou_exists_open_python(self, tmp_path):
        """Should detect TOCTOU with os.path.exists() then open()."""
        test_file = tmp_path / "toctou.py"
        test_file.write_text('''
import os

def unsafe_read(path):
    if os.path.exists(path):
        # Race window!
        with open(path) as f:
            return f.read()
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        toctou_finding = next((f for f in result.findings if f.rule_id == "CC002"), None)
        assert toctou_finding is not None


# =============================================================================
# CC003: SIGNAL HANDLER RACE
# =============================================================================


class TestSignalHandler:
    """Tests for signal handler race detection."""

    @pytest.mark.asyncio
    async def test_detect_printf_in_signal_handler_c(self, tmp_path):
        """Should detect non-reentrant function in signal handler."""
        test_file = tmp_path / "signal.c"
        test_file.write_text('''
#include <signal.h>
#include <stdio.h>

void handler(int sig) {
    printf("Signal received: %d\\n", sig);  // Not async-signal-safe!
}

int main() {
    signal(SIGINT, handler);
    return 0;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        signal_finding = next((f for f in result.findings if f.rule_id == "CC003"), None)
        assert signal_finding is not None
        assert "CWE-479" in signal_finding.cwe_ids


# =============================================================================
# CC004: NESTED LOCKS (DEADLOCK)
# =============================================================================


class TestNestedLocks:
    """Tests for nested lock (deadlock) detection."""

    @pytest.mark.asyncio
    async def test_detect_nested_pthread_mutex_c(self, tmp_path):
        """Should detect nested pthread_mutex_lock calls."""
        test_file = tmp_path / "deadlock.c"
        test_file.write_text('''
#include <pthread.h>

pthread_mutex_t lock1, lock2;

void deadlock_risk() {
    pthread_mutex_lock(&lock1);
    // Some work
    pthread_mutex_lock(&lock2);  // Potential deadlock if another thread locks in reverse order
    pthread_mutex_unlock(&lock2);
    pthread_mutex_unlock(&lock1);
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        deadlock_finding = next((f for f in result.findings if f.rule_id == "CC004"), None)
        assert deadlock_finding is not None
        assert "CWE-833" in deadlock_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_nested_synchronized_java(self, tmp_path):
        """Should detect nested synchronized blocks in Java."""
        test_file = tmp_path / "Deadlock.java"
        test_file.write_text('''
public class Deadlock {
    private Object lock1 = new Object();
    private Object lock2 = new Object();

    void method() {
        synchronized (lock1) {
            // work
            synchronized (lock2) {
                // more work
            }
        }
    }
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_nested_lock_python(self, tmp_path):
        """Should detect nested lock.acquire() in Python."""
        test_file = tmp_path / "deadlock.py"
        test_file.write_text('''
import threading

lock1 = threading.Lock()
lock2 = threading.Lock()

def risky():
    lock1.acquire()
    # work
    lock2.acquire()  # Potential deadlock
    lock2.release()
    lock1.release()
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CC005: LOCK NOT RELEASED
# =============================================================================


class TestLockNotReleased:
    """Tests for lock not released on error path detection."""

    @pytest.mark.asyncio
    async def test_detect_lock_not_released_return_c(self, tmp_path):
        """Should detect lock not released before return."""
        test_file = tmp_path / "leak.c"
        test_file.write_text('''
pthread_mutex_t mutex;

int process(int value) {
    pthread_mutex_lock(&mutex);
    if (value < 0) {
        return -1;  // Lock not released!
    }
    pthread_mutex_unlock(&mutex);
    return 0;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        lock_finding = next((f for f in result.findings if f.rule_id == "CC005"), None)
        assert lock_finding is not None
        assert "CWE-764" in lock_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_lock_not_released_throw_cpp(self, tmp_path):
        """Should detect lock not released before throw."""
        test_file = tmp_path / "leak.cpp"
        test_file.write_text('''
#include <mutex>

std::mutex mtx;

void process(int value) {
    mtx.lock();
    if (value < 0) {
        throw std::runtime_error("Invalid");  // Lock not released!
    }
    mtx.unlock();
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_allow_lock_guard_cpp(self, tmp_path):
        """Should not flag when using RAII lock_guard."""
        test_file = tmp_path / "safe.cpp"
        test_file.write_text('''
#include <mutex>

std::mutex mtx;

void process(int value) {
    std::lock_guard<std::mutex> guard(mtx);
    if (value < 0) {
        throw std::runtime_error("Invalid");  // Safe - RAII releases lock
    }
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        # Should be filtered as false positive
        lock_findings = [f for f in result.findings if f.rule_id == "CC005"]
        assert len(lock_findings) == 0


# =============================================================================
# CC006: THREAD-UNSAFE FUNCTIONS
# =============================================================================


class TestThreadUnsafeFunctions:
    """Tests for thread-unsafe function detection."""

    @pytest.mark.asyncio
    async def test_detect_strtok_in_threaded_code_c(self, tmp_path):
        """Should detect strtok() in multi-threaded context."""
        test_file = tmp_path / "unsafe.c"
        test_file.write_text('''
#include <pthread.h>
#include <string.h>

void* thread_func(void* arg) {
    char* token = strtok(str, ",");  // Not thread-safe!
    return NULL;
}

int main() {
    pthread_t t;
    pthread_create(&t, NULL, thread_func, NULL);
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        unsafe_finding = next((f for f in result.findings if f.rule_id == "CC006"), None)
        assert unsafe_finding is not None
        assert "CWE-820" in unsafe_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_localtime_in_concurrent_code_c(self, tmp_path):
        """Should detect localtime() in concurrent context."""
        test_file = tmp_path / "time.c"
        test_file.write_text('''
#include <pthread.h>
#include <time.h>

void* worker(void* arg) {
    time_t now = time(NULL);
    struct tm* tm = localtime(&now);  // Not thread-safe!
    return NULL;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CC007-CC008: VOLATILE AND DATA RACE
# =============================================================================


class TestVolatileAndDataRace:
    """Tests for volatile misuse and data race detection."""

    @pytest.mark.asyncio
    async def test_detect_volatile_for_thread_sync_c(self, tmp_path):
        """Should detect volatile used for thread synchronization."""
        test_file = tmp_path / "volatile.c"
        test_file.write_text('''
#include <pthread.h>

volatile int running = 1;  // Volatile is not enough for threads!

void* worker(void* arg) {
    while (running) {
        // work
    }
    return NULL;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        volatile_finding = next((f for f in result.findings if f.rule_id == "CC007"), None)
        assert volatile_finding is not None
        assert "CWE-820" in volatile_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_shared_flag_without_atomic_c(self, tmp_path):
        """Should detect shared flag without atomic/volatile."""
        test_file = tmp_path / "flag.c"
        test_file.write_text('''
#include <pthread.h>

int stop_flag = 0;  // Shared without synchronization

void* worker(void* arg) {
    while (!stop_flag) {
        // work
    }
    return NULL;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        flag_finding = next((f for f in result.findings if f.rule_id == "CC008"), None)
        assert flag_finding is not None


# =============================================================================
# DIRECTORY SCANNING
# =============================================================================


class TestDirectoryScanning:
    """Tests for scanning directories."""

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan entire directory recursively."""
        # Create multiple files with different issues
        (tmp_path / "threads.c").write_text('''
#include <pthread.h>
int global = 0;
void* worker(void* arg) { global++; return NULL; }
int main() { pthread_t t; pthread_create(&t, NULL, worker, NULL); }
''')
        (tmp_path / "lock.py").write_text('''
import threading
lock = threading.Lock()
lock.acquire()
lock.acquire()  # Nested
''')

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "Concurrent.java").write_text('''
public class Concurrent {
    void f() {
        synchronized(this) {
            synchronized(that) { }
        }
    }
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 3
        assert len(result.findings) >= 2

    @pytest.mark.asyncio
    async def test_scan_no_issues(self, tmp_path):
        """Should handle clean files."""
        test_file = tmp_path / "safe.c"
        test_file.write_text('''
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
''')

        scanner = ConcurrencyErrorDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        # No concurrency issues in single-threaded code
        assert len(result.findings) == 0


# =============================================================================
# RULES SUMMARY
# =============================================================================


class TestRulesSummary:
    """Tests for rules summary functionality."""

    def test_get_rules_summary(self):
        """Should return structured rules summary."""
        scanner = ConcurrencyErrorDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 8
        assert len(summary["rules"]) == 8
        assert "supported_languages" in summary
        assert len(summary["supported_languages"]) >= 5  # c, cpp, java, python, go

        # Verify CWE coverage info
        assert "cwe_coverage" in summary
        assert "CWE-362" in summary["cwe_coverage"]

        # Verify rule structure
        for rule in summary["rules"]:
            assert "id" in rule
            assert "title" in rule
            assert "severity" in rule
            assert "cwe_ids" in rule
            assert "category" in rule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
