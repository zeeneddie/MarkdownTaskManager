/**
 * Validation Loop Workflow Integration
 *
 * Implements the "Generate → Validate → Fix → Repeat" loop.
 * Part of AgentEvolver Phase B (Week 19).
 *
 * Features:
 * - 5-phase validation pipeline
 * - Automatic fix iteration
 * - Experience-informed fixes
 * - Maximum iteration limits with escalation
 *
 * @author Claude Code (Week 19 Day 4)
 * @date 2025-11-22
 */

import axios from 'axios';
import { Agent } from 'kaibanjs';
import { Task } from '../integrations/experienceIntegration';
import { getExperienceConsultant, TaskContext, Guidance } from '../lib/experienceConsultant';

// ============================================================================
// Types
// ============================================================================

export type ValidationPhase = 'linting' | 'type_check' | 'style' | 'unit_tests' | 'e2e_tests';
export type Language = 'python' | 'typescript';

export interface ValidationError {
  message: string;
  line?: number;
  column?: number;
  code?: string;
  severity: 'error' | 'warning';
  phase: ValidationPhase;
}

export interface PhaseResult {
  phase: ValidationPhase;
  passed: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  duration: number;
  toolUsed: string;
}

export interface ValidationResult {
  overallPassed: boolean;
  phasesRun: ValidationPhase[];
  phaseResults: PhaseResult[];
  totalErrors: number;
  totalWarnings: number;
  coverage?: number;
  totalDuration: number;
  iterations: number;
}

export interface ValidationConfig {
  phases: ValidationPhase[];
  maxIterations: number;
  stopOnFirstFailure: boolean;
  requiredCoverage?: number;
  language: Language;
}

export interface ValidationLoopResult {
  finalCode: string;
  isValid: boolean;
  iterations: number;
  validationResult: ValidationResult;
  fixesApplied: FixRecord[];
  experienceUsed: boolean;
}

export interface FixRecord {
  iteration: number;
  phase: ValidationPhase;
  errorsFixed: number;
  fixStrategy: string;
  success: boolean;
}

// ============================================================================
// Default Configurations per Agent
// ============================================================================

export const AGENT_VALIDATION_CONFIGS: Record<string, Partial<ValidationConfig>> = {
  felix: {
    phases: ['linting', 'type_check', 'style', 'unit_tests', 'e2e_tests'],
    maxIterations: 3,
    requiredCoverage: 0.8
  },
  marcus: {
    phases: ['linting', 'type_check', 'unit_tests'],
    maxIterations: 2,
    requiredCoverage: 0.7
  },
  quinn: {
    phases: ['linting', 'type_check', 'style'],
    maxIterations: 1,
    stopOnFirstFailure: false  // Report only
  },
  betty: {
    phases: ['linting', 'unit_tests', 'e2e_tests'],
    maxIterations: 3,
    // Regression tests required
  },
  tessa: {
    phases: ['unit_tests'],
    maxIterations: 1
  },
  miguel: {
    phases: ['e2e_tests'],
    maxIterations: 2
  }
};

// ============================================================================
// Validation Loop Service
// ============================================================================

export class ValidationLoopService {
  private apiBaseUrl: string;
  private consultant = getExperienceConsultant();

