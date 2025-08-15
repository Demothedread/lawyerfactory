/**
 * Harvard-Style Workflow Visualization - Core Application
 * Main application state management and initialization
 */

class HarvardWorkflowApp {
    constructor() {
        this.state = {
            socket: null,
            currentSession: null,
            workflowData: null,
            knowledgeGraph: { nodes: [], links: [] },
            uploadedFiles: [],
            activeTab: 'case-setup',
            startTime: null,
            currentPhase: null,
            phases: ['INTAKE', 'OUTLINE', 'RESEARCH', 'DRAFTING', 'LEGAL_REVIEW', 'EDITING', 'ORCHESTRATION'],
            phaseProgress: {},
            tasks: {},
            agents: {},
            workflowGraph: null,
            isConnected: false
        };

        this.eventHandlers = new Map();
        this.initialized = false;
    }

    /**
     * Initialize the application
     */
    async initialize() {
        if (this.initialized) return;

        try {
            console.log('🎓 Initializing Harvard Workflow Application...');
            
            // Initialize core components
            this.initializeSocket();
            this.initializeEventHandlers();
            this.initializeWorkflowPhases();
            this.startElapsedTimeCounter();
            
            // Initialize visualization components
            if (window.HarvardWorkflowVisualization) {
                this.visualization = new window.HarvardWorkflowVisualization(this);
                await this.visualization.initialize();
            }

            // Initialize progress tracking
            if (window.HarvardProgressTracker) {
                this.progressTracker = new window.HarvardProgressTracker(this);
                this.progressTracker.initialize();
            }

            // Initialize UI manager
            if (window.HarvardUIManager) {
                this.uiManager = new window.HarvardUIManager(this);
                this.uiManager.initialize();
            }

            this.initialized = true;
            console.log('✅ Harvard Workflow Application initialized successfully');
            
            // Show welcome notification
            this.showNotification('🎓 Harvard-Style LawyerFactory Ready', 'success');
            
        } catch (error) {
            console.error('❌ Failed to initialize Harvard Workflow Application:', error);
            this.showNotification('❌ Failed to initialize application', 'error');
        }
    }

    /**
     * Initialize Socket.IO connection with enhanced error handling
     */
    initializeSocket() {
        try {
            this.state.socket = io({
                autoConnect: true,
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5,
                timeout: 20000
            });
            
            // Connection events
            this.state.socket.on('connect', () => {
                console.log('🔗 Connected to LawyerFactory server');
                this.state.isConnected = true;
                this.updateConnectionStatus(true);
                this.showNotification('🎓 Connected to Harvard-Style LawyerFactory', 'success');
            });
            
            this.state.socket.on('disconnect', (reason) => {
                console.log('❌ Disconnected from server:', reason);
                this.state.isConnected = false;
                this.updateConnectionStatus(false);
                this.showNotification('⚠️ Connection lost to LawyerFactory', 'error');
            });

            this.state.socket.on('connect_error', (error) => {
                console.error('🔌 Connection error:', error);
                this.showNotification('❌ Connection error - retrying...', 'error');
            });

            this.state.socket.on('reconnect', (attemptNumber) => {
                console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
                this.showNotification('✅ Reconnected to LawyerFactory', 'success');
            });
            
            // Enhanced workflow event handlers
            this.state.socket.on('workflow_started', (data) => this.handleWorkflowStarted(data));
            this.state.socket.on('workflow_phase_change', (data) => this.handlePhaseChange(data));
            this.state.socket.on('workflow_progress_update', (data) => this.handleProgressUpdate(data));
            this.state.socket.on('workflow_completed', (data) => this.handleWorkflowCompleted(data));
            this.state.socket.on('approval_required', (data) => this.handleApprovalRequired(data));
            this.state.socket.on('workflow_error', (data) => this.handleWorkflowError(data));
            this.state.socket.on('task_started', (data) => this.handleTaskStarted(data));
            this.state.socket.on('task_completed', (data) => this.handleTaskCompleted(data));
            this.state.socket.on('task_updated', (data) => this.handleTaskUpdated(data));
            this.state.socket.on('agent_activity', (data) => this.handleAgentActivity(data));
            this.state.socket.on('document_generated', (data) => this.handleDocumentGenerated(data));
            
        } catch (error) {
            console.error('❌ Socket initialization failed:', error);
            this.showNotification('❌ Failed to initialize real-time connection', 'error');
        }
    }

