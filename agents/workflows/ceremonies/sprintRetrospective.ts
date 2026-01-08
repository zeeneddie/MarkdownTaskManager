/**
 * Sprint Retrospective Ceremony Workflow
 *
 * Automated sprint retrospective with team reflection and continuous improvement.
 * Facilitator: Scrum Master (Paul)
 * Participants: All agents
 */

// @ts-ignore - KaibanJS types will be available at runtime
import { Agent } from '@kaibanjs/core';
import {
  SprintRetrospectiveResult,
  SprintRetrospectiveSession,
  RetrospectiveDecision,
  RetrospectiveStatus,
  RetrospectiveFeedback,
  FeedbackCategory,
  ActionItem,
  ActionItemPriority,
  ActionItemStatus,
  TeamHealthMetric,
  HealthMetricType,
  ProcessImprovement,
  AgentExpertiseUpdate,
  LearningOutcome,
  Celebration,
  RetrospectiveInput,
  calculateActionItemCompletionRate,
  calculateOverallTeamHealth,
  determineTeamHealthTrend,
  prioritizeFeedback,
  calculateHealthTrend,
  generateActionItemFromFeedback
} from '../../types/Retrospective';

/**
 * Execute Sprint Retrospective Ceremony
 */
export async function executeSprintRetrospective(
  input: RetrospectiveInput,
  agents: Agent[]
): Promise<SprintRetrospectiveSession> {
  const startTime = Date.now();
  const sessionId = `retro-${input.sprintNumber}-${Date.now()}`;
  const decisionsLog: RetrospectiveDecision[] = [];

  console.error('\n' + '='.repeat(80));
  console.error('🔄 SPRINT RETROSPECTIVE CEREMONY');
  console.error('='.repeat(80));
  console.error(`Sprint: #${input.sprintNumber}`);
  console.error(`Facilitator: Paul (Scrum Master)`);
  console.error(`Participants: ${agents.map(a => a.name).join(', ')}`);
  console.error('='.repeat(80) + '\n');

  // Step 1: Review previous action items
  console.error('📋 Step 1: Reviewing Previous Action Items...');
  const previousActionItems = input.previousActionItems || [];
  const completedActionItems = previousActionItems.filter(
    item => item.status === ActionItemStatus.COMPLETED
  ).length;
  const actionItemsCompletionRate = calculateActionItemCompletionRate(
    completedActionItems,
    previousActionItems.length
  );
  console.error(`   ✓ ${completedActionItems}/${previousActionItems.length} action items completed (${actionItemsCompletionRate}%)\n`);

  // Step 2: Collect "What went well"
  console.error('😊 Step 2: What Went Well...');
  const whatWentWell = await collectFeedback(
    FeedbackCategory.WHAT_WENT_WELL,
    agents,
    input.sprintMetrics
  );
  const topPositives = prioritizeFeedback(whatWentWell).slice(0, 5);
  console.error(`   ✓ ${whatWentWell.length} positive items collected`);
  console.error(`   ✓ Top item: "${topPositives[0]?.description.substring(0, 50)}..." (${topPositives[0]?.votes} votes)\n`);

  // Step 3: Collect "What didn't go well"
  console.error('😟 Step 3: What Didn\'t Go Well...');
  const whatDidntGoWell = await collectFeedback(
    FeedbackCategory.WHAT_DIDNT_GO_WELL,
    agents,
    input.sprintMetrics
  );
  const topChallenges = prioritizeFeedback(whatDidntGoWell).slice(0, 5);
  console.error(`   ✓ ${whatDidntGoWell.length} challenge items collected`);
  console.error(`   ✓ Top concern: "${topChallenges[0]?.description.substring(0, 50)}..." (${topChallenges[0]?.votes} votes)\n`);

  // Step 4: Collect improvement suggestions
  console.error('💡 Step 4: Improvement Suggestions...');
  const improvements = await collectFeedback(
    FeedbackCategory.WHAT_TO_IMPROVE,
    agents,
    input.sprintMetrics
  );
  const topImprovements = prioritizeFeedback(improvements).slice(0, 5);
  console.error(`   ✓ ${improvements.length} improvement ideas collected`);
  console.error(`   ✓ Top idea: "${topImprovements[0]?.description.substring(0, 50)}..." (${topImprovements[0]?.votes} votes)\n`);

  // Step 5: Collect appreciations
  console.error('🙏 Step 5: Team Appreciations...');
  const appreciations = await collectFeedback(
    FeedbackCategory.APPRECIATION,
    agents,
    input.sprintMetrics
  );
  console.error(`   ✓ ${appreciations.length} appreciations shared\n`);

  // Step 6: Generate action items
  console.error('✅ Step 6: Generating Action Items...');
  const actionItems = generateActionItems(
    topChallenges,
    topImprovements,
    agents,
    decisionsLog
  );
  console.error(`   ✓ ${actionItems.length} action items created`);
  console.error(`   ✓ ${actionItems.filter(a => a.priority === ActionItemPriority.HIGH).length} high priority\n`);

  // Step 7: Assess team health
  console.error('❤️ Step 7: Assessing Team Health...');
  const teamHealthMetrics = assessTeamHealth(
    whatWentWell,
    whatDidntGoWell,
    input.previousTeamHealth
  );
  const overallTeamHealthScore = calculateOverallTeamHealth(teamHealthMetrics);
  const teamHealthTrend = determineTeamHealthTrend(overallTeamHealthScore, teamHealthMetrics);
  console.error(`   ✓ Overall team health: ${overallTeamHealthScore.toFixed(1)}/10`);
  console.error(`   ✓ Trend: ${teamHealthTrend}\n`);

  // Step 8: Vote on process improvements
  console.error('🗳️ Step 8: Process Improvement Voting...');
  const processImprovements = generateProcessImprovements(
    whatDidntGoWell,
    improvements,
    agents,
    decisionsLog
  );
  const acceptedImprovements = processImprovements.filter(p => p.vote === 'ACCEPTED').length;
  console.error(`   ✓ ${acceptedImprovements}/${processImprovements.length} process improvements accepted\n`);

  // Step 9: Update agent expertise
  console.error('🎓 Step 9: Updating Agent Expertise...');
  const agentExpertiseUpdates = updateAgentExpertise(
    agents,
    whatWentWell,
    whatDidntGoWell
  );
  const totalNewSkills = agentExpertiseUpdates.reduce(
    (sum, update) => sum + update.newSkillsAcquired.length,
    0
  );
  console.error(`   ✓ ${totalNewSkills} new skills acquired across team\n`);

  // Step 10: Capture learning outcomes
  console.error('📚 Step 10: Capturing Learning Outcomes...');
  const learningOutcomes = captureLearningOutcomes(
    whatWentWell,
    whatDidntGoWell,
    agents
  );
  console.error(`   ✓ ${learningOutcomes.length} learning outcomes documented\n`);

  // Step 11: Celebrate wins
  console.error('🎉 Step 11: Celebrating Wins...');
  const celebrations = celebrateWins(
    whatWentWell,
    input.sprintMetrics,
    agents
  );
  console.error(`   ✓ ${celebrations.length} achievements celebrated\n`);

  // Step 12: Define key takeaways and next focus
  console.error('🎯 Step 12: Key Takeaways & Next Focus...');
  const keyTakeaways = generateKeyTakeaways(
    topPositives,
    topChallenges,
    actionItems,
    teamHealthTrend
  );
  const nextRetroFocus = generateNextRetroFocus(
    actionItems,
    processImprovements,
    teamHealthMetrics
  );
  console.error(`   ✓ ${keyTakeaways.length} key takeaways identified`);
  console.error(`   ✓ ${nextRetroFocus.length} focus areas for next retro\n`);

  const retrospectiveDuration = Math.round((Date.now() - startTime) / 1000 / 60);
  const consensusReached = calculateConsensus(actionItems, processImprovements);

  const result: SprintRetrospectiveResult = {
    retrospectiveId: `retro-${input.sprintId}`,
    sprintId: input.sprintId,
    sprintNumber: input.sprintNumber,
    retrospectiveDate: new Date(),
    retrospectiveDuration,

    facilitator: 'Paul',
    participants: agents.map(a => a.name),

    whatWentWell,
    whatDidntGoWell,
    improvements,
    appreciations,

    actionItems,
    actionItemsFromPreviousRetro: previousActionItems,
    actionItemsCompleted: completedActionItems,
    actionItemsCompletionRate,

    teamHealthMetrics,
    overallTeamHealthScore,
    teamHealthTrend,

    processImprovements,
    acceptedImprovements,

    learningOutcomes,
    agentExpertiseUpdates,

    celebrations,

    status: RetrospectiveStatus.COMPLETED,
    consensusReached,
    keyTakeaways,
    nextRetroFocus,
    notes: generateRetrospectiveNotes(
      overallTeamHealthScore,
      actionItems.length,
      acceptedImprovements
    )
  };

  console.error('='.repeat(80));
  console.error('✅ SPRINT RETROSPECTIVE COMPLETE');
  console.error('='.repeat(80));
  console.error(`Duration: ${retrospectiveDuration} minutes`);
  console.error(`Team Health: ${overallTeamHealthScore.toFixed(1)}/10 (${teamHealthTrend})`);
  console.error(`Action Items: ${actionItems.length} created`);
  console.error(`Process Improvements: ${acceptedImprovements} accepted`);
  console.error(`Learning Outcomes: ${learningOutcomes.length} captured`);
  console.error('='.repeat(80) + '\n');

  return {
    sessionId,
    sprintId: input.sprintId,
    result,
    decisionsLog
  };
}

