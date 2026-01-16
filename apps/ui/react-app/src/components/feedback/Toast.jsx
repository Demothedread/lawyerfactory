// Toast notification component for user feedback
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import {
  Alert,
  AlertTitle,
  Box,
  Fade,
  Grow,
  IconButton,
  Slide,
  Snackbar
} from '@mui/material';
import { createContext, useContext, useState } from 'react';

// Toast Context
const ToastContext = createContext();

// Toast Provider Component
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = (messageOrToast, options = {}) => {
    const id = Date.now() + Math.random();
    
    // Handle both calling patterns:
    // addToast(message, options) OR addToast({message, ...})
    const toast = typeof messageOrToast === 'string' 
      ? { message: messageOrToast, ...options }
      : messageOrToast;
    
    const newToast = {
      id,
      ...toast,
      open: true
    };
    setToasts(prev => [...prev, newToast]);

    // Auto-hide after duration
    if (toast.autoHideDuration !== 0) {
      setTimeout(() => {
        removeToast(id);
      }, toast.autoHideDuration || 6000);
    }

    return id;
  };

  const removeToast = (id) => {
    setToasts(prev => prev.map(toast =>
      toast.id === id ? { ...toast, open: false } : toast
    ));

    // Remove from state after animation
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, 300);
  };

  const clearAllToasts = () => {
    setToasts(prev => prev.map(toast => ({ ...toast, open: false })));
    setTimeout(() => {
      setToasts([]);
    }, 300);
  };

  const value = {
    toasts,
    addToast,
    removeToast,
    clearAllToasts
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          {...toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </ToastContext.Provider>
  );
};

// Hook to use toast
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

// Individual Toast Component
const Toast = ({
  message,
  title,
  severity = 'info',
  variant = 'filled',
  onClose,
  position = 'bottom-right',
  transition = 'grow',
  open = true,
  sx = {}
}) => {
  // Don't render anything if toast is not open
  if (!open) return null;

  const getSeverityIcon = () => {
    switch (severity) {
      case 'success':
        return <CheckCircleIcon fontSize="small" />;
      case 'error':
        return <ErrorIcon fontSize="small" />;
      case 'warning':
        return <WarningIcon fontSize="small" />;
      case 'info':
        return <InfoIcon fontSize="small" />;
      default:
        return null;
    }
  };

  const getTransitionComponent = () => {
    switch (transition) {
      case 'slide':
        return Slide;
      case 'fade':
        return Fade;
      case 'grow':
      default:
        return Grow;
    }
  };

  const getAnchorOrigin = () => {
    switch (position) {
      case 'top-left':
        return { vertical: 'top', horizontal: 'left' };
      case 'top-center':
        return { vertical: 'top', horizontal: 'center' };
      case 'top-right':
        return { vertical: 'top', horizontal: 'right' };
      case 'bottom-left':
        return { vertical: 'bottom', horizontal: 'left' };
      case 'bottom-center':
        return { vertical: 'bottom', horizontal: 'center' };
      case 'bottom-right':
      default:
        return { vertical: 'bottom', horizontal: 'right' };
    }
  };

  const TransitionComponent = getTransitionComponent();
  const anchorOrigin = getAnchorOrigin();

  const handleClose = (event, reason) => {
    // Prevent closing on clickaway for better UX
    if (reason === 'clickaway') {
      return;
    }
    
    if (onClose) {
      onClose();
    }
  };

  return (
    <Snackbar
      open={open}
      onClose={handleClose}
      anchorOrigin={anchorOrigin}
      TransitionComponent={TransitionComponent}
      sx={{
        '& .MuiSnackbar-root': {
          bottom: position.includes('bottom') ? 24 : 'auto',
          top: position.includes('top') ? 24 : 'auto'
        },
        ...sx
      }}
    >
      <Alert
        severity={severity}
        variant={variant}
        icon={getSeverityIcon()}
        action={
          <IconButton
            size="small"
            color="inherit"
            onClick={(e) => {
              e.stopPropagation();
              handleClose(e, 'closeButton');
            }}
            aria-label="close notification"
            sx={{ 
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
        sx={{
          minWidth: 300,
          maxWidth: 500,
          boxShadow: 3,
          '& .MuiAlert-message': {
            width: '100%'
          }
        }}
      >
        {title && (
          <AlertTitle sx={{ fontWeight: 'bold', mb: 0.5 }}>
            {title}
          </AlertTitle>
        )}
        {message}
      </Alert>
    </Snackbar>
  );
};

// Toast Container for multiple toasts (optional advanced usage)
export const ToastContainer = ({
  position = 'bottom-right',
  maxToasts = 3,
  sx = {}
}) => {
  const { toasts, removeToast } = useToast();

  // Only show the most recent toasts
  const visibleToasts = toasts.slice(-maxToasts);

  return (
    <Box sx={{ position: 'fixed', zIndex: 9999, ...sx }}>
      {visibleToasts.map((toast, index) => (
        <Box
          key={toast.id}
          sx={{
            mb: index < visibleToasts.length - 1 ? 1 : 0,
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <Toast
            {...toast}
            position={position}
            onClose={() => removeToast(toast.id)}
          />
        </Box>
      ))}
    </Box>
  );
};

// Helper component to use toast functions properly
export const useToastHelpers = () => {
  const { addToast } = useToast();

  return {
    success: (message, options = {}) => {
      return addToast({
        message,
        severity: 'success',
        ...options
      });
    },

    error: (message, options = {}) => {
      return addToast({
        message,
        severity: 'error',
        autoHideDuration: 8000,
        ...options
      });
    },

    warning: (message, options = {}) => {
      return addToast({
        message,
        severity: 'warning',
        ...options
      });
    },

    info: (message, options = {}) => {
      return addToast({
        message,
        severity: 'info',
        ...options
      });
    },

    loading: (message, options = {}) => {
      return addToast({
        message,
        severity: 'info',
        autoHideDuration: 0,
        ...options
      });
    }
  };
};

export default Toast;