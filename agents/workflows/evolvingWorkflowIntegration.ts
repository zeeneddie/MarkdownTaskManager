/**
 * Evolving Workflow Integration
 *
 * Integrates validation loops and experience consultation into all 9 work type workflows.
 * Part of AgentEvolver Phase B (Week 20).
 *
 * Work Types:
 * 1. NEW_FEATURE - Felix + Quinn + Tessa
 * 2. MAINTENANCE - Marcus + Quinn + Tessa
 * 3. BUG - Betty + Tessa + Quinn
 * 4. QUALITY_AUDIT - Quinn + Marcus
 * 5. ENHANCEMENT - Felix + Tessa + Diana
 * 6. MIGRATION - Miguel + Tessa + Diana
 * 7. QUALITY_IMPROVEMENT - Quinn + Marcus + Tessa
 * 8. TESTING - Tessa + Quinn
 * 9. PROJECT_DEFINITION - Peter + Felix + Paul + Diana
 *
 * @author Claude Code (Week 20 Day 2)
 * @date 2025-11-22
 */

import {
  getAllEvolvingAgents,
  getEvolvingAgentByRole,
  executeEvolvingFeatureWorkflow,
  executeEvolvingMaintenanceWorkflow,
  executeEvolvingBugWorkflow,
  executeEvolvingMigrationWorkflow,
  executeEvolvingProjectDefinitionWorkflow,
  executeEvolvingTestingWorkflow
} from '../integrations/agentEvolutionIntegration';

import { ExecutionResult } from '../integrations/experienceIntegration';

import {
  ValidationLoopService,
  ValidationConfig,
  ValidationResult,
  ValidationLoopResult,
  ValidationPhase,
  AGENT_VALIDATION_CONFIGS
} from './validationLoopWorkflow';

// ============================================================================
// Types
// ============================================================================

export type WorkType =
  | 'NEW_FEATURE'
  | 'MAINTENANCE'
  | 'BUG'
  | 'QUALITY_AUDIT'
  | 'ENHANCEMENT'
  | 'MIGRATION'
  | 'QUALITY_IMPROVEMENT'
  | 'TESTING'
  | 'PROJECT_DEFINITION';

export interface WorkflowRequest {
  workType: WorkType;
  description: string;
  context?: Record<string, any>;
  enableValidation?: boolean;
  enableExperience?: boolean;
}

export interface WorkflowResult {
  workType: WorkType;
  success: boolean;
  agentResults: Record<string, ExecutionResult>;
  validationResults?: ValidationLoopResult[];
  totalExecutionTime: number;
  lessonsLearned: string[];
  recommendations: string[];
}

// ============================================================================
// Workflow Configuration
// ============================================================================

interface WorkflowConfig {
  primaryAgent: string;
  supportingAgents: string[];
  validationRequired: boolean;
  validationPhases: string[];
}

const WORKFLOW_CONFIGS: Record<WorkType, WorkflowConfig> = {
  NEW_FEATURE: {
    primaryAgent: 'felix',
    supportingAgents: ['quinn', 'tessa', 'diana'],
    validationRequired: true,
    validationPhases: ['linting', 'typecheck', 'unit_tests', 'e2e_tests']
  },
  MAINTENANCE: {
    primaryAgent: 'marcus',
    supportingAgents: ['quinn', 'tessa'],
    validationRequired: true,
    validationPhases: ['linting', 'typecheck', 'unit_tests']
  },
  BUG: {
    primaryAgent: 'betty',
    supportingAgents: ['tessa', 'quinn'],
    validationRequired: true,
    validationPhases: ['linting', 'unit_tests', 'e2e_tests']
  },
  QUALITY_AUDIT: {
    primaryAgent: 'quinn',
    supportingAgents: ['marcus'],
    validationRequired: false,  // Audit is read-only
    validationPhases: ['linting', 'style']
  },
  ENHANCEMENT: {
    primaryAgent: 'felix',
    supportingAgents: ['tessa', 'diana'],
    validationRequired: true,
    validationPhases: ['linting', 'typecheck', 'unit_tests']
  },
  MIGRATION: {
    primaryAgent: 'miguel',
    supportingAgents: ['tessa', 'diana', 'quinn'],
    validationRequired: true,
    validationPhases: ['linting', 'typecheck', 'unit_tests', 'e2e_tests']
  },
  QUALITY_IMPROVEMENT: {
    primaryAgent: 'quinn',
    supportingAgents: ['marcus', 'tessa'],
    validationRequired: true,
    validationPhases: ['linting', 'typecheck', 'style', 'unit_tests']
  },
  TESTING: {
    primaryAgent: 'tessa',
    supportingAgents: ['quinn'],
    validationRequired: true,
    validationPhases: ['linting', 'unit_tests']
  },
  PROJECT_DEFINITION: {
    primaryAgent: 'peter',
    supportingAgents: ['felix', 'paul', 'diana'],
    validationRequired: false,  // Definition is mostly documentation
    validationPhases: ['linting']
  }
};

