/**
 * Claims Matrix Interactive Frontend - D3.js Mindmap & Decision Trees
 * Phase 3.4 Implementation for Attorney-Ready Legal Analysis Interface
 */

class ClaimsMatrixManager {
    constructor() {
        this.state = {
            currentAnalysis: null,
            mindmapSvg: null,
            mindmapSimulation: null,
            currentNodes: [],
            currentLinks: [],
            selectedElement: null,
            expandedTerms: new Set(),
            factsAttached: new Map(),
            decisionTreeState: {},
            researchCache: new Map(),
            width: 800,
            height: 600
        };

        this.colors = {
            cause: '#f59e0b',
            element: '#3b82f6',
            subElement: '#10b981',
            fact: '#8b5cf6',
            link: '#4b5563',
            linkHover: '#3b82f6',
            text: '#e5e7eb',
            textCentral: '#f59e0b',
            textElement: '#60a5fa'
        };

        this.initialized = false;
    }

    initialize() {
        if (this.initialized) return;

        console.log('Initializing Claims Matrix Manager');
        
        this.bindEventHandlers();
        this.initializeMindmapVisualization();
        
        this.initialized = true;
    }

    bindEventHandlers() {
        // Main control buttons
        const startBtn = document.getElementById('startAnalysisBtn');
        const resetBtn = document.getElementById('resetAnalysisBtn');
        const fullscreenBtn = document.getElementById('fullscreenMindmapBtn');
        const toggleFactsBtn = document.getElementById('toggleFactsPanel');

        if (startBtn) startBtn.addEventListener('click', () => this.startAnalysis());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetAnalysis());
        if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        if (toggleFactsBtn) toggleFactsBtn.addEventListener('click', () => this.toggleFactsPanel());

        // Dropdown change handlers
        const jurisdictionSelect = document.getElementById('claimsMatrixJurisdiction');
        const causeSelect = document.getElementById('claimsMatrixCause');

        if (jurisdictionSelect) jurisdictionSelect.addEventListener('change', () => this.onJurisdictionChange());
        if (causeSelect) causeSelect.addEventListener('change', () => this.onCauseOfActionChange());

