// NeonPhaseCard - Soviet Industrial neon-themed phase visualization card with MagicUI enhancements
import {
    Assignment,
    CheckCircle,
    CloudUpload,
    Description,
    Download,
    Error as ErrorIcon,
    PlayArrow,
    Schedule,
    Timeline,
    Visibility,
} from '@mui/icons-material';
import { useEffect, useState } from 'react';
import { downloadDeliverable, getPhaseA03Deliverables } from '../../services/backendService';
// MagicUI neon card components
import { BorderBeam } from './BorderBeam';
import { NeonGradientCard } from './NeonGradientCard';
import { SparklesText } from './SparklesText';
// Styles
import '../../styles/magicui-neon-card-overrides.css';
import '../../styles/neon-soviet.css';


