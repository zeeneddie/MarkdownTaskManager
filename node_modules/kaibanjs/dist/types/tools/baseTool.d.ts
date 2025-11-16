import { StructuredTool } from '@langchain/core/tools';
export type ToolResult = string | Record<string, unknown>;
export type BaseTool = StructuredTool;
