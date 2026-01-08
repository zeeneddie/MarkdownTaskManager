# Quality Gates Integration Proposal

## Current Situation

**Quality Gates (22 checks) zijn nu alleen in MAINTENANCE work type**:
- SIG-TOP-10 (10 checks)
- SOLID (5 checks)
- GRASP (3 checks)
- TDD (3 checks)
- Law of Demeter (1 check)

**Probleem**: Andere work types hebben GEEN quality checks!

---

## Proposal: Universal Quality Gate Service

### Concept
Maak een **Quality Gate Service** die door **alle work types** gebruikt kan worden waar code wordt geschreven.

---

## Work Types die Quality Gates nodig hebben

### 1. **NEW_FEATURE** (Nieuwe features bouwen)
**Current workflow**: `spec_kit_pipeline`
**Agents**: FeatureArchitect, EstimationEngine, TestEngineer, QualityInspector

**Quality Gates toevoegen**:
✅ **Voor implementatie** (Pre-commit):
- TDD: Test eerst schrijven
- Design check: SOLID, GRASP principes
- Complexity threshold: SIG #2 (<10)

✅ **Na implementatie** (Post-commit):
- Coverage check: Niet laten dalen
- Code duplication: SIG #3 (<3%)
- Law of Demeter violations

**Use case**:
```typescript
// Developer werkt aan nieuwe feature
POST /api/workflows/execute
{
  "workType": "NEW_FEATURE",
  "description": "Add user profile editing",
  "enableQualityGates": true  // ← NEW parameter
}

// Response includes quality gate results:
{
  "featureSpec": { /* ... */ },
  "qualityGateResults": {
    "preImplementation": {
      "tddCheck": "PASS - Tests written first",
      "designCheck": "PASS - SOLID principles followed"
    },
    "postImplementation": {
      "coverageCheck": "PASS - Coverage 82% → 85%",
      "duplicationCheck": "WARN - 4% duplication (threshold: 3%)"
    }
  }
}
```

---

### 2. **BUG** (Bug fixing)
**Current workflow**: `bug_fix_5_stage`
**Agents**: BugHunter, TestEngineer, DocumentationWriter

**Quality Gates toevoegen**:
✅ **Voor bug fix**:
- Regression test check: Test moet bestaan die bug reproduceert
- Root cause analysis: Waarom ontbrak deze test?

✅ **Na bug fix**:
- Test coverage: Nieuwe test toegevoegd
- Code quality: Fix introduceert geen nieuwe violations
- TDD lesson learned: Documenteer hoe TDD dit had voorkomen

**Use case**:
```typescript
POST /api/workflows/execute
{
  "workType": "BUG",
  "description": "Fix XSS vulnerability in user input",
  "enableQualityGates": true
}

// Quality gate checkt:
{
  "bugFix": { /* ... */ },
  "qualityGateResults": {
    "preFix": {
      "regressionTestExists": "FAIL - No test reproduces bug",
      "rootCauseAnalysis": "TDD violation - code written without tests"
    },
    "postFix": {
      "regressionTestAdded": "PASS - Test added and passing",
      "noNewViolations": "PASS - No new quality issues introduced",
      "tddLessonDocumented": "PASS - Added to team wiki"
    }
  }
}
```

---

### 3. **ENHANCEMENT** (Bestaande features verbeteren)
**Current workflow**: Enhancement workflow
**Agents**: FeatureArchitect, MaintenanceSpecialist, EstimationEngine

**Quality Gates toevoegen**:
✅ **Voor enhancement**:
- Refactoring opportunities: SIG, SOLID violations
- Design improvements: GRASP principes

✅ **Na enhancement**:
- Quality improvement: Score moet stijgen, niet dalen
- Performance: Geen regressie
- Test coverage: Moet stijgen bij toevoegen features

---

### 4. **TESTING** (Test suite verbeteren)
**Current workflow**: Testing workflow

**Quality Gates toevoegen**:
✅ **Test quality checks**:
- AAA Pattern compliance
- F.I.R.S.T principles
- Test Pyramid ratio (70% unit, 20% integration, 10% E2E)
- TDD compliance

---

## Implementation Architecture

### Option 1: Centralized Quality Gate Service ⭐ (RECOMMENDED)

**Voordeel**: DRY - één plek voor alle quality checks

