/**
 * Sprint Review Ceremony Workflow
 *
 * Automated sprint review with demo, stakeholder feedback, and acceptance validation.
 * Facilitator: Product Owner (Peter)
 * Participants: Dev Team + Stakeholders
 */

// @ts-ignore - KaibanJS types will be available at runtime
import { Agent } from '@kaibanjs/core';
import {
  SprintReviewResult,
  SprintReviewSession,
  ReviewDecision,
  ReviewStatus,
  CompletedStory,
  DemoResult,
  StakeholderFeedback,
  Stakeholder,
  FeedbackSentiment,
  AcceptanceStatus,
  SprintMetrics,
  BurndownAnalysis,
  BurndownPoint,
  BacklogUpdate,
  calculateVelocityAchievement,
  calculateAcceptanceRate,
  calculateEstimationError,
  determineEstimationTrend,
  analyzeBurndownTrend,
  calculateOverallSentiment,
  areAcceptanceCriteriaMet
} from '../../types/Review';
import { SprintPlan } from '../../types/Sprint';

/**
 * Sprint Review Input
 */
export interface SprintReviewInput {
  sprintPlan: SprintPlan;          // Original sprint plan
  completedStories: CompletedStory[];
  incompleteStories: string[];     // Story IDs that weren't finished
  sprintStartDate: Date;
  sprintEndDate: Date;
  actualWorkData: ActualWorkData[];
  stakeholders?: Stakeholder[];    // Optional stakeholders
}

/**
 * Actual work data for a story
 */
export interface ActualWorkData {
  storyId: string;
  actualHoursSpent: number;
  completionDate: Date;
  completedBy: string[];           // Agent names
}

/**
 * Execute Sprint Review Ceremony
 */
