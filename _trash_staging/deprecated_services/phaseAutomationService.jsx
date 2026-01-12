/**
 * Phase Automation Service - Handles automated phase execution and monitoring
 * Integrates with LawyerFactory backend for phase orchestration
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

class PhaseAutomationService {
  constructor() {
    this.activePhases = new Map();
    this.phaseListeners = new Map();
  }

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
      const response = await axios.post(
        `${API_BASE_URL}/api/phases/${phaseId}/start`,
        {
          case_id: caseId,
          llm_provider: config.llmConfig?.provider || 'openai',
          llm_model: config.llmConfig?.model || 'gpt-4',
          llm_temperature: config.llmConfig?.temperature || 0.1,
          llm_max_tokens: config.llmConfig?.maxTokens || 2000,
          ...config.phaseData,
        },
        {
          timeout: 300000, // 5 minutes timeout
        }
      );

      if (response.data.success) {
        // Update phase status
        this.activePhases.set(phaseId, {
          ...this.activePhases.get(phaseId),
          status: 'initiated',
          taskId: response.data.task_id,
        });

        return {
          success: true,
          phaseId,
          taskId: response.data.task_id,
          message: response.data.message || 'Phase started successfully',
        };
      } else {
        throw new Error(response.data.error || 'Phase execution failed');
      }
    } catch (error) {
      console.error(`❌ Phase execution error for ${phaseId}:`, error);
      
      // Mark phase as failed
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
        // Poll phase status
        const response = await axios.get(
          `${API_BASE_URL}/api/phases/${phaseId}/status/${taskId}`
        );

        const { status, progress, outputs, error } = response.data;

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
        
        // If it's a connection error, keep trying
        if (attempts < maxAttempts) {
          await this.delay(5000);
          attempts++;
          continue;
        }
        
        // Max attempts reached
        return {
          success: false,
          phaseId,
          status: 'timeout',
          error: 'Phase execution timed out',
        };
      }
    }

    // Timeout
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
  async cancelPhase(phaseId) {
    try {
      const phaseData = this.activePhases.get(phaseId);
      if (!phaseData) {
        return {
          success: false,
          error: 'Phase not found or not running',
        };
      }

      // Call backend to cancel phase
      await axios.post(`${API_BASE_URL}/api/phases/${phaseId}/cancel`, {
        task_id: phaseData.taskId,
      });

      // Remove from active phases
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
    const backoffDelay = Math.pow(2, retryCount) * 1000; // Exponential backoff

    if (retryCount >= maxRetries) {
      return {
        success: false,
        error: `Max retries (${maxRetries}) exceeded`,
      };
    }

    console.log(`🔄 Retrying phase ${phaseId} (attempt ${retryCount + 1}/${maxRetries})`);

    // Wait with exponential backoff
    await this.delay(backoffDelay);

    // Retry execution
    return this.executePhase(phaseId, caseId, config);
  }

  /**
   * Utility: Delay execution
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise<void>}
   */
  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
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
}

// Export singleton instance
const phaseAutomationService = new PhaseAutomationService();
export default phaseAutomationService;
