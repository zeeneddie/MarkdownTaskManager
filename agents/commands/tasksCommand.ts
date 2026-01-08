/**
 * /tasks Command - Task Generation from Specification
 *
 * Generates PROPOSED work breakdown structure for team review:
 * - Epics (high-level capabilities)
 * - Features (deliverable functionality)
 * - Stories (user-facing value)
 * - Tasks (technical implementation)
 *
 * IMPORTANT: This is a PROPOSAL to be challenged by the team!
 * - Breakdown structure should be reviewed and adjusted
 * - Estimations MUST be done by team using Planning Poker
 * - All estimates are placeholders (0 or TBD) until team estimation
 */

import { Agent } from 'kaibanjs';
import {
  SpecificationResult,
  TaskGenerationInput,
  TaskGenerationResult,
  Epic,
  Feature,
  Story,
  Task,
  StoryPoints,
  Estimation,
  Priority,
  ItemType,
  ComponentSpec
} from '../types/SpecKit';
import {
  SlashCommandType,
  SlashCommandInput,
  SlashCommandOutput,
  CommandStatus,
  CommandDefinition,
  OutputFormat,
  RecommendationPriority
} from '../types/SlashCommand';
import { registerCommand } from '../workflows/commandRegistry';

// ============================================================================
// COMMAND METADATA
// ============================================================================

/**
 * Full CommandDefinition for /tasks command
 */
export const TASKS_DEFINITION: CommandDefinition = {
  type: SlashCommandType.TASKS,
  name: 'Task Breakdown Generator',
  description: 'Generates PROPOSED work breakdown structure (Epics → Features → Stories → Tasks) from technical specification. ALL ESTIMATES ARE TBD - Team MUST conduct Planning Poker to finalize estimates.',
  persona: 'Feature Architect (Felix) - Expert in Agile work breakdown, user story decomposition, and task estimation. Provides PROPOSALS for team to challenge and refine using Planning Poker.',
  expertise: [
    'Work Breakdown Structure (WBS)',
    'Epic/Feature/Story/Task Decomposition',
    'User Story Writing',
    'Acceptance Criteria Definition',
    'Dependency Analysis',
    'Planning Poker Facilitation',
    'Agile Estimation (Story Points)',
    'Sprint Planning'
  ],
  capabilities: [
    'Generate proposed epics from components',
    'Break down epics into features',
    'Create user stories with acceptance criteria',
    'Decompose stories into technical tasks',
    'Identify task dependencies',
    'Suggest story point ranges (team must finalize)',
    'Calculate effort estimates (team must validate)',
    'Generate Planning Poker guidance',
    'Create sprint-ready work items'
  ],
  bestUsedFor: [
    'After specification generation (Stage 3 of Spec-Kit)',
    'Sprint planning preparation',
    'Work breakdown structure creation',
    'Backlog initialization',
    'Effort estimation kickoff',
    'Dependency mapping',
    'Team capacity planning',
    'Roadmap creation'
  ],
  requiredContext: [
    'specification'
  ],
  optionalContext: [
    'teamSize',
    'sprintLength',
    'teamVelocity',
    'constraints',
    'timeline'
  ],
  outputTypes: [OutputFormat.MARKDOWN, OutputFormat.JSON, OutputFormat.TEXT],
  examples: [
    {
      scenario: 'E-commerce platform task breakdown',
      input: {
        command: SlashCommandType.TASKS,
        context: {
          metadata: {
            specification: {
              components: [
                { name: 'User Authentication', type: 'backend' },
                { name: 'Product Catalog', type: 'backend' },
                { name: 'Shopping Cart', type: 'backend' }
              ],
              interfaces: [
                { path: '/api/auth/login', method: 'POST' },
                { path: '/api/products', method: 'GET' }
              ]
            }
          }
        } as any
      },
      expectedOutcome: 'Generates 3-5 epics, 8-12 features, 20-30 stories, 50-80 tasks. All estimates TBD. Includes Planning Poker guidance and dependency map.'
    },
    {
      scenario: 'MVP sprint planning',
      input: {
        command: SlashCommandType.TASKS,
        context: {
          metadata: {
            specification: {
              components: [{ name: 'Core MVP', type: 'fullstack' }]
            },
            teamSize: 5,
            sprintLength: '2 weeks',
            timeline: '6 weeks MVP delivery'
          }
        } as any
      },
      expectedOutcome: 'Focused breakdown for 3 sprints, critical path highlighted, dependencies mapped, team capacity considered (estimates still TBD for Planning Poker)'
    }
  ]
};

// ============================================================================
// MAIN EXECUTION FUNCTION
// ============================================================================

/**
 * Main execution function for /tasks command
 *
 * Generates PROPOSED breakdown for team to review and estimate
 */
