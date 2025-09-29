// MechanicalButton - Professional Soviet industrial mechanical button component
import React from 'react';
import PropTypes from 'prop-types';

const MechanicalButton = ({
  children,
  onClick,
  variant = 'default',
  size = 'medium',
  disabled = false,
  pressed = false,
  className = '',
  ...props
}) => {
  const handleClick = (e) => {
    if (!disabled && onClick) {
      // Add mechanical press effect
      const button = e.currentTarget;
      button.classList.add('pressed');

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
    <button
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
};

export default MechanicalButton;