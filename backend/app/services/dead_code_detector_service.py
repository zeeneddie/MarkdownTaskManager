"""
DeadCodeDetectorService - Week 132

Multi-language dead code detection using static analysis.
Supports TypeScript, Python, C#, VB.NET, Java, and more.

Agent: Marcus (Maintenance Specialist)
"""
import ast
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.dead_code import (
    AnalysisType,
    DeadCodeAnalysisResult,
    DeadCodeItem,
    DeadCodeItemType,
    DetectionMethod,
    LANGUAGE_EXTENSIONS,
    RemovalRisk,
    SuggestedAction,
    TOOL_CONFIDENCE,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Detection Patterns
# ============================================================================

# Patterns for detecting unused code in different languages
UNUSED_PATTERNS = {
    "typescript": {
        "unused_import": r"^import\s+\{?\s*(\w+).*from\s+['\"]",
        "unused_function": r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)",
        "unused_const": r"^(?:export\s+)?const\s+(\w+)\s*=",
        "unused_class": r"^(?:export\s+)?class\s+(\w+)",
        "unused_interface": r"^(?:export\s+)?interface\s+(\w+)",
        "unused_type": r"^(?:export\s+)?type\s+(\w+)\s*=",
    },
    "javascript": {
        "unused_import": r"^import\s+\{?\s*(\w+).*from\s+['\"]",
        "unused_function": r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)",
        "unused_const": r"^(?:export\s+)?const\s+(\w+)\s*=",
        "unused_class": r"^(?:export\s+)?class\s+(\w+)",
    },
    "python": {
        "unused_import": r"^(?:from\s+\S+\s+)?import\s+(\w+)",
        "unused_function": r"^def\s+(\w+)\s*\(",
        "unused_class": r"^class\s+(\w+)",
        "unused_variable": r"^(\w+)\s*=\s*",
    },
    "csharp": {
        "unused_using": r"^using\s+(\w+(?:\.\w+)*);",
        "unused_method": r"(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?\w+\s+(\w+)\s*\(",
        "unused_class": r"(?:public|private|protected|internal)?\s*(?:static\s+)?(?:partial\s+)?class\s+(\w+)",
        "unused_property": r"(?:public|private|protected|internal)?\s*\w+\s+(\w+)\s*\{\s*get",
        "unused_field": r"(?:public|private|protected|internal)?\s*(?:static\s+)?(?:readonly\s+)?\w+\s+(\w+)\s*[;=]",
    },
    "vbnet": {
        "unused_imports": r"^Imports\s+(\w+(?:\.\w+)*)",
        "unused_sub": r"(?:Public|Private|Protected|Friend)?\s*(?:Shared\s+)?Sub\s+(\w+)",
        "unused_function": r"(?:Public|Private|Protected|Friend)?\s*(?:Shared\s+)?Function\s+(\w+)",
        "unused_class": r"(?:Public|Private|Protected|Friend)?\s*(?:Partial\s+)?Class\s+(\w+)",
        "unused_property": r"(?:Public|Private|Protected|Friend)?\s*Property\s+(\w+)",
    },
    "java": {
        "unused_import": r"^import\s+(?:static\s+)?(\w+(?:\.\w+)*);",
        "unused_method": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*\(",
        "unused_class": r"(?:public|private|protected)?\s*(?:abstract\s+)?(?:final\s+)?class\s+(\w+)",
        "unused_field": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*[;=]",
    },
}

# Entry point patterns - code that is externally accessible
ENTRY_POINT_PATTERNS = {
    "typescript": [
        r"^export\s+default",
        r"^export\s+\{",
        r"app\.(get|post|put|delete|patch)\s*\(",
        r"@Controller",
        r"@Injectable",
    ],
    "javascript": [
        r"^export\s+default",
        r"^module\.exports",
        r"app\.(get|post|put|delete|patch)\s*\(",
    ],
    "python": [
        r"^if\s+__name__\s*==\s*['\"]__main__['\"]",
        r"@app\.route",
        r"@router\.(get|post|put|delete|patch)",
        r"@celery\.task",
        r"def\s+(test_|setUp|tearDown)",
    ],
    "csharp": [
        r"\[HttpGet\]",
        r"\[HttpPost\]",
        r"\[ApiController\]",
        r"public\s+static\s+void\s+Main\s*\(",
        r"\[TestMethod\]",
        r"\[Fact\]",
    ],
    "vbnet": [
        r"<WebMethod\(\)>",
        r"Sub\s+Main\s*\(",
        r"<TestMethod\(\)>",
        r"Page_Load",
    ],
    "java": [
        r"public\s+static\s+void\s+main\s*\(",
        r"@GetMapping",
        r"@PostMapping",
        r"@RequestMapping",
        r"@Test",
    ],
}