/**
 * Collect feedback in a category
 */
async function collectFeedback(
  category: FeedbackCategory,
  agents: Agent[],
  sprintMetrics: any
): Promise<RetrospectiveFeedback[]> {
  const feedback: RetrospectiveFeedback[] = [];

  // Simulate feedback from each agent
  for (const agent of agents) {
    const numItems = Math.floor(Math.random() * 3) + 1; // 1-3 items per agent

    for (let i = 0; i < numItems; i++) {
      const item = generateFeedbackItem(category, agent.name, sprintMetrics);
      feedback.push(item);
    }
  }

  // Simulate voting (other agents vote on items)
  for (const item of feedback) {
    const votes = Math.floor(Math.random() * agents.length);
    item.votes = votes;
    item.votedBy = agents
      .slice(0, votes)
      .map(a => a.name)
      .filter(name => name !== item.submittedBy);
  }

  return feedback;
}

/**
 * Generate a feedback item based on category
 */
function generateFeedbackItem(
  category: FeedbackCategory,
  agentName: string,
  sprintMetrics: any
): RetrospectiveFeedback {
  const templates: Record<FeedbackCategory, string[]> = {
    [FeedbackCategory.WHAT_WENT_WELL]: [
      'Great collaboration on complex technical problems',
      'Effective use of peer assistance when blocked',
      'All stories met acceptance criteria on first attempt',
      'Clear communication throughout the sprint',
      'Efficient use of daily standups for coordination'
    ],
    [FeedbackCategory.WHAT_DIDNT_GO_WELL]: [
      'Some estimation errors led to capacity overload',
      'Dependency between stories caused delays',
      'Technical debt accumulated in legacy code',
      'Insufficient time for code reviews',
      'Quality gate checks took longer than expected'
    ],
    [FeedbackCategory.WHAT_TO_IMPROVE]: [
      'Improve story point estimation accuracy',
      'Add more buffer time for unexpected issues',
      'Better dependency management in sprint planning',
      'More frequent code reviews during development',
      'Enhanced automated testing coverage'
    ],
    [FeedbackCategory.APPRECIATION]: [
      'Thanks to Felix for excellent architecture guidance',
      'Quinn\'s quality checks caught several critical issues',
      'Great teamwork from everyone during crunch time',
      'Diana\'s documentation made everything clear',
      'Paul kept us organized and on track'
    ]
  };

  const descriptions = templates[category];
  const description = descriptions[Math.floor(Math.random() * descriptions.length)];

  return {
    id: `feedback-${Date.now()}-${Math.random()}`,
    category,
    description,
    submittedBy: agentName,
    votes: 0,
    votedBy: [],
    impact: Math.random() > 0.5 ? 'HIGH' : Math.random() > 0.5 ? 'MEDIUM' : 'LOW',
    timestamp: new Date()
  };
}

