/**
 * Peer Assistance System
 *
 * Implements agent-to-agent help during daily standups
 * Agents can provide tips, resources, take over tasks, or pair program
 */

import { Agent, Task } from 'kaibanjs';
import { agents } from '../configs/agents';
import {
  AssistanceType,
  AssistanceOffer,
  PeerAssistanceRequest,
  PeerAssistanceResponse,
  PeerAssistanceResult,
  AgentExpertise,
  AGENT_EXPERTISES,
  calculateRelevance,
  Resource
} from '../types/Assistance';
import { BlockingIssue, TaskStatus } from '../types/TaskStatus';

/**
 * Request peer assistance for a blocker
 */
export async function requestPeerAssistance(
  request: PeerAssistanceRequest,
  availableAgents: Agent[]
): Promise<PeerAssistanceResponse[]> {

  console.error('\n[PeerAssistance] 🤝 Requesting peer assistance');
  console.error(`[PeerAssistance] Requesting agent: ${request.requestingAgent}`);
  console.error(`[PeerAssistance] Work type: ${request.context.workType}`);
  console.error(`[PeerAssistance] Blocker: ${request.blockingIssue.reason}`);

  const responses: PeerAssistanceResponse[] = [];

  // Ask each agent if they can help
  for (const agent of availableAgents) {
    // Skip the requesting agent
    if (agent.name === request.requestingAgent) {
      continue;
    }

    const offer = await analyzeAndOfferHelp(agent, request);

    if (offer.canHelp && offer.confidence > 0.6) {
      console.error(`[PeerAssistance]   ✅ ${agent.name} can help (confidence: ${(offer.confidence * 100).toFixed(0)}%)`);
      console.error(`[PeerAssistance]      Type: ${offer.assistanceType}`);
      console.error(`[PeerAssistance]      Reason: ${offer.reason}`);

      responses.push({
        assistingAgent: agent.name,
        offer,
        timestamp: new Date(),
        accepted: false
      });
    } else {
      console.error(`[PeerAssistance]   ❌ ${agent.name} cannot help (confidence: ${(offer.confidence * 100).toFixed(0)}%)`);
    }
  }

  // Sort by confidence (highest first)
  responses.sort((a, b) => b.offer.confidence - a.offer.confidence);

  console.error(`[PeerAssistance] 📊 Found ${responses.length} agents willing to help`);

  return responses;
}

/**
 * Analyze blocker and offer help if capable
 */
async function analyzeAndOfferHelp(
  agent: Agent,
  request: PeerAssistanceRequest
): Promise<AssistanceOffer> {

  const expertise = AGENT_EXPERTISES[agent.name];

  if (!expertise) {
    return {
      canHelp: false,
      confidence: 0,
      assistanceType: AssistanceType.TIP,
      reason: 'No expertise data available',
      estimatedTimeMinutes: 0
    };
  }

  // Calculate relevance score
  const relevance = calculateRelevance(request.blockingIssue, expertise);

  if (relevance < 0.6) {
    return {
      canHelp: false,
      confidence: relevance,
      assistanceType: AssistanceType.TIP,
      reason: 'Outside my area of expertise',
      estimatedTimeMinutes: 0
    };
  }

  // Determine best assistance type based on expertise and blocker
  const assistanceType = determineAssistanceType(
    expertise,
    request.blockingIssue,
    request.context
  );

  // Generate specific suggestion
  const suggestion = await generateSuggestion(
    agent,
    request,
    assistanceType,
    expertise
  );

  // Find relevant resources
  const resources = await findRelevantResources(
    request.blockingIssue,
    expertise
  );

  return {
    canHelp: true,
    confidence: relevance,
    assistanceType,
    reason: `I specialize in ${expertise.specializations.join(', ')}`,
    estimatedTimeMinutes: estimateTimeRequired(assistanceType),
    suggestion,
    resources,
    conditions: generateConditions(assistanceType, request)
  };
}

/**
 * Determine best type of assistance
 */
function determineAssistanceType(
  expertise: AgentExpertise,
  blocker: BlockingIssue,
  context: any
): AssistanceType {

  // If agent has very high expertise in the area → TAKEOVER
  if (expertise.pastAssistance.successRate > 0.9 && blocker.attempts.length >= 3) {
    return AssistanceType.TAKEOVER;
  }

  // If complex problem needing collaboration → PAIR
  if (blocker.priority === 'CRITICAL' || blocker.description.toLowerCase().includes('complex')) {
    return AssistanceType.PAIR;
  }

  // If agent has specific resource/example → RESOURCE
  if (expertise.specializations.some(s => blocker.description.toLowerCase().includes(s))) {
    return AssistanceType.RESOURCE;
  }

  // Default → TIP
  return AssistanceType.TIP;
}

