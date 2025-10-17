// PhaseA02Research - Legal research results display

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

const PhaseA02Research = ({ caseId, onComplete, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [researchData, setResearchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadResearchData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getResearchResults(caseId);
        setResearchData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadResearchData();
  }, [caseId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress sx={{ color: 'var(--neon-cyan)' }} />
        <Typography sx={{ ml: 2, color: 'var(--neon-cyan)' }}>
          Loading research data...
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
          🔍 PHASE A02 - LEGAL RESEARCH
        </Typography>

        <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
          Review gathered authorities, case law, statutes, and research matrix from legal research.
        </Typography>

        {/* Status */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
          <Chip
            label={`Case Law: ${researchData?.caseLaw?.length || 0}`}
            color="info"
            size="small"
          />
          <Chip
            label={`Statutes: ${researchData?.statutes?.length || 0}`}
            color="success"
            size="small"
          />
          <Chip
            label={`Authorities: ${researchData?.authorities?.length || 0}`}
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
          <Tab label="Case Law" />
          <Tab label="Statutes" />
          <Tab label="Legal Authorities" />
          <Tab label="Research Matrix" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3, minHeight: '400px' }}>
          {/* Case Law Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                ⚖️ Relevant Case Law
              </Typography>
              {researchData?.caseLaw?.map((caseItem, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {caseItem.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999', mb: 1 }}>
                    Citation: {caseItem.citation} | Court: {caseItem.court}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    {caseItem.summary}
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No case law found.</Typography>}
            </Box>
          )}

          {/* Statutes Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📜 Relevant Statutes
              </Typography>
              {researchData?.statutes?.map((statute, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {statute.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999', mb: 1 }}>
                    Code: {statute.code} | Section: {statute.section}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    {statute.text}
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No statutes found.</Typography>}
            </Box>
          )}

          {/* Authorities Tab */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📚 Legal Authorities
              </Typography>
              {researchData?.authorities?.map((authority, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                  <Typography variant="subtitle1" sx={{ color: '#fff' }}>
                    {authority.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999', mb: 1 }}>
                    Type: {authority.type} | Source: {authority.source}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    {authority.description}
                  </Typography>
                </Paper>
              )) || <Typography sx={{ color: '#999' }}>No authorities found.</Typography>}
            </Box>
          )}

          {/* Research Matrix Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📊 Research Matrix
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'rgba(0,50,50,0.5)' }}>
                <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
                  Research completed with {researchData?.matrix?.totalQueries || 0} queries across {researchData?.matrix?.sources || 0} sources.
                </Typography>
                {researchData?.matrix?.elements?.map((element, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: 'var(--neon-cyan)' }}>
                      {element.claim}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#fff' }}>
                      Supporting Authorities: {element.authorities?.length || 0}
                    </Typography>
                  </Box>
                )) || <Typography sx={{ color: '#999' }}>No research matrix available.</Typography>}
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
              Research Complete
            </Typography>
            <Typography variant="body2" sx={{ color: '#999' }}>
              Ready to proceed to Phase A03 - Case Outline
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
              onClick={() => onComplete(researchData)}
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
              Proceed to Outline
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default PhaseA02Research;