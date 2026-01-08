/**
 * Experience Consultant - Self-Navigating Core
 *
 * Enables agents to consult past experiences before making decisions.
 * Part of AgentEvolver Phase B (Week 19).
 *
 * Features:
 * - Similarity search across experiences
 * - Pattern matching and ranking
 * - Guidance generation from past successes/failures
 * - "Before I start, let me check..." logging
 *
 * @author Claude Code (Week 19 Day 1)
 * @date 2025-11-22
 */

import axios from 'axios';

// ============================================================================
// Types
// ============================================================================

export interface TaskContext {
  taskId: string;
  agentId: string;
  agentRole: string;
  workType: string;
  description: string;
  complexity?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface Experience {
  id: string;
  agentId: string;
  agentRole: string;
  workType: string;
  taskDescription: string;
  approach: string;
  outcome: 'SUCCESS' | 'PARTIAL' | 'FAILURE';
  qualityScore: number;
  keyDecisions: KeyDecision[];
  lessonsLearned: string[];
  duration?: number;
  createdAt: string;
  similarity?: number;  // Added during search
}

export interface KeyDecision {
  decision: string;
  reasoning: string;
  alternatives: string[];
  outcome: string;
  impactScore: number;
}

export interface SuccessfulPattern {
  id: string;
  name: string;
  description: string;
  workTypes: string[];
  applicableContexts: string[];
  steps: string[];
  successRate: number;
  usageCount: number;
  lastUsed: string;
  similarity?: number;
}

export interface FailureAnalysis {
  id: string;
  agentId: string;
  workType: string;
  failureType: string;
  description: string;
  rootCause: string;
  contributingFactors: string[];
  preventionStrategies: string[];
  similarFailures: string[];
  similarity?: number;
}

export interface Guidance {
  relevantExperiences: Experience[];
  applicablePatterns: SuccessfulPattern[];
  warningsFromFailures: FailureAnalysis[];
  recommendations: string[];
  confidenceScore: number;
  consultationLog: string;
}

export interface ConsultationOptions {
  maxExperiences?: number;
  maxPatterns?: number;
  maxFailures?: number;
  minSimilarity?: number;
  includeOtherAgents?: boolean;
}

// ============================================================================
// Experience Consultant Class
// ============================================================================

export class ExperienceConsultant {
  private apiBaseUrl: string;
  private consultationLogs: string[] = [];

  constructor(apiBaseUrl: string = 'http://localhost:8000') {
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Main entry point: Consult experience before starting a task
   *
   * "Before I start, let me check what I've learned from similar tasks..."
   */
  async consultBeforeTask(
    context: TaskContext,
    options: ConsultationOptions = {}
  ): Promise<Guidance> {
    const {
      maxExperiences = 5,
      maxPatterns = 3,
      maxFailures = 3,
      minSimilarity = 0.6,
      includeOtherAgents = true
    } = options;

    this.log(`[${context.agentId}] Before I start "${context.description}", let me check my experience...`);

    // Parallel fetch for speed
    const [experiences, patterns, failures] = await Promise.all([
      this.findSimilarExperiences(context, maxExperiences, minSimilarity, includeOtherAgents),
      this.findApplicablePatterns(context, maxPatterns, minSimilarity),
      this.findRelevantFailures(context, maxFailures, minSimilarity)
    ]);

    // Generate recommendations based on findings
    const recommendations = this.generateRecommendations(
      context,
      experiences,
      patterns,
      failures
    );

    // Calculate confidence based on amount and quality of data
    const confidenceScore = this.calculateConfidence(
      experiences,
      patterns,
      failures
    );

    const guidance: Guidance = {
      relevantExperiences: experiences,
      applicablePatterns: patterns,
      warningsFromFailures: failures,
      recommendations,
      confidenceScore,
      consultationLog: this.consultationLogs.join('\n')
    };

    this.log(`[${context.agentId}] Consultation complete. Confidence: ${(confidenceScore * 100).toFixed(0)}%`);
    this.log(`[${context.agentId}] Found ${experiences.length} experiences, ${patterns.length} patterns, ${failures.length} warnings`);

    return guidance;
  }

  /**
   * Find similar experiences from the experience store
   */
  async findSimilarExperiences(
    context: TaskContext,
    limit: number = 5,
    minSimilarity: number = 0.6,
    includeOtherAgents: boolean = true
  ): Promise<Experience[]> {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/api/evolution/experiences/search`, {
        query: context.description,
        work_type: context.workType,
        agent_role: includeOtherAgents ? undefined : context.agentRole,
        limit,
        min_similarity: minSimilarity
      });

      const experiences = response.data.experiences || [];

      this.log(`  - Found ${experiences.length} similar experiences`);

      for (const exp of experiences.slice(0, 3)) {
        this.log(`    * "${exp.task_description?.substring(0, 50)}..." (similarity: ${(exp.similarity * 100).toFixed(0)}%)`);
      }

      return experiences.map(this.mapExperience);
    } catch (error) {
      this.log(`  - Error fetching experiences: ${error}`);
      return [];
    }
  }

  /**
   * Find patterns that have worked well for similar tasks
   */
  async findApplicablePatterns(
    context: TaskContext,
    limit: number = 3,
    minSimilarity: number = 0.6
  ): Promise<SuccessfulPattern[]> {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/api/evolution/patterns/search`, {
        query: context.description,
        work_type: context.workType,
        limit,
        min_similarity: minSimilarity
      });

      const patterns = response.data.patterns || [];

      this.log(`  - Found ${patterns.length} applicable patterns`);

      for (const pattern of patterns.slice(0, 2)) {
        this.log(`    * "${pattern.name}" (success rate: ${(pattern.success_rate * 100).toFixed(0)}%)`);
      }

      return patterns.map(this.mapPattern);
    } catch (error) {
      this.log(`  - Error fetching patterns: ${error}`);
      return [];
    }
  }

