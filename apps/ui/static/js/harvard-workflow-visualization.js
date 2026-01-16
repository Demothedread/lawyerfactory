/**
 * Harvard-Style Workflow Visualization - D3.js Visualizations
 * Handles workflow graph, timeline, and knowledge graph visualizations
 */

class HarvardWorkflowVisualization {
    constructor(app) {
        this.app = app;
        this.workflowGraph = null;
        this.knowledgeGraph = null;
        this.timeline = null;
        this.initialized = false;
    }

    /**
     * Initialize the visualization components
     */
    async initialize() {
        if (this.initialized) return;

        console.log('🎨 Initializing Harvard Workflow Visualization...');
        
        try {
            // Wait for D3 to be available
            if (typeof d3 === 'undefined') {
                console.warn('D3.js not loaded, waiting...');
                await this.waitForD3();
            }
            
            this.setupD3Defaults();
            this.initialized = true;
            console.log('✅ Harvard Workflow Visualization initialized');
            
        } catch (error) {
            console.error('❌ Failed to initialize visualization:', error);
        }
    }

    /**
     * Wait for D3.js to load
     */
    waitForD3() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50;
            
            const checkD3 = () => {
                if (typeof d3 !== 'undefined') {
                    resolve();
                } else if (attempts >= maxAttempts) {
                    reject(new Error('D3.js failed to load'));
                } else {
                    attempts++;
                    setTimeout(checkD3, 100);
                }
            };
            
