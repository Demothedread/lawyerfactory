// Main App component integrating lawsuit workflow UI components
import {
  Box,
  Card,
  CardContent,
  Container,
  createTheme,
  CssBaseline,
  Grid,
  Paper,
  ThemeProvider,
  Typography,
} from "@mui/material";
import React, { useEffect, useState } from "react";
import ProgressBar from "./components/feedback/ProgressBar";
import Toast, { useToast } from "./components/feedback/Toast";
import LawsuitWizard from "./components/forms/LawsuitWizard";
import TooltipGuide, { GuidedTour } from "./components/guidance/TooltipGuide";
import Accordion from "./components/ui/Accordion";
import AgentOrchestrationPanel from "./components/ui/AgentOrchestrationPanel";
import DataTable from "./components/ui/DataTable";
import EvidenceTable from "./components/ui/EvidenceTable";
import EvidenceUpload from "./components/ui/EvidenceUpload";
import Modal, { ConfirmationModal } from "./components/ui/Modal";
import PhasePipeline from "./components/ui/PhasePipeline";
import lawyerFactoryAPI, {
  getCaseDocuments,
  uploadDocumentsUnified,
} from "./services/apiService";

// Import modular terminal components
import DeliverablesPanel from "./components/terminal/DeliverablesPanel";
import LegalIntakeForm from "./components/terminal/LegalIntakeForm";
import SettingsPanel from "./components/terminal/SettingsPanel";
import WorkflowPanel from "./components/terminal/WorkflowPanel";

// Import Soviet industrial UI components
import AnalogGauge from "./components/soviet/AnalogGauge";
import MechanicalButton from "./components/soviet/MechanicalButton";
import NixieDisplay from "./components/soviet/NixieDisplay";
import StatusLights from "./components/soviet/StatusLights";
import ToggleSwitch from "./components/soviet/ToggleSwitch";

// Create Soviet Industrial theme
const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#b87333", // Soviet brass
    },
    secondary: {
      main: "#dc143c", // Soviet crimson
    },
    background: {
      default: "#1a1a1a", // Soviet charcoal
      paper: "#2a2a2a", // Darker charcoal
    },
    text: {
      primary: "#c0c0c0", // Soviet silver
      secondary: "#8b8680", // Panel rivets
    },
  },
  typography: {
    fontFamily: '"Share Tech Mono", "Russo One", monospace',
    h4: {
      fontWeight: 600,
      fontFamily: '"Orbitron", monospace',
    },
    h6: {
      fontFamily: '"Russo One", sans-serif',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: "linear-gradient(135deg, #1a1a1a 0%, #434b4d 100%)",
          color: "#c0c0c0",
          fontFamily: '"Share Tech Mono", "Russo One", monospace',
          "&::before": {
            content: '""',
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background:
              "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.03) 2px, rgba(0, 0, 0, 0.03) 4px)",
            pointerEvents: "none",
            zIndex: 9999,
          },
        },
      },
    },
  },
});

// Mock data for demonstration
const mockLawsuits = [
  {
    id: 1,
    clientName: "John Doe",
    caseType: "Personal Injury",
    status: "Active",
    filedDate: "2024-01-15",
    jurisdiction: "State Court",
  },
  {
    id: 2,
    clientName: "Jane Smith",
    caseType: "Contract Dispute",
    status: "Discovery",
    filedDate: "2024-02-20",
    jurisdiction: "Federal Court",
  },
  {
    id: 3,
    clientName: "Bob Johnson",
    caseType: "Employment",
    status: "Mediation",
    filedDate: "2024-03-10",
    jurisdiction: "County Court",
  },
];

const mockDocuments = [
  {
    id: 1,
    name: "Complaint Document",
    type: "Legal Filing",
    status: "Draft",
    lastModified: "2024-09-10",
  },
  {
    id: 2,
    name: "Evidence Report",
    type: "Investigation",
    status: "Final",
    lastModified: "2024-09-08",
  },
  {
    id: 3,
    name: "Witness Statements",
    type: "Evidence",
    status: "Review",
    lastModified: "2024-09-05",
  },
];

