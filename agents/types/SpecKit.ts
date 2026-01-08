/**
 * Spec-Kit Workflow Types
 *
 * Type definitions for the specification-driven development workflow:
 * - Constitution: Business requirements → Project principles
 * - Specification: Constitution → Technical specification
 * - Tasks: Specification → Hierarchical tasks
 *
 * Week 8 Implementation
 */

// ============================================================================
// CONSTITUTION TYPES
// ============================================================================

/**
 * Priority levels for requirements, features, etc.
 */
export enum Priority {
  CRITICAL = 'CRITICAL',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW'
}

/**
 * Risk impact and likelihood levels
 */
export enum RiskLevel {
  CRITICAL = 'CRITICAL',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW'
}

/**
 * Principle categories for project constitution
 */
export enum PrincipleCategory {
  USER_EXPERIENCE = 'USER_EXPERIENCE',
  SECURITY = 'SECURITY',
  PERFORMANCE = 'PERFORMANCE',
  SCALABILITY = 'SCALABILITY',
  MAINTAINABILITY = 'MAINTAINABILITY',
  RELIABILITY = 'RELIABILITY',
  BUSINESS = 'BUSINESS',
  PROCESS = 'PROCESS'
}

/**
 * Requirement types
 */
export enum RequirementType {
  FUNCTIONAL = 'FUNCTIONAL',
  NON_FUNCTIONAL = 'NON_FUNCTIONAL',
  BUSINESS = 'BUSINESS',
  TECHNICAL = 'TECHNICAL'
}

/**
 * Constraint types
 */
export enum ConstraintType {
  TECHNICAL = 'TECHNICAL',
  LEGAL = 'LEGAL',
  BUSINESS = 'BUSINESS',
  RESOURCE = 'RESOURCE',
  TIME = 'TIME'
}

/**
 * Input for constitution generation
 */
export interface ConstitutionInput {
  /** Business case description */
  businessCase: string;

  /** List of stakeholders (e.g., ["customers", "support", "management"]) */
  stakeholders: string[];

  /** Project constraints (e.g., ["Must integrate with legacy", "GDPR compliant"]) */
  constraints: string[];

  /** Success criteria (e.g., ["50% reduction in support tickets"]) */
  successCriteria: string[];

  /** Optional: Technical context */
  technicalContext?: {
    existingSystems?: string[];
    technologies?: string[];
    teamSize?: number;
    timeline?: string;
  };
}

/**
 * Project principle
 */
export interface Principle {
  /** Unique identifier */
  id: string;

  /** Principle category */
  category: PrincipleCategory;

  /** Principle statement */
  principle: string;

  /** Rationale for this principle */
  rationale: string;

  /** How to apply this principle */
  application: string[];
}

/**
 * Project requirement
 */
export interface Requirement {
  /** Unique identifier (e.g., REQ-001) */
  id: string;

  /** Requirement type */
  type: RequirementType;

  /** Requirement description */
  description: string;

  /** Priority level */
  priority: Priority;

  /** Related principles */
  relatedPrinciples?: string[];

  /** Acceptance criteria */
  acceptanceCriteria?: string[];
}

/**
 * Project constraint
 */
export interface Constraint {
  /** Unique identifier */
  id: string;

  /** Constraint type */
  type: ConstraintType;

  /** Constraint description */
  description: string;

  /** Impact if not followed */
  impact: string;

  /** How to address this constraint */
  mitigation?: string;
}

/**
 * Project risk
 */
export interface Risk {
  /** Unique identifier (e.g., RISK-001) */
  id: string;

  /** Risk description */
  description: string;

  /** Impact level if risk occurs */
  impact: RiskLevel;

  /** Likelihood of occurrence */
  likelihood: RiskLevel;

  /** Mitigation strategies */
  mitigation: string[];

  /** Related requirements or constraints */
  relatedItems?: string[];
}

/**
 * Project scope definition
 */
export interface Scope {
  /** Features/capabilities in scope */
  inScope: string[];

