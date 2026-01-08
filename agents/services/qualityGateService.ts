/**
 * QualityGateService
 *
 * Centralized service for quality gate checks across all work types.
 * Supports SIG-TOP-10, SOLID, GRASP, TDD, Law of Demeter, and future best practices.
 *
 * Week 10 - Quality Gates Integration
 * Week 6 Day 3 - SuperClaude Integration (20+ additional checks)
 * Used by: MAINTENANCE, NEW_FEATURE, BUG, ENHANCEMENT, TESTING workflows
 */

import { getSuperClaudeAnalyzer, SuperClaudeAnalyzeOptions } from '../integrations/superclaudeAnalyzer';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

/**
 * Context provided to quality gate checks
 */
export interface QualityCheckContext {
  // File/code scope
  scope: 'full_codebase' | 'module' | 'specific_files';
  targetFiles?: string[];
  modulePath?: string;

  // Code content (optional - for pre-implementation checks)
  codeContent?: string;
  language?: 'typescript' | 'javascript' | 'python' | 'java' | 'csharp';

  // Git context (for TDD checks)
  commitHash?: string;
  branchName?: string;

  // Thresholds
  thresholds?: {
    maxComplexity?: number;           // Default: 10 (SIG) or 15 (general)
    minTestCoverage?: number;         // Default: 80%
    maxTechnicalDebtRatio?: number;   // Default: 10%
    maxDuplication?: number;          // Default: 3% (SIG)
  };
}

/**
 * Result from quality gate checks
 */
export interface QualityGateResult {
  // Overall status
  passed: boolean;  // True if all checks pass
  blocking: boolean;  // True if violations should block commit/PR

  // Best practice compliance scores
  bestPracticeScore: BestPracticeScore;

  // Detailed findings
  findings: QualityFinding[];

  // Summary statistics
  summary: {
    totalViolations: number;
    criticalViolations: number;
    highViolations: number;
    mediumViolations: number;
    lowViolations: number;
  };

  // Execution metadata
  metadata: {
    executionTime: number;
    timestamp: Date;
    scope: string;
  };
}

/**
 * Best Practice Compliance Scores
 */
export interface BestPracticeScore {
  // SIG-TOP-10 Compliance
  sigCompliance: {
    overall: number;  // 0-100%
    violations: {
      shortUnits: number;         // SIG #1
      simpleUnits: number;        // SIG #2
      writeOnce: number;          // SIG #3
      smallInterfaces: number;    // SIG #4
      separateConcerns: number;   // SIG #5
      looseCoupling: number;      // SIG #6
      balancedComponents: number; // SIG #7
      smallCodebase: number;      // SIG #8
      automatedPipeline: number;  // SIG #9
      cleanCode: number;          // SIG #10
    };
  };

  // SOLID Principles Compliance
  solidCompliance: {
    overall: number;  // 0-100%
    violations: {
      srp: number;  // Single Responsibility
      ocp: number;  // Open/Closed
      lsp: number;  // Liskov Substitution
      isp: number;  // Interface Segregation
      dip: number;  // Dependency Inversion
    };
  };

  // GRASP Principles Compliance
  graspCompliance: {
    overall: number;  // 0-100%
    violations: {
      informationExpert: number;
      lowCoupling: number;
      highCohesion: number;
    };
  };

  // TDD Compliance
  tddCompliance: {
    overall: number;  // 0-100%
    violations: {
      noTests: number;
      testAfterCode: number;
      coverageDecrease: number;
    };
  };

  // Testing Patterns Compliance (Week 10 Day 5)
  testingPatternsCompliance: {
    overall: number;  // 0-100%
    violations: {
      aaaPattern: number;          // Arrange-Act-Assert structure
      firstPrinciples: number;     // Fast, Independent, Repeatable, Self-Validating, Timely
      testPyramid: number;         // Unit > Integration > E2E ratio
      givenWhenThen: number;       // BDD structure
    };
  };

  // Design Patterns Compliance (Week 11 Day 1-2)
  designPatternsCompliance: {
    overall: number;  // 0-100%
    violations: {
      factoryPattern: number;      // Factory pattern violation (tight coupling)
      builderPattern: number;      // Builder pattern missing (complex constructors)
      strategyPattern: number;     // Strategy pattern missing (switch/if-else chains)
      observerPattern: number;     // Observer pattern missing (polling instead of events)
      singletonPattern: number;    // Singleton pattern misuse (global state)
    };
  };

  // Clean Code Compliance (Week 11 Day 3-4)
  cleanCodeCompliance: {
    overall: number;  // 0-100%
    violations: {
      yagni: number;                // YAGNI - Unused code
      kiss: number;                 // KISS - Over-engineering
      boyScoutRule: number;         // Leave code cleaner than you found it
      magicNumbers: number;         // Magic numbers - use named constants
      meaningfulNames: number;      // Meaningful variable/function names
    };
  };

  // Law of Demeter
  lawOfDemeter: {
    violations: number;
  };

  // Combined score
  totalScore: number;  // 0-100%
}

/**
 * Individual quality finding/violation
 */
export interface QualityFinding {
  id: string;
  category: 'dependency' | 'code_smell' | 'security' | 'performance' | 'test' | 'documentation';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  location: string;
  recommendation: string;
  estimatedEffort: number;  // Story points
  riskIfNotFixed: 'high' | 'medium' | 'low';
  autoFixable: boolean;
  bestPractice?: string;  // e.g., "SIG-TOP-10 #2" or "SOLID: SRP"
}

/**
 * Configuration for quality gate behavior
 */
