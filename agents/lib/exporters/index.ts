/**
 * Export Module - Entry Point
 *
 * Exports generated task hierarchies to various formats:
 * - Jira (JSON import format)
 * - GitHub Projects (CSV)
 * - Generic CSV
 * - Markdown documentation
 */

export { exportToJira } from './jiraExporter';
export { exportToGitHub } from './githubExporter';
export { exportToCSV, exportSummaryCSV } from './csvExporter';
export { exportToMarkdown } from './markdownExporter';

export interface ExportOptions {
    includeMetadata?: boolean;
    includeValidation?: boolean;
    format?: 'detailed' | 'summary';
}

export interface ExportResult {
    format: string;
    content: string;
    filename: string;
    size: number;
}
