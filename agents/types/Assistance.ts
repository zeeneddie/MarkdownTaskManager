/**
 * Peer Assistance Types
 *
 * Defines how agents can help each other during daily standups
 * when blockers are encountered
 */

import { Agent } from 'kaibanjs';
import { BlockingIssue } from './TaskStatus';

export enum AssistanceType {
  TIP = 'TIP',                    // Give a suggestion/tip
  RESOURCE = 'RESOURCE',          // Share documentation, code examples
  TAKEOVER = 'TAKEOVER',          // Agent takes over the task
  PAIR = 'PAIR',                  // Work together on the task
  REVIEW = 'REVIEW',              // Review the work and give feedback
  CONSULT = 'CONSULT'             // Brief consultation/Q&A
}

export interface AssistanceOffer {
  canHelp: boolean;
  confidence: number;              // 0.0 to 1.0 - how confident agent can help
  assistanceType: AssistanceType;
  reason: string;                  // Why this agent can help
  estimatedTimeMinutes: number;    // How long will assistance take
  suggestion?: string;             // The actual tip/suggestion
  resources?: Resource[];          // Shared resources
  conditions?: string[];           // Preconditions for help
}

export interface Resource {
  type: 'DOCUMENTATION' | 'CODE_EXAMPLE' | 'TUTORIAL' | 'SPECIFICATION' | 'TOOL';
  title: string;
  content: string;
  url?: string;
  relevance: number;               // 0.0 to 1.0
}

