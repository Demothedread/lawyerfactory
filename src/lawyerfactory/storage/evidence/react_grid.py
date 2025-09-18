"""
Enhanced Evidence Table with React Data Grid Integration

This module provides an interactive evidence management system with:
- React-based ag-Grid data table with advanced features
- Real-time data manipulation and filtering
- Sparkline visualization for evidence metrics
- Backend integration for CRUD operations
- Collaborative editing capabilities
"""

from dataclasses import asdict
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

from .table import EvidenceEntry, EvidenceType, PrivilegeMarker, RelevanceLevel

logger = logging.getLogger(__name__)

# React component template for evidence data grid
EVIDENCE_GRID_COMPONENT = """
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { Sparklines, SparklinesLine, SparklinesSpots } from 'react-sparklines';
import io from 'socket.io-client';

interface EvidenceEntry {
  evidence_id: string;
  object_id?: string;
  source_document: string;
  page_section: string;
  content: string;
  evidence_type: string;
  relevance_score: number;
  relevance_level: string;
  supporting_facts: string[];
  bluebook_citation: string;
  privilege_marker: string;
  extracted_date?: string;
  witness_name?: string;
  key_terms: string[];
  notes: string;
  created_at: string;
  last_modified: string;
  created_by: string;
  metrics_history?: number[];
}

interface EvidenceDataGridProps {
  evidenceData: EvidenceEntry[];
  onEvidenceUpdate: (evidence: EvidenceEntry) => void;
  onEvidenceDelete: (evidenceId: string) => void;
  onEvidenceAdd: (evidence: Partial<EvidenceEntry>) => void;
  readOnly?: boolean;
  enableSparklines?: boolean;
  backendUrl?: string;
}

const EvidenceDataGrid: React.FC<EvidenceDataGridProps> = ({
  evidenceData,
  onEvidenceUpdate,
  onEvidenceDelete,
  onEvidenceAdd,
  readOnly = false,
  enableSparklines = true,
  backendUrl = 'http://localhost:5000'
}) => {
  const [gridApi, setGridApi] = useState<any>(null);
  const [columnApi, setColumnApi] = useState<any>(null);
  const [socket, setSocket] = useState<any>(null);
  const [filterText, setFilterText] = useState('');
  const [selectedRows, setSelectedRows] = useState<EvidenceEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize socket connection for real-time updates
  useEffect(() => {
    const newSocket = io(backendUrl);
    setSocket(newSocket);

    // Join evidence collaboration room
    newSocket.emit('join_evidence_room', { room: 'evidence_main' });

    // Listen for real-time updates
    newSocket.on('evidence_created', (data: any) => {
      if (gridApi) {
        const newRow = data.evidence;
        gridApi.applyTransaction({ add: [newRow] });
      }
    });

    newSocket.on('evidence_updated', (data: any) => {
      if (gridApi) {
        const updatedRow = data.evidence;
        gridApi.applyTransaction({ update: [updatedRow] });
      }
    });

    newSocket.on('evidence_deleted', (data: any) => {
      if (gridApi) {
        gridApi.applyTransaction({ remove: [{ evidence_id: data.evidence_id }] });
      }
    });

    newSocket.on('evidence_grid_synced', (data: any) => {
      if (gridApi) {
        gridApi.setRowData(data.data);
      }
    });

    newSocket.on('evidence_filter_updated', (data: any) => {
      // Handle collaborative filtering
      console.log('Collaborative filter applied:', data.filters);
    });

    return () => {
      newSocket.emit('leave_evidence_room', { room: 'evidence_main' });
      newSocket.disconnect();
    };
  }, [backendUrl, gridApi]);

  // Load data from API on mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`${backendUrl}/api/evidence`);
        const result = await response.json();
        if (result.success && gridApi) {
          gridApi.setRowData(result.data);
        } else {
          setError(result.error || 'Failed to load evidence data');
        }
      } catch (err) {
        setError('Network error while loading evidence data');
        console.error('Error loading evidence data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (gridApi) {
      loadData();
    }
  }, [gridApi, backendUrl]);

  // Custom cell renderers
  const RelevanceScoreRenderer = (props: any) => {
    const score = props.value || 0;
    const color = score > 0.8 ? '#10b981' : score > 0.6 ? '#f59e0b' : '#ef4444';

    return (
      <div className="flex items-center space-x-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span>{(score * 100).toFixed(1)}%</span>
        {enableSparklines && props.data.metrics_history && (
          <Sparklines data={props.data.metrics_history} width={50} height={20}>
            <SparklinesLine color={color} />
            <SparklinesSpots />
          </Sparklines>
        )}
      </div>
    );
  };

  const EvidenceTypeRenderer = (props: any) => {
    const typeColors: Record<string, string> = {
      documentary: '#3b82f6',
      testimonial: '#8b5cf6',
      expert: '#f59e0b',
      physical: '#10b981',
      digital: '#ef4444',
      photographic: '#06b6d4'
    };

    return (
      <span
        className="px-2 py-1 rounded-full text-xs font-medium text-white"
        style={{ backgroundColor: typeColors[props.value] || '#6b7280' }}
      >
        {props.value}
      </span>
    );
  };

  const ActionsRenderer = (props: any) => {
    if (readOnly) return null;

    const handleEdit = async () => {
      // Open edit modal or inline editing
      if (onEvidenceUpdate) {
        onEvidenceUpdate(props.data);
      }
    };

    const handleDelete = async () => {
      if (window.confirm('Are you sure you want to delete this evidence?')) {
        try {
          const response = await fetch(`${backendUrl}/api/evidence/${props.data.evidence_id}`, {
            method: 'DELETE'
          });
          const result = await response.json();
          if (result.success) {
            if (onEvidenceDelete) {
              onEvidenceDelete(props.data.evidence_id);
            }
          } else {
            alert('Failed to delete evidence: ' + result.error);
          }
        } catch (err) {
          alert('Network error while deleting evidence');
          console.error('Error deleting evidence:', err);
        }
      }
    };

    return (
      <div className="flex space-x-1">
        <button
          onClick={handleEdit}
          className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
        >
          Edit
        </button>
        <button
          onClick={handleDelete}
          className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
        >
          Delete
        </button>
      </div>
    );
  };

  // Column definitions
  const columnDefs = useMemo(() => [
    {
      field: 'evidence_id',
      headerName: 'ID',
      width: 120,
      pinned: 'left',
      cellRenderer: (props: any) => (
        <span className="font-mono text-xs">{props.value?.substring(0, 8)}...</span>
      )
    },
    {
      field: 'source_document',
      headerName: 'Source',
      width: 150,
      filter: 'agTextColumnFilter'
    },
    {
      field: 'page_section',
      headerName: 'Section',
      width: 100
    },
    {
      field: 'content',
      headerName: 'Content',
      width: 300,
      cellRenderer: (props: any) => (
        <div className="truncate" title={props.value}>
          {props.value?.substring(0, 100)}...
        </div>
      )
    },
    {
      field: 'evidence_type',
      headerName: 'Type',
      width: 120,
      cellRenderer: 'evidenceTypeRenderer',
      filter: 'agSetColumnFilter',
      filterParams: {
        values: ['documentary', 'testimonial', 'expert', 'physical', 'digital', 'photographic']
      }
    },
    {
      field: 'relevance_score',
      headerName: 'Relevance',
      width: 140,
      cellRenderer: 'relevanceScoreRenderer',
      sortable: true,
      filter: 'agNumberColumnFilter'
    },
    {
      field: 'relevance_level',
      headerName: 'Level',
      width: 100,
      cellRenderer: (props: any) => {
        const colors: Record<string, string> = {
          critical: '#ef4444',
          high: '#f59e0b',
          medium: '#3b82f6',
          low: '#6b7280',
          unknown: '#9ca3af'
        };
        return (
          <span
            className="px-2 py-1 rounded text-xs font-medium text-white"
            style={{ backgroundColor: colors[props.value] || '#6b7280' }}
          >
            {props.value}
          </span>
        );
      },
      filter: 'agSetColumnFilter',
      filterParams: {
        values: ['critical', 'high', 'medium', 'low', 'unknown']
      }
    },
    {
      field: 'bluebook_citation',
      headerName: 'Citation',
      width: 200,
      cellRenderer: (props: any) => (
        <span className="font-mono text-xs">{props.value || 'N/A'}</span>
      )
    },
    {
      field: 'privilege_marker',
      headerName: 'Privilege',
      width: 120,
      cellRenderer: (props: any) => {
        const colors: Record<string, string> = {
          none: '#10b981',
          attorney_client: '#ef4444',
          work_product: '#f59e0b',
          confidential: '#8b5cf6',
          redacted: '#6b7280'
        };
        return (
          <span
            className="px-2 py-1 rounded text-xs font-medium text-white"
            style={{ backgroundColor: colors[props.value] || '#6b7280' }}
          >
            {props.value}
          </span>
        );
      },
      filter: 'agSetColumnFilter',
      filterParams: {
        values: ['none', 'attorney_client', 'work_product', 'confidential', 'redacted']
      }
    },
    {
      field: 'key_terms',
      headerName: 'Key Terms',
      width: 150,
      cellRenderer: (props: any) => (
        <div className="flex flex-wrap gap-1">
          {props.value?.slice(0, 3).map((term: string, idx: number) => (
            <span key={idx} className="px-1 py-0.5 bg-gray-200 text-gray-800 rounded text-xs">
              {term}
            </span>
          ))}
          {props.value?.length > 3 && (
            <span className="text-xs text-gray-500">+{props.value.length - 3} more</span>
          )}
        </div>
      )
    },
    {
      field: 'last_modified',
      headerName: 'Modified',
      width: 150,
      sortable: true,
      valueFormatter: (params: any) => {
        return new Date(params.value).toLocaleString();
      }
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      cellRenderer: 'actionsRenderer',
      pinned: 'right'
    }
  ], [readOnly, enableSparklines]);

  // Grid options
  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: true,
  }), []);

  const gridOptions = useMemo(() => ({
    enableRangeSelection: true,
    enableCharts: true,
    enableAdvancedFilter: true,
    rowSelection: 'multiple',
    suppressRowClickSelection: true,
    animateRows: true,
    pagination: true,
    paginationPageSize: 50,
    sideBar: {
      toolPanels: [
        {
          id: 'columns',
          labelDefault: 'Columns',
          labelKey: 'columns',
          iconKey: 'columns',
          toolPanel: 'agColumnsToolPanel',
        },
        {
          id: 'filters',
          labelDefault: 'Filters',
          labelKey: 'filters',
          iconKey: 'filter',
          toolPanel: 'agFiltersToolPanel',
        },
      ],
    },
  }), []);

  // Event handlers
  const onGridReady = useCallback((params: any) => {
    setGridApi(params.api);
    setColumnApi(params.columnApi);
  }, []);

  const onSelectionChanged = useCallback(() => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes();
      const selectedData = selectedNodes.map((node: any) => node.data);
      setSelectedRows(selectedData);
    }
  }, [gridApi]);

  const onFilterChanged = useCallback((event: any) => {
    setFilterText(event.api.getFilterModel());
  }, []);

  const exportToCsv = useCallback(() => {
    if (gridApi) {
      gridApi.exportDataAsCsv({
        fileName: `evidence_export_${new Date().toISOString().split('T')[0]}.csv`
      });
    }
  }, [gridApi]);

  const exportToExcel = useCallback(() => {
    if (gridApi) {
      // Note: Requires ag-grid-enterprise for Excel export
      gridApi.exportDataAsExcel({
        fileName: `evidence_export_${new Date().toISOString().split('T')[0]}.xlsx`
      });
    }
  }, [gridApi]);

  // API Integration Functions
  const createEvidence = useCallback(async (evidenceData: Partial<EvidenceEntry>) => {
    try {
      const response = await fetch(`${backendUrl}/api/evidence`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(evidenceData),
      });
      const result = await response.json();
      if (result.success) {
        // Data will be updated via Socket.IO
        return result.evidence_id;
      } else {
        throw new Error(result.error || 'Failed to create evidence');
      }
    } catch (err) {
      console.error('Error creating evidence:', err);
      throw err;
    }
  }, [backendUrl]);

  const updateEvidence = useCallback(async (evidenceId: string, updates: Partial<EvidenceEntry>) => {
    try {
      const response = await fetch(`${backendUrl}/api/evidence/${evidenceId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to update evidence');
      }
    } catch (err) {
      console.error('Error updating evidence:', err);
      throw err;
    }
  }, [backendUrl]);

  const refreshData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${backendUrl}/api/evidence`);
      const result = await response.json();
      if (result.success && gridApi) {
        gridApi.setRowData(result.data);
      } else {
        setError(result.error || 'Failed to refresh evidence data');
      }
    } catch (err) {
      setError('Network error while refreshing evidence data');
      console.error('Error refreshing evidence data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [gridApi, backendUrl]);

  return (
    <div className="evidence-data-grid w-full h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-800">Evidence Management</h3>
          <span className="text-sm text-gray-600">
            {evidenceData.length} entries
          </span>
          {isLoading && (
            <span className="text-sm text-blue-600">Loading...</span>
          )}
          {error && (
            <span className="text-sm text-red-600">Error: {error}</span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={refreshData}
            disabled={isLoading}
            className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm disabled:opacity-50"
            title="Refresh data from server"
          >
            🔄 Refresh
          </button>

          {!readOnly && (
            <button
              onClick={() => {
                const newEvidence = {
                  source_document: 'new_document.pdf',
                  content: 'New evidence content...',
                  evidence_type: 'documentary',
                  relevance_score: 0.5,
                  relevance_level: 'medium',
                  key_terms: [],
                  notes: 'New evidence entry'
                };
                createEvidence(newEvidence).catch(err => {
                  alert('Failed to create evidence: ' + err.message);
                });
              }}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
            >
              ➕ Add Evidence
            </button>
          )}

          <button
            onClick={exportToCsv}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            📊 Export CSV
          </button>

          <button
            onClick={exportToExcel}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 text-sm"
          >
            📈 Export Excel
          </button>
        </div>
      </div>

      {/* Grid Container */}
      <div className="ag-theme-alpine flex-1">
        <AgGridReact
          rowData={evidenceData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          gridOptions={gridOptions}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          onFilterChanged={onFilterChanged}
          components={{
            relevanceScoreRenderer: RelevanceScoreRenderer,
            evidenceTypeRenderer: EvidenceTypeRenderer,
            actionsRenderer: ActionsRenderer,
          }}
          frameworkComponents={{
            sparklinesRenderer: SparklinesRenderer,
          }}
        />
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between p-2 bg-gray-100 border-t text-sm text-gray-600">
        <div>
          {selectedRows.length > 0 && (
            <span>{selectedRows.length} row(s) selected</span>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <span>Filter: {Object.keys(filterText).length} active</span>
          <span>Real-time: {socket ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </div>
  );
};

export default EvidenceDataGrid;
"""


