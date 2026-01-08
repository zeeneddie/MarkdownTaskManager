/**
 * Sprint Retrospective Types for Scrum Ceremony Automation
 *
 * Defines types for sprint retrospective, team reflection, and continuous improvement
 */

/**
 * Retrospective status
 */
export enum RetrospectiveStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/**
 * Feedback category
 */
export enum FeedbackCategory {
  WHAT_WENT_WELL = 'what_went_well',
  WHAT_DIDNT_GO_WELL = 'what_didnt_go_well',
  WHAT_TO_IMPROVE = 'what_to_improve',
  APPRECIATION = 'appreciation'
}

/**
 * Action item priority
 */
export enum ActionItemPriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

/**
 * Action item status
 */
export enum ActionItemStatus {
  PROPOSED = 'proposed',
  ACCEPTED = 'accepted',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/**
 * Team health metric type
 */
export enum HealthMetricType {
  COMMUNICATION = 'communication',
  COLLABORATION = 'collaboration',
  MORALE = 'morale',
  WORKLOAD = 'workload',
  TECHNICAL_DEBT = 'technical_debt',
  PROCESS_EFFICIENCY = 'process_efficiency',
  QUALITY = 'quality',
  LEARNING = 'learning'
}

/**
 * Retrospective feedback item
 */
export interface RetrospectiveFeedback {
  id: string;
  category: FeedbackCategory;
  description: string;
  submittedBy: string;              // Agent name
  votes: number;                    // How many agents agree
  votedBy: string[];                // Agent names
  relatedTo?: string;               // Related sprint story/task
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  timestamp: Date;
}

/**
 * Action item from retrospective
 */
export interface ActionItem {
  id: string;
  title: string;
  description: string;
  category: 'PROCESS' | 'TECHNICAL' | 'TEAM' | 'TOOLING' | 'LEARNING';
  priority: ActionItemPriority;
  status: ActionItemStatus;
  owner: string;                    // Agent responsible
  dueDate?: Date;
  estimatedEffort: number;          // Hours
  expectedImpact: string;
  successCriteria: string[];
  createdFrom: string;              // Feedback ID that generated this
  createdAt: Date;
  completedAt?: Date;
}

/**
 * Team health metric
 */
export interface TeamHealthMetric {
  type: HealthMetricType;
  score: number;                    // 1-10 scale
  trend: 'IMPROVING' | 'STABLE' | 'DECLINING';
  previousScore?: number;
  feedback: string[];               // Comments from agents
  concerns: string[];
  strengths: string[];
}

/**
 * Process improvement suggestion
 */
export interface ProcessImprovement {
  id: string;
  title: string;
  description: string;
  currentProcess: string;
  proposedChange: string;
  expectedBenefit: string;
  estimatedEffort: 'LOW' | 'MEDIUM' | 'HIGH';
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  proposedBy: string;               // Agent name
  supportedBy: string[];            // Agent names
  opposedBy: string[];              // Agent names
  vote: 'ACCEPTED' | 'REJECTED' | 'DEFERRED';
  implementation?: ActionItem;
}

/**
 * Agent expertise update
 */
export interface AgentExpertiseUpdate {
  agentName: string;
  previousExpertise: string[];
  newSkillsAcquired: string[];
  skillsImproved: string[];
  areasNeedingImprovement: string[];
  confidenceLevels: Record<string, number>; // Skill -> 0-1 confidence
  learningGoals: string[];
  mentorshipOffered: string[];      // Skills they can teach
  mentorshipNeeded: string[];       // Skills they want to learn
}

/**
 * Sprint learning outcome
 */
export interface LearningOutcome {
  id: string;
  category: 'TECHNICAL' | 'PROCESS' | 'DOMAIN' | 'TEAM';
  title: string;
  description: string;
  learnedBy: string[];              // Agent names
  source: string;                   // How it was learned (e.g., "Peer assistance from Felix")
  applicability: 'HIGH' | 'MEDIUM' | 'LOW';
  documented: boolean;
  documentationLink?: string;
}

/**
 * Celebration item (wins and achievements)
 */
export interface Celebration {
  id: string;
  title: string;
  description: string;
  type: 'MILESTONE' | 'ACHIEVEMENT' | 'INNOVATION' | 'COLLABORATION' | 'QUALITY';
  involvedAgents: string[];
  impact: string;
  celebratedBy: string[];           // Agent names who want to celebrate
  timestamp: Date;
}

/**
 * Sprint Retrospective Result
 */
export interface SprintRetrospectiveResult {
  retrospectiveId: string;
  sprintId: string;
  sprintNumber: number;
  retrospectiveDate: Date;
  retrospectiveDuration: number;    // Minutes

  // Participants
  facilitator: string;              // Scrum Master (Paul)
  participants: string[];           // All agent names

  // Feedback
  whatWentWell: RetrospectiveFeedback[];
  whatDidntGoWell: RetrospectiveFeedback[];
  improvements: RetrospectiveFeedback[];
  appreciations: RetrospectiveFeedback[];

