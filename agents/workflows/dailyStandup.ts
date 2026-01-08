/**
 * Daily Standup Workflow
 *
 * Orchestrates daily standup ceremony with integrated peer assistance
 * for blocked tasks before human escalation
 */

import { Agent, Task } from 'kaibanjs';
import { agents } from '../configs/agents';
import {
  TaskStatus,
  BlockingIssue,
  TaskResult,
  DEFAULT_RETRY_CONFIG
} from '../types/TaskStatus';
import {
  PeerAssistanceRequest,
  PeerAssistanceResponse,
  PeerAssistanceResult
} from '../types/Assistance';
import {
  requestPeerAssistance,
  selectBestHelper,
  executePeerAssistance,
  updateAgentExpertise
} from './peerAssistance';
import {
  escalateToHuman,
  createBlockingIssue,
  canAutoResolve,
  attemptAutoResolve,
  EscalationConfig,
  DEFAULT_ESCALATION_CONFIG
} from './blockingHandler';
import { retryWithPeerHelp, RetryContext } from './retryHandler';

/**
 * Standup report from an agent
 */
export interface StandupReport {
  agentName: string;
  timestamp: Date;
  yesterday: string[];           // What was completed yesterday
  today: string[];              // What's planned for today
  blockers: BlockingIssue[];    // Current blockers
  needsHelp: boolean;           // Flag if agent needs help
  availableToHelp: boolean;     // Flag if agent can help others
  mood: 'productive' | 'struggling' | 'blocked';
}

/**
 * Standup session result
 */
export interface StandupSessionResult {
  timestamp: Date;
  reports: StandupReport[];
  peerAssistanceProvided: PeerAssistanceResult[];
  blockersResolved: number;
  blockersEscalated: number;
  totalTimeSpent: number;
  metrics: {
    agentsWithBlockers: number;
    peerHelpRequests: number;
    peerHelpSuccess: number;
    humanEscalations: number;
    timeSavedByPeers: number;
  };
}

/**
 * Execute daily standup
 */