/**
 * Generate action items from feedback
 */
function generateActionItems(
  challenges: RetrospectiveFeedback[],
  improvements: RetrospectiveFeedback[],
  agents: Agent[],
  decisionsLog: RetrospectiveDecision[]
): ActionItem[] {
  const actionItems: ActionItem[] = [];

  // Take top 3 challenges and create action items
  const topItems = [...challenges, ...improvements].slice(0, 5);

  for (const item of topItems) {
    const owner = agents[Math.floor(Math.random() * agents.length)].name;
    const actionItem = generateActionItemFromFeedback(item, owner);
    actionItem.status = ActionItemStatus.ACCEPTED;

    actionItems.push(actionItem);

    decisionsLog.push({
      timestamp: new Date(),
      decision: `Create action item: ${actionItem.title}`,
      category: 'ACTION_ITEM',
      rationale: `Address high-vote feedback with ${item.votes} votes`,
      proposedBy: 'Paul',
      supportedBy: item.votedBy,
      opposedBy: [],
      finalDecision: 'ACCEPTED'
    });
  }

  return actionItems;
}

/**
 * Assess team health metrics
 */
function assessTeamHealth(
  positives: RetrospectiveFeedback[],
  negatives: RetrospectiveFeedback[],
  previousHealth?: TeamHealthMetric[]
): TeamHealthMetric[] {
  const healthTypes: HealthMetricType[] = [
    HealthMetricType.COMMUNICATION,
    HealthMetricType.COLLABORATION,
    HealthMetricType.MORALE,
    HealthMetricType.WORKLOAD,
    HealthMetricType.TECHNICAL_DEBT,
    HealthMetricType.PROCESS_EFFICIENCY,
    HealthMetricType.QUALITY,
    HealthMetricType.LEARNING
  ];

  return healthTypes.map(type => {
    const baseScore = 7 + (Math.random() * 2 - 1); // 6-8 range
    const positiveBoost = positives.filter(p =>
      p.description.toLowerCase().includes(type.toLowerCase())
    ).length * 0.5;
    const negativeHit = negatives.filter(n =>
      n.description.toLowerCase().includes(type.toLowerCase())
    ).length * 0.5;

    const score = Math.max(1, Math.min(10, baseScore + positiveBoost - negativeHit));
    const previousMetric = previousHealth?.find(h => h.type === type);
    const previousScore = previousMetric?.score;

    return {
      type,
      score: Math.round(score * 10) / 10,
      trend: calculateHealthTrend(score, previousScore),
      previousScore,
      feedback: [],
      concerns: negatives.filter(n => n.impact === 'HIGH').map(n => n.description).slice(0, 2),
      strengths: positives.filter(p => p.impact === 'HIGH').map(p => p.description).slice(0, 2)
    };
  });
}

