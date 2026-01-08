/**
 * Sprint Planning Ceremony
 *
 * Automated sprint planning with agent collaboration
 * Facilitator: Paul (Project Lead)
 * Product Owner: Peter
 * Team: All available agents
 */

import { Agent } from 'kaibanjs';
import {
  SprintPlanningInput,
  SprintPlan,
  SprintPlanningSession,
  BacklogItem,
  StoryCommitment,
  AgentCapacity,
  SprintRisk,
  SprintGoal,
  SprintStatus,
  VelocityMetrics,
  PlanningDecision,
  calculateCapacityUtilization,
  calculateSprintRiskScore,
  canFitStory,
  calculateVelocityTrend
} from '../../types/Sprint';

/**
 * Execute Sprint Planning ceremony
 */
export async function executeSprintPlanning(
  input: SprintPlanningInput,
  agents: Agent[]
): Promise<SprintPlanningSession> {

  console.error('\n' + '='.repeat(80));
  console.error('📅 SPRINT PLANNING CEREMONY');
  console.error('='.repeat(80));
  console.error(`Sprint Number: ${input.sprintNumber}`);
  console.error(`Duration: ${input.sprintDuration} days`);
  console.error(`Available Agents: ${input.availableAgents.length}`);
  console.error(`Backlog Items: ${input.backlog.length}`);
  console.error('='.repeat(80) + '\n');

  const sessionStart = Date.now();
  const sessionId = `sprint-planning-${input.sprintNumber}-${Date.now()}`;
  const decisionsLog: PlanningDecision[] = [];

  // Step 1: Calculate agent capacities
  console.error('[Sprint Planning] Step 1: Calculating agent capacities...');
  const agentCapacities = calculateAgentCapacities(
    input.availableAgents,
    input.agentAvailability,
    input.sprintDuration
  );

  const totalCapacity = agentCapacities.reduce((sum, a) => sum + a.availableHours, 0);
  console.error(`[Sprint Planning] Total team capacity: ${totalCapacity} hours`);

  agentCapacities.forEach(ac => {
    console.error(`  ${ac.agentName}: ${ac.availableHours} hours`);
  });

  // Step 2: Prioritize backlog
  console.error('\n[Sprint Planning] Step 2: Prioritizing backlog...');
  const prioritizedBacklog = prioritizeBacklog(input.backlog);

  console.error(`[Sprint Planning] Top 5 priorities:`);
  prioritizedBacklog.slice(0, 5).forEach((item, idx) => {
    console.error(`  ${idx + 1}. ${item.title} (${item.storyPoints} SP, ${item.priority})`);
  });

  // Step 3: Select stories for sprint
  console.error('\n[Sprint Planning] Step 3: Selecting stories for sprint...');
  const { committedStories, capacities, remainingCapacity } = selectStoriesForSprint(
    prioritizedBacklog,
    agentCapacities,
    totalCapacity
  );

  console.error(`[Sprint Planning] Selected ${committedStories.length} stories`);
  console.error(`[Sprint Planning] Total story points: ${committedStories.reduce((sum, s) => sum + s.storyPoints, 0)}`);
  console.error(`[Sprint Planning] Capacity utilization: ${calculateCapacityUtilization(totalCapacity, totalCapacity - remainingCapacity)}%`);

  // Step 4: Identify risks
  console.error('\n[Sprint Planning] Step 4: Identifying risks...');
  const risks = identifySprintRisks(
    committedStories,
    capacities,
    input.sprintDuration
  );

  console.error(`[Sprint Planning] Identified ${risks.length} risks`);
  risks.forEach(risk => {
    console.error(`  [${risk.severity}] ${risk.category}: ${risk.description}`);
  });

  const riskScore = calculateSprintRiskScore(risks);
  console.error(`[Sprint Planning] Overall risk score: ${(riskScore * 100).toFixed(0)}%`);

  // Step 5: Define sprint goal
  console.error('\n[Sprint Planning] Step 5: Defining sprint goal...');
  const sprintGoal = defineSprintGoal(committedStories, input.teamGoals);

  console.error(`[Sprint Planning] Sprint Goal: ${sprintGoal.description}`);
  console.error(`[Sprint Planning] Business Value: ${sprintGoal.businessValue}`);

  // Step 6: Calculate velocity forecast
  console.error('\n[Sprint Planning] Step 6: Calculating velocity forecast...');
  const velocityMetrics = calculateVelocityForecast(
    committedStories,
    input.previousVelocity
  );

  console.error(`[Sprint Planning] Forecasted velocity: ${velocityMetrics.forecastedVelocity} SP`);
  console.error(`[Sprint Planning] Trend: ${velocityMetrics.trendDirection}`);
  console.error(`[Sprint Planning] Confidence: ${(velocityMetrics.confidence * 100).toFixed(0)}%`);

  // Step 7: Build consensus
  console.error('\n[Sprint Planning] Step 7: Building team consensus...');
  const consensusReached = await buildConsensus(
    committedStories,
    sprintGoal,
    risks,
    agents,
    decisionsLog
  );

  if (consensusReached) {
    console.error(`[Sprint Planning] ✅ Team consensus reached!`);
  } else {
    console.error(`[Sprint Planning] ⚠️ Some concerns remain, but proceeding...`);
  }

  // Step 8: Finalize sprint plan
  console.error('\n[Sprint Planning] Step 8: Finalizing sprint plan...');

  const startDate = new Date();
  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + input.sprintDuration);

  const sprintPlan: SprintPlan = {
    sprintId: `sprint-${input.sprintNumber}`,
    sprintNumber: input.sprintNumber,
    sprintGoal,
    startDate,
    endDate,
    durationDays: input.sprintDuration,

    totalCapacityHours: totalCapacity,
    allocatedCapacityHours: totalCapacity - remainingCapacity,
    capacityUtilization: calculateCapacityUtilization(totalCapacity, totalCapacity - remainingCapacity),
    agentCapacities: capacities,

    committedStories,
    totalStoryPoints: committedStories.reduce((sum, s) => sum + s.storyPoints, 0),
    totalEstimatedHours: committedStories.reduce((sum, s) => sum + s.estimatedHours, 0),

    velocityMetrics,

    identifiedRisks: risks,
    riskScore,

    createdBy: 'Paul', // Project Lead facilitates
    createdAt: new Date(),
    participants: input.availableAgents,
    status: SprintStatus.PLANNED,

    definitionOfDone: getDefinitionOfDone()
  };

  const sessionDuration = (Date.now() - sessionStart) / 1000 / 60; // Minutes

  console.error('\n' + '='.repeat(80));
  console.error('📊 SPRINT PLANNING COMPLETE');
  console.error('='.repeat(80));
  console.error(`Duration: ${sessionDuration.toFixed(1)} minutes`);
  console.error(`Stories committed: ${committedStories.length}`);
  console.error(`Total story points: ${sprintPlan.totalStoryPoints}`);
  console.error(`Capacity utilization: ${sprintPlan.capacityUtilization}%`);
  console.error(`Risk score: ${(riskScore * 100).toFixed(0)}%`);
  console.error(`Consensus: ${consensusReached ? 'YES ✅' : 'PARTIAL ⚠️'}`);
  console.error('='.repeat(80) + '\n');

  return {
    sessionId,
    input,
    plan: sprintPlan,
    planningDuration: sessionDuration,
    decisionsLog,
    consensusReached
  };
}

