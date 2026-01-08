/**
 * Generic CSV Exporter
 *
 * Exports task hierarchies to a flat CSV format with all details.
 * Useful for data analysis, Excel imports, or custom processing.
 */

import { ExportOptions, ExportResult } from './index';

interface Epic {
    id?: string;
    title: string;
    description: string;
    business_value?: string;
    estimated_story_points?: number;
    estimated_weeks?: number;
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
    complexity?: string;
    priority: string;
}

interface Story {
    id?: string;
    feature_id?: string;
    title: string;
    description: string;
    user_type?: string;
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
 * Escape CSV field
 */
function escapeCSV(value: any): string {
    if (value === null || value === undefined) return '';

    let escaped = String(value);
    escaped = escaped.replace(/\r?\n/g, ' ').replace(/\t/g, ' ');

    if (escaped.includes(',') || escaped.includes('"') || escaped.includes('\n')) {
        escaped = '"' + escaped.replace(/"/g, '""') + '"';
    }

    return escaped;
}

/**
 * Export to flat CSV format (all hierarchy levels)
 */
export function exportToCSV(
    epic: Epic,
    features: Feature[] = [],
    stories: Story[] = [],
    tasks: Task[] = [],
    options: ExportOptions = {}
): ExportResult {
    const rows: string[] = [];

    // CSV Header (comprehensive format)
    rows.push([
        'Level',
        'ID',
        'Title',
        'Description',
        'Priority',
        'Story Points',
        'Time Estimate',
        'Parent',
        'Type',
        'Status',
        'Business Value',
        'Technical Notes',
        'User Type',
        'Acceptance Criteria Count'
    ].join(','));

    // Export epic
    rows.push([
        escapeCSV('Epic'),
        escapeCSV(epic.id || ''),
        escapeCSV(epic.title),
        escapeCSV(epic.description),
        escapeCSV(epic.priority),
        escapeCSV(epic.estimated_story_points || ''),
        escapeCSV(epic.estimated_weeks ? `${epic.estimated_weeks} weeks` : ''),
        escapeCSV(''),
        escapeCSV('Epic'),
        escapeCSV('To Do'),
        escapeCSV(epic.business_value || ''),
        escapeCSV(''),
        escapeCSV(''),
        escapeCSV('')
    ].join(','));

    // Export features
    features.forEach(feature => {
        rows.push([
            escapeCSV('Feature'),
            escapeCSV(feature.id || ''),
            escapeCSV(feature.title),
            escapeCSV(feature.description),
            escapeCSV(feature.priority),
            escapeCSV(feature.estimated_story_points || ''),
            escapeCSV(feature.estimated_days ? `${feature.estimated_days} days` : ''),
            escapeCSV(epic.title),
            escapeCSV('Feature'),
            escapeCSV('To Do'),
            escapeCSV(''),
            escapeCSV(feature.technical_approach || ''),
            escapeCSV(''),
            escapeCSV('')
        ].join(','));

        // Export stories for this feature
        const featureStories = stories.filter(s => s.feature_id === feature.id);
        featureStories.forEach(story => {
            rows.push([
                escapeCSV('Story'),
                escapeCSV(story.id || ''),
                escapeCSV(story.title),
                escapeCSV(story.description),
                escapeCSV(story.priority),
                escapeCSV(story.story_points || ''),
                escapeCSV(story.estimated_hours ? `${story.estimated_hours} hours` : ''),
                escapeCSV(feature.title),
                escapeCSV('User Story'),
                escapeCSV('To Do'),
                escapeCSV(''),
                escapeCSV(''),
                escapeCSV(story.user_type || ''),
                escapeCSV('')
            ].join(','));

            // Export tasks for this story
            const storyTasks = tasks.filter(t => t.story_id === story.id);
            storyTasks.forEach(task => {
                rows.push([
                    escapeCSV('Task'),
                    escapeCSV(task.id || ''),
                    escapeCSV(task.title),
                    escapeCSV(task.description || ''),
                    escapeCSV(task.priority),
                    escapeCSV(''),
                    escapeCSV(task.estimated_hours ? `${task.estimated_hours} hours` : ''),
                    escapeCSV(story.title),
                    escapeCSV(task.task_type || 'Task'),
                    escapeCSV('To Do'),
                    escapeCSV(''),
                    escapeCSV(''),
                    escapeCSV(''),
                    escapeCSV('')
                ].join(','));
            });
        });
    });

    const content = rows.join('\n');
    const filename = `task-hierarchy-${epic.id || 'generated'}-${Date.now()}.csv`;

    return {
        format: 'csv',
        content,
        filename,
        size: content.length
    };
}

/**
 * Export summary CSV (high-level metrics only)
 */
export function exportSummaryCSV(
    epic: Epic,
    features: Feature[] = [],
    stories: Story[] = [],
    tasks: Task[] = []
): ExportResult {
    const rows: string[] = [];

    // Summary header
    rows.push(['Metric', 'Value'].join(','));

    // Calculate metrics
    const totalStoryPoints = features.reduce((sum, f) => sum + (f.estimated_story_points || 0), 0);
    const totalDays = features.reduce((sum, f) => sum + (f.estimated_days || 0), 0);
    const totalHours = stories.reduce((sum, s) => sum + (s.estimated_hours || 0), 0);

    // Summary metrics
    rows.push([escapeCSV('Epic'), escapeCSV(epic.title)].join(','));
    rows.push([escapeCSV('Total Features'), escapeCSV(features.length)].join(','));
    rows.push([escapeCSV('Total Stories'), escapeCSV(stories.length)].join(','));
    rows.push([escapeCSV('Total Tasks'), escapeCSV(tasks.length)].join(','));
    rows.push([escapeCSV('Total Story Points'), escapeCSV(totalStoryPoints)].join(','));
    rows.push([escapeCSV('Total Days Estimate'), escapeCSV(totalDays)].join(','));
    rows.push([escapeCSV('Total Hours Estimate'), escapeCSV(totalHours)].join(','));
    rows.push([escapeCSV('Epic Story Points'), escapeCSV(epic.estimated_story_points || '')].join(','));
    rows.push([escapeCSV('Epic Weeks'), escapeCSV(epic.estimated_weeks || '')].join(','));

    // Priority breakdown
    rows.push(['', ''].join(','));  // Empty row
    rows.push([escapeCSV('Priority Breakdown'), ''].join(','));
    const priorities = ['critical', 'high', 'medium', 'low'];
    priorities.forEach(priority => {
        const count = features.filter(f => f.priority === priority).length;
        rows.push([escapeCSV(`  ${priority}`), escapeCSV(count)].join(','));
    });

    const content = rows.join('\n');
    const filename = `summary-${epic.id || 'generated'}-${Date.now()}.csv`;

    return {
        format: 'csv-summary',
        content,
        filename,
        size: content.length
    };
}
