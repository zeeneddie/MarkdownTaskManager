/**
 * A/B Testing Framework for Agents
 *
 * Enables controlled experiments to compare:
 * - Different agent configurations
 * - Prompt variations
 * - Model selections
 * - Pattern strategies
 * - Validation approaches
 *
 * Part of AgentEvolver Phase B (Week 20).
 *
 * @author Claude Code (Week 20 Day 5)
 * @date 2025-11-22
 */

import { getMetricsCollector, MetricsCollector } from './agentMetrics';

// ============================================================================
// Types
// ============================================================================

export interface ExperimentVariant {
  id: string;
  name: string;
  description: string;
  config: Record<string, any>;
  weight: number;  // Traffic allocation (0-100)
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  targetAgent: string;          // Agent ID or 'all'
  targetWorkType?: string;      // Optional work type filter
  variants: ExperimentVariant[];
  status: 'draft' | 'running' | 'paused' | 'completed' | 'stopped';
  startTime?: string;
  endTime?: string;
  minSampleSize: number;        // Minimum samples per variant
  maxDurationHours: number;     // Maximum experiment duration
  successMetric: string;        // Primary metric to optimize
  secondaryMetrics: string[];   // Additional metrics to track
}

export interface VariantAssignment {
  experimentId: string;
  variantId: string;
  assignmentTime: string;
  context: Record<string, any>;
}

export interface VariantResult {
  variantId: string;
  sampleSize: number;
  metrics: {
    successRate: number;
    avgExecutionTime: number;
    avgQualityScore: number;
    avgValidationIterations: number;
    confidenceInterval: [number, number];
  };
  rawValues: number[];
}

export interface ExperimentResult {
  experimentId: string;
  experimentName: string;
  status: 'insufficient_data' | 'no_winner' | 'winner_found';
  variantResults: VariantResult[];
  winner?: {
    variantId: string;
    improvement: number;        // Percentage improvement
    confidence: number;         // Statistical confidence
  };
  recommendation: string;
  analysis: string;
}

// ============================================================================
// A/B Testing Service
// ============================================================================

export class ABTestingService {
  private experiments: Map<string, Experiment> = new Map();
  private assignments: Map<string, VariantAssignment> = new Map();
  private variantMetrics: Map<string, number[]> = new Map();  // variantId -> metric values
  private metricsCollector: MetricsCollector;

  constructor(collector?: MetricsCollector) {
    this.metricsCollector = collector || getMetricsCollector();
  }

  // ============================================================================
  // Experiment Management
  // ============================================================================

  /**
   * Create a new experiment
   */
  createExperiment(experiment: Omit<Experiment, 'status'>): Experiment {
    const fullExperiment: Experiment = {
      ...experiment,
      status: 'draft'
    };

    // Validate weights sum to 100
    const totalWeight = experiment.variants.reduce((sum, v) => sum + v.weight, 0);
    if (totalWeight !== 100) {
      throw new Error(`Variant weights must sum to 100, got ${totalWeight}`);
    }

    this.experiments.set(experiment.id, fullExperiment);
    console.log(`[ABTesting] Created experiment: ${experiment.name}`);

    return fullExperiment;
  }

  /**
   * Start an experiment
   */
  startExperiment(experimentId: string): void {
    const experiment = this.experiments.get(experimentId);
    if (!experiment) {
      throw new Error(`Experiment not found: ${experimentId}`);
    }

    experiment.status = 'running';
    experiment.startTime = new Date().toISOString();

    // Initialize metrics tracking for variants
    for (const variant of experiment.variants) {
      this.variantMetrics.set(variant.id, []);
    }

    console.log(`[ABTesting] Started experiment: ${experiment.name}`);
  }

  /**
   * Stop an experiment
   */
  stopExperiment(experimentId: string): void {
    const experiment = this.experiments.get(experimentId);
    if (!experiment) {
      throw new Error(`Experiment not found: ${experimentId}`);
    }

    experiment.status = 'stopped';
    experiment.endTime = new Date().toISOString();

    console.log(`[ABTesting] Stopped experiment: ${experiment.name}`);
  }

