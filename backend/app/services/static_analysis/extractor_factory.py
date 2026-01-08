# backend/app/services/static_analysis/extractor_factory.py
"""
Extractor Factory - Factory for creating language-specific business rule extractors.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline

Features:
- Auto-detection of file language
- Tier-aware extractor creation
- Multi-file processing with aggregation
- Extensible extractor registration
"""

from typing import Dict, List, Optional, Type
from pathlib import Path
import logging
import time

from .base_business_rule_extractor import BaseBusinessRuleExtractor
from .extraction_models import (
    ExtractionResult,
    MultiFileExtractionResult,
    Language,
    ExtractionTier,
    EXTENSION_LANGUAGE_MAP,
)
from .vbnet_extractor import VBNetBusinessRuleExtractor
from .classic_asp_extractor import ClassicASPExtractor
from .tsql_extractor import TSQLBusinessRuleExtractor
from .plsql_extractor import PLSQLBusinessRuleExtractor
# Phase 3: AST-based extractors
from .python_ast_extractor import PythonASTExtractor
from .csharp_ast_extractor import CSharpASTExtractor
from .javascript_ast_extractor import JavaScriptASTExtractor
from .java_ast_extractor import JavaASTExtractor
# Phase 3.5: WebForms markup extractor
from .aspx_extractor import ASPXExtractor
# Phase 4: VB6 and PHP extractors
from .vb6_extractor import VB6BusinessRuleExtractor
from .php_extractor import PHPBusinessRuleExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """
    Factory for creating and managing business rule extractors.

    Provides:
    - Language detection from file extensions
    - Extractor creation with tier configuration
    - Multi-file extraction orchestration
    - Extensible extractor registration
    """

    # Registry of extractors by language
    _extractors: Dict[Language, Type[BaseBusinessRuleExtractor]] = {
        # Tier 2: Regex-based extractors (legacy languages)
        Language.VBNET: VBNetBusinessRuleExtractor,
        Language.CLASSIC_ASP: ClassicASPExtractor,
        Language.TSQL: TSQLBusinessRuleExtractor,
        Language.PLSQL: PLSQLBusinessRuleExtractor,
        # Tier 1: AST-based extractors (Phase 3 - modern languages)
        Language.PYTHON: PythonASTExtractor,
        Language.CSHARP: CSharpASTExtractor,
        Language.JAVASCRIPT: JavaScriptASTExtractor,
        Language.TYPESCRIPT: JavaScriptASTExtractor,  # Shared extractor handles both
        Language.JAVA: JavaASTExtractor,
        # Tier 2: WebForms markup extractor (Phase 3.5)
        Language.ASPX: ASPXExtractor,
        # Tier 2: Phase 4 extractors (VB6 + PHP)
        Language.VB6: VB6BusinessRuleExtractor,
        Language.PHP: PHPBusinessRuleExtractor,
    }

    # Extension to Language mapping with compound extension support
    _extension_map: Dict[str, Language] = {
        # VB.NET
        '.vb': Language.VBNET,
        '.aspx.vb': Language.VBNET,
        '.ascx.vb': Language.VBNET,
        # Classic ASP
        '.asp': Language.CLASSIC_ASP,
        '.asa': Language.CLASSIC_ASP,
        # T-SQL (SQL Server)
        '.sql': Language.TSQL,
        '.prc': Language.TSQL,
        # PL/SQL (Oracle)
        '.pkg': Language.PLSQL,
        '.pkb': Language.PLSQL,
        '.pks': Language.PLSQL,
        '.fnc': Language.PLSQL,
        '.trg': Language.PLSQL,
        # Python (Phase 3 - AST-based)
        '.py': Language.PYTHON,
        # C# (Phase 3 - AST-based)
        '.cs': Language.CSHARP,
        '.aspx.cs': Language.CSHARP,
        '.ascx.cs': Language.CSHARP,
        # JavaScript (Phase 3 - AST-based)
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.mjs': Language.JAVASCRIPT,
        '.cjs': Language.JAVASCRIPT,
        # TypeScript (Phase 3 - AST-based)
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        # Java (Phase 3 - AST-based)
        '.java': Language.JAVA,
        # ASPX/ASCX (Phase 3.5 - WebForms markup)
        '.aspx': Language.ASPX,
        '.ascx': Language.ASPX,
        '.master': Language.ASPX,
        # VB6 (Phase 4 - Legacy VB6)
        '.frm': Language.VB6,
        '.bas': Language.VB6,
        '.cls': Language.VB6,
        '.ctl': Language.VB6,
        '.vbp': Language.VB6,
        # PHP (Phase 4 - PHP/Laravel/WordPress)
        '.php': Language.PHP,
        '.phtml': Language.PHP,
        '.inc': Language.PHP,
    }

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        """
        Initialize the factory.

        Args:
            extraction_tier: Customer tier determining LLM access
            project_id: Optional project ID for tracking
        """
        self.extraction_tier = extraction_tier
        self.project_id = project_id
        self._extractor_cache: Dict[Language, BaseBusinessRuleExtractor] = {}

    @classmethod
    def register_extractor(
        cls,
        language: Language,
        extractor_class: Type[BaseBusinessRuleExtractor],
        extensions: Optional[List[str]] = None,
    ):
        """
        Register a new extractor for a language.

        Args:
            language: Language enum value
            extractor_class: Extractor class to register
            extensions: Optional list of file extensions to associate
        """
        cls._extractors[language] = extractor_class

        if extensions:
            for ext in extensions:
                cls._extension_map[ext.lower()] = language

        logger.info(f"Registered extractor for {language.value}: {extractor_class.__name__}")

    @classmethod
    def get_supported_languages(cls) -> List[Language]:
        """Get list of languages with registered extractors."""
        return list(cls._extractors.keys())

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions."""
        return list(cls._extension_map.keys())

    def detect_language(self, file_path: str) -> Optional[Language]:
        """
        Detect the language of a file from its extension.

        Args:
            file_path: Path to the file

        Returns:
            Language enum or None if not supported
        """
        path = Path(file_path)
        file_lower = file_path.lower()

        # Check compound extensions first (e.g., .aspx.vb)
        for ext, lang in sorted(self._extension_map.items(), key=lambda x: -len(x[0])):
            if file_lower.endswith(ext):
                return lang

        # Check simple extension
        simple_ext = path.suffix.lower()
        return self._extension_map.get(simple_ext)

    def get_extractor(self, language: Language) -> Optional[BaseBusinessRuleExtractor]:
        """
        Get or create an extractor for the given language.

        Args:
            language: Language to get extractor for

        Returns:
            Extractor instance or None if not supported
        """
        # Check cache
        if language in self._extractor_cache:
            return self._extractor_cache[language]

        # Get extractor class
        extractor_class = self._extractors.get(language)
        if not extractor_class:
            logger.warning(f"No extractor registered for language: {language.value}")
            return None

        # Create and cache instance
        extractor = extractor_class(
            extraction_tier=self.extraction_tier,
            project_id=self.project_id,
        )
        self._extractor_cache[language] = extractor

        return extractor

    def get_extractor_for_file(self, file_path: str) -> Optional[BaseBusinessRuleExtractor]:
        """
        Get an extractor for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Extractor instance or None if file type not supported
        """
        language = self.detect_language(file_path)
        if not language:
            return None
        return self.get_extractor(language)

    async def extract_from_file(self, file_path: str) -> Optional[ExtractionResult]:
        """
        Extract business rules from a single file.

        Args:
            file_path: Path to the file

        Returns:
            ExtractionResult or None if file type not supported
        """
        extractor = self.get_extractor_for_file(file_path)
        if not extractor:
            logger.warning(f"No extractor available for: {file_path}")
            return None

        return await extractor.extract_from_file(file_path)

    async def extract_from_directory(
        self,
        directory: str,
        recursive: bool = True,
        languages: Optional[List[Language]] = None,
    ) -> MultiFileExtractionResult:
        """
        Extract business rules from all supported files in a directory.

        Args:
            directory: Path to directory
            recursive: Whether to scan subdirectories
            languages: Optional filter for specific languages

        Returns:
            MultiFileExtractionResult with aggregated data
        """
        start_time = time.time()
        file_results: Dict[str, ExtractionResult] = {}
        path = Path(directory)

        if not path.exists():
            logger.error(f"Directory not found: {directory}")
            return MultiFileExtractionResult(
                project_id=self.project_id,
                base_path=directory,
                extraction_tier=self.extraction_tier,
                file_results={},
            )

        # Find all supported files
        pattern = '**/*' if recursive else '*'
        for file_path in path.glob(pattern):
            if not file_path.is_file():
                continue

            # Detect language
            language = self.detect_language(str(file_path))
            if not language:
                continue

            # Filter by requested languages
            if languages and language not in languages:
                continue

            # Get extractor and process
            extractor = self.get_extractor(language)
            if not extractor:
                continue

            try:
                result = await extractor.extract_from_file(str(file_path))
                file_results[str(file_path)] = result
                logger.debug(
                    f"Extracted {len(result.business_rules)} rules from {file_path.name}"
                )
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

        total_time = int((time.time() - start_time) * 1000)

        result = MultiFileExtractionResult(
            project_id=self.project_id,
            base_path=directory,
            extraction_tier=self.extraction_tier,
            file_results=file_results,
        )
        result.total_extraction_time_ms = total_time

        logger.info(
            f"Extracted {result.total_rules} rules from {result.total_files} files "
            f"in {total_time}ms"
        )

        return result

    async def extract_from_files(
        self,
        file_paths: List[str],
    ) -> MultiFileExtractionResult:
        """
        Extract business rules from a list of specific files.

        Args:
            file_paths: List of file paths to process

        Returns:
            MultiFileExtractionResult with aggregated data
        """
        start_time = time.time()
        file_results: Dict[str, ExtractionResult] = {}

        for file_path in file_paths:
            extractor = self.get_extractor_for_file(file_path)
            if not extractor:
                logger.warning(f"No extractor available for: {file_path}")
                continue

            try:
                result = await extractor.extract_from_file(file_path)
                file_results[file_path] = result
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

        total_time = int((time.time() - start_time) * 1000)

        # Determine base path as common parent
        if file_paths:
            paths = [Path(p) for p in file_paths]
            try:
                base_path = str(Path(*paths[0].parts[:len(paths[0].parts)-1]))
            except Exception:
                base_path = "."
        else:
            base_path = "."

        result = MultiFileExtractionResult(
            project_id=self.project_id,
            base_path=base_path,
            extraction_tier=self.extraction_tier,
            file_results=file_results,
        )
        result.total_extraction_time_ms = total_time

        return result


# Convenience function for quick extraction
async def extract_business_rules(
    path: str,
    tier: ExtractionTier = ExtractionTier.FREE,
    project_id: Optional[int] = None,
    languages: Optional[List[Language]] = None,
) -> MultiFileExtractionResult:
    """
    Convenience function for extracting business rules.

    Args:
        path: File or directory path
        tier: Extraction tier
        project_id: Optional project ID
        languages: Optional language filter

    Returns:
        MultiFileExtractionResult
    """
    factory = ExtractorFactory(extraction_tier=tier, project_id=project_id)
    p = Path(path)

    if p.is_file():
        result = await factory.extract_from_file(path)
        if result:
            return MultiFileExtractionResult(
                project_id=project_id,
                base_path=str(p.parent),
                extraction_tier=tier,
                file_results={path: result},
            )
        return MultiFileExtractionResult(
            project_id=project_id,
            base_path=str(p.parent),
            extraction_tier=tier,
            file_results={},
        )
    else:
        return await factory.extract_from_directory(path, languages=languages)
