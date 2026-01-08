/**
 * Jira Exporter
 *
 * Exports task hierarchies to Jira JSON import format.
 * Supports:
 * - Epics → Jira Epics
 * - Features → Jira Stories (with epic link)
 * - Stories → Jira Sub-tasks
 * - Tasks → Jira Sub-tasks
 */

import { ExportOptions, ExportResult } from './index';

interface Epic {
    id?: string;
    title: string;
    description: string;
    business_value?: string;
    acceptance_criteria?: string[];
    estimated_story_points?: number;
    priority: string;
}

interface Feature {
    id?: string;
    epic_id?: string;
    title: string;
    description: string;
    technical_approach?: string;
    estimated_story_points?: number;
    estimated_days?: number;
    priority: string;
    dependencies?: string[];
}

interface Story {
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

interface Task {
    id?: string;
    story_id?: string;
    title: string;
    description?: string;
    task_type?: string;
    estimated_hours?: number;
    priority: string;
}

interface JiraIssue {
    issueType: string;
    summary: string;
    description: string;
    priority: string;
    storyPoints?: number;
    timeEstimate?: string;
    epicLink?: string;
    parentKey?: string;
    labels?: string[];
    customFields?: Record<string, any>;
}

/**
 * Map priority to Jira format
 */
function mapPriority(priority: string): string {
    const priorityMap: Record<string, string> = {
        'critical': 'Highest',
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low'
    };
    return priorityMap[priority] || 'Medium';
}

/**
 * Convert hours to Jira time format (e.g., "8h", "2d")
 */
function formatTimeEstimate(hours: number): string {
    if (hours >= 8) {
        const days = Math.round(hours / 8 * 10) / 10;
        return `${days}d`;
    }
    return `${hours}h`;
}

/**
 * Export epic to Jira epic format
 */
function exportEpic(epic: Epic): JiraIssue {
    let description = epic.description;

    if (epic.business_value) {
        description += `\n\n*Business Value*\n${epic.business_value}`;
    }

    if (epic.acceptance_criteria && epic.acceptance_criteria.length > 0) {
        description += '\n\n*Acceptance Criteria*\n';
        epic.acceptance_criteria.forEach((criterion, index) => {
            description += `${index + 1}. ${criterion}\n`;
        });
    }

    return {
        issueType: 'Epic',
        summary: epic.title,
        description,
        priority: mapPriority(epic.priority),
        storyPoints: epic.estimated_story_points,
        labels: ['felix-generated', 'week-12']
    };
}

/**
 * Export feature to Jira story format
 */
function exportFeature(feature: Feature, epicKey: string): JiraIssue {
    let description = feature.description;

    if (feature.technical_approach) {
        description += `\n\n*Technical Approach*\n${feature.technical_approach}`;
    }

    if (feature.dependencies && feature.dependencies.length > 0) {
        description += `\n\n*Dependencies*\n${feature.dependencies.join(', ')}`;
    }

    const timeEstimate = feature.estimated_days ? formatTimeEstimate(feature.estimated_days * 8) : undefined;

    return {
        issueType: 'Story',
        summary: feature.title,
        description,
        priority: mapPriority(feature.priority),
        storyPoints: feature.estimated_story_points,
        timeEstimate,
        epicLink: epicKey,
        labels: ['felix-generated', 'feature']
    };
}

/**
 * Export story to Jira story/sub-task format
 */
function exportStory(story: Story, parentKey: string): JiraIssue {
    let description = story.description;

    if (story.acceptance_criteria && story.acceptance_criteria.length > 0) {
        description += '\n\n*Acceptance Criteria (Given/When/Then)*\n';
        story.acceptance_criteria.forEach((ac, index) => {
            description += `\n${index + 1}. *Given:* ${ac.given}\n   *When:* ${ac.when}\n   *Then:* ${ac.then}\n`;
        });
    }

    const timeEstimate = story.estimated_hours ? formatTimeEstimate(story.estimated_hours) : undefined;

    return {
        issueType: 'Sub-task',
        summary: story.title,
        description,
        priority: mapPriority(story.priority),
        storyPoints: story.story_points,
        timeEstimate,
        parentKey,
        labels: ['felix-generated', 'user-story']
    };
}

/**
 * Export task to Jira sub-task format
 */
function exportTask(task: Task, parentKey: string): JiraIssue {
    const timeEstimate = task.estimated_hours ? formatTimeEstimate(task.estimated_hours) : undefined;

    return {
        issueType: 'Sub-task',
        summary: task.title,
        description: task.description || '',
        priority: mapPriority(task.priority),
        timeEstimate,
        parentKey,
        labels: ['felix-generated', 'task', task.task_type || 'general']
    };
}

/**
 * Export full hierarchy to Jira format
 */
export function exportToJira(
    epic: Epic,
    features: Feature[] = [],
    stories: Story[] = [],
    tasks: Task[] = [],
    options: ExportOptions = {}
): ExportResult {
    const issues: JiraIssue[] = [];

    // Export epic
    const epicIssue = exportEpic(epic);
    issues.push(epicIssue);
    const epicKey = `EPIC-${epic.id || 'generated'}`;

    // Export features
    features.forEach(feature => {
        const featureIssue = exportFeature(feature, epicKey);
        issues.push(featureIssue);
        const featureKey = `STORY-${feature.id || 'generated'}`;

        // Export stories for this feature
        const featureStories = stories.filter(s => s.feature_id === feature.id);
        featureStories.forEach(story => {
            const storyIssue = exportStory(story, featureKey);
            issues.push(storyIssue);
            const storyKey = `SUBTASK-${story.id || 'generated'}`;

            // Export tasks for this story
            const storyTasks = tasks.filter(t => t.story_id === story.id);
            storyTasks.forEach(task => {
                const taskIssue = exportTask(task, storyKey);
                issues.push(taskIssue);
            });
        });
    });

    // Build Jira import JSON
    const jiraExport = {
        projects: [
            {
                name: epic.title,
                key: `PROJ-${Date.now()}`,
                description: epic.description,
                issues: issues
            }
        ],
        metadata: options.includeMetadata ? {
            exported_at: new Date().toISOString(),
            generator: 'Felix (Feature Architect)',
            model: 'qwen2.5-coder:7b',
            total_issues: issues.length,
            breakdown: {
                epics: 1,
                features: features.length,
                stories: stories.length,
                tasks: tasks.length
            }
        } : undefined
    };

    const content = JSON.stringify(jiraExport, null, 2);
    const filename = `jira-export-${epic.id || 'generated'}-${Date.now()}.json`;

    return {
        format: 'jira-json',
        content,
        filename,
        size: content.length
    };
}

/**
 * Export just features to Jira (without full hierarchy)
 */
export function exportFeaturesToJira(features: Feature[], options: ExportOptions = {}): ExportResult {
    const issues: JiraIssue[] = features.map(feature => ({
        issueType: 'Story',
        summary: feature.title,
        description: feature.description + (feature.technical_approach ? `\n\n*Technical Approach*\n${feature.technical_approach}` : ''),
        priority: mapPriority(feature.priority),
        storyPoints: feature.estimated_story_points,
        timeEstimate: feature.estimated_days ? formatTimeEstimate(feature.estimated_days * 8) : undefined,
        labels: ['felix-generated', 'feature']
    }));

    const jiraExport = {
        issues,
        metadata: options.includeMetadata ? {
            exported_at: new Date().toISOString(),
            total_issues: issues.length
        } : undefined
    };

    const content = JSON.stringify(jiraExport, null, 2);
    const filename = `jira-features-${Date.now()}.json`;

    return {
        format: 'jira-json',
        content,
        filename,
        size: content.length
    };
}
