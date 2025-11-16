/**
 * Markdown Task Manager - Agent System
 *
 * Main entry point for the KaibanJS agent orchestration system.
 * This system uses 8 specialized AI agents to analyze repositories,
 * break down work, and generate project plans.
 */

import { agents, allAgents } from './configs/agents';
import { analyzeFeature, createFeatureAnalysisWorkflow } from './workflows/featureAnalysis';

// Import workflow board and routers (Week 5 Day 3)
import { workflowBoard, WorkflowOptions } from './boards/workflowBoard';
import { WorkType, WorkRequest, classifyWorkType, routeWorkRequest } from './routers/workTypeRouter';

// Import specific workflows
import { executeNewFeatureWorkflow, NewFeatureRequest } from './workflows/newFeatureWorkflow';
import { executeMaintenanceWorkflow, MaintenanceRequest } from './workflows/maintenanceWorkflow';
import { executeBugWorkflow, BugReport } from './workflows/bugWorkflow';

// Environment configuration
const env = {
  ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || '',
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
  OLLAMA_BASE_URL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
};

console.log('🤖 Markdown Task Manager - Agent System');
console.log('========================================');
console.log('');
console.log('Configured Agents:');
console.log(`  ✓ Feature Architect (${agents.featureArchitect.name}) - Claude Sonnet 4.5`);
console.log(`  ✓ Maintenance Specialist (${agents.maintenanceSpecialist.name}) - Ollama Llama 3.1`);
console.log(`  ✓ Quality Inspector (${agents.qualityInspector.name}) - Claude Sonnet 4.5`);
console.log(`  ✓ Bug Hunter (${agents.bugHunter.name}) - Ollama Llama 3.1`);
console.log(`  ✓ Estimation Engine (${agents.estimationEngine.name}) - Ollama Llama 3.1`);
console.log(`  ✓ Test Engineer (${agents.testEngineer.name}) - Ollama Llama 3.1`);
console.log(`  ✓ Migration Architect (${agents.migrationArchitect.name}) - GPT-4 Turbo`);
console.log(`  ✓ Documentation Writer (${agents.documentationWriter.name}) - Ollama Llama 3.1`);
console.log('');
console.log('Workflow System:');
console.log('  ✓ Work Type Router - Auto-classify 8 work types');
console.log('  ✓ Workflow Board - Orchestrate agent teams');
console.log('  ✓ NEW_FEATURE workflow - Spec-Kit pipeline');
console.log('  ✓ MAINTENANCE workflow - 6-stage process');
console.log('  ✓ BUG workflow - 5-stage bug fixing');
console.log('');
console.log('Environment:');
console.log(`  Anthropic API: ${env.ANTHROPIC_API_KEY ? '✓ Configured' : '✗ Missing'}`);
console.log(`  OpenAI API: ${env.OPENAI_API_KEY ? '✓ Configured' : '✗ Missing'}`);
console.log(`  Ollama URL: ${env.OLLAMA_BASE_URL}`);
console.log('');

/**
 * Main workflow execution function
 * Routes work request to appropriate workflow
 */
export async function executeWorkflow(
  request: WorkRequest,
  options?: WorkflowOptions
) {
  return workflowBoard.executeWorkflow(request, options);
}

// Export main interfaces
export {
  // Agents
  agents,
  allAgents,

  // Legacy workflow (for backward compatibility)
  analyzeFeature,
  createFeatureAnalysisWorkflow,

  // Workflow Board (Week 5 Day 3)
  workflowBoard,
  WorkflowOptions,

  // Work Type Router
  WorkType,
  WorkRequest,
  classifyWorkType,
  routeWorkRequest,

  // Specific Workflows
  executeNewFeatureWorkflow,
  executeMaintenanceWorkflow,
  executeBugWorkflow,

  // Types
  NewFeatureRequest,
  MaintenanceRequest,
  BugReport
};

/**
 * Example usage:
 *
 * // Automatic work type classification
 * const result = await executeWorkflow({
 *   description: 'Add OAuth2 authentication with Google and GitHub'
 * });
 *
 * // Explicit work type
 * const result = await executeWorkflow({
 *   description: 'Fix login bug',
 *   workType: WorkType.BUG
 * });
 *
 * // Specific workflow
 * const result = await executeNewFeatureWorkflow({
 *   description: 'Add payment processing',
 *   businessGoals: ['Increase revenue', 'Support subscriptions'],
 *   constraints: ['PCI compliance required']
 * });
 */
