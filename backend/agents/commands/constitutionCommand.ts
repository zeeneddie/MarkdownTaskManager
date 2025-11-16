/**
 * Constitution Command (/constitution)
 *
 * Analyzes business requirements and constraints to create project constitution.
 *
 * Agent: Peter (Product Owner) - deepseek-r1:latest
 * Purpose: Transform business case → project principles, requirements, risks, scope
 *
 * Week 8 - Monday Afternoon Implementation
 */

import { Agent } from 'kaibanjs';
import {
  ConstitutionInput,
  ConstitutionResult,
  Principle,
  PrincipleCategory,
  Requirement,
  RequirementType,
  Constraint,
  ConstraintType,
  Risk,
  RiskLevel,
  Scope,
  Phase,
  Priority,
  calculateRiskScore,
  generateId
} from '../types/SpecKit';
import {
  SlashCommandType,
  SlashCommandInput,
  SlashCommandOutput,
  CommandStatus,
  CommandDefinition,
  OutputFormat,
  RecommendationPriority
} from '../types/SlashCommand';
import { registerCommand } from '../workflows/commandRegistry';

// ============================================================================
// COMMAND METADATA
// ============================================================================

export const CONSTITUTION_COMMAND = {
  name: '/constitution',
  description: 'Analyze business requirements to create project constitution',
  agent: 'Peter', // Product Owner
  model: 'deepseek-r1:latest',
  category: 'specification',
  estimatedTime: '5-10 minutes'
};

/**
 * Full CommandDefinition for /constitution command
 */
export const CONSTITUTION_DEFINITION: CommandDefinition = {
  type: SlashCommandType.CONSTITUTION,
  name: 'Constitution Generator',
  description: 'Analyzes business requirements, constraints, and stakeholder needs to generate a comprehensive project constitution with principles, requirements, risks, and scope',
  persona: 'Product Owner (Peter) - Expert in business analysis, requirements gathering, stakeholder management, and risk assessment. Uses deep reasoning to transform business cases into actionable project foundations.',
  expertise: [
    'Business Case Analysis',
    'Requirements Engineering',
    'Stakeholder Analysis',
    'Risk Assessment & Management',
    'Scope Definition',
    'Constraint Analysis',
    'Project Principles & Values',
    'Success Criteria Definition'
  ],
  capabilities: [
    'Extract value propositions from business cases',
    'Identify and categorize stakeholders',
    'Define project principles across multiple categories',
    'Generate functional, non-functional, and business requirements',
    'Identify and assess project risks with mitigation strategies',
    'Define clear project scope (in-scope/out-of-scope)',
    'Create phased delivery plans',
    'Analyze constraints (legal, technical, resource, time)',
    'Generate comprehensive project constitution documents'
  ],
  bestUsedFor: [
    'New project initiation',
    'Business case analysis',
    'Requirements discovery workshops',
    'Project charter creation',
    'Stakeholder alignment sessions',
    'Risk assessment at project start',
    'Scope definition and boundary setting',
    'Foundation for Spec-Kit workflow (Stage 1)'
  ],
  requiredContext: [
    'businessCase',
    'stakeholders',
    'constraints',
    'successCriteria'
  ],
  optionalContext: [
    'technicalContext',
    'existingSystems',
    'teamSize',
    'timeline',
    'budget'
  ],
  outputTypes: [OutputFormat.MARKDOWN, OutputFormat.JSON, OutputFormat.TEXT],
  examples: [
    {
      scenario: 'E-commerce platform project initiation',
      input: {
        command: SlashCommandType.CONSTITUTION,
        context: {
          metadata: {
            businessCase: 'Build an online customer portal to reduce support tickets by 50%',
            stakeholders: ['customers', 'support team', 'product team'],
            constraints: ['GDPR compliance', 'Budget: €50k', 'Timeline: 6 months'],
            requirements: ['Self-service ticketing', 'Knowledge base', 'User authentication']
          }
        } as any
      },
      expectedOutcome: 'Generates constitution with 4-6 principles (UX, Security, Performance), 10-15 requirements (functional, non-functional, business), 4-6 risks with mitigation strategies, and clear scope with 3 phases'
    },
    {
      scenario: 'SaaS product validation',
      input: {
        command: SlashCommandType.CONSTITUTION,
        context: {
          metadata: {
            businessCase: 'MVP for project management tool targeting remote teams',
            stakeholders: ['remote workers', 'team leads', 'executives'],
            constraints: ['Timeline: 3 months', 'Team size: 5 developers'],
            requirements: ['Task management', 'Team collaboration', 'Progress tracking']
          }
        } as any
      },
      expectedOutcome: 'Constitution focused on MVP delivery, emphasizing scalability principles, lean requirements prioritization, and time-constrained phased approach'
    },
    {
      scenario: 'Legacy system modernization',
      input: {
        command: SlashCommandType.CONSTITUTION,
        context: {
          metadata: {
            businessCase: 'Modernize monolithic CRM to microservices architecture',
            stakeholders: ['sales team', 'IT operations', 'customers'],
            constraints: ['Zero downtime migration', 'Integration with existing systems', 'Security compliance'],
            requirements: ['Incremental migration', 'Data consistency', 'Performance improvement']
          }
        } as any
      },
      expectedOutcome: 'Constitution addressing migration risks, integration constraints, backward compatibility requirements, and phased rollout strategy'
    }
  ]
};

