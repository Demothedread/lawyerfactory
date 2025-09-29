// StatusLights - Professional Soviet industrial status indicator array component
import React from 'react';
import PropTypes from 'prop-types';

const StatusLights = ({
  statuses = [],
  labels = [],
  layout = 'horizontal',
  size = 'medium',
  className = '',
  ...props
}) => {
  const lightsArray = Array.isArray(statuses) ? statuses : [statuses];

  const containerClasses = [
    'status-lights',
    `status-lights--${layout}`,
    `status-lights--${size}`,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses} {...props}>
      {lightsArray.map((status, index) => (
        <React.Fragment key={index}>
          <div
            className={`status-light status-light--${status}`}
            title={labels[index] || `Status ${index + 1}: ${status}`}
          />
          {labels[index] && layout === 'vertical' && (
            <span className="status-label">
              {labels[index]}
            </span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

StatusLights.propTypes = {
  statuses: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.oneOf(['red', 'amber', 'green', 'blue', 'off'])),
    PropTypes.oneOf(['red', 'amber', 'green', 'blue', 'off'])
  ]),
  labels: PropTypes.arrayOf(PropTypes.string),
  layout: PropTypes.oneOf(['horizontal', 'vertical']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  className: PropTypes.string,
};

export default StatusLights;