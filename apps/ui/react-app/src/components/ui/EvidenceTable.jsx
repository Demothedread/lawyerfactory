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
  IconButton,
  InputAdornment,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Menu,
  MenuItem,
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
  FilePresent,
  Assessment,
  Gavel,
  Refresh,
  Search,
  Visibility,
  Download,
  Delete,
  Close,
  MoreVert
} from '@mui/icons-material';

import { useCallback, useEffect, useState } from 'react';
import { useToast } from '../feedback/Toast';

const EvidenceTable = ({
  caseId,
  refreshTrigger = 0,
  onEvidenceSelect,
  onEvidenceUpdate,
  apiEndpoint = '/api/evidence',
  showActions = true,
  compact = false,
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

  // Filter evidence based on search
  const filteredEvidence = evidenceData.filter(evidence => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      evidence.filename?.toLowerCase().includes(term) ||
      evidence.description?.toLowerCase().includes(term) ||
      evidence.tags?.toLowerCase().includes(term) ||
      evidence.object_id?.toLowerCase().includes(term)
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
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
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
                    <TableCell colSpan={showActions ? 7 : 6} align="center">
                      <Typography color="text.secondary" sx={{ py: 4 }}>
                        {searchTerm ? 'No evidence matches your search' : 'No evidence uploaded yet'}
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
    </Box>
  );
};

export default EvidenceTable;