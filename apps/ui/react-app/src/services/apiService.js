/**
 * API service for connecting Briefcaser frontend to LawyerFactory backend
 * Handles REST API calls and Socket.IO connections for real-time updates
 */

import axios from "axios";
import { io } from "socket.io-client";

// API Configuration
const API_BASE_URL = "http://localhost:5000";
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// Socket.IO connection
let socket = null;

/**
 * Initialize Socket.IO connection for real-time updates
 */
export const initializeSocket = (onPhaseUpdate, onError) => {
  if (!socket) {
    socket = io(API_BASE_URL, {
      transports: ["websocket", "polling"],
      timeout: 20000,
    });

    socket.on("connect", () => {
      console.log("🔌 Connected to LawyerFactory backend");
    });

    socket.on("disconnect", () => {
      console.log("🔌 Disconnected from LawyerFactory backend");
    });

    socket.on("phase_progress_update", (data) => {
      console.log("📊 Phase progress update:", data);
      if (onPhaseUpdate) onPhaseUpdate(data);
    });

    socket.on("connect_error", (error) => {
      console.error("❌ Socket connection error:", error);
      if (onError) onError(error);
    });
  }
  return socket;
};

/**
 * Get the current socket instance
 */
export const getSocket = () => {
  return socket;
};

/**
 * Close the Socket.IO connection
 */
export const closeSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
    console.log("🔌 Socket connection closed");
  }
};

/**
 * Health check endpoint
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get("/api/health");
    return response.data;
  } catch (error) {
    console.error("Health check failed:", error);
    throw error;
  }
};

/**
 * Check if backend is available
 */
export const isBackendAvailable = async () => {
  try {
    const result = await healthCheck();
    return result.status === "healthy" || result.status === "ok";
  } catch (error) {
    console.warn("Backend health check failed:", error.message);
    return false;
  }
};

/**
 * Process legal intake form data
 * @param {Object} intakeData - The intake form data
 * @param {Object} settings - User settings including aiModel (LLM provider)
 */
export const processIntake = async (intakeData, settings = {}) => {
  try {
    const payload = {
      ...intakeData,
      llm_provider: settings.aiModel || 'gpt-4',
      research_mode: settings.researchMode !== undefined ? settings.researchMode : true,
      citation_validation: settings.citationValidation !== undefined ? settings.citationValidation : true,
      jurisdiction: settings.jurisdiction || 'federal',
      citation_style: settings.citationStyle || 'bluebook',
    };
    
    const response = await apiClient.post("/api/intake", payload);
    return response.data;
  } catch (error) {
    console.error("Intake processing failed:", error);
    throw error;
  }
};

/**
 * Upload documents for a case
 */
export const uploadCaseDocuments = async (caseId, files) => {
  try {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    const response = await apiClient.post(
      `/api/cases/${caseId}/documents`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Document upload failed:", error);
    throw error;
  }
};

/**
 * Start research phase for a case
 * @param {string} caseId - The case ID
 * @param {string} researchQuery - The research query
 * @param {Object} settings - User settings including aiModel (LLM provider)
 */
export const startResearch = async (caseId, researchQuery, settings = {}) => {
  try {
    const payload = {
      case_id: caseId,
      research_query: researchQuery,
      llm_provider: settings.aiModel || 'gpt-4',
      enhanced_mode: settings.researchMode !== undefined ? settings.researchMode : true,
      citation_validation: settings.citationValidation !== undefined ? settings.citationValidation : true,
    };
    
    const response = await apiClient.post("/api/research/start", payload);
    return response.data;
  } catch (error) {
    console.error("Research start failed:", error);
    throw error;
  }
};

/**
 * Get research status for a case
 */
export const getResearchStatus = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/research/status/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Research status check failed:", error);
    throw error;
  }
};

/**
 * Get research results for a case
 */
export const getResearchResults = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/research/results/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Research results fetch failed:", error);
    throw error;
  }
};