  /**
   * Complete an experiment
   */
  completeExperiment(experimentId: string): void {
    const experiment = this.experiments.get(experimentId);
    if (!experiment) {
      throw new Error(`Experiment not found: ${experimentId}`);
    }

    experiment.status = 'completed';
    experiment.endTime = new Date().toISOString();

    console.log(`[ABTesting] Completed experiment: ${experiment.name}`);
  }

  /**
   * Get an experiment by ID
   */
  getExperiment(experimentId: string): Experiment | undefined {
    return this.experiments.get(experimentId);
  }

  /**
   * List all experiments
   */
  listExperiments(status?: Experiment['status']): Experiment[] {
    const all = Array.from(this.experiments.values());
    if (status) {
      return all.filter(e => e.status === status);
    }
    return all;
  }

  // ============================================================================
  // Variant Assignment
  // ============================================================================

  /**
   * Assign a variant to a request
   */
  assignVariant(
    experimentId: string,
    requestId: string,
    agentId: string,
    workType?: string
  ): ExperimentVariant | null {
    const experiment = this.experiments.get(experimentId);
    if (!experiment || experiment.status !== 'running') {
      return null;
    }

    // Check if experiment applies to this agent/workType
    if (experiment.targetAgent !== 'all' && experiment.targetAgent !== agentId) {
      return null;
    }
    if (experiment.targetWorkType && experiment.targetWorkType !== workType) {
      return null;
    }

    // Check for existing assignment
    const existingKey = `${experimentId}:${requestId}`;
    const existing = this.assignments.get(existingKey);
    if (existing) {
      return experiment.variants.find(v => v.id === existing.variantId) || null;
    }

    // Weighted random assignment
    const variant = this.selectVariant(experiment.variants);

    // Store assignment
    this.assignments.set(existingKey, {
      experimentId,
      variantId: variant.id,
      assignmentTime: new Date().toISOString(),
      context: { agentId, workType }
    });

    console.log(`[ABTesting] Assigned variant '${variant.name}' for ${requestId}`);

    return variant;
  }

  /**
   * Get assigned variant for a request
   */
  getAssignedVariant(experimentId: string, requestId: string): ExperimentVariant | null {
    const key = `${experimentId}:${requestId}`;
    const assignment = this.assignments.get(key);
    if (!assignment) return null;

    const experiment = this.experiments.get(experimentId);
    if (!experiment) return null;

    return experiment.variants.find(v => v.id === assignment.variantId) || null;
  }

  /**
   * Select variant based on weights
   */
  private selectVariant(variants: ExperimentVariant[]): ExperimentVariant {
    const random = Math.random() * 100;
    let cumulative = 0;

    for (const variant of variants) {
      cumulative += variant.weight;
      if (random <= cumulative) {
        return variant;
      }
    }

    // Fallback to last variant
    return variants[variants.length - 1];
  }

  // ============================================================================
  // Metrics Recording
  // ============================================================================

  /**
   * Record a metric for a variant
   */
  recordMetric(
    experimentId: string,
    variantId: string,
    metricValue: number
  ): void {
    const experiment = this.experiments.get(experimentId);
    if (!experiment || experiment.status !== 'running') {
      return;
    }

    const metrics = this.variantMetrics.get(variantId) || [];
    metrics.push(metricValue);
    this.variantMetrics.set(variantId, metrics);

    // Check if we've reached min sample size
    this.checkExperimentCompletion(experimentId);
  }

