"""
BMAD Green-Paper Session Template

For greenfield projects - defining vision, scope, and initial architecture.

This template guides a structured session to gather:
- Business vision and goals
- Key stakeholders
- Guiding principles
- Project scope (in/out)
- Constraints (budget, timeline, technology)
- Known risks

Output: Structured green-paper document ready for Spec-Kit constitution phase
"""

export interface GreenPaperQuestion {
  id: string;
  category: string;
  question: string;
  prompt: string;
  expectedOutputFormat: string;
  examples?: string[];
}

export interface GreenPaperSession {
  project_name: string;
  session_date: string;
  facilitator: string;
  participants: string[];
  responses: Record<string, string>;
  duration_minutes?: number;
}

export interface GreenPaperOutput {
  vision: {
    businessGoals: string[];
    problemStatement: string;
    successCriteria: string[];
  };
  stakeholders: {
    internal: string[];
    external: string[];
    decisionMakers: string[];
  };
  principles: {
    principle: string;
    rationale: string;
  }[];
  scope: {
    included: string[];
    excluded: string[];
    assumptions: string[];
  };
  constraints: {
    budget?: string;
    timeline?: string;
    technology?: string[];
    resources?: string;
    regulatory?: string[];
  };
  risks: {
    risk: string;
    category: "technical" | "business" | "operational";
    impact: "low" | "medium" | "high";
    probability: "low" | "medium" | "high";
    mitigation?: string;
  }[];
  /** Development stack preferences */
  developmentStack?: {
    languages?: string[];
    frameworks?: string[];
    databases?: string[];
    testing?: string[];
    versionControl?: string;
    existingCodebase?: string;
  };
  /** Operational stack preferences */
  operationalStack?: {
    hosting?: string;
    containerization?: string;
    cicd?: string;
    monitoring?: string[];
    security?: string[];
    existingInfra?: string;
  };
}