export async function executeDailyStandup(
  activeAgents: Agent[],
  blockersFromWorkflow?: BlockingIssue[],
  escalationConfig: EscalationConfig = DEFAULT_ESCALATION_CONFIG
): Promise<StandupSessionResult> {

  console.error('\n' + '='.repeat(80));
  console.error('🌅 DAILY STANDUP - ' + new Date().toLocaleString());
  console.error('='.repeat(80));

  const startTime = Date.now();
  const reports: StandupReport[] = [];
  const peerAssistanceProvided: PeerAssistanceResult[] = [];
  let blockersResolved = 0;
  let blockersEscalated = 0;

  // Step 1: Collect standup reports from all agents
  console.error('\n[DailyStandup] 📋 Collecting standup reports...\n');

  for (const agent of activeAgents) {
    const report = await collectStandupReport(agent, blockersFromWorkflow);
    reports.push(report);

    console.error(`[DailyStandup] ${agent.name}:`);
    console.error(`  Yesterday: ${report.yesterday.length} items completed`);
    console.error(`  Today: ${report.today.length} items planned`);
    console.error(`  Blockers: ${report.blockers.length}`);
    console.error(`  Mood: ${getMoodEmoji(report.mood)} ${report.mood}`);
  }

  // Step 2: Identify agents with blockers
  const agentsWithBlockers = reports.filter(r => r.blockers.length > 0);
  const availableHelpers = activeAgents.filter(a =>
    reports.find(r => r.agentName === a.name && r.availableToHelp)
  );

  console.error(`\n[DailyStandup] 📊 Summary:`);
  console.error(`  Total agents: ${activeAgents.length}`);
  console.error(`  Agents with blockers: ${agentsWithBlockers.length}`);
  console.error(`  Available helpers: ${availableHelpers.length}`);

  // Step 3: Process each blocker with peer assistance
  for (const report of agentsWithBlockers) {
    console.error(`\n[DailyStandup] 🚧 Processing blockers for ${report.agentName}...`);

    for (const blocker of report.blockers) {
      console.error(`\n[DailyStandup] Blocker: ${blocker.taskId}`);
      console.error(`  Reason: ${blocker.reason}`);
      console.error(`  Attempts: ${blocker.attempts.length}`);
      console.error(`  Priority: ${blocker.priority}`);

      // Check if blocker can be auto-resolved
      if (canAutoResolve(blocker)) {
        console.error(`[DailyStandup] 🔄 Attempting auto-resolution...`);
        const resolved = await attemptAutoResolve(blocker);

        if (resolved) {
          console.error(`[DailyStandup] ✅ Auto-resolved successfully!`);
          blockersResolved++;
          continue;
        }
      }

      // Step 4: Request peer assistance
      const assistanceRequest: PeerAssistanceRequest = {
        blockingIssue: blocker,
        requestingAgent: report.agentName,
        context: {
          workType: blocker.workType,
          taskDescription: blocker.description,
          previousAttempts: blocker.attempts.length,
          errorMessages: blocker.attempts.map(a => a.error || ''),
          currentApproach: blocker.attempts[blocker.attempts.length - 1]?.output || ''
        },
        urgency: blocker.priority
      };

      console.error(`\n[DailyStandup] 🤝 Requesting peer assistance...`);

      const responses = await requestPeerAssistance(
        assistanceRequest,
        availableHelpers
      );

      if (responses.length === 0) {
        console.error(`[DailyStandup] ❌ No peers available to help`);
        console.error(`[DailyStandup] 🚨 Escalating to human...`);

        await escalateToHuman(blocker, escalationConfig);
        blockersEscalated++;
        continue;
      }

      // Step 5: Select best helper
      const bestHelper = selectBestHelper(responses);

      if (!bestHelper) {
        console.error(`[DailyStandup] ❌ No suitable helper found`);
        console.error(`[DailyStandup] 🚨 Escalating to human...`);

        await escalateToHuman(blocker, escalationConfig);
        blockersEscalated++;
        continue;
      }

      console.error(`[DailyStandup] ✅ Best helper: ${bestHelper.assistingAgent}`);
      console.error(`  Type: ${bestHelper.offer.assistanceType}`);
      console.error(`  Confidence: ${(bestHelper.offer.confidence * 100).toFixed(0)}%`);

      // Step 6: Execute peer assistance
      const assistanceResult = await executePeerAssistance(
        assistanceRequest,
        bestHelper
      );

      peerAssistanceProvided.push(assistanceResult);

      // Step 7: Retry task with peer help
      console.error(`\n[DailyStandup] 🔄 Retrying task with peer assistance...`);

      const retryContext: RetryContext = {
        taskId: blocker.taskId,
        agent: activeAgents.find(a => a.name === report.agentName)!,
        task: {
          description: blocker.description,
          expectedOutput: 'Task completion with peer assistance'
        } as Task,
        workType: blocker.workType,
        attempts: blocker.attempts,
        config: DEFAULT_RETRY_CONFIG,
        peerHelp: bestHelper.offer.suggestion,
        peerResources: bestHelper.offer.resources
      };

      try {
        const retryResult = await retryWithPeerHelp(
          retryContext,
          bestHelper.offer.suggestion || '',
          bestHelper.assistingAgent
        );

        if (retryResult.status === TaskStatus.COMPLETED) {
          console.error(`[DailyStandup] ✅ Task completed with peer help!`);
          blockersResolved++;
          assistanceResult.outcome.blockerResolved = true;
          assistanceResult.outcome.newAttemptSuccessful = true;

          // Update agent expertise
          updateAgentExpertise(bestHelper.assistingAgent, assistanceResult);
        } else {
          console.error(`[DailyStandup] ❌ Retry failed even with peer help`);
          console.error(`[DailyStandup] 🚨 Escalating to human...`);

          // Update blocker with peer help info
          blocker.peerHelpAttempted = true;
          blocker.peerHelpProviders = [bestHelper.assistingAgent];

          await escalateToHuman(blocker, escalationConfig);
          blockersEscalated++;

          // Update agent expertise with failure
          assistanceResult.outcome.blockerResolved = false;
          updateAgentExpertise(bestHelper.assistingAgent, assistanceResult);
        }
      } catch (error) {
        console.error(`[DailyStandup] ❌ Error during retry: ${error}`);
        console.error(`[DailyStandup] 🚨 Escalating to human...`);

        blocker.peerHelpAttempted = true;
        blocker.peerHelpProviders = [bestHelper.assistingAgent];
        await escalateToHuman(blocker, escalationConfig);
        blockersEscalated++;
      }
    }
  }

  // Step 8: Calculate metrics
  const totalTimeSpent = (Date.now() - startTime) / 1000;

  const metrics = {
    agentsWithBlockers: agentsWithBlockers.length,
    peerHelpRequests: peerAssistanceProvided.length,
    peerHelpSuccess: peerAssistanceProvided.filter(p => p.outcome.blockerResolved).length,
    humanEscalations: blockersEscalated,
    timeSavedByPeers: peerAssistanceProvided
      .filter(p => p.outcome.blockerResolved)
      .reduce((sum, p) => sum + p.outcome.timeSpent, 0)
  };

  // Step 9: Print summary
  console.error('\n' + '='.repeat(80));
  console.error('📊 STANDUP SUMMARY');
  console.error('='.repeat(80));
  console.error(`Total time: ${totalTimeSpent.toFixed(2)}s`);
  console.error(`Blockers resolved by peers: ${blockersResolved}`);
  console.error(`Blockers escalated to human: ${blockersEscalated}`);
  console.error(`Peer help success rate: ${metrics.peerHelpRequests > 0
    ? ((metrics.peerHelpSuccess / metrics.peerHelpRequests) * 100).toFixed(0)
    : 0}%`);
  console.error(`Time saved by peer assistance: ${metrics.timeSavedByPeers.toFixed(2)}s`);
  console.error('='.repeat(80) + '\n');

  return {
    timestamp: new Date(),
    reports,
    peerAssistanceProvided,
    blockersResolved,
    blockersEscalated,
    totalTimeSpent,
    metrics
  };
}

