/**
 * Markdown Exporter
 *
 * Exports task hierarchies to human-readable Markdown documentation.
 * Perfect for project documentation, README files, or team wikis.
 */

import { ExportOptions, ExportResult } from './index';

interface Epic {
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

interface Feature {
    id?: string;
    epic_id?: string;
    title: string;
    description: string;
    technical_approach?: string;
    api_endpoints?: Array<{ method: string; path: string; description: string }>;
    database_changes?: Array<{ table: string; action: string }>;
    dependencies?: string[];
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
    user_goal?: string;
    user_benefit?: string;
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
    technical_notes?: string;
    code_files?: string[];
    estimated_hours?: number;
    priority: string;
}

/**
 * Format priority with emoji
 */
function formatPriority(priority: string): string {
    const icons: Record<string, string> = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    };
    return `${icons[priority] || '⚪'} ${priority.charAt(0).toUpperCase() + priority.slice(1)}`;
}

/**
 * Export to detailed Markdown format
 */
export function exportToMarkdown(
    epic: Epic,
    features: Feature[] = [],
    stories: Story[] = [],
    tasks: Task[] = [],
    options: ExportOptions = {}
): ExportResult {
    const lines: string[] = [];

    // Title and metadata
    lines.push(`# ${epic.title}`);
    lines.push('');
    lines.push(`> **Generated**: ${new Date().toLocaleDateString()}`);
    lines.push(`> **Generator**: Felix (Feature Architect) · qwen2.5-coder:7b`);
    lines.push(`> **Priority**: ${formatPriority(epic.priority)}`);
    lines.push('');
    lines.push('---');
    lines.push('');

    // Epic description
    lines.push('## Overview');
    lines.push('');
    lines.push(epic.description);
    lines.push('');

    // Business value
    if (epic.business_value) {
        lines.push('## Business Value');
        lines.push('');
        lines.push(epic.business_value);
        lines.push('');
    }

    // Estimates
    if (epic.estimated_story_points || epic.estimated_weeks) {
        lines.push('## Estimates');
        lines.push('');
        if (epic.estimated_story_points) {
            lines.push(`- **Story Points**: ${epic.estimated_story_points}`);
        }
        if (epic.estimated_weeks) {
            lines.push(`- **Timeline**: ${epic.estimated_weeks} weeks`);
        }
        lines.push('');
    }

    // User personas
    if (epic.user_personas && epic.user_personas.length > 0) {
        lines.push('## Target Users');
        lines.push('');
        epic.user_personas.forEach(persona => {
            lines.push(`- ${persona}`);
        });
        lines.push('');
    }

    // Acceptance criteria
    if (epic.acceptance_criteria && epic.acceptance_criteria.length > 0) {
        lines.push('## Acceptance Criteria');
        lines.push('');
        epic.acceptance_criteria.forEach((criterion, index) => {
            lines.push(`${index + 1}. ${criterion}`);
        });
        lines.push('');
    }

    // Summary statistics
    const totalStoryPoints = features.reduce((sum, f) => sum + (f.estimated_story_points || 0), 0);
    const totalDays = features.reduce((sum, f) => sum + (f.estimated_days || 0), 0);
    const totalHours = stories.reduce((sum, s) => sum + (s.estimated_hours || 0), 0);

    lines.push('## Summary Statistics');
    lines.push('');
    lines.push('| Metric | Value |');
    lines.push('|--------|-------|');
    lines.push(`| Features | ${features.length} |`);
    lines.push(`| Stories | ${stories.length} |`);
    lines.push(`| Tasks | ${tasks.length} |`);
    lines.push(`| Total Story Points | ${totalStoryPoints} |`);
    lines.push(`| Total Days | ${totalDays} |`);
    lines.push(`| Total Hours | ${totalHours} |`);
    lines.push('');

    // Features breakdown
    lines.push('---');
    lines.push('');
    lines.push('## Features');
    lines.push('');

    features.forEach((feature, featureIndex) => {
        lines.push(`### ${featureIndex + 1}. ${feature.title}`);
        lines.push('');
        lines.push(`**Priority**: ${formatPriority(feature.priority)} | **Story Points**: ${feature.estimated_story_points || 'N/A'} | **Complexity**: ${feature.complexity || 'N/A'}`);
        lines.push('');
        lines.push(feature.description);
        lines.push('');

        // Technical approach
        if (feature.technical_approach) {
            lines.push('**Technical Approach**:');
            lines.push('');
            lines.push(feature.technical_approach);
            lines.push('');
        }

        // API endpoints
        if (feature.api_endpoints && feature.api_endpoints.length > 0) {
            lines.push('**API Endpoints**:');
            lines.push('');
            feature.api_endpoints.forEach(endpoint => {
                lines.push(`- \`${endpoint.method} ${endpoint.path}\` - ${endpoint.description}`);
            });
            lines.push('');
        }

        // Dependencies
        if (feature.dependencies && feature.dependencies.length > 0) {
            lines.push('**Dependencies**: ' + feature.dependencies.join(', '));
            lines.push('');
        }

        // Stories for this feature
        const featureStories = stories.filter(s => s.feature_id === feature.id);
        if (featureStories.length > 0) {
            lines.push('#### User Stories');
            lines.push('');

            featureStories.forEach((story, storyIndex) => {
                lines.push(`**Story ${featureIndex + 1}.${storyIndex + 1}**: ${story.title}`);
                lines.push('');
                lines.push(`*Priority*: ${formatPriority(story.priority)} | *Story Points*: ${story.story_points || 'N/A'} | *Hours*: ${story.estimated_hours || 'N/A'}`);
                lines.push('');

                // Acceptance criteria
                if (story.acceptance_criteria && story.acceptance_criteria.length > 0) {
                    lines.push('**Acceptance Criteria**:');
                    lines.push('');
                    story.acceptance_criteria.forEach((ac, acIndex) => {
                        lines.push(`${acIndex + 1}. **Given**: ${ac.given}`);
                        lines.push(`   **When**: ${ac.when}`);
                        lines.push(`   **Then**: ${ac.then}`);
                    });
                    lines.push('');
                }

                // Tasks for this story
                const storyTasks = tasks.filter(t => t.story_id === story.id);
                if (storyTasks.length > 0) {
                    lines.push('**Tasks**:');
                    lines.push('');
                    storyTasks.forEach((task, taskIndex) => {
                        lines.push(`- [ ] **${task.title}** (${task.estimated_hours || 0}h) [${task.task_type || 'task'}]`);
                        if (task.description) {
                            lines.push(`  ${task.description}`);
                        }
                        if (task.code_files && task.code_files.length > 0) {
                            lines.push(`  Files: \`${task.code_files.join('`, `')}\``);
                        }
                    });
                    lines.push('');
                }
            });
        }

        lines.push('');
    });

    // Footer
    lines.push('---');
    lines.push('');
    lines.push('*Generated by Felix (Feature Architect) using qwen2.5-coder:7b*');
    lines.push('');

    const content = lines.join('\n');
    const filename = `${epic.title.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.md`;

    return {
        format: 'markdown',
        content,
        filename,
        size: content.length
    };
}

/**
 * Export summary markdown (high-level only)
 */
export function exportSummaryMarkdown(
    epic: Epic,
    features: Feature[] = []
): ExportResult {
    const lines: string[] = [];

    lines.push(`# ${epic.title} - Summary`);
    lines.push('');
    lines.push(`${epic.description}`);
    lines.push('');

    if (epic.business_value) {
        lines.push(`**Business Value**: ${epic.business_value}`);
        lines.push('');
    }

    lines.push('## Features Overview');
    lines.push('');
    lines.push('| # | Feature | Story Points | Days | Priority |');
    lines.push('|---|---------|--------------|------|----------|');

    features.forEach((feature, index) => {
        lines.push(`| ${index + 1} | ${feature.title} | ${feature.estimated_story_points || 'N/A'} | ${feature.estimated_days || 'N/A'} | ${feature.priority} |`);
    });

    lines.push('');

    const content = lines.join('\n');
    const filename = `${epic.title.toLowerCase().replace(/\s+/g, '-')}-summary-${Date.now()}.md`;

    return {
        format: 'markdown-summary',
        content,
        filename,
        size: content.length
    };
}
