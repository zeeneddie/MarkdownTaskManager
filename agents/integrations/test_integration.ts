/**
 * Test SuperClaude Integration with QualityGateService
 * Week 6 Day 3 - Integration Test
 */

import { QualityGateService, QualityCheckContext } from '../services/qualityGateService';
import * as path from 'path';

async function testSuperClaudeIntegration() {
  console.log('🧪 Testing SuperClaude Integration with Quality Gates\n');

  try {
    // Create QualityGateService instance
    const qualityGateService = new QualityGateService();

    // Create test context with sample file
    const testContext: QualityCheckContext = {
      scope: 'specific_files',
      targetFiles: [
        path.join(__dirname, '../services/qualityGateService.ts')
      ],
      thresholds: {
        maxComplexity: 15,
        minTestCoverage: 80,
        maxTechnicalDebtRatio: 10,
        maxDuplication: 3
      }
    };

    console.log('📋 Test Context:');
    console.log('   Scope:', testContext.scope);
    console.log('   Target Files:', testContext.targetFiles);
    console.log('');

    // Run post-implementation check (includes SuperClaude)
    console.log('🔍 Running Quality Gate Post-Implementation Check...\n');
    const result = await qualityGateService.checkPostImplementation(testContext);

    // Display results
    console.log('\n📊 Quality Gate Results:');
    console.log('   Passed:', result.passed ? '✅' : '❌');
    console.log('   Blocking:', result.blocking ? '🚫' : '✅');
    console.log('');

    console.log('📈 Summary:');
    console.log('   Total Violations:', result.summary.totalViolations);
    console.log('   Critical:', result.summary.criticalViolations);
    console.log('   High:', result.summary.highViolations);
    console.log('   Medium:', result.summary.mediumViolations);
    console.log('   Low:', result.summary.lowViolations);
    console.log('');

    // Filter SuperClaude findings
    const superclaudeFindings = result.findings.filter(f =>
      f.id.startsWith('SC-') || f.bestPractice?.includes('SuperClaude')
    );

    console.log('🤖 SuperClaude Findings:', superclaudeFindings.length);
    if (superclaudeFindings.length > 0) {
      console.log('   First 3 SuperClaude findings:');
      superclaudeFindings.slice(0, 3).forEach((finding, idx) => {
        console.log(`   ${idx + 1}. [${finding.severity}] ${finding.title}`);
        console.log(`      Location: ${finding.location}`);
      });
    }
    console.log('');

    console.log('⏱️  Execution Time:', result.metadata.executionTime, 'ms');
    console.log('');

    console.log('✅ Integration test completed successfully!');

  } catch (error) {
    console.error('❌ Integration test failed:', error);
    process.exit(1);
  }
}

// Run the test
testSuperClaudeIntegration();