  /**
   * Find relevant failure analyses to avoid past mistakes
   */
  async findRelevantFailures(
    context: TaskContext,
    limit: number = 3,
    minSimilarity: number = 0.6
  ): Promise<FailureAnalysis[]> {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/api/evolution/failures/search`, {
        query: context.description,
        work_type: context.workType,
        limit,
        min_similarity: minSimilarity
      });

      const failures = response.data.failures || [];

      if (failures.length > 0) {
        this.log(`  - Found ${failures.length} relevant failure warnings`);
        for (const failure of failures.slice(0, 2)) {
          this.log(`    ! "${failure.failure_type}": ${failure.description?.substring(0, 40)}...`);
        }
      }

      return failures.map(this.mapFailure);
    } catch (error) {
      this.log(`  - Error fetching failures: ${error}`);
      return [];
    }
  }

  /**
   * Generate actionable recommendations from consultation data
   */
  private generateRecommendations(
    context: TaskContext,
    experiences: Experience[],
    patterns: SuccessfulPattern[],
    failures: FailureAnalysis[]
  ): string[] {
    const recommendations: string[] = [];

    // Recommendations from successful experiences
    const successfulExps = experiences.filter(e => e.outcome === 'SUCCESS' && e.qualityScore >= 80);
    if (successfulExps.length > 0) {
      const topExp = successfulExps[0];
      recommendations.push(
        `Consider approach from similar successful task: "${topExp.approach?.substring(0, 100)}..."`
      );

      // Add key decisions that had high impact
      const impactfulDecisions = topExp.keyDecisions?.filter(d => d.impactScore >= 0.7) || [];
      for (const decision of impactfulDecisions.slice(0, 2)) {
        recommendations.push(`Key decision that worked: ${decision.decision}`);
      }
    }

    // Recommendations from patterns
    for (const pattern of patterns.slice(0, 2)) {
      if (pattern.successRate >= 0.8) {
        recommendations.push(
          `Apply "${pattern.name}" pattern (${(pattern.successRate * 100).toFixed(0)}% success rate)`
        );
      }
    }

    // Warnings from failures
    for (const failure of failures) {
      recommendations.push(
        `AVOID: ${failure.failureType} - ${failure.preventionStrategies?.[0] || 'No prevention strategy recorded'}`
      );
    }

    // Generic recommendations if no data
    if (recommendations.length === 0) {
      recommendations.push('No specific historical guidance available. Proceed with standard approach.');
      recommendations.push('Consider documenting this experience for future reference.');
    }

    return recommendations;
  }

  /**
   * Calculate confidence score based on consultation data quality
   */
  private calculateConfidence(
    experiences: Experience[],
    patterns: SuccessfulPattern[],
    failures: FailureAnalysis[]
  ): number {
    let score = 0.3; // Base confidence

    // More experiences = higher confidence
    if (experiences.length > 0) {
      score += Math.min(0.2, experiences.length * 0.04);

      // High similarity experiences boost confidence
      const avgSimilarity = experiences.reduce((sum, e) => sum + (e.similarity || 0), 0) / experiences.length;
      score += avgSimilarity * 0.15;

      // Successful experiences boost confidence more
      const successRate = experiences.filter(e => e.outcome === 'SUCCESS').length / experiences.length;
      score += successRate * 0.1;
    }

    // Applicable patterns boost confidence
    if (patterns.length > 0) {
      score += Math.min(0.15, patterns.length * 0.05);

      // High success rate patterns boost confidence
      const avgSuccessRate = patterns.reduce((sum, p) => sum + p.successRate, 0) / patterns.length;
      score += avgSuccessRate * 0.1;
    }

    // Failure warnings actually increase confidence (knowing what to avoid)
    if (failures.length > 0) {
      score += Math.min(0.1, failures.length * 0.03);
    }

    return Math.min(1.0, score);
  }

  /**
   * Log a consultation message
   */
  private log(message: string): void {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}`;
    this.consultationLogs.push(logEntry);
    console.log(logEntry);
  }

