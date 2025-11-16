/**
 * Quality Gate + Slash Command Integration
 *
 * Automatically triggers relevant slash commands when quality gates fail
 * to provide actionable feedback for retry attempts.
 */

import {
  QualityGateType,
  QualityGateResult,
  IssueSeverity
} from '../types/QualityGate';
import {
  SlashCommandType,
  SlashCommandInput
} from '../types/SlashCommand';
import { executeCommand } from './commandRegistry';

/**
 * Map quality gate types to relevant slash commands
 */
const GATE_TO_COMMAND_MAP: Record<QualityGateType, SlashCommandType[]> = {
  [QualityGateType.ARCHITECTURE]: [
    SlashCommandType.ARCHITECT,
    SlashCommandType.REFACTOR
  ],
  [QualityGateType.CODE_QUALITY]: [
    SlashCommandType.REVIEWER,
    SlashCommandType.REFACTOR,
    SlashCommandType.OPTIMIZER
  ],
  [QualityGateType.TEST_COVERAGE]: [
    SlashCommandType.TESTER,
    SlashCommandType.REVIEWER
  ],
  [QualityGateType.SECURITY]: [
    SlashCommandType.SECURITY,
    SlashCommandType.REVIEWER
  ],
  [QualityGateType.DOCUMENTATION]: [
    SlashCommandType.DOCUMENTER
  ],
  [QualityGateType.PERFORMANCE]: [
    SlashCommandType.OPTIMIZER,
    SlashCommandType.PERFORMANCE
  ],
  [QualityGateType.ACCESSIBILITY]: [
    SlashCommandType.ACCESSIBILITY,
    SlashCommandType.FRONTEND
  ]
};

/**
 * Automatically trigger relevant slash commands for failed quality gate
 */
export async function enhanceQualityGateFeedback(
  gateResult: QualityGateResult,
  code: string,
  triggeredBy: string
): Promise<{
  enhancedFeedback: string;
  commandOutputs: any[];
}> {
  // Only enhance if gate failed
  if (gateResult.passed) {
    return {
      enhancedFeedback: '',
      commandOutputs: []
    };
  }

  console.error('\n' + '─'.repeat(80));
  console.error('🎯 ENHANCING QUALITY GATE FEEDBACK WITH SLASH COMMANDS');
  console.error('─'.repeat(80));
  console.error(`Gate: ${gateResult.type}`);
  console.error(`Issues: ${gateResult.totalIssues} (${gateResult.criticalIssues} critical, ${gateResult.highIssues} high)`);
  console.error('');

  const relevantCommands = GATE_TO_COMMAND_MAP[gateResult.type] || [];
  const commandOutputs = [];
  const feedbackSections: string[] = [];

  // Execute relevant slash commands
  for (const commandType of relevantCommands) {
    try {
      console.error(`   Running /${commandType}...`);

      const input: SlashCommandInput = {
        command: commandType,
        context: {
          code,
          language: 'typescript',
          projectType: 'backend'
        },
        options: {
          verbose: false,
          maxRecommendations: 3,
          outputFormat: 'markdown' as any
        }
      };

      const output = await executeCommand(input, `QualityGate:${gateResult.type}`);
      commandOutputs.push(output);

      // Add to feedback
      if (output.recommendations.length > 0) {
        feedbackSections.push(
          `\n### ${output.command.toUpperCase()} Recommendations:\n` +
          output.recommendations.slice(0, 3).map((rec, i) =>
            `${i + 1}. **${rec.title}** [${rec.priority}]\n   ${rec.description}`
          ).join('\n')
        );
      }

      console.error(`   ✓ /${commandType} complete (${output.recommendations.length} recommendations)`);
    } catch (error) {
      console.error(`   ✗ /${commandType} failed: ${error}`);
    }
  }

  // Build enhanced feedback
  const enhancedFeedback = `
## 🎯 Enhanced Quality Gate Feedback

${gateResult.feedbackForRetry || ''}

${feedbackSections.join('\n')}

### 📋 Next Steps:
${gateResult.suggestedFixes.slice(0, 5).map((fix, i) => `${i + 1}. ${fix}`).join('\n')}
`;

  console.error('\n✅ Enhanced feedback generated with' + ` ${commandOutputs.length} slash command(s)\n`);
  console.error('─'.repeat(80) + '\n');

  return {
    enhancedFeedback,
    commandOutputs
  };
}

/**
 * Get recommended slash command for a specific issue
 */
export function getRecommendedCommandForIssue(
  issueCategory: string,
  severity: IssueSeverity
): SlashCommandType | null {
  const categoryMap: Record<string, SlashCommandType> = {
    'Architecture': SlashCommandType.ARCHITECT,
    'Code Smell': SlashCommandType.REVIEWER,
    'Code Complexity': SlashCommandType.REFACTOR,
    'Performance': SlashCommandType.OPTIMIZER,
    'Security': SlashCommandType.SECURITY,
    'Test Coverage': SlashCommandType.TESTER,
    'Documentation': SlashCommandType.DOCUMENTER,
    'Bug': SlashCommandType.DEBUGGER,
    'API Design': SlashCommandType.API_DESIGNER,
    'Database': SlashCommandType.DATABASE,
    'Frontend': SlashCommandType.FRONTEND,
    'Backend': SlashCommandType.BACKEND,
    'DevOps': SlashCommandType.DEVOPS,
    'Accessibility': SlashCommandType.ACCESSIBILITY
  };

  return categoryMap[issueCategory] || null;
}

/**
 * Build context for slash command from quality gate result
 */
export function buildCommandContext(
  gateResult: QualityGateResult,
  originalContext: any
): any {
  return {
    ...originalContext,
    qualityGateType: gateResult.type,
    qualityScore: gateResult.overallScore,
    criticalIssues: gateResult.criticalIssues,
    highIssues: gateResult.highIssues,
    attempt: gateResult.attempt,
    maxAttempts: gateResult.maxAttempts
  };
}

/**
 * Priority-sort slash commands based on gate issues
 */
export function prioritizeCommandsForGate(
  gateResult: QualityGateResult
): SlashCommandType[] {
  const commands = GATE_TO_COMMAND_MAP[gateResult.type] || [];
  const priorities: Partial<Record<SlashCommandType, number>> = {};

  // Calculate priority for each command based on issues
  for (const command of commands) {
    let priority = 0;

    // Higher priority for critical issues
    if (gateResult.criticalIssues > 0) {
      priority += 100;
    }

    // High issues add medium priority
    if (gateResult.highIssues > 0) {
      priority += 50;
    }

    // Overall score influences priority
    priority += (100 - gateResult.overallScore);

    priorities[command] = priority;
  }

  // Sort by priority (descending)
  return commands.sort((a, b) => (priorities[b] || 0) - (priorities[a] || 0));
}