  /** Features/capabilities out of scope */
  outScope: string[];

  /** Development phases */
  phases: Phase[];

  /** Key assumptions */
  assumptions: string[];
}

/**
 * Development phase
 */
export interface Phase {
  /** Phase number */
  number: number;

  /** Phase name */
  name: string;

  /** Phase goals */
  goals: string[];

  /** Estimated duration (e.g., "2 weeks", "3 sprints") */
  duration: string;

  /** Key deliverables */
  deliverables: string[];
}

/**
 * Result of constitution generation
 */
export interface ConstitutionResult {
  /** Project principles */
  principles: Principle[];

  /** Project requirements */
  requirements: Requirement[];

  /** Project constraints */
  constraints: Constraint[];

  /** Project risks */
  risks: Risk[];

  /** Project scope */
  scope: Scope;

  /** Metadata */
  metadata: {
    generatedAt: Date;
    generatedBy: string;
    version: string;
  };
}

// ============================================================================
// SPECIFICATION TYPES
// ============================================================================

/**
 * Architecture patterns
 */
export enum ArchitecturePattern {
  MONOLITHIC = 'MONOLITHIC',
  LAYERED = 'LAYERED',
  MICROSERVICES = 'MICROSERVICES',
  LAYERED_MICROSERVICES = 'LAYERED_MICROSERVICES',
  EVENT_DRIVEN = 'EVENT_DRIVEN',
  SERVERLESS = 'SERVERLESS'
}

/**
 * Component types
 */
export enum ComponentType {
  SERVICE = 'SERVICE',
  MICROSERVICE = 'MICROSERVICE',
  LIBRARY = 'LIBRARY',
  API = 'API',
  DATABASE = 'DATABASE',
  CACHE = 'CACHE',
  QUEUE = 'QUEUE',
  FRONTEND = 'FRONTEND'
}

/**
 * HTTP methods
 */
export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  PATCH = 'PATCH',
  DELETE = 'DELETE'
}

/**
 * Authentication types
 */
export enum AuthType {
  NONE = 'NONE',
  BASIC = 'BASIC',
  JWT = 'JWT',
  OAUTH2 = 'OAUTH2',
  API_KEY = 'API_KEY'
}

/**
 * Database field types
 */
export enum FieldType {
  UUID = 'UUID',
  INTEGER = 'INTEGER',
  BIGINT = 'BIGINT',
  VARCHAR = 'VARCHAR',
  TEXT = 'TEXT',
  BOOLEAN = 'BOOLEAN',
  DATE = 'DATE',
  DATETIME = 'DATETIME',
  TIMESTAMP = 'TIMESTAMP',
  JSON = 'JSON',
  ARRAY = 'ARRAY'
}

/**
 * Relationship types
 */
export enum RelationType {
  ONE_TO_ONE = 'ONE_TO_ONE',
  ONE_TO_MANY = 'ONE_TO_MANY',
  MANY_TO_ONE = 'MANY_TO_ONE',
  MANY_TO_MANY = 'MANY_TO_MANY'
}

/**
 * Input for specification generation
 */
export interface SpecificationInput {
  /** Constitution from previous step */
  constitution: ConstitutionResult;

  /** Technical context */
  technicalContext: {
    /** Preferred technologies (e.g., ["React", "Node.js", "PostgreSQL"]) */
    technologies?: string[];

    /** Existing systems to integrate with */
    existingSystems?: string[];

    /** Team size and composition */
    team?: {
      size: number;
      skills: string[];
    };

    /** Infrastructure constraints */
    infrastructure?: {
      cloud?: string; // AWS, Azure, GCP
      onPremise?: boolean;
      budget?: string;
    };
  };

  /**
   * Development stack from Green Paper session
   * Detailed technology choices for development
   */
  developmentStack?: DevelopmentStack;

  /**
   * Operational stack from Green Paper session
   * Infrastructure and deployment configuration
   */
  operationalStack?: OperationalStack;
}

