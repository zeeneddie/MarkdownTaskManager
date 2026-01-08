/**
 * Architecture Review Command (/review-architecture)
 *
 * BMAD-inspired evaluation phase for architecture validation.
 * Reviews specification against constitution, generates ADRs, and identifies gaps.
 *
 * Agent: Felix (Feature Architect) - qwen2.5-coder:7b
 * Purpose: Specification + Constitution -> Validated Architecture with ADRs
 *
 * Week 10+ Enhancement - Architecture Evaluation Phase
 */

import { Agent } from 'kaibanjs';
import {
  ArchitectureReviewInput,
  ArchitectureReviewResult,
  ReviewVerdict,
  TradeOffCategory,
  TradeOffAnalysis,
  AlignmentCheck,
  ArchitectureRisk,
  CostEstimate,
  ArchitectureDecisionRecord,
  Priority,
  RiskLevel,
  ConstitutionResult,
  SpecificationResult,
  PrincipleCategory,
  ArchitectureReviewConfig,
  HumanApprovalRequest
} from '../types/SpecKit';

// ============================================================================
// COMMAND METADATA
// ============================================================================

export const ARCHITECTURE_REVIEW_COMMAND = {
  name: '/review-architecture',
  description: 'Validate architecture against constitution and generate ADRs',
  agent: 'Felix', // Feature Architect
  model: 'qwen2.5-coder:7b',
  category: 'architecture',
  estimatedTime: '5-10 minutes'
};

// ============================================================================
// MAIN EXECUTION FUNCTION
// ============================================================================

/**
 * Execute architecture review
 *
 * @param input - Review input with constitution and specification
 * @param agent - Felix (Feature Architect agent)
 * @returns Architecture review result with ADRs, alignment checks, and recommendations
 */
export async function executeArchitectureReview(
  input: ArchitectureReviewInput,
  agent: Agent
): Promise<ArchitectureReviewResult> {
  console.log('🔍 Executing /review-architecture command...');
  console.log(`   Reviewing specification v${input.specification.metadata.version}`);
  console.log(`   Against constitution v${input.constitution.metadata.version}`);

  const startTime = Date.now();

  // Step 1: Check alignment with principles
  console.log('\n📋 Step 1: Checking principle alignment...');
  const principleChecks = checkPrincipleAlignment(input.constitution, input.specification);

  // Step 2: Check alignment with requirements
  console.log('\n📋 Step 2: Checking requirement alignment...');
  const requirementChecks = checkRequirementAlignment(input.constitution, input.specification);

  // Step 3: Check alignment with constraints
  console.log('\n📋 Step 3: Checking constraint alignment...');
  const constraintChecks = checkConstraintAlignment(input.constitution, input.specification, input.greenPaperConstraints);

  // Step 4: Analyze trade-offs
  console.log('\n⚖️  Step 4: Analyzing trade-offs...');
  const tradeOffs = analyzeTradeOffs(input.specification);

  // Step 5: Generate ADRs
  console.log('\n📝 Step 5: Generating Architecture Decision Records...');
  const adrs = generateADRs(input.specification, tradeOffs);

  // Step 6: Identify risks
  console.log('\n⚠️  Step 6: Identifying architecture risks...');
  const risks = identifyRisks(input.specification, input.teamContext);

  // Step 7: Estimate costs
  console.log('\n💰 Step 7: Estimating costs...');
  const costEstimates = estimateCosts(input.specification);

  // Step 8: Calculate alignment score
  const alignmentScore = calculateAlignmentScore(principleChecks, requirementChecks, constraintChecks);
  const allAlignmentChecks = [...principleChecks, ...requirementChecks, ...constraintChecks];

  // Step 9: Determine verdict (95% threshold, no high-importance gaps allowed)
  const verdict = determineVerdict(alignmentScore, risks, allAlignmentChecks, input.reviewConfig);

  // Step 10: Generate recommendations
  const recommendations = generateRecommendations(principleChecks, requirementChecks, constraintChecks, risks);

  // Step 11: Generate executive summary
  const executiveSummary = generateExecutiveSummary(
    verdict,
    alignmentScore,
    adrs.length,
    risks.length,
    costEstimates
  );

  const duration = Date.now() - startTime;
  console.log(`\n✅ Architecture review complete in ${(duration / 1000).toFixed(2)}s`);
  console.log(`   Verdict: ${verdict}`);
  console.log(`   Alignment Score: ${alignmentScore}%`);
  console.log(`   ADRs Generated: ${adrs.length}`);
  console.log(`   Risks Identified: ${risks.length}`);

  // Build the result object
  const result: ArchitectureReviewResult = {
    verdict,
    confidence: alignmentScore / 100,
    alignmentChecks: {
      principles: principleChecks,
      requirements: requirementChecks,
      constraints: constraintChecks
    },
    alignmentScore,
    tradeOffs,
    adrs,
    risks,
    costEstimates,
    totalMonthlyCost: calculateTotalMonthlyCost(costEstimates),
    recommendations,
    conditions: verdict === ReviewVerdict.APPROVED_WITH_CONDITIONS
      ? extractConditions(recommendations)
      : undefined,
    requiredRevisions: verdict === ReviewVerdict.NEEDS_REVISION
      ? extractRequiredRevisions(principleChecks, requirementChecks, constraintChecks)
      : undefined,
    executiveSummary,
    metadata: {
      reviewedAt: new Date(),
      reviewedBy: 'Felix (Feature Architect)',
      version: '1.0.0',
      specificationVersion: input.specification.metadata.version
    }
  };

  // Generate human approval request if verdict requires it
  // Triggered when: score < 95%, high-importance gaps exist, or too many high risks
  if (verdict === ReviewVerdict.NEEDS_HUMAN_APPROVAL) {
    const highGaps = allAlignmentChecks.filter(c => !c.aligned && c.gapImportance === 'high');
    let reason = '';

    if (alignmentScore < 95) {
      reason = `Alignment score (${alignmentScore}%) is below 95% threshold.`;
    }
    if (highGaps.length > 0) {
      reason += ` ${highGaps.length} high-importance alignment gap(s) detected.`;
    }
    if (risks.filter(r => r.impact === RiskLevel.HIGH).length > 2) {
      reason += ` More than 2 high-impact risks identified.`;
    }

    result.humanApprovalRequest = generateHumanApprovalRequest(
      result,
      allAlignmentChecks,
      reason.trim()
    );

    console.log(`\n⚠️  HUMAN APPROVAL REQUIRED: ${reason.trim()}`);
    console.log(`   Request ID: ${result.humanApprovalRequest.requestId}`);
    console.log(`   Decisions Required: ${result.humanApprovalRequest.decisionsRequired.length}`);
  }

  return result;
}

