/**
 * PROJECT_DEFINITION Workflow
 *
 * This workflow defines a complete new project from scratch:
 * 1. Peter (Product Owner) - Business case & scope
 * 2. Felix (Feature Architect) - Architecture vision
 * 3. Peter (Product Owner) - Epic breakdown
 * 4. Eliza (Estimation Engine) - Effort estimates
 * 5. Paul (Project Lead) - Project plan & sprints
 * 6. Diana (Documentation Writer) - Complete docs
 *
 * Result: Complete project definition with folder structure
 */

import { Task, Team } from 'kaibanjs';
import { agents } from '../configs/agents';

export interface ProjectDefinitionRequest {
  projectName: string;
  description: string;
  businessGoals?: string[];
  targetAudience?: string;
  constraints?: string[];
  folderPath?: string;
}

export interface ProjectDefinitionResult {
  project: {
    name: string;
    vision: string;
    businessCase: {
      value: string;
      roi: string;
      risks: string[];
    };
    scope: {
      included: string[];
      excluded: string[];
      constraints: string[];
    };
  };
  architecture: {
    techStack: string[];
    patterns: string[];
    infrastructure: string[];
    securityConsiderations: string[];
  };
  epics: Array<{
    id: string;
    title: string;
    description: string;
    businessValue: string;
    acceptanceCriteria: string[];
    estimatedEffort: number;
  }>;
  projectPlan: {
    phases: Array<{
      name: string;
      duration: string;
      milestones: string[];
    }>;
    sprints: Array<{
      number: number;
      goal: string;
      epics: string[];
      capacity: number;
    }>;
    timeline: string;
    risks: Array<{
      description: string;
      impact: string;
      mitigation: string;
    }>;
  };
  documentation: {
    readme: string;
    setupGuide: string;
    contributingGuide: string;
    architecture: string;
  };
  folderStructure: {
    created: boolean;
    path: string;
    files: string[];
  };
}

/**
 * Execute PROJECT_DEFINITION workflow
 *
 * Now uses Spec-Kit workflow instead of mock data:
 * Constitution → Specification → Tasks
 */