/**
 * Development stack - tools and technologies for building the software
 */
export interface DevelopmentStack {
  /** Programming languages used */
  languages: string[];

  /** Frameworks and libraries */
  frameworks: {
    frontend?: string[];
    backend?: string[];
    testing?: string[];
  };

  /** Database technologies */
  databases: {
    primary: string;
    cache?: string;
    search?: string;
  };

  /** Testing tools and frameworks */
  testing: {
    unit: string[];
    integration: string[];
    e2e?: string[];
    performance?: string[];
  };

  /** Development tools */
  devTools: {
    ide?: string[];
    linting: string[];
    formatting: string[];
    debugging?: string[];
  };

  /** Version control */
  versionControl: {
    system: string;  // git, svn
    platform: string;  // GitHub, GitLab, Bitbucket
    branchStrategy?: string;  // gitflow, trunk-based
  };

  /** Package managers */
  packageManagers: string[];

  /** Build tools */
  buildTools?: string[];
}

/**
 * Operational stack - infrastructure and deployment technologies
 */
export interface OperationalStack {
  /** Hosting platform */
  hosting: {
    provider: string;  // AWS, GCP, Azure, on-prem, hybrid
    type: 'cloud' | 'on-premise' | 'hybrid';
    region?: string[];
  };

  /** Containerization */
  containerization?: {
    runtime: string;  // Docker, Podman
    registry?: string;  // Docker Hub, ECR, GCR
  };

  /** Orchestration */
  orchestration?: {
    platform?: string;  // Kubernetes, ECS, Swarm, Nomad
    managedService?: string;  // EKS, GKE, AKS
  };

  /** CI/CD Pipeline */
  cicd: {
    platform: string;  // GitHub Actions, GitLab CI, Jenkins
    stages: string[];  // build, test, deploy, etc.
    environments: string[];  // dev, staging, prod
  };

  /** Monitoring and observability */
  monitoring: {
    metrics?: string[];  // Prometheus, Datadog, CloudWatch
    logging?: string[];  // ELK, Loki, CloudWatch Logs
    tracing?: string[];  // Jaeger, Zipkin, X-Ray
    alerting?: string[];  // PagerDuty, OpsGenie
  };

  /** Security */
  security: {
    secretsManagement?: string;  // Vault, AWS Secrets Manager
    waf?: string;  // AWS WAF, Cloudflare
    scanning?: string[];  // Snyk, SonarQube, Trivy
    sso?: string;  // Okta, Auth0
  };

  /** CDN and edge */
  cdn?: {
    provider?: string;  // CloudFront, Cloudflare, Fastly
    edgeCompute?: string;  // Lambda@Edge, Workers
  };

  /** Backup and disaster recovery */
  backupDr?: {
    strategy: string;
    rpo?: string;  // Recovery Point Objective
    rto?: string;  // Recovery Time Objective
  };
}

/**
 * System architecture specification
 */
export interface ArchitectureSpec {
  /** Architecture pattern */
  pattern: ArchitecturePattern;

  /** Architecture layers (if applicable) */
  layers?: string[];

  /** Main components */
  components: string[];

  /** Technology stack (legacy - use developmentStack/operationalStack) */
  technologies: {
    frontend?: string[];
    backend?: string[];
    database?: string[];
    cache?: string[];
    queue?: string[];
    other?: string[];
  };

  /** Development stack - detailed dev technologies */
  developmentStack?: DevelopmentStack;

  /** Operational stack - deployment & infrastructure */
  operationalStack?: OperationalStack;

  /** Integration patterns */
  integrationPatterns: string[];

  /** Architecture diagram (as text/ASCII) */
  diagram?: string;

  /** Architecture Decision Records (ADRs) */
  adrs?: ArchitectureDecisionRecord[];
}

/**
 * Architecture Decision Record
 */
export interface ArchitectureDecisionRecord {
  id: string;
  title: string;
  status: 'proposed' | 'accepted' | 'deprecated' | 'superseded';
  context: string;
  decision: string;
  consequences: string[];
  date: string;
}