export interface PeerAssistanceRequest {
  blockingIssue: BlockingIssue;
  requestingAgent: string;
  context: {
    workType: string;
    taskDescription: string;
    previousAttempts: number;
    errorMessages: string[];
    currentApproach: string;
  };
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface PeerAssistanceResponse {
  assistingAgent: string;
  offer: AssistanceOffer;
  timestamp: Date;
  accepted: boolean;
  executionPlan?: string;          // How the assistance will be provided
}

export interface PeerAssistanceResult {
  request: PeerAssistanceRequest;
  response: PeerAssistanceResponse;
  outcome: {
    status: 'HELPED' | 'PARTIAL' | 'NO_HELP' | 'TAKEOVER';
    blockerResolved: boolean;
    newAttemptSuccessful?: boolean;
    lessonsLearned: string[];
    timeSpent: number;
  };
}

/**
 * Agent Expertise Areas
 * Defines what each agent specializes in for peer assistance
 */
export interface AgentExpertise {
  agentName: string;
  specializations: string[];       // e.g., ['architecture', 'security', 'oauth']
  canHelpWith: {
    workTypes: string[];           // Which work types
    technologies: string[];        // Which tech stacks
    problemTypes: string[];        // Which problem categories
  };
  pastAssistance: {
    totalHelped: number;
    successRate: number;
    averageConfidence: number;
  };
}

export const AGENT_EXPERTISES: Record<string, AgentExpertise> = {
  'Felix': {
    agentName: 'Felix',
    specializations: ['architecture', 'system-design', 'api-design', 'microservices'],
    canHelpWith: {
      workTypes: ['NEW_FEATURE', 'ENHANCEMENT', 'MIGRATION'],
      technologies: ['rest', 'graphql', 'websocket', 'grpc'],
      problemTypes: ['design-patterns', 'scalability', 'architecture-decisions']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Quinn': {
    agentName: 'Quinn',
    specializations: ['quality', 'security', 'code-review', 'best-practices'],
    canHelpWith: {
      workTypes: ['QUALITY_AUDIT', 'QUALITY_IMPROVEMENT', 'NEW_FEATURE'],
      technologies: ['security', 'owasp', 'testing', 'ci-cd'],
      problemTypes: ['security-vulnerabilities', 'quality-issues', 'code-smells']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Betty': {
    agentName: 'Betty',
    specializations: ['debugging', 'troubleshooting', 'error-analysis', 'root-cause'],
    canHelpWith: {
      workTypes: ['BUG', 'QUALITY_IMPROVEMENT'],
      technologies: ['javascript', 'python', 'debugging-tools'],
      problemTypes: ['runtime-errors', 'logic-bugs', 'performance-issues']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Tessa': {
    agentName: 'Tessa',
    specializations: ['testing', 'test-automation', 'test-strategy', 'coverage'],
    canHelpWith: {
      workTypes: ['TESTING', 'NEW_FEATURE', 'BUG'],
      technologies: ['jest', 'pytest', 'playwright', 'cypress'],
      problemTypes: ['test-design', 'coverage-gaps', 'flaky-tests']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Eliza': {
    agentName: 'Eliza',
    specializations: ['estimation', 'effort-analysis', 'complexity-analysis'],
    canHelpWith: {
      workTypes: ['NEW_FEATURE', 'ENHANCEMENT', 'MIGRATION'],
      technologies: ['function-points', 'story-points', 'complexity-metrics'],
      problemTypes: ['estimation-uncertainty', 'scope-ambiguity']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Marcus': {
    agentName: 'Marcus',
    specializations: ['refactoring', 'tech-debt', 'code-quality', 'modernization'],
    canHelpWith: {
      workTypes: ['MAINTENANCE', 'QUALITY_IMPROVEMENT', 'MIGRATION'],
      technologies: ['refactoring', 'legacy-code', 'dependency-updates'],
      problemTypes: ['tech-debt', 'code-complexity', 'maintainability']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Miguel': {
    agentName: 'Miguel',
    specializations: ['migration', 'platform-upgrades', 'data-migration'],
    canHelpWith: {
      workTypes: ['MIGRATION'],
      technologies: ['database-migration', 'platform-migration', 'api-migration'],
      problemTypes: ['migration-strategy', 'backward-compatibility', 'data-integrity']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Diana': {
    agentName: 'Diana',
    specializations: ['documentation', 'technical-writing', 'clarity'],
    canHelpWith: {
      workTypes: ['NEW_FEATURE', 'MAINTENANCE', 'MIGRATION'],
      technologies: ['markdown', 'api-docs', 'user-guides'],
      problemTypes: ['unclear-requirements', 'documentation-gaps', 'communication']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Peter': {
    agentName: 'Peter',
    specializations: ['product-management', 'requirements', 'stakeholder-management'],
    canHelpWith: {
      workTypes: ['PROJECT_DEFINITION', 'NEW_FEATURE'],
      technologies: ['requirements-engineering', 'user-stories', 'acceptance-criteria'],
      problemTypes: ['requirement-ambiguity', 'scope-definition', 'priority-conflicts']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  },
  'Paul': {
    agentName: 'Paul',
    specializations: ['project-planning', 'resource-allocation', 'risk-management'],
    canHelpWith: {
      workTypes: ['PROJECT_DEFINITION'],
      technologies: ['project-management', 'agile', 'scrum'],
      problemTypes: ['resource-constraints', 'timeline-issues', 'dependency-management']
    },
    pastAssistance: { totalHelped: 0, successRate: 0, averageConfidence: 0 }
  }
};

/**
 * Calculate relevance of agent for a blocker
 */
export function calculateRelevance(
  blocker: BlockingIssue,
  expertise: AgentExpertise
): number {
  let score = 0;
  let factors = 0;

  // Work type match
  if (expertise.canHelpWith.workTypes.includes(blocker.workType)) {
    score += 0.4;
    factors++;
  }

  // Technology/keywords match
  const blockerText = `${blocker.description} ${blocker.reason} ${blocker.lastError}`.toLowerCase();
  const techMatches = expertise.canHelpWith.technologies.filter(tech =>
    blockerText.includes(tech.toLowerCase())
  ).length;

  if (techMatches > 0) {
    score += Math.min(0.3, techMatches * 0.1);
    factors++;
  }

  // Problem type match
  const problemMatches = expertise.canHelpWith.problemTypes.filter(problem =>
    blockerText.includes(problem.toLowerCase())
  ).length;

  if (problemMatches > 0) {
    score += Math.min(0.3, problemMatches * 0.15);
    factors++;
  }

  // Past success rate boost
  if (expertise.pastAssistance.successRate > 0.7) {
    score += 0.1;
  }

  return factors > 0 ? Math.min(1.0, score) : 0;
}
