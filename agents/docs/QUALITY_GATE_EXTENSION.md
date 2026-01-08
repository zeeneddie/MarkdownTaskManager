# QualityGateService Extension Guide

## Overview

This guide shows how to extend the QualityGateService with new best practice checks, custom quality rules, and integration with external tools.

**Version**: 1.0 (Week 11)
**Target Audience**: Developers, Tech Leads

---

## Table of Contents

1. [Adding a New Check Category](#adding-a-new-check-category)
2. [Adding Checks to Existing Categories](#adding-checks-to-existing-categories)
3. [Integrating External Tools](#integrating-external-tools)
4. [Custom Severity Levels](#custom-severity-levels)
5. [Adding New Workflows](#adding-new-workflows)
6. [Testing New Checks](#testing-new-checks)
7. [Best Practices](#best-practices)

---

## Adding a New Check Category

Let's add a **Security Patterns** category with 3 checks as an example.

### Step 1: Update BestPracticeScore Interface

**File**: `services/qualityGateService.ts`

```typescript
export interface BestPracticeScore {
  // ... existing categories ...

  // NEW: Security Patterns Compliance
  securityPatternsCompliance: {
    overall: number;  // 0-100%
    violations: {
      inputValidation: number;        // Missing input validation
      sqlInjection: number;           // SQL injection risks
      xssVulnerability: number;       // XSS vulnerabilities
    };
  };

  // ... rest of interface ...
}
```

### Step 2: Update QualityGateConfig Interface

```typescript
export interface QualityGateConfig {
  enabledChecks: {
    // ... existing checks ...
    securityPatterns: boolean;  // NEW: Security pattern checks
    // ... rest of checks ...
  };
  // ... rest of config ...
}
```

### Step 3: Update DEFAULT_QUALITY_CONFIG

```typescript
export const DEFAULT_QUALITY_CONFIG: QualityGateConfig = {
  enabledChecks: {
    // ... existing ...
    securityPatterns: true,  // NEW: Enable by default
    // ... rest ...
  },
  // ... rest of config ...
};
```

### Step 4: Implement Check Method

```typescript
/**
 * Check Security Patterns compliance
 * Input Validation, SQL Injection, XSS
 */
private async checkSecurityPatterns(context: QualityCheckContext): Promise<QualityFinding[]> {
  console.log('   Checking Security Patterns compliance...');

  // TODO: In production:
  // - Use ESLint security plugins (eslint-plugin-security)
  // - Use SonarQube security rules
  // - Use OWASP ZAP for dynamic analysis
  // - Parse AST for dangerous patterns

  const findings: QualityFinding[] = [];

  // Check 1: Input Validation
  findings.push({
    id: 'SEC-001',
    category: 'security',
    severity: 'critical',
    title: 'Missing Input Validation: User input not sanitized',
    description: 'createUser() accepts raw request.body without validation, allowing malicious input',
    location: 'src/user/UserController.ts:45',
    recommendation: 'Use Zod/Joi schema validation before processing user input',
    estimatedEffort: 2,
    riskIfNotFixed: 'high',
    autoFixable: false,
    bestPractice: 'Security Patterns: Input Validation'
  });

  // Check 2: SQL Injection
  findings.push({
    id: 'SEC-002',
    category: 'security',
    severity: 'critical',
    title: 'SQL Injection Risk: String concatenation in query',
    description: 'getUserById() builds SQL query with string concatenation instead of parameterized query',
    location: 'src/user/UserRepository.ts:78',
    recommendation: 'Use parameterized queries or ORM to prevent SQL injection',
    estimatedEffort: 1,
    riskIfNotFixed: 'high',
    autoFixable: false,
    bestPractice: 'Security Patterns: SQL Injection Prevention'
  });

  // Check 3: XSS Vulnerability
  findings.push({
    id: 'SEC-003',
    category: 'security',
    severity: 'high',
    title: 'XSS Vulnerability: Unescaped user input in template',
    description: 'UserProfile.tsx renders user.bio directly without escaping, allowing XSS attacks',
    location: 'src/components/UserProfile.tsx:123',
    recommendation: 'Use React automatic escaping or DOMPurify for HTML content',
    estimatedEffort: 1,
    riskIfNotFixed: 'high',
    autoFixable: true,
    bestPractice: 'Security Patterns: XSS Prevention'
  });

  return findings;
}
```

### Step 5: Call Check Method in checkPostImplementation

```typescript
async checkPostImplementation(context: QualityCheckContext): Promise<QualityGateResult> {
  // ... existing code ...

  // NEW: Security Patterns check
  if (this.config.enabledChecks.securityPatterns) {
    const securityFindings = await this.checkSecurityPatterns(context);
    findings.push(...securityFindings);
  }

  // ... rest of method ...
}
```

### Step 6: Update Scoring Logic

```typescript
private calculateBestPracticeScore(findings: QualityFinding[]): BestPracticeScore {
  // ... existing violation counting ...

  // NEW: Count security violations
  const securityPatternsViolations = {
    inputValidation: findings.filter(f => f.bestPractice?.includes('Security Patterns: Input Validation')).length,
    sqlInjection: findings.filter(f => f.bestPractice?.includes('Security Patterns: SQL Injection')).length,
    xssVulnerability: findings.filter(f => f.bestPractice?.includes('Security Patterns: XSS')).length
  };

  // ... existing compliance calculations ...

  // NEW: Calculate security compliance
  const securityTotal = Object.values(securityPatternsViolations).reduce((a, b) => a + b, 0);
  const securityCompliance = Math.max(0, 100 - (securityTotal * 15));  // Each violation reduces score by 15%

  // NEW: Add to enabled scores
  if (this.config.enabledChecks.securityPatterns) enabledScores.push(securityCompliance);

  // ... existing return ...
  return {
    // ... existing ...
    securityPatternsCompliance: {
      overall: securityCompliance,
      violations: securityPatternsViolations
    },
    // ... rest ...
  };
}
```

### Step 7: Update createEmptyBestPracticeScore

```typescript
private createEmptyBestPracticeScore(): BestPracticeScore {
  return {
    // ... existing ...
    securityPatternsCompliance: {
      overall: 100,
      violations: {
        inputValidation: 0,
        sqlInjection: 0,
        xssVulnerability: 0
      }
    },
    // ... rest ...
  };
}
```

### Step 8: TypeScript Compilation

```bash
$ npx tsc --noEmit
# ✅ 0 errors
```

### Step 9: Usage

```typescript
// Use new security checks
const service = new QualityGateService({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: true,
    testingPatterns: true,
    designPatterns: true,
    cleanCode: true,
    securityPatterns: true,  // NEW: Enable security checks
    lawOfDemeter: true
  }
});

const result = await service.checkPostImplementation({ scope: 'full_codebase' });

console.log(`Security Compliance: ${result.bestPracticeScore.securityPatternsCompliance.overall}%`);
console.log(`Security Violations:
  - Input Validation: ${result.bestPracticeScore.securityPatternsCompliance.violations.inputValidation}
  - SQL Injection: ${result.bestPracticeScore.securityPatternsCompliance.violations.sqlInjection}
  - XSS: ${result.bestPracticeScore.securityPatternsCompliance.violations.xssVulnerability}
`);
```

---

## Adding Checks to Existing Categories

Let's add a new check to the existing **Clean Code** category.

### Example: Add "Comment Quality" Check

**File**: `services/qualityGateService.ts`

#### Step 1: Update Interface

```typescript
cleanCodeCompliance: {
  overall: number;
  violations: {
    yagni: number;
    kiss: number;
    boyScoutRule: number;
    magicNumbers: number;
    meaningfulNames: number;
    commentQuality: number;  // NEW: Add comment quality
  };
};
```

#### Step 2: Update Check Method

```typescript
private async checkCleanCode(context: QualityCheckContext): Promise<QualityFinding[]> {
  const findings: QualityFinding[] = [];

  // ... existing checks ...

  // NEW: Comment Quality check
  findings.push({
    id: 'CLEAN-006',
    category: 'code_smell',
    severity: 'low',
    title: 'Comment Quality: Outdated or misleading comments',
    description: 'calculateDiscount() has comments that contradict the actual implementation',
    location: 'src/pricing/DiscountCalculator.ts:67',
    recommendation: 'Update comments to match code or remove if code is self-explanatory',
    estimatedEffort: 1,
    riskIfNotFixed: 'low',
    autoFixable: false,
    bestPractice: 'Clean Code: Comment Quality'
  });

  return findings;
}
```

#### Step 3: Update Scoring

```typescript
const cleanCodeViolations = {
  yagni: findings.filter(f => f.bestPractice?.includes('Clean Code: YAGNI')).length,
  kiss: findings.filter(f => f.bestPractice?.includes('Clean Code: KISS')).length,
  boyScoutRule: findings.filter(f => f.bestPractice?.includes('Clean Code: Boy Scout Rule')).length,
  magicNumbers: findings.filter(f => f.bestPractice?.includes('Clean Code: No Magic Numbers')).length,
  meaningfulNames: findings.filter(f => f.bestPractice?.includes('Clean Code: Meaningful Names')).length,
  commentQuality: findings.filter(f => f.bestPractice?.includes('Clean Code: Comment Quality')).length  // NEW
};
```

#### Step 4: Update Empty Score

```typescript
cleanCodeCompliance: {
  overall: 100,
  violations: {
    yagni: 0,
    kiss: 0,
    boyScoutRule: 0,
    magicNumbers: 0,
    meaningfulNames: 0,
    commentQuality: 0  // NEW
  }
}
```

---

## Integrating External Tools

### ESLint Integration

```typescript
import { ESLint } from 'eslint';

private async checkWithESLint(context: QualityCheckContext): Promise<QualityFinding[]> {
  const findings: QualityFinding[] = [];

  // Initialize ESLint
  const eslint = new ESLint({
    useEslintrc: true,
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  });

  // Get files to lint
  const files = context.targetFiles || await this.getFilesInScope(context);

  // Run ESLint
  const results = await eslint.lintFiles(files);

  // Convert ESLint results to QualityFinding[]
  for (const result of results) {
    for (const message of result.messages) {
      findings.push({
        id: `ESLINT-${message.ruleId}`,
        category: this.categorizeESLintMessage(message),
        severity: this.mapESLintSeverity(message.severity),
        title: `ESLint: ${message.message}`,
        description: `Rule ${message.ruleId} violated at line ${message.line}`,
        location: `${result.filePath}:${message.line}:${message.column}`,
        recommendation: message.message,
        estimatedEffort: 1,
        riskIfNotFixed: 'medium',
        autoFixable: message.fix !== undefined,
        bestPractice: `ESLint: ${message.ruleId}`
      });
    }
  }

  return findings;
}

private mapESLintSeverity(eslintSeverity: number): 'critical' | 'high' | 'medium' | 'low' {
  return eslintSeverity === 2 ? 'high' : 'medium';
}

private categorizeESLintMessage(message: any): QualityFinding['category'] {
  if (message.ruleId?.includes('security')) return 'security';
  if (message.ruleId?.includes('performance')) return 'performance';
  return 'code_smell';
}
```

### SonarQube Integration

```typescript
import axios from 'axios';

private async checkWithSonarQube(context: QualityCheckContext): Promise<QualityFinding[]> {
  const findings: QualityFinding[] = [];

  // SonarQube API endpoint
  const sonarUrl = process.env.SONAR_URL || 'http://localhost:9000';
  const projectKey = process.env.SONAR_PROJECT_KEY;

  try {
    // Fetch issues from SonarQube
    const response = await axios.get(`${sonarUrl}/api/issues/search`, {
      params: {
        componentKeys: projectKey,
        resolved: false,
        types: 'CODE_SMELL,BUG,VULNERABILITY'
      },
      auth: {
        username: process.env.SONAR_TOKEN,
        password: ''
      }
    });

    // Convert SonarQube issues to QualityFinding[]
    for (const issue of response.data.issues) {
      findings.push({
        id: `SONAR-${issue.key}`,
        category: this.categorizeSonarIssue(issue.type),
        severity: this.mapSonarSeverity(issue.severity),
        title: `SonarQube: ${issue.message}`,
        description: issue.message,
        location: `${issue.component}:${issue.line}`,
        recommendation: issue.message,
        estimatedEffort: this.estimateFromDebt(issue.debt),
        riskIfNotFixed: this.mapSonarSeverity(issue.severity),
        autoFixable: false,
        bestPractice: `SonarQube: ${issue.rule}`
      });
    }
  } catch (error) {
    console.error('SonarQube integration error:', error);
  }

  return findings;
}

private mapSonarSeverity(severity: string): 'critical' | 'high' | 'medium' | 'low' {
  const map = {
    'BLOCKER': 'critical',
    'CRITICAL': 'critical',
    'MAJOR': 'high',
    'MINOR': 'medium',
    'INFO': 'low'
  };
  return map[severity] || 'medium';
}
```

### Git History Analysis

```typescript
import simpleGit from 'simple-git';

private async checkGitHistory(context: QualityCheckContext): Promise<QualityFinding[]> {
  const findings: QualityFinding[] = [];
  const git = simpleGit();

  // Get recent commits for target files
  const files = context.targetFiles || [];

  for (const file of files) {
    const log = await git.log({ file, maxCount: 10 });

    // Check for Boy Scout Rule violations
    const commits = log.all;
    if (commits.length >= 2) {
      const recentCommits = commits.slice(0, 5);
      const hasRefactoring = recentCommits.some(c =>
        c.message.toLowerCase().includes('refactor') ||
        c.message.toLowerCase().includes('clean')
      );

      if (!hasRefactoring && recentCommits.length >= 3) {
        findings.push({
          id: 'GIT-001',
          category: 'code_smell',
          severity: 'medium',
          title: 'Boy Scout Rule: No refactoring in recent commits',
          description: `${file} has been modified ${recentCommits.length} times without refactoring`,
          location: file,
          recommendation: 'Follow Boy Scout Rule: leave code cleaner than you found it',
          estimatedEffort: 3,
          riskIfNotFixed: 'medium',
          autoFixable: false,
          bestPractice: 'Clean Code: Boy Scout Rule'
        });
      }
    }
  }

  return findings;
}
```

---

## Custom Severity Levels

### Adding Custom Severity Thresholds

```typescript
export interface QualityGateConfig {
  // ... existing ...

  severityThresholds: {
    complexity: {
      low: number;
      medium: number;
      high: number;
    };
    duplication: {
      low: number;
      medium: number;
      high: number;
    };
    // NEW: Custom thresholds
    testCoverage: {
      low: number;      // < 60% coverage
      medium: number;   // 60-80% coverage
      high: number;     // > 80% coverage
    };
    technicalDebt: {
      low: number;      // < 5% debt ratio
      medium: number;   // 5-10% debt ratio
      high: number;     // > 10% debt ratio
    };
  };
}
```

### Using Custom Thresholds

```typescript
private async checkTestCoverage(context: QualityCheckContext): Promise<QualityFinding[]> {
  const findings: QualityFinding[] = [];

  // Get coverage from context or tool
  const coverage = await this.getCoveragePercentage(context);
  const thresholds = this.config.severityThresholds.testCoverage;

  let severity: 'critical' | 'high' | 'medium' | 'low';
  if (coverage < thresholds.low) {
    severity = 'critical';
  } else if (coverage < thresholds.medium) {
    severity = 'high';
  } else if (coverage < thresholds.high) {
    severity = 'medium';
  } else {
    return findings;  // Coverage is good
  }

  findings.push({
    id: 'COV-001',
    category: 'test',
    severity,
    title: `Test Coverage Below Threshold: ${coverage}%`,
    description: `Current coverage ${coverage}% is below target ${thresholds.high}%`,
    location: 'Overall codebase',
    recommendation: `Increase test coverage to at least ${thresholds.high}%`,
    estimatedEffort: 8,
    riskIfNotFixed: 'high',
    autoFixable: false,
    bestPractice: 'TDD: Adequate Test Coverage'
  });

  return findings;
}
```

---

## Adding New Workflows

### ENHANCEMENT Workflow Example

**File**: `workflows/enhancementWorkflow.ts`

```typescript
import QualityGateService from '../services/qualityGateService';

export interface EnhancementRequest {
  description: string;
  targetFiles?: string[];
  modulePath?: string;
  userStoryPoints: number;
}

export async function executeEnhancementWorkflow(request: EnhancementRequest) {
  // Balanced configuration for enhancements
  const qualityGateService = new QualityGateService({
    enabledChecks: {
      sig: true,
      solid: true,
      grasp: true,
      tdd: true,
      testingPatterns: true,
      designPatterns: true,
      cleanCode: true,
      lawOfDemeter: true
    },
    blockingRules: {
      blockOnCritical: true,
      blockOnCoverageDecrease: true,
      blockOnNoTests: false,           // Warn, don't block
      minimumScore: 70                 // Moderate requirement
    }
  });

  // Pre-check
  const preChecks = await qualityGateService.checkPreImplementation({
    scope: request.modulePath ? 'module' : 'specific_files',
    targetFiles: request.targetFiles,
    modulePath: request.modulePath
  });

  // ... implement enhancement ...

  // Post-check
  const postChecks = await qualityGateService.checkPostImplementation({
    scope: request.modulePath ? 'module' : 'specific_files',
    targetFiles: request.targetFiles,
    modulePath: request.modulePath
  });

  if (postChecks.blocking) {
    throw new Error('ENHANCEMENT: Quality gates blocked - fix violations');
  }

  return {
    qualityGates: {
      pre: preChecks,
      post: postChecks,
      overallScore: (preChecks.bestPracticeScore.totalScore + postChecks.bestPracticeScore.totalScore) / 2,
      blocking: postChecks.blocking
    }
  };
}
```

---

## Testing New Checks

### Unit Test Example

**File**: `tests/qualityGateService.test.ts`

```typescript
import { QualityGateService } from '../services/qualityGateService';

describe('QualityGateService - Security Patterns', () => {
  it('should detect input validation violations', async () => {
    const service = new QualityGateService({
      enabledChecks: {
        sig: false,
        solid: false,
        grasp: false,
        tdd: false,
        testingPatterns: false,
        designPatterns: false,
        cleanCode: false,
        securityPatterns: true,  // Only security checks
        lawOfDemeter: false
      }
    });

    const result = await service.checkPostImplementation({
      scope: 'full_codebase'
    });

    // Assert findings
    expect(result.findings.length).toBeGreaterThan(0);
    expect(result.findings.some(f => f.id === 'SEC-001')).toBe(true);

    // Assert scoring
    expect(result.bestPracticeScore.securityPatternsCompliance.overall).toBeDefined();
    expect(result.bestPracticeScore.securityPatternsCompliance.violations.inputValidation).toBeGreaterThan(0);
  });

  it('should respect configuration', async () => {
    const service = new QualityGateService({
      enabledChecks: {
        securityPatterns: false  // Disabled
      }
    });

    const result = await service.checkPostImplementation({
      scope: 'full_codebase'
    });

    // No security findings when disabled
    expect(result.findings.filter(f => f.id.startsWith('SEC-'))).toHaveLength(0);
  });
});
```

### Integration Test Example

```typescript
describe('QualityGateService - Full Integration', () => {
  it('should run all 31 checks (28 + 3 security)', async () => {
    const service = new QualityGateService();  // All enabled

    const result = await service.checkPostImplementation({
      scope: 'full_codebase'
    });

    // 28 existing + 3 security = 31 total findings
    expect(result.findings.length).toBe(31);
    expect(result.bestPracticeScore.totalScore).toBeDefined();
  });
});
```

---

## Best Practices

### 1. Consistent ID Scheme

```typescript
// Category-NNN format
'SIG-001', 'SIG-002', 'SIG-003'
'SOLID-001', 'SOLID-002', 'SOLID-003'
'DESIGN-001', 'DESIGN-002', 'DESIGN-003'
'CLEAN-001', 'CLEAN-002', 'CLEAN-003'
'SEC-001', 'SEC-002', 'SEC-003'  // NEW
```

### 2. Clear Best Practice Strings

```typescript
// Use consistent format for filtering
'Design Patterns: Factory Pattern'
'Design Patterns: Strategy Pattern'
'Security Patterns: Input Validation'  // NEW
'Security Patterns: SQL Injection Prevention'  // NEW
```

### 3. Meaningful Effort Estimates

```typescript
// Story points based on actual effort
estimatedEffort: 1  // < 2 hours
estimatedEffort: 2  // 2-4 hours
estimatedEffort: 3  // 4-8 hours (half day)
estimatedEffort: 5  // 1-2 days
estimatedEffort: 8  // 3-5 days (full week)
```

### 4. Risk Assessment

```typescript
// Be realistic about risk
riskIfNotFixed: 'low'     // Minor inconvenience
riskIfNotFixed: 'medium'  // Could cause issues
riskIfNotFixed: 'high'    // Will cause issues
```

### 5. Auto-Fixable Flag

```typescript
// Only mark as auto-fixable if truly safe
autoFixable: true   // e.g., adding missing semicolons
autoFixable: false  // e.g., refactoring to Strategy pattern
```

---

## Complete Example: Performance Patterns

Here's a complete example adding a new **Performance Patterns** category:

```typescript
// 1. Update interface
performancePatternsCompliance: {
  overall: number;
  violations: {
    nPlusOneQuery: number;
    missingCaching: number;
    inefficientLoop: number;
  };
};

// 2. Update config
enabledChecks: {
  // ... existing ...
  performancePatterns: boolean;
};

// 3. Update default
performancePatterns: true,

// 4. Implement check
private async checkPerformancePatterns(context: QualityCheckContext): Promise<QualityFinding[]> {
  const findings: QualityFinding[] = [];

  findings.push({
    id: 'PERF-001',
    category: 'performance',
    severity: 'high',
    title: 'N+1 Query: Multiple database queries in loop',
    description: 'getUserOrders() executes N+1 queries instead of single JOIN',
    location: 'src/order/OrderService.ts:145',
    recommendation: 'Use JOIN query or DataLoader pattern to batch queries',
    estimatedEffort: 3,
    riskIfNotFixed: 'high',
    autoFixable: false,
    bestPractice: 'Performance Patterns: N+1 Query Prevention'
  });

  return findings;
}

// 5. Call in checkPostImplementation
if (this.config.enabledChecks.performancePatterns) {
  const perfFindings = await this.checkPerformancePatterns(context);
  findings.push(...perfFindings);
}

// 6. Update scoring
const performancePatternsViolations = {
  nPlusOneQuery: findings.filter(f => f.bestPractice?.includes('Performance Patterns: N+1')).length,
  missingCaching: findings.filter(f => f.bestPractice?.includes('Performance Patterns: Caching')).length,
  inefficientLoop: findings.filter(f => f.bestPractice?.includes('Performance Patterns: Loop')).length
};

const performanceTotal = Object.values(performancePatternsViolations).reduce((a, b) => a + b, 0);
const performanceCompliance = Math.max(0, 100 - (performanceTotal * 12));

if (this.config.enabledChecks.performancePatterns) enabledScores.push(performanceCompliance);

// 7. Return in score
performancePatternsCompliance: {
  overall: performanceCompliance,
  violations: performancePatternsViolations
}

// 8. Update empty score
performancePatternsCompliance: {
  overall: 100,
  violations: {
    nPlusOneQuery: 0,
    missingCaching: 0,
    inefficientLoop: 0
  }
}
```

---

## Next Steps

After adding new checks:

1. ✅ Update TypeScript interfaces
2. ✅ Implement check method
3. ✅ Update configuration
4. ✅ Update scoring logic
5. ✅ Write unit tests
6. ✅ Write integration tests
7. ✅ Update documentation
8. ✅ TypeScript compile (`npx tsc --noEmit`)
9. ✅ Run tests (`npm test`)
10. ✅ Update CHANGELOG

---

## Additional Resources

- **Usage**: [QUALITY_GATE_USAGE_GUIDE.md](./QUALITY_GATE_USAGE_GUIDE.md)
- **Configuration**: [QUALITY_GATE_CONFIGURATION.md](./QUALITY_GATE_CONFIGURATION.md)
- **Week 10 Summary**: [WEEK_10_COMPLETE_SUMMARY.md](./WEEK_10_COMPLETE_SUMMARY.md)
- **Week 11 Summary**: [WEEK_11_COMPLETE_SUMMARY.md](./WEEK_11_COMPLETE_SUMMARY.md)

---

**Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Production Ready