/**
 * Calculate agent capacities
 */
function calculateAgentCapacities(
  availableAgents: string[],
  agentAvailability: Record<string, number>,
  sprintDuration: number
): AgentCapacity[] {

  return availableAgents.map(agentName => ({
    agentName,
    availableHours: agentAvailability[agentName] || (sprintDuration * 6), // 6 hours/day default
    allocatedHours: 0,
    remainingHours: agentAvailability[agentName] || (sprintDuration * 6),
    utilizationPercentage: 0,
    assignedStories: []
  }));
}

/**
 * Prioritize backlog items
 */
function prioritizeBacklog(backlog: BacklogItem[]): BacklogItem[] {
  // Sort by: priority, then business value, then story points (smaller first)
  return [...backlog]
    .filter(item => !item.blocked) // Filter out blocked items
    .sort((a, b) => {
      // Priority weights
      const priorityWeight = {
        'CRITICAL': 4,
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1
      };

      const aPriority = priorityWeight[a.priority];
      const bPriority = priorityWeight[b.priority];

      if (aPriority !== bPriority) {
        return bPriority - aPriority; // Higher priority first
      }

      // Same priority: sort by business value
      if (a.businessValue !== b.businessValue) {
        return b.businessValue - a.businessValue; // Higher value first
      }

      // Same business value: sort by story points (smaller first for better flow)
      return a.storyPoints - b.storyPoints;
    });
}

/**
 * Select stories for sprint
 */