/**
 * Generate specific suggestion based on agent expertise
 */
async function generateSuggestion(
  agent: Agent,
  request: PeerAssistanceRequest,
  assistanceType: AssistanceType,
  expertise: AgentExpertise
): Promise<string> {

  const blocker = request.blockingIssue;
  const context = request.context;

  // Agent-specific suggestions based on their role
  switch (agent.name) {
    case 'Felix':
      if (blocker.description.toLowerCase().includes('oauth')) {
        return 'For mobile OAuth, use Authorization Code Flow with PKCE (RFC 7636) instead of implicit flow. This is more secure and works better with mobile apps.';
      }
      return 'Consider breaking down the architecture into smaller, independent components. Use SOLID principles and design patterns.';

    case 'Quinn':
      if (blocker.description.toLowerCase().includes('security')) {
        return 'Add input validation, sanitize user data, and implement rate limiting. Check OWASP Top 10 for common vulnerabilities.';
      }
      return 'Review code quality metrics: cyclomatic complexity, code coverage, and technical debt ratio. Set quality gates in CI/CD.';

    case 'Betty':
      if (blocker.lastError.includes('null') || blocker.lastError.includes('undefined')) {
        return 'Add null checks and use optional chaining (?.). Check initialization order and ensure dependencies are ready before use.';
      }
      return 'Add detailed logging at key points. Use debugger to step through execution. Check error stack trace for root cause.';

    case 'Tessa':
      return 'Write tests first (TDD). Start with happy path, then edge cases, then error scenarios. Aim for 80%+ coverage.';

    case 'Eliza':
      return 'Break down into smaller stories (< 8 SP). Use 3-point estimation (optimistic, realistic, pessimistic) for uncertainty.';

    case 'Marcus':
      return 'Refactor in small steps. Add tests before refactoring. Use IDE refactoring tools to minimize errors.';

    case 'Miguel':
      return 'Create migration plan with rollback strategy. Test with subset of data first. Keep old and new systems running in parallel.';

    case 'Diana':
      return 'Add clear examples and diagrams. Use simple language. Structure docs: Overview → Quick Start → Detailed Guide → API Reference.';

    case 'Peter':
      return 'Clarify acceptance criteria with stakeholders. Define "Definition of Done". Break epic into smaller, testable features.';

    case 'Paul':
      return 'Identify critical path and dependencies. Allocate resources based on priority. Build in buffer for unknowns (20-30%).';

    default:
      return 'Try a different approach. Review documentation and examples. Consider asking for more specific requirements.';
  }
}

/**
 * Find relevant resources
 */
async function findRelevantResources(
  blocker: BlockingIssue,
  expertise: AgentExpertise
): Promise<Resource[]> {

  const resources: Resource[] = [];

  // OAuth resources
  if (blocker.description.toLowerCase().includes('oauth')) {
    resources.push({
      type: 'SPECIFICATION',
      title: 'OAuth 2.0 with PKCE',
      content: 'RFC 7636: Proof Key for Code Exchange by OAuth Public Clients',
      url: 'https://datatracker.ietf.org/doc/html/rfc7636',
      relevance: 0.9
    });
    resources.push({
      type: 'CODE_EXAMPLE',
      title: 'OAuth PKCE Implementation Example',
      content: `
// Generate code verifier and challenge
const codeVerifier = generateRandomString(128);
const codeChallenge = base64URLEncode(sha256(codeVerifier));

// Authorization request
window.location = \`\${authEndpoint}?
  response_type=code&
  client_id=\${clientId}&
  redirect_uri=\${redirectUri}&
  code_challenge=\${codeChallenge}&
  code_challenge_method=S256\`;
      `,
      relevance: 0.85
    });
  }

  // Testing resources
  if (blocker.workType === 'TESTING' || blocker.description.toLowerCase().includes('test')) {
    resources.push({
      type: 'CODE_EXAMPLE',
      title: 'Test Structure Example',
      content: `
describe('Feature Name', () => {
  // Setup
  beforeEach(() => {
    // Initialize test data
  });

  it('should handle happy path', () => {
    // Arrange
    // Act
    // Assert
  });

  it('should handle edge case', () => {
    // Test boundary conditions
  });

  it('should handle errors gracefully', () => {
    // Test error scenarios
  });
});
      `,
      relevance: 0.8
    });
  }

  return resources.sort((a, b) => b.relevance - a.relevance);
}

