/**
 * Self-Training Workflow
 *
 * Week 23-24: Orchestrates the agent self-improvement process
 *
 * Workflow Stages:
 * 1. Data Collection - Gather performance data and recent outcomes
 * 2. Self-Questioning - Generate questions and identify gaps
 * 3. Task Generation - Create synthetic training tasks
 * 4. Training Execution - Run training tasks with validation
 * 5. Evaluation - Measure improvement and update metrics
 *
 * Integration:
 * - SelfQuestioningEngine for question/task generation
 * - AttributionProcessor for performance data
 * - ExperienceConsultant for historical patterns
 * - ValidationService for training validation
 */

import {
  SelfQuestioningEngine,
  SelfQuestion,
  SyntheticTask,
  EdgeCase,
  PerformanceGap,
  QuestioningSession,
  AgentName,
  TaskDifficulty
} from '../lib/selfQuestioningEngine';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface TrainingSessionConfig {
  /** Target agent for training */
  agentName: AgentName;

  /** Difficulty level for generated tasks */
  difficulty: TaskDifficulty;

  /** Maximum training tasks per session */
  maxTasks: number;

  /** Include edge case training */
  includeEdgeCases: boolean;

  /** Minimum improvement threshold to consider success */
  improvementThreshold: number;

  /** Maximum time per task (minutes) */
  maxTimePerTask: number;

  /** Enable validation loop */
  enableValidation: boolean;

  /** Auto-retry failed tasks */
  autoRetry: boolean;

  /** Maximum retry attempts */
  maxRetries: number;
}

export interface TrainingTask {
  id: string;
  syntheticTask: SyntheticTask;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  startedAt?: Date;
  completedAt?: Date;
  attempts: number;
  result?: {
    success: boolean;
    score: number;
    validationPassed: boolean;
    feedback: string[];
    timeSpent: number; // minutes
  };
}

export interface TrainingSessionResult {
  id: string;
  agentName: AgentName;
  config: TrainingSessionConfig;
  startedAt: Date;
  completedAt?: Date;
  status: 'running' | 'completed' | 'failed' | 'cancelled';

  // Input data
  questioningSession: QuestioningSession;
  performanceGaps: PerformanceGap[];

  // Training tasks
  trainingTasks: TrainingTask[];

  // Results
  metrics: {
    tasksAttempted: number;
    tasksCompleted: number;
    tasksFailed: number;
    averageScore: number;
    totalTimeSpent: number;
    improvementMeasured: number;
  };

  // Insights
  insights: string[];
  recommendations: string[];
}

export interface TrainingSchedule {
  id: string;
  agentName: AgentName;
  frequency: 'daily' | 'weekly' | 'on_demand';
  nextRun: Date;
  lastRun?: Date;
  config: Partial<TrainingSessionConfig>;
  enabled: boolean;
}

// ============================================================================
// DEFAULT CONFIGURATION
// ============================================================================

export const DEFAULT_TRAINING_CONFIG: TrainingSessionConfig = {
  agentName: 'Felix',
  difficulty: 'medium',
  maxTasks: 5,
  includeEdgeCases: true,
  improvementThreshold: 0.05, // 5% improvement
  maxTimePerTask: 30,
  enableValidation: true,
  autoRetry: true,
  maxRetries: 2
};

// ============================================================================
// SELF-TRAINING WORKFLOW CLASS
// ============================================================================

export class SelfTrainingWorkflow {
  private questioningEngine: SelfQuestioningEngine;
  private activeSession: TrainingSessionResult | null = null;

  constructor() {
    this.questioningEngine = new SelfQuestioningEngine();
  }

  /**
   * Start a training session for an agent
   */
  async startSession(
    config: Partial<TrainingSessionConfig> = {}
  ): Promise<TrainingSessionResult> {
    const fullConfig: TrainingSessionConfig = {
      ...DEFAULT_TRAINING_CONFIG,
      ...config
    };

    const sessionId = `ts-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    console.log('\n🎓 Starting Self-Training Session');
    console.log(`   Session ID: ${sessionId}`);
    console.log(`   Agent: ${fullConfig.agentName}`);
    console.log(`   Difficulty: ${fullConfig.difficulty}`);
    console.log(`   Max Tasks: ${fullConfig.maxTasks}`);

    // Initialize session
    const session: TrainingSessionResult = {
      id: sessionId,
      agentName: fullConfig.agentName,
      config: fullConfig,
      startedAt: new Date(),
      status: 'running',
      questioningSession: {} as QuestioningSession,
      performanceGaps: [],
      trainingTasks: [],
      metrics: {
        tasksAttempted: 0,
        tasksCompleted: 0,
        tasksFailed: 0,
        averageScore: 0,
        totalTimeSpent: 0,
        improvementMeasured: 0
      },
      insights: [],
      recommendations: []
    };

    this.activeSession = session;

    try {
      // Stage 1: Collect performance data
      console.log('\n📊 Stage 1: Collecting Performance Data');
      const performanceData = await this.collectPerformanceData(fullConfig.agentName);
      session.performanceGaps = performanceData.gaps;
      console.log(`   → Found ${performanceData.gaps.length} performance gaps`);
      console.log(`   → ${performanceData.recentOutcomes.length} recent outcomes analyzed`);

      // Stage 2: Run self-questioning session
      console.log('\n🤔 Stage 2: Self-Questioning Session');
      const questioningSession = await this.questioningEngine.runSession(
        fullConfig.agentName,
        performanceData.gaps,
        performanceData.recentOutcomes,
        performanceData.recentWork
      );
      session.questioningSession = questioningSession;

      // Stage 3: Create training tasks
      console.log('\n📝 Stage 3: Creating Training Tasks');
      const trainingTasks = await this.createTrainingTasks(
        questioningSession,
        fullConfig
      );
      session.trainingTasks = trainingTasks;
      console.log(`   → Created ${trainingTasks.length} training tasks`);

      // Stage 4: Execute training
      console.log('\n🏋️ Stage 4: Executing Training Tasks');
      await this.executeTrainingTasks(session);

      // Stage 5: Evaluate and generate insights
      console.log('\n📈 Stage 5: Evaluating Results');
      await this.evaluateSession(session);

      session.status = 'completed';
      session.completedAt = new Date();

      console.log('\n✅ Training Session Complete!');
      this.printSessionSummary(session);

    } catch (error) {
      session.status = 'failed';
      session.completedAt = new Date();
      console.error('\n❌ Training session failed:', error);
    }

    this.activeSession = null;
    return session;
  }

  /**
   * Collect performance data for an agent
   */
  private async collectPerformanceData(agentName: AgentName): Promise<{
    gaps: PerformanceGap[];
    recentOutcomes: { id: string; success: boolean; context: string }[];
    recentWork: { type: string; input: Record<string, unknown>; output: unknown }[];
  }> {
    // In production, this would query the database
    // For now, generate mock data based on agent type

    const gaps = this.generateMockGaps(agentName);
    const recentOutcomes = this.generateMockOutcomes(agentName);
    const recentWork = this.generateMockWork(agentName);

    return { gaps, recentOutcomes, recentWork };
  }

  /**
   * Create training tasks from questioning session
   */
  private async createTrainingTasks(
    questioningSession: QuestioningSession,
    config: TrainingSessionConfig
  ): Promise<TrainingTask[]> {
    const tasks: TrainingTask[] = [];

    // Add tasks from questioning session
    for (const syntheticTask of questioningSession.tasksGenerated.slice(0, config.maxTasks)) {
      tasks.push({
        id: `tt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        syntheticTask,
        status: 'pending',
        attempts: 0
      });
    }

    // Add edge case tasks if enabled
    if (config.includeEdgeCases && questioningSession.edgeCasesDiscovered.length > 0) {
      const edgeCaseLimit = Math.max(1, Math.floor(config.maxTasks / 3));

      for (const edgeCase of questioningSession.edgeCasesDiscovered.slice(0, edgeCaseLimit)) {
        tasks.push({
          id: `tt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          syntheticTask: this.edgeCaseToTask(edgeCase),
          status: 'pending',
          attempts: 0
        });
      }
    }

    return tasks;
  }

  /**
   * Execute training tasks
   */
  private async executeTrainingTasks(session: TrainingSessionResult): Promise<void> {
    const { config, trainingTasks } = session;

    for (const task of trainingTasks) {
      console.log(`\n   📋 Task: ${task.syntheticTask.title}`);
      console.log(`      Difficulty: ${task.syntheticTask.difficulty}`);

      task.status = 'in_progress';
      task.startedAt = new Date();
      task.attempts++;
      session.metrics.tasksAttempted++;

      try {
        // Simulate task execution (in production, this would run the actual task)
        const result = await this.executeTask(task, config);
        task.result = result;

        if (result.success && result.validationPassed) {
          task.status = 'completed';
          session.metrics.tasksCompleted++;
          console.log(`      ✅ Completed (score: ${result.score}/10)`);
        } else if (config.autoRetry && task.attempts < config.maxRetries) {
          console.log(`      🔄 Retrying (attempt ${task.attempts + 1}/${config.maxRetries})`);
          // Re-queue for retry
          task.status = 'pending';
        } else {
          task.status = 'failed';
          session.metrics.tasksFailed++;
          console.log(`      ❌ Failed: ${result.feedback.join(', ')}`);
        }

        session.metrics.totalTimeSpent += result.timeSpent;

      } catch (error) {
        task.status = 'failed';
        session.metrics.tasksFailed++;
        console.log(`      ❌ Error: ${error}`);
      }

      task.completedAt = new Date();
    }
  }

  /**
   * Execute a single training task
   */
  private async executeTask(
    task: TrainingTask,
    config: TrainingSessionConfig
  ): Promise<{
    success: boolean;
    score: number;
    validationPassed: boolean;
    feedback: string[];
    timeSpent: number;
  }> {
    // Simulate task execution with random results
    // In production, this would:
    // 1. Present the task to the agent
    // 2. Capture the agent's output
    // 3. Run validation
    // 4. Score the result

    const startTime = Date.now();

    // Simulate processing time
    await this.sleep(100);

    // Simulate results based on difficulty
    const difficultyFactor = {
      easy: 0.9,
      medium: 0.75,
      hard: 0.6,
      expert: 0.4
    }[task.syntheticTask.difficulty];

    const score = Math.round(5 + Math.random() * 5 * difficultyFactor);
    const success = score >= 6;
    const validationPassed = config.enableValidation ? (success && Math.random() > 0.2) : true;

    const feedback: string[] = [];
    if (!success) {
      feedback.push('Task output did not meet expected criteria');
    }
    if (!validationPassed) {
      feedback.push('Validation checks failed');
    }
    if (success && validationPassed) {
      feedback.push('Good work!');
      if (score >= 8) {
        feedback.push('Excellent performance on this task');
      }
    }

    const timeSpent = Math.round((Date.now() - startTime) / 1000 / 60 * 10) / 10; // minutes

    return {
      success,
      score,
      validationPassed,
      feedback,
      timeSpent
    };
  }

  /**
   * Evaluate session and generate insights
   */
  private async evaluateSession(session: TrainingSessionResult): Promise<void> {
    const { metrics, trainingTasks, performanceGaps, config } = session;

    // Calculate average score
    const completedTasks = trainingTasks.filter(t => t.result?.score);
    if (completedTasks.length > 0) {
      metrics.averageScore = completedTasks.reduce(
        (sum, t) => sum + (t.result?.score || 0),
        0
      ) / completedTasks.length;
    }

    // Calculate improvement (simulated)
    const baselineScore = performanceGaps.length > 0
      ? performanceGaps.reduce((sum, g) => sum + (1 - g.gap), 0) / performanceGaps.length
      : 0.7;

    metrics.improvementMeasured = metrics.averageScore / 10 - baselineScore;

    // Generate insights
    session.insights = [];

    if (metrics.tasksCompleted === metrics.tasksAttempted) {
      session.insights.push(`${config.agentName} completed all ${metrics.tasksAttempted} training tasks successfully`);
    } else if (metrics.tasksFailed > metrics.tasksCompleted) {
      session.insights.push(`${config.agentName} struggled with ${config.difficulty} difficulty tasks (${metrics.tasksFailed} failures)`);
    }

    if (metrics.averageScore >= 8) {
      session.insights.push('Excellent average score indicates strong capability in trained areas');
    } else if (metrics.averageScore < 5) {
      session.insights.push('Low average score suggests need for more foundational training');
    }

    if (metrics.improvementMeasured > config.improvementThreshold) {
      session.insights.push(`Measured improvement of ${(metrics.improvementMeasured * 100).toFixed(1)}% exceeds threshold`);
    }

    // Generate recommendations
    session.recommendations = [];

    if (metrics.tasksFailed > 0) {
      session.recommendations.push(`Consider reducing difficulty from ${config.difficulty} for failed task categories`);
    }

    if (metrics.averageScore < 7) {
      session.recommendations.push('Schedule follow-up training session within 1 week');
    }

    const topGap = performanceGaps.sort((a, b) => b.gap - a.gap)[0];
    if (topGap) {
      session.recommendations.push(`Focus next session on ${topGap.area} (${(topGap.gap * 100).toFixed(0)}% gap)`);
    }
  }

  /**
   * Print session summary
   */
  private printSessionSummary(session: TrainingSessionResult): void {
    const { metrics, insights, recommendations } = session;

    console.log('\n📊 Session Summary');
    console.log('   ─────────────────────────────────────');
    console.log(`   Tasks Attempted: ${metrics.tasksAttempted}`);
    console.log(`   Tasks Completed: ${metrics.tasksCompleted}`);
    console.log(`   Tasks Failed: ${metrics.tasksFailed}`);
    console.log(`   Average Score: ${metrics.averageScore.toFixed(1)}/10`);
    console.log(`   Total Time: ${metrics.totalTimeSpent.toFixed(1)} minutes`);
    console.log(`   Improvement: ${(metrics.improvementMeasured * 100).toFixed(1)}%`);

    if (insights.length > 0) {
      console.log('\n💡 Insights:');
      insights.forEach(i => console.log(`   • ${i}`));
    }

    if (recommendations.length > 0) {
      console.log('\n📌 Recommendations:');
      recommendations.forEach(r => console.log(`   • ${r}`));
    }
  }

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

  private edgeCaseToTask(edgeCase: EdgeCase): SyntheticTask {
    return {
      id: `st-ec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      agentName: edgeCase.agentName,
      title: `Edge Case: ${edgeCase.scenario.substring(0, 50)}...`,
      description: edgeCase.scenario,
      difficulty: edgeCase.difficulty,
      category: 'edge_case',
      expectedOutcome: edgeCase.expectedBehavior,
      validationCriteria: edgeCase.validationSteps,
      createdAt: new Date()
    };
  }

  private generateMockGaps(agentName: AgentName): PerformanceGap[] {
    const areas = {
      Felix: ['API design', 'microservice patterns', 'scalability'],
      Marcus: ['refactoring safety', 'dependency management', 'code health'],
      Quinn: ['security scanning', 'code review depth', 'compliance'],
      Betty: ['root cause analysis', 'reproduction reliability', 'fix completeness'],
      Eliza: ['estimation accuracy', 'risk assessment', 'complexity analysis'],
      Tessa: ['test coverage', 'edge case detection', 'test maintainability'],
      Miguel: ['migration safety', 'data integrity', 'rollback procedures'],
      Diana: ['clarity', 'completeness', 'maintainability'],
      Peter: ['requirement clarity', 'acceptance criteria', 'prioritization'],
      Paul: ['timeline accuracy', 'risk identification', 'resource allocation']
    }[agentName] || ['general performance'];

    return areas.map(area => ({
      agentName,
      area,
      currentScore: 0.6 + Math.random() * 0.2,
      targetScore: 0.9,
      gap: 0.1 + Math.random() * 0.2,
      frequency: Math.floor(Math.random() * 10) + 1,
      severity: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as 'low' | 'medium' | 'high',
      suggestedTasks: [`Improve ${area}`, `Practice ${area} scenarios`]
    }));
  }

  private generateMockOutcomes(agentName: AgentName): { id: string; success: boolean; context: string }[] {
    const contexts = {
      Felix: ['e-commerce API', 'user service', 'payment integration'],
      Marcus: ['legacy codebase', 'dependency update', 'tech debt reduction'],
      Quinn: ['security audit', 'code review', 'compliance check'],
      Betty: ['production bug', 'intermittent failure', 'performance issue'],
      Eliza: ['sprint planning', 'feature estimation', 'complexity assessment'],
      Tessa: ['unit tests', 'integration tests', 'E2E tests'],
      Miguel: ['database migration', 'API versioning', 'infrastructure upgrade'],
      Diana: ['API documentation', 'architecture guide', 'onboarding docs'],
      Peter: ['user story', 'requirement gathering', 'backlog refinement'],
      Paul: ['project planning', 'sprint review', 'resource planning']
    }[agentName] || ['general task'];

    return contexts.map((context, i) => ({
      id: `outcome-${i}-${Date.now()}`,
      success: Math.random() > 0.3,
      context
    }));
  }

  private generateMockWork(agentName: AgentName): { type: string; input: Record<string, unknown>; output: unknown }[] {
    return [
      { type: 'design', input: { complexity: 5, components: 3 }, output: { success: true } },
      { type: 'review', input: { linesOfCode: 500, files: 10 }, output: { issues: 3 } },
      { type: 'generate', input: { requirements: 5, constraints: 2 }, output: { artifacts: 4 } }
    ];
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ============================================================================
  // PUBLIC UTILITY METHODS
  // ============================================================================

  /**
   * Get current active session
   */
  getActiveSession(): TrainingSessionResult | null {
    return this.activeSession;
  }

  /**
   * Cancel active session
   */
  cancelSession(): void {
    if (this.activeSession) {
      this.activeSession.status = 'cancelled';
      this.activeSession.completedAt = new Date();
      this.activeSession = null;
      console.log('Training session cancelled');
    }
  }

  /**
   * Run training for all agents
   */
  async runAllAgentTraining(
    config: Partial<TrainingSessionConfig> = {}
  ): Promise<Map<AgentName, TrainingSessionResult>> {
    const agents: AgentName[] = [
      'Felix', 'Marcus', 'Quinn', 'Betty', 'Eliza',
      'Tessa', 'Miguel', 'Diana', 'Peter', 'Paul'
    ];

    const results = new Map<AgentName, TrainingSessionResult>();

    console.log('\n🎓 Starting Multi-Agent Training Session');
    console.log(`   Training ${agents.length} agents`);

    for (const agentName of agents) {
      const result = await this.startSession({ ...config, agentName });
      results.set(agentName, result);
    }

    console.log('\n✅ All Agent Training Complete!');
    console.log('   Summary:');

    for (const [agent, result] of results) {
      const status = result.status === 'completed' ? '✅' : '❌';
      console.log(`   ${status} ${agent}: ${result.metrics.tasksCompleted}/${result.metrics.tasksAttempted} tasks, avg score ${result.metrics.averageScore.toFixed(1)}`);
    }

    return results;
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export const selfTrainingWorkflow = new SelfTrainingWorkflow();
export default SelfTrainingWorkflow;
