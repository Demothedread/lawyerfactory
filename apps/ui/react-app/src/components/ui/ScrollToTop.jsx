// ScrollToTop component for smooth scrolling to top of page
import React, { useState, useEffect } from 'react';
import { Fab, Box, useScrollTrigger, Zoom, Tooltip } from '@mui/material';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { animateScroll as scroll } from 'react-scroll';

const ScrollToTop = ({
  threshold = 100,
  size = 'medium',
  color = 'primary',
  position = 'bottom-right',
  tooltip = 'Scroll to top',
  smooth = true,
  duration = 500
}) => {
  const [visible, setVisible] = useState(false);

  // Handle scroll visibility
  useEffect(() => {
    const handleScroll = () => {
      const scrolled = window.scrollY;
      setVisible(scrolled > threshold);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [threshold]);

  const handleClick = () => {
    if (smooth) {
      scroll.scrollToTop({
        duration,
        smooth: 'easeInOutQuart'
      });
    } else {
      window.scrollTo({ top: 0, behavior: 'auto' });
    }
  };

  const getPositionStyles = () => {
    const baseStyles = {
      position: 'fixed',
      zIndex: 1000
    };

    switch (position) {
      case 'bottom-right':
        return {
          ...baseStyles,
          bottom: 16,
          right: 16
        };
      case 'bottom-left':
        return {
          ...baseStyles,
          bottom: 16,
          left: 16
        };
      case 'top-right':
        return {
          ...baseStyles,
          top: 16,
          right: 16
        };
      case 'top-left':
        return {
          ...baseStyles,
          top: 16,
          left: 16
        };
      default:
        return {
          ...baseStyles,
          bottom: 16,
          right: 16
        };
    }
  };

  return (
    <Zoom in={visible}>
      <Box sx={getPositionStyles()}>
        <Tooltip title={tooltip} placement="left">
          <Fab
            color={color}
            size={size}
            onClick={handleClick}
            sx={{
              boxShadow: 3,
              '&:hover': {
                boxShadow: 6,
                transform: 'scale(1.1)'
              },
              transition: 'all 0.3s ease'
            }}
          >
            <KeyboardArrowUpIcon />
          </Fab>
        </Tooltip>
      </Box>
    </Zoom>
  );
};

// ScrollProgress component to show reading progress
export const ScrollProgress = ({
  height = 4,
  color = 'primary.main',
  position = 'top',
  showPercentage = false
}) => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.scrollY / totalHeight) * 100;
      setScrollProgress(Math.min(100, Math.max(0, progress)));
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial calculation
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const positionStyles = position === 'top'
    ? { top: 0, left: 0, right: 0 }
    : { bottom: 0, left: 0, right: 0 };

  return (
    <Box
      sx={{
        position: 'fixed',
        ...positionStyles,
        height,
        backgroundColor: color,
        width: `${scrollProgress}%`,
        zIndex: 999,
        transition: 'width 0.3s ease'
      }}
    >
      {showPercentage && (
        <Box
          sx={{
            position: 'absolute',
            right: 8,
            top: position === 'top' ? height + 4 : -height - 20,
            fontSize: '0.75rem',
            color: 'text.secondary',
            fontWeight: 'bold'
          }}
        >
          {Math.round(scrollProgress)}%
        </Box>
      )}
    </Box>
  );
};

// SmoothScrollLink component for smooth scrolling to sections
export const SmoothScrollLink = ({
  to,
  children,
  duration = 500,
  offset = 0,
  smooth = true,
  onClick,
  ...props
}) => {
  const handleClick = (e) => {
    e.preventDefault();

    if (smooth) {
      scroll.scrollTo(to, {
        duration,
        offset,
        smooth: 'easeInOutQuart'
      });
    } else {
      const element = document.getElementById(to);
      if (element) {
        element.scrollIntoView({ behavior: 'auto' });
      }
    }

    if (onClick) onClick(e);
  };

  return (
    <Box
      component="a"
      href={`#${to}`}
      onClick={handleClick}
      sx={{
        cursor: 'pointer',
        textDecoration: 'none',
        '&:hover': {
          textDecoration: 'underline'
        }
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

export default ScrollToTop;