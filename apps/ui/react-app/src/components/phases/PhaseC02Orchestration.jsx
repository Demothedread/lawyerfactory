// PhaseC02Orchestration - Final orchestration and delivery display

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

const PhaseC02Orchestration = ({ caseId, onComplete, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [orchestrationData, setOrchestrationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadOrchestrationData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getOrchestrationResults(caseId);
        setOrchestrationData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadOrchestrationData();
  }, [caseId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress sx={{ color: 'var(--neon-cyan)' }} />
        <Typography sx={{ ml: 2, color: 'var(--neon-cyan)' }}>
          Loading orchestration data...
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
          🎯 PHASE C02 - FINAL ORCHESTRATION
        </Typography>

        <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
          Review court-ready documents, filing package, case summary, and final archive.
        </Typography>

        {/* Status */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
          <Chip
            label={`Documents: ${orchestrationData?.documents?.length || 0}`}
            color="info"
            size="small"
          />
          <Chip
            label="Filing Package Ready"
            color="success"
            size="small"
          />
          <Chip
            label="Case Summary Complete"
            color="primary"
            size="small"
          />
          <Chip
            label="Archive Created"
            color="warning"
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
          <Tab label="Court-Ready Documents" />
          <Tab label="Filing Package" />
          <Tab label="Case Summary" />
          <Tab label="Final Archive" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3, minHeight: '400px' }}>
          {/* Court-Ready Documents Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                ⚖️ Court-Ready Documents
              </Typography>
              {orchestrationData?.documents?.map((doc, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {doc.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999', mb: 1 }}>
                    Type: {doc.type} | Format: {doc.format} | Pages: {doc.pages}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff', mb: 1 }}>
                    {doc.description}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    sx={{ color: 'var(--neon-cyan)', borderColor: 'var(--neon-cyan)' }}
                    onClick={() => window.open(doc.url, '_blank')}
                  >
                    Download
                  </Button>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No court-ready documents available.</Typography>}
            </Box>
          )}

          {/* Filing Package Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📦 Filing Package
              </Typography>
              <Paper sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  Complete filing package assembled and ready for court submission.
                </Typography>
                <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)', mb: 1 }}>
                  Package Contents:
                </Typography>
                {orchestrationData?.filingPackage?.contents?.map((item, index) => (
                  <Typography key={index} variant="body2" sx={{ color: '#fff', ml: 2 }}>
                    • {item}
                  </Typography>
                )) || <Typography sx={{ color: '#999' }}>No contents listed.</Typography>}
              </Paper>
              <Button
                variant="contained"
                sx={{ backgroundColor: 'var(--neon-green)', color: '#000' }}
                onClick={() => window.open(orchestrationData?.filingPackage?.downloadUrl, '_blank')}
              >
                Download Filing Package
              </Button>
            </Box>
          )}

          {/* Case Summary Tab */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📋 Case Summary
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  {orchestrationData?.summary?.overview || 'Case summary not available.'}
                </Typography>
                <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)', mb: 1 }}>
                  Key Facts:
                </Typography>
                {orchestrationData?.summary?.keyFacts?.map((fact, index) => (
                  <Typography key={index} variant="body2" sx={{ color: '#fff', ml: 2, mb: 1 }}>
                    • {fact}
                  </Typography>
                )) || <Typography sx={{ color: '#999' }}>No key facts listed.</Typography>}
                <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)', mb: 1, mt: 2 }}>
                  Legal Arguments:
                </Typography>
                {orchestrationData?.summary?.arguments?.map((arg, index) => (
                  <Typography key={index} variant="body2" sx={{ color: '#fff', ml: 2, mb: 1 }}>
                    • {arg}
                  </Typography>
                )) || <Typography sx={{ color: '#999' }}>No arguments listed.</Typography>}
              </Paper>
            </Box>
          )}

          {/* Final Archive Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📚 Final Archive
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  Complete case archive created with all deliverables, evidence, and metadata.
                </Typography>
                <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)', mb: 1 }}>
                  Archive Contents:
                </Typography>
                {orchestrationData?.archive?.contents?.map((item, index) => (
                  <Typography key={index} variant="body2" sx={{ color: '#fff', ml: 2, mb: 1 }}>
                    • {item}
                  </Typography>
                )) || <Typography sx={{ color: '#999' }}>No archive contents listed.</Typography>}
                <Typography variant="body2" sx={{ color: '#999', mt: 2 }}>
                  Archive Size: {orchestrationData?.archive?.size || 'N/A'} | Created: {orchestrationData?.archive?.createdAt || 'N/A'}
                </Typography>
              </Paper>
              <Button
                variant="contained"
                sx={{ mt: 2, backgroundColor: 'var(--neon-amber)', color: '#000' }}
                onClick={() => window.open(orchestrationData?.archive?.downloadUrl, '_blank')}
              >
                Download Archive
              </Button>
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
          border: '2px solid var(--neon-green)',
          borderRadius: '8px'
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" sx={{ color: '#fff', mb: 1 }}>
              🎉 Case Complete - All Phases Finished
            </Typography>
            <Typography variant="body2" sx={{ color: '#999', mb: 3 }}>
              Court-ready documents, filing package, and complete archive are available for download.
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="outlined"
                onClick={onClose}
                sx={{
                  color: '#999',
                  borderColor: '#666',
                  '&:hover': { borderColor: '#999' }
                }}
              >
                Close Case
              </Button>

              <Button
                variant="contained"
                onClick={() => onComplete(orchestrationData)}
                sx={{
                  backgroundColor: 'var(--neon-green)',
                  color: '#000',
                  fontFamily: 'Orbitron, monospace',
                  fontSize: '16px',
                  px: 4,
                  py: 1.5,
                  '&:hover': {
                    backgroundColor: 'var(--neon-green-dark)'
                  }
                }}
              >
                Mark Complete
              </Button>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default PhaseC02Orchestration;