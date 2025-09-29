// LegalIntakeForm - Professional legal intake form component
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { MechanicalButton } from '../soviet';

const LegalIntakeForm = ({
  open = false,
  onClose,
  onSubmit,
  initialData = {},
}) => {
  const [formData, setFormData] = useState({
    clientName: '',
    clientAddress: '',
    otherPartyName: '',
    otherPartyAddress: '',
    partyRole: '',
    eventLocation: '',
    eventDate: '',
    agreementType: '',
    evidenceUpload: false,
    witnesses: false,
    roughDraft: false,
    claimDescription: '',
    selectedCauses: [],
    ...initialData,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (!open) return null;

  return (
    <div className="legal-intake-overlay">
      <div className="legal-intake-container">
        <div className="legal-pad-header">
          <h2 className="pad-title">LEGAL INTAKE FORM</h2>
          <MechanicalButton onClick={onClose} style={{ padding: '4px 8px' }}>
            ✕
          </MechanicalButton>
        </div>
        <form onSubmit={handleSubmit} className="legal-pad-form">
          {/* Client Information Section */}
          <div className="form-section">
            <h3>📋 Client Information</h3>
            <input
              type="text"
              placeholder="Client Name"
              value={formData.clientName}
              onChange={(e) => handleInputChange('clientName', e.target.value)}
              className="form-input"
              required
            />
            <textarea
              placeholder="Client Address"
              value={formData.clientAddress}
              onChange={(e) => handleInputChange('clientAddress', e.target.value)}
              className="form-textarea"
              rows={2}
            />
          </div>

          {/* Case Information Section */}
          <div className="form-section">
            <h3>⚖️ Case Information</h3>
            <input
              type="text"
              placeholder="Other Party Name"
              value={formData.otherPartyName}
              onChange={(e) => handleInputChange('otherPartyName', e.target.value)}
              className="form-input"
              required
            />
            <select
              value={formData.partyRole}
              onChange={(e) => handleInputChange('partyRole', e.target.value)}
              className="form-select"
              required
            >
              <option value="">Select Role...</option>
              <option value="plaintiff">Plaintiff (Suing)</option>
              <option value="defendant">Defendant (Being Sued)</option>
            </select>
            <textarea
              placeholder="Describe the legal issue in detail..."
              value={formData.claimDescription}
              onChange={(e) => handleInputChange('claimDescription', e.target.value)}
              className="form-textarea"
              rows={4}
              required
            />
          </div>

          {/* Additional Information */}
          <div className="form-section">
            <h3>📄 Additional Details</h3>
            <input
              type="text"
              placeholder="Event Location (if applicable)"
              value={formData.eventLocation}
              onChange={(e) => handleInputChange('eventLocation', e.target.value)}
              className="form-input"
            />
            <input
              type="date"
              placeholder="Event Date"
              value={formData.eventDate}
              onChange={(e) => handleInputChange('eventDate', e.target.value)}
              className="form-input"
            />
            <select
              value={formData.agreementType}
              onChange={(e) => handleInputChange('agreementType', e.target.value)}
              className="form-select"
            >
              <option value="">Agreement Type (if applicable)...</option>
              <option value="contract">Contract</option>
              <option value="lease">Lease</option>
              <option value="employment">Employment</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Options */}
          <div className="form-section">
            <h3>⚙️ Processing Options</h3>
            <label style={{ display: 'block', marginBottom: 'var(--space-sm)' }}>
              <input
                type="checkbox"
                checked={formData.evidenceUpload}
                onChange={(e) => handleInputChange('evidenceUpload', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              Include evidence upload workflow
            </label>
            <label style={{ display: 'block', marginBottom: 'var(--space-sm)' }}>
              <input
                type="checkbox"
                checked={formData.witnesses}
                onChange={(e) => handleInputChange('witnesses', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              Include witness management
            </label>
            <label style={{ display: 'block', marginBottom: 'var(--space-sm)' }}>
              <input
                type="checkbox"
                checked={formData.roughDraft}
                onChange={(e) => handleInputChange('roughDraft', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              Generate rough draft automatically
            </label>
          </div>

          {/* Form Actions */}
          <div className="form-actions">
            <MechanicalButton type="button" onClick={onClose} variant="danger">
              Cancel
            </MechanicalButton>
            <MechanicalButton type="submit" variant="success">
              Submit Intake
            </MechanicalButton>
          </div>
        </form>
      </div>
    </div>
  );
};

LegalIntakeForm.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  onSubmit: PropTypes.func,
  initialData: PropTypes.object,
};

export default LegalIntakeForm;