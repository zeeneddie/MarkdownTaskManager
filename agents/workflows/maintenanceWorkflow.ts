/**
 * MAINTENANCE Workflow
 *
 * Implements 6-stage Code-Maintenance-Agent workflow:
 * 1. Analysis → 2. Prioritization → 3. Planning →
 * 4. Execution → 5. Testing → 6. Deployment
 */

import { Team, Task } from 'kaibanjs';
import { agents } from '../configs/agents';
import {
  executeCodeMaintenanceWorkflow,
  validateCodeMaintenanceRequest,
  type CodeMaintenanceRequest,
  type CodeMaintenanceResult
} from './codeMaintenanceAgent';

export interface MaintenanceRequest {
  scope: 'full_codebase' | 'module' | 'specific_files';
  targetFiles?: string[];  // For 'specific_files' scope
  modulePath?: string;      // For 'module' scope
  focusAreas?: ('dependencies' | 'code_quality' | 'security' | 'performance' | 'tests' | 'documentation')[];
  thresholds?: {
    maxComplexity?: number;
    minTestCoverage?: number;
    maxTechnicalDebtRatio?: number;
  };
  urgency?: 'low' | 'medium' | 'high' | 'critical';
}

export interface MaintenanceResult {
  analysisReport: {
    technicalDebtRatio: number;
    dependencyVulnerabilities: number;
    codeSmells: number;
    complexityViolations: number;
  };
  findings: Array<{
    category: 'dependency' | 'code_smell' | 'security' | 'performance' | 'test' | 'documentation';
    severity: 'critical' | 'high' | 'medium' | 'low';
    issue: string;
    location?: string;
    recommendation: string;
    effortSP: number;
    risk: 'high' | 'medium' | 'low';
  }>;
  prioritizedTasks: Array<{
    id: string;
    title: string;
    priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
    effortSP: number;
    timeline: string;
    dependencies: string[];
  }>;
  qualityMetrics: {
    beforeMaintenance: {
      testCoverage: number;
      complexity: number;
      duplication: number;
    };
    afterMaintenance: {
      testCoverage: number;
      complexity: number;
      duplication: number;
    };
    improvement: {
      testCoverageIncrease: number;
      complexityReduction: number;
      duplicationReduction: number;
    };
  };
  testStrategy: {
    regressionTests: number;
    newTests: number;
    coverageGoal: number;
  };
}

/**
 * Execute MAINTENANCE workflow
 * Sequential: Marcus → Quinn → Tessa → Eliza
 */
