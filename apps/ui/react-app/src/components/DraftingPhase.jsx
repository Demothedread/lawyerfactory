import {
    Error as AlertCircle,
    CheckCircle,
    CloudDownload as Download,
    Description as FileText,
    Loop as Loader2,
    PlayArrow as Play,
    Refresh as RefreshCw
} from '@mui/icons-material';
import { Alert, Badge, Box, Button, Card, CardContent, CardHeader, Divider, LinearProgress, Tab, Tabs } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { generateSkeletalOutline, getClaimsMatrix, getSocket, startPhase } from '../services/apiService';
import ComplaintViewer from './ComplaintViewer';
import StatementOfFactsViewer from './StatementOfFactsViewer';

/**
 * DraftingPhase - Complete drafting workflow component
 * Integrates skeletal outline generation, drafting execution, and document viewing
 */
const DraftingPhase = ({ caseId, onPhaseComplete }) => {
  const [phaseState, setPhaseState] = useState({
    status: 'idle', // idle, generating_outline, drafting, completed, error
    progress: 0,
    currentStep: '',
    error: null
  });

  const [documents, setDocuments] = useState({
    skeletalOutline: null,
    statementOfFacts: null,
    complaint: null
  });

  const [claimsMatrix, setClaimsMatrix] = useState([]);
  const [activeTab, setActiveTab] = useState('outline');

  // Socket.IO event handlers
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const handlePhaseUpdate = (data) => {
      if (data.phase === 'phaseB02_drafting' && data.case_id === caseId) {
        setPhaseState(prev => ({
          ...prev,
          status: data.status,
          progress: data.progress || 0,
          currentStep: data.step || '',
          error: data.error || null
        }));

        // Update documents when they're generated
        if (data.documents) {
          setDocuments(prev => ({
            ...prev,
            ...data.documents
          }));
        }

        if (data.status === 'completed') {
          onPhaseComplete && onPhaseComplete(data);
        }
      }
    };

    socket.on('phase_progress_update', handlePhaseUpdate);

    return () => {
      socket.off('phase_progress_update', handlePhaseUpdate);
    };
  }, [caseId, onPhaseComplete]);

  // Load claims matrix on mount
  useEffect(() => {
    const loadClaimsMatrix = async () => {
      try {
        const matrix = await getClaimsMatrix(caseId);
        setClaimsMatrix(matrix);
      } catch (error) {
        console.error('Failed to load claims matrix:', error);
      }
    };

    if (caseId) {
      loadClaimsMatrix();
    }
  }, [caseId]);

  // Generate skeletal outline
  const handleGenerateOutline = useCallback(async () => {
    if (!claimsMatrix.length) {
      setPhaseState(prev => ({
        ...prev,
        error: 'No claims matrix available. Please complete research phase first.'
      }));
      return;
    }

    setPhaseState({
      status: 'generating_outline',
      progress: 0,
      currentStep: 'Generating skeletal outline...',
      error: null
    });

    try {
      const outlineData = await generateSkeletalOutline(caseId, claimsMatrix);
      setDocuments(prev => ({
        ...prev,
        skeletalOutline: outlineData
      }));

      setPhaseState(prev => ({
        ...prev,
        status: 'outline_generated',
        progress: 25,
        currentStep: 'Skeletal outline generated successfully'
      }));
    } catch (error) {
      setPhaseState(prev => ({
        ...prev,
        status: 'error',
        error: error.message || 'Failed to generate skeletal outline'
      }));
    }
  }, [caseId, claimsMatrix]);

  // Start drafting phase
  const handleStartDrafting = useCallback(async () => {
    if (!documents.skeletalOutline) {
      setPhaseState(prev => ({
        ...prev,
        error: 'Please generate skeletal outline first.'
      }));
      return;
    }

    setPhaseState({
      status: 'drafting',
      progress: 25,
      currentStep: 'Starting drafting phase...',
      error: null
    });

    try {
      await startPhase('phaseB02_drafting', caseId, {
        skeletal_outline: documents.skeletalOutline,
        claims_matrix: claimsMatrix
      });
    } catch (error) {
      setPhaseState(prev => ({
        ...prev,
        status: 'error',
        error: error.message || 'Failed to start drafting phase'
      }));
    }
  }, [caseId, documents.skeletalOutline, claimsMatrix]);

  // Handle document downloads
  const handleDownloadDocument = useCallback((docType) => {
    const doc = documents[docType];
    if (!doc) return;

    const blob = new Blob([JSON.stringify(doc, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${docType}_${caseId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [documents, caseId]);

  // Handle fact clicks in statement of facts
  const handleFactClick = useCallback((factId, evidence) => {
    console.log('Fact clicked:', factId, evidence);
    // Could open evidence viewer or highlight related content
  }, []);

  // Handle section editing in complaint
  const handleSectionEdit = useCallback((sectionId, content) => {
    console.log('Section edit requested:', sectionId, content);
    // Could open edit modal or trigger regeneration
  }, []);

  // Handle citation validation
  const handleValidateCitation = useCallback(async () => {
    // Mock validation - in real implementation, call API
    return { valid: Math.random() > 0.3 };
  }, []);

  // Render status indicator
  const renderStatusIndicator = () => {
    const { status, progress, currentStep, error } = phaseState;

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {status === 'idle' && <FileText sx={{ width: 16, height: 16, color: 'text.disabled' }} />}
            {status === 'generating_outline' && <Loader2 sx={{ width: 16, height: 16, color: 'primary.main', animation: 'spin 1s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />}
            {status === 'drafting' && <Play sx={{ width: 16, height: 16, color: 'success.main' }} />}
            {status === 'completed' && <CheckCircle sx={{ width: 16, height: 16, color: 'success.main' }} />}
            {status === 'error' && <AlertCircle sx={{ width: 16, height: 16, color: 'error.main' }} />}
            <Box component="span" sx={{ fontSize: '0.875rem', fontWeight: 500, textTransform: 'capitalize' }}>
              {status.replace('_', ' ')}
            </Box>
          </Box>
          <Badge color="primary" variant="outlined">{progress}%</Badge>
        </Box>

        <LinearProgress variant="determinate" value={progress} sx={{ width: '100%' }} />

        {currentStep && (
          <Box component="p" sx={{ fontSize: '0.75rem', color: 'text.secondary', m: 0 }}>
            {currentStep}
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 1 }}>
            {error}
          </Alert>
        )}
      </Box>
    );
  };

  // Render skeletal outline preview
  const renderSkeletalOutline = () => {
    const outline = documents.skeletalOutline;
    if (!outline) {
      return (
        <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
          <FileText sx={{ width: 48, height: 48, mx: 'auto', mb: 2, opacity: 0.5 }} />
          <p>No skeletal outline generated yet.</p>
          <Button
            variant="contained"
            onClick={handleGenerateOutline}
            disabled={phaseState.status === 'generating_outline'}
            sx={{ mt: 2 }}
          >
            {phaseState.status === 'generating_outline' ? (
              <>
                <Loader2 sx={{ width: 16, height: 16, mr: 1, animation: 'spin 1s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />
                Generating...
              </>
            ) : (
              'Generate Outline'
            )}
          </Button>
        </Box>
      );
    }

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box component="h3" sx={{ fontSize: '1.125rem', fontWeight: 500 }}>Skeletal Outline</Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={handleGenerateOutline}
              disabled={phaseState.status === 'generating_outline'}
              startIcon={<RefreshCw sx={{ width: 16, height: 16 }} />}
            >
              Regenerate
            </Button>
            <Button
              variant="outlined"
              size="small"
              onClick={() => handleDownloadDocument('skeletalOutline')}
              startIcon={<Download sx={{ width: 16, height: 16 }} />}
            >
              Download
            </Button>
          </Box>
        </Box>

        <Box sx={{ bgcolor: '#f9fafb', p: 2, borderRadius: 2 }}>
          <Box component="pre" sx={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap', fontFamily: 'monospace', m: 0 }}>
            {typeof outline === 'string' ? outline : JSON.stringify(outline, null, 2)}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleStartDrafting}
            disabled={phaseState.status === 'drafting'}
          >
            {phaseState.status === 'drafting' ? (
              <>
                <Loader2 sx={{ width: 16, height: 16, mr: 1, animation: 'spin 1s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />
                Drafting...
              </>
            ) : (
              <>
                <Play sx={{ width: 16, height: 16, mr: 1 }} />
                Start Drafting
              </>
            )}
          </Button>
        </Box>
      </Box>
    );
  };

  return (
    <Card sx={{ width: '100%' }}>
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FileText sx={{ width: 20, height: 20 }} />
            Drafting Phase (B02)
          </Box>
        }
        subheader="Generate skeletal outlines from claims matrix and produce professional legal documents"
      />

      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Status and Progress */}
        {renderStatusIndicator()}

        <Divider />

        {/* Main Content Tabs */}
        <Box sx={{ width: '100%' }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab value="outline" label="Skeletal Outline" />
            <Tab value="facts" label="Statement of Facts" disabled={!documents.statementOfFacts} />
            <Tab value="complaint" label="Complaint" disabled={!documents.complaint} />
          </Tabs>

          {activeTab === 'outline' && (
            <Box sx={{ mt: 2 }}>
              {renderSkeletalOutline()}
            </Box>
          )}

          {activeTab === 'facts' && (
            <Box sx={{ mt: 2 }}>
              <StatementOfFactsViewer
                caseId={caseId}
                documentData={documents.statementOfFacts}
                onFactClick={handleFactClick}
                onDownload={() => handleDownloadDocument('statementOfFacts')}
              />
            </Box>
          )}

          {activeTab === 'complaint' && (
            <Box sx={{ mt: 2 }}>
              <ComplaintViewer
                caseId={caseId}
                documentData={documents.complaint}
                onSectionEdit={handleSectionEdit}
                onDownload={() => handleDownloadDocument('complaint')}
                onValidate={handleValidateCitation}
              />
            </Box>
          )}
        </Box>

        {/* Claims Matrix Summary */}
        {claimsMatrix.length > 0 && (
          <>
            <Divider />
            <Box sx={{ bgcolor: '#e3f2fd', p: 2, borderRadius: 2 }}>
              <Box component="h4" sx={{ fontWeight: 500, fontSize: '0.875rem', color: '#1565c0', mb: 1 }}>
                Claims Matrix Summary
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {claimsMatrix.slice(0, 5).map((claim, index) => (
                  <Badge key={index} color="secondary" sx={{ fontSize: '0.75rem' }}>
                    {claim.title || `Claim ${index + 1}`}
                  </Badge>
                ))}
                {claimsMatrix.length > 5 && (
                  <Badge variant="outlined" sx={{ fontSize: '0.75rem' }}>
                    +{claimsMatrix.length - 5} more
                  </Badge>
                )}
              </Box>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default DraftingPhase;