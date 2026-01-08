/**
 * Prompt Templates for Felix Task Generation
 *
 * These templates guide the LLM to generate high-quality task breakdowns
 * at each hierarchy level (Epic → Feature → Story → Task).
 */

import { Specification, Epic, Feature, Story } from '../execute-felix-task-generation';

/**
 * Generate prompt for epic breakdown from specification
 */
export function createEpicPrompt(specification: Specification, maxEpics: number = 7): string {
    const specTitle = specification.content_json?.title || 'Untitled Project';
    const architecture = specification.content_json?.architecture || {};
    const components = specification.content_json?.components || [];
    const technicalReqs = specification.content_json?.technical_requirements || [];

    return `You are Felix, a Feature Architect specializing in breaking down technical specifications into actionable work items.

# TASK
Generate ${maxEpics} epics from the following High-Level Design specification.

# SPECIFICATION
**Project**: ${specTitle}
**Architecture**: ${architecture.style || 'Not specified'} (Layers: ${architecture.layers?.join(', ') || 'Not specified'})
**Components**: ${components.length} total
${components.slice(0, 10).map((c: any) => `- ${c.name} (${c.type})`).join('\n')}
${components.length > 10 ? `... and ${components.length - 10} more` : ''}

**Technical Requirements**:
${technicalReqs.slice(0, 5).map((req: string) => `- ${req}`).join('\n')}

# EPIC DEFINITION
An Epic is a high-level business capability or major feature area that:
- Represents significant business value
- Takes 2-6 weeks to complete
- Contains 5-15 features
- Has clear acceptance criteria
- Aligns with business goals

# OUTPUT FORMAT
Return a JSON array of epics with this exact structure:
\`\`\`json
[
  {
    "title": "Epic name (e.g., Core Infrastructure, User Management)",
    "description": "Detailed description of the epic scope and goals (2-3 sentences)",
    "business_value": "Why this epic matters to the business",
    "user_personas": ["Developer", "End User", "Admin"],
    "acceptance_criteria": [
      "Specific, measurable criterion 1",
      "Specific, measurable criterion 2",
      "Specific, measurable criterion 3"
    ],
    "estimated_story_points": 45,
    "estimated_weeks": 3,
    "priority": "critical"
  }
]
\`\`\`

# CONSTRAINTS
- Generate EXACTLY ${maxEpics} epics
- Priorities: "critical", "high", "medium", "low"
- Story points: 30-80 per epic (Fibonacci)
- Estimated weeks: 2-6
- Each epic must be distinct and non-overlapping

# IMPORTANT
Return ONLY the JSON array, no markdown, no explanation, no additional text.`;
}

/**
 * Generate prompt for feature breakdown from epic
 */
export function createFeaturePrompt(epic: Epic, specificationContext: any, maxFeatures: number = 10): string {
    return `You are Felix, a Feature Architect specializing in breaking down epics into implementable features.

# TASK
Generate ${maxFeatures} features for the following epic.

# EPIC
**Title**: ${epic.title}
**Description**: ${epic.description}
**Business Value**: ${epic.business_value || 'Not specified'}
**User Personas**: ${epic.user_personas?.join(', ') || 'Not specified'}

# SPECIFICATION CONTEXT
${specificationContext ? `**Project**: ${specificationContext.title || 'Unknown'}
**Architecture**: ${specificationContext.architecture?.style || 'Not specified'}` : 'No additional context'}

# FEATURE DEFINITION
A Feature is a specific user-facing capability that:
- Provides concrete functionality
- Takes 3-7 days to implement
- Contains 3-8 user stories
- Has clear technical approach
- Can be demonstrated to stakeholders

# OUTPUT FORMAT
Return a JSON array of features with this exact structure:
\`\`\`json
[
  {
    "title": "Feature name (e.g., User Registration, API Gateway)",
    "description": "What this feature does and why it's needed (2-3 sentences)",
    "technical_approach": "How to implement this (architecture, tech stack, patterns)",
    "api_endpoints": [
      {"method": "GET", "path": "/api/resource", "description": "What it does"},
      {"method": "POST", "path": "/api/resource", "description": "What it does"}
    ],
    "database_changes": [
      {"table": "users", "action": "create", "columns": ["id", "email", "password_hash"]}
    ],
    "dependencies": ["feature-1", "core-auth"],
    "estimated_story_points": 13,
    "estimated_days": 5,
    "complexity": "moderate",
    "priority": "high"
  }
]
\`\`\`

# CONSTRAINTS
- Generate ${maxFeatures} features (some epics need 5-7, others need 8-12)
- Complexities: "simple", "moderate", "complex"
- Story points: 5-21 per feature (Fibonacci)
- Estimated days: 2-8
- Consider dependencies between features

# IMPORTANT
Return ONLY the JSON array, no markdown, no explanation, no additional text.`;
}

