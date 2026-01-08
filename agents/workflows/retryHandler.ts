/**
 * Retry Handler
 *
 * Implements 3-attempt retry logic with exponential backoff
 * and integration with peer assistance system
 */

import { Agent, Task } from 'kaibanjs';
import {
  TaskStatus,
  TaskAttempt,
  TaskResult,
  RetryConfig,
  DEFAULT_RETRY_CONFIG,
  getNextRetryStatus,
  calculateBackoff,
  isTerminal
} from '../types/TaskStatus';

export interface RetryContext {
  taskId: string;
  agent: Agent;
  task: Task;
  workType: string;
  attempts: TaskAttempt[];
  config: RetryConfig;
  feedback?: string[];           // Feedback from previous attempts
  peerHelp?: string;            // Tip from peer assistance
  peerResources?: any[];        // Resources shared by peers
}

/**
 * Execute task with retry logic
 */
export async function executeWithRetry(
  context: RetryContext
): Promise<TaskResult> {

  const startTime = Date.now();
  console.error(`[RetryHandler] Starting task execution for ${context.agent.name}`);
  console.error(`[RetryHandler] Max attempts: ${context.config.maxAttempts}`);

  for (let attempt = 1; attempt <= context.config.maxAttempts; attempt++) {
    const attemptStart = Date.now();
    const status = getNextRetryStatus(attempt);

    console.error(`\n[RetryHandler] 🔄 Attempt ${attempt}/${context.config.maxAttempts}`);
    console.error(`[RetryHandler] Status: ${status}`);

    try {
      // Add feedback to task if available
      if (context.feedback && context.feedback.length > 0) {
        console.error(`[RetryHandler] 💡 Applying feedback from previous attempt:`);
        context.feedback.forEach(fb => console.error(`   - ${fb}`));
      }

      // Add peer help if available
      if (context.peerHelp) {
        console.error(`[RetryHandler] 🤝 Using peer assistance tip:`);
        console.error(`   ${context.peerHelp}`);
      }

      // Execute the task
      // @ts-ignore - KaibanJS Team.start returns result
      const output = await executeTaskWithAgent(
        context.agent,
        context.task,
        {
          feedback: context.feedback,
          peerHelp: context.peerHelp,
          peerResources: context.peerResources
        }
      );

      const executionTime = (Date.now() - attemptStart) / 1000;

      // Record successful attempt
      const successfulAttempt: TaskAttempt = {
        attemptNumber: attempt,
        timestamp: new Date(),
        agentName: context.agent.name,
        status: TaskStatus.COMPLETED,
        output,
        executionTime
      };

      context.attempts.push(successfulAttempt);

      console.error(`[RetryHandler] ✅ Attempt ${attempt} SUCCESSFUL in ${executionTime.toFixed(2)}s`);

      const totalTime = (Date.now() - startTime) / 1000;

      return {
        status: TaskStatus.COMPLETED,
        output,
        attempts: attempt,
        totalExecutionTime: totalTime,
        peerAssistanceUsed: !!context.peerHelp
      };

    } catch (error) {
      const executionTime = (Date.now() - attemptStart) / 1000;
      const errorMessage = error instanceof Error ? error.message : String(error);

      console.error(`[RetryHandler] ❌ Attempt ${attempt} FAILED: ${errorMessage}`);

      // Record failed attempt
      const failedAttempt: TaskAttempt = {
        attemptNumber: attempt,
        timestamp: new Date(),
        agentName: context.agent.name,
        status,
        error: errorMessage,
        executionTime
      };

      context.attempts.push(failedAttempt);

      // Check if we should retry
      if (attempt < context.config.maxAttempts) {
        // Calculate backoff delay
        const backoffMs = calculateBackoff(attempt, context.config);
        console.error(`[RetryHandler] ⏳ Waiting ${backoffMs}ms before retry...`);

        await sleep(backoffMs);

        // Continue to next attempt
        continue;
      }

      // Max attempts reached
      console.error(`[RetryHandler] ❌ Max attempts (${context.config.maxAttempts}) reached`);
      console.error(`[RetryHandler] Task will be marked as BLOCKED`);

      const totalTime = (Date.now() - startTime) / 1000;

      return {
        status: TaskStatus.BLOCKED,
        attempts: attempt,
        totalExecutionTime: totalTime,
        blockingIssue: {
          taskId: context.taskId,
          agentName: context.agent.name,
          workType: context.workType,
          description: context.task.description,
          reason: 'Max retry attempts exceeded',
          attempts: context.attempts,
          lastError: errorMessage,
          peerHelpAttempted: !!context.peerHelp,
          peerHelpProviders: context.peerHelp ? ['peer-agent'] : undefined,
          suggestedAction: generateSuggestedAction(context, errorMessage),
          blockedAt: new Date(),
          priority: determinePriority(context),
          requiresHumanIntervention: true
        },
        peerAssistanceUsed: !!context.peerHelp
      };
    }
  }

  // Should never reach here, but TypeScript needs it
  const totalTime = (Date.now() - startTime) / 1000;
  return {
    status: TaskStatus.FAILED,
    attempts: context.config.maxAttempts,
    totalExecutionTime: totalTime
  };
}

