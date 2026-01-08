/**
 * Self-Questioning Engine
 *
 * Week 23-24: Enables agents to generate their own training tasks
 *
 * Core Capabilities:
 * - Analyze performance gaps from attribution data
 * - Generate synthetic training tasks
 * - Create edge case scenarios
 * - Identify improvement opportunities
 *
 * Integration:
 * - Uses AttributionProcessor for performance analysis
 * - Uses ExperienceConsultant for historical patterns
 * - Feeds into SelfTraining workflow
 */

import { Agent } from 'kaibanjs';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export type AgentName =
  | 'Felix' | 'Marcus' | 'Quinn' | 'Betty' | 'Eliza'
  | 'Tessa' | 'Miguel' | 'Diana' | 'Peter' | 'Paul';

export type QuestionCategory =
  | 'performance_gap'      // Where am I underperforming?
  | 'edge_case'           // What edge cases am I missing?
  | 'knowledge_gap'       // What don't I know?
  | 'skill_improvement'   // How can I do this better?
  | 'pattern_discovery';  // What patterns should I learn?

export type TaskDifficulty = 'easy' | 'medium' | 'hard' | 'expert';

export interface SelfQuestion {
  id: string;
  agentName: AgentName;
  category: QuestionCategory;
  question: string;
  context: string;
  priority: number; // 1-10, higher = more important
  createdAt: Date;
  metadata: {
    triggeredBy: string;  // What triggered this question
    relatedOutcomes: string[];  // Related outcome IDs
    estimatedImpact: number;  // 1-10
  };
}

export interface SyntheticTask {
  id: string;
  agentName: AgentName;
  title: string;
  description: string;
  difficulty: TaskDifficulty;
  category: QuestionCategory;
  expectedOutcome: string;
  validationCriteria: string[];
  hints?: string[];
  timeLimit?: number; // minutes
  createdAt: Date;
  sourceQuestion?: string; // Question ID that generated this
}

export interface EdgeCase {
  id: string;
  agentName: AgentName;
  scenario: string;
  expectedBehavior: string;
  potentialFailureMode: string;
  testInput: Record<string, unknown>;
  validationSteps: string[];
  difficulty: TaskDifficulty;
}

export interface PerformanceGap {
  agentName: AgentName;
  area: string;
  currentScore: number;
  targetScore: number;
  gap: number;
  frequency: number; // How often this gap appears
  severity: 'low' | 'medium' | 'high' | 'critical';
  suggestedTasks: string[];
}

export interface SelfQuestioningConfig {
  maxQuestionsPerAgent: number;
  minGapThreshold: number; // Minimum gap to trigger question
  questionCooldownHours: number; // Don't repeat same question within X hours
  priorityWeights: {
    performance: number;
    frequency: number;
    severity: number;
    recency: number;
  };
  enableAutoGeneration: boolean;
  enableEdgeCaseDiscovery: boolean;
}

export interface QuestioningSession {
  id: string;
  agentName: AgentName;
  startedAt: Date;
  completedAt?: Date;
  questionsGenerated: SelfQuestion[];
  tasksGenerated: SyntheticTask[];
  edgeCasesDiscovered: EdgeCase[];
  insights: string[];
}

// ============================================================================
// DEFAULT CONFIGURATION
// ============================================================================

export const DEFAULT_CONFIG: SelfQuestioningConfig = {
  maxQuestionsPerAgent: 10,
  minGapThreshold: 0.15, // 15% gap minimum
  questionCooldownHours: 24,
  priorityWeights: {
    performance: 0.4,
    frequency: 0.3,
    severity: 0.2,
    recency: 0.1
  },
  enableAutoGeneration: true,
  enableEdgeCaseDiscovery: true
};

// ============================================================================
// AGENT-SPECIFIC QUESTION TEMPLATES
// ============================================================================

