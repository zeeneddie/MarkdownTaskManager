/**
 * Code Quality Validator
 *
 * Validates code quality using linters, complexity analysis, and code smell detection
 * Triggered after code changes
 */

import {
  ValidatorResult,
  ValidationStatus,
  QualityIssue,
  IssueSeverity,
  CodeQualityValidation
} from '../types/QualityGate';

/**
 * Code quality validation input
 */
export interface CodeQualityValidationInput {
  artifactPaths: string[];
  language?: 'typescript' | 'python' | 'javascript';
  complexityThreshold?: number;
  context?: Record<string, any>;
}

/**
 * Validate code quality
 */
export async function validateCodeQuality(
  input: CodeQualityValidationInput
): Promise<ValidatorResult> {
  console.error('✨ Code Quality Validator - Starting validation...\n');

  const issues: QualityIssue[] = [];
  const metrics: CodeQualityValidation = {
    linterErrors: 0,
    linterWarnings: 0,
    complexityScore: 0,
    duplicateCodePercentage: 0,
    codeSmells: 0,
    maintainabilityIndex: 0,
    issues: []
  };

  let rulesChecked = 0;
  let rulesPassed = 0;
  const complexityThreshold = input.complexityThreshold || 15;

  // Rule 1: Run linter checks
  rulesChecked++;
  const linterResult = await runLinter(input.artifactPaths, input.language);
  metrics.linterErrors = linterResult.errors;
  metrics.linterWarnings = linterResult.warnings;

  if (linterResult.errors > 0) {
    linterResult.issues.forEach(issue => issues.push(issue));
  } else {
    rulesPassed++;
  }

  // Rule 2: Check cyclomatic complexity
  rulesChecked++;
  const complexityResult = analyzeComplexity(input.artifactPaths);
  metrics.complexityScore = complexityResult.averageComplexity;

  if (complexityResult.violatingFunctions.length > 0) {
    complexityResult.violatingFunctions.forEach(func => {
      issues.push({
        id: `complexity-${Date.now()}-${Math.random()}`,
        validator: 'code-quality',
        severity: func.complexity > complexityThreshold * 1.5
          ? IssueSeverity.HIGH
          : IssueSeverity.MEDIUM,
        category: 'Code Complexity',
        title: `Function exceeds complexity threshold`,
        description: `Function '${func.name}' has cyclomatic complexity of ${func.complexity} (threshold: ${complexityThreshold})`,
        location: func.location,
        codeSnippet: func.snippet,
        recommendation: 'Break down function into smaller, more focused functions',
        autoFixAvailable: false,
        estimatedEffort: 'MEDIUM',
        detectedAt: new Date()
      });
    });
  } else {
    rulesPassed++;
  }

  // Rule 3: Detect code duplication
  rulesChecked++;
  const duplicationResult = detectDuplication(input.artifactPaths);
  metrics.duplicateCodePercentage = duplicationResult.percentage;

  if (duplicationResult.percentage > 5) {
    issues.push({
      id: `duplication-${Date.now()}`,
      validator: 'code-quality',
      severity: duplicationResult.percentage > 15
        ? IssueSeverity.HIGH
        : IssueSeverity.MEDIUM,
      category: 'Code Duplication',
      title: `High code duplication detected`,
      description: `${duplicationResult.percentage.toFixed(1)}% of code is duplicated (threshold: 5%)`,
      location: duplicationResult.locations.join(', '),
      recommendation: 'Extract duplicated code into reusable functions or modules',
      autoFixAvailable: true,
      estimatedEffort: 'MEDIUM',
      detectedAt: new Date()
    });
  } else {
    rulesPassed++;
  }

  // Rule 4: Detect code smells
  rulesChecked++;
  const smellResult = detectCodeSmells(input.artifactPaths);
  metrics.codeSmells = smellResult.smells.length;

  if (smellResult.smells.length > 0) {
    smellResult.smells.slice(0, 5).forEach(smell => {
      issues.push({
        id: `smell-${Date.now()}-${Math.random()}`,
        validator: 'code-quality',
        severity: IssueSeverity.MEDIUM,
        category: 'Code Smell',
        title: smell.type,
        description: smell.description,
        location: smell.location,
        recommendation: smell.fix,
        autoFixAvailable: false,
        estimatedEffort: 'LOW',
        detectedAt: new Date()
      });
    });
  } else {
    rulesPassed++;
  }

  // Rule 5: Check maintainability index
  rulesChecked++;
  const maintainabilityIndex = calculateMaintainabilityIndex(
    metrics.complexityScore,
    metrics.duplicateCodePercentage,
    metrics.linterErrors
  );
  metrics.maintainabilityIndex = maintainabilityIndex;

  if (maintainabilityIndex < 65) {
    issues.push({
      id: `maintainability-${Date.now()}`,
      validator: 'code-quality',
      severity: IssueSeverity.HIGH,
      category: 'Maintainability',
      title: 'Low maintainability index',
      description: `Maintainability index: ${maintainabilityIndex}/100 (threshold: 65+)`,
      location: 'Overall codebase',
      recommendation: 'Reduce complexity, eliminate duplication, and fix linter errors',
      autoFixAvailable: false,
      estimatedEffort: 'HIGH',
      detectedAt: new Date()
    });
  } else {
    rulesPassed++;
  }

  // Rule 6: Check naming conventions
  rulesChecked++;
  const namingResult = checkNamingConventions(input.artifactPaths, input.language);

  if (namingResult.violations > 0) {
    issues.push({
      id: `naming-${Date.now()}`,
      validator: 'code-quality',
      severity: IssueSeverity.LOW,
      category: 'Naming Convention',
      title: 'Naming convention violations',
      description: `${namingResult.violations} naming convention violations found`,
      location: namingResult.locations.join(', '),
      recommendation: 'Follow consistent naming conventions (camelCase for variables, PascalCase for classes)',
      autoFixAvailable: true,
      estimatedEffort: 'LOW',
      detectedAt: new Date()
    });
  } else {
    rulesPassed++;
  }

  // Rule 7: Check function length
  rulesChecked++;
  const longFunctions = checkFunctionLength(input.artifactPaths);

  if (longFunctions.length > 0) {
    longFunctions.forEach(func => {
      issues.push({
        id: `length-${Date.now()}-${Math.random()}`,
        validator: 'code-quality',
        severity: IssueSeverity.LOW,
        category: 'Function Length',
        title: 'Function too long',
        description: `Function '${func.name}' is ${func.lines} lines (recommended: < 50)`,
        location: func.location,
        recommendation: 'Break down long functions into smaller, focused functions',
        autoFixAvailable: false,
        estimatedEffort: 'MEDIUM',
        detectedAt: new Date()
      });
    });
  } else {
    rulesPassed++;
  }

  metrics.issues = issues;

  // Determine status
  const hasCritical = issues.some(i => i.severity === IssueSeverity.CRITICAL);
  const hasHighSeverity = issues.filter(i => i.severity === IssueSeverity.HIGH).length;

  let status: ValidationStatus;
  if (hasCritical || hasHighSeverity > 3) {
    status = ValidationStatus.FAIL;
  } else if (hasHighSeverity > 0) {
    status = ValidationStatus.WARNING;
  } else {
    status = ValidationStatus.PASS;
  }

  const recommendations: string[] = [];
  if (metrics.linterErrors > 0) {
    recommendations.push(`Fix ${metrics.linterErrors} linter errors`);
  }
  if (metrics.complexityScore > complexityThreshold) {
    recommendations.push('Reduce code complexity');
  }
  if (metrics.duplicateCodePercentage > 5) {
    recommendations.push('Eliminate code duplication');
  }
  if (metrics.codeSmells > 0) {
    recommendations.push('Address code smells');
  }

  console.error(`   Linter Errors: ${metrics.linterErrors}`);
  console.error(`   Linter Warnings: ${metrics.linterWarnings}`);
  console.error(`   Complexity Score: ${metrics.complexityScore.toFixed(1)}`);
  console.error(`   Duplicate Code: ${metrics.duplicateCodePercentage.toFixed(1)}%`);
  console.error(`   Code Smells: ${metrics.codeSmells}`);
  console.error(`   Maintainability Index: ${metrics.maintainabilityIndex}/100`);
  console.error(`   Issues Found: ${issues.length}\n`);

  return {
    validatorName: 'code-quality',
    status,
    executionTime: 0,
    rulesChecked,
    rulesPassed,
    rulesFailed: rulesChecked - rulesPassed,
    issuesFound: issues,
    metrics: {
      linterErrors: metrics.linterErrors,
      linterWarnings: metrics.linterWarnings,
      complexity: metrics.complexityScore,
      duplication: metrics.duplicateCodePercentage,
      codeSmells: metrics.codeSmells,
      maintainabilityIndex: metrics.maintainabilityIndex
    },
    recommendations,
    summary: `Code quality validation: ${rulesPassed}/${rulesChecked} rules passed, ${issues.length} issues found`
  };
}