// ============================================================================
// Evolving Workflow Executor
// ============================================================================

export class EvolvingWorkflowExecutor {
  private validationService: ValidationLoopService;

  constructor() {
    this.validationService = new ValidationLoopService();
  }

  /**
   * Execute a workflow with experience consultation and validation
   */
  async executeWorkflow(request: WorkflowRequest): Promise<WorkflowResult> {
    const startTime = Date.now();
    const config = WORKFLOW_CONFIGS[request.workType];

    console.log(`\n${'='.repeat(60)}`);
    console.log(`EVOLVING WORKFLOW: ${request.workType}`);
    console.log(`Primary Agent: ${config.primaryAgent}`);
    console.log(`Supporting Agents: ${config.supportingAgents.join(', ')}`);
    console.log(`${'='.repeat(60)}\n`);

    const agentResults: Record<string, ExecutionResult> = {};
    const validationResults: ValidationLoopResult[] = [];
    const lessonsLearned: string[] = [];
    const recommendations: string[] = [];

    try {
      // Execute workflow based on work type
      const workflowResult = await this.executeWorkflowByType(request);

      // Merge agent results
      Object.assign(agentResults, workflowResult);

      // Collect lessons learned from all agents
      for (const [agent, result] of Object.entries(agentResults)) {
        if (result.lessonsLearned) {
          lessonsLearned.push(...result.lessonsLearned.map(l => `[${agent}] ${l}`));
        }
      }

      // Run validation if enabled and required
      if (request.enableValidation !== false && config.validationRequired) {
        console.log('\n--- Running Validation Loop ---');

        // Get generated code from primary agent result
        const primaryResult = agentResults[config.primaryAgent];
        if (primaryResult?.output?.code) {
          const validationConfig = this.getValidationConfig(request.workType, config.primaryAgent);
          const validationResult = await this.validationService.iterateUntilValid(
            primaryResult.output.code,
            validationConfig
          );
          validationResults.push(validationResult);

          // Add validation lessons
          if (!validationResult.isValid) {
            lessonsLearned.push(`Validation failed after ${validationResult.iterations} iterations`);
          }
        }
      }

      // Generate recommendations based on results
      recommendations.push(...this.generateRecommendations(agentResults, validationResults));

      const success = Object.values(agentResults).every(r => r.success);

      return {
        workType: request.workType,
        success,
        agentResults,
        validationResults: validationResults.length > 0 ? validationResults : undefined,
        totalExecutionTime: Date.now() - startTime,
        lessonsLearned,
        recommendations
      };

    } catch (error) {
      console.error(`Workflow execution failed: ${error}`);
      return {
        workType: request.workType,
        success: false,
        agentResults,
        totalExecutionTime: Date.now() - startTime,
        lessonsLearned: [`Error: ${error}`],
        recommendations: ['Review error and retry']
      };
    }
  }

  /**
   * Execute workflow by type using evolving agents
   */
  private async executeWorkflowByType(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    switch (request.workType) {
      case 'NEW_FEATURE':
        return this.executeNewFeatureWorkflow(request);

      case 'MAINTENANCE':
        return this.executeMaintenanceWorkflow(request);

      case 'BUG':
        return this.executeBugWorkflow(request);

      case 'QUALITY_AUDIT':
        return this.executeQualityAuditWorkflow(request);

      case 'ENHANCEMENT':
        return this.executeEnhancementWorkflow(request);

      case 'MIGRATION':
        return this.executeMigrationWorkflow(request);

      case 'QUALITY_IMPROVEMENT':
        return this.executeQualityImprovementWorkflow(request);

      case 'TESTING':
        return this.executeTestingWorkflow(request);

      case 'PROJECT_DEFINITION':
        return this.executeProjectDefinitionWorkflow(request);

      default:
        throw new Error(`Unknown work type: ${request.workType}`);
    }
  }

  // ============================================================================
  // Individual Workflow Implementations
  // ============================================================================

