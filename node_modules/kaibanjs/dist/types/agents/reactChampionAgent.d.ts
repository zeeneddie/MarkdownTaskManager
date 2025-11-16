/**
 * Enhanced ReAct Agent Implementation.
 *
 * This file implements the ReactChampionAgent, a variation of the traditional ReAct (Reasoning and Action) agent model,
 * tailored to enhance the agent's capabilities through iterative feedback loops. Unlike the original ReAct pattern that typically
 * follows a linear execution path, our Reflex Act model introduces a round-trip communication process, enabling continuous refinement
 * and fine-tuning of actions based on real-time feedback.
 *
 * This enhanced approach allows the agent to dynamically adjust its strategies and responses, significantly improving adaptability
 * and decision-making accuracy in complex scenarios. The model is designed for environments where ongoing interaction and meticulous
 * state management are crucial.
 *
 * @packageDocumentation
 */
import { BaseMessage } from '@langchain/core/messages';
import { RunnableWithMessageHistory } from '@langchain/core/runnables';
import { ChatMessageHistory } from 'langchain/stores/message/in_memory';
import { Task } from '..';
import { TeamStore } from '../stores';
import { BaseTool, ToolResult } from '../tools/baseTool';
import { LangChainChatModel } from '../utils/agents';
import { LLMInvocationError } from '../utils/errors';
import { AgentLoopResult, LLMOutput, ParsedLLMOutput, ThinkingResult } from '../utils/llm.types';
import { BaseAgent, BaseAgentParams, Env } from './baseAgent';
/**
 * ReactChampionAgent class that extends BaseAgent to implement enhanced ReAct pattern
 * @class
 */
export declare class ReactChampionAgent extends BaseAgent {
    protected executableAgent?: RunnableWithMessageHistory<unknown, unknown>;
    protected llmInstance?: LangChainChatModel;
    protected interactionsHistory: ChatMessageHistory;
    protected lastFeedbackMessage: string | null;
    protected currentIterations: number;
    constructor(config: BaseAgentParams);
    /**
     * Initializes the agent with store and environment configuration
     * @param store - The agent store instance
     * @param env - Environment configuration
     */
    initialize(store: TeamStore, env: Env): void;
    /**
     * Resumes work on a task
     * @param task - The task to resume
     */
    workOnTaskResume(task: Task): Promise<void>;
    /**
     * Updates the agent's environment configuration
     * @param env - New environment configuration
     */
    updateEnv(env: Env): void;
    /**
     * Starts work on a new task
     * @param task - The task to work on
     * @param inputs - Task inputs
     * @param context - Task context
     */
    workOnTask(task: Task, inputs: Record<string, unknown>, context: string): Promise<AgentLoopResult>;
    /**
     * Processes feedback for a task
     * @param task - The task to process feedback for
     * @param feedbackList - List of feedback items
     */
    workOnFeedback(task: Task, feedbackList: Array<{
        content: string;
    }>): Promise<AgentLoopResult>;
    /**
     * Prepares the agent for a new task
     * @param task - The task to prepare for
     * @param inputs - Task inputs
     * @param context - Task context
     */
    prepareAgentForTask(task: Task, inputs: Record<string, unknown>, context: string): {
        executableAgent: RunnableWithMessageHistory<unknown, unknown>;
        initialFeedbackMessage: string;
    };
    /**
     * Main agent loop for processing tasks
     * @param agent - The agent instance
     * @param task - The task being processed
     * @param ExecutableAgent - The executable agent instance
     * @param initialMessage - Initial feedback message
     */
    agenticLoop(agent: ReactChampionAgent, task: Task, ExecutableAgent: RunnableWithMessageHistory<unknown, unknown> | undefined, initialMessage: string | null): Promise<AgentLoopResult>;
    /**
     * Builds the system message for the agent
     */
    buildSystemMessage(agent: ReactChampionAgent, task: Task, interpolatedTaskDescription: string): string;
    /**
     * Builds the initial message for the agent
     */
    buildInitialMessage(agent: ReactChampionAgent, task: Task, interpolatedTaskDescription: string, context?: string): string;
    /**
     * Determines the type of action based on parsed LLM output
     */
    determineActionType(parsedResult: ParsedLLMOutput): string;
    handleIterationStart(params: {
        agent: ReactChampionAgent;
        task: Task;
        iterations: number;
        maxAgentIterations: number;
    }): void;
    handleIterationEnd(params: {
        agent: ReactChampionAgent;
        task: Task;
        iterations: number;
        maxAgentIterations: number;
    }): void;
    handleThinkingStart(params: {
        agent: ReactChampionAgent;
        task: Task;
        messages: BaseMessage[][];
    }): Promise<unknown[]>;
    handleThinkingEnd(params: {
        agent: ReactChampionAgent;
        task: Task;
        output: LLMOutput;
    }): Promise<ThinkingResult>;
    handleThinkingError(params: {
        agent: ReactChampionAgent;
        task: Task;
        error: LLMInvocationError;
    }): void;
    /**
     * Executes the thinking process for the agent
     */
    executeThinking(agent: ReactChampionAgent, task: Task, ExecutableAgent: RunnableWithMessageHistory<unknown, unknown>, feedbackMessage: string | null): Promise<ThinkingResult>;
    handleIssuesParsingLLMOutput(params: {
        agent: ReactChampionAgent;
        task: Task;
        output: ThinkingResult;
    }): string;
    handleIssuesParsingSchemaOutput(params: {
        agent: ReactChampionAgent;
        task: Task;
        output: ThinkingResult;
    }): string;
    handleFinalAnswer(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
    }): ParsedLLMOutput;
    handleThought(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
    }): string;
    handleSelfQuestion(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
    }): string;
    executeUsingTool(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
        tool: BaseTool;
    }): Promise<{
        result: string;
        error?: LLMInvocationError;
        reason?: string;
        action: string;
    }>;
    handleUsingToolStart(params: {
        agent: ReactChampionAgent;
        task: Task;
        tool: BaseTool;
        input?: Record<string, unknown> | string;
    }): void;
    handleUsingToolEnd(params: {
        agent: ReactChampionAgent;
        task: Task;
        tool: BaseTool;
        output: ToolResult;
    }): void;
    handleUsingToolError(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
        tool: BaseTool;
        error: LLMInvocationError;
    }): string;
    handleToolDoesNotExist(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
        toolName: string;
    }): string;
    handleObservation(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
    }): string;
    handleWeirdOutput(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedLLMOutput: ParsedLLMOutput;
    }): string;
    handleAgenticLoopError(params: {
        agent: ReactChampionAgent;
        task: Task;
        error: LLMInvocationError;
        iterations: number;
        maxAgentIterations: number;
    }): void;
    handleTaskAborted(params: {
        agent: ReactChampionAgent;
        task: Task;
        error: LLMInvocationError;
    }): void;
    handleMaxIterationsError(params: {
        agent: ReactChampionAgent;
        task: Task;
        iterations: number;
        maxAgentIterations: number;
    }): void;
    handleTaskCompleted(params: {
        agent: ReactChampionAgent;
        task: Task;
        parsedResultWithFinalAnswer: ParsedLLMOutput;
        iterations: number;
        maxAgentIterations: number;
    }): void;
    getCleanedAgent(): Partial<BaseAgent>;
    reset(): void;
}
