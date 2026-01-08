# MAINTENANCE Work Type Documentation

## Overview

The MAINTENANCE work type provides automated code maintenance through a comprehensive 6-stage workflow that analyzes, prioritizes, plans, and prepares deployment strategies for codebase maintenance tasks.

---

## Quick Start

### Basic Usage

```typescript
import { executeMaintenanceWorkflow } from './workflows/maintenanceWorkflow';

const result = await executeMaintenanceWorkflow({
  scope: 'full_codebase',
  focusAreas: ['dependencies', 'security'],
  urgency: 'high'
});

console.log(`Found ${result.findings.length} issues`);
console.log(`Created ${result.prioritizedTasks.length} tasks`);
```

### Via Work Type Router

```typescript
import { routeWorkRequest } from './routers/workTypeRouter';

const { workType, teamConfig } = routeWorkRequest({
  description: 'Update dependencies and fix security vulnerabilities',
  context: {
    scope: 'full_codebase',
    focusAreas: ['dependencies', 'security'],
    urgency: 'high'
  }
});

// workType: WorkType.MAINTENANCE
// teamConfig.agents: [Marcus, Quinn, Tessa, Eliza]
// teamConfig.workflow: 'code_maintenance_6_stage'
```

---

## API Reference

### MaintenanceRequest Interface

```typescript
interface MaintenanceRequest {
  // Required: Scope of analysis
  scope: 'full_codebase' | 'module' | 'specific_files';

  // Conditional: Required when scope = 'specific_files'
  targetFiles?: string[];

  // Conditional: Required when scope = 'module'
  modulePath?: string;

  // Optional: Areas to focus on
  focusAreas?: Array<
    | 'dependencies'    // Package updates, vulnerability fixes
    | 'code_quality'    // Complexity, duplication, refactoring
    | 'security'        // Security vulnerabilities, OWASP issues
    | 'performance'     // Performance bottlenecks, N+1 queries
    | 'tests'           // Test coverage improvements
    | 'documentation'   // Documentation updates
  >;

  // Optional: Quality thresholds
  thresholds?: {
    maxComplexity?: number;           // Default: 15
    minTestCoverage?: number;         // Default: 80%
    maxTechnicalDebtRatio?: number;   // Default: 10%
  };

  // Optional: Urgency level (affects deployment strategy)
  urgency?: 'low' | 'medium' | 'high' | 'critical';  // Default: 'medium'
}
```

### MaintenanceResult Interface

```typescript
interface MaintenanceResult {
  // Analysis metrics
  analysisReport: {
    technicalDebtRatio: number;
    dependencyVulnerabilities: number;
    codeSmells: number;
    complexityViolations: number;
  };

  // Prioritized findings with details
  findings: Array<{
    category: 'dependency' | 'code_smell' | 'security' | 'performance' | 'test' | 'documentation';
    severity: 'critical' | 'high' | 'medium' | 'low';
    issue: string;
    location?: string;
    recommendation: string;
    effortSP: number;
    risk: 'high' | 'medium' | 'low';
  }>;

  // Actionable tasks
  prioritizedTasks: Array<{
    id: string;
    title: string;
    priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
    effortSP: number;
    timeline: string;
    dependencies: string[];
  }>;

  // Quality improvement metrics
  qualityMetrics: {
    beforeMaintenance: {
      testCoverage: number;
      complexity: number;
      duplication: number;
    };
    afterMaintenance: {
      testCoverage: number;
      complexity: number;
      duplication: number;
    };
    improvement: {
      testCoverageIncrease: number;
      complexityReduction: number;
      duplicationReduction: number;
    };
  };

  // Test strategy
  testStrategy: {
    regressionTests: number;
    newTests: number;
    coverageGoal: number;
  };
}
```

---

## 6-Stage Workflow

### Stage 1: Analysis
**Agent**: Marcus (Maintenance Specialist)

