/**
 * Agent Evolution Integration - All 10 Agents
 *
 * Specific implementations for each agent's self-navigating behavior.
 * Part of AgentEvolver Phase B (Week 19-20).
 *
 * Each agent has customized:
 * - Consultation options (what to look for)
 * - Guidance interpretation (how to use guidance)
 * - Outcome attributes (what to learn from)
 *
 * Agents:
 * - Felix (Feature Architect) - Architecture & design
 * - Marcus (Maintenance Specialist) - Tech debt & refactoring
 * - Quinn (Quality Inspector) - Quality & security
 * - Betty (Bug Hunter) - Bug investigation & fixing
 * - Eliza (Estimation Engine) - Effort estimation
 * - Tessa (Test Engineer) - Test automation
 * - Miguel (Migration Architect) - Platform migrations
 * - Diana (Documentation Writer) - Technical docs
 * - Peter (Product Owner) - Requirements & vision
 * - Paul (Project Lead) - Planning & coordination
 *
 * @author Claude Code (Week 19-20)
 * @date 2025-11-22
 */

import { Agent } from 'kaibanjs';
import { agents } from '../configs/agents';
import {
  EvolvingAgentWrapper,
  ExecutionResult,
  AGENT_ROLES,
  Task  // Import Task from experienceIntegration
} from './experienceIntegration';
import {
  ConsultationOptions,
  Guidance,
  KeyDecision
} from '../lib/experienceConsultant';

// ============================================================================
// Felix - Feature Architect Evolution
// ============================================================================

export class FelixEvolvingAgent extends EvolvingAgentWrapper {
  private static FELIX_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 5,    // Felix relies heavily on architecture patterns
    maxFailures: 3,
    minSimilarity: 0.5,
    includeOtherAgents: false  // Focus on own experience first
  };

  constructor() {
    super({
      agent: agents.featureArchitect,
      agentId: 'felix',
      agentRole: 'architect',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: FelixEvolvingAgent.FELIX_CONSULTATION_OPTIONS
    });
  }

  /**
   * Felix-specific task enhancement
   *
   * Felix focuses on:
   * - Architecture patterns that worked
   * - API design decisions
   * - Microservices vs monolith choices
   * - System scalability lessons
   */
  async executeFeatureDesign(
    featureDescription: string,
    context: Record<string, any> = {}
  ): Promise<ExecutionResult> {
    console.log('\n=== FELIX: Feature Architect ===');
    console.log('🏗️ Designing feature with self-navigation...');

    const task: Task = {
      description: `
        Design architecture for: ${featureDescription}

        Context:
        - Project Type: ${context.projectType || 'web_application'}
        - Tech Stack: ${context.techStack?.join(', ') || 'FastAPI, React, PostgreSQL'}
        - Scale Requirements: ${context.scale || 'medium'}

        Deliverables:
        1. High-level architecture diagram
        2. Component breakdown
        3. API endpoints design
        4. Data model changes
        5. Integration points
      `,
      expectedOutput: 'Complete feature architecture specification'
    };

    const result = await this.executeWithExperience(task, 'NEW_FEATURE');

    // Felix-specific learning: Architecture decisions
    if (result.success) {
      this.recordDecision({
        decision: `Architecture for: ${featureDescription.substring(0, 50)}...`,
        reasoning: 'Based on requirements and past successful patterns',
        alternatives: ['Microservices', 'Monolith', 'Hybrid'],
        outcome: 'Designed',
        impactScore: 0.8
      });
    }

    return result;
  }
}

// ============================================================================
// Marcus - Maintenance Specialist Evolution
// ============================================================================

