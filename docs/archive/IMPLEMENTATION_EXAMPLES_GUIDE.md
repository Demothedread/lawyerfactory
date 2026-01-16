# Implementation Examples & Usage Guide
## LawyerFactory Component Enhancements - Technical Reference

**Date:** October 18, 2025  
**For:** Developers & QA Engineers

---

## TABLE OF CONTENTS
1. [MechanicalButton Usage](#mechanical-button-usage)
2. [AnalogGauge Usage](#analog-gauge-usage)
3. [Settings Panel Integration](#settings-panel-integration)
4. [Keyboard Shortcuts](#keyboard-shortcuts)
5. [CSS Classes Reference](#css-classes-reference)
6. [Troubleshooting](#troubleshooting)

---

## MECHANICAL BUTTON USAGE

### Basic Example

```jsx
import MechanicalButton from './components/soviet/MechanicalButton';

export function MyComponent() {
  const handleClick = () => {
    console.log('Button clicked!');
  };

  return (
    <MechanicalButton onClick={handleClick}>
      Click Me
    </MechanicalButton>
  );
}
```

**Result:** Gray button with industrial styling and mechanical feedback

### With Variants

```jsx
// Primary variant (green)
<MechanicalButton variant="primary">
  ✓ Submit
</MechanicalButton>

// Danger variant (red)
<MechanicalButton variant="danger">
  ✗ Delete
</MechanicalButton>

// Success variant
<MechanicalButton variant="success">
  ✓ Confirm
</MechanicalButton>

// Warning variant
<MechanicalButton variant="warning">
  ⚠ Warning
</MechanicalButton>

// Info variant
<MechanicalButton variant="info">
  ℹ Information
</MechanicalButton>
```

### With Sizes

```jsx
// Small button
<MechanicalButton size="small">
  Small
</MechanicalButton>

// Medium button (default)
<MechanicalButton size="medium">
  Medium
</MechanicalButton>

// Large button
<MechanicalButton size="large">
  Large
</MechanicalButton>
```

### Sound Control

```jsx
// Enable sound (default)
<MechanicalButton enableSound={true}>
  With Sound
</MechanicalButton>

// Disable sound (silent operation)
<MechanicalButton enableSound={false}>
  Silent
</MechanicalButton>
```

### Disabled State

```jsx
<MechanicalButton disabled={true}>
  Disabled Button
</MechanicalButton>
```

**Visual Result:** 50% opacity, no cursor change, click blocked

### Complex Example

```jsx
function SettingsToolbar() {
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    // Save logic
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ display: 'flex', gap: '8px' }}>
      <MechanicalButton 
        variant="primary"
        onClick={handleSave}
        disabled={saved}
      >
        {saved ? '✓ Saved' : '💾 Save'}
      </MechanicalButton>

      <MechanicalButton 
        variant="warning"
        onClick={() => window.location.reload()}
      >
        ↻ Reload
      </MechanicalButton>

      <MechanicalButton 
        variant="danger"
        onClick={() => confirm('Are you sure?')}
      >
        🗑 Delete
      </MechanicalButton>
    </div>
  );
}
```

---

## ANALOG GAUGE USAGE

### Basic Gauge

```jsx
import AnalogGauge from './components/soviet/AnalogGauge';

export function ProcessMonitor() {
  const [progress, setProgress] = useState(45);

  return (
    <AnalogGauge 
      value={progress}
      min={0}
      max={100}
      size={120}
      showValue={true}
    />
  );
}
```

**Result:** Gauge showing 45% progress with needle animation

### Phase Completion Gauge

```jsx
function PhaseTracker() {
  const [phaseProgress, setPhaseProgress] = useState(75);
  const [isPhaseComplete, setIsPhaseComplete] = useState(false);

  // Simulate phase completion
  useEffect(() => {
    if (phaseProgress >= 100) {
      setIsPhaseComplete(true);
    }
  }, [phaseProgress]);

  return (
    <AnalogGauge 
      value={phaseProgress}
      min={0}
      max={100}
      size={150}
      phaseLabel="Phase A01"
      isComplete={isPhaseComplete}
      needleColor="var(--soviet-crimson)"
      animated={true}
      showValue={true}
    />
  );
}
```

**Result:** Gauge with phase label, animates needle, shows completion badge when done

### Multiple Gauges

```jsx
function SystemDashboard() {
  const [metrics, setMetrics] = useState({
    cpuUsage: 35,
    memoryUsage: 62,
    diskUsage: 48,
  });

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
      <div>
        <h3>CPU Usage</h3>
        <AnalogGauge 
          value={metrics.cpuUsage}
          max={100}
          size={120}
          needleColor="var(--soviet-brass)"
        />
      </div>

      <div>
        <h3>Memory Usage</h3>
        <AnalogGauge 
          value={metrics.memoryUsage}
          max={100}
          size={120}
          needleColor="var(--soviet-amber)"
        />
      </div>

      <div>
        <h3>Disk Usage</h3>
        <AnalogGauge 
          value={metrics.diskUsage}
          max={100}
          size={120}
          needleColor="var(--soviet-crimson)"
        />
      </div>
    </div>
  );
}
```

### Real-Time Gauge Update

```jsx
function LivePhaseMonitor() {
  const [phaseData, setPhaseData] = useState({
    name: 'Phase A02',
    progress: 0,
    status: 'pending'
  });

  // Simulate real-time updates from backend
  useEffect(() => {
    const interval = setInterval(() => {
      setPhaseData(prev => ({
        ...prev,
        progress: Math.min(100, prev.progress + Math.random() * 10),
        status: prev.progress >= 100 ? 'complete' : 'in-progress'
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <AnalogGauge 
      value={phaseData.progress}
      min={0}
      max={100}
      size={200}
      phaseLabel={phaseData.name}
      isComplete={phaseData.status === 'complete'}
      needleColor={phaseData.status === 'complete' ? 'var(--soviet-green)' : 'var(--soviet-crimson)'}
      animated={true}
      showValue={true}
    />
  );
}
```

---

## SETTINGS PANEL INTEGRATION

### Opening Settings Panel

```jsx
// Method 1: Via Quick Action Button
function AppToolbar() {
  const handleQuickAction = (action) => {
    if (action === 'settings') {
      // This is handled by parent component's handleQuickAction
    }
  };

  return (
    <button onClick={() => handleQuickAction('settings')}>
      ⚙️ Settings
    </button>
  );
}

// Method 2: Keyboard Shortcut (in App.jsx)
// Press Ctrl+S (Windows/Linux) or Cmd+S (Mac)
// Automatically triggers: setShowSettings(true)

// Method 3: Direct State Control
function MyComponent() {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <>
      <button onClick={() => setShowSettings(true)}>
        Open Settings
      </button>

      <SettingsPanel
        open={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSettingsChange={handleSettingsChange}
      />
    </>
  );
}
```

### Settings Panel Props

```jsx
<SettingsPanel
  open={boolean}              // Control visibility (REQUIRED)
  onClose={function}          // Called when close button clicked (REQUIRED)
  settings={object}           // Current settings object (REQUIRED)
  onSettingsChange={function} // Called when settings change (REQUIRED)
/>
```

### Handling Settings Changes

```jsx
const handleSettingsChange = (newSettings) => {
  // newSettings contains updated values
  // Example: { aiModel: 'gpt-4', llmProvider: 'openai', ... }

  // Update state
  setSettings(newSettings);

  // Persist to localStorage
  localStorage.setItem('lawyerfactory_settings', JSON.stringify(newSettings));

  // Sync to backend
  await backendService.updateSettings(newSettings);

  // Show confirmation
  addToast('⚙️ Settings updated', { severity: 'success' });
};
```

### Settings Tabs

The SettingsPanel includes these tabs:

1. **LLM Configuration** (🤖)
   - Provider selection
   - Model selection
   - API key management
   - Temperature control
   - Max tokens configuration

2. **General** (⚙️)
   - Auto-save toggle
   - Notifications toggle
   - Dark mode toggle
   - Theme selection

3. **Legal Config** (⚖️)
   - Jurisdiction selection
   - Citation style selection
   - Compliance level

4. **Phase Settings** (🔄)
   - Phase behavior customization
   - Timeout settings
   - Concurrent operation limits

5. **Export** (📄)
   - Export format selection
   - Metadata inclusion toggle

---

## KEYBOARD SHORTCUTS

### Available Shortcuts

```
Ctrl+S / Cmd+S     Open Settings Panel
Escape             Close current modal
Ctrl+P / Cmd+P     Show guided tour
Ctrl+N / Cmd+N     Create new case/legal intake
```

### Implementation Example

```jsx
// Inside App.jsx useEffect
useEffect(() => {
  const handleKeyDown = (event) => {
    // Settings
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
      event.preventDefault();
      setShowSettings(true);
    }

    // Close modal
    if (event.key === 'Escape') {
      if (modalOpen) setModalOpen(false);
      if (showSettings) setShowSettings(false);
      if (showLegalIntake) setShowLegalIntake(false);
      if (showGuidedTour) setShowGuidedTour(false);
    }

    // More shortcuts...
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [modalOpen, showSettings, showLegalIntake, showGuidedTour]);
```

---

## CSS CLASSES REFERENCE

### MechanicalButton CSS Classes

```css
/* Base button */
.mech-button { }

/* Variants */
.mech-button--default { }
.mech-button--primary { }
.mech-button--secondary { }
.mech-button--success { }
.mech-button--warning { }
.mech-button--danger { }
.mech-button--info { }

/* Sizes */
.mech-button--small { }
.mech-button--medium { }
.mech-button--large { }

/* States */
.mech-button:hover { }
.mech-button:active { }
.mech-button.pressed { }
.mech-button:disabled { }

/* Inner elements */
.mech-button__content { }
.mech-button__shadow { }

/* Ripple effect */
.ripple { }
```

### AnalogGauge CSS Classes

```css
/* Gauge container */
.analog-gauge { }

/* Gauge rings */
.gauge-ring { }
.gauge-ring--outer { }
.gauge-ring--middle { }
.gauge-ring--inner { }

/* Needle */
.gauge-needle { }

/* Center hub */
.gauge-center { }

/* Value display */
.gauge-value { }
.gauge-value__number { }
.gauge-value__label { }

/* Tick marks */
.gauge-ticks { }
.gauge-tick { }
.gauge-tick--major { }
.gauge-tick--minor { }

/* Range labels */
.gauge-labels { }
.gauge-label { }
.gauge-label--min { }
.gauge-label--max { }
```

---

## TROUBLESHOOTING

### Sound Not Playing

**Problem:** No sound effect when clicking button

**Causes:**
1. Browser has audio disabled
2. Audio context not initialized
3. `enableSound={false}` set on button
4. Browser security restrictions

**Solutions:**
```jsx
// Check if audio is enabled
const testSound = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    console.log('Audio context available:', audioContext.state);
  } catch (e) {
    console.error('Audio not available:', e);
  }
};

// Enable sound
<MechanicalButton enableSound={true}>Click</MechanicalButton>

// Check browser console for errors
// Use browser's DevTools Network tab to verify no blocks
```

### Button Not Responding to Clicks

**Problem:** Button appears but doesn't click

**Causes:**
1. `disabled={true}` set
2. Parent component preventing click event
3. Event handler not provided
4. z-index conflict

**Solutions:**
```jsx
// Check disabled state
<MechanicalButton disabled={false} onClick={handleClick}>
  Click Me
</MechanicalButton>

// Ensure click handler is provided
<MechanicalButton onClick={(e) => console.log('Clicked!')}>
  Click Me
</MechanicalButton>

// Check z-index in CSS
.mech-button {
  z-index: 10; /* Ensure visibility */
}
```

### Settings Panel Not Opening

**Problem:** Settings button clicked but panel doesn't appear

**Causes:**
1. `showSettings` state not updated
2. `SettingsPanel` not receiving `open` prop
3. Modal backdrop blocking interaction
4. Component not imported correctly

**Solutions:**
```jsx
// Verify state is updating
console.log('showSettings:', showSettings); // Should be true

// Check prop passing
<SettingsPanel
  open={showSettings}  // Must be correct prop name
  onClose={() => setShowSettings(false)}
  settings={settings}
  onSettingsChange={handleSettingsChange}
/>

// Verify import
import SettingsPanel from "./components/terminal/SettingsPanel";

// Check z-index
.settings-overlay {
  z-index: 1000; /* Above other elements */
}
```

### Gauge Not Animating

**Problem:** Gauge needle doesn't move smoothly

**Causes:**
1. `animated={false}` set
2. Browser doesn't support CSS transitions
3. Performance issue causing jank
4. Value not changing

**Solutions:**
```jsx
// Enable animation
<AnalogGauge 
  value={progress}
  animated={true}  // Explicitly enable
/>

// Ensure value is updating
console.log('Gauge value:', progress);

// Check browser performance
// Use Chrome DevTools Performance tab to check for jank

// Reduce animation complexity if needed
<AnalogGauge value={progress} animated={false} />
```

### Ripple Effect Not Visible

**Problem:** Ripple animation doesn't show

**Causes:**
1. Button has `overflow: hidden` cutting off ripple
2. Ripple color not visible on background
3. Animation timing too fast
4. Browser doesn't support CSS animations

**Solutions:**
```jsx
// Verify button styling
.mech-button {
  overflow: visible; /* Allow ripple to display */
}

// Check ripple color contrast
.ripple {
  background: rgba(255, 255, 255, 0.7); /* More visible */
}

// Verify animation is defined
@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
```

### Console Errors

**Common Errors & Fixes:**

```javascript
// Error: "Cannot read property 'classList' of null"
// Fix: Check that component is mounted before accessing ref

// Error: "Audio context not defined"
// Fix: Use window.AudioContext || window.webkitAudioContext

// Error: "PropTypes validation error"
// Fix: Ensure all required props are passed

// Error: "Element has deprecated/unsupported attribute"
// Fix: Use standard HTML attributes instead
```

---

## PERFORMANCE OPTIMIZATION TIPS

### For MechanicalButtons

```jsx
// Good: Uses GPU acceleration
transform: translateY(-2px);
opacity: 1;

// Avoid: Triggers layout recalculation
top: -2px;
width: 100%;
height: 100%;
```

### For AnalogGauge

```jsx
// Good: Only updates value prop
<AnalogGauge value={newValue} />

// Avoid: Recreating entire component
key={Math.random()}
```

### Memory Management

```jsx
// Good: Cleans up intervals
useEffect(() => {
  const interval = setInterval(...);
  return () => clearInterval(interval);
}, []);

// Avoid: Interval never cleared
setInterval(...); // Memory leak!
```

---

## ACCESSIBILITY

### ARIA Labels

```jsx
<MechanicalButton
  aria-label="Save settings"
  aria-pressed={isPressed}
>
  💾 Save
</MechanicalButton>
```

### Keyboard Navigation

```jsx
// Buttons receive focus
<MechanicalButton>Click</MechanicalButton>
// Tab to focus, Enter/Space to activate

// Modal management
const handleKeyDown = (e) => {
  if (e.key === 'Escape') closeModal();
};
```

### Screen Readers

```jsx
// Announce changes
<AnalogGauge
  aria-label="Phase progress"
  aria-valuenow={progress}
  aria-valuemin={0}
  aria-valuemax={100}
/>
```

---

## FURTHER RESOURCES

- **CSS Reference:** [W3C CSS Specifications](https://www.w3.org/TR/CSS/)
- **Web Audio API:** [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- **React Hooks:** [React Documentation](https://react.dev/reference/react/hooks)
- **Accessibility:** [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