// ============================================================================
// MAIN EXECUTION FUNCTION
// ============================================================================

/**
 * Execute constitution generation
 *
 * @param input - Constitution input with business case and constraints
 * @param agent - Peter (Product Owner agent)
 * @returns Constitution result with principles, requirements, risks, scope
 */
export async function executeConstitution(
  input: ConstitutionInput,
  agent: Agent
): Promise<ConstitutionResult> {
  console.log('🏛️ Executing /constitution command...');
  console.log(`Business Case: ${input.businessCase}`);
  console.log(`Stakeholders: ${input.stakeholders.join(', ')}`);

  const startTime = Date.now();

  // Step 1: Analyze business case
  console.log('\n📊 Step 1: Analyzing business case...');
  const businessAnalysis = await analyzeBusinessCase(input, agent);

  // Step 2: Define principles
  console.log('\n📜 Step 2: Defining project principles...');
  const principles = await definePrinciples(input, businessAnalysis, agent);

  // Step 3: Extract requirements
  console.log('\n📋 Step 3: Extracting requirements...');
  const requirements = await extractRequirements(input, principles, agent);

  // Step 4: Identify constraints
  console.log('\n🔒 Step 4: Identifying constraints...');
  const constraints = await identifyConstraints(input, agent);

  // Step 5: Assess risks
  console.log('\n⚠️  Step 5: Assessing risks...');
  const risks = await assessRisks(input, requirements, constraints, agent);

  // Step 6: Define scope
  console.log('\n🎯 Step 6: Defining project scope...');
  const scope = await defineScope(input, requirements, agent);

  // Build result
  const result: ConstitutionResult = {
    principles,
    requirements,
    constraints,
    risks,
    scope,
    metadata: {
      generatedAt: new Date(),
      generatedBy: 'Peter (Product Owner)',
      version: '1.0.0'
    }
  };

  const duration = Date.now() - startTime;
  console.log(`\n✅ Constitution generated in ${(duration / 1000).toFixed(2)}s`);
  console.log(`   - ${principles.length} principles`);
  console.log(`   - ${requirements.length} requirements`);
  console.log(`   - ${constraints.length} constraints`);
  console.log(`   - ${risks.length} risks`);
  console.log(`   - ${scope.inScope.length} in-scope items`);

  return result;
}

// ============================================================================
// STEP 1: BUSINESS CASE ANALYSIS
// ============================================================================

interface BusinessAnalysis {
  valueProposition: string;
  targetUsers: string[];
  businessGoals: string[];
  keyMetrics: string[];
}

async function analyzeBusinessCase(
  input: ConstitutionInput,
  agent: Agent
): Promise<BusinessAnalysis> {
  const prompt = `
Analyze this business case and extract key information:

**Business Case:**
${input.businessCase}

**Stakeholders:**
${input.stakeholders.join(', ')}

**Success Criteria:**
${input.successCriteria.join('\n')}

Please provide:
1. **Value Proposition**: What core value does this project deliver?
2. **Target Users**: Who will use this system?
3. **Business Goals**: What business objectives does this achieve?
4. **Key Metrics**: How will we measure success?

Format as JSON:
{
  "valueProposition": "...",
  "targetUsers": ["..."],
  "businessGoals": ["..."],
  "keyMetrics": ["..."]
}
`;

  // TODO: Replace with actual agent execution when KaibanJS is integrated
  // For now, return structured analysis based on input
  const analysis: BusinessAnalysis = {
    valueProposition: extractValueProposition(input.businessCase),
    targetUsers: input.stakeholders,
    businessGoals: input.successCriteria,
    keyMetrics: input.successCriteria.map(c => `Metric for: ${c}`)
  };

  return analysis;
}

