// MagicUI Soviet Industrial Adapter
// Wrapper components applying Soviet styling to strategic MagicUI components
import React from 'react';

/**
 * RetroGridSoviet - Brushed metal panel background
 * Wraps RetroGrid with Soviet-themed colors and opacity
 */
export const RetroGridSoviet = ({ children, className = '' }) => (
  <div className={`magicui-retro-grid-soviet ${className}`}>
    <div className="magicui-retro-grid" />
    <div className="retro-grid-content">
      {children}
    </div>
  </div>
);

/**
 * FileTreeSoviet - Hierarchical evidence display
 * Wraps FileTree with Russian font, brass accents, and Soviet styling
 */
export const FileTreeSoviet = ({ items, onSelect, className = '' }) => (
  <div className={`magicui-file-tree-soviet ${className}`}>
    <FileTreeRenderer items={items} onSelect={onSelect} />
  </div>
);

// Helper component for recursive tree rendering
const FileTreeRenderer = ({ items, onSelect, level = 0 }) => {
  const [expanded, setExpanded] = React.useState({});

  const toggleExpanded = (id) => {
    setExpanded(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <div className="magicui-file-tree">
      {items?.map((item, index) => (
        <div key={`${level}-${index}`} className="magicui-file-tree-item-wrapper">
          <div
            className="magicui-file-tree-item"
            onClick={() => {
              if (item.children) {
                toggleExpanded(item.id);
              }
              onSelect?.(item);
            }}
          >
            {item.children && (
              <span className={`magicui-file-tree-toggle ${expanded[item.id] ? 'expanded' : ''}`}>
                ▶
              </span>
            )}
            <span className="magicui-file-tree-icon">
              {item.icon || (item.children ? '📁' : '📄')}
            </span>
            <span className="magicui-file-tree-name">{item.name}</span>
          </div>
          {expanded[item.id] && item.children && (
            <div className="magicui-file-tree-nested">
              <FileTreeRenderer items={item.children} onSelect={onSelect} level={level + 1} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

/**
 * MarqueeSoviet - Status ticker in Soviet style
 * Wraps Marquee with brass frame and monospace font
 */
export const MarqueeSoviet = ({ children, messages = [] }) => {
  const [messageIndex, setMessageIndex] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % (messages.length || 1));
    }, 5000);
    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="magicui-marquee-soviet">
      <div className="magicui-marquee-content">
        {messages.length > 0 ? messages[messageIndex] : children}
      </div>
    </div>
  );
};

/**
 * TerminalSoviet - CRT-style output display
 * Wraps Terminal with green text, scanlines, and monospace font
 */
export const TerminalSoviet = ({ content = '', lines = [], className = '' }) => {
  const displayContent = Array.isArray(lines) ? lines.join('\n') : content;

  return (
    <div className={`magicui-terminal-soviet ${className}`}>
      <div className="magicui-terminal">
        <div className="magicui-terminal-content">
          {displayContent}
        </div>
        <div className="magicui-terminal-scanlines" />
      </div>
    </div>
  );
};

/**
 * RetroGridSovietBackground - Applies RetroGrid as page background
 * Positions it absolutely to avoid layout interference
 */
export const RetroGridSovietBackground = () => (
  <div className="magicui-retro-grid-background">
    <div className="magicui-retro-grid" />
  </div>
);

/**
 * SovietComponentsWrapper - Higher-order component
 * Applies Soviet styling to any component with class mapping
 */
export const withSovietTheme = (Component) => {
  return function SovietThemeWrapper(props) {
    return (
      <div className="soviet-theme-wrapper">
        <Component {...props} />
      </div>
    );
  };
};

export default {
  RetroGridSoviet,
  FileTreeSoviet,
  MarqueeSoviet,
  TerminalSoviet,
  RetroGridSovietBackground,
  withSovietTheme,
};