/**
 * Component specification
 */
export interface ComponentSpec {
  /** Component name */
  name: string;

  /** Component type */
  type: ComponentType;

  /** Component responsibilities */
  responsibilities: string[];

  /** Public interfaces (API endpoints, methods, etc.) */
  interfaces: string[];

  /** Dependencies on other components */
  dependencies: string[];

  /** Technology stack for this component */
  technologies: string[];

  /** Configuration requirements */
  configuration?: {
    envVars?: string[];
    secrets?: string[];
    files?: string[];
  };
}

/**
 * API interface specification
 */
export interface InterfaceSpec {
  /** Endpoint path (e.g., "/api/auth/login") */
  endpoint: string;

  /** HTTP method */
  method: HttpMethod;

  /** Request body schema */
  requestBody?: Record<string, any>;

  /** Response body schema */
  responseBody?: Record<string, any>;

  /** Query parameters */
  queryParams?: Record<string, string>;

  /** Path parameters */
  pathParams?: Record<string, string>;

  /** Authentication required */
  authentication: AuthType;

  /** Rate limiting (e.g., "100 requests/minute") */
  rateLimit?: string;

  /** Response status codes */
  statusCodes: {
    code: number;
    description: string;
  }[];
}

/**
 * Database entity/table specification
 */
export interface EntitySpec {
  /** Entity name (singular, PascalCase) */
  name: string;

  /** Database table name (plural, snake_case) */
  table: string;

  /** Entity description */
  description: string;

  /** Entity fields */
  fields: FieldSpec[];

  /** Indexes */
  indexes: string[];

  /** Relationships to other entities */
  relationships: RelationshipSpec[];

  /** Constraints (UNIQUE, CHECK, etc.) */
  constraints?: string[];
}

/**
 * Database field specification
 */
export interface FieldSpec {
  /** Field name */
  name: string;

  /** Field type */
  type: FieldType;

  /** Type details (e.g., "VARCHAR(255)") */
  typeDetail?: string;

  /** Is primary key */
  primaryKey?: boolean;

  /** Is nullable */
  nullable?: boolean;

  /** Is unique */
  unique?: boolean;

  /** Default value */
  default?: any;

  /** Field description */
  description?: string;
}

/**
 * Database relationship specification
 */
export interface RelationshipSpec {
  /** Relationship type */
  type: RelationType;

  /** Target entity name */
  target: string;

  /** Foreign key field */
  foreignKey?: string;

  /** Join table (for many-to-many) */
  joinTable?: string;

  /** Cascade behavior */
  cascade?: {
    onDelete?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
    onUpdate?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
  };
}

/**
 * Data model specification
 */
export interface DataModelSpec {
  /** All entities */
  entities: EntitySpec[];

  /** Migration strategy */
  migrationStrategy: {
    tool: string; // Alembic, Flyway, Liquibase
    approach: string; // Blue-green, Rolling, etc.
  };

  /** Seed data requirements */
  seedData?: string[];
}

/**
 * Quality requirement categories
 */
export enum QualityCategory {
  PERFORMANCE = 'PERFORMANCE',
  SECURITY = 'SECURITY',
  SCALABILITY = 'SCALABILITY',
  AVAILABILITY = 'AVAILABILITY',
  RELIABILITY = 'RELIABILITY',
  MAINTAINABILITY = 'MAINTAINABILITY',
  USABILITY = 'USABILITY',
  ACCESSIBILITY = 'ACCESSIBILITY'
}

/**
 * Quality requirement specification
 */
export interface QualityRequirement {
  /** Category */
  category: QualityCategory;

  /** Requirement description */
  requirement: string;

  /** Target metric */
  metric: string;

  /** How to measure */
  measurement: string;

  /** Related components */
  relatedComponents?: string[];
}

/**
 * Result of specification generation
 */
