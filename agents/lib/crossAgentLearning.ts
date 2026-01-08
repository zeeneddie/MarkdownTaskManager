/**
 * Cross-Agent Learning Module
 *
 * Week 25-26: AgentEvolver Integration - Cross-Agent Learning
 * Based on: github.com/zeeneddie/AgentEvolver
 *
 * Enables agents to learn from each other's experiences.
 *
 * Author: Claude Code (Week 25 Day 5)
 * Date: 2025-11-22
 */

import { AgentName, WorkType } from '../types/AgentTypes';

// ============================================================================
// TYPES
// ============================================================================

export interface SharedKnowledge {
  id: string;
  sourceAgent: AgentName;
  targetAgents: AgentName[];
  knowledgeType: 'pattern' | 'learning' | 'warning' | 'tip';
  content: string;
  context: string;
  relevanceScore: number;
  createdAt: Date;
  expiresAt?: Date;
}

export interface LearningExchange {
  id: string;
  requestingAgent: AgentName;
  providingAgent: AgentName;
  topic: string;
  knowledge: SharedKnowledge[];
  timestamp: Date;
  success: boolean;
}

export interface AgentProfile {
  agentId: AgentName;
  expertise: string[];
  strengths: string[];
  weaknesses: string[];
  recentPerformance: number;
  knowledgeContributions: number;
  knowledgeReceived: number;
}

// ============================================================================
// AGENT EXPERTISE MAPPING
// ============================================================================

const AGENT_EXPERTISE: Record<AgentName, string[]> = {
  Felix: ['architecture', 'design', 'api', 'microservices', 'system_design'],
  Marcus: ['maintenance', 'refactoring', 'tech_debt', 'dependencies'],
  Quinn: ['security', 'quality', 'auditing', 'vulnerabilities'],
  Betty: ['debugging', 'bugs', 'root_cause', 'error_handling'],
  Eliza: ['estimation', 'planning', 'complexity', 'effort'],
  Tessa: ['testing', 'coverage', 'automation', 'e2e'],
  Miguel: ['migration', 'upgrades', 'compatibility', 'data_migration'],
  Diana: ['documentation', 'api_docs', 'user_guides', 'writing'],
  Peter: ['requirements', 'user_stories', 'product', 'business'],
  Paul: ['planning', 'coordination', 'risk', 'resources']
};

// ============================================================================
// CROSS-AGENT LEARNING CLASS
// ============================================================================

export class CrossAgentLearning {
  private knowledgeBase: Map<string, SharedKnowledge> = new Map();
  private exchanges: LearningExchange[] = [];
  private agentProfiles: Map<AgentName, AgentProfile> = new Map();

  constructor() {
    this.initializeProfiles();
  }

  private initializeProfiles(): void {
    const agents: AgentName[] = Object.keys(AGENT_EXPERTISE) as AgentName[];

    for (const agent of agents) {
      this.agentProfiles.set(agent, {
        agentId: agent,
        expertise: AGENT_EXPERTISE[agent],
        strengths: [],
        weaknesses: [],
        recentPerformance: 0.7,
        knowledgeContributions: 0,
        knowledgeReceived: 0
      });
    }
  }

  // -------------------------------------------------------------------------
  // KNOWLEDGE SHARING
  // -------------------------------------------------------------------------

  /**
   * Share knowledge from one agent to others.
   */
  shareKnowledge(
    sourceAgent: AgentName,
    targetAgents: AgentName[],
    knowledgeType: SharedKnowledge['knowledgeType'],
    content: string,
    context: string
  ): SharedKnowledge {
    const knowledge: SharedKnowledge = {
      id: this.generateId(),
      sourceAgent,
      targetAgents,
      knowledgeType,
      content,
      context,
      relevanceScore: this.calculateRelevance(sourceAgent, targetAgents[0], content),
      createdAt: new Date()
    };

    this.knowledgeBase.set(knowledge.id, knowledge);

    // Update profiles
    const profile = this.agentProfiles.get(sourceAgent);
    if (profile) {
      profile.knowledgeContributions++;
    }

    for (const target of targetAgents) {
      const targetProfile = this.agentProfiles.get(target);
      if (targetProfile) {
        targetProfile.knowledgeReceived++;
      }
    }

    return knowledge;
  }

