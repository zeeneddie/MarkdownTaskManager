/**
 * Command Registry & Dispatcher
 *
 * Central system for registering, managing, and executing slash commands.
 * Provides command discovery, validation, execution, and statistics.
 */

import {
  SlashCommandType,
  SlashCommandInput,
  SlashCommandOutput,
  CommandStatus,
  CommandDefinition,
  CommandRegistryEntry,
  CommandExecutor,
  OutputFormat
} from '../types/SlashCommand';

/**
 * Command Registry - Singleton
 */
class CommandRegistry {
  private static instance: CommandRegistry;
  private registry: Map<SlashCommandType, CommandRegistryEntry>;
  private executionHistory: SlashCommandOutput[];

  private constructor() {
    this.registry = new Map();
    this.executionHistory = [];
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): CommandRegistry {
    if (!CommandRegistry.instance) {
      CommandRegistry.instance = new CommandRegistry();
    }
    return CommandRegistry.instance;
  }

  /**
   * Register a slash command
   */
  public register(
    definition: CommandDefinition,
    executor: CommandExecutor
  ): void {
    if (this.registry.has(definition.type)) {
      console.warn(`⚠️ Command ${definition.type} is already registered. Overwriting...`);
    }

    this.registry.set(definition.type, {
      definition,
      executor,
      enabled: true,
      usageCount: 0,
      averageDuration: 0,
      successRate: 1.0
    });

    console.error(`✅ Registered slash command: /${definition.type}`);
  }

  /**
   * Unregister a slash command
   */
  public unregister(commandType: SlashCommandType): boolean {
    const deleted = this.registry.delete(commandType);
    if (deleted) {
      console.error(`🗑️ Unregistered slash command: /${commandType}`);
    }
    return deleted;
  }

  /**
   * Check if command is registered
   */
  public isRegistered(commandType: SlashCommandType): boolean {
    return this.registry.has(commandType);
  }

  /**
   * Get command definition
   */
  public getDefinition(commandType: SlashCommandType): CommandDefinition | undefined {
    return this.registry.get(commandType)?.definition;
  }

  /**
   * Get all registered commands
   */
  public getAllCommands(): CommandDefinition[] {
    return Array.from(this.registry.values())
      .filter(entry => entry.enabled)
      .map(entry => entry.definition);
  }

