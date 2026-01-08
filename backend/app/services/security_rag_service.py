"""
Security RAG Service - Week 81

OWASP/CWE knowledge base integration with RAG capabilities.
Provides context-aware security guidance based on vulnerability type,
programming language, and framework.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.ghostcrew import SecurityKnowledge

logger = logging.getLogger(__name__)


# OWASP Top 10 2021 knowledge base
OWASP_TOP_10_2021 = {
    "A01:2021": {
        "name": "Broken Access Control",
        "description": "Access control enforces policy such that users cannot act outside of their intended permissions.",
        "category": "access_control",
        "severity_default": "high",
        "likelihood": "high",
        "impact_description": "Attackers can access unauthorized functionality and data, modify data, or destroy data.",
        "remediation_guidance": """
1. Deny access by default
2. Implement access control mechanisms once and reuse throughout the application
3. Log access control failures and alert administrators
4. Rate limit API and controller access
5. Disable web server directory listing
6. Invalidate JWT tokens on server after logout
""",
        "prevention_techniques": [
            "Implement proper access control at the server side",
            "Use role-based access control (RBAC)",
            "Deny by default except for public resources",
            "Log access control failures",
        ],
        "related_cwes": ["CWE-22", "CWE-23", "CWE-35", "CWE-59", "CWE-200"],
    },
    "A02:2021": {
        "name": "Cryptographic Failures",
        "description": "Failures related to cryptography which often lead to exposure of sensitive data.",
        "category": "crypto",
        "severity_default": "high",
        "likelihood": "medium",
        "impact_description": "Exposure of sensitive data including passwords, credit cards, health records, and business data.",
        "remediation_guidance": """
1. Classify data processed, stored, or transmitted
2. Don't store sensitive data unnecessarily
3. Encrypt all sensitive data at rest
4. Use up-to-date encryption algorithms (AES-256, RSA-2048+)
5. Disable caching for sensitive data
6. Don't use legacy protocols (SSL, TLS 1.0/1.1)
""",
        "prevention_techniques": [
            "Use strong encryption algorithms (AES-256-GCM)",
            "Use proper key management",
            "Store passwords using strong adaptive hashing (bcrypt, scrypt, Argon2)",
            "Don't hardcode secrets",
        ],
        "related_cwes": ["CWE-259", "CWE-327", "CWE-331", "CWE-798"],
    },
    "A03:2021": {
        "name": "Injection",
        "description": "User-supplied data is not validated, filtered, or sanitized by the application.",
        "category": "injection",
        "severity_default": "critical",
        "likelihood": "high",
        "impact_description": "Data theft, data loss, corruption, disclosure, denial of service, or complete host takeover.",
        "remediation_guidance": """
1. Use a safe API with parameterized queries
2. Use positive server-side input validation
3. Escape special characters
4. Use LIMIT and other SQL controls
5. For dynamic queries, escape special characters using interpreter-specific syntax
""",
        "prevention_techniques": [
            "Use parameterized queries/prepared statements",
            "Use ORMs with safe query building",
            "Validate and sanitize all user input",
            "Use allowlist input validation",
        ],
        "related_cwes": ["CWE-77", "CWE-78", "CWE-79", "CWE-89", "CWE-94"],
    },
    "A04:2021": {
        "name": "Insecure Design",
        "description": "Missing or ineffective control design.",
        "category": "design",
        "severity_default": "high",
        "likelihood": "medium",
        "impact_description": "Systemic vulnerabilities that cannot be fixed by perfect implementation.",
        "remediation_guidance": """
1. Use threat modeling for critical applications
2. Integrate security throughout development lifecycle
3. Use secure design patterns
4. Write unit and integration tests for security controls
5. Segregate tenants at all tiers
""",
        "prevention_techniques": [
            "Perform threat modeling",
            "Use secure design patterns and libraries",
            "Integrate security in all phases of SDLC",
            "Establish secure development lifecycle",
        ],
        "related_cwes": ["CWE-209", "CWE-256", "CWE-501", "CWE-522"],
    },
    "A05:2021": {
        "name": "Security Misconfiguration",
        "description": "Missing appropriate security hardening or improperly configured permissions.",
        "category": "config",
        "severity_default": "medium",
        "likelihood": "high",
        "impact_description": "Unauthorized access, system exposure, or complete system compromise.",
        "remediation_guidance": """
