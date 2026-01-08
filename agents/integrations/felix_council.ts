/**
 * Felix Council Integration
 *
 * Week 52: Integrates LLM Council multi-model decision making into Felix agent
 * for critical architecture decisions.
 */

import axios, { AxiosInstance } from 'axios';

// ============================================================================
// TYPES
// ============================================================================

export interface CouncilDecision {
    session_id: string;
    final_decision: string;
    confidence: number;
    consensus_level: number;
    dissenting_opinions: string[] | null;
    chairman_model: string;
}

export interface ArchitectureContext {
    requirements: string[];
    constraints: string[];
    current_stack: string[];
    complexity?: number;
    impact?: 'low' | 'medium' | 'high';
}

export interface QuickDecisionRequest {
    question: string;
    context: Record<string, any>;
    decision_type: 'architecture' | 'planning' | 'quality' | 'generation';
    agent_id: string;
    chairman_model?: string;
}

export interface QuickDecisionResponse {
    session_id: string;
    decision: CouncilDecision;
    consensus_level: number;
    response_count: number;
    review_count: number;
    message: string;
}

// ============================================================================
// LLM COUNCIL CLIENT
// ============================================================================

export class LLMCouncilClient {
    private client: AxiosInstance;

    constructor(apiBaseUrl: string = 'http://localhost:8000') {
        this.client = axios.create({
            baseURL: `${apiBaseUrl}/api/council`,
            timeout: 300000, // 5 minutes for full 3-stage process
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    /**
     * Quick decision: All 3 stages in one call.
     */
    async quickDecision(request: QuickDecisionRequest): Promise<QuickDecisionResponse> {
        try {
            const response = await this.client.post<QuickDecisionResponse>('/quick', request);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                throw new Error(
                    `Council API error: ${error.response?.data?.detail || error.message}`
                );
            }
            throw error;
        }
    }

    /**
     * Check council health (can we reach the API?).
     */
    async healthCheck(): Promise<boolean> {
        try {
            await this.client.get('/sessions?page_size=1');
            return true;
        } catch {
            return false;
        }
    }
}

// ============================================================================
// FELIX COUNCIL INTEGRATION
// ============================================================================

export class FelixCouncilIntegration {
    private council: LLMCouncilClient;
    private agentId: string = 'felix';

    // Council usage thresholds
    private readonly MIN_COMPLEXITY_FOR_COUNCIL = 7; // 1-10 scale
    private readonly ALWAYS_USE_FOR_HIGH_IMPACT = true;

    constructor(apiBaseUrl: string = 'http://localhost:8000') {
        this.council = new LLMCouncilClient(apiBaseUrl);
    }

    /**
     * Make architecture decision using council.
     */
    async makeArchitectureDecision(
        question: string,
        context: ArchitectureContext
    ): Promise<CouncilDecision> {
        console.log('🏛️ Felix: Consulting LLM Council for architecture decision...');

        const councilContext = {
            requirements: context.requirements,
            constraints: context.constraints,
            current_stack: context.current_stack,
            complexity_score: context.complexity || 0,
            impact_level: context.impact || 'medium'
        };

        try {
            const response = await this.council.quickDecision({
                question: question,
                context: councilContext,
                decision_type: 'architecture',
                agent_id: this.agentId,
                chairman_model: 'deepseek-r1:latest'
            });

            console.log(
                `✓ Council decision complete: ${response.consensus_level.toFixed(1)}% consensus ` +
                `(${response.response_count} models, ${response.review_count} reviews)`
            );

            return response.decision;

        } catch (error) {
            console.error('❌ Felix: Council decision failed:', error);
            throw new Error(`Council decision failed: ${error}`);
        }
    }

    /**
     * Determine if council should be used for this decision.
     */
    shouldUseCouncil(
        complexity: number,
        impact: 'low' | 'medium' | 'high'
    ): boolean {
        // High impact always uses council
        if (this.ALWAYS_USE_FOR_HIGH_IMPACT && impact === 'high') {
            return true;
        }

        // Medium impact with high complexity
        if (impact === 'medium' && complexity >= this.MIN_COMPLEXITY_FOR_COUNCIL) {
            return true;
        }

        // Low impact: Felix decides alone
        return false;
    }

    /**
     * Calculate decision complexity (1-10 scale).
     */
    calculateComplexity(context: ArchitectureContext): number {
        let complexity = 5; // Base complexity

        // More requirements = more complex
        if (context.requirements.length > 10) complexity += 2;
        else if (context.requirements.length > 5) complexity += 1;

        // More constraints = more complex
        if (context.constraints.length > 5) complexity += 2;
        else if (context.constraints.length > 2) complexity += 1;

        // Larger existing stack = more complex to integrate
        if (context.current_stack.length > 10) complexity += 1;

        return Math.min(complexity, 10); // Cap at 10
    }

    /**
     * Assess impact level of decision.
     */
    assessImpact(
        affectsCore: boolean,
        affectsMultipleServices: boolean,
        isReversible: boolean
    ): 'low' | 'medium' | 'high' {
        if (affectsCore && affectsMultipleServices) {
            return 'high';
        }

        if (affectsCore || affectsMultipleServices || !isReversible) {
            return 'medium';
        }

        return 'low';
    }

    /**
     * Check if council is available.
     */
    async isCouncilAvailable(): Promise<boolean> {
        return await this.council.healthCheck();
    }
}

// ============================================================================
// USAGE EXAMPLE IN FELIX AGENT
// ============================================================================

/**
 * Example: Felix proposes architecture using council for critical decisions.
 */
export async function felixProposeArchitecture(
    task: {
        description: string;
        requirements: string[];
        constraints: string[];
        affectsCore: boolean;
        affectsMultipleServices: boolean;
        isReversible: boolean;
    },
    currentStack: string[]
): Promise<{ architecture: string; confidence: number; method: 'council' | 'solo' }> {

    const felixCouncil = new FelixCouncilIntegration();

    // Calculate complexity and impact
    const context: ArchitectureContext = {
        requirements: task.requirements,
        constraints: task.constraints,
        current_stack: currentStack
    };

    const complexity = felixCouncil.calculateComplexity(context);
    const impact = felixCouncil.assessImpact(
        task.affectsCore,
        task.affectsMultipleServices,
        task.isReversible
    );

    context.complexity = complexity;
    context.impact = impact;

    // Decide if council is needed
    if (felixCouncil.shouldUseCouncil(complexity, impact)) {
        console.log(
            `🏛️ Felix: Critical decision (complexity=${complexity}, impact=${impact}) - Using LLM Council`
        );

        // Check if council is available
        const isAvailable = await felixCouncil.isCouncilAvailable();
        if (!isAvailable) {
            console.warn('⚠️ Felix: Council unavailable, falling back to solo decision');
            return felixSoloDecision(task);
        }

        // Use council for critical decision
        try {
            const councilDecision = await felixCouncil.makeArchitectureDecision(
                `What's the best architecture for: ${task.description}`,
                context
            );

            return {
                architecture: councilDecision.final_decision,
                confidence: councilDecision.confidence,
                method: 'council'
            };

        } catch (error) {
            console.error('❌ Felix: Council failed, falling back to solo decision');
            return felixSoloDecision(task);
        }

    } else {
        console.log(
            `🤖 Felix: Simple decision (complexity=${complexity}, impact=${impact}) - Solo decision`
        );

        return felixSoloDecision(task);
    }
}

/**
 * Felix makes decision alone (for simple cases).
 */
function felixSoloDecision(task: any): { architecture: string; confidence: number; method: 'solo' } {
    // Felix's solo decision logic (existing implementation)
    return {
        architecture: `Felix's solo architecture for: ${task.description}`,
        confidence: 0.75,
        method: 'solo'
    };
}

// ============================================================================
// EXPORTS
// ============================================================================

export default FelixCouncilIntegration;
