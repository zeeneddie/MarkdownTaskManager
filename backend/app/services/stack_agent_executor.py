"""
Stack Agent Executor

Week 56 Day 2: Executes stack-specific agent tasks using the Provider Registry.
Integrates Stack Agent Factory with LLM providers for actual code generation,
review, and analysis tasks.
"""

import json
import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel

from app.providers.registry import get_registry, TaskType
from app.services.stack_agent_factory import (
    get_stack_agent_factory,
    StackAgentInstance,
    AgentRole,
    TechStack,
)


# ============================================================================
# TASK TYPES
# ============================================================================

class AgentTaskType(str, Enum):
    """Types of tasks that stack agents can execute."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    REFACTORING = "refactoring"
    TEST_GENERATION = "test_generation"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    ARCHITECTURE_REVIEW = "architecture_review"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DEPENDENCY_UPDATE = "dependency_update"


# Map agent task types to provider registry task types
TASK_TYPE_MAPPING: Dict[AgentTaskType, TaskType] = {
    AgentTaskType.CODE_GENERATION: "simple_generation",
    AgentTaskType.CODE_REVIEW: "code_review",
    AgentTaskType.SECURITY_AUDIT: "security_audit",
    AgentTaskType.REFACTORING: "refactoring",
    AgentTaskType.TEST_GENERATION: "simple_generation",
    AgentTaskType.BUG_FIX: "debugging",
    AgentTaskType.DOCUMENTATION: "documentation",
    AgentTaskType.ARCHITECTURE_REVIEW: "architecture",
    AgentTaskType.PERFORMANCE_ANALYSIS: "complex_analysis",
    AgentTaskType.DEPENDENCY_UPDATE: "standard_work",
}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

@dataclass
class AgentTaskRequest:
    """Request to execute an agent task."""
    project_id: int
    agent_name: str
    task_type: AgentTaskType
    context: Dict[str, Any] = field(default_factory=dict)
    code_files: Dict[str, str] = field(default_factory=dict)
    instructions: str = ""
    max_tokens: int = 4000
    temperature: float = 0.3
    prefer_local: bool = False


@dataclass
class AgentTaskResult:
    """Result from an agent task execution."""
    success: bool
    agent_name: str
    task_type: AgentTaskType
    output: str
    code_changes: Dict[str, str] = field(default_factory=dict)
    analysis: Dict[str, Any] = field(default_factory=dict)
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    provider_used: str = ""
    tokens_used: int = 0
    error: Optional[str] = None


@dataclass
class ValidationResult:
    """Result from validation pipeline."""
    passed: bool
    phase: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

PYTHON_PROMPTS = {
    AgentTaskType.CODE_GENERATION: """You are an expert Python developer specializing in {specialties}.

Generate high-quality Python code based on these requirements:

{instructions}

{context_section}

Requirements:
1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public APIs
4. Handle errors appropriately
5. Write testable, modular code

Respond with the generated code:
```python
# Your code here
```
""",

    AgentTaskType.CODE_REVIEW: """You are a senior Python code reviewer specializing in {specialties}.

Review the following Python code for quality, security, and best practices:

```python
{code}
```

{instructions}

Provide a structured review with:
1. **Issues Found**: List any bugs, security issues, or anti-patterns
2. **Suggestions**: Recommendations for improvement
3. **Good Practices**: What the code does well
4. **Severity Rating**: CRITICAL / HIGH / MEDIUM / LOW / INFO

Format your response as:
## Review Summary
[Overall assessment]

## Issues
- [Issue 1]: Description (Severity: X)
- [Issue 2]: Description (Severity: X)

## Suggestions
- [Suggestion 1]
- [Suggestion 2]

## Score: X/10
""",

    AgentTaskType.SECURITY_AUDIT: """You are a Python security expert specializing in {specialties}.

Perform a security audit on the following Python code:

```python
{code}
```

Check for:
1. **OWASP Top 10 vulnerabilities**
2. **Input validation issues**
3. **Authentication/Authorization flaws**
4. **Injection vulnerabilities (SQL, Command, etc.)**
5. **Sensitive data exposure**
6. **Insecure dependencies**

Format your response as:
## Security Audit Report

### Critical Issues
[List critical vulnerabilities]

### High-Risk Issues
[List high-risk issues]

### Medium-Risk Issues
[List medium-risk issues]

### Recommendations
[Security recommendations]