export class MarcusEvolvingAgent extends EvolvingAgentWrapper {
  private static MARCUS_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 3,
    maxFailures: 5,    // Marcus needs to know about past maintenance failures
    minSimilarity: 0.4,  // Lower threshold to catch more maintenance issues
    includeOtherAgents: true  // Learn from Quinn's quality findings
  };

  constructor() {
    super({
      agent: agents.maintenanceSpecialist,
      agentId: 'marcus',
      agentRole: 'maintenance',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: MarcusEvolvingAgent.MARCUS_CONSULTATION_OPTIONS
    });
  }

  /**
   * Marcus-specific task enhancement
   *
   * Marcus focuses on:
   * - Past refactoring successes/failures
   * - Dependency update strategies
   * - Technical debt patterns
   * - Safe refactoring approaches
   */
  async executeMaintenanceAnalysis(
    scope: string,
    focusAreas: string[]
  ): Promise<ExecutionResult> {
    console.log('\n=== MARCUS: Maintenance Specialist ===');
    console.log('🔧 Analyzing maintenance with self-navigation...');

    const task: Task = {
      description: `
        Perform maintenance analysis:

        Scope: ${scope}
        Focus Areas: ${focusAreas.join(', ')}

        Analysis Steps:
        1. Scan for dependency vulnerabilities
        2. Detect code smells and complexity
        3. Measure technical debt ratio
        4. Identify security issues
        5. Check test coverage gaps
        6. Review documentation state

        Output:
        - Prioritized findings list
        - Risk assessment per finding
        - Recommended remediation order
        - Effort estimates (SP)
      `,
      expectedOutput: 'Comprehensive maintenance analysis report'
    };

    const result = await this.executeWithExperience(task, 'MAINTENANCE');

    // Marcus-specific learning: What worked in past maintenance
    if (result.guidance) {
      const failureWarnings = result.guidance.warningsFromFailures;
      if (failureWarnings.length > 0) {
        console.log(`[Marcus] Noting ${failureWarnings.length} past maintenance failures to avoid`);

        // Record lessons from failures
        for (const failure of failureWarnings) {
          this.recordLesson(
            `Avoid: ${failure.failureType} - ${failure.preventionStrategies?.[0] || 'Be careful'}`
          );
        }
      }
    }

    return result;
  }

  /**
   * Execute technical debt remediation
   */
  async executeDebtRemediation(
    debtItems: Array<{ id: string; type: string; severity: string }>,
    maxEffortHours: number
  ): Promise<ExecutionResult> {
    console.log('\n=== MARCUS: Tech Debt Remediation ===');
    console.log(`🔨 Remediating ${debtItems.length} debt items...`);

    const task: Task = {
      description: `
        Remediate technical debt:

        Items (${debtItems.length}):
        ${debtItems.map(d => `- [${d.severity}] ${d.type}: ${d.id}`).join('\n')}

        Constraints:
        - Max effort: ${maxEffortHours} hours
        - Prioritize by severity
        - Ensure backward compatibility

        Steps:
        1. Validate remediation plan
        2. Apply fixes incrementally
        3. Run tests after each fix
        4. Update documentation
        5. Create PR with changes
      `,
      expectedOutput: 'Remediation summary with applied fixes'
    };

    return this.executeWithExperience(task, 'MAINTENANCE');
  }
}

// ============================================================================
// Quinn - Quality Inspector Evolution
// ============================================================================

export class QuinnEvolvingAgent extends EvolvingAgentWrapper {
  private static QUINN_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 3,
    maxPatterns: 3,
    maxFailures: 10,   // Quinn needs extensive failure knowledge
    minSimilarity: 0.3,  // Very low threshold - catch any potential issue
    includeOtherAgents: true  // Learn from all agents' quality issues
  };

  constructor() {
    super({
      agent: agents.qualityInspector,
      agentId: 'quinn',
      agentRole: 'quality',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: QuinnEvolvingAgent.QUINN_CONSULTATION_OPTIONS
    });
  }

  /**
   * Quinn-specific task enhancement
   *
   * Quinn focuses on:
   * - Past quality gate results
   * - Common security vulnerabilities found
   * - Test coverage patterns
   * - Code smell patterns that caused issues
   */
  async executeQualityAudit(
    targetFiles: string[],
    auditTypes: string[]
  ): Promise<ExecutionResult> {
    console.log('\n=== QUINN: Quality Inspector ===');
    console.log('🔍 Auditing quality with self-navigation...');

    const task: Task = {
      description: `
        Perform quality audit:

        Target: ${targetFiles.length > 0 ? targetFiles.join(', ') : 'Full codebase'}
        Audit Types: ${auditTypes.join(', ')}

        Audit Checklist:
        1. Security Scan (OWASP Top 10)
        2. Code Quality Analysis
           - Complexity (cyclomatic, cognitive)
           - Duplication detection
           - Code smells
        3. Test Coverage Analysis
           - Unit test coverage
           - Integration test coverage
           - E2E test coverage
        4. Dependency Audit
           - Vulnerability scan
           - License compliance
        5. Documentation Quality
           - API documentation
           - Code comments
           - README completeness

        Output:
        - Quality score (0-100)
        - Issues by severity
        - Remediation recommendations
      `,
      expectedOutput: 'Comprehensive quality audit report'
    };

    const result = await this.executeWithExperience(task, 'QUALITY_AUDIT');

    // Quinn-specific learning: Quality patterns
    if (result.success) {
      this.recordDecision({
        decision: `Audit completed for ${targetFiles.length || 'full'} targets`,
        reasoning: 'Following established quality standards',
        alternatives: ['Quick scan', 'Deep scan', 'Security-focused'],
        outcome: 'Completed',
        impactScore: 0.9
      });
    }

    return result;
  }

  /**
   * Execute quality gate check
   */
  async executeQualityGateCheck(
    prNumber: number,
    branch: string
  ): Promise<ExecutionResult> {
    console.log('\n=== QUINN: Quality Gate Check ===');
    console.log(`🚦 Checking PR #${prNumber} on ${branch}...`);

    const task: Task = {
      description: `
        Quality Gate Check for PR #${prNumber}

        Branch: ${branch}

        Gate Requirements:
        1. All tests pass
        2. Test coverage >= 80%
        3. No critical security issues
        4. Technical debt ratio < 10%
        5. No blocking code smells

        Actions:
        1. Run full test suite
        2. Measure coverage
        3. Run security scan
        4. Check debt metrics
        5. Analyze new code quality

        Result: PASS / FAIL with details
      `,
      expectedOutput: 'Quality gate pass/fail verdict with details'
    };

    return this.executeWithExperience(task, 'QUALITY_AUDIT');
  }
}

// ============================================================================
// Betty - Bug Hunter Evolution
// ============================================================================

