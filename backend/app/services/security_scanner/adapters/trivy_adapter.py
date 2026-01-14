"""
Trivy Scanner Adapter.

Trivy is a comprehensive security scanner for vulnerabilities,
misconfigurations, and secrets.
Apache 2.0 license - fully open source and extensible.

GitHub: https://github.com/aquasecurity/trivy
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from ..models.findings import ScannerType
from .base import ExternalCLIScanner


class TrivyAdapter(ExternalCLIScanner):
    """
    Adapter for Trivy security scanner.

    Trivy scans for:
    - Vulnerabilities in OS packages and language dependencies
    - Infrastructure as Code (IaC) misconfigurations
    - Secrets and credentials
    - Software Bill of Materials (SBOM)

    Supported package managers:
    - npm, yarn, pnpm (JavaScript)
    - pip, pipenv, poetry (Python)
    - bundler (Ruby)
    - composer (PHP)
    - cargo (Rust)
    - go modules (Go)
    - maven, gradle (Java)
    - nuget (.NET)
    - pub (Dart)
    - mix (Elixir)
    - conan (C/C++)
    - swift (Swift)
    """

    SUPPORTED_LANGUAGES = {
        "javascript", "typescript", "python", "ruby", "php",
        "rust", "go", "java", "kotlin", "scala", "csharp",
        "dart", "elixir", "c", "cpp", "swift",
    }

    # Dependency files Trivy can scan
    SUPPORTED_EXTENSIONS = {
        # JavaScript
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        # Python
        "requirements.txt", "Pipfile.lock", "poetry.lock", "setup.py",
        # Ruby
        "Gemfile.lock", "Gemfile",
        # PHP
        "composer.lock", "composer.json",
        # Rust
        "Cargo.lock", "Cargo.toml",
        # Go
        "go.mod", "go.sum",
        # Java
        "pom.xml", "build.gradle", "build.gradle.kts",
        # .NET
        ".csproj", "packages.config", "packages.lock.json",
        # Dart
        "pubspec.lock", "pubspec.yaml",
        # Elixir
        "mix.lock",
        # C/C++
        "conan.lock",
        # Swift
        "Package.resolved",
        # Docker
        "Dockerfile", ".dockerfile",
        # Terraform
        ".tf",
        # Kubernetes
        ".yaml", ".yml",
    }

    def __init__(self, timeout_seconds: int = 600):
        """Initialize Trivy adapter."""
        super().__init__(binary_name="trivy", timeout_seconds=timeout_seconds)

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.TRIVY

    @property
    def supported_languages(self) -> Set[str]:
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_extensions(self) -> Set[str]:
        return self.SUPPORTED_EXTENSIONS

    @property
    def sarif_output_args(self) -> List[str]:
        return ["--format", "sarif"]

    def supports_file(self, file_path: Path) -> bool:
        """Check if Trivy can scan this file."""
        # Trivy matches on filename, not just extension
        return file_path.name in self.SUPPORTED_EXTENSIONS or \
               file_path.suffix in {".tf", ".yaml", ".yml", ".dockerfile"}

    def build_command(
        self,
        target_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build trivy command."""
        cmd = [self.binary_name]

        # Determine scan type
        scan_type = "fs"  # filesystem scan by default
        if config and "scan_type" in config:
            scan_type = config["scan_type"]

        cmd.append(scan_type)

        # Output format
        cmd.extend(["--format", "sarif", "--output", str(output_path)])

        # Additional config
        if config:
            # Severity filter
            if "severity" in config:
                cmd.extend(["--severity", config["severity"]])

            # Scan specific types
            if "scanners" in config:
                # vuln, misconfig, secret, license
                cmd.extend(["--scanners", ",".join(config["scanners"])])
            else:
                # Default: scan for vulnerabilities and misconfigs
                cmd.extend(["--scanners", "vuln,misconfig,secret"])

            # Skip certain directories
            if "skip_dirs" in config:
                for skip_dir in config["skip_dirs"]:
                    cmd.extend(["--skip-dirs", skip_dir])

            # Skip certain files
            if "skip_files" in config:
                for skip_file in config["skip_files"]:
                    cmd.extend(["--skip-files", skip_file])

            # Ignore unfixed vulnerabilities
            if config.get("ignore_unfixed", False):
                cmd.append("--ignore-unfixed")

            # Include development dependencies
            if config.get("include_dev_deps", False):
                cmd.append("--include-dev-deps")

            # Offline mode (no updates)
            if config.get("offline", False):
                cmd.append("--offline-scan")

            # Config file
            if "config_file" in config:
                cmd.extend(["--config", config["config_file"]])

            # Ignore file
            if "ignore_file" in config:
                cmd.extend(["--ignorefile", config["ignore_file"]])

        # Target path
        cmd.append(str(target_path))

        return cmd

    async def scan_container(
        self,
        image: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Scan a container image.

        Args:
            image: Container image name (e.g., "python:3.9", "myrepo/myimage:tag")
            config: Optional configuration
        """
        import tempfile
        import asyncio
        from datetime import datetime

        started_at = datetime.utcnow()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            cmd = [self.binary_name, "image"]
            cmd.extend(["--format", "sarif", "--output", str(output_path)])

            if config:
                if "severity" in config:
                    cmd.extend(["--severity", config["severity"]])
                if config.get("ignore_unfixed", False):
                    cmd.append("--ignore-unfixed")

            cmd.append(image)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )

            from ..parsers.sarif_parser import SarifParser
            from ..models.findings import ScanResult

            parser = SarifParser(self.scanner_type)
            sarif_log = parser.parse_file(output_path)
            findings = parser.to_security_findings(sarif_log)

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return ScanResult(
                scanner=self.scanner_type,
                scanner_version=self.get_scanner_version(),
                scan_duration_ms=duration_ms,
                findings=findings,
                files_scanned=1,  # One image
                started_at=started_at,
                completed_at=completed_at,
            )

        finally:
            if output_path.exists():
                output_path.unlink()

    def get_scan_types(self) -> Dict[str, str]:
        """Get available scan types."""
        return {
            "fs": "Scan local filesystem (default)",
            "image": "Scan container image",
            "repo": "Scan remote Git repository",
            "rootfs": "Scan rootfs",
            "sbom": "Scan SBOM file",
            "config": "Scan IaC files only",
        }

    def get_available_scanners(self) -> Dict[str, str]:
        """Get available scanner types."""
        return {
            "vuln": "Vulnerability scanning in OS packages and dependencies",
            "misconfig": "Misconfiguration scanning (IaC, Dockerfile, K8s)",
            "secret": "Secret/credential scanning",
            "license": "License scanning",
        }


def create_trivy_adapter() -> TrivyAdapter:
    """Factory function to create Trivy adapter."""
    return TrivyAdapter()
