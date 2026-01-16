/**
 * LLM Configuration Module
 * Centralized LLM provider and model management system
 * Supports multiple providers: OpenAI, Anthropic, Google, Azure, Local
 */

class LLMConfigManager {
    constructor() {
        this.config = {
            provider: 'openai',
            model: 'gpt-4o',
            temperature: 0.7,
            maxTokens: 4000,
            apiKey: null,
            customEndpoint: null
        };

        this.providers = {
            openai: {
                name: 'OpenAI',
                models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                baseUrl: 'https://api.openai.com/v1',
                requiresApiKey: true,
                modelPricing: {
                    'gpt-4o': { input: 0.005, output: 0.015 },
                    'gpt-4-turbo': { input: 0.01, output: 0.03 },
                    'gpt-3.5-turbo': { input: 0.0015, output: 0.002 }
                }
            },
            anthropic: {
                name: 'Anthropic',
                models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
                baseUrl: 'https://api.anthropic.com',
                requiresApiKey: true,
                modelPricing: {
                    'claude-3-opus': { input: 0.015, output: 0.075 },
                    'claude-3-sonnet': { input: 0.003, output: 0.015 },
                    'claude-3-haiku': { input: 0.00025, output: 0.00125 }
                }
            },
            google: {
                name: 'Google',
                models: ['gemini-pro', 'gemini-pro-vision'],
                baseUrl: 'https://generativelanguage.googleapis.com',
                requiresApiKey: true,
                modelPricing: {
                    'gemini-pro': { input: 0.00025, output: 0.0005 },
                    'gemini-pro-vision': { input: 0.00025, output: 0.0005 }
                }
            },
            azure: {
                name: 'Azure OpenAI',
                models: ['gpt-4', 'gpt-35-turbo'],
                baseUrl: null, // Requires custom endpoint
                requiresApiKey: true,
                requiresEndpoint: true,
                modelPricing: {
                    'gpt-4': { input: 0.03, output: 0.06 },
                    'gpt-35-turbo': { input: 0.0015, output: 0.002 }
                }
            },
            local: {
                name: 'Local Model',
                models: ['llama-2-7b', 'llama-2-13b', 'codellama'],
                baseUrl: 'http://localhost:11434',
                requiresApiKey: false,
                modelPricing: null // No cost for local models
            }
        };

        this.eventListeners = [];
        this.loadSavedConfig();
    }

    // Configuration Management
    updateConfig(newConfig) {
        const oldConfig = { ...this.config };
        this.config = { ...this.config, ...newConfig };

        // Validate configuration
        if (!this.validateConfig()) {
            this.config = oldConfig;
            throw new Error('Invalid LLM configuration');
        }

        this.saveConfig();
        this.notifyListeners('configChanged', this.config);
        return this.config;
    }

    getConfig() {
        return { ...this.config };
    }

    resetConfig() {
        this.config = {
            provider: 'openai',
            model: 'gpt-4o',
            temperature: 0.7,
            maxTokens: 4000,
            apiKey: null,
            customEndpoint: null
        };
        this.saveConfig();
        this.notifyListeners('configReset', this.config);
        return this.config;
    }

    // Provider Management
    getAvailableProviders() {
        return Object.keys(this.providers);
    }

    getProviderInfo(provider) {
        return this.providers[provider] || null;
    }

    getAvailableModels(provider = null) {
        const targetProvider = provider || this.config.provider;
        const providerInfo = this.providers[targetProvider];
        return providerInfo ? providerInfo.models : [];
    }

    setProvider(provider) {
        if (!this.providers[provider]) {
            throw new Error(`Unknown provider: ${provider}`);
        }

        const oldProvider = this.config.provider;
        this.config.provider = provider;

        // Update to first available model for new provider
        const availableModels = this.getAvailableModels(provider);
        if (availableModels.length > 0 && !availableModels.includes(this.config.model)) {
            this.config.model = availableModels[0];
        }

        this.saveConfig();
        this.notifyListeners('providerChanged', {
            oldProvider,
            newProvider: provider,
            availableModels
        });

        return this.config;
    }

    setModel(model) {
        const availableModels = this.getAvailableModels();
        if (!availableModels.includes(model)) {
            throw new Error(`Model ${model} not available for provider ${this.config.provider}`);
        }

        const oldModel = this.config.model;
        this.config.model = model;
        this.saveConfig();

        this.notifyListeners('modelChanged', {
            oldModel,
            newModel: model
        });

        return this.config;
    }