  /**
   * Request knowledge from another agent.
   */
  requestKnowledge(
    requestingAgent: AgentName,
    topic: string,
    preferredSource?: AgentName
  ): SharedKnowledge[] {
    // Find relevant knowledge
    const relevant: SharedKnowledge[] = [];

    for (const knowledge of this.knowledgeBase.values()) {
      // Check if topic is relevant
      const topicMatch = this.isTopicMatch(knowledge.content, topic) ||
                         this.isTopicMatch(knowledge.context, topic);

      if (!topicMatch) continue;

      // Check if requesting agent is a target or no specific targets
      if (knowledge.targetAgents.length === 0 ||
          knowledge.targetAgents.includes(requestingAgent)) {

        // Prefer knowledge from preferred source
        if (preferredSource && knowledge.sourceAgent !== preferredSource) {
          knowledge.relevanceScore *= 0.8;
        }

        relevant.push(knowledge);
      }
    }

    // Sort by relevance
    relevant.sort((a, b) => b.relevanceScore - a.relevanceScore);

    // Record the exchange
    if (relevant.length > 0) {
      const exchange: LearningExchange = {
        id: this.generateId(),
        requestingAgent,
        providingAgent: relevant[0].sourceAgent,
        topic,
        knowledge: relevant.slice(0, 5),
        timestamp: new Date(),
        success: true
      };
      this.exchanges.push(exchange);
    }

    return relevant.slice(0, 5);
  }

  // -------------------------------------------------------------------------
  // EXPERT FINDING
  // -------------------------------------------------------------------------

  /**
   * Find the best agent to ask about a topic.
   */
  findExpert(topic: string, excludeAgent?: AgentName): AgentName | null {
    const topicWords = topic.toLowerCase().split(/\s+/);
    let bestAgent: AgentName | null = null;
    let bestScore = 0;

    for (const [agent, profile] of this.agentProfiles) {
      if (agent === excludeAgent) continue;

      // Calculate expertise match
      let score = 0;
      for (const word of topicWords) {
        for (const expertise of profile.expertise) {
          if (expertise.includes(word) || word.includes(expertise)) {
            score++;
          }
        }
      }

      // Factor in performance
      score *= profile.recentPerformance;

      // Factor in knowledge contributions
      score += profile.knowledgeContributions * 0.1;

      if (score > bestScore) {
        bestScore = score;
        bestAgent = agent;
      }
    }

    return bestAgent;
  }

  /**
   * Get agents with complementary expertise.
   */
  findComplementaryAgents(agent: AgentName): AgentName[] {
    const agentExpertise = new Set(AGENT_EXPERTISE[agent] || []);
    const complementary: Array<{ agent: AgentName; overlap: number }> = [];

    for (const [otherAgent, expertise] of Object.entries(AGENT_EXPERTISE)) {
      if (otherAgent === agent) continue;

      const otherExpertise = new Set(expertise);
      const overlap = [...agentExpertise].filter(e => otherExpertise.has(e)).length;

      // Low overlap = complementary
      if (overlap < 2) {
        complementary.push({
          agent: otherAgent as AgentName,
          overlap
        });
      }
    }

    // Sort by least overlap (most complementary)
    complementary.sort((a, b) => a.overlap - b.overlap);

    return complementary.map(c => c.agent);
  }

  // -------------------------------------------------------------------------
  // LEARNING PROPAGATION
  // -------------------------------------------------------------------------

  /**
   * Propagate a learning to all relevant agents.
   */
  propagateLearning(
    sourceAgent: AgentName,
    learning: string,
    context: string,
    workType?: WorkType
  ): AgentName[] {
    const recipients: AgentName[] = [];

    for (const [agent, profile] of this.agentProfiles) {
      if (agent === sourceAgent) continue;

      // Check if learning is relevant to this agent
      const relevance = this.calculateRelevance(sourceAgent, agent, learning);

      if (relevance > 0.4) {
        // Share the knowledge
        this.shareKnowledge(
          sourceAgent,
          [agent],
          'learning',
          learning,
          context
        );
        recipients.push(agent);
      }
    }

    return recipients;
  }

  // -------------------------------------------------------------------------
  // COLLABORATION SUGGESTIONS
  // -------------------------------------------------------------------------