export async function executeProjectDefinitionWorkflow(
  request: ProjectDefinitionRequest
): Promise<ProjectDefinitionResult> {
  console.log('🚀 Starting PROJECT_DEFINITION workflow...');
  console.log(`   Project: ${request.projectName}`);

  // Import Spec-Kit workflow
  const { executeSpecKitWorkflow } = await import('./specKitWorkflow');

  // Convert ProjectDefinitionRequest to SpecKitWorkflowInput
  const specKitInput = {
    businessCase: request.description,
    stakeholders: ['Product Owner', 'Development Team', 'End Users'],
    constraints: request.constraints || [
      'Timeline: 6 months',
      'Team size: 5 developers'
    ],
    successCriteria: request.businessGoals || [
      'Deliver MVP within timeline',
      'Meet user requirements',
      'Maintain code quality standards'
    ],
    technicalContext: {
      existingSystems: [],
      technologies: [],
      teamSize: 5,
      timeline: '6 months'
    },
    projectPath: request.folderPath,
    projectName: request.projectName
  };

  // Execute Spec-Kit workflow
  const specKitResult = await executeSpecKitWorkflow(specKitInput);

  // Transform Spec-Kit result to ProjectDefinitionResult format
  const constitution = specKitResult.constitution;
  const specification = specKitResult.specification;
  const tasks = specKitResult.tasks;

  const result: ProjectDefinitionResult = {
    project: {
      name: request.projectName,
      vision: (constitution.principles?.[0] as any)?.statement || `Project vision for ${request.projectName}`,
      businessCase: {
        value: Array.isArray(constitution.requirements) && constitution.requirements.length > 0
          ? (constitution.requirements[0] as any).description || 'Primary business value'
          : 'Primary business value',
        roi: 'Expected ROI based on constitution analysis',
        risks: constitution.risks?.map((r: any) => r.description || r.risk || 'Risk identified') || []
      },
      scope: {
        included: constitution.scope?.inScope || [],
        excluded: constitution.scope?.outScope || [],  // Note: outScope not outOfScope
        constraints: constitution.constraints?.map((c: any) => c.description || c.constraint || String(c)) || request.constraints || []
      }
    },
    architecture: {
      techStack: Array.isArray((specification.architecture as any)?.technologies)
        ? (specification.architecture as any).technologies
        : specification.architecture?.technologies
          ? Object.values(specification.architecture.technologies).flat()
          : ['Backend: FastAPI (Python)', 'Frontend: Vue.js 3', 'Database: PostgreSQL'],
      patterns: specification.architecture?.pattern
        ? [String(specification.architecture.pattern)]
        : ['RESTful API architecture', 'Repository pattern'],
      infrastructure: ['Development: Docker Compose', 'Production: Cloud deployment'],
      securityConsiderations: (specification as any).qualityAttributes?.security || [
        'HTTPS only',
        'OWASP Top 10 compliance'
      ]
    },
    epics: tasks.epics?.map((epic: any, index: number) => ({
      id: epic.id || `EPIC-${index + 1}`,
      title: epic.title || `Epic ${index + 1}`,
      description: epic.description || '',
      businessValue: epic.businessValue || 'Delivers core project value',
      acceptanceCriteria: epic.acceptanceCriteria || [],
      estimatedEffort: 0  // TBD - Team must estimate with Planning Poker
    })) || [],
    projectPlan: {
      phases: [
        {
          name: 'Phase 1: Foundation',
          duration: '4-6 weeks',
          milestones: ['Development environment ready', 'Database schema finalized']
        },
        {
          name: 'Phase 2: Core Development',
          duration: '10-14 weeks',
          milestones: ['All epics completed', 'Integration tests passing']
        },
        {
          name: 'Phase 3: Launch Preparation',
          duration: '3-4 weeks',
          milestones: ['User acceptance testing complete', 'Production deployment successful']
        }
      ],
      sprints: tasks.epics?.map((epic: any, index: number) => ({
        number: index + 1,
        goal: epic.title || `Sprint ${index + 1} goal`,
        epics: [epic.id || `EPIC-${index + 1}`],
        capacity: 40  // Default capacity - team should adjust
      })) || [],
      timeline: request.constraints?.find((c: string) => c.toLowerCase().includes('timeline')) || '6 months',
      risks: constitution.risks?.map((risk: any) => ({
        description: risk.description || risk,
        impact: risk.impact || 'Medium',
        mitigation: risk.mitigation || 'To be determined by team'
      })) || []
    },
    documentation: {
      readme: specKitResult.files.find((f: any) => f.filename === 'README.md')?.content ||
        `# ${request.projectName}\n\n${request.description}`,
      setupGuide: `# Setup Guide\n\nGenerated from Spec-Kit workflow\n\nRefer to README.md for complete setup instructions.`,
      contributingGuide: `# Contributing Guide\n\nPlease refer to project documentation for contribution guidelines.`,
      architecture: specKitResult.files.find((f: any) => f.filename === 'specification.md')?.content ||
        `# Architecture\n\nRefer to specification.md for detailed architecture documentation.`
    },
    folderStructure: {
      created: specKitResult.files.length > 0,
      path: request.folderPath || `projects/${request.projectName.toLowerCase().replace(/\s+/g, '-')}`,
      files: specKitResult.files.map((f: any) => f.filename)
    }
  };

  console.log(`✅ PROJECT_DEFINITION workflow completed for: ${request.projectName}`);
  console.log(`   Epics generated: ${result.epics.length}`);
  console.log(`   Files generated: ${result.folderStructure.files.length}`);

  return result;
}

/**
 * Validation for project definition requests
 */
export function validateProjectDefinitionRequest(
  request: ProjectDefinitionRequest
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!request.projectName || request.projectName.trim().length === 0) {
    errors.push('Project name is required');
  }

  if (!request.description || request.description.trim().length === 0) {
    errors.push('Project description is required');
  }

  if (request.projectName && request.projectName.length > 100) {
    errors.push('Project name must be less than 100 characters');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