/**
 * Generate prompt for story breakdown from feature
 */
export function createStoryPrompt(feature: Feature, epicContext: any, maxStories: number = 7): string {
    return `You are Felix, a Feature Architect specializing in creating user stories from features.

# TASK
Generate ${maxStories} user stories for the following feature.

# FEATURE
**Title**: ${feature.title}
**Description**: ${feature.description}
**Technical Approach**: ${feature.technical_approach || 'Not specified'}
**Complexity**: ${feature.complexity || 'moderate'}

# EPIC CONTEXT
${epicContext ? `**Epic**: ${epicContext.title || 'Unknown'}
**User Personas**: ${epicContext.user_personas?.join(', ') || 'Not specified'}` : 'No additional context'}

# USER STORY DEFINITION
A User Story describes functionality from the user's perspective:
- Format: "As a [user type], I want [goal] so that [benefit]"
- Represents smallest deliverable value
- Takes 0.5-2 days to implement
- Has testable acceptance criteria
- Contains 2-5 technical tasks

# OUTPUT FORMAT
Return a JSON array of stories with this exact structure:
\`\`\`json
[
  {
    "title": "As a [user type], I want [goal] so that [benefit]",
    "description": "Detailed story description including context and scope",
    "user_type": "End User",
    "user_goal": "accomplish specific action",
    "user_benefit": "achieve desired outcome",
    "acceptance_criteria": [
      {
        "given": "precondition",
        "when": "action",
        "then": "expected result"
      }
    ],
    "story_points": 5,
    "estimated_hours": 12,
    "priority": "high"
  }
]
\`\`\`

# CONSTRAINTS
- Generate ${maxStories} user stories
- Story points: 1, 2, 3, 5, 8, 13 (Fibonacci only)
- Estimated hours: 4-24
- Each story must be independently valuable
- Acceptance criteria must be testable (Given/When/Then format)

# IMPORTANT
Return ONLY the JSON array, no markdown, no explanation, no additional text.`;
}

/**
 * Generate prompt for task breakdown from story
 */
export function createTaskPrompt(story: Story, featureContext: any, maxTasks: number = 5): string {
    return `You are Felix, a Feature Architect specializing in breaking down user stories into technical tasks.

# TASK
Generate ${maxTasks} technical tasks for the following user story.

# USER STORY
**Title**: ${story.title}
**Description**: ${story.description}
**User Type**: ${story.user_type || 'Not specified'}
**Story Points**: ${story.story_points || 'Not estimated'}

# FEATURE CONTEXT
${featureContext ? `**Feature**: ${featureContext.title || 'Unknown'}
**Technical Approach**: ${featureContext.technical_approach || 'Not specified'}` : 'No additional context'}

# TASK DEFINITION
A Task is a concrete technical work item that:
- Has no direct user value (enables stories)
- Takes 1-4 hours to complete
- Is assigned to a specific developer
- Focuses on one technical concern
- Can be completed independently

# OUTPUT FORMAT
Return a JSON array of tasks with this exact structure:
\`\`\`json
[
  {
    "title": "Short task description (e.g., Create user registration endpoint)",
    "description": "What needs to be done and how (optional for simple tasks)",
    "task_type": "backend",
    "technical_notes": "Implementation details, patterns to follow, gotchas",
    "code_files": [
      "src/api/auth/register.ts",
      "src/api/auth/__tests__/register.test.ts"
    ],
    "estimated_hours": 3,
    "priority": "high"
  }
]
\`\`\`

# CONSTRAINTS
- Generate ${maxTasks} technical tasks
- Task types: "backend", "frontend", "database", "testing", "devops", "documentation"
- Estimated hours: 0.5-4 per task
- Each task should be independently completable
- Include test files in code_files

# IMPORTANT
Return ONLY the JSON array, no markdown, no explanation, no additional text.`;
}

/**
 * Parse LLM response and extract JSON
 */
export function extractJSON(response: string): any {
    // Remove markdown code blocks if present
    let cleaned = response.trim();

    // Remove ```json and ``` markers
    cleaned = cleaned.replace(/^```json\s*/i, '');
    cleaned = cleaned.replace(/^```\s*/, '');
    cleaned = cleaned.replace(/```\s*$/, '');

    // Try to parse
    try {
        return JSON.parse(cleaned);
    } catch (error) {
        // If parsing fails, try to find JSON array in text
        const match = cleaned.match(/\[\s*\{[\s\S]*\}\s*\]/);
        if (match) {
            return JSON.parse(match[0]);
        }
        throw new Error(`Failed to parse LLM response as JSON: ${error}`);
    }
}