Scans codebase for:
- **Dependencies**: Outdated packages, security vulnerabilities (npm audit)
- **Code Quality**: Cyclomatic complexity, duplication, long methods
- **Security**: OWASP Top 10, hardcoded secrets, unsafe dependencies
- **Performance**: N+1 queries, memory leaks, inefficient algorithms
- **Test Coverage**: Line, branch, and function coverage
- **Technical Debt**: SQALE rating, debt ratio calculation
- **Best Practices**:
  - **SIG-TOP-10**: Software Improvement Group's maintainability guidelines
  - **SOLID Principles**: Object-oriented design principles (SRP, OCP, LSP, ISP, DIP)
  - **GRASP Principles**: General Responsibility Assignment Software Patterns
  - **TDD**: Test-Driven Development (Red-Green-Refactor cycle)
  - **Law of Demeter**: Principle of Least Knowledge

**Best Practice Scoring**:
```typescript
bestPracticeScore: {
  sigCompliance: {
    overall: 68,  // 0-100% compliance
    violations: {
      shortUnits: 5,         // SIG #1: Functions >15 lines
      simpleUnits: 7,        // SIG #2: Complexity >10
      writeOnce: 11,         // SIG #3: Code duplication >3%
      smallInterfaces: 3,    // SIG #4: Functions with >4 params
      separateConcerns: 2,   // SIG #5: Mixed responsibilities
      looseCoupling: 4,      // SIG #6: >10 dependencies
      balancedComponents: 0, // SIG #7: Oversized components
      smallCodebase: 0,      // SIG #8: No dead code
      automatedPipeline: 1,  // SIG #9: Missing CI/CD
      cleanCode: 8           // SIG #10: Unclear naming/docs
    }
  },
  solidCompliance: {
    overall: 72,  // 0-100% compliance
    violations: {
      srp: 3,  // Single Responsibility
      ocp: 2,  // Open/Closed
      lsp: 1,  // Liskov Substitution
      isp: 2,  // Interface Segregation
      dip: 1   // Dependency Inversion
    }
  },
  graspCompliance: {
    overall: 75,  // 0-100% compliance
    violations: {
      informationExpert: 4,  // Wrong class has responsibility
      lowCoupling: 4,        // Too many dependencies
      highCohesion: 5        // Unrelated methods in class
    }
  },
  tddCompliance: {
    overall: 65,  // 0-100% compliance
    violations: {
      noTests: 8,              // Production code without tests
      testAfterCode: 3,        // Tests written after code
      coverageDecrease: 2      // Coverage decreased
    }
  },
  lawOfDemeter: {
    violations: 6  // Method call chains (a.getB().getC())
  },
  totalScore: 70  // Combined: (68 + 72 + 75 + 65) / 4
}
```

### Stage 2: Prioritization
**Agent**: Quinn (Quality Inspector)

Prioritizes findings using:
- **Risk Scoring**: `Impact × Likelihood` (0-100 scale)
- **ROI Calculation**: `Benefit / Effort` ratio
- **Priority Assignment**: P0 (critical) → P4 (backlog)
- **Timeline Scheduling**: immediate, this_week, next_sprint, backlog

### Stage 3: Planning
**Agent**: Eliza (Estimation Engine)

Creates maintenance roadmap:
- **Phase Grouping**: Critical Fixes → High Priority → Planned Improvements
- **Task Breakdown**: Detailed task descriptions with effort estimates
- **Dependency Tracking**: Prerequisites and blockers
- **Duration Estimation**: Based on 5 SP/day velocity

### Stage 4: Execution Strategy
**Agent**: Marcus (Maintenance Specialist)

Defines execution approach:
- **Automated Tasks**: Tool selection (npm update, prettier, npm audit fix)
- **Manual Tasks**: Category-specific checklists and guidance
- **Validation Checks**: Dynamic check generation (test, build, lint, security)

### Stage 5: Test Strategy
**Agent**: Tessa (Test Engineer)

Plans comprehensive testing:
- **Regression Tests**: Updates needed for refactored code
- **Unit Tests**: Coverage gap analysis (target - current / 2)
- **Integration Tests**: For security and dependency fixes
- **E2E Tests**: Critical path coverage for P0/P1 changes
- **Performance Benchmarks**: Based on performance findings

### Stage 6: Deployment Plan
**Agent**: Marcus (Maintenance Specialist)

