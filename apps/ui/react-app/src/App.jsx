// Main App component integrating lawsuit workflow UI components
import React, { useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Grid,
  Paper,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Fab
} from '@mui/material';
import {
  Menu,
  Gavel,
  Person,
  Description,
  Search,
  Settings,
  Help,
  Add,
  Dashboard,
  Folder
} from '@mui/icons-material';
import LawsuitWizard from './components/forms/LawsuitWizard';
import DataTable from './components/ui/DataTable';
import Accordion from './components/ui/Accordion';
import Modal from './components/ui/Modal';
import ScrollToTop from './components/ui/ScrollToTop';
import ProgressBar from './components/feedback/ProgressBar';
import Toast from './components/feedback/Toast';
import TooltipGuide from './components/guidance/TooltipGuide';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
  },
});

// Mock data for demonstration
const mockLawsuits = [
  {
    id: 1,
    clientName: 'John Doe',
    caseType: 'Personal Injury',
    status: 'Active',
    filedDate: '2024-01-15',
    jurisdiction: 'State Court'
  },
  {
    id: 2,
    clientName: 'Jane Smith',
    caseType: 'Contract Dispute',
    status: 'Discovery',
    filedDate: '2024-02-20',
    jurisdiction: 'Federal Court'
  },
  {
    id: 3,
    clientName: 'Bob Johnson',
    caseType: 'Employment',
    status: 'Mediation',
    filedDate: '2024-03-10',
    jurisdiction: 'County Court'
  }
];

const mockDocuments = [
  {
    id: 1,
    name: 'Complaint Document',
    type: 'Legal Filing',
    status: 'Draft',
    lastModified: '2024-09-10'
  },
  {
    id: 2,
    name: 'Evidence Report',
    type: 'Investigation',
    status: 'Final',
    lastModified: '2024-09-08'
  },
  {
    id: 3,
    name: 'Witness Statements',
    type: 'Evidence',
    status: 'Review',
    lastModified: '2024-09-05'
  }
];

const App = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard');
  const [showWizard, setShowWizard] = useState(false);
  const [selectedLawsuit, setSelectedLawsuit] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState(null);

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleViewChange = (view) => {
    setCurrentView(view);
    setDrawerOpen(false);
  };

  const handleNewLawsuit = () => {
    setShowWizard(true);
  };

  const handleWizardComplete = (data) => {
    console.log('Lawsuit created:', data);
    setShowWizard(false);
    setCurrentView('dashboard');
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

  const renderDashboard = () => (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Lawsuit Dashboard
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
                {mockLawsuits.filter(l => l.status === 'Active').length}
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
                {mockDocuments.filter(d => d.status === 'Draft').length}
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
              <Typography variant="h5">
                {mockLawsuits.length}
              </Typography>
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
                { key: 'clientName', label: 'Client Name' },
                { key: 'caseType', label: 'Case Type' },
                { key: 'status', label: 'Status' },
                { key: 'filedDate', label: 'Filed Date' }
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
                { key: 'name', label: 'Document Name' },
                { key: 'type', label: 'Type' },
                { key: 'status', label: 'Status' },
                { key: 'lastModified', label: 'Last Modified' }
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
                  title: 'Case Preparation (75% Complete)',
                  content: (
                    <Box>
                      <ProgressBar value={75} label="Preparation Progress" />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Client intake, evidence collection, and initial document drafting completed.
                      </Typography>
                    </Box>
                  )
                },
                {
                  title: 'Discovery Phase (45% Complete)',
                  content: (
                    <Box>
                      <ProgressBar value={45} label="Discovery Progress" />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Initial discovery requests sent, awaiting responses from opposing party.
                      </Typography>
                    </Box>
                  )
                },
                {
                  title: 'Mediation (20% Complete)',
                  content: (
                    <Box>
                      <ProgressBar value={20} label="Mediation Progress" />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Mediation scheduled for next month, preparing settlement proposals.
                      </Typography>
                    </Box>
                  )
                }
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
          { key: 'clientName', label: 'Client Name' },
          { key: 'caseType', label: 'Case Type' },
          { key: 'status', label: 'Status' },
          { key: 'filedDate', label: 'Filed Date' },
          { key: 'jurisdiction', label: 'Jurisdiction' }
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
          { key: 'name', label: 'Document Name' },
          { key: 'type', label: 'Type' },
          { key: 'status', label: 'Status' },
          { key: 'lastModified', label: 'Last Modified' }
        ]}
        searchable
        sortable
        paginated
      />
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
      case 'cases':
        return renderCases();
      case 'documents':
        return renderDocuments();
      default:
        return renderDashboard();
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Toast />

      {/* App Bar */}
      <AppBar position="static">
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <Menu />
          </IconButton>
          <Gavel sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            LawyerFactory
          </Typography>
          <Button color="inherit" startIcon={<Help />}>
            Help
          </Button>
          <Button color="inherit" startIcon={<Settings />}>
            Settings
          </Button>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={handleDrawerToggle}
      >
        <Box sx={{ width: 250 }}>
          <List>
            <ListItem button onClick={() => handleViewChange('dashboard')}>
              <ListItemIcon><Dashboard /></ListItemIcon>
              <ListItemText primary="Dashboard" />
            </ListItem>
            <ListItem button onClick={() => handleViewChange('cases')}>
              <ListItemIcon><Folder /></ListItemIcon>
              <ListItemText primary="Cases" />
            </ListItem>
            <ListItem button onClick={() => handleViewChange('documents')}>
              <ListItemIcon><Description /></ListItemIcon>
              <ListItemText primary="Documents" />
            </ListItem>
          </List>
          <Divider />
          <List>
            <ListItem button onClick={() => handleViewChange('clients')}>
              <ListItemIcon><Person /></ListItemIcon>
              <ListItemText primary="Clients" />
            </ListItem>
            <ListItem button onClick={() => handleViewChange('search')}>
              <ListItemIcon><Search /></ListItemIcon>
              <ListItemText primary="Search" />
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main">
        {renderContent()}
      </Box>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleNewLawsuit}
      >
        <Add />
      </Fab>

      {/* Modal */}
      <Modal
        open={modalOpen}
        onClose={handleModalClose}
        title="Case Details"
      >
        {modalContent}
      </Modal>

      {/* Scroll to Top */}
      <ScrollToTop />
    </ThemeProvider>
  );
};

export default App;