export async function executeSprintReview(
  input: SprintReviewInput,
  agents: Agent[]
): Promise<SprintReviewSession> {
  const startTime = Date.now();
  const sessionId = `review-${input.sprintPlan.sprintNumber}-${Date.now()}`;
  const decisionsLog: ReviewDecision[] = [];

  console.error('\n' + '='.repeat(80));
  console.error('📊 SPRINT REVIEW CEREMONY');
  console.error('='.repeat(80));
  console.error(`Sprint: #${input.sprintPlan.sprintNumber}`);
  console.error(`Facilitator: Peter (Product Owner)`);
  console.error(`Dev Team: ${input.sprintPlan.participants.join(', ')}`);
  console.error(`Completed Stories: ${input.completedStories.length}`);
  console.error(`Incomplete Stories: ${input.incompleteStories.length}`);
  console.error('='.repeat(80) + '\n');

  // Step 1: Prepare demos
  console.error('📋 Step 1: Preparing Demos...');
  const demoResults = prepareDemos(input.completedStories, agents);
  console.error(`   ✓ ${demoResults.length} demos prepared\n`);

  // Step 2: Present completed work
  console.error('🎬 Step 2: Presenting Completed Work...');
  const presentationResults = presentCompletedWork(
    input.completedStories,
    demoResults,
    agents
  );
  console.error(`   ✓ ${presentationResults.successfulDemos} successful demos\n`);

  // Step 3: Collect stakeholder feedback
  console.error('💬 Step 3: Collecting Stakeholder Feedback...');
  const stakeholders = input.stakeholders || getDefaultStakeholders();
  const stakeholderFeedback = await collectStakeholderFeedback(
    input.completedStories,
    demoResults,
    stakeholders,
    agents
  );
  const overallSentiment = calculateOverallSentiment(stakeholderFeedback);
  console.error(`   ✓ ${stakeholderFeedback.length} feedback items collected`);
  console.error(`   ✓ Overall sentiment: ${overallSentiment}\n`);

  // Step 4: Validate acceptance criteria
  console.error('✅ Step 4: Validating Acceptance Criteria...');
  const { accepted, rejected, deferred } = validateAcceptanceCriteria(
    input.completedStories,
    stakeholderFeedback,
    decisionsLog
  );
  console.error(`   ✓ Accepted: ${accepted.length}`);
  console.error(`   ✓ Rejected: ${rejected.length}`);
  console.error(`   ✓ Deferred: ${deferred.length}\n`);

  // Step 5: Analyze sprint metrics
  console.error('📈 Step 5: Analyzing Sprint Metrics...');
  const sprintMetrics = calculateSprintMetrics(
    input.sprintPlan,
    input.completedStories,
    input.incompleteStories,
    input.actualWorkData
  );
  console.error(`   ✓ Velocity: ${sprintMetrics.velocityAchieved}%`);
  console.error(`   ✓ Completion rate: ${sprintMetrics.completionRate}%`);
  console.error(`   ✓ Capacity utilization: ${sprintMetrics.capacityUtilization}%`);
  console.error(`   ✓ Acceptance rate: ${sprintMetrics.acceptanceRate}%\n`);

  // Step 6: Analyze burndown
  console.error('📉 Step 6: Analyzing Burndown Chart...');
  const burndownAnalysis = analyzeBurndown(
    input.sprintPlan,
    input.completedStories,
    input.sprintStartDate,
    input.sprintEndDate
  );
  console.error(`   ✓ Trend: ${burndownAnalysis.trend}`);
  console.error(`   ✓ Average daily velocity: ${burndownAnalysis.averageDailyVelocity.toFixed(1)} SP/day`);
  console.error(`   ✓ Final variance: ${burndownAnalysis.finalVariance.toFixed(1)} SP\n`);

  // Step 7: Update backlog based on feedback
  console.error('📝 Step 7: Updating Backlog...');
  const backlogUpdates = generateBacklogUpdates(
    stakeholderFeedback,
    rejected,
    decisionsLog
  );
  console.error(`   ✓ ${backlogUpdates.length} backlog updates\n`);

  // Step 8: Identify carry-over stories
  console.error('🔄 Step 8: Identifying Carry-Over Stories...');
  const carryOverStories = [...input.incompleteStories, ...rejected];
  console.error(`   ✓ ${carryOverStories.length} stories to carry over\n`);

  // Step 9: Generate improvement suggestions
  console.error('💡 Step 9: Generating Improvement Suggestions...');
  const suggestedImprovements = generateImprovementSuggestions(
    sprintMetrics,
    burndownAnalysis,
    stakeholderFeedback
  );
  console.error(`   ✓ ${suggestedImprovements.length} suggestions\n`);

  // Step 10: Product Owner approval
  console.error('👍 Step 10: Seeking Product Owner Approval...');
  const productOwnerApproval = seekProductOwnerApproval(
    accepted,
    rejected,
    sprintMetrics,
    overallSentiment
  );
  const consensusReached = productOwnerApproval && (rejected.length / input.completedStories.length) < 0.2;
  console.error(`   ✓ Approval: ${productOwnerApproval ? 'GRANTED' : 'WITHHELD'}`);
  console.error(`   ✓ Consensus: ${consensusReached ? 'YES' : 'NO'}\n`);

  const reviewDuration = Math.round((Date.now() - startTime) / 1000 / 60);

  const result: SprintReviewResult = {
    reviewId: `review-${input.sprintPlan.sprintId}`,
    sprintId: input.sprintPlan.sprintId,
    sprintNumber: input.sprintPlan.sprintNumber,
    reviewDate: new Date(),
    reviewDuration,

    facilitator: 'Peter',
    devTeamPresent: input.sprintPlan.participants,
    stakeholdersPresent: stakeholders,

    completedStories: input.completedStories,
    demoResults,

    stakeholderFeedback,
    overallSentiment,

    acceptedStories: accepted,
    rejectedStories: rejected,
    deferredStories: deferred,

    sprintMetrics,
    burndownAnalysis,

    backlogUpdates,

    carryOverStories,
    suggestedImprovements,

    status: ReviewStatus.COMPLETED,
    consensusReached,
    productOwnerApproval,
    notes: generateReviewNotes(sprintMetrics, overallSentiment, consensusReached)
  };

  console.error('='.repeat(80));
  console.error('✅ SPRINT REVIEW COMPLETE');
  console.error('='.repeat(80));
  console.error(`Duration: ${reviewDuration} minutes`);
  console.error(`Accepted: ${accepted.length}/${input.completedStories.length} stories`);
  console.error(`Velocity: ${sprintMetrics.completedStoryPoints}/${sprintMetrics.plannedStoryPoints} SP (${sprintMetrics.velocityAchieved}%)`);
  console.error(`Stakeholder Sentiment: ${overallSentiment}`);
  console.error('='.repeat(80) + '\n');

  return {
    sessionId,
    sprintId: input.sprintPlan.sprintId,
    result,
    decisionsLog
  };
}

/**
 * Prepare demos for completed stories
 */
