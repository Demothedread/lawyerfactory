/**
 * Orchestration Dashboard JavaScript
 * Handles the interactive functionality of the steampunk UI
 */

class OrchestrationDashboard {
    constructor() {
        this.dashboard = null;
        this.chatInterface = null;
        this.currentPhase = 'orchestration';
        this.activeAgents = [];
        this.progressBars = {
            research_progress: 0,
            writing_progress: 0,
            validation_progress: 0,
            overall_progress: 0
        };
        this.notifications = [];
        this.chatMessages = [];
        this.documentPreviews = {};
        this.agentStatus = {};

        this.initializeLLMConfig();
        this.loadSavedLLMConfig();

        this.initializeDashboard();
        this.setupEventListeners();
        this.setupLLMEventListeners();
        this.startPeriodicUpdates();
        this.initializeDashboard();
        this.setupEventListeners();
        this.startPeriodicUpdates();
    }

    async initializeDashboard() {
        try {
            // Import the dashboard and chat interface
            const { dashboard, chat_interface } = await import('/static/js/dashboard_integration.js');
            this.dashboard = dashboard;
            this.chatInterface = chat_interface;

            console.log('Orchestration Dashboard initialized successfully');
            this.addNotification('AI Maestro online and ready for collaboration', 'success');
            this.addChatMessage('AI Maestro', 'Greetings, esteemed legal practitioner! I am your AI Maestro, ready to orchestrate the creation of court-ready legal documents. How may I assist you today?', 'ai');

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.addNotification('Dashboard initialization failed', 'error');
        }
    }