function extractValueProposition(businessCase: string): string {
  // Simple heuristic: first sentence or main clause
  const sentences = businessCase.split(/[.!?]/);
  return sentences[0]?.trim() || businessCase.substring(0, 100);
}

// ============================================================================
// STEP 2: DEFINE PRINCIPLES
// ============================================================================

async function definePrinciples(
  input: ConstitutionInput,
  analysis: BusinessAnalysis,
  agent: Agent
): Promise<Principle[]> {
  const principles: Principle[] = [];
  let counter = 1;

  // Extract principles from success criteria and constraints
  // User Experience principles
  if (analysis.targetUsers.includes('customers') || analysis.targetUsers.includes('users')) {
    principles.push({
      id: generateId('PRIN', counter++),
      category: PrincipleCategory.USER_EXPERIENCE,
      principle: 'User-centric design',
      rationale: 'End users are primary stakeholders',
      application: [
        'Design interfaces for user needs',
        'Prioritize user feedback',
        'Optimize for user workflows'
      ]
    });
  }

  // Security principles (from constraints)
  const hasSecurityConstraint = input.constraints.some(c =>
    c.toLowerCase().includes('gdpr') ||
    c.toLowerCase().includes('security') ||
    c.toLowerCase().includes('compliance')
  );

  if (hasSecurityConstraint) {
    principles.push({
      id: generateId('PRIN', counter++),
      category: PrincipleCategory.SECURITY,
      principle: 'Security and compliance by design',
      rationale: 'Legal and regulatory requirements must be met',
      application: [
        'Implement security from day 1',
        'Regular security audits',
        'Encrypt sensitive data',
        'Follow compliance standards'
      ]
    });
  }

  // Performance principles
  if (analysis.businessGoals.some(g => g.toLowerCase().includes('fast') || g.toLowerCase().includes('time'))) {
    principles.push({
      id: generateId('PRIN', counter++),
      category: PrincipleCategory.PERFORMANCE,
      principle: 'Performance optimization',
      rationale: 'Fast response times improve user satisfaction',
      application: [
        'Optimize critical paths',
        'Use caching strategies',
        'Monitor performance metrics'
      ]
    });
  }

  // Scalability principles
  if (analysis.businessGoals.some(g => g.toLowerCase().includes('grow') || g.toLowerCase().includes('scale'))) {
    principles.push({
      id: generateId('PRIN', counter++),
      category: PrincipleCategory.SCALABILITY,
      principle: 'Built for growth',
      rationale: 'System must handle increasing load',
      application: [
        'Design for horizontal scaling',
        'Use load balancing',
        'Plan capacity ahead'
      ]
    });
  }

  // Maintainability principles (always important)
  principles.push({
    id: generateId('PRIN', counter++),
    category: PrincipleCategory.MAINTAINABILITY,
    principle: 'Clean, maintainable code',
    rationale: 'Long-term sustainability requires maintainable codebase',
    application: [
      'Follow coding standards',
      'Write comprehensive tests',
      'Document architecture and APIs',
      'Regular refactoring'
    ]
  });

  return principles;
}

// ============================================================================
// STEP 3: EXTRACT REQUIREMENTS
// ============================================================================

