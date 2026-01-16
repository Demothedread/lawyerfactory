# 📋 Import Migration Guide - apiService → backendService

**Status**: Migration in Progress  
**Shim**: ✅ Active (backward compatibility enabled)  
**Files to Migrate**: 10 component files  
**Timeline**: Gradual, test-as-you-go  

---

## 🎯 Overview

### Current State
- ✅ `backendService.js` exists (new unified service)
- ✅ `apiService.js` shim exists (backward compatibility layer)
- ⚠️ 10 component files still import from deprecated `apiService.js`

### Goal
Migrate all 10 component files to import directly from `backendService.js`

### Why
- Remove indirection layer (performance)
- Single source of truth
- Clear code intent
- Prepare for removal of deprecated shim

---

## 📊 Files to Migrate

### Import Categories

**Named Exports** (7 files):
```javascript
import { apiService } from '../../services/apiService';
```

**Default Export** (1 file):
```javascript
import apiService from '../../services/apiService';
```

**Function Imports** (2 files):
```javascript
import { fetchLLMConfig, updateLLMConfig } from '../../services/apiService';
import { generateSkeletalOutline, getClaimsMatrix, getSocket, startPhase } from '../services/apiService';
```

---

## ✅ Migration List

### Phase Components (5 files)

#### 1. PhaseA01Intake.jsx
**Current**:
```javascript
import { apiService } from '../../services/apiService';
```

**New**:
```javascript
import { backendService } from '../../services/backendService';
```

**Replace Usages**:
```javascript
// Find and replace all instances
apiService → backendService
```

---

#### 2. PhaseA02Research.jsx
**Current**:
```javascript
import { apiService } from '../../services/apiService';
```

**New**:
```javascript
import { backendService } from '../../services/backendService';
```

**Replace Usages**:
```javascript
apiService → backendService
```

---

#### 3. PhaseA03Outline.jsx
**Current**:
```javascript
import { apiService } from '../../services/apiService';
```

**New**:
```javascript
import { backendService } from '../../services/backendService';
```

**Replace Usages**:
```javascript
apiService → backendService
```

---

#### 4. PhaseC01Editing.jsx
**Current**:
```javascript
import { apiService } from '../../services/apiService';
```

**New**:
```javascript
import { backendService } from '../../services/backendService';
```

**Replace Usages**:
```javascript
apiService → backendService
```

---

#### 5. PhaseC02Orchestration.jsx
**Current**:
```javascript
import { apiService } from '../../services/apiService';
```

**New**:
```javascript
import { backendService } from '../../services/backendService';
```

**Replace Usages**:
```javascript
apiService → backendService
```

---

### Review Component (1 file)

#### 6. PhaseB01Review.jsx
**Current**:
```javascript
import apiService from '../../services/apiService';  // Default export
```

**New**:
```javascript
import { backendService } from '../../services/backendService';  // Named export
```

**Replace Usages**:
```javascript
apiService → backendService
```

---

### Other Components (4 files)

#### 7. DraftingPhase.jsx
**Current**:
```javascript
import { generateSkeletalOutline, getClaimsMatrix, getSocket, startPhase } from '../services/apiService';
```

**New**:
```javascript
import { generateSkeletalOutline, getClaimsMatrix, getSocket, startPhase } from '../services/backendService';
```

**Action**: Update import path only

---

#### 8. EnhancedSettingsPanel.jsx
**Current**:
```javascript
import { fetchLLMConfig, updateLLMConfig } from '../../services/apiService';
```

**New**:
```javascript
import { fetchLLMConfig, updateLLMConfig } from '../../services/backendService';
```

**Action**: Update import path only

---

#### 9. SettingsPanel.jsx
**Current**:
```javascript
import { fetchLLMConfig, updateLLMConfig } from '../../services/apiService';
```

**New**:
```javascript
import { fetchLLMConfig, updateLLMConfig } from '../../services/backendService';
```

**Action**: Update import path only

---

#### 10. NeonPhaseCard.jsx
**Current**:
```javascript
import { downloadDeliverable, getPhaseA03Deliverables } from '../../services/apiService';
```

**New**:
```javascript
import { downloadDeliverable, getPhaseA03Deliverables } from '../../services/backendService';
```

**Action**: Update import path only

---

## 🚀 Migration Steps

### Step 1: Verify Shim Works
```bash
cd apps/ui/react-app
npm run dev
# Check browser console - should see deprecation warning
# App should work normally
```

### Step 2: Migrate Files One-by-One

Pick a file to migrate (e.g., NeonPhaseCard.jsx):

```bash
# Edit the file
# Update import statement
# Update apiService references to backendService
# Test in browser
# Verify no console errors
```

### Step 3: Test Each Migration

```javascript
// Example test pattern
// Before migration
import { downloadDeliverable } from '../../services/apiService';

// After migration  
import { downloadDeliverable } from '../../services/backendService';

// Component should work identically
// Check for any console errors or warnings
```

