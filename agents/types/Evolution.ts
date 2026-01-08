/**
 * Evolution Types for Self-Evolving AI Agents
 *
 * Week 17: AgentEvolver Integration
 * Based on: github.com/zeeneddie/AgentEvolver
 *
 * Implements three core mechanisms:
 * 1. Self-Questioning: "What should I learn?"
 * 2. Self-Navigating: "How did I do this before?"
 * 3. Self-Attributing: "Which steps were crucial?"
 *
 * Author: Claude Code (Week 17 Day 1)
 * Date: 2025-11-22
 */

import { AgentRole, AgentConfig } from './AgentTypes';
import { WorkType } from './WorkTypes';

// ============================================================================
// EXPERIENCE TYPES
// ============================================================================

/**
 * Task context for experience lookup
 */
export interface TaskContext {
  workType: WorkType;
  description: string;
  complexity: 'low' | 'medium' | 'high';
  domain?: string;
  technologies?: string[];
  constraints?: string[];
  previousAttempts?: number;
}

/**
 * Result of a completed task
 */
export interface TaskResult {
  taskId: string;
  agentId: string;
  workType: WorkType;
  success: boolean;
  duration: number; // milliseconds
  qualityScore: number; // 0-100
  validationsPassed: string[];
  validationsFailed: string[];
  outputArtifacts: string[];
  errorMessages?: string[];
  retryCount: number;
  peerAssistanceUsed: boolean;
}

/**
 * Guidance from past experience
 */
export interface Guidance {
  relevantExperiences: Experience[];
  suggestedApproach: string;
  warningsFromPast: string[];
  confidenceScore: number; // 0-1
  patternMatches: PatternMatch[];
}

/**
 * A single experience record stored in ChromaDB
 */
export interface Experience {
  id: string;
  agentId: string;
  agentRole: AgentRole;
  workType: WorkType;
  taskDescription: string;
  approach: string;
  outcome: 'success' | 'partial' | 'failure';
  lessonsLearned: string[];
  keyDecisions: KeyDecision[];
  duration: number;
  qualityScore: number;
  timestamp: Date;
  embedding?: number[]; // Vector embedding for semantic search
  metadata: Record<string, any>;
}

/**
 * Key decision made during task execution
 */
export interface KeyDecision {
  decision: string;
  reasoning: string;
  alternatives: string[];
  outcome: 'positive' | 'neutral' | 'negative';
  impactScore: number; // -1 to 1
}

/**
 * Pattern match from experience store
 */
export interface PatternMatch {
  patternId: string;
  patternName: string;
  description: string;
  applicability: number; // 0-1 how applicable to current context
  successRate: number; // 0-1 historical success rate
  averageQuality: number; // 0-100
  usageCount: number;
  lastUsed: Date;
  relatedExperiences: string[]; // Experience IDs
}

/**
 * Attribution for outcome analysis
 */
export interface Attribution {
  taskId: string;
  agentId: string;
  totalScore: number;
  attributions: StepAttribution[];
  keySuccessFactors: string[];
  keyFailureFactors: string[];
  recommendations: string[];
}

/**
 * Attribution for a single step
 */
export interface StepAttribution {
  stepName: string;
  stepIndex: number;
  contribution: number; // -1 to 1 (negative = harmful, positive = helpful)
  confidence: number; // 0-1
  reasoning: string;
  couldImprove: boolean;
  improvementSuggestion?: string;
}

// ============================================================================
// PERFORMANCE METRICS
// ============================================================================

/**
 * Performance metrics for an agent
 */
export interface PerformanceMetrics {
  agentId: string;
  agentRole: AgentRole;
  period: {
    start: Date;
    end: Date;
  };

  // Success metrics
  totalTasks: number;
  successfulTasks: number;
  partialTasks: number;
  failedTasks: number;
  successRate: number; // 0-1

  // Quality metrics
  averageQualityScore: number; // 0-100
  qualityTrend: 'improving' | 'stable' | 'declining';
  validationPassRate: number; // 0-1

  // Efficiency metrics
  averageDuration: number; // milliseconds
  averageRetries: number;
  peerAssistanceRate: number; // 0-1

  // Learning metrics
  experiencesGenerated: number;
  patternsDiscovered: number;
  experienceReuseRate: number; // 0-1

