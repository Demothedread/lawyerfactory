import { useState } from 'react';
import { MechanicalButton } from '../soviet';
import PropTypes from 'prop-types';

const LegalIntakeForm = ({
  open = false,
  onClose,
  onSubmit,
  initialData = {},
}) => {
  const [formData, setFormData] = useState({
    clientFirstName: '',
    clientMiddleName: '',
    clientLastName: '',
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
    <div className="legal-intake-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="legal-intake-container">
        <div className="legal-pad-header">
          <h2 className="pad-title adobe-display-primary">LEGAL INTAKE FORM</h2>
          <MechanicalButton 
            onClick={onClose} 
            className="enhanced-close-button"
            style={{ 
              padding: '12px 16px',
              fontSize: '24px',
              fontWeight: 'bold',
              minWidth: '48px',
              minHeight: '48px',
              border: '3px solid #333',
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.6), inset 0 2px 0 rgba(255, 255, 255, 0.3)',
              color: '#1a1a1a',
              textShadow: '1px 1px 2px rgba(255, 255, 255, 0.5)'
            }}
          >
            ✕
          </MechanicalButton>
        </div>
        <form onSubmit={handleSubmit} className="legal-pad-form">
          {/* Client Information Section */}
          <div className="form-section">
            <h3 className="adobe-display-secondary">📋 Client Information</h3>
            <div className="name-fields-container" style={{ 
              display: 'grid', 
              gridTemplateColumns: '2fr 1fr 2fr', 
              gap: '12px', 
              marginBottom: '16px' 
            }}>
              <div className="name-field">
                <label className="adobe-body-bold high-contrast-dark">First Name *</label>
                <input
                  type="text"
                  placeholder="First Name"
                  value={formData.clientFirstName}
                  onChange={(e) => handleInputChange('clientFirstName', e.target.value)}
                  className="form-input high-contrast-input"
                  required
                  style={{
                    color: '#1a1a1a',
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #333',
                    fontWeight: '600',
                    fontSize: '16px',
                    textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                  }}
                />
              </div>
              <div className="name-field">
                <label className="adobe-body-bold high-contrast-dark">Middle</label>
                <input
                  type="text"
                  placeholder="Middle"
                  value={formData.clientMiddleName}
                  onChange={(e) => handleInputChange('clientMiddleName', e.target.value)}
                  className="form-input high-contrast-input"
                  style={{
                    color: '#1a1a1a',
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #333',
                    fontWeight: '600',
                    fontSize: '16px',
                    textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                  }}
                />
              </div>
              <div className="name-field">
                <label className="adobe-body-bold high-contrast-dark">Last Name *</label>
                <input
                  type="text"
                  placeholder="Last Name"
                  value={formData.clientLastName}
                  onChange={(e) => handleInputChange('clientLastName', e.target.value)}
                  className="form-input high-contrast-input"
                  required
                  style={{
                    color: '#1a1a1a',
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '2px solid #333',
                    fontWeight: '600',
                    fontSize: '16px',
                    textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                  }}
                />
              </div>
            </div>
            <div className="address-field">
              <label className="adobe-body-bold high-contrast-dark">Client Address</label>
              <textarea
                placeholder="Client Address"
                value={formData.clientAddress}
                onChange={(e) => handleInputChange('clientAddress', e.target.value)}
                className="form-textarea high-contrast-input"
                rows={2}
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '500',
                  fontSize: '16px',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              />
            </div>
          </div>

          {/* Case Information Section */}
          <div className="form-section">
            <h3 className="adobe-display-secondary">⚖️ Case Information</h3>
            <div className="case-field">
              <label className="adobe-body-bold high-contrast-dark">Other Party Name *</label>
              <input
                type="text"
                placeholder="Other Party Name"
                value={formData.otherPartyName}
                onChange={(e) => handleInputChange('otherPartyName', e.target.value)}
                className="form-input high-contrast-input"
                required
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '600',
                  fontSize: '16px',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              />
            </div>
            <div className="role-field">
              <label className="adobe-body-bold high-contrast-dark">Your Role in this Case *</label>
              <select
                value={formData.partyRole}
                onChange={(e) => handleInputChange('partyRole', e.target.value)}
                className="form-select high-contrast-input"
                required
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '600',
                  fontSize: '16px',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              >
                <option value="">Select Role...</option>
                <option value="plaintiff">Plaintiff (Suing)</option>
                <option value="defendant">Defendant (Being Sued)</option>
              </select>
            </div>
            <div className="claim-field">
              <label className="adobe-body-bold high-contrast-dark">Legal Issue Description *</label>
              <textarea
                placeholder="Describe the legal issue in detail..."
                value={formData.claimDescription}
                onChange={(e) => handleInputChange('claimDescription', e.target.value)}
                className="form-textarea high-contrast-input"
                rows={4}
                required
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '500',
                  fontSize: '16px',
                  lineHeight: '1.6',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              />
            </div>
          </div>

          {/* Additional Information */}
          <div className="form-section">
            <h3 className="adobe-display-secondary">📄 Additional Details</h3>
            <div className="details-field">
              <label className="adobe-body-bold high-contrast-dark">Event Location</label>
              <input
                type="text"
                placeholder="Event Location (if applicable)"
                value={formData.eventLocation}
                onChange={(e) => handleInputChange('eventLocation', e.target.value)}
                className="form-input high-contrast-input"
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '500',
                  fontSize: '16px',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              />
            </div>
            <div className="date-field">
              <label className="adobe-body-bold high-contrast-dark">Event Date</label>
              <input
                type="date"
                placeholder="Event Date"
                value={formData.eventDate}
                onChange={(e) => handleInputChange('eventDate', e.target.value)}
                className="form-input high-contrast-input"
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '500',
                  fontSize: '16px',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              />
            </div>
            <div className="agreement-field">
              <label className="adobe-body-bold high-contrast-dark">Agreement Type</label>
              <select
                value={formData.agreementType}
                onChange={(e) => handleInputChange('agreementType', e.target.value)}
                className="form-select high-contrast-input"
                style={{
                  color: '#1a1a1a',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '2px solid #333',
                  fontWeight: '500',
                  fontSize: '16px',
                  textShadow: '0.5px 0.5px 1px rgba(0, 0, 0, 0.2)'
                }}
              >
                <option value="">Agreement Type (if applicable)...</option>
                <option value="contract">Contract</option>
                <option value="lease">Lease</option>
                <option value="employment">Employment</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          {/* Options */}
          <div className="form-section">
            <h3 className="adobe-display-secondary">⚙️ Processing Options</h3>
            <div className="options-container" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label className="checkbox-label-enhanced" style={{ 
                display: 'flex', 
                alignItems: 'center', 
                padding: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                border: '2px solid #666',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
              }}>
                <input
                  type="checkbox"
                  checked={formData.evidenceUpload}
                  onChange={(e) => handleInputChange('evidenceUpload', e.target.checked)}
                  style={{ 
                    marginRight: '12px', 
                    transform: 'scale(1.3)',
                    accentColor: '#333'
                  }}
                />
                <span className="adobe-body-bold high-contrast-dark" style={{ fontSize: '16px' }}>
                  Include evidence upload workflow
                </span>
              </label>
              <label className="checkbox-label-enhanced" style={{ 
                display: 'flex', 
                alignItems: 'center', 
                padding: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                border: '2px solid #666',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
              }}>
                <input
                  type="checkbox"
                  checked={formData.witnesses}
                  onChange={(e) => handleInputChange('witnesses', e.target.checked)}
                  style={{ 
                    marginRight: '12px', 
                    transform: 'scale(1.3)',
                    accentColor: '#333'
                  }}
                />
                <span className="adobe-body-bold high-contrast-dark" style={{ fontSize: '16px' }}>
                  Include witness management
                </span>
              </label>
              <label className="checkbox-label-enhanced" style={{ 
                display: 'flex', 
                alignItems: 'center', 
                padding: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                border: '2px solid #666',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
              }}>
                <input
                  type="checkbox"
                  checked={formData.roughDraft}
                  onChange={(e) => handleInputChange('roughDraft', e.target.checked)}
                  style={{ 
                    marginRight: '12px', 
                    transform: 'scale(1.3)',
                    accentColor: '#333'
                  }}
                />
                <span className="adobe-body-bold high-contrast-dark" style={{ fontSize: '16px' }}>
                  Generate rough draft automatically
                </span>
              </label>
            </div>
          </div>

          {/* Form Actions */}
          <div className="form-actions" style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            gap: '20px',
            marginTop: '24px',
            padding: '20px 0'
          }}>
            <MechanicalButton 
              type="button" 
              onClick={onClose} 
              variant="danger"
              style={{
                minHeight: '50px',
                padding: '14px 32px',
                fontSize: '16px',
                fontWeight: '700',
                border: '3px solid #d32f2f',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(211, 47, 47, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                textShadow: '1px 1px 2px rgba(0, 0, 0, 0.3)',
                backgroundColor: 'rgba(255, 205, 205, 0.9)',
                color: '#1a1a1a',
                transition: 'all 0.2s ease',
                position: 'relative',
                flex: '1'
              }}
            >
              <span className="adobe-body-bold">Cancel</span>
            </MechanicalButton>
            <MechanicalButton 
              type="submit" 
              variant="success"
              style={{
                minHeight: '50px',
                padding: '14px 32px',
                fontSize: '16px',
                fontWeight: '700',
                border: '3px solid #2e7d32',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(46, 125, 50, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                textShadow: '1px 1px 2px rgba(0, 0, 0, 0.4)',
                background: 'linear-gradient(145deg, #c8e6c9, #a5d6a7)',
                color: '#1a1a1a',
                transition: 'all 0.2s ease',
                position: 'relative',
                flex: '1'
              }}
            >
              <span className="adobe-display-secondary">Initialize Legal Process</span>
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