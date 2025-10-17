// PhaseC01Editing - Final editing and formatting display

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

const PhaseC01Editing = ({ caseId, onComplete, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [editingData, setEditingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadEditingData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getEditingResults(caseId);
        setEditingData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadEditingData();
  }, [caseId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress sx={{ color: 'var(--neon-cyan)' }} />
        <Typography sx={{ ml: 2, color: 'var(--neon-cyan)' }}>
          Loading editing data...
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
          ✏️ PHASE C01 - FINAL EDITING
        </Typography>

        <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
          Review final documents, citation formatting, and professional polish.
        </Typography>

        {/* Status */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
          <Chip
            label={`Documents: ${editingData?.documents?.length || 0}`}
            color="info"
            size="small"
          />
          <Chip
            label={`Citations: ${editingData?.citations?.count || 0}`}
            color="success"
            size="small"
          />
          <Chip
            label="Professional Polish Applied"
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
          <Tab label="Final Documents" />
          <Tab label="Citation Formatting" />
          <Tab label="Professional Polish" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3, minHeight: '400px' }}>
          {/* Final Documents Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📄 Final Documents
              </Typography>
              {editingData?.documents?.map((doc, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {doc.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999', mb: 1 }}>
                    Type: {doc.type} | Pages: {doc.pages} | Status: {doc.status}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    {doc.description}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    sx={{ mt: 1, color: 'var(--neon-cyan)', borderColor: 'var(--neon-cyan)' }}
                    onClick={() => window.open(doc.url, '_blank')}
                  >
                    View Document
                  </Button>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No final documents available.</Typography>}
            </Box>
          )}

          {/* Citation Formatting Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📚 Citation Formatting
              </Typography>
              <Paper sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  Citation Style: {editingData?.citations?.style || 'Bluebook'}
                </Typography>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  Total Citations: {editingData?.citations?.count || 0}
                </Typography>
              </Paper>
              {editingData?.citations?.examples?.map((citation, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)' }}>
                    {citation.type}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff', fontFamily: 'monospace' }}>
                    {citation.formatted}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#999' }}>
                    Source: {citation.source}
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No citation examples available.</Typography>}
            </Box>
          )}

          {/* Professional Polish Tab */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                ✨ Professional Polish
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  {editingData?.polish?.summary || 'Professional editing and formatting applied to all documents.'}
                </Typography>
                {editingData?.polish?.improvements?.map((improvement, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)' }}>
                      {improvement.category}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#fff' }}>
                      {improvement.description}
                    </Typography>
                  </Box>
                )) || <Typography sx={{ color: '#999' }}>No polish details available.</Typography>}
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
              Editing Complete
            </Typography>
            <Typography variant="body2" sx={{ color: '#999' }}>
              Ready to proceed to Phase C02 - Final Orchestration
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
              onClick={() => onComplete(editingData)}
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
              Proceed to Orchestration
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default PhaseC01Editing;