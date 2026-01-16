// TooltipGuide component for contextual help and guidance
import CloseIcon from '@mui/icons-material/Close';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import {
  Box,
  Button,
  Chip,
  Fade,
  Grow,
  IconButton,
  Paper,
  Popover,
  Tooltip,
  Typography
} from '@mui/material';
import React, { useState } from 'react';

const TooltipGuide = ({
  title,
  content,
  children,
  placement = 'top',
  variant = 'icon',
  size = 'small',
  color = 'primary',
  type = 'info',
  interactive = true,
  showArrow = true,
  maxWidth = 300,
  sx = {}
}) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  const getTypeIcon = () => {
    switch (type) {
      case 'tip':
        return <LightbulbIcon />;
      case 'warning':
        return <WarningAmberIcon />;
      case 'info':
      default:
        return <HelpOutlineIcon />;
    }
  };

  const getTypeColor = () => {
    switch (type) {
      case 'tip':
        return 'warning';
      case 'warning':
        return 'error';
      case 'info':
      default:
        return color;
    }
  };

  if (variant === 'popover') {
    return (
      <>
        <Box onClick={handleClick} sx={{ cursor: 'pointer', ...sx }}>
          {children || (
            <IconButton size={size} color={color}>
              <HelpOutlineIcon fontSize={size} />
            </IconButton>
          )}
        </Box>

        <Popover
          open={open}
          anchorEl={anchorEl}
          onClose={handleClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'center',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'center',
          }}
        >
          <Paper sx={{ p: 2, maxWidth, minWidth: 200 }}>
            {title && (
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {getTypeIcon()}
                <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: 'bold' }}>
                  {title}
                </Typography>
              </Box>
            )}
            <Typography variant="body2" color="text.secondary">
              {content}
            </Typography>
          </Paper>
        </Popover>
      </>
    );
  }

  return (
    <Tooltip
      title={
        <Box sx={{ p: 1 }}>
          {title && (
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              {getTypeIcon()}
              <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: 'bold', color: 'white' }}>
                {title}
              </Typography>
            </Box>
          )}
          <Typography variant="body2" sx={{ color: 'white' }}>
            {content}
          </Typography>
        </Box>
      }
      placement={placement}
      arrow={showArrow}
      interactive={interactive}
      sx={sx}
    >
      {children || (
        <IconButton size={size} color={color}>
          <HelpOutlineIcon fontSize={size} />
        </IconButton>
      )}
    </Tooltip>
  );
};

// GuidedTour component for step-by-step guidance
export const GuidedTour = ({
  steps,
  open,
  onClose,
  currentStep = 0,
  onNext,
  onPrevious,
  onComplete,
  onSkip
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(currentStep);
  const [isClosing, setIsClosing] = useState(false);

  React.useEffect(() => {
    setCurrentStepIndex(currentStep);
  }, [currentStep]);

  React.useEffect(() => {
    if (open) {
      setIsClosing(false);
    }
  }, [open]);

  if (!open || !steps || steps.length === 0) return null;

  const currentStepData = steps[currentStepIndex];

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      const nextIndex = currentStepIndex + 1;
      setCurrentStepIndex(nextIndex);
      if (onNext) onNext(nextIndex);
    } else {
      if (onComplete) onComplete();
      handleClose();
    }
  };

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      const prevIndex = currentStepIndex - 1;
      setCurrentStepIndex(prevIndex);
      if (onPrevious) onPrevious(prevIndex);
    }
  };

  const handleSkip = () => {
    if (onSkip) onSkip();
    handleClose();
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      if (onClose) onClose();
    }, 300); // Match transition duration
  };

  return (
    <Fade in={!isClosing} timeout={300}>
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          bgcolor: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(4px)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
          transition: 'backdrop-filter 0.3s ease'
        }}
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            handleClose();
          }
        }}
      >
        <Grow in={!isClosing} timeout={400}>
          <Paper
            sx={{
              p: 3,
              maxWidth: 500,
              width: '100%',
              position: 'relative',
              boxShadow: 24,
              transition: 'transform 0.3s cubic-bezier(0.23, 1, 0.32, 1)'
            }}
          >
            {/* Close Button */}
            <IconButton
              onClick={handleClose}
              sx={{
                position: 'absolute',
                right: 8,
                top: 8,
                color: 'text.secondary',
                '&:hover': {
                  color: 'error.main',
                  bgcolor: 'error.light',
                  transform: 'scale(1.1)'
                },
                transition: 'all 0.2s ease'
              }}
              aria-label="Close guided tour"
            >
              <CloseIcon />
            </IconButton>

            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, pr: 4 }}>
                <LightbulbIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Guided Tour
                </Typography>
                <Chip
                  label={`${currentStepIndex + 1} of ${steps.length}`}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>

              <Typography variant="h5" gutterBottom>
                {currentStepData.title}
              </Typography>

              <Typography variant="body1" paragraph>
                {currentStepData.content}
              </Typography>

              {currentStepData.image && (
                <Box sx={{ textAlign: 'center', my: 2 }}>
                  <img
                    src={currentStepData.image}
                    alt={currentStepData.title}
                    style={{
                      maxWidth: '100%',
                      maxHeight: 200,
                      borderRadius: 8,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                    }}
                  />
                </Box>
              )}

              {currentStepData.tips && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    💡 Pro Tips:
                  </Typography>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {currentStepData.tips.map((tip, index) => (
                      <li key={index}>
                        <Typography variant="body2">{tip}</Typography>
                      </li>
                    ))}
                  </ul>
                </Box>
              )}
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Button
                  onClick={handleSkip}
                  color="inherit"
                  size="small"
                >
                  Skip Tour
                </Button>
              </Box>

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  onClick={handlePrevious}
                  disabled={currentStepIndex === 0}
                  variant="outlined"
                >
                  Previous
                </Button>
                <Button
                  onClick={handleNext}
                  variant="contained"
                >
                  {currentStepIndex === steps.length - 1 ? 'Finish' : 'Next'}
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grow>
      </Box>
    </Fade>
  );
};

