/**
 * Code-Maintenance-Agent
 *
 * Complete 6-stage workflow for automated codebase maintenance:
 * 1. Analysis → 2. Prioritization → 3. Planning →
 * 4. Execution → 5. Testing → 6. Deployment
 *
 * Week 8 - Code-Maintenance-Agent Implementation
 * Integrates with Marcus (Maintenance Specialist) + Quinn + Tessa + Eliza
 */

import { Team, Task, Agent } from 'kaibanjs';
import { agents } from '../configs/agents';
import QualityGateService from '../services/qualityGateService';

// ============================================================================
// FASE 37: SECURITY SCANNER INTEGRATION
// ============================================================================

/**
 * Interface for SecurityScanOrchestrator response
 */
interface SecurityScanResult {
  project_path: string;
  scanners_used: string[];
  languages_detected: string[];
  summary: {
    total_findings: number;
    critical: number;
    high: number;
    by_severity: Record<string, number>;
    by_scanner: Record<string, number>;
  };
  cwe_coverage: Record<string, number>;
  findings: Array<{
    id: string;
    rule_id: string;
    title: string;
    description: string;
    severity: string;
    scanner: string;
    location: {
      file: string;
      start_line: number;
      end_line: number;
      snippet?: string;
    };
    cwe_ids: string[];
    is_cwe_top_25: boolean;
    category?: string;
  }>;
}

/**
 * Call Python backend SecurityScanOrchestrator (Fase 37)
 */
async function executeSecurityScan(projectPath: string): Promise<SecurityScanResult | null> {
  try {
    console.log('🔒 Running SecurityScanOrchestrator via backend API...');

    const response = await fetch('http://localhost:8000/api/security/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_path: projectPath,
        scan_type: 'full',
        include_dependencies: true,
      }),
    });

    if (!response.ok) {
      console.warn(`Security scan API returned ${response.status}`);
      return null;
    }

    const result: SecurityScanResult = await response.json();
    console.log(`🔒 Security scan complete: ${result.summary?.total_findings || 0} findings`);
    return result;
  } catch (error) {
    console.warn(`Security scan failed: ${error}`);
    return null;
  }
}

/**
 * Convert security scan findings to analysis findings format
 */
function mapSecurityScanToFindings(scanResult: SecurityScanResult): Finding[] {
  return scanResult.findings.map((f, index) => ({
    id: f.id || `SEC-${String(index + 1).padStart(3, '0')}`,
    category: 'security' as const,
    severity: f.severity === 'critical' ? 'critical' :
              f.severity === 'high' ? 'high' :
              f.severity === 'medium' ? 'medium' : 'low',
    title: f.title,
    description: f.description,
    location: f.location ? `${f.location.file}:${f.location.start_line}` : 'Unknown',
    recommendation: `Fix ${f.cwe_ids?.join(', ') || 'security issue'} - ${f.description}`,
    estimatedEffort: f.severity === 'critical' ? 3 : f.severity === 'high' ? 2 : 1,
    riskIfNotFixed: f.severity === 'critical' || f.severity === 'high' ? 'high' : 'medium',
    autoFixable: false,
    // Fase 37: Include CWE data
    cweIds: f.cwe_ids,
    isCweTop25: f.is_cwe_top_25,
    scanner: f.scanner,
  }));
}

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface CodeMaintenanceRequest {
  // Scope of analysis
  scope: 'full_codebase' | 'module' | 'specific_files';
  targetFiles?: string[];  // For 'specific_files' scope
  modulePath?: string;      // For 'module' scope

  // Focus areas
  focusAreas?: Array<
    | 'dependencies'      // Outdated packages, vulnerabilities
    | 'code_quality'      // Code smells, complexity
    | 'security'          // Security vulnerabilities
    | 'performance'       // Performance bottlenecks
    | 'tests'             // Test coverage gaps
    | 'documentation'     // Missing docs
  >;

  // Quality thresholds
  thresholds?: {
    maxComplexity?: number;           // Default: 15
    minTestCoverage?: number;         // Default: 80%
    maxTechnicalDebtRatio?: number;   // Default: 10%
    maxDuplication?: number;          // Default: 5%
  };

  // Urgency level
  urgency?: 'low' | 'medium' | 'high' | 'critical';

  // Auto-execution flags
  autoFix?: {
    dependencies?: boolean;   // Auto-update dependencies
    formatting?: boolean;     // Auto-fix code formatting
    linting?: boolean;        // Auto-fix linting issues
  };
}

export interface CodeMaintenanceResult {
  // Stage 1: Analysis
  analysisReport: AnalysisReport;

  // Stage 2: Prioritization
  prioritizedFindings: PrioritizedFinding[];

  // Stage 3: Planning
  maintenancePlan: MaintenancePlan;

  // Stage 4: Execution Plan
  executionStrategy: ExecutionStrategy;

  // Stage 5: Testing Strategy
  testStrategy: TestStrategy;

  // Stage 6: Deployment Plan
  deploymentPlan: DeploymentPlan;

  // Metadata
  metadata: {
    executionTime: number;
    timestamp: Date;
    scope: string;
    agent: string;
  };
}

// Stage 1: Analysis types
export interface AnalysisReport {
  technicalDebtRatio: number;
  dependencyVulnerabilities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  codeSmells: {
    complexity: number;
    duplication: number;
    longMethods: number;
    largeClasses: number;
  };
  securityIssues: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  testCoverage: {
    line: number;
    branch: number;
    function: number;
  };
  performanceIssues: number;

  // Best Practice Compliance (SIG-TOP-10 & SOLID & GRASP & TDD)
  bestPracticeScore: {
    sigCompliance: {
      overall: number;  // 0-100%
      violations: {
        shortUnits: number;         // SIG #1
        simpleUnits: number;        // SIG #2
        writeOnce: number;          // SIG #3
        smallInterfaces: number;    // SIG #4
        separateConcerns: number;   // SIG #5
        looseCoupling: number;      // SIG #6
        balancedComponents: number; // SIG #7
        smallCodebase: number;      // SIG #8
        automatedPipeline: number;  // SIG #9
        cleanCode: number;          // SIG #10
      };
    };
    solidCompliance: {
      overall: number;  // 0-100%
      violations: {
        srp: number;  // Single Responsibility
        ocp: number;  // Open/Closed
        lsp: number;  // Liskov Substitution
        isp: number;  // Interface Segregation
        dip: number;  // Dependency Inversion
      };
    };
    graspCompliance: {
      overall: number;  // 0-100%
      violations: {
        informationExpert: number;  // Wrong class has responsibility
        lowCoupling: number;        // Too many dependencies
        highCohesion: number;       // Unrelated methods in class
      };
    };
    tddCompliance: {
      overall: number;  // 0-100%
      violations: {
        noTests: number;              // Production code without tests
        testAfterCode: number;        // Tests written after production code
        coverageDecrease: number;     // Commits that decrease coverage
      };
    };
    lawOfDemeter: {
      violations: number;  // Method call chains (a.getB().getC())
    };
    totalScore: number;  // Combined 0-100%
  };

