/**
 * Soviet Atomic Age Thematic Icons
 * Pre-digital mechanical, clunky, chunky but functional heavy machinery aesthetic
 * Unicode-based symbols optimized for terminal-like, brutalist industrial feel
 */

export const THEMATIC_ICONS = {
  // System & Configuration
  llm: '▬', // LLM Configuration - mechanical bar
  settings: '⚙', // Settings - gear
  config: '◈', // Configuration - mechanical diamond
  general: '▭', // General - mechanical box
  system: '⬛', // System - solid industrial block
  
  // Legal & Documentation
  legal: '⬢', // Legal - hexagonal brutalist form
  document: '▬', // Document - mechanical bar
  compliance: '◗', // Compliance - technical square
  contract: '▭', // Contract - mechanical rectangle
  briefcase: '▬', // Briefcase - mechanical bar
  
  // Workflow & Process
  workflow: '⟳', // Workflow - mechanical cycle
  phase: '◐', // Phase - mechanical arc
  process: '▶', // Process - mechanical arrow forward
  pipeline: '▬', // Pipeline - mechanical conduit
  stages: '▢', // Stages - stacked boxes
  
  // Actions & Controls
  start: '▶', // Start - mechanical play arrow
  pause: '⏸', // Pause - mechanical bars
  stop: '⏹', // Stop - mechanical square stop
  reset: '⟲', // Reset - mechanical counterclockwise
  export: '⤴', // Export - mechanical upward arrow
  import: '⤵', // Import - mechanical downward arrow
  save: '▬', // Save - mechanical bar
  delete: '✕', // Delete - mechanical X
  edit: '✎', // Edit - mechanical pencil
  
  // Status & Indicators
  active: '●', // Active - filled circle (light)
  inactive: '◯', // Inactive - hollow circle
  pending: '◐', // Pending - half circle
  complete: '✓', // Complete - mechanical checkmark
  error: '✕', // Error - mechanical X
  warning: '▲', // Warning - mechanical triangle
  
  // Navigation & UI
  menu: '☰', // Menu - mechanical lines
  back: '◀', // Back - mechanical left arrow
  forward: '▶', // Forward - mechanical right arrow
  up: '▲', // Up - mechanical triangle
  down: '▼', // Down - mechanical inverted triangle
  left: '◀', // Left - mechanical left arrow
  right: '▶', // Right - mechanical right arrow
  expand: '◆', // Expand - mechanical diamond
  collapse: '◇', // Collapse - hollow diamond
  
  // Evidence & Data
  evidence: '▬', // Evidence - mechanical bar/document
  upload: '⤴', // Upload - mechanical upward arrow
  download: '⤵', // Download - mechanical downward arrow
  search: '⊙', // Search - mechanical circle with dot
  filter: '⋮', // Filter - mechanical dots
  database: '▢', // Database - mechanical stacked squares
  
  // Analysis & Research
  research: '⊗', // Research - mechanical circle with cross
  analysis: '◈', // Analysis - mechanical diamond
  matrix: '▣', // Matrix - mechanical grid
  outline: '▬', // Outline - mechanical bar
  claims: '◗', // Claims - mechanical technical square
  
  // Feedback & Communication
  notification: '◆', // Notification - mechanical diamond
  alert: '▲', // Alert - mechanical triangle
  info: 'ⓘ', // Info - mechanical info circle
  success: '✓', // Success - mechanical checkmark
  toast: '◆', // Toast - mechanical diamond
  
  // Time & Scheduling
  time: '⏱', // Time - mechanical stopwatch
  schedule: '⏳', // Schedule - mechanical hourglass
  timer: '⏱', // Timer - mechanical stopwatch
  
  // Additional Utility
  refresh: '⟳', // Refresh - mechanical cycle
  sync: '⟳', // Sync - mechanical cycle
  lock: '⧭', // Lock - mechanical lock
  unlock: '⧮', // Unlock - mechanical open
  visibility: '⊙', // Visibility - mechanical eye
  copy: '⧉', // Copy - mechanical parallel lines
  paste: '▬', // Paste - mechanical bar
};

/**
 * Icon categories for organized access
 */
export const ICON_CATEGORIES = {
  system: ['settings', 'config', 'general', 'system', 'llm'],
  legal: ['legal', 'document', 'compliance', 'contract', 'briefcase'],
  workflow: ['workflow', 'phase', 'process', 'pipeline', 'stages'],
  actions: ['start', 'pause', 'stop', 'reset', 'export', 'import', 'save', 'delete', 'edit'],
  status: ['active', 'inactive', 'pending', 'complete', 'error', 'warning'],
  navigation: ['menu', 'back', 'forward', 'up', 'down', 'left', 'right', 'expand', 'collapse'],
  evidence: ['evidence', 'upload', 'download', 'search', 'filter', 'database'],
  analysis: ['research', 'analysis', 'matrix', 'outline', 'claims'],
  feedback: ['notification', 'alert', 'info', 'success', 'toast'],
  time: ['time', 'schedule', 'timer'],
  utility: ['refresh', 'sync', 'lock', 'unlock', 'visibility', 'copy', 'paste'],
};

/**
 * Get icon by key
 * @param {string} key - Icon key from THEMATIC_ICONS
 * @returns {string} Unicode icon character
 */
export const getIcon = (key) => {
  return THEMATIC_ICONS[key] || '◆'; // Default to diamond if not found
};

/**
 * Get icon with label (for accessibility and UI)
 * @param {string} key - Icon key
 * @param {string} label - Optional label text
 * @returns {object} Icon and label object
 */
export const getIconWithLabel = (key, label) => {
  return {
    icon: getIcon(key),
    label: label || key,
  };
};

export default THEMATIC_ICONS;
