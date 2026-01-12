// SettingsPanel - Consolidated professional settings and configuration panel with analog industrial styling
import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { fetchLLMConfig, updateLLMConfig } from '../../services/backendService';
import { MechanicalButton, ToggleSwitch } from '../soviet';
import './SettingsPanel.css';

const SettingsPanel = ({
  open = false,
  onClose,
  settings = {},
  onSettingsChange,
}) => {
  const [activeSettingsTab, setActiveSettingsTab] = useState('llm');
  const [llmConfig, setLLMConfig] = useState({
    provider: 'openai',
    model: 'gpt-5-mini',
    apiKey: '',
    temperature: 0.1,
    maxTokens: 2000,
  });    
  const [availableModels, setAvailableModels] = useState({});
  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  const settingsTabs = [
    { id: 'llm', label: 'LLM Configuration', icon: '🤖' },
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'legal', label: 'Legal Config', icon: '⚖️' },
    { id: 'phase', label: 'Phase Settings', icon: '🔄' },
    { id: 'export', label: 'Export', icon: '📄' },
  ];

  // Load LLM config from backend
  useEffect(() => {
    if (open) {
      loadLLMConfig();
    }
  }, [open]);

  const loadLLMConfig = async () => {
    try {
      setLoading(true);
      const response = await fetchLLMConfig();
      if (response.success) {
        setLLMConfig({
          provider: response.config.provider || 'openai',
          model: response.config.model || 'gpt-5-mini',
          apiKey: response.config.api_key || '',
          temperature: response.config.temperature || 0.1,
          maxTokens: response.config.max_tokens || 20000,
        });
        setAvailableModels(response.available_models || {});
      }
    } catch (error) {
      console.error('Failed to load LLM config:', error);
      setSaveStatus('Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleLLMConfigChange = (key, value) => {
    setLLMConfig(prev => ({ ...prev, [key]: value }));
    setSaveStatus('');
  };

  const handleSettingChange = (key, value) => {
    if (onSettingsChange) {
      onSettingsChange({ ...settings, [key]: value });
    }
  };

  const saveLLMConfig = async () => {
    try {
      setLoading(true);
      setSaveStatus('Saving...');
      const response = await updateLLMConfig(llmConfig);
      if (response.success) {
        setSaveStatus('✅ Configuration saved successfully!');
        setTimeout(() => setSaveStatus(''), 3000);
      } else {
        setSaveStatus('❌ Failed to save configuration');
      }
    } catch (error) {
      console.error('Failed to save LLM config:', error);
      setSaveStatus('❌ Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="settings-overlay">
      <div className="mechanical-settings-console">
        <div className="console-top-panel">
          <h2 className="console-title">⚙️ BRIEFCASER SETTINGS</h2>
          <MechanicalButton onClick={onClose} style={{ padding: '4px 8px' }}>
            ✕
          </MechanicalButton>
          <div className="panel-rivet rivet-tl"></div>
          <div className="panel-rivet rivet-tr"></div>
        </div>

        {/* Industrial Tab Panel */}
        <div className="settings-tabs-panel">
          <div className="tabs-container">
            {settingsTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSettingsTab(tab.id)}
                className={`settings-tab ${activeSettingsTab === tab.id ? 'active' : ''}`}
              >
                <span className="tab-rivet"></span>
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>
                <span className="tab-indicator"></span>
              </button>
            ))}
          </div>
        </div>

        {/* Settings Content Area */}
        <div className="settings-content-area">
          
          {/* LLM Configuration Tab */}
          {activeSettingsTab === 'llm' && (
            <div className="settings-section">
              <div className="section-header">
                <h3>🤖 LLM PROVIDER CONFIGURATION</h3>
                <div className="header-line"></div>
              </div>
              <p className="section-description">
                Configure the AI model used for document analysis, drafting, and research. 
                Settings are loaded from environment variables and can be overridden here.
              </p>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  LLM PROVIDER:
                </label>
                <div className="control-frame">
                  <select
                    value={llmConfig.provider}
                    onChange={(e) => handleLLMConfigChange('provider', e.target.value)}
                    className="industrial-select"
                  >
                    <option value="openai">OpenAI (GPT-5-mini, GPT-5, GPT-4.1, GPT-3.5)</option>
                    <option value="anthropic">Anthropic (Claude-sonnet-4, claude-sonnet-4.5, claud-opus-1)</option>
                    <option value="groq">Groq (Mixtral, Llama)</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  MODEL:
                </label>
                <div className="control-frame">
                  <select
                    value={llmConfig.model}
                    onChange={(e) => handleLLMConfigChange('model', e.target.value)}
                    className="industrial-select"
                  >
                    {(availableModels[llmConfig.provider] || ['gpt-4']).map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  API KEY:
                </label>
                <div className="control-frame">
                  <input
                    type="password"
                    value={llmConfig.apiKey}
                    onChange={(e) => handleLLMConfigChange('apiKey', e.target.value)}
                    placeholder="Enter API key or use environment variable"
                    className="industrial-input"
                  />
                </div>
                <small className="control-hint">
                  Leave empty to use environment variable ({llmConfig.provider.toUpperCase()}_API_KEY)
                </small>
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  TEMPERATURE: <span className="value-display">{llmConfig.temperature}</span>
                </label>
                <div className="slider-container">
                  <div className="slider-track">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={llmConfig.temperature}
                      onChange={(e) => handleLLMConfigChange('temperature', parseFloat(e.target.value))}
                      className="industrial-slider"
                    />
                    <div className="slider-notches">
                      {[0, 0.25, 0.5, 0.75, 1].map(val => (
                        <div key={val} className="notch" style={{ left: `${val * 100}%` }}></div>
                      ))}
                    </div>
                  </div>
                </div>
                <small className="control-hint">
                  Lower = more focused, Higher = more creative
                </small>
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  MAX TOKENS: <span className="value-display">{llmConfig.maxTokens}</span>
                </label>
                <div className="slider-container">
                  <div className="slider-track">
                    <input
                      type="range"
                      min="500"
                      max="4000"
                      step="100"
                      value={llmConfig.maxTokens}
                      onChange={(e) => handleLLMConfigChange('maxTokens', parseInt(e.target.value))}
                      className="industrial-slider"
                    />
                    <div className="slider-notches">
                      {[500, 1250, 2000, 2750, 3500, 4000].map(val => (
                        <div key={val} className="notch" style={{ left: `${((val - 500) / 3500) * 100}%` }}></div>
                      ))}
                    </div>
                  </div>
                </div>
                <small className="control-hint">
                  Maximum response length
                </small>
              </div>

              {saveStatus && (
                <div className={`status-message ${saveStatus.includes('✅') ? 'success' : 'error'}`}>
                  <span className="status-icon">{saveStatus.includes('✅') ? '✅' : '❌'}</span>
                  {saveStatus}
                </div>
              )}

              <MechanicalButton 
                onClick={saveLLMConfig} 
                variant="success"
                disabled={loading}
                className="save-config-btn"
              >
                {loading ? '⏳ SAVING...' : '💾 SAVE LLM CONFIGURATION'}
              </MechanicalButton>
            </div>
          )}

          {/* General Settings Tab */}
          {activeSettingsTab === 'general' && (
            <div className="settings-section">
              <div className="section-header">
                <h3>⚙️ GENERAL SETTINGS</h3>
                <div className="header-line"></div>
              </div>

              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.autoSave}
                  onToggle={() => handleSettingChange('autoSave', !settings.autoSave)}
                  label="AUTO SAVE DOCUMENTS"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.notifications}
                  onToggle={() => handleSettingChange('notifications', !settings.notifications)}
                  label="ENABLE NOTIFICATIONS"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.darkMode}
                  onToggle={() => handleSettingChange('darkMode', !settings.darkMode)}
                  label="DARK MODE (SOVIET NIGHT SHIFT)"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.debugMode}
                  onToggle={() => handleSettingChange('debugMode', !settings.debugMode)}
                  label="DEBUG MODE (SHOW PHASE DETAILS)"
                />
              </div>
            </div>
          )}

          {/* Legal Configuration Tab */}
          {activeSettingsTab === 'legal' && (
            <div className="settings-section">
              <div className="section-header">
                <h3>⚖️ LEGAL CONFIGURATION</h3>
                <div className="header-line"></div>
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  JURISDICTION:
                </label>
                <div className="control-frame">
                  <select
                    value={settings.jurisdiction}
                    onChange={(e) => handleSettingChange('jurisdiction', e.target.value)}
                    className="industrial-select"
                  >
                    <option value="federal">Federal</option>
                    <option value="state_california">State - California</option>
                    <option value="state_newyork">State - New York</option>
                    <option value="state_texas">State - Texas</option>
                    <option value="county">County</option>
                    <option value="municipal">Municipal</option>
                  </select>
                </div>
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  CITATION STYLE:
                </label>
                <div className="control-frame">
                  <select
                    value={settings.citationStyle}
                    onChange={(e) => handleSettingChange('citationStyle', e.target.value)}
                    className="industrial-select"
                  >
                    <option value="bluebook">Bluebook (Legal Standard)</option>
                    <option value="alwd">ALWD Citation Manual</option>
                    <option value="apa">APA (Academic)</option>
                    <option value="mla">MLA</option>
                  </select>
                </div>
              </div>

              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.strictCompliance}
                  onToggle={() => handleSettingChange('strictCompliance', !settings.strictCompliance)}
                  label="STRICT COMPLIANCE MODE"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.citationValidation}
                  onToggle={() => handleSettingChange('citationValidation', !settings.citationValidation)}
                  label="AUTOMATIC CITATION VALIDATION"
                />
              </div>
            </div>
          )}

          {/* Phase Settings Tab */}
          {activeSettingsTab === 'phase' && (
            <div className="settings-section">
              <div className="section-header">
                <h3>🔄 PHASE EXECUTION SETTINGS</h3>
                <div className="header-line"></div>
              </div>
              <p className="section-description">
                Configure how phases execute and interact with the LLM
              </p>

              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.autoAdvancePhases}
                  onToggle={() => handleSettingChange('autoAdvancePhases', !settings.autoAdvancePhases)}
                  label="AUTO-ADVANCE THROUGH PHASES"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.requirePhaseReview}
                  onToggle={() => handleSettingChange('requirePhaseReview', !settings.requirePhaseReview)}
                  label="REQUIRE REVIEW BEFORE ADVANCING"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.enhancedResearchMode}
                  onToggle={() => handleSettingChange('enhancedResearchMode', !settings.enhancedResearchMode)}
                  label="ENHANCED RESEARCH MODE (MORE LLM CALLS)"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.parallelProcessing}
                  onToggle={() => handleSettingChange('parallelProcessing', !settings.parallelProcessing)}
                  label="PARALLEL EVIDENCE PROCESSING"
                />
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  DRAFTING QUALITY LEVEL:
                </label>
                <div className="control-frame">
                  <select
                    value={settings.draftingQuality || 'standard'}
                    onChange={(e) => handleSettingChange('draftingQuality', e.target.value)}
                    className="industrial-select"
                  >
                    <option value="quick">Quick (Faster, Less Detailed)</option>
                    <option value="standard">Standard (Balanced)</option>
                    <option value="thorough">Thorough (Slower, More Detailed)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Export Settings Tab */}
          {activeSettingsTab === 'export' && (
            <div className="settings-section">
              <div className="section-header">
                <h3>📄 EXPORT CONFIGURATION</h3>
                <div className="header-line"></div>
              </div>

              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.pdfExport}
                  onToggle={() => handleSettingChange('pdfExport', !settings.pdfExport)}
                  label="ENABLE PDF EXPORT"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.docExport}
                  onToggle={() => handleSettingChange('docExport', !settings.docExport)}
                  label="ENABLE DOC EXPORT"
                />
              </div>
              <div className="toggle-group">
                <ToggleSwitch
                  active={settings.markdownExport}
                  onToggle={() => handleSettingChange('markdownExport', !settings.markdownExport)}
                  label="ENABLE MARKDOWN EXPORT"
                />
              </div>

              <div className="control-group">
                <label className="control-label">
                  <span className="label-indicator"></span>
                  DEFAULT EXPORT FORMAT:
                </label>
                <div className="control-frame">
                  <select
                    value={settings.defaultExportFormat}
                    onChange={(e) => handleSettingChange('defaultExportFormat', e.target.value)}
                    className="industrial-select"
                  >
                    <option value="pdf">PDF</option>
                    <option value="doc">DOC</option>
                    <option value="markdown">Markdown</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Industrial Footer with Action Buttons */}
        <div className="console-bottom-panel">
          <div className="panel-rivet rivet-bl"></div>
          <div className="panel-rivet rivet-br"></div>
          <div className="footer-actions">
            <MechanicalButton onClick={onClose} variant="danger">
              CANCEL
            </MechanicalButton>
            <MechanicalButton onClick={onClose} variant="success">
              APPLY & CLOSE
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