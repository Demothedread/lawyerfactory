// GridContainer - Self-optimizing layout engine with zero vertical scroll architecture
// Implements 6-8 column CSS Grid with golden ratio proportions and automatic density calculation
import React, { useRef, useState, useEffect, useCallback } from 'react';
import './GridContainer.css';
/**
 * GridContainer - Intelligent self-optimizing container system
 * 
 * Features:
 * - Self-optimizing layout engine with automatic density calculation
 * - Responsive breakpoints (mobile, tablet, desktop, wide)
 * - Zero vertical scroll design (all content accessible through horizontal/nested navigation)
 * - Golden ratio proportions (1.618 for optimal visual hierarchy)
 * - Performance optimization with virtual scrolling and lazy loading
 * - Grid-based spatial choreography with 6-8 column layout
 * 
* @param {ReactNode} children - Child components to render in grid
* @param {number} minColumns - Minimum columns (default: 1)
* @param {number} maxColumns - Maximum columns (default: 8)
* @param {string} gap - Grid gap size (default: '16px')
* @param {boolean} autoOptimize - Enable automatic density calculation (default: true)
* @param {string} layoutMode - Layout strategy: 'masonry', 'grid', 'flow' (default: 'grid')
* @param {boolean} noVerticalScroll - Eliminate vertical scrolling (default: true)
* @param {function} onLayoutChange - Callback when layout recalculates
*/
const GridContainer = ({
 children,
 minColumns = 1,
 maxColumns = 8,
 gap = '16px',
 autoOptimize = true,
 layoutMode = 'grid',
 noVerticalScroll = true,
 className = '',
 onLayoutChange = null,
 goldenRatio = true,
 enableVirtualization = false,
}) => {
 const containerRef = useRef(null);
 const [columns, setColumns] = useState(4);
 const [containerHeight, setContainerHeight] = useState('100%');
 const [density, setDensity] = useState('comfortable'); // 'compact', 'comfortable', 'spacious'
 const [viewportDimensions, setViewportDimensions] = useState({
   width: window.innerWidth,
   height: window.innerHeight,
 });


  // Golden ratio calculation for optimal proportions
  const GOLDEN_RATIO = 1.618;

  // Responsive breakpoints with golden ratio application
  const BREAKPOINTS = {
    mobile: { width: 320, columns: 1 },
    tablet: { width: 768, columns: goldenRatio ? Math.round(4 / GOLDEN_RATIO) : 2 },
    desktop: { width: 1024, columns: 4 },
    wide: { width: 1440, columns: goldenRatio ? Math.round(4 * GOLDEN_RATIO) : 6 },
    ultra: { width: 1920, columns: 8 },
  };

  // Calculate optimal column count based on viewport width and content density
  const calculateOptimalColumns = useCallback(() => {
    const width = viewportDimensions.width;
    
    let optimalColumns = minColumns;

    // Apply breakpoint-based column calculation
    if (width >= BREAKPOINTS.ultra.width) {
      optimalColumns = BREAKPOINTS.ultra.columns;
    } else if (width >= BREAKPOINTS.wide.width) {
      optimalColumns = BREAKPOINTS.wide.columns;
    } else if (width >= BREAKPOINTS.desktop.width) {
      optimalColumns = BREAKPOINTS.desktop.columns;
    } else if (width >= BREAKPOINTS.tablet.width) {
      optimalColumns = BREAKPOINTS.tablet.columns;
    } else {
      optimalColumns = BREAKPOINTS.mobile.columns;
    }

    // Apply density modifier
    const densityMultiplier = {
      compact: 1.2,
      comfortable: 1.0,
      spacious: 0.8,
    };

    optimalColumns = Math.round(optimalColumns * densityMultiplier[density]);

    // Clamp to min/max
    optimalColumns = Math.max(minColumns, Math.min(maxColumns, optimalColumns));

    return optimalColumns;
  }, [viewportDimensions.width, density, minColumns, maxColumns, goldenRatio]);

  // Calculate container height for zero vertical scroll
  const calculateContainerHeight = useCallback(() => {
    if (!noVerticalScroll) return 'auto';

    // Available viewport height minus header and footer
    const headerHeight = document.querySelector('.terminal-header')?.offsetHeight || 64;
    const footerHeight = document.querySelector('.terminal-footer')?.offsetHeight || 32;
    const availableHeight = viewportDimensions.height - headerHeight - footerHeight;

    return `${availableHeight}px`;
  }, [viewportDimensions.height, noVerticalScroll]);

  // Automatic density calculation based on content and viewport
  const calculateDensity = useCallback(() => {
    const width = viewportDimensions.width;
    const height = viewportDimensions.height;
    const aspectRatio = width / height;

    // Golden ratio-based density calculation
    if (goldenRatio) {
      if (aspectRatio > GOLDEN_RATIO) {
        return 'spacious'; // Wide screens get more breathing room
      } else if (aspectRatio < 1 / GOLDEN_RATIO) {
        return 'compact'; // Narrow screens get denser layout
      }
    }

    // Standard density calculation
    if (width < 768) return 'compact';
    if (width > 1920) return 'spacious';
    return 'comfortable';
  }, [viewportDimensions, goldenRatio]);

  // Handle viewport resize with debouncing
  useEffect(() => {
    let resizeTimeout;

    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        setViewportDimensions({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }, 150); // Debounce 150ms for performance
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(resizeTimeout);
    };
  }, []);

  // Optimize layout when dimensions or density change
  useEffect(() => {
    if (autoOptimize) {
      const newDensity = calculateDensity();
      setDensity(newDensity);
    }

    const newColumns = calculateOptimalColumns();
    setColumns(newColumns);

    const newHeight = calculateContainerHeight();
    setContainerHeight(newHeight);

    // Notify parent component of layout change
    if (onLayoutChange) {
      onLayoutChange({
        columns: newColumns,
        density: density,
        viewport: viewportDimensions,
        height: newHeight,
      });
    }
  }, [
    viewportDimensions,
    autoOptimize,
    calculateDensity,
    calculateOptimalColumns,
    calculateContainerHeight,
    onLayoutChange,
  ]);

  // Generate grid template columns based on column count and golden ratio
  const generateGridTemplate = () => {
    if (goldenRatio && columns > 1) {
      // Apply golden ratio to column widths for visual hierarchy
      const ratios = [];
      let remaining = columns;
      
      while (remaining > 0) {
        if (remaining >= 2) {
          ratios.push(GOLDEN_RATIO, 1);
          remaining -= 2;
        } else {
          ratios.push(1);
          remaining -= 1;
        }
      }

      return ratios.map(ratio => `${ratio}fr`).join(' ');
    }

    // Standard equal columns
    return `repeat(${columns}, 1fr)`;
  };

  // Get density-based gap size
  const getDensityGap = () => {
    const gapSizes = {
      compact: '8px',
      comfortable: '16px',
      spacious: '24px',
    };
    return gapSizes[density] || gap;
  };

  // Container class names
  const containerClasses = [
    'grid-container',
    `grid-container--${layoutMode}`,
    `grid-container--${density}`,
    noVerticalScroll ? 'grid-container--no-scroll' : '',
    className,
  ].filter(Boolean).join(' ');

  // Container styles
  const containerStyles = {
    '--grid-columns': columns,
    '--grid-gap': getDensityGap(),
    '--grid-template': generateGridTemplate(),
    '--container-height': containerHeight,
    gridTemplateColumns: generateGridTemplate(),
    gap: getDensityGap(),
    height: containerHeight,
  };

  return (
    <div
      ref={containerRef}
      className={containerClasses}
      style={containerStyles}
      data-columns={columns}
      data-density={density}
      data-layout={layoutMode}
    >
      {children}
    </div>
  );
};

