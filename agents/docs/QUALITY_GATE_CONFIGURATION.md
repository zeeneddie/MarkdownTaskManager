# QualityGateService Configuration Guide

## Overview

This guide covers all configuration options for the QualityGateService, including enabled checks, blocking rules, and severity thresholds.

**Version**: 1.0 (Week 11)
**Target Audience**: DevOps, Tech Leads, QA Engineers

---

## Table of Contents

1. [Configuration Structure](#configuration-structure)
2. [Enabled Checks](#enabled-checks)
3. [Blocking Rules](#blocking-rules)
4. [Severity Thresholds](#severity-thresholds)
5. [Workflow-Specific Configurations](#workflow-specific-configurations)
6. [Environment-Based Configurations](#environment-based-configurations)
7. [Runtime Configuration Updates](#runtime-configuration-updates)
8. [Best Practices](#best-practices)

---

## Configuration Structure

### Full Configuration Interface

```typescript
interface QualityGateConfig {
  enabledChecks: {
    sig: boolean;                 // SIG-TOP-10 (3 checks)
    solid: boolean;               // SOLID Principles (3 checks)
    grasp: boolean;               // GRASP Principles (2 checks)
    tdd: boolean;                 // TDD Compliance (3 checks)
    testingPatterns: boolean;     // Testing Patterns (6 checks)
    designPatterns: boolean;      // Design Patterns (5 checks)
    cleanCode: boolean;           // Clean Code (5 checks)
    lawOfDemeter: boolean;        // Law of Demeter (1 check)
  };
  blockingRules: {
    blockOnCritical: boolean;     // Block on any critical violation
    blockOnCoverageDecrease: boolean;  // Block if coverage decreases
    blockOnNoTests: boolean;      // Block if production code has no tests
    minimumScore?: number;        // Minimum overall score (0-100)
  };
  severityThresholds: {
    complexity: {
      low: number;                // <= low is OK
      medium: number;             // > low, <= medium is warning
      high: number;               // > medium, <= high is error
    };
    duplication: {
      low: number;                // <= low% is OK
      medium: number;             // > low%, <= medium% is warning
      high: number;               // > medium%, <= high% is error
    };
  };
}
```

### Default Configuration

```typescript
export const DEFAULT_QUALITY_CONFIG: QualityGateConfig = {
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
    blockOnNoTests: false,        // Warning only by default
    minimumScore: undefined       // No minimum by default
  },
  severityThresholds: {
    complexity: {
      low: 10,    // SIG guideline
      medium: 15,
      high: 20
    },
    duplication: {
      low: 3,     // SIG guideline: 3%
      medium: 5,
      high: 10
    }
  }
};
```

---

## Enabled Checks

### Overview

Control which best practice categories are checked. Each category can be independently enabled or disabled.

**Total Checks**: 28 across 8 categories

### Enable All Checks (Default)

```typescript
const service = new QualityGateService({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: true,
    testingPatterns: true,
    designPatterns: true,
    cleanCode: true,
    lawOfDemeter: true
  }
});
```

### Architecture Focus

Focus on design and architecture, skip testing:

```typescript
const architectureService = new QualityGateService({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: false,                // Skip TDD
    testingPatterns: false,    // Skip test patterns
    designPatterns: true,
    cleanCode: true,
    lawOfDemeter: true
  }
});
```

**Use Case**: Architecture reviews, design discussions

### Testing Focus

Focus on testing practices only:

```typescript
const testingService = new QualityGateService({
  enabledChecks: {
    sig: false,
    solid: false,
    grasp: false,
    tdd: true,                 // Check TDD compliance
    testingPatterns: true,     // Check test quality
    designPatterns: false,
    cleanCode: false,
    lawOfDemeter: false
  }
});
```

**Use Case**: QA reviews, test suite audits

### Code Quality Focus

Focus on clean code and maintainability:

```typescript
const cleanCodeService = new QualityGateService({
  enabledChecks: {
    sig: true,                 // Complexity, duplication
    solid: false,
    grasp: false,
    tdd: false,
    testingPatterns: false,
    designPatterns: false,
    cleanCode: true,           // YAGNI, KISS, magic numbers
    lawOfDemeter: true
  }
});
```

**Use Case**: Code reviews, refactoring sessions

### Minimal Checks (Fast)

Only essential checks for quick feedback:

```typescript
const minimalService = new QualityGateService({
  enabledChecks: {
    sig: true,                 // Core quality (3 checks)
    solid: true,               // Core design (3 checks)
    grasp: false,
    tdd: true,                 // Tests exist (3 checks)
    testingPatterns: false,
    designPatterns: false,
    cleanCode: false,
    lawOfDemeter: false
  }
});
```

**Use Case**: Local development, pre-commit hooks

---

## Blocking Rules

### Overview

Control when quality gate violations should **block** commits, PRs, or deployments.

### Block on Critical Only (Default)

```typescript
const service = new QualityGateService({
  blockingRules: {
    blockOnCritical: true,              // Block critical violations
    blockOnCoverageDecrease: true,      // Block if coverage drops
    blockOnNoTests: false,              // Warn, don't block
    minimumScore: undefined             // No minimum score
  }
});
```

**Severity Levels**:
- **Critical**: 2 findings (F.I.R.S.T Repeatable, Singleton Misuse)
- **High**: 7 findings (LSP, TDD, Strategy, Observer, KISS)
- **Medium**: 16 findings
- **Low**: 3 findings

### Strict Blocking

Block on any quality issue:

```typescript
const strictService = new QualityGateService({
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: true,               // Block if no tests
    minimumScore: 80                    // Block if score < 80%
  }
});
```

**Use Case**: Production deployments, release branches

### Lenient (Warnings Only)

Never block, only warn:

```typescript
const lenientService = new QualityGateService({
  blockingRules: {
    blockOnCritical: false,
    blockOnCoverageDecrease: false,
    blockOnNoTests: false,
    minimumScore: undefined
  }
});
```

**Use Case**: Early development, experimental branches

### Progressive Enforcement

Gradually increase strictness over time:

```typescript
// Week 1-2: Collect metrics, warnings only
const week1Config = {
  blockingRules: {
    blockOnCritical: false,
    blockOnCoverageDecrease: false,
    blockOnNoTests: false,
    minimumScore: undefined
  }
};

// Week 3-4: Block critical violations
const week3Config = {
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: false,
    blockOnNoTests: false,
    minimumScore: undefined
  }
};

// Week 5-6: Block coverage decrease
const week5Config = {
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: false,
    minimumScore: undefined
  }
};

// Week 7+: Require tests + minimum score
const week7Config = {
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: true,
    minimumScore: 70                    // Start with 70%
  }
};
```

**Use Case**: Rolling out quality gates to existing projects

---

## Severity Thresholds

### Overview

Define what constitutes low, medium, high severity for complexity and duplication violations.

### Default Thresholds (SIG Guidelines)

```typescript
const service = new QualityGateService({
  severityThresholds: {
    complexity: {
      low: 10,      // SIG guideline: cyclomatic complexity ≤ 10
      medium: 15,
      high: 20
    },
    duplication: {
      low: 3,       // SIG guideline: code duplication ≤ 3%
      medium: 5,
      high: 10
    }
  }
});
```

**Interpretation**:
- Complexity ≤ 10: ✅ OK (low)
- Complexity 11-15: ⚠️ Warning (medium)
- Complexity 16-20: ❌ Error (high)
- Complexity > 20: 🚨 Critical

### Strict Thresholds

Lower thresholds for high-quality codebases:

```typescript
const strictService = new QualityGateService({
  severityThresholds: {
    complexity: {
      low: 8,       // Stricter than SIG
      medium: 12,
      high: 15
    },
    duplication: {
      low: 2,       // Stricter than SIG
      medium: 4,
      high: 8
    }
  }
});
```

**Use Case**: Greenfield projects, high-quality teams

### Lenient Thresholds

Higher thresholds for legacy codebases:

```typescript
const lenientService = new QualityGateService({
  severityThresholds: {
    complexity: {
      low: 15,      // More lenient
      medium: 20,
      high: 30
    },
    duplication: {
      low: 5,       // More lenient
      medium: 10,
      high: 15
    }
  }
});
```

**Use Case**: Legacy codebases, gradual refactoring

---

## Workflow-Specific Configurations

### MAINTENANCE Workflow

Strict quality enforcement for maintenance work:

```typescript
const maintenanceConfig = {
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
    blockOnNoTests: false,
    minimumScore: 75                    // Require 75% for maintenance
  }
};
```

### NEW_FEATURE Workflow

Non-blocking for new features (Week 10-11 approach):

```typescript
const newFeatureConfig = {
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
    blockOnCritical: false,             // Warnings only
    blockOnCoverageDecrease: false,
    blockOnNoTests: false,
    minimumScore: undefined
  }
};
```

**Note**: In Week 12+, can increase to blocking for critical violations

### BUG Workflow

Strict blocking to ensure regression tests:

```typescript
const bugFixConfig = {
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: true,                          // CRITICAL: Check for regression test
    testingPatterns: true,
    designPatterns: false,              // Less important for bug fixes
    cleanCode: false,                   // Less important for bug fixes
    lawOfDemeter: true
  },
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: true,               // BLOCK if no regression test!
    minimumScore: undefined
  }
};
```

### ENHANCEMENT Workflow

Balanced approach for enhancements:

```typescript
const enhancementConfig = {
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
    blockOnNoTests: false,
    minimumScore: 70                    // Moderate requirement
  }
};
```

---

## Environment-Based Configurations

### Development Environment

Fast feedback, lenient rules:

```typescript
const devConfig = {
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: false,               // Disable slower checks
    tdd: true,
    testingPatterns: false,     // Disable slower checks
    designPatterns: false,      // Disable slower checks
    cleanCode: true,
    lawOfDemeter: false
  },
  blockingRules: {
    blockOnCritical: false,     // Warnings only
    blockOnCoverageDecrease: false,
    blockOnNoTests: false,
    minimumScore: undefined
  }
};
```

### CI/CD Pipeline

Comprehensive checks, strict enforcement:

```typescript
const ciConfig = {
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
    blockOnNoTests: true,
    minimumScore: 75            // CI requires 75%
  },
  severityThresholds: {
    complexity: { low: 10, medium: 15, high: 20 },
    duplication: { low: 3, medium: 5, high: 10 }
  }
};
```

### Production Deployment

Maximum strictness for production:

```typescript
const prodConfig = {
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
    blockOnNoTests: true,
    minimumScore: 85            // Production requires 85%
  },
  severityThresholds: {
    complexity: { low: 8, medium: 12, high: 15 },   // Stricter
    duplication: { low: 2, medium: 4, high: 8 }     // Stricter
  }
};
```

---

## Runtime Configuration Updates

### Get Current Configuration

```typescript
const service = new QualityGateService();
const config = service.getConfig();

console.log(`Current configuration:
  SIG enabled: ${config.enabledChecks.sig}
  Block on critical: ${config.blockingRules.blockOnCritical}
  Complexity threshold: ${config.severityThresholds.complexity.low}
`);
```

### Update Configuration at Runtime

```typescript
const service = new QualityGateService();

// Update blocking rules
service.updateConfig({
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: true,
    minimumScore: 80
  }
});

// Update enabled checks
service.updateConfig({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: false,       // Disable GRASP
    tdd: true,
    testingPatterns: true,
    designPatterns: true,
    cleanCode: true,
    lawOfDemeter: false // Disable LoD
  }
});

// Update severity thresholds
service.updateConfig({
  severityThresholds: {
    complexity: {
      low: 12,
      medium: 18,
      high: 25
    }
  }
});
```

---

## Best Practices

### 1. Start Lenient, Increase Gradually

```typescript
// Month 1: Warnings only, collect metrics
const month1Config = { blockingRules: { blockOnCritical: false, ... } };

// Month 2: Block critical
const month2Config = { blockingRules: { blockOnCritical: true, ... } };

// Month 3: Block critical + coverage
const month3Config = { blockingRules: { blockOnCritical: true, blockOnCoverageDecrease: true, ... } };

// Month 4: Full enforcement
const month4Config = { blockingRules: { blockOnCritical: true, blockOnCoverageDecrease: true, blockOnNoTests: true, minimumScore: 70 } };
```

### 2. Different Rules for Different Work Types

```typescript
// Bug fixes: Strict (require regression tests)
const bugService = new QualityGateService({ blockingRules: { blockOnNoTests: true } });

// New features: Moderate (warnings for new code)
const featureService = new QualityGateService({ blockingRules: { blockOnCritical: false } });

// Refactoring: Strict (improve quality)
const refactorService = new QualityGateService({ blockingRules: { minimumScore: 85 } });
```

### 3. Adjust Thresholds Based on Team Maturity

```typescript
// Junior team: Lenient thresholds
const juniorConfig = {
  severityThresholds: {
    complexity: { low: 15, medium: 20, high: 30 }
  }
};

// Senior team: Strict thresholds
const seniorConfig = {
  severityThresholds: {
    complexity: { low: 8, medium: 12, high: 15 }
  }
};
```

### 4. Enable Checks Incrementally

```typescript
// Week 1: Core checks only
const week1 = { enabledChecks: { sig: true, solid: true, tdd: true, ... (rest false) } };

// Week 2: Add testing patterns
const week2 = { enabledChecks: { sig: true, solid: true, tdd: true, testingPatterns: true, ... } };

// Week 3: Add design patterns
const week3 = { enabledChecks: { ..., designPatterns: true, ... } };

// Week 4: All checks
const week4 = { enabledChecks: { /* all true */ } };
```

### 5. Monitor Metrics Before Enforcing

```typescript
// Phase 1: Monitoring (1-2 weeks)
const monitoringService = new QualityGateService({
  blockingRules: { blockOnCritical: false, ... }  // Log only
});

const result = await monitoringService.checkPostImplementation({ scope: 'full_codebase' });

// Log to monitoring system
await logQualityMetrics({
  totalScore: result.bestPracticeScore.totalScore,
  violations: result.summary.totalViolations,
  criticalCount: result.summary.criticalViolations
});

// Phase 2: After reviewing metrics, enable blocking
const enforcingService = new QualityGateService({
  blockingRules: { blockOnCritical: true, ... }
});
```

---

## Configuration Examples by Scenario

### Scenario 1: Greenfield Project

```typescript
const greenfieldConfig = {
  enabledChecks: { /* all true */ },
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: true,
    minimumScore: 85              // High bar for new projects
  },
  severityThresholds: {
    complexity: { low: 8, medium: 12, high: 15 },
    duplication: { low: 2, medium: 4, high: 8 }
  }
};
```

### Scenario 2: Legacy Codebase

```typescript
const legacyConfig = {
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: false,               // Skip for now
    tdd: true,
    testingPatterns: false,     // Skip for now
    designPatterns: false,      // Skip for now
    cleanCode: true,
    lawOfDemeter: false
  },
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: false,  // Legacy may fluctuate
    blockOnNoTests: false,
    minimumScore: undefined     // No minimum initially
  },
  severityThresholds: {
    complexity: { low: 15, medium: 25, high: 40 },  // Lenient
    duplication: { low: 8, medium: 12, high: 20 }   // Lenient
  }
};
```

### Scenario 3: Open Source Project

```typescript
const openSourceConfig = {
  enabledChecks: { /* all true */ },
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: false,      // Contributors may not write tests
    minimumScore: 70            // Moderate bar
  },
  severityThresholds: {
    complexity: { low: 10, medium: 15, high: 20 },  // Standard SIG
    duplication: { low: 3, medium: 5, high: 10 }    // Standard SIG
  }
};
```

---

## Next Steps

- **Usage**: See [QUALITY_GATE_USAGE_GUIDE.md](./QUALITY_GATE_USAGE_GUIDE.md)
- **Extension**: See [QUALITY_GATE_EXTENSION.md](./QUALITY_GATE_EXTENSION.md)

---

**Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Production Ready