const AGENT_QUESTION_TEMPLATES: Record<AgentName, Record<QuestionCategory, string[]>> = {
  Felix: {
    performance_gap: [
      "What architectural patterns am I not considering for {context}?",
      "Why did my component design for {context} receive low scores?",
      "What API design principles am I missing in {context}?"
    ],
    edge_case: [
      "What happens when {context} receives extremely high load?",
      "How should {context} handle partial failures?",
      "What if the external dependency in {context} is unavailable?"
    ],
    knowledge_gap: [
      "What microservice patterns should I learn for {context}?",
      "What event-driven architectures would help {context}?",
      "What scalability patterns am I unfamiliar with?"
    ],
    skill_improvement: [
      "How can I better decompose {context} into components?",
      "What would make my API designs more consistent?",
      "How can I improve my technology selection process?"
    ],
    pattern_discovery: [
      "What successful patterns from similar projects apply to {context}?",
      "What anti-patterns should I avoid in {context}?",
      "What emerging patterns should I consider?"
    ]
  },

  Marcus: {
    performance_gap: [
      "Why is my refactoring of {context} causing regressions?",
      "What tech debt am I missing in {context}?",
      "Why are my dependency updates breaking {context}?"
    ],
    edge_case: [
      "What if {context} has circular dependencies?",
      "How do I handle breaking changes in {context}?",
      "What if {context} has undocumented side effects?"
    ],
    knowledge_gap: [
      "What refactoring patterns should I learn for {context}?",
      "What dependency management strategies am I missing?",
      "What code health metrics should I track?"
    ],
    skill_improvement: [
      "How can I make refactoring of {context} safer?",
      "What automated checks would prevent regressions?",
      "How can I better prioritize tech debt?"
    ],
    pattern_discovery: [
      "What successful maintenance patterns apply to {context}?",
      "What code smells indicate deeper problems?",
      "What automated fixes could I implement?"
    ]
  },

  Quinn: {
    performance_gap: [
      "What security vulnerabilities am I missing in {context}?",
      "Why are my code reviews for {context} missing issues?",
      "What quality metrics am I not checking?"
    ],
    edge_case: [
      "What happens with malicious input in {context}?",
      "How does {context} handle authentication edge cases?",
      "What if {context} receives concurrent modifications?"
    ],
    knowledge_gap: [
      "What OWASP vulnerabilities should I check for?",
      "What static analysis rules am I not using?",
      "What compliance requirements am I missing?"
    ],
    skill_improvement: [
      "How can I make my security audits more thorough?",
      "What automated security checks should I add?",
      "How can I better prioritize vulnerabilities?"
    ],
    pattern_discovery: [
      "What security patterns prevent common attacks?",
      "What quality gates catch the most issues?",
      "What audit trails are most valuable?"
    ]
  },

  Betty: {
    performance_gap: [
      "Why am I not finding the root cause in {context}?",
      "What debugging techniques am I missing for {context}?",
      "Why do my fixes for {context} not stick?"
    ],
    edge_case: [
      "What if the bug in {context} is timing-related?",
      "How do I debug {context} in production?",
      "What if {context} has multiple interacting bugs?"
    ],
    knowledge_gap: [
      "What debugging tools should I learn?",
      "What logging patterns help find bugs faster?",
      "What error handling strategies am I missing?"
    ],
    skill_improvement: [
      "How can I reproduce bugs more reliably?",
      "What would make my bug fixes more complete?",
      "How can I prevent similar bugs in the future?"
    ],
    pattern_discovery: [
      "What patterns indicate specific bug types?",
      "What root causes are most common?",
      "What fix patterns are most effective?"
    ]
  },

  Eliza: {
    performance_gap: [
      "Why are my estimates for {context} too optimistic?",
      "What complexity factors am I missing in {context}?",
      "Why do my story point estimates vary so much?"
    ],
    edge_case: [
      "How do I estimate {context} with unknown technology?",
      "What if {context} has unclear requirements?",
      "How do I estimate research tasks?"
    ],
    knowledge_gap: [
      "What estimation techniques should I learn?",
      "What historical data would improve my estimates?",
      "What team factors affect estimation accuracy?"
    ],
    skill_improvement: [
      "How can I calibrate my estimates better?",
      "What feedback loops would help accuracy?",
      "How can I communicate uncertainty better?"
    ],
    pattern_discovery: [
      "What patterns indicate underestimation?",
      "What task types are hardest to estimate?",
      "What factors most affect actual vs estimated?"
    ]
  },

  Tessa: {
    performance_gap: [
      "Why is test coverage for {context} insufficient?",
      "What test scenarios am I missing for {context}?",
      "Why are my tests for {context} flaky?"
    ],
    edge_case: [
      "What boundary conditions should I test in {context}?",
      "How do I test async behavior in {context}?",
      "What failure modes need testing in {context}?"
    ],
    knowledge_gap: [
      "What testing frameworks should I learn?",
      "What test patterns improve maintainability?",
      "What mutation testing strategies exist?"
    ],
    skill_improvement: [
      "How can I write more meaningful assertions?",
      "What would make my tests more reliable?",
      "How can I reduce test execution time?"
    ],
    pattern_discovery: [
      "What test patterns catch the most bugs?",
      "What code changes need most testing?",
      "What test antipatterns should I avoid?"
    ]
  },

  Miguel: {
    performance_gap: [
      "Why is my migration of {context} causing data loss?",
      "What migration risks am I missing in {context}?",
      "Why are my rollback procedures failing?"
    ],
    edge_case: [
      "What if {context} migration is interrupted?",
      "How do I handle partial migrations?",
      "What if {context} has data inconsistencies?"
    ],
    knowledge_gap: [
      "What migration patterns should I learn?",
      "What database migration tools exist?",
      "What blue-green deployment strategies help?"
    ],
    skill_improvement: [
      "How can I make migrations more reversible?",
      "What validation checks prevent data loss?",
      "How can I reduce migration downtime?"
    ],
    pattern_discovery: [
      "What patterns ensure data integrity?",
      "What migration sequences are safest?",
      "What monitoring catches migration issues?"
    ]
  },

  Diana: {
    performance_gap: [
      "Why is my documentation for {context} unclear?",
      "What information am I missing in {context} docs?",
      "Why are users still confused after reading my docs?"
    ],
    edge_case: [
      "How do I document edge cases in {context}?",
      "What if {context} has multiple user personas?",
      "How do I document error scenarios?"
    ],
    knowledge_gap: [
      "What documentation standards should I follow?",
      "What diagramming techniques should I learn?",
      "What API documentation patterns exist?"
    ],
    skill_improvement: [
      "How can I make my docs more scannable?",
      "What examples would clarify {context}?",
      "How can I keep docs in sync with code?"
    ],
    pattern_discovery: [
      "What documentation patterns are most helpful?",
      "What doc sections are most referenced?",
      "What makes documentation discoverable?"
    ]
  },

  Peter: {
    performance_gap: [
      "Why are my requirements for {context} ambiguous?",
      "What acceptance criteria am I missing?",
      "Why do stakeholders misunderstand my user stories?"
    ],
    edge_case: [
      "What if {context} requirements conflict?",
      "How do I handle changing requirements?",
      "What if stakeholders disagree on priorities?"
    ],
    knowledge_gap: [
      "What requirement elicitation techniques exist?",
      "What user story patterns work best?",
      "What prioritization frameworks should I use?"
    ],
    skill_improvement: [
      "How can I write clearer acceptance criteria?",
      "What would make requirements more testable?",
      "How can I better understand user needs?"
    ],
    pattern_discovery: [
      "What requirement patterns reduce rework?",
      "What user story formats are clearest?",
      "What stakeholder communication works best?"
    ]
  },

  Paul: {
    performance_gap: [
      "Why are my project plans for {context} unrealistic?",
      "What risks am I missing in my planning?",
      "Why are my resource allocations wrong?"
    ],
    edge_case: [
      "What if key team members are unavailable?",
      "How do I plan for unknown unknowns?",
      "What if {context} scope changes mid-project?"
    ],
    knowledge_gap: [
      "What project management frameworks should I learn?",
      "What risk assessment techniques exist?",
      "What capacity planning models work best?"
    ],
    skill_improvement: [
      "How can I create more realistic timelines?",
      "What buffer strategies prevent delays?",
      "How can I better track project health?"
    ],
    pattern_discovery: [
      "What planning patterns reduce overruns?",
      "What early warning signs indicate problems?",
      "What communication patterns keep teams aligned?"
    ]
  }
};

