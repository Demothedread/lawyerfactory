// Enhanced Evidence Upload component with unified storage 
//
// Enhanced Evidence Upload component with unified storage 
import {
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
  Typography,
  Alert
} from '@mui/material';

import {
  PictureAsPdf,
  Description,
  InsertDriveFile,
  Visibility,
  CheckCircle,
  Error,
  CloudUpload,
  Close,
  Delete
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
    if (file.status === 'uploading') {
      return <LinearProgress variant="determinate" value={uploadProgress[file.id] || 0} />;
    } else if (file.status === 'completed') {
      return <Chip label="Uploaded" color="success" size="small" icon={<CheckCircle />} />;
    } else if (file.status === 'error') {
      return <Chip label="Error" color="error" size="small" icon={<Error />} />;
    }
    return <Chip label="Ready" color="default" size="small" />;
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
      {/* Upload Zone */}
      <Card 
        sx={{ 
          mb: 2,
          border: dragActive ? '2px dashed #1976d2' : '2px dashed #ccc',
          backgroundColor: dragActive ? 'rgba(25, 118, 210, 0.1)' : 'transparent',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {dragActive ? 'Drop files here' : 'Upload Evidence Documents'}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Drag and drop files here, or click to select files
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Accepted formats: {acceptedTypes.join(', ')} | Max size: {Math.round(maxFileSize / 1024 / 1024)}MB
          </Typography>
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