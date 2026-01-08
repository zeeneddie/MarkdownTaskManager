"""
Domain Vocabulary Loader - Week 101

Pre-built vocabularies for common business domains to accelerate
business rule extraction and improve detection accuracy.

Domains supported:
- Healthcare (NEN7510, HIPAA compliance terminology)
- Finance (PCI-DSS, SOX compliance terminology)
- E-Commerce (GDPR, consumer protection terminology)

Usage:
    loader = DomainVocabularyLoader()

    # Auto-detect domain from code
    domain = loader.detect_domain(source_code)

    # Get vocabulary for a domain
    vocab = loader.get_vocabulary("healthcare")

    # Check if a term matches domain patterns
    matches = loader.find_domain_terms(source_code, "finance")
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter


class BusinessDomain(Enum):
    """Supported business domains."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    GENERIC = "generic"


@dataclass
class DomainTerm:
    """Represents a domain-specific term."""
    term: str
    category: str
    description: str
    synonyms: List[str] = field(default_factory=list)
    compliance_related: bool = False
    compliance_standards: List[str] = field(default_factory=list)


@dataclass
class DomainVocabulary:
    """Complete vocabulary for a business domain."""
    domain: BusinessDomain
    terms: Dict[str, DomainTerm] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    compliance_standards: List[str] = field(default_factory=list)
    entity_prefixes: List[str] = field(default_factory=list)
    common_abbreviations: Dict[str, str] = field(default_factory=dict)

    def get_all_terms(self) -> Set[str]:
        """Get all terms including synonyms."""
        all_terms = set(self.terms.keys())
        for term in self.terms.values():
            all_terms.update(term.synonyms)
        return all_terms


