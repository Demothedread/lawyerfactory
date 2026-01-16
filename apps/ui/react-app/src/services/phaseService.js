/**
 * Phase Service - Centralized phase management and utilities
 * Coordinates 7-phase workflow: A01-A03, B01-B02, C01-C02
 * Provides configuration, status tracking, and phase orchestration helpers
 */

// ============================================================================
// PHASE CONFIGURATION & CONSTANTS
// ============================================================================

/** Complete phase configuration map */
export const PHASE_CONFIG = {
  'A01': {
    id: 'A01',
    name: 'Document Intake',
    description: 'Upload and process evidence documents',
    emoji: '📥',
    weight: 10,
    series: 'A',
    stage: 'preproduction',
  },
  'A02': {
    id: 'A02',
    name: 'Legal Research',
    description: 'Conduct comprehensive legal research',
    emoji: '🔍',
    weight: 20,
    series: 'A',
    stage: 'preproduction',
  },
  'A03': {
    id: 'A03',
    name: 'Case Outline',
    description: 'Create skeletal case outline',
    emoji: '📋',
    weight: 15,
    series: 'A',
    stage: 'preproduction',
  },
  'B01': {
    id: 'B01',
    name: 'Quality Review',
    description: 'Quality assurance checkpoint',
    emoji: '✅',
    weight: 15,
    series: 'B',
    stage: 'production',
  },
  'B02': {
    id: 'B02',
    name: 'Document Drafting',
    description: 'Compose legal documents',
    emoji: '✍️',
    weight: 25,
    series: 'B',
    stage: 'production',
  },
  'C01': {
    id: 'C01',
    name: 'Document Editing',
    description: 'Final formatting and citations',
    emoji: '✏️',
    weight: 10,
    series: 'C',
    stage: 'postproduction',
  },
  'C02': {
    id: 'C02',
    name: 'Final Orchestration',
    description: 'Maestro coordination',
    emoji: '🎯',
    weight: 5,
    series: 'C',
    stage: 'postproduction',
  },
};

/** Phase series and stage definitions */
export const PHASE_SERIES = {
  'A': { name: 'Preproduction', stages: ['A01', 'A02', 'A03'] },
  'B': { name: 'Production', stages: ['B01', 'B02'] },
  'C': { name: 'Postproduction', stages: ['C01', 'C02'] },
};

/** Phase dependencies - which phases must complete before others */
export const PHASE_DEPENDENCIES = {
  'A01': [],
  'A02': ['A01'],
  'A03': ['A02'],
  'B01': ['A03'],
  'B02': ['B01'],
  'C01': ['B02'],
  'C02': ['C01'],
};

/** Phase status values */
export const PHASE_STATUS = {
  PENDING: 'pending',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  ERROR: 'error',
  PAUSED: 'paused',
  CANCELLED: 'cancelled',
};

// ============================================================================
// BASIC PHASE UTILITIES
// ============================================================================

/**
 * Get descriptive name from phase ID
 * @param {string} phaseId - Phase ID (e.g., 'A01')
 * @returns {string} Phase name
 */
export const getPhaseName = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.name || phaseId;
};

/**
 * Get emoji from phase ID
 * @param {string} phaseId - Phase ID
 * @returns {string} Phase emoji
 */
export const getPhaseEmoji = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.emoji || '📊';
};

/**
 * Get full phase description
 * @param {string} phaseId - Phase ID
 * @returns {string} Phase description
 */
export const getPhaseDescription = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.description || '';
};

/**
 * Get phase weight for progress calculation
 * @param {string} phaseId - Phase ID
 * @returns {number} Phase weight
 */
export const getPhaseWeight = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.weight || 0;
};

/**
 * Get series information for a phase
 * @param {string} phaseId - Phase ID
 * @returns {string} Series (A, B, or C)
 */
export const getPhaseSeries = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.series || null;
};

/**
 * Get stage information for a phase
 * @param {string} phaseId - Phase ID
 * @returns {string} Stage (preproduction, production, postproduction)
 */
