/**
 * Enhanced Evidence Table JavaScript Module
 * Interactive, sortable, filterable evidence management interface
 */

class EvidenceTableManager {
    constructor() {
        this.evidenceData = [];
        this.factsData = [];
        this.claimsData = [];
        this.currentFilters = {};
        this.sortConfig = { column: null, direction: 'asc' };
        this.selectedRows = new Set();
        
        this.init();
    }
    
    async init() {
        await this.loadEvidenceData();
        this.setupEventListeners();
        this.renderTable();
        this.setupFilters();
    }
    
    async loadEvidenceData() {
        try {
            const response = await fetch('/api/evidence');
            if (response.ok) {
                const data = await response.json();
                this.evidenceData = data.evidence_entries || [];
                this.factsData = data.fact_assertions || [];
                this.claimsData = data.claim_entries || [];
                this.updateStats(data.stats);
            } else {
                console.error('Failed to load evidence data');
            }
        } catch (error) {
            console.error('Error loading evidence data:', error);
        }
    }
    
    setupEventListeners() {
        // Add evidence button
        document.getElementById('add-evidence-btn')?.addEventListener('click', () => {
            this.showAddEvidenceModal();
        });
        
        // Export button
        document.getElementById('export-evidence-btn')?.addEventListener('click', () => {
            this.showExportModal();
        });
        
        // Search input
        document.getElementById('evidence-search')?.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        // Filter dropdowns
        document.getElementById('evidence-type-filter')?.addEventListener('change', (e) => {
            this.updateFilter('evidence_type', e.target.value);
        });
        
        document.getElementById('relevance-filter')?.addEventListener('change', (e) => {
            this.updateFilter('relevance_level', e.target.value);
        });
        
        // Real-time updates via Socket.IO
        if (window.socket) {
            window.socket.on('evidence_updated', (data) => {
                this.handleEvidenceUpdate(data);
            });
        }
    }
    
    renderTable() {
        const tableBody = document.getElementById('evidence-table-body');
        if (!tableBody) return;
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // Apply filters and sorting
        let filteredData = this.applyFilters(this.evidenceData);
        filteredData = this.applySorting(filteredData);
        
        // Render rows
        filteredData.forEach(evidence => {
            const row = this.createEvidenceRow(evidence);
            tableBody.appendChild(row);
        });
        
        // Update pagination if needed
        this.updatePagination(filteredData.length);
    }
    