export interface QualityGateConfig {
  // Which best practices to check
  enabledChecks: {
    sig: boolean;
    solid: boolean;
    grasp: boolean;
    tdd: boolean;
    testingPatterns: boolean;  // Week 10 Day 5: AAA, F.I.R.S.T, Test Pyramid, BDD
    designPatterns: boolean;   // Week 11 Day 1-2: Factory, Builder, Strategy, Observer, Singleton
    cleanCode: boolean;        // Week 11 Day 3-4: YAGNI, KISS, Boy Scout Rule, Magic Numbers, Meaningful Names
    lawOfDemeter: boolean;
    superclaude: boolean;      // Week 6 Day 3: SuperClaude /sc:analyze integration (20+ additional checks)
  };

  // Blocking behavior
  blockingRules: {
    blockOnCritical: boolean;    // Block on any critical violation
    blockOnCoverageDecrease: boolean;  // Block if coverage decreases
    blockOnNoTests: boolean;     // Block if production code has no tests
    minimumScore?: number;       // Minimum overall score to pass (0-100)
  };

  // Severity thresholds
  severityThresholds: {
    complexity: {
      low: number;      // <= low is OK
      medium: number;   // > low, <= medium is warning
      high: number;     // > medium, <= high is error
      // > high is critical
    };
    duplication: {
      low: number;      // <= 3% is OK (SIG guideline)
      medium: number;
      high: number;
    };
  };
}

// ============================================================================
// DEFAULT CONFIGURATION
// ============================================================================

export const DEFAULT_QUALITY_CONFIG: QualityGateConfig = {
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: true,
    testingPatterns: true,  // Week 10 Day 5
    designPatterns: true,   // Week 11 Day 1-2
    cleanCode: true,        // Week 11 Day 3-4
    lawOfDemeter: true,
    superclaude: true       // Week 6 Day 3: SuperClaude integration
  },
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: false,  // Warning only by default
    minimumScore: undefined  // No minimum by default
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

// ============================================================================
// QUALITY GATE SERVICE
// ============================================================================

export class QualityGateService {
  private config: QualityGateConfig;

  constructor(config: Partial<QualityGateConfig> = {}) {
    // Merge provided config with defaults
    this.config = {
      ...DEFAULT_QUALITY_CONFIG,
      ...config,
      enabledChecks: {
        ...DEFAULT_QUALITY_CONFIG.enabledChecks,
        ...config.enabledChecks
      },
      blockingRules: {
        ...DEFAULT_QUALITY_CONFIG.blockingRules,
        ...config.blockingRules
      },
      severityThresholds: {
        ...DEFAULT_QUALITY_CONFIG.severityThresholds,
        ...config.severityThresholds
      }
    };
  }

  // ==========================================================================
  // MAIN CHECK METHODS
  // ==========================================================================

  /**
   * Pre-implementation quality check
   * Run BEFORE code is written (e.g., during planning)
   */
  async checkPreImplementation(context: QualityCheckContext): Promise<QualityGateResult> {
    console.log('\n🔍 Quality Gate: Pre-Implementation Check');

    const startTime = Date.now();
    const findings: QualityFinding[] = [];

    // Pre-implementation checks are lighter - mostly architectural
    // TODO: In production, analyze existing code patterns to predict issues

    const bestPracticeScore = this.createEmptyBestPracticeScore();

    const result: QualityGateResult = {
      passed: true,
      blocking: false,
      bestPracticeScore,
      findings,
      summary: {
        totalViolations: 0,
        criticalViolations: 0,
        highViolations: 0,
        mediumViolations: 0,
        lowViolations: 0
      },
      metadata: {
        executionTime: Date.now() - startTime,
        timestamp: new Date(),
        scope: context.scope
      }
    };

    console.log(`   ✓ Pre-implementation check complete (${result.metadata.executionTime}ms)`);

    return result;
  }

  /**
   * Post-implementation quality check
   * Run AFTER code is written (e.g., before commit/PR)
   */
  async checkPostImplementation(context: QualityCheckContext): Promise<QualityGateResult> {
    console.log('\n🔍 Quality Gate: Post-Implementation Check');

    const startTime = Date.now();
    const findings: QualityFinding[] = [];

    // Run enabled checks
    if (this.config.enabledChecks.sig) {
      const sigFindings = await this.checkSigCompliance(context);
      findings.push(...sigFindings);
    }

    if (this.config.enabledChecks.solid) {
      const solidFindings = await this.checkSolidCompliance(context);
      findings.push(...solidFindings);
    }

    if (this.config.enabledChecks.grasp) {
      const graspFindings = await this.checkGraspCompliance(context);
      findings.push(...graspFindings);
    }

    if (this.config.enabledChecks.tdd) {
      const tddFindings = await this.checkTddCompliance(context);
      findings.push(...tddFindings);
    }

    if (this.config.enabledChecks.testingPatterns) {
      const testingPatternsFindings = await this.checkTestingPatterns(context);
      findings.push(...testingPatternsFindings);
    }

    if (this.config.enabledChecks.designPatterns) {
      const designPatternsFindings = await this.checkDesignPatterns(context);
      findings.push(...designPatternsFindings);
    }

    if (this.config.enabledChecks.cleanCode) {
      const cleanCodeFindings = await this.checkCleanCode(context);
      findings.push(...cleanCodeFindings);
    }

    if (this.config.enabledChecks.lawOfDemeter) {
      const lodFindings = await this.checkLawOfDemeter(context);
      findings.push(...lodFindings);
    }

    if (this.config.enabledChecks.superclaude) {
      const superclaudeFindings = await this.checkSuperClaude(context);
      findings.push(...superclaudeFindings);
    }

    // Calculate best practice score
    const bestPracticeScore = this.calculateBestPracticeScore(findings);

    // Calculate summary
    const summary = {
      totalViolations: findings.length,
      criticalViolations: findings.filter(f => f.severity === 'critical').length,
      highViolations: findings.filter(f => f.severity === 'high').length,
      mediumViolations: findings.filter(f => f.severity === 'medium').length,
      lowViolations: findings.filter(f => f.severity === 'low').length
    };

    // Determine if checks passed
    const passed = this.determineIfPassed(findings, bestPracticeScore);
    const blocking = this.determineIfBlocking(findings, bestPracticeScore);

    const result: QualityGateResult = {
      passed,
      blocking,
      bestPracticeScore,
      findings,
      summary,
      metadata: {
        executionTime: Date.now() - startTime,
        timestamp: new Date(),
        scope: context.scope
      }
    };

    console.log(`   ✓ Post-implementation check complete`);
    console.log(`   ✓ Best Practice Score: ${bestPracticeScore.totalScore}%`);
    console.log(`   ✓ Total Violations: ${summary.totalViolations}`);
    console.log(`   ✓ Status: ${passed ? '✅ PASSED' : '❌ FAILED'}${blocking ? ' (BLOCKING)' : ''}`);

    return result;
  }