export const getPhaseStage = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.stage || null;
};

/**
 * Get all phases in order
 * @returns {Array} Ordered array of phase configurations
 */
export const getAllPhases = () => {
  return Object.values(PHASE_CONFIG);
};

/**
 * Convert phase ID to display format for UI
 * @param {string} phaseId - Phase ID
 * @returns {string} Formatted display string
 */
export const formatPhaseDisplay = (phaseId) => {
  const config = PHASE_CONFIG[phaseId];
  if (!config) return phaseId;
  return `${config.emoji} ${config.name}`;
};

/**
 * Get full phase details
 * @param {string} phaseId - Phase ID
 * @returns {Object} Complete phase configuration
 */
export const getPhaseDetails = (phaseId) => {
  return PHASE_CONFIG[phaseId] || null;
};

// ============================================================================
// PHASE DEPENDENCY & SEQUENCING
// ============================================================================

/**
 * Get phases that must complete before the given phase
 * @param {string} phaseId - Phase ID
 * @returns {Array} Array of prerequisite phase IDs
 */
export const getPhaseDependencies = (phaseId) => {
  return PHASE_DEPENDENCIES[phaseId] || [];
};

/**
 * Check if a phase can be executed (all dependencies met)
 * @param {string} phaseId - Phase ID
 * @param {Array} completedPhases - Array of completed phase IDs
 * @returns {boolean} True if phase can be executed
 */
export const canExecutePhase = (phaseId, completedPhases = []) => {
  const dependencies = getPhaseDependencies(phaseId);
  return dependencies.every((dep) => completedPhases.includes(dep));
};

/**
 * Get next executable phase
 * @param {Array} completedPhases - Array of completed phase IDs
 * @returns {string|null} Next phase ID or null if all complete
 */
export const getNextPhase = (completedPhases = []) => {
  const allPhases = Object.keys(PHASE_CONFIG);
  for (const phaseId of allPhases) {
    if (!completedPhases.includes(phaseId) && canExecutePhase(phaseId, completedPhases)) {
      return phaseId;
    }
  }
  return null;
};

/**
 * Get all phases that can currently be executed
 * @param {Array} completedPhases - Array of completed phase IDs
 * @returns {Array} Array of executable phase IDs
 */
export const getExecutablePhases = (completedPhases = []) => {
  return Object.keys(PHASE_CONFIG).filter(
    (phaseId) => !completedPhases.includes(phaseId) && canExecutePhase(phaseId, completedPhases)
  );
};

/**
 * Check if a phase is the final phase (C02)
 * @param {string} phaseId - Phase ID
 * @returns {boolean} True if final phase
 */
export const isFinalPhase = (phaseId) => {
  return phaseId === 'C02';
};

/**
 * Get series phases (all phases in A, B, or C)
 * @param {string} series - Series ('A', 'B', or 'C')
 * @returns {Array} Array of phase IDs in series
 */
export const getSeriesPhases = (series) => {
  return PHASE_SERIES[series]?.stages || [];
};

// ============================================================================
// PROGRESS & STATUS CALCULATIONS
// ============================================================================

/**
 * Calculate total workflow weight
 * @returns {number} Total weight across all phases
 */
export const getTotalWorkflowWeight = () => {
  return Object.values(PHASE_CONFIG).reduce((sum, phase) => sum + phase.weight, 0);
};

/**
 * Calculate workflow progress percentage
 * @param {Array} phaseStatuses - Array of { phaseId, status, progress }
 * @returns {number} Progress percentage (0-100)
 */
export const calculateWorkflowProgress = (phaseStatuses = []) => {
  if (phaseStatuses.length === 0) return 0;

  const totalWeight = getTotalWorkflowWeight();
  if (totalWeight === 0) return 0;

  let completedWeight = 0;

  phaseStatuses.forEach(({ phaseId, status, progress = 0 }) => {
    const phaseWeight = getPhaseWeight(phaseId);

    if (status === PHASE_STATUS.COMPLETED) {
      completedWeight += phaseWeight;
    } else if (status === PHASE_STATUS.ACTIVE) {
      completedWeight += (phaseWeight * (progress / 100));
    }
  });

  return Math.round((completedWeight / totalWeight) * 100);
};