// ============================================================================
// ALIGNMENT CHECKS
// ============================================================================

function checkPrincipleAlignment(
  constitution: ConstitutionResult,
  specification: SpecificationResult
): AlignmentCheck[] {
  const checks: AlignmentCheck[] = [];

  for (const principle of constitution.principles) {
    const check: AlignmentCheck = {
      aspect: 'Principle',
      source: `${principle.category}: ${principle.principle}`,
      architectureElement: '',
      aligned: false
    };

    // Check alignment based on principle category
    switch (principle.category) {
      case PrincipleCategory.SECURITY:
        check.architectureElement = 'Security measures in architecture';
        check.aligned = specification.architecture.technologies.other?.some(t =>
          t.toLowerCase().includes('security') ||
          t.toLowerCase().includes('auth')
        ) || specification.components.some(c =>
          c.name.toLowerCase().includes('auth')
        );
        if (!check.aligned) {
          check.gap = 'No explicit security components or technologies identified';
          check.remediation = 'Add authentication service and security scanning tools';
        }
        break;

      case PrincipleCategory.PERFORMANCE:
        check.architectureElement = 'Performance optimization in architecture';
        check.aligned = (specification.architecture.technologies.cache?.length ?? 0) > 0 ||
          specification.qualityRequirements.some(q => q.category === 'PERFORMANCE');
        if (!check.aligned) {
          check.gap = 'No caching layer or performance requirements defined';
          check.remediation = 'Add Redis or similar caching solution';
        }
        break;

      case PrincipleCategory.SCALABILITY:
        check.architectureElement = 'Scalability in architecture pattern';
        check.aligned = specification.architecture.pattern.includes('MICROSERVICES') ||
          specification.architecture.pattern.includes('LAYERED');
        if (!check.aligned) {
          check.gap = 'Architecture pattern may not scale well';
          check.remediation = 'Consider microservices or add horizontal scaling capability';
        }
        break;

      case PrincipleCategory.MAINTAINABILITY:
        check.architectureElement = 'Maintainability in component design';
        check.aligned = specification.components.every(c =>
          c.responsibilities.length > 0 && c.responsibilities.length <= 5
        );
        if (!check.aligned) {
          check.gap = 'Some components have too many responsibilities';
          check.remediation = 'Apply single responsibility principle to large components';
        }
        break;

      default:
        check.architectureElement = 'General architecture';
        check.aligned = true; // Default to aligned for unhandled categories
    }

    checks.push(check);
  }

  return checks;
}

