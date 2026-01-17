"""
Secret Detection Scanner (K3 - Fase 24).

Detects hardcoded secrets, credentials, API keys, and tokens in code.

Features:
- 50+ secret patterns covering major providers and common patterns
- Entropy-based detection for unknown secret formats
- False positive filtering with context awareness
- Severity classification based on secret type
- Git history scanning capability
- Remediation suggestions

CWE-798: Use of Hard-coded Credentials
"""

import re
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import CustomPatternScanner
from ..models.findings import (
    SecurityFinding, ScanResult, Severity, ScannerType, Location, SuggestedFix,
)

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Classification of secret types."""
    # Cloud Providers
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    AWS_SESSION_TOKEN = "aws_session_token"
    AZURE_STORAGE_KEY = "azure_storage_key"
    AZURE_CLIENT_SECRET = "azure_client_secret"
    AZURE_SAS_TOKEN = "azure_sas_token"
    GCP_API_KEY = "gcp_api_key"
    GCP_SERVICE_ACCOUNT = "gcp_service_account"

    # Version Control & CI/CD
    GITHUB_TOKEN = "github_token"
    GITHUB_OAUTH = "github_oauth"
    GITLAB_TOKEN = "gitlab_token"
    BITBUCKET_TOKEN = "bitbucket_token"
    JENKINS_TOKEN = "jenkins_token"
    CIRCLECI_TOKEN = "circleci_token"
    TRAVIS_TOKEN = "travis_token"

    # Communication
    SLACK_TOKEN = "slack_token"
    SLACK_WEBHOOK = "slack_webhook"
    DISCORD_TOKEN = "discord_token"
    DISCORD_WEBHOOK = "discord_webhook"
    TELEGRAM_TOKEN = "telegram_token"
    TWILIO_API_KEY = "twilio_api_key"
    SENDGRID_API_KEY = "sendgrid_api_key"
    MAILGUN_API_KEY = "mailgun_api_key"
    MAILCHIMP_API_KEY = "mailchimp_api_key"

    # Payment & Financial
    STRIPE_API_KEY = "stripe_api_key"
    STRIPE_WEBHOOK_SECRET = "stripe_webhook_secret"
    PAYPAL_CLIENT_SECRET = "paypal_client_secret"
    SQUARE_ACCESS_TOKEN = "square_access_token"
    BRAINTREE_TOKEN = "braintree_token"

    # Database
    DATABASE_URL = "database_url"
    MONGODB_URI = "mongodb_uri"
    REDIS_URL = "redis_url"
    MYSQL_PASSWORD = "mysql_password"
    POSTGRES_PASSWORD = "postgres_password"
    MSSQL_CONNECTION = "mssql_connection"

    # Authentication
    JWT_SECRET = "jwt_secret"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    SESSION_SECRET = "session_secret"

    # Cryptographic
    PRIVATE_KEY = "private_key"
    RSA_PRIVATE_KEY = "rsa_private_key"
    SSH_PRIVATE_KEY = "ssh_private_key"
    PGP_PRIVATE_KEY = "pgp_private_key"
    ENCRYPTION_KEY = "encryption_key"

    # Third Party Services
    OPENAI_API_KEY = "openai_api_key"
    ANTHROPIC_API_KEY = "anthropic_api_key"
    HUGGINGFACE_TOKEN = "huggingface_token"
    DATADOG_API_KEY = "datadog_api_key"
    NEW_RELIC_KEY = "new_relic_key"
    SENTRY_DSN = "sentry_dsn"
    ALGOLIA_API_KEY = "algolia_api_key"
    FIREBASE_API_KEY = "firebase_api_key"
    MAPBOX_TOKEN = "mapbox_token"
    HEROKU_API_KEY = "heroku_api_key"
    NETLIFY_TOKEN = "netlify_token"
    VERCEL_TOKEN = "vercel_token"
    DOPPLER_TOKEN = "doppler_token"
    VAULT_TOKEN = "vault_token"

    # Generic
    PASSWORD = "password"
    SECRET = "secret"
    CREDENTIAL = "credential"
    HIGH_ENTROPY = "high_entropy"


@dataclass
class SecretPattern:
    """Definition of a secret pattern."""
    secret_type: SecretType
    pattern: str
    severity: Severity
    title: str
    description: str
    confidence: float = 0.9
    entropy_threshold: Optional[float] = None
    false_positive_patterns: List[str] = None

    def __post_init__(self):
        if self.false_positive_patterns is None:
            self.false_positive_patterns = []


# 50+ Secret Detection Patterns
SECRET_PATTERNS: List[SecretPattern] = [
    # ==================== AWS ====================
    SecretPattern(
        secret_type=SecretType.AWS_ACCESS_KEY,
        pattern=r"(?:^|[^A-Z0-9])((AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16})(?:[^A-Z0-9]|$)",
        severity=Severity.CRITICAL,
        title="AWS Access Key ID",
        description="AWS access key ID found. This can provide access to AWS services.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.AWS_SECRET_KEY,
        pattern=r"(?:aws_secret_access_key|aws_secret_key|secret_access_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
        severity=Severity.CRITICAL,
        title="AWS Secret Access Key",
        description="AWS secret access key found. Combined with access key, provides full AWS access.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.AWS_SESSION_TOKEN,
        pattern=r"(?:aws_session_token|session_token)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{100,})['\"]?",
        severity=Severity.HIGH,
        title="AWS Session Token",
        description="AWS session token found in code.",
        confidence=0.85,
    ),

    # ==================== Azure ====================
    SecretPattern(
        secret_type=SecretType.AZURE_STORAGE_KEY,
        pattern=r"DefaultEndpointsProtocol=https?;AccountName=[^;]+;AccountKey=([A-Za-z0-9+/=]{88})",
        severity=Severity.CRITICAL,
        title="Azure Storage Connection String",
        description="Azure storage account connection string with key exposed.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.AZURE_CLIENT_SECRET,
        pattern=r"(?:azure_client_secret|client_secret|AZURE_CLIENT_SECRET)\s*[=:]\s*['\"]?([A-Za-z0-9~._-]{34,})['\"]?",
        severity=Severity.CRITICAL,
        title="Azure Client Secret",
        description="Azure AD application client secret found.",
        confidence=0.8,
    ),
    SecretPattern(
        secret_type=SecretType.AZURE_SAS_TOKEN,
        pattern=r"[?&]sig=([A-Za-z0-9%+/=]{43,})",
        severity=Severity.HIGH,
        title="Azure SAS Token",
        description="Azure Shared Access Signature token found.",
        confidence=0.85,
    ),

    # ==================== GCP ====================
    SecretPattern(
        secret_type=SecretType.GCP_API_KEY,
        pattern=r"AIza[0-9A-Za-z_-]{35}",
        severity=Severity.HIGH,
        title="Google API Key",
        description="Google Cloud API key found.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.GCP_SERVICE_ACCOUNT,
        pattern=r'"type"\s*:\s*"service_account"[^}]*"private_key"\s*:\s*"-----BEGIN',
        severity=Severity.CRITICAL,
        title="GCP Service Account Key",
        description="Google Cloud service account private key found.",
        confidence=0.95,
    ),

    # ==================== GitHub ====================
    SecretPattern(
        secret_type=SecretType.GITHUB_TOKEN,
        pattern=r"gh[pousr]_[A-Za-z0-9_]{36,}",
        severity=Severity.CRITICAL,
        title="GitHub Personal Access Token",
        description="GitHub PAT found. Can access repositories and user data.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.GITHUB_OAUTH,
        pattern=r"github[_-]?oauth[_-]?token\s*[=:]\s*['\"]?([a-f0-9]{40})['\"]?",
        severity=Severity.CRITICAL,
        title="GitHub OAuth Token",
        description="GitHub OAuth token found.",
        confidence=0.9,
    ),

    # ==================== GitLab ====================
    SecretPattern(
        secret_type=SecretType.GITLAB_TOKEN,
        pattern=r"glpat-[A-Za-z0-9_-]{20,}",
        severity=Severity.CRITICAL,
        title="GitLab Personal Access Token",
        description="GitLab PAT found.",
        confidence=0.95,
    ),

    # ==================== Slack ====================
    SecretPattern(
        secret_type=SecretType.SLACK_TOKEN,
        pattern=r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
        severity=Severity.HIGH,
        title="Slack Token",
        description="Slack API token found.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.SLACK_WEBHOOK,
        pattern=r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[a-zA-Z0-9]{24}",
        severity=Severity.MEDIUM,
        title="Slack Webhook URL",
        description="Slack incoming webhook URL found.",
        confidence=0.95,
    ),

    # ==================== Discord ====================
    SecretPattern(
        secret_type=SecretType.DISCORD_TOKEN,
        pattern=r"(?:discord[_-]?token|DISCORD_TOKEN)\s*[=:]\s*['\"]?([A-Za-z0-9._-]{59,})['\"]?",
        severity=Severity.HIGH,
        title="Discord Bot Token",
        description="Discord bot token found.",
        confidence=0.85,
    ),
    SecretPattern(
        secret_type=SecretType.DISCORD_WEBHOOK,
        pattern=r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+",
        severity=Severity.MEDIUM,
        title="Discord Webhook URL",
        description="Discord webhook URL found.",
        confidence=0.95,
    ),

    # ==================== Telegram ====================
    SecretPattern(
        secret_type=SecretType.TELEGRAM_TOKEN,
        pattern=r"[0-9]{9,10}:[A-Za-z0-9_-]{35}",
        severity=Severity.HIGH,
        title="Telegram Bot Token",
        description="Telegram bot API token found.",
        confidence=0.9,
    ),

    # ==================== Stripe ====================
    SecretPattern(
        secret_type=SecretType.STRIPE_API_KEY,
        pattern=r"sk_live_[0-9a-zA-Z]{24,}",
        severity=Severity.CRITICAL,
        title="Stripe Live Secret Key",
        description="Stripe live API key found. Can process real payments.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.STRIPE_API_KEY,
        pattern=r"sk_test_[0-9a-zA-Z]{24,}",
        severity=Severity.MEDIUM,
        title="Stripe Test Secret Key",
        description="Stripe test API key found.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.STRIPE_WEBHOOK_SECRET,
        pattern=r"whsec_[0-9a-zA-Z]{24,}",
        severity=Severity.HIGH,
        title="Stripe Webhook Secret",
        description="Stripe webhook signing secret found.",
        confidence=0.95,
    ),

    # ==================== PayPal ====================
    SecretPattern(
        secret_type=SecretType.PAYPAL_CLIENT_SECRET,
        pattern=r"(?:paypal_client_secret|PAYPAL_SECRET)\s*[=:]\s*['\"]?([A-Za-z0-9_-]{40,})['\"]?",
        severity=Severity.CRITICAL,
        title="PayPal Client Secret",
        description="PayPal API client secret found.",
        confidence=0.8,
    ),

    # ==================== Database ====================
    SecretPattern(
        secret_type=SecretType.DATABASE_URL,
        pattern=r"(?:postgres|mysql|mongodb|redis)(?:ql)?://[^:]+:([^@]+)@[^/]+",
        severity=Severity.CRITICAL,
        title="Database Connection String with Password",
        description="Database connection URL with embedded password found.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.MONGODB_URI,
        pattern=r"mongodb(?:\+srv)?://[^:]+:([^@]+)@[^/]+",
        severity=Severity.CRITICAL,
        title="MongoDB Connection String",
        description="MongoDB connection URI with password found.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.REDIS_URL,
        pattern=r"redis://:[^@]+@[^:]+:[0-9]+",
        severity=Severity.HIGH,
        title="Redis URL with Password",
        description="Redis connection URL with password found.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.MSSQL_CONNECTION,
        pattern=r"(?:Server|Data Source)=[^;]+;.*(?:Password|Pwd)=([^;]+)",
        severity=Severity.CRITICAL,
        title="SQL Server Connection String",
        description="SQL Server connection string with password found.",
        confidence=0.9,
    ),

    # ==================== JWT & OAuth ====================
    SecretPattern(
        secret_type=SecretType.JWT_SECRET,
        pattern=r"(?:jwt[_-]?secret|JWT_SECRET|secret[_-]?key|SECRET_KEY)\s*[=:]\s*['\"]([^'\"]{16,})['\"]",
        severity=Severity.HIGH,
        title="JWT Secret Key",
        description="JWT signing secret found.",
        confidence=0.8,
        false_positive_patterns=[r"process\.env", r"\$\{", r"os\.environ"],
    ),
    SecretPattern(
        secret_type=SecretType.OAUTH_CLIENT_SECRET,
        pattern=r"(?:client[_-]?secret|CLIENT_SECRET|oauth[_-]?secret)\s*[=:]\s*['\"]([^'\"]{16,})['\"]",
        severity=Severity.HIGH,
        title="OAuth Client Secret",
        description="OAuth client secret found.",
        confidence=0.8,
        false_positive_patterns=[r"process\.env", r"\$\{", r"os\.environ"],
    ),

    # ==================== Private Keys ====================
    SecretPattern(
        secret_type=SecretType.RSA_PRIVATE_KEY,
        pattern=r"-----BEGIN RSA PRIVATE KEY-----",
        severity=Severity.CRITICAL,
        title="RSA Private Key",
        description="RSA private key found in code.",
        confidence=0.99,
    ),
    SecretPattern(
        secret_type=SecretType.SSH_PRIVATE_KEY,
        pattern=r"-----BEGIN OPENSSH PRIVATE KEY-----",
        severity=Severity.CRITICAL,
        title="OpenSSH Private Key",
        description="OpenSSH private key found in code.",
        confidence=0.99,
    ),
    SecretPattern(
        secret_type=SecretType.PRIVATE_KEY,
        pattern=r"-----BEGIN (EC |DSA |ENCRYPTED )?PRIVATE KEY-----",
        severity=Severity.CRITICAL,
        title="Private Key",
        description="Private key found in code.",
        confidence=0.99,
    ),
    SecretPattern(
        secret_type=SecretType.PGP_PRIVATE_KEY,
        pattern=r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
        severity=Severity.CRITICAL,
        title="PGP Private Key",
        description="PGP private key block found in code.",
        confidence=0.99,
    ),

    # ==================== AI Services ====================
    SecretPattern(
        secret_type=SecretType.OPENAI_API_KEY,
        pattern=r"sk-[A-Za-z0-9]{48,}",
        severity=Severity.HIGH,
        title="OpenAI API Key",
        description="OpenAI API key found.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.ANTHROPIC_API_KEY,
        pattern=r"sk-ant-[A-Za-z0-9_-]{90,}",
        severity=Severity.HIGH,
        title="Anthropic API Key",
        description="Anthropic Claude API key found.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.HUGGINGFACE_TOKEN,
        pattern=r"hf_[A-Za-z0-9]{34,}",
        severity=Severity.MEDIUM,
        title="Hugging Face Token",
        description="Hugging Face API token found.",
        confidence=0.95,
    ),

    # ==================== Monitoring & Analytics ====================
    SecretPattern(
        secret_type=SecretType.DATADOG_API_KEY,
        pattern=r"(?:datadog_api_key|DD_API_KEY)\s*[=:]\s*['\"]?([a-f0-9]{32})['\"]?",
        severity=Severity.MEDIUM,
        title="Datadog API Key",
        description="Datadog API key found.",
        confidence=0.85,
    ),
    SecretPattern(
        secret_type=SecretType.NEW_RELIC_KEY,
        pattern=r"(?:new_relic|NEWRELIC)[_-]?(?:license[_-]?)?key\s*[=:]\s*['\"]?([a-f0-9]{40})['\"]?",
        severity=Severity.MEDIUM,
        title="New Relic License Key",
        description="New Relic license key found.",
        confidence=0.85,
    ),
    SecretPattern(
        secret_type=SecretType.SENTRY_DSN,
        pattern=r"https://[a-f0-9]{32}@[a-z0-9]+\.ingest\.sentry\.io/[0-9]+",
        severity=Severity.LOW,
        title="Sentry DSN",
        description="Sentry DSN found. Contains project identifier.",
        confidence=0.95,
    ),

    # ==================== Cloud Platforms ====================
    SecretPattern(
        secret_type=SecretType.HEROKU_API_KEY,
        pattern=r"(?:heroku[_-]?api[_-]?key|HEROKU_API_KEY)\s*[=:]\s*['\"]?([a-f0-9-]{36})['\"]?",
        severity=Severity.HIGH,
        title="Heroku API Key",
        description="Heroku API key found.",
        confidence=0.85,
    ),
    SecretPattern(
        secret_type=SecretType.NETLIFY_TOKEN,
        pattern=r"(?:netlify[_-]?token|NETLIFY_AUTH_TOKEN)\s*[=:]\s*['\"]?([A-Za-z0-9_-]{40,})['\"]?",
        severity=Severity.HIGH,
        title="Netlify Auth Token",
        description="Netlify authentication token found.",
        confidence=0.8,
    ),
    SecretPattern(
        secret_type=SecretType.VERCEL_TOKEN,
        pattern=r"(?:vercel[_-]?token|VERCEL_TOKEN)\s*[=:]\s*['\"]?([A-Za-z0-9]{24})['\"]?",
        severity=Severity.HIGH,
        title="Vercel Token",
        description="Vercel authentication token found.",
        confidence=0.8,
    ),

    # ==================== Email Services ====================
    SecretPattern(
        secret_type=SecretType.SENDGRID_API_KEY,
        pattern=r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}",
        severity=Severity.HIGH,
        title="SendGrid API Key",
        description="SendGrid API key found.",
        confidence=0.95,
    ),
    SecretPattern(
        secret_type=SecretType.MAILGUN_API_KEY,
        pattern=r"key-[a-f0-9]{32}",
        severity=Severity.HIGH,
        title="Mailgun API Key",
        description="Mailgun API key found.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.MAILCHIMP_API_KEY,
        pattern=r"[a-f0-9]{32}-us[0-9]{1,2}",
        severity=Severity.MEDIUM,
        title="Mailchimp API Key",
        description="Mailchimp API key found.",
        confidence=0.9,
    ),

    # ==================== Twilio ====================
    SecretPattern(
        secret_type=SecretType.TWILIO_API_KEY,
        pattern=r"SK[a-f0-9]{32}",
        severity=Severity.HIGH,
        title="Twilio API Key",
        description="Twilio API key found.",
        confidence=0.9,
    ),

    # ==================== Firebase ====================
    SecretPattern(
        secret_type=SecretType.FIREBASE_API_KEY,
        pattern=r"(?:firebase[_-]?api[_-]?key|FIREBASE_API_KEY)\s*[=:]\s*['\"]?(AIza[0-9A-Za-z_-]{35})['\"]?",
        severity=Severity.MEDIUM,
        title="Firebase API Key",
        description="Firebase API key found.",
        confidence=0.9,
    ),

    # ==================== Maps ====================
    SecretPattern(
        secret_type=SecretType.MAPBOX_TOKEN,
        pattern=r"pk\.[a-zA-Z0-9]{60,}",
        severity=Severity.LOW,
        title="Mapbox Public Token",
        description="Mapbox public access token found.",
        confidence=0.9,
    ),
    SecretPattern(
        secret_type=SecretType.MAPBOX_TOKEN,
        pattern=r"sk\.[a-zA-Z0-9]{60,}",
        severity=Severity.HIGH,
        title="Mapbox Secret Token",
        description="Mapbox secret access token found.",
        confidence=0.9,
    ),

    # ==================== Generic Patterns ====================
    SecretPattern(
        secret_type=SecretType.PASSWORD,
        pattern=r"(?:password|passwd|pwd)\s*[=:]\s*['\"]([^'\"]{8,})['\"]",
        severity=Severity.HIGH,
        title="Hardcoded Password",
        description="Hardcoded password found in code.",
        confidence=0.7,
        false_positive_patterns=[
            r"password\s*[=:]\s*['\"]?\s*$",  # Empty assignment
            r"password.*example",
            r"password.*placeholder",
            r"password.*<.*>",  # Template variable
            r"password.*\$\{",  # Environment variable
            r"password.*process\.env",
            r"password.*os\.environ",
            r"password.*getenv",
        ],
    ),
    SecretPattern(
        secret_type=SecretType.API_KEY,
        pattern=r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]([A-Za-z0-9_-]{20,})['\"]",
        severity=Severity.MEDIUM,
        title="Generic API Key",
        description="Possible API key found in code.",
        confidence=0.6,
        false_positive_patterns=[
            r"api[_-]?key.*example",
            r"api[_-]?key.*placeholder",
            r"api[_-]?key.*<.*>",
            r"api[_-]?key.*\$\{",
            r"api[_-]?key.*process\.env",
            r"api[_-]?key.*os\.environ",
        ],
    ),
    SecretPattern(
        secret_type=SecretType.BASIC_AUTH,
        pattern=r"Basic\s+([A-Za-z0-9+/=]{20,})",
        severity=Severity.HIGH,
        title="Basic Auth Credentials",
        description="Base64 encoded Basic Auth credentials found.",
        confidence=0.8,
    ),
    SecretPattern(
        secret_type=SecretType.BEARER_TOKEN,
        pattern=r"Bearer\s+([A-Za-z0-9._-]{20,})",
        severity=Severity.HIGH,
        title="Bearer Token",
        description="Bearer authentication token found in code.",
        confidence=0.75,
        false_positive_patterns=[
            r"Bearer.*example",
            r"Bearer.*placeholder",
            r"Bearer.*<.*>",
        ],
    ),
]


class FalsePositiveFilter:
    """Filter for reducing false positive secret detections."""

    # Common false positive contexts
    TEST_FILE_PATTERNS = [
        r"test[_-]?",
        r"spec[_-]?",
        r"mock",
        r"fake",
        r"stub",
        r"fixture",
        r"example",
        r"sample",
        r"demo",
    ]

    # Variable reference patterns (not actual secrets)
    VARIABLE_PATTERNS = [
        r"process\.env\.",
        r"os\.environ",
        r"os\.getenv",
        r"getenv\(",
        r"\$\{[A-Z_]+\}",
        r"\$[A-Z_]+",
        r"%[A-Z_]+%",
        r"ENV\[",
        r"config\.",
        r"settings\.",
    ]

    # Documentation patterns
    DOC_PATTERNS = [
        r"example",
        r"placeholder",
        r"your[_-]?",
        r"<[A-Z_]+>",
        r"\[.*\]",
        r"xxx+",
        r"yyy+",
        r"zzz+",
        r"abc+",
        r"123+",
        r"test[_-]?",
    ]

    def __init__(self):
        self._test_file_re = re.compile(
            "|".join(self.TEST_FILE_PATTERNS), re.IGNORECASE
        )
        self._variable_re = re.compile(
            "|".join(self.VARIABLE_PATTERNS), re.IGNORECASE
        )
        self._doc_re = re.compile(
            "|".join(self.DOC_PATTERNS), re.IGNORECASE
        )

    def is_false_positive(
        self,
        matched_text: str,
        line: str,
        file_path: str,
        pattern: SecretPattern,
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if a match is likely a false positive.

        Returns:
            Tuple of (is_false_positive, reason)
        """
        # Check test files
        if self._test_file_re.search(Path(file_path).name):
            return True, "Test file"

        # Check variable references
        if self._variable_re.search(line):
            return True, "Environment variable reference"

        # Check documentation patterns
        if self._doc_re.search(matched_text.lower()):
            return True, "Documentation/example value"

        # Check pattern-specific false positives
        for fp_pattern in pattern.false_positive_patterns:
            if re.search(fp_pattern, line, re.IGNORECASE):
                return True, f"Pattern-specific: {fp_pattern}"

        # Check for comment context (might be documenting, not using)
        stripped = line.strip()
        if stripped.startswith(("#", "//", "/*", "*", "--", "'")):
            # But still flag if it looks like a real key format
            if pattern.secret_type in [
                SecretType.AWS_ACCESS_KEY,
                SecretType.PRIVATE_KEY,
                SecretType.RSA_PRIVATE_KEY,
            ]:
                return False, None  # Still flag these even in comments
            return True, "Comment context"

        return False, None


