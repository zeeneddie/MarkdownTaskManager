"""
BMAD Brown-Paper Session Template

For brownfield projects - assessing existing codebase and planning modernization/migration.

This template guides a structured session that:
- Reviews quality scan results
- Assesses current architecture
- Identifies technical debt
- Plans migration strategy
- Defines risks and constraints

Prerequisites: Quality scan must be completed FIRST

Output: Structured brown-paper document ready for Spec-Kit constitution phase
"""

export interface BrownPaperQuestion {
  id: string;
  category: string;
  question: string;
  prompt: string;
  expectedOutputFormat: string;
  usesScanned?: boolean;  // If true, pre-populate with scan data
  examples?: string[];
}

export interface BrownPaperSession {
  project_name: string;
  session_date: string;
  facilitator: string;
  participants: string[];
  scan_id: string;  // Reference to quality scan
  responses: Record<string, string>;
  duration_minutes?: number;
}

export interface QualityScanSummary {
  overall_score: number;
  security_score: number;
  quality_score: number;
  test_coverage: number;
  tech_debt_days: number;
  total_violations: number;
  architecture_pattern: string;
  tech_stack: string[];
  lines_of_code: number;
  top_violations: {
    type: string;
    severity: "low" | "medium" | "high" | "critical";
    count: number;
    description: string;
  }[];
}

export interface BrownPaperOutput {
  currentState: {
    architecture: string;
    techStack: string[];
    linesOfCode: number;
    teamFamiliarity: "low" | "medium" | "high";
  };
  technicalDebt: {
    totalDays: number;
    categories: {
      category: string;
      debt_days: number;
      priority: "low" | "medium" | "high";
    }[];
    topIssues: string[];
  };
  securityIssues: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    topVulnerabilities: string[];
  };
  preservationNeeds: {
    feature: string;
    reason: string;
    complexity: "low" | "medium" | "high";
  }[];
  improvementAreas: {
    area: string;
    currentState: string;
    desiredState: string;
    priority: "low" | "medium" | "high";
  }[];
  migrationStrategy: {
    approach: "big-bang" | "incremental" | "parallel" | "hybrid";
    rationale: string;
    phases: {
      phase: string;
      duration: string;
      deliverables: string[];
      risks: string[];
    }[];
  };
  risks: {
    risk: string;
    category: "technical" | "business" | "operational";
    impact: "low" | "medium" | "high";
    probability: "low" | "medium" | "high";
    mitigation?: string;
  }[];
}

