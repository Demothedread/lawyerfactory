// ===== LLM CONFIGURATION SYSTEM =====
let currentLLMProvider = "openai";
let llmConfig = {
    openai: {
        apiKey: "",
        model: "gpt-4",
        temperature: 0.7,
        maxTokens: 4000
    },
    ollama: {
        baseUrl: "http://localhost:11434",
        model: "llama2",
        temperature: 0.7,
        maxTokens: 4000
    },
    gemini: {
        apiKey: "",
        model: "gemini-pro",
        temperature: 0.7,
        maxTokens: 4000
    }
};

// Initialize LLM configuration
function initializeLLMConfig() {
    // Load saved configuration from localStorage
    const savedConfig = localStorage.getItem("lawyerFactoryLLMConfig");
    if (savedConfig) {
        try {
            const parsed = JSON.parse(savedConfig);
            llmConfig = { ...llmConfig, ...parsed.config };
            currentLLMProvider = parsed.currentProvider || "openai";
        } catch (error) {
            console.warn("Failed to load saved LLM config:", error);
        }
    }

    // Set up provider selection
    setupProviderSelection();

    // Set up configuration controls
    setupConfigurationControls();

    // Set up action buttons
    setupActionButtons();

    // Update UI with current configuration
    updateLLMConfigUI();
}

function setupProviderSelection() {
    // Provider selection buttons
    document.getElementById("openaiProvider").addEventListener("click", () => selectProvider("openai"));
    document.getElementById("ollamaProvider").addEventListener("click", () => selectProvider("ollama"));
    document.getElementById("geminiProvider").addEventListener("click", () => selectProvider("gemini"));
}

function setupConfigurationControls() {
    // Temperature sliders
    document.getElementById("openaiTemperature").addEventListener("input", function() {
        document.getElementById("openaiTempValue").textContent = this.value;
        llmConfig.openai.temperature = parseFloat(this.value);
    });

    document.getElementById("ollamaTemperature").addEventListener("input", function() {
        document.getElementById("ollamaTempValue").textContent = this.value;
        llmConfig.ollama.temperature = parseFloat(this.value);
    });

    document.getElementById("geminiTemperature").addEventListener("input", function() {
        document.getElementById("geminiTempValue").textContent = this.value;
        llmConfig.gemini.temperature = parseFloat(this.value);
    });

    // Input field changes
    document.getElementById("openaiApiKey").addEventListener("input", function() {
        llmConfig.openai.apiKey = this.value;
    });

    document.getElementById("ollamaBaseUrl").addEventListener("input", function() {
        llmConfig.ollama.baseUrl = this.value;
    });

    document.getElementById("geminiApiKey").addEventListener("input", function() {
        llmConfig.gemini.apiKey = this.value;
    });

    // Select changes
    document.getElementById("openaiModel").addEventListener("change", function() {
        llmConfig.openai.model = this.value;
    });

    document.getElementById("ollamaModel").addEventListener("change", function() {
        llmConfig.ollama.model = this.value;
    });

    document.getElementById("geminiModel").addEventListener("change", function() {
        llmConfig.gemini.model = this.value;
    });

    // Number inputs
    document.getElementById("openaiMaxTokens").addEventListener("input", function() {
        llmConfig.openai.maxTokens = parseInt(this.value);
    });

    document.getElementById("ollamaMaxTokens").addEventListener("input", function() {
        llmConfig.ollama.maxTokens = parseInt(this.value);
    });

    document.getElementById("geminiMaxTokens").addEventListener("input", function() {
        llmConfig.gemini.maxTokens = parseInt(this.value);
    });
}

function setupActionButtons() {
    document.getElementById("testConnectionBtn").addEventListener("click", testLLMConnection);
    document.getElementById("saveConfigBtn").addEventListener("click", saveLLMConfiguration);
    document.getElementById("resetConfigBtn").addEventListener("click", resetLLMConfiguration);
}

function selectProvider(provider) {
    // Update current provider
    currentLLMProvider = provider;

    // Update UI selection
    document.querySelectorAll(".provider-card").forEach(card => {
        card.classList.remove("selected");
    });

    document.getElementById(provider + "Provider").classList.add("selected");

    // Update checkmarks
    document.getElementById("openaiCheck").style.backgroundColor = provider === "openai" ? "#10b981" : "#6b7280";
    document.getElementById("ollamaCheck").style.backgroundColor = provider === "ollama" ? "#10b981" : "#6b7280";
    document.getElementById("geminiCheck").style.backgroundColor = provider === "gemini" ? "#10b981" : "#6b7280";

    // Show/hide configuration panels
    document.getElementById("openaiConfig").style.display = provider === "openai" ? "block" : "none";
    document.getElementById("ollamaConfig").style.display = provider === "ollama" ? "block" : "none";
    document.getElementById("geminiConfig").style.display = provider === "gemini" ? "block" : "none";

    // Update status display
    updateLLMConfigUI();
}

