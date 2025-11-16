/**
 * Quality Gate Types for Automated Validation System
 *
 * Defines types for quality validation checkpoints after each agent phase
 */

/**
 * Quality gate status
 */
export enum QualityGateStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PASSED = 'passed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

/**
 * Quality gate type (triggered after specific agents)
 */
export enum QualityGateType {
  ARCHITECTURE = 'architecture',      // After Felix (Architecture)
  CODE_QUALITY = 'code_quality',      // After code changes
  TEST_COVERAGE = 'test_coverage',    // After Tessa (Tests)
  SECURITY = 'security',              // After Quinn (Quality)
  DOCUMENTATION = 'documentation',     // After Diana (Documentation)
  PERFORMANCE = 'performance',         // After performance changes
  ACCESSIBILITY = 'accessibility'      // After UI/UX changes
}

/**
 * Severity level for quality issues
 */
export enum IssueSeverity {
  CRITICAL = 'critical',              // Must fix immediately
  HIGH = 'high',                      // Must fix before merge
  MEDIUM = 'medium',                  // Should fix soon
  LOW = 'low',                        // Can fix later
  INFO = 'info'                       // Informational only
}

/**
 * Validation result status
 */
export enum ValidationStatus {
  PASS = 'pass',
  FAIL = 'fail',
  WARNING = 'warning',
  SKIPPED = 'skipped'
}

/**
 * Quality issue detected by validator
 */
export interface QualityIssue {
  id: string;
  validator: string;                  // Which validator found this
  severity: IssueSeverity;
  category: string;                   // e.g., "Code Smell", "Security Vulnerability"
  title: string;
  description: string;
  location: string;                   // File path, line number, etc.
  codeSnippet?: string;               // Relevant code
  recommendation: string;             // How to fix
  autoFixAvailable: boolean;
  estimatedEffort: 'LOW' | 'MEDIUM' | 'HIGH';
  relatedIssues?: string[];           // IDs of related issues
  detectedAt: Date;
}

/**
 * Validation rule
 */
export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: IssueSeverity;
  enabled: boolean;
  threshold?: number;                 // e.g., coverage > 80%
  pattern?: string;                   // Regex pattern for code checks
}

/**
 * Validator result
 */
export interface ValidatorResult {
  validatorName: string;
  status: ValidationStatus;
  executionTime: number;              // Milliseconds
  rulesChecked: number;
  rulesPassed: number;
  rulesFailed: number;
  issuesFound: QualityIssue[];
  metrics?: Record<string, number>;   // e.g., { coverage: 85.5, complexity: 12 }
  recommendations: string[];
  summary: string;
}

/**
 * Quality gate configuration
 */
export interface QualityGateConfig {
  type: QualityGateType;
  enabled: boolean;
  blocking: boolean;                  // If true, failure blocks progress
  validators: string[];               // Validator names to run
  thresholds: Record<string, number>; // e.g., { coverage: 80, complexity: 15 }
  timeout: number;                    // Milliseconds
  retryOnFailure: boolean;
  maxRetries: number;
  notifyOnFailure: boolean;
  escalateAfterRetries: boolean;
}

/**
 * Quality gate result
 */
export interface QualityGateResult {
  gateId: string;
  type: QualityGateType;
  status: QualityGateStatus;
  triggeredBy: string;                // Agent name
  triggeredAt: Date;
  completedAt?: Date;
  duration: number;                   // Milliseconds

  // Validation results
  validatorResults: ValidatorResult[];
  totalIssues: number;
  criticalIssues: number;
  highIssues: number;
  mediumIssues: number;
  lowIssues: number;

  // Metrics
  overallScore: number;               // 0-100
  passedValidators: number;
  failedValidators: number;
  warningValidators: number;

  // Decision
  passed: boolean;
  canProceed: boolean;                // True if can continue despite failures
  mustRetry: boolean;
  mustEscalate: boolean;

  // Feedback for retry
  feedbackForRetry?: string;
  suggestedFixes: string[];
  autoFixesApplied: number;

  // Metadata
  attempt: number;                    // Retry attempt number
  maxAttempts: number;
  notes: string;
}

/**
 * Quality gate session (tracks full gate execution with retries)
 */
export interface QualityGateSession {
  sessionId: string;
  type: QualityGateType;
  config: QualityGateConfig;
  attempts: QualityGateResult[];
  finalResult: QualityGateResult;
  totalDuration: number;
  escalated: boolean;
  escalationReason?: string;
}

/**
 * Architecture validation result
 */
