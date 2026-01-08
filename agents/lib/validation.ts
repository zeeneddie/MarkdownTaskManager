/**
 * Advanced Validation for Felix Task Generation
 *
 * Validates generated task hierarchies for:
 * - Cross-level consistency (story points, timelines)
 * - Dependency cycles
 * - Priority inheritance
 * - Estimation reasonableness
 * - Completeness checks
 */

export interface Epic {
    id?: string;
    title: string;
    description: string;
    business_value?: string;
    user_personas?: string[];
    acceptance_criteria?: string[];
    estimated_story_points?: number;
    estimated_weeks?: number;
    priority: string;
}

export interface Feature {
    id?: string;
    epic_id?: string;
    title: string;
    description: string;
    technical_approach?: string;
    dependencies?: string[];
    estimated_story_points?: number;
    estimated_days?: number;
    complexity?: string;
    priority: string;
}

export interface Story {
    id?: string;
    feature_id?: string;
    title: string;
    description: string;
    user_type?: string;
    acceptance_criteria?: Array<{ given: string; when: string; then: string }>;
    story_points?: number;
    estimated_hours?: number;
    priority: string;
}

export interface Task {
    id?: string;
    story_id?: string;
    title: string;
    description?: string;
    task_type?: string;
    estimated_hours?: number;
    priority: string;
}

export interface ValidationResult {
    valid: boolean;
    errors: ValidationError[];
    warnings: ValidationWarning[];
    summary: {
        total_errors: number;
        total_warnings: number;
        critical_issues: number;
    };
}

export interface ValidationError {
    level: 'epic' | 'feature' | 'story' | 'task';
    item_id?: string;
    item_title: string;
    rule: string;
    message: string;
    severity: 'critical' | 'high' | 'medium';
}

export interface ValidationWarning {
    level: 'epic' | 'feature' | 'story' | 'task';
    item_id?: string;
    item_title: string;
    rule: string;
    message: string;
    suggestion?: string;
}

/**
 * Fibonacci sequence for story points validation
 */
const FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89];

/**
 * Valid priority levels
 */
const VALID_PRIORITIES = ['critical', 'high', 'medium', 'low'];

/**
 * Main validation orchestrator
 */
export class HierarchyValidator {
    private errors: ValidationError[] = [];
    private warnings: ValidationWarning[] = [];

    /**
     * Validate epic with its features, stories, and tasks
     */
    validateEpic(
        epic: Epic,
        features: Feature[] = [],
        stories: Story[] = [],
        tasks: Task[] = []
    ): ValidationResult {
        this.errors = [];
        this.warnings = [];

        // Epic-level validations
        this.validateEpicStructure(epic);
        this.validateEpicEstimates(epic);

        // Cross-level validations
        if (features.length > 0) {
            this.validateEpicFeatureConsistency(epic, features);

            // Feature-level validations
            features.forEach(feature => {
                this.validateFeatureStructure(feature);
                this.validateFeatureEstimates(feature);

                // Feature-story consistency
                const featureStories = stories.filter(s => s.feature_id === feature.id);
                if (featureStories.length > 0) {
                    this.validateFeatureStoryConsistency(feature, featureStories);

                    // Story-level validations
                    featureStories.forEach(story => {
                        this.validateStoryStructure(story);
                        this.validateStoryEstimates(story);

                        // Story-task consistency
                        const storyTasks = tasks.filter(t => t.story_id === story.id);
                        if (storyTasks.length > 0) {
                            this.validateStoryTaskConsistency(story, storyTasks);

                            // Task-level validations
                            storyTasks.forEach(task => {
                                this.validateTaskStructure(task);
                                this.validateTaskEstimates(task);
                            });
                        }
                    });
                }
            });

            // Dependency cycle detection
            this.validateDependencyCycles(features);
        }

        return this.buildResult();
    }

    /**
     * Validate just features (without full hierarchy)
     */
    validateFeatures(features: Feature[]): ValidationResult {
        this.errors = [];
        this.warnings = [];

        features.forEach(feature => {
            this.validateFeatureStructure(feature);
            this.validateFeatureEstimates(feature);
        });

        this.validateDependencyCycles(features);

        return this.buildResult();
    }

    /**
     * Validate just stories (without full hierarchy)
     */
    validateStories(stories: Story[]): ValidationResult {
        this.errors = [];
        this.warnings = [];

        stories.forEach(story => {
            this.validateStoryStructure(story);
            this.validateStoryEstimates(story);
        });

        return this.buildResult();
    }

