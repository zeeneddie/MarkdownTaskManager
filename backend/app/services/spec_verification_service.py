"""
SpecVerificationService - Agent OS Verification Concepts

Week 59-60: Implements 4 Agent OS concepts:
1. Visual asset validation (verify-spec)
2. Reusability check (verify-spec)
3. Mandatory visuals folder (research-spec)
4. Strict scope limitation (implement-tasks)

Based on patterns from github.com/zeeneddie/agent-os
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class VerificationLevel(str, Enum):
    """Verification strictness levels."""
    LENIENT = "lenient"      # Warnings only
    STANDARD = "standard"    # Some requirements
    STRICT = "strict"        # All requirements enforced


class VerificationCategory(str, Enum):
    """Categories of verification checks."""
    VISUAL_ASSETS = "visual_assets"
    REUSABILITY = "reusability"
    SCOPE = "scope"
    STRUCTURE = "structure"


@dataclass
class VerificationCheck:
    """Result of a single verification check."""
    name: str
    category: VerificationCategory
    passed: bool
    severity: str  # error, warning, info
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None


@dataclass
class VerificationResult:
    """Complete verification result."""
    passed: bool
    score: float  # 0.0 - 1.0
    checks: List[VerificationCheck] = field(default_factory=list)
    errors: int = 0
    warnings: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def add_check(self, check: VerificationCheck):
        """Add a check result."""
        self.checks.append(check)
        if not check.passed:
            if check.severity == "error":
                self.errors += 1
            elif check.severity == "warning":
                self.warnings += 1

    def calculate_score(self):
        """Calculate overall score based on checks."""
        if not self.checks:
            self.score = 1.0
            return

        passed = sum(1 for c in self.checks if c.passed)
        self.score = passed / len(self.checks)
        self.passed = self.errors == 0


# Visual asset patterns to detect
VISUAL_PATTERNS = {
    "images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"],
    "diagrams": [".mmd", ".mermaid", ".puml", ".plantuml"],
    "screenshots": ["screenshot", "screen_", "capture"],
    "mockups": ["mockup", "wireframe", "design"],
}

# Reusability indicators
REUSABILITY_INDICATORS = {
    "positive": [
        "interface", "abstract", "generic", "template", "factory",
        "adapter", "strategy", "observer", "dependency injection",
        "modular", "plugin", "extension", "hook", "callback"
    ],
    "negative": [
        "hardcoded", "hardcode", "hard-coded", "magic number",
        "copy paste", "copypaste", "duplicate", "workaround",
        "hack", "todo: remove", "temporary fix", "quick fix"
    ]
}

# Scope limitation keywords
SCOPE_KEYWORDS = {
    "in_scope": ["in scope", "in-scope", "included", "will implement", "deliverable"],
    "out_scope": ["out of scope", "out-of-scope", "excluded", "not included", "future", "later"],
    "scope_creep": ["also", "additionally", "might", "could also", "nice to have", "if time"]
}


class SpecVerificationService:
    """
    Service for verifying specifications against Agent OS quality standards.

    Implements 4 key verification concepts:
    1. Visual asset validation - Ensures specs have supporting visuals
    2. Reusability check - Validates code patterns for maintainability
    3. Visuals folder requirement - Enforces visual documentation structure
    4. Scope limitation - Prevents scope creep in implementations
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize the verification service.

        Args:
            project_root: Root directory for the project being verified
        """
        self.project_root = Path(project_root) if project_root else None
        self.level = VerificationLevel.STANDARD

    def verify_spec(
        self,
        spec_content: str,
        project_path: Optional[str] = None,
        level: VerificationLevel = VerificationLevel.STANDARD
    ) -> VerificationResult:
        """
        Run all verification checks on a specification.

        Args:
            spec_content: The specification text to verify
            project_path: Optional path to project for file checks
            level: Verification strictness level

        Returns:
            Complete verification result
        """
        self.level = level
        result = VerificationResult(passed=True, score=0.0)

        # 1. Visual asset validation
        visual_checks = self._verify_visual_assets(spec_content, project_path)
        for check in visual_checks:
            result.add_check(check)

        # 2. Reusability check
        reuse_checks = self._verify_reusability(spec_content)
        for check in reuse_checks:
            result.add_check(check)

        # 3. Scope limitation check
        scope_checks = self._verify_scope(spec_content)
        for check in scope_checks:
            result.add_check(check)

        # 4. Structure check (visuals folder requirement)
        if project_path:
            structure_checks = self._verify_structure(project_path)
            for check in structure_checks:
                result.add_check(check)

        result.calculate_score()
        return result

    def _verify_visual_assets(
        self,
        spec_content: str,
        project_path: Optional[str]
    ) -> List[VerificationCheck]:
        """
        Verify that specification has adequate visual documentation.

        Agent OS Concept: Specs should include visual assets like diagrams,
        screenshots, or mockups to improve understanding.
        """
        checks = []
        spec_lower = spec_content.lower()

        # Check for image references in spec
        image_refs = []
        for pattern in [r'!\[.*?\]\(.*?\)', r'<img.*?>', r'\.png|\.jpg|\.svg']:
            matches = re.findall(pattern, spec_content, re.IGNORECASE)
            image_refs.extend(matches)

        has_image_refs = len(image_refs) > 0
        checks.append(VerificationCheck(
            name="has_visual_references",
            category=VerificationCategory.VISUAL_ASSETS,
            passed=has_image_refs,
            severity="warning" if self.level == VerificationLevel.LENIENT else "error",
            message=f"Found {len(image_refs)} image references" if has_image_refs else "No image references found",
            details={"references": image_refs[:5]},  # First 5
            suggestion="Add diagrams or screenshots to illustrate the specification" if not has_image_refs else None
        ))

        # Check for diagram mentions
        diagram_keywords = ["diagram", "flowchart", "architecture", "erd", "uml", "sequence"]
        has_diagram_mention = any(kw in spec_lower for kw in diagram_keywords)
        checks.append(VerificationCheck(
            name="has_diagram_mention",
            category=VerificationCategory.VISUAL_ASSETS,
            passed=has_diagram_mention,
            severity="warning",
            message="Spec mentions diagrams" if has_diagram_mention else "No diagram references found",
            suggestion="Consider adding architecture or flow diagrams" if not has_diagram_mention else None
        ))

        # Check for mermaid blocks
        mermaid_pattern = r'```mermaid|```plantuml|```puml'
        has_mermaid = bool(re.search(mermaid_pattern, spec_content, re.IGNORECASE))
        checks.append(VerificationCheck(
            name="has_embedded_diagrams",
            category=VerificationCategory.VISUAL_ASSETS,
            passed=has_mermaid,
            severity="info",
            message="Has embedded diagram code" if has_mermaid else "No embedded diagrams (mermaid/plantuml)",
            suggestion="Add mermaid diagrams for better visualization" if not has_mermaid else None
        ))

        # If project path provided, check for actual visual files
        if project_path:
            visual_files = self._find_visual_files(project_path)
            has_visual_files = len(visual_files) > 0
            checks.append(VerificationCheck(
                name="has_visual_files",
                category=VerificationCategory.VISUAL_ASSETS,
                passed=has_visual_files,
                severity="warning",
                message=f"Found {len(visual_files)} visual files" if has_visual_files else "No visual files in project",
                details={"files": visual_files[:10]} if visual_files else None,
                suggestion="Add screenshots or diagrams to doc/ folder" if not has_visual_files else None
            ))

        return checks

    def _verify_reusability(self, spec_content: str) -> List[VerificationCheck]:
        """
        Verify that specification promotes reusable patterns.

        Agent OS Concept: Code should be designed for reusability,
        avoiding hardcoded values and promoting modular design.
        """
        checks = []
        spec_lower = spec_content.lower()

        # Check for positive reusability indicators
        positive_found = [
            ind for ind in REUSABILITY_INDICATORS["positive"]
            if ind in spec_lower
        ]
        has_positive = len(positive_found) >= 2
        checks.append(VerificationCheck(
            name="reusability_patterns",
            category=VerificationCategory.REUSABILITY,
            passed=has_positive,
            severity="warning",
            message=f"Found reusability patterns: {', '.join(positive_found[:5])}" if positive_found else "No reusability patterns mentioned",
            details={"patterns_found": positive_found},
            suggestion="Consider using interfaces, factories, or dependency injection" if not has_positive else None
        ))

        # Check for negative indicators (anti-patterns)
        negative_found = [
            ind for ind in REUSABILITY_INDICATORS["negative"]
            if ind in spec_lower
        ]
        has_negative = len(negative_found) > 0
        checks.append(VerificationCheck(
            name="no_antipatterns",
            category=VerificationCategory.REUSABILITY,
            passed=not has_negative,
            severity="error" if has_negative else "info",
            message=f"Found anti-patterns: {', '.join(negative_found)}" if has_negative else "No anti-patterns detected",
            details={"antipatterns_found": negative_found} if has_negative else None,
            suggestion="Refactor to remove hardcoded values and workarounds" if has_negative else None
        ))

        # Check for configuration mentions
        config_keywords = ["config", "configuration", "environment", "settings", "parameters"]
        has_config = any(kw in spec_lower for kw in config_keywords)
        checks.append(VerificationCheck(
            name="configurable_design",
            category=VerificationCategory.REUSABILITY,
            passed=has_config,
            severity="warning",
            message="Spec mentions configuration" if has_config else "No configuration strategy mentioned",
            suggestion="Define configuration approach for environment-specific values" if not has_config else None
        ))

        # Check for testing mentions (testable = reusable)
        test_keywords = ["test", "testable", "unit test", "mock", "stub", "fixture"]
        has_testing = any(kw in spec_lower for kw in test_keywords)
        checks.append(VerificationCheck(
            name="testable_design",
            category=VerificationCategory.REUSABILITY,
            passed=has_testing,
            severity="warning",
            message="Spec mentions testing" if has_testing else "No testing strategy mentioned",
            suggestion="Define testing approach - unit tests, mocks, fixtures" if not has_testing else None
        ))

        return checks

    def _verify_scope(self, spec_content: str) -> List[VerificationCheck]:
        """
        Verify that specification has clear scope boundaries.

        Agent OS Concept: Implementations should have strict scope
        limitations to prevent scope creep and maintain focus.
        """
        checks = []
        spec_lower = spec_content.lower()

        # Check for explicit scope section
        has_scope_section = any(
            pattern in spec_lower
            for pattern in ["## scope", "### scope", "# scope", "**scope**"]
        )
        checks.append(VerificationCheck(
            name="has_scope_section",
            category=VerificationCategory.SCOPE,
            passed=has_scope_section,
            severity="error" if self.level == VerificationLevel.STRICT else "warning",
            message="Has explicit scope section" if has_scope_section else "No dedicated scope section",
            suggestion="Add a ## Scope section with In Scope and Out of Scope subsections" if not has_scope_section else None
        ))

        # Check for in-scope markers
        in_scope_found = any(kw in spec_lower for kw in SCOPE_KEYWORDS["in_scope"])
        checks.append(VerificationCheck(
            name="has_in_scope",
            category=VerificationCategory.SCOPE,
            passed=in_scope_found,
            severity="warning",
            message="In-scope items defined" if in_scope_found else "No explicit in-scope items",
            suggestion="List what IS included in this work" if not in_scope_found else None
        ))

        # Check for out-of-scope markers
        out_scope_found = any(kw in spec_lower for kw in SCOPE_KEYWORDS["out_scope"])
        checks.append(VerificationCheck(
            name="has_out_scope",
            category=VerificationCategory.SCOPE,
            passed=out_scope_found,
            severity="warning",
            message="Out-of-scope items defined" if out_scope_found else "No explicit out-of-scope items",
            suggestion="List what is NOT included to prevent scope creep" if not out_scope_found else None
        ))

        # Check for scope creep indicators
        creep_found = [
            kw for kw in SCOPE_KEYWORDS["scope_creep"]
            if kw in spec_lower
        ]
        has_creep_risk = len(creep_found) >= 3
        checks.append(VerificationCheck(
            name="scope_creep_risk",
            category=VerificationCategory.SCOPE,
            passed=not has_creep_risk,
            severity="warning" if has_creep_risk else "info",
            message=f"Scope creep indicators: {', '.join(creep_found)}" if creep_found else "Low scope creep risk",
            details={"indicators": creep_found} if creep_found else None,
            suggestion="Review 'nice to have' items - move to separate spec or explicitly exclude" if has_creep_risk else None
        ))

        # Check for acceptance criteria (clear boundaries)
        has_acceptance = any(
            pattern in spec_lower
            for pattern in ["acceptance criteria", "done when", "success criteria", "definition of done"]
        )
        checks.append(VerificationCheck(
            name="has_acceptance_criteria",
            category=VerificationCategory.SCOPE,
            passed=has_acceptance,
            severity="error" if self.level == VerificationLevel.STRICT else "warning",
            message="Has acceptance criteria" if has_acceptance else "No acceptance criteria defined",
            suggestion="Add clear acceptance criteria to define completion" if not has_acceptance else None
        ))

        return checks

    def _verify_structure(self, project_path: str) -> List[VerificationCheck]:
        """
        Verify project structure meets requirements.

        Agent OS Concept: Projects should have a mandatory visuals folder
        for storing diagrams, screenshots, and other visual documentation.
        """
        checks = []
        path = Path(project_path)

        if not path.exists():
            checks.append(VerificationCheck(
                name="project_exists",
                category=VerificationCategory.STRUCTURE,
                passed=False,
                severity="error",
                message=f"Project path does not exist: {project_path}"
            ))
            return checks

        # Check for doc folder
        doc_paths = ["doc", "docs", "documentation"]
        doc_folder = None
        for doc_name in doc_paths:
            if (path / doc_name).exists():
                doc_folder = path / doc_name
                break

        has_doc_folder = doc_folder is not None
        checks.append(VerificationCheck(
            name="has_doc_folder",
            category=VerificationCategory.STRUCTURE,
            passed=has_doc_folder,
            severity="warning",
            message=f"Documentation folder: {doc_folder}" if has_doc_folder else "No doc/ folder found",
            suggestion="Create a doc/ folder for documentation" if not has_doc_folder else None
        ))

        # Check for visuals folder (Agent OS requirement)
        visual_paths = ["visuals", "images", "assets", "diagrams", "screenshots"]
        visual_folder = None

        # Check in root
        for vis_name in visual_paths:
            if (path / vis_name).exists():
                visual_folder = path / vis_name
                break

        # Check in doc folder
        if not visual_folder and doc_folder:
            for vis_name in visual_paths:
                if (doc_folder / vis_name).exists():
                    visual_folder = doc_folder / vis_name
                    break

        has_visual_folder = visual_folder is not None
        checks.append(VerificationCheck(
            name="has_visuals_folder",
            category=VerificationCategory.STRUCTURE,
            passed=has_visual_folder,
            severity="error" if self.level == VerificationLevel.STRICT else "warning",
            message=f"Visuals folder: {visual_folder}" if has_visual_folder else "No visuals folder found",
            suggestion="Create doc/visuals/ folder for diagrams and screenshots" if not has_visual_folder else None
        ))

        # Check for README
        readme_exists = any(
            (path / name).exists()
            for name in ["README.md", "readme.md", "README.rst", "README"]
        )
        checks.append(VerificationCheck(
            name="has_readme",
            category=VerificationCategory.STRUCTURE,
            passed=readme_exists,
            severity="warning",
            message="README exists" if readme_exists else "No README found",
            suggestion="Add a README.md with project overview" if not readme_exists else None
        ))

        return checks

    def _find_visual_files(self, project_path: str) -> List[str]:
        """Find visual files in the project."""
        visual_files = []
        path = Path(project_path)

        if not path.exists():
            return visual_files

        # Search for visual files
        extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mmd"]
        for ext in extensions:
            visual_files.extend([
                str(f.relative_to(path))
                for f in path.rglob(f"*{ext}")
                if "node_modules" not in str(f) and ".git" not in str(f)
            ])

        return visual_files[:50]  # Limit to 50

    def create_visuals_folder(self, project_path: str) -> Dict[str, Any]:
        """
        Create the mandatory visuals folder structure.

        Args:
            project_path: Project root path

        Returns:
            Result with created paths
        """
        path = Path(project_path)
        created = []

        # Create doc folder if needed
        doc_path = path / "doc"
        if not doc_path.exists():
            doc_path.mkdir(parents=True)
            created.append(str(doc_path))

        # Create visuals folder
        visuals_path = doc_path / "visuals"
        if not visuals_path.exists():
            visuals_path.mkdir()
            created.append(str(visuals_path))

        # Create subdirectories
        subdirs = ["diagrams", "screenshots", "mockups"]
        for subdir in subdirs:
            subdir_path = visuals_path / subdir
            if not subdir_path.exists():
                subdir_path.mkdir()
                created.append(str(subdir_path))

        # Create placeholder README
        readme_path = visuals_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text("""# Visual Documentation

