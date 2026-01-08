"""
Cycle 5: Final Synthesis Prompts

Target LLMs: Claude Opus 4.5 (premium reasoning)
Focus: Executive-level synthesis and strategic recommendations
"""

CYCLE5_PROMPTS = {
    "system": """You are a senior technical architect performing final synthesis
of a comprehensive code analysis. Your output will be used by:
- Engineering leadership for planning
- Product managers for roadmapping
- Architects for technical decisions

Be thorough, accurate, and strategic in your analysis.""",

    "executive_summary": """Create an executive summary of this code analysis:

Project: {project_name}
Repository: {repository}
Lines of Code: {loc}
Languages: {languages}

Analysis Results:
{analysis_summary}

Quality Score: {quality_score}%
Confidence: {confidence}%

Generate:
1. **Executive Summary** (2-3 paragraphs)
   - Project purpose and architecture
   - Key strengths and capabilities
   - Critical risks and technical debt

2. **Key Metrics**
   - Complexity score
   - Test coverage estimate
   - Documentation quality
   - Security posture

3. **Strategic Recommendations** (top 5)
   - Prioritized action items
   - Estimated effort
   - Business impact

4. **Migration/Modernization Path** (if applicable)
   - Current state assessment
   - Target architecture vision
   - Phased approach""",

    "final_backlog": """Synthesize the final project backlog:

Epics:
{epics}

Stories:
{stories}

Technical Debt:
{tech_debt}

Issues Detected:
{issues}

Create a prioritized backlog with:
1. **Release 1** (MVP/Quick Wins)
   - Stories that can ship immediately
   - Critical bug fixes
   - Security patches

2. **Release 2** (Core Value)
   - Main feature implementations
   - Architecture improvements
   - Integration work

3. **Release 3** (Polish & Scale)
   - Performance optimizations
   - UX improvements
   - Technical debt reduction

For each item:
- ID and title
- Priority (P0-P3)
- Effort (story points)
- Dependencies
- Risk level""",

    "architecture_recommendations": """Provide architecture recommendations:

Current Architecture Analysis:
{architecture}

Detected Patterns:
{patterns}

Issues and Tech Debt:
{issues}

Recommend:
1. **Keep**: What's working well
2. **Change**: What needs refactoring
3. **Add**: Missing capabilities
4. **Remove**: Deprecated/dead code

For major changes:
- Before/After diagrams (text-based)
- Migration strategy
- Risk mitigation
- Estimated timeline""",

    "confidence_calibration": """Calibrate confidence scores for this analysis:

Raw Analyses:
{raw_analyses}

Cross-Validation Results:
{cross_validation}

Conflict Resolutions:
{conflicts}

For each major finding:
1. Confidence level (0-100%)
2. Evidence strength (weak/moderate/strong)
3. LLM agreement (unanimous/majority/split)
4. Human review needed (yes/no)

Final calibrated scores:
- Overall extraction confidence
- Per-module confidence
- Risk-adjusted confidence"""
}