/**
 * Collect standup report from an agent
 */
async function collectStandupReport(
  agent: Agent,
  existingBlockers?: BlockingIssue[]
): Promise<StandupReport> {

  // In real implementation, would query agent's task history
  // For now, return mock report or use existing blockers

  const agentBlockers = existingBlockers?.filter(b => b.agentName === agent.name) || [];

  const mood: 'productive' | 'struggling' | 'blocked' =
    agentBlockers.length === 0 ? 'productive' :
    agentBlockers.length <= 2 ? 'struggling' :
    'blocked';

  return {
    agentName: agent.name,
    timestamp: new Date(),
    yesterday: [
      'Completed assigned tasks',
      'Participated in code review'
    ],
    today: [
      'Continue with current work items',
      'Help peers with blockers'
    ],
    blockers: agentBlockers,
    needsHelp: agentBlockers.length > 0,
    availableToHelp: agentBlockers.length === 0,
    mood
  };
}

/**
 * Get mood emoji
 */
function getMoodEmoji(mood: 'productive' | 'struggling' | 'blocked'): string {
  switch (mood) {
    case 'productive': return '😊';
    case 'struggling': return '😰';
    case 'blocked': return '😱';
  }
}

/**
 * Create scheduled standup
 */
export function scheduleStandup(
  activeAgents: Agent[],
  timeOfDay: string = '09:00',
  escalationConfig?: EscalationConfig
): void {
  console.error(`[DailyStandup] 📅 Scheduled daily standup for ${timeOfDay}`);

  // In real implementation, would use cron or scheduler
  // For now, just log the configuration
  console.error(`[DailyStandup] Agents: ${activeAgents.map(a => a.name).join(', ')}`);
  console.error(`[DailyStandup] Escalation channels: ${escalationConfig?.channels.length || 0}`);
}

/**
 * Emergency standup (triggered by critical blocker)
 */
export async function triggerEmergencyStandup(
  criticalBlocker: BlockingIssue,
  activeAgents: Agent[],
  escalationConfig?: EscalationConfig
): Promise<StandupSessionResult> {

  console.error('\n' + '='.repeat(80));
  console.error('🚨 EMERGENCY STANDUP - CRITICAL BLOCKER');
  console.error('='.repeat(80));
  console.error(`Task: ${criticalBlocker.taskId}`);
  console.error(`Agent: ${criticalBlocker.agentName}`);
  console.error(`Priority: ${criticalBlocker.priority}`);
  console.error('='.repeat(80) + '\n');

  // Execute standup with only the critical blocker
  return executeDailyStandup(activeAgents, [criticalBlocker], escalationConfig);
}