function checkRequirementAlignment(
  constitution: ConstitutionResult,
  specification: SpecificationResult
): AlignmentCheck[] {
  const checks: AlignmentCheck[] = [];

  for (const requirement of constitution.requirements) {
    const check: AlignmentCheck = {
      aspect: 'Requirement',
      source: `[${requirement.type}] ${requirement.description}`,
      architectureElement: '',
      aligned: false
    };

    // Check if any component addresses this requirement
    const desc = requirement.description.toLowerCase();
    const matchingComponent = specification.components.find(c =>
      c.responsibilities.some(r =>
        r.toLowerCase().includes(desc.substring(0, 20))
      )
    );

    if (matchingComponent) {
      check.architectureElement = matchingComponent.name;
      check.aligned = true;
    } else {
      check.architectureElement = 'No matching component';
      check.gap = `No component explicitly addresses: ${requirement.description}`;
      check.remediation = `Add component or responsibility to address this requirement`;
    }

    checks.push(check);
  }

  return checks;
}

function checkConstraintAlignment(
  constitution: ConstitutionResult,
  specification: SpecificationResult,
  greenPaperConstraints?: ArchitectureReviewInput['greenPaperConstraints']
): AlignmentCheck[] {
  const checks: AlignmentCheck[] = [];

  // Check constitution constraints
  for (const constraint of constitution.constraints) {
    const check: AlignmentCheck = {
      aspect: 'Constraint',
      source: `[${constraint.type}] ${constraint.description}`,
      architectureElement: 'Architecture',
      aligned: true // Default to aligned, mark as not aligned if specific issue found
    };

    const desc = constraint.description.toLowerCase();

    // Check technology constraints
    if (desc.includes('must use') || desc.includes('require')) {
      const techMatch = specification.architecture.technologies;
      check.architectureElement = 'Technology stack';
      // This would need more sophisticated matching in production
      check.aligned = true;
    }

    checks.push(check);
  }

  // Check Green Paper constraints if provided
  if (greenPaperConstraints) {
    // Budget constraint
    if (greenPaperConstraints.budget) {
      checks.push({
        aspect: 'Budget Constraint',
        source: `Budget: ${greenPaperConstraints.budget}`,
        architectureElement: 'Infrastructure costs',
        aligned: true, // Would need actual cost calculation
        gap: undefined
      });
    }

    // Technology constraints
    if (greenPaperConstraints.technology?.length) {
      const requiredTech = greenPaperConstraints.technology;
      const usedTech = [
        ...(specification.architecture.technologies.backend || []),
        ...(specification.architecture.technologies.frontend || []),
        ...(specification.architecture.technologies.database || [])
      ];

      for (const tech of requiredTech) {
        const found = usedTech.some(t =>
          t.toLowerCase().includes(tech.toLowerCase())
        );
        checks.push({
          aspect: 'Technology Constraint',
          source: `Must use: ${tech}`,
          architectureElement: 'Technology stack',
          aligned: found,
          gap: found ? undefined : `Required technology ${tech} not found in stack`,
          remediation: found ? undefined : `Add ${tech} to technology stack`
        });
      }
    }

    // Regulatory constraints
    if (greenPaperConstraints.regulatory?.length) {
      for (const reg of greenPaperConstraints.regulatory) {
        checks.push({
          aspect: 'Regulatory Constraint',
          source: reg,
          architectureElement: 'Compliance',
          aligned: specification.qualityRequirements.some(q =>
            q.requirement.toLowerCase().includes(reg.toLowerCase())
          ),
          gap: `Ensure ${reg} compliance is addressed`,
          remediation: `Add explicit compliance measures for ${reg}`
        });
      }
    }
  }

  return checks;
}

// ============================================================================
// TRADE-OFF ANALYSIS
// ============================================================================

function analyzeTradeOffs(specification: SpecificationResult): TradeOffAnalysis[] {
  const tradeOffs: TradeOffAnalysis[] = [];

  // Analyze architecture pattern trade-off
  if (specification.architecture.pattern.includes('MICROSERVICES')) {
    tradeOffs.push({
      category: TradeOffCategory.SCALABILITY_VS_SIMPLICITY,
      description: 'Choice between microservices and monolithic architecture',
      optionA: {
        name: 'Microservices',
        pros: ['Independent scaling', 'Technology flexibility', 'Team autonomy'],
        cons: ['Operational complexity', 'Network latency', 'Data consistency challenges']
      },
      optionB: {
        name: 'Monolith',
        pros: ['Simple deployment', 'Easy debugging', 'No network overhead'],
        cons: ['Limited scaling', 'Technology lock-in', 'Larger deployments']
      },
      chosenOption: 'A',
      rationale: 'Microservices chosen to support scalability requirements and team independence'
    });
  }

  // Analyze database choice trade-off
  const hasNoSQL = specification.architecture.technologies.database?.some(db =>
    ['MongoDB', 'DynamoDB', 'Cassandra'].includes(db)
  );

  if (hasNoSQL) {
    tradeOffs.push({
      category: TradeOffCategory.CONSISTENCY_VS_AVAILABILITY,
      description: 'CAP theorem trade-off in database selection',
      optionA: {
        name: 'NoSQL (AP)',
        pros: ['High availability', 'Horizontal scaling', 'Flexible schema'],
        cons: ['Eventual consistency', 'Limited joins', 'Complex queries harder']
      },
      optionB: {
        name: 'SQL (CP)',
        pros: ['ACID transactions', 'Strong consistency', 'Complex queries'],
        cons: ['Vertical scaling', 'Schema changes harder', 'Single point of failure']
      },
      chosenOption: 'A',
      rationale: 'NoSQL chosen for scalability and availability over strict consistency'
    });
  }

  // Analyze caching trade-off
  if ((specification.architecture.technologies.cache?.length ?? 0) > 0) {
    tradeOffs.push({
      category: TradeOffCategory.PERFORMANCE_VS_COST,
      description: 'Adding caching layer for performance',
      optionA: {
        name: 'With Caching',
        pros: ['Faster response times', 'Reduced database load', 'Better UX'],
        cons: ['Additional infrastructure', 'Cache invalidation complexity', 'Memory costs']
      },
      optionB: {
        name: 'Without Caching',
        pros: ['Simpler architecture', 'Always fresh data', 'Lower costs'],
        cons: ['Slower responses', 'Higher database load', 'Scaling issues']
      },
      chosenOption: 'A',
      rationale: 'Caching added to meet performance requirements despite added complexity'
    });
  }

  return tradeOffs;
}