  // Evolution metrics
  learningRate: number; // How fast the agent improves
  adaptationScore: number; // How well it adapts to new situations

  // Work type breakdown
  workTypeMetrics: Record<WorkType, WorkTypeMetrics>;
}

/**
 * Metrics for a specific work type
 */
export interface WorkTypeMetrics {
  workType: WorkType;
  taskCount: number;
  successRate: number;
  averageQuality: number;
  averageDuration: number;
}

// ============================================================================
// EVOLUTION CONFIGURATION
// ============================================================================

/**
 * Configuration for agent evolution behavior
 */
export interface EvolutionConfig {
  /** How quickly the agent adapts to new patterns (0-1) */
  learningRate: number;

  /** How much weight past experiences have in decisions (0-1) */
  experienceWeight: number;

  /** How much the agent explores vs exploits known patterns (0-1) */
  explorationRate: number;

  /** How deep the attribution analysis goes (1-5) */
  attributionDepth: number;

  /** Minimum confidence to use an experience (0-1) */
  minExperienceConfidence: number;

  /** Maximum experiences to consider per decision */
  maxExperiencesToConsider: number;

  /** Enable self-questioning (automatic task generation) */
  selfQuestioningEnabled: boolean;

  /** Enable self-navigating (experience-guided exploration) */
  selfNavigatingEnabled: boolean;

  /** Enable self-attributing (outcome analysis) */
  selfAttributingEnabled: boolean;
}

/**
 * Default evolution configuration
 */
export const DEFAULT_EVOLUTION_CONFIG: EvolutionConfig = {
  learningRate: 0.1,
  experienceWeight: 0.7,
  explorationRate: 0.2,
  attributionDepth: 3,
  minExperienceConfidence: 0.6,
  maxExperiencesToConsider: 10,
  selfQuestioningEnabled: true,
  selfNavigatingEnabled: true,
  selfAttributingEnabled: true
};

// ============================================================================
// VALIDATION TYPES (5-Phase Pipeline)
// ============================================================================

/**
 * Validation phases in the pipeline
 */
export enum ValidationPhase {
  LINTING = 'linting',
  TYPE_CHECK = 'type_check',
  STYLE = 'style',
  UNIT_TESTS = 'unit_tests',
  E2E_TESTS = 'e2e_tests'
}

/**
 * Tools for each validation phase
 */
export const VALIDATION_TOOLS: Record<ValidationPhase, { python: string; typescript: string }> = {
  [ValidationPhase.LINTING]: { python: 'ruff', typescript: 'eslint' },
  [ValidationPhase.TYPE_CHECK]: { python: 'mypy', typescript: 'tsc' },
  [ValidationPhase.STYLE]: { python: 'black', typescript: 'prettier' },
  [ValidationPhase.UNIT_TESTS]: { python: 'pytest', typescript: 'jest' },
  [ValidationPhase.E2E_TESTS]: { python: 'pytest+httpx', typescript: 'jest+supertest' }
};

/**
 * Result of a validation phase
 */
export interface ValidationPhaseResult {
  phase: ValidationPhase;
  passed: boolean;
  duration: number;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  fixSuggestions: string[];
}

/**
 * Validation error
 */
export interface ValidationError {
  phase: ValidationPhase;
  file: string;
  line?: number;
  column?: number;
  message: string;
  code?: string;
  severity: 'error' | 'critical';
  autoFixable: boolean;
}

/**
 * Validation warning
 */
export interface ValidationWarning {
  phase: ValidationPhase;
  file: string;
  line?: number;
  message: string;
  code?: string;
}

/**
 * Complete validation result
 */
export interface ValidationResult {
  success: boolean;
  phases: ValidationPhaseResult[];
  totalDuration: number;
  totalErrors: number;
  totalWarnings: number;
  coveragePercent?: number;
  iterations: number;
  finalCode?: string;
}

/**
 * Validation configuration per agent
 */
export interface ValidationConfig {
  phases: ValidationPhase[];
  maxIterations: number;
  stopOnFirstFailure: boolean;
  requiredCoverage?: number;
  regressionTestRequired?: boolean;
  timeout: number; // milliseconds per phase
}

/**
 * Default validation configs per agent role
 */
