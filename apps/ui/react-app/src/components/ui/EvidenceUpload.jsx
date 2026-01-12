// Enhanced Evidence Upload component with unified storage 
//
// Enhanced Evidence Upload component with unified storage 
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    IconButton,
    InputLabel,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemSecondaryAction,
    ListItemText,
    MenuItem,
    Select,
    TextField,
    Typography
} from '@mui/material';

import {
    CheckCircle,
    Close,
    CloudUpload,
    Delete,
    Description,
    Error,
    InsertDriveFile,
    PictureAsPdf,
    Visibility
} from '@mui/icons-material';

import { useCallback, useRef, useState } from 'react';
import { useToast } from '../feedback/Toast';

const EvidenceUpload = ({
  onUploadComplete,
  currentCaseId,
  sourcePhase = "phaseA01_intake",
  maxFileSize = 10 * 1024 * 1024, // 10MB default
  acceptedTypes = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.jpg', '.png'],
  apiEndpoint = '/api/storage/documents'
}) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});
  const [showMetadataDialog, setShowMetadataDialog] = useState(false);
  const [fileMetadata, setFileMetadata] = useState({});

  const fileInputRef = useRef(null);
  const { addToast } = useToast();

  const getFileIcon = (fileName) => {
    const ext = fileName.toLowerCase().split('.').pop();
    switch (ext) {
      case 'pdf':
        return <PictureAsPdf color="error" />;
      case 'doc':
      case 'docx':
        return <Description color="primary" />;
      case 'txt':
      case 'rtf':
        return <InsertDriveFile color="action" />;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return <Visibility color="info" />;
      default:
        return <InsertDriveFile color="action" />;
    }
  };

  const getFileStatus = (file) => {
    const progress = uploadProgress[file.id] || 0;
    
    if (file.status === 'uploading') {
      return (
        <Box sx={{ width: '100%', mt: 0.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              ⟳ Uploading...
            </Typography>
            <Typography variant="caption" color="primary">
              {progress}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress}
            sx={{
              height: 6,
              borderRadius: 1,
              backgroundColor: 'rgba(184, 115, 51, 0.2)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: '#b87333',
              }
            }}
          />
        </Box>
      );
    } else if (file.status === 'processing') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip 
            label="Processing" 
            color="info" 
            size="small" 
            icon={<span>⚙</span>}
            sx={{ animation: 'pulse 2s ease-in-out infinite' }}
          />
          <Typography variant="caption" color="text.secondary">
            Extracting content...
          </Typography>
        </Box>
      );
    } else if (file.status === 'vectorizing') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip 
            label="Vectorizing" 
            color="secondary" 
            size="small" 
            icon={<span>◈</span>}
          />
          <Typography variant="caption" color="text.secondary">
            Creating embeddings...
          </Typography>
        </Box>
      );
    } else if (file.status === 'completed') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip 
            label="✓ Uploaded" 
            color="success" 
            size="small" 
            icon={<CheckCircle />} 
          />
          {file.needsOCR && (
            <Chip 
              label="OCR Applied" 
              size="small" 
              variant="outlined"
              color="info"
            />
          )}
        </Box>
      );
    } else if (file.status === 'error') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip 
            label="✕ Error" 
            color="error" 
            size="small" 
            icon={<Error />} 
          />
          <Typography variant="caption" color="error">
            {file.errorMessage || 'Upload failed'}
          </Typography>
        </Box>
      );
    } else if (file.status === 'validating') {
      return (
        <Chip 
          label="Validating..." 
          color="default" 
          size="small" 
          icon={<span>⊙</span>}
        />
      );
    }
    return (
      <Chip 
        label="Ready" 
        color="default" 
        size="small" 
        variant="outlined"
      />
    );
  };

  const validateFile = (file) => {
    // Check file size
    if (file.size > maxFileSize) {
      return `File size exceeds ${Math.round(maxFileSize / 1024 / 1024)}MB limit`;
    }

    // Check file type
    const ext = '.' + file.name.toLowerCase().split('.').pop();
    if (!acceptedTypes.includes(ext)) {
      return `File type ${ext} not supported. Accepted types: ${acceptedTypes.join(', ')}`;
    }

    return null;
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFiles = (newFiles) => {
    const validFiles = [];
    const errors = [];

    newFiles.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        errors.push(`${file.name}: ${error}`);
      } else {
        const fileObj = {
          id: Date.now() + Math.random(),
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'ready',
          objectId: null,
          evidenceId: null,
        };
        validFiles.push(fileObj);
      }
    });

    if (errors.length > 0) {
      addToast(`File validation errors: ${errors.join(', ')}`, {
        severity: 'error',
        title: 'Upload Error',
      });
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
      addToast(`${validFiles.length} files added for upload`, {
        severity: 'success',
        title: 'Files Added',
      });
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      addToast('No files to upload', { severity: 'warning' });
      return;
    }

    setUploading(true);
    const successfulUploads = [];
    const failedUploads = [];

    for (const fileObj of files) {
      if (fileObj.status === 'completed') continue;

      try {
        // Update file status
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { ...f, status: 'uploading' } : f
        ));

        // Create form data
        const formData = new FormData();
        formData.append('files', fileObj.file);
        formData.append('case_id', currentCaseId || 'default');
        formData.append('phase', sourcePhase);
        
        // Add metadata if available
        const metadata = fileMetadata[fileObj.id] || {};
        if (Object.keys(metadata).length > 0) {
          formData.append('metadata', JSON.stringify(metadata));
        }

        // Upload with progress tracking
        const response = await fetch(apiEndpoint, {
          method: 'POST',
          body: formData,
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => ({ ...prev, [fileObj.id]: progress }));
          },
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();

        // Update file with success data
        const updatedFile = {
          ...fileObj,
          status: 'completed',
          objectId: result.object_id,
          evidenceId: result.evidence_id,
          s3Url: result.s3_url,
        };

        setFiles(prev => prev.map(f => 
          f.id === fileObj.id ? updatedFile : f
        ));

        successfulUploads.push(updatedFile);

      } catch (error) {
        console.error(`Failed to upload ${fileObj.name}:`, error);
        
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { ...f, status: 'error', error: error.message } : f
        ));

        failedUploads.push({ ...fileObj, error: error.message });
      }
    }

    setUploading(false);

    // Show results
    if (successfulUploads.length > 0) {
      addToast(`✅ Successfully uploaded ${successfulUploads.length} files`, {
        severity: 'success',
        title: 'Upload Complete',
        details: `ObjectIDs: ${successfulUploads.map(f => f.objectId?.substring(0, 8)).join(', ')}...`,
      });

      // Trigger callback
      if (onUploadComplete) {
        onUploadComplete(successfulUploads);
      }
    }

    if (failedUploads.length > 0) {
      addToast(`❌ Failed to upload ${failedUploads.length} files`, {
        severity: 'error',
        title: 'Upload Failed',
        details: failedUploads.map(f => f.name).join(', '),
      });
    }
  };

  const openMetadataDialog = (file) => {
    setSelectedFile(file);
    setFileMetadata(prev => ({
      ...prev,
      [file.id]: prev[file.id] || {
        description: '',
        tags: '',
        relevance: 'medium',
        confidential: false,
      }
    }));
    setShowMetadataDialog(true);
  };

  const saveMetadata = () => {
    setShowMetadataDialog(false);
    addToast(`Metadata saved for ${selectedFile.name}`, {
      severity: 'success',
      title: 'Metadata Updated',
    });
  };

  return (
    <Box>
      {/* Upload Zone with Soviet Industrial Styling */}
      <Card 
        sx={{ 
          mb: 2,
          border: dragActive ? '3px solid #b87333' : '2px dashed rgba(184, 115, 51, 0.5)',
          backgroundColor: dragActive ? 'rgba(184, 115, 51, 0.15)' : 'rgba(42, 42, 42, 0.6)',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          boxShadow: dragActive ? '0 0 20px rgba(184, 115, 51, 0.4)' : 'none',
          '&:hover': {
            border: '2px solid rgba(184, 115, 51, 0.7)',
            backgroundColor: 'rgba(184, 115, 51, 0.08)',
          }
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <CloudUpload 
            sx={{ 
              fontSize: 48, 
              color: dragActive ? '#b87333' : 'text.secondary', 
              mb: 2,
              transition: 'color 0.3s ease'
            }} 
          />
          <Typography variant="h6" gutterBottom sx={{ fontFamily: '"Courier New", monospace', letterSpacing: '0.5px' }}>
            {dragActive ? '▬ DROP FILES HERE ▬' : '⤴ UPLOAD EVIDENCE DOCUMENTS'}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom sx={{ fontFamily: '"Courier New", monospace' }}>
            {dragActive ? 'Release to upload' : 'Drag and drop files here, or click to select files'}
          </Typography>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Chip 
              label={`Formats: ${acceptedTypes.slice(0, 3).join(', ')}${acceptedTypes.length > 3 ? '...' : ''}`}
              size="small"
              variant="outlined"
              sx={{ fontFamily: '"Courier New", monospace', fontSize: '0.75rem' }}
            />
            <Chip 
              label={`Max: ${Math.round(maxFileSize / 1024 / 1024)}MB`}
              size="small"
              variant="outlined"
              sx={{ fontFamily: '"Courier New", monospace', fontSize: '0.75rem' }}
            />
          </Box>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            accept={acceptedTypes.join(',')}
            style={{ display: 'none' }}
          />
        </CardContent>
      </Card>

      {/* Files List */}
      {files.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Files to Upload ({files.length})
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setFiles([])}
                  disabled={uploading}
                >
                  Clear All
                </Button>
                <Button
                  variant="contained"
                  size="small"
                  onClick={uploadFiles}
                  disabled={uploading || files.every(f => f.status === 'completed')}
                  startIcon={<CloudUpload />}
                >
                  {uploading ? 'Uploading...' : 'Upload All'}
                </Button>
              </Box>
            </Box>

            <List dense>
              {files.map((file) => (
                <ListItem key={file.id} sx={{ border: '1px solid #eee', mb: 1, borderRadius: 1 }}>
                  <ListItemIcon>
                    {getFileIcon(file.name)}
                  </ListItemIcon>
                  <ListItemText
                    primary={file.name}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          Size: {(file.size / 1024).toFixed(1)} KB
                        </Typography>
                        {file.objectId && (
                          <Typography variant="caption" display="block" color="success.main">
                            ObjectID: {file.objectId.substring(0, 12)}...
                          </Typography>
                        )}
                        {file.error && (
                          <Typography variant="caption" display="block" color="error.main">
                            Error: {file.error}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getFileStatus(file)}
                      <Button
                        size="small"
                        onClick={() => openMetadataDialog(file)}
                        disabled={uploading}
                      >
                        Metadata
                      </Button>
                      <IconButton
                        edge="end"
                        onClick={() => removeFile(file.id)}
                        disabled={uploading}
                        size="small"
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Status Information */}
      {currentCaseId && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Files will be uploaded to <strong>Case ID: {currentCaseId}</strong> under phase <strong>{sourcePhase}</strong>
        </Alert>
      )}

      {/* Metadata Dialog */}
      <Dialog open={showMetadataDialog} onClose={() => setShowMetadataDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          File Metadata: {selectedFile?.name}
          <IconButton
            onClick={() => setShowMetadataDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Description"
              multiline
              rows={3}
              value={fileMetadata[selectedFile?.id]?.description || ''}
              onChange={(e) => setFileMetadata(prev => ({
                ...prev,
                [selectedFile.id]: {
                  ...prev[selectedFile.id],
                  description: e.target.value
                }
              }))}
              placeholder="Describe the relevance and content of this document..."
            />
            <TextField
              label="Tags"
              value={fileMetadata[selectedFile?.id]?.tags || ''}
              onChange={(e) => setFileMetadata(prev => ({
                ...prev,
                [selectedFile.id]: {
                  ...prev[selectedFile.id],
                  tags: e.target.value
                }
              }))}
              placeholder="contract, correspondence, evidence (comma-separated)"
            />
            <FormControl>
              <InputLabel>Relevance Level</InputLabel>
              <Select
                value={fileMetadata[selectedFile?.id]?.relevance || 'medium'}
                onChange={(e) => setFileMetadata(prev => ({
                  ...prev,
                  [selectedFile.id]: {
                    ...prev[selectedFile.id],
                    relevance: e.target.value
                  }
                }))}
                label="Relevance Level"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowMetadataDialog(false)}>Cancel</Button>
          <Button onClick={saveMetadata} variant="contained">Save Metadata</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EvidenceUpload;