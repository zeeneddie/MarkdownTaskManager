/**
 * Blocking Handler
 *
 * Detects blocking issues and manages human escalation
 */

import { BlockingIssue, TaskStatus } from '../types/TaskStatus';

export interface EscalationChannel {
  type: 'EMAIL' | 'SLACK' | 'WEBHOOK' | 'LOG';
  destination: string;
  enabled: boolean;
}

export interface EscalationConfig {
  channels: EscalationChannel[];
  immediateEscalation: string[]; // Work types that need immediate escalation
  escalationDelay: number;        // Minutes to wait before escalating
}

export const DEFAULT_ESCALATION_CONFIG: EscalationConfig = {
  channels: [
    {
      type: 'LOG',
      destination: 'console',
      enabled: true
    }
  ],
  immediateEscalation: ['BUG', 'QUALITY_AUDIT'],
  escalationDelay: 0
};

/**
 * Detect if issue is blocking
 */
export function isBlockingIssue(
  attempts: number,
  peerHelpAttempted: boolean,
  maxAttempts: number = 3
): boolean {

  // Blocked if max attempts reached
  if (attempts >= maxAttempts) {
    return true;
  }

  // Blocked if peer help failed
  if (peerHelpAttempted && attempts >= maxAttempts) {
    return true;
  }

  return false;
}

/**
 * Escalate blocking issue to human
 */
export async function escalateToHuman(
  blockingIssue: BlockingIssue,
  config: EscalationConfig = DEFAULT_ESCALATION_CONFIG
): Promise<void> {

  console.error('\n[BlockingHandler] 🚨 ESCALATING TO HUMAN');
  console.error(`[BlockingHandler] Task: ${blockingIssue.taskId}`);
  console.error(`[BlockingHandler] Agent: ${blockingIssue.agentName}`);
  console.error(`[BlockingHandler] Work Type: ${blockingIssue.workType}`);
  console.error(`[BlockingHandler] Priority: ${blockingIssue.priority}`);
  console.error(`[BlockingHandler] Reason: ${blockingIssue.reason}`);
  console.error(`[BlockingHandler] Attempts: ${blockingIssue.attempts.length}`);
  console.error(`[BlockingHandler] Peer help attempted: ${blockingIssue.peerHelpAttempted}`);

  // Check if immediate escalation needed
  const needsImmediate = config.immediateEscalation.includes(blockingIssue.workType);

  if (needsImmediate) {
    console.error(`[BlockingHandler] ⚡ IMMEDIATE ESCALATION (work type: ${blockingIssue.workType})`);
  } else if (config.escalationDelay > 0) {
    console.error(`[BlockingHandler] ⏳ Waiting ${config.escalationDelay} minutes before escalating...`);
    await sleep(config.escalationDelay * 60 * 1000);
  }

  // Send notifications through all enabled channels
  for (const channel of config.channels) {
    if (!channel.enabled) continue;

    try {
      await sendEscalation(blockingIssue, channel);
    } catch (error) {
      console.error(`[BlockingHandler] ❌ Failed to send via ${channel.type}: ${error}`);
    }
  }
}

/**
 * Send escalation notification
 */
async function sendEscalation(
  blockingIssue: BlockingIssue,
  channel: EscalationChannel
): Promise<void> {

  const message = formatEscalationMessage(blockingIssue);

  switch (channel.type) {
    case 'LOG':
      console.error('\n' + '='.repeat(80));
      console.error('🚨 BLOCKING ISSUE - REQUIRES HUMAN INTERVENTION');
      console.error('='.repeat(80));
      console.error(message);
      console.error('='.repeat(80) + '\n');
      break;

    case 'EMAIL':
      // In production, integrate with email service
      console.error(`[BlockingHandler] 📧 Would send email to: ${channel.destination}`);
      console.error(message);
      break;

    case 'SLACK':
      // In production, integrate with Slack API
      console.error(`[BlockingHandler] 💬 Would send Slack message to: ${channel.destination}`);
      console.error(message);
      break;

    case 'WEBHOOK':
      // In production, send HTTP POST to webhook
      console.error(`[BlockingHandler] 🔗 Would POST to webhook: ${channel.destination}`);
      console.error(message);
      break;
  }
}

/**
 * Format escalation message
 */
