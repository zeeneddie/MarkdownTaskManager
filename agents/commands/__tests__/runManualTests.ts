/**
 * Manual Test Runner for Constitution Command
 *
 * Runs tests without Jest framework
 *
 * Usage: npx ts-node commands/__tests__/runManualTests.ts
 */

import { executeConstitution, formatConstitutionMarkdown } from '../constitutionCommand';
import {
  SAMPLE_BUSINESS_CASE_1,
  SAMPLE_BUSINESS_CASE_2,
  SAMPLE_BUSINESS_CASE_3
} from './testData';
import { Agent } from 'kaibanjs';

// Mock agent
const mockAgent: Agent = {
  name: 'Peter',
  role: 'Product Owner',
  goal: 'Test constitution generation',
  background: 'Mock agent for testing'
} as Agent;

// Test results
let passed = 0;
let failed = 0;
const failures: string[] = [];

// Helper function to run a test
async function runTest(name: string, testFn: () => Promise<void>) {
  try {
    console.log(`\n🧪 Running: ${name}`);
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
async function runAllTests() {
  console.log('🚀 Starting Manual Constitution Command Tests...\n');
  console.log('=' .repeat(60));

  // Test 1: Basic execution
  await runTest('Constitution generation from customer portal case', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    if (!result) throw new Error('No result returned');
    if (result.principles.length === 0) throw new Error('No principles generated');
    if (result.requirements.length === 0) throw new Error('No requirements generated');
    if (result.constraints.length === 0) throw new Error('No constraints generated');
    if (result.risks.length === 0) throw new Error('No risks generated');
    if (result.scope.inScope.length === 0) throw new Error('No scope defined');

    console.log(`     - Principles: ${result.principles.length}`);
    console.log(`     - Requirements: ${result.requirements.length}`);
    console.log(`     - Constraints: ${result.constraints.length}`);
    console.log(`     - Risks: ${result.risks.length}`);
    console.log(`     - In-scope items: ${result.scope.inScope.length}`);
  });

  // Test 2: Markdown formatting
  await runTest('Markdown formatting', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);
    const markdown = formatConstitutionMarkdown(result);

    if (!markdown.includes('# Project Constitution')) throw new Error('Missing title');
    if (!markdown.includes('## 🏛️ Project Principles')) throw new Error('Missing principles section');
    if (!markdown.includes('## 📋 Requirements')) throw new Error('Missing requirements section');
    if (markdown.length < 500) throw new Error('Markdown too short');

    console.log(`     - Markdown length: ${markdown.length} chars`);
  });

  // Test 3: Security principles detection
  await runTest('Security principles when GDPR mentioned', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    const securityPrinciples = result.principles.filter(p =>
      p.category === 'SECURITY'
    );

    if (securityPrinciples.length === 0) {
      throw new Error('No security principles generated despite GDPR constraint');
    }

    console.log(`     - Security principles: ${securityPrinciples.length}`);
  });

  // Test 4: Requirements extraction
  await runTest('Requirements extraction from business case', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    const functionalReqs = result.requirements.filter(r => r.type === 'FUNCTIONAL');
    const businessReqs = result.requirements.filter(r => r.type === 'BUSINESS');

    if (functionalReqs.length === 0) throw new Error('No functional requirements');
    if (businessReqs.length !== 4) throw new Error('Wrong number of business requirements');

    console.log(`     - Functional: ${functionalReqs.length}`);
    console.log(`     - Business: ${businessReqs.length}`);
  });

  // Test 5: Constraint categorization
  await runTest('Constraint type identification', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    const legalConstraints = result.constraints.filter(c => c.type === 'LEGAL');
    const technicalConstraints = result.constraints.filter(c => c.type === 'TECHNICAL');

    if (legalConstraints.length === 0) throw new Error('No legal constraints (GDPR should be detected)');
    if (technicalConstraints.length === 0) throw new Error('No technical constraints (integration should be detected)');

    console.log(`     - Legal: ${legalConstraints.length}`);
    console.log(`     - Technical: ${technicalConstraints.length}`);
  });

  // Test 6: Risk assessment
  await runTest('Risk identification and scoring', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    const scopeRisk = result.risks.find(r => r.description.toLowerCase().includes('scope'));
    if (!scopeRisk) throw new Error('Scope creep risk not identified');

    const criticalRisks = result.risks.filter(r => r.impact === 'CRITICAL');
    console.log(`     - Total risks: ${result.risks.length}`);
    console.log(`     - Critical risks: ${criticalRisks.length}`);
  });

  // Test 7: Scope and phases
  await runTest('Scope definition and phase planning', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    if (result.scope.phases.length === 0) throw new Error('No phases defined');
    if (result.scope.assumptions.length === 0) throw new Error('No assumptions defined');

    // Check phase ordering
    for (let i = 0; i < result.scope.phases.length - 1; i++) {
      if (result.scope.phases[i].number >= result.scope.phases[i + 1].number) {
        throw new Error('Phases not properly ordered');
      }
    }

    console.log(`     - Phases: ${result.scope.phases.length}`);
    console.log(`     - Assumptions: ${result.scope.assumptions.length}`);
  });

  // Test 8: E-commerce case
  await runTest('E-commerce platform case', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_2, mockAgent);

    if (result.principles.length === 0) throw new Error('No principles');
    if (result.requirements.length === 0) throw new Error('No requirements');

    console.log(`     - Generated successfully`);
  });

  // Test 9: Internal tool case
  await runTest('Internal tool case', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_3, mockAgent);

    if (result.principles.length === 0) throw new Error('No principles');
    if (result.requirements.length === 0) throw new Error('No requirements');

    console.log(`     - Generated successfully`);
  });

  // Test 10: ID generation
  await runTest('ID format validation', async () => {
    const result = await executeConstitution(SAMPLE_BUSINESS_CASE_1, mockAgent);

    // Check principle IDs
    result.principles.forEach(p => {
      if (!/^PRIN-\d{3}$/.test(p.id)) {
        throw new Error(`Invalid principle ID format: ${p.id}`);
      }
    });

    // Check requirement IDs
    result.requirements.forEach(r => {
      if (!/^REQ-\d{3}$/.test(r.id)) {
        throw new Error(`Invalid requirement ID format: ${r.id}`);
      }
    });

    console.log(`     - All IDs valid`);
  });

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('\n📊 TEST SUMMARY\n');
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

  if (failures.length > 0) {
    console.log('\n❌ Failed Tests:');
    failures.forEach(name => console.log(`   - ${name}`));
  }

  console.log('\n' + '='.repeat(60));

  return failed === 0;
}

// Run tests
runAllTests()
  .then(success => {
    if (success) {
      console.log('\n✅ ALL TESTS PASSED!\n');
      process.exit(0);
    } else {
      console.log('\n❌ SOME TESTS FAILED\n');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('\n💥 TEST RUNNER ERROR:', error);
    process.exit(1);
  });