    /**
     * Initialize event handlers for UI components
     */
    initializeEventHandlers() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabId = e.target.dataset.tab;
                if (tabId) this.switchTab(tabId);
            });
        });
        
        // Case form submission
        const caseForm = document.getElementById('caseForm');
        if (caseForm) {
            caseForm.addEventListener('submit', (e) => this.handleCaseSubmission(e));
        }
        
        // File upload
        this.initializeFileUpload();
        
        // Document source selection
        document.querySelectorAll('input[name="documentSource"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleDocumentSourceChange(e));
        });
        
        // Modal controls
        const newCaseBtn = document.getElementById('newCaseBtn');
        if (newCaseBtn) {
            newCaseBtn.addEventListener('click', () => this.switchTab('case-setup'));
        }
        
        const viewWorkflowsBtn = document.getElementById('viewWorkflowsBtn');
        if (viewWorkflowsBtn) {
            viewWorkflowsBtn.addEventListener('click', () => this.showWorkflowListModal());
        }
        
        const closeWorkflowListModal = document.getElementById('closeWorkflowListModal');
        if (closeWorkflowListModal) {
            closeWorkflowListModal.addEventListener('click', () => this.hideWorkflowListModal());
        }
        
        // Approval buttons
        const approveBtn = document.getElementById('approveBtn');
        if (approveBtn) {
            approveBtn.addEventListener('click', () => this.submitApproval(true));
        }
        
        const rejectBtn = document.getElementById('rejectBtn');
        if (rejectBtn) {
            rejectBtn.addEventListener('click', () => this.submitApproval(false));
        }
        
        // Download button
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadDocument());
        }
    }

    /**
     * Initialize file upload functionality
     */
    initializeFileUpload() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        
        if (!uploadZone || !fileInput) return;
        
        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        uploadZone.addEventListener('drop', (e) => this.handleFileDrop(e));
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    /**
     * Initialize workflow phases display
     */
    initializeWorkflowPhases() {
        const container = document.getElementById('workflowPhases');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.state.phases.forEach((phase, index) => {
            const phaseDiv = document.createElement('div');
            phaseDiv.className = 'phase-indicator pending flex items-center justify-between p-4 rounded-lg text-sm font-medium transition-all duration-500';
            phaseDiv.id = `phase-${phase}`;
            
            const phaseIcon = this.getPhaseIcon(phase);
            phaseDiv.innerHTML = `
                <div class="flex items-center space-x-3">
                    <span class="text-lg">${phaseIcon}</span>
                    <span class="harvard-font font-semibold">${phase.replace('_', ' ')}</span>
                </div>
                <span class="phase-status text-xs px-2 py-1 rounded-full bg-black/30">Pending</span>
            `;
            container.appendChild(phaseDiv);
        });
    }

    /**
     * Get icon for workflow phase
     */
    getPhaseIcon(phase) {
        const icons = {
            'INTAKE': '📥',
            'OUTLINE': '📋',
            'RESEARCH': '🔍',
            'DRAFTING': '✍️',
            'LEGAL_REVIEW': '⚖️',
            'EDITING': '📝',
            'ORCHESTRATION': '🎭'
        };
        return icons[phase] || '📄';
    }

    /**
     * Switch between tabs
     */
    switchTab(tabId) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Remove active class from all tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        
        // Show selected tab content
        const targetTab = document.getElementById(tabId);
        if (targetTab) {
            targetTab.classList.add('active');
        }
        
        // Activate corresponding button
        const targetButton = document.querySelector(`[data-tab="${tabId}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
        }
        
        this.state.activeTab = tabId;
        
        // Load data for specific tabs
        if (tabId === 'workflow-graph' && this.visualization) {
            this.visualization.initializeWorkflowGraph();
        } else if (tabId === 'knowledge-viz' && this.visualization) {
            this.visualization.initializeKnowledgeGraph();
        }
    }

    /**
     * Update connection status display
     */
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;
        
        const indicator = statusElement.querySelector('div');
        const text = statusElement.querySelector('span');
        
        if (connected) {
            indicator.className = 'w-3 h-3 bg-green-400 rounded-full animate-pulse shadow-lg';
            text.textContent = 'Connected';
        } else {
            indicator.className = 'w-3 h-3 bg-red-400 rounded-full shadow-lg';
            text.textContent = 'Disconnected';
        }
    }

    /**
     * Show notification with Harvard styling
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notifications');
        if (!container) {
            console.log(`Notification: ${message}`);
            return;
        }
        
        const notification = document.createElement('div');
        
        const typeClasses = {
            success: 'border-green-500 bg-green-900/90',
            error: 'border-red-500 bg-red-900/90',
            warning: 'border-yellow-500 bg-yellow-900/90',
            info: 'border-blue-500 bg-blue-900/90'
        };
        
        notification.className = `notification ${typeClasses[type] || typeClasses.info} border-l-4 p-4 rounded-r-lg shadow-lg text-white`;
        notification.innerHTML = `
            <div class="flex justify-between items-start">
                <span class="text-sm font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="text-white/70 hover:text-white ml-4 text-lg font-bold">×</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    }

    /**
     * Start elapsed time counter
     */
    startElapsedTimeCounter() {
        setInterval(() => {
            if (this.state.startTime) {
                const elapsed = new Date() - this.state.startTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                const timeDisplay = document.getElementById('elapsedTimeDisplay');
                if (timeDisplay) {
                    timeDisplay.textContent = 
                        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }
            }
        }, 1000);
    }

    // Workflow Event Handlers
    handleWorkflowStarted(data) {
        console.log('🚀 Workflow started:', data);
        this.state.startTime = new Date();
        this.state.currentSession = data.session_id;
        this.state.workflowData = data;
        this.showNotification(`🚀 Workflow started: ${data.case_name}`, 'success');
        
        if (this.progressTracker) {
            this.progressTracker.onWorkflowStarted(data);
        }
    }

    handlePhaseChange(data) {
        console.log('📋 Phase change:', data);
        this.state.currentPhase = data.to_phase;
        
        const currentPhaseDisplay = document.getElementById('currentPhaseDisplay');
        if (currentPhaseDisplay) {
            currentPhaseDisplay.textContent = data.to_phase;
        }
        
        this.showNotification(`📋 Phase transition: ${data.from_phase} → ${data.to_phase}`, 'info');
        
        if (this.progressTracker) {
            this.progressTracker.onPhaseChange(data);
        }
        
        if (this.uiManager) {
            this.uiManager.addTimelineEvent(data.to_phase, 'Phase Started', 'active');
            if (data.from_phase) {
                this.uiManager.addTimelineEvent(data.from_phase, 'Phase Completed', 'completed');
            }
        }
    }

    handleProgressUpdate(data) {
        console.log('📊 Progress update:', data);
        
        if (this.progressTracker) {
            this.progressTracker.updateProgress(data);
        }
        
        // Update task count display
        const totalTasks = Object.keys(this.state.tasks).length;
        const completedTasks = Object.values(this.state.tasks).filter(task => task.status === 'completed').length;
        const taskCountDisplay = document.getElementById('taskCountDisplay');
        if (taskCountDisplay) {
            taskCountDisplay.textContent = `${completedTasks}/${totalTasks}`;
        }
    }

    handleTaskStarted(data) {
        console.log('⚙️ Task started:', data);
        this.state.tasks[data.task_id] = { ...data, status: 'active' };
        
        if (this.uiManager) {
            this.uiManager.updateTaskDisplay();
        }
        
        this.showNotification(`⚙️ Task started: ${data.description}`, 'info');
    }

    handleTaskCompleted(data) {
        console.log('✅ Task completed:', data);
        this.state.tasks[data.task_id] = { ...data, status: 'completed' };
        
        if (this.uiManager) {
            this.uiManager.updateTaskDisplay();
        }
        
        this.showNotification(`✅ Task completed: ${data.description}`, 'success');
    }

    handleTaskUpdated(data) {
        console.log('🔄 Task updated:', data);
        if (this.state.tasks[data.task_id]) {
            this.state.tasks[data.task_id] = { ...this.state.tasks[data.task_id], ...data };
        }
        
        if (this.uiManager) {
            this.uiManager.updateTaskDisplay();
        }
    }

    handleAgentActivity(data) {
        console.log('🤖 Agent activity:', data);
        this.state.agents[data.agent_id] = data;
        
        if (this.uiManager) {
            this.uiManager.updateAgentDisplay();
        }
    }

    handleWorkflowCompleted(data) {
        console.log('🎉 Workflow completed:', data);
        this.showNotification('🎉 Workflow completed successfully!', 'success');
        
        const downloadSection = document.getElementById('downloadSection');
        if (downloadSection) {
            downloadSection.classList.remove('hidden');
        }
    }

    handleApprovalRequired(data) {
        console.log('👨‍⚖️ Approval required:', data);
        
        const approvalPanel = document.getElementById('approvalPanel');
        const approvalMessage = document.getElementById('approvalMessage');
        
        if (approvalPanel) {
            approvalPanel.classList.remove('hidden');
        }
        
        if (approvalMessage) {
            approvalMessage.textContent = data.message;
        }
        
        this.showNotification('👨‍⚖️ Human review required', 'warning');
    }

    handleWorkflowError(data) {
        console.error('❌ Workflow error:', data);
        this.showNotification(`❌ Workflow error: ${data.error}`, 'error');
    }

    handleDocumentGenerated(data) {
        console.log('📄 Document generated:', data);
        this.showNotification(`📄 Document generated: ${data.document_type}`, 'success');
    }

    // Placeholder methods for UI interactions (to be implemented by UI components)
    async handleCaseSubmission(e) {
        if (this.uiManager) {
            return this.uiManager.handleCaseSubmission(e);
        }
        console.warn('UI Manager not available for case submission');
    }

    handleDragOver(e) {
        if (this.uiManager) {
            return this.uiManager.handleDragOver(e);
        }
    }

    handleDragLeave(e) {
        if (this.uiManager) {
            return this.uiManager.handleDragLeave(e);
        }
    }

    handleFileDrop(e) {
        if (this.uiManager) {
            return this.uiManager.handleFileDrop(e);
        }
    }

    handleFileSelect(e) {
        if (this.uiManager) {
            return this.uiManager.handleFileSelect(e);
        }
    }

    handleDocumentSourceChange(e) {
        if (this.uiManager) {
            return this.uiManager.handleDocumentSourceChange(e);
        }
    }

    showWorkflowListModal() {
        if (this.uiManager) {
            return this.uiManager.showWorkflowListModal();
        }
    }

    hideWorkflowListModal() {
        if (this.uiManager) {
            return this.uiManager.hideWorkflowListModal();
        }
    }

    async submitApproval(approved) {
        if (this.uiManager) {
            return this.uiManager.submitApproval(approved);
        }
    }

    async downloadDocument() {
        if (this.uiManager) {
            return this.uiManager.downloadDocument();
        }
    }
}

// Global instance
window.HarvardWorkflowApp = HarvardWorkflowApp;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.harvardApp = new HarvardWorkflowApp();
    window.harvardApp.initialize();
});