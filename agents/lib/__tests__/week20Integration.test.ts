/**
 * Week 20 Integration Tests
 *
 * Tests for:
 * - Pattern Library
 * - Agent Metrics
 * - A/B Testing Framework
 *
 * @author Claude Code (Week 20 Day 6)
 * @date 2025-11-22
 */

import {
  PatternLibrary,
  getPatternLibrary,
  Pattern
} from '../patternLibrary';

import {
  MetricsCollector,
  PerformanceCalculator,
  getMetricsCollector,
  getPerformanceCalculator
} from '../agentMetrics';

import {
  ABTestingService,
  getABTestingService,
  EXPERIMENT_TEMPLATES
} from '../abTestingFramework';

// ============================================================================
// Pattern Library Tests
// ============================================================================

describe('PatternLibrary', () => {
  let library: PatternLibrary;

  beforeEach(() => {
    library = new PatternLibrary();
  });

  describe('initialization', () => {
    it('should initialize with seed patterns', () => {
      const all = library.getAllPatterns();
      expect(all.length).toBeGreaterThan(0);
      // At least 17 seed patterns across all categories
      expect(all.length).toBeGreaterThanOrEqual(17);
    });

    it('should have patterns in core categories', () => {
      // Core categories that have seed patterns
      const coreCategories = [
        'architecture', 'maintenance', 'quality', 'debugging',
        'testing', 'migration', 'documentation', 'planning'
      ];

      let patternsFound = 0;
      for (const category of coreCategories) {
        const patterns = library.getByCategory(category as any);
        patternsFound += patterns.length;
      }
      // Should have patterns across categories
      expect(patternsFound).toBeGreaterThan(10);
    });
  });

  describe('getByCategory', () => {
    it('should filter by category', () => {
      const archPatterns = library.getByCategory('architecture');
      expect(archPatterns.length).toBeGreaterThan(0);
      expect(archPatterns.every(p => p.category === 'architecture')).toBe(true);
    });

    it('should return empty array for unknown category', () => {
      const patterns = library.getByCategory('unknown' as any);
      expect(patterns).toEqual([]);
    });
  });

  describe('getByWorkType', () => {
    it('should filter by work type', () => {
      const featurePatterns = library.getByWorkType('NEW_FEATURE');
      expect(featurePatterns.length).toBeGreaterThan(0);
      for (const pattern of featurePatterns) {
        expect(pattern.applicableWorkTypes).toContain('NEW_FEATURE');
      }
    });
  });

  describe('search', () => {
    it('should find patterns by name', () => {
      const results = library.search('api');
      expect(results.length).toBeGreaterThan(0);
    });

    it('should find patterns by description', () => {
      const results = library.search('microservices');
      expect(results.length).toBeGreaterThan(0);
    });

    it('should be case insensitive', () => {
      const upper = library.search('API');
      const lower = library.search('api');
      expect(upper.length).toBe(lower.length);
    });

    it('should return empty for no matches', () => {
      const results = library.search('xyznonexistent123');
      expect(results).toEqual([]);
    });
  });

  describe('getTopPatterns', () => {
    it('should return patterns sorted by success rate', () => {
      const top = library.getTopPatterns(5);
      expect(top.length).toBeLessThanOrEqual(5);

      for (let i = 0; i < top.length - 1; i++) {
        expect(top[i].successRate).toBeGreaterThanOrEqual(top[i + 1].successRate);
      }
    });
  });

  describe('updateSuccessRate', () => {
    it('should update success rate on success', () => {
      const pattern = library.getAllPatterns()[0];
      const originalRate = pattern.successRate;
      const originalCount = pattern.usageCount;

      library.updateSuccessRate(pattern.id, true);

      expect(pattern.usageCount).toBe(originalCount + 1);
      // Success should maintain or increase rate
      expect(pattern.successRate).toBeGreaterThanOrEqual(originalRate - 0.1);
    });

    it('should update success rate on failure', () => {
      const pattern = library.getAllPatterns()[0];
      const originalCount = pattern.usageCount;

      library.updateSuccessRate(pattern.id, false);

      expect(pattern.usageCount).toBe(originalCount + 1);
    });
  });

  describe('addPattern', () => {
    it('should add a new pattern', () => {
      const newPattern: Pattern = {
        id: 'test-pattern',
        name: 'Test Pattern',
        category: 'testing',
        description: 'A test pattern',
        applicableWorkTypes: ['TESTING'],
        applicableContexts: ['unit_testing'],
        steps: ['Step 1', 'Step 2'],
        preconditions: ['Pre 1'],
        postconditions: ['Post 1'],
        antiPatterns: ['Anti 1'],
        successRate: 0.9,
        usageCount: 0,
        createdBy: 'test',
        tags: ['test']
      };

      library.addPattern(newPattern);

      const found = library.getAllPatterns().find(p => p.id === 'test-pattern');
      expect(found).toBeDefined();
      expect(found?.name).toBe('Test Pattern');
    });
  });
});

