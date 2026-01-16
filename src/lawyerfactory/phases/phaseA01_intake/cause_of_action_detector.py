# Shim file to redirect cause_of_action_detector imports to the correct location
from lawyerfactory.phases.phaseA03_outline.claims.detect import *

# Re-export the main classes for backward compatibility
from lawyerfactory.phases.phaseA03_outline.claims.detect import (
    CauseOfActionDetector,
    CauseDetectionResult,
)