    /**
     * Validate just tasks (without full hierarchy)
     */
    validateTasks(tasks: Task[]): ValidationResult {
        this.errors = [];
        this.warnings = [];

        tasks.forEach(task => {
            this.validateTaskStructure(task);
            this.validateTaskEstimates(task);
        });

        return this.buildResult();
    }

    // ==================== Epic Validations ====================

    private validateEpicStructure(epic: Epic): void {
        // Required fields
        if (!epic.title || epic.title.trim().length === 0) {
            this.addError('epic', epic.id, epic.title || 'Untitled', 'required_field',
                'Epic title is required', 'critical');
        }

        if (!epic.description || epic.description.trim().length < 20) {
            this.addError('epic', epic.id, epic.title, 'required_field',
                'Epic description must be at least 20 characters', 'high');
        }

        // Priority validation
        if (!VALID_PRIORITIES.includes(epic.priority)) {
            this.addError('epic', epic.id, epic.title, 'invalid_priority',
                `Invalid priority "${epic.priority}". Must be one of: ${VALID_PRIORITIES.join(', ')}`, 'high');
        }

        // Business value check
        if (!epic.business_value) {
            this.addWarning('epic', epic.id, epic.title, 'missing_business_value',
                'Epic missing business value justification', 'Consider adding business value to explain ROI');
        }

        // Acceptance criteria check
        if (!epic.acceptance_criteria || epic.acceptance_criteria.length === 0) {
            this.addWarning('epic', epic.id, epic.title, 'missing_acceptance_criteria',
                'Epic has no acceptance criteria', 'Add 3-5 measurable acceptance criteria');
        } else if (epic.acceptance_criteria.length < 3) {
            this.addWarning('epic', epic.id, epic.title, 'insufficient_acceptance_criteria',
                `Epic has only ${epic.acceptance_criteria.length} acceptance criteria`, 'Consider adding more criteria (recommended: 3-5)');
        }
    }

    private validateEpicEstimates(epic: Epic): void {
        // Story points
        if (epic.estimated_story_points !== undefined) {
            if (epic.estimated_story_points < 30 || epic.estimated_story_points > 80) {
                this.addWarning('epic', epic.id, epic.title, 'unusual_story_points',
                    `Epic has ${epic.estimated_story_points} story points (typical range: 30-80)`,
                    'Verify the estimate or consider breaking into multiple epics');
            }
        } else {
            this.addWarning('epic', epic.id, epic.title, 'missing_estimate',
                'Epic missing story point estimate');
        }

        // Weeks estimate
        if (epic.estimated_weeks !== undefined) {
            if (epic.estimated_weeks < 2 || epic.estimated_weeks > 6) {
                this.addWarning('epic', epic.id, epic.title, 'unusual_timeline',
                    `Epic estimated at ${epic.estimated_weeks} weeks (typical range: 2-6)`,
                    'Verify the timeline or consider scope adjustment');
            }
        }
    }

    private validateEpicFeatureConsistency(epic: Epic, features: Feature[]): void {
        // Check feature count
        if (features.length < 5) {
            this.addWarning('epic', epic.id, epic.title, 'too_few_features',
                `Epic has only ${features.length} features (typical range: 5-15)`,
                'Consider if this epic is scoped appropriately');
        } else if (features.length > 15) {
            this.addWarning('epic', epic.id, epic.title, 'too_many_features',
                `Epic has ${features.length} features (typical range: 5-15)`,
                'Consider breaking into multiple epics');
        }

        // Story point consistency
        if (epic.estimated_story_points) {
            const featurePoints = features.reduce((sum, f) => sum + (f.estimated_story_points || 0), 0);
            const variance = Math.abs(epic.estimated_story_points - featurePoints);
            const percentDiff = (variance / epic.estimated_story_points) * 100;

            if (percentDiff > 20) {
                this.addError('epic', epic.id, epic.title, 'story_point_mismatch',
                    `Epic story points (${epic.estimated_story_points}) differ from sum of features (${featurePoints}) by ${percentDiff.toFixed(1)}%`,
                    'medium');
            }
        }

        // Timeline consistency (weeks vs days)
        if (epic.estimated_weeks) {
            const featureDays = features.reduce((sum, f) => sum + (f.estimated_days || 0), 0);
            const epicDays = epic.estimated_weeks * 5; // 5 working days per week
            const dayVariance = Math.abs(epicDays - featureDays);
            const percentDiff = (dayVariance / epicDays) * 100;

            if (percentDiff > 25) {
                this.addWarning('epic', epic.id, epic.title, 'timeline_mismatch',
                    `Epic timeline (${epic.estimated_weeks} weeks = ${epicDays} days) differs from sum of features (${featureDays} days) by ${percentDiff.toFixed(1)}%`);
            }
        }

        // Priority inheritance check
        const criticalFeatures = features.filter(f => f.priority === 'critical').length;
        if (epic.priority === 'critical' && criticalFeatures === 0) {
            this.addWarning('epic', epic.id, epic.title, 'priority_inheritance',
                'Critical epic has no critical features', 'Consider if some features should be marked critical');
        }
    }

