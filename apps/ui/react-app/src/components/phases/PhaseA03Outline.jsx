// PhaseA03Outline - Case outline and structure display

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
import ClaimsMatrix from '../ui/ClaimsMatrix';
import SkeletalOutlineSystem from '../ui/SkeletalOutlineSystem';

const PhaseA03Outline = ({ caseId, onComplete, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [outlineData, setOutlineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadOutlineData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getOutlineResults(caseId);
        setOutlineData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadOutlineData();
  }, [caseId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress sx={{ color: 'var(--neon-cyan)' }} />
        <Typography sx={{ ml: 2, color: 'var(--neon-cyan)' }}>
          Loading outline data...
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
          📄 PHASE A03 - CASE OUTLINE
        </Typography>

        <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
          Review claims matrix, case structure, legal theory, and argument outline.
        </Typography>

        {/* Status */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
          <Chip
            label={`Claims: ${outlineData?.claimsMatrix?.length || 0}`}
            color="info"
            size="small"
          />
          <Chip
            label={`Sections: ${outlineData?.structure?.sections || 0}`}
            color="success"
            size="small"
          />
          <Chip
            label="Legal Theory Developed"
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
          <Tab label="Claims Matrix" />
          <Tab label="Case Structure" />
          <Tab label="Legal Theory" />
          <Tab label="Argument Outline" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3, minHeight: '400px' }}>
          {/* Claims Matrix Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📋 Claims Matrix
              </Typography>
              <ClaimsMatrix
                caseId={caseId}
                onClaimSelect={(claim) => console.log('Claim selected:', claim)}
                onMatrixUpdate={(updatedMatrix) => {
                  console.log('Claims matrix updated:', updatedMatrix);
                }}
                editable={false}
              />
            </Box>
          )}

          {/* Case Structure Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                🏗️ Case Structure
              </Typography>
              {outlineData?.structure?.sections?.map((section, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {section.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999', mb: 1 }}>
                    Type: {section.type} | Order: {section.order}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    {section.description}
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No structure defined yet.</Typography>}
            </Box>
          )}

          {/* Legal Theory Tab */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                ⚖️ Legal Theory
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  {outlineData?.theory?.summary || 'No legal theory summary available.'}
                </Typography>
                {outlineData?.theory?.elements?.map((element, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)' }}>
                      {element.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#fff' }}>
                      {element.description}
                    </Typography>
                  </Box>
                )) || <Typography sx={{ color: '#999' }}>No theory elements defined.</Typography>}
              </Paper>
            </Box>
          )}

          {/* Argument Outline Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📝 Argument Outline
              </Typography>
              <SkeletalOutlineSystem
                caseId={caseId}
                claimsMatrix={outlineData?.claimsMatrix || []}
                shotList={[]} // Not needed for outline view
                onOutlineGenerated={(outline) => console.log('Outline generated:', outline)}
                onSectionUpdate={(section) => console.log('Section updated:', section)}
                editable={false}
              />
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
              Outline Complete
            </Typography>
            <Typography variant="body2" sx={{ color: '#999' }}>
              Ready to proceed to Phase B01 - Quality Review
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
              onClick={() => onComplete(outlineData)}
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
              Proceed to Review
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default PhaseA03Outline;