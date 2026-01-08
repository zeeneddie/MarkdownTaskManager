# Classic ASP Resource Leak Detector
# Detects ADO Connection/Recordset leaks in Classic ASP (VBScript) code
#
# Based on FysioOne Audit learnings (2026-01-06):
# - Case-insensitive matching (VBScript is case-insensitive)
# - Set = Nothing does NOT release connection! Require .Close() first
# - Reopen pattern detection (Open→Close→Open without final close)
# - Connection leaks = pool exhaustion = CRITICAL
# - Wrapper function analysis (CreateCusCon, CreateRecordset)
#
# See: docs/architecture/resource-leak-detection-framework.md

from typing import List, Dict
from ..base_detector import BaseResourceLeakDetector
from ..types import ResourceType, StabilityCategory


class ClassicASPLeakDetector(BaseResourceLeakDetector):
    """
    Classic ASP (VBScript) resource leak detector.

    Detects:
    - ADO Connection leaks (CRITICAL)
    - ADO Recordset leaks (HIGH)
    - COM Object leaks (XMLHTTP, ABCpdf, etc.) (HIGH)
    - File handle leaks (FSO, TextStream) (MEDIUM)

    Special handling:
    - Case-insensitive matching (VBScript)
    - Wrapper function support (CreateCusCon, CreateRecordset)
    - Reopen pattern detection
    - Set = Nothing without .Close() detection
    """

    def get_supported_extensions(self) -> List[str]:
        """Support .asp and .inc files."""
        return [".asp", ".inc"]

    def get_language(self) -> str:
        return "Classic ASP (VBScript)"

    def is_case_insensitive(self) -> bool:
        """VBScript is case-insensitive."""
        return True

    def get_category(self) -> StabilityCategory:
        return StabilityCategory.ADO_LEAKS

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        """
        Patterns for opening resources.

        All patterns capture the variable name in group 1.
        """
        return {
            ResourceType.DATABASE_CONNECTION: [
                # Direct ADODB.Connection creation
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ADODB\.Connection["\']\s*\)',
                # Wrapper function
                r'Set\s+(\w+)\s*=\s*CreateCusCon\s*\(',
                r'Set\s+(\w+)\s*=\s*GetConnection\s*\(',
                r'Set\s+(\w+)\s*=\s*OpenConnection\s*\(',
                # Note: .Open on connection is handled via CreateObject detection
            ],
            ResourceType.RECORDSET: [
                # Direct ADODB.Recordset creation
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ADODB\.Recordset["\']\s*\)',
                # Wrapper function
                r'Set\s+(\w+)\s*=\s*CreateRecordset\s*\(',
                r'Set\s+(\w+)\s*=\s*GetRecordset\s*\(',
                # Connection.Execute returns a recordset
                r'Set\s+(\w+)\s*=\s*\w+\.Execute\s*\(',
                # Recordset.Open is called on already created recordset
                # We track this via the Set CreateObject pattern above
            ],
            ResourceType.COM_OBJECT: [
                # XMLHTTP
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.ServerXMLHTTP["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Microsoft\.XMLHTTP["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.XMLHTTP["\']\s*\)',
                # XMLDOM
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Microsoft\.XMLDOM["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.DOMDocument["\']\s*\)',
                # ABCpdf
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ABCpdf\d*\.Doc["\']\s*\)',
                # Note: Generic CreateObject removed - too broad, matches ADODB types
                # Use specific patterns for each COM object type instead
            ],
            ResourceType.FILE_HANDLE: [
                # FileSystemObject
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Scripting\.FileSystemObject["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*CreateObject\s*\(\s*["\']Scripting\.FileSystemObject["\']\s*\)',
                # TextStream from FSO
                r'Set\s+(\w+)\s*=\s*\w+\.OpenTextFile\s*\(',
                r'Set\s+(\w+)\s*=\s*\w+\.CreateTextFile\s*\(',
            ],
            ResourceType.HTTP_CONNECTION: [
                # WinHttp
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']WinHttp\.WinHttpRequest["\']\s*\)',
            ],
            ResourceType.STREAM: [
                # ADODB.Stream
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ADODB\.Stream["\']\s*\)',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        """
        Patterns for closing resources.

        All patterns capture the variable name in group 1.
        """
        return {
            ResourceType.DATABASE_CONNECTION: [
                # Direct .Close
                r'(\w+)\.Close\b',
                # Wrapper functions for safe close
                r'Call\s+TryCloseConnection\s*\(\s*(\w+)\s*\)',
                r'Call\s+CloseConnection\s*\(\s*(\w+)\s*\)',
                r'TryCloseConnection\s+(\w+)',
                r'CloseConnection\s+(\w+)',
            ],
            ResourceType.RECORDSET: [
                r'(\w+)\.Close\b',
                r'Call\s+TryCloseRecordset\s*\(\s*(\w+)\s*\)',
                r'Call\s+CloseRecordset\s*\(\s*(\w+)\s*\)',
            ],
            ResourceType.COM_OBJECT: [
                # General cleanup
                r'(\w+)\.Close\b',
                # XMLHTTP abort
                r'(\w+)\.abort\b',
                # ABCpdf Clear
                r'(\w+)\.Clear\b',
            ],
            ResourceType.FILE_HANDLE: [
                r'(\w+)\.Close\b',
            ],
            ResourceType.HTTP_CONNECTION: [
                r'(\w+)\.Close\b',
            ],
            ResourceType.STREAM: [
                r'(\w+)\.Close\b',
            ],
        }

    def get_release_patterns(self) -> Dict[ResourceType, List[str]]:
        """
        Patterns for releasing resources (Set = Nothing).

        WARNING: Set = Nothing does NOT close the connection!
        This is detected as SET_WITHOUT_CLOSE if .Close() wasn't called first.
        """
        patterns = {}
        for resource_type in ResourceType:
            patterns[resource_type] = [
                # Set variable = Nothing
                r'Set\s+(\w+)\s*=\s*Nothing\b',
            ]
        return patterns

    def get_wrapper_functions(self) -> Dict[str, str]:
        """
        Map wrapper functions to their wrapped objects.

        These are common patterns in FysioOne and similar Classic ASP apps.
        """
        return {
            # Connection wrappers
            "CreateCusCon": "ADODB.Connection",
            "GetConnection": "ADODB.Connection",
            "OpenConnection": "ADODB.Connection",
            "CreateConnection": "ADODB.Connection",
            # Recordset wrappers
            "CreateRecordset": "ADODB.Recordset",
            "GetRecordset": "ADODB.Recordset",
            "OpenRecordset": "ADODB.Recordset",
            # Cleanup wrappers
            "TryCloseConnection": "CLOSE:ADODB.Connection",
            "CloseConnection": "CLOSE:ADODB.Connection",
            "TryCloseRecordset": "CLOSE:ADODB.Recordset",
            "CloseRecordset": "CLOSE:ADODB.Recordset",
        }

    def get_loop_patterns(self) -> List[str]:
        """Patterns that indicate loop structures."""
        return [
            r'\bDo\s+While\b',
            r'\bDo\s+Until\b',
            r'\bWhile\b.*',
            r'\bFor\s+Each\b',
            r'\bFor\s+\w+\s*=',
            r'\bLoop\b',
        ]

    def get_function_patterns(self) -> List[str]:
        """Patterns that indicate function/sub definitions."""
        return [
            r'^\s*(?:Public\s+|Private\s+)?Function\s+(\w+)\s*\(',
            r'^\s*(?:Public\s+|Private\s+)?Sub\s+(\w+)\s*\(',
        ]

    def get_early_exit_patterns(self) -> List[str]:
        """Patterns that indicate early exit."""
        return [
            r'\bResponse\.Redirect\b',
            r'\bResponse\.End\b',
            r'\bExit\s+Function\b',
            r'\bExit\s+Sub\b',
            r'\bExit\s+Do\b',
            r'\bExit\s+For\b',
        ]


class ClassicASPCOMDetector(BaseResourceLeakDetector):
    """
    Specialized detector for COM object leaks in Classic ASP.

    Covers Category 2: COM Objects (XMLHTTP, ABCpdf, XMLDOM)
    """

    def get_supported_extensions(self) -> List[str]:
        return [".asp", ".inc"]

    def get_language(self) -> str:
        return "Classic ASP (VBScript)"

    def is_case_insensitive(self) -> bool:
        return True

    def get_category(self) -> StabilityCategory:
        return StabilityCategory.COM_OBJECTS

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.COM_OBJECT: [
                # XMLHTTP variants
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.ServerXMLHTTP["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Microsoft\.XMLHTTP["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.XMLHTTP["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']WinHttp\.WinHttpRequest["\']\s*\)',
                # XMLDOM variants
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Microsoft\.XMLDOM["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.DOMDocument["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.DOMDocument\.\d+["\']\s*\)',
                # ABCpdf variants
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ABCpdf\d*\.Doc["\']\s*\)',
                # RegExp
                r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']VBScript\.RegExp["\']\s*\)',
                # Scripting objects
                r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']Scripting\.Dictionary["\']\s*\)',
            ],
            ResourceType.PDF_DOCUMENT: [
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']ABCpdf\d*\.Doc["\']\s*\)',
            ],
            ResourceType.XML_DOCUMENT: [
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Microsoft\.XMLDOM["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']MSXML2\.DOMDocument["\']\s*\)',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.COM_OBJECT: [
                r'(\w+)\.Close\b',
                r'(\w+)\.abort\b',
            ],
            ResourceType.PDF_DOCUMENT: [
                r'(\w+)\.Clear\b',
                r'(\w+)\.ClearData\b',
            ],
            ResourceType.XML_DOCUMENT: [
                # XMLDOM doesn't have explicit close, relies on Set = Nothing
            ],
        }

    def get_release_patterns(self) -> Dict[ResourceType, List[str]]:
        patterns = {}
        for resource_type in [ResourceType.COM_OBJECT, ResourceType.PDF_DOCUMENT, ResourceType.XML_DOCUMENT]:
            patterns[resource_type] = [
                r'Set\s+(\w+)\s*=\s*Nothing\b',
            ]
        return patterns

    def get_wrapper_functions(self) -> Dict[str, str]:
        return {}

    def get_loop_patterns(self) -> List[str]:
        return [
            r'\bDo\s+While\b',
            r'\bDo\s+Until\b',
            r'\bFor\s+Each\b',
            r'\bFor\s+\w+\s*=',
        ]

    def get_function_patterns(self) -> List[str]:
        return [
            r'^\s*(?:Public\s+|Private\s+)?Function\s+(\w+)\s*\(',
            r'^\s*(?:Public\s+|Private\s+)?Sub\s+(\w+)\s*\(',
        ]

    def get_early_exit_patterns(self) -> List[str]:
        return [
            r'\bResponse\.Redirect\b',
            r'\bResponse\.End\b',
            r'\bExit\s+Function\b',
            r'\bExit\s+Sub\b',
        ]


class ClassicASPFileDetector(BaseResourceLeakDetector):
    """
    Specialized detector for file handle leaks in Classic ASP.

    Covers Category 5: File Handles (FSO, TextStream)
    """

    def get_supported_extensions(self) -> List[str]:
        return [".asp", ".inc"]

    def get_language(self) -> str:
        return "Classic ASP (VBScript)"

    def is_case_insensitive(self) -> bool:
        return True

    def get_category(self) -> StabilityCategory:
        return StabilityCategory.FILE_HANDLES

    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.FILE_HANDLE: [
                # FileSystemObject
                r'Set\s+(\w+)\s*=\s*Server\.CreateObject\s*\(\s*["\']Scripting\.FileSystemObject["\']\s*\)',
                r'Set\s+(\w+)\s*=\s*CreateObject\s*\(\s*["\']Scripting\.FileSystemObject["\']\s*\)',
                # TextStream from FSO methods
                r'Set\s+(\w+)\s*=\s*\w+\.OpenTextFile\s*\(',
                r'Set\s+(\w+)\s*=\s*\w+\.CreateTextFile\s*\(',
                r'Set\s+(\w+)\s*=\s*\w+\.GetFile\s*\(',
            ],
        }

    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.FILE_HANDLE: [
                r'(\w+)\.Close\b',
            ],
        }

    def get_release_patterns(self) -> Dict[ResourceType, List[str]]:
        return {
            ResourceType.FILE_HANDLE: [
                r'Set\s+(\w+)\s*=\s*Nothing\b',
            ],
        }

    def get_wrapper_functions(self) -> Dict[str, str]:
        return {}

    def get_loop_patterns(self) -> List[str]:
        return [
            r'\bDo\s+While\b',
            r'\bFor\s+Each\b',
            r'\bFor\s+\w+\s*=',
        ]

    def get_function_patterns(self) -> List[str]:
        return [
            r'^\s*(?:Public\s+|Private\s+)?Function\s+(\w+)\s*\(',
            r'^\s*(?:Public\s+|Private\s+)?Sub\s+(\w+)\s*\(',
        ]

    def get_early_exit_patterns(self) -> List[str]:
        return [
            r'\bResponse\.Redirect\b',
            r'\bResponse\.End\b',
        ]
