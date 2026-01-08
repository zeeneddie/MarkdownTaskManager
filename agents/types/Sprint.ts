/**
 * Sprint Types for Scrum Ceremony Automation
 *
 * Defines types for sprint planning, execution, and retrospective
 */

/**
 * Sprint status
 */
export enum SprintStatus {
  PLANNED = 'planned',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/**
 * Sprint goal
 */
export interface SprintGoal {
  description: string;
  businessValue: string;
  successCriteria: string[];
  measurableOutcomes: string[];
}

/**
 * Agent capacity for a sprint
 */
export interface AgentCapacity {
  agentName: string;
  availableHours: number;           // Total hours available
  allocatedHours: number;           // Hours allocated to stories
  remainingHours: number;           // Hours still available
  utilizationPercentage: number;    // Allocated / Available * 100
  assignedStories: string[];        // Story IDs assigned to this agent
}

/**
 * Story commitment for sprint
 */
export interface StoryCommitment {
  storyId: string;
  title: string;
  storyPoints: number;
  estimatedHours: number;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  assignedAgents: string[];         // Agent names
  dependencies: string[];           // Other story IDs
  acceptanceCriteria: string[];
  risks: string[];
}

/**
 * Sprint risk assessment
 */
export interface SprintRisk {
  id: string;
  category: 'CAPACITY' | 'TECHNICAL' | 'DEPENDENCY' | 'QUALITY' | 'SCOPE';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  impact: string;
  likelihood: number;               // 0.0 to 1.0
  mitigation: string;
  owner: string;                    // Agent responsible
}

/**
 * Velocity metrics
 */
export interface VelocityMetrics {
  lastSprintVelocity: number;       // Story points completed
  averageVelocity: number;          // Average over last 3-5 sprints
  trendDirection: 'UP' | 'DOWN' | 'STABLE';
  confidence: number;               // 0.0 to 1.0
  forecastedVelocity: number;       // Predicted for this sprint
}

/**
 * Sprint planning result
 */
export interface SprintPlan {
  sprintId: string;
  sprintNumber: number;
  sprintGoal: SprintGoal;
  startDate: Date;
  endDate: Date;
  durationDays: number;

  // Capacity
  totalCapacityHours: number;
  allocatedCapacityHours: number;
  capacityUtilization: number;      // Percentage
  agentCapacities: AgentCapacity[];

  // Stories
  committedStories: StoryCommitment[];
  totalStoryPoints: number;
  totalEstimatedHours: number;

  // Velocity
  velocityMetrics: VelocityMetrics;

  // Risks
  identifiedRisks: SprintRisk[];
  riskScore: number;                // 0.0 to 1.0 (aggregate)

  // Metadata
  createdBy: string;                // Planning facilitator (Paul)
  createdAt: Date;
  participants: string[];           // All agents
  status: SprintStatus;

  // Definition of Done
  definitionOfDone: string[];
}

/**
 * Backlog item for planning
 */
export interface BacklogItem {
  storyId: string;
  title: string;
  description: string;
  storyPoints: number;
  estimatedHours: number;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  businessValue: number;            // 1-10
  technicalComplexity: number;      // 1-10
  dependencies: string[];
  acceptanceCriteria: string[];
  requiredSkills: string[];         // Which agents needed
  blocked: boolean;
  blockerReason?: string;
}

/**
 * Sprint planning input
 */
export interface SprintPlanningInput {
  sprintNumber: number;
  sprintDuration: number;           // Days (typically 7-14)
  availableAgents: string[];        // Agent names
  agentAvailability: Record<string, number>; // Hours per agent
  backlog: BacklogItem[];
  previousVelocity?: VelocityMetrics;
  teamGoals?: string[];
}

/**
 * Sprint planning session
 */
export interface SprintPlanningSession {
  sessionId: string;
  input: SprintPlanningInput;
  plan: SprintPlan;
  planningDuration: number;         // Minutes
  decisionsLog: PlanningDecision[];
  consensusReached: boolean;
}

/**
 * Planning decision record
 */
export interface PlanningDecision {
  timestamp: Date;
  decision: string;
  rationale: string;
  proposedBy: string;               // Agent name
  supportedBy: string[];            // Agent names
  opposedBy: string[];              // Agent names
  finalDecision: 'ACCEPTED' | 'REJECTED' | 'DEFERRED';
}

/**
 * Calculate capacity utilization
 */
export function calculateCapacityUtilization(
  totalCapacity: number,
  allocatedCapacity: number
): number {
  if (totalCapacity === 0) return 0;
  return Math.round((allocatedCapacity / totalCapacity) * 100);
}

/**
 * Calculate sprint risk score
 */
export function calculateSprintRiskScore(risks: SprintRisk[]): number {
  if (risks.length === 0) return 0;

  const severityWeights = {
    'LOW': 0.25,
    'MEDIUM': 0.5,
    'HIGH': 0.75,
    'CRITICAL': 1.0
  };

  const totalRiskScore = risks.reduce((sum, risk) => {
    const severityWeight = severityWeights[risk.severity];
    return sum + (severityWeight * risk.likelihood);
  }, 0);

  // Normalize to 0-1 range
  return Math.min(1.0, totalRiskScore / risks.length);
}

/**
 * Check if story fits in sprint capacity
 */
export function canFitStory(
  story: BacklogItem,
  remainingCapacity: number,
  requiredAgents: AgentCapacity[]
): boolean {
  // Check if we have enough total capacity
  if (story.estimatedHours > remainingCapacity) {
    return false;
  }

  // Check if required agents have capacity
  for (const skill of story.requiredSkills) {
    const agent = requiredAgents.find(a => a.agentName === skill);
    if (!agent || agent.remainingHours < story.estimatedHours / story.requiredSkills.length) {
      return false;
    }
  }

  return true;
}

/**
 * Calculate velocity trend
 */
export function calculateVelocityTrend(
  velocities: number[]
): 'UP' | 'DOWN' | 'STABLE' {
  if (velocities.length < 2) return 'STABLE';

  const recent = velocities.slice(-3); // Last 3 sprints
  const average = recent.reduce((sum, v) => sum + v, 0) / recent.length;
  const latest = velocities[velocities.length - 1];

  const difference = ((latest - average) / average) * 100;

  if (difference > 10) return 'UP';
  if (difference < -10) return 'DOWN';
  return 'STABLE';
}