export class BettyEvolvingAgent extends EvolvingAgentWrapper {
  private static BETTY_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 3,
    maxFailures: 10,   // Betty needs to know about past bugs
    minSimilarity: 0.35,
    includeOtherAgents: true  // Learn from all agents' bug reports
  };

  constructor() {
    super({
      agent: agents.bugHunter,
      agentId: 'betty',
      agentRole: 'debugger',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: BettyEvolvingAgent.BETTY_CONSULTATION_OPTIONS
    });
  }

  /**
   * Betty-specific bug investigation
   */
  async executeBugInvestigation(
    bugDescription: string,
    errorLogs: string[] = [],
    affectedFiles: string[] = []
  ): Promise<ExecutionResult> {
    console.log('\n=== BETTY: Bug Hunter ===');
    console.log('🐛 Investigating bug with self-navigation...');

    const task: Task = {
      description: `
        Investigate Bug:
        ${bugDescription}

        Error Logs:
        ${errorLogs.join('\n') || 'No logs provided'}

        Potentially Affected Files:
        ${affectedFiles.join(', ') || 'Unknown'}

        Investigation Steps:
        1. Reproduce the bug
        2. Analyze stack trace
        3. Identify root cause
        4. Check similar past bugs
        5. Propose fix

        Output:
        - Root cause analysis
        - Fix recommendation
        - Regression test suggestions
      `,
      expectedOutput: 'Bug investigation report with fix recommendation'
    };

    const result = await this.executeWithExperience(task, 'BUG');

    if (result.success) {
      this.recordLesson(`Bug pattern: ${bugDescription.substring(0, 50)}...`);
    }

    return result;
  }

  /**
   * Execute bug fix with validation
   */
  async executeBugFix(
    bugId: string,
    rootCause: string,
    proposedFix: string
  ): Promise<ExecutionResult> {
    console.log('\n=== BETTY: Bug Fix ===');
    console.log(`🔧 Fixing bug ${bugId}...`);

    const task: Task = {
      description: `
        Fix Bug: ${bugId}

        Root Cause: ${rootCause}
        Proposed Fix: ${proposedFix}

        Steps:
        1. Implement fix
        2. Add regression test
        3. Run existing tests
        4. Document changes

        Ensure backward compatibility.
      `,
      expectedOutput: 'Bug fix with regression tests'
    };

    return this.executeWithExperience(task, 'BUG');
  }
}

// ============================================================================
// Eliza - Estimation Engine Evolution
// ============================================================================

export class ElizaEvolvingAgent extends EvolvingAgentWrapper {
  private static ELIZA_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 10,  // Eliza needs lots of historical data
    maxPatterns: 5,
    maxFailures: 5,
    minSimilarity: 0.4,
    includeOtherAgents: true  // Learn from all agents' actual vs estimated
  };

  constructor() {
    super({
      agent: agents.estimationEngine,
      agentId: 'eliza',
      agentRole: 'estimator',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: ElizaEvolvingAgent.ELIZA_CONSULTATION_OPTIONS
    });
  }

  /**
   * Eliza-specific estimation
   */
  async executeEstimation(
    itemDescription: string,
    itemType: 'epic' | 'feature' | 'story' | 'task',
    complexity: 'low' | 'medium' | 'high' = 'medium'
  ): Promise<ExecutionResult> {
    console.log('\n=== ELIZA: Estimation Engine ===');
    console.log('📊 Estimating with self-navigation...');

    const task: Task = {
      description: `
        Estimate ${itemType}: ${itemDescription}

        Complexity: ${complexity}

        Methods:
        1. Function Point Analysis (if applicable)
        2. Story Point Estimation (Fibonacci)
        3. PERT (Optimistic/Most Likely/Pessimistic)
        4. Historical comparison

        Output:
        - Story Points estimate
        - Function Points (if applicable)
        - Hour range (min-max)
        - Confidence level
        - Similar past items for reference
      `,
      expectedOutput: 'Multi-method estimation with confidence'
    };

    const result = await this.executeWithExperience(task, 'NEW_FEATURE');

    // Eliza learns from estimation accuracy
    if (result.guidance?.relevantExperiences) {
      const experiences = result.guidance.relevantExperiences;
      console.log(`[Eliza] Referencing ${experiences.length} similar past estimations`);
    }

    return result;
  }

  /**
   * Calibrate estimation based on actual outcomes
   */
  async executeEstimationCalibration(
    projectId: string,
    actualVsEstimated: Array<{ estimated: number; actual: number; type: string }>
  ): Promise<ExecutionResult> {
    console.log('\n=== ELIZA: Estimation Calibration ===');
    console.log(`📈 Calibrating based on ${actualVsEstimated.length} data points...`);

    const avgVariance = actualVsEstimated.reduce((acc, item) => {
      return acc + (item.actual - item.estimated) / item.estimated;
    }, 0) / actualVsEstimated.length;

    const task: Task = {
      description: `
        Calibrate Estimation Model for Project: ${projectId}

        Data Points: ${actualVsEstimated.length}
        Average Variance: ${(avgVariance * 100).toFixed(1)}%

        Analysis:
        1. Identify systematic bias
        2. Find patterns in over/under estimation
        3. Adjust weights for item types
        4. Update confidence intervals

        Output:
        - Calibration factors by type
        - Confidence adjustment
        - Recommendations
      `,
      expectedOutput: 'Calibration report with adjustment factors'
    };

    return this.executeWithExperience(task, 'MAINTENANCE');
  }
}