This folder contains visual assets for the project.

## Structure

- `diagrams/` - Architecture diagrams, flowcharts, ERDs
- `screenshots/` - UI screenshots, test results
- `mockups/` - Design mockups, wireframes

## Guidelines

1. Use descriptive filenames: `feature-name-diagram.png`
2. Include diagrams in specs with relative paths
3. Keep originals (e.g., .mmd files) alongside exports
4. Update visuals when architecture changes
""")
            created.append(str(readme_path))

        return {
            "success": True,
            "created": created,
            "visuals_path": str(visuals_path)
        }

    def get_verification_summary(self, result: VerificationResult) -> Dict[str, Any]:
        """Get a summary of verification results."""
        by_category = {}
        for check in result.checks:
            cat = check.category.value
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0, "checks": []}

            if check.passed:
                by_category[cat]["passed"] += 1
            else:
                by_category[cat]["failed"] += 1

            by_category[cat]["checks"].append({
                "name": check.name,
                "passed": check.passed,
                "severity": check.severity,
                "message": check.message
            })

        # Add total and score to each category
        for cat, data in by_category.items():
            data["total"] = data["passed"] + data["failed"]
            data["score"] = round(data["passed"] / data["total"] * 100, 1) if data["total"] > 0 else 100

        return {
            "overall_passed": result.passed,
            "score": round(result.score * 100, 1),
            "errors": result.errors,
            "warnings": result.warnings,
            "total_checks": len(result.checks),
            "by_category": by_category,
            "timestamp": result.timestamp.isoformat()
        }
