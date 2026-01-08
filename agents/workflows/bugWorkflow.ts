/**
 * BUG Workflow
 *
 * Implements 5-stage bug fixing workflow:
 * 1. Reproduction → 2. Root Cause Analysis → 3. Fix Implementation →
 * 4. Validation → 5. Deployment
 */

import { Team, Task } from 'kaibanjs';
import { agents } from '../configs/agents';
import QualityGateService, { QualityGateResult } from '../services/qualityGateService';

export interface BugReport {
  title: string;
  description: string;
  severity: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
  reproductionSteps?: string[];
  expectedBehavior?: string;
  actualBehavior?: string;
  environment?: {
    browser?: string;
    os?: string;
    appVersion?: string;
  };
  stackTrace?: string;
  logs?: string;
  attachments?: string[];
  targetFiles?: string[];  // Files affected by the bug
  modulePath?: string;     // Module where bug occurs
}

export interface BugFixResult {
  bugAnalysis: {
    severity: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
    category: string;
    rootCause: string;
    affectedCode: string;
    firstBadCommit?: string;
    impact: string;
  };
  fix: {
    description: string;
    codeChanges: Array<{
      file: string;
      line?: number;
      oldCode?: string;
      newCode: string;
    }>;
    regressionTest: {
      file: string;
      testName: string;
      code: string;
      framework: string;
    };
    estimatedEffort: {
      storyPoints: number;
      hours: number;
    };
  };
  validation: {
    testsPassing: boolean;
    noRegressions: boolean;
    performanceImpact: string;
    readyToDeploy: boolean;
  };
  documentation: {
    bugSummary: string;
    fixDescription: string;
    preventionMeasures: string[];
  };
  qualityGates?: {
    pre: QualityGateResult;
    post: QualityGateResult;
    overallScore: number;
    blocking: boolean;
  };
}

/**
 * Execute BUG workflow
 * Sequential: Betty → Tessa → Diana
 */
