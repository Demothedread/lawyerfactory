# LawyerFactory React UI

Modern React-based user interface for the LawyerFactory lawsuit workflow application.

## Features

### Core Components
- **LawsuitWizard**: Multi-step form for guided lawsuit creation
- **DataTable**: Interactive table with search, sort, and pagination
- **Accordion**: Collapsible content sections
- **Modal**: Popup dialogs for detailed views
- **ScrollToTop**: Smooth scrolling and progress tracking
- **Toast**: Notification system with context awareness
- **TooltipGuide**: Interactive help and guidance system

### UI Enhancements
- **Progress Tracking**: Visual progress bars for workflow steps
- **Feedback System**: Real-time notifications and status updates
- **Guidance Features**: Contextual tooltips and help overlays
- **Responsive Design**: Material-UI components with consistent theming

## Directory Structure

```
src/
├── components/
│   ├── ui/           # Core UI components
│   ├── forms/        # Form components (LawsuitWizard)
│   ├── feedback/     # Progress bars, toasts
│   └── guidance/     # Help system components
├── App.jsx           # Main application component
└── main.jsx          # Entry point
```

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
```bash
cd apps/ui/react-app
npm install
npm run dev
```

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Architecture

### Component Design
- **Modular**: Each component is self-contained and reusable
- **Props-based**: Configuration through props for flexibility
- **Material-UI**: Consistent design system and theming
- **Responsive**: Mobile-first design approach

### State Management
- React hooks for local state
- Context for shared state (Toast notifications)
- Props drilling minimized through composition

### Integration
- Backend API integration through fetch
- Real-time updates for case progress
- File upload and document management

## Key Components

### LawsuitWizard
Multi-step form guiding users through lawsuit creation:
1. Client Information
2. Case Details
3. Evidence Collection
4. Document Drafting
5. Review & Submit

### DataTable
Feature-rich table component with:
- Search and filtering
- Column sorting
- Pagination
- Row selection and actions
- Export capabilities

### Guidance System
Interactive help system including:
- Contextual tooltips
- Step-by-step guides
- Help overlays
- Progress tracking

## Usage

The application provides a complete lawsuit workflow interface:

1. **Dashboard**: Overview of cases, documents, and progress
2. **Case Management**: Create and manage lawsuit cases
3. **Document Management**: Handle legal documents and evidence
4. **Wizard Flow**: Guided lawsuit creation process

## Deployment

The app is built with Vite for optimal performance:
- Fast HMR in development
- Optimized production builds
- Modern browser targets
- Tree-shaking for minimal bundle size