### Step 4: Gradual Rollout

**Recommended Order** (by dependency):
1. Utility components first (NeonPhaseCard, EnhancedSettingsPanel, SettingsPanel)
2. Data-heavy components (DraftingPhase)
3. Phase components (A01, A02, A03, B01, C01, C02)
4. Core components last

---

## 📝 Import Patterns

### Pattern 1: Named Export (Most Common)
```javascript
// OLD
import { apiService } from '../../services/apiService';

// NEW
import { backendService } from '../../services/backendService';

// In code
apiService.executePhase()  →  backendService.executePhase()
```

### Pattern 2: Function Exports
```javascript
// OLD
import { fetchLLMConfig, updateLLMConfig } from '../../services/apiService';

// NEW
import { fetchLLMConfig, updateLLMConfig } from '../../services/backendService';

// In code (no change needed)
fetchLLMConfig()  →  fetchLLMConfig()
```

### Pattern 3: Default Export (Rare)
```javascript
// OLD
import apiService from '../../services/apiService';

// NEW
import { backendService } from '../../services/backendService';

// In code
apiService.method()  →  backendService.method()
```

---

## ✔️ Verification Checklist

After migrating each file:

- [ ] File imports from `backendService.js`
- [ ] No references to `apiService` remain
- [ ] Component renders without errors
- [ ] No console errors or warnings
- [ ] Functions work as expected
- [ ] No console deprecation warning for that file's imports
- [ ] Tests pass (if applicable)

---

## 🔄 Rollback Plan

If migration breaks something:

1. **Immediate Rollback**:
   ```javascript
   // Revert import change
   import { apiService } from '../../services/apiService';
   import { backendService } from '../../services/backendService';
   
   // Shim is still active, so old import will work
   ```

2. **Why This is Safe**:
   - Shim re-exports everything from backendService.js
   - No breaking changes in function signatures
   - Same functionality guaranteed

---

## 📊 Migration Tracking

---

## 📊 Migration Tracking

```
File                           Status    Date      Notes
────────────────────────────────────────────────────────
PhaseA01Intake.jsx             ✅ DONE   2024-10   Migrated to backendService
PhaseA02Research.jsx           ✅ DONE   2024-10   Migrated to backendService
PhaseA03Outline.jsx            ✅ DONE   2024-10   Migrated to backendService
PhaseB01Review.jsx             ✅ DONE   2024-10   Migrated to backendService
PhaseC01Editing.jsx            ✅ DONE   2024-10   Migrated to backendService
PhaseC02Orchestration.jsx      ✅ DONE   2024-10   Migrated to backendService
DraftingPhase.jsx              ✅ DONE   2024-10   Migrated to backendService
EnhancedSettingsPanel.jsx      ✅ DONE   2024-10   Migrated to backendService
SettingsPanel.jsx              ✅ DONE   2024-10   Migrated to backendService
NeonPhaseCard.jsx              ✅ DONE   2024-10   Migrated to backendService
```

**Migration Status**: ✅ ALL COMPLETE (10/10 files migrated)

---

````

---

## 🎯 Phases

### Phase 1: Setup & Verification
- [x] Create shim (apiService.js)
- [x] Verify backward compatibility
- [ ] Communicate migration plan to team
- [ ] Set up tracking

### Phase 2: Gradual Migration
- [ ] Migrate utility components
- [ ] Migrate data components
- [ ] Migrate phase components
- [ ] Test each migration

### Phase 3: Cleanup
- [ ] Remove shim (apiService.js)
- [ ] Verify all files migrated
- [ ] Final testing

---

## 📞 Support

### Common Issues

**Issue**: Import fails after migration  
**Solution**: Check path relative to file location

**Issue**: Component breaks after migration  
**Solution**: Check for `apiService.` references in code

**Issue**: Console warnings about apiService  
**Solution**: File still using old import, needs migration

---

## 🎓 Learning Resources

- **Current State**: See `IMPORT_MIGRATION_STATUS.md`
- **Service Details**: See `backendService.js` (source)
- **Function Reference**: See `backendService.js` (comments)

---

## 📋 Checklist for Each File

```markdown
### [FileName.jsx] Migration

- [ ] Update import statement
- [ ] Replace `apiService` with `backendService`
- [ ] Test component renders
- [ ] Check browser console (no errors)
- [ ] Verify functionality works
- [ ] Update this tracking document
```

---

## 🔗 Related Files

- `/apps/ui/react-app/src/services/backendService.js` - New canonical service
- `/apps/ui/react-app/src/services/apiService.js` - Shim (temporary)
- Components listed above - Need migration

---

## ✅ Sign-Off

**Shim**: ✅ Created and active  
**Backward Compatibility**: ✅ Enabled  
**Ready for Migration**: ✅ Yes  
**Current Status**: Safe to start component migrations

---

**Last Updated**: 2024  
**Next Review**: After first component migration  
**Timeline**: 1-2 weeks for full migration