async function extractRequirements(
  input: ConstitutionInput,
  principles: Principle[],
  agent: Agent
): Promise<Requirement[]> {
  const requirements: Requirement[] = [];
  let counter = 1;

  // Extract functional requirements from business case
  const keywords = ['must', 'should', 'need', 'allow', 'enable', 'provide', 'support'];
  const sentences = input.businessCase.split(/[.!?]/);

  sentences.forEach(sentence => {
    const trimmed = sentence.trim();
    if (keywords.some(kw => trimmed.toLowerCase().includes(kw)) && trimmed.length > 20) {
      requirements.push({
        id: generateId('REQ', counter++),
        type: RequirementType.FUNCTIONAL,
        description: trimmed,
        priority: Priority.HIGH,
        relatedPrinciples: [principles[0]?.id],
        acceptanceCriteria: [`System implements: ${trimmed}`]
      });
    }
  });

  // Extract non-functional requirements from constraints
  input.constraints.forEach(constraint => {
    if (constraint.toLowerCase().includes('performance') || constraint.toLowerCase().includes('fast')) {
      requirements.push({
        id: generateId('REQ', counter++),
        type: RequirementType.NON_FUNCTIONAL,
        description: `Performance: ${constraint}`,
        priority: Priority.HIGH,
        relatedPrinciples: principles.filter(p => p.category === PrincipleCategory.PERFORMANCE).map(p => p.id)
      });
    }

    if (constraint.toLowerCase().includes('security') || constraint.toLowerCase().includes('gdpr')) {
      requirements.push({
        id: generateId('REQ', counter++),
        type: RequirementType.NON_FUNCTIONAL,
        description: `Security: ${constraint}`,
        priority: Priority.CRITICAL,
        relatedPrinciples: principles.filter(p => p.category === PrincipleCategory.SECURITY).map(p => p.id)
      });
    }
  });

  // Business requirements from success criteria
  input.successCriteria.forEach(criterion => {
    requirements.push({
      id: generateId('REQ', counter++),
      type: RequirementType.BUSINESS,
      description: `Business goal: ${criterion}`,
      priority: Priority.HIGH,
      acceptanceCriteria: [`Achieve: ${criterion}`]
    });
  });

  return requirements;
}

// ============================================================================
// STEP 4: IDENTIFY CONSTRAINTS
// ============================================================================

async function identifyConstraints(
  input: ConstitutionInput,
  agent: Agent
): Promise<Constraint[]> {
  const constraints: Constraint[] = [];
  let counter = 1;

  // Convert input constraints to structured format
  input.constraints.forEach(constraintText => {
    let type: ConstraintType = ConstraintType.TECHNICAL;
    let impact = 'May limit implementation choices';

    // Determine constraint type
    if (constraintText.toLowerCase().includes('legal') || constraintText.toLowerCase().includes('gdpr') || constraintText.toLowerCase().includes('compliance')) {
      type = ConstraintType.LEGAL;
      impact = 'Legal violation if not followed';
    } else if (constraintText.toLowerCase().includes('budget') || constraintText.toLowerCase().includes('cost')) {
      type = ConstraintType.RESOURCE;
      impact = 'May require cost optimization';
    } else if (constraintText.toLowerCase().includes('time') || constraintText.toLowerCase().includes('deadline')) {
      type = ConstraintType.TIME;
      impact = 'May require scope reduction';
    } else if (constraintText.toLowerCase().includes('business')) {
      type = ConstraintType.BUSINESS;
      impact = 'May affect product decisions';
    }

    constraints.push({
      id: generateId('CONST', counter++),
      type,
      description: constraintText,
      impact,
      mitigation: `Plan for: ${constraintText}`
    });
  });

  // Add technical context constraints if provided
  if (input.technicalContext?.existingSystems) {
    constraints.push({
      id: generateId('CONST', counter++),
      type: ConstraintType.TECHNICAL,
      description: `Must integrate with: ${input.technicalContext.existingSystems.join(', ')}`,
      impact: 'Integration complexity',
      mitigation: 'Design integration layer early'
    });
  }

  return constraints;
}

// ============================================================================
// STEP 5: ASSESS RISKS
// ============================================================================

