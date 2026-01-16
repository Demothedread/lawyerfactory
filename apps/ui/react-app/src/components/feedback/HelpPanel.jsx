import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

/**
 * HelpPanel Component - Makes USER_GUIDE accessible from React app
 * 
 * Features:
 * - Loads USER_GUIDE.md from public folder
 * - Markdown rendering with search functionality
 * - Keyboard accessible (Ctrl+H / Cmd+H to toggle)
 * - Responsive design for all screen sizes
 * - Scrollable content with sticky header
 */
const HelpPanel = ({ isOpen, onClose }) => {
  const [content, setContent] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredContent, setFilteredContent] = useState('');
  const [loading, setLoading] = useState(false);

  // Load USER_GUIDE.md on mount
  useEffect(() => {
    if (isOpen && !content) {
      loadUserGuide();
    }
  }, [isOpen]);

  // Handle keyboard shortcut (Ctrl+H / Cmd+H)
  useEffect(() => {
    const handleKeyPress = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
        e.preventDefault();
        isOpen ? onClose() : onOpen?.();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen, onClose]);

  const loadUserGuide = async () => {
    setLoading(true);
    try {
      const response = await fetch('/USER_GUIDE.md');
      if (response.ok) {
        const text = await response.text();
        setContent(text);
        setFilteredContent(text);
      }
    } catch (error) {
      console.error('Error loading USER_GUIDE:', error);
      setContent('Failed to load user guide. Please check the public/USER_GUIDE.md file.');
    } finally {
      setLoading(false);
    }
  };

  // Filter content based on search
  useEffect(() => {
    if (!content) return;

    if (!searchTerm.trim()) {
      setFilteredContent(content);
      return;
    }

    const lines = content.split('\n');
    const filtered = lines.filter(line =>
      line.toLowerCase().includes(searchTerm.toLowerCase())
    ).join('\n');

    setFilteredContent(filtered || 'No results found for: ' + searchTerm);
  }, [searchTerm, content]);

  if (!isOpen) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.container} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>LawyerFactory User Guide</h2>
          <button
            onClick={onClose}
            style={styles.closeButton}
            title="Close Help (Ctrl+H)"
            aria-label="Close Help"
          >
            ✕
          </button>
        </div>

        {/* Search Bar */}
        <div style={styles.searchContainer}>
          <input
            type="text"
            placeholder="Search guide (Ctrl+F)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
            aria-label="Search user guide"
            autoFocus
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              style={styles.clearButton}
              aria-label="Clear search"
            >
              Clear
            </button>
          )}
        </div>

        {/* Content */}
        <div style={styles.content}>
          {loading ? (
            <div style={styles.loading}>Loading user guide...</div>
          ) : (
            <MarkdownContent content={filteredContent} />
          )}
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <small>
            Press <kbd>Ctrl+H</kbd> to toggle • Full docs: <a href="/USER_GUIDE.md" target="_blank" rel="noopener noreferrer">USER_GUIDE.md</a>
          </small>
        </div>
      </div>
    </div>
  );
};

HelpPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

/**
 * Simple Markdown renderer for help content
 */
const MarkdownContent = ({ content }) => {
  const lines = content.split('\n');
  const elements = [];
  let codeBlock = false;
  let codeContent = '';

  lines.forEach((line, idx) => {
    // Code blocks
    if (line.trim().startsWith('```')) {
      if (codeBlock) {
        elements.push(
          <pre key={idx} style={styles.codeBlock}>
            <code>{codeContent}</code>
          </pre>
        );
        codeContent = '';
        codeBlock = false;
      } else {
        codeBlock = true;
      }
      return;
    }

    if (codeBlock) {
      codeContent += line + '\n';
      return;
    }

    // Headers
    if (line.startsWith('## ')) {
      elements.push(<h2 key={idx} style={styles.h2}>{line.slice(3)}</h2>);
      return;
    }
    if (line.startsWith('### ')) {
      elements.push(<h3 key={idx} style={styles.h3}>{line.slice(4)}</h3>);
      return;
    }
    if (line.startsWith('#### ')) {
      elements.push(<h4 key={idx} style={styles.h4}>{line.slice(5)}</h4>);
      return;
    }

    // Lists
    if (line.trim().startsWith('- ')) {
      elements.push(<li key={idx} style={styles.li}>{line.trim().slice(2)}</li>);
      return;
    }

    // Paragraphs
    if (line.trim()) {
      elements.push(<p key={idx} style={styles.p}>{line}</p>);
    }
  });

  return <div>{elements}</div>;
};

