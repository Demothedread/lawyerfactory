import { useRef } from 'react';
import PropTypes from 'prop-types';

const MechanicalButton = ({
  children,
  onClick,
  variant = 'default',
  size = 'medium',
  disabled = false,
  pressed = false,
  className = '',
  enableSound = true,
  ...props
}) => {
  const buttonRef = useRef(null);

  // Play mechanical click sound effect
  const playClickSound = () => {
    if (!enableSound) return;
    
    // Create oscillator for retro mechanical click
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const now = audioContext.currentTime;
    
    // Click tone - short burst
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    
    osc.connect(gain);
    gain.connect(audioContext.destination);
    
    osc.frequency.setValueAtTime(150, now);
    osc.frequency.exponentialRampToValueAtTime(50, now + 0.05);
    
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05);
    
    osc.start(now);
    osc.stop(now + 0.05);
  };

  const handleClick = (e) => {
    if (!disabled && onClick) {
      playClickSound();
      
      // Add mechanical press effect with ripple
      const button = e.currentTarget;
      button.classList.add('pressed');

      // Create ripple effect
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      button.appendChild(ripple);

      // Remove ripple after animation
      setTimeout(() => {
        ripple.remove();
      }, 600);

      // Remove pressed effect after animation
      setTimeout(() => {
        button.classList.remove('pressed');
      }, 150);

      onClick(e);
    }
  };

  const buttonClasses = [
    'mech-button',
    `mech-button--${variant}`,
    `mech-button--${size}`,
    pressed && 'pressed',
    disabled && 'disabled',
    className
  ].filter(Boolean).join(' ');

  return (
    <>
      <style>{`
        .mech-button {
          position: relative;
          font-family: "Share Tech Mono", monospace;
          font-weight: 600;
          border: 2px solid var(--soviet-brass);
          border-radius: 4px;
          cursor: pointer;
          overflow: hidden;
          transition: all 0.1s ease-out;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          outline: none;
          
          /* Enhanced depth with layered shadows */
          box-shadow: 
            0 8px 16px rgba(0, 0, 0, 0.6),
            0 4px 8px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            inset 0 -2px 4px rgba(0, 0, 0, 0.4);
          
          background: linear-gradient(135deg, var(--soviet-panel) 0%, rgba(42, 42, 42, 0.9) 100%);
          color: var(--soviet-brass);
        }

        .mech-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 
            0 12px 24px rgba(0, 0, 0, 0.7),
            0 6px 12px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3),
            inset 0 -2px 4px rgba(0, 0, 0, 0.4);
          background: linear-gradient(135deg, rgba(50, 50, 50, 0.95) 0%, rgba(32, 32, 32, 0.95) 100%);
        }

        .mech-button:active:not(:disabled),
        .mech-button.pressed {
          transform: translateY(4px);
          box-shadow: 
            0 2px 4px rgba(0, 0, 0, 0.6),
            inset 0 2px 4px rgba(0, 0, 0, 0.5),
            inset 0 -1px 2px rgba(255, 255, 255, 0.1),
            inset 0 0 4px rgba(0, 0, 0, 0.3);
          background: linear-gradient(135deg, rgba(30, 30, 30, 0.95) 0%, rgba(20, 20, 20, 0.95) 100%);
        }

        .mech-button--primary {
          background: linear-gradient(135deg, var(--soviet-green) 0%, rgba(16, 185, 129, 0.85) 100%);
          color: white;
          border-color: var(--soviet-green);
          box-shadow: 
            0 8px 16px rgba(16, 185, 129, 0.3),
            0 4px 8px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            inset 0 -2px 4px rgba(0, 0, 0, 0.4);
        }

        .mech-button--primary:hover:not(:disabled) {
          box-shadow: 
            0 12px 24px rgba(16, 185, 129, 0.4),
            0 6px 12px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3),
            inset 0 -2px 4px rgba(0, 0, 0, 0.4);
        }

        .mech-button--primary.pressed {
          box-shadow: 
            0 2px 4px rgba(16, 185, 129, 0.3),
            inset 0 2px 4px rgba(0, 0, 0, 0.5),
            inset 0 -1px 2px rgba(255, 255, 255, 0.1);
        }

        .mech-button--success {
          background: linear-gradient(135deg, #10b981 0%, rgba(16, 185, 129, 0.85) 100%);
          color: white;
          border-color: #10b981;
        }

        .mech-button--danger {
          background: linear-gradient(135deg, #dc2626 0%, rgba(220, 38, 38, 0.85) 100%);
          color: white;
          border-color: #dc2626;
        }

        .mech-button--warning {
          background: linear-gradient(135deg, #f59e0b 0%, rgba(245, 158, 11, 0.85) 100%);
          color: white;
          border-color: #f59e0b;
        }

        .mech-button--info {
          background: linear-gradient(135deg, #3b82f6 0%, rgba(59, 130, 246, 0.85) 100%);
          color: white;
          border-color: #3b82f6;
        }

        .mech-button--small {
          padding: 4px 8px;
          font-size: 10px;
        }

        .mech-button--medium {
          padding: 8px 16px;
          font-size: 12px;
        }

        .mech-button--large {
          padding: 12px 24px;
          font-size: 14px;
        }

        .mech-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          color: var(--soviet-panel);
        }

        .mech-button__content {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          position: relative;
          z-index: 2;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }

        .mech-button__shadow {
          position: absolute;
          bottom: -8px;
          left: 0;
          right: 0;
          height: 8px;
          background: radial-gradient(ellipse at center, rgba(0, 0, 0, 0.5) 0%, transparent 70%);
          opacity: 0;
          transition: opacity 0.15s ease-out;
          z-index: 1;
        }

        .mech-button:hover:not(:disabled) .mech-button__shadow {
          opacity: 1;
        }

        /* Ripple effect for visual feedback */
        .ripple {
          position: absolute;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.5);
          transform: scale(0);
          animation: ripple-animation 0.6s ease-out;
          pointer-events: none;
          z-index: 3;
        }

        @keyframes ripple-animation {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
      `}</style>

      <button
        ref={buttonRef}
        className={buttonClasses}
        onClick={handleClick}
        disabled={disabled}
        {...props}
      >
        <span className="mech-button__content">
          {children}
        </span>
        <div className="mech-button__shadow"></div>
      </button>
    </>
  );
};

MechanicalButton.propTypes = {
  children: PropTypes.node,
  onClick: PropTypes.func,
  variant: PropTypes.oneOf([
    'default',
    'primary',
    'secondary',
    'success',
    'warning',
    'danger',
    'info'
  ]),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  pressed: PropTypes.bool,
  className: PropTypes.string,
  enableSound: PropTypes.bool,
};

export default MechanicalButton;