Selects deployment strategy based on risk:
- **Immediate**: Critical security + urgent → Single deploy
- **Canary**: P0/high risk → 10% → 50% → 100%
- **Blue-Green**: Moderate risk → Deploy to green → Switch
- **Rolling**: Low risk → Gradual instance updates

---

## Action Breakdown System

Each maintenance task is automatically broken down into **4-8 discrete actions**, with each action taking **0.5-1 hour** to complete. This provides:
- **Granular Progress Tracking**: Track completion at action level
- **Accurate Estimates**: Each action has precise time estimate
- **Better Planning**: Split large tasks automatically
- **Status Visibility**: Monitor pending, in_progress, completed, blocked actions

### Action Structure

```typescript
interface TaskAction {
  id: string;                    // Unique action identifier
  description: string;            // What needs to be done
  estimatedHours: number;         // 0.5-1.0 hours (rounded to 0.5)
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  result?: string;                // Outcome after completion
  blockedReason?: string;         // If status = 'blocked'
}
```

### Action Generation Rules

1. **Story Points → Hours**: 1 SP ≈ 4 hours
2. **Minimum Estimate**: Tasks < 0.5 hours → rounded to 0.5 hours
3. **Action Count**: 4-8 actions per task
4. **Action Duration**: Each action 0.5-1 hour (rounded to nearest 0.5)
5. **Task Splitting**: Tasks needing >8 actions are flagged for splitting

### Category-Specific Action Templates

**Automated Tasks** (4 actions):
1. Review current implementation and identify issue
2. Run automated tool/script to apply fix
3. Verify fix resolves the issue
4. Run test suite to ensure no regressions

**Dependency Updates** (8 actions):
1. Analyze dependency vulnerability and breaking changes
2. Update package version in package.json
3. Run npm install and resolve conflicts
4. Update code for breaking changes if any
5. Run full test suite
6. Test integration with dependent modules
7. Update documentation
8. Create changelog entry

**Security Fixes** (8 actions):
1. Analyze security vulnerability (OWASP/CVE details)
2. Review OWASP guidelines for this vulnerability type
3. Implement security fix following best practices
4. Add security-specific unit tests
5. Perform security testing (penetration test)
6. Add security regression tests
7. Update security documentation
8. Notify stakeholders of security fix

**Code Refactoring** (8 actions):
1. Analyze code complexity and identify refactoring opportunities
2. Design refactoring approach (Extract Method/Class)
3. Implement refactoring incrementally
4. Add/update unit tests for refactored code
5. Run test suite and fix any failures
6. Code review and pair programming session
7. Update documentation and comments
8. Verify performance is maintained or improved

**Performance Optimization** (8 actions):
1. Profile code to identify bottleneck
2. Analyze performance metrics (response time, memory)
3. Design optimization strategy
4. Implement performance improvements
5. Run performance benchmarks
6. Compare before/after metrics
7. Add performance regression tests
8. Document optimization approach

**Test Coverage** (8 actions):
1. Analyze code coverage gaps
2. Identify critical paths needing tests
3. Write unit tests for core functionality
4. Write integration tests for key flows
5. Add edge case and error scenario tests
6. Achieve target coverage threshold
7. Review test quality and maintainability
8. Update testing documentation

**SIG-TOP-10 #2 Violation - High Complexity** (8 actions):
1. Measure current cyclomatic complexity
2. Identify complex conditional logic
3. Apply Strategy or Guard Clause pattern
4. Extract complex conditions into separate methods
5. Verify complexity is reduced to ≤10
6. Add unit tests for each code path
7. Run full test suite
8. Document refactoring in code comments

**SIG-TOP-10 #3 Violation - Code Duplication** (8 actions):
1. Detect duplicate code blocks (≥6 lines)
2. Analyze commonalities and differences
3. Design abstraction (base class, mixin, or utility)
4. Extract duplicated logic into reusable component
5. Update all call sites to use extracted code
6. Run tests to verify behavior unchanged
7. Remove duplicate code
8. Update documentation

**SOLID SRP Violation - Multiple Responsibilities** (8 actions):
1. Identify multiple responsibilities in class
2. Determine primary responsibility for each
3. Design separation: data access, logic, presentation
4. Extract classes (e.g., Repository, Service, View)
5. Update dependencies between new classes
6. Add unit tests for each separated class
7. Verify integration works correctly
8. Update documentation and architecture diagrams

