"""
UI Components for Vector Store Integration

This module provides UI components for interacting with the vector store system,
including validation type selectors, vector store status indicators, and
real-time monitoring widgets.

Components:
- ValidationTypeSelector: Dropdown for choosing validation types
- VectorStoreStatusWidget: Real-time status indicators
- SemanticSearchInterface: Search interface for vector stores
- ResearchRoundsMonitor: Monitor research round progress
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from .enhanced_vector_store import (
    EnhancedVectorStoreManager, VectorStoreType, ValidationType
)

logger = logging.getLogger(__name__)


class ValidationTypeSelector:
    """
    UI component for selecting validation types with real-time filtering
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None):
        self.vector_store = vector_store_manager
        self.selected_validation_type = ValidationType.COMPLAINTS_AGAINST_TESLA
        self.on_selection_change: Optional[Callable] = None

        # Available validation types with descriptions
        self.validation_types = {
            ValidationType.COMPLAINTS_AGAINST_TESLA: {
                "name": "Complaints Against Tesla",
                "description": "Filter for complaints specifically against Tesla Inc.",
                "keywords": ["tesla", "elon musk", "autonomous vehicle", "self-driving"],
                "expected_count": "50-200 documents",
                "quality_score": 0.85
            },
            ValidationType.CONTRACT_DISPUTES: {
                "name": "Contract Disputes",
                "description": "General contract breach and dispute cases",
                "keywords": ["breach", "contract", "agreement", "violation"],
                "expected_count": "100-500 documents",
                "quality_score": 0.78
            },
            ValidationType.PERSONAL_INJURY: {
                "name": "Personal Injury",
                "description": "Personal injury and negligence cases",
                "keywords": ["injury", "accident", "negligence", "damages"],
                "expected_count": "75-300 documents",
                "quality_score": 0.82
            },
            ValidationType.EMPLOYMENT_CLAIMS: {
                "name": "Employment Claims",
                "description": "Wrongful termination and employment disputes",
                "keywords": ["employment", "wrongful termination", "discrimination"],
                "expected_count": "60-250 documents",
                "quality_score": 0.80
            },
            ValidationType.INTELLECTUAL_PROPERTY: {
                "name": "Intellectual Property",
                "description": "Patent, copyright, and trademark disputes",
                "keywords": ["patent", "copyright", "trademark", "infringement"],
                "expected_count": "40-150 documents",
                "quality_score": 0.88
            }
        }

    def render_html(self) -> str:
        """Render the validation type selector as HTML"""
        options_html = ""

        for validation_type, info in self.validation_types.items():
            selected = "selected" if validation_type == self.selected_validation_type else ""
            options_html += f'''
                <option value="{validation_type.value}" {selected}>
                    {info["name"]}
                </option>
            '''

        html = f'''
            <div class="validation-type-selector console-panel" style="margin-bottom: 1rem;">
                <div class="panel-header">
                    <h3 style="color: var(--emerald-green); margin: 0;">
                        <i class="fas fa-filter"></i> VALIDATION TYPE SELECTOR
                    </h3>
                </div>

                <div style="padding: 1rem;">
                    <div style="margin-bottom: 1rem;">
                        <label for="validationTypeSelect" style="color: var(--metallic-silver); font-size: 0.9rem;">
                            Select Validation Type:
                        </label>
                        <select id="validationTypeSelect" class="gizmo-dial"
                                style="width: 100%; margin-top: 0.5rem; padding: 0.5rem;">
                            {options_html}
                        </select>
                    </div>

                    <div id="validationTypeInfo" style="background: rgba(80,200,120,0.1);
                                                       border: 1px solid var(--emerald-green);
                                                       border-radius: 8px; padding: 1rem;">
                        {self._get_validation_type_info_html()}
                    </div>

                    <div style="margin-top: 1rem; text-align: center;">
                        <button id="applyValidationFilter" class="gizmo-dial"
                                style="background: var(--emerald-green); color: black; border: none;">
                            <i class="fas fa-check"></i> Apply Filter
                        </button>
                    </div>
                </div>
            </div>

            <script>
                // Validation type selector functionality
                document.getElementById('validationTypeSelect').addEventListener('change', function(e) {{
                    const selectedType = e.target.value;
                    updateValidationTypeInfo(selectedType);
                }});

                document.getElementById('applyValidationFilter').addEventListener('click', function() {{
                    const selectedType = document.getElementById('validationTypeSelect').value;
                    applyValidationFilter(selectedType);
                }});

                function updateValidationTypeInfo(validationType) {{
                    const info = {json.dumps({k.value: v for k, v in self.validation_types.items()})}[validationType];
                    if (info) {{
                        document.getElementById('validationTypeInfo').innerHTML = `
                            <div style="color: var(--metallic-silver);">
                                <h4 style="color: var(--emerald-green); margin: 0 0 0.5rem 0;">${{info.name}}</h4>
                                <p style="margin: 0 0 0.5rem 0; font-size: 0.9rem;">${{info.description}}</p>
                                <div style="font-size: 0.8rem; opacity: 0.8;">
                                    <div><strong>Keywords:</strong> ${{info.keywords.join(', ')}}</div>
                                    <div><strong>Expected:</strong> ${{info.expected_count}}</div>
                                    <div><strong>Quality Score:</strong> ${(info.quality_score * 100).toFixed(1)}%</div>
                                </div>
                            </div>
                        `;
                    }}
                }}

                function applyValidationFilter(validationType) {{
                    // Send filter request to backend
                    fetch('/api/vector-store/apply-validation-filter', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            validation_type: validationType
                        }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            showNotification(`Applied ${validationType} filter. Found ${data.document_count} documents.`, 'success');
                            updateVectorStoreStatus();
                        }} else {{
                            showNotification('Failed to apply validation filter.', 'error');
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error applying validation filter:', error);
                        showNotification('Error applying validation filter.', 'error');
                    }});
                }}

                function showNotification(message, type) {{
                    // Implementation depends on existing notification system
                    console.log(`[${type.toUpperCase()}] ${message}`);
                }}

                function updateVectorStoreStatus() {{
                    // Trigger status update
                    if (window.updateVectorStoreStatus) {{
                        window.updateVectorStoreStatus();
                    }}
                }}
            </script>
        '''

        return html

    def _get_validation_type_info_html(self) -> str:
        """Get HTML for current validation type info"""
        info = self.validation_types[self.selected_validation_type]
        return f'''
            <div style="color: var(--metallic-silver);">
                <h4 style="color: var(--emerald-green); margin: 0 0 0.5rem 0;">{info["name"]}</h4>
                <p style="margin: 0 0 0.5rem 0; font-size: 0.9rem;">{info["description"]}</p>
                <div style="font-size: 0.8rem; opacity: 0.8;">
                    <div><strong>Keywords:</strong> {", ".join(info["keywords"])}</div>
                    <div><strong>Expected:</strong> {info["expected_count"]}</div>
                    <div><strong>Quality Score:</strong> {info["quality_score"]*100:.1f}%</div>
                </div>
            </div>
        '''

    def set_selected_type(self, validation_type: ValidationType):
        """Set the selected validation type"""
        self.selected_validation_type = validation_type

    def get_selected_type(self) -> ValidationType:
        """Get the currently selected validation type"""
        return self.selected_validation_type

    def get_available_types(self) -> Dict[ValidationType, Dict[str, Any]]:
        """Get all available validation types with their info"""
        return self.validation_types.copy()


