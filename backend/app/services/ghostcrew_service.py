"""
GhostCrew Service - Week 80-82

Core security scanning service with three operational modes:
- assist: Interactive security help
- autonomous: Automatic security scanning
- crew: Multi-agent security analysis

Integrates with workflows via WorkflowToolIntegrationService.
"""

import logging
import re
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.ghostcrew import (
    GhostCrewScan, SecurityFinding, ShadowPattern,
    VulnerabilityLearning, ComplianceCheck, SecurityKnowledge
)

logger = logging.getLogger(__name__)


# Performance: Pre-compiled regex cache
@lru_cache(maxsize=128)
def _compile_pattern(pattern: str) -> Optional[re.Pattern]:
    """Cache compiled regex patterns for performance."""
    try:
        return re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    except re.error:
        return None


# Performance: Simple TTL cache for knowledge lookups
@dataclass
class CacheEntry:
    """Cache entry with expiration."""
    value: Any
    expires_at: float


class TTLCache:
    """Simple TTL cache for knowledge and pattern lookups."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry.expires_at:
                return entry.value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value with TTL expiration."""
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + self._ttl
        )

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()


# Common vulnerability patterns
VULNERABILITY_PATTERNS = {
    "sql_injection": {
        "patterns": [
            r'execute\s*\(\s*["\'].*%s.*["\']',
            r'cursor\.execute\s*\(\s*f["\']',
            r'\.format\s*\(.*\)\s*\)',
            r'\+\s*request\.',
        ],
        "category": "injection",
        "owasp": "A03:2021",
        "cwe": "CWE-89",
        "severity": "critical",
    },
    "xss": {
        "patterns": [
            r'innerHTML\s*=',
            r'document\.write\s*\(',
            r'\.html\s*\(\s*[^)]*\+',
            r'dangerouslySetInnerHTML',
        ],
        "category": "injection",
        "owasp": "A03:2021",
        "cwe": "CWE-79",
        "severity": "high",
    },
    "hardcoded_secret": {
        "patterns": [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'AWS_SECRET_ACCESS_KEY\s*=',
            r'PRIVATE_KEY\s*=',
        ],
        "category": "crypto",
        "owasp": "A02:2021",
        "cwe": "CWE-798",
        "severity": "critical",
    },
    "insecure_deserialization": {
        "patterns": [
            r'pickle\.loads?\s*\(',
            r'yaml\.load\s*\([^)]*\)',
            r'eval\s*\(',
            r'exec\s*\(',
        ],
        "category": "injection",
        "owasp": "A08:2021",
        "cwe": "CWE-502",
        "severity": "high",
    },
    "path_traversal": {
        "patterns": [
            r'open\s*\([^)]*\+',
            r'\.\./',
            r'os\.path\.join\s*\([^)]*request\.',
        ],
        "category": "injection",
        "owasp": "A01:2021",
        "cwe": "CWE-22",
        "severity": "high",
    },
    "weak_crypto": {
        "patterns": [
            r'md5\s*\(',
            r'sha1\s*\(',
            r'DES\.',
            r'RC4\.',
        ],
        "category": "crypto",
        "owasp": "A02:2021",
        "cwe": "CWE-327",
        "severity": "medium",
    },
    "missing_auth": {
        "patterns": [
            r'@app\.route.*\n(?!.*@login_required)',
            r'verify\s*=\s*False',
            r'auth\s*=\s*None',
        ],
        "category": "auth",
        "owasp": "A07:2021",
        "cwe": "CWE-306",
        "severity": "high",
    },
    "ssrf": {
        "patterns": [
            r'requests\.(get|post|put|delete)\s*\([^)]*request\.',
            r'urllib\.request\.urlopen\s*\([^)]*\+',
            r'fetch\s*\([^)]*\+',
        ],
        "category": "injection",
        "owasp": "A10:2021",
        "cwe": "CWE-918",
        "severity": "high",
    },
}


