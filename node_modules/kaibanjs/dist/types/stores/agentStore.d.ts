/**
 * Agent Store Configuration.
 *
 * This file configures a Zustand store specifically for managing the state of agents within the KaibanJS library.
 * It outlines actions and state changes related to the lifecycle of agents, including task execution, status updates, and error handling.
 *
 * Usage:
 * Employ this store to handle state updates for agents dynamically throughout the lifecycle of their tasks and interactions.
 */
import { StateCreator } from 'zustand';
import { AgentStoreState } from './agentStore.types';
import { CombinedStoresState } from './teamStore.types';
export declare const useAgentStore: StateCreator<CombinedStoresState, [
], [
], AgentStoreState>;
