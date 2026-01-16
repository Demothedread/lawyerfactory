import { CloudDownload as Download, Description as FileText, Link as LinkIcon, Search } from '@mui/icons-material';
import { Badge, Box, Button, Card, CardContent, CardHeader, Divider, InputAdornment, TextField, Typography } from '@mui/material';
import { useState } from 'react';

/**
 * StatementOfFactsViewer - React component for viewing generated Statement of Facts
 * Displays the generated statement of facts with fact-evidence mapping and interactive features
 */
const StatementOfFactsViewer = ({ documentData, onFactClick, onDownload }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedFacts, setHighlightedFacts] = useState(new Set());

  // Parse document data if it's a string
  const parsedData = typeof documentData === 'string' ? JSON.parse(documentData) : documentData;

  const {
    content = '',
    facts = [],
    evidence_mapping = {},
    metadata = {}
  } = parsedData || {};

  // Filter facts based on search term
  const filteredFacts = facts.filter(fact =>
    fact.text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    fact.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle fact highlighting
  const handleFactClick = (factId) => {
    const newHighlighted = new Set(highlightedFacts);
    if (newHighlighted.has(factId)) {
      newHighlighted.delete(factId);
    } else {
      newHighlighted.add(factId);
    }
    setHighlightedFacts(newHighlighted);

    if (onFactClick) {
      onFactClick(factId, evidence_mapping[factId]);
    }
  };

  // Render fact with highlighting
  const renderFact = (fact) => {
    const isHighlighted = highlightedFacts.has(fact.id);
    return (
      <Box
        key={fact.id}
        sx={{
          p: 1.5,
          border: 1,
          borderColor: isHighlighted ? 'primary.main' : 'divider',
          borderRadius: 2,
          cursor: 'pointer',
          transition: 'all 0.2s',
          bgcolor: isHighlighted ? 'primary.light' : 'transparent',
          '&:hover': { bgcolor: isHighlighted ? 'primary.light' : 'grey.50' }
        }}
        onClick={() => handleFactClick(fact.id)}
      >
        <Box sx={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', mb: 1 }}>
          <Badge badgeContent={fact.category || 'Fact'} color="default" sx={{ '& .MuiBadge-badge': { position: 'static', transform: 'none', fontSize: '0.75rem' } }} />
          {evidence_mapping[fact.id] && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <LinkIcon sx={{ width: 12, height: 12 }} />
              <Typography variant="caption">Evidence Linked</Typography>
            </Box>
          )}
        </Box>
        <Typography variant="body2" color="text.primary">{fact.text}</Typography>
        {fact.source && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>Source: {fact.source}</Typography>
        )}
      </Box>
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
              <Typography variant="h6">Statement of Facts</Typography>
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
        {/* Search Bar */}
        <TextField
          fullWidth
          size="small"
          placeholder="Search facts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search sx={{ width: 16, height: 16, color: 'text.secondary' }} />
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 2, height: 384 }}>
          {/* Facts List */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 500, color: 'text.primary', mb: 1 }}>
              Key Facts ({filteredFacts.length})
            </Typography>
            <Box sx={{ height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 1, pr: 1 }}>
              {filteredFacts.length > 0 ? (
                filteredFacts.map(renderFact)
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  {searchTerm ? 'No facts match your search.' : 'No facts available.'}
                </Typography>
              )}
            </Box>
          </Box>

          {/* Document Content */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 500, color: 'text.primary', mb: 1 }}>
              Document Content
            </Typography>
            <Box sx={{ height: '100%', overflowY: 'auto', pr: 1 }}>
              {content ? (
                <Box>
                  {content.split('\n').map((paragraph, index) => (
                    <Typography key={index} variant="body2" sx={{ mb: 1.5, lineHeight: 1.6 }}>
                      {paragraph}
                    </Typography>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No document content available.
                </Typography>
              )}
            </Box>
          </Box>
        </Box>

        {/* Statistics */}
        <Divider />
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">Total Facts: {facts.length}</Typography>
          <Typography variant="caption" color="text.secondary">Evidence Links: {Object.keys(evidence_mapping).length}</Typography>
          <Typography variant="caption" color="text.secondary">Highlighted: {highlightedFacts.size}</Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatementOfFactsViewer;