/**
 * Workflow Board - KaibanJS Team Configuration
 *
 * Central board for managing agent teams and executing workflows
 * based on work types.
 */

import { Team, Task } from 'kaibanjs';
import {
  WorkType,
  WorkRequest,
  TeamConfiguration,
  routeWorkRequest,
  validateWorkRequest
} from '../routers/workTypeRouter';

export interface WorkflowResult {
  workType: WorkType;
  teamName: string;
  executionTime: number;
  success: boolean;
  outputs: Record<string, any>;
  errors?: string[];
}

export interface WorkflowOptions {
  timeout?: number;  // milliseconds
  retries?: number;
  verbose?: boolean;
}

/**
 * Workflow Board
 * Manages the creation and execution of agent teams
 */
export class WorkflowBoard {
  private activeTeams: Map<string, Team>;
  private executionHistory: WorkflowResult[];

  constructor() {
    this.activeTeams = new Map();
    this.executionHistory = [];
  }

  /**
   * Execute workflow for a work request
   */
  async executeWorkflow(
    request: WorkRequest,
    options: WorkflowOptions = {}
  ): Promise<WorkflowResult> {
    const startTime = Date.now();

    // Validate request
    const validation = validateWorkRequest(request);
    if (!validation.valid) {
      return {
        workType: WorkType.NEW_FEATURE,
        teamName: '',
        executionTime: 0,
        success: false,
        outputs: {},
        errors: validation.errors
      };
    }

    try {
      // Route to appropriate team
      const { workType, teamConfig } = routeWorkRequest(request);

      if (options.verbose) {
        console.log(`📋 Work Type: ${workType}`);
        console.log(`👥 Team: ${teamConfig.agents.length} agents`);
        console.log(`🔄 Process: ${teamConfig.process}`);
      }

      // Create team
      const teamName = `${workType} Team`;
      const team = this.createTeam(workType, teamConfig);

      // Create task
      const task = this.createTask(workType, request, teamConfig);

      // Execute with timeout
      const result = await this.executeWithTimeout(
        team,
        task,
        options.timeout || 300000  // 5 minutes default
      );

      const executionTime = Date.now() - startTime;

      const workflowResult: WorkflowResult = {
        workType,
        teamName,
        executionTime,
        success: true,
        outputs: result
      };

      // Store in history
      this.executionHistory.push(workflowResult);

      return workflowResult;

    } catch (error) {
      const executionTime = Date.now() - startTime;

      const workflowResult: WorkflowResult = {
        workType: WorkType.NEW_FEATURE,
        teamName: '',
        executionTime,
        success: false,
        outputs: {},
        errors: [error instanceof Error ? error.message : String(error)]
      };

      this.executionHistory.push(workflowResult);

      return workflowResult;
    }
  }

  /**
   * Create team for work type
   */
  private createTeam(workType: WorkType, config: TeamConfiguration): Team {
    const teamName = `${workType} Team`;

    // Check if team already exists
    if (this.activeTeams.has(teamName)) {
      return this.activeTeams.get(teamName)!;
    }

    // Create new team
    const team = new Team({
      name: teamName,
      agents: config.agents,
      // @ts-ignore - KaibanJS type might not have process yet
      process: config.process
    });

    this.activeTeams.set(teamName, team);

    return team;
  }

  /**
   * Create task based on work type
   */
  private createTask(workType: WorkType, request: WorkRequest, teamConfig: TeamConfiguration): Task {
    const taskDescriptions: Record<WorkType, string> = {
      [WorkType.NEW_FEATURE]: `
        Analyze this new feature request and create a complete work breakdown:
        ${request.description}

        Please provide:
        1. Epic-level breakdown (Epic → Features → Stories → Tasks)
        2. Story point estimates for all items
        3. Test strategy and scenarios
        4. Quality review and architecture assessment
        5. Technical documentation

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.MAINTENANCE]: `
        Analyze this maintenance request and create an action plan:
        ${request.description}

        Please provide:
        1. Analysis of technical debt and dependencies
        2. Prioritized list of maintenance tasks
        3. Effort estimates
        4. Testing strategy for changes
        5. Quality metrics before and after

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.QUALITY_AUDIT]: `
        Conduct a comprehensive quality audit:
        ${request.description}

        Please audit:
        1. Security vulnerabilities (OWASP Top 10)
        2. Performance bottlenecks
        3. Code quality (complexity, duplication, coverage)
        4. Technical debt ratio
        5. Test coverage gaps

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.BUG]: `
        Analyze and fix this bug:
        ${request.description}

        Please provide:
        1. Root cause analysis
        2. Suggested fix with code changes
        3. Regression test to prevent recurrence
        4. Documentation of the bug and fix

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.ENHANCEMENT]: `
        Analyze this enhancement request:
        ${request.description}

        Please provide:
        1. Analysis of existing feature
        2. Enhancement design and implementation plan
        3. Impact analysis (backward compatibility, performance)
        4. Effort estimates
        5. Testing strategy

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.MIGRATION]: `
        Plan this migration:
        ${request.description}

