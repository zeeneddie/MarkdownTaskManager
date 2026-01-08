/**
 * SPEC-KIT WORKFLOW
 *
 * Complete end-to-end pipeline from business case to executable tasks.
 *
 * Pipeline: Business Case → Constitution → Specification → Tasks
 *
 * Agents:
 * 1. Peter (Product Owner) - Executes /constitution
 * 2. Felix (Feature Architect) - Executes /specify
 * 3. Felix (Feature Architect) - Executes /tasks
 * 4. Diana (Documentation Writer) - Formats output
 *
 * Output:
 * - constitution.md
 * - specification.md
 * - tasks.md (with Planning Poker guide)
 * - metadata.json
 *
 * Usage: New projects, major features, RFPs, migration planning
 */

import { Agent } from 'kaibanjs';
import { agents } from '../configs/agents';
import {
  ConstitutionInput,
  ConstitutionResult,
  SpecificationInput,
  SpecificationResult,
  TaskGenerationInput,
  TaskGenerationResult,
  SpecKitWorkflowResult,
  GeneratedFile,
  WorkflowSummary,
  DevelopmentStack,
  OperationalStack
} from '../types/SpecKit';
import {
  executeConstitution,
  formatConstitutionMarkdown
} from '../commands/constitutionCommand';
import {
  executeSpecification,
  formatSpecificationMarkdown
} from '../commands/specifyCommand';
import {
  executeTasks,
  formatTasksMarkdown
} from '../commands/tasksCommand';
import {
  executeArchitectureReview,
  formatArchitectureReviewMarkdown
} from '../commands/architectReviewCommand';
import {
  ArchitectureReviewInput,
  ArchitectureReviewResult,
  ReviewVerdict,
  HumanApprovalRequest,
  ArchitectureReviewConfig
} from '../types/SpecKit';

/**
 * Input for Spec-Kit workflow
 */
export interface SpecKitWorkflowInput {
  /** Business case description */
  businessCase: string;

  /** Project stakeholders */
  stakeholders: string[];

  /** Project constraints */
  constraints: string[];

  /** Success criteria */
  successCriteria: string[];

  /** Technical context (optional) */
  technicalContext?: {
    existingSystems?: string[];
    technologies?: string[];
    teamSize?: number;
    timeline?: string;
  };

  /**
   * Development stack from Green Paper session (Week 10 enhancement)
   * Languages, frameworks, databases, testing, dev tools
   */
  developmentStack?: DevelopmentStack;

  /**
   * Operational stack from Green Paper session (Week 10 enhancement)
   * Hosting, CI/CD, monitoring, security
   */
  operationalStack?: OperationalStack;

  /**
   * Green Paper constraints for architecture review
   */
  greenPaperConstraints?: {
    budget?: string;
    timeline?: string;
    technology?: string[];
    resources?: string;
    regulatory?: string[];
  };

  /**
   * Team context for architecture review
   */
  teamContext?: {
    size: number;
    skills: string[];
    experience: 'junior' | 'mid' | 'senior' | 'mixed';
  };

  /**
   * Enable architecture review phase (default: true)
   */
  enableArchitectureReview?: boolean;

  /**
   * Architecture review configuration (thresholds for approval)
   * Default: 95% alignment required, no high-importance gaps
   */
  reviewConfig?: ArchitectureReviewConfig;

  /** Project folder path for file generation */
  projectPath?: string;

  /** Project name for file naming */
  projectName?: string;
}

/**
 * Execute complete Spec-Kit workflow
 *
 * This orchestrates the 3-stage pipeline:
 * 1. Constitution generation (Peter)
 * 2. Specification generation (Felix)
 * 3. Task generation (Felix)
 * 4. File generation (Diana)
 */
