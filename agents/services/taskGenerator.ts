/**
 * Task Generator Service
 * Week 23-24: Self-Questioning Agents
 *
 * Enables agents to generate their own training tasks based on
 * skill gaps, failures, and unexplored areas.
 */

import { v4 as uuidv4 } from 'uuid';
import {
  TrainingTask,
  TaskScenario,
  ExpectedOutcome,
  TrainingTaskResult,
  SkillGap,
  SkillGapEvidence,
  GenerationStrategy,
  ImprovementMetrics,
  GeneratedTaskType,
  TaskDifficulty,
  TaskStatus,
  TaskSource,
  SkillGapSeverity,
  DEFAULT_AGENT_STRATEGIES
} from '../types/TaskGeneration';
import { Attribution, CausalFactor, OutcomeType } from '../types/Attribution';

// =============================================================================
// Interfaces
// =============================================================================

interface TaskGeneratorConfig {
  maxTasksPerGeneration: number;
  minConfidenceForSkillGap: number;
  defaultCooldownMs: number;
  enableExploration: boolean;
}

interface GenerationContext {
  agentId: string;
  recentAttributions: Attribution[];
  existingSkillGaps: SkillGap[];
  completedTasks: TrainingTask[];
  strategy: GenerationStrategy;
}

// =============================================================================
// Default Configuration
// =============================================================================

const DEFAULT_CONFIG: TaskGeneratorConfig = {
  maxTasksPerGeneration: 5,
  minConfidenceForSkillGap: 0.6,
  defaultCooldownMs: 3600000, // 1 hour
  enableExploration: true
};

// =============================================================================
// Task Generator Service
// =============================================================================

export class TaskGeneratorService {
  private config: TaskGeneratorConfig;
  private skillGapStore: Map<string, SkillGap[]> = new Map();
  private taskStore: Map<string, TrainingTask[]> = new Map();
  private resultStore: Map<string, TrainingTaskResult[]> = new Map();