/**
 * Execute task with agent (wrapper for KaibanJS)
 */
async function executeTaskWithAgent(
  agent: Agent,
  task: Task,
  context: {
    feedback?: string[];
    peerHelp?: string;
    peerResources?: any[];
  }
): Promise<any> {

  // Enhance task description with feedback and peer help
  let enhancedDescription = task.description;

  if (context.feedback && context.feedback.length > 0) {
    enhancedDescription += '\n\n**Feedback from previous attempt:**\n';
    context.feedback.forEach(fb => {
      enhancedDescription += `- ${fb}\n`;
    });
  }

  if (context.peerHelp) {
    enhancedDescription += '\n\n**Peer assistance tip:**\n';
    enhancedDescription += context.peerHelp;
  }

  if (context.peerResources && context.peerResources.length > 0) {
    enhancedDescription += '\n\n**Shared resources:**\n';
    context.peerResources.forEach(resource => {
      enhancedDescription += `- ${resource.title}: ${resource.content}\n`;
    });
  }

  // Create enhanced task
  const enhancedTask = {
    ...task,
    description: enhancedDescription
  };

  // For now, return mock result
  // In real implementation, this would call KaibanJS Team.start()
  return {
    success: true,
    agentName: agent.name,
    output: {
      message: `Task completed by ${agent.name}`,
      enhanced: !!(context.feedback || context.peerHelp),
      timestamp: new Date().toISOString()
    }
  };
}

/**
 * Generate suggested action for human
 */
function generateSuggestedAction(
  context: RetryContext,
  lastError: string
): string {
  const suggestions = [
    `Review task requirements for ${context.workType}`,
    `Check if ${context.agent.name} has necessary context`,
    `Verify system dependencies are available`,
    `Consider breaking task into smaller subtasks`
  ];

  // Add error-specific suggestions
  if (lastError.toLowerCase().includes('timeout')) {
    suggestions.unshift('Increase task timeout limit');
  }

  if (lastError.toLowerCase().includes('permission')) {
    suggestions.unshift('Check agent permissions and access rights');
  }

  if (lastError.toLowerCase().includes('api key')) {
    suggestions.unshift('Verify API keys and credentials are configured');
  }

  if (context.peerHelp) {
    suggestions.push('Peer assistance was attempted but unsuccessful - may need different approach');
  }

  return suggestions.join('\n- ');
}

/**
 * Determine blocking priority
 */
function determinePriority(context: RetryContext): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
  // Critical work types
  if (['BUG', 'QUALITY_AUDIT'].includes(context.workType)) {
    return 'CRITICAL';
  }

  // High priority if many attempts
  if (context.attempts.length >= 3) {
    return 'HIGH';
  }

  // Medium priority if peer help failed
  if (context.peerHelp) {
    return 'HIGH';
  }

  return 'MEDIUM';
}

/**
 * Sleep helper
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry with peer assistance
 */
export async function retryWithPeerHelp(
  context: RetryContext,
  peerHelp: string,
  peerAgent: string
): Promise<TaskResult> {

  console.error(`\n[RetryHandler] 🤝 Retrying with peer assistance from ${peerAgent}`);

  // Add peer help to context
  context.peerHelp = peerHelp;
  context.feedback = context.feedback || [];
  context.feedback.push(`Tip from ${peerAgent}: ${peerHelp}`);

  // Execute one more attempt with peer help
  context.config.maxAttempts++; // Allow one extra attempt for peer help

  return executeWithRetry(context);
}
