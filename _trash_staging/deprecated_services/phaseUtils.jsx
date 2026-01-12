// Phase utilities - Map phase IDs to descriptive names, emojis, and configurations
export const PHASE_CONFIG = {
  'A01': {
    id: 'A01',
    name: 'Document Intake',
    description: 'Upload and process evidence documents',
    emoji: '📥',
    weight: 10,
  },
  'A02': {
    id: 'A02',
    name: 'Legal Research',
    description: 'Conduct comprehensive legal research',
    emoji: '🔍',
    weight: 20,
  },
  'A03': {
    id: 'A03',
    name: 'Case Outline',
    description: 'Create skeletal case outline',
    emoji: '📋',
    weight: 15,
  },
  'B01': {
    id: 'B01',
    name: 'Quality Review',
    description: 'Quality assurance checkpoint',
    emoji: '✅',
    weight: 15,
  },
  'B02': {
    id: 'B02',
    name: 'Document Drafting',
    description: 'Compose legal documents',
    emoji: '✍️',
    weight: 25,
  },
  'C01': {
    id: 'C01',
    name: 'Document Editing',
    description: 'Final formatting and citations',
    emoji: '✏️',
    weight: 10,
  },
  'C02': {
    id: 'C02',
    name: 'Final Orchestration',
    description: 'Maestro coordination',
    emoji: '🎯',
    weight: 5,
  },
};

// Get descriptive name from phase ID
export const getPhaseName = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.name || phaseId;
};

// Get emoji from phase ID
export const getPhaseEmoji = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.emoji || '📊';
};

// Get full phase description
export const getPhaseDescription = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.description || '';
};

// Get phase weight for progress calculation
export const getPhaseWeight = (phaseId) => {
  return PHASE_CONFIG[phaseId]?.weight || 0;
};

// Get all phases in order
export const getAllPhases = () => {
  return Object.values(PHASE_CONFIG);
};

// Convert phase ID to display format for UI
export const formatPhaseDisplay = (phaseId) => {
  const config = PHASE_CONFIG[phaseId];
  if (!config) return phaseId;
  return `${config.emoji} ${config.name}`;
};