    // Validation
    validateConfig() {
        // Check if provider exists
        if (!this.providers[this.config.provider]) {
            return false;
        }

        // Check if model is available for provider
        const availableModels = this.getAvailableModels();
        if (!availableModels.includes(this.config.model)) {
            return false;
        }

        // Validate temperature range
        if (this.config.temperature < 0 || this.config.temperature > 2) {
            return false;
        }

        // Validate max tokens
        if (this.config.maxTokens < 100 || this.config.maxTokens > 32000) {
            return false;
        }

        // Check API key requirement
        const providerInfo = this.providers[this.config.provider];
        if (providerInfo.requiresApiKey && !this.config.apiKey) {
            return false;
        }

        // Check custom endpoint requirement
        if (providerInfo.requiresEndpoint && !this.config.customEndpoint) {
            return false;
        }

        return true;
    }

    // Cost Estimation
    estimateCost(tokenCount, type = 'input') {
        const providerInfo = this.providers[this.config.provider];
        if (!providerInfo || !providerInfo.modelPricing) {
            return 0; // No cost for local models or unknown providers
        }

        const modelPricing = providerInfo.modelPricing[this.config.model];
        if (!modelPricing) {
            return 0;
        }

        const costPerToken = modelPricing[type] || modelPricing.input;
        return tokenCount * costPerToken;
    }

    // API Integration
    async testConnection() {
        try {
            const providerInfo = this.providers[this.config.provider];

            // For local models, just check if endpoint is reachable
            if (this.config.provider === 'local') {
                const response = await fetch(`${this.config.customEndpoint || providerInfo.baseUrl}/api/tags`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                return response.ok;
            }

            // For cloud providers, test with a simple request
            const testPayload = {
                model: this.config.model,
                messages: [{ role: 'user', content: 'Hello' }],
                max_tokens: 10
            };

            const headers = {
                'Content-Type': 'application/json'
            };

            if (this.config.apiKey) {
                if (this.config.provider === 'anthropic') {
                    headers['x-api-key'] = this.config.apiKey;
                } else {
                    headers['Authorization'] = `Bearer ${this.config.apiKey}`;
                }
            }

            const baseUrl = this.config.customEndpoint || providerInfo.baseUrl;
            const endpoint = this.config.provider === 'anthropic' ?
                `${baseUrl}/v1/messages` :
                `${baseUrl}/chat/completions`;

            const response = await fetch(endpoint, {
                method: 'POST',
                headers,
                body: JSON.stringify(testPayload)
            });

            return response.ok;
        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }

    // Persistence
    saveConfig() {
        try {
            // Don't save API keys to localStorage for security
            const configToSave = { ...this.config };
            delete configToSave.apiKey;

            localStorage.setItem('lawyerfactory-llm-config', JSON.stringify(configToSave));
        } catch (error) {
            console.error('Failed to save LLM configuration:', error);
        }
    }

    loadSavedConfig() {
        try {
            const saved = localStorage.getItem('lawyerfactory-llm-config');
            if (saved) {
                const savedConfig = JSON.parse(saved);
                this.config = { ...this.config, ...savedConfig };
                this.notifyListeners('configLoaded', this.config);
            }
        } catch (error) {
            console.error('Failed to load saved LLM configuration:', error);
        }
    }

    // Event System
    addEventListener(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    removeEventListener(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }

    notifyListeners(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event listener:', error);
                }
            });
        }
    }

    // Utility Methods
    getConfigSummary() {
        const provider = this.providers[this.config.provider];
        return {
            provider: provider ? provider.name : 'Unknown',
            model: this.config.model,
            temperature: this.config.temperature,
            maxTokens: this.config.maxTokens,
            hasApiKey: !!this.config.apiKey,
            hasCustomEndpoint: !!this.config.customEndpoint
        };
    }

    exportConfig() {
        return JSON.stringify(this.config, null, 2);
    }

    importConfig(configJson) {
        try {
            const importedConfig = JSON.parse(configJson);
            return this.updateConfig(importedConfig);
        } catch (error) {
            throw new Error('Invalid configuration JSON');
        }
    }
}

// Create global instance
window.LLMConfigManager = LLMConfigManager;
window.llmConfigManager = new LLMConfigManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMConfigManager;
}