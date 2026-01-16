// DeliverablesPanel - Professional deliverables and chat interface panel component
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { MetalPanel, MechanicalButton } from '../soviet';

const DeliverablesPanel = ({
  rightPanelCollapsed = false,
  onToggleRightPanel,
  mockDocuments = [],
  onDownloadPDF,
  onDownloadDOC,
}) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      agent: 'maestro',
      content: 'Welcome to Briefcaser Control Terminal. I am Maestro, your legal workflow orchestrator. How may I assist you today?',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [activeAgent, setActiveAgent] = useState('maestro');

  const agents = {
    maestro: { name: 'Maestro', icon: '🎭', color: 'var(--soviet-brass)' },
    reader: { name: 'Reader', icon: '📖', color: 'var(--soviet-emerald)' },
    researcher: { name: 'Researcher', icon: '🔍', color: 'var(--soviet-bronze)' },
    writer: { name: 'Writer', icon: '✍️', color: 'var(--soviet-amber)' },
    editor: { name: 'Editor', icon: '🔧', color: 'var(--soviet-crimson)' },
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: Date.now(),
      agent: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');

    // Simulate agent response
    setTimeout(() => {
      const response = {
        id: Date.now() + 1,
        agent: activeAgent,
        content: `${agents[activeAgent].name} acknowledges: "${inputValue}". Processing request...`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, response]);
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (rightPanelCollapsed) {
    return (
      <div className="collapsed-panel">
        DL
      </div>
    );
  }

  return (
    <div className="deliverables-container">
      {/* Generated Documents Section */}
      <div className="deliverables-section">
        <h4 style={{ marginBottom: 'var(--space-md)' }}>
          Generated Documents
        </h4>
        {mockDocuments.map((doc) => (
          <div key={doc.id} className="document-card">
            <div className="document-header">
              <span className="document-name">{doc.name}</span>
              <span className={`document-status status-${doc.status.toLowerCase()}`}>
                {doc.status}
              </span>
            </div>
            <div className="document-meta">
              {doc.type} • {doc.lastModified}
            </div>
            <div className="document-actions">
              <MechanicalButton
                variant="default"
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => onDownloadPDF(doc.name)}
              >
                PDF
              </MechanicalButton>
              <MechanicalButton
                variant="default"
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => onDownloadDOC(doc.name)}
              >
                DOC
              </MechanicalButton>
            </div>
          </div>
        ))}
      </div>

      {/* LLM Chat Interface */}
      <div className="deliverables-section">
        <h4>LLM Chat Interface</h4>
        <LLMChatPanel
          messages={messages}
          inputValue={inputValue}
          setInputValue={setInputValue}
          activeAgent={activeAgent}
          setActiveAgent={setActiveAgent}
          agents={agents}
          onSendMessage={handleSendMessage}
          onKeyPress={handleKeyPress}
        />
      </div>
    </div>
  );
};

// LLM Chat Panel Component
const LLMChatPanel = ({
  messages,
  inputValue,
  setInputValue,
  activeAgent,
  setActiveAgent,
  agents,
  onSendMessage,
  onKeyPress,
}) => {
  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className="chat-message">
            <div
              className="agent-avatar"
              style={{
                background: message.agent === 'user'
                  ? 'var(--soviet-steel)'
                  : agents[message.agent]?.color,
              }}
            >
              {message.agent === 'user' ? '👤' : agents[message.agent]?.icon}
            </div>
            <div className="message-content">
              <div style={{
                fontSize: '12px',
                opacity: 0.7,
                marginBottom: '5px',
              }}>
                {message.agent === 'user' ? 'You' : agents[message.agent]?.name} - {message.timestamp}
              </div>
              {message.content}
            </div>
          </div>
        ))}
      </div>
      <div className="chat-input">
        <div style={{ marginBottom: '10px' }}>
          <label style={{ fontSize: '12px', marginRight: '10px' }}>
            Active Agent:
          </label>
          <select
            value={activeAgent}
            onChange={(e) => setActiveAgent(e.target.value)}
            style={{
              background: 'var(--soviet-steel)',
              border: '1px solid var(--soviet-brass)',
              color: 'var(--soviet-silver)',
              padding: '5px',
            }}
          >
            {Object.entries(agents).map(([key, agent]) => (
              <option key={key} value={key}>
                {agent.icon} {agent.name}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            className="input-field"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={onKeyPress}
            placeholder={`Message ${agents[activeAgent].name}...`}
            style={{ flex: 1 }}
          />
          <MechanicalButton onClick={onSendMessage} variant="success">
            Send
          </MechanicalButton>
        </div>
      </div>
    </div>
  );
};

LLMChatPanel.propTypes = {
  messages: PropTypes.array,
  inputValue: PropTypes.string,
  setInputValue: PropTypes.func,
  activeAgent: PropTypes.string,
  setActiveAgent: PropTypes.func,
  agents: PropTypes.object,
  onSendMessage: PropTypes.func,
  onKeyPress: PropTypes.func,
};

DeliverablesPanel.propTypes = {
  rightPanelCollapsed: PropTypes.bool,
  onToggleRightPanel: PropTypes.func,
  mockDocuments: PropTypes.array,
  onDownloadPDF: PropTypes.func,
  onDownloadDOC: PropTypes.func,
};

export default DeliverablesPanel;