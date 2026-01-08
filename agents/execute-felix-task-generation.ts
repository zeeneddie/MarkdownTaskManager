#!/usr/bin/env ts-node
/**
 * Felix Task Generation Executor (Week 12 - Real LLM Integration)
 *
 * Handles Felix agent calls for hierarchical task breakdown:
 * - Generate epics from specifications
 * - Generate features from epics
 * - Generate stories from features
 * - Generate tasks from stories
 *
 * Now with actual Ollama LLM integration (qwen2.5-coder:7b)
 */

import * as readline from 'readline';
import { OllamaClient } from './lib/ollamaClient';
import {
    createEpicPrompt,
    createFeaturePrompt,
    createStoryPrompt,
    createTaskPrompt,
    extractJSON
} from './lib/promptTemplates';
import {
    validateFeatures,
    validateStories,
    validateTasks,
    Epic as ValidationEpic,
    Feature as ValidationFeature,
    Story as ValidationStory,
    Task as ValidationTask
} from './lib/validation';

// Initialize Ollama client
const ollama = new OllamaClient('qwen2.5-coder:7b', process.env.OLLAMA_BASE_URL || 'http://localhost:11434');

// Flag to use mock fallback if Ollama unavailable
let USE_MOCK_FALLBACK = false;

// Types
export interface Specification {
    id: string;
    project_id: string;
    content_json: any;
    content_markdown: string;
}

export interface Epic {
    id: string;
    title: string;
    description: string;
    business_value?: string;
    user_personas?: string[];
    acceptance_criteria?: string[];
}

export interface Feature {
    id: string;
    title: string;
    description: string;
    technical_approach?: string;
    complexity?: string;
}

export interface Story {
    id: string;
    title: string;
    description: string;
    user_type?: string;
    user_goal?: string;
    user_benefit?: string;
    acceptance_criteria?: any[];
    story_points?: number;
}

interface CommandPayload {
    command: string;
    specification?: Specification;
    epic?: Epic;
    feature?: Feature;
    story?: Story;
    specificationContext?: any;
    epicContext?: any;
    featureContext?: any;
    projectId?: string;
    options?: Record<string, any>;
}

/**
 * Read JSON input from stdin
 */
async function readInput(): Promise<CommandPayload> {
    return new Promise((resolve, reject) => {
        let inputData = '';

        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });

        rl.on('line', (line) => {
            inputData += line;
        });

        rl.on('close', () => {
            try {
                const payload = JSON.parse(inputData);
                resolve(payload);
            } catch (error) {
                reject(new Error(`Failed to parse input JSON: ${error}`));
            }
        });

        rl.on('error', (error) => {
            reject(error);
        });
    });
}

/**
 * Generate epics from specification using Felix (Real LLM)
 */
async function generateEpics(
    specification: Specification,
    projectId: string,
    options: Record<string, any>
): Promise<any> {
    const maxEpics = options.max_epics || 7;

    try {
        // Check if Ollama is available
        if (!USE_MOCK_FALLBACK) {
            const isAvailable = await ollama.healthCheck();
            if (!isAvailable) {
                console.error('⚠️  Ollama not available, falling back to mock generation');
                USE_MOCK_FALLBACK = true;
            }
        }

        // Use real LLM if available
        if (!USE_MOCK_FALLBACK) {
            const prompt = createEpicPrompt(specification, maxEpics);
            const response = await ollama.generate(prompt, {
                temperature: 0.7,
                num_predict: 4000
            });

            const epics = extractJSON(response);

            return {
                epics,
                metadata: {
                    specification_id: specification.id,
                    project_id: projectId,
                    generated_at: new Date().toISOString(),
                    generator: "Felix (Feature Architect)",
                    model: "qwen2.5-coder:7b",
                    llm_used: true
                }
            };
        }
    } catch (error) {
        console.error('Error generating epics with LLM:', error);
        console.error('Falling back to mock generation');
        USE_MOCK_FALLBACK = true;
    }

    // FALLBACK: Mock generation (for development/testing)
    return generateEpicsMock(specification, projectId, maxEpics);
}

/**
 * Mock epic generation (fallback)
 */