  /**
   * Record result for an assigned variant
   */
  recordVariantResult(
    experimentId: string,
    requestId: string,
    success: boolean,
    executionTime: number,
    qualityScore: number,
    validationIterations: number
  ): void {
    const key = `${experimentId}:${requestId}`;
    const assignment = this.assignments.get(key);
    if (!assignment) return;

    const experiment = this.experiments.get(experimentId);
    if (!experiment) return;

    // Record primary metric (success rate by default)
    const metricValue = this.getMetricValue(
      experiment.successMetric,
      success,
      executionTime,
      qualityScore,
      validationIterations
    );

    this.recordMetric(experimentId, assignment.variantId, metricValue);
  }

  /**
   * Get metric value based on metric type
   */
  private getMetricValue(
    metricType: string,
    success: boolean,
    executionTime: number,
    qualityScore: number,
    validationIterations: number
  ): number {
    switch (metricType) {
      case 'success_rate':
        return success ? 1 : 0;
      case 'execution_time':
        return executionTime;
      case 'quality_score':
        return qualityScore;
      case 'validation_iterations':
        return validationIterations;
      default:
        return success ? 1 : 0;
    }
  }

  // ============================================================================
  // Analysis
  // ============================================================================

  /**
   * Analyze experiment results
   */
  analyzeExperiment(experimentId: string): ExperimentResult {
    const experiment = this.experiments.get(experimentId);
    if (!experiment) {
      throw new Error(`Experiment not found: ${experimentId}`);
    }

    const variantResults: VariantResult[] = [];

    for (const variant of experiment.variants) {
      const values = this.variantMetrics.get(variant.id) || [];
      const result = this.calculateVariantResult(variant.id, values, experiment.successMetric);
      variantResults.push(result);
    }

    // Check if we have enough data
    const hasEnoughData = variantResults.every(
      vr => vr.sampleSize >= experiment.minSampleSize
    );

    if (!hasEnoughData) {
      return {
        experimentId,
        experimentName: experiment.name,
        status: 'insufficient_data',
        variantResults,
        recommendation: 'Continue collecting data until minimum sample size is reached.',
        analysis: this.generateAnalysisText(variantResults, experiment)
      };
    }

    // Find winner using statistical significance
    const winner = this.findWinner(variantResults, experiment.successMetric);

    return {
      experimentId,
      experimentName: experiment.name,
      status: winner ? 'winner_found' : 'no_winner',
      variantResults,
      winner,
      recommendation: this.generateRecommendation(winner, variantResults, experiment),
      analysis: this.generateAnalysisText(variantResults, experiment)
    };
  }

  /**
   * Calculate variant result
   */
  private calculateVariantResult(
    variantId: string,
    values: number[],
    metricType: string
  ): VariantResult {
    const sampleSize = values.length;

    if (sampleSize === 0) {
      return {
        variantId,
        sampleSize: 0,
        metrics: {
          successRate: 0,
          avgExecutionTime: 0,
          avgQualityScore: 0,
          avgValidationIterations: 0,
          confidenceInterval: [0, 0]
        },
        rawValues: []
      };
    }

    const mean = values.reduce((a, b) => a + b, 0) / sampleSize;
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / sampleSize;
    const stdDev = Math.sqrt(variance);

    // 95% confidence interval
    const margin = 1.96 * (stdDev / Math.sqrt(sampleSize));
    const ci: [number, number] = [mean - margin, mean + margin];

    // For success_rate metric, values are 0 or 1
    const successRate = metricType === 'success_rate' ? mean * 100 : 0;

    return {
      variantId,
      sampleSize,
      metrics: {
        successRate,
        avgExecutionTime: metricType === 'execution_time' ? mean : 0,
        avgQualityScore: metricType === 'quality_score' ? mean : 0,
        avgValidationIterations: metricType === 'validation_iterations' ? mean : 0,
        confidenceInterval: ci
      },
      rawValues: values
    };
  }

