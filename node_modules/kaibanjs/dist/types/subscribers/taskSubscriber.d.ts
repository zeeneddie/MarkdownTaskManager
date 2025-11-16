/**
 * Task Status Subscriber.
 *
 * Listens to changes in task status within the library's state management system, providing logs and reactive behaviors to these changes.
 * This helps in monitoring task progression and debugging issues in real-time.
 *
 * Usage:
 * Deploy this subscriber to actively monitor and respond to changes in task status, enhancing the observability and responsiveness of your application.
 */
import { TeamStore } from '../stores';
/**
 * Subscribes to task status updates in the store and logs them appropriately.
 * @param useStore - The store instance to subscribe to
 */
declare const subscribeTaskStatusUpdates: (useStore: TeamStore) => void;
export { subscribeTaskStatusUpdates };
