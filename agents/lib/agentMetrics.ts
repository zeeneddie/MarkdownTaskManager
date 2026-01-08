/**
 * Agent Performance Metrics System
 *
 * Tracks agent performance across all dimensions:
 * - Execution time & throughput
 * - Success/failure rates
 * - Validation iteration counts
 * - Experience consultation effectiveness
 * - Pattern usage & success rates
 *
 * Part of AgentEvolver Phase B (Week 20).
 *
 * @author Claude Code (Week 20 Day 4)
 * @date 2025-11-22
 */

import axios from 'axios';

// ============================================================================
// Types
// ============================================================================

export interface AgentMetric {
  agentId: string;
  timestamp: string;
  metricType: MetricType;
  value: number;
  context?: Record<string, any>;
}

export type MetricType =
  | 'execution_time'       // Task execution duration (seconds)
  | 'success_rate'         // Success percentage (0-100)
  | 'failure_count'        // Number of failures
  | 'validation_iterations' // Iterations needed to validate
  | 'experience_used'      // Whether experience was consulted (0/1)
  | 'pattern_applied'      // Number of patterns applied
  | 'confidence_score'     // Agent confidence (0-1)
  | 'quality_score'        // Output quality (0-100)
  | 'code_coverage'        // Test coverage percentage
  | 'throughput';          // Tasks completed per hour

export interface AgentPerformance {
  agentId: string;
  agentRole: string;
  period: string;  // 'hour', 'day', 'week', 'month'
  metrics: {
    totalTasks: number;
    successfulTasks: number;
    failedTasks: number;
    avgExecutionTime: number;
    avgValidationIterations: number;
    experienceUsageRate: number;
    patternsApplied: number;
    avgConfidence: number;
    avgQualityScore: number;
    successRate: number;
    throughput: number;
  };
  trends: {
    executionTimeTrend: 'improving' | 'stable' | 'declining';
    successRateTrend: 'improving' | 'stable' | 'declining';
    qualityTrend: 'improving' | 'stable' | 'declining';
  };
  topPatterns: Array<{
    patternId: string;
    usageCount: number;
    successRate: number;
  }>;
  commonFailures: Array<{
    failureType: string;
    count: number;
    lastOccurrence: string;
  }>;
}

export interface WorkflowMetrics {
  workType: string;
  period: string;
  metrics: {
    totalExecutions: number;
    successfulExecutions: number;
    avgDuration: number;
    agentParticipation: Record<string, number>;
    validationPassRate: number;
    avgIterationsToSuccess: number;
  };
}

export interface DashboardSummary {
  generatedAt: string;
  period: string;
  overallMetrics: {
    totalTasks: number;
    overallSuccessRate: number;
    avgExecutionTime: number;
    experienceConsultationRate: number;
    validationFirstPassRate: number;
  };
  agentPerformance: AgentPerformance[];
  workflowMetrics: WorkflowMetrics[];
  systemHealth: {
    activeAgents: number;
    avgAgentSuccessRate: number;
    topPerformer: string;
    needsAttention: string[];
  };
}

// ============================================================================
// Metrics Collector
// ============================================================================

export class MetricsCollector {
  private metrics: AgentMetric[] = [];
  private maxMetrics: number = 10000;

  /**
   * Record a metric
   */
  record(
    agentId: string,
    metricType: MetricType,
    value: number,
    context?: Record<string, any>
  ): void {
    const metric: AgentMetric = {
      agentId,
      timestamp: new Date().toISOString(),
      metricType,
      value,
      context
    };

    this.metrics.push(metric);

    // Trim if exceeding max
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }
  }

  /**
   * Record task execution
   */
  recordTaskExecution(
    agentId: string,
    success: boolean,
    executionTime: number,
    validationIterations: number,
    experienceUsed: boolean,
    patternsApplied: number,
    qualityScore: number,
    context?: Record<string, any>
  ): void {
    this.record(agentId, 'execution_time', executionTime, context);
    this.record(agentId, 'success_rate', success ? 100 : 0, context);
    if (!success) {
      this.record(agentId, 'failure_count', 1, context);
    }
    this.record(agentId, 'validation_iterations', validationIterations, context);
    this.record(agentId, 'experience_used', experienceUsed ? 1 : 0, context);
    this.record(agentId, 'pattern_applied', patternsApplied, context);
    this.record(agentId, 'quality_score', qualityScore, context);
  }

  /**
   * Get metrics for an agent within a time period
   */
  getAgentMetrics(
    agentId: string,
    periodHours: number = 24
  ): AgentMetric[] {
    const cutoff = new Date(Date.now() - periodHours * 60 * 60 * 1000);
    return this.metrics.filter(
      m => m.agentId === agentId && new Date(m.timestamp) >= cutoff
    );
  }

  /**
   * Get all metrics within a time period
   */
  getAllMetrics(periodHours: number = 24): AgentMetric[] {
    const cutoff = new Date(Date.now() - periodHours * 60 * 60 * 1000);
    return this.metrics.filter(m => new Date(m.timestamp) >= cutoff);
  }

  /**
   * Get unique agent IDs with recent activity
   */
  getActiveAgents(periodHours: number = 24): string[] {
    const metrics = this.getAllMetrics(periodHours);
    return [...new Set(metrics.map(m => m.agentId))];
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics = [];
  }
}

