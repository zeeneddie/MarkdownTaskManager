/**
 * Workflow Status Subscriber.
 *
 * Monitors changes in the workflow status, logging significant events and updating the system state accordingly.
 * This is crucial for maintaining a clear overview of workflow progress and handling potential issues promptly.
 *
 * Usage:
 * Use this subscriber to keep track of workflow statuses, enabling proactive management of workflows and their states.
 */
import { TeamStore } from '../stores';
/**
 * Subscribes to workflow status updates and logs them appropriately.
 * @param useStore - The store instance to subscribe to
 */
declare const subscribeWorkflowStatusUpdates: (useStore: TeamStore) => void;
export { subscribeWorkflowStatusUpdates };
