"use strict";
/**
 * Work Type Router
 *
 * Classifies incoming requests into work types and routes them
 * to the appropriate agent team with the correct workflow.
 *
 * Features:
 * - LLM-based intelligent classification (with confidence scoring)
 * - Keyword fallback for reliability
 * - User confirmation for low confidence (<0.8)
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WORK_TYPE_TEAMS = exports.formatClassificationForUser = exports.WorkType = void 0;
exports.classifyWorkType = classifyWorkType;
exports.classifyWorkTypeEnhanced = classifyWorkTypeEnhanced;
exports.getTeamConfiguration = getTeamConfiguration;
exports.routeWorkRequest = routeWorkRequest;
exports.routeWorkRequestEnhanced = routeWorkRequestEnhanced;
exports.validateWorkRequest = validateWorkRequest;
const agents_1 = require("../configs/agents");
const WorkTypes_1 = require("../types/WorkTypes");
Object.defineProperty(exports, "WorkType", { enumerable: true, get: function () { return WorkTypes_1.WorkType; } });
const workTypeClassifier_1 = require("../lib/workTypeClassifier");
Object.defineProperty(exports, "formatClassificationForUser", { enumerable: true, get: function () { return workTypeClassifier_1.formatClassificationForUser; } });
/**
 * Work Type to Agent Team Mapping
 * Defines which agents are assigned to each work type
 */
exports.WORK_TYPE_TEAMS = {
    [WorkTypes_1.WorkType.PROJECT_DEFINITION]: {
        agents: [
            agents_1.agents.productOwner, // 1. Business case, scope, stakeholders
            agents_1.agents.featureArchitect, // 2. Architecture vision, tech stack
            agents_1.agents.productOwner, // 3. Epic breakdown from business goals
            agents_1.agents.estimationEngine, // 4. Effort estimation per epic
            agents_1.agents.projectLead, // 5. Project plan, sprints, milestones
            agents_1.agents.documentationWriter // 6. Complete project documentation
        ],
        process: 'sequential',
        workflow: 'project_setup_pipeline'
    },
    [WorkTypes_1.WorkType.NEW_FEATURE]: {
        agents: [
            agents_1.agents.featureArchitect,
            agents_1.agents.estimationEngine,
            agents_1.agents.testEngineer,
            agents_1.agents.qualityInspector,
            agents_1.agents.documentationWriter
        ],
        process: 'sequential',
        workflow: 'spec_kit_pipeline'
    },
    [WorkTypes_1.WorkType.MAINTENANCE]: {
        agents: [
            agents_1.agents.maintenanceSpecialist,
            agents_1.agents.qualityInspector,
            agents_1.agents.testEngineer,
            agents_1.agents.estimationEngine
        ],
        process: 'sequential',
        workflow: 'code_maintenance_6_stage'
    },
    [WorkTypes_1.WorkType.QUALITY_AUDIT]: {
        agents: [
            agents_1.agents.qualityInspector,
            agents_1.agents.maintenanceSpecialist,
            agents_1.agents.testEngineer
        ],
        process: 'parallel',
        workflow: 'superclaude_audit'
    },
    [WorkTypes_1.WorkType.BUG]: {
        agents: [
            agents_1.agents.bugHunter,
            agents_1.agents.testEngineer,
            agents_1.agents.documentationWriter
        ],
        process: 'sequential',
        workflow: 'bug_fix_5_stage'
    },
    [WorkTypes_1.WorkType.ENHANCEMENT]: {
        agents: [
            agents_1.agents.featureArchitect,
            agents_1.agents.maintenanceSpecialist,
            agents_1.agents.estimationEngine,
            agents_1.agents.testEngineer
        ],
        process: 'sequential',
        workflow: 'enhancement_hybrid'
    },
    [WorkTypes_1.WorkType.MIGRATION]: {
        agents: [
            agents_1.agents.migrationArchitect,
            agents_1.agents.qualityInspector,
            agents_1.agents.estimationEngine,
            agents_1.agents.testEngineer,
            agents_1.agents.documentationWriter
        ],
        process: 'sequential', // Will use hybrid in actual workflow
        workflow: 'migration_5_stage'
    },
    [WorkTypes_1.WorkType.QUALITY_IMPROVEMENT]: {
        agents: [
            agents_1.agents.qualityInspector,
            agents_1.agents.maintenanceSpecialist,
            agents_1.agents.testEngineer,
            agents_1.agents.estimationEngine
        ],
        process: 'sequential',
        workflow: 'quality_improvement_5_stage'
    },
    [WorkTypes_1.WorkType.TESTING]: {
        agents: [
            agents_1.agents.testEngineer,
            agents_1.agents.qualityInspector,
            agents_1.agents.documentationWriter
        ],
        process: 'sequential',
        workflow: 'test_generation_4_track'
    }
};
/**
 * Classification keywords for automatic work type detection
 */