export const BROWN_PAPER_QUESTIONS: BrownPaperQuestion[] = [
  {
    id: "current_architecture",
    category: "Current State Assessment",
    question: "What is the current architecture of the system?",
    prompt: `Based on the quality scan results, review the current architecture:

    Scan Results Show:
    - Architecture Pattern: {ARCHITECTURE_PATTERN}
    - Tech Stack: {TECH_STACK}
    - Lines of Code: {LINES_OF_CODE}
    - Complexity: {COMPLEXITY_SCORE}

    Please confirm or correct this assessment:
    - Is the detected architecture accurate?
    - Are there missing components or layers?
    - What are the key integration points?
    - How familiar is the team with this stack?`,
    expectedOutputFormat: `Architecture Pattern: [Confirm or correct]

Key Components:
- [Component name]: [Purpose]
- [Component name]: [Purpose]
...

Integration Points:
- [External system/API]: [Integration type]
...

Team Familiarity: [low/medium/high]
- [Skill area]: [Level of expertise]`,
    usesScanned: true,
    examples: [
      "Architecture Pattern: Monolithic ASP.NET Web Forms (confirmed)",
      "Key Component: Patient Portal - Web-based patient access",
      "Integration: Epic EHR - SOAP API for patient data"
    ]
  },

  {
    id: "technical_debt",
    category: "Technical Debt",
    question: "What is the technical debt we need to address?",
    prompt: `Review the technical debt identified in the scan:

    Scan Results:
    - Total Technical Debt: {TECH_DEBT_DAYS} days
    - Code Quality Score: {QUALITY_SCORE}%
    - Top Issues: {TOP_VIOLATIONS}

    Please categorize and prioritize the technical debt:

    For each category (Code Quality, Architecture, Testing, Security, Documentation):
    - How many days of debt?
    - What are the specific issues?
    - What is the priority? (low/medium/high)
    - Which issues MUST be fixed for migration success?`,
    expectedOutputFormat: `Technical Debt by Category:

1. Code Quality ({X} days) - Priority: [low/medium/high]
   - [Specific issue]
   - [Specific issue]

2. Architecture ({X} days) - Priority: [low/medium/high]
   - [Specific issue]

... (continue for each category)

Critical Issues (MUST fix):
- [Issue that blocks migration]
- [Issue that blocks migration]`,
    usesScannedData: true,
    examples: [
      "Code Quality (45 days) - Priority: high",
      "- 234 code smells requiring refactoring",
      "- Cyclomatic complexity >20 in 67 methods",
      "Critical: SQL injection vulnerabilities must be fixed before migration"
    ]
  },

  {
    id: "security_vulnerabilities",
    category: "Security Assessment",
    question: "What security vulnerabilities were found?",
    prompt: `Review the security scan results (OWASP Top 10):

    Security Score: {SECURITY_SCORE}%
    Vulnerabilities:
    - Critical: {CRITICAL_COUNT}
    - High: {HIGH_COUNT}
    - Medium: {MEDIUM_COUNT}
    - Low: {LOW_COUNT}

    Top Vulnerabilities:
    {TOP_VULNERABILITIES}

    Questions:
    - Which vulnerabilities pose immediate risk?
    - Which can be addressed during migration?
    - Are there regulatory compliance issues (GDPR, HIPAA, etc.)?
    - What is the remediation plan?`,
    expectedOutputFormat: `Immediate Risk (Fix Now):
- [Vulnerability]: [Why urgent]

Fix During Migration:
- [Vulnerability]: [Migration opportunity]

Regulatory Concerns:
- [Compliance requirement]: [Current gap]

Remediation Plan:
1. [Phase 1 fixes]
2. [Phase 2 fixes]
...`,
    usesScannedData: true,
    examples: [
      "Immediate Risk: SQL Injection in patient search (HIPAA violation)",
      "Fix During Migration: Outdated encryption libraries (upgrade with new stack)",
      "Regulatory: GDPR requires audit logging (currently missing)"
    ]
  },

  {
    id: "preservation_needs",
    category: "What Must Be Preserved",
    question: "What features/capabilities must be preserved during migration?",
    prompt: `Identify the core features that MUST work identically after migration:

    Consider:
    - Critical business processes
    - User workflows that cannot change
    - Integration contracts (APIs, data formats)
    - Compliance requirements
    - Data integrity requirements

    For each preservation need:
    - What exactly must be preserved?
    - Why is it critical?
    - What is the complexity of preserving it?`,
    expectedOutputFormat: `1. Feature: [Name]
   Why Critical: [Business/regulatory reason]
   Complexity: [low/medium/high]
   Notes: [Any special considerations]

2. Feature: [Name]
   ...`,
    examples: [
      "Feature: Patient appointment scheduling workflow",
      "Why Critical: Used by 10,000 patients/month, exact sequence required by regulation",
      "Complexity: medium",
      "Notes: API contract with Epic EHR cannot change"
    ]
  },

  {
    id: "improvement_areas",
    category: "Improvement Opportunities",
    question: "What should be improved during the migration?",
    prompt: `Based on the quality scan and team experience, identify improvement opportunities:

    For each area:
    - What is the current state? (from scan if available)
    - What should it be?
    - Why is this improvement important?
    - What is the priority?

    Common areas:
    - Performance bottlenecks
    - User experience pain points
    - Operational challenges
    - Scalability limitations
    - Maintainability issues`,
    expectedOutputFormat: `1. Area: [Name]
   Current: [Current state, ideally with metrics]
   Desired: [Target state with metrics]
   Why: [Business/technical justification]
   Priority: [low/medium/high]

2. Area: [Name]
   ...`,
    examples: [
      "Area: Page Load Performance",
      "Current: Average 8 seconds (scan showed 45 unoptimized queries)",
      "Desired: <2 seconds with query optimization and caching",
      "Why: 30% user abandonment rate due to slow pages",
      "Priority: high"
    ]
  },

  {
    id: "migration_strategy",
    category: "Migration Approach",
    question: "What is the migration strategy?",
    prompt: `Choose and justify a migration approach:

    **Big-Bang**:
    - Pros: Clean cutover, no dual maintenance
    - Cons: High risk, long blackout period
    - Best for: Small systems, simple migrations

    **Incremental (Strangler Fig)**:
    - Pros: Lower risk, gradual migration, can roll back
    - Cons: Dual maintenance, integration complexity
    - Best for: Large systems, critical services

    **Parallel Run**:
    - Pros: Safe, can validate before cutover
    - Cons: Expensive, data sync complexity
    - Best for: Mission-critical systems

    **Hybrid**:
    - Pros: Tailored to specific needs
    - Cons: Complex planning
    - Best for: Complex systems with varying risk levels

    Define:
    - Which approach and why?
    - What are the migration phases?
    - What are the deliverables per phase?
    - What are the risks per phase?`,
    expectedOutputFormat: `Approach: [big-bang/incremental/parallel/hybrid]

Rationale:
[Why this approach is best for this project]

Phases:

Phase 1: [Name] (Duration: [X] weeks)
Deliverables:
- [Deliverable]
- [Deliverable]
Risks:
- [Risk]

Phase 2: [Name]
...`,
    examples: [
      "Approach: Incremental (Strangler Fig)",
      "Rationale: System too critical for big-bang, allows validation at each step",
      "Phase 1: Authentication & Authorization (4 weeks)",
      "Deliverables: New auth service, OAuth implementation, user migration",
      "Risks: Session compatibility during transition"
    ]
  },

  {
    id: "migration_risks",
    category: "Migration Risks",
    question: "What are the risks specific to this migration?",
    prompt: `Identify risks across categories:

    Technical Risks:
    - Data migration complexity
    - Integration breakage
    - Performance degradation
    - Unknown technical debt

    Business Risks:
    - User adoption resistance
    - Business continuity during migration
    - Feature parity gaps
    - Timeline slippage

    Operational Risks:
    - Team skill gaps
    - Resource constraints
    - Vendor dependencies
    - Production incidents

    For each risk:
    - Describe specific to this migration
    - Rate impact and probability
    - Suggest mitigation`,
    expectedOutputFormat: `1. Risk: [Specific risk description]
   Category: [technical/business/operational]
   Impact: [low/medium/high]
   Probability: [low/medium/high]
   Mitigation: [Specific mitigation strategy]

2. Risk: [Description]
   ...`,
    examples: [
      "Risk: Patient data migration corruption",
      "Category: technical",
      "Impact: critical",
      "Probability: medium",
      "Mitigation: Incremental migration with validation, full rollback capability, parallel run for 2 weeks"
    ]
  }
];

