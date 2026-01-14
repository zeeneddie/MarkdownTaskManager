"""Security Scanner Models."""

from .sarif import (
    SarifLog,
    SarifRun,
    SarifResult,
    SarifTool,
    SarifToolComponent,
    SarifReportingDescriptor,
    SarifMessage,
    SarifLocation,
    SarifPhysicalLocation,
    SarifArtifactLocation,
    SarifRegion,
    SarifLogicalLocation,
    SarifLevel,
    SarifKind,
    SarifInvocation,
    SarifFix,
)

from .findings import (
    Severity,
    FindingStatus,
    ScannerType,
    CWE_TOP_25,
    Location,
    SuggestedFix,
    SecurityFinding,
    ScanResult,
    SecurityReport,
)


__all__ = [
    # SARIF models
    "SarifLog",
    "SarifRun",
    "SarifResult",
    "SarifTool",
    "SarifToolComponent",
    "SarifReportingDescriptor",
    "SarifMessage",
    "SarifLocation",
    "SarifPhysicalLocation",
    "SarifArtifactLocation",
    "SarifRegion",
    "SarifLogicalLocation",
    "SarifLevel",
    "SarifKind",
    "SarifInvocation",
    "SarifFix",
    # Finding models
    "Severity",
    "FindingStatus",
    "ScannerType",
    "CWE_TOP_25",
    "Location",
    "SuggestedFix",
    "SecurityFinding",
    "ScanResult",
    "SecurityReport",
]
