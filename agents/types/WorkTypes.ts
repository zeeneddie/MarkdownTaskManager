/**
 * Work Type Definitions
 *
 * Shared types for work classification and routing.
 * Extracted to avoid circular dependencies.
 */

export enum WorkType {
  PROJECT_DEFINITION = 'PROJECT_DEFINITION',
  NEW_FEATURE = 'NEW_FEATURE',
  MAINTENANCE = 'MAINTENANCE',
  QUALITY_AUDIT = 'QUALITY_AUDIT',
  BUG = 'BUG',
  ENHANCEMENT = 'ENHANCEMENT',
  MIGRATION = 'MIGRATION',
  QUALITY_IMPROVEMENT = 'QUALITY_IMPROVEMENT',
  TESTING = 'TESTING'
}

export interface ClassificationResult {
  workType: WorkType;
  confidence: number;
  reasoning: string;
  needsUserConfirmation: boolean;
  alternativeOptions?: Array<{
    workType: WorkType;
    confidence: number;
  }>;
}