export interface ArchitectureValidation {
  patternsValidated: string[];        // e.g., "MVC", "Repository Pattern"
  designConsistency: number;          // 0-100
  scalabilityScore: number;           // 0-100
  maintainabilityScore: number;       // 0-100
  couplingScore: number;              // 0-100 (lower is better)
  cohesionScore: number;              // 0-100 (higher is better)
  issues: QualityIssue[];
}

/**
 * Code quality validation result
 */
export interface CodeQualityValidation {
  linterErrors: number;
  linterWarnings: number;
  complexityScore: number;            // Average cyclomatic complexity
  duplicateCodePercentage: number;
  codeSmells: number;
  maintainabilityIndex: number;       // 0-100
  issues: QualityIssue[];
}

/**
 * Test coverage validation result
 */
export interface TestCoverageValidation {
  lineCoverage: number;               // Percentage
  branchCoverage: number;             // Percentage
  functionCoverage: number;           // Percentage
  statementCoverage: number;          // Percentage
  uncoveredLines: string[];           // File:line references
  testQualityScore: number;           // 0-100 (AAA pattern, edge cases, etc.)
  issues: QualityIssue[];
}

/**
 * Security validation result
 */
export interface SecurityValidation {
  vulnerabilitiesFound: number;
  criticalVulnerabilities: number;
  highVulnerabilities: number;
  owaspTop10Checks: Record<string, boolean>;
  dependencyVulnerabilities: number;
  secretsExposed: number;
  securityScore: number;              // 0-100
  issues: QualityIssue[];
}

/**
 * Documentation validation result
 */
export interface DocumentationValidation {
  completenessScore: number;          // 0-100
  clarityScore: number;               // 0-100
  examplesPresent: boolean;
  apiDocumented: boolean;
  readmePresent: boolean;
  changelogPresent: boolean;
  missingDocs: string[];              // What needs documentation
  issues: QualityIssue[];
}

/**
 * Calculate overall quality score
 */
export function calculateQualityScore(
  validatorResults: ValidatorResult[]
): number {
  if (validatorResults.length === 0) return 0;

  const scores = validatorResults.map(result => {
    const passRate = result.rulesChecked > 0
      ? (result.rulesPassed / result.rulesChecked) * 100
      : 0;

    // Reduce score based on critical/high issues
    const criticalCount = result.issuesFound.filter(
      i => i.severity === IssueSeverity.CRITICAL
    ).length;
    const highCount = result.issuesFound.filter(
      i => i.severity === IssueSeverity.HIGH
    ).length;

    const penalty = (criticalCount * 10) + (highCount * 5);
    return Math.max(0, passRate - penalty);
  });

  const averageScore = scores.reduce((sum, s) => sum + s, 0) / scores.length;
  return Math.round(averageScore);
}

/**
 * Determine if quality gate passed
 */
export function determineQualityGatePassed(
  result: QualityGateResult,
  config: QualityGateConfig
): boolean {
  // Must have no critical issues
  if (result.criticalIssues > 0) return false;

  // Must pass minimum score threshold (if set)
  const minScore = config.thresholds['minScore'] || 70;
  if (result.overallScore < minScore) return false;

  // Must pass all blocking validators
  const blockingValidators = result.validatorResults.filter(
    v => v.status === ValidationStatus.FAIL
  );
  if (config.blocking && blockingValidators.length > 0) return false;

  return true;
}

/**
 * Generate feedback for retry
 */
export function generateRetryFeedback(
  result: QualityGateResult
): string {
  const criticalIssues = result.validatorResults
    .flatMap(v => v.issuesFound)
    .filter(i => i.severity === IssueSeverity.CRITICAL);

  const highIssues = result.validatorResults
    .flatMap(v => v.issuesFound)
    .filter(i => i.severity === IssueSeverity.HIGH);

  let feedback = 'Quality gate failed. Please address the following:\n\n';

  if (criticalIssues.length > 0) {
    feedback += `CRITICAL ISSUES (${criticalIssues.length}):\n`;
    criticalIssues.slice(0, 3).forEach(issue => {
      feedback += `- ${issue.title}: ${issue.recommendation}\n`;
    });
    feedback += '\n';
  }

  if (highIssues.length > 0) {
    feedback += `HIGH PRIORITY ISSUES (${highIssues.length}):\n`;
    highIssues.slice(0, 3).forEach(issue => {
      feedback += `- ${issue.title}: ${issue.recommendation}\n`;
    });
    feedback += '\n';
  }

  feedback += `Overall score: ${result.overallScore}/100\n`;
  feedback += `Attempt: ${result.attempt}/${result.maxAttempts}`;

  return feedback;
}

/**
 * Count issues by severity
 */
