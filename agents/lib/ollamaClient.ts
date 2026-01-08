/**
 * Ollama Client for LLM Integration
 *
 * Simple HTTP client for calling Ollama API directly.
 * Uses native fetch API (Node 18+).
 */

export interface OllamaRequest {
    model: string;
    prompt: string;
    stream?: boolean;
    options?: {
        temperature?: number;
        top_p?: number;
        top_k?: number;
        num_predict?: number;
    };
}

export interface OllamaResponse {
    model: string;
    created_at: string;
    response: string;
    done: boolean;
    context?: number[];
    total_duration?: number;
    load_duration?: number;
    prompt_eval_duration?: number;
    eval_duration?: number;
}

/**
 * Generation options for Ollama requests
 */
export interface GenerationOptions {
    model?: string;
    prompt: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    top_k?: number;
}

/**
 * Standalone helper: Check Ollama health
 */
export async function checkOllamaHealth(baseURL: string = 'http://localhost:11434'): Promise<boolean> {
    try {
        const response = await fetch(`${baseURL}/api/tags`, {
            signal: AbortSignal.timeout(3000)  // 3 second timeout
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Standalone helper: Generate completion
 */
export async function generateCompletion(options: GenerationOptions, baseURL: string = 'http://localhost:11434'): Promise<string> {
    const request: OllamaRequest = {
        model: options.model || 'qwen2.5-coder:7b',
        prompt: options.prompt,
        stream: false,
        options: {
            temperature: options.temperature ?? 0.7,
            top_p: options.top_p ?? 0.9,
            top_k: options.top_k,
            num_predict: options.max_tokens
        }
    };

    try {
        const response = await fetch(`${baseURL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request),
            signal: AbortSignal.timeout(60000)  // 60 second timeout
        });

        if (!response.ok) {
            throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json() as OllamaResponse;

        if (!data.response) {
            throw new Error('No response from Ollama');
        }

        return data.response.trim();
    } catch (error) {
        throw new Error(`Failed to generate from Ollama: ${error instanceof Error ? error.message : String(error)}`);
    }
}

export class OllamaClient {
    private baseURL: string;
    private model: string;

    constructor(model: string = 'qwen2.5-coder:7b', baseURL: string = 'http://localhost:11434') {
        this.baseURL = baseURL;
        this.model = model;
    }

    /**
     * Generate completion from Ollama
     */
    async generate(prompt: string, options?: OllamaRequest['options']): Promise<string> {
        const request: OllamaRequest = {
            model: this.model,
            prompt,
            stream: false,
            options: {
                temperature: 0.7,
                top_p: 0.9,
                ...options
            }
        };

        try {
            const response = await fetch(`${this.baseURL}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json() as OllamaResponse;

            if (!data.response) {
                throw new Error('No response from Ollama');
            }

            return data.response.trim();
        } catch (error) {
            throw new Error(`Failed to generate from Ollama: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Check if Ollama is available
     */
    async healthCheck(): Promise<boolean> {
        return checkOllamaHealth(this.baseURL);
    }

    /**
     * Get model info
     */
    async getModelInfo(): Promise<any | null> {
        try {
            const response = await fetch(`${this.baseURL}/api/show`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: this.model })
            });

            if (!response.ok) return null;
            return await response.json();
        } catch {
            return null;
        }
    }
}

