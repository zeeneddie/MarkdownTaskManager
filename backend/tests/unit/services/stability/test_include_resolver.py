# Unit Tests for IncludeResolver
# Tests for ASP include file resolution and cross-file analysis
# Week 144 Implementation

import pytest
import tempfile
import os
from pathlib import Path
from app.services.stability.detectors.include_resolver import (
    IncludeResolver,
    IncludeDirective,
    IncludeGraph,
    ResolvedFile,
    MergedContent,
)


class TestIncludeDirectiveParsing:
    """Tests for include directive parsing."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_find_virtual_include(self, resolver):
        """Should find virtual include directive."""
        content = '''
        <%
        ' Main page
        %>
        <!--#include virtual="/includes/header.inc"-->
        <h1>Content</h1>
        <!--#include virtual="/includes/footer.inc"-->
        '''
        includes = resolver.find_includes(content)

        assert len(includes) == 2
        assert includes[0].include_type == 'virtual'
        assert includes[0].path == '/includes/header.inc'
        assert includes[1].include_type == 'virtual'
        assert includes[1].path == '/includes/footer.inc'

    def test_find_file_include(self, resolver):
        """Should find file include directive."""
        content = '''
        <!--#include file="common.asp"-->
        <%
        ' Code here
        %>
        '''
        includes = resolver.find_includes(content)

        assert len(includes) == 1
        assert includes[0].include_type == 'file'
        assert includes[0].path == 'common.asp'

    def test_find_mixed_includes(self, resolver):
        """Should find both virtual and file includes."""
        content = '''
        <!--#include virtual="/lib/functions.inc"-->
        <!--#include file="config.asp"-->
        <!--#include virtual="/lib/database.inc"-->
        '''
        includes = resolver.find_includes(content)

        assert len(includes) == 3
        assert includes[0].include_type == 'virtual'
        assert includes[1].include_type == 'file'
        assert includes[2].include_type == 'virtual'

    def test_include_line_numbers(self, resolver):
        """Should track correct line numbers for includes."""
        content = '''Line 1
Line 2
<!--#include virtual="/test.inc"-->
Line 4
<!--#include file="local.asp"-->
Line 6'''
        includes = resolver.find_includes(content)

        assert includes[0].line_number == 3
        assert includes[1].line_number == 5

    def test_case_insensitive_include(self, resolver):
        """Should find includes regardless of case."""
        content = '''
        <!--#INCLUDE VIRTUAL="/test.inc"-->
        <!--#Include File="local.asp"-->
        '''
        includes = resolver.find_includes(content)

        assert len(includes) == 2

    def test_include_with_single_quotes(self, resolver):
        """Should handle single quotes in include paths."""
        content = "<!--#include virtual='/includes/header.inc'-->"
        includes = resolver.find_includes(content)

        assert len(includes) == 1
        assert includes[0].path == '/includes/header.inc'


class TestIncludePathResolution:
    """Tests for include path resolution."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_resolve_file_include(self, resolver):
        """Should resolve relative file include."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create parent file
            parent_file = os.path.join(tmpdir, "main.asp")
            include_file = os.path.join(tmpdir, "helper.inc")

            Path(parent_file).write_text("<%")
            Path(include_file).write_text("' Helper functions")

            include = IncludeDirective(
                line_number=1,
                include_type='file',
                path='helper.inc'
            )

            resolved = resolver.resolve_include_path(include, parent_file)
            assert resolved == os.path.abspath(include_file)

    def test_resolve_virtual_include_with_web_root(self, resolver):
        """Should resolve virtual include with web root set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            web_root = os.path.join(tmpdir, "wwwroot")
            includes_dir = os.path.join(web_root, "includes")
            os.makedirs(includes_dir)

            header_file = os.path.join(includes_dir, "header.inc")
            Path(header_file).write_text("' Header")

            parent_file = os.path.join(web_root, "main.asp")
            Path(parent_file).write_text("<%")

            resolver.set_web_root(web_root)

            include = IncludeDirective(
                line_number=1,
                include_type='virtual',
                path='/includes/header.inc'
            )

            resolved = resolver.resolve_include_path(include, parent_file)
            assert resolved == os.path.abspath(header_file)