// ============================================================================
// Tessa - Test Engineer Evolution
// ============================================================================

export class TessaEvolvingAgent extends EvolvingAgentWrapper {
  private static TESSA_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 5,   // Tessa needs test patterns
    maxFailures: 5,
    minSimilarity: 0.45,
    includeOtherAgents: true  // Learn from Quinn's quality findings
  };

  constructor() {
    super({
      agent: agents.testEngineer,
      agentId: 'tessa',
      agentRole: 'tester',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: TessaEvolvingAgent.TESSA_CONSULTATION_OPTIONS
    });
  }

  /**
   * Tessa-specific test generation
   */
  async executeTestGeneration(
    targetCode: string,
    testTypes: string[] = ['unit', 'integration']
  ): Promise<ExecutionResult> {
    console.log('\n=== TESSA: Test Engineer ===');
    console.log('🧪 Generating tests with self-navigation...');

    const task: Task = {
      description: `
        Generate tests for:
        ${targetCode.substring(0, 500)}...

        Test Types: ${testTypes.join(', ')}

        Requirements:
        1. Happy path tests
        2. Edge case tests
        3. Error handling tests
        4. Boundary tests
        5. Mock dependencies where appropriate

        Coverage Target: >= 80%

        Output:
        - Test file(s) with all test cases
        - Coverage estimate
        - Test data fixtures
      `,
      expectedOutput: 'Comprehensive test suite'
    };

    const result = await this.executeWithExperience(task, 'TESTING');

    if (result.success) {
      this.recordDecision({
        decision: `Generated ${testTypes.join(', ')} tests`,
        reasoning: 'Based on code complexity and coverage requirements',
        alternatives: ['Unit only', 'Full E2E', 'Contract tests'],
        outcome: 'Generated',
        impactScore: 0.75
      });
    }

    return result;
  }

  /**
   * Execute test strategy for project
   */
  async executeTestStrategy(
    projectScope: string,
    existingCoverage: number
  ): Promise<ExecutionResult> {
    console.log('\n=== TESSA: Test Strategy ===');
    console.log(`📋 Creating strategy (current coverage: ${existingCoverage}%)...`);

    const task: Task = {
      description: `
        Create Test Strategy for: ${projectScope}

        Current Coverage: ${existingCoverage}%
        Target Coverage: 80%

        Strategy Components:
        1. Test pyramid recommendation
        2. Critical paths identification
        3. Test data strategy
        4. CI/CD integration plan
        5. Test maintenance plan

        Output:
        - Test strategy document
        - Priority test areas
        - Resource estimates
      `,
      expectedOutput: 'Complete test strategy'
    };

    return this.executeWithExperience(task, 'TESTING');
  }
}

// ============================================================================
// Miguel - Migration Architect Evolution
// ============================================================================

export class MiguelEvolvingAgent extends EvolvingAgentWrapper {
  private static MIGUEL_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 5,
    maxFailures: 10,  // Migrations are risky - need failure knowledge
    minSimilarity: 0.4,
    includeOtherAgents: true
  };

  constructor() {
    super({
      agent: agents.migrationArchitect,
      agentId: 'miguel',
      agentRole: 'migrator',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: MiguelEvolvingAgent.MIGUEL_CONSULTATION_OPTIONS
    });
  }

  /**
   * Miguel-specific migration planning
   */
  async executeMigrationAssessment(
    fromStack: string,
    toStack: string,
    scope: string
  ): Promise<ExecutionResult> {
    console.log('\n=== MIGUEL: Migration Architect ===');
    console.log('🚀 Assessing migration with self-navigation...');

    const task: Task = {
      description: `
        Migration Assessment:
        FROM: ${fromStack}
        TO: ${toStack}
        SCOPE: ${scope}

        Assessment Areas:
        1. Technical feasibility
        2. Risk assessment
        3. Effort estimation
        4. Compatibility analysis
        5. Rollback strategy

        Output:
        - Migration feasibility report
        - Risk matrix
        - Phased migration plan
        - Rollback procedures
      `,
      expectedOutput: 'Complete migration assessment'
    };

    const result = await this.executeWithExperience(task, 'MIGRATION');

    // Miguel learns heavily from past migration failures
    if (result.guidance?.warningsFromFailures?.length) {
      console.log(`[Miguel] ⚠️ ${result.guidance.warningsFromFailures.length} past migration failures to consider`);
    }

    return result;
  }

  /**
   * Execute migration step
   */
  async executeMigrationStep(
    stepName: string,
    stepDetails: string,
    rollbackPlan: string
  ): Promise<ExecutionResult> {
    console.log('\n=== MIGUEL: Migration Step ===');
    console.log(`📦 Executing: ${stepName}...`);

    const task: Task = {
      description: `
        Execute Migration Step: ${stepName}

        Details: ${stepDetails}

        Rollback Plan: ${rollbackPlan}

        Steps:
        1. Pre-migration backup
        2. Execute migration
        3. Validate results
        4. Update documentation
        5. Prepare for next step

        IMPORTANT: Stop immediately if validation fails.
      `,
      expectedOutput: 'Migration step completion report'
    };

    return this.executeWithExperience(task, 'MIGRATION');
  }
}

