import {
    CheckCircle,
    Error as ErrorIcon,
    HourglassEmpty,
    Schedule,
    UploadFile,
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Card,
    CardContent,
    Chip,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';

/**
 * EvidenceUploadQueue Component
 * 
 * Displays animated queue of evidence files being processed
 * Shows classification status, progress, and extracted metadata
 * Real-time updates via WebSocket or polling
 */
const EvidenceUploadQueue = ({
  caseId,
  onQueueStatusUpdate,
  pollingInterval = 2000,
}) => {
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);

  // Fetch queue status
  const fetchQueueStatus = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/evidence/queue/status/${caseId}`
      );
      if (!response.ok) {
        console.error('Failed to fetch queue status');
        return;
      }

      const data = await response.json();
      setQueueItems(data.queue_items || []);
      setTotalCount(data.total || 0);
      setCompletedCount(data.completed || 0);

      if (onQueueStatusUpdate) {
        onQueueStatusUpdate(data);
      }
    } catch (error) {
      console.error('Error fetching queue status:', error);
    }
  }, [caseId, onQueueStatusUpdate]);

  // Setup polling
  useEffect(() => {
    fetchQueueStatus();
    const interval = setInterval(fetchQueueStatus, pollingInterval);
    return () => clearInterval(interval);
  }, [caseId, fetchQueueStatus, pollingInterval]);

  // Get status icon based on item status
  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return <CheckCircle sx={{ color: 'var(--soviet-green)', fontSize: 28 }} />;
      case 'error':
        return <ErrorIcon sx={{ color: 'var(--soviet-red)', fontSize: 28 }} />;
      case 'processing':
        return <HourglassEmpty sx={{ color: 'var(--soviet-brass)', fontSize: 28, animation: 'spin 2s linear infinite' }} />;
      case 'queued':
      default:
        return <Schedule sx={{ color: 'var(--soviet-silver)', fontSize: 28 }} />;
    }
  };

  // Get status color

  // Get classification badge
  const getClassificationBadge = (item) => {
    if (!item.evidence_class) return null;

    const isPrimary = item.evidence_class === 'primary';
    const colors = isPrimary
      ? { bg: 'var(--soviet-green)', text: 'white' }
      : { bg: 'var(--soviet-blue)', text: 'white' };

    return (
      <Chip
        size="small"
        label={`${item.evidence_class.toUpperCase()} - ${item.evidence_type || 'Unclassified'}`}
        sx={{
          backgroundColor: colors.bg,
          color: colors.text,
          fontSize: '0.7rem',
          marginRight: 1,
        }}
      />
    );
  };

  const overallProgress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <Box sx={{ width: '100%', mb: 3 }}>
      <Card
        sx={{
          backgroundColor: 'var(--soviet-panel)',
          border: '2px solid var(--soviet-brass)',
          borderRadius: 2,
        }}
      >
        <CardContent>
          {/* Header */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <UploadFile sx={{ color: 'var(--soviet-brass)', mr: 1, fontSize: 28 }} />
              <Typography
                variant="h6"
                sx={{
                  color: 'var(--soviet-brass)',
                  fontFamily: 'Russo One, monospace',
                  fontWeight: 'bold',
                }}
              >
                📤 Evidence Processing Queue
              </Typography>
            </Box>

            {/* Overall Progress */}
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ color: 'var(--text-secondary)' }}>
                  Overall Progress
                </Typography>
                <Typography variant="body2" sx={{ color: 'var(--soviet-brass)', fontWeight: 'bold' }}>
                  {completedCount}/{totalCount}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={overallProgress}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'var(--soviet-dark)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: 'var(--soviet-green)',
                  },
                }}
              />
            </Box>

            {/* Status Summary */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`⏳ Queued: ${queueItems.length}`}
                size="small"
                sx={{
                  backgroundColor: 'transparent',
                  border: '1px solid var(--soviet-silver)',
                  color: 'var(--soviet-silver)',
                }}
              />
              <Chip
                label={`✓ Completed: ${completedCount}`}
                size="small"
                sx={{
                  backgroundColor: 'transparent',
                  border: '1px solid var(--soviet-green)',
                  color: 'var(--soviet-green)',
                }}
              />
            </Box>
          </Box>

          {/* Queue Items List */}
          {queueItems.length === 0 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              No evidence items in queue. Upload evidence to begin processing.
            </Alert>
          ) : (
            <List sx={{ maxHeight: '600px', overflowY: 'auto' }}>
              {queueItems.map((item) => (
                <ListItem
                  key={item.id}
                  sx={{
                    mb: 1.5,
                    backgroundColor: 'var(--soviet-dark)',
                    borderLeft: `4px solid ${
                      item.status === 'complete'
                        ? 'var(--soviet-green)'
                        : item.status === 'error'
                          ? 'var(--soviet-red)'
                          : 'var(--soviet-brass)'
                    }`,
                    borderRadius: 1,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
                    },
                  }}
                >
                  {/* Status Icon */}
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    {getStatusIcon(item.status)}
                  </ListItemIcon>

                  {/* Content */}
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'var(--soviet-silver)',
                            fontWeight: '600',
                            maxWidth: '300px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {item.filename}
                        </Typography>
                        {getClassificationBadge(item)}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        {/* Progress Bar */}
                        <Box sx={{ mb: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={item.progress || 0}
                            sx={{
                              height: 4,
                              borderRadius: 2,
                              backgroundColor: 'var(--soviet-panel)',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor:
                                  item.status === 'complete'
                                    ? 'var(--soviet-green)'
                                    : item.status === 'error'
                                      ? 'var(--soviet-red)'
                                      : 'var(--soviet-brass)',
                              },
                            }}
                          />
                          <Typography variant="caption" sx={{ color: 'var(--text-secondary)' }}>
                            {item.progress}% - {item.status}
                          </Typography>
                        </Box>

                        {/* Metadata */}
                        {item.extracted_metadata && (
                          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                            {item.extracted_metadata.content_length && (
                              <Typography variant="caption" sx={{ color: 'var(--soviet-silver)' }}>
                                📄 {(item.extracted_metadata.content_length / 1024).toFixed(1)} KB
                              </Typography>
                            )}
                            {item.extracted_metadata.from && (
                              <Typography variant="caption" sx={{ color: 'var(--soviet-silver)' }}>
                                📧 {item.extracted_metadata.from.substring(0, 30)}...
                              </Typography>
                            )}
                            {item.evidence_type && (
                              <Typography variant="caption" sx={{ color: 'var(--soviet-brass)' }}>
                                🏷️ {item.evidence_type}
                              </Typography>
                            )}
                          </Box>
                        )}

                        {/* Error Message */}
                        {item.error_message && (
                          <Typography
                            variant="caption"
                            sx={{ color: 'var(--soviet-red)', display: 'block', mt: 0.5 }}
                          >
                            ❌ Error: {item.error_message}
                          </Typography>
                        )}

                        {/* Summary */}
                        {item.summary && item.status === 'complete' && (
                          <Typography
                            variant="caption"
                            sx={{
                              color: 'var(--text-secondary)',
                              display: 'block',
                              mt: 0.5,
                              maxWidth: '400px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {item.summary.substring(0, 100)}...
                          </Typography>
                        )}
                      </Box>
                    }
                  />

                  {/* Confidence Badge */}
                  {item.classification_confidence && (
                    <Box sx={{ ml: 2, textAlign: 'right' }}>
                      <Chip
                        label={`${(item.classification_confidence * 100).toFixed(0)}%`}
                        size="small"
                        sx={{
                          backgroundColor: 'var(--soviet-brass)',
                          color: 'var(--soviet-dark)',
                          fontWeight: 'bold',
                        }}
                      />
                    </Box>
                  )}
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Animation Styles */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Box>
  );
};

EvidenceUploadQueue.propTypes = {
  caseId: PropTypes.string.isRequired,
  onQueueStatusUpdate: PropTypes.func,
  onItemComplete: PropTypes.func,
  socketEndpoint: PropTypes.string,
  pollingInterval: PropTypes.number,
};

export default EvidenceUploadQueue;