    createEvidenceRow(evidence) {
        const row = document.createElement('tr');
        row.className = 'evidence-row hover:bg-gray-50 transition-colors';
        row.dataset.evidenceId = evidence.evidence_id;
        
        // Checkbox
        const checkboxCell = document.createElement('td');
        checkboxCell.className = 'px-4 py-3';
        checkboxCell.innerHTML = `
            <input type="checkbox" class="evidence-checkbox" value="${evidence.evidence_id}"
                   onchange="evidenceTable.toggleRowSelection('${evidence.evidence_id}')">
        `;
        row.appendChild(checkboxCell);
        
        // Evidence ID (shortened)
        const idCell = document.createElement('td');
        idCell.className = 'px-4 py-3 text-sm font-mono';
        idCell.textContent = evidence.evidence_id.substring(0, 8) + '...';
        idCell.title = evidence.evidence_id;
        row.appendChild(idCell);
        
        // Source Document
        const sourceCell = document.createElement('td');
        sourceCell.className = 'px-4 py-3 text-sm';
        sourceCell.innerHTML = `
            <div class="font-medium text-gray-900">${this.escapeHtml(evidence.source_document)}</div>
            ${evidence.page_section ? `<div class="text-gray-500 text-xs">${this.escapeHtml(evidence.page_section)}</div>` : ''}
        `;
        row.appendChild(sourceCell);
        
        // Content Preview
        const contentCell = document.createElement('td');
        contentCell.className = 'px-4 py-3 text-sm max-w-md';
        const contentPreview = evidence.content.length > 100 
            ? evidence.content.substring(0, 100) + '...'
            : evidence.content;
        contentCell.innerHTML = `
            <div class="truncate" title="${this.escapeHtml(evidence.content)}">
                ${this.escapeHtml(contentPreview)}
            </div>
        `;
        row.appendChild(contentCell);
        
        // Evidence Type
        const typeCell = document.createElement('td');
        typeCell.className = 'px-4 py-3 text-sm';
        typeCell.innerHTML = `
            <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${this.getTypeColor(evidence.evidence_type)}">
                ${evidence.evidence_type}
            </span>
        `;
        row.appendChild(typeCell);
        
        // Relevance Score
        const relevanceCell = document.createElement('td');
        relevanceCell.className = 'px-4 py-3 text-sm';
        relevanceCell.innerHTML = `
            <div class="flex items-center">
                <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                    <div class="h-2 rounded-full ${this.getRelevanceColor(evidence.relevance_score)}" 
                         style="width: ${evidence.relevance_score * 100}%"></div>
                </div>
                <span class="text-xs font-medium">${(evidence.relevance_score * 100).toFixed(0)}%</span>
            </div>
        `;
        row.appendChild(relevanceCell);
        
        // Supporting Facts Count
        const factsCell = document.createElement('td');
        factsCell.className = 'px-4 py-3 text-sm text-center';
        factsCell.innerHTML = `
            <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                ${evidence.supporting_facts.length}
            </span>
        `;
        row.appendChild(factsCell);
        
        // Citation
        const citationCell = document.createElement('td');
        citationCell.className = 'px-4 py-3 text-sm font-mono';
        citationCell.textContent = evidence.bluebook_citation || 'N/A';
        row.appendChild(citationCell);
        
        // Actions
        const actionsCell = document.createElement('td');
        actionsCell.className = 'px-4 py-3 text-sm';
        actionsCell.innerHTML = `
            <div class="flex space-x-2">
                <button onclick="evidenceTable.editEvidence('${evidence.evidence_id}')" 
                        class="text-blue-600 hover:text-blue-800 transition-colors" title="Edit">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                </button>
                <button onclick="evidenceTable.linkToFact('${evidence.evidence_id}')" 
                        class="text-green-600 hover:text-green-800 transition-colors" title="Link to Fact">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                    </svg>
                </button>
                <button onclick="evidenceTable.deleteEvidence('${evidence.evidence_id}')" 
                        class="text-red-600 hover:text-red-800 transition-colors" title="Delete">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        `;
        row.appendChild(actionsCell);
        
        // Add click handler for row selection
        row.addEventListener('click', (e) => {
            if (!e.target.closest('button') && !e.target.closest('input')) {
                this.selectRow(evidence.evidence_id);
            }
        });
        
        return row;
    }
    
    getTypeColor(type) {
        const colors = {
            'documentary': 'bg-blue-100 text-blue-800',
            'testimonial': 'bg-green-100 text-green-800',
            'expert': 'bg-purple-100 text-purple-800',
            'physical': 'bg-yellow-100 text-yellow-800',
            'digital': 'bg-indigo-100 text-indigo-800',
            'photographic': 'bg-pink-100 text-pink-800'
        };
        return colors[type] || 'bg-gray-100 text-gray-800';
    }
    
    getRelevanceColor(score) {
        if (score >= 0.8) return 'bg-green-500';
        if (score >= 0.6) return 'bg-yellow-500';
        if (score >= 0.4) return 'bg-orange-500';
        return 'bg-red-500';
    }
    
    applyFilters(data) {
        return data.filter(evidence => {
            for (const [key, value] of Object.entries(this.currentFilters)) {
                if (!value) continue;
                
                if (key === 'search') {
                    const searchTerm = value.toLowerCase();
                    const searchableFields = [
                        evidence.source_document,
                        evidence.content,
                        evidence.bluebook_citation,
                        evidence.notes
                    ].join(' ').toLowerCase();
                    
                    if (!searchableFields.includes(searchTerm)) {
                        return false;
                    }
                } else if (evidence[key] !== value) {
                    return false;
                }
            }
            return true;
        });
    }
    
    applySorting(data) {
        if (!this.sortConfig.column) return data;
        
        return [...data].sort((a, b) => {
            const aVal = a[this.sortConfig.column];
            const bVal = b[this.sortConfig.column];
            
            let comparison = 0;
            if (aVal < bVal) comparison = -1;
            if (aVal > bVal) comparison = 1;
            
            return this.sortConfig.direction === 'desc' ? -comparison : comparison;
        });
    }
    
    updateFilter(key, value) {
        if (value === '') {
            delete this.currentFilters[key];
        } else {
            this.currentFilters[key] = value;
        }
        this.renderTable();
    }
    