  // ==========================================================================
  // BEST PRACTICE CHECKS
  // ==========================================================================

  /**
   * Check SIG-TOP-10 compliance
   */
  private async checkSigCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking SIG-TOP-10 compliance...');

    // TODO: In production, use actual static analysis tools:
    // - ESLint with complexity rules
    // - SonarQube
    // - jscpd for duplication detection
    // - ts-complex for TypeScript complexity

    // For now, return mock findings based on typical violations
    const findings: QualityFinding[] = [];

    // SIG #2: Write Simple Units (Cyclomatic Complexity)
    findings.push({
      id: 'SIG-001',
      category: 'code_smell',
      severity: 'medium',
      title: 'SIG #2 Violation: High cyclomatic complexity in validateUserInput()',
      description: 'Function has complexity of 18, exceeding SIG guideline threshold of 10',
      location: 'src/validators/userInput.ts:28-95',
      recommendation: 'Refactor using strategy pattern to reduce complexity to ≤10',
      estimatedEffort: 3,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'SIG-TOP-10 #2: Write Simple Units of Code'
    });

    // SIG #3: Write Code Once (DRY)
    findings.push({
      id: 'SIG-002',
      category: 'code_smell',
      severity: 'medium',
      title: 'SIG #3 Violation: Code duplication in payment processors',
      description: '12% code duplication detected across PayPalProcessor and StripeProcessor, exceeding SIG threshold of 3%',
      location: 'src/payment/processors/',
      recommendation: 'Extract common payment logic into BasePaymentProcessor class',
      estimatedEffort: 4,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'SIG-TOP-10 #3: Write Code Once (DRY)'
    });

    // SIG #4: Keep Unit Interfaces Small
    findings.push({
      id: 'SIG-003',
      category: 'code_smell',
      severity: 'low',
      title: 'SIG #4 Violation: Too many parameters in createUser()',
      description: 'Function has 7 parameters, exceeding SIG guideline maximum of 4',
      location: 'src/user/UserService.ts:42',
      recommendation: 'Apply Parameter Object refactoring to group related parameters',
      estimatedEffort: 2,
      riskIfNotFixed: 'low',
      autoFixable: false,
      bestPractice: 'SIG-TOP-10 #4: Keep Unit Interfaces Small'
    });