/**
 * Generate process improvement proposals
 */
function generateProcessImprovements(
  negatives: RetrospectiveFeedback[],
  improvements: RetrospectiveFeedback[],
  agents: Agent[],
  decisionsLog: RetrospectiveDecision[]
): ProcessImprovement[] {
  const proposals: ProcessImprovement[] = [];
  const topIssues = prioritizeFeedback(negatives).slice(0, 3);

  for (const issue of topIssues) {
    const improvement: ProcessImprovement = {
      id: `improvement-${Date.now()}-${Math.random()}`,
      title: `Improve: ${issue.description.substring(0, 40)}`,
      description: `Address the issue: ${issue.description}`,
      currentProcess: 'Current sprint workflow',
      proposedChange: `Implement changes to address: ${issue.description}`,
      expectedBenefit: 'Reduce similar issues in future sprints',
      estimatedEffort: issue.impact === 'HIGH' ? 'MEDIUM' : 'LOW',
      riskLevel: 'LOW',
      proposedBy: issue.submittedBy,
      supportedBy: issue.votedBy,
      opposedBy: [],
      vote: issue.votes >= 2 ? 'ACCEPTED' : 'DEFERRED'
    };

    proposals.push(improvement);

    if (improvement.vote === 'ACCEPTED') {
      decisionsLog.push({
        timestamp: new Date(),
        decision: `Accept process improvement: ${improvement.title}`,
        category: 'PROCESS_CHANGE',
        rationale: `${issue.votes} votes in favor`,
        proposedBy: improvement.proposedBy,
        supportedBy: improvement.supportedBy,
        opposedBy: [],
        finalDecision: 'ACCEPTED'
      });
    }
  }

  return proposals;
}

/**
 * Update agent expertise based on sprint learnings
 */
function updateAgentExpertise(
  agents: Agent[],
  positives: RetrospectiveFeedback[],
  negatives: RetrospectiveFeedback[]
): AgentExpertiseUpdate[] {
  return agents.map(agent => {
    const agentPositives = positives.filter(p => p.submittedBy === agent.name);
    const agentNegatives = negatives.filter(n => n.submittedBy === agent.name);

    return {
      agentName: agent.name,
      previousExpertise: [],
      newSkillsAcquired: agentPositives.length > 2 ? ['Advanced collaboration'] : [],
      skillsImproved: agentPositives.map(p => p.description).slice(0, 2),
      areasNeedingImprovement: agentNegatives.map(n => n.description).slice(0, 2),
      confidenceLevels: {},
      learningGoals: ['Improve estimation accuracy', 'Better quality practices'],
      mentorshipOffered: [],
      mentorshipNeeded: []
    };
  });
}

