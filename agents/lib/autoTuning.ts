/**
 * Auto-Tuning Library
 *
 * Week 25-26: AgentEvolver Integration - Auto-tuning for Agents
 * Based on: github.com/zeeneddie/AgentEvolver
 *
 * Implements automatic tuning of:
 * - Validation thresholds
 * - Exploration rates
 * - Peer assistance thresholds
 * - Learning parameters
 *
 * Author: Claude Code (Week 25 Day 4)
 * Date: 2025-11-22
 */

import { AgentName, WorkType } from '../types/AgentTypes';

// ============================================================================
// TYPES
// ============================================================================

export interface ThresholdConfig {
  minConfidence: number;
  minQualityScore: number;
  maxRetries: number;
  validationStrictness: 'low' | 'medium' | 'high';
}

export interface TuningResult<T> {
  agentId: AgentName;
  previousValue: T;
  newValue: T;
  confidence: number;
  reasoning: string;
  timestamp: Date;
}

export interface PerformanceData {
  successRate: number;
  averageQuality: number;
  averageDuration: number;
  recentTrend: 'improving' | 'stable' | 'declining';
  sampleSize: number;
}

export interface TuningConfig {
  // Learning parameters
  learningRate: number;
  adaptationSpeed: 'slow' | 'normal' | 'fast';

  // Boundaries
  minExplorationRate: number;
  maxExplorationRate: number;
  minConfidenceThreshold: number;
  maxConfidenceThreshold: number;

  // Behavior
  autoTuneEnabled: boolean;
  tuningInterval: number; // hours
}

// ============================================================================
// DEFAULT CONFIGURATIONS
// ============================================================================

const DEFAULT_THRESHOLD_CONFIG: ThresholdConfig = {
  minConfidence: 0.6,
  minQualityScore: 70,
  maxRetries: 3,
  validationStrictness: 'medium'
};

const DEFAULT_TUNING_CONFIG: TuningConfig = {
  learningRate: 0.1,
  adaptationSpeed: 'normal',
  minExplorationRate: 0.05,
  maxExplorationRate: 0.4,
  minConfidenceThreshold: 0.3,
  maxConfidenceThreshold: 0.9,
  autoTuneEnabled: true,
  tuningInterval: 24
};

// ============================================================================
// AUTO-TUNING CLASS
// ============================================================================

export class AutoTuning {
  private config: TuningConfig;
  private agentConfigs: Map<AgentName, ThresholdConfig> = new Map();
  private explorationRates: Map<AgentName, number> = new Map();
  private peerThresholds: Map<AgentName, number> = new Map();
  private tuningHistory: TuningResult<any>[] = [];

  constructor(config: Partial<TuningConfig> = {}) {
    this.config = { ...DEFAULT_TUNING_CONFIG, ...config };
    this.initializeDefaults();
  }

  private initializeDefaults(): void {
    const agents: AgentName[] = [
      'Felix', 'Marcus', 'Quinn', 'Betty', 'Eliza',
      'Tessa', 'Miguel', 'Diana', 'Peter', 'Paul'
    ];

    for (const agent of agents) {
      this.agentConfigs.set(agent, { ...DEFAULT_THRESHOLD_CONFIG });
      this.explorationRates.set(agent, 0.2);
      this.peerThresholds.set(agent, 0.6);
    }
  }

  // -------------------------------------------------------------------------
  // VALIDATION THRESHOLD TUNING
  // -------------------------------------------------------------------------

