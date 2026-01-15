"""
Unit tests for ContextAwareDocumentationService (J1 - Fase 24).

Tests cover:
- Python module documentation
- Docstring parsing (Google style, Sphinx style)
- Parameter and return value extraction
- API endpoint documentation
- Multiple export formats

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.context_aware_documentation_service import (
    DocType,
    DocFormat,
    Parameter,
    ReturnValue,
    CodeExample,
    DocumentationBlock,
    ModuleDocumentation,
    ProjectDocumentation,
    ContextAwareDocumentationService,
    create_context_aware_documentation_service,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh ContextAwareDocumentationService instance."""
    return ContextAwareDocumentationService()


@pytest.fixture
def sample_parameter():
    """Create a sample parameter."""
    return Parameter(
        name="user_id",
        type_hint="int",
        default=None,
        description="The user's unique identifier",
        is_required=True,
    )


@pytest.fixture
def sample_return_value():
    """Create a sample return value."""
    return ReturnValue(
        type_hint="Dict[str, Any]",
        description="User data including profile information",
    )


@pytest.fixture
def sample_documentation_block(sample_parameter, sample_return_value):
    """Create a sample documentation block."""
    return DocumentationBlock(
        doc_type=DocType.FUNCTION,
        name="get_user",
        qualified_name="app.users.get_user",
        description="Retrieve a user by their ID.",
        file_path="/project/app/users.py",
        line_number=42,
        parameters=[sample_parameter],
        return_value=sample_return_value,
        raises=["ValueError", "NotFoundError"],
        decorators=["async", "authenticated"],
        tags={"api", "users"},
    )


@pytest.fixture
def sample_python_code():
    """Create sample Python code for testing."""
    return '''
"""
Sample module for testing documentation generation.

This module demonstrates various documentation patterns.
"""

from typing import Dict, Any, Optional, List


class UserService:
    """
    Service for managing users.

    This class provides methods for CRUD operations on users.

    Attributes:
        db: Database connection
    """

    def __init__(self, db: Any):
        """Initialize the service.

        Args:
            db: Database connection instance
        """
        self.db = db

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User data dictionary or None if not found

        Raises:
            ValueError: If user_id is invalid
        """
        pass

    async def create_user(
        self,
        name: str,
        email: str,
        age: int = 18,
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            name: User's full name
            email: User's email address
            age: User's age (default: 18)

        Returns:
            Created user data

        Examples:
            >>> await service.create_user("John", "john@example.com")
        """
        pass


def helper_function(value: str) -> str:
    """A simple helper function.

    :param value: Input value
    :returns: Processed value
    """
    return value.upper()


def _private_function():
    """This is a private function."""
    pass
'''