export async function executeTasks(
  input: TaskGenerationInput,
  agent: Agent
): Promise<TaskGenerationResult> {
  console.log('📋 Executing /tasks command...');
  console.log('   ⚠️  Generating PROPOSAL - team must review and estimate!');
  console.log(`   Input: ${input.specification.components.length} components`);

  // Step 1: Generate PROPOSED epics from components
  console.log('   Step 1/5: Generating PROPOSED epics...');
  const epics = await generateProposedEpics(input, agent);
  console.log(`   ✓ Generated ${epics.length} epic proposals`);

  // Step 2: Generate PROPOSED features from epics
  console.log('   Step 2/5: Generating PROPOSED features...');
  const features = await generateProposedFeatures(input, epics, agent);
  console.log(`   ✓ Generated ${features.length} feature proposals`);

  // Step 3: Generate PROPOSED stories from features
  console.log('   Step 3/5: Generating PROPOSED stories...');
  const stories = await generateProposedStories(input, features, agent);
  console.log(`   ✓ Generated ${stories.length} story proposals`);

  // Step 4: Generate PROPOSED tasks from stories
  console.log('   Step 4/5: Generating PROPOSED tasks...');
  const tasks = await generateProposedTasks(input, stories, agent);
  console.log(`   ✓ Generated ${tasks.length} task proposals`);

  // Step 5: Calculate SUGGESTED dependencies
  console.log('   Step 5/5: Calculating SUGGESTED dependencies...');
  const updatedTasks = calculateSuggestedDependencies(tasks, stories, features);
  console.log(`   ✓ Dependencies suggested (team should review)`);

  // Create placeholder estimations (team will fill in with Planning Poker)
  const estimations = createPlaceholderEstimations(epics, features, stories, updatedTasks);

  console.log('✅ /tasks command complete!');
  console.log('   ⚠️  NEXT: Team must review breakdown and conduct Planning Poker');
  console.log('   📝 All estimates are TBD - team estimation required!');

  return {
    epics,
    features,
    stories,
    tasks: updatedTasks,
    estimations,
    metadata: {
      generatedAt: new Date(),
      generatedBy: 'Felix (Feature Architect) - PROPOSAL ONLY',
      version: '1.0.0',
      basedOnSpecification: input.specification.metadata.version
    }
  };
}

/**
 * Step 1: Generate PROPOSED epics from components
 */
async function generateProposedEpics(
  input: TaskGenerationInput,
  agent: Agent
): Promise<Epic[]> {
  const epics: Epic[] = [];
  let epicCounter = 1;

  // Create an epic PROPOSAL for each major component
  for (const component of input.specification.components) {
    const epic: Epic = {
      id: `EPIC-${String(epicCounter).padStart(3, '0')}`,
      title: `Implement ${component.name}`,
      description: generateComponentDescription(component),
      businessValue: calculateBusinessValue(component),
      priority: determineSuggestedPriority(component),
      estimatedSP: 0, // TBD - Team must estimate with Planning Poker
      features: [], // Will be populated later
      relatedComponents: [component.name],
      relatedRequirements: [] // Could be populated from constitution
    };

    epics.push(epic);
    epicCounter++;
  }

  // Add infrastructure epic if needed
  if (hasInfrastructureNeeds(input.specification)) {
    epics.push({
      id: `EPIC-${String(epicCounter).padStart(3, '0')}`,
      title: 'Infrastructure & DevOps Setup',
      description: 'Set up development, testing, and production infrastructure with CI/CD pipeline and monitoring',
      businessValue: 'Enable development, testing, and deployment capabilities',
      priority: Priority.HIGH,
      estimatedSP: 0, // TBD - Team must estimate
      features: [],
      relatedComponents: ['Infrastructure', 'CI/CD', 'Monitoring']
    });
  }

  return epics;
}

/**
 * Step 2: Generate PROPOSED features from epics
 */