1. Remove unnecessary features and frameworks
2. Review and update configurations as part of patch management
3. Implement a repeatable hardening process
4. Segment application architecture
5. Send security directives (e.g., Security Headers)
6. Automate configuration verification
""",
        "prevention_techniques": [
            "Implement minimal platform without unused features",
            "Review and update configurations regularly",
            "Use automated configuration scanning",
            "Implement proper security headers",
        ],
        "related_cwes": ["CWE-2", "CWE-11", "CWE-13", "CWE-15"],
    },
    "A06:2021": {
        "name": "Vulnerable and Outdated Components",
        "description": "Using components with known vulnerabilities.",
        "category": "dependencies",
        "severity_default": "medium",
        "likelihood": "high",
        "impact_description": "Varies from minimal to complete system compromise depending on the vulnerability.",
        "remediation_guidance": """
1. Remove unused dependencies
2. Continuously inventory client and server component versions
3. Monitor sources like CVE and NVD
4. Only obtain components from official sources
5. Monitor for unmaintained libraries
""",
        "prevention_techniques": [
            "Keep dependency inventory up to date",
            "Use dependency scanning tools",
            "Subscribe to security alerts for dependencies",
            "Only use components from trusted sources",
        ],
        "related_cwes": ["CWE-1104"],
    },
    "A07:2021": {
        "name": "Identification and Authentication Failures",
        "description": "Confirmation of user identity, authentication, and session management is critical.",
        "category": "auth",
        "severity_default": "high",
        "likelihood": "high",
        "impact_description": "Account takeover, identity theft, unauthorized access.",
        "remediation_guidance": """
1. Implement multi-factor authentication
2. Don't ship with default credentials
3. Implement weak password checks
4. Harden password recovery paths
5. Use secure session management
6. Implement rate limiting
""",
        "prevention_techniques": [
            "Implement multi-factor authentication",
            "Use secure password policies",
            "Implement account lockout mechanisms",
            "Use secure session management",
        ],
        "related_cwes": ["CWE-255", "CWE-259", "CWE-287", "CWE-384"],
    },
    "A08:2021": {
        "name": "Software and Data Integrity Failures",
        "description": "Code and infrastructure that does not protect against integrity violations.",
        "category": "integrity",
        "severity_default": "high",
        "likelihood": "medium",
        "impact_description": "Supply chain attacks, CI/CD compromise, malicious code injection.",
        "remediation_guidance": """
1. Use digital signatures
2. Use trusted repositories for libraries
3. Use software supply chain security tools
4. Ensure CI/CD pipeline has proper access control
5. Don't send serialized data to untrusted clients without integrity checks
""",
        "prevention_techniques": [
            "Verify integrity of downloaded components",
            "Use signed releases",
            "Secure CI/CD pipelines",
            "Avoid unsafe deserialization",
        ],
        "related_cwes": ["CWE-345", "CWE-353", "CWE-426", "CWE-494", "CWE-502"],
    },
    "A09:2021": {
        "name": "Security Logging and Monitoring Failures",
        "description": "Without logging and monitoring, breaches cannot be detected.",
        "category": "logging",
        "severity_default": "medium",
        "likelihood": "high",
        "impact_description": "Unable to detect active attacks, increasing dwell time and damage.",
        "remediation_guidance": """
1. Log all authentication events
2. Log access control failures
3. Ensure logs have context for forensics
4. Ensure log integrity
5. Establish effective monitoring and alerting
""",
        "prevention_techniques": [
            "Implement comprehensive logging",
            "Use centralized log management",
            "Implement alerting for suspicious activities",
            "Regularly review logs",
        ],
        "related_cwes": ["CWE-117", "CWE-223", "CWE-532", "CWE-778"],
    },
    "A10:2021": {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": "SSRF flaws occur when a web application fetches a remote resource without validating the URL.",
        "category": "injection",
        "severity_default": "high",
        "likelihood": "medium",
        "impact_description": "Access to internal services, data exfiltration, remote code execution.",
        "remediation_guidance": """