function selectStoriesForSprint(
  prioritizedBacklog: BacklogItem[],
  agentCapacities: AgentCapacity[],
  totalCapacity: number
): {
  committedStories: StoryCommitment[];
  capacities: AgentCapacity[];
  remainingCapacity: number;
} {

  const committedStories: StoryCommitment[] = [];
  let remainingCapacity = totalCapacity;

  // Target 80% capacity utilization (leave buffer for unknowns)
  const targetCapacity = totalCapacity * 0.8;

  for (const item of prioritizedBacklog) {
    // Check if story fits
    if (!canFitStory(item, remainingCapacity, agentCapacities)) {
      continue;
    }

    // Check if we've reached target capacity
    if (totalCapacity - remainingCapacity >= targetCapacity) {
      break;
    }

    // Assign agents
    const assignedAgents = assignAgentsToStory(item, agentCapacities);

    if (assignedAgents.length === 0) {
      continue; // Can't assign agents, skip story
    }

    // Commit story
    committedStories.push({
      storyId: item.storyId,
      title: item.title,
      storyPoints: item.storyPoints,
      estimatedHours: item.estimatedHours,
      priority: item.priority,
      assignedAgents,
      dependencies: item.dependencies,
      acceptanceCriteria: item.acceptanceCriteria,
      risks: identifyStoryRisks(item)
    });

    // Update capacities
    const hoursPerAgent = item.estimatedHours / assignedAgents.length;
    assignedAgents.forEach(agentName => {
      const capacity = agentCapacities.find(c => c.agentName === agentName);
      if (capacity) {
        capacity.allocatedHours += hoursPerAgent;
        capacity.remainingHours -= hoursPerAgent;
        capacity.utilizationPercentage = (capacity.allocatedHours / capacity.availableHours) * 100;
        capacity.assignedStories.push(item.storyId);
      }
    });

    remainingCapacity -= item.estimatedHours;
  }

  return { committedStories, capacities: agentCapacities, remainingCapacity };
}

/**
 * Assign agents to story based on required skills
 */
function assignAgentsToStory(
  story: BacklogItem,
  agentCapacities: AgentCapacity[]
): string[] {

  const assignedAgents: string[] = [];

  for (const skill of story.requiredSkills) {
    const agent = agentCapacities.find(a =>
      a.agentName === skill && a.remainingHours >= story.estimatedHours / story.requiredSkills.length
    );

    if (agent) {
      assignedAgents.push(agent.agentName);
    }
  }

  // If no specific skills required, assign to agent with most capacity
  if (assignedAgents.length === 0 && story.requiredSkills.length === 0) {
    const agentWithMostCapacity = agentCapacities
      .filter(a => a.remainingHours >= story.estimatedHours)
      .sort((a, b) => b.remainingHours - a.remainingHours)[0];

    if (agentWithMostCapacity) {
      assignedAgents.push(agentWithMostCapacity.agentName);
    }
  }

  return assignedAgents;
}

/**
 * Identify story-specific risks
 */
function identifyStoryRisks(story: BacklogItem): string[] {
  const risks: string[] = [];

  if (story.storyPoints >= 8) {
    risks.push('Large story - consider breaking down');
  }

  if (story.dependencies.length > 2) {
    risks.push('Multiple dependencies - potential blocking');
  }

  if (story.technicalComplexity >= 8) {
    risks.push('High technical complexity - may need spikes');
  }

  return risks;
}

/**
 * Identify sprint-level risks
 */
function identifySprintRisks(
  committedStories: StoryCommitment[],
  agentCapacities: AgentCapacity[],
  sprintDuration: number
): SprintRisk[] {

  const risks: SprintRisk[] = [];

  // Check capacity utilization
  const overloadedAgents = agentCapacities.filter(a => a.utilizationPercentage > 90);
  if (overloadedAgents.length > 0) {
    risks.push({
      id: `risk-capacity-${Date.now()}`,
      category: 'CAPACITY',
      severity: 'HIGH',
      description: `${overloadedAgents.length} agent(s) over 90% capacity`,
      impact: 'Potential burnout, missed commitments',
      likelihood: 0.7,
      mitigation: 'Consider removing lower-priority stories',
      owner: 'Paul'
    });
  }

  // Check for dependency chains
  const storiesWithDeps = committedStories.filter(s => s.dependencies.length > 0);
  if (storiesWithDeps.length > committedStories.length * 0.5) {
    risks.push({
      id: `risk-dependency-${Date.now()}`,
      category: 'DEPENDENCY',
      severity: 'MEDIUM',
      description: 'Over 50% of stories have dependencies',
      impact: 'Potential bottlenecks and delays',
      likelihood: 0.6,
      mitigation: 'Daily standup focus on dependency resolution',
      owner: 'Paul'
    });
  }

  // Check sprint duration vs story points
  const avgVelocityPerDay = committedStories.reduce((sum, s) => sum + s.storyPoints, 0) / sprintDuration;
  if (avgVelocityPerDay > 10) {
    risks.push({
      id: `risk-scope-${Date.now()}`,
      category: 'SCOPE',
      severity: 'MEDIUM',
      description: `High daily velocity target (${avgVelocityPerDay.toFixed(1)} SP/day)`,
      impact: 'Quality may suffer',
      likelihood: 0.5,
      mitigation: 'Enforce Definition of Done strictly',
      owner: 'Quinn'
    });
  }

  return risks;
}