    handleSearch(searchTerm) {
        this.updateFilter('search', searchTerm);
    }
    
    sortBy(column) {
        if (this.sortConfig.column === column) {
            this.sortConfig.direction = this.sortConfig.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortConfig.column = column;
            this.sortConfig.direction = 'asc';
        }
        this.renderTable();
        this.updateSortIndicators();
    }
    
    updateSortIndicators() {
        // Remove existing sort indicators
        document.querySelectorAll('.sort-indicator').forEach(el => el.remove());
        
        // Add current sort indicator
        const header = document.querySelector(`[data-sort="${this.sortConfig.column}"]`);
        if (header) {
            const indicator = document.createElement('span');
            indicator.className = 'sort-indicator ml-1';
            indicator.innerHTML = this.sortConfig.direction === 'asc' ? '↑' : '↓';
            header.appendChild(indicator);
        }
    }
    
    toggleRowSelection(evidenceId) {
        const checkbox = document.querySelector(`input[value="${evidenceId}"]`);
        if (checkbox.checked) {
            this.selectedRows.add(evidenceId);
        } else {
            this.selectedRows.delete(evidenceId);
        }
        this.updateBulkActions();
    }
    
    selectRow(evidenceId) {
        // Implementation for row details or editing
        console.log('Selected evidence:', evidenceId);
    }
    
    updateBulkActions() {
        const bulkActionsContainer = document.getElementById('bulk-actions');
        if (bulkActionsContainer) {
            bulkActionsContainer.style.display = this.selectedRows.size > 0 ? 'block' : 'none';
            document.getElementById('selected-count').textContent = this.selectedRows.size;
        }
    }
    
    async showAddEvidenceModal() {
        // Implementation for add evidence modal
        const modal = document.getElementById('evidence-modal');
        if (modal) {
            modal.style.display = 'block';
            this.resetEvidenceForm();
        }
    }
    
    async editEvidence(evidenceId) {
        const evidence = this.evidenceData.find(e => e.evidence_id === evidenceId);
        if (evidence) {
            this.showAddEvidenceModal();
            this.populateEvidenceForm(evidence);
        }
    }
    
    async deleteEvidence(evidenceId) {
        if (confirm('Are you sure you want to delete this evidence entry?')) {
            try {
                const response = await fetch(`/api/evidence/${evidenceId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    await this.loadEvidenceData();
                    this.renderTable();
                    this.showNotification('Evidence entry deleted successfully', 'success');
                } else {
                    this.showNotification('Failed to delete evidence entry', 'error');
                }
            } catch (error) {
                console.error('Error deleting evidence:', error);
                this.showNotification('Error deleting evidence entry', 'error');
            }
        }
    }
    
    async linkToFact(evidenceId) {
        // Implementation for linking evidence to facts
        const modal = document.getElementById('link-fact-modal');
        if (modal) {
            modal.style.display = 'block';
            this.populateFactsSelector(evidenceId);
        }
    }
    
    showExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }
    
    async exportData(format) {
        try {
            const response = await fetch(`/api/evidence/export?format=${format}`);
            if (response.ok) {
                if (format === 'csv') {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `evidence_table_${new Date().toISOString().split('T')[0]}.csv`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    const data = await response.json();
                    const jsonStr = JSON.stringify(data, null, 2);
                    const blob = new Blob([jsonStr], { type: 'application/json' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `evidence_table_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                }
                this.showNotification('Export completed successfully', 'success');
            } else {
                this.showNotification('Export failed', 'error');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Export error', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        // Implementation for showing notifications
        const notification = document.createElement('div');
        notification.className = `notification ${type} fixed top-4 right-4 p-4 rounded shadow-lg z-50`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    updateStats(stats) {
        if (stats) {
            document.getElementById('total-evidence')?.textContent = stats.total_evidence || 0;
            document.getElementById('total-facts')?.textContent = stats.total_facts || 0;
            document.getElementById('total-claims')?.textContent = stats.total_claims || 0;
            document.getElementById('avg-relevance')?.textContent = 
                stats.average_relevance_score ? `${(stats.average_relevance_score * 100).toFixed(1)}%` : 'N/A';
        }
    }
    
    handleEvidenceUpdate(data) {
        // Handle real-time updates from WebSocket
        this.loadEvidenceData().then(() => {
            this.renderTable();
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize evidence table when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.evidenceTable = new EvidenceTableManager();
});