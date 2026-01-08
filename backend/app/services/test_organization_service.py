"""
Test Organization Service

Week 57: Standardized test folder structure for all projects.

This service manages the test organization during development:
- Creates standard test folder structure
- Organizes tests by type (unit, module, integration, e2e)
- Tracks test results and coverage
- Provides feedback to developers via Tessa (Test Agent)

Test Folder Structure:
```
tests/
├── README.md                 # Test overview & instructions
├── unit/                     # Unit tests (single function/class)
│   └── [module]/
├── module/                   # Module tests (component level)
│   └── [module]/
├── integration/              # Integration tests (cross-component)
│   └── [feature]/
├── e2e/                      # End-to-end tests (full workflows)
│   ├── screenshots/
│   └── [testcase]/
├── fixtures/                 # Shared test data
└── reports/                  # Test results & coverage
    ├── latest/
    └── history/
```
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    """Types of tests in the hierarchy."""
    UNIT = "unit"
    MODULE = "module"
    INTEGRATION = "integration"
    E2E = "e2e"


class TestStatus(str, Enum):
    """Status of a test execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


# Standard test folder structure
TEST_FOLDER_STRUCTURE = {
    "unit": {
        "description": "Unit tests - test single functions or classes in isolation",
        "naming": "test_[function]_[scenario].py",
        "agent": "Tessa",
    },
    "module": {
        "description": "Module tests - test a complete module/component",
        "naming": "test_[module]_[feature].py",
        "agent": "Tessa",
    },
    "integration": {
        "description": "Integration tests - test cross-component interactions",
        "naming": "test_[feature]_integration.py",
        "agent": "Tessa",
    },
    "e2e": {
        "description": "End-to-end tests - test complete user workflows",
        "naming": "TC[NNN]_[workflow].md + screenshots/",
        "agent": "Tessa",
        "subfolders": ["screenshots"],
    },
    "fixtures": {
        "description": "Shared test data and fixtures",
        "naming": "[domain]_fixtures.py",
    },
    "reports": {
        "description": "Test results and coverage reports",
        "subfolders": ["latest", "history"],
    },
}


# Test README template
TEST_README_TEMPLATE = """# Tests - {project_name}

**Project:** {project_name}
**Generated:** {generation_date}
**Test Agent:** Tessa

---

## Test Structuur

```
tests/
├── unit/           # Unit tests ({unit_count} tests)
├── module/         # Module tests ({module_count} tests)
├── integration/    # Integration tests ({integration_count} tests)
├── e2e/            # E2E tests ({e2e_count} tests)
├── fixtures/       # Shared test data
└── reports/        # Test results
```

---

## Test Types

### Unit Tests (`unit/`)
Test individuele functies of classes in isolatie.
- **Naming**: `test_[function]_[scenario].py`
- **Run**: `pytest tests/unit/`

### Module Tests (`module/`)
Test complete modules/componenten.
- **Naming**: `test_[module]_[feature].py`
- **Run**: `pytest tests/module/`

### Integration Tests (`integration/`)
Test cross-component interacties.
- **Naming**: `test_[feature]_integration.py`
- **Run**: `pytest tests/integration/`

### E2E Tests (`e2e/`)
Test complete user workflows met UI validatie.
- **Naming**: `TC[NNN]_[workflow].md`
- **Screenshots**: `e2e/screenshots/`
- **Run**: Via Tessa agent of Playwright

---

## Test Coverage

| Type | Tests | Passed | Failed | Coverage |
|------|-------|--------|--------|----------|
| Unit | {unit_count} | - | - | - |
| Module | {module_count} | - | - | - |
| Integration | {integration_count} | - | - | - |
| E2E | {e2e_count} | - | - | - |

---

## Laatste Test Run

**Datum:** -
**Status:** Geen tests uitgevoerd
**Agent:** Tessa

---

## Voor Tessa (Test Agent)

### Bij nieuwe code:
1. Genereer unit tests voor nieuwe functies
2. Update module tests indien nodig
3. Voeg integration tests toe voor nieuwe features
4. Maak e2e tests voor user-facing changes

### Bij test failures:
1. Analyseer failure reason
2. Genereer fix suggesties
3. Stuur feedback naar developer
4. Track in reports/

---

*Dit document wordt bijgewerkt door Tessa na elke test run.*
"""


