/**
 * Harvard-Style Workflow Visualization - Progress Tracker
 * Handles real-time progress tracking and visualization updates
 */

class HarvardProgressTracker {
    constructor(app) {
        this.app = app;
        this.progressData = {
            percentage: 0,
            currentPhase: null,
            phaseProgress: {},
            taskProgress: {},
            estimatedCompletion: null
        };
        this.initialized = false;
    }

    /**
     * Initialize the progress tracker
     */
    initialize() {
        if (this.initialized) return;

        console.log('📊 Initializing Harvard Progress Tracker...');
        
        // Initialize progress indicators
        this.initializeProgressRing();
        this.initializePhaseIndicators();
        this.setupProgressAnimations();
        
        this.initialized = true;
        console.log('✅ Harvard Progress Tracker initialized');
    }

    /**
     * Initialize the circular progress ring
     */
    initializeProgressRing() {
        const progressRing = document.getElementById('progressRingFill');
        if (!progressRing) return;

        // Set initial state
        const circumference = 314.16; // 2 * π * 50
        progressRing.style.strokeDasharray = circumference;
        progressRing.style.strokeDashoffset = circumference;
        
        // Add gradient definition if not exists
        const svg = progressRing.closest('svg');
        if (svg && !svg.querySelector('#gradientProgress')) {
            const defs = svg.querySelector('defs') || svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'defs'));
            const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
            gradient.id = 'gradientProgress';
            gradient.setAttribute('x1', '0%');
            gradient.setAttribute('y1', '0%');
            gradient.setAttribute('x2', '100%');
            gradient.setAttribute('y2', '0%');
            
            const stops = [
                { offset: '0%', color: '#A51C30' },   // Harvard Crimson
                { offset: '50%', color: '#F4C430' },  // Harvard Gold
                { offset: '100%', color: '#1A4B3A' }  // Harvard Forest
            ];
            
            stops.forEach(stop => {
                const stopElement = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                stopElement.setAttribute('offset', stop.offset);
                stopElement.setAttribute('style', `stop-color:${stop.color}`);
                gradient.appendChild(stopElement);
            });
            
