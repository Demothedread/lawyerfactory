/**
 * Unified Backend Service - Consolidated API and Phase Management
 * Merges REST API communication, Socket.IO connections, and phase orchestration
 * Provides single source of truth for all LawyerFactory backend integration
 */

import axios from 'axios';
import { io } from 'socket.io-client';

// API Configuration
const API_BASE_URL = 'http://localhost:5000';
const API_TIMEOUT = 30000; // 30 seconds

// ============================================================================
// ENHANCED EVIDENCE API INTEGRATION
// ============================================================================

/**
 * Get evidence table data with enhanced filtering and PRIMARY/SECONDARY classification
 * @param {Object} filters - Filter options (evidence_source, evidence_type, search, etc.)
 * @returns {Promise<Object>} Evidence table data
 */
export const getEvidenceTable = async (filters = {}) => {
  try {
    const params = new URLSearchParams();

    // Add filter parameters
    if (filters.evidence_source && filters.evidence_source !== 'all') {
      params.append('evidence_source', filters.evidence_source);
    }
    if (filters.evidence_type) {
      params.append('evidence_type', filters.evidence_type);
    }
    if (filters.relevance_level) {
      params.append('relevance_level', filters.relevance_level);
    }
    if (filters.search) {
      params.append('search', filters.search);
    }
    if (filters.min_relevance_score) {
      params.append('min_relevance_score', filters.min_relevance_score);
    }
    if (filters.phase) {
      params.append('phase', filters.phase);
    }

    const response = await apiClient.get(`/api/evidence?${params}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get evidence table:', error);
    throw error;
  }
};

/**
 * Add new evidence entry with enhanced validation
 * @param {Object} evidenceData - Evidence entry data
 * @returns {Promise<Object>} Creation result
 */
export const addEvidenceEntry = async (evidenceData) => {
  try {
    const response = await apiClient.post('/api/evidence', evidenceData);
    return response.data;
  } catch (error) {
    console.error('Failed to add evidence entry:', error);
    throw error;
  }
};

/**
 * Update existing evidence entry
 * @param {string} evidenceId - Evidence ID
 * @param {Object} updateData - Update data
 * @returns {Promise<Object>} Update result
 */
export const updateEvidenceEntry = async (evidenceId, updateData) => {
  try {
    const response = await apiClient.put(`/api/evidence/${evidenceId}`, updateData);
    return response.data;
  } catch (error) {
    console.error('Failed to update evidence entry:', error);
    throw error;
  }
};

/**
 * Delete evidence entry
 * @param {string} evidenceId - Evidence ID
 * @returns {Promise<Object>} Deletion result
 */
export const deleteEvidenceEntry = async (evidenceId) => {
  try {
    const response = await apiClient.delete(`/api/evidence/${evidenceId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to delete evidence entry:', error);
    throw error;
  }
};

/**
 * Download evidence file
 * @param {string} evidenceId - Evidence ID
 * @returns {Promise<Blob>} File blob
 */
export const downloadEvidenceFile = async (evidenceId) => {
  try {
    const response = await apiClient.get(`/api/evidence/${evidenceId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    console.error('Failed to download evidence file:', error);
    throw error;
  }
};

/**
 * Get evidence statistics with enhanced metrics
 * @returns {Promise<Object>} Evidence statistics
 */
export const getEvidenceStats = async () => {
  try {
    const response = await apiClient.get('/api/evidence/stats');
    return response.data;
  } catch (error) {
    console.error('Failed to get evidence stats:', error);
    throw error;
  }
};

/**
 * Export evidence data in various formats
 * @param {string} format - Export format ('json' or 'csv')
 * @param {Object} options - Export options
 * @returns {Promise<Object|Blob>} Exported data
 */
export const exportEvidenceData = async (format = 'json', options = {}) => {
  try {
    const params = new URLSearchParams();
    params.append('format', format);

    if (options.include_facts) {
      params.append('include_facts', 'true');
    }
    if (options.include_research) {
      params.append('include_research', 'true');
    }

    const response = await apiClient.get(`/api/evidence/export?${params}`, {
      responseType: format === 'csv' ? 'blob' : 'json',
    });
    return response.data;
  } catch (error) {
    console.error('Failed to export evidence data:', error);
    throw error;
  }
};

/**
 * Execute research from PRIMARY evidence
 * @param {string} evidenceId - PRIMARY evidence ID
 * @param {Array} keywords - Optional custom keywords
 * @returns {Promise<Object>} Research result
 */
export const executeResearchFromEvidence = async (evidenceId, keywords = null) => {
  try {
    const payload = {
      evidence_id: evidenceId,
      keywords: keywords,
      max_results: 5,
    };

    const response = await apiClient.post('/api/research/execute', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to execute research:', error);
    throw error;
  }
};

/**
 * Add fact assertion
 * @param {Object} factData - Fact assertion data
 * @returns {Promise<Object>} Creation result
 */
export const addFactAssertion = async (factData) => {
  try {
    const response = await apiClient.post('/api/facts', factData);
    return response.data;
  } catch (error) {
    console.error('Failed to add fact assertion:', error);
    throw error;
  }
};

/**
 * Link evidence to fact
 * @param {string} evidenceId - Evidence ID
 * @param {string} factId - Fact ID
 * @returns {Promise<Object>} Link result
 */
export const linkEvidenceToFact = async (evidenceId, factId) => {
  try {
    const response = await apiClient.post('/api/evidence/link', {
      evidence_id: evidenceId,
      fact_id: factId,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to link evidence to fact:', error);
    throw error;
  }
};

/**
 * Add claim entry
 * @param {Object} claimData - Claim entry data
 * @returns {Promise<Object>} Creation result
 */
export const addClaimEntry = async (claimData) => {
  try {
    const response = await apiClient.post('/api/claims', claimData);
    return response.data;
  } catch (error) {
    console.error('Failed to add claim entry:', error);
    throw error;
  }
};

/**
 * Perform batch operations on evidence entries
 * @param {string} operation - Operation type ('update', 'delete')
 * @param {Array} evidenceIds - Array of evidence IDs
 * @param {Object} operationData - Operation data for updates
 * @returns {Promise<Object>} Batch operation result
 */
export const batchEvidenceOperations = async (operation, evidenceIds, operationData = {}) => {
  try {
    const response = await apiClient.post('/api/evidence/batch', {
      operation,
      evidence_ids: evidenceIds,
      data: operationData,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to perform batch operation:', error);
    throw error;
  }
};

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
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
      transports: ['websocket', 'polling'],
      timeout: 20000,
    });

    socket.on('connect', () => {
      console.log('🔌 Connected to LawyerFactory backend');
    });

    socket.on('disconnect', () => {
      console.log('🔌 Disconnected from LawyerFactory backend');
    });

    socket.on('phase_progress_update', (data) => {
      console.log('📊 Phase progress update:', data);
      if (onPhaseUpdate) onPhaseUpdate(data);
    });

    socket.on('connect_error', (error) => {
      console.error('❌ Socket connection error:', error);
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
    console.log('🔌 Socket connection closed');
  }
};

/**
 * Health check endpoint
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

/**
 * Check if backend is available
 */
export const isBackendAvailable = async () => {
  try {
    const result = await healthCheck();
    return result.status === 'healthy' || result.status === 'ok';
  } catch (error) {
    console.warn('Backend health check failed:', error.message);
    return false;
  }
};

// ============================================================================
// INTAKE & BASIC OPERATIONS
// ============================================================================

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

    const response = await apiClient.post('/api/intake', payload);
    return response.data;
  } catch (error) {
    console.error('Intake processing failed:', error);
    throw error;
  }
};

// ============================================================================
// STORAGE & DOCUMENT MANAGEMENT
// ============================================================================

/**
 * Upload documents using unified storage API
 */
export const uploadDocumentsUnified = async (
  files,
  caseId = 'default',
  phase = 'phaseA01_intake'
) => {
  try {
    const formData = new FormData();

    // Add files to form data
    files.forEach((file) => {
      formData.append('files', file);
    });

    // Add metadata
    formData.append('case_id', caseId);
    formData.append('phase', phase);

    const response = await apiClient.post('/api/storage/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 1 minute timeout for file uploads
    });

    return response.data;
  } catch (error) {
    console.error('Unified document upload failed:', error);
    throw error;
  }
};

/**
 * Upload documents for a case (legacy endpoint)
 */
export const uploadCaseDocuments = async (caseId, files) => {
  try {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post(`/api/cases/${caseId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Document upload failed:', error);
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
    console.error('Document retrieval failed:', error);
    throw error;
  }
};

/**
 * Get all documents for a case from unified storage
 */
export const getCaseDocuments = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/storage/cases/${caseId}/documents`);
    return response.data;
  } catch (error) {
    console.error('Case documents retrieval failed:', error);
    throw error;
  }
};

// ============================================================================
// PHASE EXECUTION & ORCHESTRATION
// ============================================================================

/**
 * Start a specific phase for a case
 * @param {string} phaseId - The phase ID (e.g., 'phaseB02_drafting')
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
 * Get phase status - Core integration with phase automation
 * @param {string} phaseId - Phase identifier
 * @param {string} taskId - Task ID from phase execution
 */
export const getPhaseStatus = async (phaseId, taskId) => {
  try {
    const response = await apiClient.get(`/api/phases/${phaseId}/status/${taskId}`);
    return response.data;
  } catch (error) {
    console.error(`Phase status check failed for ${phaseId}:`, error);
    throw error;
  }
};

/**
 * Cancel a running phase
 * @param {string} phaseId - Phase identifier
 * @param {string} taskId - Task ID
 */
export const cancelPhase = async (phaseId, taskId) => {
  try {
    const response = await apiClient.post(`/api/phases/${phaseId}/cancel`, {
      task_id: taskId,
    });
    return response.data;
  } catch (error) {
    console.error(`Phase cancellation failed for ${phaseId}:`, error);
    throw error;
  }
};

// ============================================================================
// RESEARCH OPERATIONS
// ============================================================================

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

    const response = await apiClient.post('/api/research/start', payload);
    return response.data;
  } catch (error) {
    console.error('Research start failed:', error);
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
    console.error('Research status check failed:', error);
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
    console.error('Research results fetch failed:', error);
    throw error;
  }
};

// ============================================================================
// OUTLINE GENERATION
// ============================================================================

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

    const response = await apiClient.post('/api/outline/generate', payload);
    return response.data;
  } catch (error) {
    console.error('Outline generation failed:', error);
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
    console.error('Outline status check failed:', error);
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
    console.error('Skeletal outline generation failed:', error);
    throw error;
  }
};

// ============================================================================
// CLAIMS & LEGAL ANALYSIS
// ============================================================================

/**
 * Get claims matrix for a case
 */
export const getClaimsMatrix = async (caseId) => {
  try {
    const response = await apiClient.get(`/api/claims/matrix/${caseId}`);
    return response.data;
  } catch (error) {
    console.error('Claims matrix fetch failed:', error);
    throw error;
  }
};

/**
 * Generate Phase A03 claims matrix (legal analysis)
 */
export const generateClaimsMatrix = async (caseId, options = {}) => {
  try {
    const payload = {
      jurisdiction: options.jurisdiction || 'ca_state',
      cause_of_action: options.causeOfAction || 'negligence',
    };

    const response = await apiClient.post(`/api/phaseA03/claims-matrix/${caseId}`, payload);
    return response.data;
  } catch (error) {
    console.error('Claims matrix generation failed:', error);
    throw error;
  }
};

// ============================================================================
// DRAFTING & DOCUMENT GENERATION
// ============================================================================

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

    const response = await apiClient.post('/api/drafting/validate', payload);
    return response.data;
  } catch (error) {
    console.error('Draft validation failed:', error);
    throw error;
  }
};

// ============================================================================
// ORCHESTRATION & FINAL DELIVERY
// ============================================================================

/**
 * Start final orchestration phase for a case
 */
export const startFinalOrchestration = async (caseId) => {
  try {
    const response = await apiClient.post('/api/orchestration/start', {
      case_id: caseId,
    });
    return response.data;
  } catch (error) {
    console.error('Final orchestration start failed:', error);
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
    console.error('Orchestration status check failed:', error);
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
    console.error('Final deliverables fetch failed:', error);
    throw error;
  }
};

// ============================================================================
// PHASE A03 DELIVERABLES
// ============================================================================

/**
 * Generate Phase A03 shotlist (chronological timeline of facts)
 */
export const generateShotlist = async (caseId) => {
  try {
    const response = await apiClient.post(`/api/phaseA03/shotlist/${caseId}`);
    return response.data;
  } catch (error) {
    console.error('Shotlist generation failed:', error);
    throw error;
  }
};

/**
 * Generate all Phase A03 deliverables (shotlist, claims matrix, skeletal outline)
 */
export const generatePhaseA03Deliverables = async (caseId, options = {}) => {
  try {
    const payload = {
      jurisdiction: options.jurisdiction || 'ca_state',
      cause_of_action: options.causeOfAction || 'negligence',
    };

    const response = await apiClient.post(`/api/phaseA03/generate/${caseId}`, payload);
    return response.data;
  } catch (error) {
    console.error('Phase A03 deliverables generation failed:', error);
    throw error;
  }
};

/**
 * Download Phase A03 deliverable (shotlist.csv, claims_matrix.json, skeletal_outline.json)
 */
export const downloadDeliverable = async (caseId, deliverableType) => {
  try {
    const response = await apiClient.get(`/api/deliverables/${caseId}/${deliverableType}`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${caseId}_${deliverableType}`);
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
    const deliverables = {
      shotlist: { available: false, url: null },
      claimsMatrix: { available: false, url: null },
      skeletalOutline: { available: false, url: null },
    };

    const deliverableTypes = [
      { key: 'shotlist', filename: 'shotlist.csv' },
      { key: 'claimsMatrix', filename: 'claims_matrix.json' },
      { key: 'skeletalOutline', filename: 'skeletal_outline.json' },
    ];

    for (const type of deliverableTypes) {
      try {
        // HEAD request to check if file exists
        await apiClient.head(`/api/deliverables/${caseId}/${type.filename}`);
        deliverables[type.key] = {
          available: true,
          url: `/api/deliverables/${caseId}/${type.filename}`,
          filename: type.filename,
        };
      } catch (error) {
        // File doesn't exist, keep available: false
      }
    }

    return deliverables;
  } catch (error) {
    console.error('Failed to check Phase A03 deliverables:', error);
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
    console.error('Failed to validate deliverables:', error);
    throw error;
  }
};

/**
 * Approve Phase A03 deliverables and unlock Phase B02
 */
export const approveDeliverables = async (caseId, approvals) => {
  try {
    const response = await apiClient.post(`/api/phases/phaseB01_review/approve/${caseId}`, {
      approvals,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to approve deliverables:', error);
    throw error;
  }
};

// ============================================================================
// SETTINGS & CONFIGURATION
// ============================================================================

/**
 * Fetch LLM configuration from backend (includes environment variable defaults)
 */
export const fetchLLMConfig = async () => {
  try {
    const response = await apiClient.get('/api/settings/llm');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch LLM config:', error);
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

    const response = await apiClient.post('/api/settings/llm', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to update LLM config:', error);
    throw error;
  }
};

// ============================================================================
// UNIFIED BACKEND SERVICE CLASS
// ============================================================================

/**
 * LawyerFactoryBackend - Unified backend service class
 * Consolidates all API, phase, and orchestration operations
 */
export class LawyerFactoryBackend {
  constructor() {
    this.isConnected = false;
    this.currentCaseId = null;
    this.phaseUpdateHandlers = [];
    this.activePhases = new Map();
    this.phaseListeners = new Map();
    this.workflowState = {};
    this.settings = {}; // User settings including LLM provider
  }

  /**
   * Initialize connection to LawyerFactory backend
   */
  async connect() {
    if (this.isConnected) {
      console.log('⚠️ Already connected to LawyerFactory backend');
      return true;
    }

    try {
      const isAvailable = await isBackendAvailable();

      if (isAvailable) {
        initializeSocket(
          (phaseUpdate) => {
            this.phaseUpdateHandlers.forEach((handler) => handler(phaseUpdate));
          },
          (error) => {
            console.error('Socket connection error:', error);
            this.isConnected = false;
          }
        );

        this.isConnected = true;
        console.log('✅ LawyerFactory backend connected');
        return true;
      } else {
        console.warn('⚠️ LawyerFactory backend not available - using mock data');
        return false;
      }
    } catch (error) {
      console.error('❌ Failed to connect to LawyerFactory backend:', error);
      return false;
    }
  }

  /**
   * Disconnect from backend
   */
  disconnect() {
    closeSocket();
    this.isConnected = false;
    console.log('🔌 LawyerFactory backend disconnected');
  }

  // ========================================================================
  // PHASE EXECUTION & MONITORING (from PhaseAutomationService)
  // ========================================================================

  /**
   * Execute a phase with the given configuration
   * @param {string} phaseId - Phase identifier (e.g., 'phaseA01_intake')
   * @param {string} caseId - Case ID to process
   * @param {Object} config - Phase configuration including LLM settings
   * @returns {Promise<Object>} Phase execution result
   */
  async executePhase(phaseId, caseId, config = {}) {
    try {
      console.log(`🚀 Executing phase ${phaseId} for case ${caseId}`, config);

      // Mark phase as active
      this.activePhases.set(phaseId, {
        caseId,
        startTime: Date.now(),
        status: 'running',
        progress: 0,
      });

      // Call backend API to start phase
      const response = await startPhase(phaseId, caseId, {
        llm_provider: config.llmConfig?.provider || 'openai',
        llm_model: config.llmConfig?.model || 'gpt-4',
        llm_temperature: config.llmConfig?.temperature || 0.1,
        llm_max_tokens: config.llmConfig?.maxTokens || 2000,
        ...config.phaseData,
      });

      if (response.success) {
        this.activePhases.set(phaseId, {
          ...this.activePhases.get(phaseId),
          status: 'initiated',
          taskId: response.task_id,
        });

        return {
          success: true,
          phaseId,
          taskId: response.task_id,
          message: response.message || 'Phase started successfully',
        };
      } else {
        throw new Error(response.error || 'Phase execution failed');
      }
    } catch (error) {
      console.error(`❌ Phase execution error for ${phaseId}:`, error);

      this.activePhases.set(phaseId, {
        ...this.activePhases.get(phaseId),
        status: 'error',
        error: error.message,
      });

      return {
        success: false,
        phaseId,
        error: error.message,
        errorType: this.determineErrorType(error),
      };
    }
  }

  /**
   * Wait for phase completion with progress monitoring
   * @param {string} phaseId - Phase identifier
   * @param {string} taskId - Task ID from phase execution
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} Final phase status
   */
  async waitForPhaseCompletion(phaseId, taskId, onProgress = null) {
    const maxAttempts = 60; // 5 minutes max (5 second intervals)
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await getPhaseStatus(phaseId, taskId);
        const { status, progress, outputs, error } = response;

        // Update local phase tracking
        this.activePhases.set(phaseId, {
          ...this.activePhases.get(phaseId),
          status,
          progress,
          outputs,
          error,
        });

        // Call progress callback
        if (onProgress) {
          onProgress({
            phaseId,
            status,
            progress,
            outputs,
            error,
          });
        }

        // Check if phase is complete
        if (status === 'completed') {
          console.log(`✅ Phase ${phaseId} completed successfully`);
          this.activePhases.delete(phaseId);
          return {
            success: true,
            phaseId,
            status: 'completed',
            outputs,
          };
        }

        // Check if phase failed
        if (status === 'error' || status === 'failed') {
          console.error(`❌ Phase ${phaseId} failed:`, error);
          this.activePhases.delete(phaseId);
          return {
            success: false,
            phaseId,
            status: 'error',
            error,
          };
        }

        // Wait before next poll
        await this.delay(5000); // 5 second intervals
        attempts++;
      } catch (error) {
        console.error(`Error polling phase ${phaseId}:`, error);

        if (attempts < maxAttempts) {
          await this.delay(5000);
          attempts++;
          continue;
        }

        return {
          success: false,
          phaseId,
          status: 'timeout',
          error: 'Phase execution timed out',
        };
      }
    }

    return {
      success: false,
      phaseId,
      status: 'timeout',
      error: 'Phase execution timed out after 5 minutes',
    };
  }

  /**
   * Get current status of an active phase
   * @param {string} phaseId - Phase identifier
   * @returns {Object|null} Phase status or null if not active
   */
  getPhaseStatus(phaseId) {
    return this.activePhases.get(phaseId) || null;
  }

  /**
   * Cancel a running phase
   * @param {string} phaseId - Phase identifier
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelPhaseExecution(phaseId) {
    try {
      const phaseData = this.activePhases.get(phaseId);
      if (!phaseData) {
        return {
          success: false,
          error: 'Phase not found or not running',
        };
      }

      await cancelPhase(phaseId, phaseData.taskId);
      this.activePhases.delete(phaseId);

      return {
        success: true,
        message: `Phase ${phaseId} cancelled`,
      };
    } catch (error) {
      console.error(`Error cancelling phase ${phaseId}:`, error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Get all active phases
   * @returns {Array} Array of active phase data
   */
  getActivePhases() {
    return Array.from(this.activePhases.entries()).map(([phaseId, data]) => ({
      phaseId,
      ...data,
    }));
  }

  /**
   * Clear all active phases (use with caution)
   */
  clearActivePhases() {
    this.activePhases.clear();
  }

  /**
   * Determine error type for recovery strategies
   * @param {Error} error - Error object
   * @returns {string} Error type
   */
  determineErrorType(error) {
    const message = error.message.toLowerCase();

    if (message.includes('network') || message.includes('fetch')) {
      return 'network_error';
    }
    if (message.includes('timeout')) {
      return 'timeout_error';
    }
    if (message.includes('llm') || message.includes('ai')) {
      return 'llm_error';
    }
    if (message.includes('storage') || message.includes('database')) {
      return 'storage_error';
    }
    if (message.includes('rate limit')) {
      return 'rate_limit_error';
    }

    return 'unknown_error';
  }

  /**
   * Retry phase execution with exponential backoff
   * @param {string} phaseId - Phase identifier
   * @param {string} caseId - Case ID
   * @param {Object} config - Phase configuration
   * @param {number} retryCount - Current retry attempt
   * @returns {Promise<Object>} Retry result
   */
  async retryPhase(phaseId, caseId, config, retryCount = 0) {
    const maxRetries = 3;
    const backoffDelay = Math.pow(2, retryCount) * 1000;

    if (retryCount >= maxRetries) {
      return {
        success: false,
        error: `Max retries (${maxRetries}) exceeded`,
      };
    }

    console.log(`🔄 Retrying phase ${phaseId} (attempt ${retryCount + 1}/${maxRetries})`);

    await this.delay(backoffDelay);
    return this.executePhase(phaseId, caseId, config);
  }

  // ========================================================================
  // WORKFLOW STATE MANAGEMENT
  // ========================================================================

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
        const stateKey = `workflow_state_${this.currentCaseId}`;
        localStorage.setItem(
          stateKey,
          JSON.stringify({
            workflow_state: workflowState,
            timestamp: new Date().toISOString(),
          })
        );
        this.workflowState = workflowState;
        return { success: true, source: 'localStorage' };
      }
    } catch (error) {
      console.error('Failed to save workflow state:', error);
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
      console.error('Failed to load workflow state:', error);
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
        const stateKey = `workflow_state_${this.currentCaseId}`;
        localStorage.removeItem(stateKey);
      }
      this.workflowState = {};
      return { success: true };
    } catch (error) {
      console.error('Failed to clear workflow state:', error);
      throw error;
    }
  }

  /**
   * Get current workflow state
   */
  getCurrentWorkflowState() {
    return this.workflowState;
  }

  // ========================================================================
  // SETTINGS & CONFIGURATION
  // ========================================================================

  /**
   * Update settings (including LLM provider)
   */
  updateSettings(newSettings) {
    this.settings = { ...this.settings, ...newSettings };
    console.log('⚙️ Backend settings updated:', this.settings);
  }

  /**
   * Get current settings
   */
  getSettings() {
    return this.settings;
  }

  // ========================================================================
  // EVENT HANDLERS
  // ========================================================================

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

  // ========================================================================
  // CASE OPERATIONS
  // ========================================================================

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
        const mockCaseId = `case_${Date.now()}`;
        this.currentCaseId = mockCaseId;
        return {
          success: true,
          case_id: mockCaseId,
          case: intakeData,
          message: 'Case created (mock mode)',
        };
      }
    } catch (error) {
      console.error('Case creation failed:', error);
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
        const stateKey = `case_state_${caseName}`;
        localStorage.setItem(
          stateKey,
          JSON.stringify({
            state: stateData,
            timestamp: new Date().toISOString(),
          })
        );
        return { success: true, source: 'localStorage' };
      }
    } catch (error) {
      console.error('Failed to save case state:', error);
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
        const stateKey = `case_state_${caseName}`;
        const savedState = localStorage.getItem(stateKey);
        if (savedState) {
          const parsedState = JSON.parse(savedState);
          return { success: true, source: 'localStorage', ...parsedState };
        }
        return null;
      }
    } catch (error) {
      console.error('Failed to load case state:', error);
      return null;
    }
  }

  // ========================================================================
  // UTILITY METHODS
  // ========================================================================

  /**
   * Delay execution (utility for retries, polling)
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise<void>}
   */
  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ========================================================================
  // BARTLEBY CHATBOT API
  // ========================================================================

  /**
   * Send a chat message to Bartleby AI assistant
   * @param {Object} messageData - Message and context data
   * @returns {Promise<Object>} Chat response with message and actions
   */
  async sendChatMessage(messageData) {
    try {
      const response = await apiClient.post('/api/chat/message', {
        message: messageData.message,
        case_id: messageData.caseId,
        context: messageData.context,
        settings: messageData.settings,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to send chat message:', error);
      throw error;
    }
  }

  /**
   * Stream chat response (for long responses)
   * @param {Object} messageData - Message and context data
   * @param {Function} onChunk - Callback for each response chunk
   * @returns {Promise<void>}
   */
  async streamChatResponse(messageData, onChunk) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageData.message,
          case_id: messageData.caseId,
          context: messageData.context,
          settings: messageData.settings,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            onChunk(data);
          }
        }
      }
    } catch (error) {
      console.error('Failed to stream chat response:', error);
      throw error;
    }
  }

  /**
   * Modify skeletal outline via chatbot
   * @param {string} caseId - Case ID
   * @param {Object} modifications - Outline modifications
   * @returns {Promise<Object>} Updated outline
   */
  async modifyOutlineViaChat(caseId, modifications) {
    try {
      const response = await apiClient.post('/api/chat/modify-outline', {
        case_id: caseId,
        modifications,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to modify outline:', error);
      throw error;
    }
  }

  /**
   * Update evidence via chatbot
   * @param {string} caseId - Case ID
   * @param {Object} evidenceUpdate - Evidence update data
   * @returns {Promise<Object>} Update result
   */
  async updateEvidenceViaChat(caseId, evidenceUpdate) {
    try {
      const response = await apiClient.post('/api/chat/update-evidence', {
        case_id: caseId,
        update: evidenceUpdate,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to update evidence:', error);
      throw error;
    }
  }

  /**
   * Adjust research parameters via chatbot
   * @param {string} caseId - Case ID
   * @param {Object} researchParams - Research parameter updates
   * @returns {Promise<Object>} Update result
   */
  async adjustResearchViaChat(caseId, researchParams) {
    try {
      const response = await apiClient.post('/api/chat/adjust-research', {
        case_id: caseId,
        parameters: researchParams,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to adjust research:', error);
      throw error;
    }
  }

  /**
   * Search vector store via chatbot
   * @param {string} caseId - Case ID
   * @param {string} query - Search query
   * @param {Object} filters - Optional filters
   * @returns {Promise<Object>} Search results
   */
  async searchVectorStore(caseId, query, filters = {}) {
    try {
      const response = await apiClient.post('/api/chat/vector-search', {
        case_id: caseId,
        query,
        filters,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to search vector store:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const backendService = new LawyerFactoryBackend();

// Default export for convenience
export default backendService;