// ============================================================================
// ADR GENERATION
// ============================================================================

function generateADRs(
  specification: SpecificationResult,
  tradeOffs: TradeOffAnalysis[]
): ArchitectureDecisionRecord[] {
  const adrs: ArchitectureDecisionRecord[] = [];
  let adrId = 1;

  // Generate ADR for architecture pattern
  adrs.push({
    id: `ADR-${String(adrId++).padStart(3, '0')}`,
    title: `Use ${specification.architecture.pattern} Architecture`,
    status: 'accepted',
    context: `The system requires a scalable, maintainable architecture that supports the identified ${specification.components.length} components.`,
    decision: `We will use the ${specification.architecture.pattern} pattern for the system architecture.`,
    consequences: [
      `Components will be organized according to ${specification.architecture.pattern} principles`,
      'Clear separation of concerns between layers/services',
      specification.architecture.layers
        ? `Layers: ${specification.architecture.layers.join(' -> ')}`
        : 'Services will communicate via defined interfaces'
    ],
    date: new Date().toISOString().split('T')[0]
  });

  // Generate ADR for each major technology choice
  const techStack = specification.architecture.technologies;

  if (techStack.backend?.length) {
    adrs.push({
      id: `ADR-${String(adrId++).padStart(3, '0')}`,
      title: `Use ${techStack.backend.join(', ')} for Backend`,
      status: 'accepted',
      context: 'Backend technology selection for API and business logic implementation.',
      decision: `We will use ${techStack.backend.join(' with ')} for backend development.`,
      consequences: [
        `Team must have ${techStack.backend.join('/')} expertise`,
        'Consistent technology across backend services',
        'Access to ecosystem of libraries and tools'
      ],
      date: new Date().toISOString().split('T')[0]
    });
  }

  if (techStack.database?.length) {
    adrs.push({
      id: `ADR-${String(adrId++).padStart(3, '0')}`,
      title: `Use ${techStack.database.join(', ')} for Data Storage`,
      status: 'accepted',
      context: 'Database selection for application data persistence.',
      decision: `We will use ${techStack.database[0]} as primary database.`,
      consequences: [
        'Data model designed for chosen database paradigm',
        'Migration tooling selected accordingly',
        techStack.database.length > 1
          ? `Additional databases (${techStack.database.slice(1).join(', ')}) for specific use cases`
          : 'Single database simplifies operations'
      ],
      date: new Date().toISOString().split('T')[0]
    });
  }

  // Generate ADRs from trade-offs
  for (const tradeOff of tradeOffs) {
    const chosen = tradeOff.chosenOption === 'A' ? tradeOff.optionA : tradeOff.optionB;
    adrs.push({
      id: `ADR-${String(adrId++).padStart(3, '0')}`,
      title: `Choose ${chosen.name} for ${tradeOff.category.replace(/_/g, ' ')}`,
      status: 'accepted',
      context: tradeOff.description,
      decision: `We will use ${chosen.name}. ${tradeOff.rationale}`,
      consequences: [
        ...chosen.pros.map(p => `+ ${p}`),
        ...chosen.cons.map(c => `- ${c} (accepted trade-off)`)
      ],
      date: new Date().toISOString().split('T')[0]
    });
  }

  return adrs;
}

// ============================================================================
// RISK IDENTIFICATION
// ============================================================================

