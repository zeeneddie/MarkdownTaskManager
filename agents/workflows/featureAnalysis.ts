/**
 * Feature Analysis Workflow
 *
 * This workflow demonstrates how agents work together to analyze
 * a new feature request and break it down into tasks.
 */

import { Task, Team } from 'kaibanjs';
import { agents } from '../configs/agents';

/**
 * Example workflow: Analyze a new feature request
 *
 * Process:
 * 1. Feature Architect analyzes requirements
 * 2. Quality Inspector reviews the analysis
 * 3. Estimation Engine calculates story points
 * 4. Test Engineer defines test scenarios
 * 5. Documentation Writer creates specifications
 */
export function createFeatureAnalysisWorkflow(featureDescription: string) {
  // Task 1: Analyze feature requirements
  const analyzeTask = new Task({
    description: 'Analyze the feature request: {featureDescription}. Break it down into components and identify dependencies.',
    expectedOutput: 'Structured breakdown with Epic, Features, Stories, and Tasks in JSON format',
    agent: agents.featureArchitect
  });

  // Task 2: Quality review
  const qualityReviewTask = new Task({
    description: 'Review the feature breakdown from task 1: {taskResult:task1}. Identify potential quality issues, risks, and best practices.',
    expectedOutput: 'Quality assessment report with recommendations',
    agent: agents.qualityInspector
  });

  // Task 3: Estimation
  const estimationTask = new Task({
    description: 'Estimate story points for the breakdown: {taskResult:task1}. Consider complexity, uncertainty, and effort.',
    expectedOutput: 'Story point estimates for each item with justification',
    agent: agents.estimationEngine
  });

  // Task 4: Test scenarios
  const testScenariosTask = new Task({
    description: 'Generate test scenarios for the feature: {taskResult:task1}. Include unit tests, integration tests, and E2E tests.',
    expectedOutput: 'Comprehensive test plan with test cases',
    agent: agents.testEngineer
  });

  // Task 5: Documentation
  const documentationTask = new Task({
    description: 'Create technical documentation based on: {taskResult:task1}. Include architecture overview, API specs, and user guides.',
    expectedOutput: 'Complete technical documentation in markdown format',
    agent: agents.documentationWriter
  });

  // Create team with all agents and tasks
  const team = new Team({
    name: 'Feature Analysis Team',
    agents: [
      agents.featureArchitect,
      agents.qualityInspector,
      agents.estimationEngine,
      agents.testEngineer,
      agents.documentationWriter
    ],
    tasks: [
      analyzeTask,
      qualityReviewTask,
      estimationTask,
      testScenariosTask,
      documentationTask
    ],
    inputs: {
      featureDescription: featureDescription
    },
    memory: true // Enable task result sharing
  });

  return team;
}

/**
 * Execute the feature analysis workflow
 */
export async function analyzeFeature(featureDescription: string) {
  const team = createFeatureAnalysisWorkflow(featureDescription);

  try {
    const output = await team.start();
    return {
      success: true,
      result: output.result
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}
