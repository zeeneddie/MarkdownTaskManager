"""
Bandit Scanner Adapter.

Bandit is a security-focused static analyzer for Python code.
Apache 2.0 license - fully open source and extensible.

GitHub: https://github.com/PyCQA/bandit
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from ..models.findings import ScannerType
from .base import ExternalCLIScanner


class BanditAdapter(ExternalCLIScanner):
    """
    Adapter for Bandit Python security scanner.

    Bandit finds common security issues in Python code:
    - SQL injection
    - Hardcoded passwords
    - Shell injection
    - Weak cryptography
    - Unsafe deserialization
    - And many more...
    """

    SUPPORTED_LANGUAGES = {"python"}
    SUPPORTED_EXTENSIONS = {".py", ".pyw"}

    # Bandit test IDs mapped to CWE
    BANDIT_CWE_MAP = {
        "B101": ["CWE-703"],  # assert_used
        "B102": ["CWE-78"],   # exec_used
        "B103": ["CWE-276"],  # set_bad_file_permissions
        "B104": ["CWE-1188"], # hardcoded_bind_all_interfaces
        "B105": ["CWE-798"],  # hardcoded_password_string
        "B106": ["CWE-798"],  # hardcoded_password_funcarg
        "B107": ["CWE-798"],  # hardcoded_password_default
        "B108": ["CWE-377"],  # hardcoded_tmp_directory
        "B110": ["CWE-703"],  # try_except_pass
        "B112": ["CWE-703"],  # try_except_continue
        "B201": ["CWE-78"],   # flask_debug_true
        "B301": ["CWE-502"],  # pickle
        "B302": ["CWE-502"],  # marshal
        "B303": ["CWE-327"],  # md5
        "B304": ["CWE-327"],  # des
        "B305": ["CWE-327"],  # cipher
        "B306": ["CWE-327"],  # mktemp_q
        "B307": ["CWE-78"],   # eval
        "B308": ["CWE-94"],   # mark_safe
        "B309": ["CWE-295"],  # httpsconnection
        "B310": ["CWE-22"],   # urllib_urlopen
        "B311": ["CWE-330"],  # random
        "B312": ["CWE-295"],  # telnetlib
        "B313": ["CWE-611"],  # xml_bad_cElementTree
        "B314": ["CWE-611"],  # xml_bad_ElementTree
        "B315": ["CWE-611"],  # xml_bad_expatreader
        "B316": ["CWE-611"],  # xml_bad_expatbuilder
        "B317": ["CWE-611"],  # xml_bad_sax
        "B318": ["CWE-611"],  # xml_bad_minidom
        "B319": ["CWE-611"],  # xml_bad_pulldom
        "B320": ["CWE-611"],  # xml_bad_etree
        "B321": ["CWE-295"],  # ftplib
        "B323": ["CWE-295"],  # unverified_context
        "B324": ["CWE-327"],  # hashlib_new_insecure_functions
        "B401": ["CWE-295"],  # import_telnetlib
        "B402": ["CWE-295"],  # import_ftplib
        "B403": ["CWE-502"],  # import_pickle
        "B404": ["CWE-78"],   # import_subprocess
        "B405": ["CWE-611"],  # import_xml_etree
        "B406": ["CWE-611"],  # import_xml_sax
        "B407": ["CWE-611"],  # import_xml_expat
        "B408": ["CWE-611"],  # import_xml_minidom
        "B409": ["CWE-611"],  # import_xml_pulldom
        "B410": ["CWE-611"],  # import_lxml
        "B411": ["CWE-611"],  # import_xmlrpclib
        "B412": ["CWE-295"],  # import_httpoxy
        "B413": ["CWE-327"],  # import_pycrypto
        "B501": ["CWE-295"],  # request_with_no_cert_validation
        "B502": ["CWE-295"],  # ssl_with_bad_version
        "B503": ["CWE-295"],  # ssl_with_bad_defaults
        "B504": ["CWE-295"],  # ssl_with_no_version
        "B505": ["CWE-327"],  # weak_cryptographic_key
        "B506": ["CWE-295"],  # yaml_load
        "B507": ["CWE-295"],  # ssh_no_host_key_verification
        "B601": ["CWE-78"],   # paramiko_calls
        "B602": ["CWE-78"],   # subprocess_popen_with_shell_equals_true
        "B603": ["CWE-78"],   # subprocess_without_shell_equals_true
        "B604": ["CWE-78"],   # any_other_function_with_shell_equals_true
        "B605": ["CWE-78"],   # start_process_with_a_shell
        "B606": ["CWE-78"],   # start_process_with_no_shell
        "B607": ["CWE-78"],   # start_process_with_partial_path
        "B608": ["CWE-89"],   # hardcoded_sql_expressions
        "B609": ["CWE-78"],   # linux_commands_wildcard_injection
        "B610": ["CWE-89"],   # django_extra_used
        "B611": ["CWE-89"],   # django_rawsql_used
        "B701": ["CWE-94"],   # jinja2_autoescape_false
        "B702": ["CWE-79"],   # use_of_mako_templates
        "B703": ["CWE-79"],   # django_mark_safe
    }

    def __init__(self, timeout_seconds: int = 300):
        """Initialize Bandit adapter."""
        super().__init__(binary_name="bandit", timeout_seconds=timeout_seconds)

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.BANDIT

    @property
    def supported_languages(self) -> Set[str]:
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_extensions(self) -> Set[str]:
        return self.SUPPORTED_EXTENSIONS

    @property
    def sarif_output_args(self) -> List[str]:
        return ["-f", "sarif"]

    def build_command(
        self,
        target_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build bandit command."""
        cmd = [self.binary_name]

        # Recursive scan
        cmd.append("-r")

        # Output format and file
        cmd.extend(["-f", "sarif", "-o", str(output_path)])

        # Additional config
        if config:
            # Severity level filter
            if "severity" in config:
                # Bandit uses -l for low, -ll for medium, -lll for high
                level = config["severity"].lower()
                if level == "high":
                    cmd.append("-lll")
                elif level == "medium":
                    cmd.append("-ll")
                elif level == "low":
                    cmd.append("-l")

            # Confidence level filter
            if "confidence" in config:
                level = config["confidence"].lower()
                if level == "high":
                    cmd.append("-iii")
                elif level == "medium":
                    cmd.append("-ii")
                elif level == "low":
                    cmd.append("-i")

            # Skip specific tests
            if "skip" in config:
                cmd.extend(["-s", ",".join(config["skip"])])

            # Run only specific tests
            if "tests" in config:
                cmd.extend(["-t", ",".join(config["tests"])])

            # Exclude paths
            if "exclude" in config:
                cmd.extend(["-x", ",".join(config["exclude"])])

            # Config file
            if "config_file" in config:
                cmd.extend(["-c", config["config_file"]])

            # Baseline file (for suppressing known issues)
            if "baseline" in config:
                cmd.extend(["-b", config["baseline"]])

        # Target path
        cmd.append(str(target_path))

        return cmd

    def get_available_tests(self) -> Dict[str, str]:
        """
        Get list of available Bandit tests.

        Returns dict of test_id -> description
        """
        return {
            "B101": "Test for use of assert",
            "B102": "Test for use of exec",
            "B103": "Test for setting permissive file permissions",
            "B104": "Test for binding to all interfaces",
            "B105": "Test for hardcoded password strings",
            "B106": "Test for hardcoded passwords in function args",
            "B107": "Test for hardcoded password default values",
            "B108": "Test for hardcoded tmp directory",
            "B110": "Test for try/except/pass",
            "B112": "Test for try/except/continue",
            "B301": "Test for pickle use",
            "B302": "Test for marshal use",
            "B303": "Test for MD5 use",
            "B304": "Test for DES use",
            "B305": "Test for cipher use",
            "B306": "Test for mktemp use",
            "B307": "Test for eval use",
            "B308": "Test for mark_safe use (Django)",
            "B310": "Test for URL open",
            "B311": "Test for random use",
            "B312": "Test for telnetlib use",
            "B313-B320": "Tests for XML vulnerabilities",
            "B321": "Test for FTP use",
            "B323": "Test for unverified SSL context",
            "B324": "Test for insecure hash functions",
            "B501": "Test for requests without cert validation",
            "B502": "Test for SSL with bad version",
            "B503": "Test for SSL with bad defaults",
            "B504": "Test for SSL with no version",
            "B505": "Test for weak cryptographic key",
            "B506": "Test for unsafe YAML load",
            "B507": "Test for SSH no host key verification",
            "B601": "Test for paramiko calls",
            "B602": "Test for subprocess with shell=True",
            "B603": "Test for subprocess without shell",
            "B604": "Test for shell functions",
            "B605": "Test for process start with shell",
            "B606": "Test for process start without shell",
            "B607": "Test for process start with partial path",
            "B608": "Test for SQL injection (hardcoded)",
            "B609": "Test for wildcard injection",
            "B610": "Test for Django extra() use",
            "B611": "Test for Django RawSQL use",
            "B701": "Test for Jinja2 autoescape disabled",
            "B702": "Test for Mako templates",
            "B703": "Test for Django mark_safe",
        }


def create_bandit_adapter() -> BanditAdapter:
    """Factory function to create Bandit adapter."""
    return BanditAdapter()
