"use strict";
/**
 * KaibanJS Agent Configurations
 *
 * This file creates the actual KaibanJS Agent instances
 * using the configurations defined in AgentTypes.ts
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.allAgents = exports.agents = void 0;
const kaibanjs_1 = require("kaibanjs");
const AgentTypes_1 = require("../types/AgentTypes");
/**
 * Helper function to create LLM configuration based on provider
 */
function createLLMConfig(provider, model) {
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
exports.agents = {
    featureArchitect: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.FEATURE_ARCHITECT].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.FEATURE_ARCHITECT].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.FEATURE_ARCHITECT].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.FEATURE_ARCHITECT].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.FEATURE_ARCHITECT].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.FEATURE_ARCHITECT].llmModel)
    }),
    maintenanceSpecialist: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MAINTENANCE_SPECIALIST].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MAINTENANCE_SPECIALIST].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MAINTENANCE_SPECIALIST].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MAINTENANCE_SPECIALIST].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MAINTENANCE_SPECIALIST].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MAINTENANCE_SPECIALIST].llmModel)
    }),
    qualityInspector: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.QUALITY_INSPECTOR].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.QUALITY_INSPECTOR].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.QUALITY_INSPECTOR].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.QUALITY_INSPECTOR].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.QUALITY_INSPECTOR].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.QUALITY_INSPECTOR].llmModel)
    }),
    bugHunter: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.BUG_HUNTER].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.BUG_HUNTER].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.BUG_HUNTER].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.BUG_HUNTER].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.BUG_HUNTER].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.BUG_HUNTER].llmModel)
    }),
    estimationEngine: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.ESTIMATION_ENGINE].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.ESTIMATION_ENGINE].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.ESTIMATION_ENGINE].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.ESTIMATION_ENGINE].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.ESTIMATION_ENGINE].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.ESTIMATION_ENGINE].llmModel)
    }),
    testEngineer: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.TEST_ENGINEER].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.TEST_ENGINEER].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.TEST_ENGINEER].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.TEST_ENGINEER].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.TEST_ENGINEER].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.TEST_ENGINEER].llmModel)
    }),
    migrationArchitect: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MIGRATION_ARCHITECT].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MIGRATION_ARCHITECT].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MIGRATION_ARCHITECT].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MIGRATION_ARCHITECT].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MIGRATION_ARCHITECT].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.MIGRATION_ARCHITECT].llmModel)
    }),
    documentationWriter: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.DOCUMENTATION_WRITER].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.DOCUMENTATION_WRITER].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.DOCUMENTATION_WRITER].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.DOCUMENTATION_WRITER].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.DOCUMENTATION_WRITER].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.DOCUMENTATION_WRITER].llmModel)
    }),
    productOwner: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PRODUCT_OWNER].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PRODUCT_OWNER].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PRODUCT_OWNER].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PRODUCT_OWNER].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PRODUCT_OWNER].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PRODUCT_OWNER].llmModel)
    }),
    projectLead: new kaibanjs_1.Agent({
        name: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PROJECT_LEAD].name,
        role: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PROJECT_LEAD].role,
        goal: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PROJECT_LEAD].goal,
        background: AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PROJECT_LEAD].background,
        llmConfig: createLLMConfig(AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PROJECT_LEAD].llmProvider, AgentTypes_1.AGENT_CONFIGS[AgentTypes_1.AgentRole.PROJECT_LEAD].llmModel)
    })
};
/**
 * Export array of all agents for team configuration
 */
exports.allAgents = Object.values(exports.agents);
