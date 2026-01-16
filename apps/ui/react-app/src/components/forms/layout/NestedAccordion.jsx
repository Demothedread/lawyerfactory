// NestedAccordion - Recursive collapsible panel system with Soviet Industrial styling
// Implements accordion patterns with nested depth support and smooth animations

import from 'react';
import "./NestedAccordion.css";

/**
 * NestedAccordion - Collapsible content panels with recursive nesting
 * 
 * Features:
 * - Recursive depth support (unlimited nesting levels)
 * - Smooth expand/collapse animations with cubic-bezier easing
 * - Soviet Industrial brutalism styling (gunmetal, brass, weathered metals)
 * - Keyboard navigation support (Space/Enter to toggle)
 * - ARIA accessibility attributes
 * - Automatic height calculation with ResizeObserver
 * - Progressive complexity revelation (content hidden until expanded)
 * 
 * @param {Array<AccordionItem>} items - Array of accordion items with title, content, children
 * @param {boolean} allowMultiple - Allow multiple panels open simultaneously (default: false)
 * @param {boolean} defaultOpen - All panels start expanded (default: false)
 * @param {number} animationDuration - Duration in ms for expand/collapse (default: 300)
 * @param {string} theme - Visual theme: 'gunmetal', 'brass', 'copper' (default: 'gunmetal')
 * @param {function} onToggle - Callback when panel toggles (itemId, isOpen)
 */
const NestedAccordion = ({
  items = [],
  allowMultiple = false,
  defaultOpen = false,
  animationDuration = 300,
  theme = 'gunmetal',
  className = '',
  onToggle = null,
}) => {
  const [openPanels, setOpenPanels] = useState(
    defaultOpen ? new Set(items.map((_, idx) => idx)) : new Set()
  );

  // Toggle panel open/closed
  const togglePanel = useCallback((index) => {
    setOpenPanels(prev => {
      const newSet = new Set(allowMultiple ? prev : []);
      if (prev.has(index)) {
        newSet.delete(index);
        onToggle?.(index, false);
      } else {
        newSet.add(index);
        onToggle?.(index, true);
      }
      return newSet;
    });
  }, [allowMultiple, onToggle]);

  // Keyboard handler for accessibility
  const handleKeyDown = useCallback((e, index) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      togglePanel(index);
    }
  }, [togglePanel]);

  return (
    <div className={`nested-accordion nested-accordion--${theme} ${className}`}>
      {items.map((item, index) => (
        <AccordionItem
          key={item.id || index}
          item={item}
          index={index}
          isOpen={openPanels.has(index)}
          onToggle={togglePanel}
          onKeyDown={handleKeyDown}
          animationDuration={animationDuration}
          theme={theme}
        />
      ))}
    </div>
  );
};

/**
 * AccordionItem - Individual collapsible panel within accordion
 */
const AccordionItem = ({
  item,
  index,
  isOpen,
  onToggle,
  onKeyDown,
  animationDuration,
  theme,
}) => {
  const contentRef = useRef(null);
  const [contentHeight, setContentHeight] = useState(0);

  // Calculate content height for smooth animation
  useEffect(() => {
    if (contentRef.current) {
      const resizeObserver = new ResizeObserver(entries => {
        setContentHeight(entries[0].target.scrollHeight);
      });
      resizeObserver.observe(contentRef.current);
      return () => resizeObserver.disconnect();
    }
  }, [item.content]);

  return (
    <div className={`accordion-item ${isOpen ? 'accordion-item--open' : ''}`}>
      <button
        className="accordion-header"
        onClick={() => onToggle(index)}
        onKeyDown={(e) => onKeyDown(e, index)}
        aria-expanded={isOpen}
        aria-controls={`accordion-content-${index}`}
      >
        <span className="accordion-title">{item.title}</span>
        <span className="accordion-icon" aria-hidden="true">
          {isOpen ? '−' : '+'}
        </span>
      </button>
      
      <div
        id={`accordion-content-${index}`}
        className="accordion-content"
        style={{
          maxHeight: isOpen ? `${contentHeight}px` : '0',
          transition: `max-height ${animationDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`,
        }}
        aria-hidden={!isOpen}
      >
        <div ref={contentRef} className="accordion-content-inner">
          {item.content}
          
          {/* Recursive nesting */}
          {item.children && item.children.length > 0 && (
            <NestedAccordion
              items={item.children}
              theme={theme}
              animationDuration={animationDuration}
              className="nested-accordion--child"
            />
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Helper function to build accordion items from phase data
 * Used for integrating with phase pipeline workflow
 */
export const buildAccordionItem = (phase, content, children = []) => ({
  id: phase.id || phase.name,
  title: phase.title || phase.name,
  content: content,
  children: children,
  metadata: {
    phase: phase.name,
    status: phase.status,
    timestamp: new Date().toISOString(),
  },
});

/**
 * PhaseAccordionWrapper - Specialized wrapper for phase-based workflows
 * Automatically structures 7-phase pipeline into accordion format
 */
export const PhaseAccordionWrapper = ({ phases, renderPhaseContent }) => {
  const accordionItems = phases.map(phase => 
    buildAccordionItem(
      phase,
      renderPhaseContent(phase),
      phase.subPhases?.map(sub => buildAccordionItem(sub, renderPhaseContent(sub)))
    )
  );

  return (
    <NestedAccordion
      items={accordionItems}
      allowMultiple={true}
      theme="gunmetal"
      animationDuration={400}
    />
  );
};

export default NestedAccordion;