/**
 * Generate document outline for a case
 * @param {string} caseId - The case ID
 * @param {Object} settings - User settings including aiModel (LLM provider)
 */
export const generateOutline = async (caseId, settings = {}) => {
  try {
    const payload = {
      case_id: caseId,
      llm_provider: settings.aiModel || 'gpt-4',
      citation_style: settings.citationStyle || 'bluebook',
    };
    
    const response = await apiClient.post("/api/outline/generate", payload);
    return response.data;
  } catch (error) {
    console.error("Outline generation failed:", error);
    throw error;
  }
};

/**
 * Get outline generation status for a case
 */
export const getOutlineStatus = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/outline/status/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Outline status check failed:", error);
    throw error;
  }
};

/**
 * Start final orchestration phase for a case
 */
export const startFinalOrchestration = async (caseId) => {
  try {
    const response = await apiClient.post("/api/orchestration/start", {
      case_id: caseId,
    });
    return response.data;
  } catch (error) {
    console.error("Final orchestration start failed:", error);
    throw error;
  }
};

/**
 * Get final orchestration status for a case
 */
export const getOrchestrationStatus = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/orchestration/status/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Orchestration status check failed:", error);
    throw error;
  }
};

/**
 * Get final deliverables for a case
 */
export const getFinalDeliverables = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/orchestration/deliverables/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Final deliverables fetch failed:", error);
    throw error;
  }
};

/**
 * Upload documents using unified storage API
 */
export const uploadDocumentsUnified = async (
  files,
  caseId = "default",
  phase = "phaseA01_intake"
) => {
  try {
    const formData = new FormData();

    // Add files to form data
    files.forEach((file) => {
      formData.append("files", file);
    });

    // Add metadata
    formData.append("case_id", caseId);
    formData.append("phase", phase);

    const response = await apiClient.post("/api/storage/documents", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 60000, // 1 minute timeout for file uploads
    });

    return response.data;
  } catch (error) {
    console.error("Unified document upload failed:", error);
    throw error;
  }
};

/**
 * Retrieve document by ObjectID from unified storage
 */
export const getDocumentByObjectId = async (objectId) => {
  try {
    const response = await apiClient.get(`/api/storage/documents/${objectId}`);
    return response.data;
  } catch (error) {
    console.error("Document retrieval failed:", error);
    throw error;
  }
};

/**
 * Get all documents for a case from unified storage
 */
export const getCaseDocuments = async (caseId) => {
  try {
    const response = await apiClient.get(
      `/api/storage/cases/${caseId}/documents`
    );
    return response.data;
  } catch (error) {
    console.error("Case documents retrieval failed:", error);
    throw error;
  }
};

/**
 * Start a specific phase for a case
 * @param {string} phaseId - The phase ID (e.g., "phaseB02_drafting")
 * @param {string} caseId - The case ID
 * @param {Object} phaseData - Additional data for the phase
 */
export const startPhase = async (phaseId, caseId, phaseData = {}) => {
  try {
    const payload = {
      case_id: caseId,
      ...phaseData,
    };

    const response = await apiClient.post(`/api/phases/${phaseId}/start`, payload);
    return response.data;
  } catch (error) {
    console.error(`Phase ${phaseId} start failed:`, error);
    throw error;
  }
};

/**
 * Get claims matrix for a case
 */
export const getClaimsMatrix = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/claims/matrix/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Claims matrix fetch failed:", error);
    throw error;
  }
};

/**
 * Generate skeletal outline for a case
 */
export const generateSkeletalOutline = async (caseId, claimsMatrix = [], shotList = []) => {
  try {
    const payload = {
      case_id: caseId,
      claims_matrix: claimsMatrix,
      shot_list: shotList,
    };

    const response = await apiClient.post(`/api/outline/generate/${caseId}`, payload);
    return response.data;
  } catch (error) {
    console.error("Skeletal outline generation failed:", error);
    throw error;
  }
};

/**
 * Fetch LLM configuration from backend (includes environment variable defaults)
 */