export interface SpecificationResult {
  /** Architecture specification */
  architecture: ArchitectureSpec;

  /** Component specifications */
  components: ComponentSpec[];

  /** API interface specifications */
  interfaces: InterfaceSpec[];

  /** Data model specification */
  dataModel: DataModelSpec;

  /** Quality requirements */
  qualityRequirements: QualityRequirement[];

  /** Metadata */
  metadata: {
    generatedAt: Date;
    generatedBy: string;
    version: string;
    basedOnConstitution: string; // Constitution version
  };
}

// ============================================================================
// TASK GENERATION TYPES
// ============================================================================

/**
 * Item types in hierarchical structure
 */
export enum ItemType {
  EPIC = 'EPIC',
  FEATURE = 'FEATURE',
  STORY = 'STORY',
  TASK = 'TASK'
}

/**
 * Story points (Fibonacci sequence)
 */
export type StoryPoints = 1 | 2 | 3 | 5 | 8 | 13 | 21 | 34;

/**
 * Input for task generation
 */
export interface TaskGenerationInput {
  /** Specification from previous step */
  specification: SpecificationResult;

  /** Team capacity (hours per sprint) */
  teamCapacity?: number;

  /** Sprint duration (days) */
  sprintDuration?: number;

  /** Agent assignments */
  agentAssignments?: Record<string, string[]>; // agent name -> skills
}

/**
 * Epic specification
 */
export interface Epic {
  /** Unique identifier (e.g., EPIC-001) */
  id: string;

  /** Epic title */
  title: string;

  /** Epic description */
  description: string;

  /** Business value */
  businessValue: string;

  /** Priority */
  priority: Priority;

  /** Estimated story points (sum of features) */
  estimatedSP: number;

  /** Features in this epic */
  features: string[]; // Feature IDs

  /** Related requirements */
  relatedRequirements?: string[];

  /** Related components */
  relatedComponents?: string[];
}

/**
 * Feature specification
 */
export interface Feature {
  /** Unique identifier (e.g., FEATURE-001) */
  id: string;

  /** Parent epic ID */
  epicId: string;

  /** Feature title */
  title: string;

  /** Feature description */
  description: string;

  /** Acceptance criteria */
  acceptanceCriteria: string[];

  /** Priority */
  priority: Priority;

  /** Estimated story points (sum of stories) */
  estimatedSP: number;

  /** Stories in this feature */
  stories: string[]; // Story IDs

  /** Dependencies */
  dependencies?: string[]; // Other feature IDs
}

/**
 * User story specification
 */
export interface Story {
  /** Unique identifier (e.g., STORY-001) */
  id: string;

  /** Parent feature ID */
  featureId: string;

  /** Story title (Connextra format: "As a... I want... So that...") */
  title: string;

  /** Story description */
  description: string;

  /** Acceptance criteria (Given-When-Then format) */
  acceptanceCriteria: string[];

  /** Story points */
  storyPoints: StoryPoints;

  /** Priority */
  priority: Priority;

  /** Tasks in this story */
  tasks: string[]; // Task IDs

  /** Dependencies */
  dependencies?: string[]; // Other story IDs
}

/**
 * Task specification
 */
export interface Task {
  /** Unique identifier (e.g., TASK-001) */
  id: string;

  /** Parent story ID */
  storyId: string;

  /** Task title */
  title: string;

  /** Task description */
  description: string;

  /** Estimated hours */
  estimatedHours: number;

  /** Required skills */
  skills: string[];

  /** Suggested agent assignment */
  assignTo?: string;

  /** Technical notes */
  technicalNotes?: string[];

  /** Dependencies */
  dependencies?: string[]; // Other task IDs
}

/**
 * Estimation summary
 */
export interface Estimation {
  /** Total epics */
  totalEpics: number;

  /** Total features */
  totalFeatures: number;

  /** Total stories */
  totalStories: number;

  /** Total tasks */
  totalTasks: number;

  /** Total story points */
  totalStoryPoints: number;

