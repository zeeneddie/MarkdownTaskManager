# Week 21-22 Implementation Plan: Self-Attributing

**Fase**: C (AgentEvolver Integration)
**Doel**: Analyseer wat tot succes/falen leidde
**Timeline**: Week 21-22
**Estimated Lines**: ~2,200

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SELF-ATTRIBUTING ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   OUTCOME    │───>│ ATTRIBUTION  │───>│   FEEDBACK LOOP      │  │
│  │   TRACKER    │    │  PROCESSOR   │    │   (to agents)        │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         │                   │                      │                │
│         ▼                   ▼                      ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  ChromaDB    │    │   QUALITY    │    │    DASHBOARD         │  │
│  │  (outcomes)  │    │   GATE STATS │    │  (visualization)     │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
backend/
├── agents/
│   ├── lib/
│   │   └── attributionProcessor.ts      # NEW (~600 lines)
│   ├── integrations/
│   │   └── attributionIntegration.ts    # NEW (~300 lines)
│   └── types/
│       └── Attribution.ts               # NEW (~150 lines)
├── app/
│   ├── api/
│   │   └── attribution.py               # NEW (~350 lines)
│   ├── services/
│   │   └── attribution_service.py       # NEW (~400 lines)
│   ├── models/
│   │   └── attribution.py               # NEW (~100 lines)
│   └── schemas/
│       └── attribution.py               # NEW (~150 lines)
├── alembic/versions/
│   └── 008_add_attribution_tables.py    # NEW (~80 lines)
└── tests/
    └── api/week21/
        ├── test_attribution_api.py      # NEW (~200 lines)
        └── test_attribution_service.py  # NEW (~150 lines)

frontend/
└── attribution-dashboard.html           # NEW (~500 lines)
```

---

## Day-by-Day Breakdown

### Week 21

| Day | Focus | Deliverables | Hours |
|-----|-------|--------------|-------|
| 1 | Types + Models | Attribution.ts, attribution.py (models/schemas) | 8h |
| 2 | Attribution Processor | attributionProcessor.ts (core logic) | 8h |
| 3 | Python Service | attribution_service.py | 8h |
| 4 | API Endpoints | attribution.py (REST API) | 6h |
| 5 | Database Migration | Alembic + ChromaDB collections | 4h |

### Week 22

| Day | Focus | Deliverables | Hours |
|-----|-------|--------------|-------|
| 1 | Dashboard UI | attribution-dashboard.html (Part 1) | 8h |
| 2 | Dashboard Complete | Dashboard + Charts | 6h |
| 3 | Agent Integration | attributionIntegration.ts | 8h |
| 4 | Testing | All test files | 6h |
| 5 | Documentation + Polish | README updates, bug fixes | 4h |

---

## Code Skeletons

### 1. Types Definition (`backend/agents/types/Attribution.ts`)

```typescript
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
  experienceUsed: boolean; // Did agent consult experience store?
  patternApplied?: string; // Which pattern was used?
}

export interface CausalFactor {
  factorId: string;
  factorType: CausalFactorType;
  description: string;
  contribution: number; // -1.0 to 1.0 (negative = caused failure)
  evidence: string[];
  relatedSteps: string[]; // stepIds
}

export type CausalFactorType =
  | 'PATTERN_REUSE'        // Used successful pattern from experience
  | 'EARLY_VALIDATION'     // Caught issues early
  | 'CLEAR_SPECIFICATION'  // Good input specification
  | 'TEST_COVERAGE'        // Comprehensive testing
  | 'SECURITY_SCAN'        // Security checks
  | 'MISSING_EDGE_CASE'    // Failure: missed edge case
  | 'INCOMPLETE_VALIDATION'// Failure: validation gaps
  | 'DEPENDENCY_ISSUE'     // Failure: external dependencies
  | 'AMBIGUOUS_REQUIREMENT'// Failure: unclear requirements
  | 'RESOURCE_CONSTRAINT'; // Failure: time/memory limits

// ============================================================================
// Quality Gate Attribution
// ============================================================================

export interface QualityGateAttribution {
  gateType: string;
  gateName: string;
  passed: boolean;
  issuesCaught: number;
  falsePositives: number;
  falseNegatives: number; // Known only after production feedback
  effectiveness: number; // 0.0 - 1.0
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
  timeToFix: number; // milliseconds
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
  successRate: number; // percentage
  averageConfidence: number;
  topSuccessFactors: RankedFactor[];
  topFailurePatterns: RankedFactor[];
  qualityGateEffectiveness: QualityGateStats[];
  improvementTrend: number; // percentage change vs previous period
}

export interface RankedFactor {
  factor: CausalFactorType;
  description: string;
  frequency: number; // how often this factor appeared
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
      frequency: 1, // Will be aggregated later
      averageContribution: f.contribution,
      rank: index + 1
    }))
    .sort((a, b) => Math.abs(b.averageContribution) - Math.abs(a.averageContribution));
}
```

---

### 2. Attribution Processor (`backend/agents/lib/attributionProcessor.ts`)

```typescript
/**
 * Attribution Processor - Core Logic for Self-Attributing Agents
 * Week 21-22 Implementation
 *
 * Analyzes task outcomes and determines which steps/factors led to success or failure
 */

import {
  Attribution,
  AttributedStep,
  CausalFactor,
  CausalFactorType,
  OutcomeType,
  ImpactLevel,
  QualityGateAttribution,
  ValidationAttribution,
  AgentPerformanceMetrics,
  AttributionFeedback,
  Lesson,
  Adjustment,
  calculateConfidenceLevel,
  calculateOverallImpact,
  rankFactors
} from '../types/Attribution';
import { ChromaClient, Collection } from 'chromadb';

// ============================================================================
// Configuration
// ============================================================================

interface AttributionConfig {
  chromaHost: string;
  chromaPort: number;
  minConfidenceThreshold: number;
  maxFactorsToTrack: number;
  lookbackPeriodDays: number;
}

const DEFAULT_CONFIG: AttributionConfig = {
  chromaHost: 'localhost',
  chromaPort: 8001,
  minConfidenceThreshold: 0.5,
  maxFactorsToTrack: 10,
  lookbackPeriodDays: 30
};

// ============================================================================
// Attribution Processor Class
// ============================================================================

export class AttributionProcessor {
  private config: AttributionConfig;
  private chromaClient: ChromaClient;
  private outcomeCollection: Collection | null = null;
  private attributionCollection: Collection | null = null;

  constructor(config: Partial<AttributionConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.chromaClient = new ChromaClient({
      path: `http://${this.config.chromaHost}:${this.config.chromaPort}`
    });
  }

  /**
   * Initialize ChromaDB collections
   */
  async initialize(): Promise<void> {
    try {
      this.outcomeCollection = await this.chromaClient.getOrCreateCollection({
        name: 'task_outcomes',
        metadata: { description: 'Task outcome tracking for attribution' }
      });

      this.attributionCollection = await this.chromaClient.getOrCreateCollection({
        name: 'attributions',
        metadata: { description: 'Attribution analysis results' }
      });

      console.log('[AttributionProcessor] Initialized successfully');
    } catch (error) {
      console.error('[AttributionProcessor] Initialization failed:', error);
      throw error;
    }
  }

  // ==========================================================================
  // Core Attribution Logic
  // ==========================================================================

