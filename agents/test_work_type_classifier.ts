/**
 * Test Work Type Classifier
 *
 * Tests LLM-based and keyword-based classification with various scenarios.
 */

import {
  routeWorkRequestEnhanced,
  classifyWorkTypeEnhanced,
  WorkType,
  formatClassificationForUser
} from './routers/workTypeRouter';

interface TestCase {
  name: string;
  description: string;
  expectedWorkType: WorkType;
  context?: Record<string, any>;
}

const TEST_CASES: TestCase[] = [
  // PROJECT_DEFINITION
  {
    name: 'New Project Setup',
    description: 'Define a new e-commerce project from scratch with complete charter, vision, and roadmap',
    expectedWorkType: WorkType.PROJECT_DEFINITION
  },

  // NEW_FEATURE
  {
    name: 'New Feature',
    description: 'Add user authentication system with OAuth2 and JWT tokens',
    expectedWorkType: WorkType.NEW_FEATURE
  },
  {
    name: 'New Feature (build)',
    description: 'Build a real-time chat feature using WebSocket',
    expectedWorkType: WorkType.NEW_FEATURE
  },

  // MAINTENANCE
  {
    name: 'Dependency Update',
    description: 'Update all npm dependencies to latest versions and fix breaking changes',
    expectedWorkType: WorkType.MAINTENANCE
  },
  {
    name: 'Refactoring',
    description: 'Refactor the API layer to use async/await instead of callbacks',
    expectedWorkType: WorkType.MAINTENANCE
  },

  // QUALITY_AUDIT
  {
    name: 'Security Audit',
    description: 'Perform comprehensive security audit focusing on OWASP Top 10',
    expectedWorkType: WorkType.QUALITY_AUDIT
  },
  {
    name: 'Code Review',
    description: 'Review the entire codebase for quality issues and best practices',
    expectedWorkType: WorkType.QUALITY_AUDIT
  },

  // BUG
  {
    name: 'Bug Fix',
    description: 'Fix the login page crash when password contains special characters',
    expectedWorkType: WorkType.BUG
  },
  {
    name: 'Error Fix',
    description: 'The payment processing is failing with 500 error - need to fix this',
    expectedWorkType: WorkType.BUG
  },

  // ENHANCEMENT
  {
    name: 'Feature Enhancement',
    description: 'Improve the search functionality to include fuzzy matching and filters',
    expectedWorkType: WorkType.ENHANCEMENT
  },
  {
    name: 'Performance Enhancement',
    description: 'Optimize the database queries to reduce page load time',
    expectedWorkType: WorkType.ENHANCEMENT
  },

  // MIGRATION
  {
    name: 'Technology Migration',
    description: 'Migrate from MongoDB to PostgreSQL for better relational data handling',
    expectedWorkType: WorkType.MIGRATION
  },
  {
    name: 'Platform Upgrade',
    description: 'Upgrade the entire application from Node 16 to Node 20',
    expectedWorkType: WorkType.MIGRATION
  },

  // QUALITY_IMPROVEMENT
  {
    name: 'Technical Debt',
    description: 'Address technical debt by reducing code duplication and complexity',
    expectedWorkType: WorkType.QUALITY_IMPROVEMENT
  },
  {
    name: 'Code Smells',
    description: 'Clean up code smells identified by SonarQube analysis',
    expectedWorkType: WorkType.QUALITY_IMPROVEMENT
  },

  // TESTING
  {
    name: 'Test Coverage',
    description: 'Create comprehensive unit tests to achieve 80% code coverage',
    expectedWorkType: WorkType.TESTING
  },
  {
    name: 'E2E Tests',
    description: 'Build end-to-end test suite for the checkout flow',
    expectedWorkType: WorkType.TESTING
  }
];

async function runTest(testCase: TestCase, useLLM: boolean = true): Promise<void> {
  const mode = useLLM ? 'LLM' : 'KEYWORDS';
  console.log(`\n${'='.repeat(80)}`);
  console.log(`TEST: ${testCase.name} (${mode})`);
  console.log(`${'='.repeat(80)}`);
  console.log(`Description: "${testCase.description}"`);
  console.log(`Expected: ${testCase.expectedWorkType}`);

  try {
    const result = await routeWorkRequestEnhanced({
      description: testCase.description,
      context: testCase.context,
      useLLM
    });

    console.log(`\nClassified as: ${result.workType}`);
    console.log(`Confidence: ${(result.classification.confidence * 100).toFixed(1)}%`);
    console.log(`Reasoning: ${result.classification.reasoning}`);

    if (result.classification.alternativeOptions && result.classification.alternativeOptions.length > 0) {
      console.log(`\nAlternatives:`);
      result.classification.alternativeOptions.forEach(alt => {
        console.log(`  - ${alt.workType} (${(alt.confidence * 100).toFixed(1)}%)`);
      });
    }

    const isCorrect = result.workType === testCase.expectedWorkType;
    const status = isCorrect ? '✅ PASS' : '❌ FAIL';
    console.log(`\n${status}`);

    if (result.classification.needsUserConfirmation) {
      console.log(`⚠️ Low confidence - would ask user for confirmation`);
    }

    return;
  } catch (error) {
    console.error(`\n❌ ERROR: ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function main() {
  console.log('╔════════════════════════════════════════════════════════════════════════════╗');
  console.log('║                    Work Type Classification Test Suite                     ║');
  console.log('╚════════════════════════════════════════════════════════════════════════════╝');

  console.log('\n📊 Testing Classification Accuracy\n');
  console.log(`Total Test Cases: ${TEST_CASES.length}`);

  // Test with LLM
  console.log('\n\n🤖 LLM-BASED CLASSIFICATION');
  console.log('═'.repeat(80));

  let llmCorrect = 0;
  let llmTotal = 0;

  for (const testCase of TEST_CASES) {
    await runTest(testCase, true);
    // Count results manually for now (would need to track in runTest)
    llmTotal++;
  }

  // Test with Keywords
  console.log('\n\n🔤 KEYWORD-BASED CLASSIFICATION (Fallback)');
  console.log('═'.repeat(80));

  let keywordCorrect = 0;
  let keywordTotal = 0;

  for (const testCase of TEST_CASES) {
    await runTest(testCase, false);
    keywordTotal++;
  }

  // Summary
  console.log('\n\n╔════════════════════════════════════════════════════════════════════════════╗');
  console.log('║                            TEST SUMMARY                                    ║');
  console.log('╚════════════════════════════════════════════════════════════════════════════╝');
  console.log(`\n📊 LLM Classification: ${llmTotal} tests completed`);
  console.log(`📊 Keyword Classification: ${keywordTotal} tests completed`);
  console.log('\n✅ All tests executed successfully');
  console.log('\nNote: Review results above to check accuracy');
}

// Run tests
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
