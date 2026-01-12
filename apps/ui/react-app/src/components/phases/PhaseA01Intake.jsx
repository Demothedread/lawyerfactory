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
import backendService from '../../services/backendService';
import DocumentList from '../DocumentList';
import ShotList from '../ui/ShotList';

/**
 * PhaseA01Intake - Document Intake & Processing
 * 
 * Captures legal narrative, uploads evidence, and triggers fact extraction
 * Workflow: Narrative + Evidence → ShotList → Extracted Facts → SOF
 */
const PhaseA01Intake = ({ caseId, onComplete, onClose }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [intakeData, setIntakeData] = useState({
    claim_description: '',
    jurisdiction: '',
    venue: '',
    plaintiff_name: '',
    defendant_name: '',
  });
  const [evidenceData, setEvidenceData] = useState([]);
  const [extractedFacts, setExtractedFacts] = useState([]);
  const [sofContent, setSofContent] = useState('');
  const [shotListReady, setShotListReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (caseId) {
      loadCaseData();
    }
  }, [caseId]);

  const loadCaseData = async () => {
    try {
      setLoading(true);
      const docs = await backendService.getCaseDocuments(caseId);
      setEvidenceData(docs || []);
    } catch (err) {
      console.error('Failed to load case documents:', err);
      setError('Failed to load evidence documents');
    } finally {
      setLoading(false);
    }
  };


  const handleStatementOfFactsReady = (sofData) => {
    setSofContent(sofData);
    setExtractedFacts(sofData.facts || []);
    setShotListReady(true);
    setTabValue(2); // Switch to Extracted Facts tab
  };

  const handleComplete = () => {
    if (shotListReady && onComplete) {
      onComplete({
        intakeData,
        evidenceData,
        extractedFacts,
        sofContent,
      });
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>📋 Phase A01: Document Intake</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Documents" />
          <Tab label="Shot List" />
          <Tab label="Extracted Facts" />
          <Tab label="Metadata" />
        </Tabs>

        <Box sx={{ p: 2 }}>
          {tabValue === 0 && (
            <Box>
              <Typography variant="subtitle2">📄 Categorized Documents</Typography>
              {loading ? (
                <CircularProgress />
              ) : evidenceData.length > 0 ? (
                <DocumentList documents={evidenceData} />
              ) : (
                <Typography color="textSecondary">No documents uploaded yet</Typography>
              )}
            </Box>
          )}

          {tabValue === 1 && (
            <ShotList
              caseId={caseId}
              evidenceData={evidenceData}
              userNarrative={intakeData.claim_description}
              intakeData={intakeData}
              onStatementOfFactsReady={handleStatementOfFactsReady}
            />
          )}

          {tabValue === 2 && (
            <Box>
              <Typography variant="subtitle2">🎯 Extracted Facts</Typography>
              {extractedFacts.length > 0 ? (
                <Box>
                  {extractedFacts.map((fact, idx) => (
                    <Paper key={idx} sx={{ p: 1.5, mb: 1 }}>
                      <Typography variant="body2">
                        <strong>F{fact.fact_number}:</strong> {fact.fact_text}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        {fact.date && <Chip label={`📅 ${fact.date}`} size="small" />}
                        {fact.entities?.people?.length > 0 && (
                          <Chip label={`👤 ${fact.entities.people.join(', ')}`} size="small" />
                        )}
                      </Box>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Typography color="textSecondary">Facts will appear after LLM extraction</Typography>
              )}
            </Box>
          )}

          {tabValue === 3 && (
            <Box>
              <Typography variant="subtitle2">📊 Intake Metadata</Typography>
              <Paper sx={{ p: 2, mt: 1 }}>
                <Typography variant="body2">
                  <strong>Jurisdiction:</strong> {intakeData.jurisdiction || 'Not set'}
                </Typography>
                <Typography variant="body2">
                  <strong>Venue:</strong> {intakeData.venue || 'Not set'}
                </Typography>
                <Typography variant="body2">
                  <strong>Plaintiff:</strong> {intakeData.plaintiff_name || 'Not set'}
                </Typography>
                <Typography variant="body2">
                  <strong>Defendant:</strong> {intakeData.defendant_name || 'Not set'}
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </Paper>

      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button variant="outlined" onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleComplete}
          disabled={!shotListReady}
        >
          Continue to Phase A02 ✓
        </Button>
      </Box>
    </Box>
  );
};

export default PhaseA01Intake;