const CLASSIFICATION_KEYWORDS = {
    [WorkTypes_1.WorkType.PROJECT_DEFINITION]: [
        'project', 'define project', 'new project', 'start project',
        'project setup', 'initialize', 'product vision', 'business case',
        'project charter', 'project plan', 'roadmap'
    ],
    [WorkTypes_1.WorkType.NEW_FEATURE]: [
        'add', 'create', 'new', 'implement', 'build', 'develop',
        'feature', 'functionality', 'capability'
    ],
    [WorkTypes_1.WorkType.MAINTENANCE]: [
        'update', 'upgrade', 'dependency', 'maintenance', 'refactor',
        'clean', 'organize', 'deprecate'
    ],
    [WorkTypes_1.WorkType.QUALITY_AUDIT]: [
        'audit', 'review', 'analyze', 'inspect', 'check', 'quality',
        'security', 'performance', 'assessment'
    ],
    [WorkTypes_1.WorkType.BUG]: [
        'bug', 'fix', 'error', 'issue', 'problem', 'crash', 'fails',
        'broken', 'not working', 'doesn\'t work'
    ],
    [WorkTypes_1.WorkType.ENHANCEMENT]: [
        'improve', 'enhance', 'better', 'optimize', 'extend',
        'expand', 'modify', 'adjust'
    ],
    [WorkTypes_1.WorkType.MIGRATION]: [
        'migrate', 'migration', 'move', 'transfer', 'upgrade to',
        'switch to', 'port', 'convert'
    ],
    [WorkTypes_1.WorkType.QUALITY_IMPROVEMENT]: [
        'technical debt', 'code smell', 'complexity', 'duplication',
        'coverage', 'cleanup', 'improve quality'
    ],
    [WorkTypes_1.WorkType.TESTING]: [
        'test', 'testing', 'unit test', 'integration test', 'e2e',
        'test coverage', 'test scenario'
    ]
};
/**
 * Classify work type based on description
 * Uses keyword matching with scoring (DEPRECATED - use classifyWorkTypeEnhanced)
 * @deprecated Use classifyWorkTypeEnhanced for LLM-based classification
 */
function classifyWorkType(description) {
    const lowerDesc = description.toLowerCase();
    const scores = {};
    // Calculate scores for each work type
    for (const [workType, keywords] of Object.entries(CLASSIFICATION_KEYWORDS)) {
        scores[workType] = keywords.filter(keyword => lowerDesc.includes(keyword)).length;
    }
    // Find work type with highest score
    const sorted = Object.entries(scores)
        .sort(([, a], [, b]) => (b || 0) - (a || 0));
    const topMatch = sorted[0];
    if (topMatch && topMatch[1] > 0) {
        return topMatch[0];
    }
    // Default to NEW_FEATURE if no clear match
    return WorkTypes_1.WorkType.NEW_FEATURE;
}
/**
 * Enhanced classification with LLM + confidence scoring
 */
async function classifyWorkTypeEnhanced(description, context, useLLM = true) {
    return await (0, workTypeClassifier_1.classifyWorkType)(description, context, useLLM);
}
/**
 * Get team configuration for a work type
 */
function getTeamConfiguration(workType) {
    return exports.WORK_TYPE_TEAMS[workType];
}
/**
 * Route work request to appropriate team (sync version - uses keyword fallback)
 */
function routeWorkRequest(request) {
    // Use provided work type or classify automatically (keyword-based for sync)
    const workType = request.workType || classifyWorkType(request.description);
    const teamConfig = getTeamConfiguration(workType);
    return {
        workType,
        teamConfig
    };
}
/**
 * Route work request to appropriate team (async version with LLM)
 */
async function routeWorkRequestEnhanced(request) {
    // If work type is provided, use it directly
    if (request.workType) {
        const keywordResult = (0, workTypeClassifier_1.classifyWorkTypeKeywords)(request.description);
        return {
            workType: request.workType,
            teamConfig: getTeamConfiguration(request.workType),
            classification: {
                ...keywordResult,
                workType: request.workType,
                confidence: 1.0,
                reasoning: 'User-specified work type',
                needsUserConfirmation: false
            }
        };
    }
    // Classify using LLM or keywords
    const classification = await classifyWorkTypeEnhanced(request.description, request.context, request.useLLM !== false // Default to true
    );
    const teamConfig = getTeamConfiguration(classification.workType);
    return {
        workType: classification.workType,
        teamConfig,
        classification
    };
}
/**
 * Validate work request
 */
function validateWorkRequest(request) {
    const errors = [];
    if (!request.description || request.description.trim().length === 0) {
        errors.push('Description is required');
    }
    if (request.description && request.description.length < 10) {
        errors.push('Description must be at least 10 characters');
    }
    if (request.workType && !Object.values(WorkTypes_1.WorkType).includes(request.workType)) {
        errors.push(`Invalid work type: ${request.workType}`);
    }
    return {
        valid: errors.length === 0,
        errors
    };
}