export async function executeSpecKitWorkflow(
  input: SpecKitWorkflowInput
): Promise<SpecKitWorkflowResult> {
  console.log('🚀 Starting Spec-Kit Workflow...');
  console.log(`   Business Case: ${input.businessCase.substring(0, 80)}...`);

  const workflowStartTime = Date.now();

  // ============================================================================
  // STAGE 1: CONSTITUTION GENERATION (Peter - Product Owner)
  // ============================================================================
  console.log('\n📋 STAGE 1/5: Constitution Generation');
  console.log('   Agent: Peter (Product Owner)');

  const constitutionStartTime = Date.now();

  const constitutionInput: ConstitutionInput = {
    businessCase: input.businessCase,
    stakeholders: input.stakeholders,
    constraints: input.constraints,
    successCriteria: input.successCriteria,
    technicalContext: input.technicalContext
  };

  const constitution = await executeConstitution(
    constitutionInput,
    agents.productOwner
  );

  const constitutionTime = Date.now() - constitutionStartTime;
  console.log(`   ✓ Constitution complete (${constitutionTime}ms)`);
  console.log(`     - ${constitution.principles.length} principles`);
  console.log(`     - ${constitution.requirements.length} requirements`);
  console.log(`     - ${constitution.constraints.length} constraints`);
  console.log(`     - ${constitution.risks.length} risks`);

  // ============================================================================
  // STAGE 2: SPECIFICATION GENERATION (Felix - Feature Architect)
  // ============================================================================
  console.log('\n🏗️  STAGE 2/5: Specification Generation');
  console.log('   Agent: Felix (Feature Architect)');

  const specificationStartTime = Date.now();

  const specificationInput: SpecificationInput = {
    constitution: constitution,
    technicalContext: {
      technologies: input.technicalContext?.technologies,
      existingSystems: input.technicalContext?.existingSystems,
      team: input.technicalContext?.teamSize ? {
        size: input.technicalContext.teamSize,
        skills: [] // Will be inferred by Felix
      } : undefined
    },
    // Pass Green Paper stacks for enhanced architecture generation
    developmentStack: input.developmentStack,
    operationalStack: input.operationalStack
  };

  const specification = await executeSpecification(
    specificationInput,
    agents.featureArchitect
  );

  const specificationTime = Date.now() - specificationStartTime;
  console.log(`   ✓ Specification complete (${specificationTime}ms)`);
  console.log(`     - Architecture: ${specification.architecture.pattern}`);
  console.log(`     - ${specification.components.length} components`);
  console.log(`     - ${specification.interfaces.length} API endpoints`);
  console.log(`     - ${specification.dataModel.entities.length} entities`);

  // ============================================================================
  // STAGE 3: ARCHITECTURE REVIEW (Felix - Feature Architect) [BMAD-inspired]
  // ============================================================================
  let architectureReview: ArchitectureReviewResult | undefined;
  let reviewTime = 0;

  if (input.enableArchitectureReview !== false) {
    console.log('\n🔍 STAGE 3/5: Architecture Review (BMAD-inspired)');
    console.log('   Agent: Felix (Feature Architect)');
    console.log('   Validating architecture against constitution...');

    const reviewStartTime = Date.now();

    const reviewInput: ArchitectureReviewInput = {
      constitution,
      specification,
      greenPaperConstraints: input.greenPaperConstraints,
      teamContext: input.teamContext,
      reviewConfig: input.reviewConfig
    };

    architectureReview = await executeArchitectureReview(
      reviewInput,
      agents.featureArchitect
    );

    reviewTime = Date.now() - reviewStartTime;
    console.log(`   ✓ Architecture review complete (${reviewTime}ms)`);
    console.log(`     - Verdict: ${architectureReview.verdict}`);
    console.log(`     - Alignment Score: ${architectureReview.alignmentScore}%`);
    console.log(`     - ADRs Generated: ${architectureReview.adrs.length}`);
    console.log(`     - Risks Identified: ${architectureReview.risks.length}`);

    // Check if we should proceed
    if (architectureReview.verdict === ReviewVerdict.REJECTED) {
      console.log('\n⚠️  Architecture REJECTED - stopping workflow');
      console.log('   Review the requiredRevisions and update the specification.');
      // Return early with partial results
      return {
        constitution,
        specification,
        architectureReview,
        tasks: { epics: [], features: [], stories: [], tasks: [], estimations: {} as any, metadata: {} as any },
        files: generateFiles(constitution, specification, { epics: [], features: [], stories: [], tasks: [], estimations: {} as any, metadata: {} as any }, input, architectureReview),
        summary: {
          executionTime: Date.now() - workflowStartTime,
          constitutionTime,
          specificationTime,
          reviewTime,
          taskGenerationTime: 0,
          filesGenerated: 0,
          totalEpics: 0,
          totalFeatures: 0,
          totalStories: 0,
          estimatedWeeks: 0,
          reviewVerdict: architectureReview.verdict,
          alignmentScore: architectureReview.alignmentScore
        }
      };
    }

    if (architectureReview.verdict === ReviewVerdict.NEEDS_REVISION) {
      console.log('\n⚠️  Architecture NEEDS REVISION - proceeding with warnings');
      console.log('   Required revisions:');
      architectureReview.requiredRevisions?.forEach((rev, i) => {
        console.log(`     ${i + 1}. ${rev}`);
      });
    }

    // Handle NEEDS_HUMAN_APPROVAL - blocking factor requiring human intervention
    // Triggered when: alignment < 95%, high-importance gaps, or too many high risks
    if (architectureReview.verdict === ReviewVerdict.NEEDS_HUMAN_APPROVAL) {
      console.log('\n⛔ Architecture NEEDS HUMAN APPROVAL - workflow paused');
      console.log('   Reason: Alignment score below 95% or high-importance gaps detected');
      console.log('   This is a BLOCKING FACTOR - cannot proceed without human approval');

      if (architectureReview.humanApprovalRequest) {
        console.log(`\n   Human Approval Request:`);
        console.log(`     Request ID: ${architectureReview.humanApprovalRequest.requestId}`);
        console.log(`     Reason: ${architectureReview.humanApprovalRequest.reason}`);
        console.log(`     Decisions Required: ${architectureReview.humanApprovalRequest.decisionsRequired.length}`);
        architectureReview.humanApprovalRequest.decisionsRequired.forEach((decision, i) => {
          console.log(`       ${i + 1}. [${decision.category}] ${decision.title}`);
        });
      }

      // Return early with partial results - workflow paused awaiting human approval
      return {
        constitution,
        specification,
        architectureReview,
        tasks: { epics: [], features: [], stories: [], tasks: [], estimations: {} as any, metadata: {} as any },
        files: generateFiles(constitution, specification, { epics: [], features: [], stories: [], tasks: [], estimations: {} as any, metadata: {} as any }, input, architectureReview),
        summary: {
          executionTime: Date.now() - workflowStartTime,
          constitutionTime,
          specificationTime,
          reviewTime,
          taskGenerationTime: 0,
          filesGenerated: 0,
          totalEpics: 0,
          totalFeatures: 0,
          totalStories: 0,
          estimatedWeeks: 0,
          reviewVerdict: architectureReview.verdict,
          alignmentScore: architectureReview.alignmentScore,
          humanApprovalRequired: true,
          humanApprovalRequestId: architectureReview.humanApprovalRequest?.requestId
        }
      };
    }
  } else {
    console.log('\n⏭️  STAGE 3/5: Architecture Review (SKIPPED)');
  }

  // ============================================================================
  // STAGE 4: TASK GENERATION (Felix - Feature Architect)
  // ============================================================================
  console.log('\n📝 STAGE 4/5: Task Generation');
  console.log('   Agent: Felix (Feature Architect)');
  console.log('   ⚠️  Generating PROPOSALS for team review!');

  const tasksStartTime = Date.now();

  const taskGenerationInput: TaskGenerationInput = {
    specification: specification,
    teamCapacity: input.technicalContext?.teamSize ? input.technicalContext.teamSize * 40 : undefined,
    sprintDuration: 10 // 2-week sprints (10 working days)
  };

  const tasks = await executeTasks(
    taskGenerationInput,
    agents.featureArchitect
  );

  const tasksTime = Date.now() - tasksStartTime;
  console.log(`   ✓ Task generation complete (${tasksTime}ms)`);
  console.log(`     - ${tasks.epics.length} epics proposed`);
  console.log(`     - ${tasks.features.length} features proposed`);
  console.log(`     - ${tasks.stories.length} stories proposed`);
  console.log(`     - ${tasks.tasks.length} tasks proposed`);
  console.log(`     - ⚠️  All estimates TBD - Planning Poker required!`);

  // ============================================================================
  // STAGE 5: FILE GENERATION (Diana - Documentation Writer)
  // ============================================================================
  console.log('\n📄 STAGE 5/5: File Generation');
  console.log('   Agent: Diana (Documentation Writer)');

  const files = generateFiles(constitution, specification, tasks, input, architectureReview);

  console.log(`   ✓ Generated ${files.length} files`);
  files.forEach(file => {
    console.log(`     - ${file.path}`);
  });

  // ============================================================================
  // WORKFLOW SUMMARY
  // ============================================================================
  const totalTime = Date.now() - workflowStartTime;

  const summary: WorkflowSummary = {
    executionTime: totalTime,
    constitutionTime: constitutionTime,
    specificationTime: specificationTime,
    reviewTime: reviewTime,
    taskGenerationTime: tasksTime,
    filesGenerated: files.length,
    totalEpics: tasks.epics.length,
    totalFeatures: tasks.features.length,
    totalStories: tasks.stories.length,
    estimatedWeeks: 0, // TBD - Team must estimate after Planning Poker
    reviewVerdict: architectureReview?.verdict,
    alignmentScore: architectureReview?.alignmentScore
  };

  console.log('\n✅ Spec-Kit Workflow Complete!');
  console.log(`   Total time: ${totalTime}ms`);
  console.log(`   Generated: ${files.length} files`);
  if (architectureReview) {
    console.log(`   Architecture: ${architectureReview.verdict} (${architectureReview.alignmentScore}% aligned)`);
    console.log(`   ADRs: ${architectureReview.adrs.length} documented`);
  }
  console.log(`   Next steps: Team review → Planning Poker → Sprint Planning`);

  return {
    constitution,
    specification,
    architectureReview,
    tasks,
    files,
    summary
  };
}