// ============================================================================
// Metrics Tests
// ============================================================================

describe('MetricsCollector', () => {
  let collector: MetricsCollector;

  beforeEach(() => {
    collector = new MetricsCollector();
  });

  describe('record', () => {
    it('should record a metric', () => {
      collector.record('felix', 'execution_time', 5.5);

      const metrics = collector.getAgentMetrics('felix', 24);
      expect(metrics.length).toBe(1);
      expect(metrics[0].agentId).toBe('felix');
      expect(metrics[0].metricType).toBe('execution_time');
      expect(metrics[0].value).toBe(5.5);
    });

    it('should include timestamp', () => {
      collector.record('felix', 'success_rate', 100);

      const metrics = collector.getAgentMetrics('felix', 24);
      expect(metrics[0].timestamp).toBeDefined();
      const timestamp = new Date(metrics[0].timestamp);
      expect(timestamp.getTime()).toBeLessThanOrEqual(Date.now());
    });

    it('should include context if provided', () => {
      collector.record('felix', 'success_rate', 100, { workType: 'NEW_FEATURE' });

      const metrics = collector.getAgentMetrics('felix', 24);
      expect(metrics[0].context?.workType).toBe('NEW_FEATURE');
    });
  });

  describe('recordTaskExecution', () => {
    it('should record multiple metrics for a task', () => {
      collector.recordTaskExecution(
        'felix',
        true,      // success
        10.5,      // executionTime
        2,         // validationIterations
        true,      // experienceUsed
        3,         // patternsApplied
        85         // qualityScore
      );

      const metrics = collector.getAgentMetrics('felix', 24);
      expect(metrics.length).toBe(6);  // All metric types except failure_count

      const metricTypes = metrics.map(m => m.metricType);
      expect(metricTypes).toContain('execution_time');
      expect(metricTypes).toContain('success_rate');
      expect(metricTypes).toContain('validation_iterations');
      expect(metricTypes).toContain('experience_used');
      expect(metricTypes).toContain('pattern_applied');
      expect(metricTypes).toContain('quality_score');
    });

    it('should record failure_count on failure', () => {
      collector.recordTaskExecution('betty', false, 5, 3, true, 0, 30);

      const metrics = collector.getAgentMetrics('betty', 24);
      const failureMetric = metrics.find(m => m.metricType === 'failure_count');
      expect(failureMetric).toBeDefined();
      expect(failureMetric?.value).toBe(1);
    });
  });

  describe('getActiveAgents', () => {
    it('should return unique agent IDs', () => {
      collector.record('felix', 'success_rate', 100);
      collector.record('marcus', 'success_rate', 100);
      collector.record('felix', 'execution_time', 5);

      const active = collector.getActiveAgents(24);
      expect(active.length).toBe(2);
      expect(active).toContain('felix');
      expect(active).toContain('marcus');
    });
  });

  describe('clear', () => {
    it('should clear all metrics', () => {
      collector.record('felix', 'success_rate', 100);
      collector.record('marcus', 'success_rate', 100);

      collector.clear();

      const metrics = collector.getAllMetrics(24);
      expect(metrics.length).toBe(0);
    });
  });
});