  /** Total estimated hours */
  totalHours: number;

  /** Estimated sprints (based on team capacity) */
  estimatedSprints?: number;

  /** Estimated calendar weeks */
  estimatedWeeks?: number;

  /** Confidence level (0.0-1.0) */
  confidence: number;
}

/**
 * Result of task generation
 */
export interface TaskGenerationResult {
  /** Generated epics */
  epics: Epic[];

  /** Generated features */
  features: Feature[];

  /** Generated stories */
  stories: Story[];

  /** Generated tasks */
  tasks: Task[];

  /** Estimation summary */
  estimations: Estimation;

  /** Metadata */
  metadata: {
    generatedAt: Date;
    generatedBy: string;
    version: string;
    basedOnSpecification: string; // Specification version
  };
}

// ============================================================================
// SPEC-KIT WORKFLOW TYPES
// ============================================================================

/**
 * Complete Spec-Kit workflow result
 */
export interface SpecKitWorkflowResult {
  /** Constitution result */
  constitution: ConstitutionResult;

  /** Specification result */
  specification: SpecificationResult;

  /** Architecture review result (BMAD-inspired evaluation) */
  architectureReview?: ArchitectureReviewResult;

  /** Task generation result */
  tasks: TaskGenerationResult;

  /** Generated files */
  files: GeneratedFile[];

  /** Workflow summary */
  summary: WorkflowSummary;
}

/**
 * Generated file
 */
export interface GeneratedFile {
  /** File path relative to project root */
  path: string;

  /** File content */
  content: string;

  /** File format (markdown, json, etc.) */
  format: string;
}

/**
 * Workflow execution summary
 */
export interface WorkflowSummary {
  /** Total execution time (ms) */
  executionTime: number;

  /** Constitution generation time (ms) */
  constitutionTime: number;

  /** Specification generation time (ms) */
  specificationTime: number;

  /** Architecture review time (ms) */
  reviewTime?: number;

  /** Task generation time (ms) */
  taskGenerationTime: number;

  /** Number of files generated */
  filesGenerated: number;

  /** Total epics created */
  totalEpics: number;

  /** Total features created */
  totalFeatures: number;

  /** Total stories created */
  totalStories: number;

  /** Estimated project duration (weeks) */
  estimatedWeeks: number;

  /** Architecture review verdict */
  reviewVerdict?: ReviewVerdict;

  /** Architecture alignment score (0-100) */
  alignmentScore?: number;

  /** True if workflow paused awaiting human approval */
  humanApprovalRequired?: boolean;