function identifyRisks(
  specification: SpecificationResult,
  teamContext?: ArchitectureReviewInput['teamContext']
): ArchitectureRisk[] {
  const risks: ArchitectureRisk[] = [];
  let riskId = 1;

  // Technology risk
  const techCount = [
    ...(specification.architecture.technologies.backend || []),
    ...(specification.architecture.technologies.frontend || []),
    ...(specification.architecture.technologies.database || [])
  ].length;

  if (techCount > 8) {
    risks.push({
      id: `RISK-${String(riskId++).padStart(3, '0')}`,
      title: 'Technology Stack Complexity',
      description: `Architecture uses ${techCount} different technologies which increases complexity and maintenance burden`,
      category: 'technical',
      impact: RiskLevel.MEDIUM,
      likelihood: RiskLevel.HIGH,
      mitigation: 'Document technology choices, ensure team training, consider consolidation',
      relatedElement: 'Technology Stack'
    });
  }

  // Team skill risk
  if (teamContext?.experience === 'junior') {
    risks.push({
      id: `RISK-${String(riskId++).padStart(3, '0')}`,
      title: 'Team Experience Gap',
      description: 'Junior team may struggle with complex architecture patterns',
      category: 'team',
      impact: RiskLevel.HIGH,
      likelihood: RiskLevel.MEDIUM,
      mitigation: 'Provide training, pair with senior developers, simplify where possible'
    });
  }

  // Microservices operational risk
  if (specification.architecture.pattern.includes('MICROSERVICES')) {
    risks.push({
      id: `RISK-${String(riskId++).padStart(3, '0')}`,
      title: 'Microservices Operational Complexity',
      description: 'Microservices require sophisticated deployment, monitoring, and debugging capabilities',
      category: 'operational',
      impact: RiskLevel.MEDIUM,
      likelihood: RiskLevel.HIGH,
      mitigation: 'Implement comprehensive monitoring, use container orchestration, establish runbooks',
      relatedElement: 'Architecture Pattern'
    });
  }

  // Component count risk
  if (specification.components.length > 10) {
    risks.push({
      id: `RISK-${String(riskId++).padStart(3, '0')}`,
      title: 'High Component Count',
      description: `${specification.components.length} components may be difficult to manage and coordinate`,
      category: 'technical',
      impact: RiskLevel.MEDIUM,
      likelihood: RiskLevel.MEDIUM,
      mitigation: 'Consider component consolidation, establish clear ownership, automate deployment',
      relatedElement: 'Components'
    });
  }

  // Security risk if no auth component
  const hasAuthComponent = specification.components.some(c =>
    c.name.toLowerCase().includes('auth')
  );
  if (!hasAuthComponent) {
    risks.push({
      id: `RISK-${String(riskId++).padStart(3, '0')}`,
      title: 'Missing Authentication Component',
      description: 'No dedicated authentication service identified in architecture',
      category: 'security',
      impact: RiskLevel.CRITICAL,
      likelihood: RiskLevel.HIGH,
      mitigation: 'Add authentication service or integrate with identity provider',
      relatedElement: 'Components'
    });
  }

  return risks;
}

// ============================================================================
// COST ESTIMATION
// ============================================================================

function estimateCosts(specification: SpecificationResult): CostEstimate[] {
  const costs: CostEstimate[] = [];

  // Infrastructure costs based on architecture
  const componentCount = specification.components.length;
  const isCloud = true; // Assume cloud deployment

  if (isCloud) {
    // Compute costs
    costs.push({
      category: 'infrastructure',
      item: 'Compute (Cloud instances/containers)',
      monthlyCost: `$${componentCount * 50}-${componentCount * 150}`,
      annualCost: `$${componentCount * 600}-${componentCount * 1800}`,
      assumptions: [
        `${componentCount} services running`,
        'Medium-sized instances',
        'Auto-scaling enabled'
      ],
      scalingNotes: 'Costs scale linearly with traffic'
    });

    // Database costs
    costs.push({
      category: 'infrastructure',
      item: 'Database (Managed service)',
      monthlyCost: '$100-$500',
      annualCost: '$1,200-$6,000',
      assumptions: [
        'Managed database service',
        'Multi-AZ deployment',
        '100GB-500GB storage'
      ],
      scalingNotes: 'Storage and IOPS drive cost increases'
    });

    // Caching costs
    if ((specification.architecture.technologies.cache?.length ?? 0) > 0) {
      costs.push({
        category: 'infrastructure',
        item: 'Caching (Redis/Memcached)',
        monthlyCost: '$50-$200',
        annualCost: '$600-$2,400',
        assumptions: [
          'Managed cache service',
          '1-4 nodes',
          '1-4GB memory per node'
        ]
      });
    }
  }

  // Development costs (rough estimate)
  costs.push({
    category: 'development',
    item: 'Initial Development',
    monthlyCost: 'N/A (one-time)',
    annualCost: `$${componentCount * 5000}-${componentCount * 15000}`,
    assumptions: [
      `${componentCount} components to build`,
      'Average complexity',
      'Includes testing and documentation'
    ]
  });

  // Maintenance costs
  costs.push({
    category: 'maintenance',
    item: 'Ongoing Maintenance',
    monthlyCost: `$${componentCount * 200}-${componentCount * 500}`,
    annualCost: `$${componentCount * 2400}-${componentCount * 6000}`,
    assumptions: [
      'Bug fixes and updates',
      'Dependency updates',
      'Performance tuning'
    ]
  });

  return costs;
}