            checkD3();
        });
    }

    /**
     * Setup D3 defaults and themes
     */
    setupD3Defaults() {
        // Define Harvard color scheme for D3
        this.colorScheme = {
            crimson: '#A51C30',
            crimsonLight: '#C5374D',
            crimsonDark: '#8B1A2D',
            forest: '#1A4B3A',
            forestLight: '#2E6B54',
            forestDark: '#0F3326',
            gold: '#F4C430',
            goldLight: '#F6D055',
            goldDark: '#D1A928',
            silver: '#8E8E93',
            charcoal: '#1C1C1E'
        };

        // Phase colors
        this.phaseColors = {
            'INTAKE': this.colorScheme.crimson,
            'OUTLINE': this.colorScheme.gold,
            'RESEARCH': this.colorScheme.forest,
            'DRAFTING': this.colorScheme.crimsonLight,
            'LEGAL_REVIEW': this.colorScheme.forestLight,
            'EDITING': this.colorScheme.goldLight,
            'ORCHESTRATION': this.colorScheme.forestDark
        };

        // Status colors
        this.statusColors = {
            'pending': this.colorScheme.silver,
            'active': this.colorScheme.gold,
            'completed': this.colorScheme.forest,
            'failed': this.colorScheme.crimsonDark
        };
    }

    /**
     * Initialize workflow graph visualization
     */
    initializeWorkflowGraph() {
        const container = document.getElementById('workflowGraphViz');
        if (!container || this.workflowGraph) return;

        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // Clear any existing content
        d3.select(container).selectAll('*').remove();
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('class', 'workflow-graph-svg');

        // Create workflow nodes data
        const nodes = this.app.state.phases.map((phase, index) => ({
            id: phase,
            name: phase.replace('_', ' '),
            x: (width / (this.app.state.phases.length - 1)) * index,
            y: height / 2,
            status: 'pending',
            color: this.phaseColors[phase] || this.colorScheme.silver,
            index: index
        }));

        // Create links between phases
        const links = [];
        for (let i = 0; i < nodes.length - 1; i++) {
            links.push({
                source: nodes[i],
                target: nodes[i + 1],
                status: 'pending'
            });
        }

        // Create arrowhead marker
        svg.append('defs')
            .append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', this.colorScheme.silver);

        // Create links first (so they appear behind nodes)
        const linkGroup = svg.append('g').attr('class', 'links');
        const links_elements = linkGroup.selectAll('.workflow-link')
            .data(links)
            .enter()
            .append('line')
            .attr('class', 'workflow-link')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y)
            .attr('stroke', this.colorScheme.silver)
            .attr('stroke-width', 3)
            .attr('stroke-opacity', 0.6)
            .attr('marker-end', 'url(#arrowhead)');

        // Create node groups
        const nodeGroup = svg.append('g').attr('class', 'nodes');
        const node_elements = nodeGroup.selectAll('.workflow-node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'workflow-node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .style('cursor', 'pointer');

        // Add node circles
        node_elements.append('circle')
            .attr('r', 25)
            .attr('fill', d => d.color)
            .attr('stroke', this.colorScheme.gold)
            .attr('stroke-width', 2)
            .attr('opacity', 0.9);

        // Add phase icons
        node_elements.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('fill', 'white')
            .attr('font-size', '16px')
            .text(d => this.getPhaseEmoji(d.id));

        // Add phase labels
        node_elements.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '45px')
            .attr('fill', this.colorScheme.gold)
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .attr('font-family', 'Crimson Text, serif')
            .text(d => d.name);

        // Add hover effects
        node_elements
            .on('mouseover', function(event, d) {
                d3.select(this).select('circle')
                    .transition()
                    .duration(200)
                    .attr('r', 30)
                    .attr('stroke-width', 3);
                    
                // Show tooltip
                const tooltip = d3.select('body').append('div')
                    .attr('class', 'workflow-tooltip')
                    .style('position', 'absolute')
                    .style('background', '#1C1C1E')
                    .style('color', '#F8F5E8')
                    .style('padding', '8px 12px')
                    .style('border-radius', '6px')
                    .style('border', '2px solid #F4C430')
                    .style('font-size', '12px')
                    .style('pointer-events', 'none')
                    .style('opacity', 0)
                    .style('z-index', 1000);
                    
                tooltip.html(`
                    <div class="font-bold">${d.name}</div>
                    <div>Status: ${d.status}</div>
                `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .transition()
                .duration(200)
                .style('opacity', 1);
            })
            .on('mouseout', function(event, d) {
                d3.select(this).select('circle')
                    .transition()
                    .duration(200)
                    .attr('r', 25)
                    .attr('stroke-width', 2);
                    
                d3.selectAll('.workflow-tooltip').remove();
            });

        // Store references for updates
        this.workflowGraph = {
            svg,
            nodes,
            links,
            nodeElements: node_elements,
            linkElements: links_elements,
            container
        };

        console.log('📊 Workflow graph initialized');
    }

    /**
     * Get emoji for phase
     */
    getPhaseEmoji(phase) {
        const emojis = {
            'INTAKE': '📥',
            'OUTLINE': '📋',
            'RESEARCH': '🔍',
            'DRAFTING': '✍️',
            'LEGAL_REVIEW': '⚖️',
            'EDITING': '📝',
            'ORCHESTRATION': '🎭'
        };
        return emojis[phase] || '📄';
    }

    /**
     * Update workflow graph based on progress
     */
    updateWorkflowGraph(phaseProgress) {
        if (!this.workflowGraph) return;

        const { nodeElements, linkElements } = this.workflowGraph;

        // Update nodes
        nodeElements.each(function(d) {
            const status = phaseProgress[d.id] || 'pending';
            d.status = status;
            
            const circle = d3.select(this).select('circle');
            const statusColor = status === 'completed' ? '#2E6B54' : 
                               status === 'active' ? '#F4C430' : '#8E8E93';
            
            circle.transition()
                .duration(500)
                .attr('fill', statusColor)
                .attr('stroke', status === 'active' ? '#F4C430' : '#F6D055');
                
            // Add pulsing animation for active phase
            if (status === 'active') {
                circle.style('animation', 'crimsonPulse 2s ease-in-out infinite alternate');
            } else {
                circle.style('animation', 'none');
            }
        });

        // Update links
        linkElements.each(function(d) {
            const sourceStatus = phaseProgress[d.source.id] || 'pending';
            const isActive = sourceStatus === 'completed' || sourceStatus === 'active';
            
            d3.select(this)
                .transition()
                .duration(500)
                .attr('stroke', isActive ? '#F4C430' : '#8E8E93')
                .attr('stroke-opacity', isActive ? 1 : 0.6)
                .attr('stroke-width', isActive ? 4 : 3);
                
            // Add flow animation for active connections
            if (isActive) {
                d3.select(this)
                    .style('stroke-dasharray', '5,5')
                    .style('animation', 'flowAnimation 2s ease-in-out infinite');
            } else {
                d3.select(this)
                    .style('stroke-dasharray', 'none')
                    .style('animation', 'none');
            }
        });
    }

    /**
     * Initialize knowledge graph visualization
     */
    initializeKnowledgeGraph() {
        const container = document.getElementById('knowledgeGraphViz');
        if (!container) return;

        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // Clear any existing content
        d3.select(container).selectAll('*').remove();
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('class', 'knowledge-graph-svg');

        // Create sample knowledge graph data
        const nodes = [
            { id: 'case', name: 'Case', type: 'CASE', group: 1 },
            { id: 'plaintiff', name: 'Plaintiff', type: 'PERSON', group: 2 },
            { id: 'defendant', name: 'Defendant', type: 'PERSON', group: 2 },
            { id: 'contract', name: 'Contract', type: 'DOCUMENT', group: 3 },
            { id: 'breach', name: 'Breach of Contract', type: 'LEGAL_ISSUE', group: 4 },
            { id: 'damages', name: 'Damages', type: 'LEGAL_ISSUE', group: 4 }
        ];

        const links = [
            { source: 'case', target: 'plaintiff', relationship: 'involves' },
            { source: 'case', target: 'defendant', relationship: 'involves' },
            { source: 'case', target: 'contract', relationship: 'concerns' },
            { source: 'contract', target: 'breach', relationship: 'subject_to' },
            { source: 'breach', target: 'damages', relationship: 'results_in' }
        ];

        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));

        // Create links
        const link = svg.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(links)
            .enter()
            .append('line')
            .attr('stroke', this.colorScheme.silver)
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2);

        // Create nodes
        const node = svg.append('g')
            .attr('class', 'nodes')
            .selectAll('.knowledge-node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'knowledge-node')
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragended.bind(this)));

        // Add node circles
        node.append('circle')
            .attr('r', d => d.type === 'CASE' ? 20 : 15)
            .attr('fill', d => this.getNodeColor(d.type))
            .attr('stroke', this.colorScheme.gold)
            .attr('stroke-width', 2);

        // Add node labels
        node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('fill', 'white')
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .text(d => d.name);

        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('transform', d => `translate(${d.x}, ${d.y})`);
        });

        this.knowledgeGraph = { svg, nodes, links, simulation, container };
        console.log('🕸️ Knowledge graph initialized');
    }

    /**
     * Get color for knowledge graph node type
     */
    getNodeColor(type) {
        const colors = {
            'CASE': this.colorScheme.crimson,
            'PERSON': this.colorScheme.forest,
            'DOCUMENT': this.colorScheme.gold,
            'LEGAL_ISSUE': this.colorScheme.forestLight,
            'ORGANIZATION': this.colorScheme.crimsonLight,
            'DATE': this.colorScheme.goldLight
        };
        return colors[type] || this.colorScheme.silver;
    }

    /**
     * Drag event handlers for knowledge graph
     */
    dragstarted(event, d) {
        if (!event.active && this.knowledgeGraph) {
            this.knowledgeGraph.simulation.alphaTarget(0.3).restart();
        }
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(event, d) {
        if (!event.active && this.knowledgeGraph) {
            this.knowledgeGraph.simulation.alphaTarget(0);
        }
        d.fx = null;
        d.fy = null;
    }

    /**
     * Initialize timeline visualization
     */
    initializeTimeline() {
        const container = document.getElementById('timelineEvents');
        if (!container) return;

        // Add timeline line
        const timelineContainer = document.getElementById('timelineContainer');
        if (timelineContainer) {
            const line = timelineContainer.querySelector('.timeline-line');
            if (!line) {
                const timelineLine = document.createElement('div');
                timelineLine.className = 'timeline-line absolute top-0 bottom-0';
                timelineContainer.appendChild(timelineLine);
            }
        }

        this.timeline = { container, events: [] };
        console.log('📅 Timeline initialized');
    }

    /**
     * Add event to timeline
     */
    addTimelineEvent(phase, description, status = 'pending') {
        if (!this.timeline) {
            this.initializeTimeline();
        }

        const { container } = this.timeline;
        const eventDiv = document.createElement('div');
        eventDiv.className = 'flex items-center space-x-4 timeline-event';
        
        const timestamp = new Date().toLocaleTimeString();
        const phaseIcon = this.getPhaseEmoji(phase);
        
        eventDiv.innerHTML = `
            <div class="timeline-node ${status} flex-shrink-0"></div>
            <div class="flex-1 min-w-0">
                <div class="flex items-center space-x-2">
                    <span class="text-lg">${phaseIcon}</span>
                    <span class="font-medium text-white harvard-font">${phase.replace('_', ' ')}</span>
                </div>
                <div class="text-sm text-gray-400">${description}</div>
                <div class="text-xs text-gray-500">${timestamp}</div>
            </div>
        `;
        
        // Add with animation
        eventDiv.style.opacity = '0';
        eventDiv.style.transform = 'translateX(-20px)';
        container.appendChild(eventDiv);
        
        // Animate in
        setTimeout(() => {
            eventDiv.style.transition = 'all 0.3s ease';
            eventDiv.style.opacity = '1';
            eventDiv.style.transform = 'translateX(0)';
        }, 10);
        
        // Store event
        this.timeline.events.push({
            phase,
            description,
            status,
            timestamp: new Date(),
            element: eventDiv
        });
        
        // Limit timeline events (keep last 20)
        if (this.timeline.events.length > 20) {
            const oldEvent = this.timeline.events.shift();
            if (oldEvent.element.parentNode) {
                oldEvent.element.remove();
            }
        }
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    /**
     * Resize visualizations when container size changes
     */
    resize() {
        if (this.workflowGraph) {
            const container = this.workflowGraph.container;
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            this.workflowGraph.svg
                .attr('width', width)
                .attr('height', height);
                
            // Recalculate node positions
            this.workflowGraph.nodes.forEach((node, index) => {
                node.x = (width / (this.workflowGraph.nodes.length - 1)) * index;
                node.y = height / 2;
            });
            
            // Update positions
            this.workflowGraph.nodeElements
                .attr('transform', d => `translate(${d.x}, ${d.y})`);
                
            this.workflowGraph.linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }
        
        if (this.knowledgeGraph) {
            const container = this.knowledgeGraph.container;
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            this.knowledgeGraph.svg
                .attr('width', width)
                .attr('height', height);
                
            this.knowledgeGraph.simulation
                .force('center', d3.forceCenter(width / 2, height / 2))
                .alpha(0.3)
                .restart();
        }
    }

    /**
     * Clear all visualizations
     */
    clear() {
        if (this.workflowGraph) {
            d3.select(this.workflowGraph.container).selectAll('*').remove();
            this.workflowGraph = null;
        }
        
        if (this.knowledgeGraph) {
            this.knowledgeGraph.simulation.stop();
            d3.select(this.knowledgeGraph.container).selectAll('*').remove();
            this.knowledgeGraph = null;
        }
        
        if (this.timeline) {
            this.timeline.container.innerHTML = '';
            this.timeline = null;
        }
    }
}

// Export for use in other modules
window.HarvardWorkflowVisualization = HarvardWorkflowVisualization;

// Handle window resize
window.addEventListener('resize', () => {
    if (window.harvardApp && window.harvardApp.visualization) {
        window.harvardApp.visualization.resize();
    }
});