class VectorStoreStatusWidget:
    """
    Real-time status widget for vector store monitoring
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None):
        self.vector_store = vector_store_manager

    def render_html(self) -> str:
        """Render the status widget as HTML"""
        html = '''
            <div class="vector-store-status console-panel" style="margin-bottom: 1rem;">
                <div class="panel-header">
                    <h3 style="color: var(--gold-accent); margin: 0;">
                        <i class="fas fa-database"></i> VECTOR STORE STATUS
                    </h3>
                </div>

                <div id="vectorStoreStatus" style="padding: 1rem;">
                    <div class="status-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="status-item">
                            <div style="color: var(--emerald-green); font-size: 0.8rem;">PRIMARY EVIDENCE</div>
                            <div id="primaryEvidenceCount" style="color: var(--metallic-silver); font-size: 1.2rem; font-weight: bold;">0</div>
                        </div>
                        <div class="status-item">
                            <div style="color: var(--emerald-green); font-size: 0.8rem;">CASE OPINIONS</div>
                            <div id="caseOpinionsCount" style="color: var(--metallic-silver); font-size: 1.2rem; font-weight: bold;">0</div>
                        </div>
                        <div class="status-item">
                            <div style="color: var(--emerald-green); font-size: 0.8rem;">GENERAL RAG</div>
                            <div id="generalRagCount" style="color: var(--metallic-silver); font-size: 1.2rem; font-weight: bold;">0</div>
                        </div>
                        <div class="status-item">
                            <div style="color: var(--emerald-green); font-size: 0.8rem;">VALIDATION SUB-VECTORS</div>
                            <div id="validationSubVectorsCount" style="color: var(--metallic-silver); font-size: 1.2rem; font-weight: bold;">0</div>
                        </div>
                    </div>

                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--oxidized-copper);">
                        <div style="color: var(--metallic-silver); font-size: 0.9rem; margin-bottom: 0.5rem;">
                            <strong>System Health:</strong>
                        </div>
                        <div class="health-indicators" style="display: flex; gap: 1rem;">
                            <div class="health-item">
                                <span style="color: var(--emerald-green);">●</span>
                                <span id="cacheStatus" style="color: var(--metallic-silver); font-size: 0.8rem;">Cache: OK</span>
                            </div>
                            <div class="health-item">
                                <span style="color: var(--emerald-green);">●</span>
                                <span id="embeddingStatus" style="color: var(--metallic-silver); font-size: 0.8rem;">Embedding: OK</span>
                            </div>
                            <div class="health-item">
                                <span style="color: var(--emerald-green);">●</span>
                                <span id="storageStatus" style="color: var(--metallic-silver); font-size: 0.8rem;">Storage: OK</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Vector store status functionality
                async function updateVectorStoreStatus() {
                    try {
                        const response = await fetch('/api/vector-store/status');
                        const data = await response.json();

                        if (data.success) {
                            document.getElementById('primaryEvidenceCount').textContent = data.stores.primary_evidence?.documents || 0;
                            document.getElementById('caseOpinionsCount').textContent = data.stores.case_opinions?.documents || 0;
                            document.getElementById('generalRagCount').textContent = data.stores.general_rag?.documents || 0;
                            document.getElementById('validationSubVectorsCount').textContent = data.validation_sub_vectors || 0;

                            // Update health indicators
                            updateHealthIndicators(data.health);
                        }
                    } catch (error) {
                        console.error('Error updating vector store status:', error);
                    }
                }

                function updateHealthIndicators(health) {
                    const cacheStatus = document.getElementById('cacheStatus');
                    const embeddingStatus = document.getElementById('embeddingStatus');
                    const storageStatus = document.getElementById('storageStatus');

                    // Update cache status
                    if (health.cache_hit_rate > 0.8) {
                        cacheStatus.innerHTML = '<span style="color: var(--emerald-green);">●</span> Cache: Excellent';
                    } else if (health.cache_hit_rate > 0.6) {
                        cacheStatus.innerHTML = '<span style="color: var(--gold-accent);">●</span> Cache: Good';
                    } else {
                        cacheStatus.innerHTML = '<span style="color: var(--oxidized-copper);">●</span> Cache: Warming Up';
                    }

                    // Update embedding status
                    embeddingStatus.innerHTML = '<span style="color: var(--emerald-green);">●</span> Embedding: OK';

                    // Update storage status
                    const totalStorage = Object.values(health.stores).reduce((sum, store) => sum + (store.storage_mb || 0), 0);
                    if (totalStorage < 100) {
                        storageStatus.innerHTML = '<span style="color: var(--emerald-green);">●</span> Storage: Light';
                    } else if (totalStorage < 500) {
                        storageStatus.innerHTML = '<span style="color: var(--gold-accent);">●</span> Storage: Moderate';
                    } else {
                        storageStatus.innerHTML = '<span style="color: var(--oxidized-copper);">●</span> Storage: Heavy';
                    }
                }

                // Auto-update every 30 seconds
                setInterval(updateVectorStoreStatus, 30000);

                // Initial update
                updateVectorStoreStatus();

                // Make function globally available
                window.updateVectorStoreStatus = updateVectorStoreStatus;
            </script>
        '''

        return html

    async def get_status_data(self) -> Dict[str, Any]:
        """Get current status data"""
        if not self.vector_store:
            return {"error": "Vector store manager not available"}

        metrics = await self.vector_store.get_store_metrics()

        return {
            "success": True,
            "stores": metrics.get("stores", {}),
            "validation_sub_vectors": metrics.get("validation_sub_vectors", 0),
            "health": {
                "cache_hit_rate": metrics.get("cache_hit_rate", 0.0),
                "total_documents": metrics.get("total_documents", 0),
                "total_vectors": metrics.get("total_vectors", 0)
            }
        }


class SemanticSearchInterface:
    """
    Search interface for vector stores with real-time results
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None):
        self.vector_store = vector_store_manager

    def render_html(self) -> str:
        """Render the search interface as HTML"""
        html = '''
            <div class="semantic-search console-panel" style="margin-bottom: 1rem;">
                <div class="panel-header">
                    <h3 style="color: var(--emerald-green); margin: 0;">
                        <i class="fas fa-search"></i> SEMANTIC SEARCH
                    </h3>
                </div>

                <div style="padding: 1rem;">
                    <div style="margin-bottom: 1rem;">
                        <input type="text" id="semanticSearchQuery"
                               placeholder="Enter your search query..."
                               style="width: 100%; padding: 0.5rem; background: var(--industrial-gray);
                                      border: 2px solid var(--oxidized-copper); border-radius: 4px;
                                      color: var(--metallic-silver);">
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <select id="searchStoreType" class="gizmo-dial" style="width: 100%; padding: 0.5rem;">
                            <option value="">All Stores</option>
                            <option value="primary_evidence">Primary Evidence</option>
                            <option value="case_opinions">Case Opinions</option>
                            <option value="general_rag">General RAG</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <button id="performSemanticSearch" class="gizmo-dial"
                                style="width: 100%; background: var(--emerald-green); color: black; border: none;">
                            <i class="fas fa-search"></i> Search
                        </button>
                    </div>

                    <div id="searchResults" style="max-height: 300px; overflow-y: auto;">
                        <!-- Search results will appear here -->
                    </div>
                </div>
            </div>

            <script>
                // Semantic search functionality
                document.getElementById('performSemanticSearch').addEventListener('click', performSearch);
                document.getElementById('semanticSearchQuery').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        performSearch();
                    }
                });

                async function performSearch() {
                    const query = document.getElementById('semanticSearchQuery').value.trim();
                    const storeType = document.getElementById('searchStoreType').value;

                    if (!query) {
                        showNotification('Please enter a search query.', 'warning');
                        return;
                    }

                    try {
                        const response = await fetch('/api/vector-store/search', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                query: query,
                                store_type: storeType || null,
                                top_k: 10
                            })
                        });

                        const data = await response.json();

                        if (data.success) {
                            displaySearchResults(data.results);
                        } else {
                            showNotification('Search failed: ' + data.error, 'error');
                        }
                    } catch (error) {
                        console.error('Error performing semantic search:', error);
                        showNotification('Error performing search.', 'error');
                    }
                }

                function displaySearchResults(results) {
                    const resultsContainer = document.getElementById('searchResults');

                    if (!results || results.length === 0) {
                        resultsContainer.innerHTML = '<div style="color: var(--oxidized-copper); text-align: center; padding: 2rem;">No results found.</div>';
                        return;
                    }

                    let html = '<div style="color: var(--metallic-silver);">';
                    html += `<div style="margin-bottom: 1rem; font-size: 0.9rem;">Found ${results.length} results:</div>`;

                    results.forEach((result, index) => {
                        const doc = result.document;
                        const score = result.similarity_score;

                        html += `
                            <div style="margin-bottom: 1rem; padding: 1rem; background: rgba(47, 47, 47, 0.5);
                                        border: 1px solid var(--oxidized-copper); border-radius: 4px;">
                                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 0.5rem;">
                                    <div style="font-weight: bold; color: var(--emerald-green);">
                                        Result ${index + 1}
                                    </div>
                                    <div style="font-size: 0.8rem; color: var(--gold-accent);">
                                        Similarity: ${(score * 100).toFixed(1)}%
                                    </div>
                                </div>
                                <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">
                                    ${doc.content.substring(0, 200)}${doc.content.length > 200 ? '...' : ''}
                                </div>
                                <div style="font-size: 0.8rem; opacity: 0.7;">
                                    Store: ${doc.store_type} | Type: ${doc.metadata.content_type || 'Unknown'}
                                </div>
                            </div>
                        `;
                    });

                    html += '</div>';
                    resultsContainer.innerHTML = html;
                }

                function showNotification(message, type) {
                    // Implementation depends on existing notification system
                    console.log(`[${type.toUpperCase()}] ${message}`);
                }
            </script>
        '''

        return html


# Global instances for easy access
validation_type_selector = ValidationTypeSelector()
vector_store_status_widget = VectorStoreStatusWidget()
semantic_search_interface = SemanticSearchInterface()