```typescript
// services/qualityGateService.ts
export class QualityGateService {
  async checkPreImplementation(context: {
    workType: WorkType;
    files: string[];
    description: string;
  }): Promise<QualityGateResult> {
    return {
      tddCheck: this.checkTDD(context),
      designCheck: this.checkDesign(context),
      complexityCheck: this.checkComplexity(context)
    };
  }

  async checkPostImplementation(context: {
    workType: WorkType;
    files: string[];
    gitDiff: string;
  }): Promise<QualityGateResult> {
    return {
      coverageCheck: this.checkCoverage(context),
      duplicationCheck: this.checkDuplication(context),
      violationsCheck: this.checkViolations(context)
    };
  }

  private checkTDD(context): CheckResult {
    // Check if tests exist for production files
    // Check if tests were written first (git history)
    // Check if coverage decreased
  }

  private checkDesign(context): CheckResult {
    // Run SOLID checks
    // Run GRASP checks
    // Run Law of Demeter checks
  }

  // ... other checks
}
```

**Usage in alle workflows**:
```typescript
// workflows/newFeatureWorkflow.ts
import { QualityGateService } from '../services/qualityGateService';

export async function executeNewFeatureWorkflow(request: WorkRequest) {
  const qualityGate = new QualityGateService();

  // Pre-implementation checks
  const preChecks = await qualityGate.checkPreImplementation({
    workType: WorkType.NEW_FEATURE,
    files: request.context.targetFiles,
    description: request.description
  });

  if (preChecks.hasBlockingIssues()) {
    return {
      status: 'blocked',
      issues: preChecks.blockingIssues,
      message: 'Fix quality issues before implementing'
    };
  }

  // ... normal workflow execution ...

  // Post-implementation checks
  const postChecks = await qualityGate.checkPostImplementation({
    workType: WorkType.NEW_FEATURE,
    files: request.context.modifiedFiles,
    gitDiff: await getGitDiff()
  });

  return {
    featureSpec: result,
    qualityGateResults: {
      pre: preChecks,
      post: postChecks
    }
  };
}
```

---

### Option 2: Workflow Decorator Pattern

**Voordeel**: Kan quality gates optioneel maken per workflow

```typescript
// decorators/withQualityGates.ts
export function withQualityGates<T>(
  workflow: (request: WorkRequest) => Promise<T>,
  options: {
    preChecks?: QualityCheckType[];
    postChecks?: QualityCheckType[];
    blocking?: boolean;
  }
) {
  return async (request: WorkRequest): Promise<T & { qualityGates: QualityGateResults }> => {
    const qualityGate = new QualityGateService();

    // Pre-checks
    if (options.preChecks) {
      const preResults = await qualityGate.runChecks(options.preChecks, request);
      if (options.blocking && preResults.hasBlockingIssues()) {
        throw new QualityGateBlockedError(preResults);
      }
    }

    // Execute workflow
    const result = await workflow(request);

    // Post-checks
    let postResults;
    if (options.postChecks) {
      postResults = await qualityGate.runChecks(options.postChecks, request);
    }

    return {
      ...result,
      qualityGates: {
        pre: preResults,
        post: postResults
      }
    };
  };
}

// Usage:
export const newFeatureWorkflow = withQualityGates(
  executeNewFeatureWorkflowCore,
  {
    preChecks: ['TDD', 'DESIGN', 'COMPLEXITY'],
    postChecks: ['COVERAGE', 'DUPLICATION', 'VIOLATIONS'],
    blocking: true
  }
);
```

---

## Quality Gate Configuration per Work Type

```typescript
// configs/qualityGateConfig.ts
export const QUALITY_GATE_CONFIG: Record<WorkType, QualityGateConfig> = {
  [WorkType.NEW_FEATURE]: {
    enabled: true,
    preImplementation: {
      checks: ['TDD', 'SOLID', 'GRASP', 'SIG_COMPLEXITY'],
      blocking: true,  // Block if violated
      severity: 'high'
    },
    postImplementation: {
      checks: ['COVERAGE', 'DUPLICATION', 'LAW_OF_DEMETER', 'NEW_VIOLATIONS'],
      blocking: false,  // Warn but don't block
      severity: 'medium'
    }
  },

  [WorkType.BUG]: {
    enabled: true,
    preImplementation: {
      checks: ['REGRESSION_TEST_EXISTS', 'ROOT_CAUSE_TDD'],
      blocking: true,
      severity: 'high'
    },
    postImplementation: {
      checks: ['REGRESSION_TEST_ADDED', 'NO_NEW_VIOLATIONS', 'TDD_LESSON'],
      blocking: true,
      severity: 'high'
    }
  },

  [WorkType.MAINTENANCE]: {
    enabled: true,
    preImplementation: {
      checks: ['ALL_BEST_PRACTICES'],  // Full 22 checks
      blocking: false,
      severity: 'low'
    },
    postImplementation: {
      checks: ['QUALITY_IMPROVEMENT', 'NO_REGRESSION'],
      blocking: true,
      severity: 'medium'
    }
  },

  [WorkType.ENHANCEMENT]: {
    enabled: true,
    preImplementation: {
      checks: ['SOLID', 'GRASP', 'REFACTORING_OPPORTUNITIES'],
      blocking: false,
      severity: 'medium'
    },
    postImplementation: {
      checks: ['QUALITY_SCORE_INCREASE', 'PERFORMANCE_NO_REGRESSION'],
      blocking: true,
      severity: 'high'
    }
  },

  [WorkType.TESTING]: {
    enabled: true,
    preImplementation: {
      checks: ['AAA_PATTERN', 'FIRST_PRINCIPLES', 'TEST_PYRAMID'],
      blocking: false,
      severity: 'low'
    },
    postImplementation: {
      checks: ['TEST_QUALITY', 'COVERAGE_INCREASE'],
      blocking: false,
      severity: 'low'
    }
  }
};
```