  constructor(config: Partial<TaskGeneratorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  // ---------------------------------------------------------------------------
  // Main Generation Methods
  // ---------------------------------------------------------------------------

  /**
   * Generate training tasks for an agent based on their skill gaps and failures.
   */
  async generateTasksForAgent(
    agentId: string,
    recentAttributions: Attribution[],
    customStrategy?: Partial<GenerationStrategy>
  ): Promise<TrainingTask[]> {
    // Get or create strategy for agent
    const baseStrategy = DEFAULT_AGENT_STRATEGIES[agentId] || this.getDefaultStrategy(agentId);
    const strategy: GenerationStrategy = customStrategy
      ? { ...baseStrategy, ...customStrategy }
      : baseStrategy;

    // Analyze attributions to identify skill gaps
    const newSkillGaps = await this.analyzeAttributionsForSkillGaps(agentId, recentAttributions);

    // Get existing unaddressed skill gaps
    const existingGaps = this.getSkillGapsForAgent(agentId).filter(g => !g.addressed);
    const allGaps = [...existingGaps, ...newSkillGaps];

    // Prioritize gaps
    const prioritizedGaps = this.prioritizeSkillGaps(allGaps);

    // Generate tasks based on gaps and strategy
    const tasks: TrainingTask[] = [];
    const maxTasks = Math.min(strategy.maxTasksPerSession, this.config.maxTasksPerGeneration);

    for (let i = 0; i < maxTasks && i < prioritizedGaps.length; i++) {
      const gap = prioritizedGaps[i];
      const taskType = this.selectTaskTypeForGap(gap, strategy);
      const task = this.createTaskFromSkillGap(agentId, gap, taskType, strategy);
      tasks.push(task);
    }

    // Add exploration tasks if enabled and we have room
    if (this.config.enableExploration && tasks.length < maxTasks) {
      const explorationTask = this.createExplorationTask(agentId, strategy);
      if (explorationTask) {
        tasks.push(explorationTask);
      }
    }

    // Store tasks
    this.storeTasksForAgent(agentId, tasks);

    return tasks;
  }

  /**
   * Analyze attributions to identify skill gaps for an agent.
   */
  async analyzeAttributionsForSkillGaps(
    agentId: string,
    attributions: Attribution[]
  ): Promise<SkillGap[]> {
    const skillGaps: SkillGap[] = [];
    const agentAttributions = attributions.filter(a => a.agentId === agentId);

    for (const attribution of agentAttributions) {
      // Look for failure patterns
      if (attribution.outcome === OutcomeType.FAILURE || attribution.outcome === OutcomeType.PARTIAL) {
        const gaps = this.extractSkillGapsFromAttribution(attribution);
        skillGaps.push(...gaps);
      }

      // Look for low confidence areas even in successes
      if (attribution.confidence < this.config.minConfidenceForSkillGap) {
        const gap = this.createSkillGapFromLowConfidence(attribution);
        if (gap) {
          skillGaps.push(gap);
        }
      }
    }

    // Store new skill gaps
    for (const gap of skillGaps) {
      this.storeSkillGap(agentId, gap);
    }

    return skillGaps;
  }

  // ---------------------------------------------------------------------------
  // Skill Gap Analysis
  // ---------------------------------------------------------------------------

  private extractSkillGapsFromAttribution(attribution: Attribution): SkillGap[] {
    const gaps: SkillGap[] = [];

    // Analyze causal factors for negative impact
    const negativeFactors = attribution.causalFactors.filter(f => f.impact < 0);

    for (const factor of negativeFactors) {
      const evidence: SkillGapEvidence = {
        type: 'ATTRIBUTION_FAILURE',
        sourceId: attribution.id,
        description: factor.description,
        timestamp: new Date()
      };

      const gap: SkillGap = {
        id: uuidv4(),
        agentId: attribution.agentId,
        agentName: attribution.agentName,
        description: `Skill gap identified: ${factor.factor}`,
        area: this.categorizeFactorToArea(factor),
        severity: this.calculateSeverity(factor.impact),
        evidence: [evidence],
        addressed: false,
        generatedTaskIds: [],
        identifiedAt: new Date()
      };

      gaps.push(gap);
    }

    // Analyze validation failures
    if (attribution.validationHistory) {
      const failedPhases = attribution.validationHistory
        .filter(v => !v.passed)
        .map(v => v.phase);

      const uniquePhases = [...new Set(failedPhases)];
      for (const phase of uniquePhases) {
        const gap: SkillGap = {
          id: uuidv4(),
          agentId: attribution.agentId,
          agentName: attribution.agentName,
          description: `Repeated validation failures in ${phase}`,
          area: 'validation',
          severity: SkillGapSeverity.IMPORTANT,
          evidence: [{
            type: 'VALIDATION_FAILURE',
            sourceId: attribution.id,
            description: `Failed ${phase} validation multiple times`,
            timestamp: new Date()
          }],
          addressed: false,
          generatedTaskIds: [],
          identifiedAt: new Date()
        };
        gaps.push(gap);
      }
    }

    return gaps;
  }

  private createSkillGapFromLowConfidence(attribution: Attribution): SkillGap | null {
    if (attribution.confidence >= this.config.minConfidenceForSkillGap) {
      return null;
    }

    return {
      id: uuidv4(),
      agentId: attribution.agentId,
      agentName: attribution.agentName,
      description: `Low confidence in task execution (${(attribution.confidence * 100).toFixed(1)}%)`,
      area: 'general',
      severity: SkillGapSeverity.MINOR,
      evidence: [{
        type: 'LOW_CONFIDENCE',
        sourceId: attribution.id,
        description: `Confidence score: ${attribution.confidence}`,
        timestamp: new Date()
      }],
      addressed: false,
      generatedTaskIds: [],
      identifiedAt: new Date()
    };
  }

  private categorizeFactorToArea(factor: CausalFactor): string {
    const factorLower = factor.factor.toLowerCase();

    if (factorLower.includes('architecture') || factorLower.includes('design')) {
      return 'architecture';
    }
    if (factorLower.includes('test') || factorLower.includes('coverage')) {
      return 'testing';
    }
    if (factorLower.includes('security') || factorLower.includes('vulnerability')) {
      return 'security';
    }
    if (factorLower.includes('performance') || factorLower.includes('optimization')) {
      return 'performance';
    }
    if (factorLower.includes('documentation') || factorLower.includes('docs')) {
      return 'documentation';
    }
    if (factorLower.includes('estimation') || factorLower.includes('planning')) {
      return 'estimation';
    }

    return 'general';
  }

  private calculateSeverity(impact: number): SkillGapSeverity {
    if (impact <= -0.7) return SkillGapSeverity.CRITICAL;
    if (impact <= -0.4) return SkillGapSeverity.IMPORTANT;
    return SkillGapSeverity.MINOR;
  }

  private prioritizeSkillGaps(gaps: SkillGap[]): SkillGap[] {
    const severityOrder: Record<SkillGapSeverity, number> = {
      [SkillGapSeverity.CRITICAL]: 0,
      [SkillGapSeverity.IMPORTANT]: 1,
      [SkillGapSeverity.MINOR]: 2
    };

    return [...gaps].sort((a, b) => {
      // First by severity
      const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
      if (severityDiff !== 0) return severityDiff;

      // Then by evidence count (more evidence = higher priority)
      return b.evidence.length - a.evidence.length;
    });
  }

  // ---------------------------------------------------------------------------
  // Task Creation
  // ---------------------------------------------------------------------------

  private selectTaskTypeForGap(
    gap: SkillGap,
    strategy: GenerationStrategy
  ): GeneratedTaskType {
    const weights = strategy.typeWeights;

    // For critical gaps, prefer failure retry
    if (gap.severity === SkillGapSeverity.CRITICAL) {
      return GeneratedTaskType.FAILURE_RETRY;
    }

    // Check evidence type
    const hasValidationFailure = gap.evidence.some(e => e.type === 'VALIDATION_FAILURE');
    if (hasValidationFailure) {
      return GeneratedTaskType.VALIDATION_TEST;
    }

    // Weighted random selection based on strategy
    const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);
    let random = Math.random() * totalWeight;

    for (const [type, weight] of Object.entries(weights)) {
      random -= weight;
      if (random <= 0) {
        return type as GeneratedTaskType;
      }
    }

    return GeneratedTaskType.PATTERN_PRACTICE;
  }

