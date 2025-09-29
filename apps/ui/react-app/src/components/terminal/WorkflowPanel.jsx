// WorkflowPanel - Professional workflow control panel component
import React from 'react';
import PropTypes from 'prop-types';
import { MetalPanel, AnalogGauge, ToggleSwitch, NixieDisplay, MechanicalButton, StatusLights } from '../soviet';

const WorkflowPanel = ({
  leftPanelCollapsed = false,
  onToggleLeftPanel,
  onLegalIntakeSubmit,
  onSettingsOpen,
  systemStatus = ['green', 'green', 'amber', 'red', 'red'],
  overallProgress = 25,
  phases = [],
  onPhaseSelect,
  userResearchFiles = [],
  onResearchUpload,
}) => {
  if (leftPanelCollapsed) {
    return (
      <div className="collapsed-panel">
        WF
      </div>
    );
  }

  return (
    <div className="workflow-container">
      {/* Quick Actions */}
      <div className="workflow-actions">
        <MechanicalButton
          onClick={onLegalIntakeSubmit}
          variant="success"
          style={{ width: '100%', marginBottom: 'var(--space-sm)' }}
        >
          📋 Start Intake
        </MechanicalButton>
        <MechanicalButton
          onClick={onSettingsOpen}
          variant="default"
          style={{ width: '100%', marginBottom: 'var(--space-md)' }}
        >
          ⚙️ Settings
        </MechanicalButton>
      </div>

      {/* System Metrics */}
      <MetalPanel title="System Status">
        <StatusLights statuses={systemStatus} />
        <div className="metrics-display">
          <AnalogGauge
            value={overallProgress}
            label="Overall"
            max={100}
          />
          <div className="phase-counter">
            <NixieDisplay
              value={phases.filter(p => p.status === 'completed').length}
              digits={1}
            />
            <span style={{ margin: '0 8px' }}>/</span>
            <NixieDisplay
              value={phases.length}
              digits={1}
            />
          </div>
        </div>
      </MetalPanel>

      {/* Phase Control */}
      <MetalPanel title="Phase Control">
        <div className="phase-list">
          {phases.map((phase) => (
            <div
              key={phase.id}
              className={`phase-item phase-${phase.status}`}
            >
              <div className="phase-header">
                <span className="phase-icon">{phase.icon}</span>
                <span className="phase-id">{phase.id}</span>
                <div className={`status-light ${
                  phase.status === 'completed' ? 'green' :
                  phase.status === 'active' ? 'amber' : 'red'
                }`} />
              </div>
              <div className="phase-name">{phase.name}</div>
              <div className="phase-progress">
                <div
                  className="progress-bar"
                  style={{ width: `${phase.progress}%` }}
                />
              </div>
              <div className="phase-actions">
                {phase.status === 'pending' && (
                  <MechanicalButton
                    onClick={() => onPhaseSelect(phase.id)}
                    variant="default"
                    style={{ fontSize: '10px', padding: '4px 8px' }}
                  >
                    Start
                  </MechanicalButton>
                )}
                {phase.status === 'active' && (
                  <MechanicalButton
                    onClick={() => onPhaseSelect(null)}
                    variant="success"
                    style={{ fontSize: '10px', padding: '4px 8px' }}
                  >
                    Complete
                  </MechanicalButton>
                )}
              </div>
            </div>
          ))}
        </div>
      </MetalPanel>

      {/* Research Upload Section */}
      <MetalPanel title="Research Files">
        <div
          className="upload-zone"
          onDrop={(e) => {
            e.preventDefault();
            onResearchUpload(e.dataTransfer.files);
          }}
          onDragOver={(e) => e.preventDefault()}
        >
          <div className="upload-icon">📎</div>
          <div>Drop research files here</div>
          <input
            type="file"
            multiple
            onChange={(e) => onResearchUpload(e.target.files)}
            style={{ display: 'none' }}
            id="research-upload"
          />
          <MechanicalButton
            onClick={() => document.getElementById('research-upload').click()}
            variant="default"
            style={{ marginTop: 'var(--space-sm)', fontSize: '11px' }}
          >
            Browse Files
          </MechanicalButton>
        </div>
        {userResearchFiles.length > 0 && (
          <div className="research-files">
            {userResearchFiles.slice(-3).map((file) => (
              <div key={file.id} className="research-file-item">
                <span className="file-icon">📄</span>
                <span className="file-name">{file.name}</span>
              </div>
            ))}
          </div>
        )}
      </MetalPanel>
    </div>
  );
};

WorkflowPanel.propTypes = {
  leftPanelCollapsed: PropTypes.bool,
  onToggleLeftPanel: PropTypes.func,
  onLegalIntakeSubmit: PropTypes.func,
  onSettingsOpen: PropTypes.func,
  systemStatus: PropTypes.array,
  overallProgress: PropTypes.number,
  phases: PropTypes.array,
  onPhaseSelect: PropTypes.func,
  userResearchFiles: PropTypes.array,
  onResearchUpload: PropTypes.func,
};

export default WorkflowPanel;