export const fetchLLMConfig = async () => {
  try {
    const response = await apiClient.get("/api/settings/llm");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch LLM config:", error);
    throw error;
  }
};

/**
 * Update LLM configuration on backend
 * @param {Object} config - LLM configuration object with provider, model, apiKey, temperature, maxTokens
 */
export const updateLLMConfig = async (config) => {
  try {
    const payload = {
      provider: config.provider,
      model: config.model,
      api_key: config.apiKey,
      temperature: config.temperature,
      max_tokens: config.maxTokens,
    };
    
    const response = await apiClient.post("/api/settings/llm", payload);
    return response.data;
  } catch (error) {
    console.error("Failed to update LLM config:", error);
    throw error;
  }
};

/**
 * Validate draft complaint using DraftingValidator
 * @param {string} draftText - The draft complaint text
 * @param {string} caseId - The case ID
 */
export const validateDraftComplaint = async (draftText, caseId) => {
  try {
    const payload = {
      draft_text: draftText,
      case_id: caseId,
    };
    
    const response = await apiClient.post("/api/drafting/validate", payload);
    return response.data;
  } catch (error) {
    console.error("Draft validation failed:", error);
    throw error;
  }
};

// ============================================================================
// PHASE A03 - OUTLINE DELIVERABLES API
// ============================================================================

/**
 * Generate Phase A03 shotlist (chronological timeline of facts)
 */