function prepareDemos(
  stories: CompletedStory[],
  agents: Agent[]
): DemoResult[] {
  return stories.map(story => {
    const presenter = story.assignedAgents[0] || 'Diana';
    const duration = Math.min(15, Math.max(5, story.storyPoints * 3)); // 5-15 min based on points

    return {
      storyId: story.storyId,
      demoGiven: true,
      demoGivenBy: presenter,
      demoDuration: duration,
      visualAidsUsed: ['screenshots', 'architecture diagram'],
      questionsAsked: Math.floor(Math.random() * 5) + 1,
      questionsAnswered: Math.floor(Math.random() * 5) + 1,
      technicalIssues: [],
      audienceEngagement: 'HIGH',
      overallSuccess: true
    };
  });
}

/**
 * Present completed work to stakeholders
 */
function presentCompletedWork(
  stories: CompletedStory[],
  demos: DemoResult[],
  agents: Agent[]
): { successfulDemos: number; failedDemos: number } {
  const successfulDemos = demos.filter(d => d.overallSuccess).length;
  const failedDemos = demos.length - successfulDemos;

  return { successfulDemos, failedDemos };
}

/**
 * Collect stakeholder feedback
 */
async function collectStakeholderFeedback(
  stories: CompletedStory[],
  demos: DemoResult[],
  stakeholders: Stakeholder[],
  agents: Agent[]
): Promise<StakeholderFeedback[]> {
  const feedback: StakeholderFeedback[] = [];

  for (const stakeholder of stakeholders) {
    for (const story of stories) {
      // Determine if stakeholder is interested in this story
      const isInterested = stakeholder.priority === 'HIGH' || Math.random() > 0.5;
      if (!isInterested) continue;

      const demo = demos.find(d => d.storyId === story.storyId);
      const criteriaMet = areAcceptanceCriteriaMet(story.acceptanceCriteriaResults);

      // Simulate stakeholder sentiment based on criteria met and demo success
      let sentiment: FeedbackSentiment;
      let acceptanceVote: AcceptanceStatus;

      if (criteriaMet && demo?.overallSuccess) {
        sentiment = FeedbackSentiment.POSITIVE;
        acceptanceVote = AcceptanceStatus.ACCEPTED;
      } else if (criteriaMet && !demo?.overallSuccess) {
        sentiment = FeedbackSentiment.NEUTRAL;
        acceptanceVote = AcceptanceStatus.ACCEPTED_WITH_NOTES;
      } else {
        sentiment = FeedbackSentiment.NEGATIVE;
        acceptanceVote = AcceptanceStatus.REJECTED;
      }

      feedback.push({
        stakeholder,
        storyId: story.storyId,
        sentiment,
        comments: generateStakeholderComment(sentiment, criteriaMet),
        suggestions: sentiment === FeedbackSentiment.NEGATIVE
          ? ['Improve test coverage', 'Add more edge case handling']
          : [],
        concerns: !criteriaMet
          ? story.acceptanceCriteriaResults.filter(r => !r.met).map(r => r.criterion)
          : [],
        acceptanceVote,
        timestamp: new Date()
      });
    }
  }

  return feedback;
}

/**
 * Validate acceptance criteria for all stories
 */
function validateAcceptanceCriteria(
  stories: CompletedStory[],
  feedback: StakeholderFeedback[],
  decisionsLog: ReviewDecision[]
): {
  accepted: string[];
  rejected: string[];
  deferred: string[];
} {
  const accepted: string[] = [];
  const rejected: string[] = [];
  const deferred: string[] = [];

  for (const story of stories) {
    const storyFeedback = feedback.filter(f => f.storyId === story.storyId);
    const acceptVotes = storyFeedback.filter(
      f => f.acceptanceVote === AcceptanceStatus.ACCEPTED ||
           f.acceptanceVote === AcceptanceStatus.ACCEPTED_WITH_NOTES
    ).length;
    const rejectVotes = storyFeedback.filter(f => f.acceptanceVote === AcceptanceStatus.REJECTED).length;
    const deferVotes = storyFeedback.filter(f => f.acceptanceVote === AcceptanceStatus.DEFERRED).length;

    let decision: 'ACCEPTED' | 'REJECTED' | 'DEFERRED';
    let category: string;

    if (acceptVotes > rejectVotes && acceptVotes > deferVotes) {
      accepted.push(story.storyId);
      decision = 'ACCEPTED';
      category = 'ACCEPTANCE';
    } else if (rejectVotes >= acceptVotes) {
      rejected.push(story.storyId);
      decision = 'REJECTED';
      category = 'ACCEPTANCE';
    } else {
      deferred.push(story.storyId);
      decision = 'DEFERRED';
      category = 'ACCEPTANCE';
    }

    decisionsLog.push({
      timestamp: new Date(),
      decision: `Story ${story.storyId}: ${decision}`,
      category: 'ACCEPTANCE',
      rationale: `Accept votes: ${acceptVotes}, Reject votes: ${rejectVotes}, Defer votes: ${deferVotes}`,
      madeBy: 'Peter',
      supportedBy: storyFeedback.filter(f => f.acceptanceVote === AcceptanceStatus.ACCEPTED).map(f => f.stakeholder.name),
      opposedBy: storyFeedback.filter(f => f.acceptanceVote === AcceptanceStatus.REJECTED).map(f => f.stakeholder.name),
      finalDecision: decision
    });
  }

  return { accepted, rejected, deferred };
}

