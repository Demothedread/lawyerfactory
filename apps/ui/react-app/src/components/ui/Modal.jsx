// Modal component for popup dialogs and instructions
import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  Button,
  Divider
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const Modal = ({
  open,
  onClose,
  title,
  children,
  actions,
  maxWidth = 'md',
  fullWidth = true,
  showCloseButton = true,
  helpContent,
  variant = 'default',
  sx = {}
}) => {
  const handleClose = () => {
    if (onClose) onClose();
  };

  const renderTitle = () => {
    if (!title) return null;

    return (
      <DialogTitle sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        pb: 1
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {variant === 'help' && (
            <HelpOutlineIcon sx={{ mr: 1, color: 'primary.main' }} />
          )}
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        {showCloseButton && (
          <IconButton
            onClick={handleClose}
            size="small"
            sx={{ ml: 1 }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>
    );
  };

  const renderContent = () => {
    return (
      <DialogContent sx={{ pt: title ? 0 : 2 }}>
        {helpContent && (
          <Box sx={{ mb: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2" color="info.contrastText">
              {helpContent}
            </Typography>
          </Box>
        )}
        {children}
      </DialogContent>
    );
  };

  const renderActions = () => {
    if (!actions || actions.length === 0) return null;

    return (
      <>
        <Divider />
        <DialogActions sx={{ p: 2 }}>
          {actions.map((action, index) => (
            <Button
              key={index}
              onClick={action.onClick}
              variant={action.variant || 'contained'}
              color={action.color || 'primary'}
              disabled={action.disabled}
              startIcon={action.startIcon}
              endIcon={action.endIcon}
              sx={action.sx}
            >
              {action.label}
            </Button>
          ))}
        </DialogActions>
      </>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={maxWidth}
      fullWidth={fullWidth}
      sx={{
        '& .MuiDialog-paper': {
          borderRadius: 2,
          ...sx
        }
      }}
    >
      {renderTitle()}
      {renderContent()}
      {renderActions()}
    </Dialog>
  );
};

// InstructionModal - specialized modal for step-by-step instructions
export const InstructionModal = ({
  open,
  onClose,
  title,
  steps,
  currentStep = 0,
  onNext,
  onPrevious,
  onComplete
}) => {
  const currentStepData = steps[currentStep];

  const actions = [
    {
      label: 'Previous',
      onClick: onPrevious,
      disabled: currentStep === 0,
      variant: 'outlined'
    },
    {
      label: currentStep === steps.length - 1 ? 'Complete' : 'Next',
      onClick: currentStep === steps.length - 1 ? onComplete : onNext,
      variant: 'contained'
    }
  ];

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      actions={actions}
      maxWidth="lg"
      variant="help"
    >
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Step {currentStep + 1} of {steps.length}
        </Typography>
      </Box>

      {currentStepData && (
        <Box>
          <Typography variant="h6" gutterBottom>
            {currentStepData.title}
          </Typography>
          <Typography variant="body1" paragraph>
            {currentStepData.description}
          </Typography>

          {currentStepData.image && (
            <Box sx={{ textAlign: 'center', my: 2 }}>
              <img
                src={currentStepData.image}
                alt={currentStepData.title}
                style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: 8 }}
              />
            </Box>
          )}

          {currentStepData.tips && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                💡 Tips:
              </Typography>
              <ul>
                {currentStepData.tips.map((tip, index) => (
                  <li key={index}>
                    <Typography variant="body2">{tip}</Typography>
                  </li>
                ))}
              </ul>
            </Box>
          )}
        </Box>
      )}
    </Modal>
  );
};

// ConfirmationModal - specialized modal for confirmations
export const ConfirmationModal = ({
  open,
  onClose,
  title,
  message,
  onConfirm,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  confirmColor = 'primary'
}) => {
  const actions = [
    {
      label: cancelLabel,
      onClick: onClose,
      variant: 'outlined'
    },
    {
      label: confirmLabel,
      onClick: () => {
        onConfirm();
        onClose();
      },
      color: confirmColor,
      variant: 'contained'
    }
  ];

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      actions={actions}
      maxWidth="sm"
    >
      <Typography variant="body1">
        {message}
      </Typography>
    </Modal>
  );
};

export default Modal;