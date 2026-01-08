/**
 * Agent Utility Functions.
 *
 * This module provides utility functions specifically designed to support agent operations.
 * Functions include retrieving API keys based on agent configurations and handling agent attributes.
 *
 * @module agents
 */
import { BaseChatModel } from '@langchain/core/language_models/chat_models';
import { Env } from '../agents/baseAgent';
import { LLMProvider } from './llm.types';
/** LLM configuration options */
export type LLMConfig = {
    /** API key for the LLM service */
    apiKey?: string;
    /** LLM service provider */
    provider: LLMProvider;
    /** LLM model */
    model: string;
};
export type LangChainChatModel = BaseChatModel;
/** Agent attributes for prompt templates */
export type AgentAttributes = {
    /** Agent's name */
    name: string;
    /** Agent's role description */
    role: string;
    /** Agent's background information */
    background: string;
    /** Agent's goal */
    goal: string;
    /** Additional context for the agent */
    context?: string;
    /** Expected output format */
    expectedOutput?: string;
};
/**
 * Gets the appropriate API key based on LLM configuration and environment
 * @param llmConfig - LLM configuration object
 * @param env - Environment variables containing API keys
 * @param fromEnvFirst - Whether to prioritize environment variables over config
 * @returns API key string or undefined if not found
 */
export declare function getApiKey(llmConfig: LLMConfig | undefined, env: Env, fromEnvFirst?: boolean): string | undefined;
/**
 * Replaces placeholders in agent prompt templates with actual values
 * @param template - The prompt template string
 * @param attributes - Agent attributes to inject into the template
 * @returns Processed template with replaced values
 */
export declare function replaceAgentAttributes(template: string, attributes: AgentAttributes): string;