    // ==================== Feature Validations ====================

    private validateFeatureStructure(feature: Feature): void {
        if (!feature.title || feature.title.trim().length === 0) {
            this.addError('feature', feature.id, feature.title || 'Untitled', 'required_field',
                'Feature title is required', 'critical');
        }

        if (!feature.description || feature.description.trim().length < 20) {
            this.addError('feature', feature.id, feature.title, 'required_field',
                'Feature description must be at least 20 characters', 'high');
        }

        if (!VALID_PRIORITIES.includes(feature.priority)) {
            this.addError('feature', feature.id, feature.title, 'invalid_priority',
                `Invalid priority "${feature.priority}"`, 'high');
        }

        if (!feature.technical_approach) {
            this.addWarning('feature', feature.id, feature.title, 'missing_technical_approach',
                'Feature missing technical approach', 'Add implementation details to guide development');
        }
    }

    private validateFeatureEstimates(feature: Feature): void {
        // Story points (should be Fibonacci)
        if (feature.estimated_story_points !== undefined) {
            if (!FIBONACCI.includes(feature.estimated_story_points)) {
                this.addWarning('feature', feature.id, feature.title, 'non_fibonacci_points',
                    `Feature has ${feature.estimated_story_points} story points (not in Fibonacci sequence)`,
                    `Use Fibonacci numbers: ${FIBONACCI.join(', ')}`);
            }

            if (feature.estimated_story_points < 5 || feature.estimated_story_points > 21) {
                this.addWarning('feature', feature.id, feature.title, 'unusual_story_points',
                    `Feature has ${feature.estimated_story_points} story points (typical range: 5-21)`);
            }
        }

        // Days estimate
        if (feature.estimated_days !== undefined) {
            if (feature.estimated_days < 2 || feature.estimated_days > 8) {
                this.addWarning('feature', feature.id, feature.title, 'unusual_timeline',
                    `Feature estimated at ${feature.estimated_days} days (typical range: 2-8)`);
            }
        }

        // Complexity check
        if (feature.complexity) {
            const validComplexities = ['simple', 'moderate', 'complex'];
            if (!validComplexities.includes(feature.complexity)) {
                this.addError('feature', feature.id, feature.title, 'invalid_complexity',
                    `Invalid complexity "${feature.complexity}". Must be: simple, moderate, or complex`, 'medium');
            }
        }
    }

    private validateFeatureStoryConsistency(feature: Feature, stories: Story[]): void {
        // Check story count
        if (stories.length < 3) {
            this.addWarning('feature', feature.id, feature.title, 'too_few_stories',
                `Feature has only ${stories.length} stories (typical range: 3-8)`);
        } else if (stories.length > 8) {
            this.addWarning('feature', feature.id, feature.title, 'too_many_stories',
                `Feature has ${stories.length} stories (typical range: 3-8)`);
        }

        // Story point consistency
        if (feature.estimated_story_points) {
            const storyPoints = stories.reduce((sum, s) => sum + (s.story_points || 0), 0);
            const variance = Math.abs(feature.estimated_story_points - storyPoints);
            const percentDiff = feature.estimated_story_points > 0
                ? (variance / feature.estimated_story_points) * 100
                : 0;

            if (percentDiff > 20) {
                this.addError('feature', feature.id, feature.title, 'story_point_mismatch',
                    `Feature story points (${feature.estimated_story_points}) differ from sum of stories (${storyPoints}) by ${percentDiff.toFixed(1)}%`,
                    'medium');
            }
        }

        // Timeline consistency (days vs hours)
        if (feature.estimated_days) {
            const storyHours = stories.reduce((sum, s) => sum + (s.estimated_hours || 0), 0);
            const featureHours = feature.estimated_days * 8; // 8 working hours per day
            const hourVariance = Math.abs(featureHours - storyHours);
            const percentDiff = featureHours > 0 ? (hourVariance / featureHours) * 100 : 0;

            if (percentDiff > 25) {
                this.addWarning('feature', feature.id, feature.title, 'timeline_mismatch',
                    `Feature timeline (${feature.estimated_days} days = ${featureHours} hours) differs from sum of stories (${storyHours} hours) by ${percentDiff.toFixed(1)}%`);
            }
        }
    }

