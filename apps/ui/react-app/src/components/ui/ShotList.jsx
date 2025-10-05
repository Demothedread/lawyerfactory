import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import LinkIcon from '@mui/icons-material/Link';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
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

const ShotList = ({
  caseId,
  evidenceData = [],
  onShotUpdate,
  onEvidenceLink}) => {
  const [shots, setShots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingShot, setEditingShot] = useState(null);
  const [newShot, setNewShot] = useState({ fact: '', source: '', entities: '', citations: '' });

  useEffect(() => {
    if (caseId) {
      loadShotList();
    }
  }, [caseId, evidenceData]);

  const loadShotList = async () => {
    setLoading(true);
    try {
      // Generate shot list from evidence data
      const generatedShots = generateShotListFromEvidence(evidenceData);
      setShots(generatedShots);
    } catch (error) {
      console.error('Failed to load shot list:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateShotListFromEvidence = (evidence) => {
    // Convert evidence rows to shot list format
    return evidence.map((item, index) => ({
      id: item.evidence_id || `shot_${index}`,
      fact_id: `F${String(index + 1).padStart(3, '0')}`,
      source_id: item.evidence_id || 'Unknown',
      timestamp: item.uploadDate || new Date().toISOString(),
      summary: item.content?.substring(0, 200) || item.summary || 'Evidence summary',
      entities: extractEntities(item),
      citations: item.page_section || '',
      linked_claims: [],
      status: 'active'
    }));
  };

  const extractEntities = (evidence) => {
    // Mock entity extraction - would use NLP in production
    const entities = [];
    const content = evidence.content || evidence.summary || '';

    // Simple entity extraction patterns
    if (content.includes('contract')) entities.push('Contract');
    if (content.includes('payment')) entities.push('Payment');
    if (content.includes('breach')) entities.push('Breach');
    if (content.includes('damages')) entities.push('Damages');

    return entities;
  };

  const handleAddShot = () => {
    if (newShot.fact.trim()) {
      const shot = {
        id: `shot_${Date.now()}`,
        fact_id: `F${String(shots.length + 1).padStart(3, '0')}`,
        source_id: 'Manual Entry',
        timestamp: new Date().toISOString(),
        summary: newShot.fact,
        entities: newShot.entities.split(',').map(e => e.trim()).filter(e => e),
        citations: newShot.citations,
        linked_claims: [],
        status: 'active'
      };

      setShots([...shots, shot]);
      setNewShot({ fact: '', source: '', entities: '', citations: '' });

      if (onShotUpdate) {
        onShotUpdate([...shots, shot]);
      }
    }
  };

  const handleEditShot = (shot) => {
    setEditingShot(shot);
  };

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

  const handleDeleteShot = (shotId) => {
    const updatedShots = shots.filter(shot => shot.id !== shotId);
    setShots(updatedShots);

    if (onShotUpdate) {
      onShotUpdate(updatedShots);
    }
  };

  const handleLinkToClaim = (shotId, claimId) => {
    const updatedShots = shots.map(shot =>
      shot.id === shotId
        ? { ...shot, linked_claims: [...shot.linked_claims, claimId] }
        : shot
    );
    setShots(updatedShots);

    if (onEvidenceLink) {
      onEvidenceLink(shotId, claimId);
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
        🎯 Shot List - Fact-by-Fact Evidence Organization
      </Typography>

      {/* Add New Shot */}
      <Card sx={{ mb: 3, backgroundColor: 'var(--soviet-panel)', border: '1px solid var(--soviet-brass)' }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ color: 'var(--soviet-silver)', mb: 2 }}>
            Add New Fact to Shot List
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              label="Fact Summary"
              value={newShot.fact}
              onChange={(e) => setNewShot({ ...newShot, fact: e.target.value })}
              sx={{ flex: 1, minWidth: 200 }}
              size="small"
            />
            <TextField
              label="Entities (comma-separated)"
              value={newShot.entities}
              onChange={(e) => setNewShot({ ...newShot, entities: e.target.value })}
              sx={{ minWidth: 150 }}
              size="small"
            />
            <TextField
              label="Citations"
              value={newShot.citations}
              onChange={(e) => setNewShot({ ...newShot, citations: e.target.value })}
              sx={{ minWidth: 120 }}
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
          No facts in shot list. Upload evidence or add facts manually to build your case foundation.
        </Alert>
      ) : (
        <TableContainer component={Paper} sx={{ backgroundColor: 'var(--soviet-panel)', border: '1px solid var(--soviet-brass)' }}>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'var(--soviet-dark)' }}>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>Fact ID</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>Summary</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>Entities</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>Source</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>Linked Claims</TableCell>
                <TableCell sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {shots.map((shot) => (
                <TableRow key={shot.id} sx={{ '&:hover': { backgroundColor: 'var(--soviet-dark)' } }}>
                  <TableCell sx={{ color: 'var(--soviet-silver)', fontFamily: 'monospace' }}>
                    {shot.fact_id}
                  </TableCell>
                  <TableCell sx={{ color: 'var(--soviet-silver)' }}>
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
                      shot.summary
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {shot.entities.map((entity, index) => (
                        <Chip
                          key={index}
                          label={entity}
                          size="small"
                          sx={{
                            backgroundColor: 'var(--soviet-amber)',
                            color: 'var(--soviet-dark)',
                            fontSize: '0.7rem'
                          }}
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ color: 'var(--text-secondary)' }}>
                    {shot.source_id}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {shot.linked_claims.map((claimId, index) => (
                        <Chip
                          key={index}
                          label={claimId}
                          size="small"
                          sx={{
                            backgroundColor: 'var(--soviet-green)',
                            color: 'var(--soviet-dark)',
                            fontSize: '0.7rem'
                          }}
                        />
                      ))}
                      <Tooltip title="Link to Claim">
                        <IconButton
                          size="small"
                          onClick={() => handleLinkToClaim(shot.id, 'claim_001')}
                          sx={{ color: 'var(--soviet-brass)' }}
                        >
                          <LinkIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
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
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <>
                          <Tooltip title="Edit Fact">
                            <IconButton
                              size="small"
                              onClick={() => handleEditShot(shot)}
                              sx={{ color: 'var(--soviet-amber)' }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete Fact">
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
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: 'var(--text-secondary)' }}>
            {shots.length} facts in shot list • {shots.reduce((sum, shot) => sum + shot.linked_claims.length, 0)} claim linkages
          </Typography>
          <Button
            variant="outlined"
            sx={{
              borderColor: 'var(--soviet-brass)',
              color: 'var(--soviet-brass)',
              '&:hover': { borderColor: 'var(--soviet-amber)', color: 'var(--soviet-amber)' }
            }}
          >
            Export Shot List
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default ShotList;