            defs.appendChild(gradient);
        }
    }

    /**
     * Initialize phase indicators
     */
    initializePhaseIndicators() {
        this.app.state.phases.forEach(phase => {
            this.updatePhaseIndicator(phase, 'pending');
        });
    }

    /**
     * Setup progress animations
     */
    setupProgressAnimations() {
        // Add CSS animations for progress elements
        const style = document.createElement('style');
        style.textContent = `
            .progress-pulse {
                animation: progressPulse 2s ease-in-out infinite;
            }
            
            @keyframes progressPulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(1.05); }
            }
            
            .progress-glow {
                filter: drop-shadow(0 0 8px var(--harvard-gold));
                transition: filter 0.3s ease;
            }
            
            .phase-transition {
                transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Handle workflow started event
     */
    onWorkflowStarted(data) {
        console.log('📊 Progress tracker: Workflow started');
        
        this.progressData = {
            percentage: 0,
            currentPhase: 'INTAKE',
            phaseProgress: {},
            taskProgress: {},
            estimatedCompletion: null,
            startTime: new Date()
        };

        // Initialize all phases as pending
        this.app.state.phases.forEach(phase => {
            this.progressData.phaseProgress[phase] = 'pending';
            this.updatePhaseIndicator(phase, 'pending');
        });

        // Set first phase as active
        this.progressData.phaseProgress['INTAKE'] = 'active';
        this.updatePhaseIndicator('INTAKE', 'active');
        
        this.updateProgressDisplay();
        this.showCurrentWorkflow();
    }

    /**
     * Handle phase change event
     */
    onPhaseChange(data) {
        console.log('📊 Progress tracker: Phase change', data);
        
        // Update phase statuses
        if (data.from_phase) {
            this.progressData.phaseProgress[data.from_phase] = 'completed';
            this.updatePhaseIndicator(data.from_phase, 'completed');
        }
        
        this.progressData.phaseProgress[data.to_phase] = 'active';
        this.updatePhaseIndicator(data.to_phase, 'active');
        
        this.progressData.currentPhase = data.to_phase;
        
        // Calculate phase-based progress
        const completedPhases = Object.values(this.progressData.phaseProgress).filter(status => status === 'completed').length;
        const phaseProgress = (completedPhases / this.app.state.phases.length) * 100;
        
        // Update progress if not provided by server
        if (!data.progress_percentage) {
            this.updateProgressPercentage(phaseProgress);
        }
    }

    /**
     * Update overall progress
     */
    updateProgress(data) {
        console.log('📊 Progress tracker: Progress update', data);
        
        if (data.progress_percentage !== undefined) {
            this.updateProgressPercentage(data.progress_percentage);
        }
        
        if (data.phases) {
            Object.entries(data.phases).forEach(([phase, status]) => {
                this.progressData.phaseProgress[phase] = status;
                this.updatePhaseIndicator(phase, status);
            });
        }
        
        if (data.tasks) {
            this.progressData.taskProgress = data.tasks;
        }
        
        if (data.estimated_completion) {
            this.progressData.estimatedCompletion = new Date(data.estimated_completion);
        }
        
        this.updateProgressDisplay();
        this.updateProgressMetrics();
    }

    /**
     * Update progress percentage
     */
    updateProgressPercentage(percentage) {
        this.progressData.percentage = Math.min(100, Math.max(0, percentage));
        
        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${this.progressData.percentage}%`;
            
            // Add glow effect when progressing
            if (percentage > 0) {
                progressBar.classList.add('progress-glow');
            }
        }
        
        // Update progress ring
        const progressRing = document.getElementById('progressRingFill');
        if (progressRing) {
            const circumference = 314.16;
            const offset = circumference - (this.progressData.percentage / 100) * circumference;
            progressRing.style.strokeDashoffset = offset;
        }
        
        // Update percentage display
        const progressPercentage = document.getElementById('progressPercentage');
        if (progressPercentage) {
            progressPercentage.textContent = `${Math.round(this.progressData.percentage)}%`;
            
            // Add pulse effect for milestones
            if (this.progressData.percentage % 25 === 0 && this.progressData.percentage > 0) {
                progressPercentage.classList.add('progress-pulse');
                setTimeout(() => {
                    progressPercentage.classList.remove('progress-pulse');
                }, 2000);
            }
        }
    }

    /**
     * Update phase indicator
     */
    updatePhaseIndicator(phase, status) {
        const phaseElement = document.getElementById(`phase-${phase}`);
        if (!phaseElement) return;
        
        // Remove all status classes
        phaseElement.classList.remove('pending', 'active', 'completed', 'failed');
        
        // Add new status class with transition
        phaseElement.classList.add('phase-transition', status);
        
        // Update status text
        const statusSpan = phaseElement.querySelector('.phase-status');
        if (statusSpan) {
            statusSpan.textContent = status.replace('_', ' ').toUpperCase();
            
            // Add status-specific styling
            statusSpan.className = `phase-status text-xs px-2 py-1 rounded-full ${this.getStatusBadgeClass(status)}`;
        }
        
        // Add completion animation
        if (status === 'completed') {
            this.animatePhaseCompletion(phaseElement);
        } else if (status === 'active') {
            this.animatePhaseActivation(phaseElement);
        }
    }

    /**
     * Get CSS class for status badge
     */
    getStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-gray-600 text-gray-300',
            'active': 'bg-yellow-600 text-yellow-100',
            'completed': 'bg-green-600 text-green-100',
            'failed': 'bg-red-600 text-red-100'
        };
        return classes[status] || classes['pending'];
    }

    /**
     * Animate phase completion
     */
    animatePhaseCompletion(element) {
        // Add completion glow effect
        element.style.boxShadow = '0 0 20px rgba(46, 107, 84, 0.8)';
        
        // Create completion particles effect
        this.createCompletionParticles(element);
        
        setTimeout(() => {
            element.style.boxShadow = '';
        }, 1000);
    }

    /**
     * Animate phase activation
     */
    animatePhaseActivation(element) {
        // Add activation pulse
        element.classList.add('progress-pulse');
        
        setTimeout(() => {
            element.classList.remove('progress-pulse');
        }, 2000);
    }

    /**
     * Create completion particles effect
     */
    createCompletionParticles(element) {
        const rect = element.getBoundingClientRect();
        const particles = [];
        
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: fixed;
                width: 4px;
                height: 4px;
                background: #F4C430;
                border-radius: 50%;
                pointer-events: none;
                z-index: 1000;
                left: ${rect.left + rect.width / 2}px;
                top: ${rect.top + rect.height / 2}px;
                animation: particleBurst 0.8s ease-out forwards;
                animation-delay: ${i * 0.1}s;
            `;
            
            document.body.appendChild(particle);
            particles.push(particle);
            
            setTimeout(() => {
                particle.remove();
            }, 1000);
        }
        
        // Add particle animation styles if not exists
        if (!document.querySelector('#particleStyles')) {
            const style = document.createElement('style');
            style.id = 'particleStyles';
            style.textContent = `
                @keyframes particleBurst {
                    0% {
                        opacity: 1;
                        transform: scale(1) translate(0, 0);
                    }
                    100% {
                        opacity: 0;
                        transform: scale(0.5) translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Update progress display elements
     */
    updateProgressDisplay() {
        const progressText = document.getElementById('progressText');
        if (progressText) {
            const status = this.getProgressStatusText();
            progressText.textContent = status;
        }
        
        // Update workflow status
        const workflowStatus = document.getElementById('workflowStatus');
        if (workflowStatus) {
            workflowStatus.textContent = this.getCurrentPhaseDescription();
        }
    }

    /**
     * Get progress status text
     */
    getProgressStatusText() {
        if (this.progressData.percentage === 0) return 'Starting...';
        if (this.progressData.percentage === 100) return 'Completed';
        if (this.progressData.currentPhase) {
            return `Processing ${this.progressData.currentPhase.replace('_', ' ')}`;
        }
        return 'In Progress';
    }

    /**
     * Get current phase description
     */
    getCurrentPhaseDescription() {
        const descriptions = {
            'INTAKE': 'Analyzing uploaded documents and case information',
            'OUTLINE': 'Creating legal document structure and outline',
            'RESEARCH': 'Conducting legal research and case law analysis',
            'DRAFTING': 'Drafting legal documents and arguments',
            'LEGAL_REVIEW': 'Reviewing legal accuracy and compliance',
            'EDITING': 'Editing and refining document content',
            'ORCHESTRATION': 'Final review and document assembly'
        };
        
        return descriptions[this.progressData.currentPhase] || 'Processing workflow';
    }

    /**
     * Update progress metrics
     */
    updateProgressMetrics() {
        // Update estimated completion time
        if (this.progressData.estimatedCompletion) {
            const estimatedElement = document.getElementById('estimatedCompletion');
            if (estimatedElement) {
                const timeString = this.progressData.estimatedCompletion.toLocaleTimeString();
                estimatedElement.textContent = `Est. completion: ${timeString}`;
            }
        }
        
        // Update task progress
        const taskMetrics = this.calculateTaskMetrics();
        const taskCountDisplay = document.getElementById('taskCountDisplay');
        if (taskCountDisplay) {
            taskCountDisplay.textContent = `${taskMetrics.completed}/${taskMetrics.total}`;
        }
    }

    /**
     * Calculate task metrics
     */
    calculateTaskMetrics() {
        const tasks = Object.values(this.app.state.tasks);
        return {
            total: tasks.length,
            completed: tasks.filter(task => task.status === 'completed').length,
            active: tasks.filter(task => task.status === 'active' || task.status === 'in_progress').length,
            failed: tasks.filter(task => task.status === 'failed').length
        };
    }

    /**
     * Show current workflow
     */
    showCurrentWorkflow() {
        const currentWorkflow = document.getElementById('currentWorkflow');
        const noWorkflow = document.getElementById('noWorkflow');
        
        if (currentWorkflow) {
            currentWorkflow.classList.remove('hidden');
        }
        
        if (noWorkflow) {
            noWorkflow.classList.add('hidden');
        }
        
        // Update workflow case name
        const workflowCaseName = document.getElementById('workflowCaseName');
        if (workflowCaseName && this.app.state.workflowData) {
            workflowCaseName.textContent = this.app.state.workflowData.case_name || 'Unknown Case';
        }
    }

    /**
     * Reset progress tracker
     */
    reset() {
        this.progressData = {
            percentage: 0,
            currentPhase: null,
            phaseProgress: {},
            taskProgress: {},
            estimatedCompletion: null
        };
        
        // Reset all phase indicators
        this.app.state.phases.forEach(phase => {
            this.updatePhaseIndicator(phase, 'pending');
        });
        
        // Reset progress displays
        this.updateProgressPercentage(0);
        this.updateProgressDisplay();
        
        // Hide current workflow
        const currentWorkflow = document.getElementById('currentWorkflow');
        const noWorkflow = document.getElementById('noWorkflow');
        
        if (currentWorkflow) {
            currentWorkflow.classList.add('hidden');
        }
        
        if (noWorkflow) {
            noWorkflow.classList.remove('hidden');
        }
    }

    /**
     * Get current progress data
     */
    getProgressData() {
        return { ...this.progressData };
    }

    /**
     * Export progress metrics for analytics
     */
    exportMetrics() {
        const metrics = {
            timestamp: new Date().toISOString(),
            percentage: this.progressData.percentage,
            currentPhase: this.progressData.currentPhase,
            phaseProgress: { ...this.progressData.phaseProgress },
            taskMetrics: this.calculateTaskMetrics(),
            elapsedTime: this.progressData.startTime ? 
                new Date() - this.progressData.startTime : 0
        };
        
        return metrics;
    }
}

// Export for use in other modules
window.HarvardProgressTracker = HarvardProgressTracker;