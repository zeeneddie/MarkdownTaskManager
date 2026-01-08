/**
 * Experience Integration - Self-Navigating Agent Wrapper
 *
 * Wraps agent execution with experience consultation.
 * Part of AgentEvolver Phase B (Week 19).
 *
 * Features:
 * - "Before I start, let me check..." consultation
 * - Pattern guidance injection into agent prompts
 * - Outcome logging for learning
 * - Success/failure tracking
 *
 * @author Claude Code (Week 19 Day 3)
 * @date 2025-11-22
 */

import { Agent } from 'kaibanjs';
import {
  ExperienceConsultant,
  getExperienceConsultant,
  TaskContext,
  Guidance,
  ConsultationOptions,
  KeyDecision,
  logTaskOutcome
} from '../lib/experienceConsultant';

// Minimal Task interface for flexibility (KaibanJS Task has many required fields)
export interface Task {
  description: string;
  expectedOutput: string;
  [key: string]: any;  // Allow additional properties
}

// ============================================================================
// Types
// ============================================================================

export interface EvolvingAgentConfig {
  agent: Agent;
  agentId: string;
  agentRole: string;
  enableExperienceConsultation: boolean;
  enableOutcomeLogging: boolean;
  consultationOptions?: ConsultationOptions;
}

export interface EnhancedTask extends Task {
  taskId: string;
  workType: string;
  originalDescription: string;
  guidance?: Guidance;
  enhancedDescription?: string;
}

export interface ExecutionResult {
  success: boolean;
  output: any;
  executionTime: number;
  guidance?: Guidance;
  keyDecisions: KeyDecision[];
  lessonsLearned: string[];
}

// ============================================================================
// Experience-Enabled Agent Wrapper
// ============================================================================

export class EvolvingAgentWrapper {
  private agent: Agent;
  private agentId: string;
  private agentRole: string;
  private consultant: ExperienceConsultant;
  private enableConsultation: boolean;
  private enableLogging: boolean;
  private consultationOptions: ConsultationOptions;

  // Track decisions during execution
  private currentKeyDecisions: KeyDecision[] = [];
  private currentLessonsLearned: string[] = [];

  constructor(config: EvolvingAgentConfig) {
    this.agent = config.agent;
    this.agentId = config.agentId;
    this.agentRole = config.agentRole;
    this.enableConsultation = config.enableExperienceConsultation;
    this.enableLogging = config.enableOutcomeLogging;
    this.consultationOptions = config.consultationOptions || {};
    this.consultant = getExperienceConsultant();
  }

  /**
   * Execute task with experience consultation
   *
   * Flow:
   * 1. Consult experience store
   * 2. Enhance task description with guidance
   * 3. Execute task
   * 4. Log outcome for learning
   */
  async executeWithExperience(
    task: Task,
    workType: string,
    taskId?: string
  ): Promise<ExecutionResult> {
    const startTime = Date.now();
    const resolvedTaskId = taskId || `task-${this.agentId}-${Date.now()}`;

    // Reset tracking
    this.currentKeyDecisions = [];
    this.currentLessonsLearned = [];

    let guidance: Guidance | undefined;

    // Step 1: Consult experience (if enabled)
    if (this.enableConsultation) {
      console.log(`\n[${this.agentId}] Before I start, let me check my experience...`);

      const context: TaskContext = {
        taskId: resolvedTaskId,
        agentId: this.agentId,
        agentRole: this.agentRole,
        workType: workType,
        description: task.description,
        tags: this.extractTags(task.description)
      };

      try {
        guidance = await this.consultant.consultBeforeTask(context, this.consultationOptions);
        console.log(`[${this.agentId}] Guidance received (confidence: ${(guidance.confidenceScore * 100).toFixed(0)}%)`);

        // Log guidance summary
        if (guidance.relevantExperiences.length > 0) {
          console.log(`[${this.agentId}] Found ${guidance.relevantExperiences.length} similar experiences`);
        }
        if (guidance.applicablePatterns.length > 0) {
          console.log(`[${this.agentId}] Found ${guidance.applicablePatterns.length} applicable patterns`);
        }
        if (guidance.warningsFromFailures.length > 0) {
          console.log(`[${this.agentId}] ⚠️ ${guidance.warningsFromFailures.length} warnings from past failures`);
        }
      } catch (error) {
        console.warn(`[${this.agentId}] Experience consultation failed: ${error}`);
        // Continue without guidance
      }
    }

    // Step 2: Enhance task description with guidance
    let enhancedDescription = task.description;
    if (guidance && guidance.recommendations.length > 0) {
      enhancedDescription = this.enhanceTaskDescription(task.description, guidance);
      console.log(`[${this.agentId}] Task enhanced with ${guidance.recommendations.length} recommendations`);
    }

    // Step 3: Execute the task
    console.log(`[${this.agentId}] Executing task...`);
    let success = false;
    let output: any = null;

    try {
      // Create enhanced task
      const enhancedTask: EnhancedTask = {
        ...task,
        taskId: resolvedTaskId,
        workType: workType,
        originalDescription: task.description,
        description: enhancedDescription,
        guidance: guidance,
        enhancedDescription: enhancedDescription
      };

      // Execute (mock for now - actual execution depends on workflow)
      output = await this.executeTask(enhancedTask);
      success = true;

      // Record successful patterns
      if (guidance?.applicablePatterns) {
        for (const pattern of guidance.applicablePatterns) {
          this.recordDecision({
            decision: `Applied pattern: ${pattern.name}`,
            reasoning: `Pattern had ${(pattern.successRate * 100).toFixed(0)}% success rate`,
            alternatives: [],
            outcome: 'SUCCESS',
            impactScore: pattern.successRate
          });
        }
      }
    } catch (error) {
      success = false;
      output = { error: String(error) };

      // Record failure
      this.recordLesson(`Task failed: ${error}`);
    }

    const executionTime = (Date.now() - startTime) / 1000;

    // Step 4: Log outcome for learning (if enabled)
    if (this.enableLogging) {
      try {
        const context: TaskContext = {
          taskId: resolvedTaskId,
          agentId: this.agentId,
          agentRole: this.agentRole,
          workType: workType,
          description: task.description
        };

        await logTaskOutcome(
          context,
          success ? 'SUCCESS' : 'FAILURE',
          enhancedDescription,
          success ? 80 : 30, // Quality score
          this.currentLessonsLearned,
          this.currentKeyDecisions
        );

        console.log(`[${this.agentId}] Outcome logged for future learning`);
      } catch (error) {
        console.warn(`[${this.agentId}] Failed to log outcome: ${error}`);
      }
    }

    return {
      success,
      output,
      executionTime,
      guidance,
      keyDecisions: this.currentKeyDecisions,
      lessonsLearned: this.currentLessonsLearned
    };
  }