    // ==================== Story Validations ====================

    private validateStoryStructure(story: Story): void {
        if (!story.title || story.title.trim().length === 0) {
            this.addError('story', story.id, story.title || 'Untitled', 'required_field',
                'Story title is required', 'critical');
        }

        // User story format check
        const userStoryPattern = /^As a .+, I want .+ so that .+$/i;
        if (story.title && !userStoryPattern.test(story.title)) {
            this.addWarning('story', story.id, story.title, 'invalid_format',
                'Story title should follow format: "As a [user], I want [goal] so that [benefit]"',
                'Rephrase to follow standard user story format');
        }

        if (!story.description || story.description.trim().length < 20) {
            this.addWarning('story', story.id, story.title, 'short_description',
                'Story description is very short', 'Add more context and details');
        }

        if (!VALID_PRIORITIES.includes(story.priority)) {
            this.addError('story', story.id, story.title, 'invalid_priority',
                `Invalid priority "${story.priority}"`, 'high');
        }

        // Acceptance criteria check (Given/When/Then format)
        if (!story.acceptance_criteria || story.acceptance_criteria.length === 0) {
            this.addError('story', story.id, story.title, 'missing_acceptance_criteria',
                'Story has no acceptance criteria', 'high');
        } else {
            story.acceptance_criteria.forEach((ac, index) => {
                if (!ac.given || !ac.when || !ac.then) {
                    this.addError('story', story.id, story.title, 'incomplete_acceptance_criteria',
                        `Acceptance criterion ${index + 1} is incomplete (must have Given/When/Then)`, 'medium');
                }
            });
        }
    }

    private validateStoryEstimates(story: Story): void {
        // Story points (must be Fibonacci)
        if (story.story_points !== undefined) {
            if (!FIBONACCI.includes(story.story_points)) {
                this.addError('story', story.id, story.title, 'invalid_story_points',
                    `Story has ${story.story_points} story points (must be Fibonacci: 1, 2, 3, 5, 8, 13)`, 'medium');
            }

            if (story.story_points < 1 || story.story_points > 13) {
                this.addWarning('story', story.id, story.title, 'unusual_story_points',
                    `Story has ${story.story_points} story points (typical range: 1-13)`);
            }
        } else {
            this.addError('story', story.id, story.title, 'missing_estimate',
                'Story missing story point estimate', 'high');
        }

        // Hours estimate
        if (story.estimated_hours !== undefined) {
            if (story.estimated_hours < 4 || story.estimated_hours > 24) {
                this.addWarning('story', story.id, story.title, 'unusual_timeline',
                    `Story estimated at ${story.estimated_hours} hours (typical range: 4-24)`);
            }
        }
    }

    private validateStoryTaskConsistency(story: Story, tasks: Task[]): void {
        // Check task count
        if (tasks.length < 2) {
            this.addWarning('story', story.id, story.title, 'too_few_tasks',
                `Story has only ${tasks.length} tasks (typical range: 2-5)`);
        } else if (tasks.length > 5) {
            this.addWarning('story', story.id, story.title, 'too_many_tasks',
                `Story has ${tasks.length} tasks (typical range: 2-5)`);
        }

        // Timeline consistency (story hours vs task hours)
        if (story.estimated_hours) {
            const taskHours = tasks.reduce((sum, t) => sum + (t.estimated_hours || 0), 0);
            const variance = Math.abs(story.estimated_hours - taskHours);
            const percentDiff = story.estimated_hours > 0 ? (variance / story.estimated_hours) * 100 : 0;

            if (percentDiff > 20) {
                this.addWarning('story', story.id, story.title, 'timeline_mismatch',
                    `Story hours (${story.estimated_hours}) differ from sum of tasks (${taskHours}) by ${percentDiff.toFixed(1)}%`);
            }
        }
    }

    // ==================== Task Validations ====================

    private validateTaskStructure(task: Task): void {
        if (!task.title || task.title.trim().length === 0) {
            this.addError('task', task.id, task.title || 'Untitled', 'required_field',
                'Task title is required', 'critical');
        }

        if (!VALID_PRIORITIES.includes(task.priority)) {
            this.addError('task', task.id, task.title, 'invalid_priority',
                `Invalid priority "${task.priority}"`, 'high');
        }

        if (task.task_type) {
            const validTypes = ['backend', 'frontend', 'database', 'testing', 'devops', 'documentation'];
            if (!validTypes.includes(task.task_type)) {
                this.addWarning('task', task.id, task.title, 'unusual_task_type',
                    `Unusual task type "${task.task_type}"`, `Common types: ${validTypes.join(', ')}`);
            }
        }
    }

