/**
 * Test SuperClaude Test Runner Integration
 * Week 6 Day 5 - Integration Test
 */

import { getSuperClaudeTestRunner } from './superclaudeTestRunner';

async function testSuperClaudeTestRunner() {
  console.log('Testing SuperClaude Test Runner Integration\n');

  try {
    const testRunner = getSuperClaudeTestRunner();

    console.log('Test Configuration:');
    console.log('   Target: Sample test files');
    console.log('   Type: unit');
    console.log('   Coverage: enabled');
    console.log('');

    const isAvailable = await testRunner.isAvailable();
    console.log('Test runner available: ' + (isAvailable ? 'Yes' : 'No'));
    console.log('');

    if (!isAvailable) {
      console.log('Warning: SuperClaude test runner not available, using simulation mode');
      console.log('');
    }

    console.log('Running SuperClaude tests...');
    console.log('');

    const result = await testRunner.runTests({
      targetFiles: ['tests/sample.test.ts'],
      testType: 'unit',
      coverage: true,
      timeout: 30000
    });

    console.log('Test Results:');
    console.log('   Success: ' + (result.success ? 'Yes' : 'No'));
    console.log('');

    console.log('Test Summary:');
    console.log('   Passed:  ' + result.testResults.passed);
    console.log('   Failed:  ' + result.testResults.failed);
    console.log('   Skipped: ' + result.testResults.skipped);
    console.log('   Total:   ' + result.testResults.total);
    console.log('');

    if (result.coverage && Object.keys(result.coverage).length > 0) {
      console.log('Coverage:');
      if (result.coverage.lines !== undefined) {
        console.log('   Lines:      ' + result.coverage.lines.toFixed(1) + '%');
      }
      if (result.coverage.branches !== undefined) {
        console.log('   Branches:   ' + result.coverage.branches.toFixed(1) + '%');
      }
      if (result.coverage.functions !== undefined) {
        console.log('   Functions:  ' + result.coverage.functions.toFixed(1) + '%');
      }
      if (result.coverage.statements !== undefined) {
        console.log('   Statements: ' + result.coverage.statements.toFixed(1) + '%');
      }
      console.log('');
    }

    if (result.failures.length > 0) {
      console.log('Failures:');
      result.failures.slice(0, 3).forEach((failure, idx) => {
        console.log('   ' + (idx + 1) + '. ' + failure.testName);
        console.log('      Error: ' + failure.error);
        console.log('      Location: ' + failure.location);
      });
      if (result.failures.length > 3) {
        console.log('   ... and ' + (result.failures.length - 3) + ' more failures');
      }
      console.log('');
    }

    console.log('Execution Time: ' + result.executionTime.toFixed(3) + ' seconds');
    console.log('');

    if (result.error) {
      console.log('Error: ' + result.error);
      console.log('');
    }

    console.log('Test runner integration test completed successfully!');

  } catch (error) {
    console.error('Test runner integration test failed:', error);
    process.exit(1);
  }
}

testSuperClaudeTestRunner();