async function assessRisks(
  input: ConstitutionInput,
  requirements: Requirement[],
  constraints: Constraint[],
  agent: Agent
): Promise<Risk[]> {
  const risks: Risk[] = [];
  let counter = 1;

  // Technical risks from constraints
  const technicalConstraints = constraints.filter(c => c.type === ConstraintType.TECHNICAL);
  if (technicalConstraints.length > 2) {
    risks.push({
      id: generateId('RISK', counter++),
      description: 'Multiple technical constraints may increase complexity',
      impact: RiskLevel.HIGH,
      likelihood: RiskLevel.MEDIUM,
      mitigation: [
        'Early technical spike',
        'Prototype integration points',
        'Regular technical reviews'
      ],
      relatedItems: technicalConstraints.map(c => c.id)
    });
  }

  // Legal/compliance risks
  const legalConstraints = constraints.filter(c => c.type === ConstraintType.LEGAL);
  if (legalConstraints.length > 0) {
    risks.push({
      id: generateId('RISK', counter++),
      description: 'Compliance failure could result in legal penalties',
      impact: RiskLevel.CRITICAL,
      likelihood: RiskLevel.LOW,
      mitigation: [
        'Legal review at each milestone',
        'Compliance checklist',
        'Regular audits'
      ],
      relatedItems: legalConstraints.map(c => c.id)
    });
  }

  // Resource risks
  const resourceConstraints = constraints.filter(c => c.type === ConstraintType.RESOURCE);
  if (resourceConstraints.length > 0) {
    risks.push({
      id: generateId('RISK', counter++),
      description: 'Resource constraints may affect delivery timeline',
      impact: RiskLevel.MEDIUM,
      likelihood: RiskLevel.HIGH,
      mitigation: [
        'Prioritize ruthlessly',
        'MVP approach',
        'Regular capacity planning'
      ]
    });
  }

  // Scope creep risk (always present)
  risks.push({
    id: generateId('RISK', counter++),
    description: 'Scope creep may delay delivery',
    impact: RiskLevel.HIGH,
    likelihood: RiskLevel.MEDIUM,
    mitigation: [
      'Clear scope definition',
      'Change control process',
      'Regular stakeholder alignment'
    ]
  });

  return risks;
}

// ============================================================================
// STEP 6: DEFINE SCOPE
// ============================================================================

async function defineScope(
  input: ConstitutionInput,
  requirements: Requirement[],
  agent: Agent
): Promise<Scope> {
  // Extract in-scope items from requirements
  const inScope: string[] = [];
  const outScope: string[] = [];

  // Functional requirements → in scope
  const functionalReqs = requirements.filter(r => r.type === RequirementType.FUNCTIONAL);
  functionalReqs.forEach(req => {
    inScope.push(req.description);
  });

  // Critical requirements → Phase 1
  const criticalReqs = requirements.filter(r => r.priority === Priority.CRITICAL || r.priority === Priority.HIGH);
  const mediumReqs = requirements.filter(r => r.priority === Priority.MEDIUM);
  const lowReqs = requirements.filter(r => r.priority === Priority.LOW);

  // Define phases
  const phases: Phase[] = [];

  if (criticalReqs.length > 0) {
    phases.push({
      number: 1,
      name: 'MVP - Core Functionality',
      goals: criticalReqs.slice(0, 5).map(r => r.description),
      duration: '4-6 weeks',
      deliverables: ['Core system functional', 'Basic UI', 'Essential integrations']
    });
  }

  if (mediumReqs.length > 0) {
    phases.push({
      number: 2,
      name: 'Enhancement Phase',
      goals: mediumReqs.slice(0, 5).map(r => r.description),
      duration: '3-4 weeks',
      deliverables: ['Enhanced features', 'Improved UX', 'Additional integrations']
    });
  }

  if (lowReqs.length > 0) {
    phases.push({
      number: 3,
      name: 'Polish & Optimization',
      goals: lowReqs.slice(0, 3).map(r => r.description),
      duration: '2-3 weeks',
      deliverables: ['Performance optimization', 'Advanced features', 'Documentation']
    });
  }

  // Common out-of-scope items
  outScope.push('Advanced analytics (future)');
  outScope.push('Mobile apps (future)');
  outScope.push('Third-party integrations beyond core requirements');

  // Assumptions
  const assumptions = [
    'Team has required skills',
    'Infrastructure is available',
    'Stakeholders are available for feedback',
    'Requirements are stable'
  ];

  return {
    inScope,
    outScope,
    phases,
    assumptions
  };
}

// ============================================================================
// OUTPUT FORMATTING
// ============================================================================

/**
 * Format constitution as Markdown
 */
