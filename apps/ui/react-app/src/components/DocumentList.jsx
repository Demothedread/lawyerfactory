import {
    Delete as DeleteIcon,
    Download as DownloadIcon,
    Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useState } from 'react';

/**
 * DocumentList - Display organized evidence documents
 * 
 * Shows uploaded documents with metadata, categorization, and actions
 * Supports multiple view modes (grid/table) with filtering
 */
const DocumentList = ({ documents = [], onDelete, onPreview, viewMode = 'table' }) => {
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!documents || documents.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: '#f5f5f5' }}>
        <Typography color="textSecondary">
          📁 No documents uploaded yet. Start by uploading evidence files.
        </Typography>
      </Paper>
    );
  }

  // Helper to format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  // Helper to get document icon/category
  const getDocumentIcon = (filename = '') => {
    const ext = filename.toLowerCase().split('.').pop();
    const icons = {
      pdf: '📄',
      doc: '📘',
      docx: '📘',
      txt: '📋',
      png: '🖼️',
      jpg: '🖼️',
      jpeg: '🖼️',
      xlsx: '📊',
      csv: '📊',
    };
    return icons[ext] || '📎';
  };

  // Helper to determine document category
  const getCategory = (doc) => {
    if (doc.category) return doc.category;
    if (doc.document_type) return doc.document_type;
    return 'Evidence';
  };

  // Helper to get category color
  const getCategoryColor = (category) => {
    const colors = {
      'Deposition': 'primary',
      'Affidavit': 'info',
      'Contract': 'success',
      'Email': 'warning',
      'Report': 'default',
      'Photo': 'secondary',
      'Video': 'secondary',
      'Evidence': 'default',
    };
    return colors[category] || 'default';
  };

  const handleDownload = async (doc) => {
    try {
      setLoading(true);
      // In a real implementation, this would download from the backend
      if (doc.url) {
        window.open(doc.url, '_blank');
      } else {
        console.log('Download started for:', doc.filename);
      }
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = (doc) => {
    setSelectedDoc(doc);
    if (onPreview) {
      onPreview(doc);
    }
  };

  const handleRemove = async (doc) => {
    if (onDelete && window.confirm(`Remove "${doc.filename}"?`)) {
      try {
        setLoading(true);
        await onDelete(doc.id || doc.object_id);
      } catch (error) {
        console.error('Delete failed:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  // Table View (Default)
  if (viewMode === 'table') {
    return (
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', width: '5%' }}>Type</TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: '30%' }}>Filename</TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: '15%' }}>Category</TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: '10%' }}>Size</TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: '15%' }}>Uploaded</TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: '15%', textAlign: 'center' }}>Actions</TableCell>
              <TableCell sx={{ fontWeight: 'bold', width: '10%' }} />
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.map((doc, index) => (
              <TableRow
                key={doc.id || doc.object_id || index}
                hover
                selected={selectedDoc?.id === doc.id}
                onClick={() => setSelectedDoc(doc)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell sx={{ fontSize: '1.2em' }}>
                  {getDocumentIcon(doc.filename)}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {doc.filename || 'Unnamed'}
                  </Typography>
                  {doc.description && (
                    <Typography variant="caption" color="textSecondary">
                      {doc.description}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Chip
                    label={getCategory(doc)}
                    color={getCategoryColor(getCategory(doc))}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatFileSize(doc.file_size || doc.size)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="caption">
                    {doc.uploaded_at
                      ? new Date(doc.uploaded_at).toLocaleDateString()
                      : 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  <Tooltip title="Preview">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePreview(doc);
                      }}
                    >
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Download">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(doc);
                      }}
                      disabled={loading}
                    >
                      <DownloadIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemove(doc);
                      }}
                      disabled={loading}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
                <TableCell />
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  // Grid View
  return (
    <Grid container spacing={2}>
      {documents.map((doc, index) => (
        <Grid item xs={12} sm={6} md={4} key={doc.id || doc.object_id || index}>
          <Card
            sx={{
              cursor: 'pointer',
              border: selectedDoc?.id === doc.id ? '2px solid primary.main' : 'none',
              transition: 'all 0.2s',
              '&:hover': {
                boxShadow: 3,
                transform: 'translateY(-2px)',
              },
            }}
            onClick={() => setSelectedDoc(doc)}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography sx={{ fontSize: '2em' }}>
                  {getDocumentIcon(doc.filename)}
                </Typography>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', noWrap }}>
                    {doc.filename || 'Unnamed'}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {formatFileSize(doc.file_size || doc.size)}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mb: 1 }}>
                <Chip
                  label={getCategory(doc)}
                  color={getCategoryColor(getCategory(doc))}
                  size="small"
                  variant="outlined"
                  sx={{ mr: 0.5, mb: 0.5 }}
                />
              </Box>

              {doc.description && (
                <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                  {doc.description}
                </Typography>
              )}

              <Typography variant="caption" color="textSecondary">
                {doc.uploaded_at
                  ? `Uploaded: ${new Date(doc.uploaded_at).toLocaleDateString()}`
                  : 'Upload date unknown'}
              </Typography>

              <Box sx={{ display: 'flex', gap: 0.5, mt: 1.5 }}>
                <Tooltip title="Preview">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePreview(doc);
                    }}
                    sx={{ flex: 1 }}
                  >
                    <VisibilityIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(doc);
                    }}
                    disabled={loading}
                    sx={{ flex: 1 }}
                  >
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemove(doc);
                    }}
                    disabled={loading}
                    sx={{ flex: 1 }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default DocumentList;
