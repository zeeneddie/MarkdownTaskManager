import { z } from 'zod';
import { BaseAgent } from '../agents/baseAgent';
import { StructuredTool } from '@langchain/core/tools';
import { ToolResult } from './baseTool';
/**
 * Tool for blocking tasks when they cannot or should not proceed.
 * This tool allows agents to explicitly block tasks for various reasons such as:
 * - Insufficient permissions/clearance
 * - Missing prerequisites
 * - Security concerns
 * - Resource constraints
 */
export declare class BlockTaskTool extends StructuredTool {
    name: string;
    description: string;
    schema: z.ZodObject<{
        reason: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        reason: string;
    }, {
        reason: string;
    }>;
    protected agent: BaseAgent;
    constructor(agent: BaseAgent);
    _call(input: Record<string, unknown>): Promise<ToolResult>;
}