  findings: Finding[];
}

export interface Finding {
  id: string;
  category: 'dependency' | 'code_smell' | 'security' | 'performance' | 'test' | 'documentation';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  location: string;
  recommendation: string;
  estimatedEffort: number;  // Story points
  riskIfNotFixed: 'high' | 'medium' | 'low';
  autoFixable: boolean;
  bestPractice?: string;  // SIG-TOP-10 #X or SOLID: Principle Name
  // Fase 37: Security scanner metadata
  cweIds?: string[];      // CWE identifiers (e.g., ['CWE-89', 'CWE-79'])
  isCweTop25?: boolean;   // Is this a CWE Top 25 vulnerability?
  scanner?: string;       // Which scanner detected this (e.g., 'opengrep', 'bandit')
}

// Stage 2: Prioritization types
export interface PrioritizedFinding extends Finding {
  priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
  riskScore: number;        // Impact × Likelihood (0-100)
  roi: number;              // Return on investment score
  scheduledFor: 'immediate' | 'this_week' | 'next_sprint' | 'backlog';
}

// Stage 3: Planning types
export interface MaintenancePlan {
  phases: MaintenancePhase[];
  totalEffort: number;
  estimatedDuration: string;
  dependencies: string[];
  risks: string[];
}

export interface MaintenancePhase {
  phaseNumber: number;
  name: string;
  tasks: MaintenanceTask[];
  effortSP: number;
  duration: string;
  prerequisites: string[];
}

export interface TaskAction {
  id: string;
  description: string;
  estimatedHours: number;  // Between 0.5 and 1.0 hours
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  result?: string;          // Result after completion
  blockedReason?: string;   // If status = blocked
}

export interface MaintenanceTask {
  id: string;
  title: string;
  type: 'automated' | 'manual' | 'semi-automated';
  effortSP: number;
  effortHours: number;     // Total hours (sum of actions)
  assignedAgent: string;
  toolsRequired: string[];
  dependencies: string[];
  actions: TaskAction[];   // 4-8 actions, each 0.5-1 hour
}

// Stage 4: Execution types
export interface ExecutionStrategy {
  automatedTasks: {
    id: string;
    tool: string;
    command: string;
    expectedOutcome: string;
  }[];
  manualTasks: {
    id: string;
    instructions: string;
    checklistItems: string[];
  }[];
  validationChecks: {
    type: 'test' | 'lint' | 'build' | 'security';
    command: string;
    passCriteria: string;
  }[];
}

// Stage 5: Testing types
export interface TestStrategy {
  regressionTests: {
    existing: number;
    toUpdate: number;
    new: number;
  };
  unitTests: {
    existing: number;
    new: number;
    coverageGoal: number;
  };
  integrationTests: {
    existing: number;
    new: number;
  };
  e2eTests: {
    existing: number;
    new: number;
  };
  performanceTests: {
    benchmarks: string[];
    thresholds: Record<string, number>;
  };
}

// Stage 6: Deployment types
export interface DeploymentPlan {
  strategy: 'blue_green' | 'canary' | 'rolling' | 'immediate';
  stages: DeploymentStage[];
  rollbackProcedure: string[];
  monitoringMetrics: string[];
  successCriteria: string[];
}

export interface DeploymentStage {
  name: string;
  description: string;
  duration: string;
  validation: string[];
}

// ============================================================================
// STAGE 1: ANALYSIS
// ============================================================================

