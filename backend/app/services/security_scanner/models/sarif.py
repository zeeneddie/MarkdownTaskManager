"""
SARIF 2.1.0 Models for Security Scanner Integration.

SARIF (Static Analysis Results Interchange Format) is an OASIS standard
for representing the output of static analysis tools.

Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class SarifLevel(str, Enum):
    """SARIF result level (severity)."""
    NONE = "none"
    NOTE = "note"
    WARNING = "warning"
    ERROR = "error"


class SarifKind(str, Enum):
    """SARIF result kind."""
    NOT_APPLICABLE = "notApplicable"
    PASS = "pass"
    FAIL = "fail"
    REVIEW = "review"
    OPEN = "open"
    INFORMATIONAL = "informational"


@dataclass
class SarifMessage:
    """SARIF message object."""
    text: str
    markdown: Optional[str] = None
    id: Optional[str] = None
    arguments: Optional[List[str]] = None


@dataclass
class SarifArtifactLocation:
    """SARIF artifact location."""
    uri: str
    uri_base_id: Optional[str] = None
    index: Optional[int] = None


@dataclass
class SarifRegion:
    """SARIF region within a file."""
    start_line: int
    start_column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    char_offset: Optional[int] = None
    char_length: Optional[int] = None
    byte_offset: Optional[int] = None
    byte_length: Optional[int] = None
    snippet: Optional[SarifMessage] = None


@dataclass
class SarifPhysicalLocation:
    """SARIF physical location."""
    artifact_location: SarifArtifactLocation
    region: Optional[SarifRegion] = None
    context_region: Optional[SarifRegion] = None


@dataclass
class SarifLogicalLocation:
    """SARIF logical location (e.g., function name)."""
    name: Optional[str] = None
    fully_qualified_name: Optional[str] = None
    decorated_name: Optional[str] = None
    kind: Optional[str] = None  # function, method, class, module, etc.
    parent_index: Optional[int] = None


@dataclass
class SarifLocation:
    """SARIF location combining physical and logical."""
    physical_location: Optional[SarifPhysicalLocation] = None
    logical_locations: Optional[List[SarifLogicalLocation]] = None
    message: Optional[SarifMessage] = None


@dataclass
class SarifFix:
    """SARIF fix suggestion."""
    description: SarifMessage
    artifact_changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SarifReportingDescriptor:
    """SARIF rule definition."""
    id: str
    name: Optional[str] = None
    short_description: Optional[SarifMessage] = None
    full_description: Optional[SarifMessage] = None
    help: Optional[SarifMessage] = None
    help_uri: Optional[str] = None
    default_configuration: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None  # CWE, tags, etc.


@dataclass
class SarifToolComponent:
    """SARIF tool component (driver or extension)."""
    name: str
    version: Optional[str] = None
    semantic_version: Optional[str] = None
    information_uri: Optional[str] = None
    rules: List[SarifReportingDescriptor] = field(default_factory=list)
    notifications: List[SarifReportingDescriptor] = field(default_factory=list)
    properties: Optional[Dict[str, Any]] = None


@dataclass
class SarifTool:
    """SARIF tool definition."""
    driver: SarifToolComponent
    extensions: List[SarifToolComponent] = field(default_factory=list)


@dataclass
class SarifResult:
    """SARIF result (finding)."""
    rule_id: str
    message: SarifMessage
    level: SarifLevel = SarifLevel.WARNING
    kind: SarifKind = SarifKind.FAIL
    locations: List[SarifLocation] = field(default_factory=list)
    fixes: List[SarifFix] = field(default_factory=list)
    related_locations: List[SarifLocation] = field(default_factory=list)
    fingerprints: Optional[Dict[str, str]] = None
    partial_fingerprints: Optional[Dict[str, str]] = None
    code_flows: Optional[List[Dict[str, Any]]] = None
    properties: Optional[Dict[str, Any]] = None
    rule_index: Optional[int] = None

    # Convenience properties for CWE extraction
    @property
    def cwe_ids(self) -> List[str]:
        """Extract CWE IDs from properties."""
        if not self.properties:
            return []

        # Common locations for CWE in SARIF
        cwe_list = []

        # Direct CWE property
        if "cwe" in self.properties:
            cwe = self.properties["cwe"]
            if isinstance(cwe, list):
                cwe_list.extend(cwe)
            elif isinstance(cwe, str):
                cwe_list.append(cwe)

        # Tags containing CWE
        if "tags" in self.properties:
            for tag in self.properties["tags"]:
                if isinstance(tag, str) and tag.upper().startswith("CWE-"):
                    cwe_list.append(tag)

        return cwe_list


@dataclass
class SarifInvocation:
    """SARIF invocation (tool execution details)."""
    execution_successful: bool
    command_line: Optional[str] = None
    arguments: Optional[List[str]] = None
    working_directory: Optional[SarifArtifactLocation] = None
    start_time_utc: Optional[datetime] = None
    end_time_utc: Optional[datetime] = None
    exit_code: Optional[int] = None
    tool_execution_notifications: List[Dict[str, Any]] = field(default_factory=list)
    tool_configuration_notifications: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SarifRun:
    """SARIF run (single tool execution)."""
    tool: SarifTool
    results: List[SarifResult] = field(default_factory=list)
    invocations: List[SarifInvocation] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    logical_locations: List[SarifLogicalLocation] = field(default_factory=list)
    properties: Optional[Dict[str, Any]] = None

    @property
    def tool_name(self) -> str:
        """Get tool name."""
        return self.tool.driver.name

    @property
    def tool_version(self) -> Optional[str]:
        """Get tool version."""
        return self.tool.driver.version

    @property
    def finding_count(self) -> int:
        """Get number of findings."""
        return len(self.results)

    def get_rule(self, rule_id: str) -> Optional[SarifReportingDescriptor]:
        """Get rule definition by ID."""
        for rule in self.tool.driver.rules:
            if rule.id == rule_id:
                return rule
        return None


@dataclass
class SarifLog:
    """SARIF log (root object)."""
    version: str = "2.1.0"
    schema: str = "https://json.schemastore.org/sarif-2.1.0.json"
    runs: List[SarifRun] = field(default_factory=list)

    @property
    def total_findings(self) -> int:
        """Get total findings across all runs."""
        return sum(run.finding_count for run in self.runs)

    def get_findings_by_level(self, level: SarifLevel) -> List[SarifResult]:
        """Get all findings with specific severity level."""
        findings = []
        for run in self.runs:
            for result in run.results:
                if result.level == level:
                    findings.append(result)
        return findings

    def get_findings_by_cwe(self, cwe_id: str) -> List[SarifResult]:
        """Get all findings for a specific CWE."""
        findings = []
        normalized_cwe = cwe_id.upper()
        if not normalized_cwe.startswith("CWE-"):
            normalized_cwe = f"CWE-{normalized_cwe}"

        for run in self.runs:
            for result in run.results:
                for cwe in result.cwe_ids:
                    if cwe.upper() == normalized_cwe:
                        findings.append(result)
                        break
        return findings