export function generateBrownPaperMarkdown(
  session: BrownPaperSession,
  scanSummary: QualityScanSummary,
  output: BrownPaperOutput
): string {
  const timestamp = new Date(session.session_date).toISOString().split('T')[0];

  return `# BMAD Brown-Paper Session
## ${session.project_name}

**Date**: ${timestamp}
**Facilitator**: ${session.facilitator}
**Participants**: ${session.participants.join(', ')}
**Duration**: ${session.duration_minutes || 'N/A'} minutes
**Quality Scan ID**: ${session.scan_id}

---

## Quality Scan Summary

**Overall Score**: ${scanSummary.overall_score}%
**Security Score**: ${scanSummary.security_score}%
**Code Quality Score**: ${scanSummary.quality_score}%
**Test Coverage**: ${scanSummary.test_coverage}%
**Technical Debt**: ~${scanSummary.tech_debt_days} days
**Total Violations**: ${scanSummary.total_violations}

**Top Violations**:
${scanSummary.top_violations.map(v => `- [${v.severity.toUpperCase()}] ${v.type}: ${v.description} (${v.count} occurrences)`).join('\n')}

---

## 1. Current State Assessment

### Architecture
**Pattern**: ${output.currentState.architecture}

**Tech Stack**:
${output.currentState.techStack.map(t => `- ${t}`).join('\n')}

**Size**: ${output.currentState.linesOfCode.toLocaleString()} lines of code

**Team Familiarity**: ${output.currentState.teamFamiliarity}

---

## 2. Technical Debt Analysis

**Total Technical Debt**: ~${output.technicalDebt.totalDays} days

### Breakdown by Category
${output.technicalDebt.categories.map(c =>
  `#### ${c.category} (${c.debt_days} days) - Priority: ${c.priority}`
).join('\n\n')}