async function executeAnalysisStage(
  request: CodeMaintenanceRequest,
  agent: Agent
): Promise<AnalysisReport> {
  console.log('\n📊 Stage 1: ANALYSIS');
  console.log('   Scanning codebase for issues...');

  // Initialize Quality Gate Service
  const qualityGateService = new QualityGateService();

  // Run quality checks using the service
  const qualityGateResult = await qualityGateService.checkPostImplementation({
    scope: request.scope,
    targetFiles: request.targetFiles,
    modulePath: request.modulePath,
    thresholds: request.thresholds
  });

  // Fase 37: Run SecurityScanOrchestrator when security focus is enabled
  let securityScanFindings: Finding[] = [];
  let securityIssueCounts = { critical: 0, high: 0, medium: 0, low: 0 };

  if (!request.focusAreas || request.focusAreas.includes('security')) {
    const projectPath = request.modulePath || request.targetFiles?.[0] || '.';
    const securityScanResult = await executeSecurityScan(projectPath);

    if (securityScanResult) {
      securityScanFindings = mapSecurityScanToFindings(securityScanResult);
      securityIssueCounts = {
        critical: securityScanResult.summary?.critical || 0,
        high: securityScanResult.summary?.high || 0,
        medium: securityScanResult.summary?.by_severity?.medium || 0,
        low: securityScanResult.summary?.by_severity?.low || 0,
      };
      console.log(`   ✓ SecurityScanOrchestrator: ${securityScanFindings.length} security findings`);
    }
  }

  // TODO: In production, also execute:
  // - npm audit / pip-audit for dependency vulnerabilities
  // - Clinic.js / py-spy for performance
  // - Jest / pytest for test coverage
  //
  // For now, combine quality gate findings with mock data for other categories
  const analysisReport: AnalysisReport = {
    technicalDebtRatio: 12.5,
    dependencyVulnerabilities: {
      critical: 1,
      high: 2,
      medium: 5,
      low: 8
    },
    codeSmells: {
      complexity: 7,
      duplication: 11,
      longMethods: 5,
      largeClasses: 2
    },
    // Fase 37: Use real security scan results when available
    securityIssues: securityScanFindings.length > 0 ? securityIssueCounts : {
      critical: 0,
      high: 3,
      medium: 7,
      low: 12
    },
    testCoverage: {
      line: 72.5,
      branch: 65.3,
      function: 78.9
    },
    performanceIssues: 4,

    // Best Practice Compliance Scores (from Quality Gate Service)
    bestPracticeScore: qualityGateResult.bestPracticeScore,

    findings: [
      // Mock findings for other categories (TODO: integrate real tools)
      {
        id: 'FIND-001',
        category: 'dependency',
        severity: 'critical',
        title: 'axios XSS vulnerability (CVE-2023-12345)',
        description: 'axios@0.21.1 has a known XSS vulnerability that allows attackers to inject malicious scripts',
        location: 'package.json:12',
        recommendation: 'Update to axios@1.6.2 or later',
        estimatedEffort: 1,
        riskIfNotFixed: 'high',
        autoFixable: true
      },
      {
        id: 'FIND-002',
        category: 'code_smell',
        severity: 'high',
        title: 'High cyclomatic complexity in processUserData()',
        description: 'Function has complexity of 18, exceeding threshold of 15',
        location: 'src/utils/userProcessor.ts:42-127',
        recommendation: 'Refactor using Extract Method pattern to reduce complexity',
        estimatedEffort: 3,
        riskIfNotFixed: 'medium',
        autoFixable: false
      },
      {
        id: 'FIND-003',
        category: 'security',
        severity: 'high',
        title: 'Weak password policy',
        description: 'Current policy allows passwords with only 6 characters and no special character requirement',
        location: 'src/auth/passwordValidator.ts:15',
        recommendation: 'Enforce minimum 12 characters with mix of letters, numbers, and special characters',
        estimatedEffort: 2,
        riskIfNotFixed: 'high',
        autoFixable: false
      },
      {
        id: 'FIND-004',
        category: 'performance',
        severity: 'medium',
        title: 'N+1 query in getUserPosts endpoint',
        description: 'Endpoint generates N+1 database queries when fetching user posts with comments',
        location: 'src/api/users.ts:78-92',
        recommendation: 'Add select_related() or eager loading to optimize query',
        estimatedEffort: 2,
        riskIfNotFixed: 'medium',
        autoFixable: false
      },
      {
        id: 'FIND-005',
        category: 'test',
        severity: 'medium',
        title: 'Low test coverage in payment module',
        description: 'Payment processing module has only 45% test coverage',
        location: 'src/payment/',
        recommendation: 'Add unit tests for all payment flows and edge cases',
        estimatedEffort: 5,
        riskIfNotFixed: 'high',
        autoFixable: false
      },
      // Best practice findings from Quality Gate Service
      ...qualityGateResult.findings,
      // Fase 37: Add real security scan findings when available
      ...securityScanFindings
    ]
  };

  console.log(`   ✓ Found ${analysisReport.findings.length} issues`);
  console.log(`   ✓ Technical Debt Ratio: ${analysisReport.technicalDebtRatio}%`);
  console.log(`   ✓ Test Coverage: ${analysisReport.testCoverage.line}%`);
  console.log(`   ✓ Best Practice Score: ${analysisReport.bestPracticeScore.totalScore}%`);
  console.log(`      - SIG-TOP-10 Compliance: ${analysisReport.bestPracticeScore.sigCompliance.overall}%`);
  console.log(`      - SOLID Compliance: ${analysisReport.bestPracticeScore.solidCompliance.overall}%`);
  console.log(`      - GRASP Compliance: ${analysisReport.bestPracticeScore.graspCompliance.overall}%`);
  console.log(`      - TDD Compliance: ${analysisReport.bestPracticeScore.tddCompliance.overall}%`);
  console.log(`      - Law of Demeter Violations: ${analysisReport.bestPracticeScore.lawOfDemeter.violations}`);

  return analysisReport;
}

// ============================================================================
// STAGE 2: PRIORITIZATION
// ============================================================================

