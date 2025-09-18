// Accordion component for collapsible content sections
import React, { useState } from 'react';
import {
  Accordion as MuiAccordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  IconButton,
  Chip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const Accordion = ({
  title,
  children,
  defaultExpanded = false,
  icon,
  badge,
  helpText,
  variant = 'elevation',
  disabled = false,
  onChange,
  sx = {}
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const handleChange = (event, isExpanded) => {
    setExpanded(isExpanded);
    if (onChange) {
      onChange(isExpanded);
    }
  };

  return (
    <MuiAccordion
      expanded={expanded}
      onChange={handleChange}
      variant={variant}
      disabled={disabled}
      sx={{
        mb: 1,
        '&:before': {
          display: 'none',
        },
        ...sx
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          '& .MuiAccordionSummary-content': {
            alignItems: 'center',
          }
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {icon && (
            <Box sx={{ mr: 1, display: 'flex', alignItems: 'center' }}>
              {icon}
            </Box>
          )}
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
          {badge && (
            <Chip
              label={badge.label}
              color={badge.color || 'primary'}
              size="small"
              sx={{ mr: 1 }}
            />
          )}
          {helpText && (
            <IconButton size="small" sx={{ mr: 1 }}>
              <HelpOutlineIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        {children}
      </AccordionDetails>
    </MuiAccordion>
  );
};

// AccordionGroup component for managing multiple accordions
export const AccordionGroup = ({
  accordions,
  allowMultiple = true,
  defaultExpanded = [],
  sx = {}
}) => {
  const [expandedPanels, setExpandedPanels] = useState(defaultExpanded);

  const handleChange = (panel) => (event, isExpanded) => {
    if (allowMultiple) {
      setExpandedPanels(prev =>
        isExpanded
          ? [...prev, panel]
          : prev.filter(item => item !== panel)
      );
    } else {
      setExpandedPanels(isExpanded ? [panel] : []);
    }
  };

  return (
    <Box sx={sx}>
      {accordions.map((accordion, index) => (
        <Accordion
          key={accordion.id || index}
          title={accordion.title}
          icon={accordion.icon}
          badge={accordion.badge}
          helpText={accordion.helpText}
          defaultExpanded={expandedPanels.includes(accordion.id || index)}
          onChange={handleChange(accordion.id || index)}
          sx={accordion.sx}
        >
          {accordion.content}
        </Accordion>
      ))}
    </Box>
  );
};

export default Accordion;