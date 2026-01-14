"""
Gosec Scanner Adapter.

Gosec is a security scanner for Go code.
Apache 2.0 license - fully open source and extensible.

GitHub: https://github.com/securego/gosec
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from ..models.findings import ScannerType
from .base import ExternalCLIScanner


class GosecAdapter(ExternalCLIScanner):
    """
    Adapter for Gosec Go security scanner.

    Gosec inspects Go source code for security problems:
    - SQL injection
    - Command injection
    - Hardcoded credentials
    - Weak cryptography
    - File path injection
    - Integer overflow
    - Race conditions
    """

    SUPPORTED_LANGUAGES = {"go"}
    SUPPORTED_EXTENSIONS = {".go"}

    # Gosec rule IDs mapped to CWE
    GOSEC_CWE_MAP = {
        "G101": ["CWE-798"],   # Hardcoded credentials
        "G102": ["CWE-1188"],  # Bind to all interfaces
        "G103": ["CWE-242"],   # Audit use of unsafe block
        "G104": ["CWE-703"],   # Audit errors not checked
        "G106": ["CWE-322"],   # Audit use of ssh.InsecureIgnoreHostKey
        "G107": ["CWE-88"],    # URL provided to HTTP request as taint input
        "G108": ["CWE-22"],    # Profiling endpoint enabled
        "G109": ["CWE-190"],   # Integer overflow conversion
        "G110": ["CWE-409"],   # Decompression bomb
        "G111": ["CWE-22"],    # Directory traversal
        "G112": ["CWE-400"],   # Slowloris attack
        "G113": ["CWE-190"],   # Integer overflow
        "G114": ["CWE-1188"],  # Use of net/http default
        "G201": ["CWE-89"],    # SQL injection (format string)
        "G202": ["CWE-89"],    # SQL injection (string concat)
        "G203": ["CWE-79"],    # XSS template
        "G204": ["CWE-78"],    # Subprocess launched with variable
        "G301": ["CWE-276"],   # Poor file permissions (directory)
        "G302": ["CWE-276"],   # Poor file permissions (file)
        "G303": ["CWE-377"],   # Creating tempfile with predictable path
        "G304": ["CWE-22"],    # File path provided as taint input
        "G305": ["CWE-22"],    # File traversal when extracting zip/tar
        "G306": ["CWE-276"],   # Poor file permissions on WriteFile
        "G307": ["CWE-703"],   # Defer close without error check
        "G401": ["CWE-327"],   # Use of weak crypto (DES, MD5, SHA1)
        "G402": ["CWE-295"],   # TLS with InsecureSkipVerify
        "G403": ["CWE-310"],   # RSA keys less than 2048 bits
        "G404": ["CWE-338"],   # Weak random number generator
        "G405": ["CWE-327"],   # Use of DES/3DES
        "G406": ["CWE-327"],   # Use of MD4
        "G501": ["CWE-327"],   # Import crypto/md5
        "G502": ["CWE-327"],   # Import crypto/des
        "G503": ["CWE-327"],   # Import crypto/rc4
        "G504": ["CWE-327"],   # Import net/http/cgi
        "G505": ["CWE-327"],   # Import crypto/sha1
        "G506": ["CWE-327"],   # Import golang.org/x/crypto/md4
        "G507": ["CWE-327"],   # Import golang.org/x/crypto/ripemd160
        "G601": ["CWE-118"],   # Implicit memory aliasing in for loop
        "G602": ["CWE-118"],   # Slice access out of bounds
    }

    def __init__(self, timeout_seconds: int = 300):
        """Initialize Gosec adapter."""
        super().__init__(binary_name="gosec", timeout_seconds=timeout_seconds)

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.GOSEC

    @property
    def supported_languages(self) -> Set[str]:
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_extensions(self) -> Set[str]:
        return self.SUPPORTED_EXTENSIONS

    @property
    def sarif_output_args(self) -> List[str]:
        return ["-fmt", "sarif"]

    def build_command(
        self,
        target_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build gosec command."""
        cmd = [self.binary_name]

        # Output format
        cmd.extend(["-fmt", "sarif", "-out", str(output_path)])

        # Don't fail on findings (we parse them)
        cmd.append("-no-fail")

        # Additional config
        if config:
            # Severity filter
            if "severity" in config:
                cmd.extend(["-severity", config["severity"]])

            # Confidence filter
            if "confidence" in config:
                cmd.extend(["-confidence", config["confidence"]])

            # Exclude rules
            if "exclude" in config:
                cmd.extend(["-exclude", ",".join(config["exclude"])])

            # Include only specific rules
            if "include" in config:
                cmd.extend(["-include", ",".join(config["include"])])

            # Exclude directories
            if "exclude_dir" in config:
                for dir_name in config["exclude_dir"]:
                    cmd.extend(["-exclude-dir", dir_name])

            # Config file
            if "config_file" in config:
                cmd.extend(["-conf", config["config_file"]])

            # Tags for build
            if "tags" in config:
                cmd.extend(["-tags", ",".join(config["tags"])])

            # Concurrency
            if "concurrency" in config:
                cmd.extend(["-concurrency", str(config["concurrency"])])

        # Target path (gosec uses ./... pattern)
        if target_path.is_dir():
            cmd.append(f"{target_path}/...")
        else:
            cmd.append(str(target_path))

        return cmd

    def get_available_rules(self) -> Dict[str, str]:
        """Get list of available Gosec rules."""
        return {
            "G101": "Look for hardcoded credentials",
            "G102": "Bind to all interfaces",
            "G103": "Audit the use of unsafe block",
            "G104": "Audit errors not checked",
            "G106": "Audit the use of ssh.InsecureIgnoreHostKey",
            "G107": "URL provided to HTTP request as taint input",
            "G108": "Profiling endpoint enabled",
            "G109": "Potential Integer overflow made by strconv.Atoi",
            "G110": "Potential DoS via decompression bomb",
            "G111": "Directory traversal",
            "G112": "Potential slowloris attack",
            "G113": "Usage of Rat.SetString with overflow",
            "G114": "Use of net/http serve function",
            "G201": "SQL query construction using format string",
            "G202": "SQL query construction using string concatenation",
            "G203": "Use of unescaped data in HTML templates",
            "G204": "Audit use of command execution",
            "G301": "Poor file permissions used when creating a directory",
            "G302": "Poor file permissions used with chmod",
            "G303": "Creating tempfile using a predictable path",
            "G304": "File path provided as taint input",
            "G305": "File traversal when extracting zip/tar archive",
            "G306": "Poor file permissions used when writing to a new file",
            "G307": "Deferring a method which returns an error",
            "G401": "Detect the usage of weak cryptographic primitives",
            "G402": "Look for bad TLS connection settings",
            "G403": "Ensure minimum RSA key length of 2048 bits",
            "G404": "Insecure random number source (rand)",
            "G405": "Detect use of DES or 3DES",
            "G406": "Detect use of MD4",
            "G501": "Import blocklist: crypto/md5",
            "G502": "Import blocklist: crypto/des",
            "G503": "Import blocklist: crypto/rc4",
            "G504": "Import blocklist: net/http/cgi",
            "G505": "Import blocklist: crypto/sha1",
            "G506": "Import blocklist: golang.org/x/crypto/md4",
            "G507": "Import blocklist: golang.org/x/crypto/ripemd160",
            "G601": "Implicit memory aliasing in for loop",
            "G602": "Slice access out of bounds",
        }


def create_gosec_adapter() -> GosecAdapter:
    """Factory function to create Gosec adapter."""
    return GosecAdapter()