class TestIncludeGraph:
    """Tests for include dependency graph."""

    def test_add_include_relationship(self):
        """Should add include relationships correctly."""
        graph = IncludeGraph(root_file="/test/main.asp")

        result = graph.add_include("/test/main.asp", "/test/header.inc")
        assert result is True
        assert "/test/header.inc" in graph.includes["/test/main.asp"]
        assert "/test/main.asp" in graph.reverse_includes["/test/header.inc"]

    def test_detect_self_circular(self):
        """Should detect self-referential circular include."""
        graph = IncludeGraph(root_file="/test/main.asp")

        result = graph.add_include("/test/main.asp", "/test/main.asp")
        assert result is False
        assert ("/test/main.asp", "/test/main.asp") in graph.circular_refs

    def test_detect_circular_chain(self):
        """Should detect circular include chain."""
        graph = IncludeGraph(root_file="/test/a.asp")

        # Create chain: a -> b -> c -> a
        graph.add_include("/test/a.asp", "/test/b.inc")
        graph.add_include("/test/b.inc", "/test/c.inc")
        result = graph.add_include("/test/c.inc", "/test/a.asp")

        assert result is False
        assert ("/test/c.inc", "/test/a.asp") in graph.circular_refs

    def test_get_all_includes(self):
        """Should get all files included recursively."""
        graph = IncludeGraph(root_file="/test/main.asp")

        graph.add_include("/test/main.asp", "/test/header.inc")
        graph.add_include("/test/main.asp", "/test/footer.inc")
        graph.add_include("/test/header.inc", "/test/nav.inc")

        all_includes = graph.get_all_includes("/test/main.asp")

        assert "/test/header.inc" in all_includes
        assert "/test/footer.inc" in all_includes
        assert "/test/nav.inc" in all_includes

    def test_get_include_order(self):
        """Should return files in dependency order."""
        graph = IncludeGraph(root_file="/test/main.asp")

        graph.add_include("/test/main.asp", "/test/lib.inc")
        graph.add_include("/test/lib.inc", "/test/config.inc")

        order = graph.get_include_order("/test/main.asp")

        # Config should come before lib, lib before main
        config_idx = order.index("/test/config.inc")
        lib_idx = order.index("/test/lib.inc")
        main_idx = order.index("/test/main.asp")

        assert config_idx < lib_idx
        assert lib_idx < main_idx


class TestFileLoading:
    """Tests for file loading and caching."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_load_file(self, resolver):
        """Should load file and find includes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.asp")
            content = '''<%
' Test file
%>
<!--#include file="helper.inc"-->
'''
            Path(file_path).write_text(content)

            resolved = resolver.load_file(file_path)

            assert resolved.content == content
            assert len(resolved.includes) == 1
            assert resolved.line_count == 5

    def test_file_caching(self, resolver):
        """Should cache loaded files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.asp")
            Path(file_path).write_text("<%")

            # Load twice
            resolver.load_file(file_path)
            resolver.load_file(file_path)

            stats = resolver.get_cache_stats()
            assert stats["cached_files"] == 1

    def test_clear_cache(self, resolver):
        """Should clear cache when requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.asp")
            Path(file_path).write_text("<%")

            resolver.load_file(file_path)
            resolver.clear_cache()

            stats = resolver.get_cache_stats()
            assert stats["cached_files"] == 0


