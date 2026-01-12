import { useEffect, useState } from 'react';
import { getIcon } from '../../constants/thematicIcons';
import { fetchLLMConfig, updateLLMConfig } from '../../services/backendService';
import { MechanicalButton, ToggleSwitch } from '../soviet';

const EnhancedSettingsPanel = ({
  open = false,
  onClose,
  settings = {},
  onSettingsChange,
}) => {
  const [activeSettingsTab, setActiveSettingsTab] = useState('llm');
  const [llmConfig, setLLMConfig] = useState({
    provider: 'openai',
    model: 'gpt-5-nano',
    apiKey: '',
    temperature: 0.1,
    maxTokens: 2000,
  });
  const [availableModels, setAvailableModels] = useState({});
  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  const settingsTabs = [
    { id: 'llm', label: 'LLM Configuration', icon: getIcon('llm') },
    { id: 'general', label: 'General', icon: getIcon('settings') },
    { id: 'legal', label: 'Legal Config', icon: getIcon('legal') },
    { id: 'phase', label: 'Phase Settings', icon: getIcon('workflow') },
    { id: 'export', label: 'Export', icon: getIcon('export') },
  ];

  // Load LLM config from backend (includes env variables)
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
          model: response.config.model || 'gpt-4',
          apiKey: response.config.api_key || '',
          temperature: response.config.temperature || 0.1,
          maxTokens: response.config.max_tokens || 2000,
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
    <div className="legal-intake-overlay">
      <div className="legal-intake-container" style={{ maxWidth: '700px', maxHeight: '80vh', overflow: 'auto' }}>
        <div className="legal-pad-header">
          <h2 className="pad-title">{getIcon('settings')} BRIEFCASER SETTINGS</h2>
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
                  fontSize: '11px',
                  padding: '6px 10px',
                  margin: '2px',
                }}
              >
                {tab.icon} {tab.label}
              </MechanicalButton>
            ))}
          </div>

          <div className="settings-content" style={{ marginTop: 'var(--space-md)' }}>
            {/* LLM Configuration Tab */}
            {activeSettingsTab === 'llm' && (
              <div>
                <h4>{getIcon('llm')} LLM Provider Configuration</h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-md)' }}>
                  Configure the AI model used for document analysis, drafting, and research. 
                  Settings are loaded from environment variables and can be overridden here.
                </p>

                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontWeight: 'bold' }}>
                    LLM Provider:
                  </label>
                  <select
                    value={llmConfig.provider}
                    onChange={(e) => handleLLMConfigChange('provider', e.target.value)}
                    className="settings-select"
                    style={{ width: '100%', padding: '8px', fontSize: '14px' }}
                  >
                    <option value="openai">OpenAI (GPT-4, GPT-3.5)</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="groq">Groq (Mixtral, Llama)</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>

                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontWeight: 'bold' }}>
                    Model:
                  </label>
                  <select
                    value={llmConfig.model}
                    onChange={(e) => handleLLMConfigChange('model', e.target.value)}
                    className="settings-select"
                    style={{ width: '100%', padding: '8px', fontSize: '14px' }}
                  >
                    {(availableModels[llmConfig.provider] || ['gpt-4']).map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                </div>

                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontWeight: 'bold' }}>
                    API Key:
                  </label>
                  <input
                    type="password"
                    value={llmConfig.apiKey}
                    onChange={(e) => handleLLMConfigChange('apiKey', e.target.value)}
                    placeholder="Enter API key or use environment variable"
                    className="settings-input"
                    style={{ width: '100%', padding: '8px', fontSize: '14px' }}
                  />
                  <small style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    Leave empty to use environment variable ({llmConfig.provider.toUpperCase()}_API_KEY)
                  </small>
                </div>

                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontWeight: 'bold' }}>
                    Temperature: {llmConfig.temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={llmConfig.temperature}
                    onChange={(e) => handleLLMConfigChange('temperature', parseFloat(e.target.value))}
                    style={{ width: '100%' }}
                  />
                  <small style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    Lower = more focused, Higher = more creative
                  </small>
                </div>

                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontWeight: 'bold' }}>
                    Max Tokens: {llmConfig.maxTokens}
                  </label>
                  <input
                    type="range"
                    min="500"
                    max="4000"
                    step="100"
                    value={llmConfig.maxTokens}
                    onChange={(e) => handleLLMConfigChange('maxTokens', parseInt(e.target.value))}
                    style={{ width: '100%' }}
                  />
                  <small style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    Maximum response length
                  </small>
                </div>

                {saveStatus && (
                  <div style={{ 
                    padding: '8px', 
                    marginBottom: 'var(--space-md)', 
                    backgroundColor: saveStatus.includes('✓') ? '#d4edda' : '#f8d7da',
                    color: saveStatus.includes('✓') ? '#155724' : '#721c24',
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}>
                    {saveStatus}
                  </div>
                )}

                <MechanicalButton 
                  onClick={saveLLMConfig} 
                  variant="success"
                  disabled={loading}
                  style={{ width: '100%' }}
                >
                  {loading ? '⏳ Saving...' : `${getIcon('save')} Save LLM Configuration`}
                </MechanicalButton>
              </div>
            )}

            {/* General Settings Tab */}
            {activeSettingsTab === 'general' && (
              <div>
                <h4>General Settings</h4>
                <ToggleSwitch
                  active={settings.autoSave}
                  onToggle={() => handleSettingChange('autoSave', !settings.autoSave)}
                  label="Auto Save Documents"
                />
                <ToggleSwitch
                  active={settings.notifications}
                  onToggle={() => handleSettingChange('notifications', !settings.notifications)}
                  label="Enable Notifications"
                />
                <ToggleSwitch
                  active={settings.darkMode}
                  onToggle={() => handleSettingChange('darkMode', !settings.darkMode)}
                  label="Dark Mode (Soviet Night Shift)"
                />
                <ToggleSwitch
                  active={settings.debugMode}
                  onToggle={() => handleSettingChange('debugMode', !settings.debugMode)}
                  label="Debug Mode (Show Phase Details)"
                />
              </div>
            )}

            {/* Legal Configuration Tab */}
            {activeSettingsTab === 'legal' && (
              <div>
                <h4>{getIcon('legal')} Legal Configuration</h4>
                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Jurisdiction:
                  </label>
                  <select
                    value={settings.jurisdiction}
                    onChange={(e) => handleSettingChange('jurisdiction', e.target.value)}
                    className="settings-select"
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <option value="federal">Federal</option>
                    <option value="state_california">State - California</option>
                    <option value="state_newyork">State - New York</option>
                    <option value="state_texas">State - Texas</option>
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
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <option value="bluebook">Bluebook (Legal Standard)</option>
                    <option value="alwd">ALWD Citation Manual</option>
                    <option value="apa">APA (Academic)</option>
                    <option value="mla">MLA</option>
                  </select>
                </div>
                <ToggleSwitch
                  active={settings.strictCompliance}
                  onToggle={() => handleSettingChange('strictCompliance', !settings.strictCompliance)}
                  label="Strict Compliance Mode"
                />
                <ToggleSwitch
                  active={settings.citationValidation}
                  onToggle={() => handleSettingChange('citationValidation', !settings.citationValidation)}
                  label="Automatic Citation Validation"
                />
              </div>
            )}

            {/* Phase Settings Tab */}
            {activeSettingsTab === 'phase' && (
              <div>
                <h4>{getIcon('workflow')} Phase Execution Settings</h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-md)' }}>
                  Configure how phases execute and interact with the LLM
                </p>
                <ToggleSwitch
                  active={settings.autoAdvancePhases}
                  onToggle={() => handleSettingChange('autoAdvancePhases', !settings.autoAdvancePhases)}
                  label="Auto-Advance Through Phases"
                />
                <ToggleSwitch
                  active={settings.requirePhaseReview}
                  onToggle={() => handleSettingChange('requirePhaseReview', !settings.requirePhaseReview)}
                  label="Require Review Before Advancing"
                />
                <ToggleSwitch
                  active={settings.enhancedResearchMode}
                  onToggle={() => handleSettingChange('enhancedResearchMode', !settings.enhancedResearchMode)}
                  label="Enhanced Research Mode (More LLM Calls)"
                />
                <ToggleSwitch
                  active={settings.parallelProcessing}
                  onToggle={() => handleSettingChange('parallelProcessing', !settings.parallelProcessing)}
                  label="Parallel Evidence Processing"
                />
                <div style={{ marginTop: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Drafting Quality Level:
                  </label>
                  <select
                    value={settings.draftingQuality || 'standard'}
                    onChange={(e) => handleSettingChange('draftingQuality', e.target.value)}
                    className="settings-select"
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <option value="quick">Quick (Faster, Less Detailed)</option>
                    <option value="standard">Standard (Balanced)</option>
                    <option value="thorough">Thorough (Slower, More Detailed)</option>
                  </select>
                </div>
              </div>
            )}

            {/* Export Settings Tab */}
            {activeSettingsTab === 'export' && (
              <div>
                <h4>{getIcon('export')} Export Configuration</h4>
                <ToggleSwitch
                  active={settings.pdfExport}
                  onToggle={() => handleSettingChange('pdfExport', !settings.pdfExport)}
                  label="Enable PDF Export"
                />
                <ToggleSwitch
                  active={settings.docExport}
                  onToggle={() => handleSettingChange('docExport', !settings.docExport)}
                  label="Enable DOC Export"
                />
                <ToggleSwitch
                  active={settings.markdownExport}
                  onToggle={() => handleSettingChange('markdownExport', !settings.markdownExport)}
                  label="Enable Markdown Export"
                />
                <div style={{ marginTop: 'var(--space-md)' }}>
                  <label style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
                    Default Export Format:
                  </label>
                  <select
                    value={settings.defaultExportFormat}
                    onChange={(e) => handleSettingChange('defaultExportFormat', e.target.value)}
                    className="settings-select"
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <option value="pdf">PDF</option>
                    <option value="doc">DOC</option>
                    <option value="markdown">Markdown</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          <div className="form-actions" style={{ marginTop: 'var(--space-lg)' }}>
            <MechanicalButton onClick={onClose} variant="danger">
              {getIcon('delete')} Cancel
            </MechanicalButton>
            <MechanicalButton onClick={onClose} variant="success">
              {getIcon('complete')} Apply {getIcon('forward')} Close
            </MechanicalButton>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedSettingsPanel;
