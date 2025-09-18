import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { AgGridReact } from "ag-grid-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Sparklines, SparklinesLine, SparklinesSpots } from "react-sparklines";
import io from "socket.io-client";

const EvidenceDataGrid = ({
  evidenceData,
  onEvidenceUpdate,
  onEvidenceDelete,
  readOnly = false,
  enableSparklines = true,
  backendUrl = "http://localhost:5000",
}) => {
  const [gridApi, setGridApi] = useState(null);
  const [columnApi, setColumnApi] = useState(null);
  const [socket, setSocket] = useState(null);
  const [filterText, setFilterText] = useState("");
  const [selectedRows, setSelectedRows] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize socket connection for real-time updates
  useEffect(() => {
    const newSocket = io(backendUrl);
    setSocket(newSocket);

    // Join evidence collaboration room
    newSocket.emit("join_evidence_room", { room: "evidence_main" });

    // Listen for real-time updates
    newSocket.on("evidence_created", (data) => {
      if (gridApi) {
        const newRow = data.evidence;
        gridApi.applyTransaction({ add: [newRow] });
      }
    });

    newSocket.on("evidence_updated", (data) => {
      if (gridApi) {
        const updatedRow = data.evidence;
        gridApi.applyTransaction({ update: [updatedRow] });
      }
    });

    newSocket.on("evidence_deleted", (data) => {
      if (gridApi) {
        gridApi.applyTransaction({
          remove: [{ evidence_id: data.evidence_id }],
        });
      }
    });

    newSocket.on("evidence_grid_synced", (data) => {
      if (gridApi) {
        gridApi.setRowData(data.data);
      }
    });

    newSocket.on("evidence_filter_updated", (data) => {
      // Handle collaborative filtering
      console.log("Collaborative filter applied:", data.filters);
    });

    return () => {
      newSocket.emit("leave_evidence_room", { room: "evidence_main" });
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
          setError(result.error || "Failed to load evidence data");
        }
      } catch (err) {
        setError("Network error while loading evidence data");
        console.error("Error loading evidence data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (gridApi) {
      loadData();
    }
  }, [gridApi, backendUrl]);

  // Custom cell renderers
  const RelevanceScoreRenderer = (props) => {
    const score = props.value || 0;
    const color = score > 0.8 ? "#10b981" : score > 0.6 ? "#f59e0b" : "#ef4444";

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

  const EvidenceTypeRenderer = (props) => {
    const typeColors = {
      documentary: "#3b82f6",
      testimonial: "#8b5cf6",
      expert: "#f59e0b",
      physical: "#10b981",
      digital: "#ef4444",
      photographic: "#06b6d4",
    };

    return (
      <span
        className="px-2 py-1 rounded-full text-xs font-medium text-white"
        style={{ backgroundColor: typeColors[props.value] || "#6b7280" }}>
        {props.value}
      </span>
    );
  };

  const ActionsRenderer = (props) => {
    if (readOnly) return null;

    const handleEdit = async () => {
      // Open edit modal or inline editing
      if (onEvidenceUpdate) {
        onEvidenceUpdate(props.data);
      }
    };

    const handleDelete = async () => {
      if (window.confirm("Are you sure you want to delete this evidence?")) {
        try {
          const response = await fetch(
            `${backendUrl}/api/evidence/${props.data.evidence_id}`,
            {
              method: "DELETE",
            }
          );
          const result = await response.json();
          if (result.success) {
            if (onEvidenceDelete) {
              onEvidenceDelete(props.data.evidence_id);
            }
          } else {
            alert("Failed to delete evidence: " + result.error);
          }
        } catch (err) {
          alert("Network error while deleting evidence");
          console.error("Error deleting evidence:", err);
        }
      }
    };

    return (
      <div className="flex space-x-1">
        <button
          onClick={handleEdit}
          className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600">
          Edit
        </button>
        <button
          onClick={handleDelete}
          className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">
          Delete
        </button>
      </div>
    );
  };

  // Column definitions
  const columnDefs = useMemo(
    () => [
      {
        field: "evidence_id",
        headerName: "ID",
        width: 120,
        pinned: "left",
        cellRenderer: (props) => (
          <span className="font-mono text-xs">
            {props.value?.substring(0, 8)}...
          </span>
        ),
      },
      {
        field: "source_document",
        headerName: "Source",
        width: 150,
        filter: "agTextColumnFilter",
      },
      {
        field: "page_section",
        headerName: "Section",
        width: 100,
      },
      {
        field: "content",
        headerName: "Content",
        width: 300,
        cellRenderer: (props) => (
          <div className="truncate" title={props.value}>
            {props.value?.substring(0, 100)}...
          </div>
        ),
      },
      {
        field: "evidence_type",
        headerName: "Type",
        width: 120,
        cellRenderer: "evidenceTypeRenderer",
        filter: "agSetColumnFilter",
        filterParams: {
          values: [
            "documentary",
            "testimonial",
            "expert",
            "physical",
            "digital",
            "photographic",
          ],
        },
      },
      {
        field: "relevance_score",
        headerName: "Relevance",
        width: 140,
        cellRenderer: "relevanceScoreRenderer",
        sortable: true,
        filter: "agNumberColumnFilter",
      },
      {
        field: "relevance_level",
        headerName: "Level",
        width: 100,
        cellRenderer: (props) => {
          const colors = {
            critical: "#ef4444",
            high: "#f59e0b",
            medium: "#3b82f6",
            low: "#6b7280",
            unknown: "#9ca3af",
          };
          return (
            <span
              className="px-2 py-1 rounded text-xs font-medium text-white"
              style={{ backgroundColor: colors[props.value] || "#6b7280" }}>
              {props.value}
            </span>
          );
        },
        filter: "agSetColumnFilter",
        filterParams: {
          values: ["critical", "high", "medium", "low", "unknown"],
        },
      },
      {
        field: "bluebook_citation",
        headerName: "Citation",
        width: 200,
        cellRenderer: (props) => (
          <span className="font-mono text-xs">{props.value || "N/A"}</span>
        ),
      },
      {
        field: "privilege_marker",
        headerName: "Privilege",
        width: 120,
        cellRenderer: (props) => {
          const colors = {
            none: "#10b981",
            attorney_client: "#ef4444",
            work_product: "#f59e0b",
            confidential: "#8b5cf6",
            redacted: "#6b7280",
          };
          return (
            <span
              className="px-2 py-1 rounded text-xs font-medium text-white"
              style={{ backgroundColor: colors[props.value] || "#6b7280" }}>
              {props.value}
            </span>
          );
        },
        filter: "agSetColumnFilter",
        filterParams: {
          values: [
            "none",
            "attorney_client",
            "work_product",
            "confidential",
            "redacted",
          ],
        },
      },
      {
        field: "key_terms",
        headerName: "Key Terms",
        width: 150,
        cellRenderer: (props) => (
          <div className="flex flex-wrap gap-1">
            {props.value?.slice(0, 3).map((term, idx) => (
              <span
                key={idx}
                className="px-1 py-0.5 bg-gray-200 text-gray-800 rounded text-xs">
                {term}
              </span>
            ))}
            {props.value?.length > 3 && (
              <span className="text-xs text-gray-500">
                +{props.value.length - 3} more
              </span>
            )}
          </div>
        ),
      },
      {
        field: "last_modified",
        headerName: "Modified",
        width: 150,
        sortable: true,
        valueFormatter: (params) => {
          return new Date(params.value).toLocaleString();
        },
      },
      {
        field: "actions",
        headerName: "Actions",
        width: 120,
        cellRenderer: "actionsRenderer",
        pinned: "right",
      },
    ],
    [readOnly, enableSparklines]
  );

  // Grid options
  const defaultColDef = useMemo(
    () => ({
      resizable: true,
      sortable: true,
      filter: true,
      floatingFilter: true,
    }),
    []
  );

  const gridOptions = useMemo(
    () => ({
      enableRangeSelection: true,
      enableCharts: true,
      enableAdvancedFilter: true,
      rowSelection: "multiple",
      suppressRowClickSelection: true,
      animateRows: true,
      pagination: true,
      paginationPageSize: 50,
      sideBar: {
        toolPanels: [
          {
            id: "columns",
            labelDefault: "Columns",
            labelKey: "columns",
            iconKey: "columns",
            toolPanel: "agColumnsToolPanel",
          },
          {
            id: "filters",
            labelDefault: "Filters",
            labelKey: "filters",
            iconKey: "filter",
            toolPanel: "agFiltersToolPanel",
          },
        ],
      },
    }),
    []
  );

  // Event handlers
  const onGridReady = useCallback((params) => {
    setGridApi(params.api);
    setColumnApi(params.columnApi);
  }, []);

  const onSelectionChanged = useCallback(() => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes();
      const selectedData = selectedNodes.map((node) => node.data);
      setSelectedRows(selectedData);
    }
  }, [gridApi]);

  const onFilterChanged = useCallback((event) => {
    setFilterText(event.api.getFilterModel());
  }, []);

  const exportToCsv = useCallback(() => {
    if (gridApi) {
      gridApi.exportDataAsCsv({
        fileName: `evidence_export_${
          new Date().toISOString().split("T")[0]
        }.csv`,
      });
    }
  }, [gridApi]);

  const exportToExcel = useCallback(() => {
    if (gridApi) {
      // Note: Requires ag-grid-enterprise for Excel export
      gridApi.exportDataAsExcel({
        fileName: `evidence_export_${
          new Date().toISOString().split("T")[0]
        }.xlsx`,
      });
    }
  }, [gridApi]);

  // API Integration Functions
  const createEvidence = useCallback(
    async (evidenceData) => {
      try {
        const response = await fetch(`${backendUrl}/api/evidence`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(evidenceData),
        });
        const result = await response.json();
        if (result.success) {
          // Data will be updated via Socket.IO
          return result.evidence_id;
        } else {
          throw new Error(result.error || "Failed to create evidence");
        }
      } catch (err) {
        console.error("Error creating evidence:", err);
        throw err;
      }
    },
    [backendUrl]
  );

  const refreshData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${backendUrl}/api/evidence`);
      const result = await response.json();
      if (result.success && gridApi) {
        gridApi.setRowData(result.data);
      } else {
        setError(result.error || "Failed to refresh evidence data");
      }
    } catch (err) {
      setError("Network error while refreshing evidence data");
      console.error("Error refreshing evidence data:", err);
    } finally {
      setIsLoading(false);
    }
  }, [gridApi, backendUrl]);

  return (
    <div className="evidence-data-grid w-full h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-800">
            Evidence Management
          </h3>
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
            title="Refresh data from server">
            🔄 Refresh
          </button>

          {!readOnly && (
            <button
              onClick={() => {
                const newEvidence = {
                  source_document: "new_document.pdf",
                  content: "New evidence content...",
                  evidence_type: "documentary",
                  relevance_score: 0.5,
                  relevance_level: "medium",
                  key_terms: [],
                  notes: "New evidence entry",
                };
                createEvidence(newEvidence).catch((err) => {
                  alert("Failed to create evidence: " + err.message);
                });
              }}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm">
              ➕ Add Evidence
            </button>
          )}

          <button
            onClick={exportToCsv}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
            📊 Export CSV
          </button>

          <button
            onClick={exportToExcel}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 text-sm">
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
          <span>Real-time: {socket ? "🟢 Connected" : "🔴 Disconnected"}</span>
        </div>
      </div>

      {/* Loading Spinner */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
          <svg
            className="animate-spin h-5 w-5 text-gray-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4zm16 0a8 8 0 01-8 8v-4a4 4 0 004-4h4z"></path>
          </svg>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-100 text-red-800 rounded-md text-sm mt-4">
          {error}
        </div>
      )}
    </div>
  );
};

export default EvidenceDataGrid;