// ============================================================================
// Performance Calculator
// ============================================================================

export class PerformanceCalculator {
  private collector: MetricsCollector;

  constructor(collector: MetricsCollector) {
    this.collector = collector;
  }

  /**
   * Calculate agent performance metrics
   */
  calculateAgentPerformance(
    agentId: string,
    agentRole: string,
    periodHours: number = 24
  ): AgentPerformance {
    const metrics = this.collector.getAgentMetrics(agentId, periodHours);

    // Calculate aggregates
    const executionTimes = metrics.filter(m => m.metricType === 'execution_time');
    const successRates = metrics.filter(m => m.metricType === 'success_rate');
    const validationIterations = metrics.filter(m => m.metricType === 'validation_iterations');
    const experienceUsed = metrics.filter(m => m.metricType === 'experience_used');
    const patternsApplied = metrics.filter(m => m.metricType === 'pattern_applied');
    const qualityScores = metrics.filter(m => m.metricType === 'quality_score');

    const totalTasks = successRates.length;
    const successfulTasks = successRates.filter(m => m.value === 100).length;
    const failedTasks = totalTasks - successfulTasks;

    const avgExecutionTime = this.average(executionTimes.map(m => m.value));
    const avgValidationIterations = this.average(validationIterations.map(m => m.value));
    const experienceUsageRate = this.average(experienceUsed.map(m => m.value)) * 100;
    const totalPatterns = this.sum(patternsApplied.map(m => m.value));
    const avgQualityScore = this.average(qualityScores.map(m => m.value));

    // Calculate success rate
    const successRate = totalTasks > 0 ? (successfulTasks / totalTasks) * 100 : 0;

    // Calculate throughput (tasks per hour)
    const throughput = totalTasks / (periodHours || 1);

    // Calculate trends (compare first half to second half)
    const executionTimeTrend = this.calculateTrend(executionTimes.map(m => m.value), true);
    const successRateTrend = this.calculateTrend(successRates.map(m => m.value), false);
    const qualityTrend = this.calculateTrend(qualityScores.map(m => m.value), false);

    // Get pattern usage (from context)
    const patternUsage = this.aggregatePatternUsage(metrics);

    // Get common failures (from context)
    const failures = this.aggregateFailures(metrics);

    return {
      agentId,
      agentRole,
      period: `${periodHours}h`,
      metrics: {
        totalTasks,
        successfulTasks,
        failedTasks,
        avgExecutionTime,
        avgValidationIterations,
        experienceUsageRate,
        patternsApplied: totalPatterns,
        avgConfidence: 0.75, // Default; would come from actual measurements
        avgQualityScore,
        successRate,
        throughput
      },
      trends: {
        executionTimeTrend,
        successRateTrend,
        qualityTrend
      },
      topPatterns: patternUsage.slice(0, 5),
      commonFailures: failures.slice(0, 5)
    };
  }

  /**
   * Calculate workflow metrics
   */
  calculateWorkflowMetrics(
    workType: string,
    periodHours: number = 24
  ): WorkflowMetrics {
    const allMetrics = this.collector.getAllMetrics(periodHours);

    // Filter by work type in context
    const workflowMetrics = allMetrics.filter(
      m => m.context?.workType === workType
    );

    const executionTimes = workflowMetrics.filter(m => m.metricType === 'execution_time');
    const successRates = workflowMetrics.filter(m => m.metricType === 'success_rate');
    const validationIterations = workflowMetrics.filter(m => m.metricType === 'validation_iterations');

    const totalExecutions = new Set(workflowMetrics.map(m => m.context?.executionId)).size;
    const successfulExecutions = successRates.filter(m => m.value === 100).length;

    // Aggregate by agent
    const agentParticipation: Record<string, number> = {};
    for (const metric of workflowMetrics) {
      agentParticipation[metric.agentId] = (agentParticipation[metric.agentId] || 0) + 1;
    }

    return {
      workType,
      period: `${periodHours}h`,
      metrics: {
        totalExecutions,
        successfulExecutions,
        avgDuration: this.average(executionTimes.map(m => m.value)),
        agentParticipation,
        validationPassRate: totalExecutions > 0
          ? (successfulExecutions / totalExecutions) * 100
          : 0,
        avgIterationsToSuccess: this.average(validationIterations.map(m => m.value))
      }
    };
  }

