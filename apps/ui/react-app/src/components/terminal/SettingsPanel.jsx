// SettingsPanel - Professional settings and configuration panel component
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { MetalPanel, MechanicalButton, ToggleSwitch } from '../soviet';

const SettingsPanel = ({
  showSettings = false,
  onClose,
  settings = {},
  onSettingsChange,
}) => {
  const [activeSettingsTab, setActiveSettingsTab] = useState('general');

  const settingsTabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'ai', label: 'AI Models', icon: '🤖' },
    { id: 'legal', label: 'Legal Config', icon: '⚖️' },
    { id: 'export', label: 'Export', icon: '📄' },
  ];

  const handleSettingChange = (key, value) => {
    if (onSettingsChange) {
      onSettingsChange({ ...settings, [key]: value });
    }
  };

  if (!showSettings) return null;

  return (
    <div className="legal-intake-overlay">
      <div className="legal-intake-container" style={{ maxWidth: '600px' }}>
        <div className="legal-pad-header">
          <h2 className="pad-title">BRIEFCASER SETTINGS</h2>
          <MechanicalButton onClick={onClose} style={{ padding: '4px 8px' }}>
            ✕
          </MechanicalButton>
        </div>
        <div className="legal-pad-form">
          <div className="settings-tabs">
            {settingsTabs.map((tab) => (
              <MechanicalButton
                key={tab.id}
                onClick={() => setActiveSettingsTab(tab.id)}
                variant={activeSettingsTab === tab.id ? 'success' : 'default'}
                style={{
                  fontSize: '12px',
                  padding: '8px 12px',
                  margin: '2px',
                }}
              >
                {tab.icon} {tab.label}
              </MechanicalButton>
            ))}
          </div>

          <div className="settings-content">
            {activeSettingsTab === 'general' && (
              <div>
                <h4>General Settings</h4>
                <ToggleSwitch
                  active={settings.autoSave}
                  onToggle={() => handleSettingChange('autoSave', !settings.autoSave)}
                  label="Auto Save"
                />
                <ToggleSwitch
                  active={settings.notifications}
                  onToggle={() => handleSettingChange('notifications', !settings.notifications)}
                  label="Notifications"
                />
                <ToggleSwitch
                  active={settings.darkMode}
                  onToggle={() => handleSettingChange('darkMode', !settings.darkMode)}
                  label="Dark Mode"
                />
              </div>
            )}

            {activeSettingsTab === 'ai' && (
              <div>
                <h4>AI Model Configuration</h4>
                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Primary LLM Provider:
                  </label>
                  <select
                    value={settings.aiModel}
                    onChange={(e) => handleSettingChange('aiModel', e.target.value)}
                    className="settings-select"
                  >
                    <option value="gpt-4">GPT-4</option>
                    <option value="claude-3">Claude-3</option>
                    <option value="gemini">Gemini Pro</option>
                    <option value="groq">Groq</option>
                  </select>
                </div>
                <ToggleSwitch
                  active={settings.researchMode}
                  onToggle={() => handleSettingChange('researchMode', !settings.researchMode)}
                  label="Enhanced Research Mode"
                />
                <ToggleSwitch
                  active={settings.citationValidation}
                  onToggle={() => handleSettingChange('citationValidation', !settings.citationValidation)}
                  label="Citation Validation"
                />
              </div>
            )}

            {activeSettingsTab === 'legal' && (
              <div>
                <h4>Legal Configuration</h4>
                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Jurisdiction:
                  </label>
                  <select
                    value={settings.jurisdiction}
                    onChange={(e) => handleSettingChange('jurisdiction', e.target.value)}
                    className="settings-select"
                  >
                    <option value="federal">Federal</option>
                    <option value="state">State</option>
                    <option value="county">County</option>
                    <option value="municipal">Municipal</option>
                  </select>
                </div>
                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Citation Style:
                  </label>
                  <select
                    value={settings.citationStyle}
                    onChange={(e) => handleSettingChange('citationStyle', e.target.value)}
                    className="settings-select"
                  >
                    <option value="bluebook">Bluebook</option>
                    <option value="alwd">ALWD</option>
                    <option value="apa">APA</option>
                    <option value="mla">MLA</option>
                  </select>
                </div>
                <ToggleSwitch
                  active={settings.strictCompliance}
                  onToggle={() => handleSettingChange('strictCompliance', !settings.strictCompliance)}
                  label="Strict Compliance Mode"
                />
              </div>
            )}

            {activeSettingsTab === 'export' && (
              <div>
                <h4>Export Configuration</h4>
                <ToggleSwitch
                  active={settings.pdfExport}
                  onToggle={() => handleSettingChange('pdfExport', !settings.pdfExport)}
                  label="PDF Export"
                />
                <ToggleSwitch
                  active={settings.docExport}
                  onToggle={() => handleSettingChange('docExport', !settings.docExport)}
                  label="DOC Export"
                />
                <ToggleSwitch
                  active={settings.markdownExport}
                  onToggle={() => handleSettingChange('markdownExport', !settings.markdownExport)}
                  label="Markdown Export"
                />
                <div style={{ marginTop: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Default Export Format:
                  </label>
                  <select
                    value={settings.defaultExportFormat}
                    onChange={(e) => handleSettingChange('defaultExportFormat', e.target.value)}
                    className="settings-select"
                  >
                    <option value="pdf">PDF</option>
                    <option value="doc">DOC</option>
                    <option value="markdown">Markdown</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          <div className="form-actions">
            <MechanicalButton onClick={onClose} variant="danger">
              Cancel
            </MechanicalButton>
            <MechanicalButton onClick={onClose} variant="success">
              Save Settings
            </MechanicalButton>
          </div>
        </div>
      </div>
    </div>
  );
};

SettingsPanel.propTypes = {
  showSettings: PropTypes.bool,
  onClose: PropTypes.func,
  settings: PropTypes.object,
  onSettingsChange: PropTypes.func,
};

export default SettingsPanel;