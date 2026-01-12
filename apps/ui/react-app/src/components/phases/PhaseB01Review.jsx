// PhaseB01Review - User review and approval of Phase A03 deliverables before drafting

import CheckCircle from '@mui/icons-material/CheckCircle';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  LinearProgress,
  Paper,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';

import backendService from '../../services/backendService';
import ClaimsMatrix from '../ui/ClaimsMatrix';
import ShotList from '../ui/ShotList';
import SkeletalOutlineSystem from '../ui/SkeletalOutlineSystem';
import StatementOfFactsViewer from '../ui/StatementOfFactsViewer';

const PhaseB01Review = ({ caseId, onApprove, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [deliverables, setDeliverables] = useState(null);
  const [approvals, setApprovals] = useState({
    statementOfFacts: false,
    shotlist: false,
    claimsMatrix: false,
    skeletalOutline: false
  });
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sofContent, setSofContent] = useState(null);
  const [sofDialogOpen, setSofDialogOpen] = useState(false);

  useEffect(() => {
    const loadDeliverables = async () => {
      try {
        setLoading(true);
        const data = await backendService.validateDeliverables(caseId);
        setDeliverables(data.deliverables);
        setValidation(data.validation);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadDeliverables();
  }, [caseId]);

  const handleApprove = (type) => {
    setApprovals((prev) => ({ ...prev, [type]: true }));
  };

  const allApproved = Object.values(approvals).every(Boolean);
  const canProceed = validation?.ready_for_drafting && allApproved;
  const allValidationsPassed = Boolean(
    validation &&
      validation.shotlist_facts?.passed &&
      validation.claims_elements?.passed &&
      validation.outline_sections?.passed &&
      validation.rule_12b6_score?.passed
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress sx={{ color: 'var(--neon-cyan)' }} />
        <Typography sx={{ ml: 2, color: 'var(--neon-cyan)' }}>
          Loading deliverables...
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
          🔍 PHASE B01 - DELIVERABLE REVIEW
        </Typography>
        
        <Typography variant="body1" sx={{ color: '#fff', mb: 2 }}>
          Review and approve all Phase A03 deliverables before proceeding to drafting.
          Each deliverable must be approved to unlock Phase B02.
        </Typography>

        {/* Validation Status */}
        {validation ? (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
            <Chip
              label={`Shotlist: ${validation.shotlist_facts.passed ? 'Passed' : 'Pending'}`}
              color={validation.shotlist_facts.passed ? 'success' : 'warning'}
              size="small"
            />
            <Chip
              label={`Claims: ${validation.claims_elements.passed ? 'Passed' : 'Pending'}`}
              color={validation.claims_elements.passed ? 'success' : 'warning'}
              size="small"
            />
            <Chip
              label={`Outline: ${validation.outline_sections.passed ? 'Passed' : 'Pending'}`}
              color={validation.outline_sections.passed ? 'success' : 'warning'}
              size="small"
            />
            <Chip
              label={`Rule 12(b)(6): ${validation.rule_12b6_score.passed ? 'Passed' : 'Pending'}`}
              color={validation.rule_12b6_score.passed ? 'success' : 'warning'}
              size="small"
            />
          </Box>
        ) : (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress sx={{ backgroundColor: 'rgba(0,255,255,0.2)' }} />
            <Typography variant="caption" sx={{ color: 'var(--neon-amber)' }}>
              Validating deliverables...
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Tabs for each deliverable */}
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
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Statement of Facts
                {approvals.statementOfFacts && <CheckCircle sx={{ color: 'var(--neon-green)', fontSize: '16px' }} />}
              </Box>
            }
          />
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Shotlist Timeline
                {approvals.shotlist && <CheckCircle sx={{ color: 'var(--neon-green)', fontSize: '16px' }} />}
              </Box>
            }
          />
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Claims Matrix
                {approvals.claimsMatrix && <CheckCircle sx={{ color: 'var(--neon-green)', fontSize: '16px' }} />}
              </Box>
            }
          />
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Skeletal Outline
                {approvals.skeletalOutline && <CheckCircle sx={{ color: 'var(--neon-green)', fontSize: '16px' }} />}
              </Box>
            }
          />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ p: 3, minHeight: '400px' }}>
          {/* Statement of Facts Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📄 Statement of Facts (Rule 12(b)(6) Compliant)
              </Typography>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Rule 12(b)(6) Compliance:</strong> This Statement of Facts includes jurisdiction, venue, and ripeness determinations. 
                  Review for factual accuracy and legal sufficiency before proceeding to drafting.
                </Typography>
              </Alert>
              
              {sofContent ? (
                <StatementOfFactsViewer 
                  documentData={sofContent}
                  caseId={caseId}
                />
              ) : (
                <Typography sx={{ color: 'var(--text-secondary)', p: 2 }}>
                  Statement of Facts will be generated from extracted facts and evidence mapping.
                </Typography>
              )}
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => handleApprove('statementOfFacts')}
                  sx={{
                    backgroundColor: approvals.statementOfFacts ? 'var(--neon-green)' : 'var(--neon-cyan)',
                    color: '#000',
                    mr: 1
                  }}
                >
                  {approvals.statementOfFacts ? '✅ Approved' : 'Approve SOF'}
                </Button>
                <Chip 
                  label={approvals.statementOfFacts ? 'Approved' : 'Pending'} 
                  color={approvals.statementOfFacts ? 'success' : 'warning'} 
                />
              </Box>
            </Box>
          )}

          {/* Shotlist Tab */}
          {activeTab === 1 && deliverables && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📊 Chronological Fact Timeline
              </Typography>
              
              <ShotList
                caseId={caseId}
                evidenceData={deliverables.shotlist.data || []}
                onShotUpdate={(updatedShots) => {
                  // Handle updates
                  console.log('Shotlist updated:', updatedShots);
                }}
                editable
                onApprove={() => handleApprove('shotlist')}
              />
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => handleApprove('shotlist')}
                  sx={{
                    backgroundColor: approvals.shotlist ? 'var(--neon-green)' : 'var(--neon-cyan)',
                    color: '#000',
                    mr: 1
                  }}
                >
                  {approvals.shotlist ? '✅ Approved' : 'Approve Shotlist'}
                </Button>
                <Chip label={approvals.shotlist ? 'Approved' : 'Pending'} color={approvals.shotlist ? 'success' : 'warning'} />
              </Box>
            </Box>
          )}

          {/* Claims Matrix Tab */}
          {activeTab === 2 && deliverables && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📋 Legal Claims Analysis
              </Typography>
              
              <ClaimsMatrix
                caseId={caseId}
                onClaimSelect={(claim) => console.log('Claim selected:', claim)}
                onMatrixUpdate={(updatedMatrix) => {
                  console.log('Claims matrix updated:', updatedMatrix);
                }}
                editable
                onApprove={() => handleApprove('claimsMatrix')}
              />
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => handleApprove('claimsMatrix')}
                  sx={{
                    backgroundColor: approvals.claimsMatrix ? 'var(--neon-green)' : 'var(--neon-cyan)',
                    color: '#000',
                    mr: 1
                  }}
                >
                  {approvals.claimsMatrix ? '✅ Approved' : 'Approve Matrix'}
                </Button>
                <Chip label={approvals.claimsMatrix ? 'Approved' : 'Pending'} color={approvals.claimsMatrix ? 'success' : 'warning'} />
              </Box>
            </Box>
          )}

          {/* Skeletal Outline Tab */}
          {activeTab === 3 && deliverables && (
            <Box>
              <Typography variant="h6" sx={{ color: 'var(--neon-cyan)', mb: 2 }}>
                📄 FRCP-Compliant Document Structure
              </Typography>
              
              <SkeletalOutlineSystem
                caseId={caseId}
                claimsMatrix={deliverables.claimsMatrix.data || []}
                shotList={deliverables.shotlist.data || []}
                onOutlineGenerated={(outline) => console.log('Outline generated:', outline)}
                onSectionUpdate={(section) => console.log('Section updated:', section)}
                editable
                onApprove={() => handleApprove('skeletalOutline')}
              />
              
              <Chip label={approvals.skeletalOutline ? 'Approved' : 'Pending'} color={approvals.skeletalOutline ? 'success' : 'warning'} />
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
          border: allApproved ? '2px solid var(--neon-green)' : '2px solid var(--neon-amber)',
          borderRadius: '8px'
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" sx={{ color: '#fff', mb: 1 }}>
              {allApproved ? '✅ All Deliverables Approved' : '⚠️ Approval Required'}
            </Typography>
            <Typography variant="body2" sx={{ color: '#999' }}>
              {allApproved
                ? 'Ready to proceed to Phase B02 - Document Drafting'
                : `${Object.values(approvals).filter(v => v).length} of 4 deliverables approved`}
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
              Cancel
            </Button>

            <Button
              variant="contained"
              disabled={!canProceed}
              onClick={() => onApprove(deliverables)}
              sx={{
                backgroundColor: canProceed ? 'var(--neon-green)' : '#666',
                color: '#fff',
                fontFamily: 'Orbitron, monospace',
                fontSize: '16px',
                px: 4,
                py: 1.5,
                '&:hover': {
                  backgroundColor: canProceed ? 'var(--neon-green-dark)' : '#666'
                },
                '&:disabled': {
                  backgroundColor: '#444',
                  color: '#666'
                }
              }}
            >
              Approve All & Start Drafting
            </Button>
          </Box>
        </Box>

        {/* Validation warnings */}
        {!allValidationsPassed && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Some validations have not passed. Review the validation status above before approving.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

export default PhaseB01Review;
