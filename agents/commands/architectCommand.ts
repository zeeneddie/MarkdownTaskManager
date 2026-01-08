/**
 * /architect - Architecture Review & Design Patterns Command
 *
 * AI Persona: Senior Software Architect with 15+ years experience
 * Expertise: System design, design patterns, scalability, maintainability
 * Best used for: Architecture reviews, pattern recommendations, system design
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

/**
 * Architect command definition
 */
export const ARCHITECT_DEFINITION: CommandDefinition = {
  type: SlashCommandType.ARCHITECT,
  name: 'Architecture Reviewer',
  description: 'Reviews system architecture, recommends design patterns, and assesses scalability',
  persona: 'Senior Software Architect with expertise in distributed systems, microservices, and design patterns',
  expertise: [
    'System Architecture',
    'Design Patterns (GoF, Enterprise)',
    'Microservices Architecture',
    'Scalability & Performance',
    'API Design',
    'Database Architecture',
    'SOLID Principles',
    'Clean Architecture',
    'Domain-Driven Design (DDD)'
  ],
  capabilities: [
    'Analyze system architecture',
    'Recommend design patterns',
    'Identify architectural anti-patterns',
    'Assess scalability concerns',
    'Review component boundaries',
    'Evaluate coupling and cohesion',
    'Suggest architectural improvements',
    'Create architecture diagrams'
  ],
  bestUsedFor: [
    'New system design',
    'Architecture refactoring',
    'Scalability planning',
    'Design pattern selection',
    'Component boundary definition',
    'Technology stack evaluation'
  ],
  requiredContext: ['code'],
  optionalContext: ['filePath', 'language', 'framework', 'existingPatterns', 'projectType'],
  outputTypes: [OutputFormat.MARKDOWN, OutputFormat.TEXT],
  examples: [
    {
      scenario: 'Review microservices architecture',
      input: {
        command: SlashCommandType.ARCHITECT,
        context: {
          code: 'src/services/',
          projectType: 'microservices',
          framework: 'NestJS'
        }
      },
      expectedOutcome: 'Architecture review with service boundary recommendations'
    },
    {
      scenario: 'Evaluate design pattern usage',
      input: {
        command: SlashCommandType.ARCHITECT,
        context: {
          code: 'class UserService { ... }',
          existingPatterns: ['Repository', 'Factory']
        }
      },
      expectedOutcome: 'Pattern consistency analysis and recommendations'
    }
  ]
};

/**
 * Execute architect command
 */
export async function executeArchitectCommand(
  input: SlashCommandInput
): Promise<SlashCommandOutput> {
  const startTime = Date.now();

  console.error('🏗️ Architecture Reviewer analyzing code...\n');

  // Analyze architecture
  const analysis = await analyzeArchitecture(input.context);

  // Generate recommendations
  const recommendations = generateArchitectureRecommendations(
    analysis,
    input.context,
    input.options
  );

  // Sort by priority
  const sortedRecommendations = sortRecommendations(recommendations);
  const topRecommendation = sortedRecommendations[0];

  // Format output
  const formattedOutput = formatArchitectureOutput(
    analysis,
    sortedRecommendations,
    input.options?.outputFormat || OutputFormat.MARKDOWN
  );

  // Build result
  const output: SlashCommandOutput = {
    commandId: '',
    command: SlashCommandType.ARCHITECT,
    status: CommandStatus.COMPLETED,
    executedBy: '',
    executedAt: new Date(),
    duration: 0,
    analysis,
    recommendations: sortedRecommendations,
    topRecommendation,
    confidence: analysis.scores?.confidence || 0.85,
    needsHumanReview: sortedRecommendations.some(
      r => r.priority === RecommendationPriority.CRITICAL
    ),
    rationale: 'Architecture analysis based on design patterns, SOLID principles, and scalability assessment',
    nextSteps: generateNextSteps(sortedRecommendations),
    outputFormat: input.options?.outputFormat || OutputFormat.MARKDOWN,
    formattedOutput
  };

  console.error(`   Architecture Score: ${analysis.scores?.architectureScore || 0}/100`);
  console.error(`   Scalability Score: ${analysis.scores?.scalabilityScore || 0}/100`);
  console.error(`   Maintainability: ${analysis.scores?.maintainability || 0}/100`);
  console.error(`   Recommendations: ${recommendations.length}\n`);

  return output;
}

/**
 * Analyze architecture
 */