  /**
   * Tune validation thresholds based on success rates.
   *
   * Strategy:
   * - High success rate → increase strictness (more selective)
   * - Low success rate → decrease strictness (more inclusive)
   * - Stable performance → fine-tune based on quality distribution
   */
  async tuneValidationThresholds(
    agentId: AgentName,
    performance?: PerformanceData
  ): Promise<TuningResult<ThresholdConfig>> {
    const currentConfig = this.agentConfigs.get(agentId) || { ...DEFAULT_THRESHOLD_CONFIG };
    const newConfig = { ...currentConfig };

    // Simulate performance data if not provided
    const perf = performance || await this.getPerformanceData(agentId);

    let reasoning = '';

    // Adjust minConfidence based on success rate
    if (perf.successRate > 0.85) {
      // Very high success - increase selectivity
      newConfig.minConfidence = Math.min(
        this.config.maxConfidenceThreshold,
        currentConfig.minConfidence + (0.05 * this.config.learningRate * 10)
      );
      newConfig.validationStrictness = 'high';
      reasoning = `High success rate (${(perf.successRate * 100).toFixed(1)}%), increasing selectivity`;
    } else if (perf.successRate < 0.5) {
      // Low success - decrease selectivity
      newConfig.minConfidence = Math.max(
        this.config.minConfidenceThreshold,
        currentConfig.minConfidence - (0.1 * this.config.learningRate * 10)
      );
      newConfig.validationStrictness = 'low';
      reasoning = `Low success rate (${(perf.successRate * 100).toFixed(1)}%), decreasing selectivity`;
    } else {
      // Moderate - fine-tune based on quality
      if (perf.averageQuality > 80) {
        newConfig.minQualityScore = Math.min(90, currentConfig.minQualityScore + 5);
      } else if (perf.averageQuality < 60) {
        newConfig.minQualityScore = Math.max(50, currentConfig.minQualityScore - 5);
      }
      reasoning = `Moderate success rate, fine-tuning quality threshold`;
    }

    // Adjust retries based on trend
    if (perf.recentTrend === 'declining') {
      newConfig.maxRetries = Math.min(5, currentConfig.maxRetries + 1);
      reasoning += '; declining trend - allowing more retries';
    } else if (perf.recentTrend === 'improving' && currentConfig.maxRetries > 2) {
      newConfig.maxRetries = currentConfig.maxRetries - 1;
      reasoning += '; improving trend - reducing max retries';
    }

    // Update config
    this.agentConfigs.set(agentId, newConfig);

    const result: TuningResult<ThresholdConfig> = {
      agentId,
      previousValue: currentConfig,
      newValue: newConfig,
      confidence: Math.min(0.9, 0.5 + (perf.sampleSize / 100)),
      reasoning,
      timestamp: new Date()
    };

    this.tuningHistory.push(result);
    return result;
  }

  // -------------------------------------------------------------------------
  // EXPLORATION RATE TUNING
  // -------------------------------------------------------------------------

  /**
   * Tune exploration rate (try new approaches vs use known patterns).
   *
   * Strategy:
   * - If patterns are working well → decrease exploration
   * - If patterns are stale → increase exploration
   * - If agent is new/has few experiences → increase exploration
   */
  async tuneExplorationRate(
    agentId: AgentName,
    experienceCount?: number
  ): Promise<TuningResult<number>> {
    const currentRate = this.explorationRates.get(agentId) || 0.2;
    let newRate = currentRate;
    let reasoning = '';

    // Simulate experience count if not provided
    const expCount = experienceCount ?? Math.floor(Math.random() * 100);

    if (expCount < 10) {
      // Few experiences - explore more
      newRate = Math.min(
        this.config.maxExplorationRate,
        currentRate + 0.1
      );
      reasoning = `Low experience count (${expCount}), increasing exploration`;
    } else if (expCount > 50) {
      // Many experiences - rely more on patterns
      const performance = await this.getPerformanceData(agentId);

      if (performance.successRate > 0.8) {
        // Patterns are working - reduce exploration
        newRate = Math.max(
          this.config.minExplorationRate,
          currentRate - 0.05
        );
        reasoning = `High success with patterns, reducing exploration`;
      } else if (performance.successRate < 0.5) {
        // Patterns aren't working - increase exploration
        newRate = Math.min(
          this.config.maxExplorationRate,
          currentRate + 0.1
        );
        reasoning = `Low success with patterns, increasing exploration`;
      } else {
        reasoning = `Moderate performance, maintaining exploration rate`;
      }
    } else {
      reasoning = `Moderate experience count, maintaining exploration rate`;
    }

    // Clamp to boundaries
    newRate = Math.max(
      this.config.minExplorationRate,
      Math.min(this.config.maxExplorationRate, newRate)
    );

    this.explorationRates.set(agentId, newRate);

    const result: TuningResult<number> = {
      agentId,
      previousValue: currentRate,
      newValue: newRate,
      confidence: 0.7,
      reasoning,
      timestamp: new Date()
    };

    this.tuningHistory.push(result);
    return result;
  }

  // -------------------------------------------------------------------------
  // PEER ASSISTANCE THRESHOLD TUNING
  // -------------------------------------------------------------------------