  // Action items
  actionItems: ActionItem[];
  actionItemsFromPreviousRetro: ActionItem[];
  actionItemsCompleted: number;
  actionItemsCompletionRate: number;

  // Team health
  teamHealthMetrics: TeamHealthMetric[];
  overallTeamHealthScore: number;  // 1-10
  teamHealthTrend: 'IMPROVING' | 'STABLE' | 'DECLINING';

  // Process improvements
  processImprovements: ProcessImprovement[];
  acceptedImprovements: number;

  // Learning
  learningOutcomes: LearningOutcome[];
  agentExpertiseUpdates: AgentExpertiseUpdate[];

  // Celebrations
  celebrations: Celebration[];

  // Metadata
  status: RetrospectiveStatus;
  consensusReached: boolean;
  keyTakeaways: string[];
  nextRetroFocus: string[];
  notes: string;
}

/**
 * Sprint Retrospective Session
 */
export interface SprintRetrospectiveSession {
  sessionId: string;
  sprintId: string;
  result: SprintRetrospectiveResult;
  decisionsLog: RetrospectiveDecision[];
}

/**
 * Retrospective decision record
 */
export interface RetrospectiveDecision {
  timestamp: Date;
  decision: string;
  category: 'ACTION_ITEM' | 'PROCESS_CHANGE' | 'HEALTH' | 'LEARNING';
  rationale: string;
  proposedBy: string;               // Agent name
  supportedBy: string[];            // Agent names
  opposedBy: string[];              // Agent names
  finalDecision: 'ACCEPTED' | 'REJECTED' | 'DEFERRED';
}

/**
 * Retrospective input
 */
export interface RetrospectiveInput {
  sprintNumber: number;
  sprintId: string;
  sprintMetrics: any;               // From Sprint Review
  previousActionItems?: ActionItem[];
  previousTeamHealth?: TeamHealthMetric[];
  sprintStartDate: Date;
  sprintEndDate: Date;
}

/**
 * Calculate action item completion rate
 */
export function calculateActionItemCompletionRate(
  completedItems: number,
  totalItems: number
): number {
  if (totalItems === 0) return 100;
  return Math.round((completedItems / totalItems) * 100);
}

/**
 * Calculate overall team health score
 */
export function calculateOverallTeamHealth(
  metrics: TeamHealthMetric[]
): number {
  if (metrics.length === 0) return 5; // Neutral

  const totalScore = metrics.reduce((sum, m) => sum + m.score, 0);
  return Math.round((totalScore / metrics.length) * 10) / 10; // Round to 1 decimal
}

/**
 * Determine team health trend
 */
export function determineTeamHealthTrend(
  currentScore: number,
  metrics: TeamHealthMetric[]
): 'IMPROVING' | 'STABLE' | 'DECLINING' {
  const trendsUp = metrics.filter(m => m.trend === 'IMPROVING').length;
  const trendsDown = metrics.filter(m => m.trend === 'DECLINING').length;

  if (trendsUp > trendsDown && trendsUp > metrics.length * 0.5) {
    return 'IMPROVING';
  } else if (trendsDown > trendsUp && trendsDown > metrics.length * 0.5) {
    return 'DECLINING';
  }
  return 'STABLE';
}

/**
 * Prioritize feedback items by votes
 */
export function prioritizeFeedback(
  feedback: RetrospectiveFeedback[]
): RetrospectiveFeedback[] {
  return [...feedback].sort((a, b) => {
    // Sort by votes (descending), then by impact
    if (b.votes !== a.votes) {
      return b.votes - a.votes;
    }
    const impactWeight = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
    return impactWeight[b.impact] - impactWeight[a.impact];
  });
}

/**
 * Calculate trend for health metric
 */
export function calculateHealthTrend(
  currentScore: number,
  previousScore?: number
): 'IMPROVING' | 'STABLE' | 'DECLINING' {
  if (!previousScore) return 'STABLE';

  const difference = currentScore - previousScore;
  if (difference > 1) return 'IMPROVING';
  if (difference < -1) return 'DECLINING';
  return 'STABLE';
}

/**
 * Generate action item from feedback
 */
export function generateActionItemFromFeedback(
  feedback: RetrospectiveFeedback,
  owner: string
): ActionItem {
  return {
    id: `action-${Date.now()}`,
    title: `Improve: ${feedback.description.substring(0, 50)}...`,
    description: feedback.description,
    category: 'PROCESS',
    priority: feedback.impact === 'HIGH'
      ? ActionItemPriority.HIGH
      : feedback.impact === 'MEDIUM'
      ? ActionItemPriority.MEDIUM
      : ActionItemPriority.LOW,
    status: ActionItemStatus.PROPOSED,
    owner,
    estimatedEffort: feedback.impact === 'HIGH' ? 8 : feedback.impact === 'MEDIUM' ? 4 : 2,
    expectedImpact: `Address issue: ${feedback.description}`,
    successCriteria: ['Issue resolved', 'Team agrees improvement is effective'],
    createdFrom: feedback.id,
    createdAt: new Date()
  };
}