---

## Integration with Git Workflow

### Pre-commit Hook Integration

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|js|tsx|jsx)$')

if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

# Run quality gate checks
echo "Running quality gate checks..."

npx ts-node agents/scripts/preCommitQualityCheck.ts \
  --files "$STAGED_FILES" \
  --blocking

if [ $? -ne 0 ]; then
  echo "❌ Quality gate checks failed. Commit blocked."
  echo "Fix issues or use --no-verify to bypass (not recommended)"
  exit 1
fi

echo "✅ Quality gate checks passed"
exit 0
```

### Pre-commit Quality Check Script

```typescript
// agents/scripts/preCommitQualityCheck.ts
import { QualityGateService } from '../services/qualityGateService';

async function main() {
  const args = parseArgs(process.argv);
  const qualityGate = new QualityGateService();

  const results = await qualityGate.checkPreImplementation({
    files: args.files,
    workType: detectWorkType(args.files),
    description: getCommitMessage()
  });

  if (results.hasBlockingIssues()) {
    console.error('❌ Quality Gate Violations:');
    results.blockingIssues.forEach(issue => {
      console.error(`  - ${issue.check}: ${issue.message}`);
    });
    process.exit(1);
  }

  if (results.hasWarnings()) {
    console.warn('⚠️  Quality Gate Warnings:');
    results.warnings.forEach(warning => {
      console.warn(`  - ${warning.check}: ${warning.message}`);
    });
  }

  console.log('✅ All quality checks passed');
  process.exit(0);
}

main();
```

---

## Developer Experience

### Example: NEW_FEATURE met Quality Gates

```bash
# Developer start nieuwe feature
git checkout -b feature/user-profile-edit

# 1. Write tests first (TDD)
# src/user/UserProfile.test.ts
test('should update user profile', () => {
  // Arrange
  const user = new User({ name: 'John' });
  const profile = new UserProfile(user);

  // Act
  profile.update({ name: 'Jane' });

  // Assert
  expect(user.name).toBe('Jane');
});

# 2. Implement feature
# src/user/UserProfile.ts
class UserProfile {
  update(data: UserData) {
    // Implementation
  }
}

# 3. Commit (pre-commit hook runs)
git add .
git commit -m "feat: Add user profile editing"

# Pre-commit hook output:
Running quality gate checks...
✓ TDD Check: PASS - Tests written before implementation
✓ SOLID Check: PASS - Single Responsibility Principle followed
✓ Complexity Check: PASS - All methods < 10 complexity
✓ Coverage Check: PASS - Coverage increased from 82% to 85%
✓ Duplication Check: PASS - 2.1% duplication (threshold: 3%)
✅ All quality checks passed

[feature/user-profile-edit abc123d] feat: Add user profile editing
 2 files changed, 45 insertions(+)
```

### Example: BUG met Quality Gates

```bash
# Developer fixes bug
git checkout -b fix/xss-vulnerability

# Quality gate blokkeert als geen test bestaat!
git commit -m "fix: XSS vulnerability"

Running quality gate checks...
❌ Quality Gate Violations:
  - REGRESSION_TEST_EXISTS: FAIL - No test reproduces this bug
  - ROOT_CAUSE_TDD: WARN - This bug could have been prevented by TDD

Fix issues or use --no-verify to bypass (not recommended)

# Developer moet eerst test schrijven
# src/validation/UserInput.test.ts
test('should prevent XSS in user input', () => {
  const input = '<script>alert("XSS")</script>';
  expect(sanitize(input)).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
});