export const AGENT_VALIDATION_CONFIGS: Record<AgentRole, ValidationConfig> = {
  [AgentRole.FEATURE_ARCHITECT]: {
    phases: [ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK, ValidationPhase.STYLE, ValidationPhase.UNIT_TESTS, ValidationPhase.E2E_TESTS],
    maxIterations: 3,
    stopOnFirstFailure: false,
    requiredCoverage: 80,
    regressionTestRequired: false,
    timeout: 60000
  },
  [AgentRole.MAINTENANCE_SPECIALIST]: {
    phases: [ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK, ValidationPhase.UNIT_TESTS],
    maxIterations: 2,
    stopOnFirstFailure: false,
    requiredCoverage: 70,
    regressionTestRequired: false,
    timeout: 60000
  },
  [AgentRole.QUALITY_INSPECTOR]: {
    phases: [ValidationPhase.LINTING, ValidationPhase.TYPE_CHECK, ValidationPhase.STYLE],
    maxIterations: 1,
    stopOnFirstFailure: true,
    timeout: 30000
  },
  [AgentRole.BUG_HUNTER]: {
    phases: [ValidationPhase.LINTING, ValidationPhase.UNIT_TESTS, ValidationPhase.E2E_TESTS],
    maxIterations: 3,
    stopOnFirstFailure: false,
    regressionTestRequired: true,
    timeout: 90000
  },
  [AgentRole.ESTIMATION_ENGINE]: {
    phases: [],
    maxIterations: 0,
    stopOnFirstFailure: false,
    timeout: 0
  },
  [AgentRole.TEST_ENGINEER]: {
    phases: [ValidationPhase.UNIT_TESTS],
    maxIterations: 1,
    stopOnFirstFailure: false,
    timeout: 120000
  },
  [AgentRole.MIGRATION_ARCHITECT]: {
    phases: [ValidationPhase.E2E_TESTS],
    maxIterations: 2,
    stopOnFirstFailure: false,
    timeout: 180000
  },
  [AgentRole.DOCUMENTATION_WRITER]: {
    phases: [ValidationPhase.LINTING],
    maxIterations: 1,
    stopOnFirstFailure: false,
    timeout: 30000
  },
  [AgentRole.PRODUCT_OWNER]: {
    phases: [ValidationPhase.LINTING],
    maxIterations: 1,
    stopOnFirstFailure: false,
    timeout: 30000
  },
  [AgentRole.PROJECT_LEAD]: {
    phases: [],
    maxIterations: 0,
    stopOnFirstFailure: false,
    timeout: 0
  }
};

// ============================================================================
// EVOLVING AGENT INTERFACE
// ============================================================================

/**
 * Evolution capabilities for an agent
 */
export interface EvolutionCapabilities {
  /**
   * Consult past experiences for guidance on current task
   */
  consultExperience(context: TaskContext): Promise<Guidance>;

  /**
   * Log the outcome of a completed task
   */
  logOutcome(result: TaskResult): Promise<Experience>;

  /**
   * Receive and process attribution feedback
   */
  receiveFeedback(attribution: Attribution): Promise<void>;

  /**
   * Get current performance metrics
   */
  getPerformanceMetrics(): Promise<PerformanceMetrics>;

  /**
   * Generate self-questioning tasks (what should I learn?)
   */
  generateLearningTasks(): Promise<TaskContext[]>;

  /**
   * Update evolution parameters based on performance
   */
  adaptEvolutionConfig(): Promise<EvolutionConfig>;
}

/**
 * Validation capabilities for an agent
 */
export interface ValidationCapabilities {
  /**
   * Run validation pipeline on code
   */
  runValidation(code: string, language: 'python' | 'typescript'): Promise<ValidationResult>;

  /**
   * Iterate until code passes validation
   */
  iterateUntilValid(
    code: string,
    language: 'python' | 'typescript',
    maxIterations?: number
  ): Promise<{ code: string; result: ValidationResult }>;

  /**
   * Request fix for validation errors
   */
  requestFix(
    code: string,
    errors: ValidationError[],
    language: 'python' | 'typescript'
  ): Promise<string>;

  /**
   * Get validation config for this agent
   */
  getValidationConfig(): ValidationConfig;
}