  private async executeNewFeatureWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const result = await executeEvolvingFeatureWorkflow(
      request.description,
      request.context || {}
    );
    return result;
  }

  private async executeMaintenanceWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const result = await executeEvolvingMaintenanceWorkflow(
      request.context?.scope || 'full',
      request.context?.focusAreas || ['dependencies', 'security', 'performance']
    );
    return result;
  }

  private async executeBugWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const result = await executeEvolvingBugWorkflow(
      request.description,
      request.context?.errorLogs || []
    );
    return result;
  }

  private async executeQualityAuditWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const agents = getAllEvolvingAgents();

    const quinnResult = await agents.quinn.executeQualityAudit(
      request.context?.targetFiles || [],
      request.context?.auditTypes || ['security', 'code_quality', 'coverage']
    );

    const marcusResult = await agents.marcus.executeMaintenanceAnalysis(
      request.context?.scope || 'full',
      ['tech_debt', 'complexity']
    );

    return { quinn: quinnResult, marcus: marcusResult };
  }

  private async executeEnhancementWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const agents = getAllEvolvingAgents();

    const felixResult = await agents.felix.executeFeatureDesign(
      request.description,
      { ...request.context, type: 'enhancement' }
    );

    const tessaResult = await agents.tessa.executeTestGeneration(
      request.description,
      ['unit', 'integration']
    );

    const dianaResult = await agents.diana.executeDocumentation(
      'api',
      { enhancement: request.description }
    );

    return { felix: felixResult, tessa: tessaResult, diana: dianaResult };
  }

  private async executeMigrationWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const result = await executeEvolvingMigrationWorkflow(
      request.context?.fromStack || 'legacy',
      request.context?.toStack || 'modern',
      request.context?.scope || request.description
    );
    return result;
  }

  private async executeQualityImprovementWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const agents = getAllEvolvingAgents();

    // Quinn identifies issues
    const quinnResult = await agents.quinn.executeQualityAudit(
      request.context?.targetFiles || [],
      ['code_quality', 'complexity', 'duplication']
    );

    // Marcus fixes issues
    const marcusResult = await agents.marcus.executeDebtRemediation(
      request.context?.debtItems || [],
      request.context?.maxEffortHours || 8
    );

    // Tessa validates fixes
    const tessaResult = await agents.tessa.executeTestGeneration(
      'Quality improvement validation',
      ['unit']
    );

    return { quinn: quinnResult, marcus: marcusResult, tessa: tessaResult };
  }

  private async executeTestingWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const result = await executeEvolvingTestingWorkflow(
      request.context?.targetCode || request.description,
      request.context?.testTypes || ['unit', 'integration', 'e2e']
    );
    return result;
  }

  private async executeProjectDefinitionWorkflow(
    request: WorkflowRequest
  ): Promise<Record<string, ExecutionResult>> {
    const result = await executeEvolvingProjectDefinitionWorkflow(
      request.description,
      request.context?.stakeholders || []
    );
    return result;
  }

  // ============================================================================
  // Helper Methods
  // ============================================================================

  private getValidationConfig(workType: WorkType, agentName: string): ValidationConfig {
    const baseConfig = AGENT_VALIDATION_CONFIGS[agentName] || {};
    const workflowConfig = WORKFLOW_CONFIGS[workType];

    return {
      phases: workflowConfig.validationPhases as ValidationPhase[],
      maxIterations: 3,
      stopOnFirstFailure: false,
      language: 'typescript',
      ...baseConfig
    };
  }

  private generateRecommendations(
    agentResults: Record<string, ExecutionResult>,
    validationResults: ValidationLoopResult[]
  ): string[] {
    const recommendations: string[] = [];

    // Check for failed agents
    const failedAgents = Object.entries(agentResults)
      .filter(([_, r]) => !r.success)
      .map(([name]) => name);

    if (failedAgents.length > 0) {
      recommendations.push(`Review failures from: ${failedAgents.join(', ')}`);
    }

    // Check validation results
    for (const validation of validationResults) {
      if (!validation.isValid) {
        const failedPhases = validation.validationResult.phaseResults
          .filter(p => !p.passed)
          .map(p => p.phase);
        recommendations.push(`Fix validation issues in: ${failedPhases.join(', ')}`);
      }

      if (validation.iterations > 1) {
        recommendations.push(`Code required ${validation.iterations} iterations to validate - consider simpler approach`);
      }
    }

    // Add default recommendations if none generated
    if (recommendations.length === 0) {
      recommendations.push('All checks passed - ready for review');
    }

    return recommendations;
  }
}

// ============================================================================
// Factory Function
// ============================================================================

let executorInstance: EvolvingWorkflowExecutor | null = null;

export function getEvolvingWorkflowExecutor(): EvolvingWorkflowExecutor {
  if (!executorInstance) {
    executorInstance = new EvolvingWorkflowExecutor();
  }
  return executorInstance;
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Execute any workflow with evolving agents and validation
 */
export async function executeEvolvingWorkflow(
  workType: WorkType,
  description: string,
  context?: Record<string, any>
): Promise<WorkflowResult> {
  const executor = getEvolvingWorkflowExecutor();
  return executor.executeWorkflow({
    workType,
    description,
    context,
    enableValidation: true,
    enableExperience: true
  });
}

/**
 * Execute workflow without validation (for quick iterations)
 */
export async function executeQuickWorkflow(
  workType: WorkType,
  description: string,
  context?: Record<string, any>
): Promise<WorkflowResult> {
  const executor = getEvolvingWorkflowExecutor();
  return executor.executeWorkflow({
    workType,
    description,
    context,
    enableValidation: false,
    enableExperience: true
  });
}

// ============================================================================
// Exports
// ============================================================================

export default {
  EvolvingWorkflowExecutor,
  getEvolvingWorkflowExecutor,
  executeEvolvingWorkflow,
  executeQuickWorkflow,
  WORKFLOW_CONFIGS
};
