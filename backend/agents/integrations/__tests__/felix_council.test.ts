/**
 * Felix Council Integration Tests
 *
 * Week 52 Day 5: Tests for Felix agent integration with LLM Council
 */

import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import {
    LLMCouncilClient,
    FelixCouncilIntegration,
    CouncilDecision,
    ArchitectureContext,
    QuickDecisionResponse,
    felixProposeArchitecture
} from '../felix_council';

// Mock axios
const mockAxios = new MockAdapter(axios);

// ============================================================================
// TEST DATA
// ============================================================================

const mockCouncilDecision: CouncilDecision = {
    session_id: 'test-session-id',
    final_decision: 'Use microservices architecture with API gateway',
    confidence: 0.85,
    consensus_level: 78.5,
    dissenting_opinions: null,
    chairman_model: 'deepseek-r1:latest'
};

const mockQuickDecisionResponse: QuickDecisionResponse = {
    session_id: 'test-session-id',
    decision: mockCouncilDecision,
    consensus_level: 78.5,
    response_count: 6,
    review_count: 30,
    message: 'Council decision complete with 78.5% consensus'
};

const simpleContext: ArchitectureContext = {
    requirements: ['scalability', 'reliability'],
    constraints: ['budget'],
    current_stack: ['postgresql', 'redis'],
    complexity: 5,
    impact: 'low'
};

const complexContext: ArchitectureContext = {
    requirements: [
        'scalability', 'reliability', 'security', 'performance',
        'maintainability', 'observability', 'resilience',
        'cost-efficiency', 'developer-experience', 'testability',
        'documentation'
    ],
    constraints: [
        'budget', 'timeline', 'team-size', 'tech-stack',
        'compliance', 'legacy-integration'
    ],
    current_stack: [
        'postgresql', 'redis', 'kafka', 'elasticsearch',
        'docker', 'kubernetes', 'react', 'nodejs',
        'python', 'fastapi', 'nginx', 'grafana'
    ],
    complexity: 9,
    impact: 'high'
};

// ============================================================================
// LLMCOUNCILCLIENT TESTS
// ============================================================================

describe('LLMCouncilClient', () => {
    let client: LLMCouncilClient;

    beforeEach(() => {
        client = new LLMCouncilClient('http://localhost:8000');
        mockAxios.reset();
    });

    afterEach(() => {
        mockAxios.reset();
    });

    test('should make quick decision request successfully', async () => {
        // Setup mock
        mockAxios.onPost('/api/council/quick').reply(200, mockQuickDecisionResponse);

        // Execute
        const result = await client.quickDecision({
            question: 'What architecture should we use?',
            context: { requirements: ['scalability'] },
            decision_type: 'architecture',
            agent_id: 'felix',
            chairman_model: 'deepseek-r1:latest'
        });

        // Verify
        expect(result.session_id).toBe('test-session-id');
        expect(result.decision.final_decision).toBe(mockCouncilDecision.final_decision);
        expect(result.consensus_level).toBe(78.5);
        expect(result.response_count).toBe(6);
    });

    test('should handle API errors gracefully', async () => {
        // Setup mock error
        mockAxios.onPost('/api/council/quick').reply(500, {
            detail: 'Ollama service unavailable'
        });

        // Execute & Verify
        await expect(
            client.quickDecision({
                question: 'Test question',
                context: {},
                decision_type: 'architecture',
                agent_id: 'felix'
            })
        ).rejects.toThrow('Council API error: Ollama service unavailable');
    });

    test('should perform health check successfully', async () => {
        // Setup mock
        mockAxios.onGet('/api/council/sessions').reply(200, {
            sessions: [],
            total: 0,
            page: 1,
            page_size: 1
        });

        // Execute
        const isHealthy = await client.healthCheck();

        // Verify
        expect(isHealthy).toBe(true);
    });

    test('should return false for health check when API unavailable', async () => {
        // Setup mock error
        mockAxios.onGet('/api/council/sessions').networkError();

        // Execute
        const isHealthy = await client.healthCheck();

        // Verify
        expect(isHealthy).toBe(false);
    });
});

// ============================================================================
// FELIXCOUNCILINTEGRATION TESTS
// ============================================================================

