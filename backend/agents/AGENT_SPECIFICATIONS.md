# Agent Specifications - Detailed Role Descriptions

**Project:** Markdown Task Manager - Agentic System
**Version:** 1.0
**Date:** 2025-11-13
**Status:** Week 5 Day 2 - Agent Definitions

---

## Table of Contents

1. [Agent 1: Felix (Feature Architect)](#agent-1-felix-feature-architect)
2. [Agent 2: Marcus (Maintenance Specialist)](#agent-2-marcus-maintenance-specialist)
3. [Agent 3: Quinn (Quality Inspector)](#agent-3-quinn-quality-inspector)
4. [Agent 4: Betty (Bug Hunter)](#agent-4-betty-bug-hunter)
5. [Agent 5: Eliza (Estimation Engine)](#agent-5-eliza-estimation-engine)
6. [Agent 6: Tessa (Test Engineer)](#agent-6-tessa-test-engineer)
7. [Agent 7: Miguel (Migration Architect)](#agent-7-miguel-migration-architect)
8. [Agent 8: Diana (Documentation Writer)](#agent-8-diana-documentation-writer)

---

## Agent 1: Felix (Feature Architect)

### Profile
- **Name:** Felix
- **Role:** Feature Architect
- **LLM:** Claude Sonnet 4.5 (Cloud)
- **Persona:** Senior Software Architect with 15 years experience

### Detailed Role Description

Felix specializes in analyzing new feature requests and transforming them into well-structured, implementable work breakdowns. He excels at:
- Understanding complex business requirements
- Identifying technical dependencies and constraints
- Designing scalable and maintainable solutions
- Breaking down large features into Epic → Feature → Story → Task hierarchy

### Responsibilities

1. **Requirements Analysis**
   - Parse user stories and feature requests
   - Identify functional and non-functional requirements
   - Extract acceptance criteria
   - Clarify ambiguities

2. **Architecture Design**
   - Design system architecture for new features
   - Identify integration points with existing systems
   - Plan data models and API contracts
   - Consider scalability and performance

3. **Work Breakdown**
   - Create Epic-level breakdown
   - Define Features under each Epic
   - Break Features into User Stories
   - Decompose Stories into Technical Tasks

4. **Dependency Mapping**
   - Identify technical dependencies
   - Map external service dependencies
   - Define prerequisite tasks
   - Create execution order recommendations

### Tools & Capabilities

```typescript
const felixTools = [
  {
    name: "spec_kit_constitution",
    description: "Analyze requirements and constraints using Spec-Kit /constitution command",
    input: "Feature description, business goals, constraints",
    output: "Constitutional analysis with principles and boundaries"
  },
  {
    name: "spec_kit_specify",
    description: "Create detailed specification using Spec-Kit /specify command",
    input: "Constitutional analysis",
    output: "Detailed technical specification"
  },
  {
    name: "architecture_designer",
    description: "Design system architecture diagrams",
    input: "Feature specification",
    output: "Architecture diagram (C4 model), component design"
  },
  {
    name: "work_breakdown_generator",
    description: "Generate hierarchical task breakdown",
    input: "Technical specification",
    output: "Epic → Feature → Story → Task structure in JSON"
  },
  {
    name: "dependency_analyzer",
    description: "Identify and map dependencies",
    input: "Task breakdown",
    output: "Dependency graph with execution order"
  }
];
```

### Triggers

Felix is activated when:
- **Work Type:** `NEW_FEATURE` or `ENHANCEMENT`
- **User Input:** Feature request, user story, business requirement
- **Workflow:** Spec-Kit pipeline (`/constitution` → `/specify` → `/tasks`)

### Input Format

```json
{
  "type": "NEW_FEATURE",
  "title": "Add OAuth2 Authentication",
  "description": "Users should be able to login with Google, GitHub, and Microsoft accounts",
  "business_goals": [
    "Reduce friction in signup process",
    "Increase user acquisition by 30%"
  ],
  "constraints": [
    "Must comply with GDPR",
    "Should work on mobile and desktop",
    "Max 2-week implementation time"
  ],
  "acceptance_criteria": [
    "Users can login with Google",
    "Users can login with GitHub",
    "User data is stored securely",
    "Login takes less than 5 seconds"
  ]
}
```

### Output Format

```json
{
  "epic": {
    "id": "EPIC-001",
    "title": "OAuth2 Authentication System",
    "description": "Implement social login with Google, GitHub, Microsoft",
    "business_value": "Reduce signup friction, increase conversions",
    "function_points": 21,
    "t_shirt_size": "L",
    "estimated_sprints": 2
  },
  "features": [
    {
      "id": "FEAT-001",
      "title": "OAuth2 Provider Integration",
      "description": "Backend integration with OAuth2 providers",
      "function_points": 13,
      "stories": [
        {
          "id": "STORY-001",
          "title": "Setup Google OAuth2",
          "description": "Integrate Google OAuth2 SDK",
          "story_points": 5,
          "tasks": [
            {
              "id": "TASK-001",
              "title": "Install google-auth-library",
              "story_points": 1,
              "estimated_hours": 2
            },
            {
              "id": "TASK-002",
              "title": "Configure OAuth2 credentials",
              "story_points": 1,
              "estimated_hours": 1
            }
          ]
        }
      ]
    }
  ],
  "dependencies": [
    {
      "from": "TASK-002",
      "to": "TASK-003",
      "type": "prerequisite"
    }
  ]
}
```

### Collaboration

**Works with:**
- **Eliza (Estimation Engine)** - Receives work breakdown, returns story points
- **Tessa (Test Engineer)** - Provides feature spec, receives test strategy
- **Quinn (Quality Inspector)** - Reviews architecture for quality issues
- **Diana (Documentation Writer)** - Provides spec, receives documentation

### Example Workflow

```
User Request: "Add OAuth2 authentication"
    ↓
Felix: Analyze requirements (/constitution)
    ↓
Felix: Create specification (/specify)
    ↓
Felix: Generate work breakdown
    ↓
Eliza: Calculate story points for all tasks
    ↓
Tessa: Define test scenarios
    ↓
Quinn: Review architecture design
    ↓
Diana: Generate technical documentation
```

---

## Agent 2: Marcus (Maintenance Specialist)

### Profile
- **Name:** Marcus
- **Role:** Maintenance Specialist
- **LLM:** Llama 3.1 8B (Local - Ollama)
- **Persona:** Expert in code quality, refactoring, and technical debt

### Detailed Role Description

Marcus identifies technical debt, outdated dependencies, and refactoring opportunities. He implements the 6-stage Code-Maintenance-Agent workflow:

1. **Analysis** - Scan codebase for maintenance needs
2. **Prioritization** - Risk × Impact matrix
3. **Planning** - Create maintenance roadmap
4. **Execution** - Automated updates and refactoring
5. **Testing** - Regression validation
6. **Deployment** - Staged rollout

### Responsibilities

1. **Technical Debt Identification**
   - Scan for code smells (duplication, complexity)
   - Identify deprecated dependencies
   - Find security vulnerabilities
   - Measure technical debt ratio (TDR)

2. **Dependency Management**
   - Monitor for outdated packages
   - Identify breaking changes
   - Plan upgrade paths
   - Test compatibility

3. **Refactoring Planning**
   - Identify refactoring opportunities
   - Prioritize by ROI (value/effort)
   - Create safe refactoring plans
   - Ensure backward compatibility

4. **Preventive Maintenance**
   - Schedule periodic maintenance runs
   - Monitor system health metrics
   - Proactive issue detection
   - Performance optimization

### Tools & Capabilities

```typescript
const marcusTools = [
  {
    name: "code_smell_detector",
    description: "Detect code smells using static analysis",
    tools: ["SonarQube", "ESLint", "Pylint"],
    input: "Codebase path",
    output: "List of code smells with severity and location"
  },
  {
    name: "dependency_scanner",
    description: "Scan for outdated and vulnerable dependencies",
    tools: ["npm audit", "pip-audit", "Snyk"],
    input: "Package files (package.json, requirements.txt)",
    output: "Vulnerability report with recommendations"
  },
  {
    name: "complexity_analyzer",
    description: "Measure code complexity (cyclomatic, cognitive)",
    tools: ["radon", "complexity-report"],
    input: "Source files",
    output: "Complexity metrics per function/class"
  },
  {
    name: "refactoring_planner",
    description: "Generate safe refactoring plans",
    input: "Code smells, complexity metrics",
    output: "Refactoring recommendations with effort estimates"
  },
  {
    name: "maintenance_scheduler",
    description: "Schedule and execute periodic maintenance",
    input: "Maintenance tasks",
    output: "Scheduled maintenance plan"
  }
];
```

### Triggers

Marcus is activated when:
- **Work Type:** `MAINTENANCE` or `QUALITY_IMPROVEMENT`
- **Scheduled:** Weekly/monthly maintenance runs
- **Event-driven:** Dependency vulnerability alerts
- **Manual:** User requests codebase cleanup

### Input Format

```json
{
  "type": "MAINTENANCE",
  "scope": "full_codebase",
  "focus_areas": [
    "dependencies",
    "code_quality",
    "security"
  ],
  "thresholds": {
    "max_complexity": 15,
    "min_test_coverage": 80,
    "max_technical_debt_ratio": 10
  }
}
```

### Output Format

```json
{
  "maintenance_report": {
    "analysis_date": "2025-11-13",
    "technical_debt_ratio": 12.5,
    "findings": [
      {
        "category": "dependency",
        "severity": "high",
        "issue": "axios@0.21.1 has known XSS vulnerability",
        "recommendation": "Update to axios@1.6.2",
        "effort_sp": 1,
        "risk": "high"
      },
      {
        "category": "code_smell",
        "severity": "medium",
        "issue": "Function 'processData' has cyclomatic complexity 18",
        "recommendation": "Refactor into smaller functions",
        "effort_sp": 3,
        "risk": "medium"
      }
    ],
    "prioritized_tasks": [
      {
        "id": "MAINT-001",
        "title": "Update axios to fix XSS vulnerability",
        "priority": "P0",
        "effort_sp": 1,
        "timeline": "immediate"
      }
    ]
  }
}
```

### Collaboration

**Works with:**
- **Quinn (Quality Inspector)** - Receives quality metrics, reports improvements
- **Tessa (Test Engineer)** - Ensures regression tests exist
- **Eliza (Estimation Engine)** - Gets effort estimates for maintenance tasks

---

## Agent 3: Quinn (Quality Inspector)

### Profile
- **Name:** Quinn
- **Role:** Quality Inspector
- **LLM:** Claude Sonnet 4.5 (Cloud)
- **Persona:** QA Lead with expertise in code reviews and quality metrics

### Detailed Role Description

Quinn conducts comprehensive quality audits across 4 dimensions:
1. **Security Audit** (OWASP Top 10)
2. **Performance Audit** (Speed, memory, queries)
3. **Code Quality Audit** (Complexity, duplication, coverage)
4. **Architecture Audit** (Design patterns, scalability)

Uses SuperClaude Framework personas:
- `security_expert`
- `performance_expert`
- `code_reviewer`
- `architect`

### Responsibilities

1. **Security Review**
   - OWASP Top 10 vulnerability scanning
   - Authentication/authorization review
   - Data protection (GDPR compliance)
   - Dependency vulnerability scanning

2. **Performance Analysis**
   - Response time analysis (p50, p95, p99)
   - Database query optimization (N+1 detection)
   - Frontend performance (Lighthouse score)
   - Memory leak detection

3. **Code Quality Review**
   - Cyclomatic complexity (<15 per function)
   - Code duplication (<3%)
   - Test coverage (>80%)
   - Documentation completeness

4. **Architecture Review**
   - Design pattern compliance
   - Coupling/cohesion analysis
   - Scalability assessment
   - Technical debt measurement

### Tools & Capabilities

```typescript
const quinnTools = [
  {
    name: "security_scanner",
    description: "Scan for security vulnerabilities",
    tools: ["OWASP ZAP", "Snyk", "Bandit"],
    input: "Codebase, dependencies",
    output: "Security audit report with CVE details"
  },
  {
    name: "performance_profiler",
    description: "Profile application performance",
    tools: ["Lighthouse", "pytest-benchmark", "k6"],
    input: "Application endpoints, frontend pages",
    output: "Performance metrics with bottlenecks"
  },
  {
    name: "code_quality_analyzer",
    description: "Analyze code quality metrics",
    tools: ["SonarQube", "CodeClimate"],
    input: "Source code",
    output: "Quality report with TDR, duplication, complexity"
  },
  {
    name: "architecture_reviewer",
    description: "Review system architecture",
    input: "Architecture diagrams, code structure",
    output: "Architecture assessment with recommendations"
  },
  {
    name: "superclaude_personas",
    description: "Use SuperClaude expert personas",
    personas: ["security_expert", "performance_expert", "code_reviewer", "architect"],
    input: "Code, architecture",
    output: "Expert review from persona perspective"
  }
];
```

### Triggers

Quinn is activated when:
- **Work Type:** `QUALITY_AUDIT`
- **Pre-release:** Before major releases
- **Post-implementation:** After feature completion
- **Scheduled:** Monthly quality reviews

### Input Format

```json
{
  "type": "QUALITY_AUDIT",
  "scope": "full_application",
  "audit_dimensions": [
    "security",
    "performance",
    "code_quality",
    "architecture"
  ],
  "context": {
    "upcoming_release": "v2.0.0",
    "critical_features": ["authentication", "payment"]
  }
}
```

### Output Format

```json
{
  "audit_report": {
    "audit_date": "2025-11-13",
    "overall_score": 78,
    "dimensions": {
      "security": {
        "score": 85,
        "findings": {
          "critical": 0,
          "high": 1,
          "medium": 3,
          "low": 5
        },
        "details": [
          {
            "severity": "high",
            "category": "authentication",
            "issue": "Password policy allows weak passwords",
            "recommendation": "Enforce minimum 12 characters, special chars",
            "cve": null
          }
        ]
      },
      "performance": {
        "score": 72,
        "lighthouse_score": 89,
        "api_p95_response": "245ms",
        "bottlenecks": [
          {
            "location": "/api/users endpoint",
            "issue": "N+1 query on user.posts",
            "impact": "300ms average overhead",
            "fix": "Add select_related('posts')"
          }
        ]
      },
      "code_quality": {
        "score": 75,
        "test_coverage": 76,
        "technical_debt_ratio": 11.2,
        "duplication": 4.5,
        "complexity_violations": 12
      },
      "architecture": {
        "score": 80,
        "coupling": "acceptable",
        "scalability": "good",
        "recommendations": [
          "Consider introducing event sourcing for audit trail",
          "Decouple payment module from user module"
        ]
      }
    },
    "remediation_plan": [
      {
        "priority": "P0",
        "task": "Fix authentication password policy",
        "effort_sp": 2,
        "timeline": "this sprint"
      }
    ]
  }
}
```

### Collaboration

**Works with:**
- **Felix (Feature Architect)** - Reviews architecture designs
- **Marcus (Maintenance Specialist)** - Identifies quality improvements
- **Tessa (Test Engineer)** - Reviews test coverage

---

## Agent 4: Betty (Bug Hunter)

### Profile
- **Name:** Betty
- **Role:** Bug Hunter
- **LLM:** Llama 3.1 8B (Local - Ollama)
- **Persona:** Debugging specialist with pattern recognition expertise

### Detailed Role Description

Betty specializes in:
- Analyzing bug reports
- Reproducing issues
- Root cause analysis
- Suggesting fixes with regression tests

Implements 5-stage bug fixing workflow:
1. **Reproduction** - Create failing test
2. **Root Cause Analysis** - Find the bug
3. **Fix Implementation** - Resolve issue
4. **Validation** - Ensure fix works
5. **Deployment** - Get fix to production

### Responsibilities

1. **Bug Analysis**
   - Parse bug reports
   - Extract reproduction steps
   - Identify affected components
   - Classify severity (P0-P4)

2. **Root Cause Investigation**
   - Stack trace analysis
   - Git bisect for regression
   - Log analysis
   - Hypothesis testing

3. **Fix Development**
   - Implement minimal fix
   - Add regression test
   - Validate no side effects
   - Document fix rationale

4. **Prevention**
   - Identify bug patterns
   - Suggest preventive measures
   - Update coding standards
   - Add linter rules

### Tools & Capabilities

```typescript
const bettyTools = [
  {
    name: "bug_parser",
    description: "Parse and categorize bug reports",
    input: "Bug report text",
    output: "Structured bug data with severity, steps, expected/actual"
  },
  {
    name: "stack_trace_analyzer",
    description: "Analyze stack traces to find root cause",
    input: "Stack trace",
    output: "Root cause location with code context"
  },
  {
    name: "git_bisect_runner",
    description: "Find regression commit using git bisect",
    input: "Good commit, bad commit, test command",
    output: "First bad commit hash"
  },
  {
    name: "test_generator",
    description: "Generate failing test for bug reproduction",
    input: "Bug reproduction steps",
    output: "Test code (pytest/Jest)"
  },
  {
    name: "fix_validator",
    description: "Validate fix doesn't introduce regressions",
    input: "Fix code",
    output: "Validation report with test results"
  }
];
```

### Triggers

Betty is activated when:
- **Work Type:** `BUG`
- **Event:** Production error alert
- **Event:** Test failure in CI/CD
- **User:** Bug report submission

### Input Format

```json
{
  "type": "BUG",
  "severity": "P1",
  "title": "Login fails with 500 error after password reset",
  "description": "Users cannot login after resetting password",
  "reproduction_steps": [
    "Navigate to /forgot-password",
    "Enter email and submit",
    "Click reset link in email",
    "Enter new password",
    "Try to login with new password",
    "Observe 500 error"
  ],
  "expected_behavior": "User should login successfully",
  "actual_behavior": "500 Internal Server Error",
  "environment": {
    "browser": "Chrome 120",
    "os": "Windows 11",
    "app_version": "v1.2.3"
  },
  "stack_trace": "Traceback...",
  "logs": "ERROR: Invalid token..."
}
```

### Output Format

```json
{
  "bug_analysis": {
    "severity": "P1",
    "category": "authentication",
    "root_cause": "Password reset token not invalidated after use",
    "affected_code": "backend/app/auth/password_reset.py:142",
    "first_bad_commit": "a1b2c3d",
    "impact": "All users attempting password reset"
  },
  "fix": {
    "description": "Invalidate reset token after successful password change",
    "code_changes": [
      {
        "file": "backend/app/auth/password_reset.py",
        "line": 142,
        "old": "user.set_password(new_password)",
        "new": "user.set_password(new_password)\ntoken.invalidate()"
      }
    ],
    "regression_test": {
      "file": "tests/test_auth.py",
      "test_name": "test_password_reset_token_invalidation",
      "code": "def test_password_reset_token_invalidation(): ..."
    }
  },
  "validation": {
    "tests_passing": true,
    "no_regressions": true,
    "ready_to_deploy": true
  }
}
```

### Collaboration

**Works with:**
- **Tessa (Test Engineer)** - Creates regression tests
- **Diana (Documentation Writer)** - Documents bug and fix

---

## Agent 5: Eliza (Estimation Engine)

### Profile
- **Name:** Eliza
- **Role:** Estimation Engine
- **LLM:** Llama 3.1 8B (Local - Ollama)
- **Persona:** Agile expert with statistical analysis skills

### Detailed Role Description

Eliza calculates story points and effort estimates using:
- **Function Points (IFPUG)** for Epic/Feature level
- **Story Points (Fibonacci)** for Story/Task level
- **Three-Point Estimation** (Optimistic, Most Likely, Pessimistic)
- **ML-based refinement** using historical data

### Responsibilities

1. **Function Point Calculation**
   - Count ILF, EIF, EI, EO, EQ components
   - Apply complexity adjustment
   - Convert to effort estimates

2. **Story Point Estimation**
   - Map tasks to Fibonacci sequence
   - Calculate complexity factors
   - Apply team velocity adjustment

3. **Confidence Intervals**
   - Three-point estimation (O, M, P)
   - Calculate expected value: (O + 4M + P) / 6
   - Provide ±% confidence range

4. **Historical Learning**
   - Track estimated vs actual
   - Train ML model
   - Refine estimates based on patterns

### Tools & Capabilities

```typescript
const elizaTools = [
  {
    name: "function_point_calculator",
    description: "Calculate Function Points using IFPUG method",
    input: "Component counts (ILF, EIF, EI, EO, EQ)",
    output: "Total function points with complexity"
  },
  {
    name: "story_point_mapper",
    description: "Map tasks to Fibonacci story points",
    input: "Task description, complexity factors",
    output: "Story point estimate (1,2,3,5,8,13,21)"
  },
  {
    name: "three_point_estimator",
    description: "Calculate three-point estimate with confidence",
    input: "Optimistic, Most Likely, Pessimistic estimates",
    output: "Expected value with confidence interval"
  },
  {
    name: "ml_refinement_engine",
    description: "Refine estimates using historical data",
    input: "Initial estimate, historical data",
    output: "Refined estimate with accuracy score"
  },
  {
    name: "complexity_analyzer",
    description: "Analyze task complexity factors",
    input: "Task details",
    output: "Complexity score (1-10) with breakdown"
  }
];
```

### Triggers

Eliza is activated when:
- **After work breakdown** - Calculate estimates for all tasks
- **On demand** - User requests estimate
- **Re-estimation** - Scope changes require new estimates

### Input Format

```json
{
  "type": "ESTIMATION_REQUEST",
  "level": "epic",
  "item": {
    "id": "EPIC-001",
    "title": "OAuth2 Authentication",
    "features": [...],
    "stories": [...],
    "tasks": [...]
  },
  "historical_context": {
    "similar_projects": ["EPIC-042", "EPIC-089"],
    "team_velocity": 25
  }
}
```

### Output Format

```json
{
  "estimation_result": {
    "epic_id": "EPIC-001",
    "function_points": 21,
    "t_shirt_size": "L",
    "total_story_points": 55,
    "estimated_sprints": 2.2,
    "confidence": "±15%",
    "breakdown": {
      "features": [
        {
          "id": "FEAT-001",
          "function_points": 13,
          "stories": [
            {
              "id": "STORY-001",
              "story_points": 5,
              "optimistic": 3,
              "most_likely": 5,
              "pessimistic": 8,
              "expected": 5.17,
              "tasks": [
                {
                  "id": "TASK-001",
                  "story_points": 1,
                  "estimated_hours": 2,
                  "complexity_factors": {
                    "technical": 3,
                    "integration": 2,
                    "testing": 2
                  }
                }
              ]
            }
          ]
        }
      ]
    },
    "ml_adjustment": {
      "original_estimate": 55,
      "adjusted_estimate": 58,
      "adjustment_factor": 1.055,
      "confidence_score": 0.82
    }
  }
}
```

### Collaboration

**Works with:**
- **Felix (Feature Architect)** - Receives work breakdown, returns estimates
- **All agents** - Provides effort estimates for all work types

---

## Agent 6: Tessa (Test Engineer)

### Profile
- **Name:** Tessa
- **Role:** Test Engineer
- **LLM:** Llama 3.1 8B (Local - Ollama)
- **Persona:** Test automation specialist with TDD/BDD expertise

### Detailed Role Description

Tessa implements 4-track testing pipeline:
1. **Unit Testing** (Function/Method level) - 70%
2. **Module Testing** (Component/Service level) - 20%
3. **E2E Testing** (User Journey level) - 10%
4. **Scenario Testing** (Business Workflow level) - BDD

Target: 80% line coverage, 70% branch coverage

### Responsibilities

1. **Test Strategy**
   - Define test pyramid approach
   - Identify critical test paths
   - Plan test data and fixtures
   - Set coverage targets

2. **Test Generation**
   - Generate unit tests (AAA pattern)
   - Create integration tests
   - Design E2E test scenarios
   - Write BDD scenarios (Gherkin)

3. **Test Execution**
   - Run test suites
   - Collect coverage metrics
   - Identify flaky tests
   - Generate test reports

4. **Quality Assurance**
   - Ensure test coverage targets
   - Validate test quality
   - Review edge cases
   - Maintain test suite health

### Tools & Capabilities

```typescript
const tessaTools = [
  {
    name: "unit_test_generator",
    description: "Generate unit tests using AAA pattern",
    frameworks: ["pytest", "Jest", "JUnit"],
    input: "Function signature, code",
    output: "Unit test code with happy/edge/error cases"
  },
  {
    name: "integration_test_designer",
    description: "Design integration test scenarios",
    frameworks: ["pytest", "Postman"],
    input: "API endpoints, module boundaries",
    output: "Integration test suite"
  },
  {
    name: "e2e_test_creator",
    description: "Create end-to-end user journey tests",
    frameworks: ["Playwright", "Cypress"],
    input: "User stories, UI flows",
    output: "E2E test code with Page Object Model"
  },
  {
    name: "bdd_scenario_writer",
    description: "Write BDD scenarios in Gherkin",
    frameworks: ["Cucumber", "Behave"],
    input: "Business rules",
    output: "Feature files with scenarios"
  },
  {
    name: "coverage_analyzer",
    description: "Analyze test coverage metrics",
    tools: ["pytest-cov", "Istanbul"],
    input: "Test suite",
    output: "Coverage report with gaps"
  },
  {
    name: "test_data_generator",
    description: "Generate test fixtures and data",
    tools: ["Factory Boy", "Faker"],
    input: "Data models",
    output: "Test fixtures and factories"
  }
];
```

### Triggers

Tessa is activated when:
- **Work Type:** `TESTING`
- **After implementation** - Feature needs tests
- **Coverage gap** - Coverage below threshold
- **Bug fix** - Regression test needed

### Input Format

```json
{
  "type": "TESTING_REQUEST",
  "test_levels": ["unit", "integration", "e2e"],
  "target": {
    "type": "feature",
    "id": "FEAT-001",
    "code_location": "backend/app/auth/oauth.py",
    "user_stories": [
      {
        "id": "STORY-001",
        "title": "User can login with Google",
        "acceptance_criteria": [...]
      }
    ]
  },
  "coverage_requirements": {
    "line_coverage": 80,
    "branch_coverage": 70
  }
}
```

### Output Format

```json
{
  "test_suite": {
    "feature_id": "FEAT-001",
    "unit_tests": {
      "file": "tests/unit/test_oauth.py",
      "test_count": 15,
      "coverage": {
        "line": 85,
        "branch": 72
      },
      "tests": [
        {
          "name": "test_google_oauth_success",
          "type": "happy_path",
          "code": "def test_google_oauth_success(): ..."
        },
        {
          "name": "test_google_oauth_invalid_token",
          "type": "error_case",
          "code": "def test_google_oauth_invalid_token(): ..."
        }
      ]
    },
    "integration_tests": {
      "file": "tests/integration/test_oauth_flow.py",
      "test_count": 5,
      "tests": [...]
    },
    "e2e_tests": {
      "file": "tests/e2e/test_login_journey.spec.ts",
      "framework": "Playwright",
      "test_count": 3,
      "tests": [
        {
          "name": "User can complete Google login",
          "steps": [
            "Navigate to /login",
            "Click 'Login with Google'",
            "Enter credentials in OAuth popup",
            "Verify redirect to dashboard"
          ]
        }
      ]
    },
    "bdd_scenarios": {
      "file": "features/oauth_login.feature",
      "scenarios": [
        {
          "title": "User logs in with Google",
          "gherkin": "Feature: OAuth Login\n  Scenario: User logs in with Google\n    Given..."
        }
      ]
    }
  },
  "coverage_report": {
    "line_coverage": 85,
    "branch_coverage": 72,
    "meets_requirements": true,
    "gaps": []
  }
}
```

### Collaboration

**Works with:**
- **Felix (Feature Architect)** - Receives feature spec, creates tests
- **Betty (Bug Hunter)** - Creates regression tests
- **Quinn (Quality Inspector)** - Reports test coverage

---

## Agent 7: Miguel (Migration Architect)

### Profile
- **Name:** Miguel
- **Role:** Migration Architect
- **LLM:** GPT-4 Turbo (Cloud)
- **Persona:** Enterprise architect specializing in large-scale migrations

### Detailed Role Description

Miguel handles complex system migrations using 5-stage pipeline:
1. **Assessment** - Analyze current state, risks
2. **Planning** - Design migration strategy
3. **Execution** - Incremental migration
4. **Validation** - Data integrity, functional equivalence
5. **Cutover** - Production switch with rollback plan

Handles 4 migration types:
- Technology (Python 2→3, Vue 2→3)
- Platform (on-prem→cloud)
- Data (MySQL→PostgreSQL)
- Integration (REST→GraphQL)

### Responsibilities

1. **Migration Assessment**
   - Inventory what needs to migrate
   - Analyze dependencies
   - Calculate Migration Complexity Index (MCI)
   - Risk assessment

2. **Strategy Design**
   - Choose approach (Big Bang, Phased, Parallel)
   - Data mapping strategy
   - Timeline estimation
   - Rollback planning

3. **Migration Execution**
   - Batch processing
   - Progress tracking
   - Automated transformation
   - Checkpoint/resume capability

4. **Validation & Cutover**
   - Data integrity checks
   - Functional equivalence testing
   - Performance benchmarking
   - Production cutover

### Tools & Capabilities

```typescript
const miguelTools = [
  {
    name: "migration_analyzer",
    description: "Analyze migration scope and complexity",
    input: "Current system details, target system",
    output: "Migration assessment with MCI score"
  },
  {
    name: "data_mapper",
    description: "Map data schemas between systems",
    input: "Source schema, target schema",
    output: "Data transformation rules"
  },
  {
    name: "migration_planner",
    description: "Create detailed migration plan",
    input: "Assessment results",
    output: "Migration strategy with timeline"
  },
  {
    name: "batch_processor",
    description: "Execute migration in batches",
    input: "Migration plan, data",
    output: "Migration progress with checkpoints"
  },
  {
    name: "validation_suite",
    description: "Validate migration completeness",
    input: "Migrated data, original data",
    output: "Validation report with discrepancies"
  },
  {
    name: "rollback_generator",
    description: "Generate rollback plan",
    input: "Migration plan",
    output: "Rollback procedures"
  }
];
```

### Triggers

Miguel is activated when:
- **Work Type:** `MIGRATION`
- **User request:** Platform/technology upgrade
- **Scheduled:** Major version upgrades

### Input Format

```json
{
  "type": "MIGRATION",
  "migration_type": "technology",
  "source": {
    "framework": "Vue 2",
    "version": "2.7.14"
  },
  "target": {
    "framework": "Vue 3",
    "version": "3.4.0"
  },
  "scope": {
    "components": 150,
    "lines_of_code": 45000,
    "dependencies": 80
  },
  "constraints": {
    "max_downtime": "4 hours",
    "must_support_rollback": true,
    "data_loss_tolerance": "zero"
  }
}
```

### Output Format

```json
{
  "migration_plan": {
    "migration_id": "MIG-001",
    "complexity_index": 85,
    "risk_level": "HIGH",
    "strategy": "phased",
    "estimated_duration": "7-10 sprints",
    "phases": [
      {
        "phase": 1,
        "name": "Build tooling upgrade",
        "duration": "1 sprint",
        "tasks": [
          {
            "task": "Upgrade Webpack 4→5",
            "effort_sp": 5,
            "risk": "medium"
          }
        ]
      }
    ],
    "data_mapping": {
      "transformations": [
        {
          "from": "Options API",
          "to": "Composition API",
          "complexity": "high",
          "automated": false
        }
      ]
    },
    "validation_plan": {
      "checkpoints": [
        "Component rendering validation",
        "State management validation",
        "Performance benchmarking"
      ]
    },
    "rollback_plan": {
      "triggers": ["Error rate >5%", "Critical bug"],
      "procedure": "Switch DNS back, restore database snapshot",
      "estimated_time": "30 minutes"
    }
  }
}
```

### Collaboration

**Works with:**
- **Eliza (Estimation Engine)** - Gets migration effort estimates
- **Tessa (Test Engineer)** - Ensures migration tests
- **Quinn (Quality Inspector)** - Validates migration quality

---

## Agent 8: Diana (Documentation Writer)

### Profile
- **Name:** Diana
- **Role:** Documentation Writer
- **LLM:** Llama 3.1 8B (Local - Ollama)
- **Persona:** Technical writer with developer background

### Detailed Role Description

Diana generates and maintains:
- **Technical specifications**
- **API documentation** (OpenAPI/Swagger)
- **User guides**
- **README files**
- **Architecture Decision Records (ADRs)**
- **Code comments**

### Responsibilities

1. **Specification Writing**
   - Convert feature analysis to specs
   - Document API contracts
   - Create data model documentation
   - Write architecture documents

2. **API Documentation**
   - Generate OpenAPI schemas
   - Write endpoint descriptions
   - Document request/response formats
   - Provide code examples

3. **User Guides**
   - Write how-to guides
   - Create tutorials
   - Document workflows
   - Troubleshooting guides

4. **Code Documentation**
   - Generate docstrings
   - Write inline comments
   - Create README files
   - Maintain CHANGELOG

### Tools & Capabilities

```typescript
const dianaTools = [
  {
    name: "spec_writer",
    description: "Write technical specifications",
    input: "Feature analysis, requirements",
    output: "Markdown specification document"
  },
  {
    name: "api_doc_generator",
    description: "Generate API documentation",
    tools: ["Swagger", "JSDoc", "Sphinx"],
    input: "API endpoints, code",
    output: "OpenAPI spec, HTML docs"
  },
  {
    name: "readme_creator",
    description: "Create README files",
    input: "Project details",
    output: "Markdown README with sections"
  },
  {
    name: "docstring_generator",
    description: "Generate code docstrings",
    input: "Function signatures",
    output: "Docstrings in appropriate format"
  },
  {
    name: "adr_writer",
    description: "Write Architecture Decision Records",
    input: "Decision details",
    output: "ADR markdown file"
  },
  {
    name: "changelog_updater",
    description: "Update CHANGELOG.md",
    input: "Changes, version",
    output: "Updated CHANGELOG"
  }
];
```

### Triggers

Diana is activated when:
- **Post-implementation** - Feature needs documentation
- **API changes** - Update API docs
- **Release** - Update CHANGELOG
- **Architecture decision** - Write ADR

### Input Format

```json
{
  "type": "DOCUMENTATION_REQUEST",
  "documentation_type": "api",
  "target": {
    "feature_id": "FEAT-001",
    "endpoints": [
      {
        "path": "/api/auth/oauth/google",
        "method": "POST",
        "description": "Authenticate user with Google OAuth2",
        "parameters": [...],
        "responses": [...]
      }
    ]
  }
}
```

### Output Format

```json
{
  "documentation": {
    "type": "api",
    "format": "openapi",
    "files": [
      {
        "path": "docs/api/oauth.md",
        "content": "# OAuth API\n\n## POST /api/auth/oauth/google\n\n..."
      },
      {
        "path": "openapi.yaml",
        "content": "openapi: 3.0.0\ninfo:\n  title: OAuth API\n..."
      }
    ]
  }
}
```

### Collaboration

**Works with:**
- **Felix (Feature Architect)** - Documents feature specs
- **All agents** - Documents their outputs

---

## Agent Collaboration Matrix

| Agent | Collaborates With | Data Flow |
|-------|------------------|-----------|
| Felix (Architect) | Eliza, Tessa, Quinn, Diana | Spec → Estimates, Tests, Review, Docs |
| Marcus (Maintenance) | Quinn, Tessa, Eliza | Findings → Review, Tests, Estimates |
| Quinn (Quality) | Felix, Marcus, Tessa | Reviews all outputs |
| Betty (Bug Hunter) | Tessa, Diana | Bug → Test, Documentation |
| Eliza (Estimation) | All | Provides estimates to all |
| Tessa (Test Engineer) | Felix, Betty, Quinn | Tests features and bugs |
| Miguel (Migration) | Eliza, Tessa, Quinn | Plan → Estimates, Tests, Review |
| Diana (Documentation) | All | Documents all outputs |

---

## Next Steps (Week 5 Day 3)

Tomorrow we'll implement:
1. **KaibanBoard configuration** - Team setup with all 8 agents
2. **Task routing logic** - Route work types to appropriate agents
3. **Sequential/Parallel workflows** - Define workflow execution patterns

---

**Document Version:** 1.0
**Last Updated:** 2025-11-13
**Status:** Complete - Ready for Day 3
