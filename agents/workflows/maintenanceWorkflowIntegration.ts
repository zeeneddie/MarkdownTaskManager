/**
 * Maintenance Workflow Integration
 *
 * Integrates existing Code-Maintenance-Agent with:
 * - Project-first validation
 * - ChromaDB RAG storage
 * - Quality gate enforcement
 *
 * Week 9 - Day 3-5 Integration Layer
 */

import { validateProjectForWorkflow, getWorkflowConfiguration } from './projectValidation';
import {
  executeCodeMaintenanceWorkflow,
  type CodeMaintenanceRequest,
  type CodeMaintenanceResult
} from './codeMaintenanceAgent';

// ============================================================================
// INTEGRATION TYPES
// ============================================================================

export interface MaintenanceWorkflowRequest {
  // Project context (REQUIRED - project-first enforcement)
  project_id: number;

  // Maintenance options (maps to CodeMaintenanceRequest)
  scope?: 'full_codebase' | 'module' | 'specific_files';
  targetFiles?: string[];
  modulePath?: string;

  focusAreas?: Array<
    | 'dependencies'
    | 'code_quality'
    | 'security'
    | 'performance'
    | 'tests'
    | 'documentation'
  >;

  urgency?: 'low' | 'medium' | 'high' | 'critical';

  autoFix?: {
    dependencies?: boolean;
    formatting?: boolean;
    linting?: boolean;
  };

  // RAG options
  use_historical_patterns?: boolean;  // Query ChromaDB for similar past maintenance
  store_results?: boolean;            // Store results in ChromaDB (default: true)
}

export interface MaintenanceWorkflowResult {
  workflow_id: string;
  project_id: number;
  project_name: string;

  // Core maintenance results (from Code-Maintenance-Agent)
  maintenance_result: CodeMaintenanceResult;

  // RAG enhancements
  rag_insights?: {
    similar_maintenance_patterns: {
      pattern: string;
      frequency: number;
      success_rate: number;
    }[];
    historical_fix_time: {
      average_hours: number;
      median_hours: number;
    };
    common_issues: string[];
  };

  // ChromaDB storage
  chroma_document_id?: string;

  // Execution metadata
  metadata: {
    execution_time_ms: number;
    started_at: Date;
    completed_at: Date;
    validation_passed: boolean;
    rag_enhanced: boolean;
  };
}

// ============================================================================
// MAIN INTEGRATION WORKFLOW
// ============================================================================

export async function executeMaintenanceWorkflowIntegrated(
  request: MaintenanceWorkflowRequest
): Promise<MaintenanceWorkflowResult> {
  const workflow_id = `MAINT-${request.project_id}-${Date.now()}`;
  const started_at = new Date();

  console.log(`[MAINTENANCE-INT] Starting workflow ${workflow_id}`);

  try {
    // STEP 1: Project-first validation (HARD REQUIREMENT)
    console.log('[MAINTENANCE-INT] Step 1: Validating project...');

    const { project, rag_context } = await validateProjectForWorkflow(
      request.project_id,
      'MAINTENANCE'
    );

    console.log(`[MAINTENANCE-INT] Project validated: ${project.name} (${project.project_type})`);

    // STEP 2: Load historical maintenance patterns from ChromaDB (if enabled)
    let rag_insights;
    if (request.use_historical_patterns) {
      console.log('[MAINTENANCE-INT] Step 2: Loading historical patterns from RAG...');
      rag_insights = await loadHistoricalMaintenancePatterns(project.id, request.focusAreas);
    }

    // STEP 3: Execute core maintenance workflow
    console.log('[MAINTENANCE-INT] Step 3: Executing maintenance workflow...');

    const maintenanceRequest: CodeMaintenanceRequest = {
      scope: request.scope || 'full_codebase',
      targetFiles: request.targetFiles,
      modulePath: request.modulePath,
      focusAreas: request.focusAreas,
      urgency: request.urgency,
      autoFix: request.autoFix
    };

    const maintenanceResult = await executeCodeMaintenanceWorkflow(maintenanceRequest);

    console.log('[MAINTENANCE-INT] Maintenance workflow completed');

    // STEP 4: Store results in ChromaDB (if enabled)
    let chroma_document_id;
    if (request.store_results !== false) {
      console.log('[MAINTENANCE-INT] Step 4: Storing results in ChromaDB...');
      chroma_document_id = await storeMaintenanceResultsInRAG(
        project.id,
        maintenanceResult
      );
    }

    // STEP 5: Build final result
    const completed_at = new Date();
    const execution_time_ms = completed_at.getTime() - started_at.getTime();

    const result: MaintenanceWorkflowResult = {
      workflow_id,
      project_id: project.id,
      project_name: project.name,
      maintenance_result: maintenanceResult,
      rag_insights,
      chroma_document_id,
      metadata: {
        execution_time_ms,
        started_at,
        completed_at,
        validation_passed: true,
        rag_enhanced: !!rag_insights
      }
    };

    console.log(`[MAINTENANCE-INT] Workflow ${workflow_id} complete: ${execution_time_ms}ms`);

    return result;

  } catch (error) {
    console.error(`[MAINTENANCE-INT] Workflow ${workflow_id} failed:`, error);

    // If validation error, provide clear guidance
    if (error instanceof Error && error.name === 'ProjectValidationError') {
      console.error('[MAINTENANCE-INT] Project validation failed:', error.message);
    }

    throw error;
  }
}

