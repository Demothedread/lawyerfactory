// Phase Pipeline component for workflow visualization and control
import {
    Assessment,
    CheckCircle,
    Close,
    CloudUpload,
    Description,
    Edit,
    Error,
    ExpandMore,
    Gavel,
    Pause,
    PlayArrow,
    Schedule,
    Search,
    Stop,
    Timeline,
    Visibility,
} from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Step,
    StepContent,
    StepLabel,
    Stepper,
    Tab,
    Tabs,
    Tooltip,
    Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useToast } from "../feedback/Toast";
import EvidenceUpload from "./EvidenceUpload";

// Import unified backend service
import backendService from "../../services/backendService";

// Import the new drafting phase components
import DraftingPhase from "../DraftingPhase";

// Import phase detail components
import PhaseA01Intake from "../phases/PhaseA01Intake";
import PhaseA02Research from "../phases/PhaseA02Research";
import PhaseA03Outline from "../phases/PhaseA03Outline";
import PhaseB01Review from "../phases/PhaseB01Review";
import PhaseC01Editing from "../phases/PhaseC01Editing";
import PhaseC02Orchestration from "../phases/PhaseC02Orchestration";

// Import neon Soviet styles
import "../../styles/neon-soviet.css";

const PhasePipeline = ({
  caseId,
  onPhaseComplete,
  onPhaseError,
  autoAdvance = true,
  socketEndpoint = "/phases",
  llmConfig = {}, // LLM configuration from settings
}) => {
  const [phases, setPhases] = useState([]);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [phaseStates, setPhaseStates] = useState({});
  const [pipelineStatus, setPipelineStatus] = useState("idle"); // idle, running, paused, completed, error
  const [selectedPhase, setSelectedPhase] = useState(null);
  const [showPhaseDetails, setShowPhaseDetails] = useState(false);
  const [socket, setSocket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showEvidenceUpload, setShowEvidenceUpload] = useState(false);
  const [retryCount, setRetryCount] = useState({});
  const [maxRetries] = useState(3);
  const [activeTab, setActiveTab] = useState(0); // 0: Pipeline, 1: Drafting Phase
  const [viewMode, setViewMode] = useState('neon'); // 'stepper' or 'neon'
  const [phaseSubSteps, setPhaseSubSteps] = useState({}); // Track sub-step progress within phases

  const { addToast } = useToast();

  // Phase definitions with enhanced metadata
  const phaseDefinitions = [
    {
      id: "phaseA01_intake",
      name: "Document Intake",
      description: "Categorize and extract facts from uploaded documents",
      icon: <Description />,
      color: "primary",
      estimatedTime: "2-5 minutes",
      agent: "Reader Bot",
      outputs: [
        "Document categorization",
        "Fact extraction",
        "Initial metadata",
      ],
      subSteps: ["Uploading", "Processing", "Vectorizing", "Extracting Facts"],
    },
    {
      id: "phaseA02_research",
      name: "Legal Research",
      description: "Gather authorities and legal precedents",
      icon: <Search />,
      color: "info",
      estimatedTime: "5-10 minutes",
      agent: "Paralegal & Researcher Bots",
      outputs: ["Case law", "Statutes", "Legal authorities", "Research matrix"],
      subSteps: ["Searching", "Analyzing", "Ranking", "Validating"],
    },
    {
      id: "phaseA03_outline",
      name: "Case Outline",
      description: "Structure claims and develop case theory",
      icon: <Timeline />,
      color: "secondary",
      estimatedTime: "3-7 minutes",
      agent: "Outliner Bot",
      outputs: [
        "Claims matrix",
        "Case structure",
        "Legal theory",
        "Argument outline",
      ],
      subSteps: ["Structuring", "Mapping Claims", "Analyzing Gaps", "Finalizing"],
    },
    {
      id: "phaseB01_review",
      name: "Quality Review",
      description: "Validate facts, claims, and legal theories",
      icon: <Assessment />,
      color: "warning",
      estimatedTime: "2-4 minutes",
      agent: "Editor Bot",
      outputs: ["Quality assessment", "Fact validation", "Completeness check"],
      subSteps: ["Validating", "Cross-Checking", "Scoring", "Approving"],
    },
    {
      id: "phaseB02_drafting",
      name: "Document Drafting",
      description: "Generate legal documents using templates",
      icon: <Edit />,
      color: "success",
      estimatedTime: "3-8 minutes",
      agent: "Writer Bot",
      outputs: [
        "Legal documents",
        "IRAC analysis",
        "Citations",
        "Formatted output",
      ],
      subSteps: ["Templating", "Composing", "Citing", "Assembling"],
    },
    {
      id: "phaseC01_editing",
      name: "Final Editing",
      description: "Polish and format documents",
      icon: <Gavel />,
      color: "primary",
      estimatedTime: "2-5 minutes",
      agent: "Legal Formatter Bot",
      outputs: [
        "Final documents",
        "Citation formatting",
        "Professional polish",
      ],
      subSteps: ["Formatting", "Citation Review", "Polishing", "Finalizing"],
    },
    {
      id: "phaseC02_orchestration",
      name: "Final Orchestration",
      description: "Coordinate and finalize all deliverables",
      icon: <Assessment />,
      color: "error",
      estimatedTime: "2-5 minutes",
      agent: "Maestro Bot",
      outputs: [
        "Court-ready documents",
        "Filing package",
        "Case summary",
        "Final archive",
      ],
      subSteps: ["Coordinating", "Packaging", "Archiving", "Delivering"],
    },
  ];

  // Initialize phases and socket connection
  useEffect(() => {
    setPhases(phaseDefinitions);
    initializePhaseStates();

    // Initialize socket connection if available
    if (window.io && socketEndpoint) {
      const newSocket = window.io();
      setSocket(newSocket);

      // Socket event listeners
      newSocket.on("phase_started", handlePhaseStarted);
      newSocket.on("phase_progress", handlePhaseProgress);
      newSocket.on("phase_completed", handlePhaseCompleted);
      newSocket.on("phase_error", handlePhaseError);

      return () => {
        newSocket.disconnect();
      };
    }
  }, []);

  // Initialize phase states
  const initializePhaseStates = () => {
    const initialStates = {};
    phaseDefinitions.forEach((phase, index) => {
      initialStates[phase.id] = {
        status: index === 0 ? "ready" : "pending", // idle, ready, running, completed, error
        progress: 0,
        startTime: null,
        endTime: null,
        outputs: [],
        errors: [],
        logs: [],
      };
    });
    setPhaseStates(initialStates);
  };

  // Helper to send phase narration to Bartleby
  const sendBartlebyNarration = useCallback((phaseId, event, message, progress = 0, details = {}) => {
    if (socket && caseId) {
      socket.emit('bartleby_narrate_phase', {
        case_id: caseId,
        phase: phaseId,
        event: event, // 'started', 'progress', 'completed', 'error'
        message: message,
        progress: progress,
        details: details,
      });
    }
  }, [socket, caseId]);

  // Socket event handlers
  const handlePhaseStarted = useCallback(
    (data) => {
      const { phase_id, timestamp } = data;
      setPhaseStates((prev) => ({
        ...prev,
        [phase_id]: {
          ...prev[phase_id],
          status: "running",
          startTime: timestamp,
          progress: 0,
        },
      }));

      const phaseDef = phaseDefinitions.find((p) => p.id === phase_id);
      const phaseName = phaseDef?.name || phase_id;

      addToast(
        `Started ${phaseName}`,
        {
          severity: "info",
          title: "Phase Started",
        }
      );

      // Narrate to Bartleby
      sendBartlebyNarration(
        phase_id,
        'started',
        `Starting ${phaseName}. This phase will ${phaseDef?.description?.toLowerCase() || 'process your case'}. Estimated time: ${phaseDef?.estimatedTime || '2-5 minutes'}.`,
        0,
        { agent: phaseDef?.agent, outputs: phaseDef?.outputs }
      );
    },
    [addToast, sendBartlebyNarration]
  );

  const handlePhaseProgress = useCallback((data) => {
    const { phase_id, progress, message, sub_step } = data;
    setPhaseStates((prev) => ({
      ...prev,
      [phase_id]: {
        ...prev[phase_id],
        progress: progress,
        logs: [
          ...(prev[phase_id].logs || []),
          { timestamp: Date.now(), message },
        ],
      },
    }));

    // Update sub-step progress if provided
    if (sub_step) {
      const phase = phaseDefinitions.find(p => p.id === phase_id);
      if (phase?.subSteps) {
        const stepIndex = phase.subSteps.indexOf(sub_step);
        if (stepIndex !== -1) {
          setPhaseSubSteps(prev => ({
            ...prev,
            [phase_id]: {
              currentStep: sub_step,
              stepIndex: stepIndex,
            },
          }));
        }
      }
    }

    // Narrate significant progress updates to Bartleby
    // Only send narration for milestone updates (every 20% or sub-step changes)
    if (message && (progress % 20 === 0 || sub_step)) {
      sendBartlebyNarration(
        phase_id,
        'progress',
        message,
        progress,
        { sub_step }
      );
    }
  }, [phaseDefinitions, sendBartlebyNarration]);

  const handlePhaseCompleted = useCallback(
    (data) => {
      const { phase_id, outputs, timestamp } = data;
      setPhaseStates((prev) => ({
        ...prev,
        [phase_id]: {
          ...prev[phase_id],
          status: "completed",
          progress: 100,
          endTime: timestamp,
          outputs: outputs || [],
        },
      }));

      const phaseDef = phaseDefinitions.find((p) => p.id === phase_id);
      const phaseName = phaseDef?.name || phase_id;
      
      addToast(`✅ Completed ${phaseName}`, {
        severity: "success",
        title: "Phase Complete",
        details: `Generated ${outputs?.length || 0} outputs`,
      });

      // Narrate completion to Bartleby with details
      const outputSummary = outputs?.length > 0 
        ? `Delivered: ${outputs.map(o => o.name || o.type).join(', ')}`
        : 'Phase completed successfully';
      
      sendBartlebyNarration(
        phase_id,
        'completed',
        `✅ ${phaseName} completed! ${outputSummary}. You can now review the results or proceed to the next phase.`,
        100,
        { outputs, duration: timestamp - phaseStates[phase_id]?.startTime }
      );

      // Auto-advance to next phase if enabled
      if (autoAdvance) {
        const currentIndex = phaseDefinitions.findIndex(
          (p) => p.id === phase_id
        );
        if (currentIndex < phaseDefinitions.length - 1) {
          setCurrentPhase(currentIndex + 1);
          // Set next phase as ready
          const nextPhaseId = phaseDefinitions[currentIndex + 1].id;
          setPhaseStates((prev) => ({
            ...prev,
            [nextPhaseId]: { ...prev[nextPhaseId], status: "ready" },
          }));
        } else {
          // Pipeline completed
          setPipelineStatus("completed");
          addToast("🎉 Pipeline completed successfully!", {
            severity: "success",
            title: "All Phases Complete",
          });
          
          // Final narration
          sendBartlebyNarration(
            'pipeline',
            'completed',
            '🎉 Congratulations! Your complete lawsuit has been generated. All phases completed successfully. You can now download your documents.',
            100,
            { totalPhases: phaseDefinitions.length }
          );
        }
      }

      if (onPhaseComplete) {
        onPhaseComplete(phase_id, outputs);
      }
    },
    [autoAdvance, onPhaseComplete, addToast, sendBartlebyNarration, phaseStates]
  );

  const handlePhaseError = useCallback(
    (data) => {
      const { phase_id, error, timestamp } = data;
      setPhaseStates((prev) => ({
        ...prev,
        [phase_id]: {
          ...prev[phase_id],
          status: "error",
          endTime: timestamp,
          errors: [...(prev[phase_id].errors || []), { timestamp, error }],
        },
      }));

      setPipelineStatus("error");

      const phaseName = phaseDefinitions.find((p) => p.id === phase_id)?.name;
      addToast(`❌ Error in ${phaseName}: ${error}`, {
        severity: "error",
        title: "Phase Error",
      });

      // Narrate error to Bartleby
      sendBartlebyNarration(
        phase_id,
        'error',
        `❌ An error occurred in ${phaseName}: ${error}. Please review the error details and try again, or ask me for help troubleshooting.`,
        phaseStates[phase_id]?.progress || 0,
        { error, timestamp }
      );

      if (onPhaseError) {
        onPhaseError(phase_id, error);
      }
    },
    [onPhaseError, addToast, sendBartlebyNarration, phaseStates]
  );

  // Start a specific phase with error recovery
  const startPhase = async (phaseId) => {
    if (!caseId) {
      addToast("Case ID required to start phase", { severity: "warning" });
      return;
    }

    const currentRetries = retryCount[phaseId] || 0;

    if (currentRetries >= maxRetries) {
      addToast(`Max retries (${maxRetries}) exceeded for ${phaseId}`, {
        severity: "error",
        title: "Max Retries Exceeded",
      });
      return;
    }

    setLoading(true);
    setRetryCount(prev => ({ ...prev, [phaseId]: currentRetries + 1 }));

    // Update phase state to running
    setPhaseStates((prev) => ({
      ...prev,
      [phaseId]: {
        ...prev[phaseId],
        status: "running",
        startTime: Date.now(),
        progress: 0,
      },
    }));

    try {
      // Use backendService for backend integration
      const result = await backendService.executePhase(
        phaseId, 
        caseId, 
        { llmConfig }
      );

      if (!result.success) {
        throw new Error(result.error || 'Phase execution failed');
      }

      // Poll for phase completion
      const finalStatus = await backendService.waitForPhaseCompletion(
        phaseId,
        caseId
      );

      // Update to completed state
      setPhaseStates((prev) => ({
        ...prev,
        [phaseId]: {
          ...prev[phaseId],
          status: "completed",
          progress: 100,
          endTime: Date.now(),
          outputs: finalStatus.outputs || [],
        },
      }));

      setPipelineStatus("running");
      // Reset retry count on success
      setRetryCount(prev => ({ ...prev, [phaseId]: 0 }));

      // Notify callback
      if (onPhaseComplete) {
        onPhaseComplete(phaseId, finalStatus.outputs || []);
      }

    } catch (error) {
      console.error("Failed to start phase:", error);

      // Update to error state
      setPhaseStates((prev) => ({
        ...prev,
        [phaseId]: {
          ...prev[phaseId],
          status: "error",
          errors: [...(prev[phaseId].errors || []), error.message],
        },
      }));

      // Notify error callback
      if (onPhaseError) {
        onPhaseError(phaseId, error.message);
      }

      // Determine error type and recovery strategy
      const errorType = determineErrorType(error);
      const recoveryStrategy = getRecoveryStrategy(errorType, currentRetries);

      await executeRecoveryStrategy(recoveryStrategy, phaseId, error);

    } finally {
      setLoading(false);
    }
  };

  // Retry phase with fresh state
  const retryPhase = async (phaseId) => {
    const currentRetries = retryCount[phaseId] || 0;
    
    if (currentRetries >= maxRetries) {
      addToast(`⚠ Maximum retries reached for ${phaseId}`, {
        severity: "warning",
        title: "Cannot Retry",
      });
      return;
    }

    // Reset phase state
    setPhaseStates((prev) => ({
      ...prev,
      [phaseId]: {
        ...prev[phaseId],
        status: "ready",
        errors: [],
        progress: 0,
      },
    }));

    // Wait a moment before retrying
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    addToast(`⟳ Retrying ${phaseId}...`, {
      severity: "info",
      title: "Retry Initiated",
    });

    // Start the phase again
    await startPhase(phaseId);
  };

  // Skip phase (mark as completed but with warning)
  const skipPhase = (phaseId) => {
    const phase = phaseDefinitions.find(p => p.id === phaseId);
    
    setPhaseStates((prev) => ({
      ...prev,
      [phaseId]: {
        ...prev[phaseId],
        status: "completed",
        progress: 100,
        skipped: true,
        endTime: Date.now(),
      },
    }));

    addToast(`▶ Skipped ${phase?.name || phaseId}`, {
      severity: "warning",
      title: "Phase Skipped",
      details: "This may affect downstream processing",
    });

    // Advance to next phase
    const currentIndex = phaseDefinitions.findIndex((p) => p.id === phaseId);
    if (currentIndex < phaseDefinitions.length - 1) {
      setCurrentPhase(currentIndex + 1);
    }
  };

  // Determine error type for recovery strategy
  const determineErrorType = (error) => {
    const message = error.message.toLowerCase();

    if (message.includes('network') || message.includes('fetch')) {
      return 'network_error';
    }
    if (message.includes('timeout')) {
      return 'timeout_error';
    }
    if (message.includes('llm') || message.includes('ai')) {
      return 'llm_error';
    }
    if (message.includes('storage') || message.includes('database')) {
      return 'storage_error';
    }
    if (message.includes('rate limit')) {
      return 'rate_limit_error';
    }

    return 'unknown_error';
  };

  // Get recovery strategy based on error type and retry count
  const getRecoveryStrategy = (errorType, retries) => {
    const strategies = {
      'network_error': ['retry', 'retry_with_backoff', 'check_connection'],
      'timeout_error': ['retry_with_backoff', 'reduce_concurrency', 'switch_endpoint'],
      'llm_error': ['retry', 'switch_provider', 'reduce_complexity'],
      'storage_error': ['retry', 'alternative_storage', 'clear_cache'],
      'rate_limit_error': ['wait_and_retry', 'reduce_requests', 'queue_request'],
      'unknown_error': ['retry', 'restart_phase', 'manual_intervention']
    };

    const availableStrategies = strategies[errorType] || strategies['unknown_error'];
    return availableStrategies[Math.min(retries, availableStrategies.length - 1)];
  };

  // Execute recovery strategy
  const executeRecoveryStrategy = async (strategy, phaseId, originalError) => {
    const phaseName = phaseDefinitions.find(p => p.id === phaseId)?.name || phaseId;

    switch (strategy) {
      case 'retry':
        addToast(`Retrying ${phaseName}...`, {
          severity: "info",
          title: "Retrying Phase",
        });
        setTimeout(() => startPhase(phaseId), 1000);
        break;

      case 'retry_with_backoff':
        const backoffDelay = Math.pow(2, retryCount[phaseId] || 0) * 1000;
        addToast(`Retrying ${phaseName} in ${backoffDelay/1000}s...`, {
          severity: "info",
          title: "Retrying with Backoff",
        });
        setTimeout(() => startPhase(phaseId), backoffDelay);
        break;

      case 'switch_provider':
        addToast(`Switching to alternative provider for ${phaseName}...`, {
          severity: "info",
          title: "Provider Switch",
        });
        // Implement provider switching logic
        setTimeout(() => startPhase(phaseId), 2000);
        break;

      case 'check_connection':
        addToast("Checking connection and retrying...", {
          severity: "info",
          title: "Connection Check",
        });
        // Implement connection check
        setTimeout(() => startPhase(phaseId), 3000);
        break;

      case 'manual_intervention':
        addToast(`Manual intervention required for ${phaseName}`, {
          severity: "warning",
          title: "Manual Intervention Needed",
        });
        setPhaseStates(prev => ({
          ...prev,
          [phaseId]: { ...prev[phaseId], status: "error" }
        }));
        break;

      default:
        addToast(`Error in ${phaseName}: ${originalError.message}`, {
          severity: "error",
          title: "Phase Error",
        });
    }
  };

  // Start the entire pipeline
  const startPipeline = async () => {
    if (!caseId) {
      addToast("Case ID required to start pipeline", { severity: "warning" });
      return;
    }

    setPipelineStatus("running");
    setCurrentPhase(0);

    // Reset all phase states
    initializePhaseStates();
    setPhaseStates((prev) => ({
      ...prev,
      [phaseDefinitions[0].id]: {
        ...prev[phaseDefinitions[0].id],
        status: "ready",
      },
    }));

    // Start first phase
    await startPhase(phaseDefinitions[0].id);
  };

  // Pause the pipeline
  const pausePipeline = () => {
    setPipelineStatus("paused");
    addToast("Pipeline paused", { severity: "info" });
  };

  // Stop the pipeline
  const stopPipeline = () => {
    setPipelineStatus("idle");
    setCurrentPhase(0);
    initializePhaseStates();
    addToast("Pipeline stopped", { severity: "warning" });
  };

  // Handle evidence upload for Phase A01
  const handleEvidenceUpload = async (uploadedFiles) => {
    try {
      addToast(`Uploaded ${uploadedFiles.length} documents to Phase A01`, {
        severity: "success",
        title: "Upload Complete",
        details: `ObjectIDs: ${uploadedFiles.map(f => f.objectId?.substring(0, 8)).join(", ")}...`,
      });

      // Update phase state to show documents processed
      setPhaseStates((prev) => ({
        ...prev,
        phaseA01_intake: {
          ...prev.phaseA01_intake,
          outputs: [...(prev.phaseA01_intake.outputs || []), ...uploadedFiles.map(f => f.name)],
        },
      }));

      // Auto-advance if documents uploaded and phase is ready
      const phaseA01State = phaseStates.phaseA01_intake;
      if (phaseA01State?.status === "ready" && uploadedFiles.length > 0) {
        await startPhase("phaseA01_intake");
      }
    } catch (error) {
      addToast(`Upload error: ${error.message}`, {
        severity: "error",
        title: "Upload Failed",
      });
    }
  };

  // Get phase status icon
  const getPhaseStatusIcon = (phaseId) => {
    const state = phaseStates[phaseId];
    if (!state) return <Schedule color="disabled" />;

    switch (state.status) {
      case "running":
        return <LinearProgress sx={{ width: 20 }} />;
      case "completed":
        return <CheckCircle color="success" />;
      case "error":
        return <Error color="error" />;
      case "ready":
        return <PlayArrow color="primary" />;
      default:
        return <Schedule color="disabled" />;
    }
  };

  // Get phase status chip
  const getPhaseStatusChip = (phaseId) => {
    const state = phaseStates[phaseId];
    if (!state) return <Chip label="Unknown" size="small" />;

    const statusConfig = {
      idle: { color: "default", label: "Idle" },
      ready: { color: "primary", label: "Ready" },
      running: { color: "warning", label: "Running" },
      completed: { color: "success", label: "Complete" },
      error: { color: "error", label: "Error" },
      pending: { color: "default", label: "Pending" },
    };

    const config = statusConfig[state.status] || statusConfig.idle;

    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        icon={getPhaseStatusIcon(phaseId)}
      />
    );
  };

  // View phase details
  const viewPhaseDetails = (phase) => {
    setSelectedPhase(phase);
    setShowPhaseDetails(true);
  };

  return (
    <Box>
      <Card>
        <CardContent>
          {/* Tab Navigation */}
          <Tabs
            value={activeTab}
            onChange={(event, newValue) => setActiveTab(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
          >
            <Tab label="Phase Pipeline" />
            <Tab label="Drafting Phase (B02)" />
          </Tabs>

          {/* Pipeline Controls - Only show on Pipeline tab */}
          {activeTab === 0 && (
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 3,
              }}>
              <Typography variant="h5">
                Phase Pipeline
                {caseId && (
                  <Chip label={`Case: ${caseId}`} size="small" sx={{ ml: 1 }} />
                )}
              </Typography>

              <Box sx={{ display: "flex", gap: 1 }}>
                <Chip
                  label={pipelineStatus.toUpperCase()}
                  color={
                    pipelineStatus === "completed"
                      ? "success"
                      : pipelineStatus === "running"
                      ? "warning"
                      : pipelineStatus === "error"
                      ? "error"
                      : "default"
                  }
                />

                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={startPipeline}
                  disabled={pipelineStatus === "running" || loading || !caseId}>
                  Start Pipeline
                </Button>

                {pipelineStatus === "running" && (
                  <Button
                    variant="outlined"
                    startIcon={<Pause />}
                    onClick={pausePipeline}>
                    Pause
                  </Button>
                )}

                <Button
                  variant="outlined"
                  startIcon={<Stop />}
                  onClick={stopPipeline}
                  disabled={pipelineStatus === "idle"}>
                  Stop
                </Button>
              </Box>
            </Box>
          )}

          {!caseId && activeTab === 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Case ID required to run phases. Please upload evidence first.
            </Alert>
          )}

          {/* Tab Content */}
          {activeTab === 0 ? (
            /* Phase Pipeline Tab */
            <Box>
              {/* Phase Stepper */}
              <Stepper activeStep={currentPhase} orientation="vertical">
                {phases.map((phase) => {
                  const state = phaseStates[phase.id];
                  const isCompleted = state?.status === "completed";
                  const hasError = state?.status === "error";

                  return (
                    <Step key={phase.id} completed={isCompleted}>
                      <StepLabel
                        error={hasError}
                        icon={phase.icon}
                        optional={
                          <Box
                            sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            {getPhaseStatusChip(phase.id)}
                            <Typography variant="caption">
                              {phase.estimatedTime}
                            </Typography>
                          </Box>
                        }>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                          <Typography variant="h6">{phase.name}</Typography>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => viewPhaseDetails(phase)}>
                              <Visibility />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </StepLabel>

                      <StepContent>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mb: 2 }}>
                          {phase.description}
                        </Typography>

                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Agent: {phase.agent}
                          </Typography>

                          {state?.progress > 0 && state.status === "running" && (
                            <Box sx={{ mb: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={state.progress}
                                sx={{ mb: 0.5 }}
                              />
                              <Typography variant="caption">
                                Progress: {state.progress}%
                              </Typography>

                              {/* Sub-step Progress Indicators */}
                              {phase.subSteps && phaseSubSteps[phase.id] && (
                                <Box sx={{ mt: 1, pl: 2 }}>
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                    ⚙ Current Step: {phaseSubSteps[phase.id].currentStep || phase.subSteps[0]}
                                  </Typography>
                                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                    {phase.subSteps.map((step, idx) => {
                                      const stepIndex = phaseSubSteps[phase.id]?.stepIndex || 0;
                                      const isActive = idx === stepIndex;
                                      const isComplete = idx < stepIndex;
                                      return (
                                        <Chip
                                          key={idx}
                                          label={step}
                                          size="small"
                                          color={isComplete ? "success" : isActive ? "primary" : "default"}
                                          variant={isActive ? "filled" : "outlined"}
                                          icon={isComplete ? <span>✓</span> : isActive ? <span>⟳</span> : null}
                                          sx={{ 
                                            fontSize: '0.7rem',
                                            height: '20px',
                                            opacity: isComplete || isActive ? 1 : 0.5
                                          }}
                                        />
                                      );
                                    })}
                                  </Box>
                                </Box>
                              )}
                            </Box>
                          )}

                          {state?.outputs && state.outputs.length > 0 && (
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Outputs:
                              </Typography>
                              {state.outputs.map((output, idx) => (
                                <Chip
                                  key={idx}
                                  label={output}
                                  size="small"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}

                          {state?.errors && state.errors.length > 0 && (
                            <Box sx={{ mb: 1 }}>
                              <Alert 
                                severity="error" 
                                sx={{ mb: 1 }}
                                action={
                                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                    {/* Retry button with countdown */}
                                    {(retryCount[phase.id] || 0) < maxRetries && (
                                      <Button
                                        size="small"
                                        color="inherit"
                                        onClick={() => retryPhase(phase.id)}
                                        startIcon={<span>⟳</span>}
                                      >
                                        Retry ({maxRetries - (retryCount[phase.id] || 0)} left)
                                      </Button>
                                    )}
                                    {/* Skip phase option for non-critical phases */}
                                    {!phase.id.includes('A01') && !phase.id.includes('C02') && (
                                      <Button
                                        size="small"
                                        color="inherit"
                                        onClick={() => {
                                          if (window.confirm(`Skip ${phase.name}? This may affect downstream phases.`)) {
                                            skipPhase(phase.id);
                                          }
                                        }}
                                        startIcon={<span>▶</span>}
                                      >
                                        Skip
                                      </Button>
                                    )}
                                  </Box>
                                }
                              >
                                <Box>
                                  <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                                    ◆ Error in {phase.name}
                                  </Typography>
                                  <Typography variant="body2">
                                    {state.errors[state.errors.length - 1].error}
                                  </Typography>
                                  
                                  {/* Collapsible error details */}
                                  {state.errors.length > 1 && (
                                    <details style={{ marginTop: '8px', cursor: 'pointer' }}>
                                      <summary style={{ fontSize: '0.875rem', color: '#666' }}>
                                        View {state.errors.length - 1} previous error(s)
                                      </summary>
                                      <Box sx={{ mt: 1, pl: 2, maxHeight: '150px', overflow: 'auto' }}>
                                        {state.errors.slice(0, -1).reverse().map((err, idx) => (
                                          <Typography key={idx} variant="caption" display="block" sx={{ mb: 0.5 }}>
                                            • {new Date(err.timestamp).toLocaleTimeString()}: {err.error}
                                          </Typography>
                                        ))}
                                      </Box>
                                    </details>
                                  )}
                                </Box>
                              </Alert>
                            </Box>
                          )}
                        </Box>

                        <Box sx={{ display: "flex", gap: 1 }}>
                          {state?.status === "ready" && (
                            <Button
                              size="small"
                              variant="contained"
                              startIcon={<PlayArrow />}
                              onClick={() => startPhase(phase.id)}
                              disabled={loading}>
                              Start Phase
                            </Button>
                          )}

                          {phase.id === "phaseA01_intake" && (
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<CloudUpload />}
                              onClick={() => setShowEvidenceUpload(true)}
                              disabled={loading}>
                              Upload Evidence
                            </Button>
                          )}

                          <Button
                            size="small"
                            onClick={() => viewPhaseDetails(phase)}
                            startIcon={<Visibility />}>
                            View Details
                          </Button>
                        </Box>
                      </StepContent>
                    </Step>
                  );
                })}
              </Stepper>
            </Box>
          ) : (
            /* Drafting Phase Tab */
            <Box>
              <DraftingPhase
                caseId={caseId}
                onPhaseComplete={(phaseId, outputs) => {
                  addToast(`✅ Drafting phase ${phaseId} completed`, {
                    severity: "success",
                    title: "Drafting Complete",
                  });
                  if (onPhaseComplete) {
                    onPhaseComplete(phaseId, outputs);
                  }
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Evidence Upload Dialog */}
      <Dialog
        open={showEvidenceUpload}
        onClose={() => setShowEvidenceUpload(false)}
        maxWidth="md"
        fullWidth>
        <DialogTitle>
          Upload Evidence Documents
          <IconButton
            onClick={() => setShowEvidenceUpload(false)}
            sx={{ position: "absolute", right: 8, top: 8 }}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <EvidenceUpload
            onUploadComplete={handleEvidenceUpload}
            currentCaseId={caseId}
            sourcePhase="phaseA01_intake"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEvidenceUpload(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Phase Details Dialog */}
      <Dialog
        open={showPhaseDetails}
        onClose={() => setShowPhaseDetails(false)}
        maxWidth="md"
        fullWidth>
        <DialogTitle>
          {selectedPhase?.name} Details
          <IconButton
            onClick={() => setShowPhaseDetails(false)}
            sx={{ position: "absolute", right: 8, top: 8 }}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedPhase && (
            <Box>
              {(() => {
                switch (selectedPhase.id) {
                  case 'phaseA01_intake':
                    return (
                      <PhaseA01Intake
                        caseId={caseId}
                        onComplete={() => {
                          addToast('Phase A01 intake reviewed', { severity: 'success' });
                          setShowPhaseDetails(false);
                        }}
                        onClose={() => setShowPhaseDetails(false)}
                      />
                    );
                  case 'phaseA02_research':
                    return (
                      <PhaseA02Research
                        caseId={caseId}
                        onComplete={() => {
                          addToast('Phase A02 research reviewed', { severity: 'success' });
                          setShowPhaseDetails(false);
                        }}
                        onClose={() => setShowPhaseDetails(false)}
                      />
                    );
                  case 'phaseA03_outline':
                    return (
                      <PhaseA03Outline
                        caseId={caseId}
                        onComplete={() => {
                          addToast('Phase A03 outline reviewed', { severity: 'success' });
                          setShowPhaseDetails(false);
                        }}
                        onClose={() => setShowPhaseDetails(false)}
                      />
                    );
                  case 'phaseB01_review':
                    return (
                      <PhaseB01Review
                        caseId={caseId}
                        onApprove={() => {
                          addToast('Phase B01 deliverables approved', { severity: 'success' });
                          setShowPhaseDetails(false);
                        }}
                        onClose={() => setShowPhaseDetails(false)}
                      />
                    );
                  case 'phaseC01_editing':
                    return (
                      <PhaseC01Editing
                        caseId={caseId}
                        onComplete={() => {
                          addToast('Phase C01 editing reviewed', { severity: 'success' });
                          setShowPhaseDetails(false);
                        }}
                        onClose={() => setShowPhaseDetails(false)}
                      />
                    );
                  case 'phaseC02_orchestration':
                    return (
                      <PhaseC02Orchestration
                        caseId={caseId}
                        onComplete={() => {
                          addToast('Phase C02 orchestration completed', { severity: 'success' });
                          setShowPhaseDetails(false);
                        }}
                        onClose={() => setShowPhaseDetails(false)}
                      />
                    );
                  default:
                    return (
                      <Box>
                        <Typography variant="body1" sx={{ mb: 2 }}>
                          {selectedPhase.description}
                        </Typography>

                        <List>
                          <ListItem>
                            <ListItemIcon>{selectedPhase.icon}</ListItemIcon>
                            <ListItemText
                              primary="Agent"
                              secondary={selectedPhase.agent}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Estimated Time"
                              secondary={selectedPhase.estimatedTime}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Expected Outputs"
                              secondary={
                                <Box sx={{ mt: 1 }}>
                                  {selectedPhase.outputs.map((output, index) => (
                                    <Chip
                                      key={index}
                                      label={output}
                                      size="small"
                                      sx={{ mr: 0.5, mb: 0.5 }}
                                    />
                                  ))}
                                </Box>
                              }
                            />
                          </ListItem>
                        </List>

                        {phaseStates[selectedPhase.id]?.logs &&
                          phaseStates[selectedPhase.id].logs.length > 0 && (
                            <Accordion>
                              <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="subtitle1">Phase Logs</Typography>
                              </AccordionSummary>
                              <AccordionDetails>
                                <List dense>
                                  {phaseStates[selectedPhase.id].logs.map(
                                    (log, index) => (
                                      <ListItem key={index}>
                                        <ListItemText
                                          primary={log.message}
                                          secondary={new Date(
                                            log.timestamp
                                          ).toLocaleTimeString()}
                                        />
                                      </ListItem>
                                    )
                                  )}
                                </List>
                              </AccordionDetails>
                            </Accordion>
                          )}
                      </Box>
                    );
                }
              })()}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPhaseDetails(false)}>Close</Button>
          {selectedPhase &&
            phaseStates[selectedPhase.id]?.status === "ready" && (
              <Button
                variant="contained"
                onClick={() => {
                  startPhase(selectedPhase.id);
                  setShowPhaseDetails(false);
                }}
                startIcon={<PlayArrow />}>
                Start Phase
              </Button>
            )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PhasePipeline;
