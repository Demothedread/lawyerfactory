// ClaimsMatrix Component - Interactive Legal Analysis Interface
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Alert,
    Box,
    Button,
    Chip,
    CircularProgress,
    Grid,
    Typography
} from '@mui/material';
import { useEffect, useState } from 'react';

const ClaimsMatrix = ({
  caseId,
  onClaimSelect,
  onMatrixUpdate,
  apiEndpoint = '/api/claims'
}) => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [matrixData, setMatrixData] = useState(null);

  useEffect(() => {
    if (caseId) {
      loadClaimsMatrix();
    }
  }, [caseId]);

  const loadClaimsMatrix = async () => {
    setLoading(true);
    try {
      // This would integrate with the backend claims matrix API
      const response = await fetch(`${apiEndpoint}/matrix/${caseId}`);
      if (response.ok) {
        const data = await response.json();
        setMatrixData(data);
        setClaims(data.claims || []);
      }
    } catch (error) {
      console.error('Failed to load claims matrix:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClaimSelect = (claim) => {
    setSelectedClaim(claim);
    if (onClaimSelect) {
      onClaimSelect(claim);
    }
  };

  const getElementStatus = (element) => {
    // Mock element status - would come from backend analysis
    const statuses = ['proven', 'disputed', 'missing', 'pending'];
    return statuses[Math.floor(Math.random() * statuses.length)];
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'proven':
        return <CheckCircleIcon sx={{ color: 'var(--soviet-green)' }} />;
      case 'disputed':
        return <ErrorIcon sx={{ color: 'var(--soviet-amber)' }} />;
      case 'missing':
        return <ErrorIcon sx={{ color: 'var(--soviet-red)' }} />;
      default:
        return <InfoIcon sx={{ color: 'var(--soviet-silver)' }} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'proven':
        return 'var(--soviet-green)';
      case 'disputed':
        return 'var(--soviet-amber)';
      case 'missing':
        return 'var(--soviet-red)';
      default:
        return 'var(--soviet-silver)';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress sx={{ color: 'var(--soviet-brass)' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ color: 'var(--soviet-brass)' }}>
        🏗️ Claims Matrix - Interactive Legal Analysis
      </Typography>

      {claims.length === 0 ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          No claims matrix available. Complete intake and research phases to generate claims analysis.
        </Alert>
      ) : (
        <Box>
          {claims.map((claim, index) => (
            <Accordion
              key={claim.id || index}
              expanded={selectedClaim?.id === claim.id}
              onChange={() => handleClaimSelect(claim)}
              sx={{
                mb: 1,
                backgroundColor: 'var(--soviet-panel)',
                border: '1px solid var(--soviet-brass)',
                '&:before': { display: 'none' }
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon sx={{ color: 'var(--soviet-silver)' }} />}
                sx={{
                  backgroundColor: selectedClaim?.id === claim.id ? 'var(--soviet-dark)' : 'transparent',
                  '&:hover': { backgroundColor: 'var(--soviet-dark)' }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <Typography variant="subtitle1" sx={{ color: 'var(--soviet-silver)', mr: 2 }}>
                    {claim.name || `Cause of Action ${index + 1}`}
                  </Typography>
                  <Chip
                    label={`${claim.elements?.length || 0} Elements`}
                    size="small"
                    sx={{
                      backgroundColor: 'var(--soviet-brass)',
                      color: 'var(--soviet-dark)',
                      mr: 1
                    }}
                  />
                  <Chip
                    label={claim.jurisdiction || 'Federal'}
                    size="small"
                    variant="outlined"
                    sx={{
                      borderColor: 'var(--soviet-amber)',
                      color: 'var(--soviet-amber)'
                    }}
                  />
                </Box>
              </AccordionSummary>

              <AccordionDetails sx={{ backgroundColor: 'var(--soviet-dark)' }}>
                <Typography variant="body2" sx={{ color: 'var(--text-secondary)', mb: 2 }}>
                  {claim.description || 'Legal analysis of claim elements and evidentiary requirements.'}
                </Typography>

                <Typography variant="subtitle2" sx={{ color: 'var(--soviet-brass)', mb: 1 }}>
                  Claim Elements:
                </Typography>

                <Grid container spacing={1}>
                  {claim.elements?.map((element, elemIndex) => {
                    const status = getElementStatus(element);
                    return (
                      <Grid item xs={12} sm={6} key={elemIndex}>
                        <Box
                          sx={{
                            p: 2,
                            border: `1px solid ${getStatusColor(status)}`,
                            borderRadius: 1,
                            backgroundColor: 'var(--panel-bg)',
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 1
                          }}
                        >
                          {getStatusIcon(status)}
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body2" sx={{ color: 'var(--soviet-silver)', fontWeight: 'bold' }}>
                              {element.name || `Element ${elemIndex + 1}`}
                            </Typography>
                            <Typography variant="caption" sx={{ color: 'var(--text-secondary)' }}>
                              {element.description || 'Element definition and requirements.'}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                              <Chip
                                label={status.toUpperCase()}
                                size="small"
                                sx={{
                                  backgroundColor: getStatusColor(status),
                                  color: 'var(--soviet-dark)',
                                  fontSize: '0.7rem'
                                }}
                              />
                              {element.evidenceCount && (
                                <Chip
                                  label={`${element.evidenceCount} Evidence`}
                                  size="small"
                                  variant="outlined"
                                  sx={{
                                    borderColor: 'var(--soviet-green)',
                                    color: 'var(--soviet-green)',
                                    fontSize: '0.7rem'
                                  }}
                                />
                              )}
                            </Box>
                          </Box>
                        </Box>
                      </Grid>
                    );
                  })}
                </Grid>

                {claim.analysis && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: 'var(--soviet-brass)', mb: 1 }}>
                      Legal Analysis:
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'var(--text-secondary)' }}>
                      {claim.analysis}
                    </Typography>
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      {selectedClaim && (
        <Box sx={{ mt: 3, p: 2, backgroundColor: 'var(--soviet-panel)', borderRadius: 1 }}>
          <Typography variant="h6" sx={{ color: 'var(--soviet-brass)', mb: 2 }}>
            Selected Claim Analysis: {selectedClaim.name}
          </Typography>
          <Button
            variant="contained"
            sx={{
              backgroundColor: 'var(--soviet-green)',
              '&:hover': { backgroundColor: 'var(--soviet-green-dark)' }
            }}
          >
            Generate Skeletal Outline
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default ClaimsMatrix;