  private createTaskFromSkillGap(
    agentId: string,
    gap: SkillGap,
    taskType: GeneratedTaskType,
    strategy: GenerationStrategy
  ): TrainingTask {
    const scenario = this.createScenarioForGap(gap, taskType);
    const expectedOutcome = this.createExpectedOutcome(gap, taskType);

    const task: TrainingTask = {
      id: uuidv4(),
      agentId,
      agentName: gap.agentName,
      taskType,
      scenario,
      expectedOutcome,
      difficulty: strategy.difficultyPreference,
      source: TaskSource.ATTRIBUTION,
      status: TaskStatus.PENDING,
      skillGapId: gap.id,
      priority: this.calculateTaskPriority(gap, taskType),
      estimatedDuration: this.estimateTaskDuration(taskType, strategy.difficultyPreference),
      createdAt: new Date(),
      executionAttempts: 0,
      maxAttempts: 3
    };

    // Link task to skill gap
    gap.generatedTaskIds.push(task.id);

    return task;
  }

  private createScenarioForGap(gap: SkillGap, taskType: GeneratedTaskType): TaskScenario {
    const baseScenario: TaskScenario = {
      description: '',
      context: { skillGap: gap.description, area: gap.area },
      constraints: [],
      successCriteria: [],
      relatedPatterns: [],
      focusAreas: [gap.area]
    };

    switch (taskType) {
      case GeneratedTaskType.FAILURE_RETRY:
        baseScenario.description = `Retry the task that led to: ${gap.description}`;
        baseScenario.successCriteria = [
          'Task completes successfully',
          'No validation failures',
          'Confidence score > 0.7'
        ];
        break;

      case GeneratedTaskType.EDGE_CASE_TEST:
        baseScenario.description = `Test edge cases related to: ${gap.area}`;
        baseScenario.constraints = ['Handle null inputs', 'Handle empty collections', 'Handle boundary values'];
        baseScenario.successCriteria = ['All edge cases handled', 'No runtime errors'];
        break;

      case GeneratedTaskType.SKILL_EXPANSION:
        baseScenario.description = `Expand skills in area: ${gap.area}`;
        baseScenario.successCriteria = ['New pattern learned', 'Successfully applied to test case'];
        break;

      case GeneratedTaskType.VALIDATION_TEST:
        baseScenario.description = `Practice validation in: ${gap.area}`;
        baseScenario.successCriteria = ['All validation phases pass', 'No iteration required'];
        break;

      case GeneratedTaskType.PATTERN_PRACTICE:
        baseScenario.description = `Practice patterns for: ${gap.area}`;
        baseScenario.relatedPatterns = this.suggestPatternsForArea(gap.area);
        baseScenario.successCriteria = ['Pattern correctly applied', 'Code quality maintained'];
        break;

      case GeneratedTaskType.EXPLORATION:
        baseScenario.description = `Explore new approaches in: ${gap.area}`;
        baseScenario.successCriteria = ['New insight gained', 'Documented learning'];
        break;
    }

    return baseScenario;
  }

