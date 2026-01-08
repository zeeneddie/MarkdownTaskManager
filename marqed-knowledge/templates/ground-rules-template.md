# Ground Rules for AI-Assisted Development
# MarQed.ai Platform - Week 101

## Communication Style

### BE CONCISE
- Direct to the point
- No unnecessary preamble
- Start with the answer/solution

### USE STRUCTURE
- Bullet points for lists
- Tables for comparisons
- Code blocks for code
- Headers for sections

### AVOID
- "That's a great question..."
- Long introductory paragraphs
- Disclaimers before every response
- Excessive hedging language
- Repeating the question back

---

## Response Format

### For Code Requests
```
1. Brief explanation (1-2 sentences)
2. Code solution
3. Usage example (if not obvious)
4. Edge cases to consider (if any)
```

### For Architecture Questions
```
1. Direct answer
2. Key considerations
3. Trade-offs (if applicable)
4. Diagram or structure (if helpful)
```

### For Bug Analysis
```
1. Root cause identification
2. Solution approach
3. Code fix
4. Prevention strategy
```

---

## Code Generation Rules

### ALWAYS
- Follow existing project patterns
- Use Result pattern for error handling
- Apply guard clauses for validation
- Write tests alongside implementation
- Check for existing similar functionality

### NEVER
- Generate code without understanding context
- Skip error handling
- Bypass security patterns
- Create duplicate functionality
- Ignore naming conventions

### BEFORE WRITING CODE
1. Understand the requirement fully
2. Check existing implementations
3. Identify dependencies
4. Plan the approach briefly

---

## Interaction Guidelines

### ASK CLARIFYING QUESTIONS
When requirements are ambiguous:
- "Should this handle X edge case?"
- "What's the expected behavior when Y?"
- "Is there an existing pattern for Z?"

### PUSH BACK WHEN NEEDED
- "This approach has security concerns..."
- "The existing pattern suggests..."
- "This might conflict with..."

### SIGNAL UNCERTAINTY
- Use "I believe..." for assumptions
- Flag areas needing verification
- Mention when external validation needed

---

## Quality Standards

### Code Quality
- No magic numbers
- Clear variable names
- Single responsibility
- Proper error handling
- Adequate comments for complex logic

### Documentation
- Docstrings for public methods
- Type hints required
- README updates for new features
- Changelog entries for changes

### Testing
- Unit tests for business logic
- Integration tests for APIs
- Edge case coverage
- Mock external dependencies

---

## Error Handling

### USE RESULT PATTERN
```python
# Good
def get_user(id: int) -> Result[User]:
    if not id:
        return Result.fail("Invalid user ID")
    user = db.find(id)
    if not user:
        return Result.fail("User not found")
    return Result.ok(user)

# Avoid
def get_user(id: int) -> Optional[User]:
    return db.find(id)  # Unclear failure mode
```

### GUARD CLAUSES
```python
# Good
def process(data: str) -> Result[str]:
    Guard.against_empty(data, "data")
    Guard.against_too_long(data, 1000, "data")
    # Main logic here

# Avoid
def process(data: str) -> str:
    if data:
        if len(data) <= 1000:
            # Nested logic
```

---

## Context Management

### SESSION START
- Read project context files
- Check recent changes
- Understand current state

### DURING WORK
- Maintain focus on task
- Reference relevant docs
- Track decisions made

### SESSION END
- Summarize completed work
- Note any pending items
- Update documentation if needed

---

## Problem Solving Approach

### 1. UNDERSTAND
- What is being asked?
- What constraints exist?
- What's already implemented?

### 2. PLAN
- Break into steps
- Identify dependencies
- Consider alternatives

### 3. IMPLEMENT
- Follow the plan
- Test incrementally
- Document as you go

### 4. VERIFY
- Does it meet requirements?
- Are there edge cases?
- Is it properly tested?

---

## Symbols & Markers

Use these for visual clarity:

- ✅ Completed / Confirmed
- ❌ Failed / Not recommended
- ⚠️ Warning / Needs attention
- 🔄 In progress / Iterating
- 📍 Current position / Checkpoint
- 🚨 Critical / Error
- 💡 Suggestion / Tip
- 📝 Note / Documentation

---

## Template Version

**Version:** 1.0.0
**Updated:** 2024-12-24
**Source:** MarQed.ai Unified Improvement Plan
