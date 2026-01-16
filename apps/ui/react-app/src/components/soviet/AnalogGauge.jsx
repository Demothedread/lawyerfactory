import { useEffect, useState } from 'react';
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
  phaseLabel = '',
  isComplete = false,
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

  // Completion glow effect
  const completionGlowStyle = isComplete ? {
    boxShadow: `
      0 0 10px rgba(16, 185, 129, 0.6),
      inset 0 0 10px rgba(16, 185, 129, 0.3),
      0 0 20px rgba(16, 185, 129, 0.4)
    `,
    animation: 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  } : {};

  return (
    <>
      <style>{`
        @keyframes pulse-glow {
          0%, 100% { 
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.6),
                        inset 0 0 10px rgba(16, 185, 129, 0.3),
                        0 0 20px rgba(16, 185, 129, 0.4);
          }
          50% { 
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.8),
                        inset 0 0 15px rgba(16, 185, 129, 0.5),
                        0 0 30px rgba(16, 185, 129, 0.6);
          }
        }

        @keyframes needle-swing {
          0% { transform: translateX(-50%) rotate(-90deg); }
          50% { transform: translateX(-50%) rotate(0deg); }
          100% { transform: translateX(-50%) rotate(${currentAngle}deg); }
        }

        .analog-gauge {
          position: relative;
          border-radius: 50%;
          background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.1), rgba(0,0,0,0.3));
          border: 3px solid var(--soviet-brass);
          box-shadow: 
            inset 0 2px 4px rgba(0,0,0,0.5),
            inset 0 -2px 4px rgba(255,255,255,0.1),
            0 4px 8px rgba(0,0,0,0.4);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .gauge-ring {
          position: absolute;
          border-radius: 50%;
          border: 1px solid var(--soviet-brass);
        }

        .gauge-ring--outer {
          width: 95%;
          height: 95%;
          opacity: 0.4;
        }

        .gauge-ring--middle {
          width: 70%;
          height: 70%;
          opacity: 0.6;
        }

        .gauge-ring--inner {
          width: 45%;
          height: 45%;
          opacity: 0.3;
        }

        .gauge-needle {
          position: absolute;
          width: 35%;
          height: 3px;
          top: 50%;
          left: 50%;
          origin: left center;
          background: linear-gradient(to right, ${needleColor}, rgba(255,255,255,0.2));
          border-radius: 2px;
          box-shadow: 
            0 1px 2px rgba(0,0,0,0.6),
            0 0 3px ${needleColor};
        }

        .gauge-center {
          position: absolute;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: radial-gradient(circle at 30% 30%, var(--soviet-brass), var(--soviet-crimson));
          box-shadow: 
            inset 0 -1px 2px rgba(0,0,0,0.4),
            0 2px 4px rgba(0,0,0,0.5),
            0 0 6px rgba(184, 115, 51, 0.4);
          z-index: 10;
        }

        .gauge-value {
          position: absolute;
          text-align: center;
          color: var(--soviet-brass);
          font-family: "Share Tech Mono", monospace;
          font-weight: bold;
          text-shadow: 0 1px 2px rgba(0,0,0,0.8);
          z-index: 5;
        }

        .gauge-value__number {
          display: block;
          font-size: 18px;
        }

        .gauge-value__label {
          display: block;
          font-size: 10px;
          opacity: 0.7;
          margin-top: 2px;
        }

        .gauge-ticks {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
        }

        .gauge-tick {
          position: absolute;
          left: 50%;
          top: 50%;
          width: 2px;
          height: 20%;
          background: var(--soviet-brass);
          transform-origin: 50% 50%;
          margin-left: -1px;
          margin-top: -20%;
        }

        .gauge-tick--major {
          height: 25%;
          margin-top: -25%;
          width: 3px;
          margin-left: -1.5px;
          background: var(--soviet-brass);
          opacity: 0.8;
        }

        .gauge-tick--minor {
          opacity: 0.5;
        }

        .gauge-labels {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
        }

        .gauge-label {
          position: absolute;
          font-size: 9px;
          font-weight: bold;
          color: var(--soviet-brass);
          font-family: "Share Tech Mono", monospace;
          text-shadow: 0 1px 2px rgba(0,0,0,0.8);
        }

        .gauge-label--min {
          bottom: 8px;
          left: 8px;
        }

        .gauge-label--max {
          bottom: 8px;
          right: 8px;
        }
      `}</style>

      <div 
        className={`analog-gauge ${className}`} 
        style={{ ...gaugeStyle, ...completionGlowStyle }} 
        {...props}
      >
        {/* Gauge background rings */}
        <div className="gauge-ring gauge-ring--outer"></div>
        <div className="gauge-ring gauge-ring--middle"></div>
        <div className="gauge-ring gauge-ring--inner"></div>

        {/* Needle */}
        <div
          className="gauge-needle"
          style={{
            ...needleStyle,
            backgroundColor: isComplete ? 'var(--soviet-green)' : needleColor,
            boxShadow: isComplete 
              ? `0 1px 2px rgba(0,0,0,0.6), 0 0 5px var(--soviet-green)` 
              : `0 1px 2px rgba(0,0,0,0.6), 0 0 3px ${needleColor}`,
          }}
        />

        {/* Center hub */}
        <div className="gauge-center"></div>

        {/* Value display */}
        {showValue && (
          <div className="gauge-value">
            <span className="gauge-value__number">
              {Math.round(displayValue)}%
            </span>
            {phaseLabel && (
              <span className="gauge-value__label">{phaseLabel}</span>
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

        {/* Completion badge */}
        {isComplete && (
          <div style={{
            position: 'absolute',
            top: '-15px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--soviet-green)',
            color: 'white',
            padding: '2px 8px',
            borderRadius: '10px',
            fontSize: '10px',
            fontWeight: 'bold',
            boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
            whiteSpace: 'nowrap',
          }}>
            ✓ COMPLETE
          </div>
        )}
      </div>
    </>
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
  phaseLabel: PropTypes.string,
  isComplete: PropTypes.bool,
};

export default AnalogGauge;