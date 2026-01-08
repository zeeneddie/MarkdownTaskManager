/**
 * Pattern Library - Seed Patterns for Self-Navigating Agents
 *
 * Contains initial successful patterns that agents can learn from.
 * Part of AgentEvolver Phase B (Week 20).
 *
 * Pattern Categories:
 * - Architecture patterns (Felix)
 * - Maintenance patterns (Marcus)
 * - Quality patterns (Quinn)
 * - Debugging patterns (Betty)
 * - Estimation patterns (Eliza)
 * - Testing patterns (Tessa)
 * - Migration patterns (Miguel)
 * - Documentation patterns (Diana)
 * - Product patterns (Peter)
 * - Planning patterns (Paul)
 *
 * @author Claude Code (Week 20 Day 3)
 * @date 2025-11-22
 */

// ============================================================================
// Types
// ============================================================================

export interface Pattern {
  id: string;
  name: string;
  category: PatternCategory;
  description: string;
  applicableWorkTypes: string[];
  applicableContexts: string[];
  steps: string[];
  preconditions: string[];
  postconditions: string[];
  antiPatterns: string[];
  successRate: number;
  usageCount: number;
  createdBy: string;
  tags: string[];
}

export type PatternCategory =
  | 'architecture'
  | 'maintenance'
  | 'quality'
  | 'debugging'
  | 'estimation'
  | 'testing'
  | 'migration'
  | 'documentation'
  | 'product'
  | 'planning';

// ============================================================================
// Architecture Patterns (Felix)
// ============================================================================

const architecturePatterns: Pattern[] = [
  {
    id: 'arch-001',
    name: 'Layered Architecture Pattern',
    category: 'architecture',
    description: 'Organize code into presentation, business, and data layers for clear separation of concerns',
    applicableWorkTypes: ['NEW_FEATURE', 'ENHANCEMENT'],
    applicableContexts: ['web_application', 'api_service', 'enterprise'],
    steps: [
      '1. Define layer boundaries (presentation, business, data)',
      '2. Create interfaces between layers',
      '3. Implement dependency injection',
      '4. Ensure unidirectional dependencies (top to bottom)',
      '5. Add anti-corruption layers for external systems'
    ],
    preconditions: ['Clear domain model', 'Identified external dependencies'],
    postconditions: ['Testable layers', 'Swappable implementations'],
    antiPatterns: ['Circular dependencies', 'Business logic in presentation layer'],
    successRate: 0.92,
    usageCount: 47,
    createdBy: 'felix',
    tags: ['architecture', 'layers', 'separation-of-concerns']
  },
  {
    id: 'arch-002',
    name: 'Repository Pattern',
    category: 'architecture',
    description: 'Abstract data access behind repository interfaces for testability and flexibility',
    applicableWorkTypes: ['NEW_FEATURE', 'MAINTENANCE'],
    applicableContexts: ['database', 'data_access', 'crud'],
    steps: [
      '1. Define repository interface with CRUD operations',
      '2. Create concrete implementation for database',
      '3. Add unit of work pattern for transactions',
      '4. Implement specification pattern for queries',
      '5. Create mock repository for testing'
    ],
    preconditions: ['Database schema defined', 'Entity models created'],
    postconditions: ['Testable data access', 'Database-agnostic code'],
    antiPatterns: ['Repository doing business logic', 'Leaking ORM abstractions'],
    successRate: 0.89,
    usageCount: 63,
    createdBy: 'felix',
    tags: ['repository', 'data-access', 'abstraction']
  },
  {
    id: 'arch-003',
    name: 'API Gateway Pattern',
    category: 'architecture',
    description: 'Single entry point for microservices with routing, auth, and rate limiting',
    applicableWorkTypes: ['NEW_FEATURE', 'MIGRATION'],
    applicableContexts: ['microservices', 'api', 'distributed'],
    steps: [
      '1. Design API routes and versioning',
      '2. Implement authentication middleware',
      '3. Add rate limiting per client',
      '4. Configure request routing to services',
      '5. Add request/response logging',
      '6. Implement circuit breaker for resilience'
    ],
    preconditions: ['Multiple backend services', 'Authentication requirements'],
    postconditions: ['Unified API surface', 'Centralized security'],
    antiPatterns: ['Gateway doing business logic', 'Single point of failure'],
    successRate: 0.85,
    usageCount: 28,
    createdBy: 'felix',
    tags: ['api', 'gateway', 'microservices', 'security']
  }
];

// ============================================================================
// Maintenance Patterns (Marcus)
// ============================================================================