/**
 * Generate markdown files from workflow results
 */
function generateFiles(
  constitution: ConstitutionResult,
  specification: SpecificationResult,
  tasks: TaskGenerationResult,
  input: SpecKitWorkflowInput,
  architectureReview?: ArchitectureReviewResult
): GeneratedFile[] {
  const files: GeneratedFile[] = [];

  // Base path for generated files
  const projectName = input.projectName || 'project';
  const basePath = input.projectPath || `projects/${projectName}`;

  // ============================================================================
  // FILE 1: constitution.md
  // ============================================================================
  files.push({
    path: `${basePath}/constitution.md`,
    content: formatConstitutionMarkdown(constitution),
    format: 'markdown'
  });

  // ============================================================================
  // FILE 2: specification.md
  // ============================================================================
  files.push({
    path: `${basePath}/specification.md`,
    content: formatSpecificationMarkdown(specification),
    format: 'markdown'
  });

  // ============================================================================
  // FILE 3: tasks.md (with Planning Poker guide)
  // ============================================================================
  files.push({
    path: `${basePath}/tasks.md`,
    content: formatTasksMarkdown(tasks),
    format: 'markdown'
  });

  // ============================================================================
  // FILE 4: architecture-review.md (BMAD-inspired review with ADRs)
  // ============================================================================
  if (architectureReview) {
    files.push({
      path: `${basePath}/architecture-review.md`,
      content: formatArchitectureReviewMarkdown(architectureReview),
      format: 'markdown'
    });
  }

  // ============================================================================
  // FILE 5: README.md (Project overview)
  // ============================================================================
  const readme = generateReadme(constitution, specification, tasks, projectName, architectureReview);
  files.push({
    path: `${basePath}/README.md`,
    content: readme,
    format: 'markdown'
  });

  // ============================================================================
  // FILE 5: metadata.json (Workflow metadata)
  // ============================================================================
  const metadata = {
    projectName: projectName,
    generatedAt: new Date().toISOString(),
    generatedBy: 'Spec-Kit Workflow',
    agents: {
      constitution: 'Peter (Product Owner)',
      specification: 'Felix (Feature Architect)',
      tasks: 'Felix (Feature Architect)',
      documentation: 'Diana (Documentation Writer)'
    },
    summary: {
      principles: constitution.principles.length,
      requirements: constitution.requirements.length,
      components: specification.components.length,
      epics: tasks.epics.length,
      features: tasks.features.length,
      stories: tasks.stories.length,
      tasks: tasks.tasks.length
    },
    versions: {
      constitution: constitution.metadata.version,
      specification: specification.metadata.version,
      tasks: tasks.metadata.version
    }
  };

  files.push({
    path: `${basePath}/metadata.json`,
    content: JSON.stringify(metadata, null, 2),
    format: 'json'
  });

  return files;
}