async function generateProposedFeatures(
  input: TaskGenerationInput,
  epics: Epic[],
  agent: Agent
): Promise<Feature[]> {
  const features: Feature[] = [];
  let featureCounter = 1;

  for (const epic of epics) {
    // Find the component for this epic
    const component = input.specification.components.find(c =>
      epic.relatedComponents?.includes(c.name)
    );

    if (component) {
      // Create feature PROPOSAL for each responsibility
      for (const responsibility of component.responsibilities) {
        const feature: Feature = {
          id: `FEAT-${String(featureCounter).padStart(3, '0')}`,
          epicId: epic.id,
          title: responsibility,
          description: `Implement ${responsibility} functionality in ${component.name}`,
          acceptanceCriteria: generateFeatureAcceptanceCriteria(responsibility, component),
          priority: epic.priority,
          estimatedSP: 0, // TBD - Team must estimate with Planning Poker
          stories: [], // Will be populated later
          dependencies: [] // Will be suggested later
        };

        features.push(feature);
        epic.features.push(feature.id);
        featureCounter++;
      }
    } else if (epic.title.includes('Infrastructure')) {
      // Infrastructure feature PROPOSALS
      const infraFeatures = [
        {
          title: 'Development Environment Setup',
          description: 'Set up local development environment with all required tools and configurations',
          criteria: ['Docker environment running', 'Database accessible', 'All services can be started locally']
        },
        {
          title: 'CI/CD Pipeline Implementation',
          description: 'Implement automated build, test, and deployment pipeline',
          criteria: ['Automated builds on commit', 'Tests run automatically', 'Deployment to staging/production']
        },
        {
          title: 'Monitoring & Logging Setup',
          description: 'Implement system monitoring, logging, and alerting infrastructure',
          criteria: ['Logs centralized', 'Metrics dashboard available', 'Alerts configured']
        },
        {
          title: 'Deployment Automation',
          description: 'Automate deployment process for all environments',
          criteria: ['One-command deploy', 'Rollback capability', 'Zero-downtime deployment']
        }
      ];

      for (const infraFeature of infraFeatures) {
        const feature: Feature = {
          id: `FEAT-${String(featureCounter).padStart(3, '0')}`,
          epicId: epic.id,
          title: infraFeature.title,
          description: infraFeature.description,
          acceptanceCriteria: infraFeature.criteria,
          priority: Priority.HIGH,
          estimatedSP: 0, // TBD - Team must estimate
          stories: [],
          dependencies: []
        };

        features.push(feature);
        epic.features.push(feature.id);
        featureCounter++;
      }
    }
  }

  return features;
}

/**
 * Step 3: Generate PROPOSED stories from features
 */
async function generateProposedStories(
  input: TaskGenerationInput,
  features: Feature[],
  agent: Agent
): Promise<Story[]> {
  const stories: Story[] = [];
  let storyCounter = 1;

  for (const feature of features) {
    // Break feature into 2-4 story PROPOSALS
    const storyPhases = getStoryPhases(feature);

    for (const phase of storyPhases) {
      const story: Story = {
        id: `STORY-${String(storyCounter).padStart(3, '0')}`,
        featureId: feature.id,
        title: phase.title,
        description: phase.description,
        acceptanceCriteria: phase.acceptanceCriteria,
        storyPoints: 0 as StoryPoints, // TBD - Team must estimate with Planning Poker
        priority: feature.priority,
        tasks: [], // Will be populated later
        dependencies: [] // Will be suggested later
      };

      stories.push(story);
      feature.stories.push(story.id);
      storyCounter++;
    }
  }

  return stories;
}

/**
 * Step 4: Generate PROPOSED tasks from stories
 */
async function generateProposedTasks(
  input: TaskGenerationInput,
  stories: Story[],
  agent: Agent
): Promise<Task[]> {
  const tasks: Task[] = [];
  let taskCounter = 1;

  for (const story of stories) {
    // Generate standard task breakdown PROPOSAL
    const taskProposals = generateTaskBreakdown(story);

    for (const proposal of taskProposals) {
      const task: Task = {
        id: `TASK-${String(taskCounter).padStart(4, '0')}`,
        storyId: story.id,
        title: proposal.title,
        description: proposal.description,
        estimatedHours: 0, // TBD - Team must estimate
        skills: proposal.skills,
        assignTo: undefined, // Team will assign during sprint planning
        technicalNotes: proposal.technicalNotes,
        dependencies: [] // Will be suggested later
      };

      tasks.push(task);
      story.tasks.push(task.id);
      taskCounter++;
    }
  }

  return tasks;
}

/**
 * Step 5: Calculate SUGGESTED dependencies between tasks
 *
 * These are SUGGESTIONS - team should review and adjust
 */
function calculateSuggestedDependencies(
  tasks: Task[],
  stories: Story[],
  features: Feature[]
): Task[] {
  // Group tasks by story
  const tasksByStory = new Map<string, Task[]>();
  for (const task of tasks) {
    if (!tasksByStory.has(task.storyId)) {
      tasksByStory.set(task.storyId, []);
    }
    tasksByStory.get(task.storyId)!.push(task);
  }

  // Add SUGGESTED dependencies within each story
  // Typical flow: Database → Backend → Frontend → Integration → Tests → Docs
  for (const [storyId, storyTasks] of tasksByStory) {
    const dbTask = storyTasks.find(t => t.title.toLowerCase().includes('database') || t.title.toLowerCase().includes('schema'));
    const backendTask = storyTasks.find(t => t.title.toLowerCase().includes('backend') || t.title.toLowerCase().includes('api'));
    const frontendTask = storyTasks.find(t => t.title.toLowerCase().includes('frontend') || t.title.toLowerCase().includes('ui'));
    const integrationTask = storyTasks.find(t => t.title.toLowerCase().includes('integration'));
    const testTask = storyTasks.find(t => t.title.toLowerCase().includes('test'));
    const docsTask = storyTasks.find(t => t.title.toLowerCase().includes('doc'));

    // Suggested dependency chain
    if (backendTask && dbTask) backendTask.dependencies.push(dbTask.id);
    if (frontendTask && backendTask) frontendTask.dependencies.push(backendTask.id);
    if (integrationTask && frontendTask) integrationTask.dependencies.push(frontendTask.id);
    if (integrationTask && backendTask) integrationTask.dependencies.push(backendTask.id);
    if (testTask && integrationTask) testTask.dependencies.push(integrationTask.id);
    if (docsTask && testTask) docsTask.dependencies.push(testTask.id);
  }

  return tasks;
}

