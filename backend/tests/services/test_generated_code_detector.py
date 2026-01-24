"""
Unit tests for GeneratedCodeDetector service.

Tests detection of generated code via:
1. Directory patterns
2. File patterns (extensions and names)
3. Content markers
"""

import os
import tempfile
import pytest
from pathlib import Path

from app.services.generated_code_detector import (
    GeneratedCodeDetector,
    GeneratorType,
    GeneratedCodeMatch,
)


class TestGeneratedCodeDetector:
    """Test suite for GeneratedCodeDetector."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return GeneratedCodeDetector()

    # =========================================================================
    # DIRECTORY PATTERN TESTS
    # =========================================================================

    def test_directory_my_project(self, detector):
        """Test VB.NET 'My Project' directory detection."""
        is_gen, matched, gen_type = detector.is_generated_directory(
            "/app/MyApp/My Project/Settings.vb"
        )
        assert is_gen is True
        assert matched == "My Project"
        assert gen_type == GeneratorType.VISUAL_STUDIO_DESIGNER

    def test_directory_service_references(self, detector):
        """Test WCF Service References directory detection."""
        is_gen, matched, gen_type = detector.is_generated_directory(
            "/project/Service References/MyService/Reference.cs"
        )
        assert is_gen is True
        assert matched == "Service References"
        assert gen_type == GeneratorType.WCF_SERVICE

    def test_directory_node_modules(self, detector):
        """Test node_modules directory detection."""
        is_gen, matched, gen_type = detector.is_generated_directory(
            "/app/frontend/node_modules/react/index.js"
        )
        assert is_gen is True
        assert matched == "node_modules"
        assert gen_type == GeneratorType.PACKAGE_MANAGER

    def test_directory_obj(self, detector):
        """Test .NET obj directory detection."""
        is_gen, matched, gen_type = detector.is_generated_directory(
            "/project/obj/Debug/netcoreapp3.1/Project.dll"
        )
        assert is_gen is True
        assert matched == "obj"
        assert gen_type == GeneratorType.BUILD_OUTPUT

    def test_directory_not_generated(self, detector):
        """Test regular directory is not flagged as generated."""
        is_gen, matched, gen_type = detector.is_generated_directory(
            "/app/src/services/UserService.cs"
        )
        assert is_gen is False
        assert matched is None

    # =========================================================================
    # FILE PATTERN TESTS
    # =========================================================================

    def test_file_designer_vb(self, detector):
        """Test Windows Forms Designer.vb file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "Form1.Designer.vb"
        )
        assert is_gen is True
        assert matched == ".Designer.vb"
        assert gen_type == GeneratorType.WINDOWS_FORMS

    def test_file_designer_cs(self, detector):
        """Test Windows Forms Designer.cs file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "MainForm.Designer.cs"
        )
        assert is_gen is True
        assert matched == ".Designer.cs"
        assert gen_type == GeneratorType.WINDOWS_FORMS

    def test_file_g_cs(self, detector):
        """Test WPF generated .g.cs file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "MainWindow.g.cs"
        )
        assert is_gen is True
        assert matched == ".g.cs"
        assert gen_type == GeneratorType.WPF_XAML

    def test_file_pb_go(self, detector):
        """Test Protocol Buffers .pb.go file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "message.pb.go"
        )
        assert is_gen is True
        assert matched == ".pb.go"
        assert gen_type == GeneratorType.PROTOCOL_BUFFERS

    def test_file_min_js(self, detector):
        """Test minified .min.js file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "jquery.min.js"
        )
        assert is_gen is True
        assert matched == ".min.js"
        assert gen_type == GeneratorType.MINIFIED

    def test_file_reference_vb(self, detector):
        """Test WCF Reference.vb file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "Reference.vb"
        )
        assert is_gen is True
        assert matched == "Reference.vb"
        assert gen_type == GeneratorType.WEB_SERVICE

    def test_file_package_lock(self, detector):
        """Test package-lock.json file detection."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "package-lock.json"
        )
        assert is_gen is True
        assert matched == "package-lock.json"
        assert gen_type == GeneratorType.LOCK_FILE

    def test_file_not_generated(self, detector):
        """Test regular file is not flagged as generated."""
        is_gen, matched, gen_type = detector.is_generated_file_pattern(
            "UserService.cs"
        )
        assert is_gen is False
        assert matched is None

    # =========================================================================
    # CONTENT MARKER TESTS
    # =========================================================================

    def test_content_auto_generated_tag(self, detector):
        """Test <auto-generated> content marker detection."""
        content = """'------------------------------------------------------------------------------
' <auto-generated>
'     This code was generated by a tool.
' </auto-generated>
'------------------------------------------------------------------------------

Namespace MyApp
    Public Class Form1
    End Class
End Namespace
"""
        is_gen, matched, gen_type, confidence = detector.is_generated_by_content(
            "", content
        )
        assert is_gen is True
        assert matched == "<auto-generated>"
        assert confidence == 1.0

    def test_content_do_not_edit(self, detector):
        """Test DO NOT EDIT marker detection."""
        content = """// DO NOT EDIT - This file is auto-generated
package main
"""
        is_gen, matched, gen_type, confidence = detector.is_generated_by_content(
            "", content
        )
        assert is_gen is True
        assert matched == "DO NOT EDIT"
        assert confidence >= 0.9

    def test_content_generated_by(self, detector):
        """Test 'Generated by' marker detection."""
        content = """# Generated by protoc-gen-python v1.0
# Source: message.proto
"""
        is_gen, matched, gen_type, confidence = detector.is_generated_by_content(
            "", content
        )
        assert is_gen is True
        assert "Generated by" in matched or "protoc-gen" in matched
        assert confidence >= 0.9

    def test_content_wsdl_exe(self, detector):
        """Test wsdl.exe marker detection."""
        content = """'------------------------------------------------------------------------------
' This code was generated by wsdl.exe, Version=4.8.4084.0.
'------------------------------------------------------------------------------
"""
        is_gen, matched, gen_type, confidence = detector.is_generated_by_content(
            "", content
        )
        assert is_gen is True
        # May match "This code was generated" or "wsdl.exe" depending on order
        assert "generated" in matched.lower() or "wsdl" in matched.lower()
        assert confidence >= 0.9

    def test_content_not_generated(self, detector):
        """Test regular file content is not flagged as generated."""
        content = """using System;

namespace MyApp
{
    public class UserService
    {
        public void GetUser(int id)
        {
            // Implementation here
        }
    }
}
"""
        is_gen, matched, gen_type, confidence = detector.is_generated_by_content(
            "", content
        )
        assert is_gen is False

    # =========================================================================
    # FULL FILE DETECTION TESTS
    # =========================================================================

    def test_detect_file_by_directory(self, detector):
        """Test full file detection by directory pattern."""
        match = detector.detect_file(
            "/app/My Project/Settings.Designer.vb",
            check_content=False
        )
        assert match.is_generated is True
        assert match.detection_method == "directory"
        assert match.matched_pattern == "My Project"

    def test_detect_file_by_pattern(self, detector):
        """Test full file detection by file pattern."""
        match = detector.detect_file(
            "/app/src/Form1.Designer.cs",
            check_content=False
        )
        assert match.is_generated is True
        assert match.detection_method == "file_pattern"
        assert match.matched_pattern == ".Designer.cs"

    def test_detect_file_by_content(self, detector):
        """Test full file detection by content markers."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.cs', delete=False
        ) as f:
            f.write("""// <auto-generated>