  /**
   * Analyze a completed task and generate attribution
   */
  async analyzeTask(
    taskId: string,
    workflowId: string,
    agentId: string,
    agentName: string,
    outcome: OutcomeType,
    steps: StepData[],
    qualityGateResults: QualityGateResult[],
    validationHistory: ValidationResult[]
  ): Promise<Attribution> {
    console.log(`[AttributionProcessor] Analyzing task ${taskId} for agent ${agentName}`);

    // Step 1: Analyze individual steps
    const attributedSteps = await this.analyzeSteps(steps, outcome);

    // Step 2: Extract causal factors
    const causalFactors = await this.extractCausalFactors(
      attributedSteps,
      qualityGateResults,
      validationHistory,
      outcome
    );

    // Step 3: Analyze quality gate effectiveness
    const qualityGateAttributions = this.analyzeQualityGates(qualityGateResults);

    // Step 4: Analyze validation history
    const validationAttributions = this.analyzeValidationHistory(validationHistory);

    // Step 5: Calculate confidence
    const confidence = this.calculateAttributionConfidence(
      attributedSteps,
      causalFactors,
      outcome
    );

    // Step 6: Build attribution object
    const attribution: Attribution = {
      id: `attr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      taskId,
      workflowId,
      agentId,
      agentName,
      outcome,
      keySteps: attributedSteps,
      causalFactors,
      qualityGateResults: qualityGateAttributions,
      validationHistory: validationAttributions,
      confidence,
      confidenceLevel: calculateConfidenceLevel(confidence),
      createdAt: new Date(),
      analyzedAt: new Date()
    };

    // Step 7: Store attribution
    await this.storeAttribution(attribution);

    return attribution;
  }

  /**
   * Analyze individual steps and assign impact scores
   */
  private async analyzeSteps(
    steps: StepData[],
    outcome: OutcomeType
  ): Promise<AttributedStep[]> {
    const attributedSteps: AttributedStep[] = [];

    for (const step of steps) {
      const impact = this.calculateStepImpact(step, outcome);
      const impactScore = this.calculateImpactScore(step, outcome);

      attributedSteps.push({
        stepId: step.id,
        stepName: step.name,
        agentId: step.agentId,
        impact,
        impactScore,
        reasoning: this.generateStepReasoning(step, impact, outcome),
        duration: step.duration,
        retryCount: step.retryCount || 0,
        experienceUsed: step.experienceConsulted || false,
        patternApplied: step.patternUsed
      });
    }

    // Sort by absolute impact score (most impactful first)
    return attributedSteps.sort(
      (a, b) => Math.abs(b.impactScore) - Math.abs(a.impactScore)
    );
  }

  /**
   * Calculate impact level for a step
   */
  private calculateStepImpact(step: StepData, outcome: OutcomeType): ImpactLevel {
    // Critical: Step that directly caused success/failure
    if (step.isCriticalPath) {
      if (outcome === 'SUCCESS' && step.succeeded) return 'CRITICAL';
      if (outcome === 'FAILURE' && !step.succeeded) return 'CRITICAL';
    }

    // Important: Step that significantly contributed
    if (step.retryCount > 0 && step.succeeded) return 'IMPORTANT';
    if (step.experienceConsulted && step.succeeded) return 'IMPORTANT';

    // Minor: Step that had some effect
    if (step.duration > step.expectedDuration * 1.5) return 'MINOR';

    // Negative: Step that caused problems
    if (!step.succeeded && outcome === 'FAILURE') return 'NEGATIVE';

    return 'NEUTRAL';
  }

  /**
   * Calculate numeric impact score (-1.0 to 1.0)
   */
  private calculateImpactScore(step: StepData, outcome: OutcomeType): number {
    let score = 0;

    // Base score from success/failure
    if (step.succeeded) {
      score += 0.3;
    } else {
      score -= 0.5;
    }

    // Bonus for experience usage
    if (step.experienceConsulted && step.succeeded) {
      score += 0.2;
    }

    // Bonus for pattern application
    if (step.patternUsed && step.succeeded) {
      score += 0.15;
    }

    // Penalty for retries
    score -= step.retryCount * 0.1;

    // Penalty for timeout/slow execution
    if (step.duration > step.expectedDuration * 2) {
      score -= 0.1;
    }

    // Critical path multiplier
    if (step.isCriticalPath) {
      score *= 1.5;
    }

    // Clamp to [-1, 1]
    return Math.max(-1, Math.min(1, score));
  }

  /**
   * Generate human-readable reasoning for step impact
   */
  private generateStepReasoning(
    step: StepData,
    impact: ImpactLevel,
    outcome: OutcomeType
  ): string {
    const reasons: string[] = [];

    if (step.experienceConsulted && step.succeeded) {
      reasons.push('Successfully applied learned experience');
    }

    if (step.patternUsed) {
      reasons.push(`Applied pattern: ${step.patternUsed}`);
    }

    if (step.retryCount > 0) {
      reasons.push(`Required ${step.retryCount} retries before ${step.succeeded ? 'succeeding' : 'failing'}`);
    }

    if (step.isCriticalPath) {
      reasons.push('On critical path - directly affected outcome');
    }

    if (!step.succeeded && outcome === 'FAILURE') {
      reasons.push('Step failure contributed to overall task failure');
    }

    return reasons.length > 0 ? reasons.join('. ') : 'Standard execution';
  }

  /**
   * Extract causal factors from analysis
   */
  private async extractCausalFactors(
    steps: AttributedStep[],
    qualityGates: QualityGateResult[],
    validations: ValidationResult[],
    outcome: OutcomeType
  ): Promise<CausalFactor[]> {
    const factors: CausalFactor[] = [];

    // Analyze experience usage
    const experienceSteps = steps.filter(s => s.experienceUsed);
    if (experienceSteps.length > 0) {
      const avgImpact = experienceSteps.reduce((sum, s) => sum + s.impactScore, 0) / experienceSteps.length;
      factors.push({
        factorId: `factor_${Date.now()}_exp`,
        factorType: 'PATTERN_REUSE',
        description: `Experience consulted in ${experienceSteps.length} steps`,
        contribution: avgImpact > 0 ? 0.3 : -0.1,
        evidence: experienceSteps.map(s => s.stepName),
        relatedSteps: experienceSteps.map(s => s.stepId)
      });
    }

    // Analyze early validation
    const earlyValidations = validations.filter(v => v.iteration === 1 && v.passed);
    if (earlyValidations.length > 0) {
      factors.push({
        factorId: `factor_${Date.now()}_eval`,
        factorType: 'EARLY_VALIDATION',
        description: `${earlyValidations.length} validations passed on first try`,
        contribution: 0.25,
        evidence: earlyValidations.map(v => v.phase),
        relatedSteps: []
      });
    }

    // Analyze quality gate effectiveness
    const effectiveGates = qualityGates.filter(g => g.issuesCaught > 0);
    if (effectiveGates.length > 0) {
      factors.push({
        factorId: `factor_${Date.now()}_qg`,
        factorType: 'SECURITY_SCAN',
        description: `Quality gates caught ${effectiveGates.reduce((sum, g) => sum + g.issuesCaught, 0)} issues`,
        contribution: 0.2,
        evidence: effectiveGates.map(g => `${g.gateName}: ${g.issuesCaught} issues`),
        relatedSteps: []
      });
    }

    // Analyze failure patterns
    if (outcome === 'FAILURE') {
      const failedSteps = steps.filter(s => s.impactScore < 0);

      // Check for missing edge cases
      const edgeCaseFailures = failedSteps.filter(s =>
        s.reasoning.toLowerCase().includes('edge') ||
        s.reasoning.toLowerCase().includes('boundary')
      );
      if (edgeCaseFailures.length > 0) {
        factors.push({
          factorId: `factor_${Date.now()}_edge`,
          factorType: 'MISSING_EDGE_CASE',
          description: 'Edge cases not properly handled',
          contribution: -0.4,
          evidence: edgeCaseFailures.map(s => s.stepName),
          relatedSteps: edgeCaseFailures.map(s => s.stepId)
        });
      }

      // Check for validation gaps
      const failedValidations = validations.filter(v => !v.passed);
      if (failedValidations.length > 2) {
        factors.push({
          factorId: `factor_${Date.now()}_val`,
          factorType: 'INCOMPLETE_VALIDATION',
          description: `${failedValidations.length} validation phases failed`,
          contribution: -0.35,
          evidence: failedValidations.map(v => `${v.phase}: ${v.errors.length} errors`),
          relatedSteps: []
        });
      }
    }

    // Sort by absolute contribution
    return factors.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  }

  /**
   * Analyze quality gate effectiveness
   */
  private analyzeQualityGates(results: QualityGateResult[]): QualityGateAttribution[] {
    return results.map(result => ({
      gateType: result.gateType,
      gateName: result.gateName,
      passed: result.passed,
      issuesCaught: result.issuesCaught || 0,
      falsePositives: result.falsePositives || 0,
      falseNegatives: 0, // Updated later from production feedback
      effectiveness: this.calculateGateEffectiveness(result),
      recommendedAction: this.generateGateRecommendation(result)
    }));
  }

  /**
   * Calculate quality gate effectiveness score
   */
  private calculateGateEffectiveness(result: QualityGateResult): number {
    if (result.totalChecks === 0) return 0;

    const truePositiveRate = result.issuesCaught / Math.max(1, result.totalChecks);
    const falsePositivePenalty = (result.falsePositives || 0) * 0.1;

    return Math.max(0, Math.min(1, truePositiveRate - falsePositivePenalty));
  }

  /**
   * Generate recommendation for quality gate improvement
   */
  private generateGateRecommendation(result: QualityGateResult): string | undefined {
    if (result.falsePositives > result.issuesCaught) {
      return 'Consider relaxing gate rules - high false positive rate';
    }
    if (result.issuesCaught === 0 && result.totalChecks > 10) {
      return 'Gate may be too lenient - no issues caught';
    }
    return undefined;
  }

  /**
   * Analyze validation history
   */
  private analyzeValidationHistory(results: ValidationResult[]): ValidationAttribution[] {
    return results.map(result => ({
      phase: result.phase as any,
      iteration: result.iteration,
      passed: result.passed,
      errors: result.errors.map(e => ({
        code: e.code,
        message: e.message,
        file: e.file,
        line: e.line,
        severity: e.severity as any
      })),
      fixApplied: result.fixApplied,
      timeToFix: result.timeToFix || 0
    }));
  }

  /**
   * Calculate overall attribution confidence
   */
  private calculateAttributionConfidence(
    steps: AttributedStep[],
    factors: CausalFactor[],
    outcome: OutcomeType
  ): number {
    let confidence = 0.5; // Base confidence

    // More steps analyzed = higher confidence
    confidence += Math.min(0.2, steps.length * 0.02);

    // More factors identified = higher confidence
    confidence += Math.min(0.15, factors.length * 0.03);

    // Clear outcome (not partial) = higher confidence
    if (outcome !== 'PARTIAL') {
      confidence += 0.1;
    }

    // Steps with experience usage = higher confidence
    const experienceRatio = steps.filter(s => s.experienceUsed).length / Math.max(1, steps.length);
    confidence += experienceRatio * 0.1;

    return Math.min(1, confidence);
  }

  // ==========================================================================
  // Storage Operations
  // ==========================================================================

  /**
   * Store attribution in ChromaDB
   */
  private async storeAttribution(attribution: Attribution): Promise<void> {
    if (!this.attributionCollection) {
      throw new Error('Attribution collection not initialized');
    }

    const document = JSON.stringify(attribution);
    const metadata = {
      taskId: attribution.taskId,
      agentId: attribution.agentId,
      agentName: attribution.agentName,
      outcome: attribution.outcome,
      confidence: attribution.confidence,
      createdAt: attribution.createdAt.toISOString()
    };

    await this.attributionCollection.add({
      ids: [attribution.id],
      documents: [document],
      metadatas: [metadata]
    });

    console.log(`[AttributionProcessor] Stored attribution ${attribution.id}`);
  }

  // ==========================================================================
  // Feedback Generation
  // ==========================================================================

  /**
   * Generate feedback for an agent based on attribution
   */
  async generateFeedback(attribution: Attribution): Promise<AttributionFeedback> {
    const lessons = this.extractLessons(attribution);
    const adjustments = this.recommendAdjustments(attribution);

    const feedback: AttributionFeedback = {
      attributionId: attribution.id,
      agentId: attribution.agentId,
      feedbackType: attribution.outcome === 'SUCCESS'
        ? 'SUCCESS_REINFORCEMENT'
        : 'FAILURE_CORRECTION',
      lessons,
      recommendedAdjustments: adjustments,
      deliveredAt: new Date()
    };

    return feedback;
  }

  /**
   * Extract lessons from attribution
   */
  private extractLessons(attribution: Attribution): Lesson[] {
    const lessons: Lesson[] = [];

    // Lessons from successful patterns
    const successfulPatterns = attribution.keySteps
      .filter(s => s.impactScore > 0.2 && s.patternApplied);

    for (const step of successfulPatterns) {
      lessons.push({
        lessonId: `lesson_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        lessonType: 'DO_MORE',
        description: `Pattern "${step.patternApplied}" was effective in ${step.stepName}`,
        context: step.reasoning,
        confidence: Math.abs(step.impactScore)
      });
    }

    // Lessons from failures
    const failedSteps = attribution.keySteps
      .filter(s => s.impactScore < -0.2);

    for (const step of failedSteps) {
      lessons.push({
        lessonId: `lesson_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        lessonType: 'AVOID',
        description: `Step "${step.stepName}" caused issues`,
        context: step.reasoning,
        confidence: Math.abs(step.impactScore)
      });
    }

    // Lessons from causal factors
    for (const factor of attribution.causalFactors) {
      if (factor.contribution > 0.2) {
        lessons.push({
          lessonId: `lesson_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
          lessonType: 'DO_MORE',
          description: factor.description,
          context: factor.evidence.join(', '),
          confidence: factor.contribution
        });
      } else if (factor.contribution < -0.2) {
        lessons.push({
          lessonId: `lesson_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
          lessonType: 'AVOID',
          description: factor.description,
          context: factor.evidence.join(', '),
          confidence: Math.abs(factor.contribution)
        });
      }
    }

    return lessons.sort((a, b) => b.confidence - a.confidence);
  }

  /**
   * Recommend adjustments based on attribution
   */
  private recommendAdjustments(attribution: Attribution): Adjustment[] {
    const adjustments: Adjustment[] = [];

    // Recommend experience weight increase if experience helped
    const experienceHelpful = attribution.keySteps
      .filter(s => s.experienceUsed && s.impactScore > 0).length;

    if (experienceHelpful > 2) {
      adjustments.push({
        adjustmentType: 'WEIGHT_UPDATE',
        target: 'experienceWeight',
        currentValue: 0.5,
        recommendedValue: 0.7,
        reasoning: `Experience consultation was helpful in ${experienceHelpful} steps`
      });
    }

    // Recommend new pattern if successful approach identified
    const successfulNewApproach = attribution.keySteps
      .find(s => s.impactScore > 0.5 && !s.patternApplied);

    if (successfulNewApproach) {
      adjustments.push({
        adjustmentType: 'PATTERN_ADD',
        target: 'patterns',
        currentValue: 'none',
        recommendedValue: successfulNewApproach.stepName,
        reasoning: `Step "${successfulNewApproach.stepName}" was highly effective`
      });
    }

    return adjustments;
  }

  // ==========================================================================
  // Performance Metrics
  // ==========================================================================

  /**
   * Get performance metrics for an agent
   */
  async getAgentPerformanceMetrics(
    agentId: string,
    agentName: string,
    periodDays: number = 30
  ): Promise<AgentPerformanceMetrics> {
    if (!this.attributionCollection) {
      throw new Error('Attribution collection not initialized');
    }

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - periodDays);

    // Query attributions for this agent
    const results = await this.attributionCollection.query({
      queryTexts: [agentId],
      nResults: 1000,
      where: {
        agentId: agentId
      }
    });

    const attributions: Attribution[] = (results.documents[0] || [])
      .map(doc => JSON.parse(doc as string))
      .filter(attr => new Date(attr.createdAt) >= startDate);

    // Calculate metrics
    const totalTasks = attributions.length;
    const successfulTasks = attributions.filter(a => a.outcome === 'SUCCESS').length;
    const failedTasks = attributions.filter(a => a.outcome === 'FAILURE').length;
    const partialTasks = attributions.filter(a => a.outcome === 'PARTIAL').length;

    // Aggregate factors
    const allFactors = attributions.flatMap(a => a.causalFactors);
    const successFactors = allFactors.filter(f => f.contribution > 0);
    const failureFactors = allFactors.filter(f => f.contribution < 0);

    // Aggregate quality gate stats
    const allGates = attributions.flatMap(a => a.qualityGateResults);
    const gateStats = this.aggregateQualityGateStats(allGates);

    return {
      agentId,
      agentName,
      period: {
        start: startDate,
        end: new Date()
      },
      totalTasks,
      successfulTasks,
      failedTasks,
      partialTasks,
      successRate: totalTasks > 0 ? (successfulTasks / totalTasks) * 100 : 0,
      averageConfidence: this.calculateAverageConfidence(attributions),
      topSuccessFactors: this.aggregateFactors(successFactors).slice(0, 5),
      topFailurePatterns: this.aggregateFactors(failureFactors).slice(0, 5),
      qualityGateEffectiveness: gateStats,
      improvementTrend: this.calculateImprovementTrend(attributions)
    };
  }

  /**
   * Aggregate factors across multiple attributions
   */
  private aggregateFactors(factors: CausalFactor[]): RankedFactor[] {
    const factorMap = new Map<CausalFactorType, {
      descriptions: string[];
      contributions: number[];
    }>();

    for (const factor of factors) {
      const existing = factorMap.get(factor.factorType);
      if (existing) {
        existing.descriptions.push(factor.description);
        existing.contributions.push(factor.contribution);
      } else {
        factorMap.set(factor.factorType, {
          descriptions: [factor.description],
          contributions: [factor.contribution]
        });
      }
    }

    const ranked: RankedFactor[] = [];
    let rank = 1;

    for (const [factorType, data] of factorMap) {
      const avgContribution = data.contributions.reduce((a, b) => a + b, 0) / data.contributions.length;
      ranked.push({
        factor: factorType,
        description: data.descriptions[0], // Most common description
        frequency: data.contributions.length,
        averageContribution: avgContribution,
        rank: rank++
      });
    }

    return ranked.sort((a, b) => b.frequency - a.frequency);
  }

  /**
   * Aggregate quality gate statistics
   */
  private aggregateQualityGateStats(gates: QualityGateAttribution[]): QualityGateStats[] {
    const gateMap = new Map<string, QualityGateAttribution[]>();

    for (const gate of gates) {
      const existing = gateMap.get(gate.gateType) || [];
      existing.push(gate);
      gateMap.set(gate.gateType, existing);
    }

    const stats: QualityGateStats[] = [];

    for (const [gateType, gateList] of gateMap) {
      stats.push({
        gateType,
        totalChecks: gateList.length,
        issuesCaught: gateList.reduce((sum, g) => sum + g.issuesCaught, 0),
        falsePositiveRate: gateList.reduce((sum, g) => sum + g.falsePositives, 0) / gateList.length,
        falseNegativeRate: gateList.reduce((sum, g) => sum + g.falseNegatives, 0) / gateList.length,
        effectiveness: gateList.reduce((sum, g) => sum + g.effectiveness, 0) / gateList.length
      });
    }

    return stats;
  }

  /**
   * Calculate average confidence across attributions
   */
  private calculateAverageConfidence(attributions: Attribution[]): number {
    if (attributions.length === 0) return 0;
    return attributions.reduce((sum, a) => sum + a.confidence, 0) / attributions.length;
  }

  /**
   * Calculate improvement trend (comparing recent vs older performance)
   */
  private calculateImprovementTrend(attributions: Attribution[]): number {
    if (attributions.length < 10) return 0;

    // Sort by date
    const sorted = attributions.sort(
      (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    );

    // Split into halves
    const midpoint = Math.floor(sorted.length / 2);
    const older = sorted.slice(0, midpoint);
    const newer = sorted.slice(midpoint);

    // Calculate success rates
    const olderSuccessRate = older.filter(a => a.outcome === 'SUCCESS').length / older.length;
    const newerSuccessRate = newer.filter(a => a.outcome === 'SUCCESS').length / newer.length;

    // Return percentage change
    if (olderSuccessRate === 0) return newerSuccessRate * 100;
    return ((newerSuccessRate - olderSuccessRate) / olderSuccessRate) * 100;
  }
}

// ============================================================================
// Supporting Types (Input Data)
// ============================================================================

interface StepData {
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

interface QualityGateResult {
  gateType: string;
  gateName: string;
  passed: boolean;
  issuesCaught: number;
  falsePositives?: number;
  totalChecks: number;
}

interface ValidationResult {
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
// Export
// ============================================================================

export default AttributionProcessor;
```

---

### 3. Python Service (`backend/app/services/attribution_service.py`)

```python
"""
Attribution Service - Python Backend for Self-Attributing Agents
Week 21-22 Implementation

Handles:
- Outcome tracking and storage
- Attribution retrieval and analysis
- Performance metrics calculation
- Feedback distribution to agents
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from uuid import uuid4
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import chromadb
from chromadb.config import Settings

from app.models.attribution import (
    TaskOutcome,
    Attribution,
    AttributionFeedback,
    QualityGateStats
)
from app.schemas.attribution import (
    TaskOutcomeCreate,
    AttributionCreate,
    AttributionResponse,
    AgentPerformanceMetrics,
    FeedbackCreate
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
ATTRIBUTION_COLLECTION = "attributions"
OUTCOME_COLLECTION = "task_outcomes"


# =============================================================================
# Attribution Service Class
# =============================================================================

class AttributionService:
    """
    Service for managing task attributions and agent performance tracking.
    """

    def __init__(self, db: Session):
        self.db = db
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB client and collections."""
        try:
            self.chroma_client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT
            )

            self.attribution_collection = self.chroma_client.get_or_create_collection(
                name=ATTRIBUTION_COLLECTION,
                metadata={"description": "Attribution analysis results"}
            )

            self.outcome_collection = self.chroma_client.get_or_create_collection(
                name=OUTCOME_COLLECTION,
                metadata={"description": "Task outcome tracking"}
            )

            logger.info("ChromaDB collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            # Continue without ChromaDB - use PostgreSQL only
            self.chroma_client = None
            self.attribution_collection = None
            self.outcome_collection = None

    # =========================================================================
    # Outcome Tracking
    # =========================================================================

    async def record_task_outcome(
        self,
        outcome_data: TaskOutcomeCreate
    ) -> TaskOutcome:
        """
        Record the outcome of a task for attribution analysis.

        Args:
            outcome_data: Task outcome details

        Returns:
            Created TaskOutcome record
        """
        outcome = TaskOutcome(
            id=str(uuid4()),
            task_id=outcome_data.task_id,
            workflow_id=outcome_data.workflow_id,
            agent_id=outcome_data.agent_id,
            agent_name=outcome_data.agent_name,
            outcome_type=outcome_data.outcome_type,
            steps_data=json.dumps(outcome_data.steps),
            quality_gate_results=json.dumps(outcome_data.quality_gate_results),
            validation_history=json.dumps(outcome_data.validation_history),
            duration_ms=outcome_data.duration_ms,
            created_at=datetime.utcnow()
        )

        self.db.add(outcome)
        self.db.commit()
        self.db.refresh(outcome)

        # Also store in ChromaDB for semantic search
        if self.outcome_collection:
            await self._store_outcome_in_chroma(outcome)

        logger.info(f"Recorded task outcome: {outcome.id}")
        return outcome

    async def _store_outcome_in_chroma(self, outcome: TaskOutcome):
        """Store outcome in ChromaDB for semantic retrieval."""
        document = json.dumps({
            "task_id": outcome.task_id,
            "agent_name": outcome.agent_name,
            "outcome_type": outcome.outcome_type,
            "steps": outcome.steps_data
        })

        self.outcome_collection.add(
            ids=[outcome.id],
            documents=[document],
            metadatas=[{
                "agent_id": outcome.agent_id,
                "outcome_type": outcome.outcome_type,
                "created_at": outcome.created_at.isoformat()
            }]
        )

    # =========================================================================
    # Attribution Storage & Retrieval
    # =========================================================================

    async def store_attribution(
        self,
        attribution_data: AttributionCreate
    ) -> Attribution:
        """
        Store an attribution analysis result.

        Args:
            attribution_data: Attribution analysis data

        Returns:
            Created Attribution record
        """
        attribution = Attribution(
            id=str(uuid4()),
            task_id=attribution_data.task_id,
            workflow_id=attribution_data.workflow_id,
            agent_id=attribution_data.agent_id,
            agent_name=attribution_data.agent_name,
            outcome=attribution_data.outcome,
            key_steps=json.dumps(attribution_data.key_steps),
            causal_factors=json.dumps(attribution_data.causal_factors),
            quality_gate_results=json.dumps(attribution_data.quality_gate_results),
            validation_history=json.dumps(attribution_data.validation_history),
            confidence=attribution_data.confidence,
            confidence_level=attribution_data.confidence_level,
            created_at=datetime.utcnow(),
            analyzed_at=datetime.utcnow()
        )

        self.db.add(attribution)
        self.db.commit()
        self.db.refresh(attribution)

        # Store in ChromaDB
        if self.attribution_collection:
            await self._store_attribution_in_chroma(attribution)

        logger.info(f"Stored attribution: {attribution.id}")
        return attribution

    async def _store_attribution_in_chroma(self, attribution: Attribution):
        """Store attribution in ChromaDB for semantic search."""
        document = json.dumps({
            "task_id": attribution.task_id,
            "agent_name": attribution.agent_name,
            "outcome": attribution.outcome,
            "causal_factors": attribution.causal_factors,
            "confidence": attribution.confidence
        })

        self.attribution_collection.add(
            ids=[attribution.id],
            documents=[document],
            metadatas=[{
                "agent_id": attribution.agent_id,
                "outcome": attribution.outcome,
                "confidence": attribution.confidence,
                "created_at": attribution.created_at.isoformat()
            }]
        )

    async def get_attribution(self, attribution_id: str) -> Optional[Attribution]:
        """Get a single attribution by ID."""
        return self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()

    async def get_attributions_for_agent(
        self,
        agent_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Attribution]:
        """Get all attributions for a specific agent."""
        return self.db.query(Attribution).filter(
            Attribution.agent_id == agent_id
        ).order_by(
            Attribution.created_at.desc()
        ).offset(offset).limit(limit).all()

    async def get_attributions_by_outcome(
        self,
        outcome: str,
        days: int = 30
    ) -> List[Attribution]:
        """Get attributions filtered by outcome type."""
        since = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Attribution).filter(
            and_(
                Attribution.outcome == outcome,
                Attribution.created_at >= since
            )
        ).all()

    # =========================================================================
    # Performance Metrics
    # =========================================================================

    async def get_agent_performance_metrics(
        self,
        agent_id: str,
        agent_name: str,
        period_days: int = 30
    ) -> AgentPerformanceMetrics:
        """
        Calculate performance metrics for an agent.

        Args:
            agent_id: Agent identifier
            agent_name: Agent display name
            period_days: Number of days to analyze

        Returns:
            Comprehensive performance metrics
        """
        since = datetime.utcnow() - timedelta(days=period_days)

        # Get all attributions for this agent in period
        attributions = self.db.query(Attribution).filter(
            and_(
                Attribution.agent_id == agent_id,
                Attribution.created_at >= since
            )
        ).all()

        # Calculate basic metrics
        total_tasks = len(attributions)
        successful = sum(1 for a in attributions if a.outcome == 'SUCCESS')
        failed = sum(1 for a in attributions if a.outcome == 'FAILURE')
        partial = sum(1 for a in attributions if a.outcome == 'PARTIAL')

        # Calculate success rate
        success_rate = (successful / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate average confidence
        avg_confidence = (
            sum(a.confidence for a in attributions) / total_tasks
            if total_tasks > 0 else 0
        )

        # Aggregate causal factors
        all_factors = []
        for attr in attributions:
            factors = json.loads(attr.causal_factors) if attr.causal_factors else []
            all_factors.extend(factors)

        success_factors = [f for f in all_factors if f.get('contribution', 0) > 0]
        failure_factors = [f for f in all_factors if f.get('contribution', 0) < 0]

        # Aggregate quality gate stats
        quality_gate_stats = await self._aggregate_quality_gate_stats(attributions)

        # Calculate improvement trend
        improvement_trend = await self._calculate_improvement_trend(
            agent_id, since
        )

        return AgentPerformanceMetrics(
            agent_id=agent_id,
            agent_name=agent_name,
            period_start=since,
            period_end=datetime.utcnow(),
            total_tasks=total_tasks,
            successful_tasks=successful,
            failed_tasks=failed,
            partial_tasks=partial,
            success_rate=success_rate,
            average_confidence=avg_confidence,
            top_success_factors=self._rank_factors(success_factors)[:5],
            top_failure_patterns=self._rank_factors(failure_factors)[:5],
            quality_gate_effectiveness=quality_gate_stats,
            improvement_trend=improvement_trend
        )

    async def _aggregate_quality_gate_stats(
        self,
        attributions: List[Attribution]
    ) -> List[Dict[str, Any]]:
        """Aggregate quality gate statistics across attributions."""
        gate_map: Dict[str, List[Dict]] = {}

        for attr in attributions:
            gates = json.loads(attr.quality_gate_results) if attr.quality_gate_results else []
            for gate in gates:
                gate_type = gate.get('gateType', 'unknown')
                if gate_type not in gate_map:
                    gate_map[gate_type] = []
                gate_map[gate_type].append(gate)

        stats = []
        for gate_type, gates in gate_map.items():
            total = len(gates)
            issues_caught = sum(g.get('issuesCaught', 0) for g in gates)
            false_positives = sum(g.get('falsePositives', 0) for g in gates)
            avg_effectiveness = sum(g.get('effectiveness', 0) for g in gates) / total

            stats.append({
                'gate_type': gate_type,
                'total_checks': total,
                'issues_caught': issues_caught,
                'false_positive_rate': false_positives / total if total > 0 else 0,
                'effectiveness': avg_effectiveness
            })

        return stats

    def _rank_factors(self, factors: List[Dict]) -> List[Dict]:
        """Rank and aggregate causal factors."""
        factor_counts: Dict[str, Dict] = {}

        for factor in factors:
            factor_type = factor.get('factorType', 'unknown')
            if factor_type not in factor_counts:
                factor_counts[factor_type] = {
                    'factor': factor_type,
                    'description': factor.get('description', ''),
                    'frequency': 0,
                    'total_contribution': 0
                }
            factor_counts[factor_type]['frequency'] += 1
            factor_counts[factor_type]['total_contribution'] += abs(
                factor.get('contribution', 0)
            )

        ranked = list(factor_counts.values())
        for f in ranked:
            f['average_contribution'] = (
                f['total_contribution'] / f['frequency']
                if f['frequency'] > 0 else 0
            )
            del f['total_contribution']

        return sorted(ranked, key=lambda x: x['frequency'], reverse=True)

    async def _calculate_improvement_trend(
        self,
        agent_id: str,
        since: datetime
    ) -> float:
        """Calculate improvement trend comparing recent vs older performance."""
        midpoint = since + (datetime.utcnow() - since) / 2

        # Older period
        older = self.db.query(Attribution).filter(
            and_(
                Attribution.agent_id == agent_id,
                Attribution.created_at >= since,
                Attribution.created_at < midpoint
            )
        ).all()

        # Newer period
        newer = self.db.query(Attribution).filter(
            and_(
                Attribution.agent_id == agent_id,
                Attribution.created_at >= midpoint
            )
        ).all()

        if not older or not newer:
            return 0.0

        older_success = sum(1 for a in older if a.outcome == 'SUCCESS') / len(older)
        newer_success = sum(1 for a in newer if a.outcome == 'SUCCESS') / len(newer)

        if older_success == 0:
            return newer_success * 100

        return ((newer_success - older_success) / older_success) * 100

    # =========================================================================
    # Feedback Distribution
    # =========================================================================

    async def create_feedback(
        self,
        feedback_data: FeedbackCreate
    ) -> AttributionFeedback:
        """
        Create feedback record for an agent based on attribution.

        Args:
            feedback_data: Feedback details

        Returns:
            Created feedback record
        """
        feedback = AttributionFeedback(
            id=str(uuid4()),
            attribution_id=feedback_data.attribution_id,
            agent_id=feedback_data.agent_id,
            feedback_type=feedback_data.feedback_type,
            lessons=json.dumps(feedback_data.lessons),
            recommended_adjustments=json.dumps(feedback_data.recommended_adjustments),
            delivered=False,
            delivered_at=None,
            created_at=datetime.utcnow()
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        logger.info(f"Created feedback: {feedback.id} for agent {feedback.agent_id}")
        return feedback

    async def get_pending_feedback(
        self,
        agent_id: str
    ) -> List[AttributionFeedback]:
        """Get all undelivered feedback for an agent."""
        return self.db.query(AttributionFeedback).filter(
            and_(
                AttributionFeedback.agent_id == agent_id,
                AttributionFeedback.delivered == False
            )
        ).all()

    async def mark_feedback_delivered(
        self,
        feedback_id: str
    ) -> AttributionFeedback:
        """Mark feedback as delivered to agent."""
        feedback = self.db.query(AttributionFeedback).filter(
            AttributionFeedback.id == feedback_id
        ).first()

        if feedback:
            feedback.delivered = True
            feedback.delivered_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(feedback)

        return feedback

    # =========================================================================
    # Dashboard Data
    # =========================================================================

    async def get_dashboard_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get summary data for attribution dashboard.

        Args:
            days: Number of days to analyze

        Returns:
            Dashboard summary data
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Get all attributions in period
        attributions = self.db.query(Attribution).filter(
            Attribution.created_at >= since
        ).all()

        # Group by agent
        agent_stats = {}
        for attr in attributions:
            if attr.agent_name not in agent_stats:
                agent_stats[attr.agent_name] = {
                    'total': 0,
                    'success': 0,
                    'failure': 0,
                    'partial': 0
                }
            agent_stats[attr.agent_name]['total'] += 1
            if attr.outcome == 'SUCCESS':
                agent_stats[attr.agent_name]['success'] += 1
            elif attr.outcome == 'FAILURE':
                agent_stats[attr.agent_name]['failure'] += 1
            else:
                agent_stats[attr.agent_name]['partial'] += 1

        # Calculate success rates per agent
        agent_performance = []
        for agent_name, stats in agent_stats.items():
            success_rate = (
                stats['success'] / stats['total'] * 100
                if stats['total'] > 0 else 0
            )
            agent_performance.append({
                'agent_name': agent_name,
                'total_tasks': stats['total'],
                'success_rate': round(success_rate, 1),
                'status': 'good' if success_rate >= 80 else 'warning' if success_rate >= 60 else 'critical'
            })

        # Aggregate all causal factors
        all_success_factors = []
        all_failure_factors = []
        for attr in attributions:
            factors = json.loads(attr.causal_factors) if attr.causal_factors else []
            for f in factors:
                if f.get('contribution', 0) > 0:
                    all_success_factors.append(f)
                else:
                    all_failure_factors.append(f)

        return {
            'period': {
                'start': since.isoformat(),
                'end': datetime.utcnow().isoformat(),
                'days': days
            },
            'total_attributions': len(attributions),
            'agent_performance': sorted(
                agent_performance,
                key=lambda x: x['success_rate'],
                reverse=True
            ),
            'top_success_factors': self._rank_factors(all_success_factors)[:5],
            'top_failure_patterns': self._rank_factors(all_failure_factors)[:5],
            'overall_success_rate': round(
                sum(1 for a in attributions if a.outcome == 'SUCCESS') / len(attributions) * 100
                if attributions else 0,
                1
            )
        }


# =============================================================================
# Factory Function
# =============================================================================

def get_attribution_service(db: Session) -> AttributionService:
    """Factory function to create AttributionService instance."""
    return AttributionService(db)
```

---

### 4. API Endpoints (`backend/app/api/attribution.py`)

```python
"""
Attribution API - REST Endpoints for Self-Attributing Agents
Week 21-22 Implementation

Endpoints:
- POST /api/attribution/outcomes - Record task outcome
- POST /api/attribution/analyze - Trigger attribution analysis
- GET /api/attribution/{id} - Get single attribution
- GET /api/attribution/agent/{agent_id} - Get attributions for agent
- GET /api/attribution/metrics/{agent_id} - Get agent performance metrics
- GET /api/attribution/dashboard - Get dashboard summary
- POST /api/attribution/feedback - Create feedback
- GET /api/attribution/feedback/pending/{agent_id} - Get pending feedback
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.services.attribution_service import (
    AttributionService,
    get_attribution_service
)
from app.schemas.attribution import (
    TaskOutcomeCreate,
    TaskOutcomeResponse,
    AttributionCreate,
    AttributionResponse,
    AgentPerformanceMetrics,
    DashboardSummary,
    FeedbackCreate,
    FeedbackResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/attribution", tags=["attribution"])


# =============================================================================
# Outcome Recording
# =============================================================================

@router.post("/outcomes", response_model=TaskOutcomeResponse)
async def record_task_outcome(
    outcome_data: TaskOutcomeCreate,
    db: Session = Depends(get_db)
):
    """
    Record the outcome of a completed task.

    This is called by agents after task completion to store
    outcome data for attribution analysis.
    """
    service = get_attribution_service(db)
    try:
        outcome = await service.record_task_outcome(outcome_data)
        return TaskOutcomeResponse.from_orm(outcome)
    except Exception as e:
        logger.error(f"Failed to record outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Attribution Analysis
# =============================================================================

@router.post("/analyze", response_model=AttributionResponse)
async def analyze_task(
    attribution_data: AttributionCreate,
    db: Session = Depends(get_db)
):
    """
    Store attribution analysis results.

    Called after the TypeScript AttributionProcessor has analyzed
    a task outcome.
    """
    service = get_attribution_service(db)
    try:
        attribution = await service.store_attribution(attribution_data)
        return AttributionResponse.from_orm(attribution)
    except Exception as e:
        logger.error(f"Failed to store attribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{attribution_id}", response_model=AttributionResponse)
async def get_attribution(
    attribution_id: str,
    db: Session = Depends(get_db)
):
    """Get a single attribution by ID."""
    service = get_attribution_service(db)
    attribution = await service.get_attribution(attribution_id)

    if not attribution:
        raise HTTPException(status_code=404, detail="Attribution not found")

    return AttributionResponse.from_orm(attribution)


@router.get("/agent/{agent_id}", response_model=List[AttributionResponse])
async def get_agent_attributions(
    agent_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all attributions for a specific agent."""
    service = get_attribution_service(db)
    attributions = await service.get_attributions_for_agent(
        agent_id, limit, offset
    )
    return [AttributionResponse.from_orm(a) for a in attributions]


@router.get("/outcome/{outcome_type}", response_model=List[AttributionResponse])
async def get_attributions_by_outcome(
    outcome_type: str,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get attributions filtered by outcome type (SUCCESS/FAILURE/PARTIAL)."""
    if outcome_type not in ['SUCCESS', 'FAILURE', 'PARTIAL']:
        raise HTTPException(
            status_code=400,
            detail="Invalid outcome type. Use SUCCESS, FAILURE, or PARTIAL"
        )

    service = get_attribution_service(db)
    attributions = await service.get_attributions_by_outcome(outcome_type, days)
    return [AttributionResponse.from_orm(a) for a in attributions]


# =============================================================================
# Performance Metrics
# =============================================================================

@router.get("/metrics/{agent_id}", response_model=AgentPerformanceMetrics)
async def get_agent_metrics(
    agent_id: str,
    agent_name: str = Query(..., description="Agent display name"),
    period_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive performance metrics for an agent.

    Includes:
    - Success/failure rates
    - Top success factors
    - Common failure patterns
    - Quality gate effectiveness
    - Improvement trend
    """
    service = get_attribution_service(db)
    metrics = await service.get_agent_performance_metrics(
        agent_id, agent_name, period_days
    )
    return metrics


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get summary data for the attribution dashboard.

    Provides:
    - Overall statistics
    - Per-agent performance
    - Top success factors
    - Common failure patterns
    """
    service = get_attribution_service(db)
    summary = await service.get_dashboard_summary(days)
    return DashboardSummary(**summary)


# =============================================================================
# Feedback
# =============================================================================

@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Create feedback for an agent based on attribution analysis.
    """
    service = get_attribution_service(db)
    feedback = await service.create_feedback(feedback_data)
    return FeedbackResponse.from_orm(feedback)


@router.get("/feedback/pending/{agent_id}", response_model=List[FeedbackResponse])
async def get_pending_feedback(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get all undelivered feedback for an agent."""
    service = get_attribution_service(db)
    feedback_list = await service.get_pending_feedback(agent_id)
    return [FeedbackResponse.from_orm(f) for f in feedback_list]


@router.post("/feedback/{feedback_id}/delivered", response_model=FeedbackResponse)
async def mark_feedback_delivered(
    feedback_id: str,
    db: Session = Depends(get_db)
):
    """Mark feedback as delivered to the agent."""
    service = get_attribution_service(db)
    feedback = await service.mark_feedback_delivered(feedback_id)

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return FeedbackResponse.from_orm(feedback)


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def attribution_health_check(db: Session = Depends(get_db)):
    """Health check for attribution service."""
    service = get_attribution_service(db)

    return {
        "status": "healthy",
        "chromadb_connected": service.chroma_client is not None,
        "collections": {
            "attributions": service.attribution_collection is not None,
            "outcomes": service.outcome_collection is not None
        }
    }
```

---

### 5. Database Models (`backend/app/models/attribution.py`)

```python
"""
Attribution Database Models
Week 21-22 Implementation
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class TaskOutcome(Base):
    """Stores raw task outcome data for attribution analysis."""

    __tablename__ = "task_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    outcome_type = Column(String(20), nullable=False)  # SUCCESS, FAILURE, PARTIAL
    steps_data = Column(Text)  # JSON serialized steps
    quality_gate_results = Column(Text)  # JSON serialized
    validation_history = Column(Text)  # JSON serialized
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class Attribution(Base):
    """Stores attribution analysis results."""

    __tablename__ = "attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    outcome = Column(String(20), nullable=False)  # SUCCESS, FAILURE, PARTIAL
    key_steps = Column(Text)  # JSON serialized AttributedStep[]
    causal_factors = Column(Text)  # JSON serialized CausalFactor[]
    quality_gate_results = Column(Text)  # JSON serialized
    validation_history = Column(Text)  # JSON serialized
    confidence = Column(Float, nullable=False)
    confidence_level = Column(String(20))  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, default=datetime.utcnow)


class AttributionFeedback(Base):
    """Stores feedback generated from attribution analysis."""

    __tablename__ = "attribution_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribution_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)  # SUCCESS_REINFORCEMENT, FAILURE_CORRECTION, PATTERN_UPDATE
    lessons = Column(Text)  # JSON serialized Lesson[]
    recommended_adjustments = Column(Text)  # JSON serialized Adjustment[]
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QualityGateStats(Base):
    """Aggregated quality gate effectiveness statistics."""

    __tablename__ = "quality_gate_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_type = Column(String(50), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_checks = Column(Integer, default=0)
    issues_caught = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    effectiveness = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### 6. Database Migration (`backend/alembic/versions/008_add_attribution_tables.py`)

```python
"""Add attribution tables

Revision ID: 008
Revises: 007
Create Date: 2025-XX-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Task Outcomes table
    op.create_table(
        'task_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('workflow_id', sa.String(100), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('outcome_type', sa.String(20), nullable=False),
        sa.Column('steps_data', sa.Text(), nullable=True),
        sa.Column('quality_gate_results', sa.Text(), nullable=True),
        sa.Column('validation_history', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_outcomes_task_id', 'task_outcomes', ['task_id'])
    op.create_index('ix_task_outcomes_agent_id', 'task_outcomes', ['agent_id'])
    op.create_index('ix_task_outcomes_workflow_id', 'task_outcomes', ['workflow_id'])

    # Attributions table
    op.create_table(
        'attributions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('workflow_id', sa.String(100), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('key_steps', sa.Text(), nullable=True),
        sa.Column('causal_factors', sa.Text(), nullable=True),
        sa.Column('quality_gate_results', sa.Text(), nullable=True),
        sa.Column('validation_history', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attributions_task_id', 'attributions', ['task_id'])
    op.create_index('ix_attributions_agent_id', 'attributions', ['agent_id'])
    op.create_index('ix_attributions_outcome', 'attributions', ['outcome'])

    # Attribution Feedback table
    op.create_table(
        'attribution_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attribution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('lessons', sa.Text(), nullable=True),
        sa.Column('recommended_adjustments', sa.Text(), nullable=True),
        sa.Column('delivered', sa.Boolean(), default=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attribution_feedback_agent_id', 'attribution_feedback', ['agent_id'])
    op.create_index('ix_attribution_feedback_attribution_id', 'attribution_feedback', ['attribution_id'])

    # Quality Gate Stats table
    op.create_table(
        'quality_gate_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gate_type', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_checks', sa.Integer(), default=0),
        sa.Column('issues_caught', sa.Integer(), default=0),
        sa.Column('false_positives', sa.Integer(), default=0),
        sa.Column('false_negatives', sa.Integer(), default=0),
        sa.Column('effectiveness', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quality_gate_stats_gate_type', 'quality_gate_stats', ['gate_type'])


def downgrade() -> None:
    op.drop_table('quality_gate_stats')
    op.drop_table('attribution_feedback')
    op.drop_table('attributions')
    op.drop_table('task_outcomes')
```

---

### 7. Attribution Dashboard (`frontend/attribution-dashboard.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attribution Dashboard - Self-Attributing Agents</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
        }

        .header h1 {
            font-size: 1.8rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .period-selector {
            display: flex;
            gap: 10px;
        }

        .period-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            background: rgba(255,255,255,0.1);
            color: #e0e0e0;
            transition: all 0.3s;
        }

        .period-btn.active {
            background: #7b2cbf;
            color: white;
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-value.success { color: #4ade80; }
        .stat-value.warning { color: #fbbf24; }
        .stat-value.danger { color: #f87171; }

        .stat-label {
            color: #9ca3af;
            font-size: 0.9rem;
        }

        /* Agent Performance Grid */
        .section-title {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #00d4ff;
        }

        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .agent-card {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s;
        }

        .agent-card:hover {
            transform: translateY(-5px);
        }

        .agent-name {
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .agent-score {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .agent-score.good { color: #4ade80; }
        .agent-score.warning { color: #fbbf24; }
        .agent-score.critical { color: #f87171; }

        .agent-tasks {
            color: #9ca3af;
            font-size: 0.85rem;
        }

        /* Factors Lists */
        .factors-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        .factors-section {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
        }

        .factors-section.success {
            border-left: 4px solid #4ade80;
        }

        .factors-section.failure {
            border-left: 4px solid #f87171;
        }

        .factor-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .factor-item:last-child {
            border-bottom: none;
        }

        .factor-rank {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }

        .factors-section.success .factor-rank {
            background: rgba(74, 222, 128, 0.2);
            color: #4ade80;
        }

        .factors-section.failure .factor-rank {
            background: rgba(248, 113, 113, 0.2);
            color: #f87171;
        }

        .factor-info {
            flex: 1;
        }

        .factor-name {
            font-weight: 500;
            margin-bottom: 3px;
        }

        .factor-frequency {
            font-size: 0.85rem;
            color: #9ca3af;
        }

        .factor-contribution {
            font-size: 1.2rem;
            font-weight: bold;
        }

        /* Quality Gate Stats */
        .gate-stats {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
        }

        .gate-table {
            width: 100%;
            border-collapse: collapse;
        }

        .gate-table th,
        .gate-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .gate-table th {
            color: #9ca3af;
            font-weight: 500;
        }

        .effectiveness-bar {
            width: 100px;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }

        .effectiveness-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80, #22c55e);
            border-radius: 4px;
        }

        /* Loading State */
        .loading {
            text-align: center;
            padding: 40px;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255,255,255,0.1);
            border-top-color: #7b2cbf;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .factors-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🎯 Attribution Dashboard</h1>
            <div class="period-selector">
                <button class="period-btn" data-days="7">7 Days</button>
                <button class="period-btn active" data-days="30">30 Days</button>
                <button class="period-btn" data-days="90">90 Days</button>
            </div>
        </div>

        <!-- Loading State -->
        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p>Loading attribution data...</p>
        </div>

        <!-- Dashboard Content -->
        <div id="dashboard" style="display: none;">
            <!-- Stats Overview -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div id="total-tasks" class="stat-value">-</div>
                    <div class="stat-label">Total Tasks Analyzed</div>
                </div>
                <div class="stat-card">
                    <div id="success-rate" class="stat-value success">-</div>
                    <div class="stat-label">Overall Success Rate</div>
                </div>
                <div class="stat-card">
                    <div id="avg-confidence" class="stat-value">-</div>
                    <div class="stat-label">Avg Confidence</div>
                </div>
                <div class="stat-card">
                    <div id="improvement" class="stat-value">-</div>
                    <div class="stat-label">Improvement Trend</div>
                </div>
            </div>

            <!-- Agent Performance -->
            <h2 class="section-title">🤖 Agent Performance</h2>
            <div id="agents-grid" class="agents-grid">
                <!-- Agent cards will be inserted here -->
            </div>

            <!-- Success Factors & Failure Patterns -->
            <div class="factors-container">
                <div class="factors-section success">
                    <h2 class="section-title">✅ Top Success Factors</h2>
                    <div id="success-factors">
                        <!-- Success factors will be inserted here -->
                    </div>
                </div>
                <div class="factors-section failure">
                    <h2 class="section-title">⚠️ Common Failure Patterns</h2>
                    <div id="failure-factors">
                        <!-- Failure patterns will be inserted here -->
                    </div>
                </div>
            </div>

            <!-- Quality Gate Effectiveness -->
            <div class="gate-stats">
                <h2 class="section-title">🛡️ Quality Gate Effectiveness</h2>
                <table class="gate-table">
                    <thead>
                        <tr>
                            <th>Gate Type</th>
                            <th>Total Checks</th>
                            <th>Issues Caught</th>
                            <th>False Positive Rate</th>
                            <th>Effectiveness</th>
                        </tr>
                    </thead>
                    <tbody id="gate-table-body">
                        <!-- Gate stats will be inserted here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Configuration
        const API_BASE = '/api/attribution';
        let currentPeriod = 30;

        // DOM Elements
        const loadingEl = document.getElementById('loading');
        const dashboardEl = document.getElementById('dashboard');
        const periodBtns = document.querySelectorAll('.period-btn');

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadDashboard();
            setupEventListeners();
        });

        function setupEventListeners() {
            periodBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    periodBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentPeriod = parseInt(btn.dataset.days);
                    loadDashboard();
                });
            });
        }

        async function loadDashboard() {
            showLoading(true);

            try {
                const response = await fetch(`${API_BASE}/dashboard/summary?days=${currentPeriod}`);
                if (!response.ok) throw new Error('Failed to load dashboard data');

                const data = await response.json();
                renderDashboard(data);
            } catch (error) {
                console.error('Error loading dashboard:', error);
                showError('Failed to load dashboard data');
            }

            showLoading(false);
        }

        function renderDashboard(data) {
            // Stats Overview
            document.getElementById('total-tasks').textContent = data.total_attributions;

            const successRate = document.getElementById('success-rate');
            successRate.textContent = `${data.overall_success_rate}%`;
            successRate.className = 'stat-value ' + getStatusClass(data.overall_success_rate);

            // Agent Performance Grid
            renderAgentGrid(data.agent_performance);

            // Success Factors
            renderFactors('success-factors', data.top_success_factors, true);

            // Failure Patterns
            renderFactors('failure-factors', data.top_failure_patterns, false);

            // Quality Gate Stats (mock data for now)
            renderGateStats([
                { gate_type: 'Architecture', total_checks: 150, issues_caught: 23, false_positive_rate: 0.05, effectiveness: 0.85 },
                { gate_type: 'Code Quality', total_checks: 320, issues_caught: 45, false_positive_rate: 0.08, effectiveness: 0.82 },
                { gate_type: 'Security', total_checks: 280, issues_caught: 12, false_positive_rate: 0.02, effectiveness: 0.95 },
                { gate_type: 'Test Coverage', total_checks: 200, issues_caught: 34, false_positive_rate: 0.10, effectiveness: 0.78 }
            ]);
        }

        function renderAgentGrid(agents) {
            const grid = document.getElementById('agents-grid');
            grid.innerHTML = agents.map(agent => `
                <div class="agent-card">
                    <div class="agent-name">${agent.agent_name}</div>
                    <div class="agent-score ${agent.status}">${agent.success_rate}%</div>
                    <div class="agent-tasks">${agent.total_tasks} tasks</div>
                </div>
            `).join('');
        }

        function renderFactors(containerId, factors, isSuccess) {
            const container = document.getElementById(containerId);

            if (!factors || factors.length === 0) {
                container.innerHTML = '<p style="color: #9ca3af; text-align: center; padding: 20px;">No data available</p>';
                return;
            }

            container.innerHTML = factors.map((factor, index) => `
                <div class="factor-item">
                    <div class="factor-rank">${index + 1}</div>
                    <div class="factor-info">
                        <div class="factor-name">${formatFactorType(factor.factor)}</div>
                        <div class="factor-frequency">${factor.frequency} occurrences</div>
                    </div>
                    <div class="factor-contribution" style="color: ${isSuccess ? '#4ade80' : '#f87171'}">
                        ${isSuccess ? '+' : ''}${(factor.average_contribution * 100).toFixed(0)}%
                    </div>
                </div>
            `).join('');
        }

        function renderGateStats(stats) {
            const tbody = document.getElementById('gate-table-body');
            tbody.innerHTML = stats.map(gate => `
                <tr>
                    <td>${gate.gate_type}</td>
                    <td>${gate.total_checks}</td>
                    <td>${gate.issues_caught}</td>
                    <td>${(gate.false_positive_rate * 100).toFixed(1)}%</td>
                    <td>
                        <div class="effectiveness-bar">
                            <div class="effectiveness-fill" style="width: ${gate.effectiveness * 100}%"></div>
                        </div>
                    </td>
                </tr>
            `).join('');
        }

        function formatFactorType(type) {
            const mapping = {
                'PATTERN_REUSE': '🔄 Pattern Reuse',
                'EARLY_VALIDATION': '✓ Early Validation',
                'CLEAR_SPECIFICATION': '📋 Clear Specification',
                'TEST_COVERAGE': '🧪 Test Coverage',
                'SECURITY_SCAN': '🔒 Security Scan',
                'MISSING_EDGE_CASE': '⚠️ Missing Edge Case',
                'INCOMPLETE_VALIDATION': '❌ Incomplete Validation',
                'DEPENDENCY_ISSUE': '🔗 Dependency Issue',
                'AMBIGUOUS_REQUIREMENT': '❓ Ambiguous Requirement',
                'RESOURCE_CONSTRAINT': '⏱️ Resource Constraint'
            };
            return mapping[type] || type;
        }

        function getStatusClass(rate) {
            if (rate >= 80) return 'success';
            if (rate >= 60) return 'warning';
            return 'danger';
        }

        function showLoading(show) {
            loadingEl.style.display = show ? 'block' : 'none';
            dashboardEl.style.display = show ? 'none' : 'block';
        }

        function showError(message) {
            dashboardEl.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 3rem; margin-bottom: 15px;">⚠️</div>
                    <p style="color: #f87171;">${message}</p>
                    <button onclick="loadDashboard()" style="margin-top: 15px; padding: 10px 20px; background: #7b2cbf; border: none; border-radius: 8px; color: white; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
        }
    </script>
</body>
</html>
```

---

### 8. Test Specifications (`backend/tests/api/week21/test_attribution_api.py`)

```python
"""
Attribution API Tests
Week 21-22 Implementation

Tests cover:
- Outcome recording
- Attribution storage and retrieval
- Performance metrics calculation
- Dashboard summary
- Feedback management
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from uuid import uuid4
import json

from app.main import app
from app.database import get_db, Base, engine


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def client():
    """Create test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_outcome():
    """Sample task outcome data."""
    return {
        "task_id": f"task_{uuid4().hex[:8]}",
        "workflow_id": f"workflow_{uuid4().hex[:8]}",
        "agent_id": "felix_001",
        "agent_name": "Felix",
        "outcome_type": "SUCCESS",
        "steps": [
            {
                "id": "step_1",
                "name": "Generate specification",
                "agentId": "felix_001",
                "succeeded": True,
                "duration": 5000,
                "expectedDuration": 4000,
                "experienceConsulted": True,
                "patternUsed": "microservices_pattern"
            },
            {
                "id": "step_2",
                "name": "Create task breakdown",
                "agentId": "felix_001",
                "succeeded": True,
                "duration": 3000,
                "expectedDuration": 3500
            }
        ],
        "quality_gate_results": [
            {
                "gateType": "architecture",
                "gateName": "Architecture Review",
                "passed": True,
                "issuesCaught": 2,
                "falsePositives": 0,
                "totalChecks": 10
            }
        ],
        "validation_history": [
            {
                "phase": "LINTING",
                "iteration": 1,
                "passed": True,
                "errors": []
            }
        ],
        "duration_ms": 8500
    }


@pytest.fixture
def sample_attribution():
    """Sample attribution data."""
    return {
        "task_id": f"task_{uuid4().hex[:8]}",
        "workflow_id": f"workflow_{uuid4().hex[:8]}",
        "agent_id": "felix_001",
        "agent_name": "Felix",
        "outcome": "SUCCESS",
        "key_steps": [
            {
                "stepId": "step_1",
                "stepName": "Generate specification",
                "agentId": "felix_001",
                "impact": "CRITICAL",
                "impactScore": 0.85,
                "reasoning": "Successfully applied learned experience",
                "duration": 5000,
                "retryCount": 0,
                "experienceUsed": True,
                "patternApplied": "microservices_pattern"
            }
        ],
        "causal_factors": [
            {
                "factorId": f"factor_{uuid4().hex[:8]}",
                "factorType": "PATTERN_REUSE",
                "description": "Experience consulted in 1 steps",
                "contribution": 0.3,
                "evidence": ["Generate specification"],
                "relatedSteps": ["step_1"]
            }
        ],
        "quality_gate_results": [],
        "validation_history": [],
        "confidence": 0.85,
        "confidence_level": "HIGH"
    }


# =============================================================================
# Outcome Recording Tests
# =============================================================================

class TestOutcomeRecording:
    """Tests for task outcome recording."""

    def test_record_outcome_success(self, client, sample_outcome):
        """Test recording a successful task outcome."""
        response = client.post("/api/attribution/outcomes", json=sample_outcome)

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == sample_outcome["task_id"]
        assert data["outcome_type"] == "SUCCESS"
        assert "id" in data

    def test_record_outcome_failure(self, client, sample_outcome):
        """Test recording a failed task outcome."""
        sample_outcome["outcome_type"] = "FAILURE"
        response = client.post("/api/attribution/outcomes", json=sample_outcome)

        assert response.status_code == 200
        data = response.json()
        assert data["outcome_type"] == "FAILURE"

    def test_record_outcome_missing_required_field(self, client):
        """Test recording with missing required field."""
        incomplete_data = {
            "task_id": "test_task",
            # Missing agent_id, agent_name, etc.
        }
        response = client.post("/api/attribution/outcomes", json=incomplete_data)

        assert response.status_code == 422  # Validation error


# =============================================================================
# Attribution Storage Tests
# =============================================================================

class TestAttributionStorage:
    """Tests for attribution storage and retrieval."""

    def test_store_attribution(self, client, sample_attribution):
        """Test storing attribution analysis."""
        response = client.post("/api/attribution/analyze", json=sample_attribution)

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == sample_attribution["task_id"]
        assert data["confidence"] == sample_attribution["confidence"]

    def test_get_attribution_by_id(self, client, sample_attribution):
        """Test retrieving attribution by ID."""
        # First, create an attribution
        create_response = client.post("/api/attribution/analyze", json=sample_attribution)
        attribution_id = create_response.json()["id"]

        # Then retrieve it
        response = client.get(f"/api/attribution/{attribution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == attribution_id

    def test_get_attribution_not_found(self, client):
        """Test retrieving non-existent attribution."""
        fake_id = str(uuid4())
        response = client.get(f"/api/attribution/{fake_id}")

        assert response.status_code == 404

    def test_get_agent_attributions(self, client, sample_attribution):
        """Test retrieving all attributions for an agent."""
        # Create multiple attributions
        for _ in range(3):
            sample_attribution["task_id"] = f"task_{uuid4().hex[:8]}"
            client.post("/api/attribution/analyze", json=sample_attribution)

        # Retrieve all for agent
        response = client.get(f"/api/attribution/agent/{sample_attribution['agent_id']}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_get_attributions_by_outcome(self, client, sample_attribution):
        """Test filtering attributions by outcome type."""
        response = client.get("/api/attribution/outcome/SUCCESS?days=30")

        assert response.status_code == 200
        data = response.json()
        assert all(a["outcome"] == "SUCCESS" for a in data)


# =============================================================================
# Performance Metrics Tests
# =============================================================================

class TestPerformanceMetrics:
    """Tests for agent performance metrics."""

    def test_get_agent_metrics(self, client, sample_attribution):
        """Test getting agent performance metrics."""
        # Create some attributions first
        for i in range(5):
            sample_attribution["task_id"] = f"task_{uuid4().hex[:8]}"
            sample_attribution["outcome"] = "SUCCESS" if i % 2 == 0 else "FAILURE"
            client.post("/api/attribution/analyze", json=sample_attribution)

        response = client.get(
            f"/api/attribution/metrics/{sample_attribution['agent_id']}",
            params={"agent_name": "Felix", "period_days": 30}
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_rate" in data
        assert "top_success_factors" in data
        assert "top_failure_patterns" in data

    def test_metrics_empty_agent(self, client):
        """Test metrics for agent with no data."""
        response = client.get(
            "/api/attribution/metrics/nonexistent_agent",
            params={"agent_name": "Unknown", "period_days": 30}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0
        assert data["success_rate"] == 0


# =============================================================================
# Dashboard Tests
# =============================================================================

class TestDashboard:
    """Tests for dashboard summary endpoint."""

    def test_get_dashboard_summary(self, client):
        """Test getting dashboard summary."""
        response = client.get("/api/attribution/dashboard/summary?days=30")

        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "total_attributions" in data
        assert "agent_performance" in data
        assert "overall_success_rate" in data

    def test_dashboard_different_periods(self, client):
        """Test dashboard with different time periods."""
        for days in [7, 30, 90]:
            response = client.get(f"/api/attribution/dashboard/summary?days={days}")
            assert response.status_code == 200


# =============================================================================
# Feedback Tests
# =============================================================================

class TestFeedback:
    """Tests for feedback management."""

    def test_create_feedback(self, client, sample_attribution):
        """Test creating feedback for an agent."""
        # First create an attribution
        attr_response = client.post("/api/attribution/analyze", json=sample_attribution)
        attribution_id = attr_response.json()["id"]

        feedback_data = {
            "attribution_id": attribution_id,
            "agent_id": sample_attribution["agent_id"],
            "feedback_type": "SUCCESS_REINFORCEMENT",
            "lessons": [
                {
                    "lessonId": f"lesson_{uuid4().hex[:8]}",
                    "lessonType": "DO_MORE",
                    "description": "Pattern reuse was effective",
                    "context": "microservices_pattern",
                    "confidence": 0.85
                }
            ],
            "recommended_adjustments": []
        }

        response = client.post("/api/attribution/feedback", json=feedback_data)

        assert response.status_code == 200
        data = response.json()
        assert data["delivered"] == False

    def test_get_pending_feedback(self, client, sample_attribution):
        """Test getting pending feedback for an agent."""
        response = client.get(
            f"/api/attribution/feedback/pending/{sample_attribution['agent_id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_mark_feedback_delivered(self, client, sample_attribution):
        """Test marking feedback as delivered."""
        # Create attribution and feedback first
        attr_response = client.post("/api/attribution/analyze", json=sample_attribution)
        attribution_id = attr_response.json()["id"]

        feedback_data = {
            "attribution_id": attribution_id,
            "agent_id": sample_attribution["agent_id"],
            "feedback_type": "SUCCESS_REINFORCEMENT",
            "lessons": [],
            "recommended_adjustments": []
        }

        feedback_response = client.post("/api/attribution/feedback", json=feedback_data)
        feedback_id = feedback_response.json()["id"]

        # Mark as delivered
        response = client.post(f"/api/attribution/feedback/{feedback_id}/delivered")

        assert response.status_code == 200
        data = response.json()
        assert data["delivered"] == True
        assert data["delivered_at"] is not None


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthCheck:
    """Tests for attribution service health."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/attribution/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
```

---

## Summary

Dit implementatieplan bevat:

| Component | Lines | File |
|-----------|-------|------|
| Types (TS) | ~150 | `types/Attribution.ts` |
| Processor (TS) | ~600 | `lib/attributionProcessor.ts` |
| Service (PY) | ~400 | `services/attribution_service.py` |
| API (PY) | ~350 | `api/attribution.py` |
| Models (PY) | ~100 | `models/attribution.py` |
| Migration | ~80 | `alembic/versions/008_*.py` |
| Dashboard | ~500 | `attribution-dashboard.html` |
| Tests | ~350 | `test_attribution_api.py` |
| **Total** | **~2,530** | 8 files |

Wil je dat ik deze files nu aanmaak in de codebase?
```

---

Ik ga door met de API endpoints en de dashboard:

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create Week 21-22 Implementation Plan document", "status": "completed", "activeForm": "Creating Week 21-22 Implementation Plan"}, {"content": "Write AttributionProcessor TypeScript skeleton", "status": "completed", "activeForm": "Writing AttributionProcessor skeleton"}, {"content": "Write attribution_service.py Python skeleton", "status": "completed", "activeForm": "Writing attribution service skeleton"}, {"content": "Write attribution-dashboard.html skeleton", "status": "in_progress", "activeForm": "Writing dashboard skeleton"}, {"content": "Write test specifications", "status": "pending", "activeForm": "Writing test specifications"}]