/**
 * Generate conditions for assistance
 */
function generateConditions(
  assistanceType: AssistanceType,
  request: PeerAssistanceRequest
): string[] {

  const conditions: string[] = [];

  switch (assistanceType) {
    case AssistanceType.TAKEOVER:
      conditions.push('Original agent agrees to hand over task');
      conditions.push('Task context is fully documented');
      conditions.push('Stakeholders are notified of agent change');
      break;

    case AssistanceType.PAIR:
      conditions.push('Both agents available for 30-60 minutes');
      conditions.push('Clear communication channel established');
      conditions.push('Roles defined (navigator/driver)');
      break;

    case AssistanceType.RESOURCE:
      conditions.push('Agent reviews shared resources');
      conditions.push('Agent confirms understanding');
      break;

    case AssistanceType.TIP:
      conditions.push('Agent tries suggested approach');
      conditions.push('Agent reports back on outcome');
      break;
  }

  return conditions;
}

/**
 * Estimate time required for assistance
 */
function estimateTimeRequired(assistanceType: AssistanceType): number {
  switch (assistanceType) {
    case AssistanceType.TIP: return 5;
    case AssistanceType.RESOURCE: return 10;
    case AssistanceType.CONSULT: return 15;
    case AssistanceType.REVIEW: return 20;
    case AssistanceType.PAIR: return 60;
    case AssistanceType.TAKEOVER: return 120;
    default: return 10;
  }
}

/**
 * Execute peer assistance
 */
export async function executePeerAssistance(
  request: PeerAssistanceRequest,
  response: PeerAssistanceResponse
): Promise<PeerAssistanceResult> {

  console.error(`\n[PeerAssistance] 🚀 Executing peer assistance`);
  console.error(`[PeerAssistance] Assistant: ${response.assistingAgent}`);
  console.error(`[PeerAssistance] Type: ${response.offer.assistanceType}`);

  const startTime = Date.now();

  response.accepted = true;

  const lessonsLearned: string[] = [];

  switch (response.offer.assistanceType) {
    case AssistanceType.TIP:
      console.error(`[PeerAssistance] 💡 Providing tip...`);
      lessonsLearned.push(`Tip from ${response.assistingAgent}: ${response.offer.suggestion}`);
      break;

    case AssistanceType.RESOURCE:
      console.error(`[PeerAssistance] 📚 Sharing resources...`);
      response.offer.resources?.forEach(r => {
        lessonsLearned.push(`Resource: ${r.title}`);
      });
      break;

    case AssistanceType.TAKEOVER:
      console.error(`[PeerAssistance] 🔄 Taking over task...`);
      lessonsLearned.push(`Task reassigned from ${request.requestingAgent} to ${response.assistingAgent}`);
      break;

    case AssistanceType.PAIR:
      console.error(`[PeerAssistance] 👥 Starting pair programming...`);
      lessonsLearned.push(`Pair programming: ${request.requestingAgent} + ${response.assistingAgent}`);
      break;
  }

  const timeSpent = (Date.now() - startTime) / 1000;

  return {
    request,
    response,
    outcome: {
      status: 'HELPED',
      blockerResolved: false, // Will be determined after retry
      lessonsLearned,
      timeSpent
    }
  };
}

/**
 * Select best peer helper
 */
export function selectBestHelper(
  responses: PeerAssistanceResponse[]
): PeerAssistanceResponse | null {

  if (responses.length === 0) {
    return null;
  }

  // Already sorted by confidence in requestPeerAssistance
  // Return highest confidence offer
  return responses[0];
}

/**
 * Update agent expertise after assistance
 */
export function updateAgentExpertise(
  agentName: string,
  result: PeerAssistanceResult
): void {

  const expertise = AGENT_EXPERTISES[agentName];

  if (!expertise) return;

  expertise.pastAssistance.totalHelped++;

  if (result.outcome.blockerResolved) {
    const successRate = expertise.pastAssistance.successRate;
    const total = expertise.pastAssistance.totalHelped;

    // Update success rate (rolling average)
    expertise.pastAssistance.successRate =
      (successRate * (total - 1) + 1) / total;
  }

  // Update average confidence
  const avgConf = expertise.pastAssistance.averageConfidence;
  const total = expertise.pastAssistance.totalHelped;

  expertise.pastAssistance.averageConfidence =
    (avgConf * (total - 1) + result.response.offer.confidence) / total;
}
