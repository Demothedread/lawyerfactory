// Evidence Table component with unified storage integration
// Evidence Table component with unified storage integration
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CardHeader,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    IconButton,
    InputAdornment,
    InputLabel,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
    Menu,
    MenuItem,
    Select,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TablePagination,
    TableRow,
    TableSortLabel,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';

import {
    Add,
    Assessment,
    Close,
    Delete,
    Download,
    Edit,
    FilePresent,
    Gavel,
    MoreVert,
    Refresh,
    Science,
    Search,
    Visibility
} from '@mui/icons-material';

import { useCallback, useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { useToast } from '../feedback/Toast';

const EvidenceTable = ({
  caseId,
  refreshTrigger = 0,
  onEvidenceSelect,
  onEvidenceUpdate,
  apiEndpoint = '/api/evidence',
  showActions = true,
  compact = false,
  phaseFilter = null,
  socketEndpoint = 'http://localhost:5000',
}) => {
  const [evidenceData, setEvidenceData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState('upload_date');
  const [order, setOrder] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [menuEvidence, setMenuEvidence] = useState(null);
  const [socket, setSocket] = useState(null);
  const [realTimeUpdates, setRealTimeUpdates] = useState(true);

  // NEW: Research dialog state
  const [showResearchDialog, setShowResearchDialog] = useState(false);
  const [researchKeywords, setResearchKeywords] = useState('');
  const [researchInProgress, setResearchInProgress] = useState(false);

  // NEW: Evidence source filter
  const [evidenceSourceFilter, setEvidenceSourceFilter] = useState('all'); // 'all', 'primary', 'secondary'

  // NEW: Create/Edit evidence dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingEvidence, setEditingEvidence] = useState(null);

  const { addToast } = useToast();

  // Load evidence data
  const loadEvidence = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (caseId) params.append('case_id', caseId);
      if (searchTerm) params.append('search', searchTerm);
      params.append('page', page);
      params.append('limit', rowsPerPage);
      params.append('sort', `${orderBy}:${order}`);

      const response = await fetch(`${apiEndpoint}?${params}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load evidence: ${response.statusText}`);
      }

      const data = await response.json();
      setEvidenceData(data.evidence || []);
      
    } catch (err) {
      console.error('Error loading evidence:', err);
      setError(err.message);
      addToast(`Failed to load evidence: ${err.message}`, {
        severity: 'error',
        title: 'Load Error',
      });
    } finally {
      setLoading(false);
    }
  }, [caseId, searchTerm, page, rowsPerPage, orderBy, order, apiEndpoint, addToast]);

  // Initialize Socket.IO connection for real-time updates
  useEffect(() => {
    if (realTimeUpdates && socketEndpoint) {
      const newSocket = io(socketEndpoint, {
        transports: ['websocket', 'polling'],
        timeout: 20000,
      });

      setSocket(newSocket);

      // Socket event listeners
      newSocket.on('connect', () => {
        console.log('🔌 EvidenceTable connected to Socket.IO');
      });

      newSocket.on('disconnect', () => {
        console.log('🔌 EvidenceTable disconnected from Socket.IO');
      });

      // Evidence processing events
      newSocket.on('evidence_processed', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('📄 Evidence processed:', data);
          addToast(`Evidence processed: ${data.filename}`, {
            severity: 'info',
            title: 'Evidence Update',
          });
          // Refresh evidence list
          loadEvidence();
        }
      });

      // Evidence upload events
      newSocket.on('evidence_uploaded', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('📄 Evidence uploaded:', data);
          addToast(`New evidence uploaded: ${data.filename}`, {
            severity: 'success',
            title: 'Evidence Added',
          });
          // Refresh evidence list
          loadEvidence();
        }
      });

      // Evidence status change events
      newSocket.on('evidence_status_changed', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('📄 Evidence status changed:', data);
          // Update specific evidence item in state
          setEvidenceData(prev => prev.map(evidence =>
            evidence.evidence_id === data.evidence_id
              ? { ...evidence, status: data.new_status }
              : evidence
          ));
          
          addToast(`Evidence status updated: ${data.filename} → ${data.new_status}`, {
            severity: 'info',
            title: 'Status Update',
          });
        }
      });

      // Phase progress events that might affect evidence
      newSocket.on('phase_completed', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('🎯 Phase completed, checking for evidence updates:', data);
          // Refresh evidence list as phase completion might update evidence status
          setTimeout(() => loadEvidence(), 1000); // Small delay to ensure backend processing is complete
        }
      });

      // NEW: Research events
      newSocket.on('research_started', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('🔬 Research started:', data);
          addToast(`Research started with ${data.keywords.length} keywords`, {
            severity: 'info',
            title: 'Research In Progress',
          });
        }
      });

      newSocket.on('research_completed', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('✅ Research completed:', data);
          addToast(`Research completed! Found ${data.total_sources} sources, created ${data.secondary_evidence_ids.length} SECONDARY evidence entries`, {
            severity: 'success',
            title: 'Research Complete',
          });
          // Refresh evidence list to show new SECONDARY evidence
          loadEvidence();
          setResearchInProgress(false);
        }
      });

      newSocket.on('research_failed', (data) => {
        if (!caseId || data.case_id === caseId) {
          console.log('❌ Research failed:', data);
          addToast(`Research failed: ${data.error}`, {
            severity: 'error',
            title: 'Research Error',
          });
          setResearchInProgress(false);
        }
      });

      return () => {
        newSocket.disconnect();
      };
    }
  }, [caseId, realTimeUpdates, socketEndpoint, loadEvidence, addToast]);

  // Load data on component mount and when dependencies change
  useEffect(() => {
    loadEvidence();
  }, [loadEvidence, refreshTrigger]);

  // Handle sorting
  const handleSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  // Handle search
  const handleSearch = (value) => {
    setSearchTerm(value);
    setPage(0); // Reset to first page
  };

  // Handle row menu
  const handleMenuOpen = (event, evidence) => {
    setAnchorEl(event.currentTarget);
    setMenuEvidence(evidence);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuEvidence(null);
  };

  // Handle evidence actions
  const handleView = (evidence) => {
    setSelectedEvidence(evidence);
    setShowDetails(true);
    handleMenuClose();
    
    if (onEvidenceSelect) {
      onEvidenceSelect(evidence);
    }
  };

  const handleDownload = async (evidence) => {
    try {
      const response = await fetch(`${apiEndpoint}/${evidence.evidence_id}/download`);
      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = evidence.filename || `evidence_${evidence.evidence_id}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      addToast(`Downloaded ${evidence.filename}`, {
        severity: 'success',
        title: 'Download Complete',
      });
    } catch (err) {
      addToast(`Download failed: ${err.message}`, {
        severity: 'error',
        title: 'Download Error',
      });
    }
    handleMenuClose();
  };

  const handleDelete = async (evidence) => {
    if (!window.confirm(`Are you sure you want to delete "${evidence.filename}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${apiEndpoint}/${evidence.evidence_id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Delete failed');
      }

      addToast(`Deleted ${evidence.filename}`, {
        severity: 'success',
        title: 'Evidence Deleted',
      });

      // Refresh data
      loadEvidence();
      
      if (onEvidenceUpdate) {
        onEvidenceUpdate('deleted', evidence);
      }
    } catch (err) {
      addToast(`Delete failed: ${err.message}`, {
        severity: 'error',
        title: 'Delete Error',
      });
    }
    handleMenuClose();
  };

  // NEW: Request research from PRIMARY evidence
  const handleRequestResearch = (evidence) => {
    if (evidence.evidence_source === 'secondary') {
      addToast('Can only research from PRIMARY evidence', {
        severity: 'warning',
        title: 'Invalid Operation',
      });
      return;
    }

    setSelectedEvidence(evidence);
    setShowResearchDialog(true);
    handleMenuClose();
  };

  // NEW: Execute research
  const handleExecuteResearch = async () => {
    if (!selectedEvidence) return;

    setResearchInProgress(true);
    
    try {
      const response = await fetch('/api/research/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          case_id: caseId || 'default_case',
          evidence_id: selectedEvidence.evidence_id,
          keywords: researchKeywords ? researchKeywords.split(',').map(k => k.trim()) : null,
          max_results: 5,
        }),
      });

      if (!response.ok) {
        throw new Error('Research request failed');
      }

      const result = await response.json();
      
      addToast(`Research started! ${result.message}`, {
        severity: 'success',
        title: 'Research Initiated',
      });

      setShowResearchDialog(false);
      setResearchKeywords('');
    } catch (err) {
      addToast(`Research failed: ${err.message}`, {
        severity: 'error',
        title: 'Research Error',
      });
      setResearchInProgress(false);
    }
  };

  // NEW: Create new evidence
  const handleCreateEvidence = () => {
    setEditingEvidence(null);
    setShowCreateDialog(true);
  };

  // NEW: Edit evidence
  const handleEdit = (evidence) => {
    setEditingEvidence(evidence);
    setShowCreateDialog(true);
    handleMenuClose();
  };

  // NEW: Save evidence (create or update)

  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get status chip
  const getStatusChip = (status) => {
    const statusConfig = {
      'stored': { color: 'success', icon: <FilePresent /> },
      'processing': { color: 'warning', icon: <Assessment /> },
      'analyzed': { color: 'primary', icon: <Gavel /> },
      'error': { color: 'error', icon: null },
    };

    const config = statusConfig[status] || { color: 'default', icon: null };
    
    return (
      <Chip
        label={status?.toUpperCase() || 'UNKNOWN'}
        color={config.color}
        size="small"
        icon={config.icon}
      />
    );
  };

  // Filter evidence based on search, phase, and evidence source
  const filteredEvidence = evidenceData.filter(evidence => {
    // Phase filter
    if (phaseFilter && evidence.phase !== phaseFilter) {
      return false;
    }

    // NEW: Evidence source filter
    if (evidenceSourceFilter !== 'all') {
      if (evidenceSourceFilter === 'primary' && evidence.evidence_source !== 'primary') {
        return false;
      }
      if (evidenceSourceFilter === 'secondary' && evidence.evidence_source !== 'secondary') {
        return false;
      }
    }

    // Search filter
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      evidence.filename?.toLowerCase().includes(term) ||
      evidence.description?.toLowerCase().includes(term) ||
      evidence.tags?.toLowerCase().includes(term) ||
      evidence.object_id?.toLowerCase().includes(term) ||
      evidence.research_query?.toLowerCase().includes(term)
    );
  });

  return (
    <Box>
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant={compact ? 'h6' : 'h5'}>
                Evidence Table
              </Typography>
              {caseId && (
                <Chip label={`Case: ${caseId}`} size="small" variant="outlined" />
              )}
              {loading && <LinearProgress sx={{ width: 100 }} />}
            </Box>
          }
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Create Evidence">
                <IconButton onClick={handleCreateEvidence} color="primary">
                  <Add />
                </IconButton>
              </Tooltip>
              <Tooltip title="Refresh">
                <IconButton onClick={loadEvidence} disabled={loading}>
                  <Refresh />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        
        <CardContent>
          {/* Search and Filter */}
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="Search evidence..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 200 }}
            />
            
            {/* NEW: Evidence Source Filter */}
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Evidence Source</InputLabel>
              <Select
                value={evidenceSourceFilter}
                onChange={(e) => setEvidenceSourceFilter(e.target.value)}
                label="Evidence Source"
              >
                <MenuItem value="all">All Evidence</MenuItem>
                <MenuItem value="primary">PRIMARY Only</MenuItem>
                <MenuItem value="secondary">SECONDARY Only</MenuItem>
              </Select>
            </FormControl>
            
            <Typography variant="body2" color="text.secondary">
              {filteredEvidence.length} of {evidenceData.length} items
            </Typography>
          </Box>

          {/* Error State */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Evidence Table */}
          <TableContainer>
            <Table size={compact ? 'small' : 'medium'}>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'filename'}
                      direction={orderBy === 'filename' ? order : 'asc'}
                      onClick={() => handleSort('filename')}
                    >
                      File Name
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'upload_date'}
                      direction={orderBy === 'upload_date' ? order : 'asc'}
                      onClick={() => handleSort('upload_date')}
                    >
                      Upload Date
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Phase</TableCell>
                  <TableCell>ObjectID</TableCell>
                  {showActions && <TableCell>Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredEvidence
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((evidence) => (
                    <TableRow key={evidence.evidence_id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {evidence.filename}
                          </Typography>
                          {evidence.description && (
                            <Typography variant="caption" color="text.secondary">
                              {evidence.description.substring(0, 50)}
                              {evidence.description.length > 50 ? '...' : ''}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {getStatusChip(evidence.status)}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={evidence.evidence_source === 'primary' ? 'PRIMARY' : 'SECONDARY'}
                          color={evidence.evidence_source === 'primary' ? 'primary' : 'secondary'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {formatFileSize(evidence.file_size)}
                      </TableCell>
                      <TableCell>
                        {formatDate(evidence.upload_date)}
                      </TableCell>
                      <TableCell>
                        <Chip label={evidence.phase || 'Unknown'} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" fontFamily="monospace">
                          {evidence.object_id?.substring(0, 8)}...
                        </Typography>
                      </TableCell>
                      {showActions && (
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, evidence)}
                          >
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                
                {filteredEvidence.length === 0 && !loading && (
                  <TableRow>
                    <TableCell colSpan={showActions ? 8 : 7} align="center">
                      <Typography color="text.secondary" sx={{ py: 4 }}>
                        {searchTerm || evidenceSourceFilter !== 'all' 
                          ? 'No evidence matches your filters' 
                          : 'No evidence uploaded yet'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {filteredEvidence.length > 0 && (
            <TablePagination
              component="div"
              count={filteredEvidence.length}
              page={page}
              onPageChange={(e, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              rowsPerPageOptions={[5, 10, 25, 50]}
            />
          )}
        </CardContent>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleView(menuEvidence)}>
          <Visibility sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={() => handleEdit(menuEvidence)}>
          <Edit sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        {menuEvidence?.evidence_source === 'primary' && (
          <MenuItem onClick={() => handleRequestResearch(menuEvidence)}>
            <Science sx={{ mr: 1 }} />
            Request Research
          </MenuItem>
        )}
        <MenuItem onClick={() => handleDownload(menuEvidence)}>
          <Download sx={{ mr: 1 }} />
          Download
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => handleDelete(menuEvidence)} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Evidence Details Dialog */}
      <Dialog open={showDetails} onClose={() => setShowDetails(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Evidence Details
          <IconButton
            onClick={() => setShowDetails(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedEvidence && (
            <Box>
              <List>
                <ListItem>
                  <ListItemText
                    primary="File Name"
                    secondary={selectedEvidence.filename}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={getStatusChip(selectedEvidence.status)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="File Size"
                    secondary={formatFileSize(selectedEvidence.file_size)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Upload Date"
                    secondary={formatDate(selectedEvidence.upload_date)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Phase"
                    secondary={selectedEvidence.phase}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Object ID"
                    secondary={selectedEvidence.object_id}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Evidence ID"
                    secondary={selectedEvidence.evidence_id}
                  />
                </ListItem>
                {selectedEvidence.description && (
                  <ListItem>
                    <ListItemText
                      primary="Description"
                      secondary={selectedEvidence.description}
                    />
                  </ListItem>
                )}
                {selectedEvidence.tags && (
                  <ListItem>
                    <ListItemText
                      primary="Tags"
                      secondary={selectedEvidence.tags}
                    />
                  </ListItem>
                )}
                {selectedEvidence.facts && selectedEvidence.facts.length > 0 && (
                  <ListItem>
                    <ListItemText
                      primary="Extracted Facts"
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {selectedEvidence.facts.map((fact, index) => (
                            <Chip
                              key={index}
                              label={fact}
                              size="small"
                              sx={{ mr: 0.5, mb: 0.5 }}
                            />
                          ))}
                        </Box>
                      }
                    />
                  </ListItem>
                )}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetails(false)}>Close</Button>
          {selectedEvidence && (
            <Button
              variant="contained"
              onClick={() => handleDownload(selectedEvidence)}
              startIcon={<Download />}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Research Dialog */}
      <Dialog open={showResearchDialog} onClose={() => setShowResearchDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Request Research
          <IconButton
            onClick={() => setShowResearchDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedEvidence && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Research will be executed from PRIMARY evidence: <strong>{selectedEvidence.filename}</strong>
              </Typography>
              <TextField
                fullWidth
                label="Custom Keywords (Optional)"
                placeholder="Enter comma-separated keywords..."
                value={researchKeywords}
                onChange={(e) => setResearchKeywords(e.target.value)}
                helperText="Leave empty to automatically extract keywords from evidence content"
                multiline
                rows={3}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResearchDialog(false)} disabled={researchInProgress}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleExecuteResearch}
            disabled={researchInProgress}
            startIcon={researchInProgress ? <LinearProgress /> : <Science />}
          >
            {researchInProgress ? 'Researching...' : 'Execute Research'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EvidenceTable;