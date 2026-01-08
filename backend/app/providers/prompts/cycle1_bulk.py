"""
Cycle 1: Bulk Code Analysis Prompts

Target LLMs: Ollama (free) or Qwen (cheap)
Focus: Fast, parallel extraction of code structures
"""

CYCLE1_PROMPTS = {
    "system": """You are a code analysis agent. Your task is to extract structural
information from source code files. Be thorough but efficient.

Output format: JSON with the following structure:
{
  "file_path": "path/to/file",
  "language": "detected_language",
  "classes": [...],
  "functions": [...],
  "imports": [...],
  "dependencies": [...],
  "patterns": [...],
  "complexity_score": 1-10
}""",

    "file_analysis": """Analyze the following source code file and extract:

1. **Classes**: Name, methods, inheritance, purpose
2. **Functions**: Name, parameters, return type, purpose
3. **Imports/Dependencies**: External packages used
4. **Design Patterns**: Any detected patterns (Factory, Singleton, etc.)
5. **Complexity**: Cyclomatic complexity estimate

```{language}
{code}
```

Return a structured JSON analysis.""",

    "module_overview": """Provide a high-level overview of this module:

File: {file_path}
Language: {language}

Extract:
- Primary purpose (1 sentence)
- Key exports
- External dependencies
- Integration points
- Estimated effort to understand (hours)

Code:
```{language}
{code}
```""",

    "batch_summary": """You have analyzed {file_count} files. Synthesize:

Files analyzed:
{file_list}

Individual analyses:
{analyses}

Provide:
1. Module dependency graph (as adjacency list)
2. Core business logic locations
3. Shared utility patterns
4. Technical debt indicators
5. Recommended analysis order for deeper review"""
}