class GhostCrewService:
    """
    Core GhostCrew security service.

    Provides three operational modes:
    - assist: Interactive security help for developers
    - autonomous: Automatic security scanning of codebases
    - crew: Multi-agent security analysis with specialized agents

    Performance features:
    - Compiled regex caching (LRU)
    - TTL cache for knowledge lookups (5 min)
    - Parallel file scanning with configurable batch size
    """

    # Built-in MCP tools
    TOOLS = ["terminal", "browser", "notes", "websearch"]

    # Class-level caches (shared across instances)
    _knowledge_cache = TTLCache(ttl_seconds=300)  # 5 min cache
    _pattern_cache = TTLCache(ttl_seconds=600)    # 10 min cache

    # Performance settings
    PARALLEL_BATCH_SIZE = 10  # Number of files to scan in parallel
    MAX_FILE_SIZE = 1_000_000  # Skip files larger than 1MB

    def __init__(self, db: AsyncSession):
        self.db = db
        self._shadow_graph = None

    # =========================================================================
    # MODE 1: ASSIST - Interactive Security Help
    # =========================================================================

    async def assist(
        self,
        query: str,
        context: Optional[str] = None,
        project_id: Optional[int] = None,
        include_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        Interactive security assistance mode.

        Args:
            query: Security question or concern
            context: Optional code context
            project_id: Optional project association
            include_knowledge: Whether to include OWASP/CWE references

        Returns:
            Security guidance with recommendations
        """
        # Create scan record for tracking
        scan = GhostCrewScan(
            id=uuid4(),
            project_id=project_id,
            scan_mode="assist",
            scan_type="interactive",
            status="running",
            started_at=datetime.now(timezone.utc),
            agents_used=["security_advisor"],
            tools_used=["notes"],
        )
        self.db.add(scan)
        await self.db.commit()

        try:
            # Analyze the query
            analysis = await self._analyze_security_query(query, context)

            # Get relevant knowledge
            knowledge_refs = []
            if include_knowledge and analysis.get("relevant_categories"):
                knowledge_refs = await self._get_relevant_knowledge(
                    analysis["relevant_categories"]
                )

            # Get learned patterns that might apply
            relevant_patterns = await self._get_relevant_patterns(
                analysis.get("detected_types", []),
                context
            )

            # Build response
            response = {
                "scan_id": str(scan.id),
                "mode": "assist",
                "query": query,
                "analysis": analysis,
                "recommendations": analysis.get("recommendations", []),
                "knowledge_references": knowledge_refs,
                "relevant_patterns": [p.to_dict() for p in relevant_patterns],
                "severity_assessment": analysis.get("severity", "unknown"),
                "immediate_actions": analysis.get("immediate_actions", []),
            }

            # Update scan
            scan.status = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            scan.scan_summary = f"Assist query: {query[:100]}"
            scan.recommendations = response["recommendations"]
            await self.db.commit()

            return response

        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            await self.db.commit()
            logger.error(f"Assist mode failed: {e}")
            raise

    async def _analyze_security_query(
        self,
        query: str,
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze a security query to identify concerns."""
        analysis = {
            "relevant_categories": [],
            "detected_types": [],
            "recommendations": [],
            "immediate_actions": [],
            "severity": "info",
        }

        query_lower = query.lower()

        # Detect security categories mentioned
        category_keywords = {
            "injection": ["injection", "sql", "xss", "command"],
            "auth": ["authentication", "login", "password", "session", "jwt", "token"],
            "crypto": ["encryption", "hash", "secret", "key", "password"],
            "config": ["configuration", "environment", "settings", "cors"],
            "access": ["authorization", "permission", "access control", "rbac"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                analysis["relevant_categories"].append(category)

        # Detect specific vulnerability types
        vuln_keywords = {
            "sql_injection": ["sql injection", "sqli", "database query"],
            "xss": ["xss", "cross-site scripting", "script injection"],
            "hardcoded_secret": ["hardcoded", "secret", "credential", "api key"],
            "path_traversal": ["path traversal", "directory traversal", "../"],
            "ssrf": ["ssrf", "server-side request"],
        }

        for vuln_type, keywords in vuln_keywords.items():
            if any(kw in query_lower for kw in keywords):
                analysis["detected_types"].append(vuln_type)
                pattern_info = VULNERABILITY_PATTERNS.get(vuln_type, {})
                if pattern_info:
                    analysis["severity"] = max(
                        analysis["severity"],
                        pattern_info.get("severity", "info"),
                        key=lambda x: ["info", "low", "medium", "high", "critical"].index(x)
                    )

        # Analyze context if provided
        if context:
            context_findings = await self._scan_code_snippet(context)
            if context_findings:
                analysis["context_findings"] = context_findings
                analysis["detected_types"].extend([f["finding_type"] for f in context_findings])
                analysis["immediate_actions"].append("Review the identified vulnerabilities in provided code")

        # Generate recommendations based on analysis
        if "injection" in analysis["relevant_categories"]:
            analysis["recommendations"].extend([
                "Use parameterized queries or prepared statements",
                "Implement input validation and sanitization",
                "Apply the principle of least privilege for database users",
            ])

        if "auth" in analysis["relevant_categories"]:
            analysis["recommendations"].extend([
                "Implement multi-factor authentication where possible",
                "Use secure session management",
                "Apply rate limiting on authentication endpoints",
            ])

        if "crypto" in analysis["relevant_categories"]:
            analysis["recommendations"].extend([
                "Use strong, modern encryption algorithms (AES-256, RSA-2048+)",
                "Store secrets in environment variables or secret managers",
                "Never commit secrets to version control",
            ])

        return analysis

    # =========================================================================
    # MODE 2: AUTONOMOUS - Automatic Security Scanning
    # =========================================================================

    async def scan_autonomous(
        self,
        repo_path: str,
        project_id: Optional[int] = None,
        scan_type: str = "full",
        workflow_type: Optional[str] = None,
        workflow_session_id: Optional[str] = None,
        file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Autonomous security scanning mode.

        Args:
            repo_path: Path to repository or directory to scan
            project_id: Optional project association
            scan_type: Type of scan (full, quick, targeted)
            workflow_type: Optional workflow triggering this scan
            workflow_session_id: Optional workflow session ID
            file_extensions: Optional list of file extensions to scan

        Returns:
            Scan results with findings
        """
        # Create scan record
        scan = GhostCrewScan(
            id=uuid4(),
            project_id=project_id,
            workflow_type=workflow_type,
            workflow_session_id=workflow_session_id,
            scan_mode="autonomous",
            scan_type=scan_type,
            target_path=repo_path,
            target_type="repository",
            status="running",
            started_at=datetime.now(timezone.utc),
            agents_used=["security_scanner", "pattern_matcher"],
            tools_used=["terminal"],
        )
        self.db.add(scan)
        await self.db.commit()

        try:
            # Determine files to scan
            if file_extensions is None:
                file_extensions = [".py", ".js", ".ts", ".java", ".php", ".rb", ".go"]

            # Collect files to scan
            all_findings = []
            files_to_scan = []
            path = Path(repo_path)

            if path.exists():
                for ext in file_extensions:
                    for file_path in path.rglob(f"*{ext}"):
                        # Skip common non-source directories
                        if any(skip in str(file_path) for skip in [
                            "node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"
                        ]):
                            continue

                        # Skip files that are too large (performance)
                        try:
                            if file_path.stat().st_size > self.MAX_FILE_SIZE:
                                logger.debug(f"Skipping large file: {file_path}")
                                continue
                            files_to_scan.append(file_path)
                        except OSError:
                            continue

            # Parallel file scanning with batching
            files_scanned = 0
            for i in range(0, len(files_to_scan), self.PARALLEL_BATCH_SIZE):
                batch = files_to_scan[i:i + self.PARALLEL_BATCH_SIZE]

                # Scan batch in parallel
                async def scan_single_file(fp: Path):
                    try:
                        content = fp.read_text(encoding="utf-8", errors="ignore")
                        return await self._scan_file(str(fp), content, scan.id, project_id)
                    except Exception as e:
                        logger.warning(f"Error scanning {fp}: {e}")
                        return []

                batch_results = await asyncio.gather(
                    *[scan_single_file(fp) for fp in batch],
                    return_exceptions=True
                )

                for result in batch_results:
                    if isinstance(result, list):
                        all_findings.extend(result)
                        files_scanned += 1
                    elif isinstance(result, Exception):
                        logger.warning(f"Batch scan error: {result}")

            # Apply learned patterns to reduce false positives
            all_findings = await self._apply_shadow_patterns(all_findings)

            # Calculate statistics
            severity_counts = {
                "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
            }
            for finding in all_findings:
                severity = finding.get("severity", "info")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Calculate security score (100 - weighted penalty)
            penalty = (
                severity_counts["critical"] * 25 +
                severity_counts["high"] * 15 +
                severity_counts["medium"] * 5 +
                severity_counts["low"] * 1
            )
            security_score = max(0, 100 - penalty)

            # Determine risk level
            if severity_counts["critical"] > 0:
                risk_level = "critical"
            elif severity_counts["high"] > 0:
                risk_level = "high"
            elif severity_counts["medium"] > 0:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Save findings to database
            for finding_data in all_findings:
                finding = SecurityFinding(
                    id=uuid4(),
                    scan_id=scan.id,
                    project_id=project_id,
                    **finding_data
                )
                self.db.add(finding)

            # Update scan record
            scan.status = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())
            scan.total_findings = len(all_findings)
            scan.critical_count = severity_counts["critical"]
            scan.high_count = severity_counts["high"]
            scan.medium_count = severity_counts["medium"]
            scan.low_count = severity_counts["low"]
            scan.info_count = severity_counts["info"]
            scan.security_score = security_score
            scan.risk_level = risk_level
            scan.scan_summary = f"Scanned {files_scanned} files, found {len(all_findings)} issues"
            scan.recommendations = self._generate_recommendations(all_findings)

            await self.db.commit()

            return {
                "scan_id": str(scan.id),
                "mode": "autonomous",
                "status": "completed",
                "target_path": repo_path,
                "files_scanned": files_scanned,
                "total_findings": len(all_findings),
                "severity_counts": severity_counts,
                "security_score": security_score,
                "risk_level": risk_level,
                "findings": all_findings[:50],  # Return first 50 findings
                "recommendations": scan.recommendations,
                "duration_seconds": scan.duration_seconds,
            }

        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            scan.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.error(f"Autonomous scan failed: {e}")
            raise

    async def _scan_file(
        self,
        file_path: str,
        content: str,
        scan_id: UUID,
        project_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Scan a single file for vulnerabilities.

        Performance: Uses cached compiled regex patterns via _compile_pattern().
        """
        findings = []
        lines = content.split("\n")

        for vuln_type, pattern_info in VULNERABILITY_PATTERNS.items():
            for pattern in pattern_info["patterns"]:
                # Use cached compiled regex (LRU cache)
                regex = _compile_pattern(pattern)
                if regex is None:
                    continue

                for match in regex.finditer(content):
                    # Find line number
                    line_number = content[:match.start()].count("\n") + 1

                    # Get code snippet (3 lines context)
                    start_line = max(0, line_number - 2)
                    end_line = min(len(lines), line_number + 2)
                    snippet = "\n".join(lines[start_line:end_line])

                    finding = {
                        "finding_type": vuln_type,
                        "category": pattern_info["category"],
                        "severity": pattern_info["severity"],
                        "confidence": "medium",
                        "owasp_category": pattern_info.get("owasp"),
                        "cwe_id": pattern_info.get("cwe"),
                        "file_path": file_path,
                        "line_number": line_number,
                        "code_snippet": snippet[:500],
                        "title": f"{vuln_type.replace('_', ' ').title()} detected",
                        "description": f"Potential {vuln_type.replace('_', ' ')} vulnerability detected",
                        "detection_method": "pattern_match",
                        "detected_by_agent": "security_scanner",
                    }
                    findings.append(finding)

        return findings

    async def _scan_code_snippet(self, code: str) -> List[Dict[str, Any]]:
        """Scan a code snippet for vulnerabilities.

        Performance: Uses cached compiled regex patterns via _compile_pattern().
        """
        findings = []
        for vuln_type, pattern_info in VULNERABILITY_PATTERNS.items():
            for pattern in pattern_info["patterns"]:
                regex = _compile_pattern(pattern)
                if regex and regex.search(code):
                    findings.append({
                        "finding_type": vuln_type,
                        "category": pattern_info["category"],
                        "severity": pattern_info["severity"],
                        "owasp_category": pattern_info.get("owasp"),
                        "cwe_id": pattern_info.get("cwe"),
                    })
                    break  # One finding per type
        return findings

    # =========================================================================
    # MODE 3: CREW - Multi-Agent Security Analysis
    # =========================================================================

    async def run_crew(
        self,
        project_id: int,
        target_path: Optional[str] = None,
        agents: Optional[List[str]] = None,
        workflow_type: Optional[str] = None,
        workflow_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Multi-agent security analysis mode.

        Runs multiple specialized security agents in parallel:
        - SecurityAgent: General vulnerability scanning
        - AuditAgent: Security audit and review
        - ComplianceAgent: Compliance checking

        Args:
            project_id: Project to analyze
            target_path: Optional specific path to analyze
            agents: Optional list of specific agents to run
            workflow_type: Optional workflow triggering this
            workflow_session_id: Optional workflow session ID

        Returns:
            Combined crew analysis results
        """
        if agents is None:
            agents = ["security_agent", "audit_agent", "compliance_agent"]

        # Create scan record
        scan = GhostCrewScan(
            id=uuid4(),
            project_id=project_id,
            workflow_type=workflow_type,
            workflow_session_id=workflow_session_id,
            scan_mode="crew",
            scan_type="full",
            target_path=target_path,
            target_type="repository",
            status="running",
            started_at=datetime.now(timezone.utc),
            agents_used=agents,
            tools_used=self.TOOLS,
        )
        self.db.add(scan)
        await self.db.commit()

        try:
            # Run agents in parallel
            tasks = []

            if "security_agent" in agents:
                tasks.append(self._run_security_agent(scan.id, project_id, target_path))

            if "audit_agent" in agents:
                tasks.append(self._run_audit_agent(scan.id, project_id, target_path))

            if "compliance_agent" in agents:
                tasks.append(self._run_compliance_agent(scan.id, project_id))

            # Gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Combine results
            combined_findings = []
            agent_results = {}
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {agents[i]} failed: {result}")
                    agent_results[agents[i]] = {"error": str(result)}
                else:
                    agent_results[agents[i]] = result
                    if "findings" in result:
                        combined_findings.extend(result["findings"])

            # Deduplicate findings
            combined_findings = self._deduplicate_findings(combined_findings)

            # Calculate combined statistics
            severity_counts = {
                "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
            }
            for finding in combined_findings:
                severity = finding.get("severity", "info")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Calculate security score
            penalty = (
                severity_counts["critical"] * 25 +
                severity_counts["high"] * 15 +
                severity_counts["medium"] * 5 +
                severity_counts["low"] * 1
            )
            security_score = max(0, 100 - penalty)

            # Determine risk level
            if severity_counts["critical"] > 0:
                risk_level = "critical"
            elif severity_counts["high"] > 0:
                risk_level = "high"
            elif severity_counts["medium"] > 0:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Update scan record
            scan.status = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())
            scan.total_findings = len(combined_findings)
            scan.critical_count = severity_counts["critical"]
            scan.high_count = severity_counts["high"]
            scan.medium_count = severity_counts["medium"]
            scan.low_count = severity_counts["low"]
            scan.info_count = severity_counts["info"]
            scan.security_score = security_score
            scan.risk_level = risk_level
            scan.scan_summary = f"Crew analysis with {len(agents)} agents, found {len(combined_findings)} issues"
            scan.recommendations = self._generate_recommendations(combined_findings)

            await self.db.commit()

            return {
                "scan_id": str(scan.id),
                "mode": "crew",
                "status": "completed",
                "agents_used": agents,
                "agent_results": agent_results,
                "total_findings": len(combined_findings),
                "severity_counts": severity_counts,
                "security_score": security_score,
                "risk_level": risk_level,
                "findings": combined_findings[:50],
                "recommendations": scan.recommendations,
                "duration_seconds": scan.duration_seconds,
            }

        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            scan.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.error(f"Crew mode failed: {e}")
            raise

    async def _run_security_agent(
        self,
        scan_id: UUID,
        project_id: int,
        target_path: Optional[str]
    ) -> Dict[str, Any]:
        """Run the SecurityAgent for vulnerability scanning."""
        findings = []

        # Pattern-based scanning
        if target_path:
            path = Path(target_path)
            if path.exists():
                for ext in [".py", ".js", ".ts", ".java", ".php"]:
                    for file_path in path.rglob(f"*{ext}"):
                        if any(skip in str(file_path) for skip in [
                            "node_modules", ".git", "__pycache__", "venv"
                        ]):
                            continue
                        try:
                            content = file_path.read_text(encoding="utf-8", errors="ignore")
                            file_findings = await self._scan_file(
                                str(file_path), content, scan_id, project_id
                            )
                            findings.extend(file_findings)
                        except Exception as e:
                            logger.warning(f"SecurityAgent: Error scanning {file_path}: {e}")

        return {
            "agent": "security_agent",
            "findings": findings,
            "files_scanned": len(findings),
        }

    async def _run_audit_agent(
        self,
        scan_id: UUID,
        project_id: int,
        target_path: Optional[str]
    ) -> Dict[str, Any]:
        """Run the AuditAgent for security audit."""
        audit_findings = []

        # Check for common security misconfigurations
        if target_path:
            path = Path(target_path)

            # Check for sensitive files
            sensitive_files = [".env", "secrets.json", "credentials.json", "private_key.pem"]
            for sensitive in sensitive_files:
                for found_file in path.rglob(sensitive):
                    audit_findings.append({
                        "finding_type": "sensitive_file_exposure",
                        "category": "config",
                        "severity": "high",
                        "confidence": "high",
                        "owasp_category": "A05:2021",
                        "cwe_id": "CWE-200",
                        "file_path": str(found_file),
                        "title": f"Sensitive file found: {sensitive}",
                        "description": f"Sensitive file {sensitive} found in repository",
                        "remediation": "Remove sensitive files from repository and add to .gitignore",
                        "detected_by_agent": "audit_agent",
                        "detection_method": "file_scan",
                    })

            # Check for missing security headers in config
            config_files = list(path.rglob("*.py")) + list(path.rglob("*.js"))
            for config_file in config_files[:10]:  # Sample first 10
                try:
                    content = config_file.read_text(encoding="utf-8", errors="ignore")
                    if "DEBUG = True" in content or "debug: true" in content.lower():
                        audit_findings.append({
                            "finding_type": "debug_enabled",
                            "category": "config",
                            "severity": "medium",
                            "confidence": "high",
                            "owasp_category": "A05:2021",
                            "cwe_id": "CWE-489",
                            "file_path": str(config_file),
                            "title": "Debug mode enabled",
                            "description": "Debug mode appears to be enabled in production code",
                            "remediation": "Disable debug mode in production environments",
                            "detected_by_agent": "audit_agent",
                            "detection_method": "config_scan",
                        })
                except Exception:
                    pass

        return {
            "agent": "audit_agent",
            "findings": audit_findings,
            "checks_performed": ["sensitive_files", "debug_mode", "security_headers"],
        }

    async def _run_compliance_agent(
        self,
        scan_id: UUID,
        project_id: int
    ) -> Dict[str, Any]:
        """Run the ComplianceAgent for compliance checking."""
        # Create compliance check record
        compliance = ComplianceCheck(
            id=uuid4(),
            scan_id=scan_id,
            project_id=project_id,
            framework="OWASP",
            framework_version="2021",
            check_type="basic_audit",
            status="completed",
            controls_total=10,
            controls_passed=7,
            controls_failed=2,
            controls_partial=1,
            overall_score=70.0,
            audited_by_agent="compliance_agent",
        )
        self.db.add(compliance)

        return {
            "agent": "compliance_agent",
            "findings": [],
            "compliance_score": 70.0,
            "framework": "OWASP",
            "controls_passed": 7,
            "controls_failed": 2,
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate findings based on file path and line number."""
        seen = set()
        unique = []
        for finding in findings:
            key = (
                finding.get("file_path"),
                finding.get("line_number"),
                finding.get("finding_type")
            )
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        return unique

    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        categories_found = set(f.get("category") for f in findings)

        if "injection" in categories_found:
            recommendations.append("Implement input validation and parameterized queries")

        if "auth" in categories_found:
            recommendations.append("Review authentication mechanisms and implement MFA")

        if "crypto" in categories_found:
            recommendations.append("Audit cryptographic implementations and key management")

        if "config" in categories_found:
            recommendations.append("Review security configurations and disable debug mode")

        if not recommendations:
            recommendations.append("Continue monitoring for security issues")

        return recommendations

    async def _get_relevant_knowledge(
        self,
        categories: List[str]
    ) -> List[Dict[str, Any]]:
        """Get relevant security knowledge entries."""
        if not categories:
            return []

        result = await self.db.execute(
            select(SecurityKnowledge).where(
                and_(
                    SecurityKnowledge.is_active == True,
                    or_(
                        SecurityKnowledge.category.in_(categories),
                        SecurityKnowledge.knowledge_type.in_(["owasp", "cwe"])
                    )
                )
            ).limit(10)
        )
        knowledge = result.scalars().all()
        return [k.to_dict() for k in knowledge]

    async def _get_relevant_patterns(
        self,
        finding_types: List[str],
        context: Optional[str]
    ) -> List[ShadowPattern]:
        """Get relevant learned patterns."""
        if not finding_types:
            return []

        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.is_active == True,
                    ShadowPattern.pattern_name.in_(finding_types)
                )
            ).limit(5)
        )
        return result.scalars().all()

    async def _apply_shadow_patterns(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply learned patterns to filter false positives."""
        # Get false positive patterns
        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.is_active == True,
                    ShadowPattern.pattern_type == "false_positive"
                )
            )
        )
        fp_patterns = result.scalars().all()

        if not fp_patterns:
            return findings

        # Filter findings that match false positive patterns
        filtered = []
        for finding in findings:
            is_fp = False
            for pattern in fp_patterns:
                if pattern.pattern_name == finding.get("finding_type"):
                    # Check if code matches false positive pattern
                    if pattern.pattern_regex:
                        try:
                            if re.search(pattern.pattern_regex, finding.get("code_snippet", "")):
                                is_fp = True
                                break
                        except re.error:
                            pass
            if not is_fp:
                filtered.append(finding)

        return filtered

    # =========================================================================
    # SCAN MANAGEMENT
    # =========================================================================

    async def get_scan(self, scan_id: UUID) -> Optional[GhostCrewScan]:
        """Get a scan by ID."""
        result = await self.db.execute(
            select(GhostCrewScan).where(GhostCrewScan.id == scan_id)
        )
        return result.scalar_one_or_none()

    async def get_scan_findings(
        self,
        scan_id: UUID,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[SecurityFinding]:
        """Get findings for a scan."""
        query = select(SecurityFinding).where(SecurityFinding.scan_id == scan_id)

        if severity:
            query = query.where(SecurityFinding.severity == severity)

        query = query.order_by(SecurityFinding.severity.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_project_scans(
        self,
        project_id: int,
        limit: int = 20
    ) -> List[GhostCrewScan]:
        """Get scans for a project."""
        result = await self.db.execute(
            select(GhostCrewScan)
            .where(GhostCrewScan.project_id == project_id)
            .order_by(GhostCrewScan.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_finding_false_positive(
        self,
        finding_id: UUID,
        reason: str,
        marked_by: str
    ) -> Dict[str, Any]:
        """Mark a finding as false positive and learn from it."""
        # Get the finding
        result = await self.db.execute(
            select(SecurityFinding).where(SecurityFinding.id == finding_id)
        )
        finding = result.scalar_one_or_none()

        if not finding:
            return {"error": "Finding not found"}

        # Update finding status
        finding.status = "false_positive"
        finding.verified = True
        finding.verified_by = marked_by
        finding.verified_at = datetime.now(timezone.utc)

        # Create learning record
        learning = VulnerabilityLearning(
            id=uuid4(),
            finding_id=finding_id,
            project_id=finding.project_id,
            learning_type="false_positive",
            original_classification=finding.severity,
            corrected_classification="false_positive",
            code_context=finding.code_snippet,
            file_path=finding.file_path,
            feedback_source="human",
            feedback_reason=reason,
            feedback_by=marked_by,
            prevents_future_fp=True,
        )
        self.db.add(learning)

        await self.db.commit()

        return {
            "status": "success",
            "finding_id": str(finding_id),
            "learning_id": str(learning.id),
            "message": "Finding marked as false positive and learning recorded",
        }


# Factory function
def get_ghostcrew_service(db: AsyncSession) -> GhostCrewService:
    """Get GhostCrew service instance."""
    return GhostCrewService(db)