function calculateTotalMonthlyCost(costs: CostEstimate[]): string {
  // This is a simplified calculation - would need proper parsing in production
  return '$500-$2,000 (estimated)';
}

// ============================================================================
// SCORING AND VERDICT
// ============================================================================

function calculateAlignmentScore(
  principleChecks: AlignmentCheck[],
  requirementChecks: AlignmentCheck[],
  constraintChecks: AlignmentCheck[]
): number {
  const allChecks = [...principleChecks, ...requirementChecks, ...constraintChecks];
  if (allChecks.length === 0) return 100;

  const alignedCount = allChecks.filter(c => c.aligned).length;
  return Math.round((alignedCount / allChecks.length) * 100);
}

function determineVerdict(
  alignmentScore: number, 
  risks: ArchitectureRisk[],
  alignmentChecks: AlignmentCheck[],
  config?: ArchitectureReviewConfig
): ReviewVerdict {
  // Default config: 95% threshold for auto-approval
  const effectiveConfig: ArchitectureReviewConfig = {
    minAlignmentScore: config?.minAlignmentScore ?? 95,
    maxCriticalRisks: config?.maxCriticalRisks ?? 0,
    maxHighRisks: config?.maxHighRisks ?? 2,
    alwaysRequireHumanApproval: config?.alwaysRequireHumanApproval ?? false,
    autoRejectBelowScore: config?.autoRejectBelowScore ?? 40
  };

  const criticalRisks = risks.filter(r => r.impact === RiskLevel.CRITICAL).length;
  const highRisks = risks.filter(r => r.impact === RiskLevel.HIGH).length;
  
  // Check for high-importance alignment gaps - these are blocking factors
  const highImportanceGaps = alignmentChecks.filter(
    c => !c.aligned && c.gapImportance === 'high'
  ).length;

  // Always require human approval if configured
  if (effectiveConfig.alwaysRequireHumanApproval) {
    return ReviewVerdict.NEEDS_HUMAN_APPROVAL;
  }

  // Auto-reject below threshold
  if (alignmentScore < effectiveConfig.autoRejectBelowScore) {
    return ReviewVerdict.REJECTED;
  }

  // HIGH IMPORTANCE GAPS = BLOCKING FACTOR - requires human approval
  // "er mogen geen hoog belangrijke verschillen zijn"
  if (highImportanceGaps > 0) {
    return ReviewVerdict.NEEDS_HUMAN_APPROVAL;
  }

  // Critical risks always need revision
  if (criticalRisks > effectiveConfig.maxCriticalRisks) {
    return ReviewVerdict.NEEDS_REVISION;
  }

  // Too many high risks need human approval
  if (highRisks > effectiveConfig.maxHighRisks) {
    return ReviewVerdict.NEEDS_HUMAN_APPROVAL;
  }

  // >= 95% (configurable): Auto-approved
  if (alignmentScore >= effectiveConfig.minAlignmentScore && highRisks <= effectiveConfig.maxHighRisks) {
    return ReviewVerdict.APPROVED;
  }

  // 80-94%: Approved with conditions (minor issues only - medium/low gaps allowed)
  if (alignmentScore >= 80 && alignmentScore < effectiveConfig.minAlignmentScore) {
    return ReviewVerdict.APPROVED_WITH_CONDITIONS;
  }

  // Below 80%: Human must decide - this is a blocking factor
  // "score of alignment moet boven 95% liggen anders blocking factor en moet human worden ingeschakeld"
  return ReviewVerdict.NEEDS_HUMAN_APPROVAL;
}


/**
 * Generate human approval request when verdict is NEEDS_HUMAN_APPROVAL
 * This is triggered when:
 * - Alignment score < 95%
 * - Any high-importance gaps exist
 * - Too many high risks
 */