@dataclass
class SymbolDefinition:
    """A code symbol (function, class, variable, etc.)."""
    name: str
    symbol_type: DeadCodeItemType
    file_path: str
    line_start: int
    line_end: int
    language: str
    is_exported: bool = False
    is_entry_point: bool = False
    references: List[str] = field(default_factory=list)


class DeadCodeDetectorService:
    """
    Multi-language dead code detection service.

    Uses static analysis to identify:
    - Unused functions/methods
    - Unused classes
    - Unused imports
    - Unused variables/constants
    - Dead branches
    - Unreachable code
    """

    def __init__(self):
        self._symbol_cache: Dict[str, List[SymbolDefinition]] = {}

    def detect(
        self,
        project_path: Path,
        include_languages: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        include_tests: bool = False,
        confidence_threshold: float = 0.5,
    ) -> DeadCodeAnalysisResult:
        """
        Detect dead code in a project.

        Args:
            project_path: Root path of the project
            include_languages: Languages to analyze (None = all detected)
            exclude_patterns: Glob patterns to exclude
            include_tests: Whether to analyze test files
            confidence_threshold: Minimum confidence to report (0.0-1.0)

        Returns:
            DeadCodeAnalysisResult with findings
        """
        start_time = time.time()

        result = DeadCodeAnalysisResult(
            project_path=str(project_path),
            analysis_type=AnalysisType.STATIC,
        )

        if not project_path.exists():
            result.success = False
            result.errors.append(f"Project path does not exist: {project_path}")
            return result

        try:
            # Collect files by language
            files_by_language = self._collect_files(
                project_path, include_languages, exclude_patterns, include_tests
            )

            result.languages_detected = list(files_by_language.keys())

            # Build symbol table
            all_symbols: List[SymbolDefinition] = []
            all_references: Set[str] = set()

            for language, files in files_by_language.items():
                for file_path in files:
                    try:
                        symbols, refs = self._analyze_file(file_path, language)
                        all_symbols.extend(symbols)
                        all_references.update(refs)
                        result.total_files_scanned += 1
                        result.total_lines_scanned += self._count_lines(file_path)
                    except Exception as e:
                        logger.warning(f"Error analyzing {file_path}: {e}")
                        result.errors.append(f"Error analyzing {file_path}: {str(e)}")

            # Find unreferenced symbols
            for symbol in all_symbols:
                if symbol.is_entry_point or symbol.is_exported:
                    continue

                if symbol.name not in all_references:
                    confidence = self._calculate_confidence(symbol, all_references)

                    if confidence >= confidence_threshold:
                        item = self._create_dead_code_item(symbol, confidence)
                        result.items.append(item)

            # Calculate statistics
            result.dead_code_count = len(result.items)
            result.dead_lines_count = sum(item.lines_count for item in result.items)

            if result.total_lines_scanned > 0:
                result.dead_code_percentage = (
                    result.dead_lines_count / result.total_lines_scanned * 100
                )

            result.safe_removal_count = len([
                i for i in result.items
                if i.removal_risk in [RemovalRisk.SAFE, RemovalRisk.LOW]
            ])
            result.risky_removal_count = len([
                i for i in result.items
                if i.removal_risk in [RemovalRisk.HIGH, RemovalRisk.CRITICAL]
            ])

            # Estimate cleanup time (1 minute per safe, 5 minutes per risky)
            result.estimated_cleanup_hours = (
                result.safe_removal_count * 1 + result.risky_removal_count * 5
            ) / 60

            # Generate recommendations
            result.recommendations = self._generate_recommendations(result)
            result.tools_used = self._get_tools_used(result.languages_detected)

        except Exception as e:
            logger.error(f"Dead code detection failed: {e}")
            result.success = False
            result.errors.append(str(e))

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _collect_files(
        self,
        project_path: Path,
        include_languages: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
        include_tests: bool,
    ) -> Dict[str, List[Path]]:
        """Collect files organized by language."""
        files_by_language: Dict[str, List[Path]] = {}

        exclude_dirs = {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "dist", "build", "bin", "obj", ".idea", ".vs"
        }

        if not include_tests:
            exclude_dirs.update({"test", "tests", "__tests__", "spec"})

        for lang, extensions in LANGUAGE_EXTENSIONS.items():
            if include_languages and lang not in include_languages:
                continue

            for ext in extensions:
                for file_path in project_path.rglob(f"*{ext}"):
                    # Skip excluded directories
                    if any(excl in file_path.parts for excl in exclude_dirs):
                        continue

                    # Skip test files if not included
                    if not include_tests:
                        if any(t in file_path.name.lower() for t in ["test", "spec", ".test.", ".spec."]):
                            continue

                    # Apply exclude patterns
                    if exclude_patterns:
                        if any(file_path.match(p) for p in exclude_patterns):
                            continue

                    if lang not in files_by_language:
                        files_by_language[lang] = []
                    files_by_language[lang].append(file_path)

        return files_by_language

    def _analyze_file(
        self, file_path: Path, language: str
    ) -> Tuple[List[SymbolDefinition], Set[str]]:
        """Analyze a single file for symbols and references."""
        symbols: List[SymbolDefinition] = []
        references: Set[str] = set()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return symbols, references

        lines = content.split("\n")

        # Language-specific analysis
        if language == "python":
            symbols, references = self._analyze_python(file_path, content)
        else:
            symbols, references = self._analyze_generic(file_path, content, language, lines)

        # Check for entry points
        entry_patterns = ENTRY_POINT_PATTERNS.get(language, [])
        for symbol in symbols:
            for pattern in entry_patterns:
                if re.search(pattern, content, re.MULTILINE):
                    symbol.is_entry_point = True
                    break

        return symbols, references

    def _analyze_python(
        self, file_path: Path, content: str
    ) -> Tuple[List[SymbolDefinition], Set[str]]:
        """Analyze Python file using AST."""
        symbols: List[SymbolDefinition] = []
        references: Set[str] = set()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to regex-based analysis
            return self._analyze_generic(file_path, content, "python", content.split("\n"))

        # Collect definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(SymbolDefinition(
                    name=node.name,
                    symbol_type=DeadCodeItemType.FUNCTION,
                    file_path=str(file_path),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    language="python",
                    is_exported=not node.name.startswith("_"),
                ))
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(SymbolDefinition(
                    name=node.name,
                    symbol_type=DeadCodeItemType.FUNCTION,
                    file_path=str(file_path),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    language="python",
                    is_exported=not node.name.startswith("_"),
                ))
            elif isinstance(node, ast.ClassDef):
                symbols.append(SymbolDefinition(
                    name=node.name,
                    symbol_type=DeadCodeItemType.CLASS,
                    file_path=str(file_path),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    language="python",
                    is_exported=not node.name.startswith("_"),
                ))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[0]
                        symbols.append(SymbolDefinition(
                            name=name,
                            symbol_type=DeadCodeItemType.IMPORT,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.lineno,
                            language="python",
                        ))
                else:
                    for alias in node.names:
                        if alias.name != "*":
                            name = alias.asname or alias.name
                            symbols.append(SymbolDefinition(
                                name=name,
                                symbol_type=DeadCodeItemType.IMPORT,
                                file_path=str(file_path),
                                line_start=node.lineno,
                                line_end=node.lineno,
                                language="python",
                            ))

        # Collect references (names used in the code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                references.add(node.id)
            elif isinstance(node, ast.Attribute):
                references.add(node.attr)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    references.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    references.add(node.func.attr)

        return symbols, references

    def _analyze_generic(
        self, file_path: Path, content: str, language: str, lines: List[str]
    ) -> Tuple[List[SymbolDefinition], Set[str]]:
        """Generic regex-based analysis for non-Python languages."""
        symbols: List[SymbolDefinition] = []
        references: Set[str] = set()

        patterns = UNUSED_PATTERNS.get(language, {})

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            for pattern_name, pattern in patterns.items():
                match = re.match(pattern, stripped, re.IGNORECASE)
                if match:
                    name = match.group(1)

                    # Determine symbol type
                    if "import" in pattern_name or "using" in pattern_name:
                        symbol_type = DeadCodeItemType.IMPORT
                    elif "class" in pattern_name:
                        symbol_type = DeadCodeItemType.CLASS
                    elif "function" in pattern_name or "method" in pattern_name or "sub" in pattern_name:
                        symbol_type = DeadCodeItemType.FUNCTION
                    elif "property" in pattern_name:
                        symbol_type = DeadCodeItemType.PROPERTY
                    elif "field" in pattern_name:
                        symbol_type = DeadCodeItemType.VARIABLE
                    elif "const" in pattern_name or "variable" in pattern_name:
                        symbol_type = DeadCodeItemType.VARIABLE
                    elif "interface" in pattern_name or "type" in pattern_name:
                        symbol_type = DeadCodeItemType.CLASS
                    else:
                        symbol_type = DeadCodeItemType.VARIABLE

                    is_exported = "export" in stripped.lower() or "public" in stripped.lower()

                    symbols.append(SymbolDefinition(
                        name=name,
                        symbol_type=symbol_type,
                        file_path=str(file_path),
                        line_start=line_num,
                        line_end=line_num,  # Simplified - would need block detection
                        language=language,
                        is_exported=is_exported,
                    ))

        # Collect all identifiers as potential references
        identifier_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        for match in re.finditer(identifier_pattern, content):
            references.add(match.group(1))

        return symbols, references

    def _calculate_confidence(
        self, symbol: SymbolDefinition, all_references: Set[str]
    ) -> float:
        """Calculate confidence that a symbol is truly dead code."""
        base_confidence = TOOL_CONFIDENCE.get("custom_vb", {}).get(symbol.language, 0.6)

        # Higher confidence for imports (easier to detect)
        if symbol.symbol_type == DeadCodeItemType.IMPORT:
            base_confidence += 0.15

        # Lower confidence for methods (might be called via reflection)
        if symbol.symbol_type == DeadCodeItemType.METHOD:
            base_confidence -= 0.1

        # Lower confidence for public/exported symbols
        if symbol.is_exported:
            base_confidence -= 0.2

        # Check for partial name matches (e.g., used via string concatenation)
        partial_matches = [ref for ref in all_references if symbol.name in ref]
        if len(partial_matches) > 1:
            base_confidence -= 0.1

        return max(0.0, min(1.0, base_confidence))

    def _create_dead_code_item(
        self, symbol: SymbolDefinition, confidence: float
    ) -> DeadCodeItem:
        """Create a DeadCodeItem from a SymbolDefinition."""
        # Determine removal risk based on symbol type and confidence
        if confidence >= 0.9:
            removal_risk = RemovalRisk.SAFE
            suggested_action = SuggestedAction.REMOVE
        elif confidence >= 0.75:
            removal_risk = RemovalRisk.LOW
            suggested_action = SuggestedAction.REMOVE
        elif confidence >= 0.6:
            removal_risk = RemovalRisk.MEDIUM
            suggested_action = SuggestedAction.REVIEW
        elif confidence >= 0.45:
            removal_risk = RemovalRisk.HIGH
            suggested_action = SuggestedAction.REVIEW
        else:
            removal_risk = RemovalRisk.CRITICAL
            suggested_action = SuggestedAction.KEEP

        # Public/exported symbols are riskier to remove
        if symbol.is_exported:
            removal_risk = RemovalRisk(min(
                RemovalRisk.CRITICAL.value,
                list(RemovalRisk).index(removal_risk) + 1
            ))

        lines_count = symbol.line_end - symbol.line_start + 1

        reason = f"No references found for {symbol.symbol_type.value} '{symbol.name}'"
        if symbol.is_exported:
            reason += " (exported, may be used externally)"

        return DeadCodeItem(
            item_type=symbol.symbol_type,
            name=symbol.name,
            file_path=symbol.file_path,
            line_start=symbol.line_start,
            line_end=symbol.line_end,
            lines_count=lines_count,
            language=symbol.language,
            detection_method=DetectionMethod.STATIC,
            detection_tool=f"custom_{symbol.language}",
            confidence=confidence,
            removal_risk=removal_risk,
            reason=reason,
            references=symbol.references,
            suggested_action=suggested_action,
        )

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            return len(file_path.read_text(encoding="utf-8", errors="ignore").split("\n"))
        except Exception:
            return 0

    def _generate_recommendations(self, result: DeadCodeAnalysisResult) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        if result.dead_code_percentage > 20:
            recommendations.append(
                f"High dead code percentage ({result.dead_code_percentage:.1f}%). "
                "Consider a dedicated cleanup sprint."
            )
        elif result.dead_code_percentage > 10:
            recommendations.append(
                f"Moderate dead code ({result.dead_code_percentage:.1f}%). "
                "Schedule regular cleanup sessions."
            )

        if result.safe_removal_count > 0:
            recommendations.append(
                f"{result.safe_removal_count} items can be safely removed with high confidence."
            )

        # Group by type
        by_type: Dict[str, int] = {}
        for item in result.items:
            type_name = item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type)
            by_type[type_name] = by_type.get(type_name, 0) + 1

        if by_type.get("import", 0) > 10:
            recommendations.append(
                f"{by_type['import']} unused imports detected. "
                "Consider using auto-import cleanup tools."
            )

        if by_type.get("function", 0) > 5:
            recommendations.append(
                f"{by_type.get('function', 0)} unused functions detected. "
                "Review before removal - may be called dynamically."
            )

        if result.estimated_cleanup_hours > 0:
            recommendations.append(
                f"Estimated cleanup time: {result.estimated_cleanup_hours:.1f} hours"
            )

        return recommendations

    def _get_tools_used(self, languages: List[str]) -> List[str]:
        """Get list of detection tools used based on languages."""
        tools = []

        tool_mapping = {
            "typescript": "custom_ts (ts-prune compatible)",
            "javascript": "custom_js (eslint-unused compatible)",
            "python": "python_ast (vulture compatible)",
            "csharp": "custom_cs (roslyn compatible)",
            "vbnet": "custom_vb",
            "java": "custom_java (sonarqube compatible)",
        }

        for lang in languages:
            if lang in tool_mapping:
                tools.append(tool_mapping[lang])

        return tools

    def get_cleanup_script(
        self, result: DeadCodeAnalysisResult, safe_only: bool = True
    ) -> str:
        """
        Generate a cleanup script for removing dead code.

        Args:
            result: Analysis result
            safe_only: Only include safe removals

        Returns:
            Shell script content
        """
        items = result.items
        if safe_only:
            items = [i for i in items if i.removal_risk in [RemovalRisk.SAFE, RemovalRisk.LOW]]

        lines = [
            "#!/bin/bash",
            "# Dead Code Cleanup Script",
            f"# Generated for: {result.project_path}",
            f"# Items to remove: {len(items)}",
            "",
            "# WARNING: Review each change before committing!",
            "",
        ]

        # Group by file
        by_file: Dict[str, List[DeadCodeItem]] = {}
        for item in items:
            if item.file_path not in by_file:
                by_file[item.file_path] = []
            by_file[item.file_path].append(item)

        for file_path, file_items in by_file.items():
            lines.append(f"# File: {file_path}")
            for item in sorted(file_items, key=lambda x: -(x.line_start or 0)):
                lines.append(
                    f"# Remove {item.item_type.value if hasattr(item.item_type, 'value') else item.item_type}: "
                    f"{item.name} (lines {item.line_start}-{item.line_end})"
                )
            lines.append("")

        return "\n".join(lines)
