/**
 * Workflow Integration Tests
 *
 * Tests the complete integration of:
 * 1. Spec-Kit workflow (constitution → specification → tasks)
 * 2. Command registry (3 new commands)
 * 3. ProjectDefinition workflow using Spec-Kit
 *
 * Week 8 Day 5 - Jest Integration Testing
 */

import { executeConstitution } from '../constitutionCommand';
import { executeSpecification } from '../specifyCommand';
import { executeTasks } from '../tasksCommand';
import { executeSpecKitWorkflow } from '../../workflows/specKitWorkflow';
import { executeProjectDefinitionWorkflow, validateProjectDefinitionRequest } from '../../workflows/projectDefinitionWorkflow';
import { Agent } from 'kaibanjs';
import { SAMPLE_BUSINESS_CASE_1 } from './testData';

// Mock agent
const mockAgent: Agent = {
  name: 'Test Agent',
  role: 'Integration Tester',
  goal: 'Test workflow integration',
  background: 'Mock agent for testing'
} as Agent;

// ========================================
// TEST SUITE 1: Spec-Kit Workflow Pipeline
// ========================================

describe('Spec-Kit Workflow Pipeline', () => {
  let constitutionResult: any;
  let specificationResult: any;
  let tasksResult: any;

  test('Stage 1: Constitution generation', async () => {
    constitutionResult = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    expect(constitutionResult).toBeDefined();
    expect(constitutionResult.principles).toBeDefined();
    expect(Array.isArray(constitutionResult.principles)).toBe(true);
    expect(constitutionResult.principles.length).toBeGreaterThan(0);

    expect(constitutionResult.requirements).toBeDefined();
    expect(constitutionResult.constraints).toBeDefined();
    expect(constitutionResult.risks).toBeDefined();
    expect(constitutionResult.scope).toBeDefined();
  });

  test('Stage 2: Specification from constitution', async () => {
    expect(constitutionResult).toBeDefined();

    specificationResult = await executeSpecification(
      {
        constitution: constitutionResult,
        technicalContext: SAMPLE_BUSINESS_CASE_1.technicalContext || {}
      },
      mockAgent
    );

    expect(specificationResult).toBeDefined();
    expect(specificationResult.architecture).toBeDefined();
    expect(specificationResult.architecture.pattern).toBeDefined();

    expect(specificationResult.components).toBeDefined();
    expect(Array.isArray(specificationResult.components)).toBe(true);

    expect(specificationResult.interfaces).toBeDefined();
    expect(Array.isArray(specificationResult.interfaces)).toBe(true);

    expect(specificationResult.dataModel).toBeDefined();
    expect(specificationResult.dataModel.entities).toBeDefined();
  });

  test('Stage 3: Tasks from specification', async () => {
    expect(specificationResult).toBeDefined();

    tasksResult = await executeTasks(
      { specification: specificationResult },
      mockAgent
    );

    expect(tasksResult).toBeDefined();
    expect(tasksResult.epics).toBeDefined();
    expect(Array.isArray(tasksResult.epics)).toBe(true);
    expect(tasksResult.epics.length).toBeGreaterThan(0);

    expect(tasksResult.features).toBeDefined();
    expect(Array.isArray(tasksResult.features)).toBe(true);

    expect(tasksResult.stories).toBeDefined();
    expect(Array.isArray(tasksResult.stories)).toBe(true);

    expect(tasksResult.tasks).toBeDefined();
    expect(Array.isArray(tasksResult.tasks)).toBe(true);

    // Verify Planning Poker enforcement
    tasksResult.epics.forEach((epic: any) => {
      expect([0, null, undefined, 'TBD']).toContain(epic.storyPoints);
    });
  });

  test('Complete 3-stage workflow', async () => {
    const completeResult = await executeSpecKitWorkflow({
      businessCase: SAMPLE_BUSINESS_CASE_1.businessCase,
      stakeholders: SAMPLE_BUSINESS_CASE_1.stakeholders,
      constraints: SAMPLE_BUSINESS_CASE_1.constraints,
      successCriteria: SAMPLE_BUSINESS_CASE_1.successCriteria,
      technicalContext: SAMPLE_BUSINESS_CASE_1.technicalContext
    });

    expect(completeResult).toBeDefined();
    expect(completeResult.constitution).toBeDefined();
    expect(completeResult.specification).toBeDefined();
    expect(completeResult.tasks).toBeDefined();
    expect(completeResult.files).toBeDefined();
    expect(Array.isArray(completeResult.files)).toBe(true);
    expect(completeResult.files.length).toBeGreaterThanOrEqual(4);
  });
});

