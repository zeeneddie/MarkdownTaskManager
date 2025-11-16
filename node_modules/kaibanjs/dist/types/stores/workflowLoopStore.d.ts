import { StateCreator } from 'zustand';
import { CombinedStoresState } from './teamStore.types';
import { WorkflowLoopState } from './workflowLoopStore.types';
export declare const useWorkflowLoopStore: StateCreator<CombinedStoresState, [
], [
], WorkflowLoopState>;