function generateEpicsMock(
    specification: Specification,
    projectId: string,
    numEpics: number
): any {
    const specTitle = specification.content_json?.title || 'Untitled Project';
    const components = specification.content_json?.components || [];

    const epics = [];
    const epicTemplates = [
        {
            title: "Core Infrastructure",
            description: "Foundational technical infrastructure including database setup, API architecture, authentication system, and core service layers. Establishes the technical backbone for all features.",
            business_value: "Enables rapid feature development with secure, scalable foundation",
            user_personas: ["Developer", "System Administrator"],
            priority: "critical"
        },
        {
            title: "User Management & Authentication",
            description: "Complete user lifecycle management including registration, login, password management, profile editing, and role-based access control (RBAC). Provides secure user authentication and authorization.",
            business_value: "Ensures secure access control and personalized user experience",
            user_personas: ["End User", "Admin", "Developer"],
            priority: "critical"
        },
        {
            title: "Data Management & Storage",
            description: "Comprehensive data handling including CRUD operations, data validation, search and filtering, export/import capabilities, and data integrity maintenance.",
            business_value: "Provides reliable data persistence and retrieval mechanisms",
            user_personas: ["End User", "Data Analyst"],
            priority: "high"
        },
        {
            title: "User Interface & Experience",
            description: "Responsive frontend application with intuitive navigation, interactive components, real-time updates, and accessibility features. Delivers delightful user experience.",
            business_value: "Maximizes user adoption and satisfaction through excellent UX",
            user_personas: ["End User", "UX Designer"],
            priority: "high"
        },
        {
            title: "Integration & APIs",
            description: "External system integrations, third-party API connections, webhook support, and data synchronization mechanisms. Enables ecosystem connectivity.",
            business_value: "Extends platform capabilities through external integrations",
            user_personas: ["Developer", "Integration Specialist"],
            priority: "medium"
        },
        {
            title: "Analytics & Reporting",
            description: "Data analytics dashboard, custom reporting, metrics visualization, and export capabilities. Provides actionable insights from system data.",
            business_value: "Enables data-driven decision making",
            user_personas: ["Business Analyst", "Manager", "Admin"],
            priority: "medium"
        },
        {
            title: "Admin & Configuration",
            description: "Administrative control panel for system configuration, user management, permission controls, and system monitoring. Centralized admin capabilities.",
            business_value: "Simplifies system administration and configuration",
            user_personas: ["Admin", "System Administrator"],
            priority: "medium"
        }
    ];

    for (let i = 0; i < numEpics; i++) {
        const template = epicTemplates[i];
        epics.push({
            title: template.title,
            description: template.description,
            business_value: template.business_value,
            user_personas: template.user_personas,
            acceptance_criteria: [
                "All core functionality implemented and tested",
                "Documentation complete with examples",
                "Integration tests passing",
                "Performance benchmarks met",
                "Security review completed"
            ],
            estimated_story_points: 40 + Math.floor(Math.random() * 30),
            estimated_weeks: 2 + Math.floor(Math.random() * 3),
            priority: template.priority
        });
    }

    return {
        epics,
        metadata: {
            specification_id: specification.id,
            project_id: projectId,
            generated_at: new Date().toISOString(),
            generator: "Felix (Feature Architect)",
            model: "qwen2.5-coder:7b (mock)",
            llm_used: false
        }
    };
}

/**
 * Generate features from epic using Felix (Real LLM)
 */
async function generateFeatures(
    epic: Epic,
    specificationContext: any,
    options: Record<string, any>
): Promise<any> {
    const maxFeatures = options.max_features || 10;

    try {
        // Use real LLM if available
        if (!USE_MOCK_FALLBACK) {
            const prompt = createFeaturePrompt(epic, specificationContext, maxFeatures);
            const response = await ollama.generate(prompt, {
                temperature: 0.7,
                num_predict: 5000
            });

            const features = extractJSON(response);

            // Validate generated features
            const validationResult = validateFeatures(features as ValidationFeature[]);

            return {
                features,
                metadata: {
                    epic_id: epic.id,
                    epic_title: epic.title,
                    generated_at: new Date().toISOString(),
                    generator: "Felix (Feature Architect)",
                    model: "qwen2.5-coder:7b",
                    llm_used: true
                },
                validation: {
                    valid: validationResult.valid,
                    errors: validationResult.errors.length,
                    warnings: validationResult.warnings.length,
                    critical_issues: validationResult.summary.critical_issues,
                    details: validationResult.errors.length > 0 || validationResult.warnings.length > 0 ? validationResult : undefined
                }
            };
        }
    } catch (error) {
        console.error('Error generating features with LLM:', error);
        console.error('Falling back to mock generation');
    }

    // FALLBACK: Mock generation
    return generateFeaturesMock(epic, maxFeatures);
}

