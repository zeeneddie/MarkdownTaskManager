"""
SARIF Parser Service.

Parses SARIF 2.1.0 JSON output from various security scanners
and converts to unified SecurityFinding models.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..models.sarif import (
    SarifLog, SarifRun, SarifResult, SarifTool, SarifToolComponent,
    SarifReportingDescriptor, SarifMessage, SarifLocation,
    SarifPhysicalLocation, SarifArtifactLocation, SarifRegion,
    SarifLogicalLocation, SarifLevel, SarifKind, SarifInvocation,
)
from ..models.findings import (
    SecurityFinding, Location, SuggestedFix, Severity, ScannerType,
)

logger = logging.getLogger(__name__)


# Level mapping from SARIF to unified severity
SARIF_LEVEL_TO_SEVERITY = {
    SarifLevel.ERROR: Severity.HIGH,
    SarifLevel.WARNING: Severity.MEDIUM,
    SarifLevel.NOTE: Severity.LOW,
    SarifLevel.NONE: Severity.INFO,
}


class SarifParser:
    """Parser for SARIF 2.1.0 format."""

    def __init__(self, scanner_type: ScannerType):
        """
        Initialize parser.

        Args:
            scanner_type: The scanner that produced the SARIF output
        """
        self.scanner_type = scanner_type

    def parse_file(self, file_path: Path) -> SarifLog:
        """Parse SARIF from file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return self.parse_json(json.load(f))

    def parse_string(self, sarif_string: str) -> SarifLog:
        """Parse SARIF from string."""
        return self.parse_json(json.loads(sarif_string))

    def parse_json(self, data: Dict[str, Any]) -> SarifLog:
        """Parse SARIF from JSON dict."""
        runs = []
        for run_data in data.get("runs", []):
            runs.append(self._parse_run(run_data))

        return SarifLog(
            version=data.get("version", "2.1.0"),
            schema=data.get("$schema", ""),
            runs=runs,
        )

    def _parse_run(self, data: Dict[str, Any]) -> SarifRun:
        """Parse a SARIF run."""
        tool = self._parse_tool(data.get("tool", {}))
        results = [
            self._parse_result(r, tool)
            for r in data.get("results", [])
        ]
        invocations = [
            self._parse_invocation(i)
            for i in data.get("invocations", [])
        ]

        return SarifRun(
            tool=tool,
            results=results,
            invocations=invocations,
            artifacts=data.get("artifacts", []),
            properties=data.get("properties"),
        )

    def _parse_tool(self, data: Dict[str, Any]) -> SarifTool:
        """Parse SARIF tool definition."""
        driver_data = data.get("driver", {})
        driver = SarifToolComponent(
            name=driver_data.get("name", "unknown"),
            version=driver_data.get("version"),
            semantic_version=driver_data.get("semanticVersion"),
            information_uri=driver_data.get("informationUri"),
            rules=[
                self._parse_rule(r)
                for r in driver_data.get("rules", [])
            ],
            properties=driver_data.get("properties"),
        )

        extensions = [
            SarifToolComponent(
                name=ext.get("name", ""),
                version=ext.get("version"),
                rules=[self._parse_rule(r) for r in ext.get("rules", [])],
            )
            for ext in data.get("extensions", [])
        ]

        return SarifTool(driver=driver, extensions=extensions)

    def _parse_rule(self, data: Dict[str, Any]) -> SarifReportingDescriptor:
        """Parse SARIF rule definition."""
        return SarifReportingDescriptor(
            id=data.get("id", ""),
            name=data.get("name"),
            short_description=self._parse_message(data.get("shortDescription")),
            full_description=self._parse_message(data.get("fullDescription")),
            help=self._parse_message(data.get("help")),
            help_uri=data.get("helpUri"),
            default_configuration=data.get("defaultConfiguration"),
            properties=data.get("properties"),
        )

    def _parse_message(self, data: Optional[Dict[str, Any]]) -> Optional[SarifMessage]:
        """Parse SARIF message."""
        if not data:
            return None
        return SarifMessage(
            text=data.get("text", ""),
            markdown=data.get("markdown"),
            id=data.get("id"),
            arguments=data.get("arguments"),
        )

    def _parse_result(self, data: Dict[str, Any], tool: SarifTool) -> SarifResult:
        """Parse SARIF result (finding)."""
        rule_id = data.get("ruleId", "")
        message_data = data.get("message", {})

        # Get level from result or rule default
        level_str = data.get("level", "warning")
        try:
            level = SarifLevel(level_str)
        except ValueError:
            level = SarifLevel.WARNING

        # Get kind
        kind_str = data.get("kind", "fail")
        try:
            kind = SarifKind(kind_str)
        except ValueError:
            kind = SarifKind.FAIL

        # Parse locations
        locations = [
            self._parse_location(loc)
            for loc in data.get("locations", [])
        ]

        # Parse related locations
        related_locations = [
            self._parse_location(loc)
            for loc in data.get("relatedLocations", [])
        ]

        # Get properties (contains CWE, tags, etc.)
        properties = data.get("properties", {})

        # Also check rule properties for CWE
        rule_index = data.get("ruleIndex")
        if rule_index is not None and rule_index < len(tool.driver.rules):
            rule = tool.driver.rules[rule_index]
            if rule.properties:
                # Merge rule properties
                properties = {**rule.properties, **properties}

        return SarifResult(
            rule_id=rule_id,
            message=SarifMessage(
                text=message_data.get("text", ""),
                markdown=message_data.get("markdown"),
            ),
            level=level,
            kind=kind,
            locations=locations,
            related_locations=related_locations,
            fingerprints=data.get("fingerprints"),
            partial_fingerprints=data.get("partialFingerprints"),
            code_flows=data.get("codeFlows"),
            properties=properties,
            rule_index=rule_index,
        )

    def _parse_location(self, data: Dict[str, Any]) -> SarifLocation:
        """Parse SARIF location."""
        physical = None
        physical_data = data.get("physicalLocation")
        if physical_data:
            artifact_loc = physical_data.get("artifactLocation", {})
            region_data = physical_data.get("region", {})

            physical = SarifPhysicalLocation(
                artifact_location=SarifArtifactLocation(
                    uri=artifact_loc.get("uri", ""),
                    uri_base_id=artifact_loc.get("uriBaseId"),
                    index=artifact_loc.get("index"),
                ),
                region=SarifRegion(
                    start_line=region_data.get("startLine", 1),
                    start_column=region_data.get("startColumn"),
                    end_line=region_data.get("endLine"),
                    end_column=region_data.get("endColumn"),
                    snippet=self._parse_message(region_data.get("snippet")),
                ) if region_data else None,
            )

        logical_locations = None
        logical_data = data.get("logicalLocations", [])
        if logical_data:
            logical_locations = [
                SarifLogicalLocation(
                    name=loc.get("name"),
                    fully_qualified_name=loc.get("fullyQualifiedName"),
                    kind=loc.get("kind"),
                )
                for loc in logical_data
            ]

        return SarifLocation(
            physical_location=physical,
            logical_locations=logical_locations,
            message=self._parse_message(data.get("message")),
        )

    def _parse_invocation(self, data: Dict[str, Any]) -> SarifInvocation:
        """Parse SARIF invocation."""
        return SarifInvocation(
            execution_successful=data.get("executionSuccessful", True),
            command_line=data.get("commandLine"),
            arguments=data.get("arguments"),
            exit_code=data.get("exitCode"),
        )

    def to_security_findings(self, sarif_log: SarifLog) -> List[SecurityFinding]:
        """Convert SARIF log to unified SecurityFinding list."""
        findings = []

        for run in sarif_log.runs:
            for result in run.results:
                finding = self._convert_result_to_finding(result, run)
                if finding:
                    findings.append(finding)

        return findings

    def _convert_result_to_finding(
        self,
        result: SarifResult,
        run: SarifRun
    ) -> Optional[SecurityFinding]:
        """Convert single SARIF result to SecurityFinding."""
        # Get location
        if not result.locations:
            logger.warning(f"Result {result.rule_id} has no locations, skipping")
            return None

        sarif_loc = result.locations[0]
        if not sarif_loc.physical_location:
            logger.warning(f"Result {result.rule_id} has no physical location, skipping")
            return None

        phys = sarif_loc.physical_location
        location = Location(
            file_path=phys.artifact_location.uri,
            start_line=phys.region.start_line if phys.region else 1,
            end_line=phys.region.end_line if phys.region else None,
            start_column=phys.region.start_column if phys.region else None,
            end_column=phys.region.end_column if phys.region else None,
            snippet=phys.region.snippet.text if phys.region and phys.region.snippet else None,
        )

        # Get logical location if available
        if sarif_loc.logical_locations:
            for log_loc in sarif_loc.logical_locations:
                if log_loc.kind == "function":
                    location.function_name = log_loc.name
                elif log_loc.kind == "class":
                    location.class_name = log_loc.name

        # Get rule info
        rule = run.get_rule(result.rule_id)
        title = result.rule_id
        description = result.message.text

        if rule:
            if rule.short_description:
                title = rule.short_description.text
            if rule.full_description:
                description = rule.full_description.text

        # Convert severity
        severity = SARIF_LEVEL_TO_SEVERITY.get(result.level, Severity.MEDIUM)

        # Check for security-specific severity in properties
        if result.properties:
            prop_severity = result.properties.get("security-severity")
            if prop_severity:
                try:
                    score = float(prop_severity)
                    if score >= 9.0:
                        severity = Severity.CRITICAL
                    elif score >= 7.0:
                        severity = Severity.HIGH
                    elif score >= 4.0:
                        severity = Severity.MEDIUM
                    else:
                        severity = Severity.LOW
                except (ValueError, TypeError):
                    pass

        # Extract CWE IDs
        cwe_ids = result.cwe_ids

        # Also check rule properties
        if rule and rule.properties:
            rule_cwes = rule.properties.get("cwe", [])
            if isinstance(rule_cwes, str):
                rule_cwes = [rule_cwes]
            cwe_ids.extend(rule_cwes)

        # Extract category/tags
        category = None
        tags = set()
        if result.properties:
            if "category" in result.properties:
                category = result.properties["category"]
            if "tags" in result.properties:
                tags.update(result.properties["tags"])

        # Generate ID
        finding_id = f"{self.scanner_type.value}-{result.rule_id}-{location.file_path}:{location.start_line}"

        return SecurityFinding(
            id=finding_id,
            rule_id=result.rule_id,
            title=title,
            description=description,
            severity=severity,
            scanner=self.scanner_type,
            location=location,
            cwe_ids=list(set(cwe_ids)),  # Deduplicate
            category=category,
            tags=tags,
            raw_data={"sarif_result": result.__dict__} if result else None,
        )


def create_sarif_parser(scanner_type: ScannerType) -> SarifParser:
    """Factory function to create SARIF parser."""
    return SarifParser(scanner_type=scanner_type)