const App = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentView, setCurrentView] = useState("dashboard");
  const [showWizard, setShowWizard] = useState(false);
  const [selectedLawsuit, setSelectedLawsuit] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState(null);

  // Toast integration
  const { addToast } = useToast();

  // Backend integration state
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [currentCaseId, setCurrentCaseId] = useState(null);
  const [phaseStatuses, setPhaseStatuses] = useState({});
  const [realTimeProgress, setRealTimeProgress] = useState({});

  // Soviet Control Panel State
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);
  const [activePhase, setActivePhase] = useState(null);
  const [systemStatus, setSystemStatus] = useState([
    "green",
    "green",
    "amber",
    "red",
    "red",
  ]);
  const [overallProgress, setOverallProgress] = useState(25);

  // Enhanced UI state
  const [showGuidedTour, setShowGuidedTour] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationData, setConfirmationData] = useState(null);

  // Briefcaser Professional Terminal State
  const [showSettings, setShowSettings] = useState(false);
  const [showLegalIntake, setShowLegalIntake] = useState(false);
  const [userResearchFiles, setUserResearchFiles] = useState([]);
  const [currentWorkspace, setCurrentWorkspace] = useState("dashboard");

  // Backend connection initialization
  useEffect(() => {
    const initializeBackend = async () => {
      try {
        const connected = await lawyerFactoryAPI.connect();
        setIsBackendConnected(connected);

        if (connected) {
          addToast("✅ Connected to LawyerFactory backend", {
            severity: "success",
            title: "Backend Connected",
          });
        } else {
          addToast("⚠️ Running in offline mode - using mock data", {
            severity: "warning",
            title: "Offline Mode",
          });
        }
      } catch (error) {
        console.error("Backend initialization failed:", error);
        addToast("❌ Backend connection failed - using offline mode", {
          severity: "error",
          title: "Connection Failed",
        });
      }
    };

    initializeBackend();

    // Setup phase update handler
    const handlePhaseUpdate = (phaseData) => {
      console.log("📊 Phase update received:", phaseData);
      setRealTimeProgress((prev) => ({
        ...prev,
        [phaseData.phase]: {
          progress: phaseData.progress,
          message: phaseData.message,
          timestamp: new Date().toISOString(),
        },
      }));

      addToast(`${phaseData.phase}: ${phaseData.message}`, {
        severity: phaseData.progress === 100 ? "success" : "info",
        title: "Workflow Update",
      });
    };

    lawyerFactoryAPI.onPhaseUpdate(handlePhaseUpdate);

    // Cleanup on component unmount
    return () => {
      lawyerFactoryAPI.offPhaseUpdate(handlePhaseUpdate);
      lawyerFactoryAPI.disconnect();
    };
  }, [addToast]);

  // Load case documents when currentCaseId changes
  useEffect(() => {
    if (currentCaseId && isBackendConnected) {
      loadCaseDocuments(currentCaseId);
    }
  }, [currentCaseId, isBackendConnected]);

  // Keyboard shortcuts for better UX
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Only trigger shortcuts when not in input fields
      if (
        event.target.tagName === "INPUT" ||
        event.target.tagName === "TEXTAREA"
      ) {
        return;
      }

      // Ctrl/Cmd + key combinations
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case "n":
            event.preventDefault();
            handleQuickAction("new_case");
            break;
          case "f":
            event.preventDefault();
            handleQuickAction("search");
            break;
          case "u":
            event.preventDefault();
            handleQuickAction("upload");
            break;
          case ",":
            event.preventDefault();
            handleQuickAction("settings");
            break;
          case "?":
            event.preventDefault();
            handleQuickAction("help");
            break;
          default:
            break;
        }
      }

      // Escape key actions
      if (event.key === "Escape") {
        if (modalOpen) {
          handleModalClose();
        }
        if (showSettings) {
          setShowSettings(false);
        }
        if (showLegalIntake) {
          setShowLegalIntake(false);
        }
        if (showGuidedTour) {
          setShowGuidedTour(false);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [modalOpen, showSettings, showLegalIntake, showGuidedTour]);

  const handleWizardComplete = (data) => {
    console.log("Lawsuit created:", data);
    addToast("Lawsuit created successfully!", {
      severity: "success",
      title: "Success",
    });
    setShowWizard(false);
    setCurrentView("dashboard");
    // Here you would typically send data to backend
  };

  const handleWizardCancel = () => {
    setShowWizard(false);
  };

  const handleLawsuitClick = (lawsuit) => {
    setSelectedLawsuit(lawsuit);
    setModalContent(
      <Box>
        <Typography variant="h6" gutterBottom>
          {lawsuit.clientName} - {lawsuit.caseType}
        </Typography>
        <Typography>Status: {lawsuit.status}</Typography>
        <Typography>Filed: {lawsuit.filedDate}</Typography>
        <Typography>Jurisdiction: {lawsuit.jurisdiction}</Typography>
      </Box>
    );
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setModalContent(null);
  };

  const toggleLeftPanel = () => {
    setLeftPanelCollapsed(!leftPanelCollapsed);
  };

  const toggleRightPanel = () => {
    setRightPanelCollapsed(!rightPanelCollapsed);
  };

  // Document download handlers

  // Semantic search functionality
  const handleSemanticSearch = async (query = "", onResults = null) => {
    try {
      addToast(`🔍 Searching for: "${query}"`, {
        severity: "info",
        title: "Semantic Search Started",
      });

      // If no query provided, open search modal
      if (!query.trim()) {
        const searchQuery = prompt("Enter your search query:");
        if (!searchQuery) return;
        query = searchQuery;
      }

      // Call LawyerFactory API for semantic search
      if (lawyerFactoryAPI.isConnected) {
        // TODO: Implement semantic search API endpoint
        // For now, show mock results
        const mockResults = [
          {
            id: 1,
            title: "Contract Law Precedent",
            content: `Legal precedent regarding ${query}...`,
            relevance: 0.95,
            source: "case_law_database",
          },
          {
            id: 2,
            title: "Similar Case Analysis",
            content: `Analysis of cases similar to ${query}...`,
            relevance: 0.87,
            source: "research_database",
          },
          {
            id: 3,
            title: "Legal Commentary",
            content: `Expert commentary on ${query}...`,
            relevance: 0.73,
            source: "secondary_sources",
          },
        ];

        // Show results in modal
        setModalContent(
          React.createElement("div", { style: { padding: "20px" } }, [
            React.createElement(
              "h3",
              { key: "title", style: { color: "var(--soviet-brass)" } },
              `Search Results for: "${query}"`
            ),
            React.createElement(
              "div",
              { key: "results" },
              mockResults.map((result) =>
                React.createElement(
                  "div",
                  {
                    key: result.id,
                    style: {
                      padding: "15px",
                      marginBottom: "10px",
                      backgroundColor: "var(--panel-bg)",
                      border: "1px solid var(--soviet-brass)",
                      borderRadius: "5px",
                    },
                  },
                  [
                    React.createElement(
                      "h4",
                      {
                        key: "result-title",
                        style: { color: "var(--soviet-silver)" },
                      },
                      result.title
                    ),
                    React.createElement(
                      "p",
                      {
                        key: "result-content",
                        style: { color: "var(--text-secondary)" },
                      },
                      result.content
                    ),
                    React.createElement(
                      "small",
                      {
                        key: "result-meta",
                        style: { color: "var(--soviet-amber)" },
                      },
                      `Relevance: ${(result.relevance * 100).toFixed(
                        1
                      )}% | Source: ${result.source}`
                    ),
                  ]
                )
              )
            ),
          ])
        );
        setModalOpen(true);

        if (onResults) onResults(mockResults);
      } else {
        addToast("🔍 Semantic search requires backend connection", {
          severity: "warning",
          title: "Search Unavailable",
        });
      }

      addToast(`✅ Found ${3} results for "${query}"`, {
        severity: "success",
        title: "Search Complete",
      });
    } catch (error) {
      console.error("Semantic search failed:", error);
      addToast(`❌ Search failed: ${error.message}`, {
        severity: "error",
        title: "Search Error",
      });
    }
  };

  // Quick action handlers
  const handleQuickAction = (action) => {
    switch (action) {
      case "new_case":
        setShowWizard(true);
        break;
      case "search":
        handleSemanticSearch();
        break;
      case "upload":
        document.getElementById("research-upload")?.click();
        break;
      case "settings":
        setShowSettings(true);
        break;
      case "help":
        setShowGuidedTour(true);
        break;
      default:
        addToast(`Action "${action}" triggered`, {
          severity: "info",
          title: "Quick Action",
        });
    }
  };

  // Guided tour setup
  const tourSteps = [
    {
      title: "Welcome to Briefcaser",
      content:
        "This is your professional legal document automation control terminal. Let's take a quick tour of the key features.",
      tips: [
        "Use the workflow panel to track your case progress",
        "The chat interface connects you with AI legal assistants",
      ],
    },
    {
      title: "Workflow Control Panel",
      content:
        "Monitor your 7-phase legal workflow here. Each phase represents a different stage of document preparation.",
      tips: [
        "Green lights indicate completed phases",
        "Amber lights show active phases",
        "Red lights indicate phases needing attention",
      ],
    },
    {
      title: "Document Deliverables",
      content:
        "View and download your generated legal documents from this panel.",
      tips: [
        "Documents can be exported as PDF or DOC",
        "The evidence table shows supporting materials",
      ],
    },
  ];

  const handleStartTour = () => {
    setShowGuidedTour(true);
  };

  // Briefcaser Professional Handlers
  const handleLegalIntakeSubmit = async (formData) => {
    try {
      console.log("Legal intake submitted:", formData);

      // Create case using LawyerFactory API
      const result = await lawyerFactoryAPI.createCase(formData);
      setCurrentCaseId(result.case_id);

      addToast(`✅ Case ${result.case_id} created successfully!`, {
        severity: "success",
        title: "Case Created",
      });

      // Load any existing documents for this case from unified storage
      await loadCaseDocuments(result.case_id);

      // Auto-start research phase if we have case description
      if (formData.claimDescription && formData.claimDescription.trim()) {
        setTimeout(async () => {
          try {
            await lawyerFactoryAPI.startResearchPhase(
              formData.claimDescription
            );
            addToast("🔍 Legal research phase initiated", {
              severity: "info",
              title: "Research Started",
            });
          } catch (error) {
            console.error("Auto-research start failed:", error);
          }
        }, 1000);
      }
    } catch (error) {
      console.error("Legal intake failed:", error);
      addToast(`❌ Case creation failed: ${error.message}`, {
        severity: "error",
        title: "Intake Failed",
      });
    }
  };

  // Load case documents from unified storage
  const loadCaseDocuments = async (caseId) => {
    try {
      const documentsResult = await getCaseDocuments(caseId);

      if (documentsResult.success) {
        // Convert stored documents to UI format
        const storedFiles = documentsResult.documents.map((doc) => ({
          id: doc.object_id,
          name: doc.metadata?.filename || "Unknown File",
          size: doc.size || 0,
          type: doc.metadata?.content_type || "unknown",
          uploadDate: new Date(doc.metadata?.uploaded_at * 1000).toISOString(),
          status: "completed",
          object_id: doc.object_id,
          evidence_id: doc.evidence_id,
          s3_url: doc.s3_url,
          phase: doc.metadata?.phase || "unknown",
        }));

        // Filter by phase and update appropriate state
        const researchFiles = storedFiles.filter(
          (file) =>
            file.phase === "phaseA02_research" || file.phase === "research"
        );

        setUserResearchFiles(researchFiles);

        if (storedFiles.length > 0) {
          addToast(
            `📂 Loaded ${storedFiles.length} documents from unified storage`,
            {
              severity: "info",
              title: "Case Documents Loaded",
              details: `Research: ${researchFiles.length} files`,
            }
          );
        }
      }
    } catch (error) {
      console.error("Failed to load case documents:", error);
      addToast(`⚠️ Could not load existing documents: ${error.message}`, {
        severity: "warning",
        title: "Document Load Warning",
      });
    }
  };

  const renderDashboard = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Case Management Dashboard
        <TooltipGuide
          title="Dashboard Overview"
          content="Monitor your active cases, recent documents, and case progress from this central hub."
          type="info"
        />
      </Typography>

      <Grid container spacing={3}>
        {/* Quick Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Cases
              </Typography>
              <Typography variant="h5">
                {mockLawsuits.filter((l) => l.status === "Active").length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Pending Documents
              </Typography>
              <Typography variant="h5">
                {mockDocuments.filter((d) => d.status === "Draft").length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                This Month
              </Typography>
              <Typography variant="h5">{mockLawsuits.length}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Cases */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Cases
            </Typography>
            <DataTable
              data={mockLawsuits}
              columns={[
                { field: "clientName", headerName: "Client Name" },
                { field: "caseType", headerName: "Case Type" },
                { field: "status", headerName: "Status" },
                { field: "filedDate", headerName: "Filed Date" },
              ]}
              onRowClick={handleLawsuitClick}
              searchable
              sortable
            />
          </Paper>
        </Grid>

        {/* Recent Documents */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Documents
            </Typography>
            <DataTable
              data={mockDocuments}
              columns={[
                { field: "name", headerName: "Document Name" },
                { field: "type", headerName: "Type" },
                { field: "status", headerName: "Status" },
                { field: "lastModified", headerName: "Last Modified" },
              ]}
              searchable
              sortable
            />
          </Paper>
        </Grid>

        {/* Case Progress */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Case Progress Overview
            </Typography>
            <Accordion
              items={[
                {
                  title: "Case Preparation (75% Complete)",
                  content: (
                    <Box>
                      <ProgressBar value={75} label="Preparation Progress" />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Client intake, evidence collection, and initial document
                        drafting completed.
                      </Typography>
                    </Box>
                  ),
                },
                {
                  title: "Discovery Phase (45% Complete)",
                  content: (
                    <Box>
                      <ProgressBar value={45} label="Discovery Progress" />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Initial discovery requests sent, awaiting responses from
                        opposing party.
                      </Typography>
                    </Box>
                  ),
                },
                {
                  title: "Mediation (20% Complete)",
                  content: (
                    <Box>
                      <ProgressBar value={20} label="Mediation Progress" />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Mediation scheduled for next month, preparing settlement
                        proposals.
                      </Typography>
                    </Box>
                  ),
                },
              ]}
            />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );

  const renderCases = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Case Management
      </Typography>
      <DataTable
        data={mockLawsuits}
        columns={[
          { field: "clientName", headerName: "Client Name" },
          { field: "caseType", headerName: "Case Type" },
          { field: "status", headerName: "Status" },
          { field: "filedDate", headerName: "Filed Date" },
          { field: "jurisdiction", headerName: "Jurisdiction" },
        ]}
        onRowClick={handleLawsuitClick}
        searchable
        sortable
        paginated
      />
    </Container>
  );

  const renderDocuments = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Document Management
      </Typography>
      <DataTable
        data={mockDocuments}
        columns={[
          { field: "name", headerName: "Document Name" },
          { field: "type", headerName: "Type" },
          { field: "status", headerName: "Status" },
          { field: "lastModified", headerName: "Last Modified" },
        ]}
        searchable
        sortable
        paginated
      />
    </Container>
  );

  // Enhanced Orchestration Workspace
  const renderOrchestrationView = () => (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}>
        <Typography variant="h4" sx={{ color: "var(--soviet-brass)" }}>
          Agent Swarm Orchestration Command
        </Typography>
        <Box sx={{ display: "flex", gap: 2 }}>
          <MechanicalButton
            onClick={() => setCurrentView("dashboard")}
            variant="secondary">
            ← Dashboard
          </MechanicalButton>
          <MechanicalButton
            onClick={() => setCurrentView("pipeline")}
            variant="primary">
            Phase Pipeline →
          </MechanicalButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Agent Orchestration Panel */}
        <Grid item xs={12}>
          <AgentOrchestrationPanel
            currentCaseId={currentCaseId}
            socket={null} // Will be connected to actual Socket.IO in production
            collapsed={false}
            onToggleCollapsed={() => {}}
            showDetails={true}
          />
        </Grid>

        {/* Additional System Monitoring */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ color: "var(--soviet-amber)" }}>
                System Resource Monitor
              </Typography>
              <Box
                sx={{ display: "flex", justifyContent: "space-around", mt: 2 }}>
                <Box sx={{ textAlign: "center" }}>
                  <AnalogGauge
                    value={overallProgress}
                    label="System Load"
                    max={100}
                  />
                </Box>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  <StatusLights statuses={systemStatus} />
                  <Typography
                    variant="caption"
                    sx={{ color: "var(--soviet-silver)" }}>
                    Agent Health Status
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Workflow Integration */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ color: "var(--soviet-amber)" }}>
                Workflow Integration Status
              </Typography>
              <Box sx={{ mt: 2 }}>
                {currentCaseId ? (
                  <Box>
                    <Typography
                      variant="body1"
                      sx={{ mb: 2, color: "var(--soviet-green)" }}>
                      ✅ Active Case: {currentCaseId}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{ color: "var(--soviet-silver)" }}>
                      Agent swarm is coordinating on active case. Monitor
                      real-time collaboration above.
                    </Typography>
                  </Box>
                ) : (
                  <Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2 }}>
                      No active case detected. Upload evidence or start a new
                      case to activate agent coordination.
                    </Typography>
                    <MechanicalButton
                      onClick={() => setCurrentView("evidence")}
                      variant="primary"
                      style={{
                        backgroundColor: "var(--soviet-green)",
                        borderColor: "var(--soviet-green)",
                      }}>
                      Start Evidence Upload →
                    </MechanicalButton>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );

  const renderContent = () => {
    if (showWizard) {
      return (
        <LawsuitWizard
          onComplete={handleWizardComplete}
          onCancel={handleWizardCancel}
        />
      );
    }

    switch (currentView) {
      case "cases":
        return renderCases();
      case "documents":
        return renderDocuments();
      case "orchestration":
        return renderOrchestrationView();
      case "evidence":
        return renderEvidenceWorkspace();
      case "pipeline":
        return renderPipelineWorkspace();
      default:
        return renderDashboard();
    }
  };

  // Enhanced Evidence Workspace
  const renderEvidenceWorkspace = () => (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Typography
        variant="h4"
        gutterBottom
        sx={{ color: "var(--soviet-brass)" }}>
        Evidence Management System
      </Typography>

      <Grid container spacing={3}>
        {/* Evidence Upload Section */}
        <Grid item xs={12} lg={6}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ color: "var(--soviet-amber)" }}>
                Document Upload
              </Typography>
              <EvidenceUpload
                currentCaseId={currentCaseId}
                onUploadComplete={(files) => {
                  addToast(`✅ Uploaded ${files.length} documents`, {
                    severity: "success",
                    title: "Upload Complete",
                  });

                  // Set case ID from first upload if not set
                  if (!currentCaseId && files.length > 0) {
                    const newCaseId =
                      files[0].evidenceId?.split("_")[0] ||
                      "case_" + Date.now();
                    setCurrentCaseId(newCaseId);
                  }

                  // Trigger evidence table refresh
                  setRealTimeProgress((prev) => ({
                    ...prev,
                    evidenceRefresh: Date.now(),
                  }));
                }}
                apiEndpoint="/api/storage/documents"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Phase Pipeline Preview */}
        <Grid item xs={12} lg={6}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ color: "var(--soviet-amber)" }}>
                Phase Pipeline Preview
              </Typography>
              <Box sx={{ textAlign: "center", py: 4 }}>
                {currentCaseId ? (
                  <Box>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      Case: {currentCaseId}
                    </Typography>
                    <MechanicalButton
                      onClick={() => setCurrentView("pipeline")}
                      variant="primary"
                      style={{
                        backgroundColor: "var(--soviet-green)",
                        borderColor: "var(--soviet-green)",
                      }}>
                      Start Phase Pipeline →
                    </MechanicalButton>
                  </Box>
                ) : (
                  <Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2 }}>
                      Upload evidence to create a case and enable phase
                      processing
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{ color: "var(--soviet-silver)" }}>
                      Phase A01 → A02 → A03 → B01 → B02 → C01
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Evidence Table */}
        <Grid item xs={12}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <EvidenceTable
                caseId={currentCaseId}
                refreshTrigger={realTimeProgress.evidenceRefresh}
                onEvidenceSelect={(evidence) => {
                  addToast(`Selected: ${evidence.filename}`, {
                    severity: "info",
                    title: "Evidence Selected",
                  });
                }}
                onEvidenceUpdate={(action, evidence) => {
                  if (action === "deleted") {
                    addToast(`Deleted: ${evidence.filename}`, {
                      severity: "success",
                      title: "Evidence Deleted",
                    });
                  }
                }}
                apiEndpoint="/api/evidence"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );

  // Enhanced Pipeline Workspace
  const renderPipelineWorkspace = () => (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}>
        <Typography variant="h4" sx={{ color: "var(--soviet-brass)" }}>
          Phase Pipeline Control
        </Typography>
        <Box sx={{ display: "flex", gap: 2 }}>
          <MechanicalButton
            onClick={() => setCurrentView("evidence")}
            variant="secondary">
            ← Back to Evidence
          </MechanicalButton>
          <MechanicalButton
            onClick={() => setCurrentView("dashboard")}
            variant="primary">
            Dashboard
          </MechanicalButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Phase Pipeline Component */}
        <Grid item xs={12}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <PhasePipeline
                caseId={currentCaseId}
                onPhaseComplete={(phaseId, outputs) => {
                  addToast(
                    `✅ Phase ${phaseId} completed with ${
                      outputs?.length || 0
                    } outputs`,
                    {
                      severity: "success",
                      title: "Phase Complete",
                      details: `Phase ${phaseId} processing finished successfully`,
                    }
                  );

                  // Update phase statuses
                  setPhaseStatuses((prev) => ({
                    ...prev,
                    [phaseId]: "completed",
                  }));

                  // Update overall progress
                  const totalPhases = 6;
                  const completedPhases = Object.values({
                    ...phaseStatuses,
                    [phaseId]: "completed",
                  }).filter((status) => status === "completed").length;
                  setOverallProgress(
                    Math.round((completedPhases / totalPhases) * 100)
                  );
                }}
                onPhaseError={(phaseId, error) => {
                  addToast(`❌ Phase ${phaseId} failed: ${error}`, {
                    severity: "error",
                    title: "Phase Error",
                  });

                  setPhaseStatuses((prev) => ({
                    ...prev,
                    [phaseId]: "error",
                  }));
                }}
                autoAdvance={true}
                showDetails={true}
                apiEndpoint="/api/phases"
                socketEndpoint="/phases"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Pipeline Status and Results */}
        <Grid item xs={12}>
          <Card
            sx={{
              backgroundColor: "var(--soviet-bg)",
              border: "1px solid var(--soviet-brass)",
              borderRadius: "4px",
            }}>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ color: "var(--soviet-amber)" }}>
                Pipeline Results & Deliverables
              </Typography>
              <Box sx={{ mt: 2 }}>
                {Object.keys(phaseStatuses).length > 0 ? (
                  <Grid container spacing={2}>
                    {Object.entries(phaseStatuses).map(([phaseId, status]) => (
                      <Grid item xs={12} sm={6} md={4} key={phaseId}>
                        <Paper
                          sx={{ p: 2, backgroundColor: "var(--soviet-panel)" }}>
                          <Typography
                            variant="subtitle2"
                            sx={{ color: "var(--soviet-brass)" }}>
                            {phaseId}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color:
                                status === "completed"
                                  ? "var(--soviet-green)"
                                  : "var(--soviet-amber)",
                            }}>
                            Status: {status.toUpperCase()}
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No phase results yet. Start the pipeline to see progress.
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Toast />

      {/* Briefcaser Professional Control Terminal */}
      <div
        className={`control-station ${
          leftPanelCollapsed ? "sidebar-collapsed" : ""
        } ${rightPanelCollapsed ? "info-collapsed" : ""} ${
          leftPanelCollapsed && rightPanelCollapsed ? "both-collapsed" : ""
        }`}>
        {/* Terminal Header */}
        <div className="terminal-header">
          <div className="briefcaser-logo">Briefcaser</div>
          <div className="system-status-bar">
            <StatusLights
              statuses={[
                isBackendConnected ? "green" : "red", // Backend connection
                currentCaseId ? "green" : "amber", // Active case
                ...systemStatus.slice(2), // Other system statuses
              ]}
            />
            <ToggleSwitch
              active={!leftPanelCollapsed}
              onToggle={toggleLeftPanel}
              label="Workflow"
            />
            <ToggleSwitch
              active={!rightPanelCollapsed}
              onToggle={toggleRightPanel}
              label="Info"
            />
            <MechanicalButton
              variant={isBackendConnected ? "success" : "danger"}
              onClick={handleStartTour}
              style={{ fontSize: "12px", padding: "6px 12px" }}>
              {isBackendConnected ? "🟢 Online" : "🔴 Offline"}
            </MechanicalButton>
            <div className="terminal-time">
              <NixieDisplay value={new Date().getHours()} digits={2} />
              :
              <NixieDisplay value={new Date().getMinutes()} digits={2} />
            </div>
          </div>
        </div>

        {/* Sidebar Panel - Workflow Control */}
        <div
          className={`sidebar-panel ${leftPanelCollapsed ? "collapsed" : ""}`}>
          <div className="sidebar-header">
            <h3
              style={{
                color: "var(--soviet-brass)",
                fontSize: "var(--text-md)",
              }}>
              {leftPanelCollapsed ? "WF" : "Workflow Control"}
            </h3>
            <MechanicalButton
              onClick={toggleLeftPanel}
              style={{ padding: "4px 8px", fontSize: "12px" }}>
              {leftPanelCollapsed ? "→" : "←"}
            </MechanicalButton>
          </div>
          <div className="sidebar-content">
            <WorkflowPanel />
          </div>
        </div>

        {/* Main Panel - Primary Content */}
        <div className="main-panel">
          <div className="main-panel-header">
            <h2
              style={{
                color: "var(--soviet-silver)",
                fontSize: "var(--text-lg)",
              }}>
              Legal Document Control Station
            </h2>
            <div
              style={{
                display: "flex",
                gap: "var(--space-sm)",
                alignItems: "center",
              }}>
              <AnalogGauge value={overallProgress} label="Progress" max={100} />
              <MechanicalButton
                onClick={() => handleSemanticSearch()}
                variant="primary"
                style={{
                  backgroundColor: "var(--soviet-amber)",
                  borderColor: "var(--soviet-amber)",
                }}>
                🔍 Search
              </MechanicalButton>
              <MechanicalButton
                onClick={() => setShowWizard(true)}
                variant="success">
                New Case
              </MechanicalButton>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div
            className="navigation-tabs"
            style={{
              display: "flex",
              gap: "2px",
              padding: "var(--space-sm)",
              backgroundColor: "var(--soviet-panel)",
              borderBottom: "1px solid var(--soviet-brass)",
            }}>
            <MechanicalButton
              onClick={() => setCurrentView("dashboard")}
              variant={currentView === "dashboard" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "dashboard"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "dashboard"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
              }}>
              📊 Dashboard
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("evidence")}
              variant={currentView === "evidence" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "evidence"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "evidence"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
              }}>
              📁 Evidence
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("pipeline")}
              variant={currentView === "pipeline" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "pipeline"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "pipeline"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
              }}>
              ⚙️ Pipeline
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("cases")}
              variant={currentView === "cases" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "cases"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "cases"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
              }}>
              📋 Cases
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("documents")}
              variant={currentView === "documents" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "documents"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "documents"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
              }}>
              📄 Documents
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("orchestration")}
              variant={currentView === "orchestration" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "orchestration"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "orchestration"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
              }}>
              🎯 Orchestration
            </MechanicalButton>
          </div>
          <div className="main-panel-content">{renderContent()}</div>
        </div>

        {/* Info Panel - Deliverables and Chat */}
        <div className={`info-panel ${rightPanelCollapsed ? "collapsed" : ""}`}>
          <div className="info-panel-header">
            <h3
              style={{
                color: "var(--soviet-brass)",
                fontSize: "var(--text-md)",
              }}>
              {rightPanelCollapsed ? "DL" : "Deliverables"}
            </h3>
            <MechanicalButton
              onClick={toggleRightPanel}
              style={{ padding: "4px 8px", fontSize: "12px" }}>
              {rightPanelCollapsed ? "←" : "→"}
            </MechanicalButton>
          </div>
          <div className="info-panel-content">
            <DeliverablesPanel />
          </div>
        </div>

        {/* Terminal Footer */}
        <div className="terminal-footer">
          <span>Briefcaser v2.1.0 | Legal Document Automation Terminal</span>
          <span>
            Backend:{" "}
            {isBackendConnected
              ? "🟢 LawyerFactory Connected"
              : "🔴 Offline Mode"}{" "}
            | Case: {currentCaseId ? `📂 ${currentCaseId}` : "No Active Case"} |
            System: {systemStatus.filter((s) => s === "green").length}/5 Online
          </span>
        </div>
      </div>

      {/* Modal */}
      <Modal open={modalOpen} onClose={handleModalClose} title="Case Details">
        {modalContent}
      </Modal>

      {/* Guided Tour */}
      <GuidedTour
        steps={tourSteps}
        open={showGuidedTour}
        onClose={() => setShowGuidedTour(false)}
        onComplete={() => {
          setShowGuidedTour(false);
          addToast("Briefcaser tour completed!", {
            severity: "success",
            title: "Tour Complete",
          });
        }}
      />

      {/* Legal Intake Form Modal */}
      <LegalIntakeForm
        open={showLegalIntake}
        onClose={() => setShowLegalIntake(false)}
        onSubmit={handleLegalIntakeSubmit}
      />

      {/* Settings Panel Modal */}
      <Modal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        title="Briefcaser Settings">
        <SettingsPanel />
      </Modal>

      {/* Confirmation Modal */}
      <ConfirmationModal
        open={showConfirmation}
        onClose={() => setShowConfirmation(false)}
        title={confirmationData?.title}
        message={confirmationData?.message}
        onConfirm={confirmationData?.onConfirm}
        confirmLabel={confirmationData?.confirmLabel}
        cancelLabel={confirmationData?.cancelLabel}
      />

      {/* Scroll to Top - Removed for terminal interface */}
    </ThemeProvider>
  );
};

export default App;
