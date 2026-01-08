/**
 * LLM Council Multi-Model Decision Making Types
 *
 * Week 52: Supports 3-stage consensus process
 * - Stage 1: Response (query all models in parallel)
 * - Stage 2: Peer Review (blind review of responses)
 * - Stage 3: Synthesis (chairman creates final decision)
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum SessionStatus {
    PENDING = 'pending',
    REVIEWING = 'reviewing',
    COMPLETE = 'complete'
}

export enum DecisionType {
    ARCHITECTURE = 'architecture',
    PLANNING = 'planning',
    QUALITY = 'quality',
    GENERATION = 'generation'
}

// ============================================================================
// CORE INTERFACES
// ============================================================================

export interface CouncilSession {
    id: string;
    question: string;
    context: Record<string, any>;
    decision_type: DecisionType;
    agent_id: string;
    status: SessionStatus;
    created_at: Date;
    completed_at?: Date;
    // Relationships (populated via eager loading)
    responses?: CouncilResponse[];
    reviews?: CouncilReview[];
    decision?: CouncilDecision;
}

export interface CouncilResponse {
    id: string;
    session_id: string;
    model_name: string;
    response_text: string;
    confidence: number;  // 0.0-1.0
    reasoning?: string;
    created_at: Date;
    // Relationships
    reviews_received?: CouncilReview[];
}

export interface CouncilReview {
    id: string;
    session_id: string;
    reviewer_model: string;
    reviewed_response_id: string;
    accuracy_score: number;      // 0-10
    completeness_score: number;  // 0-10
    clarity_score: number;       // 0-10
    feasibility_score: number;   // 0-10
    comments?: string;
    created_at: Date;
}

export interface CouncilDecision {
    id: string;
    session_id: string;
    chairman_model: string;
    final_decision: string;
    confidence: number;  // 0.0-1.0
    consensus_level: number;  // 0-100% agreement
    dissenting_opinions?: string[];
    synthesis_reasoning?: string;
    created_at: Date;
}

// ============================================================================
// API REQUEST/RESPONSE INTERFACES
// ============================================================================

export interface CreateSessionRequest {
    question: string;
    context: Record<string, any>;
    decision_type: DecisionType;
    agent_id: string;
}

export interface CreateSessionResponse {
    session: CouncilSession;
    message: string;
}

export interface QuickDecisionRequest {
    question: string;
    context: Record<string, any>;
    decision_type: DecisionType;
    agent_id: string;
    wait_for_completion?: boolean;  // Default: true
}

export interface QuickDecisionResponse {
    session: CouncilSession;
    decision?: CouncilDecision;  // Only if wait_for_completion=true
    message: string;
}

export interface SessionListResponse {
    sessions: CouncilSession[];
    total: number;
    page: number;
    page_size: number;
}

export interface SessionDetailResponse {
    session: CouncilSession;
    responses: CouncilResponse[];
    reviews: CouncilReview[];
    decision?: CouncilDecision;
    consensus_metrics: ConsensusMetrics;
}

export interface ConsensusMetrics {
    total_responses: number;
    average_confidence: number;
    confidence_std_dev: number;
    consensus_level: number;  // 0-100%
    has_outliers: boolean;
    outlier_responses?: string[];  // response IDs
    review_scores: {
        average_accuracy: number;
        average_completeness: number;
        average_clarity: number;
        average_feasibility: number;
        overall_average: number;
    };
}

// ============================================================================
// CONFIGURATION INTERFACES
// ============================================================================

export interface CouncilModelConfig {
    model: string;
    weight: number;
    role: string;
    specialty?: string;
}

export interface CouncilModelsConfig {
    chairman: {
        model: string;  // "deepseek-r1:latest"
        weight: number; // 2.0
        role: string;   // "chairman"
    };
    council: CouncilModelConfig[];
}

export const DEFAULT_MODELS_CONFIG: CouncilModelsConfig = {
    chairman: {
        model: 'deepseek-r1:latest',
        weight: 2.0,
        role: 'chairman'
    },
    council: [
        {
            model: 'qwen2.5-coder:7b',
            weight: 1.5,
            role: 'technical',
            specialty: 'code architecture & design patterns'
        },
        {
            model: 'codellama:latest',
            weight: 1.5,
            role: 'implementation',
            specialty: 'code implementation & debugging'
        },
        {
            model: 'mistral:latest',
            weight: 1.0,
            role: 'documentation',
            specialty: 'technical writing & clarity'
        },
        {
            model: 'qwen2.5:7b',
            weight: 1.0,
            role: 'planning',
            specialty: 'project planning & estimation'
        },
        {
            model: 'llama3.2:latest',
            weight: 1.0,
            role: 'quality',
            specialty: 'quality assurance & testing'
        }
    ]
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Calculate consensus level from responses
 *
 * Uses weighted voting based on model weights and confidence scores.
 * Returns percentage (0-100) of agreement among models.
 */