# Nu kan developer fixen
# src/validation/UserInput.ts
function sanitize(input: string): string {
  return input.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

# Commit opnieuw
git add .
git commit -m "fix: XSS vulnerability with regression test"

Running quality gate checks...
✓ REGRESSION_TEST_EXISTS: PASS - Test reproduces bug
✓ REGRESSION_TEST_ADDED: PASS - Test now passing
✓ NO_NEW_VIOLATIONS: PASS - No new quality issues
✓ TDD_LESSON: PASS - Documented in team wiki
✅ All quality checks passed
```

---

## Implementation Phases

### Phase 1: Centralized Service (Week 10) 🎯
- [x] Create QualityGateService class
- [ ] Extract quality checks from MAINTENANCE workflow
- [ ] Add pre/post implementation check methods
- [ ] Create quality gate configuration per work type
- [ ] Write unit tests for QualityGateService

### Phase 2: Integrate with NEW_FEATURE (Week 10-11)
- [ ] Add quality gates to NEW_FEATURE workflow
- [ ] Configure checks (TDD, SOLID, GRASP, Coverage)
- [ ] Test with real feature development
- [ ] Document developer workflow

### Phase 3: Integrate with BUG (Week 11)
- [ ] Add quality gates to BUG workflow
- [ ] Add regression test checks
- [ ] Add root cause analysis
- [ ] Test with real bug fixes

### Phase 4: Pre-commit Hooks (Week 11-12)
- [ ] Create pre-commit hook script
- [ ] Add to project setup
- [ ] Document bypass procedures
- [ ] Train team on usage

### Phase 5: All Other Work Types (Week 12)
- [ ] ENHANCEMENT
- [ ] TESTING
- [ ] QUALITY_IMPROVEMENT
- [ ] MIGRATION

---

## Benefits

### For Developers
- **Consistency**: Same quality standards everywhere
- **Early Feedback**: Issues caught before code review
- **Learning**: Best practices enforced automatically
- **Confidence**: Know code meets quality standards

### For Code Quality
- **Prevention**: Issues prevented, not just detected
- **TDD Enforcement**: Tests written first becomes habit
- **No Regression**: Quality can't decrease
- **Measurable**: Track quality improvements

### For Team
- **Faster Reviews**: Less time on quality issues
- **Better Code**: Higher baseline quality
- **Knowledge Sharing**: Best practices documented
- **Reduced Bugs**: TDD + quality gates = fewer bugs

---

## Metrics to Track

### Per Work Type
```typescript
{
  workType: "NEW_FEATURE",
  totalExecutions: 45,
  qualityGateResults: {
    preImplementation: {
      passed: 38,
      failed: 7,
      blocked: 3  // Commits blocked
    },
    postImplementation: {
      passed: 42,
      warnings: 3,
      failed: 0
    }
  },
  averageQualityScore: {
    before: 68,
    after: 75  // Improvement!
  },
  tddCompliance: {
    testsFirstPercentage: 84,  // 84% wrote tests first
    coverageIncrease: 3.2      // Average +3.2% coverage per feature
  }
}
```

---

## Questions for Discussion

1. **Blocking vs Warning**: Welke checks moeten commits blokkeren vs alleen waarschuwen?

2. **Per Work Type Config**: Verschillende strictness levels per work type?
   - NEW_FEATURE: Strict TDD enforcement?
   - BUG: Require regression test?
   - ENHANCEMENT: Optional quality improvements?

3. **Developer Bypass**: Wanneer mag `--no-verify` gebruikt worden?
   - Emergency hotfixes?
   - WIP commits?
   - Never?

4. **Integration Timing**:
   - Week 10: Start met centralized service?
   - Week 11: Add to NEW_FEATURE + BUG?
   - Week 12: Pre-commit hooks?

---

## Recommendation

**Start Small, Iterate Fast**:

1. **Week 10**:
   - Create QualityGateService
   - Integrate with NEW_FEATURE (non-blocking warnings only)
   - Gather feedback

2. **Week 11**:
   - Based on feedback, adjust strictness
   - Add to BUG workflow
   - Implement pre-commit hooks (optional, developer choice)

3. **Week 12**:
   - Enable blocking for critical checks (TDD, coverage decrease)
   - Add to remaining work types
   - Document best practices

---

**Status**: 📋 PROPOSAL
**Next Step**: Decide on implementation approach + timeline
**Estimated Effort**: 3 weeks (Weeks 10-12)

