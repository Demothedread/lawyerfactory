// PhaseA01Intake - Document intake and initial processing display

import {
    Alert,
    Box,
    Button,
    Chip,
    CircularProgress,
    Paper,
    Tab,
    Tabs,
    Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';

import { apiService } from '../../services/apiService';

const PhaseA01Intake = ({ caseId, onComplete, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [intakeData, setIntakeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadIntakeData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getIntakeResults(caseId);
        setIntakeData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadIntakeData();
  }, [caseId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress sx={{ color: 'var(--neon-cyan)' }} />
        <Typography sx={{ ml: 2, color: 'var(--neon-cyan)' }}>
          Loading intake data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      {/* Header */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, rgba(0,255,255,0.1) 0%, rgba(0,200,200,0.05) 100%)',
          border: '2px solid var(--neon-cyan)',
          borderRadius: '8px'
        }}
      >
        <Typography
          variant="h4"
          sx={{
            fontFamily: 'Orbitron, monospace',
            color: 'var(--neon-cyan)',
            textShadow: '0 0 10px rgba(0,255,255,0.5)',
            mb: 2
          }}
        >
          📄 PHASE A01 - DOCUMENT INTAKE
        </Typography>

        <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
          Review categorized documents, extracted facts, and initial metadata from the intake process.
        </Typography>

        {/* Status */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
          <Chip
            label={`Documents: ${intakeData?.documents?.length || 0}`}
            color="info"
            size="small"
          />
          <Chip
            label={`Facts Extracted: ${intakeData?.facts?.length || 0}`}
            color="success"
            size="small"
          />
          <Chip
            label="Metadata Processed"
            color="primary"
            size="small"
          />
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper elevation={3} sx={{ backgroundColor: 'rgba(0,0,0,0.7)', border: '1px solid var(--neon-cyan)' }}>
        <Tabs
          value={activeTab}
          onChange={(_e, newValue) => setActiveTab(newValue)}
          sx={{
            borderBottom: '1px solid var(--neon-cyan)',
            '& .MuiTab-root': {
              color: '#999',
              fontFamily: 'Orbitron, monospace',
              '&.Mui-selected': {
                color: 'var(--neon-cyan)',
              }
            }
          }}
        >
          <Tab label="Categorized Documents" />
          <Tab label="Extracted Facts" />
          <Tab label="Metadata" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3, minHeight: '400px' }}>
          {/* Documents Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📋 Document Categorization
              </Typography>
              {intakeData?.documents?.map((doc, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {doc.filename}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999' }}>
                    Type: {doc.category} | Pages: {doc.pages}
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No documents processed yet.</Typography>}
            </Box>
          )}

          {/* Facts Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                🔍 Extracted Facts
              </Typography>
              {intakeData?.facts?.map((fact, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="body1" sx={{ color: '#fff' }}>
                    {fact.text}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#999' }}>
                    Source: {fact.source} | Confidence: {fact.confidence}%
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No facts extracted yet.</Typography>}
            </Box>
          )}

          {/* Metadata Tab */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📊 Initial Metadata
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 1 }}>
                  Case ID: {caseId}
                </Typography>
                <Typography variant="body1" sx={{ color: '#fff', mb: 1 }}>
                  Total Documents: {intakeData?.metadata?.totalDocuments || 0}
                </Typography>
                <Typography variant="body1" sx={{ color: '#fff', mb: 1 }}>
                  Processing Date: {intakeData?.metadata?.processedAt || 'N/A'}
                </Typography>
                <Typography variant="body1" sx={{ color: '#fff' }}>
                  Status: {intakeData?.metadata?.status || 'Completed'}
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Action Buttons */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          mt: 3,
          background: 'linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(0,50,50,0.8) 100%)',
          border: '2px solid var(--neon-cyan)',
          borderRadius: '8px'
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" sx={{ color: '#fff', mb: 1 }}>
              Intake Processing Complete
            </Typography>
            <Typography variant="body2" sx={{ color: '#999' }}>
              Ready to proceed to Phase A02 - Legal Research
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={onClose}
              sx={{
                color: '#999',
                borderColor: '#666',
                '&:hover': { borderColor: '#999' }
              }}
            >
              Close
            </Button>

            <Button
              variant="contained"
              onClick={() => onComplete(intakeData)}
              sx={{
                backgroundColor: 'var(--neon-cyan)',
                color: '#000',
                fontFamily: 'Orbitron, monospace',
                fontSize: '16px',
                px: 4,
                py: 1.5,
                '&:hover': {
                  backgroundColor: 'var(--neon-cyan-dark)'
                }
              }}
            >
              Proceed to Research
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default PhaseA01Intake;