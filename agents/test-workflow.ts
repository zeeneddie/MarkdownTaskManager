/**
 * Test Workflow System
 *
 * Quick test to verify work type router and agent configuration
 */

import { classifyWorkType, WorkType, routeWorkRequest } from './routers/workTypeRouter';
import { agents } from './configs/agents';

console.log('🧪 Testing Workflow System');
console.log('==========================\n');

// Test 1: Work Type Classification
console.log('Test 1: Work Type Classification');
console.log('---------------------------------');

const testCases = [
  'Add OAuth2 authentication with Google and GitHub',
  'Fix bug where login fails after password reset',
  'Update dependencies and refactor authentication module',
  'Audit security vulnerabilities and performance issues',
  'Improve test coverage for payment module',
  'Migrate from Vue 2 to Vue 3',
  'Add unit tests for user service',
  'Enhance user profile page with new features'
];

testCases.forEach(description => {
  const workType = classifyWorkType(description);
  console.log(`\n📝 "${description}"`);
  console.log(`   → ${workType}`);
});

// Test 2: Team Configuration
console.log('\n\nTest 2: Team Configuration');
console.log('--------------------------');

const request = {
  description: 'Add payment processing with Stripe'
};

const { workType, teamConfig } = routeWorkRequest(request);

console.log(`\n📋 Work Type: ${workType}`);
console.log(`👥 Team Size: ${teamConfig.agents.length} agents`);
console.log(`🔄 Process: ${teamConfig.process}`);
console.log(`📊 Workflow: ${teamConfig.workflow}`);
console.log('\nTeam Members:');
teamConfig.agents.forEach((agent, idx) => {
  console.log(`  ${idx + 1}. ${agent.name} (${agent.role})`);
});

// Test 3: Agent Status
console.log('\n\nTest 3: Agent Status');
console.log('--------------------');

console.log('\nAll Agents:');
console.log(`  ✓ Felix (Feature Architect) - ${agents.featureArchitect ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Marcus (Maintenance Specialist) - ${agents.maintenanceSpecialist ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Quinn (Quality Inspector) - ${agents.qualityInspector ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Betty (Bug Hunter) - ${agents.bugHunter ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Eliza (Estimation Engine) - ${agents.estimationEngine ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Tessa (Test Engineer) - ${agents.testEngineer ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Miguel (Migration Architect) - ${agents.migrationArchitect ? 'Ready' : 'Not configured'}`);
console.log(`  ✓ Diana (Documentation Writer) - ${agents.documentationWriter ? 'Ready' : 'Not configured'}`);

console.log('\n✅ All tests completed!');
console.log('\n📚 Next Steps:');
console.log('  1. Set API keys in .env file');
console.log('  2. Download Llama 3.1 8B: ollama pull llama3.1:8b');
console.log('  3. Test actual workflow execution (Week 5 Day 4-5)');
console.log('');