@pytest.fixture
def temp_project(sample_python_code):
    """Create a temporary project with Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create directory structure
        app_dir = project_dir / "app"
        app_dir.mkdir()

        # Create main module
        (app_dir / "__init__.py").write_text("")
        (app_dir / "users.py").write_text(sample_python_code)

        # Create another module
        (app_dir / "config.py").write_text('''
"""Configuration module."""

class Config:
    """Application configuration."""
    DEBUG = True
''')

        yield project_dir


# ==================== Parameter Tests ====================

class TestParameter:
    """Test Parameter dataclass."""

    def test_parameter_creation(self, sample_parameter):
        """Test parameter creation."""
        assert sample_parameter.name == "user_id"
        assert sample_parameter.type_hint == "int"
        assert sample_parameter.is_required is True

    def test_optional_parameter(self):
        """Test optional parameter."""
        param = Parameter(
            name="limit",
            type_hint="int",
            default="10",
            description="Maximum items to return",
            is_required=False,
        )

        assert param.is_required is False
        assert param.default == "10"


# ==================== ReturnValue Tests ====================

class TestReturnValue:
    """Test ReturnValue dataclass."""

    def test_return_value_creation(self, sample_return_value):
        """Test return value creation."""
        assert sample_return_value.type_hint == "Dict[str, Any]"
        assert "profile" in sample_return_value.description

    def test_void_return(self):
        """Test void return value."""
        ret = ReturnValue(type_hint="None", description="")
        assert ret.type_hint == "None"


# ==================== DocumentationBlock Tests ====================

class TestDocumentationBlock:
    """Test DocumentationBlock functionality."""

    def test_to_dict(self, sample_documentation_block):
        """Test serialization to dictionary."""
        data = sample_documentation_block.to_dict()

        assert data["type"] == "function"
        assert data["name"] == "get_user"
        assert data["qualified_name"] == "app.users.get_user"
        assert len(data["parameters"]) == 1
        assert data["returns"]["type"] == "Dict[str, Any]"
        assert "ValueError" in data["raises"]

    def test_to_markdown_function(self, sample_documentation_block):
        """Test Markdown generation for function."""
        md = sample_documentation_block.to_markdown()

        assert "### `get_user()`" in md
        assert "**Parameters:**" in md
        assert "`user_id`" in md
        assert "**Returns:**" in md
        assert "**Raises:**" in md

    def test_to_markdown_class(self):
        """Test Markdown generation for class."""
        block = DocumentationBlock(
            doc_type=DocType.CLASS,
            name="UserService",
            qualified_name="app.users.UserService",
            description="Service for user management.",
            file_path="/project/app/users.py",
            line_number=10,
        )

        md = block.to_markdown()

        assert "## Class: `UserService`" in md

    def test_to_markdown_module(self):
        """Test Markdown generation for module."""
        block = DocumentationBlock(
            doc_type=DocType.MODULE,
            name="users",
            qualified_name="app.users",
            description="User management module.",
            file_path="/project/app/users.py",
            line_number=1,
        )

        md = block.to_markdown()

        assert "# users" in md

    def test_deprecated_block(self):
        """Test deprecated documentation block."""
        block = DocumentationBlock(
            doc_type=DocType.FUNCTION,
            name="old_function",
            qualified_name="app.old_function",
            description="An old function.",
            file_path="/project/app.py",
            line_number=1,
            deprecated=True,
            deprecation_message="Use new_function instead",
        )

        md = block.to_markdown()

        assert "**Deprecated**" in md
        assert "new_function" in md


# ==================== ModuleDocumentation Tests ====================

class TestModuleDocumentation:
    """Test ModuleDocumentation functionality."""

    def test_to_markdown(self, sample_documentation_block):
        """Test module Markdown generation."""
        module_doc = ModuleDocumentation(
            module_name="app.users",
            file_path="/project/app/users.py",
            description="User management module.",
            blocks=[sample_documentation_block],
            imports=["typing", "datetime"],
        )

        md = module_doc.to_markdown()

        assert "# Module: `app.users`" in md
        assert "## Table of Contents" in md


# ==================== ProjectDocumentation Tests ====================

class TestProjectDocumentation:
    """Test ProjectDocumentation functionality."""

    def test_to_markdown(self):
        """Test project Markdown generation."""
        project_doc = ProjectDocumentation(
            project_name="MyProject",
            project_path="/project",
            generated_at=datetime(2026, 1, 15, 12, 0, 0),
            total_modules=10,
            total_classes=25,
            total_functions=100,
            documentation_coverage=0.75,
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
        )

        md = project_doc.to_markdown()

        assert "# MyProject" in md
        assert "## Statistics" in md
        assert "**Modules:** 10" in md
        assert "75.0%" in md
        assert "## Tech Stack" in md


# ==================== ContextAwareDocumentationService Tests ====================

class TestContextAwareDocumentationService:
    """Test ContextAwareDocumentationService functionality."""

    def test_initialization(self, service):
        """Test service initialization."""
        assert service._context_cache == {}

    @pytest.mark.asyncio
    async def test_generate_documentation(self, service, temp_project):
        """Test full documentation generation."""
        project_doc = await service.generate_documentation(temp_project)

        assert project_doc.project_name == temp_project.name
        assert project_doc.total_modules >= 1
        assert project_doc.total_classes >= 1
        assert project_doc.total_functions >= 1

    @pytest.mark.asyncio
    async def test_generate_documentation_include_private(self, service, temp_project):
        """Test documentation including private members."""
        project_doc = await service.generate_documentation(
            temp_project,
            include_private=True,
        )

        # Should have more items when including private
        assert project_doc.total_functions >= 1

    def test_should_skip_test_files(self, service):
        """Test skipping test files."""
        assert service._should_skip(Path("/project/tests/test_users.py")) is True
        assert service._should_skip(Path("/project/app/users_test.py")) is True
        assert service._should_skip(Path("/project/__pycache__/users.pyc")) is True

    def test_should_not_skip_regular_files(self, service):
        """Test not skipping regular files."""
        assert service._should_skip(Path("/project/app/users.py")) is False
        assert service._should_skip(Path("/project/app/services/auth.py")) is False

    @pytest.mark.asyncio
    async def test_document_python_module(self, service, temp_project):
        """Test documenting a Python module."""
        users_file = temp_project / "app" / "users.py"

        module_doc = await service._document_python_module(
            users_file,
            temp_project,
            include_private=False,
        )

        assert module_doc is not None
        assert "users" in module_doc.module_name
        assert len(module_doc.blocks) >= 1

    def test_document_class(self, service, sample_python_code):
        """Test class documentation."""
        import ast
        tree = ast.parse(sample_python_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "UserService":
                block = service._document_class(node, "/test.py", "app")

                assert block.name == "UserService"
                assert block.doc_type == DocType.CLASS
                assert "CRUD" in block.description
                assert "get_user" in block.children
                break

    def test_document_function(self, service, sample_python_code):
        """Test function documentation."""
        import ast
        tree = ast.parse(sample_python_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "helper_function":
                block = service._document_function(node, "/test.py", "app")

                assert block.name == "helper_function"
                assert block.doc_type == DocType.FUNCTION
                assert len(block.parameters) == 1
                break

    def test_parse_parameters(self, service, sample_python_code):
        """Test parameter parsing."""
        import ast
        tree = ast.parse(sample_python_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_user":
                docstring = ast.get_docstring(node) or ""
                params = service._parse_parameters(node, docstring)

                assert len(params) == 3
                name_param = next(p for p in params if p.name == "name")
                assert name_param.is_required is True

                age_param = next(p for p in params if p.name == "age")
                assert age_param.is_required is False
                assert age_param.default == "18"
                break

    def test_parse_return(self, service, sample_python_code):
        """Test return value parsing."""
        import ast
        tree = ast.parse(sample_python_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_user":
                docstring = ast.get_docstring(node) or ""
                ret = service._parse_return(node, docstring)

                assert ret is not None
                assert "Optional" in ret.type_hint or "Dict" in ret.type_hint
                break

    def test_parse_raises(self, service):
        """Test raises parsing."""
        docstring = """
        Do something.

        Raises:
            ValueError: If value is invalid
            TypeError: If type is wrong
        """

        raises = service._parse_raises(docstring)

        assert "ValueError" in raises
        assert "TypeError" in raises

    def test_parse_docstring_params_google_style(self, service):
        """Test Google-style docstring parameter parsing."""
        docstring = """
        Do something.

        Args:
            name: The user's name
            email (str): The user's email
        """

        params = service._parse_docstring_params(docstring)

        assert params["name"] == "The user's name"
        assert "email" in params

    def test_parse_docstring_params_sphinx_style(self, service):
        """Test Sphinx-style docstring parameter parsing."""
        docstring = """
        Do something.

        :param name: The user's name
        :param email: The user's email
        :returns: Something
        """

        params = service._parse_docstring_params(docstring)

        assert params["name"] == "The user's name"
        assert params["email"] == "The user's email"

    def test_extract_examples(self, service):
        """Test example extraction."""
        docstring = '''
        Do something.

        Examples:
            ```python
            result = do_something()
            ```

            >>> do_something()
            'result'
        '''

        examples = service._extract_examples(docstring)

        assert len(examples) >= 1

    def test_extract_tags(self, service):
        """Test tag extraction."""
        docstring = """
        Do something.

        Tags: api, internal, v2

        @deprecated
        #important
        """

        tags = service._extract_tags(docstring)

        assert "api" in tags
        assert "deprecated" in tags
        assert "important" in tags

    def test_clean_description(self, service):
        """Test description cleaning."""
        docstring = """
        Do something useful.

        Args:
            name: User name

        Returns:
            Something
        """

        cleaned = service._clean_description(docstring)

        assert "Do something useful" in cleaned
        assert "Args:" not in cleaned
        assert "Returns:" not in cleaned

    @pytest.mark.asyncio
    async def test_document_api_endpoints(self, service):
        """Test API endpoint documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            router_file = Path(tmpdir) / "routes.py"
            router_file.write_text('''
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    pass

@router.post("/users/{user_id}")
async def update_user(user_id: int):
    pass
''')

            endpoints = await service.document_api_endpoints([router_file])

            assert len(endpoints) >= 1

    def test_export_documentation(self, service):
        """Test documentation export."""
        project_doc = ProjectDocumentation(
            project_name="TestProject",
            project_path="/project",
            generated_at=datetime.utcnow(),
            modules=[
                ModuleDocumentation(
                    module_name="app.main",
                    file_path="/project/app/main.py",
                    description="Main module.",
                    blocks=[],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "docs"
            created_files = service.export_documentation(project_doc, output_dir)

            assert len(created_files) >= 1
            assert (output_dir / "README.md").exists()


# ==================== Factory Function Tests ====================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_context_aware_documentation_service(self):
        """Test factory function creates service."""
        service = create_context_aware_documentation_service()

        assert isinstance(service, ContextAwareDocumentationService)


# ==================== DocType and DocFormat Tests ====================

class TestEnums:
    """Test enum values."""

    def test_doc_types(self):
        """Test all doc types are defined."""
        assert DocType.MODULE.value == "module"
        assert DocType.CLASS.value == "class"
        assert DocType.FUNCTION.value == "function"
        assert DocType.API_ENDPOINT.value == "api_endpoint"

    def test_doc_formats(self):
        """Test all doc formats are defined."""
        assert DocFormat.MARKDOWN.value == "markdown"
        assert DocFormat.RST.value == "restructuredtext"
        assert DocFormat.HTML.value == "html"
        assert DocFormat.JSON.value == "json"


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_project(self, service):
        """Test empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_doc = await service.generate_documentation(Path(tmpdir))

            assert project_doc.total_modules == 0
            assert project_doc.total_functions == 0

    @pytest.mark.asyncio
    async def test_invalid_python_file(self, service):
        """Test handling of invalid Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_file = Path(tmpdir) / "invalid.py"
            invalid_file.write_text("this is not valid python {{{{")

            module_doc = await service._document_python_module(
                invalid_file,
                Path(tmpdir),
                include_private=False,
            )

            assert module_doc is None

    @pytest.mark.asyncio
    async def test_module_without_docstring(self, service):
        """Test module without docstring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "nodoc.py"
            py_file.write_text("def foo(): pass")

            module_doc = await service._document_python_module(
                py_file,
                Path(tmpdir),
                include_private=False,
            )

            assert module_doc is not None
            assert module_doc.description == ""

    def test_documentation_coverage_calculation(self):
        """Test documentation coverage calculation."""
        # Module with 50% documented blocks
        project_doc = ProjectDocumentation(
            project_name="Test",
            project_path="/test",
            generated_at=datetime.utcnow(),
            documentation_coverage=0.5,
        )

        assert project_doc.documentation_coverage == 0.5

    def test_code_example_creation(self):
        """Test code example creation."""
        example = CodeExample(
            title="Basic Usage",
            code="result = func()",
            language="python",
            description="Shows basic usage",
        )

        assert example.title == "Basic Usage"
        assert example.language == "python"

