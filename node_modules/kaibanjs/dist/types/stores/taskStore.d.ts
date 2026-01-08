import { StateCreator } from 'zustand';
import { TaskStoreState } from './taskStore.types';
import { CombinedStoresState } from './teamStore.types';
export declare const useTaskStore: StateCreator<CombinedStoresState, [
], [
], TaskStoreState>;