  /**
   * Generate dashboard summary
   */
  generateDashboardSummary(periodHours: number = 24): DashboardSummary {
    const activeAgents = this.collector.getActiveAgents(periodHours);
    const allMetrics = this.collector.getAllMetrics(periodHours);

    // Agent roles mapping
    const agentRoles: Record<string, string> = {
      felix: 'architect',
      marcus: 'maintenance',
      quinn: 'quality',
      betty: 'debugging',
      eliza: 'estimation',
      tessa: 'testing',
      miguel: 'migration',
      diana: 'documentation',
      peter: 'product',
      paul: 'management'
    };

    // Calculate per-agent performance
    const agentPerformance = activeAgents.map(agentId =>
      this.calculateAgentPerformance(
        agentId,
        agentRoles[agentId.toLowerCase()] || 'general',
        periodHours
      )
    );

    // Work types to analyze
    const workTypes = [
      'NEW_FEATURE', 'MAINTENANCE', 'BUG', 'QUALITY_AUDIT',
      'ENHANCEMENT', 'MIGRATION', 'QUALITY_IMPROVEMENT', 'TESTING', 'PROJECT_DEFINITION'
    ];

    // Calculate per-workflow metrics
    const workflowMetrics = workTypes.map(wt =>
      this.calculateWorkflowMetrics(wt, periodHours)
    ).filter(wm => wm.metrics.totalExecutions > 0);

    // Overall metrics
    const successRates = allMetrics.filter(m => m.metricType === 'success_rate');
    const executionTimes = allMetrics.filter(m => m.metricType === 'execution_time');
    const experienceUsed = allMetrics.filter(m => m.metricType === 'experience_used');
    const validationIterations = allMetrics.filter(m => m.metricType === 'validation_iterations');

    const totalTasks = successRates.length;
    const overallSuccessRate = this.average(successRates.map(m => m.value));
    const avgExecutionTime = this.average(executionTimes.map(m => m.value));
    const experienceConsultationRate = this.average(experienceUsed.map(m => m.value)) * 100;
    const validationFirstPassRate = validationIterations.length > 0
      ? (validationIterations.filter(m => m.value === 1).length / validationIterations.length) * 100
      : 0;

    // Find top performer and agents needing attention
    const sortedBySuccess = [...agentPerformance].sort(
      (a, b) => b.metrics.successRate - a.metrics.successRate
    );
    const topPerformer = sortedBySuccess[0]?.agentId || 'N/A';
    const needsAttention = sortedBySuccess
      .filter(ap => ap.metrics.successRate < 70)
      .map(ap => ap.agentId);

    const avgAgentSuccessRate = this.average(
      agentPerformance.map(ap => ap.metrics.successRate)
    );

    return {
      generatedAt: new Date().toISOString(),
      period: `${periodHours}h`,
      overallMetrics: {
        totalTasks,
        overallSuccessRate,
        avgExecutionTime,
        experienceConsultationRate,
        validationFirstPassRate
      },
      agentPerformance,
      workflowMetrics,
      systemHealth: {
        activeAgents: activeAgents.length,
        avgAgentSuccessRate,
        topPerformer,
        needsAttention
      }
    };
  }

  // ============================================================================
  // Helper Methods
  // ============================================================================

  private average(values: number[]): number {
    if (values.length === 0) return 0;
    return values.reduce((a, b) => a + b, 0) / values.length;
  }

  private sum(values: number[]): number {
    return values.reduce((a, b) => a + b, 0);
  }

  private calculateTrend(
    values: number[],
    lowerIsBetter: boolean
  ): 'improving' | 'stable' | 'declining' {
    if (values.length < 4) return 'stable';

    const mid = Math.floor(values.length / 2);
    const firstHalf = values.slice(0, mid);
    const secondHalf = values.slice(mid);

    const firstAvg = this.average(firstHalf);
    const secondAvg = this.average(secondHalf);

    const change = ((secondAvg - firstAvg) / (firstAvg || 1)) * 100;

    if (Math.abs(change) < 5) return 'stable';

    if (lowerIsBetter) {
      return change < 0 ? 'improving' : 'declining';
    } else {
      return change > 0 ? 'improving' : 'declining';
    }
  }

