# Soviet Control Panel UI Documentation

## Overview
The Soviet Control Panel UI is a 1950s Soviet-inspired control board interface for the LawyerFactory legal document processing system. It features a industrial aesthetic with analog gauges, toggle switches, Nixie displays, and metal panels.

## Architecture

### Layout Structure
- **Three-Panel Layout**: Fixed-width panels optimized for 1920x1080 resolution
  - Left Panel (400px): Workflow control
  - Center Panel (flex): Deliverables workspace  
  - Right Panel (600px): LLM command center

### Technology Stack
- React 18 with Hooks
- Framer Motion for animations
- ag-Grid for data tables
- Socket.IO for real-time updates
- Tailwind CSS utilities

## Component Library

### Core Components

#### AnalogGauge
Displays progress and metrics with rotating needle indicator.
```javascript
<AnalogGauge value={75} label="Progress" />
```
Props:
- `value`: Number (0-100)
- `label`: String
- `dangerZone`: Number (default: 80)

#### ToggleSwitch
Industrial toggle switch with LED status light.
```javascript
<ToggleSwitch 
  isOn={isActive} 
  onToggle={handleToggle} 
  label="Auto Mode" 
/>
```
Props:
- `isOn`: Boolean
- `onToggle`: Function
- `label`: String

#### NixieDisplay
Retro vacuum tube numeric display.
```javascript
<NixieDisplay value={42} label="Documents" />
```
Props:
- `value`: Number
- `label`: String

#### MetalPanel
Container with brushed steel appearance and rivets.
```javascript
<MetalPanel title="Control Section">
  {children}
</MetalPanel>
```
Props:
- `title`: String
- `children`: ReactNode
- `showWarningStripe`: Boolean (default: false)

### Workflow Components

#### PhaseSelector
Seven-phase legal workflow navigation.
```javascript
<PhaseSelector 
  activePhase={currentPhase}
  onPhaseChange={handlePhaseChange}
/>
```

#### ProgressTracker
Overall workflow progress display.
```javascript
<ProgressTracker 
  completed={3} 
  total={7} 
/>
```

### Deliverables Components

#### EvidenceTable
ag-Grid based evidence management table.
```javascript
<EvidenceTable 
  data={evidenceData}
  onRowSelect={handleRowSelect}
/>
```

#### ClaimsMatrix
Visual grid of legal claims with strength indicators.
```javascript
<ClaimsMatrix 
  claims={claimsData}
  evidenceLinks={linkData}
/>
```

#### ShotByShotList
Sequential document shot listing.
```javascript
<ShotByShotList 
  shots={shotData}
  onReorder={handleReorder}
/>
```

### Chat Components

#### AgentChat
Multi-agent chat interface with specialized legal agents.
```javascript
<AgentChat 
  agents={agentList}
  onMessage={handleMessage}
/>
```

#### AgentStatus
Real-time agent status indicators.
```javascript
<AgentStatus 
  agentId="researcher"
  status="active"
/>
```

## Design System

### Color Palette
```css
--soviet-red: #8B0000
--warning-amber: #FFA500
--steel-gray: #4A5568
--panel-dark: #1A1A1A
--led-green: #00FF00
--nixie-orange: #FF6B35
```

### Typography
- Headers: OCR A Extended
- Body: Share Tech Mono
- Display: Russo One

### Animations
- Gauge needle rotation: CSS transform with easing
- Button press: translateY with spring physics
- LED pulse: CSS animation with glow effect
- Panel collapse: Framer Motion with width transition

## Keyboard Shortcuts
- `F1`: Toggle left panel
- `F3`: Toggle right panel
- `Tab`: Navigate between panels
- `Enter`: Submit chat message
- `Escape`: Close modals

## Integration

### Backend Connection
```javascript
// Socket.IO connection
const socket = io('http://localhost:5000');

// Evidence updates
socket.on('evidence:update', (data) => {
  updateEvidenceTable(data);
});

// Chat messages
socket.emit('chat:message', {
  agent: 'researcher',
  message: userInput
});
```

### API Endpoints
- `/api/evidence`: Evidence CRUD operations
- `/api/claims`: Claims management
- `/api/workflow`: Phase transitions
- `/api/chat`: LLM agent interactions

## Testing

### Running Tests
```bash
# Run Puppeteer test suite
npm test tests/test_soviet_control_panel.js

# Interactive browser testing
node tests/test_soviet_control_panel.js
```

### Test Coverage
- Layout rendering and responsiveness
- Component interactions
- Keyboard shortcuts
- Tab switching
- Chat functionality
- Panel collapse/expand
- Visual regression

## Performance Considerations

### Optimization Strategies
1. React.memo for expensive components
2. useMemo for computed values
3. Lazy loading for tabs
4. Virtual scrolling in ag-Grid
5. Debounced search inputs

### Bundle Size
- Main bundle: ~450KB (gzipped)
- ag-Grid: ~200KB (lazy loaded)
- Framer Motion: ~50KB

## Accessibility

### ARIA Labels
All interactive components include proper ARIA labels and roles.

### Keyboard Navigation
Full keyboard support with visible focus indicators.

### Screen Reader Support
Semantic HTML structure with descriptive labels.

## Customization

### Theming
Modify CSS variables in the `:root` selector to adjust colors.

### Layout
Panel widths can be adjusted in the layout constants.

### Components
All components accept className prop for additional styling.

## Future Enhancements

### Planned Features
1. Industrial sound effects library
2. Advanced data visualization
3. Collaborative editing
4. Real-time notifications
5. Mobile responsive version

### Performance Improvements
1. Code splitting by route
2. Service worker caching
3. WebAssembly for heavy computations
4. GraphQL for efficient data fetching

## Troubleshooting

### Common Issues

**Panel not collapsing**: Check keyboard event listeners are attached to window.

**ag-Grid not rendering**: Ensure grid container has explicit height.

**Socket connection failing**: Verify backend server is running on correct port.

**Animations janky**: Check for unnecessary re-renders with React DevTools.

## License
MIT License - See LICENSE file for details.