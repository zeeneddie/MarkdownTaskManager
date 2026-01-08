/**
 * SuperClaude Analyzer - TypeScript Wrapper
 *
 * This module provides a TypeScript interface to the SuperClaude /sc:analyze
 * Python integration for use in the Quality Gates System.
 *
 * Week 6 Day 3 - SuperClaude Integration
 */

import { spawn } from 'child_process';
import * as path from 'path';
import { QualityFinding } from '../services/qualityGateService';

/**
 * Options for SuperClaude analysis
 */
export interface SuperClaudeAnalyzeOptions {
  targetFiles: string[];
  focus?: 'quality' | 'security' | 'performance' | 'architecture';
  depth?: 'quick' | 'deep';
  timeout?: number;  // milliseconds
}

/**
 * Result from SuperClaude analysis
 */
export interface SuperClaudeAnalyzeResult {
  success: boolean;
  findings: QualityFinding[];
  metrics: {
    overallScore: number;
    executionTime: number;
    filesAnalyzed: number;
  };
  error?: string;
}

/**
 * SuperClaude Analyzer
 *
 * Executes SuperClaude /sc:analyze via Python integration
 * and returns findings compatible with Quality Gates System.
 */
export class SuperClaudeAnalyzer {
  private pythonScriptPath: string;

  constructor() {
    // Path to Python integration script
    this.pythonScriptPath = path.join(__dirname, 'superclaude_analyze.py');
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
      // Python script will check for SuperClaude CLI availability
      // when actually running analysis
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Analyze code using SuperClaude /sc:analyze
   *
   * @param options Analysis options
   * @returns Analysis result with findings
   */
  async analyzeCode(options: SuperClaudeAnalyzeOptions): Promise<SuperClaudeAnalyzeResult> {
    const {
      targetFiles,
      focus = 'quality',
      depth = 'quick',
      timeout = 60000  // 60 seconds default
    } = options;

    // Validate inputs
    if (!targetFiles || targetFiles.length === 0) {
      return {
        success: false,
        findings: [],
        metrics: { overallScore: 0, executionTime: 0, filesAnalyzed: 0 },
        error: 'No target files provided'
      };
    }

    try {
      // Build arguments for Python script
      const args = [
        ...targetFiles,
        '--focus', focus,
        '--depth', depth,
        '--timeout', Math.floor(timeout / 1000).toString()  // Convert to seconds
      ];

      // Execute Python script
      const result = await this.executePython(args, timeout);

      if (result.success && result.data) {
        // Parse Python output
        return this.parseAnalyzeResult(result.data);
      } else {
        return {
          success: false,
          findings: [],
          metrics: { overallScore: 0, executionTime: 0, filesAnalyzed: 0 },
          error: result.error || 'SuperClaude analysis failed'
        };
      }
    } catch (error) {
      return {
        success: false,
        findings: [],
        metrics: { overallScore: 0, executionTime: 0, filesAnalyzed: 0 },
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
  private executePython(args: string[], timeout: number = 60000): Promise<{
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

        if (code === 0) {
          // Success - parse JSON output
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
   * Parse SuperClaude analyze result from Python output
   *
   * @param data Raw data from Python script
   * @returns Parsed analysis result
   */
  private parseAnalyzeResult(data: any): SuperClaudeAnalyzeResult {
    try {
      const { success, findings, metrics, error } = data;

      if (!success) {
        return {
          success: false,
          findings: [],
          metrics: metrics || { overallScore: 0, executionTime: 0, filesAnalyzed: 0 },
          error: error || 'SuperClaude analysis failed'
        };
      }

      // Convert findings to QualityFinding format
      const qualityFindings: QualityFinding[] = findings.map((f: any) => ({
        id: f.id || 'SC-UNKNOWN',
        category: f.category || 'code_smell',
        severity: f.severity || 'medium',
        title: f.title || 'Unknown issue',
        description: f.description || '',
        location: f.location || 'unknown',
        recommendation: f.recommendation || '',
        estimatedEffort: f.estimatedEffort || 2,
        riskIfNotFixed: f.riskIfNotFixed || 'medium',
        autoFixable: f.autoFixable || false,
        bestPractice: f.bestPractice || 'SuperClaude: Best Practices'
      }));

      return {
        success: true,
        findings: qualityFindings,
        metrics: {
          overallScore: metrics?.overallScore || 0,
          executionTime: metrics?.executionTime || 0,
          filesAnalyzed: metrics?.filesAnalyzed || 0
        }
      };
    } catch (error) {
      return {
        success: false,
        findings: [],
        metrics: { overallScore: 0, executionTime: 0, filesAnalyzed: 0 },
        error: `Failed to parse SuperClaude result: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }
}

/**
 * Singleton instance
 */
let analyzerInstance: SuperClaudeAnalyzer | null = null;

/**
 * Get SuperClaude analyzer instance
 */
export function getSuperClaudeAnalyzer(): SuperClaudeAnalyzer {
  if (!analyzerInstance) {
    analyzerInstance = new SuperClaudeAnalyzer();
  }
  return analyzerInstance;
}

/**
 * Convenience function to analyze code
 */
export async function analyzecode(options: SuperClaudeAnalyzeOptions): Promise<SuperClaudeAnalyzeResult> {
  const analyzer = getSuperClaudeAnalyzer();
  return analyzer.analyzeCode(options);
}

/**
 * Check if SuperClaude is available
 */
export async function isSuperClaudeAvailable(): Promise<boolean> {
  const analyzer = getSuperClaudeAnalyzer();
  return analyzer.isAvailable();
}
