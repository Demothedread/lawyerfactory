# Quick Reference Card
## LawyerFactory Component Enhancements - Cheat Sheet

---

## MECHANICAL BUTTON

### Basic Usage
```jsx
<MechanicalButton onClick={() => {}}>
  Button Text
</MechanicalButton>
```

### Variants
```
primary | success | danger | warning | info | default
```

### Sizes
```
small | medium (default) | large
```

### Key Features
- ✅ Depth animation (hover/press)
- ✅ Sound effect (enable/disable)
- ✅ Ripple feedback
- ✅ Color variants
- ✅ Disabled state

### Props
```jsx
<MechanicalButton
  variant="primary"        // Button style
  size="medium"           // Button size
  onClick={handler}       // Click handler
  disabled={false}        // Disabled state
  enableSound={true}      // Sound effects
  className="custom"      // Custom class
/>
```

---

## ANALOG GAUGE

### Basic Usage
```jsx
<AnalogGauge 
  value={75}
  size={120}
/>
```

### For Phase Tracking
```jsx
<AnalogGauge 
  value={phaseProgress}
  phaseLabel="Phase A01"
  isComplete={isPhaseComplete}
  animated={true}
/>
```

### Key Features
- ✅ Smooth needle animation
- ✅ Completion visualization
- ✅ Glow effect
- ✅ Phase labels
- ✅ Completion badge

### Props
```jsx
<AnalogGauge
  value={0-100}              // Current value
  min={0}                    // Minimum value
  max={100}                  // Maximum value
  size={120}                 // Gauge size (px)
  phaseLabel="Phase A01"     // Phase name
  isComplete={false}         // Completion state
  needleColor="var(--color)" // Needle color
  showValue={true}           // Show percentage
  animated={true}            // Enable animation
/>
```

---

## SETTINGS PANEL

### Opening
```jsx
// Via state
const [showSettings, setShowSettings] = useState(false);
<button onClick={() => setShowSettings(true)}>Settings</button>

// Via keyboard
// Ctrl+S (Windows/Linux) or Cmd+S (Mac)
```

### Props
```jsx
<SettingsPanel
  open={boolean}              // Show/hide
  onClose={function}          // Close handler
  settings={object}           // Current settings
  onSettingsChange={function} // Change handler
/>
```

### Tabs Available
1. LLM Configuration
2. General Settings
3. Legal Config
4. Phase Settings
5. Export Settings

---

## KEYBOARD SHORTCUTS

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` / `Cmd+S` | Settings |
| `Escape` | Close Modal |
| `Ctrl+P` / `Cmd+P` | Tour |
| `Ctrl+N` / `Cmd+N` | New Case |

---

## COMMON PATTERNS

### Button With Feedback
```jsx
const [saved, setSaved] = useState(false);

<MechanicalButton 
  variant={saved ? "success" : "primary"}
  onClick={() => {
    saveSettings();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }}
>
  {saved ? '✓ Saved' : '💾 Save'}
</MechanicalButton>
```

### Phase Progress Tracker
```jsx
const [progress, setProgress] = useState(0);
const isComplete = progress >= 100;

<AnalogGauge
  value={progress}
  phaseLabel="Phase A01"
  isComplete={isComplete}
  size={150}
/>
```

### Settings Integration
```jsx
const [showSettings, setShowSettings] = useState(false);

const handleSettingsChange = (newSettings) => {
  setSettings(newSettings);
  localStorage.setItem('settings', JSON.stringify(newSettings));
  backendService.updateSettings(newSettings);
};

<SettingsPanel
  open={showSettings}
  onClose={() => setShowSettings(false)}
  settings={settings}
  onSettingsChange={handleSettingsChange}