  private createExpectedOutcome(gap: SkillGap, taskType: GeneratedTaskType): ExpectedOutcome {
    return {
      learningObjective: `Address skill gap: ${gap.description}`,
      expectedSuccessRate: taskType === GeneratedTaskType.EXPLORATION ? 0.5 : 0.7,
      targetSkills: [gap.area],
      improvementMetrics: ['confidence_score', 'validation_pass_rate', 'retry_reduction']
    };
  }

  private calculateTaskPriority(gap: SkillGap, taskType: GeneratedTaskType): number {
    let priority = 50;

    // Severity boost
    if (gap.severity === SkillGapSeverity.CRITICAL) priority += 30;
    else if (gap.severity === SkillGapSeverity.IMPORTANT) priority += 15;

    // Task type adjustments
    if (taskType === GeneratedTaskType.FAILURE_RETRY) priority += 10;
    if (taskType === GeneratedTaskType.EXPLORATION) priority -= 10;

    // Evidence count boost
    priority += Math.min(gap.evidence.length * 5, 20);

    return Math.min(100, Math.max(0, priority));
  }

  private estimateTaskDuration(
    taskType: GeneratedTaskType,
    difficulty: TaskDifficulty
  ): number {
    const baseDurations: Record<GeneratedTaskType, number> = {
      [GeneratedTaskType.FAILURE_RETRY]: 600000,     // 10 min
      [GeneratedTaskType.EDGE_CASE_TEST]: 300000,    // 5 min
      [GeneratedTaskType.SKILL_EXPANSION]: 900000,   // 15 min
      [GeneratedTaskType.VALIDATION_TEST]: 300000,   // 5 min
      [GeneratedTaskType.PATTERN_PRACTICE]: 450000,  // 7.5 min
      [GeneratedTaskType.EXPLORATION]: 600000        // 10 min
    };

    const difficultyMultipliers: Record<TaskDifficulty, number> = {
      [TaskDifficulty.EASY]: 0.7,
      [TaskDifficulty.MEDIUM]: 1.0,
      [TaskDifficulty.HARD]: 1.5
    };

    return Math.round(baseDurations[taskType] * difficultyMultipliers[difficulty]);
  }

  private suggestPatternsForArea(area: string): string[] {
    const patternSuggestions: Record<string, string[]> = {
      architecture: ['microservices', 'event-driven', 'clean-architecture'],
      testing: ['unit-testing', 'integration-testing', 'tdd'],
      security: ['input-validation', 'authentication', 'authorization'],
      performance: ['caching', 'lazy-loading', 'query-optimization'],
      documentation: ['api-docs', 'readme', 'inline-comments'],
      estimation: ['story-points', 'function-points', 'complexity-analysis'],
      general: ['solid-principles', 'dry', 'kiss']
    };

    return patternSuggestions[area] || patternSuggestions.general;
  }