### Security Score: X/10
""",

    AgentTaskType.TEST_GENERATION: """You are a Python testing expert specializing in {specialties}.

Generate comprehensive tests for the following Python code:

```python
{code}
```

{instructions}

Requirements:
1. Use pytest as the testing framework
2. Include unit tests for all public functions
3. Add edge case testing
4. Include mock objects where appropriate
5. Aim for >80% code coverage

Generate the test file:
```python
# test_[module].py
import pytest
# Your tests here
```
""",

    AgentTaskType.REFACTORING: """You are a Python refactoring expert specializing in {specialties}.

Refactor the following Python code for better quality:

```python
{code}
```

{instructions}

Focus on:
1. Code readability and maintainability
2. SOLID principles
3. Reducing complexity
4. Improving performance where applicable
5. Better error handling

Provide:
## Refactored Code
```python
# Refactored code
```

## Changes Made
- [Change 1]: Why it improves the code
- [Change 2]: Why it improves the code
""",

    AgentTaskType.BUG_FIX: """You are a Python debugging expert specializing in {specialties}.

Analyze and fix the bug in the following Python code:

```python
{code}
```

Bug description:
{instructions}

Provide:
## Root Cause Analysis
[Explain why the bug occurs]

## Fixed Code
```python
# Fixed code
```

## Test Case
```python
# Test to verify the fix
```

## Prevention
[How to prevent similar bugs]
""",
}

JAVASCRIPT_PROMPTS = {
    AgentTaskType.CODE_GENERATION: """You are an expert JavaScript/TypeScript developer specializing in {specialties}.

Generate high-quality code based on these requirements:

{instructions}

{context_section}

Requirements:
1. Use modern ES6+ syntax
2. Add TypeScript types where applicable
3. Include JSDoc comments
4. Handle errors appropriately
5. Write modular, testable code

Respond with the generated code:
```typescript
// Your code here
```
""",

    AgentTaskType.CODE_REVIEW: """You are a senior JavaScript/TypeScript code reviewer specializing in {specialties}.

Review the following code for quality, security, and best practices:

```javascript
{code}
```

{instructions}

Provide a structured review covering:
1. **Issues Found**: Bugs, security issues, anti-patterns
2. **Suggestions**: Recommendations for improvement
3. **Good Practices**: What the code does well
4. **Severity Rating**: CRITICAL / HIGH / MEDIUM / LOW / INFO

## Review Summary
[Overall assessment]

## Issues
- [Issue 1]: Description (Severity: X)

## Score: X/10
""",

    AgentTaskType.SECURITY_AUDIT: """You are a JavaScript/TypeScript security expert specializing in {specialties}.

Perform a security audit on the following code:

```javascript
{code}
```

Check for:
1. **OWASP Top 10 vulnerabilities**
2. **XSS (Cross-Site Scripting)**
3. **Injection vulnerabilities**
4. **Insecure dependencies (npm audit)**
5. **Sensitive data exposure**
6. **Prototype pollution**
7. **Insecure deserialization**

Format your response as:
## Security Audit Report

### Critical Issues
[List critical vulnerabilities]

### High-Risk Issues
[List high-risk issues]

### Medium-Risk Issues
[List medium-risk issues]

### Recommendations
[Security recommendations]

### Security Score: X/10
""",

    AgentTaskType.TEST_GENERATION: """You are a JavaScript testing expert specializing in {specialties}.

Generate comprehensive tests for the following code:

```javascript
{code}
```

{instructions}

Requirements:
1. Use Jest as the testing framework
2. Include unit tests for all public functions
3. Add edge case testing
4. Include mocks where appropriate
5. Aim for >80% code coverage

Generate the test file:
```javascript
// __tests__/[module].test.js
import {{ describe, test, expect }} from 'jest';
// Your tests here
```
""",

    AgentTaskType.REFACTORING: """You are a JavaScript/TypeScript refactoring expert specializing in {specialties}.

Refactor the following code for better quality:

```javascript
{code}
```

{instructions}

Focus on:
1. Code readability and maintainability
2. Modern ES6+ patterns
3. TypeScript best practices
4. Reducing complexity (cyclomatic, cognitive)
5. Better error handling with try/catch/finally

Provide:
## Refactored Code
```typescript
// Refactored code
```

## Changes Made
- [Change 1]: Why it improves the code
- [Change 2]: Why it improves the code
""",

    AgentTaskType.BUG_FIX: """You are a JavaScript/TypeScript debugging expert specializing in {specialties}.