/**
 * Extended agent interface with evolution capabilities
 */
export interface EvolvingAgent extends AgentConfig {
  /** Unique identifier for this agent instance */
  agentId: string;

  /** Evolution capabilities */
  evolution: EvolutionCapabilities;

  /** Validation capabilities */
  validation: ValidationCapabilities;

  /** Evolution configuration */
  evolutionConfig: EvolutionConfig;

  /** Validation configuration */
  validationConfig: ValidationConfig;

  /** Current performance metrics (cached) */
  currentMetrics?: PerformanceMetrics;

  /** Whether this agent is currently learning */
  isLearning: boolean;

  /** Last time the agent evolved its config */
  lastEvolutionUpdate?: Date;
}

// ============================================================================
// EXPERIENCE STORE TYPES (ChromaDB Collections)
// ============================================================================

/**
 * ChromaDB collection names for experience store
 */
export enum ExperienceCollection {
  /** Cross-task learnings per agent */
  AGENT_EXPERIENCES = 'agent_experiences',

  /** Successful patterns that can be reused */
  SUCCESSFUL_PATTERNS = 'successful_patterns',

  /** Failure analysis for learning */
  FAILURE_ANALYSIS = 'failure_analysis',

  /** Estimation accuracy tracking */
  ESTIMATION_ACCURACY = 'estimation_accuracy',

  /** Code quality metrics over time */
  QUALITY_METRICS = 'quality_metrics'
}

/**
 * Successful pattern stored in ChromaDB
 */
export interface SuccessfulPattern {
  id: string;
  name: string;
  description: string;
  workTypes: WorkType[];
  applicableContexts: string[];
  steps: string[];
  successCount: number;
  failureCount: number;
  averageQuality: number;
  createdAt: Date;
  lastUsed: Date;
  createdBy: string; // agentId
  embedding?: number[];
}

/**
 * Failure analysis record
 */
export interface FailureAnalysis {
  id: string;
  agentId: string;
  taskId: string;
  workType: WorkType;
  failureType: 'validation' | 'timeout' | 'quality' | 'logic' | 'unknown';
  rootCause: string;
  contributingFactors: string[];
  preventionStrategies: string[];
  similarFailures: string[]; // IDs of related failures
  timestamp: Date;
  embedding?: number[];
}

/**
 * Estimation accuracy record
 */
export interface EstimationAccuracy {
  id: string;
  agentId: string;
  taskId: string;
  workType: WorkType;
  estimatedHours: number;
  actualHours: number;
  estimatedComplexity: 'low' | 'medium' | 'high';
  actualComplexity: 'low' | 'medium' | 'high';
  factors: string[];
  underestimatedAspects?: string[];
  overestimatedAspects?: string[];
  timestamp: Date;
}

/**
 * Quality metrics record
 */
export interface QualityMetricsRecord {
  id: string;
  agentId: string;
  taskId: string;
  workType: WorkType;
  codeQualityScore: number;
  testCoverage?: number;
  lintingErrors: number;
  typeErrors: number;
  securityIssues: number;
  performanceScore?: number;
  documentationScore?: number;
  timestamp: Date;
}

// ============================================================================
// SAFETY GUARDRAILS
// ============================================================================

/**
 * Actions that require human approval
 */
export enum ApprovalRequired {
  POLICY_CHANGE = 'policy_change',
  NEW_PATTERN_ADD = 'new_pattern_add',
  CROSS_WORKFLOW_RULE = 'cross_workflow_rule',
  MAJOR_BEHAVIOR_CHANGE = 'major_behavior_change',
  CONFIDENCE_OVERRIDE = 'confidence_override'
}

/**
 * Rollback trigger conditions
 */
export interface RollbackTrigger {
  metric: 'success_rate' | 'quality_score' | 'estimation_error';
  threshold: number; // Percentage drop that triggers rollback
  windowSize: number; // Number of tasks to consider
  enabled: boolean;
}

/**
 * Default rollback triggers
 */
export const DEFAULT_ROLLBACK_TRIGGERS: RollbackTrigger[] = [
  { metric: 'success_rate', threshold: 10, windowSize: 20, enabled: true },
  { metric: 'quality_score', threshold: 15, windowSize: 20, enabled: true },
  { metric: 'estimation_error', threshold: 20, windowSize: 10, enabled: true }
];

