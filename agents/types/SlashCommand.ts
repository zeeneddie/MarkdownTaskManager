/**
 * SlashCommand Types for SuperClaude Framework
 *
 * Defines types for slash command system that provides specialized AI personas
 * with domain expertise for agents to use.
 */

/**
 * Available slash commands
 */
export enum SlashCommandType {
  ARCHITECT = 'architect',
  REVIEWER = 'reviewer',
  OPTIMIZER = 'optimizer',
  DEBUGGER = 'debugger',
  TESTER = 'tester',
  DOCUMENTER = 'documenter',
  SECURITY = 'security',
  REFACTOR = 'refactor',
  API_DESIGNER = 'api-designer',
  DATABASE = 'database',
  FRONTEND = 'frontend',
  BACKEND = 'backend',
  DEVOPS = 'devops',
  ACCESSIBILITY = 'accessibility',
  PERFORMANCE = 'performance',
  MIGRATION = 'migration',
  // Spec-Kit Workflow Commands (Week 8)
  CONSTITUTION = 'constitution',
  SPECIFICATION = 'specification',
  TASKS = 'tasks'
}

/**
 * Command execution status
 */
export enum CommandStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

/**
 * Command output format
 */
export enum OutputFormat {
  TEXT = 'text',
  MARKDOWN = 'markdown',
  JSON = 'json',
  CODE = 'code',
  DIFF = 'diff'
}

/**
 * Recommendation priority
 */
export enum RecommendationPriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  OPTIONAL = 'optional'
}

/**
 * Input for slash command execution
 */
export interface SlashCommandInput {
  command: SlashCommandType;
  context: CommandContext;
  options?: CommandOptions;
}

/**
 * Context for command execution
 */
export interface CommandContext {
  code?: string;                    // Code to analyze
  filePath?: string;                // File path being analyzed
  language?: string;                // Programming language
  framework?: string;               // Framework being used
  projectType?: string;             // Type of project (web, api, mobile, etc.)
  dependencies?: string[];          // Project dependencies
  existingPatterns?: string[];      // Existing architecture patterns
  constraints?: string[];           // Project constraints
  requirements?: string[];          // Specific requirements
  metadata?: Record<string, any>;   // Additional metadata
}

/**
 * Options for command execution
 */
export interface CommandOptions {
  verbose?: boolean;                // Include detailed explanations
  includeExamples?: boolean;        // Include code examples
  outputFormat?: OutputFormat;      // Desired output format
  maxRecommendations?: number;      // Max number of recommendations
  focusAreas?: string[];           // Specific areas to focus on
  excludeAreas?: string[];         // Areas to exclude
  confidenceThreshold?: number;     // Minimum confidence (0-1)
}

/**
 * Recommendation from slash command
 */
export interface Recommendation {
  id: string;
  priority: RecommendationPriority;
  category: string;
  title: string;
  description: string;
  rationale: string;                // Why this recommendation
  benefits: string[];               // Benefits of implementing
  tradeoffs?: string[];            // Potential tradeoffs
  effort: 'LOW' | 'MEDIUM' | 'HIGH';
  impact: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence: number;               // 0.0-1.0
  implementation?: ImplementationGuide;
  relatedRecommendations?: string[]; // Related recommendation IDs
}

/**
 * Implementation guide for a recommendation
 */
export interface ImplementationGuide {
  steps: string[];                  // Step-by-step instructions
  codeExample?: string;             // Code example
  beforeAfter?: {
    before: string;
    after: string;
  };
  references?: string[];            // Links to docs/articles
  estimatedTime?: string;           // Estimated implementation time
  prerequisites?: string[];         // What needs to be in place first
}

/**
 * Analysis result from slash command
 */
export interface AnalysisResult {
  summary: string;
  scores?: Record<string, number>;  // Various quality scores
  metrics?: Record<string, any>;    // Metrics collected
  issues?: Issue[];                 // Issues found
  strengths?: string[];             // What's good
  weaknesses?: string[];            // What needs improvement
  patterns?: Pattern[];             // Patterns detected
}

/**
 * Issue detected by slash command
 */
export interface Issue {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  title: string;
  description: string;
  location: string;                 // File:line or code snippet
  codeSnippet?: string;
  recommendation: string;
  autoFixable: boolean;
}

/**
 * Pattern detected in code
 */
export interface Pattern {
  name: string;
  type: 'DESIGN_PATTERN' | 'ANTI_PATTERN' | 'IDIOM' | 'CONVENTION';
  description: string;
  locations: string[];
  confidence: number;               // 0.0-1.0
  assessment: 'GOOD' | 'NEUTRAL' | 'BAD';
}

