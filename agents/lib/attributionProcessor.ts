/**
 * Attribution Processor - Core Logic for Self-Attributing Agents
 * Week 21-22 Implementation
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
  StepData,
  QualityGateResult,
  ValidationResult,
  calculateConfidenceLevel
} from '../types/Attribution';

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

  constructor(config: Partial<AttributionConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
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

    const attributedSteps = this.analyzeSteps(steps, outcome);
    const causalFactors = this.extractCausalFactors(attributedSteps, qualityGateResults, validationHistory, outcome);
    const qualityGateAttributions = this.analyzeQualityGates(qualityGateResults);
    const validationAttributions = this.analyzeValidationHistory(validationHistory);
    const confidence = this.calculateAttributionConfidence(attributedSteps, causalFactors, outcome);

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

    return attribution;
  }

  /**
   * Analyze individual steps and assign impact scores
   */
  private analyzeSteps(steps: StepData[], outcome: OutcomeType): AttributedStep[] {
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

    return attributedSteps.sort((a, b) => Math.abs(b.impactScore) - Math.abs(a.impactScore));
  }

  private calculateStepImpact(step: StepData, outcome: OutcomeType): ImpactLevel {
    if (step.isCriticalPath) {
      if (outcome === 'SUCCESS' && step.succeeded) return 'CRITICAL';
      if (outcome === 'FAILURE' && !step.succeeded) return 'CRITICAL';
    }
    if (step.retryCount && step.retryCount > 0 && step.succeeded) return 'IMPORTANT';
    if (step.experienceConsulted && step.succeeded) return 'IMPORTANT';
    if (step.duration > step.expectedDuration * 1.5) return 'MINOR';
    if (!step.succeeded && outcome === 'FAILURE') return 'NEGATIVE';
    return 'NEUTRAL';
  }

  private calculateImpactScore(step: StepData, outcome: OutcomeType): number {
    let score = 0;
    if (step.succeeded) score += 0.3;
    else score -= 0.5;
    if (step.experienceConsulted && step.succeeded) score += 0.2;
    if (step.patternUsed && step.succeeded) score += 0.15;
    if (step.retryCount) score -= step.retryCount * 0.1;
    if (step.duration > step.expectedDuration * 2) score -= 0.1;
    if (step.isCriticalPath) score *= 1.5;
    return Math.max(-1, Math.min(1, score));
  }

  private generateStepReasoning(step: StepData, impact: ImpactLevel, outcome: OutcomeType): string {
    const reasons: string[] = [];
    if (step.experienceConsulted && step.succeeded) reasons.push('Successfully applied learned experience');
    if (step.patternUsed) reasons.push(`Applied pattern: ${step.patternUsed}`);
    if (step.retryCount && step.retryCount > 0) {
      reasons.push(`Required ${step.retryCount} retries before ${step.succeeded ? 'succeeding' : 'failing'}`);
    }
    if (step.isCriticalPath) reasons.push('On critical path - directly affected outcome');
    if (!step.succeeded && outcome === 'FAILURE') reasons.push('Step failure contributed to overall task failure');
    return reasons.length > 0 ? reasons.join('. ') : 'Standard execution';
  }

  /**
   * Extract causal factors from analysis
   */
  private extractCausalFactors(
    steps: AttributedStep[],
    qualityGates: QualityGateResult[],
    validations: ValidationResult[],
    outcome: OutcomeType
  ): CausalFactor[] {
    const factors: CausalFactor[] = [];

    // Experience usage factor
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

    // Early validation factor
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

    // Quality gate effectiveness
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

    // Failure patterns
    if (outcome === 'FAILURE') {
      const failedSteps = steps.filter(s => s.impactScore < 0);
      if (failedSteps.length > 0) {
        factors.push({
          factorId: `factor_${Date.now()}_fail`,
          factorType: 'MISSING_EDGE_CASE',
          description: `${failedSteps.length} steps failed`,
          contribution: -0.4,
          evidence: failedSteps.map(s => s.stepName),
          relatedSteps: failedSteps.map(s => s.stepId)
        });
      }

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

    return factors.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  }

  private analyzeQualityGates(results: QualityGateResult[]): QualityGateAttribution[] {
    return results.map(result => ({
      gateType: result.gateType,
      gateName: result.gateName,
      passed: result.passed,
      issuesCaught: result.issuesCaught || 0,
      falsePositives: result.falsePositives || 0,
      falseNegatives: 0,
      effectiveness: this.calculateGateEffectiveness(result),
      recommendedAction: this.generateGateRecommendation(result)
    }));
  }

  private calculateGateEffectiveness(result: QualityGateResult): number {
    if (result.totalChecks === 0) return 0;
    const truePositiveRate = result.issuesCaught / Math.max(1, result.totalChecks);
    const falsePositivePenalty = (result.falsePositives || 0) * 0.1;
    return Math.max(0, Math.min(1, truePositiveRate - falsePositivePenalty));
  }

  private generateGateRecommendation(result: QualityGateResult): string | undefined {
    if ((result.falsePositives || 0) > result.issuesCaught) {
      return 'Consider relaxing gate rules - high false positive rate';
    }
    if (result.issuesCaught === 0 && result.totalChecks > 10) {
      return 'Gate may be too lenient - no issues caught';
    }
    return undefined;
  }

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

  private calculateAttributionConfidence(
    steps: AttributedStep[],
    factors: CausalFactor[],
    outcome: OutcomeType
  ): number {
    let confidence = 0.5;
    confidence += Math.min(0.2, steps.length * 0.02);
    confidence += Math.min(0.15, factors.length * 0.03);
    if (outcome !== 'PARTIAL') confidence += 0.1;
    const experienceRatio = steps.filter(s => s.experienceUsed).length / Math.max(1, steps.length);
    confidence += experienceRatio * 0.1;
    return Math.min(1, confidence);
  }

  // ==========================================================================
  // Feedback Generation
  // ==========================================================================

  generateFeedback(attribution: Attribution): AttributionFeedback {
    const lessons = this.extractLessons(attribution);
    const adjustments = this.recommendAdjustments(attribution);

    return {
      attributionId: attribution.id,
      agentId: attribution.agentId,
      feedbackType: attribution.outcome === 'SUCCESS' ? 'SUCCESS_REINFORCEMENT' : 'FAILURE_CORRECTION',
      lessons,
      recommendedAdjustments: adjustments,
      deliveredAt: new Date()
    };
  }

  private extractLessons(attribution: Attribution): Lesson[] {
    const lessons: Lesson[] = [];

    // Lessons from successful patterns
    const successfulPatterns = attribution.keySteps.filter(s => s.impactScore > 0.2 && s.patternApplied);
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
    const failedSteps = attribution.keySteps.filter(s => s.impactScore < -0.2);
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
      if (Math.abs(factor.contribution) > 0.2) {
        lessons.push({
          lessonId: `lesson_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
          lessonType: factor.contribution > 0 ? 'DO_MORE' : 'AVOID',
          description: factor.description,
          context: factor.evidence.join(', '),
          confidence: Math.abs(factor.contribution)
        });
      }
    }

    return lessons.sort((a, b) => b.confidence - a.confidence);
  }

  private recommendAdjustments(attribution: Attribution): Adjustment[] {
    const adjustments: Adjustment[] = [];

    const experienceHelpful = attribution.keySteps.filter(s => s.experienceUsed && s.impactScore > 0).length;
    if (experienceHelpful > 2) {
      adjustments.push({
        adjustmentType: 'WEIGHT_UPDATE',
        target: 'experienceWeight',
        currentValue: 0.5,
        recommendedValue: 0.7,
        reasoning: `Experience consultation was helpful in ${experienceHelpful} steps`
      });
    }

    const successfulNewApproach = attribution.keySteps.find(s => s.impactScore > 0.5 && !s.patternApplied);
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
}

export default AttributionProcessor;