**SOLID OCP Violation - Type Switch Statements** (8 actions):
1. Identify switch/if-else chain on object types
2. Define interface or abstract base class
3. Create concrete implementations for each type
4. Replace conditionals with polymorphism
5. Add Factory pattern if needed
6. Test each concrete implementation
7. Verify new types can be added without modification
8. Update documentation with extension points

**GRASP Information Expert Violation** (8 actions):
1. Identify which class has the information needed
2. Analyze current responsibility assignment
3. Move method to Information Expert class
4. Update all callers to use correct class
5. Verify behavior is maintained
6. Add/update unit tests
7. Run full test suite
8. Document responsibility assignment

**GRASP High Cohesion Violation** (8 actions):
1. Identify unrelated responsibilities in class
2. Group related methods by purpose
3. Extract cohesive classes for each responsibility
4. Update dependencies between classes
5. Verify each class has focused purpose
6. Add tests for extracted classes
7. Run full test suite
8. Update documentation

**Law of Demeter Violation** (8 actions):
1. Identify chained method calls (a.getB().getC())
2. Analyze what information is actually needed
3. Add delegation methods to hide internal structure
4. Update callers to use single method call
5. Verify encapsulation is improved
6. Add unit tests for new delegation methods
7. Run full test suite
8. Document new public API

**TDD Violation - No Tests** (8 actions):
1. Write failing test for first public method (RED)
2. Implement minimal code to pass test (GREEN)
3. Refactor while keeping test green (REFACTOR)
4. Repeat RED-GREEN-REFACTOR for each method
5. Add edge case and error scenario tests
6. Achieve target coverage threshold
7. Review test quality and maintainability
8. Commit tests WITH production code

**TDD Violation - Tests After Code** (8 actions):
1. Review existing production code
2. Write comprehensive tests for existing code
3. Identify gaps in test coverage
4. Add missing tests (unit, integration, edge cases)
5. Refactor code while keeping tests green
6. Document TDD practice for future features
7. Setup pre-commit hooks to enforce test-first
8. Update testing documentation

**TDD Violation - Coverage Decreased** (8 actions):
1. Identify new code added without tests
2. Write tests for untested code paths
3. Add tests for edge cases and error scenarios
4. Verify coverage returns to previous level
5. Setup coverage threshold checks in CI/CD
6. Configure pre-commit hooks to block coverage decrease
7. Run full test suite
8. Update coverage reports

### Example: Task with Actions

```typescript
{
  id: 'SEC-001',
  title: 'Fix XSS vulnerability in user input validation',
  type: 'manual',
  effortSP: 2,              // 2 Story Points
  effortHours: 8,           // 2 SP × 4 hours = 8 hours
  assignedAgent: 'Security Expert',
  actions: [
    {
      id: 'SEC-001-action-1',
      description: 'Analyze security vulnerability (OWASP/CVE details)',
      estimatedHours: 1.0,
      status: 'completed',
      result: 'XSS vulnerability in /api/users endpoint confirmed'
    },
    {
      id: 'SEC-001-action-2',
      description: 'Review OWASP guidelines for this vulnerability type',
      estimatedHours: 1.0,
      status: 'completed',
      result: 'OWASP A7:2021 XSS prevention guidelines reviewed'
    },
    {
      id: 'SEC-001-action-3',
      description: 'Implement security fix following best practices',
      estimatedHours: 1.0,
      status: 'in_progress'
    },
    {
      id: 'SEC-001-action-4',
      description: 'Add security-specific unit tests',
      estimatedHours: 1.0,
      status: 'pending'
    },
    {
      id: 'SEC-001-action-5',
      description: 'Perform security testing (penetration test)',
      estimatedHours: 1.0,
      status: 'pending'
    },
    {
      id: 'SEC-001-action-6',
      description: 'Add security regression tests',
      estimatedHours: 1.0,
      status: 'pending'
    },
    {
      id: 'SEC-001-action-7',
      description: 'Update security documentation',
      estimatedHours: 1.0,
      status: 'pending'
    },
    {
      id: 'SEC-001-action-8',
      description: 'Notify stakeholders of security fix',
      estimatedHours: 1.0,
      status: 'pending'
    }
  ]
}
```