// ============================================================================
// SYNTHETIC TASK TEMPLATES
// ============================================================================

const SYNTHETIC_TASK_TEMPLATES: Record<AgentName, SyntheticTask[]> = {
  Felix: [
    {
      id: '',
      agentName: 'Felix',
      title: 'Design Microservice for High Availability',
      description: 'Design a microservice architecture that handles 10,000 requests/second with 99.99% uptime',
      difficulty: 'hard',
      category: 'skill_improvement',
      expectedOutcome: 'Architecture document with component diagram, failure modes, and recovery strategies',
      validationCriteria: [
        'Includes load balancing strategy',
        'Has circuit breaker patterns',
        'Defines health check endpoints',
        'Documents failure recovery procedures'
      ],
      hints: ['Consider using the bulkhead pattern', 'Think about data consistency during failures'],
      timeLimit: 60,
      createdAt: new Date()
    },
    {
      id: '',
      agentName: 'Felix',
      title: 'Event-Driven Architecture Design',
      description: 'Design an event-driven system for order processing with eventual consistency',
      difficulty: 'expert',
      category: 'knowledge_gap',
      expectedOutcome: 'Event flow diagram, message schemas, and consistency guarantees',
      validationCriteria: [
        'Events are immutable and versioned',
        'Includes dead letter queue handling',
        'Defines idempotency strategy',
        'Documents event ordering guarantees'
      ],
      timeLimit: 90,
      createdAt: new Date()
    }
  ],

  Marcus: [
    {
      id: '',
      agentName: 'Marcus',
      title: 'Refactor Legacy Monolith Component',
      description: 'Safely extract a payment module from a 50,000 line monolith without breaking existing functionality',
      difficulty: 'hard',
      category: 'skill_improvement',
      expectedOutcome: 'Step-by-step migration plan with rollback procedures',
      validationCriteria: [
        'No functionality regression',
        'Maintains backward compatibility',
        'Includes feature flags for gradual rollout',
        'Has automated tests for all scenarios'
      ],
      timeLimit: 45,
      createdAt: new Date()
    }
  ],

  Quinn: [
    {
      id: '',
      agentName: 'Quinn',
      title: 'Security Audit: SQL Injection Vectors',
      description: 'Identify all SQL injection vulnerabilities in a provided codebase',
      difficulty: 'medium',
      category: 'edge_case',
      expectedOutcome: 'Vulnerability report with severity ratings and remediation steps',
      validationCriteria: [
        'Identifies direct SQL concatenation',
        'Finds ORM bypass vulnerabilities',
        'Checks stored procedures',
        'Includes proof-of-concept for each finding'
      ],
      timeLimit: 30,
      createdAt: new Date()
    }
  ],

  Betty: [
    {
      id: '',
      agentName: 'Betty',
      title: 'Debug Race Condition',
      description: 'Find and fix a race condition that causes intermittent data corruption',
      difficulty: 'expert',
      category: 'edge_case',
      expectedOutcome: 'Root cause analysis, fix implementation, and regression test',
      validationCriteria: [
        'Reproduces the issue reliably',
        'Identifies the exact race condition',
        'Fix passes stress testing',
        'Includes prevention documentation'
      ],
      timeLimit: 60,
      createdAt: new Date()
    }
  ],

  Eliza: [
    {
      id: '',
      agentName: 'Eliza',
      title: 'Estimate Complex Integration Project',
      description: 'Provide accurate estimates for integrating a legacy system with a modern API',
      difficulty: 'hard',
      category: 'performance_gap',
      expectedOutcome: 'Detailed breakdown with risk-adjusted estimates',
      validationCriteria: [
        'Accounts for discovery time',
        'Includes risk buffers',
        'Separates known vs unknown work',
        'Provides confidence intervals'
      ],
      timeLimit: 30,
      createdAt: new Date()
    }
  ],

  Tessa: [
    {
      id: '',
      agentName: 'Tessa',
      title: 'Design Test Strategy for Event-Driven System',
      description: 'Create comprehensive test strategy for asynchronous message processing',
      difficulty: 'hard',
      category: 'knowledge_gap',
      expectedOutcome: 'Test strategy document with example tests',
      validationCriteria: [
        'Covers eventual consistency testing',
        'Includes chaos testing approach',
        'Defines contract testing for events',
        'Has performance testing strategy'
      ],
      timeLimit: 45,
      createdAt: new Date()
    }
  ],

  Miguel: [
    {
      id: '',
      agentName: 'Miguel',
      title: 'Zero-Downtime Database Migration',
      description: 'Migrate from PostgreSQL 12 to 15 without service interruption',
      difficulty: 'expert',
      category: 'skill_improvement',
      expectedOutcome: 'Migration runbook with validation checkpoints',
      validationCriteria: [
        'No data loss during migration',
        'Rollback tested and documented',
        'Performance validated post-migration',
        'Application compatibility verified'
      ],
      timeLimit: 60,
      createdAt: new Date()
    }
  ],

  Diana: [
    {
      id: '',
      agentName: 'Diana',
      title: 'Document Complex Algorithm',
      description: 'Create clear documentation for a machine learning pipeline',
      difficulty: 'medium',
      category: 'skill_improvement',
      expectedOutcome: 'User guide with examples and troubleshooting section',
      validationCriteria: [
        'Explains concepts for non-ML developers',
        'Includes working code examples',
        'Has troubleshooting decision tree',
        'Provides performance tuning guidance'
      ],
      timeLimit: 45,
      createdAt: new Date()
    }
  ],

  Peter: [
    {
      id: '',
      agentName: 'Peter',
      title: 'Requirements for Multi-Tenant SaaS',
      description: 'Define requirements for adding multi-tenancy to existing application',
      difficulty: 'hard',
      category: 'edge_case',
      expectedOutcome: 'Complete requirements with acceptance criteria',
      validationCriteria: [
        'Covers data isolation requirements',
        'Defines tenant provisioning flow',
        'Addresses billing integration',
        'Includes security requirements'
      ],
      timeLimit: 45,
      createdAt: new Date()
    }
  ],

  Paul: [
    {
      id: '',
      agentName: 'Paul',
      title: 'Plan Recovery from Critical Bug',
      description: 'Create action plan for recovering from a production data corruption incident',
      difficulty: 'expert',
      category: 'edge_case',
      expectedOutcome: 'Incident response plan with timeline and communication strategy',
      validationCriteria: [
        'Defines escalation procedures',
        'Includes customer communication templates',
        'Has data recovery procedures',
        'Documents post-mortem process'
      ],
      timeLimit: 30,
      createdAt: new Date()
    }
  ]
};