describe('FelixCouncilIntegration', () => {
    let felixCouncil: FelixCouncilIntegration;

    beforeEach(() => {
        felixCouncil = new FelixCouncilIntegration('http://localhost:8000');
        mockAxios.reset();
    });

    afterEach(() => {
        mockAxios.reset();
    });

    // ========================================================================
    // TEST 1: Architecture Decision
    // ========================================================================

    test('should make architecture decision using council', async () => {
        // Setup mock
        mockAxios.onPost('/api/council/quick').reply(200, mockQuickDecisionResponse);

        // Execute
        const decision = await felixCouncil.makeArchitectureDecision(
            'What architecture should we use for microservices?',
            complexContext
        );

        // Verify
        expect(decision.final_decision).toBe(mockCouncilDecision.final_decision);
        expect(decision.confidence).toBe(0.85);
        expect(decision.consensus_level).toBe(78.5);

        // Verify request was made with correct parameters
        const request = JSON.parse(mockAxios.history.post[0].data);
        expect(request.question).toContain('architecture');
        expect(request.decision_type).toBe('architecture');
        expect(request.agent_id).toBe('felix');
        expect(request.chairman_model).toBe('deepseek-r1:latest');
    });

    // ========================================================================
    // TEST 2: Council Threshold Logic
    // ========================================================================

    test('should use council for high impact decisions', () => {
        // High impact always uses council
        const shouldUse = felixCouncil.shouldUseCouncil(5, 'high');
        expect(shouldUse).toBe(true);
    });

    test('should use council for medium impact with high complexity', () => {
        // Medium impact + complexity >= 7 uses council
        const shouldUse = felixCouncil.shouldUseCouncil(7, 'medium');
        expect(shouldUse).toBe(true);
    });

    test('should NOT use council for medium impact with low complexity', () => {
        // Medium impact + complexity < 7 does NOT use council
        const shouldUse = felixCouncil.shouldUseCouncil(6, 'medium');
        expect(shouldUse).toBe(false);
    });

    test('should NOT use council for low impact decisions', () => {
        // Low impact never uses council (Felix decides alone)
        const shouldUse = felixCouncil.shouldUseCouncil(10, 'low');
        expect(shouldUse).toBe(false);
    });

    // ========================================================================
    // TEST 3: Complexity Calculation
    // ========================================================================

    test('should calculate complexity correctly for simple context', () => {
        const complexity = felixCouncil.calculateComplexity(simpleContext);

        // Base 5 + 0 (req <= 5) + 0 (constraints <= 2) + 0 (stack <= 10) = 5
        expect(complexity).toBe(5);
    });

    test('should calculate complexity correctly for complex context', () => {
        const complexity = felixCouncil.calculateComplexity(complexContext);

        // Base 5 + 2 (req > 10) + 2 (constraints > 5) + 1 (stack > 10) = 10
        expect(complexity).toBe(10);
    });

    test('should cap complexity at 10', () => {
        const extremeContext: ArchitectureContext = {
            requirements: Array(50).fill('requirement'),
            constraints: Array(50).fill('constraint'),
            current_stack: Array(50).fill('tech'),
        };

        const complexity = felixCouncil.calculateComplexity(extremeContext);
        expect(complexity).toBe(10); // Capped
    });

    // ========================================================================
    // TEST 4: Impact Assessment
    // ========================================================================

    test('should assess impact as HIGH when affects core and multiple services', () => {
        const impact = felixCouncil.assessImpact(
            true,  // affectsCore
            true,  // affectsMultipleServices
            true   // isReversible
        );
        expect(impact).toBe('high');
    });

    test('should assess impact as MEDIUM when affects core only', () => {
        const impact = felixCouncil.assessImpact(
            true,  // affectsCore
            false, // affectsMultipleServices
            true   // isReversible
        );
        expect(impact).toBe('medium');
    });

    test('should assess impact as MEDIUM when not reversible', () => {
        const impact = felixCouncil.assessImpact(
            false, // affectsCore
            false, // affectsMultipleServices
            false  // isReversible (!)
        );
        expect(impact).toBe('medium');
    });

    test('should assess impact as LOW for safe changes', () => {
        const impact = felixCouncil.assessImpact(
            false, // affectsCore
            false, // affectsMultipleServices
            true   // isReversible
        );
        expect(impact).toBe('low');
    });

    // ========================================================================
    // TEST 5: Fallback to Solo Decision
    // ========================================================================

    test('should fallback to solo decision when council unavailable', async () => {
        // Setup mock error (council unavailable)
        mockAxios.onGet('/api/council/sessions').networkError();
        mockAxios.onPost('/api/council/quick').networkError();

        // Execute felixProposeArchitecture (which checks health first)
        const result = await felixProposeArchitecture(
            {
                description: 'Build user authentication system',
                requirements: ['security', 'scalability'],
                constraints: ['time'],
                affectsCore: true,
                affectsMultipleServices: true,
                isReversible: false
            },
            ['postgresql', 'redis']
        );

        // Verify fallback to solo decision
        expect(result.method).toBe('solo');
        expect(result.architecture).toContain('Felix');
        expect(result.confidence).toBe(0.75); // Solo confidence
    });

    test('should use council when available for high-impact decisions', async () => {
        // Setup mocks
        mockAxios.onGet('/api/council/sessions').reply(200, { sessions: [] });
        mockAxios.onPost('/api/council/quick').reply(200, mockQuickDecisionResponse);

        // Execute
        const result = await felixProposeArchitecture(
            {
                description: 'Redesign core architecture',
                requirements: ['scalability', 'reliability'],
                constraints: ['budget'],
                affectsCore: true,
                affectsMultipleServices: true,
                isReversible: false
            },
            ['postgresql']
        );

        // Verify council was used
        expect(result.method).toBe('council');
        expect(result.architecture).toBe(mockCouncilDecision.final_decision);
        expect(result.confidence).toBe(0.85);
    });
});