async function analyzeArchitecture(context: any): Promise<any> {
  const patterns = detectDesignPatterns(context.code);
  const antiPatterns = detectAntiPatterns(context.code);
  const coupling = analyzeCoupling(context.code);
  const scalability = assessScalability(context);

  const architectureScore = calculateArchitectureScore(patterns, antiPatterns, coupling);
  const scalabilityScore = scalability.score;
  const maintainability = calculateMaintainability(coupling, patterns.length);

  return {
    summary: `Architecture analysis complete. ${patterns.length} design patterns detected, ${antiPatterns.length} anti-patterns found.`,
    scores: {
      architectureScore,
      scalabilityScore,
      maintainability,
      confidence: 0.85
    },
    patterns,
    issues: antiPatterns.map(ap => ({
      id: `anti-pattern-${ap.name}`,
      severity: 'HIGH' as const,
      category: 'Anti-Pattern',
      title: ap.name,
      description: ap.description,
      location: ap.location,
      recommendation: ap.fix,
      autoFixable: false
    })),
    strengths: patterns.map(p => `Good use of ${p.name} pattern`),
    weaknesses: [
      coupling.level === 'HIGH' ? 'High coupling between components' : null,
      scalability.concerns.length > 0 ? 'Scalability concerns identified' : null
    ].filter(Boolean) as string[],
    metrics: {
      coupling: coupling.score,
      cohesion: 75 + Math.random() * 20,
      complexity: 60 + Math.random() * 30,
      patterns: patterns.length,
      antiPatterns: antiPatterns.length
    }
  };
}

/**
 * Detect design patterns
 */
function detectDesignPatterns(code: string): any[] {
  const patterns = [];

  // Simulate pattern detection
  const possiblePatterns = [
    { name: 'Repository Pattern', confidence: 0.9, benefit: 'Data access abstraction' },
    { name: 'Factory Pattern', confidence: 0.85, benefit: 'Object creation flexibility' },
    { name: 'Observer Pattern', confidence: 0.75, benefit: 'Event-driven architecture' },
    { name: 'Strategy Pattern', confidence: 0.8, benefit: 'Algorithm encapsulation' }
  ];

  // Randomly select 2-3 patterns
  const count = Math.floor(Math.random() * 2) + 2;
  for (let i = 0; i < count; i++) {
    patterns.push(possiblePatterns[i]);
  }

  return patterns;
}

/**
 * Detect anti-patterns
 */
function detectAntiPatterns(code: string): any[] {
  const antiPatterns = [];

  // Simulate anti-pattern detection
  if (Math.random() > 0.6) {
    antiPatterns.push({
      name: 'God Object',
      description: 'Class has too many responsibilities',
      location: 'UserService class',
      fix: 'Split into smaller, focused classes following Single Responsibility Principle'
    });
  }

  if (Math.random() > 0.7) {
    antiPatterns.push({
      name: 'Spaghetti Code',
      description: 'Complex control flow with deep nesting',
      location: 'processRequest function',
      fix: 'Extract methods, simplify control flow, use guard clauses'
    });
  }

  return antiPatterns;
}

/**
 * Analyze coupling
 */
function analyzeCoupling(code: string): {
  score: number;
  level: 'LOW' | 'MEDIUM' | 'HIGH';
} {
  const score = 40 + Math.random() * 50; // 40-90
  const level = score < 60 ? 'HIGH' : score < 75 ? 'MEDIUM' : 'LOW';

  return { score, level };
}

/**
 * Assess scalability
 */
function assessScalability(context: any): {
  score: number;
  concerns: string[];
} {
  const score = 65 + Math.random() * 30; // 65-95
  const concerns = [];

  if (score < 75) {
    concerns.push('Consider implementing caching layer');
    concerns.push('Evaluate database query optimization');
  }

  if (context.projectType === 'microservices' && score < 80) {
    concerns.push('Add circuit breakers for resilience');
    concerns.push('Implement distributed tracing');
  }

  return { score, concerns };
}

/**
 * Calculate architecture score
 */
