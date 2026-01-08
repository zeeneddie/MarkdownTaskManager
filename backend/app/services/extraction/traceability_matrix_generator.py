"""
Traceability Matrix Generator - Week 105
FR-M-1: Traceability Matrix Generator

Creates bi-directional traceability matrices between:
- Requirements ↔ Code
- Requirements ↔ Tests
- Code ↔ Tests
- Business Rules ↔ Implementation

Supports CAFCR methodology and INVEST validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
from datetime import datetime
import re
import json
from collections import defaultdict


class ArtifactType(Enum):
    """Types of artifacts in traceability matrix."""
    REQUIREMENT = "requirement"
    USER_STORY = "user_story"
    EPIC = "epic"
    FEATURE = "feature"
    BUSINESS_RULE = "business_rule"
    CODE_FILE = "code_file"
    CODE_FUNCTION = "code_function"
    CODE_CLASS = "code_class"
    TEST_FILE = "test_file"
    TEST_CASE = "test_case"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    NFR = "nfr"  # Non-functional requirement


class LinkType(Enum):
    """Types of links between artifacts."""
    IMPLEMENTS = "implements"       # Code implements requirement
    TESTS = "tests"                 # Test verifies requirement
    DERIVES_FROM = "derives_from"   # Story derives from epic
    SATISFIES = "satisfies"         # Code satisfies business rule
    COVERS = "covers"               # Test covers code
    RELATES_TO = "relates_to"       # General relationship
    REFINES = "refines"             # More specific version


class CoverageStatus(Enum):
    """Coverage status for requirements."""
    FULL = "full"           # Fully covered by code and tests
    PARTIAL = "partial"     # Partially covered
    NONE = "none"           # No coverage
    ORPHAN = "orphan"       # Code/test without requirement


@dataclass
class TraceableArtifact:
    """An artifact that can be traced."""
    id: str
    type: ArtifactType
    name: str
    description: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "metadata": self.metadata,
            "tags": self.tags
        }


@dataclass
class TraceLink:
    """A link between two artifacts."""
    source_id: str
    target_id: str
    link_type: LinkType
    confidence: float = 1.0
    evidence: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "link_type": self.link_type.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "validated": self.validated
        }


@dataclass
class CoverageReport:
    """Coverage analysis report."""
    total_requirements: int
    covered_requirements: int
    partial_requirements: int
    uncovered_requirements: int
    orphan_code: int
    orphan_tests: int
    coverage_percentage: float
    gaps: List[Dict[str, Any]] = field(default_factory=list)


class TraceabilityMatrix:
    """
    Bi-directional traceability matrix.

    Maintains relationships between requirements, code, and tests,
    enabling impact analysis and coverage tracking.
    """

    def __init__(self):
        self.artifacts: Dict[str, TraceableArtifact] = {}
        self.links: List[TraceLink] = []
        self._forward_index: Dict[str, List[str]] = defaultdict(list)
        self._backward_index: Dict[str, List[str]] = defaultdict(list)
        self._type_index: Dict[ArtifactType, Set[str]] = defaultdict(set)

    def add_artifact(self, artifact: TraceableArtifact) -> None:
        """Add an artifact to the matrix."""
        self.artifacts[artifact.id] = artifact
        self._type_index[artifact.type].add(artifact.id)

    def add_link(self, link: TraceLink) -> bool:
        """
        Add a link between artifacts.

        Returns True if link was added, False if artifacts don't exist.
        """
        if link.source_id not in self.artifacts or link.target_id not in self.artifacts:
            return False

        self.links.append(link)
        self._forward_index[link.source_id].append(link.target_id)
        self._backward_index[link.target_id].append(link.source_id)
        return True

    def get_forward_links(self, artifact_id: str) -> List[TraceableArtifact]:
        """Get all artifacts linked FROM this artifact."""
        target_ids = self._forward_index.get(artifact_id, [])
        return [self.artifacts[tid] for tid in target_ids if tid in self.artifacts]

    def get_backward_links(self, artifact_id: str) -> List[TraceableArtifact]:
        """Get all artifacts linked TO this artifact."""
        source_ids = self._backward_index.get(artifact_id, [])
        return [self.artifacts[sid] for sid in source_ids if sid in self.artifacts]

    def get_by_type(self, artifact_type: ArtifactType) -> List[TraceableArtifact]:
        """Get all artifacts of a specific type."""
        ids = self._type_index.get(artifact_type, set())
        return [self.artifacts[aid] for aid in ids if aid in self.artifacts]

    def get_link(self, source_id: str, target_id: str) -> Optional[TraceLink]:
        """Get the link between two artifacts."""
        for link in self.links:
            if link.source_id == source_id and link.target_id == target_id:
                return link
        return None

    def get_coverage_status(self, requirement_id: str) -> CoverageStatus:
        """Determine coverage status for a requirement."""
        if requirement_id not in self.artifacts:
            return CoverageStatus.NONE

        # Get implementing code
        code_links = [
            l for l in self.links
            if l.source_id == requirement_id and l.link_type == LinkType.IMPLEMENTS
        ]

        # Get tests
        test_links = [
            l for l in self.links
            if l.source_id == requirement_id and l.link_type == LinkType.TESTS
        ]

        if code_links and test_links:
            return CoverageStatus.FULL
        elif code_links or test_links:
            return CoverageStatus.PARTIAL
        else:
            return CoverageStatus.NONE

    def get_impact_analysis(self, artifact_id: str) -> Dict[str, List[str]]:
        """
        Perform impact analysis for an artifact change.

        Returns all artifacts that would be affected by changes.
        """
        affected: Dict[str, List[str]] = {
            "direct": [],
            "indirect": [],
            "tests_to_update": [],
            "docs_to_update": []
        }

        # Direct impacts (forward links)
        for target in self.get_forward_links(artifact_id):
            affected["direct"].append(target.id)

            # Find tests that would need updating
            if target.type in [ArtifactType.CODE_FILE, ArtifactType.CODE_FUNCTION]:
                test_links = [
                    l for l in self.links
                    if l.target_id == target.id and l.link_type == LinkType.COVERS
                ]
                affected["tests_to_update"].extend([l.source_id for l in test_links])

        # Backward impacts (things that depend on this)
        for source in self.get_backward_links(artifact_id):
            affected["indirect"].append(source.id)

        return affected


class TraceabilityMatrixGenerator:
    """
    Generates traceability matrices from various sources.

    Supports:
    - Code annotation parsing (@requirement, @story)
    - Test annotation parsing (@covers, @tests)
    - Naming convention analysis
    - Semantic similarity matching
    """

    # Patterns for extracting traceability annotations
    ANNOTATION_PATTERNS = {
        "requirement": r"@requirement\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        "story": r"@story\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        "covers": r"@covers\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        "tests": r"@tests\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        "jira": r"(?:JIRA|TASK|STORY|BUG)-\d+",
        "issue": r"#(\d+)",
    }

    def __init__(self):
        self.matrix = TraceabilityMatrix()
        self._artifact_counter = 0

    def generate_id(self, prefix: str = "ART") -> str:
        """Generate unique artifact ID."""
        self._artifact_counter += 1
        return f"{prefix}-{self._artifact_counter:04d}"

    def add_requirement(
        self,
        name: str,
        description: str,
        req_type: ArtifactType = ArtifactType.REQUIREMENT,
        **metadata
    ) -> str:
        """Add a requirement to the matrix."""
        artifact_id = self.generate_id("REQ")

        artifact = TraceableArtifact(
            id=artifact_id,
            type=req_type,
            name=name,
            description=description,
            metadata=metadata
        )

        self.matrix.add_artifact(artifact)
        return artifact_id

    def add_user_story(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        epic_id: Optional[str] = None,
        **metadata
    ) -> str:
        """Add a user story with acceptance criteria."""
        story_id = self.generate_id("US")

        story = TraceableArtifact(
            id=story_id,
            type=ArtifactType.USER_STORY,
            name=title,
            description=description,
            metadata={
                "acceptance_criteria": acceptance_criteria,
                **metadata
            }
        )

        self.matrix.add_artifact(story)

        # Link to epic if provided
        if epic_id and epic_id in self.matrix.artifacts:
            self.matrix.add_link(TraceLink(
                source_id=story_id,
                target_id=epic_id,
                link_type=LinkType.DERIVES_FROM
            ))

        # Add acceptance criteria as separate artifacts
        for i, ac in enumerate(acceptance_criteria):
            ac_id = self.generate_id("AC")
            ac_artifact = TraceableArtifact(
                id=ac_id,
                type=ArtifactType.ACCEPTANCE_CRITERIA,
                name=f"AC-{i+1} for {story_id}",
                description=ac
            )
            self.matrix.add_artifact(ac_artifact)
            self.matrix.add_link(TraceLink(
                source_id=ac_id,
                target_id=story_id,
                link_type=LinkType.REFINES
            ))

        return story_id

    def add_code_artifact(
        self,
        name: str,
        artifact_type: ArtifactType,
        file_path: str,
        line_number: int,
        code_snippet: str,
        **metadata
    ) -> str:
        """Add a code artifact (class, function, file)."""
        prefix = {
            ArtifactType.CODE_FILE: "FILE",
            ArtifactType.CODE_CLASS: "CLS",
            ArtifactType.CODE_FUNCTION: "FN"
        }.get(artifact_type, "CODE")

        artifact_id = self.generate_id(prefix)

        artifact = TraceableArtifact(
            id=artifact_id,
            type=artifact_type,
            name=name,
            description=f"{artifact_type.value}: {name}",
            source_file=file_path,
            source_line=line_number,
            metadata={
                "code_snippet": code_snippet,
                **metadata
            }
        )

        self.matrix.add_artifact(artifact)
        return artifact_id

    def add_test_artifact(
        self,
        name: str,
        test_type: str,  # unit, integration, e2e
        file_path: str,
        line_number: int,
        **metadata
    ) -> str:
        """Add a test artifact."""
        artifact_id = self.generate_id("TEST")

        artifact = TraceableArtifact(
            id=artifact_id,
            type=ArtifactType.TEST_CASE,
            name=name,
            description=f"Test: {name}",
            source_file=file_path,
            source_line=line_number,
            metadata={
                "test_type": test_type,
                **metadata
            }
        )

        self.matrix.add_artifact(artifact)
        return artifact_id

    def parse_code_for_links(
        self,
        code: str,
        file_path: str,
        code_artifact_id: str
    ) -> List[TraceLink]:
        """
        Parse code for traceability annotations.

        Looks for patterns like @requirement("REQ-001") or @covers("US-001").
        """
        links = []

        for pattern_name, pattern in self.ANNOTATION_PATTERNS.items():
            matches = re.findall(pattern, code)

            for match in matches:
                target_id = match if isinstance(match, str) else match[0]

                # Determine link type
                if pattern_name in ["requirement", "story"]:
                    link_type = LinkType.IMPLEMENTS
                elif pattern_name in ["covers", "tests"]:
                    link_type = LinkType.TESTS
                else:
                    link_type = LinkType.RELATES_TO

                link = TraceLink(
                    source_id=code_artifact_id,
                    target_id=target_id,
                    link_type=link_type,
                    evidence=f"Annotation found in {file_path}"
                )

                # Only add if target exists
                if target_id in self.matrix.artifacts:
                    self.matrix.add_link(link)
                    links.append(link)

        return links

    def infer_links_from_naming(
        self,
        code_artifact: TraceableArtifact,
        requirements: List[TraceableArtifact]
    ) -> List[TraceLink]:
        """
        Infer traceability links from naming conventions.

        E.g., test_user_login() likely tests UserLogin requirement.
        """
        links = []
        code_name_lower = code_artifact.name.lower()

        for req in requirements:
            req_name_lower = req.name.lower().replace(" ", "_").replace("-", "_")

            # Check if requirement name appears in code name
            if req_name_lower in code_name_lower or code_name_lower in req_name_lower:
                # Determine link type based on artifact types
                if code_artifact.type == ArtifactType.TEST_CASE:
                    link_type = LinkType.TESTS
                else:
                    link_type = LinkType.IMPLEMENTS

                link = TraceLink(
                    source_id=code_artifact.id,
                    target_id=req.id,
                    link_type=link_type,
                    confidence=0.7,
                    evidence="Inferred from naming convention"
                )

                self.matrix.add_link(link)
                links.append(link)

        return links

    def generate_coverage_report(self) -> CoverageReport:
        """Generate a coverage analysis report."""
        requirements = self.matrix.get_by_type(ArtifactType.REQUIREMENT)
        user_stories = self.matrix.get_by_type(ArtifactType.USER_STORY)
        all_reqs = requirements + user_stories

        covered = 0
        partial = 0
        uncovered = 0
        gaps = []

        for req in all_reqs:
            status = self.matrix.get_coverage_status(req.id)

            if status == CoverageStatus.FULL:
                covered += 1
            elif status == CoverageStatus.PARTIAL:
                partial += 1
                gaps.append({
                    "artifact_id": req.id,
                    "name": req.name,
                    "status": "partial",
                    "missing": self._identify_missing_coverage(req.id)
                })
            else:
                uncovered += 1
                gaps.append({
                    "artifact_id": req.id,
                    "name": req.name,
                    "status": "uncovered",
                    "missing": ["code", "tests"]
                })

        # Find orphan code/tests
        code_artifacts = (
            self.matrix.get_by_type(ArtifactType.CODE_FILE) +
            self.matrix.get_by_type(ArtifactType.CODE_FUNCTION) +
            self.matrix.get_by_type(ArtifactType.CODE_CLASS)
        )
        test_artifacts = self.matrix.get_by_type(ArtifactType.TEST_CASE)

        orphan_code = sum(1 for c in code_artifacts if not self.matrix.get_backward_links(c.id))
        orphan_tests = sum(1 for t in test_artifacts if not self.matrix.get_forward_links(t.id))

        total = len(all_reqs)
        coverage_pct = (covered / total * 100) if total > 0 else 0

        return CoverageReport(
            total_requirements=total,
            covered_requirements=covered,
            partial_requirements=partial,
            uncovered_requirements=uncovered,
            orphan_code=orphan_code,
            orphan_tests=orphan_tests,
            coverage_percentage=round(coverage_pct, 2),
            gaps=gaps
        )

    def _identify_missing_coverage(self, requirement_id: str) -> List[str]:
        """Identify what's missing for a partially covered requirement."""
        missing = []

        code_links = [
            l for l in self.matrix.links
            if l.target_id == requirement_id and l.link_type == LinkType.IMPLEMENTS
        ]

        test_links = [
            l for l in self.matrix.links
            if l.target_id == requirement_id and l.link_type == LinkType.TESTS
        ]

        if not code_links:
            missing.append("code")
        if not test_links:
            missing.append("tests")

        return missing

    def export_matrix(self, format: str = "json") -> str:
        """Export the traceability matrix."""
        if format == "json":
            return self._to_json()
        elif format == "markdown":
            return self._to_markdown()
        elif format == "csv":
            return self._to_csv()
        elif format == "html":
            return self._to_html()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_json(self) -> str:
        """Export as JSON."""
        return json.dumps({
            "artifacts": {aid: a.to_dict() for aid, a in self.matrix.artifacts.items()},
            "links": [l.to_dict() for l in self.matrix.links],
            "coverage": self.generate_coverage_report().__dict__,
            "generated_at": datetime.utcnow().isoformat()
        }, indent=2, default=str)

    def _to_markdown(self) -> str:
        """Export as Markdown table."""
        lines = ["# Traceability Matrix\n"]

        # Requirements to Code matrix
        lines.append("## Requirements → Code\n")
        lines.append("| Requirement | Code | Status |")
        lines.append("|------------|------|--------|")

        requirements = (
            self.matrix.get_by_type(ArtifactType.REQUIREMENT) +
            self.matrix.get_by_type(ArtifactType.USER_STORY)
        )

        for req in requirements:
            code_links = [
                l for l in self.matrix.links
                if l.target_id == req.id and l.link_type == LinkType.IMPLEMENTS
            ]

            if code_links:
                for link in code_links:
                    code = self.matrix.artifacts.get(link.source_id)
                    if code:
                        lines.append(f"| {req.name} | {code.name} | ✓ |")
            else:
                lines.append(f"| {req.name} | - | ✗ |")

        # Requirements to Test matrix
        lines.append("\n## Requirements → Tests\n")
        lines.append("| Requirement | Test | Status |")
        lines.append("|------------|------|--------|")

        for req in requirements:
            test_links = [
                l for l in self.matrix.links
                if l.target_id == req.id and l.link_type == LinkType.TESTS
            ]

            if test_links:
                for link in test_links:
                    test = self.matrix.artifacts.get(link.source_id)
                    if test:
                        lines.append(f"| {req.name} | {test.name} | ✓ |")
            else:
                lines.append(f"| {req.name} | - | ✗ |")

        # Coverage summary
        report = self.generate_coverage_report()
        lines.append("\n## Coverage Summary\n")
        lines.append(f"- **Total Requirements**: {report.total_requirements}")
        lines.append(f"- **Fully Covered**: {report.covered_requirements}")
        lines.append(f"- **Partially Covered**: {report.partial_requirements}")
        lines.append(f"- **Uncovered**: {report.uncovered_requirements}")
        lines.append(f"- **Coverage**: {report.coverage_percentage}%")

        return '\n'.join(lines)

    def _to_csv(self) -> str:
        """Export as CSV."""
        lines = ["source_id,source_name,source_type,target_id,target_name,target_type,link_type,confidence"]

        for link in self.matrix.links:
            source = self.matrix.artifacts.get(link.source_id)
            target = self.matrix.artifacts.get(link.target_id)

            if source and target:
                lines.append(
                    f"{source.id},{source.name},{source.type.value},"
                    f"{target.id},{target.name},{target.type.value},"
                    f"{link.link_type.value},{link.confidence}"
                )

        return '\n'.join(lines)

    def _to_html(self) -> str:
        """Export as HTML table."""
        html = ["<!DOCTYPE html><html><head>"]
        html.append("<style>")
        html.append("table { border-collapse: collapse; width: 100%; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #4CAF50; color: white; }")
        html.append("tr:nth-child(even) { background-color: #f2f2f2; }")
        html.append(".covered { color: green; } .uncovered { color: red; }")
        html.append("</style></head><body>")

        html.append("<h1>Traceability Matrix</h1>")

        # Matrix table
        html.append("<table><tr><th>Source</th><th>Type</th><th>Link</th><th>Target</th><th>Type</th></tr>")

        for link in self.matrix.links:
            source = self.matrix.artifacts.get(link.source_id)
            target = self.matrix.artifacts.get(link.target_id)

            if source and target:
                html.append(f"<tr>")
                html.append(f"<td>{source.name}</td>")
                html.append(f"<td>{source.type.value}</td>")
                html.append(f"<td>{link.link_type.value}</td>")
                html.append(f"<td>{target.name}</td>")
                html.append(f"<td>{target.type.value}</td>")
                html.append(f"</tr>")

        html.append("</table>")

        # Coverage chart
        report = self.generate_coverage_report()
        html.append(f"<h2>Coverage: {report.coverage_percentage}%</h2>")
        html.append(f"<div style='width:100%;background:#ddd;'>")
        html.append(f"<div style='width:{report.coverage_percentage}%;background:#4CAF50;height:20px;'></div>")
        html.append("</div>")

        html.append("</body></html>")

        return '\n'.join(html)