async function executePrioritizationStage(
  analysisReport: AnalysisReport,
  agent: Agent
): Promise<PrioritizedFinding[]> {
  console.log('\n🎯 Stage 2: PRIORITIZATION');
  console.log('   Calculating risk scores and priorities...');

  // Calculate risk score for each finding
  const prioritized: PrioritizedFinding[] = analysisReport.findings.map(finding => {
    // Risk score = Impact × Likelihood
    const impactScore = {
      'critical': 10,
      'high': 7,
      'medium': 4,
      'low': 2
    }[finding.severity];

    const likelihoodScore = {
      'high': 10,
      'medium': 5,
      'low': 2
    }[finding.riskIfNotFixed];

    const riskScore = impactScore * likelihoodScore;

    // Calculate ROI (benefit / effort)
    const benefit = impactScore * 10;  // Severity impact on code quality
    const roi = benefit / finding.estimatedEffort;

    // Determine priority based on risk score and ROI
    let priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
    let scheduledFor: 'immediate' | 'this_week' | 'next_sprint' | 'backlog';

    if (finding.severity === 'critical') {
      priority = 'P0';
      scheduledFor = 'immediate';
    } else if (riskScore >= 70) {
      priority = 'P0';
      scheduledFor = 'immediate';
    } else if (riskScore >= 50 || finding.severity === 'high') {
      priority = 'P1';
      scheduledFor = 'this_week';
    } else if (riskScore >= 30) {
      priority = 'P2';
      scheduledFor = 'next_sprint';
    } else if (riskScore >= 15) {
      priority = 'P3';
      scheduledFor = 'next_sprint';
    } else {
      priority = 'P4';
      scheduledFor = 'backlog';
    }

    return {
      ...finding,
      priority,
      riskScore,
      roi,
      scheduledFor
    };
  });

  // Sort by priority, then risk score
  prioritized.sort((a, b) => {
    const priorityOrder = { 'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4 };
    const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
    if (priorityDiff !== 0) return priorityDiff;
    return b.riskScore - a.riskScore;
  });

  console.log(`   ✓ P0 (Critical): ${prioritized.filter(f => f.priority === 'P0').length}`);
  console.log(`   ✓ P1 (High): ${prioritized.filter(f => f.priority === 'P1').length}`);
  console.log(`   ✓ P2 (Medium): ${prioritized.filter(f => f.priority === 'P2').length}`);

  return prioritized;
}

// ============================================================================
// TASK ACTION BREAKDOWN HELPER
// ============================================================================

/**
 * Break down a task into 4-8 actions, each taking 0.5-1 hour
 * - If task needs >8 actions, it should be split into multiple tasks
 * - Minimum task estimate: 0.5 hours (= 1 action)
 * - Each action: 0.5-1.0 hours
 */
function generateTaskActions(
  finding: PrioritizedFinding,
  taskType: 'automated' | 'manual' | 'semi-automated'
): { actions: TaskAction[]; effortHours: number; shouldSplit: boolean } {

  // Convert Story Points to hours (1 SP ≈ 4 hours)
  let totalEstimatedHours = finding.estimatedEffort * 4;

  // Minimum task estimate: 0.5 hours
  if (totalEstimatedHours < 0.5) {
    totalEstimatedHours = 0.5;
  }

  // Calculate number of actions needed (0.5-1 hour each)
  // Use average of 0.75 hours per action for estimation
  const numActions = Math.ceil(totalEstimatedHours / 0.75);

  // If >8 actions needed, flag for task splitting
  if (numActions > 8) {
    return {
      actions: [],
      effortHours: totalEstimatedHours,
      shouldSplit: true
    };
  }

  // Ensure 4-8 actions per task
  const clampedNumActions = Math.max(4, Math.min(8, numActions));
  const hoursPerAction = totalEstimatedHours / clampedNumActions;

  // Generate actions based on finding category
  const actions: TaskAction[] = [];

  if (taskType === 'automated') {
    // Automated tasks: simpler action breakdown
    const baseActions = [
      'Review current implementation and identify issue',
      'Run automated tool/script to apply fix',
      'Verify fix resolves the issue',
      'Run test suite to ensure no regressions'
    ];

    for (let i = 0; i < clampedNumActions; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: baseActions[i] || `Additional verification step ${i - 3}`,
        estimatedHours: Math.round(hoursPerAction * 2) / 2, // Round to 0.5
        status: 'pending'
      });
    }

  } else if (finding.category === 'dependency') {
    // Dependency updates
    const depActions = [
      'Analyze dependency vulnerability and breaking changes',
      'Update package version in package.json',
      'Run npm install and resolve conflicts',
      'Update code for breaking changes if any',
      'Run full test suite',
      'Test integration with dependent modules',
      'Update documentation',
      'Create changelog entry'
    ];

    for (let i = 0; i < clampedNumActions && i < depActions.length; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: depActions[i],
        estimatedHours: Math.round(hoursPerAction * 2) / 2,
        status: 'pending'
      });
    }

  } else if (finding.category === 'code_smell') {
    // Check if this is a SIG-TOP-10 or SOLID violation
    let refactorActions: string[];

    if (finding.bestPractice?.includes('SIG-TOP-10 #2')) {
      // SIG #2: Write Simple Units (Cyclomatic Complexity)
      refactorActions = [
        'Measure current cyclomatic complexity',
        'Identify complex conditional logic',
        'Apply Strategy or Guard Clause pattern',
        'Extract complex conditions into separate methods',
        'Verify complexity is reduced to ≤10',
        'Add unit tests for each code path',
        'Run full test suite',
        'Document refactoring in code comments'
      ];
    } else if (finding.bestPractice?.includes('SIG-TOP-10 #3')) {
      // SIG #3: Write Code Once (DRY)
      refactorActions = [
        'Detect duplicate code blocks (≥6 lines)',
        'Analyze commonalities and differences',
        'Design abstraction (base class, mixin, or utility)',
        'Extract duplicated logic into reusable component',
        'Update all call sites to use extracted code',
        'Run tests to verify behavior unchanged',
        'Remove duplicate code',
        'Update documentation'
      ];
    } else if (finding.bestPractice?.includes('SIG-TOP-10 #4')) {
      // SIG #4: Keep Unit Interfaces Small
      refactorActions = [
        'Identify function with >4 parameters',
        'Group related parameters by responsibility',
        'Create Parameter Object or Config object',
        'Refactor function signature to accept object',
        'Update all call sites',
        'Add JSDoc/TypeDoc for new parameter types',
        'Run test suite',
        'Verify improved readability'
      ];
    } else if (finding.bestPractice?.includes('SOLID: Single Responsibility')) {
      // SOLID SRP
      refactorActions = [
        'Identify multiple responsibilities in class',
        'Determine primary responsibility for each',
        'Design separation: data access, logic, presentation',
        'Extract classes (e.g., Repository, Service, View)',
        'Update dependencies between new classes',
        'Add unit tests for each separated class',
        'Verify integration works correctly',
        'Update documentation and architecture diagrams'
      ];
    } else if (finding.bestPractice?.includes('SOLID: Open/Closed')) {
      // SOLID OCP
      refactorActions = [
        'Identify switch/if-else chain on object types',
        'Define interface or abstract base class',
        'Create concrete implementations for each type',
        'Replace conditionals with polymorphism',
        'Add Factory pattern if needed',
        'Test each concrete implementation',
        'Verify new types can be added without modification',
        'Update documentation with extension points'
      ];
    } else if (finding.bestPractice?.includes('SOLID: Liskov Substitution')) {
      // SOLID LSP
      refactorActions = [
        'Identify violated preconditions/postconditions',
        'Analyze inheritance hierarchy',
        'Decide: fix contract violation or use composition',
        'Implement solution (interface or composition)',
        'Update subclasses to honor contracts',
        'Add integration tests for polymorphic behavior',
        'Run full test suite',
        'Document class contracts and expectations'
      ];
    } else if (finding.bestPractice?.includes('GRASP: Information Expert')) {
      // GRASP Information Expert
      refactorActions = [
        'Identify which class has the information needed',
        'Analyze current responsibility assignment',
        'Move method to Information Expert class',
        'Update all callers to use correct class',
        'Verify behavior is maintained',
        'Add/update unit tests',
        'Run full test suite',
        'Document responsibility assignment'
      ];
    } else if (finding.bestPractice?.includes('GRASP: High Cohesion')) {
      // GRASP High Cohesion
      refactorActions = [
        'Identify unrelated responsibilities in class',
        'Group related methods by purpose',
        'Extract cohesive classes for each responsibility',
        'Update dependencies between classes',
        'Verify each class has focused purpose',
        'Add tests for extracted classes',
        'Run full test suite',
        'Update documentation'
      ];
    } else if (finding.bestPractice?.includes('Law of Demeter')) {
      // Law of Demeter
      refactorActions = [
        'Identify chained method calls (a.getB().getC())',
        'Analyze what information is actually needed',
        'Add delegation methods to hide internal structure',
        'Update callers to use single method call',
        'Verify encapsulation is improved',
        'Add unit tests for new delegation methods',
        'Run full test suite',
        'Document new public API'
      ];
    } else {
      // Generic refactoring
      refactorActions = [
        'Analyze code complexity and identify refactoring opportunities',
        'Design refactoring approach (Extract Method/Class)',
        'Implement refactoring incrementally',
        'Add/update unit tests for refactored code',
        'Run test suite and fix any failures',
        'Code review and pair programming session',
        'Update documentation and comments',
        'Verify performance is maintained or improved'
      ];
    }

    for (let i = 0; i < clampedNumActions && i < refactorActions.length; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: refactorActions[i],
        estimatedHours: Math.round(hoursPerAction * 2) / 2,
        status: 'pending'
      });
    }

  } else if (finding.category === 'security') {
    // Security fixes
    const securityActions = [
      'Analyze security vulnerability (OWASP/CVE details)',
      'Review OWASP guidelines for this vulnerability type',
      'Implement security fix following best practices',
      'Add security-specific unit tests',
      'Perform security testing (penetration test)',
      'Add security regression tests',
      'Update security documentation',
      'Notify stakeholders of security fix'
    ];

    for (let i = 0; i < clampedNumActions && i < securityActions.length; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: securityActions[i],
        estimatedHours: Math.round(hoursPerAction * 2) / 2,
        status: 'pending'
      });
    }

  } else if (finding.category === 'performance') {
    // Performance optimization
    const perfActions = [
      'Profile code to identify bottleneck',
      'Analyze performance metrics (response time, memory)',
      'Design optimization strategy',
      'Implement performance improvements',
      'Run performance benchmarks',
      'Compare before/after metrics',
      'Add performance regression tests',
      'Document optimization approach'
    ];

    for (let i = 0; i < clampedNumActions && i < perfActions.length; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: perfActions[i],
        estimatedHours: Math.round(hoursPerAction * 2) / 2,
        status: 'pending'
      });
    }

  } else if (finding.category === 'test') {
    // Check if this is a TDD violation
    let testActions: string[];

    if (finding.bestPractice?.includes('TDD: Test-Driven Development')) {
      // TDD: No tests exist
      testActions = [
        'Write failing test for first public method (RED)',
        'Implement minimal code to pass test (GREEN)',
        'Refactor while keeping test green (REFACTOR)',
        'Repeat RED-GREEN-REFACTOR for each method',
        'Add edge case and error scenario tests',
        'Achieve target coverage threshold',
        'Review test quality and maintainability',
        'Commit tests WITH production code'
      ];
    } else if (finding.bestPractice?.includes('TDD: Red-Green-Refactor')) {
      // TDD: Tests after code
      testActions = [
        'Review existing production code',
        'Write comprehensive tests for existing code',
        'Identify gaps in test coverage',
        'Add missing tests (unit, integration, edge cases)',
        'Refactor code while keeping tests green',
        'Document TDD practice for future features',
        'Setup pre-commit hooks to enforce test-first',
        'Update testing documentation'
      ];
    } else if (finding.bestPractice?.includes('TDD: Coverage should increase')) {
      // TDD: Coverage decreased
      testActions = [
        'Identify new code added without tests',
        'Write tests for untested code paths',
        'Add tests for edge cases and error scenarios',
        'Verify coverage returns to previous level',
        'Setup coverage threshold checks in CI/CD',
        'Configure pre-commit hooks to block coverage decrease',
        'Run full test suite',
        'Update coverage reports'
      ];
    } else {
      // Generic test coverage improvement
      testActions = [
        'Analyze code coverage gaps',
        'Identify critical paths needing tests',
        'Write unit tests for core functionality',
        'Write integration tests for key flows',
        'Add edge case and error scenario tests',
        'Achieve target coverage threshold',
        'Review test quality and maintainability',
        'Update testing documentation'
      ];
    }

    for (let i = 0; i < clampedNumActions && i < testActions.length; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: testActions[i],
        estimatedHours: Math.round(hoursPerAction * 2) / 2,
        status: 'pending'
      });
    }

  } else {
    // Documentation or other categories
    const genericActions = [
      'Review current state and requirements',
      'Plan implementation approach',
      'Implement changes',
      'Test changes thoroughly',
      'Code review',
      'Address review feedback',
      'Update documentation',
      'Final verification'
    ];

    for (let i = 0; i < clampedNumActions && i < genericActions.length; i++) {
      actions.push({
        id: `${finding.id}-action-${i + 1}`,
        description: genericActions[i],
        estimatedHours: Math.round(hoursPerAction * 2) / 2,
        status: 'pending'
      });
    }
  }

  return {
    actions,
    effortHours: totalEstimatedHours,
    shouldSplit: false
  };
}