/**
 * Mock feature generation (fallback)
 */
function generateFeaturesMock(epic: Epic, numFeatures: number): any {

    const features = [];
    for (let i = 1; i <= numFeatures; i++) {
        features.push({
            title: `${epic.title} - Feature ${i}`,
            description: `Detailed implementation of specific capability within ${epic.title}. Provides user-facing functionality that contributes to the overall epic goals.`,
            technical_approach: "RESTful API with async processing where needed. Frontend components using modern framework patterns. Database schema optimized for queries.",
            api_endpoints: [
                { method: "GET", path: `/api/feature-${i}`, description: "Retrieve feature data" },
                { method: "POST", path: `/api/feature-${i}`, description: "Create new item" },
                { method: "PUT", path: `/api/feature-${i}/{id}`, description: "Update existing item" }
            ],
            database_changes: [
                { table: `feature_${i}_data`, action: "create", columns: ["id", "name", "status", "created_at"] }
            ],
            dependencies: i > 1 ? [`feature-${i - 1}`] : [],
            estimated_story_points: 8 + Math.floor(Math.random() * 8), // 8-15 points
            estimated_days: 3 + Math.floor(Math.random() * 5), // 3-7 days
            complexity: i % 3 === 0 ? "complex" : (i % 3 === 1 ? "moderate" : "simple"),
            priority: i <= 2 ? "high" : "medium"
        });
    }

    return {
        features,
        metadata: {
            epic_id: epic.id,
            epic_title: epic.title,
            generated_at: new Date().toISOString(),
            generator: "Felix (Feature Architect)",
            model: "qwen2.5-coder:7b (mock)",
            llm_used: false
        }
    };
}

/**
 * Generate stories from feature using Felix (Real LLM)
 */
async function generateStories(
    feature: Feature,
    epicContext: any,
    options: Record<string, any>
): Promise<any> {
    const maxStories = options.max_stories || 7;

    try {
        // Use real LLM if available
        if (!USE_MOCK_FALLBACK) {
            const prompt = createStoryPrompt(feature, epicContext, maxStories);
            const response = await ollama.generate(prompt, {
                temperature: 0.7,
                num_predict: 4000
            });

            const stories = extractJSON(response);

            // Validate generated stories
            const validationResult = validateStories(stories as ValidationStory[]);

            return {
                stories,
                metadata: {
                    feature_id: feature.id,
                    feature_title: feature.title,
                    generated_at: new Date().toISOString(),
                    generator: "Felix (Feature Architect)",
                    model: "qwen2.5-coder:7b",
                    llm_used: true
                },
                validation: {
                    valid: validationResult.valid,
                    errors: validationResult.errors.length,
                    warnings: validationResult.warnings.length,
                    critical_issues: validationResult.summary.critical_issues,
                    details: validationResult.errors.length > 0 || validationResult.warnings.length > 0 ? validationResult : undefined
                }
            };
        }
    } catch (error) {
        console.error('Error generating stories with LLM:', error);
        console.error('Falling back to mock generation');
    }

    // FALLBACK: Mock generation
    return generateStoriesMock(feature, maxStories);
}

/**
 * Mock story generation (fallback)
 */
function generateStoriesMock(feature: Feature, numStories: number): any {

    const stories = [];
    const userTypes = ["End User", "Admin", "Developer", "Manager"];

    for (let i = 1; i <= numStories; i++) {
        const userType = userTypes[i % userTypes.length];
        stories.push({
            title: `As a ${userType}, I want to ${feature.title.toLowerCase()} so that I can achieve my goals`,
            description: `User story for ${feature.title}. Focuses on specific user needs and desired outcomes.`,
            user_type: userType,
            user_goal: `accomplish specific task related to ${feature.title}`,
            user_benefit: "increased productivity and better outcomes",
            acceptance_criteria: [
                {
                    given: "user is authenticated and has appropriate permissions",
                    when: "user performs the action",
                    then: "system responds correctly with expected results"
                },
                {
                    given: "invalid input is provided",
                    when: "user attempts the action",
                    then: "system displays clear error message"
                },
                {
                    given: "action is successful",
                    when: "completion occurs",
                    then: "user receives confirmation and system state is updated"
                }
            ],
            story_points: [3, 5, 8, 13][Math.floor(Math.random() * 4)], // Fibonacci
            estimated_hours: 8 + Math.floor(Math.random() * 16), // 8-24 hours
            priority: i <= 2 ? "high" : "medium"
        });
    }

    return {
        stories,
        metadata: {
            feature_id: feature.id,
            feature_title: feature.title,
            generated_at: new Date().toISOString(),
            generator: "Felix (Feature Architect)",
            model: "qwen2.5-coder:7b (mock)",
            llm_used: false
        }
    };
}