export function countIssuesBySeverity(
  issues: QualityIssue[]
): Record<IssueSeverity, number> {
  return {
    [IssueSeverity.CRITICAL]: issues.filter(i => i.severity === IssueSeverity.CRITICAL).length,
    [IssueSeverity.HIGH]: issues.filter(i => i.severity === IssueSeverity.HIGH).length,
    [IssueSeverity.MEDIUM]: issues.filter(i => i.severity === IssueSeverity.MEDIUM).length,
    [IssueSeverity.LOW]: issues.filter(i => i.severity === IssueSeverity.LOW).length,
    [IssueSeverity.INFO]: issues.filter(i => i.severity === IssueSeverity.INFO).length
  };
}

/**
 * Get suggested fixes from issues
 */
export function getSuggestedFixes(
  issues: QualityIssue[]
): string[] {
  // Get unique recommendations for critical and high issues
  const criticalAndHigh = issues.filter(
    i => i.severity === IssueSeverity.CRITICAL || i.severity === IssueSeverity.HIGH
  );

  return [...new Set(criticalAndHigh.map(i => i.recommendation))];
}

/**
 * Check if should escalate to human
 */
export function shouldEscalate(
  session: QualityGateSession
): boolean {
  const lastAttempt = session.attempts[session.attempts.length - 1];

  // Escalate if max attempts reached and still failing
  if (session.attempts.length >= session.config.maxRetries && !lastAttempt.passed) {
    return true;
  }

  // Escalate if critical issues persist after 2 attempts
  if (session.attempts.length >= 2 && lastAttempt.criticalIssues > 0) {
    return true;
  }

  // Escalate if score is not improving
  if (session.attempts.length >= 2) {
    const scoreImprovement = lastAttempt.overallScore - session.attempts[0].overallScore;
    if (scoreImprovement < 5) {
      return true;
    }
  }

  return false;
}

/**
 * Default quality gate configurations
 */
export const DEFAULT_QUALITY_GATE_CONFIGS: Record<QualityGateType, QualityGateConfig> = {
  [QualityGateType.ARCHITECTURE]: {
    type: QualityGateType.ARCHITECTURE,
    enabled: true,
    blocking: true,
    validators: ['architecture'],
    thresholds: { designConsistency: 80, scalabilityScore: 70 },
    timeout: 60000,
    retryOnFailure: true,
    maxRetries: 3,
    notifyOnFailure: true,
    escalateAfterRetries: true
  },
  [QualityGateType.CODE_QUALITY]: {
    type: QualityGateType.CODE_QUALITY,
    enabled: true,
    blocking: true,
    validators: ['code-quality'],
    thresholds: { minScore: 70, complexity: 15 },
    timeout: 120000,
    retryOnFailure: true,
    maxRetries: 3,
    notifyOnFailure: true,
    escalateAfterRetries: true
  },
  [QualityGateType.TEST_COVERAGE]: {
    type: QualityGateType.TEST_COVERAGE,
    enabled: true,
    blocking: true,
    validators: ['test-coverage'],
    thresholds: { coverage: 80 },
    timeout: 180000,
    retryOnFailure: true,
    maxRetries: 3,
    notifyOnFailure: true,
    escalateAfterRetries: true
  },
  [QualityGateType.SECURITY]: {
    type: QualityGateType.SECURITY,
    enabled: true,
    blocking: true,
    validators: ['security'],
    thresholds: { minScore: 90, criticalVulnerabilities: 0 },
    timeout: 120000,
    retryOnFailure: true,
    maxRetries: 2,
    notifyOnFailure: true,
    escalateAfterRetries: true
  },
  [QualityGateType.DOCUMENTATION]: {
    type: QualityGateType.DOCUMENTATION,
    enabled: true,
    blocking: false,
    validators: ['documentation'],
    thresholds: { completeness: 80, clarity: 70 },
    timeout: 60000,
    retryOnFailure: true,
    maxRetries: 2,
    notifyOnFailure: true,
    escalateAfterRetries: false
  },
  [QualityGateType.PERFORMANCE]: {
    type: QualityGateType.PERFORMANCE,
    enabled: false,
    blocking: false,
    validators: ['performance'],
    thresholds: { responseTime: 200 },
    timeout: 300000,
    retryOnFailure: false,
    maxRetries: 1,
    notifyOnFailure: true,
    escalateAfterRetries: false
  },
  [QualityGateType.ACCESSIBILITY]: {
    type: QualityGateType.ACCESSIBILITY,
    enabled: false,
    blocking: false,
    validators: ['accessibility'],
    thresholds: { wcagCompliance: 90 },
    timeout: 60000,
    retryOnFailure: true,
    maxRetries: 2,
    notifyOnFailure: true,
    escalateAfterRetries: false
  }
};
