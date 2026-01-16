import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SortIcon from '@mui/icons-material/Sort';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import { useEffect, useState } from 'react';

/**
 * Enhanced ShotList Component
 * 
 * Integrates LLM-powered fact extraction from user's intake narrative and vectorized evidence.
 * Features:
 * - Chronological fact ordering (who/what/when/where/why)
 * - Evidence mapping and citation generation
 * - Rule 12(b)(6) compliance indicators
 * - Integration with Claims Matrix and Statement of Facts
 */
const ShotList = ({
  caseId,
  evidenceData = [],
  userNarrative = "",
  intakeData = {},
  onShotUpdate,
  onEvidenceLink,
  onStatementOfFactsReady
}) => {
  const [shots, setShots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingShot, setEditingShot] = useState(null);
  const [newShot, setNewShot] = useState({ fact: '', source: '', entities: '', citations: '' });
  const [extractedFacts, setExtractedFacts] = useState([]);
  const [chronologicalOrder, setChronologicalOrder] = useState(true);
  const [sofDialogOpen, setSofDialogOpen] = useState(false);
  const [sofContent, setSofContent] = useState("");
  const [rule12b6Status, setRule12b6Status] = useState(null);

  useEffect(() => {
    if (caseId) {
      if (userNarrative && userNarrative.trim().length > 20) {
        // Use LLM-powered fact extraction if narrative provided
        loadFactsFromLLM();
      } else if (evidenceData.length > 0) {
        // Fallback to evidence-based generation
        generateShotListFromEvidence(evidenceData);
      }
    }
  }, [caseId, userNarrative, evidenceData]);

  /**
   * Load facts using LLM fact extraction from narrative + evidence
   */
  const loadFactsFromLLM = async () => {
    setLoading(true);
    try {
      console.log(`🧠 Extracting facts from narrative: ${userNarrative.substring(0, 50)}...`);
      
      // Call backend fact extraction API
      const response = await fetch('/api/facts/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          narrative: userNarrative,
          evidence: evidenceData.map(e => ({
            filename: e.filename || e.name,
            content: e.content || e.text || e.summary,
            source: e.source,
            id: e.evidence_id || e.id
          }))
        })
      });

      const data = await response.json();

      if (data.success && data.facts && data.facts.length > 0) {
        setExtractedFacts(data.facts);
        console.log(`✅ Extracted ${data.facts.length} facts`);
        
        // Convert to shot format
        const shotList = data.facts.map((fact, idx) => ({
          id: fact.id || `shot_${idx}`,
          fact_id: `F${String(idx + 1).padStart(3, '0')}`,
          source_id: fact.supporting_evidence?.[0] || 'Extracted',
          timestamp: new Date().toISOString(),
          summary: fact.fact_text,
          date: fact.date,
          entities: {
            people: fact.entities?.people || [],
            places: fact.entities?.places || [],
            organizations: fact.entities?.organizations || [],
            dates: fact.entities?.dates || []
          },
          citations: fact.supporting_evidence || [],
          linked_claims: [],
          status: 'active',
          favorableToClient: fact.favorable_to_client !== false,
          chronologicalOrder: fact.chronological_order || idx,
          rule12b6Elements: {
            hasWho: fact.fact_text.toLowerCase().includes(intakeData.user_name?.toLowerCase() || 'plaintiff') || 
                    fact.fact_text.toLowerCase().includes(intakeData.other_party_name?.toLowerCase() || 'defendant'),
            hasWhat: /did|agreed|breached|caused|failed|promised|violated/i.test(fact.fact_text),
            hasWhen: /on|date|time|when|after|before|during|month|year/i.test(fact.fact_text),
            hasWhere: fact.fact_text.toLowerCase().includes(intakeData.event_location?.toLowerCase() || '')
          }
        }));

        setShots(shotList);
        
        // Validate Rule 12(b)(6) compliance
        await validateRule12b6Compliance(shotList);
        
        // Generate and save Statement of Facts
        await generateStatementOfFacts(data.facts);
      }
    } catch (error) {
      console.error('❌ Error loading LLM facts:', error);
      // Fallback to evidence-based generation
      if (evidenceData.length > 0) {
        generateShotListFromEvidence(evidenceData);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Generate Statement of Facts document
   */
  const generateStatementOfFacts = async (facts) => {
    try {
      const response = await fetch('/api/statement-of-facts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          facts: facts,
          intake_data: intakeData
        })
      });

      const data = await response.json();

      if (data.success) {
        setSofContent(data.statement_of_facts);
        console.log(`✅ Statement of Facts generated: ${data.word_count} words, Rule 12(b)(6) compliant: ${data.rule_12b6_compliant}`);
        
        // Notify parent component
        if (onStatementOfFactsReady) {
          onStatementOfFactsReady({
            content: data.statement_of_facts,
            wordCount: data.word_count,
            factCount: facts.length,
            rule12b6Compliant: data.rule_12b6_compliant
          });
        }
      }
    } catch (error) {
      console.error('❌ Error generating Statement of Facts:', error);
    }
  };

  /**
   * Validate Rule 12(b)(6) compliance
   */
  const validateRule12b6Compliance = async (shots) => {
    try {
      const response = await fetch('/api/facts/validate-12b6', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          facts: extractedFacts
        })
      });

      const validation = await response.json();
      setRule12b6Status(validation);
      
      console.log(`📋 Rule 12(b)(6) Compliance:`, validation);
    } catch (error) {
      console.error('Error validating Rule 12(b)(6):', error);
    }
  };

  /**
   * Generate shot list from evidence (fallback method)
   */
  const generateShotListFromEvidence = (evidence) => {
    const newShots = evidence.slice(0, 20).map((item, idx) => ({
      id: item.id || item.evidence_id || `shot_${idx}`,
      fact_id: `F${String(idx + 1).padStart(3, '0')}`,
      source_id: item.source || item.filename || 'Evidence',
      timestamp: item.uploadDate || new Date().toISOString(),
      summary: item.content?.substring(0, 200) || item.summary || item.filename || 'Evidence summary',
      date: item.date || 'To be determined',
      entities: {
        people: extractEntitiesFromText(item.content || item.summary, 'people'),
        places: extractEntitiesFromText(item.content || item.summary, 'places'),
        organizations: [],
        dates: []
      },
      citations: [item.filename || item.source || `Evidence ${idx + 1}`],
      linked_claims: [],
      status: 'active',
      favorableToClient: true,
      chronologicalOrder: idx,
      rule12b6Elements: {
        hasWho: true,
        hasWhat: true,
        hasWhen: !!item.date,
        hasWhere: true
      }
    }));
    
    setShots(newShots);
  };

  /**
   * Extract entities from text content
   */
  const extractEntitiesFromText = (text, type) => {
    if (!text) return [];
    
    const entities = [];
    
    if (type === 'people') {
      // Simple pattern: capitalized words that could be names
      const matches = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g) || [];
      return [...new Set(matches)].slice(0, 5);
    }
    
    if (type === 'places') {
      // Look for location keywords
      const keywords = ['located', 'in', 'at', 'district', 'county', 'state'];
      if (keywords.some(kw => text.toLowerCase().includes(kw))) {
        const matches = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g) || [];
        return [...new Set(matches)].slice(0, 3);
      }
    }
    
    return entities;
  };

  /**
   * Handle adding new shot manually
   */
  const handleAddShot = () => {
    if (newShot.fact.trim()) {
      const shot = {
        id: `shot_${Date.now()}`,
        fact_id: `F${String(shots.length + 1).padStart(3, '0')}`,
        source_id: newShot.source || 'Manual Entry',
        timestamp: new Date().toISOString(),
        summary: newShot.fact,
        date: 'To be determined',
        entities: {
          people: newShot.entities.split(',').map(e => e.trim()).filter(e => e),
          places: [],
          organizations: [],
          dates: []
        },
        citations: newShot.citations ? [newShot.citations] : [],
        linked_claims: [],
        status: 'active',
        favorableToClient: true,
        chronologicalOrder: shots.length + 1
      };

      const updatedShots = [...shots, shot];
      setShots(updatedShots);
      setNewShot({ fact: '', source: '', entities: '', citations: '' });

      if (onShotUpdate) {
        onShotUpdate(updatedShots);
      }
    }
  };

  /**
   * Handle editing a shot
   */
  const handleEditShot = (shot) => {
    setEditingShot(shot);
  };

  /**
   * Handle saving edited shot
   */
  const handleSaveEdit = (updatedShot) => {
    const updatedShots = shots.map(shot =>
      shot.id === updatedShot.id ? updatedShot : shot
    );
    setShots(updatedShots);
    setEditingShot(null);

    if (onShotUpdate) {
      onShotUpdate(updatedShots);
    }
  };

  /**
   * Handle deleting a shot
   */
  const handleDeleteShot = (shotId) => {
    const updatedShots = shots.filter(shot => shot.id !== shotId);
    setShots(updatedShots);

    if (onShotUpdate) {
      onShotUpdate(updatedShots);
    }
  };

  /**
   * Link fact to claim
   */
  const handleLinkToClaim = (shotId, claimId) => {
    const updatedShots = shots.map(shot =>
      shot.id === shotId
        ? { ...shot, linked_claims: [...new Set([...shot.linked_claims, claimId])] }
        : shot
    );
    setShots(updatedShots);

    if (onEvidenceLink) {
      onEvidenceLink(shotId, claimId);
    }
  };

  /**
   * Toggle chronological ordering
   */
  const handleToggleChronological = () => {
    if (chronologicalOrder) {
      const sorted = [...shots].sort((a, b) => a.chronologicalOrder - b.chronologicalOrder);
      setShots(sorted);
    } else {
      // Reset to original order
      setShots([...shots]);
    }
    setChronologicalOrder(!chronologicalOrder);
  };

  /**
   * Show Statement of Facts dialog
   */
  const handleViewStatementOfFacts = () => {
    setSofDialogOpen(true);
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress sx={{ color: 'var(--soviet-brass)' }} />
        <Typography sx={{ mt: 2, color: 'var(--soviet-silver)' }}>
          🧠 Analyzing narrative & evidence to extract pertinent facts...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ color: 'var(--soviet-brass)' }}>
          🎯 Shot List - Chronological Facts (LLM-Extracted)
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Sort by chronological order">
            <IconButton 
              onClick={handleToggleChronological}
              sx={{ color: 'var(--soviet-brass)' }}
            >
              <SortIcon />
            </IconButton>
          </Tooltip>
          {sofContent && (
            <Button
              variant="outlined"
              size="small"
              onClick={handleViewStatementOfFacts}
              sx={{
                borderColor: 'var(--soviet-brass)',
                color: 'var(--soviet-brass)',
                '&:hover': { borderColor: 'var(--soviet-amber)' }
              }}
            >
              📄 View Statement of Facts
            </Button>
          )}
        </Box>
      </Box>

      {/* Rule 12(b)(6) Compliance Status */}
      {rule12b6Status && (
        <Alert 
          severity={rule12b6Status.compliant ? "success" : "warning"}
          sx={{ mb: 2 }}
        >
          <strong>Rule 12(b)(6) Status:</strong> {rule12b6Status.compliant ? '✅ Compliant' : '⚠️ Review Required'}
          {rule12b6Status.warnings && rule12b6Status.warnings.length > 0 && (
            <Box sx={{ mt: 1, fontSize: '0.9rem' }}>
              {rule12b6Status.warnings.map((w, idx) => (
                <div key={idx}>• {w}</div>
              ))}
            </Box>
          )}
        </Alert>
      )}

      {/* Add New Shot */}
      <Card sx={{ mb: 3, backgroundColor: 'var(--soviet-panel)', border: '1px solid var(--soviet-brass)' }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ color: 'var(--soviet-silver)', mb: 2 }}>
            ➕ Add Additional Fact to Shot List
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              label="Fact Summary"
              value={newShot.fact}
              onChange={(e) => setNewShot({ ...newShot, fact: e.target.value })}
              placeholder="State the fact clearly and objectively"
              sx={{ flex: 1, minWidth: 250 }}
              size="small"
            />
            <TextField
              label="Entities (comma-separated)"
              value={newShot.entities}
              onChange={(e) => setNewShot({ ...newShot, entities: e.target.value })}
              placeholder="e.g., John Smith, ABC Corp"
              sx={{ minWidth: 150 }}
              size="small"
            />
            <TextField
              label="Source/Citation"
              value={newShot.citations}
              onChange={(e) => setNewShot({ ...newShot, citations: e.target.value })}
              placeholder="Document name or exhibit"
              sx={{ minWidth: 150 }}
              size="small"
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddShot}
              sx={{
                backgroundColor: 'var(--soviet-green)',
                '&:hover': { backgroundColor: 'var(--soviet-green-dark)' }
              }}
            >
              Add Fact
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Shot List Table */}
      {shots.length === 0 ? (
        <Alert severity="info">
          No facts extracted. Upload evidence or provide case narrative to generate shot list.
        </Alert>
      ) : (
        <TableContainer component={Paper} sx={{ backgroundColor: 'var(--soviet-panel)', border: '1px solid var(--soviet-brass)', maxHeight: '600px', overflow: 'auto' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'var(--soviet-dark)' }}>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold', width: '60px' }}>ID</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold', minWidth: '250px' }}>Fact Summary</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold', width: '100px' }}>Date</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold', minWidth: '120px' }}>Entities</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold', width: '80px' }}>12(b)(6)</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold', width: '100px' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {shots.map((shot) => (
                <TableRow key={shot.id} sx={{ '&:hover': { backgroundColor: 'var(--soviet-dark)' } }}>
                  <TableCell sx={{ color: 'var(--soviet-silver)', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {shot.fact_id}
                  </TableCell>
                  <TableCell sx={{ color: 'var(--soviet-silver)', fontSize: '0.9rem' }}>
                    {editingShot?.id === shot.id ? (
                      <TextField
                        fullWidth
                        multiline
                        rows={2}
                        value={editingShot.summary}
                        onChange={(e) => setEditingShot({ ...editingShot, summary: e.target.value })}
                        size="small"
                      />
                    ) : (
                      <>
                        {shot.summary}
                        {shot.favorableToClient && (
                          <Chip label="⭐ Favorable" size="small" sx={{ ml: 1, backgroundColor: 'var(--soviet-green)', color: 'white', fontSize: '0.7rem' }} />
                        )}
                      </>
                    )}
                  </TableCell>
                  <TableCell sx={{ color: 'var(--soviet-silver)', fontSize: '0.85rem' }}>
                    {shot.date !== 'To be determined' ? shot.date : '—'}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {shot.entities.people.length > 0 && (
                        <Chip
                          label={`👤 ${shot.entities.people[0]}`}
                          size="small"
                          sx={{ backgroundColor: 'var(--soviet-amber)', color: 'var(--soviet-dark)', fontSize: '0.7rem' }}
                        />
                      )}
                      {shot.entities.places.length > 0 && (
                        <Chip
                          label={`📍 ${shot.entities.places[0]}`}
                          size="small"
                          sx={{ backgroundColor: 'var(--soviet-cyan)', color: 'var(--soviet-dark)', fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.85rem' }}>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {shot.rule12b6Elements.hasWho && <Tooltip title="WHO"><span>👤</span></Tooltip>}
                      {shot.rule12b6Elements.hasWhat && <Tooltip title="WHAT"><span>✍️</span></Tooltip>}
                      {shot.rule12b6Elements.hasWhen && <Tooltip title="WHEN"><span>📅</span></Tooltip>}
                      {shot.rule12b6Elements.hasWhere && <Tooltip title="WHERE"><span>📍</span></Tooltip>}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {editingShot?.id === shot.id ? (
                        <>
                          <Button
                            size="small"
                            variant="contained"
                            onClick={() => handleSaveEdit(editingShot)}
                            sx={{
                              backgroundColor: 'var(--soviet-green)',
                              fontSize: '0.7rem',
                              minWidth: 'auto',
                              px: 1
                            }}
                          >
                            Save
                          </Button>
                          <Button
                            size="small"
                            onClick={() => setEditingShot(null)}
                            sx={{
                              color: 'var(--soviet-silver)',
                              fontSize: '0.7rem',
                              minWidth: 'auto',
                              px: 1
                            }}
                          >
                            ✕
                          </Button>
                        </>
                      ) : (
                        <>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => handleEditShot(shot)}
                              sx={{ color: 'var(--soviet-amber)' }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteShot(shot.id)}
                              sx={{ color: 'var(--soviet-red)' }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {shots.length > 0 && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, backgroundColor: 'var(--soviet-panel)', border: '1px solid var(--soviet-brass)', borderRadius: '4px' }}>
          <Box>
            <Typography variant="body2" sx={{ color: 'var(--text-secondary)' }}>
              <strong>{shots.length}</strong> facts • <strong>{shots.reduce((sum, shot) => sum + shot.linked_claims.length, 0)}</strong> claim linkages
            </Typography>
            <Typography variant="caption" sx={{ color: 'var(--text-secondary)' }}>
              {shots.filter(s => s.favorableToClient).length} facts favorable to client
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {sofContent && (
              <Button
                variant="outlined"
                sx={{
                  borderColor: 'var(--soviet-brass)',
                  color: 'var(--soviet-brass)',
                  '&:hover': { borderColor: 'var(--soviet-amber)' }
                }}
                onClick={handleViewStatementOfFacts}
              >
                📄 Statement of Facts ({sofContent.split('\n').length} paragraphs)
              </Button>
            )}
          </Box>
        </Box>
      )}

      {/* Statement of Facts Dialog */}
      <Dialog open={sofDialogOpen} onClose={() => setSofDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          📄 Statement of Facts (Rule 12(b)(6) Compliant)
        </DialogTitle>
        <DialogContent dividers>
          <Typography 
            component="pre"
            sx={{ 
              fontFamily: 'Georgia, serif',
              fontSize: '0.95rem',
              lineHeight: 1.8,
              whiteSpace: 'pre-wrap',
              color: 'var(--soviet-silver)'
            }}
          >
            {sofContent}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSofDialogOpen(false)}>Close</Button>
          <Button variant="contained" sx={{ backgroundColor: 'var(--soviet-green)' }}>
            💾 Download
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ShotList;