// ============================================================================
// SELF-QUESTIONING ENGINE CLASS
// ============================================================================

export class SelfQuestioningEngine {
  private config: SelfQuestioningConfig;
  private recentQuestions: Map<string, Date> = new Map(); // Track cooldowns

  constructor(config: Partial<SelfQuestioningConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Generate self-questions for an agent based on performance data
   */
  async generateQuestions(
    agentName: AgentName,
    performanceData: PerformanceGap[],
    recentOutcomes: { id: string; success: boolean; context: string }[]
  ): Promise<SelfQuestion[]> {
    const questions: SelfQuestion[] = [];
    const templates = AGENT_QUESTION_TEMPLATES[agentName];

    // Filter gaps above threshold
    const significantGaps = performanceData.filter(
      gap => gap.gap >= this.config.minGapThreshold
    );

    // Generate questions for each significant gap
    for (const gap of significantGaps) {
      const category = this.mapGapToCategory(gap);
      const questionTemplates = templates[category];

      if (questionTemplates && questionTemplates.length > 0) {
        const template = questionTemplates[Math.floor(Math.random() * questionTemplates.length)];
        const question = template.replace('{context}', gap.area);

        // Check cooldown
        const cooldownKey = `${agentName}-${category}-${gap.area}`;
        if (this.isOnCooldown(cooldownKey)) continue;

        const priority = this.calculatePriority(gap, recentOutcomes);

        questions.push({
          id: `sq-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          agentName,
          category,
          question,
          context: gap.area,
          priority,
          createdAt: new Date(),
          metadata: {
            triggeredBy: `Performance gap: ${gap.area} (${gap.gap * 100}% below target)`,
            relatedOutcomes: recentOutcomes
              .filter(o => !o.success && o.context.includes(gap.area))
              .map(o => o.id),
            estimatedImpact: Math.round(gap.gap * 10)
          }
        });

        this.recentQuestions.set(cooldownKey, new Date());
      }
    }

    // Also generate questions from recent failures
    const failedOutcomes = recentOutcomes.filter(o => !o.success);
    for (const outcome of failedOutcomes.slice(0, 3)) {
      const category: QuestionCategory = 'performance_gap';
      const questionTemplates = templates[category];

      if (questionTemplates && questionTemplates.length > 0) {
        const template = questionTemplates[Math.floor(Math.random() * questionTemplates.length)];
        const question = template.replace('{context}', outcome.context);

        questions.push({
          id: `sq-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          agentName,
          category,
          question,
          context: outcome.context,
          priority: 8, // High priority for recent failures
          createdAt: new Date(),
          metadata: {
            triggeredBy: `Recent failure: ${outcome.id}`,
            relatedOutcomes: [outcome.id],
            estimatedImpact: 8
          }
        });
      }
    }

    // Sort by priority and limit
    return questions
      .sort((a, b) => b.priority - a.priority)
      .slice(0, this.config.maxQuestionsPerAgent);
  }

  /**
   * Generate synthetic training tasks from questions
   */
  async generateTrainingTasks(
    agentName: AgentName,
    questions: SelfQuestion[],
    difficulty: TaskDifficulty = 'medium'
  ): Promise<SyntheticTask[]> {
    const tasks: SyntheticTask[] = [];
    const agentTasks = SYNTHETIC_TASK_TEMPLATES[agentName] || [];

    // Select appropriate tasks based on questions
    for (const question of questions) {
      // Find matching template
      const matchingTasks = agentTasks.filter(t => t.category === question.category);

      if (matchingTasks.length > 0) {
        const template = matchingTasks[Math.floor(Math.random() * matchingTasks.length)];

        tasks.push({
          ...template,
          id: `st-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          difficulty: difficulty,
          createdAt: new Date(),
          sourceQuestion: question.id
        });
      } else {
        // Generate custom task from question
        tasks.push(this.createTaskFromQuestion(agentName, question, difficulty));
      }
    }

    return tasks;
  }

  /**
   * Discover edge cases for an agent
   */
  async discoverEdgeCases(
    agentName: AgentName,
    recentWork: { type: string; input: Record<string, unknown>; output: unknown }[]
  ): Promise<EdgeCase[]> {
    if (!this.config.enableEdgeCaseDiscovery) return [];

    const edgeCases: EdgeCase[] = [];
    const templates = AGENT_QUESTION_TEMPLATES[agentName]['edge_case'];

    // Analyze recent work for patterns
    const inputPatterns = this.analyzeInputPatterns(recentWork);

    for (const pattern of inputPatterns) {
      // Generate edge case for each identified pattern
      const template = templates[Math.floor(Math.random() * templates.length)];

      edgeCases.push({
        id: `ec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        agentName,
        scenario: template.replace('{context}', pattern.name),
        expectedBehavior: `Handle ${pattern.name} gracefully with appropriate error handling`,
        potentialFailureMode: pattern.potentialFailure,
        testInput: pattern.extremeInput,
        validationSteps: [
          `Apply ${pattern.name} input`,
          'Verify no unhandled exceptions',
          'Check error messages are user-friendly',
          'Confirm system remains stable'
        ],
        difficulty: 'hard'
      });
    }

    return edgeCases;
  }

  /**
   * Run a complete self-questioning session
   */
  async runSession(
    agentName: AgentName,
    performanceData: PerformanceGap[],
    recentOutcomes: { id: string; success: boolean; context: string }[],
    recentWork: { type: string; input: Record<string, unknown>; output: unknown }[]
  ): Promise<QuestioningSession> {
    const sessionId = `qs-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const startTime = new Date();

    console.log(`\n🤔 Starting Self-Questioning Session for ${agentName}`);
    console.log(`   Session ID: ${sessionId}`);

    // Step 1: Generate questions
    console.log('   Step 1: Generating self-questions...');
    const questions = await this.generateQuestions(agentName, performanceData, recentOutcomes);
    console.log(`   → Generated ${questions.length} questions`);

    // Step 2: Generate training tasks
    console.log('   Step 2: Creating training tasks...');
    const tasks = await this.generateTrainingTasks(agentName, questions);
    console.log(`   → Created ${tasks.length} training tasks`);

    // Step 3: Discover edge cases
    console.log('   Step 3: Discovering edge cases...');
    const edgeCases = await this.discoverEdgeCases(agentName, recentWork);
    console.log(`   → Discovered ${edgeCases.length} edge cases`);

    // Step 4: Generate insights
    const insights = this.generateInsights(agentName, questions, performanceData);

    console.log(`\n✅ Session complete for ${agentName}`);
    console.log(`   Questions: ${questions.length}`);
    console.log(`   Tasks: ${tasks.length}`);
    console.log(`   Edge Cases: ${edgeCases.length}`);
    console.log(`   Insights: ${insights.length}`);

    return {
      id: sessionId,
      agentName,
      startedAt: startTime,
      completedAt: new Date(),
      questionsGenerated: questions,
      tasksGenerated: tasks,
      edgeCasesDiscovered: edgeCases,
      insights
    };
  }

  // ============================================================================
  // PRIVATE HELPER METHODS
  // ============================================================================

  private mapGapToCategory(gap: PerformanceGap): QuestionCategory {
    if (gap.severity === 'critical' || gap.severity === 'high') {
      return 'performance_gap';
    }
    if (gap.frequency > 5) {
      return 'pattern_discovery';
    }
    if (gap.area.includes('unknown') || gap.area.includes('new')) {
      return 'knowledge_gap';
    }
    return 'skill_improvement';
  }

  private calculatePriority(
    gap: PerformanceGap,
    recentOutcomes: { id: string; success: boolean; context: string }[]
  ): number {
    const { priorityWeights } = this.config;

    // Performance score (based on gap size)
    const performanceScore = Math.min(gap.gap * 10, 10);

    // Frequency score
    const frequencyScore = Math.min(gap.frequency, 10);

    // Severity score
    const severityMap = { critical: 10, high: 8, medium: 5, low: 2 };
    const severityScore = severityMap[gap.severity];

    // Recency score (how recent were related failures)
    const relatedFailures = recentOutcomes.filter(
      o => !o.success && o.context.includes(gap.area)
    ).length;
    const recencyScore = Math.min(relatedFailures * 2, 10);

    return Math.round(
      performanceScore * priorityWeights.performance +
      frequencyScore * priorityWeights.frequency +
      severityScore * priorityWeights.severity +
      recencyScore * priorityWeights.recency
    );
  }

  private isOnCooldown(key: string): boolean {
    const lastAsked = this.recentQuestions.get(key);
    if (!lastAsked) return false;

    const hoursSince = (Date.now() - lastAsked.getTime()) / (1000 * 60 * 60);
    return hoursSince < this.config.questionCooldownHours;
  }

  private createTaskFromQuestion(
    agentName: AgentName,
    question: SelfQuestion,
    difficulty: TaskDifficulty
  ): SyntheticTask {
    return {
      id: `st-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      agentName,
      title: `Practice: ${question.context}`,
      description: `Based on question: "${question.question}"`,
      difficulty,
      category: question.category,
      expectedOutcome: `Demonstrate improved capability in ${question.context}`,
      validationCriteria: [
        'Addresses the core question',
        'Shows understanding of the gap',
        'Provides actionable improvement'
      ],
      createdAt: new Date(),
      sourceQuestion: question.id
    };
  }

  private analyzeInputPatterns(
    recentWork: { type: string; input: Record<string, unknown>; output: unknown }[]
  ): { name: string; potentialFailure: string; extremeInput: Record<string, unknown> }[] {
    const patterns: { name: string; potentialFailure: string; extremeInput: Record<string, unknown> }[] = [];

    // Identify numeric inputs that could overflow
    for (const work of recentWork) {
      for (const [key, value] of Object.entries(work.input)) {
        if (typeof value === 'number') {
          patterns.push({
            name: `Large ${key}`,
            potentialFailure: `${key} overflow or timeout`,
            extremeInput: { ...work.input, [key]: Number.MAX_SAFE_INTEGER }
          });
          patterns.push({
            name: `Negative ${key}`,
            potentialFailure: `Unexpected negative ${key} handling`,
            extremeInput: { ...work.input, [key]: -1 }
          });
        }
        if (typeof value === 'string') {
          patterns.push({
            name: `Empty ${key}`,
            potentialFailure: `Empty string handling for ${key}`,
            extremeInput: { ...work.input, [key]: '' }
          });
          patterns.push({
            name: `Long ${key}`,
            potentialFailure: `Very long string for ${key}`,
            extremeInput: { ...work.input, [key]: 'x'.repeat(10000) }
          });
        }
        if (Array.isArray(value)) {
          patterns.push({
            name: `Empty ${key} array`,
            potentialFailure: `Empty array handling for ${key}`,
            extremeInput: { ...work.input, [key]: [] }
          });
          patterns.push({
            name: `Large ${key} array`,
            potentialFailure: `Large array performance for ${key}`,
            extremeInput: { ...work.input, [key]: new Array(10000).fill(value[0]) }
          });
        }
      }
    }

    return patterns.slice(0, 10); // Limit to 10 patterns
  }

  private generateInsights(
    agentName: AgentName,
    questions: SelfQuestion[],
    performanceData: PerformanceGap[]
  ): string[] {
    const insights: string[] = [];

    // Most common category
    const categoryCounts = questions.reduce((acc, q) => {
      acc[q.category] = (acc[q.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const topCategory = Object.entries(categoryCounts)
      .sort(([, a], [, b]) => b - a)[0];

    if (topCategory) {
      insights.push(`${agentName} should focus on ${topCategory[0]} with ${topCategory[1]} related questions`);
    }

    // Highest priority gaps
    const criticalGaps = performanceData.filter(g => g.severity === 'critical' || g.severity === 'high');
    if (criticalGaps.length > 0) {
      insights.push(`${criticalGaps.length} critical/high priority areas need immediate attention: ${criticalGaps.map(g => g.area).join(', ')}`);
    }

    // Overall gap trend
    const avgGap = performanceData.reduce((sum, g) => sum + g.gap, 0) / performanceData.length;
    if (avgGap > 0.3) {
      insights.push(`Average performance gap of ${(avgGap * 100).toFixed(1)}% suggests systematic training needed`);
    } else if (avgGap < 0.1) {
      insights.push(`Low average gap of ${(avgGap * 100).toFixed(1)}% indicates strong performance`);
    }

    return insights;
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export const selfQuestioningEngine = new SelfQuestioningEngine();
export default SelfQuestioningEngine;
