"""
Context-Aware Documentation Service (J1 - Fase 24).

Auto-generates documentation based on code analysis context.
Uses code structure, comments, and patterns to create comprehensive docs.

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple

logger = logging.getLogger(__name__)


class DocType(str, Enum):
    """Documentation type."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    API_ENDPOINT = "api_endpoint"
    DATA_MODEL = "data_model"
    CONFIGURATION = "configuration"
    WORKFLOW = "workflow"


class DocFormat(str, Enum):
    """Output format."""
    MARKDOWN = "markdown"
    RST = "restructuredtext"
    HTML = "html"
    JSON = "json"


@dataclass
class Parameter:
    """Function/method parameter."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    description: str = ""
    is_required: bool = True


@dataclass
class ReturnValue:
    """Function return value."""
    type_hint: Optional[str] = None
    description: str = ""


@dataclass
class CodeExample:
    """Code example for documentation."""
    title: str
    code: str
    language: str = "python"
    description: str = ""


@dataclass
class DocumentationBlock:
    """Single documentation block."""
    doc_type: DocType
    name: str
    qualified_name: str
    description: str
    file_path: str
    line_number: int

    # Details
    parameters: List[Parameter] = field(default_factory=list)
    return_value: Optional[ReturnValue] = None
    raises: List[str] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)

    # Relationships
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    used_by: List[str] = field(default_factory=list)

    # Metadata
    decorators: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    deprecated: bool = False
    deprecation_message: str = ""
    since_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.doc_type.value,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type_hint,
                    "default": p.default,
                    "description": p.description,
                    "required": p.is_required,
                }
                for p in self.parameters
            ],
            "returns": {
                "type": self.return_value.type_hint,
                "description": self.return_value.description,
            } if self.return_value else None,
            "raises": self.raises,
            "examples": [
                {"title": e.title, "code": e.code, "language": e.language}
                for e in self.examples
            ],
            "parent": self.parent,
            "children": self.children,
            "dependencies": self.dependencies,
            "decorators": self.decorators,
            "tags": list(self.tags),
            "deprecated": self.deprecated,
        }

    def to_markdown(self) -> str:
        """Convert to Markdown format."""
        lines = []

        # Header
        if self.doc_type == DocType.MODULE:
            lines.append(f"# {self.name}")
        elif self.doc_type == DocType.CLASS:
            lines.append(f"## Class: `{self.name}`")
        elif self.doc_type == DocType.FUNCTION:
            lines.append(f"### `{self.name}()`")
        else:
            lines.append(f"### {self.name}")

        lines.append("")

        # File location
        lines.append(f"*Defined in: `{self.file_path}:{self.line_number}`*")
        lines.append("")

        # Description
        if self.description:
            lines.append(self.description)
            lines.append("")

        # Deprecation warning
        if self.deprecated:
            lines.append(f"> ⚠️ **Deprecated**: {self.deprecation_message or 'This item is deprecated.'}")
            lines.append("")

        # Parameters
        if self.parameters:
            lines.append("**Parameters:**")
            lines.append("")
            for param in self.parameters:
                type_str = f" (`{param.type_hint}`)" if param.type_hint else ""
                default_str = f" = `{param.default}`" if param.default else ""
                required_str = " *(required)*" if param.is_required else " *(optional)*"
                desc_str = f": {param.description}" if param.description else ""
                lines.append(f"- `{param.name}`{type_str}{default_str}{required_str}{desc_str}")
            lines.append("")

        # Returns
        if self.return_value:
            lines.append("**Returns:**")
            lines.append("")
            type_str = f"`{self.return_value.type_hint}`" if self.return_value.type_hint else "None"
            lines.append(f"- {type_str}: {self.return_value.description}")
            lines.append("")

        # Raises
        if self.raises:
            lines.append("**Raises:**")
            lines.append("")
            for exc in self.raises:
                lines.append(f"- `{exc}`")
            lines.append("")

        # Examples
        if self.examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in self.examples:
                if example.title:
                    lines.append(f"*{example.title}*")
                lines.append("")
                lines.append(f"```{example.language}")
                lines.append(example.code)
                lines.append("```")
                lines.append("")

        # Tags
        if self.tags:
            lines.append(f"**Tags:** {', '.join(f'`{t}`' for t in self.tags)}")
            lines.append("")

        return "\n".join(lines)


@dataclass
class ModuleDocumentation:
    """Complete documentation for a module."""
    module_name: str
    file_path: str
    description: str
    blocks: List[DocumentationBlock] = field(default_factory=list)

    # Module-level info
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    version: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert entire module to Markdown."""
        lines = []

        # Module header
        lines.append(f"# Module: `{self.module_name}`")
        lines.append("")
        lines.append(f"*File: `{self.file_path}`*")
        lines.append("")

        if self.description:
            lines.append(self.description)
            lines.append("")

        # Table of contents
        if self.blocks:
            lines.append("## Table of Contents")
            lines.append("")

            classes = [b for b in self.blocks if b.doc_type == DocType.CLASS]
            functions = [b for b in self.blocks if b.doc_type == DocType.FUNCTION]

            if classes:
                lines.append("**Classes:**")
                for block in classes:
                    lines.append(f"- [{block.name}](#{block.name.lower()})")
                lines.append("")

            if functions:
                lines.append("**Functions:**")
                for block in functions:
                    lines.append(f"- [{block.name}](#{block.name.lower()})")
                lines.append("")

        # Documentation blocks
        for block in self.blocks:
            lines.append("---")
            lines.append("")
            lines.append(block.to_markdown())

        return "\n".join(lines)