MarkdownContent.propTypes = {
  content: PropTypes.string.isRequired,
};

// Styles
const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  container: {
    backgroundColor: '#1a1a1a',
    borderRadius: '8px',
    width: '90%',
    maxWidth: '800px',
    height: '90vh',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column',
    border: '2px solid #00ff00',
    boxShadow: '0 0 20px rgba(0, 255, 0, 0.3)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    borderBottom: '1px solid #00ff00',
    backgroundColor: '#0a0a0a',
  },
  title: {
    margin: 0,
    color: '#00ff00',
    fontFamily: 'Russo One, monospace',
    fontSize: '20px',
  },
  closeButton: {
    background: 'none',
    border: '1px solid #00ff00',
    color: '#00ff00',
    fontSize: '24px',
    cursor: 'pointer',
    padding: '5px 10px',
    borderRadius: '4px',
    transition: 'all 0.2s ease',
    ':hover': {
      backgroundColor: '#00ff00',
      color: '#000000',
    },
  },
  searchContainer: {
    display: 'flex',
    gap: '10px',
    padding: '15px 20px',
    borderBottom: '1px solid #00ff00',
    backgroundColor: '#0f0f0f',
  },
  searchInput: {
    flex: 1,
    padding: '8px 12px',
    border: '1px solid #00ff00',
    backgroundColor: '#000000',
    color: '#00ff00',
    fontFamily: 'Share Tech Mono, monospace',
    fontSize: '14px',
    outline: 'none',
    ':focus': {
      boxShadow: '0 0 10px rgba(0, 255, 0, 0.5)',
    },
  },
  clearButton: {
    padding: '8px 15px',
    border: '1px solid #00ff00',
    backgroundColor: '#000000',
    color: '#00ff00',
    cursor: 'pointer',
    borderRadius: '4px',
    fontFamily: 'Share Tech Mono, monospace',
    fontSize: '14px',
    transition: 'all 0.2s ease',
    ':hover': {
      backgroundColor: '#00ff00',
      color: '#000000',
    },
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    color: '#00ff00',
    fontFamily: 'Share Tech Mono, monospace',
    fontSize: '13px',
    lineHeight: '1.6',
  },
  footer: {
    padding: '12px 20px',
    borderTop: '1px solid #00ff00',
    backgroundColor: '#0a0a0a',
    color: '#00ff00',
    fontFamily: 'Share Tech Mono, monospace',
    fontSize: '12px',
  },
  // Markdown styles
  h2: {
    marginTop: '20px',
    marginBottom: '10px',
    color: '#00ff00',
    borderLeft: '3px solid #00ff00',
    paddingLeft: '10px',
  },
  h3: {
    marginTop: '15px',
    marginBottom: '8px',
    color: '#00ff00',
    opacity: 0.9,
  },
  h4: {
    marginTop: '12px',
    marginBottom: '6px',
    color: '#00ff00',
    opacity: 0.8,
  },
  p: {
    margin: '8px 0',
    lineHeight: '1.6',
  },
  li: {
    marginLeft: '20px',
    marginBottom: '5px',
  },
  codeBlock: {
    backgroundColor: '#0a0a0a',
    border: '1px solid #00ff00',
    padding: '12px',
    borderRadius: '4px',
    overflow: 'auto',
    marginBottom: '10px',
    color: '#00ff00',
  },
  loading: {
    textAlign: 'center',
    padding: '40px 20px',
    color: '#00ff00',
  },
};

export default HelpPanel;
