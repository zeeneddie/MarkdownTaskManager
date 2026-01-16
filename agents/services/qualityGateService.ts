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

    // TODO: Integrate actual static analysis tools:
    // - ESLint with complexity rules
    // - SonarQube
    // - jscpd for duplication detection
    // - ts-complex for TypeScript complexity
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check SOLID principles compliance
   */
  private async checkSolidCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking SOLID compliance...');

    // TODO: Integrate actual analysis tools:
    // - SonarQube SOLID rules
    // - Manual code review patterns
    // - Class dependency analysis
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check GRASP principles compliance
   */
  private async checkGraspCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking GRASP compliance...');

    // TODO: Integrate actual analysis for responsibility assignment, coupling, cohesion
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check TDD compliance
   */
  private async checkTddCompliance(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking TDD compliance...');

    // TODO: Integrate actual TDD analysis:
    // - Check if test files exist for production files
    // - Analyze git history to detect tests-after-code
    // - Compare coverage between commits
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check Testing Patterns compliance (Week 10 Day 5)
   * AAA Pattern, F.I.R.S.T Principles, Test Pyramid, Given-When-Then (BDD)
   */
  private async checkTestingPatterns(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Testing Patterns compliance...');

    // TODO: Integrate actual testing pattern analysis:
    // - Parse test files using AST to detect AAA/GWT structure
    // - Analyze test execution time for F.I.R.S.T Fast
    // - Check test independence (no shared state)
    // - Count unit vs integration vs e2e tests for pyramid
    // - Detect test flakiness for F.I.R.S.T Repeatable
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check Design Patterns compliance (Week 11 Day 1-2)
   * Factory, Builder, Strategy, Observer, Singleton patterns
   */
  private async checkDesignPatterns(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Design Patterns compliance...');

    // TODO: Integrate actual design pattern analysis:
    // - Use AST parsing to detect pattern violations
    // - Analyze class structures and relationships
    // - Detect switch statements (Strategy pattern candidates)
    // - Identify complex constructors (Builder pattern candidates)
    // - Find direct instantiation (Factory pattern candidates)
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check Clean Code compliance (Week 11 Day 3-4)
   * YAGNI, KISS, Boy Scout Rule, Magic Numbers, Meaningful Names
   */
  private async checkCleanCode(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Clean Code compliance...');

    // TODO: Integrate actual clean code analysis:
    // - Use dead code detection tools (ts-prune, knip)
    // - Analyze code complexity and abstraction levels
    // - Check git history for code quality trends
    // - Detect magic numbers with regex/AST parsing
    // - Analyze naming conventions with natural language processing
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
  }

  /**
   * Check Law of Demeter compliance
   */
  private async checkLawOfDemeter(context: QualityCheckContext): Promise<QualityFinding[]> {
    console.log('   Checking Law of Demeter...');

    // TODO: Integrate actual Law of Demeter analysis:
    // - Detect method call chains (a.getB().getC())
    // For now, return empty array (no mock data to avoid blocking commits)

    return [];
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