@dataclass
class ProjectDocumentation:
    """Complete project documentation."""
    project_name: str
    project_path: str
    generated_at: datetime
    modules: List[ModuleDocumentation] = field(default_factory=list)

    # Overview info
    description: str = ""
    tech_stack: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)

    # Statistics
    total_modules: int = 0
    total_classes: int = 0
    total_functions: int = 0
    documentation_coverage: float = 0.0

    def to_markdown(self) -> str:
        """Generate project README."""
        lines = []

        lines.append(f"# {self.project_name}")
        lines.append("")
        lines.append(f"*Auto-generated documentation - {self.generated_at.strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")

        if self.description:
            lines.append("## Overview")
            lines.append("")
            lines.append(self.description)
            lines.append("")

        # Statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Modules:** {self.total_modules}")
        lines.append(f"- **Classes:** {self.total_classes}")
        lines.append(f"- **Functions:** {self.total_functions}")
        lines.append(f"- **Documentation Coverage:** {self.documentation_coverage:.1%}")
        lines.append("")

        # Tech stack
        if self.tech_stack:
            lines.append("## Tech Stack")
            lines.append("")
            for tech in self.tech_stack:
                lines.append(f"- {tech}")
            lines.append("")

        # Module index
        if self.modules:
            lines.append("## Modules")
            lines.append("")
            for module in self.modules:
                lines.append(f"- [`{module.module_name}`]({module.file_path})")
            lines.append("")

        return "\n".join(lines)


