// AnalogGauge - Professional Soviet industrial analog gauge component
import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

const AnalogGauge = ({
  value = 0,
  min = 0,
  max = 100,
  label = '',
  size = 120,
  needleColor = 'var(--soviet-crimson)',
  showValue = true,
  animated = true,
  className = '',
  ...props
}) => {
  const [displayValue, setDisplayValue] = useState(min);
  const [isAnimating, setIsAnimating] = useState(false);

  // Calculate angle for needle (-90 to 90 degrees)
  const calculateAngle = (val) => {
    const normalizedValue = Math.max(min, Math.min(max, val));
    return ((normalizedValue - min) / (max - min)) * 180 - 90;
  };

  const currentAngle = calculateAngle(displayValue);
  const targetAngle = calculateAngle(value);

  // Animate needle movement
  useEffect(() => {
    if (!animated || displayValue === value) return;

    setIsAnimating(true);
    const duration = 1000; // 1 second animation
    const steps = 60; // 60 FPS
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

  const gaugeStyle = {
    width: `${size}px`,
    height: `${size}px`,
  };

  const needleStyle = {
    transform: `translateX(-50%) rotate(${currentAngle}deg)`,
    transition: isAnimating ? 'transform 0.1s ease-out' : 'none',
  };

  return (
    <div className={`analog-gauge ${className}`} style={gaugeStyle} {...props}>
      {/* Gauge background rings */}
      <div className="gauge-ring gauge-ring--outer"></div>
      <div className="gauge-ring gauge-ring--middle"></div>
      <div className="gauge-ring gauge-ring--inner"></div>

      {/* Needle */}
      <div
        className="gauge-needle"
        style={{
          ...needleStyle,
          backgroundColor: needleColor,
          boxShadow: `0 0 4px ${needleColor}`,
        }}
      />

      {/* Center hub */}
      <div className="gauge-center"></div>

      {/* Value display */}
      {showValue && (
        <div className="gauge-value">
          <span className="gauge-value__number">
            {Math.round(displayValue)}
          </span>
          {label && (
            <span className="gauge-value__label">{label}</span>
          )}
        </div>
      )}

      {/* Tick marks */}
      <div className="gauge-ticks">
        {Array.from({ length: 11 }, (_, i) => {
          const tickAngle = (i * 18) - 90; // Every 10% of range
          const isMajor = i % 2 === 0;
          return (
            <div
              key={i}
              className={`gauge-tick ${isMajor ? 'gauge-tick--major' : 'gauge-tick--minor'}`}
              style={{
                transform: `rotate(${tickAngle}deg)`,
              }}
            />
          );
        })}
      </div>

      {/* Range labels */}
      <div className="gauge-labels">
        <span className="gauge-label gauge-label--min">{min}</span>
        <span className="gauge-label gauge-label--max">{max}</span>
      </div>
    </div>
  );
};

AnalogGauge.propTypes = {
  value: PropTypes.number,
  min: PropTypes.number,
  max: PropTypes.number,
  label: PropTypes.string,
  size: PropTypes.number,
  needleColor: PropTypes.string,
  showValue: PropTypes.bool,
  animated: PropTypes.bool,
  className: PropTypes.string,
};

export default AnalogGauge;