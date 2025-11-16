/**
 * Prompt Templates for Agents.
 *
 * This module provides templates for constructing prompts that are used to interact with language models
 * within the KaibanJS library. These templates ensure that interactions are consistent and properly
 * formatted, facilitating effective communication with LLMs.
 *
 * @module prompts
 */
import { ZodError, ZodSchema } from 'zod';
import { ParsedLLMOutput } from './llm.types';
import { Task } from '../index';
import { BaseAgent } from '../agents/baseAgent';
import { ToolResult } from '../tools/baseTool';
interface BasePromptParams {
    agent: BaseAgent;
    task: Task;
}
interface SystemMessageParams extends BasePromptParams {
    insights?: string;
}
interface InitialMessageParams extends BasePromptParams {
    context?: string;
}
interface InvalidJsonFeedbackParams extends BasePromptParams {
    llmOutput: string;
}
interface InvalidOutputSchemaParams extends BasePromptParams {
    llmOutput: string;
    outputSchema: ZodSchema | null;
    outputSchemaError?: ZodError;
}
interface ThoughtWithSelfQuestionParams extends BasePromptParams {
    question: string;
    thought: string;
    parsedLLMOutput: ParsedLLMOutput;
}
interface SelfQuestionFeedbackParams extends BasePromptParams {
    question: string;
    parsedLLMOutput: ParsedLLMOutput;
}
interface ThoughtFeedbackParams extends BasePromptParams {
    thought: string;
    parsedLLMOutput: ParsedLLMOutput;
}
interface ToolResultParams extends BasePromptParams {
    toolResult: ToolResult;
    parsedLLMOutput: ParsedLLMOutput;
}
interface ToolErrorParams extends BasePromptParams {
    toolName: string;
    error: Error;
    parsedLLMOutput: ParsedLLMOutput;
}
interface ForceFinalAnswerParams extends BasePromptParams {
    iterations: number;
    maxAgentIterations: number;
}
interface WorkOnFeedbackParams extends BasePromptParams {
    feedback: string;
}
interface ObservationParams extends BasePromptParams {
    parsedLLMOutput: ParsedLLMOutput;
}
interface WeirdOutputParams extends BasePromptParams {
    parsedLLMOutput: ParsedLLMOutput;
}
export interface DefaultPrompts {
    SYSTEM_MESSAGE: (params: SystemMessageParams) => string;
    INITIAL_MESSAGE: (params: InitialMessageParams) => string;
    INVALID_JSON_FEEDBACK: (params: InvalidJsonFeedbackParams) => string;
    INVALID_OUTPUT_SCHEMA_FEEDBACK: (params: InvalidOutputSchemaParams) => string;
    THOUGHT_WITH_SELF_QUESTION_FEEDBACK: (params: ThoughtWithSelfQuestionParams) => string;
    THOUGHT_FEEDBACK: (params: ThoughtFeedbackParams) => string;
    SELF_QUESTION_FEEDBACK: (params: SelfQuestionFeedbackParams) => string;
    TOOL_RESULT_FEEDBACK: (params: ToolResultParams) => string;
    TOOL_ERROR_FEEDBACK: (params: ToolErrorParams) => string;
    TOOL_NOT_EXIST_FEEDBACK: (params: ToolErrorParams) => string;
    OBSERVATION_FEEDBACK: (params: ObservationParams) => string;
    WEIRD_OUTPUT_FEEDBACK: (params: WeirdOutputParams) => string;
    FORCE_FINAL_ANSWER_FEEDBACK: (params: ForceFinalAnswerParams) => string;
    WORK_ON_FEEDBACK_FEEDBACK: (params: WorkOnFeedbackParams) => string;
}
/** Default prompt templates for the ReactChampionAgent */
export declare const REACT_CHAMPION_AGENT_DEFAULT_PROMPTS: DefaultPrompts;
export {};