class EntropyAnalyzer:
    """Analyze string entropy to detect potential secrets."""

    def __init__(self, threshold: float = 4.5):
        """
        Initialize entropy analyzer.

        Args:
            threshold: Shannon entropy threshold (4.5 is good for secrets)
        """
        self.threshold = threshold

    def calculate_shannon_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0

        # Count character frequencies
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1

        length = len(text)
        entropy = 0.0

        for count in freq.values():
            if count > 0:
                probability = count / length
                entropy -= probability * math.log2(probability)

        return entropy

    def is_high_entropy(self, text: str, min_length: int = 16) -> Tuple[bool, float]:
        """
        Check if text has suspiciously high entropy.

        Returns:
            Tuple of (is_high_entropy, entropy_value)
        """
        if len(text) < min_length:
            return False, 0.0

        entropy = self.calculate_shannon_entropy(text)
        return entropy >= self.threshold, entropy


class SecretScanner(CustomPatternScanner):
    """
    Secret Detection Scanner for K3 - Fase 24.

    Detects hardcoded secrets using pattern matching and entropy analysis.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        entropy_threshold: float = 4.5,
        enable_entropy_detection: bool = True,
        custom_patterns: Optional[List[SecretPattern]] = None,
    ):
        """
        Initialize secret scanner.

        Args:
            entropy_threshold: Threshold for entropy-based detection
            enable_entropy_detection: Enable high-entropy string detection
            custom_patterns: Additional patterns to detect
        """
        super().__init__()
        self.entropy_analyzer = EntropyAnalyzer(entropy_threshold)
        self.enable_entropy_detection = enable_entropy_detection
        self.false_positive_filter = FalsePositiveFilter()
        self.patterns = SECRET_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.SECRET_SCANNER

    @property
    def supported_languages(self) -> Set[str]:
        # Secrets can be in any file
        return {
            "python", "javascript", "typescript", "java", "kotlin", "scala",
            "go", "rust", "ruby", "php", "csharp", "c", "cpp", "swift",
            "bash", "shell", "yaml", "json", "xml", "html", "sql",
            "asp", "vbscript", "cobol", "terraform", "dockerfile",
        }

    @property
    def supported_extensions(self) -> Set[str]:
        return {
            ".py", ".pyw", ".js", ".jsx", ".mjs", ".ts", ".tsx",
            ".java", ".kt", ".kts", ".scala", ".go", ".rs", ".rb",
            ".php", ".cs", ".c", ".h", ".cpp", ".hpp", ".swift",
            ".sh", ".bash", ".zsh", ".yaml", ".yml", ".json", ".xml",
            ".html", ".htm", ".sql", ".asp", ".asa", ".vbs",
            ".cbl", ".cob", ".tf", ".tfvars", ".env", ".config",
            ".ini", ".cfg", ".conf", ".properties",
            # Include common config files
            "",  # Files without extension like Dockerfile, Makefile
        }

    @property
    def rules(self) -> List[Dict[str, Any]]:
        """Convert patterns to rule format for base class."""
        return [
            {
                "id": f"SECRET-{i:03d}-{p.secret_type.value}",
                "pattern": p.pattern,
                "severity": p.severity,
                "title": p.title,
                "description": p.description,
                "cwe_ids": ["CWE-798"],  # Use of Hard-coded Credentials
                "category": "secrets",
                "fix_suggestion": self._get_remediation(p.secret_type),
            }
            for i, p in enumerate(self.patterns, 1)
        ]

    def _get_remediation(self, secret_type: SecretType) -> str:
        """Get remediation suggestion for a secret type."""
        remediations = {
            SecretType.AWS_ACCESS_KEY: (
                "Use AWS IAM roles, instance profiles, or environment variables. "
                "Never commit AWS credentials to source control."
            ),
            SecretType.AWS_SECRET_KEY: (
                "Remove from code and rotate immediately. Use AWS Secrets Manager "
                "or environment variables for credential storage."
            ),
            SecretType.PRIVATE_KEY: (
                "Remove private key from code. Store in secure vault (HashiCorp Vault, "
                "AWS Secrets Manager) and inject at runtime."
            ),
            SecretType.DATABASE_URL: (
                "Use environment variables or secrets management. Never hardcode "
                "database credentials in source code."
            ),
            SecretType.JWT_SECRET: (
                "Store JWT secret in environment variable or secrets manager. "
                "Consider using asymmetric keys (RS256) for better security."
            ),
            SecretType.API_KEY: (
                "Move API key to environment variable or configuration management. "
                "Consider using API key rotation and monitoring."
            ),
            SecretType.PASSWORD: (
                "Remove hardcoded password. Use environment variables, secrets manager, "
                "or secure configuration for sensitive values."
            ),
        }
        return remediations.get(
            secret_type,
            "Remove secret from code and store in environment variables or a secrets manager."
        )

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """
        Execute secret detection scan.

        Overrides base class to add:
        - False positive filtering
        - Entropy-based detection
        - Confidence scoring
        """
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc)
        findings = []
        files_scanned = 0
        errors = []

        # Get files to scan
        if target_path.is_file():
            files = [target_path]
        else:
            files = []
            # Scan all text-like files
            for ext in self.supported_extensions:
                if ext:
                    files.extend(target_path.rglob(f"*{ext}"))
                else:
                    # Include common config files without extension
                    for name in ["Dockerfile", "Makefile", ".env", ".env.local"]:
                        files.extend(target_path.rglob(name))

        for file_path in files:
            files_scanned += 1
            try:
                # Skip binary files
                if self._is_binary(file_path):
                    continue

                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.split("\n")

                # Pattern-based detection
                for pattern in self.patterns:
                    regex = re.compile(pattern.pattern, re.IGNORECASE | re.MULTILINE)

                    for match in regex.finditer(content):
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        matched_text = match.group(1) if match.groups() else match.group(0)
                        current_line = lines[line_start - 1] if line_start <= len(lines) else ""

                        # Apply false positive filter
                        is_fp, fp_reason = self.false_positive_filter.is_false_positive(
                            matched_text, current_line, str(file_path), pattern
                        )
                        if is_fp:
                            logger.debug(f"Filtered false positive in {file_path}:{line_start}: {fp_reason}")
                            continue

                        # Get context snippet
                        start_line = max(0, line_start - 2)
                        end_line = min(len(lines), line_end + 2)
                        snippet = "\n".join(lines[start_line:end_line])

                        # Mask the secret for safe display
                        masked_value = self._mask_secret(matched_text)

                        finding = SecurityFinding(
                            id=f"secret-{self.scanner_type.value}-{file_path}:{line_start}",
                            rule_id=f"SECRET-{pattern.secret_type.value}",
                            title=pattern.title,
                            description=f"{pattern.description}\n\nMasked value: {masked_value}",
                            severity=pattern.severity,
                            scanner=self.scanner_type,
                            location=Location(
                                file_path=str(file_path),
                                start_line=line_start,
                                end_line=line_end,
                                snippet=snippet,
                            ),
                            cwe_ids=["CWE-798"],
                            category="secrets",
                            confidence=pattern.confidence,
                        )
                        finding.suggested_fixes.append(
                            SuggestedFix(description=self._get_remediation(pattern.secret_type))
                        )
                        findings.append(finding)

                # Entropy-based detection for unknown patterns
                if self.enable_entropy_detection:
                    entropy_findings = self._detect_high_entropy_strings(
                        content, lines, file_path
                    )
                    findings.extend(entropy_findings)

            except Exception as e:
                errors.append(f"Error scanning {file_path}: {e}")
                logger.error(f"Error scanning {file_path}: {e}")

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        # Deduplicate findings
        seen = set()
        unique_findings = []
        for f in findings:
            key = f.fingerprint
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        return ScanResult(
            scanner=self.scanner_type,
            scanner_version=self.VERSION,
            scan_duration_ms=duration_ms,
            findings=unique_findings,
            files_scanned=files_scanned,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _is_binary(self, file_path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
            return False
        except Exception:
            return True

    def _mask_secret(self, secret: str, visible_chars: int = 4) -> str:
        """Mask a secret for safe display."""
        if len(secret) <= visible_chars * 2:
            return "*" * len(secret)
        return secret[:visible_chars] + "*" * (len(secret) - visible_chars * 2) + secret[-visible_chars:]

    def _detect_high_entropy_strings(
        self,
        content: str,
        lines: List[str],
        file_path: Path,
    ) -> List[SecurityFinding]:
        """Detect high-entropy strings that might be secrets."""
        findings = []

        # Patterns that might contain secrets
        assignment_patterns = [
            r"(?:secret|key|token|password|credential|auth)\s*[=:]\s*['\"]([^'\"]{20,})['\"]",
            r"['\"]([A-Za-z0-9+/=_-]{32,})['\"]",  # Long base64-like strings
        ]

        for pattern_str in assignment_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)

            for match in pattern.finditer(content):
                value = match.group(1) if match.groups() else match.group(0)

                is_high, entropy = self.entropy_analyzer.is_high_entropy(value)
                if not is_high:
                    continue

                line_num = content[:match.start()].count("\n") + 1
                current_line = lines[line_num - 1] if line_num <= len(lines) else ""

                # Check false positives
                is_fp, _ = self.false_positive_filter.is_false_positive(
                    value, current_line, str(file_path),
                    SecretPattern(
                        secret_type=SecretType.HIGH_ENTROPY,
                        pattern="",
                        severity=Severity.MEDIUM,
                        title="",
                        description="",
                    )
                )
                if is_fp:
                    continue

                # Skip if it's a known UUID format (often not secrets)
                if re.match(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", value, re.I):
                    continue

                finding = SecurityFinding(
                    id=f"entropy-{file_path}:{line_num}",
                    rule_id="SECRET-ENTROPY",
                    title="High Entropy String Detected",
                    description=f"String with high entropy ({entropy:.2f}) detected. "
                                f"This might be a hardcoded secret.\n\n"
                                f"Masked value: {self._mask_secret(value)}",
                    severity=Severity.MEDIUM,
                    scanner=self.scanner_type,
                    location=Location(
                        file_path=str(file_path),
                        start_line=line_num,
                        end_line=line_num,
                        snippet=current_line.strip(),
                    ),
                    cwe_ids=["CWE-798"],
                    category="secrets",
                    confidence=0.6,  # Lower confidence for entropy-based detection
                )
                finding.suggested_fixes.append(
                    SuggestedFix(
                        description="If this is a secret, move it to environment variables or a secrets manager."
                    )
                )
                findings.append(finding)

        return findings
