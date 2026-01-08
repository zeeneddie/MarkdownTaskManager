/**
 * Custom Error Definitions.
 *
 * This module defines custom error classes for handling specific error scenarios within the KaibanJS library.
 * It includes errors for API invocation failures and more nuanced errors that provide detailed diagnostic information.
 *
 * @module errors
 */
/** Base type for error context data */
export type ErrorContext = Record<string, unknown>;
/** Configuration for creating a pretty error */
export type PrettyErrorConfig = {
    /** The main error message */
    message: string;
    /** The original error that caused this error */
    rootError?: Error | null;
    /** Suggested steps to resolve the error */
    recommendedAction?: string | null;
    /** Additional context about the error */
    context?: ErrorContext;
    /** Where the error occurred */
    location?: string;
    /** Type of error */
    type?: string;
    /** Name of the error */
    name?: string;
};
/**
 * Error thrown when LLM API invocation fails
 */
export declare class LLMInvocationError extends Error {
    /** Additional context about the error */
    context: ErrorContext;
    /** The original error that caused this error */
    originalError: Error | null;
    /** Suggested steps to resolve the error */
    recommendedAction: string | null;
    constructor(message: string, originalError?: Error | null, recommendedAction?: string | null, context?: ErrorContext);
}
/**
 * Base error class with enhanced error reporting capabilities
 */
export declare class PrettyError extends Error {
    /** Type of error */
    type: string;
    /** The original error that caused this error */
    rootError: Error | null;
    /** Suggested steps to resolve the error */
    recommendedAction: string | null;
    /** Additional context about the error */
    context: ErrorContext;
    /** Where the error occurred */
    location: string;
    /** Formatted error message */
    prettyMessage: string;
    constructor({ message, rootError, recommendedAction, context, location, type, name, }: PrettyErrorConfig);
    /**
     * Creates a standardized error message incorporating all relevant information
     * @returns Formatted and informative error message
     */
    static createPrettyMessage(name: string, message: string, rootError: Error | null, recommendedAction: string | null): string;
}
/**
 * Base class for operation abortion errors
 */
export declare class AbortError extends Error {
    constructor(message?: string);
}
/**
 * Error thrown when an operation is stopped
 */
export declare class StopAbortError extends AbortError {
    constructor(message?: string);
}
/**
 * Error thrown when an operation is paused
 */
export declare class PauseAbortError extends AbortError {
    constructor(message?: string);
}
/**
 * Error thrown when a workflow operation fails
 */
export declare class WorkflowError extends Error {
    constructor(message: string);
}
export declare class AgentBlockError extends Error {
    constructor(message: string);
}
export declare class TaskBlockError extends Error {
    blockReason: string;
    blockedBy: string;
    isAgentDecision: boolean;
    constructor(message: string, blockReason: string, blockedBy: string, isAgentDecision: boolean);
}
