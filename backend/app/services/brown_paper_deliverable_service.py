"""
Brown Paper Deliverable Service - Week 159 (Fase 24.10)

Generates a complete set of markdown deliverables from a Brown Paper analysis session.
Writes to the project's docs/ folder and syncs with the database.

Output structure:
```
{output_dir}/
├── README.md                           # Deliverables index
├── project-summary.md                  # Executive summary
├── epics/
│   ├── index.md                        # Epic overview with drill-down links
│   ├── EPIC-001/
│   │   ├── epic.md                     # Epic details
│   │   ├── FEAT-001/
│   │   │   ├── feature.md              # Feature details
│   │   │   ├── STORY-001.md            # User story with AC
│   │   │   └── STORY-002.md
│   │   └── FEAT-002/
│   │       └── ...
│   └── EPIC-002/
│       └── ...
├── user-journeys/
│   └── index.md                        # User journey mapping
├── workflows/
│   └── index.md                        # Recommended workflows
├── non-functional-requirements/
│   └── index.md                        # NFRs (security, performance, etc.)
├── architecture/
│   └── index.md                        # Architecture assessment
├── risks/
│   └── index.md                        # Risk register
├── estimation/
│   └── index.md                        # FP/SP estimation report
└── migration-strategy/
    └── index.md                        # Migration approach (if applicable)
```
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class BrownPaperDeliverableService:
    """
    Generate and write complete deliverable documentation from Brown Paper analysis.

    Takes the output of MarQedBrownPaperWorkflow.generate_tasks() and the full
    session data to produce a comprehensive docs folder.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    async def generate_deliverables(
        self,
        session: Any,
        tasks: Dict[str, Any],
        enhanced_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate all deliverable files from a Brown Paper session.

        Args:
            session: MarQedBrownPaperSession with answers, specification, etc.
            tasks: Output from generate_tasks() with epics, features, stories, summary
            enhanced_analysis: Optional enhanced analysis results (6-phase)

        Returns:
            Summary with file counts and paths
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        files_created = []

        # Extract data
        epics = tasks.get("epics", [])
        features = tasks.get("features", [])
        stories = tasks.get("stories", [])
        summary = tasks.get("summary", {})
        spec = getattr(session, 'specification', None) or {}
        if hasattr(spec, 'to_dict'):
            spec = spec.to_dict()
        answers = self._extract_answers(session)
        analysis = getattr(session, 'analysis', None) or {}
        if hasattr(analysis, 'to_dict'):
            analysis = analysis.to_dict()

        # 1. README index
        files_created.append(self._write_readme(session, summary, epics))

        # 2. Project summary
        files_created.append(self._write_project_summary(session, summary, epics, features, stories, spec))

        # 3. Epics hierarchy (with drill-down)
        epic_files = self._write_epics_hierarchy(epics, features, stories, summary)
        files_created.extend(epic_files)

        # 4. User journeys
        files_created.append(self._write_user_journeys(epics, features, stories, analysis))

        # 5. Workflows
        files_created.append(self._write_workflows(spec, summary))

        # 6. Non-functional requirements
        files_created.append(self._write_nfr(spec, enhanced_analysis))

        # 7. Architecture assessment
        files_created.append(self._write_architecture(spec, analysis, enhanced_analysis))

        # 8. Risk register
        files_created.append(self._write_risks(spec))

        # 9. Estimation report
        files_created.append(self._write_estimation(summary, epics, features, stories))

        # 10. Migration strategy (if applicable)
        files_created.append(self._write_migration_strategy(spec, answers))

        logger.info(f"Generated {len(files_created)} deliverable files to {self.output_dir}")

        return {
            "output_dir": str(self.output_dir),
            "files_created": len(files_created),
            "file_paths": [str(f) for f in files_created],
            "epics": len(epics),
            "features": len(features),
            "stories": len(stories),
        }

    # ========================================================================
    # HELPER: Extract answers
    # ========================================================================

    def _extract_answers(self, session: Any) -> Dict[str, str]:
        """Extract answer texts from session."""
        answers = {}
        raw = getattr(session, 'answers', None) or {}
        for key, val in raw.items():
            if hasattr(val, 'text'):
                answers[key] = val.text
            elif hasattr(val, 'answer'):
                answers[key] = val.answer
            elif isinstance(val, str):
                answers[key] = val
            else:
                answers[key] = str(val)
        return answers

    # ========================================================================
    # 1. README
    # ========================================================================

    def _write_readme(self, session: Any, summary: Dict, epics: List) -> Path:
        """Write the deliverables README index."""
        project_name = getattr(session, 'project_name', 'Unknown Project')
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        content = f"""# {project_name} - Deliverables

**Generated**: {now}
**Workflow**: MarQed Brown Paper Analysis
**Status**: {getattr(session, 'status', 'completed')}

---

## Documents

| Document | Description |
|----------|-------------|
| [Project Summary](project-summary.md) | Executive summary met key metrics |
| [Epics Overview](epics/index.md) | {summary.get('total_epics', len(epics))} epics met features en stories (drill-down) |
| [User Journeys](user-journeys/index.md) | Gebruikerspaden door de applicatie |
| [Workflows](workflows/index.md) | Aanbevolen workflows voor migratie/ontwikkeling |
| [Non-Functional Requirements](non-functional-requirements/index.md) | Security, performance, schaalbaarheid, etc. |
| [Architecture](architecture/index.md) | Architectuur assessment en aanbevelingen |
| [Risks](risks/index.md) | Risk register met mitigatie strategieen |
| [Estimation](estimation/index.md) | Function Points / Story Points schatting |
| [Migration Strategy](migration-strategy/index.md) | Migratie aanpak en planning |

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Epics | {summary.get('total_epics', len(epics))} |
| Total Features | {summary.get('total_features', 0)} |
| Total Stories | {summary.get('total_stories', 0)} |
| Estimated FP | {summary.get('estimated_fp', summary.get('total_function_points', 0))} |
| Estimated SP | {summary.get('total_story_points', 0)} |
| Extraction Method | {summary.get('extraction_method', 'business-driven')} |

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = self.output_dir / "README.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 2. PROJECT SUMMARY
    # ========================================================================

    def _write_project_summary(
        self, session: Any, summary: Dict,
        epics: List, features: List, stories: List,
        spec: Dict
    ) -> Path:
        project_name = getattr(session, 'project_name', 'Unknown Project')
        project_path = getattr(session, 'project_path', '')
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Extract spec sections
        exec_summary = spec.get('executive_summary', '')
        current_state = spec.get('current_state', spec.get('as_is', ''))
        if isinstance(current_state, dict):
            current_state = current_state.get('description', str(current_state))

        content = f"""# {project_name} - Project Summary

**Generated**: {now}
**Source Path**: `{project_path}`
**Extraction Method**: {summary.get('extraction_method', 'business-driven')}

---

## Executive Summary

{exec_summary or 'Geen executive summary beschikbaar.'}

## Current State (AS-IS)

{current_state or 'Beschrijving van huidige staat niet beschikbaar.'}

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Epics | {summary.get('total_epics', len(epics))} |
| Total Features | {summary.get('total_features', len(features))} |
| Total Stories | {summary.get('total_stories', len(stories))} |
| Total Function Points | {summary.get('estimated_fp', summary.get('total_function_points', 0))} |
| Total Story Points | {summary.get('total_story_points', 0)} |
| FP Confidence | {summary.get('fp_confidence', 'N/A')} |

## Epic Overview

| # | Epic | Domain | Features | Stories | FP | Complexity |
|---|------|--------|----------|---------|----|------------|
"""
        for i, epic in enumerate(epics, 1):
            epic_id = epic.get('id', f'EPIC-{i:03d}')
            epic_features = [f for f in features if f.get('epic_id') == epic_id]
            epic_stories = [s for s in stories if s.get('epic_id') == epic_id]
            content += (
                f"| {i} | [{epic.get('title', '')}](epics/{epic_id}/epic.md) "
                f"| {epic.get('domain', '')} "
                f"| {len(epic_features)} "
                f"| {len(epic_stories)} "
                f"| {epic.get('estimated_fp', 0)} "
                f"| {epic.get('complexity', 'medium')} |\n"
            )

        content += """
---
*Generated by MarQed Brown Paper Analysis*
"""
        path = self.output_dir / "project-summary.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 3. EPICS HIERARCHY (with drill-down)
    # ========================================================================

    def _write_epics_hierarchy(
        self, epics: List, features: List, stories: List, summary: Dict
    ) -> List[Path]:
        files = []
        epics_dir = self.output_dir / "epics"
        epics_dir.mkdir(parents=True, exist_ok=True)

        # Epics index
        files.append(self._write_epics_index(epics, features, stories, summary, epics_dir))

        # Individual epic/feature/story files
        for i, epic in enumerate(epics, 1):
            epic_id = epic.get('id', f'EPIC-{i:03d}')
            epic_dir = epics_dir / epic_id
            epic_dir.mkdir(parents=True, exist_ok=True)

            epic_features = [f for f in features if f.get('epic_id') == epic_id]
            epic_stories = [s for s in stories if s.get('epic_id') == epic_id]

            # Epic file
            files.append(self._write_epic_file(epic, epic_features, epic_stories, epic_dir))

            # Feature files
            for j, feat in enumerate(epic_features, 1):
                feat_id = feat.get('id', f'FEAT-{j:03d}')
                feat_dir = epic_dir / feat_id
                feat_dir.mkdir(parents=True, exist_ok=True)

                feat_stories = [s for s in stories if s.get('feature_id') == feat_id]

                files.append(self._write_feature_file(feat, feat_stories, feat_dir))

                # Story files
                for story in feat_stories:
                    files.append(self._write_story_file(story, feat_dir))

        return files

    def _write_epics_index(
        self, epics: List, features: List, stories: List,
        summary: Dict, epics_dir: Path
    ) -> Path:
        content = f"""# Epics Overview

**Total**: {len(epics)} epics, {len(features)} features, {len(stories)} stories
**Estimated FP**: {summary.get('estimated_fp', summary.get('total_function_points', 0))}
**Estimated SP**: {summary.get('total_story_points', 0)}

---

"""
        for i, epic in enumerate(epics, 1):
            epic_id = epic.get('id', f'EPIC-{i:03d}')
            epic_features = [f for f in features if f.get('epic_id') == epic_id]
            epic_stories = [s for s in stories if s.get('epic_id') == epic_id]

            content += f"""## [{epic_id}: {epic.get('title', '')}]({epic_id}/epic.md)

**Domain**: {epic.get('domain', 'N/A')} | **Complexity**: {epic.get('complexity', 'medium')} | **FP**: {epic.get('estimated_fp', 0)}

{epic.get('description', '')[:200]}{'...' if len(epic.get('description', '')) > 200 else ''}

| Feature | Stories | SP | Complexity |
|---------|---------|-----|------------|
"""
            for feat in epic_features:
                feat_id = feat.get('id', '')
                feat_stories = [s for s in stories if s.get('feature_id') == feat_id]
                content += (
                    f"| [{feat.get('title', '')}]({epic_id}/{feat_id}/feature.md) "
                    f"| {len(feat_stories)} "
                    f"| {feat.get('estimated_sp', 0)} "
                    f"| {feat.get('complexity', 'medium')} |\n"
                )

            content += "\n---\n\n"

        content += "*Generated by MarQed Brown Paper Analysis*\n"
        path = epics_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    def _write_epic_file(self, epic: Dict, epic_features: List, epic_stories: List, epic_dir: Path) -> Path:
        epic_id = epic.get('id', 'EPIC-???')
        total_sp = sum(f.get('estimated_sp', 0) for f in epic_features)

        content = f"""# {epic_id}: {epic.get('title', '')}

## Description

{epic.get('description', 'Geen beschrijving beschikbaar.')}

## Details

| Property | Value |
|----------|-------|
| Domain | {epic.get('domain', 'N/A')} |
| Complexity | {epic.get('complexity', 'medium')} |
| Estimated FP | {epic.get('estimated_fp', 0)} |
| Total SP | {total_sp} |
| Estimated Weeks | {epic.get('estimated_weeks', 'N/A')} |
| Source Modules | {', '.join(epic.get('source_modules', [])[:5]) or 'N/A'} |

## Features ({len(epic_features)})

| # | Feature | Stories | SP | Complexity |
|---|---------|---------|-----|------------|
"""
        for j, feat in enumerate(epic_features, 1):
            feat_id = feat.get('id', '')
            feat_stories = [s for s in epic_stories if s.get('feature_id') == feat_id]
            content += (
                f"| {j} | [{feat.get('title', '')}]({feat_id}/feature.md) "
                f"| {len(feat_stories)} "
                f"| {feat.get('estimated_sp', 0)} "
                f"| {feat.get('complexity', 'medium')} |\n"
            )

        content += f"""
## Stories ({len(epic_stories)})

| # | Story | Type | SP | Feature |
|---|-------|------|----|---------|
"""
        for k, story in enumerate(epic_stories, 1):
            feat_id = story.get('feature_id', '')
            content += (
                f"| {k} | {story.get('title', '')} "
                f"| {story.get('story_type', '')} "
                f"| {story.get('estimated_sp', 0)} "
                f"| {feat_id} |\n"
            )

        content += """
---
*Generated by MarQed Brown Paper Analysis*
"""
        path = epic_dir / "epic.md"
        path.write_text(content, encoding='utf-8')
        return path

    def _write_feature_file(self, feat: Dict, feat_stories: List, feat_dir: Path) -> Path:
        feat_id = feat.get('id', 'FEAT-???')
        total_sp = sum(s.get('estimated_sp', 0) for s in feat_stories)

        content = f"""# {feat_id}: {feat.get('title', '')}

## Description

{feat.get('description', 'Geen beschrijving beschikbaar.')}

## Details

| Property | Value |
|----------|-------|
| Epic | {feat.get('epic_id', 'N/A')} |
| Complexity | {feat.get('complexity', 'medium')} |
| Estimated FP | {feat.get('estimated_fp', 0)} |
| Total SP | {total_sp} |
| Source Modules | {', '.join(feat.get('source_modules', [])[:5]) or 'N/A'} |

## User Stories ({len(feat_stories)})

"""
        for k, story in enumerate(feat_stories, 1):
            story_id = story.get('id', f'STORY-{k:03d}')
            ac = story.get('acceptance_criteria', [])

            content += f"""### [{story_id}: {story.get('title', '')}]({story_id}.md)

**Type**: {story.get('story_type', 'N/A')} | **SP**: {story.get('estimated_sp', 0)} | **Complexity**: {story.get('complexity', 'medium')}

{story.get('description', '')[:150]}{'...' if len(story.get('description', '')) > 150 else ''}

**Acceptance Criteria**: {len(ac)} criteria defined

---

"""

        content += "*Generated by MarQed Brown Paper Analysis*\n"
        path = feat_dir / "feature.md"
        path.write_text(content, encoding='utf-8')
        return path

    def _write_story_file(self, story: Dict, feat_dir: Path) -> Path:
        story_id = story.get('id', 'STORY-???')
        ac = story.get('acceptance_criteria', [])

        content = f"""# {story_id}: {story.get('title', '')}

## User Story

{story.get('description', story.get('title', ''))}

## Details

| Property | Value |
|----------|-------|
| Epic | {story.get('epic_id', 'N/A')} |
| Feature | {story.get('feature_id', 'N/A')} |
| Type | {story.get('story_type', 'N/A')} |
| Story Points | {story.get('estimated_sp', 0)} |
| Complexity | {story.get('complexity', 'medium')} |

## Acceptance Criteria

"""
        if ac:
            for i, criterion in enumerate(ac, 1):
                content += f"{i}. {criterion}\n"
        else:
            content += "- [ ] Acceptance criteria nog te definieren\n"

        source_files = story.get('source_files', [])
        if source_files:
            content += f"""
## Source Files

"""
            for sf in source_files:
                content += f"- `{sf}`\n"

        content += """
---
*Generated by MarQed Brown Paper Analysis*
"""
        path = feat_dir / f"{story_id}.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 4. USER JOURNEYS
    # ========================================================================

    def _write_user_journeys(
        self, epics: List, features: List, stories: List,
        analysis: Dict
    ) -> Path:
        journeys_dir = self.output_dir / "user-journeys"
        journeys_dir.mkdir(parents=True, exist_ok=True)

        # Group stories by type to infer journeys
        story_types = {}
        for story in stories:
            st = story.get('story_type', 'unknown')
            if st not in story_types:
                story_types[st] = []
            story_types[st].append(story)

        content = """# User Journeys

Overzicht van gebruikerspaden door de applicatie, afgeleid uit de geanalyseerde code.

---

## Journey Mapping per Domain

"""
        for epic in epics:
            epic_id = epic.get('id', '')
            domain = epic.get('domain', 'Unknown')
            epic_features = [f for f in features if f.get('epic_id') == epic_id]

            content += f"""### {domain}

**Epic**: [{epic_id}](../epics/{epic_id}/epic.md) - {epic.get('title', '')}

**Gebruikerspad**:

```
"""
            # Build a simple flow from features
            for j, feat in enumerate(epic_features):
                arrow = " --> " if j < len(epic_features) - 1 else ""
                content += f"  [{feat.get('title', '')}]{arrow}\n"

            content += f"""```

**Features in dit pad**: {len(epic_features)}

| Stap | Feature | Stories | Beschrijving |
|------|---------|---------|-------------|
"""
            for j, feat in enumerate(epic_features, 1):
                feat_id = feat.get('id', '')
                feat_stories = [s for s in stories if s.get('feature_id') == feat_id]
                content += (
                    f"| {j} | {feat.get('title', '')} "
                    f"| {len(feat_stories)} "
                    f"| {feat.get('description', '')[:80]} |\n"
                )

            content += "\n---\n\n"

        # Story type distribution
        content += """## Story Type Distributie

| Type | Aantal | Percentage |
|------|--------|------------|
"""
        total = len(stories) or 1
        for st, st_stories in sorted(story_types.items(), key=lambda x: -len(x[1])):
            pct = len(st_stories) / total * 100
            content += f"| {st} | {len(st_stories)} | {pct:.1f}% |\n"

        content += """
---
*Generated by MarQed Brown Paper Analysis*
"""
        path = journeys_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 5. WORKFLOWS
    # ========================================================================

    def _write_workflows(self, spec: Dict, summary: Dict) -> Path:
        workflows_dir = self.output_dir / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        method = summary.get('extraction_method', 'business-driven')

        content = f"""# Workflows

Overzicht van aanbevolen workflows voor dit project.

---

## Uitgevoerde Workflow

| Property | Value |
|----------|-------|
| Workflow Type | Brown Paper Analysis |
| Extraction Method | {method} |
| Generated Epics | {summary.get('total_epics', 0)} |
| Generated Features | {summary.get('total_features', 0)} |
| Generated Stories | {summary.get('total_stories', 0)} |

## Brown Paper Workflow Stappen

```
1. Applicatie Intake (8 BMAD vragen)
   |
2. Code Analyse (dependency graph, module scan)
   |
3. Business Domain Extraction (LLM-driven)
   |
4. Epic/Feature/Story Generation (business-driven)
   |
5. Estimation (FP/SP berekening)
   |
6. Review & Approval
   |
7. Export (deliverables, dashboard, database)
```

## Aanbevolen Vervolg-Workflows

| Workflow | Wanneer | Beschrijving |
|----------|---------|-------------|
| **Migration Planning** | Na Brown Paper goedkeuring | Definieer target state, migratiestrategie, data migratie |
| **Sprint Planning** | Na epic goedkeuring | Plan sprints op basis van epics en prioriteiten |
| **Quality Audit** | Parallel aan migratie | Continue kwaliteitsmonitoring |
| **Security Scan** | Voor migratie start | CWE scanner suite uitvoeren |
| **Estimation Review** | Na eerste sprint | FP/SP kalibreren op basis van actuals |

## MarQed Platform Workflows

| Workflow | Type | Status |
|----------|------|--------|
| GREEN_PAPER | Greenfield project specificatie | Beschikbaar |
| BROWN_PAPER | Legacy analyse & onboarding | **Gebruikt** |
| MIGRATION | Migratie planning & uitvoering | Beschikbaar |
| QUALITY | Kwaliteitsaudit & gates | Beschikbaar |
| QUICKSCAN | 15-min legacy assessment | Beschikbaar |
| SECURITY | CWE security scanner | Beschikbaar |

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = workflows_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 6. NON-FUNCTIONAL REQUIREMENTS
    # ========================================================================

    def _write_nfr(self, spec: Dict, enhanced_analysis: Optional[Dict]) -> Path:
        nfr_dir = self.output_dir / "non-functional-requirements"
        nfr_dir.mkdir(parents=True, exist_ok=True)

        # Extract NFRs from spec and enhanced analysis
        risks = spec.get('risks', [])
        if isinstance(risks, list):
            security_risks = [r for r in risks if isinstance(r, dict) and 'security' in str(r).lower()]
            performance_risks = [r for r in risks if isinstance(r, dict) and 'performance' in str(r).lower()]
        else:
            security_risks = []
            performance_risks = []

        # Enhanced analysis NFR data
        phase1 = {}
        if enhanced_analysis and isinstance(enhanced_analysis, dict):
            phase1 = enhanced_analysis.get('phase1_result', {})

        sig_metrics = phase1.get('sig_metrics', {})
        code_analysis = phase1.get('code_analysis', {})

        content = f"""# Non-Functional Requirements

Overzicht van niet-functionele eisen afgeleid uit de code-analyse.

---

## Security

| Aspect | Status | Toelichting |
|--------|--------|-------------|
| Authentication | Te beoordelen | Authenticatie mechanismen analyseren |
| Authorization | Te beoordelen | Autorisatie model in kaart brengen |
| Data Protection | Te beoordelen | Gevoelige data identificeren |
| Input Validation | Te beoordelen | XSS, SQL injection, path traversal |
| Secrets Management | Te beoordelen | Hardcoded credentials detecteren |

**Security Risks Geidentificeerd**: {len(security_risks)}

## Performance

| Aspect | Status | Toelichting |
|--------|--------|-------------|
| Response Time | Te beoordelen | Max response time per endpoint |
| Throughput | Te beoordelen | Concurrent users / requests per seconde |
| Database | Te beoordelen | Query performance, indexering |
| Caching | Te beoordelen | Cache strategie |

**Performance Risks Geidentificeerd**: {len(performance_risks)}

## Maintainability

| Metric | Value | Target |
|--------|-------|--------|
| SIG Overall Rating | {sig_metrics.get('overall_rating', 'N/A')} | >= 3.0 |
| Average Complexity | {code_analysis.get('average_complexity', 'N/A')} | < 10 |
| Documentation Coverage | {code_analysis.get('documentation_coverage', 'N/A')}% | >= 80% |

## Reliability

| Aspect | Requirement |
|--------|-------------|
| Uptime | 99.5% (standaard) |
| Recovery Time | < 4 uur |
| Data Backup | Dagelijks, 30 dagen retentie |
| Error Handling | Graceful degradation |

## Scalability

| Aspect | Requirement |
|--------|-------------|
| Horizontal Scaling | Container-based deployment |
| Database Scaling | Connection pooling, read replicas |
| File Storage | Object storage voor uploads |

## Compliance

| Standard | Toepasselijkheid |
|----------|-----------------|
| GDPR / AVG | Te beoordelen |
| ISO 27001 | Te beoordelen |
| OWASP Top 10 | Aanbevolen |
| NEN-ISO 25010 | Software kwaliteitsmodel |

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = nfr_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 7. ARCHITECTURE
    # ========================================================================

    def _write_architecture(
        self, spec: Dict, analysis: Dict, enhanced_analysis: Optional[Dict]
    ) -> Path:
        arch_dir = self.output_dir / "architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)

        current_state = spec.get('current_state', spec.get('as_is', ''))
        if isinstance(current_state, dict):
            current_state = current_state.get('description', str(current_state))
        target_state = spec.get('target_state', spec.get('to_be', ''))
        if isinstance(target_state, dict):
            target_state = target_state.get('description', str(target_state))

        # Extract patterns from analysis
        patterns = []
        if isinstance(analysis, dict):
            patterns = analysis.get('primary_patterns', [])
        if isinstance(patterns, list):
            pattern_text = ', '.join(str(p) for p in patterns[:5]) or 'Niet gedetecteerd'
        else:
            pattern_text = str(patterns)

        content = f"""# Architecture Assessment

Architectuur analyse op basis van code-scan en domain extraction.

---

## Current Architecture (AS-IS)

{current_state or 'Huidige architectuur niet beschreven. Voer een enhanced analyse uit voor meer details.'}

### Gedetecteerde Patronen

{pattern_text}

## Target Architecture (TO-BE)

{target_state or 'Target architectuur niet beschreven. Gebruik de Migration Planning workflow.'}

## Architecture Decision Records

Nog geen ADRs gegenereerd. Gebruik de MarQed Architecture workflow om ADRs te genereren.

| ADR | Beslissing | Status |
|-----|-----------|--------|
| - | - | - |

## Component Diagram

```
[Te genereren via Enhanced Analysis of Migration Planning]
```

## Recommendations

1. Voer een **Enhanced Analysis** uit voor gedetailleerde architectuuranalyse
2. Gebruik **CWE Security Scanner** voor security assessment
3. Genereer een **Dependency Graph** voor visueel overzicht
4. Plan **Architecture Decision Records** voor key decisions

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = arch_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 8. RISKS
    # ========================================================================

    def _write_risks(self, spec: Dict) -> Path:
        risks_dir = self.output_dir / "risks"
        risks_dir.mkdir(parents=True, exist_ok=True)

        risks = spec.get('risks', spec.get('risk_register', []))
        if not isinstance(risks, list):
            risks = []

        content = """# Risk Register

Overzicht van geidentificeerde risico's en mitigatie strategieen.

---

## Risk Matrix

| # | Risico | Kans | Impact | Score | Mitigatie |
|---|--------|------|--------|-------|-----------|
"""
        if risks:
            for i, risk in enumerate(risks, 1):
                if isinstance(risk, dict):
                    name = risk.get('name', risk.get('description', f'Risk {i}'))
                    likelihood = risk.get('likelihood', risk.get('probability', 'medium'))
                    impact = risk.get('impact', 'medium')
                    mitigation = risk.get('mitigation', risk.get('response', 'Te definieren'))
                    score = risk.get('score', 'N/A')
                    content += f"| {i} | {name} | {likelihood} | {impact} | {score} | {mitigation} |\n"
                else:
                    content += f"| {i} | {risk} | medium | medium | N/A | Te definieren |\n"
        else:
            content += "| - | Geen risico's geidentificeerd | - | - | - | Voer risk assessment uit |\n"

        content += """
## Risk Categories

| Categorie | Beschrijving |
|-----------|-------------|
| **Technical** | Legacy code complexiteit, ontbrekende tests, security vulnerabilities |
| **Organisational** | Team kennis, resource beschikbaarheid, stakeholder alignment |
| **Schedule** | Timeline druk, afhankelijkheden, scope creep |
| **Quality** | Technische schuld, performance, reliability |

## Aanbevelingen

1. Voer een **Legacy Quickscan** uit voor een Go/No-Go recommendation
2. Gebruik de **CWE Security Scanner** voor gedetailleerde security risico's
3. Plan een **Risk Review** sessie met het team
4. Update dit register na elke sprint

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = risks_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 9. ESTIMATION
    # ========================================================================

    def _write_estimation(
        self, summary: Dict, epics: List, features: List, stories: List
    ) -> Path:
        est_dir = self.output_dir / "estimation"
        est_dir.mkdir(parents=True, exist_ok=True)

        total_fp = summary.get('estimated_fp', summary.get('total_function_points', 0))
        total_sp = summary.get('total_story_points', 0)
        fp_confidence = summary.get('fp_confidence', 'N/A')

        content = f"""# Estimation Report

Function Point en Story Point schattingen op basis van business domain extraction.

---

## Summary

| Metric | Value |
|--------|-------|
| Total Function Points | {total_fp} |
| Total Story Points | {total_sp} |
| FP Confidence | {fp_confidence} |
| Epics | {len(epics)} |
| Features | {len(features)} |
| Stories | {len(stories)} |

## FP per Epic

| Epic | Domain | FP | SP | Features | Stories | Complexity |
|------|--------|----|----|----------|---------|------------|
"""
        for epic in epics:
            epic_id = epic.get('id', '')
            epic_features = [f for f in features if f.get('epic_id') == epic_id]
            epic_stories = [s for s in stories if s.get('epic_id') == epic_id]
            epic_sp = sum(f.get('estimated_sp', 0) for f in epic_features)
            content += (
                f"| {epic_id} | {epic.get('domain', '')} "
                f"| {epic.get('estimated_fp', 0)} "
                f"| {epic_sp} "
                f"| {len(epic_features)} "
                f"| {len(epic_stories)} "
                f"| {epic.get('complexity', 'medium')} |\n"
            )

        content += f"""
## SP per Feature (Top 20)

| Feature | Epic | SP | Stories | Complexity |
|---------|------|----|---------|------------|
"""
        sorted_features = sorted(features, key=lambda f: f.get('estimated_sp', 0), reverse=True)
        for feat in sorted_features[:20]:
            feat_id = feat.get('id', '')
            feat_stories = [s for s in stories if s.get('feature_id') == feat_id]
            content += (
                f"| {feat.get('title', '')[:40]} | {feat.get('epic_id', '')} "
                f"| {feat.get('estimated_sp', 0)} "
                f"| {len(feat_stories)} "
                f"| {feat.get('complexity', 'medium')} |\n"
            )

        content += f"""
## Methodology

- **Function Points**: IFPUG/NESMA indicatieve telling
- **Story Points**: Afgeleid van FP (ratio ~0.19 SP/FP)
- **Confidence**: {fp_confidence}
- **Extraction Method**: {summary.get('extraction_method', 'business-driven')}

## Calibration Notes

De schattingen zijn gebaseerd op geautomatiseerde code-analyse en LLM-extractie.
Aanbevolen: kalibreer na de eerste 2-3 sprints met actuals.

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = est_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path

    # ========================================================================
    # 10. MIGRATION STRATEGY
    # ========================================================================

    def _write_migration_strategy(self, spec: Dict, answers: Dict) -> Path:
        mig_dir = self.output_dir / "migration-strategy"
        mig_dir.mkdir(parents=True, exist_ok=True)

        target_state = spec.get('target_state', spec.get('to_be', ''))
        if isinstance(target_state, dict):
            target_state = target_state.get('description', str(target_state))

        strategy = spec.get('migration_approach', spec.get('migration_strategy', ''))
        if isinstance(strategy, dict):
            strategy = strategy.get('description', str(strategy))

        data_migration = spec.get('data_migration', '')
        if isinstance(data_migration, dict):
            data_migration = data_migration.get('description', str(data_migration))

        timeline = spec.get('timeline', {})
        phases = timeline.get('phases', []) if isinstance(timeline, dict) else []

        content = f"""# Migration Strategy

Migratie aanpak en planning op basis van de Brown Paper analyse.

---

## Target State (TO-BE)

{target_state or 'Target state niet beschreven. Gebruik de Migration Planning workflow.'}

## Migration Strategy

{strategy or 'Migratiestrategie niet beschreven. Gebruik de Migration Planning workflow.'}

## Data Migration

{data_migration or 'Data migratie aanpak niet beschreven.'}

## Timeline

"""
        if phases:
            content += "| Fase | Beschrijving | Duur |\n|------|-------------|------|\n"
            for phase in phases:
                if isinstance(phase, dict):
                    content += f"| {phase.get('name', '')} | {phase.get('description', '')} | {phase.get('duration', '')} |\n"
                else:
                    content += f"| {phase} | - | - |\n"
        else:
            content += "Geen timeline beschikbaar. Gebruik Sprint Planning na epic goedkeuring.\n"

        content += """
## Recommended Approach

1. **Strangler Fig Pattern**: Geleidelijk vervangen van legacy modules
2. **Database-First**: Migreer data model als fundament
3. **API Layer**: Bouw nieuwe API bovenop legacy database
4. **Feature Toggle**: Parallel draaien van oud en nieuw
5. **Incremental Rollout**: Per business domain uitrollen

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Functional Parity | 100% van kritieke functies |
| Performance | Gelijk of beter dan legacy |
| Test Coverage | >= 80% |
| Zero Data Loss | Geen dataverlies bij migratie |
| Rollback Capability | < 1 uur rollback tijd |

---
*Generated by MarQed Brown Paper Analysis*
"""
        path = mig_dir / "index.md"
        path.write_text(content, encoding='utf-8')
        return path