  /**
   * Execute a slash command
   */
  public async execute(
    input: SlashCommandInput,
    executedBy: string = 'System'
  ): Promise<SlashCommandOutput> {
    const startTime = Date.now();
    const commandId = `cmd-${input.command}-${Date.now()}`;

    console.error('\n' + '='.repeat(80));
    console.error(`🎯 EXECUTING SLASH COMMAND: /${input.command}`);
    console.error('='.repeat(80));
    console.error(`Executed by: ${executedBy}`);
    console.error(`Command ID: ${commandId}`);

    // Validate command is registered
    if (!this.isRegistered(input.command)) {
      const errorOutput: SlashCommandOutput = {
        commandId,
        command: input.command,
        status: CommandStatus.FAILED,
        executedBy,
        executedAt: new Date(),
        completedAt: new Date(),
        duration: Date.now() - startTime,
        analysis: {
          summary: `Command '/${input.command}' is not registered`,
          issues: [{
            id: 'unknown-command',
            severity: 'HIGH',
            category: 'Command Error',
            title: 'Unknown command',
            description: `The command '/${input.command}' is not registered in the system`,
            location: 'Command Registry',
            recommendation: 'Check available commands with /help',
            autoFixable: false
          }]
        },
        recommendations: [],
        confidence: 0,
        needsHumanReview: true,
        rationale: 'Command not found',
        outputFormat: OutputFormat.TEXT,
        formattedOutput: `Error: Command '/${input.command}' not found`
      };

      this.executionHistory.push(errorOutput);
      return errorOutput;
    }

    // Get command entry
    const entry = this.registry.get(input.command)!;

    // Check if command is enabled
    if (!entry.enabled) {
      const errorOutput: SlashCommandOutput = {
        commandId,
        command: input.command,
        status: CommandStatus.FAILED,
        executedBy,
        executedAt: new Date(),
        completedAt: new Date(),
        duration: Date.now() - startTime,
        analysis: {
          summary: `Command '/${input.command}' is currently disabled`,
          issues: []
        },
        recommendations: [],
        confidence: 0,
        needsHumanReview: true,
        rationale: 'Command disabled',
        outputFormat: OutputFormat.TEXT,
        formattedOutput: `Error: Command '/${input.command}' is disabled`
      };

      this.executionHistory.push(errorOutput);
      return errorOutput;
    }

    // Validate required context
    const validationError = this.validateContext(entry.definition, input.context);
    if (validationError) {
      const errorOutput: SlashCommandOutput = {
        commandId,
        command: input.command,
        status: CommandStatus.FAILED,
        executedBy,
        executedAt: new Date(),
        completedAt: new Date(),
        duration: Date.now() - startTime,
        analysis: {
          summary: validationError,
          issues: [{
            id: 'context-validation',
            severity: 'HIGH',
            category: 'Input Error',
            title: 'Invalid context',
            description: validationError,
            location: 'Command Input',
            recommendation: 'Provide required context fields',
            autoFixable: false
          }]
        },
        recommendations: [],
        confidence: 0,
        needsHumanReview: true,
        rationale: 'Context validation failed',
        outputFormat: OutputFormat.TEXT,
        formattedOutput: `Error: ${validationError}`
      };

      this.executionHistory.push(errorOutput);
      return errorOutput;
    }

    console.error(`   Context: ${Object.keys(input.context).join(', ')}`);
    console.error(`   Options: ${input.options ? Object.keys(input.options).join(', ') : 'none'}`);
    console.error('');

    // Execute command
    try {
      const output = await entry.executor(input);
      output.commandId = commandId;
      output.executedBy = executedBy;
      output.executedAt = new Date();
      output.completedAt = new Date();
      output.duration = Date.now() - startTime;

      // Update statistics
      this.updateStatistics(input.command, output.status, output.duration);

      // Store in history
      this.executionHistory.push(output);

      console.error('='.repeat(80));
      console.error(`✅ COMMAND COMPLETED: /${input.command}`);
      console.error('='.repeat(80));
      console.error(`Status: ${output.status}`);
      console.error(`Duration: ${(output.duration / 1000).toFixed(2)}s`);
      console.error(`Recommendations: ${output.recommendations.length}`);
      console.error(`Confidence: ${(output.confidence * 100).toFixed(0)}%`);
      console.error('='.repeat(80) + '\n');

      return output;
    } catch (error) {
      const errorOutput: SlashCommandOutput = {
        commandId,
        command: input.command,
        status: CommandStatus.FAILED,
        executedBy,
        executedAt: new Date(),
        completedAt: new Date(),
        duration: Date.now() - startTime,
        analysis: {
          summary: `Command execution failed: ${error instanceof Error ? error.message : String(error)}`,
          issues: [{
            id: 'execution-error',
            severity: 'CRITICAL',
            category: 'Execution Error',
            title: 'Command execution failed',
            description: error instanceof Error ? error.message : String(error),
            location: 'Command Executor',
            recommendation: 'Check command implementation and input',
            autoFixable: false
          }]
        },
        recommendations: [],
        confidence: 0,
        needsHumanReview: true,
        rationale: 'Execution failed',
        outputFormat: OutputFormat.TEXT,
        formattedOutput: `Error: ${error instanceof Error ? error.message : String(error)}`
      };

      this.updateStatistics(input.command, CommandStatus.FAILED, errorOutput.duration);
      this.executionHistory.push(errorOutput);

      console.error('='.repeat(80));
      console.error(`❌ COMMAND FAILED: /${input.command}`);
      console.error('='.repeat(80));
      console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
      console.error('='.repeat(80) + '\n');

      return errorOutput;
    }
  }