  /**
   * Enhance task description with guidance from experience
   */
  private enhanceTaskDescription(original: string, guidance: Guidance): string {
    const sections: string[] = [original];

    // Add recommendations
    if (guidance.recommendations.length > 0) {
      sections.push('\n\n## Guidance from Past Experience');
      for (const rec of guidance.recommendations) {
        sections.push(`- ${rec}`);
      }
    }

    // Add pattern steps
    if (guidance.applicablePatterns.length > 0) {
      const topPattern = guidance.applicablePatterns[0];
      if (topPattern.steps && topPattern.steps.length > 0) {
        sections.push(`\n\n## Recommended Approach: "${topPattern.name}"`);
        topPattern.steps.forEach((step, idx) => {
          sections.push(`${idx + 1}. ${step}`);
        });
      }
    }

    // Add warnings
    if (guidance.warningsFromFailures.length > 0) {
      sections.push('\n\n## ⚠️ Warnings from Past Failures');
      for (const failure of guidance.warningsFromFailures) {
        sections.push(`- AVOID: ${failure.failureType}`);
        if (failure.preventionStrategies && failure.preventionStrategies.length > 0) {
          sections.push(`  Prevention: ${failure.preventionStrategies[0]}`);
        }
      }
    }

    return sections.join('\n');
  }

  /**
   * Execute the task (mock implementation)
   * In production, this would delegate to the actual agent
   */
  private async executeTask(task: EnhancedTask): Promise<any> {
    // Mock execution - in production this calls the actual LLM
    return {
      taskId: task.taskId,
      agentId: this.agentId,
      workType: task.workType,
      completed: true,
      hadGuidance: !!task.guidance,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Record a key decision during execution
   */
  recordDecision(decision: KeyDecision): void {
    this.currentKeyDecisions.push(decision);
  }

  /**
   * Record a lesson learned during execution
   */
  recordLesson(lesson: string): void {
    this.currentLessonsLearned.push(lesson);
  }

  /**
   * Extract tags from description
   */
  private extractTags(description: string): string[] {
    const tags: string[] = [];

    // Work type keywords
    const workTypeKeywords = ['feature', 'bug', 'maintenance', 'migration', 'quality', 'test', 'security'];
    for (const keyword of workTypeKeywords) {
      if (description.toLowerCase().includes(keyword)) {
        tags.push(keyword);
      }
    }

    // Technical keywords
    const techKeywords = ['api', 'database', 'frontend', 'backend', 'auth', 'validation', 'refactor'];
    for (const keyword of techKeywords) {
      if (description.toLowerCase().includes(keyword)) {
        tags.push(keyword);
      }
    }

    return tags;
  }

  /**
   * Get the wrapped agent
   */
  getAgent(): Agent {
    return this.agent;
  }

  /**
   * Get agent ID
   */
  getAgentId(): string {
    return this.agentId;
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create an evolving wrapper for an agent
 */
export function createEvolvingAgent(
  agent: Agent,
  agentId: string,
  agentRole: string,
  options: Partial<EvolvingAgentConfig> = {}
): EvolvingAgentWrapper {
  return new EvolvingAgentWrapper({
    agent,
    agentId,
    agentRole,
    enableExperienceConsultation: options.enableExperienceConsultation ?? true,
    enableOutcomeLogging: options.enableOutcomeLogging ?? true,
    consultationOptions: options.consultationOptions
  });
}

/**
 * Wrap all agents in the configs with evolving capabilities
 */
export function wrapAgentsWithEvolution(
  agentConfigs: Record<string, Agent>,
  agentRoles: Record<string, string>,
  options: Partial<ConsultationOptions> = {}
): Record<string, EvolvingAgentWrapper> {
  const wrappedAgents: Record<string, EvolvingAgentWrapper> = {};

  for (const [key, agent] of Object.entries(agentConfigs)) {
    const agentId = agent.name || key;
    const agentRole = agentRoles[key] || 'general';

    wrappedAgents[key] = createEvolvingAgent(agent, agentId, agentRole, {
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: options
    });
  }

  return wrappedAgents;
}

// ============================================================================
// Agent Role Mapping
// ============================================================================

export const AGENT_ROLES: Record<string, string> = {
  featureArchitect: 'architect',
  maintenanceSpecialist: 'maintenance',
  qualityInspector: 'quality',
  bugHunter: 'debugging',
  estimationEngine: 'estimation',
  testEngineer: 'testing',
  migrationArchitect: 'migration',
  documentationWriter: 'documentation',
  productOwner: 'product',
  projectLead: 'management'
};

// ============================================================================
// Exports
// ============================================================================

export default EvolvingAgentWrapper;