    return findings;
  }

  /**
   * Check SOLID principles compliance
   */
  private async checkSolidCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking SOLID compliance...');

    // TODO: In production, use:
    // - SonarQube SOLID rules
    // - Manual code review patterns
    // - Class dependency analysis

    const findings: QualityFinding[] = [];

    // SOLID SRP: Single Responsibility Principle
    findings.push({
      id: 'SOLID-001',
      category: 'code_smell',
      severity: 'medium',
      title: 'SOLID SRP Violation: UserManager has multiple responsibilities',
      description: 'UserManager class mixes data access (database queries), business logic (validation), and presentation (rendering) concerns',
      location: 'src/user/UserManager.ts',
      recommendation: 'Split into UserRepository (data), UserService (logic), and UserView (presentation)',
      estimatedEffort: 5,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'SOLID: Single Responsibility Principle'
    });

    // SOLID OCP: Open/Closed Principle
    findings.push({
      id: 'SOLID-002',
      category: 'code_smell',
      severity: 'medium',
      title: 'SOLID OCP Violation: Payment type switch statement',
      description: 'PaymentProcessor uses large switch statement on payment type, requiring modification for each new payment method',
      location: 'src/payment/PaymentProcessor.ts:15-87',
      recommendation: 'Refactor to Strategy pattern with PaymentMethod interface',
      estimatedEffort: 4,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'SOLID: Open/Closed Principle'
    });

    // SOLID LSP: Liskov Substitution Principle
    findings.push({
      id: 'SOLID-003',
      category: 'code_smell',
      severity: 'high',
      title: 'SOLID LSP Violation: Square breaks Rectangle contract',
      description: 'Square class overrides Rectangle setters in a way that violates Liskov Substitution Principle',
      location: 'src/geometry/Square.ts:12-18',
      recommendation: 'Use composition instead of inheritance, or introduce Shape interface',
      estimatedEffort: 3,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'SOLID: Liskov Substitution Principle'
    });

    return findings;
  }

  /**
   * Check GRASP principles compliance
   */
  private async checkGraspCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking GRASP compliance...');

    // TODO: Analyze responsibility assignment, coupling, cohesion

    const findings: QualityFinding[] = [];

    // GRASP: Information Expert
    findings.push({
      id: 'GRASP-001',
      category: 'code_smell',
      severity: 'medium',
      title: 'GRASP Information Expert Violation: Customer calculating order totals',
      description: 'Customer class has calculateOrderTotal() method, but Order has the information needed',
      location: 'src/customer/Customer.ts:45',
      recommendation: 'Move calculation to Order class (Information Expert principle)',
      estimatedEffort: 2,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'GRASP: Information Expert'
    });

    // GRASP: High Cohesion
    findings.push({
      id: 'GRASP-002',
      category: 'code_smell',
      severity: 'medium',
      title: 'GRASP High Cohesion Violation: UserService has unrelated methods',
      description: 'UserService contains user CRUD, email sending, and report generation (unrelated responsibilities)',
      location: 'src/user/UserService.ts',
      recommendation: 'Split into UserRepository, EmailService, and ReportService',
      estimatedEffort: 4,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'GRASP: High Cohesion'
    });

    return findings;
  }

  /**
   * Check TDD compliance
   */
  private async checkTddCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking TDD compliance...');

    // TODO: In production:
    // - Check if test files exist for production files
    // - Analyze git history to detect tests-after-code
    // - Compare coverage between commits

    const findings: QualityFinding[] = [];

    // TDD: Production code without tests
    findings.push({
      id: 'TDD-001',
      category: 'test',
      severity: 'high',
      title: 'TDD Violation: Production code without tests',
      description: 'PaymentProcessor.ts has 8 public methods but no corresponding test file exists',
      location: 'src/payment/PaymentProcessor.ts',
      recommendation: 'Create PaymentProcessor.test.ts with tests for all public methods',
      estimatedEffort: 4,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'TDD: Test-Driven Development'
    });

    // TDD: Tests written after production code
    findings.push({
      id: 'TDD-002',
      category: 'test',
      severity: 'medium',
      title: 'TDD Violation: Tests written after production code',
      description: 'Git history shows UserAuthentication feature was committed without tests, tests added 2 weeks later',
      location: 'src/auth/UserAuthentication.ts',
      recommendation: 'Follow Red-Green-Refactor cycle: write tests first, then implementation',
      estimatedEffort: 0,  // Already implemented, just document practice
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'TDD: Red-Green-Refactor Cycle'
    });

    // TDD: Coverage decreased
    findings.push({
      id: 'TDD-003',
      category: 'test',
      severity: 'high',
      title: 'TDD Violation: Coverage decreased in recent commit',
      description: 'Commit a1b2c3d added new features but decreased test coverage from 82% to 78%',
      location: 'Multiple files',
      recommendation: 'Add tests for new code before committing; maintain or increase coverage',
      estimatedEffort: 3,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'TDD: Coverage should increase, not decrease'
    });

    return findings;
  }

  /**
   * Check Testing Patterns compliance (Week 10 Day 5)
   * AAA Pattern, F.I.R.S.T Principles, Test Pyramid, Given-When-Then (BDD)
   */
  private async checkTestingPatterns(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Testing Patterns compliance...');

    // TODO: In production:
    // - Parse test files using AST to detect AAA/GWT structure
    // - Analyze test execution time for F.I.R.S.T Fast
    // - Check test independence (no shared state)
    // - Count unit vs integration vs e2e tests for pyramid
    // - Detect test flakiness for F.I.R.S.T Repeatable

    const findings: QualityFinding[] = [];

    // AAA Pattern: Arrange-Act-Assert structure
    findings.push({
      id: 'TESTING-001',
      category: 'test',
      severity: 'medium',
      title: 'AAA Pattern Violation: Tests lack clear structure',
      description: 'Test file UserService.test.ts mixes Arrange-Act-Assert phases without clear comments or spacing',
      location: 'tests/UserService.test.ts:45-78',
      recommendation: 'Add // Arrange, // Act, // Assert comments to clarify test structure',
      estimatedEffort: 1,
      riskIfNotFixed: 'medium',
      autoFixable: true,
      bestPractice: 'Testing Patterns: AAA (Arrange-Act-Assert)'
    });

    // F.I.R.S.T: Fast - Tests should run quickly
    findings.push({
      id: 'TESTING-002',
      category: 'test',
      severity: 'high',
      title: 'F.I.R.S.T Violation: Slow tests detected',
      description: 'Integration tests in PaymentProcessor.test.ts take 15+ seconds due to real API calls',
      location: 'tests/integration/PaymentProcessor.test.ts',
      recommendation: 'Mock external APIs; real integration tests should be in separate E2E suite',
      estimatedEffort: 3,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'Testing Patterns: F.I.R.S.T - Fast'
    });

    // F.I.R.S.T: Independent - Tests should not depend on each other
    findings.push({
      id: 'TESTING-003',
      category: 'test',
      severity: 'high',
      title: 'F.I.R.S.T Violation: Test interdependency detected',
      description: 'Tests in OrderService.test.ts share state via module-level variables, causing failures when run in isolation',
      location: 'tests/OrderService.test.ts:12-18',
      recommendation: 'Use beforeEach() to reset state; avoid shared mutable state',
      estimatedEffort: 2,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'Testing Patterns: F.I.R.S.T - Independent'
    });

    // F.I.R.S.T: Repeatable - Tests should produce same results
    findings.push({
      id: 'TESTING-004',
      category: 'test',
      severity: 'critical',
      title: 'F.I.R.S.T Violation: Flaky test detected',
      description: 'Test "calculateDiscount" in PricingService.test.ts fails intermittently (15% failure rate)',
      location: 'tests/PricingService.test.ts:89',
      recommendation: 'Fix race condition in async test; use deterministic dates instead of Date.now()',
      estimatedEffort: 3,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'Testing Patterns: F.I.R.S.T - Repeatable'
    });

    // Test Pyramid: Unit > Integration > E2E
    findings.push({
      id: 'TESTING-005',
      category: 'test',
      severity: 'medium',
      title: 'Test Pyramid Violation: Too many E2E tests',
      description: 'Test suite has 45 E2E tests, 30 integration tests, and only 25 unit tests. Ratio should be 70:20:10 (Unit:Integration:E2E)',
      location: 'tests/',
      recommendation: 'Increase unit test coverage to 70%, reduce E2E to 10%',
      estimatedEffort: 8,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'Testing Patterns: Test Pyramid'
    });

    // Given-When-Then (BDD): Behavior-driven test structure
    findings.push({
      id: 'TESTING-006',
      category: 'test',
      severity: 'low',
      title: 'BDD Pattern: Consider Given-When-Then structure',
      description: 'Test descriptions in CheckoutService.test.ts use technical terms instead of business behavior',
      location: 'tests/CheckoutService.test.ts',
      recommendation: 'Use "Given [context] When [action] Then [outcome]" for test descriptions',
      estimatedEffort: 2,
      riskIfNotFixed: 'low',
      autoFixable: false,
      bestPractice: 'Testing Patterns: Given-When-Then (BDD)'
    });

    return findings;
  }

  /**
   * Check Design Patterns compliance (Week 11 Day 1-2)
   * Factory, Builder, Strategy, Observer, Singleton patterns
   */
  private async checkDesignPatterns(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Design Patterns compliance...');

    // TODO: In production:
    // - Use AST parsing to detect pattern violations
    // - Analyze class structures and relationships
    // - Detect switch statements (Strategy pattern candidates)
    // - Identify complex constructors (Builder pattern candidates)
    // - Find direct instantiation (Factory pattern candidates)

    const findings: QualityFinding[] = [];

    // Factory Pattern violation (tight coupling through direct instantiation)
    findings.push({
      id: 'DESIGN-001',
      category: 'code_smell',
      severity: 'medium',
      title: 'Factory Pattern Missing: Direct object instantiation creates tight coupling',
      description: 'NotificationService directly instantiates EmailNotifier, SMSNotifier, and PushNotifier, creating tight coupling and making it hard to add new notification types',
      location: 'src/notification/NotificationService.ts:25-45',
      recommendation: 'Implement Factory pattern: create NotifierFactory that returns INotifier interface',
      estimatedEffort: 3,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'Design Patterns: Factory Pattern'
    });

    // Builder Pattern missing (complex constructor)
    findings.push({
      id: 'DESIGN-002',
      category: 'code_smell',
      severity: 'medium',
      title: 'Builder Pattern Missing: Constructor has too many parameters',
      description: 'OrderBuilder class has a constructor with 12 parameters (customer, items, shipping, billing, discounts, taxes, etc.), making it error-prone and hard to use',
      location: 'src/order/Order.ts:15',
      recommendation: 'Implement Builder pattern: create OrderBuilder with fluent interface (.withCustomer().withItems().build())',
      estimatedEffort: 4,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'Design Patterns: Builder Pattern'
    });

    // Strategy Pattern missing (switch/if-else chains)
    findings.push({
      id: 'DESIGN-003',
      category: 'code_smell',
      severity: 'high',
      title: 'Strategy Pattern Missing: Large switch statement on type',
      description: 'DiscountCalculator uses 85-line switch statement on discount type (percentage, fixed, bogo, tiered, etc.), violating Open/Closed principle',
      location: 'src/pricing/DiscountCalculator.ts:42-127',
      recommendation: 'Implement Strategy pattern: create IDiscountStrategy interface with concrete strategies for each type',
      estimatedEffort: 5,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'Design Patterns: Strategy Pattern'
    });

    // Observer Pattern missing (polling instead of events)
    findings.push({
      id: 'DESIGN-004',
      category: 'performance',
      severity: 'high',
      title: 'Observer Pattern Missing: Polling instead of event-driven updates',
      description: 'Dashboard polls OrderService every 2 seconds for status updates instead of subscribing to events, causing unnecessary load',
      location: 'src/ui/Dashboard.tsx:89-112',
      recommendation: 'Implement Observer pattern: OrderService emits events, Dashboard subscribes to order status changes',
      estimatedEffort: 4,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'Design Patterns: Observer Pattern'
    });

    // Singleton Pattern misuse (global state)
    findings.push({
      id: 'DESIGN-005',
      category: 'code_smell',
      severity: 'critical',
      title: 'Singleton Pattern Misuse: Global mutable state makes testing impossible',
      description: 'ConfigManager uses Singleton pattern with mutable global state, preventing parallel test execution and causing test pollution',
      location: 'src/config/ConfigManager.ts:8-35',
      recommendation: 'Replace Singleton with Dependency Injection; pass ConfigManager instance to classes that need it',
      estimatedEffort: 5,
      riskIfNotFixed: 'high',
      autoFixable: false,
      bestPractice: 'Design Patterns: Singleton Pattern (Anti-pattern)'
    });

    return findings;
  }

  /**
   * Check Clean Code compliance (Week 11 Day 3-4)
   * YAGNI, KISS, Boy Scout Rule, Magic Numbers, Meaningful Names
   */
  private async checkCleanCode(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Clean Code compliance...');

    // TODO: In production:
    // - Use dead code detection tools (ts-prune, knip)
    // - Analyze code complexity and abstraction levels
    // - Check git history for code quality trends
    // - Detect magic numbers with regex/AST parsing
    // - Analyze naming conventions with natural language processing

    const findings: QualityFinding[] = [];

    // YAGNI: You Aren't Gonna Need It (unused code)
    findings.push({
      id: 'CLEAN-001',
      category: 'code_smell',
      severity: 'medium',
      title: 'YAGNI Violation: Unused utility functions',
      description: 'HelperUtils.ts contains 8 utility functions that are never called anywhere in the codebase',
      location: 'src/utils/HelperUtils.ts',
      recommendation: 'Remove unused code to reduce maintenance burden; YAGNI - only write code you actually need',
      estimatedEffort: 1,
      riskIfNotFixed: 'low',
      autoFixable: true,
      bestPractice: 'Clean Code: YAGNI (You Aren\'t Gonna Need It)'
    });

    // KISS: Keep It Simple, Stupid (over-engineering)
    findings.push({
      id: 'CLEAN-002',
      category: 'code_smell',
      severity: 'high',
      title: 'KISS Violation: Over-engineered solution',
      description: 'LoggingService uses Abstract Factory + Strategy + Observer patterns for simple console.log wrapper, adding unnecessary complexity',
      location: 'src/logging/LoggingService.ts:1-250',
      recommendation: 'Simplify to basic logger class; follow KISS - solve the current problem, not hypothetical future ones',
      estimatedEffort: 5,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'Clean Code: KISS (Keep It Simple, Stupid)'
    });

    // Boy Scout Rule: Leave code cleaner than you found it
    findings.push({
      id: 'CLEAN-003',
      category: 'code_smell',
      severity: 'medium',
      title: 'Boy Scout Rule Violation: Code quality degrading over time',
      description: 'Git history shows OrderService.ts complexity increased from 8 to 25 in last 3 commits without refactoring',
      location: 'src/order/OrderService.ts',
      recommendation: 'Refactor during next change; follow Boy Scout Rule - leave code better than you found it',
      estimatedEffort: 3,
      riskIfNotFixed: 'medium',
      autoFixable: false,
      bestPractice: 'Clean Code: Boy Scout Rule'
    });

    // Magic Numbers: Use named constants
    findings.push({
      id: 'CLEAN-004',
      category: 'code_smell',
      severity: 'medium',
      title: 'Magic Numbers: Hardcoded numbers without explanation',
      description: 'PricingService contains magic numbers: 0.15 (line 42), 86400 (line 78), 1000 (line 91) - meaning unclear',
      location: 'src/pricing/PricingService.ts',
      recommendation: 'Replace with named constants: TAX_RATE = 0.15, SECONDS_PER_DAY = 86400, MS_PER_SECOND = 1000',
      estimatedEffort: 1,
      riskIfNotFixed: 'medium',
      autoFixable: true,
      bestPractice: 'Clean Code: No Magic Numbers'
    });

    // Meaningful Names: Variable/function naming conventions
    findings.push({
      id: 'CLEAN-005',
      category: 'code_smell',
      severity: 'low',
      title: 'Meaningful Names: Unclear variable names',
      description: 'Function uses unclear names: d (line 15), tmp (line 23), x1/x2 (lines 45-46) instead of descriptive names',
      location: 'src/calculator/DiscountCalculator.ts:15-50',
      recommendation: 'Use meaningful names: discountAmount, temporaryResult, originalPrice/discountedPrice',
      estimatedEffort: 1,
      riskIfNotFixed: 'low',
      autoFixable: true,
      bestPractice: 'Clean Code: Meaningful Names'
    });

    return findings;
  }

  /**
   * Check Law of Demeter compliance
   */
  private async checkLawOfDemeter(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Law of Demeter...');

    // TODO: Detect method call chains (a.getB().getC())

    const findings: QualityFinding[] = [];

    // Law of Demeter: Method call chains
    findings.push({
      id: 'LOD-001',
      category: 'code_smell',
      severity: 'medium',
      title: 'Law of Demeter Violation: Chained method calls',
      description: 'order.getCart().getItems().calculateTotal() violates Law of Demeter (too many dots)',
      location: 'src/checkout/CheckoutService.ts:28',
      recommendation: 'Add order.calculateTotal() method to delegate internally',
      estimatedEffort: 2,
      riskIfNotFixed: 'low',
      autoFixable: false,
      bestPractice: 'Law of Demeter (Principle of Least Knowledge)'
    });

    return findings;
  }

  /**
   * SuperClaude Analysis Check
   * Week 6 Day 3 - Integrates SuperClaude /sc:analyze for 20+ additional checks
   */
  private async checkSuperClaude(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking SuperClaude Analysis...');

    const findings: QualityFinding[] = [];

    try {
      // Get target files from context
      const targetFiles = context.targetFiles || [];

      if (targetFiles.length === 0) {
        console.log('   ⚠ No target files specified for SuperClaude analysis, skipping...');
        return findings;
      }

      // Get SuperClaude analyzer instance
      const analyzer = getSuperClaudeAnalyzer();

      // Check if SuperClaude is available
      const isAvailable = await analyzer.isAvailable();
      if (!isAvailable) {
        console.log('   ⚠ SuperClaude CLI not available, skipping analysis...');
        return findings;
      }

      // Run SuperClaude analysis
      const result = await analyzer.analyzeCode({
        targetFiles,
        focus: 'quality',
        depth: 'quick',
        timeout: 60000  // 60 seconds
      });

      if (result.success) {
        console.log(`   ✓ SuperClaude analysis complete: ${result.findings.length} findings (score: ${result.metrics.overallScore}/100)`);
        findings.push(...result.findings);
      } else {
        console.log(`   ⚠ SuperClaude analysis failed: ${result.error}`);
      }
    } catch (error) {
      console.error('   ✗ SuperClaude analysis error:', error instanceof Error ? error.message : String(error));
      // Don't block on SuperClaude errors - it's an enhancement, not a requirement
    }

    return findings;
  }

  // ==========================================================================
  // SCORING & DECISION LOGIC
  // ==========================================================================

  /**
   * Calculate best practice score from findings
   */
  private calculateBestPracticeScore(findings: QualityFinding[]): BestPracticeScore {
    // Count violations by best practice
    const sigViolations = {
      shortUnits: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #1')).length,
      simpleUnits: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #2')).length,
      writeOnce: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #3')).length,
      smallInterfaces: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #4')).length,
      separateConcerns: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #5')).length,
      looseCoupling: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #6')).length,
      balancedComponents: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #7')).length,
      smallCodebase: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #8')).length,
      automatedPipeline: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #9')).length,
      cleanCode: findings.filter(f => f.bestPractice?.includes('SIG-TOP-10 #10')).length
    };

    const solidViolations = {
      srp: findings.filter(f => f.bestPractice?.includes('SOLID: Single Responsibility')).length,
      ocp: findings.filter(f => f.bestPractice?.includes('SOLID: Open/Closed')).length,
      lsp: findings.filter(f => f.bestPractice?.includes('SOLID: Liskov Substitution')).length,
      isp: findings.filter(f => f.bestPractice?.includes('SOLID: Interface Segregation')).length,
      dip: findings.filter(f => f.bestPractice?.includes('SOLID: Dependency Inversion')).length
    };

    const graspViolations = {
      informationExpert: findings.filter(f => f.bestPractice?.includes('GRASP: Information Expert')).length,
      lowCoupling: findings.filter(f => f.bestPractice?.includes('GRASP: Low Coupling')).length,
      highCohesion: findings.filter(f => f.bestPractice?.includes('GRASP: High Cohesion')).length
    };

    const tddViolations = {
      noTests: findings.filter(f => f.bestPractice?.includes('TDD: Test-Driven Development')).length,
      testAfterCode: findings.filter(f => f.bestPractice?.includes('TDD: Red-Green-Refactor')).length,
      coverageDecrease: findings.filter(f => f.bestPractice?.includes('TDD: Coverage should increase')).length
    };

    const testingPatternsViolations = {
      aaaPattern: findings.filter(f => f.bestPractice?.includes('Testing Patterns: AAA')).length,
      firstPrinciples: findings.filter(f => f.bestPractice?.includes('Testing Patterns: F.I.R.S.T')).length,
      testPyramid: findings.filter(f => f.bestPractice?.includes('Testing Patterns: Test Pyramid')).length,
      givenWhenThen: findings.filter(f => f.bestPractice?.includes('Testing Patterns: Given-When-Then')).length
    };

    const designPatternsViolations = {
      factoryPattern: findings.filter(f => f.bestPractice?.includes('Design Patterns: Factory Pattern')).length,
      builderPattern: findings.filter(f => f.bestPractice?.includes('Design Patterns: Builder Pattern')).length,
      strategyPattern: findings.filter(f => f.bestPractice?.includes('Design Patterns: Strategy Pattern')).length,
      observerPattern: findings.filter(f => f.bestPractice?.includes('Design Patterns: Observer Pattern')).length,
      singletonPattern: findings.filter(f => f.bestPractice?.includes('Design Patterns: Singleton Pattern')).length
    };

    const cleanCodeViolations = {
      yagni: findings.filter(f => f.bestPractice?.includes('Clean Code: YAGNI')).length,
      kiss: findings.filter(f => f.bestPractice?.includes('Clean Code: KISS')).length,
      boyScoutRule: findings.filter(f => f.bestPractice?.includes('Clean Code: Boy Scout Rule')).length,
      magicNumbers: findings.filter(f => f.bestPractice?.includes('Clean Code: No Magic Numbers')).length,
      meaningfulNames: findings.filter(f => f.bestPractice?.includes('Clean Code: Meaningful Names')).length
    };

    const lodViolations = findings.filter(f => f.bestPractice?.includes('Law of Demeter')).length;

    // Calculate compliance percentages (simple formula: fewer violations = higher score)
    const sigTotal = Object.values(sigViolations).reduce((a, b) => a + b, 0);
    const sigCompliance = Math.max(0, 100 - (sigTotal * 5));  // Each violation reduces score by 5%

    const solidTotal = Object.values(solidViolations).reduce((a, b) => a + b, 0);
    const solidCompliance = Math.max(0, 100 - (solidTotal * 10));

    const graspTotal = Object.values(graspViolations).reduce((a, b) => a + b, 0);
    const graspCompliance = Math.max(0, 100 - (graspTotal * 10));

    const tddTotal = Object.values(tddViolations).reduce((a, b) => a + b, 0);
    const tddCompliance = Math.max(0, 100 - (tddTotal * 10));

    const testingPatternsTotal = Object.values(testingPatternsViolations).reduce((a, b) => a + b, 0);
    const testingPatternsCompliance = Math.max(0, 100 - (testingPatternsTotal * 8));  // Each violation reduces score by 8%

    const designPatternsTotal = Object.values(designPatternsViolations).reduce((a, b) => a + b, 0);
    const designPatternsCompliance = Math.max(0, 100 - (designPatternsTotal * 10));  // Each violation reduces score by 10%

    const cleanCodeTotal = Object.values(cleanCodeViolations).reduce((a, b) => a + b, 0);
    const cleanCodeCompliance = Math.max(0, 100 - (cleanCodeTotal * 8));  // Each violation reduces score by 8%

    // Total score: average of all enabled checks
    const enabledScores: number[] = [];
    if (this.config.enabledChecks.sig) enabledScores.push(sigCompliance);
    if (this.config.enabledChecks.solid) enabledScores.push(solidCompliance);
    if (this.config.enabledChecks.grasp) enabledScores.push(graspCompliance);
    if (this.config.enabledChecks.tdd) enabledScores.push(tddCompliance);
    if (this.config.enabledChecks.testingPatterns) enabledScores.push(testingPatternsCompliance);
    if (this.config.enabledChecks.designPatterns) enabledScores.push(designPatternsCompliance);
    if (this.config.enabledChecks.cleanCode) enabledScores.push(cleanCodeCompliance);

    const totalScore = enabledScores.length > 0
      ? Math.round(enabledScores.reduce((a, b) => a + b, 0) / enabledScores.length)
      : 100;

    return {
      sigCompliance: {
        overall: sigCompliance,
        violations: sigViolations
      },
      solidCompliance: {
        overall: solidCompliance,
        violations: solidViolations
      },
      graspCompliance: {
        overall: graspCompliance,
        violations: graspViolations
      },
      tddCompliance: {
        overall: tddCompliance,
        violations: tddViolations
      },
      testingPatternsCompliance: {
        overall: testingPatternsCompliance,
        violations: testingPatternsViolations
      },
      designPatternsCompliance: {
        overall: designPatternsCompliance,
        violations: designPatternsViolations
      },
      cleanCodeCompliance: {
        overall: cleanCodeCompliance,
        violations: cleanCodeViolations
      },
      lawOfDemeter: {
        violations: lodViolations
      },
      totalScore
    };
  }

  /**
   * Determine if quality gates passed
   */
  private determineIfPassed(findings: QualityFinding[], score: BestPracticeScore): boolean {
    // Check minimum score threshold
    if (this.config.blockingRules.minimumScore !== undefined) {
      if (score.totalScore < this.config.blockingRules.minimumScore) {
        return false;
      }
    }

    // No critical violations if blockOnCritical enabled
    if (this.config.blockingRules.blockOnCritical) {
      const hasCritical = findings.some(f => f.severity === 'critical');
      if (hasCritical) return false;
    }

    // No coverage decrease if enabled
    if (this.config.blockingRules.blockOnCoverageDecrease) {
      const hasCoverageDecrease = findings.some(f =>
        f.bestPractice?.includes('TDD: Coverage should increase')
      );
      if (hasCoverageDecrease) return false;
    }

    // No production code without tests if enabled
    if (this.config.blockingRules.blockOnNoTests) {
      const hasNoTests = findings.some(f =>
        f.bestPractice?.includes('TDD: Test-Driven Development')
      );
      if (hasNoTests) return false;
    }

    return true;
  }

  /**
   * Determine if violations should block commit/PR
   */
  private determineIfBlocking(findings: QualityFinding[], score: BestPracticeScore): boolean {
    // If passed, not blocking
    if (this.determineIfPassed(findings, score)) {
      return false;
    }

    // If any blocking rule failed, it's blocking
    return true;
  }

  /**
   * Create empty best practice score (for pre-implementation)
   */
  private createEmptyBestPracticeScore(): BestPracticeScore {
    return {
      sigCompliance: {
        overall: 100,
        violations: {
          shortUnits: 0,
          simpleUnits: 0,
          writeOnce: 0,
          smallInterfaces: 0,
          separateConcerns: 0,
          looseCoupling: 0,
          balancedComponents: 0,
          smallCodebase: 0,
          automatedPipeline: 0,
          cleanCode: 0
        }
      },
      solidCompliance: {
        overall: 100,
        violations: {
          srp: 0,
          ocp: 0,
          lsp: 0,
          isp: 0,
          dip: 0
        }
      },
      graspCompliance: {
        overall: 100,
        violations: {
          informationExpert: 0,
          lowCoupling: 0,
          highCohesion: 0
        }
      },
      tddCompliance: {
        overall: 100,
        violations: {
          noTests: 0,
          testAfterCode: 0,
          coverageDecrease: 0
        }
      },
      testingPatternsCompliance: {
        overall: 100,
        violations: {
          aaaPattern: 0,
          firstPrinciples: 0,
          testPyramid: 0,
          givenWhenThen: 0
        }
      },
      designPatternsCompliance: {
        overall: 100,
        violations: {
          factoryPattern: 0,
          builderPattern: 0,
          strategyPattern: 0,
          observerPattern: 0,
          singletonPattern: 0
        }
      },
      cleanCodeCompliance: {
        overall: 100,
        violations: {
          yagni: 0,
          kiss: 0,
          boyScoutRule: 0,
          magicNumbers: 0,
          meaningfulNames: 0
        }
      },
      lawOfDemeter: {
        violations: 0
      },
      totalScore: 100
    };
  }

  // ==========================================================================
  // UTILITY METHODS
  // ==========================================================================

  /**
   * Get configuration
   */
  getConfig(): QualityGateConfig {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<QualityGateConfig>): void {
    this.config = {
      ...this.config,
      ...config,
      enabledChecks: {
        ...this.config.enabledChecks,
        ...config.enabledChecks
      },
      blockingRules: {
        ...this.config.blockingRules,
        ...config.blockingRules
      },
      severityThresholds: {
        ...this.config.severityThresholds,
        ...config.severityThresholds
      }
    };
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export default QualityGateService;