    setupEventListeners() {
        // Chat input handling
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-message');

        if (chatInput && sendButton) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendChatMessage();
                }
            });

            sendButton.addEventListener('click', () => {
                this.sendChatMessage();
            });
        }

        // Action button handling
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('action-btn')) {
                const action = e.target.dataset.action;
                this.handleAction(action);
            }
        });

        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-button')) {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            }
        });

        // Agent node interactions
        document.addEventListener('click', (e) => {
            if (e.target.closest('.agent-node')) {
                const agentNode = e.target.closest('.agent-node');
                const agentName = agentNode.dataset.agent;
                this.handleAgentClick(agentName);
            }
        });
    }

    async sendChatMessage() {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput || !chatInput.value.trim()) return;

        const message = chatInput.value.trim();
        chatInput.value = '';

        // Add user message
        this.addChatMessage('User', message, 'user');

        // Process with AI Maestro
        if (this.chatInterface) {
            try {
                const response = await this.chatInterface.send_user_message(message);
                this.addChatMessage('AI Maestro', response, 'ai');
            } catch (error) {
                console.error('Chat processing error:', error);
                this.addChatMessage('AI Maestro', 'I apologize, but I encountered an error processing your message. Please try again.', 'ai');
            }
        } else {
            // Fallback response
            const response = await this.generateFallbackResponse(message);
            this.addChatMessage('AI Maestro', response, 'ai');
        }
    }

    async generateFallbackResponse(message) {
        const lowerMessage = message.toLowerCase();

        if (lowerMessage.includes('status') || lowerMessage.includes('progress')) {
            return await this.getStatusResponse();
        } else if (lowerMessage.includes('review') || lowerMessage.includes('show')) {
            return "I can help you review documents. Please specify which document you'd like to examine.";
        } else if (lowerMessage.includes('help')) {
            return "I'm here to help orchestrate your legal document creation. I can show you progress, review documents, handle objections, and guide you through the process.";
        } else {
            return "I'm processing your request. How else can I assist with your legal orchestration needs?";
        }
    }

    async getStatusResponse() {
        const overallProgress = this.progressBars.overall_progress;
        const activeAgents = this.activeAgents.length;

        return `**Current Status Report:**

⚙️ **Overall Progress:** ${overallProgress.toFixed(1)}% complete

🔧 **Active Agents:** ${activeAgents} agents currently working
${this.activeAgents.length > 0 ? '• ' + this.activeAgents.join(', ') : '• All agents idle'}

📊 **Progress Breakdown:**
• Research: ${this.progressBars.research_progress.toFixed(1)}%
• Writing: ${this.progressBars.writing_progress.toFixed(1)}%
• Validation: ${this.progressBars.validation_progress.toFixed(1)}%

🎭 **System Status:** ${overallProgress > 0 ? 'Processing in progress' : 'Ready for input'}

Would you like me to elaborate on any specific aspect?`;
    }

    addChatMessage(sender, message, type = 'info') {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Store in memory
        this.chatMessages.push({
            timestamp: Date.now(),
            sender,
            message,
            type
        });

        // Keep only last 50 messages
        if (this.chatMessages.length > 50) {
            this.chatMessages = this.chatMessages.slice(-50);
        }
    }

    addNotification(message, type = 'info') {
        const container = document.getElementById('notifications-container');
        if (!container) return;

        const notificationDiv = document.createElement('div');
        notificationDiv.className = `notification-item ${type}`;
        notificationDiv.textContent = message;

        container.appendChild(notificationDiv);

        // Store in memory
        this.notifications.push({
            timestamp: Date.now(),
            message,
            type
        });

        // Keep only last 10 notifications
        if (this.notifications.length > 10) {
            this.notifications = this.notifications.slice(-10);
            // Also remove from DOM
            while (container.children.length > 10) {
                container.removeChild(container.firstChild);
            }
        }

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notificationDiv.parentNode) {
                notificationDiv.remove();
            }
        }, 10000);
    }

    async updateProgress(component, progress) {
        this.progressBars[component] = Math.max(0, Math.min(1, progress));

        const progressBar = document.getElementById(`${component}`);
        const progressText = document.getElementById(`${component}-text`);

        if (progressBar) {
            progressBar.style.width = `${progress * 100}%`;
        }

        if (progressText) {
            progressText.textContent = `${Math.round(progress * 100)}%`;
        }

        // Update overall progress
        this.updateOverallProgress();

        // Trigger mechanical effects
        await this.triggerMechanicalEffects(component, progress);
    }

    updateOverallProgress() {
        const totalProgress = Object.values(this.progressBars).reduce((sum, p) => sum + p, 0);
        const overallProgress = totalProgress / Object.keys(this.progressBars).length;

        this.progressBars.overall_progress = overallProgress;
        this.updateProgress('overall_progress', overallProgress);
    }

    async triggerMechanicalEffects(component, progress) {
        // Trigger visual effects based on progress
        if (progress > 0.8) {
            this.showMechanicalEffect('steam-effect');
            this.showMechanicalEffect('gear-animations');
        } else if (progress > 0.5) {
            this.showMechanicalEffect('lever-effect');
        } else if (progress > 0.2) {
            this.showMechanicalEffect('light-effect');
        }
    }

    showMechanicalEffect(effectName) {
        const effect = document.getElementById(effectName);
        if (effect) {
            effect.style.display = 'block';
            setTimeout(() => {
                effect.style.display = 'none';
            }, 3000);
        }
    }

    async activateAgent(agentName) {
        if (!this.activeAgents.includes(agentName)) {
            this.activeAgents.push(agentName);
        }

        this.agentStatus[agentName] = 'active';

        // Update UI
        const agentNode = document.querySelector(`[data-agent="${agentName}"]`);
        if (agentNode) {
            agentNode.classList.add('active');
            const statusElement = agentNode.querySelector('.agent-status');
            if (statusElement) {
                statusElement.textContent = 'ACTIVE';
                statusElement.classList.add('active');
            }
        }

        this.addNotification(`Agent ${agentName} activated`, 'success');
    }

    async deactivateAgent(agentName) {
        if (this.activeAgents.includes(agentName)) {
            this.activeAgents = this.activeAgents.filter(name => name !== agentName);
        }

        this.agentStatus[agentName] = 'idle';

        // Update UI
        const agentNode = document.querySelector(`[data-agent="${agentName}"]`);
        if (agentNode) {
            agentNode.classList.remove('active');
            const statusElement = agentNode.querySelector('.agent-status');
            if (statusElement) {
                statusElement.textContent = 'IDLE';
                statusElement.classList.remove('active');
            }
        }
    }

    async handleAction(action) {
        switch (action) {
            case 'review-outline':
                this.addChatMessage('AI Maestro', 'Opening Skeletal Outline for review. This master document contains your Statement of Facts and Causes of Action. Please review and provide any objections or approvals.', 'ai');
                this.switchTab('skeletal-outline');
                break;

            case 'review-claims':
                this.addChatMessage('AI Maestro', 'Displaying Claims Matrix. This shows all identified legal claims with supporting elements. Review for completeness and accuracy.', 'ai');
                this.switchTab('claims-matrix');
                break;

            case 'review-facts':
                this.addChatMessage('AI Maestro', 'Showing Fact Matrix. This contains all relevant facts organized by category. Check for objectivity and completeness.', 'ai');
                this.switchTab('fact-matrix');
                break;

            case 'approve':
                await this.handleApproval();
                break;

            case 'objection':
                await this.handleObjection();
                break;

            default:
                this.addNotification(`Unknown action: ${action}`, 'warning');
        }
    }

    async handleApproval() {
        this.addChatMessage('AI Maestro', 'Excellent! Your approval has been noted and the system will proceed to the next phase of orchestration.', 'ai');
        this.addNotification('User approval received - proceeding with orchestration', 'success');

        // Update progress
        await this.updateProgress('overall_progress', 1.0);
    }

    async handleObjection() {
        const objection = prompt('Please describe your objection:');
        if (objection) {
            this.addChatMessage('User', `I object to: ${objection}`, 'user');
            this.addChatMessage('AI Maestro', 'I understand your objection and have initiated a research loop to address your concerns. The relevant agents will analyze and update the documents accordingly.', 'ai');
            this.addNotification('Research loop initiated for user objection', 'warning');

            // Trigger research loop effects
            await this.triggerResearchLoop();
        }
    }

    async triggerResearchLoop() {
        await this.activateAgent('rules_of_law');
        await this.activateAgent('issuespotter');
        await this.activateAgent('caselaw_researcher');

        await this.updateProgress('research_progress', 0.1);

        // Simulate research process
        setTimeout(() => this.updateProgress('research_progress', 0.5), 2000);
        setTimeout(() => this.updateProgress('research_progress', 0.8), 4000);
        setTimeout(() => this.updateProgress('research_progress', 1.0), 6000);
        setTimeout(() => this.completeResearchLoop(), 8000);
    }

    async completeResearchLoop() {
        await this.deactivateAgent('rules_of_law');
        await this.deactivateAgent('issuespotter');
        await this.deactivateAgent('caselaw_researcher');

        this.addChatMessage('AI Maestro', 'Research loop completed. Documents have been updated based on your objection. Please review the revised materials.', 'ai');
        this.addNotification('Research loop completed - documents updated', 'success');
    }

    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });

        // Show selected tab
        const selectedTab = document.getElementById(`${tabName}-content`);
        if (selectedTab) {
            selectedTab.classList.add('active');
        }

        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });

        const selectedButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (selectedButton) {
            selectedButton.classList.add('active');
        }
    }

    handleAgentClick(agentName) {
        const status = this.agentStatus[agentName] || 'idle';
        const statusText = status === 'active' ? 'Currently active and processing' : 'Currently idle - click to activate';

        this.addChatMessage('AI Maestro', `Agent ${agentName}: ${statusText}`, 'ai');
    }

    startPeriodicUpdates() {
        // Simulate periodic updates for demo purposes
        setInterval(() => {
            this.simulatePeriodicUpdates();
        }, 5000);
    }

    simulatePeriodicUpdates() {
        // Simulate random progress updates for demo
        const components = Object.keys(this.progressBars);
        const randomComponent = components[Math.floor(Math.random() * components.length)];
        const currentProgress = this.progressBars[randomComponent];

        if (currentProgress < 1.0 && Math.random() < 0.3) {
            const newProgress = Math.min(1.0, currentProgress + Math.random() * 0.1);
            this.updateProgress(randomComponent, newProgress);
        }
    }
    // LLM Configuration Methods
    initializeLLMConfig() {
        // LLM Configuration
        this.llmConfig = {
            provider: 'openai',
            model: 'gpt-4o',
            temperature: 0.7,
            maxTokens: 4000
        };
        this.llmProviders = {
            openai: {
                name: 'OpenAI',
                models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                baseUrl: 'https://api.openai.com/v1'
            },
            anthropic: {
                name: 'Anthropic',
                models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
                baseUrl: 'https://api.anthropic.com'
            },
            google: {
                name: 'Google',
                models: ['gemini-pro', 'gemini-pro-vision'],
                baseUrl: 'https://generativelanguage.googleapis.com'
            },
            azure: {
                name: 'Azure OpenAI',
                models: ['gpt-4', 'gpt-35-turbo'],
                baseUrl: null // Requires custom endpoint
            },
            local: {
                name: 'Local Model',
                models: ['llama-2-7b', 'llama-2-13b', 'codellama'],
                baseUrl: 'http://localhost:11434'
            }
        };
    }

    setupLLMEventListeners() {
        // LLM Provider change handler
        const providerSelect = document.getElementById('llm-provider');
        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                this.handleProviderChange(e.target.value);
            });
        }

        // LLM Model change handler
        const modelSelect = document.getElementById('llm-model');
        if (modelSelect) {
            modelSelect.addEventListener('change', (e) => {
                this.llmConfig.model = e.target.value;
                this.addNotification(`Model changed to ${e.target.value}`, 'info');
            });
        }

        // Temperature slider handler
        const tempSlider = document.getElementById('llm-temperature');
        const tempValue = document.getElementById('temperature-value');
        if (tempSlider && tempValue) {
            tempSlider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                this.llmConfig.temperature = value;
                tempValue.textContent = value.toFixed(1);
            });
        }

        // Max tokens input handler
        const maxTokensInput = document.getElementById('llm-max-tokens');
        if (maxTokensInput) {
            maxTokensInput.addEventListener('change', (e) => {
                const value = parseInt(e.target.value);
                if (value >= 100 && value <= 32000) {
                    this.llmConfig.maxTokens = value;
                    this.addNotification(`Max tokens set to ${value}`, 'info');
                } else {
                    e.target.value = this.llmConfig.maxTokens;
                    this.addNotification('Max tokens must be between 100 and 32,000', 'warning');
                }
            });
        }

        // Apply config button handler
        const applyBtn = document.getElementById('apply-llm-config');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.applyLLMConfig();
            });
        }

        // Reset config button handler
        const resetBtn = document.getElementById('reset-llm-config');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetLLMConfig();
            });
        }
    }

    handleProviderChange(provider) {
        this.llmConfig.provider = provider;
        const modelSelect = document.getElementById('llm-model');

        if (modelSelect && this.llmProviders[provider]) {
            // Update available models for the selected provider
            const models = this.llmProviders[provider].models;
            modelSelect.innerHTML = models.map(model =>
                `<option value="${model}">${model}</option>`
            ).join('');

            // Set default model for the provider
            this.llmConfig.model = models[0];
            this.addNotification(`Switched to ${this.llmProviders[provider].name} provider`, 'success');
        }
    }

    async applyLLMConfig() {
        try {
            // Validate configuration
            if (!this.llmConfig.provider || !this.llmConfig.model) {
                throw new Error('Provider and model are required');
            }

            // Update LLM status
            this.updateLLMStatus('Applying configuration...', 'busy');

            // Simulate API call to apply configuration
            await this.delay(1000);

            // Save configuration to localStorage
            localStorage.setItem('lawyerfactory-llm-config', JSON.stringify(this.llmConfig));

            // Update UI
            this.updateLLMStatus('Configuration applied successfully', 'success');
            this.addNotification('LLM configuration applied successfully', 'success');

            // Update chat interface with new config if available
            if (this.chatInterface && this.chatInterface.updateConfig) {
                await this.chatInterface.updateConfig(this.llmConfig);
            }

        } catch (error) {
            console.error('Failed to apply LLM configuration:', error);
            this.updateLLMStatus('Configuration failed', 'error');
            this.addNotification(`Failed to apply configuration: ${error.message}`, 'error');
        }
    }

    resetLLMConfig() {
        // Reset to default configuration
        this.llmConfig = {
            provider: 'openai',
            model: 'gpt-4o',
            temperature: 0.7,
            maxTokens: 4000
        };

        // Update UI elements
        const providerSelect = document.getElementById('llm-provider');
        const modelSelect = document.getElementById('llm-model');
        const tempSlider = document.getElementById('llm-temperature');
        const tempValue = document.getElementById('temperature-value');
        const maxTokensInput = document.getElementById('llm-max-tokens');

        if (providerSelect) providerSelect.value = this.llmConfig.provider;
        if (modelSelect) this.handleProviderChange(this.llmConfig.provider);
        if (tempSlider) tempSlider.value = this.llmConfig.temperature;
        if (tempValue) tempValue.textContent = this.llmConfig.temperature.toFixed(1);
        if (maxTokensInput) maxTokensInput.value = this.llmConfig.maxTokens;

        this.updateLLMStatus('Configuration reset to defaults', 'ready');
        this.addNotification('LLM configuration reset to defaults', 'info');
    }

    updateLLMStatus(message, status) {
        const statusElement = document.getElementById('llm-status-text');
        const indicatorElement = document.getElementById('llm-connection-status');

        if (statusElement) statusElement.textContent = message;

        if (indicatorElement) {
            indicatorElement.className = 'status-indicator';
            switch (status) {
                case 'success':
                    indicatorElement.classList.add('status-online');
                    indicatorElement.textContent = '🟢';
                    break;
                case 'busy':
                    indicatorElement.classList.add('status-busy');
                    indicatorElement.textContent = '🟡';
                    break;
                case 'error':
                    indicatorElement.classList.add('status-error');
                    indicatorElement.textContent = '🔴';
                    break;
                default:
                    indicatorElement.textContent = '⚪';
            }
        }
    }

    loadSavedLLMConfig() {
        try {
            const saved = localStorage.getItem('lawyerfactory-llm-config');
            if (saved) {
                const savedConfig = JSON.parse(saved);
                this.llmConfig = { ...this.llmConfig, ...savedConfig };
                this.addNotification('Loaded saved LLM configuration', 'info');
            }
        } catch (error) {
            console.error('Failed to load saved LLM configuration:', error);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    getLLMConfigSummary() {
        const provider = this.llmProviders[this.llmConfig.provider];
        return {
            provider: provider ? provider.name : 'Unknown',
            model: this.llmConfig.model,
            temperature: this.llmConfig.temperature,
            maxTokens: this.llmConfig.maxTokens
        };
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.orchestrationDashboard = new OrchestrationDashboard();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrchestrationDashboard;
}