  private aggregatePatternUsage(
    metrics: AgentMetric[]
  ): Array<{ patternId: string; usageCount: number; successRate: number }> {
    const patternStats: Record<string, { uses: number; successes: number }> = {};

    for (const metric of metrics) {
      if (metric.context?.patternId) {
        const id = metric.context.patternId;
        if (!patternStats[id]) {
          patternStats[id] = { uses: 0, successes: 0 };
        }
        patternStats[id].uses++;
        if (metric.metricType === 'success_rate' && metric.value === 100) {
          patternStats[id].successes++;
        }
      }
    }

    return Object.entries(patternStats)
      .map(([patternId, stats]) => ({
        patternId,
        usageCount: stats.uses,
        successRate: stats.uses > 0 ? (stats.successes / stats.uses) * 100 : 0
      }))
      .sort((a, b) => b.usageCount - a.usageCount);
  }

  private aggregateFailures(
    metrics: AgentMetric[]
  ): Array<{ failureType: string; count: number; lastOccurrence: string }> {
    const failureStats: Record<string, { count: number; lastOccurrence: string }> = {};

    const failures = metrics.filter(
      m => m.metricType === 'success_rate' && m.value === 0
    );

    for (const failure of failures) {
      const type = failure.context?.failureType || 'unknown';
      if (!failureStats[type]) {
        failureStats[type] = { count: 0, lastOccurrence: failure.timestamp };
      }
      failureStats[type].count++;
      if (failure.timestamp > failureStats[type].lastOccurrence) {
        failureStats[type].lastOccurrence = failure.timestamp;
      }
    }

    return Object.entries(failureStats)
      .map(([failureType, stats]) => ({
        failureType,
        count: stats.count,
        lastOccurrence: stats.lastOccurrence
      }))
      .sort((a, b) => b.count - a.count);
  }
}

// ============================================================================
// Metrics API Client
// ============================================================================

export class MetricsApiClient {
  private apiBaseUrl: string;

  constructor(apiBaseUrl: string = 'http://localhost:8000') {
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Submit metrics to backend API
   */
  async submitMetrics(metrics: AgentMetric[]): Promise<void> {
    try {
      await axios.post(`${this.apiBaseUrl}/api/metrics/batch`, {
        metrics: metrics.map(m => ({
          agent_id: m.agentId,
          timestamp: m.timestamp,
          metric_type: m.metricType,
          value: m.value,
          context: m.context
        }))
      });
    } catch (error) {
      console.error('[Metrics] Failed to submit metrics:', error);
    }
  }

  /**
   * Fetch dashboard summary from API
   */
  async fetchDashboard(periodHours: number = 24): Promise<DashboardSummary | null> {
    try {
      const response = await axios.get(
        `${this.apiBaseUrl}/api/metrics/dashboard`,
        { params: { period_hours: periodHours } }
      );
      return response.data;
    } catch (error) {
      console.error('[Metrics] Failed to fetch dashboard:', error);
      return null;
    }
  }

  /**
   * Fetch agent performance from API
   */
  async fetchAgentPerformance(
    agentId: string,
    periodHours: number = 24
  ): Promise<AgentPerformance | null> {
    try {
      const response = await axios.get(
        `${this.apiBaseUrl}/api/metrics/agents/${agentId}`,
        { params: { period_hours: periodHours } }
      );
      return response.data;
    } catch (error) {
      console.error('[Metrics] Failed to fetch agent performance:', error);
      return null;
    }
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

let collectorInstance: MetricsCollector | null = null;
let calculatorInstance: PerformanceCalculator | null = null;

export function getMetricsCollector(): MetricsCollector {
  if (!collectorInstance) {
    collectorInstance = new MetricsCollector();
  }
  return collectorInstance;
}

export function getPerformanceCalculator(): PerformanceCalculator {
  if (!calculatorInstance) {
    calculatorInstance = new PerformanceCalculator(getMetricsCollector());
  }
  return calculatorInstance;
}

// ============================================================================
// Integration Helper
// ============================================================================

/**
 * Record execution metrics from a workflow result
 */
export function recordWorkflowExecution(
  workType: string,
  executionId: string,
  agentResults: Record<string, any>,
  totalDuration: number,
  validationResult?: any
): void {
  const collector = getMetricsCollector();

  for (const [agentId, result] of Object.entries(agentResults)) {
    const context = {
      workType,
      executionId,
      ...result.context
    };

    collector.recordTaskExecution(
      agentId,
      result.success,
      result.executionTime || 0,
      validationResult?.iterations || 1,
      result.guidance !== undefined,
      result.keyDecisions?.length || 0,
      result.qualityScore || 70,
      context
    );
  }
}

// ============================================================================
// Exports
// ============================================================================

export default {
  MetricsCollector,
  PerformanceCalculator,
  MetricsApiClient,
  getMetricsCollector,
  getPerformanceCalculator,
  recordWorkflowExecution
};
