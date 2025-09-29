// Soviet Industrial UI Components Library
// Professional control terminal components with authentic Soviet industrial aesthetic

export { default as MetalPanel } from './MetalPanel';
export { default as AnalogGauge } from './AnalogGauge';
export { default as ToggleSwitch } from './ToggleSwitch';
export { default as NixieDisplay } from './NixieDisplay';
export { default as MechanicalButton } from './MechanicalButton';
export { default as StatusLights } from './StatusLights';

// Component collections for easy importing
export const SovietComponents = {
  MetalPanel,
  AnalogGauge,
  ToggleSwitch,
  NixieDisplay,
  MechanicalButton,
  StatusLights,
};

// Hook for managing Soviet component themes
export const useSovietTheme = () => {
  const theme = {
    colors: {
      brass: 'var(--soviet-brass)',
      bronze: 'var(--soviet-bronze)',
      emerald: 'var(--soviet-emerald)',
      crimson: 'var(--soviet-crimson)',
      silver: 'var(--soviet-silver)',
      charcoal: 'var(--soviet-charcoal)',
      steel: 'var(--soviet-steel)',
      amber: 'var(--soviet-amber)',
      warning: 'var(--soviet-warning)',
      success: 'var(--soviet-success)',
    },
    spacing: {
      xs: 'var(--space-xs)',
      sm: 'var(--space-sm)',
      md: 'var(--space-md)',
      lg: 'var(--space-lg)',
      xl: 'var(--space-xl)',
      xxl: 'var(--space-xxl)',
    },
    typography: {
      xs: 'var(--text-xs)',
      sm: 'var(--text-sm)',
      md: 'var(--text-md)',
      lg: 'var(--text-lg)',
      xl: 'var(--text-xl)',
      xxl: 'var(--text-xxl)',
    },
  };

  return theme;
};