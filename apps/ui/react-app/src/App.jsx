// Main App component integrating lawsuit workflow UI components
import {
  Box,
  Container,
  createTheme,
  CssBaseline,
  Paper,
  ThemeProvider,
  Typography
} from "@mui/material";
import React, { useEffect, useRef, useState } from "react";
import Toast, { useToast } from "./components/feedback/Toast";
import LawsuitWizard from "./components/forms/LawsuitWizard";
import TooltipGuide from "./components/guidance/TooltipGuide";
import AgentOrchestrationPanel from "./components/ui/AgentOrchestrationPanel";
import DataTable from "./components/ui/DataTable";
import EvidenceTable from "./components/ui/EvidenceTable";
import EvidenceUpload from "./components/ui/EvidenceUpload";
import { ConfirmationModal } from "./components/ui/Modal";
import PhasePipeline from "./components/ui/PhasePipeline";
import lawyerFactoryAPI, {
  fetchLLMConfig,
  getCaseDocuments
} from "./services/apiService";

// Import modular terminal components
import LegalIntakeForm from "./components/terminal/LegalIntakeForm";
import SettingsPanel from "./components/terminal/SettingsPanel";
import WorkflowPanel from "./components/terminal/WorkflowPanel";

// Import Soviet industrial UI components
import AnalogGauge from "./components/soviet/AnalogGauge";
import MechanicalButton from "./components/soviet/MechanicalButton";
import NixieDisplay from "./components/soviet/NixieDisplay";
import StatusLights from "./components/soviet/StatusLights";
import ToggleSwitch from "./components/soviet/ToggleSwitch";

// Import grid framework components for zero vertical scroll architecture
import GridContainer, {
  GridItem,
  GridSection,
} from "./components/forms/layout/GridContainer";

// Import legal analysis components
import ClaimsMatrix from "./components/ui/ClaimsMatrix";
import ShotList from "./components/ui/ShotList";
import SkeletalOutlineSystem from "./components/ui/SkeletalOutlineSystem";

// Import MagicUI components - selective, strategic imports for enhanced visual design

// Import MagicUI adapter for Soviet styling

