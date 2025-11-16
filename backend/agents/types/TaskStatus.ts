/**
 * Task Status Types for Retry & Blocking Mechanism
 *
 * Implements 3-attempt retry logic with peer assistance and human escalation
 */

export enum TaskStatus {
  // Initial states
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',

  // Retry states (3 attempts)
  RETRY_1 = 'retry_1',
  RETRY_2 = 'retry_2',
  RETRY_3 = 'retry_3',

  // Peer assistance states
  RETRY_WITH_HELP = 'retry_with_help',       // Trying again with peer tip
  RETRY_WITH_RESOURCE = 'retry_with_resource', // Trying with shared resource
  PAIR_PROGRAMMING = 'pair_programming',      // Two agents working together
  REASSIGNED = 'reassigned',                  // Different agent taking over

  // Terminal states
  COMPLETED = 'completed',
  FAILED = 'failed',
  BLOCKED = 'blocked',                        // Requires human intervention
}

export interface TaskAttempt {
  attemptNumber: number;
  timestamp: Date;
  agentName: string;
  status: TaskStatus;
  output?: any;
  error?: string;
  executionTime: number; // seconds
  feedback?: string[];   // Feedback from quality gate
}

export interface BlockingIssue {
  taskId: string;
  agentName: string;
  workType: string;
  description: string;
  reason: string;
  attempts: TaskAttempt[];
  lastError: string;
  peerHelpAttempted: boolean;
  peerHelpProviders?: string[];
  suggestedAction: string;
  escalatedTo?: string;  // Email/Slack
  blockedAt: Date;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  requiresHumanIntervention: boolean;
}

export interface TaskResult {
  status: TaskStatus;
  output?: any;
  attempts: number;
  totalExecutionTime: number;
  blockingIssue?: BlockingIssue;
  peerAssistanceUsed?: boolean;
  peerHelpers?: string[];
}

export interface RetryConfig {
  maxAttempts: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed';
  backoffMultiplier: number;
  enablePeerHelp: boolean;
  escalateAfterFailedPeerHelp: boolean;
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  backoffStrategy: 'exponential',
  backoffMultiplier: 2,
  enablePeerHelp: true,
  escalateAfterFailedPeerHelp: true
};

/**
 * Helper function: Check if status is a retry state
 */
export function isRetryState(status: TaskStatus): boolean {
  return [
    TaskStatus.RETRY_1,
    TaskStatus.RETRY_2,
    TaskStatus.RETRY_3,
    TaskStatus.RETRY_WITH_HELP,
    TaskStatus.RETRY_WITH_RESOURCE
  ].includes(status);
}

/**
 * Helper function: Check if task is blocked
 */
export function isBlocked(status: TaskStatus): boolean {
  return status === TaskStatus.BLOCKED;
}

/**
 * Helper function: Check if task is complete
 */
export function isTerminal(status: TaskStatus): boolean {
  return [
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.BLOCKED
  ].includes(status);
}

/**
 * Helper function: Get next retry status
 */
export function getNextRetryStatus(currentAttempt: number): TaskStatus {
  switch (currentAttempt) {
    case 1: return TaskStatus.RETRY_1;
    case 2: return TaskStatus.RETRY_2;
    case 3: return TaskStatus.RETRY_3;
    default: return TaskStatus.BLOCKED;
  }
}

/**
 * Helper function: Calculate backoff delay
 */
export function calculateBackoff(
  attempt: number,
  config: RetryConfig
): number {
  switch (config.backoffStrategy) {
    case 'linear':
      return attempt * config.backoffMultiplier * 1000;
    case 'exponential':
      return Math.pow(config.backoffMultiplier, attempt) * 1000;
    case 'fixed':
      return config.backoffMultiplier * 1000;
    default:
      return 1000;
  }
}