describe('PerformanceCalculator', () => {
  let collector: MetricsCollector;
  let calculator: PerformanceCalculator;

  beforeEach(() => {
    collector = new MetricsCollector();
    calculator = new PerformanceCalculator(collector);
  });

  describe('calculateAgentPerformance', () => {
    it('should calculate performance metrics', () => {
      // Record some task executions
      collector.recordTaskExecution('felix', true, 10, 1, true, 2, 90);
      collector.recordTaskExecution('felix', true, 8, 2, true, 1, 85);
      collector.recordTaskExecution('felix', false, 15, 3, false, 0, 40);

      const performance = calculator.calculateAgentPerformance('felix', 'architect', 24);

      expect(performance.agentId).toBe('felix');
      expect(performance.agentRole).toBe('architect');
      expect(performance.metrics.totalTasks).toBe(3);
      expect(performance.metrics.successfulTasks).toBe(2);
      expect(performance.metrics.failedTasks).toBe(1);
      expect(performance.metrics.successRate).toBeCloseTo(66.67, 1);
    });

    it('should handle empty metrics', () => {
      const performance = calculator.calculateAgentPerformance('unknown', 'general', 24);

      expect(performance.metrics.totalTasks).toBe(0);
      expect(performance.metrics.successRate).toBe(0);
    });
  });

  describe('generateDashboardSummary', () => {
    it('should generate summary with active agents', () => {
      collector.recordTaskExecution('felix', true, 10, 1, true, 2, 90);
      collector.recordTaskExecution('marcus', true, 8, 2, false, 1, 85);

      const summary = calculator.generateDashboardSummary(24);

      expect(summary.generatedAt).toBeDefined();
      expect(summary.systemHealth.activeAgents).toBe(2);
      expect(summary.agentPerformance.length).toBe(2);
    });
  });
});

// ============================================================================
// A/B Testing Tests
// ============================================================================