// ============================================================================
// Diana - Documentation Writer Evolution
// ============================================================================

export class DianaEvolvingAgent extends EvolvingAgentWrapper {
  private static DIANA_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 3,
    maxPatterns: 5,   // Diana needs documentation patterns
    maxFailures: 2,
    minSimilarity: 0.5,
    includeOtherAgents: false  // Focus on own documentation experience
  };

  constructor() {
    super({
      agent: agents.documentationWriter,
      agentId: 'diana',
      agentRole: 'documenter',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: DianaEvolvingAgent.DIANA_CONSULTATION_OPTIONS
    });
  }

  /**
   * Diana-specific documentation generation
   */
  async executeDocumentation(
    docType: 'api' | 'architecture' | 'user_guide' | 'readme',
    context: Record<string, any>
  ): Promise<ExecutionResult> {
    console.log('\n=== DIANA: Documentation Writer ===');
    console.log(`📝 Writing ${docType} documentation with self-navigation...`);

    const task: Task = {
      description: `
        Generate ${docType.toUpperCase()} Documentation

        Context:
        ${JSON.stringify(context, null, 2)}

        Requirements:
        1. Clear structure
        2. Code examples where relevant
        3. Diagrams/flowcharts descriptions
        4. Version information
        5. Quick start section

        Style:
        - Concise but complete
        - Consistent terminology
        - Practical examples
        - Progressive disclosure

        Output:
        - Complete ${docType} document (Markdown)
      `,
      expectedOutput: `${docType} documentation in Markdown`
    };

    return this.executeWithExperience(task, 'PROJECT_DEFINITION');
  }

  /**
   * Update existing documentation
   */
  async executeDocumentationUpdate(
    existingDoc: string,
    changes: string[]
  ): Promise<ExecutionResult> {
    console.log('\n=== DIANA: Documentation Update ===');
    console.log(`📄 Updating documentation with ${changes.length} changes...`);

    const task: Task = {
      description: `
        Update Documentation

        Changes to incorporate:
        ${changes.map((c, i) => `${i + 1}. ${c}`).join('\n')}

        Existing Document (excerpt):
        ${existingDoc.substring(0, 1000)}...

        Requirements:
        1. Maintain existing structure
        2. Update version info
        3. Mark deprecated items
        4. Add migration notes if needed

        Output:
        - Updated document
        - Change summary
      `,
      expectedOutput: 'Updated documentation'
    };

    return this.executeWithExperience(task, 'MAINTENANCE');
  }
}

// ============================================================================
// Peter - Product Owner Evolution
// ============================================================================

export class PeterEvolvingAgent extends EvolvingAgentWrapper {
  private static PETER_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 3,
    maxFailures: 3,
    minSimilarity: 0.45,
    includeOtherAgents: false  // Focus on product decisions
  };

  constructor() {
    super({
      agent: agents.productOwner,
      agentId: 'peter',
      agentRole: 'product_owner',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: PeterEvolvingAgent.PETER_CONSULTATION_OPTIONS
    });
  }

  /**
   * Peter-specific requirements analysis
   */
  async executeRequirementsAnalysis(
    businessNeed: string,
    stakeholders: string[] = []
  ): Promise<ExecutionResult> {
    console.log('\n=== PETER: Product Owner ===');
    console.log('📋 Analyzing requirements with self-navigation...');

    const task: Task = {
      description: `
        Requirements Analysis for:
        ${businessNeed}

        Stakeholders: ${stakeholders.join(', ') || 'Not specified'}

        Analysis:
        1. Business value assessment
        2. User story creation
        3. Acceptance criteria
        4. Priority recommendation
        5. Dependencies identification

        Output:
        - User stories (INVEST format)
        - Acceptance criteria
        - Priority matrix
        - Risk assessment
      `,
      expectedOutput: 'Requirements analysis with user stories'
    };

    const result = await this.executeWithExperience(task, 'PROJECT_DEFINITION');

    if (result.success) {
      this.recordDecision({
        decision: `Requirements for: ${businessNeed.substring(0, 40)}...`,
        reasoning: 'Based on business value and stakeholder input',
        alternatives: ['MVP scope', 'Full scope', 'Phased rollout'],
        outcome: 'Analyzed',
        impactScore: 0.85
      });
    }

    return result;
  }

  /**
   * Execute backlog prioritization
   */
  async executeBacklogPrioritization(
    backlogItems: Array<{ id: string; title: string; value: number; effort: number }>
  ): Promise<ExecutionResult> {
    console.log('\n=== PETER: Backlog Prioritization ===');
    console.log(`📊 Prioritizing ${backlogItems.length} items...`);

    const task: Task = {
      description: `
        Prioritize Backlog:

        Items (${backlogItems.length}):
        ${backlogItems.map(i => `- ${i.id}: ${i.title} (Value: ${i.value}, Effort: ${i.effort})`).join('\n')}

        Methods:
        1. WSJF (Weighted Shortest Job First)
        2. MoSCoW analysis
        3. Value vs Effort matrix
        4. Risk-adjusted priority

        Output:
        - Prioritized backlog
        - Justification per item
        - Sprint recommendations
      `,
      expectedOutput: 'Prioritized backlog with justifications'
    };

    return this.executeWithExperience(task, 'PROJECT_DEFINITION');
  }
}