/**
 * Create placeholder estimations summary
 * All values are 0 or TBD until team does Planning Poker
 */
function createPlaceholderEstimations(
  epics: Epic[],
  features: Feature[],
  stories: Story[],
  tasks: Task[]
): Estimation {
  return {
    totalEpics: epics.length,
    totalFeatures: features.length,
    totalStories: stories.length,
    totalTasks: tasks.length,
    totalStoryPoints: 0, // TBD - Team must estimate with Planning Poker
    totalHours: 0, // TBD - Will be calculated after Planning Poker
    confidence: 0.0, // TBD - Will be determined after team estimation
    estimatedSprints: undefined, // TBD - Depends on team velocity
    estimatedWeeks: undefined // TBD - Depends on team velocity
  };
}

/**
 * Helper: Generate component description
 */
function generateComponentDescription(component: ComponentSpec): string {
  const responsibilities = component.responsibilities.join(', ');
  const technologies = component.technologies.join(', ');

  return `Implement ${component.name} component with responsibilities: ${responsibilities}. Technologies: ${technologies}.`;
}

/**
 * Helper: Calculate business value of a component
 */
function calculateBusinessValue(component: ComponentSpec): string {
  const name = component.name.toLowerCase();

  if (name.includes('auth') || name.includes('security')) {
    return 'Critical for security and user management';
  } else if (name.includes('api') || name.includes('service')) {
    return 'Enables client integration and data access';
  } else if (name.includes('ui') || name.includes('frontend')) {
    return 'Direct user interaction and experience';
  } else if (name.includes('database') || name.includes('storage')) {
    return 'Core data persistence and integrity';
  } else {
    return `Provides ${component.name} functionality to the system`;
  }
}

/**
 * Helper: Determine SUGGESTED priority (team should review)
 */
function determineSuggestedPriority(component: ComponentSpec): Priority {
  const highPriorityKeywords = ['auth', 'security', 'database', 'api', 'core'];
  const componentNameLower = component.name.toLowerCase();

  if (highPriorityKeywords.some(keyword => componentNameLower.includes(keyword))) {
    return Priority.HIGH;
  } else if (componentNameLower.includes('ui') || componentNameLower.includes('frontend')) {
    return Priority.MEDIUM;
  } else {
    return Priority.LOW;
  }
}

/**
 * Helper: Generate feature acceptance criteria
 */
function generateFeatureAcceptanceCriteria(responsibility: string, component: ComponentSpec): string[] {
  return [
    `${responsibility} functionality is fully implemented in ${component.name}`,
    'All edge cases and error scenarios are handled',
    'Unit tests achieve >80% code coverage',
    'Integration tests pass successfully',
    'Documentation is complete and up-to-date',
    'Code review is approved by team'
  ];
}

/**
 * Helper: Check if infrastructure epic is needed
 */
function hasInfrastructureNeeds(specification: SpecificationResult): boolean {
  // Always propose infrastructure for new projects
  return true;
}

/**
 * Helper: Get story phases for a feature
 */
function getStoryPhases(feature: Feature): Array<{
  title: string;
  description: string;
  acceptanceCriteria: string[];
}> {
  return [
    {
      title: `${feature.title} - Foundation`,
      description: `Set up foundation for ${feature.title}: data models, basic structure, and dependencies`,
      acceptanceCriteria: [
        'Data models are defined and documented',
        'Basic code structure is in place',
        'Dependencies are identified and available',
        'Development environment can build the code'
      ]
    },
    {
      title: `${feature.title} - Core Implementation`,
      description: `Implement core functionality for ${feature.title}`,
      acceptanceCriteria: [
        'Main functionality is working for happy path',
        'Business logic is implemented correctly',
        'Error handling covers main scenarios',
        'Unit tests pass for core functionality'
      ]
    },
    {
      title: `${feature.title} - Integration`,
      description: `Integrate ${feature.title} with other components and systems`,
      acceptanceCriteria: [
        'Components are integrated successfully',
        'End-to-end flow works correctly',
        'Integration tests pass',
        'External dependencies are handled'
      ]
    },
    {
      title: `${feature.title} - Polish & Optimization`,
      description: `Polish UI/UX and optimize performance for ${feature.title}`,
      acceptanceCriteria: [
        'Performance meets requirements',
        'UI/UX is intuitive and polished',
        'Edge cases are handled gracefully',
        'User feedback is incorporated'
      ]
    }
  ];
}