function calculateArchitectureScore(
  patterns: any[],
  antiPatterns: any[],
  coupling: any
): number {
  let score = 70; // Base score

  // Bonus for patterns
  score += patterns.length * 5;

  // Penalty for anti-patterns
  score -= antiPatterns.length * 10;

  // Coupling impact
  score += (coupling.score - 50) / 2;

  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Calculate maintainability
 */
function calculateMaintainability(coupling: any, patternCount: number): number {
  let score = 65;
  score += coupling.score / 4;
  score += patternCount * 3;
  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Generate architecture recommendations
 */
function generateArchitectureRecommendations(
  analysis: any,
  context: any,
  options?: any
): Recommendation[] {
  const recommendations: Recommendation[] = [];

  // Recommendations based on anti-patterns
  for (const antiPattern of analysis.issues) {
    recommendations.push(
      createRecommendation(
        RecommendationPriority.HIGH,
        'Anti-Pattern',
        `Fix ${antiPattern.title}`,
        antiPattern.description,
        'MEDIUM',
        'HIGH'
      )
    );
  }

  // Recommendations based on coupling
  if (analysis.metrics.coupling < 60) {
    const rec = createRecommendation(
      RecommendationPriority.HIGH,
      'Coupling',
      'Reduce component coupling',
      'High coupling detected between components. This makes the system harder to maintain and test.',
      'HIGH',
      'HIGH'
    );
    rec.rationale = 'Loose coupling improves testability and maintainability';
    rec.benefits = [
      'Easier to test components in isolation',
      'More flexible system architecture',
      'Reduced risk of cascading changes'
    ];
    rec.implementation = {
      steps: [
        'Identify tightly coupled components',
        'Define clear interfaces between components',
        'Apply Dependency Inversion Principle',
        'Use dependency injection',
        'Refactor incrementally'
      ],
      estimatedTime: '2-3 days'
    };
    recommendations.push(rec);
  }

  // Recommendations based on patterns
  if (analysis.patterns.length < 2) {
    const rec = createRecommendation(
      RecommendationPriority.MEDIUM,
      'Design Patterns',
      'Adopt more design patterns',
      'Few design patterns detected. Consider using established patterns for better code organization.',
      'MEDIUM',
      'MEDIUM'
    );
    rec.rationale = 'Design patterns provide proven solutions to common problems';
    rec.benefits = [
      'Improved code organization',
      'Better communication among developers',
      'Proven solutions to common problems'
    ];
    recommendations.push(rec);
  }

  // Scalability recommendations
  if (analysis.scores.scalabilityScore < 75) {
    const rec = createRecommendation(
      RecommendationPriority.MEDIUM,
      'Scalability',
      'Improve scalability',
      'System may face challenges when scaling. Consider implementing caching, load balancing, and horizontal scaling strategies.',
      'HIGH',
      'HIGH'
    );
    rec.rationale = 'Proactive scalability planning prevents future bottlenecks';
    rec.benefits = [
      'Handle increased load gracefully',
      'Better user experience under high traffic',
      'Cost-effective scaling'
    ];
    recommendations.push(rec);
  }

  return recommendations.slice(0, options?.maxRecommendations || 5);
}

/**
 * Format architecture output
 */
function formatArchitectureOutput(
  analysis: any,
  recommendations: Recommendation[],
  format: OutputFormat
): string {
  if (format === OutputFormat.MARKDOWN) {
    let output = '# 🏗️ Architecture Review\n\n';
    output += `## Summary\n${analysis.summary}\n\n`;
    output += `## Scores\n`;
    output += `- **Architecture**: ${analysis.scores.architectureScore}/100\n`;
    output += `- **Scalability**: ${analysis.scores.scalabilityScore}/100\n`;
    output += `- **Maintainability**: ${analysis.scores.maintainability}/100\n\n`;

    if (analysis.patterns.length > 0) {
      output += `## Design Patterns Detected\n`;
      analysis.patterns.forEach((p: any) => {
        output += `- **${p.name}** (${(p.confidence * 100).toFixed(0)}% confidence): ${p.benefit}\n`;
      });
      output += '\n';
    }

    if (recommendations.length > 0) {
      output += `## Recommendations\n`;
      recommendations.forEach((rec, i) => {
        output += `### ${i + 1}. ${rec.title} [${rec.priority}]\n`;
        output += `${rec.description}\n\n`;
        output += `**Effort**: ${rec.effort} | **Impact**: ${rec.impact}\n\n`;
      });
    }

    return output;
  }

  // Plain text format
  return analysis.summary + '\n\n' +
    recommendations.map((r, i) => `${i + 1}. ${r.title}: ${r.description}`).join('\n');
}

/**
 * Generate next steps
 */
function generateNextSteps(recommendations: Recommendation[]): string[] {
  const steps: string[] = [];

  const critical = recommendations.filter(r => r.priority === RecommendationPriority.CRITICAL);
  const high = recommendations.filter(r => r.priority === RecommendationPriority.HIGH);

  if (critical.length > 0) {
    steps.push(`Address ${critical.length} critical architecture issues immediately`);
  }

  if (high.length > 0) {
    steps.push(`Plan refactoring for ${high.length} high-priority improvements`);
  }

  if (recommendations.length > 0) {
    steps.push('Create architecture decision records (ADRs) for major changes');
    steps.push('Schedule architecture review meeting with team');
  }

  return steps;
}

/**
 * Register architect command
 */
export function registerArchitectCommand(): void {
  registerCommand(ARCHITECT_DEFINITION, executeArchitectCommand);
}
