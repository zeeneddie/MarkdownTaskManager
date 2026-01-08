/**
 * Work Type Classifier
 *
 * LLM-based intelligent classification of work requests into work types.
 * Features:
 * - AI-powered classification using Ollama
 * - Confidence scoring (0.0 - 1.0)
 * - Graceful fallback to keyword matching
 * - User confirmation for low confidence (<0.8)
 */

import { generateCompletion, checkOllamaHealth } from './ollamaClient';
import { WorkType, type ClassificationResult } from '../types/WorkTypes';

// Re-export for convenience
export type { ClassificationResult };

/**
 * Prompt template for work type classification
 */
function createClassificationPrompt(description: string, context?: Record<string, any>): string {
  const contextStr = context ? `\n\n**Additional Context**:\n${JSON.stringify(context, null, 2)}` : '';

  return `You are an expert project manager specializing in work classification and routing.

# TASK
Classify the following work request into one of these 9 work types:

**Work Types**:
1. **PROJECT_DEFINITION** - Defining a new project from scratch (charter, vision, roadmap)
2. **NEW_FEATURE** - Adding new functionality or capabilities
3. **MAINTENANCE** - Updating dependencies, refactoring, technical debt, cleanup
4. **QUALITY_AUDIT** - Code review, security audit, quality assessment
5. **BUG** - Fixing errors, crashes, or incorrect behavior
6. **ENHANCEMENT** - Improving existing features (not new features)
7. **MIGRATION** - Moving to new technology, platform, or architecture
8. **QUALITY_IMPROVEMENT** - Addressing code smells, improving coverage, reducing complexity
9. **TESTING** - Creating or improving test suites

# WORK REQUEST
${description}${contextStr}

# CLASSIFICATION RULES
- PROJECT_DEFINITION: Use only for complete project setup (not individual features)
- NEW_FEATURE vs ENHANCEMENT: New = entirely new capability; Enhancement = improving existing
- MAINTENANCE vs QUALITY_IMPROVEMENT: Maintenance = dependencies/updates; Quality = code health
- BUG vs ENHANCEMENT: Bug = something broken; Enhancement = making working code better
- Consider the scope and intent carefully
- If uncertain between two types, choose the one with broader scope

# OUTPUT FORMAT
Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{
  "work_type": "WORK_TYPE_NAME",
  "confidence": 0.95,
  "reasoning": "Brief 1-2 sentence explanation of why this classification",
  "alternatives": [
    {
      "work_type": "ALTERNATIVE_TYPE",
      "confidence": 0.60
    }
  ]
}

IMPORTANT: Return ONLY the JSON object. No markdown code blocks, no additional text.`;
}

/**
 * Extract JSON from LLM response (handles markdown code blocks)
 */
function extractJSON(response: string): any {
  try {
    // Try parsing directly first
    return JSON.parse(response);
  } catch {
    // Look for JSON in markdown code blocks
    const jsonMatch = response.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1]);
    }

    // Look for JSON object pattern
    const objectMatch = response.match(/\{[\s\S]*\}/);
    if (objectMatch) {
      return JSON.parse(objectMatch[0]);
    }

    throw new Error('No valid JSON found in response');
  }
}

/**
 * Validate work type string
 */
function validateWorkType(workType: string): WorkType | null {
  const validTypes = Object.values(WorkType);
  if (validTypes.includes(workType as WorkType)) {
    return workType as WorkType;
  }
  return null;
}

/**
 * Classify work type using LLM
 */
export async function classifyWorkTypeWithLLM(
  description: string,
  context?: Record<string, any>
): Promise<ClassificationResult | null> {
  try {
    // Check Ollama health
    const isHealthy = await checkOllamaHealth();
    if (!isHealthy) {
      console.warn('[WorkTypeClassifier] Ollama not available, will use fallback');
      return null;
    }

    // Generate classification
    const prompt = createClassificationPrompt(description, context);
    const response = await generateCompletion({
      model: 'qwen2.5-coder:7b',
      prompt,
      temperature: 0.3,  // Lower temperature for consistent classification
      max_tokens: 500
    });

    // Extract and validate JSON
    const data = extractJSON(response);

    if (!data.work_type || typeof data.confidence !== 'number') {
      throw new Error('Invalid response format');
    }

    const workType = validateWorkType(data.work_type);
    if (!workType) {
      throw new Error(`Invalid work type: ${data.work_type}`);
    }

    // Validate alternatives
    const alternatives = (data.alternatives || [])
      .filter((alt: any) => validateWorkType(alt.work_type))
      .map((alt: any) => ({
        workType: validateWorkType(alt.work_type)!,
        confidence: alt.confidence
      }))
      .filter((alt: any) => alt.confidence > 0.3)  // Filter low-confidence alternatives
      .slice(0, 2);  // Keep top 2 alternatives

    const confidence = Math.max(0, Math.min(1, data.confidence));  // Clamp to [0, 1]
    const needsUserConfirmation = confidence < 0.8;

    return {
      workType,
      confidence,
      reasoning: data.reasoning || 'No reasoning provided',
      needsUserConfirmation,
      alternativeOptions: alternatives.length > 0 ? alternatives : undefined
    };

  } catch (error) {
    console.error('[WorkTypeClassifier] LLM classification failed:', error);
    return null;
  }
}

