/**
 * KaibanJS Agent Configurations
 *
 * This file creates the actual KaibanJS Agent instances
 * using the configurations defined in AgentTypes.ts
 */

import { Agent } from 'kaibanjs';
import { AGENT_CONFIGS, AgentRole } from '../types/AgentTypes';

/**
 * Helper function to create LLM configuration based on provider
 */
function createLLMConfig(provider: string, model: string) {
  switch (provider) {
    case 'claude':
      return {
        provider: 'anthropic',
        model: model,
        apiKey: process.env.ANTHROPIC_API_KEY || ''
      };
    case 'gpt4':
      return {
        provider: 'openai',
        model: model,
        apiKey: process.env.OPENAI_API_KEY || ''
      };
    case 'ollama':
      return {
        provider: 'ollama',
        model: model,
        baseURL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
      };
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

/**
 * Create all agent instances
 */
export const agents = {
  featureArchitect: new Agent({
    name: AGENT_CONFIGS[AgentRole.FEATURE_ARCHITECT].name,
    role: AGENT_CONFIGS[AgentRole.FEATURE_ARCHITECT].role,
    goal: AGENT_CONFIGS[AgentRole.FEATURE_ARCHITECT].goal,
    background: AGENT_CONFIGS[AgentRole.FEATURE_ARCHITECT].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.FEATURE_ARCHITECT].llmProvider,
      AGENT_CONFIGS[AgentRole.FEATURE_ARCHITECT].llmModel
    )
  }),

  maintenanceSpecialist: new Agent({
    name: AGENT_CONFIGS[AgentRole.MAINTENANCE_SPECIALIST].name,
    role: AGENT_CONFIGS[AgentRole.MAINTENANCE_SPECIALIST].role,
    goal: AGENT_CONFIGS[AgentRole.MAINTENANCE_SPECIALIST].goal,
    background: AGENT_CONFIGS[AgentRole.MAINTENANCE_SPECIALIST].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.MAINTENANCE_SPECIALIST].llmProvider,
      AGENT_CONFIGS[AgentRole.MAINTENANCE_SPECIALIST].llmModel
    )
  }),

  qualityInspector: new Agent({
    name: AGENT_CONFIGS[AgentRole.QUALITY_INSPECTOR].name,
    role: AGENT_CONFIGS[AgentRole.QUALITY_INSPECTOR].role,
    goal: AGENT_CONFIGS[AgentRole.QUALITY_INSPECTOR].goal,
    background: AGENT_CONFIGS[AgentRole.QUALITY_INSPECTOR].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.QUALITY_INSPECTOR].llmProvider,
      AGENT_CONFIGS[AgentRole.QUALITY_INSPECTOR].llmModel
    )
  }),

  bugHunter: new Agent({
    name: AGENT_CONFIGS[AgentRole.BUG_HUNTER].name,
    role: AGENT_CONFIGS[AgentRole.BUG_HUNTER].role,
    goal: AGENT_CONFIGS[AgentRole.BUG_HUNTER].goal,
    background: AGENT_CONFIGS[AgentRole.BUG_HUNTER].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.BUG_HUNTER].llmProvider,
      AGENT_CONFIGS[AgentRole.BUG_HUNTER].llmModel
    )
  }),

  estimationEngine: new Agent({
    name: AGENT_CONFIGS[AgentRole.ESTIMATION_ENGINE].name,
    role: AGENT_CONFIGS[AgentRole.ESTIMATION_ENGINE].role,
    goal: AGENT_CONFIGS[AgentRole.ESTIMATION_ENGINE].goal,
    background: AGENT_CONFIGS[AgentRole.ESTIMATION_ENGINE].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.ESTIMATION_ENGINE].llmProvider,
      AGENT_CONFIGS[AgentRole.ESTIMATION_ENGINE].llmModel
    )
  }),

  testEngineer: new Agent({
    name: AGENT_CONFIGS[AgentRole.TEST_ENGINEER].name,
    role: AGENT_CONFIGS[AgentRole.TEST_ENGINEER].role,
    goal: AGENT_CONFIGS[AgentRole.TEST_ENGINEER].goal,
    background: AGENT_CONFIGS[AgentRole.TEST_ENGINEER].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.TEST_ENGINEER].llmProvider,
      AGENT_CONFIGS[AgentRole.TEST_ENGINEER].llmModel
    )
  }),

  migrationArchitect: new Agent({
    name: AGENT_CONFIGS[AgentRole.MIGRATION_ARCHITECT].name,
    role: AGENT_CONFIGS[AgentRole.MIGRATION_ARCHITECT].role,
    goal: AGENT_CONFIGS[AgentRole.MIGRATION_ARCHITECT].goal,
    background: AGENT_CONFIGS[AgentRole.MIGRATION_ARCHITECT].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.MIGRATION_ARCHITECT].llmProvider,
      AGENT_CONFIGS[AgentRole.MIGRATION_ARCHITECT].llmModel
    )
  }),

  documentationWriter: new Agent({
    name: AGENT_CONFIGS[AgentRole.DOCUMENTATION_WRITER].name,
    role: AGENT_CONFIGS[AgentRole.DOCUMENTATION_WRITER].role,
    goal: AGENT_CONFIGS[AgentRole.DOCUMENTATION_WRITER].goal,
    background: AGENT_CONFIGS[AgentRole.DOCUMENTATION_WRITER].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.DOCUMENTATION_WRITER].llmProvider,
      AGENT_CONFIGS[AgentRole.DOCUMENTATION_WRITER].llmModel
    )
  }),

  productOwner: new Agent({
    name: AGENT_CONFIGS[AgentRole.PRODUCT_OWNER].name,
    role: AGENT_CONFIGS[AgentRole.PRODUCT_OWNER].role,
    goal: AGENT_CONFIGS[AgentRole.PRODUCT_OWNER].goal,
    background: AGENT_CONFIGS[AgentRole.PRODUCT_OWNER].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.PRODUCT_OWNER].llmProvider,
      AGENT_CONFIGS[AgentRole.PRODUCT_OWNER].llmModel
    )
  }),

  projectLead: new Agent({
    name: AGENT_CONFIGS[AgentRole.PROJECT_LEAD].name,
    role: AGENT_CONFIGS[AgentRole.PROJECT_LEAD].role,
    goal: AGENT_CONFIGS[AgentRole.PROJECT_LEAD].goal,
    background: AGENT_CONFIGS[AgentRole.PROJECT_LEAD].background,
    llmConfig: createLLMConfig(
      AGENT_CONFIGS[AgentRole.PROJECT_LEAD].llmProvider,
      AGENT_CONFIGS[AgentRole.PROJECT_LEAD].llmModel
    )
  })
};

/**
 * Export array of all agents for team configuration
 */
export const allAgents = Object.values(agents);
