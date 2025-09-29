// MetalPanel - Professional Soviet industrial panel component
import React from 'react';
import PropTypes from 'prop-types';

const MetalPanel = ({
  children,
  title,
  className = '',
  collapsed = false,
  variant = 'default',
  rivets = true,
  glow = false,
  ...props
}) => {
  const panelClasses = [
    'metal-panel',
    `metal-panel--${variant}`,
    rivets && 'rivets',
    glow && 'glow',
    collapsed && 'collapsed',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={panelClasses} {...props}>
      {title && (
        <div className="panel-header">
          <h3>{title}</h3>
        </div>
      )}
      {!collapsed && (
        <div className="panel-content">
          {children}
        </div>
      )}
    </div>
  );
};

MetalPanel.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  className: PropTypes.string,
  collapsed: PropTypes.bool,
  variant: PropTypes.oneOf(['default', 'active', 'warning', 'danger']),
  rivets: PropTypes.bool,
  glow: PropTypes.bool,
};

export default MetalPanel;