// ============================================================================
// STAGE 3: PLANNING
// ============================================================================

async function executePlanningStage(
  prioritizedFindings: PrioritizedFinding[],
  agent: Agent
): Promise<MaintenancePlan> {
  console.log('\n📋 Stage 3: PLANNING');
  console.log('   Creating maintenance roadmap with action breakdown...');

  // Group tasks into phases
  const immediateTasks = prioritizedFindings.filter(f => f.scheduledFor === 'immediate');
  const thisWeekTasks = prioritizedFindings.filter(f => f.scheduledFor === 'this_week');
  const nextSprintTasks = prioritizedFindings.filter(f => f.scheduledFor === 'next_sprint');

  const phases: MaintenancePhase[] = [];

  // Phase 1: Immediate fixes (P0)
  if (immediateTasks.length > 0) {
    const phase1Tasks = immediateTasks.map(f => {
      const taskType: 'automated' | 'manual' | 'semi-automated' = f.autoFixable ? 'automated' : 'manual';
      const { actions, effortHours, shouldSplit } = generateTaskActions(f, taskType);

      if (shouldSplit) {
        console.log(`   ⚠️  Task ${f.id} needs >8 actions - consider splitting`);
      }

      return {
        id: f.id,
        title: f.title,
        type: taskType,
        effortSP: f.estimatedEffort,
        effortHours: effortHours,
        assignedAgent: f.category === 'security' ? 'Security Expert' : 'Maintenance Specialist',
        toolsRequired: f.autoFixable ? ['npm update', 'auto-fixer'] : ['Manual review'],
        dependencies: [],
        actions: actions
      };
    });

    phases.push({
      phaseNumber: 1,
      name: 'Critical Fixes (Immediate)',
      tasks: phase1Tasks,
      effortSP: immediateTasks.reduce((sum, f) => sum + f.estimatedEffort, 0),
      duration: '1-2 days',
      prerequisites: []
    });
  }

  // Phase 2: High priority (P1) - This week
  if (thisWeekTasks.length > 0) {
    const phase2Tasks = thisWeekTasks.map(f => {
      const taskType: 'automated' | 'manual' | 'semi-automated' =
        f.autoFixable ? 'automated' : 'manual';
      const { actions, effortHours, shouldSplit } = generateTaskActions(f, taskType);

      if (shouldSplit) {
        console.log(`   ⚠️  Task ${f.id} needs >8 actions - consider splitting`);
      }

      return {
        id: f.id,
        title: f.title,
        type: taskType,
        effortSP: f.estimatedEffort,
        effortHours: effortHours,
        assignedAgent: 'Maintenance Specialist',
        toolsRequired: f.autoFixable ? ['Refactoring tools', 'Auto-fixer'] : ['Manual review', 'Test frameworks'],
        dependencies: immediateTasks.map(t => t.id),
        actions: actions
      };
    });

    phases.push({
      phaseNumber: 2,
      name: 'High Priority Maintenance',
      tasks: phase2Tasks,
      effortSP: thisWeekTasks.reduce((sum, f) => sum + f.estimatedEffort, 0),
      duration: '3-5 days',
      prerequisites: ['Phase 1 complete', 'All tests passing']
    });
  }

  // Phase 3: Medium priority (P2/P3) - Next sprint
  if (nextSprintTasks.length > 0) {
    const phase3Tasks = nextSprintTasks.map(f => {
      const taskType: 'automated' | 'manual' | 'semi-automated' =
        f.category === 'test' ? 'semi-automated' : 'manual';
      const { actions, effortHours, shouldSplit } = generateTaskActions(f, taskType);

      if (shouldSplit) {
        console.log(`   ⚠️  Task ${f.id} needs >8 actions - consider splitting`);
      }

      return {
        id: f.id,
        title: f.title,
        type: taskType,
        effortSP: f.estimatedEffort,
        effortHours: effortHours,
        assignedAgent: f.category === 'test' ? 'Test Engineer' : 'Maintenance Specialist',
        toolsRequired: f.category === 'test' ? ['Testing frameworks', 'Coverage tools'] : ['Manual review', 'Refactoring tools'],
        dependencies: [],
        actions: actions
      };
    });

    phases.push({
      phaseNumber: 3,
      name: 'Planned Improvements',
      tasks: phase3Tasks,
      effortSP: nextSprintTasks.reduce((sum, f) => sum + f.estimatedEffort, 0),
      duration: '1-2 weeks',
      prerequisites: ['Sprint planning approval']
    });
  }

  const totalEffort = phases.reduce((sum, phase) => sum + phase.effortSP, 0);

  const plan: MaintenancePlan = {
    phases,
    totalEffort,
    estimatedDuration: `${Math.ceil(totalEffort / 5)} days (assuming 5 SP/day)`,
    dependencies: [
      'All tests must pass before deployment',
      'Code review approval required',
      'Security scan must pass'
    ],
    risks: [
      'Breaking changes may affect dependent modules',
      'Regression issues in untested code paths',
      'Deployment downtime for critical fixes'
    ]
  };

  console.log(`   ✓ ${phases.length} phases planned`);
  console.log(`   ✓ Total effort: ${totalEffort} SP`);
  console.log(`   ✓ Estimated duration: ${plan.estimatedDuration}`);

  return plan;
}