  /**
   * Find winner using statistical significance
   */
  private findWinner(
    variantResults: VariantResult[],
    metricType: string
  ): ExperimentResult['winner'] | undefined {
    if (variantResults.length < 2) return undefined;

    // Sort by primary metric
    const sorted = [...variantResults].sort((a, b) => {
      return this.getComparisonValue(b, metricType) - this.getComparisonValue(a, metricType);
    });

    const best = sorted[0];
    const secondBest = sorted[1];

    const bestValue = this.getComparisonValue(best, metricType);
    const secondBestValue = this.getComparisonValue(secondBest, metricType);

    // Check if confidence intervals overlap
    const noOverlap = best.metrics.confidenceInterval[0] > secondBest.metrics.confidenceInterval[1];

    if (!noOverlap) {
      return undefined;  // No statistically significant winner
    }

    const improvement = secondBestValue > 0
      ? ((bestValue - secondBestValue) / secondBestValue) * 100
      : 0;

    return {
      variantId: best.variantId,
      improvement,
      confidence: 95  // 95% confidence interval
    };
  }

  /**
   * Get comparison value based on metric type
   */
  private getComparisonValue(result: VariantResult, metricType: string): number {
    switch (metricType) {
      case 'success_rate':
        return result.metrics.successRate;
      case 'execution_time':
        return -result.metrics.avgExecutionTime;  // Lower is better
      case 'quality_score':
        return result.metrics.avgQualityScore;
      case 'validation_iterations':
        return -result.metrics.avgValidationIterations;  // Lower is better
      default:
        return result.metrics.successRate;
    }
  }

  /**
   * Generate recommendation text
   */
  private generateRecommendation(
    winner: ExperimentResult['winner'] | undefined,
    variantResults: VariantResult[],
    experiment: Experiment
  ): string {
    if (!winner) {
      return 'No statistically significant winner. Consider extending the experiment or increasing sample size.';
    }

    const winningVariant = experiment.variants.find(v => v.id === winner.variantId);
    const variantName = winningVariant?.name || winner.variantId;

    return `Adopt variant "${variantName}" which shows ${winner.improvement.toFixed(1)}% improvement with ${winner.confidence}% confidence.`;
  }

  /**
   * Generate analysis text
   */
  private generateAnalysisText(
    variantResults: VariantResult[],
    experiment: Experiment
  ): string {
    const lines: string[] = [];
    lines.push(`Experiment: ${experiment.name}`);
    lines.push(`Metric: ${experiment.successMetric}`);
    lines.push('');

    for (const result of variantResults) {
      const variant = experiment.variants.find(v => v.id === result.variantId);
      const name = variant?.name || result.variantId;
      lines.push(`${name}:`);
      lines.push(`  Samples: ${result.sampleSize}`);
      lines.push(`  Success Rate: ${result.metrics.successRate.toFixed(1)}%`);
      lines.push(`  95% CI: [${result.metrics.confidenceInterval[0].toFixed(3)}, ${result.metrics.confidenceInterval[1].toFixed(3)}]`);
      lines.push('');
    }

    return lines.join('\n');
  }

  /**
   * Check if experiment should be completed
   */
  private checkExperimentCompletion(experimentId: string): void {
    const experiment = this.experiments.get(experimentId);
    if (!experiment || experiment.status !== 'running') return;

    // Check max duration
    if (experiment.startTime) {
      const duration = Date.now() - new Date(experiment.startTime).getTime();
      const maxDuration = experiment.maxDurationHours * 60 * 60 * 1000;
      if (duration >= maxDuration) {
        this.completeExperiment(experimentId);
        return;
      }
    }

    // Check if all variants have reached min sample size
    const allReached = experiment.variants.every(variant => {
      const metrics = this.variantMetrics.get(variant.id) || [];
      return metrics.length >= experiment.minSampleSize;
    });

    if (allReached) {
      console.log(`[ABTesting] Minimum sample size reached for experiment: ${experiment.name}`);
      // Don't auto-complete, but notify
    }
  }
}

// ============================================================================
// Pre-built Experiment Templates
// ============================================================================

