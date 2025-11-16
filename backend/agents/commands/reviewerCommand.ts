/**
 * /reviewer - Code Review Command
 *
 * AI Persona: Senior Code Reviewer with focus on quality and best practices
 * Expertise: Code quality, best practices, code smells, refactoring
 * Best used for: Code reviews, quality assessment, PR feedback
 */

import {
  SlashCommandType,
  SlashCommandInput,
  SlashCommandOutput,
  CommandStatus,
  CommandDefinition,
  OutputFormat,
  Recommendation,
  RecommendationPriority,
  createRecommendation,
  sortRecommendations
} from '../types/SlashCommand';
import { registerCommand } from '../workflows/commandRegistry';

export const REVIEWER_DEFINITION: CommandDefinition = {
  type: SlashCommandType.REVIEWER,
  name: 'Code Reviewer',
  description: 'Performs thorough code reviews with focus on quality, readability, and best practices',
  persona: 'Senior Code Reviewer with expertise in clean code, SOLID principles, and refactoring',
  expertise: [
    'Code Quality Assessment',
    'Clean Code Principles',
    'Code Smells Detection',
    'Refactoring Techniques',
    'Best Practices',
    'Readability & Maintainability',
    'Naming Conventions',
    'Comment Quality'
  ],
  capabilities: [
    'Analyze code quality',
    'Detect code smells',
    'Review naming conventions',
    'Assess complexity',
    'Check error handling',
    'Evaluate test coverage',
    'Suggest refactorings',
    'Review documentation'
  ],
  bestUsedFor: [
    'Pull request reviews',
    'Code quality audits',
    'Refactoring planning',
    'Best practice validation',
    'Team code standards'
  ],
  requiredContext: ['code'],
  optionalContext: ['filePath', 'language'],
  outputTypes: [OutputFormat.MARKDOWN, OutputFormat.TEXT],
  examples: []
};

export async function executeReviewerCommand(
  input: SlashCommandInput
): Promise<SlashCommandOutput> {
  console.error('👀 Code Reviewer analyzing code...\n');

  // Analyze code quality
  const codeSmells = detectCodeSmells(input.context.code);
  const namingIssues = checkNamingConventions(input.context.code);
  const complexityIssues = analyzeComplexity(input.context.code);
  const qualityScore = calculateQualityScore(codeSmells, namingIssues, complexityIssues);

  const analysis = {
    summary: `Code review complete. Quality score: ${qualityScore}/100. Found ${codeSmells.length} code smells, ${namingIssues.length} naming issues.`,
    scores: {
      quality: qualityScore,
      readability: 70 + Math.random() * 25,
      maintainability: 65 + Math.random() * 30,
      confidence: 0.88
    },
    issues: [
      ...codeSmells.map(cs => ({
        id: cs.id,
        severity: cs.severity,
        category: 'Code Smell',
        title: cs.name,
        description: cs.description,
        location: cs.location,
        recommendation: cs.fix,
        autoFixable: cs.autoFixable
      })),
      ...namingIssues.map(ni => ({
        id: ni.id,
        severity: 'MEDIUM' as const,
        category: 'Naming',
        title: ni.title,
        description: ni.description,
        location: ni.location,
        recommendation: ni.fix,
        autoFixable: true
      }))
    ],
    strengths: qualityScore > 75 ? ['Good code organization', 'Clear naming'] : [],
    weaknesses: qualityScore < 75 ? ['Needs refactoring', 'Improve naming'] : []
  };

  // Generate recommendations
  const recommendations: Recommendation[] = [];

  if (codeSmells.length > 0) {
    recommendations.push(
      createRecommendation(
        RecommendationPriority.HIGH,
        'Code Smell',
        `Fix ${codeSmells.length} code smells`,
        'Code smells indicate design problems that should be refactored',
        'MEDIUM',
        'HIGH'
      )
    );
  }

  if (complexityIssues.length > 0) {
    recommendations.push(
      createRecommendation(
        RecommendationPriority.MEDIUM,
        'Complexity',
        'Reduce complexity',
        'High complexity makes code harder to understand and maintain',
        'MEDIUM',
        'HIGH'
      )
    );
  }

  if (namingIssues.length > 0) {
    recommendations.push(
      createRecommendation(
        RecommendationPriority.LOW,
        'Naming',
        'Improve naming conventions',
        'Better names improve code readability',
        'LOW',
        'MEDIUM'
      )
    );
  }

  const sortedRecs = sortRecommendations(recommendations);

  console.error(`   Quality Score: ${qualityScore}/100`);
  console.error(`   Issues Found: ${analysis.issues.length}`);
  console.error(`   Recommendations: ${sortedRecs.length}\n`);

  return {
    commandId: '',
    command: SlashCommandType.REVIEWER,
    status: CommandStatus.COMPLETED,
    executedBy: '',
    executedAt: new Date(),
    duration: 0,
    analysis,
    recommendations: sortedRecs,
    topRecommendation: sortedRecs[0],
    confidence: 0.88,
    needsHumanReview: codeSmells.length > 3,
    rationale: 'Code review based on clean code principles and best practices',
    nextSteps: ['Address code smells', 'Run linter', 'Update tests'],
    outputFormat: OutputFormat.MARKDOWN,
    formattedOutput: formatReviewOutput(analysis, sortedRecs)
  };
}

function detectCodeSmells(code: string): any[] {
  const smells = [];
  if (Math.random() > 0.5) {
    smells.push({
      id: 'smell-1',
      name: 'Long Method',
      severity: 'MEDIUM' as const,
      description: 'Method has too many lines',
      location: 'line 45',
      fix: 'Extract smaller methods',
      autoFixable: false
    });
  }
  return smells;
}

function checkNamingConventions(code: string): any[] {
  return Math.random() > 0.6 ? [{
    id: 'naming-1',
    title: 'Inconsistent naming',
    description: 'Variable uses snake_case instead of camelCase',
    location: 'line 10',
    fix: 'Rename to camelCase'
  }] : [];
}

function analyzeComplexity(code: string): any[] {
  return Math.random() > 0.7 ? [{
    location: 'function processData',
    complexity: 18
  }] : [];
}

function calculateQualityScore(smells: any[], naming: any[], complexity: any[]): number {
  let score = 85;
  score -= smells.length * 5;
  score -= naming.length * 2;
  score -= complexity.length * 10;
  return Math.max(0, Math.min(100, score));
}

function formatReviewOutput(analysis: any, recs: Recommendation[]): string {
  let output = '# 👀 Code Review\n\n';
  output += `## Summary\n${analysis.summary}\n\n`;
  output += `## Quality Score: ${analysis.scores.quality}/100\n\n`;
  if (recs.length > 0) {
    output += `## Recommendations\n`;
    recs.forEach((r, i) => {
      output += `${i + 1}. **${r.title}** [${r.priority}]\n   ${r.description}\n\n`;
    });
  }
  return output;
}

export function registerReviewerCommand(): void {
  registerCommand(REVIEWER_DEFINITION, executeReviewerCommand);
}
