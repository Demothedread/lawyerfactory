// ProgressBar component for showing progress and loading states
import React from 'react';
import {
  LinearProgress,
  CircularProgress,
  Box,
  Typography,
  Paper,
  Chip,
  Stack
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';

const ProgressBar = ({
  value,
  variant = 'determinate',
  color = 'primary',
  size = 'medium',
  showValue = true,
  label,
  sublabel,
  status,
  height = 8,
  sx = {}
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return color;
    }
  };

  return (
    <Box sx={{ width: '100%', ...sx }}>
      {(label || sublabel) && (
        <Box sx={{ mb: 1 }}>
          {label && (
            <Typography variant="body2" fontWeight="medium" gutterBottom>
              {label}
            </Typography>
          )}
          {sublabel && (
            <Typography variant="caption" color="text.secondary">
              {sublabel}
            </Typography>
          )}
        </Box>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ width: '100%', mr: 1 }}>
          <LinearProgress
            variant={variant}
            value={value}
            color={getStatusColor()}
            sx={{
              height,
              borderRadius: height / 2,
              '& .MuiLinearProgress-bar': {
                borderRadius: height / 2
              }
            }}
          />
        </Box>

        {showValue && variant === 'determinate' && (
          <Typography variant="body2" color="text.secondary" sx={{ minWidth: 35 }}>
            {Math.round(value)}%
          </Typography>
        )}

        {status && getStatusIcon()}
      </Box>
    </Box>
  );
};

// CircularProgressWithLabel component
export const CircularProgressWithLabel = ({
  value,
  size = 40,
  thickness = 3.6,
  color = 'primary',
  showValue = true,
  label,
  sx = {}
}) => {
  return (
    <Box sx={{ position: 'relative', display: 'inline-flex', ...sx }}>
      <CircularProgress
        variant="determinate"
        value={value}
        size={size}
        thickness={thickness}
        color={color}
      />
      {showValue && (
        <Box
          sx={{
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography
            variant="caption"
            component="div"
            color="text.secondary"
            fontWeight="bold"
          >
            {`${Math.round(value)}%`}
          </Typography>
        </Box>
      )}
      {label && (
        <Box sx={{ mt: 1, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {label}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

// StepProgress component for multi-step processes
export const StepProgress = ({
  steps,
  currentStep,
  orientation = 'horizontal',
  size = 'medium',
  showLabels = true,
  sx = {}
}) => {
  const getStepSize = () => {
    switch (size) {
      case 'small':
        return 24;
      case 'large':
        return 40;
      default:
        return 32;
    }
  };

  const stepSize = getStepSize();

  return (
    <Box sx={{ width: '100%', ...sx }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: orientation === 'vertical' ? 'column' : 'row',
          alignItems: 'center',
          gap: orientation === 'vertical' ? 2 : 1
        }}
      >
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          return (
            <Box
              key={index}
              sx={{
                display: 'flex',
                flexDirection: orientation === 'vertical' ? 'row' : 'column',
                alignItems: 'center',
                gap: 1,
                minWidth: orientation === 'vertical' ? 'auto' : stepSize + 40
              }}
            >
              <Box
                sx={{
                  width: stepSize,
                  height: stepSize,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: isCompleted
                    ? 'success.main'
                    : isCurrent
                    ? 'primary.main'
                    : 'grey.300',
                  color: isCompleted || isCurrent ? 'white' : 'text.secondary',
                  fontSize: size === 'small' ? '0.75rem' : '1rem',
                  fontWeight: 'bold',
                  transition: 'all 0.3s ease'
                }}
              >
                {isCompleted ? (
                  <CheckCircleIcon fontSize={size === 'small' ? 'small' : 'medium'} />
                ) : (
                  index + 1
                )}
              </Box>

              {showLabels && (
                <Typography
                  variant={size === 'small' ? 'caption' : 'body2'}
                  sx={{
                    textAlign: 'center',
                    color: isCurrent ? 'primary.main' : isCompleted ? 'success.main' : 'text.secondary',
                    fontWeight: isCurrent ? 'bold' : 'normal',
                    maxWidth: orientation === 'vertical' ? 'auto' : 80
                  }}
                >
                  {step.label}
                </Typography>
              )}

              {index < steps.length - 1 && (
                <Box
                  sx={{
                    width: orientation === 'vertical' ? 2 : '100%',
                    height: orientation === 'vertical' ? '100%' : 2,
                    bgcolor: index < currentStep ? 'success.main' : 'grey.300',
                    flex: orientation === 'vertical' ? 'none' : 1,
                    minHeight: orientation === 'vertical' ? 20 : 'auto',
                    transition: 'background-color 0.3s ease'
                  }}
                />
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

// LoadingOverlay component
export const LoadingOverlay = ({
  open,
  message = 'Loading...',
  size = 'medium',
  backdropColor = 'rgba(255, 255, 255, 0.8)',
  sx = {}
}) => {
  if (!open) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        bgcolor: backdropColor,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        ...sx
      }}
    >
      <CircularProgress size={size === 'large' ? 60 : size === 'small' ? 20 : 40} />
      {message && (
        <Typography variant="body1" sx={{ mt: 2, color: 'text.secondary' }}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default ProgressBar;