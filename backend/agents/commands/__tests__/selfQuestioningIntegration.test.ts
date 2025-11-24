/**
 * Self-Questioning Integration Tests
 *
 * Tests the complete integration of:
 * 1. Self-Questioning Engine (question generation)
 * 2. Synthetic Task Generation
 * 3. Edge Case Discovery
 * 4. Self-Training Workflow
 *
 * Week 23-24 - Self-Questioning Agents
 */

import {
  SelfQuestioningEngine,
  QuestionCategory,
  TaskDifficulty,
  SelfQuestion,
  SyntheticTask,
  EdgeCase,
  AgentName
} from '../../lib/selfQuestioningEngine';

import {
  SelfTrainingWorkflow,
  TrainingSessionConfig,
  TrainingSessionResult
} from '../../workflows/selfTrainingWorkflow';

// Training modes enum
enum TrainingMode {
  BALANCED = 'balanced',
  INTENSIVE = 'intensive',
  FOCUSED = 'focused'
}

// Training stages enum
enum TrainingStage {
  DATA_COLLECTION = 'DATA_COLLECTION',
  SELF_QUESTIONING = 'SELF_QUESTIONING',
  TASK_GENERATION = 'TASK_GENERATION',
  TRAINING_EXECUTION = 'TRAINING_EXECUTION',
  EVALUATION = 'EVALUATION'
}

// Mock performance data for testing
const mockPerformanceData = {
  agent_id: 'felix',
  success_rate: 0.75,
  total_tasks: 100,
  failed_tasks: 25,
  common_failure_categories: ['architecture_complexity', 'edge_cases', 'requirements_ambiguity'],
  average_confidence: 0.68,
  recent_trend: 'improving' as const
};

const mockRecentTasks = [
  {
    task_id: 'task_001',
    task_type: 'NEW_FEATURE',
    outcome: 'SUCCESS' as const,
    complexity: 'high',
    duration_minutes: 45,
    quality_score: 0.85
  },
  {
    task_id: 'task_002',
    task_type: 'NEW_FEATURE',
    outcome: 'FAILURE' as const,
    complexity: 'high',
    duration_minutes: 60,
    quality_score: 0.45,
    failure_reason: 'Missed edge case in authentication flow'
  },
  {
    task_id: 'task_003',
    task_type: 'ARCHITECTURE',
    outcome: 'PARTIAL' as const,
    complexity: 'medium',
    duration_minutes: 30,
    quality_score: 0.65
  }
];

// ========================================
// TEST SUITE 1: Self-Questioning Engine
// ========================================

describe('Self-Questioning Engine', () => {
  let engine: SelfQuestioningEngine;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
  });

  test('Engine initializes with question templates', () => {
    expect(engine).toBeDefined();
    const templates = engine.getTemplatesForAgent('felix');
    expect(templates.length).toBeGreaterThan(0);
  });

  test('Generates questions from performance data', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    expect(questions).toBeDefined();
    expect(Array.isArray(questions)).toBe(true);
    expect(questions.length).toBeGreaterThan(0);
    expect(questions.length).toBeLessThanOrEqual(5);

    // Verify question structure
    questions.forEach((q: SelfQuestion) => {
      expect(q.question_id).toBeDefined();
      expect(q.agent_id).toBe('felix');
      expect(q.question_text).toBeDefined();
      expect(q.category).toBeDefined();
      expect(q.difficulty).toBeDefined();
      expect(q.generated_at).toBeDefined();
    });
  });

  test('Questions target failure areas', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 10
    });

    // At least one question should address the failure categories
    const relevantCategories = ['ARCHITECTURE', 'EDGE_CASES', 'REQUIREMENTS'];
    const hasRelevantQuestions = questions.some((q: SelfQuestion) =>
      relevantCategories.includes(q.category)
    );

    expect(hasRelevantQuestions).toBe(true);
  });

  test('Generates questions for all 10 agents', async () => {
    const agents = ['felix', 'marcus', 'quinn', 'betty', 'eliza', 'tessa', 'miguel', 'diana', 'peter', 'paul'];

    for (const agentId of agents) {
      const questions = await engine.generateQuestions({
        agentId,
        performanceData: { ...mockPerformanceData, agent_id: agentId },
        recentTasks: mockRecentTasks,
        maxQuestions: 3
      });

      expect(questions.length).toBeGreaterThan(0);
      questions.forEach((q: SelfQuestion) => {
        expect(q.agent_id).toBe(agentId);
      });
    }
  });

  test('Question difficulty matches performance level', async () => {
    // High-performing agent should get harder questions
    const highPerformanceData = {
      ...mockPerformanceData,
      success_rate: 0.95,
      average_confidence: 0.9
    };

    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: highPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    // Should have harder questions for high performers
    const hardQuestions = questions.filter((q: SelfQuestion) =>
      q.difficulty === 'hard' || q.difficulty === 'extreme'
    );

    expect(hardQuestions.length).toBeGreaterThan(0);
  });
});

