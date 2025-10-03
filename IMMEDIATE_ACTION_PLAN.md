# Immediate Action Plan for LawyerFactory

## 🔴 Critical Fix: React App Black Screen

### Step 1: Diagnose React App
```bash
cd apps/ui/react-app
npm install  # Ensure dependencies
npm run build  # Test build
npm run dev  # Test development server
```

### Step 2: Check Vite Config
The vite.config.js needs proper server and proxy configuration for API calls.

### Step 3: Verify API Connection
Ensure the React app can reach the backend API server.

---

## 🟡 High Priority: Code Consolidation

### Files to Consolidate (violating no_duplicate_enhanced rule):

#### Storage APIs
- **KEEP**: `src/lawyerfactory/storage/core/unified_storage_api.py`
- **MERGE & DELETE**: `src/lawyerfactory/storage/core/enhanced_unified_storage_api.py`
- **DELETE DUPLICATE**: `src/lawyerfactory/storage/enhanced_unified_storage_api.py`

#### Research Bots
- **KEEP**: `src/lawyerfactory/phases/phaseA02_research/research_bot.py`
- **MERGE & DELETE**: `src/lawyerfactory/phases/phaseA02_research/enhanced_research_bot.py`

#### Outline Generators
- **KEEP**: `src/lawyerfactory/outline/generator.py`
- **MERGE & DELETE**: `src/lawyerfactory/outline/enhanced_generator.py`

#### Maestro/Workflow (Multiple implementations)
- **KEEP**: `src/lawyerfactory/compose/maestro/maestro.py`
- **REVIEW & MERGE**: All workflow_*.py variants
- **DELETE**: Legacy implementations

#### Model Definitions
- **KEEP**: `src/lawyerfactory/lf_core/models.py`
- **MERGE & DELETE**: `models_shared.py`, `models_shared_new.py`

---

## 🟢 Quick Wins: Immediate Cleanup

### 1. Remove Trash/Temp Directories
```bash
rm -rf _trash_staging/
rm -rf trash/
rm -rf test_path/
```

### 2. Consolidate Documentation
- Keep only one README per directory
- Move all guides to main README.md

### 3. Fix Import Paths
After consolidation, update all imports throughout the codebase.

---

## 📋 Consolidation Script

Create a script to automate the consolidation:

```python
#!/usr/bin/env python3
"""
consolidate.py - Merges enhanced files back to canonical versions
"""

import os
import shutil
from pathlib import Path

CONSOLIDATION_MAP = {
    'src/lawyerfactory/storage/core/enhanced_unified_storage_api.py': 
        'src/lawyerfactory/storage/core/unified_storage_api.py',
    'src/lawyerfactory/phases/phaseA02_research/enhanced_research_bot.py':
        'src/lawyerfactory/phases/phaseA02_research/research_bot.py',
    'src/lawyerfactory/outline/enhanced_generator.py':
        'src/lawyerfactory/outline/generator.py',
}

def consolidate_files():
    for enhanced, canonical in CONSOLIDATION_MAP.items():
        if os.path.exists(enhanced):
            print(f"Merging {enhanced} -> {canonical}")
            # TODO: Implement intelligent merging logic
            # For now, manual review required
            
if __name__ == "__main__":
    consolidate_files()
```

---

## 🚀 Launch Sequence

### 1. Start Backend API
```bash
cd apps/api
python simple_server.py
# or
python server.py
```

### 2. Start Frontend (after fixing)
```bash
cd apps/ui/react-app
npm run dev
```

### 3. Verify System Health
- Check API endpoints: http://localhost:5000/
- Check React app: http://localhost:5173/
- Review logs for errors

---

## 📊 Success Metrics

- [ ] React app loads without black screen
- [ ] All "enhanced" files consolidated
- [ ] Single maestro/workflow implementation
- [ ] All imports updated and working
- [ ] Tests passing
- [ ] Knowledge graph updated

---

## 🔄 Daily Maintenance Tasks

1. Run consolidation check
2. Update knowledge_graph.json
3. Remove any new "enhanced" files
4. Verify no duplicate functionality
5. Check for and fix broken imports

---

*Follow rooinstructions.json strictly during all consolidation work*