  /** Human approval request ID (for resuming workflow) */
  humanApprovalRequestId?: string;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Calculate risk score (0.0-1.0) based on impact and likelihood
 */
export function calculateRiskScore(impact: RiskLevel, likelihood: RiskLevel): number {
  const riskValues: Record<RiskLevel, number> = {
    [RiskLevel.CRITICAL]: 1.0,
    [RiskLevel.HIGH]: 0.75,
    [RiskLevel.MEDIUM]: 0.5,
    [RiskLevel.LOW]: 0.25
  };

  return (riskValues[impact] + riskValues[likelihood]) / 2;
}

/**
 * Convert story points to estimated hours
 * Rule of thumb: 1 SP = 4-6 hours (we use 5)
 */
export function storyPointsToHours(storyPoints: StoryPoints): number {
  return storyPoints * 5;
}

/**
 * Convert hours to story points (Fibonacci)
 */
export function hoursToStoryPoints(hours: number): StoryPoints {
  if (hours <= 5) return 1;
  if (hours <= 10) return 2;
  if (hours <= 15) return 3;
  if (hours <= 25) return 5;
  if (hours <= 40) return 8;
  if (hours <= 65) return 13;
  if (hours <= 105) return 21;
  return 34;
}

/**
 * Generate unique ID with prefix
 */
export function generateId(prefix: string, counter: number): string {
  return `${prefix}-${String(counter).padStart(3, '0')}`;
}

/**
 * Validate constitution result
 */
export function validateConstitution(constitution: ConstitutionResult): boolean {
  return (
    constitution.principles.length > 0 &&
    constitution.requirements.length > 0 &&
    constitution.scope.inScope.length > 0
  );
}

/**
 * Validate specification result
 */
export function validateSpecification(specification: SpecificationResult): boolean {
  return (
    specification.components.length > 0 &&
    specification.dataModel.entities.length > 0
  );
}

/**
 * Validate task generation result
 */
export function validateTaskGeneration(tasks: TaskGenerationResult): boolean {
  return (
    tasks.epics.length > 0 &&
    tasks.features.length > 0 &&
    tasks.stories.length > 0 &&
    tasks.tasks.length > 0
  );
}

// ============================================================================
// ARCHITECT REVIEW TYPES (BMAD-inspired evaluation phase)
// ============================================================================

/**
 * Architecture review verdict
 */
export enum ReviewVerdict {
  APPROVED = 'APPROVED',
  APPROVED_WITH_CONDITIONS = 'APPROVED_WITH_CONDITIONS',
  NEEDS_HUMAN_APPROVAL = 'NEEDS_HUMAN_APPROVAL',  // < 95% alignment
  NEEDS_REVISION = 'NEEDS_REVISION',
  REJECTED = 'REJECTED'
}

/**
 * Human approval request for architecture review
 */
export interface HumanApprovalRequest {
  /** Unique request ID */
  requestId: string;
  /** Review that triggered the request */
  reviewResult: ArchitectureReviewResult;
  /** Why human approval is needed */
  reason: string;
  /** Specific items requiring decision */
  decisionsRequired: {
    id: string;
    category: 'alignment_gap' | 'risk' | 'trade_off' | 'cost';
    title: string;
    description: string;
    options: string[];
    recommendation: string;
  }[];
  /** Deadline for approval */
  deadline?: Date;
  /** Status */
  status: 'pending' | 'approved' | 'rejected' | 'modified';
  /** Human response */
  response?: {
    approvedBy: string;
    approvedAt: Date;
    decisions: Record<string, string>;
    comments?: string;
    proceedWithGeneration: boolean;
  };
}

/**
 * Architecture review configuration
 */
export interface ArchitectureReviewConfig {
  /** Minimum alignment score to auto-approve (default: 95) */
  minAlignmentScore: number;
  /** Maximum critical risks allowed (default: 0) */
  maxCriticalRisks: number;
  /** Maximum high risks allowed (default: 2) */
  maxHighRisks: number;
  /** Require human approval for all reviews */
  alwaysRequireHumanApproval: boolean;
  /** Auto-reject below this score */
  autoRejectBelowScore: number;
}

/**
 * Trade-off category for architecture decisions
 */
export enum TradeOffCategory {
  PERFORMANCE_VS_COST = 'PERFORMANCE_VS_COST',
  SECURITY_VS_USABILITY = 'SECURITY_VS_USABILITY',
  SCALABILITY_VS_SIMPLICITY = 'SCALABILITY_VS_SIMPLICITY',
  FLEXIBILITY_VS_SPEED = 'FLEXIBILITY_VS_SPEED',
  CONSISTENCY_VS_AVAILABILITY = 'CONSISTENCY_VS_AVAILABILITY',
  BUILD_VS_BUY = 'BUILD_VS_BUY'
}

/**
 * Alignment check result
 */
export interface AlignmentCheck {
  /** What was checked */
  aspect: string;
  /** Source requirement/constraint */
  source: string;
  /** Architecture element being validated */
  architectureElement: string;
  /** Is it aligned? */
  aligned: boolean;
  /** Gap description if not aligned */
  gap?: string;
  /** Importance level of the gap (low, medium, high) */
  gapImportance?: 'low' | 'medium' | 'high';
  /** Suggested remediation */
  remediation?: string;
}

/**
 * Trade-off analysis
 */
export interface TradeOffAnalysis {
  /** Trade-off category */
  category: TradeOffCategory;
  /** Description of the trade-off */
  description: string;
  /** Option A */
  optionA: {
    name: string;
    pros: string[];
    cons: string[];
  };
  /** Option B */
  optionB: {
    name: string;
    pros: string[];
    cons: string[];
  };
  /** Chosen option */
  chosenOption: 'A' | 'B';
  /** Rationale for choice */
  rationale: string;
}

/**
 * Risk identified during architecture review
 */
export interface ArchitectureRisk {
  /** Risk ID */
  id: string;
  /** Risk title */
  title: string;
  /** Detailed description */
  description: string;
  /** Category */
  category: 'technical' | 'operational' | 'security' | 'cost' | 'team';
  /** Impact level */
  impact: RiskLevel;
  /** Likelihood */
  likelihood: RiskLevel;
  /** Mitigation strategy */
  mitigation: string;
  /** Related architecture element */
  relatedElement?: string;
}

/**
 * Cost estimate for architecture
 */
export interface CostEstimate {
  /** Category */
  category: 'infrastructure' | 'licensing' | 'development' | 'maintenance' | 'operations';
  /** Item */
  item: string;
  /** Monthly cost estimate */
  monthlyCost: string;
  /** Annual cost estimate */
  annualCost: string;
  /** Assumptions */
  assumptions: string[];
  /** Scaling notes */
  scalingNotes?: string;
}

/**
 * Input for architecture review
 */
export interface ArchitectureReviewInput {
  /** Constitution from step 1 */
  constitution: ConstitutionResult;
  /** Specification from step 2 */
  specification: SpecificationResult;
  /** Original Green Paper constraints */
  greenPaperConstraints?: {
    budget?: string;
    timeline?: string;
    technology?: string[];
    resources?: string;
    regulatory?: string[];
  };
  /** Team context */
  teamContext?: {
    size: number;
    skills: string[];
    experience: 'junior' | 'mid' | 'senior' | 'mixed';
  };
  /** Review configuration (thresholds, etc.) */
  reviewConfig?: ArchitectureReviewConfig;
}

/**
 * Result of architecture review
 */
export interface ArchitectureReviewResult {
  /** Overall verdict */
  verdict: ReviewVerdict;
  /** Confidence score (0-1) */
  confidence: number;