// HelpPanel component for contextual help
export const HelpPanel = ({
  topics,
  defaultTopic,
  position = 'right',
  width = 300,
  sx = {}
}) => {
  const [selectedTopic, setSelectedTopic] = useState(defaultTopic || topics[0]?.id);
  const [isOpen, setIsOpen] = useState(false);

  const selectedTopicData = topics.find(topic => topic.id === selectedTopic);

  const positionStyles = position === 'left'
    ? { left: 0, top: 0, bottom: 0 }
    : { right: 0, top: 0, bottom: 0 };

  return (
    <>
      <IconButton
        onClick={() => setIsOpen(!isOpen)}
        sx={{
          position: 'fixed',
          ...positionStyles,
          zIndex: 1000,
          bgcolor: 'primary.main',
          color: 'white',
          borderRadius: position === 'left' ? '0 8px 8px 0' : '8px 0 0 8px',
          '&:hover': {
            bgcolor: 'primary.dark'
          },
          ...sx
        }}
      >
        <HelpOutlineIcon />
      </IconButton>

      {isOpen && (
        <Paper
          sx={{
            position: 'fixed',
            ...positionStyles,
            width,
            zIndex: 999,
            overflowY: 'auto',
            maxHeight: '100vh'
          }}
        >
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Help & Guidance</Typography>
              <IconButton onClick={() => setIsOpen(false)} size="small">
                <HelpOutlineIcon />
              </IconButton>
            </Box>

            <Box sx={{ mb: 2 }}>
              {topics.map((topic) => (
                <Button
                  key={topic.id}
                  fullWidth
                  variant={selectedTopic === topic.id ? 'contained' : 'outlined'}
                  onClick={() => setSelectedTopic(topic.id)}
                  sx={{ mb: 1, justifyContent: 'flex-start' }}
                >
                  {topic.title}
                </Button>
              ))}
            </Box>

            {selectedTopicData && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  {selectedTopicData.title}
                </Typography>
                <Typography variant="body2" paragraph>
                  {selectedTopicData.content}
                </Typography>

                {selectedTopicData.steps && (
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Steps:
                    </Typography>
                    <ol style={{ paddingLeft: 20 }}>
                      {selectedTopicData.steps.map((step, index) => (
                        <li key={index}>
                          <Typography variant="body2">{step}</Typography>
                        </li>
                      ))}
                    </ol>
                  </Box>
                )}
              </Box>
            )}
          </Box>
        </Paper>
      )}
    </>
  );
};

export default TooltipGuide;