  /**
   * Tune confidence threshold for peer assistance.
   *
   * Strategy:
   * - If agent often needs help → lower threshold (ask sooner)
   * - If agent rarely needs help → raise threshold (be more independent)
   * - Balance between efficiency and accuracy
   */
  async tunePeerAssistanceThreshold(
    agentId: AgentName,
    assistanceRate?: number
  ): Promise<TuningResult<number>> {
    const currentThreshold = this.peerThresholds.get(agentId) || 0.6;
    let newThreshold = currentThreshold;
    let reasoning = '';

    // Simulate assistance rate if not provided
    const rate = assistanceRate ?? Math.random();

    if (rate > 0.3) {
      // Frequently asking for help - lower threshold slightly
      // (ask for help earlier, before getting stuck)
      newThreshold = Math.max(0.4, currentThreshold - 0.05);
      reasoning = `High assistance rate (${(rate * 100).toFixed(1)}%), lowering threshold to ask sooner`;
    } else if (rate < 0.1) {
      // Rarely asking for help - might be missing opportunities
      // Check if success rate is still good
      const performance = await this.getPerformanceData(agentId);

      if (performance.successRate > 0.8) {
        // High success - agent is doing well independently
        newThreshold = Math.min(0.8, currentThreshold + 0.05);
        reasoning = `Low assistance rate with high success, raising threshold`;
      } else {
        // Low success but not asking for help - should ask more
        newThreshold = Math.max(0.4, currentThreshold - 0.1);
        reasoning = `Low assistance rate but lower success, lowering threshold`;
      }
    } else {
      reasoning = `Moderate assistance rate, maintaining threshold`;
    }

    this.peerThresholds.set(agentId, newThreshold);

    const result: TuningResult<number> = {
      agentId,
      previousValue: currentThreshold,
      newValue: newThreshold,
      confidence: 0.6,
      reasoning,
      timestamp: new Date()
    };

    this.tuningHistory.push(result);
    return result;
  }

  // -------------------------------------------------------------------------
  // BULK TUNING
  // -------------------------------------------------------------------------

  /**
   * Tune all parameters for an agent.
   */
  async tuneAll(agentId: AgentName): Promise<{
    thresholds: TuningResult<ThresholdConfig>;
    explorationRate: TuningResult<number>;
    peerThreshold: TuningResult<number>;
  }> {
    const thresholds = await this.tuneValidationThresholds(agentId);
    const explorationRate = await this.tuneExplorationRate(agentId);
    const peerThreshold = await this.tunePeerAssistanceThreshold(agentId);

    return { thresholds, explorationRate, peerThreshold };
  }

  /**
   * Tune all agents.
   */
  async tuneAllAgents(): Promise<Map<AgentName, any>> {
    const results = new Map<AgentName, any>();

    const agents: AgentName[] = [
      'Felix', 'Marcus', 'Quinn', 'Betty', 'Eliza',
      'Tessa', 'Miguel', 'Diana', 'Peter', 'Paul'
    ];

    for (const agent of agents) {
      results.set(agent, await this.tuneAll(agent));
    }

    return results;
  }

  // -------------------------------------------------------------------------
  // GETTERS
  // -------------------------------------------------------------------------

  getThresholdConfig(agentId: AgentName): ThresholdConfig {
    return this.agentConfigs.get(agentId) || { ...DEFAULT_THRESHOLD_CONFIG };
  }

  getExplorationRate(agentId: AgentName): number {
    return this.explorationRates.get(agentId) || 0.2;
  }

  getPeerThreshold(agentId: AgentName): number {
    return this.peerThresholds.get(agentId) || 0.6;
  }

  getTuningHistory(limit: number = 50): TuningResult<any>[] {
    return this.tuningHistory.slice(-limit);
  }

  // -------------------------------------------------------------------------
  // HELPERS
  // -------------------------------------------------------------------------

  private async getPerformanceData(agentId: AgentName): Promise<PerformanceData> {
    // In production, this would fetch from the experience store
    // For now, return simulated data

    return {
      successRate: 0.6 + Math.random() * 0.3,
      averageQuality: 60 + Math.random() * 30,
      averageDuration: 5000 + Math.random() * 10000,
      recentTrend: ['improving', 'stable', 'declining'][
        Math.floor(Math.random() * 3)
      ] as 'improving' | 'stable' | 'declining',
      sampleSize: Math.floor(20 + Math.random() * 80)
    };
  }
}

// ============================================================================
// SINGLETON EXPORT
// ============================================================================

let autoTuningInstance: AutoTuning | null = null;

export function getAutoTuning(config?: Partial<TuningConfig>): AutoTuning {
  if (!autoTuningInstance) {
    autoTuningInstance = new AutoTuning(config);
  }
  return autoTuningInstance;
}

export default AutoTuning;
