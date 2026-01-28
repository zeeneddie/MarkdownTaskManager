"""
Reconciliation Service

Compares 3 independent epic sets (bottom-up, top-down, enhanced) and produces
7 reconciliation reports:
  8a. Epic Matching (fuzzy)
  8b. Blind Spot Report
  8c. Phantom Feature Report
  8d. Confidence Heatmap
  8e. FP Delta Score
  8f. Domain Boundary Disputes
  8g. Unified Epic Set

The unified epics are stored in the existing brown_paper_epics table so the
dashboard works without changes.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brown_paper import (
    BrownPaperConstitution as BrownPaperConstitutionDB,
    BrownPaperEpic as BrownPaperEpicDB,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EpicMatch:
    """A matched pair of epics from two different sources."""
    epic_a: Dict[str, Any]
    label_a: str
    epic_b: Dict[str, Any]
    label_b: str
    similarity_score: float
    match_details: Dict[str, float] = field(default_factory=dict)


@dataclass
class EpicMatchResult:
    """Result of matching two epic sets."""
    matched: List[EpicMatch]
    unmatched_a: List[Dict[str, Any]]
    unmatched_b: List[Dict[str, Any]]
    label_a: str
    label_b: str


@dataclass
class BlindSpot:
    """Epic in code but not in answers - functionality the human forgot to mention."""
    epic_name: str
    source_modules: List[str]
    estimated_fp: int
    source_domain: str
    recommendation: str


@dataclass
class PhantomFeature:
    """Epic in answers but not in code - dead code, future wish, or scanner miss."""
    epic_name: str
    source_answer: str
    description: str
    recommendation: str


@dataclass
class ConfidenceEntry:
    """Per-epic confidence score based on how many sources confirm it."""
    epic_name: str
    source_count: int  # 1, 2, or 3
    confidence: float  # 0.4, 0.7, or 1.0
    sources: List[str]  # ["bottom_up", "top_down", "enhanced"]
    invest_score: Optional[float] = None


@dataclass
class FPDelta:
    """FP estimation difference between sources for a matched epic."""
    epic_name: str
    fp_bottom_up: Optional[int]
    fp_top_down: Optional[int]
    delta_absolute: int
    delta_percent: float
    is_risk: bool  # delta > 30%


@dataclass
class DomainDispute:
    """Module assigned to different domains by code vs business analysis."""
    module_name: str
    domain_code: str
    domain_business: str
    recommendation: str


@dataclass
class ReconciliationResult:
    """Complete reconciliation output from all 7 analyses."""
    # 8a: Epic matching results
    matches_bu_td: EpicMatchResult
    matches_bu_en: EpicMatchResult
    matches_td_en: EpicMatchResult

    # 8b-8f: Reports
    blind_spots: List[BlindSpot]
    phantom_features: List[PhantomFeature]
    confidence_heatmap: List[ConfidenceEntry]
    fp_deltas: List[FPDelta]
    domain_disputes: List[DomainDispute]

    # 8g: Unified epic set
    unified_epics: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSONB storage."""
        return {
            "blind_spots": [
                {
                    "epic_name": bs.epic_name,
                    "source_modules": bs.source_modules,
                    "estimated_fp": bs.estimated_fp,
                    "source_domain": bs.source_domain,
                    "recommendation": bs.recommendation,
                }
                for bs in self.blind_spots
            ],
            "phantom_features": [
                {
                    "epic_name": pf.epic_name,
                    "source_answer": pf.source_answer,
                    "description": pf.description,
                    "recommendation": pf.recommendation,
                }
                for pf in self.phantom_features
            ],
            "confidence_heatmap": [
                {
                    "epic_name": ce.epic_name,
                    "source_count": ce.source_count,
                    "confidence": ce.confidence,
                    "sources": ce.sources,
                    "invest_score": ce.invest_score,
                }
                for ce in self.confidence_heatmap
            ],
            "fp_deltas": [
                {
                    "epic_name": fd.epic_name,
                    "fp_bottom_up": fd.fp_bottom_up,
                    "fp_top_down": fd.fp_top_down,
                    "delta_absolute": fd.delta_absolute,
                    "delta_percent": fd.delta_percent,
                    "is_risk": fd.is_risk,
                }
                for fd in self.fp_deltas
            ],
            "domain_disputes": [
                {
                    "module_name": dd.module_name,
                    "domain_code": dd.domain_code,
                    "domain_business": dd.domain_business,
                    "recommendation": dd.recommendation,
                }
                for dd in self.domain_disputes
            ],
            "unified_epics_count": len(self.unified_epics),
            "unified_features_count": sum(
                len(e.get("features", [])) for e in self.unified_epics
            ),
            "unified_stories_count": sum(
                sum(len(f.get("stories", [])) for f in e.get("features", []))
                for e in self.unified_epics
            ),
            "matching_summary": {
                "bottom_up_top_down": {
                    "matched": len(self.matches_bu_td.matched),
                    "unmatched_a": len(self.matches_bu_td.unmatched_a),
                    "unmatched_b": len(self.matches_bu_td.unmatched_b),
                },
                "bottom_up_enhanced": {
                    "matched": len(self.matches_bu_en.matched),
                    "unmatched_a": len(self.matches_bu_en.unmatched_a),
                    "unmatched_b": len(self.matches_bu_en.unmatched_b),
                },
                "top_down_enhanced": {
                    "matched": len(self.matches_td_en.matched),
                    "unmatched_a": len(self.matches_td_en.unmatched_a),
                    "unmatched_b": len(self.matches_td_en.unmatched_b),
                },
            },
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate normalized Levenshtein similarity (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    # Wagner-Fischer algorithm
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,       # deletion
                matrix[i][j - 1] + 1,       # insertion
                matrix[i - 1][j - 1] + cost  # substitution
            )

    distance = matrix[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _get_epic_name(epic: Dict[str, Any]) -> str:
    """Extract epic name from various dict formats."""
    return epic.get("name", epic.get("title", epic.get("epic_name", "")))


def _get_epic_modules(epic: Dict[str, Any]) -> set:
    """Extract module set from an epic dict."""
    modules = epic.get("source_modules", epic.get("modules", []))
    if isinstance(modules, list):
        return set(modules)
    return set()


def _get_epic_domain(epic: Dict[str, Any]) -> str:
    """Extract domain name from an epic dict."""
    return epic.get("source_domain", epic.get("domain", epic.get("domain_name", "")))


def _get_epic_fp(epic: Dict[str, Any]) -> Optional[int]:
    """Extract FP estimate from an epic dict."""
    fp = epic.get("function_points", epic.get("estimated_fp", epic.get("fp", None)))
    if fp is not None:
        try:
            return int(fp)
        except (ValueError, TypeError):
            return None
    return None


# ============================================================================
# RECONCILIATION SERVICE
# ============================================================================

class ReconciliationService:
    """
    Compares 3 independent epic sets and produces reconciliation reports.
    """

    MATCH_THRESHOLD = 0.6  # Minimum combined similarity to consider a match
    FP_DELTA_RISK_THRESHOLD = 0.30  # 30% FP delta = risk indicator

    def __init__(self, db: AsyncSession):
        self.db = db

    async def reconcile(
        self,
        epics_bottom_up: List[Dict],
        epics_top_down: List[Dict],
        epics_enhanced: List[Dict],
        fp_bottom_up: Optional[Dict] = None,
        fp_top_down: Optional[Dict] = None,
        domains_code: Optional[List[Dict]] = None,
        domains_business: Optional[List[Dict]] = None,
    ) -> ReconciliationResult:
        """Main method: run all 7 analyses and produce unified epic set."""
        logger.info(
            f"Starting reconciliation: {len(epics_bottom_up)} bottom-up, "
            f"{len(epics_top_down)} top-down, {len(epics_enhanced)} enhanced"
        )

        # 8a: Match epics across all pairs
        matches_bu_td = self._match_epics(epics_bottom_up, "bottom_up", epics_top_down, "top_down")
        matches_bu_en = self._match_epics(epics_bottom_up, "bottom_up", epics_enhanced, "enhanced")
        matches_td_en = self._match_epics(epics_top_down, "top_down", epics_enhanced, "enhanced")

        # 8b: Blind Spot Report (in code but not in answers)
        blind_spots = self._build_blind_spot_report(matches_bu_td, epics_bottom_up)

        # 8c: Phantom Feature Report (in answers but not in code)
        phantom_features = self._build_phantom_report(matches_bu_td, epics_top_down)

        # 8d: Confidence Heatmap
        confidence_heatmap = self._build_confidence_heatmap(
            matches_bu_td, matches_bu_en, matches_td_en,
            epics_bottom_up, epics_top_down, epics_enhanced
        )

        # 8e: FP Delta Score
        fp_deltas = self._calculate_fp_delta(matches_bu_td, fp_bottom_up, fp_top_down)

        # 8f: Domain Boundary Disputes
        domain_disputes = self._detect_domain_disputes(domains_code, domains_business)

        # 8g: Unified Epic Set
        confidence_map = {ce.epic_name: ce for ce in confidence_heatmap}
        unified_epics = self._build_unified_epic_set(
            matches_bu_td, matches_bu_en, matches_td_en,
            confidence_map,
            epics_bottom_up, epics_top_down, epics_enhanced,
        )

        result = ReconciliationResult(
            matches_bu_td=matches_bu_td,
            matches_bu_en=matches_bu_en,
            matches_td_en=matches_td_en,
            blind_spots=blind_spots,
            phantom_features=phantom_features,
            confidence_heatmap=confidence_heatmap,
            fp_deltas=fp_deltas,
            domain_disputes=domain_disputes,
            unified_epics=unified_epics,
        )

        logger.info(
            f"Reconciliation complete: {len(unified_epics)} unified epics, "
            f"{len(blind_spots)} blind spots, {len(phantom_features)} phantoms"
        )
        return result

    # ========================================================================
    # 8a: EPIC MATCHING (FUZZY)
    # ========================================================================

    def _match_epics(
        self,
        set_a: List[Dict], label_a: str,
        set_b: List[Dict], label_b: str,
    ) -> EpicMatchResult:
        """
        Fuzzy match epics on name (Levenshtein), domain, and module overlap.
        Weighted combination: 0.5 * name + 0.3 * modules + 0.2 * domain.
        Threshold: similarity >= 0.6 = match.
        """
        matched = []
        used_b_indices = set()

        for epic_a in set_a:
            name_a = _get_epic_name(epic_a)
            modules_a = _get_epic_modules(epic_a)
            domain_a = _get_epic_domain(epic_a)

            best_match = None
            best_score = 0.0

            for j, epic_b in enumerate(set_b):
                if j in used_b_indices:
                    continue

                name_b = _get_epic_name(epic_b)
                modules_b = _get_epic_modules(epic_b)
                domain_b = _get_epic_domain(epic_b)

                # Calculate component similarities
                name_sim = _levenshtein_similarity(name_a, name_b)
                module_sim = _jaccard_similarity(modules_a, modules_b)
                domain_sim = 1.0 if (domain_a and domain_b and domain_a.lower() == domain_b.lower()) else 0.0

                # Weighted combination
                combined = 0.5 * name_sim + 0.3 * module_sim + 0.2 * domain_sim

                if combined > best_score:
                    best_score = combined
                    best_match = (j, epic_b, {
                        "name_similarity": round(name_sim, 3),
                        "module_similarity": round(module_sim, 3),
                        "domain_similarity": round(domain_sim, 3),
                        "combined": round(combined, 3),
                    })

            if best_match and best_score >= self.MATCH_THRESHOLD:
                j, epic_b, details = best_match
                used_b_indices.add(j)
                matched.append(EpicMatch(
                    epic_a=epic_a,
                    label_a=label_a,
                    epic_b=epic_b,
                    label_b=label_b,
                    similarity_score=best_score,
                    match_details=details,
                ))

        unmatched_a = [e for i, e in enumerate(set_a) if not any(
            m.epic_a is e for m in matched
        )]
        unmatched_b = [e for j, e in enumerate(set_b) if j not in used_b_indices]

        return EpicMatchResult(
            matched=matched,
            unmatched_a=unmatched_a,
            unmatched_b=unmatched_b,
            label_a=label_a,
            label_b=label_b,
        )

    # ========================================================================
    # 8b: BLIND SPOT REPORT
    # ========================================================================

    def _build_blind_spot_report(
        self,
        match_result: EpicMatchResult,
        epics_bottom_up: List[Dict],
    ) -> List[BlindSpot]:
        """Epics in code (bottom-up) but not in answers (top-down)."""
        blind_spots = []
        for epic in match_result.unmatched_a:
            name = _get_epic_name(epic)
            modules = list(_get_epic_modules(epic))
            domain = _get_epic_domain(epic)
            fp = _get_epic_fp(epic) or 0

            blind_spots.append(BlindSpot(
                epic_name=name,
                source_modules=modules,
                estimated_fp=fp,
                source_domain=domain,
                recommendation=(
                    f"Code analysis identified '{name}' in domain '{domain}' "
                    f"with {len(modules)} modules, but this was not mentioned in the "
                    f"stakeholder answers. Verify if this is relevant functionality "
                    f"or legacy/dead code."
                ),
            ))

        return blind_spots

    # ========================================================================
    # 8c: PHANTOM FEATURE REPORT
    # ========================================================================

    def _build_phantom_report(
        self,
        match_result: EpicMatchResult,
        epics_top_down: List[Dict],
    ) -> List[PhantomFeature]:
        """Epics in answers (top-down) but not in code (bottom-up)."""
        phantoms = []
        for epic in match_result.unmatched_b:
            name = _get_epic_name(epic)
            description = epic.get("description", "")

            phantoms.append(PhantomFeature(
                epic_name=name,
                source_answer=epic.get("source_answer", "stakeholder input"),
                description=description[:200] if description else "",
                recommendation=(
                    f"Stakeholders mentioned '{name}' but no corresponding code was found. "
                    f"This could be: (1) a future feature request, (2) functionality in "
                    f"external systems, or (3) code the scanner missed. Investigate further."
                ),
            ))

        return phantoms

    # ========================================================================
    # 8d: CONFIDENCE HEATMAP
    # ========================================================================

    def _build_confidence_heatmap(
        self,
        matches_bu_td: EpicMatchResult,
        matches_bu_en: EpicMatchResult,
        matches_td_en: EpicMatchResult,
        epics_bottom_up: List[Dict],
        epics_top_down: List[Dict],
        epics_enhanced: List[Dict],
    ) -> List[ConfidenceEntry]:
        """Per epic: in how many of the 3 sources does it appear? Score 0.4/0.7/1.0."""
        # Build a map of epic_name -> set of sources
        epic_sources: Dict[str, set] = {}

        # All bottom-up epics
        for e in epics_bottom_up:
            name = _get_epic_name(e)
            if name:
                epic_sources.setdefault(name, set()).add("bottom_up")

        # All top-down epics
        for e in epics_top_down:
            name = _get_epic_name(e)
            if name:
                epic_sources.setdefault(name, set()).add("top_down")

        # All enhanced epics
        for e in epics_enhanced:
            name = _get_epic_name(e)
            if name:
                epic_sources.setdefault(name, set()).add("enhanced")

        # Cross-reference matched epics to merge names
        # When epics match across sources, unify under the top-down name (richer)
        for match in matches_bu_td.matched:
            name_a = _get_epic_name(match.epic_a)
            name_b = _get_epic_name(match.epic_b)
            if name_a and name_b and name_a != name_b:
                # Merge sources under the top-down name
                merged = epic_sources.get(name_a, set()) | epic_sources.get(name_b, set())
                epic_sources[name_b] = merged
                if name_a in epic_sources and name_a != name_b:
                    del epic_sources[name_a]

        for match in matches_bu_en.matched:
            name_a = _get_epic_name(match.epic_a)
            name_b = _get_epic_name(match.epic_b)
            if name_a and name_b and name_a != name_b:
                merged = epic_sources.get(name_a, set()) | epic_sources.get(name_b, set())
                # Keep the name that's already largest
                target = name_b if name_b in epic_sources else name_a
                epic_sources[target] = merged
                other = name_a if target == name_b else name_b
                if other in epic_sources and other != target:
                    del epic_sources[other]

        for match in matches_td_en.matched:
            name_a = _get_epic_name(match.epic_a)
            name_b = _get_epic_name(match.epic_b)
            if name_a and name_b and name_a != name_b:
                merged = epic_sources.get(name_a, set()) | epic_sources.get(name_b, set())
                target = name_a if name_a in epic_sources else name_b
                epic_sources[target] = merged
                other = name_b if target == name_a else name_a
                if other in epic_sources and other != target:
                    del epic_sources[other]

        # Calculate confidence scores
        confidence_entries = []
        for name, sources in sorted(epic_sources.items()):
            count = len(sources)
            if count >= 3:
                confidence = 1.0
            elif count == 2:
                confidence = 0.7
            else:
                confidence = 0.4

            # Try to find INVEST score from enhanced epics
            invest_score = None
            for e in epics_enhanced:
                if _get_epic_name(e) == name:
                    invest_score = e.get("invest_score", e.get("invest_total", None))
                    break

            confidence_entries.append(ConfidenceEntry(
                epic_name=name,
                source_count=count,
                confidence=confidence,
                sources=sorted(sources),
                invest_score=invest_score,
            ))

        return confidence_entries

    # ========================================================================
    # 8e: FP DELTA SCORE
    # ========================================================================

    def _calculate_fp_delta(
        self,
        match_result: EpicMatchResult,
        fp_bottom_up: Optional[Dict],
        fp_top_down: Optional[Dict],
    ) -> List[FPDelta]:
        """Per matched epic: compare FP from code-scan vs question-analysis."""
        deltas = []
        fp_bu = fp_bottom_up or {}
        fp_td = fp_top_down or {}

        for match in match_result.matched:
            name_a = _get_epic_name(match.epic_a)
            name_b = _get_epic_name(match.epic_b)

            # Get FP from epic dicts or from separate FP dicts
            fp_a = _get_epic_fp(match.epic_a) or fp_bu.get(name_a, None)
            fp_b = _get_epic_fp(match.epic_b) or fp_td.get(name_b, None)

            if fp_a is not None and fp_b is not None and (fp_a > 0 or fp_b > 0):
                delta_abs = abs(fp_a - fp_b)
                max_fp = max(fp_a, fp_b, 1)  # avoid division by zero
                delta_pct = delta_abs / max_fp

                deltas.append(FPDelta(
                    epic_name=name_b or name_a,  # prefer top-down name
                    fp_bottom_up=fp_a,
                    fp_top_down=fp_b,
                    delta_absolute=delta_abs,
                    delta_percent=round(delta_pct, 3),
                    is_risk=delta_pct > self.FP_DELTA_RISK_THRESHOLD,
                ))

        return deltas

    # ========================================================================
    # 8f: DOMAIN BOUNDARY DISPUTES
    # ========================================================================

    def _detect_domain_disputes(
        self,
        domains_code: Optional[List[Dict]],
        domains_business: Optional[List[Dict]],
    ) -> List[DomainDispute]:
        """Compare module->domain mapping from code vs from answers."""
        if not domains_code or not domains_business:
            return []

        disputes = []

        # Build module->domain maps
        code_map: Dict[str, str] = {}
        for domain in domains_code:
            domain_name = domain.get("name", "")
            for module in domain.get("modules", []):
                mod_name = module if isinstance(module, str) else module.get("name", "")
                if mod_name:
                    code_map[mod_name.lower()] = domain_name

        business_map: Dict[str, str] = {}
        for domain in domains_business:
            domain_name = domain.get("name", "")
            for module in domain.get("modules", []):
                mod_name = module if isinstance(module, str) else module.get("name", "")
                if mod_name:
                    business_map[mod_name.lower()] = domain_name

        # Find conflicts
        for mod_key in set(code_map.keys()) & set(business_map.keys()):
            code_domain = code_map[mod_key]
            biz_domain = business_map[mod_key]
            if code_domain.lower() != biz_domain.lower():
                disputes.append(DomainDispute(
                    module_name=mod_key,
                    domain_code=code_domain,
                    domain_business=biz_domain,
                    recommendation=(
                        f"Module '{mod_key}' is classified as '{code_domain}' by code analysis "
                        f"but as '{biz_domain}' by business stakeholders. "
                        f"Review architecture alignment and consider domain restructuring."
                    ),
                ))

        return disputes

    # ========================================================================
    # 8g: UNIFIED EPIC SET
    # ========================================================================

    def _build_unified_epic_set(
        self,
        matches_bu_td: EpicMatchResult,
        matches_bu_en: EpicMatchResult,
        matches_td_en: EpicMatchResult,
        confidence_map: Dict[str, ConfidenceEntry],
        epics_bottom_up: List[Dict],
        epics_top_down: List[Dict],
        epics_enhanced: List[Dict],
    ) -> List[Dict]:
        """
        Merge 3 epic sets into 1 definitive set.

        Merge strategy per epic:
        - Name + description: from top-down (human, richer)
        - Features: union of all sources (nothing left out)
        - Stories: enhanced version if available (INVEST-validated), else top-down
        - FP/SP: average of available estimates
        - Confidence: from confidence heatmap
        - source_origin: which sources contributed
        """
        unified = []
        processed_names = set()
        epic_counter = 0

        # Helper to find enhanced epic by name
        enhanced_by_name = {_get_epic_name(e).lower(): e for e in epics_enhanced if _get_epic_name(e)}
        td_by_name = {_get_epic_name(e).lower(): e for e in epics_top_down if _get_epic_name(e)}
        bu_by_name = {_get_epic_name(e).lower(): e for e in epics_bottom_up if _get_epic_name(e)}

        # Process matched epics from bottom-up <-> top-down
        for match in matches_bu_td.matched:
            epic_counter += 1
            name_td = _get_epic_name(match.epic_b)  # top-down name (richer)
            name_bu = _get_epic_name(match.epic_a)

            # Find corresponding enhanced epic
            enhanced_epic = None
            for m_en in matches_td_en.matched:
                if _get_epic_name(m_en.epic_a).lower() == name_td.lower():
                    enhanced_epic = m_en.epic_b
                    break
            if not enhanced_epic:
                enhanced_epic = enhanced_by_name.get(name_td.lower()) or enhanced_by_name.get(name_bu.lower())

            unified_epic = self._merge_epic(
                epic_counter, match.epic_a, match.epic_b, enhanced_epic, confidence_map
            )
            unified.append(unified_epic)
            processed_names.add(name_td.lower())
            processed_names.add(name_bu.lower())

        # Add unmatched top-down epics (phantoms get included with low confidence)
        for epic in matches_bu_td.unmatched_b:
            name = _get_epic_name(epic)
            if name.lower() in processed_names:
                continue
            epic_counter += 1
            enhanced_epic = enhanced_by_name.get(name.lower())
            unified_epic = self._merge_epic(
                epic_counter, None, epic, enhanced_epic, confidence_map
            )
            unified_epic["is_phantom"] = True
            unified.append(unified_epic)
            processed_names.add(name.lower())

        # Add unmatched bottom-up epics (blind spots get included with low confidence)
        for epic in matches_bu_td.unmatched_a:
            name = _get_epic_name(epic)
            if name.lower() in processed_names:
                continue
            epic_counter += 1
            enhanced_epic = enhanced_by_name.get(name.lower())
            unified_epic = self._merge_epic(
                epic_counter, epic, None, enhanced_epic, confidence_map
            )
            unified_epic["is_blind_spot"] = True
            unified.append(unified_epic)
            processed_names.add(name.lower())

        # Add remaining enhanced epics not yet processed
        for epic in epics_enhanced:
            name = _get_epic_name(epic)
            if name.lower() in processed_names:
                continue
            epic_counter += 1
            unified_epic = self._merge_epic(
                epic_counter, None, None, epic, confidence_map
            )
            unified.append(unified_epic)
            processed_names.add(name.lower())

        return unified

    def _merge_epic(
        self,
        counter: int,
        epic_bu: Optional[Dict],
        epic_td: Optional[Dict],
        epic_en: Optional[Dict],
        confidence_map: Dict[str, ConfidenceEntry],
    ) -> Dict:
        """Merge up to 3 epic versions into one unified epic."""
        # Determine the canonical name (prefer top-down, then enhanced, then bottom-up)
        name = ""
        if epic_td:
            name = _get_epic_name(epic_td)
        if not name and epic_en:
            name = _get_epic_name(epic_en)
        if not name and epic_bu:
            name = _get_epic_name(epic_bu)

        # Description: prefer top-down (human, richer), then enhanced, then bottom-up
        description = ""
        if epic_td:
            description = epic_td.get("description", "")
        if not description and epic_en:
            description = epic_en.get("description", "")
        if not description and epic_bu:
            description = epic_bu.get("description", "")

        # Features: union from all sources
        features = self._merge_features(
            epic_bu.get("features", []) if epic_bu else [],
            epic_td.get("features", []) if epic_td else [],
            epic_en.get("features", []) if epic_en else [],
        )

        # FP/SP: average of available estimates
        fp_values = []
        sp_values = []
        for e in [epic_bu, epic_td, epic_en]:
            if e:
                fp = _get_epic_fp(e)
                if fp is not None and fp > 0:
                    fp_values.append(fp)
                sp = e.get("story_points", e.get("estimated_sp", None))
                if sp is not None:
                    try:
                        sp_val = int(sp)
                        if sp_val > 0:
                            sp_values.append(sp_val)
                    except (ValueError, TypeError):
                        pass

        avg_fp = round(sum(fp_values) / len(fp_values)) if fp_values else 0
        avg_sp = round(sum(sp_values) / len(sp_values)) if sp_values else 0

        # Source origin
        source_origin = []
        if epic_bu:
            source_origin.append("bottom_up")
        if epic_td:
            source_origin.append("top_down")
        if epic_en:
            source_origin.append("enhanced")

        # Confidence from heatmap
        confidence_entry = confidence_map.get(name)
        confidence = confidence_entry.confidence if confidence_entry else 0.4

        # Domain / modules from bottom-up (most accurate for code structure)
        source_domain = ""
        source_modules = []
        if epic_bu:
            source_domain = _get_epic_domain(epic_bu)
            source_modules = list(_get_epic_modules(epic_bu))
        elif epic_td:
            source_domain = _get_epic_domain(epic_td)
            source_modules = list(_get_epic_modules(epic_td))
        elif epic_en:
            source_domain = _get_epic_domain(epic_en)
            source_modules = list(_get_epic_modules(epic_en))

        # Priority: prefer top-down, then enhanced, then bottom-up
        priority = 3  # default medium
        for e in [epic_td, epic_en, epic_bu]:
            if e and e.get("priority"):
                try:
                    priority = int(e["priority"])
                    break
                except (ValueError, TypeError):
                    pass

        # Complexity
        complexity = "medium"
        for e in [epic_en, epic_td, epic_bu]:
            if e and e.get("complexity"):
                complexity = e["complexity"]
                break

        return {
            "epic_number": f"EPIC-{counter:03d}",
            "name": name,
            "description": description,
            "priority": priority,
            "complexity": complexity,
            "source_domain": source_domain,
            "source_modules": source_modules,
            "function_points": avg_fp,
            "story_points": avg_sp,
            "features": features,
            "source_origin": source_origin,
            "confidence": confidence,
            "is_blind_spot": False,
            "is_phantom": False,
            "reconciliation_data": {
                "confidence": confidence,
                "source_origin": source_origin,
                "fp_values": fp_values,
                "sp_values": sp_values,
                "is_blind_spot": False,
                "is_phantom": False,
            },
        }

    def _merge_features(
        self,
        features_bu: List,
        features_td: List,
        features_en: List,
    ) -> List[Dict]:
        """
        Merge features from all sources. Deduplicate on title similarity.
        Stories: prefer enhanced (INVEST-validated) > top-down > bottom-up.
        """
        all_features = []
        seen_titles = set()

        # Process enhanced first (highest quality stories)
        for f in features_en:
            title = f.get("title", f.get("name", "")).lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                all_features.append(f)

        # Add top-down features not already covered
        for f in features_td:
            title = f.get("title", f.get("name", "")).lower().strip()
            if title and title not in seen_titles:
                # Check fuzzy match
                is_dup = False
                for existing_title in seen_titles:
                    if _levenshtein_similarity(title, existing_title) >= 0.7:
                        is_dup = True
                        break
                if not is_dup:
                    seen_titles.add(title)
                    all_features.append(f)

        # Add bottom-up features not already covered
        for f in features_bu:
            title = f.get("title", f.get("name", "")).lower().strip()
            if title and title not in seen_titles:
                is_dup = False
                for existing_title in seen_titles:
                    if _levenshtein_similarity(title, existing_title) >= 0.7:
                        is_dup = True
                        break
                if not is_dup:
                    seen_titles.add(title)
                    all_features.append(f)

        return all_features

    # ========================================================================
    # DATABASE PERSISTENCE
    # ========================================================================

    async def save_unified_epics_to_db(
        self,
        unified_epics: List[Dict],
        constitution_id: uuid.UUID,
        unified_session_id: uuid.UUID,
    ) -> List[BrownPaperEpicDB]:
        """
        Save unified epics to brown_paper_epics table.
        Adds reconciliation_data JSONB per epic for dashboard display.
        """
        saved_epics = []

        for epic_data in unified_epics:
            reconciliation_data = epic_data.get("reconciliation_data", {})
            reconciliation_data["unified_session_id"] = str(unified_session_id)

            epic = BrownPaperEpicDB(
                id=uuid.uuid4(),
                constitution_id=constitution_id,
                epic_number=epic_data.get("epic_number", f"EPIC-{len(saved_epics)+1:03d}"),
                name=epic_data.get("name", "Unnamed Epic"),
                description=epic_data.get("description", ""),
                priority=epic_data.get("priority", 3),
                complexity=epic_data.get("complexity", "medium"),
                source_domain=epic_data.get("source_domain", ""),
                source_modules=epic_data.get("source_modules", []),
                function_points=epic_data.get("function_points", 0),
                story_points=epic_data.get("story_points", 0),
                features=epic_data.get("features", []),
                status="draft",
                reconciliation_data=reconciliation_data,
            )
            self.db.add(epic)
            saved_epics.append(epic)

        await self.db.flush()
        logger.info(f"Saved {len(saved_epics)} unified epics to brown_paper_epics")
        return saved_epics