### Progress Tracking

Track progress at action level:

```typescript
const task = maintenancePlan.phases[0].tasks[0];

// Count completed actions
const completed = task.actions.filter(a => a.status === 'completed').length;
const total = task.actions.length;
const progress = (completed / total) * 100;

console.log(`Task Progress: ${progress}% (${completed}/${total} actions)`);

// Estimate remaining time
const remainingActions = task.actions.filter(a => a.status === 'pending');
const remainingHours = remainingActions.reduce((sum, a) => sum + a.estimatedHours, 0);

console.log(`Estimated time remaining: ${remainingHours} hours`);
```

---

## Usage Examples

### Example 1: Full Codebase Security Audit

```typescript
const result = await executeMaintenanceWorkflow({
  scope: 'full_codebase',
  focusAreas: ['dependencies', 'security', 'code_quality'],
  thresholds: {
    maxComplexity: 15,
    minTestCoverage: 80,
    maxTechnicalDebtRatio: 10
  },
  urgency: 'high'
});

console.log('Analysis Report:');
console.log(`  Technical Debt: ${result.analysisReport.technicalDebtRatio}%`);
console.log(`  Vulnerabilities: ${result.analysisReport.dependencyVulnerabilities}`);
console.log(`  Code Smells: ${result.analysisReport.codeSmells}`);

console.log('\nPrioritized Tasks:');
result.prioritizedTasks.forEach(task => {
  console.log(`  [${task.priority}] ${task.title} (${task.effortSP} SP)`);
});
```

**Output:**
```
Analysis Report:
  Technical Debt: 12.5%
  Vulnerabilities: 8
  Code Smells: 18

Prioritized Tasks:
  [P0] Update axios to fix XSS vulnerability (1 SP)
  [P0] Strengthen password policy (2 SP)
  [P1] Fix N+1 query in getUserPosts (2 SP)
  [P2] Refactor processUserData function (3 SP)
```

---

### Example 2: Module Performance Optimization

```typescript
const result = await executeMaintenanceWorkflow({
  scope: 'module',
  modulePath: 'src/auth',
  focusAreas: ['performance', 'code_quality'],
  thresholds: {
    maxComplexity: 12,
    minTestCoverage: 85
  },
  urgency: 'medium'
});

console.log('Quality Metrics:');
console.log(`  Before: ${result.qualityMetrics.beforeMaintenance.complexity} complexity`);
console.log(`  After: ${result.qualityMetrics.afterMaintenance.complexity} complexity`);
console.log(`  Improvement: ${result.qualityMetrics.improvement.complexityReduction}%`);
```

---

### Example 3: Specific Files Test Coverage

```typescript
const result = await executeMaintenanceWorkflow({
  scope: 'specific_files',
  targetFiles: [
    'src/payment/processor.ts',
    'src/payment/validator.ts',
    'src/payment/stripe-integration.ts'
  ],
  focusAreas: ['tests', 'code_quality'],
  thresholds: {
    minTestCoverage: 90
  },
  urgency: 'high'
});

console.log('Test Strategy:');
console.log(`  Regression Tests: ${result.testStrategy.regressionTests}`);
console.log(`  New Tests Needed: ${result.testStrategy.newTests}`);
console.log(`  Coverage Goal: ${result.testStrategy.coverageGoal}%`);
```

---

### Example 4: Critical Security Patch

```typescript
const result = await executeMaintenanceWorkflow({
  scope: 'specific_files',
  targetFiles: [
    'src/validation/user-input.ts',
    'src/sanitization/html-cleaner.ts'
  ],
  focusAreas: ['security'],
  urgency: 'critical'
});

// With urgency: 'critical' + security findings:
// Deployment Strategy: immediate
// Stages: Single production deployment
// Monitoring: Authentication failures, Authorization denials
```

---

## Team Configuration

The MAINTENANCE work type uses a **sequential** team of 4 agents:

### 1. Marcus - Maintenance Specialist
**Role**: Primary maintenance analysis and planning
**Stages**: 1 (Analysis), 4 (Execution), 6 (Deployment)
**Expertise**: Dependency management, refactoring, technical debt reduction

### 2. Quinn - Quality Inspector
**Role**: Quality assessment and prioritization
**Stage**: 2 (Prioritization)
**Expertise**: Code quality metrics, risk assessment, ROI analysis

### 3. Tessa - Test Engineer
**Role**: Test strategy and coverage planning
**Stage**: 5 (Testing)
**Expertise**: Test automation, coverage analysis, regression testing

### 4. Eliza - Estimation Engine
**Role**: Effort estimation and timeline planning
**Stage**: 3 (Planning)
**Expertise**: Story point estimation, velocity tracking, sprint planning

---

## Deployment Strategy Selection

The workflow automatically selects deployment strategy based on:

### Immediate Deployment
**Triggers:**
- Critical security fixes (`urgency: 'critical'` + security findings)
- P0 priority security vulnerabilities

**Process:**
1. Production Deployment (30 min)
2. Verify security patch
3. Monitor for 30 minutes

**Use Case:** Emergency security patches

---

### Canary Deployment
**Triggers:**
- P0 priority findings
- Risk score ≥ 70 (high-risk changes)

**Process:**
1. Canary (10%) - 2 hours
2. Partial (50%) - 4 hours
3. Full (100%) - 2 hours

**Use Case:** High-risk refactoring, critical bug fixes

---

### Blue-Green Deployment
**Triggers:**
- `urgency: 'high'` or `'medium'`
- Moderate risk changes

**Process:**
1. Deploy to green environment - 1 hour
2. Switch traffic - 30 minutes
3. Decommission blue - 1 hour (after 24h)

**Use Case:** Feature refactoring, dependency updates

---

### Rolling Deployment
**Triggers:**
- `urgency: 'low'`
- No critical findings
- Documentation updates

**Process:**
1. Rolling update start - 2 hours
2. Rolling update complete - 1 hour

**Use Case:** Documentation, low-risk improvements

---

## Validation

### Automatic Validation

All requests are automatically validated before execution:

```typescript
import { validateMaintenanceRequest } from './workflows/maintenanceWorkflow';

const validation = validateMaintenanceRequest(request);

if (!validation.valid) {
  console.error('Validation errors:', validation.errors);
  return;
}
```

### Validation Rules

**Scope Validation:**
- Must be: `full_codebase`, `module`, or `specific_files`

**Scope-Specific Validation:**
- `scope: 'module'` requires `modulePath`
- `scope: 'specific_files'` requires `targetFiles` (non-empty array)

**Threshold Validation:**
- `maxComplexity`: Must be ≥ 1
- `minTestCoverage`: Must be 0-100
- `maxTechnicalDebtRatio`: Must be ≥ 0

---

## Work Type Classification

The MAINTENANCE work type is automatically detected from these keywords:

- update, upgrade
- dependency, dependencies
- maintenance
- refactor, refactoring
- clean, cleanup
- organize
- deprecate, deprecated

### Example Classifications

```typescript
// All classified as MAINTENANCE:
"Update dependencies"
"Upgrade React to v18"
"Refactor authentication module"
"Clean up deprecated code"
"Organize project structure"
"Update npm packages"
```

---

## Integration Guide

### Python → TypeScript Bridge

```bash
# Via execute-workflow.ts
echo '{
  "description": "Update dependencies and fix vulnerabilities",
  "context": {
    "scope": "full_codebase",
    "focusAreas": ["dependencies", "security"],
    "urgency": "high"
  }
}' | npx ts-node execute-workflow.ts
```

### Direct Integration

```typescript
import { executeMaintenanceWorkflow } from './workflows/maintenanceWorkflow';

async function runMaintenance() {
  try {
    const result = await executeMaintenanceWorkflow({
      scope: 'full_codebase',
      focusAreas: ['dependencies'],
      urgency: 'high'
    });

    console.log('Maintenance completed!');
    console.log(`Findings: ${result.findings.length}`);
    console.log(`Tasks: ${result.prioritizedTasks.length}`);

  } catch (error) {
    console.error('Maintenance failed:', error);
  }
}

runMaintenance();
```

