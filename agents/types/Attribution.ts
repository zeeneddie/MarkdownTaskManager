/**
 * Attribution Types for Self-Attributing Agents
 * Week 21-22 Implementation
 */

// ============================================================================
// Core Attribution Types
// ============================================================================

export type OutcomeType = 'SUCCESS' | 'FAILURE' | 'PARTIAL';
export type ImpactLevel = 'CRITICAL' | 'IMPORTANT' | 'MINOR' | 'NEUTRAL' | 'NEGATIVE';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export interface Attribution {
  id: string;
  taskId: string;
  workflowId: string;
  agentId: string;
  agentName: string;
  outcome: OutcomeType;
  keySteps: AttributedStep[];
  causalFactors: CausalFactor[];
  qualityGateResults: QualityGateAttribution[];
  validationHistory: ValidationAttribution[];
  confidence: number; // 0.0 - 1.0
  confidenceLevel: ConfidenceLevel;
  createdAt: Date;
  analyzedAt: Date;
}

export interface AttributedStep {
  stepId: string;
  stepName: string;
  agentId: string;
  impact: ImpactLevel;
  impactScore: number; // -1.0 to 1.0
  reasoning: string;
  duration: number; // milliseconds
  retryCount: number;
  experienceUsed: boolean;
  patternApplied?: string;
}

export interface CausalFactor {
  factorId: string;
  factorType: CausalFactorType;
  description: string;
  contribution: number; // -1.0 to 1.0
  evidence: string[];
  relatedSteps: string[];
}

export type CausalFactorType =
  | 'PATTERN_REUSE'
  | 'EARLY_VALIDATION'
  | 'CLEAR_SPECIFICATION'
  | 'TEST_COVERAGE'
  | 'SECURITY_SCAN'
  | 'MISSING_EDGE_CASE'
  | 'INCOMPLETE_VALIDATION'
  | 'DEPENDENCY_ISSUE'
  | 'AMBIGUOUS_REQUIREMENT'
  | 'RESOURCE_CONSTRAINT';

// ============================================================================
// Quality Gate Attribution
// ============================================================================

export interface QualityGateAttribution {
  gateType: string;
  gateName: string;
  passed: boolean;
  issuesCaught: number;
  falsePositives: number;
  falseNegatives: number;
  effectiveness: number;
  recommendedAction?: string;
}

// ============================================================================
// Validation Attribution
// ============================================================================

export interface ValidationAttribution {
  phase: ValidationPhase;
  iteration: number;
  passed: boolean;
  errors: ValidationError[];
  fixApplied?: string;
  timeToFix: number;
}

export type ValidationPhase = 'LINTING' | 'TYPE_CHECK' | 'STYLE' | 'UNIT_TEST' | 'E2E_TEST';

export interface ValidationError {
  code: string;
  message: string;
  file?: string;
  line?: number;
  severity: 'ERROR' | 'WARNING' | 'INFO';
}

// ============================================================================
// Agent Performance Metrics
// ============================================================================

export interface AgentPerformanceMetrics {
  agentId: string;
  agentName: string;
  period: {
    start: Date;
    end: Date;
  };
  totalTasks: number;
  successfulTasks: number;
  failedTasks: number;
  partialTasks: number;
  successRate: number;
  averageConfidence: number;
  topSuccessFactors: RankedFactor[];
  topFailurePatterns: RankedFactor[];
  qualityGateEffectiveness: QualityGateStats[];
  improvementTrend: number;
}

export interface RankedFactor {
  factor: CausalFactorType;
  description: string;
  frequency: number;
  averageContribution: number;
  rank: number;
}

export interface QualityGateStats {
  gateType: string;
  totalChecks: number;
  issuesCaught: number;
  falsePositiveRate: number;
  falseNegativeRate: number;
  effectiveness: number;
}

// ============================================================================
// Feedback Types
// ============================================================================

export interface AttributionFeedback {
  attributionId: string;
  agentId: string;
  feedbackType: FeedbackType;
  lessons: Lesson[];
  recommendedAdjustments: Adjustment[];
  deliveredAt: Date;
}

export type FeedbackType = 'SUCCESS_REINFORCEMENT' | 'FAILURE_CORRECTION' | 'PATTERN_UPDATE';

export interface Lesson {
  lessonId: string;
  lessonType: 'DO_MORE' | 'DO_LESS' | 'AVOID' | 'TRY_ALTERNATIVE';
  description: string;
  context: string;
  confidence: number;
}

export interface Adjustment {
  adjustmentType: 'WEIGHT_UPDATE' | 'PATTERN_ADD' | 'PATTERN_REMOVE' | 'THRESHOLD_CHANGE';
  target: string;
  currentValue: number | string;
  recommendedValue: number | string;
  reasoning: string;
}

// ============================================================================
// Input Data Types
// ============================================================================

export interface StepData {
  id: string;
  name: string;
  agentId: string;
  succeeded: boolean;
  duration: number;
  expectedDuration: number;
  retryCount?: number;
  experienceConsulted?: boolean;
  patternUsed?: string;
  isCriticalPath?: boolean;
}

export interface QualityGateResult {
  gateType: string;
  gateName: string;
  passed: boolean;
  issuesCaught: number;
  falsePositives?: number;
  totalChecks: number;
}

export interface ValidationResult {
  phase: string;
  iteration: number;
  passed: boolean;
  errors: Array<{
    code: string;
    message: string;
    file?: string;
    line?: number;
    severity: string;
  }>;
  fixApplied?: string;
  timeToFix?: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

export function calculateConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.8) return 'HIGH';
  if (confidence >= 0.5) return 'MEDIUM';
  return 'LOW';
}

export function calculateOverallImpact(steps: AttributedStep[]): number {
  if (steps.length === 0) return 0;
  const totalImpact = steps.reduce((sum, step) => sum + step.impactScore, 0);
  return totalImpact / steps.length;
}

export function rankFactors(factors: CausalFactor[]): RankedFactor[] {
  return factors
    .map((f, index) => ({
      factor: f.factorType,
      description: f.description,
      frequency: 1,
      averageContribution: f.contribution,
      rank: index + 1
    }))
    .sort((a, b) => Math.abs(b.averageContribution) - Math.abs(a.averageContribution));
}

export function impactLevelToScore(impact: ImpactLevel): number {
  const scores: Record<ImpactLevel, number> = {
    'CRITICAL': 1.0,
    'IMPORTANT': 0.7,
    'MINOR': 0.3,
    'NEUTRAL': 0,
    'NEGATIVE': -0.5
  };
  return scores[impact];
}
