// ToggleSwitch - Professional Soviet industrial toggle switch component
import React from 'react';
import PropTypes from 'prop-types';

const ToggleSwitch = ({
  active = false,
  onToggle,
  label = '',
  disabled = false,
  size = 'medium',
  variant = 'default',
  className = '',
  ...props
}) => {
  const handleClick = () => {
    if (!disabled && onToggle) {
      onToggle(!active);
    }
  };

  const switchClasses = [
    'toggle-switch',
    `toggle-switch--${size}`,
    `toggle-switch--${variant}`,
    active && 'active',
    disabled && 'disabled',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={switchClasses} {...props}>
      {label && (
        <span className="toggle-label">
          {label}
        </span>
      )}

      <div
        className="toggle-track"
        onClick={handleClick}
        role="switch"
        aria-checked={active}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        <div className="toggle-handle" />
      </div>

      <div className="led-indicator" />
    </div>
  );
};

ToggleSwitch.propTypes = {
  active: PropTypes.bool,
  onToggle: PropTypes.func,
  label: PropTypes.string,
  disabled: PropTypes.bool,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  variant: PropTypes.oneOf(['default', 'warning', 'danger', 'success']),
  className: PropTypes.string,
};

export default ToggleSwitch;