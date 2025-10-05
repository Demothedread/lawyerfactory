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
   * Upload research documents
   */
  async uploadResearchDocuments(files) {
    if (!this.currentCaseId) {
      throw new Error("No active case - create case first");
    }

    try {
      if (this.isConnected) {
        return await uploadCaseDocuments(this.currentCaseId, files);
      } else {
        // Mock response
        return {
          success: true,
          message: `${files.length} documents uploaded (mock mode)`,
          case_id: this.currentCaseId,
          processed_documents: files.map((file) => ({
            filename: file.name,
            size: file.size,
            type: file.type,
          })),
        };
      }
    } catch (error) {
      console.error("Document upload failed:", error);
      throw error;
    }
  }
}

// Export singleton instance
export const lawyerFactoryAPI = new LawyerFactoryAPI();

// Default export for convenience
export default lawyerFactoryAPI;