function generateHumanApprovalRequest(
  reviewResult: ArchitectureReviewResult,
  alignmentChecks: AlignmentCheck[],
  reason: string
): HumanApprovalRequest {
  // Identify decisions required from human
  const decisionsRequired: HumanApprovalRequest['decisionsRequired'] = [];

  // Add alignment gap decisions
  const highGaps = alignmentChecks.filter(c => !c.aligned && c.gapImportance === 'high');
  highGaps.forEach((gap, index) => {
    decisionsRequired.push({
      id: `gap-${index + 1}`,
      category: 'alignment_gap',
      title: `High-Importance Gap: ${gap.aspect}`,
      description: `${gap.gap || 'Alignment not achieved'}. Source: ${gap.source}`,
      options: [
        'Accept gap and proceed',
        'Require remediation before proceeding',
        'Modify architecture to address gap',
        'Remove requirement from scope'
      ],
      recommendation: gap.remediation || 'Consider addressing this gap before proceeding'
    });
  });

  // Add risk decisions
  const criticalRisks = reviewResult.risks.filter(r => r.impact === RiskLevel.CRITICAL);
  criticalRisks.forEach((risk, index) => {
    decisionsRequired.push({
      id: `risk-${index + 1}`,
      category: 'risk',
      title: `Critical Risk: ${risk.title}`,
      description: risk.description,
      options: [
        'Accept risk and proceed',
        'Implement mitigation first',
        'Redesign to eliminate risk',
        'Defer feature to reduce risk'
      ],
      recommendation: risk.mitigation || 'Consider mitigation before proceeding'
    });
  });

  // Add trade-off decisions for all identified trade-offs
  // Trade-offs always require human review as they involve strategic choices
  reviewResult.tradeOffs.forEach((tradeOff, index) => {
    decisionsRequired.push({
      id: `tradeoff-${index + 1}`,
      category: 'trade_off',
      title: `Trade-off: ${tradeOff.category}`,
      description: `${tradeOff.description}. Chosen: Option ${tradeOff.chosenOption} (${tradeOff.chosenOption === 'A' ? tradeOff.optionA.name : tradeOff.optionB.name})`,
      options: [
        `Accept Option ${tradeOff.chosenOption}: ${tradeOff.chosenOption === 'A' ? tradeOff.optionA.name : tradeOff.optionB.name}`,
        `Switch to Option ${tradeOff.chosenOption === 'A' ? 'B' : 'A'}: ${tradeOff.chosenOption === 'A' ? tradeOff.optionB.name : tradeOff.optionA.name}`,
        'Defer decision pending more analysis'
      ],
      recommendation: tradeOff.rationale
    });
  });

  // Add cost decisions if budget is exceeded
  // monthlyCost is a string like "€1000" or "1000", parse to number
  const totalCost: number = reviewResult.costEstimates.reduce(
    (sum: number, c) => {
      const cost = parseFloat(c.monthlyCost.replace(/[^0-9.]/g, '')) || 0;
      return sum + cost;
    },
    0
  );
  if (totalCost > 10000) { // Example threshold
    decisionsRequired.push({
      id: 'cost-1',
      category: 'cost',
      title: 'Total Monthly Cost Review',
      description: `Estimated monthly cost: €${totalCost.toLocaleString()}`,
      options: [
        'Approve budget as estimated',
        'Require cost reduction analysis',
        'Reduce scope to fit budget'
      ],
      recommendation: 'Review cost breakdown and confirm budget allocation'
    });
  }

  return {
    requestId: `har-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    reviewResult,
    reason,
    decisionsRequired,
    status: 'pending'
  };
}

// ============================================================================
// RECOMMENDATIONS AND SUMMARY
// ============================================================================

function generateRecommendations(
  principleChecks: AlignmentCheck[],
  requirementChecks: AlignmentCheck[],
  constraintChecks: AlignmentCheck[],
  risks: ArchitectureRisk[]
): ArchitectureReviewResult['recommendations'] {
  const recommendations: ArchitectureReviewResult['recommendations'] = [];

  // Recommendations from gaps
  const allChecks = [...principleChecks, ...requirementChecks, ...constraintChecks];
  const gaps = allChecks.filter(c => !c.aligned && c.remediation);

  for (const gap of gaps.slice(0, 5)) { // Top 5 gaps
    recommendations.push({
      priority: Priority.HIGH,
      category: gap.aspect,
      title: `Address ${gap.aspect} Gap`,
      description: gap.remediation || gap.gap || 'Address alignment gap',
      impact: 'Improves alignment with project requirements'
    });
  }

  // Recommendations from risks
  for (const risk of risks.filter(r => r.impact === RiskLevel.CRITICAL || r.impact === RiskLevel.HIGH)) {
    recommendations.push({
      priority: risk.impact === RiskLevel.CRITICAL ? Priority.CRITICAL : Priority.HIGH,
      category: 'Risk Mitigation',
      title: `Mitigate: ${risk.title}`,
      description: risk.mitigation,
      impact: `Reduces ${risk.category} risk`
    });
  }

  return recommendations;
}

function extractConditions(
  recommendations: ArchitectureReviewResult['recommendations']
): string[] {
  return recommendations
    .filter(r => r.priority === Priority.HIGH || r.priority === Priority.CRITICAL)
    .map(r => r.description);
}

function extractRequiredRevisions(
  principleChecks: AlignmentCheck[],
  requirementChecks: AlignmentCheck[],
  constraintChecks: AlignmentCheck[]
): string[] {
  const allChecks = [...principleChecks, ...requirementChecks, ...constraintChecks];
  return allChecks
    .filter(c => !c.aligned)
    .map(c => c.remediation || `Address: ${c.source}`);
}

function generateExecutiveSummary(
  verdict: ReviewVerdict,
  alignmentScore: number,
  adrCount: number,
  riskCount: number,
  costs: CostEstimate[]
): string {
  const verdictText = {
    [ReviewVerdict.APPROVED]: 'Architecture is approved and ready for implementation.',
    [ReviewVerdict.APPROVED_WITH_CONDITIONS]: 'Architecture is approved with conditions that must be addressed.',
    [ReviewVerdict.NEEDS_REVISION]: 'Architecture requires revision before approval.',
    [ReviewVerdict.REJECTED]: 'Architecture does not meet requirements and must be redesigned.'
  };

  return `
## Executive Summary

**Verdict**: ${verdict}

${verdictText[verdict]}

### Key Metrics
- **Alignment Score**: ${alignmentScore}% alignment with project requirements
- **Architecture Decisions**: ${adrCount} ADRs documented
- **Identified Risks**: ${riskCount} risks requiring attention
- **Estimated Monthly Cost**: ${calculateTotalMonthlyCost(costs)}

### Recommendation
${verdict === ReviewVerdict.APPROVED
    ? 'Proceed to task generation phase.'
    : verdict === ReviewVerdict.APPROVED_WITH_CONDITIONS
      ? 'Address conditions before proceeding to implementation.'
      : 'Review alignment gaps and revise architecture accordingly.'}
`.trim();
}

// ============================================================================
// OUTPUT FORMATTING
// ============================================================================

/**
 * Format architecture review as Markdown
 */
export function formatArchitectureReviewMarkdown(review: ArchitectureReviewResult): string {
  let md = '# Architecture Review Report\n\n';
  md += `**Reviewed**: ${review.metadata.reviewedAt.toISOString()}\n`;
  md += `**By**: ${review.metadata.reviewedBy}\n`;
  md += `**Specification Version**: ${review.metadata.specificationVersion}\n\n`;
  md += '---\n\n';

  // Executive Summary
  md += review.executiveSummary + '\n\n';
  md += '---\n\n';

  // Alignment Checks
  md += '## Alignment Analysis\n\n';

  md += '### Principle Alignment\n\n';
  md += '| Principle | Architecture Element | Aligned | Notes |\n';
  md += '|-----------|---------------------|---------|-------|\n';
  for (const check of review.alignmentChecks.principles) {
    md += `| ${check.source.substring(0, 30)}... | ${check.architectureElement} | ${check.aligned ? '✅' : '❌'} | ${check.gap || '-'} |\n`;
  }
  md += '\n';

  // ADRs
  md += '## Architecture Decision Records\n\n';
  for (const adr of review.adrs) {
    md += `### ${adr.id}: ${adr.title}\n\n`;
    md += `**Status**: ${adr.status} | **Date**: ${adr.date}\n\n`;
    md += `**Context**: ${adr.context}\n\n`;
    md += `**Decision**: ${adr.decision}\n\n`;
    md += '**Consequences**:\n';
    for (const c of adr.consequences) {
      md += `- ${c}\n`;
    }
    md += '\n---\n\n';
  }

  // Risks
  md += '## Risk Assessment\n\n';
  md += '| Risk | Category | Impact | Likelihood | Mitigation |\n';
  md += '|------|----------|--------|------------|------------|\n';
  for (const risk of review.risks) {
    md += `| ${risk.title} | ${risk.category} | ${risk.impact} | ${risk.likelihood} | ${risk.mitigation.substring(0, 40)}... |\n`;
  }
  md += '\n';

  // Cost Estimates
  md += '## Cost Estimates\n\n';
  md += '| Category | Item | Monthly | Annual |\n';
  md += '|----------|------|---------|--------|\n';
  for (const cost of review.costEstimates) {
    md += `| ${cost.category} | ${cost.item} | ${cost.monthlyCost} | ${cost.annualCost} |\n`;
  }
  md += `\n**Total Estimated Monthly Cost**: ${review.totalMonthlyCost}\n\n`;

  // Recommendations
  if (review.recommendations.length > 0) {
    md += '## Recommendations\n\n';
    for (const rec of review.recommendations) {
      md += `### [${rec.priority}] ${rec.title}\n\n`;
      md += `${rec.description}\n\n`;
      md += `**Impact**: ${rec.impact}\n\n`;
    }
  }

  md += '---\n\n';
  md += `*Generated by Architecture Review - ${review.metadata.version}*\n`;

  return md;
}
