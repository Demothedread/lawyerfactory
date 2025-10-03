// ContextOverlay - Modal, drawer, and floating panel system with portal rendering

import './ContextOverlay.css';


/**
 * ResearchPanelOverlay - Floating research panel
 */
export const ResearchPanelOverlay = ({
  open,
  onClose,
  researchData = [],
  onSelectAuthority = null,
}) => {
  return (
    <ContextOverlay
      open={open}
      onClose={onClose}
      variant="floating"
      title="Legal Research Panel"
      subtitle={`${researchData.length} authorities found`}
      icon="🔍"
      width={500}
      height="600px"
      draggable={true}
      initialPosition={{ x: 100, y: 100 }}
    >
      <div className="research-panel">
        {researchData.length === 0 ? (
          <div className="research-empty">
            <p>No research results available</p>
            <p className="research-empty-subtitle">
              Start a research phase to populate this panel
            </p>
          </div>
        ) : (
          <div className="research-list">
            {researchData.map((item, index) => (
              <div
                key={index}
                className="research-item"
                onClick={() => onSelectAuthority && onSelectAuthority(item)}
              >
                <div className="research-item-header">
                  <strong>{item.title || `Authority ${index + 1}`}</strong>
                  <span className={`research-badge research-badge--${item.authority_type}`}>
                    {item.authority_type || 'unknown'}
                  </span>
                </div>
                <p className="research-item-content">
                  {item.content?.substring(0, 200)}...
                </p>
                <div className="research-item-meta">
                  <span>Relevance: {(item.relevance * 100).toFixed(1)}%</span>
                  <span>Source: {item.source}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ContextOverlay>
  );
};

/**
 * DrawerOverlay - Sliding drawer from left or right
 */
export const DrawerOverlay = ({
  open,
  onClose,
  side = 'right', // 'left' or 'right'
  title,
  children,
  width = 400,
}) => {
  return (
    <ContextOverlay
      open={open}
      onClose={onClose}
      variant={`drawer-${side}`}
      title={title}
      width={width}
      closeOnClickOutside={true}
      closeOnEscape={true}
    >
      {children}
    </ContextOverlay>
  );
};

export default ContextOverlay;