/**
 * Keyword-based fallback classification
 * (Extracted from existing workTypeRouter for consistency)
 */
const CLASSIFICATION_KEYWORDS: Record<WorkType, string[]> = {
  [WorkType.PROJECT_DEFINITION]: [
    'project', 'define project', 'new project', 'start project',
    'project setup', 'initialize', 'product vision', 'business case',
    'project charter', 'project plan', 'roadmap'
  ],
  [WorkType.NEW_FEATURE]: [
    'add', 'create', 'new', 'implement', 'build', 'develop',
    'feature', 'functionality', 'capability'
  ],
  [WorkType.MAINTENANCE]: [
    'update', 'upgrade', 'dependency', 'maintenance', 'refactor',
    'clean', 'organize', 'deprecate'
  ],
  [WorkType.QUALITY_AUDIT]: [
    'audit', 'review', 'analyze', 'inspect', 'check', 'quality',
    'security', 'performance', 'assessment'
  ],
  [WorkType.BUG]: [
    'bug', 'fix', 'error', 'issue', 'problem', 'crash', 'fails',
    'broken', 'not working', 'doesn\'t work'
  ],
  [WorkType.ENHANCEMENT]: [
    'improve', 'enhance', 'better', 'optimize', 'extend',
    'expand', 'modify', 'adjust'
  ],
  [WorkType.MIGRATION]: [
    'migrate', 'migration', 'move', 'transfer', 'upgrade to',
    'switch to', 'port', 'convert'
  ],
  [WorkType.QUALITY_IMPROVEMENT]: [
    'technical debt', 'code smell', 'complexity', 'duplication',
    'coverage', 'cleanup', 'improve quality'
  ],
  [WorkType.TESTING]: [
    'test', 'testing', 'unit test', 'integration test', 'e2e',
    'test coverage', 'test scenario'
  ]
};

/**
 * Fallback keyword-based classification
 */
export function classifyWorkTypeKeywords(description: string): ClassificationResult {
  const lowerDesc = description.toLowerCase();
  const scores: Partial<Record<WorkType, number>> = {};

  // Calculate scores for each work type
  for (const [workType, keywords] of Object.entries(CLASSIFICATION_KEYWORDS)) {
    scores[workType as WorkType] = keywords.filter(keyword =>
      lowerDesc.includes(keyword)
    ).length;
  }

  // Find work type with highest score
  const sorted = Object.entries(scores)
    .sort(([, a], [, b]) => (b || 0) - (a || 0));

  const topMatch = sorted[0];
  const secondMatch = sorted[1];

  // Calculate confidence based on score difference
  const topScore = topMatch?.[1] || 0;
  const secondScore = secondMatch?.[1] || 0;
  const totalScore = topScore + secondScore;

  let confidence = 0.5;  // Default medium confidence
  if (topScore > 0 && totalScore > 0) {
    // Confidence increases with score gap
    confidence = Math.min(0.75, 0.5 + (topScore - secondScore) / totalScore * 0.25);
  }

  const workType = (topScore > 0 ? topMatch[0] : WorkType.NEW_FEATURE) as WorkType;

  const alternatives = sorted
    .slice(1, 3)
    .filter(([, score]) => score > 0)
    .map(([wt, score]) => ({
      workType: wt as WorkType,
      confidence: Math.min(0.6, (score / totalScore) * 0.6)
    }));

  return {
    workType,
    confidence,
    reasoning: `Keyword-based classification (matched ${topScore} keywords)`,
    needsUserConfirmation: confidence < 0.8,
    alternativeOptions: alternatives.length > 0 ? alternatives : undefined
  };
}

/**
 * Main classification function with LLM + fallback
 */
export async function classifyWorkType(
  description: string,
  context?: Record<string, any>,
  useLLM: boolean = true
): Promise<ClassificationResult> {
  // Try LLM-based classification first
  if (useLLM) {
    const llmResult = await classifyWorkTypeWithLLM(description, context);
    if (llmResult) {
      return {
        ...llmResult,
        reasoning: `[AI] ${llmResult.reasoning}`
      };
    }
  }

  // Fallback to keyword-based classification
  const keywordResult = classifyWorkTypeKeywords(description);
  return {
    ...keywordResult,
    reasoning: `[Keywords] ${keywordResult.reasoning}`
  };
}

/**
 * Format classification result for user confirmation
 */
export function formatClassificationForUser(result: ClassificationResult): string {
  let message = `🤖 Work Type Classification\n\n`;
  message += `**Classified as**: ${result.workType}\n`;
  message += `**Confidence**: ${(result.confidence * 100).toFixed(1)}%\n`;
  message += `**Reasoning**: ${result.reasoning}\n`;

  if (result.alternativeOptions && result.alternativeOptions.length > 0) {
    message += `\n**Alternative Options**:\n`;
    result.alternativeOptions.forEach(alt => {
      message += `- ${alt.workType} (${(alt.confidence * 100).toFixed(1)}%)\n`;
    });
  }

  if (result.needsUserConfirmation) {
    message += `\n⚠️ Low confidence - please confirm or select different work type`;
  }

  return message;
}
