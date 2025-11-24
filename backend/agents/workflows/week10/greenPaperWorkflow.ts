/**
 * Green-Paper Workflow - BMAD Constitution Generation
 *
 * KaibanJS workflow for generating project constitutions from BMAD answers.
 *
 * Agents involved:
 * - Peter (Product Owner) - Analyzes BMAD answers and generates constitution
 * - Diana (Documentation Writer) - Formats constitution documentation
 *
 * Work Type: NEW_FEATURE (Spec-Kit Pipeline)
 * Trigger: User completes 6 BMAD questions
 * Output: Project Constitution (ready for user approval)
 */

import { Agent, Task, Team } from 'kaibanjs';

// ========== Agent Definitions ==========

/**
 * Peter - Product Owner
 * Model: deepseek-r1:latest (local via Ollama)
 * Specialty: Requirements analysis, stakeholder management, product vision
 */
const peter = new Agent({
  name: 'Peter',
  role: 'Product Owner',
  goal: 'Analyze BMAD green-paper answers and generate comprehensive project constitution',
  background: 'Product management expert with deep understanding of business analysis and stakeholder needs',
  tools: [], // TODO: Add tools as needed
  llmConfig: {
    provider: 'ollama',
    model: 'deepseek-r1:latest',
    temperature: 0.7,
    maxTokens: 4000
  }
});

/**
 * Diana - Documentation Writer
 * Model: mistral:latest (local via Ollama)
 * Specialty: Technical documentation, clear communication
 */
const diana = new Agent({
  name: 'Diana',
  role: 'Documentation Writer',
  goal: 'Format constitution into clear, structured documentation',
  background: 'Technical writing expert who creates clear, accessible documentation',
  tools: [], // TODO: Add tools as needed
  llmConfig: {
    provider: 'ollama',
    model: 'mistral:latest',
    temperature: 0.5,
    maxTokens: 3000
  }
});

// ========== Task Definitions ==========

/**
 * Task 1: Analyze BMAD Answers
 * Agent: Peter
 * Input: 6 BMAD question answers
 * Output: Structured analysis
 */
const analyzeBMADAnswers = new Task({
  name: 'Analyze BMAD Answers',
  description: `
    Analyze the 6 BMAD green-paper question answers provided by the user.

    BMAD Answers:
    - Q1 (Problem): {bmad_answer_1}
    - Q2 (Users/Stakeholders): {bmad_answer_2}
    - Q3 (Core Functionalities): {bmad_answer_3}
    - Q4 (Success Criteria): {bmad_answer_4}
    - Q5 (Technical Constraints): {bmad_answer_5}
    - Q6 (Timeline): {bmad_answer_6}

    Your analysis should:
    1. Extract key insights from each answer
    2. Identify patterns and connections between answers
    3. Flag any contradictions or missing information
    4. Prepare structured data for constitution generation
  `,
  expectedOutput: `
    JSON object with:
    - problem_insights: Key points from Q1
    - stakeholder_groups: Parsed stakeholder list from Q2
    - functionality_list: Categorized functionalities from Q3
    - measurable_criteria: Extracted metrics from Q4
    - constraints: Listed constraints from Q5
    - timeline_estimate: Parsed timeline from Q6
    - contradictions: Any conflicts found
    - missing_info: Gaps that need addressing
  `,
  agent: peter
});

/**
 * Task 2: Generate Constitution Sections
 * Agent: Peter
 * Input: Analysis from Task 1
 * Output: Constitution content
 */
const generateConstitution = new Task({
  name: 'Generate Constitution',
  description: `
    Using the BMAD analysis, generate a comprehensive PROJECT CONSTITUTION.

    Follow the constitution template structure:

    1. PROBLEM STATEMENT (150-250 words)
       - Expand on the problem from Q1
       - Add context and quantify impact
       - Identify root causes

    2. STAKEHOLDERS ANALYSIS (100-200 words)
       - Parse Q2 into structured stakeholder list
       - For each: role, needs, priority, success definition

    3. CORE FUNCTIONALITIES BREAKDOWN (200-400 words)
       - Parse Q3 into structured functionality list
       - For each: name, description, priority (Must/Should/Could), related stakeholder
       - Identify dependencies

    4. SUCCESS CRITERIA (150-250 words)
       - Parse Q4 into SMART criteria
       - For each: metric, target, measurement method, timeframe

    5. TECHNICAL CONSTRAINTS (100-150 words)
       - Parse Q5 (or note "None specified")
       - For each: constraint, reason, impact level

    6. TIMELINE & MILESTONES (150-200 words)
       - Parse Q6 or propose timeline based on scope
       - Break into phases: Discovery, MVP, Beta, Release
       - Define 3-5 milestones with deliverables

    7. RISKS & ASSUMPTIONS (100-150 words)
       - Identify 3-5 key risks
       - State assumptions
       - Suggest mitigations

    REQUIREMENTS:
    - Total: 1000-1500 words
    - Format: Structured JSON
    - Tone: Professional, clear, actionable
    - SMART criteria: All success criteria must be measurable
  `,
  expectedOutput: `
    Complete constitution JSON matching the Constitution data model:
    {
      "content": {
        "problem_statement": "...",
        "stakeholders": [...],
        "core_functionalities": [...],
        "success_criteria": [...],
        "technical_constraints": [...],
        "timeline": {...},
        "risks_and_assumptions": {...}
      },
      "metadata": {
        "generated_by": "Peter",
        "generation_method": "BMAD_green_paper",
        "llm_model": "deepseek-r1:latest",
        "word_count": 1250
      }
    }
  `,
  agent: peter,
  dependencies: [analyzeBMADAnswers]
});

