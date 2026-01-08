/**
 * A/B Testing Types for Agent Evolution
 *
 * Multi-variant experimentation framework for continuous agent improvement.
 */

/**
 * Experiment status enum
 */
export enum ExperimentStatus {
    DRAFT = 'DRAFT',           // Setup phase, can edit variants
    ACTIVE = 'ACTIVE',         // Running, traffic allocated
    PAUSED = 'PAUSED',         // Temporarily stopped
    COMPLETED = 'COMPLETED',    // Winner declared
    CANCELLED = 'CANCELLED'     // Aborted without winner
}

/**
 * Traffic allocation configuration
 */
export interface TrafficAllocation {
    variantId: string;
    percentage: number;  // 0-100
}

/**
 * Metrics snapshot for experiment result
 */
export interface MetricsSnapshot {
    success_rate?: number;           // 0-1
    estimation_accuracy?: number;    // 0-1
    code_quality_score?: number;     // 0-10
    execution_time_ms?: number;
    retry_count?: number;
    [key: string]: any;  // Allow additional metrics
}

/**
 * Experiment variant configuration
 */
export interface ExperimentVariant {
    id: string;
    experiment_id: string;
    variant_name: string;           // e.g., "control", "variant_a"
    description?: string;
    traffic_percentage: number;      // 0-100
    config_json: Record<string, any>; // Agent-specific config
    is_control: boolean;
    created_at: Date;
}

/**
 * A/B test experiment
 */
export interface Experiment {
    id: string;
    agent_id: string;               // Which agent is being tested
    feature_name: string;           // Feature being experimented with
    description?: string;
    status: ExperimentStatus;
    created_at: Date;
    started_at?: Date;
    completed_at?: Date;
    winner_variant_id?: string;
    extra_metadata?: Record<string, any>;

    // Relationships (populated)
    variants?: ExperimentVariant[];
    winner_variant?: ExperimentVariant;
}

/**
 * Single result from a variant
 */
export interface ExperimentResult {
    id: string;
    variant_id: string;
    task_id: string;
    work_type?: string;
    success: boolean;
    metrics_json: MetricsSnapshot;
    error_message?: string;
    created_at: Date;

    // Relationship (populated)
    variant?: ExperimentVariant;
}

/**
 * Statistical analysis result
 */
export interface ExperimentAnalysis {
    experiment_id: string;
    sample_size_per_variant: Record<string, number>;
    success_rate_per_variant: Record<string, number>;
    confidence_intervals: Record<string, { lower: number; upper: number }>;
    p_value?: number;
    recommended_winner?: string;
    consensus_level: number;  // 0-1 (confidence in winner)
    min_samples_reached: boolean;
}

/**
 * Request to create new experiment
 */
export interface CreateExperimentRequest {
    agent_id: string;
    feature_name: string;
    description?: string;
    variants: CreateVariantRequest[];
}

/**
 * Request to create variant
 */
export interface CreateVariantRequest {
    variant_name: string;
    description?: string;
    traffic_percentage: number;
    config_json: Record<string, any>;
    is_control?: boolean;
}

/**
 * Request to start experiment
 */
export interface StartExperimentRequest {
    experiment_id: string;
}

/**
 * Request to complete experiment
 */
export interface CompleteExperimentRequest {
    experiment_id: string;
    winner_variant_id: string;
}

/**
 * Request to log experiment result
 */
export interface LogResultRequest {
    variant_id: string;
    task_id: string;
    work_type?: string;
    success: boolean;
    metrics: MetricsSnapshot;
    error_message?: string;
}

/**
 * Helper: Calculate traffic allocation for task
 */
export function allocateTraffic(
    variants: ExperimentVariant[],
    taskId: string,
    experimentId: string
): string {
    // Deterministic hash for sticky assignment
    const hash = simpleHash(`${taskId}-${experimentId}`);
    const randomValue = hash % 100;  // 0-99

    let cumulative = 0;
    for (const variant of variants) {
        cumulative += variant.traffic_percentage;
        if (randomValue < cumulative) {
            return variant.id;
        }
    }

    // Fallback to first variant
    return variants[0]?.id || '';
}

/**
 * Simple hash function for consistent assignment
 */
function simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;  // Convert to 32bit integer
    }
    return Math.abs(hash);
}

/**
 * Validation: Check if traffic percentages sum to 100
 */
export function validateTrafficAllocation(
    variants: CreateVariantRequest[]
): boolean {
    const total = variants.reduce((sum, v) => sum + v.traffic_percentage, 0);
    return Math.abs(total - 100) < 0.01;  // Allow for floating point errors
}

/**
 * Helper: Check if minimum samples reached for statistical significance
 */
export function hasMinimumSamples(
    resultsPerVariant: Record<string, number>,
    minSamples: number = 30
): boolean {
    return Object.values(resultsPerVariant).every(count => count >= minSamples);
}

/**
 * Helper: Calculate success rate from results
 */
export function calculateSuccessRate(results: ExperimentResult[]): number {
    if (results.length === 0) return 0;
    const successes = results.filter(r => r.success).length;
    return successes / results.length;
}

/**
 * Helper: Group results by variant
 */
export function groupResultsByVariant(
    results: ExperimentResult[]
): Record<string, ExperimentResult[]> {
    return results.reduce((acc, result) => {
        if (!acc[result.variant_id]) {
            acc[result.variant_id] = [];
        }
        acc[result.variant_id].push(result);
        return acc;
    }, {} as Record<string, ExperimentResult[]>);
}

/**
 * Export all types
 */
export type {
    TrafficAllocation,
    MetricsSnapshot,
    ExperimentVariant,
    Experiment,
    ExperimentResult,
    ExperimentAnalysis,
    CreateExperimentRequest,
    CreateVariantRequest,
    StartExperimentRequest,
    CompleteExperimentRequest,
    LogResultRequest
};