function updateLLMConfigUI() {
    // Update form fields with current configuration
    const config = llmConfig[currentLLMProvider];

    // Update input fields
    document.getElementById("openaiApiKey").value = llmConfig.openai.apiKey;
    document.getElementById("ollamaBaseUrl").value = llmConfig.ollama.baseUrl;
    document.getElementById("geminiApiKey").value = llmConfig.gemini.apiKey;

    // Update selects
    document.getElementById("openaiModel").value = llmConfig.openai.model;
    document.getElementById("ollamaModel").value = llmConfig.ollama.model;
    document.getElementById("geminiModel").value = llmConfig.gemini.model;

    // Update sliders and displays
    document.getElementById("openaiTemperature").value = llmConfig.openai.temperature;
    document.getElementById("openaiTempValue").textContent = llmConfig.openai.temperature;
    document.getElementById("ollamaTemperature").value = llmConfig.ollama.temperature;
    document.getElementById("ollamaTempValue").textContent = llmConfig.ollama.temperature;
    document.getElementById("geminiTemperature").value = llmConfig.gemini.temperature;
    document.getElementById("geminiTempValue").textContent = llmConfig.gemini.temperature;

    // Update number inputs
    document.getElementById("openaiMaxTokens").value = llmConfig.openai.maxTokens;
    document.getElementById("ollamaMaxTokens").value = llmConfig.ollama.maxTokens;
    document.getElementById("geminiMaxTokens").value = llmConfig.gemini.maxTokens;

    // Update status display
    document.getElementById("configProvider").textContent = currentLLMProvider.charAt(0).toUpperCase() + currentLLMProvider.slice(1);
    document.getElementById("configModel").textContent = config.model;
    document.getElementById("configRagStatus").textContent = "No"; // Will be updated when RAG is implemented

    // Update provider selection UI
    selectProvider(currentLLMProvider);
}

async function testLLMConnection() {
    const connectionLight = document.getElementById("connectionStatusLight");
    const connectionText = document.getElementById("connectionStatusText");

    connectionLight.style.backgroundColor = "#f59e0b"; // yellow/loading
    connectionText.textContent = "Testing...";

    try {
        const config = llmConfig[currentLLMProvider];
        let isConnected = false;

        // Test connection based on provider
        switch (currentLLMProvider) {
            case "openai":
                if (!config.apiKey) {
                    throw new Error("API key is required");
                }
                // Simple test request to OpenAI
                const openaiResponse = await fetch("/api/llm/test-connection", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        provider: "openai",
                        config: config
                    })
                });
                isConnected = openaiResponse.ok;
                break;

            case "ollama":
                // Test Ollama connection
                const ollamaResponse = await fetch(`${config.baseUrl}/api/tags`);
                isConnected = ollamaResponse.ok;
                break;

            case "gemini":
                if (!config.apiKey) {
                    throw new Error("API key is required");
                }
                // Test Gemini connection
                const geminiResponse = await fetch("/api/llm/test-connection", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        provider: "gemini",
                        config: config
                    })
                });
                isConnected = geminiResponse.ok;
                break;
        }

        if (isConnected) {
            connectionLight.style.backgroundColor = "#10b981"; // green/success
            connectionText.textContent = "Connected";
            showNotification("LLM connection successful!", "success");
        } else {
            throw new Error("Connection failed");
        }

    } catch (error) {
        connectionLight.style.backgroundColor = "#ef4444"; // red/error
        connectionText.textContent = "Failed";
        showNotification(`LLM connection failed: ${error.message}`, "error");
    }
}

function saveLLMConfiguration() {
    try {
        const configToSave = {
            currentProvider: currentLLMProvider,
            config: llmConfig,
            timestamp: new Date().toISOString()
        };

        localStorage.setItem("lawyerFactoryLLMConfig", JSON.stringify(configToSave));

        // Send configuration to backend
        fetch("/api/llm/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(configToSave)
        }).catch(error => {
            console.warn("Failed to save config to backend:", error);
        });

        showNotification("LLM configuration saved successfully!", "success");
    } catch (error) {
        showNotification("Failed to save configuration", "error");
    }
}

function resetLLMConfiguration() {
    if (confirm("Are you sure you want to reset the LLM configuration? This will clear all settings.")) {
        // Reset to defaults
        llmConfig = {
            openai: {
                apiKey: "",
                model: "gpt-4",
                temperature: 0.7,
                maxTokens: 4000
            },
            ollama: {
                baseUrl: "http://localhost:11434",
                model: "llama2",
                temperature: 0.7,
                maxTokens: 4000
            },
            gemini: {
                apiKey: "",
                model: "gemini-pro",
                temperature: 0.7,
                maxTokens: 4000
            }
        };

        currentLLMProvider = "openai";
        updateLLMConfigUI();

        // Clear localStorage
        localStorage.removeItem("lawyerFactoryLLMConfig");

        showNotification("LLM configuration reset to defaults", "info");
    }
}

// Initialize LLM config when DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
    // Initialize LLM config after a short delay to ensure all elements are loaded
    setTimeout(initializeLLMConfig, 100);
});

// Add CSS for provider selection
const style = document.createElement("style");
style.textContent = `
    .provider-card.selected {
        border-color: #10b981 !important;
        background: rgba(16, 185, 129, 0.1) !important;
    }
    .provider-card {
        transition: all 0.2s ease;
    }
    .provider-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
`;
document.head.appendChild(style);