// Create Soviet Industrial theme with dynamic dark mode
const getSovietTheme = (darkMode = true) => createTheme({
  palette: {
    mode: darkMode ? "dark" : "light",
    primary: {
      main: "#b87333", // Soviet brass
    },
    secondary: {
      main: "#dc143c", // Soviet crimson
    },
    background: {
      default: darkMode ? "#1a1a1a" : "#e8e8e8", // Soviet charcoal or light gray
      paper: darkMode ? "#2a2a2a" : "#f5f5f5", // Darker charcoal or paper white
    },
    text: {
      primary: darkMode ? "#c0c0c0" : "#2a2a2a", // Soviet silver or dark gray
      secondary: darkMode ? "#8b8680" : "#5a5a5a", // Panel rivets or medium gray
    },
  },
  typography: {
    fontFamily: '"Share Tech Mono", "Russo One", monospace',
    body2: {
      fontFamily: "elevon"
    },
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
          background: darkMode 
            ? "linear-gradient(135deg, #1a1a1a 0%, #434b4d 100%)"
            : "linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)",
          color: darkMode ? "#c0c0c0" : "#2a2a2a",
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

//Mock data for demonstration
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
    clientName: "",
    caseType: "",
    status: "",
    filedDate: "",
    jurisdiction: "",
  },
  {
    id: 3,
    clientName: "",
    caseType: '',
    status: "",
    filedDate: "",
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
    name: "",
    type: "",
    status: "",
    lastModified: "",
  },
  {
    id: 3,
    name: "",
    type: "",
    status: "",
    lastModified: "",
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

  // Legal Analysis State
  const [claimsMatrix, setClaimsMatrix] = useState([]);
  const [shotList, setShotList] = useState([]);
  const [skeletalOutline, setSkeletalOutline] = useState(null);
  const [selectedClaim, setSelectedClaim] = useState(null);

  // Ref to track backend initialization (prevents duplicate connections)
  const backendInitialized = useRef(false);

  // Settings state with localStorage persistence
  //
  // NOTE: These values are initial defaults only. They are NOT hardcoded in a way
  // that prevents user updates. Behavior:
  //  - On first load, we attempt to read persisted settings from localStorage.
  //  - If none exist, we use these defaults (e.g., aiModel: 'gpt-5-mini', llmProvider: 'openai').
  //  - The SettingsPanel (and handleSettingsChange) allow the user to update these settings,
  //    which are then persisted to localStorage and synced to the backend via lawyerFactoryAPI.updateSettings.
  //  - If the backend/environment exposes an LLM configuration (fetchLLMConfig), the app will update
  //    these settings at runtime to reflect environment-provided values (see initializeBackend()).
  // In short: defaults are provided for convenience but are adjustable and can be overridden.
  const [settings, setSettings] = useState(() => {
    const savedSettings = localStorage.getItem('lawyerfactory_settings');
    return savedSettings ? JSON.parse(savedSettings) : {
      // AI Model Configuration
      aiModel: 'gpt-5-mini', // gpt-4, gpt-4-turbo, anthropic-claude-2, groq-1
      llmProvider: 'openai', // openai, anthropic, groq
      researchMode: true,
      citationValidation: true,
      
      // General Settings
      autoSave: true,
      notifications: true,
      darkMode: true,
      
      // Legal Configuration
      jurisdiction: 'federal',
      citationStyle: 'bluebook',
      strictCompliance: true,
      
      // Agent Configuration
      agentConcurrency: 3,
      agentTimeout: 300,
      
      // Export Settings
      exportFormat: 'pdf',
      includeMetadata: true,
    };
  });

  // Persist settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('lawyerfactory_settings', JSON.stringify(settings));
  }, [settings]);

  // Settings change handler
  const handleSettingsChange = (newSettings) => {
    setSettings(newSettings);
    addToast('⚙️ Settings updated', {
      severity: 'success',
      title: 'Settings Saved',
    });
  };

  // Case management state
  const [cases, setCases] = useState(() => {
    const savedCases = localStorage.getItem('lawyerfactory_cases');
    return savedCases ? JSON.parse(savedCases) : [];
  });
  const [currentCaseName, setCurrentCaseName] = useState(null);

  // Persist cases to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('lawyerfactory_cases', JSON.stringify(cases));
  }, [cases]);

  // Generate case name from plaintiff last name + date
  const generateCaseName = (formData) => {
    const plaintiffName = formData.plaintiffName || '';
    const lastName = plaintiffName.split(' ').pop() || 'Unknown';
    const today = new Date();
    const dateStr = today.getFullYear().toString() +
                   (today.getMonth() + 1).toString().padStart(2, '0') +
                   today.getDate().toString().padStart(2, '0');
    return `${lastName}_${dateStr}`;
  };

  // Save current application state for a case
  const saveCaseState = async (caseName) => {
    try {
      const stateToSave = {
        currentView,
        phaseStatuses,
        realTimeProgress,
        settings,
        claimsMatrix,
        shotList,
        skeletalOutline,
        currentCaseId,
        savedAt: new Date().toISOString(),
      };

      const result = await lawyerFactoryAPI.saveCaseState(caseName, stateToSave);

      if (result.success) {
        // Update case in local cases array
        setCases(prev => {
          const existingIndex = prev.findIndex(c => c.name === caseName);
          const caseData = {
            name: caseName,
            lastModified: new Date().toISOString(),
            status: 'Active',
            plaintiffName: caseName.split('_')[0], // Extract from case name
            caseType: 'Legal Action',
            jurisdiction: settings.jurisdiction,
          };

          if (existingIndex >= 0) {
            // Update existing case
            const updated = [...prev];
            updated[existingIndex] = caseData;
            return updated;
          } else {
            // Add new case
            return [...prev, caseData];
          }
        });

        addToast(`💾 Case "${caseName}" saved successfully`, {
          severity: 'success',
          title: 'Case Saved',
        });
      } else {
        throw new Error(result.error || 'Save failed');
      }
    } catch (error) {
      console.error('Failed to save case state:', error);
      addToast(`❌ Failed to save case: ${error.message}`, {
        severity: 'error',
        title: 'Save Failed',
      });
    }
  };

  // Load application state for a case
  const loadCaseState = async (caseName) => {
    try {
      const result = await lawyerFactoryAPI.loadCaseState(caseName);

      if (result.success && result.state) {
        const state = result.state;

        // Restore application state
        setCurrentView(state.currentView || 'dashboard');
        setPhaseStatuses(state.phaseStatuses || {});
        setRealTimeProgress(state.realTimeProgress || {});
        setSettings(prev => ({ ...prev, ...state.settings }));
        setClaimsMatrix(state.claimsMatrix || []);
        setShotList(state.shotList || []);
        setSkeletalOutline(state.skeletalOutline || null);
        setCurrentCaseId(state.currentCaseId || null);
        setCurrentCaseName(caseName);

        addToast(`📂 Case "${caseName}" loaded successfully`, {
          severity: 'success',
          title: 'Case Loaded',
        });
      } else {
        throw new Error(result.error || 'Load failed');
      }
    } catch (error) {
      console.error('Failed to load case state:', error);
      addToast(`❌ Failed to load case: ${error.message}`, {
        severity: 'error',
        title: 'Load Failed',
      });
    }
  };

  // Handle case selection from case list
  const handleCaseSelect = async (caseName) => {
    await loadCaseState(caseName);
  };

  // Backend connection initialization
  useEffect(() => {
    // Only initialize once
    if (backendInitialized.current) {
      return;
    }

    const initializeBackend = async () => {
      try {
        const connected = await lawyerFactoryAPI.connect();
        setIsBackendConnected(connected);
        backendInitialized.current = true;

        if (connected) {
          addToast("✅ Connected to LawyerFactory backend", {
            severity: "success",
            title: "Backend Connected",
          });

          // Load LLM configuration from environment variables
          try {
            const llmConfigResponse = await fetchLLMConfig();
            if (llmConfigResponse.success) {
              // Update settings with environment variable values
              setSettings(prev => ({
                ...prev,
                llmProvider: llmConfigResponse.config.provider || prev.llmProvider,
                aiModel: llmConfigResponse.config.model || prev.aiModel,
              }));

              console.log('✅ LLM config loaded from environment:', llmConfigResponse.config);
            }
          } catch (error) {
            console.warn('⚠️ Failed to load LLM config from environment:', error);
          }
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
      
      // Update real-time progress state
      setRealTimeProgress((prev) => ({
        ...prev,
        [phaseData.phase]: {
          progress: phaseData.progress,
          message: phaseData.message,
          timestamp: new Date().toISOString(),
        },
      }));

      // Update phase statuses for visual indicators
      setPhaseStatuses((prev) => ({
        ...prev,
        [phaseData.phase]: phaseData.progress === 100 ? 'completed' : 'in-progress',
      }));

      // Update overall progress based on phase completion
      const phaseWeights = {
        'A01': 10,  // Document Intake
        'A02': 20,  // Legal Research
        'A03': 15,  // Case Outline
        'B01': 15,  // Quality Review
        'B02': 25,  // Document Drafting
        'C01': 10,  // Document Editing
        'C02': 5,   // Final Orchestration
      };
      
      if (phaseData.progress === 100) {
        const completedWeight = phaseWeights[phaseData.phase] || 0;
        setOverallProgress((prev) => Math.min(prev + completedWeight, 100));
      }

      // Show detailed toast notification
      const phaseEmoji = {
        'A01': '📥',  // Document Intake
        'A02': '🔍',  // Legal Research
        'A03': '📋',  // Case Outline
        'B01': '✅',  // Quality Review
        'B02': '✍️',  // Document Drafting
        'C01': '✏️',  // Document Editing
        'C02': '🎯',  // Final Orchestration
      };

      addToast(`${phaseEmoji[phaseData.phase] || '📊'} ${phaseData.phase}: ${phaseData.message}`, {
        severity: phaseData.progress === 100 ? "success" : "info",
        title: phaseData.progress === 100 ? "Phase Complete" : "Phase Progress",
        details: `Progress: ${phaseData.progress}% | LLM: ${settings.aiModel}`,
      });
    };

    lawyerFactoryAPI.onPhaseUpdate(handlePhaseUpdate);

    // Cleanup on component unmount
    return () => {
      lawyerFactoryAPI.offPhaseUpdate(handlePhaseUpdate);
      lawyerFactoryAPI.disconnect();
      backendInitialized.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run once on mount

  // Sync settings with API service whenever they change
  useEffect(() => {
    lawyerFactoryAPI.updateSettings(settings);
  }, [settings]);

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

  const ControlTerminalContainer = "app-container";

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
        setShowLegalIntake(true);
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

  const handleStartTour = () => {
    setShowGuidedTour(true);
  };

  // Briefcaser Professional Handlers
  const handleLegalIntakeSubmit = async (formData) => {
    try {
      console.log("Legal intake submitted:", formData);

      // Generate case name from plaintiff last name + date
      const caseName = generateCaseName(formData);

      // Create case using LawyerFactory API
      const result = await lawyerFactoryAPI.createCase(formData);
      setCurrentCaseId(result.case_id);
      setCurrentCaseName(caseName);

      addToast(`✅ Case ${result.case_id} created successfully!`, {
        severity: "success",
        title: "Case Created",
      });

      // Load any existing documents for this case from unified storage
      await loadCaseDocuments(result.case_id);

      // Add case to cases list
      setCases(prev => {
        const newCase = {
          name: caseName,
          created: new Date().toISOString(),
          lastModified: new Date().toISOString(),
          status: "Active",
          jurisdiction: formData.jurisdiction || "Federal",
        };
        // Remove any existing case with the same name
        const filtered = prev.filter(c => c.name !== caseName);
        return [...filtered, newCase];
      });

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

  // Auto-save case state when enabled and case data changes
  useEffect(() => {
    if (settings.autoSave && currentCaseName && (currentCaseId || currentView !== "cases")) {
      const timeoutId = setTimeout(async () => {
        try {
          await saveCaseState(currentCaseName);
          console.log("💾 Auto-saved case state:", currentCaseName);
        } catch (error) {
          console.error("Auto-save failed:", error);
        }
      }, 2000); // Debounce auto-save by 2 seconds

      return () => clearTimeout(timeoutId);
    }
  }, [currentCaseName, currentCaseId, currentView, phaseStatuses, overallProgress, claimsMatrix, shotList, skeletalOutline, settings.autoSave]);


  const renderCases = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Case Management
      </Typography>
      <DataTable
        data={cases.map(caseItem => ({
          name: caseItem.name,
          created: caseItem.created,
          lastModified: caseItem.lastModified,
          status: caseItem.status || "Active",
          jurisdiction: caseItem.jurisdiction || "Federal",
        }))}
        columns={[
          { field: "name", headerName: "Case Name" },
          { field: "created", headerName: "Created" },
          { field: "lastModified", headerName: "Last Modified" },
          { field: "status", headerName: "Status" },
          { field: "jurisdiction", headerName: "Jurisdiction" },
        ]}
        onRowClick={(caseItem) => handleCaseSelect(caseItem.name)}
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

  // Legal Analysis Views
  const renderClaimsView = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Claims Matrix Analysis
        <TooltipGuide
          title="Claims Matrix"
          content="Interactive legal analysis of causes of action with evidentiary requirements and Rule 12(b)(6) compliance checking."
          type="info"
        />
      </Typography>
      <ClaimsMatrix
        caseId={currentCaseId}
        onClaimSelect={setSelectedClaim}
        onMatrixUpdate={setClaimsMatrix}
      />
    </Container>
  );

  const renderShotListView = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Shot List - Evidence Organization
        <TooltipGuide
          title="Shot List"
          content="Fact-by-fact organization of evidence with claim linkages and citation management."
          type="info"
        />
      </Typography>
      <ShotList
        caseId={currentCaseId}
        evidenceData={userResearchFiles}
        onShotUpdate={setShotList}
        onEvidenceLink={(shotId, claimId) => {
          addToast(`Linked evidence ${shotId} to claim ${claimId}`, {
            severity: "success",
            title: "Evidence Linked",
          });
        }}
      />
    </Container>
  );

  const renderOutlineView = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Skeletal Outline System
        <TooltipGuide
          title="Skeletal Outline"
          content="FRCP-compliant blueprint for complaint creation, generated from claims matrix and evidence analysis."
          type="info"
        />
      </Typography>
      <SkeletalOutlineSystem
        caseId={currentCaseId}
        claimsMatrix={claimsMatrix}
        shotList={shotList}
        onOutlineGenerated={setSkeletalOutline}
        onSectionUpdate={(sectionId) => {
          addToast(`Section ${sectionId} updated`, {
            severity: "success",
            title: "Outline Updated",
          });
        }}
      />
    </Container>
  );

  // Enhanced Orchestration Workspace with Zero Vertical Scroll
  const renderOrchestrationView = () => (
    <Box sx={{ width: "100%", height: "100vh", overflow: "hidden", p: 2 }}>
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

      <GridContainer
        minColumns={1}
        maxColumns={2}
        gap="24px"
        autoOptimize={true}
        layoutMode="grid"
        noVerticalScroll={true}
        goldenRatio={true}
        density="comfortable">
        {/* Main Agent Orchestration Panel - Full Width */}
        <GridItem colSpan={2}>
          <GridSection
            title="🤖 Agent Swarm Coordination Matrix"
            collapsible={false}
            icon="⚡">
            <AgentOrchestrationPanel
              currentCaseId={currentCaseId}
              socket={null} // Will be connected to actual Socket.IO in production
              collapsed={false}
              onToggleCollapsed={() => {}}
              showDetails={true}
            />
          </GridSection>
        </GridItem>

        {/* System Resource Monitor */}
        <GridItem colSpan={1}>
          <GridSection
            title="📊 System Resource Monitor"
            collapsible={true}
            defaultCollapsed={false}
            icon="🔧">
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
          </GridSection>
        </GridItem>

        {/* Workflow Integration */}
        <GridItem colSpan={1}>
          <GridSection
            title="🔄 Workflow Integration Status"
            collapsible={true}
            defaultCollapsed={false}
            icon="📋">
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
                    No active case detected. Upload evidence or start a new case
                    to activate agent coordination.
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
          </GridSection>
        </GridItem>
      </GridContainer>
    </Box>
  );

  const renderContent = () => {
    if (showWizard) {
      return (
        <LawsuitWizard
          onComplete={handleWizardComplete}
          onCancel={handleWizardCancel}
          apiEndpoint="/api/intake"
        />
      );
    }

    switch (currentView) {
      case "cases":
        return renderCases();
      case "documents":
        return renderDocuments();
      case "claims":
        return renderClaimsView();
      case "shotlist":
        return renderShotListView();
      case "outline":
        return renderOutlineView();
      case "orchestration":
        return renderOrchestrationView();
      case "evidence":
        return renderEvidenceWorkspace();
      case "pipeline":
        return renderPipelineWorkspace();
      default:
        return renderCases();
    }
  };

  // Enhanced Evidence Workspace with Zero Vertical Scroll Architecture
  const renderEvidenceWorkspace = () => (
    <Box sx={{ width: "100%", height: "100vh", overflow: "hidden", p: 2 }}>
      <Typography
        variant="h4"
        gutterBottom
        sx={{ color: "var(--soviet-brass)", mb: 3 }}>
        Evidence Management System
      </Typography>

      <GridContainer
        minColumns={1}
        maxColumns={2}
        gap="24px"
        autoOptimize={true}
        layoutMode="grid"
        noVerticalScroll={true}
        goldenRatio={true}
        density="comfortable">
        {/* Evidence Upload Section */}
        <GridItem colSpan={1}>
          <GridSection
            title="📄 Document Upload"
            collapsible={false}
            icon="📤">
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
                    files[0].evidenceId?.split("_")[0] || "case_" + Date.now();
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
          </GridSection>
        </GridItem>

        {/* Phase Pipeline Preview */}
        <GridItem colSpan={1}>
          <GridSection
            title="⚡ Phase Pipeline Preview"
            collapsible={false}
            icon="🔄">
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
                    Upload evidence to create a case and enable phase processing
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{ color: "var(--soviet-silver)" }}>
                    Phase A01 → A02 → A03 → B01 → B02 → C01 → C02
                  </Typography>
                </Box>
              )}
            </Box>
          </GridSection>
        </GridItem>

        {/* Evidence Table - Full Width */}
        <GridItem colSpan={2}>
          <GridSection
            title="📊 Evidence Registry"
            collapsible={true}
            defaultCollapsed={false}
            icon="📋">
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
          </GridSection>
        </GridItem>
      </GridContainer>
    </Box>
  );

  // Enhanced Pipeline Workspace with Zero Vertical Scroll
  const renderPipelineWorkspace = () => (
    <Box sx={{ width: "100%", height: "100vh", overflow: "hidden", p: 2 }}>
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

      <GridContainer
        minColumns={1}
        maxColumns={1}
        gap="24px"
        autoOptimize={false}
        layoutMode="grid"
        noVerticalScroll={true}
        density="comfortable">
        {/* Phase Pipeline Component */}
        <GridItem colSpan={1}>
          <GridSection
            title="⚙️ Phase Workflow Pipeline"
            collapsible={false}
            icon="🔄">
            <PhasePipeline
              caseId={currentCaseId}
              llmConfig={{
                provider: settings.llmProvider,
                model: settings.aiModel,
                temperature: settings.temperature || 0.1,
                maxTokens: settings.maxTokens || 2000,
              }}
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
          </GridSection>
        </GridItem>

        {/* Pipeline Status and Results - Collapsible */}
        <GridItem colSpan={1}>
          <GridSection
            title="📊 Pipeline Results & Deliverables"
            collapsible={true}
            defaultCollapsed={false}
            icon="📋">
            <Box sx={{ mt: 2 }}>
              {Object.keys(phaseStatuses).length > 0 ? (
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(auto-fit, minmax(250px, 1fr))",
                    gap: 2,
                  }}>
                  {Object.entries(phaseStatuses).map(([phaseId, status]) => (
                    <Paper
                      key={phaseId}
                      sx={{
                        p: 2,
                        backgroundColor: "var(--soviet-panel)",
                        border: "1px solid var(--soviet-brass)",
                      }}>
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
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" align="center">
                  No phase results yet. Start the pipeline to see progress.
                </Typography>
              )}
            </Box>
          </GridSection>
        </GridItem>
      </GridContainer>
    </Box>
  );

  return (
    <ControlTerminalContainer className="Container">
    <ThemeProvider theme={getSovietTheme(settings.darkMode)} />
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
          <div className="briefcaser-logo-under">Briefcaser</div>
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
              style={{ 
                fontSize: "12px", 
                padding: "6px 12px",
                boxShadow: "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
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
              style={{ 
                padding: "4px 8px", 
                fontSize: "12px",
                boxShadow: "0 3px 5px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
              {leftPanelCollapsed ? "→" : "←"}
            </MechanicalButton>
          </div>
          <div className="sidebar-content">
            <WorkflowPanel
              leftPanelCollapsed={leftPanelCollapsed}
              onToggleLeftPanel={toggleLeftPanel}
              onLegalIntakeSubmit={() => setShowLegalIntake(true)}
              onSettingsOpen={() => setShowSettings(true)}
              systemStatus={systemStatus}
              overallProgress={overallProgress}
              phases={[
                { id: 'A-01', name: 'Intake', icon: '📥', status: 'start', progress: 0 },
                { id: 'A-02', name: 'Research', icon: '🔍', status: 'pending', progress: 0 },
                { id: 'A-03', name: 'Outline', icon: '📋', status: 'pending', progress: 0 },
                { id: 'B-01', name: 'Review', icon: '✅', status: 'pending', progress: 0 },
                { id: 'B-02', name: 'Drafting', icon: '✍️', status: 'pending', progress: 0 },
                { id: 'C-01', name: 'Editing', icon: '📝', status: 'pending', progress: 0 },
                { id: 'C-02', name: 'Final', icon: '🎯', status: 'pending', progress: 0 },
              ]}
              onPhaseSelect={(phaseId) => {
                console.log('Phase selected:', phaseId);
                addToast(`Phase ${phaseId} ${phaseId ? 'started' : 'completed'}`, {
                  severity: 'info',
                  title: 'Phase Update',
                });
              }}
              userResearchFiles={userResearchFiles}
              onResearchUpload={(files) => {
                const fileArray = Array.from(files);
                setUserResearchFiles(prev => [...prev, ...fileArray.map((file, idx) => ({
                  id: Date.now() + idx,
                  name: file.name,
                  size: file.size,
                  type: file.type,
                }))]);
                addToast(`${fileArray.length} file(s) uploaded`, {
                  severity: 'success',
                  title: 'Upload Complete',
                });
              }}
            />
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
               Main Terminal Control
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
                  boxShadow: "0 4px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)",
                  textShadow: "0 1px 3px rgba(0,0,0,0.9)",
                  fontWeight: "bold",
                  color: settings.darkMode ? "#ffffff" : "#1a1a1a",
                }}>
                🔍 SEARCH 
              </MechanicalButton>
              <MechanicalButton
                onClick={() => setShowLegalIntake(true)}
                variant="success"
                style={{
                  boxShadow: "0 4px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)",
                  textShadow: "0 1px 3px rgba(0,0,0,0.9)",
                  fontWeight: "bold",
                  color: settings.darkMode ? "#ffffff" : "#1a1a1a",
                }}>
                NEW CASE
              </MechanicalButton>
              <MechanicalButton
                onClick={() => handleQuickAction("upload")}
                variant="primary"
                style={{
                  boxShadow: "0 4px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)",
                  textShadow: "0 1px 3px rgba(0,0,0,0.9)",
                  fontWeight: "bold",
                  color: settings.darkMode ? "#ffffff" : "#1a1a1a",
                }}
              >
                📤 UPLOAD
              </MechanicalButton>
              <MechanicalButton
                onClick={() => setShowSettings(true)}
                variant="default"
                style={{
                  backgroundColor: "var(--soviet-panel)",
                  borderColor: "var(--soviet-brass)",
                  boxShadow: "0 4px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)",
                  textShadow: "0 1px 3px rgba(0,0,0,0.9)",
                  fontWeight: "bold",
                  color: settings.darkMode ? "#ffffff" : "#1a1a1a",
                }}
              >
                ⚙️ SETTINGS
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
              backgroundColor: "var(--soviet-bronze)",
              borderBottom: "1px solid var(--soviet-bronze)",
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
                    ? "var(--soviet-crimson)"
                    : "var(--soviet-brass)",
                boxShadow: currentView === "dashboard" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
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
                boxShadow: currentView === "evidence" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
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
                boxShadow: currentView === "pipeline" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
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
                boxShadow: currentView === "cases" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
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
                boxShadow: currentView === "documents" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
              📄 Documents
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("claims")}
              variant={currentView === "claims" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "claims"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "claims"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
                boxShadow: currentView === "claims" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
              🏗️ Claims
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("shotlist")}
              variant={currentView === "shotlist" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "shotlist"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "shotlist"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
                boxShadow: currentView === "shotlist" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(0,0,0,0.3)" 
                  : "0 4px 6px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
              🎯 Shot List
            </MechanicalButton>
            <MechanicalButton
              onClick={() => setCurrentView("outline")}
              variant={currentView === "outline" ? "primary" : "default"}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                backgroundColor:
                  currentView === "outline"
                    ? "var(--soviet-green)"
                    : "var(--soviet-panel)",
                borderColor:
                  currentView === "outline"
                    ? "var(--soviet-green)"
                    : "var(--soviet-brass)",
                boxShadow: currentView === "outline" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(36, 36, 36, 0.3)" 
                  : "0 4px 6px rgba(78, 78, 78, 0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                textShadow: "0 1px 2px rgba(43, 34, 34, 0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
              📋 Outline
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
                boxShadow: currentView === "orchestration" 
                  ? "0 3px 6px rgba(0,0,0,0.4), inset 0 -2px 4px rgba(57, 50, 50, 0.3)" 
                  : "0 4px 6px rgba(87, 75, 75, 0.3), inset 0 1px 0 rgba(62, 44, 44, 0.1)",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                fontWeight: "bold",
                color: settings.darkMode ? "#ffffff" : "#1a1a1a",
              }}>
              🎛️ Orchestration
            </MechanicalButton>
          </div>

          {/* Main Content Area */}
          <div className="main-content">
            {renderContent()}

            {/* Debug: Show current view */}
            {/* <pre style={{ color: "white", fontSize: "10px", position: "absolute", top: 10, right: 10 }}>
              Current View: {currentView}
            </pre> */}
          </div>
        </div>
      </div>

      {/* Guided Tour */}
      {/* Legal Intake Form (Briefcaser Professional) */}
      <LegalIntakeForm
        open={showLegalIntake}
        onClose={() => setShowLegalIntake(false)}
        onSubmit={handleLegalIntakeSubmit}
        apiEndpoint="/api/intake"
      />

      {/* Settings Panel (Briefcaser Professional) */}
      <SettingsPanel
        open={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSettingsChange={handleSettingsChange}
      />

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
    </ControlTerminalContainer>
  );
};

export default App;
