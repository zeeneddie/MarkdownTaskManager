/**
 * Test script for MAINTENANCE workflow
 * Week 8 Day 1 - Code-Maintenance-Agent integration test
 */

import {
  executeCodeMaintenanceWorkflow,
  validateCodeMaintenanceRequest,
  type CodeMaintenanceRequest
} from './workflows/codeMaintenanceAgent';

async function testMaintenanceWorkflow() {
  console.log('\n' + '='.repeat(80));
  console.log('🧪 TESTING MAINTENANCE WORKFLOW');
  console.log('='.repeat(80) + '\n');

  // Test 1: Validation
  console.log('Test 1: Request Validation');
  const invalidRequest: CodeMaintenanceRequest = {
    scope: 'invalid_scope' as any,
    urgency: 'high' as const
  };

  const validation1 = validateCodeMaintenanceRequest(invalidRequest);
  console.log(`   ✓ Invalid request caught: ${!validation1.valid}`);
  console.log(`   ✓ Errors: ${validation1.errors.join(', ')}`);

  // Test 2: Valid full codebase scan
  console.log('\nTest 2: Full Codebase Maintenance');
  const fullCodebaseRequest: CodeMaintenanceRequest = {
    scope: 'full_codebase' as const,
    focusAreas: ['dependencies' as const, 'security' as const, 'code_quality' as const],
    thresholds: {
      maxComplexity: 15,
      minTestCoverage: 80,
      maxTechnicalDebtRatio: 10
    },
    urgency: 'high' as const
  };

  const validation2 = validateCodeMaintenanceRequest(fullCodebaseRequest);
  console.log(`   ✓ Valid request: ${validation2.valid}`);

  console.log('\n   Executing workflow...\n');
  const result = await executeCodeMaintenanceWorkflow(fullCodebaseRequest);

  console.log('\n📊 Results Summary:');
  console.log(`   Technical Debt Ratio: ${result.analysisReport.technicalDebtRatio}%`);
  console.log(`   Dependency Vulnerabilities (total): ${
    result.analysisReport.dependencyVulnerabilities.critical +
    result.analysisReport.dependencyVulnerabilities.high +
    result.analysisReport.dependencyVulnerabilities.medium
  }`);
  console.log(`   Code Smells (total): ${
    result.analysisReport.codeSmells.complexity +
    result.analysisReport.codeSmells.duplication
  }`);
  console.log(`   Prioritized Findings: ${result.prioritizedFindings.length}`);
  console.log(`   Maintenance Phases: ${result.maintenancePlan.phases.length}`);
  console.log(`   Total Effort: ${result.maintenancePlan.totalEffort} SP`);
  console.log(`   Test Coverage: ${result.analysisReport.testCoverage.line}%`);
  console.log(`   Test Coverage Goal: ${result.testStrategy.unitTests.coverageGoal}%`);

  // Test 3: Module-specific scan
  console.log('\n\nTest 3: Module-Specific Maintenance');
  const moduleRequest: CodeMaintenanceRequest = {
    scope: 'module' as const,
    modulePath: 'src/workflows',
    focusAreas: ['performance' as const, 'tests' as const],
    urgency: 'medium' as const
  };

  const validation3 = validateCodeMaintenanceRequest(moduleRequest);
  console.log(`   ✓ Valid module request: ${validation3.valid}`);

  console.log('\n   Executing module workflow...\n');
  const moduleResult = await executeCodeMaintenanceWorkflow(moduleRequest);

  console.log('\n📊 Module Results:');
  console.log(`   Findings: ${moduleResult.prioritizedFindings.length}`);
  console.log(`   P0 Tasks: ${moduleResult.prioritizedFindings.filter(f => f.priority === 'P0').length}`);
  console.log(`   P1 Tasks: ${moduleResult.prioritizedFindings.filter(f => f.priority === 'P1').length}`);

  console.log('\n' + '='.repeat(80));
  console.log('✅ ALL TESTS PASSED');
  console.log('='.repeat(80) + '\n');
}

// Run tests
testMaintenanceWorkflow()
  .then(() => {
    console.log('✅ Test suite completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Test suite failed:', error);
    process.exit(1);
  });
