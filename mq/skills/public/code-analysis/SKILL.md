# Code Analysis Skill

**Comprehensive codebase analysis for quality, architecture, and technical debt assessment**

---

## Overview

This skill enables systematic code analysis across multiple technology stacks, identifying quality issues, architectural patterns, technical debt, and providing actionable insights for improvement.

### What This Skill Does

- ✅ Multi-stack code analysis (ASP Classic, .NET, Java, Python, Node.js)
- ✅ Automated tool orchestration and result parsing
- ✅ Architecture pattern detection and evaluation
- ✅ Technical debt identification and quantification
- ✅ Code quality metrics calculation
- ✅ Complexity analysis and reporting
- ✅ Best practice verification

### When to Use This Skill

Use this skill when you need to:
- Understand a legacy codebase structure
- Assess code quality and maintainability
- Identify technical debt and prioritize fixes
- Plan modernization or refactoring efforts
- Generate comprehensive analysis reports
- Evaluate migration complexity

---

## Core Capabilities

### 1. Technology Stack Detection

**Automatic Detection Logic**:
```python
def detect_stack(codebase_path):
    """Automatically detect technology stack from codebase"""
    
    indicators = {
        'dotnet': ['*.csproj', '*.sln', 'packages.config'],
        'asp_classic': ['*.asp', '*.vbs', 'global.asa'],
        'java': ['pom.xml', 'build.gradle', '*.java'],
        'python': ['requirements.txt', 'setup.py', '*.py'],
        'nodejs': ['package.json', 'node_modules/'],
        'php': ['composer.json', '*.php']
    }
    
    detected_stacks = []
    
    for stack, patterns in indicators.items():
        if any(find_files(codebase_path, pattern) for pattern in patterns):
            detected_stacks.append(stack)
    
    return detected_stacks
```

### 2. Static Code Analysis

**Tool Selection by Stack**:

**.NET/C#**:
```bash
# Roslyn analyzers
dotnet format --verify-no-changes --severity info

# Build with all analyzers enabled
dotnet build /p:RunAnalyzers=true /p:TreatWarningsAsErrors=false

# SonarScanner (if available)
sonar-scanner -Dsonar.projectKey=myproject
```

**Java**:
```bash
# SpotBugs
spotbugs -textui -effort:max ./target/classes

# PMD
pmd -d ./src -R rulesets/java/quickstart.xml

# Checkstyle
checkstyle -c /google_checks.xml src/
```

**Python**:
```bash
# Pylint
pylint --output-format=json src/

# Flake8
flake8 --format=html --htmldir=report src/

# Mypy (type checking)
mypy --html-report report src/
```

**ASP Classic** (Custom Patterns):
```bash
# SQL injection patterns
grep -rn "Execute.*&\|.*&" *.asp

# XSS vulnerabilities
grep -rn "Response.Write.*Request\." *.asp

# Hardcoded credentials
grep -rni "password.*=.*['\"]" *.asp *.vbs
```

### 3. Architecture Analysis

**Pattern Detection**:
```python
def detect_architecture_pattern(codebase):
    """Detect architectural patterns in use"""
    
    patterns = []
    
    # Check for MVC
    if has_directories(['Models', 'Views', 'Controllers']):
        patterns.append({
            'name': 'MVC',
            'confidence': 'high',
            'evidence': ['Model/View/Controller directories']
        })
    
    # Check for Layered Architecture
    if has_directories(['Presentation', 'Business', 'Data']) or \
       has_directories(['UI', 'Domain', 'Infrastructure']):
        patterns.append({
            'name': 'Layered',
            'confidence': 'high',
            'evidence': ['Clear layer separation']
        })
    
    # Check for Microservices
    if count_services() > 1:
        patterns.append({
            'name': 'Microservices',
            'confidence': 'medium',
            'evidence': [f'{count_services()} separate services']
        })
    
    # Check for Monolith
    if not patterns and has_single_deployment():
        patterns.append({
            'name': 'Monolith',
            'confidence': 'high',
            'evidence': ['Single deployment unit']
        })
    
    return patterns
```

