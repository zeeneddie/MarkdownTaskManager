/**
 * Command System Initialization
 *
 * Registers all 19 slash commands at startup (16 SuperClaude + 3 Spec-Kit)
 */

import { registerArchitectCommand } from './architectCommand';
import { registerReviewerCommand } from './reviewerCommand';
import { registerOptimizerCommand } from './optimizerCommand';
import { registerDebuggerCommand } from './debuggerCommand';
import { registerAllCommands } from './allCommands';
import { getCommandRegistry } from '../workflows/commandRegistry';

// Spec-Kit workflow commands
import { registerConstitutionCommand } from './constitutionCommand';
import { registerSpecifyCommand } from './specifyCommand';
import { registerTasksCommand } from './tasksCommand';

/**
 * Initialize all slash commands
 */
export function initializeAllCommands(): void {
  console.error('\n' + '='.repeat(80));
  console.error('🎯 INITIALIZING SUPERCLAUDE FRAMEWORK + SPEC-KIT');
  console.error('='.repeat(80));
  console.error('Registering 19 slash commands (16 SuperClaude + 3 Spec-Kit)...\n');

  // Register core 4 commands
  registerArchitectCommand();
  registerReviewerCommand();
  registerOptimizerCommand();
  registerDebuggerCommand();

  // Register remaining 12 SuperClaude commands
  registerAllCommands();

  // Register 3 Spec-Kit workflow commands (Week 8)
  console.error('📋 Registering Spec-Kit workflow commands...');
  registerConstitutionCommand();
  registerSpecifyCommand();
  registerTasksCommand();
  console.error('✅ Spec-Kit commands registered\n');

  // Get summary
  const registry = getCommandRegistry();
  const summary = registry.getSummary();

  console.error('='.repeat(80));
  console.error('✅ SUPERCLAUDE FRAMEWORK INITIALIZED');
  console.error('='.repeat(80));
  console.error(`Total Commands: ${summary.totalCommands}`);
  console.error(`Enabled Commands: ${summary.enabledCommands}`);
  console.error('\n📋 Available Commands:');

  const commands = registry.getAllCommands();
  commands.forEach(cmd => {
    console.error(`   /${cmd.type.padEnd(20)} - ${cmd.description}`);
  });

  console.error('\n' + '='.repeat(80) + '\n');
}

/**
 * Export command registry access
 */
export { getCommandRegistry, executeCommand, getAvailableCommands } from '../workflows/commandRegistry';

/**
 * Export all command types
 */
export { SlashCommandType, SlashCommandInput, SlashCommandOutput } from '../types/SlashCommand';