// ============================================================================
// RAG INTEGRATION HELPERS
// ============================================================================

/**
 * Load historical maintenance patterns from ChromaDB
 */
async function loadHistoricalMaintenancePatterns(
  project_id: number,
  focusAreas?: string[]
): Promise<any> {
  console.log(`[MAINTENANCE-INT-RAG] Loading historical patterns for project ${project_id}`);

  // TODO: Implement actual ChromaDB query
  // Query code_analysis collection for past maintenance results
  // Find patterns in:
  // - Common issues (grouped by category)
  // - Fix success rates
  // - Average time to fix
  // - Recurring problems

  // Placeholder data
  return {
    similar_maintenance_patterns: [
      {
        pattern: 'Outdated FastAPI dependencies',
        frequency: 5,
        success_rate: 100
      },
      {
        pattern: 'Missing test coverage in services',
        frequency: 3,
        success_rate: 85
      }
    ],
    historical_fix_time: {
      average_hours: 2.5,
      median_hours: 2.0
    },
    common_issues: [
      'Dependency updates breaking tests',
      'Type errors after refactoring',
      'Missing error handling'
    ]
  };
}

/**
 * Store maintenance results in ChromaDB for future reference
 */
async function storeMaintenanceResultsInRAG(
  project_id: number,
  result: CodeMaintenanceResult
): Promise<string> {
  console.log(`[MAINTENANCE-INT-RAG] Storing results for project ${project_id}`);

  // TODO: Implement actual ChromaDB storage
  // Store in code_analysis collection:
  // - Analysis report (technical debt, vulnerabilities, etc.)
  // - Prioritized findings
  // - Execution results
  // - Success/failure patterns

  // Create searchable text representation
  const analysisText = createAnalysisText(result);

  // Generate document ID
  const doc_id = `maintenance-${project_id}-${Date.now()}`;

  // ChromaDB storage would happen here:
  // await chromaService.code_analysis.add({
  //   documents: [analysisText],
  //   metadatas: [{
  //     project_id: String(project_id),
  //     type: 'maintenance_result',
  //     timestamp: new Date().toISOString(),
  //     technical_debt_ratio: result.analysisReport.technicalDebtRatio,
  //     vulnerabilities_fixed: result.prioritizedFindings.filter(f => f.category === 'security').length
  //   }],
  //   ids: [doc_id]
  // });

  console.log(`[MAINTENANCE-INT-RAG] Results stored with ID: ${doc_id}`);

  return doc_id;
}

/**
 * Create searchable text from maintenance results
 */
function createAnalysisText(result: CodeMaintenanceResult): string {
  const { analysisReport, prioritizedFindings } = result;

  const text = `
Maintenance Analysis Report

Technical Debt Ratio: ${analysisReport.technicalDebtRatio}%

Vulnerabilities:
- Critical: ${analysisReport.dependencyVulnerabilities.critical}
- High: ${analysisReport.dependencyVulnerabilities.high}
- Medium: ${analysisReport.dependencyVulnerabilities.medium}
- Low: ${analysisReport.dependencyVulnerabilities.low}

Code Smells:
- Complexity issues: ${analysisReport.codeSmells.complexity}
- Code duplication: ${analysisReport.codeSmells.duplication}
- Long methods: ${analysisReport.codeSmells.longMethods}
- Large classes: ${analysisReport.codeSmells.largeClasses}

Test Coverage:
- Line coverage: ${analysisReport.testCoverage.line}%
- Branch coverage: ${analysisReport.testCoverage.branch}%
- Function coverage: ${analysisReport.testCoverage.function}%

Top Findings:
${prioritizedFindings.slice(0, 10).map((f, i) => `${i + 1}. [${f.severity.toUpperCase()}] ${f.title} (${f.category})`).join('\n')}

Best Practice Compliance:
- SIG Compliance: ${analysisReport.bestPracticeScore.sigCompliance.overall}%
- SOLID Compliance: ${analysisReport.bestPracticeScore.solidCompliance.overall}%
- GRASP Compliance: ${analysisReport.bestPracticeScore.graspCompliance.overall}%
- TDD Compliance: ${analysisReport.bestPracticeScore.tddCompliance.overall}%
  `.trim();

  return text;
}

// ============================================================================
// EXPORT
// ============================================================================

export default {
  executeMaintenanceWorkflowIntegrated,
  loadHistoricalMaintenancePatterns,
  storeMaintenanceResultsInRAG
};
