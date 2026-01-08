"use strict";
/**
 * Ollama Client for LLM Integration
 *
 * Simple HTTP client for calling Ollama API directly.
 * Uses native fetch API (Node 18+).
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.OllamaClient = void 0;
exports.checkOllamaHealth = checkOllamaHealth;
exports.generateCompletion = generateCompletion;
/**
 * Standalone helper: Check Ollama health
 */
async function checkOllamaHealth(baseURL = 'http://localhost:11434') {
    try {
        const response = await fetch(`${baseURL}/api/tags`, {
            signal: AbortSignal.timeout(3000) // 3 second timeout
        });
        return response.ok;
    }
    catch {
        return false;
    }
}
/**
 * Standalone helper: Generate completion
 */
async function generateCompletion(options, baseURL = 'http://localhost:11434') {
    const request = {
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
            signal: AbortSignal.timeout(60000) // 60 second timeout
        });
        if (!response.ok) {
            throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        if (!data.response) {
            throw new Error('No response from Ollama');
        }
        return data.response.trim();
    }
    catch (error) {
        throw new Error(`Failed to generate from Ollama: ${error instanceof Error ? error.message : String(error)}`);
    }
}
class OllamaClient {
    baseURL;
    model;
    constructor(model = 'qwen2.5-coder:7b', baseURL = 'http://localhost:11434') {
        this.baseURL = baseURL;
        this.model = model;
    }
    /**
     * Generate completion from Ollama
     */
    async generate(prompt, options) {
        const request = {
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
            const data = await response.json();
            if (!data.response) {
                throw new Error('No response from Ollama');
            }
            return data.response.trim();
        }
        catch (error) {
            throw new Error(`Failed to generate from Ollama: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * Check if Ollama is available
     */
    async healthCheck() {
        return checkOllamaHealth(this.baseURL);
    }
    /**
     * Get model info
     */
    async getModelInfo() {
        try {
            const response = await fetch(`${this.baseURL}/api/show`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: this.model })
            });
            if (!response.ok)
                return null;
            return await response.json();
        }
        catch {
            return null;
        }
    }
}
exports.OllamaClient = OllamaClient;
