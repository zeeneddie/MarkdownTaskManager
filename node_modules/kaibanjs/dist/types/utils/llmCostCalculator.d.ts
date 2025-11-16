/**
 * LLM Cost Calculation Utilities.
 *
 * This module provides functions for calculating costs associated with using large language models (LLMs)
 * based on token usage and model-specific pricing. It helps in budgeting and monitoring the financial
 * aspects of LLM usage within the KaibanJS library.
 *
 * @module llmCostCalculator
 */
import { LLMProvider } from './llm.types';
/** Model pricing information */
export type ModelPricing = {
    /** Unique identifier for the model */
    modelCode: string;
    /** Provider of the model */
    provider: LLMProvider;
    /** Cost per million input tokens */
    inputPricePerMillionTokens: number;
    /** Cost per million output tokens */
    outputPricePerMillionTokens: number;
    /** Description of model features */
    features: string;
};
/** LLM usage statistics */
export type LLMUsageStats = {
    /** Number of input tokens processed */
    inputTokens: number;
    /** Number of output tokens generated */
    outputTokens: number;
    /** Total number of API calls made */
    callsCount: number;
    /** Number of failed API calls */
    callsErrorCount: number;
    /** Number of parsing errors encountered */
    parsingErrors: number;
};
/** Cost calculation result */
export type CostResult = {
    /** Cost for input tokens (-1 if calculation failed) */
    costInputTokens: number;
    /** Cost for output tokens (-1 if calculation failed) */
    costOutputTokens: number;
    /** Total cost (-1 if calculation failed) */
    totalCost: number;
};
/** Model usage statistics by model code */
export type ModelUsageStats = Record<string, {
    inputTokens: number;
    outputTokens: number;
}>;
/**
 * Calculates the approximate cost of using a specified AI model based on token usage
 * @param modelCode - The unique code identifier for the AI model
 * @param llmUsageStats - Object containing usage statistics
 * @returns Cost calculation result
 *
 * @example
 * ```typescript
 * const stats = {
 *   inputTokens: 500000,
 *   outputTokens: 200000,
 *   callsCount: 10,
 *   callsErrorCount: 1,
 *   parsingErrors: 0
 * };
 * const costs = calculateTaskCost('gpt-4o-mini', stats);
 * console.log(costs);
 * ```
 */
export declare function calculateTaskCost(modelCode: string, llmUsageStats: LLMUsageStats): CostResult;
/**
 * Calculates the total cost across all models used in a workflow
 * @param modelUsageStats - Object mapping model codes to their usage statistics
 * @returns Combined cost calculation result
 */
export declare function calculateTotalWorkflowCost(modelUsageStats: ModelUsageStats): CostResult;
