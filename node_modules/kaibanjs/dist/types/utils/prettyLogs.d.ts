/**
 * Pretty Logging Utilities.
 *
 * This module enhances log outputs by formatting them into more readable and visually appealing structures.
 * It provides functions that generate styled log entries for various operational states and outcomes,
 * making it easier to interpret and review logs.
 *
 * @module prettyLogs
 */
import { CostResult, LLMUsageStats } from './llmCostCalculator';
import { Task } from '..';
import { WorkflowFinishedLog } from '../types/logs';
import { WORKFLOW_STATUS_enum } from './enums';
/** Task completion log parameters */
export type TaskCompletionParams = {
    /** Task */
    task: Task;
    /** Number of iterations taken */
    iterationCount?: number;
    /** Duration in seconds */
    duration?: number;
    /** LLM usage statistics */
    llmUsageStats?: LLMUsageStats;
    /** Name of the agent */
    agentName?: string;
    /** Model used by the agent */
    agentModel?: string;
    /** Title of the task */
    taskTitle: string;
    /** Current task number */
    currentTaskNumber: number;
    /** Total number of tasks */
    totalTasks: number;
    /** Cost calculation details */
    costDetails?: CostResult;
};
/** Task status log parameters */
export type TaskStatusParams = {
    /** Task */
    task: Task;
    /** Current task number */
    currentTaskNumber: number;
    /** Total number of tasks */
    totalTasks: number;
    /** Title of the task */
    taskTitle: string;
    /** Current status of the task */
    taskStatus: string;
    /** Name of the agent */
    agentName?: string;
};
/** Workflow status log parameters */
export type WorkflowStatusParams = {
    /** Current workflow status */
    status: WORKFLOW_STATUS_enum;
    /** Status message */
    message: string;
};
/** Workflow result metadata */
export type WorkflowResultMetadata = {
    /** Final workflow result */
    result: string;
    /** Duration in seconds */
    duration?: number;
    /** LLM usage statistics */
    llmUsageStats?: LLMUsageStats;
    /** Number of iterations taken */
    iterationCount?: number;
    /** Cost calculation details */
    costDetails?: CostResult;
    /** Name of the team */
    teamName: string;
    /** Number of tasks */
    taskCount: number;
    /** Number of agents */
    agentCount: number;
};
/**
 * Logs task completion details in a formatted box
 * @param params - Task completion parameters
 */
export declare function logPrettyTaskCompletion(params: TaskCompletionParams): void;
/**
 * Logs task status changes in a formatted box
 * @param params - Task status parameters
 */
export declare function logPrettyTaskStatus(params: TaskStatusParams): void;
/**
 * Logs workflow status updates
 * @param params - Workflow status parameters
 */
export declare function logPrettyWorkflowStatus(params: WorkflowStatusParams): void;
/**
 * Logs workflow completion results in a formatted box
 * @param params - Workflow result parameters
 */
export declare function logPrettyWorkflowResult(params: WorkflowFinishedLog): void;