export const EXPERIMENT_TEMPLATES = {
  /**
   * Compare different LLM models for an agent
   */
  modelComparison: (agentId: string, modelA: string, modelB: string): Omit<Experiment, 'status'> => ({
    id: `model-${agentId}-${Date.now()}`,
    name: `Model Comparison: ${modelA} vs ${modelB}`,
    description: `Compare performance of ${modelA} and ${modelB} for agent ${agentId}`,
    targetAgent: agentId,
    variants: [
      { id: 'model-a', name: modelA, description: `Use ${modelA}`, config: { model: modelA }, weight: 50 },
      { id: 'model-b', name: modelB, description: `Use ${modelB}`, config: { model: modelB }, weight: 50 }
    ],
    minSampleSize: 30,
    maxDurationHours: 168,  // 1 week
    successMetric: 'success_rate',
    secondaryMetrics: ['execution_time', 'quality_score']
  }),

  /**
   * Compare experience consultation strategies
   */
  experienceStrategy: (agentId: string): Omit<Experiment, 'status'> => ({
    id: `experience-${agentId}-${Date.now()}`,
    name: `Experience Consultation: On vs Off`,
    description: `Compare agent performance with and without experience consultation`,
    targetAgent: agentId,
    variants: [
      { id: 'exp-on', name: 'With Experience', description: 'Consult experience before tasks', config: { enableExperience: true }, weight: 50 },
      { id: 'exp-off', name: 'Without Experience', description: 'No experience consultation', config: { enableExperience: false }, weight: 50 }
    ],
    minSampleSize: 50,
    maxDurationHours: 168,
    successMetric: 'success_rate',
    secondaryMetrics: ['execution_time', 'validation_iterations']
  }),

  /**
   * Compare validation iteration limits
   */
  validationIterations: (agentId: string): Omit<Experiment, 'status'> => ({
    id: `validation-${agentId}-${Date.now()}`,
    name: `Validation Iterations: 2 vs 3 vs 5`,
    description: `Compare success rates with different max validation iterations`,
    targetAgent: agentId,
    variants: [
      { id: 'iter-2', name: '2 Iterations', description: 'Max 2 validation iterations', config: { maxIterations: 2 }, weight: 33 },
      { id: 'iter-3', name: '3 Iterations', description: 'Max 3 validation iterations', config: { maxIterations: 3 }, weight: 34 },
      { id: 'iter-5', name: '5 Iterations', description: 'Max 5 validation iterations', config: { maxIterations: 5 }, weight: 33 }
    ],
    minSampleSize: 30,
    maxDurationHours: 168,
    successMetric: 'success_rate',
    secondaryMetrics: ['validation_iterations', 'execution_time']
  }),

  /**
   * Compare prompt variations
   */
  promptVariation: (agentId: string, prompts: { name: string; prompt: string }[]): Omit<Experiment, 'status'> => ({
    id: `prompt-${agentId}-${Date.now()}`,
    name: `Prompt Variation Test`,
    description: `Compare different prompt strategies for ${agentId}`,
    targetAgent: agentId,
    variants: prompts.map((p, i) => ({
      id: `prompt-${i}`,
      name: p.name,
      description: `Prompt variant: ${p.name}`,
      config: { systemPrompt: p.prompt },
      weight: Math.floor(100 / prompts.length)
    })),
    minSampleSize: 40,
    maxDurationHours: 336,  // 2 weeks
    successMetric: 'quality_score',
    secondaryMetrics: ['success_rate', 'execution_time']
  })
};

// ============================================================================
// Singleton Instance
// ============================================================================

let abTestingInstance: ABTestingService | null = null;

export function getABTestingService(): ABTestingService {
  if (!abTestingInstance) {
    abTestingInstance = new ABTestingService();
  }
  return abTestingInstance;
}

// ============================================================================
// Exports
// ============================================================================

export default {
  ABTestingService,
  EXPERIMENT_TEMPLATES,
  getABTestingService
};