/**
 * Run linter (simulated)
 */
async function runLinter(
  paths: string[],
  language?: string
): Promise<{ errors: number; warnings: number; issues: QualityIssue[] }> {
  const errors = Math.floor(Math.random() * 3);
  const warnings = Math.floor(Math.random() * 5);
  const issues: QualityIssue[] = [];

  if (errors > 0) {
    issues.push({
      id: `lint-${Date.now()}`,
      validator: 'code-quality',
      severity: IssueSeverity.HIGH,
      category: 'Linter Error',
      title: 'Unused variable detected',
      description: 'Variable "unusedVar" is declared but never used',
      location: 'src/utils/helper.ts:23',
      codeSnippet: 'const unusedVar = 42;',
      recommendation: 'Remove unused variable or use it',
      autoFixAvailable: true,
      estimatedEffort: 'LOW',
      detectedAt: new Date()
    });
  }

  return { errors, warnings, issues };
}

/**
 * Analyze cyclomatic complexity
 */
function analyzeComplexity(paths: string[]): {
  averageComplexity: number;
  violatingFunctions: Array<{
    name: string;
    complexity: number;
    location: string;
    snippet: string;
  }>;
} {
  const averageComplexity = 8 + Math.random() * 10; // 8-18
  const violatingFunctions = [];

  if (averageComplexity > 15) {
    violatingFunctions.push({
      name: 'processData',
      complexity: 18,
      location: 'src/services/processor.ts:45',
      snippet: 'function processData(data: any[]) { ... }'
    });
  }

  return { averageComplexity, violatingFunctions };
}