// ============================================================================
// INTEGRATION SCENARIO TESTS
// ============================================================================

describe('Felix Council Integration Scenarios', () => {
    let felixCouncil: FelixCouncilIntegration;

    beforeEach(() => {
        felixCouncil = new FelixCouncilIntegration('http://localhost:8000');
        mockAxios.reset();
    });

    afterEach(() => {
        mockAxios.reset();
    });

    test('Scenario: Simple feature (low impact, low complexity) - Felix alone', async () => {
        // Context: Add logging to existing endpoint (low impact, low complexity)
        const result = await felixProposeArchitecture(
            {
                description: 'Add logging to user endpoint',
                requirements: ['observability'],
                constraints: [],
                affectsCore: false,
                affectsMultipleServices: false,
                isReversible: true
            },
            ['postgresql', 'redis']
        );

        // Verify Felix decided alone
        expect(result.method).toBe('solo');
    });

    test('Scenario: Core refactor (high impact, high complexity) - Council', async () => {
        // Setup mocks
        mockAxios.onGet('/api/council/sessions').reply(200, { sessions: [] });
        mockAxios.onPost('/api/council/quick').reply(200, mockQuickDecisionResponse);

        // Context: Refactor authentication system (high impact, high complexity)
        const result = await felixProposeArchitecture(
            {
                description: 'Refactor authentication system to use OAuth2',
                requirements: [
                    'security', 'scalability', 'maintainability',
                    'backward-compatibility', 'user-experience',
                    'integration', 'performance', 'monitoring'
                ],
                constraints: [
                    'no-downtime', 'existing-users', 'legacy-clients'
                ],
                affectsCore: true,
                affectsMultipleServices: true,
                isReversible: false
            },
            [
                'postgresql', 'redis', 'jwt', 'sessions',
                'oauth-client', 'user-service', 'api-gateway'
            ]
        );

        // Verify council was consulted
        expect(result.method).toBe('council');
        expect(result.confidence).toBeGreaterThan(0.7);
    });

    test('Scenario: Medium feature with council failure - Graceful fallback', async () => {
        // Setup mocks (council available but fails during decision)
        mockAxios.onGet('/api/council/sessions').reply(200, { sessions: [] });
        mockAxios.onPost('/api/council/quick').reply(500, {
            detail: 'Insufficient responses for consensus'
        });

        // Context: Add caching layer (medium impact, medium complexity)
        const result = await felixProposeArchitecture(
            {
                description: 'Add Redis caching layer',
                requirements: ['performance', 'scalability'],
                constraints: ['budget', 'timeline'],
                affectsCore: false,
                affectsMultipleServices: true,
                isReversible: true
            },
            ['postgresql', 'api']
        );

        // Verify fallback to solo decision
        expect(result.method).toBe('solo');
    });
});
