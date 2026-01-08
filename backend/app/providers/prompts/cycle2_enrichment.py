"""
Cycle 2: Cross-Enrichment Prompts

Target LLMs: Gemini (1M context) or Groq (fast)
Focus: Cross-file analysis and relationship mapping
"""

CYCLE2_PROMPTS = {
    "system": """You are a cross-analysis agent specializing in understanding
relationships between code components. Your context window is large - use it
to identify patterns across multiple files.

Focus on:
- Call graphs between modules
- Data flow between components
- Shared state and side effects
- Integration boundaries""",

    "cross_reference": """Analyze the relationships between these modules:

{module_summaries}

Identify:
1. **Call Dependencies**: Which modules call which
2. **Data Flow**: How data moves between components
3. **Shared State**: Globals, singletons, caches
4. **Event Chains**: Sequences of function calls
5. **Coupling Score**: 1-10 (10 = tightly coupled)

Return structured analysis with specific file:line references.""",

    "integration_points": """Based on these module analyses:

{analyses}

Map all integration points:
1. **API Endpoints**: REST/GraphQL/gRPC routes
2. **Database Access**: Which modules access which tables
3. **External Services**: Third-party API calls
4. **Message Queues**: Async communication
5. **File I/O**: Disk access patterns

For each integration point, note:
- Source location (file:line)
- Direction (inbound/outbound)
- Data format (JSON, XML, etc.)
- Error handling present (yes/no)""",

    "dependency_enrichment": """Enrich this dependency analysis with cross-cutting concerns:

Base Analysis:
{base_analysis}

Additional Context:
{additional_files}

Add:
1. Transitive dependencies (A->B->C)
2. Circular dependency warnings
3. Orphan modules (no callers)
4. Hub modules (many callers)
5. Suggested module boundaries for microservices"""
}