  /** Alignment checks against constitution */
  alignmentChecks: {
    principles: AlignmentCheck[];
    requirements: AlignmentCheck[];
    constraints: AlignmentCheck[];
  };

  /** Overall alignment score (0-100) */
  alignmentScore: number;

  /** Trade-off analyses */
  tradeOffs: TradeOffAnalysis[];

  /** Generated ADRs */
  adrs: ArchitectureDecisionRecord[];

  /** Identified risks */
  risks: ArchitectureRisk[];

  /** Cost estimates */
  costEstimates: CostEstimate[];

  /** Total estimated monthly cost */
  totalMonthlyCost?: string;

  /** Recommendations */
  recommendations: {
    priority: Priority;
    category: string;
    title: string;
    description: string;
    impact: string;
  }[];

  /** Conditions for approval (if verdict is APPROVED_WITH_CONDITIONS) */
  conditions?: string[];

  /** Required revisions (if verdict is NEEDS_REVISION) */
  requiredRevisions?: string[];

  /** Human approval request (if verdict is NEEDS_HUMAN_APPROVAL) */
  humanApprovalRequest?: HumanApprovalRequest;

  /** Summary for stakeholders */
  executiveSummary: string;

  /** Metadata */
  metadata: {
    reviewedAt: Date;
    reviewedBy: string;
    version: string;
    specificationVersion: string;
  };
}

/**
 * Validate architecture review result
 */
export function validateArchitectureReview(review: ArchitectureReviewResult): boolean {
  return (
    review.alignmentChecks.principles.length > 0 &&
    review.adrs.length > 0 &&
    review.executiveSummary.length > 0
  );
}