**Dependency Mapping**:
```bash
# Generate dependency graph
# .NET
dotnet list package --include-transitive

# Java
mvn dependency:tree

# Python
pipdeptree --graph-output png > dependencies.png

# Analyze circular dependencies
find_circular_dependencies() {
    # Use language-specific tools or custom analysis
}
```

### 4. Technical Debt Calculation

**Debt Scoring Algorithm**:
```python
def calculate_technical_debt(codebase_analysis):
    """Calculate technical debt in hours"""
    
    debt_factors = {
        'code_smells': {
            'long_methods': 0.5,      # 30 min per method
            'large_classes': 2.0,     # 2 hours per class
            'duplicate_code': 1.0,    # 1 hour per duplication
            'complex_methods': 1.5,   # 1.5 hours per complex method
            'magic_numbers': 0.25     # 15 min per magic number
        },
        'outdated_dependencies': {
            'critical': 4.0,          # 4 hours per critical
            'high': 2.0,              # 2 hours per high
            'medium': 1.0,            # 1 hour per medium
            'low': 0.5                # 30 min per low
        },
        'missing_tests': {
            'per_untested_function': 1.0  # 1 hour per function
        },
        'documentation': {
            'per_undocumented_public': 0.5  # 30 min per public member
        }
    }
    
    total_debt = 0
    
    # Calculate from code smells
    for smell_type, hours_per in debt_factors['code_smells'].items():
        count = codebase_analysis['code_smells'][smell_type]
        total_debt += count * hours_per
    
    # Calculate from outdated dependencies
    for severity, hours_per in debt_factors['outdated_dependencies'].items():
        count = codebase_analysis['dependencies'][severity]
        total_debt += count * hours_per
    
    # Calculate from missing tests
    untested = codebase_analysis['test_coverage']['untested_functions']
    total_debt += untested * debt_factors['missing_tests']['per_untested_function']
    
    # Calculate from missing documentation
    undocumented = codebase_analysis['documentation']['undocumented_public']
    total_debt += undocumented * debt_factors['documentation']['per_undocumented_public']
    
    return {
        'total_hours': total_debt,
        'total_weeks': total_debt / 40,
        'breakdown': calculate_breakdown(debt_factors, codebase_analysis)
    }
```

### 5. Complexity Metrics

**Cyclomatic Complexity**:
```python
def calculate_complexity_metrics(codebase):
    """Calculate various complexity metrics"""
    
    metrics = {
        'cyclomatic_complexity': {
            'average': 0,
            'max': 0,
            'functions_over_10': [],
            'functions_over_20': []
        },
        'cognitive_complexity': {
            'average': 0,
            'max': 0
        },
        'nesting_depth': {
            'average': 0,
            'max': 0,
            'deep_nesting': []  # Functions with depth > 4
        },
        'maintainability_index': 0
    }
    
    # Use tool-specific calculations
    # For Python: radon
    # For Java: JavaNCSS
    # For .NET: Visual Studio metrics
    
    return metrics
```

### 6. Code Quality Scoring

**Quality Score Formula**:
```python
def calculate_quality_score(analysis_results):
    """
    Quality Score = weighted average of:
    - Maintainability (30%)
    - Test Coverage (25%)
    - Complexity (20%)
    - Documentation (15%)
    - Code Smells (10%)
    
    Scale: 0-100 (higher is better)
    """
    
    weights = {
        'maintainability': 0.30,
        'test_coverage': 0.25,
        'complexity': 0.20,
        'documentation': 0.15,
        'code_smells': 0.10
    }
    
    scores = {
        'maintainability': calculate_maintainability_score(analysis_results),
        'test_coverage': analysis_results['test_coverage']['percentage'],
        'complexity': calculate_complexity_score(analysis_results),
        'documentation': calculate_documentation_score(analysis_results),
        'code_smells': 100 - calculate_smell_penalty(analysis_results)
    }
    
    quality_score = sum(
        scores[metric] * weight 
        for metric, weight in weights.items()
    )
    
    return {
        'overall_score': quality_score,
        'grade': get_grade(quality_score),  # A, B, C, D, F
        'breakdown': scores
    }

def get_grade(score):
    if score >= 90: return 'A'
    if score >= 80: return 'B'
    if score >= 70: return 'C'
    if score >= 60: return 'D'
    return 'F'
```