class TestOrganizationService:
    """Service for managing test organization in projects."""

    def __init__(self):
        self._test_results: Dict[str, List[Dict[str, Any]]] = {}

    def initialize_test_structure(
        self,
        project_path: Path,
        project_name: str,
    ) -> Dict[str, Any]:
        """
        Initialize the standard test folder structure for a project.

        Args:
            project_path: Root path of the project
            project_name: Name of the project

        Returns:
            Summary of created structure
        """
        tests_path = project_path / "tests"
        created_folders = []

        # Create main tests folder
        tests_path.mkdir(parents=True, exist_ok=True)
        created_folders.append("tests/")

        # Create subfolders
        for folder, config in TEST_FOLDER_STRUCTURE.items():
            folder_path = tests_path / folder
            folder_path.mkdir(exist_ok=True)
            created_folders.append(f"tests/{folder}/")

            # Create subfolders if defined
            if "subfolders" in config:
                for subfolder in config["subfolders"]:
                    (folder_path / subfolder).mkdir(exist_ok=True)
                    created_folders.append(f"tests/{folder}/{subfolder}/")

            # Create __init__.py for Python test folders
            if folder in ["unit", "module", "integration"]:
                (folder_path / "__init__.py").touch()

        # Create README
        readme_content = TEST_README_TEMPLATE.format(
            project_name=project_name,
            generation_date=datetime.now().strftime("%Y-%m-%d"),
            unit_count=0,
            module_count=0,
            integration_count=0,
            e2e_count=0,
        )
        (tests_path / "README.md").write_text(readme_content)
        created_folders.append("tests/README.md")

        logger.info(f"Initialized test structure for {project_name} at {tests_path}")

        return {
            "project": project_name,
            "tests_path": str(tests_path),
            "created": created_folders,
            "structure": TEST_FOLDER_STRUCTURE,
        }

    def get_test_counts(self, project_path: Path) -> Dict[str, int]:
        """Count tests by type in a project."""
        tests_path = project_path / "tests"
        counts = {
            "unit": 0,
            "module": 0,
            "integration": 0,
            "e2e": 0,
        }

        if not tests_path.exists():
            return counts

        # Count Python test files
        for test_type in ["unit", "module", "integration"]:
            type_path = tests_path / test_type
            if type_path.exists():
                counts[test_type] = len(list(type_path.glob("**/test_*.py")))

        # Count E2E test cases (markdown files)
        e2e_path = tests_path / "e2e"
        if e2e_path.exists():
            counts["e2e"] = len(list(e2e_path.glob("TC*.md")))

        return counts

    def register_test_result(
        self,
        project_name: str,
        test_type: TestType,
        test_name: str,
        status: TestStatus,
        duration_ms: int = 0,
        error_message: Optional[str] = None,
        screenshots: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a test execution result.

        This is called by Tessa after running tests.
        """
        if project_name not in self._test_results:
            self._test_results[project_name] = []

        result = {
            "test_type": test_type.value,
            "test_name": test_name,
            "status": status.value,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "error_message": error_message,
            "screenshots": screenshots or [],
        }

        self._test_results[project_name].append(result)

        return result

    def get_test_results(
        self,
        project_name: str,
        test_type: Optional[TestType] = None,
    ) -> List[Dict[str, Any]]:
        """Get test results for a project, optionally filtered by type."""
        results = self._test_results.get(project_name, [])

        if test_type:
            results = [r for r in results if r["test_type"] == test_type.value]

        return results

    def generate_test_report(
        self,
        project_path: Path,
        project_name: str,
    ) -> Dict[str, Any]:
        """
        Generate a test report for a project.

        This creates a report in tests/reports/latest/
        """
        results = self._test_results.get(project_name, [])
        counts = self.get_test_counts(project_path)

        # Calculate statistics
        total = len(results)
        passed = len([r for r in results if r["status"] == "passed"])
        failed = len([r for r in results if r["status"] == "failed"])
        errors = len([r for r in results if r["status"] == "error"])

        report = {
            "project": project_name,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "N/A",
            },
            "test_counts": counts,
            "results": results,
            "failures": [r for r in results if r["status"] in ["failed", "error"]],
        }

        # Save report
        reports_path = project_path / "tests" / "reports" / "latest"
        reports_path.mkdir(parents=True, exist_ok=True)

        report_file = reports_path / "test_report.json"
        report_file.write_text(json.dumps(report, indent=2))

        # Also save to history
        history_path = project_path / "tests" / "reports" / "history"
        history_path.mkdir(parents=True, exist_ok=True)

        history_file = history_path / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        history_file.write_text(json.dumps(report, indent=2))

        logger.info(f"Generated test report for {project_name}: {passed}/{total} passed")

        return report

    def get_developer_feedback(
        self,
        project_name: str,
    ) -> Dict[str, Any]:
        """
        Generate feedback for the developer based on test results.

        This is used by Tessa to communicate issues back to the developer.
        """
        results = self._test_results.get(project_name, [])
        failures = [r for r in results if r["status"] in ["failed", "error"]]

        if not failures:
            return {
                "status": "success",
                "message": "Alle tests geslaagd!",
                "action_required": False,
                "failures": [],
            }

        # Group failures by type
        failures_by_type: Dict[str, List[Dict]] = {}
        for f in failures:
            test_type = f["test_type"]
            if test_type not in failures_by_type:
                failures_by_type[test_type] = []
            failures_by_type[test_type].append(f)

        # Generate feedback message
        feedback_items = []
        for test_type, type_failures in failures_by_type.items():
            feedback_items.append(f"**{test_type.upper()}**: {len(type_failures)} failures")
            for f in type_failures[:3]:  # Show max 3 per type
                feedback_items.append(f"  - {f['test_name']}: {f.get('error_message', 'Unknown error')}")

        return {
            "status": "failure",
            "message": f"{len(failures)} test(s) gefaald - actie vereist",
            "action_required": True,
            "failures": failures,
            "feedback": "\n".join(feedback_items),
            "recommendation": "Fix de gefaalde tests voordat je verder gaat met development.",
        }


# Singleton instance
_test_organization_service: Optional[TestOrganizationService] = None


def get_test_organization_service() -> TestOrganizationService:
    """Get or create the TestOrganizationService singleton."""
    global _test_organization_service
    if _test_organization_service is None:
        _test_organization_service = TestOrganizationService()
    return _test_organization_service