const maintenancePatterns: Pattern[] = [
  {
    id: 'maint-001',
    name: 'Incremental Refactoring Pattern',
    category: 'maintenance',
    description: 'Refactor code incrementally with continuous testing to avoid big-bang rewrites',
    applicableWorkTypes: ['MAINTENANCE', 'QUALITY_IMPROVEMENT'],
    applicableContexts: ['legacy_code', 'tech_debt', 'refactoring'],
    steps: [
      '1. Characterize existing behavior with tests',
      '2. Identify smallest refactorable unit',
      '3. Apply single refactoring step',
      '4. Run tests to verify behavior preserved',
      '5. Commit and repeat',
      '6. Track technical debt metrics'
    ],
    preconditions: ['Existing test coverage', 'Version control'],
    postconditions: ['Improved code quality', 'Preserved functionality'],
    antiPatterns: ['Big-bang rewrite', 'Refactoring without tests'],
    successRate: 0.94,
    usageCount: 82,
    createdBy: 'marcus',
    tags: ['refactoring', 'incremental', 'safe']
  },
  {
    id: 'maint-002',
    name: 'Dependency Update Strategy',
    category: 'maintenance',
    description: 'Safely update dependencies with testing and rollback plans',
    applicableWorkTypes: ['MAINTENANCE'],
    applicableContexts: ['dependencies', 'security', 'updates'],
    steps: [
      '1. Audit current dependencies for vulnerabilities',
      '2. Group updates by risk level (patch/minor/major)',
      '3. Update patch versions first with tests',
      '4. Update minor versions with integration tests',
      '5. Update major versions with migration plan',
      '6. Document breaking changes and workarounds'
    ],
    preconditions: ['Dependency lock file', 'CI/CD pipeline'],
    postconditions: ['Updated dependencies', 'No regressions'],
    antiPatterns: ['Update all at once', 'Ignore security advisories'],
    successRate: 0.91,
    usageCount: 56,
    createdBy: 'marcus',
    tags: ['dependencies', 'updates', 'security']
  },
  {
    id: 'maint-003',
    name: 'Technical Debt Triage',
    category: 'maintenance',
    description: 'Prioritize technical debt based on impact and effort',
    applicableWorkTypes: ['MAINTENANCE', 'QUALITY_IMPROVEMENT'],
    applicableContexts: ['tech_debt', 'prioritization', 'planning'],
    steps: [
      '1. Inventory all technical debt items',
      '2. Score impact (1-5) for each item',
      '3. Score effort (1-5) for each item',
      '4. Calculate priority = impact / effort',
      '5. Group by theme (security, performance, maintainability)',
      '6. Schedule high-priority items in sprints'
    ],
    preconditions: ['Technical debt backlog', 'Team capacity'],
    postconditions: ['Prioritized debt list', 'Sprint commitments'],
    antiPatterns: ['Ignoring debt', 'Only fixing easy items'],
    successRate: 0.88,
    usageCount: 34,
    createdBy: 'marcus',
    tags: ['tech-debt', 'prioritization', 'planning']
  }
];

// ============================================================================
// Quality Patterns (Quinn)
// ============================================================================

const qualityPatterns: Pattern[] = [
  {
    id: 'qual-001',
    name: 'Security-First Review',
    category: 'quality',
    description: 'Review code with security as primary focus using OWASP guidelines',
    applicableWorkTypes: ['QUALITY_AUDIT', 'NEW_FEATURE'],
    applicableContexts: ['security', 'code_review', 'audit'],
    steps: [
      '1. Check for injection vulnerabilities (SQL, XSS, etc)',
      '2. Verify authentication and authorization',
      '3. Review sensitive data handling',
      '4. Check for security misconfigurations',
      '5. Verify cryptographic implementations',
      '6. Check for known vulnerable dependencies'
    ],
    preconditions: ['Code access', 'OWASP checklist'],
    postconditions: ['Security report', 'Remediation plan'],
    antiPatterns: ['Security as afterthought', 'Ignoring warnings'],
    successRate: 0.93,
    usageCount: 71,
    createdBy: 'quinn',
    tags: ['security', 'owasp', 'audit']
  },
  {
    id: 'qual-002',
    name: 'Code Quality Gates',
    category: 'quality',
    description: 'Automated quality gates that block deployments on violations',
    applicableWorkTypes: ['QUALITY_AUDIT', 'QUALITY_IMPROVEMENT'],
    applicableContexts: ['ci_cd', 'automation', 'quality'],
    steps: [
      '1. Define quality thresholds (coverage, complexity, etc)',
      '2. Configure linting rules',
      '3. Set up automated testing',
      '4. Configure static analysis',
      '5. Implement blocking gates in CI/CD',
      '6. Create bypass process for emergencies'
    ],
    preconditions: ['CI/CD pipeline', 'Quality tools'],
    postconditions: ['Automated quality checks', 'Consistent standards'],
    antiPatterns: ['Too strict gates', 'Ignoring gate results'],
    successRate: 0.90,
    usageCount: 45,
    createdBy: 'quinn',
    tags: ['quality', 'automation', 'ci-cd']
  }
];