/**
 * Capture learning outcomes from sprint
 */
function captureLearningOutcomes(
  positives: RetrospectiveFeedback[],
  negatives: RetrospectiveFeedback[],
  agents: Agent[]
): LearningOutcome[] {
  const outcomes: LearningOutcome[] = [];

  // Positive learnings
  for (const positive of positives.slice(0, 3)) {
    outcomes.push({
      id: `learning-${Date.now()}-${Math.random()}`,
      category: 'PROCESS',
      title: positive.description,
      description: `Successfully applied: ${positive.description}`,
      learnedBy: [positive.submittedBy, ...positive.votedBy.slice(0, 2)],
      source: `Sprint ${positive.submittedBy} experience`,
      applicability: positive.impact === 'HIGH' ? 'HIGH' : 'MEDIUM',
      documented: true
    });
  }

  return outcomes;
}

/**
 * Celebrate team wins
 */
function celebrateWins(
  positives: RetrospectiveFeedback[],
  sprintMetrics: any,
  agents: Agent[]
): Celebration[] {
  const celebrations: Celebration[] = [];

  // Top positive items become celebrations
  const topWins = prioritizeFeedback(positives).slice(0, 3);

  for (const win of topWins) {
    celebrations.push({
      id: `celebration-${Date.now()}-${Math.random()}`,
      title: win.description,
      description: `Team achievement: ${win.description}`,
      type: 'COLLABORATION',
      involvedAgents: [win.submittedBy, ...win.votedBy],
      impact: `Contributed to sprint success with ${win.votes} team votes`,
      celebratedBy: agents.map(a => a.name),
      timestamp: new Date()
    });
  }

  return celebrations;
}

/**
 * Generate key takeaways
 */
function generateKeyTakeaways(
  positives: RetrospectiveFeedback[],
  challenges: RetrospectiveFeedback[],
  actionItems: ActionItem[],
  healthTrend: 'IMPROVING' | 'STABLE' | 'DECLINING'
): string[] {
  return [
    `Team health is ${healthTrend.toLowerCase()}`,
    `Top strength: ${positives[0]?.description || 'Strong collaboration'}`,
    `Main challenge: ${challenges[0]?.description || 'Estimation accuracy'}`,
    `${actionItems.length} action items created for next sprint`,
    'Continuous improvement mindset maintained'
  ];
}

/**
 * Generate focus areas for next retrospective
 */
function generateNextRetroFocus(
  actionItems: ActionItem[],
  improvements: ProcessImprovement[],
  healthMetrics: TeamHealthMetric[]
): string[] {
  const focus: string[] = [];

  // Focus on high-priority action items
  const highPriorityActions = actionItems.filter(a => a.priority === ActionItemPriority.HIGH);
  if (highPriorityActions.length > 0) {
    focus.push(`Track completion of ${highPriorityActions.length} high-priority action items`);
  }

  // Focus on accepted improvements
  const acceptedImprovements = improvements.filter(i => i.vote === 'ACCEPTED');
  if (acceptedImprovements.length > 0) {
    focus.push(`Measure impact of ${acceptedImprovements.length} process improvements`);
  }

  // Focus on declining health metrics
  const decliningMetrics = healthMetrics.filter(h => h.trend === 'DECLINING');
  if (decliningMetrics.length > 0) {
    focus.push(`Address declining ${decliningMetrics[0].type} metric`);
  }

  return focus.length > 0 ? focus : ['General team health and velocity'];
}

/**
 * Calculate consensus
 */
function calculateConsensus(
  actionItems: ActionItem[],
  improvements: ProcessImprovement[]
): boolean {
  const acceptedItems = actionItems.filter(a => a.status === ActionItemStatus.ACCEPTED).length;
  const acceptedImprovements = improvements.filter(i => i.vote === 'ACCEPTED').length;

  return (acceptedItems + acceptedImprovements) > 0;
}

/**
 * Generate retrospective notes
 */
function generateRetrospectiveNotes(
  healthScore: number,
  actionItemsCount: number,
  improvementsCount: number
): string {
  return `Sprint retrospective completed successfully. Team health: ${healthScore.toFixed(1)}/10. ` +
    `Created ${actionItemsCount} action items and accepted ${improvementsCount} process improvements. ` +
    `Team demonstrated strong commitment to continuous improvement.`;
}