export function formatConstitutionMarkdown(constitution: ConstitutionResult): string {
  let markdown = '# Project Constitution\n\n';
  markdown += `**Generated**: ${constitution.metadata.generatedAt.toISOString()}\n`;
  markdown += `**By**: ${constitution.metadata.generatedBy}\n`;
  markdown += `**Version**: ${constitution.metadata.version}\n\n`;
  markdown += '---\n\n';

  // Principles
  markdown += '## 🏛️ Project Principles\n\n';
  constitution.principles.forEach(principle => {
    markdown += `### ${principle.principle} (${principle.category})\n\n`;
    markdown += `**ID**: ${principle.id}\n\n`;
    markdown += `**Rationale**: ${principle.rationale}\n\n`;
    markdown += '**Application**:\n';
    principle.application.forEach(app => {
      markdown += `- ${app}\n`;
    });
    markdown += '\n';
  });

  // Requirements
  markdown += '## 📋 Requirements\n\n';
  const reqsByType = {
    [RequirementType.FUNCTIONAL]: constitution.requirements.filter(r => r.type === RequirementType.FUNCTIONAL),
    [RequirementType.NON_FUNCTIONAL]: constitution.requirements.filter(r => r.type === RequirementType.NON_FUNCTIONAL),
    [RequirementType.BUSINESS]: constitution.requirements.filter(r => r.type === RequirementType.BUSINESS),
    [RequirementType.TECHNICAL]: constitution.requirements.filter(r => r.type === RequirementType.TECHNICAL)
  };

  Object.entries(reqsByType).forEach(([type, reqs]) => {
    if (reqs.length > 0) {
      markdown += `### ${type}\n\n`;
      reqs.forEach(req => {
        markdown += `- **[${req.id}]** ${req.description} (${req.priority})\n`;
      });
      markdown += '\n';
    }
  });

  // Constraints
  markdown += '## 🔒 Constraints\n\n';
  constitution.constraints.forEach(constraint => {
    markdown += `### ${constraint.description} (${constraint.type})\n\n`;
    markdown += `**ID**: ${constraint.id}\n\n`;
    markdown += `**Impact**: ${constraint.impact}\n\n`;
    if (constraint.mitigation) {
      markdown += `**Mitigation**: ${constraint.mitigation}\n\n`;
    }
  });

  // Risks
  markdown += '## ⚠️ Risks\n\n';
  constitution.risks.forEach(risk => {
    const riskScore = calculateRiskScore(risk.impact, risk.likelihood);
    markdown += `### ${risk.description}\n\n`;
    markdown += `**ID**: ${risk.id}\n\n`;
    markdown += `**Impact**: ${risk.impact} | **Likelihood**: ${risk.likelihood} | **Score**: ${riskScore.toFixed(2)}\n\n`;
    markdown += '**Mitigation**:\n';
    risk.mitigation.forEach(mit => {
      markdown += `- ${mit}\n`;
    });
    markdown += '\n';
  });

  // Scope
  markdown += '## 🎯 Project Scope\n\n';
  markdown += '### In Scope\n\n';
  constitution.scope.inScope.forEach(item => {
    markdown += `- ${item}\n`;
  });
  markdown += '\n### Out of Scope\n\n';
  constitution.scope.outScope.forEach(item => {
    markdown += `- ${item}\n`;
  });
  markdown += '\n### Phases\n\n';
  constitution.scope.phases.forEach(phase => {
    markdown += `#### Phase ${phase.number}: ${phase.name}\n\n`;
    markdown += `**Duration**: ${phase.duration}\n\n`;
    markdown += '**Goals**:\n';
    phase.goals.forEach(goal => {
      markdown += `- ${goal}\n`;
    });
    markdown += '\n**Deliverables**:\n';
    phase.deliverables.forEach(del => {
      markdown += `- ${del}\n`;
    });
    markdown += '\n';
  });

  markdown += '### Assumptions\n\n';
  constitution.scope.assumptions.forEach(assumption => {
    markdown += `- ${assumption}\n`;
  });

  return markdown;
}

// ============================================================================
// COMMAND EXECUTOR (CommandRegistry Interface)
// ============================================================================

/**
 * Execute constitution command via CommandRegistry interface
 * Adapts the executeConstitution function to match CommandExecutor signature
 */