// ============================================================================
// Debugging Patterns (Betty)
// ============================================================================

const debuggingPatterns: Pattern[] = [
  {
    id: 'debug-001',
    name: 'Binary Search Debugging',
    category: 'debugging',
    description: 'Find bugs by systematically bisecting code changes',
    applicableWorkTypes: ['BUG'],
    applicableContexts: ['regression', 'intermittent', 'debugging'],
    steps: [
      '1. Identify last known working version',
      '2. Identify first broken version',
      '3. Check middle commit between them',
      '4. Narrow down based on result',
      '5. Repeat until bug-introducing commit found',
      '6. Analyze the change for root cause'
    ],
    preconditions: ['Version history', 'Reproducible bug'],
    postconditions: ['Root cause identified', 'Fix implemented'],
    antiPatterns: ['Random debugging', 'Ignoring version history'],
    successRate: 0.87,
    usageCount: 39,
    createdBy: 'betty',
    tags: ['debugging', 'bisect', 'regression']
  },
  {
    id: 'debug-002',
    name: 'Rubber Duck Debugging',
    category: 'debugging',
    description: 'Explain code line by line to find logic errors',
    applicableWorkTypes: ['BUG'],
    applicableContexts: ['logic_error', 'complex_code', 'debugging'],
    steps: [
      '1. Find the relevant code section',
      '2. Explain each line\'s purpose aloud',
      '3. State your assumptions explicitly',
      '4. Question each assumption',
      '5. Identify discrepancies',
      '6. Test your hypothesis'
    ],
    preconditions: ['Code access', 'Understanding of expected behavior'],
    postconditions: ['Bug identified', 'Assumptions validated'],
    antiPatterns: ['Skimming code', 'Making assumptions'],
    successRate: 0.82,
    usageCount: 52,
    createdBy: 'betty',
    tags: ['debugging', 'logic', 'analysis']
  }
];

// ============================================================================
// Testing Patterns (Tessa)
// ============================================================================

const testingPatterns: Pattern[] = [
  {
    id: 'test-001',
    name: 'Test Pyramid Strategy',
    category: 'testing',
    description: 'Balance unit, integration, and E2E tests for optimal coverage and speed',
    applicableWorkTypes: ['TESTING', 'NEW_FEATURE'],
    applicableContexts: ['testing', 'strategy', 'automation'],
    steps: [
      '1. Start with unit tests (70% of tests)',
      '2. Add integration tests (20% of tests)',
      '3. Add E2E tests (10% of tests)',
      '4. Measure coverage and execution time',
      '5. Adjust ratios based on failure patterns',
      '6. Optimize slow tests'
    ],
    preconditions: ['Test framework', 'CI/CD pipeline'],
    postconditions: ['Balanced test suite', 'Fast feedback'],
    antiPatterns: ['Ice cream cone (too many E2E)', 'No integration tests'],
    successRate: 0.91,
    usageCount: 67,
    createdBy: 'tessa',
    tags: ['testing', 'pyramid', 'strategy']
  },
  {
    id: 'test-002',
    name: 'Behavior-Driven Testing',
    category: 'testing',
    description: 'Write tests in Given-When-Then format for clarity',
    applicableWorkTypes: ['TESTING', 'NEW_FEATURE'],
    applicableContexts: ['bdd', 'acceptance', 'testing'],
    steps: [
      '1. Define scenarios in Given-When-Then format',
      '2. Implement step definitions',
      '3. Run tests and capture results',
      '4. Generate living documentation',
      '5. Review with stakeholders',
      '6. Maintain scenario repository'
    ],
    preconditions: ['User stories', 'Acceptance criteria'],
    postconditions: ['Executable specifications', 'Documentation'],
    antiPatterns: ['Technical scenarios', 'Overly complex steps'],
    successRate: 0.86,
    usageCount: 41,
    createdBy: 'tessa',
    tags: ['bdd', 'acceptance', 'documentation']
  }
];

// ============================================================================
// Migration Patterns (Miguel)
// ============================================================================