/**
 * Helper: Generate task breakdown for a story
 */
function generateTaskBreakdown(story: Story): Array<{
  title: string;
  description: string;
  skills: string[];
  technicalNotes?: string[];
}> {
  const storyType = determineStoryType(story.title);

  if (storyType === 'foundation') {
    return [
      {
        title: `${story.title} - Database Schema`,
        description: 'Design and implement database schema/migrations',
        skills: ['database', 'sql', 'migrations'],
        technicalNotes: ['Define tables, relationships, and indexes', 'Write migration scripts', 'Test on local database']
      },
      {
        title: `${story.title} - Data Models`,
        description: 'Create data models and domain entities',
        skills: ['backend', 'domain-modeling'],
        technicalNotes: ['Define domain entities', 'Implement model validation', 'Add model tests']
      },
      {
        title: `${story.title} - Project Structure`,
        description: 'Set up project structure and basic scaffolding',
        skills: ['backend', 'frontend'],
        technicalNotes: ['Create folder structure', 'Set up build configuration', 'Add basic templates']
      }
    ];
  } else if (storyType === 'core') {
    return [
      {
        title: `${story.title} - Backend API`,
        description: 'Implement backend API endpoints and business logic',
        skills: ['backend', 'api', 'business-logic'],
        technicalNotes: ['Define API endpoints', 'Implement business logic', 'Add error handling', 'Write API documentation']
      },
      {
        title: `${story.title} - Frontend UI`,
        description: 'Implement frontend user interface',
        skills: ['frontend', 'ui', 'react'],
        technicalNotes: ['Create UI components', 'Implement user interactions', 'Add form validation', 'Style components']
      },
      {
        title: `${story.title} - Unit Tests`,
        description: 'Write unit tests for backend and frontend',
        skills: ['testing', 'backend', 'frontend'],
        technicalNotes: ['Test business logic', 'Test UI components', 'Achieve >80% coverage', 'Test edge cases']
      }
    ];
  } else if (storyType === 'integration') {
    return [
      {
        title: `${story.title} - API Integration`,
        description: 'Integrate frontend with backend APIs',
        skills: ['frontend', 'api', 'integration'],
        technicalNotes: ['Connect UI to API', 'Handle API responses', 'Add loading states', 'Handle errors']
      },
      {
        title: `${story.title} - Integration Tests`,
        description: 'Write integration and end-to-end tests',
        skills: ['testing', 'e2e', 'integration'],
        technicalNotes: ['Test complete user flows', 'Test API integration', 'Test error scenarios', 'Verify data persistence']
      }
    ];
  } else { // polish
    return [
      {
        title: `${story.title} - Performance Optimization`,
        description: 'Optimize performance and resource usage',
        skills: ['performance', 'optimization'],
        technicalNotes: ['Profile performance', 'Optimize database queries', 'Reduce API calls', 'Optimize rendering']
      },
      {
        title: `${story.title} - UX Improvements`,
        description: 'Improve user experience and polish UI',
        skills: ['ux', 'ui', 'frontend'],
        technicalNotes: ['Improve feedback messages', 'Add loading indicators', 'Polish animations', 'Improve accessibility']
      },
      {
        title: `${story.title} - Documentation`,
        description: 'Write user and technical documentation',
        skills: ['documentation', 'writing'],
        technicalNotes: ['Document user flows', 'Write technical docs', 'Add code comments', 'Create user guide']
      }
    ];
  }
}

/**
 * Helper: Determine story type from title
 */
function determineStoryType(title: string): 'foundation' | 'core' | 'integration' | 'polish' {
  const lowerTitle = title.toLowerCase();

  if (lowerTitle.includes('foundation')) return 'foundation';
  if (lowerTitle.includes('core')) return 'core';
  if (lowerTitle.includes('integration')) return 'integration';
  if (lowerTitle.includes('polish')) return 'polish';

  return 'core'; // default
}

/**
 * Format task generation result as markdown
 *
 * IMPORTANT: This is a PROPOSAL document for team review!
 * Team must challenge the breakdown and conduct Planning Poker for estimation.
 */