export const GREEN_PAPER_QUESTIONS: GreenPaperQuestion[] = [
  {
    id: "vision",
    category: "Business Vision",
    question: "What is the business vision for this project?",
    prompt: `Describe the business vision and goals for this project:

    Consider:
    - What problem are you solving?
    - What business goals do you want to achieve?
    - What does success look like?
    - How will this create value?

    Please provide a clear, concise vision statement and 3-5 key business goals.`,
    expectedOutputFormat: `Vision statement: [One sentence describing the vision]

Business Goals:
1. [Specific, measurable goal]
2. [Specific, measurable goal]
3. ...

Success Criteria:
1. [How we measure success]
2. [How we measure success]
3. ...`,
    examples: [
      "Vision: Enable patients to manage their healthcare journey digitally with a modern, secure portal.",
      "Goal: Reduce patient support calls by 40% through self-service features."
    ]
  },

  {
    id: "stakeholders",
    category: "Stakeholders",
    question: "Who are the key stakeholders for this project?",
    prompt: `Identify all key stakeholders:

    Internal:
    - Who inside the organization cares about this project?
    - Who will use the system?
    - Who will maintain it?

    External:
    - Who outside the organization will be affected?
    - Customers, partners, regulators?

    Decision Makers:
    - Who has authority to make key decisions?
    - Who approves scope, budget, architecture?`,
    expectedOutputFormat: `Internal Stakeholders:
- [Role]: [Name/Team] - [Interest/Concern]

External Stakeholders:
- [Role]: [Name/Organization] - [Interest/Concern]

Decision Makers:
- [Role]: [Name] - [Authority Level]`,
    examples: [
      "Internal: IT Team - Will maintain the system, concerned about technical debt",
      "External: Patients - End users, concerned about ease of use and privacy",
      "Decision Maker: CIO - Final approval on architecture and budget"
    ]
  },

  {
    id: "principles",
    category: "Guiding Principles",
    question: "What are the guiding principles for this project?",
    prompt: `Define 3-7 guiding principles that will drive decisions throughout the project.

    Principles should be:
    - Clear and actionable
    - Specific to this project
    - Help make trade-off decisions

    Common categories:
    - Quality (maintainability, reliability, performance)
    - Security & Privacy
    - User Experience
    - Development Process
    - Technology Choices`,
    expectedOutputFormat: `1. Principle: [Short principle name]
   Rationale: [Why this matters for this project]

2. Principle: [Short principle name]
   Rationale: [Why this matters for this project]

...`,
    examples: [
      "Principle: Security by Default\nRationale: Healthcare data requires HIPAA compliance, security cannot be added later",
      "Principle: Mobile-First Design\nRationale: 70% of patients access healthcare info via mobile devices"
    ]
  },

  {
    id: "scope",
    category: "Scope Definition",
    question: "What is in scope and what is out of scope?",
    prompt: `Clearly define the project boundaries:

    In Scope:
    - What features/capabilities WILL be included?
    - What problems WILL we solve?

    Out of Scope:
    - What features/capabilities will NOT be included?
    - What problems will NOT be solved (now or ever)?

    Assumptions:
    - What are we assuming to be true?
    - What external dependencies exist?`,
    expectedOutputFormat: `In Scope:
- [Feature/capability]
- [Feature/capability]
...

Out of Scope:
- [Feature/capability] - [Reason]
- [Feature/capability] - [Reason]
...

Assumptions:
- [Assumption about users, technology, or environment]
- [Assumption about users, technology, or environment]
...`,
    examples: [
      "In Scope: Patient appointment scheduling via web and mobile",
      "Out of Scope: Insurance claim processing (separate system exists)",
      "Assumption: Patients have access to email for notifications"
    ]
  },

  {
    id: "constraints",
    category: "Constraints",
    question: "What are the project constraints?",
    prompt: `Identify all constraints that will limit the project:

    Budget:
    - What is the total budget?
    - Any specific budget limits per category?

    Timeline:
    - When must this be delivered?
    - Are there interim milestones?

    Technology:
    - Must use certain technologies?
    - Cannot use certain technologies?

    Resources:
    - Team size limits?
    - Skill gaps?

    Regulatory:
    - Compliance requirements?
    - Legal constraints?`,
    expectedOutputFormat: `Budget:
- Total: [Amount]
- [Category]: [Amount/Constraint]

Timeline:
- Launch Date: [Date]
- Milestones: [Key dates]

Technology:
- Must Use: [Technology stack requirements]
- Cannot Use: [Prohibited technologies]

Resources:
- Team Size: [Number] developers, [Number] QA, etc.
- Skills: [Available skills] / [Skill gaps]

Regulatory:
- [Compliance requirement]
- [Compliance requirement]`,
    examples: [
      "Budget: Total €150,000 (includes development, testing, deployment)",
      "Timeline: Launch by Q2 2026, MVP by end Q1 2026",
      "Technology: Must integrate with existing .NET backend APIs",
      "Regulatory: HIPAA compliance required for patient data"
    ]
  },

  {
    id: "risks",
    category: "Known Risks",
    question: "What are the known risks for this project?",
    prompt: `Identify risks across categories:

    Technical Risks:
    - Technology unknowns
    - Integration challenges
    - Performance concerns

    Business Risks:
    - Market changes
    - Competitive threats
    - Adoption concerns

    Operational Risks:
    - Resource availability
    - Dependencies on other projects
    - Organizational changes

    For each risk:
    - Describe the risk
    - Rate impact (low/medium/high)
    - Rate probability (low/medium/high)
    - Suggest mitigation if possible`,
    expectedOutputFormat: `1. Risk: [Description of risk]
   Category: [technical/business/operational]
   Impact: [low/medium/high]
   Probability: [low/medium/high]
   Mitigation: [How we could reduce risk]

2. Risk: [Description]
   ...`,
    examples: [
      "Risk: HIPAA audit could delay launch\nCategory: operational\nImpact: high\nProbability: medium\nMitigation: Start compliance review early, parallel to development",
      "Risk: Users may not adopt new mobile app\nCategory: business\nImpact: high\nProbability: medium\nMitigation: User testing, gradual rollout, training materials"
    ]
  },

  {
    id: "development_stack",
    category: "Development Stack",
    question: "What technologies will be used for development?",
    prompt: `Define the development technology stack:

    Languages:
    - What programming languages will be used?
    - Backend vs frontend languages?

    Frameworks:
    - What frameworks for frontend/backend/testing?
    - Any required frameworks from existing systems?

    Databases:
    - Primary database (SQL/NoSQL)?
    - Caching layer?
    - Search engine?

    Testing:
    - Unit testing frameworks?
    - Integration testing?
    - E2E testing?

    Development Tools:
    - Version control (Git, SVN)?
    - Platform (GitHub, GitLab)?
    - Linting/formatting tools?

    Existing Codebase:
    - Is there existing code to integrate with?
    - What languages/frameworks does it use?`,
    expectedOutputFormat: `Languages:
- Backend: [e.g., Python, Node.js, Java]
- Frontend: [e.g., TypeScript, JavaScript]

Frameworks:
- Backend: [e.g., FastAPI, Express, Spring]
- Frontend: [e.g., React, Vue, Angular]
- Testing: [e.g., pytest, Jest]

Databases:
- Primary: [e.g., PostgreSQL, MongoDB]
- Cache: [e.g., Redis, Memcached]
- Search: [e.g., Elasticsearch, if needed]

Testing:
- Unit: [e.g., pytest, Jest]
- Integration: [e.g., pytest-httpx, Supertest]
- E2E: [e.g., Playwright, Cypress]

Version Control:
- System: [Git]
- Platform: [GitHub, GitLab, Bitbucket]
- Branch Strategy: [gitflow, trunk-based]

Existing Codebase:
- [Description of existing code, if any]`,
    examples: [
      "Languages: Python (backend), TypeScript (frontend)",
      "Frameworks: FastAPI, React with Vite",
      "Database: PostgreSQL with Redis caching",
      "Testing: pytest + Jest + Playwright",
      "Version Control: Git on GitHub, trunk-based development"
    ]
  },

  {
    id: "operational_stack",
    category: "Operational Stack",
    question: "What infrastructure and deployment technologies will be used?",
    prompt: `Define the operational/deployment stack:

    Hosting:
    - Cloud provider (AWS, GCP, Azure)?
    - Or on-premise / hybrid?
    - Which regions?

    Containerization:
    - Docker, Podman, or none?
    - Container registry?

    Orchestration:
    - Kubernetes, ECS, or simpler?
    - Managed service or self-managed?

    CI/CD:
    - Pipeline tool (GitHub Actions, GitLab CI)?
    - Deployment stages (dev, staging, prod)?
    - Deployment strategy (blue-green, rolling)?

    Monitoring:
    - Metrics (Prometheus, Datadog)?
    - Logging (ELK, CloudWatch)?
    - Alerting (PagerDuty, OpsGenie)?

    Security:
    - Secrets management (Vault, AWS Secrets)?
    - WAF/DDoS protection?
    - Security scanning tools?

    Existing Infrastructure:
    - What infrastructure already exists?
    - What must we integrate with?`,
    expectedOutputFormat: `Hosting:
- Provider: [AWS, GCP, Azure, on-prem]
- Type: [cloud, on-premise, hybrid]
- Regions: [e.g., eu-west-1, us-east-1]

Containerization:
- Runtime: [Docker, Podman, none]
- Registry: [ECR, Docker Hub, GCR]

Orchestration:
- Platform: [Kubernetes, ECS, Swarm, none]
- Service: [EKS, GKE, AKS, self-managed]

CI/CD:
- Platform: [GitHub Actions, GitLab CI, Jenkins]
- Environments: [dev, staging, prod]
- Strategy: [blue-green, rolling, canary]

Monitoring:
- Metrics: [Prometheus, Datadog, CloudWatch]
- Logging: [ELK, Loki, CloudWatch Logs]
- Alerting: [PagerDuty, OpsGenie, Slack]

Security:
- Secrets: [Vault, AWS Secrets Manager]
- WAF: [AWS WAF, Cloudflare]
- Scanning: [Snyk, SonarQube, Trivy]

Existing Infrastructure:
- [Description of existing infra to integrate]`,
    examples: [
      "Hosting: AWS eu-west-1, with disaster recovery in eu-central-1",
      "Containerization: Docker with ECR registry",
      "Orchestration: EKS (managed Kubernetes)",
      "CI/CD: GitHub Actions with dev → staging → prod pipeline",
      "Monitoring: Prometheus + Grafana + PagerDuty",
      "Security: AWS Secrets Manager, WAF, Snyk for vulnerability scanning"
    ]
  }
];