/**
 * Calculate series progress
 * @param {string} series - Series ('A', 'B', or 'C')
 * @param {Array} completedPhases - Array of completed phase IDs
 * @returns {number} Series completion percentage
 */
export const calculateSeriesProgress = (series, completedPhases = []) => {
  const seriesPhases = getSeriesPhases(series);
  if (seriesPhases.length === 0) return 0;

  const completed = seriesPhases.filter((phaseId) => completedPhases.includes(phaseId)).length;
  return Math.round((completed / seriesPhases.length) * 100);
};

/**
 * Count completed phases
 * @param {Array} completedPhases - Array of completed phase IDs
 * @returns {number} Number of completed phases
 */
export const getCompletedPhaseCount = (completedPhases = []) => {
  return completedPhases.length;
};

/**
 * Get completion status for display
 * @param {Array} completedPhases - Array of completed phase IDs
 * @returns {string} Completion string (e.g., "3/7 phases complete")
 */
export const getCompletionStatus = (completedPhases = []) => {
  const completed = completedPhases.length;
  const total = Object.keys(PHASE_CONFIG).length;
  return `${completed}/${total} phases complete`;
};

// ============================================================================
// PHASE STATUS & STATE MANAGEMENT
// ============================================================================

/**
 * Initialize phase state
 * @returns {Object} Initial phase state object
 */
export const initializePhaseState = () => {
  const state = {};
  Object.keys(PHASE_CONFIG).forEach((phaseId) => {
    state[phaseId] = {
      phaseId,
      status: PHASE_STATUS.PENDING,
      progress: 0,
      startTime: null,
      endTime: null,
      error: null,
      results: null,
      taskId: null,
    };
  });
  return state;
};

/**
 * Update phase status
 * @param {Object} phaseState - Current phase state
 * @param {string} phaseId - Phase ID
 * @param {string} status - New status
 * @param {Object} updates - Additional updates
 * @returns {Object} Updated phase state
 */
export const updatePhaseStatus = (phaseState, phaseId, status, updates = {}) => {
  return {
    ...phaseState,
    [phaseId]: {
      ...phaseState[phaseId],
      status,
      ...updates,
      ...(status === PHASE_STATUS.ACTIVE && !phaseState[phaseId].startTime && { startTime: Date.now() }),
      ...(status === PHASE_STATUS.COMPLETED && { endTime: Date.now() }),
    },
  };
};

/**
 * Get phases by status
 * @param {Object} phaseState - Current phase state
 * @param {string} status - Status to filter by
 * @returns {Array} Array of phase IDs with given status
 */
export const getPhasesByStatus = (phaseState, status) => {
  return Object.entries(phaseState)
    .filter(([, phase]) => phase.status === status)
    .map(([phaseId]) => phaseId);
};

/**
 * Get active phase (first one with ACTIVE status)
 * @param {Object} phaseState - Current phase state
 * @returns {string|null} Active phase ID or null
 */
export const getActivePhase = (phaseState) => {
  const activePhases = getPhasesByStatus(phaseState, PHASE_STATUS.ACTIVE);
  return activePhases.length > 0 ? activePhases[0] : null;
};

/**
 * Get completion percentage for a phase
 * @param {Object} phaseState - Current phase state
 * @param {string} phaseId - Phase ID
 * @returns {number} Progress percentage (0-100)
 */
export const getPhaseProgress = (phaseState, phaseId) => {
  return phaseState[phaseId]?.progress || 0;
};

// ============================================================================
// BATCH OPERATIONS
// ============================================================================

/**
 * Mark multiple phases as completed
 * @param {Object} phaseState - Current phase state
 * @param {Array} phaseIds - Phase IDs to mark complete
 * @returns {Object} Updated phase state
 */
