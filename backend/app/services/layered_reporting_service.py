"""
LayeredReportingService - Generate Reports from Layered Analysis

Week 77: Creates various report formats from analysis results.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import UUID
from io import StringIO
import json

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.layered_analysis import (
    LayeredAnalysisSession,
    VBScriptAnalysis,
    StoredProcedureAnalysis,
    SWOTAnalysis,
    ImprovementItem,
    AnalysisReport
)

logger = logging.getLogger(__name__)


class LayeredReportingService:
    """
    Generate various report formats from layered analysis results.

    Supported formats:
    - Executive Summary (PDF/HTML)
    - Technical Deep-Dive
    - Improvement Backlog (CSV/JSON)
    - Migration Roadmap
    - SWOT Presentation
    """

    def __init__(self, db: Session):
        self.db = db

    async def generate_executive_summary(
        self,
        session_id: UUID,
        format: str = "html"
    ) -> Dict[str, Any]:
        """
        Generate executive summary report.

        Args:
            session_id: Analysis session ID
            format: Output format (html, markdown, json)

        Returns:
            Report content and metadata
        """
        session = self.db.get(LayeredAnalysisSession, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Gather all analysis data
        data = await self._gather_session_data(session_id)

        # Generate report content
        if format == "html":
            content = self._generate_html_executive_summary(data)
        elif format == "markdown":
            content = self._generate_markdown_executive_summary(data)
        else:
            content = json.dumps(data, indent=2, default=str)

        # Store report
        report = AnalysisReport(
            session_id=session_id,
            report_type="executive_summary",
            format=format,
            content=content,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(report)
        self.db.commit()

        return {
            "report_id": str(report.id),
            "type": "executive_summary",
            "format": format,
            "content": content,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def generate_technical_report(
        self,
        session_id: UUID,
        include_code_samples: bool = True
    ) -> Dict[str, Any]:
        """Generate detailed technical report."""
        data = await self._gather_session_data(session_id)

        content = self._generate_technical_report_content(data, include_code_samples)

        report = AnalysisReport(
            session_id=session_id,
            report_type="technical_deep_dive",
            format="markdown",
            content=content,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(report)
        self.db.commit()

        return {
            "report_id": str(report.id),
            "type": "technical_deep_dive",
            "format": "markdown",
            "content": content,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def generate_improvement_backlog(
        self,
        session_id: UUID,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Generate improvement backlog in export format."""
        improvements = self.db.execute(
            select(ImprovementItem).where(ImprovementItem.session_id == session_id)
        ).scalars().all()

        if format == "csv":
            content = self._generate_csv_backlog(improvements)
        elif format == "json":
            content = json.dumps(
                [self._improvement_to_dict(i) for i in improvements],
                indent=2
            )
        else:
            content = self._generate_jira_import(improvements)

        report = AnalysisReport(
            session_id=session_id,
            report_type="improvement_backlog",
            format=format,
            content=content,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(report)
        self.db.commit()

        return {
            "report_id": str(report.id),
            "type": "improvement_backlog",
            "format": format,
            "content": content,
            "item_count": len(improvements),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def generate_migration_roadmap(
        self,
        session_id: UUID,
        team_size: int = 3
    ) -> Dict[str, Any]:
        """Generate migration roadmap based on analysis."""
        data = await self._gather_session_data(session_id)
        improvements = self.db.execute(
            select(ImprovementItem).where(ImprovementItem.session_id == session_id)
        ).scalars().all()

        roadmap = self._create_roadmap(data, improvements, team_size)
        content = self._generate_roadmap_content(roadmap)

        report = AnalysisReport(
            session_id=session_id,
            report_type="migration_roadmap",
            format="markdown",
            content=content,
            metadata={"roadmap": roadmap},
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(report)
        self.db.commit()

        return {
            "report_id": str(report.id),
            "type": "migration_roadmap",
            "roadmap": roadmap,
            "content": content,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def generate_swot_presentation(
        self,
        session_id: UUID
    ) -> Dict[str, Any]:
        """Generate SWOT presentation content."""
        swot = self.db.execute(
            select(SWOTAnalysis).where(SWOTAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        if not swot:
            raise ValueError(f"No SWOT analysis found for session {session_id}")

        slides = self._generate_swot_slides(swot)
        content = self._render_slides_to_html(slides)

        report = AnalysisReport(
            session_id=session_id,
            report_type="swot_presentation",
            format="html",
            content=content,
            metadata={"slides": slides},
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(report)
        self.db.commit()

        return {
            "report_id": str(report.id),
            "type": "swot_presentation",
            "slides": slides,
            "content": content,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def _gather_session_data(self, session_id: UUID) -> Dict[str, Any]:
        """Gather all analysis data for a session."""
        session = self.db.get(LayeredAnalysisSession, session_id)

        vb_analysis = self.db.execute(
            select(VBScriptAnalysis).where(VBScriptAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        sp_analysis = self.db.execute(
            select(StoredProcedureAnalysis).where(StoredProcedureAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        swot = self.db.execute(
            select(SWOTAnalysis).where(SWOTAnalysis.session_id == session_id)
        ).scalar_one_or_none()

        improvements = self.db.execute(
            select(ImprovementItem).where(ImprovementItem.session_id == session_id)
        ).scalars().all()

        return {
            "session": {
                "id": str(session.id),
                "name": session.name,
                "description": session.description,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at
            },
            "vbscript": self._vb_to_dict(vb_analysis) if vb_analysis else None,
            "stored_procedures": self._sp_to_dict(sp_analysis) if sp_analysis else None,
            "swot": self._swot_to_dict(swot) if swot else None,
            "improvements": [self._improvement_to_dict(i) for i in improvements]
        }

    def _vb_to_dict(self, analysis: VBScriptAnalysis) -> Dict[str, Any]:
        """Convert VBScript analysis to dict."""
        return {
            "file_count": analysis.file_count,
            "total_lines": analysis.total_lines,
            "security_findings": analysis.security_findings,
            "complexity_score": analysis.complexity_score,
            "modernization_score": analysis.modernization_score,
            "recommendations": analysis.recommendations
        }

    def _sp_to_dict(self, analysis: StoredProcedureAnalysis) -> Dict[str, Any]:
        """Convert SP analysis to dict."""
        return {
            "procedure_count": analysis.procedure_count,
            "total_lines": analysis.total_lines,
            "complexity_metrics": analysis.complexity_metrics,
            "vendor_specific_patterns": analysis.vendor_specific_patterns,
            "recommendations": analysis.recommendations
        }

    def _swot_to_dict(self, swot: SWOTAnalysis) -> Dict[str, Any]:
        """Convert SWOT analysis to dict."""
        return {
            "strengths": swot.strengths,
            "weaknesses": swot.weaknesses,
            "opportunities": swot.opportunities,
            "threats": swot.threats,
            "prioritization": swot.prioritization,
            "migration_readiness": swot.migration_readiness
        }

    def _improvement_to_dict(self, item: ImprovementItem) -> Dict[str, Any]:
        """Convert improvement item to dict."""
        return {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "item_type": item.item_type,
            "priority": item.priority,
            "effort_days": item.effort_days,
            "business_impact": item.business_impact,
            "risk_if_not_done": item.risk_if_not_done,
            "status": item.status
        }

    def _generate_html_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate HTML executive summary."""
        session = data["session"]
        vb = data.get("vbscript") or {}
        sp = data.get("stored_procedures") or {}
        swot = data.get("swot") or {}
        improvements = data.get("improvements") or []

        # Calculate key metrics
        total_lines = (vb.get("total_lines", 0) or 0) + (sp.get("total_lines", 0) or 0)
        security_count = len(vb.get("security_findings", []) or [])
        weakness_count = len(swot.get("weaknesses", []) or [])
        total_effort = sum(i.get("effort_days", 0) for i in improvements)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Executive Summary: {session['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        .metric-box {{ display: inline-block; padding: 20px; margin: 10px; background: #f8f9fa; border-radius: 8px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2980b9; }}
        .metric-label {{ color: #7f8c8d; }}
        .risk-high {{ color: #e74c3c; }}
        .risk-medium {{ color: #f39c12; }}
        .risk-low {{ color: #27ae60; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Executive Summary</h1>
    <p><strong>Project:</strong> {session['name']}</p>
    <p><strong>Analysis Date:</strong> {session.get('completed_at', 'In Progress')}</p>

    <h2>Key Metrics</h2>
    <div class="metric-box">
        <div class="metric-value">{total_lines:,}</div>
        <div class="metric-label">Lines of Code</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">{security_count}</div>
        <div class="metric-label">Security Findings</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">{weakness_count}</div>
        <div class="metric-label">Identified Weaknesses</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">{len(improvements)}</div>
        <div class="metric-label">Improvement Items</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">{total_effort:.0f}</div>
        <div class="metric-label">Estimated Days</div>
    </div>

    <h2>SWOT Overview</h2>
    <table>
        <tr>
            <th>Strengths ({len(swot.get('strengths', []))})</th>
            <th>Weaknesses ({len(swot.get('weaknesses', []))})</th>
        </tr>
        <tr>
            <td>
                <ul>
                    {''.join(f"<li>{s.get('title', s) if isinstance(s, dict) else s}</li>" for s in (swot.get('strengths', []) or [])[:5])}
                </ul>
            </td>
            <td>
                <ul>
                    {''.join(f"<li class='risk-high'>{w.get('title', w) if isinstance(w, dict) else w}</li>" for w in (swot.get('weaknesses', []) or [])[:5])}
                </ul>
            </td>
        </tr>
        <tr>
            <th>Opportunities ({len(swot.get('opportunities', []))})</th>
            <th>Threats ({len(swot.get('threats', []))})</th>
        </tr>
        <tr>
            <td>
                <ul>
                    {''.join(f"<li>{o.get('title', o) if isinstance(o, dict) else o}</li>" for o in (swot.get('opportunities', []) or [])[:5])}
                </ul>
            </td>
            <td>
                <ul>
                    {''.join(f"<li class='risk-medium'>{t.get('title', t) if isinstance(t, dict) else t}</li>" for t in (swot.get('threats', []) or [])[:5])}
                </ul>
            </td>
        </tr>
    </table>

    <h2>Top Priority Improvements</h2>
    <table>
        <tr>
            <th>Priority</th>
            <th>Title</th>
            <th>Category</th>
            <th>Effort (days)</th>
            <th>Impact</th>
        </tr>
        {''.join(f'''
        <tr>
            <td>{i.get('priority', '-')}</td>
            <td>{i.get('title', '-')}</td>
            <td>{i.get('category', '-')}</td>
            <td>{i.get('effort_days', '-')}</td>
            <td>{i.get('business_impact', '-')}</td>
        </tr>
        ''' for i in sorted(improvements, key=lambda x: x.get('priority', 99))[:10])}
    </table>

    <h2>Recommendations</h2>
    <ol>
        {''.join(f"<li>{r}</li>" for r in (vb.get('recommendations', []) or [])[:5])}
        {''.join(f"<li>{r}</li>" for r in (sp.get('recommendations', []) or [])[:5])}
    </ol>

    <footer>
        <p><em>Generated by MARQED Layered Analysis Service</em></p>
    </footer>
</body>
</html>
"""
        return html

    def _generate_markdown_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate Markdown executive summary."""
        session = data["session"]
        vb = data.get("vbscript") or {}
        sp = data.get("stored_procedures") or {}
        swot = data.get("swot") or {}
        improvements = data.get("improvements") or []

        total_lines = (vb.get("total_lines", 0) or 0) + (sp.get("total_lines", 0) or 0)
        security_count = len(vb.get("security_findings", []) or [])
        total_effort = sum(i.get("effort_days", 0) for i in improvements)

        md = f"""# Executive Summary: {session['name']}

**Analysis Date:** {session.get('completed_at', 'In Progress')}

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Lines of Code | {total_lines:,} |
| Security Findings | {security_count} |
| Identified Weaknesses | {len(swot.get('weaknesses', []) or [])} |
| Improvement Items | {len(improvements)} |
| Estimated Effort | {total_effort:.0f} days |

## SWOT Analysis

### Strengths
{chr(10).join(f"- {s.get('title', s) if isinstance(s, dict) else s}" for s in (swot.get('strengths', []) or [])[:5])}

### Weaknesses
{chr(10).join(f"- {w.get('title', w) if isinstance(w, dict) else w}" for w in (swot.get('weaknesses', []) or [])[:5])}

### Opportunities
{chr(10).join(f"- {o.get('title', o) if isinstance(o, dict) else o}" for o in (swot.get('opportunities', []) or [])[:5])}

### Threats
{chr(10).join(f"- {t.get('title', t) if isinstance(t, dict) else t}" for t in (swot.get('threats', []) or [])[:5])}

## Top Priority Improvements

| Priority | Title | Category | Effort | Impact |
|----------|-------|----------|--------|--------|
{chr(10).join(f"| {i.get('priority', '-')} | {i.get('title', '-')} | {i.get('category', '-')} | {i.get('effort_days', '-')}d | {i.get('business_impact', '-')} |" for i in sorted(improvements, key=lambda x: x.get('priority', 99))[:10])}

## Recommendations

{chr(10).join(f"1. {r}" for r in (vb.get('recommendations', []) or [])[:5])}
{chr(10).join(f"1. {r}" for r in (sp.get('recommendations', []) or [])[:5])}

---
*Generated by MARQED Layered Analysis Service*
"""
        return md

    def _generate_technical_report_content(
        self,
        data: Dict[str, Any],
        include_code: bool
    ) -> str:
        """Generate technical deep-dive report."""
        session = data["session"]
        vb = data.get("vbscript") or {}
        sp = data.get("stored_procedures") or {}

        md = f"""# Technical Analysis Report: {session['name']}

## VBScript/ASP Analysis

### Overview
- **Files Analyzed:** {vb.get('file_count', 0)}
- **Total Lines:** {vb.get('total_lines', 0):,}
- **Complexity Score:** {vb.get('complexity_score', 'N/A')}
- **Modernization Score:** {vb.get('modernization_score', 'N/A')}

### Security Findings
"""
        for finding in (vb.get('security_findings', []) or [])[:10]:
            if isinstance(finding, dict):
                md += f"\n#### {finding.get('type', 'Unknown')}\n"
                md += f"- **Severity:** {finding.get('severity', 'Unknown')}\n"
                md += f"- **Description:** {finding.get('description', '')}\n"
                if include_code and finding.get('code_snippet'):
                    md += f"\n```vbscript\n{finding.get('code_snippet')}\n```\n"

        md += f"""

## Stored Procedure Analysis

### Overview
- **Procedures Analyzed:** {sp.get('procedure_count', 0)}
- **Total Lines:** {sp.get('total_lines', 0):,}

### Complexity Metrics
"""
        complexity = sp.get('complexity_metrics', {}) or {}
        for metric, value in complexity.items():
            md += f"- **{metric}:** {value}\n"

        md += "\n### Vendor-Specific Patterns\n"
        vendor = sp.get('vendor_specific_patterns', {}) or {}
        for pattern, count in vendor.items():
            md += f"- {pattern}: {count} occurrences\n"

        md += "\n---\n*Generated by MARQED Layered Analysis Service*\n"
        return md

    def _generate_csv_backlog(self, improvements: List[ImprovementItem]) -> str:
        """Generate CSV export of improvements."""
        output = StringIO()
        output.write("ID,Title,Category,Type,Priority,Effort (days),Impact,Risk,Status\n")

        for item in improvements:
            output.write(
                f'"{item.id}","{item.title}","{item.category}",'
                f'"{item.item_type}",{item.priority},{item.effort_days},'
                f'"{item.business_impact}","{item.risk_if_not_done}","{item.status}"\n'
            )

        return output.getvalue()

    def _generate_jira_import(self, improvements: List[ImprovementItem]) -> str:
        """Generate Jira import format."""
        items = []
        for item in improvements:
            items.append({
                "Summary": item.title,
                "Description": item.description or "",
                "Issue Type": "Improvement",
                "Priority": self._map_priority(item.priority),
                "Labels": f"{item.category},{item.item_type}",
                "Story Points": self._effort_to_points(item.effort_days),
                "Custom field (Business Impact)": item.business_impact,
                "Custom field (Risk)": item.risk_if_not_done
            })
        return json.dumps(items, indent=2)

    def _map_priority(self, priority: int) -> str:
        """Map numeric priority to Jira priority."""
        mapping = {1: "Highest", 2: "High", 3: "Medium", 4: "Low", 5: "Lowest"}
        return mapping.get(priority, "Medium")

    def _effort_to_points(self, days: float) -> int:
        """Convert effort days to story points."""
        if days <= 1:
            return 1
        elif days <= 2:
            return 2
        elif days <= 3:
            return 3
        elif days <= 5:
            return 5
        elif days <= 8:
            return 8
        else:
            return 13

    def _create_roadmap(
        self,
        data: Dict[str, Any],
        improvements: List[ImprovementItem],
        team_size: int
    ) -> Dict[str, Any]:
        """Create migration roadmap."""
        # Group by priority
        by_priority = {}
        for item in improvements:
            if item.priority not in by_priority:
                by_priority[item.priority] = []
            by_priority[item.priority].append(item)

        # Calculate phases
        phases = []
        current_week = 0

        # Phase 1: Critical security and quick wins
        phase1_items = [i for i in improvements if i.priority <= 2]
        phase1_effort = sum(i.effort_days for i in phase1_items)
        phase1_weeks = max(1, int(phase1_effort / (team_size * 5)))
        phases.append({
            "phase": 1,
            "name": "Critical Fixes & Quick Wins",
            "start_week": current_week + 1,
            "end_week": current_week + phase1_weeks,
            "items": len(phase1_items),
            "effort_days": phase1_effort
        })
        current_week += phase1_weeks

        # Phase 2: Strategic improvements
        phase2_items = [i for i in improvements if i.priority == 3]
        phase2_effort = sum(i.effort_days for i in phase2_items)
        phase2_weeks = max(1, int(phase2_effort / (team_size * 5)))
        phases.append({
            "phase": 2,
            "name": "Strategic Improvements",
            "start_week": current_week + 1,
            "end_week": current_week + phase2_weeks,
            "items": len(phase2_items),
            "effort_days": phase2_effort
        })
        current_week += phase2_weeks

        # Phase 3: Technical debt
        phase3_items = [i for i in improvements if i.priority >= 4]
        phase3_effort = sum(i.effort_days for i in phase3_items)
        phase3_weeks = max(1, int(phase3_effort / (team_size * 5)))
        phases.append({
            "phase": 3,
            "name": "Technical Debt Reduction",
            "start_week": current_week + 1,
            "end_week": current_week + phase3_weeks,
            "items": len(phase3_items),
            "effort_days": phase3_effort
        })

        total_effort = sum(i.effort_days for i in improvements)
        total_weeks = sum(p["end_week"] - p["start_week"] + 1 for p in phases)

        return {
            "team_size": team_size,
            "total_items": len(improvements),
            "total_effort_days": total_effort,
            "total_weeks": total_weeks,
            "phases": phases
        }

    def _generate_roadmap_content(self, roadmap: Dict[str, Any]) -> str:
        """Generate roadmap markdown content."""
        md = f"""# Migration Roadmap

## Overview
- **Team Size:** {roadmap['team_size']} developers
- **Total Items:** {roadmap['total_items']}
- **Total Effort:** {roadmap['total_effort_days']:.0f} days
- **Estimated Duration:** {roadmap['total_weeks']} weeks

## Phases

"""
        for phase in roadmap['phases']:
            md += f"""### Phase {phase['phase']}: {phase['name']}
- **Timeline:** Week {phase['start_week']} - {phase['end_week']}
- **Items:** {phase['items']}
- **Effort:** {phase['effort_days']:.0f} days

"""
        return md

    def _generate_swot_slides(self, swot: SWOTAnalysis) -> List[Dict[str, Any]]:
        """Generate SWOT presentation slides."""
        return [
            {
                "title": "SWOT Analysis Overview",
                "type": "title",
                "content": "Legacy System Assessment"
            },
            {
                "title": "Strengths",
                "type": "bullets",
                "items": [
                    s.get("title", s) if isinstance(s, dict) else s
                    for s in (swot.strengths or [])[:6]
                ]
            },
            {
                "title": "Weaknesses",
                "type": "bullets",
                "items": [
                    w.get("title", w) if isinstance(w, dict) else w
                    for w in (swot.weaknesses or [])[:6]
                ]
            },
            {
                "title": "Opportunities",
                "type": "bullets",
                "items": [
                    o.get("title", o) if isinstance(o, dict) else o
                    for o in (swot.opportunities or [])[:6]
                ]
            },
            {
                "title": "Threats",
                "type": "bullets",
                "items": [
                    t.get("title", t) if isinstance(t, dict) else t
                    for t in (swot.threats or [])[:6]
                ]
            },
            {
                "title": "Migration Readiness",
                "type": "metrics",
                "data": swot.migration_readiness or {}
            }
        ]

    def _render_slides_to_html(self, slides: List[Dict[str, Any]]) -> str:
        """Render slides to HTML presentation."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>SWOT Presentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .slide { min-height: 100vh; padding: 60px; box-sizing: border-box; }
        .slide:nth-child(odd) { background: #f8f9fa; }
        h1 { color: #2c3e50; font-size: 2.5em; }
        h2 { color: #3498db; font-size: 2em; }
        ul { font-size: 1.4em; line-height: 1.8; }
        .metric { display: inline-block; margin: 20px; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 3em; font-weight: bold; color: #2980b9; }
        .metric-label { color: #7f8c8d; margin-top: 10px; }
    </style>
</head>
<body>
"""
        for slide in slides:
            html += f'<div class="slide">\n'
            html += f'<h2>{slide["title"]}</h2>\n'

            if slide["type"] == "title":
                html += f'<h1>{slide.get("content", "")}</h1>\n'
            elif slide["type"] == "bullets":
                html += '<ul>\n'
                for item in slide.get("items", []):
                    html += f'<li>{item}</li>\n'
                html += '</ul>\n'
            elif slide["type"] == "metrics":
                for key, value in slide.get("data", {}).items():
                    html += f'''
<div class="metric">
    <div class="metric-value">{value}</div>
    <div class="metric-label">{key}</div>
</div>
'''
            html += '</div>\n'

        html += '</body></html>'
        return html

    async def list_reports(
        self,
        session_id: UUID,
        report_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List reports for a session."""
        query = select(AnalysisReport).where(AnalysisReport.session_id == session_id)

        if report_type:
            query = query.where(AnalysisReport.report_type == report_type)

        reports = self.db.execute(query).scalars().all()

        return [
            {
                "id": str(r.id),
                "type": r.report_type,
                "format": r.format,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reports
        ]

    async def get_report(self, report_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a specific report."""
        report = self.db.get(AnalysisReport, report_id)
        if not report:
            return None

        return {
            "id": str(report.id),
            "session_id": str(report.session_id),
            "type": report.report_type,
            "format": report.format,
            "content": report.content,
            "metadata": report.metadata,
            "created_at": report.created_at.isoformat() if report.created_at else None
        }