class ReactEvidenceDataGrid:
    """
    React-based evidence data grid with ag-Grid integration
    """

    def __init__(self, storage_path: str = "./data/evidence"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.react_component_path = self.storage_path / "evidence_grid.jsx"

        # Generate React component
        self._generate_react_component()

    def _generate_react_component(self):
        """Generate the React component file"""
        try:
            with open(self.react_component_path, "w", encoding="utf-8") as f:
                f.write(EVIDENCE_GRID_COMPONENT)
            logger.info(f"Generated React evidence grid component at {self.react_component_path}")
        except Exception as e:
            logger.error(f"Failed to generate React component: {e}")

    def get_component_html(self) -> str:
        """Get HTML template for embedding the React component"""
        return f"""
        <div id="evidence-grid-container" class="w-full h-96">
          <div id="evidence-grid-root"></div>
        </div>
        <script src="https://unpkg.com/react@17/umd/react.development.js"></script>
        <script src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <script type="text/babel" data-presets="react" src="{self.react_component_path}"></script>
        """

    def get_grid_data(self, evidence_entries: List[EvidenceEntry]) -> List[Dict[str, Any]]:
        """Convert evidence entries to grid-compatible format"""
        grid_data: List[Dict[str, Any]] = []
        for entry in evidence_entries:
            entry_dict = asdict(entry)

            # Add metrics history for sparklines (mock data for now)
            entry_dict["metrics_history"] = [
                entry.relevance_score * 0.8 + 0.1,
                entry.relevance_score * 0.9 + 0.05,
                entry.relevance_score,
                entry.relevance_score * 1.1 - 0.05,
                entry.relevance_score * 1.05,
            ]

            grid_data.append(entry_dict)

        return grid_data

    def update_evidence_entry(self, evidence_id: str, updates: Dict[str, Any]) -> bool:
        """Update an evidence entry via the grid"""
        try:
            # This would integrate with the backend API
            logger.info(f"Updating evidence entry {evidence_id} with {updates}")
            return True
        except Exception as e:
            logger.error(f"Failed to update evidence entry: {e}")
            return False

    def delete_evidence_entry(self, evidence_id: str) -> bool:
        """Delete an evidence entry via the grid"""
        try:
            # This would integrate with the backend API
            logger.info(f"Deleting evidence entry {evidence_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete evidence entry: {e}")
            return False

    def add_evidence_entry(self, evidence_data: Dict[str, Any]) -> Optional[str]:
        """Add a new evidence entry via the grid"""
        try:
            # Generate new evidence ID
            new_id = str(uuid.uuid4())

            # Create new evidence entry
            new_entry = EvidenceEntry(evidence_id=new_id, **evidence_data)

            logger.info(f"Added new evidence entry {new_id}")
            return new_id
        except Exception as e:
            logger.error(f"Failed to add evidence entry: {e}")
            return None

    # API Integration Methods
    async def fetch_evidence_data(
        self, backend_url: str = "http://localhost:5000"
    ) -> List[Dict[str, Any]]:
        """Fetch evidence data from the backend API"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backend_url}/api/evidence") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            return data.get("data", [])
                        else:
                            logger.error(f"API error: {data.get('error')}")
                            return []
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return []
        except ImportError:
            logger.warning("aiohttp not available, using synchronous requests")
            return self._fetch_evidence_data_sync(backend_url)
        except Exception as e:
            logger.error(f"Failed to fetch evidence data: {e}")
            return []

    def _fetch_evidence_data_sync(
        self, backend_url: str = "http://localhost:5000"
    ) -> List[Dict[str, Any]]:
        """Synchronous fallback for fetching evidence data"""
        try:
            import requests

            response = requests.get(f"{backend_url}/api/evidence")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("data", [])
                else:
                    logger.error(f"API error: {data.get('error')}")
                    return []
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch evidence data synchronously: {e}")
            return []

    async def create_evidence_via_api(
        self, evidence_data: Dict[str, Any], backend_url: str = "http://localhost:5000"
    ) -> Optional[str]:
        """Create evidence via backend API"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/api/evidence", json=evidence_data
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        if data.get("success"):
                            return data.get("evidence_id")
                        else:
                            logger.error(f"API error: {data.get('error')}")
                            return None
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return None
        except ImportError:
            logger.warning("aiohttp not available, using synchronous requests")
            return self._create_evidence_via_api_sync(evidence_data, backend_url)
        except Exception as e:
            logger.error(f"Failed to create evidence via API: {e}")
            return None

    def _create_evidence_via_api_sync(
        self, evidence_data: Dict[str, Any], backend_url: str = "http://localhost:5000"
    ) -> Optional[str]:
        """Synchronous fallback for creating evidence"""
        try:
            import requests

            response = requests.post(f"{backend_url}/api/evidence", json=evidence_data)
            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    return data.get("evidence_id")
                else:
                    logger.error(f"API error: {data.get('error')}")
                    return None
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Failed to create evidence via API synchronously: {e}")
            return None

    async def update_evidence_via_api(
        self, evidence_id: str, updates: Dict[str, Any], backend_url: str = "http://localhost:5000"
    ) -> bool:
        """Update evidence via backend API"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{backend_url}/api/evidence/{evidence_id}", json=updates
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("success", False)
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return False
        except ImportError:
            logger.warning("aiohttp not available, using synchronous requests")
            return self._update_evidence_via_api_sync(evidence_id, updates, backend_url)
        except Exception as e:
            logger.error(f"Failed to update evidence via API: {e}")
            return False

    def _update_evidence_via_api_sync(
        self, evidence_id: str, updates: Dict[str, Any], backend_url: str = "http://localhost:5000"
    ) -> bool:
        """Synchronous fallback for updating evidence"""
        try:
            import requests

            response = requests.put(f"{backend_url}/api/evidence/{evidence_id}", json=updates)
            if response.status_code == 200:
                data = response.json()
                return data.get("success", False)
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to update evidence via API synchronously: {e}")
            return False

    async def delete_evidence_via_api(
        self, evidence_id: str, backend_url: str = "http://localhost:5000"
    ) -> bool:
        """Delete evidence via backend API"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{backend_url}/api/evidence/{evidence_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("success", False)
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return False
        except ImportError:
            logger.warning("aiohttp not available, using synchronous requests")
            return self._delete_evidence_via_api_sync(evidence_id, backend_url)
        except Exception as e:
            logger.error(f"Failed to delete evidence via API: {e}")
            return False

    def _delete_evidence_via_api_sync(
        self, evidence_id: str, backend_url: str = "http://localhost:5000"
    ) -> bool:
        """Synchronous fallback for deleting evidence"""
        try:
            import requests

            response = requests.delete(f"{backend_url}/api/evidence/{evidence_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("success", False)
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete evidence via API synchronously: {e}")
            return False
