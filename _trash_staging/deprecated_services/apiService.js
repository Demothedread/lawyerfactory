/**
 * API Service - Backward Compatibility Shim
 * 
 * DEPRECATED: This file maintains backward compatibility during migration to backendService.js
 * 
 * All functionality has been consolidated into backendService.js
 * New code should import from backendService.js directly
 * 
 * Timeline:
 * - Currently: Shim re-exports all functions from backendService.js
 * - Next Phase: Migrate component imports one-by-one to backendService.js
 * - Final: Remove this shim after all imports updated
 * 
 * Migration Files (10 total):
 * 1. PhaseA01Intake.jsx
 * 2. PhaseA02Research.jsx
 * 3. PhaseA03Outline.jsx
 * 4. PhaseB01Review.jsx
 * 5. PhaseC01Editing.jsx
 * 6. PhaseC02Orchestration.jsx
 * 7. DraftingPhase.jsx
 * 8. EnhancedSettingsPanel.jsx
 * 9. SettingsPanel.jsx
 * 10. NeonPhaseCard.jsx
 * 
 * See: IMPORT_MIGRATION_GUIDE.md for detailed migration instructions
 */

// Re-export everything from backendService.js for backward compatibility
export {

    // Service Class
    LawyerFactoryBackend, approveDeliverables, backendService, cancelPhase, closeSocket, downloadDeliverable,
    // Settings
    fetchLLMConfig, generateClaimsMatrix,
    // Outline
    generateOutline, generatePhaseA03Deliverables,
    // Phase A03 Deliverables
    generateShotlist, generateSkeletalOutline, getCaseDocuments,
    // Claims
    getClaimsMatrix, getDocumentByObjectId, getFinalDeliverables, getOrchestrationStatus, getOutlineStatus, getPhaseA03Deliverables, getPhaseStatus, getResearchResults, getResearchStatus, getSocket,
    // Health & Connection
    healthCheck,
    // Socket.IO Operations
    initializeSocket, isBackendAvailable,

    // Intake & Basic
    processIntake,
    // Orchestration
    startFinalOrchestration,
    // Phase Execution
    startPhase,
    // Research
    startResearch, updateLLMConfig, uploadCaseDocuments,
    // Storage & Documents
    uploadDocumentsUnified, validateDeliverables,
    // Drafting
    validateDraftComplaint
} from './backendService.js';

// Deprecation warning (logged once per session)
if (typeof window !== 'undefined') {
  const deprecationKey = '__apiService_deprecation_warned__';
  if (!window[deprecationKey]) {
    console.warn(
      '%c⚠️  DEPRECATION WARNING',
      'color: orange; font-weight: bold; font-size: 14px',
      '\n\n' +
      '  File: apiService.js is deprecated\n' +
      '  Use: backendService.js instead\n\n' +
      '  All functionality has been consolidated into backendService.js\n' +
      '  This shim maintains backward compatibility during migration.\n\n' +
      '  Migration Guide: See IMPORT_MIGRATION_GUIDE.md\n\n'
    );
    window[deprecationKey] = true;
  }
}

export default {
  // Re-export default as well for convenience
  initializeSocket,
  getSocket,
  closeSocket,
  healthCheck,
  isBackendAvailable,
  processIntake,
  uploadDocumentsUnified,
  uploadCaseDocuments,
  getDocumentByObjectId,
  getCaseDocuments,
  startPhase,
  getPhaseStatus,
  cancelPhase,
  startResearch,
  getResearchStatus,
  getResearchResults,
  generateOutline,
  getOutlineStatus,
  generateSkeletalOutline,
  getClaimsMatrix,
  generateClaimsMatrix,
  validateDraftComplaint,
  startFinalOrchestration,
  getOrchestrationStatus,
  getFinalDeliverables,
  generateShotlist,
  generatePhaseA03Deliverables,
  downloadDeliverable,
  getPhaseA03Deliverables,
  validateDeliverables,
  approveDeliverables,
  fetchLLMConfig,
  updateLLMConfig,
  LawyerFactoryBackend,
  backendService,
};