export function generateGreenPaperMarkdown(
  session: GreenPaperSession,
  output: GreenPaperOutput
): string {
  const timestamp = new Date(session.session_date).toISOString().split('T')[0];

  return `# BMAD Green-Paper Session
## ${session.project_name}

**Date**: ${timestamp}
**Facilitator**: ${session.facilitator}
**Participants**: ${session.participants.join(', ')}
**Duration**: ${session.duration_minutes || 'N/A'} minutes

---

## 1. Business Vision

### Vision Statement
${output.vision.problemStatement}

### Business Goals
${output.vision.businessGoals.map((goal, i) => `${i + 1}. ${goal}`).join('\n')}

### Success Criteria
${output.vision.successCriteria.map((criteria, i) => `${i + 1}. ${criteria}`).join('\n')}

---

## 2. Stakeholders

### Internal Stakeholders
${output.stakeholders.internal.map(s => `- ${s}`).join('\n')}

### External Stakeholders
${output.stakeholders.external.map(s => `- ${s}`).join('\n')}

### Decision Makers
${output.stakeholders.decisionMakers.map(s => `- ${s}`).join('\n')}

---

## 3. Guiding Principles

${output.principles.map((p, i) => `### ${i + 1}. ${p.principle}
${p.rationale}\n`).join('\n')}

---

## 4. Scope Definition

### In Scope
${output.scope.included.map(s => `- ${s}`).join('\n')}

### Out of Scope
${output.scope.excluded.map(s => `- ${s}`).join('\n')}

### Assumptions
${output.scope.assumptions.map(s => `- ${s}`).join('\n')}

---

## 5. Constraints

### Budget
${output.constraints.budget || 'Not specified'}

### Timeline
${output.constraints.timeline || 'Not specified'}

### Technology
${output.constraints.technology ? output.constraints.technology.map(t => `- ${t}`).join('\n') : 'Not specified'}

### Resources
${output.constraints.resources || 'Not specified'}

### Regulatory
${output.constraints.regulatory ? output.constraints.regulatory.map(r => `- ${r}`).join('\n') : 'None'}

---

## 6. Known Risks

${output.risks.map((r, i) => `### ${i + 1}. ${r.risk}
- **Category**: ${r.category}
- **Impact**: ${r.impact}
- **Probability**: ${r.probability}
${r.mitigation ? `- **Mitigation**: ${r.mitigation}` : ''}\n`).join('\n')}

---

## 7. Development Stack

${output.developmentStack ? `
### Languages
${output.developmentStack.languages?.map(l => `- ${l}`).join('\n') || 'Not specified'}

### Frameworks
${output.developmentStack.frameworks?.map(f => `- ${f}`).join('\n') || 'Not specified'}

### Databases
${output.developmentStack.databases?.map(d => `- ${d}`).join('\n') || 'Not specified'}

### Testing
${output.developmentStack.testing?.map(t => `- ${t}`).join('\n') || 'Not specified'}

### Version Control
${output.developmentStack.versionControl || 'Not specified'}

### Existing Codebase
${output.developmentStack.existingCodebase || 'Greenfield project - no existing code'}
` : 'Not yet defined - will be determined during specification phase'}

---

## 8. Operational Stack

${output.operationalStack ? `
### Hosting
${output.operationalStack.hosting || 'Not specified'}

### Containerization
${output.operationalStack.containerization || 'Not specified'}

### CI/CD
${output.operationalStack.cicd || 'Not specified'}

### Monitoring
${output.operationalStack.monitoring?.map(m => `- ${m}`).join('\n') || 'Not specified'}

### Security
${output.operationalStack.security?.map(s => `- ${s}`).join('\n') || 'Not specified'}

### Existing Infrastructure
${output.operationalStack.existingInfra || 'No existing infrastructure'}
` : 'Not yet defined - will be determined during specification phase'}

---

## Next Steps

This green-paper document will be used as input for the Spec-Kit workflow:

1. **Constitution Phase**: Transform vision, principles, and constraints into formal constitution
2. **Specification Phase**: Design architecture and components based on principles
3. **Task Generation Phase**: Break down work into epics, features, and stories

**Mapping**:
- Vision → Constitution Principles
- Stakeholders → Constitution Stakeholders
- Scope → Constitution Scope
- Constraints → Constitution Constraints
- Risks → Constitution Risks
- Development Stack → Architecture Spec (developmentStack)
- Operational Stack → Architecture Spec (operationalStack)

---

*Generated by BMAD Green-Paper Session - ${timestamp}*
`;
}

export default {
  GREEN_PAPER_QUESTIONS,
  generateGreenPaperMarkdown
};