    private validateTaskEstimates(task: Task): void {
        if (task.estimated_hours !== undefined) {
            if (task.estimated_hours < 0.5 || task.estimated_hours > 4) {
                this.addWarning('task', task.id, task.title, 'unusual_timeline',
                    `Task estimated at ${task.estimated_hours} hours (typical range: 0.5-4)`);
            }
        } else {
            this.addWarning('task', task.id, task.title, 'missing_estimate',
                'Task missing hour estimate');
        }
    }

    // ==================== Dependency Cycle Detection ====================

    private validateDependencyCycles(features: Feature[]): void {
        const graph = this.buildDependencyGraph(features);
        const cycles = this.detectCycles(graph);

        if (cycles.length > 0) {
            cycles.forEach(cycle => {
                const cycleStr = cycle.map(id => {
                    const feature = features.find(f => f.id === id);
                    return feature ? feature.title : id;
                }).join(' → ');

                this.addError('feature', cycle[0], cycleStr, 'dependency_cycle',
                    `Circular dependency detected: ${cycleStr}`, 'critical');
            });
        }
    }

    private buildDependencyGraph(features: Feature[]): Map<string, string[]> {
        const graph = new Map<string, string[]>();

        features.forEach(feature => {
            if (feature.id) {
                const deps = feature.dependencies || [];
                graph.set(feature.id, deps);
            }
        });

        return graph;
    }

    private detectCycles(graph: Map<string, string[]>): string[][] {
        const cycles: string[][] = [];
        const visited = new Set<string>();
        const recStack = new Set<string>();
        const path: string[] = [];

        const dfs = (node: string): boolean => {
            visited.add(node);
            recStack.add(node);
            path.push(node);

            const neighbors = graph.get(node) || [];
            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    if (dfs(neighbor)) {
                        return true;
                    }
                } else if (recStack.has(neighbor)) {
                    // Cycle detected
                    const cycleStart = path.indexOf(neighbor);
                    cycles.push([...path.slice(cycleStart), neighbor]);
                    return true;
                }
            }

            path.pop();
            recStack.delete(node);
            return false;
        };

        for (const node of graph.keys()) {
            if (!visited.has(node)) {
                dfs(node);
            }
        }

        return cycles;
    }

    // ==================== Helper Methods ====================

    private addError(
        level: 'epic' | 'feature' | 'story' | 'task',
        id: string | undefined,
        title: string,
        rule: string,
        message: string,
        severity: 'critical' | 'high' | 'medium' = 'high'
    ): void {
        this.errors.push({ level, item_id: id, item_title: title, rule, message, severity });
    }

    private addWarning(
        level: 'epic' | 'feature' | 'story' | 'task',
        id: string | undefined,
        title: string,
        rule: string,
        message: string,
        suggestion?: string
    ): void {
        this.warnings.push({ level, item_id: id, item_title: title, rule, message, suggestion });
    }

    private buildResult(): ValidationResult {
        const criticalIssues = this.errors.filter(e => e.severity === 'critical').length;

        return {
            valid: this.errors.length === 0,
            errors: this.errors,
            warnings: this.warnings,
            summary: {
                total_errors: this.errors.length,
                total_warnings: this.warnings.length,
                critical_issues: criticalIssues
            }
        };
    }
}

/**
 * Convenience function for validating a full hierarchy
 */
export function validateHierarchy(
    epic: Epic,
    features: Feature[],
    stories: Story[],
    tasks: Task[]
): ValidationResult {
    const validator = new HierarchyValidator();
    return validator.validateEpic(epic, features, stories, tasks);
}

/**
 * Convenience function for validating features only
 */
export function validateFeatures(features: Feature[]): ValidationResult {
    const validator = new HierarchyValidator();
    return validator.validateFeatures(features);
}

/**
 * Convenience function for validating stories only
 */
export function validateStories(stories: Story[]): ValidationResult {
    const validator = new HierarchyValidator();
    return validator.validateStories(stories);
}

/**
 * Convenience function for validating tasks only
 */
export function validateTasks(tasks: Task[]): ValidationResult {
    const validator = new HierarchyValidator();
    return validator.validateTasks(tasks);
}