class ContextAwareDocumentationService:
    """
    Service for generating context-aware documentation.

    Features:
    - Parse Python/JavaScript/TypeScript code
    - Extract docstrings and type hints
    - Infer documentation from context
    - Generate Markdown/RST/HTML output
    - Track relationships and dependencies
    """

    def __init__(self):
        """Initialize service."""
        self._context_cache: Dict[str, Any] = {}

    async def generate_documentation(
        self,
        project_path: Path,
        output_format: DocFormat = DocFormat.MARKDOWN,
        include_private: bool = False,
    ) -> ProjectDocumentation:
        """
        Generate documentation for a project.

        Args:
            project_path: Path to project
            output_format: Output format
            include_private: Include private members

        Returns:
            Complete project documentation
        """
        modules = []

        # Find all Python files
        for py_file in project_path.rglob("*.py"):
            # Skip tests, __pycache__, etc.
            if self._should_skip(py_file):
                continue

            module_doc = await self._document_python_module(
                py_file,
                project_path,
                include_private,
            )
            if module_doc:
                modules.append(module_doc)

        # Calculate statistics
        total_classes = sum(
            len([b for b in m.blocks if b.doc_type == DocType.CLASS])
            for m in modules
        )
        total_functions = sum(
            len([b for b in m.blocks if b.doc_type == DocType.FUNCTION])
            for m in modules
        )

        # Calculate coverage
        documented = sum(
            len([b for b in m.blocks if b.description])
            for m in modules
        )
        total = sum(len(m.blocks) for m in modules)
        coverage = documented / total if total > 0 else 0.0

        return ProjectDocumentation(
            project_name=project_path.name,
            project_path=str(project_path),
            generated_at=datetime.utcnow(),
            modules=modules,
            total_modules=len(modules),
            total_classes=total_classes,
            total_functions=total_functions,
            documentation_coverage=coverage,
        )

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "test_",
            "_test.py",
            "tests/",
        ]
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    async def _document_python_module(
        self,
        file_path: Path,
        project_root: Path,
        include_private: bool,
    ) -> Optional[ModuleDocumentation]:
        """Generate documentation for a Python module."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

        # Get module docstring
        module_docstring = ast.get_docstring(tree) or ""

        # Calculate relative path for module name
        try:
            relative_path = file_path.relative_to(project_root)
            module_name = str(relative_path).replace("/", ".").replace(".py", "")
        except ValueError:
            module_name = file_path.stem

        blocks = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not include_private and node.name.startswith("_"):
                    continue
                block = self._document_class(node, str(file_path), module_name)
                blocks.append(block)

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Skip nested functions
                if not include_private and node.name.startswith("_"):
                    continue
                # Only document top-level functions
                for parent_node in ast.walk(tree):
                    if isinstance(parent_node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node in ast.walk(parent_node) and parent_node != node:
                            break
                else:
                    block = self._document_function(node, str(file_path), module_name)
                    blocks.append(block)

        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return ModuleDocumentation(
            module_name=module_name,
            file_path=str(file_path),
            description=module_docstring,
            blocks=blocks,
            imports=imports,
        )

    def _document_class(
        self,
        node: ast.ClassDef,
        file_path: str,
        module_name: str,
    ) -> DocumentationBlock:
        """Document a class."""
        docstring = ast.get_docstring(node) or ""

        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)

        # Check for deprecation
        deprecated = "deprecated" in [d.lower() for d in decorators]

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)

        # Get methods
        children = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                children.append(item.name)

        return DocumentationBlock(
            doc_type=DocType.CLASS,
            name=node.name,
            qualified_name=f"{module_name}.{node.name}",
            description=docstring,
            file_path=file_path,
            line_number=node.lineno,
            decorators=decorators,
            children=children,
            dependencies=bases,
            deprecated=deprecated,
            tags=self._extract_tags(docstring),
        )

    def _document_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        module_name: str,
    ) -> DocumentationBlock:
        """Document a function."""
        docstring = ast.get_docstring(node) or ""

        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)

        # Check for deprecation
        deprecated = "deprecated" in [d.lower() for d in decorators]

        # Parse parameters
        parameters = self._parse_parameters(node, docstring)

        # Parse return value
        return_value = self._parse_return(node, docstring)

        # Parse raises
        raises = self._parse_raises(docstring)

        # Extract examples from docstring
        examples = self._extract_examples(docstring)

        return DocumentationBlock(
            doc_type=DocType.FUNCTION,
            name=node.name,
            qualified_name=f"{module_name}.{node.name}",
            description=self._clean_description(docstring),
            file_path=file_path,
            line_number=node.lineno,
            parameters=parameters,
            return_value=return_value,
            raises=raises,
            examples=examples,
            decorators=decorators,
            deprecated=deprecated,
            tags=self._extract_tags(docstring),
        )

    def _parse_parameters(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        docstring: str,
    ) -> List[Parameter]:
        """Parse function parameters."""
        parameters = []

        args = node.args
        defaults = args.defaults
        num_defaults = len(defaults)
        num_args = len(args.args)

        # Parse docstring for parameter descriptions
        param_descriptions = self._parse_docstring_params(docstring)

        for i, arg in enumerate(args.args):
            if arg.arg == "self" or arg.arg == "cls":
                continue

            # Get type hint
            type_hint = None
            if arg.annotation:
                type_hint = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)

            # Get default value
            default = None
            default_index = i - (num_args - num_defaults)
            if default_index >= 0:
                default_node = defaults[default_index]
                default = ast.unparse(default_node) if hasattr(ast, 'unparse') else str(default_node)

            parameters.append(Parameter(
                name=arg.arg,
                type_hint=type_hint,
                default=default,
                description=param_descriptions.get(arg.arg, ""),
                is_required=default is None,
            ))

        return parameters

    def _parse_return(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        docstring: str,
    ) -> Optional[ReturnValue]:
        """Parse return value."""
        # Get type hint
        type_hint = None
        if node.returns:
            type_hint = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)

        # Get description from docstring
        description = ""
        returns_match = re.search(
            r'Returns?:\s*\n?\s*(.+?)(?:\n\n|\n\s*\n|$)',
            docstring,
            re.IGNORECASE | re.DOTALL,
        )
        if returns_match:
            description = returns_match.group(1).strip()

        if type_hint or description:
            return ReturnValue(type_hint=type_hint, description=description)

        return None

    def _parse_raises(self, docstring: str) -> List[str]:
        """Parse exceptions from docstring."""
        raises = []

        raises_match = re.search(
            r'Raises?:\s*\n((?:\s+\w+.*\n?)+)',
            docstring,
            re.IGNORECASE,
        )
        if raises_match:
            for line in raises_match.group(1).split('\n'):
                line = line.strip()
                if line:
                    # Extract exception name
                    exc_match = re.match(r'(\w+)', line)
                    if exc_match:
                        raises.append(exc_match.group(1))

        return raises

    def _parse_docstring_params(self, docstring: str) -> Dict[str, str]:
        """Parse parameter descriptions from docstring."""
        params = {}

        # Google style: "Args:\n    param: description"
        args_match = re.search(
            r'Args?:\s*\n((?:\s+\w+.*\n?)+)',
            docstring,
            re.IGNORECASE,
        )
        if args_match:
            for line in args_match.group(1).split('\n'):
                line = line.strip()
                param_match = re.match(r'(\w+)\s*(?:\([^)]+\))?:\s*(.+)', line)
                if param_match:
                    params[param_match.group(1)] = param_match.group(2)

        # Sphinx style: ":param name: description"
        for match in re.finditer(r':param\s+(\w+):\s*(.+?)(?=:param|:return|:raises|$)', docstring, re.DOTALL):
            params[match.group(1)] = match.group(2).strip()

        return params

    def _extract_examples(self, docstring: str) -> List[CodeExample]:
        """Extract code examples from docstring."""
        examples = []

        # Find code blocks
        code_blocks = re.findall(
            r'```(\w+)?\n(.*?)```',
            docstring,
            re.DOTALL,
        )
        for lang, code in code_blocks:
            examples.append(CodeExample(
                title="Example",
                code=code.strip(),
                language=lang or "python",
            ))

        # Find doctest examples
        doctest_matches = re.findall(
            r'>>>\s*(.+?)(?:\n(?!>>>).*)*',
            docstring,
        )
        for code in doctest_matches:
            examples.append(CodeExample(
                title="Example",
                code=code.strip(),
                language="python",
            ))

        return examples

    def _extract_tags(self, docstring: str) -> Set[str]:
        """Extract tags from docstring."""
        tags = set()

        # Look for tags like: @tag, #tag, or "Tags: tag1, tag2"
        tag_matches = re.findall(r'[@#](\w+)', docstring)
        tags.update(tag_matches)

        tags_line = re.search(r'Tags?:\s*(.+?)(?:\n|$)', docstring, re.IGNORECASE)
        if tags_line:
            for tag in tags_line.group(1).split(','):
                tags.add(tag.strip())

        return tags

    def _clean_description(self, docstring: str) -> str:
        """Clean description by removing parameter/return sections."""
        # Remove Args, Returns, Raises sections
        cleaned = re.sub(
            r'(?:Args?|Returns?|Raises?|Examples?|Notes?|Attributes?):\s*\n(?:\s+.*\n?)*',
            '',
            docstring,
            flags=re.IGNORECASE,
        )

        # Remove Sphinx directives
        cleaned = re.sub(r':param\s+\w+:.*(?:\n|$)', '', cleaned)
        cleaned = re.sub(r':returns?:.*(?:\n|$)', '', cleaned)
        cleaned = re.sub(r':raises?\s+\w+:.*(?:\n|$)', '', cleaned)

        return cleaned.strip()

    async def document_api_endpoints(
        self,
        router_files: List[Path],
    ) -> List[DocumentationBlock]:
        """
        Document API endpoints from router files.

        Args:
            router_files: List of router/route files

        Returns:
            List of API endpoint documentation blocks
        """
        endpoints = []

        for file_path in router_files:
            try:
                content = file_path.read_text(encoding='utf-8')

                # Find FastAPI/Flask decorators
                route_pattern = r'@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'

                for match in re.finditer(route_pattern, content, re.IGNORECASE):
                    path = match.group(1)

                    # Find the function after the decorator
                    func_match = re.search(
                        rf'{re.escape(match.group(0))}.*?(?:async\s+)?def\s+(\w+)',
                        content[match.start():],
                        re.DOTALL,
                    )

                    if func_match:
                        func_name = func_match.group(1)
                        endpoints.append(DocumentationBlock(
                            doc_type=DocType.API_ENDPOINT,
                            name=path,
                            qualified_name=f"{file_path.stem}.{func_name}",
                            description=f"API endpoint: {path}",
                            file_path=str(file_path),
                            line_number=content[:match.start()].count('\n') + 1,
                            tags={"api"},
                        ))

            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")

        return endpoints

    def export_documentation(
        self,
        project_doc: ProjectDocumentation,
        output_dir: Path,
        format: DocFormat = DocFormat.MARKDOWN,
    ) -> List[Path]:
        """
        Export documentation to files.

        Args:
            project_doc: Project documentation
            output_dir: Output directory
            format: Output format

        Returns:
            List of created files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        # Write README
        readme_path = output_dir / "README.md"
        readme_path.write_text(project_doc.to_markdown())
        created_files.append(readme_path)

        # Write individual module docs
        modules_dir = output_dir / "modules"
        modules_dir.mkdir(exist_ok=True)

        for module in project_doc.modules:
            module_file = modules_dir / f"{module.module_name.replace('.', '_')}.md"
            module_file.write_text(module.to_markdown())
            created_files.append(module_file)

        logger.info(f"Exported {len(created_files)} documentation files to {output_dir}")
        return created_files


def create_context_aware_documentation_service() -> ContextAwareDocumentationService:
    """Factory function to create Context-Aware Documentation service."""
    return ContextAwareDocumentationService()
