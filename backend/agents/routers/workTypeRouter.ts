/**
 * Work Type Router
 *
 * Classifies incoming requests into work types and routes them
 * to the appropriate agent team with the correct workflow.
 */

import { agents } from '../configs/agents';
import { Agent } from 'kaibanjs';

export enum WorkType {
  PROJECT_DEFINITION = 'PROJECT_DEFINITION',
  NEW_FEATURE = 'NEW_FEATURE',
  MAINTENANCE = 'MAINTENANCE',
  QUALITY_AUDIT = 'QUALITY_AUDIT',
  BUG = 'BUG',
  ENHANCEMENT = 'ENHANCEMENT',
  MIGRATION = 'MIGRATION',
  QUALITY_IMPROVEMENT = 'QUALITY_IMPROVEMENT',
  TESTING = 'TESTING'
}

export interface WorkRequest {
  description: string;
  workType?: WorkType;
  context?: Record<string, any>;
}

export interface TeamConfiguration {
  agents: Agent[];
  process: 'sequential' | 'parallel';
  workflow: string;
}

/**
 * Work Type to Agent Team Mapping
 * Defines which agents are assigned to each work type
 */
export const WORK_TYPE_TEAMS: Record<WorkType, TeamConfiguration> = {
  [WorkType.PROJECT_DEFINITION]: {
    agents: [
      agents.productOwner,      // 1. Business case, scope, stakeholders
      agents.featureArchitect,  // 2. Architecture vision, tech stack
      agents.productOwner,      // 3. Epic breakdown from business goals
      agents.estimationEngine,  // 4. Effort estimation per epic
      agents.projectLead,       // 5. Project plan, sprints, milestones
      agents.documentationWriter // 6. Complete project documentation
    ],
    process: 'sequential',
    workflow: 'project_setup_pipeline'
  },

  [WorkType.NEW_FEATURE]: {
    agents: [
      agents.featureArchitect,
      agents.estimationEngine,
      agents.testEngineer,
      agents.qualityInspector,
      agents.documentationWriter
    ],
    process: 'sequential',
    workflow: 'spec_kit_pipeline'
  },

  [WorkType.MAINTENANCE]: {
    agents: [
      agents.maintenanceSpecialist,
      agents.qualityInspector,
      agents.testEngineer,
      agents.estimationEngine
    ],
    process: 'sequential',
    workflow: 'code_maintenance_6_stage'
  },

  [WorkType.QUALITY_AUDIT]: {
    agents: [
      agents.qualityInspector,
      agents.maintenanceSpecialist,
      agents.testEngineer
    ],
    process: 'parallel',
    workflow: 'superclaude_audit'
  },

  [WorkType.BUG]: {
    agents: [
      agents.bugHunter,
      agents.testEngineer,
      agents.documentationWriter
    ],
    process: 'sequential',
    workflow: 'bug_fix_5_stage'
  },

  [WorkType.ENHANCEMENT]: {
    agents: [
      agents.featureArchitect,
      agents.maintenanceSpecialist,
      agents.estimationEngine,
      agents.testEngineer
    ],
    process: 'sequential',
    workflow: 'enhancement_hybrid'
  },

  [WorkType.MIGRATION]: {
    agents: [
      agents.migrationArchitect,
      agents.qualityInspector,
      agents.estimationEngine,
      agents.testEngineer,
      agents.documentationWriter
    ],
    process: 'sequential',  // Will use hybrid in actual workflow
    workflow: 'migration_5_stage'
  },

  [WorkType.QUALITY_IMPROVEMENT]: {
    agents: [
      agents.qualityInspector,
      agents.maintenanceSpecialist,
      agents.testEngineer,
      agents.estimationEngine
    ],
    process: 'sequential',
    workflow: 'quality_improvement_5_stage'
  },

  [WorkType.TESTING]: {
    agents: [
      agents.testEngineer,
      agents.qualityInspector,
      agents.documentationWriter
    ],
    process: 'sequential',
    workflow: 'test_generation_4_track'
  }
};

/**
 * Classification keywords for automatic work type detection
 */
const CLASSIFICATION_KEYWORDS: Record<WorkType, string[]> = {
  [WorkType.PROJECT_DEFINITION]: [
    'project', 'define project', 'new project', 'start project',
    'project setup', 'initialize', 'product vision', 'business case',
    'project charter', 'project plan', 'roadmap'
  ],
  [WorkType.NEW_FEATURE]: [
    'add', 'create', 'new', 'implement', 'build', 'develop',
    'feature', 'functionality', 'capability'
  ],
  [WorkType.MAINTENANCE]: [
    'update', 'upgrade', 'dependency', 'maintenance', 'refactor',
    'clean', 'organize', 'deprecate'
  ],
  [WorkType.QUALITY_AUDIT]: [
    'audit', 'review', 'analyze', 'inspect', 'check', 'quality',
    'security', 'performance', 'assessment'
  ],
  [WorkType.BUG]: [
    'bug', 'fix', 'error', 'issue', 'problem', 'crash', 'fails',
    'broken', 'not working', 'doesn\'t work'
  ],
  [WorkType.ENHANCEMENT]: [
    'improve', 'enhance', 'better', 'optimize', 'extend',
    'expand', 'modify', 'adjust'
  ],
  [WorkType.MIGRATION]: [
    'migrate', 'migration', 'move', 'transfer', 'upgrade to',
    'switch to', 'port', 'convert'
  ],
  [WorkType.QUALITY_IMPROVEMENT]: [
    'technical debt', 'code smell', 'complexity', 'duplication',
    'coverage', 'cleanup', 'improve quality'
  ],
  [WorkType.TESTING]: [
    'test', 'testing', 'unit test', 'integration test', 'e2e',
    'test coverage', 'test scenario'
  ]
};

/**
 * Classify work type based on description
 * Uses keyword matching with scoring
 */
export function classifyWorkType(description: string): WorkType {
  const lowerDesc = description.toLowerCase();
  const scores: Partial<Record<WorkType, number>> = {};

  // Calculate scores for each work type
  for (const [workType, keywords] of Object.entries(CLASSIFICATION_KEYWORDS)) {
    scores[workType as WorkType] = keywords.filter(keyword =>
      lowerDesc.includes(keyword)
    ).length;
  }

  // Find work type with highest score
  const sorted = Object.entries(scores)
    .sort(([, a], [, b]) => (b || 0) - (a || 0));

  const topMatch = sorted[0];

  if (topMatch && topMatch[1] > 0) {
    return topMatch[0] as WorkType;
  }

  // Default to NEW_FEATURE if no clear match
  return WorkType.NEW_FEATURE;
}

/**
 * Get team configuration for a work type
 */
export function getTeamConfiguration(workType: WorkType): TeamConfiguration {
  return WORK_TYPE_TEAMS[workType];
}

/**
 * Route work request to appropriate team
 */
export function routeWorkRequest(request: WorkRequest): {
  workType: WorkType;
  teamConfig: TeamConfiguration;
} {
  // Use provided work type or classify automatically
  const workType = request.workType || classifyWorkType(request.description);
  const teamConfig = getTeamConfiguration(workType);

  return {
    workType,
    teamConfig
  };
}

/**
 * Validate work request
 */
export function validateWorkRequest(request: WorkRequest): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!request.description || request.description.trim().length === 0) {
    errors.push('Description is required');
  }

  if (request.description && request.description.length < 10) {
    errors.push('Description must be at least 10 characters');
  }

  if (request.workType && !Object.values(WorkType).includes(request.workType)) {
    errors.push(`Invalid work type: ${request.workType}`);
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
