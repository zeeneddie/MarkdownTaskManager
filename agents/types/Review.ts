/**
 * Sprint Review Types for Scrum Ceremony Automation
 *
 * Defines types for sprint review, demo, stakeholder feedback, and acceptance
 */

import { SprintStatus } from './Sprint';

/**
 * Review status
 */
export enum ReviewStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/**
 * Acceptance status for completed work
 */
export enum AcceptanceStatus {
  ACCEPTED = 'accepted',              // Meets all criteria
  ACCEPTED_WITH_NOTES = 'accepted_with_notes',  // Accepted but minor improvements noted
  REJECTED = 'rejected',               // Does not meet criteria
  DEFERRED = 'deferred'                // Needs more discussion
}

/**
 * Stakeholder feedback sentiment
 */
export enum FeedbackSentiment {
  POSITIVE = 'positive',
  NEUTRAL = 'neutral',
  NEGATIVE = 'negative',
  MIXED = 'mixed'
}

/**
 * Completed story item for review
 */
export interface CompletedStory {
  storyId: string;
  title: string;
  description: string;
  storyPoints: number;
  assignedAgents: string[];
  acceptanceCriteria: string[];
  acceptanceCriteriaResults: CriteriaResult[];
  demoNotes: string;
  actualHoursSpent: number;
  estimatedHours: number;
  completionDate: Date;
}

/**
 * Acceptance criteria result
 */
export interface CriteriaResult {
  criterion: string;
  met: boolean;
  evidence: string;
  verifiedBy: string;              // Agent who verified
  verificationDate: Date;
}

/**
 * Stakeholder (simulated or real)
 */
export interface Stakeholder {
  name: string;
  role: string;                    // e.g., "Product Owner", "Customer Representative", "Business Analyst"
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  interests: string[];             // Areas of interest
}

/**
 * Stakeholder feedback on a story
 */
export interface StakeholderFeedback {
  stakeholder: Stakeholder;
  storyId: string;
  sentiment: FeedbackSentiment;
  comments: string;
  suggestions: string[];
  concerns: string[];
  acceptanceVote: AcceptanceStatus;
  timestamp: Date;
}

/**
 * Demo result for a story
 */
export interface DemoResult {
  storyId: string;
  demoGiven: boolean;
  demoGivenBy: string;             // Agent who presented
  demoDuration: number;            // Minutes
  visualAidsUsed: string[];        // Screenshots, diagrams, etc.
  questionsAsked: number;
  questionsAnswered: number;
  technicalIssues: string[];       // Any problems during demo
  audienceEngagement: 'HIGH' | 'MEDIUM' | 'LOW';
  overallSuccess: boolean;
}

/**
 * Sprint metrics from review
 */
export interface SprintMetrics {
  sprintNumber: number;
  startDate: Date;
  endDate: Date;

  // Velocity
  plannedStoryPoints: number;
  completedStoryPoints: number;
  velocityAchieved: number;        // Completed / Planned * 100

  // Stories
  totalStoriesPlanned: number;
  totalStoriesCompleted: number;
  totalStoriesCarriedOver: number;
  completionRate: number;          // Completed / Planned * 100

  // Capacity
  totalCapacityHours: number;
  totalHoursSpent: number;
  capacityUtilization: number;     // Hours Spent / Capacity * 100

  // Quality
  acceptedStories: number;
  rejectedStories: number;
  acceptanceRate: number;          // Accepted / Total * 100

  // Estimation accuracy
  averageEstimationError: number;  // Percentage difference between estimated and actual
  estimationTrend: 'OVER' | 'UNDER' | 'ACCURATE';
}

/**
 * Burndown data point
 */
export interface BurndownPoint {
  day: number;                     // Day of sprint (1-14)
  date: Date;
  remainingStoryPoints: number;
  idealRemaining: number;          // Ideal burndown line
  completedToday: number;
}

/**
 * Burndown analysis
 */
export interface BurndownAnalysis {
  sprintDuration: number;
  dataPoints: BurndownPoint[];
  finalVariance: number;           // Difference from ideal at end
  trend: 'AHEAD_OF_SCHEDULE' | 'ON_TRACK' | 'BEHIND_SCHEDULE';
  criticalDays: number[];          // Days with significant deviations
  averageDailyVelocity: number;
  projectedCompletion: Date;       // If trend continues
}

/**
 * Backlog update from review
 */
export interface BacklogUpdate {
  action: 'ADD' | 'MODIFY' | 'REMOVE' | 'REPRIORITIZE';
  storyId?: string;                // For existing stories
  newStory?: {                     // For new stories
    title: string;
    description: string;
    priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
    estimatedStoryPoints: number;
  };
  rationale: string;
  requestedBy: string;             // Stakeholder name
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
}