---

## Usage Examples

### Example 1: Basic Code Analysis
```python
from code_analysis import analyze_codebase

# Analyze a Python project
results = analyze_codebase(
    path='./my-project',
    stack='python',
    depth='standard'
)

print(f"Quality Score: {results['quality_score']}/100")
print(f"Technical Debt: {results['technical_debt']['total_hours']} hours")
print(f"Test Coverage: {results['test_coverage']['percentage']}%")
```

### Example 2: Migration Assessment
```python
from code_analysis import assess_migration_complexity

# Assess migration from ASP Classic to .NET
assessment = assess_migration_complexity(
    source='./legacy-asp',
    target_stack='dotnet-core'
)

print(f"Migration Complexity: {assessment['complexity_score']}")
print(f"Estimated Effort: {assessment['estimated_hours']} hours")
print(f"Risk Level: {assessment['risk_level']}")
```

### Example 3: Technical Debt Report
```python
from code_analysis import generate_debt_report

# Generate prioritized technical debt report
report = generate_debt_report(
    codebase='./src',
    format='markdown'
)

# Outputs TECHNICAL-DEBT-REPORT.md with:
# - Total debt in hours
# - Breakdown by category
# - Prioritized action items
# - Effort estimates
```

---

## Best Practices

### 1. Run Analysis Regularly
```bash
# Weekly analysis for active projects
0 2 * * 1 /usr/local/bin/analyze-codebase --id weekly-$(date +%Y%m%d)

# Pre-release analysis
analyze-codebase --id pre-release --depth deep --export-all
```

### 2. Focus on Actionable Metrics

Don't just collect metrics - use them:
- Set quality gates (e.g., no new code with complexity > 10)
- Track trends over time
- Prioritize debt by impact/effort ratio
- Celebrate improvements

### 3. Combine with Manual Review

Automated analysis finds patterns, but humans understand context:
- Review high-complexity code manually
- Validate architectural decisions
- Assess business logic clarity
- Check domain model appropriateness

### 4. Document Decisions
```markdown
# ADR-001: Accepting Technical Debt in Legacy Module

**Status**: Accepted
**Date**: 2026-01-23

## Context
The UserService module has high complexity (cyclomatic: 45)
and significant technical debt (estimated 40 hours).

## Decision
We accept this debt for now because:
- Module is scheduled for replacement in Q2
- Refactoring would take 40h with no business value
- No active bugs or performance issues
- Replacement will eliminate debt entirely

## Consequences
- Document this decision
- Monitor for bugs (none expected)
- Proceed with replacement as planned
```

---

## Integration Points

### With MarQed.ai Workflows
```yaml
workflow_integration:
  analyze_workflow:
    - phase: "Phase 2 - Automated Analysis"
      uses: code-analysis skill
      outputs:
        - quality_metrics
        - complexity_analysis
        - technical_debt_report
  
  migration_workflow:
    - phase: "Phase 1 - Analysis"
      uses: code-analysis skill
      outputs:
        - migration_complexity
        - effort_estimate
        - risk_assessment
```

### With Other Skills

**With security-scan skill**:
```python
# Combine code quality and security analysis
results = {
    'quality': code_analysis.analyze(codebase),
    'security': security_scan.scan(codebase)
}

# Integrated risk score
risk_score = calculate_integrated_risk(
    quality_score=results['quality']['score'],
    security_vulnerabilities=results['security']['critical_count']
)
```

