#!/usr/bin/env ts-node
/**
 * Pre-commit Quality Gate Check
 *
 * Runs QualityGateService on staged files before commit
 * Week 12 Day 1-2 - Pre-commit hooks
 */

import { execSync } from 'child_process';
import QualityGateService from '../services/qualityGateService';

interface PreCommitConfig {
  enabledChecks?: {
    sig?: boolean;
    solid?: boolean;
    grasp?: boolean;
    tdd?: boolean;
    testingPatterns?: boolean;
    designPatterns?: boolean;
    cleanCode?: boolean;
    lawOfDemeter?: boolean;
    superclaude?: boolean;  // Week 6 Day 3: SuperClaude integration
  };
  blockingRules?: {
    blockOnCritical?: boolean;
    blockOnCoverageDecrease?: boolean;
    blockOnNoTests?: boolean;
    minimumScore?: number;
  };
  skipIfNoStagedFiles?: boolean;
  verbose?: boolean;
}

/**
 * Get list of staged files
 */
function getStagedFiles(): string[] {
  try {
    const output = execSync('git diff --cached --name-only --diff-filter=ACMR', {
      encoding: 'utf-8'
    });

    return output
      .split('\n')
      .filter(file => file.trim().length > 0)
      .filter(file =>
        file.endsWith('.ts') ||
        file.endsWith('.tsx') ||
        file.endsWith('.js') ||
        file.endsWith('.jsx')
      );
  } catch (error) {
    console.error('Error getting staged files:', error);
    return [];
  }
}

/**
 * Main pre-commit check
 */
async function preCommitCheck(config: PreCommitConfig = {}): Promise<void> {
  const {
    enabledChecks = {
      sig: true,
      solid: true,
      grasp: true,
      tdd: true,
      testingPatterns: true,
      designPatterns: true,
      cleanCode: true,
      lawOfDemeter: true,
      superclaude: true  // Week 6 Day 3: SuperClaude integration
    },
    blockingRules = {
      blockOnCritical: true,
      blockOnCoverageDecrease: true,
      blockOnNoTests: false,  // Don't block on missing tests in pre-commit
      minimumScore: undefined
    },
    skipIfNoStagedFiles = true,
    verbose = false
  } = config;

  console.log('\n🔍 Running pre-commit quality checks...\n');

  // Get staged files
  const stagedFiles = getStagedFiles();

  if (stagedFiles.length === 0) {
    if (skipIfNoStagedFiles) {
      console.log('ℹ️  No staged TypeScript/JavaScript files found');
      console.log('✅ Pre-commit check skipped\n');
      process.exit(0);
    }
  }

  if (verbose) {
    console.log(`📝 Checking ${stagedFiles.length} staged files:`);
    stagedFiles.forEach(file => console.log(`   - ${file}`));
    console.log();
  }

  // Initialize QualityGateService
  const qualityGateService = new QualityGateService({
    enabledChecks: enabledChecks as any,
    blockingRules: blockingRules as any
  });

  // Run quality checks
  try {
    const result = await qualityGateService.checkPostImplementation({
      scope: 'specific_files',
      targetFiles: stagedFiles.map(f => `../../${f}`)  // Adjust path from scripts/
    });

    // Display results
    console.log('Quality Gate Results:');
    console.log('===================');
    console.log(`Status: ${result.passed ? '✅ PASSED' : '❌ FAILED'}${result.blocking ? ' (BLOCKING)' : ''}`);
    console.log(`Overall Score: ${result.bestPracticeScore.totalScore}%`);
    console.log();

    console.log(`Violations: ${result.summary.totalViolations} total`);
    console.log(`  - Critical: ${result.summary.criticalViolations}`);
    console.log(`  - High: ${result.summary.highViolations}`);
    console.log(`  - Medium: ${result.summary.mediumViolations}`);
    console.log(`  - Low: ${result.summary.lowViolations}`);
    console.log();

    if (verbose && result.findings.length > 0) {
      console.log('Category Scores:');
      console.log(`  - SIG-TOP-10:        ${result.bestPracticeScore.sigCompliance.overall}%`);
      console.log(`  - SOLID:             ${result.bestPracticeScore.solidCompliance.overall}%`);
      console.log(`  - GRASP:             ${result.bestPracticeScore.graspCompliance.overall}%`);
      console.log(`  - TDD:               ${result.bestPracticeScore.tddCompliance.overall}%`);
      console.log(`  - Testing Patterns:  ${result.bestPracticeScore.testingPatternsCompliance.overall}%`);
      console.log(`  - Design Patterns:   ${result.bestPracticeScore.designPatternsCompliance.overall}%`);
      console.log(`  - Clean Code:        ${result.bestPracticeScore.cleanCodeCompliance.overall}%`);
      console.log();

      // Week 6 Day 4: Show SuperClaude findings separately
      const superclaudeFindings = result.findings.filter(f =>
        f.id.startsWith('SC-') || f.bestPractice?.includes('SuperClaude')
      );
      if (superclaudeFindings.length > 0) {
        console.log(`  - SuperClaude:       ${superclaudeFindings.length} findings from 20+ advanced checks`);
        console.log();
      }
    }

    // Display findings
    if (result.findings.length > 0) {
      console.log('Findings:');
      console.log('=========');

      result.findings.forEach((finding, index) => {
        const icon = finding.severity === 'critical' ? '🚨' :
                     finding.severity === 'high' ? '❌' :
                     finding.severity === 'medium' ? '⚠️' : 'ℹ️';

        console.log(`${index + 1}. ${icon} [${finding.severity.toUpperCase()}] ${finding.title}`);
        console.log(`   Location: ${finding.location}`);
        console.log(`   ${finding.description}`);
        console.log(`   💡 ${finding.recommendation}`);
        console.log(`   Effort: ${finding.estimatedEffort} story points`);
        console.log();
      });
    }

    console.log(`Execution Time: ${result.metadata.executionTime}ms\n`);

    // Block commit if quality gates failed
    if (result.blocking) {
      console.error('❌ COMMIT BLOCKED: Fix quality violations before committing\n');
      console.error(`Run 'npm run quality:check' to see all violations\n`);
      process.exit(1);
    }

    if (!result.passed) {
      console.log('⚠️  Quality gates did not pass, but commit is allowed (warnings only)\n');
      console.log('Consider fixing these issues before your next commit\n');
    } else {
      console.log('✅ All quality checks passed! Proceeding with commit\n');
    }

    process.exit(0);

  } catch (error) {
    console.error('Error running quality checks:', error);
    console.error('\n⚠️  Quality check failed to run - allowing commit\n');
    process.exit(0);  // Don't block commit on check failure
  }
}

// Run if executed directly
if (require.main === module) {
  const args = process.argv.slice(2);
  const verbose = args.includes('--verbose') || args.includes('-v');
  const skipTests = args.includes('--skip-tests');
  const strict = args.includes('--strict');

  const config: PreCommitConfig = {
    verbose,
    enabledChecks: {
      sig: true,
      solid: true,
      grasp: true,
      tdd: !skipTests,
      testingPatterns: !skipTests,
      designPatterns: true,
      cleanCode: true,
      lawOfDemeter: true,
      superclaude: true  // Week 6 Day 3: SuperClaude integration
    },
    blockingRules: {
      blockOnCritical: true,
      blockOnCoverageDecrease: !skipTests,
      blockOnNoTests: false,
      minimumScore: strict ? 70 : undefined
    }
  };

  preCommitCheck(config).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { preCommitCheck, getStagedFiles };