const migrationPatterns: Pattern[] = [
  {
    id: 'migrate-001',
    name: 'Strangler Fig Pattern',
    category: 'migration',
    description: 'Gradually replace legacy system by routing traffic to new system',
    applicableWorkTypes: ['MIGRATION'],
    applicableContexts: ['legacy', 'migration', 'modernization'],
    steps: [
      '1. Identify migration boundaries',
      '2. Create facade over legacy system',
      '3. Build new implementation behind facade',
      '4. Route traffic gradually to new system',
      '5. Monitor and compare results',
      '6. Remove legacy code when 100% migrated'
    ],
    preconditions: ['Legacy system documentation', 'Routing capability'],
    postconditions: ['Migrated functionality', 'Zero downtime'],
    antiPatterns: ['Big bang migration', 'No comparison testing'],
    successRate: 0.88,
    usageCount: 23,
    createdBy: 'miguel',
    tags: ['migration', 'strangler', 'legacy']
  },
  {
    id: 'migrate-002',
    name: 'Database Migration Strategy',
    category: 'migration',
    description: 'Safely migrate database schema and data with rollback capability',
    applicableWorkTypes: ['MIGRATION'],
    applicableContexts: ['database', 'schema', 'data'],
    steps: [
      '1. Backup current database',
      '2. Create migration scripts (up and down)',
      '3. Test migration on copy of production data',
      '4. Plan maintenance window',
      '5. Execute migration with monitoring',
      '6. Verify data integrity'
    ],
    preconditions: ['Database access', 'Backup capability'],
    postconditions: ['Migrated schema', 'Data integrity verified'],
    antiPatterns: ['No rollback plan', 'Skipping integrity checks'],
    successRate: 0.92,
    usageCount: 37,
    createdBy: 'miguel',
    tags: ['database', 'migration', 'schema']
  }
];

// ============================================================================
// Documentation Patterns (Diana)
// ============================================================================

const documentationPatterns: Pattern[] = [
  {
    id: 'doc-001',
    name: 'API Documentation Pattern',
    category: 'documentation',
    description: 'Document APIs with examples, schemas, and error codes',
    applicableWorkTypes: ['PROJECT_DEFINITION', 'NEW_FEATURE'],
    applicableContexts: ['api', 'documentation', 'openapi'],
    steps: [
      '1. Document all endpoints with methods',
      '2. Add request/response schemas',
      '3. Include authentication requirements',
      '4. Add example requests and responses',
      '5. Document error codes and handling',
      '6. Generate interactive documentation'
    ],
    preconditions: ['API specification', 'Schema definitions'],
    postconditions: ['Complete API docs', 'Interactive playground'],
    antiPatterns: ['Missing examples', 'Outdated documentation'],
    successRate: 0.89,
    usageCount: 54,
    createdBy: 'diana',
    tags: ['api', 'documentation', 'openapi']
  }
];

// ============================================================================
// Product Patterns (Peter)
// ============================================================================

const productPatterns: Pattern[] = [
  {
    id: 'prod-001',
    name: 'User Story Mapping',
    category: 'product',
    description: 'Map user journey to identify features and priorities',
    applicableWorkTypes: ['PROJECT_DEFINITION'],
    applicableContexts: ['requirements', 'planning', 'user_stories'],
    steps: [
      '1. Identify user personas',
      '2. Map user activities (backbone)',
      '3. Detail user tasks under activities',
      '4. Slice into releases horizontally',
      '5. Prioritize by business value',
      '6. Create user stories from tasks'
    ],
    preconditions: ['User research', 'Business goals'],
    postconditions: ['Story map', 'Release plan'],
    antiPatterns: ['Feature-first thinking', 'Ignoring user journey'],
    successRate: 0.87,
    usageCount: 29,
    createdBy: 'peter',
    tags: ['user-stories', 'mapping', 'planning']
  }
];

// ============================================================================
// Planning Patterns (Paul)
// ============================================================================

const planningPatterns: Pattern[] = [
  {
    id: 'plan-001',
    name: 'Sprint Planning Pattern',
    category: 'planning',
    description: 'Plan sprint with capacity-based story selection',
    applicableWorkTypes: ['PROJECT_DEFINITION'],
    applicableContexts: ['sprint', 'planning', 'scrum'],
    steps: [
      '1. Review and refine backlog',
      '2. Calculate team capacity',
      '3. Select stories within capacity',
      '4. Break stories into tasks',
      '5. Identify dependencies and risks',
      '6. Commit to sprint goal'
    ],
    preconditions: ['Refined backlog', 'Team availability'],
    postconditions: ['Sprint backlog', 'Sprint goal'],
    antiPatterns: ['Overcommitment', 'Ignoring capacity'],
    successRate: 0.90,
    usageCount: 48,
    createdBy: 'paul',
    tags: ['sprint', 'planning', 'scrum']
  }
];

