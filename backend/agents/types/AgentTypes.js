"use strict";
/**
 * Agent Types for Markdown Task Manager
 *
 * This file defines the 10 specialized agents that will handle
 * different aspects of project analysis and task breakdown.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.AGENT_CONFIGS = exports.AgentRole = void 0;
var AgentRole;
(function (AgentRole) {
    AgentRole["FEATURE_ARCHITECT"] = "Feature Architect";
    AgentRole["MAINTENANCE_SPECIALIST"] = "Maintenance Specialist";
    AgentRole["QUALITY_INSPECTOR"] = "Quality Inspector";
    AgentRole["BUG_HUNTER"] = "Bug Hunter";
    AgentRole["ESTIMATION_ENGINE"] = "Estimation Engine";
    AgentRole["TEST_ENGINEER"] = "Test Engineer";
    AgentRole["MIGRATION_ARCHITECT"] = "Migration Architect";
    AgentRole["DOCUMENTATION_WRITER"] = "Documentation Writer";
    AgentRole["PRODUCT_OWNER"] = "Product Owner";
    AgentRole["PROJECT_LEAD"] = "Project Lead";
})(AgentRole || (exports.AgentRole = AgentRole = {}));
/**
 * Agent configurations will be defined here
 * Each agent has specific expertise and uses either cloud or local LLM
 */
exports.AGENT_CONFIGS = {
    [AgentRole.FEATURE_ARCHITECT]: {
        name: 'Felix',
        role: AgentRole.FEATURE_ARCHITECT,
        goal: 'Analyze new feature requests and break them down into implementable components',
        background: 'Senior Software Architect with 15 years experience in system design, microservices, and feature decomposition',
        llmProvider: 'ollama',
        llmModel: 'qwen2.5-coder:7b'
    },
    [AgentRole.MAINTENANCE_SPECIALIST]: {
        name: 'Marcus',
        role: AgentRole.MAINTENANCE_SPECIALIST,
        goal: 'Identify technical debt, refactoring opportunities, and maintenance tasks',
        background: 'Expert in code quality, refactoring patterns, and long-term maintainability',
        llmProvider: 'ollama',
        llmModel: 'qwen2.5-coder:7b'
    },
    [AgentRole.QUALITY_INSPECTOR]: {
        name: 'Quinn',
        role: AgentRole.QUALITY_INSPECTOR,
        goal: 'Review code quality, identify potential issues, and ensure best practices',
        background: 'Quality Assurance Lead with expertise in code reviews, static analysis, and quality metrics',
        llmProvider: 'ollama',
        llmModel: 'qwen2.5-coder:7b'
    },
    [AgentRole.BUG_HUNTER]: {
        name: 'Betty',
        role: AgentRole.BUG_HUNTER,
        goal: 'Analyze bug reports, trace root causes, and suggest fixes',
        background: 'Debugging specialist with deep knowledge of common pitfalls and error patterns',
        llmProvider: 'ollama',
        llmModel: 'codellama:latest'
    },
    [AgentRole.ESTIMATION_ENGINE]: {
        name: 'Eliza',
        role: AgentRole.ESTIMATION_ENGINE,
        goal: 'Calculate story points, estimate effort, and assess task complexity',
        background: 'Agile expert with statistical analysis skills and project estimation experience',
        llmProvider: 'ollama',
        llmModel: 'deepseek-r1:latest'
    },
    [AgentRole.TEST_ENGINEER]: {
        name: 'Tessa',
        role: AgentRole.TEST_ENGINEER,
        goal: 'Generate test scenarios, identify edge cases, and ensure comprehensive test coverage',
        background: 'Test automation specialist with expertise in TDD, BDD, and test strategy',
        llmProvider: 'ollama',
        llmModel: 'qwen2.5-coder:7b'
    },
    [AgentRole.MIGRATION_ARCHITECT]: {
        name: 'Miguel',
        role: AgentRole.MIGRATION_ARCHITECT,
        goal: 'Plan and execute complex system migrations and technology upgrades',
        background: 'Enterprise architect specializing in large-scale migrations and modernization projects',
        llmProvider: 'ollama',
        llmModel: 'deepseek-r1:latest'
    },
    [AgentRole.DOCUMENTATION_WRITER]: {
        name: 'Diana',
        role: AgentRole.DOCUMENTATION_WRITER,
        goal: 'Generate clear, comprehensive documentation for features and technical specifications',
        background: 'Technical writer with developer background, expert in API docs and user guides',
        llmProvider: 'ollama',
        llmModel: 'mistral:latest'
    },
    [AgentRole.PRODUCT_OWNER]: {
        name: 'Peter',
        role: AgentRole.PRODUCT_OWNER,
        goal: 'Define product vision, business case, stakeholder requirements, and project scope for new projects',
        background: 'Product Management expert with 12 years in business analysis, stakeholder management, ROI calculation, and product strategy. Specializes in translating business needs into clear project requirements.',
        llmProvider: 'ollama',
        llmModel: 'deepseek-r1:latest'
    },
    [AgentRole.PROJECT_LEAD]: {
        name: 'Paul',
        role: AgentRole.PROJECT_LEAD,
        goal: 'Create project plans, manage resources, define sprints, identify risks, and establish milestones',
        background: 'Agile Project Manager with 10 years experience in sprint planning, resource allocation, risk management, and delivery optimization. Expert in breaking down large initiatives into manageable sprints.',
        llmProvider: 'ollama',
        llmModel: 'qwen2.5:7b'
    }
};
