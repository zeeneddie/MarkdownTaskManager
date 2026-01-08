"""
Cycle 4: Quality Synthesis Prompts

Target LLMs: Gemini Pro or OpenAI
Focus: Synthesizing findings into quality-scored deliverables
"""

CYCLE4_PROMPTS = {
    "system": """You are a quality synthesis agent. Your role is to combine
multiple analyses into coherent, quality-scored deliverables.

Your outputs should be:
- Well-structured and comprehensive
- Quality-scored with confidence levels
- Actionable for development teams
- Suitable for project planning""",

    "story_generation": """Generate user stories from these code analyses:

Module Analysis:
{module_analysis}

Integration Points:
{integration_points}

Detected Issues:
{issues}

Generate INVEST-compliant user stories:
- Independent: No dependencies between stories
- Negotiable: Flexible implementation
- Valuable: Clear business value
- Estimable: Can be sized
- Small: Fits in a sprint
- Testable: Clear acceptance criteria

Format each story as:
```
AS A [user type]
I WANT [action]
SO THAT [benefit]

Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2

Technical Notes:
- Implementation approach
- Dependencies
- Estimated effort (story points)
```""",

    "epic_synthesis": """Synthesize these user stories into epics:

Stories:
{stories}

Group into epics based on:
1. Feature domains
2. Technical dependencies
3. Business value alignment
4. Sprint capacity fit

For each epic:
- Title and description
- Contained stories (IDs)
- Total story points
- Priority (P0-P3)
- Risk assessment
- Definition of Done""",

    "quality_scoring": """Score the quality of this extraction:

Extraction Results:
{results}

Score on these dimensions (0-100):
1. **Completeness**: Are all code areas covered?
2. **Accuracy**: Are analyses factually correct?
3. **Consistency**: Do analyses agree with each other?
4. **Actionability**: Can devs act on these findings?
5. **Clarity**: Is the output easy to understand?

Overall confidence score: weighted average
Improvement suggestions: what's missing/unclear""",

    "traceability_matrix": """Create a traceability matrix:

Epics:
{epics}

Stories:
{stories}

Code Modules:
{modules}

Matrix format:
| Epic ID | Story ID | Module(s) | Files | Lines | Status |
|---------|----------|-----------|-------|-------|--------|

Include:
- Forward traceability (requirement -> code)
- Backward traceability (code -> requirement)
- Gap analysis (untraceable code)"""
}