export const markPhasesCompleted = (phaseState, phaseIds = []) => {
  let updated = phaseState;
  phaseIds.forEach((phaseId) => {
    updated = updatePhaseStatus(updated, phaseId, PHASE_STATUS.COMPLETED);
  });
  return updated;
};

/**
 * Reset phase state (clear all progress)
 * @returns {Object} Fresh phase state
 */
export const resetPhaseState = () => {
  return initializePhaseState();
};

/**
 * Get phase timeline (duration from start to end)
 * @param {Object} phaseState - Current phase state
 * @param {string} phaseId - Phase ID
 * @returns {number|null} Duration in milliseconds or null if not completed
 */
export const getPhaseDuration = (phaseState, phaseId) => {
  const phase = phaseState[phaseId];
  if (phase.startTime && phase.endTime) {
    return phase.endTime - phase.startTime;
  }
  return null;
};

/**
 * Format phase duration for display
 * @param {number} durationMs - Duration in milliseconds
 * @returns {string} Formatted duration (e.g., "2m 30s")
 */
export const formatPhaseDuration = (durationMs) => {
  if (!durationMs) return 'N/A';

  const seconds = Math.floor((durationMs / 1000) % 60);
  const minutes = Math.floor((durationMs / (1000 * 60)) % 60);
  const hours = Math.floor((durationMs / (1000 * 60 * 60)) % 24);

  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0) parts.push(`${seconds}s`);

  return parts.length > 0 ? parts.join(' ') : '0s';
};

// ============================================================================
// LOOKUP & SEARCH UTILITIES
// ============================================================================

/**
 * Get phase by name (case-insensitive)
 * @param {string} name - Phase name to search for
 * @returns {Object|null} Phase configuration or null
 */
export const findPhaseByName = (name) => {
  const lowerName = name.toLowerCase();
  return (
    Object.values(PHASE_CONFIG).find((phase) => phase.name.toLowerCase() === lowerName) || null
  );
};

/**
 * Get phases in a specific series
 * @param {string} series - Series identifier ('A', 'B', 'C')
 * @returns {Array} Array of phase configurations in series
 */
export const getPhasesBySeries = (series) => {
  return Object.values(PHASE_CONFIG).filter((phase) => phase.series === series);
};

/**
 * Get phases in a specific stage
 * @param {string} stage - Stage identifier (preproduction, production, postproduction)
 * @returns {Array} Array of phase configurations in stage
 */
export const getPhasesByStage = (stage) => {
  return Object.values(PHASE_CONFIG).filter((phase) => phase.stage === stage);
};

/**
 * Check if phase is in preproduction (A series)
 * @param {string} phaseId - Phase ID
 * @returns {boolean} True if preproduction
 */
export const isPreproductionPhase = (phaseId) => {
  return getPhaseSeries(phaseId) === 'A';
};

/**
 * Check if phase is in production (B series)
 * @param {string} phaseId - Phase ID
 * @returns {boolean} True if production
 */
export const isProductionPhase = (phaseId) => {
  return getPhaseSeries(phaseId) === 'B';
};

/**
 * Check if phase is in postproduction (C series)
 * @param {string} phaseId - Phase ID
 * @returns {boolean} True if postproduction
 */
export const isPostproductionPhase = (phaseId) => {
  return getPhaseSeries(phaseId) === 'C';
};

// ============================================================================
// EXPORT PRESET PHASE ARRAYS
// ============================================================================

/** All phase IDs in execution order */
export const ALL_PHASES = Object.keys(PHASE_CONFIG);

/** Preproduction phases */
export const PREPRODUCTION_PHASES = getPhasesBySeries('A').map((p) => p.id);

/** Production phases */
export const PRODUCTION_PHASES = getPhasesBySeries('B').map((p) => p.id);

/** Postproduction phases */
export const POSTPRODUCTION_PHASES = getPhasesBySeries('C').map((p) => p.id);