  /**
   * Validate command context
   */
  private validateContext(
    definition: CommandDefinition,
    context: any
  ): string | null {
    for (const required of definition.requiredContext) {
      if (!context[required]) {
        return `Missing required context field: ${required}`;
      }
    }
    return null;
  }

  /**
   * Update command statistics
   */
  private updateStatistics(
    commandType: SlashCommandType,
    status: CommandStatus,
    duration: number
  ): void {
    const entry = this.registry.get(commandType);
    if (!entry) return;

    entry.usageCount++;

    // Update average duration
    entry.averageDuration =
      (entry.averageDuration * (entry.usageCount - 1) + duration) / entry.usageCount;

    // Update success rate
    const successCount = this.executionHistory
      .filter(h => h.command === commandType && h.status === CommandStatus.COMPLETED)
      .length;
    entry.successRate = successCount / entry.usageCount;
  }

  /**
   * Get command statistics
   */
  public getStatistics(commandType: SlashCommandType): {
    usageCount: number;
    averageDuration: number;
    successRate: number;
  } | null {
    const entry = this.registry.get(commandType);
    if (!entry) return null;

    return {
      usageCount: entry.usageCount,
      averageDuration: entry.averageDuration,
      successRate: entry.successRate
    };
  }

  /**
   * Get execution history
   */
  public getHistory(
    commandType?: SlashCommandType,
    limit: number = 10
  ): SlashCommandOutput[] {
    let history = this.executionHistory;

    if (commandType) {
      history = history.filter(h => h.command === commandType);
    }

    return history.slice(-limit);
  }

  /**
   * Enable/disable a command
   */
  public setEnabled(commandType: SlashCommandType, enabled: boolean): void {
    const entry = this.registry.get(commandType);
    if (entry) {
      entry.enabled = enabled;
      console.error(`${enabled ? '✅' : '❌'} Command /${commandType} ${enabled ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Get registry summary
   */
  public getSummary(): {
    totalCommands: number;
    enabledCommands: number;
    totalExecutions: number;
    successfulExecutions: number;
    failedExecutions: number;
    averageDuration: number;
  } {
    const totalCommands = this.registry.size;
    const enabledCommands = Array.from(this.registry.values()).filter(e => e.enabled).length;
    const totalExecutions = this.executionHistory.length;
    const successfulExecutions = this.executionHistory.filter(h => h.status === CommandStatus.COMPLETED).length;
    const failedExecutions = this.executionHistory.filter(h => h.status === CommandStatus.FAILED).length;
    const averageDuration = this.executionHistory.length > 0
      ? this.executionHistory.reduce((sum, h) => sum + h.duration, 0) / this.executionHistory.length
      : 0;

    return {
      totalCommands,
      enabledCommands,
      totalExecutions,
      successfulExecutions,
      failedExecutions,
      averageDuration
    };
  }

  /**
   * Clear execution history
   */
  public clearHistory(): void {
    this.executionHistory = [];
    console.error('🗑️ Execution history cleared');
  }
}

/**
 * Get command registry instance
 */
export function getCommandRegistry(): CommandRegistry {
  return CommandRegistry.getInstance();
}

/**
 * Register a command
 */
export function registerCommand(
  definition: CommandDefinition,
  executor: CommandExecutor
): void {
  getCommandRegistry().register(definition, executor);
}

/**
 * Execute a command
 */
export async function executeCommand(
  input: SlashCommandInput,
  executedBy?: string
): Promise<SlashCommandOutput> {
  return getCommandRegistry().execute(input, executedBy);
}

/**
 * Get all available commands
 */
export function getAvailableCommands(): CommandDefinition[] {
  return getCommandRegistry().getAllCommands();
}
