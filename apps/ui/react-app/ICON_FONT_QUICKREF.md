# Soviet Atomic Age Thematic Icons & Fonts - Quick Reference

## Quick Icon Usage

```jsx
import { getIcon } from '@/constants/thematicIcons';

// Common icons:
{getIcon('search')}      // ⊙
{getIcon('settings')}    // ⚙
{getIcon('complete')}    // ✓
{getIcon('error')}       // ✕
{getIcon('upload')}      // ⤴
{getIcon('download')}    // ⤵
{getIcon('workflow')}    // ⟳
{getIcon('legal')}       // ⬢
{getIcon('analysis')}    // ◈
{getIcon('evidence')}    // ▬
{getIcon('outline')}     // ▬
```

## Font Improvements Made

### Before → After

| Element | Before | After |
|---------|--------|-------|
| Body text | Share Tech Mono | Courier New |
| Line height | 1.4 | 1.6 |
| Letter spacing | 0px | 0.2-0.3px |
| Font size | 12px | 13px |
| Form inputs | Share Tech Mono | Courier New |

### Result: Enhanced Readability
- Wider spacing between letters improves legibility
- Courier New is more readable than Share Tech Mono
- Increased line height reduces eye strain
- Consistent across all form elements

## Icon System Architecture

### Centralized Management
- **File**: `/src/constants/thematicIcons.js`
- **Function**: `getIcon(key)` - returns Unicode character
- **Categories**: 11 organized categories with 60+ icons

### Thematic Consistency
- All icons use **Unicode mechanical symbols**, not emoji
- Soviet atomic age aesthetic: Heavy machinery, brutalism
- No generic emoji feeling - authentic industrial look

## Component Integration

### EnhancedSettingsPanel
- Tab headers: `getIcon('llm')`, `getIcon('settings')`, `getIcon('legal')`
- Buttons: `getIcon('save')`, `getIcon('delete')`, `getIcon('complete')`
- Status messages: Updated to use mechanical symbols

### App.jsx
- Navigation tabs: System, Evidence, Pipeline, Cases, Documents, Claims, etc.
- Action buttons: Search, New Case, Upload, Settings
- Status indicators: Online/Offline
- Section headers: Dashboard, Claims Matrix, Shot List, Outline

## Font Implementation

### Typography Settings (App.jsx)
```javascript
const getSovietTheme = (darkMode = true) => createTheme({
  typography: {
    fontFamily: '"Courier New", "JetBrains Mono", "Share Tech Mono", monospace',
    fontSize: 13,
    lineHeight: 1.6,
    letterSpacing: '0.3px',
    body1: { lineHeight: 1.7, letterSpacing: '0.3px' },
    body2: { lineHeight: 1.6, letterSpacing: '0.2px' },
    // Heading fonts preserve Orbitron/Russo One for industrial aesthetic
  }
});
```

### CSS Enhancement
- **File**: `/src/components/styles/formElements.css`
- **Coverage**: Form inputs, selects, labels, range sliders
- **Result**: Consistent readable monospace across all controls

## Styling Hierarchy

### Color Scheme (Unchanged)
```css
--soviet-brass: #b58558     /* Primary accent */
--soviet-crimson: #9d263e   /* Secondary accent */
--soviet-green: (varied)    /* Success state */
--soviet-amber: #ffb000     /* Warning state */
--soviet-charcoal: #0e0d0d  /* Background */
```

### Font Stack Order
1. **Primary**: Courier New (system font, fast load)
2. **Fallback**: JetBrains Mono (Google Fonts, modern)
3. **Fallback**: Share Tech Mono (Google Fonts, industrial)
4. **Final**: monospace (system default)

## Migration Notes

### For Developers Adding Icons
1. Add icon to `THEMATIC_ICONS` in `/src/constants/thematicIcons.js`
2. Import `getIcon` in your component
3. Use `{getIcon('your_icon_key')}` in JSX
4. No need to import Unicode directly

### For Component Updates
Search/Replace emoji patterns:
- `🔍` → `{getIcon('search')}`
- `⚙️` → `{getIcon('settings')}`
- `✓` → `{getIcon('complete')}`
- `✕` → `{getIcon('error')}`
- `📤` → `{getIcon('upload')}`
- `📥` → `{getIcon('download')}`

### Testing
- Verify all text displays clearly
- Check icon rendering on different browsers
- Test at different zoom levels (90%, 100%, 110%, etc.)
- Validate keyboard navigation still works

## Browser Support

| Browser | Unicode Support | Font Loading |
|---------|-----------------|--------------|
| Chrome/Edge | ✓ | ✓ |
| Firefox | ✓ | ✓ |
| Safari | ✓ | ✓ |
| IE11 | ✓ | ⚠️ (Fallback fonts) |

## Performance Impact

- **Zero additional HTTP requests** (Unicode symbols)
- **Fonts cached** at browser level
- **CSS-only styling** (no JS icon rendering)
- **Minimal bundle increase** (static constant)

## Accessibility

✓ Icons paired with text labels  
✓ High contrast with Courier New  
✓ Proper line-height for screen readers  
✓ Color not solely relied upon  
✓ ARIA attributes maintained  

## Debugging

If icons don't appear:
1. Check console for import errors
2. Verify `thematicIcons.js` exists at `/src/constants/`
3. Ensure `getIcon()` function is exported
4. Test in browser console: `getIcon('search')`

If fonts look wrong:
1. Check Google Fonts loaded in DevTools
2. Verify CSS cascade (browser dev tools)
3. Clear browser cache
4. Test with system fonts enabled

## Philosophy

- **Not generic**: Themed icons feel authentic to Soviet atomic age
- **Minimal**: Unicode reduces complexity vs. icon fonts
- **Maintainable**: Centralized icon definitions
- **Extensible**: Easy to add more icons or font changes
- **Themeable**: Can swap fonts/colors in one place