export function calculateConsensus(
    responses: CouncilResponse[],
    modelsConfig: CouncilModelsConfig
): number {
    if (responses.length === 0) return 0;

    // Extract key recommendations from each response
    const recommendations = responses.map(r =>
        extractRecommendation(r.response_text)
    );

    // Calculate similarity between all pairs
    let totalWeight = 0;
    let agreementWeight = 0;

    for (let i = 0; i < responses.length; i++) {
        for (let j = i + 1; j < responses.length; j++) {
            const model1 = responses[i].model_name;
            const model2 = responses[j].model_name;

            const weight1 = getModelWeight(model1, modelsConfig);
            const weight2 = getModelWeight(model2, modelsConfig);
            const pairWeight = (weight1 + weight2) / 2;

            totalWeight += pairWeight;

            // Check if recommendations are similar
            const similarity = calculateTextSimilarity(
                recommendations[i],
                recommendations[j]
            );

            if (similarity > 0.7) {  // 70% similarity threshold
                agreementWeight += pairWeight;
            }
        }
    }

    return totalWeight > 0 ? (agreementWeight / totalWeight) * 100 : 0;
}

/**
 * Detect outlier responses that significantly differ from consensus
 *
 * Returns IDs of responses that are >2 standard deviations from mean confidence
 * or have recommendation text that differs significantly from others.
 */
export function detectOutliers(
    responses: CouncilResponse[]
): string[] {
    if (responses.length < 3) return [];  // Need at least 3 for outlier detection

    const outliers: string[] = [];

    // 1. Check confidence outliers
    const confidences = responses.map(r => r.confidence);
    const meanConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;
    const stdDev = Math.sqrt(
        confidences.reduce((sum, c) => sum + Math.pow(c - meanConfidence, 2), 0) / confidences.length
    );

    responses.forEach(r => {
        if (Math.abs(r.confidence - meanConfidence) > 2 * stdDev) {
            if (!outliers.includes(r.id)) {
                outliers.push(r.id);
            }
        }
    });

    // 2. Check recommendation text outliers
    const recommendations = responses.map(r =>
        extractRecommendation(r.response_text)
    );

    responses.forEach((r, idx) => {
        let totalSimilarity = 0;
        let comparisons = 0;

        recommendations.forEach((otherRec, otherIdx) => {
            if (idx !== otherIdx) {
                totalSimilarity += calculateTextSimilarity(
                    recommendations[idx],
                    otherRec
                );
                comparisons++;
            }
        });

        const avgSimilarity = totalSimilarity / comparisons;
        if (avgSimilarity < 0.3) {  // Less than 30% similar to others
            if (!outliers.includes(r.id)) {
                outliers.push(r.id);
            }
        }
    });

    return outliers;
}

/**
 * Calculate average review scores for a response
 */
export function calculateAverageReviewScores(
    reviews: CouncilReview[]
): {
    accuracy: number;
    completeness: number;
    clarity: number;
    feasibility: number;
    overall: number;
} {
    if (reviews.length === 0) {
        return { accuracy: 0, completeness: 0, clarity: 0, feasibility: 0, overall: 0 };
    }

    const sum = reviews.reduce((acc, r) => ({
        accuracy: acc.accuracy + r.accuracy_score,
        completeness: acc.completeness + r.completeness_score,
        clarity: acc.clarity + r.clarity_score,
        feasibility: acc.feasibility + r.feasibility_score
    }), { accuracy: 0, completeness: 0, clarity: 0, feasibility: 0 });

    const count = reviews.length;
    const accuracy = sum.accuracy / count;
    const completeness = sum.completeness / count;
    const clarity = sum.clarity / count;
    const feasibility = sum.feasibility / count;
    const overall = (accuracy + completeness + clarity + feasibility) / 4;

    return { accuracy, completeness, clarity, feasibility, overall };
}

// ============================================================================
// PRIVATE HELPER FUNCTIONS
// ============================================================================

function extractRecommendation(responseText: string): string {
    // Extract text after "RECOMMENDATION:" marker
    const match = responseText.match(/RECOMMENDATION:\s*(.+?)(?=\n|REASONING:|CONFIDENCE:|$)/s);
    return match ? match[1].trim() : responseText.substring(0, 200);
}

function getModelWeight(
    modelName: string,
    config: CouncilModelsConfig
): number {
    if (config.chairman.model === modelName) {
        return config.chairman.weight;
    }

    const councilModel = config.council.find(m => m.model === modelName);
    return councilModel ? councilModel.weight : 1.0;
}

function calculateTextSimilarity(text1: string, text2: string): number {
    // Simple Jaccard similarity based on word sets
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));

    const intersection = new Set([...words1].filter(w => words2.has(w)));
    const union = new Set([...words1, ...words2]);

    return intersection.size / union.size;
}
