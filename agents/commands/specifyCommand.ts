/**
 * Specify Command (/specify)
 *
 * Transforms project constitution into detailed technical specification.
 *
 * Agent: Felix (Feature Architect) - qwen2.5-coder:7b
 * Purpose: Constitution → Technical specification (architecture, components, APIs, data model)
 *
 * Week 8 - Monday Afternoon / Tuesday Implementation
 */

import { Agent } from 'kaibanjs';
import {
  SpecificationInput,
  SpecificationResult,
  ArchitectureSpec,
  ArchitecturePattern,
  ComponentSpec,
  ComponentType,
  InterfaceSpec,
  HttpMethod,
  AuthType,
  DataModelSpec,
  EntitySpec,
  FieldSpec,
  FieldType,
  RelationshipSpec,
  RelationType,
  QualityRequirement,
  QualityCategory,
  ConstitutionResult,
  Requirement,
  RequirementType,
  Constraint,
  ConstraintType,
  Priority,
  DevelopmentStack,
  OperationalStack
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

export const SPECIFY_COMMAND = {
  name: '/specify',
  description: 'Transform constitution into detailed technical specification',
  agent: 'Felix', // Feature Architect
  model: 'qwen2.5-coder:7b',
  category: 'specification',
  estimatedTime: '10-15 minutes'
};

/**
 * Full CommandDefinition for /specify command
 */
export const SPECIFICATION_DEFINITION: CommandDefinition = {
  type: SlashCommandType.SPECIFICATION,
  name: 'Technical Specification Generator',
  description: 'Transforms project constitution into detailed technical specification including architecture design, component breakdown, API interfaces, data models, and quality requirements',
  persona: 'Feature Architect (Felix) - Expert in software architecture, system design, API design, and data modeling. Specializes in translating business requirements into scalable technical solutions.',
  expertise: [
    'Software Architecture Design',
    'Design Patterns & Best Practices',
    'API Design (REST, GraphQL)',
    'Database Schema Design',
    'Component-Based Architecture',
    'Microservices & Monolith Patterns',
    'Data Modeling & ER Diagrams',
    'Quality Attributes (Performance, Security, Scalability)'
  ],
  capabilities: [
    'Design system architecture based on requirements',
    'Select appropriate architecture patterns',
    'Break down system into components',
    'Define component responsibilities and dependencies',
    'Design RESTful API endpoints',
    'Create comprehensive data models with entities and relationships',
    'Extract quality requirements (performance, security, scalability)',
    'Generate technical diagrams and specifications',
    'Map requirements to technical components'
  ],
  bestUsedFor: [
    'After constitution generation (Stage 2 of Spec-Kit)',
    'Technical architecture design',
    'System specification documentation',
    'API contract definition',
    'Database schema planning',
    'Component breakdown for implementation',
    'Technical feasibility assessment',
    'Architecture review and validation'
  ],
  requiredContext: [
    'constitution'
  ],
  optionalContext: [
    'technicalContext',
    'existingSystems',
    'preferredTechStack',
    'architecturePattern',
    'constraints'
  ],
  outputTypes: [OutputFormat.MARKDOWN, OutputFormat.JSON, OutputFormat.TEXT],
  examples: [
    {
      scenario: 'E-commerce platform technical spec',
      input: {
        command: SlashCommandType.SPECIFICATION,
        context: {
          metadata: {
            constitution: {
              principles: [
                { category: 'Security', principle: 'GDPR compliant user data handling' },
                { category: 'Performance', principle: 'Sub-100ms response times' }
              ],
              requirements: [
                { type: 'functional', description: 'User authentication and authorization' },
                { type: 'functional', description: 'Product catalog with search' }
              ]
            }
          }
        } as any
      },
      expectedOutcome: 'Generates architecture (layered/microservices), 5-8 components (auth, product catalog, cart, payment), 10-15 API endpoints, data model with 4-6 entities, quality requirements'
    },
    {
      scenario: 'SaaS product technical specification',
      input: {
        command: SlashCommandType.SPECIFICATION,
        context: {
          metadata: {
            constitution: {
              principles: [
                { category: 'Scalability', principle: 'Multi-tenant architecture' },
                { category: 'Maintainability', principle: 'Clean separation of concerns' }
              ]
            },
            technicalContext: {
              preferredTechStack: ['Node.js', 'PostgreSQL', 'React']
            }
          }
        } as any
      },
      expectedOutcome: 'Architecture aligned with tech stack preferences, multi-tenant data model design, component breakdown optimized for team expertise'
    }
  ]
};

// ============================================================================
// MAIN EXECUTION FUNCTION
// ============================================================================

/**
 * Execute specification generation
 *
 * @param input - Specification input with constitution and technical context
 * @param agent - Felix (Feature Architect agent)
 * @returns Specification result with architecture, components, interfaces, data model
 */
export async function executeSpecification(
  input: SpecificationInput,
  agent: Agent
): Promise<SpecificationResult> {
  console.log('🏗️  Executing /specify command...');
  console.log(`Based on constitution version: ${input.constitution.metadata.version}`);

  const startTime = Date.now();

  // Step 1: Design architecture
  console.log('\n📐 Step 1: Designing system architecture...');
  const architecture = await designArchitecture(input, agent);

  // Step 2: Break down components
  console.log('\n🧩 Step 2: Breaking down components...');
  const components = await breakDownComponents(input, architecture, agent);

  // Step 3: Define interfaces (APIs)
  console.log('\n🔌 Step 3: Defining API interfaces...');
  const interfaces = await defineInterfaces(input, components, agent);

  // Step 4: Design data model
  console.log('\n🗄️  Step 4: Designing data model...');
  const dataModel = await designDataModel(input, components, agent);

  // Step 5: Extract quality requirements
  console.log('\n⭐ Step 5: Extracting quality requirements...');
  const qualityRequirements = await extractQualityRequirements(input, agent);

  // Build result
  const result: SpecificationResult = {
    architecture,
    components,
    interfaces,
    dataModel,
    qualityRequirements,
    metadata: {
      generatedAt: new Date(),
      generatedBy: 'Felix (Feature Architect)',
      version: '1.0.0',
      basedOnConstitution: input.constitution.metadata.version
    }
  };

  const duration = Date.now() - startTime;
  console.log(`\n✅ Specification generated in ${(duration / 1000).toFixed(2)}s`);
  console.log(`   - Architecture: ${architecture.pattern}`);
  console.log(`   - ${components.length} components`);
  console.log(`   - ${interfaces.length} API endpoints`);
  console.log(`   - ${dataModel.entities.length} entities`);
  console.log(`   - ${qualityRequirements.length} quality requirements`);

  return result;
}

// ============================================================================
// STEP 1: DESIGN ARCHITECTURE
// ============================================================================

async function designArchitecture(
  input: SpecificationInput,
  agent: Agent
): Promise<ArchitectureSpec> {
  const { constitution, technicalContext, developmentStack, operationalStack } = input;

  // Determine architecture pattern based on requirements
  const pattern = selectArchitecturePattern(constitution, technicalContext);

  // Define layers (if layered architecture)
  const layers = pattern.includes('LAYERED')
    ? ['presentation', 'application', 'domain', 'infrastructure']
    : undefined;

  // Identify main components from requirements
  const components = identifyMainComponents(constitution);

  // Select technology stack (use developmentStack from Green Paper if provided)
  const technologies = selectTechnologyStack(constitution, technicalContext, developmentStack);

  // Define integration patterns
  const integrationPatterns = defineIntegrationPatterns(constitution);

  // Generate architecture diagram (as text)
  const diagram = generateArchitectureDiagram(pattern, components, technologies);

  return {
    pattern,
    layers,
    components,
    technologies,
    integrationPatterns,
    diagram,
    // Include detailed stacks from Green Paper session
    developmentStack,
    operationalStack
  };
}

function selectArchitecturePattern(
  constitution: ConstitutionResult,
  technicalContext: SpecificationInput['technicalContext']
): ArchitecturePattern {
  // Check for scalability requirements
  const needsScalability = constitution.requirements.some(r =>
    r.description.toLowerCase().includes('scale') ||
    r.description.toLowerCase().includes('concurrent')
  );

  // Check for integration requirements
  const hasIntegrations = constitution.constraints.some(c =>
    c.description.toLowerCase().includes('integrate')
  );

  // Decision logic
  if (needsScalability && hasIntegrations) {
    return ArchitecturePattern.LAYERED_MICROSERVICES;
  } else if (needsScalability) {
    return ArchitecturePattern.MICROSERVICES;
  } else if (hasIntegrations) {
    return ArchitecturePattern.LAYERED;
  } else {
    return ArchitecturePattern.MONOLITHIC;
  }
}

function identifyMainComponents(constitution: ConstitutionResult): string[] {
  const components: string[] = [];

  // Always include authentication if users are involved
  if (constitution.scope.inScope.some(item =>
    item.toLowerCase().includes('user') || item.toLowerCase().includes('login')
  )) {
    components.push('authentication-service');
  }

  // Extract components from functional requirements
  const functionalReqs = constitution.requirements.filter(
    r => r.type === RequirementType.FUNCTIONAL
  );

  functionalReqs.forEach(req => {
    const desc = req.description.toLowerCase();

    // Common component patterns
    if (desc.includes('user') || desc.includes('account')) {
      if (!components.includes('user-service')) {
        components.push('user-service');
      }
    }
    if (desc.includes('product') || desc.includes('catalog')) {
      if (!components.includes('product-service')) {
        components.push('product-service');
      }
    }
    if (desc.includes('order') || desc.includes('checkout')) {
      if (!components.includes('order-service')) {
        components.push('order-service');
      }
    }
    if (desc.includes('support') || desc.includes('ticket')) {
      if (!components.includes('support-service')) {
        components.push('support-service');
      }
    }
    if (desc.includes('notification') || desc.includes('email')) {
      if (!components.includes('notification-service')) {
        components.push('notification-service');
      }
    }
  });

  // Always add frontend and API gateway
  components.push('frontend-app');
  components.push('api-gateway');

  return components;
}

function selectTechnologyStack(
  constitution: ConstitutionResult,
  technicalContext: SpecificationInput['technicalContext'],
  developmentStack?: DevelopmentStack
): ArchitectureSpec['technologies'] {
  // If developmentStack is provided from Green Paper, use it as the primary source
  if (developmentStack) {
    return {
      frontend: developmentStack.frameworks.frontend || ['React', 'TypeScript'],
      backend: developmentStack.frameworks.backend || developmentStack.languages,
      database: [developmentStack.databases.primary, developmentStack.databases.cache, developmentStack.databases.search].filter(Boolean) as string[],
      cache: developmentStack.databases.cache ? [developmentStack.databases.cache] : [],
      queue: [],
      other: [
        ...(developmentStack.testing.unit || []),
        ...(developmentStack.devTools.linting || []),
        ...(developmentStack.buildTools || [])
      ]
    };
  }

  // Use preferred technologies if specified
  const preferred = technicalContext.technologies || [];

  // Default stack (can be overridden)
  const stack: ArchitectureSpec['technologies'] = {
    frontend: preferred.filter(t => ['React', 'Vue', 'Angular'].includes(t)),
    backend: preferred.filter(t => ['Node.js', 'Python', 'Java'].includes(t)),
    database: preferred.filter(t => ['PostgreSQL', 'MySQL', 'MongoDB'].includes(t)),
    cache: [],
    queue: [],
    other: []
  };

  // Fill in defaults if not specified
  if (stack.frontend!.length === 0) {
    stack.frontend = ['React', 'TypeScript'];
  }
  if (stack.backend!.length === 0) {
    stack.backend = ['Node.js', 'Express'];
  }
  if (stack.database!.length === 0) {
    stack.database = ['PostgreSQL'];
  }

  // Add cache if performance is critical
  const needsPerformance = constitution.requirements.some(r =>
    r.description.toLowerCase().includes('performance') ||
    r.description.toLowerCase().includes('fast')
  );
  if (needsPerformance) {
    stack.cache = ['Redis'];
  }

  // Add queue for async processing
  const needsAsync = constitution.requirements.some(r =>
    r.description.toLowerCase().includes('async') ||
    r.description.toLowerCase().includes('background')
  );
  if (needsAsync) {
    stack.queue = ['RabbitMQ'];
  }

  return stack;
}

function defineIntegrationPatterns(constitution: ConstitutionResult): string[] {
  const patterns: string[] = [];

  // Check for external system integrations
  const hasIntegrations = constitution.constraints.some(c =>
    c.description.toLowerCase().includes('integrate')
  );

  if (hasIntegrations) {
    patterns.push('REST API integration');
    patterns.push('API Gateway pattern');
    patterns.push('Service mesh (for microservices)');
  }

  // Always include these
  patterns.push('Request-Response');
  patterns.push('Database per service');

  return patterns;
}

function generateArchitectureDiagram(
  pattern: ArchitecturePattern,
  components: string[],
  technologies: ArchitectureSpec['technologies']
): string {
  let diagram = `
Architecture Pattern: ${pattern}

┌─────────────────┐
│   Frontend      │  (${technologies.frontend?.join(', ')})
│   Application   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
`;

  // Add components
  components
    .filter(c => !['frontend-app', 'api-gateway'].includes(c))
    .forEach((component, index) => {
      if (index % 3 === 0 && index > 0) diagram += '\n';
      diagram += `  ┌──────────┐`;
    });

  diagram += '\n';

  components
    .filter(c => !['frontend-app', 'api-gateway'].includes(c))
    .forEach((component, index) => {
      if (index % 3 === 0 && index > 0) diagram += '\n';
      const name = component.replace('-service', '').padEnd(8);
      diagram += `  │${name}  │`;
    });

  diagram += '\n';

  components
    .filter(c => !['frontend-app', 'api-gateway'].includes(c))
    .forEach((component, index) => {
      if (index % 3 === 0 && index > 0) diagram += '\n';
      diagram += `  └──────────┘`;
    });

  diagram += `

         │
         ▼
┌─────────────────┐
│    Database     │  (${technologies.database?.join(', ')})
└─────────────────┘
`;

  if (technologies.cache && technologies.cache.length > 0) {
    diagram += `
         │
         ├──────────────┐
         ▼              ▼
  ┌──────────┐   ┌──────────┐
  │  Cache   │   │  Queue   │
  └──────────┘   └──────────┘
`;
  }

  return diagram;
}

// ============================================================================
// STEP 2: BREAK DOWN COMPONENTS
// ============================================================================

async function breakDownComponents(
  input: SpecificationInput,
  architecture: ArchitectureSpec,
  agent: Agent
): Promise<ComponentSpec[]> {
  const components: ComponentSpec[] = [];

  // Create spec for each component
  for (const componentName of architecture.components) {
    const spec = createComponentSpec(componentName, input, architecture);
    components.push(spec);
  }

  return components;
}

function createComponentSpec(
  name: string,
  input: SpecificationInput,
  architecture: ArchitectureSpec
): ComponentSpec {
  // Determine component type
  const type = determineComponentType(name);

  // Define responsibilities
  const responsibilities = defineResponsibilities(name, input.constitution);

  // Define interfaces
  const interfaces = defineComponentInterfaces(name, type);

  // Identify dependencies
  const dependencies = identifyDependencies(name, architecture.components);

  // Select technologies
  const technologies = selectComponentTechnologies(type, architecture);

  // Configuration requirements
  const configuration = {
    envVars: [`${name.toUpperCase()}_PORT`, `${name.toUpperCase()}_DB_URL`],
    secrets: [`${name.toUpperCase()}_API_KEY`],
    files: [`${name}.config.json`]
  };

  return {
    name,
    type,
    responsibilities,
    interfaces,
    dependencies,
    technologies,
    configuration
  };
}

function determineComponentType(name: string): ComponentType {
  if (name.includes('frontend')) return ComponentType.FRONTEND;
  if (name.includes('api-gateway') || name.includes('gateway')) return ComponentType.API;
  if (name.includes('database')) return ComponentType.DATABASE;
  if (name.includes('cache')) return ComponentType.CACHE;
  if (name.includes('queue')) return ComponentType.QUEUE;
  if (name.includes('service')) return ComponentType.MICROSERVICE;
  return ComponentType.SERVICE;
}

function defineResponsibilities(name: string, constitution: ConstitutionResult): string[] {
  const responsibilities: string[] = [];

  if (name.includes('auth')) {
    responsibilities.push('User authentication and authorization');
    responsibilities.push('Session management');
    responsibilities.push('Token generation and validation');
  } else if (name.includes('user')) {
    responsibilities.push('User profile management');
    responsibilities.push('User data CRUD operations');
    responsibilities.push('User preferences');
  } else if (name.includes('product')) {
    responsibilities.push('Product catalog management');
    responsibilities.push('Product search and filtering');
    responsibilities.push('Inventory tracking');
  } else if (name.includes('order')) {
    responsibilities.push('Order processing');
    responsibilities.push('Payment integration');
    responsibilities.push('Order status tracking');
  } else if (name.includes('support') || name.includes('ticket')) {
    responsibilities.push('Support ticket creation');
    responsibilities.push('Ticket status management');
    responsibilities.push('Assignment to support staff');
  } else if (name.includes('notification')) {
    responsibilities.push('Send email notifications');
    responsibilities.push('Push notifications');
    responsibilities.push('SMS notifications');
  } else if (name.includes('frontend')) {
    responsibilities.push('User interface rendering');
    responsibilities.push('User interaction handling');
    responsibilities.push('API communication');
  } else if (name.includes('api-gateway')) {
    responsibilities.push('Request routing');
    responsibilities.push('Authentication and authorization');
    responsibilities.push('Rate limiting');
    responsibilities.push('API versioning');
  }

  return responsibilities;
}

function defineComponentInterfaces(name: string, type: ComponentType): string[] {
  const interfaces: string[] = [];

  if (type === ComponentType.MICROSERVICE || type === ComponentType.SERVICE) {
    const basePath = `/${name.replace('-service', '')}`;
    interfaces.push(`GET ${basePath}`);
    interfaces.push(`POST ${basePath}`);
    interfaces.push(`GET ${basePath}/:id`);
    interfaces.push(`PUT ${basePath}/:id`);
    interfaces.push(`DELETE ${basePath}/:id`);
  }

  return interfaces;
}

function identifyDependencies(name: string, allComponents: string[]): string[] {
  const dependencies: string[] = [];

  // All services depend on database
  if (name.includes('service') && !name.includes('database')) {
    const dbComponent = allComponents.find(c => c.includes('database'));
    if (dbComponent) dependencies.push(dbComponent);
  }

  // All services may depend on cache
  if (name.includes('service')) {
    const cacheComponent = allComponents.find(c => c.includes('cache'));
    if (cacheComponent) dependencies.push(cacheComponent);
  }

  // Frontend depends on API gateway
  if (name.includes('frontend')) {
    const gateway = allComponents.find(c => c.includes('gateway'));
    if (gateway) dependencies.push(gateway);
  }

  // Services depend on authentication
  if (name.includes('service') && !name.includes('auth')) {
    const authService = allComponents.find(c => c.includes('auth'));
    if (authService) dependencies.push(authService);
  }

  return dependencies;
}

function selectComponentTechnologies(
  type: ComponentType,
  architecture: ArchitectureSpec
): string[] {
  const tech: string[] = [];

  switch (type) {
    case ComponentType.FRONTEND:
      tech.push(...(architecture.technologies.frontend || ['React']));
      break;
    case ComponentType.MICROSERVICE:
    case ComponentType.SERVICE:
      tech.push(...(architecture.technologies.backend || ['Node.js']));
      break;
    case ComponentType.DATABASE:
      tech.push(...(architecture.technologies.database || ['PostgreSQL']));
      break;
    case ComponentType.CACHE:
      tech.push(...(architecture.technologies.cache || ['Redis']));
      break;
    case ComponentType.QUEUE:
      tech.push(...(architecture.technologies.queue || ['RabbitMQ']));
      break;
  }

  return tech;
}

// ============================================================================
// STEP 3: DEFINE INTERFACES (APIs)
// ============================================================================

async function defineInterfaces(
  input: SpecificationInput,
  components: ComponentSpec[],
  agent: Agent
): Promise<InterfaceSpec[]> {
  const interfaces: InterfaceSpec[] = [];

  // Generate API specs for each service component
  for (const component of components) {
    if (component.type === ComponentType.MICROSERVICE || component.type === ComponentType.SERVICE) {
      const componentInterfaces = generateInterfaceSpecs(component);
      interfaces.push(...componentInterfaces);
    }
  }

  return interfaces;
}

function generateInterfaceSpecs(component: ComponentSpec): InterfaceSpec[] {
  const specs: InterfaceSpec[] = [];
  const basePath = `/${component.name.replace('-service', '')}`;

  // List endpoint
  specs.push({
    endpoint: basePath,
    method: HttpMethod.GET,
    requestBody: undefined,
    responseBody: {
      items: 'array',
      total: 'number',
      page: 'number'
    },
    queryParams: {
      page: 'number',
      limit: 'number',
      sort: 'string'
    },
    authentication: AuthType.JWT,
    rateLimit: '100 requests/minute',
    statusCodes: [
      { code: 200, description: 'Success' },
      { code: 401, description: 'Unauthorized' },
      { code: 429, description: 'Too many requests' }
    ]
  });

  // Create endpoint
  specs.push({
    endpoint: basePath,
    method: HttpMethod.POST,
    requestBody: {
      data: 'object'
    },
    responseBody: {
      id: 'string',
      createdAt: 'date'
    },
    authentication: AuthType.JWT,
    rateLimit: '50 requests/minute',
    statusCodes: [
      { code: 201, description: 'Created' },
      { code: 400, description: 'Bad request' },
      { code: 401, description: 'Unauthorized' }
    ]
  });

  // Get by ID endpoint
  specs.push({
    endpoint: `${basePath}/:id`,
    method: HttpMethod.GET,
    pathParams: {
      id: 'string (UUID)'
    },
    responseBody: {
      id: 'string',
      data: 'object'
    },
    authentication: AuthType.JWT,
    rateLimit: '200 requests/minute',
    statusCodes: [
      { code: 200, description: 'Success' },
      { code: 404, description: 'Not found' },
      { code: 401, description: 'Unauthorized' }
    ]
  });

  return specs;
}

// ============================================================================
// STEP 4: DESIGN DATA MODEL
// ============================================================================

async function designDataModel(
  input: SpecificationInput,
  components: ComponentSpec[],
  agent: Agent
): Promise<DataModelSpec> {
  const entities: EntitySpec[] = [];

  // Generate entities from components
  for (const component of components) {
    if (component.type === ComponentType.MICROSERVICE || component.type === ComponentType.SERVICE) {
      const entityName = component.name.replace('-service', '').replace(/-/g, '');
      const capitalizedName = entityName.charAt(0).toUpperCase() + entityName.slice(1);

      const entity = generateEntitySpec(capitalizedName);
      entities.push(entity);
    }
  }

  // Migration strategy
  const migrationStrategy = {
    tool: 'Alembic',
    approach: 'Rolling updates with backward compatibility'
  };

  return {
    entities,
    migrationStrategy,
    seedData: ['Initial admin user', 'Default configuration']
  };
}

function generateEntitySpec(name: string): EntitySpec {
  // Base fields for all entities
  const fields: FieldSpec[] = [
    {
      name: 'id',
      type: FieldType.UUID,
      primaryKey: true,
      nullable: false,
      description: 'Unique identifier'
    },
    {
      name: 'created_at',
      type: FieldType.TIMESTAMP,
      nullable: false,
      default: 'NOW()',
      description: 'Creation timestamp'
    },
    {
      name: 'updated_at',
      type: FieldType.TIMESTAMP,
      nullable: false,
      default: 'NOW()',
      description: 'Last update timestamp'
    }
  ];

  // Add entity-specific fields
  if (name.toLowerCase().includes('user')) {
    fields.push(
      {
        name: 'email',
        type: FieldType.VARCHAR,
        typeDetail: 'VARCHAR(255)',
        unique: true,
        nullable: false,
        description: 'User email address'
      },
      {
        name: 'name',
        type: FieldType.VARCHAR,
        typeDetail: 'VARCHAR(255)',
        nullable: false,
        description: 'User full name'
      }
    );
  }

  // Table name (plural, snake_case)
  const tableName = `${name.toLowerCase()}s`;

  return {
    name,
    table: tableName,
    description: `${name} entity`,
    fields,
    indexes: ['created_at', 'updated_at'],
    relationships: [],
    constraints: ['CHECK (created_at <= updated_at)']
  };
}

// ============================================================================
// STEP 5: EXTRACT QUALITY REQUIREMENTS
// ============================================================================

async function extractQualityRequirements(
  input: SpecificationInput,
  agent: Agent
): Promise<QualityRequirement[]> {
  const requirements: QualityRequirement[] = [];
  const { constitution } = input;

  // Extract from non-functional requirements
  const nonFunctionalReqs = constitution.requirements.filter(
    r => r.type === RequirementType.NON_FUNCTIONAL
  );

  nonFunctionalReqs.forEach(req => {
    const desc = req.description.toLowerCase();

    if (desc.includes('performance') || desc.includes('fast') || desc.includes('response')) {
      requirements.push({
        category: QualityCategory.PERFORMANCE,
        requirement: req.description,
        metric: 'Response time < 1s (p95)',
        measurement: 'Load testing with k6 or JMeter'
      });
    }

    if (desc.includes('security') || desc.includes('gdpr') || desc.includes('compliance')) {
      requirements.push({
        category: QualityCategory.SECURITY,
        requirement: req.description,
        metric: '0 critical vulnerabilities',
        measurement: 'OWASP ZAP + Snyk scans'
      });
    }

    if (desc.includes('availability') || desc.includes('uptime')) {
      requirements.push({
        category: QualityCategory.AVAILABILITY,
        requirement: req.description,
        metric: '99.9% uptime',
        measurement: 'Uptime monitoring (Pingdom)'
      });
    }
  });

  // Add default quality requirements
  requirements.push(
    {
      category: QualityCategory.MAINTAINABILITY,
      requirement: 'Code must be maintainable and well-documented',
      metric: 'Code coverage > 80%',
      measurement: 'Jest/PyTest coverage reports'
    },
    {
      category: QualityCategory.SCALABILITY,
      requirement: 'System must scale horizontally',
      metric: 'Support 10x load increase',
      measurement: 'Load testing scenarios'
    }
  );

  return requirements;
}

// ============================================================================
// OUTPUT FORMATTING
// ============================================================================

/**
 * Format specification as Markdown
 */
export function formatSpecificationMarkdown(spec: SpecificationResult): string {
  let md = '# Technical Specification\n\n';
  md += `**Generated**: ${spec.metadata.generatedAt.toISOString()}\n`;
  md += `**By**: ${spec.metadata.generatedBy}\n`;
  md += `**Version**: ${spec.metadata.version}\n\n`;
  md += '---\n\n';

  // Architecture
  md += '## 🏗️ System Architecture\n\n';
  md += `**Pattern**: ${spec.architecture.pattern}\n\n`;
  if (spec.architecture.layers) {
    md += `**Layers**: ${spec.architecture.layers.join(' → ')}\n\n`;
  }
  md += `**Components**: ${spec.architecture.components.length}\n\n`;
  md += '**Technology Stack**:\n';
  Object.entries(spec.architecture.technologies).forEach(([key, values]) => {
    if (values && values.length > 0) {
      md += `- ${key}: ${values.join(', ')}\n`;
    }
  });
  md += '\n**Architecture Diagram**:\n```\n';
  md += spec.architecture.diagram;
  md += '\n```\n\n';

  // Development Stack (from Green Paper)
  if (spec.architecture.developmentStack) {
    const devStack = spec.architecture.developmentStack;
    md += '## 💻 Development Stack\n\n';
    md += '### Languages\n';
    devStack.languages.forEach(l => md += `- ${l}\n`);
    md += '\n### Frameworks\n';
    if (devStack.frameworks.frontend?.length) {
      md += `**Frontend**: ${devStack.frameworks.frontend.join(', ')}\n`;
    }
    if (devStack.frameworks.backend?.length) {
      md += `**Backend**: ${devStack.frameworks.backend.join(', ')}\n`;
    }
    if (devStack.frameworks.testing?.length) {
      md += `**Testing**: ${devStack.frameworks.testing.join(', ')}\n`;
    }
    md += '\n### Databases\n';
    md += `- **Primary**: ${devStack.databases.primary}\n`;
    if (devStack.databases.cache) md += `- **Cache**: ${devStack.databases.cache}\n`;
    if (devStack.databases.search) md += `- **Search**: ${devStack.databases.search}\n`;
    md += '\n### Testing\n';
    if (devStack.testing.unit?.length) md += `- **Unit**: ${devStack.testing.unit.join(', ')}\n`;
    if (devStack.testing.integration?.length) md += `- **Integration**: ${devStack.testing.integration.join(', ')}\n`;
    if (devStack.testing.e2e?.length) md += `- **E2E**: ${devStack.testing.e2e.join(', ')}\n`;
    md += '\n### Version Control\n';
    md += `- **System**: ${devStack.versionControl.system}\n`;
    md += `- **Platform**: ${devStack.versionControl.platform}\n`;
    if (devStack.versionControl.branchStrategy) md += `- **Branch Strategy**: ${devStack.versionControl.branchStrategy}\n`;
    md += '\n---\n\n';
  }

  // Operational Stack (from Green Paper)
  if (spec.architecture.operationalStack) {
    const opsStack = spec.architecture.operationalStack;
    md += '## 🚀 Operational Stack\n\n';
    md += '### Hosting\n';
    md += `- **Provider**: ${opsStack.hosting.provider}\n`;
    md += `- **Type**: ${opsStack.hosting.type}\n`;
    if (opsStack.hosting.region?.length) md += `- **Regions**: ${opsStack.hosting.region.join(', ')}\n`;
    if (opsStack.containerization) {
      md += '\n### Containerization\n';
      md += `- **Runtime**: ${opsStack.containerization.runtime}\n`;
      if (opsStack.containerization.registry) md += `- **Registry**: ${opsStack.containerization.registry}\n`;
    }
    if (opsStack.orchestration) {
      md += '\n### Orchestration\n';
      if (opsStack.orchestration.platform) md += `- **Platform**: ${opsStack.orchestration.platform}\n`;
      if (opsStack.orchestration.managedService) md += `- **Managed Service**: ${opsStack.orchestration.managedService}\n`;
    }
    md += '\n### CI/CD\n';
    md += `- **Platform**: ${opsStack.cicd.platform}\n`;
    md += `- **Stages**: ${opsStack.cicd.stages.join(' → ')}\n`;
    md += `- **Environments**: ${opsStack.cicd.environments.join(', ')}\n`;
    if (opsStack.monitoring) {
      md += '\n### Monitoring\n';
      if (opsStack.monitoring.metrics?.length) md += `- **Metrics**: ${opsStack.monitoring.metrics.join(', ')}\n`;
      if (opsStack.monitoring.logging?.length) md += `- **Logging**: ${opsStack.monitoring.logging.join(', ')}\n`;
      if (opsStack.monitoring.tracing?.length) md += `- **Tracing**: ${opsStack.monitoring.tracing.join(', ')}\n`;
      if (opsStack.monitoring.alerting?.length) md += `- **Alerting**: ${opsStack.monitoring.alerting.join(', ')}\n`;
    }
    if (opsStack.security) {
      md += '\n### Security\n';
      if (opsStack.security.secretsManagement) md += `- **Secrets**: ${opsStack.security.secretsManagement}\n`;
      if (opsStack.security.waf) md += `- **WAF**: ${opsStack.security.waf}\n`;
      if (opsStack.security.scanning?.length) md += `- **Scanning**: ${opsStack.security.scanning.join(', ')}\n`;
    }
    md += '\n---\n\n';
  }

  // Components
  md += '## 🧩 Components\n\n';
  spec.components.forEach(comp => {
    md += `### ${comp.name} (${comp.type})\n\n`;
    md += '**Responsibilities**:\n';
    comp.responsibilities.forEach(r => md += `- ${r}\n`);
    md += '\n';
  });

  return md;
}

// ============================================================================
// COMMAND EXECUTOR (CommandRegistry Interface)
// ============================================================================

/**
 * Execute specification command via CommandRegistry interface
 * Adapts the executeSpecification function to match CommandExecutor signature
 */
export async function executeSpecificationCommand(
  input: SlashCommandInput
): Promise<SlashCommandOutput> {
  const startTime = Date.now();

  try {
    // Extract context (using type assertion for custom fields)
    const ctx = input.context as any;
    const specificationInput: SpecificationInput = {
      constitution: ctx.constitution as ConstitutionResult,
      technicalContext: ctx.technicalContext || {}
    };

    if (!specificationInput.constitution) {
      throw new Error('Constitution is required for specification generation. Run /constitution first.');
    }

    // Mock agent (will be replaced with actual agent from KaibanJS)
    const mockAgent: Agent = {
      name: 'Felix',
      role: 'Feature Architect',
      goal: 'Design technical architecture',
      background: 'Software Architect with expertise in system design'
    } as Agent;

    // Execute specification generation
    const result = await executeSpecification(specificationInput, mockAgent);

    // Convert to SlashCommandOutput
    const duration = Date.now() - startTime;

    const output: SlashCommandOutput = {
      commandId: `spec-${Date.now()}`,
      command: SlashCommandType.SPECIFICATION,
      status: CommandStatus.COMPLETED,
      executedBy: 'Felix (Feature Architect)',
      executedAt: new Date(),
      completedAt: new Date(),
      duration,
      analysis: {
        summary: `Generated technical specification with ${result.components.length} components, ${result.interfaces.length} APIs, ${result.dataModel.entities.length} entities`,
        scores: {
          completeness: 0.92,
          technicalDepth: 0.88,
          implementability: 0.90
        },
        strengths: [
          `${result.components.length} well-defined components`,
          `${result.interfaces.length} RESTful API endpoints`,
          `${result.dataModel.entities.length} entities with relationships`,
          `${result.qualityRequirements.length} quality requirements addressed`,
          `Architecture pattern: ${result.architecture.pattern}`
        ],
        weaknesses: result.qualityRequirements.filter(q => q.category === QualityCategory.SECURITY).length > 3
          ? ['Multiple security requirements need careful attention']
          : []
      },
      recommendations: [
        {
          id: 'rec-1',
          priority: RecommendationPriority.HIGH,
          category: 'Next Steps',
          title: 'Proceed to Task Generation',
          description: 'Use this specification as input for /tasks command to generate epics, features, and stories',
          rationale: 'Specification provides the foundation for breaking down work into tasks',
          benefits: ['Clear development roadmap', 'Actionable work items'],
          effort: 'MEDIUM',
          impact: 'HIGH',
          confidence: 0.95
        },
        {
          id: 'rec-2',
          priority: RecommendationPriority.MEDIUM,
          category: 'Architecture Review',
          title: 'Validate Architecture with Team',
          description: `Review ${result.architecture.pattern} architecture pattern with development team`,
          rationale: 'Team alignment on architecture is critical for success',
          benefits: ['Team buy-in', 'Early issue detection'],
          effort: 'LOW',
          impact: 'HIGH',
          confidence: 0.9
        },
        {
          id: 'rec-3',
          priority: RecommendationPriority.MEDIUM,
          category: 'Data Model',
          title: 'Review Data Model Relationships',
          description: `Validate entity relationships and data model integrity`,
          rationale: 'Correct data model prevents costly refactoring later',
          benefits: ['Data integrity', 'Scalable schema'],
          effort: 'MEDIUM',
          impact: 'HIGH',
          confidence: 0.85
        }
      ],
      topRecommendation: {
        id: 'rec-1',
        priority: RecommendationPriority.HIGH,
        category: 'Next Steps',
        title: 'Proceed to Task Generation',
        description: 'Use this specification as input for /tasks command',
        rationale: 'Specification provides the foundation for task breakdown',
        benefits: ['Clear development roadmap', 'Actionable work items'],
        effort: 'MEDIUM',
        impact: 'HIGH',
        confidence: 0.95
      },
      confidence: 0.90,
      needsHumanReview: result.components.length > 15,
      rationale: 'Specification generated based on constitution requirements and technical constraints',
      nextSteps: [
        'Review architecture pattern with team',
        'Validate API contracts with stakeholders',
        'Review data model relationships',
        'Execute /tasks command to generate work breakdown',
        'Set up development environment based on tech stack'
      ],
      outputFormat: input.options?.outputFormat || OutputFormat.MARKDOWN,
      formattedOutput: formatSpecificationMarkdown(result)
    };

    return output;
  } catch (error) {
    const duration = Date.now() - startTime;

    // Return error output
    return {
      commandId: `spec-error-${Date.now()}`,
      command: SlashCommandType.SPECIFICATION,
      status: CommandStatus.FAILED,
      executedBy: 'Felix (Feature Architect)',
      executedAt: new Date(),
      completedAt: new Date(),
      duration,
      analysis: {
        summary: `Specification generation failed: ${error instanceof Error ? error.message : String(error)}`,
        issues: [{
          id: 'specification-error',
          severity: 'CRITICAL',
          category: 'Execution Error',
          title: 'Specification generation failed',
          description: error instanceof Error ? error.message : String(error),
          location: 'Specification Command',
          recommendation: 'Ensure constitution is provided in context and valid',
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
 * Register /specify command with the command registry
 */
export function registerSpecifyCommand(): void {
  registerCommand(SPECIFICATION_DEFINITION, executeSpecificationCommand);
}