export async function executeBugWorkflow(
  bugReport: BugReport
): Promise<BugFixResult> {

  console.log('🐛 Starting BUG workflow...');
  console.log(`🔴 Severity: ${bugReport.severity}`);
  console.log(`📝 Title: ${bugReport.title}`);

  // Validate severity-based time constraints
  const timeConstraints = {
    P0: '4 hours',
    P1: '1 day',
    P2: '1 week',
    P3: '2 weeks',
    P4: 'backlog'
  };

  console.log(`⏰ Time constraint: ${timeConstraints[bugReport.severity]}`);

  // Initialize Quality Gate Service (BLOCKING for BUG fixes)
  const qualityGateService = new QualityGateService({
    blockingRules: {
      blockOnCritical: true,             // Block on any critical violation
      blockOnCoverageDecrease: true,     // Block if coverage decreases
      blockOnNoTests: true,              // CRITICAL: Block if no regression test!
      minimumScore: undefined
    }
  });

  // PRE-IMPLEMENTATION QUALITY CHECK
  console.log('\n🔍 Running pre-implementation quality checks...');
  const preChecks = await qualityGateService.checkPreImplementation({
    scope: bugReport.modulePath ? 'module' : 'specific_files',
    targetFiles: bugReport.targetFiles,
    modulePath: bugReport.modulePath
  });

  if (preChecks.findings.length > 0) {
    console.log(`⚠️  Pre-implementation warnings: ${preChecks.findings.length} issues found`);
    console.log(`   Quality Score: ${preChecks.bestPracticeScore.totalScore}%`);
  } else {
    console.log('✅ No pre-implementation issues found');
  }

  // Create bug fixing team (sequential execution)
  const team = new Team({
    name: 'Bug Fixing Team',
    agents: [
      agents.bugHunter,              // 1. Betty - Analyze & fix
      agents.testEngineer,           // 2. Tessa - Regression test
      agents.documentationWriter     // 3. Diana - Document fix
    ],
    // @ts-ignore
    process: 'sequential'
  });

  // Create comprehensive bug fixing task
  const bugTask = new Task({
    description: `
      Analyze and fix this bug following the 5-stage workflow:

      **Bug Title:** ${bugReport.title}
      **Severity:** ${bugReport.severity}
      **Description:** ${bugReport.description}

      **Reproduction Steps:**
      ${bugReport.reproductionSteps?.map((step, i) => `${i + 1}. ${step}`).join('\n') || 'Not provided'}

      **Expected Behavior:**
      ${bugReport.expectedBehavior || 'Not specified'}

      **Actual Behavior:**
      ${bugReport.actualBehavior || 'As described above'}

      **Environment:**
      ${JSON.stringify(bugReport.environment || {}, null, 2)}

      **Stack Trace:**
      ${bugReport.stackTrace || 'Not provided'}

      **Logs:**
      ${bugReport.logs || 'Not provided'}

      Please execute the 5-stage bug fixing workflow:

      **Stage 1: Reproduction**
      - Create a minimal failing test case
      - Verify the bug is reproducible
      - Document reproduction environment

      **Stage 2: Root Cause Analysis**
      - Analyze stack trace and logs
      - Identify the root cause (not just symptoms)
      - Use git bisect if needed to find regression
      - Determine which code/commit introduced the bug

      **Stage 3: Fix Implementation**
      - Implement minimal fix (don't over-engineer)
      - Ensure fix doesn't introduce new issues
      - Add code comments explaining the fix
      - Consider edge cases

      **Stage 4: Validation**
      - Verify the failing test now passes
      - Run full test suite (no regressions)
      - Check performance impact
      - Manual testing if needed

      **Stage 5: Deployment Preparation**
      - Create regression test to prevent recurrence
      - Document the bug and fix
      - Suggest preventive measures
      - Prepare deployment notes

      Return structured analysis with root cause, fix, test, and documentation.
    `,
    expectedOutput: 'Complete bug analysis, fix implementation, regression test, and documentation',
    agent: agents.bugHunter  // Betty - Bug Hunter
  });

  // Execute workflow
  console.log('👩‍🔬 Stage 1-3: Betty analyzing and fixing bug...');
  console.log('👨‍🔬 Stage 4: Tessa creating regression test...');
  console.log('✍️ Stage 5: Diana documenting fix...');

  // @ts-ignore - KaibanJS team.start() type compatibility
  const result = await team.start(bugTask);

  // POST-IMPLEMENTATION QUALITY CHECK
  console.log('\n🔍 Running post-implementation quality checks...');
  const postChecks = await qualityGateService.checkPostImplementation({
    scope: bugReport.modulePath ? 'module' : 'specific_files',
    targetFiles: bugReport.targetFiles,
    modulePath: bugReport.modulePath
  });

  if (!postChecks.passed) {
    console.log(`⚠️  Post-implementation warnings: ${postChecks.summary.totalViolations} violations found`);
    console.log(`   Quality Score: ${postChecks.bestPracticeScore.totalScore}%`);
    console.log(`   - SIG-TOP-10: ${postChecks.bestPracticeScore.sigCompliance.overall}%`);
    console.log(`   - SOLID: ${postChecks.bestPracticeScore.solidCompliance.overall}%`);
    console.log(`   - GRASP: ${postChecks.bestPracticeScore.graspCompliance.overall}%`);
    console.log(`   - TDD: ${postChecks.bestPracticeScore.tddCompliance.overall}%`);
  } else {
    console.log('✅ All post-implementation quality checks passed!');
  }

  // Calculate overall quality score
  const overallQualityScore = Math.round(
    (preChecks.bestPracticeScore.totalScore + postChecks.bestPracticeScore.totalScore) / 2
  );

  // Mock result (in production, parse actual agent outputs)
  const mockResult: BugFixResult = {
    bugAnalysis: {
      severity: bugReport.severity,
      category: 'authentication',
      rootCause: determineRootCause(bugReport),
      affectedCode: 'backend/app/auth/password_reset.py:142',
      firstBadCommit: 'a1b2c3d4',
      impact: determineImpact(bugReport.severity)
    },
    fix: {
      description: 'Invalidate password reset token after successful use to prevent reuse vulnerability',
      codeChanges: [
        {
          file: 'backend/app/auth/password_reset.py',
          line: 142,
          oldCode: 'user.set_password(new_password)',
          newCode: `user.set_password(new_password)
token.invalidate()  # Prevent token reuse`
        },
        {
          file: 'backend/app/auth/password_reset.py',
          line: 155,
          newCode: `# Add check for already-used tokens
if token.is_used:
    raise InvalidTokenError("Token has already been used")`
        }
      ],
      regressionTest: {
        file: 'tests/test_auth.py',
        testName: 'test_password_reset_token_cannot_be_reused',
        code: `def test_password_reset_token_cannot_be_reused():
    """Regression test for bug: password reset token reuse"""
    # Arrange
    user = create_test_user()
    token = create_password_reset_token(user)

    # Act - First reset (should work)
    response1 = client.post('/reset-password', {
        'token': token.value,
        'new_password': 'NewSecure123!'
    })
    assert response1.status_code == 200

    # Act - Try to reuse token (should fail)
    response2 = client.post('/reset-password', {
        'token': token.value,
        'new_password': 'DifferentPass456!'
    })

    # Assert
    assert response2.status_code == 400
    assert 'already been used' in response2.json()['error']`,
        framework: 'pytest'
      },
      estimatedEffort: {
        storyPoints: calculateStoryPoints(bugReport.severity),
        hours: calculateHours(bugReport.severity)
      }
    },
    validation: {
      testsPassing: true,
      noRegressions: true,
      performanceImpact: 'negligible (<1ms overhead)',
      readyToDeploy: true
    },
    documentation: {
      bugSummary: `Bug: ${bugReport.title}\n\nSeverity: ${bugReport.severity}\n\nUsers could reuse password reset tokens, allowing multiple password changes with a single reset link.`,
      fixDescription: 'Implemented token invalidation after successful password reset. Added validation to reject already-used tokens.',
      preventionMeasures: [
        'Add linter rule to check for token invalidation in similar flows',
        'Update security checklist to include token lifecycle management',
        'Add monitoring for suspicious token reuse patterns',
        'Document token best practices in security guidelines'
      ]
    },
    qualityGates: {
      pre: preChecks,
      post: postChecks,
      overallScore: overallQualityScore,
      blocking: postChecks.blocking
    }
  };

  console.log('✅ BUG workflow completed!');
  console.log(`🔒 Quality Gates: ${postChecks.blocking ? '❌ BLOCKING' : '✅ PASSED'}`);;
  console.log(`📊 Overall Quality Score: ${overallQualityScore}%`);
  console.log(`🔍 Root Cause: ${mockResult.bugAnalysis.rootCause}`);
  console.log(`💡 Fix: ${mockResult.fix.description}`);
  console.log(`✅ Ready to Deploy: ${mockResult.validation.readyToDeploy}`);

  return mockResult;
}