        Please provide:
        1. Migration assessment (complexity, risks)
        2. Detailed migration plan (strategy, phases, timeline)
        3. Data mapping and transformation rules
        4. Validation and testing strategy
        5. Rollback plan

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.QUALITY_IMPROVEMENT]: `
        Create a quality improvement plan:
        ${request.description}

        Please provide:
        1. Quality scan results (code smells, complexity, duplication)
        2. Prioritized remediation tasks
        3. Effort estimates
        4. Testing strategy for improvements
        5. Metrics tracking (before/after)

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.TESTING]: `
        Generate comprehensive test suite:
        ${request.description}

        Please provide:
        1. Unit tests (AAA pattern)
        2. Integration tests
        3. E2E test scenarios
        4. BDD scenarios (Gherkin)
        5. Coverage report and gaps

        Context: ${JSON.stringify(request.context || {})}
      `,

      [WorkType.PROJECT_DEFINITION]: `
        Define this new project:
        ${request.description}

        Please provide:
        1. Project scope and boundaries
        2. Business goals and success criteria
        3. Constraints and assumptions
        4. High-level roadmap and milestones
        5. Resource requirements and team structure

        Context: ${JSON.stringify(request.context || {})}
      `
    };

    return new Task({
      description: taskDescriptions[workType],
      expectedOutput: this.getExpectedOutput(workType),
      agent: teamConfig.agents[0]  // First agent in the team
    });
  }

  /**
   * Get expected output format for work type
   */
  private getExpectedOutput(workType: WorkType): string {
    const outputs: Record<WorkType, string> = {
      [WorkType.NEW_FEATURE]: 'Complete work breakdown with Epic, Features, Stories, Tasks, estimates, test plan, quality review, and documentation',
      [WorkType.MAINTENANCE]: 'Maintenance plan with prioritized tasks, estimates, and quality metrics',
      [WorkType.QUALITY_AUDIT]: 'Comprehensive quality audit report with findings and remediation plan',
      [WorkType.BUG]: 'Root cause analysis, fix implementation, regression test, and documentation',
      [WorkType.ENHANCEMENT]: 'Enhancement design, implementation plan, impact analysis, and estimates',
      [WorkType.MIGRATION]: 'Migration assessment, detailed plan, validation strategy, and rollback plan',
      [WorkType.QUALITY_IMPROVEMENT]: 'Quality improvement plan with prioritized tasks and metrics',
      [WorkType.TESTING]: 'Complete test suite with unit, integration, E2E tests and coverage report',
      [WorkType.PROJECT_DEFINITION]: 'Complete project definition with scope, business goals, constraints, success criteria, roadmap, and resource plan'
    };

    return outputs[workType];
  }

  /**
   * Execute team with timeout
   */
  private async executeWithTimeout(
    team: Team,
    task: Task,
    timeout: number
  ): Promise<any> {
    return Promise.race([
      // @ts-ignore - KaibanJS team.start() type compatibility
      team.start(task),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error(`Execution timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }

  /**
   * Get execution history
   */
  getExecutionHistory(): WorkflowResult[] {
    return this.executionHistory;
  }

  /**
   * Get active teams
   */
  getActiveTeams(): string[] {
    return Array.from(this.activeTeams.keys());
  }

  /**
   * Clear team cache
   */
  clearTeamCache(): void {
    this.activeTeams.clear();
  }

  /**
   * Get statistics
   */
  getStatistics(): {
    totalExecutions: number;
    successRate: number;
    averageExecutionTime: number;
    workTypeBreakdown: Record<string, number>;
  } {
    const total = this.executionHistory.length;
    const successful = this.executionHistory.filter(r => r.success).length;

    const totalTime = this.executionHistory.reduce(
      (sum, r) => sum + r.executionTime,
      0
    );

    const workTypeBreakdown: Record<string, number> = {};
    this.executionHistory.forEach(r => {
      workTypeBreakdown[r.workType] = (workTypeBreakdown[r.workType] || 0) + 1;
    });

    return {
      totalExecutions: total,
      successRate: total > 0 ? (successful / total) * 100 : 0,
      averageExecutionTime: total > 0 ? totalTime / total : 0,
      workTypeBreakdown
    };
  }
}

/**
 * Singleton instance
 */
export const workflowBoard = new WorkflowBoard();
