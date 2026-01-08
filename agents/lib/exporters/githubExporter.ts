/**
 * GitHub Projects Exporter
 *
 * Exports task hierarchies to GitHub Projects CSV format.
 * Compatible with GitHub Projects import feature.
 */

import { ExportOptions, ExportResult } from './index';

interface Epic {
    id?: string;
    title: string;
    description: string;
    business_value?: string;
    estimated_story_points?: number;
    priority: string;
}

interface Feature {
    id?: string;
    epic_id?: string;
    title: string;
    description: string;
    estimated_story_points?: number;
    estimated_days?: number;
    priority: string;
}

interface Story {
    id?: string;
    feature_id?: string;
    title: string;
    description: string;
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

/**
 * Escape CSV field (handle commas, quotes, newlines)
 */
function escapeCSV(value: string | undefined): string {
    if (!value) return '';

    // Convert to string and escape
    let escaped = String(value);

    // Replace newlines with spaces
    escaped = escaped.replace(/\r?\n/g, ' ');

    // If contains comma, quote, or newline, wrap in quotes and escape quotes
    if (escaped.includes(',') || escaped.includes('"') || escaped.includes('\n')) {
        escaped = '"' + escaped.replace(/"/g, '""') + '"';
    }

    return escaped;
}

/**
 * Map priority to GitHub label
 */
function mapPriority(priority: string): string {
    const priorityMap: Record<string, string> = {
        'critical': 'Priority: Critical',
        'high': 'Priority: High',
        'medium': 'Priority: Medium',
        'low': 'Priority: Low'
    };
    return priorityMap[priority] || 'Priority: Medium';
}

/**
 * Convert hours to estimate string
 */
function formatEstimate(hours: number): string {
    if (hours >= 8) {
        return `${Math.round(hours / 8 * 10) / 10}d`;
    }
    return `${hours}h`;
}

/**
 * Export to GitHub Projects CSV format
 */
export function exportToGitHub(
    epic: Epic,
    features: Feature[] = [],
    stories: Story[] = [],
    tasks: Task[] = [],
    options: ExportOptions = {}
): ExportResult {
    const rows: string[] = [];

    // CSV Header (GitHub Projects format)
    rows.push('Title,Description,Labels,Estimate,Priority,Status,Type,Parent');

    // Export epic as milestone/issue
    rows.push([
        escapeCSV(epic.title),
        escapeCSV(epic.description + (epic.business_value ? `\n\nBusiness Value: ${epic.business_value}` : '')),
        escapeCSV(`type: epic, ${mapPriority(epic.priority)}, felix-generated`),
        escapeCSV(epic.estimated_story_points ? `${epic.estimated_story_points} SP` : ''),
        escapeCSV(mapPriority(epic.priority)),
        escapeCSV('To Do'),
        escapeCSV('Epic'),
        escapeCSV('')
    ].join(','));

    // Export features
    features.forEach(feature => {
        rows.push([
            escapeCSV(feature.title),
            escapeCSV(feature.description),
            escapeCSV(`type: feature, ${mapPriority(feature.priority)}, felix-generated`),
            escapeCSV(feature.estimated_story_points ? `${feature.estimated_story_points} SP` : ''),
            escapeCSV(mapPriority(feature.priority)),
            escapeCSV('To Do'),
            escapeCSV('Issue'),
            escapeCSV(epic.title) // Parent is epic
        ].join(','));

        // Export stories for this feature
        const featureStories = stories.filter(s => s.feature_id === feature.id);
        featureStories.forEach(story => {
            rows.push([
                escapeCSV(story.title),
                escapeCSV(story.description),
                escapeCSV(`type: story, ${mapPriority(story.priority)}, felix-generated`),
                escapeCSV(story.story_points ? `${story.story_points} SP` : ''),
                escapeCSV(mapPriority(story.priority)),
                escapeCSV('To Do'),
                escapeCSV('Issue'),
                escapeCSV(feature.title) // Parent is feature
            ].join(','));

            // Export tasks for this story
            const storyTasks = tasks.filter(t => t.story_id === story.id);
            storyTasks.forEach(task => {
                rows.push([
                    escapeCSV(task.title),
                    escapeCSV(task.description || ''),
                    escapeCSV(`type: task, ${task.task_type || 'general'}, ${mapPriority(task.priority)}, felix-generated`),
                    escapeCSV(task.estimated_hours ? formatEstimate(task.estimated_hours) : ''),
                    escapeCSV(mapPriority(task.priority)),
                    escapeCSV('To Do'),
                    escapeCSV('Task'),
                    escapeCSV(story.title) // Parent is story
                ].join(','));
            });
        });
    });

    const content = rows.join('\n');
    const filename = `github-projects-${epic.id || 'generated'}-${Date.now()}.csv`;

    return {
        format: 'github-csv',
        content,
        filename,
        size: content.length
    };
}

/**
 * Export just features to GitHub CSV
 */
export function exportFeaturesToGitHub(features: Feature[], options: ExportOptions = {}): ExportResult {
    const rows: string[] = [];

    // CSV Header
    rows.push('Title,Description,Labels,Estimate,Priority,Status,Type');

    // Export features
    features.forEach(feature => {
        rows.push([
            escapeCSV(feature.title),
            escapeCSV(feature.description),
            escapeCSV(`type: feature, ${mapPriority(feature.priority)}, felix-generated`),
            escapeCSV(feature.estimated_story_points ? `${feature.estimated_story_points} SP` : ''),
            escapeCSV(mapPriority(feature.priority)),
            escapeCSV('To Do'),
            escapeCSV('Issue')
        ].join(','));
    });

    const content = rows.join('\n');
    const filename = `github-features-${Date.now()}.csv`;

    return {
        format: 'github-csv',
        content,
        filename,
        size: content.length
    };
}
