"""
Cycle 3: Conflict Detection Prompts

Target LLMs: OpenAI GPT-4o (coding specialist)
Focus: Identifying inconsistencies, conflicts, and code issues
"""

CYCLE3_PROMPTS = {
    "system": """You are a code conflict detection specialist. Your role is to
identify inconsistencies, conflicts, and potential issues in code analyses.

Look for:
- Contradictory analyses from different LLMs
- Inconsistent naming conventions
- Conflicting design patterns
- Potential bugs and race conditions
- Security vulnerabilities""",

    "conflict_detection": """Compare these analyses from different LLMs:

Analysis 1 ({llm1}):
{analysis1}

Analysis 2 ({llm2}):
{analysis2}

Identify:
1. **Factual Conflicts**: Different conclusions about the same code
2. **Missing Coverage**: What one found that the other missed
3. **Confidence Divergence**: Where certainty differs significantly
4. **Resolution**: Which analysis is more accurate (with evidence)

For each conflict, provide:
- Location (file:line)
- Nature of conflict
- Evidence for resolution
- Impact severity (low/medium/high)""",

    "code_issue_detection": """Analyze this code for potential issues:

```{language}
{code}
```

Context from previous analyses:
{context}

Check for:
1. **Race Conditions**: Concurrent access issues
2. **Resource Leaks**: Unclosed handles/connections
3. **Null/Undefined**: Missing null checks
4. **Type Mismatches**: Implicit conversions
5. **Security**: SQL injection, XSS, etc.
6. **Performance**: N+1 queries, inefficient algorithms

Severity rating for each issue: critical/high/medium/low""",

    "inconsistency_resolution": """Resolve these detected inconsistencies:

Inconsistencies:
{inconsistencies}

Original Code Snippets:
{code_snippets}

For each inconsistency:
1. Identify the ground truth
2. Explain why the conflict arose
3. Provide the correct interpretation
4. Suggest code improvements if applicable"""
}