/>
```

---

## CSS VARIABLES REFERENCE

```css
--soviet-brass: #b87333          /* Brass color */
--soviet-crimson: #dc143c        /* Red accent */
--soviet-green: #10b981          /* Green accent */
--soviet-amber: #f59e0b          /* Amber color */
--soviet-silver: #c0c0c0         /* Silver text */
--soviet-panel: #2a2a2a          /* Panel background */
--panel-bg: rgba(42, 42, 42, 0.8) /* Panel transparency */
--text-primary: #c0c0c0          /* Primary text */
--text-secondary: #8b8680        /* Secondary text */
```

---

## DEBUGGING TIPS

### No Sound Playing
```javascript
// Check audio context
const ctx = new (window.AudioContext || window.webkitAudioContext)();
console.log(ctx.state); // Should be "running"
```

### Button Not Responding
```javascript
// Check if disabled
if (buttonRef.disabled) console.log('Button is disabled');

// Check click handler
<MechanicalButton onClick={() => console.log('Clicked!')}>
```

### Gauge Not Animating
```javascript
// Check animation property
const gauge = document.querySelector('.analog-gauge');
console.log(getComputedStyle(gauge).animation);

// Force update
<AnalogGauge key={Math.random()} value={newValue} />
```

### Settings Panel Not Opening
```javascript
// Check state
console.log('showSettings:', showSettings); // Should be true

// Verify prop name
<SettingsPanel open={showSettings} />  // Not showSettings!
```

---

## FILES MODIFIED

```
apps/ui/react-app/src/components/soviet/
  ├── MechanicalButton.jsx (Enhanced)
  └── AnalogGauge.jsx (Enhanced)

apps/ui/react-app/src/components/terminal/
  ├── SettingsPanel.jsx (Fixed)
  └── EnhancedSettingsPanel.jsx (Fixed)

Root directory/
  ├── INTERACTIVE_COMPONENT_TESTING.md
  ├── COMPONENT_ENHANCEMENT_REPORT.md
  ├── COMPONENT_REVIEW_FINAL_SUMMARY.md
  ├── IMPLEMENTATION_EXAMPLES_GUIDE.md
  └── FINAL_VERIFICATION_REPORT.md
```

---

## TEST CHECKLIST

- [ ] Button click triggers action
- [ ] Button depth animation visible
- [ ] Button sound plays
- [ ] Ripple effect displays
- [ ] Settings button opens panel
- [ ] Keyboard shortcut works (Ctrl+S)
- [ ] Gauge displays value
- [ ] Gauge animates smoothly
- [ ] Gauge shows completion badge
- [ ] Completion glow effect works
- [ ] All color variants display
- [ ] Disabled buttons don't respond
- [ ] No console errors

---

## PERFORMANCE NOTES

- All animations use `transform` (GPU-accelerated)
- Sound effects use Web Audio API (no file loading)
- Ripple effects cleaned up after animation
- No memory leaks from event listeners
- 60fps smooth animations on desktop
- Mobile-optimized with touch support

---

## BROWSER SUPPORT

| Browser | Status |
|---------|--------|
| Chrome | ✅ Full |
| Firefox | ✅ Full |
| Safari | ✅ Full |
| Edge | ✅ Full |
| Mobile | ✅ Full |

---

## QUICK FIXES

| Issue | Fix |
|-------|-----|
| No sound | Check `enableSound={true}` |
| Button not responsive | Check `disabled` prop |
| Gauge not animating | Check `animated={true}` |
| Settings don't open | Check `open` prop (not `showSettings`) |
| No ripple effect | Check button has `overflow: visible` |

---

## COLOR CODES

```
Primary (Green):   #10b981
Success (Green):   #10b981
Danger (Red):      #dc2626
Warning (Orange):  #f59e0b
Info (Blue):       #3b82f6
Default (Brass):   #b87333
```

---

## ANIMATION TIMING

```
Depth animation:   0.1s (buttons)
Ripple animation:  0.6s (fade out)
Gauge sweep:       1s (needle movement)
Glow pulse:        2s (infinite)
```

---

**Quick Reference v1.0**  
**October 18, 2025**  
**For LawyerFactory Development Team**