// ============================================================================
// Paul - Project Lead Evolution
// ============================================================================

export class PaulEvolvingAgent extends EvolvingAgentWrapper {
  private static PAUL_CONSULTATION_OPTIONS: ConsultationOptions = {
    maxExperiences: 5,
    maxPatterns: 5,
    maxFailures: 5,
    minSimilarity: 0.4,
    includeOtherAgents: true  // Paul needs to know about all agents' issues
  };

  constructor() {
    super({
      agent: agents.projectLead,
      agentId: 'paul',
      agentRole: 'project_lead',
      enableExperienceConsultation: true,
      enableOutcomeLogging: true,
      consultationOptions: PaulEvolvingAgent.PAUL_CONSULTATION_OPTIONS
    });
  }

  /**
   * Paul-specific sprint planning
   */
  async executeSprintPlanning(
    sprintGoal: string,
    capacity: number,
    backlogItems: Array<{ id: string; points: number; priority: number }>
  ): Promise<ExecutionResult> {
    console.log('\n=== PAUL: Project Lead ===');
    console.log('📅 Planning sprint with self-navigation...');

    const task: Task = {
      description: `
        Sprint Planning:

        Goal: ${sprintGoal}
        Capacity: ${capacity} story points
        Available Items: ${backlogItems.length}

        Planning Steps:
        1. Select items within capacity
        2. Ensure sprint goal alignment
        3. Risk assessment
        4. Dependency ordering
        5. Resource allocation

        Output:
        - Sprint backlog (within capacity)
        - Risk items flagged
        - Dependency graph
        - Success criteria
      `,
      expectedOutput: 'Sprint plan with backlog selection'
    };

    const result = await this.executeWithExperience(task, 'PROJECT_DEFINITION');

    if (result.success) {
      this.recordDecision({
        decision: `Sprint: ${sprintGoal.substring(0, 40)}...`,
        reasoning: 'Based on capacity and backlog priorities',
        alternatives: ['Conservative', 'Aggressive', 'Focus on tech debt'],
        outcome: 'Planned',
        impactScore: 0.8
      });
    }

    return result;
  }

