"""
Quick test to verify scanner timeout works with file-by-file progress.

Tests that:
1. File progress callback is called
2. Timeout actually works (scanner can be interrupted between files)
3. Partial results are returned on timeout
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.security_scanner.orchestrator import SecurityScanOrchestrator
from app.services.security_scanner.models.findings import ScannerType


async def test_scanner_with_short_timeout():
    """Test scanner with a very short timeout to verify interruption works."""

    print("=" * 70)
    print("SCANNER TIMEOUT TEST")
    print("=" * 70)
    print()

    # Use a small test directory first to verify basics work
    test_path = Path("/home/eddie/Projects/MarkdownTaskManager/backend/app/services/security_scanner")

    if not test_path.exists():
        print(f"ERROR: Test path not found: {test_path}")
        return

    # Count files
    file_count = len(list(test_path.rglob("*.py")))
    print(f"Test path: {test_path}")
    print(f"Python files: {file_count}")
    print()

    # Create orchestrator with just a few scanners
    orchestrator = SecurityScanOrchestrator(
        enabled_scanners={
            ScannerType.SECRET_SCANNER,
            ScannerType.OWASP_SCANNER,
        }
    )

    print(f"Available scanners: {orchestrator.get_available_scanners()}")
    print()

    # Track progress
    file_progress_calls = []
    scanner_progress_calls = []

    def scanner_progress(current: int, total: int, scanner_name: str):
        scanner_progress_calls.append((current, total, scanner_name))
        print(f"  [SCANNER] {current + 1}/{total}: {scanner_name}")

    def file_progress(current_file: int, total_files: int, file_path: str, scanner_name: str):
        file_progress_calls.append((current_file, total_files, file_path, scanner_name))
        if current_file % 10 == 0 or current_file == total_files - 1:
            file_name = Path(file_path).name if file_path != "complete" else "DONE"
            print(f"    [{scanner_name}] {current_file + 1}/{total_files}: {file_name}")

    orchestrator.set_progress_callback(scanner_progress)
    orchestrator.set_file_progress_callback(file_progress)

    print("-" * 70)
    print("TEST 1: Normal scan (should complete)")
    print("-" * 70)

    start = datetime.now()

    try:
        report = await orchestrator.scan(
            target_path=test_path,
            timeout_per_scanner=60,  # 60 second timeout per scanner
            total_timeout=120,  # 2 minute total
        )

        elapsed = (datetime.now() - start).total_seconds()
        print()
        print(f"Result: {report.total_findings} findings in {elapsed:.1f}s")
        print(f"Scanner progress calls: {len(scanner_progress_calls)}")
        print(f"File progress calls: {len(file_progress_calls)}")
        print(f"Scanners used: {[s.value for s in report.scanners_used]}")
        print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Now test with a very short timeout
    print("-" * 70)
    print("TEST 2: Very short timeout (should trigger timeout)")
    print("-" * 70)

    # Reset tracking
    file_progress_calls = []
    scanner_progress_calls = []

    start = datetime.now()

    try:
        report = await orchestrator.scan(
            target_path=test_path,
            timeout_per_scanner=0.1,  # 100ms timeout - should trigger!
            total_timeout=1,  # 1 second total
        )

        elapsed = (datetime.now() - start).total_seconds()
        print()
        print(f"Result: {report.total_findings} findings in {elapsed:.1f}s")
        print(f"Scanner progress calls: {len(scanner_progress_calls)}")
        print(f"File progress calls: {len(file_progress_calls)}")

        # Check if any scanner reported timeout error
        for result in report.scan_results:
            if result.errors:
                print(f"Scanner {result.scanner.value} errors: {result.errors}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_scanner_with_short_timeout())