/**
 * Generate README.md for the project
 */
function generateReadme(
  constitution: ConstitutionResult,
  specification: SpecificationResult,
  tasks: TaskGenerationResult,
  projectName: string,
  architectureReview?: ArchitectureReviewResult
): string {
  let readme = `# ${projectName}\n\n`;

  // Architecture review status
  if (architectureReview) {
    readme += `**Architecture Status**: ${architectureReview.verdict} (${architectureReview.alignmentScore}% aligned)\n\n`;
  }

  // Project overview from first principle
  if (constitution.principles.length > 0) {
    readme += `## Overview\n\n`;
    readme += `${constitution.principles[0].principle}\n\n`;
  }

  // Architecture
  readme += `## Architecture\n\n`;
  readme += `**Pattern**: ${specification.architecture.pattern}\n\n`;

  if (specification.architecture.technologies.backend) {
    readme += `**Backend**: ${specification.architecture.technologies.backend.join(', ')}\n\n`;
  }

  if (specification.architecture.technologies.frontend) {
    readme += `**Frontend**: ${specification.architecture.technologies.frontend.join(', ')}\n\n`;
  }

  if (specification.architecture.technologies.database) {
    readme += `**Database**: ${specification.architecture.technologies.database.join(', ')}\n\n`;
  }

  // Development Stack (from Green Paper)
  if (specification.architecture.developmentStack) {
    readme += `## Development Stack\n\n`;
    const devStack = specification.architecture.developmentStack;
    readme += `**Languages**: ${devStack.languages.join(', ')}\n\n`;
    if (devStack.frameworks.frontend?.length) {
      readme += `**Frontend Framework**: ${devStack.frameworks.frontend.join(', ')}\n\n`;
    }
    if (devStack.frameworks.backend?.length) {
      readme += `**Backend Framework**: ${devStack.frameworks.backend.join(', ')}\n\n`;
    }
    readme += `**Primary Database**: ${devStack.databases.primary}\n\n`;
    readme += `**Version Control**: ${devStack.versionControl.system} on ${devStack.versionControl.platform}\n\n`;
  }

  // Operational Stack (from Green Paper)
  if (specification.architecture.operationalStack) {
    readme += `## Operational Stack\n\n`;
    const opsStack = specification.architecture.operationalStack;
    readme += `**Hosting**: ${opsStack.hosting.provider} (${opsStack.hosting.type})\n\n`;
    readme += `**CI/CD**: ${opsStack.cicd.platform}\n\n`;
    readme += `**Environments**: ${opsStack.cicd.environments.join(' → ')}\n\n`;
    if (opsStack.containerization) {
      readme += `**Containerization**: ${opsStack.containerization.runtime}\n\n`;
    }
  }

  // Project structure
  readme += `## Project Structure\n\n`;
  readme += `\`\`\`\n`;
  readme += `${projectName}/\n`;
  readme += `├── constitution.md        # Project principles and requirements\n`;
  readme += `├── specification.md       # Technical specification\n`;
  readme += `├── tasks.md              # Work breakdown (PROPOSAL)\n`;
  readme += `└── README.md             # This file\n`;
  readme += `\`\`\`\n\n`;

  // Next steps
  readme += `## Next Steps\n\n`;
  readme += `### 1. Review Constitution\n`;
  readme += `- Read [constitution.md](./constitution.md)\n`;
  readme += `- Challenge principles and requirements\n`;
  readme += `- Add missing constraints or risks\n\n`;

  readme += `### 2. Review Specification\n`;
  readme += `- Read [specification.md](./specification.md)\n`;
  readme += `- Validate architecture decisions\n`;
  readme += `- Confirm technology choices\n\n`;

  readme += `### 3. Estimate Tasks\n`;
  readme += `- Read [tasks.md](./tasks.md)\n`;
  readme += `- Conduct Planning Poker for all stories\n`;
  readme += `- Refine task breakdown as needed\n\n`;

  readme += `### 4. Sprint Planning\n`;
  readme += `- Assign tasks to team members\n`;
  readme += `- Create sprint backlog\n`;
  readme += `- Set sprint goals\n\n`;

  // Summary statistics
  readme += `## Summary\n\n`;
  readme += `- **Epics**: ${tasks.epics.length}\n`;
  readme += `- **Features**: ${tasks.features.length}\n`;
  readme += `- **Stories**: ${tasks.stories.length} (requires team estimation)\n`;
  readme += `- **Tasks**: ${tasks.tasks.length}\n`;
  readme += `- **Components**: ${specification.components.length}\n\n`;

  readme += `---\n\n`;
  readme += `*Generated by Spec-Kit Workflow - ${new Date().toISOString()}*\n`;

  return readme;
}

/**
 * Validate Spec-Kit workflow input
 */
export function validateSpecKitInput(
  input: SpecKitWorkflowInput
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!input.businessCase || input.businessCase.trim().length === 0) {
    errors.push('Business case is required');
  }

  if (!input.stakeholders || input.stakeholders.length === 0) {
    errors.push('At least one stakeholder is required');
  }

  if (!input.constraints || input.constraints.length === 0) {
    errors.push('At least one constraint is required');
  }

  if (!input.successCriteria || input.successCriteria.length === 0) {
    errors.push('At least one success criterion is required');
  }

  if (input.businessCase && input.businessCase.length < 50) {
    errors.push('Business case must be at least 50 characters');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Helper: Save files to disk (optional - for actual file system writes)
 */
export async function saveFilesToDisk(files: GeneratedFile[]): Promise<void> {
  const fs = await import('fs/promises');
  const path = await import('path');

  for (const file of files) {
    const dirPath = path.dirname(file.path);

    // Create directory if it doesn't exist
    await fs.mkdir(dirPath, { recursive: true });

    // Write file
    await fs.writeFile(file.path, file.content, 'utf-8');

    console.log(`   ✓ Saved: ${file.path}`);
  }
}
