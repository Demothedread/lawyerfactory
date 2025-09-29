// NixieDisplay - Professional Soviet industrial nixie tube display component
import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

const NixieDisplay = ({
  value = 0,
  digits = 3,
  label = '',
  glow = true,
  animated = true,
  className = '',
  ...props
}) => {
  const [displayValue, setDisplayValue] = useState(value);
  const [isAnimating, setIsAnimating] = useState(false);

  // Format value with leading zeros
  const formatValue = (val) => {
    const numStr = String(Math.max(0, Math.floor(val)));
    return numStr.padStart(digits, '0').slice(-digits);
  };

  const currentDisplay = formatValue(displayValue);
  const targetDisplay = formatValue(value);

  // Animate value changes
  useEffect(() => {
    if (!animated || displayValue === value) return;

    setIsAnimating(true);
    const duration = 500; // 0.5 second animation
    const steps = 30; // 30 FPS
    const stepDuration = duration / steps;
    const stepSize = (value - displayValue) / steps;

    let step = 0;
    const timer = setInterval(() => {
      step++;
      const newValue = displayValue + (stepSize * step);
      setDisplayValue(newValue);

      if (step >= steps) {
        clearInterval(timer);
        setDisplayValue(value);
        setIsAnimating(false);
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [value, displayValue, animated]);

  const displayClasses = [
    'nixie-display',
    glow && 'glow',
    isAnimating && 'animating',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className="nixie-container" {...props}>
      <div className={displayClasses}>
        {currentDisplay.split('').map((digit, index) => (
          <span
            key={index}
            className={`nixie-digit ${isAnimating ? 'changing' : ''}`}
            data-digit={digit}
          >
            {digit}
          </span>
        ))}
      </div>
      {label && (
        <div className="nixie-label">
          {label}
        </div>
      )}
    </div>
  );
};

NixieDisplay.propTypes = {
  value: PropTypes.number,
  digits: PropTypes.number,
  label: PropTypes.string,
  glow: PropTypes.bool,
  animated: PropTypes.bool,
  className: PropTypes.string,
};

export default NixieDisplay;