/**
 * Output from slash command execution
 */
export interface SlashCommandOutput {
  commandId: string;
  command: SlashCommandType;
  status: CommandStatus;
  executedBy: string;               // Agent name
  executedAt: Date;
  completedAt?: Date;
  duration: number;                 // Milliseconds

  // Results
  analysis: AnalysisResult;
  recommendations: Recommendation[];
  topRecommendation?: Recommendation;

  // Metadata
  confidence: number;               // Overall confidence in output
  needsHumanReview: boolean;
  rationale: string;                // Why these recommendations
  nextSteps?: string[];             // Suggested next actions

  // Output formatting
  outputFormat: OutputFormat;
  formattedOutput: string;
}

/**
 * Slash command session (can include multiple executions)
 */
export interface SlashCommandSession {
  sessionId: string;
  command: SlashCommandType;
  executions: SlashCommandOutput[];
  aggregatedRecommendations: Recommendation[];
  finalStatus: CommandStatus;
  totalDuration: number;
}

/**
 * Command definition (metadata about a slash command)
 */
export interface CommandDefinition {
  type: SlashCommandType;
  name: string;
  description: string;
  persona: string;                  // Description of AI persona
  expertise: string[];              // Areas of expertise
  capabilities: string[];           // What it can do
  bestUsedFor: string[];           // When to use this command
  requiredContext: string[];        // What context is needed
  optionalContext: string[];        // What context is helpful
  outputTypes: OutputFormat[];      // Supported output formats
  examples: CommandExample[];
}

/**
 * Example usage of a command
 */
export interface CommandExample {
  scenario: string;
  input: Partial<SlashCommandInput>;
  expectedOutcome: string;
}

/**
 * Command registry entry
 */
export interface CommandRegistryEntry {
  definition: CommandDefinition;
  executor: CommandExecutor;
  enabled: boolean;
  usageCount: number;
  averageDuration: number;
  successRate: number;
}

/**
 * Command executor function type
 */
export type CommandExecutor = (
  input: SlashCommandInput
) => Promise<SlashCommandOutput>;

/**
 * Helper: Create recommendation
 */
export function createRecommendation(
  priority: RecommendationPriority,
  category: string,
  title: string,
  description: string,
  effort: 'LOW' | 'MEDIUM' | 'HIGH',
  impact: 'LOW' | 'MEDIUM' | 'HIGH'
): Recommendation {
  return {
    id: `rec-${Date.now()}-${Math.random()}`,
    priority,
    category,
    title,
    description,
    rationale: '',
    benefits: [],
    effort,
    impact,
    confidence: 0.8,
    relatedRecommendations: []
  };
}

/**
 * Helper: Calculate recommendation score
 */
export function calculateRecommendationScore(rec: Recommendation): number {
  const priorityWeight = {
    [RecommendationPriority.CRITICAL]: 100,
    [RecommendationPriority.HIGH]: 75,
    [RecommendationPriority.MEDIUM]: 50,
    [RecommendationPriority.LOW]: 25,
    [RecommendationPriority.OPTIONAL]: 10
  };

  const effortPenalty = {
    'LOW': 0,
    'MEDIUM': 10,
    'HIGH': 25
  };

  const impactBonus = {
    'LOW': 0,
    'MEDIUM': 15,
    'HIGH': 30
  };

  let score = priorityWeight[rec.priority];
  score -= effortPenalty[rec.effort];
  score += impactBonus[rec.impact];
  score *= rec.confidence;

  return Math.round(score);
}

/**
 * Helper: Sort recommendations by priority
 */
export function sortRecommendations(
  recommendations: Recommendation[]
): Recommendation[] {
  return [...recommendations].sort((a, b) => {
    const scoreA = calculateRecommendationScore(a);
    const scoreB = calculateRecommendationScore(b);
    return scoreB - scoreA;
  });
}

/**
 * Helper: Filter recommendations by confidence threshold
 */
export function filterByConfidence(
  recommendations: Recommendation[],
  threshold: number
): Recommendation[] {
  return recommendations.filter(rec => rec.confidence >= threshold);
}

/**
 * Helper: Group recommendations by category
 */
export function groupRecommendationsByCategory(
  recommendations: Recommendation[]
): Record<string, Recommendation[]> {
  return recommendations.reduce((groups, rec) => {
    if (!groups[rec.category]) {
      groups[rec.category] = [];
    }
    groups[rec.category].push(rec);
    return groups;
  }, {} as Record<string, Recommendation[]>);
}