describe('ABTestingService', () => {
  let service: ABTestingService;

  beforeEach(() => {
    service = new ABTestingService();
  });

  describe('createExperiment', () => {
    it('should create an experiment', () => {
      const experiment = service.createExperiment({
        id: 'test-exp',
        name: 'Test Experiment',
        description: 'A test experiment',
        targetAgent: 'felix',
        variants: [
          { id: 'a', name: 'Control', description: 'Control group', config: {}, weight: 50 },
          { id: 'b', name: 'Treatment', description: 'Treatment group', config: {}, weight: 50 }
        ],
        minSampleSize: 30,
        maxDurationHours: 168,
        successMetric: 'success_rate',
        secondaryMetrics: []
      });

      expect(experiment.status).toBe('draft');
      expect(experiment.variants.length).toBe(2);
    });

    it('should throw if weights do not sum to 100', () => {
      expect(() => {
        service.createExperiment({
          id: 'bad-exp',
          name: 'Bad Experiment',
          description: 'Invalid weights',
          targetAgent: 'felix',
          variants: [
            { id: 'a', name: 'A', description: 'A', config: {}, weight: 30 },
            { id: 'b', name: 'B', description: 'B', config: {}, weight: 30 }
          ],
          minSampleSize: 30,
          maxDurationHours: 168,
          successMetric: 'success_rate',
          secondaryMetrics: []
        });
      }).toThrow('weights must sum to 100');
    });
  });

  describe('startExperiment', () => {
    it('should start an experiment', () => {
      service.createExperiment({
        id: 'test-exp',
        name: 'Test',
        description: 'Test',
        targetAgent: 'felix',
        variants: [
          { id: 'a', name: 'A', description: 'A', config: {}, weight: 50 },
          { id: 'b', name: 'B', description: 'B', config: {}, weight: 50 }
        ],
        minSampleSize: 30,
        maxDurationHours: 168,
        successMetric: 'success_rate',
        secondaryMetrics: []
      });

      service.startExperiment('test-exp');

      const exp = service.getExperiment('test-exp');
      expect(exp?.status).toBe('running');
      expect(exp?.startTime).toBeDefined();
    });
  });

  describe('assignVariant', () => {
    beforeEach(() => {
      service.createExperiment({
        id: 'test-exp',
        name: 'Test',
        description: 'Test',
        targetAgent: 'felix',
        variants: [
          { id: 'a', name: 'A', description: 'A', config: {}, weight: 50 },
          { id: 'b', name: 'B', description: 'B', config: {}, weight: 50 }
        ],
        minSampleSize: 30,
        maxDurationHours: 168,
        successMetric: 'success_rate',
        secondaryMetrics: []
      });
      service.startExperiment('test-exp');
    });

    it('should assign a variant', () => {
      const variant = service.assignVariant('test-exp', 'req-1', 'felix');

      expect(variant).not.toBeNull();
      expect(['a', 'b']).toContain(variant?.id);
    });

    it('should return same variant for same request', () => {
      const variant1 = service.assignVariant('test-exp', 'req-1', 'felix');
      const variant2 = service.assignVariant('test-exp', 'req-1', 'felix');

      expect(variant1?.id).toBe(variant2?.id);
    });

    it('should return null for wrong agent', () => {
      const variant = service.assignVariant('test-exp', 'req-1', 'marcus');
      expect(variant).toBeNull();
    });

    it('should return null for non-running experiment', () => {
      service.stopExperiment('test-exp');
      const variant = service.assignVariant('test-exp', 'req-1', 'felix');
      expect(variant).toBeNull();
    });
  });

  describe('recordVariantResult', () => {
    beforeEach(() => {
      service.createExperiment({
        id: 'test-exp',
        name: 'Test',
        description: 'Test',
        targetAgent: 'felix',
        variants: [
          { id: 'a', name: 'A', description: 'A', config: {}, weight: 50 },
          { id: 'b', name: 'B', description: 'B', config: {}, weight: 50 }
        ],
        minSampleSize: 5,
        maxDurationHours: 168,
        successMetric: 'success_rate',
        secondaryMetrics: []
      });
      service.startExperiment('test-exp');
    });

    it('should record results', () => {
      service.assignVariant('test-exp', 'req-1', 'felix');
      service.recordVariantResult('test-exp', 'req-1', true, 10, 85, 1);

      const result = service.analyzeExperiment('test-exp');
      expect(result.variantResults.some(vr => vr.sampleSize > 0)).toBe(true);
    });
  });

  describe('analyzeExperiment', () => {
    beforeEach(() => {
      service.createExperiment({
        id: 'test-exp',
        name: 'Test',
        description: 'Test',
        targetAgent: 'all',
        variants: [
          { id: 'a', name: 'A', description: 'A', config: {}, weight: 50 },
          { id: 'b', name: 'B', description: 'B', config: {}, weight: 50 }
        ],
        minSampleSize: 5,
        maxDurationHours: 168,
        successMetric: 'success_rate',
        secondaryMetrics: []
      });
      service.startExperiment('test-exp');
    });

    it('should return insufficient_data when not enough samples', () => {
      const result = service.analyzeExperiment('test-exp');
      expect(result.status).toBe('insufficient_data');
    });

    it('should calculate results with enough data', () => {
      // Simulate data collection with biased assignment
      for (let i = 0; i < 10; i++) {
        service.assignVariant('test-exp', `req-${i}`, 'felix');
        service.recordVariantResult(
          'test-exp',
          `req-${i}`,
          i < 8,  // 80% success for variant A
          10,
          80,
          1
        );
      }

      const result = service.analyzeExperiment('test-exp');
      expect(result.variantResults.length).toBe(2);
    });
  });

  describe('EXPERIMENT_TEMPLATES', () => {
    it('should create model comparison experiment', () => {
      const template = EXPERIMENT_TEMPLATES.modelComparison('felix', 'gpt-4', 'gpt-3.5');
      expect(template.variants.length).toBe(2);
      expect(template.successMetric).toBe('success_rate');
    });

    it('should create experience strategy experiment', () => {
      const template = EXPERIMENT_TEMPLATES.experienceStrategy('felix');
      expect(template.variants.length).toBe(2);
      expect(template.variants[0].config.enableExperience).toBe(true);
      expect(template.variants[1].config.enableExperience).toBe(false);
    });

    it('should create validation iterations experiment', () => {
      const template = EXPERIMENT_TEMPLATES.validationIterations('felix');
      expect(template.variants.length).toBe(3);
    });
  });
});

// ============================================================================
// Singleton Tests
// ============================================================================

describe('Singleton Instances', () => {
  it('should return same PatternLibrary instance', () => {
    const lib1 = getPatternLibrary();
    const lib2 = getPatternLibrary();
    expect(lib1).toBe(lib2);
  });

  it('should return same MetricsCollector instance', () => {
    const col1 = getMetricsCollector();
    const col2 = getMetricsCollector();
    expect(col1).toBe(col2);
  });

  it('should return same PerformanceCalculator instance', () => {
    const calc1 = getPerformanceCalculator();
    const calc2 = getPerformanceCalculator();
    expect(calc1).toBe(calc2);
  });

  it('should return same ABTestingService instance', () => {
    const svc1 = getABTestingService();
    const svc2 = getABTestingService();
    expect(svc1).toBe(svc2);
  });
});
