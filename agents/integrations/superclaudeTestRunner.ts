/**
 * SuperClaude Test Runner - TypeScript Wrapper
 *
 * This module provides a TypeScript interface to the SuperClaude /sc:test
 * Python integration for automated test execution and coverage analysis.
 *
 * Week 6 Day 5 - SuperClaude Test Integration
 */

import { spawn } from 'child_process';
import * as path from 'path';

/**
 * Options for SuperClaude test execution
 */
export interface SuperClaudeTestOptions {
  targetFiles?: string[];
  testType?: 'unit' | 'integration' | 'e2e' | 'all';
  coverage?: boolean;
  watch?: boolean;
  timeout?: number;  // milliseconds
}

/**
 * Test results from SuperClaude execution
 */
export interface SuperClaudeTestResult {
  success: boolean;
  testResults: {
    passed: number;
    failed: number;
    skipped: number;
    total: number;
  };
  coverage: {
    lines?: number;
    branches?: number;
    functions?: number;
    statements?: number;
  };
  failures: Array<{
    testName: string;
    error: string;
    location: string;
  }>;
  executionTime: number;  // seconds
  error?: string;
}

/**
 * SuperClaude Test Runner
 *
 * Executes SuperClaude /sc:test via Python integration
 * and returns test results with coverage data.
 */
export class SuperClaudeTestRunner {
  private pythonScriptPath: string;

  constructor() {
    // Path to Python integration script
    this.pythonScriptPath = path.join(__dirname, 'superclaude_test.py');
  }

  /**
   * Check if SuperClaude CLI is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      // Simple check: verify Python script exists
      const fs = require('fs');
      if (!fs.existsSync(this.pythonScriptPath)) {
        return false;
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Run tests using SuperClaude /sc:test
   *
   * @param options Test execution options
   * @returns Test results with coverage data
   */
  async runTests(options: SuperClaudeTestOptions): Promise<SuperClaudeTestResult> {
    const {
      targetFiles = [],
      testType = 'unit',
      coverage = true,
      watch = false,
      timeout = 120000  // 2 minutes default
    } = options;

    try {
      // Build arguments for Python script
      const args = [...targetFiles];

      args.push('--type', testType);

      if (coverage) {
        args.push('--coverage');
      }

      if (watch) {
        args.push('--watch');
      }

      args.push('--timeout', Math.floor(timeout / 1000).toString());

      // Execute Python script
      const result = await this.executePython(args, timeout);

      if (result.success && result.data) {
        return this.parseTestResult(result.data);
      } else {
        return {
          success: false,
          testResults: {
            passed: 0,
            failed: 0,
            skipped: 0,
            total: 0
          },
          coverage: {},
          failures: [],
          executionTime: 0,
          error: result.error || 'SuperClaude test execution failed'
        };
      }
    } catch (error) {
      return {
        success: false,
        testResults: {
          passed: 0,
          failed: 0,
          skipped: 0,
          total: 0
        },
        coverage: {},
        failures: [],
        executionTime: 0,
        error: `Unexpected error: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }

  /**
   * Execute Python script and capture output
   *
   * @param args Command-line arguments
   * @param timeout Timeout in milliseconds
   * @returns Execution result
   */
  private executePython(args: string[], timeout: number = 120000): Promise<{
    success: boolean;
    data?: any;
    error?: string;
  }> {
    return new Promise((resolve, reject) => {
      let stdout = '';
      let stderr = '';
      let timedOut = false;

      // Spawn Python process
      const pythonProcess = spawn('python3', [this.pythonScriptPath, ...args], {
        cwd: process.cwd(),
        stdio: ['pipe', 'pipe', 'pipe']
      });

      // Set timeout
      const timeoutId = setTimeout(() => {
        timedOut = true;
        pythonProcess.kill('SIGTERM');
        resolve({
          success: false,
          error: `Python script timed out after ${timeout}ms`
        });
      }, timeout);

      // Capture stdout
      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      // Capture stderr
      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      // Handle process exit
      pythonProcess.on('close', (code) => {
        clearTimeout(timeoutId);

        if (timedOut) {
          return;  // Already resolved with timeout error
        }

        // SuperClaude test returns exit code 1 if tests fail, which is expected
        if (code === 0 || code === 1) {
          // Parse JSON output
          try {
            // Extract JSON from stdout (filter out debug messages)
            const jsonMatch = stdout.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
              const data = JSON.parse(jsonMatch[0]);
              resolve({ success: true, data });
            } else {
              resolve({
                success: false,
                error: 'No JSON output found in Python script response'
              });
            }
          } catch (error) {
            resolve({
              success: false,
              error: `Failed to parse Python output: ${error instanceof Error ? error.message : String(error)}`
            });
          }
        } else {
          resolve({
            success: false,
            error: `Python script exited with code ${code}: ${stderr || stdout}`
          });
        }
      });

      // Handle process error
      pythonProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
    });
  }

  /**
   * Parse SuperClaude test result from Python output
   *
   * @param data Raw data from Python script
   * @returns Parsed test result
   */
  private parseTestResult(data: any): SuperClaudeTestResult {
    try {
      const { success, testResults, coverage, failures, executionTime, error } = data;

      return {
        success: success || false,
        testResults: {
          passed: testResults?.passed || 0,
          failed: testResults?.failed || 0,
          skipped: testResults?.skipped || 0,
          total: testResults?.total || 0
        },
        coverage: coverage || {},
        failures: failures || [],
        executionTime: executionTime || 0,
        error: error || undefined
      };
    } catch (error) {
      return {
        success: false,
        testResults: {
          passed: 0,
          failed: 0,
          skipped: 0,
          total: 0
        },
        coverage: {},
        failures: [],
        executionTime: 0,
        error: `Failed to parse SuperClaude result: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }
}

/**
 * Singleton instance
 */
let testRunnerInstance: SuperClaudeTestRunner | null = null;

/**
 * Get SuperClaude test runner instance
 */
export function getSuperClaudeTestRunner(): SuperClaudeTestRunner {
  if (!testRunnerInstance) {
    testRunnerInstance = new SuperClaudeTestRunner();
  }
  return testRunnerInstance;
}

/**
 * Convenience function to run tests
 */
export async function runTests(options: SuperClaudeTestOptions): Promise<SuperClaudeTestResult> {
  const runner = getSuperClaudeTestRunner();
  return runner.runTests(options);
}

/**
 * Check if SuperClaude test runner is available
 */
export async function isTestRunnerAvailable(): Promise<boolean> {
  const runner = getSuperClaudeTestRunner();
  return runner.isAvailable();
}
