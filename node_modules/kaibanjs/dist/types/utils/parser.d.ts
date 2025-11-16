/**
 * Data Parsing Utilities.
 *
 * This module provides functions for parsing and sanitizing data formats, particularly focusing
 * on JSON structures that agents might receive or need to process. These utilities ensure that
 * data handled by agents is in the correct format and free of errors.
 *
 * @module parser
 */
/** Action input data structure */
export type ActionInput = Record<string, unknown>;
/** Parsed agent response structure */
export type AgentResponse = {
    /** Agent's reasoning about the task */
    thought?: string;
    /** Action to be taken */
    action?: string;
    /** Input parameters for the action */
    actionInput?: ActionInput | null;
    /** Result of the action */
    observation?: string;
    /** Whether the agent has reached a final answer */
    isFinalAnswerReady?: boolean;
    /** The final answer from the agent */
    finalAnswer?: string;
};
/**
 * Parses a JSON string into a structured object, with fallback to regex-based parsing
 * @param str - The JSON string to parse
 * @returns Parsed object or empty object if parsing fails
 *
 * @example
 * ```typescript
 * const input = `{
 *   "thought": "Need to search for information",
 *   "action": "search",
 *   "actionInput": {"query": "example"}
 * }`;
 * const result = getParsedJSON(input);
 * ```
 */
export declare function getParsedJSON(str: string): AgentResponse;