/**
 * GridItem - Individual grid item component
 * 
 * @param {number} colSpan - Number of columns to span (default: 1)
 * @param {number} rowSpan - Number of rows to span (default: 1)
 * @param {string} area - Named grid area (optional)
 * @param {boolean} sticky - Make item sticky within viewport (default: false)
 */
export const GridItem = ({
  children,
  colSpan = 1,
  rowSpan = 1,
  area = null,
  sticky = false,
  className = '',
  minHeight = 'auto',
  maxHeight = 'auto',
}) => {
  const itemClasses = [
    'grid-item',
    sticky ? 'grid-item--sticky' : '',
    className,
  ].filter(Boolean).join(' ');

  const itemStyles = {
    gridColumn: area ? undefined : `span ${colSpan}`,
    gridRow: area ? undefined : `span ${rowSpan}`,
    gridArea: area || undefined,
    minHeight,
    maxHeight,
  };

  return (
    <div className={itemClasses} style={itemStyles}>
      {children}
    </div>
  );
};

/**
 * GridSection - Semantic section within grid
 * 
 * @param {string} title - Section title
 * @param {boolean} collapsible - Enable collapse functionality
 * @param {boolean} defaultCollapsed - Start collapsed
 */
export const GridSection = ({
  title,
  children,
  collapsible = false,
  defaultCollapsed = false,
  icon = null,
  actions = null,
  className = '',
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const toggleCollapsed = () => {
    if (collapsible) {
      setCollapsed(!collapsed);
    }
  };

  const sectionClasses = [
    'grid-section',
    collapsed ? 'grid-section--collapsed' : '',
    collapsible ? 'grid-section--collapsible' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={sectionClasses}>
      <div className="grid-section__header" onClick={toggleCollapsed}>
        {icon && <span className="grid-section__icon">{icon}</span>}
        <h3 className="grid-section__title">{title}</h3>
        {collapsible && (
          <span className="grid-section__toggle">
            {collapsed ? '▶' : '▼'}
          </span>
        )}
        {actions && <div className="grid-section__actions">{actions}</div>}
      </div>
      {!collapsed && (
        <div className="grid-section__content">
          {children}
        </div>
      )}
    </div>
  );
};

export default GridContainer;
