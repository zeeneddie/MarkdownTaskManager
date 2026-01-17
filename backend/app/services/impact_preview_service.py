# backend/app/services/impact_preview_service.py
"""
Impact Preview Service - Week 118

Felix agent analyzes feature requests to preview their impact
on architecture, security, performance, and UX.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import json
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.portal_enhancements import (
    FeatureImpactPreview,
    ImpactLevel,
    RiskLevel,
)
from app.providers.registry import ProviderRegistry
from app.providers.base import LLMRequest


class ImpactPreviewService:
    """Service for Felix impact analysis."""

    # Cache duration
    CACHE_HOURS = 24

    # Felix analysis prompt
    FELIX_PROMPT = """You are Felix, a Feature Architect agent. Analyze this feature request and provide an impact assessment.

Feature Request:
Title: {title}
Description: {description}
{context}

Analyze the impact across these dimensions:
1. **Architecture Impact** - Changes to system structure, new components, refactoring
2. **Security Impact** - Authentication, authorization, data protection concerns
3. **Performance Impact** - Load, latency, resource usage considerations
4. **UX Impact** - User interface changes, workflow modifications
5. **Data Impact** - Database changes, migrations, data model updates

Provide your analysis in this exact JSON format:
{{
    "architecture_impact": "none|low|medium|high|critical",
    "security_impact": "none|low|medium|high|critical",
    "performance_impact": "none|low|medium|high|critical",
    "ux_impact": "none|low|medium|high|critical",
    "data_impact": "none|low|medium|high|critical",
    "overall_impact": "none|low|medium|high|critical",
    "risk_level": "low|medium|high",
    "complexity_score": 1-10,
    "affected_components": ["list", "of", "affected", "modules"],
    "affected_apis": ["list", "of", "API", "endpoints"],
    "dependencies": ["required", "changes", "or", "prerequisites"],
    "breaking_changes": ["list", "of", "breaking", "changes"],
    "implementation_approach": "Brief description of how to implement",
    "recommended_priority": "P0|P1|P2|P3|P4",
    "estimated_effort_hours": 8-200,
    "warnings": ["list", "of", "warnings"],
    "notes": "Additional notes"
}}