### Top Issues to Address
${output.technicalDebt.topIssues.map((issue, i) => `${i + 1}. ${issue}`).join('\n')}

---

## 3. Security Vulnerabilities

**Critical**: ${output.securityIssues.critical}
**High**: ${output.securityIssues.high}
**Medium**: ${output.securityIssues.medium}
**Low**: ${output.securityIssues.low}

### Top Vulnerabilities
${output.securityIssues.topVulnerabilities.map((vuln, i) => `${i + 1}. ${vuln}`).join('\n')}

---

## 4. Preservation Requirements

${output.preservationNeeds.map((need, i) => `### ${i + 1}. ${need.feature}
**Why Critical**: ${need.reason}
**Complexity**: ${need.complexity}\n`).join('\n')}

---

## 5. Improvement Opportunities

${output.improvementAreas.map((area, i) => `### ${i + 1}. ${area.area}
**Current**: ${area.currentState}
**Desired**: ${area.desiredState}
**Priority**: ${area.priority}\n`).join('\n')}

---

## 6. Migration Strategy

### Approach: ${output.migrationStrategy.approach}

**Rationale**:
${output.migrationStrategy.rationale}

### Migration Phases

${output.migrationStrategy.phases.map((phase, i) => `#### Phase ${i + 1}: ${phase.phase}
**Duration**: ${phase.duration}

**Deliverables**:
${phase.deliverables.map(d => `- ${d}`).join('\n')}

**Risks**:
${phase.risks.map(r => `- ${r}`).join('\n')}\n`).join('\n')}

---

## 7. Migration Risks

${output.risks.map((r, i) => `### ${i + 1}. ${r.risk}
- **Category**: ${r.category}
- **Impact**: ${r.impact}
- **Probability**: ${r.probability}
${r.mitigation ? `- **Mitigation**: ${r.mitigation}` : ''}\n`).join('\n')}

---

## Next Steps

This brown-paper document, combined with the quality scan results, will be used as input for the Spec-Kit workflow:

1. **Constitution Phase**: Transform current state, debt, and migration plan into formal constitution
2. **Specification Phase**: Design target architecture addressing identified issues
3. **Task Generation Phase**: Break down migration into epics, features, and stories

**Mapping**:
- Current State → Technical Context
- Technical Debt → Constraints
- Security Issues → Risks & Requirements
- Preservation Needs → Functional Requirements
- Improvement Areas → Quality Requirements
- Migration Strategy → Constraints & Approach
- Risks → Risks

---

*Generated by BMAD Brown-Paper Session - ${timestamp}*
*Based on Quality Scan: ${session.scan_id}*
`;
}

export default {
  BROWN_PAPER_QUESTIONS,
  generateBrownPaperMarkdown
};