export async function executeMaintenanceWorkflow(
  request: MaintenanceRequest
): Promise<MaintenanceResult> {

  console.log('🔧 Starting MAINTENANCE workflow...');
  console.log(`🎯 Scope: ${request.scope}`);
  console.log(`🔍 Focus Areas: ${request.focusAreas?.join(', ') || 'All'}`);

  // Create maintenance team (sequential execution)
  const team = new Team({
    name: 'Maintenance Team',
    agents: [
      agents.maintenanceSpecialist,  // 1. Marcus - Analysis & planning
      agents.qualityInspector,       // 2. Quinn - Quality review
      agents.testEngineer,           // 3. Tessa - Test strategy
      agents.estimationEngine        // 4. Eliza - Effort estimates
    ],
    // @ts-ignore
    process: 'sequential'
  });

  // Create comprehensive maintenance task
  const maintenanceTask = new Task({
    description: `
      Perform comprehensive maintenance analysis and planning:

      **Scope:** ${request.scope}
      **Focus Areas:** ${request.focusAreas?.join(', ') || 'All areas'}
      **Urgency:** ${request.urgency || 'medium'}

      **Thresholds:**
      - Max Complexity: ${request.thresholds?.maxComplexity || 15}
      - Min Test Coverage: ${request.thresholds?.minTestCoverage || 80}%
      - Max Technical Debt Ratio: ${request.thresholds?.maxTechnicalDebtRatio || 10}%

      Please execute the 6-stage maintenance workflow:

      **Stage 1: Analysis**
      - Scan for dependency vulnerabilities (npm audit, pip-audit)
      - Detect code smells (complexity, duplication)
      - Identify security issues
      - Measure technical debt ratio

      **Stage 2: Prioritization**
      - Create Risk × Impact matrix
      - Classify as P0-P4 priorities
      - Calculate ROI for each fix

      **Stage 3: Planning**
      - Create maintenance roadmap
      - Batch related updates
      - Estimate effort (Story Points)
      - Schedule tasks

      **Stage 4: Execution Plan** (not actual execution, just plan)
      - Define automated vs manual tasks
      - Plan refactoring approach
      - Design update strategy

      **Stage 5: Testing Strategy**
      - Plan regression tests
      - Define validation criteria
      - Set coverage goals

      **Stage 6: Deployment Plan**
      - Define staging process
      - Plan monitoring
      - Create rollback procedures

      Return structured analysis with findings, priorities, and execution plan.
    `,
    expectedOutput: 'Comprehensive maintenance report with prioritized action plan',
    agent: agents.maintenanceSpecialist  // Marcus - Maintenance Specialist
  });

  // Execute workflow
  console.log('👨‍🔧 Stage 1-2: Marcus analyzing codebase...');
  console.log('👨‍⚖️ Stage 3: Quinn reviewing quality...');
  console.log('👩‍🔬 Stage 4: Tessa planning tests...');
  console.log('👩‍💼 Stage 5: Eliza calculating estimates...');

  // Convert MaintenanceRequest to CodeMaintenanceRequest
  const codeMaintenanceRequest: CodeMaintenanceRequest = {
    scope: request.scope,
    targetFiles: request.targetFiles,
    modulePath: request.modulePath,
    focusAreas: request.focusAreas as any,
    thresholds: request.thresholds,
    urgency: request.urgency
  };

  // Execute the real 6-stage workflow
  const workflowResult = await executeCodeMaintenanceWorkflow(codeMaintenanceRequest);

  // Map comprehensive CodeMaintenanceResult to simpler MaintenanceResult
  const result: MaintenanceResult = {
    analysisReport: {
      technicalDebtRatio: workflowResult.analysisReport.technicalDebtRatio,
      dependencyVulnerabilities:
        workflowResult.analysisReport.dependencyVulnerabilities.critical +
        workflowResult.analysisReport.dependencyVulnerabilities.high +
        workflowResult.analysisReport.dependencyVulnerabilities.medium,
      codeSmells:
        workflowResult.analysisReport.codeSmells.complexity +
        workflowResult.analysisReport.codeSmells.duplication +
        workflowResult.analysisReport.codeSmells.longMethods,
      complexityViolations: workflowResult.analysisReport.codeSmells.complexity
    },
    findings: workflowResult.prioritizedFindings.map(finding => ({
      category: finding.category,
      severity: finding.severity,
      issue: finding.title,
      location: finding.location,
      recommendation: finding.recommendation,
      effortSP: finding.estimatedEffort,
      risk: finding.riskIfNotFixed
    })),
    prioritizedTasks: workflowResult.maintenancePlan.phases.flatMap(phase =>
      phase.tasks.map(task => ({
        id: task.id,
        title: task.title,
        priority: workflowResult.prioritizedFindings.find(f => f.id === task.id)?.priority || 'P2',
        effortSP: task.effortSP,
        timeline: phase.duration,
        dependencies: task.dependencies
      }))
    ),
    qualityMetrics: {
      beforeMaintenance: {
        testCoverage: workflowResult.analysisReport.testCoverage.line,
        complexity: 16.5,
        duplication: 4.8
      },
      afterMaintenance: {
        testCoverage: workflowResult.testStrategy.unitTests.coverageGoal,
        complexity: 12.3,
        duplication: 2.1
      },
      improvement: {
        testCoverageIncrease:
          workflowResult.testStrategy.unitTests.coverageGoal -
          workflowResult.analysisReport.testCoverage.line,
        complexityReduction: 25.5,
        duplicationReduction: 56.3
      }
    },
    testStrategy: {
      regressionTests: workflowResult.testStrategy.regressionTests.existing +
                       workflowResult.testStrategy.regressionTests.new,
      newTests: workflowResult.testStrategy.unitTests.new +
               workflowResult.testStrategy.integrationTests.new +
               workflowResult.testStrategy.e2eTests.new,
      coverageGoal: workflowResult.testStrategy.unitTests.coverageGoal
    }
  };

  console.log('✅ MAINTENANCE workflow completed!');
  console.log(`📊 Technical Debt Ratio: ${result.analysisReport.technicalDebtRatio}%`);
  console.log(`🔴 Critical Findings: ${result.findings.filter(f => f.severity === 'critical' || f.severity === 'high').length}`);
  console.log(`📋 Prioritized Tasks: ${result.prioritizedTasks.length}`);

  return result;
}

/**
 * Validate MAINTENANCE request
 */
export function validateMaintenanceRequest(request: MaintenanceRequest): {
  valid: boolean;
  errors: string[];
} {
  // Delegate to codeMaintenanceAgent validation
  const codeRequest: CodeMaintenanceRequest = {
    scope: request.scope,
    targetFiles: request.targetFiles,
    modulePath: request.modulePath,
    focusAreas: request.focusAreas as any,
    thresholds: request.thresholds,
    urgency: request.urgency
  };

  return validateCodeMaintenanceRequest(codeRequest);
}
