// LawsuitWizard component for guiding users through lawsuit creation process
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Person,
  Gavel,
  Description,
  Search,
  CheckCircle,
  ArrowBack,
  ArrowForward,
  HelpOutline
} from '@mui/icons-material';
import { useToast } from '../feedback/Toast';
import TooltipGuide from '../guidance/TooltipGuide';
import EvidenceUpload from '../ui/EvidenceUpload';

const STEPS = [
  {
    id: 'client-info',
    label: 'Client Information',
    icon: <Person />,
    description: 'Gather basic information about your client'
  },
  {
    id: 'case-details',
    label: 'Case Details',
    icon: <Gavel />,
    description: 'Define the legal matter and jurisdiction'
  },
  {
    id: 'evidence-collection',
    label: 'Evidence Collection',
    icon: <Search />,
    description: 'Identify and organize supporting evidence'
  },
  {
    id: 'document-drafting',
    label: 'Document Drafting',
    icon: <Description />,
    description: 'Generate legal documents and filings'
  },
  {
    id: 'review-submit',
    label: 'Review & Submit',
    icon: <CheckCircle />,
    description: 'Final review and submission preparation'
  }
];

const LawsuitWizard = ({
  onComplete,
  onCancel,
  initialData = {},
  apiEndpoint = '/api/lawsuit'
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState({
    clientInfo: {
      name: '',
      address: '',
      phone: '',
      email: '',
      ...initialData.clientInfo
    },
    caseDetails: {
      caseType: '',
      jurisdiction: '',
      description: '',
      parties: [],
      ...initialData.caseDetails
    },
    evidence: {
      documents: [],
      witnesses: [],
      timeline: [],
      ...initialData.evidence
    },
    documents: {
      complaint: null,
      motions: [],
      discovery: [],
      ...initialData.documents
    },
    review: {
      checklist: [],
      notes: '',
      ...initialData.review
    }
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const { addToast } = useToast();

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleStepClick = (stepIndex) => {
    // Allow navigation to completed steps or current step
    if (stepIndex <= activeStep) {
      setActiveStep(stepIndex);
    }
  };

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 0: // Client Info
        if (!formData.clientInfo.name.trim()) {
          newErrors.name = 'Client name is required';
        }
        if (!formData.clientInfo.email.trim()) {
          newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.clientInfo.email)) {
          newErrors.email = 'Please enter a valid email';
        }
        break;

      case 1: // Case Details
        if (!formData.caseDetails.caseType) {
          newErrors.caseType = 'Case type is required';
        }
        if (!formData.caseDetails.jurisdiction) {
          newErrors.jurisdiction = 'Jurisdiction is required';
        }
        if (!formData.caseDetails.description.trim()) {
          newErrors.description = 'Case description is required';
        }
        break;

      default:
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));

    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Enhanced API call with retry logic and timeout
  const apiCallWithRetry = async (url, options, maxRetries = 3, timeout = 30000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          return response;
        } else if (response.status >= 500 && attempt < maxRetries) {
          // Retry on server errors
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000); // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        clearTimeout(timeoutId);

        if (error.name === 'AbortError') {
          throw new Error(`Request timeout after ${timeout}ms`);
        }

        if (attempt === maxRetries) {
          throw error;
        }

        // Exponential backoff for retries
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const response = await apiCallWithRetry(
        apiEndpoint,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData),
        },
        3, // maxRetries
        30000 // timeout in ms
      );

      const result = await response.json().catch(() => ({}));

      addToast('Lawsuit created successfully!', {
        severity: 'success',
        title: 'Success'
      });

      if (onComplete) {
        onComplete(formData);
      }
    } catch (error) {
      console.error('Lawsuit creation failed:', error);

      let errorMessage = 'Failed to create lawsuit. Please try again.';
      let errorTitle = 'Error';

      if (error.message.includes('timeout')) {
        errorMessage = 'Request timed out. Please check your connection and try again.';
        errorTitle = 'Timeout Error';
      } else if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
        errorMessage = 'Network error. Please check your internet connection.';
        errorTitle = 'Network Error';
      } else if (error.message.includes('HTTP 5')) {
        errorMessage = 'Server error. Please try again in a few moments.';
        errorTitle = 'Server Error';
      }

      addToast(errorMessage, {
        severity: 'error',
        title: errorTitle
      });
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <ClientInfoStep
            data={formData.clientInfo}
            onChange={(field, value) => handleInputChange('clientInfo', field, value)}
            errors={errors}
          />
        );
      case 1:
        return (
          <CaseDetailsStep
            data={formData.caseDetails}
            onChange={(field, value) => handleInputChange('caseDetails', field, value)}
            errors={errors}
          />
        );
      case 2:
        return (
          <EvidenceCollectionStep
            data={formData.evidence}
            onChange={(field, value) => handleInputChange('evidence', field, value)}
          />
        );
      case 3:
        return (
          <DocumentDraftingStep
            data={formData.documents}
            onChange={(field, value) => handleInputChange('documents', field, value)}
          />
        );
      case 4:
        return (
          <ReviewSubmitStep
            data={formData}
            onChange={(field, value) => handleInputChange('review', field, value)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto', p: 2 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom align="center">
          Lawsuit Creation Wizard
        </Typography>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {STEPS.map((step, index) => (
            <Step key={step.id} completed={index < activeStep}>
              <StepLabel
                onClick={() => handleStepClick(index)}
                sx={{
                  cursor: index <= activeStep ? 'pointer' : 'default',
                  '& .MuiStepLabel-label': {
                    fontSize: '0.875rem'
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {step.icon}
                  <Box>
                    <Typography variant="subtitle2">{step.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {step.description}
                    </Typography>
                  </Box>
                </Box>
              </StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mt: 2, mb: 4 }}>
          {renderStepContent(activeStep)}
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
            startIcon={<ArrowBack />}
          >
            Back
          </Button>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button onClick={onCancel} variant="outlined">
              Cancel
            </Button>

            {activeStep === STEPS.length - 1 ? (
              <Button
                variant="contained"
                color="primary"
                onClick={handleComplete}
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Complete Lawsuit'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<ArrowForward />}
              >
                Next
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

// Step Components
const ClientInfoStep = ({ data, onChange, errors }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Client Information
      <TooltipGuide
        title="Client Information"
        content="Enter your client's basic contact information. This will be used throughout the lawsuit process."
        type="info"
      />
    </Typography>

    <Grid container spacing={3}>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Full Name"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          error={!!errors.name}
          helperText={errors.name}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Phone Number"
          value={data.phone}
          onChange={(e) => onChange('phone', e.target.value)}
        />
      </Grid>
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Email Address"
          type="email"
          value={data.email}
          onChange={(e) => onChange('email', e.target.value)}
          error={!!errors.email}
          helperText={errors.email}
          required
        />
      </Grid>
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Address"
          multiline
          rows={3}
          value={data.address}
          onChange={(e) => onChange('address', e.target.value)}
        />
      </Grid>
    </Grid>
  </Box>
);

const CaseDetailsStep = ({ data, onChange, errors }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Case Details
      <TooltipGuide
        title="Case Details"
        content="Define the type of legal matter, jurisdiction, and provide a detailed description of the case."
        type="info"
      />
    </Typography>

    <Grid container spacing={3}>
      <Grid item xs={12} sm={6}>
        <FormControl fullWidth error={!!errors.caseType}>
          <InputLabel>Case Type</InputLabel>
          <Select
            value={data.caseType}
            onChange={(e) => onChange('caseType', e.target.value)}
            label="Case Type"
          >
            <MenuItem value="personal-injury">Personal Injury</MenuItem>
            <MenuItem value="contract-dispute">Contract Dispute</MenuItem>
            <MenuItem value="employment">Employment</MenuItem>
            <MenuItem value="property">Property Dispute</MenuItem>
            <MenuItem value="other">Other</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={12} sm={6}>
        <FormControl fullWidth error={!!errors.jurisdiction}>
          <InputLabel>Jurisdiction</InputLabel>
          <Select
            value={data.jurisdiction}
            onChange={(e) => onChange('jurisdiction', e.target.value)}
            label="Jurisdiction"
          >
            <MenuItem value="federal">Federal Court</MenuItem>
            <MenuItem value="state">State Court</MenuItem>
            <MenuItem value="county">County Court</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Case Description"
          multiline
          rows={4}
          value={data.description}
          onChange={(e) => onChange('description', e.target.value)}
          error={!!errors.description}
          helperText={errors.description}
          placeholder="Provide a detailed description of the case, including what happened, when, and why you're seeking legal action..."
          required
        />
      </Grid>
    </Grid>
  </Box>
);
const EvidenceCollectionStep = ({ data, onChange }) => {
  const { addToast } = useToast();
  
  const handleUploadComplete = (uploadedFiles) => {
    // Update evidence documents array
    const newDocuments = uploadedFiles.map(file => ({
      id: file.objectId,
      name: file.name,
      objectId: file.objectId,
      evidenceId: file.evidenceId,
      s3Url: file.s3Url,
      uploadDate: new Date().toISOString(),
    }));
    
    onChange('documents', [...data.documents, ...newDocuments]);
    
    addToast(`✅ ${uploadedFiles.length} documents added to evidence`, {
      severity: 'success',
      title: 'Evidence Updated',
    });
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Evidence Collection
        <TooltipGuide
          title="Evidence Collection"
          content="Upload documents, identify witnesses, and create a timeline of events to strengthen your case."
          type="tip"
        />
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        Upload supporting documents such as contracts, correspondence, photos, or any evidence relevant to your case.
      </Alert>

      {/* Integrated Evidence Upload */}
      <Box sx={{ mb: 3 }}>
        <EvidenceUpload
          onUploadComplete={handleUploadComplete}
          currentCaseId={null} // Will be set when case is created
          sourcePhase="phaseA01_intake"
          apiEndpoint="/api/storage/documents"
        />
      </Box>

      {/* Evidence Summary */}
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Evidence Summary</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Chip
                label={`${data.documents.length} Documents`}
                color={data.documents.length > 0 ? 'success' : 'default'}
                sx={{ width: '100%' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Chip
                label={`${data.witnesses.length} Witnesses`}
                color={data.witnesses.length > 0 ? 'success' : 'default'}
                sx={{ width: '100%' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Chip
                label={`${data.timeline.length} Timeline Events`}
                color={data.timeline.length > 0 ? 'success' : 'default'}
                sx={{ width: '100%' }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};


const DocumentDraftingStep = ({ data, onChange }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Document Drafting
      <TooltipGuide
        title="Document Drafting"
        content="The system will generate legal documents based on the information provided. Review and customize as needed."
        type="info"
      />
    </Typography>

    <Alert severity="success" sx={{ mb: 3 }}>
      Legal documents will be automatically generated based on your case details and evidence.
    </Alert>

    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      <Chip label="Complaint" color={data.complaint ? 'success' : 'default'} />
      <Chip label="Motions" color={data.motions.length > 0 ? 'success' : 'default'} />
      <Chip label="Discovery Requests" color={data.discovery.length > 0 ? 'success' : 'default'} />
    </Box>
  </Box>
);

const ReviewSubmitStep = ({ data, onChange }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Review & Submit
      <TooltipGuide
        title="Final Review"
        content="Review all information before submitting. Make sure everything is accurate and complete."
        type="warning"
      />
    </Typography>

    <Alert severity="warning" sx={{ mb: 3 }}>
      Please review all information carefully. Once submitted, you can still make edits but it's best to get it right the first time.
    </Alert>

    <Grid container spacing={3}>
      <Grid item xs={12} sm={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Client Info</Typography>
            <Typography>Name: {data.clientInfo.name}</Typography>
            <Typography>Email: {data.clientInfo.email}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Case Details</Typography>
            <Typography>Type: {data.caseDetails.caseType}</Typography>
            <Typography>Jurisdiction: {data.caseDetails.jurisdiction}</Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>

    <TextField
      fullWidth
      multiline
      rows={3}
      label="Additional Notes"
      value={data.review.notes}
      onChange={(e) => onChange('notes', e.target.value)}
      sx={{ mt: 3 }}
      placeholder="Any additional notes or special instructions..."
    />
  </Box>
);

export default LawsuitWizard;