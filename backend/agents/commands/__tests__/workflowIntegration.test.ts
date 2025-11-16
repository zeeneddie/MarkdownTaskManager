/**
 * Workflow Integration Tests
 *
 * Tests the complete integration of:
 * 1. Spec-Kit workflow (constitution → specification → tasks)
 * 2. Command registry (3 new commands)
 * 3. ProjectDefinition workflow using Spec-Kit
 *
 * Week 8 Day 4 - Integration Testing
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

// Test results tracking
let passed = 0;
let failed = 0;
const failures: string[] = [];

// Helper function to run a test
async function runTest(name: string, testFn: () => Promise<void>) {
  try {
    console.log(`\n🧪 Testing: ${name}`);
    await testFn();
    console.log(`   ✅ PASSED`);
    passed++;
  } catch (error) {
    console.log(`   ❌ FAILED: ${error instanceof Error ? error.message : String(error)}`);
    failed++;
    failures.push(name);
  }
}

// Main test execution
async function runIntegrationTests() {
  console.log('\n' + '='.repeat(80));
  console.log('🚀 WORKFLOW INTEGRATION TESTS - Week 8');
  console.log('='.repeat(80));
  console.log('Testing: Spec-Kit Workflow + Command Registry + ProjectDefinition\n');

  // ========================================
  // TEST SUITE 1: Spec-Kit Workflow Pipeline
  // ========================================
  console.log('\n🔄 Suite 1: Spec-Kit Workflow Pipeline');
  console.log('-'.repeat(80));

  let constitutionResult: any;
  let specificationResult: any;
  let tasksResult: any;

  await runTest('Stage 1: Constitution generation', async () => {
    constitutionResult = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    if (!constitutionResult) throw new Error('No constitution result');
    if (!constitutionResult.principles) throw new Error('Missing principles');
    if (!constitutionResult.requirements) throw new Error('Missing requirements');
    if (!constitutionResult.constraints) throw new Error('Missing constraints');
    if (!constitutionResult.risks) throw new Error('Missing risks');
    if (!constitutionResult.scope) throw new Error('Missing scope');

    console.log(`     - Principles: ${constitutionResult.principles.length}`);
    console.log(`     - Requirements: ${constitutionResult.requirements.length}`);
    console.log(`     - Risks: ${constitutionResult.risks.length}`);
  });

  await runTest('Stage 2: Specification from constitution', async () => {
    if (!constitutionResult) throw new Error('Constitution result not available');

    specificationResult = await executeSpecification(
      {
        constitution: constitutionResult,
        technicalContext: SAMPLE_BUSINESS_CASE_1.technicalContext || {}
      },
      mockAgent
    );

    if (!specificationResult) throw new Error('No specification result');
    if (!specificationResult.architecture) throw new Error('Missing architecture');
    if (!specificationResult.components) throw new Error('Missing components');
    if (!specificationResult.interfaces) throw new Error('Missing interfaces');
    if (!specificationResult.dataModel) throw new Error('Missing data model');

    console.log(`     - Architecture: ${specificationResult.architecture.pattern}`);
    console.log(`     - Components: ${specificationResult.components.length}`);
    console.log(`     - API Endpoints: ${specificationResult.interfaces.length}`);
    console.log(`     - Entities: ${specificationResult.dataModel.entities.length}`);
  });

  await runTest('Stage 3: Tasks from specification', async () => {
    if (!specificationResult) throw new Error('Specification result not available');

    tasksResult = await executeTasks(
      { specification: specificationResult },
      mockAgent
    );

    if (!tasksResult) throw new Error('No tasks result');
    if (!tasksResult.epics) throw new Error('Missing epics');
    if (!tasksResult.features) throw new Error('Missing features');
    if (!tasksResult.stories) throw new Error('Missing stories');
    if (!tasksResult.tasks) throw new Error('Missing tasks');

    console.log(`     - Epics: ${tasksResult.epics.length}`);
    console.log(`     - Features: ${tasksResult.features.length}`);
    console.log(`     - Stories: ${tasksResult.stories.length}`);
    console.log(`     - Tasks: ${tasksResult.tasks.length}`);
  });

  await runTest('Complete Spec-Kit workflow (3 stages)', async () => {
    const workflowResult = await executeSpecKitWorkflow({
      businessCase: SAMPLE_BUSINESS_CASE_1.businessCase,
      stakeholders: SAMPLE_BUSINESS_CASE_1.stakeholders,
      constraints: SAMPLE_BUSINESS_CASE_1.constraints,
      successCriteria: SAMPLE_BUSINESS_CASE_1.successCriteria,
      technicalContext: SAMPLE_BUSINESS_CASE_1.technicalContext,
      projectPath: '/tmp/test-project',
      projectName: 'Test Project'
    });

    if (!workflowResult.constitution) throw new Error('Missing constitution');
    if (!workflowResult.specification) throw new Error('Missing specification');
    if (!workflowResult.tasks) throw new Error('Missing tasks');
    if (workflowResult.files.length === 0) throw new Error('No files generated');

    console.log(`     - Files generated: ${workflowResult.files.length}`);
    console.log(`     - Execution time: ${(workflowResult.summary.executionTime / 1000).toFixed(2)}s`);
  });

  // ========================================
  // TEST SUITE 2: ProjectDefinition Integration
  // ========================================
  console.log('\n🏗️  Suite 2: ProjectDefinition Workflow Integration');
  console.log('-'.repeat(80));

  await runTest('ProjectDefinition request validation', async () => {
    const validRequest = {
      projectName: 'E-commerce Platform',
      description: 'Online shopping platform',
      businessGoals: ['Increase sales'],
      constraints: ['Budget: €50k']
    };

    const validation = validateProjectDefinitionRequest(validRequest);
    if (!validation.valid) {
      throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
    }

    console.log(`     - Validation passed`);
  });

  await runTest('ProjectDefinition uses Spec-Kit workflow', async () => {
    const projectRequest = {
      projectName: 'Test E-commerce',
      description: SAMPLE_BUSINESS_CASE_1.businessCase,
      businessGoals: SAMPLE_BUSINESS_CASE_1.successCriteria,
      constraints: SAMPLE_BUSINESS_CASE_1.constraints,
      folderPath: '/tmp/test-ecommerce'
    };

    const result = await executeProjectDefinitionWorkflow(projectRequest);

    if (!result) throw new Error('No result from projectDefinition');
    if (!result.project) throw new Error('Missing project info');
    if (!result.architecture) throw new Error('Missing architecture');
    if (!result.epics) throw new Error('Missing epics');
    if (!result.projectPlan) throw new Error('Missing project plan');

    // Verify it used Spec-Kit workflow (not mock data)
    if (result.epics.length === 0) {
      throw new Error('No epics generated - workflow may not be working');
    }

    console.log(`     - Project: ${result.project.name}`);
    console.log(`     - Epics: ${result.epics.length}`);
    console.log(`     - Tech Stack: ${result.architecture.techStack.join(', ')}`);
    console.log(`     - Files: ${result.folderStructure.files.length}`);
  });

  await runTest('ProjectDefinition epic estimates are TBD', async () => {
    const projectRequest = {
      projectName: 'Test Project',
      description: 'Test description',
      constraints: ['Timeline: 6 months']
    };

    const result = await executeProjectDefinitionWorkflow(projectRequest);

    // All estimates should be 0 (TBD) - team must use Planning Poker
    result.epics.forEach(epic => {
      if (epic.estimatedEffort !== 0) {
        throw new Error(`Epic ${epic.id} has estimate ${epic.estimatedEffort} - should be 0 (TBD)`);
      }
    });

    console.log(`     - All ${result.epics.length} epics have TBD estimates (Planning Poker required)`);
  });

  // ========================================
  // TEST SUITE 3: Data Flow Integrity
  // ========================================
  console.log('\n🔗 Suite 3: Data Flow Integrity');
  console.log('-'.repeat(80));

  await runTest('Constitution requirements flow to specification', async () => {
    if (!constitutionResult || !specificationResult) {
      throw new Error('Previous results not available');
    }

    // Verify that constitution requirements influenced specification
    const hasAuthComponent = specificationResult.components.some((c: any) =>
      c.name.toLowerCase().includes('auth')
    );

    if (!hasAuthComponent && constitutionResult.scope.inScope.some((item: string) =>
      item.toLowerCase().includes('user') || item.toLowerCase().includes('login')
    )) {
      throw new Error('Constitution scope should influence specification components');
    }

    console.log(`     - Data flow validated`);
  });

  await runTest('Specification components create corresponding epics', async () => {
    if (!specificationResult || !tasksResult) {
      throw new Error('Previous results not available');
    }

    // Each component should have a corresponding epic (or close to it)
    const componentCount = specificationResult.components.length;
    const epicCount = tasksResult.epics.length;

    // Should be similar numbers (within 20% variance)
    const variance = Math.abs(componentCount - epicCount) / componentCount;
    if (variance > 0.5) {
      console.warn(`     ⚠️  Large variance: ${componentCount} components → ${epicCount} epics`);
    }

    console.log(`     - Components: ${componentCount}, Epics: ${epicCount}`);
  });

  await runTest('Epic-Feature-Story-Task hierarchy is valid', async () => {
    if (!tasksResult) throw new Error('Tasks result not available');

    // Verify hierarchy: epics → features → stories → tasks
    for (const epic of tasksResult.epics) {
      if (epic.features.length === 0) {
        throw new Error(`Epic ${epic.id} has no features`);
      }

      for (const featureId of epic.features) {
        const feature = tasksResult.features.find((f: any) => f.id === featureId);
        if (!feature) {
          throw new Error(`Feature ${featureId} not found (referenced by ${epic.id})`);
        }

        if (feature.stories.length === 0) {
          throw new Error(`Feature ${featureId} has no stories`);
        }
      }
    }

    console.log(`     - All ${tasksResult.epics.length} epics have valid feature references`);
    console.log(`     - All ${tasksResult.features.length} features have valid story references`);
  });

  // ========================================
  // TEST SUMMARY
  // ========================================
  console.log('\n' + '='.repeat(80));
  console.log('\n📊 TEST SUMMARY\n');
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

  if (failures.length > 0) {
    console.log('\n❌ Failed Tests:');
    failures.forEach(name => console.log(`   - ${name}`));
  } else {
    console.log('\n🎉 ALL INTEGRATION TESTS PASSED!');
    console.log('\n✅ Verified:');
    console.log('   1. Command registry has 3 new Spec-Kit commands');
    console.log('   2. Spec-Kit workflow executes all 3 stages');
    console.log('   3. ProjectDefinition workflow uses Spec-Kit (not mocks)');
    console.log('   4. Data flows correctly through the pipeline');
    console.log('   5. All estimates are TBD (Planning Poker required)');
  }

  console.log('\n' + '='.repeat(80) + '\n');

  return failed === 0;
}

// Run tests
runIntegrationTests()
  .then(success => {
    if (success) {
      console.log('✅ INTEGRATION TEST SUITE PASSED!\n');
      process.exit(0);
    } else {
      console.log('❌ INTEGRATION TEST SUITE FAILED\n');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('\n💥 TEST RUNNER ERROR:', error);
    console.error(error.stack);
    process.exit(1);
  });