export const generateShotlist = async (caseId) => {
  try {
    const response = await apiClient.post(`/api/phaseA03/shotlist/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Shotlist generation failed:", error);
    throw error;
  }
};

/**
 * Generate Phase A03 claims matrix (legal analysis)
 */
export const generateClaimsMatrix = async (caseId, options = {}) => {
  try {
    const payload = {
      jurisdiction: options.jurisdiction || "ca_state",
      cause_of_action: options.causeOfAction || "negligence"
    };
    
    const response = await apiClient.post(`/api/phaseA03/claims-matrix/${caseId}`, payload);
    return response.data;
  } catch (error) {
    console.error("Claims matrix generation failed:", error);
    throw error;
  }
};

/**
 * Generate all Phase A03 deliverables (shotlist, claims matrix, skeletal outline)
 */
export const generatePhaseA03Deliverables = async (caseId, options = {}) => {
  try {
    const payload = {
      jurisdiction: options.jurisdiction || "ca_state",
      cause_of_action: options.causeOfAction || "negligence"
    };
    
    const response = await apiClient.post(`/api/phaseA03/generate/${caseId}`, payload);
    return response.data;
  } catch (error) {
    console.error("Phase A03 deliverables generation failed:", error);
    throw error;
  }
};

/**
 * Download Phase A03 deliverable (shotlist.csv, claims_matrix.json, skeletal_outline.json)
 */
export const downloadDeliverable = async (caseId, deliverableType) => {
  try {
    const response = await apiClient.get(
      `/api/deliverables/${caseId}/${deliverableType}`,
      { responseType: "blob" }
    );
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${caseId}_${deliverableType}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  } catch (error) {
    console.error(`Deliverable download failed (${deliverableType}):`, error);
    throw error;
  }
};

/**
 * Get Phase A03 deliverables status for a case (check if generated)
 */
export const getPhaseA03Deliverables = async (caseId) => {
  try {
    // Try to fetch each deliverable to check if it exists
    const deliverables = {
      shotlist: { available: false, url: null },
      claimsMatrix: { available: false, url: null },
      skeletalOutline: { available: false, url: null }
    };
    
    const deliverableTypes = [
      { key: "shotlist", filename: "shotlist.csv" },
      { key: "claimsMatrix", filename: "claims_matrix.json" },
      { key: "skeletalOutline", filename: "skeletal_outline.json" }
    ];
    
    for (const type of deliverableTypes) {
      try {
        // HEAD request to check if file exists
        await apiClient.head(`/api/deliverables/${caseId}/${type.filename}`);
        deliverables[type.key] = {
          available: true,
          url: `/api/deliverables/${caseId}/${type.filename}`,
          filename: type.filename
        };
      } catch (error) {
        // File doesn't exist, keep available: false
      }
    }
    
    return deliverables;
  } catch (error) {
    console.error("Failed to check Phase A03 deliverables:", error);
    throw error;
  }
};

/**
 * Validate Phase A03 deliverables before approving
 * Checks fact count, element completeness, section requirements
 */
export const validateDeliverables = async (caseId) => {
  try {
    const response = await apiClient.post(`/api/phases/phaseB01_review/validate/${caseId}`);
    return response.data;
  } catch (error) {
    console.error("Failed to validate deliverables:", error);
    throw error;
  }
};

/**
 * Approve Phase A03 deliverables and unlock Phase B02
 */
export const approveDeliverables = async (caseId, approvals) => {
  try {
    const response = await apiClient.post(`/api/phases/phaseB01_review/approve/${caseId}`, {
      approvals
    });
    return response.data;
  } catch (error) {
    console.error("Failed to approve deliverables:", error);
    throw error;
  }
};


/**
  * API service class for managing backend connections
  */
export class LawyerFactoryAPI {
  constructor() {
    this.isConnected = false;
    this.currentCaseId = null;
    this.phaseUpdateHandlers = [];
    this.workflowState = {};
    this.settings = {}; // User settings including LLM provider
  }

  /**
   * Initialize connection to LawyerFactory backend
   */
  async connect() {
    // Prevent duplicate connections
    if (this.isConnected) {
      console.log("⚠️ Already connected to LawyerFactory backend");
      return true;
    }

    try {
      // Check if backend is available
      const isAvailable = await isBackendAvailable();

      if (isAvailable) {
        // Initialize Socket.IO connection
        initializeSocket(
          (phaseUpdate) => {
            this.phaseUpdateHandlers.forEach((handler) => handler(phaseUpdate));
          },
          (error) => {
            console.error("Socket connection error:", error);
            this.isConnected = false;
          }
        );

        this.isConnected = true;
        console.log("✅ LawyerFactory API connected");
        return true;
      } else {
        console.warn(
          "⚠️ LawyerFactory backend not available - using mock data"
        );
        return false;
      }
    } catch (error) {
      console.error("❌ Failed to connect to LawyerFactory API:", error);
      return false;
    }
  }

  /**
   * Upload documents using unified storage API
   */
  async uploadDocumentsUnified(
    files,
    caseId = "default",
    phase = "phaseA01_intake"
  ) {
    try {
      const formData = new FormData();

      // Add files to form data
      files.forEach((file) => {
        formData.append("files", file);
      });

      // Add metadata
      formData.append("case_id", caseId);
      formData.append("phase", phase);

      const response = await apiClient.post(
        "/api/storage/documents",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          timeout: 60000, // 1 minute timeout for file uploads
        }
      );

      return response.data;
    } catch (error) {
      console.error("Unified document upload failed:", error);
      throw error;
    }
  }

  /**
   * Retrieve document by ObjectID from unified storage
   */
  async getDocumentByObjectId(objectId) {
    try {
      const response = await apiClient.get(
        `/api/storage/documents/${objectId}`
      );
      return response.data;
    } catch (error) {
      console.error("Document retrieval failed:", error);
      throw error;
    }
  }

  /**
   * Get all documents for a case from unified storage
   */
  async getCaseDocuments(caseId) {
    try {
      const response = await apiClient.get(
        `/api/storage/cases/${caseId}/documents`
      );
      return response.data;
    } catch (error) {
      console.error("Case documents retrieval failed:", error);
      throw error;
    }
  }

  /**
   * Disconnect from backend
   */
  disconnect() {
    closeSocket();
    this.isConnected = false;
    console.log("🔌 LawyerFactory API disconnected");
  }

  /**
   * Save workflow state for persistence
   */
  async saveWorkflowState(workflowState) {
    try {
      if (this.isConnected) {
        const response = await apiClient.post(`/api/workflow/${this.currentCaseId}/state`, {
          workflow_state: workflowState,
          timestamp: new Date().toISOString(),
        });
        this.workflowState = workflowState;
        return response.data;
      } else {
        // Store locally when backend unavailable
        const stateKey = `workflow_state_${this.currentCaseId}`;
        localStorage.setItem(stateKey, JSON.stringify({
          workflow_state: workflowState,
          timestamp: new Date().toISOString(),
        }));
        this.workflowState = workflowState;
        return { success: true, source: 'localStorage' };
      }
    } catch (error) {
      console.error("Failed to save workflow state:", error);
      throw error;
    }
  }

  /**
   * Load workflow state for recovery
   */
  async loadWorkflowState() {
    try {
      if (this.isConnected) {
        const response = await apiClient.get(`/api/workflow/${this.currentCaseId}/state`);
        this.workflowState = response.data.workflow_state;
        return response.data;
      } else {
        // Load from localStorage when backend unavailable
        const stateKey = `workflow_state_${this.currentCaseId}`;
        const savedState = localStorage.getItem(stateKey);
        if (savedState) {
          const parsedState = JSON.parse(savedState);
          this.workflowState = parsedState.workflow_state;
          return { success: true, source: 'localStorage', ...parsedState };
        }
        return null;
      }
    } catch (error) {
      console.error("Failed to load workflow state:", error);
      return null;
    }
  }

  /**
   * Clear workflow state
   */
  async clearWorkflowState() {
    try {
      if (this.isConnected) {
        await apiClient.delete(`/api/workflow/${this.currentCaseId}/state`);
      } else {
        // Clear from localStorage
        const stateKey = `workflow_state_${this.currentCaseId}`;
        localStorage.removeItem(stateKey);
      }
      this.workflowState = {};
      return { success: true };
    } catch (error) {
      console.error("Failed to clear workflow state:", error);
      throw error;
    }
  }

  /**
   * Get current workflow state
   */
  getCurrentWorkflowState() {
    return this.workflowState;
  }

  /**
   * Update settings (including LLM provider)
   */
  updateSettings(newSettings) {
    this.settings = { ...this.settings, ...newSettings };
    console.log('⚙️ LawyerFactoryAPI settings updated:', this.settings);
  }

  /**
   * Get current settings
   */
  getSettings() {
    return this.settings;
  }

  /**
   * Add handler for phase updates
   */
  onPhaseUpdate(handler) {
    this.phaseUpdateHandlers.push(handler);
  }

  /**
   * Remove handler for phase updates
   */
  offPhaseUpdate(handler) {
    const index = this.phaseUpdateHandlers.indexOf(handler);
    if (index > -1) {
      this.phaseUpdateHandlers.splice(index, 1);
    }
  }

  /**
   * Create new case and start workflow
   */
  async createCase(intakeData) {
    try {
      if (this.isConnected) {
        const result = await processIntake(intakeData, this.settings);
        this.currentCaseId = result.case_id;
        return result;
      } else {
        // Mock response when backend unavailable
        const mockCaseId = `case_${Date.now()}`;
        this.currentCaseId = mockCaseId;
        return {
          success: true,
          case_id: mockCaseId,
          case: intakeData,
          message: "Case created (mock mode)",
        };
      }
    } catch (error) {
      console.error("Case creation failed:", error);
      throw error;
    }
  }

  /**
   * Start research phase
   */
  async startResearchPhase(researchQuery) {
    if (!this.currentCaseId) {
      throw new Error("No active case - create case first");
    }

    try {
      if (this.isConnected) {
        return await startResearch(this.currentCaseId, researchQuery, this.settings);
      } else {
        // Mock response
        return {
          success: true,
          message: "Research started (mock mode)",
          case_id: this.currentCaseId,
        };
      }
    } catch (error) {
      console.error("Research phase start failed:", error);
      throw error;
    }
  }

  /**
   * Generate outline phase
   */
  async generateOutlinePhase() {
    if (!this.currentCaseId) {
      throw new Error("No active case - create case first");
    }

    try {
      if (this.isConnected) {
        return await generateOutline(this.currentCaseId, this.settings);
      } else {
        // Mock response
        return {
          success: true,
          message: "Outline generation started (mock mode)",
          case_id: this.currentCaseId,
        };
      }
    } catch (error) {
      console.error("Outline generation failed:", error);
      throw error;
    }
  }

  /**
   * Start final orchestration phase
   */
  async startFinalOrchestrationPhase() {
    if (!this.currentCaseId) {
      throw new Error("No active case - create case first");
    }

    try {
      if (this.isConnected) {
        return await startFinalOrchestration(this.currentCaseId);
      } else {
        // Mock response
        return {
          success: true,
          message: "Final orchestration started (mock mode)",
          case_id: this.currentCaseId,
          deliverables: {
            court_ready_documents: [],
            filing_package: {},
            case_summary: "",
            final_archive: "",
          },
        };
      }
    } catch (error) {
      console.error("Final orchestration failed:", error);
      throw error;
    }
  }

  /**
   * Get orchestration status
   */
  async getOrchestrationStatus() {
    if (!this.currentCaseId) {
      throw new Error("No active case - create case first");
    }

    try {
      if (this.isConnected) {
        return await getOrchestrationStatus(this.currentCaseId);
      } else {
        // Mock response
        return {
          status: "completed",
          progress: 100,
          case_id: this.currentCaseId,
          deliverables_ready: true,
        };
      }
    } catch (error) {
      console.error("Orchestration status check failed:", error);
      throw error;
    }
  }

  /**
   * Get final deliverables
   */
  async getFinalDeliverables() {
    if (!this.currentCaseId) {
      throw new Error("No active case - create case first");
    }

    try {
      if (this.isConnected) {
        return await getFinalDeliverables(this.currentCaseId);
      } else {
        // Mock response
        return {
          court_ready_documents: [
            { name: "complaint.pdf", type: "complaint", pages: 15 },
            { name: "exhibits.pdf", type: "exhibits", pages: 8 },
          ],
          filing_package: {
            name: "filing_package.zip",
            size: "2.4MB",
            contents: 3,
          },
          case_summary: "Complete case analysis and documentation ready for filing",
          final_archive: "case_archive_" + this.currentCaseId + ".zip",
        };
      }
    } catch (error) {
      console.error("Final deliverables fetch failed:", error);
      throw error;
    }
  }

  /**
   * Save case state to backend
   */
  async saveCaseState(caseName, stateData) {
    try {
      if (this.isConnected) {
        const response = await apiClient.post(`/api/cases/${caseName}/state`, {
          state: stateData,
          timestamp: new Date().toISOString(),
        });
        return response.data;
      } else {
        // Store locally when backend unavailable
        const stateKey = `case_state_${caseName}`;
        localStorage.setItem(stateKey, JSON.stringify({
          state: stateData,
          timestamp: new Date().toISOString(),
        }));
        return { success: true, source: 'localStorage' };
      }
    } catch (error) {
      console.error("Failed to save case state:", error);
      throw error;
    }
  }

  /**
   * Load case state from backend
   */
  async loadCaseState(caseName) {
    try {
      if (this.isConnected) {
        const response = await apiClient.get(`/api/cases/${caseName}/state`);
        return response.data;
      } else {
        // Load from localStorage when backend unavailable
        const stateKey = `case_state_${caseName}`;
        const savedState = localStorage.getItem(stateKey);
        if (savedState) {
          const parsedState = JSON.parse(savedState);
          return { success: true, source: 'localStorage', ...parsedState };
        }
        return null;
      }
    } catch (error) {
      console.error("Failed to load case state:", error);
      return null;
    }
  }
}

// Export singleton instance
export const apiService = new LawyerFactoryAPI();
export const lawyerFactoryAPI = new LawyerFactoryAPI();

// Default export for convenience
export default lawyerFactoryAPI;
