/**
 * SPEC-KIT EXECUTOR
 *
 * Standalone TypeScript executor for Spec-Kit workflow commands.
 * Communicates with Python backend via stdin/stdout JSON.
 *
 * Commands:
 * - spec-kit: Execute complete workflow (constitution → specification → tasks)
 * - constitution: Execute only constitution stage
 * - specification: Execute only specification stage
 * - tasks: Execute only tasks stage
 */

import * as readline from 'readline';
import { executeSpecKitWorkflow, SpecKitWorkflowInput } from './workflows/specKitWorkflow';
import { executeConstitution } from './commands/constitutionCommand';
import { executeSpecification } from './commands/specifyCommand';
import { executeTasks } from './commands/tasksCommand';
import {
  ConstitutionInput,
  SpecificationInput,
  TaskGenerationInput
} from './types/SpecKit';
import { agents } from './configs/agents';

// Input from Python backend
interface SpecKitRequest {
  command: 'spec-kit' | 'constitution' | 'specification' | 'tasks';
  businessCase: string;
  stakeholders: string[];
  constraints: string[];
  successCriteria: string[];
  technicalContext?: {
    existingSystems?: string[];
    technologies?: string[];
    teamSize?: number;
    timeline?: string;
  };
  projectPath?: string;
  projectName?: string;
  constitution?: any;  // For specification command
  specification?: any; // For tasks command
}

/**
 * Read JSON from stdin
 */
async function readStdin(): Promise<SpecKitRequest> {
  return new Promise((resolve, reject) => {
    let input = '';

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false
    });

    rl.on('line', (line) => {
      input += line;
    });

    rl.on('close', () => {
      try {
        const parsed = JSON.parse(input);
        resolve(parsed);
      } catch (error) {
        reject(new Error(`Failed to parse JSON input: ${error}`));
      }
    });

    rl.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Write JSON to stdout
 */
function writeStdout(data: any): void {
  console.log(JSON.stringify(data, null, 2));
}

/**
 * Main execution function
 */
async function main() {
  try {
    // Read request from Python backend
    const request = await readStdin();

    console.error(`🚀 Spec-Kit Executor: ${request.command}`);
    console.error(`   Business Case: ${request.businessCase.substring(0, 80)}...`);

    let result: any;

    switch (request.command) {
      case 'spec-kit':
        // Execute complete workflow
        const workflowInput: SpecKitWorkflowInput = {
          businessCase: request.businessCase,
          stakeholders: request.stakeholders,
          constraints: request.constraints,
          successCriteria: request.successCriteria,
          technicalContext: request.technicalContext,
          projectPath: request.projectPath,
          projectName: request.projectName
        };
        result = await executeSpecKitWorkflow(workflowInput);
        break;

      case 'constitution':
        // Execute only constitution
        const constitutionInput: ConstitutionInput = {
          businessCase: request.businessCase,
          stakeholders: request.stakeholders,
          constraints: request.constraints,
          successCriteria: request.successCriteria,
          technicalContext: request.technicalContext
        };
        const constitutionResult = await executeConstitution(constitutionInput, agents.productOwner);
        result = { constitution: constitutionResult };
        break;

      case 'specification':
        // Execute only specification
        const specInput: SpecificationInput = {
          constitution: request.constitution,
          technicalContext: request.technicalContext || {}
        };
        const specResult = await executeSpecification(specInput, agents.featureArchitect);
        result = { specification: specResult };
        break;

      case 'tasks':
        // Execute only tasks
        const tasksInput: TaskGenerationInput = {
          specification: request.specification
        };
        const tasksResult = await executeTasks(tasksInput, agents.featureArchitect);
        result = { tasks: tasksResult };
        break;

      default:
        throw new Error(`Unknown command: ${request.command}`);
    }

    // Write result to stdout for Python backend
    writeStdout(result);
    console.error(`✅ Spec-Kit Executor completed: ${request.command}`);
    process.exit(0);

  } catch (error: any) {
    console.error(`❌ Spec-Kit Executor error: ${error.message}`);
    console.error(error.stack);

    // Write error to stdout
    writeStdout({
      success: false,
      error: error.message,
      stack: error.stack
    });

    process.exit(1);
  }
}

// Run main
main();