        // Window resize handler
        window.addEventListener('resize', () => this.handleResize());
    }

    initializeMindmapVisualization() {
        const container = document.getElementById('claimsMatrixMindmap');
        if (!container) return;

        this.state.width = container.clientWidth;
        this.state.height = container.clientHeight;

        // Clear any existing visualization
        d3.select('#claimsMatrixMindmap svg').remove();

        // Create SVG canvas
        const svg = d3.select('#claimsMatrixMindmap')
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${this.state.width} ${this.state.height}`);

        // Create zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                this.state.mindmapGroup.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Create main group
        const g = svg.append('g');

        // Store references
        this.state.mindmapSvg = svg;
        this.state.mindmapGroup = g;

        console.log('Mindmap visualization initialized');
    }

    async startAnalysis() {
        const jurisdiction = document.getElementById('claimsMatrixJurisdiction').value;
        const causeOfAction = document.getElementById('claimsMatrixCause').value;

        if (!jurisdiction || !causeOfAction) {
            this.showNotification('Please select both jurisdiction and cause of action', 'warning');
            return;
        }

        this.showNotification('Starting Claims Matrix analysis...', 'info');

        try {
            // Start analysis session with backend
            const response = await fetch('/api/claims-matrix/analysis/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jurisdiction: jurisdiction,
                    cause_of_action: causeOfAction,
                    case_facts: []
                })
            });

            const result = await response.json();

            if (result.success) {
                this.state.currentAnalysis = result.session_id;
                
                // Load comprehensive definition and element breakdown
                await this.loadClaimsMatrixData(result.session_id);
                
                // Show panels
                this.showAnalysisPanels();
                
                this.showNotification('Claims Matrix analysis started successfully', 'success');
            } else {
                this.showNotification(result.error || 'Failed to start analysis', 'error');
            }
        } catch (error) {
            console.error('Error starting claims analysis:', error);
            this.showNotification('Failed to start claims analysis', 'error');
        }
    }

    async loadClaimsMatrixData(sessionId) {
        try {
            // Load comprehensive definition
            const definitionResponse = await fetch(`/api/claims-matrix/definition/${sessionId}`);
            const definition = await definitionResponse.json();

            if (definition.success) {
                this.createInteractiveMindmap(definition.data);
            }

            // Load available facts
            await this.loadAvailableFacts();

        } catch (error) {
            console.error('Error loading claims matrix data:', error);
            this.showNotification('Error loading analysis data', 'error');
        }
    }

    createInteractiveMindmap(definitionData) {
        // Hide placeholder
        const placeholder = document.getElementById('mindmapPlaceholder');
        if (placeholder) placeholder.style.display = 'none';

        // Create central node
        const centerX = this.state.width / 2;
        const centerY = this.state.height / 2;

        const nodes = [
            {
                id: 'central',
                type: 'cause',
                label: this.formatLabel(definitionData.cause_of_action),
                definition: definitionData.primary_definition,
                x: centerX,
                y: centerY,
                fx: centerX, // Fixed position
                fy: centerY,
                importance: 1.0
            }
        ];

        // Add element nodes in a circle around central node
        const links = [];
        if (definitionData.elements && definitionData.elements.length > 0) {
            const angleStep = (2 * Math.PI) / definitionData.elements.length;
            const radius = 150;

            definitionData.elements.forEach((element, index) => {
                const angle = index * angleStep;
                const nodeId = `element_${element.name.toLowerCase().replace(/\s+/g, '_')}`;

                nodes.push({
                    id: nodeId,
                    type: 'element',
                    label: element.name,
                    definition: element.definition,
                    questions: element.questions || [],
                    importance: element.importance || 0.8,
                    x: centerX + Math.cos(angle) * radius,
                    y: centerY + Math.sin(angle) * radius
                });

                links.push({
                    source: 'central',
                    target: nodeId,
                    type: 'element-link'
                });
            });
        }

        // Store in state
        this.state.currentNodes = nodes;
        this.state.currentLinks = links;

        // Render the mindmap
        this.renderMindmap();
        
        // Update counters
        this.updateCounters();
    }

    renderMindmap() {
        const { mindmapGroup: g, currentNodes: nodes, currentLinks: links } = this.state;
        
        // Clear previous content
        g.selectAll('*').remove();

        // Create force simulation
        this.state.mindmapSimulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.state.width / 2, this.state.height / 2))
            .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d) + 5));

        // Create links
        const link = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'mindmap-link')
            .attr('stroke', this.colors.link)
            .attr('stroke-width', 2);

        // Create node groups
        const node = g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter().append('g')
            .attr('class', 'mindmap-node')
            .call(this.createDragBehavior());

        // Add circles to nodes
        node.append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => this.getNodeStrokeColor(d))
            .attr('stroke-width', d => d.type === 'cause' ? 3 : 2)
            .on('click', (event, d) => this.handleNodeClick(event, d))
            .on('mouseover', (event, d) => this.handleNodeHover(event, d))
            .on('mouseout', (event, d) => this.handleNodeHoverOut(event, d));

        // Add labels to nodes
        node.append('text')
            .attr('class', d => `mindmap-label ${d.type}`)
            .attr('dy', '.35em')
            .attr('text-anchor', 'middle')
            .style('font-size', d => this.getLabelFontSize(d))
            .style('fill', d => this.getLabelColor(d))
            .style('font-weight', d => d.type === 'cause' ? 'bold' : 'normal')
            .text(d => d.label)
            .style('pointer-events', 'none');

        // Update positions on simulation tick
        this.state.mindmapSimulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }

    createDragBehavior() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.state.mindmapSimulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.state.mindmapSimulation.alphaTarget(0);
                if (d.type !== 'cause') { // Don't release fixed position for central node
                    d.fx = null;
                    d.fy = null;
                }
            });
    }

    getNodeRadius(d) {
        if (d.type === 'cause') return 40;
        return 20 + (d.importance * 20);
    }

    getNodeColor(d) {
        switch (d.type) {
            case 'cause': return this.colors.cause;
            case 'element': return this.colors.element;
            case 'sub-element': return this.colors.subElement;
            default: return '#6b7280';
        }
    }

    getNodeStrokeColor(d) {
        return d.type === 'cause' ? this.colors.cause : '#4b5563';
    }

    getLabelFontSize(d) {
        switch (d.type) {
            case 'cause': return '16px';
            case 'element': return '14px';
            default: return '12px';
        }
    }

    getLabelColor(d) {
        switch (d.type) {
            case 'cause': return this.colors.textCentral;
            case 'element': return this.colors.textElement;
            default: return this.colors.text;
        }
    }

    formatLabel(text) {
        return text.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    handleNodeClick(event, d) {
        console.log('Node clicked:', d);
        
        if (d.type === 'element') {
            this.state.selectedElement = d;
            this.loadElementDecisionTree(d);
            this.highlightSelectedNode(d);
        } else if (d.type === 'cause') {
            this.showCauseDefinitionPopup(event, d);
        }
    }

    handleNodeHover(event, d) {
        this.showDefinitionTooltip(event, d);
        
        // Highlight node
        d3.select(event.currentTarget).select('circle')
            .transition().duration(200)
            .attr('stroke-width', d => d.type === 'cause' ? 4 : 3)
            .attr('stroke', this.colors.linkHover);
    }

    handleNodeHoverOut(event, d) {
        this.hideDefinitionTooltip();
        
        // Restore node appearance
        d3.select(event.currentTarget).select('circle')
            .transition().duration(200)
            .attr('stroke-width', d => d.type === 'cause' ? 3 : 2)
            .attr('stroke', this.getNodeStrokeColor(d));
    }

    showDefinitionTooltip(event, d) {
        // Remove existing tooltip
        d3.select('.definition-tooltip').remove();

        const tooltip = d3.select('body').append('div')
            .attr('class', 'definition-tooltip research-popup')
            .style('opacity', 0)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')
            .style('position', 'absolute')
            .style('z-index', '1000');

        tooltip.html(`
            <div class="text-sm font-medium text-white mb-2">${d.label}</div>
            <div class="text-xs text-gray-300 mb-2">${d.definition || 'Click to expand'}</div>
            ${d.type === 'element' && d.questions ? `
                <div class="text-xs text-blue-300">${d.questions.length} provable questions</div>
            ` : ''}
            ${d.type === 'cause' ? `
                <div class="text-xs text-yellow-300 mt-2">Click for full definition</div>
            ` : ''}
        `);

        tooltip.transition()
            .duration(200)
            .style('opacity', 1);
    }

    hideDefinitionTooltip() {
        d3.select('.definition-tooltip').remove();
    }

    async loadElementDecisionTree(element) {
        if (!this.state.currentAnalysis) return;

        const currentElementName = document.getElementById('currentElementName');
        if (currentElementName) {
            currentElementName.textContent = `${element.label} - Decision Analysis`;
        }

        try {
            const response = await fetch(`/api/claims-matrix/decision-tree/${this.state.currentAnalysis}/${element.id}`);
            const result = await response.json();

            if (result.success) {
                this.renderDecisionTree(result.data);
            }
        } catch (error) {
            console.error('Error loading decision tree:', error);
            this.showNotification('Error loading decision tree', 'error');
        }
    }

    renderDecisionTree(treeData) {
        const container = document.getElementById('decisionTreeContent');
        if (!container) return;

        container.innerHTML = '';

        if (!treeData.questions || treeData.questions.length === 0) {
            container.innerHTML = '<div class="text-gray-400 text-center py-4">No decision tree available for this element</div>';
            return;
        }

        treeData.questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'decision-node mb-4';
            questionDiv.innerHTML = `
                <div class="decision-question text-white mb-2">${question.text}</div>
                <div class="text-xs text-gray-400 mb-3">
                    <span class="px-2 py-1 bg-gray-700 rounded mr-2">${question.type}</span>
                    Evidence: ${question.evidence_types.join(', ')}
                </div>
                <div class="decision-options flex gap-2">
                    <button class="decision-option" data-answer="yes" data-question="${index}">Yes</button>
                    <button class="decision-option" data-answer="no" data-question="${index}">No</button>
                    <button class="decision-option" data-answer="unclear" data-question="${index}">Needs Discovery</button>
                </div>
            `;

            // Bind decision handlers
            questionDiv.querySelectorAll('.decision-option').forEach(btn => {
                btn.addEventListener('click', (e) => this.handleDecisionChoice(e));
            });

            container.appendChild(questionDiv);
        });
    }

    handleDecisionChoice(event) {
        const answer = event.target.dataset.answer;
        const questionIndex = event.target.dataset.question;

        // Update UI
        const siblings = event.target.parentElement.querySelectorAll('.decision-option');
        siblings.forEach(btn => btn.classList.remove('selected'));
        event.target.classList.add('selected');

        // Store decision in state
        const elementId = this.state.selectedElement?.id;
        if (elementId) {
            if (!this.state.decisionTreeState[elementId]) {
                this.state.decisionTreeState[elementId] = {};
            }
            this.state.decisionTreeState[elementId][questionIndex] = {
                answer: answer,
                timestamp: new Date()
            };
        }

        // Provide immediate feedback based on answer
        this.provideFeedback(event.target, answer);
        
        console.log('Decision recorded:', { elementId, questionIndex, answer });
    }

    provideFeedback(buttonElement, answer) {
        let feedbackClass = '';
        let feedbackText = '';

        switch (answer) {
            case 'yes':
                feedbackClass = 'bg-green-600';
                feedbackText = '✓ Element likely satisfied';
                break;
            case 'no':
                feedbackClass = 'bg-red-600';
                feedbackText = '✗ Element may not be satisfied';
                break;
            case 'unclear':
                feedbackClass = 'bg-yellow-600';
                feedbackText = '? Additional discovery needed';
                break;
        }

        // Add feedback indicator
        const existingFeedback = buttonElement.parentElement.parentElement.querySelector('.decision-feedback');
        if (existingFeedback) existingFeedback.remove();

        const feedback = document.createElement('div');
        feedback.className = `decision-feedback text-xs text-white px-2 py-1 rounded mt-2 ${feedbackClass}`;
        feedback.textContent = feedbackText;

        buttonElement.parentElement.parentElement.appendChild(feedback);
    }

    async loadAvailableFacts() {
        try {
            const response = await fetch('/api/knowledge-graph/facts');
            const result = await response.json();

            if (result.success) {
                this.displayAvailableFacts(result.facts);
            }
        } catch (error) {
            console.error('Error loading facts:', error);
        }
    }

    displayAvailableFacts(facts) {
        const container = document.getElementById('availableFacts');
        if (!container) return;

        container.innerHTML = '';

        facts.forEach(fact => {
            const factDiv = document.createElement('div');
            factDiv.className = 'fact-item mb-2 p-3 bg-gray-800 rounded border border-gray-600 cursor-move';
            factDiv.draggable = true;
            factDiv.dataset.factId = fact.id;
            factDiv.innerHTML = `
                <div class="text-sm text-gray-200 mb-1">${fact.text}</div>
                <div class="text-xs text-gray-400 flex justify-between items-center">
                    <span>Source: ${fact.source}</span>
                    <span class="fact-confidence bg-gray-700 px-2 py-1 rounded">
                        ${Math.round(fact.confidence * 100)}%
                    </span>
                </div>
            `;

            // Add drag handlers
            factDiv.addEventListener('dragstart', (e) => this.handleFactDragStart(e));
            factDiv.addEventListener('dragend', (e) => this.handleFactDragEnd(e));

            container.appendChild(factDiv);
        });
    }

    handleFactDragStart(event) {
        event.dataTransfer.setData('text/plain', event.target.dataset.factId);
        event.target.classList.add('dragging', 'opacity-60');
    }

    handleFactDragEnd(event) {
        event.target.classList.remove('dragging', 'opacity-60');
    }

    showAnalysisPanels() {
        const decisionPanel = document.getElementById('decisionTreePanel');
        const factsPanel = document.getElementById('factsAttachmentPanel');
        
        if (decisionPanel) decisionPanel.classList.remove('hidden');
        if (factsPanel) factsPanel.classList.remove('hidden');
    }

    hideAnalysisPanels() {
        const decisionPanel = document.getElementById('decisionTreePanel');
        const factsPanel = document.getElementById('factsAttachmentPanel');
        
        if (decisionPanel) decisionPanel.classList.add('hidden');
        if (factsPanel) factsPanel.classList.add('hidden');
    }

    resetAnalysis() {
        // Clear state
        this.state.currentAnalysis = null;
        this.state.currentNodes = [];
        this.state.currentLinks = [];
        this.state.selectedElement = null;
        this.state.expandedTerms.clear();
        this.state.factsAttached.clear();
        this.state.decisionTreeState = {};

        // Stop simulation
        if (this.state.mindmapSimulation) {
            this.state.mindmapSimulation.stop();
        }

        // Clear visualization
        if (this.state.mindmapGroup) {
            this.state.mindmapGroup.selectAll('*').remove();
        }

        // Show placeholder
        const placeholder = document.getElementById('mindmapPlaceholder');
        if (placeholder) placeholder.style.display = 'flex';

        // Hide panels
        this.hideAnalysisPanels();

        // Reset dropdowns
        const jurisdictionSelect = document.getElementById('claimsMatrixJurisdiction');
        const causeSelect = document.getElementById('claimsMatrixCause');
        
        if (jurisdictionSelect) jurisdictionSelect.value = '';
        if (causeSelect) causeSelect.value = '';

        // Reset counters
        this.updateCounters();

        this.showNotification('Claims Matrix reset', 'info');
    }

    highlightSelectedNode(selectedNode) {
        // Remove previous highlights
        this.state.mindmapGroup.selectAll('.mindmap-node circle')
            .classed('selected', false)
            .attr('stroke-width', d => d.type === 'cause' ? 3 : 2)
            .attr('stroke', d => this.getNodeStrokeColor(d));

        // Highlight selected node
        this.state.mindmapGroup.selectAll('.mindmap-node')
            .filter(d => d.id === selectedNode.id)
            .select('circle')
            .classed('selected', true)
            .attr('stroke-width', 4)
            .attr('stroke', '#10b981');
    }

    updateCounters() {
        const elementCount = this.state.currentNodes.filter(n => n.type === 'element').length;
        const attachedFactsCount = this.state.factsAttached.size;

        const elementCountEl = document.getElementById('elementCount');
        const attachedFactsCountEl = document.getElementById('attachedFactsCount');

        if (elementCountEl) elementCountEl.textContent = elementCount;
        if (attachedFactsCountEl) attachedFactsCountEl.textContent = attachedFactsCount;
    }

    toggleFullscreen() {
        const container = document.getElementById('claimsMatrixMindmap');
        if (!container) return;

        if (!document.fullscreenElement) {
            container.requestFullscreen().catch(err => {
                console.log('Error attempting to enable fullscreen:', err.message);
            });
        } else {
            document.exitFullscreen();
        }
    }

    toggleFactsPanel() {
        const content = document.getElementById('factsAttachmentContent');
        if (!content) return;

        if (content.style.display === 'none') {
            content.style.display = 'grid';
        } else {
            content.style.display = 'none';
        }
    }

    handleResize() {
        const container = document.getElementById('claimsMatrixMindmap');
        if (!container || !this.state.mindmapSvg) return;

        const newWidth = container.clientWidth;
        const newHeight = container.clientHeight;

        if (newWidth !== this.state.width || newHeight !== this.state.height) {
            this.state.width = newWidth;
            this.state.height = newHeight;

            this.state.mindmapSvg.attr('viewBox', `0 0 ${newWidth} ${newHeight}`);
            
            if (this.state.mindmapSimulation) {
                this.state.mindmapSimulation
                    .force('center', d3.forceCenter(newWidth / 2, newHeight / 2))
                    .alpha(0.3).restart();
            }
        }
    }

    onJurisdictionChange() {
        const jurisdiction = document.getElementById('claimsMatrixJurisdiction').value;
        console.log('Jurisdiction changed to:', jurisdiction);
        
        // Update available causes of action based on jurisdiction
        // This would typically fetch jurisdiction-specific causes from the backend
        this.updateAvailableCauses(jurisdiction);
    }

    onCauseOfActionChange() {
        const cause = document.getElementById('claimsMatrixCause').value;
        console.log('Cause of action changed to:', cause);
    }

    updateAvailableCauses(jurisdiction) {
        // Mock implementation - would be replaced with actual API call
        const causeSelect = document.getElementById('claimsMatrixCause');
        if (!causeSelect) return;

        // Clear existing options except the first one
        causeSelect.innerHTML = '<option value="">Select Cause</option>';

        // Add jurisdiction-specific causes
        const causes = {
            'ca_state': [
                { value: 'negligence', text: 'Negligence' },
                { value: 'breach_of_contract', text: 'Breach of Contract' },
                { value: 'fraud', text: 'Fraud' },
                { value: 'iied', text: 'Intentional Infliction of Emotional Distress' },
                { value: 'defamation', text: 'Defamation' }
            ],
            'ca_federal': [
                { value: 'civil_rights', text: 'Civil Rights Violation' },
                { value: 'employment_discrimination', text: 'Employment Discrimination' },
                { value: 'antitrust', text: 'Antitrust Violation' }
            ]
        };

        const jurisdictionCauses = causes[jurisdiction] || causes['ca_state'];
        
        jurisdictionCauses.forEach(cause => {
            const option = document.createElement('option');
            option.value = cause.value;
            option.textContent = cause.text;
            causeSelect.appendChild(option);
        });
    }

    showNotification(message, type = 'info', duration = 5000) {
        // Use the existing notification system from the main app
        if (typeof showNotification === 'function') {
            showNotification(message, type, duration);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    showCauseDefinitionPopup(event, causeNode) {
        // Create a more detailed popup for cause of action definition
        this.hideDefinitionTooltip(); // Hide any existing tooltip

        const popup = d3.select('body').append('div')
            .attr('class', 'cause-definition-popup research-popup')
            .style('opacity', 0)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')
            .style('position', 'absolute')
            .style('z-index', '1001')
            .style('max-width', '400px');

        popup.html(`
            <div class="p-4">
                <div class="text-lg font-medium text-yellow-300 mb-3">${causeNode.label}</div>
                <div class="text-sm text-gray-300 mb-3">${causeNode.definition}</div>
                <div class="text-xs text-gray-400 mb-3">
                    Click on individual elements to explore decision trees and attach case facts.
                </div>
                <button class="close-popup text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded">
                    Close
                </button>
            </div>
        `);

        // Add close handler
        popup.select('.close-popup').on('click', () => {
            popup.remove();
        });

        // Show popup with animation
        popup.transition()
            .duration(200)
            .style('opacity', 1);

        // Auto-close after 10 seconds
        setTimeout(() => {
            if (popup.node()) popup.remove();
        }, 10000);
    }
}

// Initialize Claims Matrix when the page loads
let claimsMatrixManager = null;

// Export for global access
window.ClaimsMatrixManager = ClaimsMatrixManager;

// Initialize function to be called from main application
window.initializeClaimsMatrix = function() {
    if (!claimsMatrixManager) {
        claimsMatrixManager = new ClaimsMatrixManager();
    }
    claimsMatrixManager.initialize();
    return claimsMatrixManager;
};

console.log('Claims Matrix module loaded');