---

## Best Practices

### 1. Choose Appropriate Scope

**Full Codebase:**
- Periodic maintenance reviews (weekly/monthly)
- Security audits
- Dependency updates

**Module:**
- Performance optimization
- Feature refactoring
- Module-specific improvements

**Specific Files:**
- Critical bug fixes
- Security patches
- Focused test coverage improvements

### 2. Set Realistic Thresholds

```typescript
// Conservative (stricter)
{
  maxComplexity: 10,
  minTestCoverage: 90,
  maxTechnicalDebtRatio: 5
}

// Balanced (recommended)
{
  maxComplexity: 15,
  minTestCoverage: 80,
  maxTechnicalDebtRatio: 10
}

// Lenient (for legacy code)
{
  maxComplexity: 20,
  minTestCoverage: 60,
  maxTechnicalDebtRatio: 20
}
```

### 3. Use Appropriate Urgency

- **critical**: Security vulnerabilities, production issues
- **high**: Important refactoring, significant debt
- **medium**: Regular maintenance, improvements
- **low**: Documentation, minor cleanup

### 4. Focus Areas Combinations

**Security-First:**
```typescript
focusAreas: ['security', 'dependencies']
```

**Quality-First:**
```typescript
focusAreas: ['code_quality', 'tests']
```

**Performance-First:**
```typescript
focusAreas: ['performance', 'code_quality']
```

**Comprehensive:**
```typescript
focusAreas: ['dependencies', 'security', 'code_quality', 'performance', 'tests']
```

---

## Troubleshooting

### Issue: "Invalid scope" error

**Solution:** Use only: `full_codebase`, `module`, or `specific_files`

```typescript
// ✗ Wrong
{ scope: 'all' }

// ✓ Correct
{ scope: 'full_codebase' }
```

---

### Issue: "modulePath required" error

**Solution:** Provide modulePath when using module scope

```typescript
// ✗ Wrong
{ scope: 'module' }

// ✓ Correct
{ scope: 'module', modulePath: 'src/auth' }
```

---

### Issue: "targetFiles required" error

**Solution:** Provide targetFiles array when using specific_files scope

```typescript
// ✗ Wrong
{ scope: 'specific_files' }

// ✓ Correct
{
  scope: 'specific_files',
  targetFiles: ['src/auth/validator.ts']
}
```

---

## Performance Considerations

- **Full Codebase Scan**: ~30-60 seconds (depends on codebase size)
- **Module Scan**: ~10-30 seconds
- **Specific Files**: ~5-15 seconds

**Optimization Tips:**
- Use `scope: 'module'` for focused analysis
- Specify `focusAreas` to limit analysis scope
- Run comprehensive scans periodically (weekly/monthly)
- Use specific files scope for critical fixes

---

## Changelog

### Week 8 (Current)
- ✅ Implemented 6-stage workflow
- ✅ Added intelligent prioritization (Risk × ROI)
- ✅ Dynamic deployment strategy selection
- ✅ Coverage gap analysis for test planning
- ✅ Category-specific task checklists
- ✅ Work type router integration
- ✅ **Action breakdown system** (4-8 actions per task, 0.5-1 hour each)
- ✅ Category-specific action templates (7 categories)
- ✅ Automatic task splitting detection (>8 actions)
- ✅ Minimum 0.5 hour estimate enforcement
- ✅ Action-level progress tracking with status

### Week 7
- ✅ Basic MAINTENANCE work type defined
- ✅ Team configuration (Marcus, Quinn, Tessa, Eliza)
- ✅ Sequential workflow process

---

## See Also

- [Best Practices Reference (SIG-TOP-10 & SOLID)](./BEST_PRACTICES_REFERENCE.md)
- [Code-Maintenance-Agent Architecture](../WEEK_8_DAY_1_SUMMARY.md)
- [Enhanced Stages 4-6](../WEEK_8_DAY_2_3_SUMMARY.md)
- [Work Type Router](../routers/workTypeRouter.ts)
- [Example Requests](../examples/maintenance-requests.json)
- [Integration Tests](../test-maintenance-integration.ts)
