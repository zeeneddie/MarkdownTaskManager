"""
ShadowGraph Service - Week 80-82

Vulnerability pattern learning and knowledge consolidation.
Learns from security scans to improve detection accuracy
and reduce false positives over time.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc

from app.models.ghostcrew import (
    ShadowPattern, VulnerabilityLearning, SecurityFinding,
    GhostCrewScan, SecurityKnowledge
)

logger = logging.getLogger(__name__)


class ShadowGraphService:
    """
    ShadowGraph: Continuous learning from security scans.

    Features:
    - Pattern recording and learning
    - False positive tracking and filtering
    - Accuracy improvement over time
    - Knowledge consolidation
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # PATTERN RECORDING
    # =========================================================================

    async def record_finding(
        self,
        finding: SecurityFinding,
        scan_id: UUID
    ) -> Optional[ShadowPattern]:
        """
        Record a finding and update or create pattern.

        Args:
            finding: The security finding to record
            scan_id: The scan that produced this finding

        Returns:
            Updated or created pattern
        """
        # Check if pattern already exists
        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.pattern_name == finding.finding_type,
                    ShadowPattern.category == finding.category,
                    ShadowPattern.language == self._detect_language(finding.file_path)
                )
            )
        )
        pattern = result.scalar_one_or_none()

        if pattern:
            # Update existing pattern
            pattern.times_detected += 1
            pattern.last_detection = datetime.utcnow()

            # Add scan to learned_from list
            if str(scan_id) not in pattern.learned_from_scans:
                scans = list(pattern.learned_from_scans) if pattern.learned_from_scans else []
                scans.append(str(scan_id))
                pattern.learned_from_scans = scans[-100:]  # Keep last 100 scans

            # Add code example if unique
            if finding.code_snippet:
                examples = list(pattern.code_examples) if pattern.code_examples else []
                if len(examples) < 10 and finding.code_snippet not in examples:
                    examples.append(finding.code_snippet[:500])
                    pattern.code_examples = examples

        else:
            # Create new pattern
            pattern = ShadowPattern(
                id=uuid4(),
                pattern_name=finding.finding_type,
                pattern_type="vulnerability",
                category=finding.category,
                language=self._detect_language(finding.file_path),
                severity=finding.severity,
                owasp_mapping=finding.owasp_category,
                cwe_mapping=finding.cwe_id,
                times_detected=1,
                true_positives=0,
                false_positives=0,
                last_detection=datetime.utcnow(),
                source="learned",
                learned_from_scans=[str(scan_id)],
                code_examples=[finding.code_snippet[:500]] if finding.code_snippet else [],
            )
            self.db.add(pattern)

        await self.db.commit()
        return pattern

    async def record_false_positive(
        self,
        finding_id: UUID,
        reason: str,
        feedback_by: str
    ) -> Dict[str, Any]:
        """
        Record a false positive and update pattern accuracy.

        Args:
            finding_id: The finding marked as false positive
            reason: Reason why it's a false positive
            feedback_by: Who provided the feedback

        Returns:
            Learning record and pattern update info
        """
        # Get the finding
        result = await self.db.execute(
            select(SecurityFinding).where(SecurityFinding.id == finding_id)
        )
        finding = result.scalar_one_or_none()

        if not finding:
            return {"error": "Finding not found"}

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
            language=self._detect_language(finding.file_path),
            feedback_source="human",
            feedback_reason=reason,
            feedback_by=feedback_by,
            prevents_future_fp=True,
        )
        self.db.add(learning)

        # Update or create false positive pattern
        fp_pattern = await self._create_false_positive_pattern(finding, reason)

        # Update existing vulnerability pattern accuracy
        await self._update_pattern_accuracy(finding.finding_type, finding.category, is_fp=True)

        await self.db.commit()

        return {
            "status": "success",
            "learning_id": str(learning.id),
            "pattern_id": str(fp_pattern.id) if fp_pattern else None,
            "message": "False positive recorded and patterns updated",
        }

    async def _create_false_positive_pattern(
        self,
        finding: SecurityFinding,
        reason: str
    ) -> Optional[ShadowPattern]:
        """Create or update a false positive pattern."""
        language = self._detect_language(finding.file_path)

        # Check if FP pattern already exists
        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.pattern_name == finding.finding_type,
                    ShadowPattern.pattern_type == "false_positive",
                    ShadowPattern.language == language
                )
            )
        )
        fp_pattern = result.scalar_one_or_none()

        if fp_pattern:
            # Update existing FP pattern
            fp_pattern.times_detected += 1

            # Add code example
            if finding.code_snippet:
                examples = list(fp_pattern.code_examples) if fp_pattern.code_examples else []
                if len(examples) < 20 and finding.code_snippet not in examples:
                    examples.append(finding.code_snippet[:500])
                    fp_pattern.code_examples = examples

            # Try to extract regex pattern from code
            if finding.code_snippet and len(fp_pattern.code_examples or []) >= 3:
                common_pattern = self._extract_common_pattern(fp_pattern.code_examples)
                if common_pattern:
                    fp_pattern.pattern_regex = common_pattern

        else:
            # Create new FP pattern
            fp_pattern = ShadowPattern(
                id=uuid4(),
                pattern_name=finding.finding_type,
                pattern_type="false_positive",
                category=finding.category,
                language=language,
                semantic_pattern=reason,
                code_examples=[finding.code_snippet[:500]] if finding.code_snippet else [],
                times_detected=1,
                source="learned",
                is_active=True,
            )
            self.db.add(fp_pattern)

        return fp_pattern

    async def _update_pattern_accuracy(
        self,
        finding_type: str,
        category: str,
        is_fp: bool
    ) -> None:
        """Update pattern accuracy metrics."""
        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.pattern_name == finding_type,
                    ShadowPattern.category == category,
                    ShadowPattern.pattern_type == "vulnerability"
                )
            )
        )
        pattern = result.scalar_one_or_none()

        if pattern:
            if is_fp:
                pattern.false_positives += 1
            else:
                pattern.true_positives += 1

            # Recalculate accuracy
            total = pattern.true_positives + pattern.false_positives
            if total > 0:
                pattern.accuracy_score = pattern.true_positives / total

    async def confirm_vulnerability(
        self,
        finding_id: UUID,
        confirmed_by: str
    ) -> Dict[str, Any]:
        """
        Confirm a finding as a true positive.

        Args:
            finding_id: The finding to confirm
            confirmed_by: Who confirmed it

        Returns:
            Confirmation result
        """
        # Get the finding
        result = await self.db.execute(
            select(SecurityFinding).where(SecurityFinding.id == finding_id)
        )
        finding = result.scalar_one_or_none()

        if not finding:
            return {"error": "Finding not found"}

        # Update finding
        finding.status = "confirmed"
        finding.verified = True
        finding.verified_by = confirmed_by
        finding.verified_at = datetime.utcnow()

        # Create learning record
        learning = VulnerabilityLearning(
            id=uuid4(),
            finding_id=finding_id,
            project_id=finding.project_id,
            learning_type="confirmed_vuln",
            original_classification=finding.severity,
            corrected_classification=finding.severity,
            code_context=finding.code_snippet,
            file_path=finding.file_path,
            language=self._detect_language(finding.file_path),
            feedback_source="human",
            feedback_by=confirmed_by,
        )
        self.db.add(learning)

        # Update pattern accuracy
        await self._update_pattern_accuracy(finding.finding_type, finding.category, is_fp=False)

        await self.db.commit()

        return {
            "status": "success",
            "learning_id": str(learning.id),
            "message": "Vulnerability confirmed and pattern accuracy updated",
        }

    # =========================================================================
    # PATTERN RETRIEVAL
    # =========================================================================

    async def get_patterns(
        self,
        project_type: Optional[str] = None,
        language: Optional[str] = None,
        pattern_type: str = "vulnerability",
        min_accuracy: float = 0.5,
        limit: int = 50
    ) -> List[ShadowPattern]:
        """
        Get learned patterns.

        Args:
            project_type: Optional filter by project type
            language: Optional filter by language
            pattern_type: Type of pattern (vulnerability, false_positive, secure_pattern)
            min_accuracy: Minimum accuracy score
            limit: Maximum patterns to return

        Returns:
            List of patterns
        """
        query = select(ShadowPattern).where(
            and_(
                ShadowPattern.is_active == True,
                ShadowPattern.pattern_type == pattern_type
            )
        )

        if language:
            query = query.where(ShadowPattern.language == language)

        if min_accuracy > 0 and pattern_type == "vulnerability":
            query = query.where(
                or_(
                    ShadowPattern.accuracy_score >= min_accuracy,
                    ShadowPattern.accuracy_score.is_(None)  # Include unverified
                )
            )

        query = query.order_by(
            desc(ShadowPattern.times_detected)
        ).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_false_positive_patterns(
        self,
        language: Optional[str] = None
    ) -> List[ShadowPattern]:
        """Get false positive patterns for filtering."""
        query = select(ShadowPattern).where(
            and_(
                ShadowPattern.is_active == True,
                ShadowPattern.pattern_type == "false_positive"
            )
        )

        if language:
            query = query.where(ShadowPattern.language == language)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def should_filter_finding(
        self,
        finding_type: str,
        code_snippet: str,
        file_path: str
    ) -> bool:
        """
        Check if a finding should be filtered as a likely false positive.

        Args:
            finding_type: Type of finding
            code_snippet: The code snippet
            file_path: Path to the file

        Returns:
            True if finding should be filtered
        """
        language = self._detect_language(file_path)

        # Get FP patterns for this finding type and language
        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.is_active == True,
                    ShadowPattern.pattern_type == "false_positive",
                    ShadowPattern.pattern_name == finding_type,
                    or_(
                        ShadowPattern.language == language,
                        ShadowPattern.language.is_(None)
                    )
                )
            )
        )
        fp_patterns = result.scalars().all()

        for pattern in fp_patterns:
            # Check regex pattern
            if pattern.pattern_regex:
                try:
                    if re.search(pattern.pattern_regex, code_snippet, re.IGNORECASE):
                        return True
                except re.error:
                    pass

            # Check code examples similarity
            if pattern.code_examples:
                for example in pattern.code_examples:
                    if self._code_similarity(code_snippet, example) > 0.8:
                        return True

        return False

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================

    async def get_recommendations(
        self,
        vulnerability: str,
        language: Optional[str] = None
    ) -> List[str]:
        """
        Get recommendations for a vulnerability type.

        Args:
            vulnerability: Vulnerability type (e.g., sql_injection)
            language: Optional language context

        Returns:
            List of recommendations
        """
        recommendations = []

        # Get from security knowledge
        result = await self.db.execute(
            select(SecurityKnowledge).where(
                and_(
                    SecurityKnowledge.is_active == True,
                    or_(
                        SecurityKnowledge.identifier.ilike(f"%{vulnerability}%"),
                        SecurityKnowledge.name.ilike(f"%{vulnerability.replace('_', ' ')}%")
                    )
                )
            ).limit(5)
        )
        knowledge_entries = result.scalars().all()

        for entry in knowledge_entries:
            if entry.remediation_guidance:
                recommendations.append(entry.remediation_guidance)
            if entry.prevention_techniques:
                recommendations.extend(entry.prevention_techniques[:3])

        # Get from learned patterns
        result = await self.db.execute(
            select(ShadowPattern).where(
                and_(
                    ShadowPattern.is_active == True,
                    ShadowPattern.pattern_type == "secure_pattern",
                    ShadowPattern.pattern_name.ilike(f"%{vulnerability}%")
                )
            ).limit(3)
        )
        secure_patterns = result.scalars().all()

        for pattern in secure_patterns:
            if pattern.semantic_pattern:
                recommendations.append(f"Secure pattern: {pattern.semantic_pattern}")

        # Default recommendations if none found
        if not recommendations:
            default_recs = {
                "sql_injection": [
                    "Use parameterized queries or prepared statements",
                    "Implement input validation",
                    "Apply principle of least privilege",
                ],
                "xss": [
                    "Escape output based on context",
                    "Use Content Security Policy headers",
                    "Implement input sanitization",
                ],
                "hardcoded_secret": [
                    "Use environment variables for secrets",
                    "Implement a secrets manager",
                    "Add sensitive files to .gitignore",
                ],
            }
            recommendations = default_recs.get(vulnerability, [
                f"Review and remediate {vulnerability.replace('_', ' ')} vulnerabilities"
            ])

        return list(set(recommendations))[:10]

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    async def get_learning_stats(
        self,
        project_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get learning statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Count patterns
        patterns_query = select(func.count(ShadowPattern.id))
        if project_id:
            # Filter by patterns learned from project's scans
            pass  # Complex query, simplified for now

        patterns_result = await self.db.execute(patterns_query)
        total_patterns = patterns_result.scalar() or 0

        # Count learnings
        learnings_query = select(func.count(VulnerabilityLearning.id)).where(
            VulnerabilityLearning.created_at >= since
        )
        if project_id:
            learnings_query = learnings_query.where(
                VulnerabilityLearning.project_id == project_id
            )

        learnings_result = await self.db.execute(learnings_query)
        total_learnings = learnings_result.scalar() or 0

        # Count by type
        fp_query = select(func.count(VulnerabilityLearning.id)).where(
            and_(
                VulnerabilityLearning.learning_type == "false_positive",
                VulnerabilityLearning.created_at >= since
            )
        )
        fp_result = await self.db.execute(fp_query)
        false_positives = fp_result.scalar() or 0

        confirmed_query = select(func.count(VulnerabilityLearning.id)).where(
            and_(
                VulnerabilityLearning.learning_type == "confirmed_vuln",
                VulnerabilityLearning.created_at >= since
            )
        )
        confirmed_result = await self.db.execute(confirmed_query)
        confirmed_vulns = confirmed_result.scalar() or 0

        # Average pattern accuracy
        accuracy_query = select(func.avg(ShadowPattern.accuracy_score)).where(
            and_(
                ShadowPattern.is_active == True,
                ShadowPattern.pattern_type == "vulnerability",
                ShadowPattern.accuracy_score.isnot(None)
            )
        )
        accuracy_result = await self.db.execute(accuracy_query)
        avg_accuracy = accuracy_result.scalar() or 0

        return {
            "period_days": days,
            "total_patterns": total_patterns,
            "total_learnings": total_learnings,
            "false_positives_recorded": false_positives,
            "confirmed_vulnerabilities": confirmed_vulns,
            "average_pattern_accuracy": round(avg_accuracy * 100, 1) if avg_accuracy else 0,
            "learning_rate": round(total_learnings / days, 2) if days > 0 else 0,
        }

    async def get_top_patterns(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most frequently detected patterns."""
        result = await self.db.execute(
            select(ShadowPattern)
            .where(
                and_(
                    ShadowPattern.is_active == True,
                    ShadowPattern.pattern_type == "vulnerability"
                )
            )
            .order_by(desc(ShadowPattern.times_detected))
            .limit(limit)
        )
        patterns = result.scalars().all()

        return [
            {
                "pattern_name": p.pattern_name,
                "category": p.category,
                "language": p.language,
                "severity": p.severity,
                "times_detected": p.times_detected,
                "accuracy": round(p.accuracy_score * 100, 1) if p.accuracy_score else None,
                "true_positives": p.true_positives,
                "false_positives": p.false_positives,
            }
            for p in patterns
        ]

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _detect_language(self, file_path: Optional[str]) -> Optional[str]:
        """Detect programming language from file path."""
        if not file_path:
            return None

        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang

        return None

    def _extract_common_pattern(self, code_examples: List[str]) -> Optional[str]:
        """Try to extract a common regex pattern from code examples."""
        if not code_examples or len(code_examples) < 3:
            return None

        # Simple heuristic: find common substrings
        # This is a simplified implementation
        common = code_examples[0]
        for example in code_examples[1:]:
            new_common = ""
            for i, char in enumerate(common):
                if i < len(example) and example[i] == char:
                    new_common += char
                else:
                    break
            common = new_common

        if len(common) > 10:
            # Escape for regex
            return re.escape(common)

        return None

    def _code_similarity(self, code1: str, code2: str) -> float:
        """Calculate simple similarity between code snippets."""
        if not code1 or not code2:
            return 0.0

        # Normalize
        code1 = code1.lower().strip()
        code2 = code2.lower().strip()

        if code1 == code2:
            return 1.0

        # Token-based similarity
        tokens1 = set(re.findall(r'\w+', code1))
        tokens2 = set(re.findall(r'\w+', code2))

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union)


# Factory function
def get_shadow_graph_service(db: AsyncSession) -> ShadowGraphService:
    """Get ShadowGraph service instance."""
    return ShadowGraphService(db)