  constructor(apiBaseUrl: string = 'http://localhost:8000') {
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Run validation pipeline on code
   */
  async runValidation(
    code: string,
    config: ValidationConfig,
    filePath?: string
  ): Promise<ValidationResult> {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/api/validation/run`, {
        code,
        language: config.language,
        phases: config.phases,
        max_iterations: 1,  // Single run
        stop_on_first_failure: config.stopOnFirstFailure,
        required_coverage: config.requiredCoverage,
        file_path: filePath
      });

      return this.mapValidationResult(response.data);
    } catch (error) {
      console.error('[ValidationLoop] API error:', error);
      throw error;
    }
  }

  /**
   * Main entry point: Iterate until code is valid
   *
   * Loop:
   * 1. Validate code
   * 2. If passed → return
   * 3. Consult experience for fix strategies
   * 4. Apply fixes
   * 5. Repeat until max iterations
   */
  async iterateUntilValid(
    code: string,
    config: ValidationConfig,
    agentContext?: TaskContext
  ): Promise<ValidationLoopResult> {
    console.log('\n=== VALIDATION LOOP STARTING ===');
    console.log(`Language: ${config.language}`);
    console.log(`Phases: ${config.phases.join(', ')}`);
    console.log(`Max iterations: ${config.maxIterations}`);

    let currentCode = code;
    let iteration = 0;
    const fixesApplied: FixRecord[] = [];
    let experienceUsed = false;
    let lastResult: ValidationResult | null = null;

    while (iteration < config.maxIterations) {
      iteration++;
      console.log(`\n--- Iteration ${iteration}/${config.maxIterations} ---`);

      // Step 1: Run validation
      const result = await this.runValidation(currentCode, config);
      lastResult = result;

      console.log(`Validation result: ${result.overallPassed ? 'PASSED' : 'FAILED'}`);
      console.log(`  Errors: ${result.totalErrors}, Warnings: ${result.totalWarnings}`);

      // Step 2: Check if passed
      if (result.overallPassed) {
        console.log('\n=== VALIDATION PASSED ===');
        return {
          finalCode: currentCode,
          isValid: true,
          iterations: iteration,
          validationResult: result,
          fixesApplied,
          experienceUsed
        };
      }

      // Step 3: If not last iteration, try to fix
      if (iteration < config.maxIterations) {
        // Collect errors from failed phases
        const failedPhases = result.phaseResults.filter(pr => !pr.passed);

        for (const failedPhase of failedPhases) {
          console.log(`\nFixing ${failedPhase.phase} errors (${failedPhase.errors.length})...`);

          // Consult experience for fix strategies
          let fixStrategy = 'default';
          if (agentContext) {
            const guidance = await this.consultForFixStrategy(
              agentContext,
              failedPhase.phase,
              failedPhase.errors
            );
            if (guidance) {
              fixStrategy = guidance.recommended_approach || 'experience-guided';
              experienceUsed = true;
            }
          }

          // Apply fix
          const fixResult = await this.applyFix(
            currentCode,
            config.language,
            failedPhase.errors,
            fixStrategy
          );

          if (fixResult.success) {
            currentCode = fixResult.fixedCode;
          }

          fixesApplied.push({
            iteration,
            phase: failedPhase.phase,
            errorsFixed: fixResult.errorsFixed,
            fixStrategy,
            success: fixResult.success
          });
        }
      }
    }

    console.log('\n=== MAX ITERATIONS REACHED ===');
    return {
      finalCode: currentCode,
      isValid: false,
      iterations: iteration,
      validationResult: lastResult!,
      fixesApplied,
      experienceUsed
    };
  }

  /**
   * Consult experience store for fix strategies
   */
  private async consultForFixStrategy(
    context: TaskContext,
    phase: ValidationPhase,
    errors: ValidationError[]
  ): Promise<any> {
    try {
      // Create a specific context for the fix
      const fixContext: TaskContext = {
        ...context,
        description: `Fix ${phase} errors: ${errors.slice(0, 3).map(e => e.message).join('; ')}`
      };

      const guidance = await this.consultant.consultBeforeTask(fixContext, {
        maxExperiences: 3,
        maxPatterns: 2,
        maxFailures: 5,  // Important to know what didn't work
        minSimilarity: 0.4
      });

      if (guidance.confidenceScore > 0.5) {
        return {
          recommended_approach: guidance.recommendations[0] || 'Follow standard fix procedure',
          patterns: guidance.applicablePatterns,
          warnings: guidance.warningsFromFailures
        };
      }
    } catch (error) {
      console.warn('[ValidationLoop] Experience consultation failed:', error);
    }

    return null;
  }

  /**
   * Apply fixes to code based on errors
   */
  private async applyFix(
    code: string,
    language: Language,
    errors: ValidationError[],
    strategy: string
  ): Promise<{ fixedCode: string; errorsFixed: number; success: boolean }> {
    try {
      // Call the API to request fixes
      const response = await axios.post(`${this.apiBaseUrl}/api/validation/fix`, {
        code,
        language,
        errors: errors.map(e => ({
          message: e.message,
          line: e.line,
          column: e.column,
          code: e.code
        })),
        strategy
      });

      return {
        fixedCode: response.data.fixed_code || code,
        errorsFixed: response.data.errors_fixed || 0,
        success: response.data.success || false
      };
    } catch (error) {
      // If API fails, return original code
      console.warn('[ValidationLoop] Fix API failed, returning original:', error);
      return {
        fixedCode: code,
        errorsFixed: 0,
        success: false
      };
    }
  }

  /**
   * Map API response to internal types
   */
  private mapValidationResult(data: any): ValidationResult {
    return {
      overallPassed: data.overall_passed,
      phasesRun: data.phases_run,
      phaseResults: (data.phase_results || []).map((pr: any) => ({
        phase: pr.phase as ValidationPhase,
        passed: pr.passed,
        errors: (pr.errors || []).map((e: any) => ({
          message: e.message,
          line: e.line,
          column: e.column,
          code: e.code,
          severity: 'error' as const,
          phase: pr.phase as ValidationPhase
        })),
        warnings: (pr.warnings || []).map((w: any) => ({
          message: w.message,
          line: w.line,
          column: w.column,
          code: w.code,
          severity: 'warning' as const,
          phase: pr.phase as ValidationPhase
        })),
        duration: pr.duration,
        toolUsed: pr.tool_used
      })),
      totalErrors: data.total_errors,
      totalWarnings: data.total_warnings,
      coverage: data.coverage,
      totalDuration: data.total_duration,
      iterations: data.iterations || 1
    };
  }
}

// ============================================================================
// Workflow Integration
// ============================================================================

/**
 * Wrap agent task execution with validation loop
 */
export async function executeTaskWithValidation(
  agent: Agent,
  task: Task,
  generatedCode: string,
  language: Language,
  agentName: string
): Promise<{
  code: string;
  validated: boolean;
  validationResult: ValidationLoopResult;
}> {
  console.log(`\n[${agentName}] Starting task with validation loop...`);

  // Get agent-specific config
  const agentConfig = AGENT_VALIDATION_CONFIGS[agentName.toLowerCase()] || {};
  const config: ValidationConfig = {
    phases: agentConfig.phases || ['linting', 'type_check'],
    maxIterations: agentConfig.maxIterations || 2,
    stopOnFirstFailure: agentConfig.stopOnFirstFailure ?? false,
    requiredCoverage: agentConfig.requiredCoverage,
    language
  };

  // Create task context for experience consultation
  const taskContext: TaskContext = {
    taskId: `task-${agentName}-${Date.now()}`,
    agentId: agentName.toLowerCase(),
    agentRole: agentName.toLowerCase(),
    workType: 'code_generation',
    description: task.description
  };

  // Run validation loop
  const service = new ValidationLoopService();
  const result = await service.iterateUntilValid(generatedCode, config, taskContext);

  console.log(`[${agentName}] Validation complete: ${result.isValid ? 'PASSED' : 'FAILED'}`);
  console.log(`[${agentName}] Iterations: ${result.iterations}, Fixes applied: ${result.fixesApplied.length}`);

  return {
    code: result.finalCode,
    validated: result.isValid,
    validationResult: result
  };
}

/**
 * Create validation-enabled workflow executor
 */
export function createValidatingWorkflow(
  workflowName: string,
  agents: Agent[],
  language: Language = 'typescript'
) {
  return async (input: any): Promise<any> => {
    console.log(`\n=== ${workflowName} (with validation) ===`);

    const results: any[] = [];

    for (const agent of agents) {
      const agentName = agent.name || 'UnknownAgent';
      console.log(`\nExecuting ${agentName}...`);

      // Create task
      const task: Task = {
        description: `${workflowName} task for ${agentName}`,
        expectedOutput: `Validated output from ${agentName}`
      };

      // Mock code generation (in production, this would be LLM output)
      const generatedCode = `// Generated by ${agentName}\n// Task: ${input.description || 'N/A'}\nconsole.log('Hello from ${agentName}');`;

      // Execute with validation
      const result = await executeTaskWithValidation(
        agent,
        task,
        generatedCode,
        language,
        agentName
      );

      results.push({
        agent: agentName,
        success: result.validated,
        iterations: result.validationResult.iterations,
        errors: result.validationResult.validationResult.totalErrors,
        fixesApplied: result.validationResult.fixesApplied.length
      });

      // If validation failed and this agent is critical, stop workflow
      if (!result.validated && ['felix', 'marcus'].includes(agentName.toLowerCase())) {
        console.warn(`[${workflowName}] Critical agent ${agentName} failed validation, stopping workflow`);
        break;
      }
    }

    return {
      workflow: workflowName,
      completed: results.every(r => r.success),
      agentResults: results,
      timestamp: new Date().toISOString()
    };
  };
}

// ============================================================================
// Singleton
// ============================================================================

let validationServiceInstance: ValidationLoopService | null = null;

export function getValidationLoopService(): ValidationLoopService {
  if (!validationServiceInstance) {
    validationServiceInstance = new ValidationLoopService();
  }
  return validationServiceInstance;
}

// ============================================================================
// Exports
// ============================================================================

export default ValidationLoopService;