// ============================================================================
// STAGE 4: EXECUTION STRATEGY
// ============================================================================

async function executeExecutionStage(
  prioritizedFindings: PrioritizedFinding[],
  maintenancePlan: MaintenancePlan,
  agent: Agent
): Promise<ExecutionStrategy> {
  console.log('\n⚙️  Stage 4: EXECUTION STRATEGY');
  console.log('   Defining automated and manual tasks...');

  // Identify automated tasks (auto-fixable findings)
  const automatedTasks = prioritizedFindings
    .filter(f => f.autoFixable)
    .map(f => {
      let tool = 'auto-fixer';
      let command = 'auto-fix';

      // Category-specific tool selection
      if (f.category === 'dependency') {
        tool = 'npm update';
        const packageName = f.title.split(' ')[0];
        command = `npm update ${packageName}`;
      } else if (f.category === 'code_smell' && f.title.includes('formatting')) {
        tool = 'prettier';
        command = 'npx prettier --write .';
      } else if (f.category === 'security' && f.title.includes('package')) {
        tool = 'npm audit fix';
        command = 'npm audit fix';
      }

      return {
        id: f.id,
        tool,
        command,
        expectedOutcome: f.recommendation
      };
    });

  // Identify manual tasks (non-auto-fixable findings)
  const manualTasks = prioritizedFindings
    .filter(f => !f.autoFixable)
    .map(f => {
      const checklistItems: string[] = [
        `Review code at: ${f.location}`,
        `Understand issue: ${f.description}`,
        `Implement: ${f.recommendation}`
      ];

      // Category-specific checklist additions
      if (f.category === 'code_smell') {
        checklistItems.push('Refactor using Extract Method or Extract Class pattern');
        checklistItems.push('Add unit tests for refactored code');
      } else if (f.category === 'security') {
        checklistItems.push('Review OWASP guidelines for this vulnerability');
        checklistItems.push('Add security tests to prevent regression');
      } else if (f.category === 'performance') {
        checklistItems.push('Add performance benchmarks');
        checklistItems.push('Measure improvement with profiling tools');
      } else if (f.category === 'test') {
        checklistItems.push('Write test cases for all code paths');
        checklistItems.push('Achieve minimum coverage threshold');
      }

      checklistItems.push('Update documentation');
      checklistItems.push('Request code review');

      return {
        id: f.id,
        instructions: f.recommendation,
        checklistItems
      };
    });

  // Generate validation checks based on findings
  const validationChecks: ExecutionStrategy['validationChecks'] = [
    { type: 'test', command: 'npm test', passCriteria: 'All tests pass' },
    { type: 'build', command: 'npm run build', passCriteria: 'Build succeeds' }
  ];

  // Add lint check if code quality issues found
  if (prioritizedFindings.some(f => f.category === 'code_smell')) {
    validationChecks.push({
      type: 'lint',
      command: 'npm run lint',
      passCriteria: '0 errors, 0 warnings'
    });
  }

  // Add security check if security issues found
  if (prioritizedFindings.some(f => f.category === 'security' || f.category === 'dependency')) {
    validationChecks.push({
      type: 'security',
      command: 'npm audit',
      passCriteria: '0 high or critical vulnerabilities'
    });
  }

  console.log(`   ✓ ${automatedTasks.length} automated tasks`);
  console.log(`   ✓ ${manualTasks.length} manual tasks`);
  console.log(`   ✓ ${validationChecks.length} validation checks`);

  return {
    automatedTasks,
    manualTasks,
    validationChecks
  };
}

// ============================================================================
// STAGE 5: TEST STRATEGY
// ============================================================================