// ============================================================================
// Pattern Library Service
// ============================================================================

export class PatternLibrary {
  private patterns: Map<string, Pattern> = new Map();

  constructor() {
    this.loadSeedPatterns();
  }

  private loadSeedPatterns(): void {
    const allPatterns = [
      ...architecturePatterns,
      ...maintenancePatterns,
      ...qualityPatterns,
      ...debuggingPatterns,
      ...testingPatterns,
      ...migrationPatterns,
      ...documentationPatterns,
      ...productPatterns,
      ...planningPatterns
    ];

    for (const pattern of allPatterns) {
      this.patterns.set(pattern.id, pattern);
    }

    console.log(`[PatternLibrary] Loaded ${this.patterns.size} seed patterns`);
  }

  /**
   * Get patterns by category
   */
  getByCategory(category: PatternCategory): Pattern[] {
    return Array.from(this.patterns.values())
      .filter(p => p.category === category);
  }

  /**
   * Get patterns by work type
   */
  getByWorkType(workType: string): Pattern[] {
    return Array.from(this.patterns.values())
      .filter(p => p.applicableWorkTypes.includes(workType));
  }

  /**
   * Get patterns by context keywords
   */
  getByContext(context: string): Pattern[] {
    const contextLower = context.toLowerCase();
    return Array.from(this.patterns.values())
      .filter(p =>
        p.applicableContexts.some(c => c.toLowerCase().includes(contextLower)) ||
        p.tags.some(t => t.toLowerCase().includes(contextLower))
      );
  }

  /**
   * Search patterns by text
   */
  search(query: string): Pattern[] {
    const queryLower = query.toLowerCase();
    return Array.from(this.patterns.values())
      .filter(p =>
        p.name.toLowerCase().includes(queryLower) ||
        p.description.toLowerCase().includes(queryLower) ||
        p.tags.some(t => t.toLowerCase().includes(queryLower))
      )
      .sort((a, b) => b.successRate - a.successRate);
  }

  /**
   * Get top patterns by success rate
   */
  getTopPatterns(limit: number = 10): Pattern[] {
    return Array.from(this.patterns.values())
      .sort((a, b) => b.successRate - a.successRate)
      .slice(0, limit);
  }

  /**
   * Get pattern by ID
   */
  getById(id: string): Pattern | undefined {
    return this.patterns.get(id);
  }

  /**
   * Add new pattern (from agent learning)
   */
  addPattern(pattern: Pattern): void {
    this.patterns.set(pattern.id, pattern);
    console.log(`[PatternLibrary] Added pattern: ${pattern.name}`);
  }

  /**
   * Update pattern success rate
   */
  updateSuccessRate(patternId: string, success: boolean): void {
    const pattern = this.patterns.get(patternId);
    if (pattern) {
      const totalUses = pattern.usageCount + 1;
      const currentSuccesses = pattern.successRate * pattern.usageCount;
      const newSuccesses = currentSuccesses + (success ? 1 : 0);
      pattern.successRate = newSuccesses / totalUses;
      pattern.usageCount = totalUses;
    }
  }

  /**
   * Get all patterns
   */
  getAllPatterns(): Pattern[] {
    return Array.from(this.patterns.values());
  }

  /**
   * Get pattern statistics
   */
  getStatistics(): {
    total: number;
    byCategory: Record<string, number>;
    averageSuccessRate: number;
    totalUsage: number;
  } {
    const patterns = Array.from(this.patterns.values());
    const byCategory: Record<string, number> = {};

    for (const pattern of patterns) {
      byCategory[pattern.category] = (byCategory[pattern.category] || 0) + 1;
    }

    return {
      total: patterns.length,
      byCategory,
      averageSuccessRate: patterns.reduce((a, p) => a + p.successRate, 0) / patterns.length,
      totalUsage: patterns.reduce((a, p) => a + p.usageCount, 0)
    };
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

let libraryInstance: PatternLibrary | null = null;

export function getPatternLibrary(): PatternLibrary {
  if (!libraryInstance) {
    libraryInstance = new PatternLibrary();
  }
  return libraryInstance;
}

// ============================================================================
// Exports
// ============================================================================

export default {
  PatternLibrary,
  getPatternLibrary,
  architecturePatterns,
  maintenancePatterns,
  qualityPatterns,
  debuggingPatterns,
  testingPatterns,
  migrationPatterns,
  documentationPatterns,
  productPatterns,
  planningPatterns
};