/**
 * Define sprint goal
 */
function defineSprintGoal(
  committedStories: StoryCommitment[],
  teamGoals?: string[]
): SprintGoal {

  // Analyze committed stories to create goal
  const priorities = committedStories.map(s => s.priority);
  const hasCritical = priorities.includes('CRITICAL');
  const hasHigh = priorities.includes('HIGH');

  let description = '';
  if (hasCritical) {
    description = 'Complete critical features and resolve high-priority issues';
  } else if (hasHigh) {
    description = 'Deliver high-value features to increase user satisfaction';
  } else {
    description = 'Improve product quality and add requested enhancements';
  }

  const businessValue = teamGoals?.[0] || 'Increase product value and user satisfaction';

  return {
    description,
    businessValue,
    successCriteria: [
      `Complete ${committedStories.length} committed stories`,
      'All stories meet Definition of Done',
      'Zero critical bugs introduced',
      'Test coverage maintained above 80%'
    ],
    measurableOutcomes: [
      `${committedStories.reduce((sum, s) => sum + s.storyPoints, 0)} story points delivered`,
      `${committedStories.length} features deployed to production`,
      'User satisfaction score improvement'
    ]
  };
}

/**
 * Calculate velocity forecast
 */
function calculateVelocityForecast(
  committedStories: StoryCommitment[],
  previousVelocity?: VelocityMetrics
): VelocityMetrics {

  const forecastedVelocity = committedStories.reduce((sum, s) => sum + s.storyPoints, 0);

  if (!previousVelocity) {
    return {
      lastSprintVelocity: 0,
      averageVelocity: 0,
      trendDirection: 'STABLE',
      confidence: 0.5, // Low confidence without history
      forecastedVelocity
    };
  }

  const trend = calculateVelocityTrend([
    previousVelocity.lastSprintVelocity,
    previousVelocity.averageVelocity,
    forecastedVelocity
  ]);

  const difference = Math.abs(forecastedVelocity - previousVelocity.averageVelocity);
  const variance = difference / previousVelocity.averageVelocity;
  const confidence = Math.max(0.3, Math.min(0.9, 1 - variance));

  return {
    lastSprintVelocity: previousVelocity.lastSprintVelocity,
    averageVelocity: previousVelocity.averageVelocity,
    trendDirection: trend,
    confidence,
    forecastedVelocity
  };
}

/**
 * Build consensus among agents
 */
async function buildConsensus(
  committedStories: StoryCommitment[],
  sprintGoal: SprintGoal,
  risks: SprintRisk[],
  agents: Agent[],
  decisionsLog: PlanningDecision[]
): Promise<boolean> {

  // Check if any agent is overloaded
  const concerns: string[] = [];

  // Simulate consensus building
  if (risks.length > 3) {
    concerns.push('High number of risks identified');
  }

  if (committedStories.reduce((sum, s) => sum + s.storyPoints, 0) > 50) {
    concerns.push('Very ambitious sprint scope');
  }

  // Log consensus decision
  decisionsLog.push({
    timestamp: new Date(),
    decision: 'Commit to sprint plan',
    rationale: concerns.length === 0
      ? 'Balanced workload, manageable risks, clear goal'
      : `Some concerns raised: ${concerns.join(', ')}. Team agrees to proceed with mitigation.`,
    proposedBy: 'Paul',
    supportedBy: agents.map(a => a.name),
    opposedBy: [],
    finalDecision: 'ACCEPTED'
  });

  return concerns.length <= 1; // Consensus if 0-1 concerns
}

/**
 * Get Definition of Done
 */
function getDefinitionOfDone(): string[] {
  return [
    'Code complete and reviewed',
    'Unit tests written and passing (> 80% coverage)',
    'Integration tests passing',
    'Documentation updated',
    'No critical or high severity bugs',
    'Acceptance criteria met',
    'Deployed to staging environment',
    'Product Owner approval received'
  ];
}