async function executeTestingStage(
  prioritizedFindings: PrioritizedFinding[],
  analysisReport: AnalysisReport,
  agent: Agent
): Promise<TestStrategy> {
  console.log('\n🧪 Stage 5: TEST STRATEGY');
  console.log('   Planning test coverage improvements...');

  // Calculate test requirements based on findings
  const testFindings = prioritizedFindings.filter(f => f.category === 'test');
  const codeSmellFindings = prioritizedFindings.filter(f => f.category === 'code_smell');
  const securityFindings = prioritizedFindings.filter(f => f.category === 'security');
  const performanceFindings = prioritizedFindings.filter(f => f.category === 'performance');

  // Regression tests: Update existing tests for refactored code
  const toUpdateRegression = codeSmellFindings.filter(f =>
    f.title.includes('refactor') || f.title.includes('complexity')
  ).length;

  const regressionTests = {
    existing: 120, // Mock baseline
    toUpdate: toUpdateRegression * 2, // Each refactor affects ~2 tests
    new: Math.max(testFindings.length, 5) // At least 5 new regression tests
  };

  // Unit tests: Based on test coverage gap
  const coverageGap = 85 - analysisReport.testCoverage.line;
  const newUnitTests = Math.ceil(coverageGap / 2); // Rough estimate: 2% coverage per test file

  const unitTests = {
    existing: 234, // Mock baseline
    new: newUnitTests + testFindings.length,
    coverageGoal: 85
  };

  // Integration tests: For security and dependency fixes
  const integrationTests = {
    existing: 45, // Mock baseline
    new: securityFindings.length + Math.floor(prioritizedFindings.filter(f => f.category === 'dependency').length / 2)
  };

  // E2E tests: For critical user flows affected by changes
  const criticalChanges = prioritizedFindings.filter(f => f.priority === 'P0' || f.priority === 'P1').length;
  const e2eTests = {
    existing: 12, // Mock baseline
    new: Math.min(criticalChanges, 5) // Cap at 5 new e2e tests
  };

  // Performance tests: For performance-related findings
  const performanceTests = {
    benchmarks: [] as string[],
    thresholds: {} as Record<string, number>
  };

  if (performanceFindings.length > 0) {
    performanceTests.benchmarks.push('API response time');
    performanceTests.thresholds['API response'] = 200; // ms

    if (performanceFindings.some(f => f.title.toLowerCase().includes('query'))) {
      performanceTests.benchmarks.push('Database query performance');
      performanceTests.thresholds['DB query'] = 100; // ms
    }

    if (performanceFindings.some(f => f.title.toLowerCase().includes('memory'))) {
      performanceTests.benchmarks.push('Memory usage');
      performanceTests.thresholds['Memory'] = 512; // MB
    }
  } else {
    // Default benchmarks if no specific performance issues
    performanceTests.benchmarks = ['API response time', 'Database query performance'];
    performanceTests.thresholds = { 'API response': 200, 'DB query': 100 };
  }

  console.log(`   ✓ Regression: ${regressionTests.new} new tests`);
  console.log(`   ✓ Unit: ${unitTests.new} new tests (target ${unitTests.coverageGoal}% coverage)`);
  console.log(`   ✓ Integration: ${integrationTests.new} new tests`);
  console.log(`   ✓ E2E: ${e2eTests.new} new tests`);
  console.log(`   ✓ Performance: ${performanceTests.benchmarks.length} benchmarks`);

  return {
    regressionTests,
    unitTests,
    integrationTests,
    e2eTests,
    performanceTests
  };
}

// ============================================================================
// STAGE 6: DEPLOYMENT PLAN
// ============================================================================

async function executeDeploymentStage(
  prioritizedFindings: PrioritizedFinding[],
  urgency: string,
  agent: Agent
): Promise<DeploymentPlan> {
  console.log('\n🚀 Stage 6: DEPLOYMENT PLAN');
  console.log('   Defining deployment strategy...');

  // Select deployment strategy based on risk and urgency
  const hasCriticalFindings = prioritizedFindings.some(f => f.priority === 'P0');
  const hasHighRiskChanges = prioritizedFindings.some(f => f.riskScore >= 70);
  const hasSecurityFixes = prioritizedFindings.some(f => f.category === 'security' && f.priority === 'P0');

  let strategy: DeploymentPlan['strategy'];
  let stages: DeploymentStage[];

  if (hasSecurityFixes && urgency === 'critical') {
    // Immediate deployment for critical security fixes
    strategy = 'immediate';
    stages = [
      {
        name: 'Production Deployment',
        description: 'Deploy critical security fixes immediately to all users',
        duration: '30 minutes',
        validation: [
          'Verify security vulnerability is patched',
          'Monitor error rates for 30 minutes',
          'Validate authentication/authorization still works'
        ]
      }
    ];
  } else if (hasCriticalFindings || hasHighRiskChanges) {
    // Canary deployment for high-risk changes
    strategy = 'canary';
    stages = [
      {
        name: 'Canary (10%)',
        description: 'Deploy to 10% of users to validate changes',
        duration: '2 hours',
        validation: [
          'Monitor error rates (must be < 0.1%)',
          'Check performance metrics (response time < 200ms)',
          'Verify core functionality works'
        ]
      },
      {
        name: 'Partial (50%)',
        description: 'Expand to 50% of users after successful canary',
        duration: '4 hours',
        validation: [
          'Verify user feedback is positive',
          'Monitor success metrics',
          'Check database performance'
        ]
      },
      {
        name: 'Full (100%)',
        description: 'Complete rollout to all users',
        duration: '2 hours',
        validation: [
          'Final metrics check',
          'Verify all features operational',
          'Monitor for 24 hours post-deployment'
        ]
      }
    ];
  } else if (urgency === 'high' || urgency === 'medium') {
    // Blue-green deployment for moderate changes
    strategy = 'blue_green';
    stages = [
      {
        name: 'Green Environment Deploy',
        description: 'Deploy to green environment (inactive)',
        duration: '1 hour',
        validation: [
          'Run full test suite in green environment',
          'Verify all services are healthy',
          'Test critical user journeys'
        ]
      },
      {
        name: 'Traffic Switch',
        description: 'Switch traffic from blue to green',
        duration: '30 minutes',
        validation: [
          'Monitor error rates during switch',
          'Verify smooth transition',
          'Keep blue environment ready for rollback'
        ]
      },
      {
        name: 'Blue Decommission',
        description: 'Decommission old blue environment after 24h stability',
        duration: '1 hour',
        validation: [
          'Confirm 24h stability period passed',
          'Archive blue environment for emergency rollback'
        ]
      }
    ];
  } else {
    // Rolling deployment for low-risk changes
    strategy = 'rolling';
    stages = [
      {
        name: 'Rolling Update Start',
        description: 'Begin rolling update across instances',
        duration: '2 hours',
        validation: [
          'Update instances one at a time',
          'Verify each instance after update',
          'Maintain service availability'
        ]
      },
      {
        name: 'Rolling Update Complete',
        description: 'Complete deployment to all instances',
        duration: '1 hour',
        validation: [
          'All instances updated successfully',
          'Run smoke tests',
          'Monitor for anomalies'
        ]
      }
    ];
  }

  // Rollback procedures based on deployment strategy
  const rollbackProcedure = [];
  if (strategy === 'canary') {
    rollbackProcedure.push('Stop canary rollout immediately');
    rollbackProcedure.push('Route all traffic back to stable version');
    rollbackProcedure.push('Analyze logs and metrics from canary phase');
  } else if (strategy === 'blue_green') {
    rollbackProcedure.push('Switch traffic back to blue environment');
    rollbackProcedure.push('Keep green environment for debugging');
  } else if (strategy === 'rolling') {
    rollbackProcedure.push('Halt rolling update');
    rollbackProcedure.push('Roll back updated instances to previous version');
  } else {
    rollbackProcedure.push('Revert to previous version immediately');
  }

  rollbackProcedure.push('Notify stakeholders and team');
  rollbackProcedure.push('Create incident report');
  rollbackProcedure.push('Investigate root cause before retry');

  // Monitoring metrics based on findings
  const monitoringMetrics = ['Error rate', 'Response time', 'CPU usage', 'Memory usage'];

  if (prioritizedFindings.some(f => f.category === 'security')) {
    monitoringMetrics.push('Authentication failures', 'Authorization denials');
  }

  if (prioritizedFindings.some(f => f.category === 'performance')) {
    monitoringMetrics.push('Database query time', 'API latency p95', 'Throughput');
  }

  if (prioritizedFindings.some(f => f.category === 'dependency')) {
    monitoringMetrics.push('Service health checks', 'Dependency availability');
  }

  // Success criteria
  const successCriteria = [
    'Error rate < 0.1%',
    'Response time < 200ms (p95)',
    'No critical bugs reported',
    'All automated tests passing'
  ];

  if (hasCriticalFindings) {
    successCriteria.push('Critical issues resolved and verified');
  }

  if (hasSecurityFixes) {
    successCriteria.push('Security vulnerability patched and validated');
  }

  console.log(`   ✓ Strategy: ${strategy}`);
  console.log(`   ✓ Stages: ${stages.length}`);
  console.log(`   ✓ Monitoring: ${monitoringMetrics.length} metrics`);

  return {
    strategy,
    stages,
    rollbackProcedure,
    monitoringMetrics,
    successCriteria
  };
}

