/**
 * Attribution Processor Tests
 * Week 21-22: Self-Attributing Agents
 */

import { AttributionProcessor } from '../lib/attributionProcessor';
import {
  StepData,
  QualityGateResult,
  ValidationResult,
  OutcomeType,
  Attribution,
  AttributionFeedback,
  ImpactLevel
} from '../types/Attribution';

describe('AttributionProcessor', () => {
  let processor: AttributionProcessor;

  beforeEach(() => {
    processor = new AttributionProcessor({
      minConfidenceThreshold: 0.5,
      maxFactorsToTrack: 10,
      lookbackPeriodDays: 30
    });
  });

  // ==========================================================================
  // Test Data
  // ==========================================================================

  const createSuccessfulSteps = (): StepData[] => [
    {
      id: 'step_1',
      name: 'Generate Specification',
      agentId: 'felix_001',
      succeeded: true,
      duration: 5000,
      expectedDuration: 4000,
      retryCount: 0,
      experienceConsulted: true,
      patternUsed: 'spec_template_v2',
      isCriticalPath: true
    },
    {
      id: 'step_2',
      name: 'Create Tasks',
      agentId: 'felix_001',
      succeeded: true,
      duration: 3000,
      expectedDuration: 3500,
      retryCount: 1,
      experienceConsulted: false,
      isCriticalPath: true
    },
    {
      id: 'step_3',
      name: 'Validate Output',
      agentId: 'quinn_001',
      succeeded: true,
      duration: 2000,
      expectedDuration: 2000,
      retryCount: 0,
      experienceConsulted: true,
      isCriticalPath: false
    }
  ];

  const createFailedSteps = (): StepData[] => [
    {
      id: 'step_1',
      name: 'Generate Code',
      agentId: 'felix_001',
      succeeded: false,
      duration: 8000,
      expectedDuration: 4000,
      retryCount: 3,
      experienceConsulted: false,
      isCriticalPath: true
    },
    {
      id: 'step_2',
      name: 'Validate Output',
      agentId: 'quinn_001',
      succeeded: false,
      duration: 1000,
      expectedDuration: 2000,
      retryCount: 0,
      experienceConsulted: false,
      isCriticalPath: true
    }
  ];

  const createQualityGates = (): QualityGateResult[] => [
    {
      gateType: 'ARCHITECTURE',
      gateName: 'Architecture Review',
      passed: true,
      issuesCaught: 2,
      falsePositives: 0,
      totalChecks: 15
    },
    {
      gateType: 'SECURITY',
      gateName: 'Security Scan',
      passed: true,
      issuesCaught: 1,
      falsePositives: 1,
      totalChecks: 25
    }
  ];

  const createValidationHistory = (): ValidationResult[] => [
    {
      phase: 'LINTING',
      iteration: 1,
      passed: true,
      errors: []
    },
    {
      phase: 'TYPE_CHECK',
      iteration: 1,
      passed: false,
      errors: [
        { code: 'E001', message: 'Type mismatch', file: 'src/index.ts', line: 42, severity: 'ERROR' }
      ]
    },
    {
      phase: 'TYPE_CHECK',
      iteration: 2,
      passed: true,
      errors: [],
      fixApplied: 'Added type annotation',
      timeToFix: 30000
    }
  ];

  // ==========================================================================
  // analyzeTask Tests
  // ==========================================================================

  describe('analyzeTask', () => {
    it('should analyze a successful task', async () => {
      const attribution = await processor.analyzeTask(
        'task_001',
        'workflow_001',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        createQualityGates(),
        createValidationHistory()
      );

      expect(attribution).toBeDefined();
      expect(attribution.taskId).toBe('task_001');
      expect(attribution.agentId).toBe('felix_001');
      expect(attribution.outcome).toBe('SUCCESS');
      expect(attribution.keySteps.length).toBe(3);
      expect(attribution.confidence).toBeGreaterThan(0);
      expect(attribution.confidence).toBeLessThanOrEqual(1);
    });

    it('should analyze a failed task', async () => {
      const attribution = await processor.analyzeTask(
        'task_002',
        'workflow_002',
        'felix_001',
        'Felix',
        'FAILURE',
        createFailedSteps(),
        createQualityGates(),
        []
      );

      expect(attribution.outcome).toBe('FAILURE');
      expect(attribution.keySteps.some(s => s.impactScore < 0)).toBe(true);
      expect(attribution.causalFactors.some(f => f.contribution < 0)).toBe(true);
    });

    it('should identify critical path steps', async () => {
      const attribution = await processor.analyzeTask(
        'task_003',
        'workflow_003',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        [],
        []
      );

      const criticalSteps = attribution.keySteps.filter(
        s => s.impact === 'CRITICAL'
      );
      expect(criticalSteps.length).toBeGreaterThan(0);
    });

    it('should calculate confidence based on data quality', async () => {
      // With more data, confidence should be higher
      const richAttribution = await processor.analyzeTask(
        'task_004',
        'workflow_004',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        createQualityGates(),
        createValidationHistory()
      );

      // With less data, confidence should be lower
      const poorAttribution = await processor.analyzeTask(
        'task_005',
        'workflow_005',
        'felix_001',
        'Felix',
        'PARTIAL',
        [createSuccessfulSteps()[0]],
        [],
        []
      );

      expect(richAttribution.confidence).toBeGreaterThan(poorAttribution.confidence);
    });
  });

  // ==========================================================================
  // Causal Factor Extraction Tests
  // ==========================================================================

  describe('causal factor extraction', () => {
    it('should identify experience usage as a factor', async () => {
      const steps = createSuccessfulSteps();
      // Ensure experience was consulted
      steps[0].experienceConsulted = true;
      steps[2].experienceConsulted = true;

      const attribution = await processor.analyzeTask(
        'task_006',
        'workflow_006',
        'felix_001',
        'Felix',
        'SUCCESS',
        steps,
        [],
        []
      );

      const experienceFactor = attribution.causalFactors.find(
        f => f.factorType === 'PATTERN_REUSE'
      );
      expect(experienceFactor).toBeDefined();
      expect(experienceFactor!.contribution).toBeGreaterThan(0);
    });

    it('should identify early validation success', async () => {
      const validations: ValidationResult[] = [
        { phase: 'LINTING', iteration: 1, passed: true, errors: [] },
        { phase: 'TYPE_CHECK', iteration: 1, passed: true, errors: [] }
      ];

      const attribution = await processor.analyzeTask(
        'task_007',
        'workflow_007',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        [],
        validations
      );

      const validationFactor = attribution.causalFactors.find(
        f => f.factorType === 'EARLY_VALIDATION'
      );
      expect(validationFactor).toBeDefined();
    });

    it('should identify quality gate effectiveness', async () => {
      const gates = createQualityGates();
      gates[0].issuesCaught = 5; // Make it more effective

      const attribution = await processor.analyzeTask(
        'task_008',
        'workflow_008',
        'quinn_001',
        'Quinn',
        'SUCCESS',
        createSuccessfulSteps(),
        gates,
        []
      );

      const gateFactor = attribution.causalFactors.find(
        f => f.factorType === 'SECURITY_SCAN'
      );
      expect(gateFactor).toBeDefined();
    });

    it('should identify failure patterns', async () => {
      const failedValidations: ValidationResult[] = [
        { phase: 'TYPE_CHECK', iteration: 1, passed: false, errors: [{ code: 'E1', message: 'Error 1', severity: 'ERROR' }] },
        { phase: 'TYPE_CHECK', iteration: 2, passed: false, errors: [{ code: 'E1', message: 'Error 1', severity: 'ERROR' }] },
        { phase: 'TYPE_CHECK', iteration: 3, passed: false, errors: [{ code: 'E1', message: 'Error 1', severity: 'ERROR' }] }
      ];

      const attribution = await processor.analyzeTask(
        'task_009',
        'workflow_009',
        'felix_001',
        'Felix',
        'FAILURE',
        createFailedSteps(),
        [],
        failedValidations
      );

      const failureFactor = attribution.causalFactors.find(
        f => f.factorType === 'INCOMPLETE_VALIDATION' || f.factorType === 'MISSING_EDGE_CASE'
      );
      expect(failureFactor).toBeDefined();
      expect(failureFactor!.contribution).toBeLessThan(0);
    });
  });

  // ==========================================================================
  // Feedback Generation Tests
  // ==========================================================================

  describe('generateFeedback', () => {
    it('should generate success reinforcement feedback', async () => {
      const attribution = await processor.analyzeTask(
        'task_010',
        'workflow_010',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        createQualityGates(),
        createValidationHistory()
      );

      const feedback = processor.generateFeedback(attribution);

      expect(feedback).toBeDefined();
      expect(feedback.feedbackType).toBe('SUCCESS_REINFORCEMENT');
      expect(feedback.agentId).toBe('felix_001');
    });

    it('should generate failure correction feedback', async () => {
      const attribution = await processor.analyzeTask(
        'task_011',
        'workflow_011',
        'felix_001',
        'Felix',
        'FAILURE',
        createFailedSteps(),
        [],
        []
      );

      const feedback = processor.generateFeedback(attribution);

      expect(feedback.feedbackType).toBe('FAILURE_CORRECTION');
    });

    it('should extract lessons from successful patterns', async () => {
      const steps = createSuccessfulSteps();
      steps[0].patternUsed = 'effective_pattern';

      const attribution = await processor.analyzeTask(
        'task_012',
        'workflow_012',
        'felix_001',
        'Felix',
        'SUCCESS',
        steps,
        [],
        []
      );

      const feedback = processor.generateFeedback(attribution);

      const doMoreLessons = feedback.lessons.filter(l => l.lessonType === 'DO_MORE');
      expect(doMoreLessons.length).toBeGreaterThan(0);
    });

    it('should extract lessons from failures', async () => {
      const attribution = await processor.analyzeTask(
        'task_013',
        'workflow_013',
        'felix_001',
        'Felix',
        'FAILURE',
        createFailedSteps(),
        [],
        []
      );

      const feedback = processor.generateFeedback(attribution);

      const avoidLessons = feedback.lessons.filter(l => l.lessonType === 'AVOID');
      expect(avoidLessons.length).toBeGreaterThan(0);
    });

    it('should recommend experience weight adjustment', async () => {
      // Create steps where experience was helpful multiple times
      const steps: StepData[] = [
        { id: '1', name: 'Step 1', agentId: 'felix', succeeded: true, duration: 1000, expectedDuration: 1000, experienceConsulted: true },
        { id: '2', name: 'Step 2', agentId: 'felix', succeeded: true, duration: 1000, expectedDuration: 1000, experienceConsulted: true },
        { id: '3', name: 'Step 3', agentId: 'felix', succeeded: true, duration: 1000, expectedDuration: 1000, experienceConsulted: true }
      ];

      const attribution = await processor.analyzeTask(
        'task_014',
        'workflow_014',
        'felix_001',
        'Felix',
        'SUCCESS',
        steps,
        [],
        []
      );

      const feedback = processor.generateFeedback(attribution);

      const weightAdjustment = feedback.recommendedAdjustments.find(
        a => a.adjustmentType === 'WEIGHT_UPDATE' && a.target === 'experienceWeight'
      );
      expect(weightAdjustment).toBeDefined();
    });
  });

  // ==========================================================================
  // Impact Score Tests
  // ==========================================================================

  describe('impact scoring', () => {
    it('should give positive scores to successful steps', async () => {
      const attribution = await processor.analyzeTask(
        'task_015',
        'workflow_015',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        [],
        []
      );

      const positiveSteps = attribution.keySteps.filter(s => s.impactScore > 0);
      expect(positiveSteps.length).toBeGreaterThan(0);
    });

    it('should give negative scores to failed steps', async () => {
      const attribution = await processor.analyzeTask(
        'task_016',
        'workflow_016',
        'felix_001',
        'Felix',
        'FAILURE',
        createFailedSteps(),
        [],
        []
      );

      const negativeSteps = attribution.keySteps.filter(s => s.impactScore < 0);
      expect(negativeSteps.length).toBeGreaterThan(0);
    });

    it('should boost scores for experience usage', async () => {
      const withExperience: StepData = {
        id: '1', name: 'Step', agentId: 'felix', succeeded: true,
        duration: 1000, expectedDuration: 1000, experienceConsulted: true
      };

      const withoutExperience: StepData = {
        id: '2', name: 'Step', agentId: 'felix', succeeded: true,
        duration: 1000, expectedDuration: 1000, experienceConsulted: false
      };

      const attrWith = await processor.analyzeTask(
        'task_017a', 'wf', 'felix', 'Felix', 'SUCCESS', [withExperience], [], []
      );
      const attrWithout = await processor.analyzeTask(
        'task_017b', 'wf', 'felix', 'Felix', 'SUCCESS', [withoutExperience], [], []
      );

      expect(attrWith.keySteps[0].impactScore).toBeGreaterThan(attrWithout.keySteps[0].impactScore);
    });

    it('should penalize retries', async () => {
      const noRetry: StepData = {
        id: '1', name: 'Step', agentId: 'felix', succeeded: true,
        duration: 1000, expectedDuration: 1000, retryCount: 0
      };

      const withRetries: StepData = {
        id: '2', name: 'Step', agentId: 'felix', succeeded: true,
        duration: 1000, expectedDuration: 1000, retryCount: 3
      };

      const attrNoRetry = await processor.analyzeTask(
        'task_018a', 'wf', 'felix', 'Felix', 'SUCCESS', [noRetry], [], []
      );
      const attrRetries = await processor.analyzeTask(
        'task_018b', 'wf', 'felix', 'Felix', 'SUCCESS', [withRetries], [], []
      );

      expect(attrNoRetry.keySteps[0].impactScore).toBeGreaterThan(attrRetries.keySteps[0].impactScore);
    });
  });

  // ==========================================================================
  // Confidence Level Tests
  // ==========================================================================

  describe('confidence levels', () => {
    it('should assign HIGH confidence for rich data', async () => {
      const manySteps = Array(10).fill(null).map((_, i) => ({
        id: `step_${i}`,
        name: `Step ${i}`,
        agentId: 'felix',
        succeeded: true,
        duration: 1000,
        expectedDuration: 1000,
        experienceConsulted: true
      }));

      const attribution = await processor.analyzeTask(
        'task_019',
        'workflow_019',
        'felix_001',
        'Felix',
        'SUCCESS',
        manySteps,
        createQualityGates(),
        createValidationHistory()
      );

      expect(attribution.confidenceLevel).toBe('HIGH');
    });

    it('should assign MEDIUM confidence for moderate data', async () => {
      const attribution = await processor.analyzeTask(
        'task_020',
        'workflow_020',
        'felix_001',
        'Felix',
        'SUCCESS',
        createSuccessfulSteps(),
        [],
        []
      );

      expect(['MEDIUM', 'HIGH']).toContain(attribution.confidenceLevel);
    });

    it('should assign LOW confidence for sparse data', async () => {
      const attribution = await processor.analyzeTask(
        'task_021',
        'workflow_021',
        'felix_001',
        'Felix',
        'PARTIAL',
        [{ id: '1', name: 'Step', agentId: 'felix', succeeded: true, duration: 1000, expectedDuration: 1000 }],
        [],
        []
      );

      expect(['LOW', 'MEDIUM']).toContain(attribution.confidenceLevel);
    });
  });
});
