// Phase Pipeline component for workflow visualization and control
import {
  Assessment,
  CheckCircle,
  Close,
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
  Tooltip,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useToast } from "../feedback/Toast";

const PhasePipeline = ({
  caseId,
  onPhaseComplete,
  onPhaseError,
  autoAdvance = true,
  apiEndpoint = "/api/phases",
  socketEndpoint = "/phases",
}) => {
  const [phases, setPhases] = useState([]);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [phaseStates, setPhaseStates] = useState({});
  const [pipelineStatus, setPipelineStatus] = useState("idle"); // idle, running, paused, completed, error
  const [selectedPhase, setSelectedPhase] = useState(null);
  const [showPhaseDetails, setShowPhaseDetails] = useState(false);
  const [socket, setSocket] = useState(null);
  const [loading, setLoading] = useState(false);

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

      addToast(
        `Started ${phaseDefinitions.find((p) => p.id === phase_id)?.name}`,
        {
          severity: "info",
          title: "Phase Started",
        }
      );
    },
    [addToast]
  );

  const handlePhaseProgress = useCallback((data) => {
    const { phase_id, progress, message } = data;
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
  }, []);

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

      const phaseName = phaseDefinitions.find((p) => p.id === phase_id)?.name;
      addToast(`✅ Completed ${phaseName}`, {
        severity: "success",
        title: "Phase Complete",
        details: `Generated ${outputs?.length || 0} outputs`,
      });

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
        }
      }

      if (onPhaseComplete) {
        onPhaseComplete(phase_id, outputs);
      }
    },
    [autoAdvance, onPhaseComplete, addToast]
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

      if (onPhaseError) {
        onPhaseError(phase_id, error);
      }
    },
    [onPhaseError, addToast]
  );

  // Start a specific phase
  const startPhase = async (phaseId) => {
    if (!caseId) {
      addToast("Case ID required to start phase", { severity: "warning" });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiEndpoint}/${phaseId}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start phase: ${response.statusText}`);
      }

      setPipelineStatus("running");
    } catch (error) {
      console.error("Failed to start phase:", error);
      addToast(`Failed to start phase: ${error.message}`, {
        severity: "error",
        title: "Start Error",
      });
    } finally {
      setLoading(false);
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
          {/* Pipeline Controls */}
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

          {!caseId && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Case ID required to run phases. Please upload evidence first.
            </Alert>
          )}

          {/* Phase Stepper */}
          <Stepper activeStep={currentPhase} orientation="vertical">
            {phases.map((phase, index) => {
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
                        <Alert severity="error" sx={{ mb: 1 }}>
                          {state.errors[state.errors.length - 1].error}
                        </Alert>
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
        </CardContent>
      </Card>

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