class DomainVocabularyLoader:
    """
    Loads and manages domain-specific vocabularies.

    Provides pre-built vocabularies for common business domains
    and can auto-detect domains from source code.
    """

    def __init__(self):
        self._vocabularies: Dict[BusinessDomain, DomainVocabulary] = {}
        self._load_default_vocabularies()

    def _load_default_vocabularies(self) -> None:
        """Load all pre-built vocabularies."""
        self._vocabularies[BusinessDomain.HEALTHCARE] = self._build_healthcare_vocabulary()
        self._vocabularies[BusinessDomain.FINANCE] = self._build_finance_vocabulary()
        self._vocabularies[BusinessDomain.ECOMMERCE] = self._build_ecommerce_vocabulary()
        self._vocabularies[BusinessDomain.GENERIC] = self._build_generic_vocabulary()

    # =========================================================================
    # Healthcare Domain
    # =========================================================================

    def _build_healthcare_vocabulary(self) -> DomainVocabulary:
        """Build vocabulary for healthcare domain."""
        vocab = DomainVocabulary(
            domain=BusinessDomain.HEALTHCARE,
            compliance_standards=["NEN7510", "HIPAA", "GDPR", "HL7", "FHIR"],
            entity_prefixes=["patient", "doctor", "nurse", "clinic", "hospital"],
            common_abbreviations={
                "EMR": "Electronic Medical Record",
                "EHR": "Electronic Health Record",
                "PHI": "Protected Health Information",
                "HIPAA": "Health Insurance Portability and Accountability Act",
                "ICD": "International Classification of Diseases",
                "CPT": "Current Procedural Terminology",
                "NPI": "National Provider Identifier",
                "BSN": "Burger Service Nummer",
            },
            patterns=[
                r"patient[_\s]?id",
                r"diagnosis",
                r"prescription",
                r"medical[_\s]?record",
                r"treatment[_\s]?plan",
                r"appointment",
                r"health[_\s]?insurance",
                r"bsn",  # Dutch citizen ID
                r"hipaa",
                r"nen[_\s]?7510",
            ],
        )

        # Core entities
        vocab.terms["patient"] = DomainTerm(
            term="patient",
            category="entity",
            description="Person receiving medical care",
            synonyms=["client", "subject", "individual"],
            compliance_related=True,
            compliance_standards=["HIPAA", "NEN7510"],
        )

        vocab.terms["diagnosis"] = DomainTerm(
            term="diagnosis",
            category="medical",
            description="Identification of disease or condition",
            synonyms=["condition", "assessment", "finding"],
        )

        vocab.terms["prescription"] = DomainTerm(
            term="prescription",
            category="medical",
            description="Medication order from healthcare provider",
            synonyms=["medication_order", "rx", "drug_order"],
        )

        vocab.terms["appointment"] = DomainTerm(
            term="appointment",
            category="scheduling",
            description="Scheduled patient visit",
            synonyms=["visit", "encounter", "booking", "consult"],
        )

        vocab.terms["healthcare_provider"] = DomainTerm(
            term="healthcare_provider",
            category="entity",
            description="Person or organization delivering care",
            synonyms=["doctor", "physician", "nurse", "clinician", "practitioner"],
        )

        vocab.terms["medical_record"] = DomainTerm(
            term="medical_record",
            category="data",
            description="Patient health information documentation",
            synonyms=["health_record", "chart", "emr", "ehr"],
            compliance_related=True,
            compliance_standards=["HIPAA", "NEN7510"],
        )

        vocab.terms["insurance_claim"] = DomainTerm(
            term="insurance_claim",
            category="billing",
            description="Request for payment to insurance",
            synonyms=["claim", "reimbursement_request"],
        )

        vocab.terms["consent"] = DomainTerm(
            term="consent",
            category="compliance",
            description="Patient authorization for treatment or data use",
            synonyms=["authorization", "permission", "approval"],
            compliance_related=True,
            compliance_standards=["HIPAA", "GDPR", "NEN7510"],
        )

        return vocab

    # =========================================================================
    # Finance Domain
    # =========================================================================

    def _build_finance_vocabulary(self) -> DomainVocabulary:
        """Build vocabulary for finance domain."""
        vocab = DomainVocabulary(
            domain=BusinessDomain.FINANCE,
            compliance_standards=["PCI-DSS", "SOX", "GDPR", "AML", "KYC", "MiFID II"],
            entity_prefixes=["account", "customer", "transaction", "payment", "bank"],
            common_abbreviations={
                "AML": "Anti-Money Laundering",
                "KYC": "Know Your Customer",
                "PCI": "Payment Card Industry",
                "DSS": "Data Security Standard",
                "SOX": "Sarbanes-Oxley Act",
                "IBAN": "International Bank Account Number",
                "BIC": "Bank Identifier Code",
                "SWIFT": "Society for Worldwide Interbank Financial Telecommunication",
                "ACH": "Automated Clearing House",
            },
            patterns=[
                r"account[_\s]?number",
                r"transaction[_\s]?id",
                r"payment",
                r"credit[_\s]?card",
                r"debit",
                r"balance",
                r"transfer",
                r"iban",
                r"pci[_\s]?dss",
                r"kyc",
                r"aml",
            ],
        )

        # Core entities
        vocab.terms["account"] = DomainTerm(
            term="account",
            category="entity",
            description="Financial account holding funds or value",
            synonyms=["bank_account", "savings", "checking"],
            compliance_related=True,
            compliance_standards=["PCI-DSS", "SOX"],
        )

        vocab.terms["transaction"] = DomainTerm(
            term="transaction",
            category="operation",
            description="Financial operation affecting account balance",
            synonyms=["transfer", "payment", "debit", "credit"],
            compliance_related=True,
            compliance_standards=["PCI-DSS", "AML"],
        )

        vocab.terms["payment"] = DomainTerm(
            term="payment",
            category="operation",
            description="Transfer of funds for goods or services",
            synonyms=["remittance", "settlement", "disbursement"],
        )

        vocab.terms["credit_card"] = DomainTerm(
            term="credit_card",
            category="instrument",
            description="Payment card with credit line",
            synonyms=["card", "cc", "payment_card"],
            compliance_related=True,
            compliance_standards=["PCI-DSS"],
        )

        vocab.terms["customer"] = DomainTerm(
            term="customer",
            category="entity",
            description="Person or entity using financial services",
            synonyms=["client", "account_holder", "member"],
            compliance_related=True,
            compliance_standards=["KYC", "AML", "GDPR"],
        )

        vocab.terms["balance"] = DomainTerm(
            term="balance",
            category="value",
            description="Current amount in an account",
            synonyms=["available_balance", "ledger_balance", "funds"],
        )

        vocab.terms["interest"] = DomainTerm(
            term="interest",
            category="calculation",
            description="Cost of borrowing or return on deposits",
            synonyms=["rate", "apr", "yield"],
        )

        vocab.terms["fraud"] = DomainTerm(
            term="fraud",
            category="risk",
            description="Deceptive financial activity",
            synonyms=["suspicious_activity", "unauthorized", "fraud_detection"],
            compliance_related=True,
            compliance_standards=["AML", "PCI-DSS"],
        )

        vocab.terms["verification"] = DomainTerm(
            term="verification",
            category="process",
            description="Identity or transaction confirmation",
            synonyms=["authentication", "validation", "confirmation"],
            compliance_related=True,
            compliance_standards=["KYC", "PCI-DSS"],
        )

        return vocab

    # =========================================================================
    # E-Commerce Domain
    # =========================================================================

    def _build_ecommerce_vocabulary(self) -> DomainVocabulary:
        """Build vocabulary for e-commerce domain."""
        vocab = DomainVocabulary(
            domain=BusinessDomain.ECOMMERCE,
            compliance_standards=["GDPR", "CCPA", "PCI-DSS", "Consumer Rights"],
            entity_prefixes=["product", "order", "cart", "customer", "shop"],
            common_abbreviations={
                "SKU": "Stock Keeping Unit",
                "UPC": "Universal Product Code",
                "EAN": "European Article Number",
                "COD": "Cash on Delivery",
                "RMA": "Return Merchandise Authorization",
                "AOV": "Average Order Value",
                "GMV": "Gross Merchandise Value",
                "CVR": "Conversion Rate",
            },
            patterns=[
                r"product[_\s]?id",
                r"order[_\s]?id",
                r"cart",
                r"checkout",
                r"inventory",
                r"shipping",
                r"catalog",
                r"sku",
                r"gdpr",
                r"consent",
            ],
        )

        # Core entities
        vocab.terms["product"] = DomainTerm(
            term="product",
            category="entity",
            description="Item available for purchase",
            synonyms=["item", "article", "sku", "merchandise"],
        )

        vocab.terms["order"] = DomainTerm(
            term="order",
            category="entity",
            description="Customer purchase request",
            synonyms=["purchase", "transaction", "booking"],
        )

        vocab.terms["cart"] = DomainTerm(
            term="cart",
            category="entity",
            description="Collection of items for purchase",
            synonyms=["basket", "shopping_cart", "bag"],
        )

        vocab.terms["customer"] = DomainTerm(
            term="customer",
            category="entity",
            description="Person making purchases",
            synonyms=["buyer", "shopper", "user", "client"],
            compliance_related=True,
            compliance_standards=["GDPR", "CCPA"],
        )

        vocab.terms["inventory"] = DomainTerm(
            term="inventory",
            category="management",
            description="Stock of available products",
            synonyms=["stock", "warehouse", "availability"],
        )

        vocab.terms["shipping"] = DomainTerm(
            term="shipping",
            category="logistics",
            description="Product delivery process",
            synonyms=["delivery", "fulfillment", "dispatch"],
        )

        vocab.terms["checkout"] = DomainTerm(
            term="checkout",
            category="process",
            description="Purchase completion process",
            synonyms=["purchase", "payment_flow", "order_completion"],
        )

        vocab.terms["return"] = DomainTerm(
            term="return",
            category="process",
            description="Product return by customer",
            synonyms=["refund", "rma", "exchange"],
            compliance_related=True,
            compliance_standards=["Consumer Rights"],
        )

        vocab.terms["discount"] = DomainTerm(
            term="discount",
            category="pricing",
            description="Price reduction on products",
            synonyms=["promotion", "coupon", "sale", "offer"],
        )

        vocab.terms["wishlist"] = DomainTerm(
            term="wishlist",
            category="feature",
            description="Customer saved items list",
            synonyms=["favorites", "saved_items", "watch_list"],
        )

        return vocab

    # =========================================================================
    # Generic Domain
    # =========================================================================

    def _build_generic_vocabulary(self) -> DomainVocabulary:
        """Build generic vocabulary applicable to all domains."""
        vocab = DomainVocabulary(
            domain=BusinessDomain.GENERIC,
            compliance_standards=["GDPR", "Security Best Practices"],
            entity_prefixes=["user", "admin", "system"],
            common_abbreviations={
                "CRUD": "Create, Read, Update, Delete",
                "API": "Application Programming Interface",
                "DTO": "Data Transfer Object",
                "SSO": "Single Sign-On",
                "MFA": "Multi-Factor Authentication",
                "RBAC": "Role-Based Access Control",
            },
            patterns=[
                r"user[_\s]?id",
                r"email",
                r"password",
                r"role",
                r"permission",
                r"authentication",
                r"authorization",
            ],
        )

        vocab.terms["user"] = DomainTerm(
            term="user",
            category="entity",
            description="System user or actor",
            synonyms=["account", "member", "participant"],
            compliance_related=True,
            compliance_standards=["GDPR"],
        )

        vocab.terms["role"] = DomainTerm(
            term="role",
            category="authorization",
            description="User permission grouping",
            synonyms=["permission_group", "access_level"],
        )

        vocab.terms["authentication"] = DomainTerm(
            term="authentication",
            category="security",
            description="Identity verification process",
            synonyms=["login", "sign_in", "auth"],
        )

        vocab.terms["audit"] = DomainTerm(
            term="audit",
            category="compliance",
            description="Record of system activities",
            synonyms=["audit_log", "audit_trail", "history"],
            compliance_related=True,
            compliance_standards=["GDPR", "SOX"],
        )

        return vocab

    # =========================================================================
    # Public API
    # =========================================================================

    def get_vocabulary(self, domain: str) -> Optional[DomainVocabulary]:
        """
        Get vocabulary for a specific domain.

        Args:
            domain: Domain name (healthcare, finance, ecommerce, generic)

        Returns:
            DomainVocabulary or None if not found
        """
        try:
            business_domain = BusinessDomain(domain.lower())
            return self._vocabularies.get(business_domain)
        except ValueError:
            return None

    def get_all_domains(self) -> List[str]:
        """Get list of all supported domains."""
        return [d.value for d in BusinessDomain]

    def detect_domain(self, source_code: str) -> Tuple[BusinessDomain, float]:
        """
        Auto-detect the business domain from source code.

        Analyzes the code for domain-specific terms and patterns
        to determine the most likely business domain.

        Args:
            source_code: Source code to analyze

        Returns:
            Tuple of (detected domain, confidence score 0-1)
        """
        source_lower = source_code.lower()
        domain_scores: Dict[BusinessDomain, int] = Counter()

        for domain, vocab in self._vocabularies.items():
            if domain == BusinessDomain.GENERIC:
                continue  # Skip generic for detection

            # Count pattern matches
            for pattern in vocab.patterns:
                matches = len(re.findall(pattern, source_lower))
                domain_scores[domain] += matches * 2  # Patterns worth 2 points

            # Count term matches
            for term in vocab.get_all_terms():
                if term.lower() in source_lower:
                    domain_scores[domain] += 1

            # Count abbreviation matches
            for abbr in vocab.common_abbreviations.keys():
                if abbr.lower() in source_lower:
                    domain_scores[domain] += 3  # Abbreviations worth 3 points

        if not domain_scores:
            return BusinessDomain.GENERIC, 0.0

        # Get highest scoring domain
        best_domain = max(domain_scores, key=lambda d: domain_scores[d])
        best_score = domain_scores[best_domain]
        total_score = sum(domain_scores.values())

        # Calculate confidence (relative to other domains)
        confidence = best_score / total_score if total_score > 0 else 0.0

        # Require minimum score threshold
        if best_score < 3:
            return BusinessDomain.GENERIC, 0.0

        return best_domain, round(confidence, 2)

    def find_domain_terms(
        self,
        source_code: str,
        domain: str,
    ) -> List[Tuple[str, DomainTerm, int]]:
        """
        Find domain-specific terms in source code.

        Args:
            source_code: Source code to analyze
            domain: Domain to search for

        Returns:
            List of (matched_text, term_info, count) tuples
        """
        vocab = self.get_vocabulary(domain)
        if not vocab:
            return []

        source_lower = source_code.lower()
        results: List[Tuple[str, DomainTerm, int]] = []

        for term_key, term_info in vocab.terms.items():
            # Count main term
            count = source_lower.count(term_key.lower())

            # Count synonyms
            for synonym in term_info.synonyms:
                count += source_lower.count(synonym.lower())

            if count > 0:
                results.append((term_key, term_info, count))

        # Sort by count descending
        return sorted(results, key=lambda x: x[2], reverse=True)

    def get_compliance_terms(
        self,
        domain: str,
        standard: Optional[str] = None,
    ) -> List[DomainTerm]:
        """
        Get compliance-related terms for a domain.

        Args:
            domain: Domain to query
            standard: Optional specific compliance standard to filter by

        Returns:
            List of compliance-related DomainTerms
        """
        vocab = self.get_vocabulary(domain)
        if not vocab:
            return []

        results = []
        for term in vocab.terms.values():
            if term.compliance_related:
                if standard is None or standard in term.compliance_standards:
                    results.append(term)

        return results

    def expand_term(self, term: str, domain: str) -> List[str]:
        """
        Expand a term to include all synonyms.

        Args:
            term: Term to expand
            domain: Domain context

        Returns:
            List of term and all its synonyms
        """
        vocab = self.get_vocabulary(domain)
        if not vocab:
            return [term]

        term_lower = term.lower()

        # Check if term is a main term
        if term_lower in vocab.terms:
            domain_term = vocab.terms[term_lower]
            return [domain_term.term] + domain_term.synonyms

        # Check if term is a synonym
        for domain_term in vocab.terms.values():
            if term_lower in [s.lower() for s in domain_term.synonyms]:
                return [domain_term.term] + domain_term.synonyms

        return [term]

    def get_abbreviation_expansion(self, abbr: str, domain: str) -> Optional[str]:
        """
        Get the expansion of an abbreviation.

        Args:
            abbr: Abbreviation to expand
            domain: Domain context

        Returns:
            Full expansion or None
        """
        vocab = self.get_vocabulary(domain)
        if not vocab:
            return None

        return vocab.common_abbreviations.get(abbr.upper())


# Factory functions for convenience
def healthcare_vocabulary() -> DomainVocabulary:
    """Get healthcare domain vocabulary."""
    return DomainVocabularyLoader().get_vocabulary("healthcare")


def finance_vocabulary() -> DomainVocabulary:
    """Get finance domain vocabulary."""
    return DomainVocabularyLoader().get_vocabulary("finance")


def ecommerce_vocabulary() -> DomainVocabulary:
    """Get e-commerce domain vocabulary."""
    return DomainVocabularyLoader().get_vocabulary("ecommerce")
