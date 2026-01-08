import { TeamStore } from '../stores';
export type DependencyResult = {
    taskId: string;
    taskTitle: string;
    taskDescription: string;
    result: string | Record<string, unknown>;
    timestamp: number;
};
/**
 * Creates a deterministic execution subscriber that manages task execution
 * using a queue and dependency graph.
 *
 * @param teamStore - The team store instance
 * @returns Cleanup function to unsubscribe
 */
export declare const subscribeDeterministicExecution: (teamStore: TeamStore) => void;