// ============================================================================
// MAIN WORKFLOW EXECUTION
// ============================================================================

export async function executeCodeMaintenanceWorkflow(
  request: CodeMaintenanceRequest
): Promise<CodeMaintenanceResult> {
  const startTime = Date.now();

  console.log('\n' + '='.repeat(80));
  console.log('🔧 CODE-MAINTENANCE-AGENT WORKFLOW');
  console.log('='.repeat(80));
  console.log(`Scope: ${request.scope}`);
  console.log(`Focus: ${request.focusAreas?.join(', ') || 'All areas'}`);
  console.log(`Urgency: ${request.urgency || 'medium'}`);
  console.log('='.repeat(80));

  // Stage 1: Analysis
  const analysisReport = await executeAnalysisStage(request, agents.maintenanceSpecialist);

  // Stage 2: Prioritization
  const prioritizedFindings = await executePrioritizationStage(analysisReport, agents.qualityInspector);

  // Stage 3: Planning
  const maintenancePlan = await executePlanningStage(prioritizedFindings, agents.estimationEngine);

  // Stage 4: Execution Strategy
  const executionStrategy = await executeExecutionStage(
    prioritizedFindings,
    maintenancePlan,
    agents.maintenanceSpecialist
  );

  // Stage 5: Test Strategy
  const testStrategy = await executeTestingStage(
    prioritizedFindings,
    analysisReport,
    agents.testEngineer
  );

  // Stage 6: Deployment Plan
  const deploymentPlan = await executeDeploymentStage(
    prioritizedFindings,
    request.urgency || 'medium',
    agents.maintenanceSpecialist
  );

  const executionTime = Date.now() - startTime;

  console.log('\n' + '='.repeat(80));
  console.log('✅ CODE-MAINTENANCE-AGENT COMPLETED');
  console.log('='.repeat(80));
  console.log(`Total findings: ${analysisReport.findings.length}`);
  console.log(`Critical (P0): ${prioritizedFindings.filter(f => f.priority === 'P0').length}`);
  console.log(`High (P1): ${prioritizedFindings.filter(f => f.priority === 'P1').length}`);
  console.log(`Execution time: ${(executionTime / 1000).toFixed(2)}s`);
  console.log('='.repeat(80) + '\n');

  return {
    analysisReport,
    prioritizedFindings,
    maintenancePlan,
    executionStrategy,
    testStrategy,
    deploymentPlan,
    metadata: {
      executionTime,
      timestamp: new Date(),
      scope: request.scope,
      agent: 'Code-Maintenance-Agent (Marcus + Quinn + Tessa + Eliza)'
    }
  };
}

// ============================================================================
// VALIDATION
// ============================================================================

export function validateCodeMaintenanceRequest(request: CodeMaintenanceRequest): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Validate scope
  const validScopes = ['full_codebase', 'module', 'specific_files'];
  if (!validScopes.includes(request.scope)) {
    errors.push(`Invalid scope. Must be one of: ${validScopes.join(', ')}`);
  }

  // Validate scope-specific requirements
  if (request.scope === 'specific_files' && (!request.targetFiles || request.targetFiles.length === 0)) {
    errors.push('targetFiles required when scope is "specific_files"');
  }

  if (request.scope === 'module' && !request.modulePath) {
    errors.push('modulePath required when scope is "module"');
  }

  // Validate thresholds
  if (request.thresholds) {
    if (request.thresholds.maxComplexity && request.thresholds.maxComplexity < 1) {
      errors.push('maxComplexity must be at least 1');
    }
    if (request.thresholds.minTestCoverage &&
        (request.thresholds.minTestCoverage < 0 || request.thresholds.minTestCoverage > 100)) {
      errors.push('minTestCoverage must be between 0 and 100');
    }
    if (request.thresholds.maxTechnicalDebtRatio && request.thresholds.maxTechnicalDebtRatio < 0) {
      errors.push('maxTechnicalDebtRatio must be non-negative');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