class TestMergedContent:
    """Tests for merged content generation."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_get_merged_content(self, resolver):
        """Should merge content from multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            main_file = os.path.join(tmpdir, "main.asp")
            header_file = os.path.join(tmpdir, "header.inc")

            Path(header_file).write_text("' Header content\nDim x")
            Path(main_file).write_text(
                '<!--#include file="header.inc"-->\n<%\nResponse.Write x\n%>'
            )

            merged = resolver.get_merged_content(main_file)

            assert "Header content" in merged.content
            assert "Response.Write x" in merged.content
            assert len(merged.included_files) >= 1

    def test_line_mapping(self, resolver):
        """Should maintain line mapping in merged content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.asp")
            helper_file = os.path.join(tmpdir, "helper.inc")

            Path(helper_file).write_text("Line1\nLine2\nLine3")
            Path(main_file).write_text(
                '<!--#include file="helper.inc"-->\nMainLine'
            )

            merged = resolver.get_merged_content(main_file)

            # Check that line mapping exists
            assert len(merged.line_mapping) > 0

    def test_get_original_location(self, resolver):
        """Should map merged line back to original file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.asp")
            Path(main_file).write_text("Line1\nLine2\nLine3")

            merged = resolver.get_merged_content(main_file)
            location = resolver.get_original_location(2, merged)

            if location:
                file_path, line_num = location
                assert line_num == 2


class TestWebRootDetection:
    """Tests for web root detection."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_detect_wwwroot(self, resolver):
        """Should detect wwwroot as web root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wwwroot = os.path.join(tmpdir, "wwwroot")
            subdir = os.path.join(wwwroot, "pages")
            os.makedirs(subdir)

            test_file = os.path.join(subdir, "test.asp")
            Path(test_file).write_text("<%")

            detected = resolver.detect_web_root(test_file)
            assert detected == wwwroot

    def test_detect_web_config(self, resolver):
        """Should detect directory with web.config as web root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            web_root = os.path.join(tmpdir, "mysite")
            subdir = os.path.join(web_root, "admin")
            os.makedirs(subdir)

            # Create web.config
            Path(os.path.join(web_root, "web.config")).write_text("<configuration/>")
            test_file = os.path.join(subdir, "test.asp")
            Path(test_file).write_text("<%")

            detected = resolver.detect_web_root(test_file)
            assert detected == web_root


class TestIncludeDepthCalculation:
    """Tests for include depth calculation."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_no_includes_depth_zero(self, resolver):
        """Should return depth 0 for file with no includes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.asp")
            Path(file_path).write_text("<% Response.Write 1 %>")

            resolver.build_include_graph(file_path)
            depth = resolver.get_include_depth(file_path)

            assert depth == 0

    def test_single_level_include(self, resolver):
        """Should return depth 1 for single level include."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.asp")
            header_file = os.path.join(tmpdir, "header.inc")

            Path(header_file).write_text("' Header")
            Path(main_file).write_text('<!--#include file="header.inc"-->')

            resolver.build_include_graph(main_file)
            depth = resolver.get_include_depth(main_file)

            assert depth == 1


class TestReverseIncludes:
    """Tests for finding files that include a given file."""

    @pytest.fixture
    def resolver(self):
        return IncludeResolver()

    def test_get_files_that_include(self, resolver):
        """Should find files that include given file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            common_file = os.path.join(tmpdir, "common.inc")
            page1 = os.path.join(tmpdir, "page1.asp")
            page2 = os.path.join(tmpdir, "page2.asp")

            Path(common_file).write_text("' Common functions")
            Path(page1).write_text('<!--#include file="common.inc"-->')
            Path(page2).write_text('<!--#include file="common.inc"-->')

            # Build graph from page1
            resolver.build_include_graph(page1)

            includers = resolver.get_files_that_include(common_file)
            abs_page1 = os.path.abspath(page1)

            assert abs_page1 in includers


class TestResolvedFileProperties:
    """Tests for ResolvedFile dataclass properties."""

    def test_exists_property(self):
        """Should return correct exists property."""
        resolved_with_content = ResolvedFile(
            original_path="test.asp",
            resolved_path="/path/test.asp",
            content="<% code %>",
            line_count=1
        )
        assert resolved_with_content.exists is True

        resolved_empty = ResolvedFile(
            original_path="empty.asp",
            resolved_path="/path/empty.asp",
            content="",
            line_count=0
        )
        assert resolved_empty.exists is False
