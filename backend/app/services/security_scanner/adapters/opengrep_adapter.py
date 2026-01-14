"""
OpenGrep Scanner Adapter.

OpenGrep is the open-source fork of Semgrep (LGPL 2.1 license).
Supports 30+ languages with pattern-based security rules.

GitHub: https://github.com/opengrep/opengrep
Rules: https://github.com/opengrep/opengrep-rules
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from ..models.findings import ScannerType
from .base import ExternalCLIScanner


class OpenGrepAdapter(ExternalCLIScanner):
    """
    Adapter for OpenGrep security scanner.

    OpenGrep supports:
    - 30+ programming languages
    - Custom YAML rules
    - CWE/OWASP rule mapping
    - SARIF output
    """

    # Comprehensive language support
    SUPPORTED_LANGUAGES = {
        # Web/Scripting
        "javascript", "typescript", "python", "ruby", "php",
        # Systems
        "go", "rust", "c", "cpp",
        # JVM
        "java", "kotlin", "scala",
        # .NET
        "csharp",
        # Mobile
        "swift", "objective-c",
        # Other
        "lua", "r", "julia", "elixir", "clojure", "ocaml",
        # Config/IaC
        "terraform", "dockerfile", "yaml", "json", "xml", "html",
        # Solidity (blockchain)
        "solidity",
    }

    SUPPORTED_EXTENSIONS = {
        # JavaScript/TypeScript
        ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        # Python
        ".py", ".pyw",
        # Ruby
        ".rb", ".erb",
        # PHP
        ".php", ".phtml",
        # Go
        ".go",
        # Rust
        ".rs",
        # C/C++
        ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
        # Java
        ".java",
        # Kotlin
        ".kt", ".kts",
        # Scala
        ".scala",
        # C#
        ".cs",
        # Swift
        ".swift",
        # Objective-C
        ".m", ".mm",
        # Lua
        ".lua",
        # R
        ".r", ".R",
        # Julia
        ".jl",
        # Elixir
        ".ex", ".exs",
        # Clojure
        ".clj", ".cljs", ".cljc",
        # OCaml
        ".ml", ".mli",
        # Config
        ".tf", ".hcl",  # Terraform
        ".dockerfile", "Dockerfile",
        ".yaml", ".yml",
        ".json",
        ".xml",
        ".html", ".htm",
        # Solidity
        ".sol",
    }

    def __init__(
        self,
        rules_path: Optional[Path] = None,
        config_file: Optional[Path] = None,
        timeout_seconds: int = 600,
    ):
        """
        Initialize OpenGrep adapter.

        Args:
            rules_path: Path to custom rules directory (uses built-in if None)
            config_file: Path to opengrep.yaml config file
            timeout_seconds: Maximum execution time
        """
        # Try opengrep first, fall back to semgrep for compatibility
        super().__init__(binary_name="opengrep", timeout_seconds=timeout_seconds)
        self.rules_path = rules_path
        self.config_file = config_file
        self._fallback_to_semgrep = False

    def is_available(self) -> bool:
        """Check if opengrep or semgrep is available."""
        if super().is_available():
            return True

        # Fallback to semgrep if opengrep not installed
        import shutil
        semgrep_path = shutil.which("semgrep")
        if semgrep_path:
            self.binary_name = "semgrep"
            self._binary_path = semgrep_path
            self._fallback_to_semgrep = True
            self._available = True
            return True

        return False

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.OPENGREP

    @property
    def supported_languages(self) -> Set[str]:
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_extensions(self) -> Set[str]:
        return self.SUPPORTED_EXTENSIONS

    @property
    def sarif_output_args(self) -> List[str]:
        return ["--sarif"]

    def build_command(
        self,
        target_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build opengrep/semgrep command."""
        cmd = [self.binary_name]

        # Output format
        cmd.extend(["--sarif", "--output", str(output_path)])

        # Config file
        if self.config_file and self.config_file.exists():
            cmd.extend(["--config", str(self.config_file)])
        elif self.rules_path and self.rules_path.exists():
            cmd.extend(["--config", str(self.rules_path)])
        else:
            # Use built-in security rules
            cmd.extend(["--config", "auto"])

        # Additional config from parameters
        if config:
            # Severity filter
            if "severity" in config:
                cmd.extend(["--severity", config["severity"]])

            # Exclude patterns
            if "exclude" in config:
                for pattern in config["exclude"]:
                    cmd.extend(["--exclude", pattern])

            # Include patterns
            if "include" in config:
                for pattern in config["include"]:
                    cmd.extend(["--include", pattern])

            # Max target bytes (for large files)
            if "max_target_bytes" in config:
                cmd.extend(["--max-target-bytes", str(config["max_target_bytes"])])

            # Timeout per file
            if "timeout" in config:
                cmd.extend(["--timeout", str(config["timeout"])])

            # Jobs (parallelism)
            if "jobs" in config:
                cmd.extend(["--jobs", str(config["jobs"])])

            # Specific rules
            if "rules" in config:
                for rule in config["rules"]:
                    cmd.extend(["--config", rule])

        # Don't fail on findings (we parse them)
        cmd.append("--no-error")

        # Target path
        cmd.append(str(target_path))

        return cmd

    def get_available_rulesets(self) -> List[str]:
        """
        Get list of available built-in rulesets.

        These can be passed to --config.
        """
        return [
            "auto",  # Auto-detect appropriate rules
            "p/security-audit",  # Security audit rules
            "p/owasp-top-ten",  # OWASP Top 10
            "p/cwe-top-25",  # CWE Top 25
            "p/secrets",  # Secret detection
            "p/ci",  # CI-friendly rules
            "p/default",  # Default ruleset
            # Language-specific
            "p/python",
            "p/javascript",
            "p/typescript",
            "p/java",
            "p/go",
            "p/ruby",
            "p/php",
            "p/csharp",
            "p/rust",
            "p/kotlin",
            "p/swift",
            # Framework-specific
            "p/react",
            "p/django",
            "p/flask",
            "p/express",
            "p/spring",
            "p/rails",
            "p/laravel",
            "p/nodejs",
            # Security-specific
            "p/sql-injection",
            "p/xss",
            "p/command-injection",
        ]


def create_opengrep_adapter(
    rules_path: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> OpenGrepAdapter:
    """Factory function to create OpenGrep adapter."""
    return OpenGrepAdapter(rules_path=rules_path, config_file=config_file)