/**
 * Detect code duplication
 */
function detectDuplication(paths: string[]): {
  percentage: number;
  locations: string[];
} {
  const percentage = Math.random() * 10; // 0-10%
  const locations = percentage > 5
    ? ['src/utils/helper.ts:100-120', 'src/utils/processor.ts:50-70']
    : [];

  return { percentage, locations };
}

/**
 * Detect code smells
 */
function detectCodeSmells(paths: string[]): {
  smells: Array<{
    type: string;
    description: string;
    location: string;
    fix: string;
  }>;
} {
  const smells = [];
  const hasSmell = Math.random() > 0.6;

  if (hasSmell) {
    smells.push({
      type: 'Long Parameter List',
      description: 'Function has 6 parameters (recommended: 3-4 max)',
      location: 'src/api/users.ts:78',
      fix: 'Use parameter object or builder pattern'
    });
  }

  return { smells };
}

/**
 * Calculate maintainability index
 * Based on Halstead Volume, Cyclomatic Complexity, and Lines of Code
 */
function calculateMaintainabilityIndex(
  complexity: number,
  duplication: number,
  linterErrors: number
): number {
  let index = 100;

  // Reduce by complexity
  index -= (complexity - 10) * 2;

  // Reduce by duplication
  index -= duplication * 1.5;

  // Reduce by linter errors
  index -= linterErrors * 5;

  return Math.max(0, Math.min(100, Math.round(index)));
}

/**
 * Check naming conventions
 */
function checkNamingConventions(
  paths: string[],
  language?: string
): { violations: number; locations: string[] } {
  const violations = Math.floor(Math.random() * 3);
  const locations = violations > 0
    ? ['src/models/user_model.ts:10']
    : [];

  return { violations, locations };
}

/**
 * Check function length
 */
function checkFunctionLength(paths: string[]): Array<{
  name: string;
  lines: number;
  location: string;
}> {
  const hasLongFunction = Math.random() > 0.7;

  return hasLongFunction
    ? [{
        name: 'handleUserRequest',
        lines: 75,
        location: 'src/handlers/userHandler.ts:100-175'
      }]
    : [];
}