export async function executeConstitutionCommand(
  input: SlashCommandInput
): Promise<SlashCommandOutput> {
  const startTime = Date.now();

  try {
    // Extract context (using metadata for custom fields)
    const ctx = input.context as any;
    const constitutionInput: ConstitutionInput = {
      businessCase: ctx.businessCase || '',
      stakeholders: ctx.stakeholders || [],
      constraints: ctx.constraints || [],
      successCriteria: ctx.successCriteria || ctx.requirements || [],
      technicalContext: ctx.technicalContext
    };

    // Mock agent (will be replaced with actual agent from KaibanJS)
    const mockAgent: Agent = {
      name: 'Peter',
      role: 'Product Owner',
      goal: 'Analyze business requirements',
      background: 'Product Owner with expertise in business analysis'
    } as Agent;

    // Execute constitution generation
    const result = await executeConstitution(constitutionInput, mockAgent);

    // Convert to SlashCommandOutput
    const duration = Date.now() - startTime;

    const output: SlashCommandOutput = {
      commandId: `const-${Date.now()}`,
      command: SlashCommandType.CONSTITUTION,
      status: CommandStatus.COMPLETED,
      executedBy: 'Peter (Product Owner)',
      executedAt: new Date(),
      completedAt: new Date(),
      duration,
      analysis: {
        summary: `Generated project constitution with ${result.principles.length} principles, ${result.requirements.length} requirements, ${result.risks.length} risks`,
        scores: {
          completeness: 0.9,
          clarity: 0.85,
          actionability: 0.9
        },
        strengths: [
          `${result.principles.length} well-defined project principles`,
          `${result.requirements.length} structured requirements`,
          `${result.risks.length} identified risks with mitigation strategies`,
          `Clear scope definition with ${result.scope.phases.length} delivery phases`
        ],
        weaknesses: result.risks.filter(r => r.impact === RiskLevel.CRITICAL || r.impact === RiskLevel.HIGH).length > 0
          ? ['High-risk items require immediate attention']
          : []
      },
      recommendations: [
        {
          id: 'rec-1',
          priority: RecommendationPriority.HIGH,
          category: 'Next Steps',
          title: 'Proceed to Specification Stage',
          description: 'Use this constitution as input for /specification command to generate technical architecture',
          rationale: 'Constitution provides the foundation for technical design',
          benefits: ['Aligned technical design', 'Requirements traceability'],
          effort: 'MEDIUM',
          impact: 'HIGH',
          confidence: 0.95
        },
        {
          id: 'rec-2',
          priority: RecommendationPriority.MEDIUM,
          category: 'Risk Management',
          title: 'Review High-Impact Risks',
          description: `Address ${result.risks.filter(r => r.impact === RiskLevel.HIGH || r.impact === RiskLevel.CRITICAL).length} high-impact risks before proceeding`,
          rationale: 'Mitigating risks early prevents costly issues later',
          benefits: ['Reduced project risk', 'Better planning'],
          effort: 'MEDIUM',
          impact: 'HIGH',
          confidence: 0.9
        }
      ],
      topRecommendation: {
        id: 'rec-1',
        priority: RecommendationPriority.HIGH,
        category: 'Next Steps',
        title: 'Proceed to Specification Stage',
        description: 'Use this constitution as input for /specification command',
        rationale: 'Constitution provides the foundation for technical design',
        benefits: ['Aligned technical design', 'Requirements traceability'],
        effort: 'MEDIUM',
        impact: 'HIGH',
        confidence: 0.95
      },
      confidence: 0.88,
      needsHumanReview: result.risks.some(r => r.impact === RiskLevel.CRITICAL),
      rationale: 'Constitution generated based on business case analysis, stakeholder input, and constraint evaluation',
      nextSteps: [
        'Review constitution with stakeholders',
        'Validate principles and requirements',
        'Execute /specification command for technical design',
        'Plan risk mitigation strategies'
      ],
      outputFormat: input.options?.outputFormat || OutputFormat.MARKDOWN,
      formattedOutput: formatConstitutionMarkdown(result)
    };

    return output;
  } catch (error) {
    const duration = Date.now() - startTime;

    // Return error output
    return {
      commandId: `const-error-${Date.now()}`,
      command: SlashCommandType.CONSTITUTION,
      status: CommandStatus.FAILED,
      executedBy: 'Peter (Product Owner)',
      executedAt: new Date(),
      completedAt: new Date(),
      duration,
      analysis: {
        summary: `Constitution generation failed: ${error instanceof Error ? error.message : String(error)}`,
        issues: [{
          id: 'constitution-error',
          severity: 'CRITICAL',
          category: 'Execution Error',
          title: 'Constitution generation failed',
          description: error instanceof Error ? error.message : String(error),
          location: 'Constitution Command',
          recommendation: 'Check input context and try again',
          autoFixable: false
        }]
      },
      recommendations: [],
      confidence: 0,
      needsHumanReview: true,
      rationale: 'Execution failed',
      outputFormat: OutputFormat.TEXT,
      formattedOutput: `Error: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

// ============================================================================
// COMMAND REGISTRATION
// ============================================================================

/**
 * Register /constitution command with the command registry
 */
export function registerConstitutionCommand(): void {
  registerCommand(CONSTITUTION_DEFINITION, executeConstitutionCommand);
}