export function formatTasksMarkdown(result: TaskGenerationResult): string {
  let markdown = '# Project Tasks - PROPOSAL\n\n';
  markdown += `**Generated**: ${result.metadata.generatedAt.toISOString()}\n`;
  markdown += `**Generated By**: ${result.metadata.generatedBy}\n`;
  markdown += `**Based On**: Specification ${result.metadata.basedOnSpecification}\n\n`;

  // Important warning
  markdown += '## ⚠️  IMPORTANT: Team Review Required\n\n';
  markdown += '**This is a PROPOSED breakdown for team discussion!**\n\n';
  markdown += '### Required Actions:\n';
  markdown += '1. **Challenge the Breakdown**: Review epic/feature/story/task structure\n';
  markdown += '2. **Conduct Planning Poker**: Estimate all stories using team Planning Poker\n';
  markdown += '3. **Adjust Priorities**: Refine priorities based on business value\n';
  markdown += '4. **Review Dependencies**: Validate and adjust suggested dependencies\n';
  markdown += '5. **Assign Tasks**: Assign tasks to team members during sprint planning\n\n';
  markdown += '**All estimates (SP and hours) are currently TBD until team estimation!**\n\n';
  markdown += '---\n\n';

  markdown += '## 📊 Summary\n\n';
  markdown += `- **Epics**: ${result.estimations.totalEpics}\n`;
  markdown += `- **Features**: ${result.estimations.totalFeatures}\n`;
  markdown += `- **Stories**: ${result.estimations.totalStories}\n`;
  markdown += `- **Tasks**: ${result.estimations.totalTasks}\n`;
  markdown += `- **Total Story Points**: TBD (Planning Poker required)\n`;
  markdown += `- **Total Hours**: TBD (Calculated after Planning Poker)\n`;
  markdown += `- **Confidence**: TBD (After team estimation)\n\n`;

  markdown += '---\n\n';

  // Epics
  markdown += '## 📚 Epics (PROPOSED)\n\n';
  for (const epic of result.epics) {
    markdown += `### ${epic.id}: ${epic.title}\n\n`;
    markdown += `**Priority**: ${epic.priority} _(team should review)_\n`;
    markdown += `**Estimation**: TBD - **Planning Poker Required**\n\n`;
    markdown += `**Business Value**: ${epic.businessValue}\n\n`;
    markdown += `**Description**: ${epic.description}\n\n`;

    if (epic.relatedComponents && epic.relatedComponents.length > 0) {
      markdown += `**Related Components**: ${epic.relatedComponents.join(', ')}\n\n`;
    }

    markdown += `**Features**: ${epic.features.length} features proposed\n\n`;
    markdown += '---\n\n';
  }

  // Features
  markdown += '## 🎯 Features (PROPOSED)\n\n';
  for (const feature of result.features) {
    markdown += `### ${feature.id}: ${feature.title}\n\n`;
    markdown += `**Epic**: ${feature.epicId}\n`;
    markdown += `**Priority**: ${feature.priority} _(team should review)_\n`;
    markdown += `**Estimation**: TBD - **Planning Poker Required**\n\n`;
    markdown += `**Description**: ${feature.description}\n\n`;

    markdown += '**Acceptance Criteria** _(team should review)_:\n';
    feature.acceptanceCriteria.forEach(criteria => {
      markdown += `- ${criteria}\n`;
    });
    markdown += '\n';

    markdown += `**Stories**: ${feature.stories.length} stories proposed\n\n`;
    markdown += '---\n\n';
  }

  // Stories
  markdown += '## 📖 User Stories (PROPOSED)\n\n';
  markdown += '_Team should conduct Planning Poker to estimate each story_\n\n';

  for (const story of result.stories) {
    markdown += `### ${story.id}: ${story.title}\n\n`;
    markdown += `**Feature**: ${story.featureId}\n`;
    markdown += `**Priority**: ${story.priority}\n`;
    markdown += `**Story Points**: TBD - **Planning Poker Required** 🃏\n\n`;

    markdown += `**Description**: ${story.description}\n\n`;

    markdown += '**Acceptance Criteria** _(team should review)_:\n';
    story.acceptanceCriteria.forEach(criteria => {
      markdown += `- ${criteria}\n`;
    });
    markdown += '\n';

    markdown += `**Tasks**: ${story.tasks.length} tasks proposed\n\n`;
    markdown += '---\n\n';
  }

  // Tasks
  markdown += '## ✅ Tasks (PROPOSED)\n\n';
  markdown += '_Team should review task breakdown and estimate hours_\n\n';

  // Group tasks by story
  const tasksByStory = new Map<string, typeof result.tasks>();
  for (const task of result.tasks) {
    if (!tasksByStory.has(task.storyId)) {
      tasksByStory.set(task.storyId, []);
    }
    tasksByStory.get(task.storyId)!.push(task);
  }

  for (const story of result.stories) {
    const storyTasks = tasksByStory.get(story.id) || [];
    if (storyTasks.length > 0) {
      markdown += `### ${story.id} - Proposed Tasks\n\n`;

      for (const task of storyTasks) {
        markdown += `#### ${task.id}: ${task.title}\n\n`;
        markdown += `**Description**: ${task.description}\n\n`;
        markdown += `**Estimated Hours**: TBD - **Team estimation required**\n\n`;
        markdown += `**Required Skills**: ${task.skills.join(', ')}\n\n`;

        if (task.dependencies && task.dependencies.length > 0) {
          markdown += `**Suggested Dependencies** _(team should review)_: ${task.dependencies.join(', ')}\n\n`;
        }

        if (task.technicalNotes && task.technicalNotes.length > 0) {
          markdown += '**Technical Notes**:\n';
          task.technicalNotes.forEach(note => {
            markdown += `- ${note}\n`;
          });
          markdown += '\n';
        }
      }

      markdown += '---\n\n';
    }
  }

  // Planning Poker Guide
  markdown += '## 🃏 Planning Poker Guide\n\n';
  markdown += '### How to Estimate Stories\n\n';
  markdown += '1. **Read the story** and acceptance criteria together\n';
  markdown += '2. **Discuss complexity**, unknowns, and dependencies\n';
  markdown += '3. **Each team member** selects a story point value privately (1, 2, 3, 5, 8, 13, 21, 34)\n';
  markdown += '4. **Reveal estimates** simultaneously\n';
  markdown += '5. **Discuss differences** - highest and lowest explain their reasoning\n';
  markdown += '6. **Re-estimate** until consensus is reached\n';
  markdown += '7. **Record final estimate** and move to next story\n\n';

  markdown += '### Story Point Reference\n\n';
  markdown += '- **1 SP**: Very simple task, < 4 hours, no unknowns\n';
  markdown += '- **2 SP**: Simple task, 4-8 hours, minimal complexity\n';
  markdown += '- **3 SP**: Moderate task, 8-12 hours, some complexity\n';
  markdown += '- **5 SP**: Complex task, 12-20 hours, multiple components\n';
  markdown += '- **8 SP**: Very complex, 20-32 hours, many dependencies\n';
  markdown += '- **13 SP**: Extremely complex, 32-52 hours, high uncertainty\n';
  markdown += '- **21+ SP**: Too large - break into smaller stories!\n\n';

  markdown += '---\n\n';
  markdown += '_Generated by Spec-Kit Workflow - Felix (Feature Architect)_\n';

  return markdown;
}