/**
 * Calculate sprint metrics
 */
function calculateSprintMetrics(
  plan: SprintPlan,
  completedStories: CompletedStory[],
  incompleteStories: string[],
  actualWorkData: ActualWorkData[]
): SprintMetrics {
  const completedStoryPoints = completedStories.reduce((sum, s) => sum + s.storyPoints, 0);
  const velocityAchieved = calculateVelocityAchievement(plan.totalStoryPoints, completedStoryPoints);

  const totalStoriesPlanned = plan.committedStories.length;
  const totalStoriesCompleted = completedStories.length;
  const totalStoriesCarriedOver = incompleteStories.length;
  const completionRate = calculateVelocityAchievement(totalStoriesPlanned, totalStoriesCompleted);

  const totalHoursSpent = actualWorkData.reduce((sum, w) => sum + w.actualHoursSpent, 0);
  const capacityUtilization = Math.round((totalHoursSpent / plan.totalCapacityHours) * 100);

  const acceptedStories = completedStories.length;
  const rejectedStories = 0; // Will be updated in validation
  const acceptanceRate = 100;

  const estimationErrors = completedStories.map(story => {
    const actualData = actualWorkData.find(w => w.storyId === story.storyId);
    if (!actualData) return 0;
    return calculateEstimationError(story.estimatedHours, actualData.actualHoursSpent);
  });
  const averageEstimationError = estimationErrors.length > 0
    ? Math.round(estimationErrors.reduce((sum, e) => sum + e, 0) / estimationErrors.length)
    : 0;
  const estimationTrend = determineEstimationTrend(averageEstimationError);

  return {
    sprintNumber: plan.sprintNumber,
    startDate: plan.startDate,
    endDate: plan.endDate,
    plannedStoryPoints: plan.totalStoryPoints,
    completedStoryPoints,
    velocityAchieved,
    totalStoriesPlanned,
    totalStoriesCompleted,
    totalStoriesCarriedOver,
    completionRate,
    totalCapacityHours: plan.totalCapacityHours,
    totalHoursSpent,
    capacityUtilization,
    acceptedStories,
    rejectedStories,
    acceptanceRate,
    averageEstimationError,
    estimationTrend
  };
}

/**
 * Analyze burndown chart
 */
function analyzeBurndown(
  plan: SprintPlan,
  completedStories: CompletedStory[],
  startDate: Date,
  endDate: Date
): BurndownAnalysis {
  const sprintDuration = plan.durationDays;
  const totalPoints = plan.totalStoryPoints;
  const idealBurnRate = totalPoints / sprintDuration;

  const dataPoints: BurndownPoint[] = [];
  let remainingPoints = totalPoints;

  for (let day = 0; day <= sprintDuration; day++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(currentDate.getDate() + day);

    const idealRemaining = Math.max(0, totalPoints - (idealBurnRate * day));
    const completedToday = day === sprintDuration
      ? completedStories.reduce((sum, s) => sum + s.storyPoints, 0)
      : Math.floor(Math.random() * 3); // Simulate daily completion

    remainingPoints = Math.max(0, remainingPoints - completedToday);

    dataPoints.push({
      day: day + 1,
      date: currentDate,
      remainingStoryPoints: remainingPoints,
      idealRemaining,
      completedToday
    });
  }

  const finalVariance = dataPoints[dataPoints.length - 1].remainingStoryPoints;
  const trend = analyzeBurndownTrend(finalVariance);
  const completedPoints = totalPoints - remainingPoints;
  const averageDailyVelocity = completedPoints / sprintDuration;

  return {
    sprintDuration,
    dataPoints,
    finalVariance,
    trend,
    criticalDays: [],
    averageDailyVelocity,
    projectedCompletion: endDate
  };
}

/**
 * Generate backlog updates based on feedback
 */