/**
 * Generate tasks from story using Felix (Real LLM)
 */
async function generateTasks(
    story: Story,
    featureContext: any,
    options: Record<string, any>
): Promise<any> {
    const maxTasks = options.max_tasks || 5;

    try {
        // Use real LLM if available
        if (!USE_MOCK_FALLBACK) {
            const prompt = createTaskPrompt(story, featureContext, maxTasks);
            const response = await ollama.generate(prompt, {
                temperature: 0.7,
                num_predict: 3000
            });

            const tasks = extractJSON(response);

            // Validate generated tasks
            const validationResult = validateTasks(tasks as ValidationTask[]);

            return {
                tasks,
                metadata: {
                    story_id: story.id,
                    story_title: story.title,
                    generated_at: new Date().toISOString(),
                    generator: "Felix (Feature Architect)",
                    model: "qwen2.5-coder:7b",
                    llm_used: true
                },
                validation: {
                    valid: validationResult.valid,
                    errors: validationResult.errors.length,
                    warnings: validationResult.warnings.length,
                    critical_issues: validationResult.summary.critical_issues,
                    details: validationResult.errors.length > 0 || validationResult.warnings.length > 0 ? validationResult : undefined
                }
            };
        }
    } catch (error) {
        console.error('Error generating tasks with LLM:', error);
        console.error('Falling back to mock generation');
    }

    // FALLBACK: Mock generation
    return generateTasksMock(story, maxTasks);
}

/**
 * Mock task generation (fallback)
 */
function generateTasksMock(story: Story, numTasks: number): any {

    const tasks = [];
    const taskTypes = ["backend", "frontend", "database", "testing", "devops"];

    for (let i = 1; i <= numTasks; i++) {
        const taskType = taskTypes[i % taskTypes.length];
        tasks.push({
            title: `Implement ${taskType} component for ${story.title.substring(0, 40)}...`,
            description: `Technical implementation task for ${taskType} layer. Includes coding, unit testing, and integration.`,
            task_type: taskType,
            technical_notes: `Follow ${taskType} best practices. Ensure error handling, logging, and monitoring are included.`,
            code_files: [
                `src/${taskType}/component_${i}.ts`,
                `src/${taskType}/__tests__/component_${i}.test.ts`
            ],
            estimated_hours: 2 + Math.floor(Math.random() * 4), // 2-5 hours
            priority: i === 1 ? "high" : "medium"
        });
    }

    return {
        tasks,
        metadata: {
            story_id: story.id,
            story_title: story.title,
            generated_at: new Date().toISOString(),
            generator: "Felix (Feature Architect)",
            model: "qwen2.5-coder:7b (mock)",
            llm_used: false
        }
    };
}

/**
 * Main execution function
 */
async function main() {
    try {
        // Read input from stdin
        const payload = await readInput();

        let result: any;

        // Route to appropriate handler based on command
        switch (payload.command) {
            case 'generate-epics':
                if (!payload.specification || !payload.projectId) {
                    throw new Error('specification and projectId are required for generate-epics');
                }
                result = await generateEpics(
                    payload.specification,
                    payload.projectId,
                    payload.options || {}
                );
                break;

            case 'generate-features':
                if (!payload.epic) {
                    throw new Error('epic is required for generate-features');
                }
                result = await generateFeatures(
                    payload.epic,
                    payload.specificationContext || {},
                    payload.options || {}
                );
                break;

            case 'generate-stories':
                if (!payload.feature) {
                    throw new Error('feature is required for generate-stories');
                }
                result = await generateStories(
                    payload.feature,
                    payload.epicContext || {},
                    payload.options || {}
                );
                break;

            case 'generate-tasks':
                if (!payload.story) {
                    throw new Error('story is required for generate-tasks');
                }
                result = await generateTasks(
                    payload.story,
                    payload.featureContext || {},
                    payload.options || {}
                );
                break;

            default:
                throw new Error(`Unknown command: ${payload.command}`);
        }

        // Output result as JSON
        console.log(JSON.stringify(result));
        process.exit(0);

    } catch (error) {
        console.error(JSON.stringify({
            error: error instanceof Error ? error.message : String(error),
            success: false
        }));
        process.exit(1);
    }
}

// Execute
main();