Be realistic and thorough. If the feature is simple, impacts can be "none" or "low"."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_registry = ProviderRegistry()

    async def analyze_feature(
        self,
        feature_request_id: int,
        title: str,
        description: str,
        project_id: Optional[int] = None,
        context: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Analyze feature request impact using Felix."""

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = await self._get_cached_preview(feature_request_id)
            if cached and not cached.is_stale:
                return self._preview_to_dict(cached)

        # Build prompt
        context_text = f"\nAdditional Context:\n{context}" if context else ""
        prompt = self.FELIX_PROMPT.format(
            title=title,
            description=description,
            context=context_text,
        )

        # Call LLM (Felix uses qwen2.5-coder:7b via Ollama)
        try:
            provider = self.provider_registry.get_provider("ollama")
            if not provider:
                raise ValueError("Ollama provider not available")

            # Create proper LLMRequest object
            request = LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000,
                timeout=120,
            )
            response = await provider.generate(request)

            # Check for success
            if not response.success:
                raise ValueError(response.error or "LLM generation failed")

            # Parse response
            analysis = self._parse_felix_response(response.content)

            # Create preview record
            preview = await self._create_preview(
                feature_request_id=feature_request_id,
                project_id=project_id,
                analysis=analysis,
                provider="ollama",
                model=response.model,
                tokens_used=response.token_input + response.token_output,
            )

            return self._preview_to_dict(preview)

        except Exception as e:
            # Return fallback analysis on error
            return {
                "success": False,
                "error": str(e),
                "fallback_analysis": self._get_fallback_analysis(title, description),
            }

    def _parse_felix_response(self, response: str) -> Dict[str, Any]:
        """Parse Felix's JSON response."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback parsing
        return self._get_fallback_analysis("", "")

    def _get_fallback_analysis(self, title: str, description: str) -> Dict[str, Any]:
        """Generate fallback analysis when LLM fails."""
        # Simple heuristic-based analysis
        text = f"{title} {description}".lower()

        # Detect keywords
        security_keywords = ["auth", "login", "password", "encrypt", "permission", "role"]
        performance_keywords = ["cache", "fast", "slow", "optimize", "scale", "load"]
        data_keywords = ["database", "migrate", "schema", "table", "column", "data"]
        ui_keywords = ["button", "form", "page", "modal", "dashboard", "display"]

        return {
            "architecture_impact": ImpactLevel.MEDIUM.value,
            "security_impact": ImpactLevel.MEDIUM.value if any(k in text for k in security_keywords) else ImpactLevel.LOW.value,
            "performance_impact": ImpactLevel.MEDIUM.value if any(k in text for k in performance_keywords) else ImpactLevel.LOW.value,
            "ux_impact": ImpactLevel.MEDIUM.value if any(k in text for k in ui_keywords) else ImpactLevel.LOW.value,
            "data_impact": ImpactLevel.MEDIUM.value if any(k in text for k in data_keywords) else ImpactLevel.LOW.value,
            "overall_impact": ImpactLevel.MEDIUM.value,
            "risk_level": RiskLevel.LOW.value,
            "complexity_score": 5,
            "affected_components": [],
            "affected_apis": [],
            "dependencies": [],
            "breaking_changes": [],
            "implementation_approach": "Standard implementation approach",
            "recommended_priority": "P2",
            "estimated_effort_hours": 16,
            "warnings": ["Analysis based on heuristics - LLM analysis failed"],
            "notes": "Fallback analysis used",
        }

    async def _get_cached_preview(
        self,
        feature_request_id: int,
    ) -> Optional[FeatureImpactPreview]:
        """Get cached preview if not stale."""
        result = await self.db.execute(
            select(FeatureImpactPreview)
            .where(FeatureImpactPreview.feature_request_id == feature_request_id)
            .order_by(FeatureImpactPreview.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def _create_preview(
        self,
        feature_request_id: int,
        project_id: Optional[int],
        analysis: Dict[str, Any],
        provider: str,
        model: str,
        tokens_used: int,
    ) -> FeatureImpactPreview:
        """Create new impact preview record."""
        preview = FeatureImpactPreview(
            id=uuid4(),
            feature_request_id=feature_request_id,
            project_id=project_id,
            analyzer_agent="felix",
            analysis_version="1.0",
            # Impact categories
            architecture_impact=analysis.get("architecture_impact", ImpactLevel.MEDIUM.value),
            security_impact=analysis.get("security_impact", ImpactLevel.LOW.value),
            performance_impact=analysis.get("performance_impact", ImpactLevel.LOW.value),
            ux_impact=analysis.get("ux_impact", ImpactLevel.LOW.value),
            data_impact=analysis.get("data_impact", ImpactLevel.LOW.value),
            # Overall
            overall_impact=analysis.get("overall_impact", ImpactLevel.MEDIUM.value),
            risk_level=analysis.get("risk_level", RiskLevel.LOW.value),
            complexity_score=analysis.get("complexity_score", 5),
            # Details
            affected_components=analysis.get("affected_components", []),
            affected_apis=analysis.get("affected_apis", []),
            dependencies=analysis.get("dependencies", []),
            breaking_changes=analysis.get("breaking_changes", []),
            # Recommendations
            implementation_approach=analysis.get("implementation_approach"),
            recommended_priority=analysis.get("recommended_priority"),
            estimated_effort_hours=analysis.get("estimated_effort_hours"),
            suggested_sprint=analysis.get("suggested_sprint"),
            # Warnings
            warnings=analysis.get("warnings", []),
            notes=analysis.get("notes"),
            # LLM info
            llm_provider=provider,
            llm_model=model,
            tokens_used=tokens_used,
            # Cache
            is_stale=False,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=self.CACHE_HOURS),
        )

        self.db.add(preview)
        await self.db.commit()
        await self.db.refresh(preview)
        return preview

    def _preview_to_dict(self, preview: FeatureImpactPreview) -> Dict[str, Any]:
        """Convert preview to dictionary response."""
        return {
            "success": True,
            "preview_id": str(preview.id),
            "feature_request_id": preview.feature_request_id,
            "analyzer": preview.analyzer_agent,
            "impact": {
                "architecture": preview.architecture_impact,
                "security": preview.security_impact,
                "performance": preview.performance_impact,
                "ux": preview.ux_impact,
                "data": preview.data_impact,
                "overall": preview.overall_impact,
            },
            "risk_level": preview.risk_level,
            "complexity_score": preview.complexity_score,
            "affected_components": preview.affected_components or [],
            "affected_apis": preview.affected_apis or [],
            "dependencies": preview.dependencies or [],
            "breaking_changes": preview.breaking_changes or [],
            "recommendations": {
                "implementation_approach": preview.implementation_approach,
                "priority": preview.recommended_priority,
                "effort_hours": preview.estimated_effort_hours,
                "suggested_sprint": preview.suggested_sprint,
            },
            "warnings": preview.warnings or [],
            "notes": preview.notes,
            "is_high_risk": preview.is_high_risk(),
            "has_breaking_changes": preview.has_breaking_changes(),
            "cached": not preview.is_stale,
            "expires_at": preview.expires_at.isoformat() if preview.expires_at else None,
            "created_at": preview.created_at.isoformat(),
        }

    async def invalidate_cache(self, feature_request_id: int) -> bool:
        """Mark cached preview as stale."""
        result = await self.db.execute(
            select(FeatureImpactPreview)
            .where(FeatureImpactPreview.feature_request_id == feature_request_id)
        )
        previews = result.scalars().all()

        for preview in previews:
            preview.is_stale = True

        await self.db.commit()
        return len(previews) > 0

    async def get_impact_summary(
        self,
        project_id: Optional[int] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get summary of recent impact analyses."""
        query = select(FeatureImpactPreview).order_by(
            FeatureImpactPreview.created_at.desc()
        ).limit(limit)

        if project_id:
            query = query.where(FeatureImpactPreview.project_id == project_id)

        result = await self.db.execute(query)
        previews = result.scalars().all()

        # Calculate statistics
        high_risk_count = sum(1 for p in previews if p.is_high_risk())
        breaking_changes_count = sum(1 for p in previews if p.has_breaking_changes())
        avg_complexity = sum(p.complexity_score or 0 for p in previews) / len(previews) if previews else 0

        return {
            "total_analyzed": len(previews),
            "high_risk_count": high_risk_count,
            "breaking_changes_count": breaking_changes_count,
            "average_complexity": round(avg_complexity, 1),
            "recent_previews": [
                {
                    "feature_id": p.feature_request_id,
                    "overall_impact": p.overall_impact,
                    "risk_level": p.risk_level,
                    "complexity": p.complexity_score,
                    "created_at": p.created_at.isoformat(),
                }
                for p in previews[:5]
            ],
        }