function generateBacklogUpdates(
  feedback: StakeholderFeedback[],
  rejectedStories: string[],
  decisionsLog: ReviewDecision[]
): BacklogUpdate[] {
  const updates: BacklogUpdate[] = [];

  // Re-prioritize rejected stories
  for (const storyId of rejectedStories) {
    updates.push({
      action: 'REPRIORITIZE',
      storyId,
      rationale: 'Story rejected in review, needs rework',
      requestedBy: 'Peter',
      impact: 'HIGH'
    });
  }

  // Add new stories from stakeholder suggestions
  const newStorySuggestions = feedback
    .flatMap(f => f.suggestions)
    .filter((s, i, arr) => arr.indexOf(s) === i); // Unique

  for (const suggestion of newStorySuggestions.slice(0, 2)) { // Limit to 2 new stories
    updates.push({
      action: 'ADD',
      newStory: {
        title: suggestion,
        description: `New feature request from sprint review`,
        priority: 'MEDIUM',
        estimatedStoryPoints: 3
      },
      rationale: 'Stakeholder feedback from sprint review',
      requestedBy: 'Stakeholders',
      impact: 'MEDIUM'
    });
  }

  return updates;
}

/**
 * Generate improvement suggestions
 */
function generateImprovementSuggestions(
  metrics: SprintMetrics,
  burndown: BurndownAnalysis,
  feedback: StakeholderFeedback[]
): string[] {
  const suggestions: string[] = [];

  if (metrics.velocityAchieved < 80) {
    suggestions.push('Improve sprint planning accuracy - velocity was below target');
  }

  if (metrics.estimationTrend === 'UNDER') {
    suggestions.push('Stories are consistently underestimated - add buffer to estimates');
  } else if (metrics.estimationTrend === 'OVER') {
    suggestions.push('Stories are consistently overestimated - refine estimation process');
  }

  if (metrics.capacityUtilization > 95) {
    suggestions.push('Team is at capacity limit - consider reducing sprint commitment');
  } else if (metrics.capacityUtilization < 70) {
    suggestions.push('Team has spare capacity - consider adding more stories');
  }

  if (burndown.trend === 'BEHIND_SCHEDULE') {
    suggestions.push('Burndown shows late delivery - break stories into smaller chunks');
  }

  const negativeCount = feedback.filter(f => f.sentiment === FeedbackSentiment.NEGATIVE).length;
  if (negativeCount > feedback.length * 0.3) {
    suggestions.push('Significant negative feedback - improve quality checks before demo');
  }

  return suggestions;
}

/**
 * Seek Product Owner approval
 */
function seekProductOwnerApproval(
  accepted: string[],
  rejected: string[],
  metrics: SprintMetrics,
  sentiment: FeedbackSentiment
): boolean {
  // Approve if:
  // - Most stories accepted (>70%)
  // - Velocity achieved >60%
  // - Sentiment not negative
  const acceptanceRate = accepted.length / (accepted.length + rejected.length);
  return acceptanceRate > 0.7 &&
         metrics.velocityAchieved > 60 &&
         sentiment !== FeedbackSentiment.NEGATIVE;
}

/**
 * Generate review notes
 */
function generateReviewNotes(
  metrics: SprintMetrics,
  sentiment: FeedbackSentiment,
  consensus: boolean
): string {
  return `Sprint review completed with ${metrics.velocityAchieved}% velocity achievement. ` +
    `Stakeholder sentiment: ${sentiment}. ` +
    `Consensus ${consensus ? 'reached' : 'not reached'}.`;
}

/**
 * Generate stakeholder comment based on sentiment
 */
function generateStakeholderComment(
  sentiment: FeedbackSentiment,
  criteriaMet: boolean
): string {
  if (sentiment === FeedbackSentiment.POSITIVE) {
    return 'Excellent work! All acceptance criteria met and demo was impressive.';
  } else if (sentiment === FeedbackSentiment.NEUTRAL) {
    return 'Good progress, though some minor improvements could be made.';
  } else {
    return 'Does not meet acceptance criteria. Needs rework before acceptance.';
  }
}

/**
 * Get default stakeholders (simulated)
 */
function getDefaultStakeholders(): Stakeholder[] {
  return [
    {
      name: 'Product Owner (Peter)',
      role: 'Product Owner',
      priority: 'HIGH',
      interests: ['business value', 'user experience', 'market fit']
    },
    {
      name: 'Technical Lead (Felix)',
      role: 'Technical Stakeholder',
      priority: 'HIGH',
      interests: ['architecture', 'scalability', 'technical debt']
    },
    {
      name: 'Quality Lead (Quinn)',
      role: 'Quality Stakeholder',
      priority: 'MEDIUM',
      interests: ['test coverage', 'quality metrics', 'bug count']
    }
  ];
}