Analyze and fix the bug in the following code:

```javascript
{code}
```

Bug description:
{instructions}

Provide:
## Root Cause Analysis
[Explain why the bug occurs, including event loop issues, async problems, type mismatches, etc.]

## Fixed Code
```typescript
// Fixed code
```

## Test Case
```javascript
// Jest test to verify the fix
describe('Bug fix verification', () => {{
  test('should fix the reported bug', () => {{
    // Test here
  }});
}});
```

## Prevention
[How to prevent similar bugs using TypeScript, linting rules, etc.]
""",

    AgentTaskType.DOCUMENTATION: """You are a JavaScript/TypeScript documentation expert specializing in {specialties}.

Generate comprehensive documentation for the following code:

```javascript
{code}
```

{instructions}

Include:
1. **Module Overview**: Purpose and usage
2. **API Reference**: Functions, classes, interfaces
3. **Examples**: Code examples with expected output
4. **Type Definitions**: TypeScript interfaces/types
5. **Error Handling**: Possible errors and how to handle them

Format with JSDoc/TSDoc:
```typescript
/**
 * Module documentation here
 * @module ModuleName
 */
```

And a README section:
## ModuleName

### Installation
```bash
npm install module-name
```

### Usage
```typescript
import {{ func }} from 'module-name';
```
""",

    AgentTaskType.ARCHITECTURE_REVIEW: """You are a JavaScript/TypeScript architecture expert specializing in {specialties}.

Review the architecture of the following code:

```javascript
{code}
```

{instructions}

Analyze:
1. **Component Structure**: Separation of concerns
2. **Dependency Management**: Imports, circular dependencies
3. **State Management**: How state is handled
4. **API Design**: Interface consistency
5. **Scalability**: Performance at scale
6. **Testability**: How easy to test

## Architecture Review

### Current Architecture
[Describe the current structure]

### Strengths
- [Strength 1]
- [Strength 2]

### Concerns
- [Concern 1] (Impact: HIGH/MEDIUM/LOW)
- [Concern 2] (Impact: HIGH/MEDIUM/LOW)

### Recommendations
1. [Recommendation with code example]
2. [Recommendation with code example]

### Architecture Score: X/10
""",

    AgentTaskType.PERFORMANCE_ANALYSIS: """You are a JavaScript/TypeScript performance expert specializing in {specialties}.

Analyze the performance of the following code:

```javascript
{code}
```

{instructions}

Check for:
1. **Memory Leaks**: Event listeners, closures, timers
2. **Inefficient Loops**: O(n²) operations, unnecessary iterations
3. **Blocking Operations**: Sync I/O, heavy computation
4. **Bundle Size**: Large dependencies, tree-shaking issues
5. **Render Performance**: DOM manipulation, reflows
6. **Async Issues**: Promise chains, async/await misuse

## Performance Analysis

### Hot Paths
[Identify performance-critical code paths]

### Issues Found
- [Issue 1]: Description (Impact: HIGH/MEDIUM/LOW)
- [Issue 2]: Description (Impact: HIGH/MEDIUM/LOW)

### Optimization Suggestions
```typescript
// Before
// [problematic code]

// After
// [optimized code]
```

### Performance Score: X/10
""",

    AgentTaskType.DEPENDENCY_UPDATE: """You are a JavaScript/TypeScript dependency management expert specializing in {specialties}.

Analyze and recommend dependency updates for the following package.json:

```json
{code}
```

{instructions}

Check for:
1. **Outdated packages**: Major/minor/patch updates available
2. **Security vulnerabilities**: npm audit issues
3. **Deprecated packages**: Alternatives needed
4. **Bundle size impact**: Lighter alternatives
5. **TypeScript compatibility**: @types packages

## Dependency Analysis

### Updates Available
| Package | Current | Latest | Type | Breaking Changes |
|---------|---------|--------|------|------------------|
| package1 | 1.0.0 | 2.0.0 | Major | Yes - [details] |

### Security Vulnerabilities
[List from npm audit]

### Recommendations
1. [Priority update with migration steps]
2. [Optional update]

### Updated package.json
```json
{{
  "dependencies": {{
    // Updated versions
  }}
}}
```
""",
}


# Go language prompts
GO_PROMPTS = {
    AgentTaskType.CODE_GENERATION: """You are an expert Go developer specializing in {specialties}.

Generate high-quality Go code based on these requirements:

{instructions}

{context_section}

Requirements:
1. Follow Go idioms and conventions
2. Use proper error handling (return errors, don't panic)
3. Add godoc comments for exported functions
4. Keep functions small and focused
5. Use interfaces for abstraction

Respond with the generated code:
```go
// Your code here
package main
```
""",

    AgentTaskType.CODE_REVIEW: """You are a senior Go code reviewer specializing in {specialties}.

Review the following Go code for quality and best practices:

```go
{code}
```

{instructions}

Check for:
1. **Error Handling**: Proper error propagation
2. **Concurrency**: Goroutine leaks, race conditions
3. **Memory**: Unnecessary allocations, slice capacity
4. **Idioms**: Go best practices
5. **Testing**: Test coverage and quality

## Review Summary
[Overall assessment]

## Issues
- [Issue 1]: Description (Severity: X)

## Score: X/10
""",

    AgentTaskType.TEST_GENERATION: """You are a Go testing expert specializing in {specialties}.

Generate comprehensive tests for the following Go code:

```go
{code}
```

{instructions}

Requirements:
1. Use the testing package
2. Include table-driven tests
3. Add benchmark tests where appropriate
4. Include error case testing
5. Use testify/assert for cleaner assertions

Generate the test file:
```go
package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestFunction(t *testing.T) {{
    // Your tests here
}}
```
""",
}

# Rust language prompts
RUST_PROMPTS = {
    AgentTaskType.CODE_GENERATION: """You are an expert Rust developer specializing in {specialties}.

Generate high-quality Rust code based on these requirements:

{instructions}

{context_section}

Requirements:
1. Follow Rust idioms and ownership patterns
2. Use Result<T, E> for error handling
3. Add documentation comments (///)
4. Prefer references over ownership where appropriate
5. Use iterators and functional patterns

Respond with the generated code:
```rust
// Your code here
```
""",

    AgentTaskType.CODE_REVIEW: """You are a senior Rust code reviewer specializing in {specialties}.

Review the following Rust code for quality and safety:

```rust
{code}
```

{instructions}

Check for:
1. **Safety**: Unsafe blocks, memory safety
2. **Ownership**: Unnecessary clones, borrows
3. **Error Handling**: Proper Result usage
4. **Performance**: Unnecessary allocations
5. **Idioms**: Rust best practices

## Review Summary
[Overall assessment]

## Issues
- [Issue 1]: Description (Severity: X)

## Score: X/10
""",

    AgentTaskType.TEST_GENERATION: """You are a Rust testing expert specializing in {specialties}.

Generate comprehensive tests for the following Rust code:

```rust
{code}
```

{instructions}

Requirements:
1. Use #[test] attribute
2. Include unit tests in the same file
3. Add integration tests where appropriate
4. Test error cases with Result types
5. Use assert_eq!, assert!, assert_ne!

Generate the test module:
```rust
#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn test_function() {{
        // Your tests here
    }}
}}
```
""",
}


# ============================================================================
# STACK AGENT EXECUTOR
# ============================================================================

class StackAgentExecutor:
    """
    Executes stack-specific agent tasks using the Provider Registry.

    Integrates:
    - Stack Agent Factory (agent templates and instances)
    - Provider Registry (LLM routing)
    - Validation Pipeline (quality gates)

    Example:
        executor = StackAgentExecutor()

        result = await executor.execute_task(AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_py",
            task_type=AgentTaskType.CODE_REVIEW,
            code_files={"main.py": "def foo(): ..."},
            instructions="Review for security issues"
        ))
    """

    def __init__(self):
        self.factory = get_stack_agent_factory()
        self.registry = get_registry()
        self._execution_history: List[AgentTaskResult] = []

    async def execute_task(self, request: AgentTaskRequest) -> AgentTaskResult:
        """
        Execute an agent task.

        Args:
            request: Task request with agent, type, and context

        Returns:
            AgentTaskResult with output and validation status
        """
        start_time = datetime.now()

        # Get the agent instance
        agent = self.factory.get_agent_by_name(
            request.project_id,
            request.agent_name
        )

        if not agent:
            return AgentTaskResult(
                success=False,
                agent_name=request.agent_name,
                task_type=request.task_type,
                output="",
                error=f"Agent '{request.agent_name}' not found for project {request.project_id}"
            )

        if not agent.active:
            return AgentTaskResult(
                success=False,
                agent_name=request.agent_name,
                task_type=request.task_type,
                output="",
                error=f"Agent '{request.agent_name}' is inactive"
            )

        try:
            # Build the prompt
            prompt = self._build_prompt(agent, request)

            # Get the appropriate provider
            provider_task_type = TASK_TYPE_MAPPING.get(
                request.task_type,
                "standard_work"
            )
            provider = self.registry.route_task(
                provider_task_type,
                prefer_local=request.prefer_local
            )

            # Execute the LLM call
            response = await self._call_provider(
                provider,
                prompt,
                request.max_tokens,
                request.temperature
            )

            # Parse the response
            output, code_changes, analysis = self._parse_response(
                response,
                request.task_type
            )

            # Run validation if code was generated
            validation_passed = True
            validation_errors = []

            if code_changes:
                validation_result = await self._validate_output(
                    agent,
                    request.task_type,
                    code_changes
                )
                validation_passed = validation_result.passed
                validation_errors = validation_result.errors

            # Calculate execution time
            execution_time_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )

            # Update agent performance
            success = bool(output) and (not code_changes or validation_passed)
            performance_delta = 0.1 if success else -0.05

            self.factory.update_agent_performance(
                request.project_id,
                request.agent_name,
                success=success,
                performance_delta=performance_delta
            )

            result = AgentTaskResult(
                success=success,
                agent_name=request.agent_name,
                task_type=request.task_type,
                output=output,
                code_changes=code_changes,
                analysis=analysis,
                validation_passed=validation_passed,
                validation_errors=validation_errors,
                execution_time_ms=execution_time_ms,
                provider_used=provider.config.name if provider else "unknown",
                tokens_used=len(output) // 4  # Rough estimate
            )

            self._execution_history.append(result)
            return result

        except Exception as e:
            return AgentTaskResult(
                success=False,
                agent_name=request.agent_name,
                task_type=request.task_type,
                output="",
                error=str(e)
            )

    def _build_prompt(
        self,
        agent: StackAgentInstance,
        request: AgentTaskRequest
    ) -> str:
        """Build the LLM prompt based on stack and task type."""
        template = agent.template

        # Select prompt templates based on stack
        if template.stack == TechStack.PYTHON:
            prompts = PYTHON_PROMPTS
        elif template.stack in (TechStack.JAVASCRIPT, TechStack.TYPESCRIPT):
            prompts = JAVASCRIPT_PROMPTS
        elif template.stack == TechStack.GO:
            prompts = GO_PROMPTS
        elif template.stack == TechStack.RUST:
            prompts = RUST_PROMPTS
        else:
            # Default to Python-style prompts for other stacks
            prompts = PYTHON_PROMPTS

        # Get the task-specific prompt template
        prompt_template = prompts.get(request.task_type)
        if not prompt_template:
            # Fallback generic prompt
            prompt_template = """You are a {specialties} expert.

{instructions}

{context_section}

Provide a detailed response.
"""

        # Build specialties string
        specialties = ", ".join([c.name for c in template.capabilities])

        # Build context section
        context_section = ""
        if request.context:
            context_section = "Context:\n" + json.dumps(request.context, indent=2)

        # Get code if provided
        code = ""
        if request.code_files:
            code_parts = []
            for filename, content in request.code_files.items():
                code_parts.append(f"# {filename}\n{content}")
            code = "\n\n".join(code_parts)

        # Format the prompt
        prompt = prompt_template.format(
            specialties=specialties,
            instructions=request.instructions,
            context_section=context_section,
            code=code
        )

        # Add stack-specific system context
        system_context = f"""
You are acting as a {template.role.value} agent specialized in {template.stack.value}.
Your capabilities include: {specialties}
Tools you use: {', '.join(template.specialized_tools)}
"""
        return system_context + "\n\n" + prompt

    async def _call_provider(
        self,
        provider,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Call the LLM provider."""
        if not provider:
            return "Error: No provider available"

        try:
            # Use the provider's generate method
            response = await provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response

        except Exception as e:
            return f"Error calling provider: {str(e)}"

    def _parse_response(
        self,
        response: str,
        task_type: AgentTaskType
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Parse the LLM response into structured output.

        Returns:
            (output_text, code_changes, analysis)
        """
        output = response
        code_changes: Dict[str, str] = {}
        analysis: Dict[str, Any] = {}

        # Extract code blocks
        code_pattern = r"```(?:python|javascript|typescript|js|ts)?\n(.*?)```"
        matches = re.findall(code_pattern, response, re.DOTALL)

        if matches:
            for i, match in enumerate(matches):
                # Try to determine filename from context
                filename = f"generated_{i}.py" if task_type in [
                    AgentTaskType.CODE_GENERATION,
                    AgentTaskType.REFACTORING,
                    AgentTaskType.BUG_FIX
                ] else f"test_{i}.py"
                code_changes[filename] = match.strip()

        # Extract analysis data based on task type
        if task_type == AgentTaskType.CODE_REVIEW:
            # Parse review score
            score_match = re.search(r"Score:\s*(\d+)/10", response)
            if score_match:
                analysis["score"] = int(score_match.group(1))

            # Parse severity counts
            analysis["critical"] = len(re.findall(r"Severity:\s*CRITICAL", response))
            analysis["high"] = len(re.findall(r"Severity:\s*HIGH", response))
            analysis["medium"] = len(re.findall(r"Severity:\s*MEDIUM", response))
            analysis["low"] = len(re.findall(r"Severity:\s*LOW", response))

        elif task_type == AgentTaskType.SECURITY_AUDIT:
            # Parse security score
            score_match = re.search(r"Security Score:\s*(\d+)/10", response)
            if score_match:
                analysis["security_score"] = int(score_match.group(1))

            # Count issues
            analysis["critical_issues"] = response.count("Critical")
            analysis["high_risk_issues"] = response.count("High-Risk")

        return output, code_changes, analysis

    async def _validate_output(
        self,
        agent: StackAgentInstance,
        task_type: AgentTaskType,
        code_changes: Dict[str, str]
    ) -> ValidationResult:
        """
        Run validation pipeline on generated code.

        Uses the agent's configured validation phases.
        """
        template = agent.template
        phases = template.validation_phases

        # For now, do basic validation
        # Full validation would integrate with ruff, mypy, pytest, etc.

        errors = []
        warnings = []

        for phase in phases:
            if phase == "linting":
                # Check for common issues
                for filename, code in code_changes.items():
                    if "import *" in code:
                        errors.append(f"{filename}: Avoid wildcard imports")
                    if "eval(" in code:
                        errors.append(f"{filename}: Avoid eval() for security")
                    if "exec(" in code:
                        warnings.append(f"{filename}: Be cautious with exec()")

            elif phase == "type_check":
                # Basic type hint check
                for filename, code in code_changes.items():
                    if "def " in code and " -> " not in code:
                        warnings.append(f"{filename}: Consider adding return type hints")

            elif phase == "style":
                # Basic style check
                for filename, code in code_changes.items():
                    lines = code.split("\n")
                    for i, line in enumerate(lines, 1):
                        if len(line) > 120:
                            warnings.append(f"{filename}:{i}: Line too long (>120 chars)")

        return ValidationResult(
            passed=len(errors) == 0,
            phase="combined",
            errors=errors,
            warnings=warnings
        )

    async def execute_batch(
        self,
        requests: List[AgentTaskRequest]
    ) -> List[AgentTaskResult]:
        """Execute multiple agent tasks."""
        results = []
        for request in requests:
            result = await self.execute_task(request)
            results.append(result)
        return results

    def get_execution_history(
        self,
        project_id: Optional[int] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentTaskResult]:
        """Get execution history with optional filters."""
        history = self._execution_history

        if project_id is not None:
            # Note: We don't store project_id in result, so filter by agent name
            pass

        if agent_name:
            history = [h for h in history if h.agent_name == agent_name]

        return history[-limit:]

    def get_success_metrics(self) -> Dict[str, Any]:
        """Get aggregate success metrics."""
        if not self._execution_history:
            return {
                "total_tasks": 0,
                "successful_tasks": 0,
                "success_rate": 0.0,
                "validation_pass_rate": 0.0,
                "avg_execution_time_ms": 0,
            }

        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r.success)
        validated = sum(1 for r in self._execution_history if r.validation_passed)
        avg_time = sum(r.execution_time_ms for r in self._execution_history) / total

        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "validation_pass_rate": validated / total if total > 0 else 0.0,
            "avg_execution_time_ms": int(avg_time),
        }


# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_executor: Optional[StackAgentExecutor] = None


def get_stack_agent_executor() -> StackAgentExecutor:
    """Get the global stack agent executor instance."""
    global _executor
    if _executor is None:
        _executor = StackAgentExecutor()
    return _executor
