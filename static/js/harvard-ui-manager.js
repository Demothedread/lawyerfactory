/**
 * Harvard-Style Workflow UI Manager
 * Handles DOM interactions, form submissions, modals, and user interface events
 */

class HarvardUIManager {
    constructor(app) {
        this.app = app;
        this.modals = new Map();
        this.notifications = [];
        this.initialized = false;
    }

    /**
     * Initialize UI manager
     */
    async initialize() {
        if (this.initialized) return;

        console.log('🎛️ Initializing Harvard UI Manager...');
        
        try {
            this.setupEventListeners();
            this.initializeModals();
            this.initializeNotifications();
            this.setupFormValidation();
            this.initialized = true;
            console.log('✅ Harvard UI Manager initialized');
            
        } catch (error) {
            console.error('❌ Failed to initialize UI manager:', error);
        }
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Handle workflow control buttons
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            // Start workflow button
            if (target.matches('.start-workflow-btn') || target.closest('.start-workflow-btn')) {
                this.handleStartWorkflow(event);
            }
            
            // Pause workflow button
            if (target.matches('.pause-workflow-btn') || target.closest('.pause-workflow-btn')) {
                this.handlePauseWorkflow(event);
            }
            
            // Resume workflow button
            if (target.matches('.resume-workflow-btn') || target.closest('.resume-workflow-btn')) {
                this.handleResumeWorkflow(event);
            }
            
            // Stop workflow button
            if (target.matches('.stop-workflow-btn') || target.closest('.stop-workflow-btn')) {
                this.handleStopWorkflow(event);
            }
            
            // Modal triggers
            if (target.matches('[data-modal]')) {
                this.openModal(target.dataset.modal);
            }
            
            // Modal close buttons
            if (target.matches('.modal-close') || target.closest('.modal-close')) {
                this.closeModal(event);
            }
            
            // Notification close buttons
            if (target.matches('.notification-close') || target.closest('.notification-close')) {
                this.closeNotification(event);
            }
        });

        // Handle form submissions
        document.addEventListener('submit', (event) => {
            if (event.target.matches('.harvard-form')) {
                this.handleFormSubmission(event);
            }
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboardShortcuts(event);
        });

        // Handle window resize for responsive adjustments
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Handle tab visibility changes
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
    }

    /**
     * Handle start workflow action
     */
    async handleStartWorkflow(event) {
        event.preventDefault();
        const button = event.target.closest('.start-workflow-btn');
        
        try {
            // Show loading state
            this.setButtonLoading(button, true);
            
            // Get workflow parameters from form if exists
            const form = document.getElementById('workflowStartForm');
            const params = form ? this.getFormData(form) : {};
            
            // Start workflow
            const response = await this.app.api.startWorkflow(params);
            
            if (response.success) {
                this.showNotification('Workflow started successfully', 'success');
                this.updateWorkflowControls('running');
            } else {
                throw new Error(response.error || 'Failed to start workflow');
            }
            
        } catch (error) {
            console.error('Error starting workflow:', error);
            this.showNotification('Failed to start workflow: ' + error.message, 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    /**
     * Handle pause workflow action
     */
    async handlePauseWorkflow(event) {
        event.preventDefault();
        const button = event.target.closest('.pause-workflow-btn');
        
        try {
            this.setButtonLoading(button, true);
            const response = await this.app.api.pauseWorkflow();
            
            if (response.success) {
                this.showNotification('Workflow paused', 'info');
                this.updateWorkflowControls('paused');
            } else {
                throw new Error(response.error || 'Failed to pause workflow');
            }
            
        } catch (error) {
            console.error('Error pausing workflow:', error);
            this.showNotification('Failed to pause workflow: ' + error.message, 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    /**
     * Handle resume workflow action
     */
    async handleResumeWorkflow(event) {
        event.preventDefault();
        const button = event.target.closest('.resume-workflow-btn');
        
        try {
            this.setButtonLoading(button, true);
            const response = await this.app.api.resumeWorkflow();
            
            if (response.success) {
                this.showNotification('Workflow resumed', 'success');
                this.updateWorkflowControls('running');
            } else {
                throw new Error(response.error || 'Failed to resume workflow');
            }
            
        } catch (error) {
            console.error('Error resuming workflow:', error);
            this.showNotification('Failed to resume workflow: ' + error.message, 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    /**
     * Handle stop workflow action
     */
    async handleStopWorkflow(event) {
        event.preventDefault();
        
        // Show confirmation modal
        const confirmed = await this.showConfirmationModal(
            'Stop Workflow',
            'Are you sure you want to stop the current workflow? This action cannot be undone.',
            'Stop',
            'Cancel'
        );
        
        if (!confirmed) return;
        
        const button = event.target.closest('.stop-workflow-btn');
        
        try {
            this.setButtonLoading(button, true);
            const response = await this.app.api.stopWorkflow();
            
            if (response.success) {
                this.showNotification('Workflow stopped', 'warning');
                this.updateWorkflowControls('stopped');
            } else {
                throw new Error(response.error || 'Failed to stop workflow');
            }
            
        } catch (error) {
            console.error('Error stopping workflow:', error);
            this.showNotification('Failed to stop workflow: ' + error.message, 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    /**
     * Update workflow control buttons based on state
     */
    updateWorkflowControls(state) {
        const startBtn = document.querySelector('.start-workflow-btn');
        const pauseBtn = document.querySelector('.pause-workflow-btn');
        const resumeBtn = document.querySelector('.resume-workflow-btn');
        const stopBtn = document.querySelector('.stop-workflow-btn');
        
        // Reset all buttons
        [startBtn, pauseBtn, resumeBtn, stopBtn].forEach(btn => {
            if (btn) {
                btn.disabled = true;
                btn.classList.add('opacity-50');
            }
        });
        
        // Enable appropriate buttons based on state
        switch (state) {
            case 'idle':
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.classList.remove('opacity-50');
                }
                break;
                
            case 'running':
                if (pauseBtn) {
                    pauseBtn.disabled = false;
                    pauseBtn.classList.remove('opacity-50');
                }
                if (stopBtn) {
                    stopBtn.disabled = false;
                    stopBtn.classList.remove('opacity-50');
                }
                break;
                
            case 'paused':
                if (resumeBtn) {
                    resumeBtn.disabled = false;
                    resumeBtn.classList.remove('opacity-50');
                }
                if (stopBtn) {
                    stopBtn.disabled = false;
                    stopBtn.classList.remove('opacity-50');
                }
                break;
                
            case 'stopped':
            case 'completed':
            case 'failed':
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.classList.remove('opacity-50');
                }
                break;
        }
    }

    /**
     * Set button loading state
     */
    setButtonLoading(button, loading) {
        if (!button) return;
        
        if (loading) {
            button.disabled = true;
            button.classList.add('loading');
            
            // Add spinner if doesn't exist
            if (!button.querySelector('.spinner')) {
                const spinner = document.createElement('div');
                spinner.className = 'spinner inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2';
                button.insertBefore(spinner, button.firstChild);
            }
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            
            // Remove spinner
            const spinner = button.querySelector('.spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }

    /**
     * Handle form submission
     */
    async handleFormSubmission(event) {
        event.preventDefault();
        const form = event.target;
        const formData = this.getFormData(form);
        
        // Validate form
        if (!this.validateForm(form)) {
            this.showNotification('Please correct the form errors', 'error');
            return;
        }
        
        try {
            // Show loading state
            const submitBtn = form.querySelector('[type="submit"]');
            this.setButtonLoading(submitBtn, true);
            
            // Submit form based on action
            const action = form.dataset.action || 'submit';
            let response;
            
            switch (action) {
                case 'start-workflow':
                    response = await this.app.api.startWorkflow(formData);
                    break;
                case 'save-settings':
                    response = await this.app.api.saveSettings(formData);
                    break;
                default:
                    response = await this.app.api.submitForm(action, formData);
            }
            
            if (response.success) {
                this.showNotification('Form submitted successfully', 'success');
                
                // Close modal if form is in a modal
                const modal = form.closest('.modal');
                if (modal) {
                    this.closeModal();
                }
                
                // Reset form if specified
                if (form.dataset.reset !== 'false') {
                    form.reset();
                }
            } else {
                throw new Error(response.error || 'Form submission failed');
            }
            
        } catch (error) {
            console.error('Form submission error:', error);
            this.showNotification('Form submission failed: ' + error.message, 'error');
        } finally {
            const submitBtn = form.querySelector('[type="submit"]');
            this.setButtonLoading(submitBtn, false);
        }
    }

    /**
     * Get form data as object
     */
    getFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            // Handle multiple values (checkboxes, multi-select)
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    /**
     * Validate form
     */
    validateForm(form) {
        let isValid = true;
        const fields = form.querySelectorAll('[required], [data-validate]');
        
        fields.forEach(field => {
            const errors = this.validateField(field);
            this.showFieldErrors(field, errors);
            
            if (errors.length > 0) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * Validate individual field
     */
    validateField(field) {
        const errors = [];
        const value = field.value.trim();
        const rules = field.dataset.validate ? field.dataset.validate.split('|') : [];
        
        // Required validation
        if (field.required && !value) {
            errors.push('This field is required');
        }
        
        // Skip other validations if field is empty and not required
        if (!value && !field.required) {
            return errors;
        }
        
        // Custom validation rules
        rules.forEach(rule => {
            const [ruleName, ruleValue] = rule.split(':');
            
            switch (ruleName) {
                case 'min':
                    if (value.length < parseInt(ruleValue)) {
                        errors.push(`Minimum ${ruleValue} characters required`);
                    }
                    break;
                    
                case 'max':
                    if (value.length > parseInt(ruleValue)) {
                        errors.push(`Maximum ${ruleValue} characters allowed`);
                    }
                    break;
                    
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        errors.push('Please enter a valid email address');
                    }
                    break;
                    
                case 'number':
                    if (isNaN(value) || isNaN(parseFloat(value))) {
                        errors.push('Please enter a valid number');
                    }
                    break;
                    
                case 'url':
                    try {
                        new URL(value);
                    } catch {
                        errors.push('Please enter a valid URL');
                    }
                    break;
            }
        });
        
        return errors;
    }

    /**
     * Show field validation errors
     */
    showFieldErrors(field, errors) {
        // Remove existing error displays
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Remove error styling
        field.classList.remove('border-red-500', 'border-crimson');
        
        if (errors.length > 0) {
            // Add error styling
            field.classList.add('border-red-500');
            
            // Create error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-red-500 text-sm mt-1';
            errorDiv.textContent = errors[0]; // Show first error
            
            field.parentNode.appendChild(errorDiv);
        }
    }

    /**
     * Initialize modal system
     */
    initializeModals() {
        // Create modal overlay if it doesn't exist
        if (!document.getElementById('modalOverlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'modalOverlay';
            overlay.className = 'modal-overlay fixed inset-0 bg-black bg-opacity-50 hidden z-50 flex items-center justify-center';
            overlay.innerHTML = '<div class="modal-container"></div>';
            document.body.appendChild(overlay);
            
            // Close modal when clicking overlay
            overlay.addEventListener('click', (event) => {
                if (event.target === overlay) {
                    this.closeModal();
                }
            });
        }
    }

    /**
     * Open modal
     */
    openModal(modalId, data = {}) {
        const modalContent = document.getElementById(modalId);
        if (!modalContent) {
            console.error(`Modal with id "${modalId}" not found`);
            return;
        }
        
        const overlay = document.getElementById('modalOverlay');
        const container = overlay.querySelector('.modal-container');
        
        // Clone modal content
        const modalClone = modalContent.cloneNode(true);
        modalClone.style.display = 'block';
        
        // Replace placeholders with data
        if (Object.keys(data).length > 0) {
            this.replacePlaceholders(modalClone, data);
        }
        
        // Clear container and add modal
        container.innerHTML = '';
        container.appendChild(modalClone);
        
        // Show overlay
        overlay.classList.remove('hidden');
        
        // Focus first input
        const firstInput = modalClone.querySelector('input, textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Store current modal
        this.currentModal = modalId;
    }

    /**
     * Close modal
     */
    closeModal() {
        const overlay = document.getElementById('modalOverlay');
        overlay.classList.add('hidden');
        this.currentModal = null;
    }

    /**
     * Show confirmation modal
     */
    showConfirmationModal(title, message, confirmText = 'Confirm', cancelText = 'Cancel') {
        return new Promise((resolve) => {
            const modalId = 'confirmationModal';
            
            // Create confirmation modal if it doesn't exist
            if (!document.getElementById(modalId)) {
                const modal = document.createElement('div');
                modal.id = modalId;
                modal.style.display = 'none';
                modal.innerHTML = `
                    <div class="bg-charcoal rounded-lg shadow-xl max-w-md mx-auto p-6 border-2 border-gold">
                        <h3 class="text-lg font-bold text-gold mb-4 harvard-font" id="confirmTitle">${title}</h3>
                        <p class="text-cream mb-6" id="confirmMessage">${message}</p>
                        <div class="flex space-x-4 justify-end">
                            <button type="button" class="modal-close px-4 py-2 border border-gray-600 rounded-md text-gray-300 hover:bg-gray-700 transition-colors">
                                ${cancelText}
                            </button>
                            <button type="button" id="confirmBtn" class="px-4 py-2 bg-crimson text-white rounded-md hover:bg-crimson-dark transition-colors">
                                ${confirmText}
                            </button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            
            // Update content
            document.getElementById('confirmTitle').textContent = title;
            document.getElementById('confirmMessage').textContent = message;
            
            // Setup event listeners
            const confirmBtn = document.getElementById('confirmBtn');
            const cancelBtn = modal.querySelector('.modal-close');
            
            const cleanup = () => {
                confirmBtn.removeEventListener('click', handleConfirm);
                cancelBtn.removeEventListener('click', handleCancel);
                this.closeModal();
            };
            
            const handleConfirm = () => {
                cleanup();
                resolve(true);
            };
            
            const handleCancel = () => {
                cleanup();
                resolve(false);
            };
            
            confirmBtn.addEventListener('click', handleConfirm);
            cancelBtn.addEventListener('click', handleCancel);
            
            // Show modal
            this.openModal(modalId);
        });
    }

    /**
     * Replace placeholders in element
     */
    replacePlaceholders(element, data) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        textNodes.forEach(textNode => {
            let text = textNode.textContent;
            Object.keys(data).forEach(key => {
                text = text.replace(new RegExp(`{{${key}}}`, 'g'), data[key]);
            });
            textNode.textContent = text;
        });
    }

    /**
     * Initialize notification system
     */
    initializeNotifications() {
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        
        const typeClasses = {
            success: 'bg-green-600 border-green-500',
            error: 'bg-red-600 border-red-500',
            warning: 'bg-yellow-600 border-yellow-500',
            info: 'bg-blue-600 border-blue-500'
        };
        
        const typeIcons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        notification.className = `notification ${typeClasses[type]} text-white px-4 py-3 rounded-lg shadow-lg border-l-4 max-w-sm transform translate-x-full transition-transform duration-300`;
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <span class="text-lg">${typeIcons[type]}</span>
                <span class="flex-1">${message}</span>
                <button class="notification-close text-white hover:text-gray-300 ml-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }
        
        // Store notification
        this.notifications.push(notification);
        
        return notification;
    }

    /**
     * Close notification
     */
    closeNotification(event) {
        const notification = event.target.closest('.notification');
        if (notification) {
            this.removeNotification(notification);
        }
    }

    /**
     * Remove notification
     */
    removeNotification(notification) {
        if (!notification.parentNode) return;
        
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
            
            // Remove from notifications array
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Escape key - close modal or clear notifications
        if (event.key === 'Escape') {
            if (this.currentModal) {
                this.closeModal();
            } else if (this.notifications.length > 0) {
                this.notifications.forEach(notification => {
                    this.removeNotification(notification);
                });
            }
        }
        
        // Ctrl/Cmd + Enter - submit form
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            const activeForm = document.querySelector('.harvard-form:focus-within');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.click();
                }
            }
        }
    }

    /**
     * Handle window resize
     */
    handleResize() {
        // Adjust modal positioning if needed
        const overlay = document.getElementById('modalOverlay');
        if (overlay && !overlay.classList.contains('hidden')) {
            // Modal auto-adjusts with flexbox, but we could add custom logic here
        }
        
        // Limit notifications on small screens
        if (window.innerWidth < 640) {
            const container = document.getElementById('notificationContainer');
            if (container) {
                container.classList.add('left-4', 'right-4');
                container.style.top = '1rem';
            }
        }
    }

    /**
     * Handle visibility change (tab switching)
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden - reduce activity
            console.log('🔕 Page hidden, reducing UI activity');
        } else {
            // Page is visible - resume normal activity
            console.log('👁️ Page visible, resuming UI activity');
        }
    }

    /**
     * Setup form validation
     */
    setupFormValidation() {
        // Real-time validation on blur
        document.addEventListener('blur', (event) => {
            const field = event.target;
            if (field.matches('[required], [data-validate]')) {
                const errors = this.validateField(field);
                this.showFieldErrors(field, errors);
            }
        }, true);
        
        // Clear errors on input
        document.addEventListener('input', (event) => {
            const field = event.target;
            if (field.matches('[required], [data-validate]')) {
                const existingError = field.parentNode.querySelector('.field-error');
                if (existingError) {
                    field.classList.remove('border-red-500', 'border-crimson');
                    existingError.remove();
                }
            }
        });
    }

    /**
     * Update progress indicators in UI
     */
    updateProgressIndicators(progress) {
        // Update overall progress bar
        const overallProgress = document.getElementById('overallProgress');
        if (overallProgress) {
            const percentage = Math.round(progress.overall * 100);
            overallProgress.style.width = `${percentage}%`;
            overallProgress.setAttribute('aria-valuenow', percentage);
            
            const progressText = document.getElementById('overallProgressText');
            if (progressText) {
                progressText.textContent = `${percentage}%`;
            }
        }
        
        // Update phase progress indicators
        Object.keys(progress.phases || {}).forEach(phase => {
            const phaseElement = document.querySelector(`[data-phase="${phase}"]`);
            if (phaseElement) {
                const phaseProgress = progress.phases[phase];
                const progressBar = phaseElement.querySelector('.phase-progress');
                if (progressBar) {
                    progressBar.style.width = `${Math.round(phaseProgress * 100)}%`;
                }
                
                // Update phase status
                const status = phaseProgress === 1 ? 'completed' : 
                              phaseProgress > 0 ? 'active' : 'pending';
                phaseElement.dataset.status = status;
            }
        });
        
        // Update task counters
        if (progress.tasks) {
            const completedTasks = document.getElementById('completedTasks');
            const totalTasks = document.getElementById('totalTasks');
            
            if (completedTasks) {
                completedTasks.textContent = progress.tasks.completed || 0;
            }
            if (totalTasks) {
                totalTasks.textContent = progress.tasks.total || 0;
            }
        }
    }

    /**
     * Clear all UI state
     */
    clear() {
        // Close any open modals
        this.closeModal();
        
        // Clear notifications
        this.notifications.forEach(notification => {
            this.removeNotification(notification);
        });
        
        // Reset workflow controls
        this.updateWorkflowControls('idle');
        
        // Clear progress indicators
        this.updateProgressIndicators({
            overall: 0,
            phases: {},
            tasks: { completed: 0, total: 0 }
        });
    }
}

// Export for use in other modules
window.HarvardUIManager = HarvardUIManager;