  /**
   * Clear consultation logs
   */
  clearLogs(): void {
    this.consultationLogs = [];
  }

  /**
   * Get consultation logs
   */
  getLogs(): string[] {
    return [...this.consultationLogs];
  }

  // ========================================================================
  // Mapping Functions (API response to internal types)
  // ========================================================================

  private mapExperience(raw: any): Experience {
    return {
      id: raw.id,
      agentId: raw.agent_id,
      agentRole: raw.agent_role,
      workType: raw.work_type,
      taskDescription: raw.task_description,
      approach: raw.approach,
      outcome: raw.outcome,
      qualityScore: raw.quality_score,
      keyDecisions: (raw.key_decisions || []).map((kd: any) => ({
        decision: kd.decision,
        reasoning: kd.reasoning,
        alternatives: kd.alternatives || [],
        outcome: kd.outcome,
        impactScore: kd.impact_score
      })),
      lessonsLearned: raw.lessons_learned || [],
      duration: raw.duration,
      createdAt: raw.created_at,
      similarity: raw.similarity
    };
  }

  private mapPattern(raw: any): SuccessfulPattern {
    return {
      id: raw.id,
      name: raw.name,
      description: raw.description,
      workTypes: raw.work_types || [],
      applicableContexts: raw.applicable_contexts || [],
      steps: raw.steps || [],
      successRate: raw.success_rate,
      usageCount: raw.usage_count,
      lastUsed: raw.last_used,
      similarity: raw.similarity
    };
  }

  private mapFailure(raw: any): FailureAnalysis {
    return {
      id: raw.id,
      agentId: raw.agent_id,
      workType: raw.work_type,
      failureType: raw.failure_type,
      description: raw.description,
      rootCause: raw.root_cause,
      contributingFactors: raw.contributing_factors || [],
      preventionStrategies: raw.prevention_strategies || [],
      similarFailures: raw.similar_failures || [],
      similarity: raw.similarity
    };
  }
}

// ============================================================================
// Factory & Singleton
// ============================================================================

let consultantInstance: ExperienceConsultant | null = null;

export function getExperienceConsultant(apiBaseUrl?: string): ExperienceConsultant {
  if (!consultantInstance) {
    consultantInstance = new ExperienceConsultant(apiBaseUrl);
  }
  return consultantInstance;
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Quick consultation before starting a task
 */
export async function consultExperience(
  context: TaskContext,
  options?: ConsultationOptions
): Promise<Guidance> {
  const consultant = getExperienceConsultant();
  return consultant.consultBeforeTask(context, options);
}

/**
 * Log outcome after completing a task (for learning)
 */
export async function logTaskOutcome(
  context: TaskContext,
  outcome: 'SUCCESS' | 'PARTIAL' | 'FAILURE',
  approach: string,
  qualityScore: number,
  lessonsLearned: string[],
  keyDecisions: KeyDecision[] = []
): Promise<void> {
  const consultant = getExperienceConsultant();

  try {
    await axios.post(`${consultant['apiBaseUrl']}/api/evolution/experiences`, {
      agent_id: context.agentId,
      agent_role: context.agentRole,
      work_type: context.workType,
      task_id: context.taskId,
      task_description: context.description,
      approach,
      outcome,
      quality_score: qualityScore,
      lessons_learned: lessonsLearned,
      key_decisions: keyDecisions.map(kd => ({
        decision: kd.decision,
        reasoning: kd.reasoning,
        alternatives: kd.alternatives,
        outcome: kd.outcome,
        impact_score: kd.impactScore
      }))
    });

    console.log(`[ExperienceConsultant] Logged ${outcome} outcome for task ${context.taskId}`);
  } catch (error) {
    console.error(`[ExperienceConsultant] Failed to log outcome: ${error}`);
  }
}

export default ExperienceConsultant;