// ========================================
// TEST SUITE 2: Synthetic Task Generation
// ========================================

describe('Synthetic Task Generation', () => {
  let engine: SelfQuestioningEngine;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
  });

  test('Generates tasks from questions', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 3
    });

    const tasks = await engine.generateTrainingTasks({
      agentId: 'felix',
      questions,
      maxTasks: 5
    });

    expect(tasks).toBeDefined();
    expect(Array.isArray(tasks)).toBe(true);
    expect(tasks.length).toBeGreaterThan(0);

    // Verify task structure
    tasks.forEach((task: SyntheticTask) => {
      expect(task.task_id).toBeDefined();
      expect(task.agent_id).toBe('felix');
      expect(task.task_name).toBeDefined();
      expect(task.description).toBeDefined();
      expect(task.source_question_id).toBeDefined();
      expect(task.expected_outcome).toBeDefined();
      expect(task.validation_criteria).toBeDefined();
    });
  });

  test('Tasks inherit difficulty from questions', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 3
    });

    const tasks = await engine.generateTrainingTasks({
      agentId: 'felix',
      questions,
      maxTasks: 5
    });

    // Tasks should have complexity levels
    tasks.forEach((task: SyntheticTask) => {
      expect(['easy', 'medium', 'hard', 'extreme']).toContain(task.complexity);
    });
  });

  test('Tasks have validation criteria', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 2
    });

    const tasks = await engine.generateTrainingTasks({
      agentId: 'felix',
      questions,
      maxTasks: 3
    });

    tasks.forEach((task: SyntheticTask) => {
      expect(task.validation_criteria).toBeDefined();
      expect(Array.isArray(task.validation_criteria)).toBe(true);
      expect(task.validation_criteria.length).toBeGreaterThan(0);
    });
  });
});

// ========================================
// TEST SUITE 3: Edge Case Discovery
// ========================================

describe('Edge Case Discovery', () => {
  let engine: SelfQuestioningEngine;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
  });

  test('Discovers edge cases from recent work patterns', async () => {
    const edgeCases = await engine.discoverEdgeCases({
      agentId: 'felix',
      recentTasks: mockRecentTasks,
      failureAnalysis: {
        common_errors: ['null_pointer', 'race_condition', 'timeout'],
        error_contexts: ['authentication', 'database', 'api_calls']
      }
    });

    expect(edgeCases).toBeDefined();
    expect(Array.isArray(edgeCases)).toBe(true);
  });

  test('Edge cases have required properties', async () => {
    const edgeCases = await engine.discoverEdgeCases({
      agentId: 'felix',
      recentTasks: mockRecentTasks,
      failureAnalysis: {
        common_errors: ['timeout'],
        error_contexts: ['api_calls']
      }
    });

    edgeCases.forEach((ec: EdgeCase) => {
      expect(ec.edge_case_id).toBeDefined();
      expect(ec.agent_id).toBe('felix');
      expect(ec.edge_case_type).toBeDefined();
      expect(ec.description).toBeDefined();
      expect(ec.pattern_source).toBeDefined();
      expect(ec.discovered_at).toBeDefined();
    });
  });

  test('Edge cases are categorized by type', async () => {
    const edgeCases = await engine.discoverEdgeCases({
      agentId: 'quinn', // Quality agent
      recentTasks: mockRecentTasks,
      failureAnalysis: {
        common_errors: ['sql_injection', 'xss', 'auth_bypass'],
        error_contexts: ['user_input', 'api_endpoints']
      }
    });

    const validTypes = ['ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'DATA', 'INTEGRATION', 'USER_INPUT', 'CONCURRENCY', 'EDGE_BOUNDARY'];
    edgeCases.forEach((ec: EdgeCase) => {
      expect(validTypes).toContain(ec.edge_case_type);
    });
  });
});

// ========================================
// TEST SUITE 4: Questioning Session
// ========================================

describe('Questioning Session', () => {
  let engine: SelfQuestioningEngine;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
  });

  test('Runs complete questioning session', async () => {
    const sessionInput: QuestioningSessionInput = {
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 5,
      maxTasks: 3,
      discoverEdgeCases: true
    };

    const session = await engine.runSession(sessionInput);

    expect(session).toBeDefined();
    expect(session.session_id).toBeDefined();
    expect(session.agent_id).toBe('felix');
    expect(session.questions).toBeDefined();
    expect(session.tasks).toBeDefined();
    expect(session.edge_cases).toBeDefined();
    expect(session.started_at).toBeDefined();
    expect(session.status).toBeDefined();
  });

  test('Session tracks status correctly', async () => {
    const session = await engine.runSession({
      agentId: 'marcus',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 3,
      maxTasks: 2,
      discoverEdgeCases: false
    });

    expect(['ACTIVE', 'COMPLETED', 'PAUSED']).toContain(session.status);
  });

  test('Session generates insights', async () => {
    const session = await engine.runSession({
      agentId: 'quinn',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 5,
      maxTasks: 3,
      discoverEdgeCases: true
    });

    expect(session.insights).toBeDefined();
    expect(Array.isArray(session.insights)).toBe(true);
  });
});

// ========================================
// TEST SUITE 5: Self-Training Workflow
// ========================================

describe('Self-Training Workflow', () => {
  let workflow: SelfTrainingWorkflow;

  beforeEach(() => {
    workflow = new SelfTrainingWorkflow();
  });

  test('Workflow initializes correctly', () => {
    expect(workflow).toBeDefined();
    expect(workflow.getStatus()).toBe('IDLE');
  });

  test('Starts training session for agent', async () => {
    const sessionInput: TrainingSessionInput = {
      agentId: 'felix',
      mode: TrainingMode.BALANCED,
      maxQuestions: 5,
      maxTasks: 3,
      autoAdvance: false
    };

    const session = await workflow.startSession(sessionInput);

    expect(session).toBeDefined();
    expect(session.session_id).toBeDefined();
    expect(session.agent_id).toBe('felix');
    expect(session.mode).toBe(TrainingMode.BALANCED);
    expect(session.current_stage).toBeDefined();
  });

  test('Training modes affect intensity', async () => {
    const intensiveSession = await workflow.startSession({
      agentId: 'quinn',
      mode: TrainingMode.INTENSIVE,
      maxQuestions: 10,
      maxTasks: 8,
      autoAdvance: false
    });

    const focusedSession = await workflow.startSession({
      agentId: 'betty',
      mode: TrainingMode.FOCUSED,
      maxQuestions: 3,
      maxTasks: 2,
      autoAdvance: false
    });

    expect(intensiveSession.config.maxQuestions).toBeGreaterThan(focusedSession.config.maxQuestions);
  });

  test('Training workflow has 5 stages', async () => {
    const session = await workflow.startSession({
      agentId: 'eliza',
      mode: TrainingMode.BALANCED,
      maxQuestions: 3,
      maxTasks: 2,
      autoAdvance: true
    });

    const expectedStages = [
      TrainingStage.DATA_COLLECTION,
      TrainingStage.SELF_QUESTIONING,
      TrainingStage.TASK_GENERATION,
      TrainingStage.TRAINING_EXECUTION,
      TrainingStage.EVALUATION
    ];

    expect(session.stages).toBeDefined();
    expect(Object.keys(session.stages).length).toBe(5);

    expectedStages.forEach(stage => {
      expect(session.stages[stage]).toBeDefined();
    });
  });

  test('Training execution validates tasks', async () => {
    const session = await workflow.startSession({
      agentId: 'tessa',
      mode: TrainingMode.FOCUSED,
      maxQuestions: 2,
      maxTasks: 2,
      autoAdvance: true
    });

    // Wait for session to complete or timeout
    const result = await workflow.executeTrainingTasks(session.session_id);

    expect(result).toBeDefined();
    expect(result.tasks_attempted).toBeGreaterThanOrEqual(0);
    expect(result.tasks_passed).toBeGreaterThanOrEqual(0);
    expect(result.validation_results).toBeDefined();
  }, 30000); // 30 second timeout

  test('Evaluation generates recommendations', async () => {
    const session = await workflow.startSession({
      agentId: 'miguel',
      mode: TrainingMode.BALANCED,
      maxQuestions: 3,
      maxTasks: 2,
      autoAdvance: true
    });

    await workflow.executeTrainingTasks(session.session_id);
    const evaluation = await workflow.evaluateSession(session.session_id);

    expect(evaluation).toBeDefined();
    expect(evaluation.improvement_score).toBeDefined();
    expect(evaluation.insights).toBeDefined();
    expect(evaluation.recommendations).toBeDefined();
    expect(Array.isArray(evaluation.recommendations)).toBe(true);
  }, 30000);
});

// ========================================
// TEST SUITE 6: Data Flow Integrity
// ========================================

describe('Self-Questioning Data Flow', () => {
  let engine: SelfQuestioningEngine;
  let workflow: SelfTrainingWorkflow;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
    workflow = new SelfTrainingWorkflow();
  });

  test('Questions flow to task generation', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 3
    });

    const tasks = await engine.generateTrainingTasks({
      agentId: 'felix',
      questions,
      maxTasks: 5
    });

    // Each task should reference a source question
    tasks.forEach((task: SyntheticTask) => {
      const sourceQuestion = questions.find((q: SelfQuestion) => q.question_id === task.source_question_id);
      expect(sourceQuestion).toBeDefined();
    });
  });

  test('Performance data influences question categories', async () => {
    // Agent with security failures should get security questions
    const securityFailureData = {
      ...mockPerformanceData,
      agent_id: 'quinn',
      common_failure_categories: ['security_vulnerabilities', 'input_validation']
    };

    const questions = await engine.generateQuestions({
      agentId: 'quinn',
      performanceData: securityFailureData,
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    const securityQuestions = questions.filter((q: SelfQuestion) =>
      q.category === 'SECURITY' || q.question_text.toLowerCase().includes('security')
    );

    expect(securityQuestions.length).toBeGreaterThan(0);
  });

  test('Training results update metrics', async () => {
    const session = await workflow.startSession({
      agentId: 'diana',
      mode: TrainingMode.FOCUSED,
      maxQuestions: 2,
      maxTasks: 1,
      autoAdvance: true
    });

    await workflow.executeTrainingTasks(session.session_id);
    const evaluation = await workflow.evaluateSession(session.session_id);

    // Metrics should be updated
    expect(evaluation.metrics_updated).toBe(true);
    expect(evaluation.new_baseline).toBeDefined();
  }, 30000);
});

// ========================================
// TEST SUITE 7: Agent-Specific Behavior
// ========================================

describe('Agent-Specific Question Generation', () => {
  let engine: SelfQuestioningEngine;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
  });

  test('Felix gets architecture questions', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: { ...mockPerformanceData, agent_id: 'felix' },
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    const architectureQuestions = questions.filter((q: SelfQuestion) =>
      q.category === 'ARCHITECTURE' ||
      q.question_text.toLowerCase().includes('design') ||
      q.question_text.toLowerCase().includes('pattern')
    );

    expect(architectureQuestions.length).toBeGreaterThan(0);
  });

  test('Quinn gets security questions', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'quinn',
      performanceData: { ...mockPerformanceData, agent_id: 'quinn' },
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    const securityQuestions = questions.filter((q: SelfQuestion) =>
      q.category === 'SECURITY' ||
      q.question_text.toLowerCase().includes('security') ||
      q.question_text.toLowerCase().includes('vulnerability')
    );

    expect(securityQuestions.length).toBeGreaterThan(0);
  });

  test('Betty gets debugging questions', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'betty',
      performanceData: { ...mockPerformanceData, agent_id: 'betty' },
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    const debuggingQuestions = questions.filter((q: SelfQuestion) =>
      q.category === 'DEBUGGING' ||
      q.question_text.toLowerCase().includes('bug') ||
      q.question_text.toLowerCase().includes('error') ||
      q.question_text.toLowerCase().includes('debug')
    );

    expect(debuggingQuestions.length).toBeGreaterThan(0);
  });

  test('Eliza gets estimation questions', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'eliza',
      performanceData: { ...mockPerformanceData, agent_id: 'eliza' },
      recentTasks: mockRecentTasks,
      maxQuestions: 5
    });

    const estimationQuestions = questions.filter((q: SelfQuestion) =>
      q.category === 'ESTIMATION' ||
      q.question_text.toLowerCase().includes('estimate') ||
      q.question_text.toLowerCase().includes('complexity') ||
      q.question_text.toLowerCase().includes('effort')
    );

    expect(estimationQuestions.length).toBeGreaterThan(0);
  });
});

// ========================================
// TEST SUITE 8: Error Handling
// ========================================

describe('Self-Questioning Error Handling', () => {
  let engine: SelfQuestioningEngine;
  let workflow: SelfTrainingWorkflow;

  beforeEach(() => {
    engine = new SelfQuestioningEngine();
    workflow = new SelfTrainingWorkflow();
  });

  test('Handles unknown agent gracefully', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'unknown_agent',
      performanceData: mockPerformanceData,
      recentTasks: mockRecentTasks,
      maxQuestions: 3
    });

    // Should still generate generic questions
    expect(questions).toBeDefined();
    expect(Array.isArray(questions)).toBe(true);
  });

  test('Handles empty performance data', async () => {
    const questions = await engine.generateQuestions({
      agentId: 'felix',
      performanceData: {
        agent_id: 'felix',
        success_rate: 0,
        total_tasks: 0,
        failed_tasks: 0,
        common_failure_categories: [],
        average_confidence: 0,
        recent_trend: 'stable' as const
      },
      recentTasks: [],
      maxQuestions: 3
    });

    expect(questions).toBeDefined();
    expect(Array.isArray(questions)).toBe(true);
  });

  test('Handles session timeout gracefully', async () => {
    const session = await workflow.startSession({
      agentId: 'felix',
      mode: TrainingMode.INTENSIVE,
      maxQuestions: 100, // Large number that might timeout
      maxTasks: 50,
      autoAdvance: false,
      timeout: 1000 // 1 second timeout
    });

    // Should handle gracefully without crashing
    expect(session).toBeDefined();
    expect(session.session_id).toBeDefined();
  });
});