// This code was generated by a tool
// </auto-generated>
namespace Generated {}
""")
            f.flush()

            try:
                match = detector.detect_file(f.name, check_content=True)
                assert match.is_generated is True
                assert match.detection_method == "content_marker"
                assert "<auto-generated>" in match.matched_pattern
            finally:
                os.unlink(f.name)

    def test_detect_file_not_generated(self, detector):
        """Test regular file detection."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.cs', delete=False
        ) as f:
            f.write("""using System;

namespace MyApp
{
    public class RegularService
    {
        public void DoWork() { }
    }
}
""")
            f.flush()

            try:
                match = detector.detect_file(f.name, check_content=True)
                assert match.is_generated is False
                assert match.detection_method == ""
            finally:
                os.unlink(f.name)

    # =========================================================================
    # DIRECTORY ANALYSIS TESTS
    # =========================================================================

    def test_analyze_directory(self, detector):
        """Test analyzing an entire directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            # Generated file
            gen_file = Path(tmpdir) / "Form1.Designer.cs"
            gen_file.write_text("// Windows Forms Designer generated code\n" * 100)

            # Regular file
            reg_file = Path(tmpdir) / "UserService.cs"
            reg_file.write_text("public class UserService {}\n" * 50)

            # Another generated file
            gen_file2 = Path(tmpdir) / "Reference.cs"
            gen_file2.write_text("// Web service reference\n" * 75)

            # Analyze
            summary = detector.analyze_directory(tmpdir, check_content=False)

            assert summary.total_files == 3
            assert summary.generated_files == 2  # Designer.cs and Reference.cs
            assert summary.handwritten_files == 1
            assert "file_pattern" in summary.by_detection_method

    # =========================================================================
    # EXPORT TESTS
    # =========================================================================

    def test_generate_gitattributes(self, detector):
        """Test .gitattributes generation."""
        content = detector.generate_gitattributes()

        assert "linguist-generated=true" in content
        assert "**/node_modules/**" in content
        assert "**/My Project/**" in content
        assert "*.Designer.vb" in content
        assert "*.min.js" in content
        assert "package-lock.json" in content

    def test_generate_sonar_exclusions(self, detector):
        """Test SonarQube exclusions generation."""
        content = detector.generate_sonar_exclusions()

        assert "sonar.exclusions=" in content
        assert "sonar.cpd.exclusions=" in content
        assert "**/node_modules/**" in content
        assert "**/*.Designer.*" in content or "**/My Project/**" in content


class TestGeneratorTypes:
    """Test generator type identification."""

    @pytest.fixture
    def detector(self):
        return GeneratedCodeDetector()

    def test_vs_designer_type(self, detector):
        """Test Visual Studio Designer type detection."""
        _, _, gen_type = detector.is_generated_directory("/app/My Project/file.vb")
        assert gen_type == GeneratorType.VISUAL_STUDIO_DESIGNER

    def test_wcf_service_type(self, detector):
        """Test WCF Service type detection."""
        _, _, gen_type = detector.is_generated_directory("/app/Service References/svc/ref.cs")
        assert gen_type == GeneratorType.WCF_SERVICE

    def test_protobuf_type(self, detector):
        """Test Protocol Buffers type detection."""
        _, _, gen_type = detector.is_generated_file_pattern("message.pb.go")
        assert gen_type == GeneratorType.PROTOCOL_BUFFERS

    def test_minified_type(self, detector):
        """Test minified file type detection."""
        _, _, gen_type = detector.is_generated_file_pattern("app.min.js")
        assert gen_type == GeneratorType.MINIFIED

    def test_lock_file_type(self, detector):
        """Test lock file type detection."""
        _, _, gen_type = detector.is_generated_file_pattern("yarn.lock")
        assert gen_type == GeneratorType.LOCK_FILE
