# Stability Detectors Package
# Language-specific resource leak detectors and analyzers
# Week 143-144 Implementation

from .classic_asp_detector import (
    ClassicASPLeakDetector,
    ClassicASPCOMDetector,
    ClassicASPFileDetector,
)

# Week 144: New analyzers
from .external_service_analyzer import (
    ExternalServiceAnalyzer,
    ExternalServiceIssueType,
    ExternalServiceCall,
    ExternalServiceFinding,
)

from .memory_analyzer import (
    MemoryAnalyzer,
    MemoryIssueType,
    MemoryOperation,
    MemoryFinding,
)

from .session_analyzer import (
    SessionAnalyzer,
    SessionIssueType,
    SessionOperation,
    SessionFinding,
)

from .include_resolver import (
    IncludeResolver,
    IncludeDirective,
    IncludeGraph,
    ResolvedFile,
    MergedContent,
)

# Week 145: Additional analyzers
from .exception_analyzer import (
    ExceptionAnalyzer,
    ExceptionIssueType,
    ErrorHandlingRegion,
    ExceptionFinding,
)

from .sql_analyzer import (
    SQLAnalyzer,
    SQLIssueType,
    SQLQuery,
    SQLFinding,
)

__all__ = [
    # Classic ASP detectors (Week 143)
    "ClassicASPLeakDetector",
    "ClassicASPCOMDetector",
    "ClassicASPFileDetector",
    # External Service Analyzer (Week 144 - Category 3)
    "ExternalServiceAnalyzer",
    "ExternalServiceIssueType",
    "ExternalServiceCall",
    "ExternalServiceFinding",
    # Memory Analyzer (Week 144 - Category 4)
    "MemoryAnalyzer",
    "MemoryIssueType",
    "MemoryOperation",
    "MemoryFinding",
    # Session Analyzer (Week 144 - Category 6)
    "SessionAnalyzer",
    "SessionIssueType",
    "SessionOperation",
    "SessionFinding",
    # Include Resolver (Week 144)
    "IncludeResolver",
    "IncludeDirective",
    "IncludeGraph",
    "ResolvedFile",
    "MergedContent",
    # Exception Analyzer (Week 145 - Category 7)
    "ExceptionAnalyzer",
    "ExceptionIssueType",
    "ErrorHandlingRegion",
    "ExceptionFinding",
    # SQL Analyzer (Week 145 - Category 8)
    "SQLAnalyzer",
    "SQLIssueType",
    "SQLQuery",
    "SQLFinding",
]
