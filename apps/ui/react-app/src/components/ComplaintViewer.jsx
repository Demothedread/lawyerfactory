import {
    Error as AlertCircle,
    CheckCircle,
    ExpandMore as ChevronDown,
    ChevronRight,
    CloudDownload as Download,
    Edit,
    Description as FileText
} from '@mui/icons-material';
import { Badge, Box, Button, Card, CardContent, CardHeader, Collapse, Divider, IconButton, Paper, Typography } from '@mui/material';
import { useState } from 'react';

/**
 * ComplaintViewer - React component for viewing generated Complaint document
 * Displays the generated complaint with expandable causes of action, citations, and interactive features
 */
const ComplaintViewer = ({ documentData, onSectionEdit, onDownload, onValidate }) => {
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [validationStatus, setValidationStatus] = useState({});

  // Parse document data if it's a string
  const parsedData = typeof documentData === 'string' ? JSON.parse(documentData) : documentData;

  const {
    content = '',
    causes_of_action = [],
    citations = [],
    parties = {},
    metadata = {}
  } = parsedData || {};

  // Toggle section expansion
  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  // Handle section editing
  const handleSectionEdit = (sectionId, content) => {
    if (onSectionEdit) {
      onSectionEdit(sectionId, content);
    }
  };

  // Handle citation validation
  const handleValidateCitation = async (citationId) => {
    if (onValidate) {
      try {
        const result = await onValidate(citationId);
        setValidationStatus(prev => ({
          ...prev,
          [citationId]: result.valid ? 'valid' : 'invalid'
        }));
      } catch (error) {
        setValidationStatus(prev => ({
          ...prev,
          [citationId]: 'error'
        }));
      }
    }
  };

  // Render cause of action section
  const renderCauseOfAction = (coa, index) => {
    const sectionId = `coa-${index}`;
    const isExpanded = expandedSections.has(sectionId);

    return (
      <Paper key={sectionId} sx={{ border: 1, borderColor: 'divider', borderRadius: 2, mb: 1 }}>
        <Box
          sx={{ 
            width: '100%', 
            p: 2, 
            cursor: 'pointer', 
            '&:hover': { bgcolor: 'grey.50' }, 
            transition: 'background-color 0.2s' 
          }}
          onClick={() => toggleSection(sectionId)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              {isExpanded ? (
                <ChevronDown sx={{ width: 16, height: 16, color: 'text.secondary' }} />
              ) : (
                <ChevronRight sx={{ width: 16, height: 16, color: 'text.secondary' }} />
              )}
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                  {coa.title || `Cause of Action ${index + 1}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {coa.description || 'Legal claim details'}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {coa.citations && coa.citations.length > 0 && (
                <Badge badgeContent={coa.citations.length} color="primary" sx={{ '& .MuiBadge-badge': { fontSize: '0.75rem' } }}>
                  <Typography variant="caption">citations</Typography>
                </Badge>
              )}
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleSectionEdit(sectionId, coa.content);
                }}
              >
                <Edit sx={{ width: 12, height: 12 }} />
              </IconButton>
            </Box>
          </Box>
        </Box>

        <Collapse in={isExpanded}>
          <Box sx={{ px: 2, pb: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {/* IRAC Structure */}
            {coa.irac && (
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 1.5 }}>
                {coa.irac.issue && (
                  <Box sx={{ bgcolor: '#e3f2fd', p: 1.5, borderRadius: 1, borderLeft: 4, borderColor: '#42a5f5' }}>
                    <Typography variant="caption" sx={{ fontWeight: 500, color: '#1565c0', display: 'block', mb: 0.5 }}>ISSUE</Typography>
                    <Typography variant="body2" sx={{ color: '#1976d2' }}>{coa.irac.issue}</Typography>
                  </Box>
                )}
                {coa.irac.rule && (
                  <Box sx={{ bgcolor: '#e8f5e9', p: 1.5, borderRadius: 1, borderLeft: 4, borderColor: '#66bb6a' }}>
                    <Typography variant="caption" sx={{ fontWeight: 500, color: '#2e7d32', display: 'block', mb: 0.5 }}>RULE</Typography>
                    <Typography variant="body2" sx={{ color: '#388e3c' }}>{coa.irac.rule}</Typography>
                  </Box>
                )}
                {coa.irac.application && (
                  <Box sx={{ bgcolor: '#fff9c4', p: 1.5, borderRadius: 1, borderLeft: 4, borderColor: '#ffeb3b' }}>
                    <Typography variant="caption" sx={{ fontWeight: 500, color: '#f57f17', display: 'block', mb: 0.5 }}>APPLICATION</Typography>
                    <Typography variant="body2" sx={{ color: '#f9a825' }}>{coa.irac.application}</Typography>
                  </Box>
                )}
                {coa.irac.conclusion && (
                  <Box sx={{ bgcolor: '#f3e5f5', p: 1.5, borderRadius: 1, borderLeft: 4, borderColor: '#ab47bc' }}>
                    <Typography variant="caption" sx={{ fontWeight: 500, color: '#6a1b9a', display: 'block', mb: 0.5 }}>CONCLUSION</Typography>
                    <Typography variant="body2" sx={{ color: '#7b1fa2' }}>{coa.irac.conclusion}</Typography>
                  </Box>
                )}
              </Box>
            )}

            {/* Citations */}
            {coa.citations && coa.citations.length > 0 && (
              <Box>
                <Typography variant="caption" sx={{ fontWeight: 500, color: 'text.primary', display: 'block', mb: 1 }}>CITATIONS</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {coa.citations.map((citation, citIndex) => (
                    <Box key={citIndex} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{citation.text}</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {validationStatus[citation.id] === 'valid' && (
                          <CheckCircle sx={{ width: 16, height: 16, color: 'success.main' }} />
                        )}
                        {validationStatus[citation.id] === 'invalid' && (
                          <AlertCircle sx={{ width: 16, height: 16, color: 'error.main' }} />
                        )}
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => handleValidateCitation(citation.id)}
                        >
                          Validate
                        </Button>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}

            {/* Full Content */}
            {coa.content && (
              <Box>
                <Typography variant="caption" sx={{ fontWeight: 500, color: 'text.primary', display: 'block', mb: 1 }}>FULL CONTENT</Typography>
                <Box sx={{ bgcolor: 'grey.50', p: 1.5, borderRadius: 1 }}>
                  <Typography variant="body2" sx={{ lineHeight: 1.6, m: 0 }}>{coa.content}</Typography>
                </Box>
              </Box>
            )}
          </Box>
        </Collapse>
      </Paper>
    );
  };

  return (
    <Card sx={{ width: '100%', height: '100%' }}>
      <CardHeader 
        sx={{ pb: 1.5 }}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FileText sx={{ width: 20, height: 20 }} />
              <Typography variant="h6">Complaint Document</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={onDownload}
                disabled={!content}
                startIcon={<Download sx={{ width: 16, height: 16 }} />}
              >
                Download
              </Button>
            </Box>
          </Box>
        }
        subheader={
          metadata.generated_at && (
            <Typography variant="caption" color="text.secondary">
              Generated: {new Date(metadata.generated_at).toLocaleString()}
            </Typography>
          )
        }
      />

      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Parties Information */}
        {parties && Object.keys(parties).length > 0 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
            {parties.plaintiff && (
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 500, color: 'text.primary', mb: 0.5 }}>Plaintiff</Typography>
                <Typography variant="body2">{parties.plaintiff}</Typography>
              </Box>
            )}
            {parties.defendant && (
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 500, color: 'text.primary', mb: 0.5 }}>Defendant</Typography>
                <Typography variant="body2">{parties.defendant}</Typography>
              </Box>
            )}
          </Box>
        )}

        {/* Causes of Action */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 500, color: 'text.primary' }}>
            Causes of Action ({causes_of_action.length})
          </Typography>
          {causes_of_action.length > 0 ? (
            causes_of_action.map(renderCauseOfAction)
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
              No causes of action available.
            </Typography>
          )}
        </Box>

        {/* Full Document Content */}
        {content && (
          <>
            <Divider />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 500, color: 'text.primary' }}>Full Document</Typography>
              <Box sx={{ maxHeight: 256, overflowY: 'auto', pr: 1 }}>
                <Box>
                  {content.split('\n\n').map((paragraph, index) => (
                    <Typography key={index} variant="body2" sx={{ mb: 1.5, lineHeight: 1.6 }}>
                      {paragraph}
                    </Typography>
                  ))}
                </Box>
              </Box>
            </Box>
          </>
        )}

        {/* Statistics */}
        <Divider />
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Causes of Action: {causes_of_action.length}</Typography>
          <Typography variant="caption" color="text.secondary">Total Citations: {citations.length}</Typography>
          <Typography variant="caption" color="text.secondary">Validated: {Object.values(validationStatus).filter(s => s === 'valid').length}</Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ComplaintViewer;