  /**
   * Suggest agents to collaborate with on a task.
   */
  suggestCollaborators(
    primaryAgent: AgentName,
    taskDescription: string,
    maxSuggestions: number = 3
  ): Array<{ agent: AgentName; reason: string; score: number }> {
    const suggestions: Array<{ agent: AgentName; reason: string; score: number }> = [];
    const taskWords = taskDescription.toLowerCase().split(/\s+/);

    for (const [agent, profile] of this.agentProfiles) {
      if (agent === primaryAgent) continue;

      // Calculate relevance to task
      let score = 0;
      const matchedExpertise: string[] = [];

      for (const word of taskWords) {
        for (const expertise of profile.expertise) {
          if (expertise.includes(word) || word.includes(expertise)) {
            score++;
            if (!matchedExpertise.includes(expertise)) {
              matchedExpertise.push(expertise);
            }
          }
        }
      }

      if (score > 0) {
        // Factor in performance and contributions
        score *= profile.recentPerformance;
        score += profile.knowledgeContributions * 0.05;

        suggestions.push({
          agent,
          reason: `Expert in: ${matchedExpertise.join(', ')}`,
          score
        });
      }
    }

    // Sort by score and return top suggestions
    suggestions.sort((a, b) => b.score - a.score);
    return suggestions.slice(0, maxSuggestions);
  }

  // -------------------------------------------------------------------------
  // STATISTICS
  // -------------------------------------------------------------------------

  getStatistics(): {
    totalKnowledge: number;
    totalExchanges: number;
    topContributors: Array<{ agent: AgentName; contributions: number }>;
    topReceivers: Array<{ agent: AgentName; received: number }>;
  } {
    const contributors = [...this.agentProfiles.values()]
      .map(p => ({ agent: p.agentId, contributions: p.knowledgeContributions }))
      .sort((a, b) => b.contributions - a.contributions);

    const receivers = [...this.agentProfiles.values()]
      .map(p => ({ agent: p.agentId, received: p.knowledgeReceived }))
      .sort((a, b) => b.received - a.received);

    return {
      totalKnowledge: this.knowledgeBase.size,
      totalExchanges: this.exchanges.length,
      topContributors: contributors.slice(0, 5),
      topReceivers: receivers.slice(0, 5)
    };
  }

  getAgentProfile(agent: AgentName): AgentProfile | undefined {
    return this.agentProfiles.get(agent);
  }

  getRecentExchanges(limit: number = 10): LearningExchange[] {
    return this.exchanges.slice(-limit);
  }

  // -------------------------------------------------------------------------
  // HELPERS
  // -------------------------------------------------------------------------

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private calculateRelevance(
    sourceAgent: AgentName,
    targetAgent: AgentName,
    content: string
  ): number {
    const sourceExpertise = new Set(AGENT_EXPERTISE[sourceAgent] || []);
    const targetExpertise = new Set(AGENT_EXPERTISE[targetAgent] || []);
    const contentWords = content.toLowerCase().split(/\s+/);

    // Check content overlap with target expertise
    let overlap = 0;
    for (const word of contentWords) {
      for (const expertise of targetExpertise) {
        if (expertise.includes(word) || word.includes(expertise)) {
          overlap++;
        }
      }
    }

    // Normalize to 0-1
    const relevance = Math.min(1, overlap / 5);
    return relevance;
  }

  private isTopicMatch(text: string, topic: string): boolean {
    const textLower = text.toLowerCase();
    const topicLower = topic.toLowerCase();
    const topicWords = topicLower.split(/\s+/);

    // Direct match
    if (textLower.includes(topicLower)) return true;

    // Word match
    let matches = 0;
    for (const word of topicWords) {
      if (textLower.includes(word)) matches++;
    }

    return matches >= topicWords.length * 0.5;
  }
}

// ============================================================================
// SINGLETON EXPORT
// ============================================================================

let crossAgentLearningInstance: CrossAgentLearning | null = null;

export function getCrossAgentLearning(): CrossAgentLearning {
  if (!crossAgentLearningInstance) {
    crossAgentLearningInstance = new CrossAgentLearning();
  }
  return crossAgentLearningInstance;
}

export default CrossAgentLearning;