  /**
   * Execute project status review
   */
  async executeStatusReview(
    projectId: string,
    metrics: Record<string, number>
  ): Promise<ExecutionResult> {
    console.log('\n=== PAUL: Status Review ===');
    console.log(`📈 Reviewing project ${projectId}...`);

    const task: Task = {
      description: `
        Project Status Review: ${projectId}

        Metrics:
        ${Object.entries(metrics).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

        Analysis:
        1. Progress vs plan
        2. Risk status update
        3. Resource utilization
        4. Blocker identification
        5. Forecast adjustment

        Output:
        - Status summary
        - Risk register update
        - Action items
        - Forecast update
      `,
      expectedOutput: 'Project status report'
    };

    return this.executeWithExperience(task, 'PROJECT_DEFINITION');
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

// Singleton instances
let felixInstance: FelixEvolvingAgent | null = null;
let marcusInstance: MarcusEvolvingAgent | null = null;
let quinnInstance: QuinnEvolvingAgent | null = null;
let bettyInstance: BettyEvolvingAgent | null = null;
let elizaInstance: ElizaEvolvingAgent | null = null;
let tessaInstance: TessaEvolvingAgent | null = null;
let miguelInstance: MiguelEvolvingAgent | null = null;
let dianaInstance: DianaEvolvingAgent | null = null;
let peterInstance: PeterEvolvingAgent | null = null;
let paulInstance: PaulEvolvingAgent | null = null;

/**
 * Get Felix (Feature Architect) with evolution capabilities
 */
export function getEvolvingFelix(): FelixEvolvingAgent {
  if (!felixInstance) {
    felixInstance = new FelixEvolvingAgent();
  }
  return felixInstance;
}

/**
 * Get Marcus (Maintenance Specialist) with evolution capabilities
 */
export function getEvolvingMarcus(): MarcusEvolvingAgent {
  if (!marcusInstance) {
    marcusInstance = new MarcusEvolvingAgent();
  }
  return marcusInstance;
}

/**
 * Get Quinn (Quality Inspector) with evolution capabilities
 */
export function getEvolvingQuinn(): QuinnEvolvingAgent {
  if (!quinnInstance) {
    quinnInstance = new QuinnEvolvingAgent();
  }
  return quinnInstance;
}

/**
 * Get Betty (Bug Hunter) with evolution capabilities
 */
export function getEvolvingBetty(): BettyEvolvingAgent {
  if (!bettyInstance) {
    bettyInstance = new BettyEvolvingAgent();
  }
  return bettyInstance;
}

/**
 * Get Eliza (Estimation Engine) with evolution capabilities
 */
export function getEvolvingEliza(): ElizaEvolvingAgent {
  if (!elizaInstance) {
    elizaInstance = new ElizaEvolvingAgent();
  }
  return elizaInstance;
}

/**
 * Get Tessa (Test Engineer) with evolution capabilities
 */
export function getEvolvingTessa(): TessaEvolvingAgent {
  if (!tessaInstance) {
    tessaInstance = new TessaEvolvingAgent();
  }
  return tessaInstance;
}

/**
 * Get Miguel (Migration Architect) with evolution capabilities
 */
export function getEvolvingMiguel(): MiguelEvolvingAgent {
  if (!miguelInstance) {
    miguelInstance = new MiguelEvolvingAgent();
  }
  return miguelInstance;
}

/**
 * Get Diana (Documentation Writer) with evolution capabilities
 */
export function getEvolvingDiana(): DianaEvolvingAgent {
  if (!dianaInstance) {
    dianaInstance = new DianaEvolvingAgent();
  }
  return dianaInstance;
}

/**
 * Get Peter (Product Owner) with evolution capabilities
 */
export function getEvolvingPeter(): PeterEvolvingAgent {
  if (!peterInstance) {
    peterInstance = new PeterEvolvingAgent();
  }
  return peterInstance;
}

/**
 * Get Paul (Project Lead) with evolution capabilities
 */
export function getEvolvingPaul(): PaulEvolvingAgent {
  if (!paulInstance) {
    paulInstance = new PaulEvolvingAgent();
  }
  return paulInstance;
}

/**
 * Get all evolving agents (all 10)
 */
export function getAllEvolvingAgents(): {
  felix: FelixEvolvingAgent;
  marcus: MarcusEvolvingAgent;
  quinn: QuinnEvolvingAgent;
  betty: BettyEvolvingAgent;
  eliza: ElizaEvolvingAgent;
  tessa: TessaEvolvingAgent;
  miguel: MiguelEvolvingAgent;
  diana: DianaEvolvingAgent;
  peter: PeterEvolvingAgent;
  paul: PaulEvolvingAgent;
} {
  return {
    felix: getEvolvingFelix(),
    marcus: getEvolvingMarcus(),
    quinn: getEvolvingQuinn(),
    betty: getEvolvingBetty(),
    eliza: getEvolvingEliza(),
    tessa: getEvolvingTessa(),
    miguel: getEvolvingMiguel(),
    diana: getEvolvingDiana(),
    peter: getEvolvingPeter(),
    paul: getEvolvingPaul()
  };
}

/**
 * Get evolving agent by role name
 */
export function getEvolvingAgentByRole(role: string): EvolvingAgentWrapper | null {
  const roleMap: Record<string, () => EvolvingAgentWrapper> = {
    'felix': getEvolvingFelix,
    'architect': getEvolvingFelix,
    'marcus': getEvolvingMarcus,
    'maintenance': getEvolvingMarcus,
    'quinn': getEvolvingQuinn,
    'quality': getEvolvingQuinn,
    'betty': getEvolvingBetty,
    'debugger': getEvolvingBetty,
    'bug': getEvolvingBetty,
    'eliza': getEvolvingEliza,
    'estimator': getEvolvingEliza,
    'tessa': getEvolvingTessa,
    'tester': getEvolvingTessa,
    'miguel': getEvolvingMiguel,
    'migrator': getEvolvingMiguel,
    'diana': getEvolvingDiana,
    'documenter': getEvolvingDiana,
    'peter': getEvolvingPeter,
    'product_owner': getEvolvingPeter,
    'paul': getEvolvingPaul,
    'project_lead': getEvolvingPaul
  };

  const getter = roleMap[role.toLowerCase()];
  return getter ? getter() : null;
}

// ============================================================================
// Workflow Integration Helpers
// ============================================================================

/**
 * Execute NEW_FEATURE workflow with evolving agents
 */
export async function executeEvolvingFeatureWorkflow(
  description: string,
  context: Record<string, any> = {}
): Promise<{
  felix: ExecutionResult;
  quinn: ExecutionResult;
}> {
  const felix = getEvolvingFelix();
  const quinn = getEvolvingQuinn();

  // Felix designs
  const felixResult = await felix.executeFeatureDesign(description, context);

  // Quinn reviews (if Felix succeeded)
  let quinnResult: ExecutionResult;
  if (felixResult.success) {
    quinnResult = await quinn.executeQualityAudit([], ['code_quality', 'security']);
  } else {
    quinnResult = {
      success: false,
      output: { skipped: true, reason: 'Felix failed' },
      executionTime: 0,
      keyDecisions: [],
      lessonsLearned: ['Skipped due to previous failure']
    };
  }

  return { felix: felixResult, quinn: quinnResult };
}

/**
 * Execute MAINTENANCE workflow with evolving agents
 */
export async function executeEvolvingMaintenanceWorkflow(
  scope: string,
  focusAreas: string[]
): Promise<{
  marcus: ExecutionResult;
  quinn: ExecutionResult;
}> {
  const marcus = getEvolvingMarcus();
  const quinn = getEvolvingQuinn();

  // Marcus analyzes
  const marcusResult = await marcus.executeMaintenanceAnalysis(scope, focusAreas);

  // Quinn validates quality
  const quinnResult = await quinn.executeQualityAudit([], focusAreas);

  return { marcus: marcusResult, quinn: quinnResult };
}

/**
 * Execute BUG workflow with evolving agents
 */
export async function executeEvolvingBugWorkflow(
  bugDescription: string,
  errorLogs: string[] = []
): Promise<{
  betty: ExecutionResult;
  tessa: ExecutionResult;
}> {
  const betty = getEvolvingBetty();
  const tessa = getEvolvingTessa();

  // Betty investigates
  const bettyResult = await betty.executeBugInvestigation(bugDescription, errorLogs);

  // Tessa writes regression tests (if Betty found root cause)
  let tessaResult: ExecutionResult;
  if (bettyResult.success) {
    tessaResult = await tessa.executeTestGeneration(
      `Regression tests for: ${bugDescription}`,
      ['unit', 'integration']
    );
  } else {
    tessaResult = {
      success: false,
      output: { skipped: true, reason: 'Betty investigation incomplete' },
      executionTime: 0,
      keyDecisions: [],
      lessonsLearned: []
    };
  }

  return { betty: bettyResult, tessa: tessaResult };
}

/**
 * Execute MIGRATION workflow with evolving agents
 */
export async function executeEvolvingMigrationWorkflow(
  fromStack: string,
  toStack: string,
  scope: string
): Promise<{
  miguel: ExecutionResult;
  tessa: ExecutionResult;
  diana: ExecutionResult;
}> {
  const miguel = getEvolvingMiguel();
  const tessa = getEvolvingTessa();
  const diana = getEvolvingDiana();

  // Miguel assesses
  const miguelResult = await miguel.executeMigrationAssessment(fromStack, toStack, scope);

  // Tessa prepares test strategy
  const tessaResult = await tessa.executeTestStrategy(scope, 60);

  // Diana documents
  const dianaResult = await diana.executeDocumentation('architecture', {
    migration: { from: fromStack, to: toStack },
    scope
  });

  return { miguel: miguelResult, tessa: tessaResult, diana: dianaResult };
}

/**
 * Execute PROJECT_DEFINITION workflow with evolving agents
 */
export async function executeEvolvingProjectDefinitionWorkflow(
  businessNeed: string,
  stakeholders: string[]
): Promise<{
  peter: ExecutionResult;
  felix: ExecutionResult;
  paul: ExecutionResult;
  diana: ExecutionResult;
}> {
  const peter = getEvolvingPeter();
  const felix = getEvolvingFelix();
  const paul = getEvolvingPaul();
  const diana = getEvolvingDiana();

  // Peter analyzes requirements
  const peterResult = await peter.executeRequirementsAnalysis(businessNeed, stakeholders);

  // Felix designs architecture
  const felixResult = await felix.executeFeatureDesign(businessNeed, {
    requirements: peterResult.output
  });

  // Paul plans sprint
  const paulResult = await paul.executeSprintPlanning(
    businessNeed,
    40, // default capacity
    [] // backlog items from Peter's analysis
  );

  // Diana documents
  const dianaResult = await diana.executeDocumentation('readme', {
    project: businessNeed,
    requirements: peterResult.output,
    architecture: felixResult.output
  });

  return { peter: peterResult, felix: felixResult, paul: paulResult, diana: dianaResult };
}

/**
 * Execute TESTING workflow with evolving agents
 */
export async function executeEvolvingTestingWorkflow(
  targetCode: string,
  testTypes: string[]
): Promise<{
  tessa: ExecutionResult;
  quinn: ExecutionResult;
}> {
  const tessa = getEvolvingTessa();
  const quinn = getEvolvingQuinn();

  // Tessa generates tests
  const tessaResult = await tessa.executeTestGeneration(targetCode, testTypes);

  // Quinn reviews quality
  const quinnResult = await quinn.executeQualityAudit([], ['test_quality', 'coverage']);

  return { tessa: tessaResult, quinn: quinnResult };
}

// ============================================================================
// Exports
// ============================================================================

export default {
  // Agent Classes
  FelixEvolvingAgent,
  MarcusEvolvingAgent,
  QuinnEvolvingAgent,
  BettyEvolvingAgent,
  ElizaEvolvingAgent,
  TessaEvolvingAgent,
  MiguelEvolvingAgent,
  DianaEvolvingAgent,
  PeterEvolvingAgent,
  PaulEvolvingAgent,
  // Factory Functions
  getEvolvingFelix,
  getEvolvingMarcus,
  getEvolvingQuinn,
  getEvolvingBetty,
  getEvolvingEliza,
  getEvolvingTessa,
  getEvolvingMiguel,
  getEvolvingDiana,
  getEvolvingPeter,
  getEvolvingPaul,
  getAllEvolvingAgents,
  getEvolvingAgentByRole,
  // Workflow Helpers
  executeEvolvingFeatureWorkflow,
  executeEvolvingMaintenanceWorkflow,
  executeEvolvingBugWorkflow,
  executeEvolvingMigrationWorkflow,
  executeEvolvingProjectDefinitionWorkflow,
  executeEvolvingTestingWorkflow
};