/**
 * Safety guardrails configuration
 */
export interface SafetyGuardrails {
  /** Actions allowed without human approval */
  automaticActions: string[];

  /** Actions requiring human approval */
  approvalRequired: ApprovalRequired[];

  /** Rollback triggers */
  rollbackTriggers: RollbackTrigger[];

  /** Maximum learning rate allowed */
  maxLearningRate: number;

  /** Minimum experiences before making policy changes */
  minExperiencesForPolicyChange: number;

  /** Enable rollback capability */
  rollbackEnabled: boolean;
}

/**
 * Default safety guardrails (Balanced Mode)
 */
export const DEFAULT_SAFETY_GUARDRAILS: SafetyGuardrails = {
  automaticActions: [
    'experience_logging',
    'pattern_matching',
    'outcome_tracking',
    'minor_weight_updates'
  ],
  approvalRequired: [
    ApprovalRequired.POLICY_CHANGE,
    ApprovalRequired.NEW_PATTERN_ADD,
    ApprovalRequired.CROSS_WORKFLOW_RULE,
    ApprovalRequired.MAJOR_BEHAVIOR_CHANGE
  ],
  rollbackTriggers: DEFAULT_ROLLBACK_TRIGGERS,
  maxLearningRate: 0.3,
  minExperiencesForPolicyChange: 50,
  rollbackEnabled: true
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Calculate experience relevance score
 */
export function calculateExperienceRelevance(
  experience: Experience,
  context: TaskContext
): number {
  let score = 0;

  // Work type match (highest weight)
  if (experience.workType === context.workType) {
    score += 0.4;
  }

  // Complexity match
  const complexityMap = { low: 1, medium: 2, high: 3 };
  const expComplexity = experience.qualityScore > 80 ? 'high' :
                        experience.qualityScore > 50 ? 'medium' : 'low';
  if (expComplexity === context.complexity) {
    score += 0.2;
  }

  // Outcome weight (successful experiences weighted higher)
  if (experience.outcome === 'success') {
    score += 0.2;
  } else if (experience.outcome === 'partial') {
    score += 0.1;
  }

  // Recency bonus (more recent experiences are more relevant)
  const daysSince = (Date.now() - experience.timestamp.getTime()) / (1000 * 60 * 60 * 24);
  if (daysSince < 7) {
    score += 0.1;
  } else if (daysSince < 30) {
    score += 0.05;
  }

  // Quality bonus
  if (experience.qualityScore > 80) {
    score += 0.1;
  }

  return Math.min(1, score);
}

/**
 * Check if rollback should be triggered
 */
export function shouldTriggerRollback(
  metrics: PerformanceMetrics,
  previousMetrics: PerformanceMetrics,
  triggers: RollbackTrigger[]
): { shouldRollback: boolean; reason?: string } {
  for (const trigger of triggers) {
    if (!trigger.enabled) continue;

    let current: number;
    let previous: number;

    switch (trigger.metric) {
      case 'success_rate':
        current = metrics.successRate * 100;
        previous = previousMetrics.successRate * 100;
        break;
      case 'quality_score':
        current = metrics.averageQualityScore;
        previous = previousMetrics.averageQualityScore;
        break;
      case 'estimation_error':
        // Higher is worse for estimation error
        current = 100 - metrics.adaptationScore * 100;
        previous = 100 - previousMetrics.adaptationScore * 100;
        break;
      default:
        continue;
    }

    const drop = previous - current;
    if (drop > trigger.threshold) {
      return {
        shouldRollback: true,
        reason: `${trigger.metric} dropped by ${drop.toFixed(1)}% (threshold: ${trigger.threshold}%)`
      };
    }
  }

  return { shouldRollback: false };
}

/**
 * Create default evolving agent config
 */
export function createEvolvingAgentConfig(
  agentConfig: AgentConfig,
  agentId: string
): Partial<EvolvingAgent> {
  return {
    ...agentConfig,
    agentId,
    evolutionConfig: DEFAULT_EVOLUTION_CONFIG,
    validationConfig: AGENT_VALIDATION_CONFIGS[agentConfig.role],
    isLearning: false
  };
}