// ============================================================================
// COMMAND EXECUTOR (CommandRegistry Interface)
// ============================================================================

/**
 * Execute tasks command via CommandRegistry interface
 * Adapts the executeTasks function to match CommandExecutor signature
 */
export async function executeTasksCommand(
  input: SlashCommandInput
): Promise<SlashCommandOutput> {
  const startTime = Date.now();

  try {
    // Extract context (using type assertion for custom fields)
    const ctx = input.context as any;
    const taskInput: TaskGenerationInput = {
      specification: ctx.specification as SpecificationResult
    };

    if (!taskInput.specification) {
      throw new Error('Specification is required for task generation. Run /specification first.');
    }

    // Mock agent (will be replaced with actual agent from KaibanJS)
    const mockAgent: Agent = {
      name: 'Felix',
      role: 'Feature Architect',
      goal: 'Break down specification into tasks',
      background: 'Agile expert with task decomposition skills'
    } as Agent;

    // Execute task generation
    const result = await executeTasks(taskInput, mockAgent);

    // Convert to SlashCommandOutput
    const duration = Date.now() - startTime;

    const output: SlashCommandOutput = {
      commandId: `tasks-${Date.now()}`,
      command: SlashCommandType.TASKS,
      status: CommandStatus.COMPLETED,
      executedBy: 'Felix (Feature Architect)',
      executedAt: new Date(),
      completedAt: new Date(),
      duration,
      analysis: {
        summary: `Generated PROPOSED work breakdown: ${result.epics.length} epics, ${result.features.length} features, ${result.stories.length} stories, ${result.tasks.length} tasks`,
        scores: {
          completeness: 0.85,
          granularity: 0.88,
          feasibility: 0.90
        },
        strengths: [
          `${result.epics.length} epics aligned with components`,
          `${result.features.length} features with clear acceptance criteria`,
          `${result.stories.length} user stories ready for estimation`,
          `${result.tasks.length} technical tasks identified`,
          'Dependencies mapped for sprint planning'
        ],
        weaknesses: [
          'All estimates are TBD - Planning Poker required',
          'Team must review and challenge breakdown',
          'Priorities need team validation'
        ]
      },
      recommendations: [
        {
          id: 'rec-1',
          priority: RecommendationPriority.HIGH,
          category: 'Estimation',
          title: 'Conduct Planning Poker Session',
          description: `Team MUST estimate all ${result.stories.length} stories using Planning Poker. Current estimates are placeholders only.`,
          rationale: 'Accurate estimates require team consensus through Planning Poker',
          benefits: ['Accurate estimates', 'Team buy-in', 'Risk identification'],
          effort: 'HIGH',
          impact: 'HIGH',
          confidence: 1.0,
          implementation: {
            steps: [
              'Schedule Planning Poker session with full team',
              'Review each story one by one',
              'Team members vote simultaneously using Fibonacci sequence',
              'Discuss differences and re-estimate until consensus',
              'Record final estimates in backlog'
            ],
            estimatedTime: `${Math.ceil(result.stories.length / 10)} hours for ${result.stories.length} stories`,
            prerequisites: ['All team members present', 'Story details clarified']
          }
        },
        {
          id: 'rec-2',
          priority: RecommendationPriority.HIGH,
          category: 'Review',
          title: 'Challenge the Breakdown Structure',
          description: 'Team should review and potentially restructure the epic/feature/story hierarchy',
          rationale: 'AI-generated breakdown is a PROPOSAL - team knows the domain better',
          benefits: ['Better aligned work items', 'Team ownership'],
          effort: 'MEDIUM',
          impact: 'HIGH',
          confidence: 0.9
        },
        {
          id: 'rec-3',
          priority: RecommendationPriority.MEDIUM,
          category: 'Dependencies',
          title: 'Validate Dependency Map',
          description: 'Review suggested dependencies and add/remove based on team knowledge',
          rationale: 'Dependency mapping affects sprint planning and delivery order',
          benefits: ['Realistic sprint plans', 'No blocked work'],
          effort: 'LOW',
          impact: 'MEDIUM',
          confidence: 0.85
        },
        {
          id: 'rec-4',
          priority: RecommendationPriority.MEDIUM,
          category: 'Sprint Planning',
          title: 'Create First Sprint Backlog',
          description: 'Select highest priority stories for Sprint 1 based on team velocity',
          rationale: 'Get started with actionable sprint plan',
          benefits: ['Clear sprint goal', 'Team focus'],
          effort: 'LOW',
          impact: 'HIGH',
          confidence: 0.9
        }
      ],
      topRecommendation: {
        id: 'rec-1',
        priority: RecommendationPriority.HIGH,
        category: 'Estimation',
        title: 'Conduct Planning Poker Session',
        description: `Team MUST estimate all ${result.stories.length} stories using Planning Poker`,
        rationale: 'Accurate estimates require team consensus',
        benefits: ['Accurate estimates', 'Team buy-in'],
        effort: 'HIGH',
        impact: 'HIGH',
        confidence: 1.0
      },
      confidence: 0.75,
      needsHumanReview: true,
      rationale: 'Task breakdown is a PROPOSAL. Team MUST review, challenge, and estimate using Planning Poker. All current estimates are TBD.',
      nextSteps: [
        '1. Schedule Planning Poker session with team',
        '2. Review and challenge epic/feature/story breakdown',
        '3. Estimate all stories using Planning Poker',
        '4. Validate dependencies and priorities',
        '5. Create Sprint 1 backlog',
        '6. Assign tasks to team members'
      ],
      outputFormat: input.options?.outputFormat || OutputFormat.MARKDOWN,
      formattedOutput: formatTasksMarkdown(result)
    };

    return output;
  } catch (error) {
    const duration = Date.now() - startTime;

    // Return error output
    return {
      commandId: `tasks-error-${Date.now()}`,
      command: SlashCommandType.TASKS,
      status: CommandStatus.FAILED,
      executedBy: 'Felix (Feature Architect)',
      executedAt: new Date(),
      completedAt: new Date(),
      duration,
      analysis: {
        summary: `Task generation failed: ${error instanceof Error ? error.message : String(error)}`,
        issues: [{
          id: 'tasks-error',
          severity: 'CRITICAL',
          category: 'Execution Error',
          title: 'Task generation failed',
          description: error instanceof Error ? error.message : String(error),
          location: 'Tasks Command',
          recommendation: 'Ensure specification is provided in context and valid',
          autoFixable: false
        }]
      },
      recommendations: [],
      confidence: 0,
      needsHumanReview: true,
      rationale: 'Execution failed',
      outputFormat: OutputFormat.TEXT,
      formattedOutput: `Error: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

// ============================================================================
// COMMAND REGISTRATION
// ============================================================================

/**
 * Register /tasks command with the command registry
 */
export function registerTasksCommand(): void {
  registerCommand(TASKS_DEFINITION, executeTasksCommand);
}