1. Sanitize and validate all client-supplied input data
2. Enforce allow lists for URL schemas, ports, and destinations
3. Disable HTTP redirections
4. Don't send raw responses to clients
5. Segment remote resource access functionality
""",
        "prevention_techniques": [
            "Validate and sanitize all URLs",
            "Use URL allow lists",
            "Disable URL redirects",
            "Segment network access",
        ],
        "related_cwes": ["CWE-918"],
    },
}

# Common CWE entries
CWE_KNOWLEDGE = {
    "CWE-79": {
        "name": "Improper Neutralization of Input During Web Page Generation (XSS)",
        "description": "The software does not neutralize or incorrectly neutralizes user-controllable input before it is placed in output.",
        "category": "injection",
        "severity_default": "high",
        "remediation_guidance": "Use context-aware output encoding. Use Content Security Policy. Validate input on server side.",
        "code_examples_vulnerable": [
            "document.innerHTML = userInput;",
            "response.write('<div>' + userInput + '</div>')",
        ],
        "code_examples_secure": [
            "document.textContent = userInput;",
            "response.write('<div>' + htmlEncode(userInput) + '</div>')",
        ],
    },
    "CWE-89": {
        "name": "Improper Neutralization of Special Elements in SQL Commands (SQL Injection)",
        "description": "The software constructs SQL queries using user-controllable input without proper sanitization.",
        "category": "injection",
        "severity_default": "critical",
        "remediation_guidance": "Use parameterized queries or prepared statements. Use ORM frameworks. Validate input.",
        "code_examples_vulnerable": [
            "cursor.execute('SELECT * FROM users WHERE id = ' + user_id)",
            "query = f'SELECT * FROM users WHERE name = \"{name}\"'",
        ],
        "code_examples_secure": [
            "cursor.execute('SELECT * FROM users WHERE id = ?', [user_id])",
            "User.objects.filter(name=name)",
        ],
    },
    "CWE-798": {
        "name": "Use of Hard-coded Credentials",
        "description": "The software contains hard-coded credentials, such as a password or cryptographic key.",
        "category": "crypto",
        "severity_default": "critical",
        "remediation_guidance": "Use environment variables or secure secret management. Never commit secrets to version control.",
        "code_examples_vulnerable": [
            "password = 'admin123'",
            "API_KEY = 'sk-abc123xyz'",
        ],
        "code_examples_secure": [
            "password = os.environ.get('DB_PASSWORD')",
            "API_KEY = get_secret('api_key')",
        ],
    },
    "CWE-22": {
        "name": "Improper Limitation of a Pathname to a Restricted Directory (Path Traversal)",
        "description": "The software uses external input to construct a pathname without proper sanitization.",
        "category": "injection",
        "severity_default": "high",
        "remediation_guidance": "Validate and sanitize file paths. Use canonical paths. Implement access controls.",
        "code_examples_vulnerable": [
            "open('/var/www/' + user_file)",
            "path = request.GET['file']",
        ],
        "code_examples_secure": [
            "safe_path = os.path.realpath(os.path.join(base_dir, user_file))",
            "if not safe_path.startswith(base_dir): raise Error",
        ],
    },
    "CWE-502": {
        "name": "Deserialization of Untrusted Data",
        "description": "The application deserializes untrusted data without sufficiently verifying validity.",
        "category": "injection",
        "severity_default": "high",
        "remediation_guidance": "Avoid deserializing untrusted data. Use safe serialization formats (JSON). Implement integrity checks.",
        "code_examples_vulnerable": [
            "pickle.loads(user_data)",
            "yaml.load(user_input)",
        ],
        "code_examples_secure": [
            "json.loads(user_data)",
            "yaml.safe_load(user_input)",
        ],
    },
    "CWE-918": {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": "The web server receives a URL from an upstream component and retrieves the contents without validation.",
        "category": "injection",
        "severity_default": "high",
        "remediation_guidance": "Validate and sanitize URLs. Use URL allowlists. Block requests to internal networks.",
        "code_examples_vulnerable": [
            "requests.get(user_provided_url)",
            "fetch(userInput)",
        ],
        "code_examples_secure": [
            "if is_allowed_domain(url): requests.get(url)",
            "validate_external_url(url) && fetch(url)",
        ],
    },
    "CWE-327": {
        "name": "Use of a Broken or Risky Cryptographic Algorithm",
        "description": "The use of a broken or risky cryptographic algorithm is an unnecessary risk.",
        "category": "crypto",
        "severity_default": "medium",
        "remediation_guidance": "Use modern, secure algorithms. Use AES-256 for encryption. Use SHA-256+ for hashing.",
        "code_examples_vulnerable": [
            "hashlib.md5(password).hexdigest()",
            "DES.encrypt(data)",
        ],
        "code_examples_secure": [
            "bcrypt.hashpw(password, bcrypt.gensalt())",
            "AES.new(key, AES.MODE_GCM)",
        ],
    },
    "CWE-78": {
        "name": "Improper Neutralization of Special Elements in OS Command (OS Command Injection)",
        "description": "The software constructs OS commands using externally-influenced input without neutralization.",
        "category": "injection",
        "severity_default": "critical",
        "remediation_guidance": "Avoid system calls with user input. Use language APIs instead of shell commands. Validate and sanitize input.",
        "code_examples_vulnerable": [
            "os.system('ping ' + user_ip)",
            "subprocess.call(f'cat {filename}', shell=True)",
        ],
        "code_examples_secure": [
            "subprocess.run(['ping', user_ip], shell=False)",
            "pathlib.Path(filename).read_text()",
        ],
    },
    "CWE-352": {
        "name": "Cross-Site Request Forgery (CSRF)",
        "description": "The web application does not verify that the request was intentionally provided by the user.",
        "category": "auth",
        "severity_default": "medium",
        "remediation_guidance": "Use CSRF tokens. Verify Origin/Referer headers. Use SameSite cookie attribute.",
        "code_examples_vulnerable": [
            "<form action='/transfer' method='POST'>",
            "// No CSRF token in form",
        ],
        "code_examples_secure": [
            "<input type='hidden' name='csrf_token' value='{{csrf_token}}'>",
            "verify_csrf_token(request.form['csrf_token'])",
        ],
    },
}


class SecurityRAGService:
    """
    Security RAG (Retrieval-Augmented Generation) Service.

    Provides OWASP/CWE knowledge base queries and context-aware
    security guidance for vulnerability remediation.
    """

    # Expose module constants as class attributes for tests
    OWASP_TOP_10_2021 = OWASP_TOP_10_2021
    CWE_KNOWLEDGE = CWE_KNOWLEDGE

    def __init__(self, db: AsyncSession):
        self.db = db
        self._initialized = False

    async def initialize_knowledge_base(self) -> Dict[str, Any]:
        """
        Initialize the security knowledge base with OWASP and CWE data.
        Should be called once during setup.

        Returns:
            Initialization result with counts
        """
        owasp_count = 0
        cwe_count = 0

        # Insert OWASP Top 10
        for identifier, data in OWASP_TOP_10_2021.items():
            existing = await self.db.execute(
                select(SecurityKnowledge).where(
                    SecurityKnowledge.identifier == identifier
                )
            )
            if not existing.scalar_one_or_none():
                knowledge = SecurityKnowledge(
                    id=uuid4(),
                    knowledge_type="owasp",
                    identifier=identifier,
                    name=data["name"],
                    description=data["description"],
                    category=data["category"],
                    severity_default=data["severity_default"],
                    likelihood=data["likelihood"],
                    impact_description=data["impact_description"],
                    remediation_guidance=data["remediation_guidance"],
                    prevention_techniques=data["prevention_techniques"],
                    related_cwes=data["related_cwes"],
                    source="owasp.org",
                )
                self.db.add(knowledge)
                owasp_count += 1

        # Insert CWE entries
        for identifier, data in CWE_KNOWLEDGE.items():
            existing = await self.db.execute(
                select(SecurityKnowledge).where(
                    SecurityKnowledge.identifier == identifier
                )
            )
            if not existing.scalar_one_or_none():
                knowledge = SecurityKnowledge(
                    id=uuid4(),
                    knowledge_type="cwe",
                    identifier=identifier,
                    name=data["name"],
                    description=data["description"],
                    category=data["category"],
                    severity_default=data["severity_default"],
                    remediation_guidance=data["remediation_guidance"],
                    code_examples_vulnerable=data.get("code_examples_vulnerable", []),
                    code_examples_secure=data.get("code_examples_secure", []),
                    source="cwe.mitre.org",
                )
                self.db.add(knowledge)
                cwe_count += 1

        await self.db.commit()
        self._initialized = True

        return {
            "status": "success",
            "owasp_entries": owasp_count,
            "cwe_entries": cwe_count,
            "total": owasp_count + cwe_count,
        }

    async def get_owasp_guidance(
        self,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get OWASP Top 10 guidance for a category.

        Args:
            category: OWASP category (e.g., "A01:2021", "A01", or "injection")

        Returns:
            OWASP guidance or None
        """
        # Normalize category format (A01 -> A01:2021)
        normalized_category = category
        if category.startswith("A") and ":" not in category and len(category) <= 3:
            normalized_category = f"{category}:2021"

        # FIRST: Try from embedded knowledge (fast, no DB)
        for identifier, data in OWASP_TOP_10_2021.items():
            if normalized_category == identifier or category == identifier or category == data["category"]:
                return {
                    "identifier": identifier,
                    **data
                }

        # THEN: Try database for custom/extended knowledge
        try:
            result = await self.db.execute(
                select(SecurityKnowledge).where(
                    and_(
                        SecurityKnowledge.knowledge_type == "owasp",
                        or_(
                            SecurityKnowledge.identifier == normalized_category,
                            SecurityKnowledge.identifier == category,
                            SecurityKnowledge.category == category
                        )
                    )
                )
            )
            knowledge = result.scalar_one_or_none()

            if knowledge:
                return knowledge.to_dict()
        except Exception as e:
            logger.debug(f"Database query failed, using embedded knowledge: {e}")

        return None

    async def get_cwe_guidance(
        self,
        cwe_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get CWE guidance.

        Args:
            cwe_id: CWE identifier (e.g., "CWE-89" or "89")

        Returns:
            CWE guidance or None
        """
        # Normalize CWE ID
        if not cwe_id.startswith("CWE-"):
            cwe_id = f"CWE-{cwe_id}"

        # FIRST: Try from embedded knowledge (fast, no DB)
        if cwe_id in CWE_KNOWLEDGE:
            return {
                "identifier": cwe_id,
                **CWE_KNOWLEDGE[cwe_id]
            }

        # THEN: Try database for extended knowledge
        try:
            result = await self.db.execute(
                select(SecurityKnowledge).where(
                    and_(
                        SecurityKnowledge.knowledge_type == "cwe",
                        SecurityKnowledge.identifier == cwe_id
                    )
                )
            )
            knowledge = result.scalar_one_or_none()

            if knowledge:
                return knowledge.to_dict()
        except Exception as e:
            logger.debug(f"Database query failed for CWE lookup: {e}")

        return None

    async def get_remediation(
        self,
        vulnerability_type: str,
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get remediation guidance for a vulnerability type.

        Args:
            vulnerability_type: Type of vulnerability (e.g., "sql_injection")
            language: Optional programming language context
            framework: Optional framework context

        Returns:
            Remediation guidance with examples
        """
        # Map vulnerability types to OWASP/CWE
        vuln_mapping = {
            "sql_injection": {"owasp": "A03:2021", "cwe": "CWE-89"},
            "xss": {"owasp": "A03:2021", "cwe": "CWE-79"},
            "hardcoded_secret": {"owasp": "A02:2021", "cwe": "CWE-798"},
            "path_traversal": {"owasp": "A01:2021", "cwe": "CWE-22"},
            "insecure_deserialization": {"owasp": "A08:2021", "cwe": "CWE-502"},
            "ssrf": {"owasp": "A10:2021", "cwe": "CWE-918"},
            "weak_crypto": {"owasp": "A02:2021", "cwe": "CWE-327"},
            "missing_auth": {"owasp": "A07:2021", "cwe": "CWE-287"},
        }

        mapping = vuln_mapping.get(vulnerability_type.lower(), {})

        result = {
            "vulnerability_type": vulnerability_type,
            "language": language,
            "framework": framework,
            "owasp_guidance": None,
            "cwe_guidance": None,
            "remediation_steps": [],
            "code_examples": {"vulnerable": [], "secure": []},
            "prevention_techniques": [],
        }

        # Get OWASP guidance
        if mapping.get("owasp"):
            owasp = await self.get_owasp_guidance(mapping["owasp"])
            if owasp:
                result["owasp_guidance"] = {
                    "identifier": owasp.get("identifier"),
                    "name": owasp.get("name"),
                    "remediation": owasp.get("remediation_guidance"),
                }
                result["prevention_techniques"].extend(
                    owasp.get("prevention_techniques", [])
                )

        # Get CWE guidance
        if mapping.get("cwe"):
            cwe = await self.get_cwe_guidance(mapping["cwe"])
            if cwe:
                result["cwe_guidance"] = {
                    "identifier": cwe.get("identifier"),
                    "name": cwe.get("name"),
                    "remediation": cwe.get("remediation_guidance"),
                }
                result["code_examples"]["vulnerable"] = cwe.get(
                    "code_examples_vulnerable", []
                )
                result["code_examples"]["secure"] = cwe.get(
                    "code_examples_secure", []
                )

        # Add language-specific guidance
        if language:
            lang_guidance = self._get_language_specific_guidance(
                vulnerability_type, language, framework
            )
            result["language_specific"] = lang_guidance

        # Compile remediation steps
        result["remediation_steps"] = self._compile_remediation_steps(
            vulnerability_type, language, framework
        )

        return result

    async def search_knowledge(
        self,
        query: str,
        knowledge_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search security knowledge base.

        Args:
            query: Search query
            knowledge_type: Optional filter (owasp, cwe, best_practice)
            limit: Maximum results

        Returns:
            Matching knowledge entries
        """
        results = []
        query_lower = query.lower()

        # FIRST: Search embedded OWASP knowledge
        if knowledge_type is None or knowledge_type == "owasp":
            for identifier, data in OWASP_TOP_10_2021.items():
                if (query_lower in identifier.lower() or
                    query_lower in data.get("name", "").lower() or
                    query_lower in data.get("description", "").lower() or
                    query_lower in data.get("category", "").lower()):
                    results.append({
                        "identifier": identifier,
                        "knowledge_type": "owasp",
                        **data
                    })

        # THEN: Search embedded CWE knowledge
        if knowledge_type is None or knowledge_type == "cwe":
            for identifier, data in CWE_KNOWLEDGE.items():
                if (query_lower in identifier.lower() or
                    query_lower in data.get("name", "").lower() or
                    query_lower in data.get("description", "").lower() or
                    query_lower in data.get("category", "").lower()):
                    results.append({
                        "identifier": identifier,
                        "knowledge_type": "cwe",
                        **data
                    })

        # THEN: Try database for extended knowledge
        try:
            base_query = select(SecurityKnowledge).where(
                SecurityKnowledge.is_active == True
            )

            if knowledge_type:
                base_query = base_query.where(
                    SecurityKnowledge.knowledge_type == knowledge_type
                )

            # Search in name and description
            base_query = base_query.where(
                or_(
                    SecurityKnowledge.name.ilike(f"%{query}%"),
                    SecurityKnowledge.description.ilike(f"%{query}%"),
                    SecurityKnowledge.identifier.ilike(f"%{query}%"),
                    SecurityKnowledge.category.ilike(f"%{query}%")
                )
            ).limit(limit)

            db_result = await self.db.execute(base_query)
            entries = db_result.scalars().all()

            # Add database results (avoid duplicates)
            existing_ids = {r["identifier"] for r in results}
            for entry in entries:
                if entry.identifier not in existing_ids:
                    results.append(entry.to_dict())
        except Exception as e:
            logger.debug(f"Database search failed, using embedded knowledge only: {e}")

        return results[:limit]

    async def get_security_checklist(
        self,
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a security checklist based on language/framework.

        Args:
            language: Programming language
            framework: Framework name

        Returns:
            Security checklist
        """
        checklist = {
            "language": language,
            "framework": framework,
            "categories": {},
        }

        # General categories
        categories = [
            ("injection", "Injection Prevention"),
            ("auth", "Authentication & Authorization"),
            ("crypto", "Cryptography"),
            ("config", "Security Configuration"),
            ("logging", "Logging & Monitoring"),
        ]

        # FIRST: Build from embedded knowledge
        for category_id, category_name in categories:
            items = []

            # Get from embedded OWASP knowledge
            for identifier, data in OWASP_TOP_10_2021.items():
                if data.get("category") == category_id:
                    items.append({
                        "id": identifier,
                        "name": data.get("name", ""),
                        "prevention": data.get("prevention_techniques", [])[:3],
                    })

            # Try to extend with database items
            try:
                result = await self.db.execute(
                    select(SecurityKnowledge).where(
                        and_(
                            SecurityKnowledge.is_active == True,
                            SecurityKnowledge.category == category_id
                        )
                    ).limit(5)
                )
                entries = result.scalars().all()

                for entry in entries:
                    # Avoid duplicates
                    if not any(item["id"] == entry.identifier for item in items):
                        items.append({
                            "id": entry.identifier,
                            "name": entry.name,
                            "prevention": entry.prevention_techniques[:3] if entry.prevention_techniques else [],
                        })
            except Exception as e:
                logger.debug(f"Database query failed for checklist category {category_id}: {e}")

            checklist["categories"][category_id] = {
                "name": category_name,
                "items": items[:5],  # Limit to 5 items
            }

        return checklist

    def _get_language_specific_guidance(
        self,
        vulnerability_type: str,
        language: str,
        framework: Optional[str]
    ) -> Dict[str, Any]:
        """Get language-specific security guidance."""
        guidance = {
            "language": language,
            "framework": framework,
            "libraries": [],
            "patterns": [],
        }

        language_guidance = {
            "python": {
                "sql_injection": {
                    "libraries": ["SQLAlchemy ORM", "psycopg2 parameterized queries"],
                    "patterns": [
                        "Use session.query() with filter()",
                        "Use cursor.execute() with parameters tuple",
                    ],
                },
                "xss": {
                    "libraries": ["MarkupSafe", "bleach"],
                    "patterns": [
                        "Use Jinja2 autoescaping",
                        "Use bleach.clean() for user input",
                    ],
                },
            },
            "javascript": {
                "sql_injection": {
                    "libraries": ["Prisma", "Sequelize ORM"],
                    "patterns": [
                        "Use ORM query builders",
                        "Use prepared statements",
                    ],
                },
                "xss": {
                    "libraries": ["DOMPurify", "sanitize-html"],
                    "patterns": [
                        "Use textContent instead of innerHTML",
                        "Use React's automatic escaping",
                    ],
                },
            },
        }

        lang_data = language_guidance.get(language.lower(), {})
        vuln_data = lang_data.get(vulnerability_type.lower(), {})

        guidance["libraries"] = vuln_data.get("libraries", [])
        guidance["patterns"] = vuln_data.get("patterns", [])

        return guidance

    def _compile_remediation_steps(
        self,
        vulnerability_type: str,
        language: Optional[str],
        framework: Optional[str]
    ) -> List[str]:
        """Compile remediation steps for a vulnerability."""
        steps = []

        remediation_steps = {
            "sql_injection": [
                "1. Replace string concatenation with parameterized queries",
                "2. Use ORM framework for database operations",
                "3. Implement input validation on all user-supplied data",
                "4. Apply principle of least privilege for database users",
                "5. Implement query result limits to prevent data extraction",
            ],
            "xss": [
                "1. Encode output based on context (HTML, JS, CSS, URL)",
                "2. Implement Content Security Policy headers",
                "3. Use modern frameworks with automatic escaping",
                "4. Validate and sanitize all user input",
                "5. Set HttpOnly and Secure flags on cookies",
            ],
            "hardcoded_secret": [
                "1. Move all secrets to environment variables",
                "2. Use a secrets manager (Vault, AWS Secrets Manager)",
                "3. Add sensitive files to .gitignore",
                "4. Rotate any exposed credentials immediately",
                "5. Implement git hooks to prevent secret commits",
            ],
            "path_traversal": [
                "1. Validate and sanitize file paths",
                "2. Use canonical path comparison",
                "3. Implement allowlist for accessible directories",
                "4. Never use user input directly in file operations",
                "5. Use chroot or similar isolation techniques",
            ],
        }

        steps = remediation_steps.get(vulnerability_type.lower(), [
            f"1. Review and remediate {vulnerability_type} vulnerability",
            "2. Implement input validation",
            "3. Apply security best practices",
            "4. Add security tests",
            "5. Conduct security review",
        ])

        return steps


# Factory function
def get_security_rag_service(db: AsyncSession) -> SecurityRAGService:
    """Get Security RAG service instance."""
    return SecurityRAGService(db)