function formatEscalationMessage(blockingIssue: BlockingIssue): string {
  const lines = [
    `TASK ID: ${blockingIssue.taskId}`,
    `AGENT: ${blockingIssue.agentName}`,
    `WORK TYPE: ${blockingIssue.workType}`,
    `PRIORITY: ${blockingIssue.priority}`,
    '',
    `DESCRIPTION:`,
    blockingIssue.description,
    '',
    `REASON FOR BLOCKING:`,
    blockingIssue.reason,
    '',
    `LAST ERROR:`,
    blockingIssue.lastError,
    '',
    `ATTEMPTS: ${blockingIssue.attempts.length}`,
    blockingIssue.attempts.map((a, i) =>
      `  ${i + 1}. ${a.status} - ${a.error || 'Success'} (${a.executionTime.toFixed(2)}s)`
    ).join('\n'),
    '',
    `PEER HELP ATTEMPTED: ${blockingIssue.peerHelpAttempted ? 'YES' : 'NO'}`,
  ];

  if (blockingIssue.peerHelpProviders && blockingIssue.peerHelpProviders.length > 0) {
    lines.push(`PEER HELPERS: ${blockingIssue.peerHelpProviders.join(', ')}`);
  }

  lines.push(
    '',
    `SUGGESTED ACTIONS:`,
    blockingIssue.suggestedAction,
    '',
    `BLOCKED AT: ${blockingIssue.blockedAt.toISOString()}`,
    '',
    `⚠️  This task requires human intervention to proceed.`
  );

  return lines.join('\n');
}

/**
 * Create blocking issue from task context
 */
export function createBlockingIssue(
  taskId: string,
  agentName: string,
  workType: string,
  description: string,
  reason: string,
  attempts: any[],
  lastError: string,
  peerHelpAttempted: boolean = false,
  peerHelpProviders?: string[]
): BlockingIssue {

  return {
    taskId,
    agentName,
    workType,
    description,
    reason,
    attempts,
    lastError,
    peerHelpAttempted,
    peerHelpProviders,
    suggestedAction: generateSuggestedActions(reason, lastError, peerHelpAttempted),
    blockedAt: new Date(),
    priority: determinePriority(workType, attempts.length, peerHelpAttempted),
    requiresHumanIntervention: true
  };
}

/**
 * Generate suggested actions
 */
function generateSuggestedActions(
  reason: string,
  lastError: string,
  peerHelpAttempted: boolean
): string {

  const actions: string[] = [];

  // Error-specific suggestions
  if (lastError.toLowerCase().includes('timeout')) {
    actions.push('- Increase task timeout limit in configuration');
    actions.push('- Check if external services are responding');
  }

  if (lastError.toLowerCase().includes('permission') || lastError.toLowerCase().includes('unauthorized')) {
    actions.push('- Verify agent has necessary permissions');
    actions.push('- Check API keys and authentication tokens');
  }

  if (lastError.toLowerCase().includes('api key') || lastError.toLowerCase().includes('ollama')) {
    actions.push('- Configure Ollama API endpoint in agents config');
    actions.push('- Verify Ollama service is running: ollama serve');
    actions.push('- Check model availability: ollama list');
  }

  if (lastError.toLowerCase().includes('connection')) {
    actions.push('- Check network connectivity');
    actions.push('- Verify service endpoints are accessible');
  }

  // General suggestions
  actions.push('- Review task requirements and acceptance criteria');
  actions.push('- Check agent configuration and capabilities');
  actions.push('- Consider breaking task into smaller subtasks');

  if (peerHelpAttempted) {
    actions.push('- Peer assistance was attempted but unsuccessful');
    actions.push('- May require different approach or additional context');
    actions.push('- Consider manual review of task requirements');
  }

  return actions.join('\n');
}

/**
 * Determine priority
 */
function determinePriority(
  workType: string,
  attempts: number,
  peerHelpAttempted: boolean
): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {

  // Critical work types
  if (['BUG', 'QUALITY_AUDIT'].includes(workType)) {
    return 'CRITICAL';
  }

  // High if many attempts or peer help failed
  if (attempts >= 3 || peerHelpAttempted) {
    return 'HIGH';
  }

  // Medium for most cases
  if (attempts >= 2) {
    return 'MEDIUM';
  }

  return 'LOW';
}

/**
 * Sleep helper
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if blocker can be auto-resolved
 */
export function canAutoResolve(blockingIssue: BlockingIssue): boolean {
  // Check if error is self-correcting (e.g., temporary network issue)
  const selfCorrecting = [
    'timeout',
    'connection refused',
    'service unavailable',
    'rate limit'
  ];

  return selfCorrecting.some(pattern =>
    blockingIssue.lastError.toLowerCase().includes(pattern)
  );
}

/**
 * Attempt auto-resolution
 */
export async function attemptAutoResolve(
  blockingIssue: BlockingIssue
): Promise<boolean> {

  console.error(`[BlockingHandler] 🔄 Attempting auto-resolution for ${blockingIssue.taskId}`);

  // Wait and retry once
  await sleep(30000); // 30 seconds

  // In real implementation, would retry the task here
  // For now, return false (manual intervention needed)
  return false;
}