/**
 * Sprint review result
 */
export interface SprintReviewResult {
  reviewId: string;
  sprintId: string;
  sprintNumber: number;
  reviewDate: Date;
  reviewDuration: number;          // Minutes

  // Participants
  facilitator: string;             // Product Owner (Peter)
  devTeamPresent: string[];        // Agent names
  stakeholdersPresent: Stakeholder[];

  // Completed work
  completedStories: CompletedStory[];
  demoResults: DemoResult[];

  // Feedback
  stakeholderFeedback: StakeholderFeedback[];
  overallSentiment: FeedbackSentiment;

  // Acceptance
  acceptedStories: string[];       // Story IDs
  rejectedStories: string[];       // Story IDs
  deferredStories: string[];       // Story IDs

  // Metrics
  sprintMetrics: SprintMetrics;
  burndownAnalysis: BurndownAnalysis;

  // Backlog updates
  backlogUpdates: BacklogUpdate[];

  // Next sprint
  carryOverStories: string[];      // Story IDs
  suggestedImprovements: string[];

  // Metadata
  status: ReviewStatus;
  consensusReached: boolean;
  productOwnerApproval: boolean;
  notes: string;
}

/**
 * Sprint review session
 */
export interface SprintReviewSession {
  sessionId: string;
  sprintId: string;
  result: SprintReviewResult;
  decisionsLog: ReviewDecision[];
}

/**
 * Review decision record
 */
export interface ReviewDecision {
  timestamp: Date;
  decision: string;
  category: 'ACCEPTANCE' | 'BACKLOG' | 'PROCESS' | 'TECHNICAL';
  rationale: string;
  madeBy: string;                  // Stakeholder or agent name
  supportedBy: string[];
  opposedBy: string[];
  finalDecision: 'ACCEPTED' | 'REJECTED' | 'DEFERRED';
}

/**
 * Calculate velocity achievement percentage
 */
export function calculateVelocityAchievement(
  planned: number,
  completed: number
): number {
  if (planned === 0) return 0;
  return Math.round((completed / planned) * 100);
}

/**
 * Calculate acceptance rate
 */
export function calculateAcceptanceRate(
  accepted: number,
  total: number
): number {
  if (total === 0) return 0;
  return Math.round((accepted / total) * 100);
}

/**
 * Calculate estimation accuracy
 */
export function calculateEstimationError(
  estimated: number,
  actual: number
): number {
  if (estimated === 0) return 0;
  return Math.round(((actual - estimated) / estimated) * 100);
}

/**
 * Determine estimation trend
 */
export function determineEstimationTrend(
  averageError: number
): 'OVER' | 'UNDER' | 'ACCURATE' {
  if (averageError > 20) return 'UNDER';     // Underestimating (actual > estimated)
  if (averageError < -20) return 'OVER';     // Overestimating (actual < estimated)
  return 'ACCURATE';
}

/**
 * Analyze burndown trend
 */
export function analyzeBurndownTrend(
  finalVariance: number
): 'AHEAD_OF_SCHEDULE' | 'ON_TRACK' | 'BEHIND_SCHEDULE' {
  if (finalVariance < -10) return 'AHEAD_OF_SCHEDULE';  // Finished more than expected
  if (finalVariance > 10) return 'BEHIND_SCHEDULE';     // Finished less than expected
  return 'ON_TRACK';
}

/**
 * Calculate overall feedback sentiment
 */
export function calculateOverallSentiment(
  feedbacks: StakeholderFeedback[]
): FeedbackSentiment {
  if (feedbacks.length === 0) return FeedbackSentiment.NEUTRAL;

  const sentimentScores = {
    [FeedbackSentiment.POSITIVE]: 1,
    [FeedbackSentiment.NEUTRAL]: 0,
    [FeedbackSentiment.NEGATIVE]: -1,
    [FeedbackSentiment.MIXED]: 0
  };

  const totalScore = feedbacks.reduce(
    (sum, fb) => sum + sentimentScores[fb.sentiment],
    0
  );
  const averageScore = totalScore / feedbacks.length;

  if (averageScore > 0.5) return FeedbackSentiment.POSITIVE;
  if (averageScore < -0.5) return FeedbackSentiment.NEGATIVE;
  if (Math.abs(averageScore) < 0.2) return FeedbackSentiment.NEUTRAL;
  return FeedbackSentiment.MIXED;
}

/**
 * Check if story acceptance criteria are met
 */
export function areAcceptanceCriteriaMet(
  results: CriteriaResult[]
): boolean {
  return results.every(result => result.met);
}
