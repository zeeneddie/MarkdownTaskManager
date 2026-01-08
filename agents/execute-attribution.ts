#!/usr/bin/env npx ts-node
/**
 * Attribution Execution Script
 * Week 21-22: Self-Attributing Agents
 *
 * This script is called by the Python backend to analyze task outcomes
 * and generate attribution feedback.
 *
 * Usage:
 *   npx ts-node execute-attribution.ts analyze '{"taskId": "...", ...}'
 *   npx ts-node execute-attribution.ts feedback '{"attributionId": "...", ...}'
 */

import { AttributionProcessor } from './lib/attributionProcessor';
import {
  StepData,
  QualityGateResult,
  ValidationResult,
  OutcomeType,
  Attribution,
  AttributionFeedback
} from './types/Attribution';

// Initialize processor
const processor = new AttributionProcessor({
  chromaHost: process.env.CHROMA_HOST || 'localhost',
  chromaPort: parseInt(process.env.CHROMA_PORT || '8001'),
  minConfidenceThreshold: 0.5,
  maxFactorsToTrack: 10,
  lookbackPeriodDays: 30
});

// =============================================================================
// Input Interfaces
// =============================================================================

interface AnalyzeInput {
  taskId: string;
  workflowId: string;
  agentId: string;
  agentName: string;
  outcome: OutcomeType;
  steps: StepData[];
  qualityGateResults: QualityGateResult[];
  validationHistory: ValidationResult[];
}

interface FeedbackInput {
  attributionId: string;
  agentId: string;
  outcome: OutcomeType;
  keySteps: any[];
  causalFactors: any[];
  confidence: number;
}

// =============================================================================
// Command Handlers
// =============================================================================

async function analyzeTask(input: AnalyzeInput): Promise<Attribution> {
  console.error(`[Attribution] Analyzing task ${input.taskId} for agent ${input.agentName}`);

  // Convert snake_case to camelCase for steps
  const steps: StepData[] = input.steps.map(s => ({
    id: s.id || (s as any).step_id,
    name: s.name || (s as any).step_name,
    agentId: s.agentId || (s as any).agent_id,
    succeeded: s.succeeded,
    duration: s.duration,
    expectedDuration: s.expectedDuration || (s as any).expected_duration || s.duration,
    retryCount: s.retryCount || (s as any).retry_count || 0,
    experienceConsulted: s.experienceConsulted || (s as any).experience_consulted || false,
    patternUsed: s.patternUsed || (s as any).pattern_used,
    isCriticalPath: s.isCriticalPath || (s as any).is_critical_path || false
  }));

  // Convert quality gate results
  const qualityGates: QualityGateResult[] = input.qualityGateResults.map(g => ({
    gateType: g.gateType || (g as any).gate_type,
    gateName: g.gateName || (g as any).gate_name,
    passed: g.passed,
    issuesCaught: g.issuesCaught || (g as any).issues_caught || 0,
    falsePositives: g.falsePositives || (g as any).false_positives || 0,
    totalChecks: g.totalChecks || (g as any).total_checks || 0
  }));

  // Convert validation history
  const validations: ValidationResult[] = input.validationHistory.map(v => ({
    phase: v.phase,
    iteration: v.iteration,
    passed: v.passed,
    errors: (v.errors || []).map(e => ({
      code: e.code,
      message: e.message,
      file: e.file,
      line: e.line,
      severity: e.severity
    })),
    fixApplied: v.fixApplied || (v as any).fix_applied,
    timeToFix: v.timeToFix || (v as any).time_to_fix
  }));

  const attribution = await processor.analyzeTask(
    input.taskId,
    input.workflowId,
    input.agentId,
    input.agentName,
    input.outcome,
    steps,
    qualityGates,
    validations
  );

  console.error(`[Attribution] Analysis complete. Confidence: ${(attribution.confidence * 100).toFixed(1)}%`);
  return attribution;
}

function generateFeedback(input: FeedbackInput): AttributionFeedback {
  console.error(`[Attribution] Generating feedback for attribution ${input.attributionId}`);

  // Reconstruct a minimal attribution object for feedback generation
  const attribution: Attribution = {
    id: input.attributionId,
    taskId: '',
    workflowId: '',
    agentId: input.agentId,
    agentName: '',
    outcome: input.outcome,
    keySteps: input.keySteps,
    causalFactors: input.causalFactors,
    qualityGateResults: [],
    validationHistory: [],
    confidence: input.confidence,
    confidenceLevel: input.confidence >= 0.8 ? 'HIGH' : input.confidence >= 0.5 ? 'MEDIUM' : 'LOW',
    createdAt: new Date(),
    analyzedAt: new Date()
  };

  const feedback = processor.generateFeedback(attribution);
  console.error(`[Attribution] Feedback generated. Type: ${feedback.feedbackType}, Lessons: ${feedback.lessons.length}`);
  return feedback;
}

// =============================================================================
// Main Entry Point
// =============================================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: execute-attribution.ts <command> <json-input>');
    console.error('Commands: analyze, feedback');
    process.exit(1);
  }

  const command = args[0];
  let input: any;

  try {
    input = JSON.parse(args[1]);
  } catch (e) {
    console.error('Error parsing JSON input:', e);
    process.exit(1);
  }

  try {
    let result: any;

    switch (command) {
      case 'analyze':
        result = await analyzeTask(input as AnalyzeInput);
        break;

      case 'feedback':
        result = generateFeedback(input as FeedbackInput);
        break;

      default:
        console.error(`Unknown command: ${command}`);
        process.exit(1);
    }

    // Output result as JSON to stdout
    console.log(JSON.stringify(result, null, 2));

  } catch (error) {
    console.error('Error executing command:', error);
    process.exit(1);
  }
}

main().catch(console.error);