  private createExplorationTask(
    agentId: string,
    strategy: GenerationStrategy
  ): TrainingTask | null {
    if (!this.config.enableExploration) return null;

    const agentName = this.getAgentName(agentId);
    const unexploredArea = this.findUnexploredArea(agentId, strategy.focusAreas);

    if (!unexploredArea) return null;

    return {
      id: uuidv4(),
      agentId,
      agentName,
      taskType: GeneratedTaskType.EXPLORATION,
      scenario: {
        description: `Explore new territory: ${unexploredArea}`,
        context: { area: unexploredArea },
        constraints: [],
        successCriteria: ['New insight documented', 'Potential patterns identified'],
        focusAreas: [unexploredArea]
      },
      expectedOutcome: {
        learningObjective: `Expand knowledge in ${unexploredArea}`,
        expectedSuccessRate: 0.5,
        targetSkills: [unexploredArea],
        improvementMetrics: ['patterns_discovered']
      },
      difficulty: TaskDifficulty.MEDIUM,
      source: TaskSource.EXPLORATION,
      status: TaskStatus.PENDING,
      priority: 30,
      estimatedDuration: 600000,
      createdAt: new Date(),
      executionAttempts: 0,
      maxAttempts: 2
    };
  }

  private findUnexploredArea(agentId: string, focusAreas: string[]): string | null {
    const exploredAreas = new Set(
      this.getSkillGapsForAgent(agentId).map(g => g.area)
    );

    for (const area of focusAreas) {
      if (!exploredAreas.has(area)) {
        return area;
      }
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // Task Execution
  // ---------------------------------------------------------------------------

  /**
   * Record the result of executing a training task.
   */
  recordTaskResult(result: TrainingTaskResult): void {
    const results = this.resultStore.get(result.agentId) || [];
    results.push(result);
    this.resultStore.set(result.agentId, results);

    // Update task status
    const tasks = this.taskStore.get(result.agentId) || [];
    const task = tasks.find(t => t.id === result.taskId);
    if (task) {
      task.status = result.success ? TaskStatus.COMPLETED : TaskStatus.FAILED;
      task.completedAt = result.completedAt;
      task.executionAttempts++;
    }

    // Mark skill gap as addressed if task was successful
    if (result.success && task?.skillGapId) {
      this.markSkillGapAddressed(result.agentId, task.skillGapId);
    }
  }

  // ---------------------------------------------------------------------------
  // Metrics
  // ---------------------------------------------------------------------------

  /**
   * Calculate improvement metrics for an agent.
   */
  calculateImprovementMetrics(
    agentId: string,
    periodStart: Date,
    periodEnd: Date
  ): ImprovementMetrics {
    const tasks = this.getTasksForAgent(agentId)
      .filter(t => t.createdAt >= periodStart && t.createdAt <= periodEnd);

    const results = this.getResultsForAgent(agentId)
      .filter(r => r.completedAt >= periodStart && r.completedAt <= periodEnd);

    const gaps = this.getSkillGapsForAgent(agentId)
      .filter(g => g.identifiedAt >= periodStart && g.identifiedAt <= periodEnd);

    const completedTasks = tasks.filter(t => t.status === TaskStatus.COMPLETED);
    const successfulResults = results.filter(r => r.success);

    return {
      agentId,
      period: { start: periodStart, end: periodEnd },
      tasksGenerated: tasks.length,
      tasksCompleted: completedTasks.length,
      tasksSuccessful: successfulResults.length,
      tasksFailed: results.length - successfulResults.length,
      skillGapsIdentified: gaps.length,
      skillGapsAddressed: gaps.filter(g => g.addressed).length,
      lessonsLearned: results.reduce((sum, r) => sum + r.lessons.length, 0),
      patternsDiscovered: 0, // Would need pattern tracking
      successRateChange: this.calculateSuccessRateChange(agentId, periodStart),
      confidenceChange: this.calculateConfidenceChange(results),
      estimationAccuracyChange: 0, // Would need estimation tracking
      trend: this.determineTrend(successfulResults.length, results.length)
    };
  }

  private calculateSuccessRateChange(agentId: string, since: Date): number {
    const results = this.getResultsForAgent(agentId);
    const recentResults = results.filter(r => r.completedAt >= since);
    const olderResults = results.filter(r => r.completedAt < since);

    if (olderResults.length === 0 || recentResults.length === 0) return 0;

    const recentRate = recentResults.filter(r => r.success).length / recentResults.length;
    const olderRate = olderResults.filter(r => r.success).length / olderResults.length;

    return recentRate - olderRate;
  }

  private calculateConfidenceChange(results: TrainingTaskResult[]): number {
    if (results.length < 2) return 0;

    const firstHalf = results.slice(0, Math.floor(results.length / 2));
    const secondHalf = results.slice(Math.floor(results.length / 2));

    const firstAvg = firstHalf.reduce((sum, r) => sum + r.metrics.confidenceScore, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, r) => sum + r.metrics.confidenceScore, 0) / secondHalf.length;

    return secondAvg - firstAvg;
  }

  private determineTrend(
    successful: number,
    total: number
  ): 'IMPROVING' | 'STABLE' | 'DECLINING' {
    if (total === 0) return 'STABLE';
    const rate = successful / total;
    if (rate > 0.7) return 'IMPROVING';
    if (rate < 0.4) return 'DECLINING';
    return 'STABLE';
  }

  // ---------------------------------------------------------------------------
  // Storage Helpers
  // ---------------------------------------------------------------------------

  private getDefaultStrategy(agentId: string): GenerationStrategy {
    return {
      agentId,
      focusAreas: ['general'],
      difficultyPreference: TaskDifficulty.MEDIUM,
      maxTasksPerSession: 5,
      cooldownPeriod: this.config.defaultCooldownMs,
      typeWeights: {
        [GeneratedTaskType.FAILURE_RETRY]: 0.25,
        [GeneratedTaskType.EDGE_CASE_TEST]: 0.2,
        [GeneratedTaskType.SKILL_EXPANSION]: 0.15,
        [GeneratedTaskType.VALIDATION_TEST]: 0.15,
        [GeneratedTaskType.PATTERN_PRACTICE]: 0.15,
        [GeneratedTaskType.EXPLORATION]: 0.1
      }
    };
  }

  private getAgentName(agentId: string): string {
    const names: Record<string, string> = {
      felix_001: 'Felix',
      marcus_001: 'Marcus',
      quinn_001: 'Quinn',
      betty_001: 'Betty',
      eliza_001: 'Eliza',
      tessa_001: 'Tessa',
      miguel_001: 'Miguel',
      diana_001: 'Diana',
      peter_001: 'Peter',
      paul_001: 'Paul'
    };
    return names[agentId] || 'Unknown';
  }

  private storeSkillGap(agentId: string, gap: SkillGap): void {
    const gaps = this.skillGapStore.get(agentId) || [];
    gaps.push(gap);
    this.skillGapStore.set(agentId, gaps);
  }

  private storeTasksForAgent(agentId: string, tasks: TrainingTask[]): void {
    const existing = this.taskStore.get(agentId) || [];
    this.taskStore.set(agentId, [...existing, ...tasks]);
  }

  private markSkillGapAddressed(agentId: string, gapId: string): void {
    const gaps = this.skillGapStore.get(agentId) || [];
    const gap = gaps.find(g => g.id === gapId);
    if (gap) {
      gap.addressed = true;
      gap.addressedAt = new Date();
    }
  }

  // ---------------------------------------------------------------------------
  // Public Getters
  // ---------------------------------------------------------------------------

  getSkillGapsForAgent(agentId: string): SkillGap[] {
    return this.skillGapStore.get(agentId) || [];
  }

  getTasksForAgent(agentId: string): TrainingTask[] {
    return this.taskStore.get(agentId) || [];
  }

  getResultsForAgent(agentId: string): TrainingTaskResult[] {
    return this.resultStore.get(agentId) || [];
  }

  getPendingTasks(agentId: string): TrainingTask[] {
    return this.getTasksForAgent(agentId).filter(t => t.status === TaskStatus.PENDING);
  }
}

// =============================================================================
// Singleton Export
// =============================================================================

export const taskGenerator = new TaskGeneratorService();