/**
 * Task 3: Format Constitution Documentation
 * Agent: Diana
 * Input: Constitution from Task 2
 * Output: Markdown documentation
 */
const formatConstitutionDocs = new Task({
  name: 'Format Constitution Documentation',
  description: `
    Format the generated constitution into clear, readable Markdown documentation.

    Create two versions:
    1. Full constitution document (all sections)
    2. Executive summary (1-page overview)

    Use proper Markdown formatting:
    - Clear headings (# ## ###)
    - Bullet points for lists
    - Tables for structured data
    - Callout blocks for important notes
    - Links to related sections

    Ensure:
    - Easy to scan and read
    - Professional formatting
    - Consistent style
    - No technical jargon (or explain when necessary)
  `,
  expectedOutput: `
    Two Markdown documents:
    1. Full constitution (constitution_full.md)
    2. Executive summary (constitution_summary.md)

    Both properly formatted and ready for user review.
  `,
  agent: diana,
  dependencies: [generateConstitution]
});

// ========== Workflow Definition ==========

/**
 * Green-Paper Workflow Team
 *
 * Sequential workflow:
 * 1. Peter analyzes BMAD answers
 * 2. Peter generates constitution
 * 3. Diana formats documentation
 *
 * Total estimated time: 3-5 minutes (local AI)
 */
export const greenPaperWorkflow = new Team({
  name: 'Green-Paper Constitution Generation',
  agents: [peter, diana],
  tasks: [
    analyzeBMADAnswers,
    generateConstitution,
    formatConstitutionDocs
  ],
  env: {
    OLLAMA_BASE_URL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
  },
  inputs: {
    // BMAD answers provided by API
    bmad_answer_1: '',  // Problem statement
    bmad_answer_2: '',  // Users/Stakeholders
    bmad_answer_3: '',  // Core functionalities
    bmad_answer_4: '',  // Success criteria
    bmad_answer_5: '',  // Technical constraints (optional)
    bmad_answer_6: ''   // Timeline (optional)
  },
  // TODO: Add quality gates integration
  // TODO: Add retry mechanism (max 3 attempts)
  // TODO: Add peer assistance (if Peter blocked, consult Felix)
});

// ========== Workflow Execution ==========

/**
 * Execute green-paper workflow
 *
 * @param bmadAnswers - Object with answers to 6 BMAD questions
 * @returns Constitution and formatted documentation
 */
export async function executeGreenPaperWorkflow(
  bmadAnswers: {
    answer_1: string;
    answer_2: string;
    answer_3: string;
    answer_4: string;
    answer_5?: string;
    answer_6?: string;
  }
) {
  // Set inputs
  greenPaperWorkflow.inputs = {
    bmad_answer_1: bmadAnswers.answer_1,
    bmad_answer_2: bmadAnswers.answer_2,
    bmad_answer_3: bmadAnswers.answer_3,
    bmad_answer_4: bmadAnswers.answer_4,
    bmad_answer_5: bmadAnswers.answer_5 || 'None specified',
    bmad_answer_6: bmadAnswers.answer_6 || 'Flexible timeline'
  };

  // Execute workflow
  const result = await greenPaperWorkflow.start();

  return result;
}

// ========== Validation Checkpoint ==========

/**
 * Progressive validation checkpoint
 *
 * After constitution generation, pause for user review.
 * User can:
 * - Approve → Proceed to Felix for specification
 * - Reject → Regenerate with feedback (max 3 attempts)
 */
export interface ConstitutionValidation {
  action: 'approve' | 'reject';
  feedback: string;
  requested_changes?: Array<{
    section: string;
    field: string;
    current_value: string;
    suggested_value: string;
    reason: string;
  }>;
}

/**
 * Handle constitution validation result
 */
export async function handleConstitutionValidation(
  validation: ConstitutionValidation,
  constitutionId: string
): Promise<{
  next_step: string;
  workflow_id?: string;
}> {
  if (validation.action === 'approve') {
    return {
      next_step: 'generate_specification',
      workflow_id: '' // TODO: Trigger Felix specification workflow
    };
  } else {
    // Reject - regenerate with feedback
    // TODO: Implement regeneration with requested changes
    return {
      next_step: 'regenerate_constitution'
    };
  }
}

// ========== Export ==========

export default {
  workflow: greenPaperWorkflow,
  execute: executeGreenPaperWorkflow,
  validate: handleConstitutionValidation
};