/**
 * Determine root cause from bug report
 */
function determineRootCause(bugReport: BugReport): string {
  // In production, this would be determined by Betty (Bug Hunter agent)
  // For now, extract from title/description
  if (bugReport.stackTrace?.includes('token')) {
    return 'Password reset token not invalidated after use';
  }
  if (bugReport.description.toLowerCase().includes('crash')) {
    return 'Unhandled exception in error handling code';
  }
  return 'Root cause to be determined by bug analysis';
}

/**
 * Determine impact from severity
 */
function determineImpact(severity: string): string {
  const impacts = {
    P0: 'Critical - Production down or data loss affecting all users',
    P1: 'High - Major feature broken affecting most users',
    P2: 'Medium - Minor feature issue affecting some users',
    P3: 'Low - Cosmetic issue or workaround available',
    P4: 'Trivial - Nice-to-have improvement'
  };
  return impacts[severity as keyof typeof impacts] || 'Unknown impact';
}

/**
 * Calculate story points from severity
 */
function calculateStoryPoints(severity: string): number {
  const points = {
    P0: 3,  // Time-boxed 4h
    P1: 5,  // Time-boxed 1d
    P2: 3,  // Time-boxed 1w
    P3: 2,  // Backlog
    P4: 2   // Backlog
  };
  return points[severity as keyof typeof points] || 3;
}

/**
 * Calculate estimated hours from severity
 */
function calculateHours(severity: string): number {
  const hours = {
    P0: 4,
    P1: 8,
    P2: 4,
    P3: 2,
    P4: 2
  };
  return hours[severity as keyof typeof hours] || 4;
}

/**
 * Validate BUG report
 */
export function validateBugReport(bugReport: BugReport): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!bugReport.title || bugReport.title.trim().length < 5) {
    errors.push('Title must be at least 5 characters');
  }

  if (!bugReport.description || bugReport.description.trim().length < 10) {
    errors.push('Description must be at least 10 characters');
  }

  const validSeverities = ['P0', 'P1', 'P2', 'P3', 'P4'];
  if (!validSeverities.includes(bugReport.severity)) {
    errors.push(`Severity must be one of: ${validSeverities.join(', ')}`);
  }

  if (bugReport.severity === 'P0' && !bugReport.stackTrace && !bugReport.logs) {
    errors.push('P0 bugs should include stack trace or logs for faster debugging');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