// ========================================
// TEST SUITE 2: ProjectDefinition Integration
// ========================================

describe('ProjectDefinition Workflow Integration', () => {
  test('Validation: Valid request passes', () => {
    const validRequest = {
      projectName: 'Test Project',
      description: 'Test description for validation',
      constraints: ['Timeline: 6 months']
    };

    const validation = validateProjectDefinitionRequest(validRequest);

    expect(validation.valid).toBe(true);
    expect(validation.errors.length).toBe(0);
  });

  test('Validation: Missing projectName fails', () => {
    const invalidRequest = {
      projectName: '',
      description: 'Test description'
    };

    const validation = validateProjectDefinitionRequest(invalidRequest);

    expect(validation.valid).toBe(false);
    expect(validation.errors.length).toBeGreaterThan(0);
    expect(validation.errors.some(e => e.includes('name'))).toBe(true);
  });

  test('ProjectDefinition uses Spec-Kit workflow', async () => {
    const projectRequest = {
      projectName: 'Test E-commerce',
      description: SAMPLE_BUSINESS_CASE_1.businessCase,
      businessGoals: SAMPLE_BUSINESS_CASE_1.successCriteria,
      constraints: SAMPLE_BUSINESS_CASE_1.constraints,
      folderPath: '/tmp/test-ecommerce'
    };

    const result = await executeProjectDefinitionWorkflow(projectRequest);

    // Verify all required fields exist
    expect(result).toBeDefined();
    expect(result.project).toBeDefined();
    expect(result.project.name).toBe('Test E-commerce');

    expect(result.architecture).toBeDefined();
    expect(result.architecture.techStack).toBeDefined();
    expect(Array.isArray(result.architecture.techStack)).toBe(true);

    expect(result.epics).toBeDefined();
    expect(Array.isArray(result.epics)).toBe(true);

    expect(result.projectPlan).toBeDefined();
    expect(result.projectPlan.phases).toBeDefined();
    expect(Array.isArray(result.projectPlan.phases)).toBe(true);

    expect(result.documentation).toBeDefined();
    expect(result.folderStructure).toBeDefined();
  }, 60000); // 60 second timeout for complete workflow

  test('ProjectDefinition epic estimates are TBD', async () => {
    const projectRequest = {
      projectName: 'Test Project',
      description: 'Test description for Planning Poker verification',
      constraints: ['Timeline: 6 months'],
      businessGoals: ['Deliver value to users']
    };

    const result = await executeProjectDefinitionWorkflow(projectRequest);

    // All estimates should be 0 (TBD) - team must use Planning Poker
    expect(result.epics).toBeDefined();
    expect(Array.isArray(result.epics)).toBe(true);

    result.epics.forEach(epic => {
      expect(epic.estimatedEffort).toBe(0); // Must be 0 (TBD)
    });
  }, 60000); // 60 second timeout
});

// ========================================
// TEST SUITE 3: Data Flow Integrity
// ========================================

describe('Data Flow Integrity', () => {
  test('Constitution → Specification flow', async () => {
    const constitution = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    const specification = await executeSpecification(
      {
        constitution: constitution,
        technicalContext: SAMPLE_BUSINESS_CASE_1.technicalContext || {}
      },
      mockAgent
    );

    // Verify constitution principles influence architecture
    expect(specification.architecture).toBeDefined();
    expect(constitution.principles.length).toBeGreaterThan(0);
  });

  test('Specification → Epic mapping', async () => {
    const constitution = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);
    const specification = await executeSpecification(
      { constitution, technicalContext: {} },
      mockAgent
    );

    const tasks = await executeTasks({ specification }, mockAgent);

    // Each epic should roughly map to major components
    expect(tasks.epics).toBeDefined();
    expect(tasks.epics.length).toBeGreaterThan(0);
    expect(specification.components.length).toBeGreaterThan(0);
  });

  test('Epic-Feature-Story-Task hierarchy', async () => {
    const constitution = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);
    const specification = await executeSpecification(
      { constitution, technicalContext: {} },
      mockAgent
    );

    const tasks = await executeTasks({ specification }, mockAgent);

    // Verify hierarchy exists
    expect(tasks.epics.length).toBeGreaterThan(0);
    expect(tasks.features.length).toBeGreaterThanOrEqual(tasks.epics.length);
    expect(tasks.stories.length).toBeGreaterThanOrEqual(tasks.features.length);
    expect(tasks.tasks.length).toBeGreaterThanOrEqual(tasks.stories.length);
  });
});
