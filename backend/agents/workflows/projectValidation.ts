/**
 * Project Validation Module
 *
 * Enforces project-first workflow - all workflows require an active project with BMAD session.
 *
 * Validation Flow:
 * 1. Check project exists
 * 2. Check project is active
 * 3. Check BMAD session exists
 * 4. For brownfield: check quality scan exists
 * 5. Load RAG context for workflow enhancement
 *
 * Errors provide clear next actions for user.
 */

export interface WorkflowValidationError extends Error {
  code: string;
  message: string;
  current_status?: string;
  project_type?: string;
  suggested_workflow?: string;
  next_action: string;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  project_type: 'greenfield' | 'brownfield';
  project_status: 'draft' | 'active' | 'archived';
  bmad_session_id: string | null;
  quality_scan_id: string | null;
  chroma_collection_id: string | null;
  tech_stack?: string[];
  architecture_pattern?: string;
  created_at: Date;
  updated_at: Date;
}

export interface RAGContext {
  project_knowledge: {
    content: string;
    similarity: number;
    metadata: any;
  }[];
  similar_projects: {
    project_id: number;
    project_name: string;
    similarity: number;
    shared_patterns: string[];
  }[];
  bmad_session: {
    session_id: string;
    content: string;
    metadata: any;
  } | null;
  quality_scan: {
    scan_id: string;
    overall_score: number;
    content: string;
  } | null;
}

export class ProjectValidationError extends Error implements WorkflowValidationError {
  code: string;
  current_status?: string;
  project_type?: string;
  suggested_workflow?: string;
  next_action: string;

  constructor(params: {
    code: string;
    message: string;
    current_status?: string;
    project_type?: string;
    suggested_workflow?: string;
    next_action: string;
  }) {
    super(params.message);
    this.name = 'ProjectValidationError';
    this.code = params.code;
    this.current_status = params.current_status;
    this.project_type = params.project_type;
    this.suggested_workflow = params.suggested_workflow;
    this.next_action = params.next_action;
  }
}

/**
 * Validate project exists and is valid for workflow execution
 */
export async function validateProjectForWorkflow(
  projectId: number | undefined,
  workType: string
): Promise<{ project: Project; rag_context: RAGContext }> {
  // STEP 1: Validate project ID provided
  if (!projectId) {
    throw new ProjectValidationError({
      code: 'PROJECT_REQUIRED',
      message: 'Please select or create a project first',
      next_action: 'redirect_to_project_selection',
    });
  }

  // STEP 2: Get project from database
  // TODO: Replace with actual database call
  const project = await getProjectFromDatabase(projectId);

  if (!project) {
    throw new ProjectValidationError({
      code: 'PROJECT_NOT_FOUND',
      message: `Project ${projectId} not found`,
      next_action: 'redirect_to_project_selection',
    });
  }

  // STEP 3: Validate project status
  if (project.project_status !== 'active') {
    const suggested_workflow =
      project.project_type === 'greenfield'
        ? 'GREEN_PAPER_PROJECT'
        : 'BROWN_PAPER_PROJECT';

    throw new ProjectValidationError({
      code: 'PROJECT_NOT_ACTIVE',
      message: `Project must be active. Current status: ${project.project_status}`,
      current_status: project.project_status,
      suggested_workflow,
      next_action:
        project.project_status === 'draft'
          ? 'complete_project_definition'
          : 'contact_admin',
    });
  }

  // STEP 4: Validate BMAD session (required for all projects)
  if (!project.bmad_session_id) {
    const workflow_type =
      project.project_type === 'greenfield'
        ? 'GREEN_PAPER_PROJECT'
        : 'BROWN_PAPER_PROJECT';

    throw new ProjectValidationError({
      code: 'BMAD_SESSION_REQUIRED',
      message: 'BMAD session required before starting workflows',
      project_type: project.project_type,
      suggested_workflow: workflow_type,
      next_action: 'start_bmad_session',
    });
  }

  // STEP 5: Brownfield-specific validation (quality scan required)
  if (project.project_type === 'brownfield' && !project.quality_scan_id) {
    throw new ProjectValidationError({
      code: 'QUALITY_SCAN_REQUIRED',
      message: 'Quality scan required for brownfield projects',
      project_type: 'brownfield',
      next_action: 'start_quality_scan',
    });
  }

  // STEP 6: Load RAG context (enhance workflow with historical data)
  const rag_context = await loadRAGContext(project, workType);

  return { project, rag_context };
}

/**
 * Get project from database
 * TODO: Implement actual PostgreSQL query
 */
async function getProjectFromDatabase(projectId: number): Promise<Project | null> {
  // Placeholder implementation
  // In real implementation, this would query PostgreSQL
  console.log(`[ProjectValidation] Getting project ${projectId} from database`);

  // For now, return null to indicate not found
  // Real implementation:
  // const result = await pool.query('SELECT * FROM projects WHERE id = $1', [projectId]);
  // return result.rows[0] || null;

  return null;
}

/**
 * Load RAG context for workflow enhancement
 */
async function loadRAGContext(
  project: Project,
  workType: string
): Promise<RAGContext> {
  console.log(`[ProjectValidation] Loading RAG context for project ${project.id}, work type: ${workType}`);

  // TODO: Implement actual ChromaDB queries
  // For now, return empty context
  return {
    project_knowledge: [],
    similar_projects: [],
    bmad_session: null,
    quality_scan: null,
  };

  // Real implementation would:
  // 1. Query project documents from ChromaDB
  // 2. Find similar historical projects
  // 3. Load BMAD session content
  // 4. Load quality scan if brownfield
}

/**
 * Get workflow configuration based on project validation
 */
export function getWorkflowConfiguration(
  project: Project,
  rag_context: RAGContext,
  workType: string
) {
  return {
    project_id: project.id,
    project_name: project.name,
    project_type: project.project_type,
    work_type: workType,
    context: {
      bmad_session: rag_context.bmad_session,
      quality_scan: rag_context.quality_scan,
      similar_projects: rag_context.similar_projects,
      project_knowledge: rag_context.project_knowledge.slice(0, 5), // Top 5 most relevant
    },
    constraints: {
      tech_stack: project.tech_stack || [],
      architecture_pattern: project.architecture_pattern || 'undefined',
    },
  };
}

/**
 * Export validation function for use in workflow router
 */
export default {
  validateProjectForWorkflow,
  getWorkflowConfiguration,
  ProjectValidationError,
};