---

## Advanced Features

### Incremental Analysis
```python
def incremental_analysis(codebase, since_commit):
    """Only analyze files changed since last analysis"""
    
    # Get changed files
    changed_files = git_diff(since_commit)
    
    # Analyze only changed files
    results = analyze_files(changed_files)
    
    # Merge with cached results for unchanged files
    full_results = merge_with_cache(results, since_commit)
    
    return full_results
```

### Custom Rules
```yaml
# custom-rules.yml
code_analysis:
  custom_rules:
    - id: no_god_objects
      description: "Classes should not exceed 500 lines"
      severity: high
      threshold: 500
      
    - id: max_method_length
      description: "Methods should not exceed 50 lines"
      severity: medium
      threshold: 50
      
    - id: min_test_coverage
      description: "Code coverage must be at least 80%"
      severity: high
      threshold: 80
```

### Trend Analysis
```python
def analyze_trends(project_id, time_range='3m'):
    """Analyze quality trends over time"""
    
    analyses = load_historical_analyses(project_id, time_range)
    
    trends = {
        'quality_score': calculate_trend([a['score'] for a in analyses]),
        'technical_debt': calculate_trend([a['debt'] for a in analyses]),
        'test_coverage': calculate_trend([a['coverage'] for a in analyses]),
        'complexity': calculate_trend([a['complexity'] for a in analyses])
    }
    
    # Identify improving/declining metrics
    for metric, trend in trends.items():
        if trend['direction'] == 'declining':
            alert(f"⚠️  {metric} is declining: {trend['change_percent']}%")
    
    return trends
```

---

## Output Formats

### JSON Export
```json
{
  "analysis_id": "ANALYZE-2026-01-23-001",
  "timestamp": "2026-01-23T10:00:00Z",
  "codebase": {
    "path": "./src",
    "stack": "python",
    "loc": 45000,
    "files": 230
  },
  "quality": {
    "score": 72,
    "grade": "C",
    "maintainability": 68,
    "test_coverage": 75,
    "complexity": 70,
    "documentation": 65
  },
  "technical_debt": {
    "total_hours": 240,
    "total_weeks": 6,
    "by_category": {
      "code_smells": 120,
      "missing_tests": 80,
      "outdated_deps": 40
    }
  },
  "findings": [...],
  "recommendations": [...]
}
```

### Markdown Report
```markdown
# Code Analysis Report

## Executive Summary
- **Quality Score**: 72/100 (C)
- **Technical Debt**: 240 hours (6 weeks)
- **Test Coverage**: 75%
- **Critical Issues**: 3

## Quality Breakdown
- Maintainability: 68/100
- Test Coverage: 75/100
- Complexity: 70/100
- Documentation: 65/100

## Top Recommendations
1. Refactor UserService (complexity: 45) - 8h
2. Add tests for PaymentService - 12h
3. Update 5 critical dependencies - 6h

[... detailed findings ...]
```

---

## Troubleshooting

### Tool Not Found
```bash
# Install missing tools
pip install pylint flake8 bandit radon
npm install -g jshint eslint
dotnet tool install -g dotnet-format
```

### Analysis Timeout
```python
# For large codebases, use incremental mode
analyze_codebase(
    path='./large-project',
    mode='incremental',
    cache=True,
    parallel=True
)
```

### Inaccurate Results
```python
# Calibrate thresholds for your context
configure_analysis(
    complexity_threshold=15,  # Default: 10
    min_test_coverage=70,     # Default: 80
    custom_rules='./rules.yml'
)
```

---

## Version History

- **2.0** (2026-01-23): Added healthcare compliance, multi-stack support
- **1.5** (2025-10-01): Added technical debt calculation
- **1.0** (2025-06-01): Initial release

---

**Skill Version**: 2.0  
**Last Updated**: January 23, 2026  
**Maintained By**: MarQed.ai B.V.