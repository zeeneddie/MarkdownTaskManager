# NFR Priority Scorer - Week 102: NFR Quick Wins
# NFR-QW-2: Priority scoring based on category weights

"""
NFR Priority Scorer

Calculates priority scores for Non-Functional Requirements based on:
- Category importance (security > performance > usability)
- Business impact assessment
- Risk if not met
- Implementation effort
- Testability/measurability
- Industry/domain context

Produces:
- Priority score (1-100)
- Priority tier (Critical, High, Medium, Low)
- Justification for scoring
- Suggested implementation order
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re


class NFRCategory(Enum):
    """Categories of Non-Functional Requirements."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    RELIABILITY = "reliability"
    SCALABILITY = "scalability"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"
    PORTABILITY = "portability"
    COMPLIANCE = "compliance"
    CAPACITY = "capacity"


class PriorityTier(Enum):
    """Priority tiers for NFRs."""
    CRITICAL = "critical"   # 85-100: Must-have, blocks release
    HIGH = "high"           # 70-84: Important, should have
    MEDIUM = "medium"       # 50-69: Nice to have
    LOW = "low"             # 0-49: Can defer


class BusinessDomain(Enum):
    """Business domain for context-aware scoring."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    GOVERNMENT = "government"
    SOCIAL = "social"
    GAMING = "gaming"
    ENTERPRISE = "enterprise"
    STARTUP = "startup"
    GENERIC = "generic"


class RiskLevel(Enum):
    """Risk level if NFR is not met."""
    CATASTROPHIC = "catastrophic"  # Business-ending, legal liability
    SEVERE = "severe"              # Major revenue/reputation loss
    MODERATE = "moderate"          # Notable impact
    MINOR = "minor"                # Some inconvenience
    NEGLIGIBLE = "negligible"      # Minimal impact


@dataclass
class ScoringFactor:
    """A factor that contributes to the priority score."""
    name: str
    weight: float       # How much this factor matters (0-1)
    score: float        # Score for this factor (0-100)
    justification: str  # Why this score was given


@dataclass
class NFRInput:
    """Input NFR for priority scoring."""
    category: NFRCategory
    description: str
    has_metric: bool = True
    metric_value: Optional[str] = None
    stakeholder: Optional[str] = None
    source: Optional[str] = None  # e.g., "customer requirement", "compliance"

    @classmethod
    def from_text(cls, text: str, category: Optional[NFRCategory] = None) -> "NFRInput":
        """Create NFRInput from text description."""
        if category is None:
            category = cls._detect_category(text)

        has_metric = bool(re.search(r"\d+(?:\.\d+)?(?:\s*%|\s*ms|\s*s|\s*users?)", text))

        return cls(
            category=category,
            description=text,
            has_metric=has_metric
        )

    @staticmethod
    def _detect_category(text: str) -> NFRCategory:
        """Auto-detect NFR category from text."""
        text_lower = text.lower()

        category_keywords = {
            NFRCategory.SECURITY: ["security", "encrypt", "auth", "password", "token"],
            NFRCategory.PERFORMANCE: ["response time", "latency", "throughput", "speed"],
            NFRCategory.AVAILABILITY: ["uptime", "availability", "downtime", "sla"],
            NFRCategory.RELIABILITY: ["reliability", "mtbf", "error rate", "failure"],
            NFRCategory.SCALABILITY: ["scale", "concurrent", "users", "load"],
            NFRCategory.USABILITY: ["usability", "accessibility", "user experience"],
            NFRCategory.MAINTAINABILITY: ["maintain", "code quality", "documentation"],
            NFRCategory.COMPLIANCE: ["gdpr", "hipaa", "compliance", "regulation"],
            NFRCategory.CAPACITY: ["storage", "memory", "capacity", "disk"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return category

        return NFRCategory.PERFORMANCE  # Default


@dataclass
class NFRPriorityResult:
    """Result of priority scoring for an NFR."""
    nfr: NFRInput
    overall_score: float      # 0-100
    priority_tier: PriorityTier
    factors: List[ScoringFactor]
    justification: str
    implementation_order: int  # Suggested order (1 = first)
    estimated_effort: str     # "low", "medium", "high"
    risk_if_skipped: RiskLevel

    def to_dict(self) -> dict:
        return {
            "description": self.nfr.description,
            "category": self.nfr.category.value,
            "overall_score": round(self.overall_score, 1),
            "priority_tier": self.priority_tier.value,
            "factors": [
                {
                    "name": f.name,
                    "weight": f.weight,
                    "score": round(f.score, 1),
                    "justification": f.justification
                }
                for f in self.factors
            ],
            "justification": self.justification,
            "implementation_order": self.implementation_order,
            "estimated_effort": self.estimated_effort,
            "risk_if_skipped": self.risk_if_skipped.value
        }


@dataclass
class BulkPriorityResult:
    """Result of prioritizing multiple NFRs."""
    nfrs: List[NFRPriorityResult]
    ordered_nfrs: List[NFRPriorityResult]  # Sorted by priority
    statistics: Dict[str, Any]
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            "total_nfrs": len(self.nfrs),
            "nfrs": [n.to_dict() for n in self.ordered_nfrs],
            "statistics": self.statistics,
            "recommendations": self.recommendations
        }


class NFRPriorityScorer:
    """
    Calculates priority scores for Non-Functional Requirements.

    Uses multiple factors:
    - Category base importance
    - Business domain context
    - Risk assessment
    - Metric clarity (testability)
    - Stakeholder source

    Usage:
        scorer = NFRPriorityScorer(domain=BusinessDomain.HEALTHCARE)

        nfr = NFRInput(
            category=NFRCategory.SECURITY,
            description="All PHI must be encrypted at rest with AES-256",
            has_metric=True
        )
        result = scorer.score(nfr)
        print(f"Priority: {result.priority_tier.value}, Score: {result.overall_score}")
    """

    # Base category weights (sum doesn't need to equal 1, these are multipliers)
    DEFAULT_CATEGORY_WEIGHTS = {
        NFRCategory.SECURITY: 0.95,
        NFRCategory.COMPLIANCE: 0.90,
        NFRCategory.AVAILABILITY: 0.85,
        NFRCategory.RELIABILITY: 0.80,
        NFRCategory.PERFORMANCE: 0.75,
        NFRCategory.SCALABILITY: 0.70,
        NFRCategory.CAPACITY: 0.65,
        NFRCategory.USABILITY: 0.60,
        NFRCategory.MAINTAINABILITY: 0.55,
        NFRCategory.PORTABILITY: 0.50,
    }

    # Domain-specific weight adjustments
    DOMAIN_ADJUSTMENTS = {
        BusinessDomain.HEALTHCARE: {
            NFRCategory.SECURITY: 1.2,
            NFRCategory.COMPLIANCE: 1.3,  # HIPAA critical
            NFRCategory.AVAILABILITY: 1.1,
        },
        BusinessDomain.FINANCE: {
            NFRCategory.SECURITY: 1.2,
            NFRCategory.RELIABILITY: 1.2,
            NFRCategory.COMPLIANCE: 1.2,  # PCI-DSS, SOX
            NFRCategory.PERFORMANCE: 1.1,
        },
        BusinessDomain.ECOMMERCE: {
            NFRCategory.PERFORMANCE: 1.3,  # Speed = revenue
            NFRCategory.SCALABILITY: 1.2,  # Handle traffic
            NFRCategory.AVAILABILITY: 1.2,
        },
        BusinessDomain.GAMING: {
            NFRCategory.PERFORMANCE: 1.3,
            NFRCategory.SCALABILITY: 1.2,
            NFRCategory.USABILITY: 1.1,
        },
        BusinessDomain.GOVERNMENT: {
            NFRCategory.SECURITY: 1.3,
            NFRCategory.COMPLIANCE: 1.3,
            NFRCategory.AVAILABILITY: 1.1,
        },
        BusinessDomain.SOCIAL: {
            NFRCategory.SCALABILITY: 1.3,
            NFRCategory.PERFORMANCE: 1.2,
            NFRCategory.USABILITY: 1.1,
        },
        BusinessDomain.ENTERPRISE: {
            NFRCategory.SECURITY: 1.1,
            NFRCategory.RELIABILITY: 1.2,
            NFRCategory.MAINTAINABILITY: 1.1,
        },
        BusinessDomain.STARTUP: {
            NFRCategory.PERFORMANCE: 1.1,
            NFRCategory.USABILITY: 1.2,
            NFRCategory.SCALABILITY: 1.0,  # Can delay
            NFRCategory.MAINTAINABILITY: 0.8,
        },
    }

    # Risk keywords
    RISK_INDICATORS = {
        RiskLevel.CATASTROPHIC: [
            "breach", "data loss", "legal", "lawsuit", "compliance violation",
            "patient safety", "financial loss", "life-threatening",
        ],
        RiskLevel.SEVERE: [
            "outage", "revenue loss", "reputation", "customer churn",
            "regulatory fine", "security incident",
        ],
        RiskLevel.MODERATE: [
            "degraded", "slow", "frustrated users", "support tickets",
            "workaround", "manual process",
        ],
        RiskLevel.MINOR: [
            "inconvenient", "suboptimal", "could be better",
        ],
    }

    # Stakeholder importance
    STAKEHOLDER_WEIGHTS = {
        "executive": 1.2,
        "customer": 1.15,
        "regulator": 1.25,
        "compliance": 1.2,
        "security": 1.15,
        "operations": 1.0,
        "development": 0.9,
        "internal": 0.85,
    }

    # Source importance
    SOURCE_WEIGHTS = {
        "compliance": 1.3,
        "legal": 1.25,
        "customer requirement": 1.15,
        "contract": 1.2,
        "sla": 1.15,
        "internal": 0.9,
        "nice to have": 0.7,
    }

    def __init__(
        self,
        domain: BusinessDomain = BusinessDomain.GENERIC,
        custom_category_weights: Optional[Dict[NFRCategory, float]] = None,
        risk_multiplier: float = 1.0
    ):
        """
        Initialize the scorer.

        Args:
            domain: Business domain for context-aware scoring
            custom_category_weights: Override default category weights
            risk_multiplier: Multiplier for risk factor (higher = more risk-averse)
        """
        self.domain = domain
        self.risk_multiplier = risk_multiplier

        # Apply domain adjustments to base weights
        self.category_weights = self.DEFAULT_CATEGORY_WEIGHTS.copy()
        if custom_category_weights:
            self.category_weights.update(custom_category_weights)

        domain_adj = self.DOMAIN_ADJUSTMENTS.get(domain, {})
        for category, adjustment in domain_adj.items():
            if category in self.category_weights:
                self.category_weights[category] *= adjustment

    def score(self, nfr: NFRInput) -> NFRPriorityResult:
        """
        Calculate priority score for a single NFR.

        Args:
            nfr: The NFR to score

        Returns:
            NFRPriorityResult with score and justification
        """
        factors = []

        # Factor 1: Category importance (40% weight)
        category_factor = self._score_category(nfr)
        factors.append(category_factor)

        # Factor 2: Risk if not met (25% weight)
        risk_factor = self._score_risk(nfr)
        factors.append(risk_factor)

        # Factor 3: Testability/Measurability (15% weight)
        testability_factor = self._score_testability(nfr)
        factors.append(testability_factor)

        # Factor 4: Stakeholder/Source importance (10% weight)
        stakeholder_factor = self._score_stakeholder(nfr)
        factors.append(stakeholder_factor)

        # Factor 5: Domain relevance (10% weight)
        domain_factor = self._score_domain_relevance(nfr)
        factors.append(domain_factor)

        # Calculate weighted average
        total_weight = sum(f.weight for f in factors)
        overall_score = sum(f.score * f.weight for f in factors) / total_weight

        # Apply risk multiplier
        overall_score = min(100, overall_score * (1 + (self.risk_multiplier - 1) * 0.1))

        # Determine tier
        priority_tier = self._score_to_tier(overall_score)

        # Assess risk level
        risk_level = self._assess_risk_level(nfr)

        # Estimate effort
        effort = self._estimate_effort(nfr)

        # Generate justification
        justification = self._generate_justification(nfr, factors, overall_score)

        return NFRPriorityResult(
            nfr=nfr,
            overall_score=overall_score,
            priority_tier=priority_tier,
            factors=factors,
            justification=justification,
            implementation_order=0,  # Set during bulk scoring
            estimated_effort=effort,
            risk_if_skipped=risk_level
        )

    def score_bulk(self, nfrs: List[NFRInput]) -> BulkPriorityResult:
        """
        Score and prioritize multiple NFRs.

        Args:
            nfrs: List of NFRs to score

        Returns:
            BulkPriorityResult with ordered NFRs
        """
        # Score each NFR
        results = [self.score(nfr) for nfr in nfrs]

        # Sort by score (highest first)
        ordered = sorted(results, key=lambda r: r.overall_score, reverse=True)

        # Assign implementation order
        for i, result in enumerate(ordered):
            result.implementation_order = i + 1

        # Generate statistics
        statistics = self._generate_statistics(ordered)

        # Generate recommendations
        recommendations = self._generate_recommendations(ordered)

        return BulkPriorityResult(
            nfrs=results,
            ordered_nfrs=ordered,
            statistics=statistics,
            recommendations=recommendations
        )

    def _score_category(self, nfr: NFRInput) -> ScoringFactor:
        """Score based on category importance."""
        base_weight = self.category_weights.get(nfr.category, 0.5)

        # Convert weight to 0-100 score
        score = base_weight * 100

        return ScoringFactor(
            name="Category Importance",
            weight=0.40,
            score=min(100, score),
            justification=f"{nfr.category.value} has base importance of {base_weight:.2f}"
        )

    def _score_risk(self, nfr: NFRInput) -> ScoringFactor:
        """Score based on risk if NFR is not met."""
        description_lower = nfr.description.lower()

        # Check for risk indicators
        for risk_level, keywords in self.RISK_INDICATORS.items():
            if any(kw in description_lower for kw in keywords):
                if risk_level == RiskLevel.CATASTROPHIC:
                    score = 100
                    justification = "Contains catastrophic risk indicators"
                elif risk_level == RiskLevel.SEVERE:
                    score = 85
                    justification = "Contains severe risk indicators"
                elif risk_level == RiskLevel.MODERATE:
                    score = 65
                    justification = "Contains moderate risk indicators"
                else:
                    score = 45
                    justification = "Contains minor risk indicators"

                return ScoringFactor(
                    name="Risk Impact",
                    weight=0.25 * self.risk_multiplier,
                    score=score,
                    justification=justification
                )

        # Default based on category
        category_risk = {
            NFRCategory.SECURITY: 85,
            NFRCategory.COMPLIANCE: 80,
            NFRCategory.AVAILABILITY: 75,
            NFRCategory.RELIABILITY: 70,
            NFRCategory.PERFORMANCE: 60,
            NFRCategory.SCALABILITY: 55,
        }

        score = category_risk.get(nfr.category, 50)

        return ScoringFactor(
            name="Risk Impact",
            weight=0.25 * self.risk_multiplier,
            score=score,
            justification=f"Default risk for {nfr.category.value} category"
        )

    def _score_testability(self, nfr: NFRInput) -> ScoringFactor:
        """Score based on testability/measurability."""
        score = 50  # Base score

        # Has quantitative metric
        if nfr.has_metric:
            score += 30

        # Has specific value mentioned
        if nfr.metric_value:
            score += 10

        # Check for measurable language
        measurable_terms = [
            "must be", "shall", "at least", "at most", "within",
            "less than", "greater than", "exactly", "between"
        ]
        if any(term in nfr.description.lower() for term in measurable_terms):
            score += 10

        justification = "Testable" if score >= 70 else "Needs clearer metrics"

        return ScoringFactor(
            name="Testability",
            weight=0.15,
            score=min(100, score),
            justification=justification
        )

    def _score_stakeholder(self, nfr: NFRInput) -> ScoringFactor:
        """Score based on stakeholder/source importance."""
        score = 50  # Base score
        justification_parts = []

        # Check stakeholder
        if nfr.stakeholder:
            stakeholder_lower = nfr.stakeholder.lower()
            for stakeholder, weight in self.STAKEHOLDER_WEIGHTS.items():
                if stakeholder in stakeholder_lower:
                    score *= weight
                    justification_parts.append(f"Stakeholder: {stakeholder}")
                    break

        # Check source
        if nfr.source:
            source_lower = nfr.source.lower()
            for source, weight in self.SOURCE_WEIGHTS.items():
                if source in source_lower:
                    score *= weight
                    justification_parts.append(f"Source: {source}")
                    break

        justification = ", ".join(justification_parts) if justification_parts else "Standard stakeholder"

        return ScoringFactor(
            name="Stakeholder Priority",
            weight=0.10,
            score=min(100, score),
            justification=justification
        )

    def _score_domain_relevance(self, nfr: NFRInput) -> ScoringFactor:
        """Score based on relevance to business domain."""
        # Get domain-specific critical categories
        domain_critical = {
            BusinessDomain.HEALTHCARE: [NFRCategory.SECURITY, NFRCategory.COMPLIANCE, NFRCategory.AVAILABILITY],
            BusinessDomain.FINANCE: [NFRCategory.SECURITY, NFRCategory.RELIABILITY, NFRCategory.COMPLIANCE],
            BusinessDomain.ECOMMERCE: [NFRCategory.PERFORMANCE, NFRCategory.AVAILABILITY, NFRCategory.SCALABILITY],
            BusinessDomain.GAMING: [NFRCategory.PERFORMANCE, NFRCategory.SCALABILITY],
            BusinessDomain.GOVERNMENT: [NFRCategory.SECURITY, NFRCategory.COMPLIANCE],
        }

        critical_categories = domain_critical.get(self.domain, [])

        if nfr.category in critical_categories:
            score = 90
            justification = f"{nfr.category.value} is critical for {self.domain.value}"
        else:
            score = 60
            justification = f"Standard relevance for {self.domain.value}"

        return ScoringFactor(
            name="Domain Relevance",
            weight=0.10,
            score=score,
            justification=justification
        )

    def _score_to_tier(self, score: float) -> PriorityTier:
        """Convert score to priority tier."""
        if score >= 85:
            return PriorityTier.CRITICAL
        elif score >= 70:
            return PriorityTier.HIGH
        elif score >= 50:
            return PriorityTier.MEDIUM
        else:
            return PriorityTier.LOW

    def _assess_risk_level(self, nfr: NFRInput) -> RiskLevel:
        """Assess the risk level if NFR is not met."""
        description_lower = nfr.description.lower()

        for risk_level, keywords in self.RISK_INDICATORS.items():
            if any(kw in description_lower for kw in keywords):
                return risk_level

        # Default based on category
        category_risk = {
            NFRCategory.SECURITY: RiskLevel.SEVERE,
            NFRCategory.COMPLIANCE: RiskLevel.SEVERE,
            NFRCategory.AVAILABILITY: RiskLevel.MODERATE,
            NFRCategory.RELIABILITY: RiskLevel.MODERATE,
        }

        return category_risk.get(nfr.category, RiskLevel.MINOR)

    def _estimate_effort(self, nfr: NFRInput) -> str:
        """Estimate implementation effort."""
        description_lower = nfr.description.lower()

        # High effort indicators
        high_effort = ["entire system", "all data", "complete", "comprehensive", "end-to-end"]
        if any(term in description_lower for term in high_effort):
            return "high"

        # Low effort indicators
        low_effort = ["single", "one", "specific", "simple", "basic"]
        if any(term in description_lower for term in low_effort):
            return "low"

        # Category-based defaults
        high_effort_categories = [NFRCategory.SECURITY, NFRCategory.SCALABILITY, NFRCategory.COMPLIANCE]
        if nfr.category in high_effort_categories:
            return "high"

        low_effort_categories = [NFRCategory.USABILITY]
        if nfr.category in low_effort_categories:
            return "low"

        return "medium"

    def _generate_justification(
        self,
        nfr: NFRInput,
        factors: List[ScoringFactor],
        overall_score: float
    ) -> str:
        """Generate human-readable justification."""
        tier = self._score_to_tier(overall_score)

        # Find top contributing factors
        sorted_factors = sorted(factors, key=lambda f: f.score * f.weight, reverse=True)
        top_factor = sorted_factors[0]

        justification = f"{tier.value.capitalize()} priority ({overall_score:.0f}/100): "
        justification += f"Primarily driven by {top_factor.name.lower()} ({top_factor.justification}). "

        if nfr.category in [NFRCategory.SECURITY, NFRCategory.COMPLIANCE]:
            justification += "This NFR is non-negotiable for compliance."
        elif overall_score >= 85:
            justification += "Should be addressed before release."
        elif overall_score >= 70:
            justification += "Plan to address in current sprint if possible."

        return justification

    def _generate_statistics(self, ordered: List[NFRPriorityResult]) -> Dict[str, Any]:
        """Generate statistics about the scored NFRs."""
        tier_counts = {tier: 0 for tier in PriorityTier}
        category_counts = {}
        effort_counts = {"low": 0, "medium": 0, "high": 0}

        for result in ordered:
            tier_counts[result.priority_tier] += 1
            cat = result.nfr.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            effort_counts[result.estimated_effort] += 1

        return {
            "total": len(ordered),
            "by_tier": {t.value: c for t, c in tier_counts.items()},
            "by_category": category_counts,
            "by_effort": effort_counts,
            "average_score": sum(r.overall_score for r in ordered) / len(ordered) if ordered else 0,
            "critical_count": tier_counts[PriorityTier.CRITICAL],
        }

    def _generate_recommendations(self, ordered: List[NFRPriorityResult]) -> List[str]:
        """Generate recommendations based on scored NFRs."""
        recommendations = []

        # Critical NFRs
        critical = [r for r in ordered if r.priority_tier == PriorityTier.CRITICAL]
        if critical:
            recommendations.append(
                f"{len(critical)} critical NFR(s) must be addressed before release"
            )

        # Security gaps
        security_nfrs = [r for r in ordered if r.nfr.category == NFRCategory.SECURITY]
        if not security_nfrs:
            recommendations.append(
                "No security NFRs detected - consider adding security requirements"
            )

        # Compliance gaps
        if self.domain in [BusinessDomain.HEALTHCARE, BusinessDomain.FINANCE, BusinessDomain.GOVERNMENT]:
            compliance_nfrs = [r for r in ordered if r.nfr.category == NFRCategory.COMPLIANCE]
            if not compliance_nfrs:
                recommendations.append(
                    f"No compliance NFRs for {self.domain.value} domain - review regulatory requirements"
                )

        # High effort critical items
        high_effort_critical = [r for r in critical if r.estimated_effort == "high"]
        if high_effort_critical:
            recommendations.append(
                f"{len(high_effort_critical)} critical NFR(s) require high effort - plan accordingly"
            )

        # Untestable NFRs
        untestable = [r for r in ordered if not r.nfr.has_metric]
        if untestable:
            recommendations.append(
                f"{len(untestable)} NFR(s) lack quantitative metrics - add measurable criteria"
            )

        return recommendations


# Convenience functions
def score_nfr(
    description: str,
    category: Optional[NFRCategory] = None,
    domain: BusinessDomain = BusinessDomain.GENERIC
) -> NFRPriorityResult:
    """
    Score a single NFR from description.

    Args:
        description: NFR description text
        category: Optional category (auto-detected if not provided)
        domain: Business domain for context

    Returns:
        NFRPriorityResult with score and tier
    """
    nfr = NFRInput.from_text(description, category)
    scorer = NFRPriorityScorer(domain=domain)
    return scorer.score(nfr)


def prioritize_nfrs(
    descriptions: List[str],
    domain: BusinessDomain = BusinessDomain.GENERIC
) -> List[NFRPriorityResult]:
    """
    Prioritize multiple NFRs.

    Args:
        descriptions: List of NFR descriptions
        domain: Business domain for context

    Returns:
        List of NFRPriorityResult ordered by priority
    """
    nfrs = [NFRInput.from_text(d) for d in descriptions]
    scorer = NFRPriorityScorer(domain=domain)
    result = scorer.score_bulk(nfrs)
    return result.ordered_nfrs


def get_priority_tier(
    description: str,
    domain: BusinessDomain = BusinessDomain.GENERIC
) -> PriorityTier:
    """
    Get priority tier for an NFR.

    Args:
        description: NFR description
        domain: Business domain

    Returns:
        PriorityTier enum value
    """
    result = score_nfr(description, domain=domain)
    return result.priority_tier
